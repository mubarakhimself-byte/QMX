# 42: Grounding, the code shipped in the last month and the open stack

Written 2026-10-30 by a grounding agent. Read and record only. Nothing here is a design. No repo, branch, worktree or PR was changed.

It builds on `18-grounding-today.md` (trunk `origin/engine/base` at `d82be318`) and goes deeper on seven topics, mainly into the 29 open PRs that the wrap-up coordination session built from 26 to 29 October.

## How to read this

**Labels.** CHECKED = read at the cited path and line, or seen in the cited command output, on 2026-10-30. INFERRED = my reading of checked facts, not seen directly.

**Status tags.**
- SHIPPED = merged on `origin/engine/base` (`d82be318`).
- STACKED (PR n) = in an open PR, not merged. The stack tip is `origin/build/sy5` at `074670ac`.
- PLANNED-ONLY = in a plan or design under `tracker/qma-v2/`, no code.
- MISSING = in neither.

**Short paths.**

| Alias | Path |
|---|---|
| `EB` | `origin/engine/base` at `d82be318` |
| `TIP` | `origin/build/sy5` at `074670ac`, the top of the open stack. Read with `git show TIP:<path>` after `git fetch` in `C:/Users/Mubarak/Desktop/QMX`. Line numbers below are at `TIP` unless marked `EB`. |
| `ENG` | `qmx-agents/packages/qmx-engine/src/qmx_engine` |
| `TPL` | `ENG/templates` |
| `HO` | `qmx-agents/packages/qmx-host/src/qmx_host` |
| `CTL` | `qmx-agents/packages/qmx-control/src/qmx_control` |
| `HAR` | `qmx-agents/packages/qma-harness/src/qma/harness` |
| `LIB` | `qmx-agents/packages/qmx-library/src/qmx_library` |
| `BRK` | `qmx-agents/packages/qmx-broker/src/qmx_broker` |
| `T` | `D:/QMX-worktrees/unit-plan/tracker/qma-v2/` |
| `WR` | `D:/QMX-worktrees/qma-ship/wrapup/RESUME.md` |
| `PR n` | the PR body, read with `gh pr view n --repo MubarakHimself/QMX` |

**The big caveat.** Nothing in the stack has run on his real QMX folder. The stack is not landed, and the first real start on This PC waits for his landing (`WR` "Update 2026-10-26 morning", "real-step order"; `T/LOCAL-FIRST-PLAN.md:502`). CHECKED. Every STACKED row below is code with tests and lanes on throwaway folders, nothing more.

---

## 0. What shipped in the last month, by program

Command: `git log origin/engine/base --since=2026-10-01 --merges --first-parent` and `gh pr list --state merged` (180 PRs merged since 1 Oct). CHECKED.

| Program | PRs | Dates | What it shipped | Status |
|---|---|---|---|---|
| Rebuild P01 to P23 | 26 to 70 (into `rebuild/base`) | 7 to 12 Oct | Green test baseline, CI, control service (REST, MCP, events), old workflow compiler, mini-app runtime, broker accounts and read tools, storage and backup, hooks, remote runs, Docker tier, then the P16 retirement of the old QMA runtime | SHIPPED (brought into `EB` by PR 155) |
| Harness HP0 to HP17 | 71 to 90 | 14 to 18 Oct | The Claude Code based harness: one host, chats under OS limits, money rule and credential guards, approvals, usage, model switch, delegate, provider lanes, temporary console | SHIPPED |
| Engine EP0 to EP14, HG1, HG2 | 91 to 107 | 18 Oct | The `qmx.workflow/1` format, ledger, orchestrator with replay, fan-out, loop, wait, local worker, failure ladder, drafts and runs over REST, llm and agent nodes, triggers, control doors | SHIPPED |
| Template pack TP1 to TP4 | 108 to 111 | 18 Oct | The template pack: research, trader, node, risk, Lab and developer templates (many as drafts) | SHIPPED |
| Build program | 112 to 170 | 21 to 22 Oct | Probes, caps removed, one host process, the guard replacing the money gate, one catalog, Library store and Hub (LIB1 to LIB4), router (RTR0 to RTR6), Surface, triggers incl. event triggers across machines, sessions in the Library, packs as plugins, delegate v2, memory on Hindsight, TPL1 to TPL3, remote worker, run adoption, deletion of the old daemon and LangChain | SHIPPED |
| Data round DR0 to DR14 | 171 to 197 | 24 Oct | Old ticks saved with checksums, typed monthly price partitions, the one price door with a holdout lock, backtests through a door with one result shape, connections registry, feeds and downloaders as workflows, trade kind and journals, upload door, OpenObserve events, Lab workspace and PC training, branch and merge for agents, bar paging past 1,000, steps placed by data | SHIPPED |
| Wrap-up WU1 to WU9 | 198 to 206 | 26 Oct | App tools reach a chat, provider rows and tests, keys and roles, templates install into the real Library, `just ci` green, real copy counts, the cTrader demo sign-in, the server ready to be home | SHIPPED |

The open stack (29 PRs, none merged). Command: `gh pr list --state open --json number,headRefName,baseRefName`. CHECKED.

| Program | PRs | One line each |
|---|---|---|
| WU4 | 204 (on the merged `build/wu2`, not restacked) | Agent backtests through QMB's door, silent runner only |
| WU11, LF5, LF1, LF2, LF6, LF3, LF4, LF7 | 207, 208, 209, 210, 212, 213, 214, 211 | Local first: price door opens by default, no server in defaults, one QMX folder resolver and tree, places he names, store versions, bring old QMX data in, cTrader on This PC |
| MD1 to MD3 | 216, 215, 217 | Mock data out: scripts use the real Library, every broker read says demo or live, old imports labelled |
| LS1 to LS6 | 219, 218, 220, 221, 224, 223, 222 | Loose strings: bring-in as a job, resumed runs land, run inputs, cTrader out of the box, refuse impossible demo rows, template install as a job, the host names what did not open |
| BR1 to BR5 | 225 to 229 | Backup and restore: copies on This PC and a second drive, restore, automatic copies, restore from the first-start card and from Settings |
| SY1 to SY5 | 231, 230, 233, 232, 234 | Sync and connect: what is saved by class, connect a storage, packed copies through rclone, connect a server, Modal, E2B and deep logs, sync before update |

