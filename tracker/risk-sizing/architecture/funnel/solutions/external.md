# External connections: brokers, exchanges and data routes

**What this part is.** How QMX reaches markets: cTrader first, CCXT opened beyond reading spot, Hyperliquid looked up and designed, futures routes designed now and switched on later, free order-flow data where it exists (weak spot 7), and the feed keeper that holds live connections on each machine. The node sends orders through these links (`node.md`); the PC host reads through them.

**Verdict: core ports, adapters behind them.** Two ports are core: the venue-client port (orders, positions, fills, reconcile) and the data-route port (bars, quotes, depth, prints, derivatives fields, each with its data level). Adapters plug in behind them. Order adapters run only inside the trading node app; read adapters run on any QMX host.

## His words

- "CCTX only reads crypto spot. Change that. Open it up. Hyperliquid, look it up." (T3:1562)
- "Is it going to place and execute trades via an API?" (T3:1096)
- "Hyperliquid can't ban me from to be trading. I already have accounts there." (T3:903)
- "I don't want to pay for a platform, I'm not gonna lie." (T3:1264) "They need order flow data." (T3:1264)
- "I think I'll use CME, man." (T3:1562) "When the app is live, I'll be spoiled for choice" (T3:1562)
- "Live trading, which I think might have been catered for a bit, not fully, but a bit." (T3:1264)

## 1. What exists today

| Link | State | Where checked |
| --- | --- | --- |
| cTrader Open API: protobuf over TLS on port 5035, Spotware's pinned descriptor, no Spotware SDK; OAuth on This PC; reads (accounts, balance, positions, a spot quote, trendbars, symbol specs), each stamped demo or live; a view-only grant only | BUILT, never run on his folder | G3 §2.1; G4a §2.3 |
| cTrader orders (new, cancel, amend protection, close) in QMN's live client | BUILT, never run | G3 §2.1 |
| cTrader facts: 50 requests a second, 5 for history; no server clock; no dead man's switch; no exchange futures; no public tape, real volume or open interest | venue facts | G3 §2.1 |
| CCXT 4.5.85 pinned; QMX's adapter reads spot only and refuses any contract market; no order code | BUILT (spot reads) | G3 §2.2 |
| CCXT 4.5.85 already contains Hyperliquid with `createOrder`, positions, funding, open interest, order book, leverage, testnet, and a streaming twin | in the pinned package | G4a §2.6 (CHECKED in an installed copy) |
| Hyperliquid, Rithmic, CQG, Tradovate, IBKR | MISSING | G3 §2.3, §2.5 |
| MT5 | a declaration only (Windows, a terminal per account) | G3 §2.4 |
| Databento | a key check only | G3 §2.5 |
| A long-running connection manager on the PC | MISSING (broker reads open one short session per read; WU10 waits on gate G-CT) | research 43 §3.6 |
| Venue-neutral laws: CT-18 capability declaration with a measured profile and an error map, CT-19 commands (five kinds, four outcomes, UNKNOWN never retried), CT-20 events recorded before interpreted, reconcile | BUILT | G3 §3 |
| `VenueClientKind` closed to `ctrader`, `replay`, `conformance` | BUILT (must open) | G3 §5 |

## 2. Harvest: solutions already on disk

| Solution | Where | Fits now? |
| --- | --- | --- |
| One feed keeper per venue and account environment per machine, one subscription per symbol, fanned out to the units on that machine; the PC and the server hold separate grants | research 12; research 43 §3.6; research 38 §3.1, §6 | Yes |
| In-process fan-out is not a limit: about 520,000 deliveries a second, median about 0.5 ms (measured) | research 31 §2.2 via research 43 §3.6 | Yes |
| A connection has two roles, data and execution; a unit binds one data route per data kind and one execution route; proxies are declared | `live-field.md` B052-B055 via research 43 §3.6; funnel6 intent item 3 | Yes |
| Protection at the broker before anything can fail (cTrader has no cancel-on-disconnect); re-place after Hyperliquid's `scheduleCancel` | research 38 §7; research 43 §4 | Yes |
| Rationed order actions in a venue rules row with a live counter | research 32 §4 | Yes (`instruments.md`) |
| Ranked routes for an algorithm: Hyperliquid public feeds; Binance or Bybit through CCXT; Databento CME (199 a month); Rithmic or CQG through a futures broker; IBKR | research 54 §1.5 | Yes, as the option list |
| Sierra Chart, NinjaTrader, Quantower, ATAS, Bookmap, MultiCharts are not data sources for an outside algorithm | research 54 §1.1, §1.5 | Yes |
| Every API speaks a wire protocol any language can use; QML stays Python with an adapter per venue | research 54 §2 | Yes |
| A cheaper first step toward futures: CME data through a data-only route as a declared signal for an index or gold CFD unit | research 38 §8 option B | Yes, as a Could |

