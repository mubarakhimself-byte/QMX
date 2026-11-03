# R4 - alphaXiv research harvest: synthesis

Harvested 2026-11-03 from new alphaXiv assistant chats, one topic per chat. Every chat file in this folder holds the questions and answers verbatim, with the chat URL.

**How to read this file.** Every paper description below is the alphaXiv assistant's claim, copied in condensed form. A title in an answer is not proof of what the paper says, and some arXiv IDs point to 2026 preprints that nobody here has opened. Read the paper before building on it. Where the assistant itself flagged a limit ("not a sizing rule", "simulation only"), that flag is kept.

**Status.** This file is written as the chats finish. The "Coverage" table shows which topics are done.

## Layer key

| Code | QMX layer |
|---|---|
| X1 | Template shape (what a strategy template declares: unit of observation, costs, sessions, exits) |
| X2 | Sizing and accelerators |
| X3 | Brakes, exits and drift (kill switches, drawdown control, decay detection) |
| X4 | Scenarios (stress tests, event windows, regime scenarios) |
| X5 | Edge verification (promotion gates, overfitting checks, post-selection correction) |
| X6 | Observability (monitors, alarms, ledgers) |
| X7 | Agents (what agents may propose, read and never touch) |

## Coverage and run notes

- **Model.** The first two chats (topics 1 and 10) ran on alphaXiv "Pro". The free plan's 5-hour Pro limit then hit, and the operator switched to "Smart". All later answers are Smart. Smart answers are shorter and cite fewer arXiv papers per answer.
- **Method per chat.** One topic question, then follow-up (a) on the top three papers in depth, then follow-up (b) on asset-class differences plus combinations with other topics. From chat 06 on, the per-asset-class question was folded into follow-up (b) to save messages.
- **Dates.** Agent topics ask for the newest work. Trading, portfolio, risk and market-structure topics ask for the strongest work from any year (operator correction, mid-run). Chats 01 and 10 were asked "2025-2026 first", so they lean new.
- **Bookmarks.** "Bookmark all to library" opens a folder picker. Papers go to the existing library folder **qmx-risk-sizing**. Only the first answer of a chat usually carries the bookmark button, so papers named only in follow-ups are not bookmarked.

| Order | Topic | Chat file | Status |
|---|---|---|---|
| Top-down A | Portfolio optimisation and portfolio-level sizing for a book of strategies | chat-23-A-portfolio-level-sizing.md | running |
| Top-down B | Scalping and very low timeframes: risk and sizing when costs dominate | chat-24-B-scalping-low-timeframe.md | running |
| Top-down C | Day trading and intraday: risk and sizing | chat-25-C-intraday-day-trading.md | running |
| Top-down D | Market macrostructure feeding risk limits | chat-26-D-macrostructure.md | running |
| Top-down E | Market microstructure feeding retail risk and sizing | not yet | pending |
| Top-down F | Agents for macro, micro and news, without touching money | not yet | pending |
| Top-down G | Multi-asset book: normalising risk across classes | not yet | pending |
| Technique 10 | Alpha decay detected live | chat-10-alpha-decay-live.md | done (Pro, then Smart) |
| Technique 1 | Sizing with a small, uncertain edge | chat-01-sizing-uncertain-edge.md | done (Pro, then Smart) |
| Technique 6 | Kill switches and circuit breakers | chat-06-kill-switches-breakers.md | done (Smart) |
| Technique 8 | Risk-off regimes and correlation breakdowns | chat-08-risk-off-regimes.md | done (Smart) |

---

## Top-down A - Portfolio-level sizing for a book of strategies (chat 23)

Place in the top-down order: **first**. This is the frame the other topics plug into.

