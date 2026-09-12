"""Extractor — pull structured demand fields from classified documents."""
from app.intelligence.llm_client import chat_json

EXTRACTOR_SYSTEM_PROMPT = """You are a demand signal extractor for a product discovery system.

Extract structured demand fields from the given classified text.

Respond with STRICT JSON only:
{
	"problem": "<core problem, or null>",
	"pain_points": ["<specific pain point>"] or null,
	"job_to_be_done": "<underlying job, or null>",
	"desired_outcome": "<what the user wants, or null>",
	"current_solution": "<what they use now, or null>",
	"severity": <0-10 float, or null>,
	"willingness_to_pay": <0-10 float, or null>,
	"evidence_strength": <0-10 float>,
	"evidence_quote": "<key sentence copied verbatim from the text>"
}

HARD RULES (Evidence First):
- Every field MUST be backed by explicit evidence in the text
- No clear evidence -> null. NEVER invent or over-infer.
- evidence_quote must be copied word-for-word from the input
- severity: how painful the problem is (10 = agonizing)
- evidence_strength: how explicit the textual evidence is (10 = stated outright)
"""

async def extract(document_text: str, demand_type: str) -> dict:
    """Extract demand signal fields via LLM."""
    return await chat_json(EXTRACTOR_SYSTEM_PROMPT, document_text)