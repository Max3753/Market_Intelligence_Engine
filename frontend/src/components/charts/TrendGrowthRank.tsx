import type { TrendMetric } from "@/types";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";

interface TrendGrowthRankProps {
  data: TrendMetric[];
}

/**
 * 信号增长排行 —— 按增长率降序排列的簇列表。
 * 优先展示 7 天窗口；无 7d 增长数据时回退到 30d / 全量。
 * growth_rate 为 null 或 0 时显示占位符，全部为空时展示空态文案。
 */
export default function TrendGrowthRank({ data }: TrendGrowthRankProps) {
  // 筛选有有效增长率的条目
  const withGrowth = data.filter(
    (t) => t.growth_rate != null && t.growth_rate !== 0,
  );

  // 按 period 优先级：7d → 30d → 90d → 全量
  const ranked = ["7d", "30d", "90d"]
    .map((p) => withGrowth.filter((t) => t.period === p))
    .find((arr) => arr.length > 0) ?? withGrowth;

  const sorted = [...ranked].sort((a, b) => b.growth_rate - a.growth_rate);

  if (sorted.length === 0) {
    return (
      <p className="py-16 text-center text-sm text-slate-500">
        数据不足，暂无增长趋势
      </p>
    );
  }

  const maxVal = Math.max(...sorted.map((t) => t.value), 1);

  return (
    <ul className="mt-4 space-y-2">
      {sorted.slice(0, 8).map((t, i) => {
        const barPct = (t.value / maxVal) * 100;
        const up = t.growth_rate > 0;
        return (
          <li
            key={t.id}
            className="flex items-center gap-3 rounded-lg bg-white/[0.02] px-3 py-2 transition-colors hover:bg-white/[0.04]"
          >
            {/* 排名 */}
            <span className="w-5 text-center text-xs font-medium text-slate-500 tabular-nums">
              {i + 1}
            </span>
            {/* 簇名 + 进度条 */}
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-2">
                <span className="truncate text-sm text-slate-300">
                  {t.topic}
                </span>
                <span className="shrink-0 tabular-nums text-sm text-slate-400">
                  {t.value}
                </span>
              </div>
              <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-white/5">
                <div
                  className="bar-grow h-full rounded-full bg-sky-400/50"
                  style={{
                    width: `${barPct}%`,
                    animationDelay: `${i * 0.06}s`,
                  }}
                />
              </div>
            </div>
            {/* 增长率徽章 */}
            <span
              className={`inline-flex shrink-0 items-center gap-0.5 rounded-md px-2 py-0.5 text-xs font-medium tabular-nums ring-1 ${
                up
                  ? "bg-emerald-400/10 text-emerald-300 ring-emerald-400/20"
                  : "bg-red-400/10 text-red-300 ring-red-400/20"
              }`}
            >
              {up ? (
                <ArrowUpRight className="h-3 w-3" />
              ) : (
                <ArrowDownRight className="h-3 w-3" />
              )}
              {up ? "+" : ""}
              {Math.round(t.growth_rate * 100)}%
            </span>
          </li>
        );
      })}
    </ul>
  );
}
