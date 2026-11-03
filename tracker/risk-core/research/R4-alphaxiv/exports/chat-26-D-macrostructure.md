<!-- alphaXiv chat export via the page's Chat actions > Copy Markdown, saved 2026-11-03. Chat URL: https://www.alphaxiv.org/assistant/01a1a169-b23b-7bd3-b50c-58860a448b51 -->

# Chat Transcript: Macro Regimes and Trading Risk

## User

Context: a retail multi-strategy trading system. Many small automated strategies (scalpers, intraday) trade around the clock across FX, indices, metals, energy, crypto, futures and stocks from one $500 account. Agents propose strategies but never touch money; a human promotes strategies to live. Topic (only this one): market macrostructure, meaning regimes, cross-asset links and macro drivers (rates, the US dollar, risk appetite, commodities, liquidity and volatility cycles), and how they should feed risk limits for a book of short-horizon strategies. Cover regime classification from macro and cross-asset data, shifts in cross-asset correlation (stock-bond, USD as a risk factor, crypto-equity link, commodity shocks), volatility regimes and term structure, factor models for multi-asset books, and how to translate a macro state into exposure caps, per-class limits or turning strategies on and off. Give the strongest work from any year, classics included, with titles, years, links and concrete recommendations.

## Aurelle

For a $500 book of short-horizon strategies, macro state should act as a **shared risk governor**, not as a standalone entry signal: it changes how much risk the book may carry and which exposures are allowed, while each strategy still has to earn its place on its own.

### Strong foundations

