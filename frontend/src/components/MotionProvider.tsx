"use client";

import { MotionConfig } from "framer-motion";

/**
 * framer-motion 全局配置 —— reducedMotion="user" 让所有 motion 组件
 * 自动响应系统 prefers-reduced-motion（禁用 transform/layout 动画，保留 opacity）。
 * 避免在各组件里用 useReducedMotion() 条件渲染 initial 导致 hydration mismatch。
 */
export default function MotionProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  return <MotionConfig reducedMotion="user">{children}</MotionConfig>;
}