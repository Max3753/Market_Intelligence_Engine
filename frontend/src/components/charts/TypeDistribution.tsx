interface BarDatum {
  name: string;
  value: number;
  color: string;
}

interface TypeDistributionProps {
  data: BarDatum[];
}

/**
 * 需求类型分布条形图 —— 纯 CSS 横向条形，无第三方图表库。
 * 按数量降序，每类用语义色（低饱和）。
 */
export default function TypeDistribution({ data }: TypeDistributionProps) {
  if (data.length === 0) return null;
  const max = Math.max(...data.map((d) => d.value), 1);

  return (
    <div className="flex flex-col gap-2.5">
      {data.map((d, i) => (
        <div
          key={d.name}
          className="group flex items-center gap-3 rounded-md px-1 py-0.5 transition-colors hover:bg-white/[0.03]"
        >
          <span className="w-20 shrink-0 truncate text-xs text-slate-400 transition-colors group-hover:text-slate-200">
            {d.name}
          </span>
          <div className="relative h-4 flex-1 overflow-hidden rounded-md bg-white/5">
            <div
              className="bar-grow h-full rounded-md"
              style={{
                width: `${(d.value / max) * 100}%`,
                background: `linear-gradient(90deg, ${d.color}cc, ${d.color}66)`,
                animationDelay: `${i * 0.08}s`,
              }}
            />
          </div>
          <span className="w-8 shrink-0 text-right tabular-nums text-xs text-slate-300 transition-colors group-hover:text-white">
            {d.value}
          </span>
        </div>
      ))}
    </div>
  );
}
