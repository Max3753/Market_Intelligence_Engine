"""Pydantic schemas for all API resources (merged for a leaner framework)."""

import json
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


# --- Source ---


class SourceCreate(BaseModel):
    """Payload to create a new data source."""

    name: str
    type: str
    base_url: Optional[str] = None
    crawl_interval: int = 60


class SourceRead(BaseModel):
    """Serialized representation of a Source."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    base_url: Optional[str] = None
    status: str
    crawl_interval: int
    created_at: datetime
    updated_at: datetime


class SourceStats(BaseModel):
    """Per-source crawl statistics + signal yield + health (GET /sources/stats)."""

    id: int
    name: str
    type: str
    status: str
    config: Optional[dict] = None
    last_crawl_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    consecutive_failures: int
    avg_latency: Optional[float] = None
    # 信号产出（源质量反馈）
    document_count: int
    signal_count: int
    signal_yield: float          # 信号数 / 文档数
    # 爬取统计（近 30 天）
    job_total: int
    job_success_rate: float      # completed / total
    job_avg_latency: Optional[float] = None   # 秒
    dedup_rate: float            # 1 - items_stored/items_found


# --- Document ---


class DocumentRead(BaseModel):
    """Serialized representation of a Document."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    source_item_id: Optional[str] = None
    url: str
    canonical_url: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    author_id: Optional[int] = None
    published_at: Optional[datetime] = None
    engagement_score: Optional[float] = None
    language: Optional[str] = None
    created_at: datetime


# --- DemandSignal ---


class DemandSignalRead(BaseModel):
    """Serialized representation of a DemandSignal."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    demand_type: str
    problem: Optional[str] = None
    pain_points: Optional[str] = None
    job_to_be_done: Optional[str] = None
    desired_outcome: Optional[str] = None
    current_solution: Optional[str] = None
    frequency: Optional[float] = None
    severity: Optional[float] = None
    willingness_to_pay: Optional[float] = None
    evidence_strength: Optional[float] = None
    confidence: Optional[float] = None
    cluster_id: Optional[int] = None      # Phase 4 聚类挂载；噪声信号为 null
    created_at: datetime


# --- DemandCluster ---


class DemandClusterRead(BaseModel):
    """Serialized representation of a DemandCluster."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    user_segment: Optional[str] = None
    document_count: int
    unique_user_count: int
    source_count: int = 0          # 独立数据源数；<2 = 单源待交叉验证
    pain_score: Optional[float] = None
    frequency_score: Optional[float] = None
    money_score: Optional[float] = None
    growth_score: Optional[float] = None
    competition_gap: Optional[float] = None
    demand_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime


# --- Opportunity ---


class OpportunityCreate(BaseModel):
    """POST /opportunities — promote a cluster to an opportunity (human decision)."""

    cluster_id: int
    title: str
    problem_statement: Optional[str] = None
    target_customer: Optional[str] = None
    proposed_solution: Optional[str] = None
    # 单源簇（source_count < 2）立项必须显式确认；false 时后端 422 拒绝
    acknowledge_single_source: bool = False


class OpportunityStatusUpdate(BaseModel):
    """PATCH /opportunities/{id}/status — advance / reject / revive."""

    new_status: str
    note: Optional[str] = None      # REJECTED 时必填（端点校验）


class OpportunityDraftRequest(BaseModel):
    """POST /opportunities/draft — LLM 起草请求。"""

    cluster_id: int


class OpportunityRelinkRequest(BaseModel):
    """POST /opportunities/{id}/relink — 重新关联断链机会。

    cluster_id 缺省时自动匹配最合适的当前簇；显式指定则人工覆盖（Human-in-the-Loop）。
    """

    cluster_id: Optional[int] = None


class OpportunityAnalysisRead(BaseModel):
    """Serialized representation of an OpportunityAnalysis (LLM 可行性分析)。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    opportunity_id: int
    feasibility_score: Optional[float] = None
    technical_feasibility: Optional[str] = None
    market_feasibility: Optional[str] = None
    competition: Optional[str] = None
    risks: list[str] = []
    validation_hypotheses: list[str] = []
    action_items: list[str] = []
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("risks", "validation_hypotheses", "action_items", mode="before")
    @classmethod
    def _parse_json_list(cls, value):
        """DB 存 JSON 字符串，序列化时还原为 list。"""
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except (TypeError, ValueError):
                return []
        return []


class OpportunityRead(BaseModel):
    """Serialized representation of an Opportunity."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    cluster_id: Optional[int] = None     # rebuild 断链后为 null
    title: Optional[str] = None
    problem_statement: Optional[str] = None
    target_customer: Optional[str] = None
    proposed_solution: Optional[str] = None
    market_score: Optional[float] = None
    source_count: Optional[int] = None    # 立项时快照；rebuild 断链后仍可追溯
    validation_status: str
    priority: int
    rejection_note: Optional[str] = None
    analysis: Optional[OpportunityAnalysisRead] = None
    created_at: datetime
    updated_at: datetime


# --- TrendMetric ---


class TrendMetricRead(BaseModel):
    """GET /trends — 簇信号增长趋势（实时计算，不落 trend_metrics 表）。

    字段对齐前端 TrendMetric 类型：topic=簇名、metric_name=指标名、
    value=窗口内信号数、growth_rate=窗口增长率（前一窗口无信号时为 null）。
    """

    id: int
    topic: str
    metric_name: str
    value: int
    growth_rate: Optional[float] = None
    period: str
    created_at: datetime


# --- CrawlJob ---


class CrawlJobCreate(BaseModel):
    """Payload to create a new crawl job."""

    source_id: int


class CrawlJobRead(BaseModel):
    """Serialized representation of a CrawlJob."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    status: str
    items_found: int
    items_stored: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime