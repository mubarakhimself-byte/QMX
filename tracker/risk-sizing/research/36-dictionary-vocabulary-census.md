---
title: Dictionary vocabulary census against the MQL5 library
date: 2026-10-30
author: opus research agent (poteto-mode, no sub-agents)
status: census for the lead; records, does not redesign the dictionary
---

# 36: Dictionary vocabulary census against 3,128 MQL5 articles

**Labels.** CHECKED means I read it at the cited place this session or a script I wrote printed it (script named). INFERRED means my reasoning. Article ids are MQL5 ids; the file is `md/<id>.md` in the library. `D` = `C:/Users/Mubarak/Desktop/Stats/dictionary/`. `LIB` = `C:/Users/Mubarak/Desktop/QMX/.worktrees/mql5-library/data/mql5-library/`. `S` = my scratch folder (section 9). Every number is a census count, not a setting; nothing here is a default for QMX.

## 0. What matters most (short)

1. **The dictionary covers the trader's chart well and the quant's toolbox not at all.** Price action, sessions, exits and filters are 70-88% covered when weighted by how many articles use each concept. Statistical tests and models score 0 of 40 concepts, and they appear in 31% of screened articles; learned models (neural nets, trees, RL, LLMs) appear in 39%. CHECKED (`census.py`, `unions.py`).
2. **Almost every strategy article uses at least one word the dictionary does not have.** Among 466 strategy-bearing articles (an entry concept plus a stop or target mention), 85% name at least one missing non-statistical concept; the median article has 75% of its trading concepts covered. CHECKED (`article_coverage.py`).
3. **The biggest single indicator gap is MetaTrader's own built-ins.** CCI, Parabolic SAR, Williams %R, Awesome/Accelerator, Alligator, DeMarker, MFI, OBV, A/D, RVI, Force, Bulls/Bears, TRIX: 15 concepts, all missing, 273 articles (13%). The indicators family folder is empty. CHECKED (`unions.py`; `ls D/indicators-and-transformations`).
4. **Exits: single-trade exits are covered, account-level and grid exits are not.** Stop, target, trailing, break-even, partial, time and session exits all have entries. Basket profit exits, equity kill switches, daily loss limits, grid take-profit on the weighted average price, confidence exits and close-by are missing (199 article-hits together). CHECKED (`concept_counts.csv`).
5. **Authors write fixed numbers and let the optimiser pick them.** Stop inputs are in points in 84 articles and in ATR multiples in 9. Self-tuning appears as eight distinct mechanisms (section 6), and the dictionary's 12 fields have no slot for any of them. CHECKED (`inputs_summary.py`, `assembly.py`); the "no slot" reading is INFERRED from the 12-field list in `D/README.md`.
6. **MetaTrader already has an assembly model: Signal + Trailing + Money, with weighted signals summed against open/close thresholds.** The strategy-DNA graph has `K_OF_N` but no weighted-sum-with-threshold operator. CHECKED (706, 3642: `Signal_ThresholdOpen=10 ... [0...100]`, `filter0.Weight(...)`; `C:/Users/Mubarak/Desktop/Stats/schema/strategy-dna.md` operator table).

## 1. Method and counts

### 1.1 Corpus and screen

| Step | Count | Source |
|---|---|---|
| Articles with text (`fetch_status='ok'`) | 3,128 | CHECKED `LIB/index.sqlite` |
| Title screen include (rules of research 06 §3.2, re-implemented) | 1,888 | CHECKED `screen.py` |
| Title screen exclude (X1 GUI 382, X3 tooling 246, X2 IO 179, X5 simulator 110, X6 metaheuristics 52, X4 business 22) | 991 | CHECKED `screen.py` |
| Unmatched titles | 249 | CHECKED `screen.py` |
| Unmatched kept because the prose names 5 or more distinct trading concepts | 150 | CHECKED `census.py` |
| **Screened set used for all counts** | **2,038** | CHECKED `census.py` |

Research 06 got 1,970 at title stage with hand adjudication of the unmatched; my automated version gets 2,038. The gap is the body-based rule for unmatched titles, which replaces the hand step. INFERRED. Full-text plumbing still sits inside the screened set (research 06 found 26% at full text; my sample found 18 of 66, 27%). CHECKED (section 5.1). Counts below therefore include some tutorial and plumbing articles.

### 1.2 Counting

- Dictionary: 239 entries in 4 family files, parsed from `## slug` headings that carry a `Definition` field, with aliases split on `;` and `,`. CHECKED (`dict_extract.py`; matches research 34 §3.1).
- Concept list: 252 MQL5 concepts in 11 census families, each a regex plus a status against the dictionary: **covered** (an entry whose slug, title or alias carries the MQL5 wording), **renamed** (an entry exists, the MQL5 wording is not among its names), **partial** (an entry covers part: broader, narrower, one variant, one role), **missing**. Statuses are my judgement; `alias_check.py` tests every "covered" claim against the entry's names, and the 8 that failed were moved to "renamed". CHECKED (`alias_check.py` now prints 0 failures).
- Counts are over prose only (code blocks, image links and URLs removed, text cut at "Attached files"). "Articles" = distinct screened articles with at least one hit; "mentions" = total hits. CHECKED (`census.py`).
- Discovery of terms the list missed: title n-grams not matched by any regex (`discovery_titles.py`), and a head-noun phrase scan (`discovery.csv`, noisy). The title scan added 5 concepts: multi-symbol trading, options/greeks, synthetic data, feature engineering, microstructure. CHECKED.
- Reading: a stratified sample of 66 articles (section 5), read from compact extracts, plus targeted reads (17781, 17737, 706, 3642). CHECKED.

### 1.3 Precision of the counts

I read 10 random matches (seed 7) per concept for the broadest regexes and tightened those that failed. CHECKED (`precision.py`).

