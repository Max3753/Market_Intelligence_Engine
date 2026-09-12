import type { DemandType } from "@/types";
import { badgeBaseCls } from "@/lib/ui";

/** 需求类型徽章配色 —— 低饱和 + ring，见 DESIGN.md §7 */
export const DEMAND_TYPE_STYLES: Record<DemandType, string> = {
  pain: "bg-red-400/10 text-red-300 ring-1 ring-red-400/20",
  complaint: "bg-orange-400/10 text-orange-300 ring-1 ring-orange-400/20",
  feature_request: "bg-sky-400/10 text-sky-300 ring-1 ring-sky-400/20",
  workaround: "bg-yellow-400/10 text-yellow-300 ring-1 ring-yellow-400/20",
  buying_intent: "bg-emerald-400/10 text-emerald-300 ring-1 ring-emerald-400/20",
  alternative_search: "bg-teal-400/10 text-teal-300 ring-1 ring-teal-400/20",
  price_complaint: "bg-amber-400/10 text-amber-300 ring-1 ring-amber-400/20",
  churn_signal: "bg-rose-400/10 text-rose-300 ring-1 ring-rose-400/20",
  unmet_need: "bg-violet-400/10 text-violet-300 ring-1 ring-violet-400/20",
  general_discussion: "bg-slate-400/10 text-slate-300 ring-1 ring-slate-400/20",
  noise: "bg-slate-400/5 text-slate-500 ring-1 ring-slate-400/10",
};

/** 需求类型中文标签 */
export const DEMAND_TYPE_LABELS: Record<DemandType, string> = {
  pain: "痛点",
  complaint: "抱怨",
  feature_request: "功能请求",
  workaround: "变通方案",
  buying_intent: "购买意向",
  alternative_search: "替代搜索",
  price_complaint: "价格抱怨",
  churn_signal: "流失信号",
  unmet_need: "未满足需求",
  general_discussion: "一般讨论",
  noise: "噪声",
};

interface DemandTypeBadgeProps {
  type: DemandType;
  showLabel?: boolean;
}

/** 需求类型徽章 —— 全站统一 */
export default function DemandTypeBadge({
  type,
  showLabel = false,
}: DemandTypeBadgeProps) {
  const style = DEMAND_TYPE_STYLES[type] ?? "bg-slate-400/10 text-slate-300 ring-1 ring-slate-400/20";
  return (
    <span className={`${badgeBaseCls} ${style}`}>
      {showLabel ? DEMAND_TYPE_LABELS[type] ?? type : type}
    </span>
  );
}
