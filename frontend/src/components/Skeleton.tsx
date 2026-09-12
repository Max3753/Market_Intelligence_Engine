import type { ReactNode } from "react";

interface SkeletonProps {
  className?: string;
}

/**
 * 骨架屏块 —— loading 态占位，替代裸文本。
 * 默认圆角 + 微亮脉冲；用 className 控制尺寸。
 */
export default function Skeleton({ className = "" }: SkeletonProps) {
  return <div className={`skeleton ${className}`} />;
}

/** 骨架卡片 —— 模拟一张卡片的整体结构 */
export function SkeletonCard() {
  return (
    <div className="rounded-xl border border-white/5 bg-slate-800/60 p-5 shadow-lg shadow-black/20">
      <Skeleton className="h-3 w-24" />
      <Skeleton className="mt-3 h-8 w-32" />
      <Skeleton className="mt-4 h-3 w-full" />
      <Skeleton className="mt-2 h-3 w-3/4" />
    </div>
  );
}

/** 骨架表格行 —— 模拟表格的若干行 */
export function SkeletonTable({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4">
          <Skeleton className="h-4 w-8" />
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="h-4 w-12" />
        </div>
      ))}
    </div>
  );
}

/**
 * 骨架图表卡片 —— 卡片壳 + 区块标题条 + 副标题 + 图表体占位。
 * 与 dashboard 的图表卡结构一致（sectionTitleCls 布局），loading 态更接近真实布局。
 */
export function SkeletonChartCard({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-xl border border-white/5 bg-slate-800/60 p-5 shadow-lg shadow-black/20">
      <div className="flex items-center gap-2">
        <Skeleton className="h-4 w-1 rounded-full" />
        <Skeleton className="h-4 w-28" />
      </div>
      <Skeleton className="mt-2 h-3 w-36" />
      <div className="mt-4">{children}</div>
    </div>
  );
}

/** 雷达图骨架 —— 圆形占位 + 维度标签行（对齐 ClusterRadar 布局） */
export function SkeletonRadar() {
  return (
    <div className="flex flex-col items-center">
      <Skeleton className="h-56 w-56 rounded-full" />
      <div className="mt-4 grid w-full grid-cols-3 gap-x-4 gap-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-3 w-full" />
        ))}
      </div>
    </div>
  );
}

/** 条形图骨架 —— 若干横条（对齐 TypeDistribution 布局） */
export function SkeletonBars({ rows = 8 }: { rows?: number }) {
  return (
    <div className="flex flex-col gap-2.5">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton className="h-3 w-20 shrink-0" />
          <Skeleton className="h-4 flex-1 rounded-md" />
          <Skeleton className="h-3 w-8 shrink-0" />
        </div>
      ))}
    </div>
  );
}

/** 环形图骨架 —— 圆环 + 图例（对齐 SeverityDonut 布局） */
export function SkeletonDonut() {
  return (
    <div className="flex flex-col items-center gap-4">
      <Skeleton className="h-44 w-44 rounded-full" />
      <div className="flex flex-wrap justify-center gap-x-4 gap-y-1.5">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex items-center gap-1.5">
            <Skeleton className="h-2 w-2 rounded-full" />
            <Skeleton className="h-3 w-10" />
          </div>
        ))}
      </div>
    </div>
  );
}

/** Top 列表骨架 —— 色点 + 名称 + 数值（对齐 dashboard「需求类型 Top」） */
export function SkeletonTopList({ rows = 6 }: { rows?: number }) {
  return (
    <ul className="mt-4 space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <li
          key={i}
          className="flex items-center justify-between rounded-lg bg-white/[0.02] px-3 py-2"
        >
          <div className="flex items-center gap-2">
            <Skeleton className="h-2 w-2 rounded-full" />
            <Skeleton className="h-3 w-24" />
          </div>
          <Skeleton className="h-3 w-6" />
        </li>
      ))}
    </ul>
  );
}

/** 增长排行骨架 —— 排名 + 名称 + 进度条 + 徽章（对齐 TrendGrowthRank 布局） */
export function SkeletonTrendList({ rows = 6 }: { rows?: number }) {
  return (
    <ul className="mt-4 space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <li
          key={i}
          className="flex items-center gap-3 rounded-lg bg-white/[0.02] px-3 py-2"
        >
          <Skeleton className="h-3 w-5" />
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-between gap-2">
              <Skeleton className="h-3 w-32" />
              <Skeleton className="h-3 w-8" />
            </div>
            <Skeleton className="mt-1.5 h-1.5 w-full rounded-full" />
          </div>
          <Skeleton className="h-5 w-14 rounded-md" />
        </li>
      ))}
    </ul>
  );
}

/** 周期信号量骨架 —— 三条周期横条（对齐 TrendPeriodBar 布局） */
export function SkeletonPeriodBars() {
  return (
    <div className="mt-4 space-y-5">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i}>
          <div className="flex items-center justify-between">
            <Skeleton className="h-3 w-12" />
            <Skeleton className="h-3 w-8" />
          </div>
          <Skeleton className="mt-2 h-2 w-full rounded-full" />
        </div>
      ))}
    </div>
  );
}