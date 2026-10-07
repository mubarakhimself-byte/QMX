# P19: Research sources (MQL5 scraper app, Firecrawl MCP)

## Goal
QMX keeps feeding its Library with research:
- a scheduled scraper of MQL5 articles, built as a headless mini app
- Firecrawl as an optional paid MCP provider

## Read first
- `rebuild/DESIGN.md` §7 and §11
- Branch `research/mql5-article-library` (existing scraped library and scripts). Inspect it before writing anything new.

## Build
1. **`examples/apps/mql5-articles`:** a headless mini app (P12 format).
   - Schedule: daily.
   - Fetch new articles politely: respect robots.txt and rate limits, only fetch new items, use conditional requests.
   - Store raw HTML plus clean markdown in `blobs/` and metadata in `app.db`.
   - Emit Library artifacts (`library_save`).
   - Seed from the existing library on the branch so nothing is fetched twice.
2. **Firecrawl:** add it as a configurable MCP server entry in settings (API key in Credential Manager `qmx/firecrawl`), off until the operator enables it. Add it to the `researcher` sub-agent's MCP list when enabled.

## Tests
- parsing on saved HTML fixtures
- dedupe against existing items
- the schedule entry is valid
- no network in tests
