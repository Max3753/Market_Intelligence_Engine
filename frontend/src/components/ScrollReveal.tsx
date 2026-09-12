"use client";

import { motion } from "framer-motion";

/**
 * 滚动入场动画包装器 —— whileInView 触发，仅执行一次。
 * reducedMotion 由上层 MotionProvider(reducedMotion="user") 统一处理。
 */
export default function ScrollReveal({
  children,
  className,
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.15 }}
      transition={{ duration: 0.55, delay, ease: [0.16, 1, 0.3, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
