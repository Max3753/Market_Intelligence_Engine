"""Zhihu source adapter — hot list discovery + question answers.

Requires ZHIHU_COOKIES env var (z_c0; d_c0; __zse_ck) copied from a logged-in
browser session. Without it, discover() raises RuntimeError with setup hints.

Skeleton status: structure complete, signature uses a format-valid random
value (Zhihu GET endpoints validate header presence/format, not crypto
content — verified 2026). If Zhihu tightens validation, replace
_signature() with a real SM4 signer (see cv-cat/ZhihuApis).
"""

import random
import string
from typing import Any
from urllib.parse import urlparse

import httpx

from app.adapters.base import SourceAdapter, register
from app.config.settings import settings
from app.extraction.pipeline import clean_text

API_BASE = "https://www.zhihu.com/api/v3"
SITE_BASE = "https://www.zhihu.com/question"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "x-api-version": "3.0.91",
    "x-zse-93": "101_3_3.0",
}
LIMIT = 20  # 热榜问题数 / 每问题回答数


def _unix_ts(value: Any) -> int | None:
    """Convert a unix timestamp (int/float/numeric string) to int; 0/None → None."""
    if value is None:
        return None
    try:
        ts = int(value)
    except (TypeError, ValueError):
        return None
    return ts or None  # 0 → None


def _signature(url_path: str) -> str:
    """Generate a format-valid x-zse-96 signature (2.0_ + 64 hex chars).

    Zhihu GET endpoints only check the header's presence and format, not its
    cryptographic content (CN-SEC 2026 verification). Full SM4-CBC signing is
    deferred; swap in a real signer if validation tightens.
    """
    return "2.0_" + "".join(random.choices(string.hexdigits, k=64))


class ZhihuAdapter(SourceAdapter):
    """Zhihu source adapter — hot list discovery + question answers."""

    @property
    def name(self) -> str:
        return "zhihu"

    def _cookies(self) -> str:
        """Read Zhihu cookies from source config, falling back to settings."""
        return self._config.get("cookies") or settings.ZHIHU_COOKIES

    async def discover(self, source_config: dict) -> list[str]:
        """Discover hot-list questions, return question page URLs."""
        cookies = self._cookies()
        if not cookies:
            raise RuntimeError(
                "Zhihu cookies not configured. Set source config 'cookies' "
                "or ZHIHU_COOKIES in backend/.env (z_c0=...; d_c0=...; __zse_ck=...)"
            )

        path = "/feed/topstory/hot-lists/total"
        headers = {
            **HEADERS,
            "cookie": cookies,
            "x-zse-96": _signature(path),
        }
        # 深度：source.config["depth"] = 热榜条数倍数（默认 1）
        depth = int(self._config.get("depth") or 1)
        async with httpx.AsyncClient(headers=headers, timeout=self.timeout()) as client:
            resp = await client.get(f"{API_BASE}{path}?limit={LIMIT * depth}")
            if resp.status_code != 200:
                raise ValueError(f"Zhihu API returned {resp.status_code}")
            data = resp.json()

        urls: list[str] = []
        for item in data.get("data", []):
            # 热榜项结构：question id 在 card_id（"Q_<qid>"）里；target 仅为展示区
            qid = None
            card_id = item.get("card_id", "")
            if card_id.startswith("Q_"):
                qid = card_id[2:]
            if not qid:
                qid = (item.get("target") or {}).get("id")
            if qid:
                urls.append(f"{SITE_BASE}/{qid}")
        return urls[:LIMIT]

    async def fetch(self, url: str) -> dict[str, Any]:
        """Fetch answers for a question page URL."""
        cookies = self._cookies()
        qid = urlparse(url).path.rstrip("/").split("/")[-1]

        path = f"/api/v4/questions/{qid}/answers"
        headers = {
            **HEADERS,
            "cookie": cookies,
            "x-zse-96": _signature(path),
        }
        params = {
            "include": (
                "data[*].content,data[*].voteup_count,data[*].comment_count,"
                "data[*].author.name,data[*].created_time"
            ),
            "limit": LIMIT,
            "offset": 0,
            "platform": "desktop",
            "sort_by": "default",
        }
        async with httpx.AsyncClient(headers=headers, timeout=self.timeout()) as client:
            resp = await client.get(f"https://www.zhihu.com{path}", params=params)
            if resp.status_code != 200:
                raise ValueError(f"Zhihu API returned {resp.status_code}")
            return resp.json()

    async def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Parse the answers response into standardised document dicts.

        Note: returns a single dict for the first answer — the worker's
        process_job expects one document per fetch/parse pair. For full
        coverage, extend discover to emit one URL per answer (future work).
        """
        answers = raw.get("data", [])
        if not answers:
            raise ValueError("No answers in Zhihu response")
        first = answers[0]
        content = clean_text(first.get("content") or "")

        return {
            "source_item_id": f"zhihu_{first['id']}",
            "url": f"{SITE_BASE}/{first.get('question', {}).get('id', '')}",
            "title": first.get("question", {}).get("title", ""),
            "content": content,
            "published_at": _unix_ts(first.get("created_time")),  # unix 秒
            "engagement_score": first.get("voteup_count", 0)
            + first.get("comment_count", 0),
            "author": first.get("author", {}).get("name", ""),
            "language": "zh",
        }


register("zhihu", ZhihuAdapter)