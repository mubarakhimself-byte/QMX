---
ticket: strategyquant-family
title: StrategyQuant family as the anchor for testing, QMB and the Lab
date: 2026-10-24
author: opus research agent (read-only; this file is the only write)
method: live pages read fresh in the built-in browser (nav bars, "Show more features" expanders, hidden tab panels, sitemap), Exa fetch for long doc pages and YouTube transcripts, then QMX docs and code on plan/agent-system to map. The 2026-09-14 donor notes and UI-BACKLOG were used only as a cross-check at the end (section 8).
labels: CHECKED = seen on a live page or transcript (URL given). PRACTITIONER = a user's own report (forum, review, video). INFERRED = my reasoning, not a source.
numbers: every number in this file is a starting point and must be configurable (UI-editable), never a baked default.
---

# StrategyQuant family: what it is, how people really use it, and what QMX should take

## 0. The short version

1. **StrategyQuant shipped an agent in 2026 that looks like QMX's Copilot plan.** "Q" lives inside SQX, has plugins made of skills, commands, sub-agents and standing rules in plain Markdown folders, a four-layer memory ("AI Brain"), a research ledger (`/recall`, `/journal`), an overnight auto-research loop, fenced file access, snapshots before every write, an audit log, and a UI-driving lock the agent cannot lift itself. SQX also ships an MCP server (6 tools). CHECKED: https://strategyquant.com/doc/q-introduction/ , https://strategyquant.com/doc/q-extending/ , https://strategyquant.com/doc/strategyquant/mcp-integration/
2. **SQ's robustness tests are a funnel of pass/fail gates with thresholds like "≥ 80 % of the original".** Practitioners report that the funnel does not reliably pick strategies that survive unseen data: one user ran the experiment many times and found no lift. Another says fewer than 10 % of fully tested strategies trade live like their backtest. PRACTITIONER: https://strategyquant.com/forum/topic/robustness-tests-do-they-really-work/ , https://strategyquant.com/forum/topic/strategyquant-success/
3. **SQ has no correction for the number of tries.** It generates millions of candidates and keeps the luckiest. Nothing in the product deflates the result for the size of the search: no PBO, no deflated Sharpe, no count of tries carried with the strategy. CHECKED by absence across the docs tree (section 1.3). Its users say it plainly: "searching millions of combinations and keeping the luckiest one is literally the job of SQX if you don't know what you're doing". PRACTITIONER: Ali Casey, https://www.youtube.com/watch?v=EZy4k1v2IwI . QMX has slots for this correction but has not built it (PBO/CSCV deferred in `qmb/src/qmb/robustness/summary.py`). This is the one place QMX can be clearly better.
4. **The tests that worked in a practitioner's controlled demo were SPP and the Walk-Forward Matrix, not Monte Carlo.** A strategy built to be overfit passed 70,000 Monte Carlo simulations across 7 methods and 2 tools. SPP and WF Matrix killed it in minutes. Monte Carlo is still useful for one job: sizing the capital and the risk of ruin. PRACTITIONER: https://www.youtube.com/watch?v=EZy4k1v2IwI (published 2026-09-24)
5. **QuantAnalyzer's "Compare Results" (live vs backtest, mass-compare by magic number) and "Predict & Verify" (live path against the Monte Carlo cone) are the most useful pieces for QMX's unit idea.** They match the existing operator rule "trust is judged against each bot's own Monte Carlo worst run". CHECKED: https://strategyquant.com/quantanalyzer/compare-results/ ; `workroom/risk-lab-2026-10-05/decisions.md:82`
6. **QMB already has more of SQ than the operator may think.** It already has: What-If trade-list filters (`analysis.project`: days/hours/session/max_trades/include/exclude), a stable-region versus lone-spike flag (`optimize/sensitivity.py`), an instrument × timeframe × parameter grid (`sweep/axes.py`), trade shuffle, candle perturbation, walk-forward, and a pre-build rule-significance gate. Missing: the funnel runner, multi-market as a gate, SPP medians, the WF Matrix, the Monte Carlo variants added in 2025-26, a portfolio combiner (`analysis/deferred.py` refuses it as F07), the live-vs-backtest compare, and the tries correction.

---

## 1. Product map (as the site and docs present it)

### 1.1 Top navigation of strategyquant.com (CHECKED, browser, https://strategyquant.com/)

```
StrategyQuant (site)
├── Products
│   ├── StrategyQuant (SQ X)           https://strategyquant.com/
│   ├── Q AI Assistant                  https://strategyquant.com/q-ai-assistant/   (+ /pricing)
│   ├── AlgoCloud                       https://algocloud.com/   (separate site, cloud execution)
│   ├── QuantAnalyzer                   https://strategyquant.com/quantanalyzer/
│   └── QuantDataManager                https://strategyquant.com/quantdatamanager/
├── Free Course (YouTube playlist)
├── Company: About, Contact, Partner with us, Team
├── Blog /blog · Documentation /doc · Codebase /codebase · Shared /shared · Forum /forum (now READ-ONLY; community moved to Discord + YouTube)
└── Support, Login, 7 languages
```

The SQ X product sub-nav: Overview · Features · Pricing · Download · Stories · More → Data Subscription, FAQ, StrategyQuant for Business (MQL Market sellers), What's new, Learning (docs), Community (forum). CHECKED.

The forum banner reads: "The forum is now a read-only archive … Our community lives on Discord and YouTube". CHECKED: https://strategyquant.com/forum/topic/robustness-tests-do-they-really-work/

### 1.2 SQ X feature groups (CHECKED, https://strategyquant.com/features/ including the three hidden tab panels and "Show more features")

