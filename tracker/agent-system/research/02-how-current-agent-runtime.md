---
label: wayfinder:research
created: 2026-10-12
feeds: tickets/02-harness-choice.md
source: origin/rebuild/base @ 1cc46f9c (P16c PRs #58-#62 merged). The new-runtime files are identical in this worktree (plan/agent-system @ 3e006948).
---

# How QMX's agent runtime works today (input to ticket 02)

## Summary in plain words

1. Every new QMX agent is a LangGraph graph built by Deep Agents. One builder makes it: `build_agent` in `spec.py`.
2. Agents are described in small YAML files. Each names a model tier, its tools, its sub-agents and its limits.
3. One router picks the model. Today's "daily" profile sends every call through a local CLIProxy at `127.0.0.1:8317`.
4. **Nothing in the product starts a copilot turn yet.** Only a test script and the unit tests do. The server can store chat blocks, but nothing runs the agent when a message arrives.
5. The chat log the UI reads is a SQLite table in qmx-control. The UI follows it over SSE.
6. Hooks (P20) are LangChain middleware wrapped around each model call and tool call.
7. Sub-agents use the Deep Agents `task` tool. Each named sub-agent has its own model on paper. But a copilot turn forces one tier onto all of them (see section 2).
8. The Lab workflow compiler exists (P10). The server's workflow API still answers `not_implemented` (501).
9. Option B plugs in at one seam: `build_agent` returning a Claude Code runnable for a spec marked `engine: claude-code`. Option C also needs that, plus a second copilot path.
10. The old QMA daemon is still started by `qmb host start`. The new `qmx-control start` replaces start/stop/status only, not pairing or recovery. The old daemon also holds the only Claude Code and Codex worker code QMX has ever written, and P16 plans to delete it.

## The picture

```
 UI (not wired yet on rebuild/base)
   |  POST /api/sessions/{id}/blocks   -> only stores the block, runs nothing
   |  GET  /api/events/sessions?subject=<id>  (SSE, polls SQLite every 50 ms)
   v
 qmx-control  (FastAPI + FastMCP, control.db: sessions, blocks, events, work)
   ^  sessions_append(...)                    ^ apps_call("execute") for sandbox
   |                                          |
 [MISSING: a turn host]  <- today only scripts/live/copilot_build_app.py
   |  build_copilot(ctx) -> stream_turn(graph, ...)
   v
 qmx_agents.spec.build_agent  --> deepagents.create_deep_agent(...)
   |-- model     : ModelRouter (router.py, models.yaml)  -> CLIProxy / OpenRouter / APIs
   |-- tools     : qmx_tools registry + in-process FastMCP servers + settings MCP + memory tools
   |-- middleware: journal, router, context editing, memory+summary, money path, app hooks, limits, approvals
   |-- subagents : researcher, data-analyst, app-builder (CompiledSubAgent) + general-purpose
   `-- checkpointer: LangGraph SQLite, thread_id = session_id
```

## 1. What runs an agent today

### Packages and versions
- `qmx-agents` pins `deepagents==0.7.22`, `langgraph==1.2.14`, `langchain==1.4.3`, `langchain-anthropic==1.7.5`, `langchain-openai==1.6.7` (`qmx-agents/packages/qmx-agents/pyproject.toml:7-17`).
- `qmx-control` is the node's API: REST, SSE and MCP (`qmx-control/src/qmx_control/server.py`).
- `qmx-apps` runs mini-apps under a supervisor. It only imports guard helpers from qmx-agents (`qmx_apps/supervisor.py:29`, `road/__init__.py:11`). Example apps build their own Deep Agents in-process (`examples/apps/weekend-watcher/server.py:14-15`).
- `qmx-remote` runs an agent on a remote box with the same builder (`qmx_remote/worker.py:184-209`).

Paths below are under `qmx-agents/packages/` unless stated.

### Who starts a copilot turn
- `build_copilot` loads `agents/copilot.yaml`, adds the in-process MCP servers (`qmx-control`, `qmx-data`, `qmx-backtest`, `qmx-research`) and calls `build_agent` (`qmx-agents/src/qmx_agents/copilot.py:54-95`).
- `stream_turn` runs one turn. It writes the user block, streams the graph and copies each finished message into the session log (`copilot.py:98-213`).
- **The only callers are `scripts/live/copilot_build_app.py:60-76` (repo root) and tests.** qmx-control never imports `qmx_agents`. `POST /api/sessions/{id}/blocks` only appends a row (`qmx-control/src/qmx_control/service.py:324-335`). Approvals are answered on the script's stdin (`copilot_build_app.py:64-76`).
- P16c PR #59 deleted the old copilot host (`qma/daemon/sessions/copilot.py`, 692 lines). No new host took its place.

### How a thread or session is stored
Three stores, all keyed by the same session id:
- **LangGraph checkpoints.** `thread_id = session_id` (`copilot.py:108`). The script puts them in `<home>/copilot/threads.db` (`copilot_build_app.py:43-51`). Each background task gets its own file, `<home>/copilot/tasks/<run>/threads.db` (`tasks.py:127-136`).
- **The chat log the UI sees.** `sessions` and `blocks` tables in `control.db`, append-only, with typed blocks such as `text`, `tool`, `agents`, `permission`, `needs_you` (`service.py:47-73`, `120-123`, `300-342`). A sub-agent gets a child session with `parent_id` (`copilot.py:133-145`).
- **The run journal.** `<home>/runs/<session>/journal.jsonl` (`copilot.py:61-65`). The journal records every model call with its `usage_metadata` (`guards/middleware.py:104-121`).

### How the UI receives events
- Every append also writes an `events` row (`service.py:156-169`).
- `GET /api/events/{topic}` is SSE. It polls that table every 50 ms (`server.py:215-228`, `service.py:187-198`).
- `stream_turn` uses `stream_mode="updates"` (`copilot.py:128-130`). The UI therefore gets whole messages, not tokens.
- No UI code on rebuild/base calls these endpoints yet (grep for `api/sessions` and `api/events` under `apps/` found nothing).

### How tools are registered
`_build` (`spec.py:246-291`) collects tools from:
- the names in the spec's `tools:` list, taken from `qmx_tools.default_tool_registry` (`spec.py:148`, `253`; `qmx_tools/registry.py:274`);
- in-process FastMCP servers, read through `langchain.mcp.MCPAdapter` (`spec.py:263-277`; `qmx_tools/servers.py`; `copilot.py:66-69`). Tool names get a `qmx-data_` style prefix, except qmx-control's;
- external MCP servers from `models.yaml` and `settings.toml`. Credentials come from Credential Manager `qmx/<name>` (`spec.py:197-243`). Firecrawl is wired but off by default (`router.py:33-37`);
- broker tools. The broker's own `propose_order` is dropped and a local proposal tool is added instead (`spec.py:278-290`);
- memory tools (`spec.py:378-384`) and `start_task` for background agents (`spec.py:254-259`, `tasks.py:31-60`);
- Deep Agents built-ins: file tools, `write_todos`, `task`, and `execute` when the backend is a sandbox. The copilot's sandbox runs commands through a supervised mini-app (`copilot.py:30-51`).
- Every tool passes the money-path check at build time and again on each call (`spec.py:291-295`, `guards/middleware.py:34-72`).

### How hooks (P20) fire
They are middleware, assembled per agent in `guards()` (`spec.py:401-428`). In order:
1. `JournalMiddleware`: before and after the agent, each model call and each tool call (`guards/middleware.py:74-206`).
2. Router middleware, then fallback and retry (`router.py:205-278`).
3. `ContextEditingMiddleware`, on the copilot only (`spec.py:406-407`).
4. Memory middleware and the summary wrapper (`spec.py:408-409`).
5. `AdmissionStateMiddleware` and `MoneyPathMiddleware` (`guards/middleware.py:28-72`).
6. `AppHooksMiddleware`: before `apps_publish`, tests must be green. After `apps_create`/`apps_update`, tests run automatically (`guards/hooks.py:22-150`).
7. `ResearchLibraryMiddleware` when Firecrawl is on (`spec.py:416-417`).
8. Call limits from the spec's `budget` (`spec.py:418-425`).
9. `JournalApprovals`, a human-in-the-loop middleware for `interrupt_on` tools (`guards/middleware.py:208-237`).

Outside the middleware:
- When an app breaker trips, a `needs_you` block is posted, between turns too (`guards/hooks.py:153-179`, wired through `service.py:839-860`).
- Before compaction, memory's `on_pre_compress` runs (`memory.py:640-678`).

### How the model is chosen
- A spec names `tier:<fast|workhorse|coding|reasoning_high>` or `provider:<exact id>` (`router.py:40-52`). The providers are `anthropic`, `openai`, `openrouter`, `local` and `cliproxy`.
- Override order: base, then node, app, workflow, agent node, sub-agent. A per-request model beats them all (`router.py:194-203`).
- The "daily" profile maps `reasoning_high` to `cliproxy:claude-opus-5-5` and the other tiers to GPT-6.x, all through CLIProxy (`qmx-agents/src/qmx_agents/models.yaml:1-14`).
- CLIProxy Claude ids go to `ChatAnthropic` and the rest to `ChatOpenAI` (`router.py:181-186`).
- `stream_turn` always sets the per-request model: `reasoning_high` in "plan" mode, otherwise `workhorse` (`copilot.py:105-113`). So in a normal turn the copilot runs on GPT-6.1 (workhorse), not the Opus its YAML names.

### How caching and compaction are configured
- **Caching.** QMX configures none. Deep Agents adds `AnthropicPromptCachingMiddleware` to every agent, and it does nothing on non-Anthropic models (installed deepagents 0.7.21, `deepagents/graph.py:389`, docstring). Claude through CLIProxy uses `ChatAnthropic`, so the cache markers should apply (INFERRED, not measured).
- **Compaction.** Deep Agents' default summarisation is wrapped by `_MemorySummarization` so memory can save facts first (`memory.py:520-530`, `648-678`). It keeps the default keep-tail behaviour, which the audit (LCS §a10) calls unsafe for Opus 5.5. The copilot also gets `ContextEditingMiddleware`, which clears old tool results (`spec.py:406-407`). No trigger sizes are set anywhere in QMX.

## 2. Sub-agents today

- **Named sub-agents.** `subagents: [ref: researcher.yaml, ...]` are built recursively by the same `_build`. Each becomes a `CompiledSubAgent` with its own tools, memory scope, budget and guards (`spec.py:297-324`). Cycles are refused (`spec.py:300-301`).
- **Workflow sub-agents.** A spec may name `workflow:` instead. The compiled LangGraph workflow becomes a sub-agent (`spec.py:325-335`; `workflows/compiler.py:312-334`).
- **General-purpose sub-agent.** Every agent also gets one. It uses the parent's model, tools and guards (`spec.py:444-476`).
- **Background tasks.** `start_task` is a different path. It starts a whole agent in an asyncio task with its own checkpoint file and a child session (`tasks.py:31-151`).
- **Can a sub-agent use another provider?** On paper, yes. The child's `model` goes into `RunContext.subagent` and is resolved by the same router (`spec.py:303-308`, `338-339`). Any of the five providers works, so a GPT lead with a Claude researcher is expressible today.
- **In practice, not inside a copilot turn.** `stream_turn` sets `request_model`, and that beats `subagent` (`router.py:199-200`). LangGraph 1.2 merges the parent's runtime context into nested graphs (`langgraph/pregel/main.py:2866-2882`). So the sub-agent's router reads the parent's `request_model` and runs on the turn's tier. INFERRED from the code. No test covers it (`tests/test_router.py:66-74` only tests a single agent).
- **Nesting.** Every child also gets its own general-purpose sub-agent, because `general_purpose_subagent` is inherited (`spec.py:310-317`, `453-476`). So sub-agents can spawn sub-agents today. Workflow agent nodes default this to off (`workflows/models.py:103`).

## 3. The Lab workflow path

- **Confirmed.** `workflows_get`, `workflows_put`, `workflows_validate` and `workflows_run` all raise `not_implemented` with HTTP 501, naming "P10" or "P10/P22" (`qmx-control/src/qmx_control/service.py:880-894`, through `_unavailable` at `644-647`). The routes are registered at `server.py:47-50`.
- **What exists (P10).**
  - `workflow.v1` models with node kinds `python`, `agent`, `tool`, `app_call`, `condition`, `parallel`, `join`, `loop`, `human_gate` and `subworkflow`, plus topology and port checks (`workflows/models.py:11-289`).
  - A compiler to a LangGraph `StateGraph` with a checkpointer (`workflows/compiler.py:277-310`).
  - `to_python` for the UI's Code view (`compiler.py:337`).
  - A run API with start, resume, cancel and status (`workflows/runs.py:21-124`).
- **What is missing.** Storage for workflow definitions, the bridge from qmx-control to `WorkflowRuns`, and run events into the session or runs log.
- **Where the graph layer lives.** It already lives in `qmx_agents.workflows`. An `agent` node calls `build_agent` and then `ainvoke` (`compiler.py:189-199`). Wiring it to the API needs a host that owns both qmx-control and qmx-agents. That is the same missing host as in section 1.
- The packages already import in a circle: qmx-control depends on qmx-apps (`qmx-control/pyproject.toml:15`), qmx-apps on qmx-agents (`qmx-apps/pyproject.toml:15`), and qmx-agents imports qmx_control (`spec.py:35`, `copilot.py:16-18`). Adding the host inside qmx-control would deepen that circle.

## 4. Where a Claude Code worker plugs in

### Option B (LangGraph + Deep Agents base, Claude Code and Codex as workers)

**The seam is `build_agent` / `_build` in `spec.py:190-499`.** Every runner calls it:
- the copilot (`copilot.py:95`);
- named sub-agents (`spec.py:309-323`);
- background tasks (`tasks.py:135`);
- workflow `agent` nodes (`compiler.py:173`, `196`);
- remote runs (`qmx_remote/worker.py:199`);
- example apps.

Proposed shape (design sketch, not built):
- Add `engine: deepagents | claude-code | codex` to `AgentSpec` (`spec.py:108-126`).
- For `claude-code`, `_build` returns a LangChain `Runnable` instead of `create_deep_agent(...)`. Input is `{"messages": [...]}` and output is `{"messages": [...]}`, the contract `CompiledSubAgent` and the compiler already use.
- Inside, it starts a Claude Agent SDK session with:
  - QMX tools served as one MCP server from the same registry and FastMCP servers (`qmx_tools/servers.py` already builds them);
  - `CLAUDE_CONFIG_DIR` and `setting_sources=[]` for isolation;
  - `can_use_tool` and PreToolUse hooks that call the same `check_tool` and app-hook logic;
  - stream messages mapped onto `sessions_append` blocks in a child session, the way `stream_turn` does at `copilot.py:132-207`;
  - SDK `ResultMessage` usage written to the run journal.

Three things the seam does not give for free:
- **Approvals.** A LangGraph `interrupt()` inside a node replays the node from the start on resume. That would restart the Claude Code session. The worker must hold its approval inside `can_use_tool`, waiting on a QMX approval record, rather than use `interrupt()` (INFERRED from LangGraph's documented resume behaviour).
- **Events.** Updates from a worker running inside `task` do not show up as LangGraph sub-graph namespaces. The worker must write its own blocks.
- **Sandbox and research hooks.** Claude Code's own Bash and WebFetch bypass `AppSandbox` (`copilot.py:30-51`) and `ResearchLibraryMiddleware` (`spec.py:416-417`). Either turn those built-ins off (the old driver used `tools=[]`) or redo the rules as SDK hooks.

Prior art exists. The old daemon's `qma/daemon/request_runtime/native_claude.py` (435 lines, `claude-agent-sdk==0.2.163`) already does isolation and MCP-only tools:
- `CLAUDE_CONFIG_DIR` at lines 121 and 275;
- `tools=[]` at line 245;
- `setting_sources=[]` at line 261;
- `create_sdk_mcp_server` at line 268.

`native_codex.py` (553 lines) and `native_sessions.py` (446 lines) sit beside it.

Packets touched under B, roughly:

| Packet | Change |
|---|---|
| P06 spec and router | `engine` field; the Claude route goes through the SDK, not CLIProxy |
| P08 guards, P20 hooks | the same rule code exposed as SDK hooks and `can_use_tool` |
| P09 tools | none, served over MCP as now |
| P10 workflows | none; an `agent` node with a worker spec just works |
| P11 control | the turn host and approval records (needed in any option) |
| P12/P17 sandbox | decide where Claude Code's shell runs |
| P15 copilot | none, unless the copilot itself becomes a worker |
| P19 research | Library saving for worker web results |
| P21 remote | the worker needs the `claude` binary and sign-in on the target |
| P22 run index | the worker's usage into the journal and ledger |
| P07 memory, P13/P14 apps, P18 brokers | none |

### Option C (copilots on Claude Code, workflow and server agents on LangGraph)

Everything in B, plus:
- **P15:** `build_copilot` and `stream_turn` get a second implementation, an SDK session builder and an SDK-to-block mapper (`copilot.py:54-213`).
- **P06:** `copilot.yaml`'s Deep Agents sub-agents (`agents/copilot.yaml:8-11`) become SDK agent definitions. Router tiers no longer decide the copilot's model.
- **P07:** memory (Store-based, `memory.py`) must be reachable from the SDK session as MCP tools. The pre-compress hook moves to the SDK's PreCompact.
- **P08/P20:** guards kept twice, as middleware and as SDK hooks, fed by one rule module, with tests on both paths.
- **P11/ticket 11:** the session log normalises two event streams.
- **P24 (on hold):** its plan assumes LangChain middleware (`rebuild/packets/P24-copilot-modes-and-hooks.md`). It would need a rewrite.
- Kept as is: P09, P10, P12-P14, P17, P18, P21 (Deep Agents remote runs), P22's Library.

## 5. What still depends on the old QMA runtime

- **Confirmed.** `qmb/src/qmb/doors/cli/host.py:104` sets `DAEMON_SPAWN_MODULE = "qma.daemon"`. `_spawn_argv` builds `python -m qma.daemon` (`host.py:689-693`). `invoke_host_start` (`host.py:886`, spawning at `938-941`) and `invoke_host_recover_control` (`host.py:1702`, spawning at `1746`) launch it.
- The other `invoke_host_*` functions talk to the running daemon over its control socket: status, stop, configure (four kinds), pair, pair-revoke and rotate-control (`host.py:1011-1649`).
- `qmb/src/qmb/doors/cli/tree.py:116` wires them into the `qmb host ...` CLI.
- The old QMA source is still 116,780 lines across `qma-core`, `qma-daemon` and `qma-wire` (`src/` only, counted on base).
- **Replacement status: partial.** `qmx-control start|status|stop|serve` is "a small replacement host door" (`qmx-control/src/qmx_control/__main__.py:1`, `22-60`).
  - There is no new equivalent for pair, pair-revoke, rotate-control, recover-control or the configure commands.
  - The P16 plan says so itself. Changing the spawn constant is not enough, and a separate caller-migration packet is needed (`rebuild/reports/p16-deletion-plan.md:46`, also `:110-111`).
  - None of this is agent runtime. The new agent code does not import `qma` (grep of `qmx-*/src` found nothing).
- **The harness-relevant dependency is the other way round.** The P16 plan lists `native_claude.py`, `native_codex.py` and `native_sessions.py` for deletion. It names `ModelRouter` and `build_agent` as their replacements (`p16-deletion-plan.md:178-183`). Neither one runs Claude Code or Codex. Under option B or C, those files are the closest existing reference. Harvest them before the deletion lands, or accept recovering them from git history.

## 6. Surprises

1. **No turn host exists.** Every option, A, B or C, must first build "a message arrives, so run a turn, stream blocks, handle approvals". That host is where the B/C choice is actually implemented. It is not yet a packet.
2. **The per-request model beats the per-agent model.** Today the copilot runs on the workhorse tier (GPT-6.1 via CLIProxy), and so do its sub-agents (section 2). This undercuts the map's "a sub-agent can have its own provider" premise for copilot turns until `router.py:199-200` changes. The fix is small, but it is a rule to decide: should a turn's choice reach sub-agents?
3. **Claude already runs through CLIProxy** (`models.yaml:4`, `14`). The audit's row 26 says subscription use is not allowed on the LangGraph path. If CLIProxy fronts subscription accounts, which its accounts and quota endpoints suggest (`router.py:288-302`, INFERRED), the current daily profile already sits in that grey zone. Ticket 06 should rule on it.
4. **"No modes" versus the code.** `stream_turn(mode="plan"|"do")` still exists and switches the tier (`copilot.py:105-113`). P24 is on hold because modes were withdrawn.
5. **Sub-agents can spawn sub-agents** (section 2). The map's cost rule says a subagent never does. Under B, a Claude Code worker would also get Claude Code's own Agent tool unless it is turned off.
6. **Approvals and LangGraph replay** (section 4). A Claude Code worker must not use `interrupt()` mid-session.
7. **Compaction is still keep-tail on Opus routes** (`memory.py:520-530`). Under B this stays QMX's job for Deep Agents agents (LCS §d BUILD 2). Under C, Claude copilots escape it.
8. **No token streaming.** Ticket 11's "feels like Claude Code" chat needs `messages` or `custom` stream modes. Updates mode alone is not enough (`copilot.py:128-130`).
9. **The P16 deletion plan names the wrong replacement for the native workers** (section 5). Deleting them removes the only tested isolation recipe for running Claude Code beside the operator's own install.

## Where things live

| What | Where (under `qmx-agents/packages/`) |
|---|---|
| Agent builder, the seam | `qmx-agents/src/qmx_agents/spec.py` |
| Copilot composition and turn streaming | `qmx-agents/src/qmx_agents/copilot.py`, `agents/*.yaml`, `skills/` |
| Model routing and profiles | `qmx-agents/src/qmx_agents/router.py`, `models.yaml` |
| Hooks and guards | `qmx-agents/src/qmx_agents/guards/` |
| Memory and compaction wrapper | `qmx-agents/src/qmx_agents/memory.py` |
| Background agents | `qmx-agents/src/qmx_agents/tasks.py` |
| Lab workflows | `qmx-agents/src/qmx_agents/workflows/` |
| Session log, SSE, workflow stubs | `qmx-control/src/qmx_control/service.py`, `server.py` |
| Domain tools and MCP servers | `qmx-tools/src/qmx_tools/` |
| Remote agent runs | `qmx-remote/src/qmx_remote/worker.py` |
| Old Claude Code and Codex drivers (P16 delete list) | `qma-daemon/src/qma/daemon/request_runtime/native_*.py` |
| Old host spawn | `qmb/src/qmb/doors/cli/host.py` (repo root) |
