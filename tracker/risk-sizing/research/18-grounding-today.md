# 18: Grounding, what exists today

Written 2026-10-30 by grounding agent B. Read and record only. Nothing here is a design or a recommendation, and nothing was changed in any repo.

It rechecks `01-ground-truth.md` (24 Oct, engine/base `f05fc64b`) against the trunk as it stands today.

## How to read this

**Labels.**
- **CHECKED**: read at the cited path and line on 2026-10-30, or seen in the output of the cited command.
- **INFERRED**: my reading of what the checked facts mean. Not seen directly.

**Status tags.** BUILT = code exists and runs in tests or on a host. PARTIAL = some of it is code, the rest refuses or is missing. DESIGNED-ONLY = in docs or the planning tree, no code. MISSING = in neither.

**Short paths.**

| Alias | Path |
|---|---|
| `EB` | `origin/engine/base` at `d82be318` (merge of PR 206, 26 Oct), read with `git show` in `C:/Users/Mubarak/Desktop/QMX` after `git fetch` on 2026-10-30. This is the code truth. |
| `ENG` | `EB:qmx-agents/packages/qmx-engine/src/qmx_engine` |
| `TPL` | `ENG/templates` |
| `CTL` | `EB:qmx-agents/packages/qmx-control/src/qmx_control` |
| `HAR` | `EB:qmx-agents/packages/qma-harness/src/qma/harness` |
| `LIB` | `EB:qmx-agents/packages/qmx-library/src/qmx_library` |
| `HOST` | `EB:qmx-agents/packages/qmx-host/src/qmx_host` |
| `TOOLS` | `EB:qmx-agents/packages/qmx-tools/src/qmx_tools` |
| `DOCS` | `C:/Users/Mubarak/Desktop/QMX/docs/` (working tree of `main`, `c3e8ec5e`; last docs commit 27 Sep) |
| `DW` | `C:/Users/Mubarak/Desktop/QMX/_docwork/` |
| `T` | `D:/QMX-worktrees/unit-plan/tracker/qma-v2/` |
| `RS` | `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` |

**Trunk movement since 01.** `git log f05fc64b..origin/engine/base` shows PRs 198, 199, 200, 201, 202, 203, 205 and 206 merged (WU1, WU2, WU3, WU5, WU6, WU7, WU8, WU9). PR 204 (WU4) is still open. `git diff --stat f05fc64b origin/engine/base -- qmb qml qmn packages` shows one changed file (`qmb/tests/test_qmb_examples.py`, 2 lines). So QMB, QML, QMN and every QMF package are unchanged since 01. CHECKED.

**Open PRs.** 29 open (`gh pr list --repo MubarakHimself/QMX --state open`). They form one stack off `EB`: LF5 (208) → LF1 (209) → LF2 (210) → LF6 (212) → LF3 (213) → LF4 (214) → MD1 (216) / MD2 (215) → MD3 (217) → LS1 (219) / LS2a (218) → LS2b (220) → LS5 (223) / LS6 (222) → LS4 (224) → BR1-BR5 (225-229) → SY1-SY5 (230-234), plus WU11 (207) → LF7 (211), and WU4 (204) on the merged `build/wu2`. CHECKED (`gh pr list --json headRefName,baseRefName`).

---

## 1. How QMX workflows work

### 1.1 The engine and the workflow format

| Thing | Status | Evidence | Note |
|---|---|---|---|
| One host process runs chats, the engine, control doors and the webhook door on one port | BUILT | `HOST/host.py:1-25` | It is the one writer of `<home>/library/`. CHECKED |
| Workflow document `qmx.workflow/1` (nodes, connections, inputs, outputs, settings, `extends` with JSON patches, `meta.needs`) | BUILT | `ENG/definition/model.py:215-228`, `:187-190`, `:207-212` | Version, hash and lifecycle are Library facts, not fields (`model.py:1-7`). CHECKED |
| Node kinds that run: trigger, script, rule, loop, join, wait, llm, agent, subworkflow, grader (deterministic only), monitor, app_op, library | BUILT | `ENG/definition/registry.py:56-94` | `available=True` on each. CHECKED |
| Node kinds declared but not runnable: `human_gate`, `rlm`, `claude_workflow`, grader `llm` mode | DESIGNED-ONLY | `registry.py:62`, `:81`, `:84-91`, `:95` | `available` is False. CHECKED |
| Catalog rows become node types `<pack>.<toolset>_<op>` (unavailable until each executor exists) | PARTIAL | `registry.py` `with_operations`, `REGISTRY` last line | CHECKED |
| Per-node `runs_on` (default `"pc"`), `toolsets`, `skills`, `credentials`, `outputs.files` | BUILT | `model.py:141`, `:145`, `:149`, `:129-160` | CHECKED |
| `settings.error_workflow` field | PARTIAL | `model.py` `Settings`; `git grep error_workflow` finds no reader outside `definition/` | INFERRED: declared, not wired |
| Script node: `python -I` subprocess, JSON on stdin and stdout, `[QMX_FAILURE]` line, allow-listed env with `qmx/tool/<name>` keys, no run timeout (idle detector instead) | BUILT | `ENG/nodes/script.py:1-17` | "so a long backtest runs on". CHECKED |
| Agent node: one harness Background chat per chunk, Surface built from declared toolsets and skills, read-only policy denies undeclared tools, no turn or time ceiling, stuck detector | BUILT | `ENG/nodes/agent.py:1-24` | CHECKED |
| Loop, subworkflow (own run id, `caller_policy`, max depth), monitor (hash diff fires `changed`), grader (pass/fail script) | BUILT | `nodes/loop.py:1-3`; `nodes/subworkflow.py:1-13`; `nodes/monitor.py:1-7`; `nodes/grader.py:1-4` | CHECKED |
| app_op node: runs a mini app's operation in its supervised process, placement by declared `state`, waits when the app's home is unreachable | BUILT | `ENG/nodes/app_op.py:1-22` | No `qmb` app or `backtest` job exists on `EB`. PR 204 adds `{app: qmb, job: backtest}` (`T/QMB-BACKTEST-DOOR-HANDOFF.md:12`). CHECKED |
| Run zones: read-only hashed `code/`, shared `work/`, per-attempt overlay, staged idempotent commits | BUILT | `ENG/workers/zones.py:1-20` | CHECKED |
| Ledger (`engine.sqlite`, one writer), replay, memo, redaction, spans | BUILT | `ENG/ledger/` file list; `triggers/rows.py:1` | CHECKED |
| Engine REST and catalog rows: `workflows_get/put/validate/run`, drafts, `tests_run`, versions, `runs_list/get/explain/cancel/resume`, triggers list/create/enable/disable/run_now, inbox | BUILT | `CTL/service.py:1524-1730` | CHECKED |
| A live run takes inputs from REST and from its trigger | PARTIAL | PR 220 (LS2b, open) body | On `EB` a run has no inputs body. CHECKED (PR body) |

