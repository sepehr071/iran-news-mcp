import httpx
import pytest

from iran_news_mcp import article, http

pytestmark = pytest.mark.anyio

MEHR = "https://www.mehrnews.com/news/1/slug"

# Same CMS markup as Mehr/Khabaronline/Hamshahri: unclosed <p>, an ad box, a script and a figure inside the body.
# The saba-backlink is the inline site name ("به گزارش همشهری‌آنلاین") and stays.
CMS_PAGE = """<html><head><meta property="og:title" content="عنوان خبر">
<meta name="description" content="خلاصه"><meta property="article:published_time" content="2026-10-20T09:36:57Z"></head>
<body><div class="sidebar"><p>منو</p></div>
<div class="item-text" itemprop="articleBody"><p>پاراگراف اول<p>پاراگراف <b>دوم</b>&nbsp;اینجا</p>
<div class="box ads"><p>تبلیغ</p></div><script>var x = 1;</script><br>
<figure><img src="a.jpg"><figcaption>عکس</figcaption></figure>
<p>به گزارش <a class="saba-backlink">همشهری</a>، پاراگراف سوم</p></div><div class="box related-items"><p>خبر مرتبط</p></div></body></html>""".encode()

ZOOMIT_PAGE = """<html><head><meta property="og:title" content="زومیت"></head><body>
<article class="contents"><div class="col-span-full row-start-1"><h1>عنوان</h1><span>نویسنده</span></div>
<div class="x"><div class="BlockContainer__InnerArticleContainer-sc-1 a"><p>متن یک</p></div>
<div class="flex invisible"><span>تبلیغات</span></div><div class="HeadingLink__CopyText-sc-2 b">کپی لینک</div>
<div class="BlockContainer__InnerArticleContainer-sc-1 a"><h2>زیرعنوان</h2><p>متن دو</p></div></div></article>
<footer><p>پانویس</p></footer></body></html>""".encode()


def test_extract_cms_body_skips_junk():
    a = article.extract(CMS_PAGE)
    assert a["text"] == "پاراگراف اول\nپاراگراف دوم اینجا\nبه گزارش همشهری، پاراگراف سوم"
    assert a["title"] == "عنوان خبر" and a["lead"] == "خلاصه" and a["published"].startswith("2026-10-20")


@pytest.mark.parametrize(
    "body",
    [
        '<div class="body" id="newsMainBody"><p>متن یک</p><div class="adv_content">x</div><p>متن دو</p></div>',
        '<div class="articlePost"><p class="wp-block-paragraph">متن یک</p><div class="ad_728_90">x</div>'
        '<p class="wp-block-paragraph">متن دو</p></div>',
    ],
    ids=["tabnak", "digiato"],
)
def test_extract_tabnak_and_digiato(body):
    assert article.extract(f"<html><body><p>بیرون</p>{body}<p>بیرون</p></body></html>".encode())["text"] == (
        "متن یک\nمتن دو"
    )


def test_extract_zoomit_skips_header_and_ad_label():
    assert article.extract(ZOOMIT_PAGE)["text"] == "متن یک\nزیرعنوان\nمتن دو"


def test_chunks_split_on_paragraphs(monkeypatch):
    monkeypatch.setattr(article, "CHUNK", 10)
    assert article._chunks("aaaa\nbbbb\ncccccccccccccc\nd") == ["aaaa\nbbbb", "cccccccccccccc", "d"]


async def test_article_tool(client, feeds):
    feeds["www.mehrnews.com/news/1/slug"] = CMS_PAGE
    r = await client.call_tool("nw_article", {"url": MEHR})
    d = r.structured_content
    assert d["title"] == "عنوان خبر" and d["parts"] == 1 and d["text"].startswith("پاراگراف اول")
    r = await client.call_tool("nw_article", {"url": MEHR, "part": 2})
    assert r.is_error and "only 1 part" in r.content[0].text


async def test_long_article_parts_stay_under_15kb(client, feeds):
    body = "".join(f"<p>{'خبر ' * 60}{i}</p>" for i in range(200))  # ~48k characters
    feeds["www.mehrnews.com/news/1/slug"] = f'<div itemprop="articleBody">{body}</div>'.encode()
    first = await client.call_tool("nw_article", {"url": MEHR})
    parts = first.structured_content["parts"]
    assert parts > 1
    last = await client.call_tool("nw_article", {"url": MEHR, "part": parts})
    for r in (first, last):
        assert len(r.content[0].text.encode()) < 15_000


async def test_page_without_body_is_an_error(client, feeds):
    feeds["www.mehrnews.com/news/1/slug"] = '<div itemprop="articleBody"><a>دریافت</a><span>44 MB</span></div>'.encode()
    r = await client.call_tool("nw_article", {"url": MEHR})
    assert r.is_error and "No article text" in r.content[0].text


async def test_arvan_challenge_is_a_clear_error(client, feeds):
    feeds["www.khabaronline.ir/news/1"] = b"<html><script>document.cookie = '__arcsjs=' + x;</script></html>"
    r = await client.call_tool("nw_article", {"url": "https://www.khabaronline.ir/news/1"})
    assert r.is_error and "browser check" in r.content[0].text


async def test_missing_article_message(feeds):
    with pytest.raises(http.ApiError, match="Article not found"):
        await http.fetch_page("https://www.mehrnews.com/news/404")


async def test_one_redirect_is_followed(feeds):
    feeds["www.mehrnews.com/news/1"] = lambda req: httpx.Response(301, headers={"location": "/news/1/slug"})
    feeds["www.mehrnews.com/news/1/slug"] = CMS_PAGE
    assert await http.fetch_page("https://www.mehrnews.com/news/1") == CMS_PAGE
    assert feeds.calls[-1].headers["accept"].startswith("text/html")


async def test_redirect_off_the_allowlist_is_refused(feeds):
    feeds["www.mehrnews.com/news/1"] = lambda req: httpx.Response(302, headers={"location": "https://evil.example/x"})
    with pytest.raises(http.ApiError, match="unexpected host"):
        await http.fetch_page("https://www.mehrnews.com/news/1")


async def test_page_host_allowlist_and_https():
    for url in ("https://example.com/news/1", "http://www.mehrnews.com/news/1"):
        with pytest.raises(http.ApiError, match="unexpected host"):
            await http.fetch_page(url)
