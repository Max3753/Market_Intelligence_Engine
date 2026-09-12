"""SourceAdapter — abstract base class + registry for all data source adapters."""

from abc import ABC, abstractmethod
from typing import Any

import httpx


# 默认请求超时：连接 5s + 读取 15s（可被源级配置 timeout 覆盖）
DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=15.0, write=10.0, pool=5.0)


class SourceAdapter(ABC):
    """Base interface every source adapter must implement."""

    def __init__(self, source_config: dict | None = None) -> None:
        """Store per-source config (base_url / timeout / cookies / verify …)."""
        self._config = source_config or {}

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable adapter name (e.g. 'reddit', 'github')."""
        ...

    @abstractmethod
    async def discover(self, source_config: dict) -> list[str]:
        """Discover content URLs from a source. Returns list of URLs to fetch."""
        ...

    @abstractmethod
    async def fetch(self, url: str) -> dict[str, Any]:
        """Fetch raw content from a single URL."""
        ...

    @abstractmethod
    async def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Parse raw fetch result into a standardised document dict."""
        ...

    def timeout(self) -> httpx.Timeout:
        """Resolve request timeout from source config, falling back to default."""
        t = self._config.get("timeout")
        if isinstance(t, (int, float)) and t > 0:
            return httpx.Timeout(t)
        return DEFAULT_TIMEOUT


# --- Registry ---

ADAPTERS: dict[str, type[SourceAdapter]] = {}


def register(name: str, cls: type[SourceAdapter]) -> None:
    """Register an adapter class by its source type name."""
    ADAPTERS[name] = cls


def get_adapter(name: str) -> type[SourceAdapter]:
    """Look up an adapter by source type name."""
    try:
        return ADAPTERS[name]
    except KeyError:
        raise KeyError(f"No adapter registered for source type: {name}")