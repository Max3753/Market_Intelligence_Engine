"""API routes for Opportunities — the Human-in-the-Loop gate.

Clusters are machine-produced; Opportunities are human-confirmed directions.
Promotion through this router is THE decision gate between the two.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.intelligence.llm_client import chat_json
from app.intelligence.opportunity_analyzer import _json_dumps, analyze_opportunity
from app.intelligence.opportunity_relink import relink_opportunity
from app.models.demand import DemandCluster, DemandSignal
from app.models.opportunity import Opportunity, OpportunityAnalysis
from app.schemas import (
    OpportunityAnalysisRead,
    OpportunityCreate,
    OpportunityDraftRequest,
    OpportunityRead,
    OpportunityRelinkRequest,
    OpportunityStatusUpdate,
)

router = APIRouter(prefix="/opportunities", tags=["opportunities"])

# LLM 起草 prompt —— 起草 ≠ 决定，最终签字的是人
DRAFT_SYSTEM_PROMPT = """You are a product analyst drafting an opportunity brief.

Given demand signals extracted from real user complaints (multiple users expressing
the same underlying need), draft a product opportunity. Respond with STRICT JSON only:

{
  "problem_statement": "<1-2 sentences: the shared problem, grounded in the signals>",
  "target_customer": "<who suffers from this most>",
  "proposed_solution": "<1-2 sentences: a concrete product direction>"
}

Rules:
- Ground every claim in the given signals; do NOT invent features nobody asked for
- Be specific, not generic
"""

# 显式状态流转表 —— 数据即文档；REJECTED/DORMANT 为终态（DORMANT 可复活回起点）
VALID_TRANSITIONS: dict[str, set[str]] = {
    "DISCOVERED": {"EVIDENCE_GATHERING", "HUMAN_REVIEW", "REJECTED", "DORMANT"},
    "EVIDENCE_GATHERING": {"HUMAN_REVIEW", "INTERVIEW", "REJECTED", "DORMANT"},
    "HUMAN_REVIEW": {"INTERVIEW", "REJECTED", "DORMANT"},
    "INTERVIEW": {"VALIDATED", "REJECTED", "DORMANT"},
    "VALIDATED": {"MVP", "REJECTED", "DORMANT"},
    "MVP": {"EARLY_USERS", "DORMANT"},
    "EARLY_USERS": {"PAID", "DORMANT"},
    "PAID": {"SCALED", "DORMANT"},
    "SCALED": set(),
    "REJECTED": set(),
    "DORMANT": {"DISCOVERED"},
}


def _require_valid_transition(current: str, new: str) -> None:
    if new not in VALID_TRANSITIONS.get(current, set()):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid transition: {current} -> {new}",
        )


@router.post("", response_model=OpportunityRead)
async def create_opportunity(
    payload: OpportunityCreate, db: AsyncSession = Depends(get_db)
):
    """Promote a cluster to an opportunity — the human decision gate."""
    # 1. 簇必须存在
    cluster = await db.get(DemandCluster, payload.cluster_id)
    if cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")

    # 2. 一个簇只能有一个机会（占用校验）
    existing = await db.scalar(
        select(Opportunity).where(Opportunity.cluster_id == payload.cluster_id)
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Cluster already has opportunity #{existing.id}",
        )

    # 3. 单源门禁：软警告 + 勾选确认。未确认的单源簇拒绝立项
    is_single_source = (cluster.source_count or 0) < 2
    if is_single_source and not payload.acknowledge_single_source:
        raise HTTPException(
            status_code=422,
            detail=(
                "Cluster evidence comes from a single source — awaiting cross-validation. "
                "Set acknowledge_single_source=true to promote anyway."
            ),
        )

    # 4. market_score / source_count 快照 —— 记录创建那一刻的状态，簇漂移不篡改历史依据
    opp = Opportunity(
        cluster_id=payload.cluster_id,
        title=payload.title,
        problem_statement=payload.problem_statement,
        target_customer=payload.target_customer,
        proposed_solution=payload.proposed_solution,
        market_score=cluster.demand_score,
        source_count=cluster.source_count,
        # 单源立项 → 语义编码为 EVIDENCE_GATHERING（等待交叉验证）
        validation_status="EVIDENCE_GATHERING" if is_single_source else "DISCOVERED",
    )
    db.add(opp)
    await db.commit()
    return opp


@router.get("", response_model=list[OpportunityRead])
async def list_opportunities(db: AsyncSession = Depends(get_db)):
    """All opportunities — priority first, then by snapshot score.

    每个机会嵌套其可行性分析（若有）。
    """
    result = await db.execute(
        select(Opportunity)
        .options(selectinload(Opportunity.analysis))
        .order_by(
            Opportunity.priority.desc(),
            Opportunity.market_score.desc().nulls_last(),
        )
    )
    return list(result.scalars())


@router.get("/{opportunity_id}", response_model=OpportunityRead)
async def get_opportunity(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    opp = await db.get(Opportunity, opportunity_id)
    if opp is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp


@router.patch("/{opportunity_id}/status", response_model=OpportunityRead)
async def update_opportunity_status(
    opportunity_id: int,
    payload: OpportunityStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Advance / reject / revive an opportunity along the validation funnel."""
    opp = await db.get(Opportunity, opportunity_id)
    if opp is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    _require_valid_transition(opp.validation_status, payload.new_status)

    # 否决必须留理由 —— 被否决的机会是组织记忆
    if payload.new_status == "REJECTED" and not (
        payload.note and payload.note.strip()
    ):
        raise HTTPException(status_code=422, detail="Rejection requires a note")

    opp.validation_status = payload.new_status
    if payload.note:
        opp.rejection_note = payload.note      # 非 REJECTED 的 note 也存（如 DORMANT 原因）
    await db.commit()
    return opp


