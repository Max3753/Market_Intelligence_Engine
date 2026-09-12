"""适配器契约测试 —— mock 响应 → 验证 parse/discover 输出符合 Document schema。

不依赖网络：HTTP 调用用 httpx.MockTransport 拦截。
运行：uv run pytest tests/test_adapters.py -q
"""
import asyncio
from typing import Any

import httpx

from app.adapters.github import GithubAdapter
from app.adapters.hn import HackerNewsAdapter
from app.adapters.juejin import JuejinAdapter
from app.adapters.reddit import RedditAdapter
from app.adapters.v2ex import V2exAdapter
from app.adapters.zhihu import ZhihuAdapter

# ── 契约：parse 输出必须包含的字段 ──
REQUIRED_FIELDS = [
    "source_item_id", "url", "title", "content",
    "published_at", "engagement_score",
]


def _assert_parse_contract(doc: dict[str, Any]) -> None:
    """断言 parse 输出符合 Document schema 契约。"""
    for field in REQUIRED_FIELDS:
        assert field in doc, f"parse 输出缺少字段 {field}"
    assert isinstance(doc["source_item_id"], str)
    assert isinstance(doc["url"], str)
    assert isinstance(doc["title"], str)
    assert isinstance(doc["content"], str)
    # published_at：unix 秒 int（zhihu/v2ex/juejin/reddit/hn）或 ISO8601 str（github）
    assert doc["published_at"] is None or isinstance(doc["published_at"], (int, str))
    assert isinstance(doc["engagement_score"], (int, float))


# ── mock 原始数据（各适配器 API 响应形状）──

ZHIHU_RAW = {
    "data": [{
        "id": "12345",
        "content": "<p>测试内容</p>",
        "voteup_count": 10,
        "comment_count": 3,
        "created_time": 1787794399,
        "author": {"name": "测试用户"},
        "question": {"id": "67890", "title": "测试问题"},
    }],
}

V2EX_RAW = {
    "id": 12345,
    "title": "测试主题",
    "content": "测试内容",
    "created": 1787794399,
    "replies": 5,
    "member": {"username": "测试用户"},
}

JUEJIN_SHORT_MSG = {
    "msg_id": "12345",
    "msg_Info": {"content": "测试沸点", "ctime": "1787794399", "digg_count": 3, "comment_count": 1},
    "topic": {"title": "测试话题"},
    "author_user_info": {"user_name": "测试用户"},
}

JUEJIN_ARTICLE = {
    "content": {"content_id": "67890", "title": "测试文章", "brief": "测试摘要", "ctime": 0},
    "content_counter": {"view": 100, "like": 10, "collect": 5},
    "author": {"name": "测试作者"},
}

REDDIT_RAW = {
    "listing": {
        "id": "abc123",
        "permalink": "/r/test/comments/abc123/test/",
        "title": "测试帖子",
        "selftext": "测试内容",
        "created_utc": 1787794399,
        "score": 10,
        "num_comments": 3,
        "author": "测试用户",
    },
    "comments_listing": [],
}

HN_RAW = {
    "id": 12345,
    "title": "测试故事",
    "text": "<p>测试内容</p>",
    "time": 1787794399,
    "score": 10,
    "descendants": 3,
    "by": "测试用户",
}

GITHUB_RAW = {
    "repository_url": "https://api.github.com/repos/test/repo",
    "number": 42,
    "html_url": "https://github.com/test/repo/issues/42",
    "title": "测试 issue",
    "body": "测试内容",
    "created_at": "2026-09-01T10:00:00Z",
    "comments": 3,
    "user": {"login": "测试用户"},
}


# ── parse 契约测试 ──

def test_zhihu_parse_contract():
    doc = asyncio.run(ZhihuAdapter().parse(ZHIHU_RAW))
    _assert_parse_contract(doc)
    assert doc["language"] == "zh"
    assert doc["source_item_id"] == "zhihu_12345"


def test_v2ex_parse_contract():
    doc = asyncio.run(V2exAdapter().parse(V2EX_RAW))
    _assert_parse_contract(doc)
    assert doc["language"] == "zh"
    assert doc["source_item_id"] == "v2ex_12345"


def test_juejin_short_msg_parse_contract():
    doc = asyncio.run(JuejinAdapter().parse(JUEJIN_SHORT_MSG))
    _assert_parse_contract(doc)
    assert doc["language"] == "zh"
    assert doc["source_item_id"] == "juejin_12345"


def test_juejin_article_parse_contract():
    doc = asyncio.run(JuejinAdapter().parse(JUEJIN_ARTICLE))
    _assert_parse_contract(doc)
    assert doc["language"] == "zh"
    assert doc["source_item_id"] == "juejin_67890"


def test_reddit_parse_contract():
    doc = asyncio.run(RedditAdapter().parse(REDDIT_RAW))
    _assert_parse_contract(doc)
    assert doc["source_item_id"] == "t3_abc123"


def test_hn_parse_contract():
    doc = asyncio.run(HackerNewsAdapter().parse(HN_RAW))
    _assert_parse_contract(doc)
    assert doc["source_item_id"] == "hn_12345"


