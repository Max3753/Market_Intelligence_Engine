import Link from "next/link";
import {
  ArrowRight,
  Globe,
  Eraser,
  Tags,
  Search,
  Boxes,
  Star,
  Lightbulb,
  Shield,
  Users,
  GitMerge,
  TrendingUp,
  ChevronRight,
  ChevronDown,
} from "lucide-react";
import MotionProvider from "@/components/MotionProvider";
import ScrollReveal from "@/components/ScrollReveal";
import SiteNav from "@/components/SiteNav";
import "./landing.css";

/** 流水线七阶段 —— 与 README 架构图一致 */
const PIPELINE_STEPS = [
  { icon: Globe, label: "数据采集", desc: "多平台适配器" },
  { icon: Eraser, label: "清洗去重", desc: "标准化与去重" },
  { icon: Tags, label: "内容分类", desc: "需求类型识别" },
  { icon: Search, label: "需求抽取", desc: "痛点与场景提取" },
  { icon: Boxes, label: "向量聚类", desc: "语义相似聚合" },
  { icon: Star, label: "需求评分", desc: "多维量化排序" },
  { icon: Lightbulb, label: "机会引擎", desc: "产品方向推荐" },
];

/** 核心特性 —— bento 网格，1/4 宽卡、2/3 窄卡 */
const FEATURES = [
  {
    icon: Shield,
    title: "Evidence First",
    desc: "每个需求结论可追溯到原始帖子和评论，决策有据可依，不靠直觉拍板。",
    span: "md:col-span-2",
  },
  {
    icon: Users,
    title: "Human-in-the-Loop",
    desc: "AI 负责发现与整理，人做最终判断。单源门禁、否决留理由。",
    span: undefined,
  },
  {
    icon: GitMerge,
    title: "多源交叉验证",
    desc: "Reddit、GitHub、Hacker News 等多平台信号交叉验证，过滤噪声。",
    span: undefined,
  },
  {
    icon: TrendingUp,
    title: "趋势识别",
    desc: "自动追踪需求变化趋势，发现增长信号，先于竞品洞察方向。",
    span: "md:col-span-2",
  },
];

/** 项目四原则 */
const PRINCIPLES = [
  {
    title: "Evidence First",
    desc: "证据优先。每个需求结论必须可追溯到原始证据，不允许无据推测。",
  },
  {
    title: "User Behavior > User Opinion",
    desc: "真实行为数据优先于用户主观意愿。用户说的和做的往往不一样。",
  },
  {
    title: "Demand > Feature",
    desc: "优先识别问题和任务，而非功能愿望。痛点比功能清单更有价值。",
  },
  {
    title: "Human in the Loop",
    desc: "AI 做发现和整理，人做最终判断。决策支持，而非决策替代。",
  },
];

/** 主 CTA —— 全页统一标签 */
const PRIMARY_CTA = {
  href: "/dashboard",
  label: "进入控制台",
};