| Concept | Before | After tightening | Notes |
|---|---|---|---|
| price gap | 1/10 ("bridge the gap") | about 8/10, 67 articles | was 419 |
| grid entry | 2/10 (GUI grids, hyperparameter grids) | 10/10, 41 articles | was 199 |
| hedging | 3/10 (hedging account mode) | about 7/10, 33 articles | was 180 |
| basket exit | 3/10 (currency baskets, "total profit" in reports) | about 7/10, 14 articles | was 212 |
| liquidity sweep | 5/10 (parameter sweeps) | 10/10, 47 articles | was 99 |
| range/consolidation | "arranging" matched "ranging" | fixed, 369 articles | was 454 |
| custom indicator (iCustom) | about 5/10 strategy-relevant | kept | half are "how to code an indicator" |
| forecast-direction entry | about 4/10 | kept, flagged | calendar "forecast" values add noise |
| fundamental/macro | about 6/10 | kept | "inflation" in other senses |
| signal voting/ensemble | about 6/10 | kept | ML ensembles dominate |
| regression, doji, multi-symbol, z-score, server time, trailing, seasonality | 8-10/10 | kept | |

Two counts are inflated by long series: "Neural networks made easy / in trading" is 182 screened articles, "MQL5 Wizard Techniques" 99. CHECKED (title count in `articles.json`). Counts are per article, not per work.

## 2. Coverage per family

### 2.1 Summary

"Concept %" = covered + renamed concepts over all concepts in the family. "Article-weighted %" = the same, weighting each concept by its article count. CHECKED (`census.py` → `family_summary.txt`).

| Census family | Concepts | Covered | Renamed | Partial | Missing | Concept % | Article-weighted % (cov+ren / partial / missing) |
|---|---|---|---|---|---|---|---|
| Indicators | 46 | 17 | 1 | 5 | 23 | 39% | 70 / 6 / 25 |
| Statistical tests and models | 40 | 0 | 0 | 1 | 39 | 0% | 0 / 7 / 93 |
| Price action and structure | 46 | 31 | 1 | 7 | 7 | 70% | 74 / 12 / 14 |
| Order flow and volume | 13 | 9 | 0 | 3 | 1 | 69% | 60 / 39 / 0 |
| Context and regime | 16 | 9 | 0 | 2 | 5 | 56% | 56 / 20 / 23 |
| Session and calendar | 11 | 6 | 2 | 1 | 2 | 73% | 86 / 2 / 13 |
| Entry types | 21 | 9 | 2 | 2 | 8 | 52% | 61 / 12 / 28 |
| Exit types | 23 | 11 | 1 | 5 | 6 | 52% | 88 / 5 / 7 |
| Trade management | 9 | 1 | 1 | 2 | 5 | 22% | 26 / 32 / 41 |
| Money management and sizing | 17 | 3 | 1 | 2 | 11 | 24% | 43 / 4 / 53 |
| Filters and confirmations | 10 | 4 | 3 | 1 | 2 | 70% | 81 / 8 / 11 |
| **All** | **252** | **100** | **12** | **31** | **109** | **44%** | |

Per article: across all 2,015 screened articles with any hit, the median article has 50% of its distinct concepts covered (70% if statistical concepts are set aside). Across 466 strategy-bearing articles (one of 14 entry concepts plus a generic stop-loss or take-profit mention), the median is 68% (75% without statistics), and 85% of them have at least one missing non-statistical concept. CHECKED (`article_coverage.py`).

### 2.2 Per family (non-covered concepts in full; covered concepts as one line)

Format: concept: articles (example ids). Dictionary slugs in backticks. All counts CHECKED (`concept_counts.csv`).

**Indicators.** Covered: moving average 644, RSI 341, ATR 311, stochastic 290, MACD 181, Bollinger 158, MA crossover 119, Fibonacci 95, envelopes 67, fractals 52, momentum 41, ROC 41, pivot points 36, Ichimoku 22, Donchian 19, currency strength 18, Keltner 6.

| Concept | Status | Articles | Examples | Note |
|---|---|---|---|---|
| custom indicator / iCustom | missing | 214 | 14481, 12510, 691 | no way to point at a user's own indicator; about half the hits are coding how-tos |
| ADX / DMI | renamed → `trend-strength` | 105 | 10715, 17910, 22754 | ADX only as alias "ADX level" |
| Parabolic SAR | missing | 81 | 10920, 18399, 14782 | also used as a trailing source |
| CCI | missing | 79 | 10592, 17910, 18551 | |
| ZigZag | partial → `swing-high`, `swing-low` | 73 | 2774, 1468, 1470 | depth/deviation/backstep and repaint not named |
| z-score | missing | 72 | 24652, 17800, 23676 | |
| adaptive MAs (AMA, KAMA, VIDYA, FrAMA, DEMA, TEMA, T3) | partial → `moving-average` | 61 | 3791, 11341, 18144 | only HMA is an alias |
| Renko, Kagi, range, tick, volume bars | missing | 58 | 20239, 8226, 22875 | bar construction, not an indicator |
| Williams %R | missing | 49 | 11142, 18251, 3339 | |
| Awesome Oscillator | missing | 41 | 16657, 11468, 16365 | |
| Heikin-Ashi | missing | 41 | 19260, 12510, 12845 | |
| linear regression channel/slope | missing | 34 | 23130, 20347, 3642 | |
| A/D, Chaikin | missing | 30 | 11242, 1357, 14775 | |
| Alligator, Gator | missing | 29 | 11928, 18992, 18946 | |
| OsMA / MACD histogram | partial → `macd` | 28 | 5703, 2817, 18462 | |
| standard deviation indicator | partial → `realized-volatility` | 28 | 11185, 23676, 2118 | |
| Money Flow Index | missing | 21 | 11037, 12172, 17065 | |
| Accelerator Oscillator | missing | 19 | 11467, 16365, 13277 | |
| DeMarker | missing | 18 | 11394, 17987, 18033 | |
| OBV | missing | 17 | 10961, 18462, 13277 | |
| RVI | missing | 17 | 11425, 18399, 18433 | |
| Ehlers, Fisher, Laguerre, Hilbert filters | missing | 17 | 23444, 23149, 8807 | |
| Bulls/Bears Power | missing | 14 | 5014, 13244, 11327 | |
| Force Index | missing | 13 | 11269, 18144, 18188 | |
| Aroon, Vortex, Choppiness, Efficiency Ratio | partial → `market-regime` | 12 | 14006, 1103, 15160 | choppiness only as regime alias |
| other oscillators (Ultimate, CMO, DPO, Schaff, TSI) | missing | 12 | 19547, 11341, 3791 | |
| Market Facilitation Index | missing | 10 | 12172, 13277, 3968 | |
| TRIX | missing | 7 | 18251, 19794, 18305 | |
| Supertrend | missing | 6 | 20755, 23161, 20908 | |

