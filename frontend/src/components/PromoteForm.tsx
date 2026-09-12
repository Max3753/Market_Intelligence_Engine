"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, ArrowUp, TriangleAlert } from "lucide-react";
import { api } from "@/lib/api";
import { inputCls, secondaryBtnCls, successBtnCls, focusRingCls } from "@/lib/ui";

/**
 * 「升级为机会」表单 —— Human-in-the-Loop 的签字动作。
 * 客户端组件：需要表单状态与提交交互。
 */
export default function PromoteForm({
  clusterId,
  sourceCount,
}: {
  clusterId: number;
  sourceCount: number;
}) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [problemStatement, setProblemStatement] = useState("");
  const [targetCustomer, setTargetCustomer] = useState("");
  const [proposedSolution, setProposedSolution] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [drafting, setDrafting] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);

  const isSingleSource = sourceCount < 2;

  /** LLM 起草 —— 基于簇内信号生成三个字段的草稿，人修改后提交 */
  async function handleDraft() {
    setError(null);
    setDrafting(true);
    try {
      const draft = await api<{
        problem_statement?: string;
        target_customer?: string;
        proposed_solution?: string;
      }>("/opportunities/draft", {
        method: "POST",
        body: JSON.stringify({ cluster_id: clusterId }),
      });
      setProblemStatement(draft.problem_statement ?? "");
      setTargetCustomer(draft.target_customer ?? "");
      setProposedSolution(draft.proposed_solution ?? "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "起草失败");
    } finally {
      setDrafting(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api("/opportunities", {
        method: "POST",
        body: JSON.stringify({
          cluster_id: clusterId,
          title,
          problem_statement: problemStatement || null,
          target_customer: targetCustomer || null,
          proposed_solution: proposedSolution || null,
          acknowledge_single_source: acknowledged,
        }),
      });
      setOpen(false);
      router.refresh();   // 触发 server component 重新取数，机会列表立刻更新
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败");
    } finally {
      setSubmitting(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className={successBtnCls + " mt-6"}
      >
        <ArrowUp className="mr-1.5 inline h-4 w-4" />
        升级为机会
      </button>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="mt-6 rounded-xl border border-white/5 bg-slate-800/60 p-5 shadow-lg shadow-black/20">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-white">升级为产品机会</h3>
        <button
          type="button"
          onClick={handleDraft}
          disabled={drafting}
          className={`rounded-lg bg-sky-500 px-3 py-1 text-xs font-medium text-white transition-all duration-200 hover:bg-sky-400 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed ${focusRingCls}`}
        >
          {drafting ? "起草中…" : (
            <>
              <Sparkles className="mr-1 inline h-3.5 w-3.5" />
              LLM 起草
            </>
          )}
        </button>
      </div>
      <p className="mt-1 text-xs text-slate-400">
        这是人工决策门——确认这个簇值得追。可先让 LLM 起草再修改；title 必填。
      </p>

      <div className="mt-4 space-y-3">
        <div>
          <label className="mb-1 block text-xs text-slate-400">机会名称 *</label>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            placeholder="例：平台静默行为聚合提醒插件"
            className={inputCls}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-400">问题陈述</label>
          <textarea
            value={problemStatement}
            onChange={(e) => setProblemStatement(e.target.value)}
            rows={2}
            placeholder="这个机会解决什么问题？"
            className={inputCls}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-400">目标用户</label>
          <input
            value={targetCustomer}
            onChange={(e) => setTargetCustomer(e.target.value)}
            placeholder="例：重度 SaaS 工具使用者"
            className={inputCls}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-400">方案设想</label>
          <textarea
            value={proposedSolution}
            onChange={(e) => setProposedSolution(e.target.value)}
            rows={2}
            placeholder="你打算怎么做？"
            className={inputCls}
          />
        </div>
      </div>

      {isSingleSource && (
        <div className="mt-3 rounded-lg border-l-2 border-amber-400/40 bg-amber-400/5 px-3 py-2 text-xs text-amber-300">
          <p className="flex items-start gap-1.5">
            <TriangleAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span>
              该簇证据仅来自 <b>1 个数据源</b>（单源信号，等待交叉验证）。
              立项后状态将自动设为 <b>EVIDENCE_GATHERING</b>。
            </span>
          </p>
          <label className="mt-2 flex cursor-pointer items-center gap-2">
            <input
              type="checkbox"
              checked={acknowledged}
              onChange={(e) => setAcknowledged(e.target.checked)}
              className="h-3.5 w-3.5 accent-amber-400"
            />
            已知晓单源风险，仍要立项
          </label>
        </div>
      )}

      {error && (
        <p className="mt-3 rounded-lg border-l-2 border-red-400/40 bg-red-400/5 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}

      <div className="mt-4 flex gap-2">
        <button
          type="submit"
          disabled={submitting || !title.trim() || (isSingleSource && !acknowledged)}
          className={successBtnCls}
        >
          {submitting ? "提交中…" : "确认立项"}
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className={secondaryBtnCls}
        >
          取消
        </button>
      </div>
    </form>
  );
}
