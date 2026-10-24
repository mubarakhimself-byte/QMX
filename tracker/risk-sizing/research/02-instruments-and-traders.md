# 02: Instruments and what their traders need

Written 2026-10-24 for the Wayfinder ticket `wayfinder/tickets/instruments-and-trader-needs.md`. Research only. Nothing here is ratified.

The lens is production QMX trading real instruments. Sources are live venue, exchange, broker and regulator pages read on 2026-10-24, plus QMX code and docs.

## How to read this

- **CHECKED (Sn):** read today in source Sn (list at the end), or in QMX code at the cited path.
- **PRACTITIONER (Sn):** a trader, educator or vendor says it. It is not a primary rule.
- **INFERRED:** my reading or arithmetic. Test it before building on it.
- Every number is an example from a named venue on a named date. In QMX each one is a configurable value read from the venue or the operator, never a hardcoded rule.
- "Router" means the MIS as a load balancer (seeds.md): it places a unit on markets, sessions and states where that unit has proof.

## Short answer

1. **Each class differs in four places:** how costs arrive, how time works, what data exists, and how the contract ends. The router and QMB must model all four per instrument. Today they model mostly FX.
   - **How costs arrive:** spread plus commission, daily swap, hourly funding, or exchange fees. A dividend cash adjustment also counts.
   - **How time works:** 24/5 with a daily break, 24/7, exchange sessions with halts, or an expiry calendar.
   - **What data exists:** tick volume only, broker L2 depth, full exchange tape, open interest and funding, or options greeks.
   - **How the contract ends:** never (spot and CFD), at expiry (futures and futures CFDs), or as a perp that never expires but charges funding.
2. **IC Markets on cTrader cannot trade IC's stock CFDs.** IC lists its 2,100+ stock CFDs on MT5 only (CHECKED S11). A stock-scalper unit at IC needs the MT5 path.
3. **Hyperliquid is more than crypto.** HIP-3 deployments list perps on stocks, equity indices, commodities and FX that trade 24/7, with special weekend pricing (CHECKED S37, S36). "Hyperliquid first" therefore also means "24/7 stock and gold perps", with their own edge cases.
4. **Hyperliquid limits a scalper's order traffic by its traded volume.** It allows 1 action per 1 USDC traded since the address opened, plus a starting buffer of 10,000 (CHECKED S32). A bot that quotes and cancels a lot can run out of requests. This is a router input, not only a venue detail.
5. **On IC's cTrader CFDs, order-flow scalping only half works.** The cTrader Open API has a Level-2 depth book but no time-and-sales tape (CHECKED `docs/components/ctrader.md`). Footprint, delta and absorption need the tape, so they belong to futures, perps and spot crypto. Best-quote imbalance (OFI, S48) needs only quote sizes, so it can run on cTrader depth.
6. **Backend today:**
   - **cTrader:** reads symbols, quotes, bars, positions and account state.
   - **CCXT:** spot only. It refuses every contract market, so it has no perps, no funding and no open interest.
   - **QMB:** models commissions, synthetic spreads, FX slippage and daily swap.
   - **Missing:** funding, expiry and roll, dividend adjustments, per-instrument session calendars beyond forex-17NY and always-open, and order-flow indicators. All CHECKED, paths in §10.
7. **The 9 scalper types** (verdict in §11):
   - **Keep 5:** momentum, mean reversion, volatility expansion, session-open/ORB, VWAP.
   - **Change 3:** the order-flow sniper splits by data type; liquidity window and funding become router axes, not types.
   - **Drop 1:** cross-venue latency.
   - **Add 2:** the liquidity-sweep reversal and the passive maker scalper.
   - **Add 1 guard:** martingale and grid detection, as a guard rather than a type.

---

## 1. One-screen comparison

| Class (example venue) | Size and steps | Main costs | Time | Ends | Volume data | Depth / tape |
|---|---|---|---|---|---|---|
| FX CFD (IC Raw) | 1 lot = 100,000 base, down to 1,000 units (S3, S7) | Raw spread + $3.50/lot/side on MT, or $3 per $100k per side on cTrader (S2, S1); daily swap, triple on Wednesday (S3) | 24/5; server GMT+2/+3; break 23:59–00:01 server (S5, S6) | Never (cash CFD, S13) | Tick volume only (S17) | cTrader L2, no tape (ctrader.md) |
| Spot metals CFD (IC) | Per-broker `lotSize` (INFERRED: commonly 100 oz) | Spread + commission (S4); swap, triple Wednesday (S3) | 01:02–23:59 server (S5) | Never | Tick volume | cTrader L2 |
| Index CFD, cash (IC) | Per-broker point value (S9) | Spread only, no commission (S9); financing, triple Friday (S3); dividend adjustments (S9) | Near 24/5 with daily breaks per index (S5) | Never | Tick volume | cTrader L2 |
| Commodity CFD, spot and futures-based (IC) | Per contract (S8) | Spread; swap (energies triple Friday, S3) | Daily breaks, e.g. Brent 00:59–03:00 server (S5) | Futures CFDs expire 2 working days before the underlying; not rolled (S10) | Tick volume | cTrader L2 |
| Stock CFD (IC, MT5 only) | 1 contract = 1 share (S11) | Spread/commission; financing; dividends (S11) | Exchange hours (S13) | Never; corporate actions can terminate (S55) | MT5 real volume if the broker feeds it (S17) | Broker-specific |
| Exchange futures (CME ES/MES) | ES $50 × index, tick 0.25 = $12.50; MES $5, tick $1.25 (S18, S19) | Exchange + broker fees; data fees (S23, S24) | Sun–Fri 5pm–4pm CT with a daily break (S21) | Quarterly; terminates 8:30 CT on the 3rd Friday; cash-settled (S18, S21) | Real volume | Full DOM + tape (paid) |
| Crypto perp (Hyperliquid) | 1 unit; `szDecimals`; price ≤5 significant figures (S27, S29) | Taker 0.045% / maker 0.015% at tier 0 (S28); hourly funding (S26) | 24/7 | Never; funding instead (S27) | Real trade volume | L2 20 levels; public trades (S35) |
| HIP-3 perp (xyz: stocks, indices, gold, FX) | Per market, e.g. `xyz:TSLA` max 10×, strict isolated (S36) | Fees (growth mode can cut them 90%+, S28); funding (S37) | 24/7, but the oracle switches to internal pricing when the underlying is closed (S37, S38) | Never | Real | L2 |
| Spot crypto (via CCXT; Binance, HL spot) | Filters: tick size, step size, min notional (S41) | HL spot 0.07% / 0.04% at tier 0 (S28) | 24/7 | Never | Real | L2 + trades |
| Options (Deribit; MT5 can model them) | 1 BTC per contract, min 0.1 (S44) | Venue fees | 24/7 (Deribit) | Daily/weekly/monthly expiry at 08:00 UTC; European, cash-settled (S44) | Real | L2; IV and greeks |

---

## 2. FX (spot FX CFDs)