### 1.2 Triggers and schedules

| Thing | Status | Evidence | Note |
|---|---|---|---|
| Trigger kinds: cron (IANA zone), interval, manual, after, webhook, event, session | BUILT | `ENG/triggers/rows.py:1-17` | A trigger pins one published object and names one `home_engine`. CHECKED |
| Cron through `cronsim` 2.7 with DST rules | BUILT | `triggers/cron.py:1-7` | CHECKED |
| Event trigger on Library landings (filter by kind, output, producer; cursor per trigger; `each` or `latest`) | BUILT | `triggers/event.py:1-25` | This is how a workflow can fire when a result lands. CHECKED |
| One catch-up run after downtime, earlier occurrences recorded skipped | BUILT | `triggers/catchup.py:1-8` | CHECKED |
| `session` trigger for copilot loops | PARTIAL | `triggers/rows.py:6-7` ("waits for copilot loops") | CHECKED |
| Chats lose the CLI's own schedule and loop tools; every schedule is an engine trigger | BUILT | `HAR/surface.py:12-15` | CHECKED |
| Template triggers install disabled; enabling is his click | BUILT | `TPL/install.py:1-8` | CHECKED |

### 1.3 Where workflows run

| Thing | Status | Evidence | Note |
|---|---|---|---|
| Default placement is the PC, in process | BUILT | `model.py:141`; `ENG/workers/local.py:1-22` | Scripts sit in a Windows Job object and die with the engine. CHECKED |
| Remote placement: attempt shipped as a bundle with a run pass, run by `qmx-run-sidecar`, heartbeats and results through the Hub | BUILT | `ENG/workers/remote.py:1-22` | Routes by `runs_on` and data locality (AD-70). CHECKED |
| Compute providers: SSH, Amp, Modal, E2B | BUILT | `EB:qmx-agents/packages/qmx-remote/src/qmx_remote/providers.py:61`, `:186`, `:199`, `:280` | CHECKED. Never run against his accounts: INFERRED from `T/HANDOFF-2026-10-24.md:18` ("Nothing has run on your real QMX home yet") |
| Workflow server ("node" in `qmx node setup`, the Contabo box): bootstrap, recovery script, firewall, `server` role, store root `/srv/qmx/library`, drain before update | BUILT | `CTL/node.py:1-30` (WU9, merged) | This "node" is a workflow worker, not the trading node QMN. CHECKED |
| Server as primary store and final-look door | BUILT on `EB`, reversed by ruling | `HOST/market_data.py:104-110`, `:192-194`; ruling 136 (`T/research/methodology/26-operator-rulings-and-alignment.md:265`) | PR 207 moves the final look to `[library] primary`, pc unless set. PR 208 removes the server from defaults. Both open. CHECKED |
| Connect a server, Modal, E2B from one dialog | PARTIAL | PR 232 (SY4, open) title | CHECKED (title only) |

### 1.4 How a workflow reaches tools, QMB, the Library and data

| Thing | Status | Evidence | Note |
|---|---|---|---|
| Core toolsets: library, workflows, data, backtest, research, node, broker_read, apps_admin, memory, context, delegate, settings_read, ops, router, lab | BUILT | `CTL/catalog.py:48-63` | An agent node names the ones it gets. CHECKED |
| Dynamic toolsets `app:<id>`, `mcp:<name>`, `run:<id>` | BUILT | `HAR/surface.py:442-450` | CHECKED |
| Data rows: `data.instruments`, `data.bars`, `data.features`, `data.calendar` through the market-data door | BUILT | `CTL/catalog.py:237-241`; `TOOLS/service.py:242-262` | Reads use `purpose="exploration"`. On `EB` the door refuses to open without `[data] seal_boundary_ns` (`HOST/market_data.py:215-224`). CHECKED |
| Backtest rows: `backtest.run`, `.status`, `.results`, `.compare` | PARTIAL | `CTL/catalog.py:242-276`; `TOOLS/service.py:280-299` | `run` refuses "This host binds no qmb_backtest door". `status` and `results` read old-shape objects. `compare` reads two CT-32 artifacts. CHECKED |
| `research.qml_run` | PARTIAL | `TOOLS/functions.py:191` | Refuses "Unknown bot_ref; ask the host to register a QML HostedBot". CHECKED |
| `node.state`, `node.propose_order` | PARTIAL | `CTL/catalog.py:277`, `:232` | No trading node is configured. A proposal always asks. CHECKED |
| Broker reads: accounts, account_state, positions, quotes, symbol_info, bars | BUILT | `CTL/catalog.py:225-233` | PR 215 (MD2, open) stamps every read demo or live. CHECKED |
| Library rows: save, search, get, versions, link, links, branch, merge, conflicts, resolve, history, blame, mark, move, publish_card, eval_tasks, server_lost | BUILT | `CTL/service.py:867-1138`; `CTL/catalog.py:330`, `:557-570` | CHECKED |
| Lab rows (levels, new, open, workspace, panel, training, model) | BUILT for screens, closed to agents | `CTL/catalog.py:586-674` | All seven are `agent=False`; "pods are not among them". CHECKED |
| QMB templates call QMB through agent nodes with `[library, backtest, data]` toolsets | PARTIAL | `TPL/l1-idea-to-first-result/definition.json`, `TPL/d4-variant-comparison/definition.json` (node list printed by a scratch parser) | They wait on `qmb-door`. CHECKED |
| QMB scripts in templates | DESIGNED-ONLY | `TPL/b-build-and-prove/scripts/qmb.py:1-15` | Prints "waits for QMB's spec, backtest and robustness doors for agents" and exits 1. CHECKED |
| How a run stores results: a `workflow-run` item; writes only on `refs/runs/<run_id>` as `run:<run_id>`; drafts on `refs/drafts/`; `main` holds published versions; nothing deleted | BUILT | `ENG/ports/library.py:1-15` | CHECKED |
| Script nodes read and write the real Library | PARTIAL | PR 216 (MD1, open) body | MD1 says ten template scripts "opened a hidden fake Library" on `EB` (digest, clippings, crystallise, revolution brief, seven lineage scripts). CHECKED (PR body); not re-run |
| Template install into the real Library through the host | BUILT | commit `ec3d1694` (WU5) in `git log EB`; `TPL/install.py:1-8` | 01 listed this as broken. CHECKED |
| Templates that read prices | PARTIAL | `git grep -l 'read_bars\|market_data\|materialise' EB -- TPL` | Only the three downloaders (which write) and `d6-ml-training-run` (needs `qmb-door`, `sandbox`). No runnable template analyses prices today. CHECKED; the "no runnable" reading is INFERRED |

