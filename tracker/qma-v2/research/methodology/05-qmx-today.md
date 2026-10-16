> STATUS 2026-10-16 (rubric walk): PARTLY-STALE. See 27-rubric-walk.md. Rulings in 26 win.

# 05 — What QMX has today (ground truth for the methodology, organogram and workflow designs)

Research date: 2026-10-16. Read-only study of the code and plans. Nothing was changed except adding this file.

## How to read the citations

- **Harness and backend code** is read from branch `qma/hp17`, the top of the stacked QMA v2 PRs (#81-#90, not yet merged into `rebuild/base`). Citations look like `hp17:qmx-agents/packages/qmx-apps/src/qmx_apps/manifest.py:84`. `origin/rebuild/base` itself still stops at HP0 (`3618f198`, PR #71).
- **UI** is read from the worktree `C:\Users\Mubarak\Desktop\QMX-worktrees\ui-review-repair` (branch `ui-review/repair`, head `eea09941`). Citations look like `ui:apps/qmx-ui/src/lib/lab/catalog.ts:84`.
- **Plan** is `D:\QMX-worktrees\agent-system\tracker\` (branch `plan/agent-system`). Citations look like `plan:qma-v2/BACKLOG.md:83`.
- **Main repo** (`C:\Users\Mubarak\Desktop\QMX`, branch `main`) is cited as `main:docs/...`.
- "Deleted in D1/D3" means the code exists at `hp17` but the approved deletion program removes it after the operator signs off HP17 (`plan:qma-v2/DELETION-PLAN.md:70-95`, `:183-200`).

One fact shapes everything below: **QMX has a running agent harness and a running mini-app runtime, but no workflow engine that survives the deletion, no session "home", and no backend for the Lab's or Portfolio's own layer.** The UI shows all of these, on demo data only.

---

## 1. Mini apps

### What a mini app is today

- A mini app is a folder with `app.toml`, `pyproject.toml`, `uv.lock` and an MCP server script. The hash of all its source and lock bytes is its identity. Changed content under the same id and version is refused; you publish a new version instead (`hp17:qmx-agents/packages/qmx-apps/README.md:3-8`).
- The manifest (`hp17:.../qmx_apps/manifest.py:54-99`) declares:
  - `risk`: `shows | runs | money`;
  - `kind`: `screens | headless | both`;
  - `entrypoints`: `mcp` (required), `jobs`, `agents`, `workflows`, `ui`;
  - `capabilities`: `network` allow-list, `secrets` (mapped to `qmx/<name>` keyring entries), `data_reads`;
  - `schedule.interval_seconds`, `budget` (runs, CPU seconds, memory, CPU percent), `breaker` (max errors, heartbeat timeout);
  - `provides` and `feeds`: JSON Schemas for artifacts it produces and consumes.
- Trust levels are `first_party | operator | reviewed | agent` (`manifest.py:18`). The default is `agent`, which **refuses local (T1) install** until review, or runs in Docker at T2 (`README.md:13-15`, `:74-90`).
- Four example apps exist: `exchange-status`, `macro-daily-bias`, `mql5-articles`, `weekend-watcher` (`hp17:examples/apps/`). `macro-daily-bias/app.toml:1-34` shows the full shape: an MCP server, a daily job, an agent spec, a `ui/view.html`, a schedule, secrets and a `provides.bias` schema.

### The runtime (`qmx_apps`)

- `Supervisor` (`hp17:.../qmx_apps/supervisor.py:96`) installs (`:131`), starts (`:340`), stops, restarts, calls tools (`:715`) and reads MCP resources on real subprocesses. Each app owns a volume `<qmx_home>/apps/<id>` with `app.db`, optional agent `memory.db`, `data/`, `blobs/`, `logs/` (`README.md:17-24`).
- Limits: Windows Job Objects (memory, CPU percent, tree kill) or Linux rlimits; heartbeats meter CPU, RSS, runs and errors; a breach trips the breaker and stops the tree (`README.md:43-55`).
- Apps pass data only by **artifact reference**: the producer returns `{"output": name, "data": ...}`, the host validates and hashes it, and the consumer gets an immutable copy in its own volume (`README.md:57-64`; `hp17:.../qmx_apps/artifacts.py:43`, `:74`).
- `DockerSupervisor` runs the same definitions at T2 with a read-only root, dropped capabilities, and a Squid egress allow-list (`README.md:74-90`).
- Backup, snapshot and Litestream replication exist (`README.md:92-107`).

### The road to live

- Stages are `build → tests → sandbox → shadow → live` (`hp17:.../qmx_apps/road/models.py:14-15`). Each stage writes immutable evidence; `advance` runs the next stage (`road/__init__.py:77`); `publish` activates proven code with compare-and-swap and risk rules (`:180`), and rollback is a new evidenced transition.
- This matches the UI lane's "QMX's own CI" proposal (`ui:apps/qmx-ui/handoff/MINI-APPS-AND-COPILOT-CONTRACT.md:105-113`).

### The control door (how anyone drives apps)

`qmx-control` exposes one REST and MCP door (`hp17:.../qmx_control/server.py:29-46`): `apps_list`, `apps_registry`, `apps_get`, `apps_create` (install from a local folder path), `apps_update` (new immutable version), `apps_versions`, `apps_test` (next road stage), `apps_publish`, `apps_rollback`, `apps_start/stop/restart`, `apps_call`, `apps_resource`, `apps_logs`, `apps_evidence`, `apps_backup`, `apps_restore`. The service methods are at `hp17:.../qmx_control/service.py:685-791`.

### Who creates, builds, maintains, edits, publishes and deletes them

| Step | Today | After D1 |
|---|---|---|
| Create / build | The LangGraph copilot delegates to an `app-builder` sub-agent (`hp17:.../qmx_agents/agents/copilot.yaml:7-11`, `app-builder.yaml:1-8`) or the `overnight-builder` background task. Its prompt is four lines: create immutable definitions, test, inspect evidence, request publication (`app-builder.md:1-4`). A live script `scripts/live/copilot_build_app.py` drives it. | Ported to `qmx-agents/plugin/agents/app-builder.md` and `overnight-builder.md` (`plan:qma-v2/DELETION-PLAN.md:76`). The LangGraph runtime and the live script are deleted (`:81-82`). |
| Skills | `build-mini-app`, `build-workflow` and `debug-app` exist but are **empty placeholders**: "Pending authoring" (`hp17:.../qmx_agents/skills/build-mini-app/SKILL.md:1-5`). | Ported as-is into the plugin (`DELETION-PLAN.md:77`). Still empty. |
| Edit | Write files in a folder, then `apps_update` with the expected hash (`service.py:697-703`). | Same, through `mcp__qmx__apps_update`. |
| Test / publish / start | `apps_test` and `apps_publish` / `apps_start` behind LangGraph `interrupt_on` approvals (`copilot.yaml:12`). | All are `MANAGE` in the harness: **always ask** (`hp17:.../qma/harness/tools.py:55-90`, table at `:115-170`). `apps_test` is forced to `auto_publish=False` for agents, so a test can never publish by itself (`tools.py:186-190`). |
| Install trust | The caller passes `trust`; the API default is `agent` (`service.py:693`). | Unchanged. No approval record sets trust yet (the rev-1 architecture wanted it host-assigned, `git show 00a1d1b5:tracker/qma-v2/ARCHITECTURE.md:662`). |
| Delete / uninstall | **No route and no method.** The supervisor has no uninstall, and the control door has no `apps_delete` (`server.py:29-46`; nothing in `supervisor.py`). | Unchanged. |
| Scripts | `mql5-articles` and `weekend-watcher` run on schedules inside the runtime. `macro-daily-bias` and `weekend-watcher` embed the old LangGraph agent, pinned by git commit, and keep running old code until new versions go through the road (`DELETION-PLAN.md:89`). | Same. |

### The mini-app SDK

There are two halves, and neither is a written SDK.

- **Backend half:** the manifest format, the MCP server convention, `provides/feeds` schemas and the `run()` job convention (`README.md:55`). No Python helper library, template or `qmx new-app` scaffold exists.
- **Screen half:** the UI ships a "tier 1" panel description, a flat JSON element map drawn only from QMX's catalog (Stack, Grid, Heading, Text, Metric, Table, LineChart, Badge, Callout, Button), with a validator (`ui:apps/qmx-ui/handoff/MINI-APPS-AND-COPILOT-CONTRACT.md:21-54`; `ui:apps/qmx-ui/src/lib/sdk/spec.ts`, `SpecView.svelte`). The copilot's "draft panel → keep / throw away / pin to a Lab tile" exists in the demo only (`CONTRACT.md:80-91`; `ui:.../lib/sdk/pinned.svelte.ts`). Tier 2 (sealed MCP-Apps-style iframe) and tier 3 (reviewed in-window plugin code) are not built (`CONTRACT.md:23-27`). json-render was never installed (`ui:apps/qmx-ui/handoff/research/session-review.md:167`). The example apps' `ui/view.html` is a separate, unconnected convention.

### What the backlog says

- **B23** mini-app creation design: how they are created, built, maintained and edited; they become plugins any copilot can load; no app gets its own copilot; publish and install only when he invokes them or a rule allows (`plan:qma-v2/BACKLOG.md:52`).
- **B16** MCP apps: discussed in the UI session, never designed (`BACKLOG.md:53`). The storyboard says MCP Apps is where a mini app's copilot gets its own permissions and tools (Excalidraw text, section 3 below).
- **B31** plugins for Lab and Portfolio: a plugin is tools/MCP + skills + model + hooks; a session can load one by default (`BACKLOG.md:49`).
- **B42** make the backend and database usable by agents, and check if the runtime needs a refactor (`BACKLOG.md:117`).
- UI ruling R3: mini apps will be redesigned; "many apps were not meant to be just like VS Code style extensions" (`ui:apps/qmx-ui/UI-BACKLOG.md:30-31`).

### Gaps

1. No delete or uninstall, and no "disable".
2. Skills for building, editing and debugging apps are empty.
3. "Mini apps become plugins" (B23) has no mechanism. The harness loads **exactly one** plugin, the shipped QMX plugin, and refuses to launch if its SHA-256 differs from a constant in code (`hp17:.../qma/harness/home.py:70-105`; `launch.py:409`). A mini app cannot contribute skills, agents or hooks to a chat without a harness change.
4. Apps declare `entrypoints.agents` and `entrypoints.workflows`, but the agent format they use is the LangGraph spec that D1 deletes, and nothing runs `workflows` entries.
5. No trust-from-approval: the caller still names the trust level.
6. No mini-app SDK document, scaffold or template, and the screen catalog is UI-only (no server-side validator, no data binding).

---

## 2. The Lab

### What the UI shows (all demo data)

- The Lab merges Authoring, Backtest lab and ML Studio into one permanent page (operator, 2026-10-02; `ui:apps/qmx-ui/UI-BACKLOG.md:358`). Two benches: **Strategies** (Build, Test, Train, Compare) and **Pods** (Design, Test, Paper) (`ui:.../routes/lab/+page.svelte:63-66`; `lib/lab/lab.svelte.ts:23-142`).
- 28 tile panels (`ui:.../lib/lab/catalog.ts:72-234`): Resources, Toolbox, Editor, Inspector, Runs, Sweep grid, Equity, Robustness, Compare, Training, Model slots, Data, Compute, Agents, Pod, Block, Size trail, Drawdown fan, Stress board, Interventions, Pod equity, Pod resources, Head to head, Paper run, Live decisions, Ready for live?, Log, Pinned by the copilot.
- **Node editor:** `EditorPanel.svelte` has three modes of the same subject, Graph (an `@xyflow/svelte` canvas), Code (CodeMirror) and Import (Claude Code / Codex work, notebooks, ONNX). "Drafts never run; only published versions do" (`ui:.../lib/lab/panels/EditorPanel.svelte:1-7`, `:37`). It renders `DEMO_STEPS` only.
- **Notebooks:** only as an import mode. No notebook runner or notebook panel.
- **Scenario generator** (pairs, timeframes, pair trading, parameters, measures), **machine picker** (switch the Lab to a machine, VS Code remote style), **Start something new** (a copilot-led question flow that ends in a saved layout and can be kept as a template), and **guided walks** (`ui:.../lib/lab/ScenarioDialog.svelte`, `MachinePicker.svelte`, `StartDialog.svelte:1-7`, `guides.ts:1-6`).
- **Lab copilot context:** its own tool list (`qmb.backtest`, `qmb.sweep`, `qmb.walk_forward`, `qmb.robustness`, `qmb.optimize`, training, panels, placement), targets and attachments (`ui:.../lib/lab/copilot.ts:1-40`). These tool ids are UI names; none maps to a backend tool.

### What the operator asked of the Lab (transcripts, storyboard)

- One Lab for "experiment, test, prove in paper, then live"; some work needs a node editor, some code, some neither; bring in work built elsewhere (`UI-BACKLOG.md:539`).
- Models as first-class objects with slots (entry, sizing, regime, risk throttle); any compute provider; saved tests, reports, datasets and feature sets as reusable items; agents and sub-agent swarms in workflows, with where each runs (`ui:apps/qmx-ui/BACKEND-REQUIREMENTS.md:73-82`). Panel-by-panel backend needs are tabled at `BACKEND-REQUIREMENTS.md:84-99`.
- He now prefers graphs and loops to an n8n-style node editor; cron jobs belong to workflows; a daily decay-spotting workflow (old WF3) lives under the Lab (`UI-BACKLOG.md:39-40`).
- Open in the backlog: genetic algorithms, editor run state and copilot editing the graph, agents shown live, robustness from workflows, custom workflows as first-class objects (`UI-BACKLOG.md:333-353`).

### The node-editor zip and design

- The zip is `C:\Users\Mubarak\Downloads\Explore-Node-Editor-Architecture.zip` (a ChatGPT conversation of 2026-09-17, 1,238 lines, 8 operator turns). Unpacked at `main:workroom/research/2026-09-18_node-editor-architecture/explore-conversation/Explore-Node-Editor-Architecture.md`, with reference recon (LSE, OpenBB, Taskade) beside it.
- It was read in full on 2026-10-12 in `plan:agent-system/research/21-miniapps-and-workflows-seeds.md` (62 seeds S01-S62, 43 operator positions at `:389-431`, a 30-item complexity list at `:435-466`, 16 open questions at `:470-488`).
- Grok turned it into the "Workflows construction kit" sitting, absorbed as `main:docs/decisions/ADR-0024-workflows-construction-kit.md` (status ratified for docs only; its AD-23..31 were "repairs required; not ratified", `:28`). It keeps four layers distinct: Experimentation Board layout (client-only), Graph Template (authored versioned DAG), Task Graph (one run's projection), and ungoverned library calls (`ADR-0024:44`).

### What the backend has for the Lab

| Need | Backend today |
|---|---|
| Backtests | QMB, a large library with CLI, API and MCP doors (`hp17:qmb/src/qmb`, `qmb/examples/*_usage.py`: sweeps, optimize, walk-forward, robustness, synthetic data, significance gates). Agents reach it only through `run_backtest(config_ref)`, which **refuses any config the host did not pre-register** (`hp17:.../qmx_tools/service.py:201-206`). There is no agent tool for sweep, optimize, walk-forward or robustness. |
| Run index and remote runs | `runs_list/get/status/logs/fetch/resume/stop`, `runs_start_remote`, `run_job` (`server.py:51-65`); `qmx-remote` providers (ssh, amp, modal, e2b, partly stubbed) and a worker that runs workflows, agents, jobs and apps remotely (`hp17:.../qmx_remote/worker.py:137-279`). D1 stubs `execute_agent` and `execute_workflow` (`DELETION-PLAN.md:80`). |
| Experiment notebook | `qmx_ledger.experiments`: an append-only notebook keyed by run and app (`hp17:.../qmx_ledger/experiments.py:1-30`). Not exposed as a tool. |
| Workflow graphs (node editor) | `qmx_agents.workflows`: a `workflow.v1` JSON schema with 10 node kinds (python, agent, tool, app_call, condition, parallel, join, loop, human_gate, subworkflow), typed ports, cardinality, checkpointed runs on LangGraph (`hp17:.../qmx_agents/workflows/README.md:1-77`; `models.py:11-22`). **Deleted in D1** (`plan:qma-v2/research/one-engine/architect/DESIGN.md:419`). The control door's `workflows_get/put/validate/run` were never wired: they return 501 "requires P10" (`service.py:916-930`). |
| ML runs, models, slots, training | None. No model object exists (`BACKEND-REQUIREMENTS.md:68`, `:76`). |
| Notebooks | None. |
| Pods, pod tests, paper per pod, run together | None. "The engines exist; the layer the screens show does not" (`UI-BACKLOG.md:19`). Operator ruled 2026-10-14 that this layer is designed during actual coding, not in a separate session (memory `qmx-ui-rebuild.md:36`). |
| Experimentation Board object | None, by design: docs keep it client-only (`main:docs/glossary.md:356-358`). |

---

## 3. The storyboard ("vibe coding for trading strategies")

Two different things carry the name. Both matter.

### a. The idea he means today: the Experimentation Board

- In his words on 2026-10-16: "storyboard is something where I tried to come up in QMX with ... vibe coding, but for trading strategies", which "means we need to ground ourselves with methodologies" (parent session `5efecf49`, operator message at 2026-10-16T07:01Z).
- Its origin is the node-editor transcript, 2026-09-17: workflows "would have acted more like a storyboard"; "the one whereby I have an assistant to help me create workflows because that's a storyboard idea ... you dump stuff, then after dumping stuff, you kinda like use that for inspiration" (`Explore-Node-Editor-Architecture.md`, L198). He renamed it the **Experimentation Board** because QMA has research staff (L316), and said it "should be messy" (L1070). Summary in `plan:agent-system/research/21-miniapps-and-workflows-seeds.md:31`, `:42`, `:121-124`, `:393`, `:397-398`.
- What it does, as described: charts, questions, notes and unfinished pieces sit next to runnable parts. "Run" has a scope: one step, a connected section, or a defined procedure. The assistant does most of the building while he talks; he can build too. Only a tested method is promoted: experiment → tested method → workflow or template → optional mini app (`21-seeds.md:121-124`, `:42`, `:398`).
- Where it stands:
  - Docs: a client-only layout alias that writes nothing durable and is never a registry kind (`main:docs/glossary.md:356-358`; `main:docs/decisions/ADR-0022-workbench-expansion.md:114`; `ADR-0024:44`).
  - UI: it became the Lab tiling workbench plus "Start something new" and the guided walks (`21-seeds.md:124`; `ui:.../lib/lab/StartDialog.svelte:1-7`). No board of mixed notes, charts and runnable steps exists.
  - Backend: no board object, no drafts, no "run this section" (`21-seeds.md:124`, open question 2 at `:473`). Run scope was designed once (`Runner.run_scope`, one node / a section / all, marked NEXT) and dropped by later revisions (`git show 00a1d1b5:tracker/qma-v2/ARCHITECTURE.md:517`).
- The methodology study already linked it to BMad's human taste gates (`plan:qma-v2/research/methodology/01-bmad.md:252`) and to a Pocock-style strategy pipeline (`02-pocock-pstack.md:251`).

### b. The UI storyboard (the design board)

- `C:\Users\Mubarak\Documents\brain\brain\Excalidraw\qmx-ui-storyboard.md` (Obsidian Excalidraw, 141 elements, dictated 2026-09-22). It is the spec the UI was rebuilt from on 2026-10-01 (memory `qmx-ui-rebuild.md`; `UI-BACKLOG.md:432`, `:492`).
- What it says that matters here: a main copilot with "more tools, more access, almost everything" that can open single mini apps, widgets and workflows; a mini-app copilot with "different permissions and tools ... This is where MCP apps configuration comes into play"; JSON render for widgets; a preview pane that is "an agentic browser" for mini apps, workflows, strategy cards, code, diffs and a terminal, but "not where we design or make workflows from"; a mini app is "a composition of widgets and workflows"; the node editor is not designed yet (storyboard text elements `rrUMAlEq`, `JHZj5SdT`).
- Reading notes: `main:workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/storyboard-reading.md:1-65`. Lost ideas from it (json-render, MCP Apps renderer, preview pane as agentic browser, preview-to-Library, per-app settings, a mini-app SDK) are listed at `ui:apps/qmx-ui/handoff/research/session-review.md:213-220`.

---

## 4. Library / Strats: data model and storage

The Library is named **Strats** (`plan:qma-v2/BACKLOG.md:113`, out of this backlog: own session). Today strategy knowledge is spread over five stores. All of it is structured and parseable without an LLM.

| Store | What it holds | Fields a parser can read |
|---|---|---|
| **Control Library** `<home>/library.db` + `artifacts/<sha256>` (`hp17:.../qmx_control/library.py:26-45`) | Every saved item: Firecrawl reads (kind `article`, `hp17:.../qmx_agents/research.py:170-193`), backtest results (kind `backtest`, `qmx_tools/service.py:201-240`), MQL5 articles from the scraper app. | `id, kind, title, tags, source, created, root_id, version, previous_id, sha256, size, ref, fetched_date` (`library.py:112-126`); full-text index over title, tags, text (`:41`); `links(source, target, relation)` with free-text relations (`:42-43`, `:226-237`); `memo` keyed by `strategy_version, data_snapshot, params, engine_version` (`models.py:30`, `library.py:249`). |
| **QMF registry** (per-world registry room: SQLite metadata + JSONL lineage) (`hp17:packages/qmf-registry/README.md`) | Registered records by kind: `bot-definition` (CT-33), `confluence` (CT-34), `strategy-family` (CT-06), `book-definition` (CT-22), `bms-definition` (CT-27), `book-binding` (CT-28), `split-manifest` (CT-12), `source-observation` (CT-10), `performance-result` (CT-32), `experiment-spec` (`hp17:qmb/src/qmb/registryread/library.py:78-90`). | fp1 identity, kind, at-birth parent refs, writer, sequence. **Typed lineage edges**, a closed set of 14: `supersedes, promoted-from, occurrence-of, corroborates, disagrees-with, confirmed-as, confirmation, invalidation, interaction, out-of-sequence, continues-performance, carries-ledger, enacts, branches-from` (`hp17:packages/qmf-registry/src/qmf/registry/lineage.py:104-134`). |
| **Bot definitions** (CT-33) | The declaration half of a strategy. | `strategy_family_id`, `confluence_set`, `parameter_space` (name, type, bounds, step, default, unit-kind), `footprint.stream_set` (instruments, bar specs), `required_calendars`, `producer_bindings` (indicators), `permitted_exit_intents`, `logic_reference` (code distribution + source-manifest hash), `version_graph` (`main:docs/contracts/ct-33-bot-definition.yaml:49-63`). |
| **QMB ledger** (orchestrator-written JSONL) | One line per run. | `run_id, role (trial/confirmation/replicate/aborted), world, result_label, book_bar_fp1, measures, ct32_fingerprint, refusal, sweep_coordinates, workbench_lane, trial_label` (`hp17:qmb/src/qmb/ledger/line.py:130-144`). No pass/fail verdict is stored (`:131`). |
| **Apps and runs** | App definitions, road evidence, artifacts with producer and consumer schemas, run journals, experiment notebook. | `provides/feeds` schemas (`manifest.py:98-99`), artifact refs with producer and content hash (`artifacts.py:21-74`), road evidence records (`road/__init__.py:48-60`), `qmx_ledger` journals and experiment entries. |

What a knowledge graph could be built from by parsing alone:
- **Nodes:** family, bot version, confluence, indicator/producer, instrument and timeframe, calendar, dataset split, backtest run, performance result, experiment spec, Library item, app, artifact, article.
- **Edges:** CT-07 lineage (14 typed relations), bot → family, bot → confluences → producers, bot → instruments, run → bot version (via `book_bar_fp1` and resolved config), run → measures, memo key → backtest item, Library `links`, artifact producer → consumer, article source URL.
- The UI already draws "where an item is used" across Lab, Portfolio, Copilot, Home and Mini apps (`ui:.../lib/library/ConnectionsMap.svelte:1-40`) and has 15 shelves: bots, models, workflows, pods, blocks, apps, templates, reports, paper, scenarios, setups, datasets, files, articles, sources (`ui:.../lib/library/items.ts:66-81`). All demo.

Gaps: the five stores are not joined; the Library's `links.relation` is free text, not the CT-07 vocabulary; agents cannot read the QMF registry or QMB ledger through any tool (only `library_search/get/versions/links` and `compare_runs`); "models", "workflows", "pods", "scenarios", "reports" have no backend kind (`BACKEND-REQUIREMENTS.md:80`).

---

## 5. Portfolio

### UI (demo data)

- Layouts: Overview, Pods, Live, Road to live, MIS (`ui:.../lib/portfolio/portfolio.svelte.ts:10-70`). Panels: accounts, positions, holdings, exposure, correlation, events, bot charts, journal, nodes (trading servers), pods, pod detail, road to live, signing (promotion card), MIS, control (`ui:.../lib/portfolio/panels/`). Kill switch grid in the header (`ui:.../lib/portfolio/KillMatrix.svelte`). Pod templates (`TemplatesDialog.svelte`).
- Portfolio copilot tools in the UI: `pod.bring_from_lab`, `pod.draft_version`, `pod.from_template`, `promotion.prepare_card`, `journal.summarise`, `risk.explain`, `news.watch`; targets PM, trader, pod, account, Lab, event (`ui:.../lib/portfolio/copilot.ts:14-99`). None exist in the backend.
- Rulings: the trading node folds into Portfolio as a Live section; Portfolio is "mostly watching"; Allocate and agent requests moved out; every pod has a live and a paper side (`UI-BACKLOG.md:395-403`; memory `qmx-ui-rebuild.md`). Open: wire a Lab-built pod or workflow into Portfolio (`UI-BACKLOG.md:386`).

### Backend

- **Broker reads:** `qmx-broker` MCP exposes `list_accounts, account_state, positions, quotes, symbol_info, bars` and one writer, `propose_order`, which only saves an **unsigned** proposal and never opens a broker connection (`hp17:.../qmx_broker/server.py:1`, `:12-67`; `service.py:164-188`).
- **Control:** `portfolio_proposals` lists those unsigned proposals for his signature (`service.py:332-334`). That is the only Portfolio operation on the door.
- **Harness:** broker reads are `READ`; `propose_order` is `PROPOSE_MONEY` and always asks; there is no `Effect` member for moving money (`tools.py:55-73`). The QMX plugin's first rule is "Money is read-only" (`hp17:qmx-agents/plugin/QMX.md`).
- **QMN** (the trading node) has paper, promotion, protection, reconcile, seats, MIS and capital modules (`hp17:qmn/src/qmn/`), but the UI has no read model or powers path to it (`BACKEND-REQUIREMENTS.md:112`).
- The risk-and-sizing redesign is unsettled ("are we still using books?"), so pods may change (`UI-BACKLOG.md:36-37`).

So today a Portfolio copilot could read accounts and positions and draft an unsigned proposal. Nothing else it shows in the UI is backed.

---

## 6. Copilot and sessions

### Before QMA v2 (still in the code at `hp17`, deleted in D1)

- `qmx_agents` built one LangGraph/Deep Agents copilot from YAML specs: `copilot.yaml` with sub-agents `researcher`, `data-analyst`, `app-builder`, one background task `overnight-builder`, MCP servers `qmx-control, qmx-data, qmx-backtest, qmx-research, qmx-broker`, approvals on `apps_publish` and `apps_start`, and a budget of 200 model and 400 tool calls (`hp17:.../qmx_agents/agents/copilot.yaml:1-16`).
- `tasks.py` gave the copilot four tools, `start_task`, `check_task`, `cancel_task`, `list_tasks`. Each start created a child control session (`parent_id`), ran the named spec as an asyncio task with its own SQLite LangGraph checkpointer and run journal, and recorded `running → completed | needs_you | failed | cancelled` (`hp17:.../qmx_agents/tasks.py:21-151`).
- `research.py` saved every successful Firecrawl page into the Library automatically (`research.py:1-60`).
- Workflow graphs ran on LangGraph (`workflows/`), and `as_subagent(spec)` exposed a workflow as a Deep Agents sub-agent (`workflows/README.md:68-72`).
- Memory: `memory.py` with scopes (session, task, workflow, global), SQLite under `copilot/memory.db` or `apps/<id>/memory.db`, global writes needing approval (`hp17:.../qmx-agents/README.md:68-80`).

### QMA v2 (the harness that replaces it)

- A chat **is** Claude Code launched by QMX with its own home, settings in code, one QMX plugin, and QMX's MCP tools (`plan:qma-v2/research/one-engine/architect/DESIGN.md:23`, `:206-212`).
- `Harness.start_chat(NewChat)` creates a control session with `origin="qma"` and a chat record; the chat runs in a **workspace folder** (a fresh one under `<home>/workspaces/<id>` if none is given) (`hp17:.../qma/harness/harness.py:150-160`, `:298-332`).
- Chat kinds: `Interactive` (asks reach him), `Background` ("started without the operator present, such as a scheduled news scan"), `Child` (started by `delegate`, unattended copied from the parent, no Agent tool, no delegate) (`hp17:.../qma/harness/launch.py:61-84`).
- Instructions per chat: `QMX.md`, then the workspace's `CLAUDE.md` and `AGENTS.md` (`launch.py:314-322`). Auto memory per workspace under `<home>/agent-memory/<workspace>/` (`home.py:14`, `:145-155`, `:442`).
- REST: `POST /api/chats`, `GET /api/chats`, `POST /api/sessions/{sid}/turns`, `/interrupt`, `/quote` and `/apply` (model, provider, effort switch with cost warning), `/export`, `/rewind`, `GET /api/sessions/{sid}/live` (SSE), `POST /api/approvals/{ask_id}`, `/api/usage`, `/api/doctor`, `/api/claude-settings` (`hp17:.../qma/harness/routes.py:263-427`).
- What the UI copilot page shows (sessions with an origin `Main | Lab | Portfolio | Library | Mini apps`, moving a session into Main keeps history, typed blocks, activity feed) is demo only (`ui:.../lib/copilot/demo.ts:11`; `store.svelte.ts:79-97`; `BACKEND-REQUIREMENTS.md:150-156`).

### Removed or replaced

| Old | QMA v2 |
|---|---|
| LangGraph copilot graph, Deep Agents sub-agents | Claude Code native sub-agents from the plugin's `agents/*.md` (ported in D1) |
| `start_task` background tasks | `Background` chats (Python API only) and `delegate` |
| LangGraph `interrupt_on` approvals | Claude permission rules and modes, plus QMX's effect table (`tools.py:82-90`) answered at `POST /api/approvals/{ask_id}` |
| Workflow compiler and runs | **Nothing.** The Claude Code Workflow tool is off by default (`DESIGN.md:285`) |
| Memory scopes and SQLite memory | Claude Code auto memory per workspace; the pluggable layer is backlog B40 |
| Research middleware (auto-save Firecrawl) | Nothing yet |
| WF1/WF2 | Never built; "dead in docs" (memory `qmx-ui-rebuild.md`), and backlog B10 is his to restart |

### Hook points QMA v2 offers for workflows

1. **Background chats (HP11).** `Background` kind: verbatim prompts, turn and spend limits from `settings.toml [budgets]`, refused at the background cap (default 50% of the 5-hour window), unattended asks expire after `unattended_ask_seconds`, interrupted with a `needs_you` block at the plan hard stop (`plan:qma-v2/HARNESS-PLAN.md:699-750`; `harness.py:334-366`). **Limit:** the REST route cannot create one; `NewChatIn` has no `kind` field (`routes.py:130-137`, `:263-277`). There is no scheduler or trigger that starts one.
2. **Delegation (HP13).** `mcp__qmx__delegate({profile, prompt})` starts a `Child` chat on another provider in the same workspace, sends the prompt as untrusted text, waits, and returns the final text. Allow-list of profiles, refused at once when the chat table is full, depth 1 (`harness.py:401-445`; `HARNESS-PLAN.md:802-850`). It is synchronous: no job handle, no later collection.
3. **Approvals (HP9).** Asks become `permission` blocks; answers are `allow_once | allow_always | reject_once | reject_always | cancel`; a second answer is `already_answered`; after restart it is `expired` (`HARNESS-PLAN.md:596-645`; `routes.py:361`). Effects: READ never asks; DOMAIN_WRITE per `[agents] domain_write` (default allow); MANAGE (publish, install, schedule, run, cancel) and PROPOSE_MONEY always ask (`tools.py:55-90`). `workflows_run` and `run_job` are MANAGE (`tools.py:142-158`).
4. **Events.** Durable SSE per topic `runs, jobs, sessions, apps, library, settings, aggregates` with `Last-Event-ID` replay (`hp17:.../qmx_control/server.py:219-232`; `service.py:56`). Session blocks are an append-only list of 14 kinds (`service.py:67-85`). Live deltas per chat on `/live`, never stored (`project.py:177-182`). App runtime events can be forwarded into a session (`service.py:893`). Approvals are not yet their own topic (UI-NOTES asks for it, `plan:qma-v2/UI-NOTES.md:25`).
5. **Claude Code hooks.** Operator hooks ride in `settings.toml [claude] hooks` and run natively (`DESIGN.md:209`, `:285`). Project hooks and `.mcp.json` are off (`DESIGN.md:336`).
6. **Workspace files.** A workspace's `CLAUDE.md` / `AGENTS.md` load into every chat in it (`launch.py:314-322`). This is the only existing way to give a session a "home" context.
7. **Control-door operations** an agent can call: run index, remote runs and jobs, apps, library, settings reads (`tools.py:115-170`).

What is missing for B30 "session homes": a control session has only `title`, `origin` (free string) and `parent_id` (`service.py:60-64`); no home kind, no project id, no filter, and the harness always writes `origin="qma"` (`harness.py:317-319`).

---

## 7. The old workflow and research harness, templates, memory and lessons

### The August/September research harness (Open Research + Delphi)

- Donor study of 2026-09-14: OpenResearch (experiment tree, freeze-after-answer, promote-then-descend, isolated parallel arms), OpenScience (studies, budgets, autoresearch hill-climb), Delphi (indexed retrieval, corpus snapshots, context packs). QMX was to adopt **mechanisms, never the products** (`main:_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-14/inputs/donor-openresearch-family.md:1-40`; `CAPABILITY-EXPANSION.md:47-48`). Delphi was kept only as "a future KnowledgeSource adapter", with pgvector refused.
- What was built: the QMA daemon's Mission / Task Graph / Graph Template / procedures / ExperimentSpec / experiment ledger machinery (`hp17:.../qma-daemon/src/qma/daemon/taskgraph/procedures.py:1-15`, `experiments/`, `ledgers/`), and a `research-corpus` pack whose only graph template is a two-node `search → cite` "survey" (`hp17:.../qma/daemon/bundled_packs/research-corpus/daemon/plugin.py:166-192`). Its `graphs/` and `skills/` folders are empty (`.gitkeep`). The stacked-bush loop itself was never a shipped graph (`donor-openresearch-family.md:34`).
- All of it is **deleted in D3** (`plan:qma-v2/DELETION-PLAN.md:183-190`). The operator said the August harness "may have been overkill" and wants a redesigned one shipped as templates (`plan:agent-system/research/00-session-ledger-2026-10-12.md:136`; BACKLOG B13 at `BACKLOG.md:63`).
- Shipped and kept: the MQL5 scraper app, opt-in Firecrawl (`plan:agent-system/research/27-requirements-from-audit-session.md:336-337`). Planned, never built: a deep-research skill with hard caps (5 researchers, 6 rounds, 10 tool calls), and keeping idea generation apart from narrowing, using technique catalogues as data (`27-requirements:338-339`).

### Workflow templates

- None exist as runnable content. The P10 compiler shipped one recorded example, `ingest-backtest-report.json` (`hp17:.../qmx_agents/workflows/README.md:74-77`), deleted with D1.
- A seed catalogue for built-in templates is in `plan:agent-system/research/22-cookbooks-and-templates.md:311` (section 3). Requested templates: a news and sentiment workflow (`UI-BACKLOG.md:311`), the daily decay-spotting WF3 (`UI-BACKLOG.md:39`), research templates "OpenAI-cookbook style" (B13).

### Memory and lessons designs deleted by architecture revisions (B53)

From revision 1 of the QMA v2 architecture (`git show 00a1d1b5:tracker/qma-v2/ARCHITECTURE.md`, run in `D:\QMX-worktrees\agent-system`):
- **`run_scope`** (line 517): `Runner.run_scope(version, scope)` runs one node, a section, or all, marked NEXT (FR-068). This is the Experimentation Board's "run has a scope" in code form. The same runner had `resume` that skips finished nodes and consults an effects ledger (`:515-516`), gates bound to the graph's content hash (`:520`), and `watch` and `command` node kinds (`:502`, `:522-523`).
- **`lessons`** (line 601): self-improvement as "a `lessons` table of proposals, a weekly mining job, a skill draft as a new plugin version, an eval gate against 'no skill' on `FakeAdapter`, an approval row before activation, undo by the previous plugin hash" (FR-142, FR-037).
- **`trigger_fires`** (line 611, storage table): `triggers` + `trigger_fires` in `control.db`, NEXT. A-08 says "Triggers are rows that start a run, not nodes" (`:687`). Slice planning parked "scheduler and triggers, mailbox and board, variants, self-improvement" (`:750`).
- The same revision kept `workflow.v1` models, schema and validators and planned to replace only the LangGraph compiler (`:656`). Revision 3 dropped the runner entirely; the one-engine DESIGN keeps no workflow engine.

---

## Gaps that block the methodology/workflow design

1. **No workflow engine survives.** The LangGraph compiler and runs are deleted in D1, the control door's `workflows_*` are 501 stubs, and the Claude Workflow tool is off. B33 must pick an engine (own runner over `workflow.v1`, Claude dynamic workflows, or chats-as-steps) before any template, trader agent or WF1/WF2 rework can exist.
2. **No trigger or scheduler for agent work.** `Background` chats exist only as a Python API; no REST route, cron, event trigger or `trigger_fires` record starts one. Mini-app jobs have an interval schedule, but nothing schedules a chat. Scheduling is MANAGE (always asks), and no standing allow-rule format for "this schedule may run" exists.
3. **No session home.** Sessions carry only `origin` and `parent_id`, and the harness always writes `origin="qma"`. The organogram (general copilot, Lab copilot, Portfolio copilot, workflow agents, trader agents) has nothing to key on except a workspace folder and its `CLAUDE.md`.
4. **One fixed plugin.** The harness loads only the shipped QMX plugin and refuses any change to it by SHA-256. Per-home plugins (B31), mini apps as plugins (B23), agent-as-a-folder (B32) and self-improving skills (B41) all need a signed, versioned way to load more than one plugin.
5. **Empty methodology content.** `build-mini-app`, `build-workflow` and `debug-app` are placeholders; agent prompts are four-line stubs; there is no system-prompt design (B29), no Lab or Portfolio skill, and no output methodology.
6. **Delegation is synchronous and shallow.** `delegate` blocks until the child answers, depth is 1, and there is no job handle, mailbox or fan-out. Long research loops, parallel arms and trader agents that run for days (B46) have no primitive.
7. **No Experimentation Board backend.** No board, draft, section, or "run this part" (`run_scope`) exists, and the docs forbid a durable board record. "Vibe coding for trading strategies" needs a decision: a backend object, or Lab layouts plus Library drafts.
8. **Lab backend layer missing.** Agents can run only pre-registered QMB configs; no tools for sweep, optimize, walk-forward or robustness; no model object, slots, training runs, notebooks, pods, pod tests or paper-per-pod. The Lab copilot's UI tool list has no backend twin.
9. **Portfolio has almost nothing to act on.** Broker reads and unsigned proposals only; no pod, risk, MIS, road-to-live or kill-switch read model for agents or the UI. With the risk-and-sizing unit unsettled, the Portfolio copilot's job cannot be pinned down.
10. **Library/Strats is fragmented.** Five stores (control Library, QMF registry, CT-33 bots, QMB ledger, app artifacts and journals) with no join, free-text Library relations, and no agent read path into the registry or ledger. The knowledge graph needs one index over these, and B8 (Strats v2) sits in another session.
11. **No memory or lessons layer.** Workspace auto memory is the only memory; the scoped memory provider is deleted; the `lessons` table, mining job and eval gate exist only in a superseded revision.
12. **Mini-app lifecycle holes.** No delete, uninstall or disable; trust is caller-chosen; app `agents` entries use the deleted LangGraph spec; `workflows` entries run nowhere; no SDK, scaffold or server-side panel catalog; MCP Apps (B16) is undesigned.
13. **Event gaps for a workflow UI.** No `approvals` topic, no run or node event kinds for workflows, and the live kinds the rev-1 design had (`tool.progress`, `terminal.*`, `cursor.*`) are not all back (UI-NOTES section 9).
14. **Research harness reset.** The August machinery (Missions, procedures, ExperimentSpec ledger, survey template) is deleted in D3 with no replacement; the deep-research skill and idea-generation catalogues were never built.
