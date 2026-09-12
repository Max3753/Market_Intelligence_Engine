"""Scoring — compute composite demand score per §17 weights."""

# Scoring weights from project doc §17 (total = 1.0)

from app.intelligence.llm_client import chat_json

WEIGHTS = {
    "pain": 0.20,
    "frequency": 0.15,
    "market_reach": 0.15,
    "willingness_to_pay": 0.15,
    "evidence_strength": 0.10,
    "growth": 0.10,
    "competition_gap": 0.10,
    "technical_feasibility": 0.05,
}

SCORING_SYSTEM_PROMPT = """You are a demand scoring analyst for product discovery.

Given a demand cluster description, assess two dimensions on a 0-10 scale.
Respond with STRICT JSON only:

{"competition_gap": <0-10>, "technical_feasibility": <0-10>}

Definitions:
- competition_gap: how unserved this need currently is (10 = wide open market, no good solutions exist; 0 = saturated market)
- technical_feasibility: how buildable a solution is by a small team (10 = straightforward CRUD/tooling; 0 = requires breakthrough research)
"""

def score(metrics: dict[str, float]) -> float:
    """Compute weighted demand score (0–100).

    Args:
        metrics: dict with keys matching WEIGHTS, values 0–10.

    Returns:
        Composite score normalised to 0–100.

    """
    total = sum(metrics.get(dim, 0.0) * weight for dim, weight in WEIGHTS.items())
    
    return round(total * 10, 1)

async def evaluate_cluster(
    severity_avg: float | None,
    wtp_avg: float | None,
    evidence_avg: float | None,
    doc_count: int,
    user_count: int,
    max_doc_count: int,
    description: str,
) -> dict[str, float]:
    """Assemble all 8 dimension scores for one cluster."""
    # --- 数据维度 ---
    pain = severity_avg if severity_avg is not None else 0.0
    wtp = wtp_avg if wtp_avg is not None else 3.0      # 无付费信号 ≠ 0 分，给保守底分
    evidence = evidence_avg or 0.0
    frequency = min(doc_count / max(max_doc_count, 1) * 10, 10)   # 相对归一到 0-10
    market_reach = min(user_count / max(max_doc_count, 1) * 10, 10)

    growth = 5.0                                        # MVP：数据不足，中性分

    # --- LLM 维度 ---
    llm_scores = await chat_json(SCORING_SYSTEM_PROMPT, description)
    competition_gap = float(llm_scores.get("competition_gap", 5))
    feasibility = float(llm_scores.get("technical_feasibility", 5))

    return {
        "pain": pain, "frequency": frequency, "market_reach": market_reach,
        "willingness_to_pay": wtp, "evidence_strength": evidence,
        "growth": growth, "competition_gap": competition_gap,
        "technical_feasibility": feasibility,
    }
