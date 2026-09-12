"""掘金 (Juejin) source adapter — 沸点 + 文章热榜需求信号采集。

沸点（short_msg）是需求信号金矿：开发者直接吐槽/提问/求推荐；
文章热榜补充高质量长文信号。

网络策略：国内服务，直连，不走代理（与 GitHub 适配器相反）。
"""
from typing import Any
from urllib.parse import urlparse, parse_qs

import httpx

from app.adapters.base import SourceAdapter, register
from app.extraction.pipeline import clean_text

SHORT_MSG_API = "https://api.juejin.cn/recommend_api/v1/short_msg/recommend"
ARTICLE_RANK_API = "https://api.juejin.cn/content_api/v1/content/article_rank"
SITE_BASE = "https://juejin.cn"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://juejin.cn",
    "Referer": "https://juejin.cn/",
}
LIMIT = 20          # 每页条数
MAX_PAGES = 2       # discover 只取 1-2 页，控制频率
TITLE_MAX = 50      # 沸点内容截断为标题的长度


def _unix_ts(value: Any) -> int | None:
    """Convert a unix timestamp (int/float/numeric string) to int; 0/None → None.

    Juejin API returns ctime as a JSON string (e.g. "1787794399"); normalise()
    expects a numeric type, so coerce here.
    """
    if value is None:
        return None
    try:
        ts = int(value)
    except (TypeError, ValueError):
        return None
    return ts or None  # 0 → None


class JuejinAdapter(SourceAdapter):
    """掘金适配器 — 沸点推荐流 + 文章热榜。"""

    @property
    def name(self) -> str:
        return "juejin"

    async def discover(self, source_config: dict) -> list[str]:
        """沸点推荐流（最多 2 页）+ 文章热榜 → 内部标识 URL 列表。

        每个条目一个 URL（含 index），与 github.py 每 issue 一个 URL 同款，
        保证 worker 循环里 fetch→parse 一一对应、全部入库。
        """
        urls: list[str] = []
        # 深度：source.config["depth"] = 拉取页数（默认 MAX_PAGES）
        depth = int(self._config.get("depth") or MAX_PAGES)

        async with httpx.AsyncClient(headers=HEADERS, timeout=self.timeout()) as client:
            # ── 沸点推荐流：cursor 分页 ──
            cursor = "0"
            for _ in range(depth):
                resp = await client.post(
                    SHORT_MSG_API,
                    json={"id_type": 4, "sort_type": 200, "cursor": cursor, "limit": LIMIT},
                )
                if resp.status_code != 200:
                    raise ValueError(f"Juejin short_msg API returned {resp.status_code}")
                body = resp.json()
                items = body.get("data") or []
                for i in range(len(items)):
                    urls.append(f"juejin://short_msg/recommend?cursor={cursor}&index={i}")
                if not body.get("has_more") or not items:
                    break
                cursor = str(body.get("cursor") or cursor)

            # ── 文章热榜：单次请求 ──
            # 热榜接口 brief 字段实测全空（2026-08），无正文无法抽取需求，
            # 过滤掉空 brief 条目；若未来接口补全 brief 则自动生效。
            resp = await client.get(
                ARTICLE_RANK_API,
                params={"category_id": 1, "type": "hot"},
            )
            if resp.status_code != 200:
                raise ValueError(f"Juejin article_rank API returned {resp.status_code}")
            items = resp.json().get("data") or []
            for i in range(len(items)):
                brief = (items[i].get("content") or {}).get("brief") or ""
                if brief.strip():
                    urls.append(f"juejin://article_rank?category_id=1&type=hot&index={i}")

        return urls

    async def fetch(self, url: str) -> dict[str, Any]:
        """解析内部标识 URL → 请求对应接口 → 返回该 index 的单条原始数据。"""
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        index = int(query.get("index", ["0"])[0])

        async with httpx.AsyncClient(headers=HEADERS, timeout=self.timeout()) as client:
            if parsed.netloc == "short_msg":
                cursor = query.get("cursor", ["0"])[0]
                resp = await client.post(
                    SHORT_MSG_API,
                    json={"id_type": 4, "sort_type": 200, "cursor": cursor, "limit": LIMIT},
                )
                if resp.status_code != 200:
                    raise ValueError(f"Juejin short_msg API returned {resp.status_code}")
                items = resp.json().get("data") or []
            elif parsed.netloc == "article_rank":
                resp = await client.get(
                    ARTICLE_RANK_API,
                    params={"category_id": 1, "type": "hot"},
                )
                if resp.status_code != 200:
                    raise ValueError(f"Juejin article_rank API returned {resp.status_code}")
                items = resp.json().get("data") or []
            else:
                raise ValueError(f"Unknown juejin internal URL: {url}")

        if index >= len(items):
            raise ValueError(f"Juejin item index {index} out of range (len={len(items)})")
        return items[index]

    async def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        """映射为标准文档 dict。"""
        # ── 沸点 ──
        if "msg_id" in raw:
            info = raw.get("msg_Info") or {}
            content = clean_text(info.get("content") or "")
            topic = (raw.get("topic") or {}).get("title") or ""
            return {
                "source_item_id": f"juejin_{raw['msg_id']}",
                "url": f"{SITE_BASE}/pin/{raw['msg_id']}",
                "title": content[:TITLE_MAX] or topic or "沸点",
                "content": content,
                "published_at": _unix_ts(info.get("ctime")),              # unix 秒
                "engagement_score": info.get("digg_count", 0) + info.get("comment_count", 0),
                "author": (raw.get("author_user_info") or {}).get("user_name", ""),
                "language": "zh",
            }

        # ── 文章热榜 ──
        if "content" in raw and "content_counter" in raw:
            content = raw.get("content") or {}
            counter = raw.get("content_counter") or {}
            ctime = content.get("ctime") or None                          # 热榜接口 ctime 常为 0
            return {
                "source_item_id": f"juejin_{content.get('content_id')}",
                "url": f"{SITE_BASE}/post/{content.get('content_id')}",
                "title": content.get("title") or clean_text(content.get("brief") or "")[:TITLE_MAX],
                "content": clean_text(content.get("brief") or ""),
                "published_at": _unix_ts(ctime),                          # unix 秒，可能为 None
                "engagement_score": counter.get("view", 0) + counter.get("like", 0) + counter.get("collect", 0),
                "author": (raw.get("author") or {}).get("name", ""),
                "language": "zh",
            }

        raise ValueError("Unknown juejin raw item shape")


register("juejin", JuejinAdapter)