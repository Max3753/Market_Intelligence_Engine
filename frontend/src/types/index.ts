/* ================================================================
 * Market Intelligence Engine — 前端类型定义
 * 与后端 Section 23 数据库 schema 对齐
 * ================================================================ */

/** 数据来源 (Section 23.1) */
export interface Source {
  id: number;
  name: string;
  type: string;
  base_url: string;
  status: string;
  crawl_interval: string;
  created_at: string;
  updated_at: string;
}

/** 数据源统计（GET /sources/stats）—— 健康度 + 信号产出 + 爬取统计 */
export interface SourceStats {
  id: number;
  name: string;
  type: string;
  status: string;
  config: Record<string, unknown> | null;
  last_crawl_at: string | null;
  last_success_at: string | null;
  consecutive_failures: number;
  avg_latency: number | null;
  document_count: number;
  signal_count: number;
  signal_yield: number;
  job_total: number;
  job_success_rate: number;
  job_avg_latency: number | null;
  dedup_rate: number;
}

/** 已爬取文档 (Section 23.2) */
export interface Document {
  id: number;
  source_id: number;
  source_item_id: string;
  url: string;
  canonical_url: string;
  title: string;
  content: string;
  author_id: number | null;
  published_at: string;
  engagement_score: number;
  language: string;
  content_hash: string;
  created_at: string;
  updated_at: string;
}

/** 需求信号 (Section 23.3) */
export type DemandType =
  | "pain"
  | "feature_request"
  | "complaint"
  | "workaround"
  | "buying_intent"
  | "alternative_search"
  | "price_complaint"
  | "churn_signal"
  | "unmet_need"
  | "general_discussion"
  | "noise";

export interface DemandSignal {
  id: number;
  document_id: number;
  demand_type: DemandType;
  problem: string | null;
  pain_points: string | null;
  job_to_be_done: string | null;
  desired_outcome: string | null;
  current_solution: string | null;
  severity: number | null;
  willingness_to_pay: number | null;
  evidence_strength: number | null;
  confidence: number | null;
  cluster_id: number | null;
  created_at: string;
}

/** 需求聚类 (Section 23.4) */
export interface Cluster {
  id: number;
  name: string;
  description: string | null;
  user_segment: string | null;
  document_count: number | null;
  unique_user_count: number | null;
  source_count: number;   // 独立数据源数；<2 = 单源待交叉验证
  pain_score: number | null;
  frequency_score: number | null;
  money_score: number | null;
  growth_score: number | null;
  competition_gap: number | null;
  demand_score: number | null;
  created_at: string;
  updated_at: string;
}

/** 产品机会 (Section 23.5) */
export type ValidationStatus =
  | "DISCOVERED"
  | "EVIDENCE_GATHERING"
  | "HUMAN_REVIEW"
  | "INTERVIEW"
  | "VALIDATED"
  | "MVP"
  | "EARLY_USERS"
  | "PAID"
  | "SCALED"
  | "REJECTED"
  | "DORMANT";

/** 机会可行性分析 (opportunity_analyses 表) —— GET /opportunities 内嵌，可为 null */
export interface OpportunityAnalysis {
  id: number;
  opportunity_id: number;
  feasibility_score: number | null;      // 0-100 可实现性评分
  technical_feasibility: string | null;  // 技术可行性
  market_feasibility: string | null;     // 市场可行性
  competition: string | null;            // 竞争格局
  risks: string[];                       // 风险清单
  validation_hypotheses: string[];       // 待验证假设
  action_items: string[];                // 行动建议
  summary: string | null;                // 总结反馈正文
  created_at: string;
  updated_at: string;
}

export interface Opportunity {
  id: number;
  cluster_id: number | null;   // rebuild 断链后为 null
  title: string;
  problem_statement: string;
  target_customer: string;
  proposed_solution: string;
  market_score: number | null;
  source_count: number | null;   // 立项时快照；rebuild 断链后仍可追溯
  validation_status: ValidationStatus;
  priority: number;
  rejection_note: string | null;
  analysis: OpportunityAnalysis | null;   // 可行性分析；未生成时为 null
  created_at: string;
  updated_at: string;
}

/** 趋势指标 (Section 23 — trend_metrics) */
export interface TrendMetric {
  id: number;
  topic: string;
  metric_name: string;
  value: number;
  growth_rate: number;
  period: string;
  created_at: string;
}

/** 证据 (evidences 表) */
export interface Evidence {
  id: number;
  demand_signal_id: number;
  document_id: number;
  snippet: string | null;
  relevance_score: number | null;
  evidence_type: string | null;
  created_at: string;
}

/** 通用分页响应 (部分 API 可能返回此格式) */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
