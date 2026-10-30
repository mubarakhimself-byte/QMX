# 32: The broker and instrument facts a unit must have checked

Ticket: `wayfinder/tickets/research-terrain-and-venues.md` (covers L05-01, L05-05, L05-12, L05-07, Q80). Written 2026-10-30 by research agent 3. Facts, field lists and options only. No risk percentages, no account sizes, no sizing maths (the risk session owns those).

## How to read this

- **CHECKED** = read today at the URL, file or command named. **INFERRED** = reasoned from checked facts. **SECONDARY** = a third-party page read today.
- This file fills the field list of research 43's foundation F6 ("one record per instrument per venue"). It does not design the record.
- Who gives which data and how QMX connects is research 38. History depth, data terms and disk are research 33. The node is research 31.
- "Terrain" was a brainstorming name, not a QMX word (STATE, 30 Oct). This file says "instrument facts".
- Every threshold below is a number: named, with a starting default, never settled here (standing order 5).

## 0. The short answer

1. **Half the facts come from the broker's API, a quarter from the broker's documents, and the rest must be measured.** The API gives lot sizes, steps, swaps, trading hours and holidays. Documents give expiry calendars and dividend schedules. Spread, commission paid, slippage and fill rates by hour can only be measured (the market journal in research 12 §5).
2. **cTrader's symbol record has no expiry field.** It carries lot size, minimum and step volume, swap, a weekly schedule, a holiday list, a trading mode (enabled, close-only, disabled) and a per-symbol maximum exposure (CHECKED `ProtoOASymbol` in the Spotware protocol file). An expiry can only reach a unit from the broker's documents or from a change of trading mode to close-only.
3. **IC Markets' futures CFDs are MT4/MT5 only, expire two working days before the underlying, go close-only a day or so earlier, are closed at the exchange settlement price, and are never rolled** (CHECKED IC futures page). The expiry table on that page still showed 2024 dates when read on 30 Oct 2026, so a document can be stale.
4. **MT5 gives what cTrader lacks:** a direct money-per-tick value, an expiration time, a freeze level and a margin calculator per order (CHECKED MQL5 `symbol_info` and the function list).
5. **Real futures facts come from the exchange.** CME Micro E-mini S&P 500: USD 5 times the index, tick 0.25 = USD 1.25, quarterly, last trade 08:30 CT on the third Friday, cash settled, daily price limits at 7, 13 and 20 percent (CHECKED CME rulebook chapter 353 and the micro fact card).
6. **Perps have no expiry, but funding every hour (Hyperliquid) or every 8, 4 or 1 hours (Binance, per symbol).** Live read today: Binance declares 465 symbols on 4-hour funding, 353 on 8-hour, 2 on 1-hour (CHECKED `fapi/v1/fundingInfo`). The interval is a per-symbol fact, not a class constant.
7. **Venue limits move.** Binance's BTCUSDT minimum order value read live today is 50 USDT; a library's example from May said 5 (CHECKED live `fapi/v1/exchangeInfo`; SECONDARY example). Hyperliquid perps need at least USD 10 per order (CHECKED error list). The record must be refreshed from the venue, never typed in once.
8. **Rationed order actions exist on several venues and are visible in different ways:** Hyperliquid by traded volume per address; Binance by order counts per 10 seconds and per minute; IBKR by pacing rules; cTrader by 50 requests a second per connection. A unit learns them from the venue rules row of its instrument record, and from the venue's own counters where they exist (§4).

---

## 1. The field list, per instrument per venue

One row per fact. "Where from" says which source owns it. "Refresh" is how often it changes (each cadence is a number with a starting default).

### 1.1 Identity

