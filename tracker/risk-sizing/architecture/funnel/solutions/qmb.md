# QMB: the backtester agents call as a tool

**What this part is.** QMB is the history world: backtest, stress, optimise, walk-forward, robustness, what-if, on recorded data, for units. It is a tool an agent calls and waits on, the way a test suite runs. It is not live trading (ledger B-01). Judging its results has its own file (`judging.md`), because the try count and the judge must stay in the core even when QMB is swapped.

**Verdict: the first mini app.** QMB runs as a mini app on the existing mini-app core, so he can build a new version, improve it, or run several side by side. The parts that must never differ between versions (the landing of a result, the run id, the try ledger, the judge) stay in the core.

## His words

- "So if one day I decide to build a new version of QMB, I should be able to." (T3:1383) "Or improve it, or give multiple variants, because it can be a mini app, for God's sake." (T3:1383)
- "It runs the same way you run your tests." (T2:135) "QMB is just a tool that an agent is meant to call" (T2:135) "the idea was that agents can call QMB as a tool" (T3:1562)
- "Now we either toss or we rebuild QMB based off this." (T2:135)
- "your whole goal is building something that agents can use, but at the same time at a professional quantitative trader level" (T1:1574)
- "it is run on every bot across multiple instruments" (T1:442) "If they fail, we need to be able to know why is it failing." (T1:513)
- "the old one had some things that are partially better" (T1:1177) "Back then, we didn't have QMB in the old system." (T1:513)
- "there is no point in me being refused that" (T1:1574) (about testing back to the 1990s)
- "I hope you haven't confused QMB and live trading." (T1:1177)
- "I don't want to talk about it. First understand it." (T2:219)

## 1. What exists today

| Piece | State | Where checked |
| --- | --- | --- |
| 91,252 source lines, 113 test files; 173 replay and robustness tests pass on Windows | BUILT (run) | G1 §4.1, header |
| Doors: CLI (needs a Python caller to inject port and fragments), Python API, MCP scaffolded and refusing | BUILT / DESIGNED | G1 §4.1 |
| House rules by test: no `subprocess`, `threading`, `socket` and the rest outside allowed homes; the words engine, kernel, exam, plugin, snapshot banned | BUILT | G1 §4.1 |
| Agents' `backtest_run` refuses: "Unknown config_ref", then "This host binds no qmb_backtest door" | BUILT (refusing) | G4b Q4 |
| PR 204: one function `backtest_and_land` lands every backtest from the copilot and from a workflow; replay in a child process; read back by object id; only runner `silent` | STACKED (open, base `build/wu2`, conflicts in two files, all both-sides-added hunks) | G4a §2.4; `tracker/qma-v2/QMB-BACKTEST-DOOR-HANDOFF.md` |
| A backtest that trades exists only in fixtures; inputs built in Python (`BoundExecution`, `BookAdmissionContext`, journal reader, ledger root, split fingerprint) | BUILT for fixtures | G1 §3.3; handoff "What QMB needs" |
| The typed monthly partitions cannot enter the trading replay (`execute_recorded_replay_request` re-resolves receipts and refuses other sources) | MISSING join | G1 §4.3 |
| Replay copies all history per step (three copies plus whole-frame compares) | BUILT (the only lookback limit; no step-cap constant) | G1 §4.3 |
| Quotes only: bid and ask pairs; half a pair refused | BUILT (limit) | G1 §4.3 |
| Fill, cost, spread, slippage, financing (forex swap), commission ports; calibration empty (GAP-0048) | BUILT / MISSING content | G1 §4.4 |
| Results: 27 measures in money and counts; R exists in CT-29 exit records and is never surfaced | BUILT | G1 §4.4 |
| Optuna optimiser with splits and sensitivity; trade shuffle, candle perturbation, rule significance, walk-forward; sweeps; analysis; synthetic series (forex only) | BUILT, tests pass | G1 §4.4 |
| `app_op` runs a mini app's operation in its supervised process, with a `pin = {pack, version}` and a `profile`; an instance's home may be another machine; today `{app: qmb}` fails because no app named qmb runs | BUILT | read this session: `qmx-engine/src/qmx_engine/nodes/app_op.py` docstring; G4b Q4 |
| Seven templates declare `qmb-door` and install as drafts | BUILT | G2 §4 |

