# QMA workflow templates around units

**What this part is.** The QMX workflow templates that find, build, check, test, judge, expand, watch and review units and markets, and the shared pieces they all call. Workflows are content on the engine that already exists (G2 §4); templates can be removed or improved later.

**Verdict: content on the core engine.** The engine is core and built; templates are content. The shared judge and the try ledger they call are core (`judging.md`).

## His words

- "Workflow templates, yeah, build them." (T3:903) "They should be using the logs from the MIS." (T3:903)
- "It's far better to enhance them." (T2:1148)
- "Think of it like levels, okay? With branches." (T1:513) "Most strategies can work." (T1:513)
- "If they fail, we need to be able to know why is it failing." (T1:513)

## 1. What exists today

| Piece | State | Where checked |
| --- | --- | --- |
| Engine node kinds: trigger, script, rule, loop, join, wait, llm, agent, subworkflow, grader (deterministic), monitor, app_op | BUILT | G2 §4 |
| 45 templates: 22 runnable (15 test-run on real models with recorded cost), 23 drafts waiting on `meta.needs` (trading-node 9, qmb-door 7, sandbox 4, app-op 2, risk-session 2, others) | BUILT | G4b Q1 |
| Agent steps get only declared toolsets and no file or shell tool; script steps run Python (`qml`, `qmb` importable) with Library reads and writes through the host | BUILT | G4b Q1 |
| Triggers: cron in an IANA zone, interval, manual, after, webhook, session, Library event (across machines); installed disabled | BUILT | G2 §4 |
| `d3-iterate-against-qmb` already has the shape agent builds, script tests, loop repeats; its test script refuses until QMB's door exists | BUILT as a draft | G4b Q1 |
| `b-build-and-prove` hard-codes a family holdout and a 60/20/20 split | BUILT, conflicts | G2 §4 |
| No template uses an event trigger between stages or names a skill | BUILT (absence) | research 42 via STATE |
| The `library` node kind is marked available with no executor | BUILT bug | G2 §4 |

## 2. Harvest

| Solution | Where | Fits now? |
| --- | --- | --- |
| Build the shared core first, write the rest as validated drafts that name what they wait for | research 43 §3.7 (decision 6); superseded in part by his "build them" (T3:903), ledger W-01, so the first families are built too | Yes, widened |
| The core: one judge subworkflow, the try and holdout ledgers, a verdict-grid kind, the conveyor (event triggers between stages with a loop guard), one lineage writer, the death certificate (a typed cause of death), a forecast ledger with a scoring script, the journal door, the proposal card | research 43 §3.7 | Yes |
| The four proof checks: receipts grader, a window field on every claim, a forecast ledger, a data-quality check before any read | research 29 §4; research 43 §3.7 | Yes |
| 57 candidate templates in 11 families; the funnel already exists as unfinished drafts; one shared judge step every template runs; a fail branch that looks for where a failed unit's rules still hold | funnel7 intent and `workflows-field.md` | Yes |
| Enhance the shipped `b`, `l1`, `d3`, `d4`, `l4`, `rs6` with the Hermes workflows ("Friendly greeting" and the gold mine, close to the old WF1 and WF2) | research 43 §3.7; ledger W-02 | Yes |
| Desk rhythms: prepare, watch, review, re-plan weekly, recalibrate rarely; missing templates: a pre-session read per market, the end-of-session wrap, a daily unit report card, weekly market selection, session-close forecasts | research 30 §2.4, §7 | Yes |
| The old WF3 "pool cleaning" (read journals, score decay, keep, reduce, demote, retire or rehab) | research 08 §2.1 | Yes, as the decay check, informing only |
| The finding loop (hypothesis, constrained build, backtest, feedback) with three cheap gates (originality, complexity, code matches hypothesis) | research 11 (STATE row) | Yes |

## 3. The shapes

### Shape A. Build the shared core and the first families now; the rest as validated drafts (recommended)

His "build them" (T3:903) settles build against write-up (W-01). The core is tested once; templates that still lack a door install as validated drafts naming what they wait for (`meta.needs`), so nothing pretends to run.

### Shape B. Build every candidate template now

- **Why not.** Most of the 57 wait on doors that the first build is creating; building them before their doors exist means building them twice.

### Shape C. Write recipes now, code later

- **Superseded** by W-01.

**Pick: Shape A.**

## 4. The shared core (built first, called by every template)

