"""Opportunity, OpportunityAnalysis & TrendMetric — product opportunities and demand growth tracking."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Opportunity(Base):
    """A validated product opportunity derived from demand clusters (§19)."""

    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 可空：rebuild 全量重建会删簇，机会作为人工决策记录必须存活，届时断链保留
    cluster_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("demand_clusters.id"), nullable=True
    )
    title: Mapped[Optional[str]] = mapped_column(nullable=True)
    problem_statement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_customer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proposed_solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    market_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # 立项时快照的独立数据源数；rebuild 断链后仍可追溯当时是否单源
    source_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    validation_status: Mapped[str] = mapped_column(default="DISCOVERED")
    priority: Mapped[int] = mapped_column(default=0)
    rejection_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 一个机会一条可行性分析（uselist=False）；级联删除由 FK ondelete 处理
    analysis: Mapped[Optional["OpportunityAnalysis"]] = relationship(
        back_populates="opportunity", uselist=False
    )


class OpportunityAnalysis(Base):
    """LLM 生成的机会可行性分析 —— 辅助人决策，不替代人（Human-in-the-Loop）。

    一个机会一条分析（opportunity_id 唯一）；重复生成覆盖旧记录。
    risks / validation_hypotheses / action_items 以 JSON 字符串存储（与
    DemandSignal.pain_points 模式一致）。
    """

    __tablename__ = "opportunity_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 级联删除：机会删除时其分析一并删除
    opportunity_id: Mapped[int] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), unique=True
    )
    feasibility_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    technical_feasibility: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    market_feasibility: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    competition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON 数组字符串
    validation_hypotheses: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON 数组字符串
    action_items: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON 数组字符串
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    opportunity: Mapped["Opportunity"] = relationship(back_populates="analysis")


class TrendMetric(Base):
    """A time-series data point tracking demand growth (§20)."""

    __tablename__ = "trend_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 可空：rebuild 全量重建会删簇，趋势数据作为历史记录必须存活，届时断链保留
    cluster_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("demand_clusters.id"), nullable=True
    )
    period: Mapped[str] = mapped_column(String(30))  # e.g. "2024-W01" or "2024-01"
    signal_count: Mapped[int] = mapped_column(default=0)
    avg_severity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_willingness_to_pay: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    growth_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)