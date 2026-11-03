# R4 - alphaXiv research harvest: synthesis

Harvested 2026-11-03 from new alphaXiv assistant chats, one topic per chat. Every chat file in this folder holds the questions and answers verbatim, with the chat URL.

**How to read this file.** Every paper description below is the alphaXiv assistant's claim, copied in condensed form. A title in an answer is not proof of what the paper says, and some arXiv IDs point to 2026 preprints that nobody here has opened. Read the paper before building on it. Where the assistant itself flagged a limit ("not a sizing rule", "simulation only"), that flag is kept.

**Status.** Complete for this run (2026-11-03). The "Coverage" table lists every topic and its chat file.

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
| Technique 13 | Stops and exits | chat-13-stops-and-exits.md | done |
| Technique 18 | LLM-agent harnesses for alpha discovery | chat-18-agent-harness-alpha-discovery.md | done |
| Technique 2 | Breadth and effective number of bets | chat-02-breadth-effective-bets.md | done |
| Technique 15 | Stress tests and scenario generation | chat-15-stress-scenarios.md | done |
| Technique 5 | Allocating risk across strategies and clusters | chat-05-allocation-across-strategies.md | done |
| Technique 17 | Self-configuring parameters | chat-17-self-configuring-parameters.md | done |
| Technique 4 | Drawdown-controlled sizing | chat-04-drawdown-controlled-sizing.md | done (follow-up a needed one retry) |
| Technique 11 | Backtest overfitting and validation | chat-11-backtest-overfitting-validation.md | done (topic question needed one retry) |
| Technique 12 | Safe de-risking and re-risking | chat-12-safe-derisk-rerisk.md | done |
| Technique 14 | Early exit and meta-labelling | chat-14-early-exit-meta-labelling.md | done |
| Technique 16 | Trading costs, retail FX and crypto | chat-16-trading-costs-retail-fx-crypto.md | done |
| Technique 7 | Layered limits and alarm fatigue | chat-07-layered-limits-alarm-fatigue.md | done |
| Technique 9 | News and event risk | chat-09-news-event-risk.md | done |
| Technique 19 | LLM agents for risk monitoring | chat-19-llm-agents-risk-monitoring.md | done |
| Technique 20 | Approval gates and agent evaluation | chat-20-agent-approval-gates-evaluation.md | done |
| Technique 21 | Multi-agent market simulation for risk testing | chat-21-multi-agent-market-simulation.md | done |
| Technique 22 | The operator's saved papers, two per chat attached with '@' (deep dive, then combinations) | chat-22a ... chat-22e | done (5 chats) |
| Technique 3 | (skipped) | - | Not run as its own chat: its ground is covered by G (chat 29, multi-asset normalisation) and B (chat 24, scalping and costs). |

All 32 new chats (01, 02, 04-21, 22a-22e, and A-G as 23-29) have three turns: topic question, follow-up (a), follow-up (b). No topic in the brief's list is left unasked except topic 3, skipped as above.

