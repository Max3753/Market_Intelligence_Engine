"""OpenAI-compatible LLM client — one wrapper for DeepSeek/Kimi/MiMo/..."""
import json

from openai import AsyncOpenAI

from app.config.settings import settings

_client: AsyncOpenAI | None = None

def get_client() -> AsyncOpenAI:
    """Lazy singleton — reuse one client across calls."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
        )
    return _client

async def chat_json(system_prompt: str, user_prompt: str) -> dict:
    """Chat completion that must return a JSON object."""
    resp = await get_client().chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or ""
    
    # 防御：有的模型会用 ```json ... ``` 包裹，剥掉再解析
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`").removeprefix("json").strip()
        
    return json.loads(content)
    