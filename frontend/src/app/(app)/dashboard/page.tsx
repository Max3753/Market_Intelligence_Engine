import StatCard from "@/components/StatCard";
import FadeIn from "@/components/FadeIn";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import Link from "next/link";
import {
  FileText,
  MessageSquare,
  Layers,
  TrendingUp,
  ArrowRight,
  TriangleAlert,
  CheckCircle2,
} from "lucide-react";
import { getClusters, getDemands, getDocuments, getTrends } from "@/lib/api";
import { cardCls, sectionTitleCls, sectionTitleBarCls } from "@/lib/ui";
import ClusterRadar from "@/components/charts/ClusterRadar";
import TypeDistribution from "@/components/charts/TypeDistribution";
import SeverityDonut from "@/components/charts/SeverityDonut";
import TrendGrowthRank from "@/components/charts/TrendGrowthRank";
import TrendPeriodBar from "@/components/charts/TrendPeriodBar";
import { DEMAND_TYPE_LABELS } from "@/components/DemandTypeBadge";
import type { DemandType } from "@/types";

export const dynamic = "force-dynamic";

/** 需求类型 → 图表色（低饱和，与徽章一致） */
const TYPE_CHART_COLORS: Record<DemandType, string> = {
  pain: "#f87171",
  complaint: "#fb923c",
  feature_request: "#38bdf8",
  workaround: "#facc15",
  buying_intent: "#34d399",
  alternative_search: "#2dd4bf",
  price_complaint: "#fbbf24",
  churn_signal: "#fb7185",
  unmet_need: "#a78bfa",
  general_discussion: "#94a3b8",
  noise: "#64748b",
};

/** 严重度分桶 → 色（互斥区间，与副标题「高 ≥7 · 中 4-6 · 低 0-3」一致） */
const SEVERITY_BUCKETS = [
  { key: "高", min: 7, max: 10, color: "#f87171" },
  { key: "中", min: 4, max: 6, color: "#fbbf24" },
  { key: "低", min: 0, max: 3, color: "#34d399" },
];

