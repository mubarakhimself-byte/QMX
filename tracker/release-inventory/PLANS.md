# Plans behind the shipped code

Each plan or design document behind the merged PRs. For each: where it is, what it covers, and which PRs it produced. PR ranges are proved by git (see `MERGED-PRS.md`). What each plan covers was read in the document. Where the code went another way, the row says so.

**Branches.** `plan/agent-system` and `plan/unit-system` are on origin. `plan/risk-core` is **local only**. The local `plan/unit-system` (2026-11-05) is newer than origin's (2026-11-03): it holds the repair plan, which origin lacks. The worktree `D:/QMX-worktrees/unit-plan` has two uncommitted edits (`PROMPT-REPAIR.md`, `repair_check.py`), which were not read.

## 1. Plans that produced the shipped code (newest first)

| # | Plan | Branch | What it covers | PRs it produced |
|---|---|---|---|---|
| 1 | `tracker/risk-sizing/build/repair/REPAIR-PLAN.md` (+ `audit/`, `FIX-LOG.md`, `PROMPT-REPAIR.md`) | `plan/unit-system` (**local only**) | 24 repairs after an audit of the unit build: honest gates, units that refuse what they cannot run, backtests on his own facts and data, a judge that cannot be talked round, node records, alarms and kill that act. | #329-#352 (24) |
| 2 | `tracker/risk-sizing/build/UNIT-PLAN.md` (+ `plan-parts/`, `BRIEF-BUILDER.md`, `PROMPT-ORCHESTRATOR.md`) | `plan/unit-system` | 91 PR sections in 7 phases: the unit document, the QML checker and dictionary (Part A), QMB as a mini app, journals and the judge (Part B), the trading node, the MIS and outside links (Part C). | #235-#328 (94, including 9 stack repairs with no plan section). C-15, C-19, C-20, C-21 never built. |
| 3 | `tracker/risk-sizing/architecture/level-0/ARCHITECTURE-SPINE.md` and `architecture/parts/{A-qml-dictionary-unit, B-qmb-journals-workflows, C-node-mis-external}/` (spines, `CONTRACTS.md`, `BUILD-SLICES.md`, `UI-NEEDS.md`) | `plan/unit-system` | The unit system's design: Level 0 decisions AD-1 to AD-47, then each part's decisions and build slices. The UNIT-PLAN was cut from these. | Design for #235-#352 |
| 4 | `tracker/risk-sizing/architecture/funnel/experience/design-thinking.md`, `problem-solving.md`, `ui-needs.md` | `plan/unit-system` | Journeys J1-J25, personas, the weak spots, and screen needs. See `JOURNEYS.md` section A. | Design input to #235-#328 |
| 5 | `tracker/risk-sizing/build/UI-NOTES-UNITS.md` | `plan/unit-system` | What each screen must show for the unit system, written for the UI session. | No PRs (no UI code was written) |
| 6 | `tracker/risk-sizing/build/RISK-SIZING-PLACEHOLDERS.md` | `plan/unit-system` | Every placeholder the risk session must replace. | Lists placeholders from #235-#328; #272 gives the contract tests |
| 7 | `tracker/qma-v2/SYNC-PLAN.md` | `plan/agent-system` | Saving by class, the connect dialog for storage, compute and deep logs, rclone packs, install and first start, sync before update. | #230-#234 (5) |
| 8 | `tracker/qma-v2/BACKUP-RESTORE-PLAN.md` | `plan/agent-system` | Copies on This PC and a second drive, restore and the drill, restore from the first-start card and Settings. | #225-#229 (5). B6 folded into SY3; B7 dropped. |
| 9 | `tracker/qma-v2/LOOSE-STRINGS-PLAN.md` | `plan/agent-system` | Background bring-in, resumed runs land, run inputs, cTrader out of the box, template install as a job, the host names what did not open. | #218-#224 (7) |
| 10 | `tracker/qma-v2/MOCK-DATA-PLAN.md` | `plan/agent-system` | Templates use the real Library; broker reads say demo or live; the old-data import labels unproven items. | #215-#217 (3) |
| 11 | `tracker/qma-v2/LOCAL-FIRST-PLAN.md`, design `research/methodology/62-local-first-design.md` (+ `62a`, `62b`) | `plan/agent-system` | This PC is home: no server in the defaults, one way to find the QMX folder, its layout, places he names, store versions, bring in old data. | #208-#214 (7), plus WU11 #207 |
| 12 | `tracker/qma-v2/WRAPUP-PLAN.md`, design `research/methodology/60-wrapup-seams.md`, `61-server-substitute-and-wu9b.md` | `plan/agent-system` | List A of the 24 Oct handoff: app tools reach a chat, templates install for real, green CI, provider test, Hub copy counts, cTrader demo sign-in, the server ready to be home. | #198-#207 (9). WU4 open (#204). WU10 never built. |
| 13 | `tracker/qma-v2/DATA-PLAN.md`, design `research/methodology/51`-`58` and `architecture/library-and-data/` | `plan/agent-system` | The data round: the one Library, server sync and flip, price partitions and the price door, backtests land one result, connections, feeds, uploads, branch and merge, OpenObserve, the Lab workspace, steps next to data. | #171-#197 (27). DR2E, DR5B, PRB-CT never built. |
| 14 | `tracker/qma-v2/HARDENING-PLAN.md`, design `research/methodology/39-architecture-rerun.md`, `43-whole-app-unlocked.md`, `47-studies-folded.md`, `40-retriage.md` | `plan/agent-system` | The build program: one host, caps removed, the guard, the catalog and Surface, the Library store, sessions as items, the router and providers, delegate v2, memory on Hindsight, templates, server work, deletions. | #112-#170 (59). AGW and RTR7 never built. |
| 15 | `tracker/qma-v2/architecture/workflow-engine/` (`ARCHITECTURE-SPINE.md`, `SOLUTION-DESIGN.md`, `HARNESS-REQUESTS.md`) and `tracker/qma-v2/archive/2026-10-18-engine-program/ENGINE-PLAN.md` | `plan/agent-system` | The workflow engine: format, ledger, orchestrator, fan-out, workers, failure ladder, triggers, doors, and the template pack. | #91-#111 (21) |
| 16 | `tracker/qma-v2/archive/2026-10-18-harness-program/HARNESS-PLAN.md` | `plan/agent-system` | The agent harness on the Claude Code CLI: host, plan chats, relay for key providers, approvals, usage and overage stop, model switch, delegate, GPT lane, console. | #71-#90 (20, of which #76 and #80 are test fixes with no plan) |
| 17 | `rebuild/DESIGN.md`, `rebuild/packets/P01-P24`, `rebuild/reports/*` | `engine/base` | The QMA v2 rebuild: green baseline, CI, deletions, agent specs and router, memory, guards, domain tools, workflow compiler, control service, mini-app runtime, storage, brokers, Docker, research app, remote runs, and retiring the old runtime (P16). | #26-#70 (45). P24 has no PR. Much of this was later replaced by programs 14-16. |
| 18 | `_bmad-output/planning-artifacts/epics-UI-2026-09-27.md`, Epics 67-73 | `main` | The old factory epics: daemon start, pairing, mailbox, artifacts, editor drafts, pack UI, cancel. | #12-#19 (8, #12 is a CI fix with no plan). The code they built was deleted by #169. |

