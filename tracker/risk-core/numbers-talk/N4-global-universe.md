# N4: The global universe — where an ORB and a scalper can trade, around the clock

Measured and researched on 2026-11-09. This extends N3 from 15 to 36 instruments: the 12 Dukascopy instruments N3 measured, recomputed, plus 21 new ones, plus N3's three crypto coins. It also covers every index market a retail trader can reach, the CME hours question, and which futures fit a $500 account. Scripts: `numbers-talk/measure/` (analyze_n4.py, split_half_n4.py, sanity_n4.py, build_n4_tables.py).

## Plain-English summary

Terms used:
- **5m range**: the distance from the highest to the lowest price inside one 5-minute block.
- **Cost**: what one round trip (open and close) costs. For index and oil CFDs it is the spread. For FX, gold and silver it is the spread plus an assumed commission. For stock CFDs it is the spread plus $0.04 per share.
- **Ratio**: the median 5m range divided by the cost. A ratio of 10 means a typical 5-minute swing is 10 times the cost. It is a ceiling, not a profit.
- **Cash session**: the hours when the home stock exchange is open, for example Tokyo 09:00-15:30.
- **Separate bet**: a group of markets that move together. If two markets have a 5m-return correlation of 0.6 or more, a trade in each is one bet, not two.
- **Period a**: 2026-08-11 to 2026-11-08 (this season). **Period b**: 2025-11-01 to 2026-02-28 (last winter).
- **Labels**: READ = read from a primary page, or computed directly from the downloaded price data. SNIPPET = from a search snippet or secondary page. ESTIMATE = my judgement or general knowledge, not checked today.

What the data says (all READ from Dukascopy data unless marked):
- The **US open is still the best hour of the day** for every US index, the new ones included. US tech 100 leads at a ratio of 35. The Dow (US 30, new) is second at 29, and the Russell 2000 (US 2000, new) has 13.
- **Japan 225 (25) and Germany 40 (22) remain the best non-US markets.** Japan 225 owns the Asian morning (00-01 UTC). Germany 40 owns the European open (07-08 UTC in summer).
- **Most of the new markets are weak at Dukascopy's prices.** France 40 has 7.8, Italy 40 5.9, Switzerland 20 4.3, China A50 3.7, Netherlands 25 3.1, Spain 35 3.0, South Africa 40 2.8, Poland 20 2.4 and Singapore 1.2.
- **Oil moves more this season.** Its 5m range is about 1.5 times last winter's, so WTI and Brent now have a ratio of 5.3 to 5.4, against 2.4 last winter. Silver has 4.7, copper 2.6 and natural gas 2.3.
- **The five biggest US stocks reach 5 to 7 with CFD commission included**, at the US open and close only. NVIDIA leads with 7.2.
- **Costs depend on the broker.** With IC Markets' published average spreads, US tech 100 falls to 21 and Japan 225 to 15. US 30 rises to 34, France 40 to 10, oil to 8 and Australia 200 to 6. With Pepperstone's, US tech 100 is 37 and US 30 is 24.
- **Japan 225 and US tech 100 never trade in their home cash sessions at the same time** (0 shared 5-minute blocks). Their 0.74 correlation comes entirely from CFDs trading while the home exchange is closed. In Tokyo hours it is 0.68, and in New York hours it is 0.85. So at the Tokyo open, Japan 225 and the night US tech 100 are one bet.
- **This season, the Dow and the Nasdaq move apart.** Their correlation is 0.52 over all hours and 0.27 in the US open, against 0.67 last winter. At the US open they are two separate bets.
- **Oil now moves against stocks**: -0.29 with US 500, against +0.12 last winter.
- **Separate bets per session** (threshold 0.6, markets with ratio 5 or more): Asia 3, Europe 3, London-New York overlap 3, **US open 10** (6 index or commodity bets plus 4 single stocks), US afternoon 2, US close 3. Gold is its own bet in every session.
- **Futures that fit $500 today** (IBKR intraday margin, READ): the CME E-nanos (Dow $123, Russell $90, S&P $233, Nasdaq $417), the Nikkei 225 Micro (about $378), Micro Euro Stoxx 50 (about $426) and 1-Ounce Gold ($434). Micro-DAX ($1,751), Micro WTI ($1,940), Mini Hang Seng, China A50, SPI 200 and FTSE 100 do not fit.
- **CME did not move equity-index futures to 24 hours.** They trade 23 hours a day, as before. What goes to 23 hours on 6 December 2026 is US **stocks**, on Nasdaq and NYSE Arca (READ).
- **Dukascopy has no CFD for** India (GIFT Nifty), Taiwan, Korea, China H, Canada, Brazil, Mexico, the Nordics or the Middle East. Those markets stay unmeasured.

The biggest caveats:
1. A CFD spread is the broker's price, not a market fact. Every Dukascopy ratio is shown next to the IC Markets and Pepperstone ratio where those brokers publish a spread.
2. South Africa 40 has only 14 days of period-a data, because Dukascopy stopped quoting it after 2026-08-28.
3. "Singapore" here is a Dukascopy index near 535 points, not the Straits Times Index (about 4,000). Its ratio is not useful.

## Ranking: all measured instruments, by best-hours ratio

Ratio (a) uses Dukascopy's spread, plus the assumed commission where one applies, in each instrument's best 3 UTC hours (READ, computed). The broker columns divide the same 5m range by the broker's published **average** spread. Those averages cover all hours (IC: READ, ic.com 2026-11-09; Pepperstone: READ for the US indices, Razor, August 2026 data; SNIPPET for DE40, AU200 and gold from Pepperstone's costs PDF, and for HK50 from a third-party page). Because the averages include quiet hours, the broker ratios at the best hours are a little pessimistic. For stocks, the broker estimate uses a 1-cent spread (ESTIMATE) plus $0.04 commission (READ). Cluster = the leader rule on the both-in-cash-session correlation, at 0.6.