export default function LandingPage() {
  return (
    <MotionProvider>
      <SiteNav />
      <main className="relative z-10">
        {/* ── Hero：价值主张 + 仪表盘截图槽位 ── */}
        <section id="top" className="relative flex min-h-[100dvh] items-center">
          <div className="mx-auto w-full max-w-7xl px-8 py-16">
            <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-5">
              {/* 左：品牌 + 价值主张 + CTA */}
              <div className="lg:col-span-2">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-sky-400 to-emerald-400 text-base font-bold text-slate-950 shadow-lg shadow-sky-500/20">
                    M
                  </div>
                  <div className="leading-tight">
                    <div className="text-sm font-semibold text-white">MIE</div>
                    <div className="text-[10px] text-slate-400">
                      Market Intelligence
                    </div>
                  </div>
                </div>

                <h1 className="mt-8 text-4xl font-semibold leading-tight tracking-tight text-white md:text-5xl lg:text-[3.25rem]">
                  从用户声音中
                  <br />
                  发现产品机会
                </h1>

                <p className="mt-5 max-w-md text-base leading-relaxed text-slate-400">
                  持续监听 Reddit、GitHub、Hacker News 等多平台用户行为，自动提取需求信号并聚类评分，找到真正值得做的产品机会。
                </p>

                <div className="mt-8 flex flex-wrap items-center gap-3">
                  <Link
                    href={PRIMARY_CTA.href}
                    className="inline-flex items-center gap-2 rounded-lg bg-sky-500 px-5 py-2.5 text-sm font-medium text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-sky-400 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400/50 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
                  >
                    {PRIMARY_CTA.label}
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>

              {/* 右：仪表盘截图 */}
              <div className="lg:col-span-3">
                <div className="relative mx-auto w-full max-w-md overflow-hidden rounded-xl border border-white/10 bg-slate-800/60 shadow-2xl shadow-black/40 transition-all duration-200 hover:-translate-y-0.5 hover:border-white/20 hover:shadow-2xl hover:shadow-black/50 lg:max-w-none">
                  <img
                    src="/dashboard-screenshot.png"
                    alt="Market Intelligence Engine 仪表盘"
                    className="w-full"
                    loading="eager"
                  />
                  <div
                    aria-hidden
                    className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-sky-400/50 to-transparent"
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── 流水线：七阶段可视化流程 ── */}
        <section id="pipeline" className="scroll-mt-24 py-24">
          <div className="mx-auto max-w-7xl px-8">
            <ScrollReveal>
              <div className="mb-12 text-center">
                <h2 className="text-2xl font-semibold text-white md:text-3xl">
                  完整的智能流水线
                </h2>
                <p className="mt-3 text-slate-400">
                  从数据采集到机会发现，端到端自动化
                </p>
              </div>
            </ScrollReveal>

            <ScrollReveal>
              <div className="hide-scrollbar flex flex-col items-center gap-0 pb-2 md:flex-row md:items-center md:justify-center md:gap-0 md:overflow-x-auto">
                {PIPELINE_STEPS.map((step, i) => {
                  const Icon = step.icon;
                  return (
                    <div
                      key={step.label}
                      className="group flex flex-col items-center gap-2 md:shrink-0"
                    >
                      <div className="flex flex-col items-center gap-1.5 md:w-[88px]">
                        <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-white/5 bg-slate-800/60 shadow-md shadow-black/10 transition-all duration-200 group-hover:-translate-y-0.5 group-hover:border-sky-400/30">
                          <Icon className="h-5 w-5 text-sky-400 transition-transform duration-200 group-hover:scale-110" />
                        </div>
                        <span className="whitespace-nowrap text-xs font-medium text-slate-200">
                          {step.label}
                        </span>
                        <span className="hidden text-center text-[11px] text-slate-400 md:block">
                          {step.desc}
                        </span>
                      </div>
                      {i < PIPELINE_STEPS.length - 1 && (
                        <div className="flex shrink-0 items-center justify-center py-2 md:flex-col md:px-1 md:py-0">
                          <ChevronRight className="hidden h-4 w-4 text-slate-600 md:block" />
                          <ChevronDown className="block h-4 w-4 text-slate-600 md:hidden" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </ScrollReveal>
          </div>
        </section>

        {/* ── 核心特性：bento 网格 ── */}
        <section id="features" className="scroll-mt-24 py-24">
          <div className="mx-auto max-w-7xl px-8">
            <ScrollReveal>
              <div className="mb-12 text-center">
                <h2 className="text-2xl font-semibold text-white md:text-3xl">
                  核心能力
                </h2>
                <p className="mt-3 text-slate-400">
                  为产品决策者设计的四大核心能力
                </p>
              </div>
            </ScrollReveal>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {FEATURES.map((feature) => {
                const Icon = feature.icon;
                const wide = feature.span === "md:col-span-2";
                return (
                  <ScrollReveal key={feature.title} className={feature.span}>
                    <div
                      className={`group flex h-full flex-col rounded-xl border p-6 shadow-lg shadow-black/20 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-black/30 ${
                        wide
                          ? "border-sky-400/10 bg-gradient-to-br from-slate-800/80 via-slate-800/60 to-sky-900/20 hover:border-sky-400/30"
                          : "border-white/5 bg-slate-800/60 hover:border-white/10"
                      }`}
                    >
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-400/10 transition-transform duration-200 group-hover:scale-110">
                        <Icon className="h-5 w-5 text-sky-400" />
                      </div>
                      <h3 className="mt-4 text-base font-semibold text-white">
                        {feature.title}
                      </h3>
                      <p className="mt-2 text-sm leading-relaxed text-slate-400">
                        {feature.desc}
                      </p>
                    </div>
                  </ScrollReveal>
                );
              })}
            </div>
          </div>
        </section>

        {/* ── 真实数据展示区：全宽截图槽位 ── */}
        <section id="data" className="scroll-mt-24 py-24">
          <div className="mx-auto max-w-7xl px-8">
            <ScrollReveal>
              <div className="mb-12 text-center">
                <h2 className="text-2xl font-semibold text-white md:text-3xl">
                  数据驱动的决策支持
                </h2>
                <p className="mt-3 text-slate-400">
                  仪表盘实时展示需求信号、趋势变化与机会评分
                </p>
              </div>
            </ScrollReveal>

            <ScrollReveal>
              <div className="mx-auto w-full max-w-[1200px] overflow-hidden rounded-xl border border-white/10 bg-slate-900/50 shadow-2xl shadow-black/40 transition-all duration-200 hover:-translate-y-0.5 hover:border-white/20 hover:shadow-2xl hover:shadow-black/50">
                <img
                  src="/dashboard-screenshot.png"
                  alt="Market Intelligence Engine 仪表盘全览"
                  className="w-full"
                  loading="lazy"
                />
              </div>
            </ScrollReveal>
          </div>
        </section>

        {/* ── 原则区：四原则卡片 ── */}
        <section id="principles" className="scroll-mt-24 py-24">
          <div className="mx-auto max-w-7xl px-8">
            <ScrollReveal>
              <div className="mb-12 text-center">
                <h2 className="text-2xl font-semibold text-white md:text-3xl">
                  核心原则
                </h2>
                <p className="mt-3 text-slate-400">
                  指导每一次产品发现决策的基础理念
                </p>
              </div>
            </ScrollReveal>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {PRINCIPLES.map((p, i) => (
                <ScrollReveal key={p.title}>
                  <div className="flex h-full flex-col rounded-xl border border-white/5 bg-slate-800/60 p-6 shadow-lg shadow-black/20 transition-all duration-200 hover:-translate-y-0.5 hover:border-white/10 hover:shadow-xl hover:shadow-black/30">
                    <span className="text-3xl font-bold tabular-nums text-sky-400/20">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <h3 className="mt-2 text-base font-semibold text-white">
                      {p.title}
                    </h3>
                    <p className="mt-2 text-sm leading-relaxed text-slate-400">
                      {p.desc}
                    </p>
                  </div>
                </ScrollReveal>
              ))}
            </div>
          </div>
        </section>

        {/* ── CTA ── */}
        <section className="py-24">
          <div className="mx-auto max-w-7xl px-8 text-center">
            <ScrollReveal>
              <h2 className="text-2xl font-semibold text-white md:text-3xl">
                从噪声中发现信号
              </h2>
              <p className="mt-4 text-slate-400">
                让数据告诉你，用户真正需要什么
              </p>
              <Link
                href={PRIMARY_CTA.href}
                className="mt-8 inline-flex items-center gap-2 rounded-lg bg-sky-500 px-6 py-3 text-sm font-medium text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-sky-400 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400/50 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
              >
                {PRIMARY_CTA.label}
                <ArrowRight className="h-4 w-4" />
              </Link>
            </ScrollReveal>
          </div>
        </section>

        {/* ── Footer ── */}
        <footer className="border-t border-white/5 py-8">
          <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-8 md:flex-row">
            <div className="flex items-center gap-2.5">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-br from-sky-400 to-emerald-400 text-[10px] font-bold text-slate-950">
                M
              </div>
              <span className="text-sm font-medium text-slate-300">MIE</span>
            </div>
            <p className="text-xs text-slate-500">
              Market Intelligence Engine · Evidence-driven Product Discovery
            </p>
          </div>
        </footer>
      </main>
    </MotionProvider>
  );
}