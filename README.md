<!-- mcp-name: io.github.sepehr071/iran-news-mcp -->

# iran-news-mcp: Iranian news MCP server for AI agents

**Let your AI agent read Iranian news (اخبار ایران) from 10 Persian news sites.**<br>
An unofficial, read-only MCP server over the public RSS feeds and article pages of [Mehr](https://www.mehrnews.com), [Khabaronline](https://www.khabaronline.ir), [Hamshahri](https://www.hamshahrionline.ir), [Tabnak](https://www.tabnak.ir), [Entekhab](https://www.entekhab.ir), [Asriran](https://www.asriran.com), [Zoomit](https://www.zoomit.ir), [Digiato](https://digiato.com), [Varzesh3](https://www.varzesh3.com) and [Khabarvarzeshi](https://www.khabarvarzeshi.com):<br>
latest headlines, a merged overview, keyword search and the full text of any story, from Claude, Cursor or Copilot.

[![PyPI](https://img.shields.io/pypi/v/iran-news-mcp?color=2563eb)](https://pypi.org/project/iran-news-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/iran-news-mcp)](https://pypi.org/project/iran-news-mcp/)
[![CI](https://github.com/sepehr071/iran-news-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sepehr071/iran-news-mcp/actions/workflows/ci.yml)
[![MCP Registry](https://img.shields.io/badge/MCP_Registry-io.github.sepehr071%2Firan--news--mcp-7c3aed)](https://registry.modelcontextprotocol.io/?q=iran-news-mcp)
[![License: MIT](https://img.shields.io/badge/license-MIT-16a34a)](https://github.com/sepehr071/iran-news-mcp/blob/main/LICENSE)

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_iran--news--mcp-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=iran-news&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22iran-news-mcp%22%5D%7D)

[For AI agents](#for-ai-agents) · [Why](#why) · [What it can do](#what-it-can-do) · [Quick start](#quick-start) · [Tools](#tools) · [Sources](#sources) · [How it works](#how-it-works) · [Good to know](#good-to-know) · [FAQ](#faq) · [Configuration](#configuration) · [فارسی](#فارسی) · [Development](#development) · [Related servers](#related-servers)

---

## For AI agents

- **What:** unofficial MCP server (model context protocol) for the RSS feeds and article pages of Mehr (mehrnews.com), Khabaronline (khabaronline.ir), Hamshahri (hamshahrionline.ir), Tabnak (tabnak.ir), Entekhab (entekhab.ir), Asriran (asriran.com), Zoomit (zoomit.ir), Digiato (digiato.com), Varzesh3 (varzesh3.com) and Khabarvarzeshi (khabarvarzeshi.com). Text is Persian. Each source has a `group`: `news`, `tech` or `sports`.
- **Install:** `uvx iran-news-mcp` or `claude mcp add iran-news -- uvx iran-news-mcp`. Transport: stdio. Needs [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python 3.10+).
- **Auth:** none, no API key or account. Optional `IRAN_NEWS_MCP_PROXY` (HTTP proxy URL, or a comma-separated list); system proxy settings are ignored.
- **Access:** read-only. It cannot log in or post, so no confirmation is needed before calling any tool.
- **Tools:** 6, all prefixed `nw_`: `nw_list_sources`, `nw_latest`, `nw_search`, `nw_latest_all`, `nw_tech_news`, `nw_article`. Start with `nw_list_sources` for valid source ids and category slugs; for any technology question start with `nw_tech_news`.
- **Use when:** the user wants current Iranian headlines, a news overview, recent coverage of a keyword, or the full text of a story.
- **Do not use when:** an archive is needed. Only what is in the current feeds (10 to 300 stories per feed) is searchable.
- **Output:** compact JSON. Times are UTC ISO strings (Tehran is UTC+3:30); summaries are plain Persian text. Null and empty fields are omitted. Each item has a `url` to pass to `nw_article`.
- **Machine-readable:** [`server.json`](https://github.com/sepehr071/iran-news-mcp/blob/main/server.json) and the
  [awesome-iran-mcp catalog](https://github.com/sepehr071/awesome-iran-mcp).

## Why

Iranian news is spread over many sites, in Persian, each with its own category layout and feed addresses. Asking "what happened in the economy today" or "what is being said about X" means opening several pages. With `iran-news-mcp` the agent lists the sources, pulls the newest headlines in one call (or searches them all for a keyword) and opens the full text of the story that matters.

## What it can do

- **Latest headlines** of one source, optionally one category (politics, economy, society, culture, world, sports, science, provinces, photo, ...)
- **Merged overview** of every source (or a chosen group) sorted by time
- **Keyword search** over the stories currently in the feeds, with Arabic/Persian ي/ك and ZWNJ normalised
- **Technology news** from Digiato (read several feed pages deep) and optionally Zoomit
- **Full article text** of a story from its link, in parts of 6000 characters
- **Sports news** from Varzesh3 and Khabarvarzeshi
- **Read-only by design**: no login, no posting

Example prompts:

- "What are the top economy headlines on Tabnak and Khabaronline right now?"
- "Give me a one-line overview of the latest news from every source."
- "Search the news for 'earthquake' and summarize what the first two results say."
- "Latest smartphone news from Digiato and Zoomit."
- <span dir="rtl">آخرین خبرهای اقتصادی همشهری و خبرآنلاین را بیاور.</span>
- <span dir="rtl">درباره «بورس» در خبرگزاری&zwnj;ها جست&zwnj;وجو کن و متن کامل مهم&zwnj;ترین خبر را خلاصه کن.</span>
- <span dir="rtl">تازه&zwnj;ترین اخبار فناوری از دیجیاتو و زومیت چیست؟</span>

## Quick start

You need [uv](https://docs.astral.sh/uv/getting-started/installation/). No API key or account.

<details open>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add iran-news -- uvx iran-news-mcp
```
</details>

<details>
<summary><b>Claude Desktop</b></summary>

Settings → Developer → Edit Config, then add:

```json
{
  "mcpServers": {
    "iran-news": { "command": "uvx", "args": ["iran-news-mcp"] }
  }
}
```
</details>

<details>
<summary><b>Cursor</b></summary>

Add the Claude Desktop block to `~/.cursor/mcp.json` (or `.cursor/mcp.json` in a project).
</details>

<details>
<summary><b>VS Code (Copilot agent mode)</b></summary>

Click **Install in VS Code** above, or add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "iran-news": { "type": "stdio", "command": "uvx", "args": ["iran-news-mcp"] }
  }
}
```
</details>

<details>
<summary><b>Codex CLI</b></summary>

```bash
codex mcp add iran-news -- uvx iran-news-mcp
```

or add to `~/.codex/config.toml`:

```toml
[mcp_servers.iran-news]
command = "uvx"
args = ["iran-news-mcp"]
```
</details>

<details>
<summary><b>Gemini CLI</b></summary>

Add the Claude Desktop block to `~/.gemini/settings.json`.
</details>

<details>
<summary><b>Windsurf</b></summary>

Add the Claude Desktop block to `~/.codeium/windsurf/mcp_config.json`.
</details>

<details>
<summary><b>Anything else</b></summary>

It's a standard stdio MCP server: run `uvx iran-news-mcp`, or `pip install iran-news-mcp` and run `iran-news-mcp`.
</details>

## Tools

| Tool | What it does |
|---|---|
| `nw_list_sources` | Lists the 10 sources with their `group` and category slugs; call this first for valid `source` and `category` values. |
| `nw_latest` | Newest headlines of one source, optionally one category (`source`, `category`, `limit` 1-15). |
| `nw_search` | Keyword search over the current feeds of several sources (`query`, `sources`, `category`, `limit` 1-15). |
| `nw_latest_all` | Newest headlines from every source merged by time (`sources`, `category`, `per_source` 1-2). |
| `nw_tech_news` | Technology news, Digiato by default read several feed pages deep, optionally Zoomit (`topic`, `category`, `limit` 1-30, `source` digiato / zoomit / both); summaries up to 300 characters, `scanned` shows search depth. |
| `nw_article` | Full body text of one story from its `url`, in parts of 6000 characters (`url`, `part`). |

All tools are annotated `readOnlyHint: true`.

## Sources

| id | Site | Group | Categories | Feeds |
|---|---|---|---|---|
| `mehr` | Mehr | news | 14 | one per category (30 items) |
| `khabaronline` | Khabaronline | news | 12 | one per category (30 items) |
| `hamshahri` | Hamshahri | news | 16 | one per category (30 items) |
| `tabnak` | Tabnak | news | 11 | one per category (up to 100 items) |
| `entekhab` | Entekhab | news | 11 | one per category (up to 100 items) |
| `asriran` | Asriran | news | 11 | one per category (up to 100 items) |
| `zoomit` | Zoomit | tech | 18 | one feed (300 items), categories filtered here |
| `digiato` | Digiato | tech | 14 | one per topic (10 items) |
| `varzesh3` | Varzesh3 | sports | 1 (`sports`) | one feed (40 items) |
| `khabarvarzeshi` | Khabarvarzeshi | sports | 1 (`sports`) | one feed (30 items) |

Common slugs shared by most sources: `politics`, `economy`, `society`, `culture`, `world`, `sports`, `science`, `provinces`, `photo`. Always call `nw_list_sources` for the exact slugs per source.

## How it works

```text
  AI agent  (Claude, Cursor, Copilot, ...)
      │
      │  MCP over stdio
      ▼
  iran-news-mcp  (runs on your machine)
      │
      │  HTTPS
      └──────▶  public RSS feeds and article pages of the 10 news sites
```

`iran-news-mcp` runs locally, reads each site's public RSS feed (RSS 2.0 or Atom) and, for `nw_article`, the story's HTML page. There is no hosted server in between, no API key, and nothing about you is sent anywhere else.

## Good to know

- **Times are UTC** ISO strings; Tehran is UTC+3:30.
- **Feeds only, no archive.** Search covers the stories currently in the feeds (10 to 300 per feed), newest first. It is a keyword match, not a full-text index of the sites.
- **Reply size is capped** at about 15 KB: `limit` is at most 15 and `per_source` at most 2. `nw_tech_news` is the exception (`limit` up to 30, summaries up to 300 characters, replies up to roughly 25 KB).
- **Summaries** are plain text cut to 200 characters (80 in `nw_latest_all`). Photo feeds (for example Mehr `photo`) have mostly empty descriptions.
- **Stale feeds:** `nw_latest` sets `stale: true` when a feed's newest story is more than 3 days old.
- **Feeds are cached for 3 minutes**, so repeated calls do not hit the sites again. Timeouts, network errors, 5xx and 429 are retried up to twice.
- **Partial answers:** a source that fails is listed under `errors` while the others still answer.
- **Zoomit** has a single feed, so its categories are filtered on this side. **Digiato** feeds hold 10 items, so `nw_tech_news` reads extra pages.
- **No ISNA or IRNA.** Their article pages sit behind a JavaScript challenge that plain clients cannot pass, so only headlines would work. They were left out.
- **What it does NOT do:** no login, no posting, no comments, no images in results, no archive search.
- **Proxy:** set `IRAN_NEWS_MCP_PROXY` if your network cannot reach the sites. Normal system proxy variables are ignored on purpose.

## FAQ

<details>
<summary><b>Is there an MCP server for Iranian news?</b></summary>

Yes: `iran-news-mcp` is an unofficial, read-only MCP server with 6 tools over the public RSS feeds and article pages of 10 Persian news sites. No API key is needed.
</details>

<details>
<summary><b>How do I read Persian news with Claude, Cursor or Copilot?</b></summary>

Add the server with `claude mcp add iran-news -- uvx iran-news-mcp` (or the matching config in [Quick start](#quick-start)), then ask in plain language, in Persian or English.
</details>

<details>
<summary><b>Is it official, safe and free?</b></summary>

It is unofficial and not affiliated with any of the news sites. It is read-only, runs on your machine, and is free under the MIT license.
</details>

<details>
<summary><b>Does it work outside Iran?</b></summary>

Yes: in testing the feeds and article pages answered both from a direct Iranian connection and from a Turkish proxy exit. If your network blocks the sites, set `IRAN_NEWS_MCP_PROXY`.
</details>

<details>
<summary><b>Can I get only tech or only sports news?</b></summary>

Yes. `nw_list_sources` shows each source's `group` (`news`, `tech`, `sports`); pass the ids of one group as `sources` to `nw_search` or `nw_latest_all`. For technology questions use `nw_tech_news`.
</details>

<details>
<summary><b>Can it search old news?</b></summary>

No. `nw_search` looks only at the stories currently in the RSS feeds. For something older, give `nw_article` a link you already have.
</details>

<details>
<summary><b>Why are ISNA and IRNA missing?</b></summary>

Their article pages answer non-browser clients with a JavaScript check, even from an Iranian connection, so only headlines would work. They were left out rather than half-supported.
</details>

<details>
<summary><b>A long article is cut off</b></summary>

`nw_article` returns the body in parts of 6000 characters. When a story has more than one part, call it again with `part=2`, and so on.
</details>

<details>
<summary><b>Claude Desktop says <code>uvx</code> is not found</b></summary>

Use the full path to `uvx` (`where uvx` on Windows, `which uvx` on macOS/Linux) as `command`.
</details>

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `IRAN_NEWS_MCP_PROXY` | unset | Optional HTTP proxy URL. System proxy settings are ignored. Also accepts a comma-separated list: one is used until it gets blocked or fails to connect, then the next. |

<a id="فارسی"></a>

## فارسی: سرور MCP اخبار ایران

<div dir="rtl">

**iran-news-mcp** یک سرور MCP غیررسمی و فقط&zwnj;خواندنی برای خواندن اخبار ایران است. این سرور از خوراک RSS و صفحه&zwnj;های خبر ده منبع استفاده می&zwnj;کند: مهر، خبرآنلاین، همشهری، تابناک، انتخاب، عصر ایران، زومیت، دیجیاتو، ورزش سه و خبرورزشی. دستیار هوش مصنوعی شما (Claude، Cursor، Copilot و ...) با آن می&zwnj;تواند آخرین خبرها را بخواند و در خبرگزاری&zwnj;ها جست&zwnj;وجو کند.

**چه کارهایی می&zwnj;کند**

- **آخرین عناوین** هر خبرگزاری و هر دسته (سیاسی، اقتصادی، اجتماعی، فرهنگی، جهان، ورزشی، علمی، استان&zwnj;ها و ...).
- **مرور ترکیبی** خبرهای همه منابع، مرتب بر اساس زمان.
- **جست&zwnj;وجوی کلیدواژه** در خبرهایی که اکنون در خوراک&zwnj;ها هستند.
- **اخبار فناوری** از دیجیاتو و زومیت (موبایل، لپ&zwnj;تاپ، هوش مصنوعی، بازی و ...).
- **متن کامل خبر** از روی پیوند آن، در بخش&zwnj;های ۶۰۰۰ نویسه&zwnj;ای.

**نکته&zwnj;ها**

- فقط خواندنی است: وارد حساب نمی&zwnj;شود و چیزی منتشر نمی&zwnj;کند.
- جست&zwnj;وجو فقط روی خبرهای فعلی خوراک&zwnj;ها کار می&zwnj;کند و آرشیو نیست.
- زمان&zwnj;ها به وقت UTC هستند (تهران UTC+3:30).
- روی سیستم خود شما اجرا می&zwnj;شود و کلید API لازم ندارد.
- ایسنا و ایرنا به&zwnj;دلیل محافظ جاوااسکریپتی صفحه&zwnj;های خبرشان پشتیبانی نمی&zwnj;شوند.

**نصب** (اول [uv](https://docs.astral.sh/uv/getting-started/installation/) را نصب کنید). در Claude Code:

</div>

```bash
claude mcp add iran-news -- uvx iran-news-mcp
```

<div dir="rtl">

در Claude Desktop، Cursor و بقیه برنامه&zwnj;ها همان تنظیم بخش [Quick start](#quick-start) را بگذارید.

**نمونه پرسش&zwnj;ها**

- «آخرین خبرهای اقتصادی تابناک و خبرآنلاین چیست؟»
- «درباره زلزله در همه خبرگزاری&zwnj;ها جست&zwnj;وجو کن.»
- «تازه&zwnj;ترین خبرهای ورزشی را از ورزش سه بیاور.»
- «اخبار فناوری و موبایل امروز را از دیجیاتو و زومیت بگو.»

</div>

## Development

```bash
git clone https://github.com/sepehr071/iran-news-mcp && cd iran-news-mcp
uv sync
uv run python -m pytest            # offline, against recorded feeds
uv run python -m pytest -m live    # real feeds
uv run ruff check .
```

Tools live in `src/iran_news_mcp/news.py` (feeds, search, tech news) and `article.py` (story text); each is a typed async function with a docstring that tells the agent when to use it. Feed addresses are in the `SOURCES` table in `news.py`. Issues and PRs are welcome, especially new sources and fixes when a feed changes.

Releases: bump the version in `pyproject.toml` and `server.json`, then push a `v*` tag. GitHub Actions tests, publishes to PyPI and the [MCP Registry](https://registry.modelcontextprotocol.io), and creates the GitHub Release.

## Related servers

- [Tgju MCP server](https://github.com/sepehr071/tgju-mcp) for gold, currency and market prices
- [Tsetmc MCP server](https://github.com/sepehr071/tsetmc-mcp) for the Tehran Stock Exchange
- [Iran Quake MCP server](https://github.com/sepehr071/iran-quake-mcp) for earthquakes in Iran
- [Iran Crypto MCP server](https://github.com/sepehr071/iran-crypto-mcp) for cryptocurrency prices in Iran
- [awesome-iran-mcp](https://github.com/sepehr071/awesome-iran-mcp): catalog of all Iranian-service MCP servers

## Disclaimer

Unofficial and not affiliated with or endorsed by Mehr, Khabaronline, Hamshahri, Tabnak, Entekhab, Asriran, Zoomit, Digiato, Varzesh3 or Khabarvarzeshi. It reads their public RSS feeds and article pages, which can change without notice. Headlines and article text belong to their publishers; please keep request rates reasonable.

## License

[MIT](https://github.com/sepehr071/iran-news-mcp/blob/main/LICENSE)
