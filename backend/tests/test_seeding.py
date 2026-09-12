"""启动播种测试 —— default_sources 纯函数（不依赖 DB）。

运行：uv run pytest tests/test_seeding.py -q
"""
from app.crawling.seeding import default_sources
from app.config.settings import settings


def test_default_sources_without_github(monkeypatch):
    """未设置 GITHUB_REPO → 只播种 HN + V2EX，间隔 60 分钟。"""
    monkeypatch.setattr(settings, "GITHUB_REPO", "")
    sources = default_sources()
    assert [s["type"] for s in sources] == ["hackernews", "v2ex"]
    assert all(s["crawl_interval"] == 60 for s in sources)
    assert all("base_url" not in s for s in sources)


def test_default_sources_with_github(monkeypatch):
    """设置 GITHUB_REPO → 追加 GitHub 源，proxy 取 GITHUB_PROXY（默认直连）。"""
    monkeypatch.setattr(settings, "GITHUB_REPO", "microsoft/vscode")
    monkeypatch.setattr(settings, "GITHUB_PROXY", "")
    sources = default_sources()
    assert [s["type"] for s in sources] == ["hackernews", "v2ex", "github"]

    gh = sources[2]
    assert gh["base_url"] == "https://github.com/microsoft/vscode"
    assert gh["config"] == {"proxy": ""}
    assert gh["crawl_interval"] == 1440  # 每天


def test_default_sources_with_github_proxy(monkeypatch):
    """GITHUB_PROXY 非空 → 播种的 GitHub 源使用该代理。"""
    monkeypatch.setattr(settings, "GITHUB_REPO", "microsoft/vscode")
    monkeypatch.setattr(settings, "GITHUB_PROXY", "http://127.0.0.1:7890")
    sources = default_sources()
    gh = sources[2]
    assert gh["config"] == {"proxy": "http://127.0.0.1:7890"}