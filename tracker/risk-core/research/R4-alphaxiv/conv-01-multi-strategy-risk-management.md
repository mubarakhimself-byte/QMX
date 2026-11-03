# Multi-Strategy Risk Management (risk and sizing reading list)

- Source: alphaXiv assistant conversation, https://www.alphaxiv.org/assistant/01a1a149-87f4-72e8-99dd-3515efdd22e9
- Copied: 2026-11-03, verbatim from the assistant's own Copy button (questions copied the same way).
- The answers are the alphaXiv assistant's words, not checked against the papers. A paper title here is not proof the paper says it.
- Note: Bookmarked to library (Want to read): the 7 papers with alphaXiv pages, from sections 1, 4 and 5.

---

## Turn 1 - question

I'm designing the risk management and position sizing layer for a retail multi-strategy trading system: many small automated strategies (scalpers, intraday) trading 24h across FX, indices, metals, energy, crypto, futures and stocks from one small account (about $500). I want the best papers, from portfolio and risk management, quant finance, market microstructure and trading agents, and also from other fields that solve the same problems. Topics: (1) position sizing when the edge is small and uncertain (fractional/Bayesian Kelly, sizing off confidence bounds, volatility targeting, many small bets and breadth); (2) allocating one risk budget across many correlated strategies (risk parity, hierarchical allocation, drawdown control, portfolio heat); (3) layered limits and circuit breakers at strategy, cluster and portfolio level that don't fire too often or all at once, including market or asset-class isolation on risk-off and news days; (4) telling a bad run from a decayed edge in live trading (sequential tests, change-point detection, alpha decay, gradual de-risking); (5) stop-loss and exit design (dynamic stops, breakeven moves, fast invalidation) and how exits change sizing; (6) self-configuring parameters with defaults and override hierarchies across many instruments; (7) stress scenarios for correlated losses. For each paper: one line on what to borrow. Include non-finance analogues (clinical trials, power-grid protection, reinsurance accumulation, SRE alerting, control theory) where they fit.

## Turn 1 - answer

**For a $500 account, build the risk layer around executable minimum size, net-of-cost edge, and shared failure domains—not around independent per-strategy Kelly bets.** A strategy can deserve a positive theoretical allocation yet still deserve **zero live size** because its minimum contract, spread, commission, or gap exposure exceeds the account’s risk budget.

I would prioritize the following reading list. The “borrow” column gives an implementation idea, not necessarily a prescription tested by the authors for retail scalping. Foundational work comes first; newer trading-agent papers are marked as exploratory. Engineering references are explicitly distinguished from papers.

## 1. Sizing a small, uncertain edge

