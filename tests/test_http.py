import httpx
import pytest
from conftest import fixture

from iran_news_mcp import http

pytestmark = pytest.mark.anyio

URL = "https://www.mehrnews.com/rss"


async def test_cache_hit(feeds):
    feeds["www.mehrnews.com/rss"] = fixture("mehr.xml")
    await http.fetch_feed(URL)
    await http.fetch_feed(URL)
    assert len(feeds.calls) == 1


async def test_retry_on_500_then_ok(feeds):
    n = {"c": 0}

    def flaky(req):
        n["c"] += 1
        return httpx.Response(500) if n["c"] == 1 else httpx.Response(200, content=fixture("mehr.xml"))

    feeds["www.mehrnews.com/rss"] = flaky
    assert (await http.fetch_feed(URL)).startswith(b"<?xml")
    assert n["c"] == 2


async def test_403_not_retried_and_message(feeds):
    feeds["www.mehrnews.com/rss"] = lambda req: httpx.Response(403)
    with pytest.raises(http.ApiError, match="403"):
        await http.fetch_feed(URL)
    assert len(feeds.calls) == 1


async def test_html_page_is_not_a_feed(feeds):
    feeds["www.mehrnews.com/rss"] = lambda req: httpx.Response(
        200, content=b"<!DOCTYPE html><html><body>Wait</body></html>"
    )
    with pytest.raises(http.ApiError, match="web page"):
        await http.fetch_feed(URL)


async def test_host_allowlist():
    with pytest.raises(http.ApiError, match="unexpected host"):
        await http.fetch_feed("https://example.com/rss")


def test_proxy_env_is_a_comma_list(monkeypatch):
    monkeypatch.delenv("IRAN_NEWS_MCP_PROXY", raising=False)
    assert http._proxies() == []
    monkeypatch.setenv("IRAN_NEWS_MCP_PROXY", " http://a:1 , ,http://b:2")
    assert http._proxies() == ["http://a:1", "http://b:2"]


async def test_proxy_rotates_on_block(monkeypatch, feeds):
    seen = []
    monkeypatch.setenv("IRAN_NEWS_MCP_PROXY", "http://a:1,http://b:2")
    real = httpx.AsyncClient
    monkeypatch.setattr(http.httpx, "AsyncClient", lambda **kw: real(**kw))
    feeds["www.mehrnews.com/rss"] = lambda req: (seen.append(http._proxy_index), httpx.Response(403))[1]
    with pytest.raises(http.ApiError):
        await http.fetch_feed(URL)
    assert http._proxy_index == 1 and http._client is None  # next call builds the client on proxy b
    assert seen == [0]


def test_proxy_reaches_the_transport(monkeypatch):
    got = {}

    class Fake(httpx.AsyncBaseTransport):
        def __init__(self, **kw):
            got.update(kw)

    monkeypatch.setattr(http, "_XhrTransport", Fake)
    monkeypatch.setenv("IRAN_NEWS_MCP_PROXY", "http://a:1,http://b:2")
    http.set_transport(None)
    http._get_client()
    assert got["proxy"] == "http://a:1"
    http._proxy_index, http._client = 1, None
    http._get_client()
    assert got["proxy"] == "http://b:2"
