"use client";

import { useEffect, useState } from "react";
import {
  motion,
  useMotionValue,
  animate,
  useReducedMotion,
} from "framer-motion";

/**
 * 数字 count-up —— 从 0 计数到目标值。
 * 尊重 prefers-reduced-motion：用户偏好减少动画时直接跳到终值。
 */
function CountUp({ value }: { value: string | number }) {
  const reduced = useReducedMotion();
  const numTarget = typeof value === "number" ? value : parseFloat(value);
  const isNum = !isNaN(numTarget);
  const isInt = isNum && Number.isInteger(numTarget);
  const [display, setDisplay] = useState(() =>
    isNum ? (isInt ? "0" : "0.0") : String(value),
  );
  const mv = useMotionValue(0);

  useEffect(() => {
    if (!isNum) {
      setDisplay(String(value));
      return;
    }
    if (reduced) {
      setDisplay(isInt ? numTarget.toLocaleString() : numTarget.toFixed(1));
      return;
    }
    const unsub = mv.on("change", (v) => {
      setDisplay(isInt ? Math.round(v).toLocaleString() : v.toFixed(1));
    });
    const c = animate(mv, numTarget, {
      duration: 1.2,
      ease: [0.16, 1, 0.3, 1],
    });
    return () => {
      c.stop();
      unsub();
    };
  }, [numTarget, isNum, isInt, reduced, mv, value]);

  return <span>{display}</span>;
}

interface StatCardProps {
  title: string;
  value: string | number;
  /** 已渲染的图标元素（ReactNode，可跨 client/server 边界传递） */
  icon?: React.ReactNode;
  accent?: "sky" | "emerald" | "amber" | "violet";
  /** 卡片底部的小字说明（可选） */
  hint?: string;
  /** 仅当卡片可交互（如包在 Link 内）时启用 hover 提升 */
  interactive?: boolean;
  /** 入场 stagger 延迟（秒） */
  delay?: number;
}

const ACCENTS: Record<
  string,
  { bar: string; number: string; glow: string; iconBg: string }
> = {
  sky: {
    bar: "from-sky-400 to-sky-600",
    number: "text-sky-300",
    glow: "shadow-[0_10px_15px_-3px_rgba(0,0,0,0.2),0_4px_6px_-4px_rgba(0,0,0,0.2),0_0_30px_-5px_rgba(56,189,248,0.15)]",
    iconBg: "bg-sky-400/15 text-sky-400",
  },
  emerald: {
    bar: "from-emerald-400 to-emerald-600",
    number: "text-emerald-300",
    glow: "shadow-[0_10px_15px_-3px_rgba(0,0,0,0.2),0_4px_6px_-4px_rgba(0,0,0,0.2),0_0_30px_-5px_rgba(52,211,153,0.15)]",
    iconBg: "bg-emerald-400/15 text-emerald-400",
  },
  amber: {
    bar: "from-amber-400 to-amber-600",
    number: "text-amber-300",
    glow: "shadow-[0_10px_15px_-3px_rgba(0,0,0,0.2),0_4px_6px_-4px_rgba(0,0,0,0.2),0_0_30px_-5px_rgba(251,191,36,0.15)]",
    iconBg: "bg-amber-400/15 text-amber-400",
  },
  violet: {
    bar: "from-violet-400 to-violet-600",
    number: "text-violet-300",
    glow: "shadow-[0_10px_15px_-3px_rgba(0,0,0,0.2),0_4px_6px_-4px_rgba(0,0,0,0.2),0_0_30px_-5px_rgba(167,139,250,0.15)]",
    iconBg: "bg-violet-400/15 text-violet-400",
  },
};

export default function StatCard({
  title,
  value,
  icon,
  accent = "sky",
  hint,
  interactive = false,
  delay = 0,
}: StatCardProps) {
  const a = ACCENTS[accent];

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: [0.16, 1, 0.3, 1] }}
      className={`group relative overflow-hidden rounded-xl border border-white/5 bg-slate-800/60 p-5 transition-all duration-200 hover:border-white/10 ${a.glow} ${
        interactive
          ? "hover:-translate-y-0.5 hover:shadow-xl hover:shadow-black/30"
          : ""
      }`}
    >
      {/* 左侧 accent 渐变条 */}
      <div
        aria-hidden
        className={`absolute left-0 top-3 bottom-3 w-[2px] rounded-full bg-gradient-to-b ${a.bar}`}
      />
      {/* 顶部光晕 */}
      <div
        aria-hidden
        className="pointer-events-none absolute -right-6 -top-6 h-20 w-20 rounded-full bg-gradient-to-br from-white/5 to-transparent blur-xl"
      />
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
          {title}
        </p>
        {icon && (
          <span
            className={`flex h-8 w-8 items-center justify-center rounded-lg ${a.iconBg}`}
          >
            {icon}
          </span>
        )}
      </div>
      <p className={`mt-2 text-3xl font-semibold tabular-nums tracking-tight ${a.number}`}>
        <CountUp value={value} />
      </p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </motion.div>
  );
}
