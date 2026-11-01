# External connections: venues and data routes

Part C, area 3. How QMX reaches brokers, exchanges and data. Rules: spine AD-308 to AD-311 under Level 0 AD-8, AD-9, AD-41. Shapes: `CONTRACTS.md` §6 and §9.

His words: "CCTX only reads crypto spot. Change that. Open it up. Hyperliquid, look it up." (T3:1562); "I don't want to pay for a platform, I'm not gonna lie." (T3:1264); "They need order flow data." (T3:1264); "When the app is live, I'll be spoiled for choice" (T3:1562).

**Verdict: core ports, adapters behind them.** Order adapters run only inside the node app; read adapters run on any host.

## 1. What exists

| Link | State | Where (CHECKED) |
| --- | --- | --- |
| cTrader Open API, protobuf over TLS on 5035, pinned descriptor | BUILT | `packages/qmf-venue/src/qmf/venue/connection.py:13-17`; `qmx_broker/protocol/openapi-91.pb` |
| cTrader orders (new, cancel, amend protection, close) in the node's client | BUILT, never run | `qmn/src/qmn/venue/live.py:1-35`; `encode.py:50-69` |
| `clientOrderId` written; `label` not written | BUILT | `encode.py:598` |
| CCXT 4.5.85 with Hyperliquid (orders, positions, funding, open interest, book, leverage, trigger and reduce-only orders, sandbox) | in the pinned package | Level 0 `blast-radius.md` item 9 |
| CCXT read adapter: spot only | BUILT | `qmx_broker/adapters.py:330-339` |
| Venue kinds closed to `ctrader`, `replay`, `conformance` | BUILT | `qmn/src/qmn/venue/port.py:40-45` |
| Databento key check only; MT5 a declaration | BUILT | `providers/databento.py:1-59`; `adapters.py:59-72` |

## 2. cTrader

- Facts (help.ctrader.com, CHECKED): 50 requests a second, 5 for history; heartbeat every 10 s; no server clock; no cancel-on-disconnect; access token about 30 days, refresh token never expires; a refresh invalidates the old token's sessions; `label` up to 100 characters, `clientOrderId` up to 50, `comment` up to 512; absolute `stopLoss` is not supported on market orders, `relativeStopLoss` is.
- Tags: `clientOrderId` = `q<tag>-<ULID>` (36 characters); `label` = `qmx:<tag>:<unit tag>`; the encoder refuses a value past the venue's length (a typed refusal, never a truncation).
- History: trendbars by period with paging; ticks one side per request, one week per request, 5 a second; the history adapter pages by those limits; retention per broker is measured once on demo and stored on the venue record (EX-04).
- The broker switching the Open API off arrives as an account event or an authorisation failure; it is a venue state with its reason (EX-05).
- Server region: IC Markets' cTrader servers sit in Equinix LD5, London (icmarkets.com trading-servers page, CHECKED); a London VPS is the default region for a cTrader node.

**Demo probes, slice C-15 (owed; need his demo sign-in, ruling 37).** Pass marks: a market order with `label` and `relativeStopLoss` fills and its position's trade data carries the same `label`; a partial close keeps the label on the remainder; a second order with the same `clientOrderId` is either refused by cTrader or accepted (the probe records which; the design reads open orders before any resend either way); reconcile attributes the test position as mine; the network-cut drill (TN-01): the socket closed right after a send leaves exactly one position after reconnect and no resend; the refresh drill (TN-05): a forced grant refresh stores the new grant before discarding the old, the session comes back ready, and a second refresher is refused. Each mark is a script under `qmn/probes/ctrader_demo/` that prints PASS or FAIL per line.

## 3. CCXT and Hyperliquid

The `ccxt` venue client maps CT-19 onto CCXT's unified calls.

| CT-19 kind | CCXT call (Hyperliquid) | Notes |
| --- | --- | --- |
| `place_order` | `create_order` with `clientOrderId` (cloid, 16 bytes, tag first) | entry first; protection after the fill (spine AD-308) |
| protection after a fill | `create_order` with `params = {stopLoss: {triggerPrice, type: market}, grouping: "positionTpsl"}`, which CCXT 4.5.85 sends as a whole-position stop of size 0 (`ccxt/hyperliquid.py:1576-1579`, `:2254-2262`, CHECKED in the pinned package) | follows partial fills |
| `amend_protection` | `edit_order` on the stop trigger, or cancel and place | risk-non-increasing only |
| `cancel_order` | `cancel_order` by order id or cloid | |
| `close_position` | `create_order` reduce-only IOC for the position size | |
| `close_all` | reduce-only IOC per position in scope | never `scheduleCancel` |
| observations | `watch_orders`, `watch_my_trades`, `watch_positions` (ccxt.pro) | recorded before interpreted |
| reconcile | `fetch_open_orders`, `fetch_positions`, `fetch_my_trades` | attribution by cloid on orders; the account record owns positions |

