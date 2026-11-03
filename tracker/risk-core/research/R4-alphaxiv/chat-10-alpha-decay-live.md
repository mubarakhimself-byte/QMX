# Chat 10 - Detecting alpha decay or strategy degradation live (topic 10)

- Chat URL: https://www.alphaxiv.org/assistant/01a1a155-e489-7d81-a3f6-d61032491480
- Source: alphaXiv assistant, harvested 2026-11-03. Answers are copied verbatim with the page's Copy-message button. Paper titles and claims below are the assistant's claims, not verified.

## Turn 1 (topic question, model: Pro) - question

Context: a retail multi-strategy trading system. Many small automated strategies (scalpers, intraday) trade around the clock across FX, indices, metals, energy, crypto, futures and stocks from one $500 account. Agents propose strategies but never touch money; a human promotes strategies to live. Topic (only this one): detecting alpha decay or strategy degradation live. Sequential tests (CUSUM, SPRT), change-point detection (e.g. Bayesian online changepoint detection), e-values, e-processes and anytime-valid inference / safe testing, used to decide when a live strategy's edge has gone and it should be cut or demoted. Newest 2025-2026 work first, then the classics they build on. Give titles, years, arXiv links and concrete recommendations, including how to set thresholds when a strategy has few trades and returns are fat-tailed.

## Turn 1 (topic question, model: Pro) - answer

**Use a one-sided, restart-aware e-process to confirm economically meaningful degradation, with a faster change detector for warnings—not a rolling Sharpe ratio or repeated ordinary $t$-tests.** For your $500 account, statistical confirmation may arrive too late to protect capital: a pre-authorized loss-budget rule should be able to demote a strategy before its decay test rejects.

The key distinction is **“performance changed” versus “the edge is no longer worth trading.”** A change detector can flag increased volatility, improved returns, or altered execution costs. A cut decision needs a directional hypothesis about **net** performance.

## Newest work first: 2025–2026

These are methodological papers to adapt to strategy monitoring, not demonstrations that alpha decay can reliably be detected from a handful of retail trades. Dates below distinguish first arXiv appearance from subsequent revisions.

