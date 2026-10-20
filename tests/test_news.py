import httpx
import pytest
from conftest import fixture

from iran_news_mcp import http, news

pytestmark = pytest.mark.anyio

HOSTS = {
    "mehr": "www.mehrnews.com",
    "khabaronline": "www.khabaronline.ir",
    "hamshahri": "www.hamshahrionline.ir",
    "tabnak": "www.tabnak.ir",
    "zoomit": "www.zoomit.ir",
    "digiato": "digiato.com",
}


def route_all(feeds):
    for src, host in HOSTS.items():
        feeds[host + news.SOURCES[src]["latest"].split(host, 1)[1]] = fixture(f"{src}.xml")


@pytest.mark.parametrize("src", HOSTS)
def test_parse_each_fixture(src):
    items = news.parse_feed(fixture(f"{src}.xml"), src)
    assert len(items) == 3
    for i in items:
        assert i["title"] and i["url"].startswith("http") and i["date"] and i["date"].tzinfo
        assert "<" not in (i.get("summary") or "")


def test_tabnak_date_and_zoomit_categories():
    t = news.parse_feed(fixture("tabnak.xml"), "tabnak")[0]
    assert t["date"].isoformat().startswith("2026-10-19T19:12:01")  # 22:42:01 +03:30
    z = news.parse_feed(fixture("zoomit.xml"), "zoomit")[0]
    assert "cryptocurrency" in z["slugs"] and "ارز دیجیتال" in z["categories"]
    assert z["image"].startswith("https://api2.zoomit.ir/media/")


def test_text_and_norm():
    assert news._text("<p>سلام&nbsp;<b>دنیا</b></p>\n x") == "سلام دنیا x"
    assert news._norm("كتاب‌ها ۱۲") == "کتاب ها 12"
    assert news._date("2026-10-19T10:00:00Z").hour == 10
    assert news._date("garbage") is None


async def test_list_sources(client):
    r = await client.call_tool("nw_list_sources", {})
    ids = [s["id"] for s in r.structured_content["sources"]]
    assert ids == list(HOSTS)
    assert r.structured_content["sources"][0]["categories"]["politics"] == "سیاست"


async def test_latest_category_url_and_limit(client, feeds):
    feeds["www.mehrnews.com/rss/tp/7"] = fixture("mehr.xml")
    r = await client.call_tool("nw_latest", {"source": "mehr", "category": "politics", "limit": 2})
    d = r.structured_content
    assert d["count"] == 2 and d["items"][0]["source"] == "mehr"
    assert d["items"][0]["published"] > d["items"][1]["published"]
    assert feeds.calls[0].url.path == "/rss/tp/7"


async def test_default_sizes_keep_replies_small(client):
    props = {t.name: t.input_schema["properties"] for t in (await client.list_tools()).tools}
    assert props["nw_latest"]["limit"]["default"] == 10
    assert props["nw_search"]["limit"]["default"] == 10
    assert props["nw_latest_all"]["per_source"]["default"] == 2


async def test_zoomit_category_filters_client_side(client, feeds):
    feeds["www.zoomit.ir/feed/"] = fixture("zoomit.xml")
    r = await client.call_tool("nw_latest", {"source": "zoomit", "category": "cryptocurrency"})
    assert r.structured_content["count"] == 1
    r = await client.call_tool("nw_latest", {"source": "zoomit", "category": "gaming"})
    assert r.structured_content["count"] == 0


async def test_unknown_source_and_category(client):
    r = await client.call_tool("nw_latest", {"source": "nope"})
    assert r.is_error and "Unknown source" in r.content[0].text
    r = await client.call_tool("nw_latest", {"source": "mehr", "category": "nope"})
    assert r.is_error and "no category" in r.content[0].text
    r = await client.call_tool("nw_latest", {"source": "zoomit", "category": "nope"})  # client-side filtered source
    assert r.is_error and "no category" in r.content[0].text


async def test_search_rejects_blank_query(client):
    for q in ("   ", "\u200c"):
        r = await client.call_tool("nw_search", {"query": q})
        assert r.is_error and "searchable" in r.content[0].text


async def test_empty_channel_is_an_error(client, feeds):
    feeds["digiato.com/feed"] = b"<rss version='2.0'><channel><title>x</title></channel></rss>"
    r = await client.call_tool("nw_latest", {"source": "digiato"})
    assert r.is_error and "empty feed" in r.content[0].text


def test_wordpress_footer_removed():
    s = "<p>متن خبر.</p><p>The post <a href='x'>عنوان</a> appeared first on <a>دیجیاتو</a>.</p>"
    assert news._text(s) == "متن خبر."


