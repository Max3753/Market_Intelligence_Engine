"use client";

import { AlertTriangle, RefreshCw, ServerCrash } from "lucide-react";
import { primaryBtnCls } from "@/lib/ui";

/**
 * 路由级错误边界 —— 后端挂掉/网络失败时优雅降级，而不是白屏。
 * 必须是 client component（reset 需要交互）。
 * 区分「后端未启动」（连接类错误）与「其他错误」两类文案。
 */
function isConnectionError(message: string): boolean {
  const m = message.toLowerCase();
  return (
    m.includes("fetch failed") ||
    m.includes("failed to fetch") ||
    m.includes("networkerror") ||
    m.includes("load failed") ||
    m.includes("econnrefused") ||
    m.includes("api 5") // 5xx：服务端异常
  );
}

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const connection = isConnectionError(error.message);

  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-red-400/20 bg-slate-800/40 px-6 py-16 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-400/10 text-red-400">
        {connection ? (
          <ServerCrash className="h-6 w-6" />
        ) : (
          <AlertTriangle className="h-6 w-6" />
        )}
      </div>
      <h2 className="mt-4 text-base font-semibold text-white">
        {connection ? "无法连接后端服务" : "页面加载失败"}
      </h2>
      <p className="mt-2 max-w-sm text-sm text-slate-400">
        {connection
          ? "仪表盘需要后端 API 才能取数。请确认 uvicorn 已启动，且端口与 frontend/.env.local 的 NEXT_PUBLIC_API_URL 一致。"
          : error.message}
      </p>
      <p className="mt-1 text-xs text-slate-500">
        {connection
          ? "启动后端后点击重试即可恢复。"
          : "若页面内容缺失而非报错，可能是数据为空——各区块会显示引导提示。"}
      </p>
      <button onClick={reset} className={primaryBtnCls + " mt-4"}>
        <RefreshCw className="mr-1.5 inline h-4 w-4" />
        重试
      </button>
    </div>
  );
}