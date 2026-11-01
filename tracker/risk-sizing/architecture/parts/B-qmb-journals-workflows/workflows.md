# Workflow templates, their shared pieces, and the two engine changes

Part B, sub-area 5. Decisions: spine AD-213 (templates), AD-214 (engine changes). Slices: `BUILD-SLICES.md` B17, B18a, B18b, B18c, B19 to B21 (B18 split by consumer after R1-B-08; the data-quality check is built in B11).

**In plain words.** Between sessions, workflows do the slow analysis a trading desk does: they review each unit (why it traded, skipped or missed), review each market and keep an almanac, shortlist markets before each session, tag units to the markets that fit them, check the MIS against an agent's own reading, review the day's data, and watch the trading nodes. They read the journals and the MIS's published readings, never the MIS model. Scripts decide every pass and fail; agents explain and propose; he clicks. Nothing here touches the fast lane.

His words: "Workflow templates, yeah, build them." (T3:903); "They should be using the logs from the MIS." (T3:903); "We are literally trading 24/7, my days." (T2:325); "Favor determinism over non-determinism. That's the whole point of QML" (T3:903).

Ledger rows that bind: W-01, W-02, W-04 to W-07 (seeds, honoured), W-08, A-02, A-03 (seed), A-04, A-08 (seed), CC-09, CC-10; STATE midday rulings 44, 49, 50, 53.

## 1. The engine is his: what this part rests on, and the two changes

STATE midday ruling 49: every engine change rests on the ideas of the "QMA V2 Workflow System Design 2" session. Those ideas, as built, and how this part uses each:

| The session's idea (as built) | Where | How part B uses it |
| --- | --- | --- |
| Deterministic control flow: no model output is ever a control-flow edge; a model only produces data a `rule` node reads | engine AD-1 | every gate here is a script, `rule` or `grader`; agent and `llm` steps only produce data |
| One n8n-shaped definition format; a workflow is a folder; script-only, mixed and fully agentic runs are all first-class (Hermes `no_agent`) | engine AD-2 | each template is a folder; most slow-lane steps are scripts and spend no tokens |
| Memory as a port: evidence in Library `memory-row` items with tags `dead_end`, `do_not_retry`, `lesson` | engine AD-18 | death certificates write `dead_end` rows; build templates call `check_dead_end` before building |
| Agents do real local work inside their attempt overlay | engine AD-60 | AGW is built (below) |
| Context references pinned in a workflow's inputs (`@run`, `@library`) | engine AD-63 | the `library` node kind is not needed (below) |
| Ask an operation or leave a result; `feeds` wired by a node input | engine AD-64 | `app_op` passes inputs to QMB's jobs (`mini-app-core.md`) |
| One heartbeat per host; events from the Library ref log | engine AD-65; PR 160 | the conveyor and event triggers |