| # | Instrument | New in N4 | Best 3 UTC hours (a) | Median 5m range there | Dukascopy cost | Ratio (a), Dukascopy | Ratio (b) | Period-a hours in b | Ratio at IC Markets avg spread | Ratio at Pepperstone avg spread | Cluster |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | US100 |  | 13, 14, 15 | 37.45 pts (0.126%) | 1.08 | **35.3** | 31.7 | 27.6 | 20.7 | 37.5 | G1 |
| 2 | US30 | yes | 13, 14, 15 | 47.75 pts (0.091%) | 1.63 | **29.5** | 24.3 | 20.5 | 33.8 | 23.9 | G2 |
| 3 | JP225 |  | 00, 01, 14 | 128.5 pts (0.195%) | 5.17 | **24.9** | 11.3 | 10.6 | 14.5 | - | G3 |
| 4 | DE40 |  | 07, 08, 13 | 25.49 pts (0.099%) | 1.15 | **22.2** | 16.2 | 11.9 | 19.1 | 18.2 | G4 |
| 5 | US2000 | yes | 13, 14, 15 | 3.454 pts (0.119%) | 0.263 | **13.1** | 11.6 | 10.0 | 7.2 | 11.5 | G2 |
| 6 | US500 |  | 13, 14, 15 | 5.84 pts (0.076%) | 0.513 | **11.4** | 13.2 | 10.7 | 11.9 | 14.6 | G1 |
| 7 | UK100 |  | 07, 08, 13 | 9.78 pts (0.091%) | 1 | **9.8** | 6.2 | 4.4 | 4.6 | - | G4 |
| 8 | XAUUSD |  | 12, 13, 14 | 6.193 USD/oz (0.145%) | 0.64 | **9.7** | 9.5 | 7.8 | - | 24.8 | G5 |
| 9 | FR40 | yes | 07, 08, 13 | 7.784 pts (0.096%) | 1 | **7.8** | 6.6 | 5.8 | 10.4 | - | G4 |
| 10 | NVDA | yes | 14, 15, 20 | 0.5523 USD (0.264%) | 0.0767 | **7.2** | 7.7 | 6.0 | - (broker est. 11.0) | - | G1 |
| 11 | TSLA | yes | 14, 15, 20 | 1.265 USD (0.339%) | 0.204 | **6.2** | 8.0 | 6.0 | - (broker est. 25.3) | - | G6 |
| 12 | IT40 | yes | 07, 08, 14 | 57.55 pts (0.112%) | 9.8 | **5.9** | 3.7 | 3.3 | 6.4 | - | G4 |
| 13 | AMZN | yes | 14, 15, 20 | 0.5707 USD (0.221%) | 0.103 | **5.6** | 5.9 | 4.3 | - (broker est. 11.4) | - | G7 |
| 14 | AAPL | yes | 14, 15, 20 | 0.6755 USD (0.201%) | 0.121 | **5.6** | 5.2 | 4.0 | - (broker est. 13.5) | - | G8 |
| 15 | BRENT | yes | 08, 13, 15 | 0.2685 USD/bbl (0.267%) | 0.05 | **5.4** | 2.4 | 2.0 | 7.9 | - | G9 |
| 16 | WTI | yes | 13, 14, 15 | 0.2657 USD/bbl (0.289%) | 0.05 | **5.3** | 2.4 | 2.3 | 7.8 | - | G9 |
| 17 | MSFT | yes | 14, 19, 20 | 1.03 USD (0.199%) | 0.197 | **5.2** | 5.3 | 3.2 | - (broker est. 20.6) | - | G10 |
| 18 | XAGUSD | yes | 12, 13, 14 | 0.1623 USD/oz (0.265%) | 0.0347 | **4.7** | 6.7 | 5.5 | - | - | G5 |
| 19 | CH20 | yes | 07, 13, 14 | 14.14 pts (0.100%) | 3.3 | **4.3** | 2.4 | 1.8 | 4.0 | - | G11 |
| 20 | USDJPY |  | 00, 13, 14 | 0.06133 JPY (0.039%) | 0.0147 | **4.2** | 5.1 | 4.7 | - | - | G12 |
| 21 | EURUSD |  | 12, 13, 14 | 0.0003867 USD (0.034%) | 0.0001 | **3.9** | 4.6 | 3.9 | - | - | G13 |
| 22 | GBPUSD |  | 13, 14, 15 | 0.0004933 USD (0.037%) | 0.00013 | **3.8** | 4.8 | 4.8 | - | - | G13 |
| 23 | CN50 | yes | 01, 02, 05 | 24.74 pts (0.176%) | 6.62 | **3.7** | 1.9 | 1.9 | 3.6 | - | G14 |
| 24 | AU200 |  | 00, 01, 02 | 7.392 pts (0.083%) | 2.05 | **3.6** | 4.0 | 3.5 | 6.1 | 4.1 | G15 |
| 25 | EU50 |  | 07, 08, 14 | 5.901 pts (0.094%) | 1.77 | **3.3** | 2.3 | 1.9 | 3.4 | - | G4 |
| 26 | NL25 | yes | 07, 08, 13 | 0.9072 pts (0.081%) | 0.296 | **3.1** | 3.3 | 2.5 | 4.8 | - | G4 |
| 27 | ES35 | yes | 07, 08, 14 | 21.04 pts (0.108%) | 7 | **3.0** | 2.7 | 2.4 | 4.8 | - | G4 |
| 28 | SA40 | yes | 07, 13, 14 | 147.9 pts (0.137%) | 52.2 | **2.8** | 3.1 | 1.9 | 9.6 | - | G5 |
| 29 | COPPER | yes | 12, 13, 14 | 0.0091 USD (0.138%) | 0.0035 | **2.6** | 3.4 | 2.9 | - | - | G16 |
| 30 | PL20 | yes | 07, 08, 14 | 5.029 pts (0.123%) | 2.08 | **2.4** | 2.0 | 1.4 | - | - | G17 |
| 31 | HK50 |  | 02, 05, 14 | 25.86 pts (0.106%) | 11 | **2.4** | 3.1 | 3.0 | 3.2 | 5.2 | G18 |
| 32 | NATGAS | yes | 12, 13, 14 | 0.01013 USD/MMBtu (0.344%) | 0.0045 | **2.3** | 4.2 | 4.1 | 2.5 | - | G19 |
| 33 | SG | yes | 01, 02, 14 | 0.608 pts (0.118%) | 0.5 | **1.2** | 0.9 | 0.8 | - | - | G20 |

Crypto is not re-measured here. N3 (Hyperliquid taker cost): SOL 3.3, ETH 2.9, BTC 2.4; with maker orders 7 to 10.

Global clusters (leader rule on the both-in-cash-session correlation, threshold 0.6; strongest market by ratio leads):
- G1: US100, US500, NVDA
- G2: US30, US2000
- G3: JP225
- G4: DE40, UK100, FR40, IT40, EU50, NL25, ES35
- G5: XAUUSD, XAGUSD, SA40
- G6: TSLA
- G7: AMZN
- G8: AAPL
- G9: BRENT, WTI
- G10: MSFT
- G11: CH20
- G12: USDJPY
- G13: EURUSD, GBPUSD
- G14: CN50
- G15: AU200
- G16: COPPER
- G17: PL20
- G18: HK50
- G19: NATGAS
- G20: SG
- crypto: BTC, ETH, SOL

## Separate bets per world session

Method: for each session (sessions use local exchange clocks, as in N3), take every instrument with a session ratio of 5 or more at Dukascopy costs. Compute the correlation of 5m returns **inside that session only**. Then apply the pod's own rule: take the strongest market, put every market with a correlation of 0.6 or more to it in its cluster, and repeat with what is left. Each cluster is one separate bet. The leader is the market to trade.

| Session | Instruments at ratio >= 5 | Separate bets | The bets (strongest member first, session ratio) |
|---|---|---|---|
| Asia (00-07 UTC) | 5 | **3** | [JP225, US100] lead JP225 17.4; [US30, FR40] lead US30 7.0; [XAUUSD] lead XAUUSD 5.5 |
| Europe (Frankfurt 09:00 to New York 08:00) | 9 | **3** | [DE40, US30, UK100, FR40, US2000, US500] lead DE40 19.1; [US100, JP225] lead US100 13.5; [XAUUSD] lead XAUUSD 5.8 |
| London-New York overlap (NY 08:00-09:30) | 9 | **3** | [DE40, US30, JP225, UK100, FR40] lead DE40 17.5; [US100, US2000, US500] lead US100 16.0; [XAUUSD] lead XAUUSD 8.8 |
| US open (NY 09:30-11:00) | 18 | **10** | [US100, JP225, US500, NVDA] lead US100 51.0; [US30] lead US30 40.1; [DE40, UK100, FR40, IT40] lead DE40 21.4; [US2000] lead US2000 17.1; [XAUUSD, XAGUSD] lead XAUUSD 10.6; [TSLA] lead TSLA 7.3; [AAPL] lead AAPL 6.8; [AMZN] lead AMZN 5.7; [MSFT] lead MSFT 5.5; [WTI, BRENT] lead WTI 5.4 |
| US afternoon (NY 11:00-15:00) | 8 | **2** | [US100, US30, JP225, US500, US2000, DE40, NVDA] lead US100 26.1; [XAUUSD] lead XAUUSD 5.9 |
| US close (NY 15:00-16:15) | 9 | **3** | [US100, US30, JP225, US500, US2000, DE40, NVDA] lead US100 22.4; [TSLA] lead TSLA 5.3; [AAPL] lead AAPL 5.2 |

How sensitive the count is to the 0.6 threshold (bets at 0.5 / 0.6 / 0.7): Asia 3 / 3 / 5; Europe 2 / 3 / 5; London-New York overlap 2 / 3 / 4; US open 9 / 10 / 11; US afternoon 2 / 2 / 3; US close 3 / 3 / 5.

Notes:
- Asia: the night US 30 is its own bet. Its correlation with Japan 225 in Asia hours is 0.44, and with the night US tech 100 it is 0.60, right at the threshold. Its Asia ratio is 5 to 10 in every hour, best at 06 UTC (9.8). France 40 joins it only at 06 UTC, when its futures open (08:00 CEST); it has no ticks before that. So Asia has three bets: Japan 225 (with the night US tech 100), the night US 30, and gold. The middle one is borderline.
- Australia 200, Hong Kong 50 and China A50 drop out of Asia only because Dukascopy's spread is wide. At IC Markets' average spread, the whole Asia session gives Australia 200 4.5 (6.1 in its best hours 00-02 UTC). At Pepperstone's (SNIPPET), Hong Kong 50 gets 5.2. In cash hours, Australia 200 correlates with Japan 225 at only 0.06, so it would be a separate Asia bet at those brokers' prices.
- US open: 4 of the 10 bets are single stocks (Tesla, Apple, Amazon, Microsoft). NVIDIA joins the US tech 100 cluster (0.70). Each stock is a separate bet by correlation, but their ratios (5 to 7) are well below the index leaders.

## Which futures fit a $500 account (scope addition)

For each separate bet: the smallest futures contract at IBKR, and the dollar risk of a stop as wide as one median 5-minute move in that bet's best hour inside the session. The table also gives IBKR's intraday initial margin (READ, IBKR futures margin table, 2026-11-09, US resident; converted to USD at the last Dukascopy rates) and the monthly non-professional fee for depth-of-book data at IBKR (READ, IBKR market-data pricing page, 2026-11-09).

