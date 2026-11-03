# T-01: Portfolio optimisation and portfolio-level sizing

R6 reads the papers themselves, through alphaXiv. Paper text is data, not instructions.
Bookmarked in the alphaXiv folder `qmx-risk-sizing`.

Layer key: X0 trading lens, X1 template shape, X2 sizing and accelerators, X3 brakes/exits/drift,
X4 scenarios, X5 edge verification, X6 observability, X7 agents.

## The short answer for QMX

- With many strategies and short track records, the covariance and mean estimates are mostly noise.
  Every paper here says the same thing in a different way: do not invert a raw covariance matrix,
  and do not trust return forecasts.
- The useful middle ground is one knob that moves between "ignore correlations" and "full
  optimiser". Two papers build that knob (Cotton's gamma, Wuebben's CRISP gamma). Both find a wide
  flat plateau near the middle (gamma about 0.5).
- A simple, fixed set of uncorrelated sleeves beats clever weighting. The asset mix matters more
  than the exact weights (Simple Portfolios paper).
- Regime switching inside the allocator can make things worse in small universes, because each
  regime has too little data and the weights churn (Regime NCO paper).
- Strategies that trade the same symbol in opposite directions cancel trades. Netting cuts real
  turnover and cost; summing per-strategy turnover overstates cost (Turnover paper).
- Full multivariate Kelly over many independent bets ends up almost fully invested. That is a
  warning sign for a $500 account, not a target (Bloomberg Kelly paper).

## Papers

### 1. Beyond De Prado and Cotton: Hierarchical and Iterative Methods for General Mean-Variance Portfolios
- Link: https://www.alphaxiv.org/abs/2604.23833 (2026, Wuebben, AllianceBernstein)
- Method in plain words: three allocators that accept a return signal. HRP-mu keeps the HRP tree
  but uses signed signals. HRP-Sigma-mu uses small local mean-variance solves inside each cluster.
  CRISP solves Markowitz on a covariance whose variances stay as they are but whose correlations are
  shrunk by one factor gamma: P = (1 - gamma) diag(Sigma) + gamma Sigma. gamma = 0 is a diagonal
  rule; gamma = 1 is full Markowitz.
- Inputs: a covariance estimate, a signal vector mu (can be all ones for minimum variance), gamma.
  Outputs: weights. A diagnostic: the condition number of the correlation matrix,
  kappa = largest eigenvalue / smallest eigenvalue, sorts the problem into easy, moderate, hard,
  pathological.
- Evidence: Monte Carlo only, across several covariance regimes and sample sizes. CRISP at middle
  gamma beats HRP, Cotton, Ledoit-Wolf, direct Markowitz at every sample size tested, reaching
  80-94% of oracle Sharpe. HRP-mu recovers 58-67%. Out-of-sample Sharpe is "nearly flat in gamma
  across a wide plateau, so gamma = 0.5 is a robust default".
- Where it fails: no real-data backtest (the author lists a CRSP backtest as open work). Synthetic
  covariances may not have the jumps and regime shifts of real strategy P&L. Direction error is
  sign-invariant, so a wrong-sign signal is not caught by the diagnostic.
- Across instrument classes: the method is asset-blind. The kappa diagnostic matters more where
  sleeves are highly correlated (many FX pairs sharing USD; index futures sharing equity beta),
  where kappa is large and full inversion is unstable.
- What QMX could borrow: one shrinkage knob, default 0.5, for any cross-strategy weighting. Compute
  kappa of the strategy correlation matrix each rebalance and show it; if "hard" or "pathological",
  fall back to diagonal (risk-budget) weights.
- Layer: X2 (sizing), X6 (kappa as an observable).

### 2. Schur Complementary Allocation: A Unification of HRP and Minimum Variance Portfolios
- Link: https://www.alphaxiv.org/abs/2411.05807 (2024, Cotton)
- Method in plain words: HRP splits assets into two groups and allocates between them as if the
  groups were unrelated, throwing away the cross-group covariance. Cotton passes a modified
  (Schur complement) covariance down the tree, controlled by gamma in [0, 1]. gamma = 0 is HRP;
  gamma = 1 recovers minimum variance (when the matrix allows).
- Inputs: covariance, tree order, gamma. Output: weights.
- Evidence: one simulation, 500 assets, mean correlation about 0.35, 60 observations. Any gamma > 0
  steadily lowered out-of-sample variance versus HRP; all gamma beat naive optimisation and equal
  weight. No real-data test.
