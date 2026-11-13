# 08 QMX today, for the design lead

Read-only grounding, 2026-11-10. Code: `D:/QMX-worktrees/engine-base-read` at `3ae41ffc` (engine/base, 2026-11-08, PR #352). Paths below are relative to `qmx-agents/packages/` unless they start with `qml/`, `apps/`, `examples/` or a drive.

Short names:
- **CS** = `qmx-control/src/qmx_control/service.py`; **CAT** = `qmx-control/src/qmx_control/catalog.py`; **HR** = `qma-harness/src/qma/harness/routes.py`; **HOST** = `qmx-host/src/qmx_host/`.
- **INV** = `C:/Users/Mubarak/Desktop/QMX/tracker/release-inventory/` (SHIPPED, JOURNEYS, PLANS, MERGED-PRS).
- **UIH** = `D:/QMX-worktrees/unit-plan/tracker/qma-v2/UI-HANDOFF.md` (last current 2026-10-28). **UNU** = `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/build/UI-NOTES-UNITS.md`.
- **G01/G02/G03** = the earlier grounding reports in this folder.

"(plan, not verified in code)" marks every claim I could not find in code.

---

## 1. QMX in ten lines

1. QMX is a Windows-first desktop app for one non-technical trader. It mixes quant research (data, backtests, a judge) with AI agents that do the work for him.
2. Today it is a backend only. One program, `python -m qmx_host serve`, runs chats, workflows, the Library and mini apps on one port (default 8766) behind one bearer token (HOST `__main__.py`, `host.py:1169`).
3. **No screen talks to it yet.** There is no desktop shell in the repo. `apps/qmx-ui` on engine/base is a stale 2026-09-28 stub (G01 §4; INV SHIPPED "Three things true").
4. He talks to a **copilot** (a Claude Code chat run through the Claude Agent SDK). The copilot writes units, workflows and apps, runs backtests and reads data through about 19 tool sets (CAT:48-68).
5. A **unit** is a trading strategy written as a document. It is checked, backtested by the **QMB** mini app and judged. It moves to paper or live **only on his click**.
6. A **trading node** (a headless mini app) trades units on a broker account (cTrader demo, Hyperliquid testnet). It runs on This PC or on a server he names.
7. **Workflows** are QMX's own engine documents. They run on schedules and events, with or without AI steps, and land results in the **Library**.
8. The **Library** is the one store for everything: 49 item kinds, versions, links, no delete (`qmx-library/src/qmx_library/kinds/`).
9. A normal day (plan, from J22 and UNU §2): overnight workflows run. In the morning he reads a "needs you" list and proposals. He asks the copilot for an idea, a unit or a backtest. He clicks to promote what passed. He glances at nodes and alarms.
10. Nothing has yet run on his real folder or a real demo account. Risk and sizing are placeholders until the open risk-core PRs (#353-#369) land (INV README rows 8-9).

---

## 2. The nouns

Each block says: what it is · built today · planned · how it relates · what he does with it.

**Agent / copilot / session / sub-agent**
- **Copilot** = his own chat, an "Interactive" chat in the harness (`qma-harness/src/qma/harness/home.py:707-725`). Other chat kinds: **Background** (a workflow's `agent` step, nobody watching) and **Child** (a helper of another chat).
- **Session** = one chat. It has a title, model, effort, permission mode, profile (provider) and a **home**. Home kinds: `general, lab, portfolio, library, app, agent` (`qma-harness/.../launch.py:166`). Every session is also saved as a `session` Library item (PR #141).
- **Sub-agent / helper**: two kinds.
  - Native Claude sub-agents. Their tool calls go into a child session.
  - `delegate` helpers. They return a handle at once and run in parallel, on any provider. They can be listed, steered ("queued for the next checkpoint") and stopped. States: `queued, running, done, failed, stalled, stopped, unknown` (`qma-harness/.../delegate.py:62,518-530`; PR #151).
- Built: create, list, send, stop, approvals, model/effort/mode switch with a cost quote, rewind and export over REST (HR:267-371).
- Missing at REST: rename, delete, compact now, setting the home, attach on click (G01 Copilot table).
- He: chats, approves, switches models, watches helpers.

**Orchestrator (planned, not in code)**
- His new idea (`refs/his-words.md:52`): a "Shepherd-protocol" orchestrator plus Hindsight memory that self-improves and drives workflows and mini apps. "We may or may not build it, but cater for it."
- Nearest things that exist:
  - the engine's "pure orchestrator" core (`qmx-engine/src/qmx_engine/core/__init__.py:1`). This is a workflow scheduler, not an agent.
  - `delegate` v2 parallel helpers.
  - The spine allows a `delegate` role `orchestrator` with a depth setting (`unit-plan/tracker/qma-v2/architecture/workflow-engine/ARCHITECTURE-SPINE.md:338`). No such role appears in the harness code.
  - Backlog B35 "a Claude orchestrator that picks models" (`unit-plan/tracker/qma-v2/BACKLOG.md:69`).
- Design for a run tree (orchestrator, then helpers, then tools), but wire it to sessions plus delegate handles.

**Workflow (kinds, triggers, runs)**
- What it is: a folder holding `definition.json` (schema `qmx.workflow/1`, n8n-shaped) plus scripts, prompts and schemas. QMX's own durable engine runs it (G02 §0).
- Step kinds available: trigger, script, rule, loop, join, wait, llm, agent, subworkflow, grader (deterministic), monitor, app_op, library (`qmx-engine/src/qmx_engine/definition/registry.py:50-95`). `human_gate`, `rlm` and `claude_workflow` exist but are not available.
- Shapes: script-only, mixed, or fully agentic. These are shapes of one thing, not separate products.
- Lifecycle: draft → published version → enabled ⇄ disabled → archived. Publish and enable are his clicks only (G02 §1).
- Trigger kinds: `cron, interval, manual, after, webhook, event, session`. A trigger pins one published version and has a home place (`qmx-engine/.../triggers/rows.py:1-20`). The `event` matcher and `session` triggers are only partly built (same docstring).
- Run statuses: `queued, running, waiting, passed, failed, stopped, interrupted`, plus a mode badge `live | test`.
- One run list covers every unit of work. There are no separate "jobs" or "remote runs" lists.
- About 55 templates ship (`qmx-engine/src/qmx_engine/templates/`).
- Made mainly by the copilot's `build-workflow` skill (PR #152). No graph editor is built.
- He: says one line, reviews the test result card, clicks Publish and Enable, watches runs.

**Mini app, pack, plugin, widget, panel**
- A **mini app** is a folder with `app.toml` plus an MCP server, jobs, agents, workflows and an optional `ui/` folder (`qmx-apps/src/qmx_apps/manifest.py:102-107`).
- App kinds: `screens | headless | both`. Risk class: `shows | runs | money` (`manifest.py:234-235`).
- When published it is a `mini-app` Library item. A chat loads it as a **Claude plugin view**: skills, agents and commands only, never hooks or `.mcp.json` (`qma-harness/.../packs.py:1-17`; PR #144).
- "Pack" = the same packaging for the Lab, Portfolio and core groups.
- An app's **screen** is plain HTML served as an MCP `ui://` resource (`examples/apps/exchange-status/server.py:16`, `ui/view.html`). The UI reads it via `GET /api/apps/{id}/resources` (CS:2065-2067). This is the MCP Apps pattern: the shell must host sandboxed HTML.
- Built: install, test, publish, rollback, start/stop/restart, logs, evidence, call an operation (`POST /api/apps/{id}/tools/{op}`) (G01 Apps).
- The three first-party apps (QMB, MIS, trading node) are all `headless`. They have no screen of their own.
- Two example apps have screens: `exchange-status` is `screens`, `macro-daily-bias` is `both`.
- **Widgets/panels**: no widget object exists in backend code. The only grep hit is a template script. The October tiling board and widget frame are UI-only ideas. The backend gives you `ui://` app panels, the `panel` and `table` chat blocks, and Library cards. The design's "widgets inside chat" via directives is (plan, not verified in code) (UIH §11 row 1).
- He: installs, enables, opens apps, and asks the copilot to build one. The `build-mini-app` skill is a placeholder (`qmx-agents/plugin/skills/build-mini-app/`; G02).

**Library item kinds**
- 49 schema files in `qmx-library/src/qmx_library/kinds/`.
- Trading things: unit, strategy, bot, bot-card, logic, component, setup, pod, pod-block, book, bms.
- Proof: backtest-result, verdict, try, test-report, study-spec, paper-run, trade, death-certificate, stress-scenario.
- Inputs: dataset, instrument, venue, account, source, forecast, binding.
- Running things: workflow, workflow-run, template, mini-app, mini-app-instance, app-profile, agent, agent-tool, skill, persona, methodology, model.
- Knowledge: note, hypothesis, memory-row, artifact, collection, proposal-card, session, baseline-card, merge-conflict.
- Behaviour: write-once versions, drafts on side refs, merge, typed links, history, blame, marks such as "built on quarantined input", and archive with a reason. There is no delete except a secret purge (PRs #131, #136, #195).
- REST: search, read, versions, links, save, branch, merge and publish. There is no kind filter on the list route (G01 Library).
- He: browses shelves, opens a card, then the full page, adds items to the copilot, publishes drafts.

**Unit** (formerly bot / strategy)
- Document `qmx.unit/1` (`qml/src/qml/unit/`, PR #239). Built from 113 dictionary blocks. The checker names every problem at once (PR #253).
- One lifecycle per unit version per market: `draft, tested, parked, paper, live, stopped, retired`. It is moved by three actors: the judge, his click and risk rules. Only his click (principal `operator`) moves a unit toward paper or live (`qml/src/qml/lifecycle/machine.py:1-54`).
- Promote route: `POST /api/units/promote`, operator-only (HOST `promote.py`, PR #302).
- Most unit reads (`unit_check`, `unit_explain`, `journal_query`, `blocks_*`) are **model tools only**, with no REST route (G01 Unit screens).
- The old `bot` and `strategy` kinds still exist beside `unit`.
- He: asks for a unit, reads its checks, results and journal, clicks Publish, then Promote to paper.

**Pod**
- Only the `pod` and `pod-block` Library kinds exist. No pod code. Pods are parked behind the unit work (INV SHIPPED §10; JOURNEYS G).
- Planned: a versioned stack of blocks with a live and a paper side (UIH §5) (plan, not verified in code).

**Lab / experiment / project / run / backtest (QMB)**
- Lab backend: a `Lab` class with 7 operations: levels, new, open, workspace, panel, training, model (`qmx-control/src/qmx_control/lab.py:190`; CAT:805-893).
- Every Lab row is `agent=False` and has no REST route. Nothing mounts it. **The Lab has no HTTP today** (G01 §3 gap 3).
- Projects are Library collections. "New…" installs a template at one of four levels: quick idea, experiment, study, campaign.
- Lab procedures (backtest, sweep, walk-forward, training) are workflow templates (G02 §4).
- **QMB** is a headless mini app. Its jobs: backtest, behaviour check, conformance, sweep, walk-forward, robustness, optimize, what-if, replay check (`apps/qmb/app.toml`). Results land as `backtest-result` items.
- The **judge** counts tries and cannot be talked round (`qmx-judge/`, PRs #275, #340, #341).
- Backtests start via copilot tools (`backtest_run` and the rest). There is no REST route to start one from a screen (G01).
- He: asks for a backtest, reads money/R/drawdown results and the verdict.

**Trading node / server / machine / placement ("where it runs")**
- **Place** = This PC (`pc`, always first and always the default) plus the names he gives servers (`GET/PUT /api/settings/engine`, `placement.<name>.*`). No server ships in the defaults (PR #208).
- Each run records `placement: {place, machine, placed_by, line}`, for example "ran on pc, by default". The single run read carries it; the run list does not (G01).
- **Connect dialog** kinds: storage, compute, deep logs, trading node (`HOST/connect.py:384-390`). Each is a job that returns generic `needs` cards (card, line, fields, key, link, job).
- **Trading node** = a headless app with about 20 operations: status, units, positions, journal_tail, passport, deploy, withdraw, pause, resume, kill, flatten, sign-in, self_test, rotate_keys and more (`apps/trading-node/app.toml`). Reached through the generic app-call door.
- Node state words: Setting up · Starting · Ready · Trading · Healing · Paused · Stopped by a risk rule · Stopped by a health check · Unreachable since … (UNU §0).
- Heartbeats and a live machine state are model tools only. There is no nodes strip at REST (G01).
- He: starts a node on This PC, adds a server, deploys a unit, pauses or kills.

**MIS (market intelligence)**
- A headless app with four operations: configure, status, round, board (`apps/mis/app.toml`, PR #295).
- It publishes readings per market (efficiency, variance ratio, Hurst, spread state), each with a freshness word. It never trades.
- Agents read it with the `readings` tools. Screens reach it through the app-call door.

**Provider / account / usage / model routing**
- Providers are data files. Built-in profiles: claude, gpt, kimi, deepseek, glm, qwen, minimax, meta, ollama, opencode-go, openrouter (`qmx-router/src/qmx_router/profiles/`).
- One row per model. Routing is by model id. The account pool rotates keys on errors. Sub-agents can run on other providers (PRs #137-#149).
- Settings sections `providers` and `roles` (CS:55-78). `GET /api/usage` returns plan windows, readings and tokens per profile (HR:373).
- **No QMX caps, shares or budgets.** Only the providers' own limits, shown as readings (UIH §9 row 15; rulings 26, 90, 106).
- Per-turn cost and a context meter are not passed to the UI (G03 "Dropped").
- The "Accounts page" with per-account strategy is (plan, not verified in code) beyond the pool itself.

**Inbox / notifications / approvals**
- `GET /api/inbox` merges three lists: observer notes, open incidents (for example backups) and workflow inbox items. Severity: `normal | urgent | black`, plus `info` for the digest.
- The actions are a closed set: `retry, stronger_model, skip_node, open_trace, stop, resume` (`POST /api/inbox/{id}/resolve`; CS:2380).
- There is no inbox push stream; the UI must poll.
- **Approvals** are chat blocks (`permission`, `question`) answered at `POST /api/approvals/{sid}.{seq}`. Decisions: `allow_once` (optionally with edited input), `allow_always`, `reject` (with a message), `answers` (HR:180-205).
- Background chats answer by policy or time out.
- Phone alarms (ntfy, Healthchecks) exist only for the trading node (PRs #303, #346).
- "Proposals" (promote this unit, accept this lesson) are Library `proposal-card` items, not inbox items.

**Memory**
- Hindsight engine with the built-in search as backup. Memories are `memory-row` Library items (PR #153).
- Operations: recall, note, check, forget, rebuild. These are **model tools only**, with no REST route (CAT ~668-730).

**First start**
- A separate card program on the same port, with no bearer: new folder, open, restore, bring in old data. It hands over the folder, then the desktop shell starts `serve` (HOST `first_start.py:1729-1742`; UIH §19 has the exit codes).
- On first start the dummy unit lands as a draft and the dictionary as a collection waiting for one publish click (PRs #256, #270).
- The "Getting started" checklist **has no backend** (INV JOURNEYS J1).

---

## 3. What agents can and cannot do today

**Tools.** Every chat gets the core QMX plugin plus tool sets: library, workflows, data, backtest, research, node, broker_read, apps_admin, memory, context, delegate, settings_read, ops, router, lab, unit, blocks, instrument, readings (CAT:48-68).
- One catalog row serves chats, workflows and REST alike.
- Each mini app adds a set named `app:<id>`. Published Library skills join as a `library-skills` view (`packs.py:15`).
- Core plugin contents (`qmx-agents/plugin/`):
  - skills: build-workflow, build-unit, build-mini-app (placeholder), debug-app, inspect-qmx, qmx-overview;
  - agents: app-builder, data-analyst, overnight-builder, researcher.

**Permission modes:** `default, acceptEdits, plan, bypassPermissions, dontAsk, auto` (`launch.py:68-70`). Effort: `low, medium, high, xhigh, max`. He set no planning mode in the October UI ("I don't want a planning mode", trace §3), but the backend accepts `plan`.

**What they may touch.** The **guard** runs first on every tool call, including inside sub-agents (`qma-harness/.../guard.py:1-12`).
- It blocks sign-ins and key files, the OS keyring, QMX's own stores, his `~/.claude`, and destructive or evasive commands. Then it applies his never-allow list.
- His always-allow list never lifts those blocks.
- The guard says itself that it is not a sandbox ("a determined command gets around it").
- An agent step in a workflow may write only its declared output file (PR #243). Agents are kept out of grants folders (PR #312).

**Money boundary.**
- "nothing in the catalog places, amends or cancels an order" (CAT:281). `node_propose_order` only writes an unsigned proposal and always asks.
- Promote and deploy are an operator-only host route, never a tool (PR #302).
- One exception: cTrader's own MCP tools are given to agents **for demo accounts only**. Every launch checks the account record is `world: demo` (`demo_only.py`, PR #324).
- Broker reads (balances, positions, quotes, bars) are tools stamped demo or live. There is no REST route for screens yet (G01 gap 4).

**What the UI can observe live** (G01 streams, G03 §3):
- Chat: 14 stored block kinds `user, text, plan, agents, tool, changed, artifact, table, entity, question, permission, panel, handoff, needs_you` (CS:158-176), plus a live delta stream (`text | thinking | tool_progress`) at `/api/sessions/{sid}/live`.
- Sub-agents: an `agents` card. Child tool calls go into a child session. `tool_progress` gives "description: last tool". Delegate completions arrive as events.
- Tool calls: `tool` blocks go started → finished or error.
- **File changes: there is no file-change or diff event.** The `changed` block means config change, rewind or compaction only (`chat.py:900,1008,1441`). A file edit shows only as a `tool` block with an Edit/Write input.
- Library changes: SSE topic `library` sends `{type:"saved", item_id}`.
- Workflow runs: `/api/engine/events?run_id=` streams one run at a time. Events include node_started/finished, tool_called, gate_opened, memory_written and zone_committed.
- SSE needs the bearer header, so the UI must stream with `fetch`, not `EventSource`.

**What the backend drops** (G03 "Dropped"):
- thinking after reload;
- the init list of skills, slash commands, MCP servers and plugins, so there is no "/" palette data;
- the "compacting" status;
- per-turn cost, time and tokens;
- the context-window meter;
- sub-agent tokens and elapsed time, and sub-agent prose;
- permission titles, and which sub-agent asked;
- a per-helper stop for native sub-agents;
- session fork.

The `jobs` topic is never written. The `runs` topic refreshes only when someone reads aggregates (CS:1011, 1851-1867).

---

## 4. What changed since October that an early-October UI gets wrong

The October UI (`ui-review/repair`, last commit 2026-10-14) predates the build program (19-22 Oct), the data round, local-first (31 Oct), and the unit build and repair (#235-#352, merged around 8 Nov).

| Concept | October UI assumed | True now | Source |
|---|---|---|---|
| Backend door | "Not connected to daemon"; qma-wire, packs, mailbox | One `qmx_host` process, REST + SSE, bearer from the keyring; the daemon and wire were deleted | PR #119, #169; HOST `host.py` |
| Strategies | Bots, strategies, pods with live/paper sides | **Units** with a per-market lifecycle; pods unbuilt | `qml/src/qml/lifecycle/machine.py`; PR #239, #250 |
| Portfolio pods, books, BMS | Central Portfolio screens | Parked; risk core not merged (#353-#369 open) | INV SHIPPED §10, README |
| Trading node | Folded into Portfolio Live as VPS chips | A headless mini app with ~20 operations; starts on This PC first | `apps/trading-node/app.toml`; PR #282, #288, #325 |
| Machines | Contabo and a QMB machine as defaults; "3 of 4 machines" | This PC is home; servers are opt-in places he names; no server in the defaults | PR #208, #212; UIH §20 |
| Backtests | Lab "Test" bench, sweep grid | QMB mini app jobs, started by the copilot; judged with counted tries | `apps/qmb/app.toml`; PR #261, #275 |
| Lab | Build/Test/Train/Compare benches, Graph/Code editor | Backend workspace not mounted at HTTP; no graph editor; procedures are templates | `qmx_control/lab.py:190`; CAT:805-893; G02 §4 |
| Workflows | Live on a Lab Resources tile; node palette | Engine documents with their own lifecycle, triggers and runs; built by the copilot skill | `qmx-engine/`; PR #152; G02 |
| Widgets / tile board | Every surface is a tiling board of widgets; copilot makes widgets via json-render | No widget object in the backend; app screens are `ui://` HTML; chat has 14 fixed block kinds | `manifest.py:107,235`; CS:158-176 |
| Mini apps | 21 demo apps, per-app copilot, Remove button | Apps are Claude plugins loaded into any chat; no per-app copilot; archive (501 today) instead of delete | PR #144; CS:2387-2390 |
| Inbox | A bell plus a "Needs you" panel | `/api/inbox`: notes + incidents + workflow items with closed actions; poll only; he wants it "agentic" (11-09) | CS:2380; `refs/october-ui-trace.md` §1 |
| Caps and budgets | Safety page with agent plan share and daily caps | No QMX caps anywhere; provider readings only | UIH §9 row 15 |
| Copilot modes | Ask / Plan / Do, then "areas" | Permission modes from the SDK plus effort; tool sets per chat | `launch.py:68-71`; CAT:48 |
| Sessions | Copilot-local threads | Every chat is a Library `session` item with a home kind (incl. `agent`) | PR #141; `launch.py:166` |
| Data | "Add source" dialog | Typed monthly price partitions behind one data door; downloader workflows; connections with health words | PR #184, #185, #189, #191 |
| Holdout | Sealed months by default | Open by default; holdout is per study | PR #207, #335 |
| Backups | Not designed | Copies on This PC and a second drive; restore from the card; storage via rclone | PR #225-#234 |
| Agents and brokers | Agents never touch brokers | Agents read demo/live-stamped broker data and act on **demo** via cTrader MCP | PR #215, #324 |
| Memory | Not shown | Hindsight memory rows in the Library, model tools only | PR #153 |
| Templates | 26 on a shelf | About 55, installed published but disabled | `qmx-engine/.../templates/catalog.py` |

---

## 5. The journeys that matter most

From INV JOURNEYS A and B and UNU. Status is backend status; nothing is wired.

1. **First start**: card → new/restore/bring-in → handover → (getting started list, not built). Nouns: first start, Library, unit, place.
2. **Idea to judged unit (R14)**: "Build me a unit on EURUSD … ADX above 25, backtest March 2025, tell me what the judge says." Nouns: copilot, unit, QMB, judge, Library.
3. **Copilot writes a unit with live checks** (J2): a draft card fills, then the problem list, then checks pass. Nouns: session, unit, checker.
4. **Overnight agent builds and proves units** (J3), then morning proposals. Nouns: workflow, trigger, agent step, judge, proposal-card, inbox.
5. **Promote to paper on his click** (J5, C-23). Nouns: unit lifecycle, proposal, trading node, account.
6. **Start a trading node on This PC, sign in to cTrader demo** (J6, C-11). Nouns: connect dialog, node, keys, place.
7. **Deploy a unit to a node, then withdraw** (J7). Nouns: unit, node, account, markets.
8. **"Why didn't it trade at 08:00?"** (J13, R19). Nouns: journal, node, readings.
9. **A unit stops on a risk rule; alarm; resume / back to paper / retire** (J9, J12). Nouns: node, inbox, phone alarm, lifecycle.
10. **Build and publish a workflow from one sentence** (TPL2, J11). Nouns: copilot skill, workflow draft, test run, triggers.
11. **Watch runs and fix a failure from the inbox** (retry / stronger model / skip). Nouns: run, inbox, spans, place.
12. **Watch the copilot work: helpers, tool calls, approvals** (his words 11-09; UIH §10). Nouns: session, sub-agent, delegate, approval.
13. **Install / enable a mini app and use its tools in chat** (PACK). Nouns: mini app, plugin, operations, `ui://` panel.
14. **Download data and see its coverage** (R08, data shelf). Nouns: dataset, connection, workflow, Library.
15. **Usage and providers: see plan windows, add a provider, test it**. This shipped with no journey written (JOURNEYS J). Nouns: provider, account pool, usage.

---

## 6. Extensibility: what he can add, remove or rebuild today

| Thing | Add / change by | Remove by | Built? |
|---|---|---|---|
| Mini apps | Folder with `app.toml`, install/publish via `/api/apps…`; or the copilot (skill placeholder) | Disable; archive returns 501 | Yes, except archive |
| App screens (panels) | `ui/` folder → `ui://` resources, `kind = screens/both` | Republish | Yes (2 examples) |
| Workflows | Copilot `build-workflow`, templates, or REST draft put | Disable trigger, archive version | Yes |
| Triggers / schedules | `/api/triggers*` (7 kinds) | Disable | Yes (session, event matcher partial) |
| Skills, agents, commands | Inside a pack; published Library `skill` items join chats | Archive | Yes (`packs.py`) |
| Providers and models | `providers` / `roles` settings rows; profile files | Remove row | Yes (no REST "Test"; tool only) |
| Machines / places | `placement.<name>` rows in `[engine]`; connect dialog (compute, trading node, storage, deep logs) | Remove row (its triggers read `blocked_config`) | Yes |
| Data sources | Connections settings; downloader and feed workflows; upload door | Disable workflow | Yes |
| Broker accounts | `brokers` / `connections` settings; cTrader sign-in; keys via `PUT /api/keys/{name}` | Settings | Yes |
| MCP servers | `mcp_servers` settings section | Same | Yes |
| Rules (always/never allow) | `rules` settings, `[claude]` hooks | Same | Yes |
| Library item kinds | Schema files in `qmx_library/kinds/` (code change) | Code change | Not by him at runtime |
| Units, blocks, dictionary entries | Copilot and dictionary doors | Archive / retire | Yes |

**The UI must never hard-code:**
- the list of mini apps, their operations, or their screens;
- Library kinds, shelves or card fields (render from the schemas; UIH §4);
- step kinds, trigger kinds, templates or their slots;
- provider and model lists, roles or accounts;
- places and machines (only `pc` is fixed);
- connect-dialog kinds and their `needs` cards;
- settings sections and fields;
- tool sets and skills;
- inbox actions (render the closed set the item carries);
- the count of anything.

---

## 7. Open or contradictory points

1. **Workflows as plugins.**
   - His summary (`refs/his-words.md:12`, "workflows are technically now Claude plugins") says workflows are Claude plugins.
   - Spine AD-2 and AD-5 and the code say workflows are engine documents and Claude's Workflow tool is retired (`registry.py:95`). Only packs and apps are plugins (G02 §0).
2. **Lab tools for agents.**
   - INV SHIPPED §10 and §1 say "the `lab` toolset" works.
   - In code every Lab row is `agent=False` with no REST route (CAT:805-893). `lab` is still listed in CORE_TOOLSETS, but it has no agent operations.
3. **@ references.**
   - INV SHIPPED §9 says "Context references with `@` (#143)".
   - G01 and UIH §18 say: `context_add` is model-only, there is no attach-on-click route, and `@file/@folder/@url/@youtube` are refused until REF2.
4. **Session home on create.**
   - UIH §1 row 2 says `home` is sent in the `POST /api/chats` body and returned by `GET /api/chats`.
   - Code: `NewChatIn` forbids extra fields and has no `home` (HR:134-141), and `chat_entry` does not return it (HR:229-237).
5. **Words for machines.**
   - UIH §17 row 14 says "trading server" for where bots trade, "worker" for step machines, and "node" only for a workflow step.
   - UNU §0 says "Trading node" names the trading app, "Connect a server" names the QMX server, and there are no machine kinds on screens. UNU is newer (31 Oct).
6. **Inbox shape.**
   - The backend inbox is a list with closed actions (CS:2380).
   - The 10-16 ruling says notifications are UI-side (UIH §8).
   - His 11-09 verdict says the inbox "must be agentic" (trace §1). No agentic inbox exists in code.
7. **Lab design.**
   - The Lab spine (UIH §5) has Graph/Code projections, `lab.*`/`qmb.*` node packs and pods.
   - The code has none of these. G02 recommends project → subject → run a procedure → compare.
   - He said on 11-09 to "keep the old Lab's project journey" (trace §5).
8. **Bots versus units.** The `bot`, `bot-card` and `strategy` kinds remain beside `unit` (`kinds/`). Ruling 138 says "units not bots". Which shelves to show is open.
9. **Placement for backtests.** UIH §5 says backtests run on the `qmb` machine. Local-first (PR #208, rulings 140-144) makes `pc` the default. UNU §9 shows "where it ran" per run.
10. **Templates count.** The docstring says 31 and UIH says 32. There are 55 catalog rows in code (G02 §1).
11. **Todo / plan blocks.** QMX maps TodoWrite and Task tools to `plan` blocks. On Opus 5.5 those tools are off unless opted in, so a plan panel may never fill (G03; not tested live).
12. **Backups UI.** UIH §24 says wait for the "sync to my account" redesign. Routes for restore, check and carry-on now exist (G01). The design target is unclear.
13. **Getting started and one-click app enables on the first-start card** (UNU §1): no backend (plan, not verified in code).
14. **Orchestrator**: an operator wish only. No plan document defines it beyond backlog B35 and the delegate `orchestrator` role in the spine.