export default async function DashboardPage() {
  // 三个请求并行发 —— Promise.all 同时出发，总耗时 = 最慢的那个
  const [docs, demands, clusters, trends] = await Promise.all([
    getDocuments(),
    getDemands(),
    getClusters(),
    getTrends(),
  ]);

  const top = clusters[0]; // 后端已按 demand_score 排序，第一个即榜首

  // ── 榜首簇 8 维评分（雷达图）──
  const radarData = top
    ? [
        { dimension: "痛点", value: top.pain_score ?? 0 },
        { dimension: "频率", value: top.frequency_score ?? 0 },
        { dimension: "付费意愿", value: top.money_score ?? 0 },
        { dimension: "增长", value: top.growth_score ?? 0 },
        { dimension: "竞争缺口", value: top.competition_gap ?? 0 },
        { dimension: "综合", value: (top.demand_score ?? 0) / 10 },
      ]
    : [];

  // ── 需求类型分布（条形图）──
  const typeCounts = new Map<DemandType, number>();
  for (const d of demands) {
    typeCounts.set(d.demand_type, (typeCounts.get(d.demand_type) ?? 0) + 1);
  }
  const typeData = [...typeCounts.entries()]
    .map(([type, count]) => ({
      name: DEMAND_TYPE_LABELS[type] ?? type,
      value: count,
      color: TYPE_CHART_COLORS[type] ?? "#94a3b8",
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8);

  // ── 严重度分布（环形图）──
  const severityCounts = SEVERITY_BUCKETS.map((b) => ({
    name: b.key,
    value: demands.filter((d) => {
      const s = d.severity ?? 0;
      return s >= b.min && s <= b.max;
    }).length,
    color: b.color,
  })).reverse(); // 低→高，环形图从底部开始

  return (
    <>
      <PageHeader title="Market Intelligence Engine" subtitle="仪表盘概览" />

      {/* 统计卡 —— stagger 入场 */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          title="文档"
          value={docs.length}
          icon={<FileText className="h-4 w-4" />}
          accent="sky"
          delay={0}
        />
        <StatCard
          title="需求信号"
          value={demands.length}
          icon={<MessageSquare className="h-4 w-4" />}
          accent="emerald"
          delay={0.06}
        />
        <StatCard
          title="簇"
          value={clusters.length}
          icon={<Layers className="h-4 w-4" />}
          accent="violet"
          delay={0.12}
        />
        <StatCard
          title="最高分"
          value={top?.demand_score?.toFixed(1) ?? "—"}
          icon={<TrendingUp className="h-4 w-4" />}
          accent="amber"
          hint={top ? `榜首：${top.name}` : undefined}
          delay={0.18}
        />
      </div>

      {/* 榜首机会高亮卡 —— Hero 级 accent 氛围 */}
      {top && (
        <FadeIn delay={0.24}>
          <Link
            href="/opportunities"
            className="group relative mt-6 block overflow-hidden rounded-xl border border-sky-400/10 bg-gradient-to-br from-slate-800/80 via-slate-800/60 to-sky-900/20 p-5 shadow-lg shadow-sky-500/5 transition-all duration-200 hover:-translate-y-1 hover:border-sky-400/20 hover:shadow-2xl hover:shadow-sky-500/15 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400/50 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
          >
            {/* 角落光晕 */}
            <div
              aria-hidden
              className="pointer-events-none absolute -left-20 -top-20 h-40 w-40 rounded-full bg-sky-400/5 blur-3xl"
            />
            {/* 顶部 2px 渐变 accent 线 */}
            <div
              aria-hidden
              className="pointer-events-none absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-transparent via-sky-400/80 to-transparent"
            />
            <div className="relative flex items-center justify-between">
              <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                TOP OPPORTUNITY
              </p>
              <ArrowRight className="h-4 w-4 text-slate-500 transition-transform group-hover:translate-x-1 group-hover:text-sky-400" />
            </div>
            <div className="relative mt-1 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">{top.name}</h2>
              <span className="text-3xl font-bold tabular-nums text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,0.3)]">
                {top.demand_score?.toFixed(1)}
              </span>
            </div>
            <p className="relative mt-2 text-sm text-slate-400">{top.description}</p>
            <div className="relative mt-3 flex flex-wrap gap-4 text-xs text-slate-500">
              <span className="tabular-nums">信号数 {top.document_count ?? 0}</span>
              <span className="tabular-nums">独立用户 {top.unique_user_count ?? 0}</span>
              {top.source_count < 2 ? (
                <span className="inline-flex items-center gap-1 text-amber-400">
                  <TriangleAlert className="h-3.5 w-3.5" />
                  单源
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-emerald-400">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  双源
                </span>
              )}
            </div>
          </Link>
        </FadeIn>
      )}

      {/* 可视化区 —— stagger 入场 */}
      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* 榜首簇评分画像 */}
        <FadeIn delay={0.30}>
          <div className={cardCls}>
            <div className={sectionTitleCls}>
              <span className={sectionTitleBarCls} />
              <h3>榜首簇评分画像</h3>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              六维评分雷达 · 满分 10
            </p>
            {radarData.length > 0 ? (
              <ClusterRadar data={radarData} />
            ) : (
              <EmptyState
                variant="inline"
                title="暂无评分数据"
                description="先运行聚类评分，榜首簇的六维画像会显示在这里"
                icon={<Layers className="h-5 w-5" />}
              />
            )}
          </div>
        </FadeIn>

        {/* 需求类型分布 */}
        <FadeIn delay={0.36}>
          <div className={cardCls}>
            <div className={sectionTitleCls}>
              <span className={sectionTitleBarCls} />
              <h3>需求类型分布</h3>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              按需求类型聚合 · 前 8 类
            </p>
            {typeData.length > 0 ? (
              <TypeDistribution data={typeData} />
            ) : (
              <EmptyState
                variant="inline"
                title="暂无需求信号"
                description="先运行爬取任务，或等待数据源接入"
                icon={<MessageSquare className="h-5 w-5" />}
              />
            )}
          </div>
        </FadeIn>

        {/* 严重度分布 */}
        <FadeIn delay={0.42}>
          <div className={cardCls}>
            <div className={sectionTitleCls}>
              <span className={sectionTitleBarCls} />
              <h3>严重度分布</h3>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              高 ≥7 · 中 4-6 · 低 0-3
            </p>
            {demands.length > 0 ? (
              <SeverityDonut data={severityCounts} />
            ) : (
              <EmptyState
                variant="inline"
                title="暂无需求信号"
                description="先运行爬取任务，或等待数据源接入"
                icon={<MessageSquare className="h-5 w-5" />}
              />
            )}
          </div>
        </FadeIn>

        {/* 需求类型 Top 列表 */}
        <FadeIn delay={0.48}>
          <div className={cardCls}>
            <div className={sectionTitleCls}>
              <span className={sectionTitleBarCls} />
              <h3>需求类型 Top</h3>
            </div>
            <p className="mt-1 text-xs text-slate-500">按信号量排序</p>
            {typeData.length > 0 ? (
              <ul className="mt-4 space-y-2">
                {typeData.slice(0, 6).map((t) => (
                  <li
                    key={t.name}
                    className="flex items-center justify-between rounded-lg bg-white/[0.02] px-3 py-2"
                  >
                    <span className="flex items-center gap-2 text-sm text-slate-300">
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: t.color }}
                      />
                      {t.name}
                    </span>
                    <span className="tabular-nums text-sm text-slate-400">
                      {t.value}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState
                variant="inline"
                title="暂无需求信号"
                description="先运行爬取任务，或等待数据源接入"
                icon={<MessageSquare className="h-5 w-5" />}
              />
            )}
          </div>
        </FadeIn>
      </div>

      {/* 需求趋势 —— 增长排行 + 周期概览 */}
      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <FadeIn delay={0.54}>
          <div className={cardCls}>
            <div className={sectionTitleCls}>
              <span className={sectionTitleBarCls} />
              <h3>信号增长排行</h3>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              按增长率排序 · 7 天窗口优先
            </p>
            {trends.length > 0 ? (
              <TrendGrowthRank data={trends} />
            ) : (
              <EmptyState
                variant="inline"
                title="暂无趋势数据"
                description="趋势需要跨时间窗口的信号积累，数据量上来后自动生成"
                icon={<TrendingUp className="h-5 w-5" />}
              />
            )}
          </div>
        </FadeIn>

        <FadeIn delay={0.60}>
          <div className={cardCls}>
            <div className={sectionTitleCls}>
              <span className={sectionTitleBarCls} />
              <h3>周期信号量</h3>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              各时间窗口总信号数
            </p>
            {trends.length > 0 ? (
              <TrendPeriodBar data={trends} />
            ) : (
              <EmptyState
                variant="inline"
                title="暂无趋势数据"
                description="趋势需要跨时间窗口的信号积累，数据量上来后自动生成"
                icon={<TrendingUp className="h-5 w-5" />}
              />
            )}
          </div>
        </FadeIn>
      </div>
    </>
  );
}
