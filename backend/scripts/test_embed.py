"""Verify local embedding model downloads and works."""
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

v1 = model.encode("Jira export is broken, I need CSV download",
    normalize_embeddings=True)
v2 = model.encode("How do I export issues from Jira to Excel?",
    normalize_embeddings=True)
v3 = model.encode("My cat knocked over my coffee this morning",
    normalize_embeddings=True)

print(f"dim={len(v1)}")
print(f"similar pair:   {np.dot(v1, v2):.3f}")   # 预期 > 0.7
print(f"unrelated pair: {np.dot(v1, v3):.3f}")   # 预期 < 0.3