### 2.1 Contract mechanics
- **Lot.** Each pair's swap is quoted per 1.0 lot = 100,000 base units. CHECKED (S3).
- **Smallest size.** Lots go as small as 1,000 units (a micro lot). CHECKED (S7).
- **The venue gives the exact rules.** cTrader gives `minVolume`, `stepVolume`, `maxVolume`, `lotSize` (all in cents), `pipPosition`, `digits` and `maxExposure`. CHECKED (S15). MT5 gives `SYMBOL_VOLUME_MIN/STEP/MAX/LIMIT`, `SYMBOL_TRADE_TICK_SIZE/VALUE` and `SYMBOL_TRADE_CONTRACT_SIZE`. CHECKED (S16).
- **Commission at IC Raw.**
  - MetaTrader: USD 3.50 per lot per side (USD 7.00 round turn). CHECKED (S2).
  - cTrader: USD 3 per USD 100,000 traded per side. Example: 1 lot EURUSD at 1.30 → 1.31 costs USD 7.83 round turn. CHECKED (S1, S4).
  - Commission applies to FX and metals only. CHECKED (S4).
- **cTrader commission types.** USD per million, USD per lot, percentage of value, and quote currency per lot, plus a minimum commission. CHECKED (S15).
- **Spread.** IC states a EURUSD Raw average of 0.1 pips. CHECKED (S14). INFERRED: on EURUSD at about USD 10 per pip per lot, the MT commission of USD 7 round turn is about 0.7 pips. All-in cost is then about 0.8 pips per round turn.
- **Swap.**
  - Charged in points per lot at the start of the next trading day. CHECKED (S3, S4).
  - Tripled on Wednesday night for FX, metals, bonds and commodity CFDs. CHECKED (S3).
  - The reason is T+2 spot settlement across the weekend, applied at 17:00 New York. CHECKED (S2).
  - cTrader exposes `swapLong`, `swapShort`, `swapRollover3Days`, `swapCalculationType` (pips or annual %), `swapPeriod`, `swapTime`, `skipSWAPPeriods` and `chargeSwapAtWeekends`. CHECKED (S15).
- **Swap-free accounts** pay a dated administrative fee instead: `rolloverCommission`, with its own triple day. CHECKED (S15; `docs/components/ctrader.md`).
- **Leverage.** Varies by entity and is a configurable value.
  - IC's global site (Raw Trading Ltd, FSA) says "up to 1:5000" for FX. CHECKED (S7, 2026-10-24).
  - ESMA retail rules cap majors at 30:1 and other pairs at 20:1. They require a margin close-out at 50% of initial margin and negative balance protection. CHECKED (S54).
  - cTrader can carry tiered "dynamic leverage" by position size. CHECKED (S15).
- **Hours.** IC quotes all pairs 00:01–23:59 server time (Friday 23:57). Server time is GMT+2, or GMT+3 under US daylight saving. CHECKED (S5, S6). INFERRED: server midnight is therefore 17:00 New York all year, so the daily gap is the NY rollover.
- **Settlement.** Cash-settled CFD. No currency is delivered. CHECKED (S13).
- **True deliverable spot FX** is a bank, ECN or prime-broker product, out of reach of a retail API. INFERRED. In QMX "spot FX" should mean "CFD on the spot rate" unless a venue says otherwise.

### 2.2 Data FX traders use, and what exists
- **No central volume.**
  - MT5 bars carry `tick_volume` (quote updates) and `real_volume`. CHECKED (S17).
  - For OTC instruments real volume may be missing, or it reflects only one broker's or LP's flow. PRACTITIONER (S62, S63).
- **cTrader trendbars carry a tick count.** QMX's adapter labels it `volume_unit: "ticks"`. CHECKED (`qmx-agents/packages/qmx-broker/src/qmx_broker/adapters.py:134-135`).
- **Depth.** cTrader offers a Level-2 resting-liquidity book with differential updates. It has no Level-3 book and no time-and-sales. CHECKED (`docs/components/ctrader.md`, "Depth and connectivity"). INFERRED: this is IC's LP aggregate, not the whole market.
- **Tick history.** cTrader history is BID or ASK selectable, capped at one week per request. CHECKED (ctrader.md).
- **Free deep history.** Dukascopy publishes free tick data (CHECKED S57) with bid and ask prices and volumes per tick. It is free for personal use and may not be redistributed. PRACTITIONER (S58).
- **Session structure.** Trading concentrates in the UK (38% of turnover) and the US (19%). Singapore is at 11.8% and Hong Kong at 7.0%. CHECKED (BIS 2025, S46). Activity and volatility move together and spreads narrow when activity is high. Overlap hours carry outsized activity. CHECKED (EBS data, S47).

### 2.3 Tools and how complex strategies get
- **Common tools.** Moving averages, RSI, Bollinger Bands, ATR stops, session high/low ranges, pivots, round numbers, and an economic calendar. PRACTITIONER (S59).
- **Retail "smart money" concepts** are widely used on FX and gold: liquidity pools, sweeps, fair-value gaps, order blocks. PRACTITIONER (S59).
- **Complexity ladder.** INFERRED from the sources above:
  - one-timeframe rules
  - multi-timeframe bias (H1/H4 context, M1/M5 entry; S59)
  - session-conditioned rules (Asian range, London open)
  - currency-strength baskets and cross-pair stat-arb
  - ML on engineered features
- Order flow is weak on FX CFDs because there is no tape (§2.2).

### 2.4 Scalper and intraday styles, and what each needs from the router
- **London/NY open breakout and momentum.** Needs: an active session (overlap hours, S47), a spread ceiling, and expanding volatility.
- **Asian-range mean reversion.** Needs: quiet hours, a tight two-sided spread, stable volatility, and no change-point. INFERRED, supported by S47's quiet Tokyo-afternoon pattern.
- **Liquidity sweep.** The London open sweeps the Asian range, closes back inside, and the bot enters on the retest. PRACTITIONER (S59). Needs: the session range levels marked before the window, a live window (e.g. 07:00–09:30 UTC in S59), and no high-impact news 30 minutes either side.
- **Router inputs** (INFERRED; each value configurable per unit):
  - **Cost ratio:** round-trip cost ÷ unit's average target, at or below the unit's proven ceiling. For example, 0.8 pips ÷ 5 pips = 16% on IC EURUSD.
  - **Live spread ÷ normal spread:** the SQS ratio. The current design blocks below a configurable threshold (report 09 §A.8).
  - **Session window flag** from the venue schedule, not a hardcoded clock.

### 2.5 Edge cases that break FX bots
- **Daily rollover.** The 23:59–00:01 server gap is closed to trading (CHECKED S5). PRACTITIONER: spreads widen around it.
- **Triple-swap Wednesday** (S3). A "scalper" that holds over the rollover pays three days.
- **Weekend gap.** Friday close 23:57 server, Monday open 00:01 (S5).
- **Server-time shift on US daylight-saving dates** (S6). Any clock-based window must come from the venue schedule.
- **Holidays.** cTrader returns `SYMBOL_HAS_HOLIDAY` (error 69) and a per-symbol holiday list. CHECKED (S15).
- **Stop distance minimums.** cTrader `slDistance`/`tpDistance` → `PROTECTION_IS_TOO_CLOSE_TO_MARKET` (129). MT5 `SYMBOL_TRADE_STOPS_LEVEL`/`FREEZE_LEVEL`. CHECKED (S15, S16).
- **Exposure caps.** `MAX_EXPOSURE_REACHED` (119) and `TOO_MANY_POSITIONS` (124). CHECKED (S15).
- **Partial fills and LP rejects.** Deal status can be `PARTIALLY_FILLED`, `REJECTED` (no liquidity) or `MISSED` (no LP response in time). CHECKED (S15).
- **Account-currency conversion.** Commission is converted to the deposit currency at spot. CHECKED (S1). `pnlConversionFeeRate` applies when the quote asset differs from the deposit asset. CHECKED (S15).
- **News spikes.** INFERRED: spreads widen and fills slip. The news kill switch already exists (seeds.md).