- Keys: one agent wallet per trading process; it can trade, cannot withdraw, and expires within 180 days (Hyperliquid docs, research 38 §3.8, CHECKED there). He approves it on Hyperliquid's own page; its key enters on the trading machine in the setup window; its expiry is on the passport; a renewal card shows 14 days ahead (EX-10).
- Nonces must lie within a window around block time, so the node checks its clock band before signing (CK-09).
- Limits are the venue's: per IP 10 websockets, 1,000 subscriptions, 2,000 messages a minute; an address action budget (1 per USDC traded plus 10,000 at start); the pacer keeps a share for cancels and stops (TN-22).
- Positions net per coin: one unit per coin per subaccount (spine AD-308); subaccounts trade through the agent wallet with the vault address field.
- Triggers fire on mark price; the venue record says so, and QMB replays stops on mark price as a what-if.
- History: candles only the last 5,000; the recorder starts with the link (EX-09).

**Testnet probe, slice C-16 (owed; needs his testnet agent wallet).** Pass marks: an agent-wallet-signed limit and IOC order fill on testnet; a reduce-only `positionTpsl` stop trigger is accepted, shows in `fetch_open_orders`, resizes after a second fill and survives the node's process being killed (read back from a fresh process); `cancel_order` by cloid works; a fill event arrives on `watch_my_trades` within 2 s. A failed mark that CCXT cannot meet is the trigger for a native client (Level 0 LC-26), and only for that mark.

Binance and Bybit (a Should): the same client; Binance's per-symbol countdown cancel is used only if protective orders survive it, which its probe must show; Bybit's disconnect-cancel is institutional only and not used.

## 4. Data routes and order flow

The data-route port declares, per venue and instrument, the levels it offers with their three splits (volume kind, depth grade, the clock of each derivatives field) and licence, and serves subscribe and history in the internal format (`CONTRACTS.md` §6).

| Layer | Source | Level | Label |
| --- | --- | --- | --- |
| Real tape, free | Hyperliquid (perps and HIP-3), Binance, Bybit through CCXT streams | 4 | `tape` |
| Broker-side estimates | cTrader ticks and depth, computed by reading blocks (tick-rule imbalance, quote pressure, depth imbalance) | 2, 3 | `estimate: broker-side` |
| Real futures order flow | a route he switches on later (Databento CME, Rithmic or CQG through a futures broker) | 4, MBO | `tape` |
| The placeholder now | a `file` adapter reading trades and MBP-10 in Databento's published schemas from `data/routes/<route>/` | 4 when files exist | `tape (files)` |

With no files the level is absent, the checker's layer D sees it, and units take their declared fallbacks. Sierra Chart, NinjaTrader, Quantower, ATAS, Bookmap and MultiCharts are not data sources for an outside algorithm (research 54 §1.1, CHECKED there), so none is designed in.

A futures tape read by a CFD unit is a declared proxy: both series are recorded on one clock and their gap is a reading (EX-15).

## 5. Demo, testnet and live

Demo and live are separate endpoints and separate worlds. Every journal row carries its world; costs are calibrated per world; a demo pass mark never stands in for live calibration (EX-19). Practice on cTrader is a demo account; practice on Hyperliquid is the testnet.

## 6. Declarations without code

- MT5: needs Windows and a terminal per account; its capability record says so; a unit needing MT5 is refused on a Linux node (EX-21).
- Rithmic R|Protocol and CQG WebAPI: protobuf over WebSocket, any language; each needs a funded account and a conformance test before production; declared, not built.
- IBKR: a manual weekly login; TopstepX: no orders from a server. Their records declare it and setup refuses an unattended node on them (EX-16).

## 7. Reads on This PC

- The CCXT read adapter opens to contract markets: positions, funding, open interest, the book (`adapters.py:330-339` changed; it stays read-only, Level 0 `blast-radius.md` item 8).
- The cTrader read app keeps its view-only grant under the host (`qmx/token/ctrader-app`), separate from every trading app, so a refresh never logs out a node.

## 8. Settings

| Setting | Default | Origin |
| --- | --- | --- |
| cTrader pacing | under 50 a second, 5 for history | the venue's limits |
| `open_orders_margin` | 900 | `external.md` §8 |
| `agent_wallet_renewal_days` | 14 | INFERRED |
| `order_budget_warn` | 20% of the venue's remaining budget | INFERRED |
| `history_page` (cTrader ticks) | one week, one side | the venue's limit |
| `rtt_samples` at setup | 8 | research 38 measurement |

## 9. Checks

| Must not break | Check |
| --- | --- |
| No order call on any host | Level 0 `br8_host_orders.py` reruns on every slice touching `qmx-broker` |
| Encoder length limits | unit tests: a 51-character client order id and a 101-character label are refused |
| The CCXT mapping | conformance tests against a fake exchange object with CCXT's method names; UNKNOWN on an unmapped error |
| Capability re-verification | a test pins that a changed CCXT version string forces re-verification before live |

## 10. Ledger rows, growth seam

- Binds: X-01 to X-07, L-06, C-03, N-04.
- Growth seam: a venue is a capability declaration plus an adapter; a data route is a level declaration plus an adapter; the `file` placeholder is replaced by switching a route on.
