<!-- alphaXiv chat export via the page's Chat actions > Copy Markdown, saved 2026-11-03. Chat URL: https://www.alphaxiv.org/assistant/01a1a1c1-955b-731f-9a42-7b2a4fbe8d4b -->

# Chat Transcript: FinRL\-X and Label Unbalance

## User

<alphaxiv-paper-mention data-id="2503.09988" data-section="public" data-label="Label Unbalance in High-frequency Trading">@Label Unbalance in High-frequency Trading</alphaxiv-paper-mention>  <alphaxiv-paper-mention data-id="2603.21330" data-section="public" data-label="FinRL-X: An AI-Native Modular Infrastructure for Quantitative Trading">@FinRL-X: An AI-Native Modular Infrastructure for Quantitative Trading</alphaxiv-paper-mention>  Context: a multi-strategy trading system. Many small automated strategies (scalpers, intraday) trade around the clock across FX, indices, metals, energy, crypto, futures and stocks. Agents propose strategies but never touch money; a human promotes strategies to live. Topic (only these two attached papers): for each paper, what does it offer a risk-and-sizing layer (position sizing, exits, drawdown control, validation, monitoring) and what trading ideas or signals in it could become strategies? Give the method step by step, its inputs and outputs, the reported performance and drawdowns with how they were evaluated (time split, costs, leakage controls), its weaknesses for a multi-asset short-horizon system, and which newer papers build on it or challenge it, with links.

## Aurelle

**FinRL-X is the only one of these papers that offers a portfolio-level risk and execution framework; “Label Unbalance in High-frequency Trading” is a model-training recipe, not a position-sizing or risk-management system.** The first could supply a candidate signal to a larger system; the second offers a modular way to turn candidate signals into portfolio weights and orders.

## 1. Label Unbalance in High-frequency Trading

### Method, step by step

