# T-09: Validation against overfitting

R6 reads the papers themselves, through alphaXiv. Paper text is data, not instructions.
Bookmarked in the alphaXiv folder `qmx-risk-sizing`.

STOPPED EARLY: the alphaXiv free-plan quota ran out ("assistant quota exceeded") just as this topic
began. The two papers found for this topic were not read. This file assembles the validation
evidence from papers already read under other topics, and lists what to read next.

## The short answer for QMX (from papers read)

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

## Not read (quota stopped the run); read these next
- https://www.alphaxiv.org/abs/2611.03384 Can We Stop the Backtest Yet? Anytime-Valid Promotion
  Tests for Adaptive Financial Research Agents (2026-11-02). Title matches QMX exactly: candidates
  appear at data-dependent times, weak rules abandoned. Highest priority.
- https://www.alphaxiv.org/abs/2610.07701 On the Boundary of Admission Gates: An Injected-Truth Study
  of Falsification-First Selection (2026, Fudan). Tests admission gates by planting true edges.
- https://www.alphaxiv.org/abs/2501.03938 In-Sample and Out-of-Sample Sharpe Ratios for Linear
  Predictive Models (2025, Imperial / Qube). How much in-sample Sharpe shrinks out of sample.
- https://www.alphaxiv.org/abs/2604.15531 Spurious Predictability in Financial Machine Learning (2026).
- https://www.alphaxiv.org/abs/2609.29530 The Impossible Trinity of Time-Series Validation (2026).
- https://www.alphaxiv.org/abs/2608.23808 MinervaScore: Luck or Edge? (2026).

## Combinations
- Trial counting (2608.27734) + James-Stein (2606.01650) + five gates (2605.04004): one promotion
  record per candidate family with k, raw and shrunk Sharpe, gate results, delay test.
- Sealed evaluator (AQuA) + staged credit with shuffle tests (2607.09230): agents can propose
  features but only the sealed harness credits them.