| Paper | What to borrow |
|---|---|
| **Risk-Constrained Kelly Gambling** — Busseti, Ryu & Boyd (2016) | Optimize growth subject to a bound on the probability of wealth falling below a floor, rather than selecting an arbitrary Kelly fraction; distinguish this floor constraint from running-peak drawdown. |
| [**Optimal Sports Betting Strategies in Practice** — Uhrín et al. (2021)](https://www.alphaxiv.org/abs/2107.08827) | Use the betting analogue to compare conservative sizing and simultaneous correlated opportunities; probability-estimation error matters as much as the nominal payoff. |
| [**Time-uniform, Nonparametric, Nonasymptotic Confidence Sequences** — Howard et al. (2021)](https://www.alphaxiv.org/abs/1810.08240) | Maintain an anytime-valid lower bound on net expected performance and use it as a conservative sizing input; choose assumptions appropriate to dependent, heavy-tailed trading observations. |
| [**Volatility-Managed Portfolios** — Moreira & Muir (2017)](https://www.nber.org/papers/w22208) | Reduce exposure when estimated variance rises; their inverse-variance scaling is not the same rule as constant-volatility targeting. |
| [**On the Performance of Volatility-Managed Portfolios** — Cederburg et al. (2020)](https://www.sciencedirect.com/science/article/abs/pii/S0304405X2030132X) | Require implementable out-of-sample improvement before adopting volatility timing; favorable retrospective regressions are insufficient. |
| [**A Well-Conditioned Estimator for Large-Dimensional Covariance Matrices** — Ledoit & Wolf (2004)](https://www.sciencedirect.com/science/article/pii/S0047259X03000964) | Shrink covariance estimates before sizing many strategies from short histories; otherwise the optimizer can lever apparent diversification that is estimation noise. |

**Important distinction:** Bayesian uncertainty does not automatically imply fractional Kelly. In a simple binary bet with fixed odds, posterior-expected log utility can yield Kelly sizing at the posterior mean probability. Shrinkage, a conservative posterior quantile, an ambiguity set, or a drawdown constraint must be introduced deliberately if you want additional conservatism.

Likewise, “many small bets” helps only when their **net edges survive costs and their losses are sufficiently independent**. Ten variants of the same signal are not ten independent sources of breadth.

## 2. Sharing one risk budget across correlated strategies

| Paper | What to borrow |
|---|---|
| [**The Hierarchical Equal Risk Contribution Portfolio** — Raffinot (2018)](https://dx.doi.org/10.2139/ssrn.3237540) | Allocate through clusters rather than directly across every strategy; compare volatility-based allocation with downside- or drawdown-based cluster risk. |
| [**A Constrained Hierarchical Risk Parity Algorithm with Cluster-Based Capital Allocation** — Pfitzinger & Katzke (2019)](https://www.ekon.sun.ac.za/wpapers/2019/wp142019/wp142019.pdf) | Add explicit cluster and position constraints to hierarchical allocation; diversification weights should not override operational exposure caps. |
| [**Optimization of Conditional Value-at-Risk** — Rockafellar & Uryasev (2000)](https://sites.math.washington.edu/~rtr/papers/rtr179-CVaR1.pdf) | Allocate against joint scenario losses and expected tail loss, rather than relying exclusively on ordinary covariance. |
| [**Hierarchical Clustering-Based Portfolios** — Palomar, textbook treatment](https://portfoliooptimizationbook.com/book/12.3-hierarchical-clustering-based-portfolios.html) | Use this implementation companion for the original hierarchical-risk-parity construction and its alternatives; linkage, cluster stopping, and splitting rules are meaningful design choices. |

For your system, cluster **strategy P&L on a common clock**, not just underlying asset returns. Include unrealized P&L and zero-exposure periods. Then overlay economic failure domains: USD exposure, equity beta, precious metals, energy, crypto liquidity, and shared broker or data infrastructure. These domains can overlap; they are not necessarily a single tree.

Keep three separate constraints: **statistical portfolio risk, stressed loss, and margin/liquidity consumption**. “Portfolio heat,” meaning summed planned stop losses, is useful bookkeeping but is neither a guaranteed loss ceiling nor a complete correlation model.

## 3. Layered limits, selective isolation, and non-noisy circuit breakers

| Paper or engineering reference | What to borrow |
|---|---|
| [**Optimal Adaptive Coordination of Overcurrent Relays in Power Systems** — Sadeghi et al. (2024)](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/rpg2.13041) | Borrow primary/backup protection coordination: isolate the smallest affected domain first, with broader protection acting when local action fails or the disturbance is systemic. |
| [**Optimal Overcurrent Relay Coordination: A Review** — Hussain et al. (2013), survey](https://www.sciencedirect.com/science/article/pii/S1877705813001628) | Learn selective protection and coordination margins; translate them into severity and escalation rules, not delays that permit a financial hard limit to be breached. |
| [**Robust Model Predictive Control of Constrained Linear Systems with Bounded Disturbances** — Mayne, Seron & Raković (2005)](https://www.sciencedirect.com/science/article/pii/S0005109804002870) | Reserve headroom for disturbances and constrain how quickly exposure changes; the analogy requires explicit uncertainty bounds and does not certify unbounded market jumps. |
| [**Alerting on SLOs** — Google SRE Workbook (2018), engineering chapter](https://sre.google/workbook/alerting-on-slos/) | Use paired short/long windows, budget-consumption rates, severity levels, and alert suppression for soft controls; keep immediate hard safety limits outside this filtering. |

The power-grid analogy is particularly useful: a bad gold strategy should not automatically disconnect unrelated strategies, but a broker outage should affect everything routed through that broker. News isolation should follow **event exposure**, not merely instrument labels—an interest-rate announcement can affect FX, equities, gold, and crypto together.

Do not try to avoid simultaneous triggers by simply staggering thresholds. Use one central controller to reconcile the incident and choose the action. Suppressing duplicate alerts must not suppress independent safety enforcement.

## 4. Bad luck versus a decayed edge

| Paper | What to borrow |
|---|---|
| [**Bayesian Online Changepoint Detection** — Adams & MacKay (2007)](https://www.alphaxiv.org/abs/0710.3742) | Track posterior run length and regime-change probability instead of treating every losing streak as failure; monitor mean, variance, and execution costs separately. |
| [**Time-uniform, Nonparametric, Nonasymptotic Confidence Sequences** — Howard et al. (2021)](https://www.alphaxiv.org/abs/1810.08240) | Inspect performance repeatedly without ordinary fixed-sample confidence intervals becoming invalid; a cumulative-mean bound alone is not a detector of recent decay. |
| [**Discrete Sequential Boundaries for Clinical Trials** — Lan & DeMets (1983)](https://academic.oup.com/biomet/article-abstract/70/3/659/247777) | Spend a preallocated false-alarm budget across scheduled information updates rather than restarting a fresh significance test every day. |
| [**Sequential Control of False Positives in Online Change Point Detection** (2026), recent preprint](https://www.alphaxiv.org/abs/2607.15423) | Investigate explicit false-positive control across repeated change alarms; repeated resets and multiple monitored strategies need more than a one-test threshold. |
| [**Certified Alpha Capacity: Statistical Arbitrage When Learning Takes Time** (2026), exploratory preprint](https://www.alphaxiv.org/abs/2610.01115) | Account for the opportunity lost while collecting evidence: an edge may decay before enough observations justify deployment. |

Use different evidence thresholds for **reducing size**, **suspending a strategy**, and **declaring its edge gone**. A risk controller can reduce exposure before the statistical case for permanent retirement is conclusive.

Also separate signal decay from spread inflation, slippage deterioration, volatility increases, and implementation faults. They can produce the same negative P&L but require different remedies. After suspension, maintain shadow observations; simulated execution should not be mistaken for evidence that live fills have recovered.

## 5. Stops, fast invalidation, and execution-aware sizing

| Paper | What to borrow |
|---|---|
| [**When Do Stop-Loss Rules Stop Losses?** — Kaminski & Lo (2014)](https://www.sciencedirect.com/science/article/pii/S138641811300030X) | Evaluate exits against the return-generating process; a stop is not automatically beneficial, and momentum and mean reversion can imply different effects. |
| [**Dynamic Trading with Predictable Returns and Transaction Costs** — Gârleanu & Pedersen (2013)](https://www.nber.org/system/files/working_papers/w15205/revisions/w15205.rev0.pdf) | Make target positions depend on signal persistence and trading costs; fast-decaying signals and persistent signals should not share one turnover or exit policy. |
| [**Optimal Execution of Portfolio Transactions** — Almgren & Chriss](https://www.smallake.kr/wp-content/uploads/2016/03/optliq.pdf) | Separate desired exposure from its execution path and price execution risk; for $500, minimum fees, spread, and order granularity are generally more relevant than institutional market impact. |
| [**Optimal Stop-Loss and Take-Profit Parameterization for Autonomous Trading Agent Swarm** (2026), exploratory preprint](https://www.alphaxiv.org/abs/2604.27150) | Treat exits as jointly tuned components of the strategy and compare them under realistic execution; do not import its parameters as cross-market defaults. |

A tighter stop is **not permission to increase size without limit**. Stops alter win probability, payoff distribution, turnover, and slippage; size must be recalibrated on the resulting **net trade distribution**. Breakeven moves deserve the same treatment: an entry-price stop is not economic breakeven after fees and spread, and gaps can bypass it.

For fast invalidation, prefer a test of whether the entry premise still holds over an arbitrary requirement to “give the trade room.”

## 6. Self-configuring parameters, defaults, and overrides

This problem has two parts: estimating sensible parameters from sparse data, and ensuring configuration cannot defeat safety controls.

| Paper or engineering reference | What to borrow |
|---|---|
| [**A Well-Conditioned Estimator for Large-Dimensional Covariance Matrices** — Ledoit & Wolf (2004)](https://www.sciencedirect.com/science/article/pii/S0047259X03000964) | Apply the shrinkage principle: sparse instrument estimates should remain near stable pooled defaults instead of receiving unconstrained bespoke estimates. |
| [**The Hierarchical Equal Risk Contribution Portfolio** — Raffinot (2018)](https://dx.doi.org/10.2139/ssrn.3237540) | Let data inform the number of allocation clusters rather than assuming one independent bucket per instrument. |
| [**Configuration Design and Best Practices** — Google SRE Workbook, engineering chapter](https://sre.google/workbook/configuration-design/) | Use explicit schemas, validation, auditable effective configuration, and controlled rollout instead of scattered per-instrument special cases. |
| [**Canarying Releases** — Google SRE Workbook, engineering chapter](https://sre.google/workbook/canarying-releases/) | Roll out parameter changes to a small exposure slice before broad deployment; stagger recovery and releases to avoid synchronized risk expansion. |

My suggested configuration structure is **global default → strategy family → asset class → instrument → temporary event override**. That is a software inheritance scheme, not a statistical theorem.

Keep hard account and cluster caps in a separate constraint layer: a child override may tighten those caps but must not loosen them. Normalize tunable parameters by volatility, tick size, spread, and holding horizon where appropriate; version and expire temporary overrides.

## 7. Correlated-loss stress scenarios and accumulation

| Paper | What to borrow |
|---|---|
| [**Optimization of Conditional Value-at-Risk** — Rockafellar & Uryasev (2000)](https://sites.math.washington.edu/~rtr/papers/rtr179-CVaR1.pdf) | Construct a common scenario-loss matrix for all strategies and constrain portfolio tail loss; scenario completeness matters more than optimizer sophistication. |
| [**A Multivariate Exponential Distribution** — Marshall & Olkin (1967)](https://www.tandfonline.com/doi/abs/10.1080/01621459.1967.10482885) | Borrow the common-shock construction from reliability: one event can affect several components simultaneously, beyond what ordinary pairwise correlations describe. |
| [**Time-consistent Robust Investment-Reinsurance Strategy with Common Shock Dependence** — Li et al. (2025)](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0316649) | Borrow reinsurance accumulation accounting: aggregate exposures to the same underlying event and include uncertainty about dependence, rather than treating positions as separate claims. |
| [**Robust Model Predictive Control of Constrained Linear Systems with Bounded Disturbances** — Mayne, Seron & Raković (2005)](https://www.sciencedirect.com/science/article/pii/S0005109804002870) | Recompute feasible exposure after shocks while retaining a reserve for further disturbance; do not allocate all remaining capacity immediately after a loss. |

At minimum, stress **cross-asset repricing**, **spread/slippage explosions**, **market gaps or halts**, **margin increases**, **broker/data failures**, and **many strategies exiting together**. Revalue the actual instruments and their execution conditions; “set every correlation to one” is not a sufficient stress test.

For this account size, the first implementation should be simpler than the literature: one centralized pre-trade gate, a small number of economic risk clusters, conservative net-edge estimates, scenario-based headroom, and an explicit **reject trade** result whenever minimum executable size does not fit. Keep the strategy universe broad in research, but do not force all of it into live exposure.


