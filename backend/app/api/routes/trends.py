"""API routes for TrendMetrics — 簇信号增长趋势（REQ-009 收尾）。

实时计算（不写 trend_metrics 表）：每个簇按 7/30/90 天窗口统计信号数，
growth_rate = (当前窗口信号数 - 前一窗口信号数) / 前一窗口信号数；
前一窗口无信号时 growth_rate 为 null（数据不足，不臆造增长率）。
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.demand import DemandCluster, DemandSignal
from app.schemas import TrendMetricRead

router = APIRouter(prefix="/trends", tags=["trends"])

# 趋势窗口：7/30/90 天（与设计文档 §20 一致）
WINDOWS: dict[str, int] = {"7d": 7, "30d": 30, "90d": 90}


@router.get("/", response_model=list[TrendMetricRead])
async def list_trends(db: AsyncSession = Depends(get_db)):
    """Return per-cluster signal growth across 7/30/90-day windows."""
    now = datetime.utcnow()
    clusters = (await db.execute(select(DemandCluster))).scalars().all()

    results: list[TrendMetricRead] = []
    seq = 0
    for cluster in clusters:
        for period, days in WINDOWS.items():
            cur_start = now - timedelta(days=days)
            prev_start = now - timedelta(days=days * 2)

            cur_count = (
                await db.execute(
                    select(func.count())
                    .select_from(DemandSignal)
                    .where(
                        DemandSignal.cluster_id == cluster.id,
                        DemandSignal.created_at >= cur_start,
                    )
                )
            ).scalar_one()

            prev_count = (
                await db.execute(
                    select(func.count())
                    .select_from(DemandSignal)
                    .where(
                        DemandSignal.cluster_id == cluster.id,
                        DemandSignal.created_at >= prev_start,
                        DemandSignal.created_at < cur_start,
                    )
                )
            ).scalar_one()

            growth = (cur_count - prev_count) / prev_count if prev_count > 0 else None

            seq += 1
            results.append(
                TrendMetricRead(
                    id=seq,
                    topic=cluster.name or f"Cluster {cluster.id}",
                    metric_name="signal_growth",
                    value=cur_count,
                    growth_rate=growth,
                    period=period,
                    created_at=now,
                )
            )
    return results