**Core answer (assistant's claim).** Treat each strategy as a sleeve with its own risk allowance; the central book budget binds, not each sleeve's own sizing. Default allocator: equal or conservative risk budgets (risk parity) with cluster caps; HRP when correlations are hard to estimate; fractional Kelly only as an overlay that reduces or ranks, never as the primary allocator. Size every sleeve in **account-level loss units** (fraction of NAV lost under a defined adverse move), with separate limits for what volatility misses: gaps, margin, crowded exposures, minimum trade size. If the minimum lot breaches the sleeve's budget, the sleeve stays simulated.

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| Optimal Versus Naive Diversification: How Inefficient Is the 1/N Portfolio Strategy? (DeMiguel, Garlappi, Uppal) | https://doi.org/10.1093/rfs/hhm075 | 2009 | Estimation error makes optimisers hard to beat out of sample; equal risk budgets are the baseline any optimiser must beat after costs. | X2, X5 |
| Agnostic Risk Parity: Taming Known and Unknown-Unknowns | https://www.alphaxiv.org/abs/1610.08818 | 2016 | Balance risk across risk directions without trusting signal correlations; a continuum toward Markowitz through a shrunk signal covariance. Risk contribution of sleeve i is w_i (Sigma w)_i. | X2 |
| Building Diversified Portfolios that Outperform Out of Sample (Lopez de Prado, HRP) | https://doi.org/10.3905/jpm.2016.42.4.059 | 2016 | Cluster sleeves by P&L or exposure, allocate recursively; no expected returns needed. Clusters stop many similar scalpers looking like diversification. Signal-blind. | X2 |
| Beyond De Prado and Cotton: Hierarchical and Iterative Methods for General Mean-Variance Portfolios | https://www.alphaxiv.org/abs/2604.23833 | 2026 | Critique: HRP ignores alpha views; hierarchical methods that take a view. | X2 |
| The Mathematics of Heuristic Portfolio Optimization (HPO) | https://www.alphaxiv.org/abs/2606.12612 | 2026 | Framework to compare equal weight, inverse vol, risk parity and HRP before reaching for forecast-heavy optimisers; HRP is not universally optimal. | X2 |
| Asset and Factor Risk Budgeting: A Balanced Approach | https://www.alphaxiv.org/abs/2312.11132 | 2023 | Budget risk at two levels: across sleeves and across shared exposures (USD, equity beta, vol selling, event risk). | X2 |
| Honey, I Shrunk the Sample Covariance Matrix (Ledoit, Wolf) | https://doi.org/10.1016/S0047-259X(03)00096-4 | 2004 | Shrink covariances toward a structured target when sleeves are many and history short. | X2 |
| Bayes-Stein Estimation for Portfolio Analysis (Jorion) | https://doi.org/10.1093/rfs/1.3.293 | 1986 | Shrink expected returns toward a conservative prior (near zero net alpha). | X2, X5 |
| Global Portfolio Optimization (Black, Litterman) | https://doi.org/10.2469/faj.v48.n5.28 | 1992 | Start from the risk-budgeted book and tilt only where evidence is credible, weighted by confidence. | X2 |
| Robust Portfolio Optimization (Goldfarb, Iyengar) | https://doi.org/10.1287/opre.51.3.423.14950 | 2003 | Optimise against uncertainty sets; stress correlations and vol. | X2, X4 |
| Universal Portfolios (Cover) | https://doi.org/10.1111/j.2517-6161.1991.tb01883.x | 1991 | Online reweighting, but slower than the trading, capped, cost-charged. | X2 |
| Cost-Sensitive Online Window Size Selection for Portfolio Management | https://www.alphaxiv.org/abs/2609.29887 | 2026 | The lookback window is itself a noisy choice; pick it out of sample and charge turnover. | X2 |
| Portfolio Selection with a Drawdown Constraint (Grossman-Zhou line) | https://doi.org/10.1111/1467-9965.00041 | 1993/2002 | Drawdown-aware brake around the allocator. | X2, X3 |
| On the Fundamental Law of Active Management (Clarke, de Silva, Thorley) | https://doi.org/10.3905/jpm.1999.319752 | 1999/2002 | Effective breadth, not strategy count; breadth describes diversification, not extra evidence of alpha. | X2 |
| Cost-aware Portfolios in a Large Universe of Assets | https://www.alphaxiv.org/abs/2412.11575 | 2024 | Defer reallocations whose benefit is below trading cost. | X2 |
| Optimal Execution of Portfolio Transactions (Almgren, Chriss) | https://doi.org/10.21314/JOR.2001.041 | 2001 | Charge each reallocation for impact and spread. | X2 |
| Markowitz (1952), Kelly (1956) | DOIs in chat | - | Foundations; mean-variance is fragile, Kelly is a ceiling to scale down from. | X2 |

**Operating numbers the assistant gave (implementation choices, not results from the papers).**
- Risk and account limits recomputed **daily** and allowed to cut at once; planned allocation changes **weekly**; full review **monthly**; earlier only on an alarm, a logic change or a limit hit.
- New strategy enters at **10-25% of its eventual risk budget**, raised in stages on live net performance, costs, slippage, realised risk and its marginal diversification to the whole book.
- Three portfolio quantities per sleeve: routine risk (vol or ES at its holding horizon), stress loss (shared shocks with correlations rising), feasible size (loss, margin and notional of the minimum position with gaps and stop slippage).
- Pod-shop practice is an operating analogy: sleeves with risk allowances, central monitoring, cut or scale against book limits.

**Per asset class (assistant's claim).** FX: pip value and conversion, lot size, broker stop-out rules; majors converge through USD in stress. Indices: CFD vs future vs ETF multipliers and financing; cash vs overnight gaps; shared equity beta. Metals: precious vs industrial; USD and rates; roll and CFD financing. Energy: gaps, limit moves, roll yield, contract limits; correlation to equities flips by episode. Crypto: exchange, custody, funding and outage risk are implementation risk, not price vol; forced liquidation can beat the stop. Futures: product-specific; margin rises with vol; dollar P&L per tick. Single stocks: borrow, recalls, squeezes, overnight earnings gaps, survivorship.

## Technique 10 - Detecting alpha decay live (chat 10)

**Core answer (assistant's claim).** Confirm economic failure with a one-sided, restart-aware e-process on **net** outcomes against a minimum viable edge m_i, and run a faster CUSUM or e-detector for reversible warnings. Keep a dollar loss limit independent of the statistics, because a weak edge often cannot be proven dead before its loss budget is gone ("the account should never need to finance the detector's full statistical sample size").

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| Multiple testing in multi-stream sequential change detection (Dandapanthula, Ramdas) | https://arxiv.org/abs/2501.04130 | 2025, rev. 2026 | e-d-BH and e-d-Bonferroni for declaring which of many strategies changed. Controls "error over patience" (EOP), not plain FDR: to target FDR q over horizon H, set alpha = q/H. Each stream's evidence must stay valid given all streams' information. | X3, X6 |
| Non-partitioned e-detectors for nonparametric sequential change detection (Saha, Ramdas) | https://arxiv.org/abs/2607.28322 | 2026 | Change detection with unknown pre- and post-change laws; separate constructions for average-run-length and lifetime false-alarm control. | X3 |
| E-detectors: a nonparametric framework for sequential change detection (Shin, Ramdas, Rinaldo) | https://arxiv.org/abs/2203.03532 | 2022/2024 | Generalises CUSUM and Shiryaev-Roberts with restarted e-processes; separates ARL control from lifetime control. Foundation for the two above. | X3 |
| Universality of e-detectors for ARL control | https://arxiv.org/abs/2608.12660 | 2026 | Strong e-detectors also bound false-alarm probability at data-dependent horizons, not only ARL. | X3 |
| Optimal Priors for Betting Tests with Bounded Payoffs (Orabona) | https://arxiv.org/abs/2610.25821 | 2026 | For weak edges, put mixture mass near small bets (Robbins-type priors) to cut the adaptation penalty near the null. | X3, X5 |
| Change detection with conformal martingales (Bhattacharyya, Ramdas) | https://arxiv.org/abs/2609.27179 | 2026 | Some conformal detectors go sluggish after a long stable period; weighted restarts fix it. Restart weights pi_s summing to at most 1 keep lifetime control. | X3 |
| Post-detection inference for sequential changepoint localization (Saha, Ramdas) | https://arxiv.org/abs/2502.06096 | 2025/2026 | After an alarm, a confidence set for when the change began: did decay start with a spread change or a regime? | X3, X6 |
| Estimating means of bounded random variables by betting (Waudby-Smith, Ramdas) | https://arxiv.org/abs/2010.09686 | 2020/2024 | The bounded betting e-process. Downward update L = 1 + lambda(m_i - X), lambda in [0, 1/(b - m_i)], bets chosen from past data only. | X3, X5 |
| Catoni-style confidence sequences for heavy-tailed mean estimation (Wang, Ramdas) | https://arxiv.org/abs/2202.01250 | 2022/2023 | Raw fat-tailed P&L needs a **known** bound on conditional variance (or a p-th moment, 1 < p < 2). A sample variance from 12 trades does not keep the guarantee. | X3, X5 |
| Time-uniform, nonparametric, nonasymptotic confidence sequences (Howard et al.) | https://arxiv.org/abs/1810.08240 | 2018/2021 | Mixture and stitched boundaries; empirical-Bernstein confidence sequences. | X5 |
| Bayesian Online Changepoint Detection (Adams, MacKay) | https://arxiv.org/abs/0710.3742 | 2007 | Run-length posterior with a hazard 1/L. Use for diagnosis and reversible warnings, not as a frequentist alarm. | X3, X6 |
| Improved E-Value Thresholds (Shen et al.) | https://arxiv.org/abs/2610.11186 | 2026 | Warning: its lower thresholds need extra density structure; the sequential version keeps the 1/alpha boundary. Do not lower live thresholds on its strength. | X3 |
| Gaussian-efficient testing by betting on the mean of bounded data (Martinez-Taboada, Ramdas) | https://arxiv.org/abs/2608.21694 | 2026 | Sharp fixed-horizon bounded-mean tests; fits scheduled reassessments, not rolling monitoring. | X5 |
| Classics: Wald SPRT (1945), Page CUSUM (1954), Ville (1939) | pre-arXiv | - | The roots of all of the above. | X3 |

**Concrete numbers the assistant gave (illustrations, not validated settings).**
- Lifetime false-demotion budget q = 0.05 over 20 strategies gives alpha_i = 0.0025, so cut at e-value >= 400 (union bound, no independence needed).
- Bounded-horizon warnings: 20 strategies x 100 observations at 5% gives an ARL threshold A = 40,000. For mixed trade rates, require sum(H_i / A_i) <= q.
- Evidence needed for a drop of 0.1 sigma at A = 400 is roughly 1,200 observations. A weak edge cannot be confirmed dead fast.
- Re-promotion is a new testing episode with its own budget, for example alpha_i x 2^-j for episode j. Never reset evidence for free.
- Observation unit: completed position campaigns or non-overlapping risk blocks, not fills. Keep a separate marked-to-market loss monitor.
- Record the demotion cause: statistical evidence of failure, distribution-change warning, or pre-authorised loss rule.

**Per asset class (assistant's claim).** FX: net out swap and rollover, treat pairs sharing a currency as correlated streams. Indices: split cash session from overnight exposure. Metals and energy: use actual contract P&L, never back-adjusted continuous series; model inventory-release jumps. Crypto: 24/7, no weekday close that hides weekend risk; venue, funding, liquidation are part of P&L. Futures: multiplier, tick value and roll per trade; margin is not risk. Single stocks: splits, dividends, halts, earnings gaps; sparse trades make detectors slow. Everywhere: trade-time evidence plus calendar-time safety checks for strategies that have gone quiet.

## Technique 1 - Sizing with a small, uncertain edge (chat 01)

**Core answer (assistant's claim).** Separate the edge-estimation layer from the exposure layer. Shrink the selected strategy's edge for selection bias, require a positive selection-aware lower bound before any exposure, size the **combined book**, and only then apply fractional Kelly or a wealth-floor constraint. "Fractional Kelly is the final brake, not the uncertainty estimator." Round down to executable lots; if the minimum lot exceeds the allowed size, the size is zero.

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| Post-Selection Estimation of Sharpe Ratios (Pav) | https://arxiv.org/abs/2606.01650 | 2026 | After picking the best of k candidates, shrink its Sharpe toward the pool mean with positive-part James-Stein: s = (1 - ((k-2)/n) / ||z - zbar||^2)+. Use GMLEB when few candidates are truly good. Needs the **whole** candidate pool, including rejected variants. | X5, X2 |
| Distributional Robust Kelly Gambling (Sun, Boyd) | https://arxiv.org/abs/1812.10371 | 2018/2021 | Maximise worst-case expected log growth over an uncertainty set (box, ellipsoid, divergence, Wasserstein, moment). Returns a full allocation including cash; holds cash when the edge is weak relative to the set. | X2 |
| Risk-Constrained Kelly Gambling (Busseti, Ryu, Boyd) | https://arxiv.org/abs/1603.06183 | 2016 | Replace an arbitrary Kelly fraction with an explicit wealth-floor probability constraint (convex). Bounds falling below a fraction of initial wealth, not peak-to-trough drawdown. | X2, X3 |
| Kelly betting on horse races with uncertainty in probability estimates (Metel) | https://arxiv.org/abs/1701.02814 | 2017/2018 | Integrate parameter uncertainty or add a mild chance constraint on expected log wealth; strong conservatism costs too much growth. | X2 |
| Conformal Kelly: When Marginal Coverage Transfers and the Economics Do Not (Ryan) | https://arxiv.org/abs/2608.01494 | 2026 | A warning: well-calibrated prediction intervals used as a volatility proxy in capped fractional Kelly still ranked last out of sample. Evaluate the whole sizing rule, and check coverage per regime. | X2, X5 |
| Certified Alpha Capacity: Statistical Arbitrage When Learning Takes Time (Bonacorsi) | https://arxiv.org/abs/2610.01115 | 2026 | Treat validation time and alpha decay jointly; declare false-deployment and power targets; count candidates searched. A certification frame, not a sizing formula. | X5 |
| Anytime-valid t-tests and confidence sequences for Gaussian means with unknown variance (Wang, Ramdas) | https://arxiv.org/abs/2310.03722 | 2023/2025 | Continuously updated one-sided edge bounds that survive optional stopping (Gaussian setting). | X5 |
| Tackling estimation risk in Kelly investing using options (Lillo et al.) | https://arxiv.org/abs/2508.18868 | 2025 | Mix two Kelly portfolios that react differently to misspecification; long-run, model-specific. Low priority. | X2 |
| Sizing the Risk: Kelly, VIX, and Hybrid Approaches in Put-Writing (Wysocki) | https://arxiv.org/abs/2508.16598 | 2025 | Kelly times a regime factor (1 - normalised VIX rank), then round contracts down subject to margin. A template for "regime multiplier on top of Kelly". | X2 |
| Optimal Betting Under Parameter Uncertainty (Baker, McHale) | https://ideas.repec.org/a/inm/ordeca/v10y2013i3p189-199.html | 2013 | Estimate the Kelly haircut from the uncertainty instead of assuming half-Kelly. | X2 |
| Long-term capital growth: good and bad properties of Kelly and fractional Kelly (MacLean, Thorp, Ziemba) | https://ideas.repec.org/a/taf/quantf/v10y2010i7p681-687.html | 2010 | The growth-for-safety trade of fractional Kelly. | X2 |
| Browne and Whitt, Portfolio Choice and the Bayesian Kelly Criterion | ResearchGate | 1996 | Bayesian Kelly with filtered parameter estimates. | X2 |
| Classics: Kelly (1956); James and Stein (1961); Jiang and Zhang GMLEB (2009) | pre-arXiv | - | Foundations. | X2, X5 |

**Formulas the assistant gave (to check before use).** Bayesian Kelly for a binary bet uses the posterior mean win probability, so posterior uncertainty alone adds **no** haircut; a sceptical prior does. Lower-bound Kelly: mu_L = mu_hat - z x SE, f = max(mu_L, 0) / sigma_U^2 (an illustration, not a published rule). Shrinkage: mu_tilde = mu_0 + tau^2 / (tau^2 + s_i^2) x (mu_hat - mu_0), within defensible strategy families only.

**Per asset class (assistant's claim).** One sizing architecture, calibrated per class. FX: edge and cost by session and pair; group by underlying currency (long EUR/USD plus short GBP/USD is a big USD bet). Indices: size the actual traded vehicle; cluster index strategies into one equity-beta bucket. Metals: per metal and contract; convert via multiplier and tick value; margin posted is not maximum loss. Energy: contract-level data, explicit roll costs, jump and limit-move scenarios, wider uncertainty sets. Crypto: funding, venue and liquidation inside the return model; heavy shrinkage; hard liquidation buffers; tokens collapse into one risk-on cluster in stress. Futures: size in contracts from stressed dollar P&L per contract; margin buffer above broker minimum. Single stocks: shrink toward sector or style group; borrow, corporate-action and gap costs; point-in-time universes. Everywhere: count effective independent evidence, not bars.

## Technique 6 - Kill switches and circuit breakers (chat 06)

**Core answer (assistant's claim).** Three levels (strategy, asset class, account), tightest limit wins. The kill path is external to every agent and strategy process and acts without model inference. Halt means stop new orders and cancel working orders; flattening is a separate, pre-agreed action. Re-enable is state-based, not a timer.

| Paper or source | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| Trading Agents or Market Crashers? (FARSIGHT) | https://arxiv.org/abs/2609.19705 | 2026 | Interrupts must bypass model inference; immutable hard limits outside the agent; scoped tool permissions; human override. In its simulation, an exchange LULD pause alone did not stop every crash, while an external fast halt plus hard loss limits did. Its fast path costs "a few false halts per calm hour". | X3, X7 |
| Unbounded Losses, Unchecked Inputs: Measuring the Safeguards of LLM Options-Trading Agents | https://arxiv.org/abs/2610.24289 | 2026 | Compute and enforce worst-case loss on the actual order structure at the order boundary, not via size caps or prompts. | X3, X7 |
| On Data-Driven Drawdown Control with Restart Mechanism in Trading | https://arxiv.org/abs/2303.02613 | 2023 | Exposure scales with the remaining drawdown cushion; a restart re-initialises with a forgetting factor (smaller post-restart size). Restart must never reset the true high-water mark. | X2, X3 |
| On Control of Drawdown: Robust Invariance and Optimality | https://arxiv.org/abs/2609.23272 | 2026 | Multi-asset, support-based condition for actions that keep drawdown inside a bound on every return path in the assumed support. | X2, X3 |
| High Frequency Trading and Mini Flash Crashes | https://arxiv.org/abs/1211.6667 | 2012 | Aggressive orders sweep depth; spreads stay wide after. Use price collars and depth-aware checks; the top quote is not executable depth. | X3, X4 |
| Breaking news (exchange trading breaks around macro announcements) | https://arxiv.org/abs/2603.22835 | 2026 | Breakers around news can interrupt price discovery; "wait, then resume" does not mean conditions normalised. | X3, X4 |
| Agentic Limit Order Books: Phase Transitions and Market Impact | https://arxiv.org/abs/2609.31260 | 2026 | Simulated books flip between liquid, frozen and collapsed regimes as agent count and depth change; a stress-test scenario, not a live threshold. | X4 |
| Learning AI Agents, Market Makers, and Stress in Automated Markets | https://arxiv.org/abs/2611.01799 | 2026 | Same return distribution, very different stress persistence; liquidity returns only after a further improvement (hysteresis). Supports separate trip and clear thresholds. | X3, X6 |
| Dependence-Aware Risk Assessment and Optimal Design of AI-Agent Safeguard Systems | https://arxiv.org/abs/2611.00386 | 2026 | Assess safeguards as a dependent system: agents share data, broker and model failure modes. | X6, X7 |
| Online Safety Monitoring for LLMs | https://arxiv.org/abs/2607.02510 | 2026 | A read-only LLM monitor may summarise incidents; it must not be the detector or the re-enable authority. | X6, X7 |
| SEC order on Knight Capital | https://www.sec.gov/files/litigation/admin/2013/34-70694.pdf | 2013 | 45 minutes, 4 million orders, over $460M lost through dormant code. Deployment and rollback controls matter as much as strategy logic. | X3, X6 |

**Design rules the assistant gave.**
- Trigger families: financial (session loss, rolling loss, drawdown from high-water mark, margin, projected gap loss), execution (slippage vs estimate, fills outside collars, duplicate or partial fills, position mismatch, rejects), system health (stale data, clock or sequence gaps, ack latency, disconnects, order bursts), behaviour (disabled instrument traded, size or frequency jumps, many strategies taking the same side).
- Stages: alert and reduce, block new entries, cancel working orders and revoke the strategy's order permission, account-wide stop. Hard stop at once for stale price used in an order, position mismatch, out-of-bounds order, account loss ceiling.
- Starting values it floated for a $500 account (to test, not adopt): alert at 1% daily loss ($5), stop new entries at 2% ($10), human review at 5% peak-to-trough ($25). Strategy budgets must sum below the account budget.
- Re-enable gate: trip stays latched; minimum cool-down **and** trigger cleared **and** health checks pass; hysteresis with several consecutive in-band observations; re-enter one strategy or a small cohort at reduced size, staggered with jitter; hard and account stops need human re-authorisation. Loss counters survive restarts, market closes and date changes.

**Per asset class (assistant's claim).** Asset-specific trip logic, one dollar loss ceiling for the account. FX: session-specific baselines, tighter gates in thin hours, rollover and weekend reopen; exposure by currency. Indices: a venue halt is an external condition, not proof that account risk cleared; split overnight futures from cash session. Metals: block new entries near a configured roll or expiry unless the strategy handles rolls. Energy: a limit move or inability to trade means "risk uncontained"; no auto-restart. Crypto: no daily close resets the budget; weekend baselines; stricter exposure caps; independent account monitor. Futures: hard stop on uncertain contract identity, rejected margin check or mismatch; a limit move is not a normal cool-down. Single stocks: block while halted; require post-reopen stability; tighter limits for thin names.

## Technique 8 - Risk-off regimes and correlation breakdowns (chat 08)

**Core answer (assistant's claim).** No method gives a dependable minutes-ahead warning. Use a fast layer (turbulence and correlation surprise) as a nowcast and a slower confirmation layer (absorption ratio or ARR, graph and eigenvalue measures). Compute signals per bucket (asset class, session or region) from synchronised valid returns, and cut only the implicated bucket; keep a separate whole-book emergency control. Treat bad data as "risk state unknown", never "calm".

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| Skulls, Financial Turbulence, and Risk Management (Kritzman, Li) | https://doi.org/10.2469/faj.v66.n5.3 | 2010 | Turbulence = normalised Mahalanobis distance of the joint return vector. A nowcast; the paper itself says it does not anticipate the first extreme event, but turbulence persists once it starts. | X3, X6 |
| Correlation Surprise (Kinlaw, Turkington) | https://link.springer.com/article/10.1057/jam.2013.27 | 2013 | CS = turbulence / magnitude surprise. CS > 1 with high magnitude surprise predicted higher next-day magnitude surprise in its daily data; decays over days 2-5. Unstable when magnitude surprise is near zero. | X3, X6 |
| Principal Components as a Measure of Systemic Risk (Kritzman et al., absorption ratio) | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1633027 | 2010 | Share of variance absorbed by the top principal components; rising means tighter coupling. Window length sets responsiveness. | X3, X6 |
| Detecting Changes in Asset Co-Movement Using the Autoencoder Reconstruction Ratio (ARR) | https://arxiv.org/abs/2002.02008 | 2020 | Nonlinear absorption ratio (ARR ~ 1 - AR; lower = more co-movement). Trained on 1-second returns with time of day as input; improved some 5-minute and 1-hour volatility and crash forecasts on 11 US sector indices. Not for buckets of two or three instruments. | X3 |
| Hamilton Markov-switching (1989) and HMMs | pre-arXiv | 1989 | Act only on **filtered** probabilities; smoothed labels leak the future. | X3 |
| Regimes in the Order Flow | https://www.alphaxiv.org/abs/2609.07989 | 2026 | Structural breaks in intraday order-flow regimes; candidate signal. | X3 |
| Lower Spectrum of Financial Correlation Matrices | https://www.alphaxiv.org/abs/2608.09641 | 2026 | Market synchronisation from the lower eigenvalue spectrum. Candidate. | X3 |
| ORCA - Online Regime Correlation Analyzer | https://www.alphaxiv.org/abs/2604.17251 | 2026 | Online cross-asset correlation network. Candidate. | X3, X6 |
| Systemic Risk Radar: A Multi-Layer Graph Framework for Early Market Crash Warning | https://www.alphaxiv.org/abs/2512.17185 | 2025 | Multi-layer graph early warning; no lead time reported. Candidate. | X3 |
| Weekend Crypto Volatility and Monday Market Risk | https://www.alphaxiv.org/abs/2610.35702 | 2026 | Research lead: weekend crypto stress as a Monday exposure review trigger. | X4 |
| Risk-Aware Deep Reinforcement Learning for Dynamic Portfolio Optimization | https://arxiv.org/abs/2511.11481 | 2025 | Candidate learned exposure policy, always wrapped by a deterministic governor. | X2 |

**Isolation rule the assistant proposed (to test walk-forward).** Normalise each bucket's score to its own trailing, time-of-day-aware distribution and alert on a high percentile. Crypto-only cut: local crypto turbulence or low ARR plus, when enough liquid instruments exist, crypto correlation surprise; one extreme token cuts that token's cluster only. Asian-session index cut: compute from instruments trading in that session; never fill closed markets with zero returns. On alert: block new entries in the bucket and cut its open risk by a pre-approved step; on persistent stress, pause the bucket. Small buckets: use a broader liquid proxy basket, shrinkage, or a simple return-and-correlation rule instead of a covariance inverse or an autoencoder. Score by false triggers, missed sell-offs and drawdown avoided, not label accuracy.

**Per asset class (assistant's claim) - which links isolate each class.** FX: 24/5 with a weekend gap; watch broad USD, rates and risk assets; one-currency or one-session divergence means a local cut. Indices: regional indices, index futures, volatility proxies, rates, credit; cut a region or session, not all equity. Metals: split precious from industrial; gold vs USD and real rates; industrial vs energy and manufacturing. Energy: contract-specific; a front-month squeeze or roll dislocation disables that contract cluster, not all classes. Crypto: BTC and ETH, cross-venue prices, funding, basis; equity links only in overlapping hours. Futures: a contract form, not a class; basis or roll breaks cut the contract, not the underlying class. Single stocks: compare with sector, peers and own liquidity; one-name events are name-level cuts.

---

## Asset-class differences across topics (running table)

Condensed from chats 01, 06, 08 and 10. All of it is the assistant's claim.

| Class | Sizing (chat 01) | Brakes (chat 06) | Regime isolation (chat 08) | Decay detection (chat 10) |
|---|---|---|---|---|
| FX | Edge and cost by session and pair; group by currency | Session baselines; tighter in thin hours, rollover, weekend reopen | USD, rates, risk assets; local cut on one-currency divergence | Net out swap; pairs sharing a currency are correlated streams |
| Indices | Size the traded vehicle; one equity-beta cluster | Venue halt is not "risk cleared"; overnight futures separate | Regional indices, futures, vol, rates, credit | Cash vs overnight split; correlated streams |
| Metals | Per metal and contract; multiplier and tick value | Block near roll or expiry | Precious vs industrial; gold vs USD and real rates | Actual contract P&L; macro jumps |
| Energy | Contract data, roll costs, jump scenarios, wider sets | Limit move = risk uncontained; no auto-restart | Contract-specific; roll squeezes are local | Seasonality, inventory jumps, roll yield |
| Crypto | Funding, venue, liquidation in returns; heavy shrinkage | No daily reset; weekend baselines; stricter caps | BTC/ETH, venues, funding; equity links only in overlap | 24/7; no weekday close; venue-specific |
| Futures | Contracts from stressed $ P&L per contract; margin buffer | Hard stop on contract identity or margin reject | Basis or roll break cuts the contract | Multiplier, tick, roll per trade; margin is not risk |
| Single stocks | Shrink to sector; borrow, gaps; point-in-time universe | Block while halted; stability check after reopen | Sector, peers, own liquidity; name-level cuts | Corporate actions, earnings gaps; sparse trades |

---

## Workflows QMX could have

Proposed in the answers so far (assistant's claims, framed as QMX workflows).

1. **Search ledger to promotion gate.** Agents record every candidate, variant, data version and cost-model version in an immutable ledger. The promotion service applies post-selection shrinkage (Pav 2026) and DSR/PBO plus leakage-safe held-out checks, then a funded anytime-valid promotion test on fresh net returns ("Can We Stop the Backtest Yet? Anytime-Valid Promotion Tests for Adaptive Financial Research Agents", https://arxiv.org/abs/2611.03384). A human gives the final live promotion. (chat 01)
2. **Graded live demotion.** Warning detector (CUSUM or e-detector) cuts the strategy's risk budget and opens a review; confirmed economic failure (e-process >= 1/alpha_i) suspends it; a pre-authorised dollar loss rule can demote before either. Each demotion records its cause. Re-promotion is a new funded episode. (chat 10)
3. **External breaker governor.** A process outside all agents watches equity, open risk, margin, reconciliation, data freshness, rejects, slippage and order rate, and moves each strategy, bucket and the account through explicit states: alert, block new entries, cancel working orders, disabled, account stop. An order-boundary validator computes worst-case loss for every order. (chat 06)
4. **Bucket stress isolation.** Per bucket (asset class, session or region): data-validity check, then turbulence, correlation surprise and absorption ratio; a bucket alert blocks entries and steps down that bucket's risk; a separate whole-book control covers broad shocks; re-risk in capped steps after a persistence window. (chat 08)
5. **Read-only LLM risk narrator.** An LLM summarises incidents, explains shared exposure across strategies and drafts a review checklist; it never trips or clears a breaker. (chat 06)

## Papers that could combine

Pairs, triples and larger groups the answers proposed. One line each on what the mix would do.

- **Pav post-selection Sharpe + Anytime-valid promotion tests (2611.03384) + "What survives honest evaluation?" (2608.27734):** shrink the winner for search, check leakage and DSR/PBO, then require fresh prospective evidence under a funded e-value budget before any live money. (chats 01, 10)
- **Promotion tests + Taming Tail Risk: Conformal Calibration for Nonstationary Portfolio VaR (2602.03903):** one stream tests edge decay, a separate calibrated VaR limits exposure; a VaR breach constrains risk without claiming the alpha is gone. (chat 01)
- **Pav shrinkage + Distributional Robust Kelly + The Mathematics of Heuristic Portfolio Optimization (2606.12612):** shrink edges, size against the worst plausible joint distribution, start from an HRP-style cluster allocation, track N_eff = (sum w)^2 / sum w^2. (chat 01)
- **Risk-Constrained Kelly + Distributional Robust Kelly + an external kill path:** robust growth sizing under an explicit wealth-floor probability, with operational stops outside the optimiser. (chat 01)
- **Anytime-valid promotion + Safe Meta-Policy Design with Risk Control (2610.10393):** treat every strategy or sizing change as a risky policy update with a budget of expected harmful updates; choose when to switch rather than switching on every good backtest. (chat 01)
- **Distributional Robust Kelly + Long-run risk-sensitive portfolio optimisation with proportional transaction costs (2608.18676):** size on post-cost, post-roll, post-slippage returns with discrete rebalancing opportunities. (chat 01)
- **Non-partitioned e-detectors + multi-stream multiple testing + conformal portfolio VaR:** per-strategy decay detection, error control across the whole strategy set, and a separate portfolio tail-risk limit. (chat 10)
- **e-detectors + Conformal Kelly + uncertain-edge Kelly:** a weakening detector lowers a strategy's edge estimate or size cap gradually instead of an all-or-nothing cut. (chat 10)
- **Multi-stream testing + HPO + End-to-End Parametric Portfolio Policies for Cross-Asset Futures Timing (2607.00475):** detector evidence lowers weak strategies' risk budgets, then the remaining budget is spread over correlated clusters. (chat 10)
- **Implementation Risk in Portfolio Backtesting (2603.20319) + transaction-cost portfolio model (2608.18676) + e-detectors:** separate true edge decay from simulator-versus-live mismatch, spread widening or roll-cost errors. (chat 10)
- **FARSIGHT + On Control of Drawdown: Robust Invariance (2609.23272) + a cluster governor:** account budget bounded by the remaining drawdown cushion, cluster caps catch correlated losses early, breaker blocks orders instantly on hard faults. (chat 06)
- **Mini Flash Crashes + Breaking news + Agentic Limit Order Books:** "exchange resumed" is not a re-enable signal; require spreads, depth and fills inside collars to normalise, then re-enter small and staggered. (chat 06)
- **Drawdown control with restart + robust drawdown invariance + Regime-Based Portfolio Allocation Using HMMs and RL (2605.27848):** regime probabilities may lengthen a pause or keep size reduced, never override a hard stop. (chat 06)
- **Conformal Kelly + robust drawdown + Unbounded Losses order-boundary veto:** sizing proposes, drawdown clips, an independent validator checks worst-case loss, fees, margin and structure before routing. (chat 06)
- **Certified Alpha Capacity + FARSIGHT + OpenPM: Auditable Point-in-Time Evaluation for LLM Portfolio-Management Agents (2608.09988):** decay is a soft signal that cuts budget and stops adding correlated clones; re-enable only after point-in-time re-evaluation. (chat 06)
- **ARR + correlation surprise + turbulence:** a local contagion trigger per bucket (co-movement, unusual dependence, unusual joint move). (chat 08)
- **Conformal Kelly + Page CUSUM + the bucket contagion gate:** a strategy's own decay lowers its risk even in a calm bucket; the bucket is cut only when bucket stress also fires. (chat 08)
- **Robust drawdown invariance + HRP (Lopez de Prado 2016):** cluster caps from strategy P&L (not instrument labels), then a portfolio drawdown multiplier and local regime multipliers. (chat 08)