## 2. Where QMB came from, and what the old system did better

**The founding intent** (risk-lab `grounding/07-qmb-lineage.md` §1, §2, CHECKED there against the August memlog): his own copy of the LEAN CLI, fed with Jesse's quant features (MCP, Monte Carlo, significance tests, optimisation, symbol by timeframe permutations); "agents as quants"; "build QMB more like npm"; extensible toward "more of the use cases QuantConnect designed for". What drifted (§7 there): the quant-tool feel was buried under governance nouns; the CLI never became the working face and MCP never shipped; breadth never reached asset classes (forex-only costs, one settlement asset, no margin, no instrument database); sizes are refused unless they land on an exact lot multiple; results stayed in money.

**Old QMX's backtesting** (research 08 §1.1, §1.4, CHECKED there against the vault): a parity replay that ran the same sizing, stops and kill switch as live with only the data and the fill simulator swapped; a fill simulator per symbol; walk-forward with a minimum trade count per window; a 1,000-shuffle Monte Carlo; PBO by CSCV; pass numbers in R (200 trades, +0.15R after costs, PBO below 0.25 to pass, above 0.50 dead); report slices by session and regime; MAE and MFE; a stress stage; a paper window and journal per bot. **What the new QMB does better** (§1.5 there): counts every try, labels shuffled and synthetic runs honestly, keeps raw measures and judges later, calibrates costs from real fills, fingerprints runs.

So "toss or rebuild" resolves as research 43 and 52 both concluded: **keep the measuring parts, rebuild the core loop around the unit, and add what the old system had that the new one dropped** (R, slices, MAE and MFE, a stress stage, a minimum trade count, per-unit paper in the node).

## 3. Harvest: solutions already on disk

