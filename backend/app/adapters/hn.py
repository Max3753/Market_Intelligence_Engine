"""Hacker News source adapter — discover & fetch HN stories (Phase 1)."""
import asyncio
from typing import Any
from urllib.parse import urlparse, parse_qs

import httpx

from app.adapters.base import SourceAdapter, register
from app.extraction.pipeline import clean_text

API_BASE = "https://hacker-news.firebaseio.com/v0"      # Firebase API
SITE_BASE = "https://news.ycombinator.com/item"          # 帖子页地址
HEADERS = {"User-Agent": "mie-bot/0.1 (market research)"}
LIMIT = 25                                               # 每次发现的帖子数

class HackerNewsAdapter(SourceAdapter):
    """Hacker News source adapter — discover & fetch HN stories (Phase 1)."""
    
    @property
    def name(self) -> str:
        return "hackernews"
    
    # 扩充数据
    DISCOVER_FEEDS = [
        ("askstories.json", 20),    # 需求金矿
        ("showstories.json", 20),   # 解决方案发布
        ("newstories.json", 20),    # 保持新鲜度
    ]
    
    async def discover(self, source_config: dict) -> list[str]:
        
        ids: list[int] = []
        # 速率限制：source.config["rate_limit"] = 秒/请求（0/缺省 = 不限速）
        rate_limit = float(source_config.get("rate_limit") or 0)
        # 深度：source.config["depth"] = 每 feed 拉取条数倍数（默认 1）
        depth = int(source_config.get("depth") or 1)
        
        # step1：请求 ID 列表（askstories + showstories + newstories）
        async with httpx.AsyncClient(headers=HEADERS, timeout=self.timeout()) as client:
            for i, (feed, n) in enumerate(self.DISCOVER_FEEDS):
                if rate_limit > 0 and i > 0:
                    await asyncio.sleep(rate_limit)
                resp = await client.get(f"{API_BASE}/{feed}")
                if resp.status_code != 200:
                    raise ValueError(f"HN API returned {resp.status_code}")
                ids.extend(resp.json()[: n * depth])
        
        # step2：每个 ID 拼接成帖子页 URL 地址
        return [f"{SITE_BASE}?id={i}" for i in ids]

    async def fetch(self, url: str) -> dict[str, Any]:
        # step1：解析 query string 中的 ID
        parsed = urlparse(url)
        item_id = parse_qs(parsed.query)["id"][0]
        
        # step2：请求 item 接口
        async with httpx.AsyncClient(headers=HEADERS, timeout=self.timeout()) as client:
            resp = await client.get(f"{API_BASE}/item/{item_id}.json")
            if resp.status_code != 200:
                raise ValueError(f"HN API returned {resp.status_code}")

        # step3：提取正文
        return resp.json()
    
    async def  parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        # text 是可选字段且是 HTML —— 用 .get() 兜底 + clean_text 清洗
        content = clean_text(raw.get("text") or "")
        
        return {
        "source_item_id": f"hn_{raw['id']}",
        "url": f"{SITE_BASE}?id={raw['id']}",
        "title": raw["title"],
        "content": content,
        "published_at": raw["time"],                                  # unix 秒
        "engagement_score": raw["score"] + raw.get("descendants", 0),  # descendants 可选
        "author": raw["by"],
        }
        
register("hackernews", HackerNewsAdapter)
