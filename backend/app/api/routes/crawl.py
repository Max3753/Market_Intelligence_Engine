import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crawling.workers import process_job
from app.db.session import get_db
from app.models.source import CrawlJob, Source
from app.schemas import CrawlJobCreate, CrawlJobRead

router = APIRouter(prefix="/crawl", tags=["crawl"])

@router.post("/jobs", response_model=CrawlJobRead)
async def create_crawl_job(payload: CrawlJobCreate, db: AsyncSession = Depends(get_db)):
    """Create a new crawl job for a source"""
    # 1. 验证 source cunzai
    source = await db.get(Source, payload.source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    # 2. 创建 任务记录
    job = CrawlJob(source_id=payload.source_id, status="pending")
    db.add(job)
    await db.commit()
    await db.refresh(job)   # 那会自增 id
    
    # 3. 后台执行 -- 不 await ，直接返回
    asyncio.create_task(process_job(job.id, source.id))
    
    return job

@router.get("/jobs", response_model=list[CrawlJobRead])
async def list_crawl_jobs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Recent crawl jobs, newest first."""
    result = await db.execute(
        select(CrawlJob).order_by(CrawlJob.id.desc()).limit(limit)
    )
    return list(result.scalars())


@router.get("/jobs/{job_id}", response_model=CrawlJobRead)
async def get_crawl_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Return the status of a crawl job"""
    job = await db.get(CrawlJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Crawl job not found")
    return job
    