---
ticket: research-mis-sensor-speed
title: Which market states a 1m or 5m scalper can use in time
date: 2026-10-30
author: research agent 1 (MIS), Opus poteto-agent
method: the literature in research 37 (rows E01-E49 cited here, not repeated), plus three simulations run this session (scripts named in §6; copies in `research/22-study/`). Real price data was not used: no Library partition was found on this machine, and a Binance Vision download needs his go.
labels: CHECKED (URL, path:line or command) or INFERRED. Simulation numbers are CHECKED as command output and INFERRED as statements about real markets.
---

# 22: Which market states a 1m or 5m scalper can use in time

## How to read this

- Options and evidence, not a design. Every threshold is a number with a starting default (§8).
- Research 37 holds the paper catalogue (E-ids) and the style × data matrices. This file answers the speed questions: lag and false alarms per sensor, fast proxies, order flow, spot FX stand-ins, indicators versus models, the persistence family, impossible combinations, the label-at-entry replay, and which knot (a) options survive.
- His objection, which this file tests rather than overrules: "you are not going to put an HMM inside a scalper's MIS. That makes no sense. But you can put multiple indicators inside a scalper's MIS" (`T2:219`, CHECKED). And on the four fixes: "this 44 minute thing is huge" and "Quick proxies, I don't know, man" (`T2:325`, CHECKED).

## Short answer

1. **Per trade, a 1m or 5m scalper can use: volatility against its usual level, spread and cost, tick rate and depth against usual, session and scheduled events, and order-book pressure where a book exists.** These show a change in minutes or less. A 50% volatility rise shows in about 27 bars from 1-minute closes and about 8 bars from bar ranges (CHECKED command, §6 S3), down from the 44 minutes he flagged.
2. **"Trending" or "mean-reverting" can only be a session or day list at 1m and 5m, unless the state lasts much longer than the sensor's window.** A strong trend takes about 4 hours to show at one false alarm per 10 days; strong bar-level mean reversion about 4 to 5 hours; weak versions a day or more (CHECKED command, §6 S1). Bar size does not change the time for direction, only the bar count (INFERRED algebra, §2).
3. **The label known at entry is the only honest one, and it loses most of its value when states are short.** With 2-hour states and a 4-hour window, gating a fade scalper by the at-entry label gave no gain in total result over no gate, while the same label computed with hindsight claimed a 76% better edge per trade. With 2-day states the at-entry label kept 81% of the perfect-knowledge edge (CHECKED command, §6 S2).
4. **His seed holds in a sharper form.** The split that matters is lag against holding time, not "indicator versus model". Small online models (CUSUM, Kalman, two-scale volatility) are fast and fit a scalper; HMMs and regime models belong on the session and day clocks because they flip falsely and need long windows (E19).
5. **Hurst, variance ratio and efficiency ratio are one family with autocorrelation and entropy: persistence readings.** They are sensors like any other, but slow. Efficiency ratio sees trend and is blind to mean reversion; variance ratio and autocorrelation see mean reversion and miss trend (§6 S1). Hurst needs at least about 1,000 points to mean anything (E37), which is 17 hours of 1-minute bars.
6. **Price-only mean-reversion sensors are fooled by bid-ask bounce.** Bounce noise at a quarter of a bar's sigma doubles to quintuples their false alarms; at half, 10 to 130 times (§6 S1). Use mid or one-sided quotes, or check the noise ratio first.
7. **Order flow is fast but short-lived.** It predicts seconds ahead and is gone by 30 to 60 seconds (E06, E46). It can show that a move is liquidity pressure, which tends to revert within the hour (E13, E09), sooner than price statistics can. No study tests order flow as a mean-reversion state detector (empty cell, research 37 §4).
8. **Spot FX has no tape.** The stand-ins are tick volume (tracks traded volume at the hourly scale, vendor study E30), quote-based spread and tick rate, the cTrader depth book (untested as a predictor), and a borrowed CME futures tape (a second feed and a dependency).