| Field | Meaning | Where from | Refresh | Source |
| --- | --- | --- | --- | --- |
| venue, broker, account type, environment | Which broker, which account kind (Raw, Standard, netting or hedging), demo or live | Account record | On change | cTrader `ProtoOAAccountType` HEDGED / NETTED / SPREAD_BETTING (CHECKED OpenApiModelMessages.proto line 252-255) |
| venue symbol id and name | The venue's own id; ids differ per server | API | On change | `ProtoOASymbol.symbolId` "Different servers have different IDs" (CHECKED proto) |
| class | FX, metal, index CFD, futures CFD, real future, stock CFD, crypto spot, perp, HIP-3 perp, quarterly crypto future | Derived | Once | INFERRED |
| underlying link | What it tracks (US500 CFD ↔ ES/MES; XAUUSD ↔ GC/MGC; HIP-3 `xyz:GOLD` ↔ gold) | Document, then checked by measuring the basis | Once, then measured | INFERRED; basis question D-02 in `live-field.md` |
| base, quote, margin, settle currency | Needed for money per point in account currency | API | On change | cTrader base and quote asset ids; MT5 `currency_base`, `currency_profit`, `currency_margin` (CHECKED); Binance `marginAsset` (CHECKED live) |
| measurement units | e.g. ounces, barrels, shares, coins | API | On change | cTrader `measurementUnits` field 40 (CHECKED) |

### 1.2 Contract and order size