---

## 3. Metals (spot gold, silver, platinum, palladium CFDs)

### 3.1 Mechanics
- **Leverage at IC global.** Gold up to 1:2000, silver 1:1000, platinum and palladium 1:500. CHECKED (S8). ESMA retail cap for gold: 20:1. CHECKED (S54).
- **Commission and swap.** Commission applies (S4). Swap tripled on Wednesday (S3).
- **Contract size per lot** comes from the symbol record (`lotSize`, `SYMBOL_TRADE_CONTRACT_SIZE`). INFERRED: 100 oz per lot is common but not universal, so read it per broker.
- **Hours.** IC trades gold 01:02–23:59 server (Friday close 23:57). CHECKED (S5). The daily break is about one hour, longer than FX's two minutes.
- **Gold futures CFD.** IC also lists one (GCZ26_CFD) with start, close-only and expiry dates (close-only 23/11/2026, expiry 25/11/2026). CHECKED (S10).

### 3.2 Data
- **OTC tick volume only.**
- **Benchmark auctions.** The LBMA Gold Price is set by auctions at 10:30 and 15:00 London time. CHECKED (S56). PRACTITIONER: avoid entries in the fix windows (S59, Quantum Algo).
- **Volume proxy.** INFERRED: COMEX gold futures volume and depth are a real-volume proxy for gold CFD bots, if QMX buys CME data (§7.2).

### 3.3 Tools, styles and router needs
- **London open and NY open windows dominate gold scalping.** PRACTITIONER (S59: sweep of the Asian range, 07:00–09:30 UTC; "live session" 06:00–09:00 and 13:00–16:00 UTC).
- **Gold is a "stop-collecting" market.** Sweeps typically revert to mid-range within 30–90 minutes in a live session, and fail in dead hours. PRACTITIONER (S59, goldhunts).
- **Router needs.** INFERRED:
  - a session window from the venue schedule
  - a fix-window blackout, configurable from LBMA times
  - a spread ceiling, because gold spreads swing far more than EURUSD
  - a news blackout (CPI, NFP, FOMC)

### 3.4 Edge cases
- The one-hour daily break (S5), so stops cannot fill during it. INFERRED.
- The fix auctions (S56).
- Contract size differs between brokers, so a unit proven on one broker's XAUUSD needs a value-factor check before it moves to another. INFERRED; QMX already refuses when the value factor is missing (`docs/components/qmf-venue.md`).

---

## 4. Index CFDs (cash indices)

### 4.1 Mechanics
- **IC terms.** 25 indices, leverage up to 1:200, no commission. Spreads as low as 0.4 in one listing. The US500 table shows min 0.2 and average about 0.49 points. CHECKED (S9).
- **ESMA retail cap:** 20:1 for major indices, 10:1 for others. CHECKED (S54).
- **Hours with daily breaks**, per index (CHECKED S5):
  - US500 trades 01:00–23:59 server, break 23:59–01:00.
  - AUS200 has two breaks.
  - HK50 has three sessions.
  - DE40 has a one-minute break at 03:15–03:16 server.
- **Financing.** Indices pay financing with a triple charge on Friday, not Wednesday. CHECKED (S3).
  - An older IC sheet gives the formula as stake × price × (benchmark rate ± 250 bp) ÷ 360 or 365. CHECKED but stale (S64, 2014). Treat the rate as broker-supplied.
- **Dividend adjustments.**
  - When constituents go ex-dividend, longs are credited and shorts debited. CHECKED (S9).
  - US index long credits are net of withholding tax (15% with a treaty and W-8BEN), while short debits are gross. CHECKED (S9).
  - cTrader books these as `BALANCE_DEPOSIT_DIVIDENDS` and `BALANCE_WITHDRAW_DIVIDENDS`. CHECKED (S15).
- **Out-of-hours quotes.** IC quotes some indices when the reference futures are closed. Those quotes are built from flow, peers, news and other markets, with more slippage. CHECKED (S64, older sheet). INFERRED: such prices are synthetic and should be a separate session state.

### 4.2 Data
- CFD tick volume only.
- The real volume and tape live in the reference futures (ES, NQ, FDAX), which are paid data (§7.2).
- Cash-open timing (09:30 New York for US indices) matters more than the CFD's 23-hour schedule. INFERRED from S49 and S50, which both key off the cash open.

### 4.3 Tools, styles and router needs
- **Opening-range breakout and intraday momentum.** Rule: a "noise area" built from the average move from the open at each time of day over the prior 14 days. The bot trades breaks of it on half-hour checks with a VWAP trailing stop. CHECKED as research (S50, on SPY 2007–2024: Sharpe 1.33 net of costs as reported).
- **Router needs:**
  - a cash-session window keyed to the underlying exchange
  - a dividend calendar
  - a halt and limit state (see 4.4)
  - a gap-from-prior-close measure. S50 widens its bands by the overnight gap.

### 4.4 Edge cases
- **Underlying halts.** ES futures halt at the 7% and 13% index declines and stop for the day at 20%. CHECKED (S18). INFERRED: index CFDs freeze or gap with them.
- **Dividend cash events** land as balance operations, not trades, so an accounting fold that ignores them misstates P&L. INFERRED.
- **Triple financing on Friday** (S3).
- **Synthetic out-of-hours pricing** (S64).
- **Per-index daily breaks** (S5).

---

## 5. Commodity CFDs (energies, softs; spot and futures-based)

### 5.1 Mechanics
- **IC range.** More than 22 commodity CFDs, spot and futures-based. Softs leverage up to 1:100. Wheat example: 4 bushels per contract. CHECKED (S8).
- **Futures CFDs expire two working days before the underlying contract.** Open positions close at the exchange settlement price, usually the day after expiry. They are **not rolled**: a holder must reopen on the next contract. CHECKED (S10).
- **IC publishes start, close-only and expiry dates per contract.** Example: WTI_Z6 starts 13/10/2026, close-only 15/11/2026, expiry 16/11/2026. CHECKED (S10).
- **Spot energies** (XTIUSD, XBRUSD, XNGUSD) are also listed. Energies take triple swap on Friday. CHECKED (S8, S3).
- **Hours.** Brent futures CFD breaks 00:59–03:00 server on Tuesday–Friday. WTI breaks 00:00–01:00. CHECKED (S5).
- **Expiry fields by platform.**
  - MT5 has `SYMBOL_START_TIME`, `SYMBOL_EXPIRATION_TIME` and trade mode "close only". CHECKED (S16).
  - cTrader's `ProtoOASymbol` field list has **no expiry field**, only `schedule`, `holiday` and `tradingMode`. CHECKED by reading the field list (S15).
  - INFERRED: on cTrader, expiry must come from the broker's published table, the symbol name or a close-only `tradingMode`.

