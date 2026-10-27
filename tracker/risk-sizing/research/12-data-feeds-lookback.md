# 12: Lookback limits, historical data, the live feed pool, and the market journal

Research for the unit work, 2026-10-27. Read-only; nothing in code or docs was changed.

## How to read this

- **CHECKED** = I read it: a file with its line number, or a web page (URL in §8).
- **INFERRED** = my reasoning from checked facts. Treat it as a proposal.
- Code paths are on `origin/engine/base` (`d82be318`, 26 Oct, the latest merged code) unless marked "plan branch" (`plan/agent-system`, `034abe7e`, which still carries older code).
- Every number in a design proposal is a **default the operator can edit**. Numbers that come from a vendor are that vendor's limits, not ours.
- Not repeated here: instrument mechanics (02), router design (09), connection basics and auth (qma-v2 study 56), storage stack choice (qma-v2 study 53).

---

## 0. The answer in twelve lines

1. **The lookback limit he heard of is QMB's replay reader.** Every step of a replay holds a full copy of all prices so far, so memory grows with the square of the steps. A probe died at 4,320 steps; runs are bounded to **1,000 steps**. With 1-minute bars that is about 17 hours of history per run. CHECKED.
2. **Fix:** each step points into one shared price array, or holds only the window the unit declares it needs. QML already works out that window per unit. This is foundation 2 in 07 ("windowed reader").
3. **No other lookback cap exists.** The docs say "keep all obtainable history" forever. The 12-month seal hides the *newest* year and is not a cap. The other limits are per-request page sizes that QMX loops over. CHECKED.
4. **How far back data really goes** decides "1990". Dukascopy intraday starts in **2003** for FX and gold, **2010-2012** for indices and oil, **2017** for stocks and crypto. Daily bars go back to 1973 (EURUSD), 1980 (US 500) and 1999 (gold). A 1990 test runs on daily bars, or on paid intraday data from 2008-2010. CHECKED.
5. **Dukascopy changed under QMX's feet.** Its old `bi5` file feed (the format QMX decodes) broke in July 2026. The new feed sits behind an AWS bot wall that challenges non-browser clients, so dukascopy-node now drives a hidden Chromium. A challenged hour can come back **empty without an error**. CHECKED.
6. **Dukascopy's website terms** forbid bots and "constructing a database" without written consent. QMX's personal-use stance (DEC-0170) is the same posture every dukascopy-node user takes. He should know it; it is not a blocker. CHECKED (terms) / INFERRED (posture).
7. **Free alternatives:** HistData (FX ticks with bid and ask; files before June 2009 have bid and ask swapped), Binance and Bybit bulk files (crypto trades and bars), broker history (cTrader, MT5). TrueFX stopped publishing in January 2026. **Paid:** Databento (CME from June 2010; $199/month Standard or pay per GB), FirstRate (1-minute bars from 2008-2010; stocks from 2000), Tardis (crypto perps tick data and books, including Hyperliquid since Oct 2024). CHECKED.
8. **Feed pool:** one feed keeper per broker connection subscribes **once per symbol** and fans out to every unit on that machine over a local bus. The router reads the bus like any unit. If the router dies, units keep their feed. CHECKED limits / INFERRED design.
9. **cTrader allows about two connections per app** (one demo, one live; "unlimited accounts" each, no symbol cap). So the PC and the node must not both open a live connection under one app. One machine holds a lease on the connection; the other reads its pool. CHECKED / INFERRED.
10. **Costs and session facts live in one market journal** per (broker, account type, instrument, time bucket). It holds spread, swap, commission, funding, session state, and slippage folded in nightly from all units' fills. A unit journal keeps only its own orders and fills, plus a key into the market journal. CHECKED ruling / INFERRED layout.
11. **Storage is per instrument, not per unit.** 200 units on 60 instruments: about 14 GB of 1-minute bars back to 2003, about 180 GB of ticks, about 15 GB a year of live ticks per broker, about 1 GB a year of 1-minute market journal. INFERRED from checked sizes.
12. **Local first, honestly:** the PC had 12 GB free on C: and 8.3 GB on D: when the data inventory read it. It can hold the bars for the instruments in use, not the whole tick archive. The tick archive lives on the server and in the bucket; the PC caches the months a run needs. CHECKED (disk) / INFERRED.

---

## 1. Every lookback-style limit in docs and code

The ruling: no limit on how far back a unit or backtest looks. Post-COVID is a default, never a cap (STATE.md:42-43).

