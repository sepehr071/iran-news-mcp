<!-- mcp-name: io.github.sepehr071/iran-news-mcp -->

# iran-news-mcp: Iranian news RSS MCP server for AI agents

**Let your AI agent read Iranian news (اخبار ایران) from 10 sources: Mehr, Khabaronline, Hamshahri, Tabnak, Entekhab, Asriran, Zoomit, Digiato, Varzesh3 and Khabarvarzeshi.**<br>
An unofficial, read-only MCP server over the sites' public RSS feeds and article pages: latest headlines per source and category, a merged overview, keyword search across all of them, and the full text of any story.

[For AI agents](#for-ai-agents) · [Quick start](#quick-start) · [Tools](#tools) · [Sources](#sources) · [فارسی](#فارسی)

---

## For AI agents

- **What:** unofficial MCP server for the RSS feeds and article pages of Mehr (mehrnews.com), Khabaronline (khabaronline.ir), Hamshahri (hamshahrionline.ir), Tabnak (tabnak.ir), Entekhab (entekhab.ir), Asriran (asriran.com), Zoomit (zoomit.ir), Digiato (digiato.com), Varzesh3 (varzesh3.com) and Khabarvarzeshi (khabarvarzeshi.com). Persian text. Each source has a `group`: `news`, `tech` or `sports`.
- **Install:** `uvx iran-news-mcp` or `claude mcp add iran-news -- uvx iran-news-mcp`. Transport: stdio. Needs [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python 3.10+).
- **Auth:** none. Optional `IRAN_NEWS_MCP_PROXY` (HTTP proxy URL, or a comma-separated list); system proxy settings are ignored. All sources answer from a direct Iranian connection.
- **Access:** read-only. No login or posting, so no confirmation is needed before calling any tool.
- **Tools:** 6: `nw_list_sources`, `nw_latest`, `nw_search`, `nw_latest_all`, `nw_tech_news`, `nw_article`. Start with `nw_list_sources` for valid source ids and category slugs; for any technology question start with `nw_tech_news`.
- **Use when:** the user wants current Iranian headlines, a news overview, recent coverage of a keyword, or the full text of a story.
- **Do not use when:** an archive is needed (only what is in the current feeds, 10 to 300 stories per feed, is searchable).
- **Output:** compact JSON. Times are UTC ISO strings (Tehran is UTC+3:30); summaries are plain text cut to 200 characters (80 in `nw_latest_all`). Null and empty fields are omitted. Replies stay under ~15 KB: `limit` is capped at 15 and `per_source` at 2; `nw_tech_news` is the exception (summaries up to 300 characters, `limit` up to 30, up to ~35 KB). A failing source is listed under `errors` while the others still answer. `nw_latest` sets `stale: true` when a feed's newest story is over 3 days old. Feeds are cached for 3 minutes.
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
| `nw_list_sources` | The 10 sources with their `group` and category slugs. |
| `nw_latest` | Newest headlines of one source, optionally one category (`source`, `category`, `limit` 1-15). |
| `nw_search` | Keyword search over the current feeds of several sources (`query`, `sources`, `category`, `limit` 1-15). |
| `nw_latest_all` | Newest headlines from every source merged by time (`sources`, `category`, `per_source` 1-2). |
| `nw_tech_news` | Technology news, Digiato by default read several feed pages deep, optionally Zoomit (`topic`, `category`, `limit` 1-30, `source` digiato / zoomit / both); summaries up to 300 characters, `scanned` shows search depth. |
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
| `entekhab` | Entekhab | 11 | one per category (up to 100 items) |
| `asriran` | Asriran | 11 | one per category (up to 100 items) |
| `varzesh3` | Varzesh3 (sports) | 1 (`sports`) | one feed (40 items) |
| `khabarvarzeshi` | Khabarvarzeshi (sports) | 1 (`sports`) | one feed (30 items) |

Common slugs shared by most sources: `politics`, `economy`, `society`, `culture`, `world`, `sports`, `science`, `provinces`, `photo`. The sites offer more sub-category feeds than listed here; see the API map.

## FAQ

**Does it work outside Iran?** Yes: the RSS endpoints and article pages answered from a Turkish exit in testing, and from a direct Iranian connection.

**Can I filter by group?** Yes: filter on `group` (`news`, `tech`, `sports`) from `nw_list_sources` and pass the ids as `sources`.

**Why no ISNA or IRNA?** Their article pages (also `/amp/` and `/print/`) answer every non-browser client with an ArvanCloud JavaScript check, from an Iranian connection too, so only headlines would work. They were left out.

## فارسی

سرور MCP غیررسمی و فقط‌خواندنی برای خوراک RSS و صفحه‌های خبر ده منبع خبری: مهر، خبرآنلاین، همشهری، تابناک، انتخاب، عصر ایران، زومیت، دیجیاتو، ورزش سه و خبرورزشی. آخرین عناوین هر منبع و دسته، مرور ترکیبی، جست‌وجوی کلیدواژه در همه منابع و متن کامل خبر.

```bash
claude mcp add iran-news -- uvx iran-news-mcp
```

## License

MIT