### 1.5 Every shipped template (46)

Source: `TPL/catalog.py`, parsed by a scratch script (`CATALOG` rows). A row with `needs` installs as a validated draft whose test run and enable are refused with the need named (`model.py:193-205`). A row without installs, is test-run on real models and published disabled (`install.py:1-8`). Whether each test run passed on real models was not checked.

| catalog.py line | id | folder | needs | cron triggers (installed disabled) | Status |
|---|---|---|---|---|---|
| 69 | paper-scout-to-research-note | rs1-paper-scout | none | `0 */6 * * *` UTC | BUILT |
| 79 | news-and-macro-calendar-watch | t3-news-calendar-watch | none | `5 0 * * *` UTC | BUILT |
| 89 | rough-idea-to-test-plan | rs0-idea-grill | none | none | BUILT |
| 98 | source-to-component-card | rs2-source-to-component-card | none | none | BUILT |
| 107 | literature-review-on-a-topic | rs4-literature-review | none | none | BUILT |
| 116 | video-to-strategy-ideas | a-fill-the-library | none | none | BUILT |
| 125 | weekly-review | rv-weekly-review | none | `0 6 * * 1` UTC | BUILT |
| 135 | morning-market-brief | db-desk-brief | none | 06:00 London, 07:30 and 17:05 New York, weekdays | BUILT (calendar and other runs only; node facts and MIS grid left out, `db-desk-brief/README.md` "Left out") |
| 149 | research-desk-overnight | t4-research-desk-overnight | none | `0 3 * * 0-4` London | BUILT |
| 159 | copilot-eval-battery | ev-copilot-eval-battery | none | none | BUILT |
| 168 | demo-trades-fill-quality | dm-demo-monitor | trading-node | none | PARTIAL (draft) |
| 176 | trade-journal-in-risk-units | t7-trade-journal-review | trading-node | none | PARTIAL (draft) |
| 184 | trading-guards-alive | gw-guard-watchdogs | trading-node | none | PARTIAL (draft) |
| 192 | correlation-and-exposure-drift | rk2-correlation-drift | trading-node | none | PARTIAL (draft) |
| 200 | decay-and-limit-report | dc-decay-and-limit-report | trading-node | none | PARTIAL (draft) |
| 208 | stress-tests | rk5-stress-tests | trading-node | none | PARTIAL (draft) |
| 211 | incident-post-mortem | rk8-incident-post-mortem | trading-node | none | PARTIAL (draft) |
| 219 | portfolio-combination-study | p1-portfolio-combination | trading-node, risk-session | none | PARTIAL (draft) |
| 227 | daily-book-report | p2-daily-book-report | broker-read-token | none | PARTIAL (draft) |
| 235 | change-bundle-for-approval | pp-proposal-pack | trading-node, risk-session | none | PARTIAL (draft) |
| 243 | strategy-idea-to-paper-tested | b-build-and-prove | qmb-door | none | PARTIAL (draft) |
| 251 | source-to-a-lab-test | rs3-source-to-lab-test | qmb-door | none | PARTIAL (draft) |
| 259 | hypotheses-from-dead-ends | rs6-hypotheses-from-dead-ends | real-library | `0 5 * * 1` UTC | PARTIAL (draft) |
| 268 | question-over-a-large-table | rs8-big-data-question | rlm | none | PARTIAL (draft) |
| 276 | first-backtest-from-an-idea | l1-idea-to-first-result | qmb-door | none | PARTIAL (draft) |
| 284 | overnight-lab-loop | l4-overnight-lab-loop | qmb-door | `0 23 * * *` London | PARTIAL (draft) |
| 293 | build-a-component-or-indicator | bc-build-a-component | sandbox | none | PARTIAL (draft) |
| 301 | iterate-against-qmb-with-overfit-guards | d3-iterate-against-qmb | qmb-door | none | PARTIAL (draft) |
| 309 | variant-generation-and-comparison | d4-variant-comparison | qmb-door | none | PARTIAL (draft) |
| 317 | ml-training-run-with-a-holdout | d6-ml-training-run | qmb-door, sandbox | none | PARTIAL (draft) |
| 325 | mini-app-lifecycle | ma-mini-app-lifecycle | sandbox, app-op | none | PARTIAL (draft) |
| 333 | connect-mini-apps | d9-mini-app-pipeline | app-op | none | PARTIAL (draft) |
| 341 | revolution-loop | revolution-loop | none | none | BUILT |
| 350 | ask-the-panel | ask-the-panel | none | none | BUILT |
| 359 | clippings-into-research | clippings-into-research | none | none | BUILT |
| 368 | morning-digest | morning-digest | none | `0 7 * * *` London | BUILT |
| 378 | crystallise-a-workflow | crystallise-a-workflow | none | none | BUILT |
| 387 | run-one-job-on-his-server | run-on-a-machine | sandbox | none | PARTIAL (draft) |
| 396 | backup-weekly | backup-weekly | none | `0 6 * * 1` UTC | BUILT |
| 405 | synthetic-data | synthetic-data | none | none | BUILT (moving-block bootstrap from a month of prices) |
| 425 | connections-health | connections-health | none | `*/5 * * * *` UTC | BUILT |
| 434 | feed | feed | none | none | BUILT |
| 450 | download-dukascopy | download-dukascopy | none | `0 2 * * *` UTC | BUILT |
| 459 | download-binance | download-binance | none | `30 2 * * *` UTC | BUILT |
| 468 | download-ccxt | download-ccxt | none | `0 3 * * *` UTC | BUILT |
| 477 | extract-source | extract-source | none | none | BUILT |

