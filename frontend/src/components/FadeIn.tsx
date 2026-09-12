"use client";

import { motion } from "framer-motion";

/**
 * 入场动画包装器 —— opacity + slide up。
 * reduced motion 由全局 MotionConfig reducedMotion="user" 处理，
 * 不在组件内条件渲染 initial（避免 SSR/客户端 hydration mismatch）。
 * 用于 server component 内部包裹需要动画的子树（如 page.tsx）。
 */
export default function FadeIn({
  children,
  delay = 0,
  className,
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: [0.16, 1, 0.3, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
