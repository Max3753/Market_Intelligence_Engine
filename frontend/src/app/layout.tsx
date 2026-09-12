import "./globals.css"
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Market Intelligence Engine",
  description: "Evidence-driven Product Discovery System",
};

/**
 * 根布局 —— 只负责 html/body + 全局氛围背景。
 * 应用壳（Sidebar + 主内容区）在 (app)/layout.tsx，落地页在 /page.tsx。
 * 环境光晕用 fixed 而非 absolute，保证滚动页面（落地页）与应用壳（h-screen）都覆盖。
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="relative min-h-screen bg-slate-950 text-slate-200 antialiased">
        {/* 环境光晕 —— 深炭蓝基底上的微妙氛围光 */}
        <div
          aria-hidden
          className="pointer-events-none fixed inset-0 z-0"
          style={{
            background:
              "radial-gradient(1200px 600px at 15% -10%, rgba(56,189,248,0.08), transparent 60%), radial-gradient(1000px 500px at 100% 0%, rgba(52,211,153,0.05), transparent 55%), linear-gradient(180deg, #0b1120 0%, #0f172a 100%)",
          }}
        />
        {/* 亚感知点阵纹理 —— Linear 式材质感 */}
        <div
          aria-hidden
          className="pointer-events-none fixed inset-0 z-0 opacity-[0.015]"
          style={{
            backgroundImage:
              "radial-gradient(circle, rgba(255,255,255,1) 1px, transparent 1px)",
            backgroundSize: "24px 24px",
          }}
        />
        {children}
      </body>
    </html>
  );
}