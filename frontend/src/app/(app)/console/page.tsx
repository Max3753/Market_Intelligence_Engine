"use client";

/**
 * 运营控制台 —— 抓取 / 分析 / 聚类评分 / 数据源管理。
 * 已绑定真实后端 API；破坏性操作走两步确认。
 * 设计遵循 frontend/DESIGN.md。
 */
import { useCallback, useEffect, useState } from "react";
import { Download, FlaskConical, Boxes, Plus } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import SectionTitle from "@/components/SectionTitle";
import EmptyState from "@/components/EmptyState";
import { api } from "@/lib/api";
import {
  inputCls,
  primaryBtnCls,
  dangerBtnCls,
  secondaryBtnCls,
  successBtnCls,
} from "@/lib/ui";

// ---- 类型 ----
interface SourceItem {
  id: number;
  name: string;
  type: string;
  status: string;
  // 健康度（P1）
  last_crawl_at: string | null;
  last_success_at: string | null;
  consecutive_failures: number;
  avg_latency: number | null;
  // 信号产出（源质量反馈）
  document_count: number;
  signal_count: number;
  signal_yield: number;
  // 爬取统计
  job_total: number;
  job_success_rate: number;
  job_avg_latency: number | null;
  dedup_rate: number;
}

interface JobItem {
  id: number;
  source_id: number;
  status: string;
  items_found: number | null;
  items_stored: number | null;
  error_message: string | null;
  created_at: string;
}

interface Msg {
  ok: boolean;
  text: string;
}

/** 相对时间格式化（中文）—— "3 分钟前" / "2 小时前" / "昨天" */
function formatRelativeTime(iso: string | null): string {
  if (!iso) return "—";
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 0) return "刚刚";
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "刚刚";
  if (mins < 60) return `${mins} 分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} 小时前`;
  const days = Math.floor(hours / 24);
  if (days === 1) return "昨天";
  if (days < 30) return `${days} 天前`;
  const months = Math.floor(days / 30);
  return `${months} 个月前`;
}

/**
 * 相对时间组件 —— SSR 时显示占位，挂载后再计算。
 * 避免 Date.now() 在服务端渲染与客户端 hydration 时值不同导致的 mismatch。
 */
function RelativeTime({ iso }: { iso: string | null }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  if (!mounted) return <span>—</span>;
  return <span>{formatRelativeTime(iso)}</span>;
}

// ---- 状态徽章样式（低饱和 + 光晕，见 DESIGN.md）----
const JOB_STATUS_STYLES: Record<string, string> = {
  completed:
    "bg-emerald-400/10 text-emerald-300 ring-1 ring-emerald-400/20",
  running:
    "bg-sky-400/10 text-sky-300 ring-1 ring-sky-400/20 animate-pulse",
  failed: "bg-red-400/10 text-red-300 ring-1 ring-red-400/20",
  pending: "bg-slate-400/10 text-slate-300 ring-1 ring-slate-400/20",
};

const SOURCE_TYPE_OPTIONS = ["hackernews", "github", "v2ex", "reddit", "juejin", "zhihu"];

/** 源健康度：绿=健康 / 黄=告警 / 红=异常 / 灰=未知 */
function healthOf(s: SourceItem): { dot: string; label: string } {
  if (s.consecutive_failures >= 3) return { dot: "bg-red-400", label: "异常" };
  if (s.consecutive_failures > 0) return { dot: "bg-amber-400", label: "告警" };
  if (s.last_success_at) return { dot: "bg-emerald-400", label: "健康" };
  return { dot: "bg-slate-400", label: "未知" };
}

