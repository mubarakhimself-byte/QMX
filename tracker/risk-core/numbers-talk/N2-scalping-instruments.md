# N2: which instruments suit a $500 automated scalper

Facts gathered 2026-11-09. Every number carries a label:

- **READ**: I read it on the primary page or pulled it from the venue's own API.
- **SNIPPET**: I saw it only in a search result or a third-party page. Check it before relying on it.
- **ESTIMATE**: my own arithmetic or my own calculation on price data. The working is shown.

Two words used throughout:

- **Round trip (RT)**: one buy plus one sell. Cost = spread paid once + commission/fees on both sides.
- **1-min move (ATR proxy)**: the average "true range" of a one-minute bar (high minus low, stretched to include any gap from the previous close). It stands in for ATR, the average true range. "Busy" means the main session of that market. "Quiet" means the all-hours median.

## Short answer

| Class (main instrument) | RT cost as share of a 1-min move (busy / quiet) | Same, 5-min move (busy) | Real order-flow data? | Fits $500 at $5-$50 risk? | Hours | How they move together |
|---|---|---|---|---|---|---|
| FX majors, cTrader raw (EURUSD) | **27% / 41%** (GBPUSD 30% / 53%, USDJPY ~30%) | 12% | **No.** Broker quotes and broker depth only. No trade tape with buyer/seller side. | Yes at offshore leverage. **No** at 1:30 retail leverage: a $10 risk needs ~$750 margin. | 24h, Mon-Fri | EURUSD~GBPUSD 0.76 (5-min). Both move against USDJPY (-0.43). |
| Gold CFD (XAUUSD) | 5-11% / 8-18% (depends on broker commission) | 2-5% | **No** on the CFD. Real flow only via the COMEX futures feed (paid). | Yes. 0.01 lot = 1 oz. | 24h, Mon-Fri | Gold~S&P 0.41, gold~EURUSD 0.39 (5-min). Loose. |
| Index CFDs (US500 / NAS100 / GER40) | 8% / 18%; 5% / 9%; 12% / 14% | 2-5% | **No** on the CFD. Real flow via CME/Eurex futures (paid). | Probably. Minimum size **not confirmed**. | ~23h a day (US), ~20h (GER40) | ES~NQ 0.91, ES~YM 0.75, ES~DAX 0.58 (5-min). Near 1.0 in crashes. |
| CME micros (MES / MNQ / MGC / MCL) | MES 9% / 20%; MNQ 3% / 5%; MGC 14% / 21%; MCL 16% / 31% | 1-7% | **Yes.** Every trade with buyer/seller side, plus full depth. $12.10 per exchange per month (non-pro depth). | MES, MCL: yes. MGC: borderline. **MNQ: no.** One contract risks $77-$143 on a 2-ATR stop. | Sun 6pm-Fri 5pm ET, 1h daily break | MES~MNQ 0.92 (1-min). Same as index CFDs. |
| Hyperliquid perps (BTC / ETH / SOL) | **Taker: 193% / 308%** (BTC). **Maker: 63% / 101%** | Taker 73%, maker 24% | **Yes, free.** Trades with side, 20-level book, by API. | Yes ($10 minimum order, up to 40x). Taker fees eat ~1R per trade. | 24/7 | BTC~ETH 0.88, BTC~SOL 0.83 (1-min). One trade, not three. |

What this says, in plain words:

