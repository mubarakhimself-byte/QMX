# MQL5 articles

A first-party T1 laptop app. Install with
`Supervisor(home).install(path, trust="first_party")`, then `start("mql5-articles")`.
The control service must listen at `http://127.0.0.1:8766/mcp/`; the supervisor
injects its `qmx/control-token` Credential Manager secret as `QMX_CONTROL_TOKEN`.
This example uses laptop loopback and is not configured for a remote Docker node.

Every 86,400 seconds the job imports up to 500 archived articles, discovers
up to five listing pages, fetches at most 25 new articles, and publishes up to
1,000 pending Library artifacts. It respects robots.txt, its crawl delay and
request rate, and a minimum two-second interval. HTTP validators and upstream
Retry-After windows survive restarts. Successful article bodies are never
fetched again. Redirects are refused. Raw HTML and clean Markdown are
content-addressed blobs; metadata, discovery queue, HTTP cache and publication
outbox live in WAL `app.db`.

## Seed the recovered archive offline

`seed-ids.json` records the 3,057 successful IDs in the recovered
`research/mql5-article-library` worktree catalog. Its 258 failed rows remain
eligible for fetching. The catalog and article files were local archive data,
not tracked files in that branch; the manifest records their catalog checksum.

Copy **only** `catalog.jsonl`, `md/` and `raw/` from that worktree's
`data/mql5-library/` into `<qmx_home>/apps/mql5-articles/data/seed/`.
Do not copy any credential files. The importer validates canonical URLs and
Markdown checksums, normalizes the old Windows newline conversion, and
decompresses the saved HTML. Calling `seed_library(limit=500)` repeatedly
imports all batches without network access. The scheduled job publishes the
imported articles through the control service's `library_save` MCP tool.
If the archive is absent, bundled successful IDs still prevent refetching;
their article content becomes available after the archive is supplied.

`status` reports local counts; `article(article_id=623)` reads local content.
Neither inspection tool fetches anything. A Library save is acknowledged in
the outbox only after success. On retry, source URL and content hash lookup
recover an already persisted artifact after a lost response.

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
