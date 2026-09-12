"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowUpDown, X, Check, TriangleAlert, CheckCircle2, Sparkles, RefreshCw } from "lucide-react";
import StatusBadge, {
  STATUS_LABELS,
  STATUS_STYLES,
} from "@/components/StatusBadge";
import Badge from "@/components/Badge";
import EmptyState from "@/components/EmptyState";
import { api, analyzeOpportunity } from "@/lib/api";
import {
  cardCls,
  linkCls,
  secondaryBtnCls,
  dangerBtnCls,
  inputCls,
  focusRingCls,
} from "@/lib/ui";
import type { Opportunity, OpportunityAnalysis, ValidationStatus } from "@/types";

/** 显式状态流转表 —— 与后端 VALID_TRANSITIONS 对齐 */
const VALID_TRANSITIONS: Record<ValidationStatus, ValidationStatus[]> = {
  DISCOVERED: ["EVIDENCE_GATHERING", "HUMAN_REVIEW", "REJECTED", "DORMANT"],
  EVIDENCE_GATHERING: ["HUMAN_REVIEW", "INTERVIEW", "REJECTED", "DORMANT"],
  HUMAN_REVIEW: ["INTERVIEW", "REJECTED", "DORMANT"],
  INTERVIEW: ["VALIDATED", "REJECTED", "DORMANT"],
  VALIDATED: ["MVP", "REJECTED", "DORMANT"],
  MVP: ["EARLY_USERS", "DORMANT"],
  EARLY_USERS: ["PAID", "DORMANT"],
  PAID: ["SCALED", "DORMANT"],
  SCALED: [],
  REJECTED: [],
  DORMANT: ["DISCOVERED"],
};

type SortKey = "priority" | "market_score";

interface OpportunitiesListProps {
  opportunities: Opportunity[];
}