**Change 1: AGW, the skipped agent-step file writes (probe P-PERM, 18 Oct).** What happened (CHECKED, `qma-ship/build/evidence/prb-h/check2-prb-h-perm.log`): in a test chat that **offered** Bash, the CLI ran an undeclared `echo a3-undeclared` and a Bash write inside the overlay without asking, because its own rules pass read-only commands and writes under an `Edit(<overlay>/**)` allow rule before the policy callback sees them ("cli_rules=passed with no ask"); every other case passed, including a write outside the overlay refused and an undeclared MCP tool refused. The fallback fired and AGW was skipped. The root cause is that the probe offered a tool the step never declared; a real step's launch passes only its declared built-ins as `tools` (`qma-harness/src/qma/harness/launch.py:706`). The design:
1. The engine policy gains its AGW form (`qmx_engine/policy.py`): `Write`, `Edit`, `MultiEdit`, `NotebookEdit` allowed only under the attempt overlay; `Bash` and `PowerShell` allowed only when the node declares them (engine AD-60's honest boundary); anything undeclared refused with its reason.
2. Every engine chat whose node does not declare `Bash` or `PowerShell` carries them in `disallowed_tools`, so even a CLI change that offered them could not run them (INFERRED to beat the CLI's auto-allow, rechecked by the rerun below).
3. Only the attempt's declared `outputs.files` commit to `work/` (engine AD-51, built for script steps).
4. The packet reruns P-PERM on the real engine launch path: A3 and A3W must now be impossible (the tool is not offered) or refused.
Proof already run: `scratchpad/l1b/agw_offered_tools.py` runs the harness's own built-in selection and launch filter; a step declaring `Write` and `Edit` is offered exactly those, with no Bash and no PowerShell. Script steps writing files stay as built and intended (ruling 49).

**Change 2: the `library` node kind.** It is marked available with no executor (`qmx_engine/definition/registry.py:94`; no entry in `runner.py:700-720`, G2 §4). It is marked unavailable, the registry's own rule for node types without an executor (`registry.py:108-119`), because pulling a past run's output into a run is what `@run:<id>/<output>` and `@library:<query>` in a workflow's inputs already do (engine AD-63, data round). Validation then refuses a definition that uses it, naming why (WF-08).

**No other engine change.** The `app_op` inputs are the engine half of the mini-app fix, carried by engine AD-64. WF-02 (the forex-shaped `market_open` precheck, `qmx_engine/triggers/preflight.py:14-16`) is handled by content: market-tied templates use the shared calendar-open trigger check below, and the preflight stays as it is for the templates that use it today. The loop guard is content too: event triggers filter by producer and dedupe by intent key (engine AD-64).

## 2. The shared pieces (built once, called by every template)

| Piece | Kind | What it does | Check |
| --- | --- | --- | --- |
| `judge` subworkflow | subworkflow over `qmx_judge` | runs the default chain on a result, reads the try rows and the study spec, lands a verdict | the judge's own tests; one fixture run lands one verdict |
| conveyor | trigger pattern | a landed result (kind, output name, producer) starts the next stage; the trigger excludes its own producer and dedupes by intent key, so a child's landing never re-fires its parent (WF-05) | a template that lands what its own trigger watches fires once |
| lineage writer | script block | one writer of source, idea, unit, version and result links (replaces seven copies of `lineage.py`) | a run's links walk from source to result |
| death certificate | script plus kind | a typed cause of death classified by script first, then explained; writes a `dead_end` memory row | a failed unit lands one certificate and one memory row |
| forecast ledger | script plus kind | writes dated `forecast` items before a session and scores them after it against the recorded market | a forecast is scored by the script, never by its author (WF-11) |
| receipts grader | grader node | every number an agent states must match a tool call the engine logged; recomputed where cheap; fails the step otherwise (AG-12) | a fixture output with an uncited number fails |
| marked sources | prompt block | outside text (a video description, a forum post, a page) enters an agent step inside a marked data block with the instruction that it is data (AG-07) | a fixture source carrying an instruction is quoted, not followed, and the grader catches any number it supplied |
| data-quality check | script block | before any read: missing minutes counted against the instrument's calendar, an empty open hour is a fetch failure (LD-01), stamp-unit and cadence seams read from the card | a fixture month with a hole is flagged |
| proposal card | kind plus script | collects what waits for his click with its evidence and cost | a template's proposal lands as a card, never as a state change |
| unit-check step | script plus grader plus loop | calls Part A's `unit_check`; a grader routes every problem back to the agent step; the same problem set twice stops the loop (AG-11, Part A) | the dummy unit's broken twin loops once and passes |
| calendar-open check | trigger check script | open or shut from the instrument record's calendar; replaces `market_open` in market-tied templates (WF-02) | a crypto template fires on a Saturday; an FX one does not |
| digest | script | the daily digest per unit from `journal_query`, before any model reads it | a fixture day's digest has fixed numbers |

## 3. The first template families

**Build and prove** (enhances shipped drafts; frees them from `needs: qmb-door`):

| Template | Enhances | What it does | Needs after this build |
| --- | --- | --- | --- |
| Build and prove a unit | `b-build-and-prove`, `l1-idea-to-first-result`, `d3-iterate-against-qmb` | source or idea in; claim card; an agent writes the unit document (cheap model; no backtest toolset while building); unit-check loop; QMB `backtest` via `app_op`; `judge`; pass to a governed draft and a proposal card, fail to a death certificate | none (Part A's unit rows, the QMB app) |
| Run on every market | `d4-variant-comparison` | his "run on every bot across multiple instruments" (T1:442): a QMB `sweep` over his admitted markets, every cell a counted try, one judging rule | none |
| Where would its rules hold | new (the fail branch) | for a failed unit, a sweep over contexts (sessions, readings states, markets) where its rules may hold; every context a try; the best judged with the try correction | none |
| Overnight lab loop | `l4-overnight-lab-loop` | revolutions of variants on a plateau; loop counts are editable numbers, never caps | none |
| Dictionary expansion | new | a source in; Part A's match report and authoring door; entries written and checked; governed drafts | Part A's door |
| Librarian | new | finds repeated custom code across units and proposes a new block | Part A's catalogue |

**The slow lane** (STATE midday ruling 44), each reading journals and the MIS's published readings:

| Template | Enhances | Reads | Writes | Trigger | Agent's job | Needs after this build |
| --- | --- | --- | --- | --- | --- | --- |
| Unit review | `t7-trade-journal-review`, `dm-demo-monitor` | `journal_query` (signals with reasons, trades in R), the baseline card, `replay_check` diffs for missed trades | a `note` per unit (traded, skipped, missed, why), proposal cards | each unit market's session close, and every 10 closed trades (event trigger on the records job's landing) | write one plain paragraph from the script's findings | none |
| Decay check | `dc-decay-and-limit-report` | trades in R, the baseline card | OK, Watch, Alarm per unit; tighten-only proposal cards | nightly | explain a flagged unit | none (informs only; the action is the risk session's) |
| Market review and almanac | `db-desk-brief` (end-of-day wrap), `rv-weekly-review` | the market journal (`minute`, `offset`), reading history, the forecast ledger | a session `note` per market, `forecast` items, the almanac page per market and session | each market's session close; 00:00 UTC for 24/7 markets (WF-04) | write the session's notes; make dated calls | none |
| Pre-session shortlist | `db-desk-brief` (pre-session read) | the board (the MIS's landed `provides.board`), reading history, baseline cards and the readings range each unit earned in | a shortlist `note`, a `shortlist` try per market, forecasts scored after the session | 30 minutes before each session open, from each market's calendar | explain the shortlist | none; units trade their admitted markets on their own conditions whatever arrives (MIS-09) |
| Tagging units to markets | new (weekly market selection) | judge verdicts per market (shrunk), reading history against each unit's condition needs | proposal cards to admit or drop a market; a `paper_pick` try per proposal | Sunday evening before Asia opens; scored at Friday's close | explain each proposal | none |
| MIS check | new | reading history beside bars through `data_features`; the agent reads the market its own way | disagreement examples as `note` items linked to the reading rows, for him to improve the MIS (STATE ruling 50) | daily after the last close | read the market and say where it disagrees | none |
| Daily data review | `connections-health` (its check style) plus the downloaders' results | dataset cards (quality, coverage, seams), the records job's `maintenance-result`, `clock_ok = false` rows, market journal gaps, cross-source offsets | a daily data `note`; `offset` rows written by its script | daily, his routine in This PC's zone | one paragraph from the script's counts | none |
| Node watcher | `gw-guard-watchdogs`, `rk8-incident-post-mortem` | heartbeats and node states through AD-46 (`heartbeats`, `apps.ask status`), the node journal (pulled), guard rows | alerts and proposal cards; never presses a node control | every 5 minutes for the gauge (script only), daily for the review | explain an anomaly | Part C's node operations |
| Nightly live-day replay | new | QMB `replay_check` on each live unit's day, from the quotes and bars the node recorded, harvested on its machine and pulled home (bars hourly and ticks daily by default; a day not yet home waits for the next pull and is caught up once) | a diff `note` per unit; a proposal when the match falls under the setting | after each market's session close | none (script only) | none |

Each of these replaces its shipped draft's one read script (for example `dc-decay-and-limit-report/scripts/journal.py`, which today refuses with "waits for the trading node's unit adapter", CHECKED) with `journal_query` and Library reads, and changes `meta.needs` to what it truly waits for. The shipped tests that pin the old draft statuses (`qmx-engine/tests/test_templates.py:613-620`, `test_install_through_host.py:34-38`) are updated in the same PR as the template they free; that is an intended change, named in its slice.

**Why agents are cheap here.** The unit and market reviews, the shortlist and the data review spend tokens only on the paragraph a person would read; every number comes from a script, and the receipts grader checks it. A provider outage makes the slow lane fail and say so (AG-14); nothing in the fast lane waits on it.

## 4. Surgical fixes to shipped templates

| Fix | Reason, one line |
| --- | --- |
| `b-build-and-prove`'s family holdout and 60/20/20 split become study settings, off by default (`scripts/spec.py:1-19`) | a holdout is his choice per study (ruling 137); QB-12 |
| `d3` 3 generations, `l4` 200 trials, `d4` 12 variants become editable numbers on the template card | no default may act as a cap (standing order 9) |
| the gate scripts copied into `b` and `d3` give way to the `judge` subworkflow | one judge |
| the builder model defaults to a cheap role, the rewrite step to a strong one | his cheap-workhorse seed (ledger A-09) |
| templates reading "the node's MIS state" read reading history and the board instead | his ruling that templates read the MIS's logs |
| market-tied templates use the calendar-open check, not `market_open` | WF-02 |

## 5. Edge cases handled here, by id

WF-01 (each draft names its door), WF-02 (calendar-open check), WF-03 (one default zone for his routines; market-tied triggers in the market's zone), WF-04 (session close or a named UTC hour), WF-05 (conveyor filter and intent keys), WF-07 (long work as jobs or script steps; the agent's QMB wait is 240 s), WF-08 (`library` kind unavailable), WF-09 (an update publishes a new version beside his edited copy, `templates/install.py:1-8`), WF-10 (webhook signatures stay backlog: no template here uses a webhook trigger), WF-11 (forecasts scored by script), WF-13 and WF-14 (adoption and catch-up as built; each slow-lane template states catch-up once or skip, default skip for the shortlist and catch-up once for reviews), AG-05, AG-07, AG-12, AG-14. WF-06: a PC-minted run pass parses at a server holding the same pairing key and is refused by an unpaired one (Part C's C9, run by parse); a real two-host run is Part C's server slice; these templates run on This PC by default and reach a server-homed tester only through `apps.job`. WF-12 is the judge's.

## 6. Numbers (starting defaults, all editable)

| Setting | Default | Origin |
| --- | --- | --- |
| unit analysis trigger | every 10 closed trades and every session close | research 43 §5 |
| session clocks | Sydney, Tokyo, London, New York closes from the calendars; 24/7 markets 00:00 UTC | WF-04 |
| pre-session read | 30 minutes before each session open | research 43 §5 |
| weekly market selection | Sunday evening before Asia opens; scored at Friday's close | research 43 §5 |
| node watcher gauge | every 5 minutes | the shipped `gw-guard-watchdogs` cron |
| plateau before a strong rewrite | 30 trials without a better validated score | research 43 §5 |
| overnight loop | 6 revolutions, 2 without gain, 200 trials; editable, never a cap | research 43 §5 |
| dead ends that wake the fail-branch miner | 5 | research 43 §5 |
| replay match warning | under 80% of decisions matched | research 43 §5 |
| catch-up after downtime | reviews catch up once; the shortlist skips | WF-14 |

## 7. What must not break

The engine's shipped tests; the 22 runnable templates' installs and their recorded test runs (`templates/catalog.py` `test_cost` rows); script steps' Python with `qml` and `qmb` importable; the read-only policy for every chat that does not declare a write.

## 8. Growth seams

A template is a folder; an unmet need installs as a validated draft naming what it waits for. A shared piece is a script block or a subworkflow. New analyst families (desks by trading style, a sensor scout, a rebuild with a newer model) are templates on the same pieces, parked until needed.
