# MQL5 articles

A first-party T1 laptop app. Install with
`Supervisor(home).install(path, trust="first_party")`, then `start("mql5-articles")`.
It declares no secret and calls no host door. Its only network is `www.mql5.com`.

Every 86,400 seconds the job imports up to 500 archived articles, discovers
up to five listing pages and fetches at most 25 new articles. It then answers
the next unlanded articles, oldest first, as its job's `outputs`. The host lands
each one as its own `mql5-article` Library artifact: title, source URL, Markdown
sha256, published date and Markdown. The crawl respects robots.txt, its crawl
delay and request rate, and a minimum two-second interval. HTTP validators and
upstream Retry-After windows survive restarts. Successful article bodies are
never fetched again. Redirects are refused. A site that cannot be reached is
reported as `crawl_error`, and the archive still lands. Raw HTML and clean
Markdown are content-addressed blobs. Metadata, discovery queue, HTTP cache and
publication outbox live in WAL `app.db`.

## Settings

The instance's `data/config.json` holds two settings. Each has a default.

```json
{"crawl": true, "publish": {"per_run": 200}}
```

`crawl` set to `false` skips the web and only lands what the archive holds.
`publish.per_run` is how many articles one job answers.

## Seed the recovered archive offline

`seed-ids.json` records the 3,057 successful IDs in the recovered
`research/mql5-article-library` worktree catalog. Its 258 failed rows remain
eligible for fetching. The catalog and article files were local archive data,
not tracked files in that branch; the manifest records their catalog checksum.

Copy **only** `catalog.jsonl`, `md/` and `raw/` from that worktree's
`data/mql5-library/` into `<qmx_home>/apps/mql5-articles/data/seed/`.
Do not copy any credential files. The importer validates canonical URLs and
Markdown checksums, normalizes the old Windows newline conversion, and
decompresses the saved HTML. Calling `seed_library(limit=50)` repeatedly
imports all batches without network access. The scheduled job lands the
imported articles through its outputs.
If the archive is absent, bundled successful IDs still prevent refetching;
their article content becomes available after the archive is supplied.

`status` reports local counts; `article(article_id=623)` reads local content.
Neither inspection tool fetches anything. An article answered by a job is
marked sent under the sha256 the host stores its artifact by. At the next
job's start it is marked landed once that artifact is in the app's volume, and
sent again otherwise. The host writes the artifact there only after the Library
holds the item, so an article whose landing failed is sent again. The host never lands the same artifact twice, so a
re-sent article adds no second Library item.

## Optional Firecrawl for the researcher

Firecrawl is a separate paid MCP source, disabled by default. Store its key
in Windows Credential Manager as service `qmx/firecrawl`, username `firecrawl`
(for example, `uv run python -m keyring set qmx/firecrawl firecrawl`).
Use the control service's `settings_put` tool with section `mcp_servers`:

```json
{"firecrawl":{"enabled":true,"url":"https://mcp.firecrawl.dev/v2/mcp","credential_ref":"qmx/firecrawl"}}
```

The equivalent REST route is `PUT /api/settings/mcp_servers`. This replaces
that settings section, so retain other entries when updating it. The next
agent build automatically adds Firecrawl to an AgentSpec named `researcher`,
including a referenced researcher sub-agent. No spec edit is required. The
adapter receives a vault-derived bearer token in memory. Settings accept no
plaintext key, auth header or credential-bearing URL. Disabling the entry
prevents both credential lookup and MCP discovery. No paid calls are made by
the daily scraper or the tests. Settings changes apply on the next build.
