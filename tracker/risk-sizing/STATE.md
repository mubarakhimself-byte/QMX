# Unit system: state of play

**Read this first.** It is the single entry point for the unit work: every finding, operator correction and open decision in one place, with links to the detail. Updated after every agent result and every operator message.

Last updated: 2026-10-25 (after 07 funnel).

## Where everything is

| What | Where |
| --- | --- |
| The operator's seeds (his ideas, newest corrections) | `seeds.md` (this folder; moved from the git-ignored workroom) |
| The map and decision tickets | `wayfinder/MAP.md`, `wayfinder/tickets/`, run `python wayfinder/frontier.py` |
| Research, one file per question | `research/01` … `research/09` (table below) |
| Older context | `C:\Users\Mubarak\Desktop\QMX\workroom\risk-lab-2026-10-05\` (HANDOFF, decisions.md, grounding 01-09) |

## Operator corrections (binding; outrank every research file)

1. **Keep it simple.** Design FOR complexity (hard edge cases, the 95th percentile), never a complex system. No "every part must prove itself" machinery, no hundreds of tests. Agents never touch money: bots trade, and the broker sits outside QMX.
2. **A unit replaces the trading bot.** It is one complete trading algorithm with no separations: entry, exits, its own self-calibrating risk and sizing, its own condition needs, its session profile, its exam baseline and its journals, tested as one. The precedent is MT5 Wizard's signal + trailing + money modules, except the money part calibrates itself. "The unit itself is the end." The 13 Oct four-part formula was Claude's baseline and was never agreed.
3. **QML gets upgraded into the library agents use to build units**: build, test, promote, monitor. Deep modules (small simple interface, complex internals), JSON schemas, simple mental models. The dictionary was GPT's idea: a good start, not sacred.
4. **QMB is not live trading.** Backtest and stress test are one world; live trading on the node is another.
5. **The router only routes.** The unit alone controls its trading, risk and sizing. Router speed is an architecture problem, not a modelling one.
6. **A trading journal per unit**, from creation through stress, paper and live. Possible fields: best instruments, timeframes, family, risk profile, pod.
7. **Nothing is out of scope**, but every proposal names what it touches. Never casually remove shipped backend work (2-3 weeks to ship).
8. **Broaden before architecture.** Fresh, live sources over old notes. Exa plus the browser; Firecrawl last (low credits).
9. **The MQL5 DeepSeek run is dropped** (no credits). Use the articles later inside QMX through mini apps and workflows.
10. **Positioning:** when generating strategies is nearly free, judging them is the product. QMX is his own platform, not for sale.
11. **Bring him only real ambiguity.** Settle simple architecture issues and report them in one line.

## Research findings (short; detail in each file)

| File | Most important findings |
| --- | --- |
| [01 ground truth](research/01-ground-truth.md) | Agents can't backtest a strategy they wrote (PR #204 open, setup-only). QMB replays bid/ask quotes only, so no crypto or perps. QMB's reader may need ~16 GB per month of 1m bars (estimate). Cost calibration empty (GAP-0048), so nothing counts as proof. The tries correction lives in idle workflow templates. The Library already has `unit`/`bot`/`pod` kinds with Markets and Family-tree tabs. MIS = 6 rule labelers + 1 fitted model, no router. Only 6 indicators run. Docs contradict the new intent (no futures, Book owns exits, bot never sizes). |
| [02 instruments](research/02-instruments-and-traders.md) | IC stock CFDs are MT5-only. IC futures CFDs expire early and are never rolled. Hyperliquid has 24/7 perps on stocks, indices, gold and FX; funding is hourly; order actions are rationed; only ~3.5 days of 1m candles, so QMX must record its own history. cTrader has depth but no trade tape. Backend: CCXT spot only; nothing models funding, expiry/roll, dividends, session calendars or order flow. Scalper types: keep 5, split the order-flow sniper, router settings for liquidity window and funding, add liquidity-sweep and passive maker, a guard flags martingale/grid. |
| [03 StrategyQuant](research/03-strategyquant.md) | SQ's "Q" agent resembles QMX's Copilot plan. SQ never corrects for tries. Users say its robustness tests don't predict live results; only the parameter-neighbourhood test and the walk-forward grid caught a planted overfit. QMB already has What-If filters, a plateau check and an instrument × timeframe × parameter grid. Missing: funnel runner, walk-forward grid, portfolio combiner, live-vs-backtest compare. 26-row take/adapt map, 20 hybrids. |
| [04 platforms](research/04-platform-study.md) | All seven platforms use QML's contract shape already. Copy strategy-owned exits (Jesse, freqtrade), the MT5 Wizard's modules and 0-100 signal strength, freqtrade's look-ahead checks, signals that expire (LEAN Insights). Any instrument = typed instrument specs. Every exit and the router must be replayable in QMB. Agent door: follow QuantConnect's MCP server. |
| [05 academic](research/05-academic.md) | Router speed comes from information per bar: run on volatility, spread, liquidity and cost against the usual level for the time of day. Meta-labeling = routing per trade. No single test predicts live survival (Quantopian, 888 algos): count tries, deflated Sharpe + PBO. Domain expansion as a stream of tests with a numeric stop rule; cells borrow strength from the parent. Gaps: QMB results aren't in R, and backtest trades carry no market state. |
| [06 MQL5 pilot](research/06-mql5-pilot.md) | 1,970 of 3,128 articles pass screening (1,185 distinct). Evidence thin: 5 of 37 have out-of-sample tests. Codebook, idea-mining skill draft and starter prompt are ready but parked. Best finds: 19460, 21833, 5373, 23543, 21976. |
| [07a party](research/07a-funnel-party.md), [07b CIS](research/07b-funnel-cis.md) | ~300 raw ideas, 28 disagreements. Strongest: the two-speed router; the ratchet on the account floor; exits as a variant axis; labelers inside QMB plus results in R; proof grades from uncalibrated to live; "judging is the product". |
| [07 funnel](research/07-funnel.md) | 304 ideas → 33 clusters, forged. **Shape:** a unit = one complete algorithm (entry, exits, self-calibrating risk and sizing from its own journal, condition needs, session profile, exam baseline, one journal: backtest and stress written only by QMB, paper and live only by the node). Outside it, only: the account guard (stops, never resizes), the pod (shared budget, same-bet limits), the router (switches units on and off; precomputed table cached on the node). The judge: count tries per family, correct the best, sealed months, cost stress, live vs own exam baseline. **QML → unit library**, upgraded in place: verbs `new`, `check`, `test`, `promote`, `watch`, `find` over two JSON schemas (unit spec, journal). Foundations in order: record overrules → QMB windowed reader → unit spec + journal schemas → tries at the QMB door → instrument spec → published-cost calibration → MIS labelers in QMB → library verbs → exits and scalper indicators → one reference unit to paper on the cTrader demo. Note: §10 still says 1,400 trades for decay; 08 corrected it to ~240. |
| [08 old QMX testing and decay](research/08-old-qmx-testing-and-decay.md) | Old QMX had fixed pass numbers in R (200 trades, +0.15R after costs, PBO < 0.25 pass, > 0.50 dead). New QMB has more tests but no pass numbers, no tries correction, no calibrated costs, no R. Recommended QMB set: tries ledger + deflated Sharpe, 2× cost stress, out-of-sample in R, plateau check, PBO per family, block-bootstrap Monte Carlo for sizing and the live cone only; one frozen baseline card per unit. WF3 recovered (daily spotting, fortnightly action, maths never written). Decay check: nightly per unit journal (CUSUM on R, cone, cost/fill drift, trade-rate drift) → OK / Watch / Alarm, inform only. CUSUM catches +0.1R → 0 in ~240 trades (corrects 05's 1,400). |
| [09 router](research/09-router-architecture.md) | Split the router. A planner on the PC writes a signed placement plan with an expiry. The node runs a cheap gate per bar that only blocks new entries. With the PC offline the node runs from the plan; after expiry no new entries, open trades and the kill switch continue. |

## Open decisions for the operator (filtered; each has a recommended "yes")

From 07-funnel §9, plus the router split from 09:
1. **Same logic on a new instrument, timeframe or broker = a sibling unit** in one family tree. Shared try count; counted as one bet where they move together. Sessions and sniping windows stay inside one unit. (Sources clash: 13 Oct vs 20 Oct.)
2. **When something is "new":** logic or exit change = new version linked to its parent; a setting moved inside its range = same unit, each value counted as a try; self-recalibration = a journal entry; a model rewrite = a new unit marked "rewritten from".
3. **Promotion:** his click admits each unit. A sibling of an admitted unit may go live at minimum lot without his click, paid from a monthly evidence budget he sets (start 5% of equity), after its own backtest and stress test. New brokers and market kinds still need his click. Reopens DEC-0261.
4. **Size may grow back** after a cut, only on fresh trades that still show the edge, after a minimum time, never above his ranges. (This is the "tighten, never loosen" explanation: the one-way ratchet goes on the account floor.)
5. **House money per unit**, switched on only when its own record shows streaks.
6. **Keep the word "unit"** in QMX; "bot" is fine in conversation.
7. **Router split:** the planning half of the MIS on the PC, cheap live checks on the node (his seed said the node holds the MIS).
8. **Scalper types and seed additions:** report 09 + file 02's verdict.

## QMB backtest door: handed to the unit work (2026-10-24)

The operator ruled that the unit work owns QMB. Source: `../qma-v2/QMB-BACKTEST-DOOR-HANDOFF.md`.

- **Today:** an agent's `run_backtest` refuses ("binds no qmb_backtest door").
- **PR 204** (`build/wu4`, head `aabb813b`) is open and not stacked. Treat it as a reference, not a finished piece.
  - **Proved:** one function lands every backtest (`backtest_and_land`), copilot and workflow land the same object, the replay runs in one child process, and status/results read by object id.
  - **Blocked by QMB house rules:** subprocess outside `qmb/orchestrator/`, threading, and the word "engine". The fix is mechanical.
- **The real gap is a backtest that trades.** The only runner is `silent`: no trades, no equity, no ledger line. Three things are missing:
  1. A typed-partition entry to `execute_recorded_replay_request`, which today refuses the Library's typed monthly partitions.
  2. Execution inputs as data: `BoundExecution`, `BookAdmissionContext`, journal reader, ledger root, split fingerprint. All are built in Python today.
  3. A shipped bot nameable by reference. Only test fixtures trade.
- **Smaller gaps:**
  - `compare_runs` can't compare landed results by object id.
  - Run configs are files, not UI-editable.
  - The child's memory limit works on POSIX only.
  - ~16 GB per month of 1m data: bound runs to ~1,000 steps until the reader is windowed.
- **Fit with the funnel:** items 1-3 overlap foundations 2, 3 and 8 (windowed reader, unit spec and journal schemas, library verbs). The reference unit (foundation 10) is the "shipped bot nameable by reference".

## Conflicts with existing rules (to settle in architecture)

- **DEC-0162** bans stored composite scores. Fitness-bank ideas must stay sort-only, or the rule gets amended.
- **DEC-0261** "no per-bot warm-up": does it also ban indicator warm-up when the router adds a market?
- **GAP-0048** keeps cost calibration empty, so no QMB verdict is proof yet.
- **Docs** say no futures or options, the Book owns exits, the bot never sizes, no per-bot paper. All contradict the new intent and need a doc pass after the design.
- **decisions.md** (workroom) still carries the 20 Oct "MIS = blocks bots read" lean, which `seeds.md` reversed.

## Owed to the operator (explain in plain words, at his laptop)

- "Tighten, never loosen belongs on the drawdown floor, not on the edge estimate."
- "The bot never sizes vs the unit sizes itself": clear the ambiguity given correction 2.
- An explainer page for the converged design.

## Next steps, in order

**PAUSED (operator, 2026-10-25):** no architecture step yet. A deeper conversation with him comes first. Then planning, architecture and PRs, then coding in another session.


1. DONE: the funnel converged (07).
2. An explainer page for him, then his decisions 1-8 above.
3. Settle the technical tickets: `domain-expansion-rule`, `self-tuning-sizing-and-exits`.
4. The edge-case review (bmad-review) over the money paths.
5. Architecture: bmad-architecture, domain-modeling, codebase-design.
6. Then the trading-node session (QMN rework: node = trading server).
