"""Startup seeding — create default sources on first boot.

幂等：仅当 sources 表为空时播种，绝不覆盖用户已创建的源。
"""
import logging

from sqlalchemy import func, select

from app.config.settings import settings
from app.db.session import async_session_factory
from app.models.source import Source

logger = logging.getLogger(__name__)


def default_sources() -> list[dict]:
    """默认数据源定义（纯函数，便于测试）。

    - Hacker News / V2EX：无需配置，国内可直连
    - GitHub：仅当 GITHUB_REPO 设置时创建；proxy 取 GITHUB_PROXY（默认直连）
    """
    defaults = [
        {"name": "Hacker News", "type": "hackernews", "crawl_interval": 60},
        {"name": "V2EX", "type": "v2ex", "crawl_interval": 60},
    ]
    if settings.GITHUB_REPO:
        defaults.append({
            "name": f"GitHub {settings.GITHUB_REPO}",
            "type": "github",
            "base_url": f"https://github.com/{settings.GITHUB_REPO}",
            "crawl_interval": 1440,
            "config": {"proxy": settings.GITHUB_PROXY},
        })
    return defaults


async def seed_default_sources() -> list[Source]:
    """启动时若 sources 表为空，创建默认数据源（幂等）。

    返回本次创建的源列表；已有源时返回空列表（不覆盖用户配置）。
    """
    async with async_session_factory() as db:
        count = await db.scalar(select(func.count()).select_from(Source))
        if count:
            return []
        sources = default_sources()
        created: list[Source] = []
        for d in sources:
            src = Source(
                name=d["name"],
                type=d["type"],
                base_url=d.get("base_url"),
                crawl_interval=d["crawl_interval"],
                config=d.get("config"),
            )
            db.add(src)
            created.append(src)
        await db.commit()
        for src in created:
            await db.refresh(src)          # 拿回自增 id
        logger.info("seeded %d default sources: %s", len(created), [s.type for s in created])
        return created