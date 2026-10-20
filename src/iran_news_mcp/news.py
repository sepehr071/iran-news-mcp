"""News tools: list sources, latest per source/category, keyword search and a mixed latest across sources."""

from __future__ import annotations

import asyncio
import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Annotated, Any

from pydantic import Field

from . import http
from .registry import clip, tool

# source -> name, latest feed, category feed template, {slug: (id in template, Persian title)}.
# cat=None: the site has one feed only and categories are filtered client-side on the item <category> domain slug.
SOURCES: dict[str, dict[str, Any]] = {
    "mehr": {
        "name": "Mehr (مهر)",
        "latest": "https://www.mehrnews.com/rss",
        "cat": "https://www.mehrnews.com/rss/tp/{}",
        "cats": {
            "politics": ("7", "سیاست"),
            "world": ("8", "بین الملل"),
            "economy": ("25", "اقتصاد"),
            "society": ("6", "جامعه"),
            "sports": ("9", "ورزش"),
            "culture": ("2", "فرهنگ و ادب"),
            "art": ("1", "هنر"),
            "religion": ("3", "دین، حوزه، اندیشه"),
            "science": ("5", "دانشگاه و فناوری"),
            "health": ("550", "سلامت"),
            "photo": ("11", "عکس"),
            "video": ("121", "فیلم"),
            "provinces": ("19", "استان‌ها"),
            "market": ("653", "بازار"),
        },
    },
    "khabaronline": {
        "name": "Khabaronline (خبرآنلاین)",
        "latest": "https://www.khabaronline.ir/rss",
        "cat": "https://www.khabaronline.ir/rss/tp/{}",
        "cats": {
            "politics": ("1", "سیاسی"),
            "economy": ("2", "اقتصادی"),
            "culture": ("3", "فرهنگی و هنری"),
            "society": ("4", "اجتماعی"),
            "world": ("5", "بین‌الملل"),
            "sports": ("6", "ورزشی"),
            "science": ("7", "دانش و فناوری"),
            "multimedia": ("10", "چندرسانه‌ای"),
            "provinces": ("12", "استان‌ها"),
            "ideas": ("1409", "اندیشه"),
            "religion": ("1155", "دین"),
            "history": ("1427", "تاریخ"),
        },
    },
    "hamshahri": {
        "name": "Hamshahri (همشهری)",
        "latest": "https://www.hamshahrionline.ir/rss",
        "cat": "https://www.hamshahrionline.ir/rss/tp/{}",
        "cats": {
            "politics": ("6", "سیاسی ایران"),
            "world": ("11", "جهان"),
            "economy": ("10", "اقتصادی"),
            "society": ("5", "اجتماعی"),
            "city": ("7", "شهر"),
            "life": ("21", "زندگی"),
            "science": ("20", "دانش"),
            "sports": ("9", "ورزشی"),
            "culture": ("26", "فرهنگی"),
            "provinces": ("746", "استان‌ها"),
            "ict": ("19", "ارتباطات"),
            "multimedia": ("630", "چندرسانه‌ای"),
            "health": ("745", "سلامت و پزشکی"),
            "photo": ("731", "عکس"),
            "business": ("751", "کسب و کار"),
            "incidents": ("766", "حوادث"),
        },
    },
    "tabnak": {
        "name": "Tabnak (تابناک)",
        "latest": "https://www.tabnak.ir/fa/rss/allnews",
        "cat": "https://www.tabnak.ir/fa/rss/{}",
        "cats": {
            "front-page": ("1", "صفحه نخست"),
            "world": ("17", "بین الملل"),
            "economy": ("6", "اقتصادی"),
            "sports": ("2", "ورزشی"),
            "politics": ("24", "سیاسی"),
            "society": ("3", "اجتماعی"),
            "culture": ("21", "فرهنگی"),
            "video": ("16", "فیلم"),
            "photo": ("27", "عکس"),
            "market": ("23", "بازار و آگهی"),
            "tech": ("26", "فناوری"),
        },
    },
    "zoomit": {
        "name": "Zoomit (زومیت)",
        "latest": "https://www.zoomit.ir/feed/",
        "cat": None,
        "cats": {
            "mobile": ("", "موبایل"),
            "science": ("", "علم"),
            "ai-articles": ("", "هوش مصنوعی"),
            "tech-iran": ("", "ایران"),
            "iran-news": ("", "اخبار ایران"),
            "business": ("", "کسب و کار"),
            "apple": ("", "اپل"),
            "car": ("", "خودرو و موتورسیکلت"),
            "health-medical": ("", "پزشکی و سلامت"),
            "gaming": ("", "بازی"),
            "economics": ("", "مالی و اقتصادی"),
            "samsung": ("", "سامسونگ"),
            "tech": ("", "فناوری"),
            "security": ("", "امنیت و حریم خصوصی"),
            "internet-network": ("", "اینترنت و شبکه"),
            "software-news": ("", "دنیای نرم‌افزار"),
            "cryptocurrency": ("", "ارز دیجیتال"),
            "space": ("", "نجوم و فضا"),
        },
    },
    "digiato": {
        "name": "Digiato (دیجیاتو)",
        "latest": "https://digiato.com/feed",
        "cat": "https://digiato.com/topic/{}/feed",
        "cats": {
            "mobile": ("tech/mobile", "موبایل"),
            "apps": ("tech/app", "اپلیکیشن"),
            "ai": ("tech/artificial-intelligence", "هوش مصنوعی"),
            "gadgets": ("tech/gadgets", "گجت"),
            "hardware": ("tech/computers-hardware", "کامپیوتر و سخت‌افزار"),
            "laptop": ("tech/laptop", "لپ‌تاپ"),
            "crypto": ("tech/cryptocurrency", "ارز دیجیتال"),
            "internet": ("tech/internet-network", "اینترنت و شبکه"),
            "security": ("tech/security", "امنیت"),
            "reviews": ("dgreview", "بررسی تخصصی"),
            "car": ("car/car-news", "اخبار خودرو"),
            "business": ("business", "کسب‌وکار"),
            "buying-guide": ("buying-guide", "راهنمای خرید"),
            "science": ("science/astronomy", "علم و نجوم"),
        },
    },
}

