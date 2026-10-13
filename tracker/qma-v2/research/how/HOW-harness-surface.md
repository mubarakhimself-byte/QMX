---
label: qma-v2:how-harness-surface
created: 2026-10-13
source: origin/rebuild/base @ 4eac8f69, read in D:/QMX-worktrees/harness-survey (read-only)
inputs: how/explorer-control-plane.md, how/explorer-agent-code.md, H3-code-map.md, H1-sdk-facts.md, ARCHITECTURE.md §0-§2.0
method: synthesis of two explorer reports, with the contested or load-bearing lines re-read in code. Nothing was run.
---

# How a chat session flows through QMX today, and where qma2 plugs in

Path keys: `CTL/` = `qmx-agents/packages/qmx-control/src/qmx_control/`, `QA/` = `qmx-agents/packages/qmx-agents/src/qmx_agents/` (the LangChain core), `RR/` = `qmx-agents/packages/qma-daemon/src/qma/daemon/request_runtime/`, `TOOLS/` = `qmx-agents/packages/qmx-tools/src/qmx_tools/`. "Inferred" means I reasoned it from reading and did not run it.

## Overview

QMX already has a working session store but no harness. `qmx-control` is a FastAPI process on 127.0.0.1:8766. It keeps sessions and an append-only list of typed blocks in `~/.qmx/control.db`, and streams them over SSE. One registry, `OPERATIONS`, publishes each service method as both a REST route and an MCP tool. Any client can create a session and append blocks, and any SSE subscriber sees them within about 50 ms. Nothing in the control plane drives a model. It has no turn route, no approvals table or answer route, no usage ledger and no account router.

The model-driving code lives in two places that the control plane never calls. The first is the LangChain/Deep Agents copilot (`QA/copilot.py`). Its `stream_turn` is the only existing "engine events → blocks" projector, and its only caller is the operator script `scripts/live/copilot_build_app.py`. The second is the old daemon's native Claude Agent SDK driver (`RR/native_claude.py`). It holds the only Claude SDK recipe (preflight, isolation, event loop). It has run only against fake clients and has never made a live call. qma2 is a new package that `qmx-control` calls. It replaces the copilot as the engine driver, uses `sessions_append`-style projection as its output, and adds the approvals, usage and account state that do not exist anywhere today.

## Key Concepts

- **ControlService** (`CTL/service.py`, 894 lines). This is the whole backend: sessions, blocks, events, runs/jobs work items, settings, Library, apps (through the qmx-apps `Supervisor`) and remote runs. Every REST route and MCP tool is a bound method on it.
- **OPERATIONS** (`CTL/server.py:28-81`). 52 tuples of `(name, method, path, destructive)`. `create_app` binds each row to REST (`:206-213`) and `create_mcp` binds it to MCP (`:120-129`). The comment at `:27` states the rule: "there is no second implementation to drift." Adding a row exposes a method to agents as well as to the UI.
- **Session**. A row `{id, title, origin="copilot", parent_id}` (`service.py:47-51`). It has no status and no timestamps, and there is no get-by-id. A non-null `parent_id` makes a child session. Child sessions are how the old copilot showed delegated sub-agents.
- **Block**. `SessionBlock{type, content}` (`service.py:54-72`). `type` is a closed Literal of 14 kinds: user, text, plan, agents, tool, changed, artifact, table, entity, question, permission, panel, handoff, needs_you. `content` is a free-form JSON dict with no per-kind validation. Blocks are append-only, so a tool call becomes two `tool` blocks (started, then finished) rather than one updated block.
- **Event**. A row in `events(seq, topic, subject, data)`. `topic` is a closed Literal of 7 (`service.py:43`): runs, jobs, sessions, apps, library, settings, aggregates. Every block append writes one `sessions` event whose subject is the session id. SSE is just a cursor over this table.
- **Work + RunJournal**. Runs and jobs reach `runs.db` by two routes: `record_work` rows in control.db, and hash-chained JSONL journals (`QA/guards/journal.py RunJournal`) that `RunIndex.refresh()` projects (`CTL/runs.py`). The one existing cost channel is a journal `model_call` event with `payload.metadata.cost`, summed into `runs.cost` (`runs.py:122-126`).
- **Destructive flag / `interrupt_on`**. 19 of the 52 operations are marked destructive. MCP advertises the flag as both `destructiveHint` and `meta.interrupt_on` (`server.py:126-127`). Nothing reads `meta.interrupt_on`. The approval gating that actually ran was a per-agent YAML `interrupt_on` map wired to LangGraph's `HumanInTheLoopMiddleware` (`QA/guards/middleware.py:208 JournalApprovals`).
- **Secrets**. The OS keyring, with service `qmx/<name>` and username `<name>`. The control token is `qmx/control-token` (`server.py:84-90`). Provider keys go through `QA/router.py credential()`. `settings_put` rejects any key named like key, token, password or secret (`service.py:79-91`), so settings hold only `credential_ref: "qmx/..."`.
- **Native recipe**. `_ClaudeSDKLifecycle` in `RR/native_claude.py:55-355`. It builds `ClaudeAgentOptions`, opens one `ClaudeSDKClient` per turn with `resume=<session_id>`, exposes host tools through an in-process SDK MCP server named `qmx`, gates them with a `PreToolUse` hook, and maps `ResultMessage` to completed, interrupted or failed.

