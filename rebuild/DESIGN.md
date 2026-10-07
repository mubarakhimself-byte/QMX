# QMX rebuild design: agent core and mini apps

Status: proposed by Claude on 2026-10-07, approved in outline by the operator in chat.
Inputs: everything under `research/`, the transcripts it cites, and the UI on `ui-review/repair`.
This document replaces the QMA runtime architecture (AD-5, AD-10..18, AD-20, AD-23, AD-29) where they conflict.
The domain core (QMF, QML, QMB, QMN, MIS) is unchanged.

## 1. Plain-language summary

- QMX keeps its quant engine: data (QMF), research language (QML), backtester (QMB), trading node (QMN) and MIS. That code works and stays.
- The agent layer is rebuilt as a thin layer on top of **LangChain Deep Agents**. The library already provides planning, sub-agents, files, context compaction, skills, approvals and checkpoints. QMX stops hand-building those.
- An **agent is a settings file**: which model, which tools, which MCP servers, which skills, what memory, which sub-agents, what needs approval.
- The **Copilot is a Deep Agent** that uses the same API the UI uses. Anything you can click, it can do; anything it does, you can see.
- A **mini app works like a Docker container**:
  - definition = image
  - running app = container
  - its own data folder = volume
  - Agents, workflows, screens and a background loop are optional parts of one shape.
- Every mini app **speaks MCP**. Its tools and screens (MCP Apps) are what the Copilot and other apps use. Apps pass data to each other by reference, through the Copilot or a workflow.
- **One workflow engine: LangGraph.** The node editor saves a graph as JSON, and QMX compiles it into a LangGraph graph. A workflow can be handed to the Copilot as a sub-agent.
- Every app gets **its own small database file**, backed up to S3. There is no shared app database.

## 2. Principles (apply to every packet)

1. Adopt before building. If LangChain, LangGraph, Deep Agents, MCP or the standard library does it, use that.
2. YAGNI. Build the 95% case. No speculative layers, no "future-proof" abstractions without a second user.
3. Modular by design. Each part has one job and a small interface (section 9 lists them).
4. Invariants survive as thin wrappers, never as a parallel runtime:
   - the evidence journal
   - the ledgers
   - the money-path barrier
   - the admission gate
5. Configurable means UI-editable (standing operator rule).
6. No ceremony in code. Comments explain *why* in plain words. No decision-ID prose in code. One short doc per module at most.
7. Main holds no code. Work lands on `rebuild/base` through PRs; `integration` later.

## 3. What stays, what gets replaced, what goes

| Area | Verdict | Notes |
|---|---|---|
| QMF, QML, QMB, QMN, MIS packages | **Keep** | Exposed to agents as tools (section 6). No rewrite. |
| LangChain loop, LangGraph research/actor workflows (`request_runtime/`) | **Keep, slim** | Becomes the seed of `qmx-agents` |
| Skills/hooks via LangChain middleware | **Keep** | |
| Mini-app staging code from MA02–MA04 (versioning, validation, publish) | **Port** | Into the road-to-live module (section 7.5) |
| Evidence journal, ledgers, money-path barrier, admission | **Keep as middleware / backend wrappers** | |
| QMA task graph engine, loop registry, MissionCompiler, canonical join | **Replace** with LangGraph | Retired once the workflow compiler (7.4) works |
| Hook registry (23 verbs) | **Replace** with LangChain middleware | |
| Model proxy chain, `native_*` sessions, `proxy/` | **Replace** with the model router (5.3) | |
| Tool registry and MCP adapter layer | **Replace** with per-agent `tools=` and `langchain-mcp-adapters` | |
| Agent bus and mailboxes | **Replace** with sync/async sub-agents | |
| Memory provider contract and two memory modules | **Replace** with one `MemoryProvider` (5.4) | |
| Hand-written HTTP/WebSocket server, JSON-RPC wire, pairing | **Replace** with FastAPI (section 8) | |
| `DaemonProcess` (4,000 lines) | **Retire** | Do not refactor; the strangler replaces it |
| LangMem extraction, `authored_graphs.py` | **Delete** | Dead in production; LangMem is dormant upstream |
| Test fixtures inside `src/`, empty `qma-ui-contract`, `_docwork/`, evidence folders | **Delete or move** | |

Strategy: **strangler**. New thin packages run beside the old daemon. Callers move one at a time, then old code is deleted. Code that is about to be replaced is not refactored.

## 4. System shape