**Statistical tests and models.** No dictionary entry; the only partial is correlation (`currency-pair-correlation`, FX pairs only), 394 articles (19343, 5481, 20945).

| Concept | Articles | Examples |
|---|---|---|
| neural network (generic) | 566 | 1103, 11275, 16845 |
| performance ratios (Sharpe, Sortino, Calmar, profit factor) | 443 | 9171, 24150, 3642 |
| hypothesis tests (t, KS, chi-square, Wilcoxon, p-values) | 322 | 23742, 2742, 14199 |
| walk-forward / out-of-sample | 282 | 3279, 20485, 3642 |
| overfitting controls (CSCV, PBO, deflated Sharpe) | 271 | 21603, 13743, 24238 |
| distribution shape (skew, kurtosis, tails) | 259 | 2742, 20167, 24150 |
| expectancy / win rate | 228 | 19211, 18587, 18991 |
| regression (linear, logistic, ridge, lasso, OLS) | 201 | 11735, 23130, 2358 |
| CNN | 187 | 8234, 15259, 18138 |
| clustering (k-means, SOM, DBSCAN) | 175 | 14548, 14489, 11615 |
| transformer / attention | 173 | 14766, 13348, 18885 |
| ONNX model | 173 | 14330, 13394, 13506 |
| ADF / KPSS / stationarity | 169 | 14199, 24468, 19052 |
| genetic / metaheuristic optimisation | 163 | 2225, 18847, 1409 |
| synthetic data / simulated paths | 147 | 16214, 5373, 3973 |
| LSTM / RNN / GRU | 142 | 15182, 15114, 11245 |
| tree ensembles | 139 | 14926, 13765, 16017 |
| feature engineering | 129 | 15482, 16285, 12739 |
| cross-validation | 127 | 21603, 17446, 20117 |
| Monte Carlo / bootstrap / permutation | 123 | 20059, 22912, 23125 |
| reinforcement learning | 123 | 16008, 19794, 11452 |
| entropy / mutual information / IC | 118 | 21743, 15393, 23286 |
| Fourier / wavelet / spectral | 92 | 14858, 23426, 14913 |
| autocorrelation / variance ratio | 83 | 14203, 3299, 23488 |
| SVM / kNN / naive Bayes | 79 | 13395, 14681, 7603 |
| Bayesian | 71 | 12184, 22775, 20163 |
| ARIMA / autoregression | 68 | 18247, 12583, 22224 |
| PCA / SVD | 66 | 3526, 12229, 13968 |
| LLM / AI agent | 66 | 13506, 15595, 19782 |
| autoencoder / GAN / VAE | 51 | 11172, 14760, 11206 |
| hidden Markov / Markov | 49 | 11930, 17917, 15033 |
| cointegration / pairs | 44 | 19626, 19052, 18702 |
| labelling (triple barrier, trend scanning, meta-labels) | 39 | 19253, 18864, 19850 |
| Hurst / fractal dimension | 35 | 2930, 6834, 15222 |
| GARCH | 29 | 23677, 22258, 22438 |
| MFE / MAE | 23 | 22855, 24466, 23245 |
| Kalman filter | 14 | 23016, 17273, 18766 |
| Ornstein-Uhlenbeck / half-life | 8 | 20173, 14203, 22275 |
| copula | 5 | 19931, 19930, 18361 |

Grouped: a learned model used as a signal source appears in 796 articles (39%); a statistical or econometric model or test used as signal or context in 632 (31%); evaluation vocabulary (ratios, tests, walk-forward, overfitting, Monte Carlo, expectancy, MFE/MAE, distribution shape) in 1,066 (52%). CHECKED (`unions.py`).

**Price action and structure.** Covered: range/consolidation 369, breakout 314, support/resistance 233, pullback/retracement 169, trendline 164, swing high/low 112, higher high/lower low 95, divergence 89, false breakout 80, pin bar 68, price gap 67, N-bar high/low 65, opening range 64, engulfing 62, supply/demand 54, liquidity sweep 47, retest 38, double top/bottom 36, order block 28, inside/outside bar 28, BOS/CHoCH 23, head and shoulders 22, round numbers 20, triangle/wedge 19, previous day high/low 19, fair value gap 12, morning/evening star 11, flag/pennant 10, premium/discount 8, Wyckoff 4, three soldiers 4.

| Concept | Status | Articles | Examples | Note |
|---|---|---|---|---|
| trend-following (strategy style) | missing | 163 | 5427, 16633, 15509 | the dictionary has primitives, no style layer |
| mean reversion (strategy style) | missing | 152 | 20173, 14203, 20220 | same |
| candlestick patterns (generic catalogue) | partial | 87 | 17832, 17525, 20223 | about ten named shapes exist |
| harmonic patterns (Gartley, Butterfly, Bat, Crab) | partial → `measured-move` | 72 | 2990, 19442, 19111 | only AB=CD named |
| bar counting / N in a row | partial → `three-bar-directional-completion` | 68 | 15899, 15040, 17987 | |
| price channel (equidistant, regression) | partial → `donchian-channel`, `trendline` | 50 | 21443, 4267, 1862 | |
| candle body/wick ratio | partial → `wick-rejection-bar` | 50 | 22341, 17832, 22927 | 5751 parameterises Long 1.3, Doji 0.04, Marubozu 0.01 |
| doji | missing | 49 | 9801, 12355, 17832 | |
| smart money / ICT as a method label | partial | 40 | 20414, 22526, 16340 | parts exist |
| Wolfe, pitchfork, Gann, Murrey | missing | 33 | 1470, 15556, 15566 | |
| marubozu, spinning top, tweezer, piercing, dark cloud | missing | 22 | 12385, 18207, 17525 | |
| Elliott wave | missing | 18 | 16494, 12140, 1564 | |
| harami | renamed → `inside-bar` | 7 | 5576, 17525, 18789 | |
| megaphone / broadening | missing | 5 | 22572, 14113, 18548 | |
| Darvas box | partial → `structural-range` | 3 | 24111, 17466, 24279 | |