## 3. Venue integration: the shapes

### Shape A. One venue-client port in the node with three adapters: cTrader (kept), CCXT (new, covering Binance, Bybit and Hyperliquid), and futures placeholders (recommended)

- **What.** The node's `VenueClientKind` opens to `ccxt`; a CCXT adapter maps the five command kinds onto CCXT's unified calls (`create_order`, `cancel_order`, `edit_order`, `fetch_positions`, `fetch_my_trades`) and CCXT's streaming calls (`watch_trades`, `watch_order_book`, `watch_orders`), behind the same capability declaration, error map and reconcile as cTrader.
- **Reuses.** The CT-18, CT-19, CT-20 laws, reconcile, the pacer, the venue-resident stop rule, the pinned CCXT package.
- **Hard cases.** A venue-specific behaviour CCXT does not cover (handled in the capability declaration: anything unmapped is UNKNOWN plus an alarm, as the law already says); rationed actions (the order-budget gauge); protection semantics differing per venue (the port rule below).
- **Explain.** "QMX talks to every crypto exchange through one library it already has, and to cTrader through its own code. Only the trading node sends orders."

### Shape B. A native client per venue (a Hyperliquid client on its own SDK, and so on)

- **When.** Only where a test shows CCXT falls short (for example Hyperliquid agent-wallet signing or trigger-order details). Party P13 clash; lead's call: CCXT first with a probe on Hyperliquid's testnet, a native client only if the probe fails.

### Shape C. Trade through a platform app (MT5, NinjaTrader)

- **Why not.** Each needs its Windows desktop app running per account (G3 §2.4; research 54 §2), which breaks "a server is a server" on a Linux VPS. MT5 stays a declaration for research and stocks later.

**Pick: Shape A.**