### 5.2 Data, styles and router needs
- Tick volume only on CFDs. Real volume and open interest are in the futures (NYMEX, ICE; paid). INFERRED.
- **Router needs.** INFERRED:
  - an expiry and close-only state per symbol
  - a "front contract" link so a unit's registry proof follows the contract chain
  - scheduled-report blackouts, e.g. weekly inventory data (not checked)

### 5.3 Edge cases
- **The close-only phase.** New entries are rejected. The router must stop placing the unit there.
- **Forced close at settlement.** A gap to settlement is possible.
- **New symbol per contract month** (WTI_X6 → WTI_Z6). A naive registry keyed on symbol loses the unit's history.
- **Long daily breaks** (S5).

---

## 6. Stock CFDs

### 6.1 Mechanics
- **IC lists 2,100+ stock CFDs** (ASX, NYSE, NASDAQ) **only on MT5**. One contract equals one share, and a one-point move is USD 1 per contract. CHECKED (S11).
- **Hours.** Only during the exchange's open hours (or narrower hours IC sets). CHECKED (S13).
- **Financing and dividends** both apply. IC's own example text says long positions are credited interest and shorts debited. CHECKED as written (S11). INFERRED: verify the sign per broker, since most brokers charge longs.
- **cTrader brokers may charge equities as `PERCENTAGE_OF_VALUE`.** cTrader also has an `enableShortSelling` flag and error `SHORT_SELLING_NOT_ALLOWED` (136). CHECKED (S15).
- **ESMA retail cap:** 5:1 for individual equities. CHECKED (S54).
- **Corporate actions**, using one broker's published rules as the example (CHECKED S55):
  - cash dividends → cash adjustment
  - splits and stock dividends → position adjustment
  - spin-offs and mergers → new CFD, cash, or termination
  - if no fair adjustment exists, the CFD is closed before the ex-date at the closing price
  - IC's EU cost policy reportedly charges nothing for corporate actions. Seen only in a secondary copy, not checked first-hand.

### 6.2 Data
- **Real exchange volume exists for the underlying.** Whether the CFD feed carries it is broker-specific: MT5 `real_volume`, and `SYMBOL_CHART_MODE` Bid vs Last. CHECKED (S16, S17).
- **Scanning "stocks in play"** needs relative volume (RVOL) across a universe at the open. CHECKED as research method (S49).

### 6.3 Styles and router needs
- **5-minute ORB limited to stocks in play.** These are stocks with abnormal activity, mostly from news. Across 7,000+ US stocks in 2016–2023, the top-20 portfolio reported a Sharpe of 2.81 net of costs. CHECKED as research claim (S49). Re-test before trusting it.
- **Router needs.** INFERRED:
  - an RVOL-at-open selector across the universe
  - an earnings and corporate-action calendar
  - an exchange-session calendar per listing
  - a short-sell availability flag

### 6.4 Edge cases
- Overnight gaps at the open.
- Earnings.
- Exchange halts: LULD pauses. INFERRED, not checked here.
- Ex-dividend price drops.
- Short selling disabled per symbol (S15).
- Position adjustments after splits change the unit's quantity outside its own orders (S55).
- IC: no cTrader route (S11).

---

## 7. Exchange futures (CME micro and E-mini)

Not offered through IC. QMX would need a futures broker (NinjaTrader, Rithmic or CQG-routed FCMs). INFERRED from S23 and S24.

### 7.1 Mechanics
- **E-mini S&P 500 (ES).** USD 50 × index. Tick 0.25 = USD 12.50 (0.05 for calendar spreads). CHECKED (S18).
- **Micro E-mini (MES).** USD 5 × index. Tick 0.25 = USD 1.25. CHECKED (S19).
- **Other micros** (CHECKED S20):

  | Contract | Multiplier | Tick | Tick value |
  |---|---|---|---|
  | MNQ | USD 2 | 0.25 | USD 0.50 |
  | MYM | USD 0.50 | 1.00 | USD 0.50 |
  | M2K | USD 5 | 0.10 | USD 0.50 |