**Order flow and volume.** Covered: tick volume 94, DOM/order book 60, real volume 58, VWAP 48, footprint 48, volume spike 40, volume profile/POC 23, delta/CVD 9, book imbalance 5. Partial: tick data / time and sales 133 (`data-health-feed`, as a data source only; 22063, 23077, 23169), order flow generic 59, microstructure generic 59 (22938, 22638, 22263). Missing: volume spread analysis 2 (16062, 3266). INFERRED: this family is covered because the dictionary was written from order-flow sources; MQL5 authors use it little (spot FX has only tick volume).

**Context and regime.** Covered: trend direction 380, market regime 345, higher/multi timeframe 221, trend strength 143, intermarket 63, risk-on/off 41, implied vol 12, dollar index 10, distance to level 8.

| Concept | Status | Articles | Examples | Note |
|---|---|---|---|---|
| volatility regime | partial → `market-regime`, `realized-volatility` | 241 | 16830, 16914, 22220 | no volatility-state entry |
| multi-symbol / multi-currency trading | partial → `currency-strength` | 201 | 19008, 14329, 14051 | the DNA binds one pair per binding |
| fundamental / macro (rates, CPI, PPP, GDP) | missing | 188 | 20949, 18451, 20995 | precision about 6/10 |
| sentiment / positioning (COT, open interest) | missing | 105 | 1573, 23410, 2773 | |
| seasonality | missing | 85 | 12996, 17361, 15622 | often time-series seasonality, not calendar |
| options / greeks | missing | 83 | 23410, 20287, 20054 | 18363 emulates options with spot positions |
| market fingerprint / state vector | missing | 47 | 19460, 23673, 3886 | |

**Session and calendar.** Covered: trading session 166, economic calendar/news 160, time-of-day 128, day of week 75, swap/rollover 52, session overlap 6. Renamed: new-bar event 473 → `close-confirmed-entry`; Asian/session range 12 → `session-range`. Partial: weekend gap / Friday close 20. Missing: broker server time / GMT offset / DST 115 (16171, 19496, 14912), holidays / month end 51 (18549, 22516, 17986). INFERRED: the server-time gap matters because every MQL5 session rule is written in broker time.

**Entry types.** Covered: threshold/overbought-oversold 192, re-entry/cooldown 136, buy/sell stop 131, buy/sell limit 114, pending expiry 69, stop-and-reverse 47, stop-limit 35, pyramiding 22, averaging/DCA 18. Renamed: crossover entry 193 → `series-crossover`, market order 148 → `market-entry-order`.

