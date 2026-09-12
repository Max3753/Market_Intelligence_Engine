"""Clustering — group similar demand signals into clusters."""

import numpy as np
from sklearn.cluster import HDBSCAN
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.llm_client import chat_json
from app.intelligence.scoring import score, evaluate_cluster
from app.models.demand import DemandCluster, DemandSignal
from app.models.document import Document
from app.models.opportunity import Opportunity

NAMING_SYSTEM_PROMPT = """You are a market analyst naming demand clusters.

Given several demand statements from different users that were grouped together
because they express the same underlying need, respond with STRICT JSON only:

{"name": "<short cluster name, <=6 words>", "description": "<1-2 sentence summary of the shared need>"}

Rules:
- Name the UNDERLYING need, not any specific product
- Use the language of the source texts (English here)
"""

"""Demand clustering — HDBSCAN over normalized embeddings."""

MIN_CLUSTER_SIZE = 2    # 小样本参数；数据过百后提到 3-5

def cluster_vectors(vectors: list[list[float]]) -> list[int]:
    """Cluster embedding vectors, return cluster label per vector.

    Label -1 = noise (HDBSCAN's way of saying "belongs to no cluster").
    """
    if len(vectors) < MIN_CLUSTER_SIZE:
        return [-1] * len(vectors)  # 点太少，直接返回噪声
    
    matrix = np.array(vectors)
    model = HDBSCAN(min_cluster_size=MIN_CLUSTER_SIZE, metric="euclidean")
    return model.fit_predict(matrix).tolist()

async def name_clusters(problems: list[str]) -> dict:
    """Ask LLM to name a cluster from its member problem statements."""
    joined = "\n".join(f"- {p}" for p in problems)
    
    return await chat_json(NAMING_SYSTEM_PROMPT, joined)


async def rebuild_clusters(db: AsyncSession) -> dict:
    """Re-cluster all embedded demand signals (full rebuild).

    Raises ValueError when fewer than 2 embedded signals exist.
    """
    # 1. 取所有有向量的信号（join documents 拿向量 + author）
    result = await db.execute(
        select(DemandSignal, Document)
        .join(Document, DemandSignal.document_id == Document.id)
        .where(Document.embedding.is_not(None))
    )
    rows = result.all()

    signals = [r[0] for r in rows]
    if len(signals) < 2:
        raise ValueError("Need at least 2 embedded signals to cluster")

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


async def rescore_clusters(db: AsyncSession) -> dict:
    """Score every cluster and persist demand_score.

    Raises ValueError when no clusters exist.
    """
    clusters = (await db.execute(select(DemandCluster))).scalars().all()
    if not clusters:
        raise ValueError("No clusters yet — run rebuild first")

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
