import Skeleton, {
  SkeletonCard,
  SkeletonChartCard,
  SkeletonRadar,
  SkeletonBars,
  SkeletonDonut,
  SkeletonTopList,
  SkeletonTrendList,
  SkeletonPeriodBars,
} from "@/components/Skeleton";

/**
 * 路由级加载态 —— server component 取数期间展示。
 * 布局镜像 dashboard：标题 → 统计卡 → 榜首高亮卡 → 4 图表 → 2 趋势，
 * 让加载态与真实页面结构一致，减少布局跳动。
 */
export default function Loading() {
  return (
    <div className="space-y-6">
      {/* 标题骨架 */}
      <div className="space-y-2">
        <div className="skeleton h-7 w-56" />
        <div className="skeleton h-4 w-40" />
      </div>

      {/* 统计卡骨架 */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>

      {/* 榜首高亮卡骨架 */}
      <div className="rounded-xl border border-white/5 bg-slate-800/60 p-5 shadow-lg shadow-black/20">
        <Skeleton className="h-3 w-28" />
        <div className="mt-3 flex items-center justify-between gap-4">
          <Skeleton className="h-6 w-1/2" />
          <Skeleton className="h-8 w-16" />
        </div>
        <Skeleton className="mt-3 h-4 w-3/4" />
        <div className="mt-3 flex flex-wrap gap-4">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-3 w-12" />
        </div>
      </div>

      {/* 可视化区骨架 —— 4 图表 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SkeletonChartCard>
          <SkeletonRadar />
        </SkeletonChartCard>
        <SkeletonChartCard>
          <SkeletonBars rows={8} />
        </SkeletonChartCard>
        <SkeletonChartCard>
          <SkeletonDonut />
        </SkeletonChartCard>
        <SkeletonChartCard>
          <SkeletonTopList rows={6} />
        </SkeletonChartCard>
      </div>

      {/* 趋势区骨架 —— 2 图表 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SkeletonChartCard>
          <SkeletonTrendList rows={6} />
        </SkeletonChartCard>
        <SkeletonChartCard>
          <SkeletonPeriodBars />
        </SkeletonChartCard>
      </div>
    </div>
  );
}