| Paper | Year | What matters for your system |
|---|---:|---|
| [**Optimal Priors for Betting Tests with Bounded Payoffs: An Exact Expected-Time Characterization**](https://arxiv.org/abs/2610.25821) — Orabona | **2026, October** | Directly relevant to weak edges: the mixture’s mass near **small bets** determines the adaptation penalty. Robbins-type priors can be substantially better near the null than a uniform prior. These are expected-time asymptotics, not a promise of fast detection after ten trades. [Prior Choice](https://www.alphaxiv.org/abs/2610.25821v2?page=2) |
| [**Improved E-Value Thresholds with Applications to Multiple and Sequential Testing**](https://arxiv.org/abs/2610.11186) — Shen et al. | **2026, October** | Smaller thresholds require additional null-density structure. Crucially, the sequential construction **retains the $1/\alpha$ boundary** and changes the evidence updates. Do not lower your live boundary merely because this paper reports improved fixed-time thresholds. [Sequential Calibration](https://www.alphaxiv.org/abs/2610.11186v1?page=7) |
| [**Change detection with conformal martingales: new optimal constructions, and suboptimality of existing methods**](https://arxiv.org/abs/2609.27179) — Bhattacharyya & Ramdas | **2026, September** | Shows that some existing conformal detectors can respond very slowly after a long stable period; proposes weighted restarted constructions. Attractive for distributional warnings, but its main change model assumes independent observations within regimes, and conformal validity uses a specific information filtration. [Findings](https://www.alphaxiv.org/abs/2609.27179v1?page=1)[Information Used](https://www.alphaxiv.org/abs/2609.27179v1?page=10) |
| [**Gaussian-efficient testing by betting on the mean of bounded data**](https://arxiv.org/abs/2608.21694) — Martinez-Taboada & Ramdas | **2026, August; revised October/November** | Sharp finite-sample bounded-mean inference under conditional-mean assumptions. The principal efficiency result is **fixed-horizon**, not unrestricted rolling-window monitoring; the paper also develops planned-window confidence sequences. Useful for scheduled reassessments, but do not turn its terminal intervals into repeated unadjusted tests. [Scope](https://www.alphaxiv.org/abs/2608.21694v2?page=13) |
| [**Non-partitioned e-detectors for nonparametric sequential change detection**](https://arxiv.org/abs/2607.28322) — Saha & Ramdas | **2026, July** | Handles unknown pre- and post-change laws without prescribing disjoint families. Provides distinct constructions for average-run-length and lifetime false-alarm control. Excellent background for monitoring a strategy with an uncertain baseline—but a change still needs economic interpretation. [Constructions](https://www.alphaxiv.org/abs/2607.28322v1?page=7) |
| [**Post-detection inference for sequential changepoint localization**](https://arxiv.org/abs/2502.06096) — Saha & Ramdas | **2025; revised 2026** | After an alarm, constructs confidence sets for when the change occurred, accounting for data-dependent stopping. Useful for investigating whether decay began with a spread change or market regime, and for avoiding a falsely precise “last profitable date.” [Localization](https://www.alphaxiv.org/abs/2502.06096v6?page=6) |
| [**Multiple testing in multi-stream sequential change detection**](https://arxiv.org/abs/2501.04130) — Dandapanthula & Ramdas | **2025; major October 2026 revision** | The most directly relevant paper for **many simultaneous strategies**. Distinguishes ordinary anytime error control from “error over patience,” and requires streamwise evidence to remain valid when decisions use information from all streams. Its guarantees concern the currently declared set; repeated permanent removals require additional accounting. [Multi-stream Guarantees](https://www.alphaxiv.org/abs/2501.04130v5?page=3)[Repeated Decisions](https://www.alphaxiv.org/abs/2501.04130v5?page=28) |

**My priorities:** the multi-stream paper for system-level error accounting, the optimal-priors paper for weak-edge sensitivity, and the conformal paper for understanding why an apparently valid monitor can become sluggish.

I would **not** deploy the density-based threshold reductions first. The paper’s stock example explicitly does not establish its conditional e-value and density assumptions from historical data. [Stock Experiment](https://www.alphaxiv.org/abs/2610.11186v1?page=10)

## Foundations they build on

| Paper | Year | Role |
|---|---:|---|
| **Safe testing** — Grünwald, de Heide & Koolen | **2019 preprint; 2024 publication** | Foundation for evidence that remains valid under optional stopping and continuation. |
| [**Estimating means of bounded random variables by betting**](https://arxiv.org/abs/2010.09686) — Waudby-Smith & Ramdas | **2020 preprint; 2024 publication** | Practical variance-adaptive betting tests and confidence sequences; bets can adapt to past observations without losing validity. |
| [**Catoni-style confidence sequences for heavy-tailed mean estimation**](https://arxiv.org/abs/2202.01250) — Wang & Ramdas | **2022 preprint; 2023 publication** | The essential heavy-tail reference: finite conditional variance with a known upper bound, plus extensions to bounded conditional moments of order between one and two. |
| [**E-detectors: a nonparametric framework for sequential change detection**](https://arxiv.org/abs/2203.03532) — Shin, Ramdas & Rinaldo | **2022 preprint; 2024 publication** | Generalizes CUSUM and Shiryaev–Roberts using restarted e-processes; separates average-run-length control from lifetime false-alarm control. |
| [**Time-uniform, nonparametric, nonasymptotic confidence sequences**](https://arxiv.org/abs/1810.08240) — Howard et al. | **2018 preprint; 2021 publication** | Mixture and stitched boundaries, confidence-sequence/test duality, and empirical-Bernstein inference. |
| [**Bayesian Online Changepoint Detection**](https://arxiv.org/abs/0710.3742) — Adams & MacKay | **2007** | Recursive inference over run length, using a hazard and within-segment predictive model. |

The original historical landmarks predate arXiv: **Wald, “Sequential Tests of Statistical Hypotheses” (1945)** for SPRT; **Page, “Continuous inspection schemes” (1954)** for CUSUM; and **Ville, “Étude critique de la notion de collectif” (1939)** for the martingale maximal inequality. Their connection to modern confidence sequences and e-detectors is described explicitly in the modern papers. [SPRT Foundations](https://www.alphaxiv.org/abs/1810.08240v9?page=3)[CUSUM Foundations](https://www.alphaxiv.org/abs/2203.03532v4?page=2)

## What I would implement

### 1. Define “gone” before looking at the live losses

Let $X_{i,t}$ be strategy $i$’s net outcome per observation, normalized by a **pre-outcome** risk scale. Include commissions, spread, slippage, funding, borrow costs, and conversion costs.

Use two distinct targets:

- **Economic failure:** expected net outcome has fallen below a minimum viable edge $m_i$.
- **Relative degradation:** performance has fallen materially below its promotion baseline.

For economic failure, the healthy null is:

$$
H_{0,i}:\quad
\mathbb{E}[X_{i,t}\mid\mathcal F_{t-1}] \ge m_i
\quad\text{throughout monitoring}.
$$

Evidence grows against that null when outcomes are persistently worse. Set $m_i=0$ if you mean literal disappearance of positive expected net return; set $m_i>0$ if a tiny positive edge is not worth its capital, operational load, or execution uncertainty.

**Failure to establish profitability is not proof of decay.** Conversely, rejecting an optimistic backtest mean does not prove that expected net returns are negative.

Freeze the promotion baseline and its uncertainty. Do not treat a selected backtest estimate as the known true live mean, or continuously move the healthy benchmark down with deteriorating results.

### 2. Make the observation unit defensible

For a scalper, twenty fills from one position are not twenty independent observations.

My default would be **completed position campaigns or non-overlapping risk blocks**, retaining a separate marked-to-market loss monitor for open positions. Choose the grouping rule before seeing outcomes. Calendar blocks can help capture an intraday strategy’s total performance, while campaign observations avoid manufacturing observations during inactivity.

Cross-strategy correlation is not automatically fatal. The important condition is that a test’s conditional validity holds given **all information used to choose bets and make decisions**, including other strategies’ outcomes. Aggregating trades into blocks does not, by itself, prove independence or conditional-mean assumptions. [Global Information](https://www.alphaxiv.org/abs/2501.04130v5?page=5)

### 3. Use one confirmation test and one warning detector

**Confirmation:** a one-sided mean e-process, with explicit accounting for candidate change times.

**Warning:** a robust CUSUM/e-detector or Bayesian run-length monitor, used to trigger review or reversible demotion.

Do not require both to fire. That can make a sparse-trade system needlessly slow. Instead, record whether a demotion came from:

- statistical evidence of economic failure;
- a distributional-change warning;
- or a pre-authorized capital-loss rule.

That distinction prevents “we stopped it to protect the account” from being reported as “we proved its alpha disappeared.”

## Thresholds: three different guarantees

### A. Lifetime false-demotion probability

For a valid e-process $E_{i,t}$, cut or demote on:

$$
E_{i,t}\ge \frac{1}{\alpha_i}.
$$

This controls the probability of **ever** crossing while the healthy null holds. It is not a posterior probability that the strategy is dead. The $1/\alpha_i$ boundary follows from the anytime maximal inequality. [Anytime Boundary](https://www.alphaxiv.org/abs/2609.27179v1?page=9)

As an **illustrative policy**, allocate a total false-demotion budget $q=0.05$ across 20 strategies:

$$
\alpha_i=\frac{0.05}{20}=0.0025,
\qquad
\frac{1}{\alpha_i}=400.
$$

A union bound controls any false statistical demotion across those strategies without requiring cross-strategy independence, provided each process is valid for the information used.

The price is low power. For your setting I would reserve this conservative guarantee for **confirmed failure**, not every reversible warning.

### B. Unknown change times: do not restart for free

A test running from promotion can become insensitive because early healthy outcomes overwhelm recent deterioration. Restarted tests solve this—but searching over starts has an error cost.

For candidate starts $s$, build valid delayed processes $E_{i,s:t}$ and assign deterministic weights $\pi_s$ satisfying $\sum_s\pi_s\le1$. One simple aggregate is:

$$
E^{\mathrm{change}}_{i,t}
=
\sum_{s\le t}\pi_s E_{i,s:t}
+
\sum_{s>t}\pi_s.
$$

Threshold the aggregate at $1/\alpha_i$. The second term represents capital reserved for future starts. Summable restart weights preserve lifetime control; late starts receive less weight and therefore need more evidence. [Restart Weighting](https://www.alphaxiv.org/abs/2609.27179v1?page=13)

For a single component to cause rejection, sufficient evidence is roughly $1/(\alpha_i\pi_s)$—not merely $1/\alpha_i$.

**Re-promotion is another testing episode.** Allocate it another budget, for example $\alpha_{i,j}=\alpha_i2^{-j}$ for episodes $j=1,2,\ldots$. Resetting after every bad patch, parameter tweak, or re-promotion without accounting for it destroys a lifetime claim.

### C. Recurrent warnings: use average run length or a bounded horizon

An e-detector is different from an e-process. Thresholding an e-detector at $A$ gives a null average run length of at least $A$, and suitable constructions also give:

$$
\Pr_0(\tau\le H)\le \frac{H}{A}.
$$

It does **not** make the probability of ever alarming equal to $1/A$. [ARL and Horizon](https://www.alphaxiv.org/abs/2607.28322v1?page=7)

For 20 strategies, each monitored for at most 100 observations, an equal common threshold giving a conservative family-wide bounded-horizon error budget of 5% is:

$$
A=\frac{20\times100}{0.05}=40{,}000.
$$

That large threshold is the real cost of repeatedly scanning many streams. For reversible warnings, I would instead choose an operationally tolerable false-warning frequency and validate detection delay, while clearly labeling the guarantee as **ARL**, not lifetime probability.

For asynchronous streams with different observation horizons, use $\sum_i H_i/A_i\le q$ rather than pretending every strategy has the same trading frequency.

## Few trades and fat tails

### Bounded scores: the simplest reliable implementation

If your monitored score genuinely lies in $[a,b]$, and $m_i$ is inside that interval, a downward betting update is:

$$
L_{i,t}
=
1+\lambda_{i,t}(m_i-X_{i,t}),
\qquad
0\le\lambda_{i,t}\le\frac{1}{b-m_i}.
$$

Under the healthy conditional-mean null, its conditional expectation is at most one, and the bound keeps it nonnegative. Products form a valid downward e-process. This is the bounded-mean betting construction with the direction reversed. [Betting Construction](https://www.alphaxiv.org/abs/2010.09686v7?page=13)[Supermartingale Form](https://www.alphaxiv.org/abs/2010.09686v7?page=14)

Practical choices:

- Choose bets using **only past data**.
- Avoid betting at the endpoint, where one observation can wipe out a component.
- Mix several small and moderate bets instead of choosing one large bet from ten observations.
- For sensitivity to weak edges, consider the small-bet-heavy priors studied in [**Optimal Priors for Betting Tests with Bounded Payoffs**](https://arxiv.org/abs/2610.25821). Its theoretical advantage is about adaptation near the null, not universally best performance at every small sample size. [Small-bet Priors](https://www.alphaxiv.org/abs/2610.25821v2?page=9)

**Clipping changes the target.** If you winsorize P&L, the test concerns the mean of winsorized P&L—not automatically the raw dollar edge. A sign test concerns win probability, which can deteriorate while profitability remains positive, or stay high while losses become catastrophic.

Also, a stop-loss order is not a hard return bound: gaps, liquidation, slippage, and failed execution can breach it.

### Raw heavy-tailed means: use moment-based inference

For raw net P&L, my preferred reference is [**Catoni-style confidence sequences for heavy-tailed mean estimation**](https://arxiv.org/abs/2202.01250). It permits dependent observations under a constant conditional mean and a known upper bound on conditional variance; its extensions accommodate predictable moment bounds and infinite variance when a conditional moment of order $p$, with $1<p<2$, is bounded. [Assumptions](https://www.alphaxiv.org/abs/2202.01250v6?page=3)[Heavier Tails](https://www.alphaxiv.org/abs/2202.01250v6?page=14)

Use an upper confidence sequence for a specified post-start mean; demote for economic failure when the upper endpoint falls below $m_i$. Account for searching over starts as above. A confidence sequence accumulated since promotion estimates that segment’s mean—it does not automatically estimate the **current** mean after a change.

The crucial restriction is **known moment control**. Replacing a variance bound with the sample variance of twelve trades does not preserve the theorem. For unrestricted unbounded distributions, simply assuming “finite variance” without a uniform known bound is not enough for useful distribution-free mean inference. [Moment Necessity](https://www.alphaxiv.org/abs/2202.01250v6?page=16)

If you cannot defend a moment bound, use a bounded economically defined score for statistical monitoring and retain an **unclipped dollar-loss override**. Do not claim distribution-free confirmation of raw expected P&L.

### Sparse trades: lower exposure, not the evidence threshold

There is no universal “cut after five losses” threshold. The same loss streak means different things for a high-win-rate scalper and a low-win-rate asymmetric strategy.

For scale, an idealized known-variance Gaussian shift of size $\Delta$ has information per observation $\Delta^2/(2\sigma^2)$. A rough evidence-accumulation time is:

$$
n\approx
\frac{2\sigma^2}{\Delta^2}\log A.
$$

With $A=400$ and $\Delta=0.1\sigma$, that is approximately **1,200 observations**, before additional adaptation penalties. This is an optimistic planning calculation, not a valid heavy-tail stopping rule.

For a small account, the implication is decisive: **a weak edge may be impossible to confirm as dead before its allocated loss budget is exhausted**. Reversible demotion is reasonable while the evidence remains inconclusive.

## Where CUSUM, SPRT, and Bayesian detection fit

**CUSUM:** best viewed as a fast directional change monitor. With specified healthy and degraded densities, accumulate the log likelihood ratio and reset at zero. Under a Gaussian equal-variance model, the downward increment targeting a mean drop $\Delta$ is:

$$
\ell_t
=
\frac{\Delta(\mu_0-X_t)}{\sigma^2}
-
\frac{\Delta^2}{2\sigma^2}.
$$

But fitted Gaussian tails and a sample variance are not a robust guarantee. Prefer valid e-increments or calibrate the entire warning procedure on untouched chronological data with realistic dependence and tail stress. Calibration should examine **early false alarms and delay**, not just average run length.

**SPRT:** useful for a specified healthy-versus-degraded comparison over one episode. Classical Wald boundaries involving both type-I and type-II targets are approximations affected by overshoot; they are not automatically exact small-sample thresholds. If the likelihood ratio is a valid e-process, the one-sided $1/\alpha_i$ boundary gives the clean optional-stopping guarantee. Restarting that SPRT repeatedly still requires restart accounting.

**Bayesian online changepoint detection:** useful for diagnosis and reversible warnings. [**Bayesian Online Changepoint Detection**](https://arxiv.org/abs/0710.3742) maintains a run-length posterior using a hazard; a constant hazard $1/L$ encodes a geometric prior with mean segment length $L$. Its original model assumes within-segment i.i.d. observations. [Segment Assumptions](https://www.alphaxiv.org/abs/0710.3742v1?page=1)[Hazard](https://www.alphaxiv.org/abs/0710.3742v1?page=2)

I would use a tail-aware predictive model and inspect the posterior probability of **recent regime change together with a below-floor regime mean**. Do not equate “short run length” with lost alpha, or interpret a 95% Bayesian alarm as a 5% frequentist false-alarm guarantee. Hazard and likelihood choices materially determine those probabilities.

## Recommendation for this account

Start with **one economic-failure test per strategy**, explicit restart and re-promotion budgets, and a modest robust warning detector. Keep monitoring parameters outside the strategy-generating agents’ control once a version goes live.

Let the monitor produce a demotion recommendation—or enact only a human-preauthorized reversible safety demotion—with the cause recorded. Keep raw marked-to-market loss limits independent of statistical confirmation. Human re-promotion should require a fresh version, fresh forward evidence, and a new allocated testing episode.

**The account should never need to finance the detector’s full statistical sample size.** That is the central design constraint when many weak, sparse, fat-tailed strategies share $500.


