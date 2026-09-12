"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, MessageSquare, Target, Settings } from "lucide-react";
import { focusRingCls } from "@/lib/ui";

const NAV_ITEMS = [
  { label: "仪表盘", href: "/dashboard", icon: LayoutDashboard },
  { label: "需求信号", href: "/demands", icon: MessageSquare },
  { label: "机会榜", href: "/opportunities", icon: Target },
  { label: "控制台", href: "/console", icon: Settings },
];

/**
 * 侧边栏 —— 桌面端 w-56 全宽；移动端（<md）收窄为图标栏，
 * 保留导航可达性，不引入汉堡菜单等大改。
 */
export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="relative z-10 flex h-screen w-14 flex-col border-r border-white/5 bg-slate-900/40 backdrop-blur-sm md:w-56">
      {/* 品牌区 —— 点击返回介绍页 */}
      <Link
        href="/"
        title="返回介绍页"
        aria-label="Market Intelligence Engine 返回介绍页"
        className={`group flex items-center justify-center gap-2.5 rounded-lg px-2 py-5 transition-opacity duration-200 hover:opacity-90 md:justify-start md:px-5 ${focusRingCls}`}
      >
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-sky-400 to-emerald-400 text-sm font-bold text-slate-950 shadow-lg shadow-sky-500/20 transition-transform duration-200 group-hover:scale-105">
          M
        </div>
        <div className="hidden leading-tight md:block">
          <div className="text-sm font-semibold text-white">MIE</div>
          <div className="text-[10px] text-slate-500">Market Intelligence</div>
        </div>
      </Link>

      {/* 导航 */}
      <nav className="flex-1 space-y-1 px-2 md:px-3">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              title={item.label}
              aria-label={item.label}
              className={`group relative flex items-center justify-center gap-2.5 rounded-lg px-2 py-2 text-sm transition-all duration-200 md:justify-start md:px-3 ${focusRingCls} ${
                active
                  ? "bg-white/5 text-white"
                  : "text-slate-400 hover:bg-white/5 hover:text-slate-100"
              }`}
            >
              {/* 激活指示条 */}
              {active && (
                <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-sky-400 shadow-[0_0_8px_rgba(56,189,248,0.6)]" />
              )}
              <Icon
                className={`h-4 w-4 shrink-0 ${
                  active ? "text-sky-400" : "text-slate-500 group-hover:text-slate-300"
                }`}
              />
              <span className="hidden md:inline">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* 版本 */}
      <div className="hidden border-t border-white/5 px-5 py-3 text-[11px] text-slate-500 md:block">
        v0.1.0
      </div>
    </aside>
  );
}