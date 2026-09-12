"""API routes for DemandClusters."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select

from app.db.session import get_db
from app.models.demand import DemandCluster, DemandSignal, Evidence
from app.models.document import Document
from app.intelligence.clustering import rebuild_clusters, rescore_clusters
from app.schemas import DemandClusterRead

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
async def rebuild_clusters_endpoint(db: AsyncSession = Depends(get_db)):
    """Re-cluster all embedded demand signals (full rebuild)."""
    try:
        return await rebuild_clusters(db)
    except ValueError as e:
        raise HTTPException(422, detail=str(e))

@router.post("/rescore")
async def rescore_clusters_endpoint(db: AsyncSession = Depends(get_db)):
    """Score every cluster and persist demand_score."""
    try:
        return await rescore_clusters(db)
    except ValueError as e:
        raise HTTPException(422, detail=str(e))

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