`git diff --stat EB TIP` = 322 files, +42,707 / -3,002. The stack edits QMF in one place (`packages/qmf-data/src/qmf/data/series.py`, a retry on `os.replace`, PR 227) and no QMB, QML or QMN file. CHECKED (`git diff --stat EB TIP -- qmb qml qmn packages`).

---

## 1. How QMA v2 runs workflows, in depth

### 1.1 The engine's pieces

| Thing | Status | Evidence | Note |
|---|---|---|---|
| Runnable node kinds: trigger, script, rule, loop, join, wait, llm, agent, subworkflow, grader (deterministic), monitor, app_op | SHIPPED | `ENG/definition/registry.py:56-95`; executor table `ENG/runner.py:700-719` plus `app_op` from `ENG/control_door.py:308` | CHECKED |
| `library` node kind | Declared runnable, no executor | `registry.py:94` says `available=True`; the runner's table at `runner.py:700-719` has no `library` entry; `workers/local.py:256` fails a node with "no executor serves kind" | 18 listed it as runnable. No template uses it (parser below). The failure at run time is INFERRED from the two checked lines |
| `human_gate`, `rlm`, `claude_workflow`, grader `llm` mode | PLANNED-ONLY | `registry.py:62`, `:81`, `:95`, `:84-91` | No in-workflow approval step exists. Approval today is the draft and publish card (§1.5, §6.1). CHECKED |
| Operation node types `<pack>.<toolset>_<op>` from catalog rows | Declared, unavailable | `registry.py:108-110` docstring | CHECKED |
| Per-node `runs_on` (default `pc`), `toolsets`, `skills`, `credentials`, `outputs.files` | SHIPPED | `ENG/definition/model.py:129-160` (18) | CHECKED in 18 |
| `runs_on` names any place he adds; an empty slot asks for a place by name | STACKED (PR 212) | `ENG/settings.py:68` `places()`; PR 212 body | CHECKED |
| Every attempt records `place`, `place_id`, `machine`, `placed_by` (`default`, `chosen`, `spilled`, `stand_in`) | STACKED (PR 212) | `ENG/runner.py:215-240` | The run's `workflow-run` item carries it as `placement`. CHECKED |
| A live run takes inputs from REST and from its trigger's stored inputs, checked against the workflow's input schema | STACKED (PR 220) | PR 220 body; ledger step 5 adds `triggers.inputs` | CHECKED (PR body) |
| A run killed before its first summary still lands when resumed | STACKED (PR 218) | PR 218 body (`summarize_resumed`) | CHECKED (PR body) |

### 1.2 Triggers

| Thing | Status | Evidence | Note |
|---|---|---|---|
| Time: cron (IANA zone) and interval | SHIPPED | `ENG/triggers/rows.py:1-17`, `triggers/cron.py:1-7` (18) | CHECKED in 18 |
| Library event: fires when an item lands, filtered by kind, output and producer, `each` or `latest` | SHIPPED | `ENG/triggers/event.py:1-25` (18) | No shipped template uses an event trigger. Template trigger kinds across all definitions: 20 `cron+manual`, 1 `interval+manual`, 34 `manual` only. CHECKED (`git grep -o '"kinds": [...]'` over `TPL/*/definition.json`) |
| Manual, after, webhook, session | SHIPPED (session waits for copilot loops) | `rows.py:1-17` (18) | CHECKED in 18 |
| A trigger may name any place as its home | STACKED (PR 212) | PR 212 body (ledger step 4 drops the `pc`/`contabo` check) | CHECKED (PR body) |
| Template triggers install disabled; enabling is his click | SHIPPED | `TPL/install.py:1-8` | CHECKED |
| Host jobs land a `maintenance-result` artifact so an event trigger can fire on it | STACKED (PR 234) | PR 234 body "Maintenance" | CHECKED (PR body) |

### 1.3 How a step reaches an agent, a skill, a hook, a script or a tool

