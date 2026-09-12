import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import PromoteForm from "@/components/PromoteForm";
import ClusterRadar from "@/components/charts/ClusterRadar";
import EmptyState from "@/components/EmptyState";
import { focusRingCls, cardCls, sectionTitleCls, sectionTitleBarCls } from "@/lib/ui";
import { BASE_URL } from "@/lib/api";
import { TriangleAlert, CheckCircle2 } from "lucide-react";
import Badge from "@/components/Badge";

export const dynamic = "force-dynamic";

/** GET /clusters/{id}/detail 的响应结构 */
interface ClusterDetail {
  cluster: {
    id: number;
    name: string;
    description: string | null;
    demand_score: number | null;
    pain_score: number | null;
    frequency_score: number | null;
    money_score: number | null;
    growth_score: number | null;
    competition_gap: number | null;
    document_count: number | null;
    unique_user_count: number | null;
    source_count: number;
  };
  members: Array<{
    signal_id: number;
    demand_type: string;
    problem: string | null;
    severity: number | null;
    confidence: number | null;
    document_title: string;
    document_url: string;
    evidences: Array<{ snippet: string | null; relevance: number | null }>;
  }>;
}

// 后端没有现成的取数函数 —— 组装型接口直接在页面里 fetch
async function getClusterDetail(id: string): Promise<ClusterDetail> {
  const res = await fetch(`${BASE_URL}/clusters/${id}/detail`);
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

export default async function ClusterDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;     // Next.js 15：params 是 Promise，要 await
}) {
  const { id } = await params;
  const { cluster, members } = await getClusterDetail(id);

  // 8 维评分 → 雷达图数据
  const radarData = [
    { dimension: "痛点", value: cluster.pain_score ?? 0 },
    { dimension: "频率", value: cluster.frequency_score ?? 0 },
    { dimension: "付费意愿", value: cluster.money_score ?? 0 },
    { dimension: "增长", value: cluster.growth_score ?? 0 },
    { dimension: "竞争缺口", value: cluster.competition_gap ?? 0 },
    { dimension: "综合", value: (cluster.demand_score ?? 0) / 10 },
  ];

  return (
    <>
      <PageHeader title={cluster.name} subtitle={`需求簇 #${cluster.id} · 综合分 ${cluster.demand_score?.toFixed(1) ?? "未评分"}`} />

      <p className="text-sm text-slate-400">{cluster.description}</p>

      <div className="mt-4 flex gap-4 text-xs text-slate-500">
        <span className="tabular-nums">信号数 {cluster.document_count}</span>
        <span className="tabular-nums">独立用户 {cluster.unique_user_count}</span>
        {cluster.source_count < 2 ? (
          <Badge tone="warning">
            <TriangleAlert className="h-3 w-3" />
            单源 等待交叉验证
          </Badge>
        ) : (
          <Badge tone="success">
            <CheckCircle2 className="h-3 w-3" />
            双源
          </Badge>
        )}
      </div>

      {/* 8 维评分画像 */}
      <div className="mt-6 rounded-xl border border-white/5 bg-slate-800/60 p-5 shadow-lg shadow-black/20">
        <div className={sectionTitleCls}>
          <span className={sectionTitleBarCls} />
          <h3>评分画像</h3>
        </div>
        <p className="mt-1 text-xs text-slate-500">六维评分雷达 · 满分 10</p>
        <div className="mt-4">
          <ClusterRadar data={radarData} />
        </div>
      </div>

      {/* Human-in-the-Loop：人工确认门 */}
      <PromoteForm clusterId={cluster.id} sourceCount={cluster.source_count} />

      {/* 成员信号 + 证据 */}
      <div className={`${sectionTitleCls} mb-3 mt-8`}>
        <span className={sectionTitleBarCls} />
        <h2 className="text-lg font-semibold">成员信号</h2>
      </div>
      <div className="flex flex-col gap-4">
        {members.length === 0 ? (
          <EmptyState
            title="暂无成员信号"
            description="该簇还没有关联的需求信号，可能正在聚类中"
          />
        ) : (
          members.map((m) => (
            <div key={m.signal_id} className={cardCls}>
              <div className="flex items-center justify-between">
                <a
                  href={m.document_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`font-medium text-sky-300 transition-colors hover:text-sky-200 hover:underline ${focusRingCls}`}
                >
                  {m.document_title}
                </a>
                <span className="tabular-nums text-xs text-slate-500">severity {m.severity ?? "—"}</span>
              </div>
              <p className="mt-2 text-sm text-slate-300">{m.problem ?? "—"}</p>

              {/* 证据引用 —— Evidence First 的可视化 */}
              {m.evidences.length > 0 && (
                <blockquote className="mt-3 border-l-2 border-emerald-400/40 pl-3 text-sm italic text-slate-400">
                  “{m.evidences[0].snippet}”
                </blockquote>
              )}
            </div>
          ))
        )}
      </div>

      <Link href="/opportunities" className={`mt-6 inline-block text-sm text-slate-500 transition-colors hover:text-slate-300 ${focusRingCls}`}>
        ← 返回机会榜
      </Link>
    </>
  );
}
