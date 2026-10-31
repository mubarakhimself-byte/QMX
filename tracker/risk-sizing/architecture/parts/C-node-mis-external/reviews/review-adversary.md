# Review: adversary (two slices that obey every AD and still build incompatibly)

The second configured `finalize_reviewers` lens, run in sequence by the part's agent. Each pair below obeys the spine as first drafted and still diverges; each is a hole to close.

| # | Severity | Two builders | How they diverge | Fix |
| --- | --- | --- | --- | --- |
| AV-1 | High | The order-path builder (C-12) and the Hyperliquid client builder (C-16) | both obey "the tag rides the client order id and cloid", but the trace id length is unbounded: a 40-character trace fits cTrader's 50, a UUID text does not, and a 16-byte cloid cannot hold a 26-character ULID plus a tag | fix the trace id as a ULID (26 characters, so `q<tag>-<ULID>` is 36); the cloid is the tag's 5 bytes plus the first 11 bytes of SHA-256 of the ULID; the node journals the cloid with its trace |
| AV-2 | High | The copilot's tool surface and the host route | on This PC the harness serves a running app's operations to chats (`qma/harness/tools.py:538-588`), so the practice node's `kill` reaches the copilot as a tool that asks him (R35), while a server's `kill` is refused to every agent by the route. Two builders read this as two different rules | state it once in AD-302: on This PC the copilot sees the practice node's operations because it runs there, every `manage` one asks him first and the practice node holds demo grants only; a server's node offers agents reads only |
| AV-3 | Medium | The node runtime builder and the `mis` app builder | both stamp a reading with one id at different tiers (AD-313 and AD-314 say tier, the series key does not) | the tier joins the series key (RW-3) |
| AV-4 | Medium | The node link builder and the UI's node routes | the UI calls a reachable node directly; a queued `pause` from an hour ago flushes after his newer `resume` | all `manage` changes through the outbox, in order (RW-4) |
| AV-5 | Medium | The take-over builder and the deploy builder | after `take_over` the old deployments name the old identity, so the deploy preflight refuses them and units stay flat with positions adopted but unmanaged | the take-over re-issues the deployments for the new identity (RW-7) |
| AV-6 | Low | The deploy builder and the route builder | a deployment with many blocks could pass the MCP tool call's practical size and stall past the 20 s inner timeout | a deployment document is at most `deploy_max_bytes` (16 MB, a setting) and refused past it, naming the size |

## Pairs tried and found closed

- Two nodes on one account: the account record's owner, the tag and the attribution verdicts leave no room.
- Two writers on the node's state: `desired` and `observed` have one writer each.
- Two refreshers on one cTrader grant: one grant per trading machine's own app, refreshed only by the node.
- The host and the node both writing the market-data store: the bootstrap refuses the node's writes outside its volume; only the door writes.