| Session | Bet (lead) | Best UTC hour in session | Median 5m range then | Smallest future at IBKR | Value per point | Value per tick | $ risk for a one-median-5m stop | IBKR intraday initial margin (USD) | Order-flow data, non-pro, per month |
|---|---|---|---|---|---|---|---|---|---|
| Asia (00-07 UTC) | JP225 | 00 | 160.076 | OSE Nikkei 225 Micro (225MC) | JPY 10 (SNIPPET) | JPY 50.00 | **$10** | $378 | OSE L2 JPY 400/mo |
| Asia (00-07 UTC) | US30 | 06 | 19.554 | CBOT E-nano Dow NDOW | USD 0.05 (READ) | USD 0.10 | **$1** | $123 | CBOT L2 $12.10/mo |
| Asia (00-07 UTC) | XAUUSD | 01 | 6.115 | COMEX 1-Ounce Gold 1OZ | USD 1 (ESTIMATE) | not read | **$6** | $434 | COMEX L2 $12.10/mo |
| Europe (Frankfurt 09:00 to New York 08:00) | DE40 | 07 | 28.500 | Eurex Micro-DAX FDXS | EUR 1 (READ) | EUR 1.00 | **$32** | $1,751 | Eurex Core L2 EUR 13.00/mo |
| Europe (Frankfurt 09:00 to New York 08:00) | US100 | 08 | 22.772 | CME E-nano Nasdaq-100 NNQ | USD 0.2 (READ) | USD 0.10 | **$5** | $417 | CME L2 $12.10/mo |
| Europe (Frankfurt 09:00 to New York 08:00) | XAUUSD | 07 | 3.996 | COMEX 1-Ounce Gold 1OZ | USD 1 (ESTIMATE) | not read | **$4** | $434 | COMEX L2 $12.10/mo |
| London-New York overlap (NY 08:00-09:30) | DE40 | 13 | 23.462 | Eurex Micro-DAX FDXS | EUR 1 (READ) | EUR 1.00 | **$26** | $1,751 | Eurex Core L2 EUR 13.00/mo |
| London-New York overlap (NY 08:00-09:30) | US100 | 13 | 37.771 | CME E-nano Nasdaq-100 NNQ | USD 0.2 (READ) | USD 0.10 | **$8** | $417 | CME L2 $12.10/mo |
| London-New York overlap (NY 08:00-09:30) | XAUUSD | 13 | 6.690 | COMEX 1-Ounce Gold 1OZ | USD 1 (ESTIMATE) | not read | **$7** | $434 | COMEX L2 $12.10/mo |
| US open (NY 09:30-11:00) | US100 | 14 | 42.406 | CME E-nano Nasdaq-100 NNQ | USD 0.2 (READ) | USD 0.10 | **$8** | $417 | CME L2 $12.10/mo |
| US open (NY 09:30-11:00) | US30 | 14 | 52.518 | CBOT E-nano Dow NDOW | USD 0.05 (READ) | USD 0.10 | **$3** | $123 | CBOT L2 $12.10/mo |
| US open (NY 09:30-11:00) | DE40 | 14 | 23.000 | Eurex Micro-DAX FDXS | EUR 1 (READ) | EUR 1.00 | **$26** | $1,751 | Eurex Core L2 EUR 13.00/mo |
| US open (NY 09:30-11:00) | US2000 | 14 | 3.897 | CME E-nano Russell 2000 N2K | USD 0.5 (READ) | USD 0.10 | **$2** | $90 | CME L2 $12.10/mo |
| US open (NY 09:30-11:00) | XAUUSD | 14 | 6.588 | COMEX 1-Ounce Gold 1OZ | USD 1 (ESTIMATE) | not read | **$7** | $434 | COMEX L2 $12.10/mo |
| US open (NY 09:30-11:00) | TSLA | 14 | 1.371 | no IBKR future (CFD only) | - | - | - | - | - |
| US open (NY 09:30-11:00) | AAPL | 14 | 0.691 | no IBKR future (CFD only) | - | - | - | - | - |
| US open (NY 09:30-11:00) | AMZN | 14 | 0.591 | no IBKR future (CFD only) | - | - | - | - | - |
| US open (NY 09:30-11:00) | MSFT | 14 | 1.180 | no IBKR future (CFD only) | - | - | - | - | - |
| US open (NY 09:30-11:00) | WTI | 14 | 0.260 | NYMEX Micro WTI MCL | USD 100 (ESTIMATE) | USD 1.00 | **$26** | $1,940 | NYMEX L2 $12.10/mo |
| US afternoon (NY 11:00-15:00) | US100 | 15 | 32.183 | CME E-nano Nasdaq-100 NNQ | USD 0.2 (READ) | USD 0.10 | **$6** | $417 | CME L2 $12.10/mo |
| US afternoon (NY 11:00-15:00) | XAUUSD | 15 | 5.095 | COMEX 1-Ounce Gold 1OZ | USD 1 (ESTIMATE) | not read | **$5** | $434 | COMEX L2 $12.10/mo |
| US close (NY 15:00-16:15) | US100 | 19 | 22.573 | CME E-nano Nasdaq-100 NNQ | USD 0.2 (READ) | USD 0.10 | **$5** | $417 | CME L2 $12.10/mo |
| US close (NY 15:00-16:15) | TSLA | 20 | 1.425 | no IBKR future (CFD only) | - | - | - | - | - |
| US close (NY 15:00-16:15) | AAPL | 20 | 0.776 | no IBKR future (CFD only) | - | - | - | - | - |

What this shows:
- **Fits $500 on margin, with room to spare:** E-nano Dow NDOW ($123), E-nano Russell N2K ($90), E-nano S&P NES ($233). **Just fits:** E-nano Nasdaq NNQ ($417), Nikkei 225 Micro (about $378), Micro Euro Stoxx 50 FSXE (EUR 382, about $426), 1-Ounce Gold ($434). **Does not fit:** Micro-DAX FDXS ($1,751), Micro WTI MCL ($1,940), Micro natural gas MNG ($589), Mini CAC MFC (about $534), Micro SMI FSMS (about $911), Mini Hang Seng MHI (about $2,394), SGX China A50 CN ($1,232), SPI 200 AP (about $8,696), FTSE 100 Z (about $7,126), CME Micro Nikkei MNK ($3,325).
- **Dollar risk per stop is small on the E-nanos.** NDOW about $3 and N2K about $2 at the US open. NNQ is about $8, the Nikkei Micro about $10 at the Tokyo open, and 1-Ounce Gold $4 to $7. On a $500 account, a 1% risk ($5) allows one NNQ contract with a stop of about 25 Nasdaq points, which is less than one median 5-minute move at the open (42 points). The E-nano tick (NNQ 0.50 points = $0.10) is fine enough for that.
- **Order-flow data** (trades plus book depth) exists for every one of these futures through the exchange feed. At IBKR, non-professional depth costs per month: CME $12.10, CBOT $12.10, NYMEX $12.10 and COMEX $12.10, each charged separately. Then Eurex EUR 13.00, OSE JPY 400, HKFE HKD 100 (top of book free), ASX24 AUD 21.50, MEFF EUR 6.00, Montreal $10.50, ICE Futures Europe financials $132 (no cheaper non-pro row) and Euronext index derivatives (non-pro row unclear: EUR 1.00 retail-derivatives L2 or EUR 45.50 pro). SGX shows only top of book (SGD 2.00), and GIFT Nifty top of book costs $16.50. IBKR requires USD 500 minimum equity to keep any market-data subscription (READ), which is exactly this account size.
- **Buyer or seller side.** CME (MDP 3.0) and Eurex (EOBI) publish the aggressor side of each trade in their native feeds. Elsewhere, and in IBKR's own time-and-sales, the side is inferred by comparing the trade price with the bid and ask. ESTIMATE: from general knowledge of the feeds, not re-read today.
- **CFDs have no order flow.** A CFD is the broker's own quote. The N2/N3 plan stands: read order flow on the future, trade the CFD or the micro future.

## Correlation of 5-minute returns (period a)

Two ways, for every measured instrument. (i) All hours: every weekday 5m block where both markets ticked. (ii) Both in cash session: only the blocks where each market is inside its own home cash session. Cash windows are in the assumptions below. Full matrices (36 x 36): `measure/results/n4_corr_all_hours.csv`, `n4_corr_cash_sessions.csv`, and the block counts in `n4_corr_cash_nobs.csv`. All values are READ (computed).

| Japan 225 vs US tech 100, 5m returns, period a | Correlation | 5m blocks |
|---|---|---|
| all hours | 0.74 | 16,572 |
| Tokyo cash session only (US100 CFD trading at night) | 0.68 | 4,209 |
| New York cash session only (JP225 CFD trading at night) | 0.85 | 4,956 |
| both in own cash session | n/a | 0 |
| neither in own cash session | 0.77 | 7,407 |

Japan 225 vs US tech 100, in plain words: the two home sessions never overlap, so the "both in cash" correlation does not exist. All of the 0.74 comes from one CFD trading while its home exchange is closed. During Tokyo hours, Japan 225 moves with the night US tech 100 at 0.68. During New York hours, the Japan 225 CFD follows US tech 100 at 0.85, so it is a lagging copy of the US, not a separate market. Treat Japan 225 at the Tokyo open and the night US tech 100 as one bet. Treat the Japan 225 CFD during US hours as a worse-priced US tech 100.

**Indices, all hours (period a):**

