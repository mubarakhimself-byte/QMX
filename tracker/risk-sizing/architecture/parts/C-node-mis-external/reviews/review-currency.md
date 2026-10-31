# Review: currency (is every committed decision checked against reality?)

The first configured `finalize_reviewers` lens, run in sequence by the part's agent. Each named technology and venue behaviour the spine commits to, and how it was checked on 31 Oct 2026.

| Commitment | How checked | Verdict |
| --- | --- | --- |
| cTrader `label` 100, `clientOrderId` 50, `comment` 512; no absolute stop on market orders | help.ctrader.com/open-api/messages (Exa fetch) | current |
| cTrader at IC Markets runs in Equinix LD5, London | icmarkets.com trading-servers pages (Exa) | current |
| Hyperliquid TP/SL triggers on mark price; parent-order children cancelled with a partially filled parent; position TP/SL sized to the whole position | hyperliquid.gitbook.io "Take profit and stop loss orders" (Exa fetch) | current |
| Hyperliquid `positionTpsl` through CCXT | **not checked in the first draft**; the meaning came from a third-party TypeScript SDK comment | finding CU-1 |
| CCXT 4.5.85 includes Hyperliquid orders, positions, trigger and reduce-only orders, sandbox | Level 0 `blast-radius.md` item 9, run offline | current |
| OpenObserve binds 0.0.0.0 with an empty `ZO_HTTP_ADDR` | openobserve `src/main.rs` and its environment reference (Exa) | current |
| Healthchecks.io free plan, 20 checks, alerts on a missing ping, notifies through ntfy | healthchecks.io home, docs and pricing (Exa) | current |
| ntfy publishes by one HTTPS POST; free, open source, self-hostable | ntfy docs and README (Exa) | current |
| keyring's fallback backend raises on every call | the pinned package's `keyring/backends/fail.py` | current; the pin's number missing from the Stack (CU-2) |
| SNTP sources | the spine says "configured sources" without a default; Level 0 AD-43 forbids mixing smeared and unsmeared sources | finding CU-3 |
| Spotware's app review time "about 24 hours" | research 38 §3.1 (forum, 2023; secondary) | kept as a waiting step with no number |

## Findings

| # | Severity | Finding | Fix |
| --- | --- | --- | --- |
| CU-1 | High | The design relies on CCXT passing Hyperliquid's `positionTpsl` grouping for the post-fill stop. Checked in the pinned package now: `ccxt/hyperliquid.py` sends a whole-position TP/SL with grouping `positionTpsl` and size 0 when `params.stopLoss` and `grouping = "positionTpsl"` are given (`:1576-1579`, `:2254-2262`, CCXT 4.5.85) | cite it in AD-308 and `EXTERNAL.md` §3; the testnet probe keeps its marks |
| CU-2 | Low | keyring pin number | 25.7.0 from `qmx-agents/uv.lock` |
| CU-3 | Medium | No default time sources; a builder could pick Google's or AWS's smeared servers beside pool servers | default `0.pool.ntp.org` to `3.pool.ntp.org` on servers and the probe; never Google or AWS time unless all sources are theirs |