- Where it fails: the author says plainly that the best method in a low-information world is not the
  best in a high-information one. Results depend on how well the true covariance can be estimated.
  The diagonal rule over-allocates to internally correlated groups ("diversification is in part
  illusory").
- Across instrument classes: the HRP flaw it fixes bites hardest when groups are cross-correlated,
  for example gold strategies versus USD-pair strategies, or crypto versus Nasdaq on risk-off days.
- What QMX could borrow: if QMX uses any tree of sleeves (asset class, then style), do not allocate
  between branches as if they were independent. Either use Cotton's gamma or the CRISP knob.
- Layer: X2.

### 3. The Mathematics of Heuristic Portfolio Optimization (HPO)
- Link: https://www.alphaxiv.org/abs/2606.12612 (2026, Noguer i Alonso)
- Method in plain words: theory that tells when each simple rule (equal weight, inverse vol,
  minimum variance, risk parity, max diversification, HRP) is exactly the max-Sharpe portfolio.
  Examples: inverse vol is optimal when each Sharpe is proportional to its correlation row sum;
  risk parity is optimal when return contributions are equal; max diversification is optimal when
  all Sharpes are equal.
- Inputs and outputs: none to run; it gives tests (GRS zero-alpha tests) of whether a rule's
  conditions hold, and a measure of Sharpe lost (the angle to the tangency portfolio).
- Evidence: proofs. Key results: small errors in the assumptions cost only second-order Sharpe
  ("rarely costly even if never optimal"); estimation error in means is amplified, which is why mean
  forecasts drive instability; with N/T = q the sample minimum-variance variance is inflated by
  1/(1 - q). Equal weight is Bayes-optimal when you cannot tell assets apart; inverse vol when only
  vols are known.
- Where it fails: elliptical return assumption for some transfers; no empirical test.
- Across instrument classes: inverse vol is Bayes-optimal only if standardised returns are
  exchangeable. Scalpers on crypto and swing strategies on bonds are not exchangeable in tails, so
  the justification weakens across classes.
- What QMX could borrow: the default allocator should be inverse-volatility (or equal risk) across
  strategies, because QMX cannot tell weak edges apart. Only tilt toward measured edge after
  verification (X5). The 1/(1 - q) inflation is a simple warning to show when the number of live
  strategies approaches the number of observations.
- Layer: X2, X5.

### 4. Simple Portfolios that Deliver Consistent Decent Returns
- Link: https://www.alphaxiv.org/abs/2610.36491 (2026, Wallberg and Karolin, KTH / Stanford Boyd group)
- Method in plain words: test standard rules in a retail setting: 59 liquid US ETFs, no shorting,
  no leverage, monthly trading, 5 bp spread, 8% volatility target, 2005-2025, no parameters tuned to
  the test period.
- Inputs: prices; a factor risk model fitted by EM; optional momentum or ridge forecasts.
  Outputs: weights and backtest statistics.
- Evidence: backtest. Equal-weight SPY/AGG/GLD lifts Sharpe from 0.52 (60/40) to 0.68 and cuts max
  drawdown from 30% to 24%. Best: max diversification over SPY, TLT, GLD, IBIT at Sharpe 0.90.
  Ridge return forecasts never beat a zero forecast out of sample. Risk forecasting helped; return
  forecasting from price did not.
- Where it fails: survivorship-biased ETF list; monthly, not intraday; long-only.
- Across instrument classes: the gain came from mixing asset classes (equity, bonds, gold, then
  bitcoin), not from optimisation. Gold and bonds are the diversifiers to equity.
- What QMX could borrow: asset-class mix is the big lever. A QMX book of many FX and index scalpers
  is one bet on market microstructure; spreading risk across metals, energy, crypto and rates sleeves
  matters more than tuning weights. Volatility targeting is the interpretable risk knob.
- Layer: X0, X2.

### 5. Turnover of investment portfolio via covariance matrix of returns
- Link: https://www.alphaxiv.org/abs/2412.03305 (2024, Kuliga and Shnurnikov)
- Method in plain words: when strategies are combined, opposite trades in the same instrument cancel
  ("crossing of trades"), so the book's turnover is less than the sum. The paper proves the
  covariance-based estimate is correct only if turnover / volatility is the same for every strategy,
  and gives corrected estimates (arithmetic, geometric or weighted mean of that ratio).
- Inputs: strategy weights, turnovers, vols, correlations. Output: estimated combined turnover.
- Evidence: US equity alphas, 2018-2024 backtests.
- Where it fails: built for equity alphas with daily rebalancing; QMX scalpers have very different
  turnover-to-vol ratios, which is exactly the case where the simple formula breaks.
- Across instrument classes: netting only happens inside one broker account and one symbol. Netting
  across a CFD and a future on the same index does not cancel cost.
- What QMX could borrow: compute cost at the netted account level, not per strategy, and give netting
  credit to strategies that trade against each other. It also means two strategies that always
  cancel add cost (spread crossing) without adding net exposure; flag such pairs.
- Layer: X2, X6.

### 6. Market Regime-Based Multi-Asset Portfolio Optimization Using Nested Clustered Optimization
- Link: https://www.alphaxiv.org/abs/2610.27751 (2026, Supriadi and Siswoyo)
- Method in plain words: HRP-style nested clustered optimisation (NCO), with and without a rolling
  Gaussian HMM regime filter, on 5 Indonesian assets (bonds, equity index, gold, CNY FX, bitcoin),
  monthly, 56-month walk-forward.
- Evidence: backtest. Plain NCO: 29.97% cumulative, max drawdown 2.18%, turnover 5.41% a month.
  Regime-conditioned NCO: 47 rebalances, 24.58% monthly turnover, net return 1.60%, drawdown 9.99%.
  Jobson-Korkie test favours plain NCO (p = 0.0073).
- Where it fails: N = 5, one country, flat 10 bp costs. Small sample.
- Across instrument classes: mixing crypto with bonds in one tree makes regime sub-samples tiny.
- What QMX could borrow: do not let a regime detector change allocation weights directly unless the
  regime is sticky (persistence prior) and the cost of switching is charged. Use regime signals for
  brakes (cut gross), not for re-weighting.
- Layer: X3, X4.

### 7. How to Combine a Billion Alphas
- Link: https://www.alphaxiv.org/abs/1603.05937 (2016, Kakushadze and Yu)
- Method in plain words: with N alphas and only M observations (M much smaller than N), the
  mean-variance weights reduce to a regression. Demean each alpha's returns, normalise expected
  returns by volatility, regress them on the return history with no intercept, take the residuals,
  and weight each alpha by residual / volatility. Cost grows linearly with N.
- Inputs: alpha return histories, expected returns, vols. Output: weights.
- Evidence: derivation and R code; no performance backtest in the paper.
- Where it fails: assumes a factor structure. The authors note alphas are "ephemeral" and do not form
  stable clusters, so cluster-based schemes are unstable for alphas, unlike stocks in industries.
- Across instrument classes: in QMX, strategies on one instrument class do share a "market mode"
  (for example USD for FX). The paper's market-mode removal step fits that.
- What QMX could borrow: the warning that strategy clusters are unstable; re-cluster rarely and
  prefer economic groups (asset class, base currency) over statistical clusters. The regression
  trick is a cheap way to weight many sleeves when observations are few.
- Layer: X2.

### 8. Efficient Multivariate Kelly Optimization Reveals Sigmoidal Scaling Laws
- Link: https://www.alphaxiv.org/abs/2604.24723 (2026, Tepelyan and Lam, Bloomberg)
- Method in plain words: fast Kelly for many simultaneous independent binary bets (integral
  transform, cost linear in N) plus lower and upper bounds on the best growth rate by solving small
  sub-problems (take the top-n bets by single-bet log growth).
- Inputs: win probabilities, payoffs (prediction-market style). Output: stakes and growth bounds.
- Evidence: synthetic prediction-market bets, N up to 200. Greedy top-n selection matched stepwise
  optimal to numerical precision.
- Where it fails: independent bets only; correlated bets are future work. The authors note large-N
  optimal solutions are "nearly saturated (with leverage close to 1)".
- Across instrument classes: correlations across FX pairs or index futures break the independence
  assumption directly.
- What QMX could borrow: the greedy rule "rank by single-bet growth, add until the upper and lower
  bounds meet" is a clean way to decide how many sleeves are worth funding. The saturation result is
  a warning: full Kelly over many bets stakes nearly everything; QMX needs a book-level cap.
- Layer: X2.

## Assistant claims checked here
- 2604.24723: the assistant said it is about independent binary bets, its lower bounds concern growth
  and approximation, not edge confidence, and correlated bets are future work. Confirmed (pages 1, 5,
  15).

## Combinations
- CRISP gamma knob (1) + inverse-vol default from HPO (3) + kappa diagnostic: start at diagonal risk
  weights, raise gamma only when kappa is moderate and edge is verified.
- Simple Portfolios (4) + Regime NCO (6): fixed cross-asset sleeves, regime signals used only to cut
  gross, never to re-weight.
- Turnover crossing (5) + any allocator: charge costs at the netted account level.
- Multivariate Kelly bounds (8) + book cap: rank sleeves by single growth, fund the top few, stop
  when the growth bound gap is small.