| Piece | Does | Kind |
| --- | --- | --- |
| `judge` subworkflow | runs the judge's default chain on a result, reads the try ledger and the study spec, lands a verdict | subworkflow over the core judge block |
| Conveyor | starts the next stage when a stage's result lands (Library event triggers), with a loop guard so a child's landing never re-fires its own parent's build | trigger pattern |
| Lineage writer | one writer for source, idea, unit, version and result links (replaces seven copies of `lineage.py`, research 43 "Subtract first" item 3) | script block |
| Death certificate | a typed cause of death from an appendable list, classified by script first, then explained | Library kind plus script |
| Forecast ledger | dated calls written before the session, scored by a script after it; the market is the comparer | Library kind plus scoring script |
| Receipts grader | every number an agent states must match a tool call the engine logged, recomputed where cheap | grader node |
| Data-quality check | before any read: missing minutes counted, an unannounced gap refuses, any gap flags; an empty Dukascopy hour after a bot-wall challenge is a fetch failure | script block |
| Proposal card | collects what waits for his click, with the evidence and the cost | Library kind |
| Unit check step | calls `unit_check`; a grader routes the problems back to the agent step through a loop | script plus grader |

## 5. The first templates

| Template | What it does | Needs |
| --- | --- | --- |
| **Build and prove a unit** (enhances `b`, `l1`, `d3`) | source or idea in; claim card; agent builds the unit document (cheap model, blind: no backtest toolset); unit check loop; QMB backtest; judge; pass to a governed draft and the expansion step; fail to a death certificate | the unit rows, the QMB app |
| **Run on every market** (enhances `d4`) | his "run on every bot across multiple instruments" (T1:442): the sweep grid, every cell a counted try, one judging rule for every market | the QMB app, the judge |
| **Where would its rules hold** (the fail branch) | for a failed unit, look for contexts where its rules hold; every context tried is counted; the best is judged with the try correction | the QMB app, the judge |
| **Overnight lab loop** (enhances `l4`) | revolutions of variants on a plateau, with loop counts as editable numbers, never caps | the QMB app |
| **Unit review** | traded, skipped and missed per unit at each session close and every N closed trades | journals, the journal door |
| **Session-close market review with scored calls** | a dated forecast per market; scored at the next close | MIS logs (data door), forecast ledger |
| **Pre-session shortlist** | 30 minutes before each session open; counted tries; scored after | the board, MIS logs |
| **Weekly market selection** | Sunday evening before Asia opens, scored at Friday's close | MIS logs, forecast ledger |
| **Decay check** | nightly per unit against its baseline card: CUSUM on R, the cone, cost and fill drift, trade-rate drift, readings drift; OK, Watch, Alarm; informs only | journals, baseline cards |
| **Node watcher** | heartbeats, node journals and guard rows over time; proposals and alerts, never presses | the node's provides, journals |
| **Dictionary expansion** | a source in; match report; append requests; entries written; the dictionary checker; governed drafts | the dictionary kind and checker |
| **Librarian** | finds repeated custom code across units and proposes a new block | the catalogue |
| **Daily data review** | gaps, clock flags, fetch failures, written as a daily note | the data-quality check |

## 6. Fixes to shipped templates (surgical)

| Fix | Reason, one line |
| --- | --- |
| `b-build-and-prove`: the family holdout and the 60/20/20 split become study settings, off by default | a holdout is his choice per study (ruling 137) |
| `d3` 3 generations, `l4` 200 trials, `d4` 12 variants become editable numbers on the template card | no default may act as a cap (standing order 9) |
| The gate scripts copied into `b` and `d3` give way to the shared judge | one judge (research 43 "Subtract first" item 3) |
| The builder model tier defaults to cheap, the rewrite step to strong | his cheap-workhorse seed (A-09) |
| Templates reading "the node's MIS state" read the MIS's partitions and events instead of a node read model | his ruling that templates read the MIS's logs |

## 7. Numbers (starting defaults, all editable; from research 43 §5)

| Number | Default |
| --- | --- |
| Unit analysis trigger | every 10 closed trades and every session close |
| Session clocks | Sydney, Tokyo, London and New York closes; crypto every 8 hours (the funding interval itself is per symbol) |
| Pre-session read | 30 minutes before each session open |
| Weekly market selection | Sunday evening before Asia opens, scored at Friday's close |
| Plateau before a strong rewrite | 30 trials without a better validated score |
| Overnight loop | 6 revolutions, 2 without gain, 200 trials; editable, never a cap |
| Dead ends that wake the fail-branch miner | 5 new |
| Refinement rounds before a family stops spawning variants | 15 without a validated gain |

## 8. Connection points

| From | To | What crosses |
| --- | --- | --- |
| Templates | unit rows, QMB app, judge | unit documents; run requests; verdicts |
| Templates | journals, MIS logs | queries with a time window |
| Templates | Library | governed drafts, death certificates, forecasts, proposal cards |
| Conveyor | engine triggers | a landed result starts the next stage |

## 9. Open for the architecture step

1. Whether an event trigger can see his publish click (research 43 §3.7, unchecked engine fact).
2. Whether his Claude hooks reach engine agent steps in practice (G4b says the merge reaches every chat kind; a probe confirms).

## 10. Parked

- Analyst desks by trading style; crossover across families; a sensor scout; rebuild with a newer model; template health (research 43 Appendix B, Could).
- The MQL5 articles mined through a mini app and workflows (W-08), later.
