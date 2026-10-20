<!-- mcp-name: io.github.sepehr071/iran-news-mcp -->

# iran-news-mcp: Iranian news RSS MCP server for AI agents

**Let your AI agent read Iranian news (اخبار ایران) from Mehr, Khabaronline, Hamshahri, Tabnak, Zoomit and Digiato.**<br>
An unofficial, read-only MCP server over the sites' public RSS feeds and article pages: latest headlines per source and category, a merged overview, keyword search across all six, and the full text of any story.

[For AI agents](#for-ai-agents) · [Quick start](#quick-start) · [Tools](#tools) · [Sources](#sources) · [فارسی](#فارسی)

---

## For AI agents

- **What:** unofficial MCP server for the RSS feeds and article pages of Mehr (mehrnews.com), Khabaronline (khabaronline.ir), Hamshahri (hamshahrionline.ir), Tabnak (tabnak.ir), Zoomit (zoomit.ir) and Digiato (digiato.com). Persian text.
- **Install:** `uvx iran-news-mcp` or `claude mcp add iran-news -- uvx iran-news-mcp`. Transport: stdio. Needs [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python 3.10+).
- **Auth:** none. Optional `IRAN_NEWS_MCP_PROXY` (HTTP proxy URL, or a comma-separated list); system proxy settings are ignored.
- **Access:** read-only. No login or posting, so no confirmation is needed before calling any tool.
- **Tools:** 5: `nw_list_sources`, `nw_latest`, `nw_search`, `nw_latest_all`, `nw_article`. Start with `nw_list_sources` for valid source ids and category slugs.
- **Use when:** the user wants current Iranian headlines, a news overview, recent coverage of a keyword, or the full text of a story.
- **Do not use when:** an archive is needed (only what is in the current feeds, 10 to 300 stories per feed, is searchable).
- **Output:** compact JSON. Times are UTC ISO strings (Tehran is UTC+3:30); summaries are plain text cut to 200 characters (80 in `nw_latest_all`). Null and empty fields are omitted. Replies stay under ~15 KB: `limit` is capped at 15 and `per_source` at 3. A failing source is listed under `errors` while the others still answer. `nw_latest` sets `stale: true` when a feed's newest story is over 3 days old. Feeds are cached for 3 minutes.
- **Machine-readable:** [`server.json`](https://github.com/sepehr071/iran-news-mcp/blob/main/server.json) and the
  [awesome-iran-mcp catalog](https://github.com/sepehr071/awesome-iran-mcp).

## Quick start

```bash
claude mcp add iran-news -- uvx iran-news-mcp
```

Other clients: command `uvx`, args `["iran-news-mcp"]`.

## Tools

| Tool | What it does |
|---|---|
| `nw_list_sources` | The six sources and their category slugs. |
| `nw_latest` | Newest headlines of one source, optionally one category (`source`, `category`, `limit` 1-15). |
| `nw_search` | Keyword search over the current feeds of several sources (`query`, `sources`, `category`, `limit` 1-15). |
| `nw_latest_all` | Newest headlines from every source merged by time (`sources`, `category`, `per_source` 1-3). |
| `nw_article` | Full body text of one story from its `url`, in parts of 6000 characters (`url`, `part`). |

## Sources

| id | Site | Categories | Feeds |
|---|---|---|---|
| `mehr` | Mehr | 14 | one per category (30 items) |
| `khabaronline` | Khabaronline | 12 | one per category (30 items) |
| `hamshahri` | Hamshahri | 16 | one per category (30 items) |
| `tabnak` | Tabnak | 11 | one per category (up to 100 items) |
| `zoomit` | Zoomit | 18 | one feed (300 items), categories filtered here |
| `digiato` | Digiato | 14 | one per topic (10 items) |

Common slugs shared by most sources: `politics`, `economy`, `society`, `culture`, `world`, `sports`, `science`, `provinces`, `photo`. The sites offer more sub-category feeds than listed here; see the API map.

## FAQ

**Does it work outside Iran?** Yes: the RSS endpoints answered from a Turkish exit and from a direct connection in testing. Article pages of Mehr, Khabaronline, Hamshahri, Tabnak, Zoomit and Digiato also answered from both.

**Why no ISNA or IRNA?** Their article pages (also `/amp/` and `/print/`) answer every non-browser client with an ArvanCloud JavaScript check, from an Iranian connection too, so only headlines would work. They were left out.

## فارسی

سرور MCP غیررسمی و فقط‌خواندنی برای خوراک RSS و صفحه‌های خبر شش سایت خبری: مهر، خبرآنلاین، همشهری، تابناک، زومیت و دیجیاتو. آخرین عناوین هر منبع و دسته، مرور ترکیبی، جست‌وجوی کلیدواژه در همه منابع و متن کامل خبر.

```bash
claude mcp add iran-news -- uvx iran-news-mcp
```

## License

MIT
