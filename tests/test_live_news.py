import pytest

pytestmark = [pytest.mark.anyio, pytest.mark.live]


async def call(client, name, args):
    result = await client.call_tool(name, args)
    assert not result.is_error, result.content[0].text
    return result.structured_content


SOURCES = [
    "mehr",
    "khabaronline",
    "hamshahri",
    "tabnak",
    "zoomit",
    "digiato",
    "entekhab",
    "asriran",
    "varzesh3",
    "khabarvarzeshi",
]


@pytest.mark.parametrize("source", SOURCES)
async def test_nw_latest_each_source(client, source):
    data = await call(client, "nw_latest", {"source": source, "limit": 5})
    assert data["items"] and data["items"][0]["title"] and data["items"][0]["url"].startswith("http")


async def test_nw_latest_category(client):
    data = await call(client, "nw_latest", {"source": "mehr", "category": "economy", "limit": 3})
    assert data["items"]
    data = await call(client, "nw_latest", {"source": "zoomit", "category": "mobile", "limit": 3})
    assert data["items"]


@pytest.mark.parametrize(
    ("source", "category"),
    [
        ("entekhab", "sports"),
        ("entekhab", "economy"),
        ("asriran", "sports"),
        ("asriran", "economy"),
        ("varzesh3", "sports"),
        ("khabarvarzeshi", "sports"),
    ],
)
async def test_nw_latest_new_source_categories(client, source, category):
    data = await call(client, "nw_latest", {"source": source, "category": category, "limit": 3})
    assert data["items"]


async def test_nw_list_sources(client):
    data = await call(client, "nw_list_sources", {})
    assert len(data["sources"]) == len(SOURCES)


async def test_nw_latest_all(client):
    data = await call(client, "nw_latest_all", {"per_source": 2})
    assert len({i["source"] for i in data["items"]}) >= 10


@pytest.mark.parametrize("source", SOURCES)
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


async def test_nw_tech_news_digiato_deep(client):
    data = await call(client, "nw_tech_news", {"limit": 25})
    assert data["count"] == 25 and {i["source"] for i in data["items"]} == {"digiato"}
    assert all(i["title"] and i["url"].startswith("http") for i in data["items"])
    both = await call(client, "nw_tech_news", {"category": "mobile", "source": "both", "limit": 10})
    assert both["count"] > 0
