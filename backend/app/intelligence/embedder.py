"""Local embeddings — all-MiniLM-L6-v2, 384-dim, fully offline."""
import asyncio
from functools import lru_cache

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

@lru_cache(maxsize=1)
def get_model():
    """Load once from local cache, reuse forever.

    惰性导入：sentence_transformers 导入链含 tensorflow（transformers 依赖），
    顶层导入会让任何引用 EMBEDDING_DIM 的模块（如 models/document.py）在
    pytest 收集/导入阶段触发 protobuf 版本冲突。只在真正需要模型时导入。
    """
    from sentence_transformers import SentenceTransformer

    try:
        # 第一优先：纯本地加载 —— 零网络请求，秒级
        return SentenceTransformer(MODEL_NAME, local_files_only=True)
    except Exception:
        # 本地无缓存（首次运行/换了模型）→ 联网下载
        return SentenceTransformer(MODEL_NAME)

async def embed(text: str) -> list[float]:
    """Embed text into a normalized 384-dim vector.

    encode() is CPU-bound sync — push to a thread so the event loop isn't blocked.
    """
    vector = await asyncio.to_thread(
        get_model().encode,
        text,
        normalize_embeddings=True,
    )
    return vector.tolist()

async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts in one model pass (much faster than N× single)."""
    vectors = await asyncio.to_thread(
        get_model().encode, texts, normalize_embeddings=True
    )
    return vectors.tolist()