| Thing | Status | Evidence | Note |
|---|---|---|---|
| Agent step: one Background chat per chunk, its Surface built from the node's `tools`, `toolsets` and `skills`, nothing else offered; read-only policy denies undeclared writes; no turn or time ceiling; stuck detector | SHIPPED | `ENG/nodes/agent.py:1-30`, `:93-94`, `:172-173`, `:352-353` | CHECKED |
| Agent step's hooks: the engine's own sink only (PostToolUse spans, PreCompact memory note, Stop logged) | SHIPPED | `agent.py:22-25`, `:409-438` | A workflow cannot declare its own hook. CHECKED |
| Skills a node can name | SHIPPED | `HAR/surface.py:274-279`, `:344-349` | Core plugin skills, pack skills and published Library skills (§7). No shipped template node names a skill: every `skills` list is empty. CHECKED (scratch parser over all 45 definitions) |
| Toolsets agent steps use in templates | SHIPPED | parser | Only `library`, `research`, `data`, `backtest` appear. None uses `broker_read`, `node`, `router` or `lab`. CHECKED |
| Script step: `python -I` subprocess, JSON in and out, allow-listed env, `qmx/tool/<name>` keys, no run timeout | SHIPPED | `ENG/nodes/script.py:1-16` | CHECKED |
| Script step reads and writes the real Library through the host (`parameters.library_reads`, writes listed under `library`, landed on the run's own ref) | STACKED (PR 216) | `script.py:18-22`, `:252-256`, `:577` | On `EB` ten template scripts wrote a hidden fake Library (PR 216 body). Three templates declare `library_reads` at `TIP`: clippings-into-research, crystallise-a-workflow, morning-digest. CHECKED |
| Script step reads prices | SHIPPED | `TPL/download-dukascopy/scripts/download.py:41`, `:199-250` | A script imports `qmx_host.market_data.MarketDoor` and opens the door itself at `[data] root`. CHECKED. Whether two doors on one store read safely together is not checked |
| app_op step runs a mini app's operation | SHIPPED | `ENG/nodes/app_op.py:1-22` (18) | PR 204 adds the `{app: qmb, job: backtest}` job. CHECKED |
| Subworkflow, loop, monitor, grader | SHIPPED | 18 §1.1 | CHECKED in 18 |

### 1.4 Where runs execute

| Thing | Status | Evidence | Note |
|---|---|---|---|
| This PC, in process, scripts in a Job object | SHIPPED | `ENG/workers/local.py:1-22` (18) | CHECKED in 18 |
| A remote machine: the attempt ships as a bundle with a run pass, runs under `qmx-run-sidecar`, heartbeats and results come back through the Hub | SHIPPED | `ENG/workers/remote.py:1-22` | No key travels; model calls go through the owning host's router. CHECKED |
| Providers SSH, Amp, Modal, E2B | SHIPPED | `qmx-remote/.../providers.py:61`, `:186`, `:199`, `:280` (18) | Never run against his accounts (18). CHECKED in 18 |
| Connect a server, Modal or E2B from one dialog | STACKED (PR 232) | `HO/connect_compute.py:1-17`, `:655-676`, `:793-910` | §2 has the steps. CHECKED |
| Steps placed by data locality | SHIPPED | DR14 (PR 197), `remote.py:19-21` | CHECKED |

### 1.5 How results land in the Library

| Thing | Status | Evidence | Note |
|---|---|---|---|
| A run writes only on `refs/runs/<run_id>`; when it passes, records fast-forward to `main` for a live run whose rule is `publish = auto`; definitions and governed kinds go to `refs/drafts/` and wait for his yes | SHIPPED | `LIB/landing.py:1-18` | Governed kinds: binding, bms, book, bot-card, bot, strategy, unit. CHECKED (`git grep '"class": "governed"'`) |
| A test or fake run's artifacts and memory rows are archived "made by a test run" | STACKED (PR 218) | PR 218 body | CHECKED (PR body) |
| An imported old run with no recorded mode reads `unknown` and lands nothing on `main` | STACKED (PR 217) | `LIB/kinds/workflow-run.schema.json` (diff), `landing.py:29` `Mode` | CHECKED |

### 1.6 How templates install and run

| Thing | Status | Evidence | Note |
|---|---|---|---|
| Install: a runnable template is saved, test-run on real models, published `0.1.0`, given its triggers disabled; a template with `meta.needs` is saved as a validated draft and stops | SHIPPED | `TPL/install.py:1-8` | Idempotent by content hash. CHECKED |
| Install into the real Library through the host | SHIPPED (WU5) | 18 §1.4 | CHECKED in 18 |
| Install as a background job with progress (`POST /api/templates/install` answers 202; `GET .../{job_id}` reads step, done of total, rows) | STACKED (PR 223) | PR 223 body | A CLI from before PR 223 fails against a host after it (`WR` "Mixed-version note"). CHECKED |
| Template scripts use the real Library | STACKED (PR 216) | §1.3 | CHECKED |
| Template install has run on his real folder | MISSING | `WR`; `T/HANDOFF-2026-10-24.md:23` | CHECKED |

### 1.7 How a workflow could analyse markets or units today

| Way | Status | Evidence | Note |
|---|---|---|---|
| An agent step with the `data` toolset reads `data.instruments`, `data.bars`, `data.features`, `data.calendar` | SHIPPED, but the door is shut by default on `EB` | `CTL/catalog.py:237-241` (18); `HO/market_data.py:215-224` at `EB` | PR 207 opens it by default. CHECKED |
| A tool call cannot pass a study holdout or a run id yet | STACKED gap (PR 207) | PR 207 "Departures": `qmx_tools/functions.py` was outside its files | CHECKED (PR body) |
| A script step opens the price door directly | SHIPPED | §1.3 | CHECKED |
| An agent step reads broker data (`broker_read`) | SHIPPED; every read stamped demo or live STACKED (PR 215) | `CTL/catalog.py` broker rows (diff at `TIP`) | No template uses `broker_read`. CHECKED |
| A workflow runs a backtest | STACKED (PR 204), silent runner only | §5 | A result lands with no trades. CHECKED |
| A workflow reads a unit, its journal or its MIS state | MISSING | no catalog row for units or journals; the `unit` kind has no fields (`LIB/kinds/unit.schema.json:7-10`) | CHECKED |
| Runnable templates that analyse prices | MISSING | 18 §1.4; parser below | synthetic-data reads a month only to draw a synthetic series. CHECKED |

### 1.8 Every template at the stack tip (45)

Source: a scratch parser over `TIP:TPL/*/definition.json` and `TPL/catalog.py`. `TIP` has 45, one fewer than `EB`: PR 231 removed `backup-weekly` (catalog diff `EB..TIP` at `catalog.py:396-404`). 22 install and run; 23 wait as drafts on a named need; 12 have cron triggers. CHECKED.

"Like" = resemblance by name and purpose to the old WF1 (find and build bots from a source), WF2 (iterate, vary and expand bots), WF3 (bot performance over time) as research 19 describes them (`research/19-grounding-old-system.md:45-74`), or to the Hermes-era strategy sessions (research 39, 40). Every "Like" entry is INFERRED.

**Runnable today (22).**

| Folder | Plain name | Steps | Like |
|---|---|---|---|
| a-fill-the-library | Turn a video, a playlist or saved posts into strategy ideas | 13 script, 6 llm, 1 agent, 2 grader | WF1 intake (the YouTube and article scan) |
| rs0-idea-grill | Question a rough idea until it is a clear test plan | 3 script, 2 llm | WF1 front, Hermes experiment-design bot |
| rs1-paper-scout | Paper scout to research note, every 6 h | monitor, 2 llm, 1 agent | Hermes STRATS research |
| rs2-source-to-component-card | Source to component card | 4 llm, 1 agent | WF1 "vanilla" step (logic as it comes from the source) |
| rs4-literature-review | Literature review on a topic | 7 llm, 1 agent | Hermes STRATS context library |
| clippings-into-research | Turn new clippings into linked research | 1 llm | Hermes intake |
| revolution-loop | Loop a subworkflow until the idea plateaus | loop, subworkflow | WF2 loop shape, no QMB inside |
| ask-the-panel | Ask several model families and show the spread | 4 llm | WF2's "one diagnosis plus one reviewer" against false diagnosis |
| crystallise-a-workflow | Replace a settled agent step with a script | 1 llm | none |
| morning-digest | Digest of everything since he last looked, 07:00 London | 1 llm | none |
| db-desk-brief | Morning market brief before each session | 1 llm | none (node facts and MIS grid left out, 18) |
| t3-news-calendar-watch | News and macro calendar watch | monitor, 1 llm | none |
| t4-research-desk-overnight | Research desk overnight | monitor, 2 llm | Hermes overnight research |
| rv-weekly-review | Weekly review | 2 llm | WF3 review cadence, without bots |
| ev-copilot-eval-battery | Copilot eval battery | 4 llm | none |
| synthetic-data | Synthetic data from a month of prices | 3 script | none |
| connections-health | Connections health, every 5 min (`meta.kind = maintenance`) | 1 script | none |
| feed | Feed (rss, sitemap, page-diff, api, bulk files) | monitor, script | Hermes intake |
| download-dukascopy, download-binance, download-ccxt | Download prices on a schedule | 1 script each | none |
| extract-source | Extract one file's text with page or minute locators | subworkflow | none |

**Drafts waiting on a need (23).**

| Folder | Plain name | Waits for | Like |
|---|---|---|---|
| b-build-and-prove | Turn a strategy idea into a tested strategy, ending on paper | qmb-door | WF1 whole (idea to paper) |
| l1-idea-to-first-result | Get a first backtest result from an idea | qmb-door | WF1 to first report |
| rs3-source-to-lab-test | Source to a Lab test | qmb-door | WF1 "spiced" step |
| d3-iterate-against-qmb | Iterate against QMB with overfit guards | qmb-door | WF2 core (improve with guards) |
| d4-variant-comparison | Variant generation and comparison | qmb-door | WF2 variants; old "AlphaForge" WF1 numbering |
| l4-overnight-lab-loop | Overnight Lab loop, 23:00 London | qmb-door | WF2 unattended loop |
| d6-ml-training-run | ML training run with a holdout | qmb-door, sandbox | none |
| bc-build-a-component | Build a component or indicator | sandbox | QML block building |
| dc-decay-and-limit-report | Decay and limit report | trading-node | WF3 performance over time |
| t7-trade-journal-review | Review my trade journal in risk units | trading-node | WF3, unit journal reading |
| dm-demo-monitor | Watch demo trades and check fill quality | trading-node | WF2 old "paper-trading gate" numbering |
| gw-guard-watchdogs | Check that the trading guards are alive (`maintenance`) | trading-node | none |
| rk2-correlation-drift | Correlation and exposure drift | trading-node | the correlation control he remembers (18 §5) |
| rk5-stress-tests | Stress tests | trading-node | none |
| rk8-incident-post-mortem | Incident post-mortem | trading-node | none |
| p1-portfolio-combination | Portfolio combination study | trading-node, risk-session | none |
| pp-proposal-pack | Bundle a change for me to approve | trading-node, risk-session | none |
| p2-daily-book-report | Daily book report | broker-read-token | none |
| rs6-hypotheses-from-dead-ends | Hypotheses from dead ends | real-library | WF2 rehab of failed ideas |
| rs8-big-data-question | Answer a question over a large table | rlm | none |
| ma-mini-app-lifecycle | Mini app lifecycle | sandbox, app-op | none |
| d9-mini-app-pipeline | Connect one mini app's output to another | app-op | none |
| run-on-a-machine | Run one job on his server (`runs_on: ""` asks for a place) | sandbox | none |

Shared blocks under `TPL/_shared/`: calibrate, extract-source, overfit-gates (deflated Sharpe), paper-read, preflight, render-and-grade, research-harness, save-source, understand-extract (18). CHECKED in 18.

**What the list says.** Every WF1-like and WF2-like template that touches a backtest is a draft waiting on `qmb-door`. PR 204 does not free any of them: each also waits on a door it does not add (spec compile, robustness, family ledger, the Lab), so `catalog.py` is unchanged (PR 204 "Departures"). CHECKED (PR body). Nine templates wait on `trading-node`.

---

## 2. Local first and external compute

### 2.1 What LF, SY and BR ship

| Thing | Status | Evidence | Note |
|---|---|---|---|
| No server in any default; monitoring off until `[telemetry] send_to` names a target; a test fails on any IP literal in shipped source | STACKED (PR 208) | `qma/telemetry.py:1`, `:39-40`; PR 208 body | The hard-coded collector address is gone. CHECKED |
| One resolver finds his QMX folder (flag, `QMX_HOME`, pointer under `%APPDATA%\QMX`, default folder, a scan of fixed drives); nothing makes a folder he did not ask for | STACKED (PR 209) | PR 209 body; package `qmx-home` | CHECKED (PR body) |
| The folder's tree: label plus `data`, `keys`, `backups`, `cache`, `logs`; a step moves a flat old home in | STACKED (PR 210) | PR 210 body, table "Where each file goes" | Several files stay in `data/` because their readers were out of scope (PR 210 departure 2). CHECKED |
| Places are names he types; only `pc` is built in; the `contabo` defaults are gone | STACKED (PR 212) | `ENG/settings.py:68` | CHECKED |
| Every store has a version; open, upgrade after a copy, or refuse by name; Library and price data open read-only when too new | STACKED (PR 213) | PR 213 body | CHECKED (PR body) |
| First-start card: make a new folder, open one, restore from a backup, bring in the old QMX data | STACKED (PRs 214, 219, 228, 234) | `HO/first_start.py:1-25` | CHECKED |
| Bring in old data: the old `~/.qmx` folder, read only, hashed before and after, copied into the new tree, then the Library switched on the copy | STACKED (PR 214, as a job in PR 219) | `HO/bring_in.py`; PR 214 body | A 10,000-item old folder took 663 s in the builder's perf run. This is his old QMX folder, not the 10 GB of old ticks (§4). CHECKED (PR body) |
| Copies: hourly quick undo in `backups/quick/`, copies to any folder or second drive, restore with a staged, journalled finish, a monthly drill | STACKED (PRs 225 to 229) | PR bodies 225 to 229 | CHECKED (PR bodies) |
| What travels: one class table; recipes, his content, run results and prices that cannot be downloaded again are sent; secrets, rebuildable files and scratch never leave the PC; pasted keys listed as "keys to fill" | STACKED (PR 231) | PR 231 body (`qmx_home.classes`) | Removes the weekly GitHub snapshot and the `backup-weekly` template. CHECKED |
| Connect a storage from one dialog (folder, Google Drive, Cloudflare R2, his server over SFTP, any rclone remote) | STACKED (PR 230) | `HO/connect_storage.py:713-731`; PR 230 body | rclone pinned to 1.75.2 by sha256. CHECKED |
| Packed, compressed copies through rclone, monthly upkeep | STACKED (PR 233) | PR 233 body | CHECKED (PR body) |
| A sync before every update; restore from a storage on the first-start card | STACKED (PR 234) | PR 234 body | CHECKED (PR body) |
| Deep logs (OpenObserve) on This PC or on a server | STACKED (PR 232) | `HO/connect_logs.py:443`, `:535` | The OpenObserve sha256 pin is empty, so a fetch refuses until it is filled; OpenObserve on PATH works (PR 232 departures; `WR` "2026-10-29 wave 2 arm"). CHECKED |
| The connect dialog's kinds | STACKED | `HO/connect.py:389` `KINDS = kinds_of(STORAGE, COMPUTE, DEEP_LOGS)` | No kind for a trading server. CHECKED |

### 2.2 Setting up a remote machine today, step by step (PR 232)

From `HO/connect_compute.py:229-238`, `:655-676` and `CTL/node.py:757-790`. All CHECKED.

1. **His card: choose and pay.** "Choose a server and pay for it at a provider such as Hetzner or Contabo, with Ubuntu on it and any size you like; answer yes once it is running" (`connect_compute.py:229-232`).
2. **His card: the address.**
3. **His card: a one-off Tailscale key**, through the write-only key route.
4. **QMX makes an SSH key** in `keys/`.
5. **His card: the server password**, typed in a terminal window QMX opens. QMX never sees it. The window copies QMX's key onto the server.
6. **His card: approve the firewall step.** The firewall stays on only after a fresh login works, and switches itself off within five minutes if that login fails (`:233-237`).
7. **QMX ships its source** to the server.
8. **QMX runs `qmx node setup`'s server steps**, each with a check: bootstrap, join the tailnet, install the recovery script, close the firewall, install the host unit, stop the standalone Hub, lay out the QMX folder, move the pairing key and control token, import as `qmx`, start the host (`node.py:778-790`). Then the PC half: copy the pairing key, write the Hub address, write the recovery twin, read the server's doctor (`node.py:886-889`).
9. **QMX writes one place row** `[engine.placement.<name>]`: `provider = "ssh"`, `kind = "owned"`, `host`, `root = /srv/qmx/home`, `engine_url`, `gateway_url`, `attempt_cpus = 2`, `attempt_timeout = "2h"`, `can = ["run"]` (`:522-538`, `:49-53`).
10. **QMX runs a one-node smoke run** on the server's own engine, reads the status ladder, and reads `qmx-recover status` back.

A rerun skips every step whose check passes (`:10-11`). "Keep copies on your server" is a separate kind run after (`:780`). Modal and E2B take a key, make one provider call and write a row with the provider's kind (`:793-910`). Unproven until a real server runs: the smoke on a real server, the real Modal and E2B check addresses (PR 232 departures). CHECKED.

| Thing | Status | Evidence | Note |
|---|---|---|---|
| The server setup above | STACKED (PR 232); the command-line `qmx node setup` is SHIPPED (WU9) | §2.2 | WU9's server lanes passed on his real server, which was then restored to empty (`WR` "Update 2026-10-25 evening"). CHECKED |
| What the server is | the same `qmx-host` as the PC, `server` role: workflow steps, Library, Hub | `node.py:1-12` | It is a worker and a store, not a trading server. CHECKED |
| Could a trading node be set up the same way | MISSING | no trading-server kind (`connect.py:389`); `qmx-host` setup never installs QMN (`git grep -i qmn` over `HO/` and `CTL/node.py` = 0 hits) | The step-runner shape (his cards, then checked steps, rerun-safe, one row written last) is the reusable part. That a "trading server" kind could be one more `Kind` of the same runner is INFERRED |

---

## 3. The trading node (QMN)

| Thing | Status | Evidence | Note |
|---|---|---|---|
| QMN code | SHIPPED, unchanged in the last month and in the stack | `git diff --stat EB TIP -- qmn` = empty; 18 §7 | CHECKED |
| QMN deploy planners: install, network posture, credentials, lifecycle, upgrade, systemd units, observability | SHIPPED, check mode only | `qmn/deploy/install.py:1-10` ("never SSHes to Contabo"); `lifecycle.py:1-6` | Never run against a host. CHECKED |
| Agents read QMN status | SHIPPED, answers "No node configured" | `qmx-tools/.../functions.py:10`, `:233-235` | CHECKED |
| Anything in the stack touching QMN | none | stack diff | Nine templates still wait on `trading-node` (§1.8). CHECKED |
| Can the shipped connect-a-server path host a node | No | §2.2 last row | CHECKED (no QMN in the setup); "a second kind could" INFERRED |

**What the QMN code still assumes.** Each row CHECKED at the cited path.

| Assumption | Evidence |
|---|---|
| Linux only: the powers door is an AF_UNIX socket checked with `SO_PEERCRED` | `qmn/src/qmn/doors/http/powers.py:1-3`, `:81-82`, `:111` |
| systemd: `Type=notify`, watchdog, fixed `qmx` account, `ProtectSystem=strict`, install under `/opt/qmx/current`, state in `/var/lib/qmx` | `qmn/deploy/systemd/templates/qmn.service.in:14-37` |
| Its own paths, unlike the QMX server's `/srv/qmx/home` and `/srv/qmx/library` | same file; `connect_compute.py:49`; `node.py:6` |
| Credentials sealed with `systemd-creds --with-key=host`, plaintext on SSH stdin only | `qmn/deploy/creds.py:1-6` |
| Inbound default-deny with three SSH identities, doors on loopback or a Unix socket, an egress allow-list | `qmn/deploy/network.py:1-5` |
| Its own observability stack (Grafana, Loki, Prometheus, promtail), while QMX moved to OpenObserve | `git ls-tree TIP qmn/deploy/observability`; PR 232 |
| No command line; three doors only (Python API, localhost HTTP evidence, Unix-socket powers) | `qmn/src/qmn/doors/__init__.py:1-7` |
| Live trading keys belong only on a trading server; the PC, the workflow server and any machine an agent can reach hold read-only or demo keys | ruling 135, `T/research/methodology/26-operator-rulings-and-alignment.md:250-257` (a lead's decision derived from rulings 116-118, with the tension against ruling 117 named at `:257`) |
| Each trading server registers its own cTrader app with Spotware, which approves each one with no published timeline | same file `:254` |
| In code, a live-capable cTrader grant is refused by name and never stored on This PC or a workflow server | `BRK/adapters.py:107`, `:137`, `:172`; `BRK/service.py:342`; PR 211 fix round |

---

## 4. Brokers and data

| Thing | Status | Evidence | Note |
|---|---|---|---|
| cTrader demo sign-in, loopback receiver, home exchange | SHIPPED (WU8), never run | 18 §8 | CHECKED in 18 |
| cTrader signed in on This PC with no server; This PC exchanges the code itself; the pair sits in Credential Manager as `qmx/token/ctrader-app` | STACKED (PR 211) | `HO/venue_session.py:507` `for_host`; PR 211 body | CHECKED |
| A live-capable grant refused before anything is stored | STACKED (PR 211 fix round) | `BRK/adapters.py:107`, `:137-172` | CHECKED |
| cTrader out of the box: Spotware's protocol descriptor ships inside QMX; a token is refreshed before a read; a failed read says why in one line | STACKED (PR 221) | `BRK/service.py:63` (`protocol/openapi-91.pb`); PR 221 body | CHECKED |
| Every broker read (`account_state`, `positions`, `quotes`, `bars`, `symbol_info`) answers `{environment, is_live, connection_id, account_id, result}`; a session that proves the other kind fails as `environment_mismatch` | STACKED (PR 215) | `BRK/service.py:482`, `:507`, `:553`; catalog row texts in `CTL/catalog.py` diff | No orders or history read exists to stamp (PR 215 "Scope"). CHECKED |
| A CCXT demo row on an exchange with no demo mode is refused at write and at read, by asking CCXT itself | STACKED (PR 224) | `BRK/sandbox.py:10` | 54 exchanges at CCXT 4.5.85 (PR 224 body). CHECKED |
| Price door opens by default; holdout off by default and chosen per study (`"off"` or `{"boundary": "YYYY-MM", "months": n}`); a run's holdout is fixed on its first read | STACKED (PR 207) | `HO/market_data.py:88`, `:93`, `:388`, `:758-763` | The final look is served by `[library] primary`, which is `pc` unless set. CHECKED |
| cTrader reads forwarded through a server, and broker history downloads (`download-broker`) | PLANNED-ONLY (WU10, waits on gate G-CT) | `T/WRAPUP-PLAN.md:59`, `:681-722` | CHECKED |
| Bring his old QMX data in | STACKED (PR 214, 219) | §2.1 | CHECKED |
| His old 10 GB Dukascopy ticks | SHIPPED as a script, not run on This PC | `scripts/data/import_old_ticks.py` (PR 207 makes `--seal-boundary-ns` optional and `--placement` default `pc`); `T/LOCAL-FIRST-PLAN.md:502` | Saved on the server with checksums; the PC copy is still on `C:` (`T/HANDOFF-2026-10-24.md:30-33`). Not part of the first-start card. CHECKED |
| MT5 reads or execution | MISSING (declaration only) | 18 §8 | CHECKED in 18 |
| Hyperliquid | MISSING | 18 §8 | CHECKED in 18 |

---

## 5. QMF, QML, QMB

| Thing | Status | Evidence | Note |
|---|---|---|---|
| QML, QMB, QMN since 18 | Unchanged on trunk and in the stack | `git diff --stat EB TIP -- qmb qml qmn` = empty | CHECKED |
| QMF since 18 | One stacked change: the price store's `os.replace` retries Windows errors 5 and 32 | PR 227 body; `packages/qmf-data/src/qmf/data/series.py` (+28/-4) | So a backup round reading a month never breaks a fetch. CHECKED |
| PR 204, the agent backtest path | STACKED (PR 204), not in the main stack | branch `build/wu4` on the merged `build/wu2`; `git diff --stat EB origin/build/wu4 -- qmb` = 5 files, +592 | Left alone on his word and handed to the unit session (`WR` "Operator decisions" item 8; `T/QMB-BACKTEST-DOOR-HANDOFF.md`). CHECKED |
| What PR 204 does | | `qmb/src/qmb/host/backtest_door.py:1-26` at `build/wu4` | A recorded run configuration (series, window, instrument, `runner`, `consumed` dataset card, `uses` bot version, claim class) reads prices through the host's door, replays in one child process, and lands one `backtest-result` on the run's ref, or on `main` as the operator. CHECKED |
| PR 204's only runner | `silent` | `backtest_door.py:60` `RUNNERS = {"silent"}`, `:302`, `:346` | A real QMB run with a CT-32 artifact, but no trades, no equity and no ledger line (PR 204 "Departures"). CHECKED |
| Why PR 204 is not stacked | breaks QMB's scaffold rules (`subprocess`, `threading`, the word "engine") | `backtest_door.py:33-42` imports; 18 §2 | CHECKED |
| A runner with a real bot | MISSING | `T/QMB-BACKTEST-DOOR-HANDOFF.md:29-35` (18) | Needs a factory, a declaration and Book policy that no recorded config carries (PR 204 "Departures"). CHECKED |
| PR 204 against the stack | not rebased | its base is `build/wu2` | It edits `HO/host.py` and `qmx_tools/service.py`, which the stack also edits (`git diff --stat`). A conflict is likely. INFERRED |

---

## 6. The Library

### 6.1 Kinds and records relevant to units, journals and lineage

| Thing | Status | Evidence | Note |
|---|---|---|---|
| 39 kinds, 39 link types | SHIPPED; unchanged in the stack apart from `workflow-run` | 18 §6; `git diff --stat EB TIP -- LIB/kinds` | CHECKED |
| `unit` kind: governed, `identity: manifest`, no fields; card shows version, state, used in, an equity thumbnail; page tabs Logic (`uses` out), Results (`produced-by` in), Family tree (`variant-of`), Markets (`fields.markets`), Versions | SHIPPED | `LIB/kinds/unit.schema.json:1-50` | A unit page exists in the schema. Nothing writes a unit. CHECKED |
| Governed kinds land only as drafts that wait for his yes | SHIPPED | `LIB/landing.py:8-11` | Fits "only he promotes". CHECKED |
| `trade` kind: account, instrument, side, world (backtest, paper, demo, live, synthetic), `initial_risk`; tabs Fills, Chart, Notes and tags, Screenshots, Produced by, History | SHIPPED | `LIB/kinds/trade.schema.json:94`, `:145-170` | Imported fills carry no initial risk or R (18). CHECKED |
| Journals: one per account (backtest, paper, demo, live), tags and notes on a trade never make a new version | SHIPPED as the trade kind plus importers | `T/UI-HANDOFF.md:297` (Library AD-31) | No unit journal and no router journal. No catalog row reads a journal for an agent (`git grep -i journal CTL/catalog.py` finds only the chat request journal at `:336-340`). CHECKED |
| Lineage edges a unit would use: `variant-of`, `uses`, `produced-by`, `consumed`, `tests`, `derived-from`, `promoted-from`, `branches-from`, `continues-performance` | SHIPPED | `LIB/port.py:74-120` (18) | CHECKED in 18 |
| Branch, merge, history, blame for agents | SHIPPED (DR8) | 18 §1.4 | CHECKED in 18 |
| Run results ranked below his own items unless the run was live and passed | STACKED (PR 217 fix round) | PR 217 body (`fts.py`) | CHECKED |
| Imported test-run items archived, never deleted | STACKED (PR 217) | PR 217 body | CHECKED |

### 6.2 What the UI shows

The UI was judged by which screens exist only.

| Thing | Status | Evidence | Note |
|---|---|---|---|
| UI branch `ui-review/repair` at `eea09941` (14 Oct), SvelteKit, demo data, not wired | built before the engine and Library | `git log -1 ui-review/repair`; `T/UI-NOTES.md` §1 | Route pages: home, copilot, library, library item, library article, lab, portfolio, trade, apps, app, authoring, gallery, catalog, settings. CHECKED (`git ls-tree`) |
| Library shelves for units, bots, bot cards, logic | absent on the branch | `T/UI-HANDOFF.md:202` | He said the demo Library shows them; the study found none. CHECKED (doc) |
| Screens the backend now expects: a card and page per kind, the data shelf, trade journals, History and Blame, sealed months in plain words, the Lab workspace | PLANNED-ONLY (UI) | `T/UI-HANDOFF.md:287-300` (§17) | CHECKED (doc) |
| Attach from the Library to a chat or a workflow | backend SHIPPED, screen PLANNED-ONLY | `T/UI-HANDOFF.md:302-308` | CHECKED (doc) |
| First start, places, store versions, runs and templates, broker reads, backups, monitoring | backend STACKED, screens PLANNED-ONLY | `T/UI-HANDOFF.md:312-405` (§19 to §25) | §26 lists gaps, such as the run read not carrying `placement` (`:411`), which PR 234 fixes. CHECKED |

---

## 7. Skills and hooks available to workflows

| Thing | Status | Evidence | Note |
|---|---|---|---|
| Core plugin skills: build-workflow, build-mini-app, debug-app, inspect-qmx, qmx-overview; sub-agents researcher, data-analyst, app-builder, overnight-builder | SHIPPED, unchanged in the stack | `git ls-tree TIP qmx-agents/plugin/` | No skill for markets, units, QMB or QML. CHECKED |
| Add a skill, way 1: a file under `qmx-agents/plugin/skills/<name>/SKILL.md` | SHIPPED | `HAR/surface.py:344-345` (globs `plugin_dir/skills/*/SKILL.md`) | Ships with a QMX release. CHECKED |
| Add a skill, way 2: save and publish a Library `skill` item; it appears in the `library-skills` view | SHIPPED | `HAR/packs.py:15-18`; `LIB/kinds/skill.schema.json` class `definition` | A run-made skill lands as a draft and waits for his yes (`landing.py:8-11`). CHECKED |
| Add a skill, way 3: a pack (a published Library object with `skills/`, `agents/`, `commands/`) | SHIPPED | `HAR/packs.py:1-12` | CHECKED |
| A workflow step uses a skill by naming it in the agent node's `skills` | SHIPPED | `ENG/nodes/agent.py:93-94`, `:352-353` | No template does yet (§1.3). CHECKED |
| The guard: one PreToolUse callback on every tool call, in every mode and inside sub-agents; it protects sign-ins, the keyring, QMX stores, `~/.claude` and a floor of destructive commands; no money words | SHIPPED | `HAR/guard.py:1-12` | It reads inputs as text and says a determined command gets around it. CHECKED |
| The engine's hook sink for agent steps | SHIPPED | §1.3 | CHECKED |
| His own Claude Code hooks in `settings.toml [claude] hooks`, merged into every chat launch the harness makes | SHIPPED | `HAR/home.py:237-247` (`hooks` is an allowed key), `:343-360` (checked shape), `:449-474` (merged per launch) | Whether engine agent chats get them too is INFERRED (same launch path) |
| A pack's or a workflow's own hooks | never written, by design | `HAR/packs.py:8`, `:44` `NEVER_WRITTEN = ("hooks", ".mcp.json")` | CHECKED |
| Tools a step can reach | SHIPPED | `CTL/catalog.py:48-63` core toolsets; `HAR/surface.py:442-450` dynamic `app:`, `mcp:`, `run:` | A new tool is a catalog row on the one `qmx` server, or a mini-app operation. CHECKED |

---

## What the unit-system design can reuse as is

Each row CHECKED unless marked.

| What | Why it fits | Where |
|---|---|---|
| The workflow engine: script, agent, loop, subworkflow, monitor, grader, app_op; cron, interval and Library event triggers; no run timeout for scripts | Builders, monitors and studies for units can be workflows without new machinery | `ENG/` (§1) |
| Placement by name, with `placed_by` recorded on every attempt | A unit study can run on This PC by default and spill to a server or Modal | PR 212 |
| Governed kinds land as drafts and wait for his yes | Matches "only he promotes" with no new gate | `LIB/landing.py:8-11` |
| The `unit` kind's card and page (Logic, Results, Family tree, Markets, Versions) | A page shape already exists; the unit's fields are empty and are the design's to fill | `LIB/kinds/unit.schema.json` |
| The `trade` kind with `world` and `initial_risk`, per-account journals | A unit journal can be built from trade items plus links | `LIB/kinds/trade.schema.json` |
| Event triggers on Library landings | A workflow can react when a unit's result or journal row lands | `ENG/triggers/event.py` |
| The price door with a per-study holdout, off by default, fixed per run | Unit studies choose their holdout; nothing capped | PR 207 |
| Every broker read stamped demo or live | Unit journals can carry the world of every figure | PR 215 |
| The connect dialog's step runner: his cards first, then checked steps, rerun-safe, one row written last | The shape a trading-server setup could take (INFERRED) | `HO/connect.py`, `HO/connect_compute.py` |
| Copies by class, restore, sync before update | Unit records travel with his content; what class a unit journal is remains open | PRs 225 to 234 |
| The overfit-gates shared block (deflated Sharpe), the rk2 correlation and exposure maths (draft) | Ready building blocks for unit checks | `TPL/_shared/overfit-gates`, `TPL/rk2-correlation-drift` |
| QMB projection, rerun, variants, sweeps, robustness, synthetic data, and PR 204's door shape | The backtest side of unit testing; only the real-bot runner is missing | `qmb/src/qmb/`; `build/wu4` |

## What the unit-system design must not break

| What | Why | Where |
|---|---|---|
| Ruling 135 in code: a live-capable grant is never stored where agents work | It is the only thing between an agent shell and live money | `BRK/adapters.py:107-172` |
| The one host as the one Library writer; scripts reach the Library only through `Served` | Two writers caused the hidden fake Library that PR 216 fixed | `ENG/nodes/script.py:18-22` |
| Run refs and the landing rule (nothing on `main` from a test, fake or `unknown` run) | Keeps test output out of his Library | `LIB/landing.py`; PRs 217, 218 |
| Template triggers install disabled; publish and enable are his | His standing rule | `TPL/install.py:1-8` |
| No server in defaults; This PC is home; no IP literals | Rulings 136, 140, 142 | PRs 208, 209, 212 |
| The QMX folder tree and store versions | Every store opens, upgrades after a copy, or refuses by name | PRs 210, 213 |
| The class table's rule that secrets never travel | A unit's settings must not carry keys into copies | PR 231 |
| The price door's run-fixed holdout | A unit study cannot change its holdout mid-run | `HO/market_data.py:88` |
| QMN's protection set (KSA, news windows, kill line, ratchet, SQS) | Never deployed, but it is the live-side safety code | `qmn/src/qmn/` |
| Stores' version labels and the mixed-version note for template install | A CLI and host from different releases break on the install job | `WR` "Mixed-version note" |

## Questions the code raises

1. **Where does a unit run live?** Ruling 135 (a lead's decision) keeps live-capable keys off This PC and off the workflow server, and QMN is Linux and systemd only. "Local first" and "units stand alone" then meet a machine the shipped setup cannot build. Does a unit trade live only on a trading server, or does he overrule 135 for his PC (`26-operator-rulings-and-alignment.md:257` names this choice)? CHECKED facts, INFERRED tension.
2. **Is a trading server one more connect-dialog kind?** The step runner fits, but QMN's paths (`/opt/qmx`, `/var/lib/qmx`), credstore and observability differ from the QMX server's. Same machine as the workflow server, or never? INFERRED.
3. **Does QMN stay the live runtime for units?** It hosts "bots" under Books with seats and promotion. The unit replaces the bot and sizes itself, which the docs contradict (18 §9 rows 2, 3). What of QMN's admission, seats and Book door survives? INFERRED.
4. **What is a unit in the Library?** The `unit` kind has no fields and `identity: manifest`. What its manifest holds (logic, risk, conditions, session profile, exam baseline) is open. CHECKED (empty schema).
5. **Where do unit journals and the router journal live, and what backup class are they?** No journal kind exists, and the class table decides what leaves the PC. CHECKED (no kind); class INFERRED open.
6. **Which door runs a unit's backtest?** PR 204 is the only path and runs no trades. A real runner needs a factory, a declaration and policy as data. Does the unit become that declaration? CHECKED (handoff); question INFERRED.
7. **Is PR 204 kept, reshaped or replaced?** It is off the stack, on an old base, against QMB's scaffold rules, and handed to this session. INFERRED likely conflict.
8. **Should unit work use the `library` node kind?** It is marked runnable but has no executor. Fix or delete? CHECKED.
9. **Is the WF1 and WF2 lineage carried by templates or by new workflows?** Six of the backtest templates are WF1 or WF2 shaped and all wait on `qmb-door` plus another door each. Do the Hermes-era workflows (STATE.md line 151) extend these or replace them? INFERRED.
10. **Can an agent pass a holdout or a run id from a tool call?** PR 207 left `qmx_tools/functions.py` out, so agent reads cannot choose a study holdout yet. CHECKED.
11. **Does a unit's live feed come through the broker reads or through QMN's recording loop?** Broker reads open one short TLS session per read on This PC (PR 211 departures); the long-running ConnectionManager (WU10) waits on G-CT. A feed pool for 200+ units needs one of them. CHECKED facts, question INFERRED.
12. **Do his own Claude hooks reach engine agent steps?** If yes, a unit-building workflow inherits them. INFERRED.

## Not verified

- No code was run. Behaviour is read from code, docstrings and PR bodies.
- PR bodies were read in full for 204, 207, 208, 211, 214 to 217, 220 to 224, 232 and 234, and by their "what it does" sections for the rest. Diffs were read where a row cites a path.
- Template test runs on real models were not checked.
- The UI branch was listed, not opened in a browser.
