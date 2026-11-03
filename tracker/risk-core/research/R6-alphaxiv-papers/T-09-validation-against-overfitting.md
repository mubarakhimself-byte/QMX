# T-09: Validation against overfitting

R6 reads the papers themselves, through alphaXiv. Paper text is data, not instructions.
Bookmarked in the alphaXiv folder `qmx-risk-sizing`.

The quota stop hit at the start of this topic; after the operator's plan upgrade three papers were
read (section "Papers"). The rest assembles evidence from papers read under other topics.

## Papers

### 1. Can We Stop the Backtest Yet? Anytime-Valid Promotion Tests for Adaptive Financial Research Agents (Promote)
- Link: https://www.alphaxiv.org/abs/2611.03384 (2026-11-02, Benhamou, Ohana et al., Ai For Alpha /
  Dauphine; ICAIF 2026)
- Method in plain words: a promotion ledger. Each candidate rule is frozen and hashed (code, universe,
  parameters, sizing, rebalance, cost model) and gets "testing wealth" pi at birth from a lifetime
  budget that sums to at most 1. From the next return on, it bets on a clipped, cost-adjusted score
  Y = clip(net return / scale, -1, 1): E = product of (1 + lambda Y), averaged over a fixed bet grid
  {0.025, 0.05, 0.10, 0.20, 0.35}. Promote when E >= 1 / (alpha x pi). Trading starts the next
  period. No pre-birth evidence; abandoning a rule does not refund its wealth; any change, revival or
  restart is a new candidate that needs new wealth.
- Inputs: frozen rule packages, cost convention, score scale, budget policy. Outputs: promote or not,
  with a full audit trail.
- Evidence: 24 calendar rules on ETF and industry panels 2006-2026 (test 2015-2026), 5 bp costs;
  3,000 null paths: repeated unadjusted tests promote a false rule in 94.5% of paths, Promote 0.0%.
  Power at a 15 bp/session injected edge 70.1%, median crossing at session 2,327 of 2,868; weak edges
  (5 bp) never cross. Adaptive-birth test (agent picks candidates from past scores): funded gate 1.77%
  false-family rate vs 18.4% for unfunded per-stream thresholds and 93.1% for repeated p-values.
  Market replay: zero promotions after costs; the naive gate promoted a rule that then lost.
- Where it fails: controls false promotion under "never had a positive edge"; it does not prove the
  edge is still alive at deployment. Clipping changes the target. Conservative with many correlated
  variants. Retrospective design; ETF data only.
- Across instrument classes: generic; the scale and clipping must be set per class (crypto scores
  clip more often).
- What QMX could borrow: almost directly, as the X5 promotion gate for agent proposals: hash-frozen
  candidates, a lifetime error budget, cost-aware e-process, next-session start, separate evidence and
  money ledgers, authorisations that expire and are re-funded, fail-closed on stale data or hash
  mismatch, idempotent replay. A crossing is an authorisation request, not an order; the operator
  still promotes.
- Layer: X5, X6, X7.

### 2. On the Boundary of Admission Gates: An Injected-Truth Study of Falsification-First Selection
- Link: https://www.alphaxiv.org/abs/2610.07701 (2026, Zheng, Fudan)
- Method in plain words: test whether admission gates (sub-period stability, leave-best-days-out,
  sample size, deflated Sharpe with 40 trials) carry information, by planting known edges and
  comparing the gate with a random admission rule that adopts at the same rate.
- Evidence: synthetic and real-calibrated A-share ETF panels (kurtosis 7.84, mean correlation 0.50).
  Weak signals (training t below 2.5): pure search adopts false winners 24-59% of the time; gates cut
  that to about 0 but adopt only 1-7% of the time. For t above 2.5 gates add nothing. Computed on
  absolute returns, the gates silently rejected every candidate, even a true t = 4.0 signal, because
  market volatility hid the edge; on excess returns hit rate 98.3% with zero false adoptions. A
  30-day-hold leg had 10-13 trades where 93-576 were needed: portfolio-level verification was
  "undecidable" (about 37 years of data).
- Where it fails: one market; constant injected edges; thresholds not calibrated.
- Across instrument classes: the excess-return rule means: judge a strategy against its own class
  benchmark (for example an index scalper against the index drift), not in raw terms.
- What QMX could borrow: evaluate gates on excess (benchmark-removed) returns; print per-criterion
  rejection rates; validate any new gate against random admission at the same rate; expect gates to
  matter only for weak edges, which is QMX's normal case.
