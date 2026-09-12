"""CrawlQueue + worker functions — Redis-backed job queue and consumers."""
import asyncio
import json
from datetime import datetime

import httpx
from sqlalchemy import select

from app.adapters import get_adapter
from app.config.settings import settings
from app.db.session import async_session_factory
from app.extraction.pipeline import check_semantic_duplicate, normalise
from app.intelligence.analysis import auto_pipeline
from app.models.document import Author, Document, RawDocument
from app.models.source import CrawlJob, Source

# 瞬时错误重试：最多 3 次，退避 1s / 5s / 30s
RETRY_ATTEMPTS = 3
RETRY_BACKOFF = (1, 5, 30)


def _is_transient(exc: Exception) -> bool:
    """瞬时错误（网络/超时/5xx/429）→ 可重试；其余 → 永久失败。"""
    if isinstance(
        exc,
        (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError, httpx.TransportError),
    ):
        return True
    msg = str(exc)
    # 适配器抛的 "…returned 429/5xx" 类错误 → 瞬时
    if "returned" in msg:
        for token in msg.split():
            if token.isdigit() and (int(token) >= 500 or int(token) == 429):
                return True
    return False

class CrawlQueue:
    """Manages crawl job enqueueing and dequeuing via Redis lists."""

    def __init__(self, redis_url: str) -> None:
        # TODO: initialise Redis connection
        self._redis_url = redis_url

    async def enqueue(self, job_id: int, source_id: int) -> None:
        """Push a crawl job onto the queue."""
        # TODO: LPUSH job payload to Redis list
        raise NotImplementedError

    async def dequeue(self) -> dict | None:
        """Pop the next crawl job from the queue."""
        # TODO: RPOP from Redis list, return job payload or None
        raise NotImplementedError

    async def get_status(self, job_id: int) -> str:
        """Return the current status of a job."""
        # TODO: look up job status from Redis hash
        raise NotImplementedError


async def crawl_worker() -> None:
    """Main worker loop — dequeue jobs and execute crawls."""
    # TODO: loop: dequeue job → resolve adapter → discover → fetch → store raw docs
    raise NotImplementedError