Source = Annotated[
    str,
    Field(
        description="Source id: mehr, khabaronline, hamshahri, tabnak, zoomit or digiato (see nw_list_sources).",
        examples=["mehr"],
    ),
]
Category = Annotated[
    str,
    Field(
        description="Category slug from nw_list_sources, e.g. 'politics', 'economy', 'sports'. Empty = the source's main latest feed.",
        examples=["economy"],
    ),
]
SourceList = Annotated[
    list[str], Field(description="Source ids to include. Empty = all six.", examples=[["mehr", "tabnak"]])
]

LIMIT_MAX = 15  # keeps a full nw_latest / nw_search reply under ~15 KB
PER_SOURCE_MAX = 3  # 6 sources x 3 brief items stay under ~15 KB
STALE_AFTER = timedelta(days=3)  # a feed whose newest story is older is flagged (Digiato leaf feeds go quiet)

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_WP_TAIL = re.compile(r"\s*The post .* appeared first on .*$")  # WordPress feed footer (Digiato)
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def _norm(s: str) -> str:
    """Lowercase; Arabic ي/ك become Persian ی/ک; ZWNJ and Persian/Arabic digits are normalised."""
    return _WS.sub(" ", s.translate(_DIGITS).replace("ي", "ی").replace("ك", "ک").replace("‌", " ")).strip().lower()


def _text(s: str | None) -> str:
    """HTML (possibly CDATA) to plain text."""
    return _WP_TAIL.sub("", _WS.sub(" ", html.unescape(_TAG.sub(" ", s or ""))).strip())


