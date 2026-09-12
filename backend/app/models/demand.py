"""DemandSignal, DemandCluster & Evidence — the demand intelligence core."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DemandSignal(Base):
    """An extracted demand from a classified document (§11)."""

    __tablename__ = "demand_signals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    demand_type: Mapped[str] = mapped_column(nullable=False)  # pain / feature_request / ...
    problem: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pain_points: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    job_to_be_done: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    desired_outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    frequency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    severity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    willingness_to_pay: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evidence_strength: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    cluster_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("demand_clusters.id"), nullable=True
    )


class DemandCluster(Base):
    """A group of similar demand signals (§15/§16)."""

    __tablename__ = "demand_clusters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(nullable=True)
    description: Mapped[Optional[str]] = mapped_column(nullable=True)
    user_segment: Mapped[Optional[str]] = mapped_column(nullable=True)
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    unique_user_count: Mapped[int] = mapped_column(Integer, default=0)
    # 独立数据源数（成员文档 source_id 去重）；<2 = 单源信号，等待交叉验证
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    pain_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    frequency_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    money_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    growth_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    competition_gap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    demand_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Evidence(Base):
    """Supporting proof linking documents to demand signals (§12)."""

    __tablename__ = "evidences"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    demand_signal_id: Mapped[int] = mapped_column(ForeignKey("demand_signals.id"))
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    evidence_type: Mapped[Optional[str]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)