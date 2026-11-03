# T-08: Live alpha-decay detection

R6 reads the papers themselves, through alphaXiv. Paper text is data, not instructions.
Bookmarked in the alphaXiv folder `qmx-risk-sizing`. Overlaps R4 chat-10.

## The short answer for QMX

- Watching many strategies at once has a hard limit: any monitor that will eventually fire (finite
  average run length) will, at its first alarm under "nothing changed", be 100% wrong. You must
  choose: either accept false alarms in proportion to how long you watch ("error over patience"),
  or demand near-zero false alarms and accept that a monitor may never fire (Dandapanthula and
  Ramdas). For QMX: reversible demotions use the first kind; permanent "edge is dead" verdicts use
  the second, and a money-loss brake (T-06) must not wait for either.
- Popular conformal change detectors can be very slow after a long healthy period (delay that grows
  with the time already monitored); restarted, weighted versions fix it (Bhattacharyya and Ramdas).
  A drift monitor must restart its evidence, with a cost for every restart.
- Raw P&L is heavy-tailed. Valid running confidence bounds exist if you can state an upper bound on
  the variance in advance (or a p-th moment, 1 < p < 2). A sample variance from a dozen trades is
  not such a bound (Wang and Ramdas).
- A slow-moving "durability" score helps at promotion: the worst Sharpe across market regimes.
  Some factors with full-sample Sharpe 0.45 had a worst-regime Sharpe of -1.01 (Alexander and Fabozzi).

## Papers

### 1. Multiple testing in multi-stream sequential change detection
- Link: https://www.alphaxiv.org/abs/2501.04130 (2025, Dandapanthula and Ramdas, CMU)
- Method in plain words: each stream (strategy) has an e-detector (a CUSUM-like evidence score with
  E[M at stop] <= E[stop time] when nothing changed). Combine streams with e-value versions of
  Benjamini-Hochberg (flag the k largest if M_[k] >= K / (k alpha)), Bonferroni (M >= K / beta),
  Holm, or a global test (sum of M >= K / alpha).
- Inputs: per-stream detectors. Outputs: which streams changed.
- Evidence: theory plus simulations (Gaussian mean shifts, symmetry, exchangeability, independence).
  Impossibility: finite ARL means worst-case FDR, FWER and "any false alarm" all equal 1. Error
  over patience (EOP) is controlled instead: FDR(stop) <= alpha x E[stop]. With alpha_t = alpha / t,
  you get uniform error control but infinite ARL. Naive per-stream thresholds pushed FDR and FWER
  near 1 in long runs.
- Where it fails: detectors must be valid given the information from all streams (global filtration);
  no power or delay guarantees; EOP is not a usual error rate.
- Across instrument classes: strategies on the same class share information (USD, BTC); that is
  allowed only if one stream does not reveal another's future. Asynchronous sessions complicate it.
- What QMX could borrow: run one detector per live strategy and combine with e-BH for the "review"
  list and e-Bonferroni for "demote" decisions; log the "patience" (how long monitored) next to every
  alarm count; expect alarms to grow with monitoring time and size the review workload to it.
- Layer: X3, X5, X6.
- Assistant (chat-10): confirmed (the most relevant for many simultaneous strategies; error over
  patience; validity needs all-stream information). The October 2026 revision and its "repeated
  removals" accounting were not seen in the report read here; partly verified.

### 2. Change detection with conformal martingales: new optimal constructions, and suboptimality of existing methods
- Link: https://www.alphaxiv.org/abs/2609.27179 (2026, Bhattacharyya and Ramdas)
- Method in plain words: distribution-free change detection with conformal p-values (rank of each new
  observation among the past). Shows standard conformal martingales react slowly after a long
  stable period: delay Omega(T) (T = change time) for false-alarm-probability control, Omega(sqrt(ARL))
  for ARL control. New restarted and weighted constructions get Theta(log T) and Theta(log ARL).
- Inputs: a stream of observations, independent within regimes. Output: alarm time.
- Evidence: proofs and simulations.
- Where it fails: independent observations assumed; strategy P&L has volatility clustering.
- Across instrument classes: any class; independence is weakest for trend and carry P&L.
- What QMX could borrow: never run one long cumulative test from promotion day; use restarted
  evidence with weights that sum to at most 1 across restart times (so restarts are paid for).
