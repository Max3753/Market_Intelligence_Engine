"use client";

import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ChevronLeft, ChevronRight, Search } from "lucide-react";
import DemandTypeBadge, {
  DEMAND_TYPE_LABELS,
} from "@/components/DemandTypeBadge";
import EmptyState from "@/components/EmptyState";
import {
  inputCls,
  secondaryBtnCls,
  focusRingCls,
  tableWrapCls,
  thCls,
  trCls,
  tdCls,
} from "@/lib/ui";
import type { DemandSignal, DemandType } from "@/types";

const PAGE_SIZE = 10;

/** pain_points 在后端是 JSON 字符串（Text 列）—— 安全解析成数组 */
function parsePainPoints(raw: string | null): string[] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

/** 严重度色条 */
function SeverityBar({ value }: { value: number | null }) {
  if (value === null || value === undefined) return <span className="text-slate-500">—</span>;
  const pct = Math.min(100, Math.max(0, value * 10));
  const color =
    value >= 7 ? "bg-red-400" : value >= 4 ? "bg-amber-400" : "bg-emerald-400";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-white/10">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="tabular-nums text-xs text-slate-400">{value}</span>
    </div>
  );
}

interface DemandsTableProps {
  demands: DemandSignal[];
}

export default function DemandsTable({ demands }: DemandsTableProps) {
  const [typeFilter, setTypeFilter] = useState<DemandType | "all">("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<DemandSignal | null>(null);

  // 过滤 + 搜索
  const filtered = useMemo(() => {
    let list = demands;
    if (typeFilter !== "all") {
      list = list.filter((d) => d.demand_type === typeFilter);
    }
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      list = list.filter(
        (d) =>
          d.problem?.toLowerCase().includes(q) ||
          d.job_to_be_done?.toLowerCase().includes(q) ||
          d.desired_outcome?.toLowerCase().includes(q)
      );
    }
    return list;
  }, [demands, typeFilter, search]);

  // 分页
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pageItems = filtered.slice(
    (safePage - 1) * PAGE_SIZE,
    safePage * PAGE_SIZE
  );

  // 类型选项（按出现频率排序）
  const typeOptions = useMemo(() => {
    const counts = new Map<DemandType, number>();
    for (const d of demands) {
      counts.set(d.demand_type, (counts.get(d.demand_type) ?? 0) + 1);
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [demands]);

  return (
    <>
      {/* 工具栏：筛选 + 搜索 */}
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => {
              setTypeFilter("all");
              setPage(1);
            }}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all duration-200 active:scale-[0.98] ${focusRingCls} ${
              typeFilter === "all"
                ? "bg-sky-500/20 text-sky-300 ring-1 ring-sky-400/30"
                : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-slate-200"
            }`}
          >
            全部
          </button>
          {typeOptions.map(([type, count]) => (
            <button
              key={type}
              onClick={() => {
                setTypeFilter(type);
                setPage(1);
              }}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all duration-200 active:scale-[0.98] ${focusRingCls} ${
                typeFilter === type
                  ? "bg-sky-500/20 text-sky-300 ring-1 ring-sky-400/30"
                  : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-slate-200"
              }`}
            >
              {DEMAND_TYPE_LABELS[type] ?? type}
              <span className="ml-1 tabular-nums text-slate-500">{count}</span>
            </button>
          ))}
        </div>
        <div className="relative sm:w-64">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="搜索问题 / 任务 / 期望…"
            className={`${inputCls} pl-9`}
          />
        </div>
      </div>

      {/* 结果计数 */}
      <p className="mb-3 text-xs text-slate-500">
        共 <span className="tabular-nums text-slate-300">{filtered.length}</span>{" "}
        条需求信号
      </p>

      {/* 表格（桌面端） */}
      {pageItems.length === 0 ? (
        <EmptyState
          title="没有匹配的需求信号"
          description="试试调整类型筛选或搜索关键词"
        />
      ) : (
        <>
          <div className={`hidden ${tableWrapCls} md:block`}>
            <table className="w-full text-left text-sm">
              <thead className="border-b border-white/5 text-slate-500">
                <tr>
                  <th className={thCls}>ID</th>
                  <th className={thCls}>类型</th>
                  <th className={thCls}>问题描述</th>
                  <th className={thCls}>严重度</th>
                  <th className={thCls}>置信度</th>
                  <th className={thCls}>所属簇</th>
                </tr>
              </thead>
              <tbody>
                {pageItems.map((d) => (
                  <tr
                    key={d.id}
                    onClick={() => setSelected(d)}
                    className={`cursor-pointer ${trCls}`}
                  >
                    <td className={`${tdCls} tabular-nums text-slate-400`}>
                      {d.id}
                    </td>
                    <td className={tdCls}>
                      <DemandTypeBadge type={d.demand_type} showLabel />
                    </td>
                    <td className={`max-w-md ${tdCls}`}>
                      <span className="line-clamp-1">{d.problem ?? "—"}</span>
                      {parsePainPoints(d.pain_points).length > 0 && (
                        <div className="mt-1 flex flex-wrap gap-1">
                          {parsePainPoints(d.pain_points)
                            .slice(0, 3)
                            .map((p, i) => (
                              <span
                                key={i}
                                className="rounded-md bg-white/5 px-1.5 py-0.5 text-xs text-slate-400"
                              >
                                {p}
                              </span>
                            ))}
                        </div>
                      )}
                    </td>
                    <td className={tdCls}>
                      <SeverityBar value={d.severity} />
                    </td>
                    <td className={`${tdCls} tabular-nums`}>
                      {d.confidence?.toFixed(2) ?? "—"}
                    </td>
                    <td className={`${tdCls} tabular-nums text-slate-400`}>
                      {d.cluster_id ? `#${d.cluster_id}` : "未聚类"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 卡片列表（移动端） */}
          <div className="space-y-3 md:hidden">
            {pageItems.map((d) => (
              <button
                key={d.id}
                onClick={() => setSelected(d)}
                className={`w-full rounded-xl border border-white/5 bg-slate-800/60 p-4 text-left shadow-lg shadow-black/20 transition-all duration-200 hover:border-white/10 ${focusRingCls}`}
              >
                <div className="flex items-center justify-between">
                  <DemandTypeBadge type={d.demand_type} showLabel />
                  <span className="tabular-nums text-xs text-slate-500">
                    #{d.id}
                  </span>
                </div>
                <p className="mt-2 text-sm text-slate-200 line-clamp-2">
                  {d.problem ?? "—"}
                </p>
                <div className="mt-2 flex items-center gap-4 text-xs text-slate-500">
                  <SeverityBar value={d.severity} />
                  <span className="tabular-nums">
                    置信 {d.confidence?.toFixed(2) ?? "—"}
                  </span>
                </div>
              </button>
            ))}
          </div>

          {/* 分页 */}
          <div className="mt-4 flex items-center justify-between">
            <span className="text-xs text-slate-500">
              第 <span className="tabular-nums text-slate-300">{safePage}</span> /{" "}
              <span className="tabular-nums text-slate-300">{totalPages}</span>{" "}
              页
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={safePage <= 1}
                className={secondaryBtnCls + " px-2.5 py-1.5"}
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={safePage >= totalPages}
                className={secondaryBtnCls + " px-2.5 py-1.5"}
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </>
      )}

      {/* 详情抽屉 */}
      <AnimatePresence>
        {selected && (
          <>
            {/* 遮罩 */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelected(null)}
              className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
            />
            {/* 抽屉 */}
            <motion.aside
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "tween", duration: 0.25, ease: "easeOut" }}
              className="fixed right-0 top-0 z-50 flex h-full w-full max-w-md flex-col border-l border-white/10 bg-slate-900/95 shadow-2xl backdrop-blur"
            >
              <div className="flex items-center justify-between border-b border-white/5 px-5 py-4">
                <div className="flex items-center gap-2">
                  <DemandTypeBadge type={selected.demand_type} showLabel />
                  <span className="tabular-nums text-xs text-slate-500">
                    #{selected.id}
                  </span>
                </div>
                <button
                  onClick={() => setSelected(null)}
                  className={`rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-white/10 hover:text-white ${focusRingCls}`}
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="flex-1 space-y-5 overflow-y-auto px-5 py-5">
                {/* 问题 */}
                <div>
                  <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500">
                    问题描述
                  </h3>
                  <p className="mt-1.5 text-sm text-slate-200">
                    {selected.problem ?? "—"}
                  </p>
                </div>

                {/* 痛点 */}
                {parsePainPoints(selected.pain_points).length > 0 && (
                  <div>
                    <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500">
                      痛点
                    </h3>
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      {parsePainPoints(selected.pain_points).map((p, i) => (
                        <span
                          key={i}
                          className="rounded-md bg-white/5 px-2 py-1 text-xs text-slate-300"
                        >
                          {p}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* 待办任务 */}
                {selected.job_to_be_done && (
                  <div>
                    <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500">
                      Job to be done
                    </h3>
                    <p className="mt-1.5 text-sm text-slate-200">
                      {selected.job_to_be_done}
                    </p>
                  </div>
                )}

                {/* 期望结果 */}
                {selected.desired_outcome && (
                  <div>
                    <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500">
                      期望结果
                    </h3>
                    <p className="mt-1.5 text-sm text-slate-200">
                      {selected.desired_outcome}
                    </p>
                  </div>
                )}

                {/* 当前方案 */}
                {selected.current_solution && (
                  <div>
                    <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500">
                      当前方案
                    </h3>
                    <p className="mt-1.5 text-sm text-slate-200">
                      {selected.current_solution}
                    </p>
                  </div>
                )}

                {/* 评分 */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="rounded-lg bg-white/[0.03] p-3">
                    <p className="text-xs text-slate-500">严重度</p>
                    <p className="mt-1 text-lg font-semibold tabular-nums text-white">
                      {selected.severity ?? "—"}
                    </p>
                  </div>
                  <div className="rounded-lg bg-white/[0.03] p-3">
                    <p className="text-xs text-slate-500">付费意愿</p>
                    <p className="mt-1 text-lg font-semibold tabular-nums text-white">
                      {selected.willingness_to_pay ?? "—"}
                    </p>
                  </div>
                  <div className="rounded-lg bg-white/[0.03] p-3">
                    <p className="text-xs text-slate-500">证据强度</p>
                    <p className="mt-1 text-lg font-semibold tabular-nums text-white">
                      {selected.evidence_strength ?? "—"}
                    </p>
                  </div>
                </div>

                {/* 元信息 */}
                <div className="space-y-1.5 text-xs text-slate-500">
                  <div className="flex justify-between">
                    <span>置信度</span>
                    <span className="tabular-nums text-slate-300">
                      {selected.confidence?.toFixed(2) ?? "—"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>所属簇</span>
                    <span className="tabular-nums text-slate-300">
                      {selected.cluster_id ? `#${selected.cluster_id}` : "未聚类"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>文档 ID</span>
                    <span className="tabular-nums text-slate-300">
                      #{selected.document_id}
                    </span>
                  </div>
                </div>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