| # | Limit | Where (CHECKED) | Is it a lookback cap? | What removing or changing it touches |
|---|---|---|---|---|
| 1 | **QMB replay reader is quadratic.** `_materialise_quotes` appends each quote to `cumulative` and stores `"samples": list(cumulative)` as the frame for every step. A month of 1-minute steps = about 1.0e9 sample entries, about 16 GB. 744 steps peaked near 1 GB; 4,320 steps died with `MemoryError`. | `qmb/src/qmb/host/replay.py:475-572` (copy at :569, frame at :572); probe `scripts/probes/data/p_qmbread.py:17-24, 218-224`; `D:\QMX-worktrees\qma-ship\data\BACKLOG.md:26`; `tracker/qma-v2/WRAPUP-PLAN.md:443` ("Every live lane uses a replay of at most 1,000 steps"); `tracker/qma-v2/QMB-BACKTEST-DOOR-HANDOFF.md:39` | **Yes, in practice.** 1,000 steps = about 17 hours of 1-minute bars, or about 6 weeks of hourly bars, per run. This is almost certainly what he heard. | (a) Build frames as an end offset into one shared, immutable series instead of a copy: the same answers in linear memory. (b) Or keep only the unit's declared window: QML already derives a warm-up horizon from the producer chain (`qml/src/qml/footprint/__init__.py:1-8`; `warm_up` and `warm_up_time_bound` in `qml/src/qml/footprint/template.py:132, 140`). Touches `qml.protocol.MappingReadSurface` (a QML contract type), both entry points in `replay.py` (`read_recorded_replay_source` :244, `read_typed_replay_source` :608), and the replay-equality check in `qmb/src/qmb/host/replay_execution.py:824-828`, which compares frames. Re-run P-QMBREAD with the 1,000 bound lifted. 07 foundation 2. |
| 2 | **Holdout seal, newest 12 months.** `historical_holdout_months = 12`, "No-peek seal, not retention (data is kept regardless)". The door's default is 12 when settings name none. | `C:\Users\Mubarak\Desktop\QMX\docs\registry\variables.yaml:253-262`; `qmx-agents/packages/qmx-host/src/qmx_host/market_data.py:76-77`; `packages/qmf-data/src/qmf/data/seal.py:3-17` | **No.** It hides the newest year, not the oldest. | Keep it. It is already configurable. Note: with a post-COVID default (March 2020 to now, about 80 months), the seal takes 12 of them. |
| 3 | **Raw history kept forever.** `raw_history_retention_policy = all-obtainable-history`. | `docs/registry/variables.yaml:264-273` (DEC-0118) | No. This is the "unbounded" rule already written down. | Nothing. Cite it when someone proposes a retention cap. |
| 4 | **Dukascopy adapter takes one day per call** and refuses a "complete-corpus" download. | `packages/qmf-data/src/qmf/data/dukascopy.py:93-95` (`FACTORY_MAX_WINDOW_NS = 24h`), :231 (`refuse_complete_corpus_download`), :664, :750 | **No.** It sizes one call; a downloader loops over days, which is how partitions are stored anyway. | Keep the per-call size. The "refuse complete corpus" wording (FM-5, DEC-0051) dates from the factory era and reads like a ban on full-history downloads; reword it in the doc pass so nobody cites it against the ruling. INFERRED. |
| 5 | **Broker bar read capped at 1,000 bars.** | Plan branch: `qmx-agents/packages/qmx-broker/src/qmx_broker/service.py:152-155`. engine/base: **already removed**: `service.py:188-195` now says "no limit for every bar" and pages. | Was a cap; now gone. | Nothing. The `<= 2147483646000` bound there is January 2038, a timestamp ceiling, not a capacity (comment at :189). |
| 6 | **cTrader ticks: one week per request.** | `packages/qmf-venue/src/qmf/venue/ctrader.py:139, 610`; ctrader docs | No. It is the venue's own page size. | Keep; page with `hasMore`. |
| 7 | **Agent tools page results.** `read_bars` returns 50 rows per page with a cursor; the door returns a handle past 5,000 rows. | Plan branch `qmx-agents/packages/qmx-tools/src/qmx_tools/registry.py:38-58`; `market_data.py:70-71` (`HANDLE_ROWS`) | No. Paging keeps chat context small. | Nothing. |
| 8 | **MIS regime corpus reads M5 bars only.** | `qmn/src/qmn/mis/regime_corpus.py:694` | No (a bar size, not a depth). | The router rework (09) decides MIS inputs; flag only. |
| 9 | **"Light" live-path producers must declare a bounded lookback window.** Unbounded ones are classed "heavy", not refused. | `docs/lenses/performance/budgets.md:48`; `docs/contracts/ct-17-causal-structure.yaml:31` | No. A live-speed label. | Nothing. A unit may look back as far as it likes; it just isn't "light". |
| 10 | **Venue history caps** (outside QMX): Hyperliquid candles = last 5,000 per interval; MT5 limited by the terminal's "Max. bars in chart" setting. | 02 §8.3; study 56 §4; study 53 §3.2 | Yes, but the venue's own. | Record our own history from day one (02 already says so). Set MT5's "Max. bars in chart" to Unlimited on any terminal used as a source. INFERRED. |
| 11 | **"Post-COVID window"** in the seeds. | `tracker/risk-sizing/seeds.md:37` | No. An example for "hypothetical markets". | Possibly the other half of what he heard. It is now a default (STATE.md:43). |
| 12 | **What is on disk today:** the old Dukascopy ticks cover EURUSD and USDJPY, 2003-2026, about 10 GB. | `tracker/qma-v2/research/methodology/54-data-round-funnel.md:243` (I-001); `55-data-round-architecture.md:381` (DR0) | A coverage limit, not a rule. | Downloads for more instruments (data round DR work). |

Not a lookback limit: `reconciliation_lookback` (`variables.yaml:1069`) is the node's window for resolving an order with an unknown outcome.

**Default to set (INFERRED):** a `lookback_default_start` setting per run kind, default `2020-03-01` (post-COVID), with `earliest` = whatever the dataset card says exists. No `lookback_max`. A request before the data starts gets a plain answer ("no 1-minute EURUSD before 2003-05-04 from Dukascopy; daily bars exist from 1973"), never a refusal by rule.

---

## 2. Historical data per instrument class

### 2.1 Dukascopy through dukascopy-node