---

## 1. The question in his frame

He orders the MIS by style, then timeframe, then data (`T2:219`, CHECKED; STATE `:119`). For a scalper on 1m or 5m bars that means: which readings are fast enough to change a trade, and which only pick markets for the session.

Any trader already knows three things, so they are stated, not asked (research 35 K-list via `mis-field.md` §3 "Dropped", CHECKED): sessions and news windows matter; spread against target decides whether a scalp pays; a 1m and a 5m version of one logic are one idea (his own correction, `T2:1001` as cited in `mis-field.md` S-CORR, CHECKED).

## 2. Lag and false alarms per sensor at 1m and 5m

**Method (S1, S3).** Gaussian 1-minute bars with sigma 1. Each sensor alarms when its rolling value crosses a threshold. The threshold is set so that, on no-change data, alarm episodes arrive once per 14,400 bars (10 trading days of 24-hour 1m bars, the spacing research 05 used) or once per 1,440 bars (one a day). Then the regime changes and the bars to first alarm are counted, 300 runs each. Numbers are medians, then the 90th percentile in brackets. "miss" means more than half the runs saw nothing within 4,000 bars. The episode-spacing metric is comparable across sensors here; it is not identical to research 05's average run length, so compare orders of magnitude with 05, not exact values.

**Regimes.** Strong trend: drift 0.2 sigma per bar. Weak trend: 0.1. Strong mean reversion: bar autocorrelation −0.2. Weak: −0.1. Volatility jump: ×1.5.

**At one false alarm per 10 days (CHECKED command `mis_sensor_lag.py 14400`; S3 for range and ticks):**

| Sensor (window in 1m bars) | Strong trend | Weak trend | Strong mean reversion | Weak mean reversion | Vol ×1.5 | False-alarm spacing with bounce noise 0.5 sigma |
| --- | --- | --- | --- | --- | --- | --- |
| Efficiency ratio (30) above | 1,124 (3,104) | miss | miss | miss | miss | 133,323 (fewer alarms) |
| Efficiency ratio (240) above | 264 (702) | 1,530 (miss) | miss | miss | miss | 399,760 |
| Variance ratio q=4 (240) below | miss | miss | 318 (640) | 1,072 (3,300) | miss | **113** |
| Variance ratio q=4 (240) above | 2,376 (miss) | miss | miss | miss | miss | 399,760 |
| Lag-1 autocorrelation (60) below | miss | miss | 350 (1,211) | 1,838 (miss) | miss | **435** |
| Lag-1 autocorrelation (240) below | miss | miss | 240 (487) | 1,282 (miss) | miss | **107** |
| Realised vol from closes (30) above | miss | miss | miss | miss | 27 (69) | 15,999 |
| CUSUM on squared returns (vol ×1.5) | miss | miss | miss | miss | 29 (61) | 16,667 |
| Parkinson range vol (10) above | n/a | n/a | n/a | n/a | 8 (16) | not run |
| Tick realised vol (3), noise-free ticks | n/a | n/a | n/a | n/a | 1 (1) | not run; real ticks carry noise (E28) |
| CUSUM for a known drift (oracle) | 226 (453) | 892 (2,436) | miss | miss | 1,408 | 399,999 |

**Bounce noise at three levels, threshold set for one alarm a day (CHECKED command):**

| Sensor | Noise 0.1 sigma | 0.25 sigma | 0.5 sigma | Designed |
| --- | --- | --- | --- | --- |
| Efficiency ratio (60) | 1,262 | 1,960 | 8,332 | 1,440 |
| Variance ratio (60) below | 1,197 | 704 | 165 | 1,440 |
| Variance ratio (240) below | 896 | 331 | 83 | 1,440 |
| Autocorrelation (60) below | 1,123 | 482 | 110 | 1,440 |
| Autocorrelation (240) below | 1,208 | 268 | 75 | 1,440 |
| Realised vol (30) | 1,242 | 1,449 | 1,294 | 1,440 |

