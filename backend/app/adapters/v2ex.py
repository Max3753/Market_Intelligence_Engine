"""V2EX source adapter — hot topics discovery + topic detail fetch.

V2EX serves its legacy JSON API over HTTPS on www.v2ex.com (the newer
api.v2ex.com is unreachable from CN networks; /api/v2/ requires a token).
The server sends an incomplete TLS cert chain (missing intermediate), so
requests use verify=False — acceptable for a read-only public API; revisit
if V2EX fixes their TLS config. Direct HTTPS works without a proxy.
"""

from typing import Any
from urllib.parse import urlparse

import httpx

from app.adapters.base import SourceAdapter, register
from app.extraction.pipeline import clean_text

API_BASE = "https://www.v2ex.com/api"
SITE_BASE = "https://www.v2ex.com/t"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}
LIMIT = 20


def _unix_ts(value: Any) -> int | None:
    """Convert a unix timestamp (int/float/numeric string) to int; 0/None → None."""
    if value is None:
        return None
    try:
        ts = int(value)
    except (TypeError, ValueError):
        return None
    return ts or None  # 0 → None


class V2exAdapter(SourceAdapter):
    @property
    def name(self) -> str:
        return "v2ex"

    async def discover(self, source_config: dict) -> list[str]:
        """Hot topics list → per-topic page URLs."""
        async with httpx.AsyncClient(headers=HEADERS, timeout=self.timeout(), verify=self._config.get("verify", False)) as client:
            resp = await client.get(f"{API_BASE}/topics/hot.json")
            if resp.status_code != 200:
                raise ValueError(f"V2EX API returned {resp.status_code}")
            topics = resp.json()

        # 深度：source.config["depth"] = 拉取条数倍数（默认 1）
        depth = int(self._config.get("depth") or 1)
        return [f"{SITE_BASE}/{t['id']}" for t in topics if t.get("id")][: LIMIT * depth]

    async def fetch(self, url: str) -> dict[str, Any]:
        topic_id = urlparse(url).path.rstrip("/").split("/")[-1]

        async with httpx.AsyncClient(headers=HEADERS, timeout=self.timeout(), verify=self._config.get("verify", False)) as client:
            resp = await client.get(f"{API_BASE}/topics/show.json", params={"id": topic_id})
            if resp.status_code != 200:
                raise ValueError(f"V2EX API returned {resp.status_code}")
            data = resp.json()

        if isinstance(data, list) and data:
            return data[0]
        raise ValueError("No topic in V2EX response")

    async def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "source_item_id": f"v2ex_{raw['id']}",
            "url": f"{SITE_BASE}/{raw['id']}",
            "title": raw.get("title", ""),
            "content": clean_text(raw.get("content") or ""),
            "published_at": _unix_ts(raw.get("created")),  # unix 秒
            "engagement_score": raw.get("replies", 0),  # 回复数 = 互动量
            "author": raw.get("member", {}).get("username", ""),
            "language": "zh",
        }


register("v2ex", V2exAdapter)