> STATUS 2026-10-16 (rubric walk): PARTLY-STALE. See 27-rubric-walk.md. Rulings in 26 win.

# 17 — Template catalogue: the quant developer, the Lab and the portfolio manager

Written 2026-10-16 by an ideation agent. This file proposes options; nothing in it is ratified. Inputs: files `01` to `15` in this folder. `12` (design synthesis) is the base, `13` covers failure handling, `14` covers folders, mini apps and `qmx app check`, and `15` sets the card format. Where this file disagrees with `12`, `12` wins until he rules. The portfolio cards are kept light, because the risk-sizing session (`09`) may reshape them.

Claim labels: `[retrieved]` means taken from a file in this folder or a source it cites. `[inferred]` means designed here.

Words used below (the same as `15`, plus four):
- **Template**, **variant**, **methodology**, **mode** (C, C+S, W, C+W), **step kinds** (`script`, `rule`, `model`, `agent`, `rlm`, `human`, `subflow`, `grader`, plus `fanout`) and **model role**: as defined in `15`.
- **Board**: the Experimentation Board. It is a backend object with notes, questions, charts and runnable sections, plus a workflow draft with run scope. `[retrieved]` `12` §(e).
- **Draft / published**: a draft is editable and runs only in the Lab sandbox. A published version is immutable, has a content hash, and is the only thing that runs anywhere else. `[retrieved]` `10` §1 ("Drafts never run; only published versions do").
- **Family**: every variant, child and retry that comes from one idea. The deflated Sharpe counts every trial in the family, dead ones included. `[retrieved]` `12` §(d), `15` R6.
- **Unit**: a placeholder for what the Lab hands to Portfolio, until the risk session names it. Its parts are a list, not fixed fields. `[retrieved]` `09` §3.1.

The Lab rule applies to every Lab template below. Inside the Lab, nothing asks him except two things: money (always read-only for agents) and publishing outside the Lab. Lab-scoped schedules run under a standing allow rule, bounded by the usage cap. `[retrieved]` `12` decision 2. Spend above his "ask above" number is the one extra ask: a pre-flight estimate is shown first, as in `15` R8.

---

## Summary table

| # | Template | One-line purpose | Mode | Trigger | Main output | Feeds next |
|---|---|---|---|---|---|---|
| **Lab / Experimentation Board** | | | | | | |
| L1 | Idea to first result (≤2 iterations) | Go from his rough idea to a backtested first result he recognises, in at most two round trips | C+W | He talks on a board or in the hub | Spec card + first-result scorecard (with 2-3 options if needed) | L2, D3, L4, L3, R6 |
| L2 | Run just this part (`run_scope`) | Run one step, one section or the whole board, reusing everything upstream that is still fresh | C+W (engine call) | A click or "run this bit" | Section result with fresh/stale badges | Board, L3 |
| L3 | Promote a tested method to the Library | Turn a board section that passed its gates into a reusable, versioned Library item | W | He clicks "promote", or L1/L4/D3 proposes | Library item (component, method, template) + lineage | Toolbox, R2, D4, template B, mini apps |
| L4 | Overnight Lab loop | Search a strategy space while he sleeps (Build Alpha style), behind a gate the agent cannot loosen, keeping every dead end | W | Lab-scoped cron, or "run this overnight" | Morning card: survivors, plateau map, dead ends | D3, P1, P4, R6, L3 |
| **Developer** | | | | | | |
| D1 | Component card to Lab build | Turn a component card into Graph and Code with tests that prove it | C+W | From R2 or a card, or manual | Tested component (draft, then published) | D4, D5, template B, L3 |
| D2 | Strategy to QMB backtest config | Compile a strategy or unit into a sealed experiment spec that QMB will accept | W (subflow) | Called by L1, D3, D4, L4, template B | Experiment spec + smoke run | Template B stage 9, D3, D4 |
| D3 | Iterate against QMB with overfit guards | The useful core of the old WF2 "annealing" loop: diagnose, make structurally different children, retest, capped | W, C to start | From template B stage 10, L1, or manual | Generation tree + survivor scorecard | Template B stage 12, P4, R6 |
| D4 | Variant generation and comparison | Make labelled variants (instrument, timeframe, parameters, spiced, structural) and compare them fairly | C+W | Manual, or from L1 options | Head-to-head comparison page | D3, L3, P1 |
| D5 | Indicator authoring | Write a new indicator with a reference test, a no-future test and a picture | C+W | Manual, or from R2 / D1 | Indicator in the Toolbox | D1, L1, L4 search space |
| D6 | ML / neural-net training run with a holdout | Train a model for a slot (entry, regime, sizing, throttle) with leakage checks and a sealed test touched once | C+W | Manual | Model card + model object in a slot | D2, D4, L4, MIS work |
| D7 | Mini app: create, check, publish | Build a mini app from a rough description, pass `qmx app check` (including render), install only on his click | C+S | He describes an app | Install card with check report | D8, D9 |
| D8 | Mini app: maintain, version, archive | Keep an app healthy, ship fixes as new versions, deprecate or archive with blast radius | W, C on a card | Health monitor, breaker trip, weekly | Health tab, version cards, archive card | D7 (new version), D9 |
| D9 | Mini-app-to-mini-app data pipeline | Wire one app's output into another's input, through typed artifacts and the host event bus | C+W | Manual | Pipeline folder + contract test report | D8, P2, workflows |
| D10 | Code health of Lab artifacts | Weekly check that Lab code, tests, data snapshots and memoised results still hold | W | Weekly cron | Health card (red, amber, green) + fix proposals | D1, D5, D8, R9-style review |
| **Portfolio manager (light)** | | | | | | |
| P1 | Portfolio-of-strategies combination study | Read-only simulation of how candidates combine with the book: correlation, combining methods, rebalance | C+W | Manual, or from P4 / L4 | Book-picture explainer | P4 |
| P2 | Daily portfolio report | Script-only snapshot of the book after the close | W | Weekday cron | Dashboard card | P3, morning brief |
| P3 | Decay and limit report | Flag units drifting outside their term sheet or limits; propose tighten-only actions | W | Daily cron + event | Red/amber/green list + tighten cards | P4, D3, R6 |
| P4 | Lab-to-Portfolio proposal pack | Bundle Lab evidence into at most three decision cards he signs | C+S | From L4, D3, P1, P3, or manual | Proposal pack (cards) | His signature, then paper (template B stage 12) |

Template A (Fill the Library) and template B (Build and prove) are in `12` §(d). R0 to R9 are in `15`. This catalogue plugs into them and does not replace them.

---

## Template cards: the Lab and the Experimentation Board

### L1 — Idea to first result in at most two iterations

