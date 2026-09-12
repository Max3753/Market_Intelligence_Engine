"""Extraction pipeline — clean, parse and normalise raw content into documents."""
from __future__ import annotations

import re
import hashlib
import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# 语义去重阈值：余弦相似度 ≥ 0.95 判定为重复。
# pgvector 的 <=> 返回余弦距离（0=完全相同，2=完全相反），
# 因此距离阈值 = 1 - 相似度阈值 = 0.05。
SEMANTIC_DEDUP_THRESHOLD = 0.95


async def check_semantic_duplicate(
    db: AsyncSession,
    text: str,
    threshold: float = SEMANTIC_DEDUP_THRESHOLD,
) -> int | None:
    """语义去重：新文档与已有文档的 embedding 余弦相似度超过阈值 → 判定重复。

    作为 content_hash 精确去重之后的补充层（hash 先拦截，语义兜底）。
    返回重复文档的 id；无重复返回 None。
    旧文档 embedding 为 null 时自动跳过（只比较有向量的文档）。
    """
    if not text:
        return None

    # 惰性导入：embedder/models 导入链含 tensorflow（embedding），
    # 顶层导入会让 pytest 收集阶段触发 protobuf 版本冲突（见 conftest.py 注释）
    from sqlalchemy import select

    from app.intelligence.embedder import embed
    from app.models.document import Document

    embedding = await embed(text)

    # 余弦距离 ≤ (1 - 阈值) ⟺ 余弦相似度 ≥ 阈值
    distance_threshold = 1.0 - threshold

    dup_id = await db.scalar(
        select(Document.id)
        .where(Document.embedding.is_not(None))
        .where(Document.embedding.cosine_distance(embedding) <= distance_threshold)
        .limit(1)
    )
    return dup_id


def clean_text(raw_text: str) -> str:
	"""将原始文本进行清洗

	Args:
		raw_text (str): _description_

	Returns:
		str: _description_
	"""
	# 判断 raw_text 是否为空
	if not raw_text:
		return ""
	# 移除 HTML 标签
	text = re.sub(r"<[^>]+>", "", raw_text)
	text  = re.sub(r"\s+", " ", text).strip()
	
	return text


def parse_content(cleaned_text: str, source_type: str) -> dict:
	"""将清洗后的文本，进行解析

	Args:
		cleaned_text (str): _description_
		source_type (str): _description_

	Returns:
		dict: _description_
	"""
	
	text = cleaned_text
	# 当 source_type == "reddit"
	if source_type == "reddit":
		## 移除链接语法
		text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
		text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
		text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)

	# 标题/正文分离
	t_c = text.split("\n\n", 1)
	title = t_c[0]
	content = t_c[1] if "\n\n" in text else None

	return {
		"title": title,
		"content": content,
	}


def normalise(parsed_data: dict, source_type: str) -> dict:
	"""将接收到数据，进行清洗、解析、标准化

	Args:
		parsed_data (dict): _description_
		source_type (str): _description_

	Returns:
		dict: _description_
	"""
	# content_hash 计算（去重核心）
	raw = f"{parsed_data.get('url') or ''}|{parsed_data.get('content') or ''}"
	content_hash = hashlib.sha256(raw.encode()).hexdigest()

	# Unix 时间戳 → datetime（缺失则 None）
	ts = parsed_data.get("published_at")
	if ts is None:
		published_at = None
	elif isinstance(ts, (int, float)) or (
        isinstance(ts, str) and ts.strip().lstrip("-").isdigit()
    ):
		published_at = datetime.datetime.fromtimestamp(float(ts))
	else:
		published_at = datetime.datetime.fromisoformat(
            ts.replace("Z", "+00:00")
        ).astimezone(datetime.timezone.utc).replace(tzinfo=None)
	return {
        "source_id": parsed_data.get("source_id"),
        "source_item_id": parsed_data.get("source_item_id"),
        "url": parsed_data.get("url"),
        "title": parsed_data.get("title"),
        "content": parsed_data.get("content"),
        "published_at": published_at,
        "engagement_score": parsed_data.get("engagement_score"),
        "language": parsed_data.get("language") or "en",
        "content_hash": content_hash,
    }
