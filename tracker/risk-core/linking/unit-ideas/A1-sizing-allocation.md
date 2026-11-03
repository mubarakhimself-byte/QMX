# Unit idea bank: seeds found while dissecting the sizing and allocation cluster (A1)

Signals and market readings, not risk or sizing. Not ranked. Each seed is what its source claims; nothing here was re-tested. Paths are relative to `tracker/risk-core/`.

## 1. FX fix reversal
- **Source:** `research/R2-trader-practice-windows-drift-isolation-breadth.md:54` (Bank of Canada swp2021-48; JF 2024 version).
- **Signal:** the dollar rises about 2.5 bp before the Tokyo, ECB and London 16:00 fixes and falls the same afterwards, across 9 currencies, 1999-2019. The cause is dealers hedging fixed dollar demand.
- **Style, timeframe, classes:** intraday, minutes around each fix; FX majors.
- **Data QMX needs:** fix times per currency; quotes at second-to-minute resolution; QMX's own measured spread at the fix, because the result turns on cost.
- **MIS or QML:** a calendar state for fix windows (the MIS page already plans gold's London fix windows); one QML entry block.
- **Evidence:** academic backtest. Gross Sharpe up to 2.45. Negative at full quoted spreads; 0.12 to 1.03 at half spreads.

## 2. Month-end London fix rebalancing
- **Source:** `R2:56` (sciencedirect S1386418114000779).
- **Signal:** equity gains over the month predict the currency weakening before the month-end fix, as equity managers rebalance their hedges.
- **Style, timeframe, classes:** once a month, intraday into the fix; FX against equity-heavy currencies.
- **Data QMX needs:** month-to-date equity index returns per country; fix calendar.
- **MIS or QML:** an MIS day-tier reading, "month-to-date equity move per currency"; one QML block.
- **Evidence:** academic; the abstract makes no cost claim.

## 3. Intraday momentum: first half-hour predicts the last half-hour
- **Source:** `research/R4-alphaxiv/chat-25-C-intraday-day-trading.md:87-97`; `R4-alphaxiv-synthesis.md:115-117`; `R2:58` (60+ futures).
- **Signal:** the market's first 30-minute return predicts the direction of its last 30 minutes (S&P ETF 1993-2013). Extended internationally; Chinese stocks show both momentum and reversal.
- **Style, timeframe, classes:** intraday, session open and close; index futures, ETFs, stock indices.
- **Data QMX needs:** exchange session calendars; bars aligned to the cash open and close.
- **MIS or QML:** a session-tier reading, "opening-window return"; a QML entry block.
- **Evidence:** published backtests. The futures and ETF study says it survives costs. It is market- and horizon-specific.

## 4. Opening-range breakout on "stocks in play"
- **Source:** `research/R5-mql5-corpus-ideas.md:100-101` (MQL5 17745, 23226); `R2:61`.
- **Signal:** ORB limited to stocks with unusual relative volume at the open. The cited study's net Sharpe was 2.81 for the top 20. A pre-screen keeps price, volume and ATR above $0.50. Win rate is below 30 %. Three Concretum ORB variants combined cut max drawdown to about 10 %, against 15 %+ alone, at about 0.3 monthly correlation.
- **Style, timeframe, classes:** intraday ORB, 1-5m; US stocks (FX and gold use London or NY opens).
- **Data QMX needs:** real volume and a 20-day median by minute (RVOL); stock route (none in this build).
- **MIS or QML:** RVOL as a reading for real-volume markets (it is a dictionary concept, not an MIS reading); ORB entry blocks.
- **Evidence:** the published paper is net of costs for one period. The MQL5 rebuild is in-sample.

## 5. Volatility-managed momentum and FX carry
- **Source:** `research/R4-alphaxiv/chat-29-G-multi-asset-normalisation.md` (turn 3 section 2; Barroso and Santa-Clara 2015; Moreira and Muir 2017).
- **Signal:** cut momentum exposure when its realised volatility is high, to avoid momentum crashes. FX carry with volatility timing showed positive historical results.
- **Style, timeframe, classes:** swing to monthly; equities (momentum), FX (carry).
- **Data QMX needs:** carry and swap data per pair; tradable quotes; currency factor exposures.
- **MIS or QML:** a "carry differential" reading per pair; QML carry block.
- **Evidence:** published backtests. Cederburg et al. challenge whether volatility timing holds in real time.

## 6. Time-series trend across futures
- **Source:** `chat-29` (turn 3 section 2); `R4-alphaxiv-synthesis.md:161` (Value and Momentum Everywhere).
- **Signal:** trend following across many futures, each scaled to comparable dollar risk.
- **Style, timeframe, classes:** daily swing; futures in every sector.
- **Data QMX needs:** continuous futures with correct roll handling; paid futures data, which this program does not include.
- **MIS or QML:** trend-against-range reading (planned); QML trend block.
- **Evidence:** a long academic record; not re-tested here.

## 7. Crypto 15-minute reversal (signs, not sizes)
- **Source:** `research/R6-alphaxiv-papers/T-02-trading-styles-scalping-intraday.md:79-88` (2608.21888).
- **Signal:** 90 % of 183 Binance pairs show significant 15-minute sign reversal against 2.7 % of US stocks, in every coin-year since 2021, with a frozen holdout and a permutation null. Gross edge peaks near 1.3 bp against about 5 bp of costs.
- **Style, timeframe, classes:** scalper 15m; crypto spot and perpetuals.
- **Data QMX needs:** real trade tape per venue; fee tier; maker fill markouts.
- **MIS or QML:** a "short-horizon reversal strength" reading per crypto market; a maker-only QML block.
- **Evidence:** out-of-sample measurement. Fees bind, so the edge is inside costs at retail fee tiers.

## 8. Quarter-hour effect in 24/7 markets
- **Source:** `R4-alphaxiv-synthesis.md:124` (2607.09426); `R6-synthesis.md` (combination with the market maker's dilemma).
- **Signal:** recurring bursts in the first seconds after each quarter hour. Quarter-hour order imbalance predicts the first 10 seconds.
- **Style, timeframe, classes:** execution timing in seconds; crypto.
- **Data QMX needs:** tick or trade tape with timestamps.
- **MIS or QML:** a tick-tier "bar-boundary burst" reading, used for execution timing (avoid entering at the boundary) more than for direction.
- **Evidence:** a 2026 preprint; R6 rates it useful for execution timing, not for trading against costs.

## 9. MNQ positive controls: regime transitions with 60-75 minute holds
- **Source:** `T-02:24-50` (Mesfin 2605.04004).
- **Signal:** GMM regime-transition signals held 60-75 minutes passed where 14 retail families failed: RTH confluence OOS T = 3.11 on 196 trades; London signal B OOS T = 4.30 on 247 trades. The London signal flips sign with a one-bar delay.
- **Style, timeframe, classes:** intraday 5m entries with longer holds; micro index futures.
- **Data QMX needs:** 5m bars, ideally ticks, to test the delay sensitivity.
- **MIS or QML:** a regime-transition reading; QML block.
- **Evidence:** author backtest. 53+ combinations were tried before the RTH control was locked, so its OOS T is optimistic.

## 10. Gold mean reversion is too slow for intraday scalping
- **Source:** `T-02` (MNQ study, gold OU arm); `R6-synthesis.md` class table.
- **Reading:** gold's intraday OU half-life is about 8 hours, too slow for 5-minute scalping.
- **Style, timeframe, classes:** reading for unit placement; metals.
- **Data QMX needs:** mid prices; half-life estimate (A13b plans half-life as an entry).
- **MIS or QML:** a "mean-reversion half-life" day-tier reading per market. It would tell placement whether a mean-reverting scalper fits a market.
- **Evidence:** author backtest.

## 11. Implied-to-realised volatility ratio for gold and indices
- **Source:** `R5:126` (MQL5 23734).
- **Reading:** implied over realised volatility as a forward-looking risk state. The author says it is "not a timing trigger".
- **Style, timeframe, classes:** intraday to swing; gold, major indices, some FX (needs liquid options).
- **Data QMX needs:** an options implied volatility feed, published as JSON by an outside job.
- **MIS or QML:** a new MIS day-tier reading. Component A1-sizing-allocation-013 uses it for size.
- **Evidence:** mechanism check only.

## 12. Quote-duration activity gauge (ACD)
- **Source:** `R5:81` (MQL5 24742).
- **Reading:** the wait between quotes. In EURUSD's quietest half hour it is about 47 times longer than in its busiest. An Engle-Russell duration model adds a small but significant gain to next-minutes volatility forecasts on six symbols.
- **Style, timeframe, classes:** scalper 1m; FX, metals, index CFDs.
- **Data QMX needs:** tick quote timestamps. Recalibrate monthly and on any broker change.
- **MIS or QML:** a tick-tier reading, "activity against usual". The MIS plans tick rate against usual; this adds a duration model.
- **Evidence:** out-of-sample gain on six symbols.

## 13. Session volatility features beat session flags
- **Source:** `R5:105` (MQL5 22516; 22274 feature importance).
- **Reading:** session *volatility* columns carried 25.6 % of model importance against 2.5 % for session *flags*.
- **Style, timeframe, classes:** intraday models; FX.
- **Data QMX needs:** volatility per session window.
- **MIS or QML:** supports gating sessions on measured volatility, not on the clock; a session-tier volatility reading.
- **Evidence:** out-of-sample inside 22274.

## 14. Network momentum along lead-lag links
- **Source:** `R5:62` (MQL5 23763).
- **Signal:** learn which markets lead which, and spread momentum along those links.
- **Style, timeframe, classes:** swing; cross-asset.
- **Data QMX needs:** aligned returns across markets.
- **MIS or QML:** a cross-market "lead-lag graph" reading on This PC. It could also flag correlated units before both fire.
- **Evidence:** in-sample.

## 15. Weekend crypto volatility leads Monday risk
- **Source:** `R4-alphaxiv-synthesis.md:321`; `R6-synthesis.md` (2610.35702; combination with cushion sizing).
- **Reading:** a volatile crypto weekend predicts larger Monday gaps and variance in indices, metals and bonds.
- **Style, timeframe, classes:** Monday opening risk; indices, metals, bonds (read from crypto).
- **Data QMX needs:** crypto weekend realised volatility.
- **MIS or QML:** an MIS calendar-tier reading, "weekend crypto stress". It could raise the worst-move input for Monday sizing.
- **Evidence:** a 2026 paper read by R6.

## 16. Macro prediction-market probabilities forecast crypto volatility
- **Source:** `R4-alphaxiv-synthesis.md:164` (2604.01431); `chat-26` turn 3.
- **Reading:** daily changes in Kalshi macro-contract probabilities forecast 5-day crypto volatility for some channels. One example implies about 7 % less BTC weight under inverse-volatility sizing. This forecasts volatility, not direction.
- **Style, timeframe, classes:** daily; crypto.
- **Data QMX needs:** timestamped prediction-market prices.
- **MIS or QML:** a day-tier "macro repricing" reading feeding volatility forecasts.
- **Evidence:** a 2026 preprint, not read by R6.

## 17. Shared dollar and carry factors in FX
- **Source:** `R4-alphaxiv-synthesis.md:158` (Lustig, Roussanov and Verdelhan 2011).
- **Reading:** FX pairs load on a common dollar factor and a carry factor.
- **Style, timeframe, classes:** reading for exposure and placement; FX.
- **Data QMX needs:** a basket of pairs; interest differentials.
- **MIS or QML:** a "USD factor" and "carry factor" reading. This PC already plans currency strength. It also feeds factor budgets (component 097).
- **Evidence:** a published academic factor model.

## 18. Order-flow imbalance (OFI, MLOFI) as a short-horizon pressure reading
- **Source:** `R4-alphaxiv-synthesis.md:184-186`; `chat-24` turn 3 combination D.
- **Signal:** signed queue changes at the best quotes explain about 65 % of contemporaneous 10-second mid changes. Ten-level MLOFI cut out-of-sample RMSE 15-74 % against best-level OFI on six Nasdaq stocks.
- **Style, timeframe, classes:** scalper, seconds; exchange futures and stocks. Not valid on CFD quotes or spot FX.
- **Data QMX needs:** the traded venue's L2 book (futures routes are out of this program).
- **MIS or QML:** a tick-tier node reading (the node plans depth imbalance); run as a shadow label before any veto.
- **Evidence:** academic, explanatory. Forecasting is not proven. (The A3 cluster likely covers this in more depth.)
