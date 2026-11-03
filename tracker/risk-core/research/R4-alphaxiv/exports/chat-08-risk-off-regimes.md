<!-- alphaXiv chat export via the page's Chat actions > Copy Markdown, saved 2026-11-03. Chat URL: https://www.alphaxiv.org/assistant/01a1a157-c49d-7fe5-bebb-1080ee14a39d -->

# Chat Transcript: Intraday Risk\-Off Regime Detection and Contagion Methods

## User

Context: a retail multi-strategy trading system. Many small automated strategies (scalpers, intraday) trade around the clock across FX, indices, metals, energy, crypto, futures and stocks from one $500 account. Agents propose strategies but never touch money; a human promotes strategies to live. Topic (only this one): detecting risk-off regimes and correlation breakdowns early enough to isolate or cut one asset class or region. Absorption ratio (Kritzman), financial turbulence (Mahalanobis), correlation-surprise, regime-switching and hidden Markov models, and recent ML or graph methods for regime and contagion detection that run on intraday data. Newest 2025-2026 work first, then the classics. Give titles, years, arXiv links, the inputs each method needs, its lead time, and concrete recommendations.

## Aurelle

**No paper in this set establishes a dependable “minutes ahead” warning for an intraday retail system.** The newer papers mostly propose or study regime indicators; their abstracts do not report an operational lead time. Treat these as candidate signals to test, not as evidence that a detector will reliably anticipate a selloff.

### Newer work (2025–2026)

