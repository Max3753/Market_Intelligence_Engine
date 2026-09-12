import type { ValidationStatus } from "@/types";
import { badgeBaseCls } from "@/lib/ui";

/** 验证漏斗状态徽章配色 —— 11 态穷举，低饱和 + ring，见 DESIGN.md §7 */
export const STATUS_STYLES: Record<ValidationStatus, string> = {
  DISCOVERED: "bg-slate-400/10 text-slate-300 ring-1 ring-slate-400/20",
  EVIDENCE_GATHERING: "bg-sky-400/10 text-sky-300 ring-1 ring-sky-400/20",
  HUMAN_REVIEW: "bg-amber-400/10 text-amber-300 ring-1 ring-amber-400/20",
  INTERVIEW: "bg-violet-400/10 text-violet-300 ring-1 ring-violet-400/20",
  VALIDATED: "bg-emerald-400/10 text-emerald-300 ring-1 ring-emerald-400/20",
  MVP: "bg-green-400/10 text-green-300 ring-1 ring-green-400/20",
  EARLY_USERS: "bg-teal-400/10 text-teal-300 ring-1 ring-teal-400/20",
  PAID: "bg-yellow-400/10 text-yellow-300 ring-1 ring-yellow-400/20",
  SCALED: "bg-emerald-400/20 text-emerald-200 ring-1 ring-emerald-400/30",
  REJECTED: "bg-red-400/10 text-red-300 ring-1 ring-red-400/20",
  DORMANT: "bg-slate-400/10 text-slate-400 ring-1 ring-slate-400/20",
};

/** 状态中文标签 */
export const STATUS_LABELS: Record<ValidationStatus, string> = {
  DISCOVERED: "已发现",
  EVIDENCE_GATHERING: "收集证据",
  HUMAN_REVIEW: "人工评审",
  INTERVIEW: "用户访谈",
  VALIDATED: "已验证",
  MVP: "MVP",
  EARLY_USERS: "早期用户",
  PAID: "已付费",
  SCALED: "已规模化",
  REJECTED: "已否决",
  DORMANT: "休眠",
};

interface StatusBadgeProps {
  status: ValidationStatus;
  showLabel?: boolean;
}

/** 机会验证状态徽章 —— 全站统一 */
export default function StatusBadge({
  status,
  showLabel = false,
}: StatusBadgeProps) {
  const style =
    STATUS_STYLES[status] ??
    "bg-slate-400/10 text-slate-300 ring-1 ring-slate-400/20";
  return (
    <span className={`${badgeBaseCls} ${style}`}>
      {showLabel ? STATUS_LABELS[status] ?? status : status}
    </span>
  );
}
