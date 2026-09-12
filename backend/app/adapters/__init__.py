"""Adapter package — importing this package registers all source adapters."""

from app.adapters.base import SourceAdapter, get_adapter, register
from app.adapters import v2ex
from app.adapters import github

# Import adapter modules so their register() calls execute.
from app.adapters import hn as _hn          # noqa: F401
from app.adapters import reddit as _reddit  # noqa: F401
from app.adapters import juejin as _juejin  # noqa: F401
from app.adapters import zhihu as _zhihu    # noqa: F401

__all__ = ["SourceAdapter", "get_adapter", "register"]