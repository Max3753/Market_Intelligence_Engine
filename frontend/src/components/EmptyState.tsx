import { Inbox } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  /**
   * card：独立空态卡片（虚线边框 + 大图标），用于页面级空数据；
   * inline：卡片内部使用（无边框、紧凑），用于图表/区块级空数据。
   */
  variant?: "card" | "inline";
}

/**
 * 空态 —— 数据为空时的引导占位，替代裸文本。
 * 图标 + 主文案 + 副文案（引导下一步动作），可选操作按钮。
 * 全站统一：dashboard 图表 / demands / opportunities / console 复用。
 */
export default function EmptyState({
  title,
  description,
  icon,
  action,
  variant = "card",
}: EmptyStateProps) {
  const isCard = variant === "card";
  return (
    <div
      className={`flex flex-col items-center justify-center px-6 text-center ${
        isCard
          ? "rounded-xl border border-dashed border-white/10 bg-slate-800/40 py-12"
          : "py-10"
      }`}
    >
      <div
        className={`flex items-center justify-center rounded-full bg-white/5 text-slate-500 ${
          isCard ? "h-12 w-12" : "h-10 w-10"
        }`}
      >
        {icon ?? <Inbox className={isCard ? "h-6 w-6" : "h-5 w-5"} />}
      </div>
      <p className="mt-4 text-sm font-medium text-slate-300">{title}</p>
      {description && (
        <p className="mt-1 max-w-sm text-xs leading-relaxed text-slate-500">
          {description}
        </p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}