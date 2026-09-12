import asyncio

import pytest

from app.adapters.reddit import RedditAdapter

# Reddit 因国内网络被墙（403，IP 层封锁）+ 官方 API 注册受限，
# 已改用 Hacker News 作为第一个数据源（见 docs/PROJECT_LOG.md 数据源决策变更）。
# 适配器保留，Phase 7 再接 —— 在此之前跳过该测试。
pytestmark = pytest.mark.skip(reason="Reddit 被墙，Phase 7 再接（见 PROJECT_LOG 数据源决策变更）")


async def test():
    a = RedditAdapter()
    urls = await a.discover({"base_url": "https://www.reddit.com/r/startups"})
    print(f"发现 {len(urls)} 个帖子")
    raw = await a.fetch(urls[0])
    doc = await a.parse(raw)
    print(doc)


if __name__ == "__main__":
    asyncio.run(test())