| Paper | Why it matters here |
|---|---|
| [“A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle” (1989)](https://doi.org/10.2307/1912559) | James Hamilton’s classic Markov-switching framework: a foundation for modeling discrete, persistent regimes rather than assuming markets have one stable behavior. |
| [“International Asset Allocation With Regime Shifts” (2002)](https://doi.org/10.1093/rfs/15.4.1137) | Shows why portfolio decisions should account for changing regimes and their different return and risk distributions. |
| [“The Determinants of Stock and Bond Return Comovements” (2010)](https://doi.org/10.1093/rfs/hhp069) | Useful for treating stock–bond correlation as time-varying and economically conditioned—not as a permanent diversification property. |
| [“Common Risk Factors in Currency Markets” (2011)](https://doi.org/10.1016/j.jfineco.2010.10.003) | Identifies broad currency risk factors, supporting the view that FX positions can share exposures even when they involve different currency pairs. |
| [“Not All Oil Price Shocks Are Alike” (2009)](https://doi.org/10.1257/aer.99.3.1053) | Distinguishes oil-supply shocks from demand-driven price moves—a useful reminder that the same commodity return can imply different macro risks. |
| [“Dynamic Conditional Correlation: A Simple Class of Multivariate GARCH Models” (2002)](https://doi.org/10.1198/073500102288618487) | A standard framework for estimating correlations that evolve over time, relevant to detecting when diversification across strategies is weakening. |
| [“A Simple Long Memory Model of Realized Volatility” (2009)](https://doi.org/10.1093/jjfinec/nbp001) | Introduces HAR-RV, a practical way to combine short-, medium-, and longer-horizon realized volatility signals. |
| [“Volatility-Managed Portfolios” (2017)](https://doi.org/10.1111/jofi.125) | Supports reducing exposure when volatility rises, rather than leaving strategy size fixed across volatility environments. |
| [“Value and Momentum Everywhere” (2013)](https://doi.org/10.1111/jofi.12021) | A cross-asset perspective on shared style factors: strategies in different markets may still concentrate in common exposures. |
| [“Honey, I Shrunk the Sample Covariance Matrix” (2004)](https://doi.org/10.3905/jpm.2004.110) | A practical foundation for shrinkage covariance estimation, which can be more stable than raw sample correlations in a noisy, multi-asset book. |

These classics are more useful for designing the risk layer than newer papers that propose a particular regime detector or portfolio optimizer: they address the underlying problems of regime change, unstable dependence, volatility clustering, and shared factors.

### Turning macro and cross-asset data into a risk state

Use a small number of interpretable features, measured at more than one speed:

- **Macro backdrop:** growth and inflation surprises, policy-rate expectations, real yields, and yield-curve slope.
- **Cross-asset stress:** broad USD movement, credit spreads if available, equity trends, and commodity moves—especially energy.
- **Volatility and liquidity:** realized volatility at several horizons, implied volatility where available, volatility term structure, spread/slippage measures, and gaps or jumps.
- **Dependence:** rolling or shrinkage correlations, plus exposure to common factors such as equity risk, duration, USD, energy, and crypto/equity risk.

A practical first version need not be a sophisticated machine-learning model. Define a few states—such as **calm expansion, inflation/rates stress, growth-risk-off, and liquidity/volatility shock**—from transparent features, then estimate state probabilities with a Markov-switching model or use robust threshold rules. Use probabilities or a gradual score, not a brittle label that flips on one observation. Apply hysteresis and require confirmation before changing the risk budget.

Keep the data point-in-time correct: macro releases must enter only when they were actually published, and regime features should be lagged to match when the strategies could have observed them. Otherwise a convincing backtest can be an artifact of look-ahead.

Cross-asset relationships need interpretation, not just correlation tracking. Bonds may diversify equities during a growth scare but fail to do so during an inflation or rate shock. USD strength can reflect safe-haven demand, higher relative rates, or funding stress; it should not be treated as a universal “risk-off” switch. Crypto may behave like a high-beta equity exposure in some selloffs, but that link is not stable enough to assume it always will. Oil and other commodities can transmit a supply shock that raises inflation risk even while growth assets weaken.

For volatility, distinguish **level** from **structure**. A high but easing volatility level is different from volatility rising sharply with the front end of the curve above deferred maturities. Track each market’s own realized volatility and, where liquid and relevant, its implied-volatility term structure; an equity volatility index is not a universal volatility gauge for FX, commodities, or crypto.

### Translate state into book controls

Estimate total risk at the **book level**, not by adding each agent’s standalone risk limit. Map every position to common risk units and factors: for example, convert contracts or lots to notional or delta-adjusted exposure, account for quote currency, and aggregate related instruments. Use a regularized covariance model for ordinary conditions, but supplement it with explicit stress scenarios—correlations often rise precisely when a historical covariance estimate is least dependable.

Then let the macro state modify a small set of controls:

| State signal | Practical response |
|---|---|
| Calm conditions; contained realized vol; ordinary correlations | Permit the normal book risk budget, subject to per-strategy and per-class caps. |
| Rates or inflation shock; stock–bond diversification weakening | Reduce combined equity and duration exposure; tighten limits on strategies that depend on bonds hedging equities. |
| Broad risk-off or USD/funding stress | Reduce aggregate risk across equities, high-beta FX, and crypto together; do not count their separate strategy limits as independent diversification. |
| Commodity supply shock | Tighten energy and inflation-sensitive exposure, and reassess correlated FX and index positions rather than treating the commodity trade as isolated. |
| Volatility rising, front end of vol curve elevated, or liquidity deteriorating | Scale gross exposure down, reduce simultaneous positions and leverage, and disable strategies whose expected edge depends on normal spreads or continuous fills. |
| State uncertain or data disagree | Use an intermediate, reduced risk budget; uncertainty is a reason to limit risk, not to force a confident regime label. |

For short-horizon agents, implement those responses as **hard shared caps**: total book risk, per-asset-class risk, common-factor risk, and maximum concentration in correlated strategies. Add a per-strategy loss or drawdown stop, and a book-level loss stop that pauses new risk. Strategies can be switched off when their risk-adjusted edge degrades in a state, but avoid letting an unvalidated classifier turn the entire system on and off from one noisy signal. A graduated size reduction is generally safer than a binary switch.

With only $500, the most important constraint may be operational rather than statistical: minimum contract sizes, leverage, spreads, funding, and slippage can make a nominally diversified portfolio effectively concentrated. Keep the initial live book small enough that a single gap or correlated loss cannot consume a large fraction of capital; promote strategies one at a time, with a human reviewing their live exposure and the combined book risk before raising limits.

## User

Follow-up 1: Pick the three papers or methods that matter most for turning macro and cross-asset state into risk limits for this book, from any year. For each one: what exactly it computes, step by step; its inputs and outputs (which macro or market series, at what frequency, and what state, score or limit it hands back); its realistic lag or lead; where it fails (regime labels that change after the fact, short intraday horizons, crypto with little macro history, data revisions, structural breaks such as rate-regime changes); and which later papers build on it or challenge it, with links. Then: give a concrete mapping from a macro state to exposure caps per asset class that a deterministic risk service could apply, and say how often the state should be recomputed.

## Aurelle

The most useful three-part design is **Hamilton-style filtered regime probabilities + DCC-style conditional covariance + volatility scaling**. They answer different questions: *what broad state are we in?*, *are the strategies still diversifying one another?*, and *how much smaller should the book be as risk rises?* None produces a trustworthy “risk-on” label that predicts the next few minutes.

### 1. Hamilton: estimate a probability of a persistent macro regime

**[“A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle” (1989)](https://doi.org/10.2307/1912559)** models an unobserved state that changes the behavior of an observed economic series.

1. Choose a macro series or a small set of indicators. Hamilton’s original application used **quarterly US real GNP growth**; a live implementation might use published growth and inflation surprises, yield changes, and credit or market-stress indicators.
2. Specify a small number of latent states, each with different return or growth dynamics, and a Markov transition matrix governing the probability of moving between them.
3. For each new observation, calculate how likely it is under each state.
4. Update the state probabilities using those likelihoods and the previous period’s probabilities.
5. Hand the risk service the **filtered probability vector**—for example, \(P(\text{stress}_t\mid\text{data observed through }t)\)—rather than a hard label. Use the filtered probability in production; a smoothed probability uses later observations and can revise the apparent past.

**Frequency and timing.** The original economic application was quarterly. Market inputs can be sampled daily or more often, but the macro releases themselves do not become more current just because the model runs every minute. GDP, inflation, and employment releases arrive with publication lags and may later be revised. A release surprise is available at publication; the underlying economic condition is not observed in real time. The model estimates a persistent state; it does not forecast the next intraday move.

**Where it fails.** States can be hard to interpret, and smoothed historical labels can make regime changes look cleaner and earlier than they were live. A model fitted to a particular rate and inflation era can misclassify a new one. It can also overreact to noisy or revised macro data. For crypto, there is too little long macro history to fit a dependable asset-specific macro-state model; use macro context as a shared overlay, and let crypto’s own realized risk and cross-asset dependence drive its short-horizon limits.

**Later work.** [Filardo’s “Business-Cycle Phases and Their Transitional Dynamics” (1994)](https://doi.org/10.1080/07350015.1994.10524545) extends the setup with transition probabilities that can depend on explanatory variables, allowing transition risk to vary with the macro environment. [Hamilton’s “Calling Recessions in Real Time” (2011)](https://doi.org/10.1016/j.ijforecast.2010.09.003) is a useful warning about the difference between a retrospective business-cycle chronology and a usable real-time signal. For deployment, evaluate filtered, point-in-time probabilities using data vintages and publication timestamps—not final revised series.

### 2. DCC: estimate whether cross-asset diversification is changing

**[Engle’s “Dynamic Conditional Correlation: A Simple Class of Multivariate GARCH Models” (2002)](https://doi.org/10.1198/073500102288618487)** supplies a time-varying correlation matrix. It is a dependence estimator, not a macro classifier.

1. Align return observations for the instruments or strategy portfolios to be combined.
2. Fit a univariate volatility model to each return series and divide returns by their estimated conditional standard deviations.
3. Update a latent correlation matrix using recent standardized returns and its own lagged value. In the standard DCC recursion, recent co-movement moves the estimate while a persistence term carries forward its previous value.
4. Rescale that matrix to conditional correlations, then combine it with the individual volatility estimates to obtain a conditional covariance matrix.
5. Give the risk service the covariance forecast, or derived outputs such as portfolio variance and factor-risk contributions.

**Inputs, frequency, and lag.** The basic method takes synchronized return series—commonly daily in portfolio applications—and produces a conditional correlation/covariance estimate at that same interval. The estimate reacts to observed co-movement; it is not a leading indicator. If used for intraday strategies, a DCC model fitted to daily returns cannot by itself capture minute-scale correlation changes. Conversely, minute data across FX, futures, equities, and 24/7 crypto introduce nonsynchronous trading, market closures, stale prices, and microstructure noise. Aggregate to a common clock and treat closed markets explicitly rather than filling them with artificial zero returns.

**Where it fails.** It assumes a particular smooth evolution of dependence; a sudden structural break can leave estimates slow or unstable. Pairwise correlations also miss nonlinear and tail dependence: correlations that look moderate in ordinary periods can jump during liquidation or funding stress. A growing universe creates estimation and computational burdens. For many strategies and assets, shrinkage and explicit stress scenarios should supplement—not be replaced by—the estimated covariance matrix.

**Later work.** [Cappiello, Engle, and Sheppard’s “Asymmetric Dynamics in the Correlations of Global Equity and Bond Returns” (2006)](https://doi.org/10.1016/j.jfineco.2005.05.005) shows why correlation dynamics can be asymmetric, a relevant challenge to one symmetric update rule. [Aielli’s “Dynamic Conditional Correlation: On Properties and Estimation” (2013)](https://doi.org/10.1080/07350015.2013.771027) analyzes estimation properties and proposes a corrected approach, particularly relevant when scaling the method to larger asset sets. For this book, the operational lesson is to monitor correlation jumps and factor exposures directly; do not trust a smooth covariance estimate alone during a break.

### 3. Volatility management: scale risk down when recent variance rises

**[Moreira and Muir’s “Volatility-Managed Portfolios” (2019)](https://doi.org/10.1111/jofi.12713)** uses recent realized variance to scale portfolio exposure. The useful idea is a sizing rule, not its particular portfolio universe.

1. For each portfolio or factor, calculate realized variance from recent returns. In their monthly implementation, daily returns over the preceding month provide the variance estimate.
2. In the next period, scale exposure approximately **inversely to the estimated variance**: high estimated variance means less exposure; low estimated variance means more.
3. Normalize the scale and impose leverage or exposure bounds in a live system.
4. Return a position multiplier for each strategy or risk sleeve.

**Frequency and lag.** The paper’s portfolio sizing is monthly and based on daily observations. It uses lagged realized risk: the signal is available after the measurement window, and responds to volatility that has already occurred. This is not a direct prescription for reacting to every intraday volatility spike. For short-horizon strategies, use the principle with a shorter, validated realized-volatility measure, but cap the multiplier and avoid extrapolating the paper’s monthly results to minute-by-minute trading.

**Where it fails.** Volatility can rise after a gap, and a lagged estimator may respond too late; a very short estimator may instead overreact to noise. Inverse-variance sizing can create excessive leverage in unusually quiet periods unless there is a hard cap. Volatility is not the same as liquidity: a calm-looking market can still have wide spreads, poor fills, or jump risk. Nor does a volatility multiplier identify whether the shock came from rates, USD funding, oil supply, or something else. Keep separate liquidity, gap, and concentration controls.

**Later work.** [Barroso and Santa-Clara’s “Momentum Has Its Moments” (2015)](https://doi.org/10.1016/j.jfineco.2014.11.010) applies volatility scaling to time-series momentum, illustrating how the sizing principle can be attached to a specific strategy family. It is an extension, not validation that one monthly estimator or scaling rule suits every asset class, crypto, or intraday strategy.

### A deterministic mapping the risk service can apply

Treat the following as a **starting policy to backtest and approve**, not as limits established by those papers. Define each asset-class cap in **risk units**—for example, stop-distance loss or stressed loss—rather than raw lots or notional. A futures contract, a leveraged FX position, and a stock share are not comparable by face value.

First compute a normal-state cap for each class from its independently approved strategy limits. Then apply a macro-state multiplier. A second, book-wide multiplier comes from realized volatility, covariance, and liquidity. The final class limit is:

\[
\text{class limit}
=
\text{approved normal cap}
\times
\text{macro-state multiplier}
\times
\text{volatility/liquidity multiplier}.
\]

| Macro state | Equity indices and stocks | FX | Rates / bond futures | Metals | Energy | Crypto |
|---|---:|---:|---:|---:|---:|---:|
| Calm / ordinary dependence | 1.00 | 1.00 | 1.00 | 1.00 | 0.75 | 0.50 |
| Growth risk-off / funding stress | 0.50 | 0.65 | 0.80 | 0.65 | 0.40 | 0.25 |
| Inflation or rate shock; stock–bond hedge unreliable | 0.65 | 0.70 | 0.40 | 0.70 | 0.60 | 0.35 |
| Volatility, liquidity, or correlation shock | 0.25 | 0.25 | 0.25 | 0.25 | 0.25 | 0.25 |

The multipliers act on the **previously approved class risk caps**, not directly on account notional. Keep additional hard controls:

- A total open-book stressed-loss cap that overrides the sum of class caps.
- Aggregate factor caps for equity beta, duration, broad USD, energy, and crypto/equity risk. These stop several agents from consuming separate limits while expressing the same underlying bet.
- A stricter limit when stock–bond correlation changes sign or rises sharply, and a stress scenario that assumes correlations move toward one during a liquidity shock.
- Per-strategy stops and a book-level stop that pauses new risk. Agents may propose actions; only the risk service enforces limits, and human promotion remains the live-trading gate.
- For a $500 account, verify that minimum trade size, margin, fees, and plausible slippage fit inside the loss budget before enabling an instrument. A risk fraction that cannot be implemented at the broker’s minimum size is not a usable cap.

On a volatility/liquidity shock, for example, the service applies the 0.25 class multipliers **and** checks the portfolio-wide stress limit; it does not let six individually compliant strategy caps imply that the combined book is safe. If inputs are stale, inconsistent, or unavailable, use a preapproved conservative fallback rather than silently carrying forward a permissive state.

### Recompute cadence

Run **market volatility, correlation, and portfolio-risk checks on each new bar or material event**, with a practical starting cadence of 5–15 minutes for intraday monitoring and an immediate check before accepting an order. Recompute the **macro state once per day** and on scheduled macro releases, using only information available at that timestamp. Let the risk service use smoothed or hysteretic transitions for raising limits, but allow a fast move to lower limits when volatility, drawdown, or liquidity breaches a hard threshold. Daily macro updates cannot make a macro classifier an intraday predictor; the faster risk layer should be driven by market data and book exposures.

## User

Follow-up 2, three parts. (1) Asset classes: how should macro and cross-asset state feed limits differently for FX, stock indices, metals, energy, crypto, futures and single stocks (sessions, leverage and margin, volatility regimes, typical stress correlations, contract mechanics, data history)? Give the differences per class. (2) Performance, not only safety: where do these macro overlays trade growth against survival, and what do the papers report on both sides (returns or Sharpe given up versus drawdown avoided)? Also list any trading ideas or market readings in these papers that could themselves become strategies or signals, with the style, instruments and data each needs. (3) Combinations: what would the best papers here combine with from other areas: position sizing under an uncertain edge, live alpha-decay detection, drawdown control, breadth and effective number of bets, kill switches, intraday risk-off detection, stop and exit design, safe de-risking and re-risking, news and event windows, stress scenarios, LLM agents for macro and news? Name concrete pairs or triples of papers with links, what the combined method would do, and why.

## Aurelle

The key design choice is to **separate macro context from market-state controls**: macro data should adjust a slow-moving risk budget, while market-specific volatility, liquidity, and margin conditions determine how much of that budget is usable now. FX, an equity index, and a single stock should not receive the same multiplier simply because the macro label says “risk-off.”

## 1. How the limits should differ by asset class

These are operational differences and starting principles, not universal numerical limits. Risk limits should be denominated in stressed loss or risk contribution—not raw lots, shares, or notional—then adjusted for the broker’s contract and margin rules.

| Class | What the risk service should treat differently |
|---|---|
| **FX** | FX trades nearly around the clock on weekdays, but liquidity and spreads change materially across the Asia, London, and New York sessions and around fixes and data releases. Leverage makes modest price moves consequential; margin depends on the pair, broker, and jurisdiction. Aggregate by currency and common drivers—not just by pair—so several positions can’t quietly create one large USD, JPY, or carry exposure. Stress cases should include abrupt USD/funding moves, carry unwinds, and wider spreads. Long histories exist for major pairs, but high-quality intraday coverage and reliable crisis-era execution assumptions are not uniform. |
| **Stock indices** | Index futures trade for much of the day, but the underlying cash session, overnight liquidity, and opening gaps matter. Treat index futures and cash-linked products as leveraged exposures with explicit contract multipliers and margin, and don’t assume stops can execute at their trigger through a gap. Common stress exposures include equity beta, rates, USD, and volatility; stock–bond hedging can weaken in rate or inflation shocks. Deep historical data exist for major indices, but today’s overnight access and products differ from older samples. |
| **Metals** | Separate precious metals from industrial metals: gold may respond to real yields, USD, and safe-haven demand, while industrial metals are more exposed to growth and supply chains. Futures have contract-specific tick values, expiries, delivery rules, and margin. Liquidity varies by metal and session; stress can include USD/rate shocks, geopolitical demand for havens, or industrial-supply disruption. Use separate limits by metal and by common USD/rates exposure rather than one “metals” bucket. |
| **Energy** | Don’t treat crude, refined products, and natural gas as interchangeable. They have distinct contract sizes, expiry and roll effects, delivery mechanics, and—especially for gas—potentially extreme volatility and discontinuous moves. Macro growth and inflation matter, but so do inventories, weather, geopolitics, transport constraints, and production shocks. Use tighter per-contract and gap-risk limits; a broad macro regime is a poor substitute for contract-level fundamentals and liquidity. |
| **Crypto** | Crypto trades 24/7, so there is no daily exchange close that lines up naturally with equity or macro data. Venue, funding, liquidation, and weekend liquidity can dominate; leverage can trigger forced liquidations before a conventional stop helps. Use asset-specific realized volatility and crypto-native liquidity/funding data, with conservative cross-asset stress links to equities and USD rather than assuming one stable “crypto beta.” The history is short and structurally different across tokens. A 2026 study found channel-specific, daily macro signals for some assets, but those forecasts concern **five-day volatility**, not intraday returns or profitable trade direction. |
| **Futures** | “Futures” is an execution wrapper across classes, not a single macro exposure. Risk must use the actual contract multiplier, tick value, expiry, roll, delivery terms, initial/maintenance margin, and exchange trading hours. Margin is not a loss limit: gaps can produce losses beyond posted margin. The risk service should map each contract to its underlying factor class, enforce both contract-level and aggregate-factor limits, and stress roll and overnight periods explicitly. |
| **Single stocks** | Add issuer-specific and sector risks to market beta: earnings, guidance, corporate actions, halts, borrow availability, and overnight gaps. A diversified-looking list can become concentrated through sector, factor, or common event exposure. Use earnings/event calendars, position and sector caps, and a single-name gap scenario; do not rely on index-level volatility alone. Individual-name histories are shorter and noisier than index histories, and survivorship and corporate-action handling matter. |

For implementation, maintain **two layers of caps**: a strategic cap by underlying exposure (equity beta, duration, USD, energy, crypto, and so on), and a tighter instrument/contract cap reflecting leverage, margin, liquidity, and gaps. If a stock-index future and an ETF express the same equity risk, they should draw from the same factor budget even though their contract mechanics differ.

## 2. Growth versus survival: what the evidence says

The research does not supply a single comparable “Sharpe sacrificed versus drawdown prevented” figure for a short-horizon multi-asset retail book. Studies use different portfolios, horizons, costs, risk constraints, and markets. The distinction matters: a better volatility forecast is not by itself proof of higher net returns, and a lower VaR exceedance rate is not the same thing as a smaller realized maximum drawdown.

- **Volatility scaling can improve returns per unit risk, but it is not free.** [Moreira and Muir’s “Volatility-Managed Portfolios” (2017)](https://doi.org/10.1111/jofi.125) scales exposure down when estimated volatility is high and reports higher Sharpe ratios for several factor portfolios. That result argues against assuming all de-risking necessarily sacrifices growth: if risk rises more than expected return, holding less exposure can improve both compounding and risk-adjusted performance. But it is not a guarantee for a scalper after spread, fees, leverage, or delayed signals. Its rule is a portfolio-level volatility-timing result, not a tested per-agent kill switch.
- **Tail calibration trades capital efficiency for fewer exceedances.** A 2026 conformal VaR study reports that on its CRSP index test sample, a GARCH-based 99% VaR with regime-weighted calibration had a 0.63% exceedance rate and a 381-basis-point average VaR bound; the uncalibrated base had a 1.94% exceedance rate and 260-basis-point average bound. In the same comparison, a feedback method had 1.14% exceedances and a 330-basis-point bound. The paper also finds regime weighting’s value depends on the base forecaster: it helps stress-period calibration most when the underlying model adapts slowly. These are **risk-bound and coverage outcomes**, not returns, Sharpe, or drawdown results. [VaR Tradeoff](https://www.alphaxiv.org/abs/2602.03903v3?page=4) [Stress Coverage](https://www.alphaxiv.org/abs/2602.03903v3?page=5)
- **A controller can improve the return–drawdown frontier in its test, but that is not a macro overlay comparison.** [CAST: “A Cross-Asset State-Space Trading System for Drawdown Control in Stock Markets” (2026)](https://www.alphaxiv.org/abs/2609.14205) reports daily stock-market tests in which its predictor-plus-controller sits on the paper’s return/max-drawdown Pareto frontier across four markets. For NASDAQ, it reports annualized Sharpe 0.523 and maximum drawdown 0.114; an ablation without its risk penalty reports Sharpe −0.884 and drawdown 0.806. Those are the paper’s reported backtest results, not independent evidence that an overlay will achieve those figures in live retail trading. The study uses stock price histories and a model-predictive controller, not the multi-asset, broker-constrained setup in the question. [Main Results](https://www.alphaxiv.org/abs/2609.14205v1?page=7) [Risk Penalty](https://www.alphaxiv.org/abs/2609.14205v1?page=8)
- **Macro information may help size risk without specifying trade direction.** [“Do Prediction Markets Forecast Cryptocurrency Volatility? Evidence from Kalshi Macro Contracts” (2026)](https://www.alphaxiv.org/abs/2604.01431) studies daily Kalshi macro-probability changes and five-day crypto realized volatility. Its Bitcoin rate-repricing signal is regime-dependent and does not provide full-window out-of-sample gains; recession-risk and some CPI signals have modest reported out-of-sample MSFE improvements. The authors estimate that one high-signal example would imply roughly a 7% reduction in Bitcoin weight under inverse-volatility sizing. They do **not** report that this adjustment earned returns or reduced drawdown in a trading strategy. The sample is 2023–March 2026, so it cannot establish stability across many rate regimes. [Forecast Results](https://www.alphaxiv.org/abs/2604.01431v1?page=11) [Crypto Signal](https://www.alphaxiv.org/abs/2604.01431v1?page=2)

### Strategy or signal ideas suggested by this research

These are hypotheses to test separately from risk limits; a signal that forecasts volatility does not automatically predict return direction.

- **Volatility-managed trend or momentum:** scale time-series momentum, FX carry, or an index strategy inversely to a lagged volatility estimate; needs point-in-time returns, realized volatility, and realistic turnover and transaction costs. [“Momentum Has Its Moments” (2015)](https://doi.org/10.1016/j.jfineco.2014.11.010) is a related example.
- **Macro-repricing volatility sizing in crypto:** use changes in rate, CPI, or recession probabilities as inputs to a *volatility forecast*, not a BTC/altcoin directional position, and size down only when the out-of-sample forecast improves. Needs timestamped prediction-market data, matched crypto prices, conventional controls such as USD/equity/volatility, and enough independent macro episodes. The cited study’s own findings are asset- and channel-specific. [Crypto Findings](https://www.alphaxiv.org/abs/2604.01431v1?page=4)
- **Event-window risk management:** reduce, hedge, or test event-specific positioning around scheduled CPI, employment, central-bank, or earnings announcements. The event schedule itself is a feature; any directional or volatility strategy needs intraday prices, announcement timestamps, pre-event expectations, and spread/fill data. Do not infer that “trade the announcement” is profitable just because it is an important risk window.
- **News-attributed jump risk:** [“Interpretable Systematic Risk around the Clock” (2026)](https://www.alphaxiv.org/abs/2604.13458) links high-frequency equity and E-mini futures jumps with contemporaneous news topics. It reports a macro-jump factor Sharpe of 0.78 and an annual real-time topic-selection strategy Sharpe of 0.95, versus 0.28 for its intraday-only version. That is a specific historical factor-mimicking portfolio exercise, not evidence that a retail strategy can simply buy or sell on an LLM label. A practical derivative is an **event-risk or exposure-reduction signal** around unusually large, classified jumps. It needs high-frequency futures/equity prices, timestamped news, and reliable controls for overnight gaps and classification errors. [Jump Premia](https://www.alphaxiv.org/abs/2604.13458v1?page=23) [Sharpe Comparison](https://www.alphaxiv.org/abs/2604.13458v1?page=48)

## 3. Research combinations that fit together

The most useful combinations are modular: an alpha model proposes direction, a sizing layer accounts for uncertainty and dependence, a risk monitor detects deterioration, and deterministic controls decide whether the proposal is admissible. The following pairs and triples are concrete research directions, not claims that the combined methods have already been validated.

1. **[Hamilton’s Markov-switching model (1989)](https://doi.org/10.2307/1912559) + [Engle’s Dynamic Conditional Correlation model (2002)](https://doi.org/10.1198/073500102288618487) + [Moreira–Muir volatility management (2017)](https://doi.org/10.1111/jofi.125):** use filtered macro-state probabilities to select a conservative dependence/risk scenario, use conditional covariance to measure current cross-asset concentration, then apply a capped volatility multiplier to the book. The macro state sets the slow risk budget; market covariance and volatility determine the faster usable amount. Include a stressed correlation floor because ordinary conditional correlations can fail during liquidation.
2. **[MacLean, Thorp, and Ziemba’s Kelly framework](https://press.princeton.edu/books/hardcover/9780691153589/the-kelly-capital-growth-investment-criterion) + [Garlappi, Uppal, and Wang’s “Portfolio Selection with Parameter and Model Uncertainty” (2007)](https://doi.org/10.1093/rfs/hhm003) + [Moreira–Muir](https://doi.org/10.1111/jofi.125):** estimate strategy edge and its uncertainty, shrink or fractionally scale the Kelly position when the edge estimate is weak, then volatility-scale the aggregate factor exposure. This addresses a central weakness of Kelly sizing: sizing from an overconfident edge estimate can make a nominal growth-optimal strategy ruinous.
3. **[Grinold’s “The Fundamental Law of Active Management” (1989)](https://doi.org/10.3905/jpm.1989.409211) + [Clarke, de Silva, and Thorley’s “Portfolio Constraints and the Fundamental Law of Active Management” (2002)](https://doi.org/10.3905/jpm.2002.319852) + a DCC/shrinkage covariance model:** aggregate strategy signals by common factor and estimate **effective breadth**—how many genuinely independent bets the agents make—rather than counting strategies. If a dozen FX and index agents all load on USD or equity beta, they are not a dozen independent opportunities. Feed the effective-breadth estimate into the total risk budget and strategy-concentration caps.
4. **[Barber and coauthors’ “The Limits of Distribution-Free Conditional Predictive Inference” (2021)](https://doi.org/10.1214/20-AOS1965) + [the 2026 regime-weighted conformal VaR study](https://www.alphaxiv.org/abs/2602.03903) + a conditional volatility forecaster:** forecast portfolio or class-level tail loss, calibrate the bound against recent forecast errors, and require adequate effective sample size before localizing to a rare regime. This gives the risk service a calibrated loss threshold, but it does not replace a hard account-level stop or promise return improvement.
5. **[Grossman and Zhou’s “Optimal Investment Strategies for Controlling Drawdowns” (1993)](https://doi.org/10.1111/j.1540-6261.1993.tb04708.x) + [CAST’s uncertainty-penalized controller](https://www.alphaxiv.org/abs/2609.14205) + conformal VaR calibration:** use account drawdown and forecast uncertainty to constrain new trades, while a calibrated loss forecast sets a separate tail-risk bound. This combines a path-dependent survival objective with a per-period risk forecast; test whether the resulting lower exposure reduces drawdown enough to justify missed rebounds and re-entry delay.
6. **[Kaminski and Lo’s “When Do Stop-Loss Rules Stop Losses?” (2014)](https://doi.org/10.1016/j.jbankfin.2013.12.020) + [Almgren and Chriss’s “Optimal Execution of Portfolio Transactions” (2001)](https://doi.org/10.21314/JOR.2001.041):** distinguish the *decision to cut risk* from the *execution of the cut*. A stop can reduce exposure but incur adverse execution or whipsaw; an execution schedule can reduce impact but leave risk open longer. Combine a hard exposure-reduction instruction with liquidity-aware execution, and retain a separate emergency marketable exit for catastrophic conditions.
7. **[“Interpretable Systematic Risk around the Clock”](https://www.alphaxiv.org/abs/2604.13458) + [Andersen, Bollerslev, Diebold, and Vega’s “Real-Time Price Discovery in Stock, Bond and Foreign Exchange Markets” (2007)](https://doi.org/10.1111/j.1540-6261.2007.01218.x) + deterministic event windows:** map scheduled surprises and unanticipated news jumps to an intraday risk-off trigger, then cap exposures by affected factor and session. The event trigger should be time-stamped and observable at decision time; an LLM can classify and summarize news, but should not set or bypass the numerical limits.
8. **[Hamilton (1989)](https://doi.org/10.2307/1912559) + [Barber et al. (2023), “Conformal Prediction Beyond Exchangeability”](https://doi.org/10.1214/23-AOS2276) + explicit crisis scenarios:** use the model’s current filtered state to select relevant historical or designed stress scenarios, then calibrate tail bounds using recent forecast errors. The state model proposes what conditions resemble; the scenario engine tests specific shocks such as a rate gap, USD squeeze, energy spike, crypto weekend liquidation, or correlation convergence. Scenario limits should remain operative even if the classifier assigns a high probability to “calm.”

**For LLMs and news, keep a strict boundary:** use the model to extract timestamped facts, classify event type, and propose which preapproved scenario applies. A deterministic service should calculate exposures, enforce limits, and manage order permissions. [“Interpretable Systematic Risk around the Clock”](https://www.alphaxiv.org/abs/2604.13458) is a research example of LLM-based news classification; it is not a reason to give a language model control over account capital.

For the retail system described, I would prioritize combinations **1, 3, 5, and 6**: robust cross-asset aggregation, avoid counting correlated agents as independent, constrain account-level drawdown, and make de-risking executable under actual liquidity. Macro state is most valuable as a **budget modifier and scenario selector**; it should not be the only mechanism that decides when a short-horizon strategy trades.