| | US100 | US500 | US30 | US2000 | DE40 | EU50 | FR40 | NL25 | IT40 | ES35 | CH20 | UK100 | PL20 | SA40 | JP225 | HK50 | CN50 | SG | AU200 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| US100 |  | 0.90 | 0.52 | 0.62 | 0.54 | 0.59 | 0.43 | 0.50 | 0.49 | 0.39 | 0.23 | 0.31 | 0.31 | 0.30 | 0.74 | 0.31 | 0.33 | 0.32 | 0.34 |
| US500 | 0.90 |  | 0.75 | 0.74 | 0.61 | 0.65 | 0.52 | 0.55 | 0.55 | 0.47 | 0.36 | 0.44 | 0.36 | 0.36 | 0.69 | 0.36 | 0.32 | 0.38 | 0.45 |
| US30 | 0.52 | 0.75 |  | 0.73 | 0.61 | 0.61 | 0.56 | 0.50 | 0.53 | 0.51 | 0.47 | 0.55 | 0.34 | 0.30 | 0.45 | 0.34 | 0.23 | 0.37 | 0.53 |
| US2000 | 0.62 | 0.74 | 0.73 |  | 0.60 | 0.62 | 0.55 | 0.50 | 0.54 | 0.49 | 0.43 | 0.49 | 0.34 | 0.35 | 0.55 | 0.35 | 0.27 | 0.37 | 0.52 |
| DE40 | 0.54 | 0.61 | 0.61 | 0.60 |  | 0.89 | 0.80 | 0.65 | 0.75 | 0.69 | 0.61 | 0.69 | 0.42 | 0.32 | 0.52 | 0.37 | 0.27 | 0.37 | 0.56 |
| EU50 | 0.59 | 0.65 | 0.61 | 0.62 | 0.89 |  | 0.88 | 0.78 | 0.85 | 0.80 | 0.62 | 0.71 | 0.44 | 0.38 | 0.66 | 0.52 | 0.50 | 0.56 | 0.70 |
| FR40 | 0.43 | 0.52 | 0.56 | 0.55 | 0.80 | 0.88 |  | 0.66 | 0.76 | 0.73 | 0.66 | 0.72 | 0.38 | 0.33 | 0.52 | 0.47 | 0.42 | 0.50 | 0.68 |
| NL25 | 0.50 | 0.55 | 0.50 | 0.50 | 0.65 | 0.78 | 0.66 |  | 0.63 | 0.62 | 0.53 | 0.66 | 0.35 | 0.32 | 0.55 | 0.43 | 0.41 | 0.45 | 0.58 |
| IT40 | 0.49 | 0.55 | 0.53 | 0.54 | 0.75 | 0.85 | 0.76 | 0.63 |  | 0.81 | 0.51 | 0.65 | 0.43 | 0.33 | 0.56 | 0.46 | 0.44 | 0.51 | 0.63 |
| ES35 | 0.39 | 0.47 | 0.51 | 0.49 | 0.69 | 0.80 | 0.73 | 0.62 | 0.81 |  | 0.52 | 0.67 | 0.40 | 0.31 | 0.47 | 0.46 | 0.38 | 0.48 | 0.62 |
| CH20 | 0.23 | 0.36 | 0.47 | 0.43 | 0.61 | 0.62 | 0.66 | 0.53 | 0.51 | 0.52 |  | 0.69 | 0.26 | 0.21 | 0.33 | 0.35 | 0.28 | 0.38 | 0.57 |
| UK100 | 0.31 | 0.44 | 0.55 | 0.49 | 0.69 | 0.71 | 0.72 | 0.66 | 0.65 | 0.67 | 0.69 |  | 0.36 | 0.35 | 0.36 | 0.36 | 0.21 | 0.35 | 0.59 |
| PL20 | 0.31 | 0.36 | 0.34 | 0.34 | 0.42 | 0.44 | 0.38 | 0.35 | 0.43 | 0.40 | 0.26 | 0.36 |  | 0.36 | 0.36 | 0.34 | 0.32 | 0.31 | 0.42 |
| SA40 | 0.30 | 0.36 | 0.30 | 0.35 | 0.32 | 0.38 | 0.33 | 0.32 | 0.33 | 0.31 | 0.21 | 0.35 | 0.36 |  | 0.37 | 0.41 | 0.29 | 0.28 | 0.46 |
| JP225 | 0.74 | 0.69 | 0.45 | 0.55 | 0.52 | 0.66 | 0.52 | 0.55 | 0.56 | 0.47 | 0.33 | 0.36 | 0.36 | 0.37 |  | 0.34 | 0.38 | 0.32 | 0.32 |
| HK50 | 0.31 | 0.36 | 0.34 | 0.35 | 0.37 | 0.52 | 0.47 | 0.43 | 0.46 | 0.46 | 0.35 | 0.36 | 0.34 | 0.41 | 0.34 |  | 0.49 | 0.34 | 0.32 |
| CN50 | 0.33 | 0.32 | 0.23 | 0.27 | 0.27 | 0.50 | 0.42 | 0.41 | 0.44 | 0.38 | 0.28 | 0.21 | 0.32 | 0.29 | 0.38 | 0.49 |  | 0.19 | 0.21 |
| SG | 0.32 | 0.38 | 0.37 | 0.37 | 0.37 | 0.56 | 0.50 | 0.45 | 0.51 | 0.48 | 0.38 | 0.35 | 0.31 | 0.28 | 0.32 | 0.34 | 0.19 |  | 0.38 |
| AU200 | 0.34 | 0.45 | 0.53 | 0.52 | 0.56 | 0.70 | 0.68 | 0.58 | 0.63 | 0.62 | 0.57 | 0.59 | 0.42 | 0.46 | 0.32 | 0.32 | 0.21 | 0.38 |  |

**Indices, only 5m blocks where BOTH markets are inside their own cash session:** (n/a = the two cash sessions never overlap, or fewer than 300 shared blocks)

| | US100 | US500 | US30 | US2000 | DE40 | EU50 | FR40 | NL25 | IT40 | ES35 | CH20 | UK100 | PL20 | SA40 | JP225 | HK50 | CN50 | SG | AU200 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| US100 |  | 0.90 | 0.48 | 0.57 | 0.40 | 0.53 | 0.29 | 0.43 | 0.44 | 0.29 | -0.03 | 0.05 | 0.36 | n/a | n/a | n/a | n/a | n/a | n/a |
| US500 | 0.90 |  | 0.74 | 0.69 | 0.52 | 0.59 | 0.41 | 0.51 | 0.51 | 0.41 | 0.16 | 0.26 | 0.45 | n/a | n/a | n/a | n/a | n/a | n/a |
| US30 | 0.48 | 0.74 |  | 0.68 | 0.52 | 0.50 | 0.49 | 0.43 | 0.45 | 0.48 | 0.42 | 0.49 | 0.37 | n/a | n/a | n/a | n/a | n/a | n/a |
| US2000 | 0.57 | 0.69 | 0.68 |  | 0.54 | 0.55 | 0.51 | 0.45 | 0.51 | 0.44 | 0.35 | 0.41 | 0.40 | n/a | n/a | n/a | n/a | n/a | n/a |
| DE40 | 0.40 | 0.52 | 0.52 | 0.54 |  | 0.88 | 0.80 | 0.64 | 0.73 | 0.68 | 0.58 | 0.67 | 0.42 | 0.32 | n/a | 0.40 | n/a | 0.45 | n/a |
| EU50 | 0.53 | 0.59 | 0.50 | 0.55 | 0.88 |  | 0.88 | 0.78 | 0.85 | 0.81 | 0.59 | 0.69 | 0.45 | 0.39 | n/a | 0.42 | n/a | 0.50 | n/a |
| FR40 | 0.29 | 0.41 | 0.49 | 0.51 | 0.80 | 0.88 |  | 0.66 | 0.74 | 0.74 | 0.65 | 0.72 | 0.39 | 0.33 | n/a | 0.31 | n/a | 0.42 | n/a |
| NL25 | 0.43 | 0.51 | 0.43 | 0.45 | 0.64 | 0.78 | 0.66 |  | 0.61 | 0.62 | 0.52 | 0.66 | 0.36 | 0.33 | n/a | 0.31 | n/a | 0.36 | n/a |
| IT40 | 0.44 | 0.51 | 0.45 | 0.51 | 0.73 | 0.85 | 0.74 | 0.61 |  | 0.81 | 0.46 | 0.64 | 0.43 | 0.33 | n/a | 0.34 | n/a | 0.43 | n/a |
| ES35 | 0.29 | 0.41 | 0.48 | 0.44 | 0.68 | 0.81 | 0.74 | 0.62 | 0.81 |  | 0.50 | 0.67 | 0.40 | 0.32 | n/a | 0.36 | n/a | 0.42 | n/a |
| CH20 | -0.03 | 0.16 | 0.42 | 0.35 | 0.58 | 0.59 | 0.65 | 0.52 | 0.46 | 0.50 |  | 0.68 | 0.26 | 0.22 | n/a | 0.27 | n/a | 0.30 | n/a |
| UK100 | 0.05 | 0.26 | 0.49 | 0.41 | 0.67 | 0.69 | 0.72 | 0.66 | 0.64 | 0.67 | 0.68 |  | 0.36 | 0.35 | n/a | 0.41 | n/a | 0.40 | n/a |
| PL20 | 0.36 | 0.45 | 0.37 | 0.40 | 0.42 | 0.45 | 0.39 | 0.36 | 0.43 | 0.40 | 0.26 | 0.36 |  | 0.36 | n/a | 0.27 | n/a | 0.27 | n/a |
| SA40 | n/a | n/a | n/a | n/a | 0.32 | 0.39 | 0.33 | 0.33 | 0.33 | 0.32 | 0.22 | 0.35 | 0.36 |  | n/a | n/a | n/a | 0.28 | n/a |
| JP225 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |  | 0.24 | 0.32 | 0.12 | 0.06 |
| HK50 | n/a | n/a | n/a | n/a | 0.40 | 0.42 | 0.31 | 0.31 | 0.34 | 0.36 | 0.27 | 0.41 | 0.27 | n/a | 0.24 |  | 0.48 | 0.22 | 0.07 |
| CN50 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0.32 | 0.48 |  | 0.10 | 0.09 |
| SG | n/a | n/a | n/a | n/a | 0.45 | 0.50 | 0.42 | 0.36 | 0.43 | 0.42 | 0.30 | 0.40 | 0.27 | 0.28 | 0.12 | 0.22 | 0.10 |  | 0.23 |
| AU200 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0.06 | 0.07 | 0.09 | 0.23 |  |

