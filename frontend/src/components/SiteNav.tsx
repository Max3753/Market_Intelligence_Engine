"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useScroll, useMotionValueEvent } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { focusRingCls, primaryBtnCls } from "@/lib/ui";

/** 锚点导航 —— 与 page.tsx 各 section id 一一对应 */
const NAV_LINKS = [
  { href: "#pipeline", label: "流水线" },
  { href: "#features", label: "核心能力" },
  { href: "#data", label: "数据展示" },
  { href: "#principles", label: "核心原则" },
];

/** 主 CTA 标签 —— 与 page.tsx PRIMARY_CTA 保持一致 */
const PRIMARY_CTA_LABEL = "进入控制台";

/**
 * 落地页顶部导航 —— 初始透明，滚动后毛玻璃（backdrop-blur + 半透明 bg）。
 * 滚动状态用 framer-motion useScroll 被动监听，仅在阈值翻转时 setState，
 * 避免每帧重渲染；motion-reduce 下禁用背景过渡。
 */
export default function SiteNav() {
  const [scrolled, setScrolled] = useState(false);
  const { scrollY } = useScroll();

  useMotionValueEvent(scrollY, "change", (latest) => {
    setScrolled(latest > 16);
  });

  // 刷新时若已处于滚动位置，立即同步状态（客户端执行，无 hydration mismatch）
  useEffect(() => {
    setScrolled(window.scrollY > 16);
  }, []);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 motion-reduce:transition-none ${
        scrolled
          ? "border-b border-white/5 bg-base/70 backdrop-blur-md"
          : "border-b border-transparent bg-transparent"
      }`}
    >
      <nav
        aria-label="主导航"
        className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-8"
      >
        {/* 品牌 */}
        <Link
          href="#top"
          aria-label="Market Intelligence Engine，回到顶部"
          className={`flex items-center gap-2.5 rounded-lg ${focusRingCls}`}
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-sky-400 to-emerald-400 text-sm font-bold text-slate-950 shadow-lg shadow-sky-500/20">
            M
          </div>
          <div className="leading-tight">
            <div className="text-sm font-semibold text-white">MIE</div>
            <div className="hidden text-[10px] text-slate-400 sm:block">
              Market Intelligence
            </div>
          </div>
        </Link>

        {/* 锚点链接 —— 移动端隐藏，仅保留品牌 + CTA */}
        <div className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`relative text-sm text-slate-300 transition-colors duration-200 hover:text-white after:absolute after:-bottom-1 after:left-0 after:h-px after:w-0 after:bg-sky-400 after:transition-all after:duration-200 hover:after:w-full ${focusRingCls}`}
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* CTA */}
        <Link href="/dashboard" className={`${primaryBtnCls} inline-flex items-center gap-2`}>
          {PRIMARY_CTA_LABEL}
          <ArrowRight className="hidden h-4 w-4 sm:block" />
        </Link>
      </nav>
    </header>
  );
}