---
title: The trader's vocabulary beyond FX, per asset class and data level
date: 2026-10-30
author: research agent 2 (poteto-mode, no sub-agents)
ticket: wayfinder/tickets/research-dictionary-beyond-fx.md
status: research; options and evidence, not a design
---

# 45: The trader's vocabulary beyond FX

**Labels.** CHECKED means I read it at the cited place this session (file and line, a command I ran, or a URL I fetched). INFERRED means my reasoning or plain trading knowledge, not a source I read today. Settings are starting defaults only, never rulings (standing order 5). Every entry stays role-neutral: a concept is a thing that can be measured; its job (context, trigger, filter, exit) is set later on the unit that uses it (`C:/Users/Mubarak/Desktop/Stats/dictionary/README.md`, CHECKED).

**Keys.** `D` = `C:/Users/Mubarak/Desktop/Stats/dictionary/`. `MQ` = `C:/Users/Mubarak/Desktop/QMX/.worktrees/mql5-library/data/mql5-library/md/` (3,128 article files). `T1` = `operator/transcript-2026-10-20-to-28.md`, `T2` = `operator/transcript-2026-10-29-to-30.md`. `R36`, `R35`, `R43` and so on are files in this folder.

**Settled before this file, not re-argued here.** The dictionary is rebuilt, and the 239 entries are kept as seeds (R44, lead's rulings; R43 §3.2). The new form gives each entry trader words, a machine spec and code, a minimum data level, a transfer status per class, and number kinds (R43 §3.2). This file says what the rebuilt vocabulary must contain beyond FX.

---

## 0. What matters most (short)

1. **The data ladder in research 43 hides three splits that change which concepts can run.** "Bars" can carry real exchange volume or only a count of price changes. "Depth" can be the best price only, a summary by price, or every resting order one by one; iceberg and stop-run detection needs the last kind (Bookmap needs CME order-by-order data for native icebergs, CHECKED). "Open interest" on CME is an end-of-day number, while on Binance it is published every 5 minutes (CHECKED). A concept must name which side of each split it needs. Section 2.
2. **About 150 trader concepts outside FX are missing, and most of them are not exotic.** Market profile (time at price, initial balance, range extension), the futures calendar (front month, roll, settlement, the daily one-hour break), stock rules (earnings, ex-dividend, trading halts, the short-sale rule, auction imbalances), index internals (TICK, advance-decline, TRIN, VIX), perps fields (funding, mark versus index versus last price, basis, open interest change, liquidations, long/short ratios) and the metals and energy clocks (the gold auctions at 10:30 and 15:00 London, the oil inventory report at 10:30 New York on Wednesdays). Section 3.
3. **Several existing entries are written as if the world were FX and crypto spot.** `order-book-depth` says "Centralized exchanges only (crypto spot)"; `trading-session` says sessions on 24/7 markets are only "heuristic liquidity waves" (`D`, CHECKED). Futures, stocks and perps break both claims. The rebuild has to rewrite the market line of old entries, not only add new ones. Section 4.
4. **Twelve words mean different things across classes under one name.** Volume, open interest, session, rollover, basis, settlement, gap, spread, liquidation, funding versus swap, "the open", and "the close". Each needs a per-class meaning on its entry, or one entry per meaning. Section 4.
5. **Statistics and models are used as strategy parts, not only as judging words.** QuantConnect's engine ships the Hurst exponent, Kaufman's efficiency ratio, the choppiness index, ARIMA, "Momersion" and breadth indicators as indicators any strategy can call (CHECKED). Regime models scale exposure in published backtests (Kritzman, Page and Turkington 2012, CHECKED). The MQL5 corpus has 58 articles naming Hurst and 86 naming GARCH (CHECKED, command below). They belong in the vocabulary as readings; Sharpe, PBO and walk-forward stay in a separate judging glossary. Section 5.
6. **The free history is better than the API limits suggest.** Binance's live API keeps only one month of open-interest history (CHECKED), but Binance's public archive holds 5-minute open interest, long/short ratios, taker volume ratios and depth bands back to September 2020 for BTCUSDT (CHECKED by download). Liquidations are the exception: the live stream sends at most one liquidation per symbol per second, and the history call covers 90 days (CHECKED). So "liquidations" in any backtest is a sample, and the vocabulary entry must say so. Section 2.3.
7. **Class packs are options, not a choice.** Section 6 lists what each class needs before a unit can trade it, and three orders to build them in, with what each costs.

---

## 1. How this was done

- Read the dictionary's own index and entry names (`D/README.md`; `grep "^## "` over the four family files, CHECKED) so that "missing" means missing from the 239, not from my memory.
- Read research 36 (the MQL5 census), 35 §2-3 (vocabulary per style and class), 34, 39, 43 §2-3.2 and the funnel4 QML field §T3-T5 and its questions Q25-Q57. Not repeated here: the MetaTrader built-in indicators that 36 lists as missing (CCI, Parabolic SAR, Williams %R and twelve more, 273 articles), the price-action gaps and the exit gaps. They stand as 36 wrote them.
- Read his words in `T1` and `T2` on QML and the dictionary: "That's why it's called a dictionary, yeah? From languages, terminologies" and "if it's new, we can append it" (`T2`, 30 Oct 06:11 message, CHECKED); "we are expanding to way beyond FX, in fact, to the point of where we added indices yesterday" (`T2`, 30 Oct 06:42, CHECKED); "a market is still a market regardless" and "we are going to consider variables that each market has" (`T2`, 29 Oct 17:25, CHECKED); "Order flow is good for scalpers" (`T2:132` via R35 §7, CHECKED there).
- Practitioner and venue sources fetched live through Exa (section 10). One extra local count on the MQL5 corpus (section 1.1).

### 1.1 How thin the MQL5 corpus is beyond FX

Raw counts over all 3,128 article files (not the screened 2,038), case-sensitive phrases to avoid false hits. Command: `grep -l -E "<pattern>" MQ/*.md | wc -l`, run this session. CHECKED.

| Phrase | Articles |
| --- | --- |
| Market Profile | 28 |
| TPO (as a word) | 10 |
| Order Book | 66 |
| DOM or Depth of Market | 75 |
| Footprint | 83 (includes "memory footprint"; precision not checked) |
| Open Interest | 23 |
| Funding | 11 |
| Perpetual | 8 |
| Cumulative Delta or CVD | 1 |
| Hurst (any case) | 58 |
| GARCH (any case) | 86 |
| hidden Markov or HMM (any case) | 66 |
| variance ratio (any case) | 11 |
| efficiency ratio (any case) | 14 |

INFERRED reading: the MQL5 library is an FX and MetaTrader corpus. It is good evidence for indicators and FX habits and weak evidence for futures, stocks and perps vocabulary. Research 36's 44% coverage is coverage of FX practice, which is why this file goes to exchange and platform sources instead. His own memory points the same way: in August he said most strategies come "from futures traders" (research 39, GM 3262, CHECKED there).

---

## 2. The data ladder, sharpened

Research 43 F6 names seven data levels: 0 calendar, 1 bars, 2 quote ticks, 3 depth, 4 trade tape, 5 derivatives fields, 6 outside data (`R43:101-104`, CHECKED). The ticket names a slightly different ladder (calendar, bars, real volume, depth, trades tape, open interest and funding, outside data). The sources show three splits inside these levels. Each changes what a concept can do.

### 2.1 Volume truth sits inside "bars"

| Kind of volume | What it counts | Where it exists | Source |
| --- | --- | --- | --- |
| Exchange volume | contracts or shares actually traded | futures, stocks, crypto exchanges | CME: volume "is calculated by counting the number of contracts" traded (cmegroup.com "What is Volume?", CHECKED) |
| Taker buy volume inside the bar | the part of bar volume where the buyer took the offer | Binance spot and futures bars carry it as a column | Binance public data README, kline columns "Taker buy base asset volume" (CHECKED) |
| Tick volume | number of price changes in the bar | FX and CFD brokers, including cTrader | dictionary entry `spot-fx-tick-volume` (`D`, CHECKED) |
| Venue or liquidity-provider volume | one dealer's own flow | some FX feeds | INFERRED; the dictionary's `vwap` entry already warns that FX VWAP is "only broker/venue-specific" (`D`, CHECKED) |

So level 1 needs a tag: `volume: exchange | taker-split | tick-count | venue`. A volume profile, VWAP or OBV built on tick counts is a proxy and must be flagged (the dictionary already says this for volume profile, `D`, CHECKED). INFERRED.

### 2.2 Depth has three grades

| Grade | What it shows | What it enables | Source |
| --- | --- | --- | --- |
| Top of book | best bid and best ask with sizes | spread, quote imbalance | Binance "bookTicker" archive (CHECKED by S3 listing) |
| Depth by price | total size at each price level, or summed in bands | book pressure, walls, depth bands; Binance archives depth summed at ±1% to ±5% from the price (`timestamp,percentage,depth,notional`, CHECKED by download) | dictionary `order-book-depth` names "L2 vs L3" (`D`, CHECKED) |
| Order by order | every resting order with its own id | native iceberg detection, queue position, which order was pulled | Bookmap: native CME icebergs are shown "with precision based on the MBO data" (bookmap.com blog, CHECKED); its Stops & Icebergs add-on "works only with CME exchange" adapters (Bookmap knowledge base, CHECKED) |

cTrader gives depth but no public trade tape (research 21, CHECKED via STATE). Without a tape, footprint, delta and iceberg detection are not available on cTrader at all. INFERRED from that.

### 2.3 Derivatives fields differ in clock and history

| Field | CME futures | Binance USD-M perps | Hyperliquid perps |
| --- | --- | --- | --- |
| Open interest | total contracts held "at the end of the trading day" (CME "Open Interest" course, CHECKED); official figures the next morning (CME VOI reports page, CHECKED) | live value; history in 5m to 1d steps, API keeps "only the data of the latest 1 month" (Binance Open Interest Statistics doc, CHECKED); public archive keeps 5-minute history from 2020-09-01 (CHECKED: S3 key `BTCUSDT-metrics-2020-09-01.zip`) | not checked this session |
| Funding | none | default 8-hour interval (R35 §2.2, CHECKED there); monthly funding archive exists (CHECKED by S3 listing) | paid every hour at one eighth of the 8-hour rate; capped at 4% per hour (Hyperliquid funding docs, CHECKED) |
| Mark, index, last price | settlement price daily | separate mark, index and premium-index bar series, each archived (CHECKED by S3 listing) | mark price = median of three inputs; used "for margining, liquidations, triggering TP/SL" (Hyperliquid robust price indices, CHECKED) |
| Liquidations | none (margin calls are private) | stream sends at most one per symbol per 1,000 ms, now "the largest one" (Binance changelog 2026-04-10, CHECKED); history call "only ... past 90 days" (changelog 2026-04-06, CHECKED); no liquidation archive in the daily USD-M listing (CHECKED by S3 listing) | not checked this session |
| Long/short ratios, taker ratio | COT report, weekly (INFERRED) | 5-minute archive columns: top-trader long/short ratio (accounts and positions), global long/short ratio, taker long/short volume ratio (CHECKED by download) | not checked |

INFERRED consequence for the vocabulary: every derivatives entry must say its clock (end of day, 5 minutes, live) and whether its history is complete, sampled, or limited by the provider. A liquidation-cascade reading backtested on Binance data reads a one-per-second sample of the largest event, not every liquidation. That is a provider limit, not a cap QMX sets (standing order 9).

### 2.4 Two more dimensions every entry needs

- **Clock base.** Sessions on CME follow Chicago time, the gold auctions London time, stock auctions New York time, and Binance UTC (sources in section 3). Broker server time is separate again (R36 §2.2 "broker server time" 115 articles, CHECKED there). INFERRED: each calendar entry names its clock and its daylight-saving rule.
- **Bar construction.** Tick, range, Renko, volume and dollar bars change what every price concept sees (R36: 58 articles, CHECKED there). Order-flow tools let you pick it per chart (ATAS footprint "bar type" is a setting; the dictionary's `footprint-order-flow` lists "bar type (time/tick/range/renko)", `D`, CHECKED).

---

## 3. Concepts not in the dictionary today

**How to read.** Family: indicator, price action, order flow, context, session, entry, exit, trade management, filter, statistics and models. Data level as in section 2 (0 calendar, 1 bars, 1v bars with exchange volume, 2 quote ticks, 3t top of book, 3p depth by price, 3o order by order, 4 trade tape with aggressor side, 5 derivatives fields, 6 outside data). Classes: FX, IC (index CFD), IF (index futures), M (metals), E (energy), S (stocks), CS (crypto spot), CP (crypto perps), F (any listed future). "Status" says whether the dictionary has it: missing, or partial (an alias or a narrower entry exists). Settings are starting defaults; the source column says where the default comes from, or INFERRED.

Only concepts beyond what research 36 already lists are here. Exits are named as vocabulary only; their maths belongs to the risk session (`RISK-SIZING-PACK.md`).

### 3.1 Auction and volume-at-price (market profile)

| Concept | Family | Level | Classes | Settings (starting default) | Status | Source |
| --- | --- | --- | --- | --- | --- | --- |
| Time-at-price profile (TPO) | context | 1 | all | block length 30 min; value-area share 70% | partial: `volume-profile` alias "market profile (related)" (`D`, CHECKED) | TradingView TPO help: value area "70% of trading activity" (CHECKED); 30-minute blocks most common (FTMO/OANDA blog, CHECKED) |
| Initial balance | context, price action | 1 | IF, IC, S, E, M | first 60 min of the main session (two 30-min blocks) | missing | Aspen "Using Market Profile": the first hour "creates what is called the initial balance" (CHECKED) |
| Range extension above or below initial balance | trigger, context | 1 | as above | none beyond IB | missing | Aspen, same page (CHECKED) |
| Responsive vs initiating activity (relative to yesterday's value) | context | 1 | as above | yesterday's value area | missing | Aspen, same page (CHECKED) |
| Day type (normal, trend, neutral, double distribution) | context | 1 | as above | classification by IB width and extensions | missing | TradingView TPO help names normal, trend and neutral days (CHECKED) |
| Single prints, poor high or low | price action | 1 | as above | single-print row count 1 | missing | TradingView TPO help (CHECKED) |
| Naked (untouched) point of control from an earlier day | location | 1v | IF, S, CS, CP | look-back N days, default 5 (INFERRED) | partial: `point-of-control` exists (`D`, CHECKED) | Tradovate TPO page: "untouched ... POC ... extended into the future" (CHECKED) |
| Developing value area and POC (live during the session) | context | 1v | IF, S, CS, CP | session anchor | missing | INFERRED; every profile tool draws it |
| Anchored VWAP (from a chosen bar or event) and VWAP deviation bands | location | 1v | IF, S, CS, CP; proxy on FX | anchor event; bands at 1 and 2 standard deviations (INFERRED) | partial: `vwap` has "session anchor" only (`D`, CHECKED) | INFERRED (common platform built-in) |

### 3.2 Order flow from the tape and the book

| Concept | Family | Level | Classes | Settings | Status | Source |
| --- | --- | --- | --- | --- | --- | --- |
| Diagonal bid/ask imbalance | order flow | 4 | IF, F, CS, CP, S | ratio 300% as a working start; ATAS ships 150%; range 150-400% | missing (footprint entry mentions "imbalance threshold (e.g. 2–4×)") | ATAS settings: default "set to 150%" (CHECKED); ATAS Learn: "around 300%" as a start (CHECKED) |
| Stacked imbalance | order flow, trigger | 4 | as above | 3 levels in a row | missing | ATAS Learn: "Three or more consecutive imbalances" (CHECKED) |
| Unfinished or finished auction (zero at the bar edge) | order flow | 4 | as above | none | missing | ATAS Learn footprint patterns (CHECKED) |
| Delta per bar and delta divergence | order flow | 4 | as above | bar type | partial: `cumulative-delta`, `order-flow-divergence` (`D`, CHECKED) | ATAS Learn (CHECKED) |
| Iceberg order (native vs detected) | order flow | 3o + 4 | IF, F (native needs order-by-order data); CS detected only | minimum order size filter | missing | Bookmap Stops & Icebergs (CHECKED) |
| Stop run detected from the tape | order flow | 3o + 4 | IF, F | burst volume V within time T | partial: `stop-run-label` is a price-action label (`D`, CHECKED) | Bookmap: triggers when volume "is greater or equal to V within the time interval T" (CHECKED) |
| Large resting order (wall, large lot) | order flow, location | 3p | IF, F, CS, CP | ≥20% of size at that price (Bookmap default) | missing | Bookmap Large Lot Tracker: "At least a configurable 20%" (CHECKED) |
| Pulled or added liquidity (book changes without trades) | order flow | 3p | as above | window in ms | partial: `order-book-liquidity-change` (`D`, CHECKED) | INFERRED |
| Taker buy/sell ratio | order flow, context | 1 (Binance bars carry it) or 4 | CS, CP | bar length | missing | Binance kline columns (CHECKED); Binance 5-min `sum_taker_long_short_vol_ratio` (CHECKED by download) |
| Trade size filter (large prints only) | filter | 4 | IF, S, CS, CP | size threshold per instrument | missing | INFERRED |
| Tape speed (trades per second against the usual rate) | context | 4 | all with a tape | ratio to time-of-day median | missing | INFERRED; research 05's "information per bar" idea (STATE, CHECKED) |
| Depth bands (book size within ±1% to ±5%) | context | 3p | CS, CP | bands 1-5% | missing | Binance `bookDepth` archive (CHECKED by download) |

### 3.3 Derivatives fields (perps, futures)

| Concept | Family | Level | Classes | Settings | Status | Source |
| --- | --- | --- | --- | --- | --- | --- |
| Funding rate (current and predicted) | context, cost | 5 | CP | interval 8 h (Binance default) or 1 h (Hyperliquid) | missing (`rollover-swap-cost` warns "Do not conflate FX swap with crypto funding", `D`, CHECKED) | Hyperliquid funding doc (CHECKED) |
| Funding settlement window | session | 0 + 5 | CP | minutes before settlement, default 15 (INFERRED) | missing | Hyperliquid: funding is "paid every hour" (CHECKED) |
| Mark price vs index price vs last price | context, execution | 5 | CP, F | which price triggers stops | missing | Hyperliquid robust price indices (CHECKED); freqtrade stop on `last`, `mark` or `index` (R35 §2.2, CHECKED there); Binance `workingType` MARK_PRICE or CONTRACT_PRICE (Binance skill reference, CHECKED) |
| Premium or basis (perp vs index; future vs cash) | context | 5 | CP, IF, F | annualised basis | missing | Binance `basis` and `premiumIndexKlines` (CHECKED); CME "What is Equity Index Basis?" (CHECKED) |
| Open interest level and change | context | 5 | F, CP | change over N bars; Binance step 5 min | missing (R36: 105 articles under sentiment, CHECKED there) | CME Open Interest course: rising OI "typically a confirmation of the trend" (CHECKED) |
| Price-volume-OI quadrant (price up with OI up, etc.) | context | 5 | F, CP | look-back N bars | missing | Investopedia on volume with OI (CHECKED; secondary, use CME as primary) |
| Liquidation level estimate and liquidation cascade | context, trigger | 5 | CP | leverage tiers per asset | missing | Hyperliquid liquidations doc: maintenance margin "between 1.25% ... and 16.7%" (CHECKED) |
| Liquidation flow (sampled) | order flow | 5 | CP | 1 event per second per symbol is the provider's limit | missing | Binance forceOrder stream doc and changelog (CHECKED) |
| Long/short ratio (all accounts, top traders) | context | 5 | CP | 5-min step | missing | Binance metrics archive columns (CHECKED by download) |
| Auto-deleveraging risk, insurance fund | context | 5 | CP | none | missing | Binance endpoints `adl-risk`, insurance fund snapshot (Binance skill reference, CHECKED) |
| Leverage and margin mode (isolated, cross) | trade management | 0 | CP, F, CFDs | per unit | missing | Hyperliquid liquidations doc on cross vs isolated (CHECKED) |
| Reduce-only order | trade management | 0 | CP, F | none | missing | Binance enum `reduce-only` (CHECKED) |
| Front month and roll date | session | 0 + 1v | F, IF, E, M | switch when next contract's volume passes the expiring one | missing (`centralized-futures-execution-context` mentions front months, `D`, CHECKED) | CME "What is Volume?": switch "When the September contract has more volume" (CHECKED) |
| Continuous contract method (back-adjusted, ratio-adjusted, unadjusted) | data construction | 1 | F, IF, E, M | back-adjusted (INFERRED) | missing | R35 §2.2 lists continuous and back-adjusted (CHECKED there) |
| Settlement price | location | 0 + 1 | F, IF, E, M | exchange's settlement time | missing | CME fair value page: official FV settlement "at 3:15 p.m." Chicago on month end (CHECKED, FVPremiums.pdf) |
| Fair value premium (index future vs cash index) | context | 1 + 6 | IF, IC | rate and dividends to expiry | missing | CME "Calculating Fair Value": "= Cash [1+r (x/360)] - Dividends" (CHECKED) |
| Term structure (contango, backwardation), calendar spread | context | 1v (two contracts) | F, E, M, CP (dated futures) | front vs second month | missing | R35 §2.2 (CHECKED there); MQL5 has 1 article (section 1.1) |
| Commitments of Traders positioning | context | 6 (weekly) | F, FX (via currency futures), M, E | weekly, Friday release (INFERRED) | missing | R36 sentiment row (CHECKED there) |

### 3.4 Index, stock, metals, energy and crypto spot calendars and internals

| Concept | Family | Level | Classes | Settings | Status | Source |
| --- | --- | --- | --- | --- | --- | --- |
| Globex daily break and Sunday open | session | 0 | IF, F, E, M | 16:00-17:00 Chicago, Monday-Thursday | missing | CME product notice: "60-minute break each day beginning at 4:00 p.m." CT (CHECKED) |
| Regular vs extended trading hours (RTH, ETH), overnight high and low | session, location | 0 + 1 | IF, F, S | RTH = cash session | missing | R35 §2.2 (CHECKED there) |
| Cash open and opening drive | session, price action | 0 + 1 | IF, IC, S | first 5-30 min (INFERRED) | partial: `session-open-price`, `opening-range` (`D`, CHECKED) | R35 §2.2 (CHECKED there) |
| Opening and closing auction imbalance | context | 6 (exchange feed) | S (NYSE-listed) | publication from 15:50 New York, every second | missing | NYSE auctions page (CHECKED) |
| Market internals: TICK, advance-decline line, TRIN, up/down volume | context | 6 (breadth feed) | IF, IC, S | TICK extremes ±1,000 as a start | missing | IBKR glossary TICK and TRIN (CHECKED); Investopedia TICK "+1,000 or -1,000" (CHECKED, secondary); LEAN ships Advance Decline, Arms Index, McClellan (CHECKED) |
| Volatility index level and term (VIX and similar) | context | 6 | IF, IC, S | level and 1-day change | partial: `implied-volatility` (`D`, CHECKED) | R36: VIX in 15 MQL5 articles (section 1.1) |
| Trading halt (LULD pause) | context, guard | 6 | S | bands 5%, 10%, 20% by price tier; doubled at open and close; 5-min pause | missing | SEC investor bulletin on LULD (CHECKED) |
| Short-sale restriction day (Rule 201) | context, constraint | 6 | S (US) | trigger at a 10% fall from yesterday's close; lasts the rest of the day and the next | missing | SEC Rule 201 FAQ and 17 CFR 242.201 (CHECKED) |
| Earnings date and time (before open, after close) | session (event) | 6 | S, IC (index weights) | blackout window around the event | missing | INFERRED; R36: 11 MQL5 articles (section 1.1) |
| Ex-dividend date and dividend adjustment | session (event), cost | 6 | S, IC (CFD dividend adjustments) | none | missing | INFERRED; R43 Q44 asks whether QMB must model corporate actions (CHECKED in `qml-field.md`) |
| Splits and corporate actions | data construction | 6 | S | adjusted vs unadjusted series | missing | INFERRED |
| Pre-market and after-hours sessions | session | 0 | S | 04:00-09:30 and 16:00-20:00 New York (INFERRED) | missing | INFERRED |
| Relative volume (today vs usual for this time of day) | filter | 1v | S, IF, CS | 20-day median by minute of day (INFERRED) | missing | LEAN ships "Relative Daily Volume" and "Time Profile" (CHECKED) |
| Gap fill (overnight gap to prior close) | price action, target | 1 | IF, IC, S | gap size in ATR | partial: `price-gap` (`D`, CHECKED) | R35 §2.2 (CHECKED there) |
| Index rebalance, quarterly expiry ("quad witching"), month end | session (event) | 0 | IF, IC, S | exchange calendars | missing | CME month-end fair-value settlement (CHECKED) |
| Gold and silver auction windows (London AM/PM) | session (event) | 0 | M, FX (XAU) | gold 10:30 and 15:00 London; silver 12:00 | missing | ICE Benchmark Administration LBMA page (CHECKED) |
| Real yields, gold/silver ratio | context | 6 / 1 | M | daily | missing | R35 §2.2 lists real yields (INFERRED there) |
| Oil inventory report | session (event) | 0 + 6 | E | Wednesday 10:30 New York, holiday shifts | missing | EIA WPSR schedule page (CHECKED) |
| Natural gas storage report | session (event) | 0 + 6 | E | Thursday 10:30 New York | missing | EIA release schedules page (CHECKED) |
| Crypto day boundary | session | 0 | CS, CP | 00:00 UTC (Binance bars) | missing | INFERRED (Binance timestamps are UTC) |
| Weekend liquidity regime | context | 0 + 1 | CS, CP | Saturday-Sunday flag | missing | R35 §2.2 (INFERRED there) |
| Listing, delisting, token unlock events | session (event) | 6 | CS, CP | none | missing | freqtrade Delist filter (R04 via R35, CHECKED there) |
| BTC dominance, stablecoin supply change | context | 6 | CS, CP | daily | missing | R39 L6 and funnel4 B046 (CHECKED there) |
| Maker vs taker fee tier | cost | 0 | CS, CP, F | per venue | partial: `post-only-entry`, `trading-cost` (`D`, CHECKED) | INFERRED |
| Venue fragmentation (same coin, several exchanges) | context | 1 per venue | CS, CP | reference venue | missing | Hyperliquid oracle is a "weighted median of CEX spot prices" (CHECKED) |

### 3.5 Statistics and models used as parts (detail in section 5)

| Concept | Family | Level | Classes | Settings | Status | Source |
| --- | --- | --- | --- | --- | --- | --- |
| Kaufman efficiency ratio | statistics | 1 | all | period 10 (KAMA's 10,2,30) | partial: regime alias (R36, CHECKED there) | StockCharts KAMA (R35 §3.1, CHECKED there); LEAN built-in (CHECKED) |
| Hurst exponent | statistics | 1 | all | window 100 bars (INFERRED) | missing | LEAN built-in (CHECKED) |
| Variance ratio | statistics | 1 | all | horizons 2, 4, 8, 16 (INFERRED from the test's design) | missing | Lo and MacKinlay 1988, RFS (CHECKED abstract and working paper) |
| Choppiness index | statistics | 1 | all | period 14 (INFERRED) | partial: regime alias (R36, CHECKED there) | LEAN built-in (CHECKED) |
| Momersion (share of momentum vs mean-reversion steps) | statistics | 1 | all | window 20 (INFERRED) | missing | LEAN built-in (CHECKED) |
| Autocorrelation of returns | statistics | 1 | all | lag 1 | missing | Lo and MacKinlay working paper notes variance ratios are linear in autocorrelations (CHECKED) |
| Augmented Dickey-Fuller and half-life of a spread | statistics | 1 | all; pairs | window 100 bars (INFERRED) | missing | R36: ADF 169, OU and half-life 8 articles (CHECKED there) |
| Z-score of price or spread | statistics | 1 | all | window 20 (INFERRED) | missing | R36: 72 articles (CHECKED there) |
| Realised volatility estimators (Parkinson, Garman-Klass, Rogers-Satchell) | statistics | 1 | all | window 20 | partial: `realized-volatility` (`D`, CHECKED) | LEAN ships "Rogers Satchell Volatility" (CHECKED) |
| GARCH volatility forecast | model | 1 | all | GARCH(1,1) (INFERRED) | missing | R36: 29 screened articles (CHECKED there); 86 raw (section 1.1) |
| Two-state or three-state regime model (hidden Markov, Markov switching) | model | 1 (or 6 for macro inputs) | all | two states ("normal" and "event") | partial: `market-regime` "2/3/4-state ... unresolved" (`D`, CHECKED) | Kritzman, Page and Turkington 2012 found "a 'normal' and an 'event' regime" (FAJ, CHECKED) |
| Change-point detection (online) | model | 1 | all | hazard rate (INFERRED) | missing | his "HMM, BOCPD, MS, GARC" (`T1:1951` via funnel4 B057, CHECKED there) |
| Kalman filter (trend or hedge ratio) | model | 1 | all; pairs | noise settings | missing | R36: 14 articles (CHECKED there) |
| Cointegration of two instruments | statistics | 1 | pairs, intermarket | window | missing | R36: 44 articles (CHECKED there) |
| ARIMA forecast | model | 1 | all | (1,0,1) (INFERRED) | missing | LEAN built-in (CHECKED) |
| Option greeks and dealer positioning levels | context | 6 | IF, S, CP (options venues) | none | missing | LEAN ships Delta, Gamma, Vega, Theta, Rho (CHECKED); funnel4 B047 options as context only (CHECKED there) |

### 3.6 Exits and entries that appear only outside FX (names only)

Vocabulary names for the risk session to design or reject; no maths here.

| Name | Classes | Why it exists | Source |
| --- | --- | --- | --- |
| Exit before funding settlement | CP | avoid paying funding | INFERRED from Hyperliquid funding timing (CHECKED) |
| Exit or roll before contract expiry | F, IF, IC (expiring CFD futures) | positions expire; IC's futures CFDs expire early and are never rolled (STATE research 02 row, CHECKED) | CME roll course via R35 (CHECKED there) |
| Flat before the cash close or before the closing auction | S, IF | overnight gap and auction risk | NYSE auctions (CHECKED) |
| Flat before a scheduled report (EIA, earnings, gold auction) | E, S, M | jump risk at a known time | EIA and LBMA pages (CHECKED) |
| Exit at a distance from the estimated liquidation price | CP | liquidation before the stop | Hyperliquid liquidations doc (CHECKED) |
| Stop triggered on mark price instead of last price | CP, F | mark price drives liquidation and TP/SL on Hyperliquid | Hyperliquid robust prices (CHECKED) |
| Entry on the closing or opening auction (market-on-close order) | S | auction liquidity | NYSE auctions (CHECKED) |
| Entry at initial balance break | IF, S, E | market profile practice | Aspen (CHECKED) |

---

## 4. Same name, different meaning

| Word | Meaning by class | What the entry must carry | Source |
| --- | --- | --- | --- |
| **Volume** | Futures and stocks: traded contracts or shares. Crypto: traded coins per venue, with a taker split. FX and CFDs: tick count. | a `volume kind` tag; proxies flagged | section 2.1 |
| **Open interest** | Futures: end-of-day total, final next morning. Perps: live, 5-minute history. FX, stocks, CFDs: none. | clock and history depth | CME OI course; Binance OI doc (CHECKED) |
| **Session** | FX: liquidity waves in a 24/5 market. Futures: exchange hours with a daily break. Stocks: open, close, pre and post market. Crypto: no venue hours, 00:00 UTC bar boundary. The dictionary's own `trading-session` already calls this "a real semantic difference" (`D`, CHECKED). | per-class calendar, named clock | sections 3.4, 2.4 |
| **Rollover** | FX and CFDs: the daily swap charge at 5 p.m. New York, tripled on one weekday. Futures: moving from the expiring to the next contract. Some index CFDs: a dated CFD that expires. | two entries (carry charge, contract roll), never one | `rollover-swap-cost` (`D`, CHECKED); CME roll (CHECKED via R35) |
| **Swap vs funding** | FX swap: rate differential, broker-quoted, once a day. Perp funding: peer to peer, every 8 h or 1 h, from the perp-index premium. | separate entries | dictionary warning in `rollover-swap-cost` (CHECKED); Hyperliquid (CHECKED) |
| **Basis** | Index futures: future minus cash index, from rates minus dividends, falls to zero at expiry. Perps: perp minus index, held near zero by funding, never expires. Commodities: storage and supply (INFERRED). | per-class meaning | CME basis course (CHECKED); Hyperliquid funding (CHECKED) |
| **Settlement** | Futures: the exchange's daily settlement price and final settlement. Perps: funding settlement times. FX: value date (INFERRED). | per-class meaning | CME fair value pages (CHECKED) |
| **Gap** | Stocks and index cash: overnight gap at the open. Futures: only around the daily break and weekends. FX: weekend gap only. Crypto: no gaps on 24/7 venues except outages. | per-class "when can it happen" | INFERRED; `price-gap` exists (`D`, CHECKED) |
| **The open / the close** | Stocks and index cash: auction prices. Futures: session open after the break, settlement near the close. FX: 5 p.m. New York day turn, or whatever the broker's server uses. Crypto: 00:00 UTC by convention. | named clock and event | NYSE auctions; CME hours (CHECKED) |
| **Spread** | Bid-ask spread everywhere; in futures also a calendar spread between months; in pairs trading the price difference of two assets. | separate entries | INFERRED |
| **Liquidation** | Perps: forced closing by the exchange at the mark price, visible as public flow. FX and CFDs: the broker's stop-out on one account, private. Futures: margin call, private. | per-class meaning, visibility flag | Hyperliquid and Binance docs (CHECKED) |
| **Index price** | Perps: the spot reference used for funding (an oracle). Indices: the cash index itself. | per-class meaning | Hyperliquid (CHECKED); CME basis (CHECKED) |

**Entries to rewrite, not only extend.** `order-book-depth` ("Centralized exchanges only (crypto spot)"), `exchange-volume` ("crypto spot, futures, equities", correct but without the taker split), `footprint-order-flow` ("crypto spot, futures"), `trading-session` (24/7 heuristic only) and `centralized-futures-execution-context` ("Not the intended STRATS venue") were written for FX and crypto spot (`D`, CHECKED). Their market lines need the per-class rewrite above. INFERRED.

---

## 5. Statistics and models: parts or judging words?

The census found that 6 of the 10 most-cited missing concepts are judging words (R36 §3.1, CHECKED there). The ticket asks which statistics and models practitioners use as strategy parts. The evidence splits them cleanly.

**Used as parts (readings a unit computes and acts on):**
- Efficiency ratio, Hurst exponent, choppiness, Momersion, ARIMA, regression channel, realised-volatility estimators and option greeks are shipped as indicators in QuantConnect's engine, callable from any strategy like an RSI (LEAN supported indicators page, CHECKED).
- Kaufman's efficiency ratio drives KAMA's smoothing directly (R35 §4.1, CHECKED there): the statistic is inside an indicator.
- Markov-switching regime forecasts scaled exposure and beat static allocation out of sample (Kritzman, Page and Turkington 2012, CHECKED). Their note that "arbitrary thresholds give false signals" is the practitioner case for a model over a fixed cut-off (same page, CHECKED).
- The variance-ratio test measures whether a series trends or reverts over a horizon (Lo and MacKinlay 1988, CHECKED). Used as a reading, it answers his "which markets are mean-reverting at this timeframe" seed directly (`T1`, 28 Oct 17:49, CHECKED).
- His own MIS used HMM, change-point detection and Markov-switching GARCH (`T1`, 28 Oct 18:23, CHECKED). R43 already places these as versioned readings, one catalogue with the MIS (R43 §3.2, CHECKED).

**Used as judging words (never inside a unit's rules):** Sharpe, Sortino, profit factor, deflated Sharpe, PBO, walk-forward, cross-validation, Monte Carlo of results, expectancy as a verdict (R36 §2.2, CHECKED there). These go to the judging glossary that research 26 feeds.

**Both, depending on use.** Expectancy and win rate computed from a unit's own recent trades can drive its own sizing or switch it off (the "equity curve trading" family, R35 §4.1, CHECKED there). The vocabulary should hold one entry with two eligible uses, not two words. INFERRED.

**What a statistic needs that an indicator does not.** A window and a horizon (variance ratio at q), a sampling clock (bars, ticks, volume), a minimum sample before it is meaningful, and a stated lag. Research 15's skeptic found a mean-reversion state can take about 8 hours to show on 1-minute data (STATE research 15 row, CHECKED). INFERRED: each statistics entry carries "minimum sample" and "expected lag in bars" fields beside its settings.

---

## 6. Class packs: what each class needs before a unit can trade it

A pack is the smallest set of entries, instrument-record fields and data levels without which a unit on that class is blind or mis-costed. These are options. The order is his call (funnel4 Q40, R43 decision 4 recommends "FX, gold and index CFDs on cTrader first; perps second; futures and stocks later", CHECKED).

| Pack | Must have before any unit trades | Data levels | Already in the dictionary | Biggest gap |
| --- | --- | --- | --- | --- |
| **FX** | sessions with broker server time and DST, 5 p.m. New York day turn, swap and triple-swap day, news windows, tick-volume proxy flags | 0, 1 (tick-count), 2 | most of it (R36: sessions 86%, CHECKED there) | broker server time (R36: 115 articles) |
| **Gold and silver (CFD)** | FX pack plus the London auction windows, New York open, swap on longs, real yields and dollar index as context | 0, 1, 2, 6 | dollar index, safe-haven demand (`D`, CHECKED) | the auction windows |
| **Index CFDs** | cash open and close in the index's own clock, opening drive, overnight high and low, gap fill, initial balance, CFD dividend adjustments, CFD expiry (IC) | 0, 1 (tick-count), 2 | opening range, session open (`D`, CHECKED) | everything from futures and breadth is a proxy here |
| **Index futures** | index CFD pack plus the Globex break, RTH and ETH, front month and roll, settlement, fair value premium, real volume, market profile, and order flow where a tape exists | 0, 1v, 3p, 4, 5 (end of day) | volume profile, VWAP, footprint, delta (`D`, CHECKED) | roll and settlement; market profile |
| **Energy and other futures** | futures pack plus report clocks (oil Wednesday, gas Thursday), term structure, COT | 0, 1v, 5, 6 | none specific | the report clocks |
| **Stocks** | auctions, pre and post market, earnings and dividend dates, splits, halts, short-sale rule, relative volume, index membership | 0, 1v, 6 | none specific | corporate actions (QMB question Q44) |
| **Crypto spot** | 00:00 UTC day, weekend regime, maker and taker fees, venue choice, listings and delistings, taker split in bars | 0, 1 (taker split), 3p, 4 | `crypto-spot-execution-context` (`D`, CHECKED) | venue fragmentation |
| **Crypto perps** | crypto spot pack plus funding and its clock, mark vs index vs last, basis, OI and its change, liquidation estimate, margin mode, reduce-only, long/short ratios | 0, 1, 3p, 4, 5 | none | all of section 3.3 |

**Three orders, with what each costs** (options, not a choice):

| Order | For | Against |
| --- | --- | --- |
| A. Follow the doors he has: FX, gold, index CFDs on cTrader; then perps; then futures and stocks (R43 decision 4) | every early entry can be tested and traded at once | index CFD units read only proxies of the order flow he wants ("Order flow is good for scalpers ... especially now that I'm adding indices", via R35 §7, CHECKED there); the futures-native vocabulary waits |
| B. Futures-native first: build the index-futures pack as the "native" language and mark FX and CFD entries as adapted | matches his August view that most strategies come from futures traders (R39 GM 3262, CHECKED there); funnel4 B127 | futures execution door is not settled (research 38's job); data cost (STATE question 7 lists Databento at $199 a month, CHECKED) |
| C. Perps first among the new classes | free, deep public history for OI, depth bands, taker ratio and funding (section 2.3); Hyperliquid already in his plans (STATE 30 Oct seeds, CHECKED) | the 24/7 clock and funding change many old entries at once; liquidation data is sampled |

INFERRED: order A plus building the market-profile entries now (they run on bars and exchange-volume, and on CFDs as flagged proxies) would let index units start on cTrader without waiting for a futures door.

---

## 7. What this asks of other parts (pointers only, no design)

- **The instrument record (R43 F6)** needs, per instrument: the volume kind, the depth grade, the derivatives clock and history depth, the session clock and DST rule, report and auction clocks, the funding interval, the roll rule and the contract expiry. All facts in sections 2-4 have a home there or in the entry, never both (funnel4 B048, CHECKED there).
- **QMB** must refuse a test whose unit needs a data level the stored data lacks (funnel4 B052, R43 §3.2, CHECKED there), and must say when a reading's history is a provider sample (liquidations) or provider-limited (one-month OI through the API).
- **The MIS and research 23 / 37** may change which statistics run per class; this file only lists what practitioners use.
- **Research 33** decides what history is keepable; section 2.3 found the Binance archive is wider than the live API.

---

## 8. Questions practice does not settle

1. How well does order flow from index futures stand in for an index CFD's price? (Funnel4 Q41; still open. R35 §7 item 8, CHECKED there.)
2. One entry per meaning, or one entry with per-class meanings, for the twelve words in section 4? Both work; the first keeps entries short, the second keeps one name. Lead call.
3. Does a statistic's "minimum sample before it is meaningful" belong in the entry (fixed) or in the unit's binding (it depends on the bar length)? Lead call.
4. Should an exchange-only concept (market internals, auction imbalance) be allowed on a CFD unit as outside data, read from a feed QMX does not trade on? Data source is a research 33 / 38 question.
5. What counts as "the open" for a gold CFD: the London auction, the New York open, or the broker's day turn? Traders use all three (INFERRED); the vocabulary should name all three and let the unit pick.

## 9. Things any trader knows (stated, not asked)

- Futures have exchange volume and open interest; FX does not (R35 §2.2, CHECKED there).
- Funding and swap are carry costs, not signals, unless a unit chooses to read them as signals (R35 §2.2).
- Rising open interest with price confirms a trend; falling open interest warns it is tiring (CME OI course, CHECKED).
- The value area is about 70% of activity (TradingView, CHECKED).
- One imbalance is noise; three stacked is a zone (ATAS Learn, CHECKED).
- Stops on perps should consider the mark price, because liquidations use it (Hyperliquid, CHECKED).
- Stocks gap at the open; 24/7 crypto rarely gaps.

---

## 10. Sources read this session

Exchange and venue:
- https://www.cmegroup.com/education/courses/introduction-to-futures/open-interest
- https://www.cmegroup.com/education/courses/introduction-to-futures/what-is-volume
- https://www.cmegroup.com/market-data/volume-open-interest.html
- https://www.cmegroup.com/trading/equity-index/fairvalue.html
- https://www.cmegroup.com/education/courses/introduction-to-equity-index-products/what-is-equity-index-basis
- https://www.cmegroup.com/trading/equity-index/files/FVPremiums.pdf
- https://www.cmegroup.com/notices/clearing/2019/10/Chadv19-357.pdf (Globex hours and daily break)
- https://www.nyse.com/trade/auctions ; https://www.nyse.com/publicdocs/nyse/markets/nyse/NYSE_Opening_and_Closing_Auctions_Fact_Sheet.pdf
- https://www.ice.com/iba/lbma-precious-metals ; https://www.lbma.org.uk/prices-and-data/lbma-precious-metal-prices
- https://www.eia.gov/petroleum/supply/weekly/schedule.php ; https://www.eia.gov/reports/upcoming.php
- https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions-7 ; https://www.ecfr.gov/current/title-17/chapter-II/part-242/subject-group-ECFR1607681c7b4f78d/section-242.201 ; https://www.sec.gov/investor/alerts/circuitbreakersbulletin.htm
- https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding ; .../robust-price-indices ; .../liquidations
- https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Open-Interest-Statistics
- https://developers.binance.com/docs/derivatives/coin-margined-futures/websocket-market-streams/Liquidation-Order-Streams ; https://developers.binance.com/docs/derivatives (changelog)
- https://github.com/binance/binance-skills-hub/blob/main/skills/binance/binance/references/futures-usds.md (endpoint and enum list)
- https://github.com/binance/binance-public-data (archive columns)
- Binance public archive listing and two sample files, by command: `curl "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/futures/um/daily/"` and the `metrics` and `bookDepth` BTCUSDT files for 2026-10-01 (saved under the scratchpad's `bv-dl/`, not in the repo)

Platforms and practitioners:
- https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/supported-indicators
- https://help.atas.net/en/support/solutions/articles/72000606631-footprint-settings ; https://learn.atas.net/volume-basics/volume-analysis/imbalances ; https://learn.atas.net/volume-basics/volume-analysis/footprint-patterns ; https://learn.atas.net/volume-basics/atas-volume-core/l2-2-footprint-atas
- https://bookmap.com/knowledgebase/docs/Addons-Stops-And-Icebergs-On-Chart-Indicator ; https://bookmap.com/knowledgebase/docs/KB-Indicators-LLT ; https://bookmap.com/knowledgebase/docs/Addons-SIT ; https://bookmap.com/blog/bookmaps-stop-iceberg-sub-chart-with-mbo-data
- https://www.tradingview.com/support/solutions/43000713306-time-price-opportunity-tpo-indicator/
- http://www.aspenres.com/Documents/AspenGraphics4.0/Using_Market_profile.htm
- https://help.cqg.com/cqgic/26/Documents/marketprofilevalueareasmpva.htm
- https://info.tradovate.com/tpo-profile-charts
- https://ftmo.oanda.com/blog/market-profile-how-to-read-market-context-and-uncover-fair-value-zones/
- https://www.interactivebrokers.com/campus/glossary-terms/tick-trin-market-indicator/
- https://www.investopedia.com/terms/t/tickindex.asp ; https://www.investopedia.com/articles/trading/03/102203.asp (secondary; used only where a primary agrees)

Papers:
- https://doi.org/10.2469/faj.v68.n3.3 (Kritzman, Page, Turkington 2012)
- https://doi.org/10.1093/rfs/1.1.41 and https://rodneywhitecenter.wharton.upenn.edu/wp-content/uploads/2014/04/8705.pdf (Lo and MacKinlay)

Local:
- `C:/Users/Mubarak/Desktop/Stats/dictionary/` (README and the four family files)
- `MQ/*.md` (counts in section 1.1)
- `research/34`, `35`, `36`, `39`, `43`, `44`, `funnel4-qml/party-brainstorm/qml-field.md`, `STATE.md`, `operator/transcript-*.md`