**Commodities, stocks, FX and crypto against the main indices, all hours / both-in-cash-session:**

| | US100 | US500 | DE40 | JP225 | XAUUSD | WTI |
|---|---|---|---|---|---|---|
| XAUUSD | 0.35 / 0.32 | 0.40 / 0.38 | 0.35 / 0.37 | 0.33 / n/a |  | -0.29 / -0.33 |
| XAGUSD | 0.42 / 0.40 | 0.45 / 0.44 | 0.39 / 0.41 | 0.39 / n/a | 0.84 / 0.86 | -0.28 / -0.31 |
| COPPER | 0.40 / 0.43 | 0.42 / 0.46 | 0.37 / 0.39 | 0.38 / n/a | 0.52 / 0.56 | -0.16 / -0.18 |
| WTI | -0.24 / -0.19 | -0.29 / -0.25 | -0.36 / -0.33 | -0.23 / n/a | -0.29 / -0.33 |  |
| BRENT | -0.24 / -0.19 | -0.29 / -0.24 | -0.36 / -0.33 | -0.24 / n/a | -0.29 / -0.33 | 0.95 / 0.94 |
| NATGAS | -0.04 / -0.04 | -0.05 / -0.06 | -0.06 / -0.05 | -0.04 / n/a | -0.04 / -0.04 | 0.14 / 0.15 |
| NVDA | 0.73 / 0.73 | 0.65 / 0.65 | 0.36 / 0.26 | 0.62 / n/a | 0.22 / 0.21 | -0.10 / -0.10 |
| TSLA | 0.48 / 0.48 | 0.44 / 0.44 | 0.31 / 0.25 | 0.40 / n/a | 0.18 / 0.16 | -0.10 / -0.11 |
| AAPL | 0.27 / 0.27 | 0.35 / 0.35 | 0.16 / 0.07 | 0.16 / n/a | 0.12 / 0.11 | -0.12 / -0.12 |
| MSFT | 0.43 / 0.43 | 0.44 / 0.44 | 0.24 / 0.17 | 0.28 / n/a | 0.14 / 0.12 | -0.11 / -0.11 |
| AMZN | 0.52 / 0.52 | 0.54 / 0.54 | 0.31 / 0.23 | 0.38 / n/a | 0.20 / 0.18 | -0.15 / -0.16 |
| EURUSD | 0.13 / 0.05 | 0.18 / 0.12 | 0.18 / 0.18 | 0.13 / n/a | 0.43 / 0.51 | -0.21 / -0.22 |
| GBPUSD | 0.17 / 0.07 | 0.23 / 0.16 | 0.21 / 0.19 | 0.16 / n/a | 0.44 / 0.52 | -0.19 / -0.19 |
| USDJPY | -0.04 / 0.03 | -0.09 / -0.03 | -0.12 / -0.15 | 0.04 / n/a | -0.32 / -0.45 | 0.25 / 0.29 |
| BTC | 0.43 / 0.43 | 0.41 / 0.42 | 0.29 / 0.26 | 0.35 / 0.32 | 0.30 / 0.37 | -0.12 / -0.12 |
| ETH | 0.44 / 0.43 | 0.42 / 0.42 | 0.29 / 0.27 | 0.37 / 0.34 | 0.30 / 0.37 | -0.14 / -0.13 |
| SOL | 0.42 / 0.43 | 0.40 / 0.42 | 0.27 / 0.25 | 0.35 / 0.30 | 0.29 / 0.36 | -0.14 / -0.13 |

Pairs at or above 0.6 (all hours | both-in-cash):
- BRENT / WTI: 0.95 | 0.94
- US100 / US500: 0.90 | 0.90
- DE40 / EU50: 0.89 | 0.88
- EU50 / FR40: 0.88 | 0.88
- BTC / ETH: 0.87 | 0.87
- EU50 / IT40: 0.85 | 0.85
- ETH / SOL: 0.84 | 0.84
- XAGUSD / XAUUSD: 0.84 | 0.86
- BTC / SOL: 0.83 | 0.83
- EURUSD / GBPUSD: 0.81 | 0.81
- ES35 / IT40: 0.81 | 0.81
- ES35 / EU50: 0.80 | 0.81
- DE40 / FR40: 0.80 | 0.80
- EU50 / NL25: 0.78 | 0.78
- FR40 / IT40: 0.76 | 0.74
- US30 / US500: 0.75 | 0.74
- DE40 / IT40: 0.75 | 0.73
- JP225 / US100: 0.74 | n/a
- US2000 / US500: 0.74 | 0.69
- ES35 / FR40: 0.73 | 0.74
- US2000 / US30: 0.73 | 0.68
- NVDA / US100: 0.73 | 0.73
- FR40 / UK100: 0.72 | 0.72
- EU50 / UK100: 0.71 | 0.69
- AU200 / EU50: 0.70 | n/a
- CH20 / UK100: 0.69 | 0.68
- DE40 / UK100: 0.69 | 0.67
- DE40 / ES35: 0.69 | 0.68
- JP225 / US500: 0.69 | n/a
- AU200 / FR40: 0.68 | n/a
- ES35 / UK100: 0.67 | 0.67
- FR40 / NL25: 0.66 | 0.66
- CH20 / FR40: 0.66 | 0.65
- NL25 / UK100: 0.66 | 0.66
- EU50 / JP225: 0.66 | n/a
- IT40 / UK100: 0.65 | 0.64
- DE40 / NL25: 0.65 | 0.64
- NVDA / US500: 0.65 | 0.65
- EU50 / US500: 0.65 | 0.59
- IT40 / NL25: 0.63 | 0.61
- AU200 / IT40: 0.63 | n/a
- US100 / US2000: 0.62 | 0.57
- JP225 / NVDA: 0.62 | n/a
- EU50 / US2000: 0.62 | 0.55
- CH20 / EU50: 0.62 | 0.59
- ES35 / NL25: 0.62 | 0.62
- AU200 / ES35: 0.62 | n/a
- DE40 / US500: 0.61 | 0.52
- EU50 / US30: 0.61 | 0.50
- DE40 / US30: 0.61 | 0.52
- CH20 / DE40: 0.61 | 0.58
- DE40 / US2000: 0.60 | 0.54

## CME hours

Short answer: **CME equity-index futures did not move to 24-hour trading.** They already trade about 23 hours a day, five days a week. The "~23-hour" news the owner heard is most likely about US **stock exchanges**, which start 23-hour trading on 6 December 2026.