## How It Works

### 1. Start-up

`qmb host start` (`qmb/src/qmb/doors/cli/__init__.py:1691-1721` → `host.py:1785-1836 control_host`) runs `uv run --project qmx-agents/packages/qmx-control ... python -m qmx_control start --port 8766`. It does not pass `--ui-origin`, so CORS stays pinned to `http://127.0.0.1:5173`.

`CTL/__main__.py start` refuses if `<home>/control-process.json` exists or the port is taken. It then spawns `python -m qmx_control serve` detached (CREATE_NO_WINDOW, log at `<home>/control.log`), polls `/api/health` with the bearer token for up to 10 s, checks that the reported pid is in its own process tree, and records `{pid, port, created}`. `serve` runs `uvicorn.run(create_app(ControlService(home), token, ui_origin))`.

`ControlService.__init__` (`service.py:95-149`) builds `Library` (library.db) and `RunIndex` (runs.db). It then runs the control.db schema script (sets WAL; four tables, no migrations), takes `BEGIN IMMEDIATE`, migrates a legacy `library` table, and replays every `work kind='runs'` row into runs.db. `create_app` (`server.py:143-252`) gets the token from the keyring, calls `service.app_runtime().road.signing_key(token)` (which creates the Supervisor and apps.db), and mounts FastMCP at `/mcp`. It wraps everything in `BearerGate` and CORS, and starts a lifespan `maintain()` task. Every 60 s that task runs `runs_list` and, if a backup repository is set, `backup_weekly` in a worker thread.

### 2. A session, its blocks and events

```mermaid
sequenceDiagram
    participant C as Client (UI / script / agent)
    participant API as FastAPI + BearerGate (server.py)
    participant S as ControlService (service.py)
    participant DB as control.db
    participant SSE as GET /api/events/sessions
    C->>API: POST /api/sessions {title, origin, parent_id}
    API->>S: sessions_create(SessionInput)   [thread pool]
    S->>DB: INSERT sessions; _event("sessions", sid, {type:"created"})
    C->>SSE: subscribe ?subject=sid&after=N (fetch-based, Bearer)
    loop each block
        C->>API: POST /api/sessions/{sid}/blocks {type, content}
        API->>S: sessions_append(sid, SessionBlock)
        S->>DB: MAX(seq)+1; INSERT blocks; INSERT events (one txn)
    end
    loop every 50 ms
        SSE->>S: stream() -> events(topic, after, subject)
        S->>DB: SELECT ... WHERE topic=? AND seq>? AND subject=?
        SSE-->>C: event=sessions, id=seq, data={type:"block", block:{seq,type,content}}
    end
```

`sessions_create` (`service.py:300-313`) holds the in-process `RLock` and a fresh connection. It checks that the parent exists (404 otherwise), inserts a uuid4 session, and emits `{type:"created", session}`. `sessions_append` (`:324-335`) checks the session, computes `seq = COALESCE(MAX(seq),0)+1`, inserts the block, and calls `_event` in the same `with db` transaction. `_event` (`:156-169`) inserts the event row. For runs, jobs, apps and library it also computes aggregate counts (opening runs.db and library.db inside the control.db transaction) and inserts an `aggregates` event.

