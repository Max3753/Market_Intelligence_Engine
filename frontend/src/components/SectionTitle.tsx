import { sectionTitleBarCls, sectionTitleCls } from "@/lib/ui";

interface SectionTitleProps {
  icon?: React.ReactNode;
  children: React.ReactNode;
}

/**
 * 区块标题 —— 左侧 3px accent 竖条，DESIGN.md §7。
 * 替代 console 里散落的 SectionTitle 实现，全站统一。
 */
export default function SectionTitle({ icon, children }: SectionTitleProps) {
  return (
    <div className={sectionTitleCls}>
      <span className={sectionTitleBarCls} />
      <h2 className="flex items-center gap-1.5">
        {icon}
        {children}
      </h2>
    </div>
  );
}
