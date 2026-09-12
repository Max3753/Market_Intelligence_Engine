"use client";

import { motion } from "framer-motion";

/**
 * 页面过渡 —— 淡入 + 轻微上移，framer-motion。
 * 包在 server component 页面内容外层，提供一致的入场动效。
 * 尊重 prefers-reduced-motion（framer-motion 默认处理）。
 */
export default function PageTransition({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
}