```
UI (Svelte)  ──HTTP/SSE/WS──►  qmx-server (FastAPI)  ◄──MCP──  external hosts (Claude Desktop, VS Code)
                                  │
              ┌───────────────────┼─────────────────────────┐
              ▼                   ▼                         ▼
       qmx-agents           qmx-apps (supervisor)     qmx-control (one API, served as REST + MCP)
   Deep Agents + router     definitions/instances/     apps, workflows, runs, jobs, logs,
   memory + middleware      volumes, road to live      library, settings
              │                   │
              └──────── domain tools (QMF, QML, QMB, QMN, MIS adapters) ────────┘
```

## 5. Agent core (`qmx-agents`)

### 5.1 Agent definition (config, not code)

An `AgentSpec` file (YAML) compiles to `create_deep_agent(...)`.

```yaml
name: lab-researcher
model: tier:workhorse            # resolved by the router (5.3)
system_prompt: prompts/lab-researcher.md
tools: [qmb.backtest, qmf.read_bars, library.save]
mcp_servers: [firecrawl, qmx-control]
skills: [skills/backtest-analysis]
memory: { scope: workflow }      # task | workflow | session | global
subagents:
  - ref: agents/data-analyst.yaml          # sync sub-agent
  - workflow: workflows/backtest-pipeline   # compiled LangGraph graph as sub-agent
async_subagents: [agents/overnight-sweep.yaml]
interrupt_on: { promote_strategy: true, publish_mini_app: true }
permissions: { write: ["/artifacts/**"], deny_write: ["/data/**"] }
budget: { model_calls: 200, tool_calls: 400 }
```

- **Deep Agents is the default agent type.** The general-purpose sub-agent stays on for the Copilot and is off inside workflow nodes unless the spec turns it on.
- **Specific tools, MCPs and data per agent:**
  - Tools: `SubAgent.tools` replaces inherited tools.
  - MCP: one `MultiServerMCPClient` per spec.
  - Data: a `CompositeBackend` route plus `permissions`.
- Per-run identity (session, workflow, task, app) travels in `context_schema`.

### 5.2 Delegation

| Need | Mechanism |
|---|---|
| Quick isolated job (look-up, short research) | sync `SubAgent` through the `task` tool |
| Long job (sweep, app build, overnight) | `AsyncSubAgent`: start/check/update/cancel/list. Feeds the UI "Activity / jobs" panel |
| Fixed pipeline (ingest → backtest → tearsheet) | `CompiledSubAgent` wrapping a LangGraph workflow |
| Bulk coverage (every symbol or fold) | `CodeInterpreterMiddleware` fan-out, with the interpreter tool gated |
| Irreversible decision | escalate to a high-reasoning model, or ask the operator via `interrupt_on` |

Sub-agents hand results back as **artifact references** (paths in the artifact store), not long text.

### 5.3 Model router

- `init_chat_model("provider:model")` per tier.
- Tiers: `fast`, `workhorse`, `coding`, `reasoning_high`.
- Routing via `@wrap_model_call` (a 20-line custom router). LangChain's experimental router middleware may replace it later.
- `ModelFallbackMiddleware` and `ModelRetryMiddleware` for resilience.
- Providers: Anthropic API, OpenAI API, OpenRouter, local (OpenAI-compatible). Keys come from Windows Credential Manager `qmx/*`.
- **CLIProxyAPI** is an optional provider entry (an OpenAI-compatible base URL).
  - Anthropic's terms say Claude subscription OAuth is only for Claude Code and Claude apps, and Anthropic may enforce that without notice.
  - Turning it on is the operator's choice and is off by default.
  - The Codex subscription path is unclear; there is no primary OpenAI statement.

### 5.4 Memory

- One `MemoryProvider` protocol, signatures in `research/research-memory-storage.md` §B4.
- A `MemoryManager` holds built-in memory plus at most one external provider (the Hermes rule). The provider is chosen in settings.
- Default provider: LangGraph `SqliteStore`, one file per profile (`copilot/memory.db`, `apps/<id>/memory.db`).
- Scopes map to store namespaces: task ⊂ workflow, session, global.
- Hooks attach as LangChain middleware: `before_agent` loads the pinned profile, `before_model` prefetches, `after_agent` syncs the turn, and summarization runs the pre-compress hook.
- **No LangMem.** Background extraction is a scheduled sub-agent that writes to `/memories/`.
- Mem0, Honcho and Hindsight adapters come later, one at a time.
- Rules:
  - Automatic writes only from the primary agent.
  - Global writes need approval (on by default).
  - Prompt-bound text is length-capped.

### 5.5 Context