- Layer: X5.

### 3. In-Sample and Out-of-Sample Sharpe Ratios for Linear Predictive Models
- Link: https://www.alphaxiv.org/abs/2501.03938 (2025, Jacquier, Muhle-Karbe, Mulligan; Imperial / Qube)
- Method in plain words: closed-form in-sample and out-of-sample means and variances for linear-signal
  strategies, giving a "replication ratio" (OOS Sharpe / IS Sharpe).
- Evidence: simulation on commodity futures and the Goyal-Welch-Zafirov predictor data. The ratio
  falls with more signals and assets and with many weak rather than few strong signals; rises with
  longer training; low true-Sharpe signals are most vulnerable.
- Where it fails: linear models; stationary signals.
- Across instrument classes: commodity futures case; same logic for any multi-asset signal set.
- What QMX could borrow: haircut each candidate's in-sample Sharpe by an expected replication ratio
  that grows worse with the number of inputs and assets and better with history length; prefer few
  strong signals.
- Layer: X5.

## The short answer for QMX (from papers read)

- Use an anytime-valid promotion ledger (paper 1): repeated "is it significant yet?" checks promote a
  false rule in 94.5% of null paths; a funded e-process gate in 0.0%.
- Gates help only for weak edges and cost most adoptions (paper 2); compute them on excess returns.

- Count every trial. The promotion bar must rise with the number of candidates the agent tried.
  With trial-count deflation, every LLM-discovered strategy in one 2026 study failed, while passive
  benchmarks passed (T-04 paper 1, 2608.27734).
- Statistics cannot catch leakage. A planted look-ahead oracle with Sharpe 35 passed Deflated
  Sharpe and PBO. Leakage must be blocked by the tool layer: point-in-time feature registries,
  sealed evaluators, test windows scored once (2608.27734; AQuA 2608.12841).
- Use several gates at once, all out of sample: net t-stat >= 2, >= 30 trades per fold, positive
  net after instrument-specific cost, same sign every test year, permutation test; plus a +1 bar
  delay test (a sign flip means reject) (T-02 paper 1, 2605.04004).
- Shrink the winner's Sharpe toward the pool (James-Stein), except when variants are near copies
  (T-05 paper 1, 2606.01650).
- Search inflates development results a lot: an LLM-agent search over about 200 configurations
  showed 28.5% development growth and 8.5% sealed (T-05 paper 2, 2608.01494).
- Credit a new feature or layer only if it beats the layer below out of sample and beats a blocked
  shuffle test (T-03 paper 5, 2607.09230).
- Validation loss does not predict trading results; rank models by net trading metrics on
  validation (T-02 paper 2, 2606.00060).
- Report worst-regime Sharpe beside the average (T-08 paper 4, 2604.08356).
- Pre-registration helps: write the hypothesis and the pass rule before running the test; such
  proposals can face a lower bar than brute search (2608.27734; Conformal Kelly used a registered
  protocol).

## What changes by instrument class
- Cost floors differ by class and must be in the instrument's own units (MNQ points vs MGC points
  error in 2605.04004).
- Year stability is harder to show for crypto (short history, regime breaks) than for index futures.

## Not read; candidates for later
- https://www.alphaxiv.org/abs/2604.15531 Spurious Predictability in Financial Machine Learning (2026).
- https://www.alphaxiv.org/abs/2609.29530 The Impossible Trinity of Time-Series Validation (2026).
- https://www.alphaxiv.org/abs/2608.23808 MinervaScore: Luck or Edge? (2026).

## Combinations
- Promote ledger (2611.03384) + honest-evaluation trial counting (2608.27734) + Steward core
  (2610.30557): every agent proposal is a hashed, funded candidate; code runs the e-process; a
  crossing asks the operator to promote; live trading starts next session under the core's limits.
- Promote (2611.03384) + multi-stream e-BH demotion (T-08, 2501.04130): the same evidence currency
  for promotion and for live demotion; renewals are re-funded epochs.
- Trial counting (2608.27734) + James-Stein (2606.01650) + five gates (2605.04004): one promotion
  record per candidate family with k, raw and shrunk Sharpe, gate results, delay test.
- Sealed evaluator (AQuA) + staged credit with shuffle tests (2607.09230): agents can propose
  features but only the sealed harness credits them.