async def process_job(job_id: int, source_id: int) -> None:
    """Execute a single crawl job.

    - discover 阶段：瞬时错误重试（指数退避），永久错误直接 failed
    - fetch/parse 阶段：单个 URL 失败记录错误并跳过，不中断整个 job
    - 全部 URL 失败 → failed；部分失败 → completed + error_message
    - 任何未捕获异常 → failed（不卡 running）
    - 更新源健康度：last_crawl_at / last_success_at / consecutive_failures / avg_latency
    """
    # ── 开一个独立 session（后台任务不能复用请求的 session）──
    async with async_session_factory() as db:
        try:
            # 第1步：查 source 配置
            source = await db.get(Source, source_id)
            if source is None:
                return

            # 第2步：标记 running
            job = await db.get(CrawlJob, job_id)
            job.status = "running"
            job.started_at = datetime.utcnow()
            await db.commit()

            # 第3步：拿适配器实例（带源配置：base_url + config JSON）
            source_cfg = {
                "base_url": source.base_url,
                **(source.config or {}),
            }
            adapter = get_adapter(source.type)(source_cfg)

            # 第4步：发现帖子 —— 瞬时错误重试（指数退避）
            # 增量基准：上次爬取时间（本次之前的 last_crawl_at）
            discover_cfg = {
                **source_cfg,
                "last_crawl_at": source.last_crawl_at,
            }
            urls: list[str] = []
            for attempt in range(RETRY_ATTEMPTS):
                try:
                    urls = await adapter.discover(discover_cfg)
                    break
                except Exception as e:
                    if not _is_transient(e) or attempt == RETRY_ATTEMPTS - 1:
                        raise
                    await asyncio.sleep(RETRY_BACKOFF[attempt])
            job.items_found = len(urls)

            # 第5步：逐个抓取+解析+存储 —— 单 URL 失败跳过，不中断
            # 速率限制：source.config["rate_limit"] = 秒/请求（0/缺省 = 不限速）
            rate_limit = float(source_cfg.get("rate_limit") or 0)
            errors: list[str] = []
            for i, url in enumerate(urls):
                if rate_limit > 0 and i > 0:
                    await asyncio.sleep(rate_limit)
                try:
                    raw = await adapter.fetch(url)
                    doc = await adapter.parse(raw)
                    norm = normalise(doc, source.type)

                    # 5a. 存原始数据（可追溯层）
                    db.add(RawDocument(
                        crawl_job_id=job_id,
                        source_id=source.id,
                        url=url,
                        payload=json.dumps(raw),
                        content_type="application/json",
                        status="fetched"
                    ))

                    # 5b. 按 content_hash 去重 —— 已存在就跳过
                    existing = await db.scalar(
                        select(Document).where(Document.content_hash == norm["content_hash"])
                    )
                    if existing:
                        continue

                    # 5b'. 语义去重 —— content_hash 未命中时，用 embedding 余弦相似度兜底
                    # 与 _analyze_one 相同的文本拼接，保证向量可比
                    # 失败时放行（fail-open）：语义去重是补充层，不应阻断入库
                    try:
                        text = f"{norm['title'] or ''}\n\n{norm['content'] or ''}"
                        dup_id = await check_semantic_duplicate(db, text)
                        if dup_id is not None:
                            continue
                    except Exception as e:
                        errors.append(f"{url}: semantic_dedup: {type(e).__name__}: {e}")

                    # 5c. Author upsert —— 查不到才建
                    author_id = None
                    if doc.get("author"):
                        author = await db.scalar(
                            select(Author).where(
                                Author.source_id == source_id,
                                Author.source_author_id == doc["author"]
                            )
                        )
                        if author is None:
                            author = Author(source_id=source_id, source_author_id=doc["author"])
                            db.add(author)
                            await db.flush()
                        author_id = author.id

                    # 5d. 存标准化文档
                    db.add(Document(
                        source_id=source.id,
                        source_item_id=norm["source_item_id"],
                        url=norm["url"],
                        title=norm["title"],
                        content=norm["content"],
                        author_id=author_id,
                        published_at=norm["published_at"],      # 已是 datetime
                        engagement_score=norm["engagement_score"],
                        language=norm["language"],
                        content_hash=norm["content_hash"],
                    ))
                    job.items_stored += 1
                except Exception as e:
                    errors.append(f"{url}: {type(e).__name__}: {e}")

            # 第6步：收尾 —— 全部失败 → failed；部分失败 → completed + 错误记录
            latency = (datetime.utcnow() - job.started_at).total_seconds()
            if errors and len(errors) == len(urls) and job.items_stored == 0:
                job.status = "failed"
                job.error_message = "; ".join(errors)[:2000]
                source.consecutive_failures += 1
            else:
                if errors:
                    job.error_message = "; ".join(errors)[:2000]
                job.status = "completed"
                source.consecutive_failures = 0
                source.last_success_at = datetime.utcnow()
                # avg_latency：指数移动平均（EMA，α=0.3）
                source.avg_latency = (
                    latency if source.avg_latency is None
                    else 0.7 * source.avg_latency + 0.3 * latency
                )
            # 增量基准推进：本次爬取时间
            source.last_crawl_at = datetime.utcnow()
            job.finished_at = datetime.utcnow()
            await db.commit()
        except Exception as e:
            # 第7步：任何异常 → 标记 failed，别让状态卡在 running
            await db.rollback()
            job = await db.get(CrawlJob, job_id)      # rollback 后重新拿 job
            if job is not None:
                job.status = "failed"
                job.error_message = f"{type(e).__name__}: {e}"[:2000]
                job.finished_at = datetime.utcnow()
                await db.commit()
            # 健康度：连续失败 +1
            source = await db.get(Source, source_id)
            if source is not None:
                source.consecutive_failures += 1
                await db.commit()

        # 第8步：爬取成功且有新文档 → 触发自动分析流水线（分析→聚类→评分）
        # 独立 session 后台任务；信号不足/无簇时内部正常跳过
        if job.status == "completed" and job.items_stored > 0 and settings.AUTO_PIPELINE:
            asyncio.create_task(auto_pipeline())
    