| Solution | Where | Fits now? | Carried as |
| --- | --- | --- | --- |
| Rebuild the reader, a runner that trades a unit, the agent door, the what-if split, a judge, a funding port; extend results with R and receipts; keep the ports, optimiser, robustness, sweeps, exact money, the trial ledger, process per run | research 43 §3.4 table; research 52 §4 QMB row; ledger B-07 (LEAD'S CALL) | Yes | §6 |
| QMB as a tool, not a library: a sealed service; in a strategy package, an instrument row, a data recipe, a cost profile, a procedure; out a signed result in R and money | `07-qmb-lineage.md` §10 | Yes, and the mini app is that service | §5, §6 |
| Borrow from LEAN: instrument spec as data, per-instrument reality models, funding as a scheduled cash event, round to lot size instead of refusing, agent-friendly CLI grammar (`--parameter`, `--constraint`, `--estimate`), containment of strategy code | `07-qmb-lineage.md` §8 B-L1 to B-L6 | Yes | §6, §7 |
| Borrow from Jesse: routes as the stream declaration, the simulation model chosen apart from the data source (spot, perp, CFD on the same candles), gap rules for markets that close, version-pinned agent rules beside the tool, plain three-word robustness readouts, a GA as one more sampler | `07-qmb-lineage.md` §8 B-J1 to B-J8 | Yes | §7 |
| Reject: LEAN's Docker and C# engine, Jesse's floats and zero slippage, MCP powers that let agents edit the tester or run arbitrary scripts | `07-qmb-lineage.md` §9 | Yes | agents get operations only |
| The recommended test set: tries ledger with deflated Sharpe, 2x cost stress, out-of-sample in R, plateau check, PBO per family, block bootstrap for sizing and the live cone, one frozen baseline card per unit | research 08 §1.6 | Yes | `judging.md` |
| What-if split: views that can only worsen results; filters that improve results become counted reruns | research 26 §5; research 43 §3.4 | Yes | §7 |
| One door reached three ways: the copilot's rows, a workflow `app_op {app: qmb, job: backtest}`, the Lab's QMB node pack through a `QmbPort` | engine AD-31, Lab AD-5 (G4b Q4) | Yes | §8 |
| PR 204: one landing function, child process, read-back by id; rebase is small | G4a §2.4 | Yes as the landing; the child process is replaced by the mini-app runtime | §5 |
| Crypto trade prints replay with a declared spread model and a lower-fidelity label; Binance top-of-book where it exists | research 43 §4 L08-07 | Yes | §7 |
| "Run on every bot across multiple instruments", preferred and hypothetical markets | his 20 Oct seed (T1:442); seeds "Registry" (ledger U-21) | Yes, as the sweep grid with every cell a counted try | §7 |
| Live results overlaid on the backtest (LEAN `report --live-results`) | research 30 §8; research 43 §3.4 Results row | Yes | §7 |

## 4. The shapes

### Shape A. QMB as a mini app, with the landing, run id and try ledger in the core (recommended)

- **What.** An `app.toml` for `qmb` (risk `runs`, kind `both`) with an MCP server and operations (§6). The server is a thin layer that imports the QMB library; QMB itself spawns nothing. The core host keeps PR 204's one landing function: it issues the run id, writes the try ledger, lands the `backtest-result`, and stamps who asked (`agent:<session>`, `workflow:<run>`, `user`).
- **Reuses.** The mini-app core (operations with schemas and approvals, the supervised process, the Job object on Windows, health logs, instance homes, `app_op` with version pins), PR 204's landing, QMB's library whole.
- **Variants.** A second version installs beside the first; a workflow pins which one it means (`app_op` `pin`); results carry the tester id and version; `compare` shows a parity diff. Before a version becomes the default, it reproduces the conformance pack (§6).
- **Hard cases.** A tester that crashes (the breaker trips and logs, by design); a tester that "forgets" to count tries (impossible, the core counts); a run on a server instance (the home machine answers through `remote`); Windows memory limits (the Job object; PR 204's limit was POSIX-only).
- **Maintain.** QMB's house rules stop being a problem: no child process or thread inside `qmb/host`.
- **Explain.** "QMB is an app inside QMX. Agents ask it to test a unit and wait for the answer. You can install a second version and compare them. QMX itself keeps the score of how many tests were run."

### Shape B. QMB stays a core library behind a host door (PR 204 rebased as designed)

- **What.** The host binds a backtest door; the door launches QMB in a child process (moved under `qmb/orchestrator/` to satisfy the house rules).
- **Hard cases.** Fine for one version. Variants need a second door or a version switch in the host.
- **Maintain.** The child process, its memory limit on Windows and its health logs are QMB's own code to keep.
- **Why not.** It rebuilds what the mini-app core already gives, and side-by-side variants have no home.

### Shape C. A fresh tester written from scratch on the LEAN and Jesse lessons

- **What.** Toss the 91,000 lines; write a lean event-driven tester around the unit.
- **Why not.** It throws away a working, tested set of ports, an optimiser and robustness batteries (G1 §4.4) to rebuild them; his rule never to remove shipped backend work casually (STATE correction 7) and research 52's "do not toss". A fresh tester remains possible later as a variant under Shape A, which is the point of Shape A.

**Pick: Shape A.** Reason: it gives him new versions and side-by-side variants with no new machinery, removes PR 204's house-rule breaks and its POSIX-only memory limit, and keeps the honesty parts (landing, run id, tries) in the core where a variant cannot skip them.

## 5. What stays in the core, and what QMB computes

| In the core (host code, never part of a tester) | In the QMB app (swappable) |
| --- | --- |
| The landing function: run id, `backtest-result` landing, principal stamp | Running a request: replay, fills, costs, robustness, optimisation |
| The try ledger (every run's daily R stream, for effective-try clustering) | Results: trades, money, R, excursions, receipts, slices |
| The judge and its presets (`judging.md`) | What-if views and counted reruns |
| The study spec (rules fixed before results are read) | Synthetic series and stress scenarios |
| The conformance pack runner | |

## 6. The QMB contract: what any QMB version implements

**Operations** (each with JSON Schema 2020-12 input and output in `app.toml`):

| Operation | In | Out | Approval |
| --- | --- | --- | --- |
| `backtest` | `unit` (id and version), `markets`, `window` (any start; default March 2020 when none is given), `data_recipe` (partitions by fingerprint, holdout off unless his study names one), `cost_profile`, `seed`, `purpose`, `study_ref` | a run handle; on completion the core lands a `backtest-result` | read-write research (runs without asking) |
| `sweep` | as `backtest`, plus a grid (markets, timeframes, parameter values inside declared ranges) | one result per cell, all in one family | same |
| `walk_forward` | as `backtest`, plus the split rule | per-window results and the joined test record | same |
| `robustness` | a result id and the battery (trade shuffle, candle perturbation, rule significance, block bootstrap, cost stress) | readouts in three words (overfit, good, conservative) plus numbers | same |
| `optimize` | a unit, its declared ranges, the target measure, constraints | candidate settings, each a counted try | same |
| `whatif` | a result id and a scenario set | views (can only worsen) or counted reruns (may improve) | same |
| `status`, `results`, `compare` | run ids or result ids | status; results; a parity diff by object id (fixes `compare_runs` reading only old artifacts, handoff "Smaller gaps") | read |
| `instruments` | none | the instrument records QMB can replay, with data levels | read |

**The `backtest-result` shape** (extends Library AD-29's one result shape): trades with money and R, excursions in R (MAE and MFE), the context receipt per trade (reading ids, versions and ages at entry and exit), costs split, tuned values in force, calibration rows from the run, slices by session and by state, the tester id and version, the run id, the seed, the data fingerprints, "costs uncalibrated" while GAP-0048 is open.

**The conformance pack** (S059). Golden runs on the dummy unit (`unit.md` §8): fixed data fingerprints, fixed seed, fixed cost profile; expected trade lists. A QMB version that reproduces them may become the default tester; one that differs shows a parity diff and stays a variant. The core runs the pack, not the variant.

**Who ran it.** The landing stamps the principal and the chat or workflow run; QMB's screen lists runs with who, when, which unit, which tester version, the verdict and the family's try count.

## 7. Inside QMB: rebuild, extend, keep

| Part | Verdict | Why | Touches |
| --- | --- | --- | --- |
| Replay reader | **Rebuild** as a windowed reader that keeps only `derive_horizon` plus the unit's declared lookback | the only lookback limit; memory grows with the square of the steps | `qmb/host/replay.py`, `replay_execution.py`; QML `evidence.py` and `MappingReadSurface` (G1 §4.3) |
| Typed-partition entry into the trading replay | **New** | Library data cannot reach a run that trades today | `replay_execution.py:68` (handoff item 1) |
| Execution inputs as data | **New**: the run config names cost, fill, financing and slippage adapters and the instrument record; the unit's socket replaces `BookAdmissionContext` for units | only fixtures can build them today | handoff item 2 |
| Runner | **Rebuild**: a runner that trades a compiled unit by reference, replacing `silent` | PR 204's gap | handoff item 3 |
| Sizes | **Change**: round to the lot step and refuse only below the minimum order, recording the residue | QMB refuses non-multiples today; real sizes rarely land exactly (`07-qmb-lineage.md` §7 item 4, B-L4) | `book_handler.py` sizing path |
| Results | **Extend** with R, excursions, receipts, slices, the cost split, calibration rows | money only today | `results/measures.py`; CT-32 and CT-29 projections |
| Trade-print and tape replay | **New**: crypto prints with a declared spread model and a lower-fidelity label; futures tapes when a route exists | quotes only today | `replay.py:608-625` |
| Funding cost port | **New**: funding as a scheduled cash event from recorded rates | perps results come out too good without it | `execution/` cost family |
| Margin and liquidation port | **New** for perps and futures (buying power, margin call) | LEAN models it; QMB has none (`07-qmb-lineage.md` B-L2) | `execution/` |
| Calendars | **Extend**: per-instrument calendars from the instrument record, beyond `forex-17NY` | futures sessions, indices' breaks, 24/7 crypto | financing and session code |
| What-if | **Rebuild** as two sets: robustness views (remove the top 5% of trades, fixed size instead of the sizer, entry one bar late, cost shock, missed limit fills, stops on mark price, funding at each settlement) and improvement filters as counted reruns | research 26 §5 | `analysis/project.py` |
| Sweep grid | **Keep**, as "run on every bot across multiple instruments", every cell a counted try | his 20 Oct seed | `sweep/` |
| Optimiser, robustness batteries, synthetic series, exact money, process per run, fingerprints | **Keep** | built and tested | none |
| Live-against-backtest overlay | **New** view: the node's journal for a period against QMB's replay of the same period | QuantConnect's reconciliation (research 30 §8) | results views |

## 8. How agents and he reach it

- **The copilot:** the existing `backtest` catalog rows stay its door (core toolset, so it has them by default) and forward to the QMB app's operations through the core landing (party P6 clash; lead's call: rows that forward, because they already exist and reach the copilot with no settings line). `app:qmb` in the default home preset is the fallback if forwarding proves awkward.
- **Workflows:** `app_op {app: qmb, job: backtest, pin: ...}` with no engine change.
- **The Lab:** its designed QMB node pack (`qmb.compile`, `qmb.run`, `qmb.sweep`, and the rest) through a `QmbPort` whose default adapter is the same `app_op` (Lab AD-5 via G4b Q4).
- **"It runs and waits."** A tool call waits for the result up to `qmb_tool_wait_s`, then returns the handle and the agent polls `status`; a workflow's `app_op` waits as long as the job runs. Agents never edit QMB and never build its inputs by hand.
- **Out of the box.** The first-start card offers one click to turn on QMX's default apps (QMB, the MIS, the practice node), since enabling an app is his act by design (G4b Q5).

## 9. His screen (notes for the UI agent, no UI code)

- A runs list: who ran it (copilot chat, workflow, him), when, the unit and version, the tester version, markets, the verdict word, the family's try count; filter by unit and by family.
- A run page: equity in R and in money, the trades table with excursions, the slices, the robustness readouts in three words, the calibration rows, "costs uncalibrated" while it applies.
- A versions panel: installed QMB versions, which is the default, the conformance pack's last result per version, and a parity diff between two versions.

## 10. Numbers (starting defaults, all editable)

| Number | Default | Why |
| --- | --- | --- |
| backtest start when none is given | March 2020; any start allowed | research 12; never a cap |
| holdout | off; his choice per study | ruling 137, PR 207 |
| `qmb_tool_wait_s` | 600 | a tool call should not idle for hours (`S:2798` idea via G4b §1.3); workflows wait fully |
| concurrent runs on This PC | CPU cores minus one | the machine's own limit, not an invented cap |
| app memory | unset (unlimited); his number if he sets one | `APPS/manifest.py` isolation (read this session) |
| breaker `max_errors` | 3 (shipped default, logged trips) | by design for monitoring (his 31 Oct words) |
| conformance pack match | identical trade list for the same seed and data | determinism |
| replay-match on paper | about 80% of trades | research 43 §5 |

## 11. Connection points

| From | To | What crosses | Door |
| --- | --- | --- | --- |
| Copilot or agent | QMB app | a run request; a run handle; a result id | `backtest` rows forwarding to the app |
| Workflow | QMB app | the same, pinned to a version | `app_op` |
| QMB app | core landing | the finished result; the run's daily R stream | `backtest_and_land` |
| QMB app | Library market-data door | partitions by fingerprint, holdout per study | `materialise` |
| QMB app | QML | the compiled unit by id and version | the factory seam |
| QMB app | instrument records | contract facts, calendars, data levels, cost profiles | snapshot |
| Judge | QMB results | result ids, the try ledger | `judging.md` |

## 12. Open for the architecture step

1. Where shipped first-party apps live in the repo (QMB, the node, the MIS): beside `examples/apps/`, or a new folder installed by default.
2. How the core landing receives a run's daily R stream for the try ledger (inside the result, or as a separate partition).
3. Whether the windowed reader and the streaming indicators (which also recompute over all history, G1 §2.3) are fixed in one packet.

## 13. Parked

- A GA sampler over block choices (Jesse's lineage idea, B-J7): after the first slice; it is one more sampler adapter.
- A Rust or compiled speed path (B-J7 note): only when trial counts make speed the limit.
- ML and RL experimentation inside QMB (the Lab holds training runs today).