1. **Build short-horizon examples.** Each example uses a 60-second window of 13 order-book and trade features sampled every 0.5 seconds. The target is a three-class label for the forward one-minute mid-price return: above the fee threshold, below the negative fee threshold, or within the fee band. The neutral class is about 80% of the data, versus about 10% each for up and down. [Labels and Inputs](https://www.alphaxiv.org/abs/2503.09988?page=3)

2. **Split data chronologically and train a classifier.** The authors describe an 8:1:1 train/validation/test split, early stopping, and MLP, LSTM, and Mamba backbones. They compare random undersampling of the neutral class, fixed class weights, a distribution-based cost-sensitive loss, focal loss, and per-class adaptive weights. [Training Setup](https://www.alphaxiv.org/abs/2503.09988?page=3)

3. **Emit class predictions, not executable trades.** The model’s output is a three-class prediction. A strategy could convert that prediction—or preferably calibrated class probabilities—into a long, short, or no-trade proposal, but the paper does not specify that conversion, position size, exit, or execution rule.

The most plausible strategy signals are the up/down predictions and the paper’s candidate features: recent mid-price mean, volatility, skew and kurtosis; volume activity; quoted spread; a return–volume beta; and an illiquidity measure. These are proposed or examined as predictive factors, not demonstrated as standalone, tradable strategies. [Candidate Factors](https://www.alphaxiv.org/abs/2503.09988?page=10)

### Risk layer, results, and evaluation

**It supplies no sizing, exits, stop-losses, portfolio drawdown controls, live monitoring, or order handling.** Its risk-related contribution is limited to making the classifier pay more attention to rare profitable/unprofitable labels. Fixed class weights are one option; the cost-sensitive loss uses class frequencies; focal loss increases weight on examples the model predicts with low confidence. [Imbalance Methods](https://www.alphaxiv.org/abs/2503.09988?page=7)

The experiment covers **20 trading days** of six Chinese futures contracts, sampled at 0.5 seconds. The paper reports qualitative comparisons in figures: cost-sensitive loss and fixed loss weighting often do better, while undersampling and focal loss can sometimes underperform the unadjusted benchmark. It does **not** report a strategy backtest with portfolio returns, Sharpe ratio, or maximum drawdown, so there is no trading-performance or drawdown figure to carry into deployment. [Results and Data](https://www.alphaxiv.org/abs/2503.09988?page=8)

The split is chronological, and the target incorporates a fee threshold, but that is not the same as a realistic net-of-cost trading simulation. The paper does not establish that fees, slippage, market impact, latency, or fills were modeled in a portfolio backtest. Nor does it describe a purge or embargo for overlapping one-minute forward labels around split boundaries. Its own discussion flags a normalization mistake: the authors initially normalized using the full dataset, observed an apparent performance improvement, and then identified that as a source of leakage; they say the corrected approach uses a rolling one-minute window. [Leakage and Domain Shift](https://www.alphaxiv.org/abs/2503.09988?page=8)

**For your system:** treat this paper as a candidate *signal-model* experiment for short-horizon futures—not as a sizing or risk layer. Its evidence is especially thin for a system spanning FX, equities, crypto, and other venues: six contracts, 20 days, one-minute labels, and no reported net portfolio performance or drawdown. Class imbalance handling also does not, by itself, establish that predicted minority-class trades have positive expected value after execution costs.

## 2. FinRL-X: An AI-Native Modular Infrastructure for Quantitative Trading

### Method, step by step

1. **Ingest and align data.** The framework describes structured market, fundamental, and macro data, alongside news transformed into sentiment signals. Inputs are aligned to a trading calendar, with raw and processed data stored for reproducibility. [Data Layer](https://www.alphaxiv.org/abs/2603.21330?page=4)

2. **Select assets.** A selection component chooses a candidate universe from information available up to the decision time.

3. **Allocate capital.** An allocator turns the selected assets into base portfolio weights. The paper names equal-weight, mean–variance, minimum-variance, and DRL-based alternatives.

4. **Adjust timing, then apply a risk overlay.** Trend or learned signals modify the base weights. A portfolio-level overlay can then scale aggregate exposure, for example using volatility information, while keeping relative allocations intact. The final output is a target weight vector—not a buy/sell prediction or a broker-specific order. [Strategy Pipeline](https://www.alphaxiv.org/abs/2603.21330?page=5)

5. **Backtest or execute through the same interface.** The executor converts target weights into orders and records realized allocations. The system also describes persistence for crash recovery, logs for reconciliation, and mechanisms to handle broker API interruptions. [Execution Safeguards](https://www.alphaxiv.org/abs/2603.21330?page=5)

### Risk layer, trading ideas, and results

FinRL-X provides **a place to attach portfolio sizing and exposure control**, but the paper does not supply a complete short-horizon risk policy. It describes feasible weights subject to normalization and leverage constraints, timing adjustments, and portfolio-level volatility scaling. It does not specify a general instrument-level sizing formula, explicit stop-loss or take-profit logic, maximum drawdown kill switch, or a standard exit policy. After a leveraged-instrument drawdown in paper trading, it motivates volatility-aware scaling and instrument-specific exposure caps; that is a safeguard recommendation, not a demonstrated drawdown-control rule. [Leveraged-Asset Stress](https://www.alphaxiv.org/abs/2603.21330?page=11)

Strategy ideas described in the paper include:

- **Trend timing:** trend-following or KAMA-based exposure adjustments.
- **Rolling equity selection:** update the candidate set with quarterly reports, select the top 25% of Nasdaq-100 constituents, then allocate with a DRL policy.
- **Multi-asset rotation:** rebalance weekly; select at most two groups from Growth, Real Assets, and Defensive using Information Ratio relative to QQQ; allocate within groups using residual momentum; use regime indicators as risk gates rather than alpha signals. [Rotation Strategy](https://www.alphaxiv.org/abs/2603.21330?page=9)

**Backtest:** The paper describes liquid U.S. equities and ETFs, SPY and QQQ benchmarks, a January 7, 2018–October 24, 2025 horizon, and proportional transaction costs of 10 basis points per side. It says learning models use rolling out-of-sample validation and decisions use information available up to time $t$, but gives little detail on fold construction, model-selection safeguards, or point-in-time universe handling. [Evaluation Setup](https://www.alphaxiv.org/abs/2603.21330?page=6)

Across the reported allocation comparisons, **DRL plus timing** has a 3.03 cumulative-return figure, 0.89 Sharpe, and −27% maximum drawdown; **DRL without timing** has 2.33, 0.55, and −31%, respectively. The table’s cumulative-return convention appears to correspond to portfolio-value multiples in the accompanying figure, so it should not be read as a percentage return. [Allocation Results](https://www.alphaxiv.org/abs/2603.21330?page=7)

For the separate rolling-selection and rotation use cases, the table reports **5.98 cumulative return, 25.85% annualized return, and −38.95% maximum drawdown** for Rolling Strategy, versus **4.80, 22.32%, and −21.46%** for Adaptive Rotation. These are separate strategy configurations, not one directly comparable row-by-row ablation of the allocation results above. The paper’s tables also give different benchmark cumulative-return figures across experiments, so compare within each experiment rather than treating all reported totals as one unified leaderboard. [Use Case Results](https://www.alphaxiv.org/abs/2603.21330?page=8)

**Paper trading:** A daily-rebalanced ensemble ran in an Alpaca paper account from October 26, 2025 to March 12, 2026. It reports +19.76% total return, 1.96 Sharpe, and −12.22% maximum drawdown. The authors explicitly frame this short window as a test of system execution, not statistically significant evidence of alpha. They report tracking order rejections, guardrail triggers, and target-to-realized weight error, but do not give numerical values for those monitoring indicators in the text returned here. [Paper Trading Results](https://www.alphaxiv.org/abs/2603.21330?page=10)

**For your system:** FinRL-X is the more relevant blueprint for the human-promoted-strategy setup: keep strategy proposals separate from the final weight/execution interface, then add risk overlays and execution monitoring downstream. But its experiments are mostly daily or weekly U.S.-equity/ETF allocation—not round-the-clock scalping across FX, metals, energy, crypto, futures, and stocks. The paper discusses execution distortions such as latency, partial fills, slippage, and liquidity effects, but those risks are not the same as having validated them in short-horizon, multi-venue live trading. [Deployment Gaps](https://www.alphaxiv.org/abs/2603.21330?page=2)

## Newer or adjacent work

I could not verify direct citing papers for either attached paper. The following are **adjacent work or challenges**, not confirmed citation descendants:

- [FinRL Contests: Benchmarking Data-driven Financial Reinforcement Learning Agents](https://www.alphaxiv.org/abs/2504.02281) (2025) is relevant to benchmark design for learning-based trading agents.
- [Execution Realism and Reproducibility in LLM-Based Trading Systems: A Systematic Scoping Review and Evidence Audit](https://www.alphaxiv.org/abs/2606.08285) (2026) addresses the execution-realism and reproducibility gap central to evaluating FinRL-X-style systems.
- [How Execution Assumptions Change Short-Horizon Sharpe Rankings: Evidence from a Synthetic Trading Benchmark](https://www.alphaxiv.org/abs/2610.05077) (2026) is a direct challenge to relying on short-horizon backtest rankings without scrutinizing fill assumptions.
- [ViperQ: Order Flow Pattern Recognition via Auction Market Theory for Reinforcement Learning Trading](https://www.alphaxiv.org/abs/2609.13825) (2026) explores order-flow patterns as trading inputs, making it adjacent to the high-frequency futures signal problem.
- [PPO-HRAP: Proximal Policy Optimization with a Hybrid Regime-Aware Policy for Risk-Controlled Trading](https://www.alphaxiv.org/abs/2610.01325) (2026) focuses on regime-aware risk control, an area the first paper does not cover and FinRL-X handles only at a broad overlay level.

**Bottom line:** use the first paper, at most, to prototype rare-event prediction; use the second as an architectural pattern for turning vetted strategies into weights and monitored orders. Neither paper validates a complete multi-asset short-horizon system with robust net-of-cost returns, instrument-level sizing, exits, and drawdown limits.

## User

Follow-up 1: Go deeper on the two attached papers. For Label Unbalance in High-frequency Trading: how label imbalance distorts short-horizon models, which fixes it tests, how thresholds and position sizes should be set when classes are imbalanced, and what it implies for scalpers and their validation. For FinRL-X: which parts of its modular infrastructure (data, environment, agents, backtest, deployment, risk modules) map onto a multi-strategy system with a deterministic risk service, and what its results show. For both: how would they change across FX, stock indices, metals, energy, crypto, futures and single stocks, and what does each cost in growth versus what it protects?

## Aurelle

**The key distinction is that class rebalancing changes what a predictor learns, while a deterministic risk service should decide what the system is allowed to trade.** [Label Unbalance in High-frequency Trading](https://www.alphaxiv.org/abs/2503.09988) tests ways to train a rare-class predictor; [FinRL-X](https://www.alphaxiv.org/abs/2603.21330) offers a modular pipeline from data to portfolio weights and execution. Neither paper validates a complete, cross-asset scalping system.

## Label imbalance: what goes wrong and what the paper tests

The paper labels each observation by its forward one-minute return relative to a fee threshold: positive if return exceeds the fee, negative if it falls below the negative fee, and neutral otherwise. In its data, about 80% of labels are neutral and about 10% each are positive and negative. That skew encourages a model trained with ordinary loss to favor the common class; a model can look good on overall accuracy while missing the less frequent trade opportunities. The paper also notes the other side of the problem: rare examples may be noise, so aggressively emphasizing them can teach the model to chase spurious patterns. [Labels and Imbalance](https://www.alphaxiv.org/abs/2503.09988?page=3) [Imbalance Pitfalls](https://www.alphaxiv.org/abs/2503.09988?page=1)

It tests four main ways of changing training:

- **Undersample the neutral class:** randomly drop one eighth of neutral examples each epoch, roughly balancing the three labels.
- **Fixed class weights:** use weights of 8 for each directional class and 1 for neutral.
- **Distribution-based cost-sensitive loss:** calculate class weights from the observed class frequencies.
- **Focal loss:** increase the loss weight on examples the model finds difficult. The paper also describes a class-weighting variant based on per-class accuracy. [Tested Losses](https://www.alphaxiv.org/abs/2503.09988?page=6) [Cost-Sensitive Methods](https://www.alphaxiv.org/abs/2503.09988?page=7)

The result is **not that balancing always helps**. The authors report that fixed weighting and their cost-sensitive loss tend to perform better in their experiment, but undersampling and focal loss sometimes do worse than the unadjusted baseline. Results are shown as model experiments across six futures, not as a full trading simulation with net returns and drawdowns. [Imbalance Results](https://www.alphaxiv.org/abs/2503.09988?page=8)

### Setting thresholds and sizes for a scalper

The paper does **not** tune decision thresholds, calibrate class probabilities, translate predictions into positions, or test position sizing. Its class weights are training choices; they are not a prescription to trade eight times larger, nor do they imply that the model’s raw output probabilities can be used directly as probabilities of profitable trades.

A practical approach is to treat the model’s output as an input to a **separate decision rule**:

1. **Estimate probabilities on data representative of deployment.** If training used class weights or undersampling, first check calibration on naturally imbalanced, chronologically later data. Training reweighting can change the probability scale, so a predicted “70% up” should not be assumed to mean a 70% chance of an up move.
2. **Choose actions by expected net value, not a universal class-probability cutoff.** For each candidate action—long, short, or flat—estimate expected return after fees, spread, expected slippage, and other execution costs. Trade only when the estimated net advantage clears a safety margin. The long and short thresholds need not be symmetric: their costs, fill likelihood, and downside may differ.
3. **Size from risk and uncertainty, not class rarity.** Convert the chosen action into a small risk-budgeted position, accounting for forecast uncertainty, volatility, liquidity, and correlation with the rest of the book. Cap exposure per instrument, strategy, and portfolio. The deterministic risk service can always reduce or reject a proposed size.
4. **Reassess the threshold and size in walk-forward tests.** Select them on past validation windows, freeze them, and evaluate on later periods. Measure per-class precision and recall, calibration, trades per day, turnover, net P&L, tail losses, and drawdown—not just accuracy. For short-horizon labels that overlap in time, use time-aware splits and prevent overlapping target intervals from leaking across boundaries.

That procedure is a design recommendation, not a method demonstrated by the paper. The authors’ own validation uses a chronological 8:1:1 split and early stopping, but reports that they mistakenly used whole-dataset normalization at one point; they say this made performance look better and identify it as leakage/domain shift. That is a concrete warning for scalpers: all transforms, thresholds, and probability calibration must use only information available at the time. [Split and Normalization](https://www.alphaxiv.org/abs/2503.09988?page=3) [Leakage Warning](https://www.alphaxiv.org/abs/2503.09988?page=8)

For scalping, class balance is only one concern. Labels should reflect realistic executable prices and the strategy’s actual holding period; tests should account for spread, fees, rebates if applicable, latency, partial fills, and queue position. The paper uses a one-minute fee-threshold label on 20 days of Chinese futures data sampled every half-second; it does not establish that its label rule or model remains profitable after those execution effects. [Dataset Scope](https://www.alphaxiv.org/abs/2503.09988?page=7)

## FinRL-X: mapping its modules to your system

FinRL-X’s core design is a **target-weight interface**: each strategy pipeline produces desired portfolio weights, and downstream evaluation or execution consumes those weights. Its stated transformations are selection, allocation, timing, and a portfolio-level risk overlay. [Weight Interface](https://www.alphaxiv.org/abs/2603.21330?page=4)

For a multi-strategy system with a deterministic risk service, I would map the components this way:

| FinRL-X component | Fit for your system | Important boundary |
|---|---|---|
| **Data layer** | Normalize and timestamp market and reference data; retain raw snapshots; provide consistent historical replay and live feeds. Add per-venue calendars, contract metadata, and point-in-time data. | Its paper describes market, fundamental, macro, and news inputs aligned to a trading calendar; that is not evidence of validated tick-level feeds across your requested venues. [Data Layer](https://www.alphaxiv.org/abs/2603.21330?page=4) |
| **Environment / backtest** | Give each strategy a repeatable simulation interface, then assess it under common instruments, timestamps, costs, and order rules. | The paper reports backtesting via a common weight interface and discusses execution modeling, but does not establish high-frequency fill, queue, or market-impact fidelity. [Backtest Interface](https://www.alphaxiv.org/abs/2603.21330?page=5) |
| **Agents / strategies** | Let agents propose signals or target weights; compose rule-based and learning-based modules behind a stable interface. For your governance model, agents should never have broker credentials or authority to release live orders. | FinRL-X supports DRL allocators and timing signals, but it does not specify a human-promotion workflow. Add that as a separate authorization gate. [Composability](https://www.alphaxiv.org/abs/2603.21330?page=2) |
| **Deterministic risk service** | Place after strategy proposals and before order generation. Enforce hard caps: per-trade and per-instrument exposure, strategy risk budgets, aggregate correlated exposure, leverage, loss/drawdown limits, trading halts, and stale-data or feed-failure rules. | FinRL-X describes portfolio-level volatility scaling and leverage constraints, not a complete deterministic kill-switch or instrument-level risk specification. [Risk Overlay](https://www.alphaxiv.org/abs/2603.21330?page=5) |
| **Deployment and monitoring** | Translate approved weights into orders; reconcile target versus realized positions; persist state; log decisions and failures; monitor rejected orders, guardrail triggers, and weight-tracking error. | These are useful system controls, but the paper’s paper-trading evidence is daily rebalancing in a broker paper account, not proof of low-latency multi-market operation. [Deployment Safeguards](https://www.alphaxiv.org/abs/2603.21330?page=5) |

This separation also fits your human-promotion rule: agents produce candidates; a human promotes a versioned strategy; the risk service independently constrains every live proposal; and the execution service alone has broker access. That governance arrangement is a recommended extension, not something the paper claims to implement.

### What FinRL-X’s results show—and do not show

The historical tests use liquid U.S. equities and ETFs, January 2018–October 2025, with 10 basis points of proportional transaction costs per side. The paper says decisions use information available up to the decision time and that learning-based models use rolling out-of-sample validation. It does not provide enough fold-level detail here to assess all model-selection, survivorship, or execution assumptions. [Evaluation Design](https://www.alphaxiv.org/abs/2603.21330?page=6)

The timing ablation is suggestive: DRL with timing reports a Sharpe of 0.89 and maximum drawdown of −27%, compared with 0.55 and −31% without timing. Other allocation methods also show improved risk-adjusted results with timing in this table. That supports the idea that timing can be composed with allocation in their setup; it does **not** prove that timing improves scalper strategies or transfers across markets. [Timing Ablation](https://www.alphaxiv.org/abs/2603.21330?page=7)

A separate multi-asset rotation use case reports a Sharpe of 1.10 and maximum drawdown of −21.46%; its rolling-selection example reports 0.93 Sharpe and −38.95% drawdown. The paper’s short paper-trading period reports +19.76% total return, Sharpe 1.96, and −12.22% maximum drawdown, with daily rebalancing. The authors explicitly say the short paper-trading window is intended to validate the execution pipeline, not establish statistically significant alpha. [Rotation and Selection](https://www.alphaxiv.org/abs/2603.21330?page=8) [Paper Trading](https://www.alphaxiv.org/abs/2603.21330?page=10)

One useful caution is visible in the stress case: the paper describes a roughly 12.2% peak-to-trough drawdown after an extreme move in a leveraged instrument, and says this motivates volatility-aware scaling and instrument-specific caps. That is evidence of why such controls matter—not evidence that the proposed controls already prevented the loss. [Stress Case](https://www.alphaxiv.org/abs/2603.21330?page=11)

## What changes across markets

The asset-specific points below are **design implications**, not cross-asset experiments reported in either paper. The same high-level system can be reused, but labels, cost models, trading calendars, sizing units, and hard risk limits should be instrument-aware.

| Market | Adaptation needed | Main protection and potential growth cost |
|---|---|---|
| **FX** | Model by pair and session; account for spread, rollover, venue-specific liquidity, and currency exposure shared across pairs. | Currency and session caps protect against correlated exposure and thin periods; tighter limits may suppress trades during short-lived opportunities. |
| **Stock indices** | Handle cash-index versus futures/ETF instruments, session gaps, contract multipliers, and event-driven volatility. | Index-level exposure and overnight-gap controls reduce concentration; they can limit participation in fast breakouts. |
| **Metals** | Separate precious and industrial metals, contract specifications, session liquidity, and related FX exposure. | Metal- and complex-level limits protect against correlated shocks; stricter caps can cut risk during strong directional moves. |
| **Energy** | Treat each contract month and roll separately; model expiry, gaps, limit moves, and potentially abrupt liquidity changes. | Contract and expiry controls protect against discontinuities and roll effects; lower limits can reduce exposure to high-volatility trends. |
| **Crypto** | Account for 24/7 operation, venue fragmentation, funding, liquidation rules, and rapid liquidity changes. | Always-on monitoring, venue and leverage caps, and loss halts protect against operational and liquidation risk; they may constrain overnight strategy capacity. |
| **Futures** | Normalize by tick value, multiplier, margin, expiry, and session; distinguish contract-level from underlying-level exposures. | Per-contract and portfolio margin controls protect against leverage and expiry risk; risk budgets can materially limit notional exposure. |
| **Single stocks** | Use point-in-time membership and corporate-action data; model halts, auctions, borrow availability, and name-specific liquidity. | Per-name, sector, and borrow caps reduce single-name and crowding risk; they can exclude the most volatile—and sometimes most profitable—setups. |

A single global class threshold or position size is especially unsuitable here. “One tick,” “one basis point,” and “one unit of predicted confidence” do not represent the same execution cost or risk across these instruments. A more portable design is to let each strategy estimate its own signal and expected net edge, while a central risk service expresses limits in common portfolio-risk terms and applies instrument-specific constraints before orders are sent.

## Growth versus protection

For **Label Unbalance**, weighting or undersampling can make rare directional cases more visible to the learner, but it can also raise false positives or distort probability calibration. The paper’s own mixed results argue for selecting the fix by *out-of-sample net trading utility*, not by class balance or accuracy alone. The protective value is better attention to rare moves; the cost is potentially more noisy trades, turnover, and transaction-cost exposure.

For **FinRL-X**, timing and volatility overlays can reduce exposure in unfavorable regimes, and its reported allocation ablations show a drawdown improvement in some configurations. But an overlay that scales down exposure necessarily gives up some upside when its signal is wrong or lags a rapid reversal. The paper’s broader lesson is architectural: keep those controls modular and observable, so a strategy’s intended weights can be compared with the risk-approved and actually executed portfolio. [Risk Overlay](https://www.alphaxiv.org/abs/2603.21330?page=5)

## User

Follow-up 2: Combinations. What would Label Unbalance in High-frequency Trading and FinRL-X each combine with from other areas of this system: meta-labelling and triple-barrier exits, edge-to-cost admission gates, deflated Sharpe and search ledgers, live alpha-decay detection, kill switches, stress scenarios, LLM research harnesses? Name concrete pairs or triples of papers with links, what the combined method or workflow would do for sizing, validation or monitoring, and why. Then say which single idea from each paper is most worth building first.

## Aurelle

**Build the label-imbalance classifier as a signal proposer, then put admission, sizing, and live permission behind separate gates.** The useful combination is not to let a rebalance method or a research agent decide that an imbalanced-model prediction is automatically a trade.

The pairings below are **proposed integrations**, not combined methods evaluated by the papers. [Label Unbalance in High-frequency Trading](https://www.alphaxiv.org/abs/2503.09988) tests classification-loss adjustments; [FinRL-X](https://www.alphaxiv.org/abs/2603.21330) provides a modular, target-weight pipeline. Neither paper demonstrates the full set of controls you list.

### 1. Imbalanced signal + meta-labeling and triple-barrier outcomes + FinRL-X

**Papers:** [Label Unbalance in High-frequency Trading](https://www.alphaxiv.org/abs/2503.09988) + [FinRL-X](https://www.alphaxiv.org/abs/2603.21330). Meta-labeling and triple-barrier exits are the additional method components in this proposed pairing.

Use the imbalanced classifier as the **primary model**: it proposes a direction or trade candidate. A second, separately trained **meta-model** estimates whether taking that candidate is worthwhile under the current context. Define candidate outcomes using triple barriers: profit target, stop, or maximum holding time. The meta-model’s inputs can include primary-model confidence, spread, volatility, liquidity, and time of day.

The output should be more than “up/down”: it should estimate the chance and payoff of each exit outcome. Convert that to expected **net** edge after expected costs; only then ask FinRL-X’s allocation stage for a target weight. A deterministic risk service caps that weight, and the execution layer handles orders. This separates *finding a possible direction* from *deciding whether to risk capital on it*.

**Why:** the first paper’s three-class, fee-threshold label does not test exits or sizing. Barrier outcomes make the training target more like the trade lifecycle, while FinRL-X gives the resulting decision a downstream allocation interface. Keep the second model calibrated on the natural class distribution; class weighting in the primary model does not make its probabilities reliable for sizing. [Labels and Imbalance](https://www.alphaxiv.org/abs/2503.09988?page=3) [Weight Interface](https://www.alphaxiv.org/abs/2603.21330?page=4)

### 2. Edge-to-cost admission + execution-aware evaluation

**Papers:** [Label Unbalance in High-frequency Trading](https://www.alphaxiv.org/abs/2503.09988) + [FinRL-X](https://www.alphaxiv.org/abs/2603.21330) + [How Execution Assumptions Change Short-Horizon Sharpe Rankings](https://www.alphaxiv.org/abs/2610.05077).

Add a deterministic **admission gate** between signal generation and sizing. For each proposed trade, estimate expected gain against a conservative cost estimate: spread, fees, slippage, and a penalty for fill uncertainty. Reject the trade if the net edge is below a predefined margin. Use venue- and instrument-specific estimates rather than one global fee number.

Then replay candidates under more than one execution assumption—e.g., optimistic, expected, and stressed fills—and see whether strategy rankings or admission decisions change. The execution-assumptions paper is relevant because its topic is precisely how fill assumptions can change short-horizon Sharpe rankings; it is not evidence that this gate is already validated for your markets.

**Why:** the first paper’s label threshold accounts for a fee in defining classes, but it does not report net portfolio returns under realistic fills. FinRL-X describes transaction-cost and slippage modeling, while also recognizing the gap between simulation and broker execution. A cost gate makes the model’s “directional opportunity” compete against the hurdle that an actual scalp must clear. [Label Threshold](https://www.alphaxiv.org/abs/2503.09988?page=3) [Execution Gaps](https://www.alphaxiv.org/abs/2603.21330?page=2)

### 3. Strategy search ledger + leakage-safe promotion tests

**Papers:** [FinRL-X](https://www.alphaxiv.org/abs/2603.21330) + [What survives honest evaluation? Leakage-safe, search-aware assessment of LLM-driven trading strategy discovery](https://www.alphaxiv.org/abs/2608.27734) + [Reliable Before Profitable: QuantHarness for Governing Financial Strategy Development with LLM Agents](https://www.alphaxiv.org/abs/2610.26101).

Give each candidate strategy a permanent record: hypothesis, code/version, data range, instruments, labels, features, thresholds, costs, execution assumptions, every parameter trial, and every rejected variant. Run time-ordered, leakage-aware validation; reserve a final untouched test; then require a human promotion decision before the candidate can reach live paper or live routing. Use deflated-Sharpe or backtest-overfitting diagnostics as **additional search-aware checks**, not replacements for the ledger or untouched evaluation.

The named papers here are about leakage-safe evaluation and governing agent-generated research; I did not verify a retrieved paper that establishes a specific DSR or PBO implementation for this combination. FinRL-X contributes the stable strategy-to-weight interface, not a complete search-accounting protocol.

**Why:** when agents can rapidly propose variants, the number of tried strategies is part of the evidence. Recording only the winner hides selection effects. The ledger gives reviewers the denominator—what was tried—not just a polished backtest.

### 4. Live alpha-decay monitoring + exposure reduction or retirement

**Papers:** [FinRL-X](https://www.alphaxiv.org/abs/2603.21330) + [AlphaAgent: LLM-Driven Alpha Mining with Regularized Exploration to Counteract Alpha Decay](https://www.alphaxiv.org/abs/2502.16789) + [Measuring Strategy-Decay Risk: Minimum Regime Performance and the Durability of Systematic Investing](https://www.alphaxiv.org/abs/2604.08356).

Track each strategy’s **realized net edge**, forecast calibration, win/loss profile, turnover, and fill quality against its expected range. Segment monitoring by instrument, session, and regime where sample sizes allow. If performance persistently degrades, first reduce that strategy’s risk budget; if it breaches a predeclared failure criterion, suspend it and send it back for research review.

AlphaAgent is about alpha mining and decay, while the durability paper addresses decay risk; neither result as retrieved establishes a production-ready live alarm. Treat them as motivation for this monitoring design, not as proof of a validated threshold. FinRL-X supplies the modular allocation and tracking structure where such a strategy-level risk adjustment can be applied. [Monitoring](https://www.alphaxiv.org/abs/2603.21330?page=10)

### 5. Stress scenarios + hard risk controls + monitored execution

**Papers:** [FinRL-X](https://www.alphaxiv.org/abs/2603.21330) + [Execution Realism and Reproducibility in LLM-Based Trading Systems: A Systematic Scoping Review and Evidence Audit](https://www.alphaxiv.org/abs/2606.08285) + [How Execution Assumptions Change Short-Horizon Sharpe Rankings](https://www.alphaxiv.org/abs/2610.05077).

Replay candidates through adverse but plausible scenarios: spread widening, slippage spikes, partial or rejected fills, stale feeds, venue disconnects, volatility jumps, contract rolls, and correlated market moves. Have the risk service enforce **hard rules** independently of agent output: maximum exposure and leverage, stale-data rejection, per-strategy loss limits, aggregate drawdown limits, and a kill switch that blocks new orders and/or flattens according to an explicitly approved policy.

FinRL-X describes execution safeguards, logging, persistence, and tracking target-to-realized weights. Its paper-trading period also includes a roughly 12.2% drawdown tied to an extreme leveraged-instrument move, which motivates instrument-specific limits; it does not demonstrate that a kill switch prevented the loss. [Stress Case](https://www.alphaxiv.org/abs/2603.21330?page=11)

**Why:** monitoring is not a kill switch. A deterministic service should own the authority to reject or stop orders; the agent should not be able to override that service. Stress tests are how you check whether the rules actually trip under the scenarios they are meant to contain.

### 6. LLM research harness + sealed evaluation and human promotion

**Papers:** [FinRL-X](https://www.alphaxiv.org/abs/2603.21330) + [Reliable Before Profitable: QuantHarness for Governing Financial Strategy Development with LLM Agents](https://www.alphaxiv.org/abs/2610.26101) + [What survives honest evaluation?](https://www.alphaxiv.org/abs/2608.27734).

Let an LLM harness propose hypotheses, generate candidate code, and summarize results—but not control capital or label its own candidate as approved. The harness should enforce data-cutoff checks, strategy-versioning, cost assumptions, test-set access controls, and a record of all trials. A separate evaluator runs the prescribed tests, and a human decides promotion. Once approved, the candidate only produces a proposal or target weight; the risk and execution services remain independent.

**Why:** this matches your governance model directly. It separates fast idea generation from evidence review and capital authorization. The cited harness paper is on governing agent-driven financial strategy development; it does not imply LLMs can reliably enforce their own boundaries without external controls.

## Which idea to build first

For **Label Unbalance**, build the **fixed class-weighting or distribution-based cost-sensitive classifier as a signal-only challenger**, evaluated against the unweighted model on chronological out-of-sample data. Those are the imbalance treatments the authors report as generally more effective in their experiment; undersampling and focal loss sometimes underperform. Add an edge-to-cost gate before turning predictions into trades, because the paper does not test position sizing or net trading outcomes. [Loss Comparison](https://www.alphaxiv.org/abs/2503.09988?page=8)

For **FinRL-X**, build the **weight-centric interface with a deterministic risk overlay placed between strategy proposal and order generation**. It gives every small strategy the same downstream contract, lets the risk service cap or reject exposure consistently, and keeps broker execution separate from strategy logic. That architectural seam is the most directly reusable contribution for a multi-strategy system; its reported portfolio results are encouraging ablations and demonstrations, not validation of your short-horizon multi-asset strategies. [Risk Pipeline](https://www.alphaxiv.org/abs/2603.21330?page=5)