def test_github_parse_contract():
    doc = asyncio.run(GithubAdapter().parse(GITHUB_RAW))
    _assert_parse_contract(doc)
    assert doc["source_item_id"] == "gh_test/repo_42"


# ── discover 契约测试（MockTransport 拦截 HTTP）──

def _patch_async_client(monkeypatch: Any, handler: Any) -> None:
    """让 httpx.AsyncClient 使用 MockTransport（按 URL 路由）。"""
    transport = httpx.MockTransport(handler)

    class _MockClient(httpx.AsyncClient):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", _MockClient)


def test_zhihu_discover_returns_question_urls(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [
            {"card_id": "Q_1001", "target": {"id": "1001"}},
            {"card_id": "Q_1002", "target": {"id": "1002"}},
        ]})

    _patch_async_client(monkeypatch, handler)
    urls = asyncio.run(ZhihuAdapter({"cookies": "z_c0=test"}).discover({"base_url": "https://www.zhihu.com"}))
    assert len(urls) == 2
    assert all(u.startswith("https://www.zhihu.com/question/") for u in urls)


def test_v2ex_discover_returns_topic_urls(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[
            {"id": 1001}, {"id": 1002},
        ])

    _patch_async_client(monkeypatch, handler)
    urls = asyncio.run(V2exAdapter().discover({"base_url": "https://www.v2ex.com"}))
    assert len(urls) == 2
    assert all(u.startswith("https://www.v2ex.com/t/") for u in urls)


def test_hn_discover_returns_story_urls(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        # 3 个 feed（askstories/showstories/newstories）各返回 2 个 ID
        return httpx.Response(200, json=[1, 2])

    _patch_async_client(monkeypatch, handler)
    urls = asyncio.run(HackerNewsAdapter().discover({"base_url": "https://news.ycombinator.com"}))
    assert len(urls) == 6  # 3 feeds × 2 ids
    assert all(u.startswith("https://news.ycombinator.com/item?id=") for u in urls)


def test_juejin_discover_returns_internal_urls(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(200, json={
                "data": [{"msg_id": "1"}, {"msg_id": "2"}],
                "has_more": False,
            })
        return httpx.Response(200, json={"data": [
            {"content": {"brief": "有摘要的文章"}},
            {"content": {"brief": ""}},  # 空 brief 应被过滤
        ]})

    _patch_async_client(monkeypatch, handler)
    urls = asyncio.run(JuejinAdapter().discover({"base_url": "https://juejin.cn"}))
    # 2 沸点 + 1 有摘要文章
    assert len(urls) == 3
    assert all(u.startswith("juejin://") for u in urls)


def test_reddit_discover_returns_post_urls(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"children": [
            {"data": {"permalink": "/r/test/comments/abc/test/"}},
            {"data": {"permalink": "/r/test/comments/def/test2/"}},
        ]}})

    _patch_async_client(monkeypatch, handler)
    urls = asyncio.run(RedditAdapter().discover({"base_url": "https://www.reddit.com/r/test"}))
    assert len(urls) == 2
    assert all(u.startswith("https://www.reddit.com") for u in urls)


def test_github_discover_returns_issue_urls(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[
            {"number": 1},  # 非 PR：无 pull_request 键
            {"number": 2},  # 非 PR
            {"number": 3, "pull_request": {"url": "x"}},  # PR 应被排除
        ])

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    monkeypatch.setattr(GithubAdapter, "_get_client", lambda self: client)

    urls = asyncio.run(GithubAdapter().discover({"base_url": "https://github.com/test/repo"}))
    assert len(urls) == 2
    assert all(u.startswith("https://api.github.com/repos/test/repo/issues/") for u in urls)


def test_github_proxy_resolution(monkeypatch):
    """proxy 解析：缺省 → 默认本地代理；空字符串 → 禁用代理（直连）；显式 URL → 使用之。"""
    captured: dict[str, Any] = {}

    class _RecordingClient(httpx.AsyncClient):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            captured["client_proxy"] = kwargs.get("proxy")
            super().__init__(*args, **kwargs)

    class _RecordingTransport(httpx.AsyncHTTPTransport):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            captured["transport_proxy"] = kwargs.get("proxy")
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", _RecordingClient)
    monkeypatch.setattr(httpx, "AsyncHTTPTransport", _RecordingTransport)

    # 缺省 → 默认本地代理（本地开发行为不变）
    GithubAdapter()._get_client()
    assert captured["client_proxy"] == "http://127.0.0.1:7890"
    assert captured["transport_proxy"] == "http://127.0.0.1:7890"

    # 空字符串 → 禁用代理（服务器直连）
    GithubAdapter({"proxy": ""})._get_client()
    assert captured["client_proxy"] is None
    assert captured["transport_proxy"] is None

    # 显式代理 URL → 使用之
    GithubAdapter({"proxy": "http://proxy.example:8080"})._get_client()
    assert captured["client_proxy"] == "http://proxy.example:8080"
    assert captured["transport_proxy"] == "http://proxy.example:8080"