---
ticket: academic-enhancements
title: Academic and practitioner work that strengthens QML, the MIS and the unit
date: 2026-10-24
author: opus research agent (read-only; this file is the only write)
method: Exa search and fetch of primary pages (arXiv, SSRN, journal pages, authors' PDFs), read on 2026-10-24. Firecrawl not used. Built on 01-ground-truth, 02-instruments-and-traders, 03-strategyquant and seeds.md; their findings are cited, not repeated.
labels: CHECKED (URL) = read on that page today. PRACTITIONER = a trader, vendor or forum report, not peer-reviewed. INFERRED = my reasoning, arithmetic or proposal.
numbers: every number below is a starting point or a worked example. In QMX each is a configurable, UI-editable value, never a baked default.
---

# 05: Academic enhancements for the MIS router, the registry and the unit

## How to read this

- One section per ticket question (1-8). Each section gives: the best methods, the evidence, how fast and robust they are, how they fail, and **where they plug into QMX** (the named part they touch).
- QMX paths use the aliases from `01-ground-truth.md` (`EB` = engine/base `f05fc64b`). "Seeds" = `workroom/risk-lab-2026-10-05/seeds.md`. "Decisions" = `decisions.md` beside it.
- The scalper lens comes first: 1-minute and 5-minute bars, many small trades, costs that decide the edge, a small account (starting money $300 in decisions.md).

## Short answer

1. **No detector can beat an information limit.** For any change detector with a given false-alarm rate, the fastest possible average delay is about ln(false-alarm spacing) ÷ (information per bar) (Lorden's bound; CUSUM reaches it). CHECKED: https://doi.org/10.18880/0000002821 , https://ar5iv.labs.arxiv.org/html/1310.3285 . BOCPD, HMMs and Kalman filters cannot get under it. Speed comes from more information per bar, not from a cleverer model. INFERRED.
2. **At 1m, a volatility jump is detectable in minutes; a trend is not detectable in hours.** Worked numbers (§1.3, INFERRED from the bound): a 1.5× vol jump takes about 44 bars (44 minutes on 1m, 3 hours on 5m); a strong new drift takes about 480 bars (8 hours on 1m). So a scalper router should run on volatility, spread, liquidity and cost states. Trend/range labels at these horizons describe the past.
3. **Most of a scalper MIS is "now versus the usual for this time of day".** Intraday seasonality dominates high-frequency volatility and must be removed before any change test. CHECKED (Andersen & Bollerslev 1997): https://public.econ.duke.edu/~boller/Published_Papers/joef_97.pdf . SQS already works this way for spread. Generalising its seasonal baseline to volatility, tick rate, depth and cost gives near-zero-lag states. INFERRED.
4. **Meta-labeling is the formal version of "the MIS is a router outside the bot".** The bot proposes; a secondary model, trained on that bot's own trades and the market state at entry, decides take/skip/size. CHECKED (López de Prado): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3104816 . It keeps the rule that bots never read the MIS. INFERRED.
5. **Statistics catch decay slowly; loss limits must catch bleeding.** Detecting a 0.1R edge going to zero takes about 1,400 trades at one false alarm per 1,000 trades (§4.6, INFERRED from the bound). That supports the split in decisions.md: fast bleeding control by loss points, slow decay detection by statistics.
6. **"Tighten, never loosen" belongs on the floor, not on the estimates.** Grossman-Zhou's optimal drawdown policy risks in proportion to the cushion above a floor that rises with the high-water mark. CHECKED: https://doi.org/10.1111/j.1467-9965.1993.tb00044.x . A one-way ratchet on noisy edge estimates drifts to the minimum size over time. INFERRED. Loosening needs its own evidence gate.
7. **Anti-martingale sizing (house money, reverse house money) only helps if the unit's own returns are serially correlated.** CHECKED (Kaminski & Lo 2014): https://www.sciencedirect.com/science/article/abs/pii/S138641811300030X . Measure the autocorrelation of each unit's record before switching it on. INFERRED.
8. **Kelly at QMX's kill line:** with a known edge, P(ever falling to 60% of the bankroll) is 60% at full Kelly, 22% at half Kelly and 3% at quarter Kelly. CHECKED formula: https://condor.depaul.edu/~wchin/riskpaper.pdf ; numbers INFERRED. Estimation error makes it worse. CHECKED (Baker & McHale): https://doi.org/10.1287/deca.2013.0271 .
9. **Backtest Sharpe barely predicts live Sharpe.** On 888 Quantopian algorithms R² < 0.025, and more backtesting meant a bigger gap. Volatility and max drawdown predicted better. CHECKED: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2745220 . A rule that passed White's Reality Check still failed out of sample over 1987-1996. CHECKED: https://www.kevinsheppard.com/files/teaching/mfe/advanced-econometrics/Sullivan_Timmermann_White.pdf . No single test predicts survival well enough. QMX has to measure each gate's lift (03 H1).
10. **Domain expansion is online multiple testing.** Every new cell is one more hypothesis in a stream. Alpha-investing and LORD spend error budget per test and earn it back on discoveries, which matches "expand only from a parent that passed". CHECKED: https://doi.org/10.1214/17-aos1559 . E-values allow watching the evidence after every trade and stopping at any time without breaking the error rate. CHECKED: https://arxiv.org/abs/2210.01948 .
11. **Most cells will be too thin, so cells must borrow strength.** An edge of 0.1R per trade needs about 270 trades for 95% confidence; a skewed 70%-win scalper needs about 550 (§2.4, INFERRED via MinTRL, CHECKED: https://www.davidhbailey.com/dhbpapers/sharpe-frontier.pdf ). Shrink each cell toward its parent (empirical Bayes). CHECKED (Efron & Morris 1975): https://faculty.chicagobooth.edu/nicholas.polson/teaching/41900/efron-morris1.pdf .
12. **Two missing data fields block most of this.** QMB stores results in money, not R, and attaches no MIS label to backtest trades. CHECKED in `01-ground-truth.md` §1.3, §7.9. Both are prerequisites for §2, §4, §6 and §7.

---

## 1. Market state for a router, fast enough for scalpers

### 1.1 Methods, from fastest to slowest

| Tier | What | Lag | Evidence |
|---|---|---|---|
| T0 facts | Market hours, news windows, feed alive, gap event | Zero (calendar or event) | Already in the node: identity, gap-event, feed-state labelers. CHECKED (`01` §1.5) |
| T1 seasonal ratios | Live value ÷ seasonal normal for this instrument and time of week: spread (SQS), realised volatility, tick rate, top-of-book depth, cost ÷ unit target | Only the smoothing window (seconds to a few minutes) | Intraday periodicity dominates high-frequency volatility in FX and equities; ignoring it distorts every volatility model. CHECKED: https://public.econ.duke.edu/~boller/Published_Papers/joef_97.pdf . Session structure per class: 02 §2.2, §8.3 (S47, S51-S53) |
| T1 microstructure | OFI, queue (depth) imbalance | One to a few ticks | OFI explains 65% of short-interval mid-price changes, linear, slope ∝ 1/depth. It explains the same interval and is not a long-horizon forecast. CHECKED: https://arxiv.org/html/1011.6402v3 . Queue imbalance predicts the next mid move: +50-60% binary accuracy over the null for large-tick stocks, +10-30% for small-tick stocks, out of sample. CHECKED: https://arxiv.org/html/1512.03492 |
| T2 change-point flag | CUSUM or BOCPD on deseasonalised volatility | Minutes at 1m (table §1.3) | BOCPD: exact online run-length posterior, cost about the expected run length per step with pruning. CHECKED: https://arxiv.org/abs/0710.3742 . Standard BOCPD false-alarms on outliers: over 90% false discovery rate on the well-log data. The robust β-divergence version reduces it to 0%. CHECKED: https://arxiv.org/abs/1806.02261 |
| T3 regime label | Statistical jump model or HMM on 5m/1h features | Hours to weeks | Jump models flip far less often than HMMs (fewer than 1 vs about 2-8 shifts a year on daily data). They detect a crash about half a month late; Nystrup et al. report a 25-day median latency. CHECKED: https://arxiv.org/html/2402.05272v3 . Only one research network supports this, and the penalty was tuned on the evaluated strategy. PRACTITIONER review: https://www.signaltrace.wiki/markov-model/Models/Statistical-Jump-Model |
| T3 vol forecast | EWMA, HAR-RV (day/week/month components) | Daily-scale | HAR-RV is simple, captures long memory, forecasts well. CHECKED: https://doi.org/10.1093/jjfinec/nbp001 |
| Noise gauge | Variance ratio / Kalman gain / efficiency ratio | Slow (same information problem as a trend, §1.3) | The variance-ratio test compares variance across sampling frequencies. CHECKED: https://doi.org/10.1093/rfs/1.1.41 . Kalman gain: see §1.4 |

### 1.2 What not to use

- **VPIN.** It predicts short-run volatility poorly, peaked after the flash crash rather than before it, and its signal is mostly a mechanical tie to trading intensity. CHECKED (Andersen & Bondarenko 2014): https://www.sciencedirect.com/science/article/abs/pii/S1386418113000189 .
- **Raw-return HMMs at 1m without deseasonalising.** They will "discover" the London open every day. INFERRED from Andersen & Bollerslev.
- **Regime labels as entry filters for scalpers.** By the time a trend is "confirmed" (§1.3), a scalper's holding period has passed many times. INFERRED.

### 1.3 Detection lag at 1m and 5m (worked from the bound)

Method: CUSUM delay ≈ ln(ARL) ÷ KL, where ARL is the mean spacing between false alarms and KL is the information per bar. Lorden showed no stopping rule with that false-alarm spacing can do better asymptotically. CHECKED (bound and its "minimum over all stopping times" scope): https://doi.org/10.18880/0000002821 . The numbers are INFERRED arithmetic with Gaussian bars and an assumed false-alarm spacing of about 10 trading days of 24-hour FX (14,400 bars on 1m, 2,880 on 5m). Fat tails and estimating the post-change level make real delays longer.

| Change in deseasonalised returns | KL per bar | 1m delay | 5m delay |
|---|---|---|---|
| Vol ×2 | 0.81 | ~12 bars = 12 min | ~10 bars = 50 min |
| Vol ×1.5 | 0.22 | ~44 bars = 44 min | ~36 bars = 3 h |
| Vol ×1.25 | 0.058 | ~165 bars = 2.7 h | ~137 bars = 11 h |
| Vol halves | 0.32 | ~30 bars = 30 min | ~25 bars = 2 h |
| New drift 0.2σ per bar (a strong trend) | 0.02 | ~480 bars = 8 h | ~400 bars = 33 h |
| New drift 0.1σ per bar | 0.005 | ~1,900 bars = 32 h | ~1,600 bars = 5.5 days |

What this means for QMX (INFERRED):
- **Volatility and liquidity states are fast; direction states are not.** Spread, tick rate and depth are observed directly, so their lag is only the smoothing window.
- **More information per bar is the only real speed-up.** The high-low range estimator needs about 5× fewer observations than close-to-close for the same accuracy. CHECKED (Parkinson 1980): https://www.cmegroup.com/trading/fx/files/michael_parkinson.pdf . Tick-level realised variance carries more again (roughly the tick count per bar, minus microstructure noise). INFERRED. So the T2 change flag should read ticks or ranges, not 1m closes. That cuts the vol ×1.5 delay from about 44 bars to single digits. INFERRED.
- **Expect BOCPD to sit at or above these delays.** It does not know the post-change level, and the bound applies to every detector. INFERRED.

### 1.4 Kalman gain as a noise gauge

- In a local-level model, the steady-state gain is K = (−q + √(q² + 4q)) ÷ 2, where q is the signal-to-noise variance ratio. A Kalman filter in steady state is an EWMA with α = K. INFERRED (standard state-space algebra).
- A high gain means price moves are mostly signal (trend-like). A low gain means mostly noise (range-like).
- Estimating q online is the same information problem as detecting drift (§1.3), so the gain moves slowly. It is a fine descriptive feature (a smoothed variance ratio) and a poor fast detector. INFERRED.

### 1.5 Failure modes

- Seasonal baselines go stale around daylight-saving shifts, holidays and rollover. Key them per instrument per venue schedule; the calendars are missing outside forex (01 §3.2). INFERRED.
- OFI needs depth updates. cTrader has L2 depth but no trade tape, so OFI works there but trade-delta does not. CHECKED in 02 short answer 5.
- Change-point detectors false-alarm on single spikes unless made robust. CHECKED (Knoblauch et al. above).
- Regime models fit on one period re-label the past when refit. Store labels as computed at the time. INFERRED.

### 1.6 Where it plugs into QMX

- **`qmn/mis/` labelers** (`EB qmn/src/qmn/mis/labelers.py`). Add T1 ratio labelers beside spread-state and SQS. Add the T2 change flag through the existing shadow lane (`shadow.py`), where BOCPD already sits as a candidate without authority (DEC-0262). INFERRED.
- **One "seasonal baseline" component.** SQS already keeps a baseline keyed (venue, environment, instrument) per session window (CHECKED `01` §1.5). Make that baseline generic so volatility, tick rate, depth and cost ratios reuse it. INFERRED.
- **`qmf-indicators`.** ATR, VWAP and session range are named but not runnable (CHECKED `01` §1.1). The range estimator and the T1 ratios need them.
- **QMB.** Compute the same labels on backtest bars and stamp them on each trade, or the registry cannot prove states (01 §7.9).

---

## 2. Learning where a strategy thrives

### 2.1 Conditional performance attribution

- **Idea:** judge performance conditional on observable state, not unconditionally. Conditioning on public information variables changed the inferences on fund skill. CHECKED (Ferson & Schadt 1996): https://doi.org/10.1111/j.1540-6261.1996.tb02690.x .
- **QMX form (INFERRED):** every trade row carries its **entry-time** state vector: session, weekday, T0-T3 labels from §1, instrument class, cost ratio. Per-cell results are computed in R with trade counts.
- **Rule:** use only states known at entry. A label computed with later data is look-ahead. Projections over these states are What-If views, not proof (03 H3).

### 2.2 Clustering strategies by where their profits came from

- **Profile vector per unit (INFERRED):** its shrunk expectancy in each state cell (§2.4). Two bots with similar profiles thrive in the same conditions.
- **Clustering tool:** ONC, which clusters on a distance built from correlations and finds the number of clusters itself. Its stated use is counting the effectively independent trials. CHECKED: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167017 .
- **Two outputs (INFERRED):**
  - families of units that thrive in the same conditions, which the router treats as one bet in those conditions;
  - the effective trial count N for the deflated Sharpe in §6.

### 2.3 Similarity between markets ("hypotheticals")

- **Method (INFERRED):** fingerprint each (instrument, window) with features a router cares about:
  - seasonal volatility curve shape;
  - cost burden (spread ÷ typical 1m range);
  - variance ratio at 1/5/15 minutes;
  - 1m return autocorrelation;
  - tail heaviness;
  - tick rate.
- Then rank nearest neighbours of a unit's proven cells. Generic fast feature sets exist: catch22 has 22 interpretable features, runs about 1,000× faster than the full hctsa library and loses about 7% accuracy. CHECKED: https://link.springer.com/article/10.1007/s10618-019-00647-x .
- **Validate the similarity measure itself:** across pairs of cells where the unit was tested, check whether feature distance predicts the performance gap. If it does not, similarity is not evidence. INFERRED.
- **Hypotheticals stay hypotheses.** A neighbour is a candidate to test on unseen data, never a placement (seeds; 03 H3).

### 2.4 Sample-size limits per cell

- **Minimum track record length** (Bailey & López de Prado 2012). MinTRL ≈ 1 + [1 − skew·SR + (kurt − 1)/4·SR²]·(z_α ÷ (SR − SR*))². It is counted in observations; here one observation is one trade. CHECKED (concept and dependence on skew and kurtosis): https://www.davidhbailey.com/dhbpapers/sharpe-frontier.pdf .
- **Worked numbers (INFERRED, 95% one-sided, SR* = 0):**

| Unit's trade profile | Per-trade SR | Trades needed |
|---|---|---|
| 55% wins at 1:1 (mean 0.1R) | 0.10 | ~270 |
| 70% wins at +0.5R, losses −1R (mean 0.05R, skew −0.87) | 0.073 | ~550 |
| Thin edge, mean 0.05R at 1:1 | 0.05 | ~1,090 |

- **Consequence:** 4 sessions × 3 vol bands × 2 spread bands × a change flag = 48 cells. A scalper with 2,000 trades has about 40 per cell, so no cell proves anything on its own. INFERRED.
- **Remedy: partial pooling.**
  - Formula: cell estimate = w·cell + (1 − w)·parent, with w = n ÷ (n + k). k is set from the spread across cells (empirical Bayes).
  - On baseball averages after 45 at-bats, Stein's rule had less than half the total squared error of the raw averages; efficiency was 3.5×. CHECKED: https://faculty.chicagobooth.edu/nicholas.polson/teaching/41900/efron-morris1.pdf .
  - Raised SR*: when a cell was picked from many, set SR* to the expected maximum under the null (§6), not zero. CHECKED (DSR paper): https://davidhbailey.com/dhbpapers/deflated-sharpe.pdf .
- **Scalpers' advantage:** many trades per week, so MinTRL arrives in weeks, not years, if results are kept per trade. INFERRED.

### 2.5 Failure modes

- Too many cells. Coarse cells plus shrinkage beat fine cells. Start with session × vol band. INFERRED.
- State labels that depend on the strategy's own trades (for example "after a loss"). They mix sizing effects into placement. INFERRED.
- Survivorship. Cells nobody tested look absent rather than bad. INFERRED.

### 2.6 Where it plugs into QMX

- **QMB `analysis/project.py`** (What-If projection) gets MIS-state predicate keys, the same proposal as 03 H3. It needs R per trade (`realized_r` exists only in `qmf-risk` and the node; CHECKED 01 §1.3).
- **Library `unit` kind**: the empty "Markets" tab (`unit.schema.json`, `fields.markets`; CHECKED 01 §2 row 11) holds per-cell {n, shrunk R, raw R, interval, last updated, proof run ids}.
- **ONC clustering** feeds the families ledger the Lab designs (`LP` AD-18) and the d4 variant comparison (`templates/d4-variant-comparison/scripts/compare.py`, a draft).

---

## 3. Routing and allocation

### 3.1 Evidence on allocation across strategies

- **1/N is hard to beat.** None of 14 optimised portfolio models beat 1/N consistently out of sample. Mean-variance needs about 3,000 months of data to beat 1/N with 25 assets. CHECKED: https://academic.oup.com/rfs/article/22/5/1915/1592901 .
- **HRP** avoids inverting the covariance matrix. In Monte Carlo it gave lower out-of-sample variance than the critical line algorithm and traditional risk parity. CHECKED: https://doi.org/10.3905/jpm.2016.42.4.059 . Independent tests are mixed: HRP "does not report the best performance" in Brazil (CHECKED: https://doi.org/10.12660/rbfin.v21n4.2023.89848 ). It gave smaller drawdowns than equal weight on 14 ETFs with short lookbacks (CHECKED, a student paper: https://www.ysjlab.com/papers/hierarchical-risk-parity.pdf ).
- **Bandits for blending portfolios.** Thompson sampling over basis portfolios beat equal weight and value weight on Fama-French datasets at monthly frequency. CHECKED: https://www.ijcai.org/Proceedings/16/Papers/283.pdf . A follow-up reports that its version "is not robust enough" at higher frequency. CHECKED: https://arxiv.org/html/1911.05309v2 . Bandit selection among trading strategies is supported only by small conference studies that struggle in adverse markets. CHECKED: https://doi.org/10.54254/2755-2721/83/2024glg0075 .
- **Non-stationary bandits.** Discounted UCB and sliding-window UCB match the regret lower bound for abruptly changing rewards up to a log factor. The window or discount must be tuned to how often things change. CHECKED: https://doi.org/10.48550/arxiv.0805.3415 .

### 3.2 Meta-labeling as a sizer and router

- **What it is:** a primary model chooses the side; a secondary model predicts whether that bet will be right, which sets take/skip and size. Splitting side and size limits overfitting, because the ML layer never picks direction. Labels come from the triple-barrier exit (profit-take, stop, time). CHECKED: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3104816 .
- **Evidence:**
  - A controlled experiment on its three components, with improved Sharpe and drawdown. CHECKED: https://doi.org/10.3905/jfds.2022.1.098 .
  - Calibrating the probabilities significantly helps fixed sizing rules; rules fitted on training data gain nothing from calibration. CHECKED: https://doi.org/10.3905/jfds.2023.1.119 .
  - Mostly one research group (Hudson & Thames) on synthetic or controlled data. PRACTITIONER-adjacent.
- **Why it fits QMX (INFERRED):**
  - The bot never sees the MIS.
  - The meta-labeler lives in the router/unit sizer, reads entry-time MIS states, and learns from that bot's own trades.
  - That is "MIS = router" at the level of single trades, and it reconciles the 20 Oct "MIS = TA blocks" lean with seeds' router: state matters, but outside the bot.
- **Data need:** thousands of labelled trades per unit. Scalpers have them; swing bots do not. INFERRED.

### 3.3 Speed and robustness (INFERRED)

- Telling two strategies apart whose per-trade SR differs by 0.05 needs roughly 2·(1.645/0.05)² ≈ 2,200 trades per arm. A bandit that switches between strategies by regime cannot learn faster than regimes change. So bandits fit **exploration budgets** (which hypothetical cells get paper or min-lot slots), not fast switching.
- 1/N in risk units (each unit risks the same fraction of R) is the honest default. HRP becomes worth it once there are many correlated units (1m and 5m of one pair).

### 3.4 Failure modes

- Correlation estimated on full history breaks in stress. Use rolling, regime-conditioned correlation (03 H13). INFERRED.
- A meta-labeler trained and tested on overlapping trades leaks. Use purged CV (§6). CHECKED (the purging rationale): https://doi.org/10.1016/j.knosys.2024.112477 .
- Every meta-label model and every bandit configuration is a trial. INFERRED.

### 3.5 Where it plugs into QMX

- **Pods' allocator and sizer slots** (7 fixed slots; CHECKED 01 §4.1): "1/N risk", "HRP over unit P&L", "Thompson exploration" and "meta-label sizer" become pod blocks.
- **Router placement** (seeds): the registry's shrunk posteriors (§2.4) are the bandit's arms.
- **QML**: the bot emits signals with optional strength (decisions.md). A meta-label probability can multiply that strength, outside the bot.

---

## 4. Self-tuning sizing

### 4.1 Fractional Kelly under estimation error

- **Kelly maximises long-run growth but is risky in the short term.** CHECKED (MacLean, Thorp & Ziemba): https://escholarship.org/uc/item/5mr5k8qj .
- **Half Kelly keeps about 75% of the growth.** If the true edge is half the estimate, full Kelly has zero growth, and 1.5× Kelly with that error is ruin. CHECKED (Thorp): https://web.williams.edu/Mathematics/sjmiller/public_html/341/handouts/Thorpe_KellyCriterion2007.pdf .
- **Drawdown risk for fraction c of Kelly:** P(ever falling to fraction a of the bankroll) = a^(2/c − 1). CHECKED: https://condor.depaul.edu/~wchin/riskpaper.pdf .
  - Applied to QMX's kill line at 40% below seed (a = 0.6), INFERRED: full Kelly 60%, half 22%, quarter 2.8%.
  - Applied to a 50% drawdown: 50%, 12.5% and 0.8%.
  - Read this for the whole account. It assumes a known edge, so the real risk is higher.
- **With an estimated edge, shrink the bet.** CHECKED (Baker & McHale 2013): https://doi.org/10.1287/deca.2013.0271 .
  - My algebra for Gaussian returns: shrink factor k = t² ÷ (1 + t²), where t is the edge's t-stat. So t = 1 → 0.5, t = 2 → 0.8, t = 3 → 0.9. INFERRED.
  - Selection makes t too high. Use the deflated or held-out estimate (§6), not the best in-sample one. INFERRED.

### 4.2 Volatility targeting

- Volatility scaling raises Sharpe only for risk assets (equities, credit). It is negligible for bonds, FX and commodities. It reduces extreme returns and vol-of-vol in every asset class. CHECKED (Harvey et al. 2018, 60+ assets): https://people.duke.edu/~charvey/Research/Published_Papers/P135_The_impact_of.pdf .
- Real-time volatility-managed portfolios did not beat the unmanaged ones across 103 strategies; the gains were in-sample. CHECKED (Cederburg et al. 2020): https://www.lehigh.edu/~xuy219/research/COWY.pdf .
- **For scalpers (INFERRED):** an ATR-scaled stop with fixed risk in R is volatility targeting at the trade level already. Use book-level vol scaling for tail control, not for edge.

### 4.3 Drawdown-controlled sizing

- **Optimal policy under a max-drawdown limit:** risk in proportion to the surplus W − αM, where M is the high-water mark. The floor ratchets up with M. CHECKED: https://doi.org/10.1111/j.1467-9965.1993.tb00044.x .
- **QMX today:** daily budget = (equity − kill line) ÷ 5 (decisions.md). That is portfolio insurance with a fixed floor. Grossman-Zhou suggests letting the floor rise with the high-water mark, with α configurable. INFERRED.
- **Effect:** risk falls automatically near the kill line, and also at new highs when α is high. On a $300 account a high α would choke compounding, so expose it as one number with a preview in the pod simulator. INFERRED.

### 4.4 Anti-martingale evidence (house money, reverse house money)

- **Stop-loss and de-risking after losses lower expected return when returns are a random walk.** They can add value only when returns have momentum or regime switches. CHECKED: https://www.sciencedirect.com/science/article/abs/pii/S138641811300030X .
- **Strategy returns can be autocorrelated.** 65 equity factors have mean monthly AR(1) of 0.11 (positive in 59 of 65), and timing them on their own past return earns an information ratio of 0.33. CHECKED (Gupta & Kelly 2019): https://www.aqr.com/-/media/AQR/Documents/Insights/Journal-Article/Factor-Momentum-Everywhere-JPM-Quant-19.pdf?sc_lang=en .
- **QMX rule (INFERRED):** before a unit gets house money (HME) or reverse house money (RHME), measure the serial correlation of its own trade-R or daily-R series in QMB.
  - Positive and significant: equity-curve sizing has a basis.
  - Near zero: RHME only cuts return; keep only the loss-point brakes for safety.
  - Martingale (size up after losses) stays a guard that flags the bot, never a mode (02 §11 row C).

### 4.5 Bayesian sizing

- **Keep a posterior over the unit's per-trade edge and variance.** Start from the backtest prior, deflated, and update with every paper or live trade. Size = shrunk Kelly from the posterior × the fraction c. INFERRED.
- **This is decisions.md's "Bayesian ramp".** Paper-to-live size climbs as the posterior narrows, capped by the Kelly ceiling. INFERRED.

### 4.6 "Tighten, never loosen"

- **The ratchet bias (INFERRED):** size_t = min(size_{t−1}, g(estimate_t)) tracks the running minimum of a noisy estimate. Over many updates it drifts to the floor even when the edge never changed.
- **Where a one-way ratchet is principled:** the drawdown floor (§4.3).
- **For per-unit settings (INFERRED):**
  - **Tighten fast:** loss points per session or day (rules, immediate), a breach of the MC cone (03 H7), or a CUSUM alarm on trade R.
  - **Loosen slowly and only on evidence:** an e-value against "edge ≤ the level that justified the tighter size" that crosses 1/α on trades after the tightening (SAVI, §7), plus a minimum time.
  - **Always bounded:** inside the declared parameter ranges and under the Kelly ceiling.
- **How slow decay detection is** (CUSUM on per-trade R, σ = 1R, one false alarm per 1,000 trades; INFERRED from the bound in §1.3):

| Edge before → after | Trades to detect |
|---|---|
| +0.1R → 0 | ~1,400 |
| +0.1R → −0.1R | ~345 |
| +0.1R → −0.3R (broken bot) | ~86 |

  Only a badly broken bot shows up fast. That is why bleeding control must be loss limits and decay detection must be statistics; decisions.md already separates them.

### 4.7 Small-account granularity (INFERRED)

- Size must round down to the venue's lot step. QMB already refuses non-multiples (CHECKED 01 §1.6).
- If the minimum lot forces risk above the Kelly ceiling, skip the trade rather than over-bet. Show "skipped for size" as its own count. Otherwise the record looks better than the unit's real fill rate.

### 4.8 Where it plugs into QMX

- **`qmf-risk/sizing.py`**: the ladder is "defined-unwired" (CHECKED 01 §1.1). The surplus-based budget and the Kelly ceiling fill it.
- **Pods' sizer/throttles/caps slots.**
- **The unit's risk profile:** HME, RHME, Kelly ceiling, size ramp and loss points (decisions.md baseline).
- **QMB rerun** (`analysis/rerun.py`): any sizing change is a new run (03; WB spine), so the serial-correlation test and sizing variants count as trials.

---

## 5. Exits

### 5.1 Methods and evidence

- **Optimal stopping for mean reversion.** For an Ornstein-Uhlenbeck spread with costs:
  - the entry region is a bounded band strictly above the stop-loss;
  - a higher stop-loss level always lowers the optimal take-profit;
  - entering close to the stop is never optimal.
  CHECKED (Leung & Li 2015): https://arxiv.org/abs/1411.5062 .
- **Stops and serial correlation.** Tight stops on US stocks underperform buy-and-hold because of trading costs, unless returns are strongly autocorrelated. Some stop rules reduce downside risk, but not much. CHECKED (Lo & Remorov 2017): https://www.sciencedirect.com/science/article/abs/pii/S1386418117300472 . Under a random walk, stop-loss rules always lower expected return. CHECKED (Kaminski & Lo, §4.4).
- **Trailing stops.**
  - On stocks they lower mean return versus the benchmark and reduce total and downside risk. Transaction costs eat the benefit of tight trails; wider trails survive costs. CHECKED (Dai et al. 2021): https://onlinelibrary.wiley.com/doi/10.1111/irfi.12328 .
  - On commodity factor portfolios (monthly), trailing stops beat fixed stops and volatility targeting. CHECKED (Fan & Zhang 2024): https://doi.org/10.1002/fut.22507 .
  - In a 10-year FX backtest, trailing stops cut profit by 15-22% without cutting drawdown. PRACTITIONER: https://forexop.com/strategy/trailing-stops/ .
- **Intraday exits on index futures.** Intraday stop-loss exits added return to an open-to-close trend strategy. Profit-lock exits showed no strong evidence, and neither helped a gap-reversal strategy. CHECKED (Rentzler & Yu 2004): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=523762 .
- **Triple barrier:** profit-take and stop set by volatility, plus a vertical time barrier. It is both the exit grammar and the label for meta-labeling. CHECKED: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3104816 .
- **Time exits.** For mean-reversion bots the OU half-life gives a natural time barrier (for example exit after k half-lives). INFERRED from the OU setup in Leung & Li.
- **Survival and competing-risks exits.** Model time-to-TP, time-to-SL and time-out as competing hazards, given covariates updated during the trade (OFI, vol ratio, distance to VWAP). Exit when the SL hazard overtakes the TP hazard. INFERRED; I found no peer-reviewed trading evidence. Test it in QMB before believing it.

### 5.2 What this means for exit design (INFERRED)

- **Mean-reversion scalper:** fixed target at the reversion level (VWAP, the operator's named exit, fits here), a stop placed so entry stays clear of it, and a time barrier.
- **Momentum or breakout scalper:** trailing or structure stops make sense only if the unit's own in-trade returns show positive autocorrelation (measured in QMB from MFE/MAE paths).
- **Costs decide tight stops.** Judge every exit variant at tick precision with real spread (03 H12) and at 2× cost (03 H18).
- **The safest exit wins,** and safety exits (hard stop, fast invalidation, breakeven, kill flatten) stay separate (decisions.md).

### 5.3 Failure modes

- Exits tuned on the same trades they are judged on. Exit variants are trials. INFERRED.
- Bar-level backtests misjudge which barrier was touched first inside a bar. Tick replay is needed for scalper exits. INFERRED; QMB replays ticks with bid/ask (CHECKED 01 §1.3).

### 5.4 Where it plugs into QMX

- **QML exit blocks** (the "fill the empty exits family" item in decisions.md): triple-barrier, OU time barrier, VWAP target, trailing (ATR or structure).
- **QMB robustness:** an exit-variant sweep axis plus the MFE/MAE analysis already in results (03 §1.2).
- **Node:** the safety exits stay in the node (breakeven ratchet, kill line; CHECKED 01 §1.4).

---

## 6. Judging real versus luck

### 6.1 The toolset

| Tool | What it answers | Source |
|---|---|---|
| Deflated Sharpe (DSR) | Is the best Sharpe above the expected maximum of N null trials, after skew, kurtosis and length? | CHECKED: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551 |
| Effective N via ONC | How many independent trials were really run | CHECKED: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167017 |
| PBO via CSCV | How often the in-sample winner falls below the median out of sample, across all half/half splits. Its authors suggest rejecting PBO > 0.05 | CHECKED: https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf |
| White's Reality Check | Is the best of a universe better than the benchmark, after snooping? | Applied to 7,846 rules: CHECKED: https://www.kevinsheppard.com/files/teaching/mfe/advanced-econometrics/Sullivan_Timmermann_White.pdf |
| Hansen's SPA | Same question, more power, less hurt by poor alternatives | CHECKED: https://doi.org/10.1198/073500105000000063 |
| Harvey-Liu haircut | How much to cut a Sharpe for multiple testing. The cut is nonlinear: above 50% for SR < 0.4, at most 25% for SR > 1. They prefer BHY (FDR) | CHECKED: https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF |
| CPCV vs walk-forward | Which out-of-sample scheme overfits least. CPCV had lower PBO and better DSR; walk-forward was weakest (synthetic data plus S&P check) | CHECKED: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4686376 |
| MinTRL | How many trades before an SR is credible | CHECKED (§2.4) |

### 6.2 Which tests actually predict out-of-sample survival

- **Backtest Sharpe barely does.** R² < 0.025 on 888 live-tracked algorithms. CHECKED: https://doi.org/10.3905/joi.2016.25.3.069 .
- **Volatility and max drawdown predict more.** Hedging features do too. CHECKED (same paper).
- **The amount of backtesting predicts disappointment.** More backtests meant a bigger backtest-live gap. CHECKED (same paper). That makes the tries ledger (03 H2) the single most predictive record QMX can keep. INFERRED.
- **ML on backtest features did better.** It reached R² 0.17 on hold-out data, and a portfolio built on its predictions beat the top-Sharpe pick. CHECKED (same paper).
- **Snooping-corrected significance is not survival.** The best DJIA rule survived the Reality Check over 1897-1986, then was not significant over 1987-1996 (p ≈ 0.32 for the chosen rule). CHECKED (Sullivan, Timmermann & White, above). Non-stationarity and decay remain after correction.
- **Published anomalies:** returns are 26% lower out of sample (an upper bound for pure data mining) and 58% lower after publication. CHECKED: https://doi.org/10.1111/jofi.12365 .
- **SQ's robustness funnel** showed no lift in one practitioner's repeated meta-test, and fewer than 10% of fully tested strategies traded live like their backtest. PRACTITIONER (03 §2.3).
- **Verdict (INFERRED):** no single published test reliably predicts survival for FX/CFD scalpers. The literature supports four things together:
  1. trial-aware deflation (DSR with ONC's effective N);
  2. PBO on each family;
  3. cost stress and tick-precision replay;
  4. incubation with sequential monitoring.

  QMX should then measure each gate's lift on its own data (03 H1, H15).

### 6.3 Live-versus-backtest decay monitoring

- Per unit: a CUSUM or e-process on per-trade R against the backtest's deflated expectancy, plus the MC cone (03 H7, H8). Expect the delays in §4.6. INFERRED.
- Split drift into signal, fill and cost drift (03 H8). Fill drift recalibrates QMB's slippage port.

### 6.4 Failure modes

- N undercounted: hidden trials such as agent retries, What-If promotions and exit variants. INFERRED.
- CSCV on very short series: too few slices to compute a Sharpe per slice. CHECKED (the paper discusses slice count S).
- DSR assumes roughly IID returns. Per-trade R series of a scalper usually fit better than daily equity. INFERRED.

### 6.5 Where it plugs into QMX

- **Pick one home for the anti-luck maths** (01 §7.5). The deflated Sharpe exists idle in `templates/_shared/overfit-gates/scripts/deflated_sharpe.py`. PBO/CSCV is named and deferred in `qmb/robustness/summary.py`. The Lab designs a families ledger. Recommend QMB `robustness/` as the computing home and the Library families ledger as the record, with templates calling QMB. INFERRED.
- **QMB ledger roles** `trial`/`replicate` exist (03 H2). Make "every run at the QMB door is a trial" automatic.

---

## 7. Domain expansion stopping rules

### 7.1 The frame

- Each cell (logic × instrument × timeframe × window) is one hypothesis: "after-cost expectancy > 0 here". Expansion generates a stream of them. That is the online multiple-testing problem. INFERRED.

### 7.2 Methods

- **Alpha-investing and LORD.** You start with error "wealth" ≤ α. Each test spends some, and each discovery earns some back. The rules control FDR online when null p-values are independent; the paper adds conditions for dependent p-values and a version that bounds the tail of the false-discovery proportion. CHECKED: https://doi.org/10.1214/17-aos1559 . The origin is Foster & Stine's α-investing. CHECKED: https://academic.oup.com/jrsssb/article-pdf/70/2/429/49780159/jrsssb_70_2_429.pdf . This matches seeds' rule "expand only from a parent that passed": discoveries fund their children. INFERRED.
- **E-values and e-processes (safe anytime-valid inference).** Evidence is a betting score. You can check it after every trade and stop or continue for any reason without breaking the error rate. CHECKED: https://arxiv.org/abs/2210.01948 . This is the right tool for paper incubation and live loosening (§4.6), where peeking is constant. INFERRED.
- **Effective N.** 1m and 5m of one pair are largely one bet (seeds). Count correlated cells as one effective trial with ONC (§2.2), and use that N in DSR and in the alpha spending. INFERRED.
- **Hierarchical priors.** A child cell starts shrunk to its parent's estimate. The prior speeds up proof but never replaces unseen data. INFERRED.

### 7.3 A numeric stopping rule (INFERRED; every number configurable)

Expand a branch only while all four hold:
1. **Alpha wealth remains** for the logic's family (LORD/α-investing state, starting at a configurable α, for example 0.05).
2. **The cell can reach MinTRL in time.** Expected trades per month × the maximum incubation months ≥ MinTRL at the raised SR*. Otherwise the cell is "too thin to prove" and is closed, not failed.
3. **The neighbourhood median stays above zero after costs** (SPP across cells, 03 H4).
4. **Marginal breadth is real.** The new cell's rolling P&L correlation with live units is below a cap. Otherwise it adds tries without adding breadth.

**The fail branch is the strictest.** Every context the search projects counts as a trial, and proof must come from data after the search (the sealed holdout; `qmf-data` seal and splits, CHECKED 01 §1.1).

### 7.4 Failure modes

- Dependent p-values (overlapping data across cells) weaken FDR guarantees. The LOND variant handles arbitrary dependence at a power cost. CHECKED (arXiv 1502.06197 abstract): https://arxiv.org/abs/1502.06197 .
- Alpha wealth can be "gamed" by testing easy cells first. Order the tests before looking at data (pre-registration, 03 H14). INFERRED.

### 7.5 Where it plugs into QMX

- **The domain-expansion workflow** (seeds; a workflow, not an agent) holds the alpha-wealth ledger per family.
- **The QMB sweep** (`sweep/axes.py`, `sweep/rank.py`) adds a window axis (missing; CHECKED 01 §2 row 16).
- **The Library registry**: each cell records its state (hypothesis, incubating, proven, closed-thin, failed) with its e-value and alpha spent.

---

## 8. Ideas the operator may not be seeing (all INFERRED)

1. **The scalper MIS is mostly one reusable part:** seasonal baseline plus ratio. SQS is already the template. Build it once, key it per instrument and session, and get the spread, vol, tick-rate, depth and cost states nearly for free. Touches `qmn/mis/` and `qmb/execution/spread.py`'s modelled series.
2. **Speed means information per bar, not a smarter model.** Feed the change flag from ticks or high-low range (about 5× better than closes), not 1m closes. Touches `qmf-data` (ticks exist for FX/CFD via Dukascopy) and `qmf-indicators`.
3. **Meta-labeling is the router at the single-trade level.** It keeps "bots never read the MIS", uses the triple-barrier exit as its label, and gives the unit a calibrated P(win) for sizing. One mechanism serves §1, §3 and §4. Touches Pods' sizer slot and the router.
4. **A bandit over registry posteriors gives "hypotheticals" a budget.** Thompson sampling on the shrunk per-cell posteriors decides which hypothetical cells get paper or min-lot slots. Proven cells get full size, and nothing hypothetical trades full size. Touches the registry and Pods.
5. **The kill line already implies a Kelly fraction.** With the kill line 40% below seed, half Kelly gives a 22% chance of touching it even with a known edge, and quarter Kelly about 3%. A one-screen "risk of touching the kill line" readout per pod makes the trade-off visible. Touches the pod simulator.
6. **Put the ratchet on the floor, not on the estimates.** A rising floor tied to the high-water mark is principled. A one-way ratchet on noisy estimates drifts to minimum size. Loosening goes through an e-value gate.
7. **Test before granting house money.** HME/RHME only make sense if the unit's own record is serially correlated. One QMB statistic per unit decides whether those knobs switch on.
8. **Bleeding versus decay is forced by the maths.** Detecting a lost 0.1R edge takes about 1,400 trades. Fast protection must be rules; "3 strikes → paper" needs redefinition in those terms (decisions.md open item).
9. **Judge scalpers in trades, not days.** MinTRL in trades arrives in weeks. QMB needs per-trade R (missing) to use it.
10. **Prove the similarity measure before using it.** "Markets that look alike" should only feed hypotheticals once the feature distance is shown to predict the performance gap on cells already tested. That is a standing QMB job, like 03 H1.
11. **The tries count is the best-documented predictor of disappointment** (Wiecki et al.). Logging every QMB run as a trial automatically is worth more than any extra robustness test. Touches the QMB ledger and the Library families ledger.
12. **Funnel recipes can get an error rate.** Combining 03 H15 (backtest the workflow) with online FDR (§7) gives each Lab recipe a measured false-discovery rate. Recipes can then be compared like bots.
13. **The cost ratio is the master state for scalpers.** Tight stops lose to costs unless returns are autocorrelated (Lo & Remorov). So live round-trip cost ÷ the unit's average target belongs in every unit's required conditions (02 §11.1 already lists it).
14. **The change flag should gate exploration and loosening, not every entry.** Given its lag, it is better at pausing size increases and new-cell trials after a break than at timing entries.
15. **Regime models at T3 are placement tools on a days scale** (which units are eligible this week), not trade filters. That keeps the HMM/BOCPD/MS-GARCH candidates (DEC-0262) in a role their latency supports.

---

## 9. Configurable numbers seen here (starting points only)

| Number | Source | Where it would live |
|---|---|---|
| False-alarm spacing for the change flag (example: about 10 trading days) | INFERRED | MIS T2 labeler config |
| Seasonal baseline bucket (example: 5 minutes of week) | INFERRED | seasonal baseline component |
| Jump penalty λ (50-100 gave fewer than 1 shift a year on daily data) | CHECKED, Shu et al. | T3 regime labeler |
| EWMA half-life for book vol scaling (20 days in Harvey et al.) | CHECKED | Pods throttle |
| Kelly fraction c (½, ¼) | CHECKED formula | unit Kelly ceiling |
| Shrink factor t²/(1+t²) | INFERRED | unit sizer |
| Floor fraction α of high-water mark | CHECKED form (Grossman-Zhou) | account guard / daily budget |
| Confidence for MinTRL (95% one-sided) | CHECKED form | registry cell proof |
| Shrinkage k in w = n/(n+k) | CHECKED method (empirical Bayes) | registry cells |
| PBO reject level (0.05 suggested) | CHECKED | QMB robustness |
| FDR level and LORD γ sequence | CHECKED method | domain-expansion workflow |
| e-value loosen threshold 1/α | CHECKED method | unit sizer loosen gate |
| Max incubation months per cell | INFERRED | domain-expansion workflow |
| Correlation cap for marginal breadth | INFERRED | domain-expansion workflow, Pods caps |
| Cost-stress multiple (2×) | from 03 H18 | QMB sweep axis |

## 10. Sources (all read 2026-10-24)

Change detection and state
- Adams & MacKay 2007, BOCPD: https://arxiv.org/abs/0710.3742
- Knoblauch, Jewson & Damoulas 2018, robust BOCPD: https://arxiv.org/abs/1806.02261
- Lorden bound and CUSUM optimality (thesis summary): https://doi.org/10.18880/0000002821 ; Polunchenko & Tartakovsky review: https://ar5iv.labs.arxiv.org/html/1310.3285 ; Moustakides 2004: https://doi.org/10.1214/aos/1079120138
- Shu, Yu & Mulvey 2024, jump models vs HMM: https://arxiv.org/html/2402.05272v3 ; practitioner review: https://www.signaltrace.wiki/markov-model/Models/Statistical-Jump-Model
- Andersen & Bollerslev 1997, intraday periodicity: https://public.econ.duke.edu/~boller/Published_Papers/joef_97.pdf
- Cont, Kukanov & Stoikov 2014, OFI: https://arxiv.org/html/1011.6402v3
- Gould & Bonart 2016, queue imbalance: https://arxiv.org/html/1512.03492
- Andersen & Bondarenko 2014, VPIN critique: https://www.sciencedirect.com/science/article/abs/pii/S1386418113000189
- Corsi 2009, HAR-RV: https://doi.org/10.1093/jjfinec/nbp001
- Parkinson 1980, range estimator: https://www.cmegroup.com/trading/fx/files/michael_parkinson.pdf
- Lo & MacKinlay 1988, variance ratio: https://doi.org/10.1093/rfs/1.1.41
- Seasonality per class, via 02 sources S47, S51-S53 (Ito & Hashimoto; Hansen, Kim & Kimbrough; Brauneis et al.; Wang et al.)

Attribution, similarity, pooling
- Ferson & Schadt 1996: https://doi.org/10.1111/j.1540-6261.1996.tb02690.x
- López de Prado & Lewis 2019, ONC: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167017
- Lubba et al. 2019, catch22: https://link.springer.com/article/10.1007/s10618-019-00647-x
- Efron & Morris 1975: https://faculty.chicagobooth.edu/nicholas.polson/teaching/41900/efron-morris1.pdf

Allocation and routing
- DeMiguel, Garlappi & Uppal 2009: https://academic.oup.com/rfs/article/22/5/1915/1592901
- López de Prado 2016, HRP: https://doi.org/10.3905/jpm.2016.42.4.059 ; Reis et al. 2023: https://doi.org/10.12660/rbfin.v21n4.2023.89848 ; ETF study: https://www.ysjlab.com/papers/hierarchical-risk-parity.pdf
- Garivier & Moulines, non-stationary UCB: https://doi.org/10.48550/arxiv.0805.3415
- Shen & Wang 2016, Thompson portfolio blending: https://www.ijcai.org/Proceedings/16/Papers/283.pdf ; follow-up: https://arxiv.org/html/1911.05309v2 ; Guo 2024: https://doi.org/10.54254/2755-2721/83/2024glg0075
- López de Prado 2018, 10 reasons (triple barrier, meta-labeling): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3104816
- Joubert 2022: https://doi.org/10.3905/jfds.2022.1.098 ; Meyer, Barziy & Joubert 2023: https://doi.org/10.3905/jfds.2023.1.119

Sizing
- MacLean, Thorp & Ziemba 2010: https://escholarship.org/uc/item/5mr5k8qj ; Thorp: https://web.williams.edu/Mathematics/sjmiller/public_html/341/handouts/Thorpe_KellyCriterion2007.pdf ; Chin, fractional Kelly drawdown: https://condor.depaul.edu/~wchin/riskpaper.pdf
- Baker & McHale 2013: https://doi.org/10.1287/deca.2013.0271
- Harvey et al. 2018, vol targeting: https://people.duke.edu/~charvey/Research/Published_Papers/P135_The_impact_of.pdf
- Cederburg et al. 2020: https://www.lehigh.edu/~xuy219/research/COWY.pdf
- Grossman & Zhou 1993: https://doi.org/10.1111/j.1467-9965.1993.tb00044.x
- Kaminski & Lo 2014: https://www.sciencedirect.com/science/article/abs/pii/S138641811300030X
- Gupta & Kelly 2019: https://www.aqr.com/-/media/AQR/Documents/Insights/Journal-Article/Factor-Momentum-Everywhere-JPM-Quant-19.pdf?sc_lang=en

Exits
- Leung & Li 2015: https://arxiv.org/abs/1411.5062
- Lo & Remorov 2017: https://www.sciencedirect.com/science/article/abs/pii/S1386418117300472
- Dai et al. 2021: https://onlinelibrary.wiley.com/doi/10.1111/irfi.12328
- Fan & Zhang 2024: https://doi.org/10.1002/fut.22507
- Rentzler & Yu 2004: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=523762
- forexop trailing-stop test (PRACTITIONER): https://forexop.com/strategy/trailing-stops/

Real vs luck, sequential testing
- Bailey & López de Prado 2014, DSR: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551 ; PDF: https://davidhbailey.com/dhbpapers/deflated-sharpe.pdf
- Bailey & López de Prado 2012, PSR/MinTRL: https://www.davidhbailey.com/dhbpapers/sharpe-frontier.pdf
- Bailey, Borwein, López de Prado & Zhu, PBO/CSCV: https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf
- Sullivan, Timmermann & White 1999: https://www.kevinsheppard.com/files/teaching/mfe/advanced-econometrics/Sullivan_Timmermann_White.pdf
- Hansen 2005, SPA: https://doi.org/10.1198/073500105000000063
- Harvey & Liu 2015, backtesting haircut: https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF
- Wiecki et al. 2016: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2745220
- Arian, Norouzi & Seco 2024, CPCV vs WF: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4686376
- McLean & Pontiff 2016: https://doi.org/10.1111/jofi.12365
- Javanmard & Montanari 2018, online FDR: https://doi.org/10.1214/17-aos1559 ; 2015 preprint (LOND/LORD): https://arxiv.org/abs/1502.06197
- Foster & Stine 2008, α-investing: https://academic.oup.com/jrsssb/article-pdf/70/2/429/49780159/jrsssb_70_2_429.pdf
- Ramdas, Grünwald, Vovk & Shafer 2023, SAVI: https://arxiv.org/abs/2210.01948

## 11. Not verified

- Every lag, trade-count and drawdown number in §1.3, §2.4, §4.1 and §4.6 is my arithmetic from the cited formulas under Gaussian or IID assumptions. None was simulated on QMX data. Fat tails, autocorrelation and unknown post-change levels make real numbers worse.
- Abstracts and key sections were read for most papers, not full texts. The Baker-McHale shrink factor in §4.1 is my own derivation, not their formula.
- Meta-labeling, jump-model and bandit results come mostly from single research groups or small studies. No independent replication on FX/CFD scalpers was found.
- No peer-reviewed evidence was found for survival or competing-risks exits in trading (§5.1). It is a hypothesis for QMB.
- QMX code facts are taken from `01-ground-truth.md` (CHECKED there on 2026-10-24), not re-read here.