Counts: 46 rows, 23 with needs, 23 without, 13 with cron triggers. CHECKED (scratch parser over `catalog.py`). The catalogue docstring still says "the 31 templates" (`catalog.py:1`). CHECKED.

Shared blocks under `TPL/_shared/`: calibrate, extract-source, overfit-gates (`deflated_sharpe.py`), paper-read, preflight, render-and-grade, research-harness, save-source, understand-extract. CHECKED (`git ls-tree`).

### 1.6 Skills, hooks, agents, copilot, mini apps, harness

| Thing | Status | Evidence | Note |
|---|---|---|---|
| Core plugin skills: build-workflow, build-mini-app, debug-app, inspect-qmx, qmx-overview | BUILT | `EB:qmx-agents/plugin/skills/*/SKILL.md` (5 files) | `build-workflow` turns one line of intent into a tested draft and a publish card; never publishes or enables (`build-workflow/SKILL.md:1-25`). CHECKED |
| Core plugin sub-agents: researcher, data-analyst, app-builder, overnight-builder | BUILT | `EB:qmx-agents/plugin/agents/` | CHECKED |
| Copilot rules file: money is read-only, workflows are built not configured, helpers by role | BUILT | `EB:qmx-agents/plugin/QMX.md:1-30` | CHECKED |
| No skill for markets, units, QMB or QML analysis | MISSING | same listing | CHECKED |
| Pack plugins: a published Library object materialised as `skills/`, `agents/`, `commands/` only; a pack's hooks and `.mcp.json` are never written | BUILT | `HAR/packs.py:1-18` | So a pack cannot ship a hook. CHECKED |
| `library-skills` view of published Library skills | BUILT | `HAR/packs.py:15-18` | CHECKED |
| Hooks: one PreToolUse guard on every call (keys, keyring, QMX stores, destructive commands, his never-allow list); engine hook sink for PostToolUse, PreCompact, Stop | BUILT | `HAR/guard.py:1-12`; `ENG/nodes/agent.py:19-24` | No user-defined workflow hooks. CHECKED (`git grep -i hook` in `ENG/definition` returns nothing) |
| Harness: chat slots from RAM, Interactive, Background and Child chats, reaper, resume | BUILT | `HAR/harness.py:1-16`; `HAR/chat.py:1-20` | CHECKED |
| Surface: one function decides toolsets, tools, sub-agents, skills, system text per chat kind | BUILT | `HAR/surface.py:1-20` | CHECKED |
| Delegate v2: helper chats that return a handle at once; steer, stop, list | BUILT | `HAR/delegate.py:1-20` | CHECKED |
| Router with provider rows, accounts, `llm_complete` | BUILT | `CTL/catalog.py:505-531` region (router rows); WU2/WU3 commits | CHECKED |
| Memory on Hindsight | BUILT | `EB:qmx-agents/packages/qmx-memory/src/qmx_memory/hindsight.py` exists | CHECKED |
| Mini apps as plugins with a supervisor, bundles, volumes, backup | BUILT | `EB:qmx-agents/packages/qmx-apps/src/qmx_apps/` listing | CHECKED |
| App operations reach a chat (`app:<id>` rows) | BUILT | `HAR/tools.py:39`, `:541` (WU1, merged) | 01 listed this as open. CHECKED |
| Example mini apps: exchange-status, macro-daily-bias, mql5-articles, weekend-watcher | BUILT | `EB:examples/apps/` | Two import the deleted runtime (01 §4.3). Not rechecked |

---

## 2. QMB

QMB code is unchanged since 01 (one test file differs). Rows below are rechecked by spot reads.

