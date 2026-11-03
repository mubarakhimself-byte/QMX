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

- **Budget framing.** Chats 01, 10, 06, 08, 23 (A), 24 (B), 25 (C), 26 (D) and 27 (E) were asked with "from one $500 account" in the context (and B and C follow-ups asked about $500 directly). The operator later ruled that a fixed budget biases research; chats 28 (F) onward carry no budget figure. Which answers bent around the $500: **B and C clearly did** (per-class "realistic from $500" verdicts, dollar loss limits sized to $500, best hours "from a $500 account"); their general method (cost hurdle, stressed-loss sizing, time-of-day cost and vol) still stands, but their per-class feasibility verdicts and dollar limits should be read as small-account. Chats 01, 06 and E carry a few $500-sized starting limits that are easy to ignore. Chats 10, 08, A and D answered in general terms. No rerun was judged necessary.
- **Equations.** Answers were copied with the page's Copy-message button, which yields Markdown with LaTeX, so equations survive. Checked on chat 13: all 11 TeX expressions on the page are present verbatim in the saved file.

| Order | Topic | Chat file | Status |
|---|---|---|---|
| Top-down A | Portfolio optimisation and portfolio-level sizing for a book of strategies | chat-23-A-portfolio-level-sizing.md | done ($500 framing) |
| Top-down B | Scalping and very low timeframes: risk and sizing when costs dominate | chat-24-B-scalping-low-timeframe.md | done ($500 framing, leans small-account) |
| Top-down C | Day trading and intraday: risk and sizing | chat-25-C-intraday-day-trading.md | done ($500 framing, leans small-account) |
| Top-down D | Market macrostructure feeding risk limits | chat-26-D-macrostructure.md | done ($500 framing) |
| Top-down E | Market microstructure feeding risk and sizing | chat-27-E-microstructure.md | done ($500 framing) |
| Top-down F | Agents for macro, micro and news, without touching money | chat-28-F-agents-macro-micro-news.md | done |
| Top-down G | Multi-asset book: normalising risk across classes | chat-29-G-multi-asset-normalisation.md | done |
| Technique 10 | Alpha decay detected live | chat-10-alpha-decay-live.md | done (Pro, then Smart; $500 framing) |
| Technique 1 | Sizing with a small, uncertain edge | chat-01-sizing-uncertain-edge.md | done (Pro, then Smart; $500 framing) |
| Technique 6 | Kill switches and circuit breakers | chat-06-kill-switches-breakers.md | done ($500 framing) |
| Technique 8 | Risk-off regimes and correlation breakdowns | chat-08-risk-off-regimes.md | done ($500 framing) |
| Technique 13 | Stops and exits | chat-13-stops-and-exits.md | running |
| Technique 18 | LLM-agent harnesses for alpha discovery | chat-18-agent-harness-alpha-discovery.md | running |
| Technique 2 | Breadth and effective number of bets | chat-02-breadth-effective-bets.md | running |
| Technique 15 | Stress tests and scenario generation | chat-15-stress-scenarios.md | running |

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

## Top-down B - Scalping and very low timeframes: risk and sizing when costs dominate (chat 24)

Place in the top-down order: **second**. Asked with the "$500 account" framing; follow-up (b) explicitly asked which classes are realistic from $500, so the per-class verdicts below lean small-account.

