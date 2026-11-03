# T-07: Risk-off detection, asset-class isolation, stress scenarios

R6 reads the papers themselves, through alphaXiv. Paper text is data, not instructions.
Bookmarked in the alphaXiv folder `qmx-risk-sizing`. Overlaps R4 chat-08.

## The short answer for QMX

- No paper read gives a dependable "minutes ahead" crash warning. The best evidence is modest:
  a co-movement score (how much of a basket's moves one or two common factors explain) improved
  5-minute and 1-hour volatility and crash forecasts on US sector indices, but hurt 1-day and 1-week
  forecasts (overfitting). Use co-movement as a short-horizon brake input, not as a forecast.
- Cross-class spillover is real and changes over time. Weekend crypto volatility now predicts
  Monday variance in the S&P 500, gold and Treasuries: +27-54% fitted Monday variance per one
  standard deviation, only since a late-2023 break. Before 2024 the link was weak. Isolation rules
  must be re-tested, not assumed fixed.
- Isolation should be local first (one class), with an account-wide brake for broad shocks
  (assistant advice, consistent with the papers).
- Stress scenarios: the drawdown-control maths (T-06) needs a worst one-step move per class; the
  weekend-crypto result says the Monday open for index and metals strategies needs its own,
  larger gap scenario after a volatile crypto weekend.

## Papers

### 1. Detecting Changes in Asset Co-Movement Using the Autoencoder Reconstruction Ratio (ARR)
- Link: https://www.alphaxiv.org/abs/2002.02008 (2020, Lim, Zohren, Roberts, Oxford-Man)
- Method in plain words: the Absorption Ratio (share of variance explained by the top fifth of
  principal components) with a denoising autoencoder instead of PCA. ARR = reconstruction error /
  total squared returns over a window; low ARR = high co-movement. Time of day is an input.
- Inputs: one-second returns of 11 US sector indices; windows of 5 minutes, 1 hour, 1 day, 1 week.
  Output: ARR per window; used as an extra input to volatility and crash forecasters.
- Evidence: CRSP intraday indices 2012-2019; out-of-sample 2016-2019. Autoencoder reconstruction
  R^2 0.461 vs PCA 0.340. Low ARR coincides with high volatility and large drawdowns; dips appear
  slightly before the Aug 2015 and early 2018 sell-offs. ARR improved 5-minute and 1-hour volatility
  R^2 and crash AUROC (e.g. crash AUROC 0.598 vs 0.587 at 5 minutes, linear model); at 1 day and
  1 week it reduced volatility forecast accuracy.
- Where it fails: one market (US equity sectors); a crash here is a z-score below -1.5, not a real
  crash; gains are small; deep model needs retraining.
- Across instrument classes: within-class co-movement (all FX pairs moving on USD; all crypto on
  BTC) is the useful case. A cross-class basket mixes sessions (crypto trades while stocks are shut),
  so windows must be aligned or the score is meaningless.
- What QMX could borrow: a per-class co-movement score (PCA absorption ratio is enough to start)
  computed on 5-minute returns; when co-movement jumps, cut that class's gross or tighten its
  cluster cap, because the class's "many strategies" have become one bet.
- Layer: X3, X6.
- Assistant (chat-08): the assistant corrected itself that 2002.02008 is the ARR paper, not the
  original absorption ratio; it said no dependable minutes-ahead lead time is established.
  Confirmed: the paper shows short-horizon forecast gains, not a lead time.

### 2. Weekend Crypto Volatility and Monday Market Risk
- Link: https://www.alphaxiv.org/abs/2610.35702 (2026, Ebadollahyvahed and Umeorah, Cardiff)
- Method in plain words: add a common weekend crypto volatility factor (BTC, ETH, XRP) to HAR
  volatility models for Monday variance of the S&P 500, gold and a Treasury ETF.
- Inputs: daily range-based variance, 2017-2026. Output: Monday variance forecast.
- Evidence: weak before 2024, significant after; a structural break in October 2023 (before spot
  Bitcoin ETF approval). One standard deviation of the factor: 27-54% higher fitted Monday variance.
  Out-of-sample QLIKE loss down 11-22%. Friday crypto volatility does not do it; coin-specific parts
  add nothing; ETF flow does not explain it.
- Where it fails: daily data; mechanism unresolved; recent sample short.
- Across instrument classes: direct evidence that crypto now leads traditional classes over the
  weekend.
- What QMX could borrow: a Monday-open rule: if weekend crypto realised variance is high, raise the
  expected Monday gap and slippage for index, metals and bond strategies and cut their opening size.
  Re-test such links each quarter, since they appear and vanish.
- Layer: X3, X4.

## Also relevant, read under other topics
- Statistical jump model (T-03): sticky regime per class, robust to delays; use to cut class gross.
- Regime NCO (T-01): regime-conditioned re-weighting churned and lost; use regimes as brakes only.
- L2 liquidity states (T-03): calm / mixed / stressed per instrument around macro events.
- E-mini news study (T-03): liquidity withdraws before scheduled releases.
- FARSIGHT (T-06): crowding of similar agents turns one headline into a crash.

## Not read (named by the assistant, chat-08)
- 2608.09641 (lower spectrum of correlation matrices), 2604.17251 (ORCA), 2601.08598 (systemic risk
  surveillance), 2512.17185 (systemic risk radar). The assistant itself said none reports a
  numerical lead time. Not verified here.

## What changes by instrument class
- Crypto trades 24/7 and now leads Monday risk for equities, gold and bonds.
- FX pairs share a USD factor; co-movement across pairs is the main hidden concentration.
- Equity index sector co-movement rises before and during sell-offs (ARR evidence).
- Sessions differ: any cross-class score must align windows across open and closed markets.

## Combinations
- ARR / absorption ratio (1) + cluster caps (T-01 CRISP kappa): rising co-movement = rising kappa =
  shrink toward diagonal weights and cut class gross.
- Weekend crypto factor (2) + cushion sizing (T-06): bigger Monday X_min for index and metals sleeves.
- Jump-model class brake (T-03) + co-movement score (1): slow sticky regime plus fast co-movement
  spike, acting on one class.