1. **The cheapest scalping venue is the CME micro on the Nasdaq-100 (MNQ).** Costs are 3-5% of a one-minute move. Index CFDs and MES come next at 5-20%. But one MNQ contract moves $2 per point. That is too big for a $5-$50 risk on a $500 account most of the time.
2. **MES and MCL are the best fit for $500.** Costs are 9-31% of a one-minute move. One contract on a two-ATR stop risks $18-$60. Real order-flow data costs about $25-$37 a month.
3. **FX majors look cheap but are not, at one-minute horizons.** The commission alone is 0.67-0.95 pip. A busy one-minute EURUSD bar is only ~2.5 pips. Cost is 27-41% of the move. At five minutes it falls to ~12%.
4. **Hyperliquid at the base fee tier is the most expensive place to scalp.** Taking liquidity both ways costs 0.09% of notional. A one-minute BTC move is ~0.047%. The fee is about twice the move. Even maker-maker costs 63% of a one-minute move. Free order-flow data does not fix this.
5. **Order-flow imbalance does not beat fees on its own.** The evidence shows it explains the price move *in the same moment*. Its power to forecast the *next* move is real only below about 1-10 seconds. That forecast is a fraction of a basis point, below every fee in this table.
6. **Instruments inside a class are mostly one bet.** ES/NQ, BTC/ETH/SOL and (less so) EURUSD/GBPUSD correlate 0.75-0.92 at 1-5 minutes. In crashes they rise to 0.93-0.99.

## How the one-minute and five-minute moves were measured

All ESTIMATE. Scripts and raw outputs: `N2_scripts/` next to this file (`analyze.py`, `costs.py`, `duka.py`, `*_out.txt`).

