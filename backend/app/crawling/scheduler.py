"""CrawlScheduler — manages periodic crawl execution via APScheduler."""

import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, update

from app.crawling.workers import process_job
from app.db.session import async_session_factory
from app.models.source import CrawlJob, Source


class CrawlScheduler:
    """Thin wrapper around APScheduler for scheduling crawl jobs."""

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler()
        self._running = False

    async def start(self) -> None:
        """Start the scheduler, registering crawl jobs from active sources."""
        if self._running:
            return
        await self._recover_orphan_jobs()
        await self._register_active_sources()
        self._scheduler.start()
        self._running = True

    async def _recover_orphan_jobs(self) -> None:
        """Mark jobs stuck in 'running' as 'interrupted' (previous process died).

        进程崩溃/重启时 asyncio 任务被中断，try/except 没机会执行，job 会永远
        卡在 running。启动时统一回收为 interrupted，避免状态机卡死。
        """
        async with async_session_factory() as db:
            await db.execute(
                update(CrawlJob)
                .where(CrawlJob.status == "running")
                .values(status="interrupted", finished_at=datetime.utcnow())
            )
            await db.commit()

    async def stop(self) -> None:
        """Gracefully stop the scheduler."""
        if not self._running:
            return
        self._scheduler.shutdown(wait=False)
        self._running = False

    async def add_job(self, source_id: int, interval_minutes: int) -> None:
        """Schedule a recurring crawl for a source."""
        self._scheduler.add_job(
            self._run_crawl,
            "interval",
            minutes=interval_minutes,
            args=[source_id],
            id=f"crawl-source-{source_id}",
            replace_existing=True,
            max_instances=1,   # 同一源不并发跑
            coalesce=True,     # 错过多次只补一次
        )

    async def _register_active_sources(self) -> None:
        """Register all active sources from the database."""
        async with async_session_factory() as db:
            result = await db.execute(
                select(Source).where(Source.status == "active")
            )
            sources = result.scalars().all()
        for source in sources:
            await self.add_job(source.id, source.crawl_interval)

    async def _run_crawl(self, source_id: int) -> None:
        """Create a crawl job and dispatch it to the worker (fire-and-forget)."""
        async with async_session_factory() as db:
            source = await db.get(Source, source_id)
            if source is None or source.status != "active":
                return
            job = CrawlJob(source_id=source_id, status="pending")
            db.add(job)
            await db.commit()
            await db.refresh(job)
        asyncio.create_task(process_job(job.id, source_id))
