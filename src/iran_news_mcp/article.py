"""Article tool: fetch a story page from one of the supported sites and return its body as plain text."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Annotated

from pydantic import Field

from . import http
from .registry import tool

CHUNK = 6000  # characters per part; Persian is 2 bytes per character, so a part stays under ~15 KB
VOID = {"area", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
BLOCK = {"p", "div", "li", "br", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "tr", "section"}
SKIP_TAGS = {"script", "style", "noscript", "iframe", "ins", "figure", "figcaption", "form", "button", "svg", "video"}
# "row-start-1": Zoomit's title/breadcrumb/author header inside <article class="contents">.
JUNK = {
    "ads",
    "tags",
    "gallery",
    "item-sharing",
    "news_tools",
    "related-items",
    "invisible",
    "hidden",
    "row-start-1",
    "entekhab_lead2",  # Entekhab's "site name :" label before the first paragraph
}
JUNK_PREFIX = ("ad_", "adv", "cyt-ad", "digiBanner", "HeadingLink__CopyText")
_WS = re.compile(r"[ \t\r\f\v\u00a0]+")


def _is_body(tag: str, attrs: dict[str, str]) -> bool:
    """The element that holds the story text on each site."""
    cls = attrs.get("class", "").split()
    return (
        attrs.get("itemprop") == "articleBody"  # Mehr, Khabaronline, Hamshahri (same CMS)
        or attrs.get("id") == "newsMainBody"  # Tabnak
        or (tag == "article" and "contents" in cls)  # Zoomit (its inner blocks only carry hashed class names)
        or "articlePost" in cls  # Digiato (WordPress)
        or (tag == "div" and "body" in cls)  # Entekhab, Asriran (Tabnak's CMS; no id on these two)
        or "news-body" in cls  # Varzesh3 (other classes are hashed)
    )


def _is_junk(tag: str, attrs: dict[str, str]) -> bool:
    """Ads, related links, tags, share bars, comments and media inside the body."""
    if tag in SKIP_TAGS:
        return True
    return any(c in JUNK or c.startswith(JUNK_PREFIX) or "comment" in c for c in attrs.get("class", "").split())


class _Extract(HTMLParser):
    """Collects the body text (one line per block) plus og:title, description and published time from <meta>."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.stack: list[tuple[str, bool]] = []  # open tags inside the body: (tag, junk)
        self.junk = 0  # how many open tags in the stack are junk
        self.found = False
        self.done = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: v or "" for k, v in attrs}
        if tag == "meta" and (key := a.get("property") or a.get("name")):
            self.meta.setdefault(key, a.get("content", ""))
        if self.done:
            return
        if not self.stack:
            if tag not in VOID and _is_body(tag, a):
                self.found = True
                self.stack.append((tag, False))
            return
        if a.get("id") == "MV_afterBody":  # Asriran leaves its body div open around the "most viewed" and video blocks
            self.done = True
            return
        if tag in BLOCK:
            self.parts.append("\n")
        if tag not in VOID:
            j = _is_junk(tag, a)
            self.junk += j
            self.stack.append((tag, j))

    def handle_endtag(self, tag: str) -> None:
        if not self.stack or self.done:
            return
        # Pop to the matching open tag; unmatched end tags are ignored (pages close <p> implicitly).
        if any(t == tag for t, _ in self.stack):
            while self.stack:
                t, j = self.stack.pop()
                self.junk -= j
                if t == tag:
                    break
            if tag in BLOCK:
                self.parts.append("\n")
            self.done = not self.stack

    def handle_data(self, data: str) -> None:
        if self.stack and not self.junk and not self.done:
            self.parts.append(data)

    def text(self) -> str:
        lines = (_WS.sub(" ", s).strip() for s in "".join(self.parts).split("\n"))
        return "\n".join(s for s in lines if s)


def extract(page: bytes) -> dict[str, str | None]:
    """Article HTML to {title, lead, published, text}. text is "" when no body element was found."""
    p = _Extract()
    p.feed(page.decode("utf-8", "replace"))
    m = p.meta
    return {
        "title": m.get("og:title") or None,
        "lead": m.get("description") or m.get("og:description") or None,
        "published": m.get("article:published_time") or None,
        "text": p.text(),
    }


def _chunks(text: str) -> list[str]:
    """Split on paragraph boundaries into parts of at most CHUNK characters (a longer paragraph stays whole)."""
    out = [""]
    for line in text.split("\n"):
        if out[-1] and len(out[-1]) + len(line) + 1 > CHUNK:
            out.append("")
        out[-1] = f"{out[-1]}\n{line}" if out[-1] else line
    return out


@tool("Read a news article")
async def nw_article(
    url: Annotated[
        str,
        Field(
            description="Article url from nw_latest / nw_search / nw_latest_all (from any listed source).",
            examples=["https://www.mehrnews.com/news/6983987"],
        ),
    ],
    part: Annotated[
        int,
        Field(ge=1, description=f"Part number for long articles ({CHUNK} characters each); see `parts`.", examples=[1]),
    ] = 1,
) -> dict:
    """Fetch one article page and return its full body text, split into parts for long stories.

    Works for every source. Photo and video items often have no body text. `parts` > 1 means call again with part=2, 3, ...
    """
    a = extract(await http.fetch_page(url))
    if len(a["text"] or "") < 40:  # video pages hold only a download label such as "دریافت 44 MB"
        raise http.ApiError("No article text found on that page (photo/video item, live page or a layout change).")
    parts = _chunks(a.pop("text") or "")
    if part > len(parts):
        raise http.ApiError(f"This article has only {len(parts)} part(s).")
    return {"url": url, **a, "part": part, "parts": len(parts), "text": parts[part - 1]}