| Thing | Status | Evidence | Note |
|---|---|---|---|
| Run loop, config compiler, orchestrator with ledger, process per run | BUILT | `EB:qmb/src/qmb/{runloop,config,orchestrator,ledger}/` listings | CHECKED |
| Fill, spread, slippage, commission, swap ports | PARTIAL | `EB:qmb/src/qmb/execution/cost.py:1-8`; `fill.py:1-7` | Every cost model refuses without a per-broker calibration (GAP-0048). Fills stay `optimistic`-tainted. CHECKED |
| Optuna optimisation with splits, sensitivity, resume | BUILT | `EB:qmb/src/qmb/optimize/` listing; `git grep -l optuna` | CHECKED |
| Robustness: trade shuffle, candle perturbation, rule significance, walk-forward, carve-out | BUILT | `EB:qmb/src/qmb/robustness/` listing | CHECKED |
| PBO, CSCV, MC-1000 batteries | DESIGNED-ONLY | `robustness/summary.py:13`, `:71`, `:82-83`; `robustness/contract.py:109` | Named and deferred. CHECKED |
| Sweeps: instruments × timeframes × parameters for one bot, pre-flight run count | BUILT | `sweep/axes.py:1-12` | No window axis. CHECKED |
| Tries and trials: every trial ledgered | PARTIAL | 01 §1.3 | No correction applied in QMB. Deflated Sharpe lives in `TPL/_shared/overfit-gates/scripts/deflated_sharpe.py`. CHECKED |
| What-If filters (projection): a saved view over one result, predicates `days`, `exclude`, `hours`, `include`, `max_trades`, `session` | BUILT | `analysis/project.py:1-14`, `:85-92` | Never a new result, never admission evidence. CHECKED |
| Rerun: any change of size, Book or costs is a new run | BUILT | `analysis/rerun.py` exists; 01 §1.3 | CHECKED |
| Book/BMS variants as complete candidates plus replay | BUILT | `analysis/variants.py:1-14` | CHECKED |
| Portfolio combination of two bots' streams | DESIGNED-ONLY | `analysis/deferred.py:1-6` | Deferred. CHECKED |
| Synthetic series: block-bootstrap, gaussian-resample, gaussian-noise, gbm (forex-CFD) | BUILT | `data/generate.py:1-10` | CHECKED |
| Results format: CT-32 summary and CT-29 stream, exact-integer money, typed refusal for undefined measures, no composite score | BUILT | `results/measures.py:1-8`; `results/ct32.py`, `ct29.py` exist | Results are in money; per-trade R is not a QMB measure (01 §1.3). CHECKED |
| Landing: one `backtest-result` per run with `consumed`, `uses`, `tests` edges | BUILT | `qmb/host/library_landing.py`; `LIB/migrate/from_qmb_results.py:32` | CHECKED |
| Doors: Python API and CLI; MCP door scaffolded | PARTIAL | `qmb/doors/__init__.py:1-6` | CHECKED |
| Lanes by which door was called; research-paper only, no agent paper | BUILT | `qmb/workbench.py:1-6`; `qmb/paper.py:1-6` | CHECKED |
| Backtest door for agents | PARTIAL | `TOOLS/service.py:280-299` refuses; PR 204 open | PR 204 adds `qmb/host/backtest_door.py` (430 lines), `StoreLanding`, an app_op job, and only the `silent` runner: "a result lands, but with no trades, no equity and no ledger line". Not stacked because it breaks QMB's own scaffold rules (`subprocess`, `threading`, the word "engine"). CHECKED (`git diff --stat` of `build/wu4`; `T/QMB-BACKTEST-DOOR-HANDOFF.md:9-27`) |
| A runner with a real bot | MISSING | `T/QMB-BACKTEST-DOOR-HANDOFF.md:29-35` | Needs a typed-partition entry to `execute_recorded_replay_request`, execution inputs as data, and a nameable shipped bot. CHECKED (handoff) |
| Replay instruments: ticks with bid and ask, or a bid plus ask `bar-m1` pair of one month | PARTIAL | `qmb/host/replay.py:744-778` | Trade prints and trade bars are refused, so the Binance and CCXT data QMX downloads cannot replay. CHECKED; consequence INFERRED |
| Lookback and replay memory | PARTIAL | `qmb/host/replay.py:475-572` (`cumulative` at `:490`, `"samples": list(cumulative)` at `:569`) | Every step stores the whole history so far. About 16 GB for a month of M1 (P-QMBREAD). Runs are bounded to about 1,000 steps until windowed. CHECKED (code); the 16 GB figure is from `T/QMB-BACKTEST-DOOR-HANDOFF.md:39` and `RS/research/12-data-feeds-lookback.md:38`, not measured here |
| Other lookback-style limits | CHECKED in 12 | `RS/research/12-data-feeds-lookback.md:32-52` | The 12-month holdout hides the newest year, not the oldest; the 1,000-bar broker cap is already gone on `EB`. CHECKED (research 12) |

---

## 3. QML

QML code last changed 7 Oct (`git log -1 EB -- qml/src` = `ef976949`). CHECKED.

| Thing | Status | Evidence | Note |
|---|---|---|---|
| Protocol: factory, evidence, intents, state, contract | BUILT | `EB:qml/src/qml/protocol/` listing | CHECKED |
| Declaration: bot, confluence, parameters, versioning, alternative (ATC/PolicyPair) | BUILT | `qml/src/qml/declaration/` listing | CHECKED |
| Footprint, families, generation (structure generation, gaps), research (Stage 0 mill), host (graduation, seed_cite) | BUILT | `qml/src/qml/*/` listings | CHECKED |
| Conformance: layer 1, layer 2, prediction linter, registration, scan, harness | BUILT | `qml/src/qml/conformance/` listing | CHECKED |
| Example bot | BUILT | `qml/examples/conformant_bot/bot.py` | No real bot anywhere (01). CHECKED |
| Block catalogue | MISSING | no module | CHECKED (listing) |
| Indicators that run: SMA, EMA, WMA, RSI, MOM, ROC (6) | BUILT | `EB:packages/qmf-indicators/src/qmf/indicators/wrappers.py` `WRAPPER_SET` | CHECKED |
| Indicators named only: ATR, MACD, BBANDS, ADX, STOCH, OBV, VWAP, session VWAP, session range | DESIGNED-ONLY | `indicators/arithmetic.py:111-131` | CHECKED |
| Structure: swing points only | PARTIAL | `qmf-structure/src/qmf/structure/families.py` (01) | Not rechecked line by line |
| The dictionary in the repo | PARTIAL | `EB:qml/tests/fixtures/research-seed/dictionary/` (3 markdown files) | Test fixture only. The full dictionary sits outside the repo at `C:/Users/Mubarak/Desktop/Stats/dictionary/` (11 entries at top level, `ls`). CHECKED |
| Agent door that takes a strategy and validates or compiles it | MISSING | `TOOLS/functions.py:191` | CHECKED |

---

## 4. MIS

| Thing | Status | Evidence | Note |
|---|---|---|---|
| Six rule labelers: identity, spread-state, gap-event, feed-state, SQS, degraded-sensors, plus the snapshot fold | BUILT | `EB:qmn/src/qmn/mis/labelers.py:1-7`; `signal_snapshot.py` | Runs inside QMN only. CHECKED |
| Fitted `liquidity_stress_v1` | BUILT | `qmn/mis/liquidity.py` | CHECKED (file) |
| Regime training pipeline (corpus, design, eval, labels, register, train) | PARTIAL | `qmn/mis/regime_*.py` (6 files) | No ratified model (`DOCS/glossary.md:556-558`). The corpus reads M5 bars only (`RS/research/12…:46`). CHECKED |
| Shadow lane for candidate labelers | BUILT | `qmn/mis/shadow.py` | CHECKED (file) |
| Readers: the Book door and the KSA, never bots | BUILT | `DOCS/glossary.md:556-558`; snapshot read in `qmn/host/admission_*.py`, `decision_root.py`, `shakedown.py`, `sqs_baseline_producer.py` | Nothing in `qmb`, `qml`, `qmx-agents` or `packages` imports `qmn.mis`. CHECKED (`git grep -l 'qmn\.mis'`) |
| Where it runs | PARTIAL | QMN only; QMN never deployed (`T/research/methodology/50-backend-packages-and-data-today.md:21`, `:133`) | So no labeler has run on a live feed. INFERRED |
| MIS labels on backtest trades | MISSING | 01 §1.5 | QMB has a modelled spread series that non-live SQS can read (`qmb/execution/spread.py`). CHECKED (01) |
| Agents or workflows reading the MIS | MISSING | no catalog row; `db-desk-brief/README.md` leaves out "T2's per-unit MIS conditions grid" | CHECKED |
| Router, premium-session detector, RVOL gate, scalper labelers | MISSING | 01 §1.5 | Not rechecked |

