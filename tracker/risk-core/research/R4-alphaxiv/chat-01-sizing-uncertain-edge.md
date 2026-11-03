# Chat 01 - Sizing when the edge is small and uncertain (topic 1)

- Chat URL: https://www.alphaxiv.org/assistant/01a1a153-f1c1-72a4-9bbb-1fce9775c8ec
- Source: alphaXiv assistant, harvested 2026-11-03. Answers are copied verbatim with the page's Copy-message button. Paper titles and claims below are the assistant's claims, not verified.

## Turn 1 (topic question, model: Pro) - question

Context: a retail multi-strategy trading system. Many small automated strategies (scalpers, intraday) trade around the clock across FX, indices, metals, energy, crypto, futures and stocks from one $500 account. Agents propose strategies but never touch money; a human promotes strategies to live. Topic (only this one): position sizing when the edge is small and uncertain. What do 2025-2026 papers say about Bayesian Kelly, fractional Kelly, sizing off confidence bounds of the edge estimate (e.g. lower-bound Kelly), and shrinkage of edge/Sharpe estimates? Newest work first, then the classic papers they build on. Give titles, years and arXiv links, and what each concretely recommends.

## Turn 1 (topic question, model: Pro) - answer

**For your $500 account, I would use a shrunk estimate of the net edge, require a positive lower bound before taking exposure, and apply fractional Kelly only after those steps—not half-Kelly to the best backtest Sharpe.** The most directly relevant 2026 paper recommends James–Stein shrinkage after strategy selection; another shows that well-calibrated prediction intervals can still produce poor Kelly-inspired allocations.

There is **no verified 2025–2026 result here establishing a universal Kelly fraction or proving “lower-bound Kelly” best for retail scalpers**. The newer work addresses separate pieces: selection bias, uncertainty calibration, validation timing, and model misspecification. The direct foundations for Bayesian Kelly and uncertainty-aware bet shrinkage are older.

## 2025–2026 papers, newest first

Dates below distinguish first arXiv submission from later revisions. Links go to arXiv.