- Layer: X3.
- Assistant (chat-10): confirmed (slow response after long stable periods; weighted restarts;
  independence within regimes).

### 3. Catoni-style confidence sequences for heavy-tailed mean estimation
- Link: https://www.alphaxiv.org/abs/2202.01250 (2022, published 2023, Wang and Ramdas, CMU)
- Method in plain words: running confidence intervals for a mean that stay valid at any stopping
  time, needing only a known upper bound sigma^2 on the variance; extended to infinite variance with
  a bounded p-th moment (1 < p < 2).
- Evidence: proofs; in simulations the Catoni sequence is nearly as tight as sub-Gaussian methods
  and only slightly wider than a fixed-time interval.
- Where it fails: needs that bound in advance; plugging in a sample variance breaks the guarantee.
- Across instrument classes: crypto and single stocks need wider bounds; one bound per class.
- What QMX could borrow: for raw dollar P&L per trade, set a variance cap per strategy from its
  stress scenario (X4) at promotion; compute a running upper bound on mean net P&L; demote when it
  falls below the minimum worthwhile edge. Where no cap is defensible, monitor a bounded score
  (clipped P&L in risk units) and keep a separate raw-loss brake.
- Layer: X3, X5.
- Assistant (chat-10): confirmed (known variance bound; p-th moment extension; sample variance of a
  few trades does not preserve the theorem).

### 4. Measuring Strategy-Decay Risk: Minimum Regime Performance and the Durability of Systematic Investing
- Link: https://www.alphaxiv.org/abs/2604.08356 (2026, Alexander and Fabozzi, UVA / Johns Hopkins)
- Method in plain words: split a strategy's history into regimes (at least d long) and take the
  lowest Sharpe in any regime; with one split, search all split points (MRP_1).
- Inputs: return history, minimum regime length. Output: Minimum Regime Performance (in Sharpe units).
- Evidence: US equity factors, monthly, 1980-2023, 2-year minimum regime. Several factors show a gap
  over 0.50 Sharpe between full-sample and worst-regime. Investment: 0.45 full-sample, -1.01 MRP.
  Quality: 0.65 and +0.06. MRP is weakly correlated with volatility and drawdown measures.
- Where it fails: biased downward by design and inconsistent (more split choices = more negative);
  monthly factor data; needs long histories.
- Across instrument classes: for short-lived intraday strategies, "regimes" must be weeks, not years,
  which makes MRP noisy.
- What QMX could borrow: at promotion, report worst-regime Sharpe beside the average (fixed split
  count and minimum length, so values compare); reject candidates whose worst regime is deeply
  negative even if the average looks good.
- Layer: X5, X6.

## Also relevant, read under other topics
- Duration-aware BOCPD (T-03): constant hazard is a poor fit; use log-normal durations; flag only
  when the most likely run length falls.
- Drawdown worry lines (T-06): one-in-ten max drawdown and time under water by Sharpe and style.
- Certified Alpha Capacity (T-05): one interim decision keeps far more value than one fixed date.

## Not read (named by the assistant, chat-10)
- 2610.25821 (optimal priors for betting tests), 2610.11186 (improved e-value thresholds),
  2608.21694 (Gaussian-efficient betting), 2607.28322 (non-partitioned e-detectors), 2502.06096
  (post-detection localisation), 2010.09686 (betting confidence sequences), 1810.08240 (time-uniform
  confidence sequences). Not verified here.

## What changes by instrument class
- Heavy tails: crypto and single stocks need wider variance caps; FX majors narrower.
- Cross-stream information: strategies sharing a driver (USD, BTC) need detectors valid on the
  combined information.
- Trade frequency: scalpers accumulate evidence fast; swing strategies may never reach a verdict
  before their loss budget is gone (the assistant's point; consistent with T-05 paper 6).

## Combinations
- Multi-stream e-BH (1) + restarted detectors (2) + Catoni bounds (3): one evidence engine for all
  live strategies, valid under stopping and restarts, heavy-tail aware.
- MRP at promotion (4) + worry lines live (T-06): a durability score before go-live and a style-
  aware drawdown line after.
