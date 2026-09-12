from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.demand import DemandSignal
from app.models.document import Document
from app.models.source import CrawlJob, Source
from app.schemas import SourceCreate, SourceRead, SourceStats

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceRead])          # ← 空字符串，不是 "/"
async def list_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).order_by(Source.id))
    return list(result.scalars())


@router.post("", response_model=SourceRead, status_code=201)
async def create_source(payload: SourceCreate, db: AsyncSession = Depends(get_db)):
    source = Source(
        name=payload.name, type=payload.type,
        base_url=payload.base_url, crawl_interval=payload.crawl_interval
        )
    
    db.add(source)
    await db.commit()
    await db.refresh(source)      # 拿回自增 id 和 created_at
    return source


@router.get("/stats", response_model=list[SourceStats])
async def source_stats(db: AsyncSession = Depends(get_db)):
    """每个源的爬取统计 + 信号产出（源质量反馈）+ 健康度。

    - signal_yield = 信号数 / 文档数（该源产出的需求信号占比）
    - job_* 统计近 30 天的爬取任务（成功率 / 平均耗时 / 去重率）
    - 健康度字段来自 Source（last_success_at / consecutive_failures / avg_latency）
    """
    sources = (await db.execute(select(Source).order_by(Source.id))).scalars().all()

    # 每个源的文档数
    doc_counts = dict((await db.execute(
        select(Document.source_id, func.count(Document.id)).group_by(Document.source_id)
    )).all())

    # 每个源的信号数（经 Document 关联）
    signal_counts = dict((await db.execute(
        select(Document.source_id, func.count(DemandSignal.id))
        .join(DemandSignal, DemandSignal.document_id == Document.id)
        .group_by(Document.source_id)
    )).all())

    # 每个源的爬取统计（近 30 天）
    job_rows = (await db.execute(
        select(
            CrawlJob.source_id,
            func.count(CrawlJob.id),
            func.sum(case((CrawlJob.status == "completed", 1), else_=0)),
            func.avg(func.extract("epoch", CrawlJob.finished_at - CrawlJob.started_at)),
            func.sum(CrawlJob.items_found),
            func.sum(CrawlJob.items_stored),
        )
        .where(CrawlJob.created_at >= func.now() - func.make_interval(0, 0, 0, 30))
        .group_by(CrawlJob.source_id)
    )).all()

    job_stats: dict[int, dict] = {}
    for source_id, total, completed, avg_lat, found, stored in job_rows:
        job_stats[source_id] = {
            "total": total,
            "success_rate": (completed / total) if total else 0.0,
            "avg_latency": float(avg_lat) if avg_lat is not None else None,
            "dedup_rate": (1 - stored / found) if found else 0.0,
        }

    result = []
    for s in sources:
        docs = doc_counts.get(s.id, 0)
        signals = signal_counts.get(s.id, 0)
        js = job_stats.get(s.id, {})
        result.append(SourceStats(
            id=s.id,
            name=s.name,
            type=s.type,
            status=s.status,
            config=s.config,
            last_crawl_at=s.last_crawl_at,
            last_success_at=s.last_success_at,
            consecutive_failures=s.consecutive_failures,
            avg_latency=s.avg_latency,
            document_count=docs,
            signal_count=signals,
            signal_yield=round(signals / docs, 3) if docs else 0.0,
            job_total=js.get("total", 0),
            job_success_rate=js.get("success_rate", 0.0),
            job_avg_latency=js.get("avg_latency"),
            dedup_rate=js.get("dedup_rate", 0.0),
        ))
    return result