| Group (site's own tab) | Features listed |
|---|---|
| **Strategies creation / generation** | Integrated free data (Dukascopy forex, Yahoo stocks; paid futures/equities); a fast own backtest engine with real-tick precision ("thousands of backtests per second", "tens of thousands strategies per hour"); no-code; multi-TF and multi-symbol strategies (trade H1, confirm on H4/D1; trade EURUSD, read GBPUSD/USDCHF); standard indicators + candle patterns, "4 types of trade entries and 6 types of exits"; custom blocks (AlgoWizard) or Java snippets; full source export to NinjaTrader, MT4, MT5 (hedging and netting), TradeStation, MultiCharts, JForex |
| **Overfitting protection & robustness** | Cross-checks you can switch on and off inside the build; "two separate Monte Carlo tests with 9+ different simulation types"; WF analysis, WF optimization, WF Matrix ("cluster analysis"); 3D optimization charts; System Parameter Permutation + Optimization Profile (Walton, Pardo); advanced filtering "for virtually every metric … including optimization and Walk-Forward"; customizable fully automatic workflows (Builder or Custom Projects) |
| **Advanced and unique features** | Generate from your own template (Random placeholders); fuzzy logic ("what percentage of the conditions has to be true"); ATM scaling-out with multiple exits ("a very simple ATM configuration can improve 10-30% strategies"); pluggable Custom Analysis (can call Python) |
| **Rest of features** | Integrated data download; portfolios with several portfolio models; Improver ("improve your existing strategies or only their parts"); Retester and Optimizer modes ("re-run all the robustness tests"); trades on chart; unlimited OOS periods filtered separately; MAE/MFE/daily equity; Fit to portfolio; "Automatic recognition of strategy problems"; plugin/snippet architecture; one environment (SQ, QuantAnalyzer, QuantDataManager, AlgoWizard) |

Homepage pitch: a 4-step loop (Build with ML / genetic programming → Quality and robustness tests → Trade live or demo through exported code → Build a portfolio). CHECKED: https://strategyquant.com/

### 1.3 Documentation tree (CHECKED, browser + live sitemap `/doc-category-sitemap.xml`, `/doc_new-sitemap.xml`)

Doc products: Q - AI assistant · StrategyQuant · QuantAnalyzer · QuantDataManager · EA Wizard · CLI - Command line · Programming for SQ.

SQ X categories: Introduction · Installation · Quick Start · Program Screens (Progress Layout, Results, Data Manager, Full Settings) · Functions · How to. The "new docs" set (2025-26, by page slug):

```
Builder: builder, what-to-build, building-blocks, genetic-algorithm-options, trading-options, data-settings,
         money-management, atm, cross-checks, ranking, notes, parts-to-improve, templates, algowizard
Results: overview, list-of-trades, strategy-analysis-metrics, equity-chart, strategy-correlation,
         trade-analysis, strategy-config, source-code, trades-on-chart
Modules: retester, optimizer, portfolio-master, portfolio-composer, databanks
Cross-checks: cross-checks-robust-testing-overview, in-sample-out-of-sample-is-vs-oos-testing,
         what-if-simulation, monte-carlo-tests, higher-backtest-precision, backtest-on-additional-markets,
         sequential-optimization-cross-checks, opti-profile-sys-param-permutation,
         walk-forward-optimization-cross-checks, walk-forward-matrix, description-of-advanced-walk-forward-values
Optimization: simple-optimization, sequential-optimization-optimization, walk-forward-optimization-optimization
Custom projects: what-is-a-custom-project, how-to-create-a-workflow, tasks, recommended-workflow-using-custom-projects
Portfolio: automatic-portfolio-construction-mpt
Other: custom-analysis, atm-multiple-exits-generation, sq4business-mql-market, metatrader5-data-import,
       results-plugins, mcp-integration, q-introduction, q-extending
CLI: project / databank / symbol / instrument / data / tools / run / gui (remote web GUI) / waitfor / deletefile / execute / exit
Programming: snippets (indicators, signals, databank columns, MC methods, what-if, MM), calling Python, public API javadoc,
       running backtests/optimizations programmatically, save databank results to DB
```

Doc quality is uneven. CHECKED: the live Monte Carlo page still contains an editor's note, "DOES THIS REQUIRE TICK DATA????" (https://strategyquant.com/doc/monte-carlo-tests/, updated 2025-08-29). The WF Matrix page was last updated 2015. The "supported platforms" page lists MT4/MT5/TradeStation/MultiCharts/PseudoCode. The features page also lists NinjaTrader and JForex. CHECKED: https://strategyquant.com/doc/supported-platforms/ against https://strategyquant.com/features/

### 1.4 Release cadence, recent builds (CHECKED, https://strategyquant.com/whatsnew/ and the `?date=` pages)

| Build | Date | What matters for QMX |
|---|---|---|
| 141 | Nov 2024 | Portfolio Composer (weights); broker profiles; Portfolio Master gains MM and overlap filters; max number of exit types; better % risk on MT5 (currency conversion, contract size by instrument type) |
| 142 | Apr 2025 | Automatic weight calculation in Composer; VWAP; "Filter by correlation" button on the databank; high-priority CPU mode |
| 143 | Jan 2026 | AlgoWizard rewritten; **AI in AlgoWizard** (text → strategy, improve existing); **ATR risk-based sizing**; robustness cross-checks for the cloud engine; **Auto Retest task now multi-symbol and multi-timeframe**; SQX vs MultiCharts/TradeStation indicator parity to 6 decimals |
| 144 | May 2026 | **Custom Results plugins in HTML/JS, "vibe-coded" with Claude Code**; Volume Profile/TPO; **MCP server v1**; direct MT5 data import; ARM builds; DataManager CLI; "Trades by Close Type" chart; **databank Correlation Filter task (daily P/L)**; **new MC methods: MACHR block randomization, SimulateParameterJitter, RandomlyDegradeExecution** |
| Q | 2026 (doc updated 21 Oct 2026) | Q AI assistant for SQX now. Planned next: QuantDataManager (Q4 2026), QuantAnalyzer (2027), AlgoCloud (2027). CHECKED: https://strategyquant.com/q-ai-assistant/ |

### 1.5 QuantAnalyzer navigation (CHECKED, browser, https://strategyquant.com/quantanalyzer/)

Overview · Functions → Extensive detailed reports · What If scenarios · Money Management Simulator · Monte Carlo analysis · Equity control simulation · Portfolio Master · Compare Results · Extendability · MT4 QuantAnalyzer · Pricing · Download · What's new (4.9.4, Mar 2026: loaders for TradingView, MT5 statements, MyFxBook, general CSV with MAE/MFE).

Free-version limits: MM and Equity control show only 30 % of trades; Portfolio Master max 4 strategies; Compare Results only the first 50 trades. CHECKED.

### 1.6 QuantDataManager navigation (CHECKED, browser, https://strategyquant.com/quantdatamanager/)

Overview · Functions · Pricing (Free with ads; Pro $49 lifetime, adds own CDN plus "verified downloads") · Download · What's New. Sources: Dukascopy, Yahoo, Darwinex, Binance (spot, plus coin-m and USDT futures since QDM build 125, Dec 2025), Bitfinex, Coinbase, Poloniex, File import. In-app tabs (from the official video): Dukascopy / old tick downloader / CSV import / Darwinex / crypto / Yahoo · Export · Clone · View & Analyze · Instruments and Sessions · Broker profiles · Help · Log. CHECKED: https://www.youtube.com/watch?v=J40dT7TW5BE (transcript)

### 1.7 Other products

- **AlgoCloud**: cloud no-code stock-picker and single-asset strategies, executed "directly on your brokerage account. No VPS" (IBKR, Alpaca, RoboForex, TradeStation named in the disclaimer). It is SQ's equivalent of a trading node. CHECKED: https://algocloud.com/
- **EA Wizard / AlgoWizard**: the no-code editor. Rebuilt in 143, with AI.
- **Data subscription**: US equities (split/dividend back-adjusted) and US futures, EOD 30+ years, 1-minute 10+ years, continuous futures (rolled on open interest). "Data can be used only within StrategyQuant, they cannot be exported." CHECKED: https://strategyquant.com/data-subscription/

### 1.8 Pricing, context only (CHECKED, https://strategyquant.com/pricing/ , https://strategyquant.com/q-ai-assistant/pricing)

- SQ X is a lifetime licence, paid as 12 monthly payments or once. The page shows Starter $129/mo, Professional $149/mo (struck price $175), Ultimate $290/mo (struck price $420). I did not capture the one-time price toggle.
  - Starter = Builder, Retester, Improver, *without* advanced robustness tests, Optimizer, or Custom Projects.
  - Professional adds those three.
  - Ultimate adds QuantAnalyzer Pro, Portfolio Master and Composer, ATM, lifetime data, and the Seasonal Toolbox.
  - **The robustness funnel is a paid upsell.**
- Q credits: Basic $20/mo = 4,500 credits; Pro $50 = 12,500; Max $200 = 60,000. Top-up $5 per 1,000. Licences include 1,200 / 2,400 / 6,000 welcome credits. Typical costs: explain a strategy 31 credits, apply a Builder config 51, review a backtest 81, an autonomous research run "hundreds".

---

## 2. Feature by feature: what it does, how users use it, strengths, weaknesses

### 2.1 Builder: random and genetic generation, building blocks, templates

**What (CHECKED).**
- Two build modes: random generation, and genetic evolution. Genetic options cover population, generations (doc says 5–100 recommended; "restart after stagnation" beats more generations), crossover, mutation, islands with migration, fresh blood, and decimation. https://strategyquant.com/doc/genetic-algorithm-options/
- Templates are strategies with Random placeholders. https://strategyquant.com/features/
- "What to build" sets the strategy type, direction, symmetric or independent rules, condition count, period and shift ranges, and required SL/PT.
- Multi-TF and multi-symbol charts.
- Fuzzy logic: a percentage of the conditions must be true.
- ATM scale-out exits.
- Improver: rebuild only some parts of an existing strategy.
- AlgoWizard AI (b143): text → strategy.

**How users use it (PRACTITIONER).**
- Ali Casey (StatOasis) Builder walkthrough: start from shipped templates (trend-following, mean-reversion, daily, fuzzy). Each template mainly swaps the building-block set and the what-to-build tab. In one default run, **63 % of generated strategies were rejected by the automatic "too many trades closing at the same bar" filter**. He suggests turning off databank syncing at first "because there is no point in syncing a thousand strategies when they are all garbage". https://www.youtube.com/watch?v=z81pH7dVTkc (transcript, no timestamps in source)
- Lisa Forex explains genetic evolution as population → crossover of the best → mutation → islands to escape local optima. https://www.youtube.com/watch?v=fLInoRgsDuQ
- Testimonial on the homepage: a user filters for PF ≥ 1.6, win rate ≥ 65 % and Ret/DD ≥ 3, and finds "about one strategy that 'works' in every million iterations … about 6 potential winning strategies every 24 hours". CHECKED that the quote is on https://strategyquant.com/ . The selection-bias reading is INFERRED: that ratio is pure data mining.
- SQ support's own advice on overfitting: "focus on strategy logic meaning there should be at least 'an idea' why the strategy should work … Relying strictly on randomly made strategies can work as well but the success rate is lower". https://strategyquant.com/forum/topic/handling-overfitting-in-strategyquant-generated-strategies/ (admin reply, 2025)

**Strengths.**
- Very fast search across structure (which blocks, which comparisons), not just across numbers.
- Templates give the user control over the skeleton.
- The automatic problem filters drop broken strategies early.

**Weaknesses.**
- PRACTITIONER: genetic search uses IS + OOS fitness when "additional markets" is on, so OOS stops being out of sample ("OOS is absolutely useless in the builder"). https://strategyquant.com/forum/topic/fake-backtest-is-oos-overfitting/
- SQ's own docs say genetic crossover cannot keep template constraints beyond generation 0. (The 14 Sep notes cite this from the random-groups page.)
- PRACTITIONER: "99 % of strategies are rubbish"; "overfitting is the way of genetic building program". https://www.prorealcode.com/topic/anyone-tried-strategy-building-software/

### 2.2 Ranking, fitness, filters, databanks ("the fitness bank")

**What (CHECKED, https://strategyquant.com/doc/ranking/).**
- The databank keeps the top N. It can stop when full.
- Fitness is a normalized 0–1 score from one metric or a weighted custom formula. The doc itself warns: "Overcomplicating the fitness function may result in conflicting objectives".
- Fitness can be computed on Main data, on a Portfolio (all symbols), or on an **Existing Portfolio**: the new strategy's fitness is the fitness of the combined portfolio.
- Automatic filters: no trades, unprofitable, no filled orders.
- Custom filters are scoped to IS / OOS / RT (robustness tests) / P (portfolio), money/%/pips, and long/short/both.
- A correlation filter against the existing portfolio (by P/L per day/week/month, with a minimum number of overlapping points).
- Dismiss similar strategies: same trade count, net profit and DD within a tolerance (14 Sep notes).
- b142 added a "Filter by correlation" button; b144 added a Correlation Filter task in Custom Projects.

**How users use it (PRACTITIONER).**
- Filters are the main lever: users stack Ret/DD, PF, trade-count and OOS-ratio filters. Example: a shared NASDAQ workflow keeps strategies whose OOS keeps 80 % of IS performance. https://strategyquant.com/shared/simple-workflow-on-nasdaq-is-and-oos-verification-for-multi-timeframe-strategy/
- Ali Casey reads the Builder's rejection statistics (which filter killed how many) to retune the build.

**Strengths.**
- "Fit to existing portfolio" is the right idea. It judges a new strategy by what it adds, not by itself.
- Filter scopes (IS/OOS/RT/P) are clean.

**Weaknesses.**
- INFERRED: a stored 0–1 fitness invites ranking on one number. The databank keeps "the best", which is the luckiest by construction.
- INFERRED: top-N capacity silently throws away the search history, so the count of tries is lost.

### 2.3 Robustness tests (cross-checks)

The funnel (CHECKED, https://strategyquant.com/doc/cross-checks-robust-testing-overview/):
- Tests run cheap → expensive, grouped as Basic / Standard / Extensive.
- A strategy that fails one test is dropped, and the later tests never run.
- Example funnel: fast "Selected timeframe" build → global filters → higher precision → MC trade manipulation → additional markets → optional MC retest.
- Cost warning: "0.2 seconds … might require 10–200 seconds" per strategy.

| Test | What it does (CHECKED) | User practice / critique |
|---|---|---|
| **Higher backtest precision** | Retest the same strategy at M1, real tick with custom spread, or real tick with real spread. Filter example: precision Net Profit ≤ 80 % of the original → drop. https://strategyquant.com/doc/higher-backtest-precision/ | Used early to catch stop/limit-order artefacts. Matters most for scalpers (INFERRED) |
| **What-If simulation** (b129, came from QuantAnalyzer) | Applied to the existing trade list, no new backtest. Options: random skip, weekdays/hours only, partial execution, omit the top x % of profitable trades. Filter example: What-If NP < 80 % of original → drop. https://strategyquant.com/doc/what-if-simulation/ , https://strategyquant.com/doc/strategyquant/what-if-simulations/ | An SQ admin says filtering "bad days" after the fact is pointless ("you never know in advance what daily PnL will be"). A rule that wins under What-If must be hand-coded into the strategy (MQL or AlgoWizard) and retested. PRACTITIONER and admin, comments on that page (2020, 2024) |
| **MC trade manipulation** | Randomize trade order (exact or resampling), randomly skip trades. Confidence levels 50–100 (11 fixed levels). Example: "95 % confidence $3,943 vs original $6,990". https://strategyquant.com/doc/monte-carlo-tests/ | Ali Casey: a shuffle cannot change total profit, so every path ends at the same point. A strategy with a high average trade relative to its standard deviation passes **every** MC method by construction. PRACTITIONER: https://www.youtube.com/watch?v=EZy4k1v2IwI |
| **MC retest methods** | Each simulation is a full backtest: randomize strategy parameters (probability, max % change, e.g. 60 ± 10 % → 54–66), randomize history (OHLC by % of ATR), randomize starting bar, randomize spread/slippage. Same page | The same demo: 10,000 retests barely flinched on the overfit strategy |
| **New MC methods (2025-26)** | **MACHR block randomization**: bootstrap blocks of consecutive trades (default 5, range 2–50) to test dependence on the regime sequence. **Randomly degrade execution**: a random subset of trades gets a worse close, up to x % of each trade's range. **SimulateParameterJitter**. CHECKED: https://strategyquant.com/codebase/monte-carlo-machr-block-randomization/ , https://strategyquant.com/codebase/monte-carlo-randomly-degrade-execution/ | Community-built (clonex / Ivan Hudec), shipped in b144 |
| **Backtest on additional markets** | Retest on other symbols or timeframes. "A robust strategy does not have to perform equally well on all markets"; moderate profit or slight losses are acceptable. Filter example: PF of EVERY additional market < 1 → drop. https://strategyquant.com/doc/backtest-on-additional-markets/ | PRACTITIONER: turning this on inside the Builder makes genetic fitness use IS+OOS, which leaks OOS (forum above). This test is SQ's version of the operator's domain expansion, but it is used as a gate, not as a map |
| **Opt. Profile / SPP** (b114) | Needs an optimization run first. Optimization Profile (Pardo): share of profitable runs, average > 0, uniform distribution, top result within 1 SD of the average, stable 3D surface. **SPP (Walton, 2014 Wagner award)**: judge the strategy by the **median** across all parameter sets, not by the best one. Medians can be databank columns and filter inputs. Works best with 2–3 parameters. https://strategyquant.com/doc/opti-profile-sys-param-permutation/ | SQ support recommends SPP to pick a parameter set inside a stable area (forum 2025). Ali Casey: SPP asks whether "your strategy [is] standing on a plateau … or balancing on … a needle" |
| **Sequential optimization** | One parameter at a time, pick the middle of the stable area (14 Sep notes, doc slug `sequential-optimization-cross-checks`) | Rarely discussed by users |
| **Walk-forward optimization** | Reoptimize on rolling IS, trade the OOS. WF values: **WF Stability** (OOS vs IS, normalized per day, e.g. NP stability > 60 %), **WF Score** (WF vs original non-optimized; > 100 % means reoptimizing helps), max DD in one run, max share of profit from one run, min trades in one run, % profitable runs. https://strategyquant.com/doc/description-of-advanced-walk-forward-values/ | Forum debate: WFO "relies on constant optimization … you're effectively working with a completely different strategy every time". Others say it has value if done carefully, and warn the WF Matrix can "over-optimize the WF process itself". PRACTITIONER: https://strategyquant.com/forum/topic/walk-forward-optimization-vs-robustness/ |
| **Walk-Forward Matrix** | A grid of WF runs × OOS % (e.g. runs 5–15 step 2 × OOS 20/30/40 %). Each cell passes when a configurable share of score components pass (e.g. 80 %). Robust = at least one 3×3 block with ≥ 7/9 passing. Pick the middle cell as the reoptimization period. A "Simulation" WF mode is 10–100× faster. https://strategyquant.com/doc/strategyquant/walk-forward-matrix/ (page dated 2015) | Ali Casey wants a block of cells, not a peak: "a plateau, a plain level. We don't want one peak"; 0 of 16 cells passed on his overfit strategy |
| **Multiple OOS periods** | Unlimited OOS slices, each filtered separately. https://strategyquant.com/features/ | Shared workflows use two OOS periods plus slippage plus a second timeframe (Gold H1 workflow) |
| **Results plugin "Robustness Scorecard"** (b144 example) | Scores a strategy 0–100 across six pillars, with a **low-trade gate**: under 100 trades caps the sample pillar at 30. Built by Claude Code from a shipped CLAUDE.md. https://strategyquant.com/doc/strategyquant/results-plugins | A composite score, written by an AI, from databank stats only (INFERRED: same blind spots) |

**The hardest practitioner evidence on whether the funnel works.**
- rsantinikk's protocol:
  1. Build 1000 strategies on 2018–2023.
  2. Measure what share are profitable on unseen 2024 (say 30 %).
  3. Apply a robustness test on 2018–2023 only (e.g. WF Matrix).
  4. Check whether the survivors beat 30 % on 2024.
  Result: "I have performed this procedure many times … the result was always the same: the 'Robustness Test' was not able to select the strategies that were most likely to be profitable in 'Unseen' periods." PRACTITIONER: https://strategyquant.com/forum/topic/robustness-tests-do-they-really-work/ (2025)
- His protocol is a **meta-test of the test**. INFERRED: QMX should run exactly this protocol as a standing QMB job (section 4, H1).
- Another user: "only a small proportion trade as per the backtests (less than 10%) … I can't figure out which systems work live even after selecting only the ones which pass all the robustness tests without doing this incubation phase". He runs about 200 systems on demo and live across 30+ broker accounts and swaps them by magic number. PRACTITIONER: https://strategyquant.com/forum/topic/strategyquant-success/
- A counterexample from the same forum: one user's best live portfolio was 96 strategies on H4 with **no** OOS and **no** robustness tests. He built them with "ridiculously high spreads" over the longest data. INFERRED reading: cost stress plus long history plus diversity across many pairs did the work that the gates did not. https://strategyquant.com/forum/topic/fake-backtest-is-oos-overfitting/

### 2.4 Optimizer

- **What (CHECKED via the doc tree, details in the 14 Sep notes):** Simple optimization (start/stop/step, or genetic), sequential, walk-forward, WF Matrix, 3D surfaces. Recommended parameters only: periods, multipliers, SL/PT. The Optimization Profile tab appears automatically.
- **Users:** a final "optimize once on all data after OOS survived" camp versus a "reoptimize periodically" camp (forum above). PRACTITIONER.
- **Weakness:** INFERRED. The optimizer and the generator are two separate searches, and neither records how many trials were run toward the final pick.

### 2.5 Custom Projects (workflows) and Auto Retest

**What (CHECKED, https://strategyquant.com/doc/tasks/).** 17 task types:
1. Build
2. Retest
3. Automatic Retest (same config, new data; b143: multi-symbol and multi-TF)
4. Optimize
5. Stop & Start (stop on count or time, start another project)
6. Filter (delete/move/copy between databanks)
7. Go To (loop back, e.g. "Final < 100 → Build")
8. Notification (in-app or email)
9. Create Portfolio
10. Clear Databanks
11. Load from Files
12. Save to Files
13. Call External Script
14. Delete a File
15. Wait for User/File
16. Update Data
17. Log Databank Stats

Each task has a source and a target databank. There is also a "Custom Analysis" task (per strategy or per databank, can call Python) and the b144 Correlation Filter task.

**Users (PRACTITIONER).**
- "Best feature for StrategyQuant X, it's Workflow Automation!" https://www.youtube.com/watch?v=BqjUFZTG1DA
- Shared `.cfx` workflows are the main way people learn: Gold H1, NASDAQ IS/OOS, TradeStation futures. Before Auto Retest, one user had built "13 or 14" separate `.cfx` files, one per robustness test, and ran them by hand. https://strategyquant.com/shared/automatic-retest/
- Crashes on heavy workflows ("always crashes in the M30 or H4 test … SQX doesn't respond"). https://strategyquant.com/shared/algolab-workflow-for-gold-h1-updated-2024/
- Thomas Nickel (10+ years on SQX) built a "toolbox" that simulates whole workflows end to end. His finding: "it has usually shown me that the workflows don't work … So far I have only found one workflow that is reasonably good: the GBPJPY H1 workflow". Quoted in the robustness forum thread above.

**Strengths.** A visible, repeatable pipeline with loops and stop rules. Shareable as one file.

**Weaknesses.**
- No versioned link from a final strategy back to the exact workflow, seed and count of tries (INFERRED).
- Long chains are fragile on desktop hardware (PRACTITIONER).

### 2.6 Portfolio: Portfolio Master, Portfolio Composer, Fit to portfolio

- **Portfolio Master** (QA and SQX), CHECKED: https://strategyquant.com/quantanalyzer/portfolio-master/
  - Brute force or genetic search over combinations (pick k of N strategies or markets).
  - Correlation cap, sector caps, metric filters.
  - In genetic mode, an OOS part the search must not see.
  - Custom ranking and correlation snippets.
- **Portfolio Composer** (b141): weights per strategy. b142 added automatic weights: Markowitz frontier by Sharpe, Ret/DD, or CAGR vs max DD, from 500–1000 simulated weight sets, with VaR and expected shortfall. The doc assumes normal returns for VaR (CHECKED, https://strategyquant.com/doc/automatic-portfolio-construction-mpt/).
- **Users** (PRACTITIONER, tradingtact.com, https://tradingtact.com/diversified-portfolio/):
  - Pool: 40 M30 strategies on 4 pairs → pick 8, at most 2 per pair. Correlation by weekly P/L, cap 0.4. OOS 30 %. PF ≥ 1.5 on OOS.
  - Brute force over 76 M combinations took 69 min. A 10-minute genetic run found 6 of the brute-force top 10.
  - Warning: "Correlations do shift over time … During financial crises … prevailing correlations are likely to break down."
- **Weaknesses** (INFERRED):
  - Choosing k of N on the same history is another search with its own selection bias, and nothing corrects for it.
  - Markowitz on backtest returns over-trusts the backtest.
  - A static correlation hides the "not correlated right now" problem the operator raised in his seeds.

### 2.7 Money management

CHECKED (https://strategyquant.com/doc/money-management/): fixed size (recommended during generation), fixed amount, risk fixed % of account, risk fixed % of balance, stocks size by price, crypto size by price, simple martingale. b143 added ATR risk-based sizing. Sizing is set per strategy, and the exported EA carries it.

Weakness (INFERRED): sizing is a property of the exported robot. Nothing adapts it from the robot's own live record. QMX's unit idea goes further.

### 2.8 Results and the custom Results plugins

- **Results tabs** (CHECKED, doc tree): overview, list of trades, metrics, equity (with MAE/MFE), correlation, trade analysis, config, source code, trades on chart, WF and optimization profile.
- **b144 Results plugins** (CHECKED, https://strategyquant.com/doc/strategyquant/results-plugins):
  - Each plugin is a single HTML/JS (Vue) file talking to SQX through `postMessage` (`GET_STATS`).
  - SQX ships a `CLAUDE.md` for Claude Code to build plugins.
  - Pro tier and above.
  - Plugins can call `AI_COMPLETE` to ask Q one question, billed in credits.
- This is SQ's version of QMX mini apps. INFERRED.

### 2.9 Q AI assistant, AlgoWizard AI, MCP

**Q (CHECKED, https://strategyquant.com/doc/q-introduction/ , https://strategyquant.com/doc/q-extending/).**
- **Eight areas:** Text to Strategy · Analyze & Research · Build & Automate Workflows · Market & Data Analysis · Custom Analysis Tabs & Code · Plugins & Skills · AlgoCloud · Learn SQX & Trading.
- **Behaviour:**
  - It plans, calls tools, uses sub-agents, and shows each step with tool-call counts and a Stop button.
  - It "computes, it does not estimate", using shipped Python and pandas.
  - It schedules its own continuation for overnight research, with user-set limits ("at most three rounds, stop at 7 a.m.").
  - Licensed data never leaves the app.
- **Memory ("AI Brain"):** long-term memory, a daily ledger, a knowledge base (including the "trading ledger of verdicts" and rejected ideas), and learned skills (optionally held for approval). All plain Markdown, editable. "Reject an idea and give a reason, and it will not be proposed back to you next month".
- **Control:**
  - Files are fenced to the data root.
  - UI driving is locked until the user types `/drive-ui`; Q "cannot unlock it for itself".
  - Every write is snapshotted. There is an audit log.
  - Nothing goes into databanks without the user's say-so.
- **"Before you trust an answer" checklist:**
  1. Numbers come from a run you can point at.
  2. Period and market are the ones you meant.
  3. Judged out of sample.
  4. Comparisons use real trade lists, not databank rows.
  5. Costs and slippage were in the test.
  6. Verify installation claims.
  7. Ask for the step that produced the claim.
- **Extending Q:**
  - 18 shipped plugins under `user/extend/AIPlugins/`. Each has `plugin.json`, `skills/`, `commands/`, `agents/` (optionally with a restricted tool allow-list), and `rules/` (always on). Drop a folder in and it is live on the next message.
  - `/make-plugin` turns a pasted protocol into a plugin.
  - Java "AI tools" become callable as `ext_*`.
  - Shipped skills include `sqx-project`, `quant-research` (A/B tests on a setting, portfolio pre-checks, overnight digests), `auto-research` (hypothesis → build → evaluate → journal loop) and `trading-memory` (`/recall`, `/journal`).
  - Standing rules: `oos-discipline` (no judging on IS alone), `confirm-before-applying-configs`, `ui-only-on-request`.
- **Pricing:** credits (section 1.8). Models from several providers, chosen per message. The 2025 beta used "ChatGPT and Claude". CHECKED: https://strategyquant.com/blog/strategyquant-ai-assistant-beta-now-available-full-video-tutorial/

**MCP v1 (CHECKED).** `list_projects`, `list_strategies`, `list_databanks`, `get_strategy_stats`, `run_project`, `stop_project`, served at `http://localhost:8080/mcp`. The docs show it working with Claude Desktop and Claude Code. https://strategyquant.com/doc/strategyquant/mcp-integration/

**How users use the AI (PRACTITIONER and vendor demos).**
- In the vendor demo, the AI builds a SuperTrend + daily-high strategy and the presenter tests it on gold, NASDAQ, US30, US500, EURUSD and USDJPY. He calls it "quite robust as it is profitable without changing parameters across multiple markets". https://strategyquant.com/blog/new-ai-assistant-for-all-trading-platforms-see-it-build-a-strategy-in-seconds/ (transcript)
- INFERRED critique: that is cross-market eyeballing after the fact, with no count of tries and no costs check stated.
- Ali Casey reviewed the v143 AI builder (building demo at 13:42). Secondary summary: https://strategydecoder.app/strategy/strategyquant-x-v143-ai-strategy-builder-33975ee2-4eca-4d0d-9676-dc7436223737
- I found no independent long-term user reports on Q yet. It is weeks old (doc dated 21 Oct 2026). CHECKED by search, absence.

### 2.10 QuantAnalyzer

| Function | What (CHECKED) | Users / notes |
|---|---|---|
| Extensive reports | Sharpe, Ret/DD, AHPR, Z-score, expectancy, SQN, stagnation, monthly table, results by day and hour, 20+ charts, portfolio report, correlation (daily/weekly/monthly), HTML export. https://strategyquant.com/quantanalyzer/extensive-reports/ | Day/hour tables are where users find What-If ideas (INFERRED) |
| What-If | Mon–Thu only, max 1 trade/day, 9:00–15:00, and more; each scenario is an open-source snippet. https://strategyquant.com/quantanalyzer/what-if-scenarios/ | See 2.3. The vendor itself says to retest with the rule built in |
| MM simulator | Apply MM methods to the existing orders, no new backtest (14 Sep notes, doc) | "setup the max dd money management, and montecarlo … Now i know, how much risk i can afford with my 12 pairs algo". PRACTITIONER, testimonial on the QA page |
| Monte Carlo + Predict & Verify | MC on trades; project the cone forward and check the live path against it (doc slug `predict-verify-strategy-performance-using-monte-carlo-simulation`) | Direct match for the operator's rule "trust judged against the bot's own MC worst run" (decisions.md:82) |
| Equity control | Switch a strategy on and off from its own equity curve (e.g. MA of equity); skipped trades update the curve on paper (14 Sep notes) | Admin: QA cannot give you the code; implement it in the EA |
| Portfolio Master | See 2.6 | |
| **Compare Results** | Draw live and backtest equity side by side. **Mass-compare** all strategies in one step ("some of our users trade tens and even hundreds of strategies"). https://strategyquant.com/quantanalyzer/compare-results/ | The incubation practice in 2.3 is this tool used by hand |
| Extendability | Java snippets in QuantEditor for metrics, MC, MM, What-If, correlation | |
| MT4 QuantAnalyzer | Free MT4 plugin: account history by symbol, magic number or comment; Sharpe, R-expectancy, CAGR, Z-score; P/L by weekday and hour. https://strategyquant.com/quantanalyzer/mtquantanalyzer/ | Grouping by magic number = a per-bot ledger (INFERRED) |

### 2.11 QuantDataManager and data sources

- **What (CHECKED):**
  - Sources listed in 1.6.
  - Broker profiles convert the source timezone automatically at download.
  - Clone to timezone; clones update with the source.
  - Compute higher timeframes from tick or M1.
  - View & Analyze: gaps, spikes, incorrect candles.
  - Export: CSV, MT4 FXT/HST, MT5, NinjaTrader (export format fixed in QDM 125), TradeStation, and others.
  - Since QDM 125, export can recalculate timezone at export time.
  - CLI. Direct MT5 import (b144).
- **QDM 125 changelog:** the "suspiciously large candles" algorithm was tuned to reduce false findings, and a false open > high warning caused by rounding was fixed. INFERRED: the spike detector is heuristic and noisy. https://strategyquant.com/quantdatamanager/whats-new/
- **How users use it** (official video, PRACTITIONER-grade walkthrough, https://www.youtube.com/watch?v=J40dT7TW5BE):
  - Download Dukascopy with a broker profile, so no clone is needed.
  - Analyze. The gap list does not account for holidays or the ±5 minutes around midnight, so many "gaps" are not real.
  - The presenter's advice: "we don't recommend building strategies for lower time frames" because gaps are much denser there.
  - Recommended practice: "Forex is a decentralized market and each broker may have its own data feed … I recommend exporting data directly from your broker". M1 is enough for swing strategies; tick data can be "tens of gigabytes".
- René Balke (FX bot YouTuber) installs QDM on a VPS, uses a broker profile per broker (IC Markets), and finds the free version gives "the same data". https://www.youtube.com/watch?v=u3gEToP7fBE
- **Strength:** broker-timezone alignment and a plain gap view.
- **Weakness:**
  - Spike and gap heuristics need a human to judge them.
  - Clones are second copies, so there is no lineage.
  - SQ's paid data cannot leave the app.

### 2.12 Export and execution

- **What (CHECKED):**
  - Full source for MT4, MT5 (hedging and netting), TradeStation, MultiCharts, NinjaTrader, JForex, and pseudocode.
  - A switchable internal engine that imitates each platform's execution ("Always develop and test your strategies using the backtesting engine that corresponds to the platform where you plan to deploy").
  - b143: indicator values match MultiCharts/TradeStation to 6 decimals.
  - AlgoCloud runs strategies in the cloud.
- **Users (PRACTITIONER):**
  - "strategies that are great in the platform but when I export the code to my platform they seem to fall apart" (2018 review, https://dreamtotrade.com/software-i-use/).
  - SQ's own shared TradeStation workflow says per-trade differences "should not exceed 5-10%", and that "many people struggling with the achieving the same results in TS platform as in SQX". https://strategyquant.com/shared/workflow-for-nasdaq-or-any-other-futures-indices/

---

## 3. Mapping to QMX surfaces: take, adapt, combine, improve

Notes on reading this table:
- "Blast radius" names the existing QMX part each proposal touches. Paths are on `plan/agent-system` (`D:\QMX-worktrees\agent-system`).
- The scope rule applies: nothing is blocked, and shipped backend work is extended, not removed.
- "Lever" is the compounding-test lever it serves: edge per trade (E), trade count (N), right size (S), less drag (D), or proof (P) for the Judge step.

| # | SQ feature | QMX surface | Verb | What exactly | Blast radius in QMX | Lever |
|---|---|---|---|---|---|---|
| 1 | Cross-check funnel (cheap → expensive, drop on fail) | QMB + Lab + Copilot | ADAPT | A **funnel recipe** made of ordered QMB procedures, each with an optional threshold the user owns. Results are stored as raw measures. "Pass" is a read-time fold, never stored. Failing early saves compute, but is logged as a try | `qmb/src/qmb/robustness/*` (procedures exist), `sweep/admit.py`, `sweep/rank.py` (read-time fold), QMA graph templates (`qmx-agents/plugins/analysis-backtest/graphs` is empty today), B-4 fold (DEC-0162 stays: no stored pass/fail) | P, D |
| 2 | Higher precision retest | QMB | TAKE | Run the same bot at a higher fidelity (bar → M1 → tick with real spread) and report the ratio | `qmb/src/qmb/execution/*` fill/slippage ports, B-6 fidelity identity; needs a "fidelity ladder" run-config axis in `sweep/axes.py` | D, P |
| 3 | What-If (trade-list filters) | QMB + Lab | IMPROVE (exists) | `analysis.project` already supports days/hours/session/max_trades/include/exclude, as a `projection` claim class. Add skip-k%, drop-top-x% and degrade-exit, and a one-click **promote to rule** that writes the filter into the bot's Python and runs `analysis.rerun` | `qmb/src/qmb/analysis/project.py` (`PERMITTED_PREDICATE_KEYS`), `analysis/rerun.py`, QML bot source (new version via branches-from) | E, N |
| 4 | MC trade manipulation + retest + new methods (MACHR blocks, degrade execution, parameter jitter, start-bar) | QMB | ADAPT | Extend the robustness ladder. Label each method with what it **can** and **cannot** detect (shuffle cannot change total profit; resampling cannot hurt a high mean/SD strategy) | `robustness/shuffle.py`, `perturbation.py`, `summary.py` (no verdicts, caller-supplied bands); new `blocks.py`, `degrade.py` | P, S |
| 5 | MC for capital and risk of ruin (Ali Casey) | Pods (sizing) + unit | TAKE | Use the MC distribution to set **minimum capital and risk per trade** for a target max DD at a chosen confidence. Feed it to the unit's sizing and to the "back to paper" rule | `qmf-risk` Book `money_rules` (CT-22), `analysis/variants.py` (Book variants as dev-zone candidates), decisions.md:82 rule | S |
| 6 | Backtest on additional markets | QMB sweep + registry | COMBINE | Not a gate. It is the **domain-expansion map**: the same logic run across instrument × timeframe × window cells, each cell a registry entry with its own proof | `sweep/axes.py` (`instruments[]`, `timeframes[]` exist), registry "preferred / hypotheticals" (seeds), correlation ledger | N, P |
| 7 | SPP + Optimization Profile | QMB optimize | TAKE | Publish **median-of-neighbourhood** measures and the share of profitable trials beside the best trial. `optimize/sensitivity.py` already flags `ISOLATED_SPIKE` and `STABLE_CLUSTER`; add SPP medians and the Pardo profile criteria as data | `qmb/src/qmb/optimize/sensitivity.py`, `study.py` | P, E |
| 8 | Walk-forward + WF Matrix + WF Stability/Score | QMB robustness | ADAPT | Add per-window reoptimization (today WF is a split sequence of a fixed assignment), the matrix of runs × OOS %, and a **plateau rule** (k of m cells in a block, configurable) as a read-time fold | `robustness/walkforward.py`, `optimize/splits.py`, CT-12 split manifests | P |
| 9 | Ranking / fitness / dismiss-similar | QMB rank + Lab | ADAPT | A **named, versioned ranking lens** (user-defined weights) used only to *sort*, never stored as evidence. Dismiss-similar becomes "cluster near-duplicates and count them as one try-family" | `sweep/rank.py` (`FORBIDDEN_COMPOSITE_EXPRESSIONS` today rejects composites); needs an AD to allow a *sort-only* lens. DEC-0162 | P |
| 10 | Fit to existing portfolio + correlation filter | Pods + registry | TAKE | Score a candidate by its **marginal** effect on the live book (ΔRet/DD, Δtail, correlation to existing units) | `analysis/deferred.py` (F07 synthetic portfolio combination refused today; un-defer as a projection class), correlation ledger | D, S |
| 11 | Portfolio Master / Composer (k of N, sector caps, weights, MPT) | Pods | ADAPT | Combine units with caps per correlation cluster and sector, out-of-sample holdout, and a tries count. Prefer robust allocators (risk parity, capped weights) over raw Markowitz on backtests | `analysis/deferred.py` F07, Book/BMS CT-22/27 constraints, Pods (not yet specified) | S, D |
| 12 | Custom Projects (17 tasks, Go To loops, notifications, wait-for-user) | Copilot workflows (QMA graph templates) | TAKE (shape) | Task kinds map onto graph nodes: Build → QMA candidate mint, Retest/Optimize/Filter → QMB door, Go To → Loop with `stopping_condition`, Notification/Wait-for-user → `approval_request`, Update Data → `qmb data download`, Log stats → Experiment Ledger | `qmx-agents/plugins/analysis-backtest` (contributions `tool:qmb`, `graph_template:procedure`), QMA daemon graph templates, CT-47 ExperimentSpec | P, N |
| 13 | Auto Retest (same config, new data, multi-symbol, multi-TF) | Copilot routine + MIS/registry | TAKE | A scheduled routine that re-runs every registered unit on fresh data and updates registry proof and drift | QMA Routine, `qmb data download` / `verify`, registry as-of sets (B-15) | P, D |
| 14 | Q AI: skills / commands / agents / rules folders, AI Brain memory, trading ledger, auto-research loop, `/drive-ui` lock, snapshot-before-write, audit log, "Before you trust an answer" | Copilot | COMBINE | QMX's Claude Agent SDK harness already has a plugin manifest with contributions. Take Q's **verdict ledger with reasons** ("rejected ideas are not proposed again") and the **trust checklist as standing rules** that every agent report must satisfy | `qmx-agents/packages/qma-*`, plugin manifests, agent memory (seeds: "needs agent memory") | P |
| 15 | MCP server (6 tools) | QMB doors | TAKE | QMB already plans "an MCP door after CLI v1". SQ's minimal tool set (list / stats / run / stop) is a good first cut | `qmb/src/qmb/doors/*`, B-1 | P |
| 16 | Results plugins (HTML/JS, `postMessage`, vibe-coded) | Mini apps | TAKE | A mini-app template: "analysis tab over one CT-32 + CT-29". The agent writes it from a shipped CLAUDE.md-style guide. Cache any AI answer, label billed calls | `apps/qmx-ui` mini-app slots (`preview-tab`, `detail`), UI-BACKLOG "Copilot pass" rules | P |
| 17 | QuantAnalyzer Compare Results + MTQA grouping by magic number | Node + Lab + unit | TAKE | **Live-vs-replay drift per unit**: the same bot's live CT-29 stream against its replay on the same dates and costs. Mass-compare all units nightly | QMN journals (CT-13/CT-25), `analysis/compare.py` (CT-32 readout today), QMB calibration (B-6: slippage from fill journals) | D, P |
| 18 | Predict & Verify | Unit + Pods | TAKE | The live path checked against the bot's own MC cone. Outside the cone at confidence x → back to paper | decisions.md:82, Book `control_policy`/leash, KSA | S, D |
| 19 | Equity control | Pods (later) | ADAPT carefully | Only as a Class-B analysis first. If it wins out of sample, promote it to a Book `control_policy` rule with a replay rerun | `analysis/project.py` (would need a sequential class), CT-22 `leash_grammar` | S |
| 20 | Money management methods incl. ATR risk sizing | Unit sizing | IMPROVE | Sizing is the unit's job, tuned from its own record, never a fixed EA setting | `qmf-risk` sizing ladder, self-tuning-sizing ticket | S |
| 21 | QDM broker profiles, clone-to-TZ, View & Analyze | QMF data + QMB data | ADAPT | Broker-calendar *views* (derived, with lineage) rather than clones; gap reports that know the calendar (QMB `gap-check` already does); spike flags as annotations | `qmb/src/qmb/data/gap_check.py`, `verify.py`, qmf-data processed room | D |
| 22 | QDM export formats, MT5 import | QMB data | ADAPT (narrow) | CSV/Parquet extract for portable research. Broker history import through CT-15 from cTrader/MT5 | `qmb data` commands, CT-15 adapters | D |
| 23 | Builder random/genetic structure search + templates + Improver | Lab + Copilot | ADAPT | Agents (cheap model in bulk, stronger model for rewrites, per seeds) generate *Python* bot variants from templates with named slots. Each variant is a dev-zone candidate with lineage. **Every candidate counts as a try** | QML template (`qml/footprint/template.py`), registry dev zone, QMA StrategyHandle | E, N |
| 24 | Automatic problem detection ("too many trades closing at same bar", no fills) | QMB | TAKE | Built-in sanity refusals and flags (look-ahead suspects, same-bar entry and exit, zero fills, extreme concentration) | `qmb/src/qmb/runloop/*`, typed refusals | D |
| 25 | Multiple OOS periods, IS/OOS/RT/P filter scopes | QMB | TAKE | Several sealed slices. Filters name the slice they read | CT-12 split manifests (seal exists) | P |
| 26 | AlgoCloud (cloud execution) | Node | Context | Confirms the "trading server" direction. No feature to take | QMN | — |

---

## 4. Hybrids and new improvements (all INFERRED)

Each item names what it touches. All numbers are configurable starting points.

**H1. The robustness test of the robustness tests (rsantinikk's protocol as a standing QMB job).**
- Every month: take all candidates generated in the window, measure the base rate on a held-back period, then measure the rate among those that passed each test.
- Publish **lift per test, per instrument class, per bot type**, and retire tests that show no lift.
- This turns "which tests matter" from belief into data, and the Judge step gets proof that each gate earns its compute.
- Touches: `robustness/*`, `sweep/rank.py`, CT-12 seals, a new "test lift" ledger view.

**H2. The tries ledger.**
- Every candidate the Copilot or the Lab creates is a try, and so is every trial, every What-If promoted to a rule, and every cell in domain expansion. Tries are grouped by **family** (near-duplicates by trade-stream correlation, replacing SQ's ±5 % fingerprint).
- Any headline metric shown in the Lab carries "best of N effective tries". QMB later adds the deflated statistic (DSR / PBO-CSCV slots already reserved in `robustness/summary.py`).
- SQ has nothing like this. Touches: the QMB ledger (roles `trial`/`replicate` exist), registry lineage, the Lab results table.

**H3. What-If + the registry's hypotheticals = "context search with a held-out proof".**
- What-If finds candidate *contexts* where a bot did well (hours, sessions, weekdays, MIS states). Each context becomes a **hypothetical** registry entry, never a placement.
- It graduates only when a *later*, unseen window confirms it.
- This is the operator's fail branch ("find a context where its rules are met") with the strict version from seeds: proof from data the search never saw.
- Touches: `analysis/project.py`, the registry hypotheticals, the MIS labelers (identity, spread-state, SQS, ...) as What-If predicates (new predicate keys).

**H4. SPP + domain expansion stopping rule.**
- Apply SPP across *cells*, not just parameters: for a logic, compute the median outcome across its whole neighbourhood of instruments × timeframes × windows.
- Expand only while the **neighbourhood median** stays above zero after costs and each new cell has at least a configurable minimum trade count (start at 100, matching SQ's Scorecard low-trade gate, configurable).
- Stop a branch when the median falls or the cells get too thin.
- Touches: `sweep/axes.py`, `optimize/sensitivity.py`, the domain-expansion-rule ticket.

**H5. Fitness bank + compounding test.**
- Replace the 0–1 fitness with a **compounding scorecard** of the four levers measured separately: edge per trade after costs (E), trades per month (N), sizing headroom from MC capital (S), and marginal drag or correlation added to the live book (D).
- No single composite is stored. The Lab sorts by any lens the user names, and the Judge step reads the per-lever evidence.
- Fits DEC-0162 (per-requirement outcomes, no composite) and gives the operator his "fitness bank". Touches: `sweep/rank.py` lens config, CT-32 measures roster (AD-23/AD-41).

**H6. Robustness tests run by agents through QMB, with a trust checklist.**
- The Copilot assembles funnels from a menu of QMB procedures. It runs them through the one `qmb` door per environment and writes a verdict entry with reasons to the agent ledger.
- Q's 7-point "Before you trust an answer" list becomes a **machine-checked rule**: the report must cite run ids, name period and market, state the slice (IS/OOS), use real trade streams, and include the costs model.
- Touches: qmx-agents plugin rules, Experiment Ledger, CT-47.

**H7. Monte Carlo for sizing, not for selection.**
- Demote MC from a gate to an input: the MC cone sets each unit's capital floor and risk per trade for a target DD at a chosen confidence (Ali Casey's risk-of-ruin chart).
- The same cone drives Predict & Verify live ("outside the cone → back to paper").
- Touches: Book `money_rules`, the self-tuning-sizing ticket, decisions.md:82.

**H8. Live-vs-replay drift as a first-class unit metric.**
- QuantAnalyzer Compare Results, done properly: nightly, per unit, the same dates and the same calibrated costs, split into signal drift (different entries), fill drift (slippage) and cost drift.
- The drift itself calibrates QMB's slippage port (B-6 already says calibrate from fill journals).
- Touches: QMN journals, `analysis/compare.py`, the execution ports.

**H9. Regime-sequence robustness feeding the MIS.**
- Use MACHR-style block bootstrap labelled by **MIS state**: resample blocks of trades *by regime label* and ask how the bot does when the regime mix shifts.
- The output is the bot's regime sensitivity profile. That is exactly the "conditions a bot thrives in" the router needs.
- Touches: `robustness/` (new block method), MIS labelers, registry preferred states.

**H10. Degrade-execution MC sized from real fills.**
- SQ's RandomlyDegradeExecution uses a made-up "max % of range". QMX can draw degradations from its own recorded slippage distribution per instrument, hour and session (calibration, not invention).
- Especially important for scalpers, where costs decide the edge.
- Touches: CT-25 risk journal, execution slippage port, SQS door.

**H11. What-If "promote to rule" in one click.**
- When a projection wins (e.g. no trading 08:00–09:00 Thursday), the Lab writes the filter into a new bot version's Python, reruns in replay, and shows both results side by side with the try counted. Users in SQ's own comments struggle to do this by hand in AlgoWizard.
- Touches: `analysis/project.py`, `analysis/rerun.py`, the QML version graph.

**H12. Higher-precision ladder as the scalper gate.**
- For scalper types, run the bar-precision vs tick-real-spread ratio first: a scalper that loses more than x % of its edge at tick precision is dropped before anything else.
- Touches: the execution fidelity ladder, the scalper-types ticket.

**H13. Fit-to-portfolio with "not correlated right now".**
- Correlation computed on a rolling window and conditioned on MIS state, not on full history. Candidates are scored by marginal tail risk in the regimes where the live book is weakest.
- Touches: correlation ledger, Pods, MIS.

**H14. Auto-research loop with a pre-registered plan.**
- Q's overnight loop goes hypothesis → build → evaluate OOS → journal. QMX can do the same with one more step: the agent **pre-registers** the test plan (slices, measures, thresholds, max tries) before it touches data, and the ledger refuses verdicts that do not match the plan.
- This kills the "change the test until it passes" failure mode. Touches: CT-47 ExperimentSpec (has fp1, seed, data refs), the agent memory ledger.

**H15. Workflow simulator (Thomas Nickel's idea).**
- Backtest the *workflow*, not the strategy: run the whole funnel on old data (say 2015–2020), pick what it would have picked, then trade those picks on 2021+ in replay.
- The result is the expected live hit rate of the recipe itself, so the operator can compare recipes. This is the strongest proof the Judge step could get for a Lab recipe.
- Touches: QMA graph templates as replayable objects, QMB orchestrator, H1.

**H16. Results tabs as mini apps, with an "explain" button that is cached and labelled.**
- Copy Q's house rules for AI inside a results tab: only on an explicit click, cached per bot, a Regenerate button, labelled as a paid call.
- Touches: mini-app template, UI-BACKLOG copilot rules.

**H17. Template slots + cheap/strong model split for generation.**
- A QML template with named slots (entry filter, exit, session window). DeepSeek-class models fill slots in bulk, a stronger model attempts rewrites of near-misses (per seeds), and the tries ledger counts all of them.
- Keep random fill (honours the template) over genetic crossover (SQ's own docs say crossover breaks it).
- Touches: `qml/footprint/template.py`, QMA StrategyHandle, registry dev zone.

**H18. Cost-stress as the cheapest robust filter.**
- The forum counterexample (96 H4 strategies, no OOS, "ridiculously high spreads") suggests a cheap, strong first gate: require the bot to survive at a configurable multiple of the calibrated cost (start at 2×).
- Touches: execution cost port, sweep axis "cost multiplier".

**H19. Plateau rule shared by WF Matrix, SPP and domain cells.**
- One plateau fold: in any grid (parameters, WF runs × OOS %, instruments × timeframes), the bot must have a connected block of k-of-m good cells. One concept the operator learns once and sees everywhere in the Lab.
- Touches: a shared fold in `robustness/summary.py` or `sweep/rank.py`.

**H20. "Rejected ideas are not proposed again" with a reason and an expiry.**
- From Q's memory: store rejected bot ideas with the reason and the evidence run. The Copilot checks this before generating. Add an expiry so a context can be re-tested when the regime changes.
- Touches: agent memory, registry lineage.

---

## 5. Where SQ overfits or misleads, and how QMX can do better

| SQ blind spot | Evidence | QMX better |
|---|---|---|
| **No correction for the number of tries.** Millions searched, top N kept, the count discarded | CHECKED by absence in the docs tree. PRACTITIONER: "one strategy … in every million iterations" (homepage testimonial); Ali Casey quote above | Tries ledger with families and deflated metrics (H2). PBO/CSCV slots already exist in `robustness/summary.py` |
| **OOS leakage inside the Builder.** Genetic fitness reads IS+OOS when additional markets are on; reusing a prior generation as the initial population "cancel[s] your OOS area" | PRACTITIONER: forum thread "Fake backtest IS OOS" | CT-12 seals with one final look (B-9). Generation never reads sealed slices. A refusal, not a convention |
| **Gates instead of measurements.** "≥ 80 % of original" thresholds become pass/fail. Users cannot tell whether a gate adds lift | CHECKED: thresholds on every cross-check page. PRACTITIONER: rsantinikk found no lift | Store raw measures, fold verdicts at read time (DEC-0162), and measure each gate's lift (H1) |
| **Monte Carlo cannot catch overfit trade lists.** A shuffle cannot change total profit, and resampling cannot hurt a high mean/SD list | PRACTITIONER: Ali Casey, 70,000 sims passed a strategy built to be garbage | Label each MC method with what it can detect. Use MC for capital and sizing (H7). Rely on SPP, plateau and WF Matrix for selection |
| **What-If tempts hindsight filtering.** Users ask "can it automatically select best days?" | CHECKED: comments on the What-If doc; the admin warns against it | What-If outputs are `projection` class, become hypotheticals, and need an unseen window (H3) |
| **Correlation as a static number.** Full-history daily P/L correlation | CHECKED: correlation docs. PRACTITIONER: "correlations … break down" in crises | Rolling, regime-conditioned correlation (H13) |
| **Markowitz on backtests, normal VaR.** | CHECKED: MPT doc assumes a normal distribution for VaR | Capped or risk-parity weights, tail measures from the bot's own MC and live record |
| **Backtest-to-platform mismatch.** Export and re-run on a broker gives different numbers | PRACTITIONER: 2018 review; SQ's own "5-10%" tolerance note | One run loop for replay and node (QMN drives QMB's B-2 loop unforked), so no export gap. Calibrated costs from QMX's own fills |
| **Live decay found by hand.** Users run hundreds of demo accounts and compare by magic number | PRACTITIONER: "200 systems … across over 30 broker accounts"; "less than 10%" match | Nightly live-vs-replay drift per unit (H8), Predict & Verify (H7) |
| **Composite scores again** (Robustness Scorecard 0–100, fitness 0–1) | CHECKED: Results plugin doc | Per-lever scorecard, sort-only lenses (H5) |
| **Doc and product rot.** Stale pages, editor notes left in, a read-only forum, crash reports on heavy workflows | CHECKED: MC doc note; 2015 WF Matrix page. PRACTITIONER: workflow crash comment; "full of bugs" (ProRealCode 2019); EA Studio vs SQ thread ("more bugs") | QMX's verification-first culture. Keep docs generated from code where possible |
| **Licensed data locked in the app** | CHECKED: data subscription page; Q intro | QMX data stays in QMX rooms with licence tags (B-11) but is computable by agents inside the controlled room |
| **AI that proves "robust" by eyeballing several markets** | CHECKED: vendor AI demo transcript | Agents must pass the trust checklist and count tries (H6, H2) |

---

## 6. What the operator may not be seeing

1. **SQ is now an agent company too, with nearly the same plan as QMX's Copilot** (plugins, skills, agents, rules, memory, auto-research, MCP). Q is already on sale in 2026, with QuantDataManager next (Q4 2026) and QuantAnalyzer in 2027. QMX's difference cannot be "an AI that builds strategies". It has to be what SQ lacks: tries-corrected proof, units that size themselves from their own record, the MIS router, and one run loop from replay to the live node. CHECKED (Q pages) + INFERRED.
2. **SQX has an MCP server.** A QMX agent could, in principle, drive a licensed SQX install as an *external generator*. Its candidates would enter the QMX registry as dev-zone tries, and QMB would judge them. This is the cheapest "use SQ as the anchor" path; it needs an operator decision on licences. CHECKED (MCP doc) + INFERRED.
3. **Most of what the operator calls "StrategyQuant features" is already half-built in QMB** (section 0, point 6). The work is connecting and extending, not new design. Removing or rewriting `analysis/project.py`, `optimize/sensitivity.py` or `sweep/axes.py` would throw away the closest things QMX has to What-If, SPP and domain expansion. INFERRED from code.
4. **The fitness bank conflicts with an existing ratified rule.** DEC-0162 bans stored composite scores, and `sweep/rank.py` enforces it with `FORBIDDEN_COMPOSITE_EXPRESSIONS`. The way through is a sort-only lens plus the per-lever scorecard (H5). That needs a short AD, not a silent change. CHECKED (code) + INFERRED.
5. **Practitioners say the gates matter less than three plain things:**
   - a reason the edge exists (SQ's own support says so);
   - cost stress with long history;
   - live incubation with drift checks.
   QMX can build all three as proof, not as advice. PRACTITIONER + INFERRED.
6. **Domain expansion is SQ's "additional markets" used the other way round.** SQ uses other markets to *reject* a strategy. The operator wants them to *place* units. SQ's own doc admits a robust strategy "does not have to perform equally well on all markets", which is exactly why a map (registry cells with their own proof) beats a gate. But every cell is a try, and SQ never counts them. CHECKED + INFERRED.
7. **The scalper-first plan makes precision and cost tests the main gate.** SQ's QDM presenter says they "don't recommend building strategies for lower time frames" because gaps are dense there. QMX's scalpers will live or die on tick-precision fills, real spreads and session-aware gap handling. PRACTITIONER (official video) + INFERRED.
8. **A "recipe" can be backtested** (H15). This lets the operator compare Lab workflows by expected live hit rate, which is the strongest proof the Judge step could get. Nobody in the SQ world does this except one freeware author. PRACTITIONER + INFERRED.
9. **SQ hides its robustness funnel behind the Professional tier.** For QMX the funnel is core, but it costs compute: 10–200 seconds per strategy in SQ's own numbers. QMB's governor (`min(cpu, memory)`) and "show where jobs run" (operator's Lego vision) need a cost estimate beside every expensive test, as UI-BACKLOG already notes. CHECKED + INFERRED.

---

## 7. Configurable numbers seen in this study (starting points only)

| Number | Source | Where it would live in QMX |
|---|---|---|
| Keep ≥ 80 % of baseline (precision, What-If, MC filters) | SQ docs | funnel recipe threshold, per test |
| WF Stability NP > 60 %; DD stability < 200 % | SQ WF values doc | WF fold |
| WF Matrix: runs 5–15 step 2, OOS 20/30/40 %; plateau 3×3 with ≥ 7/9; cell passes at 80 % of score parts | SQ WF Matrix doc | plateau fold (H19) |
| MC confidence levels 50…100 | SQ MC doc | `summary.py` caller-supplied bands |
| Param jitter: probability, max % change (e.g. ±10 %) | SQ MC doc | perturbation config |
| MACHR block size 5 (2–50); 500+ sims | SQ codebase | block method config |
| Dismiss-similar tolerance ±5 % on trades/NP/DD | 14 Sep notes (SQ doc) | try-family clustering threshold |
| Correlation cap 0.4 by weekly P/L; max 2 per pair | tradingtact | Pods caps |
| Low-trade gate: < 100 trades caps the sample pillar | SQ Results plugin | min trades per cell (H4) |
| Generations 5–100, restart on stagnation | SQ GA doc | generator config |
| Cost multiplier for stress (start 2×) | INFERRED from forum | sweep cost axis (H18) |
| SQ ↔ platform tolerance 5–10 % | SQ shared workflow | drift alert threshold (H8) |
| MC risk-of-ruin target DD and confidence (e.g. 30 % at 98 %) | Ali Casey | unit capital floor (H7) |

---

## 8. Cross-check against the 2026-09-14 donor notes and UI-BACKLOG (done last)

- **Still true from 14 Sep:** structure search and parameter search are separate; genetic crossover breaks templates; databank = top N; Custom Projects ≈ QMA graph templates; QuantAnalyzer's simulations do not re-backtest. Those notes were architecture-gated ("do not copy"). This study uses the production lens and the 2026-10-18 ruling that nothing is legacy, so several "do not copy" lines become "adapt with proof" here (fitness lens, portfolio combiner, MCP use).
- **New since 14 Sep:**
  - Q AI assistant with plugins, memory and auto-research (Oct 2026).
  - MCP server (b144).
  - Results plugins vibe-coded with Claude Code (b144).
  - New MC methods (MACHR, degrade execution, parameter jitter).
  - Correlation filter task.
  - Auto Retest multi-symbol and multi-TF (b143).
  - ATR risk sizing (b143).
  - Automatic Markowitz weights (b142).
  - QDM Binance futures and export-time timezone (QDM 125).
  - The forum went read-only.
- **Corrections to 14 Sep:** the What-If filter is already in QMB code (`analysis/project.py`, Story 35.2), not "absent". The stable-region versus lone-spike analysis is shipped (`optimize/sensitivity.py`). The 14 Sep QA notes list portfolio combination as "new"; the code has an explicit deferral refusal (`analysis/deferred.py`, F07).
- **UI-BACKLOG (2026-10-01):** the borrowed patterns there (databank dock, What-If overlays, tiered robustness with cost estimate, WF Matrix flat heatmap with a cluster rule, filter scopes, correlation matrix, task pipelines with visible loop caps) all agree with this study. Its line "StrategyQuant-style scenario generation: many pairs, timeframes, pair trading" is the operator's "What-If scenario generator". In SQ that idea is split across Backtest on Additional Markets, Auto Retest multi-symbol/multi-TF and Portfolio Master's "5 of 20 markets". In QMX it is the domain-expansion grid (`sweep/axes.py`) plus the registry (H4, row 6).

---

## 9. Sources visited (all 2026-10-24)

**StrategyQuant live pages, read in the browser:** https://strategyquant.com/ (nav + "Show more features"), /features/ (all hidden tab panels), /q-ai-assistant/, /q-ai-assistant/pricing, /pricing/, /whatsnew/ (+ ?date=2026-1, 2025-4, 2024-11), /doc/, /doc/category/strategyquant/ (+ program-screens), /sitemap_index.xml, /doc-category-sitemap.xml, /doc_new-sitemap.xml, /quantanalyzer/, /quantdatamanager/, https://algocloud.com/

**Docs and codebase, fetched with Exa:** /doc/q-introduction/, /doc/q-extending/, /doc/strategyquant/mcp-integration/, /doc/what-if-simulation/, /doc/strategyquant/what-if-simulations/, /doc/monte-carlo-tests/, /doc/opti-profile-sys-param-permutation/, /doc/strategyquant/walk-forward-matrix/, /doc/description-of-advanced-walk-forward-values/, /doc/ranking/, /doc/cross-checks-robust-testing-overview/, /doc/backtest-on-additional-markets/, /doc/higher-backtest-precision/, /doc/recommended-workflow-using-custom-projects/, /doc/tasks/, /doc/automatic-portfolio-construction-mpt/, /doc/strategyquant/results-plugins, /doc/supported-platforms/, /doc/money-management/, /codebase/monte-carlo-machr-block-randomization/, /codebase/monte-carlo-randomly-degrade-execution/, /quantanalyzer/compare-results/, /quantanalyzer/mtquantanalyzer/, /quantanalyzer/whats-new/, /quantanalyzer/extensive-reports/, /quantanalyzer/what-if-scenarios/, /data-subscription/, /quantdatamanager/whats-new/

**Practitioner sources:** strategyquant.com forum threads (robustness-tests-do-they-really-work, strategyquant-success, fake-backtest-is-oos-overfitting, walk-forward-optimization-vs-robustness, handling-overfitting-in-strategyquant-generated-strategies); strategyquant.com/shared workflows (NASDAQ IS/OOS, TradeStation futures, Automatic Retest, Gold H1); prorealcode.com topic; dreamtotrade.com review; forexfactory.com EA Studio vs SQ thread; nexusfi.com review (2025-12); tradingtact.com Portfolio Master guide; reddit r/mltraders snapshot (question only, no answers captured).

**YouTube (transcripts read through Exa; no video files downloaded):**
- Ali Casey, "70000 Monte Carlo Sims Said Yes. Walk-Forward Matrix…" https://www.youtube.com/watch?v=EZy4k1v2IwI (2026-09-24; transcript without timestamps)
- Ali Casey, "Learn how to use Strategy Quant X! Builder Module Part 1" https://www.youtube.com/watch?v=z81pH7dVTkc
- Ali Casey, "SQX v143: The AI Strategy Builder…" (timestamps via strategydecoder.app; AI build at 13:42)
- Lisa Forex, "Genetic Evolution Explained" https://www.youtube.com/watch?v=fLInoRgsDuQ
- StrategyQuant, "How to Achieve 99% Backtest Accuracy in MetaTrader 5…" https://www.youtube.com/watch?v=J40dT7TW5BE
- René Balke, "Free MT5 Tick Data Tutorial" https://www.youtube.com/watch?v=u3gEToP7fBE
- StrategyQuant AI assistant demos (blog transcripts, 2025-06)

I did not use the `watch` skill. It downloads video files, and file downloads need the operator's own permission. The transcripts covered the same content.

**QMX (read-only):**
- `workroom/risk-lab-2026-10-05/seeds.md`, `decisions.md:82`
- `docs/components/qmb.md`, `qml.md` (headings and key sections)
- Code on `plan/agent-system`: `qmb/src/qmb/{analysis,robustness,optimize,sweep}/*`, `qmx-agents/plugins/analysis-backtest/manifest.json`
- Cross-check at the end: `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-14/inputs/donor-{strategyquant,quantanalyzer,quantdatamanager}.md`, `QMX-worktrees/ui-review-repair/apps/qmx-ui/UI-BACKLOG.md`
