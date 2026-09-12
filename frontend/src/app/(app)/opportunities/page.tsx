import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import OpportunitiesList from "@/components/OpportunitiesList";
import EmptyState from "@/components/EmptyState";
import { getClusters, getOpportunities } from "@/lib/api";
import { interactiveCardCls, sectionTitleCls, sectionTitleBarCls } from "@/lib/ui";
import { TriangleAlert, CheckCircle2 } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function OpportunitiesPage() {
  // 并行取：人工确认的机会 + 全部簇（用于算候选集）
  const [opps, clusters] = await Promise.all([getOpportunities(), getClusters()]);

  // 已立项的簇不再是候选
  const promotedClusterIds = new Set(opps.map((o) => o.cluster_id));
  const candidates = clusters.filter((c) => !promotedClusterIds.has(c.id));

  return (
    <>
      <PageHeader title="Opportunities" subtitle="人工确认的产品机会 · Human-in-the-Loop" />

      {/* ── 已确认机会（含排序/筛选/状态流转）── */}
      <div className={`${sectionTitleCls} mb-4`}>
        <span className={sectionTitleBarCls} />
        <h2 className="text-lg font-semibold">已确认机会</h2>
      </div>
      <OpportunitiesList opportunities={opps} />

      {/* ── 候选簇（未立项）── */}
      <div className={`${sectionTitleCls} mb-4`}>
        <span className={sectionTitleBarCls} />
        <h2 className="text-lg font-semibold">候选簇（未立项）</h2>
      </div>
      {candidates.length === 0 ? (
        <EmptyState
          title="所有簇都已处理完毕"
          description="没有待立项的候选簇。新簇聚类完成后会自动出现在这里。"
          icon={<CheckCircle2 className="h-6 w-6" />}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {candidates.map((c) => (
            <Link
              key={c.id}
              href={`/clusters/${c.id}`}
              className={`group block ${interactiveCardCls}`}
            >
              <div className="flex items-start justify-between">
                <h3 className="text-base font-semibold text-white">{c.name}</h3>
                <span className="text-lg font-semibold tabular-nums text-emerald-400">
                  {c.demand_score?.toFixed(1) ?? "—"}
                </span>
              </div>
              <p className="mt-2 line-clamp-2 text-sm text-slate-400">{c.description}</p>
              <div className="mt-3 flex gap-4 text-xs text-slate-500">
                <span className="tabular-nums">信号数 {c.document_count ?? 0}</span>
                <span className="tabular-nums">独立用户 {c.unique_user_count ?? 0}</span>
                {c.source_count < 2 ? (
                  <span className="inline-flex items-center gap-1 text-amber-400">
                    <TriangleAlert className="h-3.5 w-3.5" />
                    单源
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-emerald-400">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    双源
                  </span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