| Concept | Status | Articles | Examples |
|---|---|---|---|
| forecast-direction entry (trade the model's predicted direction) | missing | 133 | 3172, 15024, 15171 |
| signal voting / ensemble | partial → `confluence-count` | 130 | 4227, 4722, 16838 |
| scalping (style) | missing | 115 | 19989, 1284, 1509 |
| one trade per bar / max open positions | partial → `one-shot-signal` | 92 | 8616, 17001, 20569 |
| confidence / probability threshold entry | missing | 76 | 17466, 18324, 21938 |
| arbitrage (triangular, synthetic, statistical) | missing | 70 | 19462, 15964, 17422 |
| grid of orders | missing | 41 | 21833, 10672, 13906 |
| hedging / locking | missing | 33 | 4830, 13845, 1479 |
| random entry (as a test baseline) | missing | 20 | 24273, 1360, 24146 |
| news straddle | missing | 16 | 18951, 19704, 16169 |

**Exit types.** See section 4.

**Trade management.** Covered: order retry/requote 61. Renamed: max spread/slippage guard 39. Partial: netting vs hedging account 92 (`otc-fx-execution-context`), trade state machine 30. Missing: martingale 56 (5269, 1446, 8390), stops level / freeze level 40 (23327, 7286, 19911), grid management 37 (21833, 10671, 10672), recovery (zone/loss) 12 (16705, 17001, 15067), anti-martingale 11 (5008, 8793, 4368).

**Money management and sizing.** Covered: percent risk 122, fixed lot 111, fixed cash risk 18. Renamed: stop-distance sizing 76. Partial: volatility-scaled 32, balance-proportional lot 2.

| Concept | Articles | Examples |
|---|---|---|
| margin / leverage / free margin | 114 | 22391, 16820, 19508 |
| lot step / min-max lot | 79 | 14912, 23716, 23327 |
| portfolio allocation / risk parity | 71 | 20657, 16604, 20485 |
| Kelly / optimal f | 33 | 21915, 24147, 4162 |
| prop-firm rules | 30 | 19655, 11850, 17249 |
| drawdown-based size reduction | 23 | 12026, 1349, 14273 |
| confidence-scaled sizing | 22 | 22754, 16445, 18864 |
| correlation exposure limit | 15 | 21720, 21460, 17742 |
| fixed ratio (Ryan Jones) | 9 | 3280, 23245, 734 |
| risk of ruin | 9 | 14365, 1367, 18587 |
| equity-curve trading | 3 | 21142, 22391, 23200 (not verified; a wider grep found none) |

**Filters and confirmations.** Covered: confluence/confirmation 410, trend filter 74, signal score 67, news filter 17. Renamed: volume filter 44, spread filter 21, ADX filter 21. Partial: volatility filter 69. Missing: consecutive-loss pause 59 (about half are tester statistics, not rules; 18991, 1383, 19439), edge-decay / drift monitor 33 (23043, 20946, 18864).

## 3. Top missing concepts ranked by articles

### 3.1 All families

| Rank | Concept | Articles | % of 2,038 |
|---|---|---|---|
| 1 | neural network | 566 | 27.8 |
| 2 | performance ratios (Sharpe, Sortino, Calmar, PF) | 443 | 21.7 |
| 3 | hypothesis tests | 322 | 15.8 |
| 4 | walk-forward / out-of-sample | 282 | 13.8 |
| 5 | overfitting controls | 271 | 13.3 |
| 6 | distribution shape | 259 | 12.7 |
| 7 | expectancy / win rate | 228 | 11.2 |
| 8 | custom indicator (iCustom) | 214 | 10.5 |
| 9 | regression | 201 | 9.9 |
| 10 | fundamental / macro | 188 | 9.2 |
| 11 | CNN | 187 | 9.2 |
| 12 | clustering | 175 | 8.6 |
| 13 | transformer / attention | 173 | 8.5 |
| 14 | ONNX model | 173 | 8.5 |
| 15 | ADF / stationarity | 169 | 8.3 |
| 16 | trend-following style | 163 | 8.0 |
| 17 | genetic / metaheuristic optimisation | 163 | 8.0 |
| 18 | mean-reversion style | 152 | 7.5 |
| 19 | synthetic data | 147 | 7.2 |
| 20 | LSTM / RNN | 142 | 7.0 |

CHECKED (`concept_counts.csv`). Six of the top ten are evaluation words, which the dictionary was never meant to hold: it stores strategy primitives (`D/README.md`). INFERRED.

### 3.2 Strategy-building concepts only (evaluation, optimisers, ONNX, feature engineering and synthetic data set aside)

neural network as signal source 566; custom indicator 214; regression 201; fundamental/macro 188; CNN 187; clustering 175; transformer 173; ADF/stationarity 169; trend-following style 163; mean-reversion style 152; LSTM 142; tree ensembles 139; forecast-direction entry 133; reinforcement learning 123; entropy/IC 118; broker server time 115; scalping style 115; margin/leverage 114; sentiment 105; volatility regime (partial) 241 and multi-symbol (partial) 201. CHECKED (`concept_counts.csv`).

Grouped gaps that read better as one concept: learned model as signal source 796; MT5 built-in indicators 273; averaging/grid/martingale/hedging family 172; non-time bars and Heikin-Ashi 98; account-level exits 55. CHECKED (`unions.py`).

## 4. Exits

### 4.1 What the dictionary has

57 entries in `invalidation-exits-and-management/`, of which 17 are exit events and management (fixed, structural, volatility, time, signal, session exits; trailing; break-even; partial; ladder; target-to-trail; cost-aware target). None of their Parameters lines holds a number. CHECKED (`grep -c` on Parameters lines with digits: 0; matches research 34 §3.4). Example: `trailing-protective-threshold` names "anchor, distance/estimator, update frequency, ratchet rule, trigger basis ... all values `source-stated` or `unresolved`". CHECKED (`exits-execution-management.md:238-247`).

### 4.2 How MQL5 authors exit

| Exit | Status | Articles | Examples |
|---|---|---|---|
| stop loss (any) | covered | 762 | 16169, 22691, 3621 |
| take profit (any) | covered | 676 | 16169, 12202, 3621 |
| R-multiple / RR target | covered | 272 | 22855, 23620, 23970 |
| trailing stop | covered | 271 | 2411, 14862, 21497 |
| break-even | covered | 113 | 18111, 17957, 23755 |
| opposite-signal exit | renamed → `signal-exit` | 88 | 3261, 14329, 22950 |
| fixed points SL/TP | covered | 80 | 2195, 23429, 3973 |
| ATR stop | covered | 73 | 23429, 23618, 10748 |
| partial close | covered | 71 | 19682, 19911, 24466 |
| indicator trailing (SAR, MA, chandelier) | partial | 69 | 14782, 14862, 2411 |
| model / confidence exit | missing | 55 | 21938, 12941, 13737 |
| grid TP on weighted average price | missing | 50 | 13906, 21390, 16984 |
| session / end-of-day exit | covered | 49 | 11452, 23226, 11392 |
| step / profit-lock trailing | partial | 44 | 20378, 17546, 14782 |
| time exit / max holding | covered | 39 | 22372, 24106, 1492 |
| equity / drawdown close-all (kill switch) | missing | 32 | 23732, 23315, 21833 |
| daily loss limit | missing | 30 | 21720, 17249, 23732 |
| structural / swing stop | covered | 28 | 1435, 18462, 20262 |
| stats-derived SL/TP (MFE, quantile) | partial | 24 | 13737, 14167, 22275 |
| close-by (opposite position) | missing | 18 | 3620, 1378, 7014 |
| basket / total-profit exit | missing | 14 | 6954, 24331, 21833 |
| hidden / virtual stop | partial → `intrabar-protective-exit` | 13 | 22614, 3620, 3621 |
| money or percent SL/TP | partial | 3 | 2281, 5268, 5111 |

All CHECKED (`concept_counts.csv`).

### 4.3 What the exit census shows

- **Shares among 552 strategy-bearing articles** (one of 18 entry concepts and any stop or target concept in the prose; a wider net than the 466 of section 2.1): stop 86%, target 86%, trailing or break-even 35%, opposite-signal or model exit 13%, time or session exit 9%, aggregate exit 9%, partial 5%. CHECKED (`assembly.py` part B). These are mention shares, not proof each article uses the exit.
- **Stops are written in points.** Stop inputs: points or pips 128 inputs in 84 articles; ATR or ratio 11 in 9; percent 1 in 1. Take-profit: points 88 in 61; ATR or ratio 8 in 8; percent 5 in 3; money 2 in 2. Trailing: points 30 in 16. CHECKED (`inputs_summary.py`; only 664 articles have parseable `input` lines).
- **Exits seen in reading that the dictionary has no word for**: exit when price returns to the EMA of a synthetic spread (17512); exit at the next bar open in a random-direction test (18086); exit at an emulated option expiry hour (18363, `ExpirationTimeHours = 24`); "SL/TP are checked before the agent action ... a position is closed after MAX_POSITION_BARS" (21314); exit only by the trailing stop (1995: "Making an exit will be performed solely with a Stop Loss"); all pyramid legs share one TP (1515). CHECKED (ids). From research 06 (CHECKED by that agent): stop and target chosen to maximise TP x P(reach) from the excursion history (13737), cycle-age exit for grids (21833), exit when model confidence crosses 40/60 (19047), hidden local stop on the terminal (22691).
- **Exits by aggregate P/L sit with risk, not with the trade.** Basket stops in account currency (23662: `InpUsdLongStop = -200.00 // USD_LONG basket stop`), "close all open positions if the overall profit reaches a specified sum in $" (6954), daily and overall loss limits (15085, 24249). CHECKED. The dictionary's exits are per position, and the risk-and-sizing folder is empty. CHECKED (`ls D/`).
- **Many strategy articles state no exit at all.** In my sample, 10 of 36 articles with an entry rule showed no stop and no exit in the extract (section 5.2). INFERRED that the DNA's `entry_hypothesis` class will be common for MQL5 sources; the extract may miss exits that live only in code.

## 5. How strategies are assembled (sample)

### 5.1 Sample

66 articles, seed 20261030, strata of research 06 (section group x year band), allocation Examples 16, Trading systems 16, Trading 12, Tester 6, Indicators 6, Other 8 plus year floors, one per series, research 06's 50 pilot ids excluded. Spread: 2026 19, 2025 13, 2024 9, 2023 5, 2020-22 6, 2013-19 9, 2005-12 5. CHECKED (`sample.py`). Read from compact extracts (strategy inputs without colour/panel lines, plus sentences with entry, exit, sizing, filter and tuning words), not full text. CHECKED (`brief_extract.py`).

What the 66 are: 18 not strategies (plumbing, tutorials, ML or maths walk-throughs: 1453, 1390, 772, 13920, 17742, 24562, 16163, 23449, 12475, 16296, 15319, 15332, 15042, 23660, 19683, 3046, 8136, 17469); 10 tuning, testing or risk tools (1052, 9305, 1467, 7718, 22291, 20540, 18991, 24147, 16952, 23662); 2 context-only indicators (19422, 18661); 36 with an entry rule. CHECKED (ids).

### 5.2 The 36 entry-bearing articles

"?" = not visible in my extract. "Tuned" = how the author sets the numbers.

| id (year) | Entry | Context / filter | Order | Stop | Exit / target | Management | Sizing | Tuned |
|---|---|---|---|---|---|---|---|---|
| 2626 (2016) | MACD cross beyond open level | MA trend 26 | market | none | TP 50 pips | trail 30 | lot 0.1 | optimiser; P/L by entry hour/day/month first |
| 8699 (2021) | candle body crosses MA | ? | market | ? | ? | ? | ? | by hand in a spreadsheet |
| 15336 (2024) | Bollinger zone change plus forecast | model gate | market | input `stop_loss_values = 1` | ? | ? | ? | "no optimization techniques were employed" |
| 19371 (2025) | close beyond MA-high/MA-low channel | ML trend forecast on two horizons must agree | market | width from indicator | ? | trailing | min lot | with/without model compared |
| 21581 (2026) | LTF structure into HTF liquidity zone | H1 zones, discount/premium | arrows | ? | ? | ? | ? | lookback 1000, ratio 3.0 fixed |
| 18363 (2026) | emulated option construction | hours window | market legs | none | expiry 24 h | delta rebalance | min-lots multiplier | fixed |
| 1345 (2012) | forecast vs price | HP filter | market | 100 pips | 100 pips | ? | 1 lot | fixed |
| 3886 (2017) | Kalman direction | ? | ? | ? | ? | ? | ? | ? |
| 12202 (2023) | NN on price template | ? | market | points | points, TP:SL 1:1 and 2:1 tried | ? | ? | optimiser + forward test |
| 10459 (2022) | linear regression forecast | MA 50, RSI 13 features | ? | ? | ? | ? | ? | ? |
| 13954 (2024) | RL actor policy | ? | agent | none ("did not focus on the risk management model") | agent | ? | ? | trained policy |
| 16573 (2024) | breakout | volume above MA x 1.5 | market | 2 ATR | 3 ATR | single position, new bar | ? | defaults suggested |
| 15222 (2024) | Hurst exponent with two MAs | Wizard signal class | Wizard | Wizard module | Wizard | Wizard | Wizard | optimiser |
| 16894 (2025) | pattern rules plus LSTM confidence | ? | ? | ? | ? | ? | from confidence | forecast horizon param |
| 18873 (2025) | price vs SVD-model expected value (fade) | ? | ? | ? | ? | ? | ? | refit each run ("self optimizing") |
| 23341 (2026) | breakout of order-block base candle | closed bars only | ? | ? | fixed TP | ? | lot 0.10 | fixed |
| 18086 (2026) | random direction each bar | none | market | from another article | next bar | ? | ? | optimiser on hold time, SL, TP |
| 17654 (2026) | ML class 1 (buy only) | meta-label trade ban | market | SL | TP or model signal, first wins | ? | ? | labelled and trained |
| 21314 (2026) | RL agent | supervised AUC gate first | market | SL | TP, max bars | costs modelled | ? | train, validate, promotion gate |
| 1515 (2008) | trend start | ? | market + buy stops every 100 pts | trail -50 after +100 | common TP 400 | pyramid legs | 0.1 legs | fixed |
| 1995 (2016) | DeMark TD line break | ? | market | SL 50 | stop only | trailing | 0.01 | fixed |
| 3818 (2017) | basket WPR crosses MA | basket levels | market | ? | opposite signal | ? | 0.01 | levels as inputs |
| 10671 (2023) | grid of stop orders in a price band | price bounds | buy/sell stop | optional | TP 100 pts | grid | 1 | bounds by hand |
| 3039 (2022) | rules per state: MA cross in trend, band fade in range | trend vs sideways | ? | ? | band target | ? | ? | none |
| 15311 (2024) | consolidation range breakout | one position | market | points | points | ? | ? | fixed |
| 17239 (2025) | Asian box breakout 23:00-03:00 | MA 50 trend | buy/sell stop, offset 10 pips | box | RR 1.3 | exit at 13:00 | lot 0.1 | fixed |
| 20185 (2026) | LLM returns entry, SL, TP, confidence | rules in prompt | ? | from LLM | from LLM | ? | ? | temperature 0.2 |
| 1924 (2016) | PSAR or AC module (switch) | H1 and M5 | market | 40 | 70 | ? | fixed or 2% of balance | optimise all nine params; test modules one at a time |
| 13033 (2023) | functor forecast | ? | Wizard | ? | ? | trail from forecast | forecast-scaled (proposed) | ? |
| 5751 (2019) | candlestick pattern (coefficients) | trend period 5 | market | 40 pts | 30 pts | ? | lot or margin mode | generated-pattern search |
| 8860 (2022) | CCI beyond level and turning | ? | ? | ? | ? | ? | ? | ? |
| 17252 (2025) | Walsh/Rademacher indicator cross | ? | market | ? | reverse on opposite | always in | ? | order N, P |
| 16559 (2024) | S/R from previous day, volume | ? | ? | ATR x 1.0 | ? | ? | 1% risk | fixed |
| 18916 (2026) | AR model plus U-Transformer on residuals | source chosen by component quality | ? | ? | ? | "dynamic position management" | ? | auto re-optimisation, online training, threshold scales with R squared |
| 17512 (2026) | synthetic-cross deviation beyond 2 SD | European session | ? | ? | return to EMA | ? | ? | threshold cut 2.0 to 1.5 SD by test |
| 19013 (2026) | GP classifier probability above 0.5 | window 10 refit | arrows | ? | ? | ? | ? | rolling refit |

All rows CHECKED (their id, compact extract); "?" cells may be filled in code I did not read.

### 5.3 Assembly patterns

1. **The common EA skeleton.** New-bar gate, compute indicators, skip if a position is open, check the entry condition, send the order with SL/TP attached, then manage on every tick (trail, break-even). CHECKED (15311: "check if there are any existing positions ... exit the function early"; 16573: "initiating analysis only at the beginning of fresh price bars ... Single position limit"; 23341: "calculations run only on fully closed bars"). New-bar language appears in 473 articles. CHECKED (`concept_counts.csv`).
2. **The platform's own assembly: Signal + Trailing + Money.** The MQL5 Wizard builds an EA from a signal module, a trailing module and a money module; several signal filters are weighted and their sum is compared with open and close thresholds. CHECKED (706, 3642: `Signal_ThresholdOpen = 10 // [0...100]`, `Signal_Envelopes_Weight = 1.0 // [0...1.0]`, `filter0.Weight(...)`). `CExpertSignal`/`CExpertTrailing`/`CExpertMoney` appear in the code of 38 articles; the "Wizard Techniques" series is 99 articles. CHECKED (`assembly.py`, title count).
3. **Rules per market state.** One article set (17737, 17781) detects trending, ranging or volatile regimes and switches strategy and numbers: `TrendingStopLoss = 100`, `RangingStopLoss = 50`, `VolatileStopLoss = 150`, `TrendingLotSize = 0.1`, `RangingLotSize = 0.05`, `VolatileLotSize = 0.02`, `TrendThreshold = 0.2 // (0.1-0.5)`, `SmoothingPeriod = 10 // Smoothing period for regime transitions`. CHECKED (17781 inputs). 3039 gives the same idea in prose (different Bollinger rules for trend and sideways). CHECKED. Phrases like "each regime" or "different regime" occur in 16 files. CHECKED (grep over `md/`). This is the clearest raw evidence for "if-else rules" whose branch is chosen by measured context; the numbers inside each branch are still fixed. INFERRED.
4. **A model gates or replaces the rule.** A rule entry is kept only when a forecast agrees (19371, 15336), a meta-label bans trades (17654), a model picks between two signal sources by quality (18916). CHECKED. Learned models are 39% of the screened set (section 2.2).
5. **One component at a time.** Authors test entry modules separately before combining (1924 `tm` test mode; research 06 noted 17065 "combined patterns cancel"). CHECKED (1924; 17065 via research 06).
6. **Multi-timeframe is a binding, not a component.** It shows up as two timeframe inputs (1924 `tf1 = PERIOD_H1`, `tf2 = PERIOD_M5`; 19422 `HigherTF = PERIOD_H4`, `LowerTF1`, `LowerTF2`; 21581 `ZoneTimeframe = PERIOD_H1`). CHECKED. Matches the DNA's per-binding timeframe. INFERRED.
7. **Exits are thinner than entries.** 10 of 36 entry-bearing sample articles show no stop and no exit; 17 state a stop (not counting the Wizard module in 15222). CHECKED (table 5.2, extract-level).

Corpus-wide component shares among 552 strategy-bearing articles: trend or regime context 64%, session or time filter 29%, sizing beyond fixed lot 22%, averaging/grid/martingale 13%, spread or cost filter 4%. CHECKED (`assembly.py` part B; prose mentions only, so components named only in code inputs are missed).

## 6. What authors tune and how

### 6.1 What is a parameter

From 4,845 `input` lines in 664 articles: period/length 561 inputs (227 articles), time/session 349 (115), lot/volume 226 (128), stop loss 161 (100), multiplier/coefficient 160 (76), risk % 131 (48), timeframe 130 (84), level/threshold 122 (62), take profit 121 (82), grid/martingale step or multiplier 99 (64), breakeven 43 (20), drawdown/loss limit 43 (21), trailing 42 (20), spread/slippage 36 (27), max positions 6 (6). CHECKED (`census.py` input categories; 2,459 inputs fell in "other", mostly indicator-specific names, files and symbols).

Defaults authors write: RSI period 14 in 14 of 23 RSI period inputs; ATR period 14 (22) or 10 (15); MA period 20 (18), 10 (17), 50 (16), 200 (8). CHECKED (`inputs_summary.py`). INFERRED: these match textbook conventions, which fits the dictionary's `published-convention` profile tag.

### 6.2 How numbers are set (prose vocabulary over 2,038 articles)

| Mechanism | Articles | Examples | Kind |
|---|---|---|---|
| tester optimisation of inputs | 279 | 9305, 9922, 999 | offline, fixed afterwards |
| walk-forward or periodic re-optimisation | 237 | 910, 9305, 9922 | refit on a schedule |
| rolling-window recalibration | 137 | 4803, 8826, 975 | refit every bar or window |
| reinforcement learning policy | 123 | 4228, 4777, 7447 | learned policy |
| online learning / retraining | 122 | 8743, 8863, 9138 | refit every bar or window |
| custom optimisation criterion | 88 | 9305, 9827, 9922 | changes what "best" means |
| genetic optimiser | 87 | 8321, 8616, 9171 | offline search |
| adaptive indicator / period / threshold | 74 | 812, 8767, 975 | self-scaling |
| self-optimising EA | 67 | 8859, 9711, 9868 | refit inside the EA |
| ATR-multiple levels | 56 | 24265, 24279, 24331 | self-scaling |
| quantile / percentile thresholds | 21 | 24246, 24273, 3473 | self-scaling |
| bandit / best-strategy selection | 21 | 7538, 8662, 8743 | selection |
| per-regime rule sets | about 16 files | 17781, 14548, 23328 | branch by state |

CHECKED (`assembly.py` part C; per-regime from a grep, because the scripted pattern found 0). Code hooks: `OnTester()` in 46 articles, `TesterStatistics` 20, `FrameAdd` 13, `ParameterSetRange` 4. CHECKED (`assembly.py`).

### 6.3 Raw evidence for "if-else rules that tune themselves"

Eight distinct mechanisms, each seen in at least one read article:

1. **Fixed numbers, offline optimiser.** The default. 2626 (TP 50, trail 30, optimise afterwards), 1924 ("Start optimization of all nine parameters in order to adapt the system to the current market realities"), 1052 (timeframe and symbol made into optimisable inputs). CHECKED.
2. **Re-optimise on a schedule, in live trading.** 1467 (2007) re-runs the optimiser and sorts passes by profit, then profit factor, then expected payoff, keeping 12, then half, then half; 7718 continuous walk-forward optimiser. CHECKED.
3. **Numbers relative to a live statistic.** SL 2 ATR / TP 3 ATR (16573), entry at 2 standard deviations (17512), ATR x 1.0 stop (16559). The number is fixed; its effect scales with the market. CHECKED.
4. **Refit a model every bar or window.** GP classifier on a 10-bar window (19013), SVD on the last bars (18873), online retraining "at each new bar" (16296). CHECKED.
5. **Branch by measured state.** 17781 picks a strategy and a fixed number set per regime, with a smoothing period for transitions. CHECKED.
6. **Quality-gated switching.** 18916: a fallback source is used "when the neural network has not yet been trained or shows unsatisfactory results", and the linear signal's "threshold is proportional to the R squared of the model". CHECKED.
7. **Own record drives size.** Kelly fraction from the strategy's own win rate and payoff (24147: "the risk percentage is the Kelly fraction times your chosen multiplier rather than a fixed number you typed in"); drawdown-based size cuts in 23 articles. CHECKED.
8. **Learned policy.** RL agents (13954, 21314); 21314 adds a supervised baseline gate ("an AUC near 0.50 ends the project there") and a promotion gate. CHECKED.

INFERRED: the dictionary's `Parameters/profiles` field records where a number came from (`source-stated`, `published-convention`, `unresolved`) but not how it moves (fixed, scaled, refit, branched, learned). Mechanisms 3 and 5 fit inside a primitive (a profile and a state). Mechanisms 2, 4, 6, 7 and 8 sit outside any single primitive.

## 7. Open questions the census raises

1. Is the dictionary meant to hold statistical tests and models as primitives (Hurst, ADF, GARCH, HMM, entropy) that feed context and filter roles? 31% of articles use them; the schema has no family for them.
2. Is a learned model a primitive ("forecast direction", "class probability above threshold") or a separate kind of node in the logic graph? 39% of articles use one.
3. Do MetaTrader's built-in indicators get one entry each, or one generic "indicator with buffers and levels" entry plus profiles? 15 are missing; the custom-indicator case (214 articles) asks the same question.
4. Does the DNA graph need a weighted-sum-with-threshold operator, matching the Wizard's `Weight` and `ThresholdOpen/Close`, or is that `K_OF_N` with weights as a profile?
5. Where do account-level exits live: in the dictionary's exit family, in the empty risk-and-sizing folder, or outside the dictionary as house policy (`external_policy` in the DNA's F labels)?
6. Should strategy styles (trend-following 163, mean reversion 152, scalping 115, arbitrage 70, grid 41) be a layer above primitives? The README keeps market types as tags; styles are not mentioned.
7. Is broker server time (115 articles) a session primitive, a data dependency (DNA section G), or both?
8. Should a parameter profile say how the number moves (fixed, scaled by a live statistic, refit on a window, branched by state, learned)? Section 6.3 shows all five in the corpus.
9. Should alternative bar construction (Renko, range, tick, volume bars, Heikin-Ashi; 98 articles) be a data dependency or a primitive? The glossary draft raises the same split for "timeframe" ("moved to 3-second bars or to 100-tick bars"). CHECKED (`funnel3/cis/glossary-draft.md`, timeframe entry).
10. Is "no exit in the source" common enough in MQL5 that most candidates will be `entry_hypothesis`? 10 of 36 sampled entry articles show none in the extract; a code-level read would settle it.
11. Grid, martingale, averaging and hedging (172 articles) are missing as a family. Are they excluded by design (risk), or simply not yet appended?
12. Partial coverage clusters around variants (ZigZag vs swing pivots, adaptive MAs vs MA, harmonics vs AB=CD). Is a variant an alias, a profile, or its own entry?