async def test_search_across_sources_with_failure(client, feeds):
    route_all(feeds)
    word = news.parse_feed(fixture("mehr.xml"), "mehr")[0]["title"].split()[0]
    r = await client.call_tool("nw_search", {"query": word, "sources": ["mehr", "tabnak", "digiato"]})
    d = r.structured_content
    assert any(i["source"] == "mehr" for i in d["items"])
    feeds["digiato.com/feed"] = lambda req: httpx.Response(500)
    http.set_transport(http._transport)  # new client, empty cache
    r = await client.call_tool("nw_search", {"query": word, "sources": ["mehr", "digiato"]})
    assert "HTTP 500" in r.structured_content["errors"]["digiato"]
    assert r.structured_content["count"] >= 1


async def test_latest_all_merges_sorted(client, feeds):
    route_all(feeds)
    r = await client.call_tool("nw_latest_all", {"per_source": 2})
    items = r.structured_content["items"]
    assert len(items) == 12 and not r.structured_content.get("errors")
    dates = [i["published"] for i in items]
    assert dates == sorted(dates, reverse=True)


async def test_latest_all_category_skips_sources_without_it(client, feeds):
    feeds["www.mehrnews.com/rss/tp/25"] = fixture("mehr.xml")
    r = await client.call_tool("nw_latest_all", {"sources": ["mehr", "digiato"], "category": "economy"})
    assert r.structured_content["errors"] == {"digiato": "no category 'economy'"}
    assert {i["source"] for i in r.structured_content["items"]} == {"mehr"}


def _big_feed(n=300, title="ع" * 120, summary="خ" * 600, host="www.mehrnews.com"):
    items = "".join(
        f"<item><title>{title}{k}</title><link>https://{host}/news/{k}</link>"
        f"<pubDate>Mon, 19 Oct 2026 10:{k % 60:02d}:00 +0000</pubDate><description>{summary}</description>"
        f"<category>دسته یک</category><category>دسته دو</category><category>دسته سه</category><category>چهار</category>"
        f"<dc:creator xmlns:dc='http://purl.org/dc/elements/1.1/'>نویسنده نمونه</dc:creator></item>"
        for k in range(n)
    )
    return f"<rss version='2.0'><channel>{items}</channel></rss>".encode()


async def test_max_limit_replies_stay_under_15kb(client, feeds):
    feeds["www.mehrnews.com/rss"] = _big_feed()
    props = {t.name: t.input_schema["properties"] for t in (await client.list_tools()).tools}
    r = await client.call_tool("nw_latest", {"source": "mehr", "limit": props["nw_latest"]["limit"]["maximum"]})
    assert len(r.content[0].text.encode()) < 15_000 and "image" not in r.content[0].text
    r = await client.call_tool(
        "nw_search", {"query": "ع", "sources": ["mehr"], "limit": props["nw_search"]["limit"]["maximum"]}
    )
    assert len(r.content[0].text.encode()) < 15_000
    for s, h in HOSTS.items():
        feeds[h + news.SOURCES[s]["latest"].split(h, 1)[1]] = _big_feed(host=h)
    r = await client.call_tool("nw_latest_all", {"per_source": props["nw_latest_all"]["per_source"]["maximum"]})
    assert len(r.content[0].text.encode()) < 15_000 and r.structured_content["count"] == 6 * news.PER_SOURCE_MAX
    r = await client.call_tool("nw_latest", {"source": "mehr", "limit": 100})
    assert r.is_error  # over the cap is refused


async def test_one_failing_source_keeps_the_rest(client, feeds):
    route_all(feeds)
    feeds["www.zoomit.ir/feed/"] = lambda req: httpx.Response(503)
    r = await client.call_tool("nw_latest_all", {"per_source": 1})
    d = r.structured_content
    assert list(d["errors"]) == ["zoomit"] and "HTTP 503" in d["errors"]["zoomit"]
    assert {i["source"] for i in d["items"]} == set(HOSTS) - {"zoomit"}


async def test_stale_feed_is_flagged(client, feeds):
    feeds["digiato.com/topic/tech/cryptocurrency/feed"] = _big_feed(n=2).replace(b"2026 10:", b"2020 10:")
    r = await client.call_tool("nw_latest", {"source": "digiato", "category": "crypto"})
    assert r.structured_content["stale"] is True
    feeds["www.mehrnews.com/rss"] = _big_feed(n=1).replace(b"2026 10:00", b"2099 10:00")
    r = await client.call_tool("nw_latest", {"source": "mehr"})
    assert not r.structured_content["stale"]


async def test_empty_channel_is_not_cached(client, feeds):
    empty = b"<rss version='2.0'><channel><title>x</title></channel></rss>"
    feeds["digiato.com/feed"] = empty
    assert (await client.call_tool("nw_latest", {"source": "digiato"})).is_error
    feeds["digiato.com/feed"] = fixture("digiato.xml")
    assert not (await client.call_tool("nw_latest", {"source": "digiato"})).is_error