1. **Current CME hours (READ).** CME's E-nano FAQ and SER 9789R (Aug 2026), which use the same hours as the E-mini and Micro E-mini: CME Globex runs Sunday 6:00 p.m. to Friday 5:00 p.m. New York time (5:00 p.m. Sunday to 4:00 p.m. Friday Chicago time), with a daily maintenance break from 5:00 to 6:00 p.m. New York time. In UTC, that is a break of 22:00-23:00 in northern winter and 21:00-22:00 in summer. Sources: cmegroup.com/articles/faqs/faq-e-nano-equity-index-futures.html; cmegroup.com/content/dam/cmegroup/notices/ser/2026/08/ser-9789r.pdf.
2. **CME's 24/7 trading covers other products (READ).** CME's 24/7 page lists all cryptocurrency futures and options, 1-Ounce Gold futures, and 100-Ounce Silver futures (from 11 September, pending review). Equity-index futures are not on the list. The 24/7 products keep only a 2-minute weekday break (4:00-4:02 p.m. CT) and a Saturday 2:00-4:00 a.m. CT window. Source: cmegroup.com/markets/trade-24-7. A secondary page (SNIPPET, tradingsim.com, July 2026) says crypto moved to 24/7 on 29 May 2026 and equity-index futures "did not make that move".
3. **New CME equity contracts in 2026 (READ).** E-nano equity-index futures launched 24 August 2026: S&P 500 (NES, $0.50 per point), Nasdaq-100 (NNQ, $0.20 per point), Russell 2000 (N2K, $0.50 per point) and Dow (NDOW, $0.05 per point). They are a tenth of a Micro and trade the same 23 hours. Source: CME press release, 3 August 2026, and SER 9789R. CME also listed factor E-minis (SER 9798, 21 September 2026). Neither changes the hours.
4. **What does go to 23 hours: US stocks (READ).** Nasdaq's 23/5 hub page says that from 6 December 2026 Nasdaq adds a night session from 9:00 p.m. to 4:00 a.m. New York time. Trading will run from Sunday 9:00 p.m. to Friday 8:00 p.m., with a one-hour pause from 8:00 to 9:00 p.m. each day. NYSE Arca's extended-hours FAQ gives the same 6 December date and the same 23-hour window. A law-firm note (SNIPPET, WilmerHale, Sept 2026) says the SEC has conditionally approved 23x5 trading on five exchanges: 24X, Cboe EDGX, MEMX, Nasdaq and NYSE Arca. Sources: nasdaq.com/23-5-trading; nyse.com/publicdocs/nyse/NYSE_Extended_Hours_Trading_FAQ.pdf.
5. **Elsewhere, futures hours are getting longer too.** NSE IX (GIFT Nifty) moved to 23.5 hours on 2 November 2026 (READ, circular 230/2026). KRX has run its own KOSPI 200 night session (18:00-06:00 KST) since 2025 (READ). That is why the "around the clock" map below is mostly about futures and CFDs. Home cash sessions have not changed.

What this means for the scalper: the 23-hour futures session was already there, and the CFDs track it. When US stocks trade overnight from 6 December, the night hours of US 500 and US tech 100 may get more liquid, so their night spreads and moves should be measured again after that date. This is an ESTIMATE, not tested.

## The full universe of index markets a retail trader can reach

How to read this table:
- **IC / Pep** are the CFD symbols at IC Markets and Pepperstone. Both offer index CFDs on cTrader. "-" means the broker does not list it. IC symbols READ from ic.com/en/trading-hours and ic.com/en/trading-markets/indices; Pepperstone symbols READ from pepperstone.com/en/markets/indices (2026-11-09).
- **IBKR CFD** READ from IBKR's index CFD commission page (13 index CFDs). **IBKR future** READ from IBKR's futures margin table (2026-11-09): "yes" means the contract appears there.
- **Cash open (UTC)** is the home stock exchange's continuous-trading open, given as northern winter / northern summer. Japan, China, Hong Kong, Singapore, India, Taiwan, Korea and South Africa have no daylight saving, so one time serves all year. Australia shifts the other way (its summer is our winter). Labels: Japan READ (JPX), the rest ESTIMATE (well-known exchange hours, not re-read today).
- **Night session** says whether the main future trades outside the home cash hours in a separate session, with its hours.
- **Measured** gives the Dukascopy id when this report measured it. "No Dukascopy" means Dukascopy does not carry a CFD for it, so it stays unmeasured.

### Asia-Pacific

| Market | IC | Pep | IBKR CFD | Main future (exchange) | IBKR future | Cash open UTC (W / S) | Night session of the future | Measured |
|---|---|---|---|---|---|---|---|---|
| Japan, Nikkei 225 | JP225 | JPN225 | IBJP225 | Nikkei 225 (OSE, Japan); also CME NKD/MNK and SGX | yes (N225M, N225MC; CME NKD, MNK) | 00:00 / 00:00 (READ: 09:00-11:30, 12:30-15:30 JST) | Yes. OSE day 08:45-15:45, night 17:00-06:00 JST (READ, JPX) | jpnidxjpy (N3) |
| China A50 (FTSE China A50) | CHINA50 | CN50 | - | SGX FTSE China A50 "CN" (SGX) | yes (XINA50) | 01:30 / 01:30 (Shanghai 09:30 CST; ESTIMATE) | Yes. T 09:00-16:30, T+1 16:45-05:15 SGT (READ, SGX factsheet Jul 2026) | chiidxusd (new) |
| China H (Hang Seng China Enterprises) | CHINAH | CHINAH | - | HSCEI futures HHI (HKEX) | yes (HHI, MCH) | 01:30 / 01:30 (ESTIMATE) | Yes. 09:15-12:00, 13:00-16:30, after-hours 17:00-03:00 HKT (READ, HKEX) | No Dukascopy (only an ETF) |
| Hong Kong (Hang Seng) | HK50 | HK50 | IBHK50 | HSI futures (HKEX) | yes (HSI, MHI) | 01:30 / 01:30 (09:30 HKT; ESTIMATE) | Yes. Same as HSCEI: after-hours 17:00-03:00 HKT (READ, HKEX) | hkgidxhkd (N3) |
| Singapore (Straits Times / MSCI Singapore) | - | SCI25 (SNIPPET: "Singapore 25") | - | SGX STI futures; SGX MSCI Singapore | yes (STI) | 01:00 / 01:00 (ESTIMATE) | Yes, SGX T+1 session (ESTIMATE, hours not read) | sgdidxsgd "Singapore Blue Chip Cash Index" (new) |
| India (Nifty 50 / GIFT Nifty) | - | - | - | GIFT Nifty, NSE IFSC (NSE IX), GIFT City | yes (SGX NIFTY via GIFT Connect, USD) | 03:45 / 03:45 (NSE 09:15 IST; ESTIMATE) | Yes. From 2026-11-02: session 1 05:15-15:40 IST, session 2 16:05-02:45 IST, 23.5 h a day (READ, NSE IX circular 230/2026; SNIPPET for go-live date) | No Dukascopy |
| Taiwan (TAIEX) | - | - | - | TAIEX futures TX (TAIFEX); SGX FTSE Taiwan (TWN/MTWN) | SGX TWN, MTWN only; TAIFEX not in IBKR table | 01:00 / 01:00 (ESTIMATE) | Yes. TAIFEX 08:45-13:45, night 15:00-05:00 TWT (SNIPPET) | No Dukascopy |
| Korea (KOSPI 200) | - | - | - | KOSPI 200 futures (KRX) | yes (K200, K200M) | 00:00 / 00:00 (ESTIMATE) | Yes. Regular 08:45-15:45, night 18:00-06:00 KST, KRX's own since 2025 (READ, KRX) | No Dukascopy |
| Australia (S&P/ASX 200) | AUS200 | AUS200 | IBAU200 | SPI 200 (ASX 24) | yes (AP) | 23:00 (prev. day) / 00:00 | Yes. 09:50-16:30 and 17:10-07:00 (US summer) or 17:10-08:00 (US winter) Sydney time (READ, ASX) | ausidxaud (N3) |
| Malaysia, Thailand, Indonesia, Vietnam, NZ | - | - | - | FKLI (Bursa), SET50 (TFEX), SGX FTSE Indonesia/Vietnam, NZX | Bursa and SGX FID/FVN yes | various | not checked | No Dukascopy |

### Middle East and Africa

| Market | IC | Pep | IBKR CFD | Main future (exchange) | IBKR future | Cash open UTC (W / S) | Night session | Measured |
|---|---|---|---|---|---|---|---|---|
| South Africa (Top 40) | SA40 | SA40 | - | FTSE/JSE Top 40 futures (JSE) | not in IBKR table | 07:00 / 07:00 (JSE 09:00 SAST; ESTIMATE) | No (ESTIMATE) | soaidxzar (new; period a data stops 2026-08-31) |
| Israel (TA-35) | - | - | - | TA-35 futures (TASE) | not in IBKR table | about 07:00 / 06:00 (ESTIMATE) | No (ESTIMATE) | No Dukascopy |
| Saudi, UAE, Qatar, Turkey | - | - | - | Tadawul SF30; BIST 30 futures (Borsa Istanbul) | not in IBKR table | 06:00 to 07:00 (ESTIMATE) | No (ESTIMATE) | No Dukascopy |

No Middle East index CFD is offered by IC Markets or Pepperstone (READ: absent from both lists).

### Europe