**Coverage (CHECKED, dukascopy-node instrument pages):**

| Instrument | Ticks and 1-minute from | Daily from |
|---|---|---|
| EURUSD | 2003-05-04 21:00 UTC | 1973-03-01 |
| Gold (XAUUSD) | 2003-05-05 | 1999-06-03 |
| US 500 index CFD | ticks 2012-01-16; 1-minute 2011-09-19 | 1980-01-02 |
| Brent oil CFD | 2010-12-02 | 2006-11-17 |
| Apple stock CFD | 2017-01-26 | 2017-01-26 |
| BTCUSD | 2017-05-07 | 2017-05-07 |

- About 1,500 instruments: 290 FX, 51 FX metals, 546 US stocks, 104 UK stocks, 60 US ETFs, a few commodities and bonds, 29 crypto. CHECKED (README).
- Some listing rows say "Jan 1, 2000" for instruments that cannot be that old (for example Uniswap). Read the per-instrument page, not the summary table. CHECKED (both pages) / INFERRED (that the summary is a placeholder).

**Tick vs bar, and sides (CHECKED, config docs):**
- Ticks carry both sides in one row: time, ask, bid, ask volume, bid volume.
- Bars (`s1` up to `mn1`) are **one side per run**: `priceType` defaults to `bid`. Bid and ask bars are two downloads. QMX already refuses a half pair (study 57; `p_qmbread.py:13-14`).
- Volumes default to "millions" units and are Dukascopy's own liquidity, not market volume. INFERRED for the second half.

**Defaults that hide problems (CHECKED, config docs):**
- `ignoreFlats: true` drops bars with zero volume ("mainly weekends or bank holidays"). It also hides a real outage, so a gap check cannot tell the two apart afterwards.
- `retryCount: 0` and `retryOnEmpty: false` by default. An empty hour is accepted as "no ticks".
- `utcOffset: 0` (UTC). Good; keep it.
- `batchSize: 10`, `pauseBetweenBatchesMs: 1000`.