Reads never touch `blocks`; the table is only used for `MAX(seq)`. History comes from the `events` log, which stores each block a second time. `sessions_stream` (REST page) and the SSE route both read through `events()`. The SSE route (`server.py:215-228`) resumes from `max(after, Last-Event-ID)` and yields `ServerSentEvent(data=event["data"], event=topic, id=seq)`. The subject is not in the payload, so a client must filter with `?subject=`. `ControlService.stream` (`:187-198`) is an `async` loop that calls the sync `events()` (a new SQLite connection, opened on the event loop thread) and then sleeps 50 ms. The browser's native `EventSource` cannot send a Bearer header, so the UI must use fetch-based SSE. The UI on `ui-review/repair` does not call the backend yet and names 4 of the 14 kinds differently (H3 §2).

### 3. The only "turn → blocks" code: the LangChain copilot

`scripts/live/copilot_build_app.py` builds a `ControlService(home)`, creates a session, opens an `AsyncSqliteSaver` at `<home>/copilot/threads.db`, and calls `build_copilot(ctx)` (`QA/copilot.py:54-95`). That function mounts tools in-process: `create_mcp(ctx.control)` as `qmx-control`, plus `create_server(name, DomainContext(root=home/"domain"))` for data, backtest and research. It loads `QA/agents/copilot.yaml` (interrupt_on `{apps_publish, apps_start}`, budget 200 model and 400 tool calls) and returns a LangGraph from `build_agent` → `deepagents.create_deep_agent`.

`stream_turn` (`copilot.py:98-213`) is the projector:
- A string prompt appends a `user` block, then iterates `graph.astream(stream_mode="updates", subgraphs=True)`.
- A non-empty namespace (a sub-agent subgraph) calls `sessions_create(parent_id=session_id)` once per namespace and appends `agents {session_id, state:"working", namespace}` to the parent. Later blocks for that namespace go to the child.
- `__interrupt__` appends `permission {interrupt_id, request}` and marks the target as waiting.
- `AIMessage` appends `text`, then one `tool {id,name,arguments,state:"started"}` per call. A `write_todos` call also appends `plan`; `task`/`start_task` calls also append `agents {name, state}`.
- `ToolMessage` appends `tool {id,name,state,result}`, plus `artifact` when the result carries an `artifact_id`.
- At the end each child gets `agents {state:"needs_you"|"complete"}` in the parent.

Approvals live in the LangGraph checkpointer, not in QMX. The script sees `graph.aget_state(config).next` non-empty, prints the interrupts, reads `input()`, and calls `stream_turn(..., Command(resume={"decisions":[{"type":"approve"|"reject"}]}))`. Global-memory interrupts resume with a bare bool. No route accepts an answer and no row records one. The `permission` block is only a notice. The only other producer of `needs_you` blocks is `QA/guards/hooks.py:153 watch_breakers`, which also calls `service.notify_app`. `stream_turn` is `async` but calls the sync `sessions_append`, so each block blocks the event loop on SQLite.

### 4. The native Claude recipe (the shape qma2's ClaudeAdapter copies)

`NativeSessionProvider.execute` (`RR/native_sessions.py:125-131`) runs `asyncio.run(activity)` once per turn. Before anything is submitted it writes a journal record keyed by a sha256 binding hash. It then calls `backend.start` or `backend.resume`. `_connect` runs `call_blocking(_preflight)` (`native_claude.py:97-160`), which does these checks:
- Env names only: any `ANTHROPIC_*` or `CLAUDE_CODE_USE_*` fails with `subscription_required`.
- The SDK must be exactly 0.2.163 and `claude --version` must be exactly `2.1.286`.
- `claude auth status` under `CLAUDE_CONFIG_DIR=<dedicated home>` must report `loggedIn`, `authMethod=="claude.ai"`, a first-party provider and a matching config dir.
- The home must hold no settings, hooks, plugins, agents or skills.

It then builds options (`:239-280`) and calls `client_factory(options=...)`, `connect()`, `query(prompt)`. The options are: `permission_mode="dontAsk"`, `can_use_tool=deny`, a `PreToolUse` hook that denies any call with `agent_id` or outside `mcp__qmx__*`, `setting_sources=[]`, `strict_mcp_config`, an SDK MCP server `qmx` built with `tool()`/`create_sdk_mcp_server`, and an env that adds `CLAUDE_CONFIG_DIR` plus three disable flags. Host exceptions become `"Host operation refused"` and never reach the model.