| Market | IC | Pep | IBKR CFD | Main future (exchange) | IBKR future | Cash open UTC (W / S) | Night session | Measured |
|---|---|---|---|---|---|---|---|---|
| Germany (DAX 40) | DE40 | GER40 | IBDE40 | FDAX, Mini-DAX, Micro-DAX (Eurex) | yes (FDAX, FDXM, FDXS) | 08:00 / 07:00 | One long session 01:10-22:00 CET (READ, Eurex 2026 calendar) | deuidxeur (N3) |
| Euro Stoxx 50 | STOXX50 | EUSTX50 | IBEU50 | FESX, Micro FSXE (Eurex) | yes (FESX, FSXE) | 08:00 / 07:00 | One session 01:10-22:00 CET (READ) | eusidxeur (N3) |
| France (CAC 40) | F40 | FRA40 | IBFR40 | CAC 40 FCE, Mini MFC (Euronext Paris) | yes (FCE, MFC) | 08:00 / 07:00 | One session 08:00-22:00 CET (READ, Euronext FCE/MFC specs) | fraidxeur (new) |
| UK (FTSE 100) | UK100 | UK100 | IBGB100 | FTSE 100 "Z" (ICE Futures Europe) | yes (Z) | 08:00 / 07:00 | 01:00-21:00 London (ESTIMATE) | gbridxgbp (N3) |
| Switzerland (SMI) | SWI20 | SWI20 | IBCH20 | FSMI, Micro FSMS (Eurex) | yes (FSMI, FSMS) | 08:00 / 07:00 | 07:50-22:00 CET (READ, Eurex circular 025/21 for FSMS) | cheidxchf (new) |
| Spain (IBEX 35) | ES35 | SPA35 | IBES35 | IBEX 35, Mini IBEX (MEFF) | yes (IBX, MIX) | 08:00 / 07:00 | 08:00-20:00 CET (ESTIMATE) | espidxeur (new) |
| Italy (FTSE MIB) | IT40 | - | - | FTSE MIB FIB, Micro (IDEM) | yes (FIB, MICR) | 08:00 / 07:00 | not checked | itaidxeur (new) |
| Netherlands (AEX) | NETH25 | NETH25 | IBNL25 | AEX FTI, Mini MFA (Euronext Amsterdam) | yes (FTI, MFA) | 08:00 / 07:00 | 08:00-22:00 CET (ESTIMATE) | nldidxeur (new) |
| Germany Tech 30 / Mid 50 | TecDE30, MidDE50 | GERTEC30, MidDE50 | - | TecDAX, MDAX (Eurex) | yes | 08:00 / 07:00 | not checked | No Dukascopy |
| Sweden (OMXS30) | SE30 | - | - | OMXS30 (Nasdaq Stockholm) | yes (OMXS30) | 08:00 / 07:00 | No (ESTIMATE) | No Dukascopy |
| Norway (OBX) | NOR25 | NOR25 | - | OBX (Oslo) | not in IBKR table | 08:00 / 07:00 | No | No Dukascopy |
| Finland (OMXH25) | - | - | - | FFOX (Eurex) | yes | 08:00 / 07:00 (10:00 EET) | not checked | No Dukascopy |
| Poland (WIG20) | - | - | - | WIG20 futures (GPW) | not in IBKR table | 08:00 / 07:00 | No | plnidxpln (new) |

### Americas

| Market | IC | Pep | IBKR CFD | Main future (exchange) | IBKR future | Cash open UTC (W / S) | Night session | Measured |
|---|---|---|---|---|---|---|---|---|
| S&P 500 | US500 | US500 | IBUS500 | ES, MES, E-nano NES (CME) | yes (ES, MES, NES) | 14:30 / 13:30 | CME Globex Sun 17:00 to Fri 16:00 CT, daily break 16:00-17:00 CT (READ) | usa500idxusd (N3) |
| Nasdaq 100 | USTEC | NAS100 | IBUST100 | NQ, MNQ, E-nano NNQ (CME) | yes | 14:30 / 13:30 | same 23 h (READ) | usatechidxusd (N3) |
| Dow Jones 30 | US30 | US30 | IBUS30 | YM, MYM, E-nano NDOW (CBOT) | yes | 14:30 / 13:30 | same 23 h (READ) | usa30idxusd (new) |
| Russell 2000 | US2000 | US2000 | - | RTY, M2K, E-nano N2K (CME) | yes | 14:30 / 13:30 | same 23 h (READ) | ussc2000idxusd (new) |
| Canada (S&P/TSX 60) | CA60 | CA60 | - | SXF, mini SXM (Montreal Exchange) | yes (SXF, SXM) | 14:30 / 13:30 | Extended pre-open session (ESTIMATE, hours not read) | No Dukascopy |
| Brazil (Ibovespa) | - | - | - | IND, mini WIN (B3) | yes (WIN) | 13:00 / 13:00 (10:00 BRT; ESTIMATE) | No (ESTIMATE) | No Dukascopy |
| Mexico (IPC) | - | - | - | IPC, mini MIP (MexDer) | yes (IPC, MIP) | 14:30 / 14:30 (08:30 Mexico City, no DST; ESTIMATE) | No (ESTIMATE) | No Dukascopy |

### Commodities and US stocks (Part A item 3)

| Market | IC | Pep | Main future | Smallest future at IBKR (READ margin) | Measured |
|---|---|---|---|---|---|
| WTI crude | XTIUSD (avg spread 0.034, READ) | SpotCrude | CL (NYMEX) | MCL Micro WTI, 100 bbl; intraday initial $1,940 | lightcmdusd |
| Brent crude | XBRUSD (0.034, READ) | SpotBrent | Brent (ICE) | no micro found in IBKR table | brentcmdusd |
| Silver | XAGUSD | XAGUSD | SI (COMEX) | SIC 100-oz silver, $1,147; SIL 1,000-oz, $11,472 | xagusd |
| Natural gas | XNGUSD (0.004, READ) | NatGas | NG (NYMEX) | MNG Micro Henry Hub, $589 | gascmdusd |
| Copper | - (not in IC commodity list) | Copper (avg spread 2, SNIPPET) | HG (COMEX) | MHG Micro copper, $2,339 | coppercmdusd |
| NVDA, TSLA, AAPL, MSFT, AMZN | stock CFDs, MT5 only (READ) | US share CFDs, also on cTrader (READ) | (shares) | - | nvdaususd, tslaususd, aaplususd, msftususd, amznususd |

Stock CFD commission (READ): IC Markets $0.02 per share per side, MT5 only, not cTrader (ic.com stocks page: "exclusively on the IC MetaTrader 5 platform"). Pepperstone $0.02 per share per side, minimum $0.02, on cTrader too (pepperstone.com/en/markets/shares). A secondary source (SNIPPET, brokerdir.com) says IC's minimum is $2 per trade; not confirmed on IC's own page.

## Sanity checks

1. **Timestamps are UTC.** In the summer weeks, the median 1-minute range jumps most at 13 UTC for all four US indices (13:30 UTC = 09:30 New York) and at 07 UTC for all European indices (09:00 CEST). For UK 100 the jump is at 06 UTC, the futures-driven pre-open. China A50's biggest 5-minute moves start at 01:30 UTC (09:30 Shanghai), and its best hours are 01-02 UTC. Japan 225's best hour is 00 UTC (09:00 Tokyo). The stocks jump at 19 UTC, the last trading hour; their first hour, 13 UTC, is the first active hour, so it has no prior hour to jump from. READ (computed, split_half_n4.py).
2. **Dow vs Nasdaq is not a timestamp artefact.** At 1-minute resolution, US 30 vs US tech 100 correlates 0.51 at lag 0 and at most 0.02 at lags of plus or minus 1-2 minutes. US 30 vs US 500 is 0.73. In the first 90 minutes of New York, US 30 vs US tech 100 is 0.21 now and 0.52 last winter. So the low figure is this season's market, not a data shift. READ (computed, ad-hoc check, recorded here).
3. **Dukascopy vs broker spreads** (median spread over open hours, period a; IC average / Dukascopy): US 500 0.96, Euro Stoxx 50 0.99, China A50 1.05, Switzerland 20 1.06, US tech 100 1.26, UK 100 1.42, Japan 225 1.71, US 2000 1.83; cheaper at IC: Germany 40 0.82, Italy 40 0.92, US 30 0.72, France 40 0.75, Hong Kong 50 0.74, Netherlands 25 0.64, Spain 35 0.63, WTI and Brent 0.68, Australia 200 0.27, South Africa 40 0.29. So Australia 200 and South Africa 40 look poor mainly because of Dukascopy's spread. READ (sanity_n4.py; IC averages READ).
4. **Repeatability.** In the two 45-day halves of period a, most instruments' best 3 hours agree within one hour. The exceptions: Switzerland 20, UK 100 and Netherlands 25 swap the 13 UTC hour (US data time) for 08 UTC (the European open), because both hours are near-equal peaks; and gold adds 01 UTC in the second half. The best-hours ratio moves by up to about 40% between halves (Spain 35 2.6 vs 3.6, Italy 40 5.0 vs 7.0, US tech 100 33.9 vs 40.5). Treat gaps smaller than about 40% as no real difference. Against period b, all three best hours match within one hour for 29 of 33 instruments. For France 40, Amazon, Brent and silver, two of the three match. READ (n4_split_half.csv, n4_ranking.csv).
5. **Seasonal shifts that are real moves, not data errors.** At 13-15 UTC, WTI's median 5m range is 0.29% of price now, against 0.19% last winter, on the same 0.05 spread. Its ratio rose from 2.4 to 5.3. Japan 225 rose from 11 to 25 (N3 explained this: a smaller spread and a higher index). Natural gas fell from 4.2 to 2.3. READ (computed).
6. **South Africa 40**: Dukascopy serves period-a data only to 2026-08-28 (14 kept days, 13,465 rows). Its period-a ratio and its 0.61 correlation with gold (444 shared blocks) are thin. Period b (79 days) gives 3.1. READ.
7. **Singapore**: Dukascopy's "Singapore Blue Chip Cash Index" sits near 535 points. The Straits Times Index is about 4,000 (ESTIMATE), so this is a different index, probably MSCI Singapore (ESTIMATE). Its spread of 0.5 points against a 0.6-point move gives a ratio of 1.2. Drop it.
8. **Outliers** (largest 5m ranges, new instruments): Tesla 4.4% on 2026-09-25 13:30 UTC (the open), natural gas 4.4% on 2026-10-14 19:50, China A50 1.18% on 2026-10-22 01:30 (the open), silver 3.1% on 2026-09-04 12:30 (US data release slot), WTI and Brent 2.9% on 2026-09-24 16:15. They all sit at opens or scheduled-release times. I did not verify the news behind any of them. The medians ignore them.
9. **Work actually done.** The 21 new instruments were downloaded in full for both periods: 84 bid/ask files plus 4 FX rate files, with 0 failures (dukascopy_download_n4.log). Rows per file in period a: 108,000 for the 24-hour US indices, metals and energy; 77,400 for most European indices (Dukascopy serves no closed hours); 75,898 for each stock; 13,465 for South Africa 40. No sampling was used. In correlation (i), each pair of 24-hour markets shares up to 16,600 blocks. Japan 225 vs US tech 100 in both cash sessions has exactly 0 blocks, as expected.
10. **Why not double?** For index and oil CFDs, the ratio is capped by Dukascopy's spread, which is a fixed schedule per instrument. That is why the broker columns differ so much. For stocks, the $0.04 commission is about half the cost (NVIDIA: 0.036 spread + 0.04 commission). For FX, gold and silver, the assumed commission carries the same weight it had in N3.

