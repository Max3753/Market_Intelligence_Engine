"""Opportunity feasibility analysis — LLM 基于证据链评估机会可实现性。

demand_score 高 ≠ 可实现。本模块收集机会及其来源簇的证据，交给 LLM 生成
深入分析（技术/市场/竞争/风险/假设/行动），辅助人决策（Human-in-the-Loop：
AI 只生成分析，人做最终判断）。
"""

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.llm_client import chat_json
from app.models.demand import DemandCluster, DemandSignal
from app.models.opportunity import Opportunity

# LLM 分析 prompt —— 核心指令：demand_score 高不代表可实现，必须基于证据评估
ANALYSIS_SYSTEM_PROMPT = """You are a product feasibility analyst. Given a product
opportunity and its supporting evidence chain, assess whether it is actually
implementable and worth pursuing. Respond with STRICT JSON only:

{
  "feasibility_score": <float 0-100: overall feasibility, NOT demand strength>,
  "technical_feasibility": "<text: can this be built? what are the technical risks?>",
  "market_feasibility": "<text: is there a real, reachable market? willingness to pay?>",
  "competition": "<text: competitive landscape, existing alternatives, moat?>",
  "risks": ["<risk 1>", "<risk 2>"],
  "validation_hypotheses": ["<falsifiable hypothesis to test next>"],
  "action_items": ["<concrete next step>"],
  "summary": "<1-3 sentence overall verdict for a human decision-maker>"
}

Rules:
- A HIGH demand_score does NOT mean the opportunity is feasible. Evaluate technical
  feasibility, market feasibility, competition, and risks based on the EVIDENCE given.
- Explicitly flag weak evidence (e.g. single-source signals, low confidence, low
  source_count) and reflect it in the feasibility_score.
- Ground every claim in the provided evidence; do NOT invent facts.
- Be specific and actionable, not generic.
- LANGUAGE: All text fields (technical_feasibility, market_feasibility, competition,
  risks, validation_hypotheses, action_items, summary) MUST be written in Simplified
  Chinese (中文). Keep the JSON keys in English as specified.
"""


def _json_dumps(value: Any) -> str:
    """数组字段以 JSON 字符串落库（与 DemandSignal.pain_points 模式一致）。"""
    return json.dumps(value, ensure_ascii=False)


def _json_loads(value: Any) -> list:
    """从 JSON 字符串还原数组；空/非法时返回空列表。"""
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (TypeError, ValueError):
        return []


def _clamp_score(score: Any) -> float | None:
    """feasibility_score 夹在 0-100；非法/缺失返回 None。"""
    if score is None:
        return None
    try:
        val = float(score)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(100.0, val))


def _fallback_validate(raw: dict) -> dict:
    """兜底校验：LLM 输出缺字段时给默认值，保证契约字段齐全。"""
    return {
        "feasibility_score": _clamp_score(raw.get("feasibility_score")),
        "technical_feasibility": raw.get("technical_feasibility") or "",
        "market_feasibility": raw.get("market_feasibility") or "",
        "competition": raw.get("competition") or "",
        "risks": raw.get("risks") if isinstance(raw.get("risks"), list) else [],
        "validation_hypotheses": (
            raw.get("validation_hypotheses")
            if isinstance(raw.get("validation_hypotheses"), list)
            else []
        ),
        "action_items": (
            raw.get("action_items") if isinstance(raw.get("action_items"), list) else []
        ),
        "summary": raw.get("summary") or "",
    }


async def _collect_evidence(db: AsyncSession, opp: Opportunity) -> tuple[str, list[str]]:
    """收集证据链：机会字段 + 关联簇成员信号 + 簇评分。

    返回 (user_prompt, 附加风险提示)。cluster_id 为 null（rebuild 断链）时
    只用机会自身字段，并返回断链风险提示。
    """
    lines: list[str] = []
    extra_risks: list[str] = []

    # 机会自身字段 —— 断链时仍可用的核心依据
    lines.append("=== Opportunity ===")
    lines.append(f"title: {opp.title or ''}")
    lines.append(f"problem_statement: {opp.problem_statement or ''}")
    lines.append(f"target_customer: {opp.target_customer or ''}")
    lines.append(f"proposed_solution: {opp.proposed_solution or ''}")
    lines.append(f"market_score (snapshot): {opp.market_score}")
    lines.append(f"source_count (snapshot): {opp.source_count}")
    lines.append(f"validation_status: {opp.validation_status}")

    if opp.cluster_id is None:
        # rebuild 断链：来源簇已解绑，证据链需重建
        lines.append("=== Source cluster ===")
        lines.append("(unbound — cluster was deleted by a rebuild)")
        extra_risks.append("来源簇已解绑，证据链需重建")
        return "\n".join(lines), extra_risks

    cluster = await db.get(DemandCluster, opp.cluster_id)
    if cluster is None:
        # 簇记录缺失（理论上不应发生，防御处理）
        lines.append("=== Source cluster ===")
        lines.append("(missing)")
        extra_risks.append("来源簇已解绑，证据链需重建")
        return "\n".join(lines), extra_risks

    # 簇评分
    lines.append("=== Source cluster scores ===")
    lines.append(f"name: {cluster.name or ''}")
    lines.append(f"description: {cluster.description or ''}")
    lines.append(f"demand_score: {cluster.demand_score}")
    lines.append(f"source_count: {cluster.source_count}")
    lines.append(f"pain_score: {cluster.pain_score}")
    lines.append(f"frequency_score: {cluster.frequency_score}")
    lines.append(f"money_score: {cluster.money_score}")
    lines.append(f"growth_score: {cluster.growth_score}")
    lines.append(f"competition_gap: {cluster.competition_gap}")

    # 成员信号
    result = await db.execute(
        select(DemandSignal).where(DemandSignal.cluster_id == opp.cluster_id)
    )
    signals = result.scalars().all()
    lines.append(f"=== Member signals ({len(signals)}) ===")
    for s in signals:
        parts = [f"type={s.demand_type}"]
        if s.problem:
            parts.append(f"problem: {s.problem}")
        if s.severity is not None:
            parts.append(f"severity: {s.severity}")
        if s.confidence is not None:
            parts.append(f"confidence: {s.confidence}")
        lines.append("; ".join(parts))

    return "\n".join(lines), extra_risks


async def analyze_opportunity(db: AsyncSession, opp: Opportunity) -> dict:
    """收集证据 → chat_json → 兜底校验 → 返回结构化 dict。

    返回 dict 字段与 OpportunityAnalysisRead 契约一致（数组为 Python list）。
    """
    user_prompt, extra_risks = await _collect_evidence(db, opp)

    raw = await chat_json(ANALYSIS_SYSTEM_PROMPT, user_prompt)

    result = _fallback_validate(raw)

    # 断链风险提示并入 risks（去重）
    for risk in extra_risks:
        if risk not in result["risks"]:
            result["risks"].append(risk)

    return result
