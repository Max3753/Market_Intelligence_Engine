"""Demand classifier — label documents by demand type using LLM."""

from enum import Enum

from app.intelligence.llm_client import chat_json

CLASSIFIER_SYSTEM_PROMPT = """You are a demand signal classifier for a product discovery system.

Classify the given text into exactly ONE of these 11 categories:

1. pain - user describes a real problem or frustration they experience
2. feature_request - user asks for a specific new feature in an existing product
3. complaint - negative feedback about an existing product (no specific feature ask)
4. workaround - user describes a hack or manual process to get something done
5. buying_intent - user wants to buy or pay for a solution
6. alternative_search - user asks for alternatives to an existing tool
7. price_complaint - complaint specifically about pricing
8. churn_signal - user stopped using or is leaving a product
9. unmet_need - need exists but no known solution exists at all
10. general_discussion - normal discussion without a clear demand signal
11. noise - ads, promotions, spam, memes, or text too short to judge

Respond with STRICT JSON only:
{"demand_type": "<one of the 11 values above>", "confidence": <0.0-1.0>, "reason": "<one sentence justification>"}

Rules:
- confidence below 0.6 -> prefer "general_discussion"
- Judge only by what the text says, never guess about the author
- Empty or meaningless text -> "noise"
"""

class DemandType(str, Enum):
    """Eleven demand categories per the project spec."""

    PAIN = "pain"
    FEATURE_REQUEST = "feature_request"
    COMPLAINT = "complaint"
    WORKAROUND = "workaround"
    BUYING_INTENT = "buying_intent"
    ALTERNATIVE_SEARCH = "alternative_search"
    PRICE_COMPLAINT = "price_complaint"
    CHURN_SIGNAL = "churn_signal"
    UNMET_NEED = "unmet_need"
    GENERAL_DISCUSSION = "general_discussion"
    NOISE = "noise"


async def classify(document_text: str) -> dict:
    """Classify a document's demand type via LLM."""
    result = await chat_json(CLASSIFIER_SYSTEM_PROMPT, document_text)
    # 校验 demand_type 必须是合法枚举值 -- LLM 会犯错，必须兜底
    valid = {t.value for t in DemandType}
    if result.get("demand_type") not in valid:
        result["demand_type"] = DemandType.NOISE.value
        result["confidence"] = 0.0
    return result