| Paper | Year | What it concretely recommends—and what it does not |
|---|---:|---|
| [**Certified Alpha Capacity: Statistical Arbitrage When Learning Takes Time**](https://arxiv.org/abs/2610.01115) — Nicolò Bonacorsi | **2026**, October | Treat validation time and alpha decay jointly. Declare false-deployment and power requirements; use properly controlled sequential certification rather than repeatedly checking an ordinary significance test. Account for the number of candidates searched. **This is a deployment/certification framework, not a lower-bound Kelly sizing formula.** Its quadratic exposure calculation assumes a specified drift experiment. [Certification](https://www.alphaxiv.org/abs/2610.01115v2?page=10)[Scope](https://www.alphaxiv.org/abs/2610.01115v2?page=22) |
| [**Conformal Kelly: When Marginal Coverage Transfers and the Economics Do Not**](https://arxiv.org/abs/2608.01494) — Robert Jacob Ryan | **2026**, August; substantially reframed October | Uses conformal interval **half-width as a volatility proxy**, then capped fractional Kelly. The sealed out-of-sample experiment underperformed passive comparators and ranked last on Sharpe and Calmar. Recommendation: register conditional/regime coverage alongside aggregate coverage and evaluate the **complete sizing rule**, not calibration alone. **It is not lower-confidence-bound sizing of the mean edge.** [Sizing](https://www.alphaxiv.org/abs/2608.01494v3?page=5)[Conclusion](https://www.alphaxiv.org/abs/2608.01494v3?page=26) |
| [**Post-Selection Estimation of Sharpe Ratios**](https://arxiv.org/abs/2606.01650) — Steven E. Pav | **2026**, June | The closest match to agents proposing many strategies. After selecting the maximum observed Sharpe, **use James–Stein shrinkage toward the candidate-set grand mean** as the default estimator. Consider general maximum-likelihood empirical Bayes, **GMLEB**, when only a few candidates are genuinely good. The tested polyhedral point estimators were unstable; simply subtracting the expected maximum was not recommended. **Improved estimation is not itself a confidence guarantee or sizing rule.** [Recommendations](https://www.alphaxiv.org/abs/2606.01650v1?page=29) |
| [**Tackling estimation risk in Kelly investing using options**](https://arxiv.org/abs/2508.18868) — Fabrizio Lillo, Piero Mazzarisi, Ioanna-Yvonni Tsaknaki | **2025**, August; revised November | In a binomial stock–bond–option model, combine two option-based Kelly portfolios that respond differently to parameter misspecification. The combined wealth asymptotically inherits the better component’s growth. **Not Bayesian shrinkage, not a confidence-bound rule, and not a general recommendation to buy protective puts for small accounts.** The result is long-run and model-specific; finite-horizon superiority need not hold. [Portfolio Mixture](https://www.alphaxiv.org/abs/2508.18868v2?page=14)[Implementation](https://www.alphaxiv.org/abs/2508.18868v2?page=16) |
| [**Sizing the Risk: Kelly, VIX, and Hybrid Approaches in Put-Writing on Index Options**](https://arxiv.org/abs/2508.16598) — Maciej Wysocki | **2025**, August | Estimates win probabilities and conditional gains/losses by simulation, then multiplies Kelly exposure by a volatility-regime factor, **one minus normalized VIX rank**, and rounds contracts down subject to margin. It supports a dynamic fractional-Kelly approach **for its SPX put-writing experiment**. It does not derive Bayesian edge shrinkage or statistically calibrated lower-bound Kelly. [Hybrid Sizing](https://www.alphaxiv.org/abs/2508.16598v1?page=8) |

**The most useful companion for continuously updated edge bounds** is [**Anytime-valid t-tests and confidence sequences for Gaussian means with unknown variance**](https://arxiv.org/abs/2310.03722), Hongjian Wang and Aaditya Ramdas: **2025 journal publication, originally a 2023 preprint**. It constructs confidence sequences valid under optional stopping, including a one-sided construction. Use this kind of inference rather than recycling a fixed-sample confidence interval whenever a strategy looks ready. Its principal setting is Gaussian observations; it does **not** establish validity for arbitrary dependent, heavy-tailed scalper P&L or derive a trading Kelly rule. [Contributions](https://www.alphaxiv.org/abs/2310.03722v5?page=3)[Confidence Sequences](https://www.alphaxiv.org/abs/2310.03722v5?page=4)

Two tempting 2026 titles are **not answers to the uncertainty-sizing question**:

- [**Kelly Betting as Bayesian Model Evaluation: A Framework for Time-Updating Probabilistic Forecasts**](https://arxiv.org/abs/2602.09982) evaluates competing forecasts using betting bankrolls as model credibility. “Bayesian” here does not mean a posterior-uncertainty haircut for your trading exposure. [Contribution](https://www.alphaxiv.org/abs/2602.09982v1?page=1)
- [**Efficient Multivariate Kelly Optimization Reveals Sigmoidal Scaling Laws**](https://arxiv.org/abs/2604.24723) improves optimization for many **independent binary bets**. Its lower bounds concern achievable optimal growth and computational approximation—not confidence bounds on an estimated edge. Correlated bets are identified as future work. [Lower Bounds](https://www.alphaxiv.org/abs/2604.24723v2?page=5)[Limitations](https://www.alphaxiv.org/abs/2604.24723v2?page=15)

## The classic papers behind these approaches

Several essential classics are journal papers with no arXiv version located. I label those explicitly rather than attach an unrelated arXiv link.

| Paper | Year / availability | Concrete implication |
|---|---|---|
| [**Distributional Robust Kelly Gambling: Optimal Strategy under Uncertainty in the Long-Run**](https://arxiv.org/abs/1812.10371) — Qingyun Sun, Stephen Boyd | **2018 preprint**, expanded 2021 | Optimize **worst-case expected log growth over an uncertainty set**, rather than a nominal return distribution. Provides tractable probability-box, ellipsoidal, divergence, Wasserstein, and estimated-moment formulations. This is the strongest direct foundation here for confidence-set Kelly. The uncertainty set still needs defensible calibration. [Robust Objective](https://www.alphaxiv.org/abs/1812.10371v3?page=3)[Set Calibration](https://www.alphaxiv.org/abs/1812.10371v3?page=9) |
| [**Kelly betting on horse races with uncertainty in probability estimates**](https://arxiv.org/abs/1701.02814) — Michael R. Metel | **2017 preprint**, 2018 journal | Compare plug-in Kelly with integrating over parameter uncertainty, conservative probability estimates, and chance constraints on expected log wealth. Recommends uncertainty integration with a **mild, application-calibrated chance constraint**; stronger conservatism can sacrifice too much growth. Two-outcome constraints use unfavorable probability quantiles. [Probability Bounds](https://www.alphaxiv.org/abs/1701.02814v2?page=7)[Conclusion](https://www.alphaxiv.org/abs/1701.02814v2?page=12) |
| [**Risk-Constrained Kelly Gambling**](https://arxiv.org/abs/1603.06183) — Enzo Busseti, Ernest K. Ryu, Stephen Boyd | **2016** | Choose an explicit wealth-floor probability constraint instead of an arbitrary Kelly fraction. Derives a convex sufficient condition. Some simulations improve on fractional Kelly at comparable risk; another produces essentially the same trade-off. **The guarantee concerns falling below a fraction of initial wealth, not general peak-to-trough maximum drawdown, and assumes the return model.** [Wealth Floor](https://www.alphaxiv.org/abs/1603.06183v1?page=6)[Risk Constraint](https://www.alphaxiv.org/abs/1603.06183v1?page=7)[Comparison](https://www.alphaxiv.org/abs/1603.06183v1?page=18) |
| [**Optimal Betting Under Parameter Uncertainty: Improving the Kelly Criterion**](https://ideas.repec.org/a/inm/ordeca/v10y2013i3p189-199.html) — Rose D. Baker, Ian G. McHale | **2013; no arXiv version located** | Directly addresses uncertain estimated win probabilities. **Shrink the bet to improve out-of-sample performance**; compares estimated shrinkage factors and supplies an approximate practical correction. Supports estimating the haircut from uncertainty—not treating half-Kelly as a universal optimum. |
| [**Long-term capital growth: the good and bad properties of the Kelly and fractional Kelly capital growth criteria**](https://ideas.repec.org/a/taf/quantf/v10y2010i7p681-687.html) — Leonard C. MacLean, Edward O. Thorp, William T. Ziemba | **2010; no arXiv version located** | Foundation for trading some growth for lower volatility and downside risk through fractional Kelly. It is cited by the newer sizing papers for both Kelly’s estimation sensitivity and the favorable growth–risk trade-off of fractional exposure. [Fractional Kelly](https://www.alphaxiv.org/abs/2508.16598v1?page=5) |
| **General maximum likelihood empirical Bayes estimation of normal means** — Wenhua Jiang, Cun-Hui Zhang | **2009** | Statistical foundation for GMLEB: estimate the distribution of latent signals and shrink noisy observations accordingly. The 2026 Sharpe study recommends its adaptation particularly for a candidate pool containing few genuinely good strategies. **Not originally a trading-sizing paper.** [Sparse Signals](https://www.alphaxiv.org/abs/2606.01650v1?page=13)[References](https://www.alphaxiv.org/abs/2606.01650v1?page=30) |
| [**Portfolio Choice and the Bayesian Kelly Criterion**](https://www.researchgate.net/publication/266728773_Portfolio_Choice_and_the_Bayesian_Kelly_Criterion) — Sid Browne, Ward Whitt | **1996; no arXiv version located** | Foundational Bayesian formulation: learn unknown return parameters and optimize using the information available, rather than assuming the unknown drift is known. The newer options paper describes partial-information log-optimal policies as replacing original parameters with **filtered estimates**. [Partial Information](https://www.alphaxiv.org/abs/2508.18868v2?page=16)[Bayesian Reference](https://www.alphaxiv.org/abs/1812.10371v3?page=19) |
| **Estimation with Quadratic Loss** — William James, Charles Stein | **1961; no arXiv version located** | Foundation for joint shrinkage of noisy estimates, adapted by the 2026 Sharpe paper. Shrinkage targets and noise assumptions matter; this is not a license to pool every strategy across unrelated markets indiscriminately. [Recommendations](https://www.alphaxiv.org/abs/2606.01650v1?page=29)[References](https://www.alphaxiv.org/abs/2606.01650v1?page=30) |
| **A New Interpretation of Information Rate** — John L. Kelly Jr. | **1956; predates arXiv** | Maximize expected logarithmic wealth under the specified outcome probabilities and payoffs. **Does not solve the problem of discovering or estimating an edge.** [Kelly Criterion](https://www.alphaxiv.org/abs/2508.16598v1?page=5) |

## What the four sizing approaches actually mean

These distinctions are important: they are **not four interchangeable names for “bet less.”**

### Bayesian Kelly: integrate uncertainty, but do not expect automatic conservatism

The Bayesian decision is

$$
f_{\mathrm B}
=
\arg\max_f
\mathbb E_{\theta\mid D}
\left[
\mathbb E_{R\mid\theta}
\log(1+fR)
\right],
$$

where $D$ is observed data and $\theta$ represents unknown return parameters.

For a binary bet with known net win payoff $b$ and total loss of the stake, this simplifies to Kelly using the **posterior mean win probability**:

$$
f_{\mathrm B}
=
\left[
\frac{(b+1)\mathbb E[p\mid D]-1}{b}
\right]_+.
$$

This is a direct consequence of expected log wealth being linear in $p$. **Posterior uncertainty alone does not necessarily impose an additional haircut.** A skeptical prior may shrink the posterior mean; ambiguity aversion, wealth-floor constraints, and fractional Kelly are additional decisions. The uncertainty-integration construction in [Metel’s paper](https://arxiv.org/abs/1701.02814) makes the same expectation-versus-plug-in distinction. [Integration](https://www.alphaxiv.org/abs/1701.02814v2?page=5)

### Fractional Kelly: shrink exposure, not the evidence

Fractional Kelly uses

$$
f_{\mathrm{FK}}=\lambda f_{\mathrm K},
\qquad 0<\lambda<1.
$$

It reduces exposure even if the edge estimate is unchanged. **It does not correct selection bias, establish that the edge is positive, or identify the appropriate fraction.** That is why [Baker–McHale](https://ideas.repec.org/a/inm/ordeca/v10y2013i3p189-199.html) is more relevant to your uncertainty question than merely choosing a conventional fraction.

### Lower-bound Kelly: optimize against an unfavorable plausible edge

For a single long-only strategy, a small-return quadratic approximation gives a practical rule:

$$
\mu_L=\hat\mu-z_{1-\alpha}\operatorname{SE}(\hat\mu),
\qquad
f_{\mathrm{LB}}
\approx
\frac{[\mu_L]_+}{\sigma_U^2}.
$$

Here $\mu_L$ is a lower bound on **net expected return**, and $\sigma_U^2$ is a conservative variance input. This equation is an illustrative robust approximation, **not a newly established 2026 formula**. Its justification comes from optimizing the quadratic growth approximation over an uncertainty set, in the spirit of [Sun–Boyd](https://arxiv.org/abs/1812.10371).

For a known-payoff binary bet, replacing $p$ by its lower bound $p_L$ gives

$$
f_{\mathrm{LB}}
=
\left[
\frac{(b+1)p_L-1}{b}
\right]_+.
$$

The crucial distinction is **a bound on expected edge versus a prediction bound on the next return**. A profitable strategy can have a negative lower prediction quantile because individual trades often lose. The conformal paper studies prediction-width sizing, not the mean-edge bound above.

Also, the normal-bound expression is only a fixed-time illustration. Repeated monitoring, candidate selection, serial dependence, and overlapping trades require corresponding inference adjustments; an ordinary standard error does not handle them automatically.

### Shrinkage: improve the input before optimizing

An illustrative Gaussian hierarchical model produces

$$
\tilde\mu_i
=
\mu_0+
\frac{\tau^2}{\tau^2+s_i^2}
(\hat\mu_i-\mu_0),
$$

where $s_i^2$ is estimation-noise variance and $\tau^2$ is genuine cross-strategy edge dispersion. Noisy estimates move further toward the prior or pool target $\mu_0$.

**A shrunk estimate is still a point estimate, not a lower confidence bound.** [Pav’s 2026 paper](https://arxiv.org/abs/2606.01650) supports shrinkage for estimating the selected strategy’s Sharpe, but does not justify subtracting an ordinary standard error from that shrunk value and calling the result calibrated. [Estimation Scope](https://www.alphaxiv.org/abs/2606.01650v1?page=2)

## My sizing choice for your system

I would separate the **edge-estimation layer** from the **exposure layer**:

1. **Estimate net edge at a fixed reference exposure**, including spread, fees, slippage and financing. Preserve the full candidate-search record, including rejected variants; retaining only promoted strategies hides the selection problem.
2. **Shrink within defensible strategy families.** Use the 2026 James–Stein result as a baseline, with an empirical-Bayes alternative when genuine winners appear sparse. Do not assume one common edge distribution for unrelated FX scalpers, stock strategies and crypto carry.
3. **Require a positive, selection-aware lower bound for deployment**, using sequentially valid inference if you monitor continuously. This is a conservative system-design choice, not the Bayesian log-utility optimum.
4. **Size the combined book**, then apply a fractional-Kelly or explicit wealth-floor constraint. Separate per-strategy Kelly calculations cannot each spend the same $500 or assume correlated exposures diversify.
5. **Round executable quantities down; never increase exposure merely to meet a minimum lot.** If the smallest trade exceeds the permitted allocation, the size is zero.

**The main conclusion is that fractional Kelly is the final brake, not the uncertainty estimator.** For small, uncertain edges found through agent-driven search, the strongest directly relevant new evidence favors shrinking the selected edge/Sharpe first. A calibrated lower-bound gate addresses a different objective—avoiding deployment without sufficient evidence—and portfolio-level risk limits address survival after deployment.


## Turn 2 (follow-up a: top three papers, model: Smart) - question

Follow-up 1: Pick the three papers from your answer that matter most for this system. For each one: what exactly the method does, step by step; its inputs and outputs (what I must estimate and what number it hands me); where it fails or its assumptions break (few trades per strategy, fat tails, non-stationary edge, many strategies selected from a larger pool); and which newer papers (2025-2026) build on it or challenge it, with arXiv links.

## Turn 2 (follow-up a: top three papers, model: Smart) - answer

For this system, the three most useful papers address different layers: **post-selection Sharpe shrinkage** deals with choosing winners from many backtests; **Bayesian probability uncertainty** handles uncertain inputs to Kelly; and **distributionally robust Kelly** turns a declared uncertainty set into a portfolio allocation. They are complements, not competing versions of one rule—and only the last two directly return Kelly stakes.

## 1. Correct the winner’s curse before sizing

[**Post-Selection Estimation of Sharpe Ratios**](https://arxiv.org/abs/2606.01650) — Steven E. Pav, **2026**.

**What it does, step by step**

1. Assemble Sharpe estimates for the $k$ strategies that were compared, and record the sample length $n$ used to estimate each one.
2. Identify the strategy with the highest observed Sharpe, $\hat\zeta_k$.
3. Estimate the average Sharpe of the candidate set, $\bar\zeta$, and the squared distance of the candidates’ observed Sharpes from that average, $\|\hat\zeta-\bar\zeta\mathbf1\|^2$.
4. Compute the positive-part James–Stein shrinkage factor
   $$
   s_v=\left(1-\frac{(k-2)/n}{\|\hat\zeta-\bar\zeta\mathbf1\|^2}\right)_+ .
   $$
5. Report the selected strategy’s adjusted Sharpe:
   $$
   \hat\zeta_{\mathrm{JS}}
   =\bar\zeta+s_v(\hat\zeta_k-\bar\zeta).
   $$

When the winner looks unusually good compared with the whole pool, the method pulls its estimate back toward the pool average. When the pool is small or the candidate Sharpes are not very dispersed relative to estimation noise, shrinkage can be stronger. [James-Stein](https://www.alphaxiv.org/abs/2606.01650v1?page=4)

**Inputs and output.** It needs the Sharpe estimates for the *whole comparison set*, the sample length, and a consistent return-frequency convention. Its output is an adjusted estimate of the selected strategy’s population Sharpe—not a position size, probability that the edge is real, or lower confidence bound. To use it for sizing, you would still need a risk estimate and a portfolio-sizing rule. For a single isolated strategy, one rough bridge is to convert adjusted Sharpe to adjusted mean using volatility, then put that mean into a Kelly or robust-portfolio calculation. That bridge does **not** turn the shrinkage estimate into a confidence guarantee.

**Where it can fail in your setting.** The paper’s motivating model treats the vector of Sharpe estimates approximately as noisy Gaussian observations; its simulations use normal returns, and its dependence discussion examines particular correlation structures. [Noise Model](https://www.alphaxiv.org/abs/2606.01650v1?page=2)[Simulation Setup](https://www.alphaxiv.org/abs/2606.01650v1?page=6) If strategies have only a few effective trades, use of calendar bars as $n$ can make the estimated Sharpe noise far too small. Overlapping trades, serial dependence, fat tails, changing regimes, and asset-specific heteroskedasticity all weaken a simple $1/n$ noise model. The paper does not supply a ready-made correction for all of those.

It also assumes you know what candidates belong to the selection pool. If an agent tried thousands of variants, but you apply the correction only to the few promoted strategies, the relevant selection process has been understated. Conversely, pooling unrelated strategies into one grand mean could be a bad shrinkage target. The author recommends James–Stein as a useful general estimator in tested settings, and points to GMLEB when there are known to be only a few good strategies, while calling the study preliminary. [Recommendations](https://www.alphaxiv.org/abs/2606.01650v1?page=29)

**Newer related work.** There is no later paper in the set I found that validates this James–Stein rule specifically for many short-lived, nonstationary retail strategies. Two useful adjacent papers are [**Conformal Kelly: When Marginal Coverage Transfers and the Economics Do Not**](https://arxiv.org/abs/2608.01494) (**2026**) and [**Certified Alpha Capacity: Statistical Arbitrage When Learning Takes Time**](https://arxiv.org/abs/2610.01115) (**2026**). Conformal Kelly challenges the idea that a well-calibrated uncertainty scale automatically makes a good sizing input: its sealed ETF test did not deliver the registered growth or risk-adjusted results, and its aggregate coverage concealed a regime-specific miss. [Conclusion](https://www.alphaxiv.org/abs/2608.01494v3?page=26) Certified Alpha addresses the adjacent question of how much evidence and time are needed to validate signals amid multiple testing and alpha decay; it is a certification framework, not a Sharpe shrinkage estimator or Kelly allocation rule. [Multiple Testing](https://www.alphaxiv.org/abs/2610.01115v2?page=10)

## 2. Integrate uncertainty in the probability model

[**Kelly betting on horse races with uncertainty in probability estimates**](https://arxiv.org/abs/1701.02814) — Michael R. Metel, **2017 preprint / 2018 journal paper**.

**What it does, step by step**

1. Fit a probability model—in the paper, multinomial logistic regression—and estimate uncertainty in its parameters. Metel uses an asymptotic normal parameter distribution built from a sandwich covariance estimate, to allow for model misspecification. [Parameter Uncertainty](https://www.alphaxiv.org/abs/1701.02814v2?page=4)
2. Propagate that uncertainty through the model to obtain uncertain outcome probabilities. For the paper’s logistic-normal case, posterior/parameter draws can be used to estimate mean probabilities by Monte Carlo.
3. Calculate stakes by one of several methods: use the expected probabilities in ordinary Kelly; use a conservative probability construction; or impose a **chance constraint** on expected log wealth over the uncertain probability model.
4. For two outcomes, the chance constraint has a deterministic solution using unfavorable probability quantiles. For many outcomes, the paper samples possible probability vectors and approximates the chance-constrained problem; it describes a heuristic for selecting the worst constraint scenarios. [Two Outcomes](https://www.alphaxiv.org/abs/1701.02814v2?page=7)[Many Outcomes](https://www.alphaxiv.org/abs/1701.02814v2?page=8)

**Inputs and output.** Inputs are the probability-model estimate and its parameter covariance, possible outcomes and their payoffs, plus the chosen constraint level. Output is a set of stakes—one amount per outcome—that maximizes expected log wealth subject to the selected uncertainty treatment. For two-outcome betting, the paper makes the conservative probability adjustment relatively explicit. For many outcomes, output depends on the sampled probability scenarios and approximate chance-constraint solution.

**Where it can fail in your setting.** The paper’s uncertainty model is uncertainty in **outcome probabilities**, not a universal model for noisy P&L edge estimates. Its concrete setup has discrete, mutually exclusive outcomes and fixed odds. A scalper with continuous returns, variable costs, fills, gaps, and correlated simultaneous positions needs a model that represents those factors too. Its normal approximation to parameter uncertainty can be poor with few effective observations; fat-tailed trade returns and a nonstationary edge can invalidate the fitted probability law rather than merely widen its uncertainty. It also does not correct for an agent selecting a strategy after searching many candidates.

A further practical caution: the paper reports that stronger chance constraints can damp growth, and its best overall simulated setting used $\alpha=0.4$—a permissive constraint, corresponding to a relatively weak probability requirement, **not** a recommended deployment threshold for your system. The authors say the constraint needs application-specific calibration. [Simulation Results](https://www.alphaxiv.org/abs/1701.02814v2?page=11)[Conclusion](https://www.alphaxiv.org/abs/1701.02814v2?page=12)

**Newer related work.** [**Tackling estimation risk in Kelly investing using options**](https://arxiv.org/abs/2508.18868) (**2025**) tackles misspecified binomial-market parameters with two option-based Kelly portfolios whose convex combination asymptotically attains the better component’s growth. It is a model-specific alternative hedge, not a general Bayesian posterior-sizing rule; its authors note the asymptotic result need not describe short finite horizons. [Portfolio Mixture](https://www.alphaxiv.org/abs/2508.18868v2?page=14)[Finite Horizon](https://www.alphaxiv.org/abs/2508.18868v2?page=15) Conformal Kelly (**2026**) is another adjacent challenge: it uses interval width as a risk-scale input to capped fractional Kelly, but shows that marginal predictive coverage alone did not ensure good out-of-sample economics in its study. It does not implement Metel’s posterior probability integration. [Method Scope](https://www.alphaxiv.org/abs/2608.01494v3?page=2)

## 3. Optimize for the worst plausible return distribution

[**Distributional Robust Kelly Gambling: Optimal Strategy under Uncertainty in the Long-Run**](https://arxiv.org/abs/1812.10371) — Qingyun Sun and Stephen Boyd, **2018 preprint; revised 2021**.

**What it does, step by step**

1. Represent joint portfolio outcomes as return scenarios. For each proposed allocation $b$, compute log wealth growth in each scenario.
2. Specify an uncertainty set $\Pi$ of plausible probability distributions over those scenarios. The paper gives examples based on probability bounds, norm/ellipsoidal sets, divergence or Wasserstein balls, and uncertainty in estimated mean and covariance.
3. For every allocation, find the distribution in $\Pi$ that gives the lowest expected log growth.
4. Select the feasible allocation that maximizes that worst-case value:
   $$
   \max_{b\in B}\ \inf_{\pi\in\Pi}\mathbb E_\pi[\log(r^\top b)].
   $$
5. Solve the resulting convex optimization problem using a tractable formulation appropriate to the chosen uncertainty set. Its portfolio output is an allocation vector, including cash, rather than a single scalar “Kelly fraction.” [Robust Objective](https://www.alphaxiv.org/abs/1812.10371v3?page=3)[Uncertainty Sets](https://www.alphaxiv.org/abs/1812.10371v3?page=4)[Moment Set](https://www.alphaxiv.org/abs/1812.10371v3?page=6)

**Inputs and output.** You must supply joint outcome returns, feasible portfolio constraints, and a calibrated uncertainty set—its shape and width are substantive inputs. The method hands back the allocation with the best worst-case expected log growth over that set. If the edge is too weak relative to the uncertainty set, a robust solution may hold cash or allocate much less than nominal Kelly. The result depends on whether your uncertainty set actually includes plausible bad states.

**Where it can fail in your setting.** A robust optimizer does not remove model risk: if the uncertainty set is too narrow or omits a regime, its “worst case” can still be optimistic; if it is too broad, it can suppress useful risk-taking. The paper explicitly identifies choosing a useful, efficient uncertainty set as a practical challenge. [Set Choice](https://www.alphaxiv.org/abs/1812.10371v3?page=9) Its theorem uses bounded returns and a specified set of possible distributions. [Bounded Returns](https://www.alphaxiv.org/abs/1812.10371v3?page=6) With few trades, empirical uncertainty sets may be poorly estimated; fat tails may require plausible outcomes beyond historical support; and a nonstationary edge means the uncertainty set must evolve or cover changing regimes. Because it uses joint outcomes, it can represent correlation—but only if your scenarios and uncertainty set retain the relevant cross-strategy dependence. It does not automatically account for repeated agent search or selection bias.

**Newer related work.** Conformal Kelly (**2026**) calls distributional-robust Kelly a natural home for uncertainty sets, but tests a simpler interval-width-based sizing approach instead; its results challenge the assumption that marginal interval coverage is enough to protect economic performance. [Related Work](https://www.alphaxiv.org/abs/2608.01494v3?page=4) The 2025 options paper above also tackles estimation risk, but through option portfolios rather than a worst-case distribution over a retail strategy book. I found no 2025–2026 paper in this search that establishes a validated, ready-made uncertainty-set recipe for a pool of many correlated retail strategies with short trade histories.

## How I would combine them

For your system, a defensible sequence is:

1. **Correct for selection** using the full candidate pool within a comparable strategy family; otherwise a winner’s adjusted Sharpe can still reflect uncounted search.
2. **Estimate uncertainty in expected net edge**, with costs and dependence included. Bayesian integration or confidence-set inference can inform the plausible outcomes, but the probability model must match the strategy.
3. **Optimize the combined live portfolio under uncertainty**, rather than letting each strategy independently spend a fraction of the same $500. Use a joint uncertainty set broad enough to represent correlated losses and regime changes.
4. Apply account-level exposure and loss constraints; require human promotion as planned.

In short: **Pav helps answer “how much of this winning Sharpe may be selection noise?” Metel asks “how do uncertain probabilities change the stakes?” Sun–Boyd asks “what allocation survives the worst plausible model?”** None alone resolves few-trade, fat-tail, nonstationary edge estimation; those are the assumptions your validation and uncertainty-set design must explicitly handle.