- **Limits hit.** The Pro 5-hour limit hit after two chats (01, 10); later a "Go plan" usage limit stopped new messages until the operator upgraded. No limit was hit after the upgrade.
- **Bookmarks (library folder totals at the end of the run; totals include anything the folders held before).** qmx-risk-sizing: 145 papers. qmx-agents: 30 papers (agent-topic chats, including 19 and 20). qmx-unit-seeds: 1 paper. Every "Bookmark all to library" button in every chat was used. Chats 22a and 22c show no bookmark button (their cited papers are mostly the two attached ones, already in the library).
- **Exports.** alphaXiv has no file download for a chat. Its export is the chat header menu "Chat actions > Copy Markdown" (also "Copy Markdown + Reasoning"), which copies the whole chat (questions and answers) as Markdown. That was used for every chat run here plus conv-01 to conv-03, and each copy was saved to `exports\` under the same file name as its chat file, with the chat URL in a first-line comment. No file was downloaded, opened or run. See "Exports: what carries equations and diagrams" at the end of this file.

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

## Technique 18 - LLM-agent harnesses for alpha discovery (chat 18)

Asked without any budget figure; newest papers only. Bookmarked to **qmx-agents**.

**Core answer (assistant's claim).** "More search can improve a backtest while weakening the evidence for it." Count every candidate evaluation, make future information inaccessible by design (typed registries, not prompts), keep final out-of-sample results out of the agent's loop, and treat model-training contamination as a separate failure from code leakage (a leaky oracle still passed DSR). Critics are useful but deterministic tests are the safety boundary. Human approval promotes a frozen, hashed artifact into **paper trading only**; live money is a later, separate decision.

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| What survives honest evaluation? Leakage-safe, search-aware assessment of LLM-driven strategy discovery | https://arxiv.org/abs/2608.27734 | 2026 | Typed tools over a feature registry; deterministic publication-delay audit; trial ledger; DSR, PBO, bootstrap. No discovered strategy passed certification: a 102-trial winner had design Sharpe 1.69, held-out 0.18; ETF discovery -21%. A deliberately leaky oracle scored DSR 1.00. | X5, X7 |
| AQuA: Recursively Self-Improving Quantitative Trading Research Agents | https://arxiv.org/abs/2608.12841 | 2026 | Manager plus six specialists (Data Steward, Visual Analyst, Idea Miner, Factor Evaluator, Backtest Engineer, Research Librarian); falsifiable hypotheses first; restricted DSL; memory of failures. US-equity Sharpe +2.50 held-out (2 bp), ~2.00 causal walk-forward. A look-ahead bug (full-day volume) escaped both generator and LLM reviewer. | X7 |
| EvoQuantLab | https://arxiv.org/abs/2610.17130 | 2026 | LLM hypotheses + typed genetic programming; family-diverse elites; L0-L6 staged admission; outer loop patches the **next** cycle's protocol only. Short OOS: CSI 500 18.34% ann. / -4.78% DD; S&P 500 21.30% / -5.82%; crypto 37.91% ann. (7.17% cumulative, -3.23% DD), months-long windows. | X7, X5 |
| Quant-Arena: Benchmarking LLM Agents for Quantitative Trading Research | https://arxiv.org/abs/2610.30113 | 2026 | Five-candidate cap, sealed 2024 test, costed cash account. 1 of 38 configurations beat gross equal weight (18.4% vs 17.1%); iteration raised score for 9 of 9 models but returns for 4. Agents often found cash or exposure timing, not stock-picking. | X5, X7 |
| From Search to Research | https://arxiv.org/abs/2609.35559 | 2026 | Parallel search beat sequential at a matched ten-iteration budget; held-out results never flow back. | X7 |
| Alpha-R1 | https://arxiv.org/abs/2512.23515 | 2025/2026 | RL-trained LLM selects a sparse factor subset from a timestamped market-state description; 2025 S&P 500 47.87% (Sharpe 1.62) and CSI 300 40.57% (2.23) after 10 bp; one-year test. | X7, seed |
| QuantEvolve | https://arxiv.org/abs/2510.18569 | 2025 | Hypothesis and coding agents with evolutionary islands, a quality-diversity map, and an archive of rejects. Authors flag data snooping. | X7 |
| Cognitive Alpha Mining via LLM-Driven Code-Based Evolution | https://arxiv.org/abs/2511.18850 | 2025 | Seven-level agent hierarchy, code validation, quality checker, mutation and crossover. | X7 |
| AlphaAgent (operator's saved paper) | https://arxiv.org/abs/2502.16789 | 2025 | AST novelty, hypothesis alignment and complexity penalties against alpha decay; 11.0% excess (IR 1.5) CSI 500 and 8.74% (IR 1.05) S&P 500, 2021-24, after fees. | X7, seed |
| MASS (operator's saved paper) | https://arxiv.org/abs/2505.10278 | 2025 | Simulated heterogeneous investors and a learned aggregation; candidate stress and diversity mechanism. | X4, X7 |
| Can We Stop the Backtest Yet? Anytime-Valid Promotion Tests (Promote) | https://arxiv.org/abs/2611.03384 | 2026 | Lifetime testing-wealth ledger; each frozen candidate funded and tested only on returns after registration; replay promoted 0 of 24 rules; naive repeated looks crossed in 94.5% of null paths vs 0 of 3,000 funded. | X5 |
| Propose, Don't Judge | https://arxiv.org/abs/2609.27051 | 2026 | A frozen referee admitted 5-11x fewer sub-threshold factors than leaky referees; cost: ~500 trading days median wait and a certified portfolio with lower Sharpe than ungated. Factor-viability e-detector: 204-322 days delay, 0.5-1.5% false retirement (synthetic). | X5, X3 |
| FORESIGHT-9 | https://arxiv.org/abs/2608.29372 | 2026 | Nine counterfactual worldlines: the retrospective winner stayed first in 1 of 9; equal-weight or inverse-vol beat 31 of 36 agent runs. | X4 |
| Auditing LLM Alpha-Factor Mining: Metric Provenance and Full-Cohort Reanalysis | https://arxiv.org/abs/2610.29500 | 2026 | Keep the whole cohort, failures included; state which candidates each metric averages. | X5, X6 |
| AllPath | https://arxiv.org/abs/2610.26662 | 2026 | Approval queue, versioned strategy files, no agent approves its own proposal (operational case study). | X6, X7 |

**Growth vs survival (assistant's claim).** Evidence splits three ways: promising costed retrospective tests (AlphaAgent, AQuA), short sealed windows (EvoQuantLab, Quant-Arena), and prospective or live tests (crypto paper: no LLM method beat BTC). Strict gates cost growth (Propose, Don't Judge: long admission waits, lower certified Sharpe) but stop selection noise from reaching money.

**Per asset class (assistant's claim; research-design floors, not standards).** FX: bid/ask fills, swap, Sunday open, rollover, holidays; multiple years and policy regimes, 3-5 years OOS for slower signals. Indices: point-in-time membership, cash vs overnight futures sessions, rolls; 10+ years for daily signals. Metals: separate spot, futures, ETFs; actual contracts for P&L; a decade or more. Energy: contract-specific curves, limit moves, seasonality; a decade-plus, plus explicit stress because crises are rare. Crypto: venue-specific books, funding, liquidations, token survivorship; thousands of decisions across several years and venues plus exchange paper trading. Futures: raw contract histories and roll calendars; several full roll cycles. Single stocks: point-in-time constituents incl. delisted names; 10-20+ years; count independent events, not stock-days. False discovery is worst where evidence is thin relative to search: rare-event energy, wide single-stock searches, short crypto histories, heavily parameterised FX session filters.

## Technique 2 - Breadth and the effective number of bets (chat 02)

Asked without any budget figure. Some answers contain raw alphaXiv citation tags (citepaper=...) that the Copy button kept; they are left verbatim.

**Core answer (assistant's claim).** Count independent **net P&L bets**, not strategy names. Publish three numbers together: spectral effective rank of the strategy universe (what variance directions exist), the portfolio's effective number of bets or risk-contribution concentration (how the current allocation spreads risk), and incremental out-of-sample net performance per new strategy (whether it adds alpha). Breadth never raises the total risk limit; it only shapes how a fixed limit is split. A strategy counts as new breadth only for its residual P&L after common exposures (USD and funding, equity beta, commodities, rates, crypto beta, vol and liquidity), and only if that separation survives stress.

Formulas it gave: participation ratio N_PR = (sum lambda)^2 / sum lambda^2; entropy effective rank exp(-sum p log p), p = lambda / sum lambda; Euler risk contribution RC_i = w_i (Sigma w)_i / sigma_p^2 with concentration 1 / sum RC^2; diversification ratio DR = sum |w_i| sigma_i / sqrt(w' Sigma w); Fundamental Law IR ~ IC sqrt(B) TC with B_eff = B / (1 + (B-1) rho), which saturates at 1/rho.

**Breadth to budget (its procedure; the numbers are illustrative).** Total risk from survival constraints first; estimate breadth at three levels with shrunk and stressed correlations and use the lowest relevant conservative one; cluster by measured exposures and failure modes; roughly equal risk per supported cluster, each capped (example: 20% of total risk, so eight clusters start at 12.5%); within clusters weight by conservative posterior edge and marginal risk. Recompute exposures continuously, correlations daily or weekly, full breadth and allocation monthly or after a regime break.

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| Managing Diversification (Meucci) | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1358533 | 2009 | Effective number of bets: eigen-directions of covariance, each direction's share of portfolio variance, ENB = exp(entropy); conditional version for constrained portfolios. | X2, X6 |
| The Minimum Torsion Bet (Meucci) | scholar link in chat 02 | 2010 | Decorrelated bets that stay close to the original strategies. | X2 |
| The Fundamental Law of Active Management (Grinold); Portfolio Constraints and the Fundamental Law (Clarke, de Silva, Thorley) | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=290322 | 1989; 2002 | Skill x sqrt(breadth) x transfer coefficient; correlated forecasts saturate breadth. | X2 |
| The Effective Rank (Roy, Vetterli); Toward Maximum Diversification (Choueifaty, Coignard); ERC portfolios (Maillard, Roncalli, Teiletche) | scholar links in chat 02 | 2007; 2008; 2010 | Entropy rank; diversification ratio; equal risk contribution. | X2 |
| ...and the Cross-Section of Expected Returns (Harvey, Liu, Zhu) | https://doi.org/10.1093/rfs/hhv059 | 2016 | A large search raises the evidence bar; apparent backtest breadth is not skill. | X5 |
| In-Sample and Out-of-Sample Sharpe Ratios for Linear Predictive Models | https://www.alphaxiv.org/abs/2501.03938 | 2025 | Out-of-sample replication falls as assets and weak signals grow vs history; at 10% average correlation the out-of-sample Sharpe gain from adding assets reverses. | X2, X5 |
| Re-evaluating Short- and Long-Term Trend Factors in CTA Replication: A Bayesian Graphical Approach | https://www.alphaxiv.org/abs/2507.15876 | 2025 | 2010-2025 futures: short-term trend Sharpe 0.37, long-term 0.70, correlation 0.50; adding short-term trend to market cut max DD 20.3% -> 14.9% and lifted Sharpe; adding long-term trend on top did not raise Sharpe. All-in drag 1.38-1.68% a year. | X2, seed |
| Follow the Leader: Enhancing Systematic Trend-Following Using Network Momentum | https://www.alphaxiv.org/abs/2501.07135 | 2025 | Network (lead-lag) momentum net Sharpe 0.364 vs 0.233 MACD on 2005-2024 futures; P&L correlation to baseline 0.71-0.89: a related sleeve, not a new cluster. | seed |
| Is Trend Still Your Friend? | https://www.alphaxiv.org/abs/2607.01550 | 2026 | ~100 futures: since 2009 the fastest trend Sharpe fell to 0.12 while slower trend held 0.40; volatility-normalised tick size separates outcomes better than asset class. | X1, seed |
| Cross-asset network and turbulence study (crypto, fiat, S&P 500, 381 assets) | https://www.alphaxiv.org/abs/2605.30442 | 2026 | Near-zero average FX-equity correlation, but in high turbulence fiat becomes the leading transmitter; stress blurs class boundaries. | X3, X4 |
| TrendFolios | https://www.alphaxiv.org/abs/2506.09330 | 2025 | Higher return (7.35% vs 4.80%) but lower Sharpe (0.48 vs 0.51) and higher vol than 60/40: growth is not breadth. In-sample. | X2 |
| Optimal Portfolio Choice with Parameter Uncertainty (Kan, Zhou) | https://doi.org/10.1093/rfs/hhm045 | 2007 | Parameter-uncertainty-aware allocation. | X2 |

**Growth vs survival (assistant's claim).** Adding a strategy helps only when it adds incremental forecast or payoff structure after costs; a lower-Sharpe sleeve can improve the book by changing the tail (CTA example), while many weak correlated signals inflate in-sample results.

**Per asset class (assistant's claim).** FX: majors share the USD leg; long and short versions of one signal are one bet. Indices and single stocks: index scalpers, sector and stock signals can all be one equity cluster; count residuals after market and sector. Metals and energy: not one factor, not independent either (gold on real rates and USD; copper and oil on growth). Crypto: token count is a poor breadth proxy; one crypto factor plus liquidity; weekend coupling is under-measured. Futures: broadest universe, but instrument count still exaggerates; horizon and tick size matter. Sessions: Asia, Europe and US variants of one exposure are one bet unless residual P&L stays distinct.

## Technique 15 - Stress tests and scenario generation (chat 15)

Asked without any budget figure.

**Core answer (assistant's claim).** Stress-test the **whole trading system** (all strategies together, real entry, inventory, stop and exit logic, shared exit liquidity), not a return simulation. Historical replay and transparent hypotheticals are primary; reverse stress testing finds failures you did not think of; generators broaden scenarios but are not the authority on how bad it gets. For rare joint losses, matching marginal tails is not enough: the generator must preserve **extremal dependence** (which factors go extreme together). Separate survival gates (hard, portfolio and cluster) from growth controls (allocate by marginal contribution to stressed loss and liquidity demand). Keep a fixed crisis library so calm data cannot erase it. Cadence: limits daily; rolling dependence and liquidity monthly; full generator validation quarterly; sooner after a break.

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| Simulating Stress Laws under Extremal Dependence (SSGEN) | https://www.alphaxiv.org/abs/2608.13056 | 2026 | Split extremes into Pareto magnitude and angular direction; learn directions from intermediate exceedances (diffusion as the learner), extrapolate magnitude. Synthetic test: CoVaR error ~15% vs 25% empirical conditioning vs 47% t-copula. | X4 |
| Tail-GAN: Learning to Simulate Tail Risk Scenarios | https://www.alphaxiv.org/abs/2203.01664 | 2022 | Train the generator on benchmark **strategy P&L** VaR and ES. Synthetic: 4.6% VaR/ES error vs 3.4% historical simulation vs 21.3% WGAN; 20 stocks: 25.6% vs 25.9% historical. Needs LOB data for HF realism. | X4 |
| Correlation scenarios and correlation stress testing (Packham, Woebbeking) | https://www.alphaxiv.org/abs/2107.06839 | 2021 | Factor-driven correlation scenarios and reverse stress in a plausibility region; stressed 99% VaR often >50% above unstressed in calm markets. | X4 |
| Beating the Correlation Breakdown | https://www.alphaxiv.org/abs/2504.15268 | 2025 | Dependence-matrix inference with flexible scenario restrictions. | X4 |
| Reverse Stress Testing for Multivariate Scenarios | https://www.alphaxiv.org/abs/2606.09274 | 2026 | Work backward from an adverse outcome to a coherent multivariate scenario; nonparametric version is thin when few observations sit near the target. | X4 |
| Generating Plausible Stress Scenarios via Large Deviations | https://www.alphaxiv.org/abs/2606.31122 | 2026 | Severe but plausible configurations; candidate method. | X4 |
| Diffusion Factor Models | https://www.alphaxiv.org/abs/2504.06566 | 2025/2026 | Factor-structured diffusion for high-dimensional returns; sub-Gaussian assumption, heavy tails open. | X4 |
| CoFinDiff | https://www.alphaxiv.org/abs/2503.04164 | 2025 | Conditional diffusion for requested trend and volatility; multi-asset correlation is future work. | X4 |
| Quant GANs | https://www.alphaxiv.org/abs/1907.06673 | 2020 | Baseline generator. | X4 |
| Beyond Visual Realism: Toward Reliable Financial Time Series Generation | https://www.alphaxiv.org/abs/2601.12990 | 2026 | Realistic-looking paths can still give implausible strategy outcomes: validate through the downstream strategy. | X4, X5 |
| Negative Oil & Nickel Squeeze | https://www.alphaxiv.org/abs/2610.00951 | 2026 | Forced-closure feedback (WTI -$37.63, nickel 2022) as a scenario mechanism. | X4 |
| Where does the criticality live? (BTC perpetual liquidation cascades) | https://www.alphaxiv.org/abs/2607.27070 | 2026 | Taker order-flow variance compression preceded 6 of 7 cascades (population p ~ 5e-6) but is not a reliable per-event alarm; price autocorrelation fails on sudden-news events. | X3, seed |
| Robust Hedging Valuation Adjustment under Liquidity-Demand Stress | https://www.alphaxiv.org/abs/2606.26731 | 2026 | No-trade band widened 0.02 -> 0.10 -> 0.30 as liquidity fell: costs change the risk-trading trade-off. | X1, X4 |

**Growth vs survival (assistant's claim).** Limits cost growth when they cut a real, diversified edge; they pay for themselves when they stop a forced-exit spiral (FARSIGHT sim: 400 agents selling into a 2010-sized shock deepened the fall from 9.2% to 17.3%; external interrupt plus hard limits removed it). Make limits selective by horizon, microstructure and portfolio contribution (trend Sharpe fell far more in small-tick futures after 2008) rather than one haircut everywhere.

**Per asset class: scenarios (assistant's claim).** FX: surprise central-bank moves, intervention, peg or band break through a weekend, carry unwind, cross-currency basis. Indices: overnight gap opens, vol repricing, pauses and limits, futures-led sell-offs, vol-control deleveraging. Metals: squeezes and short covering, real-rate and USD shocks, margin hikes. Energy: front-month collapse near expiry, negative prices, limit moves, storage and delivery constraints. Crypto: perpetual liquidation cascades, stablecoin or collateral depeg, funding spikes, venue outages that concentrate forced flow elsewhere. Futures: roll squeezes, calendar-spread dislocations, margin shocks, delivery constraints; each leg separately. Single stocks: earnings gaps, halts and reopen auctions, borrow squeezes, fraud news. Model contagion as a **time-indexed dependency graph** with direction, lag and regime per edge, including one market closed or one venue down.

## Technique 5 - Allocating risk across strategies and clusters over time; pod-shop practice (chat 05)

Asked without any budget figure. Two rendered charts were captured as text into the chat file.

**Core answer (assistant's claim).** Hierarchical clustering to control concentration, robust optimisation for sleeve weights, a slower risk overlay to scale capital; a **static, capped, robust clustered budget is the control portfolio**, and any adaptive allocator must beat it after costs on both growth and drawdown across walk-forward periods. Cluster by what makes strategies lose together (shared signals, exposures, hours, liquidity), not asset labels. There is **no public causal evidence** that pod-shop scaling and stop-outs improve long-run returns: measure it with a shadow allocator (fixed budgets vs staged scale-and-cut vs robust clustered).

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| Schur Complementary Allocation: A Unification of HRP and Minimum Variance | https://www.alphaxiv.org/abs/2411.05807 | 2024 | A damping parameter gamma moves from hierarchical (0) to global minimum variance (1) using A - B D^-1 C at each split; simulated variance gain worth ~10 bp a year. | X2 |
| Nested Clustered Optimization Is One End of a Schur Bridge, and the Interior Is Sometimes Provably Better | https://www.alphaxiv.org/abs/2609.21271 | 2026 | NCO (within-cluster min-variance, then across clusters) as one end of a bridge; intermediate coupling can be best under estimation noise. Theory; no empirical returns. | X2 |
| Optimal Portfolio Construction: RL Embedded Bayesian HRP (RL-BHRP) | https://www.alphaxiv.org/abs/2508.11856 | 2025 | Bayesian shrinkage to sector means + Ledoit-Wolf + HRP; PPO picks sector and within-sector weights with turnover and ERC penalties. 2020-2025 OOS: CAGR 15.16% vs 13.36% static vs 12.33% benchmark; Sharpe 0.905 vs 0.846 vs 0.763; max DD -20.33% vs -19.10% vs -18.32% (more growth, slightly deeper drawdown). | X2 |
| Relative Robust Portfolio Optimization | https://www.alphaxiv.org/abs/1305.0144 | 2013 | Robust weights under estimation error. | X2 |
| Adaptive and Regime-Aware RL for Portfolio Optimization | https://www.alphaxiv.org/abs/2509.14385 | 2025 | Candidate regime-adaptive allocator. | X2 |
| Efficient and Near-Optimal Online Portfolio Selection | https://www.alphaxiv.org/abs/2209.13932 | 2022 | Online allocation reference. | X2 |
| Meta-Learning the Optimal Mixture of Strategies for Online Portfolio Selection | https://www.alphaxiv.org/abs/2505.03659 | 2025 | Allocation as an online mixture of strategies. | X2 |
| Regime-Adaptive Continual Learning for Portfolio Management | https://www.alphaxiv.org/abs/2606.00143 | 2026 | Regime layer adjusting window or budget only after persistent evidence. | X2 |
| Systematic Trend-Following with Adaptive Portfolio Construction in Cryptocurrency Markets | https://www.alphaxiv.org/abs/2602.11708 | 2026 | Crypto trend with adaptive construction. | seed |
| Dynamic Multi-Pair Trading Strategy in Cryptocurrency Markets with Deep RL | https://www.alphaxiv.org/abs/2606.04574 | 2026 | Crypto relative value. | seed |

**Pod-style policy it proposed (a starting policy to backtest, not proven thresholds).** Pilot budget 0.10% of NAV in one-day 99% ES; scale only after 60 live trading days and 100 trades with positive net performance and no breaches; +25% per review, at most one increase a month, capped by capacity and cluster limits. High-water mark on net P&L at assigned risk: at 2R drawdown halve the budget and freeze scaling; at 3R cut to a diagnostic budget; at 4R stop new risk and require human review (R = pre-defined expected-loss unit). Operational violations stop at once regardless of P&L. Re-entry after a documented cause review, at half the pilot budget with a fresh observation period.

**Growth vs survival (assistant's claim).** Dynamic allocators may add growth when they predict relative future net performance and move slowly; they may chiefly cut drawdowns when they de-risk in bad regimes; they hurt by chasing noisy winners, cutting losers just before recovery, and turnover. A bandit's "best arm so far" is a selection-bias trap with short, intermittent histories. Use ablations: signal alone, signal + static budget, signal + adaptive allocator.

**Per asset class (assistant's claim).** FX: G10 vs EM, USD legs, carry, trend and mean-reversion sleeves; carry unwinds synchronise in risk-off. Equity indices: regional beta; index contracts merge into one global equity cluster in sell-offs. Single stocks: sector, beta, style and event exposure; crowding in mega-caps and factors. Metals: precious vs industrial. Energy: oil and products, gas, energy equities separately; crowding in the same curve, month or roll. Futures: count by underlying exposure; roll dates create correlated execution stress. Crypto: majors vs small tokens; its own clock; high beta in deleveraging. Distinguish overnight, regular-session and shared-session risk, weekend gaps and event windows when estimating co-movement.

## Technique 17 - Self-configuring parameters across many instruments (chat 17)

Asked without any budget figure. One rendered chart was captured as text into the chat file.

**Core answer (assistant's claim).** Partial pooling by default, instrument or session overrides only when they earn their complexity in forward tests, and no autonomous path from tuning to live capital. Separate **contract facts** (tick size, multiplier, hours, minimum order, fees: exact configuration, never pooled) from **learned statistics** (volatility, costs, normalised stops, thresholds, edge: shared priors with instrument posteriors). Express parameters in comparable units (stops in vol units, costs relative to spread or vol). Shrink edge toward zero, not toward an optimistic group mean. Pooling hierarchy: instrument -> liquidity, venue or session subgroup -> asset class -> strategy-family default. Never pool clock-time session windows or roll, expiry, corporate-action and funding rules.

Shrinkage formula it gave: theta_i = w_i theta_hat_i + (1 - w_i) mu_g, w_i = tau_g^2 / (tau_g^2 + s_i^2); estimate group quantities inside each training fold only.

**Defaults-with-overrides policy (governance thresholds it proposed, not statistical constants).** An instrument earns an override with a plausible mechanism, >= 100 effective independent trades over >= 30 distinct sessions and >= 2 distinct volatility conditions (session override: >= 60 instances of that session), and a material, cost-stressed gain over the group default on identical untouched forward windows. Cadence: execution-state (vol, spread) continuous or daily; instrument posteriors and overrides weekly; group priors monthly; group definitions quarterly. Rate limits: at most 5% of a parameter's normalised value per weekly update, thresholds at most 0.1 group standard deviations per update. Automatic changes may only tighten risk; loosening risk or adding an override is a human decision.

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| Improving Bayesian Optimization for Portfolio Management with an Adaptive Scheduling (TPE-AS) | https://www.alphaxiv.org/abs/2504.13529 | 2025 | TPE that penalises variability more as the budget runs out; best Sharpe in 8 of 12 scenarios, lowest optimisation variance in all 12 (3.288 vs 2.980 standard TPE; variance 0.309 vs 1.367). Search stability on undisclosed backtests, not live robustness. | X1, X5 |
| Practical Bayesian Optimization of Machine Learning Algorithms (Snoek et al.) | https://www.alphaxiv.org/abs/1206.2944 | 2012 | Sample-efficient bounded offline search. | X1 |
| AlgoXpert Alpha Research Framework: a rigorous IS-WFA-OOS protocol | https://www.alphaxiv.org/abs/2603.09219 | 2026 | Prefer stable parameter plateaus, rolling forward tests, lock before final OOS, cost stress; USDJPY OOS Sharpe 2.34, MaxDD 4.21% with simplified execution. | X5 |
| Conservative Bandits | https://www.alphaxiv.org/abs/1602.04282 | 2016 | Explore a new configuration only when a lower confidence bound keeps cumulative reward above a baseline-relative floor. | X2, X3 |
| Rotting Bandits | https://www.alphaxiv.org/abs/1702.07274 | 2017 | Arms whose reward decays: discount stale observations so a decayed configuration is not kept. | X3 |
| Unlocking Profit Potential: Bayesian Optimization of Supertrend Parameters | https://www.alphaxiv.org/abs/2405.14262 | 2024 | Cautionary: in-sample maxima, one stock worse than default (-28%), no forward evidence. | X5 |
| AQuA (also chat 18) | https://www.alphaxiv.org/abs/2608.12841 | 2026 | Held-out US-equity long/short Sharpe 2.15, 2.50 with causal vol targeting, 2.00 walk-forward; positive each year 2021-2025 at 2 bp. | X7, seed |

**Growth vs survival (assistant's claim).** No direct evidence here that hierarchical pooling raises held-out returns; its benefit is lower estimation variance. Tuning can find profitable windows that still fail selection-aware tests (search-aware study: 0 of 5 LLM-found volatility-breakout strategies survived deflation despite OOS Sharpe 0.59-0.70).

## Technique 4 - Drawdown-controlled sizing (chat 04)

Asked without any budget figure. The follow-up (a) answer failed once ("Something went wrong") and was retried.

**Core answer (assistant's claim).** Distinguish reducing size **because the estimated edge fell** from reducing it **mechanically because equity fell**. Put the hard floor on the **whole book** (unreset global high-water mark), caps on clusters of shared exposure, and use strategy-level drawdown only as a soft throttle or review trigger; independent hard stops on many noisy strategies can cut several at once after a shared transient shock. Restart logic is separate from the hard constraint and must never reset the book's loss record.

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| Optimal Investment Strategies for Controlling Drawdowns (Grossman, Zhou) | https://doi.org/10.1111/j.1540-6261.1993.tb04708.x | 1993 | Exposure proportional to the cushion above a floor tied to the running max (V >= alpha H); no ruin in the model. | X2, X3 |
| On Portfolio Optimization under Drawdown Constraints (Cvitanic, Karatzas) | scholar link in chat 04 | 1994 | Generalisation. | X2 |
| The Grossman and Zhou Investment Strategy is Not Always Optimal (Klass, Nowicki) | scholar link in chat 04 | 2005 | The continuous-time rule does not transfer to discrete time; use dynamic programming. | X2 |
| Cherny, Obloj: nonlinear drawdown constraints | https://www.alphaxiv.org/abs/1110.6289 | 2013 | Transform to an unconstrained problem with modified utility. | X2 |
| Kardaras, Obloj, Platen: numeraire portfolio under drawdown constraints | https://www.alphaxiv.org/abs/1206.2305 | 2017 | Long-run growth optimality within the drawdown-constrained class. | X2 |
| On Control of Drawdown: Robust Invariance and Optimality (Hsieh) | https://www.alphaxiv.org/abs/2609.23272 | 2026 | Safe exposure = cushion x feasible direction; worst loss over an assumed return support must fit the cushion; Bellman choice of direction. SPY/TLT: higher expected terminal return than linear feedback at every tested limit (plotted). | X2, X3 |
| Drawdown-modulated feedback (Hsieh, Barmish) | https://www.alphaxiv.org/abs/1710.01503 | 2017 | TSLA 60-day OOS: Kelly $11,360 and 22.5% DD vs modulation $10,050 and 5.0% DD: protection at a clear growth cost. | X2 |
| On Data-Driven Drawdown Control with Restart Mechanism in Trading (Hsieh) | https://www.alphaxiv.org/abs/2303.02613 | 2023 | VT: -8.42% without restart vs +20.97% with, both 10% DD; BTC: +17.41% vs +101.82%, DD 20.00% vs 20.18% (limit overshoot). | X2, X3 |
| Fractional Kelly with a ridge penalty (Hakobyan, Lototsky) | https://www.alphaxiv.org/abs/2503.17927 | 2025 | Bernoulli p = 0.75: growth 0.13 -> 0.08 (-38%) for log-growth variance 0.22 -> 0.03 (-86%). | X2 |
| Drawdown Risk Beyond Brownian Motion (Landolfi) | https://www.alphaxiv.org/abs/2608.00127 | 2026 | Same Sharpe 1, different shapes: 90th-pct max DD 1.32x Gaussian for mean-reversion or short-vol, 1.05x for trend (but longer time under water); 1.48x with Sharpe uncertainty. Calibrate drawdown budgets per strategy archetype. | X2, X4 |
| When Alpha Breaks (Sanderink) | https://www.alphaxiv.org/abs/2603.13252 | 2026 | Model-specific health gate (AUROC 0.721, 0.750 final period vs VIX percentile 0.449 / 0.504) plus a position-level tail cap: final-period Sharpe 0.375 -> 0.925. | X3, X6 |
| Minimum regime performance (Alexander, Fabozzi) | https://www.alphaxiv.org/abs/2604.08356 | 2026 | Minimum Sharpe across candidate regime splits as a durability diagnostic (not predictive). | X5 |
| Drawdown Measure in Portfolio Optimization (Chekhlov, Uryasev, Zabarankin); constrained max-drawdown optimisation (Dorador) | scholar link; https://www.alphaxiv.org/abs/2401.02601 | 2005; 2024 | Drawdown-aware book optimisation. | X2 |
| AllocateSmartly, "Surfing the Equity Curve" (practitioner study) | https://allocatesmartly.com/surfing-the-equity-curve-using-trend-following-to-switch-strategies-on-and-off/ | 2026 | 100+ tactical strategies since 1973: moving-average equity filters improved max DD in nearly all variants but every variant lost to the average strategy on return and Sharpe. | X3 |

**Growth vs survival (assistant's claim).** Theory gives no universal "X% less CAGR for Y% less drawdown". Case studies show both sides: modulation can cost most of the gain on a path (TSLA), restart can recover return at the same drawdown (VT), and equity-curve filters trade return and Sharpe for drawdown. Equity-curve trading on noisy or mean-reverting strategies cuts at the wrong time; it is not a free Sharpe improvement.

**Per asset class (assistant's claim).** FX: aggregate USD, JPY and carry; weekend reopen gaps; carry and short-vol have quiet gains and sharp losses. Indices: overnight gap stress separate from daily vol; variation margin forces reductions. Metals: precious vs industrial; session boundaries, rolls. Energy: most conservative jump scenarios; inventory, limit moves, rolls. Crypto: tail and gap stress plus venue limits and collateral buffers; liquidation can fire before the strategy stop. Futures: control by notional, vol and stressed margin, not contract count. Single stocks: issuer, sector and event limits; borrow recalls and squeezes. Calibrate drawdown rules to each strategy's holding period: intraday loss accumulation for scalpers, close-to-open for overnight holds.

## Technique 12 - Gradual, safe de-risking and re-risking (chat 12)

Asked without any budget figure.

**Core answer (assistant's claim).** Three transferable controls: a **cumulative baseline budget** (conservative bandits: try a new strategy or setting only while a lower confidence bound keeps cumulative performance above a set fraction of the incumbent, at every time), **shared-uncertainty certificates** so an uncertain baseline is not charged twice, and **increase / hold / decrease bands** from dose-escalation designs. Ramp down faster than up. No paper gives a universal "growth surrendered per drawdown avoided" figure for trading.

**Ramp ladder it proposed (to backtest, not proven).** Six live tiers: 5%, 10%, 20%, 35%, 60%, 100% of the intended allocation; the first tier small enough that total failure is tolerable. Step up on matured, independent evidence, never on calendar time alone. Hard breach (loss limit, bad data, runaway orders, exposure breach): cut to zero and require human re-promotion. Soft breach (drawdown-budget use above 80%, or two completed windows with the lower confidence bound below the minimum edge): drop one tier at once. At every tier size to the tightest constraint (instrument loss budget, impact, depth, operations, book capacity); re-estimate costs at each size, never scale tiny-size costs linearly.

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| Conservative Bandits (Wu et al.) | https://www.alphaxiv.org/abs/1602.04282 | 2016 | Anytime constraint: cumulative reward >= (1 - alpha) x baseline; Conservative UCB pays an additive regret cost O(KL/(alpha mu0)), not the multiplicative cost of "save budget, then explore". | X2, X3 |
| Conservative Contextual Linear Bandits; Conservative Contextual Bandits: Beyond Linear Representations | https://www.alphaxiv.org/abs/1611.06426 ; https://www.alphaxiv.org/abs/2412.06165 | 2017; 2024 | Context-aware and nonlinear versions of the baseline guarantee. | X2 |
| Reserve-Aware Contrast Certificates for Conservative Bandits with Uncertain Baselines (Reserve-C4B) | https://www.alphaxiv.org/abs/2609.39106 | 2026 | Shared confidence set for candidate vs baseline: fallback to baseline fell 88.2% -> 19.4% (0.5% with prefix refresh) and reward vs baseline rose 1.0084 -> 1.0557 (1.0606) in a linear simulation. More growth kept for the same safety. | X2 |
| Bayesian Decision-optimal Interval Designs for Phase I Clinical Trials (BOIN) | https://www.alphaxiv.org/abs/1309.5019 | 2013 | Fixed batch at the current level, compare the observed harm rate with two boundaries: move up, stay, or move down one level. Simulated: right dose 46.2% vs 44.7% CRM, high-toxicity risk 14.8% vs 16.9%, poor allocation 28.7% vs 43.0%. | X2, X3 |
| The i3+3 Design; accelerated BOIN; BE-BOIN (backfill and late-onset toxicity) | https://www.alphaxiv.org/abs/1901.01303 ; https://www.alphaxiv.org/abs/2309.08616 ; https://www.alphaxiv.org/abs/2509.11333 | 2019; 2023; 2025 | Late-onset toxicity maps to delayed P&L (positions still open, costs not booked). | X2 |
| Provably Safe, Yet Scalable Reinforcement Learning | https://www.alphaxiv.org/abs/2606.14536 | 2026 | Hard safety projection instead of a soft penalty (100% safe episodes in robotics; 0% without the layer). Architecture lesson only. | X3 |
| Forecast-to-Fill: Benchmark-Neutral Alpha and Billion-Dollar Capacity in Gold Futures (2015-2025) | https://www.alphaxiv.org/abs/2511.08571 | 2025 | Gold futures alpha and capacity study (named as an idea source). | seed |

**Growth vs survival (assistant's claim).** Conservative UCB's constrained performance approaches plain UCB over time (cost is additive); Reserve-C4B shows smarter certificates recover most of the growth; dose-escalation designs cut poor allocation with similar sample sizes. All assume bounded, stationary rewards; a mean-reward floor does not prevent a ruinous realised loss, so hard loss limits stay outside the learner.

**Per asset class (assistant's claim).** Steps follow executable liquidity and loss capacity per instrument: FX by session and pair, aggregated by currency factor (24/5, weekend gaps, rollover); indices in micro-contract or small-ETF steps, regular vs overnight evidence kept separate; metals as separate buckets with roll and delivery constraints; energy the slowest ramp and smallest feasible size; crypto by venue with funding and weekend liquidity; futures in integer contracts; single stocks by liquidity tier and event calendar.

## Technique 14 - Early exit and fast invalidation: meta-labelling, triple barrier, exit classifiers (chat 14)

Asked without any budget figure. Four rendered charts were captured as text into the chat file.

**Core answer (assistant's claim).** Keep three separate layers: **meta-labelling** gates and sizes entries (take or skip a primary signal, probability as a size input after calibration); a **state-based hold/exit classifier** decides whether an open trade is still worth holding; **portfolio risk** sits above both. Triple barriers are one way to build outcome labels, not proof of profitable exits. Survival or hazard models estimate how long a trade stays viable, not whether its expected net value turned negative. Sequential tests inside a trade must be calibrated for how often they are checked (repeated looks cause false exits). Barrier width heuristic: d = max(k x sigma_h, c_min x round-trip cost), calibrated per instrument on forward data.

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| MLP-Initialized Reinforcement Learning for Exit Timing in SPX Short-Straddle Portfolios | https://www.alphaxiv.org/abs/2610.13126 | 2026 | Label each open-trade state "hold" until the hindsight-best executable exit, then "exit"; train a classifier on market, quote and position state. Locked 2024-26 test: return 35.01% vs 11.56% hold-to-expiry, Sharpe 1.651 vs 0.441, max DD 4.04% vs 12.82%; mechanical exits (fixed 5-day, PT/SL, combined) did worse than holding. Chronological split required. | X3, seed |
| Supervised Autoencoders with Fractionally Differentiated Features and Triple Barrier Labelling | https://www.alphaxiv.org/abs/2411.12753 | 2024 | Triple-barrier labels on crypto: 30-minute strategy IR 2.56, max DD 23.55% vs 59.46% buy-and-hold (bullish 2020-22 test). | X3, seed |
| Stock Price Prediction Using Triple Barrier Labeling and Raw OHLCV Data: Korean Markets | https://www.alphaxiv.org/abs/2504.02249 | 2025 | Triple-barrier labels on OHLCV; same-bar barrier crossings labelled as time-limit. | X1 |
| Label Unbalance in High-frequency Trading (operator's saved paper) | https://www.alphaxiv.org/abs/2503.09988 | 2025 | Class imbalance in short-horizon futures labels: set take/skip thresholds by cost of false positives on forward data, not accuracy. | X5 |
| When Does Order Flow Matter? State-Dependent L2 Liquidity-State Transitions in Crypto Futures | https://www.alphaxiv.org/abs/2607.09230 | 2026 | Order flow matters conditionally on L2 liquidity state; candidate exit-classifier input. | seed |
| Advances in Financial Machine Learning (Lopez de Prado): meta-labelling and triple barrier | book | 2018 | Origin of both methods. | X1, X3 |

**Growth vs survival (assistant's claim).** The SPX exit classifier improved both return and drawdown on one strategy and market; mechanical exits there cost return. No clean experiment in these papers isolates meta-labelling's effect on returns, so treat it as a design pattern; require shadow operation and forward validation before an exit model may close live trades.

**Per asset class (assistant's claim).** Scale barriers to each instrument's holding-horizon volatility and round-trip cost (spread, fees, slippage, funding). FX: session end is a vertical barrier only for intraday strategies; include rollover and weekend closure. Indices and stocks: overnight gaps and earnings mean the loss barrier is not a fill price. Energy and metals: event and roll days need their own handling. Crypto: 24/7, funding timestamps; OHLC bars cannot show which barrier came first, so use quotes or a conservative intrabar fill convention. Scheduled events enter as decision-time flags only, never as leaked labels.

## Technique 11 - Backtest overfitting and validation pipelines (chat 11)

Asked without any budget figure. The first answer failed once ("Something went wrong") and was retried.

**Core answer (assistant's claim).** Validate the **entire search process**, not only the winner. DSR, PBO/CSCV and an anytime-valid funded promotion test answer different questions and must not be collapsed into one score. "Rejected by a gate" is not "proven false". No universal "true winners lost vs false strategies caught" rate exists outside injected-truth simulations. Count independent opportunities, not bars: for AR(1) returns N_eff ~ N (1 - rho)/(1 + rho), so rho = 0.9 leaves about 5% of the nominal count.

**Pipeline it gave (in order).** Artifact and point-in-time audit -> realistic instrument-specific execution replay -> purged temporal robustness splits -> DSR and PBO diagnostics on the full search ledger -> funded sequential (or online) family gate -> untouched forward confirmation -> human authorisation -> shadow or capped live ramp -> live decay and risk monitoring. A re-tuned strategy family is one family with one budget; each re-tune is a new, counted trial.

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| The Deflated Sharpe Ratio (Bailey, Lopez de Prado) | https://doi.org/10.3905/jpm.2014.40.5.094 | 2014 | Sharpe threshold expected from selecting the best of N trials given trial Sharpe variance, skew, kurtosis and length; needs an honest trial count; no correlation matrix input. | X5 |
| The Probability of Backtest Overfitting (Bailey et al., CSCV) | https://doi.org/10.21314/JCF.2016.322 | 2016/2017 | Rank-instability diagnostic across combinatorial splits; coarse with ~20 candidates; low PBO did not mean a good absolute Sharpe (0.01 PBO, OOS Sharpe 0.18). | X5 |
| Can We Stop the Backtest Yet? (Promote) | https://www.alphaxiv.org/abs/2611.03384 | 2026 | Null: 0% crossings in 3,000 paths (vs 94.5% for repeated unadjusted tests); power: 70.1% at a 15 bp injected edge, ~none at 5 bp. The price of strictness in numbers. | X5 |
| On the Boundary of Admission Gates: An Injected-Truth Study of Falsification-First Selection | https://www.alphaxiv.org/abs/2610.07701 | 2026 | Injected-truth evaluation of admission gates (the only way to count winners discarded). | X5 |
| How Execution Assumptions Change Short-Horizon Sharpe Rankings | https://www.alphaxiv.org/abs/2610.05077 | 2026 | Execution assumptions reorder short-horizon strategy rankings: costs belong inside validation. | X1, X5 |
| A Backtesting Protocol in the Era of Machine Learning (Arnott, Harvey, Markowitz) | https://doi.org/10.3905/jfds.2019.1.064 | 2019 | Protocol checklist. | X5 |
| Safe Testing (Grunwald, de Heide, Koolen); E-backtesting | https://doi.org/10.1093/jrsssb/qkae011 ; https://doi.org/10.1287/mnsc.2023.01659 | 2024 | E-values for optional continuation; e-backtests of risk forecasts. | X5, X3 |
| Understanding Alpha Decay | https://doi.org/10.1287/mnsc.2022.4353 | 2022 | Decay of published or discovered alphas. | X3 |
| Also: Harvey-Liu-Zhu (2016), What survives honest evaluation? (2026), Propose, Don't Judge (2026), Auditing LLM Alpha-Factor Mining (2026), Certified Alpha Capacity (2026) | see chats 02, 18, 01 | | | X5 |

**Growth vs survival (assistant's claim).** Strict gates lose weak real edges and delay strong ones (Promote misses most 5 bp edges; Propose, Don't Judge waited ~500 trading days), but repeated unadjusted looks promote noise almost surely. Keep "not enough evidence yet" separate from "evidence against".

**Per asset class (assistant's claim).** No universal minimum history: set it from target net edge, turnover, dependence and the error budget, then check regime coverage. Use HAC errors, block bootstrap or sequential tests. Watch survivorship (single stocks, crypto tokens), roll construction (futures, energy, metals), cost assumptions per venue (FX, crypto), and overlapping intraday trades that shrink effective evidence.

## Technique 16 - Trading costs for retail-access FX and crypto (chat 16)

Asked without any budget figure.

**Core answer (assistant's claim).** One versioned cost ledger read by both the backtester and the live monitor, calibrated by **instrument, venue, account type and order type**; never one "bps per trade" across futures, CFDs and cash stocks (some costs hit at entry, some accrue while holding, some only at roll or borrow). Use the account's own executable quotes and fills, not interbank or ECN data. Estimate spread **distributions** (not means) by venue, symbol, UTC hour, weekday, session overlap, news window, holiday and rollover. Model each order type as it executes (market: spread + slippage; limit: fill probability + post-fill markout; stop: gap-through slippage). Charge swap and funding at the right timestamp and sign. Per order or position interval log: decision quote, requested and filled size, fill price, fee, spread cost, slippage, impact estimate, reject or partial status, swap or funding, net P&L; alert when realised costs drift from the model.

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| AutoQuant: Auditable Expert-System Framework for Execution-Constrained Auto-Tuning in Crypto Perpetuals | https://www.alphaxiv.org/abs/2512.22476 | 2025 | Next-bar delay, turnover-based fees and slippage, funding at the funding timestamp, per-bar ledger. BTC 4h: CAGR 522.5% zero-cost -> 430.8% fee-only -> 272.6% fully costed (Sharpe 2.71 -> 2.51 -> 2.05). | X1, X6 |
| The Market Maker's Dilemma: Fill Probability vs Post-Fill Returns | https://www.alphaxiv.org/abs/2502.18625 | 2025 | 232,897 live minimum-size Binance BTC-perp maker orders: filled orders averaged -0.8 bp (-0.3 bp after rebate); naive market making lost ~60% in ~3 days; a reversal-filtered setup made +0.71 bp per round trip. Fill probability is adverse selection. | X1, seed |
| Foreign Exchange Markets with Last Look | https://www.alphaxiv.org/abs/1806.04460 | 2018 | Last look tightens quoted spreads while rejecting trades that moved in the client's favour: a tighter displayed spread can mean a worse effective cost. | X1 |
| Dynamic slippage control and rejection feedback in spot FX market making | https://www.alphaxiv.org/abs/2603.07752 | 2026 | Slippage tolerance and rejection-feedback state (theory). | X1 |
| How Execution Assumptions Change Short-Horizon Sharpe Rankings | https://www.alphaxiv.org/abs/2610.05077 | 2026 | Execution assumptions reorder strategy rankings. | X5 |
| Model-Free Passive Execution via Order-Level Shadowing | https://www.alphaxiv.org/abs/2609.18019 | 2026 | Passive execution by shadowing observed orders. | X1 |
| Funding-Aware Optimal Market Making for Perpetual DEXs | https://www.alphaxiv.org/abs/2605.06405 | 2026 | Funding inside execution decisions. | X1, seed |
| Optimal Trading Filters and the Value of Predictive Signals | https://www.alphaxiv.org/abs/2610.24558 | 2026 | When a signal is worth trading after costs (no-trade filters). | X2, X5 |
| Slippage-at-Risk | https://www.alphaxiv.org/abs/2603.09164 | 2026 | A tail measure for slippage; feeds a slippage kill switch. | X3, X6 |
| Also: ML Bitcoin trading under costs (2606.00060), OHLCV momentum on MNQ (2605.04004), Strategic OTC market making with reputation feedback (2607.11328) | see chat 24 | | | |

**Growth vs survival (assistant's claim).** Costs are the first-order performance variable at short horizons: realistic costs halved one BTC perpetual strategy's CAGR; fixed 10 bp per position change turned naive sign strategies sharply negative. Cost-aware filters (trade only when forecast > cost) recover part of it.

**Per asset class (assistant's claim).** Index futures: spread in ticks, per-contract commissions, tick value, depth, roll execution; index CFDs: broker spread and overnight financing. Metals and energy: contract tick values, roll costs, event-window spreads; CFD financing. Futures: exchange and clearing fees, roll, margin. Single stocks: per-share fees, spread by name and hour, auctions, borrow for shorts. FX: markup vs raw-plus-commission accounts, last look, rejects, swap triple days. Crypto: maker/taker tiers, funding, venue-specific depth. Scalping is dominated by spread and slippage; intraday adds session and event gaps; overnight adds financing.

## Technique 7 - Coordinating layered limits and avoiding alarm fatigue (chat 07)

Asked without any budget figure. Mostly standards and cross-field sources rather than arXiv papers.

**Core answer (assistant's claim).** Selective, staged intervention for ordinary breaches, plus an independent account-level kill switch that never waits. Borrow **protection selectivity** from power grids: the nearest layer (strategy) trips first, with time grading so the cluster, asset-class and account layers act as backup only if the nearer one fails to clear. Define one small shared set of risk measures (stressed loss or drawdown contribution, gross and net exposure, leverage, liquidity, factor concentration) computed consistently at every scope. From alarm management: every alert must name a specific human action and deadline, or it is a dashboard metric, log line or digest item; rationalise each alert (cause, scope, priority, response, owner); shelve and flood-suppress; group pages by incident.

**Loss-budget burn alert (SRE pattern, a starting point, not a validated financial threshold).** Burn rate = observed loss-budget consumption rate / planned rate (B/T). Page only when an elevated burn persists in **both** a long and a short window (Google example: 14.4x over 1 hour and 5 minutes, which spends 2% of a monthly budget in an hour); send slower, lower-severity notices for sustained lesser burn. Keep the immediate hard-loss trip separate. Suppress duplicate pages while the state is unchanged; escalate if it worsens or stays unacknowledged.

| Source | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| IEEE C37.112: inverse-time characteristic equations for overcurrent relays | https://standards.ieee.org/standard/C37_112-2018.html | 2018 | Inverse-time grading: nearer protection acts first; remote protection is backup. | X3 |
| ANSI/ISA-18.2: Management of Alarm Systems for the Process Industries | https://www.isa.org/standards-and-publications/isa-standards/isa-18-series-of-standards | 2016 | Alarm lifecycle, rationalisation, priorities, shelving, flood handling, performance monitoring. | X6 |
| EEMUA Publication 191 (Edition 4) | https://www.eemua.org/products/publications/digital/eemua-publication-191 | 2024 | Human-centred alarm load and flood guidance. | X6 |
| Google SRE book and workbook: Alerting on SLOs | https://sre.google/workbook/alerting-on-slos/ | 2016/2018 | Multi-window, multi-burn-rate alerts; error budgets. | X6 |
| Drew et al.: alarm fatigue with physiologic monitors (ICU) | https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0110274 | 2014 | Measure alarms by whether they were actionable, not by threshold crossings. | X6 |
| CME Globex Kill Switch | https://www.cmegroup.com/tools-information/webhelp/globex-credit-controls/Content/Kill-Switch.html | - | Exchange-side kill switch as a design reference. | X3 |
| Characterizing Cross-Relay Generalization Failure in ML-Based Power System Protection | https://www.alphaxiv.org/abs/2610.28348 | 2026 | Learned protection fails to generalise across relays: keep deterministic trips. | X3 |
| E-values: Calibration, Combination, and Applications (Vovk, Wang) | https://doi.org/10.1214/20-AOS2020 | 2021 | Combine evidence from several monitors validly. | X3, X6 |

**Growth vs survival (assistant's claim).** Nuisance trips cost production and teach operators to ignore alarms; no source gives a validated trading-book false-trip rate, so measure it: log every trip with whether it was actionable and what the strategy would have done.

**Per asset class (assistant's claim).** Same account-level emergency protection everywhere; local thresholds and alert timing aware of liquidity, sessions, venue rules and whether the planned response (cancel, reduce, hedge, pause) can execute. FX: sessions, rollover and releases are separate liquidity regimes; a calendar window may tighten controls but never silently loosen hard limits. Crypto: no quiet hours, so digest non-urgent alerts and page only actionable ones. Exchange products: halts and limit moves mean "cannot act"; escalate rather than retry. Session opens: expect bursts; group by incident.

## Technique 9 - News and event risk for automated short-horizon trading (chat 09)

Asked without any budget figure.

**Core answer (assistant's claim).** Estimate event **risk** separately from event **alpha**; a volatility forecast is not a direction forecast. For scalpers the safe default is **flat through the release and the first post-event liquidity reset**; "widen the stop" is not a default (it raises money at risk exactly when execution is least predictable). If a strategy deliberately trades an event, size it against a stressed gap and define a maximum loss that does not depend on a stop fill. Unscheduled news has no pre-window: treat it like a circuit breaker on a trustworthy signal (block entries, cancel stale orders, cut exposure if spreads, gaps or vol breach limits). Gate re-entry on observed liquidity (spread, depth, price impact), not only on a timer. Session opens and closes are liquidity transitions, handled per instrument calendar.

**Event-window starting controls (minutes before / after; the assistant's conservative starting values, not paper optima).**

| Class | Event | Window |
|---|---|---|
| FX | High-impact release | 5-10 / 15-30 |
| FX | Central-bank statement (press conference as a second event) | 10-15 / 30 |
| FX | London 4 pm fix and other fixes | 15-30 / 10-15 |
| Stock indices | Open and close | 5-15 / 10-15 |
| Stock indices | CPI or jobs | 5-10 / 15-20 |
| Stock indices | FOMC (plus press conference) | 10-15 / 30 |
| Gold and metals | Macro release; central bank; session transitions | 5-10 / 15-30; 10-15 / 30; 5-10 / 10-15 |
| Energy | Inventory report; OPEC announcement | 5-10 / 10-20; 15-30 / 30-60 |
| Crypto | Macro release; scheduled upgrade or unlock; incident | 5-10 / 15-30; 30-60 / 30-60; none before / at least 30-60 after verified stabilisation |
| Futures | Macro; roll, first notice, expiry | 5-10 / 15-30; 30-60 / 30-60 |

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| What Events Matter for Exchange Rate Volatility? (Martins, Lopes) | https://www.alphaxiv.org/abs/2411.16244 | 2024 | Sparse event-volatility model on 24-hour AUD 5-minute returns with 117 releases: nine releases matter (FOMC decision and minutes, US CPI, payrolls, retail sales, RBA, AU employment, GDP, retail sales); effects decay within ~30 minutes. Learn which events matter and how long. | X4, seed |
| Returns and Order Flow Imbalances: Intraday Dynamics and Macroeconomic News Effects | https://www.alphaxiv.org/abs/2508.06788 | 2025 | Index futures: price impact rises and liquidity withdraws before releases; volatility spikes in the first 5 minutes after. Gate on liquidity, not only the clock. | X3, X4 |
| Warp speed price moves: Jumps after earnings announcements | https://www.alphaxiv.org/abs/2601.08962 | 2026 | The stock jumped in >90% of after-hours earnings sessions vs ~3% otherwise; a surprise rule earned 1.80% per trade before frictions (much less after). | X4, seed |
| Fast Numbers, Slow Language: Quantitative and Qualitative Earnings Signals | https://www.alphaxiv.org/abs/2606.29734 | 2026 | Numbers move prices fast, language slower: two-speed earnings signals. | seed |
| Forecasting Intraday USD/CAD with News-Derived Monetary-Policy Signals | https://www.alphaxiv.org/abs/2609.32773 | 2026 | Monetary-policy news signals for intraday FX. | seed |
| Classics: Andersen, Bollerslev, Diebold, Vega (2003, real-time FX price discovery); Fleming, Remolona (Treasury response to public information); Patell, Wolfson (1984, intraday speed of adjustment to earnings); Lee, Mucklow, Ready (1993, spreads and depth around earnings) | in chat 09 | | Surprises, not the event itself, move prices; liquidity thins around news. | X4 |

**Growth vs survival (assistant's claim).** Evidence is strongest for FX volatility around major releases, index-futures liquidity around macro news, and equity price discovery around earnings; thin for oil inventory, gold, fixes, unlocks, crypto incidents and roll days, so those windows are conservative placeholders to be measured. Flattening gives up event alpha that short-horizon strategies mostly cannot capture net of costs; strategies built for events should be separate, tested units.

## Technique 19 - LLM agents for risk monitoring (chat 19)

Agent topic: newest work asked for. No budget figure.

**Core answer (assistant's claim).** The 2026 evidence supports traceable oversight plus hard-coded controls, not LLMs catching live losses sooner. No paper shows a human operations team detecting live multi-strategy problems earlier or avoiding real losses because of an LLM monitor. Build a **deterministic risk monitor with an LLM explanation layer**, not an LLM risk controller: rules raise alerts; the LLM reads decision traces, drafts a diagnosis and a review checklist, and never trips or clears a control.

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| ReguSim: Evaluating LLM Agent Rule Grounding in Financial Compliance | https://arxiv.org/abs/2608.19974 | 2026 | Alert-quality evidence: on 900 synthetic marked records the best LLM F1 was 70.9%; a high-recall model had 91.7% recall but 59.5% precision; a trained logistic-regression detector scored 89.2% F1. Measure precision and recall of every alert source; prefer trained detectors for known patterns. | X6, X7 |
| NEXTFUND: A Unified Performance Tracking Platform for Agentic Portfolio Management | https://arxiv.org/abs/2607.11141 | 2026 | Time-aligned record of observations, signals, decisions, rationales and executions; analyst signals agreed ~92.9% but final actions only ~36.4%. Record the decision chain so divergence is inspectable. | X6 |
| Oculi: A Conversational Agentic Platform for Automated Credit Risk Analysis | https://arxiv.org/abs/2608.28944 | 2026 | LLM directs analysis, deterministic tools compute; 23.8% of its feature suggestions were invalid in a small test and were filtered. Validate every LLM proposal before use. | X7 |
| Positive-Unlabeled Learning for Agent Safety False Alarm Auditing | https://arxiv.org/abs/2610.02925 | 2026 | Ranks existing alarms for human review (33.3% more false alarms recovered than the best PU baseline). A triage layer for alarm fatigue, not a better detector. | X6 |
| SwingGuard (daily strategy generation plus a five-minute crypto risk controller) | https://arxiv.org/abs/2610.12988 | 2026 | Risk triggers (drawdown, ATR, momentum, exposure, on-chain and news anomalies, six-hour accumulation) start a deeper diagnosis; retrieves similar past risk snapshots; staged recovery. Backtest only (2024-2025 BTC/ETH). | X3, X6 |
| Trading Agents or Market Crashers? | https://arxiv.org/abs/2609.19705 | 2026 | Simulated kill switches contained some cascades, but a fast-path threshold caused repeated calm-market halts. | X3 |
| FinRiskAtlas; RiskReason | https://arxiv.org/abs/2608.25325 ; https://arxiv.org/abs/2611.01236 | 2026 | Benchmarks for LLM risk review and verifiable risk reasoning; synthetic scenarios. | X7 |

**Growth vs survival (assistant's claim).** An LLM layer adds latency, cost and false alerts; its value is faster diagnosis after a deterministic alert, which no paper has measured in operator time saved. The monitor must not slow the kill path.

**Per asset class (assistant's claim; design requirements, not benchmarked).** FX: session handovers, weekend gaps, fixing windows, whole-book currency exposure, broker-to-broker price divergence, swap at each broker's rollover time. Indices: cash vs futures vs after-hours, auctions, basis, constituent closures, venue circuit breakers. Metals: broker "spot" vs exchange futures, fixing windows, margin changes. Energy: expiry, roll, first notice, inventory events, price limits, unit and multiplier checks. Crypto: no quiet hours; funding, liquidations, mark vs index vs last, venue outages, stablecoin and chain events. Futures: contract month, roll, settlement, variation margin, limit status from the exchange calendar. Single stocks: halts, auctions, corporate actions, borrow and short-sale rules.

## Technique 20 - Approval gates and agent evaluation (chat 20)

Agent topic: newest work asked for. No budget figure.

**Core answer (assistant's claim).** A gate helps only if it sits **outside the agent's control**, shows the **complete effect**, and authorises **exactly the version that later executes**. Use human gates for judgment (strategy promotion); make deterministic controls responsible for hard limits and exact action binding. Papers show gates catch things rule checks miss and add delay; none shows human approval improves financial outcomes at scale or measures real rubber-stamping.

**Approval workflow for one operator (assistant's proposal, five steps).** (1) The agent submits a frozen proposal with an immutable ID and hash; it cannot promote, change approval status, change portfolio limits, reach broker credentials or send live orders. (2) Deterministic checks run before the queue: reproducible from frozen inputs, contract tests, no data later than its decision time, no evaluation-window reuse, realistic costs, limits respected. (3) The operator sees one screen (what changed, why, evidence after costs, worst loss, failure modes) and chooses promote, reject or request changes; promotion binds to the candidate hash, instruments and limits. (4) The runtime holds a narrow capability to activate only that version; independent order, strategy and portfolio limits; a kill switch that needs no model; material changes or stale approvals revoke it. (5) An append-only, replayable audit record (hashes, checks, the exact screen shown, approver, decision, later fills and rollbacks).

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| I-HITL: Inalienable Human-in-the-Loop | https://arxiv.org/abs/2610.35835 | 2026 | 9 of 10 models raised their own spending cap by fetching an emailed OTP. The approval channel must be out of the agent's reach. | X7 |
| Approve What, Exactly? Effect Binding and Trusted Rendering for Agent Step-Up Authorization | https://arxiv.org/abs/2610.21063 | 2026 | Gateway turns the call into a canonical effect descriptor, renders the card from it, a passkey signs the digest, execution uses the stored descriptor; single-use, expiring grants. Blocked substitution and replay in 27,108 scripted trials; forged-narration attack success fell 0.54 to 0.03; flooding still worked 45-60% against a modelled human. | X7 |
| AllPath: Layered Verification for a Deployed, Self-Revising LLM Trading Agent | https://arxiv.org/abs/2610.26662 | 2026 | Agent proposes orders and revisions but cannot execute, edit files or approve itself; the operator approved 4 of 6 reflection proposals; median decision delay 8.8 hours (11 min to 80.7 h); paper account, single operator. | X7 |
| Reliable Before Profitable: QuantHarness | https://arxiv.org/abs/2610.26101 | 2026 | Task contract, spec, data bindings, output protocol, plan; a separate runtime (Harness Core) decides each stage transition; 90.72% task success on 97-task FinRelBench (A-shares). Governs development, not live risk. | X5, X7 |
| Loopjacking: Hijacking Human-in-the-Loop Approval | https://arxiv.org/abs/2609.21081 | 2026 | A correct diff at review time is not enough if state changes before use: re-check at use time. | X7 |
| Approval Laundering; Agent Approval Laundering | https://arxiv.org/abs/2609.38983 ; https://arxiv.org/abs/2609.28586 | 2026 | Approved actions can carry transitive effects beyond the approved call. | X7 |
| AStockArena; Measurement Boundaries in LLM Financial Agent Evaluation | https://arxiv.org/abs/2611.00515 ; https://arxiv.org/abs/2609.32379 | 2026 | Audit that reported actions match orders and account changes, and rationales use contemporaneous evidence; fixed-tape evaluation limits. | X5 |

**Growth vs survival (assistant's claim).** Gates cost latency (AllPath's 8.8-hour median) and missed opportunities; they protect against agent self-escalation, swapped actions and unreviewed changes. Keep human review for promotion and material change only; never put a human in the kill path.

**Per asset class (assistant's claim; operational checks, not paper results).** One gate design for all classes; the packet's pre-queue checks are class-aware: FX instrument type, calendar, rollover and value dates; indices: cash vs ETF vs futures, point-in-time membership, auctions, basis; metals and energy: contract month, delivery, roll, storage, price limits, negative prices; crypto: exchange, custody path, funding, liquidation rules, mark vs index; futures: executable contract series separate from back-adjusted series; single stocks: point-in-time constituents with delisted names, corporate actions, borrow.

## Technique 21 - Multi-agent market simulation for risk testing (chat 21)

Asked for the strongest work, classics allowed. No budget figure.

**Core answer (assistant's claim).** A rule can look safe against a fixed historical tape and fail when other agents react: in one 2026 study, price-triggered selling turned a simulated 9.2% crash into a 17.3% drawdown with 400 agents, while external fast halts and hard loss limits largely removed the amplification. Use simulators as complementary test benches: ABIDES for the configurable exchange and strategy integration, ABIDES-MARL for adapting liquidity providers, CrashGym for controlled cascade and intervention experiments. None covers a multi-asset portfolio across QMX's venues; realism must be earned by calibration.

| Paper | Link | Year | What to borrow | Layer |
|---|---|---|---|---|
| ABIDES: Towards High-Fidelity Market Simulation for AI Research | https://arxiv.org/abs/1904.12066 | 2019/2020 | Event-driven, message-based exchange; strategies as agents; latency and computation delays. Best integration start; NASDAQ-like equity. | X4 |
| ABIDES-MARL | https://arxiv.org/abs/2511.02016 | 2025 | Liquidity responds strategically; a fixed impact assumption can mislead. An opponent-adaptation test, not crisis realism. | X4 |
| CrashGym: Measuring the Decision Value of Experimentation for LLM Agents in Counterfactual Market Crashes | https://arxiv.org/abs/2610.29245 | 2026 | Switch stress channels on and off and score decisions against counterfactuals; one synthetic asset. | X4 |
| Trading Agents or Market Crashers? | https://arxiv.org/abs/2609.19705 | 2026 | The 9.2% to 17.3% amplification result; external halts and hard loss limits contain it. | X3, X4 |
| LOB-Impact Benchmark; FlowLOB; M3 | https://arxiv.org/abs/2610.27100 ; https://arxiv.org/abs/2608.13096 ; https://arxiv.org/abs/2608.19227 | 2026 | Generative limit-order-book models and a benchmark for emergent market impact. | X4 |
| Get Real: Realism Metrics for Robust Limit Order Book Market Simulations | https://arxiv.org/abs/1912.04941 | 2019/2020 | Stylised-fact checks before trusting any simulator. | X4, X5 |
| EvoMarket | https://arxiv.org/abs/2604.18046 | 2026 | Broadest market-mechanism set (multi-asset, cross-day, institutional rules); calibrated to China A-shares. | X4 |
| Agent-Based Simulation of a Perpetual Futures Market; Can AI Make Money in Crypto? | https://arxiv.org/abs/2501.09404 ; https://arxiv.org/abs/2609.34510 | 2025; 2026 | Perpetual funding and liquidation mechanics; the gap from crypto backtests to live markets. | X4 |
| How to Evaluate Trading Strategies: Single Agent Market Replay or Multiple Agent Interactive Simulation? | https://arxiv.org/abs/1906.12010 | 2019 | Replay vs interactive simulation give different verdicts. | X5 |
| LLM Multi-Agent Systems Are Vulnerable to Herding and Runaway Cascades | https://arxiv.org/abs/2610.30769 | 2026 | LLM agents cascade and self-correct less than humans (not a market test): many similar agent strategies are one crowded bet. | X7 |

**Growth vs survival (assistant's claim).** Simulation finds interaction failures a backtest cannot (crowding, liquidity withdrawal, cascades) but its numbers are only as good as its calibration; use it to compare rules, not to forecast P&L.

**Per asset class (assistant's claim).** Model the venue's rules, not just its prices. FX: dealer liquidity plus ECN books, sessions, last look, releases and rollover separately. Indices and listed futures: continuous book plus auctions, rolls, price limits, margin. Metals and energy: futures curve, rolls, delivery, storage and carry, inventory shocks, location and product basis. Crypto perpetuals: fragmented venues, funding, leverage, liquidation engines, mark vs index, cross-venue basis and latency. Single stocks: per-symbol books, auctions, halts, corporate actions, sector correlation.

## Technique 22 - The operator's saved papers, two per chat (chats 22a-22e)

Each chat attached two papers from the operator's library with '@', asked how each could serve QMX risk and sizing, then went deeper (liftable parts, asset classes, growth vs protection) and finally asked for combinations and the one idea to build first. The assistant's verdict on all ten: **none is a live risk-and-sizing layer**; each supplies a proposer, an evidence source or a governance pattern to sit in front of deterministic limits.

| Paper | Link | Year | What to borrow (assistant's claim) | Layer | Chat |
|---|---|---|---|---|---|
| AlphaAgent: LLM-Driven Alpha Mining with Regularized Exploration to Counteract Alpha Decay | https://www.alphaxiv.org/abs/2502.16789 | 2025 | Idea, factor and evaluation agents; originality (AST novelty), hypothesis alignment and complexity regularisers; duplicate screening. Reported 11.00% excess (CSI 500) and 8.74% (S&P 500), IR 1.49 and 1.05, max DD ~9%, test 2021-2024. A candidate-admission discipline. | X5, X7 | 22a |
| MASS (multi-agent simulated investors to portfolio) | https://www.alphaxiv.org/abs/2505.10278 | 2025 | Consensus minus disagreement across simulated investor types; weekly equal-weight top 20%, 0.1% round-trip cost; small 2023 returns. Use disagreement as a portfolio or stress input, never a sizing authority. | X4, seed | 22a |
| Diffusion Predictive Control with Constraints (DPCC) | https://www.alphaxiv.org/abs/2412.09342 | 2024 | A robot controller, not trading: lift the pattern propose, constrain, execute one step, observe, replan, for order and position paths under exposure, turnover and drawdown limits; constrained stress-path generation is a new use. | X2, X4 | 22b |
| QuantaAlpha | https://www.alphaxiv.org/abs/2602.07085 | 2026 | Evolves research trajectories (mutation and crossover) over hypotheses and symbolic factors; CSI 300 IC 0.0472, excess 4.68%, IR 0.65. AutoScientist-Quant (https://www.alphaxiv.org/abs/2608.28632) reports lookahead in an evaluation pipeline reused by QuantaAlpha: treat its numbers as unverified. | X5, X7 | 22b |
| MarketSenseAI 2.0 | https://www.alphaxiv.org/abs/2502.00415 | 2025 | Monthly long-only stock selection; its news, fundamentals, macro and dynamics agents can emit typed, timestamped, expiring evidence records; risk metrics are analysis inputs only. | X7 | 22c |
| EvolveTrade: Experience-Driven Policy Refinement for Self-Evolving LLM Trading Agents | https://www.alphaxiv.org/abs/2609.17632 | 2026 | A policy agent revises tool-use and analysis instructions every five trading days from decision traces and outcomes. Learn the procedure, never the risk boundary; every policy change goes through versioned replay and human promotion. | X7 | 22c |
| Label Unbalance in High-frequency Trading | https://www.alphaxiv.org/abs/2503.09988 | 2025 | Three-class, fee-threshold labels for one-minute futures moves; class weights, cost-sensitive and focal losses for rare classes. Six contracts, 20 days, no net portfolio results: a signal-model experiment only. | X1, seed | 22d |
| FinRL-X: An AI-Native Modular Infrastructure for Quantitative Trading | https://www.alphaxiv.org/abs/2603.21330 | 2026 | Strategy proposals kept separate from the final weight and execution interface, with risk overlays downstream; daily-rebalanced paper account Oct 2025-Mar 2026 +19.76%, Sharpe 1.96, max DD -12.22% (authors: an execution test, not proof of alpha). | X2, X6 | 22d |
| Reliable Before Profitable: QuantHarness | https://www.alphaxiv.org/abs/2610.26101 | 2026 | Governed development: task contract, data bindings, frozen spec, stage transitions decided by a runtime outside the agent, retained rejected outputs. FinRelBench task success 90.72% vs 74.23-84.54% for Codex CLI, SWE-agent, Aider, OpenHands (chart captured in chat 22e). Reliability, not return. | X5, X7 | 22e |
| Trading-R1: Financial Trading with LLM Reasoning via Reinforcement Learning | https://www.alphaxiv.org/abs/2509.11420 | 2025 | Qwen3-4B, staged SFT then RL (thesis structure, evidence-grounded claims, five-way recommendation with volatility-aware labels); six US equities and ETFs, June-August 2024, +2.38% to +8.08%, Sharpe 0.86-2.72. Narrow test; a proposer whose risk decision must live elsewhere. | X7, seed | 22e |

Related papers these chats surfaced: Propose, Don't Judge (https://www.alphaxiv.org/abs/2609.27051), Fake News, Real Crashes (https://www.alphaxiv.org/abs/2610.26438), SHARP rubric policy (https://www.alphaxiv.org/abs/2605.06822), FINSABER (https://www.alphaxiv.org/abs/2505.07078), Position Sizing as a Risk-Control Variable: A Closed-Loop GRPO Framework for LLM Trading (https://ieeexplore.ieee.org/document/11676654/), an injected-truth study of admission gates (https://www.alphaxiv.org/abs/2610.07701), Measuring Strategy-Decay Risk: Minimum Regime Performance (https://www.alphaxiv.org/abs/2604.08356), Anytime-Valid Distribution Shift Detection via Predictive Rank Martingales (https://www.alphaxiv.org/abs/2609.00536), Anytime-Valid Certification of Robustness Margins for Safe Control via E-Values (https://www.alphaxiv.org/abs/2610.23746).

**What to build first, per paper (assistant's picks).** AlphaAgent: candidate screening plus a frozen, anytime-valid promotion gate. MASS: agent disagreement as a stress input. DPCC: the propose-constrain-execute-one-step order filter. QuantaAlpha: traceable mutation lineage inside a search ledger. MarketSenseAI: one typed, timestamped, expiring evidence interface (advisory only). EvolveTrade: a policy-update channel that cannot touch limits, permissions or exits. Label Unbalance: the classifier as a signal proposer behind separate admission, sizing and live gates. FinRL-X: the proposal-to-weights-to-orders interface with downstream overlays. QuantHarness: the governed promotion pipeline. Trading-R1: its signal tested net of costs under the search-aware gate, with sizing decided elsewhere.

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

Continued from later chats (04, 12, 13, 16, 19-21). Event windows per class are in the chat 09 section; top-down per-class verdicts are in sections A-G. All of it is the assistant's claim.

| Class | Drawdown sizing (04) | Ramping up (12) | Stops (13) | Costs to model (16) | Monitoring (19) | Simulation needs (21) |
|---|---|---|---|---|---|---|
| FX | Aggregate currency factors (USD, JPY, carry); weekend reopen gaps | Notional steps above venue minimums; evidence per session and pair | No consolidated price or universal trigger; rollover, handoff and releases widen spreads | Last look (window, accept, reject, requote odds), broker swap long and short, rollover time and day multiplier | Session handovers, fixing windows, whole-book currency exposure, broker price divergence | Dealer liquidity plus ECN books, sessions, last look; releases and rollover stressed separately |
| Indices | Stress jointly with equity beta; separate overnight-gap stress | Micro futures or small ETF size, integer-contract steps; regular vs overnight evidence | Cash vs futures hours; auctions; gaps | Futures: spread in ticks, fees per contract, tick value, depth, roll; CFDs: spread and financing | Cash vs futures vs after-hours, auctions, basis, venue circuit breakers | Continuous book plus auctions, rolls, price limits, margin |
| Metals | Precious vs industrial; USD, real-rate, risk factors | Each metal its own bucket; valid contract rounding; active vs thin sessions | Gold liquid across sessions; silver and small contracts differ | Futures roll and fees; CFD spread, swap, multiplier | Broker spot vs exchange futures, fixing windows, margin changes | Futures curve, rolls, delivery, storage and carry |
| Energy | More conservative jump stresses; concentration caps across maturities | Slowest ramp, smallest exposure | Inventory, OPEC, weather; expiry and delivery; limit moves | Contract value, roll execution, calendar spread; back-adjusted series hide roll losses | Expiry, roll, first notice, inventory events, unit and multiplier checks | Inventory and supply shocks, location and product basis |
| Crypto | Ordinary and tail stresses; venue limits; collateral buffers | 24/7 data is not independent evidence; block by session, weekday vs weekend, venue, funding | Trigger on last, mark or index price; funding, liquidation engine | Fee tier, maker and taker fee, rebate, funding rate and time, position at funding | No quiet hours; funding, liquidations, mark vs index, outages, stablecoin and chain events | Fragmented spot and perp venues, funding, liquidation engines, basis, latency |
| Futures | Notional, vol and stressed margin per contract, not contract counts | If one contract exceeds the loss budget, size is zero, not rounded up | Limit moves; roll | Per-contract fees, tick value, roll | Contract month, roll, settlement, variation margin, limit status | Exchange rules, rolls, margin, settlement |
| Single stocks | Issuer, sector and event caps | Evidence across distinct names; whole-share minimums can make a tier infeasible | Gaps, earnings, halts; a stop cannot fill through a halt | Spread, commissions, impact, borrow availability, rate and recalls; CFD financing | Halts, auctions, corporate actions, borrow and short-sale rules | Per-symbol books, auctions, halts, corporate actions, sector correlation |

---

## Workflows QMX could have

Proposed in the answers so far (assistant's claims, framed as QMX workflows).

1. **Search ledger to promotion gate.** Agents record every candidate, variant, data version and cost-model version in an immutable ledger. The promotion service applies post-selection shrinkage (Pav 2026) and DSR/PBO plus leakage-safe held-out checks, then a funded anytime-valid promotion test on fresh net returns ("Can We Stop the Backtest Yet? Anytime-Valid Promotion Tests for Adaptive Financial Research Agents", https://arxiv.org/abs/2611.03384). A human gives the final live promotion. (chat 01)
2. **Graded live demotion.** Warning detector (CUSUM or e-detector) cuts the strategy's risk budget and opens a review; confirmed economic failure (e-process >= 1/alpha_i) suspends it; a pre-authorised dollar loss rule can demote before either. Each demotion records its cause. Re-promotion is a new funded episode. (chat 10)
3. **External breaker governor.** A process outside all agents watches equity, open risk, margin, reconciliation, data freshness, rejects, slippage and order rate, and moves each strategy, bucket and the account through explicit states: alert, block new entries, cancel working orders, disabled, account stop. An order-boundary validator computes worst-case loss for every order. (chat 06)
4. **Bucket stress isolation.** Per bucket (asset class, session or region): data-validity check, then turbulence, correlation surprise and absorption ratio; a bucket alert blocks entries and steps down that bucket's risk; a separate whole-book control covers broad shocks; re-risk in capped steps after a persistence window. (chat 08)
5. **Read-only LLM risk narrator.** An LLM summarises incidents, explains shared exposure across strategies and drafts a review checklist; it never trips or clears a breaker. (chat 06; chat 19 adds a decision-trace record in the NEXTFUND style and a false-alarm triage ranker)
6. **Bound approval packet.** Agent submits a frozen, hashed candidate; deterministic pre-queue checks (reproducible, point-in-time, no window reuse, realistic costs, limits); a one-screen operator decision bound to the hash, instruments and limits; the runtime holds a narrow capability to run only that version; drift, stale approval or material change revokes it; an append-only, replayable record. (chat 20; chats 22c-22e reuse it for self-evolving agents)
7. **Governed research pipeline.** Task contract and data bindings (QuantHarness), every trial in a search ledger, leakage-safe and search-aware evaluation, then an anytime-valid promotion test on fresh net returns, then the bound approval packet. (chats 18, 20, 22e)
8. **Staged ramp ladder.** Shadow, then the smallest feasible live size, then larger steps only after fresh evidence at each step; de-risk fast, re-risk slowly and in capped steps; "zero" when one minimum contract exceeds the step's loss budget. (chat 12; chats 05, 11 tie each step to a promotion test or capacity estimate)
9. **Shared cost ledger.** One ledger for backtest and live fills with per-fill markouts; conditional passive-fill odds instead of a fixed fill assumption; Slippage-at-Risk from visible depth; costs re-estimated per session and fed back to the edge-to-cost admission gate. (chat 16)
10. **Meta-label exit and size gate.** A primary rule proposes a trade; a meta-labeller trained on triple-barrier outcomes gives a calibrated probability; probability and payoff map to size under a conservative risk budget; a separate portfolio guard can still cut. (chats 14, 22d)
11. **Event calendar control.** Per instrument, scheduled event windows block entries and cancel stale orders; unscheduled news acts as a breaker on a trusted signal; re-entry is gated on observed spread, depth and impact, not only a timer. (chat 09)
12. **Alert rationalisation.** Every page names an action and a deadline; strategy trips first, cluster and account act as time-graded backups; multi-window loss-budget burn alerts; incidents grouped; each trip logged with whether it was actionable. (chat 07)
13. **Interactive simulation bench.** Run the same risk rules under fixed-tape replay, an interactive exchange (ABIDES), adaptive liquidity (ABIDES-MARL) and cascade scenarios (CrashGym); report where the verdicts differ before trusting a rule. (chat 21)
14. **Conservative parameter tuning.** Offline tuning proposes a few stable configurations; live switching between them runs as a conservative bandit with a baseline-relative loss budget and discounting of stale results. (chat 17)
15. **Propose-constrain-execute one step.** Strategies propose order or position paths; a deterministic layer projects them onto exposure, turnover, liquidity and drawdown limits; only the next step executes; replan with fresh state. (chat 22b, from DPCC)

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

From the later chats (same caveat: proposed designs, not tested end to end):

- **Agnostic Risk Parity + HRP + Bayes-Stein:** cluster-aware risk budgets stop similar sleeves from stacking; shrunk return estimates. (A)
- **Kelly information rate + Bayes-Stein + Deflated Sharpe:** conservative edge estimate, discounted for the number of trials, before any growth sizing. (A)
- **PBO + DSR + the agent-generated strategy log:** record every idea and variant; evaluate with leakage-safe splits. (A, 11)
- **Meucci effective number of bets + HRP + Ledoit-Wolf covariance:** measure true breadth, allocate by clusters, stable covariance. (02)
- **Hamilton Markov switching + Engle DCC + Moreira-Muir:** filtered macro regime and dynamic correlation scale vol-managed exposure. (D)
- **Grossman-Zhou drawdown control + CAST uncertainty penalty + conformal VaR:** account drawdown and forecast uncertainty both cut exposure; calibrated tail limit on top. (D)
- **Kaminski-Lo "When do stop-loss rules stop losses?" + Almgren-Chriss:** separate the decision to cut risk from the execution of the cut. (D)
- **OFI/MLOFI + a session-aware cost model + a hard risk budget:** scalp only where the book signal clears session costs. (E)
- **Schur Complementary Allocation + NCO-Schur bridge + conformal portfolio VaR:** stable cluster allocation with a calibrated tail limit. (05)
- **Efficient multivariate Kelly + Schur allocation + Conformal Kelly:** growth sizing across strategies with uncertainty-calibrated caps. (05)
- **Post-selection Sharpe + Certified Alpha Capacity + the sequential promotion test:** honest edge after search, a capacity ceiling, then fresh evidence before scaling. (05, 11)
- **TPE-AS + Conservative Bandits (+ Rotting Bandits):** offline candidate configurations, live switching under a loss budget, stale rewards discounted. (17)
- **AQuA or TPE-AS + "What survives honest evaluation?":** an LLM proposes bounded parameter or hypothesis changes only, compiled and judged by a search-aware evaluator. (17, 18)
- **EvoQuantLab + "What survives honest evaluation?" + Promote (2611.03384):** evolutionary discovery, search-aware historical evidence, anytime-valid live promotion. (18)
- **AQuA + Propose, Don't Judge + AllPath:** research memory, a frozen referee the agent cannot tune, human approval. (18)
- **Propose, Don't Judge + e-detectors + Understanding Alpha Decay:** frozen admission plus live decay retirement. (11)
- **Synthetic execution benchmark + anytime-valid promotion + instrument-mechanics stress:** promotion evidence that already includes realistic fills and contract mechanics. (11)
- **Tail-GAN + SSGEN + execution-cost stress:** generated tail scenarios for strategy P&Ls, with costs stressed too. (15)
- **Packham-Woebbeking correlation stress + SSGEN + strategy-cluster budgets:** interpretable dependence shocks that test cluster caps. (15)
- **SSGEN + CAST + an external kill switch:** find forecast and position states that create severe loss; uncertainty-aware sizing; independent stop. (15)
- **AutoQuant + The Market Maker's Dilemma (+ Slippage-at-Risk):** one backtest/live ledger with conditional passive-fill odds and depth-based slippage. (16)
- **Optimal Trading Filters + AutoQuant:** a cost-aware target-position filter between forecast and order. (16)
- **Structural Limits of OHLCV momentum in MNQ + Market Maker's Dilemma + AutoQuant:** walk-forward, per-fold trade-count and net-return gates as a falsification template. (16)
- **Funding-Aware Optimal Market Making + AutoQuant:** funding state shifts target inventory and quote skew for perps. (16)
- **Meta-label probability-to-size + portfolio kill switches:** calibrated probability sets size; the portfolio guard can still cut. (14)
- **IEEE inverse-time grading + ISA-18.2 + SRE burn-rate alerts:** layered limits that trip nearest-first, with actionable alerts only. (07)
- **E-values + burn-rate alerts + hard limits:** statistical decay monitoring and budget burn kept separate from the hard-loss trip. (07)
- **ReguSim-style alert scoring + PU false-alarm triage + NEXTFUND decision traces:** measure each alert source, rank likely false alarms, keep a replayable decision record. (19)
- **QuantHarness + "What survives honest evaluation?" + Promote:** governed development, full search accounting, anytime-valid promotion. (20, 22e)
- **AllPath + Approve What, Exactly? + Loopjacking:** a human queue whose approvals are bound to the exact effect and re-checked at use. (20)
- **AllPath + SwingGuard + FARSIGHT:** promotion gate plus continuous risk governance plus an independent kill path. (20)
- **ABIDES + ABIDES-Gym + LOB-Impact Benchmark:** production agents through an exchange adapter; measure emergent impact. (21)
- **EvoMarket + CrashGym + ABIDES-MARL:** multi-asset institutional rules, cascade scenarios, adaptive liquidity. (21)
- **ABIDES + FARSIGHT + AllPath:** shared news and signals in an interactive market to expose crowding among QMX's own strategies before promotion. (21)
- **CrashGym + Can AI Make Money in Crypto? + perpetual-futures ABM:** crypto venue model with funding and liquidations for cascade tests. (21)
- **AlphaAgent + anytime-valid promotion ledger + live decay retirement:** regularised candidate generation, sequential promotion, retirement on decay. (22a)
- **DPCC + On Control of Drawdown (2609.23272) + e-value robustness-margin certification (2610.23746):** constrained next order under a drawdown ceiling, with margins revised cautiously online. (22b)
- **QuantaAlpha + post-selection Sharpe (2606.01650) + Promote:** each mutation is a versioned candidate; the ledger makes the search count. (22b)
- **MarketSenseAI 2.0 + OpenPM (2608.09988) + Fake News, Real Crashes (2610.26438):** typed, timestamped, provenance-checked evidence records, replayed point in time. (22c)
- **EvolveTrade + AllPath + Promote:** self-evolving analysis policy under human-gated, versioned promotion. (22c)
- **Label Unbalance + FinRL-X + meta-labelling and triple-barrier exits:** a rare-event classifier as proposer, trade-lifecycle labels, a downstream allocation interface. (22d)
- **Label Unbalance + FinRL-X + How Execution Assumptions Change Short-Horizon Sharpe Rankings (2610.05077):** an edge-to-cost gate on the classifier's "opportunity" class. (22d)
- **Trading-R1 + Position Sizing as a Risk-Control Variable (GRPO) + AllPath:** keep the signal model apart from the sizing decision; human-gated revisions. (22e)

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
| Simple OHLCV base alphas | AlphaAgent 2025, https://www.alphaxiv.org/abs/2502.16789 | Four base alphas (intraday return, daily return, 20-day relative volume, normalised daily range) regularised for originality and simplicity; target was next-day stock return. | Unit raw material (needs short-horizon cost tests) | Daily stock ranking in the paper; intraday return, range and relative volume are the closest short-horizon families. | Daily or intraday OHLCV, point-in-time universe, costs. |
| Agent consensus minus disagreement | MASS 2025, https://www.alphaxiv.org/abs/2505.10278 | Weighted agreement of simulated investor types minus their disagreement; high disagreement linked to overpricing under short-sale limits. | Reading (ensemble agreement; stress input) | Across QMX's own strategies: do independent models agree on an instrument? | Per-strategy signals per instrument, timestamped. |
| Fee-threshold three-class labels | Label Unbalance in High-frequency Trading 2025, https://www.alphaxiv.org/abs/2503.09988 | Up, down or flat relative to a fee threshold on one-minute futures moves; rebalanced losses for the rare classes. | Unit (scalper signal model; experiment) | Liquid futures at one-minute bars. | One-minute futures bars, fee schedule, natural-class calibration set. |
| Volatility-aware recommendation labels | Trading-R1 2025, https://www.alphaxiv.org/abs/2509.11420 | Five-way recommendations whose labels account for volatility over the holding horizon. | Reading or unit (swing) | Single stocks and ETFs, roughly weekly horizon; not a scalper. | Prices, fundamentals, dated news, sentiment, macro. |
| Crypto risk triggers | SwingGuard 2026, https://arxiv.org/abs/2610.12988 | Drawdown, ATR, momentum, exposure, on-chain and news anomalies, source diversity, six-hour accumulation start a deeper diagnosis; staged recovery. | Reading (risk monitor input) | BTC and ETH intraday overlays. | Five-minute prices, on-chain and news feeds, exposure state. |

---

## Ten most useful papers for QMX (this run's pick)

Picked by how directly each answers a QMX design question and how often the answers came back to it across chats. Every description is the assistant's claim; none is verified here.

| # | Paper | Link | What it gives QMX | Layer |
|---|---|---|---|---|
| 1 | Can We Stop the Backtest Yet? Anytime-Valid Promotion Tests for Adaptive Financial Research Agents (Promote) | https://arxiv.org/abs/2611.03384 | A promotion gate that stays valid while agents keep searching: each frozen candidate is funded from a lifetime testing budget and tested only on returns after registration. Strict: ~no power at a 5 bp edge, 70.1% at 15 bp. | X5 |
| 2 | What survives honest evaluation? Leakage-safe, search-aware assessment of LLM-driven strategy discovery | https://arxiv.org/abs/2608.27734 | Trial ledger, publication-delay audit, DSR and PBO for agent-found strategies: the historical half of the gate. | X5, X7 |
| 3 | Post-Selection Estimation of Sharpe Ratios (Pav) | https://arxiv.org/abs/2606.01650 | Shrink the winner's Sharpe for the size of the search before it sets size; needs the whole candidate pool. | X2, X5 |
| 4 | E-detectors (Shin, Ramdas, Rinaldo) and non-partitioned e-detectors (Saha, Ramdas) | https://arxiv.org/abs/2203.03532 ; https://arxiv.org/abs/2607.28322 | Live alpha-decay detection with controlled false alarms: warning cuts budget, confirmation suspends. | X3 |
| 5 | On Control of Drawdown: Robust Invariance and Optimality | https://arxiv.org/abs/2609.23272 | Exposure bounded by the remaining drawdown cushion over an assumed return support: the account and cluster brake. | X2, X3 |
| 6 | Building Diversified Portfolios that Outperform Out of Sample (HRP) with Meucci's effective number of bets | https://doi.org/10.3905/jpm.2016.42.4.059 ; https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1358533 | Cluster strategies by their P&L so many similar units do not pass as breadth; measure true breadth. | X2, X6 |
| 7 | CAST: uncertainty-penalised state-space controller for drawdown control | https://www.alphaxiv.org/abs/2609.14205 | More forecast uncertainty means less exposure; without the penalty drawdowns reached ~80%. A sizing template. | X2 |
| 8 | Taming Tail Risk: Conformal Calibration for Nonstationary Portfolio VaR | https://arxiv.org/abs/2602.03903 | A calibrated portfolio tail limit that is separate from any claim about edge. | X3, X4 |
| 9 | Approve What, Exactly? Effect Binding and Trusted Rendering for Agent Step-Up Authorization | https://arxiv.org/abs/2610.21063 | Bind the operator's approval to the exact effect that later runs; single-use, expiring grants. | X7 |
| 10 | Reliable Before Profitable: QuantHarness, with AllPath as its deployed counterpart | https://arxiv.org/abs/2610.26101 ; https://arxiv.org/abs/2610.26662 | Governed strategy development outside the agent's control, and a live case of a human-gated, self-revising trading agent (with its 8.8-hour median approval delay). | X5, X7 |

Close runners-up: Trading Agents or Market Crashers? (https://arxiv.org/abs/2609.19705; external halts contain cascades that loss-triggered selling amplifies), turbulence and correlation surprise (Kritzman, Li 2010; bucket risk-off readings), MLOFI (https://www.alphaxiv.org/abs/1907.06230; scalper signal and entry veto), Certified Alpha Capacity (https://arxiv.org/abs/2610.01115).

## Exports: what carries equations and diagrams

Saved in `exports\` with the same file names as the chat files: 32 chats run here (01, 02, 04-21, 22a-22e, 23-29) plus conv-01 to conv-03, 35 files in all. Source: the chat header menu "Chat actions > Copy Markdown" (alphaXiv offers no file download). Each export holds the whole chat: questions (with '@' paper-mention tags), the assistant's thinking titles, and answers. Counts below are from a scan of each file; inline-equation counts are approximate (a dollar sign in prose can be miscounted).

- **Equations (LaTeX kept).** Display equations: chat 01 (9 blocks), chat 10 (9), chat 02 (3), chat 24 B (3), chats 08, 13, 14, 25 C (2 each), chats 11, 17, 22a, 27 E (1 each). Inline math: heaviest in chats 10, 02, 01, 11, 13, 14, 15. No equations: chats 05, 09, 16, 18-21, 22b, 22c, 26 D, 28 F, 29 G and conv-01 to conv-03.
- **Charts.** The export, like the per-answer copy, keeps only each chart's title as an HTML comment, not its data. Chart placeholders appear in chats 05 (2), 13 (2), 14 (4), 17 (1), 19 (1), 20 (2), 22a (4), 22c (2), 22e (1). The chart values were read from the rendered page and are written into the matching chat files in this folder (not into the exports).
- **Diagrams.** Only conv-02 carries diagrams: 3 Mermaid blocks, kept as source text. No chat run here produced a Mermaid diagram.
- **conv-03** is short on the page as well (one question, one answer); its export matches the earlier text copy.
