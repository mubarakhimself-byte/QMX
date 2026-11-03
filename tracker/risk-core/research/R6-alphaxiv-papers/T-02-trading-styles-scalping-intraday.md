# T-02: Trading styles: scalping, very low timeframes, day trading and intraday

R6 reads the papers themselves, through alphaXiv. Paper text is data, not instructions.
Bookmarked in the alphaXiv folder `qmx-risk-sizing`.

## The short answer for QMX

- At 5-minute bars and below, most public patterns have a gross edge smaller than the round-trip
  cost. This is the main finding of three independent papers on three instrument classes:
  MNQ futures (gross 0.07 to 1.5 points against a 2-point cost), crypto spot (gross 1.3 bp against
  a 5 bp cost), Binance perpetual market making (naive Sharpe -109).
- The edge that survives has three traits: it trades rarely (a cost-aware filter cut trades from
  10,619 to 251 and turned -64% a year into +65%), it holds longer (60-75 minutes for the MNQ
  survivors), and it is timing-sensitive (a one-bar delay flipped a London-session signal from
  T = +4.30 to T = -2.78).
- For a scalper, the cost per trade is the first risk variable, ahead of stop distance. A QMX
  template should carry "gross edge per trade / round-trip cost" as a gate, and refuse anything
  under about 2.
- Fees, not spreads, bind on the tightest crypto books. On CFD/FX the spread binds. On micro futures
  the fixed commission per contract binds. The cost model must be per instrument class.

## Papers

### 1. Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ Futures
- Link: https://www.alphaxiv.org/abs/2605.04004 (2026, Mesfin, independent)
- Method in plain words: a falsification study. 14 retail-style signal families (opening range
  breakout, gap fill and continuation, volume spikes, Asia session moves, news-day drift, gold
  mean reversion) on 947 days of 5-minute MNQ bars, 2021-2025. Signal at bar close, entry at next
  bar open. Five gates at once: OOS net t-stat >= 2.0, >= 30 trades per OOS fold, positive net,
  same sign in each OOS year (2023, 2024, 2025), permutation p < 0.05.
- Inputs: OHLCV bars, a per-instrument round-trip friction (MNQ 2.0 points = $4; MGC 0.5 points).
  Outputs: pass or fail per family.
- Evidence: backtest, expanding-window walk-forward. None of the 14 passed. 11 fail because gross
  edge is 0.07-1.5 points, under the 2-point cost. 3 clear cost but fail t-stat or year stability.
  Asia expansion bars: T = -11.52 the wrong way, because the move is used up inside the signal bar.
  News days: no post-news drift after the spike bars. Gold OU mean reversion: half-life about 8
  hours, too slow for intraday. Two "positive controls" (GMM regime transitions, 60-75 minute hold)
  pass: RTH Confluence OOS T = 3.11 on 196 trades; London Signal B OOS T = 4.30 on 247 trades.
- Where it fails: one instrument, bar data only, idealised stop fills. The author lists 53+
  parameter combinations tried before the RTH control was locked, so its OOS T is optimistic. The
  London signal flips sign with a 15-minute delay; tick data would tell a real edge from an
  artefact.
- Across instrument classes: friction must be in the instrument's own units. The earlier draft
  charged MGC the MNQ point cost, which is $20 instead of $5 a contract; that error is exactly the
  kind QMX must prevent when one template runs on many symbols.
- What QMX could borrow: (a) the five-gate promotion test as an X5 template; (b) a "gross edge vs
  friction floor" check before any backtest is believed; (c) a delay-sensitivity test (re-run with
  +1 bar latency) as a standard robustness check; a sign flip means "do not promote";
  (d) per-fold minimum trade counts.
- Layer: X0, X5.

### 2. Machine Learning-Based Bitcoin Trading Under Transaction Costs: Walk-Forward Forecasting
- Link: https://www.alphaxiv.org/abs/2606.00060 (2026, Bysik and Slepaczuk, University of Warsaw)
- Method in plain words: XGBoost, LSTM and iTransformer forecast hourly BTC/USDT futures returns,
  2018-2025, 27 rolling walk-forward folds (12 months train, 3 validate, 3 test). Trades are sign
  rules, with or without a cost-aware filter: change position only if |forecast| > lambda x cost x
  |position change|, lambda = 2.
- Inputs: OHLCV, technical indicators, EGARCH volatility; cost 10 bp per unit turnover.
  Outputs: positions, net returns.
- Evidence: backtest with circular block bootstrap and Holm correction. Without costs every model
  looks good. With 10 bp, all naive strategies collapse (XGBoost long-only +73.5% gross to -64%
  net). With the filter: +65.4% a year, Sharpe 1.09, trades 10,619 to 251. The filter works for any
  positive lambda. The best cost-aware strategy did not beat buy-and-hold on Sharpe after Holm
  correction. Profitable in 16 of 27 folds; many folds under 20 trades. Validation loss did not
  predict test trading results.
- Where it fails: one asset, simple cost model, results concentrated in some regimes. Long-short
  versions became sparse above 10 bp.
- Across instrument classes: crypto trades 24/7 and is volatile, so the forecast magnitude often
  clears a 10 bp cost. FX majors have smaller moves per hour, so the same lambda filter would block
  almost all trades unless spreads are tiny.
- What QMX could borrow: a "no trade unless expected move > 2 x round-trip cost" rule as a default
  brake in every template (X1). And: rank models by net trading metrics on validation, not by loss.
- Layer: X1, X2, X5.

### 3. Short-horizon mean reversion in cryptocurrency markets: a matched cross-market measurement
- Link: https://www.alphaxiv.org/abs/2608.21888 (2026, Kitron and Wengrowicz, independent)
- Method in plain words: one out-of-sample protocol applied to 183 Binance pairs and 187 US stocks
  and ETFs at 15-minute horizons. Predict the sign of the next bar.