Deep Agents defaults handle context:
- summarization at 85%
- large results offloaded at 20k tokens
- prompt caching for Claude

Add `ContextEditingMiddleware` (clear old tool results) for long Copilot sessions.

### 5.6 Data-heavy work (RLM)

A `data-analyst` sub-agent runs on a Python sandbox backend (`execute`), with pandas/DuckDB and read-only data mounts. Its prompt follows the RLM style:
- load the data as variables
- filter it in code
- call sub-models only on slices
- return compact results plus an artifact path

If that falls short, `rlms` with a Docker REPL can be wrapped as one tool.

### 5.7 Invariants as middleware

| Invariant | Implementation |
|---|---|
| Evidence journal | `after_model` / `wrap_tool_call` middleware appends run, tool and decision records |
| Admission gate | backend wrapper on `/artifacts/` and memory global writes |
| Money-path barrier | order-capable tools are never in any agent's tool list. Agents can only *propose*; the operator signs in Portfolio |
| Budgets | `ModelCallLimitMiddleware`, `ToolCallLimitMiddleware`; numbers are UI-editable |

### 5.8 Tracing and evals

- Tracing: LangSmith if a key is set, otherwise OpenTelemetry to a local file. Langfuse is an alternative adapter.
- Evals: a small `evals/` set of golden tasks per agent spec, run on demand.

## 6. Domain tools

Each domain capability gets a typed LangChain tool, grouped into MCP servers:
- `qmx-research`: QML and Library
- `qmx-backtest`: QMB run/status/results
- `qmx-data`: QMF read-only bars, features and calendars
- `qmx-node`: QMN read-only state plus a *propose order* tool

Tool rules (Anthropic tool-design guidance):
- few, task-shaped tools
- named results
- pagination
- `response_format` concise/detailed
- error messages that say how to fix

## 7. Mini apps (`qmx-apps`)

### 7.1 The model

| Docker | QMX | Content |
|---|---|---|
| image | **App definition** | `app.toml` manifest + code + `uv.lock` + optional parts. Immutable, versioned, content-hashed |
| container | **App instance** | one running process tree on one node, with limits, logs and heartbeat |
| volume | **App data** | `apps/<id>/`: `app.db` (SQLite), `memory.db` (if it has agents), `data/*.parquet`, `blobs/`. The backup unit |
| registry | **App catalog** | definitions by hash (git or bucket) |
| compose | **Node supervisor** | start/stop/restart, health, budget, breaker, backups |

**Optional parts of a definition.** Any combination is allowed:
- `agents/` (AgentSpecs)
- `workflows/` (node graphs)
- `ui/` (MCP Apps panels, or tier-1 JSON panels)
- `jobs/` (schedules)
- `tools/` (Python functions exposed over MCP)

Common shapes:

| Shape | Agents | Screens | Example |
|---|---|---|---|
| Agent app with screens | yes | yes | Macro daily bias, News & sentiment |
| Agent app, headless | yes | no | Weekend watcher (Telegram) |
| Tool/data app with screens | no | yes | Correlation map, Exchange status |
| Headless service | no | no | Trading node, dataset builder, data collector |

### 7.2 Risk classes and road to live (from the UI, kept as is)

- **Shows things**: auto-live after tests and shadow run.
- **Runs work**: auto-live inside a fixed budget.
- **Touches money**: proposes only. Every order is signed by the operator.

Road to live: **Build → Tests → Sandbox (recorded data) → Shadow run (live data, output unused) → Live** (monitoring, budget, circuit breaker). Each step stores an evidence record.

### 7.3 Every app is an MCP server

- Each instance serves its `tools/` (and `ui://` panels) over MCP: stdio locally, streamable HTTP on nodes.
- The Copilot and workflows are MCP clients of apps. External hosts (Claude Desktop, VS Code) can open the same apps.
- **App to app:**
  - App A writes an output artifact and returns a typed reference (JSON Schema per output).
  - App B's tool accepts the reference.
  - The wiring is done by a workflow node or the Copilot. There is no direct app-to-app bus.
- App screen state lives in the app's `app.db` and is re-read on open, because MCP Apps has no state persistence.

### 7.4 Workflows and the node editor

- A workflow is a JSON graph:
  - nodes: `python`, `agent` (AgentSpec), `tool`, `app_call`, `condition`, `parallel`, `join`, `loop`, `human_gate`, `subworkflow`
  - edges carry typed ports
