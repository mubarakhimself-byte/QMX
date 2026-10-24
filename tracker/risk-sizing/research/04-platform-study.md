---
ticket: platform-study
title: How MT5, cTrader, NinjaTrader, LEAN, Jesse, freqtrade and NautilusTrader organise strategy building
date: 2026-10-24
author: opus research agent (read-only; this file is the only write)
method: live official docs and reference pages fetched fresh with Exa and the built-in browser on 2026-10-24 (no Firecrawl). QMX docs and code read on `plan/agent-system` (`D:\QMX-worktrees\agent-system`) and `main` docs only to name the blast radius. Complements 03-strategyquant.md (testing funnel, robustness, QuantAnalyzer, Q AI); does not repeat it.
labels: CHECKED = seen on a live official page or in QMX code (URL or path given). INFERRED = my reasoning, not a source.
numbers: every number here is a starting point and must be configurable (UI-editable), never a baked default.
---

# 04: How the big platforms organise strategy building, and what QML should take

## 0. The short version

1. **All seven platforms converged on the same contract.** One strategy class. Declared settings with ranges. Data needs declared at start-up. Lifecycle callbacks. Orders or intents as output. The same code in backtest and live. QML's shipped protocol (a factory built from declaration + assignment + read surfaces, driven per evaluation instant, returning intents) already has this shape. CHECKED (`qml/src/qml/protocol/factory.py:1-7`). The gap is ergonomics and the block catalogue, not architecture. INFERRED.
2. **The best "exits belong to the strategy" designs already exist: Jesse and freqtrade.**
   - Jesse splits *whether* (`should_long`), *how* (`go_long` sets entry, stop and take-profit lists), *manage* (`update_position`) and *cancel* (`should_cancel_entry`). CHECKED (https://docs.jesse.trade/docs/strategies/entering-and-exiting).
   - freqtrade separates signals (`populate_entry_trend`/`populate_exit_trend`) from per-trade callbacks: `custom_stoploss`, `custom_exit`, `custom_roi`, `custom_stake_amount`, `confirm_trade_entry`, `adjust_trade_position`. CHECKED (https://www.freqtrade.io/en/stable/strategy-callbacks/).
   - Copy that split. Sizing stays outside the bot, in the unit (freqtrade's `custom_stake_amount` becomes the unit sizer). INFERRED.
3. **MT5's Wizard is the clearest block catalogue in the industry, and it already does "signal strength".**
   - Each signal module returns a strength of 0–100, weighted 0–1, and the strengths are averaged into a vote from −100 to +100. `ThresholdOpen` and `ThresholdClose` decide. Up to 64 "advisor" signals, each on its own symbol and timeframe.
   - The Wizard has three module families: Signal, Trailing and Money.
   - CHECKED (https://www.mql5.com/en/docs/standardlibrary/expertclasses/csignal ; https://www.mql5.com/en/articles/275).
   - This is the operator's "signal strength → size" and "pillars" idea, shipped since 2011. INFERRED.
4. **LEAN's own docs say its Algorithm Framework fits rebalancing and multi-factor strategies, and fits technical entries with coupled exits poorly.** That is QMX's scalper book. CHECKED (https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/overview, "Strategy Styles").
   - Copy LEAN's *separation*: universe → alpha → portfolio → risk → execution, where "the models should not communicate".
   - Do not force the five-model pipeline *inside* a bot. INFERRED.
5. **freqtrade's two analysis commands are the cheapest large win for QML.**
   - `lookahead-analysis` "chains backtests and pokes at the strategy" to catch use of future data.
   - `recursive-analysis` catches indicators whose values depend on how much history was loaded.
   - CHECKED (https://www.freqtrade.io/en/stable/lookahead-analysis/).
   - Agents write vectorised pandas fastest, and look-ahead is their most common bug. Make both checks part of QML conformance. INFERRED.
6. **Every tester documents that bar-only backtests lie for tight exits.**
   - MT5 warns that "1 minute OHLC" mode makes a "Testing Grail" possible. CHECKED (https://www.mql5.com/en/docs/runtime/testing).
   - NinjaTrader: "During backtest, strategies can ONLY be processed at the close of each bar". CHECKED (https://ninjatrader.com/support/helpguides/nt8/discrepancies_real-time_vs_bac.htm).
   - Nautilus: the adaptive OHLC path is "a deterministic heuristic, not a reconstruction". CHECKED (https://nautilustrader.io/docs/latest/concepts/backtesting/bar-execution/).
   - For scalpers QMX needs quote or tick data and a named fidelity ladder. INFERRED.
7. **No platform counts tries or deflates results, but LEAN deliberately caps cloud optimisation at three parameters, partly "to reduce overfitting".** CHECKED (https://www.quantconnect.com/docs/v2/cloud-platform/optimization/parameters). Same gap as SQ (03 §5). QMX's tries ledger stays the differentiator. INFERRED.
8. **MT5 already ships "domain expansion" as an optimisation mode.**
   - "All Symbols Selected in Market Watch" runs the same inputs across every selected symbol. CHECKED (https://www.metatrader5.com/en/terminal/help/algotrading/optimization_types).
   - The cTrader CLI can sweep the main timeframe as a parameter. CHECKED (https://help.ctrader.com/ctrader-cli/optimisation/).
   - Each is a grid of tries, and neither counts them. INFERRED.
9. **The agent door has a strong 2026 reference: QuantConnect's MCP server.**
   - `create_file` and `edit_file` compile and return the errors.
   - `check_initialization_errors` runs a backtest for a few seconds to catch start-up failures.
   - `read_project_templates` returns starter code.
   - `create_backtest` is asynchronous and pushes the result back ("Do not poll").
   - `estimate_optimization_time` gives a cost estimate before a sweep.
   - CHECKED (https://www.quantconnect.com/docs/v2/ai-assistance/mcp-server/key-concepts ; https://github.com/QuantConnect/mcp-server).
   - QMX agents today get a refusal from `research.qml_run`. CHECKED (via 01-ground-truth §1.2).
10. **"Any instrument" is mostly an instrument-spec job, and QMX's spec is thin.**
    - QMX's instrument identity is venue + symbol, with everything else in dated key/value records. CHECKED (`packages/qmf-core/src/qmf/core/identity.py:269-279, 409-422`).
    - Nautilus has a typed taxonomy: spot, CFD, future, perp/swap, options, binary, synthetic. CHECKED (https://nautilustrader.io/docs/latest/concepts/instruments/).
    - MT5 has the richest CFD fields: swap per weekday, triple-swap day, stops and freeze levels, filling modes, separate quote and trade sessions. CHECKED (https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants).
    - NinjaTrader has trading-hours templates with holidays, plus futures rollover with offsets and a merge policy. CHECKED (https://ninjatrader.com/support/helpGuides/nt8/editing_instruments.htm).
    - Copy these fields into a typed QMF instrument spec. INFERRED.

---

## How to read this

- Paths are on `plan/agent-system` (`D:\QMX-worktrees\agent-system`) unless they start with `docs/` (`C:\Users\Mubarak\Desktop\QMX\docs\`).
- "Blast radius" names the existing QMX part a proposal touches, per the scope rule. Shipped backend work is extended, never casually removed.
- **Lever** is the compounding-test lever a proposal serves: E = edge per trade, N = trade count, S = right size, D = less drag, P = proof for the Judge step.
- The section 1 subheads repeat for every platform:
  - **Contract**: what a strategy is and its lifecycle.
  - **Data**: indicators, data access, multi-timeframe and multi-symbol.
  - **Instruments**: the symbol model.
  - **Orders**: orders and positions.
  - **Testing**: testing and optimisation.
  - **Extend**: how users extend the platform.

---

## 1. Per platform

### 1.1 MetaTrader 5 / MQL5

**Contract.**
- An Expert Advisor (EA) is a program with fixed-signature event handlers: `OnInit`, `OnDeinit`, `OnTick` (new quote), `OnTimer`, `OnTrade`, `OnTradeTransaction`, `OnBookEvent` (depth change), `OnChartEvent`, plus tester hooks (`OnTester`, `OnTesterInit`, `OnTesterPass`, `OnTesterDeinit`). CHECKED (https://www.mql5.com/en/docs/event_handlers).
- Events queue per program. A new `NewTick` is *dropped* while one is still queued or being handled. CHECKED (same page).
  - INFERRED: an EA can miss ticks in fast markets, and the tester's generated ticks never reproduce that drop. This is one live-vs-test gap a scalper meets.
- Inputs (`input` variables) are the settings the optimiser varies. CHECKED (example code on the bufferdirection page).

**Data.**
- Indicators are **handles**: create once in `OnInit` (`iMA(...)` returns a handle), then copy values with `CopyBuffer(handle, buffer, start, count, array)` on each tick. CHECKED (https://www.mql5.com/en/docs/series/bufferdirection).
- Any symbol and timeframe can be requested the same way: `CopyRates`, `CopyClose` and `CopySpread` (the spread history). CHECKED (same page).
- Timeseries index 0 is the *current, unfinished* bar. CHECKED (same page). INFERRED: the classic MQL5 look-ahead trap, because a bot that reads `[0]` reads a forming bar.
- Custom indicators implement `OnCalculate` and expose buffers. CHECKED (same page).
- ML: ONNX models run inside an EA (`OnnxCreate`, `OnnxRun`, optional GPU) and can be tested in the Strategy Tester. CHECKED (https://www.mql5.com/en/docs/onnx).

**Instruments.**
- `SymbolInfoInteger/Double/String` expose about a hundred properties. CHECKED (https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants). The QMX-relevant ones:
  - contract calc mode (`SYMBOL_TRADE_CALC_MODE`)
  - tick size, plus a tick value that differs for profit and for loss
  - contract size; min, max and step volume; volume limit per direction
  - swap long/short, swap mode, a swap ratio per weekday, triple-swap day
  - stops level and freeze level (minimum distances for stops)
  - allowed filling, expiration and order modes
  - initial, maintenance and hedged margin
  - sector and industry; base, profit and margin currencies
  - expiry for futures; option strike, right and Greeks
  - a formula for synthetic symbols
- Custom symbols can be created with their own spec, quote sessions and separate trade sessions. They import M1 bars or ticks (bid/ask/last) and can be synthetic formulas (e.g. a euro index as a weighted product of pairs). EAs cannot trade outside session hours in the tester. CHECKED (https://www.metatrader5.com/en/terminal/help/trading_advanced/custom_instruments).

**Orders.**
- Three nouns: **order** (instruction), **deal** (execution), **position** (holding). Each has a ticket, and deals carry the position ticket. CHECKED (https://www.metatrader5.com/en/terminal/help/trading/general_concept).
- The broker sets the account to **netting** (one position per symbol) or **hedging** (many, including opposite). The choice changes stop-loss/take-profit inheritance, closing and margin. CHECKED (same page).
- The standard library wraps trading in `CTrade` (not re-fetched today; INFERRED from the Wizard modules page structure).

**Testing.**
- Tick modes:
  - "Every tick" (generated from M1)
  - "Every tick based on real ticks" (the broker's recorded ticks)
  - "1 minute OHLC"
  - "Open prices only"
  - "Math calculations" (no market data; only `OnInit`, `OnTester` and `OnDeinit` run)
  - CHECKED (https://www.metatrader5.com/en/terminal/help/algotrading/testing).
- Execution delay can be zero, random (0–8 s with 90 % probability, 9–18 s with 10 %) or fixed (a measured ping). Requotes are simulated. CHECKED (same page).
- **Forward period**: the date range splits into back and forward parts (½, ⅓, ¼ or a custom date). Optimised sets are re-checked on the forward part. CHECKED (same page).
- Multi-currency: the tester loads every symbol the EA touches. CHECKED (same page).
- Optimisation (https://www.metatrader5.com/en/terminal/help/algotrading/optimization_types, CHECKED):
  - "slow complete" (full grid) or a "fast genetic" algorithm (population 64–256; 15–31 generations plus convergence generations)
  - resumable from a `.gen` cache
  - criteria: balance, PF, expected payoff, DD, recovery, Sharpe, **Custom** (= the `OnTester()` return value), or a "Complex Criterion"
  - mode **"All Symbols Selected in Market Watch"**: same inputs, one pass per symbol
- Agents: local, remote, and the paid MQL5 Cloud Network (4 GB RAM and disk limits per agent). Frames (`OnTesterPass`) send per-pass data back without writing files. CHECKED (https://www.mql5.com/en/docs/runtime/testing).

**Extend.**
- The **MQL5 Wizard** builds an EA from three module families. CHECKED (https://www.mql5.com/en/docs/standardlibrary/expertclasses ; https://www.mql5.com/en/articles/275).
  - Signal: 20 shipped (AC, AMA, AO, CCI, MACD, MA, SAR, RSI, Stoch, TEMA, ... plus `CSignalITF`, "filtration of signals by time").
  - Trailing: `CTrailingFixedPips`, `CTrailingMA`, `CTrailingPSAR`, `CTrailingNone`.
  - Money: `CMoneyFixedLot`, `CMoneyFixedMargin`, `CMoneyFixedRisk`, `CMoneyNone`, `CMoneySizeOptimized` (size from previous deals).
- The vote (CHECKED, csignal page):
  - each module's market patterns have significance 1–100; the strongest pattern gives a forecast of −100…+100
  - modules enter a vote with weight 0–1; the result is the arithmetic mean of weighted forecasts
  - `ThresholdOpen` and `ThresholdClose` (0–100) trigger trades
  - worked example: MA (weight 0.4, pattern 100) and Stoch (weight 0.8, pattern −80) give (40 − 64)/2 = −12, below the open threshold of 20, so no trade
- Base class `CExpertSignal`: `LongCondition()` returns 0–100, plus `CheckOpenLong`, `CheckCloseLong`, `CheckReverseLong`, `AddFilter`, `Weight`, `Invert`, `Ignore`, `PriceLevel`/`StopLevel`/`TakeLevel`/`Expiration`. Signals nest: an "advisor" is itself a signal, up to 64. CHECKED (https://www.mql5.com/en/docs/standardlibrary/expertclasses/expertbaseclasses/cexpertsignal).
- **Python** (`pip install MetaTrader5`) reads data, account, positions and history, and sends orders through a running terminal. Its function list has no strategy-tester call. CHECKED (https://www.mql5.com/en/docs/python_metatrader5). INFERRED: Python is a data and execution bridge, not a way to author testable EAs.

### 1.2 cTrader / cTrader Algo (C# and Python)

**Contract.**
- A cBot subclasses `Robot` (C#) or is a Python class driven through an `api` object. Hooks:
  - C#: `OnStart`, `OnTick`, `OnBar` (new bar opened), `OnBarClosed` (called for the bar that just closed), `OnError`, `OnException`, `OnStop`
  - Python: `on_start`, `on_tick`, `on_bar_closed`, `on_stop`
  - CHECKED (https://help.ctrader.com/ctrader-algo/references/General/Robot/ ; https://help.ctrader.com/ctrader-algo/how-tos/cbots/create-a-cbot-in-5-mins/).
- Inside `OnBarClosed`, the `Bars` collection excludes the live bar. Bar events work on time, tick, Renko, range and Heikin Ashi charts. CHECKED (https://help.ctrader.com/ctrader-algo/documentation/cbots/cbot-bar-events/).
- Settings are `[Parameter]` properties (C#) or a `config.json` parameter list (Python). `AccessRights` declares the sandbox level. CHECKED (Robot page; https://help.ctrader.com/ctrader-algo/faq/).
- `GetFitness()` can be overridden to give a custom optimisation score. CHECKED (Robot page).

**Data.**
- `MarketData.GetBars(timeframe, symbol)`, `GetTicks(symbol)` and `GetMarketDepth(symbol)` give any symbol, timeframe, ticks or depth. CHECKED (https://help.ctrader.com/ctrader-algo/references/MarketData/MarketData/).
- Indicators: `Indicators.SimpleMovingAverage(Bars.ClosePrices, 20)` and so on. Created in `OnStart`. CHECKED (OnStart reference).

**Instruments.**
- `Symbol` is documented as "Represents a currency pair". Fields: `PipSize`, `PipValue`, `TickSize`, `TickValue`, `LotSize`, `VolumeInUnitsMin/Max/Step`, `Bid`/`Ask`/`Spread`, `MarketHours` (`IsOpened`, `TimeTillOpen`/`Close`). CHECKED (https://help.ctrader.com/ctrader-algo/references/MarketData/Symbols/Symbol/).
- INFERRED: an FX-shaped model (units, lots, pips) stretched over indices and crypto CFDs. cBots that trade several symbols must read min volume, step and pip value from each `Symbol`. CHECKED (https://help.ctrader.com/ctrader-algo/documentation/cbots/cbot-advanced-operations/).

**Orders.**
- `ExecuteMarketOrder`, `PlaceLimitOrder`, `PlaceStopOrder` and `PlaceStopLimitOrder` (each with an async variant), `ModifyPosition`, `ReversePosition`, `ClosePosition`, `ExecuteMarketRangeOrder`. Positions are found by label (e.g. `Positions.Find("SampleBot", SymbolName)`). CHECKED (Robot page). INFERRED: labels play the role of MT5 magic numbers and NinjaTrader signal names.

**Testing.**
- Backtest data choices: tick data from server, M1 bars from server, M1 bars from CSV, H1 bars from server. Spread fixed or random within a min–max range. Commission per million units. Starting capital in USD. CHECKED (https://help.ctrader.com/ctrader-algo/how-tos/cbots/backtest-a-cbot/).
- Optimisation:
  - Grid or Genetic (genetic recommended)
  - several min/max criteria at once (net profit, PF, equity/balance DD, win/loss counts, trade count, average trade) or `GetFitness`
  - "Autoselect the best pass"
  - CHECKED (https://help.ctrader.com/ctrader-algo/how-tos/cbots/optimise-a-trading-bot/).
- **cTrader CLI** runs `backtest` and `optimize` from a terminal with a JSON parameter file. `--method genetic|grid`, `--cores`, `--criteria "NetProfit:max,MaxEquityDrawdownPercentages:min"` or `--fitness`, data modes `open | m1 | m1-csv | tick-csv | ticks`, and **`--timeframe` sweeps the main timeframe**. CHECKED (https://help.ctrader.com/ctrader-cli/optimisation/).
- Since 5.9, plugins can start optimisations through `OptimizationSettings` (data mode, method, cores, `PreciseConversion` for real cross rates). CHECKED (https://help.ctrader.com/ctrader-algo/references/Plugin/Optimization/OptimizationSettings/).
- **Custom backtesting data sources**: a plugin registers a source and supplies ticks or bars on request, including custom symbols and periods, for the backtester, the optimiser and Market Replay. CHECKED (https://help.ctrader.com/ctrader-algo/guides/backtesting-custom-data-sources/).

**Extend.**
- Python is native (via pythonnet: `import clr; clr.AddReference("cAlgo.API")`). CHECKED (https://help.ctrader.com/ctrader-algo/documentation/python-basics/).
- Third-party packages come from a `requirements.txt` at the project root and resolve at build, but "work only when running locally or on a VPS, and are not supported in the cloud". CHECKED (https://help.ctrader.com/ctrader-algo/documentation/third-party-python-packages/).
- C# can use NuGet and DLLs. CHECKED (https://help.ctrader.com/ctrader-algo/how-tos/all-algos/reference-third-party-libraries/).
- Spotware's own blog says Python bots run "in a secure sandbox, with safe file storage and HTTP available even in backtests". CHECKED (https://blog.ctrader.com/python-opens-new-earning-opportunities-in-ctrader-store/). INFERRED: the opposite of QML's denial set. cTrader trusts the author; QMX denies the clock and I/O to keep determinism.

### 1.3 NinjaTrader 8 / NinjaScript

**Contract.**
- Everything runs through `OnStateChange()` and a `State` enum. CHECKED (https://ninjatrader.com/support/helpguides/nt8/onstatechange.htm):
  - `SetDefaults`: defaults shown in the UI. It is called for *every* script whenever a list UI opens.
  - `Configure`: called once. Add data series here.
  - `Active`
  - `DataLoaded`: create indicators and series here.
  - `Historical`
  - `Transition`: history finished, real-time not started.
  - `Realtime`
  - `Terminated`
- Logic lives in `OnBarUpdate()`. `Calculate` = `OnBarClose | OnEachTick | OnPriceChange`. CHECKED (same page, example).
- NinjaTrader creates several *UI clone* instances besides the one that runs, so `SetDefaults` must stay lean. CHECKED (https://ninjatrader.com/support/helpguides/nt8/understanding_the_lifecycle_of.htm).
- `Historical` is called again per optimisation pass when `IsInstantiatedOnEachOptimizationIteration` is true (the default). CHECKED (onstatechange page). INFERRED: a fresh instance per trial, which is the determinism guarantee.

**Data.**
- `AddDataSeries("AAPL", BarsPeriodType.Minute, 1)` adds extra Bars objects. They must be added in `Configure` and **hard-coded, never from runtime variables**. Every series calls `OnBarUpdate`, and `BarsInProgress` says which one. CHECKED (https://ninjatrader.com/support/helpguides/nt8/multi-time_frame__instruments.htm).
- On shared timestamps the primary series processes first. Historical order "is NOT guaranteed to be the same sequence that these events occurred in real-time" unless Tick Replay is on. CHECKED (same page).

**Instruments.**
- `MasterInstrument`: `InstrumentType`, `TickSize`, `PointValue`, `Currency`, `Exchanges`, `RolloverCollection`, `MergePolicy`, `Dividends`, `Splits`, `RoundToTickSize()`. CHECKED (https://ninjatrader.com/support/helpguides/nt8/masterinstrument.htm).
- Futures rollover uses dated offsets, downloaded or computed locally. Merge policy is `MergeBackAdjusted | MergeNonBackAdjusted | DoNotMerge`. CHECKED (https://ninjatrader.com/support/helpguides/nt8/merge_policy.htm ; editing_instruments page).
- Trading Hours templates hold several sessions per day and holidays (early close, late open, full day), pushed from NinjaTrader servers. CHECKED (NT8 help guide PDF, "New Trading Hours").

**Orders.** Two tiers that cannot be mixed in one strategy:
- **Managed**. CHECKED (https://ninjatrader.com/support/helpguides/nt8/managed_approach.htm):
  - `EnterLong/Short(...)` with **signal names** that tie exits to entries
  - `SetStopLoss`, `SetProfitTarget`, `SetTrailStop` and `SetParabolicStop` submit automatically on fill and are OCO-linked
  - `EntriesPerDirection` and `EntryHandling` limit stacking
  - entry methods auto-reverse
  - unfilled orders cancel at bar end unless re-submitted
- **Unmanaged** (`IsUnmanaged = true`): `SubmitOrderUnmanaged`, `ChangeOrder`, `CancelOrder`, no signal tracking. The strategy owns overfills, rejections and connection-loss recovery. CHECKED (https://ninjatrader.com/support/helpguides/nt8/unmanaged_approach.htm).
- **ATM strategies** (template-based brackets) can be launched from NinjaScript, but "operate in real-time only ... can't be backtested", and their fills do not count in the strategy's P&L. CHECKED (https://ninjatrader.com/support/helpGuides/nt8/using_atm_strategies.htm).

**Testing.**
- The Strategy Analyzer offers backtest, optimise, walk-forward, multi-objective, basket testing over instrument lists, Monte Carlo, and a "Discrepancies: Real-Time vs Backtest" page. CHECKED (https://ninjatrader.com/support/helpguides/nt8/strategy_analyzer.htm).
- Fill engine. CHECKED (https://ninjatrader.com/support/helpguides/nt8/understanding_historical_fill_.htm):
  - "Standard" splits each bar into 3 virtual bars, ordered by whether the open is nearer the high or the low.
  - "High" uses a finer secondary series to fill.
  - Slippage in ticks applies to market and stop orders only.
  - High resolution cannot be used with multi-timeframe or multi-instrument strategies, or with Tick Replay.
- Walk-forward: optimisation days (in-sample) then test days (out-of-sample), rolled forward. Optimiser "Default" or "Genetic" or custom NinjaScript. More than 10 fitness choices, also custom. "Optimize data series" can sweep the bar period. CHECKED (https://ninjatrader.com/support/helpguides/nt8/walk_forward_optimize_a_strate.htm).

**Extend.**
- Every piece is a NinjaScript type with its own lifecycle: Indicators, Strategies, BarTypes, ChartStyles, **OptimizationFitnesses**, **Optimizers**, **PerformanceMetrics**, ImportTypes, Market Analyzer columns, AddOns. CHECKED (onstatechange page, type table).
- The **Strategy Builder** is no-code: a Condition Builder over indicators, price and time; Condition Groups (all/any); time filters; user inputs. It shows the generated NinjaScript live. CHECKED (https://ninjatrader.com/support/helpguides/nt8/strategy_builder.htm ; https://static.ninjatrader.com/support/helpGuides/nt8/strategybuilder_condition_builder.htm).

### 1.4 QuantConnect LEAN

**Contract.**
- `QCAlgorithm` with `initialize()` and `on_data(slice)` (the "classic" design), or the **Algorithm Framework** built into the same class. CHECKED (https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/overview):
  - Universe Selection model → assets
  - Alpha model(s) → `Insight` objects
  - Portfolio Construction model → `PortfolioTarget` objects
  - Risk Management model(s) → adjusted targets
  - Execution model → orders
  - "The models should not communicate"
  - If logic must pass information between components, "use the classic design"
- **Fit warning** (same page): the framework "works best for portfolio rebalancing, ranking, and multi-factor style strategies". "Technical entry signals are often tightly coupled with their exit criteria", so they fit poorly. With one signal, equal weighting puts 100 % into one asset and churns when a second signal arrives.
- An `Insight` carries symbol, **period (expiry)**, type, **direction**, **magnitude**, **confidence**, source model, **weight** and tag. Multiple alpha models are combined by the portfolio model. Alpha models get `on_securities_changed` when the universe adds or removes assets. CHECKED (https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/alpha/key-concepts).
- Shipped risk models: `MaximumDrawdownPercentPerSecurity` (default 5 %), `MaximumDrawdownPercentPortfolio` (optional trailing), `MaximumUnrealizedProfitPercentPerSecurity`, `MaximumSectorExposure`, trailing stop and others. CHECKED (https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/risk-management/supported-models).
- Shipped portfolio models: equal, confidence-weighted, insight-weighted, and more, each with a rebalance frequency. CHECKED (https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/portfolio-construction/supported-models).

**Data.**
- Subscriptions are set in `initialize` with a resolution (tick, second, minute, hour, daily).
- **Consolidators** build any bar from smaller ones: time period, calendar, count, mixed, Renko. Each keeps a rolling window. FX and CFD consolidate quote bars, others trade bars. CHECKED (https://www.quantconnect.com/docs/v2/writing-algorithms/consolidating-data/getting-started).
- `settings.automatic_indicator_warm_up` warms indicators from history. CHECKED (walk-forward page example).

**Instruments.**
- A `Security` is keyed by a `Symbol` and holds: `symbol_properties` (lot size, minimum price variation), `exchange.hours` (regular and extended), holdings, fundamentals, leverage and margin model. CHECKED (https://www.quantconnect.com/docs/v2/writing-algorithms/securities/key-concepts).
- Indices, canonical options and continuous futures are not tradable. CHECKED (same page).

**Orders.**
- **Reality models are per security**: fill, slippage, fee, brokerage, buying power, settlement, short availability, option models, margin interest, dividend yield. Portfolio-level: margin call and risk-free rate. They are set via a security initializer. CHECKED (https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/key-concepts).
- Default models assume liquid assets. CHECKED (same page).

**Testing.**
- Cloud optimisation: grid only, **at most 3 parameters**. Reasons given: grid inefficiency, 3-D charts, and "it increases the likelihood of overfitting". More parameters need the local CLI. Constraints, targets and estimated cost come before launch. CHECKED (https://www.quantconnect.com/docs/v2/cloud-platform/optimization/parameters ; .../getting-started).
- **Walk-forward is in-algorithm**: `self.train(date_rules, time_rules, fn)` re-optimises on a schedule over a trailing window, using a vectorised objective on history. CHECKED (https://www.quantconnect.com/docs/v2/writing-algorithms/optimization/walk-forward-optimization).
- Parameters are injected with `get_parameter`. CHECKED (parameters page).

**Extend.**
- Every framework model is a swappable class, contributed by pull request to the LEAN repo. CHECKED (supported-models pages).
- **MCP server**: the older open-source repo lists 64 tools; the current remote one needs a paid node. CHECKED (https://github.com/QuantConnect/mcp-server ; key-concepts page). Tools cover projects, files (compile on write), compile, backtests (async, pushed results, paginated orders, log search), optimisations (estimate, create, read, abort), live (create, read portfolio/orders/logs, stop, liquidate, commands), object store, `check_initialization_errors`, `check_syntax`, `enhance_error_message`, `search_quantconnect` and project templates.

### 1.5 Jesse

**Contract.** A `Strategy` class. CHECKED (https://docs.jesse.trade/docs/strategies/entering-and-exiting ; .../events):
- `should_long()` / `should_short()`: booleans, called only when flat and no order is active
- `go_long()` / `go_short()`: set `self.buy` / `self.sell`, `self.stop_loss` and `self.take_profit` as `(qty, price)` or **lists of tuples** for multi-point entries and exits. The order type is inferred from price against current price: market, limit or stop.
- `should_cancel_entry()`
- `update_position()`: trail exits, add to size
- `before()` / `after()`
- events: `on_open_position`, `on_close_position` (with `order.is_take_profit` / `is_stop_loss`), `on_increased_position`, `on_reduced_position` (e.g. move the stop to breakeven after a partial), `on_cancel`
- cross-route events: `on_route_open_position(strategy)` and similar, with `self.shared_vars`

**Data.**
- **Routes** = (exchange, symbol, timeframe, strategy).
- **Data routes** = extra candles with no strategy, for multi-timeframe and multi-symbol. Jesse handles look-ahead for them but warns they make simulation slower.
- Timeframes fixed from 1m to 1D; no custom timeframes.
- Exchange + symbol must be unique, so only one position per symbol.
- About 5 routes is "usually a safe number" live.
- CHECKED (https://docs.jesse.trade/docs/routes.html).

**Instruments.** Exchange + symbol strings (crypto spot and futures). INFERRED from the routes page; no richer spec found.

**Orders.** Inferred order types plus position events (above). One position per route. CHECKED.

**Testing.**
- Optimisation runs on **Optuna** with **Ray**. Default objective Sharpe; Calmar, Sortino and Omega optional. It can optimise "the choice between which indicator to use" and "multiple entry rules". CHECKED (https://docs.jesse.trade/docs/optimize/).
- `hyperparameters()` returns dicts: `{'name','type': int|float|'categorical','min','max','step','default'}`, read as `self.hp[...]`. CHECKED (https://docs.jesse.trade/docs/optimize/hyperparameters).
- **Monte Carlo**:
  - `monte_carlo_trades`: trade-order shuffle
  - `monte_carlo_candles`: full re-backtests on modified candles via pipelines, either **Moving Block Bootstrap** (recommended; block size from a batch size such as one week of M1) or **Gaussian Noise** with OHLC sanity
  - results report percentiles, confidence intervals, p-values and an "interpretation"
  - CHECKED (https://docs.jesse.trade/docs/research/monte_carlo ; https://docs.jesse.trade/docs/monte-carlo/candle-pipelines).

**Extend.** Plain Python strategy files with Jesse's `ta` library. INFERRED (examples use `ta.sma(self.candles, ...)`).

### 1.6 freqtrade

**Contract.**
- `IStrategy` (interface version 3). Three **vectorised** functions over a pandas DataFrame: `populate_indicators`, `populate_entry_trend` (sets `enter_long` and similar columns) and `populate_exit_trend`. CHECKED (https://www.freqtrade.io/en/stable/strategy-customization/).
  - Signals are made at candle close. Trades start at next candle open.
  - "Only complete/finished candle data is available", so no repainting.
  - Backtesting passes the full range at once, so the author must avoid future data.
- Then per-trade **callbacks**: `bot_start`, `bot_loop_start`, `custom_stake_amount`, `custom_exit`, `custom_stoploss`, `custom_roi`, `custom_entry_price` and `custom_exit_price`, entry and exit timeouts, `confirm_trade_entry` and `confirm_trade_exit`, `adjust_trade_position` (scale in and out), `adjust_entry_price`, `leverage`, `order_filled`. CHECKED (https://www.freqtrade.io/en/stable/strategy-callbacks/).
- The docs include an "exit logic comparison" table: when to use a signal exit, `custom_exit`, `custom_stoploss` or `custom_roi`. CHECKED (same page).
- Static settings: `minimal_roi` (an ROI-by-time table), `stoploss`, trailing settings, `startup_candle_count`, `can_short`. INFERRED from the anatomy list ("Minimal ROI", "Stoploss fixed/trailing") on the customization page.

**Data.**
- Extra pairs and timeframes come from `informative_pairs()` or the `@informative` decorator plus `merge_informative_pair`. CHECKED (imports listed on the callbacks page).
- **Pairlists** = a chain of handlers. CHECKED (https://www.freqtrade.io/en/stable/plugins/):
  - one generator: Static, Volume, PercentChange, Producer, Remote, MarketCap or CrossMarket
  - then filters: Age, Delist, FullTrades, Offset, PairInformation, **Performance**, Precision, Price, Shuffle, **Spread**, **RangeStability**, **Volatility**
  - the blacklist supports regex
  - `VolumePairList` "does not support backtesting mode"

**Instruments.** CCXT pair strings with spot or futures trading mode (via `leverage`, `can_short`). INFERRED.

**Orders.** One open trade per pair by default. `--eps` (position stacking) works only in backtest and "cannot be reproduced in dry/live". CHECKED (hyperopt command reference).

**Testing.**
- Modes: backtesting, hyperopt, **dry ("forward testing")**, live, FreqAI. CHECKED (customization page).
- `--timeframe-detail` adds a finer series for intrabar fills. CHECKED (lookahead CLI reference).
- **Protections**: per-pair or global trading locks, also per side. CHECKED (https://www.freqtrade.io/en/stable/plugins/):
  - `StoplossGuard`: N stop-losses within a lookback → lock
  - `MaxDrawdown`: equity or ratio mode
  - `LowProfitPairs`
  - `CooldownPeriod`
  - durations in candles or minutes; an `unlock_at` time
  - backtest only with `--enable-protections`
- **Hyperopt** = Optuna (the NSGA-III sampler). The search spaces cover the buy, sell, ROI, stoploss, trailing and protection settings. Loss functions are pluggable (`--hyperopt-loss`). Options include `--min-trades`, `--early-stop` and `--random-state`. The docs say it "will burn all your CPU cores". CHECKED (https://www.freqtrade.io/en/stable/hyperopt/).
- **`lookahead-analysis`**. CHECKED (https://www.freqtrade.io/en/stable/lookahead-analysis/):
  - chains backtests and compares indicator values and moved entries against the full run
  - forces market orders, infinite wallet, fixed stake and protections off, "to avoid ... false positives"
  - runs in freqUI as a background task
- **`recursive-analysis`** is named there too. CHECKED (customization page).

**Extend.** Custom strategies, pairlist handlers, protections, hyperopt losses, FreqAI models; REST API and freqUI. CHECKED for the list of plugin kinds (plugins page); the REST API is INFERRED from the freqUI references.

### 1.7 NautilusTrader

**Contract.**
- `Strategy` extends `DataActor` with order management. A `StrategyConfig` holds settings. CHECKED (https://nautilustrader.io/docs/latest/concepts/strategies/).
- Lifecycle: `on_start`, `on_stop`, `on_resume`, `on_reset`, `on_dispose`, `on_degrade`, `on_fault`, `on_save` → `dict[str, bytes]`, `on_load(state)`. CHECKED (same page).
- Data handlers: `on_book_deltas`, `on_book`, `on_quote`, `on_trade`, `on_bar`, `on_mark_price`, `on_index_price`, **`on_funding_rate`**, `on_instrument_status`, `on_option_greeks`, `on_data`, `on_signal`, plus `on_historical_*`. CHECKED (same page).
- Order handlers: about 17 specific events (accepted, rejected, filled, triggered, ...) plus a generic `on_order_event`. CHECKED (same page).
- "The same strategy source can run in backtest and live environments", with a named list of differences: venue, transport, timing, persistence, external activity, reconciliation. CHECKED (same page; https://nautilustrader.io/docs/latest/concepts/live/).
- **Actors** (no orders) publish custom data and signals, and own timers and alerts through `self.clock`. CHECKED (https://nautilustrader.io/docs/latest/concepts/actors/). INFERRED: an Actor is the right shape for an MIS labeler or a router, outside strategies.

**Data.**
- Precedence of detail: L3 > L2 > L1 quotes > trades > bars.
- The venue's `book_type` decides which data drives matching. A table lists what is ignored. "Nautilus cannot generate higher granularity data (L2 or L3) from lower-level data". CHECKED (https://nautilustrader.io/docs/latest/concepts/backtesting/data-and-venues/).
- Bars: `ts_init` must be the bar close.
- Each bar becomes 4 synthetic L1 updates, O→H→L→C by default, or adaptive ("visits the extreme closest to the open first").
- Orders sent from `on_bar` see only the book after the close. Latency models can delay arrival. CHECKED (https://nautilustrader.io/docs/latest/concepts/backtesting/bar-execution/).

**Instruments.**
- A typed taxonomy with an `InstrumentClass`: Equity, CurrencyPair (FX and crypto spot), Commodity, **Cfd**, IndexInstrument, TokenizedAsset, FuturesContract, FuturesSpread, CryptoFuture, **CryptoPerpetual / PerpetualContract (SWAP)**, OptionContract, OptionSpread, CryptoOption, BinaryOption, BettingInstrument, **SyntheticInstrument**. CHECKED (https://nautilustrader.io/docs/latest/concepts/instruments/).
- Common fields: `id` = `{symbol}.{venue}`, `raw_symbol`, price and size precision, price and size increment, `multiplier`, `lot_size`, `margin_init`, `margin_maint`, min/max quantity, notional and price, `tick_scheme` (fixed or tiered), `info`, `ts_event`, `ts_init`. CHECKED (same page).
- The docs warn that a wrong instrument "can also make a backtest accept prices a live venue would reject". CHECKED (same page).

**Orders.**
- The venue sets `oms_type` NETTING or HEDGING and `account_type` CASH or MARGIN.
- Fees belong to the venue (`MakerTakerFeeModel`), not the instrument. CHECKED (https://nautilustrader.io/docs/latest/concepts/backtesting/apis-and-runs/).
- Execution algorithms and a portfolio exist. CHECKED (nav links on the backtesting page).

**Testing.**
- `BacktestEngine` (low level, manual) or `BacktestNode` (config objects, Parquet catalog, chunked streaming, batch runs). CHECKED (apis-and-runs page).
- **Fill models**: `prob_fill_on_limit`, `prob_slippage` (one tick), `random_seed`, `liquidity_consumption`; 11 built-ins (BestPrice, OneTickSlippage, Probabilistic, Two- and Three-Tier, SizeAware, CompetitionAware, VolumeSensitive, MarketHours, ...); custom models via `is_limit_filled` / `is_slipped`. CHECKED (https://nautilustrader.io/docs/latest/concepts/backtesting/fill-models/).
- **No optimiser or walk-forward page** in the concepts navigation. CHECKED by absence (the full concepts link list in the browser, 2026-10-24). INFERRED: users run parameter sweeps themselves over `BacktestNode` configs.

**Extend.** Python or Rust; custom data, actors, execution algorithms, adapters. CHECKED (concepts navigation: custom_data, actors, execution/algorithms, adapters).

---

## 2. Cross-platform comparison

All cells CHECKED from the sources in §1, except where marked (I) for INFERRED.

| Topic | MT5 / MQL5 | cTrader Algo | NinjaScript | LEAN | Jesse | freqtrade | Nautilus | **QML / QMB today** |
|---|---|---|---|---|---|---|---|---|
| Language | MQL5 (C++-like); Python only as a data and order bridge | C# and native Python (pythonnet) | C# | Python and C# | Python | Python (pandas) | Python and Rust | Plain Python (`qml/src/qml/protocol/factory.py`) |
| Strategy unit | EA + event handlers | `Robot` class | Strategy + `OnStateChange` states | `QCAlgorithm`; classic or framework | `Strategy` with should/go/update | `IStrategy`: 3 vectorised functions + callbacks | `Strategy` (an Actor + orders) | CT-33 declaration + factory → per-instant callback |
| Main hook | `OnTick` | `OnTick` / `OnBar` / `OnBarClosed` | `OnBarUpdate` (`Calculate` mode) | `on_data(slice)` or `AlphaModel.update` | per candle: should → go → update | `populate_*` over the whole frame | `on_bar` / `on_quote` / `on_trade` / `on_book` | per evaluation instant, declared evidence only |
| Settings with ranges | `input` + tester ranges | `[Parameter]` + optimiser ranges | user inputs + Analyzer ranges | `get_parameter`; ranges in the optimiser UI | `hyperparameters()` dict list | `IntParameter`, `DecimalParameter`, ... in the strategy | `StrategyConfig` (no ranges) | CT-33 parameter space with unit kinds (B-8) |
| Output | orders (CTrade) | orders | managed or unmanaged orders | Insights → targets → orders | buy/sell/stop/TP tuples | signal columns + callbacks | orders | CT-23 intents; never sizes |
| Strength or confidence | Wizard vote −100…+100, thresholds | none (I) | none (I) | Insight magnitude, confidence, weight, **expiry** | none | none (`enter_tag` only, I) | none (I) | none (no `strength` field in `qml/src/qml/protocol/intents.py`) |
| Exits | SL/TP fields + Trailing modules | SL/TP on orders, `ModifyPosition` | `SetStopLoss`/`SetProfitTarget`/`SetTrailStop`; ATM (live only) | Risk models + alpha "flat" insights | lists of SL/TP + `update_position` + `on_reduced_position` | `minimal_roi`, `stoploss`, trailing, `custom_exit`/`custom_stoploss`/`custom_roi` | orders + execution algorithms | permitted exit-intent kinds; Book `ExitLogicRef`; advisory stop (`docs/components/qml.md`, QL-7/QL-9) |
| Sizing | Money modules (fixed lot, margin, risk, optimized) | in bot | in bot / `QuantityType` | Portfolio Construction model | in `go_long` qty | `custom_stake_amount` | in bot | Book-resolved `requested_r` (bot never sizes) |
| Multi-timeframe | any `CopyBuffer`/`CopyRates` | `GetBars(tf, symbol)` | `AddDataSeries` in Configure, hard-coded | subscriptions + consolidators | data routes | `@informative` | subscribe bar types | declared stream set; higher BarSpec from finest base, closed only (B-2/B-12) |
| Multi-symbol | yes; tester auto-loads | yes; `Symbols.GetSymbol` | yes; `BarsInProgress` | universe (dynamic) | routes; ≤ ~5 live | pairlists (dynamic) | any instruments | stream set; one position per (venue, instrument) (B-12) |
| Instrument model | ~100 SymbolInfo props; custom and synthetic symbols | FX-shaped `Symbol` (pips, lots) | MasterInstrument + rollover + trading-hours templates | Security + SymbolProperties + exchange hours + per-security models | strings (I) | CCXT pairs (I) | typed classes incl. CFD, perp, synthetic; increments, multiplier, margins | `Instrument(venue, symbol)` + dated key/value records (`qmf/core/identity.py`) |
| Netting / hedging | per account (broker) | hedging-style positions (I) | per account (I) | per brokerage model (I) | one per route | one per pair (stacking backtest-only) | venue `oms_type` | one per (venue, instrument) per run |
| Tick fidelity | generated ticks, **real ticks**, M1 OHLC, open only, math | ticks, M1, H1, CSV, custom source | 3 virtual bars or a finer series; Tick Replay | by resolution + fill models | 1m candles (I) | `--timeframe-detail` | L3/L2/L1/trades/bars + book type + adaptive OHLC | event slices; fill/slippage/cost ports, `optimistic` taint until calibrated (B-6) |
| Latency / delay | none / random / fixed ping; requotes | none found | none found | none found in pages read | none | none | latency models | not modelled (I) |
| Optimiser | grid / genetic; custom `OnTester`; all-symbols mode; forward split | grid / genetic; multi-criteria; `GetFitness`; timeframe sweep; CLI | default / genetic / custom; multi-objective; data-series sweep | cloud grid ≤ 3 params; more locally | Optuna + Ray | Optuna NSGA-III, loss functions, spaces incl. protections | none built in | pure generation-stepped sampler, Optuna adapter (B-8); sweep axes instrument × timeframe (`qmb/src/qmb/sweep/axes.py`) |
| Walk-forward | forward period only (I) | none found | yes (rolling IS/OOS) | in-algorithm `train()` schedule | none found | none built in (I) | none | split sequence of a fixed assignment (03 row 8) |
| Monte Carlo | none in tester (I) | none | yes | none found | trade shuffle + candle bootstrap/noise | none | none | trade shuffle, candle perturbation, rule significance (B-14) |
| Look-ahead guard | none (index 0 = forming bar) | `OnBarClosed` excludes live bar | `Calculate=OnBarClose` | engine time-gating (I) | engine guards extra candles | `lookahead-analysis` + `recursive-analysis` commands | `ts_init` = close; data gated by clock | forming bar never visible (B-2); AST scan + determinism harness (QL-8) |
| Agent / automation door | none official (I) | CLI (backtest, optimize), plugins drive optimiser | none found | **MCP**: 64 tools in the open-source repo | none found | REST API + freqUI (I) | Python API | `qmb` CLI/API/MCP doors with a parity test (`qmb/src/qmb/doors/{cli,api,mcp,parity.py}`); agents refused today (01 §1.2) |
| Tries counted / deflated | no | no | no | no (but caps params) | no | no | no | slots reserved; DSR scripts idle in workflow templates (01 §0.9) |

---

## 3. What QML should COPY, ADAPT, AVOID

Each row names its donor, what to do, the QMX blast radius, and the lever. All recommendations are INFERRED unless a cell says CHECKED.

### 3.1 Strategy contract

| Verb | What | From | Blast radius | Lever |
|---|---|---|---|---|
| COPY | **Split the bot into four questions**: *when to enter* (signal, with reason and optional strength), *how to enter* (entry price/type, advisory stop, multi-point take-profit list), *manage* (an `update`-style hook that may move stops, take partials, add) and *cancel a pending entry*. This is Jesse's should/go/update/cancel. Plus freqtrade's per-trade hooks for stop, exit and ROI-by-time. | Jesse, freqtrade | `qml/src/qml/protocol/intents.py` (add `reason`, `strength`, multi-leg TP, cancel-entry intent kinds through a CT-23 format mint), CT-23 v2/v3 (`docs/contracts/ct-23-risk-evaluation.yaml`), `qml/src/qml/declaration/bot.py` permitted-intent declaration | E, N |
| COPY | **Signal expiry**: every entry signal carries a validity horizon, like LEAN's `Insight.period`. A signal not acted on in time lapses, so a late fill does not act on a stale idea. | LEAN | CT-23 entry intent (new optional field), QMB B-2 sub-phase 5/6 resting rule | E, D |
| COPY | **A fresh bot instance per trial**, so trial N never sees trial N−1's state. | NinjaTrader (`IsInstantiatedOnEachOptimizationIteration`, CHECKED) | already QMB B-5 (process per run); state it in QL-8 conformance as a test | P |
| COPY | **Closed-bar only by default.** A forming bar is never visible. The tick hook is opt-in and needs tick or quote data. | freqtrade ("does not store incomplete candles", CHECKED), cTrader `OnBarClosed` | already B-2; expose two hook kinds in the QML runtime: `on_bar_closed` (default) and `on_quote` (scalper opt-in) | D, P |
| ADAPT | **Vectorised authoring for research, event-driven for running.** Let a strategy *optionally* define `indicators(df)` and `signals(df)` over a whole frame (freqtrade style), which QML compiles into the per-instant protocol. Look-ahead and recursion checks (§3.7) run automatically. | freqtrade | new authoring helper in `qml` (pure); QL-7 protocol unchanged; conformance adds a vectorised-vs-streaming equality check | N (agents produce more working bots), P |
| ADAPT | **Lifecycle states belong to the host, not the bot.** NinjaTrader exposes `Historical`/`Transition`/`Realtime` to the script. QMX should not, because the bot must behave the same in history and live (determinism). The host owns warm-up, seat start and stop. Only `on_start(state)`, `on_stop` and `save`/`load` are visible (Nautilus `on_save`/`on_load`, CHECKED). | NinjaTrader, Nautilus | `qml/src/qml/protocol/state.py` (snapshot/restore exists), QMN seat machinery | P |
| AVOID | **Strategies talking to each other** (Jesse's `on_route_*` and `shared_vars`, CHECKED). It couples units and breaks per-unit proof. Cross-unit logic belongs to the pod. | Jesse | none (do not add) | P |
| AVOID | **Putting order-type choice in the bot.** Jesse infers market/limit/stop from price (CHECKED). Keep it, but as an intent property the node maps to venue capability (CT-18). | Jesse | CT-23 intent vocabulary, CT-18 venue capabilities | D |

### 3.2 Indicator and block catalogue

| Verb | What | From | Blast radius | Lever |
|---|---|---|---|---|
| COPY | **Three block families plus filters, like the MT5 Wizard: Signal, Exit (trailing and more), Sizer (money).** Signal blocks return strength 0–1 (MT5's 0–100). A *combiner* block turns several signals into one decision with open and close thresholds. Sizer blocks belong to the unit, not the bot. | MT5 Wizard (CHECKED) | CT-34 leg roles `level | trigger | confirmation | filter` (`qml/src/qml/declaration/confluence.py`) map onto Signal/Filter; Exit and Sizer are new block kinds (GAP-0085 mechanism nouns, deferred today per `docs/components/qml.md`) | E, S |
| ADAPT | **Make the vote configurable, not fixed.** MT5 always takes the arithmetic mean of weighted forecasts. That dilutes a strong signal when weak ones are added. The combiner becomes a block (mean, min, all-of, k-of-n, weighted) whose choice is a parameter and counts as a try. | MT5 (CHECKED mechanism) | new combiner block; parameter space (B-8) | E, P |
| COPY | **Time filter as a first-class block** (`CSignalITF`, "filtration of signals by time"; NinjaTrader Condition Group time filter). Serves sniping windows. | MT5, NinjaTrader (CHECKED) | filter block; session calendars (CT-02) | E, N |
| COPY | **Handle-then-read indicator access**: declare once at start, read by index with "closed only" semantics. QMX already has it: footprint producer bindings, closed-data update in sub-phase 4. | MT5 `iMA` + `CopyBuffer`, cTrader `Indicators.*` | `qml/src/qml/footprint/*`, `packages/qmf-indicators/*` | D |
| COPY | **Fill the indicator set traders actually use first.** QMX names 15 formulas, of which 6 have runnable wrappers (ATR, VWAP, Bollinger and sessions missing). CHECKED (01 §1.1). MT5 ships 20 signal modules on standard indicators; cTrader and NinjaTrader ship large built-in sets. | MT5, cTrader, NinjaTrader | `packages/qmf-indicators/src/qmf/indicators/wrappers.py`, `arithmetic.py` | E, N |
| ADAPT | **Strategy-Builder-style "see the code"**: a no-code condition builder that writes plain Python live and shows it. The Lab's graph and code views of one draft match this. | NinjaTrader Strategy Builder (CHECKED) | Lab (UI session); generates the same two QML artifacts (QL-2 says a future grammar "COMPILES TO these same two artifacts") | N |
| AVOID | **A closed catalogue that only grows by vendor release.** MT5's 20 modules have barely changed since 2011 (INFERRED from the 2011 article). Use LEAN's approach (models contributed and swappable, CHECKED) plus the operator's librarian. | LEAN | librarian workflow (QMA) | N |

### 3.3 Instrument model

| Verb | What | From | Blast radius | Lever |
|---|---|---|---|---|
| COPY | **A typed instrument class taxonomy**: spot (FX, crypto, metal), CFD, future, perp/swap, option, synthetic. One `InstrumentId = symbol.venue` plus `raw_symbol`. | Nautilus (CHECKED) | `packages/qmf-core/src/qmf/core/identity.py` (`Instrument`, `DatedRecord` content gets a schema per class); CT-03 (`docs/contracts/ct-03-instrument-identity.yaml`) | D |
| COPY | **The common spec fields**: price and size increment, precision, multiplier/contract size, lot size, min/max quantity and notional, initial and maintenance margin, tick scheme (fixed or tiered). | Nautilus, MT5 (CHECKED) | same; QMB fill/cost ports read them (`qmb/src/qmb/execution/{fill,cost,financing}.py`) | D |
| COPY | **CFD and FX extras**: swap long/short, swap mode, a weekday swap ratio, triple-swap day, stops and freeze levels, allowed filling modes, separate quote and trade sessions, tick value for profit vs loss. | MT5 (CHECKED) | `qmb/src/qmb/execution/financing.py`, cTrader adapter (`packages/qmf-venue/src/qmf/venue/ctrader.py`) | D |
| COPY | **Futures extras**: trading-hours templates with holidays and early closes, a rollover schedule with offsets, and a merge policy (back-adjusted / raw / none) as an explicit data choice. | NinjaTrader (CHECKED) | qmf-data processed room (derived views with lineage); CT-02 calendars | D, P |
| COPY | **Perp extras**: funding-rate and mark-price streams as first-class data. | Nautilus `on_funding_rate`, `on_mark_price` (CHECKED) | qmf-data intake (CT-15); QMB financing port (perps have "no contract, funding or margin model anywhere", 01 §0.4) | D |
| COPY | **Custom and synthetic symbols** with their own spec and sessions (MT5), and custom data sources fed to the tester (cTrader). Lets QMX test spreads, baskets and broker data it cannot download. | MT5, cTrader (CHECKED) | qmf-data; QMB reader | N |
| AVOID | **An FX-shaped symbol stretched over everything** (cTrader `Symbol` "Represents a currency pair", pips and lots). Sizing in pips on an index or perp is a known bug source. | cTrader (CHECKED wording) | sizing in `packages/qmf-risk` must use tick value and contract multiplier, never "pips" | S |
| AVOID | **Fees on the instrument.** Nautilus puts fees on the venue/account ("Two accounts can trade the same instrument under different schedules", CHECKED). Same for QMX: costs are per (venue, account, instrument). | Nautilus | QMB cost port; Book/BMS | D |

### 3.4 Multi-timeframe and multi-symbol

| Verb | What | From | Blast radius | Lever |
|---|---|---|---|---|
| COPY | **Declare every series up front, hard-coded** (NinjaTrader: `AddDataSeries` only in `Configure`, never from runtime variables, CHECKED). QMX already has this as the declared stream set (B-12) and footprint (QL-4). Keep it. | NinjaTrader, Jesse data routes | none new; state it in agent docs | P |
| COPY | **Document processing order on shared timestamps** (NinjaTrader: primary first, CHECKED) and warn it may differ from live. QMX pins sub-phase and stream order as identity (B-2). Add the live caveat to the node seat docs. | NinjaTrader | `docs/components/qmb.md` B-2; QMN docs | P |
| COPY | **Derived higher timeframes from the finest base, emitted only when complete**, including count, Renko and range bars as consolidator kinds. | LEAN consolidators (CHECKED) | `qmb/src/qmb/runloop/*` BarSpec derivation | N |
| ADAPT | **Router-added markets.** LEAN alpha models get `on_securities_changed` and must warm up indicators for new assets (CHECKED). When the MIS router places a unit on a new instrument, the host must build a fresh seat with its own warm-up per (unit, instrument). Do not add the instrument inside a running bot's state. | LEAN | QMN seat admission; router design | N, P |
| AVOID | **Too many live routes per process** (Jesse: about 5 is "a safe number", CHECKED). The node should scale by seat with per-seat deadlines (already DEC-0204), not one bot looping over many symbols. | Jesse | QMN | D |

### 3.5 Exits and money-management modules

| Verb | What | From | Blast radius | Lever |
|---|---|---|---|---|
| COPY | **An exit block catalogue that runs inside the backtest loop**: hard stop, ATR stop, trailing (fixed, ATR, MA, PSAR, chandelier), breakeven after a partial, multi-point take-profit lists, an ROI-by-time table, time stop, indicator exit (e.g. VWAP), invalidation exit. | MT5 Trailing modules, NinjaTrader `SetTrailStop`/`SetParabolicStop`, Jesse TP lists + `on_reduced_position`, freqtrade `minimal_roi`/`custom_stoploss`/`custom_roi`, LEAN `MaximumUnrealizedProfit`/trailing (all CHECKED) | new Exit block kind; QL-9 keeps CT-29 as the one close-reason taxonomy (map each exit block to a CT-29 reason); Book `ExitLogicRef` adopt-advisory mode (DEC-0185) | E, D |
| AVOID | **Exit management that the backtest cannot replay.** NinjaTrader ATM strategies "can't be backtested" and their fills do not count toward strategy P&L (CHECKED). Any exit QMX trusts must run identically in QMB replay and on the node. | NinjaTrader | QMN must host only exit logic that is a QML block or bot code QMB also runs | P |
| COPY | **Sizer modules as a menu**: fixed lot, fixed margin, fixed risk %, minimum, size-from-recent-results. These are the unit's sizer options, tuned from the unit's own record, with Kelly as a ceiling (operator's decisions). | MT5 Money modules (CHECKED) | `packages/qmf-risk/src/qmf/risk/sizing.py` (defined-unwired, 01 §0.7); unit design | S |
| COPY | **Protections as lock records**: (scope = pair, side or global; reason; until; trigger rule). Rules: N stop-losses in a lookback, drawdown over a window, low profit, cooldown after exit. These are the operator's loss points, bleeding control and bench, written as data. | freqtrade Protections (CHECKED) | unit risk profile (bench, loss points); pod guards; Book `control_policy` / leash (CT-22) | S, D |
| COPY | **Managed by default, unmanaged opt-in.** Default bots emit managed intents (entry plus linked SL/TP, OCO, one entry per direction). An advanced tier (grids, market making) gets raw order intents with the overfill and reconciliation duties NinjaTrader lists (CHECKED). | NinjaTrader | CT-23 intent tiers; QMN reconciliation | D |

### 3.6 Testing modes

| Verb | What | From | Blast radius | Lever |
|---|---|---|---|---|
| COPY | **A named fidelity ladder** the user picks, and the run label carries: open-only → M1 OHLC (fixed or adaptive path) → generated ticks → real quotes/ticks → L2. Each step says what it can and cannot prove ("1 minute OHLC" allows a Testing Grail; MT5, CHECKED). | MT5 tick modes, Nautilus data table, NinjaTrader Standard vs High (CHECKED) | `qmb/src/qmb/execution/fidelity.py` (fidelity identity exists, B-6); sweep axis for fidelity | P, D |
| COPY | **Adaptive intrabar path** as an option: visit the extreme nearest the open first. Show it as a heuristic, not a truth. Flag trades where SL and TP sit inside the same bar (SQ's "too many trades closing at the same bar", 03 §2.1). | Nautilus, NinjaTrader (CHECKED) | `qmb/src/qmb/execution/fill.py` declared-path crossing | D, P |
| COPY | **Execution delay and random spread** as stress settings: none / random / fixed (measured ping) delay with requotes (MT5); random spread in a min–max range (cTrader). Later, draw both from QMX's own fill journals (B-6 "calibration, never invention"). | MT5, cTrader (CHECKED) | `qmb/src/qmb/execution/{slippage,spread}.py`; QMN fill journals | D |
| COPY | **Probabilistic limit fills with a seed** (`prob_fill_on_limit`, one-tick `prob_slippage`, `random_seed`) as a cheap first fill model for scalpers' limit entries. | Nautilus fill models (CHECKED) | `qmb/src/qmb/execution/fill.py` | D |
| COPY | **A "math mode" run**: no market data, only init, the objective and teardown. Useful for testing sizer and allocator logic and Monte Carlo maths without a backtest. | MT5 Math calculations (CHECKED) | QMB library function (no new door) | P |
| COPY | **Dry-run = forward testing on live data with simulated fills**, named as such. QMX already has research-paper and node-paper (`docs/components/qmb.md` "Paper trinity"). | freqtrade (CHECKED) | none new | P |
| AVOID | **Tick-by-tick live while history runs bar-close.** NinjaTrader warns this produces different trades (CHECKED). A QMX bot's hook kind is fixed in its declaration and identical in QMB and the node. | NinjaTrader | QL-7 declaration | P |

### 3.7 Optimisation and walk-forward

| Verb | What | From | Blast radius | Lever |
|---|---|---|---|---|
| COPY | **Look-ahead and recursive analysis as conformance gates** (freqtrade, CHECKED). Look-ahead: rerun with the data truncated at many points t and compare signals at t with the full run. Recursive: rerun with different start-up history lengths and compare indicator values. Fail on any difference. | freqtrade | `qml/src/qml/conformance/layer2.py`, `harness.py`, `slice.py` (golden slice exists; add truncation and warm-up variants) | P |
| COPY | **Jesse's hyperparameter dict schema**, which matches QMB B-8 (int, float, categorical, bool with min, max, step, default). Categorical can pick *which indicator* or *which entry rule*. Note that this is a structure search and counts as tries. | Jesse (CHECKED) | `qml/src/qml/declaration/parameters.py` (matches already); tries ledger | E, P |
| COPY | **Several criteria at once (max/min), or a custom fitness function** (cTrader multi-criteria; MT5 `OnTester`; NinjaTrader custom `OptimizationFitness`). In QMX the criterion is a *sort lens* only, never stored as evidence (DEC-0162; 03 row 9). | cTrader, MT5, NinjaTrader (CHECKED) | `qmb/src/qmb/optimize/objective.py`, `sweep/rank.py` | P |
| COPY | **Domain expansion as an optimisation mode**: MT5 "All Symbols Selected in Market Watch" and the cTrader CLI timeframe sweep. QMX's `sweep/axes.py` already crosses instrument × timeframe (03 row 6). Every cell counts as a try. | MT5, cTrader (CHECKED) | `qmb/src/qmb/sweep/axes.py`; registry cells | N, P |
| COPY | **Estimate cost before launching a sweep** (QC `estimate_optimization_time`, CHECKED; cTrader shows `--cores` defaults). | LEAN | QMB governor (`min(cpu, memory)`, B-5); agent door | D |
| COPY | **A parameter cap as a default guard** (LEAN cloud ≤ 3 parameters, partly citing overfitting, CHECKED). Raising the cap is allowed, but the tries count grows and the Lab shows it. | LEAN | B-8 sampler config; Lab | P |
| ADAPT | **Two kinds of walk-forward.** (a) Tester-level rolling re-optimisation (NinjaTrader WFO; SQ WF Matrix in 03). (b) In-strategy scheduled retraining (LEAN `train()` on a schedule, CHECKED). (b) is how a model-bearing bot or a self-tuning unit retrains live. In QMX the retrain schedule, window and seed are declared identity, and QMB replays the retrains exactly. | NinjaTrader, LEAN | `qmb/src/qmb/robustness/walkforward.py`, `optimize/splits.py`; unit self-tuning (risk numbers only, within ranges) | P, S |
| COPY | **Resumable searches** (MT5 genetic cache resumes after a power failure, CHECKED). QMB already reads trial history from the ledger (B-8), which makes resume natural. | MT5 | `qmb/src/qmb/optimize/resume.py` (exists) | D |
| COPY | **Block-bootstrap candles** with block length tied to time (Jesse Moving Block Bootstrap, one week of M1 suggested, CHECKED). QMB has candle perturbation. Add block bootstrap as a named method, robustness-only claim class (B-7). | Jesse | `qmb/src/qmb/robustness/*` | P |
| AVOID | **Picking "the best pass" automatically** (cTrader "Autoselect the best pass"; NinjaTrader "Keep best # results", CHECKED). The best pass is the luckiest. QMX shows the plateau and the median (SPP, 03 row 7) beside the best. | cTrader, NinjaTrader | Lab results; `optimize/sensitivity.py` | P |

### 3.8 Plain-Python freedom

| Verb | What | From | Blast radius | Lever |
|---|---|---|---|---|
| COPY | **Dependencies declared next to the code** (cTrader `requirements.txt` at the project root, resolved at build, CHECKED). For QMX: the logic distribution's lockfile is part of the source-manifest identity, so the same bytes give the same `fp1` (QL-2). | cTrader | `qml` logic distribution identity (`docs/components/qml.md` QL-2); conformance Layer 2 runner | N, P |
| COPY | **ML models as artifacts the strategy loads**, testable in the tester (MT5 ONNX, CHECKED). QMX allows baked-in weights today (QL-2). Add ONNX as a supported model format, with its hash in identity. | MT5 | QL-2 deferred "weights-artifact parameter kind" | E |
| KEEP | **QML's denial set** (clock, I/O, network, undeclared randomness, `qml/src/qml/protocol/contract.py:31-33`, CHECKED) against cTrader's "HTTP available even in backtests" (CHECKED). Determinism is what makes backtest = live provable. Outside data enters as declared data streams (Nautilus `on_data` custom data). | Nautilus custom data | none new | P |
| ADAPT | **Three doors, one contract**: plain function (zero QML imports, ungoverned, already legal per DEC-0270), QML helpers (the vectorised and event styles of §3.1), and blocks (no-code). All three compile to the same two artifacts. | freqtrade + NinjaTrader Builder | `qml` helper layer; Lab | N |
| AVOID | **A second language.** MT5 forces MQL5 and NinjaTrader forces C#. cTrader added Python in 2025 because users wanted it ("one of the world's most popular languages for data science", CHECKED blog). QMX already ruled out `.qml` in V1 (QL-2). Keep it out. | cTrader history | none | N |

### 3.9 The agent door (how an agent would call QML and QMB)

Modelled on QC's MCP tools (CHECKED) and SQ's 6-tool MCP (03 row 15). It routes through the existing `qmb` doors with the parity test (B-1, `qmb/src/qmb/doors/parity.py`) and the QMA tool catalog (`qmx-agents/packages/qmx-tools/src/qmx_tools/service.py`; `research.qml_run` refuses today, 01 §1.2).

| Tool (proposed) | Does | Donor | Blast radius |
|---|---|---|---|
| `qml.templates.search(intent)` | Returns starter bots by style (scalper mean-reversion, breakout, ...) with their declarations. | QC `read_project_templates` | `qml/examples/`, template store |
| `qml.blocks.search(query)` | Reuse before writing: finds signal, exit and filter blocks. | operator's librarian rule | block catalogue |
| `qml.validate(source, declaration)` | Layer 1 + Layer 2 + look-ahead + recursive checks. Returns typed refusals with the fix named. | QC `create_file` compiles and returns errors; freqtrade analyses | `qml/src/qml/conformance/*` |
| `qml.smoke(bot, days=N)` | Runs a few days to catch start-up and warm-up errors. | QC `check_initialization_errors` | QMB run loop, short window |
| `qmb.run(bot_ref, run_spec)` | Asynchronous. The result is **pushed** to the agent when done ("do not poll"). | QC `create_backtest` | `qmb/src/qmb/doors/mcp`, orchestrator; QMA notification |
| `qmb.estimate(sweep_spec)` | Cost and time before launch; refuses beyond the governor. | QC `estimate_optimization_time` | QMB governor |
| `qmb.sweep / optimize / walkforward / montecarlo` | Same library functions as the CLI. Each trial is ledgered as a try. | MT5/cTrader/NT optimisers, Jesse MC | `qmb/src/qmb/{optimize,sweep,robustness}` |
| `qmb.read(result, view=trades|orders|equity|stats, page)` | Paginated readers (QC caps pages at 100). | QC `read_backtest_orders` | CT-32 readers |
| `qmb.compare(a, b)` | Head-to-head; live vs replay drift. | SQ Compare Results (03 row 17) | `qmb/src/qmb/analysis/compare.py` |

Rules for the door (INFERRED):
- An agent never edits QMB (operator, `decisions.md` "QMB is a tool agents call but cannot edit").
- Every call returns run ids, so the trust checklist (03 H6) can be machine-checked.

---

## 4. Mapping to the operator's seeds (all INFERRED)

### 4.1 LEAN universe → alpha → portfolio → risk → execution ↔ unit + router + Pods

| LEAN model | QMX part | Notes |
|---|---|---|
| Universe Selection | **MIS router** (placement) | LEAN selects assets inside the algorithm. QMX's router is outside the bot ("bots never read the MIS", seeds.md). The router decides which (instrument, session, state) cells a unit is seated on, from registry proof. LEAN's `on_securities_changed` becomes the host seating or unseating a unit-instrument (§3.4). |
| Alpha model → `Insight` | **The bot (strategy) inside the unit** | Insight = QML entry signal: direction, strength (≈ confidence), optional magnitude, **expiry**, reason tag. Multiple alpha models = several confluences or legs; the combiner is a block (§3.2). |
| Portfolio Construction → `PortfolioTarget` | **Unit sizer** (per bot, self-tuning from its record) **+ pod allocator** (across units) | LEAN merges both into one model. QMX splits them: the unit sizes its own trade within the pod's budget, and the pod allocates budget across units (pods' seven slots include allocator and sizer, 01 §4.1). |
| Risk Management (adjusts targets) | **Pod guards and caps + account guard** (kill line, loss budget, correlation, news, venue rules) + **unit safety exits** | LEAN risk models liquidate per security or portfolio (CHECKED). QMX: unit-level safety exits (hard stop, fast invalidation, breakeven) stay with the unit; account-level limits stay outside units (decisions.md). |
| Execution | **Node + venue adapters + SQS gate** | SQS blocks a trade when spread is abnormal, which is an execution-time gate, the way LEAN execution models (e.g. spread-aware) decide *how* to fill. |
| "Models should not communicate" | **The same rule** | Bots don't read the MIS; the sizer doesn't change signals; the router doesn't change logic. |
| "Framework fits technical strategies poorly" | **Warning for QMX** | Keep exits *inside* the bot (operator: "exits are part of the strategy"). Do not move them into the risk layer the way LEAN suggests. |

### 4.2 freqtrade pairlists and protections ↔ router and SQS

| freqtrade | QMX | Notes |
|---|---|---|
| Pairlist chain: one generator → filters in order | **Router candidate pipeline**: generator (registry *preferred* cells) → filters (spread state, volatility, range stability, data age, performance) | Same chain-of-handlers config shape, testable on its own (freqtrade has a `test-pairlist` command, CHECKED). |
| `SpreadFilter` | **SQS** | SQS is a live spread ÷ normal spread ratio; it blocks (02 §2). freqtrade filters the pair list. QMX gates the trade. Both are needed: SQS per trade, a spread filter for placement. |
| `PerformanceFilter` | **Registry proof ordering** | Order candidates by proof, not recent P&L. Recent-P&L ordering is a hidden fitted rule. |
| `VolumePairList` "does not support backtesting" (CHECKED) | **Router must be replayable** | Every router decision must be recomputable from recorded MIS states, or router value can never be proven. Big lesson. |
| Protections (per-pair, per-side, global locks; lookback; duration; `unlock_at`) | **Unit bench, loss points, bleeding control (fast), cooldown; pod-level drawdown lock** | Express them as lock records with a reason, so the UI can show "why is this unit paused". freqtrade can hyperopt protection settings (CHECKED). In QMX those tunings count as tries. |

### 4.3 MT5 Wizard modules ↔ block catalogue

| MT5 Wizard | QMX block catalogue |
|---|---|
| Signal module with patterns (significance 1–100) | Signal block with patterns; strength 0–1 |
| Advisors (nested signals, own symbol/timeframe, ≤ 64) | CT-34 legs, including child-confluence cites (already legal, DEC-0185); legs may read other declared streams |
| Weight 0–1, mean vote, `ThresholdOpen`/`ThresholdClose` | Combiner block with selectable rule and thresholds as parameters |
| `CSignalITF` time filter | Session/window filter block (sniping) |
| Trailing modules | Exit blocks (§3.5) |
| Money modules | **Unit sizer options**, not bot blocks (bot never sizes) |
| The four pillars (location/level, context, trigger, confirmation) | Map to `level | filter(context) | trigger | confirmation` leg roles that already exist in CT-34 |

### 4.4 NinjaTrader states ↔ stage tags

They are **different axes**, and the design should keep them apart.

| NinjaTrader state (runtime of one instance) | QMX equivalent |
|---|---|
| SetDefaults / Configure (declare series, once) | QML declaration + footprint; frozen at "compiled" |
| DataLoaded | Host resolves producers, builds the seat |
| Historical | QMB replay, or node warm-up from history (in-loop, trading locked, B-2) |
| Transition | Seat hand-off from warm-up to live; account and position sync |
| Realtime | Seat trading |
| Terminated | Seat stopped or quarantined (DEC-0204) |

**Stage tags** (research → backtest → optimise → stress → paper → live; open vs compiled; decisions.md) describe the *record's* maturity. NinjaTrader gives one rule worth copying into "compiled": `AddDataSeries` must be hard-coded in `Configure`. So "compiled" freezes the footprint and logic bytes (source-manifest fp), and only the risk profile tunes within its ranges.

Possible conflict to raise: DEC-0261 says the node runs "no per-bot warm-up, probation, ramp or paper lane". Indicator warm-up from history at seat start is still needed (NinjaTrader `Historical`→`Transition`). The docs should state that DEC-0261 means *probation* warm-up, not indicator warm-up. INFERRED. Check the wording in `docs/components/qml.md` (trading-node increment).

---

## 5. What the operator may not be seeing

1. **QML's skeleton is already industry-standard; "rebuild from scratch" risks throwing away matching work.** About 14k lines (`qml/src/qml/`, 01 §1.2) already do what every platform's base class does: declaration with ranges, closed-data evidence, a deterministic callback, snapshot/restore, a conformance gate. The 13 Oct ruling says rebuild. The scope rule says name the blast radius and don't casually remove shipped work. What is missing is on top: block catalogue, exit blocks, signal strength and reason, the vectorised helper, look-ahead checks, the agent door. INFERRED.
2. **QuantConnect, the platform the operator names as a donor, warns against its own framework for his strategy style.** Scalpers with coupled exits fit the "classic" design better. Copy the separation of concerns across units, the router and pods, not the five-model pipeline inside each bot. CHECKED (LEAN overview) + INFERRED.
3. **The industry does not correct for tries, but it does admit the problem.** LEAN caps parameters; NinjaTrader and Nautilus publish backtest-vs-live difference pages. Nobody ships a deflated result. QMX's tries ledger and plateau rules are a real product edge, not a nice-to-have. CHECKED + INFERRED.
4. **For scalpers, the data and fill model decide the result more than the strategy code.**
   - Every vendor documents intrabar guesswork. MT5 even names the "Testing Grail".
   - QMB reads only bid/ask quotes today (good for FX). It cannot yet hold a month of M1 (≈16 GB), and has no perp/futures funding or margin models (01 §0.4–0.5).
   - Instrument spec + data fidelity are the critical path for "any instrument", ahead of strategy features.
   - CHECKED (vendor pages; 01) + INFERRED.
5. **Look-ahead is the bug agents will make most, and the fix is cheap.** freqtrade ships it as a command. QML can ship it as a conformance gate, so an agent-written bot cannot even register with future data in it. CHECKED (freqtrade) + INFERRED.
6. **"No system has a real exit method" is half true.**
   - Jesse and freqtrade ship strong exit *hooks*; MT5 and NinjaTrader ship trailing modules.
   - What nobody ships is exits *measured as blocks*: which exit block, on which instrument and session, gives the best edge per trade. Judge that from MFE/MAE across the same entries.
   - That is where QMX can invent (and it fits QMB's What-If and rerun, 03 row 3).
   - CHECKED + INFERRED.
7. **Anything that manages a trade outside the simulated loop is unprovable.** NinjaTrader's ATM strategies cannot be backtested. If the node ever runs an exit or a safety layer that QMB does not replay identically, its value can never be shown. Keep safety exits as blocks QMB runs too. CHECKED + INFERRED.
8. **A router that cannot be replayed cannot be proven.** freqtrade's dynamic volume pairlist does not work in backtests. The MIS router must decide from recorded states, deterministically, or its contribution stays a belief. CHECKED + INFERRED.
9. **cTrader is now a credible Python platform with a Linux CLI for backtest and optimise.** QMX could run a bot's cTrader twin as an *independent parity check* on QMB's numbers, the way SQ users cross-check exported code. This is optional and needs a cTrader port of the bot, so it is a later idea. CHECKED (cTrader docs) + INFERRED.
10. **Signal expiry is missing from every QMX design I saw.** LEAN's insights expire. A QMX entry signal that rests until filled can fill long after its reason has gone. This matters most for scalpers using limit entries. CHECKED (LEAN) + INFERRED.
11. **The router's "add a market" step needs a warm-up.** LEAN makes alpha models warm indicators on `on_securities_changed`. If the router adds GBPUSD to a unit proven on EURUSD, that seat needs history-based warm-up before trading. That interacts with DEC-0261's "no per-bot warm-up" wording (§4.4). INFERRED.

---

## 6. Configurable numbers seen (starting points only)

| Number | Source | Where it would live in QMX |
|---|---|---|
| Signal strength 0–100, weights 0–1, ThresholdOpen 20 / ThresholdClose 90 (worked example) | MT5 csignal page | combiner block parameters |
| Up to 64 nested signals | MT5 | none (no cap needed; tries count instead) |
| Random delay 0–8 s (90 %), 9–18 s (10 %) | MT5 testing help | QMB latency stress setting |
| Forward split ½, ⅓, ¼ or custom | MT5 testing help | split manifest default choices (CT-12) |
| Genetic population 64–256; 15–31 generations | MT5 optimisation help | B-8 sampler config |
| ≤ 3 optimised parameters (cloud) | LEAN | Lab default parameter cap |
| Max drawdown per security 5 %; portfolio 5 % | LEAN risk models (defaults) | unit safety exit / pod guard defaults |
| ~5 live routes "usually a safe number" | Jesse | node seats per process (guidance) |
| MC candle block = 1 week of M1 (7×24×60) | Jesse | block-bootstrap config |
| StoplossGuard 4 stops / 24 candles → 4-candle lock; MaxDrawdown 20 % / 48 candles → 12-candle lock; LowProfitPairs 2 % / 6 candles → 60 min; Cooldown 2 candles | freqtrade examples | unit bench and loss-point rules |
| Volume pairlist top 20, refresh 1800 s | freqtrade | router candidate count and refresh |
| `prob_fill_on_limit` 1.0 default; `prob_slippage` 0.0 default | Nautilus | QMB fill model defaults |
| cTrader cores default = processors/2 + 1 | cTrader | QMB governor default |

---

## 7. Sources visited (all 2026-10-24)

**MT5 / MQL5:**
- https://www.mql5.com/en/docs/event_handlers
- https://www.mql5.com/en/docs/runtime/testing
- https://www.mql5.com/en/docs/series/bufferdirection
- https://www.mql5.com/en/docs/standardlibrary/expertclasses
- https://www.mql5.com/en/docs/standardlibrary/expertclasses/csignal
- https://www.mql5.com/en/docs/standardlibrary/expertclasses/expertbaseclasses/cexpertsignal
- https://www.mql5.com/en/articles/275
- https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants
- https://www.mql5.com/en/docs/onnx
- https://www.mql5.com/en/docs/python_metatrader5
- https://www.metatrader5.com/en/terminal/help/algotrading/testing
- https://www.metatrader5.com/en/terminal/help/algotrading/optimization_types
- https://www.metatrader5.com/en/terminal/help/trading/general_concept
- https://www.metatrader5.com/en/terminal/help/trading_advanced/custom_instruments

**cTrader:**
- help.ctrader.com/ctrader-algo/: python-basics, third-party-python-packages, how-tos/cbots/cbot-lifecycle, create-a-cbot, create-a-cbot-in-5-mins, backtest-a-cbot, backtest-a-trading-bot, optimise-a-trading-bot, documentation/cbots/cbot-bar-events, cbot-advanced-operations, references/General/Robot, Robot/OnStart, MarketData/MarketData, Symbols/Symbol, Symbols/GetSymbols, Plugin/Optimization/OptimizationSettings, guides/backtesting-custom-data-sources, faq
- https://help.ctrader.com/ctrader-cli/optimisation/
- https://blog.ctrader.com/python-opens-new-earning-opportunities-in-ctrader-store/

**NinjaTrader:**
- ninjatrader.com/support/helpguides/nt8/: onstatechange, understanding_the_lifecycle_of, multi-time_frame__instruments, managed_approach, unmanaged_approach, strategy_analyzer, walk_forward_optimize_a_strate, understanding_historical_fill_, discrepancies_real-time_vs_bac, masterinstrument, merge_policy, editing_instruments, strategy_builder, strategybuilder_condition_builder, using_atm_strategies, atmstrategycreate
- the NT8 help-guide PDF (release notes on instruments and trading hours)

**QuantConnect LEAN:**
- quantconnect.com/docs/v2/: writing-algorithms/algorithm-framework/overview, alpha/key-concepts, risk-management/supported-models, portfolio-construction/supported-models, reality-modeling/key-concepts, securities/key-concepts, consolidating-data/getting-started, optimization/walk-forward-optimization, cloud-platform/optimization/getting-started, optimization/parameters, ai-assistance/mcp-server/key-concepts
- https://github.com/QuantConnect/mcp-server

**Jesse:**
- docs.jesse.trade/docs/: strategies/entering-and-exiting, strategies/events, routes.html, optimize/, optimize/hyperparameters, research/monte_carlo, monte-carlo/, monte-carlo/candles-based, monte-carlo/candle-pipelines

**freqtrade:**
- freqtrade.io/en/stable/: strategy-customization, strategy-callbacks, plugins (pairlists, protections), hyperopt, lookahead-analysis

**NautilusTrader:**
- nautilustrader.io/docs/latest/concepts/: strategies, instruments, actors, live, backtesting (with the full concepts navigation read in the browser), backtesting/apis-and-runs, backtesting/data-and-venues, backtesting/bar-execution, backtesting/fill-models

**QMX (read-only):**
- tracker/risk-sizing/wayfinder/MAP.md and tickets/platform-study.md
- tracker/risk-sizing/research/01-ground-truth.md, 02-instruments-and-traders.md (headings), 03-strategyquant.md
- `docs/components/qml.md`, `qmb.md` (main)
- `workroom/risk-lab-2026-10-05/seeds.md`, `decisions.md`, `HANDOFF.md`
- Code on plan/agent-system:
  - `qml/src/qml/protocol/{contract,factory,intents}.py`
  - `qml/src/qml/declaration/parameters.py`
  - `packages/qmf-core/src/qmf/core/identity.py`
  - `packages/qmf-indicators/src/qmf/indicators/{arithmetic,catalog}.py`
  - directory listings of `qmb/src/qmb/{doors,execution,optimize,sweep}` and `qml/src/qml/conformance`