**The protection rule per venue** (a port rule, not unit logic): cTrader places the protective stop with the order; Hyperliquid places a reduce-only trigger order and re-places it after any cancel (its dead man's switch cancels protective orders too); a venue with a per-symbol countdown cancel (Binance futures) may use it only if protective orders survive it.

## 4. Hyperliquid, looked up and designed (his ruling 28)

Facts (research 38 §3.8, CHECKED there against Hyperliquid's docs):

| Fact | What the design does with it |
| --- | --- |
| Linear perps, 1 unit of the underlying, USDC collateral, funding every hour, no expiry; HIP-3 perps on stocks, indices, gold and FX | instrument records per perp, funding as a carry cost in QMB and a reading in the MIS |
| Free live data, no key: trades with taker side, a 20-level book (about every 5.4 s), a 5-level fast book (about every 500 ms), best bid and offer, funding, open interest, mark | the data route for perps; free order flow (§5) |
| Trading keys are agent wallets: trade only, cannot withdraw, expire within 180 days; one per trading process recommended | the node holds one agent wallet per trading machine; its expiry date is on the passport with a renewal card before it lapses |
| Nonces must lie within a window around block time | the node checks its clock before signing; a clock past the halt band blocks new entries (`devops-and-clocks.md`) |
| `scheduleCancel` cancels all open orders at a set time, at most 10 triggers a day | never relied on; protection re-placed after any cancel |
| Per-address action budget (1 action per USDC traded since opening plus 10,000 at start; 1 per 10 s when limited); per-IP limits (10 websockets, 1,000 subscriptions, 2,000 messages a minute) | the order-budget gauge in the market journal; the feed keeper respects the per-IP limits |
| Above 1,000 open orders, new reduce-only and trigger orders are rejected | the node keeps open orders under a margin of that cap, so protection can always be placed |
| TP and SL trigger on mark price | the exit set declares its trigger basis; QMB replays stops on mark price as a what-if |
| A testnet exists | the node's practice placement on Hyperliquid uses the testnet |
| Candles: the last 5,000 only | QMX records its own perps history from the day the route opens |
| Measured from his PC: TCP connect median 31 ms | a kept-open websocket for the feed |

**The link:** reads on the PC through CCXT's Hyperliquid class (positions, funding, open interest, the book) once the spot-only filter lifts; trading only inside the node through the CCXT adapter with an agent wallet; a probe on the testnet before the first live order.

## 5. Order-flow data with no paid platform (weak spot 7)

Algorithms need order-flow **data**, not charts (his words). The facts (research 54): no free real-time CME order flow exists for an outside algorithm; CME charges every live user (about 13.50 to 16 dollars a month per exchange at the cheapest, with a funded futures account); Sierra Chart's data can only be used inside Sierra's own program; free order flow exists only for crypto.

**The solution, in three layers, all behind one data-route port:**

| Layer | Source | Cost | What units get |
| --- | --- | --- | --- |
| Free real order flow | Hyperliquid (perps, and HIP-3 perps on indices, gold and FX), Binance and Bybit through CCXT `watch_trades` | 0 | trades with aggressor side, depth; data level 4 |
| Computed estimates | cTrader ticks and broker depth, computed by QMX itself: tick-rule imbalance, quote pressure, depth imbalance, labelled "broker-side estimate" | 0 | data levels 2 and 3; never called a tape |
| Real futures order flow | a data route he switches on later: Databento (CME, 199 a month, full order book), or Rithmic or CQG through a futures broker (data and orders together) | his money, his choice | data level 4 and order-by-order depth for CME underlyings |

**One internal format** for every route (S114): a trade print (venue time, receive time, price, size, aggressor side, trade id) and a book update (levels with sizes, or orders when the route gives them). The feed keeper normalises into it; QML evidence streams read it; QMB replays it.

**How units consume it:** as readings in the catalogue (delta, cumulative delta, imbalance, absorption) that declare level 4 and their fallback chain (depth imbalance, tick rule, range pressure), each with its expected loss (`dictionary.md` §6). The checker refuses an order-flow block on a market whose level is missing and has no fallback. A futures tape feeding a CFD unit is a declared proxy (S116).

**The futures seam, designed now:** the data-route port with level declarations; a `futures` account type and the futures instrument fields (`instruments.md` §6); venue-client placeholders for Rithmic's R|Protocol (websocket plus protobuf, any language) and CQG's WebAPI (protobuf over websocket), each needing a funded account and a conformance test before production (research 54 §1.2). Nothing in the core assumes which one he picks.

## 6. The feed keeper

- One per (venue, account environment) per machine; one subscription per symbol; fanned out in-process to every unit and the MIS instance on that machine (research 12; research 31).
- Inside the node app on a trading machine (its lifeline must not depend on another app); on his PC the practice node's keeper also serves recording and shadow runs.
- It writes the market journal (per minute: spread, quote count, gaps, depth summary, the order-budget gauge) and records bars and quote ticks for the markets units trade (research 43 §5 recording defaults).
- It refreshes the cTrader token as the one refresher for that grant on that machine.

## 7. CCXT, opened

| Today | Change | Reason, one line |
| --- | --- | --- |
| `_market` refuses any symbol that is not active, spot and non-contract (`adapters.py:330-339`) | allow contract markets for reads (positions, funding, open interest, the book) | his ruling 28; perps and Hyperliquid |
| no order code anywhere in the host | unchanged on the host; a `ccxt` venue client inside the node | only the node sends orders (ruling 135 in code stays) |
| demo rows refused on exchanges with no sandbox | unchanged | already right |
| no websocket streams | the feed keeper uses CCXT's `watch_*` calls (inside the free MIT package) | live data without polling |

## 8. Numbers (starting defaults, all editable)

| Number | Default | Why |
| --- | --- | --- |
| open-order margin under Hyperliquid's 1,000 cap | keep under 900 | room to place protection |
| agent-wallet renewal card | 14 days before expiry | INFERRED |
| order-budget warning | 20% of the venue's remaining budget | INFERRED |
| cTrader request pacing | under 50 a second, 5 for history (the venue's own limits) | G3 §2.1 |
| Hyperliquid per-IP limits | the venue's own (10 websockets, 1,000 subscriptions, 2,000 messages a minute) | providers' limits only |

## 9. Connection points

| From | To | What crosses | Door |
| --- | --- | --- | --- |
| Node | venue (cTrader, CCXT venues) | CT-19 commands; CT-20 events; reconcile reads | venue-client port |
| Feed keeper | units, MIS instance (same machine) | normalised prints, quotes, book updates, bars | in-process fan-out |
| Feed keeper | market journal | per-minute rows | writer library |
| PC host | venues (reads) | balances, positions, specs, history, stamped demo or live | read adapters |
| Data routes | Library market-data store | recorded partitions | downloaders and recorders |

## 10. Open for the architecture step

1. The Hyperliquid testnet probe's pass marks (agent-wallet signing, trigger order placement, cancel and re-place).
2. Duplicate client-order-id behaviour per venue (not covered by any research file, research 43 §8).

## 11. Parked

- A dormant Databento adapter in the first build (party P10; kept as a Could until he pays).
- IBKR (a manual weekly login; awkward on a server) and TopstepX (forbids orders from a server).
- MT5 live units (a Windows trading host).
