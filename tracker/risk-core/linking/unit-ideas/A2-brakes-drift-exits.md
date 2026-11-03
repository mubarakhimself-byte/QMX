# Unit idea bank: seeds found while dissecting brakes, drift, verification and exits (A2)

Written 2026-11-03 by the Stage A dissector for cluster A2. These are trading signals or market readings, not risk or sizing mechanisms, so they are not in `linking/components/A2-brakes-drift-exits.yaml`. They are not ranked. Paths are relative to `D:\QMX-worktrees\risk-plan\tracker\risk-core\`. Market-structure readings that belong to cluster A3 (turbulence, absorption ratio, liquidity states, weekend crypto risk, quarter-hour effect) are left to A3.

## 1. Mean-reversion half-life per instrument and session

- **Source:** `research/R4-alphaxiv/chat-13-stops-and-exits.md:165` (Leung and Li, https://www.alphaxiv.org/abs/1411.5062); gold figure from `research/R6-alphaxiv-papers/T-02-trading-styles-scalping-intraday.md:37-38` (https://www.alphaxiv.org/abs/2605.04004).
- **Reading:** fit an Ornstein-Uhlenbeck process to a price or spread and read its half-life, ln(2)/mu. It tells a mean-reversion unit how long a trade should take to revert and when a stale trade has lost its reason. The MNQ study measured gold intraday mean reversion with a half-life of about 8 hours, too slow for 5-minute scalping.
- **Style, timeframe, classes:** mean-reversion scalpers and intraday units; FX crosses, spreads and pairs, metals.
- **Data QMX needs:** bars per instrument and session, with causal (rolling, point-in-time) estimation and its uncertainty.
- **New MIS reading or QML block:** yes. A `reversion-half-life` reading per instrument and session would sit beside the shipped `half-life-of-mean-reversion` block, which a unit can already bind into its own logic. It also feeds the time exit (component 233).
- **Evidence:** theory for the exit use (simulation of an OU model); author backtest for the gold half-life.

## 2. Multi-horizon trend or reversal state

- **Source:** `research/R4-alphaxiv/chat-13-stops-and-exits.md:20,23,159,166` (Safari and Schmidhuber, https://www.alphaxiv.org/abs/2501.16772).
- **Reading:** trend strength measured at several horizons. Futures across equity indices, rates, currencies and commodities (2010-2023, end-of-minute data) show reversal at very short minute scales and weak trend persistence over longer intraday horizons. The shortest-horizon effects differ by asset and time zone.
- **Style, timeframe, classes:** intraday units; the state could choose between a mean-reversion exit and a trend exit (component 265). Index futures, FX, commodities.
- **Data QMX needs:** minute bars per instrument, session-tagged.
- **New MIS reading or QML block:** yes, a multi-horizon trend-strength reading per instrument and session.
- **Evidence:** author backtest (regressions with very small R²; the authors warn minute-scale effects may not survive costs).

## 3. MNQ "RTH Confluence" positive control

- **Source:** `research/R6-alphaxiv-papers/T-02-trading-styles-scalping-intraday.md:33-43` (https://www.alphaxiv.org/abs/2605.04004).
- **Signal:** GMM regime transitions during regular trading hours with a 60-75 minute hold. It was one of two "positive controls" that passed the study's gates: OOS t = 3.11 on 196 trades.
- **Style, timeframe, classes:** intraday, 5-minute bars, US index futures (MNQ).
- **Data QMX needs:** MNQ or index CFD 5-minute bars, an RTH session calendar, and a regime model (GMM).
- **New MIS reading or QML block:** a regime-transition reading would be new; the unit could carry it itself.
- **Evidence:** author backtest. The author lists 53 or more parameter combinations tried before locking it, so the OOS t is optimistic.

## 4. MNQ "London Signal B" positive control (fragile)

- **Source:** same paper, `T-02:41-43`.
- **Signal:** a London-session pattern on MNQ, OOS t = 4.30 on 247 trades. It flips sign with a 15-minute delay, so it may be an artefact. Tick data would decide.
- **Style, timeframe, classes:** intraday, US index futures traded in London hours.
- **Data QMX needs:** 5-minute bars, then tick data for the delay test.
- **New MIS reading or QML block:** no.
- **Evidence:** author backtest; failed the delay-sensitivity check, which is a reason to test, not to trust.

## 5. Negative seed: Asia-session expansion bars are already spent

- **Source:** `T-02:36-37` (2605.04004).
- **Reading:** following Asia-session expansion bars on MNQ gave t = -11.52 the wrong way, because the move is used up inside the signal bar. A continuation unit on that bar loses; a fade is untested.
- **Style, timeframe, classes:** intraday, index futures, Asia session.
- **Data QMX needs:** 5-minute bars, session calendar.
- **New MIS reading or QML block:** no. It could become a placement veto ("do not run continuation logic on Asia expansion bars").
- **Evidence:** author backtest (negative result).

## 6. Negative seed: no post-news drift after the spike bars

- **Source:** `T-02:37` (2605.04004).
- **Reading:** on MNQ news days there was no drift after the spike bars, so a "trade the post-news drift" unit has no support there.
- **Style, timeframe, classes:** intraday, index futures, scheduled news.
- **Data QMX needs:** calendar with release times, 5-minute bars.
- **New MIS reading or QML block:** no.
- **Evidence:** author backtest (negative result).

## 7. Change-point probability as a market reading

- **Source:** `research/R5-mql5-corpus-ideas.md:123` (MQL5 article 23482); `research/R6-alphaxiv-papers/T-03-macro-and-microstructure.md:55-74` (https://www.alphaxiv.org/abs/2609.07989).
- **Reading:** a per-bar probability that the regime just broke (BOCPD run-length posterior), best with log-normal regime durations instead of a constant hazard, and flagged only when the most likely run length falls. It measures change, not direction. 23482 showed its timing carried information against a random brake.
- **Style, timeframe, classes:** any; tested on EURUSD M30 and on US stock order flow.
- **Data QMX needs:** bars or order-flow buckets per instrument.
- **New MIS reading or QML block:** a refinement. The MIS packs already run a CUSUM change-point block; a BOCPD reading with a duration prior would be new.
- **Evidence:** controlled test (23482, few trades); author backtest (2609.07989, two stocks, four months).

## 8. Regime age as a market reading

- **Source:** `research/R5-mql5-corpus-ideas.md:124` (MQL5 article 24460).
- **Reading:** how old the current regime is, under a hidden semi-Markov model with explicit durations. On 8 months of XAUUSD M5, the trades closed by the duration gate made money (59.3% wins) while the system as a whole lost.
- **Style, timeframe, classes:** scalper and intraday; metals in the test; durations differ by class.
- **Data QMX needs:** bars per instrument; a fitted duration distribution per class.
- **New MIS reading or QML block:** yes, a `regime-age` reading, which also feeds the add-size taper (component 173).
- **Evidence:** author backtest (short sample).

## 9. Per-instrument calibrated volatility-break alarm

- **Source:** `research/R5-mql5-corpus-ideas.md:328,454-462` (MQL5 articles 23043, 23103).
- **Reading:** CUSUM on standardised returns, with its threshold fitted on each instrument's own history. Theory thresholds fired about 5 times too often. The alarms caught mostly variance shifts, and latency at macro events was a few bars.
- **Style, timeframe, classes:** all; tested on FX, gold, DE40 and USTEC across three timeframes.
- **Data QMX needs:** bars per instrument; a calibration record per instrument and detector.
- **New MIS reading or QML block:** a calibration change to the shipped MIS CUSUM reading: a threshold per instrument instead of one formula.
- **Evidence:** author backtest (cross-asset).

## 10. FX fix reversal (a "sniping window" in the professional sense)

- **Source:** `research/R2-trader-practice-windows-drift-isolation-breadth.md:54,63` (Bank of Canada SWP 2021-48).
- **Signal:** across 9 currencies in 1999-2019, the dollar rises about 2.5 bp before the Tokyo, ECB and London fixes and falls back after, driven by dealers hedging fixed dollar demand. Gross Sharpe is up to 2.45. At full indicative spreads the Sharpe is negative; at half spreads it is 0.12 to 1.03.
- **Style, timeframe, classes:** minutes around the fixes; FX majors.
- **Data QMX needs:** fix times, minute bars, and QMX's own measured spread per hour at cTrader (the cost journal decides whether the edge exists).
- **New MIS reading or QML block:** a fix-window calendar entry per currency.
- **Evidence:** author backtest (academic, long sample); depends on cost. Cluster A3 may also hold it.

## 11. OU spread unit with derived entry, target and stop

- **Source:** `research/R4-alphaxiv/chat-13-stops-and-exits.md:76-86` (1411.5062), with follow-ons 2309.16008 (signature timing) and 1706.07021 (stop-loss and leverage in energy).
- **Signal:** trade a mean-reverting spread whose entry band, take-profit and stop come from the fitted OU parameters and costs. Raising the stop level lowers the optimal target.
- **Style, timeframe, classes:** pairs and spread units; FX crosses, energy calendar spreads, index pairs.
- **Data QMX needs:** synchronised bars for both legs, cost per leg, and a causal parameter fit.
- **New MIS reading or QML block:** a spread-construction block and an OU-fit block.
- **Evidence:** simulation (analytical model with an illustrative ETF example; no out-of-sample P&L).
