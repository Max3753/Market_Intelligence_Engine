import type {
  Source,
  SourceStats,
  Document,
  DemandSignal,
  Cluster,
  Opportunity,
  OpportunityAnalysis,
  TrendMetric,
  PaginatedResponse,
} from "@/types";

/** 统一 API 基址 —— 所有 fetch 都从这里取，禁止散落硬编码 */
export const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8106";

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

/**
 * 带 body 的请求封装（POST/PATCH）—— 非 2xx 抛出后端 detail 信息。
 * 供 client 组件（console / PromoteForm / 状态流转）复用。
 */
export async function api<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const detail = body?.detail;
    throw new Error(
      typeof detail === "string" ? detail : `API ${res.status}`
    );
  }
  return res.json() as Promise<T>;
}

export async function getSources(): Promise<Source[]> {
  return fetchJson<Source[]>("/sources");
}

export async function getSourceStats(): Promise<SourceStats[]> {
  return fetchJson<SourceStats[]>("/sources/stats");
}

export async function getDocuments(): Promise<Document[]> {
  return fetchJson<Document[]>("/documents");
}

export async function getDemands(): Promise<DemandSignal[]> {
  return fetchJson<DemandSignal[]>("/demands");
}

export async function getClusters(): Promise<Cluster[]> {
  return fetchJson<Cluster[]>("/clusters");
}

export async function getOpportunities(): Promise<Opportunity[]> {
  return fetchJson<Opportunity[]>("/opportunities");
}

/** 生成/重新生成机会可行性分析 —— POST /opportunities/{id}/analyze（无 body） */
export async function analyzeOpportunity(
  id: number
): Promise<OpportunityAnalysis> {
  return api<OpportunityAnalysis>(`/opportunities/${id}/analyze`, {
    method: "POST",
  });
}

export async function getTrends(): Promise<TrendMetric[]> {
  return fetchJson<TrendMetric[]>("/trends");
}