/** 二次确认按钮 —— 第一次点击进入待确认态，再点才执行 */
function ConfirmButton({
  label,
  confirmLabel,
  hint,
  busy,
  onConfirm,
}: {
  label: string;
  confirmLabel: string;
  hint: string;
  busy: boolean;
  onConfirm: () => void;
}) {
  const [armed, setArmed] = useState(false);
  if (!armed) {
    return (
      <button
        onClick={() => setArmed(true)}
        disabled={busy}
        className={secondaryBtnCls}
      >
        {label}
      </button>
    );
  }
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs text-amber-300">{hint}</span>
      <button
        onClick={() => {
          setArmed(false);
          onConfirm();
        }}
        disabled={busy}
        className={dangerBtnCls}
      >
        {confirmLabel}
      </button>
      <button
        onClick={() => setArmed(false)}
        className={secondaryBtnCls}
      >
        取消
      </button>
    </div>
  );
}

/** 消息提示条 */
function MsgBanner({ msg }: { msg: Msg | null }) {
  if (!msg) return null;
  return (
    <div
      className={`mt-3 flex items-start gap-2 rounded-lg border px-3 py-2 text-xs ${
        msg.ok
          ? "border-emerald-400/20 bg-emerald-400/5 text-emerald-300"
          : "border-red-400/20 bg-red-400/5 text-red-300"
      }`}
    >
      <span className="mt-px">{msg.ok ? "✓" : "✕"}</span>
      <span>{msg.text}</span>
    </div>
  );
}