| Paper | Inputs the method needs | Lead time reported |
|---|---|---|
| [*Regimes in the Order Flow*](https://www.alphaxiv.org/abs/2609.07989) (2026) | Intraday order-flow data; the paper focuses on detecting structural breaks in order-flow regimes. | No numerical warning horizon surfaced; structural-break detection may be contemporaneous with a change. |
| [*Lower Spectrum of Financial Correlation Matrices: A New Perspective on Market Synchronization*](https://www.alphaxiv.org/abs/2608.09641) (2026) | A rolling cross-asset correlation matrix and its lower eigenvalue spectrum. | No numerical lead time reported; synchronization is a regime indicator, not by itself a forecast. |
| [*ORCA — Online Regime Correlation Analyzer*](https://www.alphaxiv.org/abs/2604.17251) (2026) | Online cross-asset correlation structure, represented as a network. | No numerical lead time reported in the available abstract. |
| [*Systemic Risk Surveillance*](https://www.alphaxiv.org/abs/2601.08598) (2026) | Systemic-risk indicators monitored over time; the abstract describes surveillance schemes but does not specify a single intraday input set. | Not quantified in the available abstract. |
| [*Systemic Risk Radar: A Multi-Layer Graph Framework for Early Market Crash Warning*](https://www.alphaxiv.org/abs/2512.17185) (2025) | Multiple interacting network layers; the abstract frames the target as evolving links across sectors, markets, and investor behavior. | “Early warning” is the stated goal, but no numerical lead time is available in the returned summary. |
| [*Modeling Regime Structure and Informational Drivers of Stock Market Volatility via the Financial Chaos Index*](https://www.alphaxiv.org/abs/2504.18958) (2025) | The abstract describes a tensor- and eigenvalue-based index using realized-volatility information. | No numerical intraday warning horizon reported. |
| [*Detecting Changes in Asset Co-Movement Using the Absorption Ratio*](https://www.alphaxiv.org/abs/2002.02008) (2020) | A panel of asset returns; principal components summarize how much of total variance is absorbed by common factors. | The paper proposes a real-time indicator of temporary co-movement increases; a dependable number of minutes ahead is not established here. |

### Classics and baseline methods

| Method / paper | Inputs it needs | What “lead time” means in practice |
|---|---|---|
| [*Principal Components as a Measure of Systemic Risk*](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1633027) (2010), the absorption-ratio foundation | A rolling panel of returns, a covariance/correlation estimate, and principal-component eigenvalues. | A rise can flag tighter coupling, but it is a rolling-window statistic: the lookback and update frequency govern responsiveness. It is not a guaranteed advance warning. |
| [*Correlation Surprise*](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2133396) (2012; subsequently published in 2013) | Asset returns plus a baseline covariance model, so unusual correlation changes can be distinguished from unusual return magnitudes. | Usually contemporaneous with a dependence shift; no dependable forward horizon should be assumed. |
| Financial turbulence / Mahalanobis-distance approach, associated with Kritzman and Li (2010) | Current multi-asset return vector, historical mean vector, and covariance matrix. | A large distance flags an unusual joint move as it happens. It is best treated as a fast anomaly detector, not a pre-crash predictor. |
| Hamilton’s Markov-switching model (1989) and later HMM applications | A time series of observations or features—e.g., returns, volatility, or correlation summaries—and an emission/transition model. | Filtered state probabilities update as observations arrive; detection can lag a transition. A smoothed state uses future observations and is therefore unsuitable as a live warning. |

### Recommendations for your system

1. **Use complementary signals, not one master “risk-off” score.** Put Mahalanobis turbulence and correlation surprise in the fast layer; use absorption ratio and graph/eigenvalue measures as slower confirmation. A turbulence spike says “unusual joint move now”; a rising absorption ratio says “assets are becoming more coupled.” Neither alone proves that a particular class should be cut.

2. **Make the action local.** Compute risk and exposure by asset class and region, then reduce or pause only the implicated bucket when its own stress signal fires. Also keep a portfolio-wide emergency limit for a genuinely broad shock. Aggregate all strategies’ live exposure before making either decision.

3. **Use a one-sided, live HMM probability.** If you test an HMM, act on filtered probabilities available at that timestamp—not smoothed labels, which leak future data into historical results. Compare it against simple threshold baselines; added model complexity is only useful if it improves out-of-sample warning and drawdown control.

4. **Design for noisy, asynchronous markets.** Use synchronized return intervals, stale-price checks, and a minimum-observation rule. For covariance-based signals, test shrinkage and robust estimates; otherwise a small or changing universe can make the inverse covariance unstable. Treat a data-quality failure as “risk state unknown,” not “safe.”

5. **Set warnings by measured utility, not a promised lead time.** Backtest walk-forward at the actual decision cadence, including spread, slippage, and the fact that FX, stocks, futures, and crypto have different sessions. Measure false-trigger rate, missed stress episodes, and drawdown avoided at fixed exposure—not just regime-classification accuracy. For a $500 account, conservative position caps and a simple class-level pause rule may matter more than a high-dimensional detector.

6. **Keep deployment human-gated.** Have agents propose and score detectors offline; promote only after a paper-trading period and a predeclared test. A warning should trigger a bounded exposure reduction or pause, not let an agent move money or silently rewrite live risk limits.

## User

Follow-up 1: Pick the three methods or papers that matter most for this system, from any year (strongest work, classics included). For each one: what exactly it computes, step by step; its inputs and outputs (which prices or returns, which window and frequency, what score or regime label it hands back); its realistic lead time before a sell-off; where it fails (false alarms in calm markets, lag, crypto trading 24/7 while stock markets close, few assets per class); and which later papers build on it or challenge it, with links. Then: how would you turn its output into a rule that isolates one asset class or region (for example cut crypto only, or cut Asian session index strategies only) rather than the whole book?

## Aurelle

**For this system, I’d prioritize the Autoencoder Reconstruction Ratio (ARR), correlation surprise, and financial turbulence—in that order for detecting co-movement changes, distinguishing correlation breaks from extreme moves, and flagging unusual joint shocks.** One correction to my previous answer: arXiv [2002.02008](https://arxiv.org/abs/2002.02008) is *Detecting Changes in Asset Co-Movement Using the Autoencoder Reconstruction Ratio*, not the original absorption-ratio paper. The original [*Principal Components as a Measure of Systemic Risk*](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1633027) is available via SSRN, not arXiv.

None of these methods has been shown to give this kind of retail system a dependable, instrument-independent warning **minutes** before a sell-off. The most defensible live use is to flag deteriorating conditions and reduce exposure in the affected bucket—not to treat a score as a crash countdown.

### 1. Autoencoder Reconstruction Ratio (ARR)

The paper is [*Detecting Changes in Asset Co-Movement Using the Autoencoder Reconstruction Ratio*](https://arxiv.org/abs/2002.02008) (2020). It adapts the absorption-ratio idea: when a low-dimensional model can explain a basket of assets’ returns with little residual error, those assets are moving together more tightly. **ARR is the normalized reconstruction error, so a *lower* ARR means stronger co-movement.** Under the paper’s linear-factor assumptions, ARR is approximately one minus the absorption ratio. [ARR Definition](https://www.alphaxiv.org/abs/2002.02008?page=3)

**What it computes, step by step:**

1. Form a synchronized return vector across the assets in a basket. The paper uses log returns, trained its autoencoder on **one-second** returns, and includes time of day as an input.
2. Encode that vector into a smaller set of latent factors and reconstruct the returns from those factors.
3. Over the chosen interval, sum the squared reconstruction residuals and divide by the sum of squared observed returns. This normalized error is ARR.
4. Compare the result to its own trailing distribution. The paper does not give a universal threshold that means “risk-off”; that cutoff has to be calibrated for the universe and frequency.

The paper reports ARR at **5-minute, 1-hour, daily, and weekly** aggregation frequencies. It finds that including ARR improved some **5-minute and 1-hour** volatility and crash forecasts, but that is evidence of predictive information at those forecast horizons—not proof of a fixed lead time before a sell-off. [Short-Horizon Results](https://www.alphaxiv.org/abs/2002.02008?page=7)

**Realistic lead time and failure modes:** Treat ARR as a short-horizon warning or confirmation signal, not an early-warning clock. The study’s empirical basket was 11 US equity-sector indices. A model trained on many sector series does not automatically transfer to a bucket with only two or three crypto instruments. With few assets, the learned “common structure” can be noisy or brittle; with assets that trade different hours, stale or missing prices can create artificial residuals or apparent co-movement. A model trained on one-second US equity data also needs a fresh validation before applying it to FX, futures, metals, or 24/7 crypto.

**How it builds on and differs from earlier work:** ARR explicitly replaces PCA in the classic [absorption ratio](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1633027) with a nonlinear autoencoder. The original ratio is easier to explain and train; ARR is designed to better capture nonlinear return structure, at the cost of training and validation complexity.

### 2. Correlation surprise

[Kinlaw and Turkington’s *Correlation Surprise*](https://link.springer.com/article/10.1057/jam.2013.27) (2013) decomposes the financial-turbulence score into an overall unusual-move measure and a measure of whether assets moved together in an unusual way.

**What it computes, step by step:**

1. Build a return vector $y_t$ for the selected assets, along with a historical mean vector $\mu$ and covariance matrix $\Sigma$.
2. Compute **turbulence**, a normalized Mahalanobis distance:  
   $$T_t = \frac{(y_t-\mu)^\top \Sigma^{-1}(y_t-\mu)}{N}$$
3. Compute **magnitude surprise** using the same returns and historical means and volatilities, but ignore cross-asset covariance. Equivalently, it is the average of the assets’ squared standardized return surprises.
4. Divide turbulence by magnitude surprise:  
   $$CS_t = \frac{T_t}{MS_t}$$
   A value above 1 indicates that the joint pattern is more unusual than the individual return magnitudes alone suggest. It can reflect assets that usually move together diverging, or assets that usually do not move together converging.

The original study uses **daily** data and long historical lookbacks—10 years for its equity universes and 3 years for currencies—so neither those windows nor the study’s thresholds should be assumed to work as-is on intraday bars. The paper’s strongest practical signal is *joint*: high magnitude surprise plus correlation surprise above 1. It reports that, after selecting the top 20% of magnitude-surprise days, the next day’s magnitude surprise was higher when correlation surprise exceeded 1; this difference was statistically significant at the reported levels for the three tested universes. Its analysis also found that the signal’s effect could decay quickly—one example’s difference narrowed over days 2–5. **That supports testing for roughly next-day information in those data, not claiming minutes of advance warning.**

**Realistic failure modes:** CS can spike when returns are tiny and noisy, so the paper itself filters to high magnitude-surprise observations in key tests. Its ratio can also become unstable when magnitude surprise is near zero. At intraday frequencies, asynchronous sessions matter: a closed stock market is not a zero-return observation, and crypto continuing to trade does not make a stale equity price a valid synchronized return. Small asset groups also make covariance estimates unreliable.

**How it builds on and differs from earlier work:** It extends [*Skulls, Financial Turbulence, and Risk Management*](https://doi.org/10.2469/faj.v66.n5.3) (2010) by separating magnitude and correlation contributions. In a useful contrast, turbulence can flag a statistically extreme joint move even when correlations have not changed; CS can highlight an unusual dependence pattern that may be missed by looking at return magnitude alone.

### 3. Financial turbulence / Mahalanobis distance

The foundational reference is [*Skulls, Financial Turbulence, and Risk Management*](https://doi.org/10.2469/faj.v66.n5.3) (2010). It computes how unusual the current **joint** return vector is relative to a historical multivariate distribution, taking both individual return scales and cross-asset covariance into account.

**What it computes, step by step:**

1. Select a universe, such as several crypto assets or a set of regional index futures.
2. For each observation, form the return vector $y_t$; estimate its historical mean $\mu$ and covariance matrix $\Sigma$ from a reference window.
3. Calculate the normalized Mahalanobis distance, $T_t$ above. Larger values mean the current cross-section is more unusual.
4. Optionally smooth the score or compare it with a trailing percentile threshold to generate an alert. **The score itself is continuous, not a built-in regime label.**

The 2010 paper used multiple frequencies and universes; for one exposure-scaling example it used a **30-day moving average** of turbulence and **trailing three-year** quintiles to scale a currency carry strategy. That paper explicitly cautions that turbulence does **not** reliably anticipate the initial arrival of an extreme event; it is more useful for characterizing risk and responding once stress appears. It also reports persistence after turbulence begins. [Limits of Warning](https://www.alphaxiv.org/abs/https://www.top1000funds.com/wp-content/uploads/2010/11/FAJskulls.pdf?page=7)

**Realistic lead time and failure modes:** Treat raw turbulence as a **nowcast**—“this joint move is unusual”—not a forecast of when the next sell-off will start. It can false-alarm on unusual but harmless asset-specific news, and a high score can be caused by large returns even if the dependence structure is not the issue. Covariance inversion is especially fragile with few assets, short windows, stale prices, or changing membership. The paper’s own exposure-scaling example applies a 30-day smoothing window and a one-day implementation lag, which is far slower than an intraday trigger.

**How it builds on and differs from later work:** Correlation surprise is the direct decomposition that helps explain *why* the turbulence score is high. Use it alongside turbulence rather than mistaking every turbulence spike for contagion.

### Turning the scores into bucket-specific controls

Use the **same broad process**, but calculate signals for target buckets separately—for example, crypto, metals, or Asian-session index strategies. Each bucket needs a return panel of its own, constructed from synchronized, valid observations; also maintain a separate whole-book score for genuinely broad stress.

As a starting design to test—not a threshold validated by these papers:

- Normalize each bucket’s score to its own trailing, time-of-day-aware distribution. Use a **high-percentile alert** rather than a fixed raw number; thresholds should be tested walk-forward with realistic spreads and slippage.
- For a **crypto-only** reduction, require a local crypto warning—for example, unusually low crypto ARR or high crypto turbulence—and, when enough liquid crypto instruments exist, confirmation from crypto correlation surprise. Do **not** cut all classes just because one crypto asset printed an extreme return.
- For an **Asian-session index-only** reduction, calculate the signal from instruments that actually trade in that session. Do not fill closed US or European markets with zero returns to create an apparently synchronized global panel.
- On a bucket alert, first block new entries from that bucket and reduce its aggregate open risk by a pre-approved amount; on stronger or persistent stress, pause that bucket’s strategies. Leave unaffected buckets running unless the separate whole-book control fires.
- For 24/7 crypto, use UTC-aligned bars and an explicit stale-price / missing-data rule. For small buckets, don’t trust a covariance inverse or fit a deep autoencoder to two instruments; use a broader liquid proxy basket, shrinkage, or a simpler return-and-correlation rule until there is enough data.
- Evaluate false triggers, missed sell-offs, and drawdown avoided—not just regime-label accuracy. Have a human approve the thresholds and live action limits before promotion; the detector should not let an agent change them.

The practical combination I’d test first is **bucket-level turbulence for an unusual-move alarm, correlation surprise to identify dependence dislocations, and ARR as a slower co-movement confirmation where the bucket has enough clean data**. None should override hard position and loss limits or a separate portfolio-wide emergency control.

## User

Follow-up 2, two parts. (1) Asset classes: how should regime and correlation-breakdown detection differ across FX, stock indices, metals, energy, crypto, futures and single stocks (trading sessions and closes, 24/7 crypto, weekend gaps, leverage and margin, volatility, typical cross-asset correlations in stress, contract rolls, data quality)? Give the differences per class and which cross-asset links matter most for isolating each class. (2) Combinations: what would the best methods here combine with from other parts of this system: sizing under an uncertain edge (Bayesian or fractional Kelly), live alpha-decay detection (e-values, change points), drawdown-controlled sizing, breadth and effective number of bets, risk allocation across strategy clusters (HRP), kill switches and circuit breakers, stop and exit design, safe de-risking and re-risking (conservative bandits, safe RL), news and macro event windows, stress scenarios, LLM agents for macro and news monitoring? Name concrete pairs or triples of papers with links, what the combined method would do, and why.

## Aurelle

**Use market-specific clocks and data rules, but one common risk governor:** detect stress within each asset/session bucket, reduce only that bucket first, and let a separate portfolio-wide limit handle genuinely systemic shocks. Don’t calculate a “global” correlation matrix by treating closed markets as unchanged markets.

## 1. How detection should differ by asset class

| Asset class | Clock, market structure, and main data hazards | Useful stress links for deciding whether to isolate this bucket |
|---|---|---|
| **FX** | It trades nearly 24/5, not 24/7: liquidity and spreads change across Asia, Europe, and New York, and the week opens with a gap after the weekend. Use session-aware returns and spreads; distinguish a quiet session from stale or thin quotes. Leverage makes small price gaps material. | Monitor the pair’s other side and related currencies, broad USD, rates, and risk-sensitive assets. A broad USD/rates shock may affect many FX strategies; a divergence confined to one currency or session is a case for local reduction. |
| **Stock indices** | Cash indices have exchange hours, holidays, auctions, and overnight gaps; index futures trade longer but still have maintenance breaks and session-specific liquidity. Separate overnight from regular-session returns and never fill a closed cash index with zero. | Check related regional indices, index futures, volatility proxies, rates, credit/risk proxies, and relevant currencies. If only one region’s cash/futures complex is dislocated, restrict that region or session rather than all equity strategies. |
| **Metals** | Distinguish precious metals from industrial metals: their drivers and stress links differ. Futures have session breaks, delivery months, rolls, and sometimes thinner hours. Spot/CFD feeds can differ in timestamps and rollover conventions. | For gold, check USD and real-rate proxies; for industrial metals, also check energy, broader commodities, and manufacturing-sensitive assets. If gold alone decouples while the rest of the book is normal, isolate precious metals—not “commodities” as a whole. |
| **Energy** | Often the most contract-specific bucket: oil and gas have different seasonality, inventories, local benchmarks, and delivery risks. Exchange hours, price limits, thin contracts, and futures rolls can produce jumps that are not a general risk-off regime. Use liquid contracts, spreads, and roll-aware continuous series; keep actual tradable contract prices for execution risk. | Compare related benchmarks, calendar spreads, other energy products, USD, and broad inflation/risk indicators. A front-month squeeze or roll dislocation should usually disable the affected contract or strategy cluster, not every asset class. |
| **Crypto** | Trades 24/7, including weekends when many traditional markets are shut. Exchange outages, thin books, liquidation cascades, funding/basis, and venue-specific prices matter; margin can be liquidated before a slower regime signal updates. Use venue-quality checks and separate spot, perpetual, and dated-futures signals. | Check BTC/ETH and other liquid crypto assets, cross-venue prices, funding/open-interest or basis where reliable, and—only during overlapping hours—equity/risk proxies. Weekend crypto stress is a warning to review Monday exposure, not proof that a closed equity market has already moved. A recent candidate on this question is [*Weekend Crypto Volatility and Monday Market Risk*](https://www.alphaxiv.org/abs/2610.35702); treat it as a research lead, not an established operating rule. |
| **Futures** | “Futures” is a contract form, not one risk class. Add contract expiry, roll, tick size, price limits, settlement, overnight margin, and calendar-spread behaviour to the underlying’s risk model. Use actual-contract and roll-adjusted series for different purposes; don’t mistake a synthetic-roll jump for contagion. | Compare the contract with its underlying cash/spot market, related contracts and calendar spreads, plus cross-asset hedges relevant to that underlying. If a basis or roll breaks while the underlying basket is orderly, cut the contract/strategy, not the whole underlying class. |
| **Single stocks** | Earnings, halts, corporate actions, splits, dividends, borrow, and overnight gaps dominate some risk. A single name is not a stable “asset class” correlation panel. Validate adjusted prices and corporate-action data; treat halts and stale prints as data/risk events, not flat returns. | First compare the stock with its sector/index, close peers, and its own liquidity/volatility; use options-implied risk only if the feed is reliable. A one-name event calls for a name-level or strategy-level cut. Broader sector deterioration may justify reducing the sector cluster. |

Across classes, use **active, overlapping observations** for cross-asset correlation. When markets do not overlap, either compare separately defined session returns or use a deliberate lead–lag model; do not manufacture synchronous returns from stale prices. Use robust/shrinkage covariance estimates, require enough observations for the number of assets, and make “data unreliable” a distinct state from “market calm.”

## 2. Combinations that fit this system

The core combinations below are risk overlays, not new agents authorized to trade. The risk service should turn their outputs into bounded exposure changes; strategy agents can propose tests, but a human promotes the rule.

**A. Local contagion trigger: ARR + correlation surprise + turbulence.**  
Pair [*Detecting Changes in Asset Co-Movement Using the Autoencoder Reconstruction Ratio*](https://arxiv.org/abs/2002.02008), [*Correlation Surprise*](https://link.springer.com/article/10.1057/jam.2013.27), and [*Skulls, Financial Turbulence, and Risk Management*](https://doi.org/10.2469/faj.v66.n5.3). ARR summarizes whether a basket is becoming more tightly explained by common factors; correlation surprise asks whether the joint direction is unusual given individual return magnitudes; turbulence flags an unusual joint move. The ARR paper reports information for short-horizon risk forecasts, but its equity-sector evidence does not establish a universal intraday lead time. [Short-Horizon Results](https://www.alphaxiv.org/abs/2002.02008?page=7)

**Combined action:** if crypto turbulence is high *and* its dependence structure is abnormal, block new crypto entries and reduce crypto risk in steps. If only one crypto instrument is extreme, cut that instrument/strategy cluster first. If Asian-session index stress is local to that session, gate those strategies only. Use whole-book contagion as a separate, higher-severity condition. For small baskets, skip the autoencoder and rely on a simpler, validated rule.

**B. Edge uncertainty + live alpha decay + exposure cap.**  
Pair a conservative fractional sizing policy such as [*Conformal Kelly: When Marginal Coverage Transfers and the Economics Do Not*](https://www.alphaxiv.org/abs/2608.01494) with a sequential change detector such as the classical [Page CUSUM paper](https://doi.org/10.1093/biomet/41.1-2.100), then feed the resulting *strategy-level* risk multiplier into the contagion gate above. CUSUM can flag that the strategy’s realized residual P&L or hit rate has shifted; conservative fractional sizing prevents a noisy edge estimate from translating into an outsized bet. Conformal coverage is not itself proof that an edge is profitable, so size from validated net returns after costs, not an LLM’s confidence or a prediction interval alone.

**Combined action:** lower a strategy’s allowed risk when its own alpha decays, even if its asset class is calm; lower a whole bucket only when bucket-level stress also fires. Use a hard maximum position and loss budget independent of either model.

**C. Drawdown control + cluster-aware risk allocation.**  
Combine the risk-control framing in [*On Control of Drawdown: Robust Invariance and Optimality*](https://www.alphaxiv.org/abs/2609.23272) with hierarchical risk parity (HRP), described in [*Building Diversified Portfolios that Outperform Out of Sample*](https://doi.org/10.3905/jpm.2016.42.4.059). HRP helps avoid treating many highly correlated scalpers as many independent bets; the drawdown controller limits portfolio exposure as equity falls from its peak. Recompute clusters from strategy P&L and exposures—not just instrument labels—because different strategies on the same market may share the same failure mode.

**Combined action:** cap risk by cluster, then apply the portfolio drawdown multiplier and local regime multipliers. A drawdown breach should reduce risk across the book as required; a local stress flag should reduce only the affected cluster. With a $500 account, absolute loss caps and margin headroom are more important than optimizing fractional weights finely.

**D. Safe de-risking and re-risking: deterministic governor first, learning second.**  
Use [*Risk-Aware Deep Reinforcement Learning for Dynamic Portfolio Optimization*](https://arxiv.org/abs/2511.11481) as a candidate for studying adaptive exposure, but wrap any learned suggestion in a deterministic risk governor: hard class/cluster limits, margin limits, stale-data blocks, and a kill switch. The model may recommend moving from full to reduced risk; it should not control the kill switch or relax limits. Re-risk only after stress signals normalize for a predeclared persistence period and execution/data quality recover. For this small account and human promotion process, a few fixed exposure states are easier to audit than a continuously exploring policy.

**E. News/event monitoring + price confirmation + safe execution.**  
Use macro calendars and timestamped news to define *event windows* and expected gap/liquidity scenarios; use market data to decide whether the event is actually moving the relevant bucket. LLMs can summarize source-linked headlines and propose affected instruments, but should not set the score threshold or fire a live cut by themselves. The recent [*Trading Agents or Market Crashers? Dissecting Robustness and Security Failures in Academic Financial LLM Trading Schemes*](https://www.alphaxiv.org/abs/2609.19705) and [*Execution Realism and Reproducibility in LLM-Based Trading Systems*](https://www.alphaxiv.org/abs/2606.08285) are useful cautions when evaluating that layer.

**Combined action:** before a scheduled event, optionally lower risk in exposed clusters according to a human-approved event table; during the event, use spread, liquidity, and price checks to avoid sending exits into a bad or stale market. A headline alone should not trigger indiscriminate liquidation.

### A practical decision sequence

1. **Validate the feed and market clock.** If prices are stale, a venue is unavailable, or a contract is rolling, mark the bucket *unknown* and block new entries there.
2. **Check local strategy and bucket risk.** Alpha decay reduces that strategy’s exposure; local turbulence/dependence breakdown reduces the implicated bucket or session.
3. **Check portfolio limits.** Apply cluster concentration, aggregate margin/headroom, and drawdown controls; broad stress can override local gating.
4. **Execute safely.** Prefer staged reduction within the allowed risk budget; handle exchange halts, price limits, and thin books explicitly rather than assuming a stop always fills.
5. **Re-risk slowly.** Require both market normalization and data/execution recovery; restore exposure in capped steps, with human review for material changes.

The useful distinction is: **alpha decay says “this strategy may no longer have an edge”; regime stress says “this market bucket is behaving abnormally”; drawdown control says “the whole account has less loss capacity.”** Keeping those signals separate is what allows the system to isolate crypto, a region, a contract, or one failing strategy instead of reflexively shutting down the entire book.

