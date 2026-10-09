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
| Tool registry and MCP adapter layer | **Replace** with per-agent `tools=` and LangChain's built-in `MCPAdapter` (`langchain[mcp]`) | |
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
background_tasks: [agents/overnight-sweep.yaml]   # run via QMX background tasks (§5.2)
interrupt_on: { promote_strategy: true, publish_mini_app: true }
permissions: { write: ["/artifacts/**"], deny_write: ["/data/**"] }
budget: { model_calls: 200, tool_calls: 400 }
```

- **Deep Agents is the default agent type.** The general-purpose sub-agent stays on for the Copilot and is off inside workflow nodes unless the spec turns it on.
- **Specific tools, MCPs and data per agent:**
  - Tools: `SubAgent.tools` replaces inherited tools.
  - MCP: one `langchain.mcp.MCPAdapter` per spec. The old `langchain-mcp-adapters` package is unmaintained.
  - Data: a `CompositeBackend` route plus `permissions`.
- Per-run identity (session, workflow, task, app) travels in `context_schema`.

### 5.2 Delegation

| Need | Mechanism |
|---|---|
| Quick isolated job (look-up, short research) | sync `SubAgent` through the `task` tool |
| Long job (sweep, app build, overnight) | QMX background tasks: `start_task`, `check_task`, `cancel_task`, `list_tasks` tools, backed by `qmx-control` runs, which run a compiled sub-agent or workflow in the background. Feeds the UI "Activity / jobs" panel. Deep Agents' `AsyncSubAgent` is not used because it needs an Agent Protocol server (§12b) |
| Fixed pipeline (ingest → backtest → tearsheet) | `CompiledSubAgent` wrapping a LangGraph workflow |
| Bulk coverage (every symbol or fold) | `CodeInterpreterMiddleware` fan-out, with the interpreter tool gated |
| Irreversible decision | escalate to a high-reasoning model, or ask the operator via `interrupt_on` |

Sub-agents hand results back as **artifact references** (paths in the artifact store), not long text.

### 5.3 Model router

- `init_chat_model("provider:model")` per tier.
- Tiers: `fast`, `workhorse`, `coding`, `reasoning_high`.
- Routing via `@wrap_model_call` (a 20-line custom router). LangChain's experimental router middleware may replace it later.
- `ModelFallbackMiddleware` and `ModelRetryMiddleware` for resilience.
- **The primary provider is CLIProxyAPI** (github.com/router-for-me/CLIProxyAPI), the operator's daily path.
  - It runs locally, or on a server in Docker, and exposes OpenAI-, Claude- and Gemini-compatible endpoints backed by the operator's subscriptions: Claude Code login, Codex/ChatGPT login, and others.
  - It rotates across several accounts and fails over between them. Its own dashboard manages accounts.
  - QMX treats it like any API: `ChatAnthropic(base_url=<proxy>)` for Claude models, `ChatOpenAI(base_url=<proxy>)` for GPT models.
  - QMX Settings stores the proxy URL and key and lists the models the proxy offers.
  - Details are in `research/cliproxy-video.md`, from the T3 Code video plus the repo source (v8.0.17).
    - **Endpoints:** `/v1/messages` (Claude), `/v1/chat/completions` and `/v1/responses` (OpenAI), `/v1/models`. The default port is 8317.
    - **QMX clients:** `ChatAnthropic(base_url="http://<host>:8317")` and `ChatOpenAI(base_url="http://<host>:8317/v1")`, both with a client key.
    - **Model ids** come from the proxy's catalog, for example `claude-opus-5-5` and `gpt-6.1-sol`. A suffix such as `gpt-6.1-sol(high)` sets reasoning effort.
  - **Recommended proxy settings** (what the video uses):
    - spend the account whose quota resets soonest first
    - session affinity on, so a thread stays on one account and keeps its cache
    - WebSocket on for Codex
  - **Dashboard in QMX:** a native Settings panel that calls the proxy's management API through the QMX backend. It shows accounts, quota bars for the 5-hour and 7-day windows, and login buttons. The official console can also open as a pop-up window, as a fallback.
    - The proxy keeps no usage history, so QMX records tokens and cost per run itself (journal, P08).
  - **Test before relying on it (P06 smoke):** by default the proxy can rewrite or wrap a non-Claude-Code client's system prompt (`disable-claude-cloak-mode`). Check that the Copilot's prompt reaches the model intact, and set the option accordingly.
  - The video's creator runs the proxy on a home connection rather than a cloud VPS. Remote runs can reach the laptop's proxy over Tailscale while it's on, or use a proxy on the VPS; that's the operator's choice in Settings.
- Default daily models, via CLIProxy:

  | Use | Model |
  |---|---|
  | Copilot (main agent, planning, decisions) | Claude Opus 5.5 |
  | Sub-agents, and agents inside workflows and apps | GPT-6.1 Sol |
  | Quick, high-volume steps | GPT-6 Luna |

- **Models are never hard-coded. Every level can override the one above:**
  - global profile → node (laptop or a given server) → app → workflow → agent node → sub-agent
  - Each level may set a tier or an exact `provider:model`, for example Kimi K3 for one workflow.
  - The effective model for any run is resolved from that chain and recorded in the journal.
  - Settings shows the chain and lets the operator change any level.
- **The test profile is OpenRouter** (API key), only for smoke runs during development. It is never the default. Automated tests use fake models.
- Other providers (Anthropic API, OpenAI API, local OpenAI-compatible) are optional entries. All keys and proxy credentials come from Windows Credential Manager `qmx/*`.

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

### 5.6b Agent tool catalogue (what agents can actually do)

Agents get tools from a short list of kinds. Each AgentSpec picks from these, and nothing else exists:

| Kind | Examples | Notes |
|---|---|---|
| Domain | `qmx-data`, `qmx-backtest`, `qmx-research`, `qmx-broker` (read + propose only) | P09, P18 |
| Platform | `qmx-control` (apps, workflows, runs, library, settings) | the same API as the UI (§8) |
| Files and artifacts | Deep Agents filesystem tools over the `CompositeBackend` routes | writes go through the admission wrapper |
| Code execution | a Python sandbox (`execute`) on a **target**: laptop T1, a VPS (T2 Docker), or a GPU target | the RLM-style data analyst lives here |
| Jobs on a target | `run_job(target, image or app, command, resources)`, then `job_status`, `job_logs`, `job_fetch` | for long or heavy work; the job is recorded automatically by the supervisor |
| Web | Firecrawl MCP (paid, opt-in), plain fetch, a browser MCP (Playwright) | results saved to the Library |
| External MCP | anything the operator adds in Settings | per-agent allow-list |

**GPUs.**
- The node bootstrap detects an NVIDIA GPU and installs the NVIDIA container toolkit, and the node advertises `gpu: <model>, <count>`.
- Jobs and sandboxes declare `resources: {gpu: 1}`. The supervisor only places them on a node that has one; otherwise it uses a GPU compute provider (for example a rented GPU box) configured in Settings.
- **When a GPU is actually needed:** training neural networks, fine-tuning or hosting local LLMs, and large deep-learning sweeps. Not needed for backtests, classical ML (gradient boosting, linear models, scikit-learn) or running small trained models.
- **Train once, run anywhere (ONNX).** Trained models are exported to ONNX (Open Neural Network Exchange) and run with ONNX Runtime on an ordinary CPU, on the laptop, a VPS or a trading node. A GPU is rented by the hour only for training. No GPU provider is set up until the first such job exists.
- Models are Library artifacts of type `model`: the ONNX file, its training run, data snapshot, metrics and version. Pretrained models (for example from Hugging Face) are imported the same way.
- Agents never configure drivers. They ask for a GPU target through `run_job`, and the platform handles the rest.

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

### 7.6b The whole data map (every store, its owner, its cache)

Rule zero: **everything is files.** SQLite, DuckDB over Parquet, JSONL and content-addressed blobs. There is no database server. Each file has exactly one writer process, and everyone else reads it or asks the owner through `qmx-control`.

| Data | Store | Owner (single writer) | Who reads | Cache | Backup |
|---|---|---|---|---|---|
| Market data (bars, ticks, features, calendars) | Parquet partitions + DuckDB views (`qmf-data` store, exists today) | the data ingest job | agents and apps via `qmx-data`, backtests | none needed: the store *is* the cache of the upstream feeds | Parquet is immutable, so sync it to the bucket. It can be re-downloaded, so it never goes to GitHub |
| Backtest and research results | QMB results and ledger (exists) plus artifacts | QMB | Lab, Library, agents | **result memo**: same strategy version + data snapshot + params = reuse the old result, never recompute | bucket |
| Experiments (the scientist's notebook) | Experiment Ledger, SQLite (kept per §12) | QMA guards (P08) | Lab, Library | none | bucket + GitHub weekly |
| Library (every saved thing: reports, notes, scraped articles, datasets, app outputs) | `artifacts/<sha256>` blobs + `library.db` (SQLite with full-text search; vectors later) | Library service in `qmx-control` | everyone | the catalog is the index; nothing extra | catalog → bucket + GitHub weekly; blobs → bucket |
| Lab objects (strategies, pods, versions) | typed, versioned Library artifacts | Library service | Lab, agents, Portfolio | none | as Library |
| Portfolio and live trading state | QMN's own journal and ledgers on each trading node (exists) | QMN on that node | laptop via `qmx-control` read-only views | short in-process TTL for summaries, refreshed by events | per node: bucket, plus Litestream on Linux |
| Copilot sessions and agent threads | LangGraph checkpoints `copilot/threads.db` | qmx-agents | UI via SSE | none | bucket |
| Agent memory | `memory.db` per profile (copilot, each app) | MemoryManager (P07) | its agents | prefetch only | bucket + GitHub weekly |
| Run journal (evidence) | JSONL per run + `runs.db` index | guards middleware (P08) | UI, Library, audits | none | bucket + GitHub weekly |
| Workflow definitions | JSON files, versioned as Library artifacts or inside an app | Library or the app | compiler | none | as owner |
| Workflow run state | LangGraph checkpoints in the owning app's volume, or `workflows/<id>/checkpoints.db` | the run | resume logic | none | bucket |
| Mini app data | the app's volume: `app.db`, `memory.db`, `data/`, `blobs/` | the app instance | the app; others only via its MCP tools or artifact refs | the app's choice (in-process TTL, durable rows with `fetched_at`) | bucket (+ Litestream for money apps) |
| Settings | `settings.toml` (UI-editable) | `qmx-control` | everyone | loaded once, reloaded on change | GitHub weekly |
| Secrets | Windows Credential Manager `qmx/*`; node vault on servers | operator | providers at call time | never cached on disk | never backed up anywhere outside the vault |
| Logs, metrics, traces | JSONL per process; traces to LangSmith or an OTel file | supervisor | UI, debugging | none | bucket, 30-day retention |

**Where caching is worth it** (and nowhere else):
1. **Upstream data:** fetched once into the market store; Firecrawl and web results are saved to the Library keyed by URL and date.
2. **Backtest results**, memoized by content keys.
3. **Model prompts:** the provider's prompt caching (automatic for Claude through Deep Agents). No response caching of model output.
4. **Expensive read tools** (news, quotes): an in-process TTL cache inside the tool.
5. **UI aggregates** (portfolio summary, app health): an in-process TTL cache in `qmx-control`, invalidated by events. The UI gets pushes over SSE, never polls.

No Redis, no shared cache server.

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

## 11. Operator additions (2026-10-07, after first draft)

- **Mini apps are not "just extensions".** The VS Code extension comparison is one useful analogy, not the definition. The definition is §7.1: one container-like shape (definition, instance, own data) with optional parts, such as agents, workflows, screens, jobs and tools. The shape covers apps with agents, apps without agents, headless services and trading nodes. The UI's Apps section is work in progress and its look will change; the UI follows this logic later.
- **The Copilot gets skills and hooks for building mini apps.** Skills are written with intent by Claude with the operator (P20), not generated in bulk.
  - Skills: build-mini-app, build-workflow, debug-app, publish-checklist, connect-broker.
  - Hooks are LangChain middleware events:
    - before publish: manifest valid, tests green
    - after tool: journal
    - money-path block
    - breaker trip: tell the Copilot and the operator
    - pre-compaction: memory
- **Brokers are back to CFDs.**
  - IC Markets via cTrader Open API. The adapter already exists in `packages/qmf-venue/src/qmf/venue/ctrader.py`.
  - Crypto via CCXT, already in `qmf-venue` and `qmn/venue/spot_paper.py`.
  - Model: many brokers, many connections, many accounts per connection.
  - Hummingbot is a reference for crypto connectors and strategy ideas.
  - A cTrader MCP server is on by default for the Copilot: read-only market and account tools, plus `propose_order`. The money path still needs the operator's signature.
- **Research sources.**
  - Firecrawl MCP is a paid provider the operator approves, including Alexandria data providers.
  - QMX's own scraper runs as a scheduled job (a headless mini app). Its first target is MQL5 articles; the existing library lives on branch `research/mql5-article-library`.
- **Charting.** This is a UI-lane decision. Recommendation: TradingView Lightweight Charts (open source, Apache-2.0) for all price charts. TradingView Advanced Charts needs a licence application, so consider it only if Lightweight falls short. The backend serves bars and indicators through `qmx-data`.

## 11b. Remote runs (laptop off, work continues)

The goal: from the UI, send a job to a server. It sets itself up, works with the laptop off, and every result, log and trace can be recovered afterwards. Think of it like Git: the server does work and "pushes"; QMX "fetches" when it's back.

**Two kinds of remote target, behind one `ComputeProvider` interface** (`provision`, `start`, `status`, `logs`, `stop`, `teardown`):

| Kind | What runs there | Providers |
|---|---|---|
| Machine | QMX's own job: a workflow, app instance or agent run, packaged from the same app/workflow definition | own VPS over SSH or Tailscale (T2 Docker), Modal, E2B, Daytona |
| Remote agent | Amp's agent, given a task and QMX's MCP servers | Amp orbs (managed) or Amp runners (own machine, free) |

**Amp.** Its SDK (TypeScript and Python) runs `execute(prompt, options)` with `executor: "orb"` or `executor: "runner"`, plus an MCP config.
- Orbs sleep when idle at no cost, run a repo setup script (`.agents/setup`) on first start, and can use a ChatGPT subscription.
- Pricing: the free tier is pay-as-you-go for orbs and free on your own runners; $20/month includes 45,000 orb minutes.
- QMX uses Amp for delegated agent tasks (research, coding, long investigations). Machine providers handle pure QMX compute.

**Results, Git-style:**
- Every remote run has a run id and writes a **run manifest**: inputs, versions, status, artifact list with hashes. It is uploaded with **content-addressed artifacts** to the bucket: `s3://<bucket>/runs/<run_id>/`.
- The journal, logs and traces stream to the bucket as they are written. If the server dies, QMX still has everything up to the last flush.
- Workflow checkpoints (LangGraph) are saved to the bucket, so a failed run resumes from its last step on any machine.
- Code changes (agent-written apps or strategies) go to a Git branch named after the run, never straight to the working branch.
- QMX's `fetch` pulls finished runs into the Library and app volumes, verifies hashes and records them in the journal.

**Models on the server.** CLIProxy runs on the server too (Docker), so remote agents use the same subscriptions. Per-run credentials come from the operator's vault, are scoped to that run, and are removed at teardown.

**Own servers (for example the operator's Contabo VPS): one bootstrap command.**
- `qmx node bootstrap <ssh-host>` is an idempotent script; running it twice is safe. It installs:
  - Docker
  - Tailscale (private network to the laptop)
  - the QMX node supervisor as a systemd service
  - CLIProxy in Docker
  - rclone with the bucket settings
  - log and trace shipping
- It ends with `qmx node verify`, which checks each piece and prints a pass/fail list.
- Secrets are typed by the operator in a guided prompt and stored on the node, never in the repo.
- It is written once and tested against a fresh Ubuntu VM, so it is not a one-shot hope. After that, adding a server is one command.
- **Recording is automatic, not agentic.** The supervisor journals every run, log line, metric and artifact on its own. No agent has to remember to record anything.

**Own VPS first.** The operator's VPS is the default remote target. Amp, Modal and E2B are optional extras, for GPU bursts or delegated agent tasks.

**Storage bucket, with three copies:**
1. **Primary bucket on the VPS itself:** a plain directory reached through rclone over SFTP. No object-storage software is needed. Agents on that VPS write results right next to where they run.
2. **Local copies on the laptop:** `fetch` pulls finished runs and nightly snapshots.
3. **Off-site weekly: a private GitHub repo,** the backup of the backup, for the small, precious data:
   - DB snapshots (memory, journal index, Library catalog, Experiment Ledger, app `app.db` files)
   - settings
   - definitions and manifests

   GitHub rejects files over 100 MB and large repos get slow, so bulk data (Parquet, large blobs) never goes there. Market data can be re-downloaded. Large result blobs get a second bucket (any S3-compatible store, swappable in Settings) when needed.

Never keep the only backup on the same server it protects; the copies above make sure of that.

**UI.** "Run on…" picks a target. Jobs show where they run, cost so far, live log tail and status. A failed remote run offers "resume elsewhere".

## 12. Rulings from the P05 survival-map review (Claude, 2026-10-07)

P05 (`reports/survival-map.md`) is approved. These rulings override it where they differ:

1. **No compatibility bridge for the old JSON-RPC wire.** The UI only has a recording transport and no live traffic, and no external host is known. New callers use `qmx-control` (P11), and old wire modules are deleted in P16. The one real caller to migrate is the QMB host CLI (`qmb host start|status|stop|…` spawns `python -m qma.daemon`). P11 adds a `qmx-control` equivalent and P16 moves QMB onto it.
2. **Evidence journal: keep the rules, shrink the machinery.**
   - Port: append-only, monotonic sequence, record fingerprint, serialized writes, failures raised, never silently dropped.
   - Keep the **Experiment Ledger**, the scientist's notebook per experiment, and the "invalid evidence goes to quarantine verbatim, never discarded" rule.
   - **Drop** the Task Ledger and Quant Ledger lease machinery and Quant/Task identities. A LangGraph thread/run id plus app id is the identity now.
   - Fold-contract registries, store-class ownership tables and the governed variable registry are not ported. Settings are plain UI-editable config.
3. **Money-path barrier: port as is.** `qma-core/barriers/money_path.py` and `parent_surfaces.py` are small and correct. Move them into `qmx_agents.guards`, check every resolved LangChain/MCP tool at build time, and keep a check at invoke time.
4. **Admission is an `interrupt_on` plus one backend check.** Proposals are staged, deterministic checks run, the operator approves, before/after records are kept. The `AdmissionPipeline` hook dispatch is not ported.
5. **Mini-app port (P14): no compatibility IDs or schemas.** Port the *rules*: immutable versions, compare-and-swap, strict validation, undo as a new transition. Old schema names and the `dev-factory` host go away.
6. **P04 must stop on fixture-labelled modules that have production callers** (`plugins/lifecycle.py`, `sessions/chrome.py`, `staging/change_request.py`, kit-journey re-exports). Move only the ones with no production importers; list the rest in the PR. They disappear with their callers in P16.
7. **P06 may start as soon as P01 is merged.** It builds a new package and doesn't need P02–P05.

## 12b. Rulings from the docs reference review (Claude, 2026-10-07)

`REFERENCES.md` §0 lists where the official docs differ from this design. Rulings:

1. **MCP client:** use `langchain.mcp.MCPAdapter` (`langchain[mcp]>=1.4.0`). It is beta, but it is the official path; `langchain-mcp-adapters` is unmaintained.
2. **MCP servers:** FastMCP 4.x (`fastmcp>=4,<5`).
3. **Long background work:** QMX background tasks, not Deep Agents `AsyncSubAgent`, which needs an Agent Protocol server.
   - `start_task`, `check_task`, `cancel_task` and `list_tasks` are four tools backed by `qmx-control` runs (P11/P22). Each runs a compiled sub-agent or workflow in the background, with its own checkpointer.
   - The AgentSpec field is `background_tasks`.
4. **Python data work:** `CodeInterpreterMiddleware` is JavaScript (QuickJS). The data analyst uses a **sandbox backend** instead.
   - A small `SandboxBackendProtocol` adapter over the T1 subprocess runner (P12) on the laptop, Docker (P17) on servers, and the Modal or E2B adapters for remote.
   - The JavaScript interpreter is only used for code-driven fan-out of sub-agents, and is gated.
5. **Built-in tools:** `tools=` adds to the Deep Agents built-ins. Specs that must not have shell or file tools exclude them through `HarnessProfile(excluded_tools=...)`. Workflow agent nodes turn off the general-purpose sub-agent.
6. **Amp:** remote runs on orbs or runners ignore SDK-side MCP config. QMX's MCP servers are configured in the Amp project or runner settings, and P21 documents that setup.
7. **Tests:** use a fake chat model subclass that supports `bind_tools`. Anything with approvals uses a checkpointer.
8. **Litestream:** one replica per database (0.5.x). **SSE:** FastAPI's native SSE (≥0.135).

## 12c. Rulings from the P16a deletion-plan review (Claude, 2026-10-09)

The plan (`reports/p16-deletion-plan.md`, 166 candidate modules / 77k LOC) is approved with these rulings. They clear its blockers:

1. **QMB host CLI migrates; the old host protocol goes.**
   - `qmb host start|status|stop` is rewritten to start, check and stop `qmx-control` (`python -m qmx_control`) instead of `python -m qma.daemon`.
   - `pair`, `configure`, `rotate-control`, `recover-control` and the placement commands are removed. The local token replaces pairing, and P21 compute providers replace placement.
   - This is the one authorized change inside `qmb/`, limited to `qmb/src/qmb/doors/cli/` and its tests.
2. **The Experiment Ledger is ported, not kept on the old machinery.** A new `qmx_agents.guards.experiments` module provides:
   - an append-only SQLite notebook per experiment
   - identity by run id and app id, with no leases, actors or Task/Quant ledgers
   - the "invalid evidence goes to quarantine verbatim" rule

   Old experiment modules and their callers move to it, then the old ones are deleted.
3. **Kept from `qma-wire`:** only `money_path_diff.py`, `schemas.py` and the `schema_data/` resources. QMB names the schema id `qma.wire.money_path_field_diff.v1`. Everything else in `qma-wire` follows the plan.
4. **No data migration.** The old daemon stores hold only test and fixture data; the operator never ran the product on real work. Nothing has to be converted or preserved beyond git history.
5. **`qmx-agents/plugins/`:** delete it if no loader or test references it (prove it as P04 did); otherwise retarget its imports to the new packages.
6. **Tests:** delete tests that only cover removed old-runtime behaviour together with that code. Retarget tests that guard surviving behaviour. QA epic suites that exercise removed behaviour are retired with a one-line reason each in the PR. Never lower thresholds.
7. **Order:** one PR per slice, each with `just ci` green:
   1. QMB host migration
   2. Experiment Ledger port
   3. task graph and canonical join
   4. hooks
   5. proxy and native sessions
   6. bus
   7. old memory
   8. old transport and `process.py`
   9. package moves and one lock

   "Keep" modules in the plan that only existed to serve deleted code go in the slice that removes their last caller.

## 13. Open items (not blocking packets 01–08)

- Whether `sqlite-vec` loads on Windows. Spike before turning on semantic memory search.
- MCP Apps rendering in the Svelte UI: build on the official AppBridge, since LangGraph React support is unmerged and the UI is Svelte anyway.
- Which app proves the concept end to end. Proposal: Macro daily bias, as an agent app with screens, its own data and a schedule.