---

## 5. Risk side

| Thing | Status | Evidence | Note |
|---|---|---|---|
| Book (template, instance, binding epoch; admission, sizing, doors, exit policy) | PARTIAL | `EB:packages/qmf-risk/src/qmf/risk/` (24 modules); `DOCS/glossary.md:116-119` | Shape and grammar. Never sized a real trade (01 §1.6). CHECKED (listing) |
| BMS (per account: accounting, constraints, journals, KSA policy) | PARTIAL | `DOCS/glossary.md:112-114`; `qmf-risk` | Same. CHECKED |
| Sizing ladder (book_capital → loss_floor → runway → period_loss_budget → r_unit_price → position_risk_amount) | DESIGNED-ONLY in code | `qmf-risk/sizing.py:1-34` | "Ratified `defined-unwired` surface; no wiring is authorized here (DEC-0158)" at `:34`. CHECKED |
| Loss limits: `loss_floor` (same number as the kill line), `period_loss_budget`, bench loss thresholds | PARTIAL | `sizing.py:7-14`; `DOCS/glossary.md:917` | No daily loss limit term in code (`git grep -i 'daily.loss\|loss_limit'` over `qmn/src` and `qmf-risk` = 0). CHECKED |
| Kill line (per-Book floor, auto flatten) and breakeven ratchet, bench fold | BUILT (never deployed) | `EB:qmn/src/qmn/capital/{kill_line,ratchet,bench_fold}.py`; `DOCS/glossary.md:484-486` | CHECKED (files) |
| KSA: five levels GREEN to BLACK, four trigger classes, escalate only, human resume | BUILT (never deployed) | `qmn/src/qmn/protection/{ksa,effect_matrix,dispatch,ksa_journal}.py`; `DOCS/glossary.md:504-510` | Effect values open under GAP-0050. CHECKED |
| News kill switch: news windows and dead zones, fail closed on a stale calendar | BUILT (never deployed) | `qmn/protection/windows.py:1-11`; `packages/qmf-data/src/qmf/data/calendar_feed.py` | KSA trigger `scheduled_news`. CHECKED |
| SQS (baseline ÷ live spread, block only, never sizes) | BUILT (never deployed) | `qmn/mis/labelers.py:3-5`; `DOCS/glossary.md:985-991` | CHECKED |
| Account guard | DESIGNED-ONLY | 0 hits for `account.guard` in `qmn/src`, `packages`, `qmb/src`, `qmx-agents/packages` | Operator term from `RL decisions.md` (01 §1.6). CHECKED (grep) |
| Pods (seven slots, simulator, `PodCompilerPort`) | DESIGNED-ONLY | `T/architecture/lab-and-pods/ARCHITECTURE-SPINE.md:150-166` (01); Library `pod` kind has one `slots` field, `pod-block` has `slot`, `form` | CHECKED (schemas) |
| Correlation ledger, as the docs mean it | BUILT as a name only | `DOCS/lenses/observability/logging-spec.md:138`; `DOCS/contracts/ct-25-risk-journal.yaml:20`, `:50`; `DOCS/components/trading-node.md:297` | A projection name over `enacts` edges (intent to enactment lineage). Not market correlation. CHECKED |
| Market correlation between units (the control he remembers) | PARTIAL | `qmf-risk/door.py:315-347` (`cohort_correlation`, an optional labelled evidence slot); `TPL/rk2-correlation-drift/README.md:1-20`; `TPL/d4-variant-comparison/scripts/compare.py` | The door can carry cohort-correlation evidence by label. The hourly workflow computes currency legs in R, correlation and overlap matrices, effective number of bets and per-currency limits, but is a draft that needs the trading node. No live correlation gate exists. CHECKED; "no live gate" INFERRED from the grep |
| House money, reverse house money, per-unit self-tuning | MISSING | `git grep -i 'house.money'` = 0 | CHECKED |

---

## 6. Library

| Thing | Status | Evidence | Note |
|---|---|---|---|
| Store: content-addressed objects and blobs, CAS refs, append-only edge and annotation logs, rebuilt catalog, one writer lock, roles writer/replica/cache | BUILT | `LIB/store.py:1-25` | CHECKED |
| Kinds (39): agent-tool, agent, app-profile, artifact, backtest-result, binding, bms, board, book, bot-card, bot, collection, component, dataset, hypothesis, logic, memory-row, merge-conflict, methodology, mini-app-instance, mini-app, model, note, paper-run, persona, pod-block, pod, session, setup, skill, source, strategy, stress-scenario, template, test-report, trade, unit, workflow-run, workflow | BUILT | `git ls-tree LIB/kinds/` (39 schema files) | 01 said 38. No `journal` kind. CHECKED |
| Algo kinds' fields | PARTIAL | `unit`, `bot`, `book`, `bms`, `strategy`, `setup`: no properties. `hypothesis`: statement, source, subject. `backtest-result`: memo_key, world, claim_class, role, fidelity, provenance, outcome. `paper-run`: outcome | `unit` page tabs: Logic, Results, Family tree, Markets (`fields.markets`), Versions (`kinds/unit.schema.json:22-48`). CHECKED |
| `trade` kind: account, instrument, side, world (backtest, paper, demo, live, synthetic), money_digits | BUILT | `kinds/trade.schema.json:1-46` | CHECKED |
| Link types (closed set of 39): supersedes, promoted-from, occurrence-of, corroborates, disagrees-with, confirmed-as, confirmation, invalidation, interaction, out-of-sequence, continues-performance, carries-ledger, enacts, branches-from, produced-by, consumed, derived-from, uses, part-of, cites, tested-by, tests, instance-of, run-of, ran-on, variant-of, version-of, merged-from, annotates, replaces, archived-as, resolves, made-by, used-by, compiles-to, touched, mentions, explains, related-to | BUILT | `LIB/port.py:74-120` | CHECKED |
| Journals today: `trade` items from broker fills; `workflow-run` items; chat `session` items saved by the recorder; engine ledger; `qmx-ledger` run journals; QMN's CT-13 journal (never deployed) | PARTIAL | `qmf-data/importers/journal.py:1-25`; `HOST/host.py:14-15`; `EB:qmx-agents/packages/qmx-ledger/src/qmx_ledger/__init__.py:1`; `DOCS/glossary.md:476-482` | A unit journal is DESIGNED-ONLY (`RS/STATE.md` operator round 10-27). Imported trades carry no `initial_risk` or `r` (`journal.py:20-23`). CHECKED |
| Outbox: PC saves kept while the server is away, idempotent replay, conflicts become `merge-conflict` items | BUILT | `LIB/outbox.py:1-18` | CHECKED |
| Hub and bucket replication, purge, claims | BUILT | `EB:qmx-agents/packages/qmx-hub/src/qmx_hub/` listing; WU7 commit `8c5dc61e` | CHECKED |
| Old-data import labels unproven runs and test items | PARTIAL | PR 217 (MD3, open) | CHECKED (PR body) |
| Backup, restore and sync (copies on This PC, second drive, storages through rclone) | PARTIAL | PRs 225-234 (BR1-BR5, SY1-SY5), all open | CHECKED (titles) |