`events()` (`:289-345`) reads `receive_response()`:
- `SystemMessage("init")` supplies the session id and the advertised tool list. It is refused if the id differs on resume or if a tool falls outside the permitted set.
- `AssistantMessage` yields text. A message with `parent_tool_use_id` set (sub-agent output) is refused.
- `ResultMessage` maps `aborted_*` to interrupted, an error to failed, and anything else to completed.
- Rate-limit events and thinking blocks are dropped. `total_cost_usd`, `usage`, `model_usage` and `permission_denials` are never read.

Cancel calls `client.interrupt()`, retried every 50 ms while it raises "interrupt pending". `finally` cancels the watcher, then bounds `cancel` and `close` to 2 s.

### 5. The MCP tool path

An agent reaches QMX tools in one of three ways:
- **HTTP** `http://127.0.0.1:8766/mcp/` with the operator's Bearer token. MCP arguments are wrapped by parameter name, e.g. `sessions_append {"session_id", "block":{...}}`, while REST takes a flat body.
- **In-process** `fastmcp.Client(create_mcp(service))`, with no token. The docstring says in-process callers are trusted.
- **stdio** `qmx-mcp-data|backtest|research|node` (13 domain functions, `TOOLS/registry.py:26-272`, `servers.py`). Each child builds `DomainContext`, whose `__post_init__` constructs its own `ControlService(QMX_TOOLS_ROOT or ~/.qmx)` (`TOOLS/service.py:127`, `:257`). That makes it a second writer process on the server's control.db. The constructor also re-takes `BEGIN IMMEDIATE` and replays runs.db.

On the MCP door, `ControlError`, `AppError` and `RemoteError` become `ToolError(json)` (`server.py:132-140`). On REST, an exception handler returns `{"error":{code,message}}`. The precedent for a door agents must not reach is `POST /api/apps/{id}/sign` (`server.py:184-196`). It is declared outside `OPERATIONS`, so MCP never exports it.

### 6. The database

Each SQLite file gets a fresh `sqlite3.connect(..., timeout=5)` per call: control.db at `service.py:153`, runs.db in `runs.py` and `service.py:422`, library.db at `library.py:64`, apps.db at about ten sites in `qmx_apps/supervisor.py`, plus portfolio.db and per-app app.db. The only pragma is WAL, set once. Writers include the FastAPI sync thread pool, the 60 s maintenance thread, Supervisor callbacks (`_app_event`), the tools children, and `ControlService` instances built in `QA/spec.py:396,417`. `self._lock` is per process. SQLite is 3.50.4.

## Where Things Live

| Concern | File |
|---|---|
| Host CLI | `qmb/src/qmb/doors/cli/host.py:1785-1836`; `CTL/__main__.py` (serve/start/status/stop/weekly-backup); T2 node `CTL/node.py` (`qmx` script, file vault `/etc/qmx/vault`) |
| App, auth, SSE, MCP mount, OPERATIONS | `CTL/server.py` (256 lines) |
| Sessions, blocks, events, settings, work | `CTL/service.py` (schema `:118-128`, sessions `:300-342`, events `:156-198`, 501s `:643-647`, `:880-894`) |
| Run projection and cost | `CTL/runs.py` (`RunIndex.refresh`, `model_call` cost `:122-126`) |
| Journal writer | `QA/guards/journal.py` (stdlib + pydantic only) |
| Projector reference | `QA/copilot.py:98-213 stream_turn` |
| Old approval wiring | `QA/guards/middleware.py:208 JournalApprovals`; YAML `QA/agents/*.yaml interrupt_on` |
| Money barrier | `QA/guards/money_path.py` (`check_descriptor :247-279`, acts `:21-62`) |
| Router neutral parts | `QA/router.py` (`model_selector`, `RouterConfig`, `credential :110-122`, `RunContext`) |
| Claude recipe | `RR/native_claude.py`, `RR/native_boundary.py`, `RR/native_sessions.py` (fake-client tests in `qma-daemon/tests/test_native_sessions.py`) |
| Domain tools | `TOOLS/registry.py`, `servers.py`, `service.py` |
| CI | `tools/ci.py:16-32`, `tools/test_all.py:57-127`, `qmx-agents/pyproject.toml:17,54,67,86,110-111` |

## Gotchas