@router.post("/draft")
async def draft_opportunity(
    payload: OpportunityDraftRequest, db: AsyncSession = Depends(get_db)
):
    """LLM drafts problem_statement/target_customer/solution from cluster signals.

    起草 ≠ 决定 —— 返回的草稿供人修改后通过 POST /opportunities 正式提交。
    """
    cluster = await db.get(DemandCluster, payload.cluster_id)
    if cluster is None:
        raise HTTPException(status_code=404, detail="Cluster not found")

    result = await db.execute(
        select(DemandSignal).where(DemandSignal.cluster_id == payload.cluster_id)
    )
    signals = result.scalars().all()
    if not signals:
        raise HTTPException(status_code=422, detail="Cluster has no member signals")

    # 汇总成员信号作为起草素材
    lines = []
    for s in signals:
        parts = [f"type={s.demand_type}"]
        if s.problem:
            parts.append(f"problem: {s.problem}")
        if s.desired_outcome:
            parts.append(f"wants: {s.desired_outcome}")
        if s.job_to_be_done:
            parts.append(f"job: {s.job_to_be_done}")
        lines.append("; ".join(parts))

    try:
        draft = await chat_json(DRAFT_SYSTEM_PROMPT, "\n".join(lines))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM draft failed: {e}")

    return {
        "problem_statement": draft.get("problem_statement"),
        "target_customer": draft.get("target_customer"),
        "proposed_solution": draft.get("proposed_solution"),
    }


@router.post("/{opportunity_id}/relink", response_model=OpportunityRead)
async def relink_opportunity_endpoint(
    opportunity_id: int,
    payload: OpportunityRelinkRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Re-attach an orphaned opportunity (cluster_id=null) to a current cluster.

    rebuild 全量重建会删旧簇并把机会 cluster_id 置空（机会作为人工决策记录存活）。
    本端点把断链机会重新关联到最匹配的当前簇：默认按 problem_statement 与簇
    name/description 的关键词重叠（+可选 embedding 相似度）自动匹配；也可显式
    指定 cluster_id 人工覆盖。已关联的机会直接返回当前状态。
    """
    opp = await db.get(Opportunity, opportunity_id)
    if opp is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # 显式指定目标簇 → 人工覆盖（Human-in-the-Loop）
    if payload is not None and payload.cluster_id is not None:
        cluster = await db.get(DemandCluster, payload.cluster_id)
        if cluster is None:
            raise HTTPException(status_code=404, detail="Cluster not found")
        opp.cluster_id = cluster.id
        await db.commit()
        await db.refresh(opp, ["analysis"])
        return opp

    if opp.cluster_id is not None:
        await db.refresh(opp, ["analysis"])
        return opp  # 已关联，无需修复

    cluster, score, method = await relink_opportunity(db, opp)
    if cluster is None:
        raise HTTPException(
            status_code=422,
            detail=(
                f"No cluster matched above threshold (best score={score:.3f}, "
                f"method={method}) — pass an explicit cluster_id to override"
            ),
        )
    await db.refresh(opp, ["analysis"])
    return opp


@router.post("/{opportunity_id}/analyze", response_model=OpportunityAnalysisRead)
async def analyze_opportunity_endpoint(
    opportunity_id: int, db: AsyncSession = Depends(get_db)
):
    """生成/重新生成机会可行性分析（upsert：一个机会一条，重复生成覆盖）。

    AI 只生成分析，不改变机会 validation_status —— 决策权在人（Human-in-the-Loop）。
    """
    opp = await db.get(Opportunity, opportunity_id)
    if opp is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # 收集证据 → LLM 分析 → 兜底校验
    try:
        result = await analyze_opportunity(db, opp)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM analysis failed: {e}")

    # upsert：一个机会一条分析，重复生成覆盖旧记录
    analysis = await db.scalar(
        select(OpportunityAnalysis).where(
            OpportunityAnalysis.opportunity_id == opportunity_id
        )
    )
    if analysis is None:
        analysis = OpportunityAnalysis(opportunity_id=opportunity_id)
        db.add(analysis)

    analysis.feasibility_score = result["feasibility_score"]
    analysis.technical_feasibility = result["technical_feasibility"]
    analysis.market_feasibility = result["market_feasibility"]
    analysis.competition = result["competition"]
    analysis.risks = _json_dumps(result["risks"])
    analysis.validation_hypotheses = _json_dumps(result["validation_hypotheses"])
    analysis.action_items = _json_dumps(result["action_items"])
    analysis.summary = result["summary"]

    await db.commit()
    await db.refresh(analysis)
    return analysis