## 2. Handoffs and maps that describe the shipped state

| Document | Branch | What it covers | Use |
|---|---|---|---|
| `tracker/qma-v2/HANDOFF-2026-10-24.md` | `plan/agent-system` | What the build and data rounds shipped, the leftovers (lists A, B, C), and the session order. | Good for what was open on 24 Oct. List A was closed by the wrap-up (#198-#207). |
| `tracker/qma-v2/UI-HANDOFF.md` | `plan/agent-system` | Everything the UI session needed, 26 sections, last brought current 2026-10-28 (to #228). | Read for the October backend. It predates the unit build and the repair. |
| `tracker/qma-v2/UI-NOTES.md` | `plan/agent-system` | Older harness event details. | Supplement to UI-HANDOFF. |
| `tracker/qma-v2/LAUNCH-AND-CLEANUP-MAP.md` | `plan/agent-system` | Branch tips and cleanup as of 21 Oct. | History. |
| `tracker/qma-v2/research/methodology/26-operator-rulings-and-alignment.md` | `plan/agent-system` | His rulings 1-119 (newer rulings live in memory and STATE files). | Binding rulings for the October programs. |
| `tracker/risk-sizing/STATE.md` | `plan/unit-system` | The unit-system session's state and rulings. | Binding rulings for the unit build. |

## 3. Plans that produced nothing shipped

| Plan | Branch | What it covers | Status |
|---|---|---|---|
| `tracker/risk-core/round-2/build/PLAN.md` (+ `round-2/arch/final/`, `WALKTHROUGH.html`, `UI-LOOK.md`) | `plan/risk-core` (**local only**) | Round two of risk and sizing: logic and risk halves of a unit, sizers that answer in money, brakes, exits, the decision row before every send. | Open PRs #353-#369. Not shipped. Proved by gh. |
| `tracker/risk-core/architecture/SPINE.md` and the funnel, expansion and ledger folders | `plan/risk-core` (**local only**) | The first risk template. | **Rejected** by him on 7 Nov (`REVIEW-2026-11-07.md`). |
| `tracker/qma-v2/architecture/lab-and-pods/` | `plan/agent-system` | The Lab and pods. | The Lab workspace shipped (#194). Pods never built. |
| `tracker/qma-v2/DELETION-PLAN.md`, `PROMPT-DELETION.md` | `plan/agent-system` | Old-code deletion D1-D4. | Superseded by the DEL PRs in the build program (#164-#172). |
| `tracker/agent-system/` (tickets, research 00-32) | `plan/agent-system` | The 12-13 Oct agent-system study. | Input to the harness; no PRs of its own. |

## 4. Older plans that still describe shipped behaviour

These come from August and September. Most of their architecture was replaced, but the parts below still ship in code.

| Plan | Branch | Still true for | Watch out |
|---|---|---|---|
| `_bmad-output/planning-artifacts/architecture/architecture-QMB-2026-08-20/` | `main` | The QMB backtester core in `qmb/src/qmb/` (data, execution, optimize, robustness, results, sweep). | The host and doors changed (QMB is now a mini app, #261). |
| `_bmad-output/planning-artifacts/architecture/architecture-QML-2026-08-21/` | `main` | QML's runtime seam and conformance checks in `qml/src/qml/`. | The unit document, dictionary and checker layers are newer (Part A). |
| `_bmad-output/planning-artifacts/architecture/architecture-NODE-2026-08-28/` | `main` | The old node runtime `qmn/src/qmn/`, which the trading-node app still serves. | Book/BMS paths are old; C-20 meant to cut about 47,000 lines and never did. |
| `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-08-19/` (foundation spine) and `prds/prd-QMX-2026-08-21/` | `main` | The QMF packages in `packages/qmf-*` (core, data, registry, indicators, structure, risk, venue, readings) and the calendar extensions. | Daemon, wire and pack parts are deleted. |
| `docs/` knowledge base (constitution, components, contracts, decisions, scenarios, glossary, registry) | `main`, last changed 2026-09-27 | Money, time and instrument contracts in `qmf-core`; the sealed holdout and synthetic-data labels as ideas. | It describes the September architecture. `docs/` has no page for the new host (HANDOFF-2026-10-24). |
| `qa/epics/epic_03`-`epic_23/PLAN.md` and `_bmad-output/test-artifacts/test-design-*.md` | `engine/base`, `main` | QA test designs for QMF and QMB. | Tests, not product plans. |

## Counts

- Plans that produced shipped PRs: 18 (section 1), covering 321 of the 334 merged PRs. The other 13 have no plan (CI and test fixes, the branch merge #155, and the nine `us-fix-*` stack repairs).
- Handoffs and maps: 6. Plans with nothing shipped: 5. Older plans still partly true: 6.