---

## 7. Trading node (QMN)

| Thing | Status | Evidence | Note |
|---|---|---|---|
| Code: cTrader live client, recording loop, order identity, KSA and windows, kill line, ratchet, bench, virtual ledger, reconcile, seats, MIS, Book-level paper, promotion, proof campaigns, spot paper | BUILT in code | `EB:qmn/src/qmn/` listing (204 files under `qmn/src`); `qmn/venue/` has ctrader, live, spot_paper, spot_recorded | Last code change 7 Oct. CHECKED |
| Deploy planners | PARTIAL | `EB:qmn/deploy/` (boundary, ci_lane, config, creds, data_bootstrap, demo) | Run in check mode against fixtures (`T/research/methodology/50…:133`). CHECKED |
| Deployed | MISSING | `T/research/methodology/50-backend-packages-and-data-today.md:21`, `:133` | "Never been deployed. There is no server running it." CHECKED (doc) |
| What it connects to | PARTIAL | cTrader only; localhost and Unix-socket doors; no connect-back to the PC | Agents reach it through `TOOLS/functions.py:10` (`qmn.doors.api.read_status`), which answers "No node configured". CHECKED |
| Templates waiting on it | PARTIAL | 9 rows with `trading-node` in §1.5 | CHECKED |

---

## 8. Data and brokers

| Thing | Status | Evidence | Note |
|---|---|---|---|
| cTrader Open API, read adapter | BUILT | `EB:qmx-agents/packages/qmx-broker/src/qmx_broker/adapters.py:1`, `:103` | CHECKED |
| cTrader sign-in (loopback receiver, home exchange, key store) | BUILT, not run | `HOST/venue_session.py:1-12`; `qmx_broker/oauth.py` (WU8, merged) | On `EB` the PC is never the cTrader home. PR 211 (LF7, open) makes This PC the home when no server is named. Probes "not run" (`EB:scripts/probes/data/FINDINGS-ctrader.md:5-12`). CHECKED |
| cTrader works without protocol files, refreshes before a read | PARTIAL | PR 221 (LS3, open) | CHECKED (PR body) |
| MT5 | PARTIAL | `adapters.py:59-76` (declaration only); `qmf-data/importers/journal.py` (`from_mt5`) | No reads, no execution. CHECKED |
| CCXT spot reads and bars | BUILT | `adapters.py:247`; `qmx_broker/providers/ccxt_public.py` | CHECKED |
| Hyperliquid | MISSING | `git grep -l -i hyperliquid EB` over code = 0 | CHECKED |
| Data providers: Dukascopy, Binance Vision, CCXT public, Databento (key proof only), Firecrawl | BUILT | `qmx_broker/providers/` listing; `providers/databento.py:1` | CHECKED |
| Downloaders as scheduled workflows (Dukascopy, Binance, CCXT) | BUILT, not run on his home | §1.5 rows 450-468 | CHECKED |
| Price store: typed monthly partitions `source/subject/kind/variant/month`; kinds ticks, bar-m1, fill, trades, book | BUILT | `EB:packages/qmf-data/src/qmf/data/series.py:80-92` | Not described in `DOCS/components/qmf-data.md` or `qmf-data-store.md` (0 hits for "bar-m1" or "SeriesStore"). CHECKED |
| Recorders: QMN's broker recording loop; the news calendar feed | BUILT (QMN never deployed) | `qmn/` listing; `qmf-data/calendar_feed.py` | CHECKED |
| Market-data door: one way in, `commit` for writers, seal and splits on every read, `materialise` for QMB, handles past `HANDLE_ROWS` | BUILT | `HOST/market_data.py:1-12` | CHECKED |
| Door defaults on `EB`: 12 holdout months, refuse to open without `seal_boundary_ns`, server is primary | BUILT, reversed by ruling | `market_data.py:76`, `:215-227`, `:104-110`, `:192-194` | Ruling 137: a lock that refuses by default is a bug; holdout off by default, per study (`26-operator-rulings…:266`). PR 207 (WU11, open) opens the door by default, makes holdout per study, fixes a run's holdout on first read. CHECKED |
| Old 10 GB Dukascopy ticks (EURUSD, USDJPY 2003-2026) | PARTIAL | `T/HANDOFF-2026-10-24.md` §1 | On the server with checksums, import not run. PR 214 (LF4, open) brings old data in on first start. CHECKED (doc and PR title) |
| Broker reads stamped demo or live | PARTIAL | PR 215 (MD2, open) | CHECKED (PR body) |
| Contract specs (contract size, funding, margin) | MISSING | 01 §3.2 grep | Not rechecked; no QMF change since |

---

## 9. Docs that contradict the new intent

