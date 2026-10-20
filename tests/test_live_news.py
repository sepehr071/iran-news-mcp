import pytest

pytestmark = [pytest.mark.anyio, pytest.mark.live]


async def call(client, name, args):
    result = await client.call_tool(name, args)
    assert not result.is_error, result.content[0].text
    return result.structured_content


@pytest.mark.parametrize("source", ["mehr", "khabaronline", "hamshahri", "tabnak", "zoomit", "digiato"])
async def test_nw_latest_each_source(client, source):
    data = await call(client, "nw_latest", {"source": source, "limit": 5})
    assert data["items"] and data["items"][0]["title"] and data["items"][0]["url"].startswith("http")


async def test_nw_latest_category(client):
    data = await call(client, "nw_latest", {"source": "mehr", "category": "economy", "limit": 3})
    assert data["items"]
    data = await call(client, "nw_latest", {"source": "zoomit", "category": "mobile", "limit": 3})
    assert data["items"]


async def test_nw_list_sources(client):
    data = await call(client, "nw_list_sources", {})
    assert len(data["sources"]) == 6


async def test_nw_latest_all(client):
    data = await call(client, "nw_latest_all", {"per_source": 2})
    assert len({i["source"] for i in data["items"]}) >= 5


@pytest.mark.parametrize("source", ["mehr", "khabaronline", "hamshahri", "tabnak", "zoomit", "digiato"])
async def test_nw_article_each_source(client, source):
    items = (await call(client, "nw_latest", {"source": source, "limit": 15}))["items"]
    # photo/video items have no body and feeds can list a pulled story (404); the first story with text counts
    for it in items:
        r = await client.call_tool("nw_article", {"url": it["url"]})
        if not r.is_error:
            assert len(r.structured_content["text"]) >= 40  # short "watch the video" stories are real
            return
        assert "No article text" in r.content[0].text or "HTTP 404" in r.content[0].text, r.content[0].text
    pytest.fail(f"no {source} item had article text")


async def test_nw_search(client):
    data = await call(client, "nw_search", {"query": "ایران", "limit": 10})
    assert data["items"]
