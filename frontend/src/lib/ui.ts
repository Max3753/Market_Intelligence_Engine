/**
 * 设计系统共享 token —— 见 frontend/DESIGN.md。
 * 所有页面/组件复用同一套类名，保证跨页一致性与可访问性。
 */

/** 键盘焦点环 —— 所有可交互元素（Link/button/input）必须包含，满足 DESIGN.md §6 */
export const focusRingCls =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400/50 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900";

/** 输入框 —— 深色半透明 + 聚焦 ring */
export const inputCls =
  "w-full rounded-lg border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-sky-400/50 focus:ring-2 focus:ring-sky-400/20 focus:outline-none transition-all duration-200";

/** 主按钮（sky） */
export const primaryBtnCls =
  "rounded-lg bg-sky-500 px-4 py-2 text-sm font-medium text-white transition-all duration-200 hover:bg-sky-400 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed " +
  focusRingCls;

/** 危险按钮（red） */
export const dangerBtnCls =
  "rounded-lg bg-red-500/90 px-3 py-2 text-sm font-medium text-white transition-all duration-200 hover:bg-red-400 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed " +
  focusRingCls;

/** 次级按钮（ghost） */
export const secondaryBtnCls =
  "rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 transition-all duration-200 hover:bg-white/10 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed " +
  focusRingCls;

/** 成功按钮（emerald） */
export const successBtnCls =
  "rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-white transition-all duration-200 hover:bg-emerald-400 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed " +
  focusRingCls;

/** 卡片容器 —— 半透明 + 内边框 + 深阴影 */
export const cardCls =
  "rounded-xl border border-white/5 bg-slate-800/60 p-5 shadow-lg shadow-black/20";

/** 可交互卡片（Link 包裹）—— 在 cardCls 基础上加 hover 提升 */
export const interactiveCardCls =
  cardCls +
  " transition-all duration-200 hover:-translate-y-0.5 hover:border-white/10 hover:shadow-xl hover:shadow-black/30 " +
  focusRingCls;

/** 文本链接 —— 带 hover + 焦点环 */
export const linkCls =
  "text-sky-400 transition-colors hover:text-sky-300 hover:underline " +
  focusRingCls;

/** 区块标题 —— 左侧 3px accent 竖条，DESIGN.md §7 */
export const sectionTitleCls =
  "flex items-center gap-2 text-sm font-semibold text-slate-100";

/** 区块标题的 accent 竖条 */
export const sectionTitleBarCls =
  "h-4 w-1 rounded-full bg-gradient-to-b from-sky-400 to-emerald-400";

/** 表格容器 —— 深色半透明 + 内边框 */
export const tableWrapCls =
  "overflow-x-auto rounded-xl border border-white/5 bg-slate-800/60 shadow-lg shadow-black/20";

/** 表格表头单元格 */
export const thCls = "px-4 py-3 font-medium";

/** 表格行 —— hover 微亮 */
export const trCls =
  "border-b border-white/5 transition-colors hover:bg-white/[0.02]";

/** 表格数据单元格 */
export const tdCls = "px-4 py-3";

/** 状态徽章基础 —— 低饱和 + ring，DESIGN.md §7 */
export const badgeBaseCls =
  "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium";

/** 通用徽章配色（按语义） */
export const badgeStyles = {
  success: "bg-emerald-400/10 text-emerald-300 ring-1 ring-emerald-400/20",
  running: "bg-sky-400/10 text-sky-300 ring-1 ring-sky-400/20 animate-pulse",
  danger: "bg-red-400/10 text-red-300 ring-1 ring-red-400/20",
  warning: "bg-amber-400/10 text-amber-300 ring-1 ring-amber-400/20",
  neutral: "bg-slate-400/10 text-slate-300 ring-1 ring-slate-400/20",
  muted: "bg-slate-400/5 text-slate-500 ring-1 ring-slate-400/10",
} as const;

export type BadgeTone = keyof typeof badgeStyles;
