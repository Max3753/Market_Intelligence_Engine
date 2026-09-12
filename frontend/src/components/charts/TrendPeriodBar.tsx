import type { TrendMetric } from "@/types";

interface TrendPeriodBarProps {
  data: TrendMetric[];
}

const PERIODS = [
  { key: "7d", label: "7 天", color: "#38bdf8" },
  { key: "30d", label: "30 天", color: "#34d399" },
  { key: "90d", label: "90 天", color: "#a78bfa" },
] as const;

/**
 * 周期信号量 —— 按 7d / 30d / 90d 窗口汇总信号总量，纯 CSS 横条。
 * 三个周期各一条，宽度按最大值归一化；尊重 prefers-reduced-motion（bar-grow）。
 */
export default function TrendPeriodBar({ data }: TrendPeriodBarProps) {
  const totals = PERIODS.map(({ key, label, color }) => ({
    key,
    label,
    color,
    total: data
      .filter((t) => t.period === key)
      .reduce((s, t) => s + t.value, 0),
  }));

  const maxTotal = Math.max(...totals.map((t) => t.total), 1);

  return (
    <div className="mt-4 space-y-5">
      {totals.map((t, i) => {
        const pct = (t.total / maxTotal) * 100;
        return (
          <div
            key={t.key}
            className="group rounded-md px-1 py-0.5 transition-colors hover:bg-white/[0.03]"
          >
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400 transition-colors group-hover:text-slate-200">
                {t.label}
              </span>
              <span className="tabular-nums font-medium text-slate-200 transition-colors group-hover:text-white">
                {t.total}
              </span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/5">
              <div
                className="bar-grow h-full rounded-full"
                style={{
                  width: `${pct}%`,
                  background: `linear-gradient(90deg, ${t.color}cc, ${t.color}66)`,
                  animationDelay: `${i * 0.12}s`,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