export default function OpportunitiesList({
  opportunities,
}: OpportunitiesListProps) {
  const router = useRouter();
  const [statusFilter, setStatusFilter] = useState<ValidationStatus | "all">(
    "all"
  );
  const [sortKey, setSortKey] = useState<SortKey>("priority");
  const [sortAsc, setSortAsc] = useState(false);
  const [transitioning, setTransitioning] = useState<{
    id: number;
    status: ValidationStatus;
  } | null>(null);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [analyzingId, setAnalyzingId] = useState<number | null>(null);

  // 过滤 + 排序
  const filtered = useMemo(() => {
    let list = opportunities;
    if (statusFilter !== "all") {
      list = list.filter((o) => o.validation_status === statusFilter);
    }
    const sorted = [...list].sort((a, b) => {
      const av = a[sortKey] ?? 0;
      const bv = b[sortKey] ?? 0;
      return sortAsc ? av - bv : bv - av;
    });
    return sorted;
  }, [opportunities, statusFilter, sortKey, sortAsc]);

  // 状态选项（按出现频率）
  const statusOptions = useMemo(() => {
    const counts = new Map<ValidationStatus, number>();
    for (const o of opportunities) {
      counts.set(
        o.validation_status,
        (counts.get(o.validation_status) ?? 0) + 1
      );
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [opportunities]);

  async function handleTransition(
    opp: Opportunity,
    newStatus: ValidationStatus
  ) {
    setError(null);
    setBusy(true);
    try {
      await api(`/opportunities/${opp.id}/status`, {
        method: "PATCH",
        body: JSON.stringify({
          new_status: newStatus,
          note: note.trim() || undefined,
        }),
      });
      setTransitioning(null);
      setNote("");
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "状态更新失败");
    } finally {
      setBusy(false);
    }
  }

  /** 生成/重新生成可行性分析 —— 成功后 router.refresh() 拉取最新 analysis */
  async function handleAnalyze(opp: Opportunity) {
    setError(null);
    setAnalyzingId(opp.id);
    try {
      await analyzeOpportunity(opp.id);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "分析生成失败");
    } finally {
      setAnalyzingId(null);
    }
  }

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc((v) => !v);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  }

  return (
    <>
      {/* 工具栏：状态筛选 + 排序 */}
      <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setStatusFilter("all")}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all duration-200 active:scale-[0.98] ${focusRingCls} ${
              statusFilter === "all"
                ? "bg-sky-500/20 text-sky-300 ring-1 ring-sky-400/30"
                : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-slate-200"
            }`}
          >
            全部
          </button>
          {statusOptions.map(([status, count]) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all duration-200 active:scale-[0.98] ${focusRingCls} ${
                statusFilter === status
                  ? "bg-sky-500/20 text-sky-300 ring-1 ring-sky-400/30"
                  : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-slate-200"
              }`}
            >
              {STATUS_LABELS[status] ?? status}
              <span className="ml-1 tabular-nums text-slate-500">{count}</span>
            </button>
          ))}
        </div>

        {/* 排序 */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-500">排序：</span>
          <button
            onClick={() => toggleSort("priority")}
            className={`flex items-center gap-1 rounded-lg px-2.5 py-1.5 font-medium transition-all duration-200 active:scale-[0.98] ${focusRingCls} ${
              sortKey === "priority"
                ? "bg-sky-500/20 text-sky-300 ring-1 ring-sky-400/30"
                : "bg-white/5 text-slate-400 hover:bg-white/10"
            }`}
          >
            优先级
            <ArrowUpDown className="h-3 w-3" />
          </button>
          <button
            onClick={() => toggleSort("market_score")}
            className={`flex items-center gap-1 rounded-lg px-2.5 py-1.5 font-medium transition-all duration-200 active:scale-[0.98] ${focusRingCls} ${
              sortKey === "market_score"
                ? "bg-sky-500/20 text-sky-300 ring-1 ring-sky-400/30"
                : "bg-white/5 text-slate-400 hover:bg-white/10"
            }`}
          >
            市场分
            <ArrowUpDown className="h-3 w-3" />
          </button>
          <span className="text-slate-500">
            {sortAsc ? "升序 ↑" : "降序 ↓"}
          </span>
        </div>
      </div>

      {/* 结果计数 */}
      <p className="mb-3 text-xs text-slate-500">
        共 <span className="tabular-nums text-slate-300">{filtered.length}</span>{" "}
        条机会
      </p>

      {/* 机会列表 */}
      {filtered.length === 0 ? (
        <EmptyState
          title="没有匹配的机会"
          description="试试调整状态筛选，或从候选簇升级新机会"
        />
      ) : (
        <div className="flex flex-col gap-3">
          {filtered.map((o) => (
            <div key={o.id} className={cardCls}>
              <div className="flex items-start justify-between gap-3">
                <h3 className="text-base font-semibold text-white">{o.title}</h3>
                <div className="flex shrink-0 flex-wrap items-center gap-2">
                  {o.source_count !== null && o.source_count !== undefined && (
                    o.source_count < 2 ? (
                      <Badge tone="warning">
                        <TriangleAlert className="h-3 w-3" />
                        单源
                      </Badge>
                    ) : (
                      <Badge tone="success">
                        <CheckCircle2 className="h-3 w-3" />
                        双源
                      </Badge>
                    )
                  )}
                  <StatusBadge status={o.validation_status} showLabel />
                </div>
              </div>

              {o.problem_statement && (
                <p className="mt-2 text-sm text-slate-300">{o.problem_statement}</p>
              )}

              <dl className="mt-3 space-y-1 text-xs text-slate-400">
                {o.target_customer && (
                  <div>
                    <dt className="inline text-slate-500">目标用户：</dt>
                    <dd className="inline">{o.target_customer}</dd>
                  </div>
                )}
                {o.proposed_solution && (
                  <div>
                    <dt className="inline text-slate-500">方案设想：</dt>
                    <dd className="inline">{o.proposed_solution}</dd>
                  </div>
                )}
              </dl>

              {/* 总结反馈 —— 可行性分析 */}
              <div className="mt-3 border-t border-white/5 pt-3">
                {o.analysis ? (
                  <AnalysisBlock
                    analysis={o.analysis}
                    analyzing={analyzingId === o.id}
                    onRegenerate={() => void handleAnalyze(o)}
                  />
                ) : (
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs text-slate-500">
                      尚未生成可行性分析
                    </p>
                    <button
                      onClick={() => void handleAnalyze(o)}
                      disabled={analyzingId !== null}
                      className={`rounded-lg bg-sky-500 px-3 py-1 text-xs font-medium text-white transition-all duration-200 hover:bg-sky-400 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed ${focusRingCls}`}
                    >
                      {analyzingId === o.id ? (
                        "分析中…"
                      ) : (
                        <>
                          <Sparkles className="mr-1 inline h-3.5 w-3.5" />
                          生成可行性分析
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>

              {(o.validation_status === "REJECTED" ||
                o.validation_status === "DORMANT") &&
                o.rejection_note && (
                  <p className="mt-3 rounded-lg border-l-2 border-red-400/40 bg-red-400/5 px-3 py-2 text-xs italic text-slate-400">
                    {o.rejection_note}
                  </p>
                )}

              {/* 状态流转 UI */}
              <div className="mt-3 border-t border-white/5 pt-3">
                {transitioning?.id === o.id ? (
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs text-slate-500">
                        流转到：
                      </span>
                      {VALID_TRANSITIONS[o.validation_status].map((s) => (
                        <button
                          key={s}
                          onClick={() => void handleTransition(o, s)}
                          disabled={busy}
                          className={`rounded-md px-2 py-1 text-xs font-medium transition-all duration-200 ${focusRingCls} ${
                            STATUS_STYLES[s] ??
                            "bg-slate-400/10 text-slate-300 ring-1 ring-slate-400/20"
                          } hover:opacity-80`}
                        >
                          {STATUS_LABELS[s] ?? s}
                        </button>
                      ))}
                      <button
                        onClick={() => {
                          setTransitioning(null);
                          setNote("");
                          setError(null);
                        }}
                        className="rounded-md p-1 text-slate-500 transition-colors hover:bg-white/10 hover:text-white"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                    {(o.validation_status === "REJECTED" ||
                      o.validation_status === "DORMANT" ||
                      VALID_TRANSITIONS[o.validation_status].includes(
                        "REJECTED"
                      )) && (
                      <input
                        value={note}
                        onChange={(e) => setNote(e.target.value)}
                        placeholder="流转理由（否决必填）…"
                        className={inputCls + " !py-1.5 text-xs"}
                      />
                    )}
                    {error && (
                      <p className="text-xs text-red-300">{error}</p>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 text-xs text-slate-500">
                      {o.cluster_id ? (
                        <Link
                          href={`/clusters/${o.cluster_id}`}
                          className={linkCls}
                        >
                          查看来源簇 #{o.cluster_id} →
                        </Link>
                      ) : (
                        <span>来源簇已随重建解绑</span>
                      )}
                      <span className="tabular-nums">
                        market_score 快照 {o.market_score?.toFixed(1) ?? "—"}
                      </span>
                    </div>
                    {VALID_TRANSITIONS[o.validation_status].length > 0 && (
                      <button
                        onClick={() => {
                          setTransitioning({ id: o.id, status: o.validation_status });
                          setError(null);
                        }}
                        className={secondaryBtnCls + " !px-2.5 !py-1 text-xs"}
                      >
                        <Check className="mr-1 inline h-3 w-3" />
                        流转状态
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

/** 可行性分析展示区块 —— 评分 + 总结 + 三维度 + 风险/假设/行动 */
function AnalysisBlock({
  analysis,
  analyzing,
  onRegenerate,
}: {
  analysis: OpportunityAnalysis;
  analyzing: boolean;
  onRegenerate: () => void;
}) {
  const [showDims, setShowDims] = useState(false);

  const score = analysis.feasibility_score;

  return (
    <div className="space-y-3">
      {/* 头部：评分 + 重新生成 */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium text-slate-500">总结反馈</span>
          {score !== null && (
            <span className="inline-flex items-baseline gap-1 rounded-lg bg-violet-400/10 px-2.5 py-1 ring-1 ring-violet-400/20">
              <span className="text-lg font-semibold tabular-nums text-violet-300">
                {score.toFixed(0)}
              </span>
              <span className="text-xs text-violet-400/70">可行性评分</span>
            </span>
          )}
        </div>
        <button
          onClick={onRegenerate}
          disabled={analyzing}
          className={`rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-200 transition-all duration-200 hover:bg-white/10 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed ${focusRingCls}`}
        >
          {analyzing ? (
            "分析中…"
          ) : (
            <>
              <RefreshCw className="mr-1 inline h-3 w-3" />
              重新生成
            </>
          )}
        </button>
      </div>

      {/* 总结正文 */}
      {analysis.summary && (
        <p className="text-sm leading-relaxed text-slate-300">
          {analysis.summary}
        </p>
      )}

      {/* 技术 / 市场 / 竞争 三维度（可折叠） */}
      {(analysis.technical_feasibility ||
        analysis.market_feasibility ||
        analysis.competition) && (
        <div className="rounded-lg border border-white/5 bg-slate-900/40">
          <button
            onClick={() => setShowDims((v) => !v)}
            className={`flex w-full items-center justify-between px-3 py-2 text-xs font-medium text-slate-300 transition-colors hover:text-white ${focusRingCls}`}
          >
            <span>可行性维度</span>
            <span className="text-slate-500">{showDims ? "收起" : "展开"}</span>
          </button>
          {showDims && (
            <div className="space-y-2 border-t border-white/5 px-3 py-2 text-xs text-slate-400">
              {analysis.technical_feasibility && (
                <div>
                  <span className="font-medium text-slate-300">技术可行性：</span>
                  {analysis.technical_feasibility}
                </div>
              )}
              {analysis.market_feasibility && (
                <div>
                  <span className="font-medium text-slate-300">市场可行性：</span>
                  {analysis.market_feasibility}
                </div>
              )}
              {analysis.competition && (
                <div>
                  <span className="font-medium text-slate-300">竞争格局：</span>
                  {analysis.competition}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 风险清单（红色系） */}
      {analysis.risks.length > 0 && (
        <div className="rounded-lg border-l-2 border-red-400/40 bg-red-400/5 px-3 py-2">
          <p className="mb-1 text-xs font-medium text-red-300">风险</p>
          <ul className="space-y-1">
            {analysis.risks.map((r, i) => (
              <li key={i} className="flex items-start gap-1.5 text-xs text-slate-400">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-red-400/60" />
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 待验证假设 */}
      {analysis.validation_hypotheses.length > 0 && (
        <div className="rounded-lg border-l-2 border-amber-400/40 bg-amber-400/5 px-3 py-2">
          <p className="mb-1 text-xs font-medium text-amber-300">待验证假设</p>
          <ul className="space-y-1">
            {analysis.validation_hypotheses.map((h, i) => (
              <li key={i} className="flex items-start gap-1.5 text-xs text-slate-400">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-amber-400/60" />
                {h}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 行动建议（绿色系） */}
      {analysis.action_items.length > 0 && (
        <div className="rounded-lg border-l-2 border-emerald-400/40 bg-emerald-400/5 px-3 py-2">
          <p className="mb-1 text-xs font-medium text-emerald-300">行动建议</p>
          <ul className="space-y-1">
            {analysis.action_items.map((a, i) => (
              <li key={i} className="flex items-start gap-1.5 text-xs text-slate-400">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-emerald-400/60" />
                {a}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 更新时间 */}
      <p className="text-[11px] text-slate-600">
        更新于{" "}
        <span className="tabular-nums">
          {new Date(analysis.updated_at).toLocaleString("zh-CN")}
        </span>
      </p>
    </div>
  );
}
