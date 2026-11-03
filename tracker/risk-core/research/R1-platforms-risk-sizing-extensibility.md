---
ticket: R1-platforms-risk-sizing-extensibility
title: How outside platforms do risk and sizing, and how they stay extensible
date: 2026-11-03
author: opus research agent (read-only on the repo; this file is the only write)
asked by: operator M10, `tracker/risk-core/seeds/operator-words-2026-11-03.md:10,13` ("How does Strategy Quant handle risk management and position sizing?", "what is there that we can borrow?", "how N8N handles stuff")
method: source code fetched as text from GitHub (LEAN master, n8n master, NautilusTrader develop, all on 2026-11-03), vendor docs read with WebFetch, the local MQL5 corpus (`C:\Users\Mubarak\Desktop\QMX\.worktrees\mql5-library\data\mql5-library\`, 3,128 articles) searched for risk-manager articles the earlier work missed, and two PDFs turned to text with pdftotext. Firecrawl ran out of credits early, so WebFetch replaced it.
labels: CHECKED = seen in source code or a vendor page (link or path:line given). PRACTITIONER = an article author's own build or test, not a vendor statement. SNIPPET = seen only in a search-result summary because the page refused the fetch (HTTP 403); weakest grade. INFERRED = my reasoning. [judgment] = what QMX could borrow, one line, an opinion and not a design.
line numbers: GitHub line numbers are from the branch named above on 2026-11-03. They drift as the projects change.
not done: QMX itself is not designed here. No account was created and nothing was signed in to.
---

# R1: How outside platforms do risk and sizing, and how they stay extensible

## 0. The short version

1. **Every platform makes the sizer a small function with one job.** It takes money, the entry, the stop and the instrument, and it returns a size. Zero means "skip". MT5 `CheckOpenLong(price, sl)`, StrategyQuant `computeTradeSize(...)`, Backtrader `_getsizing(comminfo, cash, data, isbuy)`, Nautilus `calculate_fixed_risk_position_size(...)` and the RiskGate oracle's `approved / lot / reason` all have this shape (sections 2.2, 3.1, 3.3, 6.1, 6.2).
2. **Risk runs after the signal and mostly shrinks or blocks.** LEAN risk models adjust targets. Nautilus denies orders with a reason code. Zipline raises an error. None of the built-in risk models grows a position (sections 1.4, 6.1, 6.3).
3. **The operator's "split it across 10 units" confusion is a real fork, and the platforms ship both answers.** LEAN's equal-weighting model gives each active idea 1/N. Its insight-weighting model gives each idea its own weight and scales down only when the total passes 100 %. freqtrade splits the free balance across free slots. RiskMetrics sets a parent limit *below* the sum of its children's limits on purpose, because the children rarely lose together (sections 1.3, 5.3, 6.4).
4. **n8n keeps defaults and freedom together with four simple rules.** Each node declares its settings as a typed list with defaults. A saved workflow stores only the values that differ from the defaults. Each saved node stores the version it was built with, so old work keeps running when a new version ships. And there is a raw-code node for anything the catalogue lacks (section 4).
5. **StrategyQuant's money management is a plug-in class, not a fixed menu.** A snippet extends `MoneyManagementMethod`, and Java annotations (`@Parameter(defaultValue, minValue, maxValue, step, category)`) generate the settings form. The earlier study listed the menu but missed the plug-in door (section 2.2).
6. **The MT5 Wizard's module header is a tiny schema.** `Title`, `Type=Money`, `Class`, and one `Parameter=Name,type,default,description` line per setting. The Wizard builds its form from that comment block (section 3.1).
7. **The 2025-26 MQL5 articles the earlier survey missed are mostly about architecture, not formulas.** A central "risk oracle" for many EAs, three scopes of risk (trade, basket, account), a split between "facts about the account" and "my response to them", a smooth taper instead of a hard stop, and a risk-manager state machine with a "restore" state (section 3.2).
8. **Built-in brakes are crude everywhere.** LEAN's portfolio drawdown model liquidates at 5 % and then re-arms at once from the new value. freqtrade's locks count stops. Graded answers (cut half, wait, restore; a "reduce-only" mode; a smooth taper; warnings at 80 % and 90 %) show up only in Nautilus and in recent community work (sections 1.4, 3.2, 6.1).
9. **Public Bloomberg material is thin.** It confirms the levels (portfolio against benchmark, factor, holding; VaR, tracking error, four kinds of scenario) but not how limits are set. Limits live in separate compliance tools (AIM) with pre-trade, post-trade and end-of-day checks. The clearest primary source on how pro limits are expressed is the RiskMetrics technical document: one money unit (VaR) for every desk, set as a hierarchy (section 5).
10. **No shipped product learns its own risk numbers with guardrails.** "Self-configuring" in shipped tools means presets plus numbers computed from live state (equity × a percent). Learning from the record exists only as a sample formula (MT5 `DecreaseFactor`), an article class (Kelly from the strategy's own trades), or a vendor test that found an equity-curve filter did not help (sections 2.3, 3.1, 3.2).

## 0.1 Where the earlier research was wrong or thin

| Earlier claim | Where | What this pass found | Grade |
|---|---|---|---|
| LEAN "merges" the unit sizer and the pod allocator in one Portfolio Construction model | `tracker/risk-sizing/research/04-platform-study.md:537` | Right but thin. LEAN never sizes from the stop. It sizes by a share of portfolio value, turned into lots by the margin model. A "risk 1 % to the stop" sizer does not exist in the framework. See 1.3. | Thin |
| LEAN ships drawdown and trailing risk models | `04-platform-study.md:242` | Thin. Every built-in risk model only liquidates (target 0). The portfolio drawdown model forgets its high after it fires and re-arms at once. Several models run in order, and the newer target for a symbol wins. See 1.4. | Thin |
| SQ money management is a list of seven methods set per strategy | `03-strategyquant.md:268-272` | Thin. Money management is an open plug-in class with annotated settings. QuantAnalyzer can re-size an existing trade list under several methods without a new backtest, and has "equity control" as snippets. SQ's own test found its moving-average equity filter "doesn't improve anything". See 2.2, 2.3. | Thin |
| MT5's money interface is "percentage and open-volume methods" | `20-self-configuring-systems.md:30` | Thin. `CExpertMoney` also has `CheckClose()` (a money module can ask to close a position) and `ValidationSettings()`. The Wizard's comment header is a settings schema. See 3.1. | Thin |
| `CMoneySizeOptimized` reduces volume after consecutive losing deals | `20-self-configuring-systems.md:30` | Plausible, but the vendor page does not state the rule. It says only that "lot size depending on results of the previous deals". The formula seen in code is MetaQuotes' Moving Average sample: `lot = lot - lot*losses/DecreaseFactor` once losses > 1. See 3.1. | Source was weaker than stated |
| The 8 Oct MQL5 survey's top 40 covers risk management | `workroom/risk-lab-2026-10-05/grounding/03-mql5-articles.md:18-84` | Thin. At least 15 risk-manager articles from 2024-26 are in the corpus and absent from the survey, including RiskGate (21720), the three-scope framework (24477), the rule-set/response split (24237, 24249) and the restore-state risk manager (15085). See 3.2. | Thin |
| "Sizing from stat-test, resampling or ML is empty" in the pilot grid | `06-mql5-pilot.md:221` | That grid covered 37 sampled articles only. The corpus has sizing that reads the strategy's own record (24147 Kelly class) and a smooth taper to the remaining loss budget (24249). Evidence in both is simulation, not live. See 3.2. | Thin (sample limit, as the pilot itself said) |

Nothing in the earlier files was found to be plainly false.

---

## 1. QuantConnect LEAN: the Algorithm Framework

The earlier study (`04-platform-study.md:229-266`) already maps the five models to QMX. This section adds the code-level contract and how a size is decided.

### 1.1 The extension points (CHECKED, source)

| Stage | Base class and method to override | Input | Output |
|---|---|---|---|
| Alpha | `AlphaModel.Update(...)` | data slice | `Insight` objects |
| Portfolio construction | `PortfolioConstructionModel.CreateTargets(algorithm, insights)` ([PortfolioConstructionModel.cs:93](https://github.com/QuantConnect/Lean/blob/master/Algorithm/Portfolio/PortfolioConstructionModel.cs#L93)); most models override only `DetermineTargetPercent(activeInsights)` (:195) | insights | `PortfolioTarget` per symbol (a quantity) |
| Risk management | `RiskManagementModel.ManageRisk(algorithm, targets)` ([RiskManagementModel.cs:32](https://github.com/QuantConnect/Lean/blob/master/Algorithm/Risk/RiskManagementModel.cs#L32)) | targets | adjusted targets |
| Execution | `ExecutionModel` | targets | orders |

- An `Insight` carries `Symbol`, `Period` (expiry), `Magnitude`, `Confidence`, `Weight`, `Score`, `SourceModel` and `Tag` ([Insight.cs:49-126](https://github.com/QuantConnect/Lean/blob/master/Common/Algorithm/Framework/Alphas/Insight.cs#L49)). CHECKED.
- The docs do not define the range of `Weight`, `Confidence` or `Magnitude`. They say only that some portfolio models need them. CHECKED ([alpha key concepts](https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/alpha/key-concepts)).
- Several alpha models can run. Each insight is tagged with its model's name, and the portfolio model "defines how the Insight collection is combined". CHECKED (same page).
- A portfolio model rebalances on a schedule, on insight changes and on universe changes. `RebalanceOnInsightChanges` and `RebalanceOnSecurityChanges` both default to true ([PortfolioConstructionModel.cs:39-44](https://github.com/QuantConnect/Lean/blob/master/Algorithm/Portfolio/PortfolioConstructionModel.cs#L39)). CHECKED.
- When an insight expires and no other insight is active for that symbol, the model emits a "flatten to 0" target (:132-140). CHECKED. INFERRED: an idea's expiry closes its position unless a fresh idea renews it.

### 1.2 How a size is decided (CHECKED, source)

1. The portfolio model returns a percent per insight from `DetermineTargetPercent` (:195).
2. `PortfolioTarget.Percent(...)` turns the percent into a quantity ([PortfolioTarget.cs:135-197](https://github.com/QuantConnect/Lean/blob/master/Common/Algorithm/Framework/Portfolio/PortfolioTarget.cs#L135)):
   - It rejects a percent above `MaxAbsolutePortfolioTargetPercentage` or below `MinAbsolutePortfolioTargetPercentage` (:138).
   - It shrinks the percent by the free cash buffer: `percent × TotalPortfolioValueLessFreeBuffer / TotalPortfolioValue` (:163).
   - It divides by the security's leverage to work in margin terms (:166).
   - The buying-power model returns whole lots for that margin share.
3. The docs say the target weight "is an unleveraged value", and `set_holdings` keeps a 0.25 % cash buffer for gaps. An order below `minimum_order_margin_portfolio_percentage` is silently skipped. CHECKED ([position sizing](https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/position-sizing)).

**What this means.** LEAN sizes by "how much of the portfolio to hold", not by "how much to lose if the stop is hit". The stop never enters the framework's sizing. INFERRED from the code above. This is the gap the earlier study did not state. A scalper's size in QMX is a stop-distance question, so LEAN's sizing maths does not carry over. Its *staging* does.

### 1.3 Two ways to share capital across many ideas (CHECKED, source and docs)

| Model | Rule | Code |
|---|---|---|
| Equal weighting | Each active idea gets 1/N of the portfolio. Ten ideas get 10 % each. | `var percent = count == 0 ? 0 : 1m / count;` ([EqualWeightingPortfolioConstructionModel.cs:124](https://github.com/QuantConnect/Lean/blob/master/Algorithm.Framework/Portfolio/EqualWeightingPortfolioConstructionModel.cs#L124)) |
| Insight weighting | Each idea gets its own `Weight`. Only if the weights add up to more than 1 are they all scaled down so they add up to 1. | `if (weightSums > 1) weightFactor = 1 / weightSums;` ([InsightWeightingPortfolioConstructionModel.cs:129-147](https://github.com/QuantConnect/Lean/blob/master/Algorithm.Framework/Portfolio/InsightWeightingPortfolioConstructionModel.cs#L129)) |
| Confidence weighting | As insight weighting, but uses `Confidence`. | docs ([supported models](https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/portfolio-construction/supported-models)) |
| Accumulative insight | Each insight moves the position by a fixed 3 % step, up or down. | same page (`percent` default 0.03) |
| Risk parity, mean-variance, Black-Litterman, sector weighting, mean reversion (OLMAR) | Optimisers over a lookback (for example `period` 63 or 252 days) | same page |

INFERRED: the operator's M10 objection ("1 unit will get $20 and then 10 different units each will get $2") describes the equal-weighting rule. The insight-weighting rule is the other answer: each unit keeps its own size until a total cap binds. LEAN treats this as a swappable model, not a fixed law.

### 1.4 Shipped risk models and how they combine (CHECKED)

| Model | Default | What it does |
|---|---|---|
| `MaximumDrawdownPercentPerSecurity` | 0.05 | Liquidates one holding whose unrealised loss passes 5 %, and cancels its insights ([MaximumDrawdownPercentPerSecurity.cs:37-70](https://github.com/QuantConnect/Lean/blob/master/Algorithm.Framework/Risk/MaximumDrawdownPercentPerSecurity.cs#L37)) |
| `MaximumDrawdownPercentPortfolio` | 0.05, `isTrailing=false` | Liquidates every targeted holding when the portfolio falls 5 % from its start (or from its high, if trailing). Then it sets `_initialised = false`, so the next call takes the current value as the new start: "restart investing on next rebalancing period" ([MaximumDrawdownPercentPortfolio.cs:41-85](https://github.com/QuantConnect/Lean/blob/master/Algorithm.Framework/Risk/MaximumDrawdownPercentPortfolio.cs#L41)) |
| `MaximumUnrealizedProfitPercentPerSecurity` | 0.05 | Takes profit on one holding at +5 % |
| `MaximumSectorExposureRiskManagementModel` | 0.20 | Caps one sector at 20 % |
| `TrailingStopRiskManagementModel` | 0.05 | Trailing stop per holding |
| `NullRiskManagementModel` | none | Changes nothing |

Defaults from the [supported risk models page](https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/risk-management/supported-models). CHECKED.

- `manage_risk` runs every time step. A custom model extends `RiskManagementModel` and implements `manage_risk(algorithm, targets) -> targets`, plus optional `on_securities_changed`. Calling `add_risk_management` several times adds several models. The docs say each later model receives the output of the one before it. They also tell authors to cancel a liquidated symbol's insights "to avoid reordering afterward". CHECKED ([risk key concepts](https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/risk-management/key-concepts)).
- In code, the composite model passes each model the merged list so far and keeps the newest target per symbol: `targets = riskAdjusted.Concat(targets).DistinctBy(t => t.Symbol)` ([CompositeRiskManagementModel.cs:89-100](https://github.com/QuantConnect/Lean/blob/master/Algorithm/Risk/CompositeRiskManagementModel.cs#L89)). CHECKED.
- INFERRED: no built-in model reduces size by a fraction, waits out a cool-down, or asks a human. The portfolio breaker forgets the loss the moment it fires. That is the opposite of the old QMX circuit breaker the operator recalls.

### 1.5 Ships, swaps, borrow

- **Ships:** about ten portfolio models and six risk models, each with one or two settings and defaults. CHECKED (pages above).
- **Users swap:** any of the five stages, by subclass, in Python or C#. A user may also skip the framework and write the "classic" algorithm. CHECKED (`04-platform-study.md:233-239`).
- **[judgment]** Borrow the fixed stage order and the "risk returns adjusted targets plus a reason" contract, and treat "1/N" versus "own weight, capped in total" as a declared allocation mode that a unit's owner picks, not a hidden law.

---

## 2. StrategyQuant X and QuantAnalyzer

The earlier study (`tracker/risk-sizing/research/03-strategyquant.md`) covers the builder, the robustness funnel (`:176-208`), workflows (`:216-250`), the portfolio tools (`:251-266`) and the evidence that the funnel does not select live survivors (`:198-208`). This section adds the extension doors for sizing and the trade-list simulators.

### 2.1 What ships (from the earlier study, CHECKED there)

- Money management methods: fixed size, fixed amount, risk a fixed % of account, risk a fixed % of balance, stock size by price, crypto size by price, simple martingale, and (b143) ATR risk sizing. Set per strategy; the exported EA carries it (`03-strategyquant.md:270`).
- Robustness tests: higher precision, What-If, Monte Carlo trade shuffles and retests (new in 2025-26: block bootstrap and "randomly degrade execution"), extra markets, SPP, walk-forward and the WF Matrix (`03-strategyquant.md:184-196`).
- Portfolio: Portfolio Master (pick k of N with correlation and sector caps), Portfolio Composer (weights, Markowitz, VaR and expected shortfall that assume normal returns) (`03-strategyquant.md:253-262`).

### 2.2 The money-management plug-in (CHECKED, vendor tutorial)

From the [ATR volatility sizing tutorial](https://strategyquant.com/doc/programming-for-sq/atr-volatility-simple-sizing/):

- A new method is a Java class that `extends MoneyManagementMethod`, created from the Code Editor as a "Money Management" snippet and saved to `User/Snippets/SQ/MoneyManagement`.
- One method to write: `computeTradeSize(StrategyBase strategy, String symbol, byte orderType, double price, double sl, double tickSize, double pointValue)`, returning the size. A commenter says build 138 added a `sizeStep` argument, so the signature changes between builds.
- The class header is `@ClassConfig(name="ATR Volatility Sizing", display="ATR Volatility Sizing: #Size# lots with multiplication #Multiplier#")`. The `display` string is a template that shows the current settings in the list.
- Each setting is one annotated field, for example `@Parameter(defaultValue="5", minValue=2, name="Fast ATR Period", maxValue=480, step=1, category="Default")`. The form is built from these annotations.
- After a restart the new method appears in the Money Management tab.
- Version drift is real: a codebase page shows a snippet failing to compile because it "does not override abstract method computeTradeSize" (search result for [codebase: fixed proportional size](https://strategyquant.com/codebase/money-management-fixed-proportional-size/), SNIPPET).

INFERRED: a settings schema (type, default, min, max, step, group, display label) written next to the code is what lets SQ ship defaults and still accept any new method. It is the same idea as n8n's `properties` (section 4) and the MT5 Wizard header (section 3.1).

### 2.3 Trade-list simulators: re-size without re-testing (CHECKED, vendor docs and blog)

- **Money Management simulator.** QuantAnalyzer "DOESNT RUN A NEW BACKTEST, it 'only' analyzes existing trades". It re-sizes the trade list under several methods (fixed lots, risk a fixed amount, risk a fixed % of account with a maximum lot cap). When a trade has no stop in the report, the stop is taken from the "maximum or average loss" found by "Recognize SL from orders". Each result can be moved into the databank for comparison. The vendor notes risk-% "has the best performance, but also the biggest drawdowns". ([QuantAnalyzer money management simulation](https://strategyquant.com/doc/quantanalyzer/money-management-simulation/)).
- **Equity control.** It simulates "switching a strategy on and off based on the equity curve". "Every equity control method is implemented as a simple code snippet", and users can write their own in QuantEditor ([equity control](https://strategyquant.com/quantanalyzer/equity-control/)).
- **The vendor's own test of equity control.** A 20-period moving average on the equity curve: take trades only when equity is above it, and keep tracking skipped trades as paper trades. The conclusion: "this kind of equity control doesn't improve anything." A variant that *doubled* size below the average made more money with a slightly larger drawdown ([blog: better results with equity control?](https://strategyquant.com/blog/better-results-with-equity-control)). PRACTITIONER (vendor's one test, one strategy).
- **What-If scenarios** filter the existing trades by hours, days, skipped trades, and so on, and are also snippets ([What-If scenarios](https://strategyquant.com/quantanalyzer/what-if-scenarios/); codebase category "What If scenarios (SQ)", SNIPPET).

INFERRED: three of SQ's sizing and braking tools work on a finished trade list, so trying a new sizing rule costs seconds, not a backtest. The vendor's null result on its own equity filter is a warning for any "brake on the equity curve" idea: test it, don't assume it.

### 2.4 Ships, swaps, borrow

- **Ships:** eight sizing methods, three trade-list simulators, a robustness funnel, portfolio pickers.
- **Users swap:** sizing methods, equity-control methods, What-If filters, ranking and correlation formulas, all as annotated Java snippets (above; portfolio snippets in `03-strategyquant.md:257`).
- **[judgment]** Borrow "a sizing or brake rule is a small annotated plug-in" and "try it on the recorded trade list first, before any backtest"; do not borrow the equity-curve moving-average filter without QMX's own test.

---

## 3. MT5 / MQL5

### 3.1 Standard Library money classes (CHECKED, vendor docs and MetaQuotes sample code)

**The base class.** `CExpertMoney` "is a base class for implementation of money and risk management classes" ([CExpertMoney](https://www.mql5.com/en/docs/standardlibrary/expertclasses/expertbaseclasses/cexpertmoney)). Its methods:

| Method | Job |
|---|---|
| `Percent(double)` | Sets the "risk percent" setting |
| `ValidationSettings()` (virtual) | Checks the settings before use |
| `CheckOpenLong(price, sl)` / `CheckOpenShort(price, sl)` (virtual) | Returns the volume for a new position |
| `CheckReverse(...)` (virtual) | Returns the volume to reverse a position |
| `CheckClose(...)` (virtual) | "Checks conditions to close the opened position"; returns true or false ([CheckClose](https://www.mql5.com/en/docs/standardlibrary/expertclasses/expertbaseclasses/cexpertmoney/cexpertmoneycheckclose)) |

Direct children: `CMoneyFixedLot`, `CMoneyFixedMargin`, `CMoneyFixedRisk`, `CMoneyNone`, `CMoneySizeOptimized` (same page).

- `CMoneySizeOptimized` "implements the market entry algorithm with the lot size depending on results of the previous deals", with one setting, `DecreaseFactor`. The page does not give the formula ([CMoneySizeOptimized](https://www.mql5.com/en/docs/standardlibrary/expertclasses/samplemmclasses/cmoneysizeoptimized)). CHECKED by absence.
- The formula in MetaQuotes' Moving Average sample EA, as reproduced in an article: start from `free margin × MaximumRisk / margin per lot`, count consecutive losing deals for this symbol and magic number, and if losses > 1, `lot = lot - lot*losses/DecreaseFactor` (default `DecreaseFactor = 3`) (`...\md\13426.md:398-462`, [article 13426](https://www.mql5.com/en/articles/13426)). CHECKED. INFERRED: with the default 3, two losses in a row cut size by two thirds and three losses cut it to zero.

**The Wizard header is a schema.** A Wizard module carries a comment block the Wizard reads to build its form:

```
// wizard description start
//| Title=Trading with the optimal f coefficient |
//| Type=Money                                   |
//| Name=FixedPart                               |
//| Class=CMoneyFactor                           |
//| Parameter=Factor,double,0.1,Optimum fixed share |
//| Parameter=MaxLoss,double,50,Maximum loss in points |
// wizard description end
```

Source: `...\md\4162.md:714-725` ([article 4162](https://www.mql5.com/en/articles/4162)). Signal modules use the same block with `Type=SignalAdvanced` and a `ShortName` (`...\md\11487.md:164-178`). CHECKED. Each `Parameter=` line is name, type, default and label. INFERRED: a one-line-per-setting schema in a comment is the cheapest way MT5 lets third parties add money modules that the stock UI can show.

### 3.2 Risk-manager articles the earlier work missed (PRACTITIONER, local corpus)

Found by title search of `catalog.jsonl` against the IDs already covered in `03-mql5-articles.md` and `06-mql5-pilot.md`. Read in the local Markdown copies. Evidence in all of them is the author's own backtest or simulation, never live.

| Article | Pattern | Detail and source |
|---|---|---|
| **21720 RiskGate: Centralized Risk Management for Multiple EAs** (2026-05) | **A risk oracle.** EAs only produce signals. Before trading they send symbol, side, stop and strategy id as JSON over localhost TCP to one service, which answers `approved`, `lot` and `reason`. | Core idea and contract `21720.md:54-75`; flow `:77-110`. Example rules: 2 % daily loss, 0.5 % per trade, 2 positions per symbol, 6 trades per day, halve the lot when the same correlation group already holds a position, and "Offline fallback: reject all trades" (`:177-186`). Extensions: per-group risk budget, per-strategy budgets keyed by `strategy_id`, a position registry of who owns what, and "a small rule pipeline: validate; hard account blockers; per-strategy rules; portfolio rules; then compute size" (`:330-356`). It warns the oracle is a single point of failure and is overkill for one strategy per account (`:361-395`). [URL](https://www.mql5.com/en/articles/21720) |
| **24477 Building Your Personal EA (Part 7): Consolidating the Risk Framework** (2026-10) | **Three scopes of risk**, one class each. | "The trade: can I afford this position, and how big?" (`CTradeRisk`); "The basket: can this EA carry it alongside its own other positions?" (`CBasketRisk`); "The account: can the account carry it alongside everything else?" (`CPortfolioRisk`) (`24477.md:77-87`). Each tier has a config struct; an EA calls `SetDefaults()` and then overrides only what it cares about (`:319`). "Where a limit can be switched off, zero is what switches it off" (`:873`). Honest limits: the gate order is kept by the EA, not enforced; defaults protect only an EA that calls `SetDefaults()`; the account tier "validates none of its settings and starts with every limit off" (`:885-892`). A second EA reuses two of the four files unchanged (`:762-790`). [URL](https://www.mql5.com/en/articles/24477) |
| **24237 ML Under Constraint (Part 1): a configurable rule set for prop-firm sizing** (2026-09) | **Facts versus response.** | A frozen, validated dataclass holds every number the firm's rules can vary; one firm is one named instance (`24237.md:89-124`). The strategy's own de-risking curve stays *outside* that rule set, "because its thresholds are not part of PropFirmRuleSet" (`:158-167`, `:279-283`). Tracing every constant found three that "looked like configuration" but no code read (`:271-277`). Takeaway: "Separate the constraint from the response to the constraint" and model a dynamic-vs-fixed daily limit as a boolean, not a number that is zero for one case (`:289-290`). [URL](https://www.mql5.com/en/articles/24237) |
| **24249 ML Under Constraint (Part 2): calibrating size to the remaining drawdown budget** (2026-09) | **A smooth taper, not a cliff.** | "A threshold creates a discontinuity": five small losses take you from full size to zero in one step (`24249.md:55-62`). Instead: `remaining budget × safety factor / stop % → largest affordable bet → sigmoid width w`, so every new position shrinks continuously as the day's budget erodes; below a 2 % floor the size is zero (`:63-104`). The safety factor must come from the strategy's costs; a scalper with many trades may need about 0.60 (`:99`). The 0.98 ceiling and 0.02 floor stay hard-coded because they are numerical guards, not trader choices (`:173-180`). [URL](https://www.mql5.com/en/articles/24249) |
| **15085 Multi-currency EA (Part 14): adaptive volume change in risk manager** (2025-01) | **A risk-manager state machine with a restore state.** | States `OK`, `DAILY_LOSS`, `RESTORE`, `OVERALL_LOSS`, `OVERALL_PROFIT` (`15085.md:120-128`). Each limit picks its basis from an enumeration: money or percent, measured from the base balance, the day's level, the balance high-water mark, or the equity high-water mark (`:130-150`, `:286-302`). Tested: cutting half the positions at part of the limit instead of all, and restoring size only at a better price within a wait window (1440 minutes) (`:579-636`). The author's backtest showed small gains. [URL](https://www.mql5.com/en/articles/15085) |
| **14336 Multi-currency EA (Part 5): variable position sizes** (2024-07) | **Normalise each strategy, then combine.** | A "normalized strategy" is sized so its worst backtest drawdown is 10 % of its "fitted balance" (`14336.md:42-60`). Combining N strategies, the worst case is all hitting their drawdown at once, so each is cut by N; but "the likelihood of such a worst case is very much reduced" for dissimilar strategies, so a `Scale` factor (default 1) is raised back up (`:166-180`). [URL](https://www.mql5.com/en/articles/14336) |
| **18918 Risk Manager for Trading Robots (Part I)** (2026-06) | **Presets plus early warnings.** | Modes `CONSERVATIVE`, `MODERATE`, `AGGRESSIVE`, `CUSTOM`, each filling every setting at once; aggressive is 10 % daily, 20 % overall, 3 % per trade (`18918.md:77-92`). Warnings at 80 % (yellow) and 90 % (orange) of the daily limit before the block (`:157`). [URL](https://www.mql5.com/en/articles/18918) |
| **17249 Risk Management (Part 3): the main class** (2026-01) | **The basis is a declared choice.** | Each limit is money or percent; a percent applies to balance, net profit, free margin or equity; account mode is personal or prop firm (`17249.md:95-150`). [URL](https://www.mql5.com/en/articles/17249) |
| **24147 Money Management in MQL5 (Part 1): Kelly from the strategy's own edge** (2026-10) | **Size from the strategy's own record.** | The class measures win rate and payoff from the symbol's closed deals and returns 0 when the edge is below break-even (`24147.md:93-110`, `:234-241`). Simulation: full Kelly halves the account in 11 % of runs, half Kelly in about 2 %, keeping about 85 % of the growth (`:214-232`). The author's own warning: "your edge is an estimate" (`:234`). [URL](https://www.mql5.com/en/articles/24147) |

Also in the corpus and not read in full here: 16820/16985/17508/17640 (Risk Management Parts 1, 2, 4, 5), 24331 and 24392 (basket risk; portfolio and correlated risk), 22833 (equity protection through governance logic), 21759 (adaptive risk for liquidity strategies), 22175 (swap-aware sizing), 22338/22558/22842/23013/23144 (Wizard custom money modules with ML), 15779 (VaR for a multi-currency portfolio). Titles CHECKED in `catalog.jsonl`.

### 3.3 Ships, swaps, borrow

- **Ships:** five money modules behind one small interface; the Wizard; no account-level risk manager. CHECKED (3.1).
- **Users swap:** any money module, by subclass plus the Wizard header; whole risk managers as include files or a separate service (3.2).
- **[judgment]** Borrow RiskGate's `approved / size / reason` contract with "reject when unreachable", 24477's three scopes, and 24237's split between facts about the venue/account and the unit's own response to them.

---

## 4. n8n: defaults and extensibility side by side

### 4.1 How a node is described (CHECKED, source and docs)

A node type is a description object plus code. The key fields of `INodeTypeDescription` ([interfaces.ts:3215-3226](https://github.com/n8n-io/n8n/blob/master/packages/workflow/src/interfaces.ts#L3215) and the base at [:2913-2931](https://github.com/n8n-io/n8n/blob/master/packages/workflow/src/interfaces.ts#L2913)):

| Field | Meaning |
|---|---|
| `name`, `displayName`, `icon`, `group`, `description`, `subtitle`, `codex` (catalogue categories) | identity and catalogue |
| `version: number \| number[]` (:3216) and `defaultVersion` (:2930) | which versions this file serves |
| `defaults` (:3217) | the canvas name (`color` is deprecated) ([standard parameters](https://docs.n8n.io/integrations/creating-nodes/build/reference/node-base-files/standard-parameters/)) |
| `inputs`, `outputs` | the connectors |
| `credentials?: INodeCredentialDescription[]` (:3226) | which credential types the node accepts, each `{ name, required, displayOptions, testedBy }` (:2845-2852) |
| `properties: INodeProperties[]` (:3225) | the settings form |

Each setting (`INodeProperties`, [:2254-2290](https://github.com/n8n-io/n8n/blob/master/packages/workflow/src/interfaces.ts#L2254)):

- `displayName`, `name`, `type`, `default` (required, :2259), `description`, `hint`, `required`, `placeholder`.
- `typeOptions` (:2258), for numbers `minValue`, `maxValue`, `numberPrecision` (:2100-2104); for option lists `loadOptionsMethod` and `loadOptionsDependsOn` (:2097-2098), which fill the choices at run time from live data.
- `displayOptions` (:2264): `show`/`hide` rules keyed on other settings, plus `@version`, `@feature` and `@tool` keys (:2219-2230).
- `noDataExpression` (:2273): by default a field may hold an expression; this flag forbids it.
- `validateType` (:2284) for type checking at run time.

Setting types include `string`, `number`, `boolean`, `options`, `multiOptions`, `collection`, `fixedCollection`, `json`, `filter`, `resourceLocator`, `resourceMapper` and `notice` ([UI elements](https://docs.n8n.io/integrations/creating-nodes/build/reference/ui-elements/)).

**Credentials are a separate type.** `ICredentialType` has its own `properties`, an `authenticate` rule and a `test` request ([interfaces.ts:438-470](https://github.com/n8n-io/n8n/blob/master/packages/workflow/src/interfaces.ts#L438)). A node only names the credential type; the secret lives elsewhere. CHECKED.

**Expressions.** Any field can hold `{{ ... }}` code that reads data from earlier nodes ([expressions](https://docs.n8n.io/code/expressions/)). INFERRED: a default can be a literal, or an expression that computes it from live data. That is n8n's form of "self-configuring".

### 4.2 Defaults are not copied into saved work (CHECKED, source)

- A saved node (`INode`) holds `type`, `typeVersion` and `parameters` ([interfaces.ts:1813-1832](https://github.com/n8n-io/n8n/blob/master/packages/workflow/src/interfaces.ts#L1813)).
- `getNodeParameters(..., returnDefaults, ...)` "either just returns the none default values or it applies all the default values" ([node-helpers.ts:763-781](https://github.com/n8n-io/n8n/blob/master/packages/workflow/src/node-helpers.ts#L763)). With `returnDefaults` false, defaults are filled in only when absent and left out otherwise (:1005-1009).
- INFERRED: a saved workflow records only what the user changed. If n8n improves a default inside the same version, every node that never touched that setting picks it up.

### 4.3 Versioning (CHECKED, docs and source)

- **Light versioning:** `version` becomes an array (for example `[1, 2]`), and `displayOptions.show['@version']` shows or hides settings per version. Code reads `this.getNode().typeVersion` ([node versioning](https://docs.n8n.io/integrations/creating-nodes/build/reference/node-versioning/)).
- **Full versioning:** a base file lists `defaultVersion` ("usually the latest") and one folder per version (`v1`, `v2`); the base file holds no logic (same page). In code, `VersionedNodeType` keeps a map `nodeVersions`, takes `defaultVersion` or the highest key, and throws `NodeVersionNotFoundError` for an unknown version ([versioned-node-type.ts](https://github.com/n8n-io/n8n/blob/master/packages/workflow/src/versioned-node-type.ts)).
- "A workflow saved with version 1 stays on version 1, even after you publish version 2"; new nodes dragged in get the latest (docs page above).

### 4.4 Custom and community nodes (CHECKED, docs)

- **Two styles.** Declarative (JSON routing, no `execute()`, "start declarative") and programmatic (an `execute()` method; needed for triggers, non-REST calls, external libraries, item-by-item transforms). One package can mix both ([choose a node style](https://docs.n8n.io/integrations/creating-nodes/plan/choose-node-method/)).
- **Community package rules.** The npm name starts `n8n-nodes-` (or `@scope/n8n-nodes-`), the keywords include `n8n-community-node-package`, and nodes and credentials are listed under an `n8n` key in `package.json`. Lint and test locally first ([submit community nodes](https://docs.n8n.io/integrations/creating-nodes/deploy/submit-community-nodes/)).
- **Verified community nodes** have stricter rules: no runtime dependencies, technical and UX guidelines, a README, and from 1 May 2026 publishing through a GitHub Actions workflow with provenance. Review takes up to four weeks. Verified nodes install from the nodes panel (same page).
- **Raw code escape hatch.** The Code node runs JavaScript or Python as a step, once for all items or once per item. On n8n Cloud it cannot import outside npm modules, and it cannot touch the file system or make HTTP calls ([Code node](https://docs.n8n.io/code/code-node/)).

### 4.5 How defaults and extensibility live together (INFERRED from 4.1-4.4)

1. The catalogue ships nodes with complete defaults, so a new workflow runs with no settings touched.
2. The user overrides a field, or computes it with an expression.
3. Only the overrides are saved, with the node's version pinned.
4. New behaviour arrives as a new version; old workflows keep the old one until someone upgrades them.
5. Anything missing is a new node in a package, or a Code node.
6. Secrets are a separate credential type the node only names.

- **[judgment]** Borrow all six as the shape of a QMX risk "template": a typed settings list with defaults, overrides-only storage, a pinned version on every unit, expressions for computed defaults, plug-in risk blocks in packages, and a raw-code block with tight limits.

---

## 5. Pro portfolio risk tools (public material only)

### 5.1 Bloomberg PORT and MAC3

- PORT is the Terminal's portfolio and risk analytics. It forecasts "risk across multiple dimensions using Bloomberg's advanced multi-asset risk models", has "customizable performance attribution", an "integrated optimization framework" for "risk-controlled portfolios", and "four different types of scenario analysis": factor-based, full-valuation, macroeconomic and climate. CHECKED ([PORT page](https://professional.bloomberg.com/products/bloomberg-terminal/portfolio-analytics/)).
- A PORT user brochure (Brazilian pension funds) names "tracking error and stress scenarios" against "all indices" and "risk limits" as what auditors checked. CHECKED (pdftotext of the [brochure PDF](https://data.bloomberglp.com/professional/sites/10/114833043_new-3.pdf), lines 34 and 70 of the extracted text).
- PORT's risk numbers come from MAC3, a multi-asset factor model. Bloomberg describes it for forecasting at several horizons, building optimised portfolios and designing hedges. SNIPPET ([MAC3](https://professional.bloomberg.com/products/risk/mac3/), seen in search results).
- Bloomberg research compares PORT's Monte Carlo VaR (factor volatilities by an exponentially weighted moving average) with historical VaR, and reports risk contribution per allocation. SNIPPET (bloomberg.com pages returned HTTP 403 to the fetch).

**Levels shown:** whole portfolio against a benchmark (tracking error), by risk factor, and by holding or allocation (contribution to risk). INFERRED from the pieces above; the public pages do not show a drill-down screen.

### 5.2 Bloomberg MARS and AIM (where limits live)

- MARS has Market Risk, Credit Risk, XVA, Valuations and Front Office modules. Market Risk monitors "intraday and end-of-day risk"; the suite runs "pre- and post-trade analysis ... including scenario analysis and stress testing". The page does not describe limit monitoring. CHECKED ([MARS](https://professional.bloomberg.com/products/risk/mars/)).
- For the US derivatives rule 18f-4, MARS Market Risk computes the absolute and relative VaR tests, ships VaR backtesting with a configurable horizon, offers historical, asset-class, custom and correlation-based stress tests, and has "explicit limit tests". SNIPPET (Bloomberg press page, 403).
- AIM Compliance runs checks "pre-trade, post-trade and end-of-day", with over 850 pre-coded rule templates and custom rules; a customer case study says guidelines and regulatory limits are encoded as rules, and exceptions go to named approvers. SNIPPET (search summaries of Bloomberg and trade-press pages).

### 5.3 How limits are expressed: the RiskMetrics document (CHECKED, primary)

The 1996 RiskMetrics Technical Document (J.P. Morgan/Reuters, now hosted by MSCI), section 3.1 "Market risk limits", page 33 ([PDF](https://www.msci.com/documents/10199/5915b101-4206-4ba0-aee2-3449d5c7e95a), read with pdftotext):

- Old-style limits were set "in nominal terms" (for example "no more than 100 million USD of Treasuries"), different for every asset class.
- VaR limits give "a common denominator", so "position benchmarks become a function of risk", and "limits become meaningful for management as they represent a reasonable estimate of how much could be lost".
- Because VaR includes diversification, "the risk limit at higher levels can be lower than the sum of risk limits of units reporting to it." Chart 3.1: a business area at $20MM VaR over groups at $10MM, $12MM and $8MM ($30MM in sum), and units below them.
- Section 3.2 checks the risk model by comparing the daily risk estimate with realised daily P&L over time.

INFERRED: this is the professional answer to the operator's M10 question about 10 units. Each unit keeps its own limit. The level above holds a smaller limit than the sum, sized on how often the units lose together. The parent does not divide its limit by 10.

### 5.4 A retail pro tool for comparison: IBKR Risk Navigator (CHECKED)

- The Risk Dashboard shows net liquidation, daily P&L, maintenance and initial margin, VaR, expected shortfall and beta. It also works on a "what-if" portfolio, where values are "calculated on demand" ([Risk Dashboard](https://ibkrguides.com/tws/usersguidebook/priceriskanalytics/risk%20navigator%20dashboard.htm)).
- Risk can be sliced by underlying, industry and country; VaR confidence is 95 %, 99 % or 99.5 %; there is a scenario matrix for price and volatility moves, and a what-if portfolio can be turned into real orders ([Risk Navigator menus](https://ibkrguides.com/traderworkstation/risk-nav-menus.htm)).
- No public page found sets limits in Risk Navigator. CHECKED by absence (the two pages above).

### 5.5 Pod-shop ladders

Already covered: a reported Millennium ladder of about 5 % drawdown → capital halved, about 7.5 % → wound down, from one press source, reference point not public (`tracker/risk-sizing/research/08-old-qmx-testing-and-decay.md:263`). This pass found the same numbers repeated only in secondary sources. Not re-graded.

### 5.6 Borrow

- **[judgment]** Borrow one money unit for every limit at every level, a parent limit set below the sum of its children, three check times (before the trade, after it, end of day), and a daily "estimate versus realised" check of the risk model itself.

---

## 6. Open-source engines with pluggable risk or sizing

### 6.1 NautilusTrader (CHECKED, source and docs, develop branch)

**Risk engine.** Every order on the submit and modify path passes through the `RiskEngine`, in backtest, sandbox and live. Unless `bypass` is set it checks price and quantity precision, positive prices, min and max quantity, expired GTD orders, that `reduce_only` orders do not grow a position, a per-instrument `max_notional_per_order`, cash-account balance impact, submit and modify rate limits, and the trading state. A failed check emits `OrderDenied` with a standard reason code ([execution docs, docs/concepts/execution/index.md:186-210](https://github.com/nautechsystems/nautilus_trader/blob/develop/docs/concepts/execution/index.md)).

- **Trading states:** `ACTIVE` (everything allowed), `REDUCING` (only reduce-only orders that shrink an existing position, plus cancels and queries), `HALTED` (cancels and queries only; even protective stops are denied) (same file, :276-300).
- **Reason codes** are a closed list in `CATEGORY_CONDITION` form, for example `QUANTITY_BELOW_MINIMUM`, `INVALID_MAX_NOTIONAL_PER_ORDER`, `EXPIRE_TIME_IN_PAST`; "only the leading code is canonical" (same file, :401-450).
- **Config:** `RiskEngineConfig { bypass, max_order_submit, max_order_modify, max_notional_per_order, full_position_exit_venues, debug }`, with both rate limits defaulting to 100 per second, and `deny_unknown_fields` so a mistyped setting is refused ([crates/risk/src/engine/config.rs:47-67](https://github.com/nautechsystems/nautilus_trader/blob/develop/crates/risk/src/engine/config.rs#L47)).
- INFERRED: the engine holds no loss limits or drawdown brakes. Those are left to the strategy or to whatever sets the trading state.

**Sizer.** One function, `calculate_fixed_risk_position_size(instrument, entry, stop_loss, equity, risk, commission_rate, exchange_rate, hard_limit, unit_batch_size, units)` ([crates/risk/src/sizing.rs:39-50](https://github.com/nautechsystems/nautilus_trader/blob/develop/crates/risk/src/sizing.rs#L39)):

1. Risk money is `equity × risk`, minus a round-trip commission on it (:132-150).
2. Size is risk money ÷ exchange rate ÷ stop distance in ticks ÷ tick size ÷ contract multiplier (:74-85).
3. It is capped by `hard_limit` (:89), divided across `units` entries (:94), rounded down to `unit_batch_size`, and capped by the instrument's maximum quantity (:107).
4. Bad inputs return an error; a zero stop distance or zero exchange rate returns size 0 (:51-80).

**Ships, swaps, borrow.** Ships one sizer and one pre-trade gate with three states. Users write their own sizing in the strategy and add custom actors and execution algorithms (`04-platform-study.md:375`). **[judgment]** Borrow the three trading states, especially `REDUCING` (may only shrink), the closed list of denial codes, and refusing unknown config keys.

### 6.2 Backtrader sizers (CHECKED, docs)

- A sizer subclasses `bt.Sizer` and overrides `_getsizing(self, comminfo, cash, data, isbuy)`. Only the absolute value of the return is used; 0 means "do nothing". A sizer can read `self.strategy` and `self.broker` ([sizers](https://www.backtrader.com/docu/sizers/sizers/)).
- Settings are a class tuple `params = (('stake', 1),)`, read as `self.p.stake` (same page).
- Set for all strategies with `cerebro.addsizer(...)`, for one with `addsizer_byidx(idx, ...)`, or inside a strategy with `setsizer`. With none set, a strategy uses `SizerFix` with stake 1 (same page).
- Built-ins: `FixedSize(stake=1, tranches=1)`, `FixedReverser(stake=1)`, `PercentSizer(percents=20)`, `AllInSizer(percents=100)`, and integer versions of the last two ([sizers reference](https://www.backtrader.com/docu/sizers-reference/)).
- **[judgment]** Borrow "one default sizer for everything, overridable per strategy", but note Backtrader's sizers see cash, not the stop, so they cannot express risk to the stop without custom code.

### 6.3 Zipline trading controls (CHECKED, docs)

- Controls set once in `initialize`: `set_max_leverage(max_leverage)`, `set_max_order_count(max_count, on_error='fail')`, `set_max_order_size(asset, max_shares, max_notional, on_error='fail')`, `set_max_position_size(asset, max_shares, max_notional, on_error='fail')`, `set_long_only(on_error='fail')`, `set_do_not_order_list(restricted_list, on_error='fail')`. A breach of order or position size raises `TradingControlException` ([API reference](https://zipline.ml4trading.io/api-reference.html)).
- The docs warn that splits, dividends and price improvement can push holdings past a position limit (same page).
- **[judgment]** Borrow the idea that each control declares what happens on breach (`on_error`) rather than one fixed reaction.

### 6.4 freqtrade (CHECKED, docs; protections were covered before)

- `"stake_amount": "unlimited"` splits the balance: `currency_balance / (max_open_trades - current_open_trades)`. `tradable_balance_ratio` (default 0.99, range 0.1-1.0) holds back a reserve. `available_capital` gives one bot a fixed slice of a shared account and is split across its `max_open_trades` ([configuration](https://www.freqtrade.io/en/stable/configuration/)).
- `custom_stake_amount` and the protections (per-pair, per-side and global locks after N stop-losses, drawdown, low profit, cool-down) are in `04-platform-study.md:304-341` and `:551`.
- INFERRED: freqtrade's default is the "split" rule the operator objected to, and the protections are count brakes. The lead's own scratch sim says count brakes fire on healthy units more often as trade count rises (`tracker/risk-core/STATE.md`, item 10).
- **[judgment]** Borrow the reserve ratio and the per-bot capital slice; treat count-based locks with care for high-frequency units.

### 6.5 Hummingbot V2 executors (CHECKED, docs)

- A position executor carries a "triple barrier": `stop_loss`, `take_profit`, `time_limit`, plus `trailing_stop_activation_price_delta` and `trailing_stop_trailing_delta`. "Whichever one the price reaches first ends the trade." Default order types: limit to open, market for the exits ([position executor](https://hummingbot.org/strategies/v2-strategies/executors/positionexecutor/)).
- Controllers emit actions that create or stop executors; several controllers can run in one bot ([controllers](https://hummingbot.org/strategies/v2-strategies/controllers/)).
- **[judgment]** Borrow the per-trade exit bundle as one declared object attached to each position, separate from account-level brakes.

---

## 7. Pointers for the operator's M10 questions (INFERRED, not designs)

| His question (M10) | What the platforms show |
|---|---|
| "1 unit will get $20 and then 10 different units each will get $2, does that make sense?" | Both rules exist and are swappable: 1/N (LEAN equal weighting, freqtrade unlimited stake) and "own size, capped in total" (LEAN insight weighting). Pros set the parent limit below the sum of children, sized on joint losses (RiskMetrics 3.1). Bykov normalises each strategy, divides by N, then scales back up for diversity (14336). Sections 1.3, 5.3, 3.2, 6.4. |
| "If you say 10 %, where does it come from? What if I want to change the way it is derived?" | Shipped tools ship numbers as presets (18918), named instances (24237) or defaults on a schema (n8n, SQ, MT5 Wizard), and let a field be computed (n8n expressions). The basis (balance, equity, high-water mark, day's level) is itself a declared choice (15085, 17249). Sections 3.2, 4.1. |
| Circuit breaker that sizes down slowly rather than pulling out on a bad day | Built-ins are cliffs (LEAN 5 % liquidate and re-arm). Graded options exist: partial cut then restore (15085), a reduce-only state (Nautilus), a smooth taper to the remaining budget (24249), early warnings (18918). SQ's own equity-curve filter test found no gain. Sections 1.4, 2.3, 3.2, 6.1. |
| How agents and outside code reach the risk part | Every platform's door is a small typed contract: a class with one method (LEAN, MT5, SQ, Backtrader) or a JSON request and reply with a reason (RiskGate), plus a schema that builds the form. n8n adds packaging, version pinning and a sandboxed code node. Sections 1.1, 3.2, 4. |

---

## 8. Patterns that recur across platforms

1. **The sizer is a small function.** Inputs: money available, entry, stop, instrument facts, sometimes the strategy's own record. Output: a size, where 0 means skip. MT5 `CheckOpenLong(price, sl)`, SQ `computeTradeSize`, Backtrader `_getsizing`, Nautilus `calculate_fixed_risk_position_size`, freqtrade `custom_stake_amount`, RiskGate's `lot`.
2. **Risk is a later stage that mostly shrinks or blocks.** LEAN risk models adjust targets, Nautilus denies, Zipline raises, RiskGate rejects. Growing a position is rare and always custom (SQ's doubling variant, LEAN's accumulative model).
3. **Decisions carry a reason.** Nautilus has a closed list of denial codes, RiskGate returns `reason`, freqtrade locks store theirs. The reason is how a person later sees why a trade did not happen.
4. **Scopes nest: trade, then strategy or basket, then account, then firm.** 24477 makes it three classes. RiskGate adds per-strategy budgets inside the account. RiskMetrics sets each parent limit below the sum of its children.
5. **Two capital-sharing rules recur, and tools let you pick:** split one budget by N (LEAN equal weighting, freqtrade unlimited stake), or give each its own size and cap only the total (LEAN insight weighting, RiskMetrics hierarchy, Bykov's Scale).
6. **Settings carry a schema next to the code.** Name, type, default, min, max, step, group, label: n8n `properties`, SQ `@Parameter`, the MT5 Wizard header, Backtrader `params`, Nautilus config with `deny_unknown_fields`. The settings form is generated from it.
7. **Defaults ship complete, and users override only what they change.** n8n stores non-default values only; 24477 calls `SetDefaults()` then overrides; 18918 and 24237 ship named presets.
8. **Facts are kept apart from responses.** The venue's or account's rules (24237's rule set, Nautilus instrument limits) are separate from the strategy's choice of how to react (de-risking curve, taper). Facts should be measured, not typed (24237's commission note).
9. **Extension is "subclass and override one method", with a raw-code escape hatch.** LEAN `ManageRisk`, MT5 `CExpertMoney`, SQ `MoneyManagementMethod`, RiskGate `OnSignal`, Backtrader `_getsizing`; n8n's Code node and SQ's external-script task are the hatches.
10. **Only n8n versions its building blocks properly.** Saved work pins the version it was built with; new versions sit beside old ones. None of the trading platforms studied versions a risk or sizing module this way.
11. **Built-in brakes are cliffs; graded brakes are custom.** Fixed-percent liquidation, immediate re-arm, count locks. Partial cuts, restore states, reduce-only mode, smooth tapers and early warnings come from Nautilus and from community articles.
12. **The basis of every limit is a declared choice.** Money or percent; of balance, equity, free margin, the day's level, or a high-water mark (15085, 17249; LEAN's trailing flag).
13. **What to do when the risk layer is down is decided up front, and the answers differ.** RiskGate rejects all trades; Nautilus denies when the account cannot be resolved; freqtrade falls back to the proposed stake when the callback fails (`20-self-configuring-systems.md:22`).
14. **Cheap re-sizing on recorded trades comes before expensive re-testing.** QuantAnalyzer's money-management simulator, equity control and What-If all work on a finished trade list; the MQL5 Monte Carlo articles shuffle recorded trades.
15. **No product self-tunes its risk numbers from live results under guardrails.** "Self-configuring" in shipped tools means presets plus numbers computed from live state. Learning from the record appears only as a sample formula (`DecreaseFactor`), an article class (24147 Kelly), or a vendor test with a null result (SQ equity control). This is open ground, and also untested ground.
