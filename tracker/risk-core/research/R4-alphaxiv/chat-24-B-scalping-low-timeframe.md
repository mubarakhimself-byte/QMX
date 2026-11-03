# Chat 24 (top-down B) - Scalping and very low timeframe trading: risk and sizing when costs dominate

- Chat URL: https://www.alphaxiv.org/assistant/01a1a165-1392-7b87-b374-89cceb1427ce
- Source: alphaXiv assistant, harvested 2026-11-03. Answers are copied verbatim with the page's Copy-message button. Paper titles and claims below are the assistant's claims, not verified.

## Turn 1 (topic question, model: Smart) - question

Context: a retail multi-strategy trading system. Many small automated strategies (scalpers, intraday) trade around the clock across FX, indices, metals, energy, crypto, futures and stocks from one $500 account. Agents propose strategies but never touch money; a human promotes strategies to live. Topic (only this one): scalping and very low timeframe trading (tick data, 1 to 5 minute bars). How do risk and sizing work when transaction costs (spread, commission, slippage) are a large share of the edge? Cover: break-even edge versus cost, trade frequency and size under costs, stop and target distances relative to the spread, adverse selection and fill quality of retail market and limit orders, latency, whether retail-size orders move price, and how a scalping P&L shape (many small wins, rare large losses, negative skew) should change sizing and risk limits. Give the strongest work from any year, classics included, with titles, years, links and concrete recommendations.

## Turn 1 (topic question, model: Smart) - answer

**For a $500 multi-strategy account, the first sizing rule is “no trade unless conservative, all-in net expectancy is positive”; if the smallest executable position breaches its risk budget, skip it.** In scalping, a high win rate or a good-looking bar signal is not enough: entry and exit costs can consume the entire edge, while a rare bad fill can erase many small wins.

### Cost first, then size

For one unit or contract, define round-trip cost $C$ as spread paid, commissions and exchange fees, expected slippage, and any relevant funding or borrow cost. For a passive order, account for the *fill-conditioned* price movement too: a maker rebate does not make a fill profitable if the market tends to move against you immediately afterward. A strategy’s break-even condition is

$$
\mathbb{E}[R_{\mathrm{gross}}] > \mathbb{E}[C_{\mathrm{round\ trip}}].
$$

Measure both sides in the same units and using realistic fills. Use live or replayed bid/ask quotes—not just bar closes—and estimate costs by instrument, session, volatility, order type, and size. The number that matters is net expectancy *after* costs, with uncertainty around that estimate; a barely positive backtest mean is not a sound deployment hurdle. As a conservative screening rule, I would want the lower confidence bound on net expectancy to stay above zero across walk-forward periods and stressed costs, not just the full-sample average.

Costs make **more trades** expensive in direct proportion to turnover; they do not create more edge. Increasing size does not fix a weak per-unit edge and may worsen fills. Size each trade from the loss you can afford under a plausible adverse exit:

$$
q \le \frac{\text{risk budget in dollars}}
{\text{stop distance}\times\text{value per price unit}+\text{stressed exit slippage per unit}}.
$$

Use the larger of expected and stressed costs in that calculation. If the minimum lot or contract size makes the result too large, do not round up—skip the trade or use a smaller instrument. With a $500 account, even a fractional-percent risk budget is only a few dollars, so minimum trade sizes and stop-gap slippage can rule out otherwise attractive-looking markets.

### Stops, targets, and order choice

A stop is a loss-control instruction, not a guarantee of a fill at its trigger price. A stop-market can slip, especially in fast or thin conditions; a stop-limit can fail to execute. The target has to clear the *whole* round-trip cost, and the stop and target should be evaluated jointly with the win probability. If $T$ is the target distance, $S$ the stop distance, and $C$ the round-trip cost in price units, the simplified break-even win probability is

$$
p_{\mathrm{BE}}=\frac{S+C}{T+S}.
$$

