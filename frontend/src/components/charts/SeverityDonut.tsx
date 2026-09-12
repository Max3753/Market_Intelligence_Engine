import type { CSSProperties } from "react";

interface SliceDatum {
  name: string;
  value: number;
  color: string;
}

interface SeverityDonutProps {
  data: SliceDatum[];
}

const SIZE = 200;
const CENTER = SIZE / 2;
const RADIUS = 80;
const STROKE = 22;
const CIRC = 2 * Math.PI * RADIUS;

/**
 * 严重度分布环形图 —— 纯 SVG stroke-dasharray，无第三方图表库。
 * 中心留白 + 语义色扇区。
 */
export default function SeverityDonut({ data }: SeverityDonutProps) {
  const total = data.reduce((s, d) => s + d.value, 0);
  if (total === 0) return null;

  let offset = 0;
  const segments = data.map((d) => {
    const frac = d.value / total;
    const seg = {
      ...d,
      dash: frac * CIRC,
      offset: -offset,
    };
    offset += frac * CIRC;
    return seg;
  });

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        <svg
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          className="h-44 w-44 -rotate-90"
          role="img"
          aria-label="严重度分布环形图"
        >
          {/* 底环 */}
          <circle
            cx={CENTER}
            cy={CENTER}
            r={RADIUS}
            fill="none"
            stroke="rgba(255,255,255,0.05)"
            strokeWidth={STROKE}
          />
          {/* 数据扇区 */}
          {segments.map((s, i) => (
            <circle
              key={i}
              cx={CENTER}
              cy={CENTER}
              r={RADIUS}
              fill="none"
              stroke={s.color}
              strokeWidth={STROKE}
              strokeDasharray={`${s.dash} ${CIRC - s.dash}`}
              strokeDashoffset={s.offset}
              strokeLinecap="round"
              className="donut-draw cursor-pointer transition-all duration-200 hover:opacity-80"
              style={
                {
                  "--dash": `${s.dash} ${CIRC - s.dash}`,
                  animationDelay: `${i * 0.15}s`,
                } as CSSProperties
              }
            >
              <title>{`${s.name}：${s.value} 条信号`}</title>
            </circle>
          ))}
        </svg>
        {/* 中心光晕 */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-8 rounded-full bg-white/[0.03] blur-xl"
        />
        {/* 中心总数 */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-semibold tabular-nums text-white">
            {total}
          </span>
          <span className="text-xs text-slate-500">信号</span>
        </div>
      </div>
      {/* 图例 */}
      <div className="flex flex-wrap justify-center gap-x-4 gap-y-1.5">
        {data.map((d) => (
          <div key={d.name} className="flex items-center gap-1.5 text-xs">
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: d.color }}
            />
            <span className="text-slate-400">{d.name}</span>
            <span className="tabular-nums text-slate-200">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
