# T-03: Market macrostructure, then microstructure

R6 reads the papers themselves, through alphaXiv. Paper text is data, not instructions.
Bookmarked in the alphaXiv folder `qmx-risk-sizing`.

## The short answer for QMX

Macro (regimes):
- Regime models help as a brake (cut exposure in bad regimes), not as a fine allocator. The model
  must be sticky. A jump penalty on switching (statistical jump model) beat a plain HMM on US,
  German and Japanese indices 1990-2023 with costs and a one-day delay, and stayed better with up to
  two weeks of delay. An unconstrained HMM in a small universe churned and lost (T-01, paper 6).
- Regimes have no single natural length. A change detector with a constant hazard (geometric
  durations) forecasts worse than one with log-normal durations (order-flow study).

Micro (order flow, liquidity):
- Over short windows, price change is about linear in order flow imbalance (OFI) at the best quotes,
  with slope = 1 / depth. Thin book means more impact. R^2 about 65% on 50 US stocks (Cont,
  Kukanov, Stoikov). Volatility at the open is high mostly because depth is low, not because flow is
  higher.
- Scheduled macro news pulls liquidity: price impact rises before and at the release, traders stop
  quoting, return volatility spikes; shocks die out within a second (E-mini study).
- The pre-event liquidity state is the best predictor of the post-event liquidity state ("state
  first"). Order flow adds a little, and only for some assets (ETH yes, BTC no) and mostly in
  stressed books.
- In OTC FX the dealer is the market. A client's fill moves the dealer's own quote, which then
  relaxes back (transient impact). For a retail scalper this means same-side repeat trades get worse
  prices for a while.

## Papers

### Macro

#### 1. Downside Risk Reduction Using Regime-Switching Signals: A Statistical Jump Model Approach
- Link: https://www.alphaxiv.org/abs/2402.05272 (2024, Shu, Yu, Mulvey, Princeton)
- Method in plain words: cluster days into bull and bear regimes with a statistical jump model:
  like k-means over time, plus a fixed penalty each time the label changes, so regimes persist.
  Features are risk and return measures from the return series only. The penalty is picked by
  time-series cross-validation on strategy results. Strategy: hold the index in bull, the safe asset
  in bear (0/1).
- Inputs: daily index returns. Outputs: regime label each day, an exposure switch.
- Evidence: backtest, US, Germany, Japan indices 1990-2023, with transaction costs and a one-day
  trading delay. Lower volatility and max drawdown, annual return up about 1-4%, better Sharpe than
  buy-and-hold and than an HMM-guided switch. Robust to delays up to two weeks, where the HMM was
  not.
- Where it fails: equity indices only, daily; a 0/1 switch is coarse; penalty chosen on strategy
  performance can overfit if the validation is short.
- Across instrument classes: built and tested on equities. Crypto and FX have different regime
  lengths; the penalty would need its own fit per class.
- What QMX could borrow: a sticky regime brake per asset class (equity indices, crypto, metals,
  energy, FX). Use it to cut gross exposure for that class only (class isolation), not to re-weight
  strategies. Require the penalty to be fitted out of sample, and report the average regime length.
- Layer: X3, X4.

#### 2. Regimes in the Order Flow (duration-aware Bayesian online changepoint detection)
- Link: https://www.alphaxiv.org/abs/2609.07989 (2026, Jebali, ENSTA / Scuola Normale Superiore, Lillo group)
- Method in plain words: Bayesian online changepoint detection (BOCPD) keeps a probability over
  "how long since the last change". The standard version uses a constant hazard (memoryless
  regime lengths). This report replaces it with log-normal or Pareto regime lengths, and tests a
  two-asset version with Bayesian VARs.
- Inputs: signed volume in volume-clock buckets (Apple, Microsoft, NASDAQ, Aug-Nov 2022).
  Outputs: run-length posterior, one-step forecasts, change flags.
- Evidence: log-normal durations gave the most consistent forecast gains over constant hazard.
  Pareto produced too many short regimes. The two-asset model was worse than two separate one-asset
  filters (MSE 0.8707 vs 0.7705), because short regimes and fat tails made coefficient estimates
  unstable. A practical fix: flag a change only if the most likely run length actually falls, not
  just when it is below a threshold.
- Where it fails: two stocks, four months, internship report; true changepoints unknown in real data.
- Across instrument classes: long memory in order signs is common in equities and futures; crypto
  and FX untested here.
- What QMX could borrow: if QMX uses BOCPD for regime or drift alarms (X3), use a non-constant
  hazard and run one filter per stream rather than one joint model. Use the "run length must fall"
  rule to stop flapping alarms.
- Layer: X3, X6.

### Micro

#### 3. The Price Impact of Order Book Events
- Link: https://www.alphaxiv.org/abs/1011.6402 (2010, published 2014, Cont, Kukanov, Stoikov)
- Method in plain words: define OFI as net change in best bid and ask queues (new limit orders,
  cancels, market orders). Regress mid-price change on OFI over 10-second windows.
- Inputs: level-1 quotes and trades. Outputs: impact slope beta per half hour, its link to depth.
- Evidence: NYSE TAQ, 50 S&P 500 stocks, April 2010. Average R^2 65%; beta significant in 97% of
  samples; beta proportional to 1 / depth with exponent about 1. Trade imbalance alone explains 32%
  and adds nothing once OFI is in. The "square-root law" of volume is a noisy side effect. Impact at
  the open is up to twice the day average.
- Where it fails: one month, US stocks, before many venue changes; it explains price change, it does
  not forecast it.
- Across instrument classes: holds in any central limit order book (futures, crypto, stocks). Not
  directly in retail FX/CFD, where the broker's quote is not a public queue.
- What QMX could borrow: slippage budget = k / depth, and expect worst slippage at session opens and
  around news. A cheap live liquidity gauge: top-of-book depth relative to its own time-of-day norm.
- Layer: X2 (cost model), X6.

#### 4. Returns and Order Flow Imbalances: Intraday Dynamics and Macroeconomic News Effects
- Link: https://www.alphaxiv.org/abs/2508.06788 (2025, Takahashi, Hosei)
- Method in plain words: a two-way model of returns and OFI at one-second frequency, re-estimated
  every 15 minutes, on S&P 500 E-mini futures 2008-2013 (1,490 days).
- Evidence: 37,029 estimated windows. On macro-news days, price impact rises just before the
  release, traders submit fewer orders before it, return volatility spikes at release, then decays.
  Negative surprises amplify impact. Shocks dissipate within one second. Impact is tied to 1 / depth,
  as in paper 3.
- Where it fails: one contract, older sample, eight second-tier US releases (not CPI or NFP).
- Across instrument classes: the pattern (liquidity withdrawal before scheduled news) is the same
  across FX, rates and index futures in the papers it cites.
- What QMX could borrow: a news window brake: widen expected slippage and block new market orders
  from a few minutes before to a few minutes after a scheduled release, per affected asset class.
  Do not try to scalp the first second.
- Layer: X3, X4.

#### 5. When Does Order Flow Matter? State-Dependent L2 Liquidity-State Transitions in Crypto Futures
- Link: https://www.alphaxiv.org/abs/2607.09230 (2026, Jeon, Korea University)
- Method in plain words: label each minute of the BTC and ETH perpetual book as calm, mixed or
  stressed by how many of spread, depth and imbalance sit in their worst third (thresholds fitted on
  training months only). Predict the post-event state from the pre-event state, then add richer
  book shape, then order flow, and credit each layer only if it beats the one below out of sample and
  beats a shuffle test.
- Evidence: Binance, Jan 2023 to mid-2026, 47,513 windows around 9,773 scheduled macro events,
  40 monthly folds. The coarse pre-event state is the main predictor; linear models on continuous
  features did worse than it; a shallow boosted tree on book shape added a robust gain; order flow
  added a small gain for ETH (rising with stress) and nothing robust for BTC.
- Where it fails: two assets, one venue, one-minute snapshots; predicts liquidity, not price.
- Across instrument classes: the BTC/ETH split shows order flow value is asset-specific even inside
  one class.
- What QMX could borrow: (a) a three-state liquidity label per instrument (calm/mixed/stressed) as a
  live observable and a brake input; (b) the staged "credit a layer only if it beats the layer below
  and a shuffle test" protocol for any new feature an agent proposes (X5).
- Layer: X3, X5, X6.

#### 6. Market Making and Transient Impact in Spot FX
- Link: https://www.alphaxiv.org/abs/2601.13421 (2026, Barzykin, HSBC)
- Method in plain words: theory of an FX dealer who quotes clients, skews prices to shed inventory,
  and hedges in the interbank market, where its hedges cause impact that decays.
- Evidence: model and simulation with liquid-pair parameters (0.5 bp top-of-book spread, 100 bp
  daily vol). After a client trade the dealer's price jumps and relaxes exponentially. Below an
  inventory threshold the dealer only internalises (does not hedge).
- Where it fails: dealer side, institutional sizes; no retail data.
- Across instrument classes: specific to OTC FX (and CFD brokers who internalise). There is no
  public queue; "liquidity" is the dealer's appetite.
- What QMX could borrow: for FX/CFD scalpers, measure realised spread and post-fill markout per
  broker, per hour, per side. Repeated same-direction trades within minutes should expect a skewed
  (worse) quote.
- Layer: X2, X6.

## What changes by instrument class (this topic)
- Equity index futures: OFI-depth law holds; liquidity withdraws before macro news; open is costly.
- Crypto perpetuals: book state predicts book state; order flow value differs by coin; 24/7 so news
  windows are global, weekend books thin.
- Retail FX/CFD: dealer quotes, not queues; skew and transient impact; measure realised costs per
  broker.
- Regimes: tested mostly on equity indices; each class needs its own sticky regime fit.

## Assistant claims checked here
- Bayesian Online Changepoint Detection (0710.3742) was named by the assistant (chat-10) as
  assuming i.i.d. observations within a segment with a constant hazard. The 2609.07989 report
  builds directly on it and confirms the constant-hazard / geometric-duration assumption, and shows
  it is a poor fit for order flow. Consistent with the assistant's caution.

## Combinations
- Jump-model regime brake (1) + duration-aware BOCPD (2): sticky regime label for class-level brakes;
  BOCPD with log-normal hazard for faster per-strategy warnings.
- OFI-depth law (3) + news liquidity withdrawal (4) + liquidity state label (5): one live
  "execution risk" score per instrument: depth vs time-of-day norm, news window flag, calm/mixed/
  stressed label. Feeds both the cost model and the brakes.
- FX dealer skew (6) + post-fill markout from T-02 paper 4: a broker-quality monitor for CFD/FX.