1. **Two writer processes on control.db, and `sessions_append` can race.** The `MAX(seq)` read (`service.py:329-331`) runs before Python's legacy transaction mode issues `BEGIN` (only before DML). Two processes appending to one session can compute the same seq, and the loser gets an `IntegrityError` that surfaces as a 500. Inferred and not reproduced; the test at `test_control.py:283-297` covers two threads in one process only.
2. **`import qmx_control` loads LangChain.** The chain is `service.py:25 qmx_apps.supervisor` → `supervisor.py:29 qmx_agents.guards.money_path` → `langchain_core` and `qmx_broker`. Separately, `qmx_remote/models.py:11` and `runs.py:16` import `guards.journal`, and `guards/__init__.py` imports `admission` (deepagents). Package edges also loop: `QA/guards/hooks.py:17` imports `qmx_control.service`. That cycle does not bite at runtime because `guards/__init__` does not import `hooks` (inferred).
3. **The import count is 4 + 3, not "four".** qmx_apps has 4 import sites (`supervisor.py:29`, `road/__init__.py:11`, `road/history.py:13`, `road/validation.py:12`). qmx_remote has 3 (`models.py:11`, `runs.py:16`, `worker.py:29-32`; the agent-code explorer's `:26-32` is off by three). ARCHITECTURE A-18's "their four imports" covers only qmx_apps.
4. **`native_claude.py` cannot be imported cleanly.** It pulls in `native_sessions` → `RequestRuntime`, `tool_loop` (LangChain) and `qma.core`/`qma.wire`. Copy it; do not import it. `native_boundary.py` needs only `ProviderError`.
5. **The recipe has never run live.** `examples/native-session-runtime-check.json` records `model_calls: 0`. Its exact CLI pin (`:41`, `:114`) would refuse this laptop's 2.1.296. SDK 0.2.163 has no Windows wheel, so it runs whatever `claude.exe` is on PATH.
6. **The env is merged, not replaced.** The SDK merges `os.environ` into the child, and Claude Code sessions set `ANTHROPIC_BASE_URL` and friends. The recipe refuses such an env; it does not scrub it (31/60 tests fail with it set, per H3). qma2 needs an allow-list env, and that needs a custom transport or a launcher.
7. **`dontAsk` plus a deny callback is a lockdown, not an approval flow.** H1 facts 1-2 add more: an unset mode may start as `auto`; the Python `can_use_tool` needs streaming input plus a dummy `PreToolUse` hook; and allow rules shadow `can_use_tool` (the recipe's own comment at `:236`).
8. **Anyone with the token can write any block.** `sessions_append` and `library_save` are non-destructive, so any MCP caller can append blocks, including fake `permission` blocks, to any session. There is one bearer token for operator and agents alike, and mini-app manifests carry `qmx/control-token` (`macro-daily-bias/app.toml:21`, `mql5-articles/app.toml:16`). Keeping a route out of `OPERATIONS` keeps it off MCP, but anyone holding the token can still call it over REST (inferred). A separate operator principal is a precondition for a safe answer route.
9. **The `check_descriptor` money gate refuses `propose_order` by name.** Splitting on `_` yields `order`, which matches `MoneyPathAct.ORDER`. The old code let it through only by Python type (`check_tool :240-242`, the LangChain proposal classes). A copied `check_descriptor` in a single `ToolInvoker` needs an explicit, non-name-based exemption for proposal-only tools (read in code, not run). `money_path.py:14-15` also imports `qmx_broker` at module top; the copy must drop those imports.
10. **Closed Literals.** A new block kind, event topic (e.g. approvals, usage) or settings section (e.g. accounts) needs a code change to `SessionBlock`, `EventTopic` or `SettingsSection`. The SSE path parameter is typed `EventTopic`, so an unknown topic is a 422.
11. **Sync vs async doors.** REST handlers are the bound methods. A sync method runs on the thread pool; an `async def` runs on the loop. `_mcp_method` (`server.py:132-140`) is a sync wrapper, so an async turn method needs an async wrapper variant. Inferred: I did not check how FastMCP treats a sync wrapper that returns a coroutine.
12. **Unread metadata.** `meta.interrupt_on` on MCP tools is never read. The `budgets` and `memory_provider` settings sections are never read. `_cancellers` is in memory, so cancel answers 501 after a restart.
13. **`RunJournal` stale lock.** The constructor opens `<journal>.lock` with mode `"x"` (`journal.py:47-48`). A crashed writer blocks reopening, and there is no recovery. Every append fsyncs.
14. **No timestamps anywhere** in sessions, blocks or events, and no retention. A usage ledger cannot be derived from events.
15. **Test traps.** rclone missing from PATH fails one control test. Keep pytest at `-n 2`. qmx-agents `addopts` is `-n auto`. `poe.exe` is blocked by App Control, so use `python -m poethepoet`.

## Plug-in points for qma2

The target, from ARCHITECTURE §0 and §2.0: the package lives at `qmx-agents/packages/qma-v2/src/qma2/`. `qmx_control`, `qmx_apps` and `qmx_remote` import `qma2`. `qma2` imports no `qmx_*` and no `qma.*` package, and only `qma2.engine` imports an SDK. New control operations register from `CTL/agent_ops.py`.

| Concern | Where it attaches today (file:line) | New vs reused/copied | Known traps |
|---|---|---|---|
| Turn route | Add a row next to `sessions_*` in `OPERATIONS` (`CTL/server.py:77-80`), registered from a new `CTL/agent_ops.py`; the method calls `qma2` `TurnHost`/`turns.submit` and returns a run id at once; blocks stream over the existing SSE (`server.py:215-228`) | New: `agent_ops.py`, `TurnHost`, the engine facade. Reused: the session row, SSE and the `OPERATIONS` double binding | The method must be async or offload work; the MCP wrapper is sync (Gotcha 11). One row also exposes turns to agents over MCP, which ARCHITECTURE intends ("agent principal allowed"). `origin` defaults to `"copilot"`. Sessions have no status for "waiting_approval" |
| Approvals table + answer route | Schema is the `executescript` at `service.py:118-128` (no migrations), or a qma2 `Store` migration. The answer route follows the `/sign` precedent at `server.py:184-196`, declared outside `OPERATIONS` | New: approvals table, `ApprovalQueue`, an operator principal gate, an `answered` write-back block. Reused: `permission`/`needs_you` block kinds (free-form content) and the 19 destructive flags as policy input | Today's single token makes "operator-only" unenforceable over REST (Gotcha 8). Any agent can forge `permission` blocks via `sessions_append`. Claude `can_use_tool` semantics are unproven live (probes P3/P5). OpenAI parks a `RunState` (H1 fact 11) |
| Block projection | Sink is `ControlService.sessions_append` (`service.py:324-335`); reference mapping is `QA/copilot.py:98-213` | New: `BlockProjector` over the `QmaEvent` from both engines. Copied: the mapping rules (text, two tool blocks per call, plan, agents, artifact, permission) | Blocks are completed messages, not deltas. `blocks` is never read; history is `events`. Closed 14-kind Literal; UI names differ in 4 kinds. Calling sync SQLite from async code blocks the loop. ARCHITECTURE projects inside qma2's own `Write`, not by calling `ControlService` |
| Usage ledger | Nothing exists. Nearest is the `model_call` journal event → `runs.cost` (`CTL/runs.py:122-126`), written by `QA/guards/middleware.py JournalMiddleware` | New: ledger table, a `usage` topic (widen `EventTopic`, `service.py:43`), capture of Claude `ResultMessage.usage/model_usage/total_cost_usd` and `RateLimitEvent`, and OpenAI `usage` | The recipe discards all usage fields. `RateLimitEvent` arrives only on change, so cache the last one per window (H1 fact 10). Events have no timestamps. `budgets` settings are never read |
| Router / accounts | Nothing for subscriptions. `QA/router.py` neutral parts: `model_selector`, `RouterConfig`, `RunContext` ladder. `accounts()`/`quotas()` call CLIProxy only | New: account rows, `Router.pick`, family guard, stickiness. Copied: `model_selector` and the `RouterConfig` shape | A Claude "account" is a `CLAUDE_CONFIG_DIR` the operator logs into himself; QMX may not store Claude tokens (H1 fact 4). An OpenAI Sign-in-with-ChatGPT token may be stored. `SettingsSection` is closed, so an `accounts` section needs a code change. `models.yaml` hardcodes CLIProxy names |
| Secrets | Keyring `qmx/<name>` (`server.py:84-90`, `QA/router.py:110-122 credential`); `_no_secrets` in `settings_put` (`service.py:79-91`); T2 file vault in `CTL/node.py` | Reused: the convention and `credential_ref`. New: `Credentials.scrub_env/redact` and an allow-list child env | SDK env merge plus the inherited `ANTHROPIC_*` (Gotcha 6). `credential()` falls back to `QMX_<P>_API_KEY` when `CI=1`. `secret_scan` flags quoted credential-like literals in tests |
| Sub-agent child sessions | `sessions_create(SessionInput(parent_id=...))` (`service.py:300-313`), as in `copilot.py:133-145` | Reused: `parent_id` and the `agents` block. New: map Claude `parent_tool_use_id`/hook `agent_id` and OpenAI `as_tool`/handoff to child sessions | The recipe refuses sub-agent output (`pre_tool` on `agent_id`; `parent_tool_use_id` refusal), so drop that lockdown. No session status or get-by-id |
| Money refusal | `QA/guards/money_path.py:21-162, 247-279` (`check_descriptor`); live user `qmx_apps/supervisor.py:29` (and `:473`, `:671` on mini-app descriptors); `qmx-broker/server.py:67` flags `propose_order` | Copied into `qma2.policy` (drop the `langchain_core` and `qmx_broker` imports and the `BaseTool` classes); qmx_apps re-points its import | `propose_order` is refused by name (Gotcha 9). qmx-tools' `propose_order` carries no `money_path` meta, only `readOnlyHint=False`. Claude built-in tools (Bash, Write) bypass a tool-descriptor gate; ARCHITECTURE §1.4 admits this until the low-rights account exists |
| Single-writer DB | Every `_connect()` (`service.py:151-154`), `RunIndex`, `Library`; extra writers at `TOOLS/service.py:127`, `QA/spec.py:396,417`, the maintenance thread at `server.py:152-165` | New: qma2 `Store` with one writer thread per file and numbered migrations | The tools children remain a second writer unless they call back over MCP/HTTP or the Store owns them. `ControlService.__init__` takes `BEGIN IMMEDIATE` and replays runs.db on every construction. The `sessions_append` seq race (Gotcha 1). SQLite 3.50.4 |
| CI wiring | `tools/ci.py:16-27` (hard-coded workspace paths and the poe loop); `tools/test_all.py:57-127` (suite list); `qmx-agents/pyproject.toml:17` members, `:67` `--ignore`, `:86` ruff `extend-exclude`, `:111` pyright `exclude`, `[tool.uv.sources]` | New: a `qma-v2` row in both scripts, its own poe `fmt-check/lint/types`, the import-linter contract (packet 0) | A new `packages/<x>` is otherwise swept into the old QMA suite (`testpaths :69`), the workspace ruff and pyright. GitHub Actions has never run; "green" means local `just ci` (~29 min, under `.ci-lock`) |
| Package placement + import rules | `qmx-agents/packages/qma-v2/` (no `qma2` name clash; old `qma` is a PEP 420 namespace). SDK pins: `claude-agent-sdk==0.2.163` sits in the workspace dev group (`pyproject.toml:54`); `openai-agents` is in no lockfile | New: package, runtime pins (`openai-agents`, `claude-agent-sdk`, explicit `openai`), import-linter. Copied as-is: `journal.py`, `parent_surfaces.py`, `experiments.py`. Copied in part: `money_path`, `router`, `spec` fields, `memory` protocol, `native_boundary`, `native_claude` logic | `openai-agents` imports as top-level `agents`; never add a first-party `agents` package at a sys.path root. qma2 cannot import `qmx_control` without LangChain until the guards move (Gotcha 2). Whether import-linter can forbid a PEP 420 root is open (ARCHITECTURE §0) |

## Open questions carried from the explorers

- The cross-process `sessions_append` seq collision is reasoned, not reproduced. A two-process script against a temp home would settle it.
- Not traced: whether any live path launches the `qmx-mcp-*` stdio servers (only the README does); how `qmx-apps` injects tokens into mini-app processes; `native_codex.py:330-553`; the keyring backend's Credential Manager target format.
- No evidence was found of a live copilot or native-Claude turn ever succeeding. The real behaviour of hooks, `can_use_tool`, `defer` and resume is what probes P3/P5 must establish.
- Moving to `claude-agent-sdk` 0.2.165 (Windows wheel with a bundled CLI, 5 days old) against the two-week rule is the operator's call.