| # | Doc says | Evidence | Against |
|---|---|---|---|
| 1 | No futures and no options ever (DEC-0015) | `DOCS/contracts/ct-03-instrument-identity.yaml:46` | Units over CFDs, perps, futures, spot. CHECKED |
| 2 | The Book owns exit policy; a bot only proposes exits | `DOCS/glossary.md:118`, `:138`, `:222`, `:342` | A unit carries its own exits. CHECKED |
| 3 | The bot never sizes; `requested_r` is Book-resolved | `DOCS/components/qml.md:92` | A unit sizes itself from its own record. CHECKED |
| 4 | Exactly one strategy family per bot | `DOCS/components/qml.md:267` (FM-10) | Open; a unit may combine. INFERRED |
| 5 | The MIS reaches only the Book door and KSA, never bots | `DOCS/glossary.md:556-558` | Router intent (01 §6 row 3). CHECKED |
| 6 | No per-bot paper lane (DEC-0261) | `DOCS/components/trading-node.md:225` | A journal and paper per unit (`RS/STATE.md` correction 6). CHECKED |
| 7 | "Correlation ledger" = `enacts` edge projection | `DOCS/lenses/observability/logging-spec.md:138` | He remembers a market-correlation control. CHECKED |
| 8 | Holdout seal of the newest 12 months | `DOCS/registry/variables.yaml:253-262`; `HOST/market_data.py:76` | Ruling 137, holdout off by default. CHECKED |
| 9 | Server is the main copy and primary | `HOST/market_data.py:105`; `T/HANDOFF-2026-10-24.md` §1 | Ruling 136, PC is home. CHECKED |
| 10 | QMB-produced verdicts never gate live money (L20); fills optimistic until calibrated | `qmb/analysis/deferred.py:4-6`; `qmb/execution/fill.py:4-6` | Registry proof from QMB. CHECKED |
| 11 | Node design has no command line | `DOCS/components/trading-node.md:23` | Not contradicted; listed so it is not lost. CHECKED |
| 12 | No page for the engine, host, Library, router, tools, Lab, pods or units; `docs/` last changed 27 Sep | `ls DOCS/components`; `git log -1 -- docs` on `main` | Everything in §1 and §6 is undocumented in `docs/`. CHECKED |
| 13 | `_docwork` workflows design targets `qma-daemon` and Graph Templates | `DW/workflows-increment-brief.md:1-10`; `DW/feature_inventory.yaml` (71 features, all `status: planned`) | The daemon is deleted; the engine replaced it. CHECKED |
| 14 | Catalogue docstring says 31 templates | `TPL/catalog.py:1` | 46 rows. CHECKED |

---

## Changed since 01-ground-truth

1. The trunk moved from `f05fc64b` to `d82be318`. WU1, WU2, WU3, WU5, WU6, WU7, WU8 and WU9 merged. WU4 (PR 204) did not. CHECKED.
2. QMB, QML, QMN and all QMF packages did not change. Every 01 finding about them still holds. CHECKED (`git diff --stat`).
3. App operations now reach a chat (WU1). 01 listed this as open. CHECKED (`HAR/tools.py:541`).
4. Template install now writes the real Library through the host (WU5). 01 listed it as broken. CHECKED (commit `ec3d1694`).
5. Template scripts still read and write a hidden fake Library on `EB`. The fix is MD1 (PR 216, open). CHECKED (PR body).
6. Templates are 46, not "about 40". Library kinds are 39, not 38. CHECKED.
7. The cTrader sign-in exists (WU8) but has never run. Its three probes read "not run". CHECKED.
8. The workflow server has a full setup, recovery and firewall path (WU9). CHECKED.
9. Rulings 136 to 142 came after 01. The PC is home, servers substitute. No default locks. Holdout off by default. `EB` still has the opposite defaults. PRs 207, 208 and 211 implement the rulings and are open. CHECKED.
10. Twenty-nine PRs are open in one stack (local-first, mock data, loose strings, backup, sync). None merged. CHECKED.
11. 01's "correlation ledger" row is refined. The docs name is an `enacts` projection. A market-correlation computation exists only in the `rk2` draft template and as an optional evidence slot in the Book door. CHECKED.

## Shipped work that must not be casually removed

Merged on `EB`. CHECKED unless marked.

| What | Where |
|---|---|
| The workflow engine: format, 13 runnable node kinds, triggers incl. event triggers on Library landings, zones, ledger, PC and remote workers | `ENG/` |
| The 46-template pack, its shared blocks, the deflated-Sharpe and family-trial scripts, the rk2 correlation and exposure maths (draft) | `TPL/` |
| One catalog as the only bridge to agents, REST and node types | `CTL/catalog.py`, `CTL/service.py` |
| The harness: Surface, guard, delegate v2, packs, slot table | `HAR/` |
| The core plugin: five skills, four sub-agents, `QMX.md` | `EB:qmx-agents/plugin/` |
| The Library store, 39 kinds, 39 link types, outbox, Hub replication | `LIB/`, `qmx-hub` |
| The market-data door and the typed price store | `HOST/market_data.py`; `qmf-data/series.py`, `seal.py`, `splits.py` |
| Downloaders, fill importers, the cTrader sign-in, broker reads | `qmf-data`, `qmx-broker`, `HOST/venue_session.py` |
| Remote compute (SSH, Amp, Modal, E2B) and the workflow server setup | `qmx-remote`, `CTL/node.py` |
| QMB: projection, rerun, variants, sweeps, optimise, robustness, synthetic data, one landing shape | `EB:qmb/src/qmb/` |
| QML: protocol, declaration, conformance, Stage 0 mill, ATC/PolicyPair | `EB:qml/src/qml/` |
| QMN's protection set: KSA, news windows, kill line, ratchet, SQS, MIS labelers (never deployed) | `EB:qmn/src/qmn/` |
| `qmf-risk` shapes, including the `cohort_correlation` slot and the unwired sizing ladder | `EB:packages/qmf-risk/` |
| The Lab workspace and PC training rows | `CTL/lab.py`, `CTL/catalog.py:586-674` |

## Not verified

- No code was run. Behaviour is read from code and docstrings.
- Template test runs on real models, and which templates pass today, were not checked.
- Open PRs were read by title, body and file stats, not reviewed as diffs.
- The 16 GB replay figure comes from the handoff and research 12, not my measurement.
- "QMF v2" names no artifact I could find (`git log --all --grep`). The nearest match is the data round's typed store in `qmf-data`, which `docs/` does not describe. INFERRED.
- Rows marked "(01)" or "not rechecked" carry 01's evidence; their code did not change since.