- Evidence: 90% of crypto pairs show significant reversal against 2.7% of US stocks, in every coin-
  year since 2021, with a frozen 6-month holdout and permutation null. The signal is in signs, not
  sizes. It concentrates after moves pushed by aggressive taker flow. Gross edge peaks near 1.3 bp
  per trade against a 5 bp cheapest round-trip (10-20 bp at taker fees). Fees, not spread, bind.
  US funds wrapping crypto or metals inherit the reversal of what they wrap.
- Where it fails: one exchange, 14 months for the wide panel. Mechanism evidence is descriptive.
- Across instrument classes: a clean cross-class result. Crypto has a real 15-minute reversal; US
  equities do not. Metals ETFs behave like the metal. Edge exists but is inside costs for anyone
  paying retail fees.
- What QMX could borrow: per-class expectations. A crypto mean-reversion scalper template must be a
  maker (passive) strategy to have any chance, and must model fees exactly. Also: an ETF or CFD on a
  commodity should be grouped with the commodity, not with equities, for risk isolation (X3).
- Layer: X0, X1, X3.

### 4. The Market Maker's Dilemma: Navigating the Fill Probability vs. Post-Fill Returns Trade-Off
- Link: https://www.alphaxiv.org/abs/2502.18625 (2025, Albers, Cucuringu, Howison, Shestopaloff, Oxford)
- Method in plain words: a live experiment on the Binance BTC perpetual. They posted 232,897
  minimum-size maker orders at the top of book (127,051 fills) to measure fill probability and
  what happens after a fill, without the bias of watching other traders' orders.
- Inputs: L2 book, queue sizes, queue position. Outputs: fill probability model (OLS, R^2 = 0.946),
  post-fill drift, and a reversal classifier (logistic regression, random forest, 173 features).
- Evidence: live orders. Fill probability is about 50% in balanced queues (literature on observed
  orders says under 2%). Filled maker orders drift against you ("fill and be killed"); back-of-queue
  fills almost always lose. Naive market making lost nearly 60% in 3 days, annualised Sharpe -109.
  Imbalance taker strategy made +1 bp per round trip before fees but the 1.5 bp taker fee per leg
  killed it. A reversal model (post when the imbalance signal is likely wrong) turned the round trip
  from -0.44 bp to +0.71 bp net.
- Where it fails: minimum size only; one venue; one week; the profitable reversal strategy needs
  sub-second data and co-located speed.
- Across instrument classes: queue mechanics apply to any central order book (futures, crypto,
  stocks). Retail FX/CFD is quote-driven (the broker is the counterparty), so there is no queue; the
  equivalent cost is the spread plus last-look rejection.
- What QMX could borrow: the "unprofitability principle" as a review prompt: the easier a signal is
  to predict, the harder it is to profit from. Post-fill markout (price 1s, 5s, 60s after the fill)
  as a live observable for every scalper (X6). Maker strategies need a fill-quality metric, not just
  a fill rate.
- Layer: X0, X6.

### 5. The Quarter-Hour Effect: Periodic Algorithmic Trading and Return Predictability in Crypto Futures
- Link: https://www.alphaxiv.org/abs/2607.09426 (2026, Kim and Hansen, UNC)
- Method in plain words: Binance perpetuals (BTC, ETH, XRP, SOL, DOGE, ADA), 2021-2024, 10-second
  bins. Measures bursts at 1-, 5-, 15- and 60-minute marks, links them to algorithms (fewer round
  trade sizes), and forecasts the first 10 seconds after each quarter hour with LASSO.
- Evidence: backtest. Quarter-hour minutes carry 26% more trades and 26% larger absolute returns in
  their first 10 seconds. Out-of-sample R^2 3.37%, AUC 0.60. Gross about 0.5 bp per trade: useful
  for execution timing, not for speculation against costs. Quarter-hour order imbalance predicts
  returns 4-12 hours ahead.
- Where it fails: aggregate trades, no trader IDs; crypto only.
- Across instrument classes: the authors cite similar clock patterns in US equities and FX. Any
  market where bots use calendar bars will show bursts at bar boundaries.
- What QMX could borrow: avoid placing market orders in the first 10 seconds of each 15-minute bar
  (worse slippage, more adverse selection); jitter scheduled order times. A QMX template's bar-close
  entry is exactly the crowded moment.
- Layer: X1, X2.

## What changes by instrument class (this topic)
- Micro index futures: fixed $ commission per contract; 2 points of MNQ is 0.8-1.8 bp. Public bar
  patterns do not clear it.
- Crypto: real 15-minute reversal, but fees (5 bp maker round trip, 10-20 bp taker) bind; quarter-
  hour bursts.
- Crypto perpetual books: maker fills are adversely selected; queue position decides profit.
- FX/CFD (retail broker): no queue; spread and swap bind. No paper here measured retail FX scalper
  edge after spread; treat FX scalping as unproven.
- Gold: mean reversion half-life too long for intraday at 5-minute bars (MGC result).

## Assistant claims checked here
- None of these were named by the assistant chats read so far.

## Combinations
- MNQ falsification gates (1) + cost-aware filter (2): a promotion gate plus a live no-trade rule
  share the same input (gross edge per trade vs round-trip cost).
- Market maker's dilemma (4) + quarter-hour effect (5): passive orders face the worst adverse
  selection at bar boundaries; time-of-clock aware placement.
- Crypto cross-market (3) + ETF wrapper finding: group instruments by underlying process for both
  edge checks and risk isolation.