- **Contract cycle.** Five quarterly contracts (March, June, September, December). The expiring contract stops trading at 8:30 a.m. CT on the third Friday and is cash-settled to the Special Opening Quotation. CHECKED (S18, S21).
- **Roll date.** CME's customary roll is the Monday before the third Friday, e.g. 14 December 2026 for the 18 December 2026 expiry. CHECKED (S22). A practitioner page says "8 days before, on Thursday". PRACTITIONER and stale (S61). Treat the roll date as calendar data from CME.
- **Hours.** Sunday–Friday 5:00 p.m.–4:00 p.m. CT with a daily maintenance break (S21 via the broker table in the search result; CME's micro launch spec also lists a 3:15–3:30 p.m. halt; older). Read hours from the exchange calendar, not code.
- **Price limits.** 7%, 13% and 20% downside halts. Overnight the band is ±7% around a reference price. CHECKED (S18).
- **Orders above 2,999 contracts** must be split into several entries. CHECKED (S21).

### 7.2 Data
- **What futures give.** Real centralized volume, full depth (DOM) and time-and-sales. This is the best data of any class for order flow. INFERRED from the products in S25 and S23.
- **It costs money.** Example monthly non-professional fees via CQG: CME top of book USD 2, CME depth USD 13, CME bundled depth USD 41. CHECKED (S23, October 2026).
  - A retail FCM lists USD 17 per exchange for depth and USD 45 for the CME depth bundle. Fees are not prorated. CHECKED (S24).
  - Professional status costs about USD 145 per exchange via CQG. CHECKED (S23).
- **Open interest and settlement data** come from the exchange. INFERRED; MT5 also exposes `SYMBOL_SESSION_INTEREST` and the settlement price. CHECKED (S16).

### 7.3 Tools and complexity
- **NinjaTrader Order Flow+** (CHECKED S25):
  - volumetric bars (footprint: bid and ask volume per price, delta, imbalance at a default diagonal ratio of 1.5)
  - cumulative delta
  - market depth map
  - trade detector
  - volume profile
  - order-flow VWAP
- **Practitioner futures scalpers** read DOM and tape: absorption, icebergs (refilling size at one price), stacked imbalances and pace of trade. PRACTITIONER (S60).
- **Complexity ladder.** INFERRED:
  - price-action ORB and VWAP
  - volume profile and value areas
  - footprint and delta
  - DOM and queue dynamics
  - market-by-order microstructure models

### 7.4 Styles and router needs
- **Cash-open ORB and momentum on ES/NQ** (S50 basis).
- **VWAP reversion.**
- **Absorption and iceberg scalps at structure.** PRACTITIONER (S60).
- **Router needs.** INFERRED:
  - the front contract and roll state
  - a data entitlement check (does this node have depth or tape?)
  - a price-limit state
  - session (RTH versus overnight)

### 7.5 Edge cases
- **Roll.** Liquidity moves to the next contract (S22).
- **Expiry.** Trading stops at 8:30 CT (S18).
- **Limit-down halts** (S18).
- **The daily maintenance break.**
- **Margins differ intraday and overnight.** Broker-specific; not checked.
- **Data entitlements end at month end.** Fees bill a full month (S24).

---

## 8. Crypto perpetual futures (Hyperliquid first)

### 8.1 Mechanics
- **Contract.** Linear perps, 1 unit of the underlying, collateral in USDC. The oracle is in USDT for most assets with no USDC/USDT conversion, so the contracts are technically quanto. No expiry: funding instead. CHECKED (S27).
- **Funding.**
  - Paid every hour at 1/8 of a computed 8-hour rate.
  - Formula: F = average premium + clamp(interest − premium, −0.05%, +0.05%).
  - The interest part is 0.01% per 8 hours (about 11.6% APR paid to shorts).
  - The premium is sampled every 5 seconds from impact prices.
  - The cap is 4% per hour.
  - Payment = size × **oracle** price × rate.
  - It is peer-to-peer: the exchange takes no cut.
  - All CHECKED (S26).
- **Margin.**
  - Initial margin = size × mark ÷ chosen leverage.
  - Leverage runs from 1 to the asset's maximum (3–40×), with margin tiers.
  - Maintenance margin is half the initial margin at max leverage (1.25%–16.7%).
  - Modes: cross, isolated and strict isolated.
  - Leverage is checked only on open.
  - All CHECKED (S30, S31).
- **Liquidation.**
  - Market orders go to the book first.
  - Positions above USD 100k liquidate 20% at a time, with a 30-second cooldown.
  - Below 2/3 of maintenance, the liquidator vault takes the position over and the maintenance margin is lost.
  - Liquidation runs off the mark price, not the book.
  - All CHECKED (S31).
- **Fees.** Rolling 14-day volume tiers; spot volume counts double. CHECKED (S28).
  - Tier 0: taker 0.045%, maker 0.015%.
  - Above USD 500M: maker 0%.
  - Maker rebates of up to −0.003% go to heavy maker share.
- **Tick and lot rules.**
  - Prices: at most 5 significant figures and at most 6 − `szDecimals` decimals. Integers are always valid.
  - Sizes: rounded to `szDecimals`.
  - All CHECKED (S29).
- **Order caps.** Maximum market order value is USD 30M for assets with max leverage ≥25, scaling down to USD 500k for low-leverage assets. The limit-order cap is 10× that. CHECKED (S27).
- **Order types.** Market, limit, stop and take (market or limit), trailing stop, TWAP (30-second slices, 3% max slippage), scale, and Chase (browser only). Options: post-only (ALO), reduce-only, GTC. CHECKED (S33).
- **Rate limits** (CHECKED S32):
  - **Per IP:** 1,200 weight per minute. `l2Book` costs weight 2; most info calls cost 20.
  - **Websocket:** 10 connections, 1,000 subscriptions, 2,000 messages per minute.
  - **Per address:** 1 action per 1 USDC traded cumulatively, plus a 10,000 starting buffer. Once limited, 1 request per 10 seconds.
  - **Cancels** get extra headroom.
  - **Open orders:** a default of 1,000 per user.
- **Via QMX's connector.** CCXT supports Hyperliquid for funding rate, funding history and the user's funding history. CHECKED (S43). CCXT's market structure carries `contract`, `linear`/`inverse`, `contractSize`, `settle` and `expiry`. CHECKED (S42).

### 8.2 HIP-3 perps on stocks, indices, commodities and FX
- **What they are.** HIP-3 deployments (e.g. trade[XYZ], dex `xyz`) list linear USDC perps on stocks, equity indices, commodities, FX and pre-IPO names. HyperCore does matching, funding and liquidations. The deployer supplies the oracle, mark and external prices. CHECKED (S37).
- **Examples from the official API.** `xyz:XYZ100` max 20×; `xyz:TSLA` and `xyz:NVDA` max 10×; all strict isolated, growth mode enabled. CHECKED (S36).
- **When the underlying is closed** (nights, weekends, holidays):
  - The oracle follows the perp's own book through a smoothed 30-minute window.
  - "Discovery bounds" limit moves to about 1 ÷ max leverage per band (±5% at 20×), re-anchoring a limited number of times.
  - Funding uses a 0.5 multiplier.
  - PRACTITIONER and secondary (S38 Hyperdash docs; S39 Messari). The primary trade.xyz pages describe the same split (S37).
- **Do weekend prices predict Monday?** Evidence is contested. Messari reports 94.9% direction accuracy on moves above 100 bp (S39). Orcas finds the Sunday 8pm price beat Friday's close only 49.9% of the time (S40). Both secondary.

### 8.3 Data, and what is free
- **Live (free):**
  - L2 book, at most 20 levels per side, optionally aggregated by significant figures. CHECKED (S35).
  - Public trades over websocket. INFERRED from S32/S35.
  - Funding, open interest, premium, oracle, mark, mid and impact prices per asset (`metaAndAssetCtxs`). CHECKED (S36).
  - Funding history (S32 lists `fundingHistory`).
- **History limits.**
  - The candle API returns only the most recent 5,000 candles. CHECKED (S35). INFERRED: 5,000 one-minute bars is about 3.5 days, so QMX must record its own bars and ticks from day one.
  - An S3 archive holds hourly L2 snapshots and asset contexts, uploaded about monthly with no timeliness guarantee. The requester pays transfer. CHECKED (S34).
  - Fills by block are on a separate bucket. CHECKED (S34).
- **Intraday patterns in crypto.**
  - Volume and volatility run higher in US/EU equity hours and lower on weekends. CHECKED as research (S53).
  - Activity, volatility and illiquidity peak at 16:00–17:00 UTC across 38 exchanges. CHECKED as research (S52).
  - Spikes at 00, 08 and 16 UTC line up with CEX funding times. CHECKED as research (S51). Hyperliquid's own funding is hourly (S26).

### 8.4 Tools and complexity
- **Tools.** The same TA tools as other markets, plus funding rate, open interest change, basis (perp versus oracle/spot), liquidation levels, CVD from trades, and order-book imbalance. INFERRED from the data in 8.3; the OFI basis is S48.
- **Complexity ladder.** INFERRED:
  - rules
  - multi-timeframe
  - order flow and OFI
  - funding and basis carry
  - cross-venue stat-arb
  - ML on order-book features

### 8.5 Styles and router needs
- **Momentum and breakout in peak liquidity hours** (S52).
- **Mean reversion in quiet hours.** INFERRED.
- **OFI and order-flow scalps.** Real trades and depth exist, so they work here. INFERRED, basis S48.
- **Passive maker scalps that earn the spread and rebates.** CHECKED fee schedule (S28) and post-only order type (S33).
- **Router needs.** INFERRED:
  - fee tier, taker versus maker
  - **remaining address request budget** (S32)
  - funding level and its next payment time
  - maximum leverage and margin tier for the size
  - for HIP-3: external versus internal session state and the discovery bounds

### 8.6 Edge cases
- **Funding sign flips.** Funding can change sign every hour and is charged on the oracle notional (S26). A position held across the hour pays it.
- **Liquidation runs off the mark price**, which can differ from the book in fast markets (S31).
- **Liquidation before the stop.** A stop above the liquidation price is mandatory. INFERRED; S31 recommends stops.
- **Running out of address-based requests** (S32).
- **Post-only periods during network upgrades.** TWAP slices and market orders do not fill then. CHECKED (S33).
- **Quanto P&L.** USDT-priced, USDC-settled (S27).
- **HIP-3 weekend discovery bounds and the snap back to the external price at the reopen** (S38).
- **Price precision rejects** (S29).
- **Order-value caps** (S27).

---

## 9. Spot crypto and options

### 9.0 Crypto CFDs at the FX broker (a different product from perps)
- **IC terms.** IC quotes crypto CFDs 7 days a week, but some symbols are unavailable at weekends. Leverage under Raw Trading: BTCUSD/ETHUSD up to 1:500 on MetaTrader, 1:300 on cTrader and TradingView, 1:300 above 50 BTC net. No commission. CHECKED (S12).
- **Costs.** They carry a daily swap, tripled on Friday (S3) or "over the weekend" (S13). They pay no funding.
- **Contract size.** Default 1 coin, as low as 0.1. CHECKED (S13).
- INFERRED: a unit proven on Hyperliquid BTC is not proven on IC BTCUSD. Costs, hours, data and price source all differ, so each needs its own registry entry and proof.

### 9.1 Spot crypto (via CCXT)
- **Order rules come from exchange filters.** Binance example (CHECKED S41):
  - `PRICE_FILTER` (tick size)
  - `LOT_SIZE` and `MARKET_LOT_SIZE` (min, max, step)
  - `NOTIONAL`/`MIN_NOTIONAL` (e.g. a 10 minimum). For market orders it is checked against an average price over `avgPriceMins`.
- **CCXT normalizes these** into `precision` and `limits`, flags `spot`/`contract` and `feeSide`. CHECKED (S42).
- **QMX's spot validator** enforces step, min and max, and notional. CHECKED (`packages/qmf-venue/src/qmf/venue/spot.py`).
- **Fees.** Hyperliquid spot tier 0 is taker 0.070% / maker 0.040%. CHECKED (S28). Report 09 records that 0.1% per side ate about 0.89R per trade in a 5 Oct simulation. CHECKED (report 09, Job E).
- **24/7, no leverage, no funding.**
- **Data.** Real trades and depth from each venue. History varies by venue; free public archives exist for some (not checked).
- **Edge cases.**
  - Fees taken in the base asset shrink the position. INFERRED from CCXT `feeSide` (S42).
  - Dust below the minimum notional cannot be closed. INFERRED.
  - Exchange maintenance windows.
  - Stablecoin depegs (INFERRED).
  - The weekend liquidity drop (S53).

### 9.2 Options
- **IC Markets lists no options.** Its product menu: forex, commodities, indices, synthetic indices, bonds, crypto, stocks and futures CFDs. CHECKED (S10, S11).
- **MT5 can model options.** It has fields for strike, call/put, option type and greeks (delta, gamma, theta, vega, rho, omega). CHECKED (S16).
- **CCXT carries `option`, `strike` and `optionType`.** CHECKED (S42).
- **Deribit BTC options** (CHECKED S44):
  - European, cash-settled in BTC, 1 BTC per contract, minimum 0.1 contract.
  - Tick 0.0001 BTC up to a price of 0.005, then 0.0005.
  - Expiries daily at 08:00 UTC. Delivery price = TWAP of the index from 07:30 to 08:00 UTC.
  - Long options pay the premium in full.
- **Data.** Implied volatility and greeks come from the venue or the platform. INFERRED; MT5 fields are S16.
- **Scalping fit.** Options are rarely scalped directly. Their intraday uses are gamma scalping (hedging) and event-volatility trades. INFERRED. Recommendation: keep options behind spot, CFDs and perps in QMX's order.

---

## 10. What QMX's backend supports today (CHECKED, read-only)

Worktree `D:\QMX-worktrees\agent-system` at `70d181fb`, and `C:\Users\Mubarak\Desktop\QMX\docs\components`.

| Area | What exists | Path |
|---|---|---|
| Instrument identity | Opaque `(venue, symbol)` pair; the symbol is never parsed. Asset class lives in registry records. | `packages/qmf-core/src/qmf/core/identity.py:269-310` |
| cTrader read adapter | Symbol list and full `ProtoOASymbol` pass-through (swap, commission and schedule fields arrive raw, not normalized); account state with `moneyDigits` scaling; positions; spot quotes; trendbars with `volume_unit: "ticks"` | `qmx-agents/packages/qmx-broker/src/qmx_broker/adapters.py:36-176` |
| cTrader live client | Live client with a depth wire kind; volume in cents decoding | `qmn/src/qmn/venue/live.py:142-165, 231, 290` |
| cTrader facts (docs) | L2 depth yes, tape no; 50 + 5 requests/sec; one-week tick span; three numeric scale systems; per-broker measured D1 boundary; swap-free accounts still pay rollover commission | `docs/components/ctrader.md` "Venue facts", "Depth and connectivity" |
| Venue capability surface | Margin surface declared but "V1 deliberately does not size by margin"; value factor only from venue metadata, refuse if absent; settlement currency must match the Book at bind time | `docs/components/qmf-venue.md` "Capability discovery" |
| CCXT adapter | **Spot only.** `_market()` refuses anything not `spot is True and contract is False and active is True`. Positions are reported as `market_type: "spot"`. | `qmx-agents/packages/qmx-broker/src/qmx_broker/adapters.py:177-250`; `packages/qmf-venue/src/qmf/venue/spot.py:68-93` |
| Broker permissions | Accounts allow `read` and `propose` only; orders are market or limit proposals | `qmx-agents/packages/qmx-broker/src/qmx_broker/models.py` (`Account.permissions`, `OrderProposal`); `service.py:164-171` |
| Spot paper account | Paper spot account for crypto | `qmn/src/qmn/venue/spot_paper.py` |
| QMB commissions | Zero, percent of notional, per lot, per 1k units; per-broker calibration; partial fills carry their own commission | `qmb/src/qmb/execution/cost.py` |
| QMB financing | Daily swap as a scheduled cash event; triple day and weekend handling from a per-broker calibration; rate content deferred to GAP-0048; a missing swap table is a refusal | `qmb/src/qmb/execution/financing.py:1-11` |
| QMB spread and slippage | Synthetic spread per instrument × hour × session from calibration; an "FX slippage catalog" | `qmb/src/qmb/execution/spread.py`, `slippage.py` |
| Calendars | Gap check knows `forex-17NY` and `AlwaysOpenCalendar` (24/7) only | `qmb/src/qmb/data/gap_check.py:43-75` |
| Indicators | A TA-Lib-referenced set incl. SMA, EMA, RSI, ATR, MACD, VWAP, Stoch, ADX, BBANDS, OBV, CCI | `packages/qmf-indicators/src/qmf/indicators/` |
| Order-flow features | **None found.** QML's `footprint` is a data-consumption manifest, not an order-flow footprint | `qml/src/qml/footprint/__init__.py:1-8` |
| Funding, expiry, dividends | **None found.** "funding" has 0 hits in `packages/`, `qmb/`, `qml/`, `qmn/` source; "futures" has 0; `perp` hits are false positives ("hyperparameter") | grep, 2026-10-24 |

INFERRED gaps for "trade anything a broker offers":
1. **An instrument-spec record per (venue, symbol)**, normalized from `ProtoOASymbol`, MT5 symbol properties and CCXT markets. It should hold:
   - contract size and value factor, tick and pip, min/step/max volume, max exposure
   - commission model (the 4 cTrader types plus percentage and per-lot)
   - financing model (swap points or %, triple day, period, time, weekends; or funding interval, cap and oracle basis; or dividend adjustments)
   - expiry and close-only dates, schedule, holidays and timezone
   - margin model (leverage tiers, margin tables, maintenance)
   - stop distances, short-sell flag, settlement currency, quanto flag
   - data capabilities: real volume, depth levels, tape, open interest, funding history
   - rate limits
2. **A CCXT contract path** for perps: funding, open interest, leverage and margin mode, reduce-only and post-only orders.
3. **QMB financing variants:** hourly funding from recorded history, dividend cash events, and futures/futures-CFD expiry with forced close at settlement.
4. **Market-hours calendars per symbol** from the venue schedule, beyond forex-17NY and always-open.
5. **Order-flow indicators** (delta, CVD, OFI, imbalance), computed only where the instrument's data capability says trades or depth exist.

---

## 11. Verdict on report 09's nine scalper types

Rule used: a "type" is an entry logic. Where something is really a **placement axis** (when or where to run), it moves to the router or registry. Report 09's table was INFERRED; these verdicts test it against the sources above.

| # | Report 09 type | Verdict | Why (with sources) |
|---|---|---|---|
| 1 | Momentum / breakout | **KEEP**, sharpen | A time-of-day "noise area" breakout with a trailing stop has published evidence on SPY (S50). The router needs a session window, a vol-expansion state and a cost ratio. Works on index CFDs, futures, FX majors, gold and perps. |
| 2 | Mean reversion / range | **KEEP**, add the Asian range | Quiet-hour FX patterns (S47) support it. It needs the strictest spread ceiling, since it wins many small amounts. Stand aside on change-point. In crypto, avoid the 16–17 UTC peak and funding-time spikes (S51, S52). |
| 3 | Order-flow sniper (absorption) | **CHANGE: split by data** | (a) **Tape/footprint absorption** needs trades with an aggressor side. That means futures, perps or spot crypto, not IC's cTrader CFDs, which have no tape (ctrader.md). PRACTITIONER detail in S60, tools in S25. (b) **OFI (best-quote imbalance)** needs only quote and size changes. It is the strongest short-horizon price driver in S48, and cTrader L2 depth can feed it. The old "low-liquidity windows (Tokyo, Sydney)" placement conflicts with absorption, which needs flow. Let each unit's record decide its window. |
| 4 | Volatility / expansion | **KEEP**, but share the router needs of #1 | It differs from #1 by trigger (a compression state first). Its router needs are the same plus the compression label. |
| 5 | Session-open / micro-ORB | **KEEP**, add an "in play" selector | The 5-minute ORB evidence is strongest when limited to stocks in play by relative volume (S49). For FX and gold the "open" is London or NY. For crypto there is no fixed open, so key it to the liquidity window. |
| 6 | VWAP / anchored reversion | **KEEP**, label the proxy | Real VWAP on futures, stocks and perps (S25 VWAP; S50 uses VWAP). On FX and index CFDs VWAP is weighted by tick volume, so mark it as a proxy in the unit's data capability. |
| 7 | Liquidity-window crypto | **CHANGE: router axis, not a type** | Hour-of-day liquidity is a placement window for every type (S51, S52, S53). It belongs with "sniping" windows in the registry. |
| 8 | Carry / funding-aware perp | **CHANGE: router axis + intraday cost** | Hyperliquid pays funding hourly at 1/8 of the 8-hour rate (S26). A minutes-long scalp pays little unless it crosses the hour. Funding extremes are a crowding/state input and a holding cost, not a scalper entry. CEX funding times are windows (S51). A true funding-carry strategy is intraday or swing, not scalping. |
| 9 | Cross-venue latency | **DROP** (backlog) | Needs co-location and speed. QMX's origin is "we can't win on speed, so we win on compounding" (seeds.md). Keep as a later idea. |
| A | **Liquidity sweep / stop-run reversal** | **ADD** | The most-taught retail FX and gold scalp: sweep of the session range, close back inside, entry on the retest, stop beyond the wick (PRACTITIONER S59). Router needs: pre-marked session levels, a live session window, a spread ceiling, a news blackout. It overlaps #2 but has its own trigger and its own failure mode (a real breakout). |
| B | **Passive maker / spread capture** | **ADD** (perps and spot first) | Maker fee 0.015% versus taker 0.045% at Hyperliquid tier 0, plus rebates for heavy maker share (S28), and a post-only order type (S33). Risks: adverse selection (S48 names OFI as a measure of it) and the address request budget (S32). Router needs: fee tier, request budget, queue/OFI state. |
| C | **Martingale / grid detection** | **ADD as a guard, not a type** | INFERRED: grids and martingales are common in MT5 EA marketplaces and look like high-win-rate scalpers until they blow up. The funnel should detect position-averaging-down patterns from the unit's record and route them to stricter review. Not researched here. |

Not added (INFERRED):
- **News-spike trading.** The operator has news trading off. The router still needs a news blackout for every type.
- **Intraday pairs/stat-arb** (e.g. index CFD pairs, gold/silver). Intraday, not scalping; later.
- **HIP-3 weekend discovery trading.** A real new market (S37, S38). The evidence is contested (S39 vs S40), so treat it as a hypothesis for QMB, not a type.

### 11.1 Router inputs every type needs (INFERRED; all values configurable per unit from its record)
- **Cost:** live round-trip cost ÷ the unit's average target. Built from spread + commission (+ funding if the hold crosses a funding time; + swap if it crosses the rollover). Examples: IC EURUSD about 0.8 pips; Hyperliquid taker about 0.09% round trip at tier 0 (S28).
- **Spread state:** the SQS ratio (current design).
- **Liquidity:** depth or top-of-book size where depth exists; RVOL where real volume exists; tick rate otherwise.
- **Volatility band:** realized range now versus the unit's proven band.
- **Window:** the venue schedule, the session, the unit's premium windows (sniping), and blackouts (rollover, fixes, news, close-only, roll week).
- **State:** trend / range / compression / expansion / stressed, plus a change-point flag (current shadow candidates).
- **Venue limits:** request budget (Hyperliquid), max exposure and stop distances (cTrader/MT5), order-value caps (Hyperliquid), data entitlements (CME).

---

## 12. Sources

Venue, broker and exchange (all read 2026-10-24):
- S1 IC spreads and commissions: https://www.ic.com/en/trading-pricing/spreads
- S2 IC Help Centre (commissions, triple swap reason): https://www.ic.com/en/help-resources/help-centre
- S3 IC swap rates (triple days by class): https://www.ic.com/en/trading-pricing/swap-rates
- S4 IC trading costs (EU site): https://www.ic.com/eu/en/trading-pricing/trading-costs
- S5 IC trading hours: https://www.ic.com/en/trading-pricing/trading-hours
- S6 IC server time GMT+3 2026: https://www.ic.com/blog/us-daylight-savings-server-time-changing-to-gmt3-2026/
- S7 IC forex: https://www.ic.com/en/trading-markets/forex
- S8 IC commodities: https://www.ic.com/en/trading-markets/commodities
- S9 IC indices: https://icmarkets.com/en/trading-markets/indices and https://www.ic.com/en/trading-markets/indices
- S10 IC futures CFDs (expiry and roll tables): https://www.ic.com/en/trading-markets/futures
- S11 IC stock CFDs (MT5 only): https://www.ic.com/en/trading-markets/stocks
- S12 IC crypto CFDs: https://www.ic.com/en/trading-markets/cryptocurrency
- S13 IC CFD Product Disclosure Statement: https://cdn.icmarkets.com/uploads/CFD-PDS.pdf
- S14 IC Raw Spread account: https://www.ic.com/en/trading-accounts/raw-spread-account
- S15 cTrader Open API model messages (`ProtoOASymbol`, error codes, commission types, deal status): https://help.ctrader.com/open-api/model-messages/
- S16 MQL5 symbol properties: https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants
- S17 MQL5 MqlRates (tick vs real volume): https://www.mql5.com/en/docs/constants/structures/mqlrates
- S18 CME Rulebook ch. 358 E-mini S&P 500: https://www.cmegroup.com/rulebook/CME/IV/350/358/358.pdf
- S19 CME Rulebook ch. 353 Micro E-mini S&P 500: https://www.cmegroup.com/rulebook/CME/IV/350/353/353.pdf
- S20 CME Micro E-mini FAQ: https://www.cmegroup.com/articles/faqs/micro-e-mini-equity-index-futures-frequently-asked-questions.html
- S21 CME E-mini FAQ: https://www.cmegroup.com/trading/equity-index/eminifaq.html (hours row via the Schwab spec table: https://www.schwab.com/futures/sp-500-emini)
- S22 CME equity index roll dates: https://www.cmegroup.com/trading/equity-index/rolldates.html
- S23 CQG exchange data fees (October 2026): https://www.cqg.com/partners/exchanges/market-data-fees
- S24 AMP Futures exchange data fees (June 2026): https://www.ampfutures.com/trading-info/exchange-data-fees
- S25 NinjaTrader Order Flow+: https://ninjatrader.com/support/helpGuides/nt8/order_flow_plus.htm and https://ninjatrader.com/support/helpguides/nt8/order_flow_volumetric_bars.htm
- S26 Hyperliquid funding: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding
- S27 Hyperliquid contract specifications: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/contract-specifications
- S28 Hyperliquid fees: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees
- S29 Hyperliquid tick and lot size: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/tick-and-lot-size
- S30 Hyperliquid margining: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/margining
- S31 Hyperliquid liquidations: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/liquidations
- S32 Hyperliquid rate and user limits: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits
- S33 Hyperliquid order types: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/order-types
- S34 Hyperliquid historical data: https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data
- S35 Hyperliquid info endpoint (l2Book, candleSnapshot): https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint
- S36 Hyperliquid perpetuals info (`metaAndAssetCtxs`, HIP-3 universe example): https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals
- S37 trade[XYZ] perpetuals (HIP-3 deployer): https://docs.trade.xyz/perpetuals
- S41 Binance spot filters: https://github.com/binance/binance-spot-api-docs/blob/master/filters.md
- S42 CCXT manual, market structure: https://github.com/ccxt/ccxt/wiki/manual
- S43 CCXT API spec by method (funding support lists): https://docs.ccxt.com/docs/base-spec
- S44 Deribit inverse options spec: https://support.deribit.com/hc/en-us/articles/31424939096093-Inverse-Options
- S55 Interactive Brokers UK, CFD corporate actions: https://www.interactivebrokers.co.uk/en/trading/cfd-corp-actions.php
- S56 LBMA precious metal prices: https://www.lbma.org.uk/prices-and-data/lbma-precious-metal-prices
- S57 Dukascopy historical data export: https://www.dukascopy.com/swiss/english/marketwatch/historical/
- S64 IC indices product sheet (2014, stale): https://www.icmarkets.com/blog/wp-content/uploads/2018/04/Indices-Product-Specification-Sheet-20141.pdf

Regulator and statistics:
- S46 BIS Triennial Survey 2025, FX turnover: https://www.bis.org/statistics/rpfx25_fx.htm
- S54 ESMA CFD product intervention measures: https://www.esma.europa.eu/sites/default/files/library/esma35-43-1000_additional_information_on_the_agreed_product_intervention_measures_relating_to_contracts_for_differences_and_binary_options.pdf

Research papers:
- S47 Ito & Hashimoto (2006), intraday seasonality in FX (EBS): https://www.nber.org/system/files/working_papers/w12413/w12413.pdf
- S48 Cont, Kukanov & Stoikov (2014), price impact of order book events: https://arxiv.org/abs/1011.6402
- S49 Zarattini, Barbon & Aziz (2024), ORB on stocks in play: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284
- S50 Zarattini, Aziz & Barbon (2024), intraday momentum on SPY: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4824172
- S51 Hansen, Kim & Kimbrough, periodicity in crypto volatility and liquidity: https://arxiv.org/html/2109.12142v2
- S52 Brauneis, Mestel & Theissen (2024), "The crypto world trades at tea time": https://link.springer.com/article/10.1007/s11156-024-01304-1
- S53 Wang, Liu & Hsu (2020), Bitcoin time-of-day periodicities: https://www.sciencedirect.com/science/article/abs/pii/S1544612319301904

Practitioner and secondary (labelled wherever used):
- S38 Hyperdash, RWA perps (third-party front end): https://docs.hyperdash.com/rwa-perps
- S39 Messari, weekend price discovery on Hyperliquid (2026-08-03): https://messari.io/report/weekend-trading-evidence-of-price-discovery-in-hyperliquid-s-weekend-markets
- S40 Orcas Capital, "Perpetuals on things that close" (2026-09-22): https://orcas.capital/research/perpetuals-on-things-that-close
- S58 Exactick, free tick data notes: https://exactick.com/free-forex-tick-data
- S59 Liquidity-sweep scalping:
  - https://en.forexclub.pl/Asian-Range-Liquidity-Sweep-at-London-Opening/
  - https://goldhunts.com/gold-strategies/gold-liquidity-sweep
  - https://www.quantum-algo.com/markets/gold/london-session-strategy/
- S60 Futures order flow and tape reading:
  - https://dhawal.org/research/futures-ta/chapters/ch11-order-flow
  - https://tra-mada.de/en/blog/tape-reading-time-sales-level-2
- S61 eminitutor, E-mini rollover day (stale): https://www.eminitutor.com/emini-futures-rollover-day/
- S62 MQL5 forum on `real_volume`: https://www.mql5.com/en/forum/33238
- S63 FXT help centre, chart volume: https://help.fxtrading.com/en/articles/17516863-mt4-and-mt5-what-does-chart-volume-mean

QMX internal: `workroom/risk-lab-2026-10-05/seeds.md`; `grounding/09-original-design-recovery.md` (Job E); code and doc paths in §10.

## 13. Not verified

- **CME gold (GC/MGC) specs.** The CME spec pages render with JavaScript and did not load. Gold futures numbers are not given here.
- **IC metals lot sizes, stock CFD financing rates and live swap values.** Read them from the account's symbol records at connection. The QMX design already demands this.
- **IC's stock-financing sign.** The page text credits longs and debits shorts. Confirm it on a live symbol.
- **LULD halts for single stocks, weekly energy report times and FX fix (WM/Reuters) effects.** Named, not researched.
- **Free public crypto archives** (e.g. Binance public data). Not checked.
- **Deribit greeks/IV API fields.** Not read.
- **Martingale/grid prevalence in MT5 marketplaces.** INFERRED only.
- **No videos were watched.** Practitioner material is web text only.
