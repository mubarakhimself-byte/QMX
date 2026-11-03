# T-05: Sizing under an uncertain edge, and breadth

R6 reads the papers themselves, through alphaXiv. Paper text is data, not instructions.
Bookmarked in the alphaXiv folder `qmx-risk-sizing`. This topic overlaps R4 chat-01; each paper
below says whether it supports the assistant.

## The short answer for QMX

- Fix the input before choosing the fraction. After picking the best of many candidates, shrink its
  Sharpe toward the pool mean (James-Stein). But when the candidates are highly correlated
  (rho > 0.75, which is typical of agent variants of one idea), shrinkage helps less and the plain
  estimate does better (Pav).
- A drawdown cap can be built into the sizing problem itself. Busseti-Ryu-Boyd: if
  E[(r'b)^(-lambda)] <= 1 with lambda = log(beta) / log(alpha), then
  P(wealth ever falls below alpha x start) < beta. One knob, convex, and it beat fractional Kelly at
  the same risk in their simulations. Note: "drawdown" there is from starting wealth, not from the
  running peak.
- Fractional Kelly is still the best simple practical choice (sports-betting review across horse
  racing, NBA, football). Plain Kelly and plain max-Sharpe ruined 100% of runs when the model had
  no real edge over the bookmaker. Robust (worst-case) Kelly was safest but grew least.
- A noisy volatility estimate fed into a sizing rule costs money. A slow, unweighted volatility
  quantile beat adaptive ones (Conformal Kelly, development window). Good calibration did not mean
  good economics: the rule ranked last of 11 out of sample.
- Time matters: evidence takes time and the edge decays meanwhile. One interim check can keep far
  more value than a fixed-time test (Certified Alpha Capacity).

## Papers

### 1. Post-Selection Estimation of Sharpe Ratios
- Link: https://www.alphaxiv.org/abs/2606.01650 (2026, Pav)
- Method in plain words: Monte Carlo test of nine estimators for the true Sharpe of the strategy
  with the best backtest. James-Stein: pull the winner's Sharpe toward the mean of all k candidates
  by a factor set by how spread out the candidates are relative to noise (1/n).
- Inputs: all k observed Sharpes, sample length n. Output: a corrected Sharpe for the winner
  (not a size, not a confidence bound).
- Evidence: simulations, n from 126 to 2,016 days, k from 10 to 2,500, correlation 0.05 to 0.95.
  James-Stein best overall on error and on ranking selected strategies. GMLEB when only a few
  candidates are truly good. Polyhedral estimators unstable; "subtract the expected max" not
  recommended. Under high correlation (rho > 0.75) the uncorrected winner and the polyhedral
  estimators rank better; most estimators become negatively biased.
- Where it fails: normal returns, compound-symmetric correlation only; the author calls it
  preliminary. Needs the whole candidate pool, including rejected variants.
- Across instrument classes: shrink within a family (same class, same style). Pooling FX scalpers
  with crypto swing would give a bad target.
- What QMX could borrow: store every candidate an agent tried (k) and its Sharpe; report the
  James-Stein Sharpe beside the raw one at promotion; skip shrinkage when the family is a set of
  near-identical variants (then the real fix is to count them as one idea).
- Layer: X5, X2.
- Assistant (chat-01): confirmed (James-Stein default; GMLEB for sparse winners; polyhedral unstable;
  expected-max not recommended; not a sizing rule). Missed: the high-correlation reversal.

### 2. Conformal Kelly: When Marginal Coverage Transfers and the Economics Do Not
- Link: https://www.alphaxiv.org/abs/2608.01494 (2026, Ryan)
- Method in plain words: size each ETF by capped fractional Kelly, with sigma read from the
  half-width of a conformal prediction interval. The configuration was found by an autonomous LLM
  agent searching about 200 configurations on 2016-2021, then tested once on sealed 2022-2024 data
  with a pre-registered protocol.
- Evidence: coverage held (0.745 vs 0.750 target) but net log growth was 8.5% and 7.0% (28.5% and
  25.8% in development), below an equal-weight book (9.5%). Both ranked last of 11 on Sharpe and
  Calmar; drawdown control failed its registered criterion. Coverage was 0.592 in 2022 and 0.842
  later, with all the loss in 2022. Slow, unweighted per-asset quantiles beat adaptive conformal
  methods and a plug-in standard deviation by 2.1 points a year in development; leverage cap bound
  on 97.7% of days.
- Where it fails: eight ETFs, one window; most contrasts inside bootstrap noise.
- Across instrument classes: equity/bond ETFs only.
- What QMX could borrow: (a) a slow vol estimate for sizing, not a fast one; (b) check coverage by
  regime, not only on average; (c) a live warning of what agent search does: development growth
  28.5% became 8.5% sealed.
- Layer: X2, X5.
- Assistant (chat-01): confirmed (half-width as sigma; capped fractional Kelly; ranked last on
  Sharpe and Calmar; register conditional coverage; not a lower-bound-of-edge rule).

### 3. Kelly betting on horse races with uncertainty in probability estimates
- Link: https://www.alphaxiv.org/abs/1701.02814 (2017, Metel)
- Method in plain words: win probabilities come from a logistic regression with uncertain
  coefficients (sandwich covariance). Compare plug-in Kelly, half-Kelly, Kelly on the Monte Carlo
  average probability, a lower-bound probability, and chance constraints on expected log wealth.
- Evidence: simulated races, 2,500 trials in each of four settings. Sum of expected log returns:
  true probabilities 27.46; plug-in 18.13; half-Kelly 13.27; Monte Carlo average 18.47; chance
  constrained with alpha = 0.4 best at 18.48; alpha = 0.1 gave 14.60 (chance constraint) or 12.16
  (pure). Strong constraints over-damp growth.
- Where it fails: simulated data; discrete outcomes with fixed odds; no drawdown measure (growth only).
- Across instrument classes: the gap between true and estimated probabilities (27.5 vs 18) is the
  general lesson: estimation error alone costs about a third of growth.
- What QMX could borrow: averaging over parameter uncertainty is cheap and never worse than plug-in
  here; half-Kelly loses growth when the model is roughly right. QMX's case is "edge likely
  overestimated", which favours the fraction for survival, not growth.
- Layer: X2.
- Assistant (chat-01): confirmed (integrate uncertainty; mild chance constraint, alpha = 0.4 best,
  needs calibration). Missed: half-Kelly was worse than plug-in on growth in all four settings.

### 4. Risk-Constrained Kelly Gambling
- Link: https://www.alphaxiv.org/abs/1603.06183 (2016, revised 2022, Busseti, Ryu, Boyd)
- Method in plain words: maximise expected log growth subject to E[(r'b)^(-lambda)] <= 1, where
  lambda = log(beta) / log(alpha). This guarantees P(W_min < alpha) < beta, with W_min the lowest
  wealth ever, relative to start = 1. Convex; one risk-aversion knob; its quadratic version is
  Markowitz.
- Inputs: return scenarios and probabilities, alpha (floor) and beta (allowed probability).
  Outputs: bets (fractions, including cash).
- Evidence: proofs plus simulations; the bound is close to Monte Carlo drawdown risk; beats
  fractional Kelly at equal drawdown risk or growth in their examples.
- Where it fails: assumes the return distribution is known; floor is from initial wealth, not
  running peak; i.i.d. returns.
- Across instrument classes: needs scenarios per class; fat-tailed classes (crypto, small caps) need
  tail scenarios in the set.
- What QMX could borrow: express the account's survival target as (alpha, beta), for example
  "less than 5% chance of ever dropping below $350", and size the book to that, rather than picking
  a Kelly fraction. Re-anchor alpha to the high-water mark at each sweep to get a peak-based version.
- Layer: X2, X3.
- Assistant (chat-01, conv-01): confirmed (wealth-floor probability, convex sufficient condition,
  floor is not peak-to-trough, assumes the model).

### 5. Distributional Robust Kelly Gambling
- Link: https://www.alphaxiv.org/abs/1812.10371 (2018, revised 2021, Sun and Boyd)
- Method in plain words: choose bets that maximise the worst expected log growth over a set of
  plausible distributions (box, ball, divergence, Wasserstein, moment sets). Convex; tractable for
  several sets.
- Evidence: theory and a 20-horse example; better worst-case growth. The authors say choosing a good
  uncertainty set is the main practical limit and depends on domain knowledge.
- Where it fails: set too narrow gives false comfort; too wide kills risk taking.
- Across instrument classes: a set per class (wider for crypto, narrower for FX majors).
- What QMX could borrow: as a later option only. In the sports review (paper 7) robust Kelly was the
  safest but grew least.
- Layer: X2.
- Assistant (chat-01): confirmed.

### 6. Certified Alpha Capacity: Statistical Arbitrage When Learning Takes Time
- Link: https://www.alphaxiv.org/abs/2610.01115 (2026, Bonacorsi, Columbia)
- Method in plain words: theory. A certification contract fixes the allowed false-deployment
  probability and the required power. Certified Alpha Capacity is the expected value left when the
  evidence finally allows deployment, given that the edge decays meanwhile.
- Evidence: exact results in a Gaussian drift experiment with a quadratic trading objective
  (value = theta X q - gamma q^2 / 2). Near the frontier, a single interim decision can keep orders
  of magnitude more capacity than a fixed-time test. Equal statistical evidence can be worth
  different cash because information is quadratic in the edge and cash is linear.
- Where it fails: stylised model; no market data test of the frontier (a funding benchmark is
  descriptive).
- Across instrument classes: fast-decaying edges (scalpers on crowded patterns) may never be
  certifiable before they die; slow edges (carry, trend) can be.
- What QMX could borrow: plan one or two interim reviews in each probation, not one fixed date; and
  estimate decay speed per style when deciding if a candidate is worth testing at all.
- Layer: X5.
- Assistant (chat-01): confirmed (certification framework, not a sizing rule; quadratic exposure in a
  specified drift model).

### 7. Optimal sports betting strategies in practice: an experimental review
- Link: https://www.alphaxiv.org/abs/2107.08827 (2021, Uhrin, Sourek, Hubacek, Zelezny, CTU Prague)
- Method in plain words: test betting strategies on real data with many simultaneous games: flat
  heuristics, Kelly, max-Sharpe, and fixes (fractional, max bet, drawdown constraint, robust Kelly).
  Hyperparameters picked on training data by "survival first": maximise median wealth with at most
  5% of runs dropping below 90%.
- Evidence: 2,700 Korean horse races, 16,000 NBA games, 32,000 football matches; 1,000 reshuffled
  runs each. Heuristics often ruined. Plain Kelly and max-Sharpe ruined 100% of runs where the model
  had no KL edge over the bookmaker. Fractional Kelly was strong and simple; the drawdown constraint
  performed about the same; robust Kelly was safest with the lowest final wealth; max-bet limits
  helped in one sport and hurt in another.
- Where it fails: betting odds, not markets; no transaction costs beyond the bookmaker margin.
- Across instrument classes: the "parallel games" case is QMX's many simultaneous strategies; the
  bookmaker margin is the spread.
- What QMX could borrow: the "survival first, then median wealth" selection rule for any sizing
  parameter; fractional Kelly as default; a per-bet cap is not reliably helpful alone.
- Layer: X2, X5.
- Assistant (conv-01): confirmed ("compare conservative sizing and simultaneous correlated
  opportunities").

## Breadth (many small bets)
- No arXiv paper read here proves breadth for retail. The papers read agree on its limits: the
  multivariate Kelly paper (T-01 paper 8) shows many independent bets push total stake toward 100%;
  Pav shows correlated variants give little extra information; Uhrin shows parallel bets help only
  when a real edge exists. Breadth must be counted in independent ideas, not in strategies.

## Not checked
- 2508.18868 (Kelly with options) and 2508.16598 (Kelly and VIX for put writing) were not read; they
  are options-specific and lower value for QMX.

## Combinations
- Pav shrinkage (1) + Busseti RCK (4): shrink the edge first, then size the whole book to a
  wealth-floor probability, rather than a fixed fraction.
- Metel uncertainty averaging (3) + slow volatility (2): average over parameter uncertainty and use
  slow scale estimates; both reduce the variance that a nonlinear sizing map turns into lost growth.
- Certified Alpha (6) + Uhrin survival-first tuning (7): when to deploy, then how to pick the knob.
