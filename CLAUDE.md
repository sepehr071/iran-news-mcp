# iran-news-mcp

Unofficial, read-only MCP server over the public RSS feeds and article pages of Mehr, Khabaronline, Hamshahri, Tabnak,
Zoomit and Digiato. ISNA and IRNA were dropped on 2026-10-20 (article pages behind a JS challenge, see Quirks). Copies the layout of `../snapp-mcp`; keep them in step. On GitHub (`sepehr071/iran-news-mcp`, public), not yet released (no tag or PyPI release).
API map: `../news-rss/`.

## Layout

- `src/iran_news_mcp/http.py`: the only HTTP code. One shared `httpx.AsyncClient` (`trust_env=False`) on a Chrome-impersonating
  curl_cffi transport, optional proxy from `IRAN_NEWS_MCP_PROXY` (comma list, sticky, next on 403/429/connect error),
  semaphore (4), 100-400 ms jitter, 180 s feed cache (128 entries), GET retries (2) on timeout/network/5xx/429,
  no redirects, host allowlist (https only), 5 MB body cap, `fetch_feed(url) -> bytes`, refuses HTML bodies (bot check
  pages), `fetch_page(url) -> bytes` for article HTML (not cached, follows one redirect to an allowed host, refuses
  the ArvanCloud `__arcsjs` challenge page), `ApiError(ToolError)`, `set_transport()` for tests. No browser fallback.
- `registry.py`: `@tool("Title")` collects tools (+ `clip`). `server.py`: registers them read-only, holds `INSTRUCTIONS`.
- `news.py`: `SOURCES` table (feed URL templates + category slug -> site id/Persian title), `parse_feed` (stdlib
  `xml.etree`, RSS 2.0 and Atom), the four tools `nw_list_sources`, `nw_latest`, `nw_search`, `nw_latest_all`.
- `article.py`: `nw_article`. stdlib `html.parser` finds the body element per site (`_is_body`), drops junk subtrees
  (`SKIP_TAGS`, class tokens in `JUNK`/`JUNK_PREFIX`), one line per block; `_chunks` splits into `CHUNK` (6000) chars.
- `tests/`: `test_news.py`, `test_http.py`, `test_article.py` (synthetic HTML per site layout) offline (MockTransport + trimmed real feeds in `tests/fixtures/<source>.xml`),
  `test_live_news.py` (`@pytest.mark.live`).

## Commands

```bash
uv sync
uv run ruff check . && uv run ruff format --check .
uv run python -m pytest -q            # offline (`uv run pytest` hits a uv trampoline error on this machine)
uv run python -m pytest -m live -q    # real feeds, needs internet only
uv build
```

If a proxy is on (v2rayN at `127.0.0.1:10898`), uv needs `HTTPS_PROXY`/`HTTP_PROXY` to download packages; the server
itself ignores env proxies.

## Rules for changes

- Read-only. Feed URL changes go in `SOURCES`; verify with a real request and update `../news-rss/README.md`.
- New tool: `@tool("Title")` async function, every param `Annotated[..., Field(...)]` with an example, first docstring
  line a complete sentence, unit test, live test, README table row, `INSTRUCTIONS` mention.
- Deps stay `mcp` + `httpx` + `httpx-curl-cffi`/`curl-cffi`. Keep `README.md` tools equal to `list_tools()`.

## Quirks (keep them)

- Feeds work on direct connections and through a Turkish proxy exit (tested both).
- Category feeds: Mehr/Khabaronline/Hamshahri `/rss/tp/<id>` (30 items), Tabnak `/fa/rss/<id>`, Digiato
  `/topic/<parent>/<child>/feed`. Digiato parent topics (`/topic/tech/feed`) return an empty channel: use child topics.
  Zoomit has one feed only (`/feed/`, 300 items); `/mobile/feed/` etc. redirect to an HTML page, so categories are
  filtered client-side on the item `<category domain=".../slug/">`. Tabnak `/fa/rss/all/mostvisited` is an empty channel.
- Dates: RFC 822 everywhere; Tabnak uses `19 Oct 2026 22:42:01 +0330` (no weekday). Output is UTC.
- Photo feeds (Mehr `photo`) have mostly empty descriptions.
- Digiato answered one transient HTTP 503 during testing; the client retries 5xx. It also answered an empty channel once
  for `mobile`; that is an error and is not cached. Leaf feeds `crypto` and `reviews` go days without a story: `nw_latest`
  sets `stale: true` past `STALE_AFTER` (3 days).
- Reply size: `LIMIT_MAX` (15) and `PER_SOURCE_MAX` (3) in `news.py` keep the largest reply under 15 KB; items carry no image.
  Persian is 2 bytes per character, so check bytes (`test_max_limit_replies_stay_under_15kb`) before raising them.
- Article bodies (2026-10-20): Mehr/Khabaronline/Hamshahri (same CMS as ISNA/IRNA) `div[itemprop=articleBody]`,
  Tabnak `#newsMainBody`, Zoomit `<article class="contents">` (inner classes are hashed styled-components; header div
  `row-start-1`, ad label `invisible`), Digiato `.articlePost`. All server-rendered, no JS. ISNA and IRNA (same CMS)
  answer every HTML path (`/news/`, `/amp/`, `/print/`) with an ArvanCloud JSFuck cookie challenge, from a Turkish exit
  and a direct Iranian (MCI) connection, with full Chrome/Safari/Firefox navigation profiles and cookie sessions; their
  RSS is not challenged. Dropped rather than solving the challenge. `fetch_page` still refuses an `__arcsjs` page in case
  another source gets the same protection. Mehr video
  pages hold only a download label, so text under 40 chars counts as no body. JSON-LD `articleBody` exists only on
  Tabnak and Digiato, so it is not used.
- Search is over the current feed contents only; names are matched after Arabic/Persian ي/ك and ZWNJ normalisation.

## Release

Bump `version` in `pyproject.toml` and both versions in `server.json`, commit, then `git tag vX.Y.Z && git push --tags`.
`.github/workflows/publish.yml` tests, publishes to PyPI (trusted publishing), creates the GitHub Release and publishes
to the MCP Registry. Needs the `sepehr071/iran-news-mcp` GitHub repo and a `uv.lock` committed (`uv sync` makes it).