## Assumptions and labels

- **Method**: the same as N3 (analyze.py helpers): 1-minute bid bars, complete clock-aligned 5m blocks, cost = ask minus bid at the last tick of each minute, median by UTC hour. Weekends and low-activity weekdays are dropped. An hour counts as open only if 80% of its minutes ticked.
- **Commission, ASSUMED**: index CFDs 0 (READ: IC and Pepperstone charge none on indices). Oil, natural gas and copper 0 (ESTIMATE: spread-only CFDs). Gold and FX $7 per lot round trip, as in N3. Silver $7 per 5,000-oz lot = $0.0014/oz (ESTIMATE). US stocks $0.02 per share per side (READ: Pepperstone and IC).
- **Cash sessions** used for correlation (ii), local time, ESTIMATE unless noted: New York 09:30-16:00 (US indices and stocks). Frankfurt clock 09:00-17:30 (Germany, Euro Stoxx, France, Netherlands, Italy, Spain). Zurich 09:00-17:20. London 08:00-16:30. Warsaw 09:00-16:50. Johannesburg 09:00-17:00. Tokyo 09:00-11:30 and 12:30-15:30 (READ, JPX). Hong Kong 09:30-12:00 and 13:00-16:00. Shanghai 09:30-11:30 and 13:00-15:00. Singapore 09:00-12:00 and 13:00-17:00. Sydney 10:00-16:00. Gold, silver and copper on the COMEX clock (New York 08:20-13:30, 08:25-13:25, 08:10-13:00). Oil and gas New York 09:00-14:30. FX London 08:00-17:00. Crypto has no home session, so all hours count.
- **Session ratio floor 5** and **cluster threshold 0.6** are my choices. They are shown with sensitivity at 0.5 and 0.7.
- **FX for dollar conversions** (READ, Dukascopy bid close): EURUSD 1.1148, GBPUSD 1.33603, USDJPY 158.253 (2026-11-08); AUDUSD 0.68616, USDCHF 0.81993, USDSGD 1.28117, USDCAD 1.41273 (2026-11-06). HKD = 7.8 per USD (ESTIMATE, the peg).
- **Contract sizes** (READ unless noted): CME E-nano NES $0.50, NNQ $0.20, N2K $0.50, NDOW $0.05 per point (SER 9789R). Micro-DAX EUR 1 (tick 1 point), Micro Euro Stoxx 50 EUR 1 (tick 0.5 points = EUR 0.50), Micro SMI CHF 1 (Eurex contract specifications). Mini CAC EUR 1 (tick 0.5 points = EUR 0.50, Euronext). SGX China A50 $1 per point (SGX factsheet). SPI 200 A$25 (ASX/spifutures). Nikkei 225 Micro JPY 10 (tick 5 points = JPY 50; SNIPPET, broker page). Mini Hang Seng HK$10, Mini AEX EUR 20, Mini IBEX EUR 1, Micro FTSE MIB EUR 0.20 (ESTIMATE; the last is implied by IBKR's margin ratio to the EUR 5 FIB). Micro WTI 100 bbl, Micro Henry Hub 1,000 MMBtu, Micro copper 2,500 lb, 1-Ounce Gold 1 oz, SIC 100 oz (ESTIMATE from the product names and standard specs).
- **IBKR margins** change daily; the values are those IBKR published on 2026-11-09 for a US resident. A margin account also needs equity above the margin, and the market-data minimum is USD 500.
- **Crypto**: N3's Binance-proxy returns are reused for correlations only. They were not re-measured.
- **Daylight saving**: Europe changed clocks on 2026-10-25 and the US on 2026-11-01. The UTC-hour tables blur those weeks by one hour; the session tables use local clocks.
- **Not measured, no Dukascopy data**: GIFT Nifty, TAIEX, KOSPI 200, Hang Seng China Enterprises, S&P/TSX 60, Ibovespa, IPC, OMXS30, OBX, OMXH25, TecDAX, MDAX, TA-35 and the Gulf indices. Dukascopy carries only ETFs on some of them (for example a Hang Seng H-share ETF and an S&P BSE SENSEX India ETF). I did not use the ETFs as stand-ins.

## Sources (read 2026-11-09)

- IC Markets: ic.com/en/trading-pricing/trading-hours; ic.com/en/trading-markets/indices; /commodities; /stocks.
- Pepperstone: pepperstone.com/en/markets/indices; /markets/indices/index-fees; /markets/shares; costs and charges PDF (eu-assets.contentstack.com, V09.2026, SNIPPET).
- IBKR: interactivebrokers.com/en/pricing/market-data-pricing.php; investors.interactivebrokers.com/en/trading/margin-futures-fops.php; interactivebrokers.co.uk/en/pricing/commissions-cfd-index.php; interactivebrokers.com/en/trading/nifty-50-index-futures.php.
- CME: cmegroup.com/markets/trade-24-7; /articles/faqs/faq-e-nano-equity-index-futures.html; SER 9789R and SER 9798 (Aug 2026); press release 2026-08-03 (E-nano).
- Nasdaq: nasdaq.com/23-5-trading. NYSE: NYSE_Extended_Hours_Trading_FAQ.pdf. WilmerHale client alert 2026-09-29 (SNIPPET).
- JPX: jpx.co.jp/english/derivatives/rules/trading-hours/; /equities/trading/domestic/01.html. HKEX: Trading-Hours/Derivatives-Market. SGX: FTSE China A50 factsheet (Jul 2026). NSE IX: circular NSEIFSC/TRADE/2720 (230/2026). KRX: global.krx.co.kr KOSPI 200 futures and Night Session pages. ASX: asx.com.au index-derivatives trading hours. Eurex: trading calendar 2026; circular 025/21 contract specifications; micro product suite page. Euronext: MFC and FCE contract specifications. TAIFEX hours: alphaprime.trading (SNIPPET).

## Reproduce

From `numbers-talk/measure/` (dukascopy-node 1.51.1; Python with pandas, run with `python -I`):
1. `INSTRUMENTS="usa30idxusd ussc2000idxusd fraidxeur cheidxchf espidxeur itaidxeur nldidxeur plnidxpln sgdidxsgd soaidxzar chiidxusd lightcmdusd brentcmdusd xagusd gascmdusd coppercmdusd nvdaususd tslaususd aaplususd msftususd amznususd" bash run_dukascopy_all.sh` (about 15 minutes), plus N3's own downloads.
2. FX rates: `node fetch_dukascopy.mjs <audusd|usdchf|usdcad|usdsgd> fx 2026-11-05 2026-11-07`.
3. `python -I analyze_n4.py`, then `python -I split_half_n4.py`, `python -I sanity_n4.py`, `python -I build_n4_tables.py`.

Outputs: `measure/results/n4_ranking.csv`, `n4_hourly_detail.csv`, `n4_session_detail.csv`, `n4_corr_all_hours.csv`, `n4_corr_cash_sessions.csv`, `n4_corr_cash_nobs.csv`, `n4_summary.json`, `n4_split_half.csv`, `n4_sanity.json` and `n4_tables.md`. `data/` is gitignored.
