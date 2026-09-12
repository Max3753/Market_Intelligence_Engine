"""Source & CrawlJob — data sources the system monitors and their crawl executions."""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(50))  # reddit / github / v2ex / hackernews
    base_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    crawl_interval: Mapped[int] = mapped_column(default=60)  # minutes
    # ── 源级配置（P1）：cookie/token/verify/timeout/rate_limit/depth 等，适配器从这读 ──
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # ── 增量爬取（P1）：上次爬取开始时间，适配器 discover 可据此只拉增量 ──
    last_crawl_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    # ── 健康度（P1）：上次成功时间 / 连续失败次数 / 平均延迟秒 ──
    last_success_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(default=0)
    avg_latency: Mapped[Optional[float]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    items_found: Mapped[int] = mapped_column(default=0)
    items_stored: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[Optional[str]] = mapped_column(nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)