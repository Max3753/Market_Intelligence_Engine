"""API routes for DemandClusters."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select, delete, update
from sqlalchemy import func

from app.db.session import get_db
from app.models.demand import DemandSignal, DemandCluster
from app.models.document import Document
from app.models.opportunity import Opportunity
from app.intelligence.clustering import cluster_vectors, name_clusters
from app.schemas import DemandClusterRead
from app.intelligence.scoring import score, evaluate_cluster
from app.models.demand import Evidence

router = APIRouter(prefix="/clusters", tags=["clusters"])


@router.get("", response_model=list[DemandClusterRead])
async def list_clusters(db: AsyncSession = Depends(get_db)):
    """Return all demand clusters, biggest first."""
    result = await db.execute(
        select(DemandCluster).order_by(DemandCluster.demand_score.desc().nulls_last())
    )
    return list(result.scalars())


@router.get("/{cluster_id}", response_model=DemandClusterRead)
async def get_cluster(cluster_id: int, db: AsyncSession = Depends(get_db)):
    """Return a single demand cluster by ID."""
    cluster = await db.get(DemandCluster, cluster_id)
    if cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster

@router.post("/rebuild")
async def rebuild_clusters(db: AsyncSession = Depends(get_db)):
    """Re-cluster all embedded demand signals (full rebuild)."""
    # 1. 取所有有向量的信号（join documents 拿向量 + author）
    result = await db.execute(
        select(DemandSignal, Document)
        .join(Document, DemandSignal.document_id == Document.id)
        .where(Document.embedding.is_not(None))
    )
    rows = result.all()
    
    signals = [r[0] for r in rows]
    if len(signals) < 2:
        raise HTTPException(422, detail="Need at least 2 embedded signals to cluster")
    
    vectors = [r[1].embedding for r in rows]
    
    # 2. 聚类
    labels = cluster_vectors(vectors)
    
    # 3. 全量重建：解除所有引用（信号 + 机会），再清旧簇
    #    机会是人工决策记录，断链保留而非删除；批量 update 覆盖全部行，
    #    包括未出现在上方 join 结果里的信号
    await db.execute(update(DemandSignal).values(cluster_id=None))
    await db.execute(update(Opportunity).values(cluster_id=None))
    await db.flush()

    await db.execute(delete(DemandCluster))
    
    # 4. 按簇分组（跳过噪声 -1）
    clusters_map: dict[int, list[int]] = {}    # label -> [signal indices]
    for idx, label in enumerate(labels):
        if label != -1:
            clusters_map.setdefault(label, []).append(idx)
    
    # 5. 每簇：LLM 命名 + 统计 + 落库
    for label, idxs in clusters_map.items():
        members = [signals[i] for i in idxs]
        problems = [m.problem or m.demand_type for m in members]    # problem 可能是 null，兜底用类型名
        
        naming = await name_clusters(problems)                      # LLM 调用
        
        member_ids = {m.id for m in members}
        author_ids = {
            r[1].author_id for r in rows if r[0].id in member_ids
        }
        source_ids = {
            r[1].source_id for r in rows if r[0].id in member_ids
        }
        
        cluster = DemandCluster(
            name=naming.get("name", f"cluster_{label}"),
            description=naming.get("description"),
            document_count=len(members),
            unique_user_count=len(author_ids),
            source_count=len(source_ids),
        )
        db.add(cluster)
        await db.flush()                    # 拿 cluster.id
        
        for m in members:
            m.cluster_id = cluster.id       # 信号挂簇
            
    await db.commit()
    
    return {"clusters_built": len(clusters_map), "noise_signals": labels.count(-1)}

@router.post("/rescore")
async def rescore_clusters(db: AsyncSession = Depends(get_db)):
    """Score every cluster and persist demand_score."""
    clusters = (await db.execute(select(DemandCluster))).scalars().all()
    if not clusters:
        raise HTTPException(422, detail="No clusters yet — run rebuild first")
    
    max_doc = max(c.document_count for c in clusters)
    
    for c in clusters:
        # 簇内信号统计（severity/wtp/evidence 均值）
        stats = await db.execute(
            select(
                func.avg(DemandSignal.severity),
                func.avg(DemandSignal.willingness_to_pay),
                func.avg(DemandSignal.evidence_strength)
            ).where(DemandSignal.cluster_id == c.id)
        )
        sev, wtp, ev = stats.one()

        metrics = await evaluate_cluster(
            sev, wtp, ev, 
            c.document_count, c.unique_user_count,
            max_doc, c.description or ""
            )
        c.demand_score = score(metrics)
        # 把各维分数也存进 cluster 行（pain_score/frequency_score/... 列都在）
        c.pain_score = metrics["pain"]
        c.frequency_score = metrics["frequency"]
        c.money_score = metrics["willingness_to_pay"]
        c.growth_score = metrics["growth"]
        c.competition_gap = metrics["competition_gap"]

    await db.commit()
    return {"scored": len(clusters)}

@router.get("/{cluster_id}/detail")
async def get_cluster_details(cluster_id: int, db: AsyncSession = Depends(get_db)):
    """Cluster deep-dive: cluster + member signals + evidence quotes."""
    cluster = await db.get(DemandCluster, cluster_id)
    if cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    # 成员信号 + 关联文档（拿 title/url 展示）
    result = await db.execute(
        select(DemandSignal, Document)
        .join(Document, DemandSignal.document_id == Document.id)
        .where(DemandSignal.cluster_id == cluster_id)
        .order_by(DemandSignal.severity.desc().nulls_last())
    )
    
    members = []
    for signal, doc in result.all():
        # 该信号的证据引用
        ev_result = await db.execute(
            select(Evidence).where(Evidence.demand_signal_id == signal.id)
        )
        evidences = [
            {"snippet": ev.snippet, "relevance": ev.relevance_score}
            for ev in ev_result.scalars()
        ]
        
        members.append({
            "signal_id": signal.id,
            "demand_type": signal.demand_type,
            "problem": signal.problem,
            "severity": signal.severity,
            "confidence": signal.confidence,
            "document_title": doc.title,
            "document_url": doc.url,
            "evidences": evidences,
        })
        
    return {
        "cluster": {
            "id": cluster.id, "name": cluster.name,
            "description": cluster.description,
            "demand_score": cluster.demand_score,
            "pain_score": cluster.pain_score,
            "frequency_score": cluster.frequency_score,
            "money_score": cluster.money_score,
            "growth_score": cluster.growth_score,
            "competition_gap": cluster.competition_gap,
            "document_count": cluster.document_count,
            "unique_user_count": cluster.unique_user_count,
            "source_count": cluster.source_count,
        },
        "members": members,
    }


@router.get("/{cluster_id}/evidence-pack")
async def get_evidence_pack(cluster_id: int, db: AsyncSession = Depends(get_db)):
    """Markdown decision brief — cluster + signals + evidence quotes for human review."""
    cluster = await db.get(DemandCluster, cluster_id)
    if cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")

    result = await db.execute(
        select(DemandSignal, Document)
        .join(Document, DemandSignal.document_id == Document.id)
        .where(DemandSignal.cluster_id == cluster_id)
        .order_by(DemandSignal.severity.desc().nulls_last())
    )

    lines = [
        f"# 需求决策简报：{cluster.name}",
        "",
        f"- 综合分：{cluster.demand_score if cluster.demand_score is not None else '未评分'}",
        f"- 信号数：{cluster.document_count} · 独立用户：{cluster.unique_user_count}",
        f"- 描述：{cluster.description or '—'}",
        "",
        "## 证据清单",
        "",
    ]

    for signal, doc in result.all():
        ev_result = await db.execute(
            select(Evidence).where(Evidence.demand_signal_id == signal.id)
        )
        evidences = list(ev_result.scalars())

        lines.append(f"### [{doc.title}]({doc.url})")
        lines.append("")
        lines.append(
            f"- 类型：{signal.demand_type} · severity {signal.severity if signal.severity is not None else '—'}"
            f" · confidence {signal.confidence if signal.confidence is not None else '—'}"
        )
        if signal.problem:
            lines.append(f"- 问题：{signal.problem}")
        for ev in evidences:
            if ev.snippet:
                lines.append(f"> “{ev.snippet}”")
        lines.append("")

    return Response(
        content="\n".join(lines),
        media_type="text/markdown; charset=utf-8",
    )
    