"""GitHub Issues adapter — structured demand signals from real bug reports.

Network resilience: shared AsyncClient (connection pool reuse) +
transport-level retries to absorb proxy flakiness.
"""
from datetime import datetime
from typing import Any

import certifi
import httpx

from app.adapters.base import SourceAdapter, register
from app.config.settings import settings
from app.extraction.pipeline import clean_text

PROXY = "http://127.0.0.1:7890"          # 默认本地代理（Clash 类软件的 HTTP 混合端口）
API_BASE = "https://api.github.com"
LIMIT = 25


class GithubAdapter(SourceAdapter):
    def __init__(self, source_config: dict | None = None) -> None:
        super().__init__(source_config)
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "github"

    def _get_client(self) -> httpx.AsyncClient:
        """Per-instance shared client — token/proxy from source config.

        连接池复用 + 连接级重试吸收代理瞬时抖动；token/proxy 可经源级
        config（"token"/"proxy"）覆盖，fallback 到 settings / 默认代理。
        proxy 解析规则：
        - config 缺省 "proxy" → 默认本地代理 PROXY（本地开发）
        - config 显式传空字符串 "" → 禁用代理（服务器直连，如无本地代理的环境）
        - config 传代理 URL → 使用之
        """
        if self._client is None:
            headers = {
                "User-Agent": "mie-bot/0.1 (market research)",
                "Accept": "application/vnd.github+json",
            }
            token = self._config.get("token") or settings.GITHUB_TOKEN
            if token:
                headers["Authorization"] = f"Bearer {token}"
            proxy = self._config.get("proxy")
            if proxy is None:
                proxy = PROXY
            # 空字符串 → None（禁用代理）；httpx 对空串代理 URL 会抛 ValueError
            proxy = proxy or None

            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=self.timeout(),
                verify=certifi.where(),
                proxy=proxy,
                # 连接级错误（拒连/超时）自动重试 3 次 —— 吸收代理瞬时抖动
                transport=httpx.AsyncHTTPTransport(
                    proxy=proxy,
                    verify=certifi.where(),
                    retries=3,
                ),
            )
        return self._client

    async def discover(self, source_config: dict) -> list[str]:
        """List a repo's most-discussed open issues → API URLs.

        增量：source_config["last_crawl_at"]（datetime）→ GitHub `since`
        参数，只返回该时间之后创建/更新的 issue，避免重复抓取。
        """
        # base_url 形如 https://github.com/microsoft/vscode → 解析 owner/repo
        path = source_config["base_url"].replace("https://github.com/", "").strip("/")
        owner, repo = path.split("/")

        # 深度：source.config["depth"] = per_page 倍数（默认 1，GitHub 上限 100）
        depth = int(self._config.get("depth") or 1)
        params: dict[str, Any] = {
            "state": "open", "sort": "comments", "direction": "desc",
            "per_page": min(LIMIT * depth, 100),
        }
        last_crawl_at = source_config.get("last_crawl_at")
        if last_crawl_at:
            since = (
                last_crawl_at.strftime("%Y-%m-%dT%H:%M:%SZ")
                if isinstance(last_crawl_at, datetime)
                else str(last_crawl_at)
            )
            params["since"] = since

        client = self._get_client()
        resp = await client.get(
            f"{API_BASE}/repos/{owner}/{repo}/issues",
            params=params,
        )
        if resp.status_code != 200:
            raise ValueError(f"GitHub API returned {resp.status_code}: {resp.text[:200]}")

        issues = [i for i in resp.json() if "pull_request" not in i]   # 排除 PR

        return [
            f"{API_BASE}/repos/{owner}/{repo}/issues/{i['number']}"
            for i in issues
        ]

    async def fetch(self, url: str) -> dict[str, Any]:
        client = self._get_client()
        resp = await client.get(url)
        if resp.status_code != 200:
            raise ValueError(f"GitHub API returned {resp.status_code}")
        return resp.json()

    async def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "source_item_id": f"gh_{raw['repository_url'].split('/repos/')[1]}_{raw['number']}",
            "url": raw["html_url"],
            "title": raw["title"],
            "content": clean_text(raw.get("body") or ""),
            "published_at": raw["created_at"],                 # ISO8601 字符串，normalise 统一转 naive UTC
            "engagement_score": raw.get("comments", 0),
            "author": raw["user"]["login"],
        }


register("github", GithubAdapter)