| Field | Design |
|---|---|
| Purpose | He says "buy pullbacks to the 20 EMA in London when the daily trend is up" and sees a backtest that matches what he meant. **An iteration** is one round trip in which he looks at something and says "not that" (`[retrieved]` `12` §(e)). The target is two: one at the card, one at the result. |
| Mode | C+W. The hub copilot (Lab pack) talks with him. Building and running are a workflow the board owns. |
| Trigger and pre-check | He talks on a board, or in the hub with the Lab pack. Pre-check `script`, run before the first question: Library search for prior boards, term sheets, components and dead ends on the same mechanism (R0's pre-check); Toolbox search for indicators and components he named; data availability for the market and timeframe implied. Facts found are shown, never asked. |
| Steps | 1 `script` pre-check above. 2 `model` **draft and grill in one message**: a draft spec card *plus* up to five numbered questions, each with a recommended answer already written into the card. "Yes" accepts all. 3 `human` **iteration 1**: he corrects the card, not the code. 4 `grader` spec check: mechanism, market, timeframe, session, entry, exit (or `external_policy` labelled), filters, kill rule, data needed, "what would fake this". 5 `rule` **divergence check**: if one or more answers are still open and would change the logic, build two or three structurally different readings (arena) instead of asking again. Otherwise build one. 6 `agent` × 1-3 `fanout` builder: Graph and Code for each reading (D1 internals), with unit tests. 7 `subflow` D2: compile to a sealed experiment spec. 8 `script` QMB backtest, costs on, on the in-sample window only. 9 `script` quick gates: at least N trades, no lookahead lint fail, costs-on result, trade-list sanity (trades only in the stated session). 10 `model` writer: first-result JSON with "what I built from your words" beside each number. 11 `grader` render check. 12 `human` **iteration 2**: he picks a reading or says "that's it". 13 `script` iteration counter written to the board. |
| Gates and kill rules | No build before the spec grader passes. No run on the holdout: the first result is in-sample only and says so on top. Lookahead lint fails → the result is not shown as a number; the card says "blocked: lookahead" with the line. Daily Sharpe above 2 → banner "assume lookahead until shown otherwise" (`[retrieved]` `02` ml4t). If the Library holds a dead end with the same mechanism and market, the card says so on top and asks what is different (R0 rule). |
| Human points | Two only: the card (iteration 1) and the pick (iteration 2). A third iteration happens only if he asks. The board counts it and the weekly review studies why. |
| Memory and lessons | Board scope: the card, questions asked, answers, readings built, picks. Operator scope: what he rejected and why, so the next board does not propose it (`[retrieved]` `12` §(e)). Lessons: every third iteration is logged with "which question would have caught it". These logs train the question battery. |
| Roles | `grill` (questions and card), `builder`, `writer`. A `validator` is not needed at this stage: the first result is in-sample and is labelled so. |
| Failure policy | Build fails → doctor repair once (`13` §4), then the reading is shown as "could not build: <reason>" beside the others. QMB refusal is a result, not a failure. Data missing → stop before any model call, with proxy options. |
| Budget guard | At most 3 readings, 1 builder each, 30 turns each, 2 repair rounds. One QMB in-sample run per reading. Pre-flight estimate shown if the total is above his "ask above" number. |
| Output | Two board artifacts. **The spec card**: an animated "what I understood" card with the rules as a flow diagram. **The first-result scorecard**: one equity curve per reading side by side, trades on a candle chart for a sample week, the gate chips, an "in-sample only" stamp, and the iteration counter ("2 of 2"). |
| Feeds | L2 (he edits one section and reruns it), D3 (improve), L4 (search around it overnight), D4 (variants), L3 (promote once it passes template B gates), R6 (if it dies). |

### L2 — Run just this part (`run_scope`)

| Field | Design |
|---|---|
| Purpose | He changes the exit section and wants to see what changed, without rerunning data loading, features and the other sections. `run_scope` was designed once and then dropped; this card brings it back. `[retrieved]` `05` §7. |
| Mode | C+W. It is an engine call, made from a button on a section or from the copilot. |
| Trigger and pre-check | A click on "run this step", "run this section" or "run all", or the copilot hearing "just rerun the exits". Pre-check `script`: resolve the scope to a node set, then compute which upstream nodes are **fresh**. A node is fresh when its memo key (code hash, inputs hash, data snapshot, params, engine version) matches a saved result. |
| Steps | 1 `script` resolve scope: one node, a connected section, or all. 2 `script` freshness walk upstream. Fresh nodes return their saved result, stale nodes are listed. 3 `rule` if stale upstream nodes are all `script` kind and under the cheap-run limit, run them; otherwise show "3 steps upstream are stale (about 4 min, 0 tokens / about 2k tokens). Run them too?" with "yes" recommended. 4 run the nodes in scope. Each keeps its own kind: `script`, `model`, `agent` or `subflow`. 5 `script` gates that apply to the scope: compile, lookahead lint, costs on (when a backtest is in scope). 6 `script` diff against the last run of the same scope: numbers, trade list, equity. 7 `grader` render check on the section output. |
| Gates and kill rules | Drafts run only in the Lab sandbox, never live, never on the holdout. A result built on a stale upstream node is never shown without the "stale input" badge. Gates bound to the graph's content hash still run on every scoped run (`[retrieved]` `12` §(c)). |
| Human points | Only the stale-upstream prompt, and only when it costs tokens or exceeds the cheap-run limit. |
| Memory and lessons | Run scope: the memo keys. Board scope: the history of scoped runs, so "what changed since the last run" is one click. |
| Roles | None by default. A section that holds an `agent` node uses that node's own role. |
| Failure policy | Default (`15`). A failed node marks only its downstream as stale. Nothing finished is rerun. |
| Budget guard | Cheap-run limit (default: zero tokens and under 2 minutes). Above that, the stale prompt. Section model calls are cached by (model, prompt hash, params). |
| Output | The section's own output, plus a **diff strip**: before and after numbers, an equity overlay, and fresh, stale and reran badges on each node of the graph. |
| Feeds | The board, L3 once the section is the method he wants. |

### L3 — Promote a tested method to the Library

| Field | Design |
|---|---|
| Purpose | Turn "this regime filter section worked" into a Library item that other boards, templates and mini apps can reuse. The path is experiment → tested method → workflow or template → optional mini app (`[retrieved]` `05` §3a). |
| Mode | W. He clicks "promote", or a template proposes it with a one-tap card. |
| Trigger and pre-check | His click, or a proposal from L1, L4, D3 or D5. Pre-check `script`: the section has a passing gate record for its class (see gates), and no Library item has the same code hash (`library_dup` from `15`). |
| Steps | 1 `script` freeze: publish the section as an immutable version with a content hash. 2 `script` package by class: `component` (signal, filter, exit, sizing rule, regime classifier), `indicator`, `method` (a multi-step procedure such as "walk-forward with purge"), `workflow template` (a whole board flow). 3 `agent` write the README and the interface: inputs, outputs, parameters with defaults and ranges, warm-up, known failure cases, and the evidence links. 4 `script` tests travel with it: unit tests, the no-future test, and a fixture run. 5 `grader` folder check (Eve rules from `14` §1: path is the name, tests and evals beside the code). 6 `subflow` `library-write`, with lineage edges from board → item and from evidence runs → item ("proved by"). 7 `rule` if the class is `workflow template`: install it as a **variant base**, disabled until he enables it. |
| Gates and kill rules | Promotion gate by class. A component or indicator needs green unit tests, a passing no-future test, and an ablation result (host with vs without) on at least two hosts. A method needs a fixture run that reproduces its board result. A workflow template needs a fake-model dry run (`[retrieved]` `12` §(i)). A strategy is not promoted here: strategies go through template B gates. Nothing is promoted on in-sample evidence alone. |
| Human points | None inside the Lab (Lab rule). Publishing the item as a mini app, or using it in Portfolio, asks (D7, P4). |
| Memory and lessons | Library scope: the item, its versions, lineage, and the board it came from. Lessons: why a promotion failed its gate, kept on the board. |
| Roles | `writer` (README and interface), `validator` (reads the README against the code in a fresh context). |
| Failure policy | Gate fails → no promotion. The card lists the missing evidence and a "get it" button that runs the missing step with L2. |
| Budget guard | One writer call, one validator call. Tests are scripts. |
| Output | Library item card: what it does as a small diagram, its interface, evidence chips, and where it is used. |
| Feeds | Toolbox and Resources tiles, R2 (as an existing match), D4, template B, L4 search spaces, mini apps. |

### L4 — Overnight Lab loop (Build Alpha style)

| Field | Design |
|---|---|
| Purpose | While he sleeps: generate, backtest, validate, detect a plateau, change the search space, restart. Every revolution writes what it tried and why. "The model proposes, the pipeline decides." `[retrieved]` `06` §3.1, §3.5. |
| Mode | W. He sets it up in C ("run this around the London pullback idea overnight"). |
| Trigger and pre-check | A Lab-scoped cron (for example 23:00), or "run this overnight". Pre-check `script`: the usage governor has headroom; the search space file is valid; data snapshots exist; the family's trial count so far; `preflight` (`15`). No headroom → `[SILENT]` park until the window opens (`[retrieved]` `03` §9.6). |
| Steps | **Setup, once:** 1 `script` load the **search space** as data: signal classes, filters, exits, timeframes and markets in scope, parameter ranges, the fitness function chosen from his approved list, and the gate thresholds (read-only from Settings). 2 `script` load dead ends for this family so the first generation avoids them. **Each revolution:** 3 `model` generator proposes a batch of candidates (default 10) inside the search space, each with a one-line hypothesis. 4 `rule` dedupe against everything tried (by spec hash). 5 `subflow` D2 compile each candidate, `fanout`. 6 `script` QMB in-sample backtests, `fanout`, costs on. 7 `script` validate: walk-forward on the validation window, Monte Carlo, cost stress at 1.5x, minimum trades. 8 `script` record every trial in the family ledger, passed or not. 9 `script` **plateau detect**: no gain in the best *validated* score for K trials (default 30) or 2 revolutions. 10 `rule` plateau → step 11; budget left → step 3; else step 12. 11 `model` **change the search space** by one fixed move: add a class, drop a class that never survives, widen or narrow one range, switch timeframe within scope. It writes the reason and keeps the old space as a dead-end region. Restart from step 3. **End:** 12 `script` rank survivors by validated score. 13 `script` **holdout, touched once**: the top 3 survivors run on the sealed holdout. 14 `script` deflated Sharpe over every trial in the family tonight and before. 15 `subflow` R7 calibrate (rerun spread across seeds and block bootstraps). 16 `model` writer: morning card. 17 `subflow` `library-write` for dead ends and the plateau map. |
| Gates and kill rules | **The gate the agent cannot loosen**: thresholds are read from Settings and bound to the graph's content hash. The loop's tool allow-list has no Settings write and no write to the search-space fitness list. A lint rejects any step that edits a threshold. Search-space moves come from a fixed list. Changing the fitness function is not a move. The holdout is touched once per night, by step 13 only. Deflated Sharpe counts the whole family, dead parents included (`[retrieved]` `15` R6). Survivors whose holdout result falls outside the validation Monte Carlo band are marked "did not hold" and kept as dead ends. Daily Sharpe above 2 → lookahead audit before ranking. |
| Human points | None during the night. In the morning, at most two decisions on the card, each with a recommendation (for example "send candidate 3 to D3 for improvement: yes"). |
| Memory and lessons | Workflow scope: the search-space history (every move with its reason) and the best-so-far. Home scope: dead ends tagged `negative_result` with run ID, variant count, and the region of the space they came from. Lessons: which moves broke plateaus, read by the generator next time. |
| Roles | `generator` (mid), `writer`. Every gate is a script. No model grades results. |
| Failure policy | Default. A QMB failure on one candidate drops that candidate, counts it as a trial, and the run continues. Usage cap → drain at a step boundary, park, resume after the reset (`[retrieved]` `03` §9.6). |
| Budget guard | Trials per night (default 200), revolutions (default 6), search-space restarts (default 3), generator calls (one per revolution). Wall-clock deadline (default 07:00). At a cap: stop, then run steps 12-17 on what exists. |
| Output | Morning card: the plateau map (a heat map of the search space, with tried regions and dead regions), the survivors' scorecard (in-sample, validation and holdout bars), the trial count and deflated Sharpe, "4 new dead ends", and two decisions. `[SILENT]` if nothing ran. |
| Feeds | D3 (improve a survivor), P1 (does it fit the book), P4, L3 (a component that kept appearing in survivors), R6 (dead ends). |

---

## Template cards: the developer

### D1 — Component card to Lab build (Graph and Code) with tests

| Field | Design |
|---|---|
| Purpose | Turn a component card (signal, filter, exit, sizing rule, regime classifier) into a runnable Lab piece in both views, with tests that prove it does what the card says. |
| Mode | C+W. The copilot confirms the card, and the workflow builds. |
| Trigger and pre-check | From R2, from a card on a board, or manual. Pre-check `script`: the card passes its schema (every parameter has a value or `unresolved`); `library_dup` on the formula hash. |
| Steps | 1 `script` scaffold the component folder from the class template: interface, parameter schema, `tests/`, fixtures. 2 `agent` builder writes the **test first**: a worked example from the card or paper, edge cases (empty bars, gaps, first bar after warm-up), and the no-future test (step 4). 3 `agent` builder writes the code until the tests pass. 4 `script` **no-future test**: compute on data truncated at bar t and on the full data; values at t must match for a sample of t. This catches lookahead without a model. 5 `script` lint, type check, and a speed check (bars per second on a fixed dataset). 6 `script` produce the **Graph view** from the code's declared steps, and check that Graph and Code round-trip (Graph → code → Graph is the same graph). 7 `script` sample picture: the component on a fixed chart week. 8 `grader` review by `validator` on another family: does the code match the card? Are any values invented? 9 `rule` all green → publish as a version. Otherwise it stays a draft with the failing check named. |
| Gates and kill rules | No publish without green tests and a passing no-future test. A test written after the code fails the "test first" check: the builder's transcript is checked for the order. A failing test twice after one repair → card saved as `fragment` with the failure note (R2 rule). |
| Human points | None. Two readings of a formula that change the meaning → `human` with both readings and a recommended one. |
| Memory and lessons | Lineage card → component version. "Formula traps" lessons shared with R2. |
| Roles | `builder`, `validator`. |
| Failure policy | Retry, doctor repair (bigger model or more turns), then escalate with the failing test. |
| Budget guard | One builder, 30 turns, two repair rounds. |
| Output | Component page: a picture of the signal on the chart, the Graph view, test results as chips, the interface table. |
| Feeds | D4 (variants), template B as an ablation, L1 and L4 (it becomes a Toolbox item), L3. |

### D2 — Strategy to QMB backtest config (sealed experiment spec)

| Field | Design |
|---|---|
| Purpose | Compile a strategy, unit or candidate into an experiment spec QMB accepts, with the data snapshot, costs, seed, splits and holdout fixed before any result is seen. Today agents can run only pre-registered configs (`[retrieved]` `05` §2), so this template is how specs get registered. |
| Mode | W, as a `subflow` called by L1, L4, D3, D4 and template B. It is also callable from chat ("make a backtest config for this"). |
| Trigger and pre-check | Called with a strategy reference. Pre-check `script` `data_available` for the instruments, timeframes, fields and periods. |
| Steps | 1 `script` resolve the strategy version (code hash) and its parameter space. 2 `script` pick the **data snapshot** (frozen ID) and the **cost model** (spread, commission, slippage, swap) for the venue. 3 `script` **splits**: in-sample, validation (walk-forward folds), and the **holdout**. The holdout is the family's sealed window. It is created once per family and is later than all other windows. 4 `script` checks: point-in-time fields only; session and timezone consistent with the strategy; minimum bars per split; holdout not overlapping any window already used by this family. 5 `script` write the spec (CT-47 shape: code ref, config, data snapshot, costs, seed, lineage; `[retrieved]` `08` stage 9) and register it through the host validator. 6 `script` smoke run on one month in-sample: it must compile, trade, and produce a ledger row. 7 `script` memo key. |
| Gates and kill rules | No spec without costs. No spec whose holdout overlaps a window the family already used. Smoke run with zero trades → "check logic" flag, not a failure. |
| Human points | None. |
| Memory and lessons | Family holdout registry (window, created, touched count). Spec ledger. |
| Roles | None. The template is all scripts. |
| Failure policy | Script retry. A host validator refusal is a result, and the reason is passed to the caller. |
| Budget guard | Zero tokens. One smoke run. |
| Output | Spec card: windows drawn on a timeline (in-sample, folds, holdout locked), the costs table, the snapshot ID. |
| Feeds | Template B stage 9, D3, D4, L1, L4. |

### D3 — Iterate against QMB with overfit guards (the old WF2 core)

| Field | Design |
|---|---|
| Purpose | Improve one strategy honestly: read the reports, form hypotheses about *why* it is weak, make 3-4 structurally different children, retest, keep survivors, stop on a budget or a plateau. "Tests diagnose; agents create." `[retrieved]` `08` §1a, §1e. |
| Mode | W. He starts it in C or accepts a proposal. |
| Trigger and pre-check | Template B stage 10 result, an L1 or L4 survivor, or manual. Pre-check `script`: the parent has a full report (backtest, walk-forward, Monte Carlo, regime and session breakdown); the family trial count; budget headroom. |
| Steps | 1 `script` load the reports and the regime/session breakdown. 2 `model` diagnoser: sort weaknesses into buckets (costs, one regime only, one session only, drawdown clustering, too few trades, exit too loose or too tight). 3 `model` diagnoser: one hypothesis per bucket about *why*, each with the evidence row. 4 `model` generator: 3-4 **structurally different** children (for example trend-filtered, volatility-adaptive, session-filtered, exit-replaced), each linked to a hypothesis. Parameter nudges alone are not a child. 5 `rule` dedupe by spec hash against the family ledger. 6 `agent` builder × children, `fanout` (D1 internals for new components). 7 `subflow` D2 for each child. 8 `script` QMB in-sample and walk-forward, `fanout`. 9 `script` robustness gates (template B stage 10 set). 10 `script` record every child in the family ledger. 11 `rule` loop: next generation from the best survivor, or stop. 12 `script` holdout touched once, on the final survivor only. 13 `script` deflated Sharpe over the whole family. 14 `subflow` R7 calibrate. 15 `model` writer. |
| Gates and kill rules | **3 generations × 4 children at most; stop after 2 generations with no gain; every child counts; holdout touched once** (`[retrieved]` `12` §(d) stage 11). A child that "wins" only in-sample is dead. A child must name the hypothesis it tests. The diagnoser may not see holdout numbers. |
| Human points | Starting it (or accepting the proposal). He sets the budget once in Settings. |
| Memory and lessons | Family ledger: parent → child with what changed and why. Dead children are tagged `negative_result`. Lessons: which buckets each kind of change fixed, read by the next diagnoser. |
| Roles | `diagnoser`, `generator`, `builder`, `writer`. |
| Failure policy | Default. A failed build counts as a dead child with "could not build". |
| Budget guard | Children cap as above. One builder per child, 20 turns. Per-run dollar cap with reserve-then-refund. |
| Output | Generation tree: each node is a child with its change label and score bars. Dead branches are greyed, not hidden. The survivor scorecard sits at the bottom. |
| Feeds | Template B stage 12 (paper card) through P4, R6 (dead children), L3 (a component that fixed a bucket). |

### D4 — Variant generation and comparison

| Field | Design |
|---|---|
| Purpose | Make labelled variants of one strategy and compare them fairly. Variants can differ by instrument, timeframe, parameter set, spiced add-ons, or structure. He asked for variants made by two agents to be compared side by side (B36, `[retrieved]` `10` §1). |
| Mode | C+W. |
| Trigger and pre-check | Manual ("try this on GBPUSD and on 15 minutes"), or L1 when it built several readings. Pre-check `script`: data for each variant; the identity rule decides whether each variant is a variant, a new strategy, or a profile version. |
| Steps | 1 `model` planner turns his request into a variant list with a label per variant (from a fixed label set: `instrument`, `timeframe`, `params`, `spiced`, `structural`, `model-made`). 2 `rule` identity rule (a table the engine reads, `[retrieved]` `09` §3.5): label → lineage edge. 3 `script` branch each variant (git-style branch of the draft). 4 `agent` builder only for `spiced`, `structural` and `model-made` variants. The others are config changes made by scripts. 5 `subflow` D2 per variant, all on the **same** windows and costs. 6 `script` QMB runs, `fanout`. 7 `script` comparison: per-variant metrics, a head-to-head equity overlay, correlation between variants, and deflated Sharpe over the variant set. 8 `script` "luck warning" when the best variant's edge over the median is inside the bootstrap spread (`[retrieved]` `10` §1 scenario builder). 9 `model` writer. |
| Gates and kill rules | Every variant counts as a trial in the family. Comparison only on identical windows and costs; the template refuses a mixed comparison. The holdout is not used in a comparison. |
| Human points | He picks which variants go forward, or ignores them. |
| Memory and lessons | Lineage edges per variant. Lessons: which label kinds tend to survive for this family. |
| Roles | `planner`, `builder`, `writer`. |
| Failure policy | A failed variant is shown as failed and still counted. |
| Budget guard | At most 12 variants per run (his number). At most 4 builder variants. |
| Output | A head-to-head page: variant cards in a row, an overlay chart, a small correlation grid, and the luck warning. |
| Feeds | D3 (improve the best one), L3, P1. |

### D5 — Indicator authoring

| Field | Design |
|---|---|
| Purpose | He says "I want an indicator that measures how fast the spread widens before news". QMX writes it, proves it, and adds it to the Toolbox. He asked to be able to add indicators (`[retrieved]` `10` §1). |
| Mode | C+W. |
| Trigger and pre-check | Manual, or from R2 or D1 when a component needs a new indicator. Pre-check `script`: Toolbox and Library search for an existing indicator with the same formula or name. A Pine script given as the source goes through the Pine parse step from R5. |
| Steps | 1 `model` grill: up to three questions with recommended answers (inputs, smoothing, output range). The answers are folded into a spec: formula, inputs, parameters, warm-up, output type, repaint risk. 2 `script` scaffold. 3 `agent` builder: tests first (a reference implementation where one exists, such as TA-Lib or pandas-ta values for a known indicator, or hand-computed values for a small table), then the code. 4 `script` no-future test (D1 step 4). 5 `script` warm-up check: the first N values are NaN-flagged, not zero. 6 `script` speed check. 7 `script` picture on a fixed chart week, plus a distribution plot. 8 `grader` `validator` on another family: does the code match the spec? 9 `subflow` L3 to publish it to the Toolbox (class `indicator`). |
| Gates and kill rules | The no-future test must pass. A Pine source with `lookahead_on` or a repaint flag is rebuilt without it, and the rebuilt version is labelled as a child. |
| Human points | Grill answers. |
| Memory and lessons | Toolbox entry, lineage from the source. |
| Roles | `grill`, `builder`, `validator`. |
| Failure policy | Default. |
| Budget guard | One builder, 20 turns, two repair rounds. |
| Output | Indicator card: a chart with the indicator under price, the formula rendered, test chips. |
| Feeds | D1, L1, L4 search spaces, MIS work. |

### D6 — ML / neural-net training run with a holdout

| Field | Design |
|---|---|
| Purpose | Train a model for a slot (entry signal, regime, sizing, risk throttle, or his own) without leaking the future and without peeking at the test set. `[retrieved]` `10` §1 (Training tile, Model slots). |
| Mode | C+W. The copilot sets the scope with him. The workflow trains. |
| Trigger and pre-check | Manual. Pre-check `script`: dataset exists; features are point-in-time; compute place and cost estimate. Above his "ask above" number, show the estimate and wait. |
| Steps | 1 `model` grill: up to five questions with recommended answers (slot, label definition, horizon, features, model family). 2 `script` build the dataset: features, labels, timestamps, all point-in-time. 3 `script` split: train, validation, **sealed test**, with purge and embargo between them (`[retrieved]` `02` ml4t `purging-embargo`). The sealed test is created once per model family. 4 `script` leakage checks: label horizon versus purge gap; features computed only from data before the label start; a shuffle test (a model trained on shuffled labels must score near chance). 5 `script` train on the chosen compute (`runs_on`), with checkpoints. 6 `script` evaluate on validation: metrics, loss curves, and the "likely overfitting" flag when the train/validation gap passes his threshold. 7 `rule` up to K configs (default 6) may be tried on validation. Each counts as a trial. 8 `script` **sealed test, touched once**, on the chosen config only. 9 `script` plug into the slot and run D2 + QMB on a host strategy with vs without the model (ablation). 10 `subflow` R7 calibrate (seeds). 11 `model` writer: the model card. |
| Gates and kill rules | Shuffle test above chance → stop (leak). Sealed-test result outside the validation band → "did not hold", kept as a dead end. The model is not published unless the ablation shows a gain after costs. A second look at the sealed test is a new, counted trial and needs a new sealed window. |
| Human points | Grill answers. Compute spend above his number. |
| Memory and lessons | Model object with version, dataset hash, split windows, and metrics. Model family trial count. Lessons: leaks found and how. |
| Roles | `grill`, `builder` (training code when not a stock model), `writer`. |
| Failure policy | Training crash → resume from the last checkpoint on the same compute. Compute lost → move with the checkpoint (`[retrieved]` `12` §(b) "where it runs"). |
| Budget guard | GPU hours and dollar cap per run. Config trials (K). A training run never starts without an estimate. |
| Output | Model card: loss curves, split bar (train, validation, sealed test with a lock icon), feature importance, the ablation result, and the slot it plugs into. |
| Feeds | D2 and D4 (strategies using the model), L4 (model as a search-space class), MIS labeller work. |

### D7 — Mini app: create, check, publish (gated)

| Field | Design |
|---|---|
| Purpose | He describes an app roughly. QMX builds it as a plugin folder, proves it works with `qmx app check`, and installs it only on his click. `[retrieved]` `12` §(g), `14` §2.5-2.6. |
| Mode | C+S. The hub copilot runs the interview. Sub-agents build and review. |
| Trigger and pre-check | He says "make me an app that…" in the hub or on the Apps page. Pre-check `script`: existing apps and templates that already do it; the Lab objects it would read (`data_reads`) exist. |
| Steps | 1 `model` grill: up to five questions with recommended answers (what it shows, where it renders as a `[ui.targets]` slot, what it reads, what it provides, schedule). 2 `agent` × 2-3 `fanout` **prototype** widget layouts on sample props (arena); he picks one. 3 `script` scaffold the folder: `.claude-plugin/plugin.json`, `app.toml` with `[ui.targets]`, `[io]`, `[health]`, `[lifecycle]` set to `draft`, `qmx_api`, `skills/`, `.mcp.json`, `monitors/`, `tests/`, `evals/`, `fixtures/`. 4 `agent` builder: tests first (unit tests, contract tests against `provides`), then the MCP server and the widgets. 5 `script` `qmx app check` steps 1-9: manifest, secrets and paths, build and bundle size, unit tests, contract tests, sandbox run, load check, agent eval, **render check**. The render check loads each widget with sample, empty, error and loading props, fails on console errors or failed requests, checks it fits its slot, and saves screenshots. 6 `grader` review by `validator` on another family: code against the interview and the check report. 7 `script` check step 10 (shadow) for `runs` apps. 8 `human` **install card**: what it does, the screenshots, the check report, the box (budget, network allow-list, breaker), and the blast radius. Install always asks. 9 `script` install **disabled**, trust from his approval record. He enables it. |
| Gates and kill rules | No install card until every check line is pass or needs-human. Render check failures block. No money tools on any allow-list; the hook refuses (`[retrieved]` `12` §(h)). A `money` risk class cannot be created by an agent. |
| Human points | Grill answers, prototype pick, install. |
| Memory and lessons | App folder in git; check records are immutable. Lessons: check lines that failed most often feed the `build-mini-app` skill. |
| Roles | `grill`, `builder`, `validator`, `judge` (optional second pass on screenshots, vision-capable). |
| Failure policy | Check line fails → builder repair, at most two rounds, then escalate with the failing line. |
| Budget guard | 3 prototypes at most, one builder (40 turns), two repair rounds. |
| Output | Install card with a widget gallery (four states each), a check report (pass, fail, needs-human per line), and the box. |
| Feeds | D8, D9, the Apps page. |

### D8 — Mini app: maintain, version, deprecate, archive

| Field | Design |
|---|---|
| Purpose | Keep installed apps healthy. Ship fixes as new versions. Retire apps cleanly, archiving them and never deleting them. |
| Mode | W for monitoring. C when a card needs him. |
| Trigger and pre-check | The `[health]` probe (monitor slot), breaker trips, failure streaks, a weekly retro cron, and a change request from him ("change weekend-watcher so it…"). Pre-check `script`: probe status, last run age, error rate. Healthy and no request → `[SILENT]`. |
| Steps | **Health:** 1 `script` probe and logs. 2 `rule` unhealthy → incident (deduped by error signature). 3 `model` doctor reads logs and the trace and sorts the cause: transient, bad input, upstream schema change, logic wrong. 4 `rule` transient → restart inside the breaker policy; anything else → fix path. **Fix or change:** 5 `agent` builder on a new draft version: test first that reproduces the bug or describes the change. 6 `script` `qmx app check` (all lines). 7 `grader` `validator`. 8 `human` publish card (a new version always asks), with the diff and blast radius: which apps and workflows consume its outputs. **Retire:** 9 `model` writes a deprecate or archive card: why, `replaced_by`, consumers affected, and data kept. 10 `human` he approves. 11 `script` set `[lifecycle]` to `deprecated` or `archived`; versions, evidence, logs and artifacts are kept. Consumers get a "producer archived" event. |
| Gates and kill rules | No in-place edit of a published version. The old version stays installable for rollback. Archive with live consumers needs the consumers rewired or explicitly accepted as stale. There is no delete route (`[retrieved]` `12` §(g)). |
| Human points | Publish of a new version, deprecate, archive, disable. |
| Memory and lessons | Incident history per app. Lessons into the `debug-app` skill. |
| Roles | `doctor`, `builder`, `validator`, `writer`. |
| Failure policy | Default ladder. Breaker trips are incidents, not retries. |
| Budget guard | Doctor cheap-first. One builder per fix, 30 turns. |
| Output | The app's DevOps tab: health line, incidents, versions, and the evidence road. Cards for publish and archive. |
| Feeds | D7 (version through the check), D9 (rewire consumers). |

### D9 — Mini-app-to-mini-app data pipeline

| Field | Design |
|---|---|
| Purpose | "When macro-daily-bias publishes, feed it to my session-filter app, then show the result in the Lab." Apps talk only through typed artifacts and the host event bus. No app calls another app's internals. `[retrieved]` `12` §(h), `14` §2.5. |
| Mode | C+W. The copilot plans the wiring. The pipeline is a workflow folder. |
| Trigger and pre-check | Manual. Pre-check `script`: both apps exist and are enabled; the producer's `provides` schema version and the consumer's `feeds` schema are compatible (JSON Schema subset check). |
| Steps | 1 `model` planner: draw the pipeline (producers, consumers, triggers, transforms) and ask at most three questions with recommended answers. 2 `rule` incompatible schemas → propose a **transform step** (a `script` mapping, written and tested) or a new consumer version through D8. 3 `script` write the pipeline folder: `workflow.yaml` with `inputs_from` (optional `wait`), `emits` and `accepts` wiring, and a trigger row ("after app X emits Y"). 4 `script` contract test with recorded fixtures: producer fixture → transform → consumer accepts; outputs validate against the consumer's `provides`. 5 `script` shadow run on live artifacts with outputs discarded, for a set period. 6 `human` enable card: the pipeline as a diagram, schemas, schedule, and blast radius. A pipeline outside the Lab is a standing schedule, so it asks. For an external webhook in: a signed secret under `qmx/*` and a trigger row he approved (`[retrieved]` `12` §(h)). |
| Gates and kill rules | A run never consumes an unvalidated artifact. A producer version change re-runs the contract test before the pipeline accepts new output. A webhook body is untrusted data. It is written as an artifact before any trigger fires. |
| Human points | Enable, and webhook secrets (he enters them himself in the keyring). |
| Memory and lessons | Pipeline version pinned to producer and consumer versions. |
| Roles | `planner`, `builder` (transforms only). |
| Failure policy | Producer missing or late → the consumer either waits (if `wait: true`) or uses the last good artifact with a "stale" mark. Schema break → pipeline paused and a D8 card raised. |
| Budget guard | Transforms are scripts, so zero tokens per run. |
| Output | A pipeline diagram with live status per edge (last artifact age, schema version) on the DevOps view. |
| Feeds | D8, P2 (apps that feed reports), other workflows. |

### D10 — Code health of Lab artifacts

| Field | Design |
|---|---|
| Purpose | Every week, check that Lab code, tests, data snapshots and saved results still hold, and propose fixes. Deterministic checks run first (`[retrieved]` memory, QA phase design: deterministic battery first). |
| Mode | W. |
| Trigger and pre-check | Weekly cron, plus an event when QMB, the data store or a dependency changes version. Pre-check `script`: anything changed in the Lab since the last run. |
| Steps | 1 `script` lint, type check and tests for every published Lab item and every draft touched this week. 2 `script` dead code (Vulture or Skylos) and coverage. 3 `script` no-future test on all components and indicators. 4 `script` **reproducibility**: rerun a random sample of memoised backtests (default 10) and compare result hashes. A mismatch means engine or data drift. 5 `script` data snapshot integrity (hashes, gaps added). 6 `script` dependency drift (lockfile vs installed). 7 `script` orphan check: Library items whose lineage points at missing versions, boards referencing archived items. 8 `model` analyst: cluster findings and rank by blast radius. 9 `agent` builder: fixes on **new drafts only**, written to `pending/`, each with a failing test first. 10 `script` tests on the fix drafts. |
| Gates and kill rules | Published versions are never edited. A fix is a new version through the normal path. A reproducibility mismatch freezes promotions from the affected engine or data version until he looks. |
| Human points | Approves fixes in `pending/`. Reads the freeze notice if one is raised. |
| Memory and lessons | Health history per item. Lessons: recurring failure classes go to the `correct`-style rule table (`[retrieved]` `02` pstack `correct`). |
| Roles | `analyst`, `builder`. |
| Failure policy | A partial run still ships, with gaps listed. |
| Budget guard | Scripts first. At most 5 fix drafts per week. |
| Output | Health card: red, amber and green by item. A reproducibility strip. Fix proposals as diff cards. |
| Feeds | D1, D5, D8, the weekly harness review. |

---

## Template cards: the portfolio manager (light)

Everything here reads money and never moves it. Portfolio is human-driven. Sizing authority lives in the GitBook and node docs (`[retrieved]` `06` §3.4). The promoted noun is "unit", and the combining and sizing method lists are data, so the risk session can change them without changing these templates (`[retrieved]` `09` §3).

### P1 — Portfolio-of-strategies combination study (read-only simulation)

| Field | Design |
|---|---|
| Purpose | Answer "does this candidate add anything to the book, and how would they combine?" with a simulation that changes nothing. |
| Mode | C+W. The hub with the Lab and Portfolio packs. |
| Trigger and pre-check | Manual, or from L4, D3 or P4. Pre-check `script`: every candidate has out-of-sample or paper return streams; the overlap with the book's streams is at least his minimum (default 12 months). |
| Steps | 1 `script` load return streams: out-of-sample and paper only, never in-sample. Book units from paper/live journals, in R and USD. 2 `script` align on a common calendar and costs basis. 3 `script` correlation (full period and in stress windows), clustering, drawdown overlap. 4 `script` combine with each method in the **method list** (default list: equal weight, inverse volatility, risk parity, hierarchical risk parity; plus whatever the risk session adds), each at several rebalance frequencies, costs on. 5 `script` stress: named crisis windows, and a block bootstrap of the combined stream. 6 `script` marginal value: book with vs without each candidate. 7 `subflow` R7 calibrate (bootstrap bands on the marginal value). 8 `model` writer. |
| Gates and kill rules | Read-only: the tool allow-list has Portfolio reads and simulations only. A candidate whose marginal value band crosses zero is never called "adds to the book". Methods are labelled "study only" until the risk session ratifies one. |
| Human points | None. He reads it. |
| Memory and lessons | The study is stored with its inputs' hashes so P4 can cite it. |
| Roles | `writer`, `explainer`. |
| Failure policy | A missing stream drops that candidate with "could not study: no out-of-sample stream". |
| Budget guard | Zero tokens until the writer. One writer call. |
| Output | Book-picture explainer: "which strategies zig when others zag" as a correlation map, combined equity per method, drawdown overlap, marginal value bars with bands. |
| Feeds | P4. |

### P2 — Daily portfolio report (script-only)

| Field | Design |
|---|---|
| Purpose | One screen after the close: what the book did, where it stands against its budgets. Zero tokens. `[retrieved]` `11` T5 pattern. |
| Mode | W. |
| Trigger and pre-check | Weekday cron after the last session close. Pre-check `script` `preflight`: broker reads reachable; journals updated today. On failure: `blocked_config`, one alert, no report. |
| Steps | 1 `script` positions, closed trades, PnL in R and USD per unit. 2 `script` exposure by instrument and currency, correlation of today's moves. 3 `script` drawdown against the account loss budget and kill line (read-only). 4 `script` paper units: today's result against their backtest Monte Carlo band. 5 `script` render the dashboard card. 6 `grader` render check. |
| Gates and kill rules | None; it is a report. Numbers come only from scripts with source rows. |
| Human points | None. An "explain this" button wakes the hub on demand. |
| Memory and lessons | Daily snapshot rows, used by P3. |
| Roles | None. |
| Failure policy | Spend-neutral retry ladder 5, 15, 30 min. Then one alert. |
| Budget guard | Zero tokens. |
| Output | Dashboard card: book equity, a per-unit R bar, exposure donut, drawdown versus budget gauge, paper units inside or outside band. |
| Feeds | P3, the morning brief. |

### P3 — Decay and limit report

| Field | Design |
|---|---|
| Purpose | Find units drifting away from their term sheet or close to limits, and propose only tightening actions: bench, back to paper, shrink. `[retrieved]` `09` §2 ("decay and benching ... only through tightening actions"). |
| Mode | W. C when he opens a card. |
| Trigger and pre-check | Daily cron after P2, plus events (a limit at 80% of budget). Pre-check `script`: compute the classification first; all green → `[SILENT]` digest line. |
| Steps | 1 `script` rolling metrics per unit (expectancy in R, win rate, trade frequency, slippage) against the term sheet and the backtest Monte Carlo band. 2 `script` change detection (CUSUM on R per trade; regime label from the MIS where available). 3 `script` limit use per unit and per account (read-only). 4 `rule` classify with a **pluggable decay definition** (default: amber when outside the 90% band for 10 trades, red when the term sheet's kill criterion trips). 5 `model` explainer, only for amber and red: what changed, with evidence rows. 6 `rule` red → draft a tighten-only card (bench, back to paper, shrink within declared ranges). Any loosening is not an option on the card. |
| Gates and kill rules | Agents never act on the account guard. Cards are proposals; nothing changes without his click. A red unit with no explanation still gets its card. |
| Human points | Signs or rejects tighten cards. |
| Memory and lessons | Decay history per unit. A unit that died in live is linked back to its Lab family as a `negative_result` (feeds R6). |
| Roles | `explainer` (cheap). |
| Failure policy | Default. Missing data → "could not check" row, never silently green. |
| Budget guard | One explainer call per amber or red unit, at most 5 per day. |
| Output | Red/amber/green list with sparkline per unit and its band. Tighten cards. |
| Feeds | P4 (demotion proposals), D3 (rehab of a decayed unit, the old WF3 role), R6. |

### P4 — Lab-to-Portfolio proposal pack he signs

| Field | Design |
|---|---|
| Purpose | Bundle Lab evidence into at most three decision cards: promote to paper, promote paper to live (his click only), demote, or add to the book. A mixed session may **propose** a Portfolio change; only his signature writes it. `[retrieved]` `12` §(b), §(h). |
| Mode | C+S. The hub with the Lab and Portfolio packs. A `validator` sub-agent works in a fresh context. |
| Trigger and pre-check | From L4, D3, P1 or P3, or manual ("should this go to paper?"). Pre-check `script`: the evidence each card type needs exists. Promote to paper needs template B stage 10 passed, P1 study done, and the holdout result. Live needs the paper window met (default 2 weeks and 30 trades, inside the Monte Carlo band; `[retrieved]` `08` Q9). |
| Steps | 1 `script` gather evidence pointers. 2 `agent` `validator` on another family re-opens the evidence (not the summary) and tries to disprove each card. 3 `model` pre-mortem: "it is three months later and this failed; why?" (`[retrieved]` `06` §3.5). 4 `subflow` R7 calibrate on headline numbers. 5 `model` writer: one card per decision with recommendation, default, consequence of silence, door type (one-way or two-way) and blast radius (`[retrieved]` `06` §3.3-3.4). 6 `grader` render check. 7 `human` he signs or rejects each card. 8 `script` on signature: write the change through the Portfolio's own path (paper start, demotion). Live promotion stays a separate click by him; no agent path. |
| Gates and kill rules | At most three cards per pack. A contested validator finding goes on the card in red. No card without its evidence links. Agents never call a money-moving tool; `propose_order` stays unsigned (`[retrieved]` `05` §5). |
| Human points | Signs every card. |
| Memory and lessons | Signed and rejected cards with reasons (operator scope, a taste signal). |
| Roles | `validator`, `writer`. |
| Failure policy | Validator fails → the card ships with "not independently checked" and cannot carry a "yes" recommendation. |
| Budget guard | One validator per card, 20 turns. |
| Output | Proposal pack: decision cards with an evidence strip (backtest, walk-forward, holdout, P1 marginal value), a pre-mortem box, and sign and reject buttons. |
| Feeds | Paper (template B stage 12), P3 watching, the Library (promotion history). |

---

## User-creatable variants: cloning a Lab, developer or PM template

The mechanism is the one in `15`: a variant is a thin folder (`variant.toml` with `extends`, `overrides.toml`, his skills, 3-5 evals). It may set topic, markets, schedules, skills, roles and lower budgets, and tighten gates. It may not loosen a gate, raise a budget above his global cap, remove a grader or calibration, or add a money tool. The builder's lint rejects these. It installs disabled; the first run is a canary. `[retrieved]` `15` §variants, `12` §(i).

What differs for these templates:

- **The search space and method lists are overridable data.** An L4 variant may narrow the search space (only crypto perps, only exits from the Library), pick the fitness function from his approved list, and set its own trial cap below the global one. It may not add a fitness function; only he adds one in Settings.
- **A board can become a variant.** When an L1 board reaches paper, "keep as template" makes a variant of L1 pre-filled with that board's question answers as recommended defaults (`[retrieved]` `12` §(e) "templates from past boards").
- **Mini-app variants** are app templates. A D7 variant fixes the slot, the data reads and the widget style ("all my watcher apps look like this").

Example: "An overnight loop on my London session scalps, only EURUSD and GBPUSD, using my Library exits."

1. He says it in the hub. The copilot loads the workflow builder.
2. The builder looks up facts first: his Library exits, the data snapshots for both pairs, his past L4 runs and their plateaus.
3. One grill round, numbered, each with a recommended answer:
   1. Base: L4 overnight loop? (recommended: yes)
   2. Search space: entries from the London pullback board, exits only from Library items tagged `exit`, timeframes 1-15 minutes? (yes)
   3. Fitness: validated expectancy in R after costs (from his approved list)? (yes)
   4. Budget: 150 trials a night, below the global 200? (yes)
   5. Schedule: Sunday to Thursday at 23:00, Lab-scoped allow rule? (yes)
4. The builder writes the variant folder, runs a fake-model dry run on fixtures, and shows the result card.
5. It installs disabled. He enables it. The first night is a canary: it runs once and waits for his thumbs up.

Other examples: "D3 improve loop with exits only from the Library", "D5 indicator author that always adds a Pine export", "P3 decay report that uses my CUSUM settings", "D7 app template for watcher apps in the Home slot", "D10 code health that runs after every QMB upgrade only".

---

## Shared building blocks

### Reused from `15` (same names, same rules)

`research-harness`, `paper-read`, `calibrate` (R7), `audit-other-family`, `library-write`, `render-and-grade`, `lab-run`, `overfit-gates`; pre-checks `feed_diff`, `new_rows`, `data_available`, `library_dup`, `preflight`; the default failure policy, default budget guard, memory scopes and notifications. Every template here ends with `render-and-grade`.

### New sub-workflows

| Block | Steps | Used by |
|---|---|---|
| `spec-compile` (D2) | resolve version → snapshot → costs → splits with sealed holdout → checks → register → smoke run → memo key | L1, L4, D3, D4, D6, template B |
| `grill-to-card` | pre-check facts → draft card with ≤5 numbered questions, recommended answers written in → grader on fields → one human look | L1, D5, D6, D7, D9, the builder |
| `arena-readings` | when open answers change the logic: 2-3 structurally different builds side by side; pick, never average | L1, D7 prototypes, D4 |
| `test-first-build` | scaffold → tests written first (transcript order checked) → code → no-future test → lint, types, speed → Graph/Code round-trip | D1, D5, D7, D8, D10 |
| `no-future-test` | compute on data truncated at t vs full data; values at t must match | D1, D5, D10, L3 |
| `family-ledger` | record every trial (passed or not) with spec hash, parent, change label; serve the trial count and deflated Sharpe | L4, D3, D4, D6, template B |
| `holdout-touch` | one-time unlock of the family's sealed window, logged with who and why; a second touch makes a new counted trial and needs a new window | L4, D3, D6, template B |
| `plateau-detect` | best validated score over the last K trials or revolutions; returns plateau yes or no | L4, D3 |
| `scope-run` (L2) | resolve scope → freshness walk by memo key → run in scope → diff | Board, L1, L3 |
| `app-check` | `qmx app check` lines 1-12, including the render check with four prop states and screenshots | D7, D8, D9 |
| `tighten-card` | build a proposal card whose options can only tighten (bench, paper, shrink) | P3, P4 |
| `book-sim` | load out-of-sample/paper streams → align → combine by method list → stress → marginal value | P1, P4 |

### New pre-checks (zero tokens)

| Pre-check | Wakes when |
|---|---|
| `headroom` | The usage governor allows background model work |
| `fresh_upstream` | Upstream memo keys are stale (for L2) |
| `evidence_complete` | The evidence a card type needs exists (P4, L3) |
| `schema_compat` | Producer and consumer schemas match (D9) |
| `lab_changed` | Anything in the Lab, QMB, data or dependencies changed (D10) |
| `book_status` | P3 classification has amber or red rows |

### New skills (under `agents/_shared/skills/`)

| Skill | Source | Purpose |
|---|---|---|
| `spec-card` | new | Fields of a strategy spec card and the question battery that fills it |
| `search-space` | new, BuildAlpha pattern (`[retrieved]` `06`) | Search-space file format and the fixed list of moves |
| `structural-children` | `08` §1a | The child types (trend-filtered, volatility-adaptive, session-filtered, exit-replaced) and why a parameter nudge is not a child |
| `weakness-buckets` | `08` stage 11 | Diagnosis buckets with the evidence each needs |
| `component-test-battery` | new | Worked-example tests, edge cases, the no-future test |
| `ml-leakage` | ml4t `data-leakage`, `purging-embargo` (`[retrieved]` `02`) | Splits, shuffle test, sealed test rules |
| `build-mini-app`, `debug-app` | today empty (`[retrieved]` `05` §1) | Filled from D7 and D8 lessons |
| `book-reading` | new | How to read a correlation map and marginal value without fooling himself |
| `hillclimb-honest` | pstack `hillclimb` + ml4t gates (`[retrieved]` `02` §7) | One change, one measurement, keep or revert, with trial counting |

### Model roles added to `15`'s table

| Role | Kind of work | Cost class |
|---|---|---|
| `generator` | Propose candidates or children inside a given space | mid |
| `diagnoser` | Read reports, sort weaknesses, write hypotheses | strong |
| `explainer` | Short plain-words explanation of a script result | cheap |

`builder`, `validator`, `grill`, `planner`, `writer`, `analyst`, `doctor` and `judge` are as in `15`. `validator` is on another family where one exists; if none exists, it uses a fresh context with a hostile brief and the chip says "same family" (`15` Q2).

---

## What the Lab backend must provide

`05` §2 and `10` §1 show that none of this exists today except QMB as a library and `run_backtest(config_ref)` with pre-registered configs. The Lab copilot's UI tool names (`qmb.*`, `lab.*`, `graph.edit_draft`, `compute.place`) are fiction until these exist (`[retrieved]` `10` §6.7). The list below is what the templates above call. Names are proposals.

### Board and drafts
1. `board.create / get / add_section / move / note` — the Experimentation Board as a backend object (`12` §(e) overrides the docs' client-only rule).
2. `board.iterations` — read and write the iteration counter and the reason for each extra round.
3. `draft.create / edit / branch / publish / versions` — drafts are editable; publish makes an immutable, content-hashed version. Branches for variants.
4. `run_scope(target, scope = node | section | all)` with a freshness walk by memo key, and a diff against the last run of the same scope.

### Code, graph and notebook
5. `lab.code.read / write` and `lab.graph.get / patch` on the same subject, with a round-trip check (Graph ↔ Code).
6. `lab.kernel.exec / snapshot / restore` — a sandboxed Python kernel (Jupyter-like) per board, with no network except the data store and no live or Portfolio paths. The same kernel pattern serves `rlm` later (`13` §2).
7. `lab.notebook.import / run` — notebooks as a source that compiles to steps.
8. `lab.test.run`, `lab.lint` (including the lookahead lint and the Pine repaint flags), `lab.no_future_test`, `lab.speed_check`.

### Backtest and validation (QMB doors for agents)
9. `qmb.spec.compile / validate / register` — replaces "pre-registered only". The host validator still decides; agents never write the registry directly.
10. `qmb.backtest`, `qmb.sweep`, `qmb.walk_forward`, `qmb.robustness` (Monte Carlo, cost stress, regime and session breakdown) taking a spec, not a stored config.
11. `qmb.holdout.create / touch` — sealed windows per family; `touch` is logged and counted.
12. `qmb.family.ledger / trial_count / deflated_sharpe` — the family ledger as a service.
13. `qmb.memo.get` and `qmb.rerun_check` (reproducibility by result hash).

### Data, compute and models
14. `data.available / snapshot / pit_check / coverage`.
15. `compute.list / estimate / place / move_with_checkpoint` — where a node runs, its cost, and moving a run with its checkpoint.
16. `ml.dataset / split (purge, embargo, sealed test) / train / evaluate / register_model / slots` — a model object with slots.

### Library and lineage
17. `library.search / get / dead_ends / write` (one writer), with classes `component`, `indicator`, `method`, `workflow template`, `model`, and `negative_result` rows.
18. `lineage.edge(source, target, relation)` using the CT-07 typed relations, not free text (`05` §4), plus "proved by" links from items to runs.
19. `search_space.get / propose_move` — moves only from the fixed list; no write to fitness functions or thresholds.

### Gates and settings
20. `gates.read` — thresholds from Settings, read-only to agents; every verdict recorded with the graph's content hash.
21. `settings.write` stays human-only. The engine lint rejects any workflow step that calls it.

### Mini apps
22. `apps.check(app_id)` (the 12 lines), `apps.render_check(widget, props_states)` with screenshots, `apps.disable`, `apps.deprecate(replaced_by)`, `apps.archive(reason)`, `apps.consumers(app_id)` for blast radius.
23. `pipelines.validate_schemas / contract_test / enable` and the host event bus (`emits`, `accepts`), with webhook routes signed by `qmx/*` secrets.

### Portfolio (read-only plus proposals)
24. `portfolio.streams` (out-of-sample, paper, live, in R and USD), `portfolio.book`, `portfolio.limits` — all reads.
25. `portfolio.sim(method, rebalance, candidates)` — read-only simulation.
26. `portfolio.propose(card)` — writes a card that waits for his signature; no other Portfolio write exists for agents.

### Events
27. Run and node events for Lab runs (`lab.run.completed`, `lab.gate.verdict`, `lab.plateau`, `app.health.changed`, `pipeline.artifact`) on the durable SSE topics, so boards and the hub update live.

---

## Open questions (with recommended answers)

| # | Question | Recommended answer |
|---|---|---|
| 1 | What counts as an iteration on the board? | A round trip where he looks at something and says "not that". Grill answers given with "yes" in the same message as the card do not count separately. The target is two: card and first result. |
| 2 | Should L1 build several readings by default, or ask another question? | Build 2-3 readings only when an open answer changes the logic; otherwise build one. Picking is cheaper for him than answering. |
| 3 | Who may touch a holdout, and how often? | Only the end step of L4, D3, D6 or template B, once per family per window. A second touch is a new, counted trial and needs a new sealed window. |
| 4 | L4 numbers? | 200 trials a night, 6 revolutions, 3 search-space restarts, plateau after 30 trials with no gain in the validated score, holdout on the top 3 only. All editable in Settings; variants may only lower them. |
| 5 | May the overnight loop change the fitness function? | No. The fitness function comes from his approved list and is fixed for the run. A new fitness function is his Settings change. |
| 6 | One source of truth for Graph and Code? | Code is the truth. The graph is drawn from declared steps, and graph edits are patches to the code. A round-trip check runs on every publish. |
| 7 | Is "promote to Library" an ask? | No, under the Lab rule. It notifies him. Publishing outside the Lab (mini app, Portfolio, a schedule outside the Lab) asks. |
| 8 | Variant identity (variant vs new strategy vs profile version)? | Keep it as a table the engine reads, with the D4 label set as the default mapping. The risk session decides the final rule (`09` §3.5). |
| 9 | P1 combining methods before the risk session? | Ship the neutral list (equal weight, inverse volatility, risk parity, HRP) labelled "study only". The method list is data, so the session can add or replace methods. |
| 10 | Which streams may P1 use? | Out-of-sample, paper and live only. In-sample streams are excluded, because they make every candidate look uncorrelated and good. |
| 11 | Default decay definition for P3? | Amber outside the 90% Monte Carlo band for 10 trades; red when the term sheet's kill rule trips. Pluggable, because the risk session may replace it (`09` §3.12). |
| 12 | Does a mini-app pipeline need his approval? | Yes to enable, because it is a standing schedule outside the Lab. Pipelines that live entirely inside the Lab (feeding a board) follow the Lab rule. |
| 13 | May D10 fix code on its own? | Only on new drafts in `pending/`. Published versions are never edited; a fix ships as a new version. |
| 14 | GPU and rented compute spend in D6 and L4? | Pre-flight estimate always. Ask above his "ask above" number. A per-run dollar cap pauses the run at the cap. |
| 15 | How strict is "tests first"? | Strict for components, indicators and mini apps: the builder's transcript order is checked. For board experiments (L1 drafts), unit tests may come with the code, because drafts never leave the sandbox. |
| 16 | Pilot order? | L1 on one real idea (it measures the iteration target), then D2 and L2 (needed by everything), then D1 on one R2 card, then D3 on one template B result, then L4 for one night with a small trial cap, then D7 on one small app, then P2, P1 and P4 last, after the risk session. |
| 17 | Does the trading node or the unit structure change these templates? | Only P1-P4, and only in their method lists, card types and the noun "unit". Lab and developer templates key on stages and families, not on benches or pods (`09` §3.3). |
