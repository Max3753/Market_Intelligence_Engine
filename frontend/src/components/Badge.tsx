import { badgeBaseCls, badgeStyles, type BadgeTone } from "@/lib/ui";

interface BadgeProps {
  tone?: BadgeTone;
  className?: string;
  children: React.ReactNode;
}

/**
 * 状态徽章 —— 低饱和 + ring，DESIGN.md §7。
 * tone 决定配色；可叠加自定义 className（如自定义 ring 色）。
 */
export default function Badge({ tone = "neutral", className = "", children }: BadgeProps) {
  return (
    <span className={`${badgeBaseCls} ${badgeStyles[tone]} ${className}`}>
      {children}
    </span>
  );
}