- `qmx-agents` compiles it to a LangGraph `StateGraph` with a SQLite checkpointer. Deterministic nodes are plain Python. Agent nodes are Deep Agents.
- Workflows run inside an app, or standalone as a job, and can be registered as `CompiledSubAgent`s.
- The Lab's Graph / Code / Import modes are three views of the same JSON.

### 7.5 Isolation tiers

| Tier | Where | Use |
|---|---|---|
| T1 (default) | laptop: subprocess + per-app `uv` venv + Windows Job Object limits; env holds only declared secrets; volume is the only writable root | first-party and operator-built apps |
| T2 | Docker container; default on Linux nodes | trading nodes, agent-written code, third-party dependencies |
| T3 | remote sandbox (E2B, Modal, Daytona) as a compute provider | untrusted or bursty work |

Agent-written app code starts at T2/T3 and moves to T1 only after operator review.

### 7.6 Storage, backup, cache

- `app.db`: SQLite in WAL mode, one writer per app (the instance).
- Analytics: DuckDB in process over `app.db` (read-only attach) plus Parquet.
- Backup: scheduled `VACUUM INTO` snapshot → rclone to `s3://<bucket>/<node>/<app>/<ts>/`, with a restore test each run.
- Litestream only on Linux nodes that need second-level recovery.
- Cache: in-process `cachetools`. The app's own SQLite holds durable cached results. No Redis.
- Convex was evaluated and rejected: its server code is TypeScript only and it adds a server per node. Its component isolation idea is what the per-app volume copies.

### 7.7 Observability (host-provided, never per app)

The supervisor provides, for every instance:
- structured logs (JSONL in the volume)
- heartbeat
- metrics (runs, errors, budget used)
- breaker state
- placement (which node)

The UI's Apps detail pane reads these. Remote nodes stream the same data over `qmx-control`.

## 8. One API for UI and Copilot (`qmx-control`)

- A FastAPI app with REST routes plus SSE/WebSocket streams, with the same operations also served as an MCP server.
- The Copilot gets the MCP form; the UI gets the REST form. **One implementation, two doors.**
- Operations:
  - apps: create, edit, version, test, publish, start, stop, logs, evidence
  - workflows: get/put graph, validate, run
  - runs and jobs: list, cancel
  - library: search, save
  - settings: providers, MCP servers, budgets
  - copilot sessions: typed block log
- Auth: a local token for the laptop; per-node token plus Tailscale for remote nodes.
- LangGraph Agent Server is not used. FastAPI plus in-process LangGraph is enough, and it avoids another server and its self-hosting licence terms (check them before revisiting).

## 9. Module interfaces (the seams)

| Module | Public interface |
|---|---|
| `qmx_agents.spec` | `load_spec(path) -> AgentSpec`, `build_agent(spec, ctx) -> CompiledGraph` |
| `qmx_agents.router` | `resolve(tier) -> BaseChatModel`, `router_middleware()` |
| `qmx_agents.memory` | `MemoryProvider`, `MemoryManager` |
| `qmx_agents.workflows` | `load_graph(json) -> WorkflowSpec`, `compile(spec) -> CompiledGraph` |
| `qmx_agents.guards` | journal, admission, money-path, budget middleware |
| `qmx_apps.manifest` | `AppDefinition` (parse/validate `app.toml`) |
| `qmx_apps.supervisor` | `install`, `start`, `stop`, `status`, `logs`, `snapshot` |
| `qmx_apps.road` | stage machine plus evidence records (ported MA02–MA04) |
| `qmx_control` | FastAPI app and MCP server over one service layer |
| `qmx_tools.*` | domain tools/MCP servers over QMF/QML/QMB/QMN |

## 10. Rulings this design amends (operator confirmed the direction in chat, 2026-10-07)

- ADR-0019 / DEC-0200/0201 (containers only for observability): containers are allowed for apps (T2).
- GAP-0075 / DEC-0316 (Modal, Daytona, E2B rejected): allowed as T3 compute providers.
- Packs execute in-process (`plugins/packs.py`): replaced by T1 subprocess.
- The QMA runtime ADs listed at the top: superseded by library equivalents (section 3).
- DEC-0117 (no database server) is kept: SQLite and DuckDB only.

## 11. Open items (not blocking packets 01–08)

- Whether `sqlite-vec` loads on Windows. Spike before turning on semantic memory search.
- MCP Apps rendering in the Svelte UI: build on the official AppBridge, since LangGraph React support is unmerged and the UI is Svelte anyway.
- Which app proves the concept end to end. Proposal: Macro daily bias, as an agent app with screens, its own data and a schedule.