| Data | Source | Window |
|---|---|---|
| EURUSD, GBPUSD, USDJPY 1-min | Dukascopy tick feed (bid/ask ticks to 1-min mid bars) | 4-6 Nov 2026, 13:00-16:00 UTC (busy) and 02:00 UTC (quiet). USDJPY: one hour of each only. |
| Gold (GC=F), ES, NQ, YM, CL, DAX 1-min | Yahoo Finance chart API | 3/4-9 Nov 2026 |
| Same, 5-min | Yahoo Finance | 17 Aug / 31 Aug - 9 Nov 2026 (60 days) |
| BTC, ETH, SOL 1-min and 5-min | Hyperliquid `candleSnapshot` API (the venue's own data) | 1-min 5-9 Nov; 5-min 23 Oct - 9 Nov 2026 |
| Daily, for stress windows | Yahoo Finance | 2020-2026 |

Warnings:

- The 3-6 Nov window held the most volatile day of the last 60 (5 Nov for ES/NQ). Busy one-minute moves are therefore on the high side. The cost shares would be **higher** in a calm week. The "quiet" column shows that.
- Yahoo one-minute FX bars were gappy and gave one-minute moves ~30% smaller than Dukascopy's tick data. I used Dukascopy for FX.
- Gold uses the COMEX futures price as a stand-in for spot XAUUSD. Index CFDs use the CME future (ES for US500, NQ for NAS100) and the DAX cash index for GER40.
- Futures 1-min spreads were not measured. For CME micros I assumed **one tick**, the smallest possible spread. That makes the micro costs a floor, not an average.

Measured moves (ESTIMATE):

| Instrument | Price | 1-min move, busy | 1-min move, quiet (median) | 5-min move, busy (same days) | 5-min move, 60-day mean |
|---|---|---|---|---|---|
| EURUSD (Dukascopy) | 1.1197 | 2.49 pips | 1.67 pips (02 UTC) | 5.73 pips | n/a |
| GBPUSD (Dukascopy) | 1.3423 | 2.85 pips | 1.59 pips (02 UTC) | 6.66 pips | n/a |
| USDJPY (Dukascopy, 1h samples) | 157.96 | 3.21 pips | 4.53 pips (02 UTC, Tokyo session) | 7.46 pips | n/a |
| Gold (GC=F) | 4,104 | $2.94 | $1.90 | $6.88 | $4.56 |
| ES (S&P 500) | 7,438 | 6.0 pts | 2.75 pts | 13.5 pts | 4.4 pts |
| NQ (Nasdaq-100) | 27,139 | 35.8 pts | 19.3 pts | 79.6 pts | 28.3 pts |
| DAX | 26,038 | 11.0 pts | 9.5 pts | 28.6 pts | 21.2 pts |
| WTI crude (CL) | 89.60 | $0.172 | $0.090 | $0.411 | $0.218 |
| BTC (Hyperliquid) | 74,142 | $35.1 (4.7 bps) | $22 | $93 | $104 (17-day) |
| ETH (Hyperliquid) | 2,107.6 | $1.46 (6.9 bps) | $0.90 | $3.69 | $4.22 |
| SOL (Hyperliquid) | 85.94 | $0.070 (8.2 bps) | $0.052 | $0.18 | $0.21 |

(bps = basis points, hundredths of a percent. Busy windows: FX 13-16 UTC; gold 12-17 UTC; US indices 13:30-20:00 UTC; crude 13:00-18:30 UTC; DAX Xetra hours; crypto all hours.)

## 1. FX majors on a cTrader raw-spread account

**Cost.**

- IC Markets raw spread, average: EURUSD 0.01, GBPUSD 0.04, USDJPY 0.03 pips. **READ** ([ic.com spreads](https://ic.com/global/en/trading-pricing/spreads), [ic.com forex](https://ic.com/global/en/trading-markets/forex)). The page gives no averaging period. These averages are far below what I measured on Dukascopy's feed in the busy hours (EURUSD 0.29, GBPUSD 0.55, USDJPY 0.47 pips mean spread, ESTIMATE from 87k-91k ticks). Treat IC's figure as a best case.
- IC cTrader commission: $3 per 100,000 USD traded, per side, Forex and Metals only. **READ** (ic.com spreads page).
- Pepperstone Razor on cTrader: $6 per lot round trip for FX, $7 for spot gold. **READ** ([Pepperstone pricing](https://pepperstone.com/en-gb/ways-to-trade/pricing/)).

Arithmetic (ESTIMATE), per standard lot (100,000 of the base currency):

- EURUSD: notional = 100,000 x 1.1197 = $111,970. Commission RT = 2 x $3 x 1.1197 = $6.72. One pip on one lot = $10, so commission = 0.67 pip. Plus 0.01 pip spread = **0.68 pip RT**. With a 0.3 pip real-world spread: 0.97 pip.
  - Share of 1-min busy move: 0.68 / 2.49 = **27%**. Quiet: 0.68 / 1.67 = **41%**. 5-min busy: 0.68 / 5.73 = **12%**. With a 0.3 pip spread: 39% / 58% / 17%.
- GBPUSD: commission = 6 x 1.3423 / 10 = 0.81 pip, plus 0.04 = **0.85 pip**. Busy 0.85 / 2.85 = **30%**; quiet 0.85 / 1.59 = **53%**; 5-min 13%.
- USDJPY: notional $100,000, commission RT $6. One pip on one lot = 1,000 JPY = $6.33 at 157.96. Commission = 6 / 6.33 = 0.95 pip, plus 0.03 = **0.98 pip**. Busy 0.98 / 3.21 = **30%**; 5-min 13%. Small sample (one hour per group).

**Order-flow data.** **No real order flow.** cTrader Open API offers live bid/ask, historical bid/ask ticks (one week per request), bars, and "depth quotes". The depth is the broker's own liquidity ladder. There is no message for public trades with a buyer/seller side. **READ** ([cTrader Open API symbol data](https://help.ctrader.com/open-api/symbol-data/), [message list](https://help.ctrader.com/open-api/messages/)). Spot FX has no central exchange, so no public tape exists. The closest real flow is CME FX futures (6E, 6B, 6J). Those need CME depth data, $12.10 per exchange per month (see section 4).

**Size and $500.** Minimum 1,000 units (0.01 lot). **READ** (ic.com forex). Max leverage "up to 1:5000" on IC's global site. **READ**. Retail rules in the EU, UK and Australia cap majors at 1:30 (not read here; standard ESMA/ASIC rule).

Sizing with a stop of two busy one-minute moves (ESTIMATE):

- EURUSD stop = 2 x 2.49 = 5.0 pips. 0.01 lot = $0.10 per pip, so the smallest trade risks $0.50.
- For $10 risk: $10 / (5.0 x $10 per lot) = 0.20 lot = $22,400 notional. Margin at 1:30 = **$746. Above $500.** At 1:500 = $45.
- For $5 risk: 0.10 lot, $11,200 notional, $373 margin at 1:30. That just fits, with one position at a time.
- So: $500 works for FX scalping only on an offshore entity with high leverage, or at $5 risk.

**Hours.** 24 hours, Monday to Friday. Exact broker server times not read.

**How they move together** (ESTIMATE from Yahoo 5-min returns, 60 days; daily from Yahoo):

| Pair | 1-min | 5-min (60 days) | 5-min per-day range | Daily 2024 | Daily COVID crash (20 Feb-30 Apr 2020) | Daily Apr 2025 tariff shock |
|---|---|---|---|---|---|---|
| EURUSD~GBPUSD | 0.57 (Yahoo bars, understated) | 0.76 | 0.33 to 0.90 | 0.78 | 0.57 | 0.75 |
| EURUSD~USDJPY | -0.22 | -0.43 | -0.73 to -0.06 | -0.48 | -0.70 | -0.86 |

EURUSD and GBPUSD are mostly one dollar bet. The link weakened in the 2020 crash. The yen pair moves the other way, and that link got stronger in both stress windows.

## 2. Gold (XAUUSD CFD)

**Cost.**

- IC Markets raw XAUUSD: minimum 0.05, average 0.09. **READ** (ic.com spreads). The unit is not printed. I read it as dollars per ounce. Commission $3 per 100k USD per side applies to metals. **READ**.
- Pepperstone: $7 per lot RT on cTrader. Spreads "from 0.08" (minimum, not average). **READ**.
- Contract size 100 oz per lot. **SNIPPET** (several brokers; IC's own gold page does not state it).

Arithmetic (ESTIMATE), per ounce, gold at $4,104:

- IC: notional per lot = 100 x 4,104 = $410,440. Commission RT = 2 x 3 x 4.104 = $24.63 per lot = $0.246 per oz. Plus 0.09 spread = **$0.34 per oz**. Busy 1-min: 0.34 / 2.94 = **11%**. Quiet: 0.34 / 1.90 = **18%**. 5-min busy 5%.
- Pepperstone: $7 / 100 oz = $0.07 + 0.08 minimum spread = **$0.15 per oz** (a floor). Busy 5%, quiet 8%, 5-min 2%.
- IC's commission grows with the gold price because it is charged on notional. Pepperstone's is a flat $7 per lot.

**Order-flow data.** None on the CFD (same cTrader limits as FX). Real flow comes from COMEX gold futures (GC/MGC). COMEX depth costs $12.10 per month (section 4).

**Size and $500.** 0.01 lot = 1 oz is typical (IC: micro lot trading 0.01. **READ**; per-symbol XAUUSD minimum **SNIPPET**). IC Australia caps gold at 1:20. **READ** ([icmarkets.com.au gold](https://icmarkets.com.au/en/trade-gold)).

- Stop = 2 x $2.94 = $5.87 per oz. At 0.01 lot the smallest trade risks $5.87. Fits.
- $10 risk = 1.7 oz = $6,980 notional. Margin at 1:20 = $349. Fits, one position.

**Hours.** "24 hours a day, 5 days a week". **READ** (IC Australia gold page).

**Moves with** (ESTIMATE, 5-min, 60 days): gold~S&P futures 0.41 (per-day 0.18 to 0.64); gold~EURUSD 0.39 (0.06 to 0.77). Gold is a partly separate bet.

## 3. Index CFDs (US500, NAS100, GER40)

**Cost.** No commission on index CFDs. **READ** (ic.com indices, icmarkets.eu indices).

| Symbol at IC | Min spread | Avg spread | Source |
|---|---|---|---|
| US500 | 0.20 | 0.492 | **READ** [ic.com indices](https://ic.com/global/en/trading-markets/indices) |
| USTEC (NAS100) | 1.00 | 1.807 | **READ** same |
| DE40 (GER40) | 0.50 | 1.338 | **READ** same |

The EU site shows slightly different averages (0.36 / 1.57 / 1.46). **READ** ([icmarkets.eu indices](https://icmarkets.eu/en/trading-markets/indices)). Neither page gives the averaging period.

Arithmetic (ESTIMATE): cost = average spread, in index points.

- US500: 0.492 / 6.0 = **8%** busy; 0.492 / 2.75 = **18%** quiet; 5-min busy 4%.
- NAS100: 1.807 / 35.8 = **5%**; / 19.25 = **9%**; 5-min 2%.
- GER40: 1.338 / 11.0 = **12%**; / 9.47 = **14%**; 5-min 5%.
- Overnight spreads on CFDs are usually wider than the average. That would raise the "quiet" figures. Not measured.

**Order-flow data.** None on the CFD. It is a broker price that follows the futures. Real flow means buying CME data (ES/NQ, section 4) or Eurex data (FDAX). Eurex prices not looked up.

**Size and $500.** **Not confirmed.** Neither IC page states contract size, value per point or minimum trade for US500, USTEC or DE40. The only example is AUS200: "$1 per index point" per contract. **READ**. Other brokers show 0.01-lot minimums on $1-per-point contracts. **SNIPPET**. Leverage: "up to 1:200" on ic.com, "up to 1:20" on icmarkets.eu. **READ**.

If one lot = $1 per point and 0.01 lot is allowed (ESTIMATE, to check in the cTrader symbol info):

- US500: stop = 2 x 6.0 = 12 points. $10 risk = 0.83 lot = $6,200 notional. Margin at 1:20 = $310. Fits.

**Hours.** Pepperstone US500 and NAS100: 01:00-23:59 Monday, 01:00-23:55 Tuesday-Thursday. GER40: 03:15-22:59 / 03:15-22:55. Server time GMT+2 or GMT+3. **READ** ([Pepperstone indices](https://pepperstone.com/en-gb/markets/indices/)).

**How they move together** (ESTIMATE):

| Pair | 1-min | 5-min (60 days) | 5-min per-day range | Most volatile day | Daily 2024 | Daily COVID crash | Daily Apr 2025 |
|---|---|---|---|---|---|---|---|
| ES~NQ | 0.92 | 0.91 | 0.74 to 0.96 | 0.94 (5 Nov) | 0.95 | 0.97 | 0.99 |
| ES~YM | 0.79 | 0.75 | 0.35 to 0.90 | 0.90 | 0.84 | 0.99 | 0.98 |
| NQ~YM | 0.58 | 0.53 | -0.21 to 0.77 | 0.77 | 0.66 | 0.96 | 0.97 |
| ES~DAX | 0.62 | 0.58 | 0.17 to 0.78 | 0.69 | 0.41* | 0.77* | 0.06* |

*Daily DAX figures are distorted because the DAX closes hours before the US. The intraday numbers are the better guide.

In calm times the Dow is a partly separate bet from the Nasdaq. In a crash all three US indices move as one (0.96-0.99). Holding long S&P and long Nasdaq at once is close to doubling one position.

## 4. CME micro futures (MES, MNQ, MGC, MCL)

**Contract specs.**

| Contract | Size | Tick | Source |
|---|---|---|---|
| MES | $5 x S&P 500 index | 0.25 pt = $1.25 | **READ** ([CME MES page](https://www.cmegroup.com/markets/equities/sp/micro-e-mini-sandp-500.html)); tick $ from [Schwab micros table](https://www.schwab.com/futures/micro-futures) (**READ**) |
| MNQ | $2 x Nasdaq-100 | 0.25 pt = $0.50 | **READ** (CME MNQ spec page; Schwab) |
| MGC | 10 troy oz (1/10 of GC) | $0.10 = $1.00 | **READ** (CME: "1/10 of Gold (GC)"; Schwab) |
| MCL | 100 barrels | $0.01 = $1.00 | **READ** (CME MCL page; Schwab) |

**Fees.**

- NinjaTrader commission on micros: Free plan $0.39 per side, Monthly ($99/mo) $0.29, Lifetime ($1,499) $0.09. Exchange, clearing and NFA fees are extra. **READ** ([NinjaTrader pricing](https://www.ninjatrader.com/pricing/)).
- Exchange fee per side, non-member: MES $0.35, MNQ $0.35, MCL $0.50, MGC $1.10. NFA fee $0.01 per side. **READ** (TradeStation exchange-fee table, page text extracted via search tool; the page blocked a direct fetch). An older broker table shows MGC lower. Check MGC on [CME's fee finder](https://www.cmegroup.com/company/clearing-fees/fee-finder.html).
- A broker clearing fee may also apply. NinjaTrader's amount was not found. The totals below leave it out.

Arithmetic (ESTIMATE), NinjaTrader Free plan, one contract, spread = one tick (a floor):

- MES: fees 2 x (0.39 + 0.35 + 0.01) = $1.50. Spread $1.25. RT = **$2.75 = 0.55 pt**. Busy 1-min: 0.55 / 6.0 = **9%**. Quiet: 0.55 / 2.75 = **20%**. 5-min busy 4%.
- MNQ: fees $1.50, spread $0.50, RT **$2.00 = 1.0 pt**. 1.0 / 35.8 = **3%**; / 19.25 = **5%**; 5-min 1%.
- MGC: fees 2 x (0.39 + 1.10 + 0.01) = $3.00, spread $1.00, RT **$4.00 = $0.40/oz**. 0.40 / 2.94 = **14%**; / 1.90 = **21%**; 5-min 6%.
- MCL: fees 2 x (0.39 + 0.50 + 0.01) = $1.80, spread $1.00, RT **$2.80 = $0.028/bbl**. 0.028 / 0.172 = **16%**; / 0.090 = **31%**; 5-min 7%.
- On the $0.09 Lifetime plan each RT is $0.60 cheaper. MES would fall to 7% / 16%.

**Order-flow data. Yes, real.** The CME feed carries every trade and the full book.

- CME's own fee list, effective 1 Jan 2026, per device per month: non-professional depth of market $12.10 per exchange, $36.50 for all four exchanges. Top of book $1.55 per exchange, $4.65 for all four. **READ** (text of [CME fee list PDF](https://www.cmegroup.com/market-data/files/january-2026-market-data-fee-list.pdf), extracted via search tool; a direct fetch timed out).
- MES and MNQ are on CME, MGC on COMEX, MCL on NYMEX. Depth for all three exchanges = 3 x $12.10 = $36.30, or $36.50 for the bundle (ESTIMATE). Depth for MES/MNQ only = $12.10.
- Brokers charge their own retail price: Tradovate $16 per exchange for depth, $41 for the four-exchange bundle; top of book $4 / $12. **READ** (Tradovate help page text). CQG's list for October 2026: CME non-pro depth $13, bundle $41. **READ** ([CQG fees](https://www.cqg.com/partners/exchanges/market-data-fees/us-dollar)).
- Whether every trade arrives with its aggressor side depends on the platform's API. CME's own feed does tag it. I did not read that spec page this session.

**Size and $500.** One contract is the minimum.

- Intraday margin at NinjaTrader: MES $50. **READ** (NinjaTrader pricing). MNQ $100, MCL $100, MGC $200. **SNIPPET** (NinjaTrader margin table via search). These end at the session close. Overnight needs full exchange margin (thousands of dollars).
- Risk of one contract on a stop of two one-minute moves (ESTIMATE):

| Contract | Busy: 2 x 1-min move | $ risk, busy | Quiet: 2 x median | $ risk, quiet | Fits $5-$50? |
|---|---|---|---|---|---|
| MES | 12.0 pts x $5 | **$60** | 5.5 pts | **$27.50** | Yes in quiet hours, slightly over in busy hours |
| MNQ | 71.6 pts x $2 | **$143** | 38.5 pts | **$77** | **No** |
| MGC | $5.87 x 10 | **$59** | $3.80 x 10 | **$38** | Borderline |
| MCL | $0.344 x 100 | **$34** | $0.18 x 100 | **$18** | Yes |

There is no smaller size than one contract. A $500 account can hold one MES or one MCL with room. MNQ is too coarse for this risk range despite having the lowest cost share.

**Hours.** Sunday 6:00 pm to Friday 5:00 pm ET, with a 5:00-6:00 pm ET daily break. **READ** (Schwab micros table; same on CME-sourced spec pages).

**How they move together.** MES~MNQ follow ES~NQ: 0.92 at 1-min, 0.97-0.99 daily in crashes (table in section 3). MGC~MES 0.41 at 5-min. MCL was not paired.

## 5. Hyperliquid perpetuals (BTC, ETH, SOL)

**Fees.** Base tier (under $5M 14-day volume): taker 0.045%, maker 0.015% per side. **READ** ([Hyperliquid fees](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees)). Staking HYPE gives 5-40% off. Maker rebates only above 0.5% of total maker volume.

**Spread** (snapshot 9 Nov 2026 11:03 UTC, `l2Book` API). **READ**: BTC $1 (0.14 bps), ETH $0.10 (0.47 bps), SOL $0.001 (0.12 bps).

Arithmetic (ESTIMATE):

- Taker both ways = 0.09% + spread. BTC: 74,142 x (0.0009 + 0.0000135) = **$67.7 per BTC**. One-minute busy move $35.1. **193%** of the move. Quiet: **308%**. 5-min: **73%**.
- Maker both ways = 0.03%. BTC: **$22.2 per BTC**. **63%** of the 1-min move, **101%** quiet, **24%** at 5-min.
- ETH: taker 137% / 222%, 5-min 54%. Maker 43% / 70%, 5-min 17%.
- SOL: taker 112% / 151%, 5-min 43%. Maker 37% / 50%, 5-min 14%.

**Order-flow data. Yes, and free.**

- WebSocket `trades` feed and `recentTrades` call: every trade with side "B" (buyer was the aggressor) or "A" (seller was the aggressor). **READ** (API response pulled today; [subscriptions doc](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions)).
- `l2Book`: 20 levels per side (5 in "fast" mode). **READ** (docs and today's response). Book depth in those 20 levels today: BTC ~$3.2M bid / $3.0M ask; ETH ~$10.3M / $7.2M; SOL ~$0.7M / $0.3M. **READ**.
- History: L2 snapshots and fills sit in AWS S3 buckets. The downloader pays transfer costs. Updates are monthly with "no guarantee". **READ** ([historical data](https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data)).
- Limits: 1,200 REST weight per minute per IP; actions limited to 1 request per $1 traded since the account opened, after a 10,000-request starting buffer. **READ** ([rate limits](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits)). A scalper placing $5k-$10k orders earns enough requests.

**Size and $500.**

- Minimum order value $10 ("Order must have minimum value of $10"). **SNIPPET** (Hyperliquid error list, quoted by several developer sites).
- Max leverage today: BTC 40x, ETH 25x, SOL 20x. **READ** (`metaAndAssetCtxs` API).
- BTC with a stop of 2 x $35.1 = $70 (9.5 bps): $10 risk = $10 / 0.000946 = $10,570 notional. Margin at 40x = $264. Fits (ESTIMATE).
- But taker fees on that trade = 0.09% x $10,570 = **$9.51, almost the full $10 risk.** Maker-maker = $3.17, about a third of the risk. ETH ($10 risk = $7,200 notional): taker $6.48. SOL ($6,120): taker $5.51.

**Hours.** 24/7. The 1-min data runs through Saturday and Sunday (ESTIMATE from the candle timestamps).

**How they move together** (ESTIMATE, Hyperliquid 1-min and 5-min; daily from Yahoo):

| Pair | 1-min | 5-min (17 days) | 5-min per-day range | Daily 2024 | COVID crash | Apr 2025 | Oct 2025 |
|---|---|---|---|---|---|---|---|
| BTC~ETH | 0.88 | 0.88 | 0.76 to 0.96 | 0.80 | 0.96 | 0.93 | 0.93 |
| BTC~SOL | 0.83 | 0.86 | 0.71 to 0.90 | 0.75 | n/a | 0.88 | 0.90 |
| ETH~SOL | 0.85 | 0.88 | 0.70 to 0.93 | 0.70 | n/a | 0.88 | 0.92 |
| BTC~NQ | 0.62 | 0.57 | 0.44 to 0.73 | | | | |

Three crypto positions in the same direction are close to one position three times as big. In stress the links rise to about 0.9. BTC also tracks the Nasdaq at 0.57-0.62 intraday, so crypto does not diversify much against index scalps.

## 6. Order-flow imbalance (OFI): what the evidence says, and fees

OFI is the net change in buy-side versus sell-side size at the best bid and ask over a short interval.

- **Cont, Kukanov & Stoikov (2014)**, 50 US stocks. Price changes over short intervals follow OFI in a straight line. The average fit is 65% (R², the share of price variation explained). The slope is inversely tied to book depth. **READ** ([arXiv 1011.6402](https://arxiv.org/html/1011.6402v3), [J. Financial Econometrics](https://academic.oup.com/jfec/article-abstract/12/1/47/816163)). **This is the same-interval move, not a forecast.** OFI and the price change are measured over the same window. A big sell that empties the bid *is* the drop.
- **Cont, Cucuringu & Zhang (2023)**, Quantitative Finance. For the *next* one minute, out-of-sample fit was **-0.37% to -0.10%**: worse than guessing no change. Lagged OFI from other stocks helped a little at very short horizons and faded fast. **READ** ([arXiv 2112.13213](https://arxiv.org/html/2112.13213)).
- **Silantyev (2019)**, Digital Finance, BitMEX BTC perpetual. In crypto, trade-flow imbalance (aggressive trades only) explained same-interval price changes better than full OFI. Thin books are the main difference from stock markets. **READ** abstract ([RePEc](https://ideas.repec.org/a/spr/digfin/v1y2019i1d10.1007_s42521-019-00007-w.html)).
- **Garaj (2025/26, Charles University thesis, not peer-reviewed)**, BTC/USDT perpetual, all of 2025, 100 ms data, 20 levels. Best out-of-sample forecast fit was **7.35-7.7% at the 100-millisecond horizon**. It fell to a few tenths of a percent by 10 seconds and a few hundredths by 30 seconds. At 1 and 10 minutes there was no gain over "no change". **READ** ([thesis PDF](https://dspace.cuni.cz/bitstream/handle/20.500.11956/213492/130479083.pdf?sequence=1)).
- A 2026 arXiv paper (Ślepaczuk, Binance perps, 1-second data) reports signals that survive a "conservative" taker backtest. **SNIPPET** (abstract only; no fee level checked).

**How big is the forecastable move against the fees?** (ESTIMATE, rough)

- BTC's one-minute move is ~4.7 bps. On a random-walk scaling, a one-second move is about 4.7 / sqrt(60) ≈ 0.6 bps.
- With 7% of variance forecastable, the predictable part is about sqrt(0.07) ≈ 0.26 of that, so **~0.16 bps at one second**.
- Hyperliquid taker RT is 9 bps: **~55 times larger**. Maker RT is 3 bps: ~19 times larger.
- MES, same logic: one-second move ≈ 6.0 / sqrt(60) ≈ 0.8 pt. Predictable part ≈ 0.2 pt. That is less than one tick (0.25 pt) and less than the 0.55 pt RT cost. (This borrows the crypto R² for an equity future; no paper read gives MES directly.)
- At one minute or more, where a $500 scalper actually holds, the papers find no forecast at all.

**Plain verdict.** OFI as a stand-alone forecast is eaten by fees on every venue here. Its forecast lives below about ten seconds. There the expected move is a fraction of a basis point. Only firms paying near-zero fees, earning rebates and sitting next to the matching engine can collect it. OFI may still help a slower system as a **filter**: skipping entries against strong one-sided flow, or pulling resting maker orders before they get run over. That use is not tested here.

## Open checks before any money

1. IC Markets index CFDs: contract size, value per point and minimum volume for US500, USTEC, DE40. Read them in the cTrader symbol info.
2. IC Markets XAUUSD spread unit (is 0.09 in dollars?) and the real average spread on the account.
3. NinjaTrader (or chosen broker) clearing fee per micro contract, and the MGC exchange fee on CME's fee finder.
4. Whether the chosen futures platform's API passes the trade aggressor side through.
5. Which IC entity the account sits on. That sets leverage, 1:30 or far higher, and decides whether FX scalping at $10 risk is possible on $500.
