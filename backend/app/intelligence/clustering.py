"""Clustering — group similar demand signals into clusters."""

import numpy as np
from sklearn.cluster import HDBSCAN


from app.intelligence.llm_client import chat_json

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