| Field | Meaning | Where from | Source |
| --- | --- | --- | --- |
| contract size (lot size) | Units per 1 lot or 1 contract | API | cTrader `lotSize` in cents (field 30); MT5 `trade_contract_size`; CME rulebook (USD 5 × index for MES); Hyperliquid 1 unit of the underlying (all CHECKED) |
| minimum volume, step, maximum | Smallest order, size increment, largest order | API | cTrader `minVolume`, `stepVolume`, `maxVolume` in cents; MT5 `volume_min`, `volume_step`, `volume_max`; Binance `LOT_SIZE` and `MARKET_LOT_SIZE`; Hyperliquid `szDecimals` (CHECKED) |
| minimum order value | Smallest notional the venue accepts | API or error list | Binance `MIN_NOTIONAL` (50 USDT on BTCUSDT, 20 on ETHUSDT, live today); Hyperliquid USD 10 for perps, 10 quote tokens for spot (CHECKED https://hyperliquid.gitbook.io/Hyperliquid-docs/for-developers/api/error-responses) |
| maximum order value | Largest single order | Document | Hyperliquid: USD 30M market order for max leverage ≥ 25, down to USD 500k; limit orders 10× (CHECKED contract-specifications page) |
| maximum exposure per symbol per account | A cap the broker enforces | API | cTrader `maxExposure` field 12, "Blocks execution if breached" (CHECKED) |
| price digits and tick size | Price precision | API | cTrader `digits`, `pipPosition`; MT5 `trade_tick_size`, `point`; Binance `PRICE_FILTER.tickSize` (0.10 on BTCUSDT live); Hyperliquid at most 5 significant figures and 6 − `szDecimals` decimals for perps (CHECKED tick-and-lot-size page) |
| price band per order | Orders too far from the reference are refused | API | Binance `PERCENT_PRICE` ±3% on BTCUSDT (live); Hyperliquid "order too far from reference price" pre-validation (CHECKED error list); CME daily limits (rulebook 353) |

### 1.3 Money per point (the fact the risk socket needs most)

| Field | Meaning | Where from | Source |
| --- | --- | --- | --- |
| money per tick, per lot, in quote currency | Tick size × contract size, or the exchange's tick value | API or exchange spec | MT5 gives it directly: `trade_tick_value`, with separate `trade_tick_value_profit` and `trade_tick_value_loss` (CHECKED example: EURJPY 0.8977 profit vs 0.8978 loss). CME: MES USD 1.25, MNQ USD 0.50, M2K USD 0.50, MYM USD 0.50 per tick (CHECKED CME FAQ) |
| conversion to account currency | Quote → account currency, live | API | cTrader `ProtoOASymbolsForConversionReq` (CHECKED message exists in OpenApiMessages.proto); MT5 tick value is already in deposit currency (INFERRED from the EURJPY example in a USD-valued figure) |
| conversion fee | Fee on P&L when quote ≠ deposit asset | API | cTrader `pnlConversionFeeRate`, 1 = 0.01% (CHECKED field 34) |
| quanto | P&L in one currency, settled in another | Document | Hyperliquid: USDT oracle, USDC collateral, no conversion applied (CHECKED contract-specifications) |

**Hard case (INFERRED):** cTrader has no tick-value field, so the money per point at cTrader is computed: lot size × tick size × conversion rate. A wrong conversion symbol gives a plausible but wrong size. MT5 gives the number directly, and its profit and loss values differ slightly.

### 1.4 Margin

| Field | Meaning | Where from | Source |
| --- | --- | --- | --- |
| account leverage | Account-wide leverage | API | cTrader `leverageInCents` (1:50 = 5000) (CHECKED field 10 of the trader model) |
| dynamic leverage tiers | Leverage that falls as size grows | API | cTrader `leverageId` → `ProtoOAGetDynamicLeverageByIDReq`, tiers in `ProtoOADynamicLeverageTier` (CHECKED proto) |
| expected margin for a size | Exact margin before sending | API | cTrader `ProtoOAExpectedMarginReq`; MT5 `order_calc_margin`, `order_check` (CHECKED) |
| exchange margin, intraday vs overnight | Futures: low intraday at the broker, full exchange margin to hold overnight | Broker document | NinjaTrader: USD 50 intraday for micro index futures, USD 500 for E-minis, initial margin needed 15 minutes before the session close to carry (CHECKED https://ninjatrader.com/pricing/). CME exchange margins not read today |
| perp margin tiers | Max leverage by notional; maintenance = half the initial at max leverage | API (`meta`) and document | Hyperliquid BTC 40× up to USD 150M then 20×; ETH 25× then 15×; others listed (CHECKED margin-tiers page); live `meta` today: BTC `maxLeverage` 40, ETH 25, SOL 20, PAXG 10 (CHECKED POST `/info` type `meta`) |
| isolated only | Some markets allow only isolated margin | API | Hyperliquid HIP-3 live today: `xyz:HOOD`, `xyz:PLTR`, `xyz:COIN` `onlyIsolated: true` (CHECKED `/info` `meta` with `dex: "xyz"`) |
| stop-out rule | Which position the broker closes first | API | cTrader `stopOutStrategy`, default MOST_MARGIN_USED_FIRST (CHECKED field 22) |
| liquidation price basis | Mark price, not the book | Document | Hyperliquid (research 02 §8.1, CHECKED 27 Oct) |

### 1.5 Trading hours and calendar

| Field | Meaning | Where from | Source |
| --- | --- | --- | --- |
| weekly schedule and time zone | Open intervals in the symbol's time zone | API | cTrader `schedule` (seconds from Sunday 00:00) and `scheduleTimeZone` (CHECKED fields 13, 26) |
| holidays | Closed days per symbol | API | cTrader `holiday` list (field 33); error 69 `SYMBOL_HAS_HOLIDAY` (CHECKED) |
| exchange session and halts | e.g. CME Globex 17:00-16:00 CT Sunday-Friday | Exchange | CME micro fact card (CHECKED); a 15:15-15:30 CT halt per a broker page (SECONDARY TradeStation) |
| trading mode now | Enabled, close-only, disabled with or without pending execution | API, plus change events | cTrader `ProtoOATradingMode` (CHECKED proto line 222-226); `ProtoOASymbolChangedEvent` exists (CHECKED message) |
| underlying-closed mode | HIP-3 perps on a closed stock market price off their own book | Document | research 02 §8.2 (CHECKED 27 Oct) |
| broker server time and daylight saving | IC server GMT+2/+3 | Document | research 02 §1 (CHECKED 27 Oct) |

### 1.6 Costs and carry

| Field | Meaning | Where from | Source |
| --- | --- | --- | --- |
| commission type and rate | Per million, per lot, percent | API | cTrader `commissionType`, `preciseTradingCommissionRate`, `preciseMinCommission` (CHECKED fields 15, 31, 32) |
| spread by hour | Live spread distribution per hour of week | **Measured** | Market journal, research 12 §5 |
| swap long and short, triple day, time, period | Daily (or intraday) financing | API | cTrader `swapLong`, `swapShort`, `swapRollover3Days`, `swapCalculationType` (pips or annual percent), `swapPeriod`, `swapTime`, `chargeSwapAtWeekends` (CHECKED fields 6-8, 29, 36-39); MT5 `swap_long`, `swap_short`, `swap_rollover3days` (CHECKED) |
| swap-free fee | Admin fee for swap-free accounts | API | cTrader `rolloverCommission`, `skipRolloverDays` (CHECKED fields 24, 25) |
| funding interval and history | Perps carry | API | Hyperliquid hourly (CHECKED contract-specifications); Binance per symbol via `fundingInfo` (465 at 4 h, 353 at 8 h, 2 at 1 h today, CHECKED live) with cap and floor per symbol (SECONDARY field list, https://dereckscompany.github.io/binance/reference/BinanceFuturesData.html) |
| funding now | Current rate and open interest | API | Hyperliquid BTC today: funding 0.0000125 per hour, open interest 40,415 BTC, mark 77,706, oracle 77,726 (CHECKED `metaAndAssetCtxs`) |
| dividend adjustments | Index and stock CFDs pay or charge dividends | Document | IC indices page: cash adjustment per lot on the ex-date, long credited, short debited (CHECKED) |
| exchange, clearing, routing, data fees | Futures | Document | AMP: Rithmic routing USD 0.10 per side, MES all-in USD 0.60 per contract at AMP (CHECKED https://commissions.ampglobal.com/exchange-traded-futures-price-quote) |
| fee tier | Venue fee tier by volume | API, document | Hyperliquid 14-day volume tiers (research 02 §8.1, CHECKED 27 Oct) |
| measured slippage, fill latency, rejection rate | Per hour, from all units' fills | **Measured** | Market journal (research 12 §5.1) |

### 1.7 Ending: expiry, roll, delisting

| Field | Meaning | Where from | Source |
| --- | --- | --- | --- |
| expiry and last trade time | When the contract ends | Exchange or broker document; MT5 field; Binance field | CME: 08:30 CT on the third Friday, quarterly (CHECKED); MT5 `expiration_time` (CHECKED field in `symbol_info`); Binance `deliveryDate` (live today: `BTCUSDT_261225` CURRENT_QUARTER, `BTCUSDT_270326` NEXT_QUARTER; perps carry a far-future placeholder 4133404800000, CHECKED); **cTrader: no field** (CHECKED by `grep -i expir` on the model proto: only order expiry) |
| close-only date | When new opens stop | Broker document; cTrader trading-mode change | IC table "Close Only Date" a working day or so before expiry (CHECKED IC futures page) |
| what happens at expiry | Closed at settlement, rolled, or delivered | Document | IC: closed at the exchange settlement price, not rolled (CHECKED); CME micro: cash settled to the Special Opening Quotation (CHECKED); some brokers auto-roll futures CFDs (SECONDARY https://www.financemagnates.com/forex/isam-securities-adds-futures-cfds-as-volatility-raises-demand-for-consistent-pricing/) |
| next contract | The symbol that replaces it | Document, naming pattern | IC names such as `VIX_F4`, `WTI_H4` (CHECKED) |
| customary roll date | When liquidity moves | Exchange | CME roll Monday before the third Friday (research 02 §7.1, CHECKED 27 Oct) |
| delisting state | Market removed | API | Hyperliquid `isDelisted`: 56 of 235 perps listed in `meta` today are delisted (CHECKED live) |
| corporate actions | Stock CFD terminated or adjusted | Document | research 02 §6 (CHECKED 27 Oct) |

### 1.8 Rules on orders

| Field | Meaning | Where from | Source |
| --- | --- | --- | --- |
| minimum stop and target distance | How close a stop may sit | API | cTrader `slDistance`, `tpDistance`, `distanceSetIn` (CHECKED fields 16, 17, 20); MT5 `trade_stops_level`, `trade_freeze_level` (CHECKED) |
| guaranteed stop availability and fee | Broker-guaranteed stops | API | cTrader `guaranteedStopLoss`, `gslDistance`, `gslCharge` (CHECKED fields 5, 18, 19) |
| short selling allowed | Some symbols cannot be shorted | API | cTrader `enableShortSelling` (CHECKED field 4) |
| order types and time in force | What the venue accepts | API | Binance `orderTypes`, `timeInForce` per symbol; Hyperliquid ALO, IOC, GTC, triggers, TWAP (research 02 §8.1); MT5 `filling_mode`, `expiration_mode`, `order_mode` (CHECKED) |
| reduce-only and trigger rules | Rejections near the open-order cap | Document | Hyperliquid: with 1,000+ open orders, new reduce-only and trigger orders are rejected (CHECKED rate-limits page) |
| maximum open orders | Per symbol or per account | API, document | Binance `MAX_NUM_ORDERS` 200 per symbol (live today); Hyperliquid 1,000 default, up to 5,000 (CHECKED) |

### 1.9 Rationed order actions (venue rules row)

| Venue | What is rationed | Visible how | Source |
| --- | --- | --- | --- |
| Hyperliquid | Actions per address: 1 per USDC traded since inception plus 10,000; then 1 per 10 s; cancels get `min(limit + 100000, 2 × limit)`; block space in congestion by maker share | A per-user rate-limit read on the info endpoint (INFERRED from SDKs, not read today); a stale `expiresAfter` cancel costs 5× | CHECKED rate-limits page; exchange endpoint page |
| Binance USD-M | Request weight 2,400 a minute; orders 1,200 a minute and 300 per 10 s | `rateLimits` in exchangeInfo (live today); usage headers (INFERRED, not read) | CHECKED live `fapi/v1/exchangeInfo` |
| cTrader | 50 requests a second, 5 for history, per connection | Error on breach (INFERRED) | CHECKED https://help.ctrader.com/open-api/ |
| IBKR | Historical pacing (60 small-bar requests per 10 minutes, etc.), data lines | Error messages | CHECKED IBKR market data page |
| Tradovate | One connection per customer | Oldest dropped | CHECKED https://api.tradovate.com/ |

### 1.10 Data available on this venue

The data levels (0 calendar to 6 outside data) per class and venue are in research 38 §4. The record carries which levels exist and the licence for each (research 33 §3).

---

## 2. Per class: which fields matter most, and the hard cases

| Class | Fields that change most often | Hard cases |
| --- | --- | --- |
| FX CFDs | Spread by hour; swap; triple-swap day | Rollover spread spike at 17:00 New York; weekend gaps; quote currency ≠ account currency |
| Metals CFDs | Spread; swap; daily break | Contract size per broker differs (100 oz assumed, INFERRED); session break 23:59-01:02 server (research 02 §1) |
| Index CFDs (cash) | Dividend adjustments; daily breaks per index | Points per lot differ per index and broker (IC AUS200 example: 1 contract = AUD 1 per point, CHECKED); dividend debits on shorts |
| Futures CFDs (IC MT5) | Expiry and close-only date; next symbol | **Never rolled**; positions closed at settlement; the broker's calendar page can be stale (2024 table seen 30 Oct 2026, CHECKED) |
| Real futures | Front contract; roll; intraday vs overnight margin; daily limits | Expiry at 08:30 CT; price limit halts; margin jump 15 minutes before close (NinjaTrader, CHECKED); data entitlement ends at month end (AMP: not prorated, CHECKED) |
| Stock CFDs (IC MT5) | Exchange hours; dividends; corporate actions | Earnings gaps; termination on corporate actions; MT5 only |
| Crypto spot | Filters; fees in base asset | Dust below the minimum notional cannot be closed (research 02 §9.1, INFERRED) |
| Perps (Hyperliquid, Binance) | Funding (per symbol interval), leverage tiers, minimum notional, address budget | Funding sign flips each interval; liquidation by mark price; venue limits change (Binance BTCUSDT min notional 50 today, CHECKED) |
| HIP-3 perps | Isolated only on some; underlying-closed pricing | Weekend discovery bounds; snap back at reopen (research 02 §8.2) |
| Quarterly crypto futures (Binance) | `deliveryDate` | Expire at delivery like real futures (CHECKED `CURRENT_QUARTER` rows) |

---

## 3. Expiry and roll: how they reach a unit that holds through them

### 3.1 The cases

| # | Case | What the venue does | How the unit can know | Source |
| --- | --- | --- | --- | --- |
| E1 | Cash CFD (FX, index, metal) | Never expires; swap and dividends | No expiry field needed | CHECKED IC pages |
| E2 | Broker futures CFD, not rolled (IC MT5) | Close-only date, then closed at the exchange settlement price, about a day after expiry | MT5 `expiration_time`; IC's calendar page; the naming pattern | CHECKED IC futures page; MT5 field |
| E3 | Broker futures CFD, auto-rolled (other brokers) | Rolled with a price adjustment | Broker document only | SECONDARY iSAM article |
| E4 | cTrader futures-style CFD at any broker | Same as E2 or E3 | **No expiry field**; only a `tradingMode` change to close-only and `ProtoOASymbolChangedEvent` | CHECKED proto |
| E5 | Real exchange future | Last trade 08:30 CT third Friday (MES); cash settled | Exchange calendar; Binance `deliveryDate` style field at crypto venues | CHECKED CME |
| E6 | Perp | Never expires; funding each interval | Funding interval field per symbol | CHECKED Binance `fundingInfo`, Hyperliquid spec |
| E7 | Quarterly crypto future | Delivers at `deliveryDate` | API field | CHECKED live exchangeInfo |
| E8 | Delisting | Market closes; positions settled | Hyperliquid `isDelisted`; exchange notice | CHECKED live `meta` |
| E9 | Stock CFD corporate action | Terminated or adjusted | Broker notice | research 02 §6 |

### 3.2 What a unit holding through it needs (INFERRED; options, not a design)

Which exit a unit takes at expiry is an exit-set question for the risk session (research 43 F6 says so). What this run must leave room for:
- **The instrument record carries the ending.** Expiry, close-only date, settlement rule, rolled or not, next symbol, roll date.
- **The trading machine keeps a snapshot** so a unit sees the ending with the Library down (43 F6, review E08).
- **QMB replays the ending.** A backtest that holds an IC futures CFD past its close-only date must see the forced close at settlement, or results come out better than live (INFERRED from the IC rule).
- **Continuous history must say how it was stitched** (research 12 §3 item 11). A unit trained on a back-adjusted series and trading the real contract sees different price levels.

Numbers to name (starting defaults, editable):

| Number | Starting default | Why that start |
| --- | --- | --- |
| `ending_warning_days`: trading days before close-only when the record flags the instrument | 3 | IC's close-only date sits one working day before expiry, which sits two before the underlying (CHECKED); 3 gives a margin for a stale calendar (INFERRED) |
| `calendar_max_age_days`: how old a broker calendar may be before it is marked suspect | 31 | One monthly futures cycle (INFERRED) |
| `roll_source`: where the roll date comes from | exchange calendar | CME publishes it (research 02) |

---

## 4. How a unit learns it is on a venue that rations order actions

Options (not a choice), each on the three tests of standing order 6:

| Option | How | Hard cases | Maintain | Explain |
| --- | --- | --- | --- | --- |
| R1. Static rule in the venue row | The instrument record's venue row carries the rule ("1 action per USDC traded, cancels extra") | Misses the live budget left | One table | "The record says this venue rations orders" |
| R2. Static rule plus a live counter | R1 plus the feed keeper reads the venue's own counter (Hyperliquid per-user limit read; Binance usage headers) into the market journal | Handles running low mid-session | One reader per venue | "The record says how many orders you may send, and a gauge shows how many are left" |
| R3. Learn from rejections only | Count rate-limit errors | Finds out too late, often mid-exit | Simple | "We find out when the venue says no" |

INFERRED: R2 is the only option that passes the hard case of a unit needing its last cancels during a fast market (Hyperliquid deliberately leaves cancel headroom for this, CHECKED rate-limits page). Whether the unit itself adapts its order pattern to the gauge is a unit-design question, not this file's.

---

## 5. The small-account facts (minimum position, money per point, margin)

The risk session works out what a small account can trade. These are the venue facts it needs. Numbers are the vendors'; arithmetic is marked INFERRED.

| Instrument @ venue | Minimum position | Money per point (or tick) at the minimum | Margin at the minimum | Source |
| --- | --- | --- | --- | --- |
| EURUSD @ IC cTrader | 0.01 lot = 1,000 EUR (research 02 S3, S7) | USD 0.10 per pip (INFERRED: 1,000 × 0.0001) | Read from `ProtoOAExpectedMarginReq`; depends on account leverage | research 02 §1 (CHECKED 27 Oct); proto CHECKED today |
| XAUUSD @ IC | 0.01 lot (contract size per broker, commonly 100 oz, INFERRED) | About USD 0.01 per USD 0.01 move at 1 oz (INFERRED) | Same request | research 02 §1 |
| AUS200 @ IC | 1 contract = AUD 1 per point (CHECKED IC example); minimum lot read from `minVolume` | AUD 1 per point per contract | Same request | CHECKED IC indices page |
| VIX futures CFD @ IC MT5 | 1 contract = USD 0.01 per point, 100 points per 1.00 (CHECKED IC example) | USD 0.01 per point | Up to 1:200 leverage (CHECKED) | CHECKED IC futures page |
| MES @ CME via an FCM | 1 contract | USD 5 per index point, USD 1.25 per tick | NinjaTrader intraday USD 50; overnight = exchange initial margin (not read today) | CHECKED CME rulebook 353; NinjaTrader pricing |
| MNQ, M2K, MYM @ CME | 1 contract | MNQ USD 2/point (0.50/tick); M2K USD 5/point (0.50/tick); MYM USD 0.50/point (0.50/tick) | NinjaTrader USD 50 intraday for micro index futures | CHECKED CME FAQ, micro fact card |
| BTC perp @ Hyperliquid | USD 10 notional; size step 0.00001 BTC (`szDecimals` 5) | 1 unit = 1 BTC; at USD 10 notional a 1% move is about USD 0.10 (INFERRED) | Notional ÷ chosen leverage, max 40× (CHECKED live `meta`) | CHECKED |
| `xyz:GOLD` HIP-3 @ Hyperliquid | USD 10; `szDecimals` 4; max 25× | 1 unit of gold oracle price | Isolated rules per market | CHECKED live `meta` dex `xyz` |
| BTCUSDT perp @ Binance | 0.001 BTC step and 50 USDT notional (live today) | 0.001 BTC per step | By leverage bracket (not read today) | CHECKED live exchangeInfo |

INFERRED observation for the risk session (fact, not a recommendation): the smallest money-per-point steps are the FX and metal CFDs at 0.01 lot and Hyperliquid's USD 10 minimum. A micro future's smallest step (USD 1.25 per tick on MES, USD 0.50 on the others) is fixed by the exchange and cannot be made smaller.

---

## 6. Where each fact comes from: the summary

| Source | Facts | Refresh |
| --- | --- | --- |
| Broker or venue API | Identity, sizes, steps, digits, swaps, commission rates, schedule, holidays, trading mode, max exposure, leverage tiers, margin estimates, funding, open interest, filters, `deliveryDate`, delisting | Starting default: daily, plus on every change event (`ProtoOASymbolChangedEvent` on cTrader) |
| Broker documents | Futures CFD expiry tables, dividend schedules, close-only dates, auto-roll rules, server time, which platform lists which product | Starting default: weekly check, plus `calendar_max_age_days` |
| Exchange documents | Contract specs, last trade time, settlement, price limits, roll calendar, margins | Starting default: monthly, plus each contract cycle |
| Measured (market journal) | Spread by hour, slippage, fill latency, rejection rate, quote gaps, basis between proxy and traded market | Continuous, rolled per bucket (research 12 §5) |
| His account | Account type (hedging or netting), leverage, deposit currency | On change |

---

## 7. Questions

| Id | Question | Tag |
| --- | --- | --- |
| T-01 | Does IC Markets publish a current futures CFD expiry calendar anywhere other than the stale page? | research |
| T-02 | What is the minimum volume and points-per-lot for US500 and other index CFDs on his own cTrader account? (read `ProtoOASymbol` on demo) | research (lead can run on demo) |
| T-03 | How large and steady is the basis between CME index futures and IC index CFDs per minute? (D-02 in `live-field.md`) | research (needs data) |
| T-04 | Which margin rules apply to his account (leverage, dynamic tiers)? | research (demo read) |
| T-05 | Is the account hedging or netting, and does any unit design assume one? | lead |
| T-06 | Does Hyperliquid's per-user rate-limit read give the remaining budget a unit can use? (read its info endpoint docs) | research |
| T-07 | Does a reduce-only close of a remainder under USD 10 pass Hyperliquid's minimum? (not stated in docs, SECONDARY cotrading.io) | research |

## 8. Not verified

CME exchange margins; Binance leverage brackets and usage headers; IC Markets FX contract specs re-read today (taken from research 02, checked 27 Oct); MGC and MCL specs; Hyperliquid's per-user rate-limit info read.