That omits gaps, partial fills, and changing costs, so it is a floor rather than a complete model. There is no universal safe “target must be X spreads” ratio: calibrate it to actual costs and fill outcomes. But if the target is only about as large as the spread and fees, a modest amount of slippage can eliminate the edge. Widening the stop without changing the signal’s payoff distribution is not a solution; it changes both risk per trade and the break-even win rate.

Market orders favor immediacy and certainty of execution, but pay the spread and can slip through shallow book depth. Limit orders control the price but may not fill, may partially fill, and are most likely to fill when the price is moving against the order. Track the result **conditional on getting filled**, as well as the missed-trade cost when an order does not fill. A marketable limit caps the price you will accept; it does not guarantee a fill or remove adverse selection. For both order types, log decision price, arrival price, fill price, subsequent mid-price, fill rate, partial fills, and time-to-fill.

Latency matters when the signal decays quickly: the quote may move between decision and arrival, a limit order may become marketable, and a resting order may lose queue priority. Ma, Saggese, and Smith’s [*The Effect of Latency on Optimal Order Execution Policy* (2025)](https://www.alphaxiv.org/abs/2504.00846) models the trade-off between limit-price improvement, fill probability, latency, and risk; it also notes that queue position and partial fills are outside its model. Its practical implication is to measure the execution policy at the latency and venue you will actually use, not assume a historical signal price was available to you. [Latency and fills](https://www.alphaxiv.org/abs/2504.00846?page=2)

At typical retail size, a single order usually will not move prices in a deep major FX pair or index future. That is not the same as having negligible execution costs: crossing the spread, fees, adverse selection, and thin top-of-book depth can still dominate a small edge. The answer changes in thin sessions, less-liquid futures, small-cap stocks, and crypto markets. There, even a small order can consume visible depth; repeated orders can also reveal a strategy’s intent. Test size against order-book depth and actual market impact rather than assuming retail size is always too small to matter.

### Negative skew changes the risk limit

“Many small wins, rare large losses” is negative skew: the average win rate can look reassuring while the losses that matter are hidden in a thin tail. Do not size from win rate, average win, or a normal-return/variance assumption alone. Include rare loss scenarios, gaps, stop slippage, correlated positions, and simultaneous strategies in stress tests; track expected shortfall or another tail-loss measure alongside drawdown and net expectancy. Keep risk limits at the **shared account** level: several agents trading correlated markets are not diversified just because they have different strategy names.

As initial, deliberately conservative operating limits for a small account, I would cap planned loss on a trade at roughly **0.1–0.25% of equity** and daily loss at roughly **0.5–1%**, including the combined exposure of open trades. These are guardrails to test and adjust—not research-derived universal optima. Reduce size further for negative-skew strategies, impose a hard strategy-level drawdown stop, and halt a strategy when realized execution costs or tail losses exceed its approved envelope. Do not let an agent raise size to “win back” losses; retain the human promotion gate and require a live, minimum-size execution trial before increasing risk.

### A focused reading list

| Paper | Why it matters |
|---|---|
| [*Optimal Execution of Portfolio Transactions* (2000)](https://doi.org/10.21314/JOR.2001.041), Robert Almgren and Neil Chriss | Classic framework for trading off execution cost against price risk. Useful for the basic principle that execution speed and execution risk must be optimized together, rather than treating cost as a fixed afterthought. |
| [*A Simple Implicit Measure of the Effective Bid-Ask Spread in an Efficient Market* (1984)](https://doi.org/10.1111/j.1540-6261.1984.tb03897.x), Richard Roll | Classic way to think about inferring spread-related costs from price data; a useful complement to direct quote and fill measurements. |
| [*The Shadow Price of Latency: Improving Intraday Fill Ratios in Foreign Exchange Markets* (2021)](https://doi.org/10.1137/19M1258888), Álvaro Cartea and Leandro Sánchez-Betancourt | FX-focused work on how latency affects fill outcomes and execution decisions. |
| [*Latency and Liquidity Risk* (2021)](https://doi.org/10.1142/S0219024921500357), Álvaro Cartea, Sebastian Jaimungal, and Leandro Sánchez-Betancourt | Connects latency with liquidity risk; relevant when a fast-moving signal depends on being filled at a particular price. |
| [*The Effect of Latency on Optimal Order Execution Policy* (2025)](https://www.alphaxiv.org/abs/2504.00846), Chutian Ma, Giacinto Paolo Saggese, and Paul Smith | A relatively recent model of limit-order fills, latency, spread, and risk-sensitive execution. Treat it as a model-based execution analysis, not a universal empirical fill guarantee. |
| [*Structural Limits of OHLCV-Based Intraday Momentum Signals in MNQ Futures: A Systematic Falsification Study* (2026)](https://www.alphaxiv.org/abs/2605.04004), Mathias Mesfin | A directly relevant five-minute-bar case study. Across 14 signal families, 11 had gross returns below the study’s assumed 2-point MNQ round-trip friction floor; none passed all of its stated validation criteria. [Cost hurdle](https://www.alphaxiv.org/abs/2605.04004?page=1) Treat it as a useful, instrument-specific falsification exercise, not a market-wide estimate: its friction assumption and signal sample do not establish a universal cost threshold. |

The practical takeaway is to optimize **net edge per unit of tail risk**, not trade count or win rate. Reject strategies whose conservative net edge does not comfortably clear measured costs; then size the surviving ones by stressed loss, including adverse fills and correlated exposure.


## Turn 2 (follow-up a: top three methods and minimum edge-to-cost ratio, model: Smart) - question

Follow-up 1: Pick the three papers or methods that matter most for scalping risk and sizing here, from any year. For each one: what exactly it does, step by step; its inputs and outputs (which cost, fill or order-book data I must measure, and what size, threshold or limit it returns); where it fails (retail CFD or crypto broker fills instead of exchange data, spreads that widen at news and session rollovers, very few independent trades, last-look and requotes); and which later papers build on it or challenge it, with links. Then: what minimum ratio of expected edge per trade to round-trip cost should a scalper show before it is allowed to trade, and how should that be measured live?

## Turn 2 (follow-up a: top three methods and minimum edge-to-cost ratio, model: Smart) - answer

The three methods I’d put at the center are **Almgren–Chriss for execution-versus-risk trade-offs, Cartea et al. for latency-driven fills, and Eisler–Muhle-Karbe for measuring execution costs from realized trading data**. None directly returns a safe dollar risk limit for a $500 scalping account; combine their outputs with an account-level loss budget and an empirically measured, venue-specific fill model.

## 1. Almgren–Chriss: choose the execution schedule, not the strategy’s risk budget

Robert Almgren and Neil Chriss’s [*Optimal Execution of Portfolio Transactions* (2000)](https://doi.org/10.21314/JOR.2001.041) is the classic framework for deciding how quickly to execute an order when trading has a cost and holding inventory has risk.

The method, in broad steps:

1. Specify the quantity to trade, the time allowed, the price volatility, and the assumed temporary and permanent market-impact costs.
2. For a candidate schedule, estimate its expected execution cost and the risk from being exposed to price movements while waiting to complete the trade.
3. Choose a risk-aversion parameter to express the cost–risk trade-off.
4. Solve for the schedule that balances those terms. The output is a time path for how much to trade—not a scalping signal, a stop distance, or a dollar risk limit.

**Measure:** order quantity, execution horizon, price volatility, fill prices and reference prices, and—if the order is large enough to matter—how impact varies with trading rate and relaxes after trades. **Output:** a preferred execution schedule under the chosen cost and risk assumptions.

**Where it fails for this use:** the classic model is about completing an order and commonly represents execution cost and risk in a simplified way. For a tiny retail order in a deep market, estimated market impact may be negligible compared with spread, fees, and slippage; the schedule then contributes little. Conversely, a model calibrated to exchange data does not automatically describe a CFD dealer’s quote, crypto venue, or broker’s requote behavior. A constant-spread or constant-impact estimate is especially unsafe around news and session transitions. Later work such as [*Optimal Trading Strategy and Supply/Demand Dynamics* (2013)](https://doi.org/10.1016/j.finmar.2012.11.001) adds liquidity recovery and order-book dynamics; [*Optimal Execution under Liquidity Uncertainty* (2025)](https://www.alphaxiv.org/abs/2506.11813) addresses uncertainty in available liquidity. These extensions reinforce the central point: a schedule optimized under the wrong liquidity assumptions is not an execution advantage.

**Use here:** apply the principle narrowly. If the position is so small that it does not consume depth, don’t spend effort optimizing a multi-part execution schedule; focus on whether the trade’s expected move clears its actual all-in costs. If it does consume meaningful depth, compare a marketable order with a patient or sliced policy using the costs and fill probabilities observed at that venue.

## 2. Cartea et al.: set the price limit for latency-exposed marketable orders

Álvaro Cartea, Sebastian Jaimungal, and Leandro Sánchez-Betancourt’s [*Latency and Liquidity Risk* (2021)](https://doi.org/10.1142/S0219024921500357) models a different execution problem: a trader sees a book, sends a marketable limit order, and the book may change before the order arrives.

The method proceeds roughly as follows:

1. Model order attempts and intervening book changes as a marked point process; the “mark” represents the price or quantity deterioration or improvement before the order reaches the venue.
2. Choose an order-price “discretion”—how far the order is allowed to walk the book.
3. Estimate the trade-off between the extra cost of walking the book when prices worsen and the penalty for a missed order.
4. Choose the discretion that minimizes expected cost plus the missed-trade penalty. Its output is a price tolerance for the order, potentially changing with the current state and number of previous misses.

**Measure:** decision and arrival timestamps, order-book state at decision and fill/arrival, price and depth changes while the order is in flight, fills and rejections, execution prices, and the cost of a missed trade. The method also requires a choice of how costly a miss is relative to paying for worse execution.

**Where it fails for this use:** it is a framework for exchange-style marketable limit orders, not a general passive-limit fill model or a complete strategy-sizing rule. A retail CFD broker may not expose a central limit order book at all. On crypto, the book is venue-specific and fragmented. Dealer last-look, requotes, partial fills, and order rejection need to be represented in the measured outcomes—not assumed away. A model fitted to ordinary conditions can misprice fills when spreads jump at news or rollover. Ma, Saggese, and Smith’s [*The Effect of Latency on Optimal Order Execution Policy* (2025)](https://www.alphaxiv.org/abs/2504.00846) develops another risk-sensitive execution policy for limit orders under latency; it explicitly excludes queue position and partial fills. [Book moves](https://www.alphaxiv.org/abs/1908.03281?page=2) [Model limits](https://www.alphaxiv.org/abs/2504.00846?page=2)

**Use here:** treat discretion as a *venue-specific execution parameter*. Estimate its effect from your broker’s actual rejects, fills, and slippage. If that data is unavailable, the method cannot reliably tell you how aggressively to quote; default to a conservative order limit or don’t trade when the edge depends on a precise fill.

## 3. Eisler–Muhle-Karbe: estimate what execution actually costs

Zoltán Eisler and Johannes Muhle-Karbe’s [*Optimizing Broker Performance Evaluation through Intraday Modeling of Execution Cost* (2024)](https://www.alphaxiv.org/abs/2405.18936) is about estimating execution costs from trading data, rather than selecting a scalping signal. That makes it useful for building the measurement layer a live scalper needs.

Its procedure is:

1. Record each order’s trading schedule, fills, execution prices, and the evolving midprice.
2. Separate a roughly linear component—spread crossing and other per-unit execution quality—from a size-related impact component.
3. Estimate how much each component contributes using the trade and price trajectory data.
4. Compare actual execution with a reference schedule or reference price to reduce noise in the estimates.
5. Use those estimates to compare execution quality or brokers. The output is a cost estimate and cost decomposition—not a strategy entry threshold or recommended position size.

**Measure:** fill prices and quantities, time-varying midprices, order size and timing, and the reference schedule or benchmark used for comparison. In their institutional setting, the authors find that estimating costs precisely can require far more observations than a short backtest suggests: in their model example, even 1,000 orders leave the naïve linear-cost estimate statistically weak. [Sample size](https://www.alphaxiv.org/abs/2405.18936?page=8)

**Where it fails for this use:** the setting is broker execution of larger orders, with an exchange-style midprice and an explicit impact model. It does not establish that a retail CFD spread or a crypto broker’s all-in cost follows the same decomposition. A dealer’s last-look or requote process needs its own observed cost data. Nor does pooling many trades solve the problem if they are concentrated in one session, one market regime, or highly correlated strategies: the effective amount of independent evidence can be much smaller than the raw trade count.

**Use here:** keep a cost ledger for each instrument, venue, order type, and session. Include commissions and exchange fees; entry and exit slippage relative to the relevant midprice; spread paid; funding or borrow where applicable; and the effects of rejections, requotes, and partial fills. Re-estimate costs separately for ordinary and stressed conditions rather than letting quiet-session averages wash out news or rollover costs.

## Minimum edge-to-cost hurdle

**My proposed promotion gate is a conservative expected gross edge of at least 2× stressed expected round-trip cost per unit.** That is an operational rule, not a universal threshold established by these papers. For a negatively skewed strategy or one with limited independent live evidence, I would use **3×** as the initial hurdle, or decline to promote it until its tail losses and fills are better measured.

Measure it this way:

- Estimate **gross edge** as the predicted or realized price move from the decision-time midprice to the planned exit-time midprice, in the strategy’s direction. Don’t calculate it only on filled orders: limit orders that fill selectively can make a fill-only edge estimate misleading.
- Estimate **round-trip cost** from actual entry and exit fills against their contemporaneous midprices, then add commissions, exchange fees, funding/borrow, and relevant rejection or requote costs. Avoid double-counting the spread: an execution-price-versus-mid measure already includes the spread crossed.
- Compare the **lower confidence bound** on expected gross edge with **twice the stressed expected round-trip cost** for that strategy’s instrument, venue, order type, and session. Stress the cost estimate for spread widening and slippage; estimate those separately for news and rollovers or prohibit trading during those windows.
- Recompute live in rolling, session-aware windows using day- or session-clustered uncertainty estimates, not by treating every trade as independent. If the evidence is too sparse for a credible lower bound, keep the strategy in observation or paper trading—not live.

The resulting ratio should not be confused with an order’s target-to-spread ratio or its win rate. It is a **net-economics admission test**: even before position sizing, the conservative edge estimate has to clear a realistic round-trip cost estimate by a margin. Position size should then be set from the account’s allowed loss under a stressed exit, with correlated strategies counted together.


## Turn 3 (follow-up b: asset classes and combinations, model: Smart) - question

Follow-up 2, two parts. (1) Asset classes: how do scalping costs, risk and sizing differ across FX, stock indices, metals, energy, crypto, futures and single stocks (spread and commission structure, trading sessions and rollover, leverage and margin, tick size and contract mechanics, volatility, news sensitivity, quality of retail broker data and fills)? Give the differences per class and which classes are realistic for scalping from a $500 account. (2) Combinations: what would the best papers here combine with from other parts of this system: sizing under an uncertain edge (Bayesian or fractional Kelly), live alpha-decay detection (e-values, change points), kill switches, risk-off regime detection, stop and exit design, meta-labelling and triple-barrier exits, backtest-overfitting checks, cost models by time of day, news and event windows, microstructure signals, LLM agents for research and risk? Name concrete pairs or triples of papers with links, what the combined method would do, and why.

## Turn 3 (follow-up b: asset classes and combinations, model: Smart) - answer

## 1. Asset classes: what the costs mean for a $500 account

“Scalp FX,” “scalp an index,” and “scalp futures” can describe very different products. A centralized exchange-traded future has a visible order book and explicit contract rules; a retail CFD is generally a broker’s contract and quote, even if it tracks the same underlying market. Cost and fill data from one venue should not be treated as evidence about the other.

| Market | Main cost and execution issues | Contract, session, and risk issues | $500 scalping realism |
|---|---|---|---|
| **FX** | OTC and fragmented: there is no single consolidated FX book. Brokers offer either a spread markup or tighter “raw” spreads plus commission; the effective spread, last-look/rejection behavior, requotes, and slippage depend on the venue and account. Spreads can widen around news, rollover, and the thin Sunday open. | Trades nearly 24 hours on weekdays. Swap/financing applies to positions held over rollover; the charge and triple-roll day depend on the broker and currency pair. Pip value depends on pair, account currency, and lot size. Leverage can make minimum sizes dangerously large relative to equity. | **Potentially feasible only with genuine micro sizing, low leverage, a regulated venue, and logged execution quality.** Confirm minimum trade size and pip value: “micro lot” still may risk too much at a normal stop. |
| **Stock indices** | Separate **index futures** from **index CFDs**. Futures have exchange spreads, commissions, and fees; CFDs have broker spreads, financing, and broker-specific fills. The cash open and major releases often bring sharp spread and volatility changes. | Index futures trade most of the day, with a maintenance break and contract expiry/roll; liquidity is usually better during the main local session. A micro contract’s tick value is smaller than the full-size contract but is not necessarily small relative to a $500 account. CFDs have broker-defined contract and margin rules. | **Usually poor for a $500 live scalping account unless a genuinely small product is available and a stress-sized stop still fits the loss budget.** Micro futures can meet margin while still being too large for prudent risk. |
| **Metals** | Gold and silver costs depend heavily on the product: exchange futures have explicit ticks and fees; metal CFDs have broker spreads, financing, and sometimes different quote conventions. News, thin overnight periods, and daily rollover can change costs materially. | Full-size gold futures have large dollar exposure per tick; micro contracts reduce it, but do not remove gap or volatility risk. CFDs may quote per ounce or per broker-defined lot. Verify tick/lot value, margin, and overnight charges from the actual contract specification. | **Micro gold or a truly small CFD may be testable; full-size futures are not appropriate.** Even a micro contract can be too large if the stop is several ticks or slippage widens. |
| **Energy** | Oil and gas can have abrupt spread and slippage changes around inventory reports and other market-moving events. Futures have explicit fees; CFDs add broker-specific spread and financing. A quiet-period average cost is a poor proxy for event fills. | Contract specifications differ widely; crude oil, natural gas, and products have different volatility, tick value, expiry, and delivery/roll risks. Futures contracts expire and may become illiquid during roll; avoid holding a deliverable contract into expiry without understanding the rules. | **Generally not a good $500 scalping venue.** A micro crude contract is smaller than standard crude, but can still create outsized risk; natural gas is especially challenging for small risk budgets. |
| **Crypto** | Costs vary by spot/perpetual venue and fee tier: maker/taker fees, spread, slippage, depth, and possibly funding. Funding is not a one-size-fits-all “rollover”; its interval and rate are venue-specific. Crypto trades 24/7, but liquidity and spreads vary by coin, venue, and time. | Contract multipliers, minimum order sizes, tick sizes, leverage, and liquidation rules differ across exchanges. Books are fragmented, outages and liquidations matter, and a venue’s data says nothing definitive about another venue. | **Spot crypto with no or very low leverage is among the more practical ways to test small sizing.** Perpetuals can be technically accessible with $500 but liquidation and leverage make them much less forgiving. Restrict the test to deep, liquid products and one venue. |
| **Exchange-traded futures** | Costs are the bid–ask spread, commission, exchange and regulatory fees, and slippage. Exchange data gives a more observable book than a typical CFD quote, but top-of-book data still does not guarantee your queue position or fill. | Contracts have fixed tick values, multipliers, sessions, expiry, margin, and roll dates. “Intraday margin” is a broker permission, not a measure of safe risk. A stop can execute worse than its trigger, and a position must fit the account’s loss budget as well as margin. | **Not automatically suitable because a broker advertises low intraday margin.** Micro contracts help; the decisive test is whether a realistic stop plus stressed slippage fits the account’s loss limit without rounding size up. |
| **Single stocks** | Costs can include commissions or per-share fees, spread, routing/price improvement, and slippage; “zero commission” does not mean zero execution cost. Spreads and depth vary greatly by ticker and time. | U.S. regular hours are the deepest for most names; pre/post-market trading is often thinner. Earnings, halts, and overnight gaps complicate stops. Tick size is typically a cent for many U.S. stocks, but share size, short-sale access, borrow fees, and fractional-share rules are broker- and market-dependent. Day-trading and margin restrictions depend on jurisdiction and account type. | **Liquid, low-price stocks may be feasible only if the broker supports the needed order size and short/exit mechanics.** Fractional shares can help with long-only sizing but are not universally available for intraday or short trades. |

**My shortlist for controlled testing from $500:** small-size **spot crypto without leverage**, and **FX only if true micro sizing and transparent, competitive fills are available**. Liquid single stocks can also be testable, subject to order, shorting, and account rules. Micro futures, metals, and especially energy are “possible to place” more often than they are “small enough to risk sensibly.” A contract that meets margin is not necessarily a contract that fits the risk budget.

For all classes, keep a venue-specific cost record: decision-time quote or mid, submission and arrival time, fill price and quantity, fees, exit fill, rejections/requotes, and the midprice after the fill. Break the estimates out by session, news/rollover windows, order type, and volatility. Don’t let favorable liquid-session averages conceal bad fills in the hours when the strategy actually trades.

## 2. Combinations that fit this system

These are proposed system designs, not claims that any cited paper validates the combination as a whole. The strongest pattern is to keep strategy generation separate from **cost estimation, sizing, execution, and kill authority**. The paper links below point to the works or methods; where a concept is a standard method rather than an identifiable paper, I name the classic source.

**A. Cost hurdle + realistic fills + an edge filter.** Combine [Bysik and Ślepaczuk, *Machine Learning-Based Bitcoin Trading Under Transaction Costs* (2026)](https://www.alphaxiv.org/abs/2606.00060), [Eisler and Muhle-Karbe, *Optimizing Broker Performance Evaluation through Intraday Modeling of Execution Cost* (2024)](https://www.alphaxiv.org/abs/2405.18936), and [Ma, Saggese, and Smith, *The Effect of Latency on Optimal Order Execution Policy* (2025)](https://www.alphaxiv.org/abs/2504.00846). The crypto study makes position changes conditional on a forecast clearing a cost-based hurdle; the broker-cost work gives a disciplined way to estimate execution costs; the latency paper frames the limit-order trade-off between price, fill chance, and delay. Together, they would produce a **trade/no-trade threshold based on current estimated round-trip cost**, plus an order policy that respects observed fill and latency behavior. The crypto paper is hourly BTC and uses proportional costs, not tick-level fills, so treat its backtest as a design example—not proof the threshold is calibrated for scalping.

**B. Uncertain-edge sizing + stop/exit outcomes + a small Kelly fraction.** Combine the [triple-barrier and meta-labelling methods in *Advances in Financial Machine Learning* (2018)](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086) with MacLean, Thorp, and Ziemba’s [*The Kelly Capital Growth Investment Criterion: Theory and Practice* (2011)](https://www.worldscientific.com/worldscibooks/10.1142/7466). Triple barriers make the label and exit outcome depend on price barriers and a time limit; meta-labelling can decide whether to take a primary signal. A downstream sizing module could estimate the return distribution for the accepted trades, shrink it for estimation uncertainty, then use a **small fraction of the resulting Kelly exposure**, subject to hard per-trade, portfolio, and drawdown caps. This addresses both noisy estimated edge and the skewed payoff profile; it does not make Kelly’s assumptions true. With few independent trades, the posterior should stay conservative and the live size should often remain the minimum size or zero.

**C. Live alpha-decay monitor + risk-off gate + kill switch.** Combine Page’s sequential change-detection method, [*Continuous Inspection Schemes* (1954)](https://doi.org/10.1093/biomet/41.1-2.100), with the cost and net-P&L ledger above and a deterministic circuit breaker. Run a sequential monitor on **net execution residuals**—for example, realized cost versus expected cost and strategy net returns versus its approved baseline—and independently monitor spread, latency, rejects, exposure, and drawdown. A detected adverse shift can first reduce size or disable that strategy; hard limits on account loss, exposure, and broker/data anomalies should stop order flow immediately without waiting for statistical confirmation. The change detector is not itself a safe kill switch: scalping may lose money faster than a detector can accumulate evidence, so hard limits must be separate, immediate rules.

**D. Time-of-day costs + news-aware risk-off + order-flow context.** Combine Heston, Korajczyk, and Sadka’s [*Intraday Patterns in the Cross-Section of Stock Returns* (2010)](https://doi.org/10.1111/j.1540-6261.2010.01573.x), Cartea et al.’s [*Latency and Liquidity Risk* (2021)](https://doi.org/10.1142/S0219024921500357), and Xu, Gould, and Howison’s [*Multi-Level Order-Flow Imbalance in a Limit Order Book* (2019)](https://www.alphaxiv.org/abs/1907.06230). The combination would estimate session-specific cost/behavior, account for the price/depth changes that occur before an order arrives, and use order-flow information as a short-horizon market-state feature. Add a scheduled-news calendar as a **known risk window**, and an observed spread/volatility trigger for unexpected events; during either, raise the cost hurdle, cut size, or stand down. Do not infer that a signal observed in Nasdaq stocks transfers unchanged to FX, CFDs, metals, or crypto books.

**E. Research and LLM agents + independent risk authority + overfit controls.** Combine [Bailey et al., *The Probability of Backtest Overfitting* (2017)](https://doi.org/10.21314/JCF.2016.322), [Bailey and López de Prado, *The Deflated Sharpe Ratio* (2014)](https://doi.org/10.3905/jpm.2014.40.5.094), and Ye et al., [*The Alpha Illusion: Reported Alpha from LLM Trading Agents Should Not Be Treated as Deployment Evidence* (2026)](https://www.alphaxiv.org/abs/2605.16895). Let agents propose hypotheses, code tests, and summarize the results, but log every trial and use walk-forward tests plus overfit-adjusted evidence before human promotion. Keep final sizing and order permission in deterministic components: independently calibrated forecast probabilities, explicit cost and exposure checks, account-level loss limits, and a kill switch. Ye et al. specifically argue that LLM confidence is not a return probability and advocate LLMs as auditable upstream information interfaces rather than final trading authority. That separation is a good fit for your rule that agents never touch money.

**Recommended wiring:** cost and liquidity estimates feed the trade gate; validated edge and exit outcomes feed conservative sizing; a session/news/regime monitor can only tighten exposure; and a separate deterministic risk service can veto or stop orders. Human promotion should require venue-specific live or replay evidence—not just a favorable backtest. For a $500 account, a strategy that needs a larger minimum position than its stressed loss budget allows should be rejected, not rounded up.


