"""Opportunity relink — re-attach orphaned opportunities to the best-matching cluster.

Clusters are rebuilt wholesale (POST /clusters/rebuild deletes old clusters and
re-creates new ones). Opportunities are human decision records that must survive
the rebuild, so their cluster_id is set to NULL (see Opportunity.cluster_id comment).
This module provides the reusable matching logic to re-attach any orphaned
opportunity to the most relevant current cluster, based on keyword overlap between
the opportunity's problem_statement and each cluster's name/description, optionally
enhanced by embedding similarity.
"""

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.demand import DemandCluster
from app.models.opportunity import Opportunity

# 常见英文停用词 —— 匹配时忽略，避免噪音词主导分数
STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "when",
    "while", "of", "at", "by", "for", "with", "about", "against", "between",
    "into", "through", "during", "before", "after", "above", "below", "to",
    "from", "up", "down", "in", "out", "on", "off", "over", "under", "again",
    "further", "once", "here", "there", "all", "any", "both", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "s", "t", "can", "will",
    "just", "don", "should", "now", "are", "is", "was", "were", "be", "been",
    "being", "have", "has", "had", "having", "do", "does", "did", "doing",
    "would", "could", "may", "might", "must", "shall", "they", "them",
    "their", "theirs", "this", "that", "these", "those", "i", "you", "he",
    "she", "it", "we", "me", "him", "her", "us", "my", "your", "his",
    "its", "our", "who", "whom", "which", "what", "where", "when", "why",
    "how", "as", "because", "until", "via", "per", "etc", "eg", "ie", "vs",
})

# 关键词分数权重：coverage 衡量问题被簇覆盖多少，precision 衡量簇是否聚焦
KEYWORD_COVERAGE_WEIGHT = 0.7
KEYWORD_PRECISION_WEIGHT = 0.3
# 组合分数中 embedding 相似度的权重（0.4 语义 + 0.6 关键词）
EMBEDDING_WEIGHT = 0.4
# 低于该分数视为无合适匹配，拒绝自动关联（Human-in-the-Loop：宁缺毋滥）
MIN_MATCH_SCORE = 0.15


def tokenize(text: str | None) -> set[str]:
    """Lowercase, strip punctuation, split into words, drop stopwords."""
    if not text:
        return set()
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 1}


def _token_overlap(problem_tokens: set[str], cluster_tokens: set[str]) -> set[str]:
    """Problem tokens matched by a cluster token (exact or substring).

    子串匹配覆盖形态变化（alter ↔ altering、license ↔ licensing），
    无需引入词干提取依赖。
    """
    matched: set[str] = set()
    for pt in problem_tokens:
        for ct in cluster_tokens:
            if pt == ct or pt in ct or ct in pt:
                matched.add(pt)
                break
    return matched


def keyword_overlap_score(problem_tokens: set[str], cluster_tokens: set[str]) -> float:
    """Coverage-weighted keyword overlap in [0, 1]."""
    if not problem_tokens:
        return 0.0
    matched = _token_overlap(problem_tokens, cluster_tokens)
    coverage = len(matched) / len(problem_tokens)
    precision = len(matched) / len(cluster_tokens) if cluster_tokens else 0.0
    return KEYWORD_COVERAGE_WEIGHT * coverage + KEYWORD_PRECISION_WEIGHT * precision


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


async def find_best_cluster_match(
    problem_statement: str | None,
    clusters: list[DemandCluster],
    use_embedding: bool = True,
) -> tuple[DemandCluster | None, float, str]:
    """Find the cluster whose name/description best matches the problem statement.

    Returns (best_cluster, score, method). method ∈ {"keyword", "keyword+embedding"}.
    """
    problem_tokens = tokenize(problem_statement)

    # 可选 embedding：语义相似度增强（失败则静默回退到纯关键词）
    problem_vec: list[float] | None = None
    cluster_vecs: dict[int, list[float]] = {}
    if use_embedding:
        try:
            from app.intelligence.embedder import embed, embed_batch

            combined = [
                f"{c.name or ''}. {c.description or ''}".strip()
                for c in clusters
            ]
            vectors = await embed_batch(combined)
            cluster_vecs = {c.id: v for c, v in zip(clusters, vectors)}
            problem_vec = await embed(problem_statement or "")
        except Exception:
            problem_vec = None
            cluster_vecs = {}

    best_cluster: DemandCluster | None = None
    best_score = 0.0
    method = "keyword"

    for cluster in clusters:
        cluster_tokens = tokenize(cluster.name) | tokenize(cluster.description)
        kw_score = keyword_overlap_score(problem_tokens, cluster_tokens)

        score = kw_score
        if problem_vec is not None and cluster.id in cluster_vecs:
            sim = _cosine_similarity(problem_vec, cluster_vecs[cluster.id])
            score = (1 - EMBEDDING_WEIGHT) * kw_score + EMBEDDING_WEIGHT * sim
            method = "keyword+embedding"

        if score > best_score:
            best_score = score
            best_cluster = cluster

    return best_cluster, best_score, method


async def relink_opportunity(
    db: AsyncSession,
    opportunity: Opportunity,
    use_embedding: bool = True,
) -> tuple[DemandCluster | None, float, str]:
    """Re-attach an orphaned opportunity to the best-matching current cluster.

    Returns (matched_cluster, score, method). If no cluster scores above the
    minimum threshold, matched_cluster is None and nothing is written.
    """
    clusters = (await db.execute(select(DemandCluster))).scalars().all()
    if not clusters:
        return None, 0.0, "keyword"

    best_cluster, score, method = await find_best_cluster_match(
        opportunity.problem_statement, clusters, use_embedding=use_embedding
    )
    if best_cluster is None or score < MIN_MATCH_SCORE:
        return None, score, method

    opportunity.cluster_id = best_cluster.id
    await db.commit()
    await db.refresh(opportunity)
    return best_cluster, score, method