**Changes in 2026 (CHECKED, GitHub issues):**
- **July 2026:** the old file feed (`datafeed.dukascopy.com/.../10h_ticks.bi5`) stopped answering. dukascopy-node 1.49.0 moved to a new JSON feed (issue #254).
- **October 2026:** that feed (`jetta.dukascopy.com/v1/ticks/USD-CAD/2026/10/16/19`) sits behind an AWS WAF. Node, Python, curl and wget get `HTTP 202` with `x-amzn-waf-action: challenge` and an empty body. A headed Chrome got 4,260 ticks for the same hour. With `retryCount: 0`, the library returned **zero rows without an error** (issue #261, closed 23 Oct). The README now says downloads "may require Chromium or Google Chrome".
- **What this means for QMX (INFERRED):** QMX's own adapter decodes `bi5` (`packages/qmf-data/src/qmf/data/dukascopy.py:297`), so its live-download path likely points at a dead feed. QMX also reads dukascopy-node CSV (`dukascopy.py:355-409`). That is the working path, but only with a browser on the machine. The 10 GB of old `bi5` ticks on disk are now irreplaceable at that cost: back them up (DR0 already plans this).
- Smaller bugs: an end time not on the hour drops the last hour's ticks (#193); `-to now` can write an empty file (#213). Data for today or yesterday may be missing until Dukascopy uploads it (wiki, "empty responses").

**Licence and terms (CHECKED):**
- Website terms: "solely for your own non-commercial use"; "may not be used to construct a database of any kind"; and (quoted by openbrokerapi.com) no "scraper, robot, bot … to access, acquire, copy … any data" without written consent.
- QMX's code stamps every Dukascopy window `internal-only` (DEC-0170, `dukascopy.py:88`).
- INFERRED: personal, non-commercial backtesting is the use every dukascopy-node user makes, and the WAF is Dukascopy saying it notices. Keep the data private, never redistribute it, keep the `licence` tag on every partition, and download slowly. **For him to know, not to decide now.**

**Cleanliness (mixed evidence):**
- A tick-data vendor that defaults to Dukascopy calls it "clean data (no gaps/spikes)" with neither the best spreads nor the densest ticks. CHECKED (eareview.net).
- An older StrategyQuant forum thread (about 11 years old) says it is "filled with gaps, and on occasion, massive tick spikes". CHECKED.
- `s1` bars have "gaps", but those are seconds with no tick, not missing data (issue #133). INFERRED.
- Dukascopy prices are Dukascopy's own feed, not his broker's. Spreads, index CFD prices and swap differ by broker. INFERRED. The market journal (§4) measures his broker's real numbers so QMB can correct for this.
- **Verdict (INFERRED):** good enough as the default deep history. Never trust it without the §3 checks, and never as his broker's costs.

### 2.2 Sources by class

"Bid/ask" means quote data (what CFD bots trade on). "Trades" means real executions. Costs are as of October 2026.

| Class | Free, deep | Free, own broker | Paid | Notes |
|---|---|---|---|---|
| **FX** | Dukascopy ticks and bars from 2003, daily from 1973. HistData: FX ticks with bid and ask plus 1-minute bars, one file per pair per month, each with a gap report; **files before June 2009 have bid and ask swapped**; stamps follow New York time *with* daylight saving, although its FAQ says otherwise (CHECKED, histdata.com; exactick.com). TrueFX: free with registration; **stopped publishing new data in January 2026** (CHECKED, soft4fx.com, a vendor statement). | cTrader: ticks (bid or ask, one week per request) and trendbars. MT5: bars and ticks from the terminal, capped by "Max. bars in chart". | FirstRate "FX Majors": 74 tickers, 1-minute and up, 2009/2010 to now (CHECKED); price not read. | Lookback before 2003 is daily only, unless a paid tick vendor covers it (not verified). |
| **Metals** | Dukascopy gold from 2003 (daily 1999). HistData has XAUUSD (CHECKED, exactick). | Same as FX. | Databento COMEX futures from June 2010 as a real-volume proxy (02 §3.2). | |
| **Index CFDs** | Dukascopy indices from 2011-2012 intraday, daily from 1980 (US 500). | cTrader, MT5. | Databento CME (ES, NQ…) from June 2010. FirstRate US indices 1-minute from 2008 (CHECKED). | The CFD's real volume and tape live in the futures (02 §4.2). |
| **Commodity CFDs** | Dukascopy energies and softs from 2010 or 2017 (Brent 2010-12; coffee 2017-12). | cTrader, MT5. | Databento NYMEX and CBOT; FirstRate futures from 2008. | IC's futures-based CFDs expire; roll history is not in any CFD feed (02 §5). |
| **Stock CFDs** | Dukascopy: 546 US and many EU and Asian stocks from 2017. | MT5 only at IC (02 §6). | FirstRate stocks 1-minute from 2000, split- and dividend-adjusted, includes delisted names (CHECKED). Massive (ex-Polygon) $29-$199/month (study 56 §7). Alpaca free tier history from 2016 (study 56). | Check whether a source's prices are adjusted for splits and dividends; a CFD is not (§3 item 10). |
| **Futures (CME)** | None deep and free. | Rithmic ticks since 2011, 40 GB a week (study 56 §1). | **Databento** GLBX.MDP3 from **2010-06-06**: before 2017-05-21 the finest level is MBP-10 and timestamps carry `F_BAD_TS_RECV`. Pay per GB for history, or Standard **$199/month** from 22 June 2026: 16+ years of 1-second to 1-day bars, last 12 months of L1 and trades, last month of L2 and L3, personal use on up to 2 devices. Plus $1,750 and Unlimited $4,500 a month. (CHECKED.) FirstRate 1-minute from 2008, continuous (unadjusted, absolute- and ratio-adjusted) and single contracts; $99.95/year for updates on one ticker (CHECKED). | Real volume, depth and tape: the best order-flow data (02 §7). |
| **Crypto perps** | Binance USD-M and COIN-M bulk files: klines from 1 second, trades, aggTrades, daily and monthly zips with a SHA-256 `.CHECKSUM`; archived files may be replaced (CHECKED). Bybit: daily trade CSVs per contract at `public.bybit.com/trading/` (CHECKED listing); L2 files on its history page need a browser (CHECKED, a third-party downloader automates it). Hyperliquid: candles = last 5,000 only; S3 archive of hourly L2 snapshots and asset contexts, requester pays (02 §8.3). | The exchange is the broker. | **Tardis.dev:** tick trades, L2 updates, book snapshots, funding, open interest and liquidations for 30+ perp venues. **Hyperliquid since 2024-10-29**; HIP-3 perps since 2025-12-02. The first day of every month is free. Yearly plans include 4 years of history; Business includes everything since 2019-03-30 (CHECKED); price not read. | Funding history per venue: Hyperliquid `fundingHistory` (02 §8.3); Binance funding files likely (INFERRED, not opened). |
| **Crypto spot** | Binance spot bulk files. **Spot timestamps are in microseconds from 1 Jan 2025**, milliseconds before (CHECKED). | CCXT top-up of recent bars (study 53). | Tardis spot; FirstRate crypto 1-minute (CHECKED bundle list). | |

**The 1990 question, plainly (INFERRED from the table):** QMX should accept any start date. Intraday data before about 2003 (FX) or 2008-2010 (futures, indices) mostly does not exist in the free or cheap sources found. A unit asking for 1990 gets daily bars, or a clear "no 1-minute data before X". When a series is stitched from two sources (Dukascopy daily before 2003, then ticks), the dataset card must record the seam, because the two feeds differ.

---

## 3. Data-quality checklist (run on every dataset, every source)

Run it when a partition is written, and store the result on the dataset card. Each check returns `pass`, `warn` or `fail`, with counts. Every threshold is a setting, and defaults come from the data itself (rolling statistics), not invented constants. INFERRED design; items marked CHECKED come from sources above.

1. **Completeness by the clock.** Count rows per hour against the instrument's session calendar. An hour that should trade but has zero rows is a gap, unless the source says "not yet uploaded" (Dukascopy's recent days). Never let `ignoreFlats` decide this; download flats on and mark sessions ourselves. Today QMX's gap check knows only `forex-17NY` and 24/7 (`qmb/src/qmb/data/gap_check.py:43-75`, 02 §10). Per-symbol calendars are needed.
2. **Silent empties.** An hour with zero rows from a call that "succeeded" is a fetch failure until proven otherwise: retry, then compare to a second source (CHECKED: dukascopy-node #261).
3. **Gaps inside an hour.** Largest gap between ticks, against that hour-of-week's usual gap (HistData publishes this per file; CHECKED).
4. **Spikes.** A price more than `k` rolling median deviations away that reverts within `n` ticks. Default `k` and `n` come from the instrument's own history. Flag; never delete silently. A spike can be real (SNB 2015).
5. **Crossed or negative spreads.** Ask below bid. Catches HistData before June 2009 (CHECKED) and swapped columns in any import.
6. **Spread outliers.** Spread against the usual level for that hour of the week. Rollover at 17:00 New York is a real widening, not an error (02 §2.5).
7. **Duplicates.** Same timestamp and same prices, repeated. Also the same partition fetched twice must give the same fingerprint (study 53: one partition, one fingerprint).
8. **Ordering.** Timestamps never go backwards. Same-millisecond events keep file order (Tardis documents row order as the tie-breaker; CHECKED).
9. **Time zone and daylight saving.** Check that the Friday close and Sunday open land where the venue says, in UTC, in summer and in winter (CHECKED method: exactick checked HistData this way). Check units: Binance spot changed from milliseconds to microseconds in 2025 (CHECKED).
10. **Corporate actions (stocks).** Splits and dividends: is the source adjusted? A stock CFD trades unadjusted and gets a cash adjustment, so backtests on adjusted prices misstate gaps and costs. Record `adjusted: yes | no` on the card. INFERRED.
11. **Futures rolls.** Continuous series must say how they were built (unadjusted, absolute, ratio; FirstRate offers all three; CHECKED). A unit trading the real contract needs per-contract data and roll dates.
12. **Weekend and holiday bars.** Bars on a closed day mean a time-zone shift or synthetic flats. Crypto has no closed days; FX CFDs do.
13. **Bar vs tick agreement.** Bars rebuilt from ticks should match the vendor's bars (high, low, close) within one tick size. Catches a missing hour inside a bar.
14. **Side pairing.** Bid and ask bar series cover the same months and the same minutes (QMX already refuses a half pair; `p_qmbread.py:13-14`).
15. **Cross-source check.** For a sample of days, compare Dukascopy to his broker's own bars (cTrader trendbars): price offset, spread, missing hours. This is also how the market journal learns his broker's real costs. Use a second source to catch bad ticks (CHECKED as practice, Forex Factory).
16. **Source seams.** When a series switches source or feed (Dukascopy `bi5` to JSON in July 2026; Databento before and after May 2017), record the date on the card and test that the statistics don't jump at the seam.
17. **Replaced files.** Binance says archived files may be replaced after fixes (CHECKED). Keep the old fingerprint; a new one becomes a new card version with a `replaces` link (study 54 already decided this).

---

## 4. Live market feed for 200+ units

### 4.1 Per-platform facts (CHECKED unless marked)

| Platform | Subscriptions | Rate limits | What the stream carries | Known breakage |
|---|---|---|---|---|
| **cTrader Open API** | "There is no limit on number of symbols you can subscribe to" (Spotware staff, forum). `ProtoOASubscribeSpotsReq` takes a list of symbol ids. Live trendbars need a spot subscription first and arrive inside spot events. Depth: `ProtoOASubscribeDepthQuotesReq`, also a list. **Connections: "At most … two connections: one for demo accounts and one for live accounts"**, each with unlimited accounts. Error 67 `CONNECTIONS_LIMIT_EXCEEDED` exists. | 50 requests/s, 5/s for history, per connection. Heartbeat every 10 s. | Bid and ask are each optional in a spot event, so keep the last value per side. With the market closed you get one event with the closing price. Depth = differential updates keyed by quote id (`newQuotes`, `deletedQuotes`); size in cents. No trade tape. | Weekend maintenance; token refresh invalidates the old token's accounts (`ProtoOAAccountsTokenInvalidatedEvent`); whole-app disconnect event (study 56 §2). |
| **MT5** | One terminal per account; prices for the symbols in Market Watch. The Python package reads ticks, bars and depth from the running terminal over local inter-process calls (study 56 §3). | None published. | Ticks with flags; depth where the broker sends it. | INFERRED: the Python package has no push callbacks, so the feed keeper polls `symbol_info_tick` or `copy_ticks_from`, or an EA inside the terminal pushes over a socket (study 56 §3: up to 128 sockets per program). Windows only (Wine on Linux). |
| **Hyperliquid** | Websocket per IP: 10 connections, 30 new per minute, **1,000 subscriptions**, 2,000 messages a minute sent (study 56 §4). | REST 1,200 weight a minute per IP. | trades, `l2Book` (20 levels, snapshot about every 5.4 s), `fastBook` (5 levels, about every 500 ms, since 2026-06-17), `bbo`, `activeAssetCtx` (funding, open interest, mark) (CHECKED, Tardis HL page). | The server may drop clients without notice; resubscribe and take a fresh snapshot (study 56 §4). |
| **CCXT / Binance futures** | One connection listens to at most 1,024 streams. | 10 incoming messages a second per connection; repeated disconnects can ban the IP. | Routed endpoints `/public`, `/market`, `/private`; an unrouted connection only gets `/public` streams (a 2026 change). | **Every connection is cut at 24 hours.** Ping every 3 minutes; disconnected without a pong within 10 minutes. CCXT Pro reconnects with backoff on the next watch call (study 56 §5). |
| **Futures brokers** | Rithmic, CQG, Interactive Brokers: market data per exchange subscription; IB counts "lines" (study 56 §1: "50 requests/s at 100 lines"). Databento live is subscription-only (Standard $199/month). | Per broker. | Full depth and tape. | IB needs a desktop session (study 56). |

### 4.2 The pool design (INFERRED)

The router is not in the data path. The feed belongs to the machine, not to the router.

```
broker / exchange connection
        │  one subscription per (venue, symbol, kind)
        ▼
  feed keeper (one per connection; owns the socket and the lease)
        │  stamps each message: venue, symbol, kind, seq, venue_time, recv_time
        ├──► local bus ──► unit workers (200+ units, each filters its symbols)
        │             ├──► router planner/gate (a reader like any unit)
        │             └──► guards (SQS, news kill switch, account guard)
        ├──► recorder ──► monthly Parquet partitions (the same store QMB reads)
        └──► market-journal roller ──► per-minute cost and session rows (§5)
```

- **One subscription per symbol, many readers.** 200 units on 60 symbols means 60 spot subscriptions, not 200. Units ask the pool for `(venue, symbol, kind)`; the keeper subscribes on the first ask and unsubscribes when the last reader leaves after a grace period (setting `unsubscribe_grace`).
- **A unit never asks the router for prices.** The ruling: "If the router is slow, down or offline, the unit keeps trading" (STATE.md:61). The router's advice ("this market fits your conditions") arrives separately and expires (09); the feed does not depend on it.
- **Bus choice, simplest first:**
  1. *In process:* the keeper and the unit workers share one Python process with asyncio queues. Fastest, nothing to install. One crash takes every unit down, so run units in a few worker processes, not one.
  2. *Local message bus between processes:* ZeroMQ PUB/SUB (no server; works on Windows) or a single NATS server (one binary; JetStream keeps a short replay so a restarted unit can refill). ZeroMQ drops messages for a slow reader once its queue fills, so sequence numbers must catch that. INFERRED from memory of both libraries; not re-read today.
  - **Recommendation:** start with option 1 inside the node process, using sequence numbers and a last-value cache per symbol. Move to option 2 only when units must run in separate processes or on separate machines. One line, settled.
- **Last-value cache:** the latest bid, ask, book and asset context per symbol. A unit that starts or restarts reads it at once, then follows the stream. Warm-up history comes from the recorder's partitions plus the last minutes in memory, not from a fresh broker history call. This keeps the history limit (5/s on cTrader) for gap repair only.
- **PC, node, or both (local first, rulings 136-139):**
  - *PC alone:* the PC runs a keeper per connection. Paper units, research and recording all read it.
  - *Node running:* the node holds the **live** cTrader connection (the trading side needs it). The PC does not open a second live connection under the same app (§4.1: about two per app). It reads the node's pool over the private network for live prices, or uses its own demo connection for research prices.
  - *Who holds the connection* is one lease record per (app, environment), the same pattern as the Library's `refs/primary` epoch (study 55; library spine AD-14). The holder renews it; the other side reads. If the node dies, the operator's click (or a timeout he sets) moves the lease to the PC.
  - *Open check:* whether two live connections under one app actually fail (error 67) or are only discouraged ("you should"). A one-minute test on the demo host with two demo connections would settle it. Until then, design for one.
  - *Crypto:* each machine may open its own websockets (per-IP limits), so PC and node can each subscribe directly. INFERRED from the per-IP wording.
- **Capacity check for 200+ units (INFERRED from §4.1):**
  - cTrader: no symbol cap, so one connection carries every symbol.
  - Hyperliquid: 1,000 subscriptions per IP ÷ about 5 channels per symbol = about 200 symbols per machine.
  - Binance: 1,024 streams per connection; open a second connection past that.
  - Futures: the cost is per exchange subscription, not per unit.

### 4.3 Failure modes and what happens

| Failure | Detection | What units do | Repair |
|---|---|---|---|
| **Socket drops, reconnect** | Heartbeat missed; socket error; Binance's 24-hour cut. | Symbols go `feed-stale` after `stale_after` (default: a multiple of that symbol's usual gap for this hour of the week). Guards close new entries on stale symbols. Open trades keep their broker-side stop and target. | Reconnect with backoff; resubscribe the whole symbol list in one request; on cTrader, ask for ticks over the gap (5/s budget, one week per request) and write them to the recorder marked `backfilled`. |
| **Gap in sequence** | A missing `seq` on the bus (slow reader), or a missing exchange sequence (Hyperliquid, Binance books). | That reader marks the symbol stale and re-reads the last-value cache. | Book feeds: drop the local book and take a fresh snapshot. cTrader depth has no snapshot message; after a reconnect, clear the book and rebuild from new quotes (INFERRED from the differential model). |
| **Stale but connected** | No price change for longer than usual, while other symbols on the same connection tick. | Same as above, for that symbol only. | Unsubscribe and resubscribe that symbol. If every symbol of a venue is stale, mark the venue stale, not each symbol (09 §4.3). |
| **Market closed** | Session calendar says closed; cTrader sends one closing-price event (CHECKED). | Not stale. No entries, by calendar. | None. |
| **Token invalidated** | `ProtoOAAccountsTokenInvalidatedEvent`; error 1. | Affected accounts' units stop new entries. | Refresh the token; re-authorise the accounts. |
| **Keeper process dies** | The bus stops; watchdog. | All its symbols stale; units keep open positions protected at the broker. | Restart the keeper; units resume from the last-value cache. |
| **Router dies** | Router heartbeat. | **Nothing changes in the feed.** Units keep trading on their own conditions; the router's last plan expires on schedule (09 §2.6). | Restart the router. |
| **Clock drift** | Receive time vs venue time drifts. | Warn; staleness uses receive time. | Sync the clock. Hyperliquid writes fail outside a 2-day nonce window (study 56 §4). |
| **Duplicates after reconnect** | Same venue time and prices, or the same exchange id. | Dropped by the keeper before the bus. | None. |

---

## 5. Where spread, fees, slippage and session facts live

### 5.1 Two journals, no duplication (INFERRED, from the ruling at STATE.md:55-56)

**Market journal** (the "router journal for market-level facts"). One row per (broker, account type, instrument, time bucket). The default bucket is 1 minute (setting `market_journal_bucket`). Written by the feed keeper's roller on whichever machine holds the connection. The router reads it like everyone else.
- From quotes: spread (mean, median, 95th percentile, maximum, time-weighted), tick count, longest quote gap, mid open and close, stale flag.
- From the symbol record, refreshed daily and on change: swap long and short, triple-swap day, commission type and rate, minimum and step volume, stop distance, trading hours. For perps: funding rate, mark, oracle, open interest. Today `ProtoOASymbol` arrives raw, not normalised (02 §10).
- From the calendar: session state (Asia, London, New York, overlap), holiday, rollover window, news window.
- **Folded in nightly from all units' fills:** slippage (filled price minus the quote at send time), fill latency, rejection rate, partial fills. Per bucket and instrument, with the fill count. Only aggregates: the fills themselves stay in the unit journals.

**Unit journal** (01-08 already define it). Only what is the unit's own: signals taken, signals seen but not taken (with the reason), missed trades, orders, fills, its own slippage per trade, its sizing inputs, its condition checks. Each row carries the key `(broker, account_type, instrument, bucket_start)`, so the UI can show "the spread when this trade was taken" by a join, not by a copy.

**Why this split (INFERRED):**
- Spread on EURUSD at 08:01 at IC is the same fact for every unit on EURUSD. Writing it 40 times breaks the "no duplication" rule.
- **It fills GAP-0048.** QMB's cost model needs per-broker spread, swap, commission and slippage by instrument, hour and session. Today it is "synthetic from calibration" with the calibration empty (02 §10; STATE.md conflicts). The market journal is exactly that calibration, measured.
- WF3-style studies ("which instruments had which conditions over time") read one table.
- Several brokers or nodes: one market journal per (broker, account type). A second node on the same broker writes the same keys; the first writer per bucket wins (the Library's "one claim per partition key" rule, study 54).

### 5.2 Storage volume estimates (INFERRED from checked sizes)

Base figures (CHECKED, study 53 §3.1): about 12 million 1-minute rows per instrument over 23 years = 100-200 MB of Parquet, so about 8-17 bytes per row. About 5 GB of ticks per FX pair over 23 years (3 GB Parquet plus 2 GB raw); 28 pairs = about 140 GB. One busy USDCAD hour = 4,260 ticks (CHECKED, issue #261).

| Data | Rows | Size | Scale for 200 units on 60 instruments |
|---|---|---|---|
| 1-minute bars, FX (bid and ask) | about 375,000 per side per year | about 6-12 MB per instrument-year | 60 × 23 years ≈ **14 GB** (Dukascopy depth) |
| 1-minute bars, crypto (24/7) | about 525,600 per year | about 4-9 MB per series-year | small |
| Ticks, FX, recent years | about 15-25 million per year (from 50,000-80,000 a day) | about 150-300 MB per instrument-year | 60 × 23 years ≈ **150-200 GB** (older years are thinner) |
| Live tick recording | same | about 150-300 MB per instrument-year | **10-20 GB a year** per broker feed |
| Crypto trades, top perps | millions a day | GBs a month per top symbol | measure before committing |
| L2 depth | 10-100 × ticks (guess) | | record only where a unit's data needs say depth |
| Market journal, 1-minute buckets | 60 × 2 brokers × 525,600 = 63 million a year | about 1-2 GB a year | hourly buckets ≈ 20 MB a year |
| Unit journals, events only | 200 units × (20 trades + 200 signal events a day) ≈ 16 million a year | a few hundred MB a year | if every unit logs every 1-minute decision: about 105 million rows, 1-2 GB a year |

**Points that matter:**
- **Prices are stored per (source, instrument), never per unit.** Units add only their journals.
- **Storage is not the bottleneck; the QMB reader is (§1 #1).** A month of one instrument's 1-minute bars is a few MB on disk but 16 GB in the reader today.
- **PC disk (CHECKED, study 52 row 63):** C: 12 GB free, D: 8.3 GB free when the inventory read it. Bars for the active instruments fit; ticks do not. The PC keeps a cache sized from free space (library spine rule 124, data round), and the full archive lives on the server and in the bucket. "Works on the PC alone" therefore means: with the data downloaded to the PC. A bigger local disk is the only full fix (his call, not a design issue).

### 5.3 How the Library store handles it (CHECKED design, INFERRED fit)

- Market data is **not** Library data. It is Parquet in `source=/instrument=/kind=/year=/month=` partitions, one immutable file per partition named by its fingerprint, read by DuckDB. The Library reaches it only through `dataset` cards and the market-data door (study 53 §3.1; library spine rule 124; AD-25, AD-28).
- Partitions: the server holds the main copy, the bucket the full copy (pushed nightly), the PC a cache. A partition may leave the PC cache any time and is re-fetched by fingerprint (library spine rule 124).
- **Fit (INFERRED):**
  - Recorded live ticks and bars: `source=<broker>-live`, `kind=tick | m1`, one partition per day while open, frozen per month.
  - Market journal: `source=<broker>`, `kind=costs-1m`, the same layout and the same door. QMB reads it as cost calibration, by fingerprint, so a backtest result names exactly which cost months it used.
  - Unit journals: one append-only series per unit, partitioned by month, also Parquet, so 200 units × years stay out of `catalog.db`. The Library holds a card per unit journal that points at its partitions. The trades a QMB run produces are already planned as Parquet blobs on the result (Lib AD-29; today they sit inside one `report` blob, `qma-ship/data/BACKLOG.md:25`).
  - Router logs and caches: the same pattern, `kind=router-plan` and `kind=router-gate`.
  - Open months are rewritten daily and the card gets a new version; frozen months never change (study 55 P-MARKS).

---

## 6. Settings this file proposes (all editable; defaults INFERRED)

| Setting | Default | Note |
|---|---|---|
| `lookback_default_start` | 2020-03-01 | post-COVID; never a cap |
| `lookback_max` | none | the ruling |
| `historical_holdout_months` | 12 | exists already |
| `market_journal_bucket` | 1 minute | hourly if disk is short |
| `stale_after` | 5 × the symbol's usual gap for that hour of the week | per symbol, learned |
| `unsubscribe_grace` | 10 minutes | keeps a subscription when a unit restarts |
| `backfill_on_reconnect` | on | uses the venue's history budget |
| `dukascopy.retries` / `retry_on_empty` | 5 / on | the library defaults are 0 / off |
| `dukascopy.include_flats` | on | QMX marks sessions itself |
| `dukascopy.pause_ms` | 2,000 | slow and polite, as in issue #261 |
| `record_depth` | per instrument, off by default | on when a unit's data needs ask for depth |
| `unit_journal_level` | events | `every_bar` on request |
| `spike_k`, `spike_revert_ticks` | learned from the instrument's history | §3 item 4 |

---

## 7. Not verified

- Whether a second live cTrader connection under one app fails or is only discouraged.
- FirstRate and Tardis prices; FirstRate's bar source (trade, mid or bid) for FX.
- Binance futures funding-rate bulk files (believed to exist; not opened).
- Bybit trade-file start dates per symbol.
- ZeroMQ and NATS behaviour on Windows (from memory, not re-read today).
- That QMX's `bi5` fetch path actually points at the dead feed: inferred from the adapter's decoder and issue #254; no live call was made.
- Tick and journal sizes in §5.2 are estimates from the checked base figures; measure on the first real month.
- How deep cTrader broker history goes at IC Markets.

## 8. Sources (all read 2026-10-27)

- dukascopy-node: https://github.com/Leo4815162342/dukascopy-node (README, instrument list); https://www.dukascopy-node.app/config/node ; https://www.dukascopy-node.app/config/cli ; https://www.dukascopy-node.app/downloading-tick-data ; https://www.dukascopy-node.app/errors-and-empty-data ; instrument pages `/instrument/eurusd`, `/xauusd`, `/usa500idxusd`, `/aaplususd`, `/brentcmdusd`, `/btcusd`
- Issues: https://github.com/Leo4815162342/dukascopy-node/issues/254 , /261 , /250 , /193 , /213 , /133 ; wiki "Information on empty responses"
- Dukascopy terms: https://www.dukascopy.com/swiss/english/legal-pages/terms-of-use/ ; anti-bot clause as quoted at https://openbrokerapi.com/data-sources/dukascopy-historical-data
- Quality: https://support.eareview.net/support/solutions/articles/19000130791-selecting-a-tick-data-source ; https://strategyquant.com/forum/topic/3516-those-using-dukascopy-data-be-warned/ ; https://www.forexfactory.com/thread/68015-good-historical-tick-data-source?page=2
- HistData and TrueFX: https://www.histdata.com/ ; https://exactick.com/free-forex-tick-data ; https://soft4fx.com/tutorials-mt5/downloading-data.php
- Binance: https://github.com/binance/binance-public-data ; https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams
- Bybit: https://public.bybit.com/trading/BBUSDT/ ; https://www.bybit.com/derivatives/en/history-data ; https://pypi.org/project/bybit-history-downloader/
- Databento: https://databento.com/pricing ; https://databento.com/blog/updates-to-subscription-pricing ; https://databento.com/blog/CME-history-extended-to-2010 ; https://www.databento.tech/docs/datasets/glbx-mdp3
- FirstRate: https://firstratedata.com/bundle/all ; https://firstratedata.com/b/20/fx-majors ; https://firstratedata.com/cb/1 ; https://firstratedata.com/i/futures/E6
- Tardis: https://docs.tardis.dev/faq/billing-and-subscriptions ; https://docs.tardis.dev/faq/general ; https://docs.tardis.dev/historical-data-details ; https://docs.tardis.dev/historical-data-details/hyperliquid
- cTrader: https://help.ctrader.com/open-api/connection/ ; https://help.ctrader.com/open-api/symbol-data/ ; https://help.ctrader.com/open-api/faq/ ; https://community.ctrader.com/forum/connect-api-support/37215/ ; https://deepwiki.com/spotware/openapi-proto-messages/4.3-market-data-operations
- Earlier QMX studies reused, not repeated: `tracker/qma-v2/research/methodology/52`-`58` (data round), `56` (connections), `53` (stack); `tracker/risk-sizing/research/02`, `09`.