**Core answer (assistant's claim).** No trade unless conservative all-in net expectancy is positive; costs scale with turnover and never create edge; size from stressed loss, not win rate. Break-even win probability p_BE = (S + C) / (T + S) for stop S, target T and round-trip cost C (a floor: ignores gaps and partial fills). Quantity q <= risk budget / (stop distance x value per price unit + stressed exit slippage per unit); never round up to a minimum lot. Negative skew (many small wins, rare big losses) means sizing on expected shortfall and stress, not variance.

**Edge-to-cost admission gate (the assistant's operational proposal, not a paper result).** Lower confidence bound of expected gross edge >= **2x** stressed expected round-trip cost per unit; **3x** for negative-skew strategies or thin live evidence. Gross edge measured from decision-time mid to planned exit mid, on all signals, not only filled ones (fill selection biases it). Cost measured from fills against contemporaneous mids plus fees, funding and reject or requote costs. Recomputed live in rolling, session-aware windows with session-clustered errors.

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| Optimizing Broker Performance Evaluation through Intraday Modeling of Execution Cost (Eisler, Muhle-Karbe) | https://www.alphaxiv.org/abs/2405.18936 | 2024 | Split execution cost into a linear part (spread crossing) and a size-related impact part from fills and the mid path. Even 1,000 orders leave the naive cost estimate weak: costs need long ledgers. | X1, X6 |
| Latency and Liquidity Risk (Cartea, Jaimungal, Sanchez-Betancourt) | https://doi.org/10.1142/S0219024921500357 | 2021 | Choose how far a marketable limit order may walk the book ("discretion") by trading extra cost against the penalty of a miss. A venue-specific execution parameter. | X1 |
| The Shadow Price of Latency: Improving Intraday Fill Ratios in FX (Cartea, Sanchez-Betancourt) | https://doi.org/10.1137/19M1258888 | 2021 | Latency effect on FX fill ratios. | X1 |
| The Effect of Latency on Optimal Order Execution Policy (Ma, Saggese, Smith) | https://www.alphaxiv.org/abs/2504.00846 | 2025 | Limit price vs fill probability vs latency vs risk; excludes queue position and partial fills. Measure at your real latency and venue. | X1 |
| Optimal Execution of Portfolio Transactions (Almgren, Chriss) | https://doi.org/10.21314/JOR.2001.041 | 2000/2001 | Execution schedule under cost vs risk; mostly irrelevant at tiny size in deep books, relevant where an order eats depth. | X1, X2 |
| Optimal Execution under Liquidity Uncertainty | https://www.alphaxiv.org/abs/2506.11813 | 2025 | Execution when available liquidity is itself uncertain. | X1 |
| Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ Futures (Mesfin) | https://www.alphaxiv.org/abs/2605.04004 | 2026 | Falsification study: 11 of 14 five-minute signal families earned less gross than a 2-point round-trip friction; none passed all checks. A cost hurdle kills most bar-based scalps. | X5 |
| Machine Learning-Based Bitcoin Trading Under Transaction Costs (Bysik, Slepaczuk) | https://www.alphaxiv.org/abs/2606.00060 | 2026 | Position changes only when the forecast clears a cost-based hurdle (hourly BTC, proportional costs). | X2, X5 |
| The Alpha Illusion: Reported Alpha from LLM Trading Agents Should Not Be Treated as Deployment Evidence (Ye et al.) | https://www.alphaxiv.org/abs/2605.16895 | 2026 | LLM confidence is not a return probability; LLMs as auditable upstream information, not trading authority. | X5, X7 |
| A Simple Implicit Measure of the Effective Bid-Ask Spread (Roll) | https://doi.org/10.1111/j.1540-6261.1984.tb03897.x | 1984 | Spread estimated from price data; complements fill logs. | X1 |

**Starting limits it floated (to test, $500-framed).** Planned loss per trade 0.1-0.25% of equity; daily loss 0.5-1% including open trades; live minimum-size execution trial before any size increase.

**Per asset class (assistant's claim, $500-framed).** FX: OTC, no consolidated book; markup vs raw-plus-commission; last-look, rejects, requotes; spreads widen at news, rollover and the Sunday open; feasible only with true micro lots and logged execution quality. Index futures vs index CFDs are different products; micro futures can meet margin yet be too big for prudent risk. Metals: micro gold or a small CFD testable; full-size futures not. Energy: inventory-report fills; natural gas especially hard; generally poor for small scalping. Crypto: spot without leverage is among the more practical small-size tests; perpetuals' liquidation makes them unforgiving; one deep venue. Futures: "intraday margin" is a broker permission, not safe risk. Single stocks: liquid low-price names may work; fractional shares not always available intraday or short. Shortlist it gave for small-size testing: unlevered spot crypto, FX with true micro sizing, liquid stocks.

## Top-down C - Day trading and intraday: risk and sizing (chat 25)

Place in the top-down order: **third**. Asked with the "$500 account" framing; the first answer gave dollar limits sized to $500.

**Core answer (assistant's claim).** One shared risk controller across strategies; size each trade from a fixed dollar risk budget divided by (stop loss per unit + cost reserve per unit), then cut size when the time-of-day volatility forecast is high or spreads widen. Estimate volatility and execution cost **separately** by instrument and time bucket: busy can mean deep, wide, fast, or all three. Flatten before the close with a buffer; size carried positions for gaps. Daily loss limits are capital circuit breakers at three levels (strategy, risk cluster, account), not a claim that trading after a loss is bad.

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| Intraday Periodicity and Volatility Persistence in Financial Markets (Andersen, Bollerslev) | https://finance.martinsewell.com/stylized-facts/volatility/AndersenBollerslev1997b.pdf | 1997 | Model the recurring intraday volatility shape separately from daily volatility. | X1, X2 |
| Multiplicative Component GARCH Model of Intraday Volatility | https://www.alphaxiv.org/abs/2111.02376 | 2021 | Seasonal bucket x daily level x short-term clustering = vol forecast for the planned hold; extends Engle-Sokalska (2012) to irregular trades. | X2 |
| Deutsche Mark-Dollar Volatility: Intraday Activity Patterns, Macroeconomic Announcements (Andersen, Bollerslev) | https://public.econ.duke.edu/~boller/Published_Papers/jf_98.pdf | 1998 | FX intraday pattern and announcement effects. | X1, X4 |
| Periodicity in Cryptocurrency Volatility and Liquidity | https://www.alphaxiv.org/abs/2109.12142 | 2021 | Crypto has its own cycles; traditional session curves do not transfer. | X1 |
| Market Intraday Momentum (Gao, Han, Li, Zhou) | https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351 | 2018 | First half-hour S&P ETF return predicts the last half-hour (1993-2013). A signal, not a sizing rule. | seed |
| Intraday Time Series Momentum: International Evidence | https://centaur.reading.ac.uk/95566/1/Accepted-Version.pdf | 2021 | Extends intraday momentum beyond the US. | seed |
| Intraday Momentum and Reversal in Chinese Stock Market | https://www.sciencedirect.com/science/article/abs/pii/S1544612318307414 | 2019 | Both effects in one market: test by market and horizon. | seed |
| When Do Stop-Loss Rules Stop Losses? (Kaminski, Lo) | link in chat 25 | 2014 | Whether cutting after losses helps depends on momentum vs mean reversion; count missed rebounds. | X3 |
| The Cross-Section of Intraday and Overnight Returns | link in chat 25 | 2016 | Intraday vs overnight returns differ; matters for flat-by-close strategies. | X1 |
| Forecasting Intraday Volume in Equity Markets with Machine Learning | https://www.alphaxiv.org/abs/2505.08180 | 2025 | Flags hours of poor execution capacity. | X1, X6 |
| Stylized Facts of Intraday Precious Metals (Batten et al.) | https://pmc.ncbi.nlm.nih.gov/articles/PMC5407636/ | 2017 | Metals intraday vol, volume and spread differences. | X1 |
| Effect of Inventory Announcements on Crude Oil Price Volatility (Bu) | https://www.sciencedirect.com/science/article/abs/pii/S0140988314001236 | 2014 | EIA report as a scheduled energy event window. | X4 |
| Time-of-Day Periodicities of Trading Volume and Volatility in Bitcoin Exchange (Wang et al.) | https://ideas.repec.org/a/eee/finlet/v34y2020ics1544612319301904.html | 2020 | Bitcoin time-of-day cycles. | X1 |
| The Quarter-Hour Effect | https://www.alphaxiv.org/abs/2607.09426 | 2026 | Recurring short-cycle pattern in a 24/7 market. | seed |
| FIA automated trading risk controls paper | https://www.fia.org/sites/default/files/2024-07/FIA_WP_AUTOMATED%20TRADING%20RISK%20CONTROLS_FINAL_0.pdf | 2024 | Industry checklist of automated-trading risk controls. | X3 |

**Growth vs survival (assistant's claim).** The stop-loss literature says a stop-after-losses rule can cost returns when the strategy mean-reverts; the evidence does not show that "stop after today's loss" improves the signal. Use daily limits to protect capital and accept the opportunity cost; never use a fixed count of consecutive losses as a universal trigger.

**Per asset class and hours (assistant's claim; UTC, test windows, not promises).** FX majors: London-New York overlap ~12:00-16:00; JPY, AUD, NZD also Asian hours; caution at the broker rollover ~21:00-22:00, data releases, late Friday. US indices: after the opening auction settles; test the close separately; caution at the cash open, data releases, thin overnight futures. Metals: London-New York overlap; caution at US inflation, jobs, central-bank releases and maintenance breaks. Energy: active US hours with an explicit EIA policy (Wednesday 10:30 New York); OPEC, expiry, settlement. Crypto: no session; compare venue-specific deep hours (Europe-US overlap is a candidate); caution at weekends, funding timestamps, maintenance. Futures: trade when the underlying contract's book is deepest; caution at reopenings, expiry and roll. Single stocks: regular hours after the opening auction; caution at earnings, halts, gaps, pre- and post-market.

## Top-down D - Macrostructure: regimes, cross-asset links and macro drivers feeding limits (chat 26)

Place in the top-down order: **fourth**. Asked with the "$500 account" framing; the answer mostly ignored it except for a minimum-size check, so it does not lean small-account.

**Core answer (assistant's claim).** Macro state is a **shared risk governor and scenario selector**, not an entry signal. A slow layer (filtered regime probabilities from point-in-time macro and cross-asset data, recomputed daily and on scheduled releases) sets a budget multiplier; a fast layer (realised vol, conditional covariance, liquidity, every 5-15 minutes and before each order) decides how much of that budget is usable now. Lower limits fast, raise them slowly with hysteresis. Uncertain or conflicting state means an intermediate, reduced budget. Stale inputs fall back to a pre-approved conservative state.

**Class limit = approved normal cap x macro-state multiplier x volatility/liquidity multiplier**, caps in risk units (stressed loss), plus a total stressed-loss cap, factor caps (equity beta, duration, USD, energy, crypto/equity) and a stressed correlation floor. Starting multipliers it proposed (a policy to backtest, not a paper result):

| Macro state | Equities | FX | Rates | Metals | Energy | Crypto |
|---|---|---|---|---|---|---|
| Calm, ordinary dependence | 1.00 | 1.00 | 1.00 | 1.00 | 0.75 | 0.50 |
| Growth risk-off or funding stress | 0.50 | 0.65 | 0.80 | 0.65 | 0.40 | 0.25 |
| Inflation or rate shock, stock-bond hedge unreliable | 0.65 | 0.70 | 0.40 | 0.70 | 0.60 | 0.35 |
| Vol, liquidity or correlation shock | 0.25 | 0.25 | 0.25 | 0.25 | 0.25 | 0.25 |

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle (Hamilton) | https://doi.org/10.2307/1912559 | 1989 | Markov-switching regimes; hand the risk service the **filtered** probability vector, never smoothed labels. | X3, X4 |
| Business-Cycle Phases and Their Transitional Dynamics (Filardo) | https://doi.org/10.1080/07350015.1994.10524545 | 1994 | Transition probabilities driven by explanatory variables. | X3 |
| Calling Recessions in Real Time (Hamilton) | https://doi.org/10.1016/j.ijforecast.2010.09.003 | 2011 | Retrospective chronology vs usable real-time signal; use data vintages. | X5 |
| Dynamic Conditional Correlation (Engle) | https://doi.org/10.1198/073500102288618487 | 2002 | Time-varying covariance: is diversification between strategies weakening? Reactive, not leading. | X2, X6 |
| Asymmetric Dynamics in the Correlations of Global Equity and Bond Returns (Cappiello, Engle, Sheppard) | https://doi.org/10.1016/j.jfineco.2005.05.005 | 2006 | Correlations rise asymmetrically in sell-offs. | X4 |
| Dynamic Conditional Correlation: On Properties and Estimation (Aielli) | https://doi.org/10.1080/07350015.2013.771027 | 2013 | Corrected DCC for larger universes. | X2 |
| Volatility-Managed Portfolios (Moreira, Muir) | https://doi.org/10.1111/jofi.12713 | 2017/2019 | Scale exposure inversely to recent realised variance; reported **higher Sharpe** for several factors. Cap the multiplier (quiet periods invite leverage). | X2 |
| Momentum Has Its Moments (Barroso, Santa-Clara) | https://doi.org/10.1016/j.jfineco.2014.11.010 | 2015 | Vol scaling attached to momentum. | X2, seed |
| International Asset Allocation With Regime Shifts (Ang, Bekaert) | https://doi.org/10.1093/rfs/15.4.1137 | 2002 | Allocation under regime-dependent distributions. | X2 |
| The Determinants of Stock and Bond Return Comovements | https://doi.org/10.1093/rfs/hhp069 | 2010 | Stock-bond correlation is time-varying and macro-conditioned. | X4 |
| Common Risk Factors in Currency Markets (Lustig, Roussanov, Verdelhan) | https://doi.org/10.1016/j.jfineco.2010.10.003 | 2011 | FX pairs share dollar and carry factors. | X2 |
| Not All Oil Price Shocks Are Alike (Kilian) | https://doi.org/10.1257/aer.99.3.1053 | 2009 | Supply vs demand oil shocks imply different macro risks. | X4 |
| A Simple Long Memory Model of Realized Volatility (Corsi, HAR-RV) | https://doi.org/10.1093/jjfinec/nbp001 | 2009 | Short-, medium-, long-horizon realised vol in one forecaster. | X2 |
| Value and Momentum Everywhere (Asness, Moskowitz, Pedersen) | https://doi.org/10.1111/jofi.12021 | 2013 | Cross-asset style factors concentrate "different" strategies. | X2 |
| Taming Tail Risk: Conformal Calibration for Nonstationary Portfolio VaR | https://arxiv.org/abs/2602.03903 | 2026 | On CRSP, GARCH 99% VaR with regime-weighted calibration: 0.63% exceedances with a 381 bp bound vs 1.94% and 260 bp uncalibrated. Fewer breaches cost a wider bound (capital efficiency). | X3, X4 |
| CAST: A Cross-Asset State-Space Trading System for Drawdown Control in Stock Markets | https://www.alphaxiv.org/abs/2609.14205 | 2026 | Predictor plus uncertainty-penalised controller; on NASDAQ, Sharpe 0.523 and max DD 0.114 vs Sharpe -0.884 and DD 0.806 without the risk penalty (backtest). | X2, X3 |
| Do Prediction Markets Forecast Cryptocurrency Volatility? Evidence from Kalshi Macro Contracts | https://www.alphaxiv.org/abs/2604.01431 | 2026 | Daily macro-probability changes forecast 5-day crypto vol for some channels; one example implies ~7% less BTC weight under inverse-vol sizing. Volatility, not direction. | X2, seed |
| Interpretable Systematic Risk around the Clock | https://www.alphaxiv.org/abs/2604.13458 | 2026 | LLM-classified news topics behind high-frequency equity and E-mini jumps; macro-jump factor Sharpe 0.78; real-time topic-selection Sharpe 0.95 vs 0.28 intraday-only. | X4, X7, seed |
| Real-Time Price Discovery in Stock, Bond and Foreign Exchange Markets (Andersen, Bollerslev, Diebold, Vega) | https://doi.org/10.1111/j.1540-6261.2007.01218.x | 2007 | How scheduled surprises move each market in real time. | X4 |
| Portfolio Selection with Parameter and Model Uncertainty (Garlappi, Uppal, Wang) | https://doi.org/10.1093/rfs/hhm003 | 2007 | Ambiguity-averse allocation when estimates are unreliable. | X2 |
| Optimal Investment Strategies for Controlling Drawdowns (Grossman, Zhou) | https://doi.org/10.1111/j.1540-6261.1993.tb04708.x | 1993 | Drawdown-constrained growth. | X2, X3 |

**Growth vs survival (assistant's claim).** No paper gives one comparable "Sharpe given up vs drawdown avoided" figure for a short-horizon multi-asset book. Volatility management is the case where de-risking can **raise** Sharpe (if risk rises faster than expected return). Conformal VaR buys fewer breaches with a wider bound. CAST's risk penalty improved both Sharpe and drawdown in its backtest. Macro overlays should be tested for whether lower exposure saves enough drawdown to pay for missed rebounds and re-entry delay.

**Per asset class (assistant's claim).** Two layers of caps: strategic by underlying exposure (equity beta, duration, USD, energy, crypto) and tighter per instrument for leverage, margin, liquidity and gaps; an index future and an ETF on the same index draw on one factor budget. FX: aggregate by currency and carry; stress USD funding and carry unwinds. Indices: overnight gaps; stock-bond hedge weakens in rate shocks. Metals: gold on real yields, USD and haven demand vs industrial metals on growth. Energy: crude, products and gas are not interchangeable; inventories, weather, geopolitics; tighter per-contract and gap limits. Crypto: no close to align with macro data; venue, funding and liquidation dominate; short history; macro links are channel-specific and about volatility. Futures: map each contract to its underlying factor class. Single stocks: earnings and event calendars, sector caps, single-name gap scenario.

## Top-down E - Microstructure feeding risk and sizing (chat 27)

Place in the top-down order: **fifth**. Asked with the "$500 account" framing; one starting limit (0.25-0.5% combined open risk) is $500-framed, the rest is general.

**Core answer (assistant's claim).** Microstructure is first a **permission-to-trade gate**, then a cost input to sizing, never a reason to add leverage. Measure quoted spread, effective spread on fills, and realised spread or **markout** (fill vs mid a few seconds later) per instrument, venue, session and news regime. Size bound Q <= R / (D x V + C + S): risk budget over stop distance times value per unit plus round-trip cost plus stop slippage. Set the stop from the trade's invalidation point, then reject or shrink if spread and slippage are large relative to it. The strategy's own fill markout is a better toxicity check for retail than VPIN.

**Venue rule.** "Don't call a quote a book unless it represents orders you can execute against." Exchange futures books support OFI and depth methods; spot FX has no central book; index CFDs and metal or energy CFDs are broker quotes; crypto books are per exchange; US single stocks are fragmented across venues.

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| The Price Impact of Order Book Events (Cont, Kukanov, Stoikov) | https://www.alphaxiv.org/abs/1011.6402 | 2014 | OFI: signed queue changes at the best quotes; mean in-sample R^2 ~65% for contemporaneous 10-second mid changes vs ~32% for trade imbalance. Explanatory, not a proven forecast. | X1, seed |
| Multi-Level Order-Flow Imbalance in a Limit Order Book (Xu, Gould, Howison) | https://www.alphaxiv.org/abs/1907.06230 | 2019 | MLOFI over the first M levels; 10-level ridge cut out-of-sample RMSE 15-74% vs best-level OFI on six Nasdaq stocks (10-second windows, refit every 30 minutes). | seed |
| The Price Impact of Order Book Events: Market Orders, Limit Orders and Cancellations (Eisler, Bouchaud, Kockelkoren) | https://www.alphaxiv.org/abs/0904.0900 | 2010 | Event-type impact responses; signed event correlations last ~10-100 events (~10 seconds). Use to veto passive entries when recent flow predicts a move against the fill. | X1 |
| Square-root market impact (I ~ Y sigma sqrt(Q/V)) | https://www.alphaxiv.org/abs/1412.0141 | 2014 | Size sanity check only; for parent orders, not tiny retail orders. | X1 |
| Beyond the square root: logarithmic dependence of market impact | https://www.alphaxiv.org/abs/1412.2152 | 2014 | Challenges the square-root law's scope. | X1 |
| Flow Toxicity and Liquidity in a High-frequency World (Easley, Lopez de Prado, O'Hara, VPIN) | https://doi.org/10.1093/rfs/hhs053 | 2012 | One noisy toxicity diagnostic; trade signing breaks on fragmented or CFD feeds. | X6 |
| Kyle (1985); Glosten and Milgrom (1985); Admati and Pfleiderer (1988); Roll (1984) | links in chat 27 | 1984-1988 | Informed flow and depth; adverse-selection spread; intraday clustering of volume and variability (session baselines); implicit spread. | X1 |
| Anomalous Price Impact and the Critical Nature of Liquidity (Toth et al.) | https://doi.org/10.1103/PhysRevX.1.021006 | 2011 | Square-root impact context. | X1 |
| Execution Realism and Reproducibility in LLM-Based Trading Systems: Scoping Review and Evidence Audit | https://www.alphaxiv.org/abs/2606.08285 | 2026 | Evaluation discipline for LLM trading claims. | X5, X7 |

**Growth vs survival (assistant's claim).** Evidence is strong for explaining short-horizon price changes in exchange books, weak for proving a retail gate improves net returns. A spread, depth or markout gate avoids costly fills and fragile stops but can reject winners, delay entries past the signal, or starve a strategy of trades. Policy: hard-block objectively untradeable conditions (spread or minimum size makes the risk budget impossible); run noisy OFI or toxicity filters as **shadow labels** first and report blocked vs permitted trades (count, net P&L, tail loss, missed winners, markout, by session and event regime) before any live veto.

**Per asset class (assistant's claim).** FX: OTC, broker-specific spread, rejects and slippage; broker tick volume is a venue proxy only. Indices: cash index is a benchmark; the central book is the future; a CFD is a broker quote; do not apply futures depth to CFDs. Metals and energy: exchange futures have contract books, CFDs do not; use the exact contract month; EIA and supply news are separate execution regimes. Crypto: per-exchange books, perpetual funding and liquidation flows, cross-venue dislocation. Futures: the cleanest setting for OFI and depth methods when data matches the contract. Single stocks: fragmented; one venue's book omits the rest; auctions, halts, earnings.

## Top-down F - Agents for macro, microstructure and news, without touching money (chat 28)

Place in the top-down order: **sixth**. Asked without any budget figure, newest papers only.

**Core answer (assistant's claim).** LLMs are evidence interpreters, not trading controllers. Each agent emits a typed, expiring, **de-risking-only** proposal (risk_scale_proposal clamped to [0, 1]); a deterministic risk service validates schema, timestamps, source allow-list and instrument mapping, aggregates, applies hard limits, and outputs an approved risk multiplier, never an order. Failed validation, expiry or loss of the service means no agent-driven change. Microstructure stays deterministic: compute spread, depth imbalance, trade-flow imbalance and liquidity gaps in code; an LLM never sits in a scalping decision loop. Store event time and availability time separately (ts_available <= decision_time).

Common envelope it proposed: instrument, venue, event_time, available_time, as_of, valid_until, source_ids, confidence, risk_scale_proposal, plus class-specific fields (FX pair and relative surprise, futures contract month, crypto venue and product, stock ticker and filing accession number).

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| OpenPM: Auditable Point-in-Time Evaluation for LLM Portfolio-Management Agents | https://arxiv.org/abs/2608.09988 | 2026 | Six channel analysts -> constructor LLM -> **deterministic critic projects weights to feasibility**; availability gates (SEC acceptance time, ALFRED vintages, bar close, news lag); gate logs. Results depend on analyst signal quality (strong capture: 4 of 5 constructors beat equal weight; weak: none); 44-day window, no impact, "upper bounds". | X6, X7 |
| Financial Language Models for News-Based Trading under Market Frictions (MFAST) | https://arxiv.org/abs/2609.23703 | 2026 | Timestamped text -> entity match -> dedupe -> sentiment classifier -> calibration -> firm-day signal. LLaMA-3 long-short Sharpe 2.85 (bootstrap CI 2.31-3.34), 180% cumulative, after 5 bp and a 10% ADV cap, June 2024-Jan 2026 (post-cutoff). 112 ms per article. Revise-and-resubmit. | X7, seed |
| Can LLMs Take the Pulse of the Economy? Real-Time Evaluation of LLM Nowcasts (LiveMacroEval) | https://arxiv.org/abs/2608.30110 | 2026 | Live pre-release nowcasts on 16 US indicators; GPT-5 tied Bloomberg consensus overall, varied by indicator; researcher-plus-verifier team got direction right on 54% vs 38% for a plain prompt. Context input, not a trading result. | X7, X4 |
| Strat-LLM: Stratified Strategy Alignment for LLM-based Stock Trading | https://arxiv.org/abs/2605.06024 | 2026 | Constraint level interacts with regime; GPT-5 max DD fell from 20.83% (Guided) to 11.66% (Strict) in its US sample. | X3, X7 |
| ViperQ: Order Flow Pattern Recognition via Auction Market Theory for RL Trading | https://arxiv.org/abs/2609.13825 | 2026 | RL, not LLM. Features: volume-area position, CVD slope and divergence, tape velocity, imbalance. Large returns on TSLA and NVDA but drawdowns -27.5% and -47.8%. | seed |
| Poisoning Agentic Alpha: Adversarial Vulnerabilities in Multi-Agent Trading Systems | https://arxiv.org/abs/2608.24069 | 2026 | A compromised terminal role bypasses upstream deliberation; voting or more agents do not replace a deterministic boundary. | X7 |
| Fake News, Real Crashes: Information Injection Attacks on LLM Financial Trading Agents | https://arxiv.org/abs/2610.26438 | 2026 | Fabricated information succeeded 62% of the time vs 14% for prompt injection (sandbox, ~10,000 decisions). Authenticate and cross-check the data plane; cap any single unverified item's effect. | X7 |
| The Price of Thought: Does Test-Time Reasoning Pay in LLM Trading? | https://arxiv.org/abs/2609.30705 | 2026 | None of nine low-vs-baseline reasoning comparisons improved net returns at 10 bp; $415 inference cost. Do not pay for longer reasoning without measured portfolio change. | X7 |
| Measurement Boundaries in LLM Financial Agent Evaluation: Fixed-Tape Execution and Multi-Defect Auditing | https://arxiv.org/abs/2609.32379 | 2026 | Replay a fixed response tape to isolate execution effects; runs vary in both responses and portfolio state. | X5, X6 |
| Can AI Make Money in Crypto? Measuring the Gap from Backtests to Real Markets | https://arxiv.org/abs/2609.34510 | 2026 | No LLM or agent method profitable on 2025 crypto backtests; live, one of four profitable, none beat BTC buy-and-hold; LLM decisions ~187 s and agent ~523 s vs 18.6 s for ML. | X5, X7 |
| The Control Layer Behind Rule-Following Agents Trading Across Market Conditions | https://arxiv.org/abs/2610.26324 | 2026 | Agents kept 97.5% of gross loss inside declared stops; one position-limit breach in 24 runs; a 13-day period with the stop engine disabled. "Rules followed" and "made money" are separate scorecards. | X3, X6 |
| FinAbstain: Uncertainty-Calibrated Multimodal RAG for Selective Financial Forecasting | https://arxiv.org/abs/2607.24875 | 2026 | Disagreement, contradiction and retrieval quality raise uncertainty, which triggers abstention, smaller exposure or human review. Its performance tables are simulated. | X7 |

**Growth vs survival (assistant's claim).** Clearest return gain: calibrated news sentiment in US equities (MFAST). Macro agents show forecast skill, not yet a costed strategy. OpenPM's gains hinge on upstream evidence quality. Crypto deployment and reasoning-cost papers show latency, fills, fees and funding erasing apparent advantage. Lower drawdown from agents counts as safety, not alpha, unless incremental net return repeats out of sample (paired tests: no agent, deterministic features only, agent output, agent plus risk service).

**Per asset class (assistant's claim).** FX: central banks, pair-relative surprises, interventions; map one headline to every pair it touches. Indices: scheduled macro and central-bank events, mega-cap earnings, rebalances; compare releases with the consensus snapshot available just before. Metals: gold on real rates, USD, central banks, ETF flows; industrial metals on inventory, supply and trade policy. Energy: EIA, OPEC, weather, outages, sanctions; very short price-impact windows. Crypto: 24/7 news, authenticity is the core risk; exchange status notices, governance, hacks, unlocks, regulators. Futures: tie the signal to the contract month; no continuous series that leaks roll info. Single stocks: SEC EDGAR with acceptance timestamps, earnings, guidance; article-to-ticker mapping and duplicates. Data rights: public access is not redistribution or commercial-use permission; keep the licence and data version.

## Top-down G - Multi-asset book: normalising risk across classes (chat 29)

Place in the top-down order: **seventh** (added by the operator's multi-instrument lens). Asked without any budget figure.

**Core answer (assistant's claim).** One account-currency loss budget for every strategy; aggregate positions through shared factors and joint scenarios. Account-currency P&L volatility sets ordinary size; portfolio stress loss and expected shortfall constrain survival; margin is a separate hard limit, never a risk proxy. ATR expresses stop distance; R multiples evaluate trades; notional tracks factor exposure and leverage; none of them alone makes two positions equally risky. Portfolio covariance approx B Sigma_F B' + D (factor exposures, factor covariance, residual), with at least USD, regional equity beta, rates or duration, commodities and crypto beta factors.

**Risk target to quantity (the procedure it gave).** (1) Budget in account currency over a stated horizon, allocated portfolio -> factor or cluster -> strategy, plus hard limits on stressed loss or ES, gross, factor exposure, margin, liquidity. (2) Convert each position to account-currency P&L (futures: move x point value x FX; stop: ticks x tick value + fees + slippage; FX pip value in account currency; crypto linear vs inverse). (3) Estimate risk on synchronised, session-aware intervals; never treat a closed market as zero return; UTC windows and explicit weekend tests for crypto; roll-aware series with basis kept separate. (4) Aggregate the whole proposed book jointly with covariance limits and joint stress (correlation up, gaps, spreads, margin shocks). (5) Solve continuous sizes q*. (6) Round toward less risk: q = sign(q*) x l x floor(|q*| / l); if |q*| < l, no trade; never round up; recompute book risk after rounding and accept unused risk. (7) Recompute after fills, vol moves, rolls and limit changes, with a no-trade band against churn.

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| Volatility-Managed Portfolios (Moreira, Muir) | https://www.nber.org/papers/w22208 | 2016/2017 | w proportional to 1/sigma^2 from last month's daily returns; Sharpe up roughly 50-100% for equity factors and FX carry; 4.86% annualised alpha for the managed market. No drawdown or ES figure retrieved. | X2 |
| On the Performance of Volatility-Managed Portfolios (Cederburg et al.) | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3357038 | 2020 | Real-time test across 103 equity strategies: the favourable evidence does not generalise reliably. Demand walk-forward, costs, lags, caps. | X2, X5 |
| Risk-aware Trading Portfolio Optimization | https://www.alphaxiv.org/abs/2503.04662 | 2025 | Trading-oriented factor-aware risk budgeting reference (not verified for specific numbers). | X2 |
| Momentum Has Its Moments (Barroso, Santa-Clara) | https://doi.org/10.1016/j.jfineco.2014.11.010 | 2015 | Vol-managed momentum to cut momentum crashes. | X2, seed |
| The Deflated Sharpe Ratio (Bailey, Lopez de Prado) | https://doi.org/10.3905/jpm.2014.40.5.094 | 2014 | Selection check before any sizing. | X5 |

**Growth vs survival (assistant's claim).** Helps when volatility is persistent and predicts risk better than return (Moreira-Muir: Sharpe up). Only cuts risk when scaling does not improve entries: gross return and drawdown both fall. Hurts when it levers up after quiet spells just before a jump, lags shocks, whipsaws on mean-reverting vol, or churns turnover. It recommended a **capped inverse-volatility** scaler (w ~ 1/sigma, steady risk contribution) for live use rather than the more aggressive inverse-variance rule, judged against fixed-risk sizing on net return, Sharpe, max DD, ES, turnover and time near limits.

**Per asset class: risk unit and factors (assistant's claim).** FX: dollar P&L vol per pair and lot, pip or ATR for stops; aggregate by currency leg, carry, risk appetite; rollover, weekend gaps. Indices: dollar P&L vol per contract; regional equity beta, USD, rates, vol; overnight gaps modelled separately from the session. Metals: per contract; USD, real rates, inflation, haven demand vs industrial demand; rolls and thin periods. Energy: vol plus scenario loss and ES; benchmarks, USD, inflation, weather, supply; term structure, storage, limit moves. Crypto: vol plus stressed gap loss and ES, funding and liquidation tracked separately; crypto and BTC/ETH beta, USD liquidity, equity beta; UTC windows. Futures: not a class; normalise the underlying, plus basis and roll. Single stocks: vol per share plus issuer and event stress; market, sector, style, FX; earnings, halts, borrow, squeezes.

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

## Technique 13 - Stops and exits, and how exits feed sizing (chat 13)

Asked without any budget figure. Two rendered bar charts in this chat were captured as text into the chat file.

**Core answer (assistant's claim).** No stop rule is best everywhere: an exit adds return or Sharpe only when it uses real information about how the edge decays or reverses; otherwise it reshapes risk and adds cost. Treat the exit as part of the strategy and size from the resulting net loss distribution. Use stop-distance sizing (q = B_trade / planned stop loss per unit incl. fees and typical slippage) as the first limit, but make a **gap-aware tail-loss budget** (high loss quantile or ES of realised net losses) the binding survival constraint; take the smaller size. Sum of individual stop budgets understates shared gap risk across concurrent strategies. Keep three layers: trade-level thesis exit, execution policy, portfolio risk governor.

Exit types (assistant's claim): fixed vs ATR stops (compare out of sample by instrument and regime; cap ATR; ATR lags jumps); trailing stops (suit "stay while the move persists", give back profit, can cut off mean reversion); breakeven moves (after costs "breakeven" is often a loss; cluster of scratch trades); time exits (when edge decays with holding time or must not cross a session; for mean reversion, a max hold relative to the half-life ln(2)/mu); targets and partial exits (only when the conditional return beyond the target is low; a higher win rate alone proves nothing).

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| Optimal Mean Reversion Trading with Transaction Costs and Stop-Loss Exit (Leung, Li) | https://www.alphaxiv.org/abs/1411.5062 | 2015 | OU spread (theta, mu, sigma) with costs: optimal entry interval, take-profit b_L* and stop L; a tighter stop lowers the optimal target. Theory, no out-of-sample P&L. | X1, X3 |
| Optimal Trading with a Trailing Stop (Leung, Zhang) | https://www.alphaxiv.org/abs/1701.03960 | 2017 | Optimal liquidation with a trailing floor f(running max); with positive drift (GBM) a trailing stop is not optimal. | X1, X3 |
| Trends and Reversion in Financial Markets on Time Scales from Minutes to Decades (Safari, Schmidhuber) | https://www.alphaxiv.org/abs/2501.16772 | 2025 | Futures 2010-2023: reversal at very short minute scales, weak-trend persistence at longer intraday horizons, shortest-horizon effects vary by asset and session; tiny R^2. Horizon-aware exits. | X1, seed |
| Optimal Stop-Loss and Take-Profit Parameterization for Autonomous Trading Agent Swarm | https://www.alphaxiv.org/abs/2604.27150 | 2026 | 900+ crypto trades replayed over an exit grid: Sharpe 0.419 -> 0.525 -> 0.653 (ATR 1x stop, 2x target, circuit breaker after two losses); profit factor 1.639 -> 2.375; max DD $829.8 -> $757.2 (first pass). Randomised final split: not clean forward evidence. | X3, X5 |
| On Data-Driven Drawdown Control with Restart Mechanism in Trading (Hsieh) | https://www.alphaxiv.org/abs/2303.02613 | 2023 | ETF at a 10% DD limit: 20.97% cumulative with restart vs -8.42% without; BTC at 20%: 101.82% (Sharpe 2.14) vs 17.41% (0.70), observed DD 20.18%; with 0.1% costs Sharpe ~1.52 vs -0.04. Bounded-return assumption. | X2, X3 |
| When Do Stop-Loss Rules Stop Losses? (Kaminski, Lo) | https://doi.org/10.1016/j.finmar.2013.10.003 | 2014 | When stops help or hurt depends on return dynamics. | X3 |
| Risk Reduction Using Trailing Stop-Loss Rules (Dai et al.) | https://doi.org/10.1111/irfi.12310 | 2021 | Trailing stops as risk reduction. | X3 |
| Trading Securities Using Trailing Stops (Glynn, Iglehart) | https://doi.org/10.1287/mnsc.41.6.1096 | 1995 | Classic theory: positive drift can make trailing stops suboptimal. | X3 |
| Optimal Entry and Exit with Signature in Statistical Arbitrage | https://www.alphaxiv.org/abs/2309.16008 | 2023 | Path-signature timing for mean-reverting spreads. | X1 |
| Stop-loss and Leverage in Optimal Statistical Arbitrage with an Application to Energy Market | https://www.alphaxiv.org/abs/1706.07021 | 2017 | Mean reversion, stop-loss and leverage in energy. | X1, X2 |

**Growth vs survival (assistant's claim).** Exits that remove states with negative conditional expectancy, or stop regime-break losses from swamping the edge, can raise growth and Sharpe; exits that only cap rare losses while clipping winners and adding churn are insurance and should be labelled as risk control, not alpha. Test each strategy against no stop, fixed, ATR, trailing, time, target and partial exits on the same trades and fills, chronologically, counting configurations tried.

**Per asset class (assistant's claim).** FX: decentralised 24/5; model stops on the executable side (bid for long exits); rollover handoff, weekends, macro releases; round numbers attract clustered orders. Index futures: trade beyond cash hours, cash-open jumps, exchange limits and pauses; an ETF stop cannot fire while its venue is closed. Metals: gold liquid across sessions, silver jumpier; handle expiry, roll and delivery. Energy: inventory, OPEC, weather; limits can block exits; stop-market may fill far past, stop-limit may not fill. Crypto: weekends with thin venues; know whether stops trigger on last, mark or index price; liquidation can beat the stop; isolated vs cross margin. Futures: active contract and roll schedule; limit-lock means no exit. Single stocks: overnight and earnings gaps, halts, borrow recall. Log trigger, order type, venue, price source, decision, submission and fill times and spread for every stop.

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

---

## Unit and reading seeds

Trading ideas and market readings found in the answers that could become QMX units (strategies) or readings (signals that feed risk or other units). All results quoted are the assistant's report of each paper; none is verified here. "Reading" means a market-state input; "unit" means a tradeable strategy idea.

| Seed | Paper (link) | What the signal is | Kind | Style and instruments it suits | Data QMX would need |
|---|---|---|---|---|---|
| Multi-level order-flow imbalance (MLOFI) | Xu, Gould, Howison 2019, https://www.alphaxiv.org/abs/1907.06230 ; base OFI: Cont, Kukanov, Stoikov 2014, https://www.alphaxiv.org/abs/1011.6402 | Signed queue changes (adds, executions, cancels) at the best M book levels, regressed on mid change; 10 levels cut out-of-sample RMSE 15-74% vs best-level OFI on six Nasdaq stocks (10-second windows). Explanatory, not yet a proven net forecast. | Unit (scalper) and reading (entry veto) | Scalping on exchange books: index, metal and energy futures, liquid stocks, one crypto venue. Not CFDs or spot FX (no central book). | Venue-matched L2 or L3 book updates with timestamps; latency-tested future returns; fill markouts. |
| Order-book event impact | Eisler, Bouchaud, Kockelkoren 2010, https://www.alphaxiv.org/abs/0904.0900 | Impact response per event type (market, limit, cancel); signed event correlation lasts ~10-100 events (~10 s). | Reading (passive-fill veto) | Execution filter for scalpers on exchange books. | Event-level best quotes, trades, adds, cancels. |
| Auction-market order-flow features | ViperQ 2026, https://arxiv.org/abs/2609.13825 | Volume-area position, CVD slope and divergence, tape velocity, imbalance, fed to an RL policy; large returns on TSLA and NVDA but drawdowns -27.5% and -47.8%. | Unit features (needs heavy risk wrapping) | Short-horizon single stocks and futures. | Trades with aggressor side, session volume profile, book imbalance. |
| Market intraday momentum | Gao, Han, Li, Zhou 2018, https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351 ; international evidence 2021, https://centaur.reading.ac.uk/95566/1/Accepted-Version.pdf | First half-hour return predicts the last half-hour (S&P ETF, 1993-2013); extended internationally; reversal also documented (China 2019). | Unit (intraday) | Index futures or ETFs with a defined cash session. | Intraday bars aligned to the cash session, real entry and exit fills, news-day flags. |
| Intraday periodicity in crypto | Periodicity in Cryptocurrency Volatility and Liquidity 2021, https://www.alphaxiv.org/abs/2109.12142 ; The Quarter-Hour Effect 2026, https://www.alphaxiv.org/abs/2607.09426 ; Wang et al. 2020 (Bitcoin time of day) | Recurring time-of-day and quarter-hour cycles in volume, volatility and liquidity in a 24/7 market. | Reading (time-of-day vol and cost); possible unit | Crypto scalping and intraday; sizing by hour. | UTC-aligned venue bars, spread and depth by hour. |
| Intraday volatility seasonality model | Andersen, Bollerslev 1997; Multiplicative Component GARCH 2021, https://www.alphaxiv.org/abs/2111.02376 | Seasonal bucket x daily level x short-term clustering = vol forecast for the planned hold. | Reading (sizing input) | All intraday and scalping units, per instrument. | Timestamped returns by bucket, realised vol, daily vol forecast. |
| Cost-hurdle gated trading | Machine Learning-Based Bitcoin Trading Under Transaction Costs 2026, https://www.alphaxiv.org/abs/2606.00060 | Change position only when the forecast clears a cost-based hurdle. | Unit wrapper | Any high-turnover unit; shown on hourly BTC. | Forecast and a live round-trip cost estimate. |
| What not to build: OHLCV momentum on MNQ | Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ Futures 2026, https://www.alphaxiv.org/abs/2605.04004 | 11 of 14 five-minute signal families earned less gross than a 2-point round-trip friction; none passed all checks. | Negative seed (a falsification template) | Bar-based futures scalps. | Bars plus a realistic friction floor. |
| Volatility-managed exposure | Moreira, Muir 2017/2019, https://doi.org/10.1111/jofi.12713 ; Momentum Has Its Moments 2015, https://doi.org/10.1016/j.jfineco.2014.11.010 | Scale exposure by inverse recent realised variance; higher Sharpe for several factors; vol-scaled momentum. | Reading (sizing multiplier) and unit (vol-scaled trend or carry) | Any unit; trend, FX carry, index strategies. | Point-in-time realised vol, turnover costs, multiplier caps. |
| Macro-probability volatility signal for crypto | Do Prediction Markets Forecast Cryptocurrency Volatility? 2026, https://www.alphaxiv.org/abs/2604.01431 | Daily changes in Kalshi rate, CPI and recession probabilities forecast 5-day crypto realised vol for some channels (~7% BTC weight cut in one example). Volatility, not direction. | Reading | Crypto sizing overlay. | Timestamped prediction-market prices, crypto prices, USD, equity and vol controls. |
| News-attributed jump risk | Interpretable Systematic Risk around the Clock 2026, https://www.alphaxiv.org/abs/2604.13458 | LLM-classified news topics behind high-frequency equity and E-mini jumps; macro-jump factor Sharpe 0.78; real-time topic selection Sharpe 0.95 vs 0.28 intraday-only. | Reading (event-risk de-risking); possible unit | Index futures and equities around news. | High-frequency futures and equity prices, timestamped news, topic classifier. |
| Calibrated news sentiment (firm-day) | MFAST 2026, https://arxiv.org/abs/2609.23703 | Dedupe, classify, calibrate, aggregate to firm-day; long-short Sharpe 2.85 after 5 bp and a 10% ADV cap (US equities, June 2024-Jan 2026). | Unit (slower news swing) | Liquid single stocks. | Licensed timestamped news, entity mapping, point-in-time universe, costs. |
| Macro surprise and revision | LiveMacroEval 2026, https://arxiv.org/abs/2608.30110 | Hourly pre-release nowcasts vs a timestamped consensus; surprise size and direction. | Reading (event-window risk); small event unit | FX, indices, rates, metals around releases. | Release calendar, vintages, consensus snapshots, quotes before and after. |
| Uncertainty-penalised sizing controller | CAST 2026, https://www.alphaxiv.org/abs/2609.14205 | Predictor plus MPC risk penalty: more forecast uncertainty, less exposure; without the penalty, drawdowns up to ~80%. | Reading (sizing template) | Stock indices in the paper; template for any unit. | Online forecast and its variance, account drawdown. |
| Turbulence and correlation surprise | Kritzman, Li 2010, https://doi.org/10.2469/faj.v66.n5.3 ; Kinlaw, Turkington 2013, https://link.springer.com/article/10.1057/jam.2013.27 | Mahalanobis turbulence (nowcast) and its split into magnitude vs correlation surprise; CS > 1 with high magnitude surprise predicted higher next-day magnitude surprise. | Reading (bucket risk-off) | Per asset-class bucket. | Synchronised returns per bucket, shrunk covariance. |
| Absorption ratio and ARR | Kritzman et al. 2010 (SSRN 1633027); ARR 2020, https://arxiv.org/abs/2002.02008 | Variance share of the top factors (or autoencoder reconstruction) as a slower coupling confirmation; ARR helped some 5-minute and 1-hour vol and crash forecasts. | Reading | Buckets with enough liquid instruments. | Synchronised returns; for ARR, 1-second returns plus time of day. |
| Weekend crypto stress to Monday risk | Weekend Crypto Volatility and Monday Market Risk 2026, https://www.alphaxiv.org/abs/2610.35702 | Weekend crypto volatility as a Monday exposure-review trigger. | Reading (lead) | Monday index and FX exposure. | Weekend crypto vol, Monday open gaps. |
| Order-flow regime breaks | Regimes in the Order Flow 2026, https://www.alphaxiv.org/abs/2609.07989 | Structural breaks in intraday order-flow regimes. | Reading (candidate) | Intraday units on exchange books. | Intraday order-flow data. |
| Scheduled energy event window | Bu 2014, https://www.sciencedirect.com/science/article/abs/pii/S0140988314001236 | Crude volatility jumps around the weekly EIA report (Wednesday 10:30 New York). | Reading (event window) | Energy units. | EIA schedule, tick data around releases. |