def _date(s: str | None) -> datetime | None:
    """RFC 822 or ISO 8601 to an aware UTC datetime; None if unparseable."""
    s = (s or "").strip()
    if not s:
        return None
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    return d.astimezone(timezone.utc) if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_feed(xml: bytes, source: str) -> list[dict[str, Any]]:
    """RSS 2.0 or Atom bytes to item dicts (title, url, published, summary, categories, image, author)."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        raise http.ApiError(f"{source} returned feed XML that could not be parsed ({e}).") from e
    items = []
    for el in root.iter():
        if _local(el.tag) not in ("item", "entry"):
            continue
        f: dict[str, Any] = {"categories": [], "slugs": []}
        for c in el:
            t = _local(c.tag)
            v = (c.text or "").strip()
            if t == "title":
                f["title"] = _text(v)
            elif t == "link":
                f["url"] = v or c.get("href", "")
            elif t == "guid" and "url" not in f and v.startswith("http"):
                f["url"] = v
            elif t in ("pubDate", "published", "updated", "date") and "date" not in f:
                f["date"] = _date(v)
            elif t in ("description", "summary") and "summary" not in f:
                f["summary"] = _text(v)
            elif t == "category":
                name = v or c.get("term", "")
                if name:
                    f["categories"].append(_text(name))
                if dom := c.get("domain"):
                    f["slugs"].append(dom.rstrip("/").rsplit("/", 1)[-1])
            elif t in ("creator", "author") and "author" not in f:
                f["author"] = _text("".join(c.itertext()))
            elif t in ("thumbnail", "content", "enclosure") and "image" not in f and c.get("url"):
                if c.get("medium", "image") == "image" and "image" in (c.get("type") or "image"):
                    f["image"] = c.get("url")
        if f.get("title") and f.get("url"):
            items.append(f)
    return items


def _entry(source: str, it: dict[str, Any], brief: bool = False) -> dict[str, Any]:
    d = it.get("date")
    return {
        "source": source,
        "title": it["title"],
        "url": it["url"],
        "published": d.isoformat(timespec="minutes") if d else None,
        "summary": clip(it.get("summary"), n=80 if brief else 200),
        "categories": [] if brief else it["categories"][:3],
        "author": None if brief else it.get("author"),
    }


def _feed_url(source: str, category: str) -> str:
    if source not in SOURCES:
        raise http.ApiError(f"Unknown source '{source}'. Use one of: {', '.join(SOURCES)}.")
    s = SOURCES[source]
    if not category:
        return s["latest"]
    if category not in s["cats"]:
        raise http.ApiError(f"{source} has no category '{category}'. Available: {', '.join(s['cats'])}.")
    return s["latest"] if s["cat"] is None else s["cat"].format(s["cats"][category][0])


async def _items(source: str, category: str) -> list[dict[str, Any]]:
    """Parsed items of one source/category, newest first. Zoomit categories are filtered here."""
    url = _feed_url(source, category)
    items = parse_feed(await http.fetch_feed(url), source)
    if not items:  # Digiato sometimes answers an empty channel for a feed that normally has items
        http.forget(url)  # do not cache the empty answer
        raise http.ApiError(f"{source} returned an empty feed; try again in a few minutes.")
    if category and SOURCES[source]["cat"] is None:
        items = [i for i in items if category in i["slugs"]]
    items.sort(key=lambda i: i.get("date") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return items


async def _many(sources: list[str], category: str) -> tuple[list[tuple[str, dict[str, Any]]], dict[str, str]]:
    """Fetch several sources concurrently (the client caps in-flight calls). Failures and sources without the
    category are reported per source instead of failing the whole call."""
    ids = list(dict.fromkeys(sources)) or list(SOURCES)
    for s in ids:
        if s not in SOURCES:
            raise http.ApiError(f"Unknown source '{s}'. Use one of: {', '.join(SOURCES)}.")
    wanted = [s for s in ids if not category or category in SOURCES[s]["cats"]]
    errors = {s: f"no category '{category}'" for s in ids if s not in wanted}
    results = await asyncio.gather(*(_items(s, category) for s in wanted), return_exceptions=True)
    out = []
    for s, r in zip(wanted, results, strict=True):
        if isinstance(r, Exception):
            errors[s] = str(r)[:200]
        else:
            out += [(s, i) for i in r]
    return out, errors


def _by_date(pairs: list[tuple[str, dict[str, Any]]]) -> list[tuple[str, dict[str, Any]]]:
    return sorted(pairs, key=lambda p: p[1].get("date") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)


@tool("List news sources")
async def nw_list_sources() -> dict:
    """List the six news sources and their category slugs; call this first to know valid `source` and `category` values.

    Sources: mehr, khabaronline, hamshahri, tabnak, zoomit, digiato. Next: nw_latest, nw_search or nw_latest_all.
    """
    return {
        "sources": [
            {
                "id": k,
                "name": v["name"],
                "categories": {slug: title for slug, (_, title) in v["cats"].items()},
            }
            for k, v in SOURCES.items()
        ]
    }


@tool("Latest news from a source")
async def nw_latest(
    source: Source,
    category: Category = "",
    limit: Annotated[
        int, Field(ge=1, le=LIMIT_MAX, description=f"Max items (1-{LIMIT_MAX}), newest first.", examples=[10])
    ] = 10,
) -> dict:
    """Return the newest headlines of one news source, optionally of one category.

    Each item has title, url, published (UTC ISO), summary (plain text) and categories. `stale: true` means the feed's
    newest story is over 3 days old (some Digiato topic feeds go quiet). Use nw_list_sources for
    category slugs; use nw_search to look for a topic across sources.
    """
    items = await _items(source, category)
    newest = items[0].get("date") if items else None
    return {
        "source": source,
        "category": category or None,
        "stale": bool(newest and datetime.now(timezone.utc) - newest > STALE_AFTER) or None,
        "count": min(limit, len(items)),
        "items": [_entry(source, i) for i in items[:limit]],
    }


@tool("Search news across sources")
async def nw_search(
    query: Annotated[
        str,
        Field(
            min_length=1,
            description="Keywords; every word must appear in the title or summary. Persian works best.",
            examples=["بورس"],
        ),
    ],
    sources: SourceList = [],  # noqa: B006
    category: Category = "",
    limit: Annotated[
        int, Field(ge=1, le=LIMIT_MAX, description=f"Max items (1-{LIMIT_MAX}), newest first.", examples=[10])
    ] = 10,
) -> dict:
    """Search recent headlines of several sources for a keyword (client-side over their current feeds, newest first).

    Only the items currently in each feed (roughly the last 10-300 stories) are searched, not an archive.
    Sources that failed or lack the category are listed under `errors`.
    """
    words = _norm(query).split()
    if not words:
        raise http.ApiError("Query has no searchable words; pass at least one keyword.")
    pairs, errors = await _many(sources, category)
    hits = [(s, i) for s, i in pairs if all(w in _norm(f"{i['title']} {i.get('summary') or ''}") for w in words)]
    hits = _by_date(hits)[:limit]
    return {"query": query, "count": len(hits), "items": [_entry(s, i) for s, i in hits], "errors": errors}


@tool("Latest news across sources")
async def nw_latest_all(
    sources: SourceList = [],  # noqa: B006
    category: Category = "",
    per_source: Annotated[
        int,
        Field(
            ge=1,
            le=PER_SOURCE_MAX,
            description=f"Items (1-{PER_SOURCE_MAX}) taken from each source before merging.",
            examples=[2],
        ),
    ] = 2,
) -> dict:
    """Return the newest headlines from every source (or the chosen ones), merged and sorted by time.

    Use it for a news overview; pass a common category slug such as 'economy' or 'sports' to narrow it.
    Sources that failed or lack the category are listed under `errors`.
    """
    pairs, errors = await _many(sources, category)
    taken: list[tuple[str, dict[str, Any]]] = []
    seen: dict[str, int] = {}
    for s, i in pairs:  # each source's items are already newest first
        if seen.get(s, 0) < per_source:
            seen[s] = seen.get(s, 0) + 1
            taken.append((s, i))
    taken = _by_date(taken)
    return {"count": len(taken), "items": [_entry(s, i, brief=True) for s, i in taken], "errors": errors}
