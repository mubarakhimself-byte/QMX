---
label: wayfinder:research
created: 2026-10-12
builds-on: 02-how-current-agent-runtime.md, 19-two-sdk-study.md (sections 0, 10, 11, 13), 20-qma-v2-direction.md
source: origin/rebuild/base @ 4fa38ffe (P16c PRs #58-#66 merged). The new packages are byte-identical to 1cc46f9c, the snapshot 02 read, so 02's citations still hold.
method: pstack /how then /why, run in one pass by one agent (no sub-agents, per the brief). Planning only. Nothing committed.
---

# 24: How and why. The integration surface QMA v2 plugs into or replaces

## Summary in plain words

1. qmx-control already holds the session log, events and SSE the UI will read. QMA v2 should write into it, not replace it.
2. Nothing runs an agent turn when a message arrives. No route exists to answer an approval. Building both is QMA v2's first job.
3. The workflow API answers 501. No store holds workflow definitions. No bridge runs them from the API.
4. The P10 graph format (`workflow.v1`) is plain Pydantic and JSON Schema. It can become QMA v2's own graph format as it is.
5. The P10 compiler and run API are LangGraph through and through. They are about 500 lines that QMA v2 replaces with its own runner.
6. Mini apps are MCP servers under a supervisor. Agents reach them only through `apps_call`. That contract does not depend on LangChain.
7. The exceptions are agent-bearing apps. They embed `qmx_agents` from a pinned git commit, so they break when that package changes.
8. The guards split cleanly. The journal, experiments, money-path rules and admission gate are pure Python. The LangChain middleware around them is not.
9. The domain tools are plain functions. They are already served as FastMCP servers. One line wraps them for LangChain.
10. qmx-remote already gives a server lane: hashed bundles, a five-second bucket flush, verified fetch and resume elsewhere. It runs agents and workflows through LangGraph.
11. The old qma packages still hold 114,228 source lines. One dead QMB helper keeps most of them importable. No new package imports them.
12. The LangChain move fixed a sprawling home-made runtime by adopting libraries. QMA v2 keeps that discipline but builds its own graph.

## The picture: today and the QMA v2 seams

```
 TODAY (rebuild/base 4fa38ffe)                    QMA v2 SEAMS (what plugs where)
 ------------------------------                   --------------------------------
 UI: no caller of /api/* on any branch            UI reads the same blocks + SSE
   |                                                |
 qmx-control  REST + MCP over one service  <--------+-- KEEP. Add: turn route, approvals
   control.db: sessions | blocks | work | events    |   table, workflow store, plugin and
   runs.db (RunIndex), library.db (out of scope)    |   router settings sections
   workflows_* -> 501                               |
   |  apps_* ------------------------------+        |
 [no turn host] <- scripts/live only        |       [NEW turn host / job runner]
   |                                        |         |  Engine interface (thin)
 qmx_agents.spec.build_agent                |         |-- ClaudeEngine (Agent SDK, plan)
   deepagents + LangGraph + LangChain       |         |-- OpenAIEngine (Agents SDK, any
   router -> CLIProxy :8317                 |         |     OpenAI-compatible endpoint)
   middleware: journal, money, admission,   |         |-- policy lives in QMX tool wrappers
     app hooks, memory, limits, HITL        |         |-- plugins = MCP + skills + model + hooks
   workflows/compiler -> LangGraph          |       [NEW QMA graph runner] over workflow.v1
   tasks.py start_task (asyncio + saver)    |         SQLite checkpoint per node, gates
   |                                        v
 qmx_tools domain functions --FastMCP-->  qmx-apps Supervisor (T1 laptop, T2 Docker)  KEEP
 qmx-broker propose_order only               MCP stdio per app, artifacts by reference
 qmx-remote worker (LangGraph inside) ----> KEEP-REWRAP: worker calls Engine + graph runner
 qma-core/daemon/wire (114k lines) -------> DELETE (P16), harvest native_claude/codex first
```

Path keys used below. `ctl/` is `qmx-agents/packages/qmx-control/src/qmx_control/`. `apps/` is `qmx-agents/packages/qmx-apps/src/qmx_apps/`. `agents/` is `qmx-agents/packages/qmx-agents/src/qmx_agents/`. `tools/` is `qmx-agents/packages/qmx-tools/src/qmx_tools/`. `remote/` is `qmx-agents/packages/qmx-remote/src/qmx_remote/`. Other paths are from the repo root.

---

# Part 1. /how

## 1. qmx-control: the API, the database, sessions and events

### 1.1 One service, two doors
- `OPERATIONS` lists 52 operations. Each row is a name, a verb, a path and a destructive flag (`ctl/server.py:28-81`).
- The same bound methods become REST routes (`server.py:206-213`) and FastMCP tools (`server.py:120-129`). There is no second implementation.
- Each MCP tool carries `meta={"interrupt_on": destructive}` (`server.py:127`). That flag is how an agent host learns which calls need approval today.
- One bearer token from the OS vault protects REST, `/mcp` and SSE (`server.py:84-117`, `237-238`). CORS allows one UI origin, `http://127.0.0.1:5173` (`server.py:144`, `239-251`).
- `POST /api/apps/{app_id}/sign` is the operator-only door. It is never exported as an MCP tool (`server.py:184-196`).
- A background loop refreshes runs and runs the weekly backup every 60 seconds (`server.py:152-165`).

### 1.2 The database
`control.db` is SQLite in WAL mode with four tables (`ctl/service.py:119-128`):

| Table | Key | Holds |
|---|---|---|
| `sessions` | `id` | `{id, title, origin, parent_id}` JSON (`service.py:47-51`, `300-313`) |
| `blocks` | `(session_id, seq)` | append-only typed blocks (`service.py:324-335`) |
| `work` | `(kind, id)` | runs and jobs with status and an in-memory canceller (`service.py:443-471`) |
| `events` | `seq` autoincrement | `(topic, subject, data)` for every change (`service.py:156-169`) |

Beside it sit `runs.db`, a rebuildable index over JSONL journals (`ctl/runs.py:19-53`), `library.db` (Library, out of scope), and `settings.toml` with seven sections (`service.py:40-42`, `200-294`). `settings_put` refuses any key that looks like a secret (`service.py:79-91`, `222`).

### 1.3 Sessions, blocks and events
- `SessionBlock.type` is a closed list of 14 kinds: `user, text, plan, agents, tool, changed, artifact, table, entity, question, permission, panel, handoff, needs_you` (`service.py:54-72`). This list is the UI's contract (`rebuild/research/ui-model-and-baseline-audit.md:162-174`).
- A child session is a session with `parent_id`. Sub-agents use it (`service.py:303-308`).
- `events` serves seven topics: `runs, jobs, sessions, apps, library, settings, aggregates` (`service.py:43`). Changes to runs, jobs, apps or the Library also write an `aggregates` row (`service.py:164-169`).
- `GET /api/events/{topic}` is SSE. It honours `Last-Event-ID` and polls the table every 50 ms (`server.py:215-228`, `service.py:187-198`).

### 1.4 The workflow API
- `workflows_get`, `workflows_put`, `workflows_validate` and `workflows_run` all call `_unavailable`, which raises `not_implemented` with HTTP 501 (`service.py:880-894`, `643-647`).
- `runs_cancel` and `jobs_cancel` also return 501 when no owner registered a canceller (`service.py:604-633`).

### 1.5 What an agent turn would call
A QMA v2 turn host needs these, and all exist:
- `sessions_create` and `sessions_append` to write the log (`service.py:300-335`). `stream_turn` shows the mapping: `write_todos` becomes `plan`, `task` becomes `agents`, an interrupt becomes `permission` (`agents/copilot.py:123-212`).
- `record_work(kind, id, data, cancel=...)` to show a background job in Activity and make it cancellable (`service.py:443-471`).
- `watch_app_events(session_id, hook)` and `notify_app` to hear app breaker trips between turns (`service.py:857-865`).
- `apps_*`, `runs_*` and `settings_*` through the MCP door, as the copilot already does (`agents/copilot.py:66-69`).

It needs these, and none exist:
- a route that starts a turn when a user block arrives (`POST .../blocks` only stores the row, `service.py:324-335`);
- an approvals record and a route to answer it. Today approvals are answered on a script's stdin (`scripts/live/copilot_build_app.py:64-76`);
- a cancel-turn route;
- token-level streaming. The log holds whole messages (`agents/copilot.py:128-130`).

### 1.6 What the UI expects
- No UI code calls `/api/sessions`, `/api/events`, `/api/workflows`, `/api/apps` or `/api/runs` on `rebuild/base` or on `origin/ui-integration` (git grep, both empty). The rebuild UI on `ui-review/repair` is wired later by Claude (`rebuild/README.md:20`).
- The expectations are written down instead. They are one session store for main and per-screen copilots, typed blocks only, sub-agents as child sessions, Activity across agents and jobs with where each runs, and a real terminal (`ui-model-and-baseline-audit.md:158-195`, `228-237`).

**QMA v2 verdict.** KEEP and enhance. QMA v2 adds a turn route, an approvals table, a workflow store, and settings sections for plugins and the router. It keeps the block contract and SSE.

## 2. qmx-apps: the mini-app runtime

### 2.1 Define, build, run, stop
- **Define.** An app is a folder with `app.toml`, `pyproject.toml`, `uv.lock` and an MCP server script (`apps/manifest.py:183-185`). The manifest declares id, version, `risk` (`shows | runs | money`), `kind`, entrypoints (`mcp`, `jobs`, `agents`, `workflows`, `ui`), capabilities, schedule, budget, breaker, `provides` and `feeds` (`manifest.py:54-99`). Secrets must name `qmx/*` vault entries (`manifest.py:173-179`).
- **Build.** The definition hash covers every file (`manifest.py:130-139`). `install` runs `uv sync --locked` into `environments/<hash>`. Agent-authored code is refused at T1 (`qmx-apps/README.md:10-15`).
- **Run.** `start` checks the road's active version, creates the volume, runs migrations, then starts the process and its stdio MCP client (`apps/supervisor.py:340-388`). The environment holds only the volume paths and the declared secrets (`supervisor.py:390-419`).
- **Stop.** `stop`, a run budget, CPU, heartbeat or error breach kill the process tree (`supervisor.py:601-638`; `README.md:53-54`).
- **Docker tier (P17).** `DockerSupervisor` runs the same definitions in a read-only container with dropped capabilities and a Squid egress proxy. The host keeps the MCP session (`apps/docker.py:120-147`; `README.md:74-90`). qmx-control picks T2 when its tier is `T2` (`ctl/service.py:755-789`). The node service starts with `tier="T2"` (`ctl/node.py:158`).

### 2.2 The app SDK
There is no app SDK package. The contract is a convention:
- serve FastMCP over stdio (`examples/apps/weekend-watcher/server.py:17`, `66-67`);
- read the volume from `QMX_VOLUME` (`supervisor.py:404`);
- return `{"output": <provides name>, "data": ...}` to emit an artifact (`supervisor.py:686-692`; `README.md:57-64`);
- expose `ui://` resources for panels (`service.py:751-753`).

An agent-bearing app builds its own Deep Agent in-process. It imports `qmx_agents.spec` and `qmx_agents.router` (`examples/apps/weekend-watcher/server.py:14-15`, `46-55`; `examples/apps/macro-daily-bias/macro_bias.py:21-22`). Its lock pins `qmx-agents` to a git commit (`examples/apps/weekend-watcher/pyproject.toml`, `[tool.uv.sources]`).

### 2.3 How an agent builds an app today (P15)
- The copilot holds the `qmx-control` MCP tools (`agents/agents/copilot.yaml:4`) and an `app-builder` sub-agent (`copilot.yaml:8-11`).
- `AppHooksMiddleware` forces tests before `apps_publish` and runs them after `apps_create` or `apps_update` (`agents/guards/hooks.py:75-108`). It also stops a copilot test from auto-promoting to live (`hooks.py:77-79`).
- `interrupt_on: {apps_publish, apps_start}` pauses for the operator (`copilot.yaml:12`).
- Code runs through a supervised "sandbox app" the operator supplies (`agents/copilot.py:30-51`; PR #47 body).
- Proven with fake models only. The live journey was never run (PR #47, "Found, not fixed").

### 2.4 Storage (P13) and road to live (P14)
- Each app owns `apps/<id>/` with `app.db`, optional `memory.db`, `data/`, `blobs/` and `logs/` (`apps/volume.py:16-51`). One supervisor holds a lease on it (`volume.py:53-77`).
- Backup is a verified snapshot through rclone, with a restore test (`apps/backup.py:122-196`; `ctl/service.py:811-837`).
- The road has five stages: `build, tests, sandbox, shadow, live` (`apps/road/models.py:14-15`). `advance` refuses skips and writes an evidence record per step (`apps/road/__init__.py:77-146`). A passing shadow run auto-publishes unless the app touches money (`road/__init__.py:144-145`). Money apps need the operator's signature (`supervisor.py:354-359`).

### 2.5 The contract between apps, agents and workflows
- **Tools and resources over MCP.** `apps_registry`, `apps_call` and `apps_resource` relay to the running instance (`service.py:728-753`). Every call passes `check_descriptor`, the money-path barrier (`supervisor.py:671`).
- **Artifacts by reference.** A producer's output is schema-checked and stored by hash. A consumer receives only a checked reference and a copy (`supervisor.py:673-675`, `686-692`; `apps/artifacts.py:43-109`). `apps_call` also saves it to the Library (`service.py:732-749`).
- **Events.** Every instance change goes to the `apps` topic and the `jobs` work list (`service.py:839-855`).
- **Workflows.** The `app_call` node kind calls a discovered app tool (`agents/workflows/compiler.py:168-170`).
- **Limits that matter for agents.** A tool call has a 20-second deadline inside a 30-second outer one, and a timeout stops the app (`supervisor.py:676`, `715-726`).

**QMA v2 verdict.** KEEP (operator: "solid enough for now", 20 §1). Two rewraps. Move its two `qmx_agents` imports to a neutral package. Give agent-bearing apps an engine seam instead of an embedded Deep Agent.

## 3. The P10 workflow compiler

### 3.1 Format, node kinds and run model
- `WorkflowSpec` is `{version: "workflow.v1", name, entry, nodes, edges}` (`agents/workflows/models.py:168-173`). Its JSON Schema ships as `workflow.v1.schema.json` (473 lines).
- A node has an id, a kind, named typed `inputs` and `outputs`, `args`, and kind-specific fields (`models.py:88-112`, `59-67`). A port has `kind` (`reference, data, event, control`), `cardinality` and a JSON Schema (`models.py:29-42`).
- An edge names source and target ports and a mapping: `one, zip, broadcast, keyed-join, cartesian` (`models.py:120-125`).
- Validation refuses unknown ports, type-incompatible ports, many-to-one without a reducing mapping, unreachable nodes and any cycle that is not a bounded `loop` repeat (`models.py:175-283`).

| Kind | Required field | How it runs today |
|---|---|---|
| `python` | `function` | imports a dotted path and calls it (`compiler.py:102-109`, `160-161`) |
| `agent` | `agent` (AgentSpec path) | `build_agent`, then `ainvoke` (`compiler.py:194-202`) |
| `tool` | `tool` | registry tool `.ainvoke` (`compiler.py:191-193`) |
| `app_call` | `app_id`, `tool` | host-bound app tool (`compiler.py:191-193`) |
| `condition` | `predicate` (JSON Pointer) | writes a route `true` or `false` (`compiler.py:150-151`) |
| `parallel` | none | LangGraph `Send` to each target (`compiler.py:223-224`) |
| `join` | none | LangGraph barrier edge from all sources (`compiler.py:251-259`) |
| `loop` | `max_iterations` | counter in state, route `repeat` or `done` (`compiler.py:152-156`) |
| `human_gate` | none | LangGraph `interrupt()` (`compiler.py:162-163`) |
| `subworkflow` | `workflow` | compiles and invokes the child graph (`compiler.py:203-205`) |

Run model. `WorkflowRuns` owns one `AsyncSqliteSaver` per database (`workflows/runs.py:21-40`). The thread id is `<name>:<run_id>` (`runs.py:54`). `start`, `resume`, `cancel` and `status` are the API. `resume` sends `Command(resume=decision)` (`runs.py:56-124`). Cancellation stops at the next checkpoint and cannot undo a running tool (`workflows/README.md:61-64`).

### 3.2 What QMA v2 keeps and what is LangGraph-only

| Piece | Lines | Engine-neutral? | Fate |
|---|---|---|---|
| `models.py` (schema, ports, `compatible`, topology) | 289 | Yes. Pydantic and jsonschema only (`models.py:1-9`) | KEEP as the QMA v2 graph format |
| `workflow.v1.schema.json` | 473 | Yes | KEEP |
| `pointer`, `template`, `input_view`, port validation in `finish` | about 70 (`compiler.py:56-99`, `142-157`) | Yes | KEEP, move into the new runner |
| `WorkflowState` reducers, `StateGraph`, `Send`, barrier edges, `interrupt`, recursion limit | `compiler.py:34-41`, `219-309` | No | REPLACE with the QMA runner |
| `agent` node via `build_agent` | `compiler.py:112-128`, `171-202` | No | REPLACE with an `Engine` call that stores the engine's resume token |
| `as_subagent` (`CompiledSubAgent`) | `compiler.py:312-334` | No | REPLACE with a `run_workflow` tool both engines can call |
| `to_python` (emits LangGraph code) | `compiler.py:337-375` | No | REPLACE or DROP. The UI's Code view needs a new emitter |
| `WorkflowRuns` (AsyncSqliteSaver, `Command`) | 124 | No | REPLACE. Keep the four-verb API and the status set |

The status set (`missing, running, paused, failed, cancelled, completed, interrupted`, `runs.py:98-124`) is a good contract to keep. The UI and the remote worker both read it.

## 4. Tools, guards, memory, router, tasks and research

| Module | Lines | Engine-neutral logic | LangChain wrapper to drop | Fate |
|---|---|---|---|---|
| `tools/registry.py` | 281 | `domain_functions`: 13 plain functions (`registry.py:26-271`) | `tool(...)(function)` (`registry.py:274-281`) | KEEP-REWRAP |
| `tools/servers.py` | 38 | four FastMCP servers over the same functions (`servers.py:9-22`) | none | KEEP |
| `tools/service.py` | 266 | `DomainContext` over QMF, QMB, QML, QMN, Library (`service.py:13-22`) | none | KEEP |
| `guards/journal.py` | 127 | append-only JSONL, fingerprints, quarantine (`journal.py:17-127`) | none (Pydantic only, `:14`) | KEEP, move to a neutral package |
| `guards/experiments.py` | 138 | SQLite notebook per experiment (`experiments.py:31-138`) | none | KEEP |
| `guards/parent_surfaces.py` | 96 | permitted parent-surface table (`parent_surfaces.py:9-96`) | none | KEEP |
| `guards/money_path.py` | 279 | `check_descriptor`, act list and aliases (`money_path.py:21-162`, `247-279`) | `OrderProposalTool` and `BrokerOrderProposalTool` are `BaseTool` (`:181-238`); `check_tool` reads `BaseTool` (`:240-244`) | KEEP-REWRAP |
| `guards/admission.py` | 277 | `AdmissionGate` stage, approve, check, record (`admission.py:59-111`) | `AdmissionBackend` is a deepagents `BackendProtocol` (`:12`, `114-277`) | KEEP gate, REPLACE backend |
| `guards/hooks.py` | 179 | `_test` (tests green for this hash) and `watch_breakers` (`hooks.py:41-73`, `153-179`) | `AppHooksMiddleware.wrap_tool_call` (`:22`, `120-150`) | KEEP-REWRAP |
| `guards/middleware.py` | 237 | none of its own | `JournalMiddleware`, `MoneyPathMiddleware`, `JournalApprovals` (`middleware.py:28-237`) | REPLACE with engine hook adapters that call the neutral code |
| `memory.py` | 678 | `MemoryProvider` protocol on plain mappings, scopes, namespaces, `MemoryManager` (`memory.py:53-131`, `185-209`, `365-464`) | `tools() -> list[BaseTool]` (`:130`), `MemoryMiddleware`, `_MemorySummarization` (`:517-678`); `StoreMemoryProvider` sits on LangGraph `SqliteStore` (`:31`, `210-353`) | KEEP-REWRAP protocol, REPLACE store and hooks |
| `router.py` | 322 | `model_selector`, `RouterConfig`, profiles, override chain, `credential` (`router.py:40-141`, `194-203`) | `init_chat_model` (`:191`), `router_middleware` (`:205-278`), deepagents harness profiles (`:15`) | KEEP-REWRAP config, REPLACE resolution |
| `router.py` CLIProxy parts | `:181-186`, `288-302`; `models.yaml:1-14` | none | none | DELETE with CLIProxy (20 §1 Router) |
| `spec.py` | 499 | `AgentSpec`, `load_spec`, `mcp_configuration` (`spec.py:108-143`, `197-243`) | `_build` and `guards()` (`:246-499`) | KEEP-REWRAP spec, REPLACE builder |
| `copilot.py` | 213 | the block mapping rules (`copilot.py:123-212`) | `build_copilot`, `stream_turn` on a LangGraph graph (`:54-213`) | REPLACE with the turn host |
| `tasks.py` | 152 | the `record_work` and child-session pattern (`tasks.py:33-60`) | `@tool`, `AsyncSqliteSaver` (`:11-12`) | REPLACE with the QMX job runner |
| `research.py` | 60 | save web results to the Library (`research.py:23-43`) | `AgentMiddleware` (`:19`) | KEEP-REWRAP as a post-tool hook. Library is a seam |

Two facts shape the rewrap. First, `check_descriptor` already says it serves "LangChain and hosted MCP tools" alike (`money_path.py:248`). Second, OpenAI Agents SDK hooks only observe, so the money-path and admission checks must run inside QMX's own tool wrappers (study 19 §11, mismatch 2).

## 5. The server lane: qmx-remote and qmx-broker

qmx-remote already has:
- **A bundle.** `RunBundle` has a kind (`workflow, agent, app, job, amp`), a definition and its hash, inputs, a model profile, scoped credential names, resources and an optional git revision (`remote/models.py:67-98`).
- **Placement.** Named targets of provider `ssh`, `amp`, `modal` or `e2b` (`models.py:100-120`), chosen by `RemoteSettings.place` (`models.py:127`). One `ComputeProvider` protocol: provision, start, status, logs, stop, teardown (`remote/providers.py:18-24`).
- **A sealed manifest.** Run id, status, versions, artifacts with hashes, the latest checkpoint digest, a revision and a fingerprint (`models.py:157-180`).
- **Bucket sync.** The worker flushes the journal, logs, app volume and `state.db` checkpoint every five seconds and on each workflow step. A failed upload fails the run (`remote/worker.py:72-100`; `qmx-remote/README.md:1-7`).
- **Resume elsewhere.** `resume` refuses running or finished runs, needs a verified checkpoint, tears down the old handle and relaunches on any target (`remote/runs.py:196-220`).
- **Laptop-off agents and workflows.** `execute_workflow` and `execute_agent` drive LangGraph with an `AsyncSqliteSaver` on `state.db` (`worker.py:137-208`). The manifest records the `langgraph` version (`worker.py:104`).
- **A node.** `qmx node bootstrap` installs Docker, Tailscale, uv, rclone, a systemd `qmx-node` service and a log-shipping timer (`ctl/node-bootstrap.sh:11-74`). CLIProxy is left to the operator (`node-bootstrap.sh:89`; `ctl/node.py:75-77`).

qmx-broker gives read tools and `propose_order`, never an order (`qmx-broker/src/qmx_broker/service.py:164-185`; `server.py:12`).

**QMA v2 verdict.** qmx-remote is KEEP-REWRAP. Bundles, placement, manifests, store and resume stay. The worker's two LangGraph executors call the `Engine` and the new graph runner instead. The Contabo "orb" (20 §3.6) is this lane plus supervised app services. qmx-broker is KEEP.

## 6. Inventory and plan

### 6.1 Package table

Source lines are `src/` Python. Test lines are separate.

| Package or folder | Src lines (tests) | Fate under QMA v2 | Imported by |
|---|---|---|---|
| `qmx-control` | 2,138 (1,597) | KEEP, enhance | qmx-agents (`spec.py:35`, `copilot.py:16-18`, `tasks.py:13-14`, `research.py:14`, `hooks.py:16-17`); qmx-tools (`service.py:20-22`); QMB host CLI spawns `python -m qmx_control` (`qmb/src/qmb/doors/cli/host.py:1799`) |
| `qmx-apps` | 3,054 (1,875) | KEEP; rewrap 4 imports | qmx-control (`service.py:20-26`); qmx-agents (`hooks.py:14-15`); qmx-remote |
| `qmx-tools` | 591 (275) | KEEP-REWRAP (drop `registry.py:274-281`) | qmx-agents (`spec.py:36`, `compiler.py:23-24`, `copilot.py:19-20`) |
| `qmx-broker` | 846 (594) | KEEP | qmx-agents (`money_path.py:14-15`, `spec.py:33-34`); qmx-control (`service.py:27-28`) |
| `qmx-remote` | 1,369 (488) | KEEP-REWRAP (worker executors) | qmx-control (`service.py:29-30`, `server.py:22`) |
| `qmx-agents` guards (journal, experiments, parent_surfaces) | 361 | KEEP, move to a neutral package | qmx-apps (`road/__init__.py:11`, `road/history.py:13`, `road/validation.py:12`); qmx-remote (`models.py:11`, `runs.py:16`, `worker.py:29`) |
| `qmx-agents` money_path, admission, hooks | 735 | KEEP-REWRAP | qmx-apps (`supervisor.py:29`) |
| `qmx-agents` middleware, copilot, tasks | 602 | REPLACE | internal only |
| `qmx-agents` memory, router, spec, research | 1,559 | KEEP-REWRAP | qmx-remote (`worker.py:30-31`); example apps |
| `qmx-agents` workflows (models + schema) | 289 + 473 | KEEP as the graph format | internal; qmx-remote (`worker.py:32`) |
| `qmx-agents` workflows (compiler, runs) | 499 | REPLACE | qmx-remote (`worker.py:32`) |
| `qmx-agents` agents/*.yaml, skills/, copilot.md | 77 | KEEP-REWRAP into plugins | `copilot.py` |
| `qma-core` | 24,072 (8,034) | DELETE (P16) | see 6.2 |
| `qma-daemon` | 74,198 (54,799) | DELETE (P16); harvest `native_*` first | see 6.2 |
| `qma-wire` | 15,958 (7,450) | DELETE, except `money_path_diff.py`, `schemas.py`, `schema_data/` (DESIGN §12c.3) | QMB names `qma.wire.money_path_field_diff.v1` as a string (`qmb/src/qmb/analysis/variants.py:66`) |
| `qmx-agents/plugins/` (old desk packs) | 583 | DELETE; the name collides with QMA v2 plugins | itself; `qmx-agents/tests/test_workspace_scaffold.py:8` |
| `qmx-agents/examples/` | 3,041 | DELETE or archive (old runtime proofs and notes) | none |
| `examples/apps/` (4 apps) | 4,143 | KEEP; rewrap the agent parts of `weekend-watcher` and `macro-daily-bias` | road tests, P15 tests |
| `scripts/live/` | 260 | KEEP-REWRAP (`copilot_build_app.py` becomes a turn-host smoke) | operator only |
| `apps/qmx-ui/src` | 4,645 | OUT OF SCOPE (scrapped UI, `rebuild/README.md:20`) | none |
| `qmb`, `qml`, `qmn`, `packages/qmf-*`, `extensions` | 155,874; 35,493; 147,865; 121,542; 1,491 (all text files) | OUT OF SCOPE, protected | they import no `qmx_*` package (git grep empty). `qmx-tools` and `qmx-broker` import them |
| Library (`ctl/library.py`) | 260 | OUT OF SCOPE; named seam | `service.py:34`, `tools/service.py:20` |

### 6.2 What still imports the old qma packages after P16c
State at 4fa38ffe. PRs #58 to #66 all merged today. The last merged at 16:40 UTC (#66). The 20 most recent PRs include none still open.

- **New packages.** None. No file under `qmx-agents/packages/qmx-*/src` imports `qma` (git grep).
- **Protected code, tests and examples.**
  - `qmb/tests/test_operator_study_cli.py:21-31`, `:189` import `qma.core` and `qma.daemon`.
  - `qmn/examples/spot_paper_journey.py:15-17` imports `qma.daemon` and `qma.wire`.
  - `qmb/src/qmb/doors/cli/host.py:104` keeps `DAEMON_SPAWN_MODULE = "qma.daemon"`. `_spawn_argv` (`:689-693`) still builds the old spawn for `invoke_host_start` (`:938`) and `invoke_host_recover_control` (`:1746`). The CLI tree no longer uses them; `qmb/examples/host_lifecycle_usage.py` does (PR #49 body).
  - PR #58 measured the cost. Through `qma.daemon.process`, that one entry point keeps about 110k of the 127k old lines alive. P16c may not edit `qmb/` beyond import lines, so it stays.
- **Repo glue.** `qa/integration/test_qma_registered_replay.py`, `qa/integration/test_qma_authenticated_study.py`, the five desk-pack plugins, four scripts in `qmx-agents/examples/`, `qmx-agents/tests/test_workspace_scaffold.py:8`, and workspace config (`qmx-agents/pyproject.toml:17`, `26-28`, `64`, `137`; root `pyproject.toml:228-230`, `341`, `360-362`).

**Correction to 02 §5.** 02 said `qmb host start` still launches the old daemon. It no longer does. PR #49 made the CLI delegate to `qmx_control`. What survives is the unreferenced helper API above.

### 6.3 Plan (order only, each step ends in a check)
1. **Subtract first.** Delete `qmx-agents/plugins/` and `qmx-agents/examples/`. Copy `native_claude.py` (435 lines), `native_codex.py` (553) and `native_sessions.py` (446) into the tracker as reference before P16 removes them.
2. **Break the cycle.** Move journal, experiments, parent_surfaces and `check_descriptor` into a neutral package with no LangChain dependency. qmx-apps and qmx-remote import that package. Check: `qmx-apps` installs without `langchain` in its lock.
3. **Turn host and approvals.** A new host package owns the `Engine` interface, a turn route, an approvals table and a cancel route in qmx-control. Check: a fake-engine turn writes the expected block types over SSE.
4. **Two engines.** ClaudeEngine and OpenAIEngine behind that interface, with QMX tool wrappers enforcing policy. Check: one money-path denial test runs on both engines.
5. **Graph runner.** A QMA runner over `workflow.v1` with one SQLite checkpoint per node, gates as approvals, and fan-out, join and loop. Fill the four `workflows_*` routes. Check: the P10 test list (`rebuild/packets/P10-workflow-compiler.md:31-37`) passes on the new runner.
6. **Plugins and router.** Convert the copilot YAML, sub-agent YAMLs and skills into plugins. The router reads settings and picks a sticky endpoint per session.
7. **Server lane.** Rewrap the qmx-remote executors and add supervised services on the node.
8. **Delete the LangChain path** in one wave: `middleware.py`, `copilot.py`, `tasks.py`, the compiler, and the deepagents, langchain and langgraph pins.

---

# Part 2. /why

## 7. Why QMX moved to LangChain, LangGraph and Deep Agents (about 2026-10-04)

| # | Reason, with evidence | Constraint for QMA v2 | Respect or drop |
|---|---|---|---|
| W1 | The operator said the agentic part "is proving to be a problem" (memory `qmx-agentic-langgraph-shift.md`, 2026-10-04; `ui-model-and-baseline-audit.md:187`). The audit found a 4,007-line `DaemonProcess`, 2,049 decision IDs in daemon comments, three ways to reach a model, nothing CI-checked, and "staging theatre" (`rebuild/research/audit-code.md:14-19`, `175-183`). | No parallel runtime, no god process, no decision IDs in code (`rebuild/DESIGN.md:28-34`). One way to reach a model. | Respect |
| W2 | Two workflow engines (`taskgraph/`, 10.8k lines, and LangGraph) were glued by `canonical_join.py` (1,185 lines). The failing tests lived there (`audit-code.md:179`, `194`). | **One** workflow engine. QMA v2's graph must not run beside LangGraph. Study 19 §13 advised keeping LangGraph for the Lab; doing both would rebuild the canonical-join problem. | Respect the rule; the engine changes |
| W3 | "Adopt before building" (`DESIGN.md:25`). Deep Agents gave planning, sub-agents, files, compaction, skills, approvals and checkpoints (`DESIGN.md:11`; `research-harness.md:296-317`). | Adopt the two SDKs for everything they give: loop, tools, sessions, hooks, compaction, tracing. Build only the graph, router, ledger, approvals and policy, which study 19 §11 says QMX must own anyway. | Respect, with one conscious drop: QMA v2 builds its own graph engine |
| W4 | Invariants survive as thin wrappers: the evidence journal, ledgers, money-path barrier and admission gate (`DESIGN.md:28-32`, `209-216`, `474-478`). | Keep each rule once, in neutral code, and call it from both engines. | Respect |
| W5 | "Configurable means UI-editable" (`DESIGN.md:33`). | Router defaults, plugin choice, budgets and summariser model live in `settings.toml` sections behind `settings_put`. | Respect |
| W6 | One API, two doors. The copilot uses what the UI uses (`DESIGN.md:13`, `354-366`). | Engines see qmx-control as MCP. No agent-only back doors (P15 test rule, `packets/P15-copilot-and-first-app.md:31`). | Respect |
| W7 | No LangGraph Agent Server, to avoid another server and its licence. Background work is QMX's own (`DESIGN.md:366`, `489-491`). | QMX owns its job runner and turn host. Neither SDK hosts QMX. | Respect |
| W8 | CLIProxy was the daily path: subscription accounts, rotation, session affinity (`DESIGN.md:121-137`). The proxy kept no usage history, so QMX journals tokens itself (`DESIGN.md:135`). | Drop CLIProxy (20 §1 Router). Keep two lessons: sticky sessions for caches, and QMX's own usage ledger. | Drop the proxy, respect the lessons |
| W9 | The override chain: global, node, app, workflow, agent node, sub-agent (`DESIGN.md:146-150`). | Keep the chain. Fix the bug where the per-request model beats every sub-agent (`router.py:199-200`; 02 §2). | Respect and fix |
| W10 | Tests use fake models; live calls only in `scripts/live/` (`rebuild/README.md:18`; `DESIGN.md:497`). | Each engine needs a fake for CI. No test may need a key or the plan. | Respect |

## 8. Why the mini-app runtime looks the way it does

| # | Reason, with evidence | Constraint for QMA v2 | Respect or drop |
|---|---|---|---|
| A1 | The operator's idea is a packaged app with its own data, earned by passing tests, usually without agents (`rebuild/research/miniapp-concept.md:21-31`). DESIGN made it Docker-shaped: definition, instance, volume (`DESIGN.md:14-18`, `242-248`). | An agent never owns an app's data. It calls the app's tools. | Respect |
| A2 | Every app speaks MCP, so the copilot, workflows and external hosts all use it the same way. MCP Apps carry the UI (`DESIGN.md:274-282`; `research-harness.md:356-388`). | Both engines consume apps as MCP. The Claude engine can mount them directly; the OpenAI engine through its MCP support or QMX wrappers. | Respect |
| A3 | No app-to-app bus. Data moves by checked reference (`DESIGN.md:278-281`; `research-harness.md:410-416`). | Cross-app wiring stays in a workflow node or an agent turn. | Respect |
| A4 | Agent-written code starts at T2 or T3 (`DESIGN.md:301`; `qmx-apps/README.md:13-15`). | Copilot-built apps run in Docker on the Contabo node until reviewed. Windows T1 refuses them. | Respect |
| A5 | Money apps never go live without the operator's signature. The signing door is not an agent tool (`server.py:184-196`; `road/__init__.py:144-145`). | No engine, plugin or router setting may reach the sign door. | Respect |
| A6 | Everything is files. No database server (`DESIGN.md:314`, `389`). | The graph runner and approvals use SQLite. | Respect |
| A7 | Agent-bearing apps embed the agent core at a pinned commit so their lock stays portable (`qmx-apps/README.md:68-70`). | That choice ties app images to one agent library. QMA v2 needs an app-side engine seam: a thin client to the host, or a small embedded engine package. | Consciously change |

## 9. Why the P10 workflow compiler looks the way it does

| # | Reason, with evidence | Constraint for QMA v2 | Respect or drop |
|---|---|---|---|
| F1 | The node editor began from n8n: a schema'd JSON description that refuses to run when wrong. JSON describes; Python and QMX capabilities execute (`miniapp-concept.md:152-156`, `171`). | Keep `workflow.v1` as the stored truth. The UI's Graph, Code and Import modes are three views of it (`DESIGN.md:291`). | Respect |
| F2 | Typed ports and explicit collection mapping came from the operator and the ratified mapping set (`miniapp-concept.md:152-154`; `packets/P10-workflow-compiler.md:8`; PR #36 body). | Keep the five mappings and the cardinality rules. | Respect |
| F3 | Deterministic by default, agents optional (`miniapp-concept.md:159`). | The runner must work with no engine at all. | Respect |
| F4 | Only bounded loops may close a cycle (`models.py:235-283`; PR #36). | Keep. It is the "loop inside a graph" from the operator's clippings (20 §2.4). | Respect |
| F5 | Workflow agent nodes default to no general-purpose sub-agent (`models.py:103`; `DESIGN.md:495`). | Sub-agents in workflows do not spawn sub-agents. Remove the Agent tool from Claude workers (study 19 §12). | Respect |
| F6 | A run pins its definition. A retry is not a new experiment (`miniapp-concept.md:164`). | Store the definition hash with each run and each checkpoint. | Respect |
| F7 | Results go back as artifact references, not text (`DESIGN.md:113`; `compiler.py:231-244`). | Keep. The Library is a seam; the artifact store can be the run folder until the Library refactor. | Respect |
| F8 | It compiled to LangGraph because LangGraph was the one engine (`DESIGN.md:20`, `289`). | Gone with the LangGraph drop. The runner must supply what LangGraph gave: per-step checkpoints, gate resume, fan-out, join barriers, bounded recursion. Study 19 §13 lists the bill. | Drop consciously |
| F9 | Paths to Python functions and AgentSpecs are host-authored configuration, never model-chosen arguments (`workflows/README.md:4-6`). | A copilot that writes workflows still writes them through `workflows_put` and validation, never as runtime arguments. | Respect |

## 10. Preserve, change, avoid

- **Preserve.** The block log and SSE. The `apps_*` contract and artifact references. `workflow.v1`. The neutral guards. Domain functions and their FastMCP servers. The remote bundle, manifest and resume model. The road to live.
- **Change.** Agent construction (`spec._build`), turn streaming, background tasks, the workflow executor, the router's resolution, memory hooks, and the two LangGraph executors in the remote worker.
- **Avoid.** A second workflow engine beside the new one. Policy that lives only in an engine's hooks. A turn host inside `ControlService`, which would deepen the import cycle. Compatibility shims: there is no data to migrate (`DESIGN.md:515`).

Sources consulted. Source control: git log, blame and grep on `origin/rebuild/base`, and PR bodies #36, #37, #47, #49, #58 and #66. Long-form documents: `rebuild/DESIGN.md`, `rebuild/README.md`, `rebuild/packets/P10`, `P12`, `P15`, `P16`, `P17`, and `rebuild/research/audit-code.md`, `research-harness.md`, `miniapp-concept.md`, `ui-model-and-baseline-audit.md`. Operator memory: `qmx-agentic-langgraph-shift.md`. Issue tracker, team chat, observability, error tracking and analytics were skipped: no such MCP is connected for QMX, and the GitHub MCP failed to connect this session (gh CLI used instead).

---

## Risks the rebuild must not miss

1. **The import cycle.** qmx-control needs qmx-apps (`qmx-control/pyproject.toml` dependencies). qmx-apps needs qmx-agents. qmx-agents needs qmx-tools, and qmx-tools needs qmx-control. qmx-apps imports qmx-agents only for the journal and `check_descriptor` (`supervisor.py:29`; `road/__init__.py:11`). Move those first, or the new engine package inherits the cycle and qmx-apps drags both SDKs into every node image.
2. **Agent apps break silently.** `weekend-watcher` and `macro-daily-bias` import `qmx_agents.spec` and `qmx_agents.router` at a pinned commit. Their hashes are immutable. Replacing those modules needs new app versions through the road, not edits.
3. **No turn host and no approvals route.** Every Wednesday-minimum item depends on them. They are not in any packet yet.
4. **Two approval styles.** Claude asks inside a live process; OpenAI pauses and serialises. The approvals table must hold both, and the UI must not see the difference (study 19 §11, mismatch 1). A `human_gate` must survive a restart without replaying a live Claude session.
5. **Policy bypass.** The money-path check at call time lives in `MoneyPathMiddleware` today (`middleware.py:34-72`). OpenAI hooks cannot block. Claude's built-in Bash and WebFetch skip QMX tools. Put the checks inside QMX tool wrappers, give the OpenAI engine only wrapped shell tools, and turn off Claude built-ins that bypass the sandbox app.
6. **Streaming load.** SSE polls SQLite every 50 ms and every event is a row (`service.py:156-198`). Token deltas written as rows would bloat `events`. Send deltas on a separate, unstored channel and write whole blocks to the log.
7. **The block list is closed.** `SessionBlock.type` is a fixed `Literal` (`service.py:54-72`). Engine events with no matching kind need a mapping decision, not a silent drop.
8. **The 110k-line anchor.** `qmb/src/qmb/doors/cli/host.py:104`, `689-693` keeps most old code importable. Only the operator can authorise that QMB edit (`DESIGN.md:504-507`). QMA v2 must not import `qma` at all, so this stays a separate deletion.
9. **Losing the only Claude SDK recipe.** `native_claude.py` holds the tested isolation pattern (`CLAUDE_CONFIG_DIR`, `tools=[]`, `setting_sources=[]`, `create_sdk_mcp_server`; 02 §4). P16 lists it for deletion. Copy it first.
10. **The server lane assumes LangGraph.** `worker.py:29-32`, `104`, `137-208` hard-wire it. A Claude engine on Contabo also needs the `claude` binary and a plan sign-in on a headless Linux box. Whether that sign-in is allowed there is UNVERIFIED; 20 §2.1 covers only the operator's own use.
11. **Workflow storage has no home.** DESIGN puts definitions in the Library or inside an app (`DESIGN.md:327`). The Library is out of scope, so `workflows_put` needs its own store, or a named seam to the Library.
12. **Long agent calls inside apps time out.** An app tool call has 20 seconds, and a timeout stops the app (`supervisor.py:676`, `715-726`). An app that runs an agent per call will trip this on real models.
13. **Two "plugins".** `qmx-agents/plugins/` holds old desk packs on `qma.core.plugins`. QMA v2 plugins are a different thing. Delete the old folder before the new loader lands, or agents and humans will confuse them.
14. **The per-request model bug.** A turn's tier overrides every sub-agent's model (`router.py:199-200`). The usage-balancing router must decide whether a session's choice reaches its sub-agents. Today it silently does.
15. **CI without keys.** Today's fakes are LangChain models (`DESIGN.md:497`). Both SDKs need fakes before the first engine PR, or CI will need live keys, which the rules forbid (`rebuild/README.md:18`).
16. **Two control planes.** The laptop and the node each run qmx-control with their own `control.db` (`ctl/node.py:158`). Server workflows write events on the node. The UI needs one view of both.