**What the tables say (INFERRED from the runs and research 05's bound):**

- **Volatility is minutes; direction is hours.** The order matches research 05 §1.3. The 44 minutes he flagged becomes about 27 from closes and about 8 from bar ranges, because a range carries about five times the information of a close (E27). Clean ticks would be near-instant, but real ticks carry bid-ask noise, which is why practice samples FX at 5 to 30 minutes for volatility (E28). A two-scale estimator keeps most of the tick speed without the noise (E28).
- **1m versus 5m.** For a volatility change, information per bar does not depend on bar size, so the same bar count is needed: about 27 bars is 27 minutes on 1m and over 2 hours on 5m. For a drift, a 5m bar carries five times the information of a 1m bar, so the bar count falls by five and the time stays the same: roughly 4 hours either way for a strong trend. (Gaussian algebra; fat tails change the constants, not the direction.)
- **A bar-level mean reversion is a property of the bar size.** An autocorrelation of −0.2 on 1m bars mostly washes out on 5m bars. "Mean-reverting on 1m" and "mean-reverting on 5m" are different questions (QR20 in `mis-field.md` §3, CHECKED), even though the unit on both is one idea.
- **No sensor sees both trend and mean reversion.** Efficiency ratio fires on trend and almost never on mean reversion; variance ratio and autocorrelation the reverse. A three-word reading (trending, reverting, neither) needs both kinds.
- **Bounce turns noise into fake mean reversion.** This is the trap behind intraday "anti-persistence" on traded prices (E14). Trend sensors become quieter under bounce, not noisier.

## 3. Which states help per trade, and which only as a session or day list

| Reading | Data it needs | Lag at 1m (one false alarm per 10 days) | Lag at 5m | Per trade or per session? | Evidence |
| --- | --- | --- | --- | --- | --- |
| Spread and cost against usual | quotes | the smoothing window (seconds) | same | per trade | research 05 T1; SQS (research 18 §4) |
| Tick rate and depth against usual | quote ticks; book | seconds to a few minutes | same | per trade | research 05 T1; E25 |
| Volatility against usual | closes, ranges, ticks | 8 to 30 minutes | 40 minutes to 2.5 hours | per trade from ranges or ticks; per session from 5m closes | S1, S3, E27, E28 |
| Session, fixes, releases, funding times | calendar | zero | zero | per trade | E10, E32, E33 |
| Book pressure (imbalance, OFI) | book | ticks | ticks | per trade, seconds horizon only | E04, E06, E46 |
| Trending or not | closes | about 4 h strong, a day weak | same in hours | session or day list | S1 |
| Mean-reverting or not | closes (mid or one-sided) | about 4-5 h strong, about a day weak | the 1m state may not exist on 5m | session or day list | S1 |
| Regime label (HMM, jump model, mixture) | any | hours to weeks | hours to weeks | day list | E19, research 05 T3 |
| Known-state returns (move since the open, rest of day) | closes | none: a measured return, not an inferred state | none | per trade or per window | E10, E11 |

## 4. Does a label known at entry lift results compared with the label known afterwards?

**S2 (CHECKED command `mis_label_timing.py`).** Simulated 1m bars switch between a random walk and strong mean reversion (autocorrelation −0.2), each spell of random length. A fade-the-last-bar scalper pays 0.05 sigma per trade. Gates: none; oracle (the true state, impossible live); centred (the autocorrelation over a 240-bar window centred on the bar, the usual hindsight mistake when a day is labelled after the fact); at entry (the same window ending at the bar).

| Mean spell | Gate | Trades | Mean result per trade (sigma) | Total |
| --- | --- | --- | --- | --- |
| 120 bars (2 h) | none | 999,999 | +0.030 | +30,050 |
| | oracle | 494,605 | +0.110 | +54,494 |
| | centred (hindsight) | 587,392 | +0.083 | +48,838 |
| | at entry | 587,391 | +0.047 | +27,671 |
| 720 bars (12 h) | none | 1,999,999 | +0.030 | +60,477 |
| | oracle | 1,003,040 | +0.110 | +110,436 |
| | centred | 1,103,153 | +0.101 | +111,837 |
| | at entry | 1,103,152 | +0.076 | +84,188 |
| 2,880 bars (2 days) | none | 999,999 | +0.032 | +31,883 |
| | oracle | 505,872 | +0.111 | +56,226 |
| | centred | 547,557 | +0.107 | +58,292 |
| | at entry | 547,556 | +0.091 | +49,574 |

(The 720-bar run used 2 million bars, the others 1 million.)

**What it says (INFERRED):**

- **The ratio of state length to sensor window decides everything.** At a ratio of 0.5 the at-entry gate earns nothing in total; at 3 it keeps about 70% of the oracle's per-trade edge; at 12 about 81%.
- **A hindsight label overstates the gate's value per trade by 18% to 76%.** A backtest that labels days after the fact will promise more than live can deliver. This is why research 43's stamped-reading foundation (F2, `research/43-convergence.md:51-55`, CHECKED) matters for scalpers most.
- **The real-data version** runs in QMB once trades carry the reading at entry: replay one unit, gate it once with readings stamped at entry and once with the same readings recomputed over a centred window, and report both. The gap is the hindsight premium for that unit, market and reading. It is one judge step, not a battery.

## 5. Fast proxies, order flow, and spot FX

**Which fast proxies beat the slow reading (Q22):**

| Proxy | Beats the slow direction reading? | Evidence |
| --- | --- | --- |
| Calendar and almanac (habits by instrument, hour, weekday) | yes, zero lag, for anything that repeats | E13 (same-time-of-day continuation for 40 days), E32, E33, research 05 |
| Ranges and ticks for volatility | yes, about 3× faster than closes | S3, E27, E28 |
| Known-state returns (move since the open, rest of day) | yes for intraday windows; documented in 60+ futures | E10, E11 |
| Higher timeframe | not faster, but already known when the scalper's session starts | his `higher-timeframe-reference` entry (research 19 §6, CHECKED) |
| Cross-section of many markets | partly: lagged cross-asset order flow helps for minutes (E05); COMEX leads gold spot (E32); currency strength untested | E05, E32 |
| Tick, volume or trade-count bars | improves the statistics (removes seasonality, closer to normal), lag untested | E25, E26; empty cell |
| Order flow where it exists | yes for seconds-scale pressure, not for a regime | E06, E09, E46 |
| The unit's own recent fills | untested in the literature | none found |

**Does order flow show mean reversion sooner where a venue has it? (L03-04)** Partly. Book imbalance and trade flow predict the next seconds and fade by 30 to 60 seconds (E06, E46). Short-term reversals in stocks are driven by temporary liquidity imbalances that last under an hour (E13), and a live Binance experiment found profitable maker logic has to trade against the book imbalance (E09). So order flow can label a move as liquidity pressure, which tends to revert, at the moment it happens. Nobody has tested an order-flow "mean-reverting market" state against a price-only one. That is an empty cell and a cheap QMB study once a tape or book is recorded.

**What stands in for order flow on spot FX (L03-05):**

| Stand-in | What it measures | Evidence | Caveat |
| --- | --- | --- | --- |
| Tick volume (quote count) | activity | hourly r 0.96-0.99 with ECN traded volume, 4 majors (E30) | vendor study; finer horizons untested; monthly ties unstable (E30, FMG) |
| Quote spread and tick rate against usual | liquidity | research 05 T1; SQS | none |
| cTrader depth book (broker L2) | resting interest at one broker | none for retail books | empty cell; one broker's book is not the market |
| Tick-rule imbalance (up-ticks minus down-ticks) | signed pressure proxy | none found for FX | INFERRED fallback (`mis-field.md` B005) |
| CME FX futures tape (6E and similar) | signed trades on a small venue | futures are a small share of FX (varianse page, PRACTITIONER, CHECKED https://varianse.com/en/forex-education/broker-knowledge/trading-volume-requires-the-right-broker/) | a second feed, a borrowed rung (`mis-field.md` P4-b) |
| Spread from OHLC (Abdi-Ranaldo, Corwin-Schultz) | cost where only bars exist | E29 | daily stock evidence; intraday use on crypto by Brauneis (E33) |

## 6. Indicators versus models, and the persistence family

**Should a scalper's sensors be plain indicators and slower styles use models? (L03-07)**

| Kind | Example | Fits a 1m/5m scalper per trade? | Why |
| --- | --- | --- | --- |
| Ratio indicators | spread ratio, tick-rate ratio, range ratio | yes | lag is the smoothing window (S1, S3) |
| Small online models | CUSUM, Shiryaev-Roberts, Kalman level, two-scale volatility | yes | cheap, near the bound, one state each (E01, E28, E36) |
| Persistence readings | efficiency ratio, variance ratio, autocorrelation, Hurst, entropy | session or day list | windows of hours; bounce-sensitive (S1, E37) |
| Regime models | HMM, jump model, Gaussian mixture, MS-GARCH | day list, or the session list when trained on intraday features | false switches, long windows, refits relabel the past (E19, E23, research 05 §1.5) |

So his line "not an HMM inside a scalper's MIS, but multiple indicators" survives with one change: small online models also belong in the fast tier, and HMMs belong in the scalper's day list, not nowhere. The rule that sorts them is the lag-to-hold ratio (`mis-field.md` B003, CHECKED) plus the spell-to-window ratio from S2.

**Are Hurst, variance ratio and efficiency ratio sensors or a family of their own? (L03-19)** Both: they are sensors, and together with autocorrelation and entropy they form one persistence family that shares three traits. They need long windows (Hurst at least about 1,000 points, E37). They are fooled by bid-ask bounce (S1). They split the work: efficiency ratio for trend, variance ratio and autocorrelation for mean reversion (S1). Entropy has one study showing it times the size of moves, not their direction (E39). The old "market physics" readings (research 19 §2) belong on the same shelf, tested the same way.

## 7. Impossible combinations (L03-22, L05-08)

| Reading | Impossible where | Why | Source |
| --- | --- | --- | --- |
| Trade delta, footprint, absorption, VPIN, volume profile on real volume | spot FX, metal CFDs, index CFDs, stock CFDs at cTrader | no time-and-sales tape | research 02 short answer 5 (CHECKED via `STATE.md:179`) |
| Volume or dollar bars | spot FX and CFDs | no consolidated volume; only tick bars (E26) | E26 |
| Funding, open interest, liquidations | everything except perps (OI also on exchange futures) | the field does not exist | research 02 table |
| Long 1m history on Hyperliquid | Hyperliquid | about 3.5 days of 1m candles; QMX must record its own | STATE research 02 row (CHECKED `STATE.md:179`) |
| A gold CFD reading the GC tape | without a second, paid futures feed | the tape lives at CME | E32; research 02 |
| Stock CFDs at IC through cTrader | cTrader | listed on MT5 only | research 02 short answer 2 |
| Depth on MT5 CFDs | broker-dependent | not every broker publishes it | research 02 table |
| Session readings on crypto | none by clock; replaced by hour-of-day and funding-hour periodicity | 24/7 | E33 |

## 8. Knot (a): which of the 14 options survive

The options are from `research/funnel3/cis/problem-solving.md:220-233` (CHECKED).

| # | Option | Verdict | Why |
| --- | --- | --- | --- |
| 1 | Two speeds: fast dimensions per bar, direction per session or day | survives | S1 and S2 back it; research 05 |
| 2 | Almanac first: habits by instrument × hour × weekday, refreshed weekly | survives, strongest zero-lag option | E13, E32, E33; research 05 seasonality |
| 3 | Cross-sectional state per cluster, every bar | open | evidence only for order-flow cross-impact (E05) and gold's lead market (E32); currency strength untested |
| 4 | Change detectors instead of state classifiers | survives for volatility and liquidity; slow for direction | S1: CUSUM on volatility in about 29 bars, drift in hours |
| 5 | The unit's own last trades as its live context sensor | open, risky | untested; it is also the unit's own record, which research 05 §2.5 warns mixes sizing into placement |
| 6 | Tick, volume or range bars for the MIS | survives for volatility (ranges 3× faster, S3); open for direction (no lag study) | E25, E26, S3 |
| 7 | Order-flow sensors only where a tape or book exists; FX uses tick activity | survives | E06, E09, E30; §5 |
| 8 | Higher-timeframe nesting known before the session | survives | known in advance; no lag at trade time |
| 9 | An agent's daily review of charts and data before each session | survives as a day-list producer, scored later | his seed (`T2:325`, CHECKED); research 43 forecasts scored by the market |
| 10 | Probabilistic labels with sample size | survives | regime models already output probabilities (E19, E44); the spell-to-window ratio can be published with it |
| 11 | Trade small to sense, grow inside the session | parked for the risk session | it changes size (STATE 30 Oct: sizing belongs to the risk session) |
| 12 | Borrow state from a faster correlated market | survives for gold (E32); INFERRED for index CFDs; adds a second feed | E32; `mis-field.md` P4-b |
| 13 | Drop direction from the MIS; it only gives terrain and fast state | survives as a pole; conflicts with his "find mean reverting markets" aim | his `T1:1903`; S2 shows direction lists still help when states are long |
| 14 | He and the copilot label markets by hand; train on those labels | survives as dated human labels; training only in shadow | his `T2:219`; hindsight risk (S2 centred row) |

## 9. Numbers named here (starting defaults, none settled)

| Number | Default | Reason |
| --- | --- | --- |
| False-alarm spacing per reading per market | one episode per 10 trading days | research 05; §2 |
| Lag-to-hold ratio for a per-trade reading | lag at most a third of the unit's median hold | `mis-field.md` B003 |
| State spell ÷ sensor window for a direction label to gate trades | at least 5 | S2: 0.5 useless, 3 good, 12 near oracle |
| Bounce ratio (noise sigma ÷ one-bar sigma) | flag above 0.1, block price-only mean-reversion readings above 0.25 | §2 bounce table |
| Volatility reading window | 10 bars of ranges; 30 bars of closes as fallback | S3 |
| Persistence window at 1m | 240 bars | S1; shorter windows miss weak states |
| Minimum points for a Hurst value | 1,000; flag below 4,000 | E37 |
| Order-flow reading horizon | 30 seconds | E06 |

## 10. Not verified

- All lags are from simulated Gaussian bars with fixed sigma and iid bounce. Real data adds fat tails, clustering and seasonality; deseasonalise first (E02) and expect longer lags.
- The sub-step tick model in S3 has no microstructure noise, so its tick result is an upper bound on speed.
- No real FX, gold, futures or crypto data was replayed. The first real check is the §4 replay in QMB, or the S1 script pointed at the Library's 1m partitions.
- Scripts (all run with the QMX venv Python, `-I`):
  - `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\ed09cf0c-69f1-44ab-8c6b-76992918774a\scratchpad\mis_sensor_lag.py` (S1; argument 1440 or 14400)
  - `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\ed09cf0c-69f1-44ab-8c6b-76992918774a\scratchpad\mis_label_timing.py` (S2)
  - `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\ed09cf0c-69f1-44ab-8c6b-76992918774a\scratchpad\mis_range_speed.py` (S3)
