"""Market Intelligence Engine — FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    sources,
    documents,
    demands,
    clusters,
    opportunities,
    trends,
    crawl,
)
from app.crawling.scheduler import CrawlScheduler
from app.crawling.seeding import seed_default_sources

# 模块级单例：lifespan 内 start/stop，供测试与 reload 复用
scheduler = CrawlScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed default sources on first boot, then start the crawl scheduler.

    新播种的源立即触发一次初始爬取（不等第一个 interval 周期），
    爬取成功后自动流水线（分析→聚类→评分）会随之运行。
    """
    seeded = await seed_default_sources()
    await scheduler.start()
    for source in seeded:
        await scheduler.trigger_now(source.id)
    yield
    await scheduler.stop()


app = FastAPI(
    title="Market Intelligence Engine",
    version="0.1.0",
    description="Evidence-driven product discovery system.",
    lifespan=lifespan,
)

# CORS — allow the Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(sources.router)
app.include_router(documents.router)
app.include_router(demands.router)
app.include_router(clusters.router)
app.include_router(opportunities.router)
app.include_router(trends.router)
app.include_router(crawl.router)


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}