export default function ConsolePage() {
  // 数据
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [jobFilter, setJobFilter] = useState("all");

  // 抓取区
  const [selectedSource, setSelectedSource] = useState("");
  const [crawling, setCrawling] = useState(false);
  const [crawlMsg, setCrawlMsg] = useState<Msg | null>(null);

  // 分析区
  const [docId, setDocId] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [batchAnalyzing, setBatchAnalyzing] = useState(false);
  const [analyzeMsg, setAnalyzeMsg] = useState<Msg | null>(null);

  // 聚类/评分区
  const [rebuilding, setRebuilding] = useState(false);
  const [rescoring, setRescoring] = useState(false);
  const [opMsg, setOpMsg] = useState<Msg | null>(null);

  // 数据源表单
  const [srcName, setSrcName] = useState("");
  const [srcType, setSrcType] = useState("hackernews");
  const [srcUrl, setSrcUrl] = useState("");
  const [addingSource, setAddingSource] = useState(false);
  const [srcMsg, setSrcMsg] = useState<Msg | null>(null);

  // ---- 取数 ----
  const refreshSources = useCallback(async () => {
    try {
      // /sources/stats 带健康度 + 信号产出 + 爬取统计（比 /sources 信息更全）
      setSources(await api<SourceItem[]>("/sources/stats"));
    } catch (e) {
      setSrcMsg({ ok: false, text: e instanceof Error ? e.message : "加载失败" });
    }
  }, []);

  const refreshJobs = useCallback(async () => {
    try {
      setJobs(await api<JobItem[]>("/crawl/jobs"));
    } catch {
      /* 任务表加载失败不阻塞页面 */
    }
  }, []);

  useEffect(() => {
    void refreshSources();
    void refreshJobs();
  }, [refreshSources, refreshJobs]);

  const filteredJobs =
    jobFilter === "all" ? jobs : jobs.filter((j) => j.status === jobFilter);

  // ---- handlers ----
  async function handleCrawl() {
    if (!selectedSource) return;
    setCrawling(true);
    setCrawlMsg(null);
    try {
      const job = await api<JobItem>("/crawl/jobs", {
        method: "POST",
        body: JSON.stringify({ source_id: Number(selectedSource) }),
      });
      setCrawlMsg({ ok: true, text: `任务 #${job.id} 已启动，后台执行中` });
      await refreshJobs();
      // 任务是异步的——10 秒后刷新一次看结果
      setTimeout(() => void refreshJobs(), 10000);
    } catch (e) {
      setCrawlMsg({ ok: false, text: e instanceof Error ? e.message : "启动失败" });
    } finally {
      setCrawling(false);
    }
  }

  async function handleAnalyzeOne() {
    if (!docId.trim()) return;
    setAnalyzing(true);
    setAnalyzeMsg(null);
    try {
      const signal = await api<{ demand_type: string; severity: number | null }>(
        `/documents/${docId.trim()}/analyze`,
        { method: "POST" }
      );
      setAnalyzeMsg({
        ok: true,
        text: `文档 #${docId} → ${signal.demand_type}（severity ${signal.severity ?? "—"}）`,
      });
    } catch (e) {
      setAnalyzeMsg({ ok: false, text: e instanceof Error ? e.message : "分析失败" });
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleBatch() {
    setBatchAnalyzing(true);
    setAnalyzeMsg(null);
    try {
      const s = await api<{
        candidates: number;
        signals_created: number;
        skipped_lowvalue: number;
        failed: number;
      }>("/documents/analyze-batch", { method: "POST" });
      setAnalyzeMsg({
        ok: s.failed === 0,
        text: `批量完成：候选 ${s.candidates} · 新信号 ${s.signals_created} · 低价值跳过 ${s.skipped_lowvalue} · 失败 ${s.failed}`,
      });
    } catch (e) {
      setAnalyzeMsg({ ok: false, text: e instanceof Error ? e.message : "批量分析失败" });
    } finally {
      setBatchAnalyzing(false);
    }
  }

  async function handleRebuild() {
    setRebuilding(true);
    setOpMsg(null);
    try {
      const r = await api<{ clusters_built: number; noise_signals: number }>(
        "/clusters/rebuild",
        { method: "POST" }
      );
      setOpMsg({ ok: true, text: `重建完成：${r.clusters_built} 簇 · ${r.noise_signals} 噪声点` });
    } catch (e) {
      setOpMsg({ ok: false, text: e instanceof Error ? e.message : "重建失败" });
    } finally {
      setRebuilding(false);
    }
  }

  async function handleRescore() {
    setRescoring(true);
    setOpMsg(null);
    try {
      const r = await api<{ scored: number }>("/clusters/rescore", { method: "POST" });
      setOpMsg({ ok: true, text: `已评分 ${r.scored} 个簇` });
    } catch (e) {
      setOpMsg({ ok: false, text: e instanceof Error ? e.message : "评分失败" });
    } finally {
      setRescoring(false);
    }
  }

  async function handleAddSource(e: React.FormEvent) {
    e.preventDefault();
    setAddingSource(true);
    setSrcMsg(null);
    try {
      const s = await api<SourceItem>("/sources", {
        method: "POST",
        body: JSON.stringify({
          name: srcName,
          type: srcType,
          base_url: srcUrl || null,
        }),
      });
      setSrcMsg({ ok: true, text: `数据源「${s.name}」已添加` });
      setSrcName("");
      setSrcUrl("");
      await refreshSources();
    } catch (err) {
      setSrcMsg({ ok: false, text: err instanceof Error ? err.message : "添加失败" });
    } finally {
      setAddingSource(false);
    }
  }

  const sourceName = (id: number) =>
    sources.find((s) => s.id === id)?.name ?? `source#${id}`;

  return (
    <>
      <PageHeader title="Console" subtitle="运营控制台 · 抓取 / 分析 / 聚类 / 数据源" />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* ── 📥 抓取区 ── */}
        <section className="rounded-xl border border-white/5 bg-slate-800/60 p-5 shadow-lg shadow-black/20">
          <SectionTitle icon={<Download className="h-4 w-4 text-sky-400" />}>数据抓取</SectionTitle>

          <div className="mt-4 flex items-end gap-2">
            <div className="flex-1">
              <label className="mb-1.5 block text-xs font-medium text-slate-400">数据源</label>
              <select
                value={selectedSource}
                onChange={(e) => setSelectedSource(e.target.value)}
                className={inputCls}
              >
                <option value="">选择数据源…</option>
                {sources.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.type})
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={() => void handleCrawl()}
              disabled={crawling || !selectedSource}
              className={primaryBtnCls}
            >
              {crawling ? "启动中…" : "启动爬取"}
            </button>
          </div>
          <MsgBanner msg={crawlMsg} />

          <h3 className="mb-2 mt-5 text-xs font-medium uppercase tracking-wider text-slate-500">
            最近任务
          </h3>
          {/* 状态过滤 tabs */}
          <div className="mb-3 flex gap-1">
            {(
              [
                ["all", "全部"],
                ["running", "运行中"],
                ["completed", "完成"],
                ["failed", "失败"],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setJobFilter(key)}
                className={`rounded-md px-2.5 py-1 text-xs font-medium transition-all duration-200 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400/50 ${
                  jobFilter === key
                    ? "bg-sky-400/10 text-sky-300 ring-1 ring-sky-400/20"
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-300"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          {jobs.length === 0 ? (
            <EmptyState
              variant="inline"
              title="暂无爬取任务"
              description="在上方选择数据源并启动爬取，任务会显示在这里"
              icon={<Download className="h-5 w-5" />}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-white/5 text-slate-500">
                  <tr>
                    <th className="py-2 pr-2 font-medium">ID</th>
                    <th className="py-2 pr-2 font-medium">来源</th>
                    <th className="py-2 pr-2 font-medium">状态</th>
                    <th className="py-2 pr-2 font-medium">发现/入库</th>
                    <th className="py-2 font-medium">时间</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredJobs.map((j) => (
                    <tr key={j.id} className="border-b border-white/5 transition-colors hover:bg-white/[0.02]" title={j.error_message ?? ""}>
                      <td className="py-2 pr-2 tabular-nums text-slate-400">#{j.id}</td>
                      <td className="py-2 pr-2 text-slate-200">{sourceName(j.source_id)}</td>
                      <td className="py-2 pr-2">
                        <span className={`rounded-md px-2 py-0.5 text-xs font-medium ${JOB_STATUS_STYLES[j.status] ?? "bg-slate-400/10 text-slate-300 ring-1 ring-slate-400/20"}`}>
                          {j.status}
                        </span>
                      </td>
                      <td className="py-2 pr-2 tabular-nums text-slate-400">
                        {j.items_found ?? 0} / {j.items_stored ?? 0}
                      </td>
                      <td className="py-2 tabular-nums text-slate-500">{j.created_at.slice(11, 16)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* ── 🔬 分析区 ── */}
        <section className="rounded-xl border border-white/5 bg-slate-800/60 p-5 shadow-lg shadow-black/20">
          <SectionTitle icon={<FlaskConical className="h-4 w-4 text-sky-400" />}>需求分析</SectionTitle>

          <div className="mt-4 flex items-end gap-2">
            <div className="flex-1">
              <label className="mb-1.5 block text-xs font-medium text-slate-400">文档 ID</label>
              <input
                value={docId}
                onChange={(e) => setDocId(e.target.value)}
                placeholder="例：42"
                className={inputCls}
              />
            </div>
            <button
              onClick={() => void handleAnalyzeOne()}
              disabled={analyzing || !docId.trim()}
              className={primaryBtnCls}
            >
              {analyzing ? "分析中…" : "分析此文档"}
            </button>
          </div>

          <div className="mt-4 border-t border-white/5 pt-4">
            <ConfirmButton
              label="批量分析未处理文档"
              confirmLabel="确认批量分析"
              hint="对所有无信号的文档逐篇调用 LLM（每篇约 1-3 秒），产生 API 费用。确定？"
              busy={batchAnalyzing}
              onConfirm={() => void handleBatch()}
            />
            {batchAnalyzing && (
              <p className="mt-2 text-xs text-sky-300">
                批量分析进行中，请勿关闭页面…
              </p>
            )}
          </div>

          <MsgBanner msg={analyzeMsg} />
        </section>

        {/* ── 🧩 聚类与评分区 ── */}
        <section className="rounded-xl border border-white/5 bg-slate-800/60 p-5 shadow-lg shadow-black/20">
          <SectionTitle icon={<Boxes className="h-4 w-4 text-sky-400" />}>聚类与评分</SectionTitle>

          <div className="mt-4 space-y-4">
            <div>
              <ConfirmButton
                label="重建聚类"
                confirmLabel="确认重建"
                hint="全量重算：簇 ID 会变化、LLM 重新命名。确定？"
                busy={rebuilding}
                onConfirm={() => void handleRebuild()}
              />
              <p className="mt-1.5 text-xs text-slate-500">
                对全部向量重新 HDBSCAN 聚类 + LLM 命名
              </p>
            </div>

            <div>
              <ConfirmButton
                label="重跑评分"
                confirmLabel="确认评分"
                hint="对每个簇调用 LLM 评估两个维度。确定？"
                busy={rescoring}
                onConfirm={() => void handleRescore()}
              />
              <p className="mt-1.5 text-xs text-slate-500">
                重算八维分数并更新 demand_score 排序
              </p>
            </div>
          </div>

          <MsgBanner msg={opMsg} />
        </section>

        {/* ── ➕ 数据源管理 ── */}
        <section className="rounded-xl border border-white/5 bg-slate-800/60 p-5 shadow-lg shadow-black/20">
          <SectionTitle icon={<Plus className="h-4 w-4 text-sky-400" />}>数据源管理</SectionTitle>

          <form onSubmit={(e) => void handleAddSource(e)} className="mt-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-slate-400">名称 *</label>
                <input
                  value={srcName}
                  onChange={(e) => setSrcName(e.target.value)}
                  required
                  placeholder="例：Product Hunt"
                  className={inputCls}
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-slate-400">类型 *</label>
                <select
                  value={srcType}
                  onChange={(e) => setSrcType(e.target.value)}
                  className={inputCls}
                >
                  {SOURCE_TYPE_OPTIONS.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-slate-400">Base URL</label>
              <input
                value={srcUrl}
                onChange={(e) => setSrcUrl(e.target.value)}
                placeholder="例：https://github.com/langchain-ai/langchain"
                className={inputCls}
              />
            </div>
            <button
              type="submit"
              disabled={addingSource}
              className={successBtnCls}
            >
              {addingSource ? "添加中…" : "添加数据源"}
            </button>
          </form>
          <MsgBanner msg={srcMsg} />

          <h3 className="mb-2 mt-5 text-xs font-medium uppercase tracking-wider text-slate-500">
            现有数据源
          </h3>
          <ul className="space-y-2">
            {sources.map((s) => {
              const h = healthOf(s);
              const isHealthy = s.status === "active" && h.label === "健康";
              return (
                <li
                  key={s.id}
                  className="flex items-center justify-between gap-3 rounded-lg border border-white/5 bg-slate-900/40 px-3 py-2 text-sm"
                >
                  <span className="flex min-w-0 items-center gap-2">
                    <span
                      className={`h-2 w-2 shrink-0 rounded-full ${h.dot} ${
                        isHealthy ? "animate-pulse" : ""
                      }`}
                      title={h.label}
                    />
                    <span className="truncate text-slate-200">{s.name}</span>
                  </span>
                  <span className="flex shrink-0 items-center gap-3 text-xs text-slate-500">
                    {s.avg_latency != null && (
                      <span className="tabular-nums" title="平均响应延迟">
                        {Math.round(s.avg_latency)}ms
                      </span>
                    )}
                    <span className="tabular-nums" title="最近抓取时间">
                      <RelativeTime iso={s.last_crawl_at} />
                    </span>
                    <span className="tabular-nums" title="信号数 / 文档数（signal yield）">
                      信号 {s.signal_count}/{s.document_count}
                      <span className="text-slate-600"> ({s.signal_yield})</span>
                    </span>
                    <span className="tabular-nums" title="近 30 天任务成功率">
                      成功率 {(s.job_success_rate * 100).toFixed(0)}%
                    </span>
                    <span
                      className={`rounded-md px-2 py-0.5 font-medium ${
                        s.status === "active"
                          ? "bg-emerald-400/10 text-emerald-300 ring-1 ring-emerald-400/20"
                          : "bg-slate-400/10 text-slate-400 ring-1 ring-slate-400/20"
                      }`}
                    >
                      {s.status}
                    </span>
                  </span>
                </li>
              );
            })}
          </ul>
        </section>
      </div>
    </>
  );
}