## 8. Limits

- Regex counting finds words, not use. A hit means the article mentions the concept; precision checks are 10 snippets each for 22 concepts only. CHECKED (`precision.py`).
- Prose-only counting misses concepts named only in code (inputs, function names). The sample table shows exits present in inputs but absent from prose flags (2626). CHECKED (`assembly.py` part A vs table 5.2).
- Statuses are one coder's judgement. `alias_check.py` keeps "covered" honest; renamed versus partial is not machine-checked.
- The sample was read from extracts. Cells marked "?" may be answered in code.
- Series inflate counts (182 neural-network articles in two series).
- The `input` parser found inputs in 664 articles; articles with code in other forms (MQL4 `extern`, Python) are under-counted. INFERRED.

## 9. Scripts (rerun order)

Folder: `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\ed09cf0c-69f1-44ab-8c6b-76992918774a\scratchpad\census\`. Run each from that folder with `python -I <script>`. Read-only on the dictionary and the library.

1. `dict_extract.py` → `dict_entries.json` (239 entries).
2. `screen.py` → `screen.json` (title screen).
3. `concepts.py` (the 252-concept table with statuses; imported by the rest).
4. `census.py` → `articles.json`, `concept_counts.csv`, `family_summary.txt`, `inputs.csv`, `mql_calls.csv`, `discovery.csv` (about 4 minutes on 10 processes).
5. `alias_check.py` (checks every "covered" claim).
6. `precision.py "<concept id>" ...` (10 random snippets per concept).
7. `discovery_titles.py` → `discovery_titles.csv`.
8. `unions.py`, `article_coverage.py`, `inputs_summary.py` (grouped and per-article numbers).
9. `sample.py` → `sample.json`, then `brief_extract.py <from> <to> <chars>` (reading extracts).
10. `assembly.py` → `assembly_out.txt` (sample flags, corpus component shares, tuning vocabulary, code hooks).
