interface RadarDatum {
  dimension: string;
  value: number; // 0-10
}

interface ClusterRadarProps {
  data: RadarDatum[];
}

const SIZE = 260;
const CENTER = SIZE / 2;
const RADIUS = 90;

/** 极坐标 → 笛卡尔坐标 */
function polar(cx: number, cy: number, r: number, angleDeg: number) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

/**
 * 簇 8 维评分雷达图 —— 纯 SVG，无第三方图表库。
 * 展示榜首簇的评分画像（0-10）。
 */
export default function ClusterRadar({ data }: ClusterRadarProps) {
  const n = data.length;
  if (n === 0) return null;

  // 网格环（3 层）
  const rings = [0.33, 0.66, 1].map((f) =>
    Array.from({ length: n }, (_, i) => {
      const p = polar(CENTER, CENTER, RADIUS * f, (360 / n) * i);
      return `${p.x},${p.y}`;
    }).join(" ")
  );

  // 轴线
  const axes = Array.from({ length: n }, (_, i) => {
    const p = polar(CENTER, CENTER, RADIUS, (360 / n) * i);
    return { x1: CENTER, y1: CENTER, x2: p.x, y2: p.y };
  });

  // 数据多边形
  const dataPoints = data.map((d, i) => {
    const p = polar(CENTER, CENTER, (Math.min(10, Math.max(0, d.value)) / 10) * RADIUS, (360 / n) * i);
    return `${p.x},${p.y}`;
  });

  // 数据点坐标（用于圆点）
  const dots = data.map((d, i) =>
    polar(CENTER, CENTER, (Math.min(10, Math.max(0, d.value)) / 10) * RADIUS, (360 / n) * i)
  );

  return (
    <div className="flex w-full flex-col items-center">
      <svg
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        className="h-56 w-56"
        role="img"
        aria-label="簇评分雷达图"
      >
        {/* 网格环 */}
        {rings.map((points, i) => (
          <polygon
            key={i}
            points={points}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth={1}
          />
        ))}
        {/* 轴线 */}
        {axes.map((a, i) => (
          <line
            key={i}
            {...a}
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={1}
          />
        ))}
        {/* 数据多边形 */}
        <defs>
          <radialGradient id="radar-fill" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.08" />
          </radialGradient>
        </defs>
        <polygon
          points={dataPoints.join(" ")}
          fill="url(#radar-fill)"
          stroke="#38bdf8"
          strokeWidth={2}
          strokeLinejoin="round"
          className="radar-draw"
        />
        {/* 数据点 */}
        {dots.map((d, i) => (
          <circle
            key={i}
            cx={d.x}
            cy={d.y}
            r={3}
            fill="#38bdf8"
            className="cursor-pointer transition-all duration-200 hover:r-[4.5] hover:fill-sky-300"
          >
            <title>{`${data[i].dimension}：${data[i].value.toFixed(1)} / 10`}</title>
          </circle>
        ))}
      </svg>
      {/* 维度标签 */}
      <div className="mt-2 grid w-full grid-cols-3 gap-x-4 gap-y-1.5">
        {data.map((d) => (
          <div
            key={d.dimension}
            className="flex items-center justify-between rounded px-1 text-xs transition-colors hover:bg-white/[0.03]"
          >
            <span className="text-slate-400 transition-colors hover:text-slate-200">
              {d.dimension}
            </span>
            <span className="tabular-nums text-slate-200">{d.value.toFixed(1)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
