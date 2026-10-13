## Control-plane survey: how a chat session flows through QMX, and where qma2 plugs in

Read at D:/QMX-worktrees/harness-survey (origin/rebuild/base 4eac8f69, worktree clean). I read the code and checked H3-code-map.md against it. Every H3 claim I re-checked holds. One thing I ran: `.venv/Scripts/python.exe -B` for the SQLite version (3.50.4, Python 3.14.6) and `inspect.signature` on three service methods. Claims marked "reasoned" below come from reading only; I ran nothing for them.

Path keys: `CTL` = qmx-agents/packages/qmx-control/src/qmx_control, `TOOLS` = qmx-agents/packages/qmx-tools/src/qmx_tools, `AG` = qmx-agents/packages/qmx-agents/src/qmx_agents.

### Components Found

**1. App start**
- `qmb host start|status|stop` (qmb/src/qmb/doors/cli/__init__.py:1691-1721, options `--home`, `--port` default 8766, `--python`) calls `control_host` (qmb/src/qmb/doors/cli/host.py:1785-1836).
  - It builds `uv run --project qmx-agents/packages/qmx-control --package qmx-control --frozen python -m qmx_control <cmd> --port N [--home H]`.
  - It does not pass `--ui-origin`, so CORS stays at `http://127.0.0.1:5173`.
- `CTL/__main__.py` has five commands: `serve|start|status|stop|weekly-backup`.
  - `start`:
    - Refuses if `<home>/control-process.json` exists, or if the port is occupied.
    - Spawns `python -m qmx_control serve --home --port --ui-origin` detached (CREATE_NO_WINDOW), logging to `<home>/control.log`.
    - Polls `/api/health` with the bearer token for up to 100 tries at 0.1 s.
    - Checks that the reported pid belongs to its own process tree, then writes `{pid, port, created}` to `control-process.json`.
  - `serve` runs `uvicorn.run(create_app(ControlService(home), token, ui_origin), host="127.0.0.1", port)` (:39-45).
  - `stop` compares the recorded create-time before killing the process tree.
  - Python 3.14 syntax is used: `except httpx.HTTPError, psutil.NoSuchProcess:` at :104 (and node.py:70) is PEP 758, not a bug.
- Home and data folder: `default_home()` = `~/.qmx` (`CTL/server.py:255`). `--home` overrides it. Files under home:
  - control.db: sessions, blocks, work, events.
  - runs.db: runs, journals.
  - library.db plus `artifacts/` blobs.
  - apps.db: the Supervisor catalog.
  - artifacts.db.
  - portfolio.db: broker proposals.
  - settings.toml.
  - `runs/**/*.jsonl` and `journals/**/*.jsonl`: run journals.
  - `apps/<id>/...`: app volumes, each with its own app.db.
  - `environments/`.
  - control-process.json and control.log.
- Secrets:
  - The `keyring` library (backend not read; on Windows it is Credential Manager).
  - Convention: service = `qmx/<name>`, username = `<name>`.
  - The control token: `keyring.get_password("qmx/control-token","control-token")`, minted with `secrets.token_urlsafe(32)` and saved if absent (`CTL/server.py:84-90`).
  - Provider keys: `AG/router.py:110-122` `credential(provider)` reads `keyring.get_password(f"qmx/{provider}", provider)`. Only when env `CI` is 1/true does it fall back to env `QMX_<PROVIDER>_API_KEY`.
  - Broker: `qmx-broker/credentials.py:9-32` reads a JSON-object secret under `qmx/<x>`.
  - Remote: `qmx/modal-token-id`, `qmx/modal-token-secret`, `qmx/e2b` (qmx-remote/providers.py:184,185,265).
  - Firecrawl: `qmx/firecrawl`.
  - `ControlService(secret_getter=keyring.get_password)` is injected into the Supervisor and RemoteRuns.
  - `settings_put` rejects any dict key (recursive, case/underscore/hyphen-insensitive) named key, apikey, token, password, secret or clientkey (`CTL/service.py:79-91`). Settings may only hold `credential_ref: "qmx/..."`.
  - The T2 VPS node (`CTL/node.py`, console script `qmx`) reads files from `/etc/qmx/vault/<name>` instead, with chmod-600 checks, and binds to a Tailscale 100.x IP on port 8766 with home `/var/lib/qmx`.
- Env vars in qmx-control itself: none. `QMX_TOOLS_ROOT` and `QMX_TOOLS_FACTORY` belong to qmx-tools (TOOLS/service.py:242-266). `CI` and `QMX_<P>_API_KEY` are read in the router. Nothing else is read.

**2. ControlService (`CTL/service.py`, 894 lines) and server (`CTL/server.py`, 256 lines)**
- `ControlService.__init__(home, *, tier="T1"|"T2", node="laptop", secret_getter)` (:95-149). In order, it:
  - Builds `Library(home)` (library.db) and `RunIndex(home)` (runs.db).
  - Runs the control.db schema.
  - Opens `BEGIN IMMEDIATE` on control.db.
  - Migrates any legacy `library` table.
  - Replays every `work kind='runs'` row into `run_index.record`.
- control.db schema (:119-128). WAL is set once here and persists in the file. There is no migration framework.
  ```sql
  sessions(id TEXT PK, data TEXT)
  blocks(session_id, seq INTEGER, data TEXT, PK(session_id,seq))
  work(kind, id, data, PK(kind,id))   -- kind IN runs|jobs
  events(seq INTEGER PK AUTOINCREMENT, topic, subject, data)
  ```
  - No timestamps exist anywhere: no `created_at` on events, blocks or sessions.
  - `blocks` is write-only. `SELECT ... FROM blocks` appears only as `MAX(seq)+1` (:329-331).
  - Reads of session history come from the `events` log, which stores the same block data a second time.
  - No pruning or compaction exists.
- Session API (:300-342):
  - `sessions_create(session: SessionInput{title 1..200, origin="copilot", parent_id|None})` returns `{id: uuid4, title, origin, parent_id}` and emits topic `sessions`, subject `<sid>`, data `{type:"created", session}`. A missing `parent_id` gives ControlError 404.
  - `sessions_list(offset=0, limit=100)` orders by rowid. There is no `sessions_get`, no status field, no updated_at.
  - `sessions_append(session_id, block: SessionBlock{type, content: Document})`:
    - Holds `self._lock` (an RLock, in-process only) and a control.db connection.
    - Computes `seq = MAX(seq)+1` per session.
    - Inserts into `blocks`, then calls `_event(db,"sessions",sid,{"type":"block","block":{seq,type,content}})` in the same transaction.
    - Returns `{seq,type,content}`.
    - An unknown session gives 404. An unknown `type` gives 422 (pydantic).
  - `sessions_stream(session_id, after=0, limit=100)` is a paged read of `events("sessions", after, subject=sid, limit)`. It returns `[{id,topic,subject,data}]`.
- The 14 SessionBlock types (:54-71), with `content: Document = dict[str, JsonValue]` and no per-kind validation: user, text, plan, agents, tool, changed, artifact, table, entity, question, permission, panel, handoff, needs_you.
  - Block shapes the old LangChain copilot actually emitted (`AG/copilot.py:98-213`):
    - `user {text}`
    - `text {text}`
    - `tool {id,name,arguments,state:"started"}`, then `tool {id,name,state,result}`
    - `plan {todos}`
    - `agents {session_id,state,namespace}`, or `{name,state}`
    - `permission {interrupt_id, request}`
    - `artifact {artifact_id,...}`
    - `needs_you {app_id,instance_id,reason}` from `AG/guards/hooks.py watch_breakers`, which also calls `service.notify_app`
  - Nothing reads an answer to a `permission` block.
  - Delegated sub-agents become child sessions (`parent_id`) plus an `agents` block in the parent.
- Events:
  - `EventTopic = Literal["runs","jobs","sessions","apps","library","settings","aggregates"]` (:43). Seven topics confirmed.
  - `_event` (:156-169) inserts the event. For runs/jobs/apps/library it also inserts an `aggregates` event with `{revision, library_items, runs, active_jobs}`. It also clears the 5-second TTL aggregate cache.
  - `events(topic, after, subject, limit<=1000)` runs `SELECT seq,subject,data ... WHERE topic=? AND seq>? AND (subject filter) ORDER BY seq LIMIT`. It returns `{"id":seq,"topic","subject","data":<dict>}`.
- SSE (`server.py:215-228`) is `GET /api/events/{topic}?after=&subject=&max_events=` (max_events 0..1000, 0 = unbounded) plus the `Last-Event-ID` header. The effective cursor is `max(after, last_event_id)`.
  - It emits `ServerSentEvent(data=event["data"], event=topic, id=str(seq))`.
  - Only the inner `data` is sent. The subject is not in the payload, so the client must filter by the `subject` query param.
  - `ControlService.stream` (:187-198) loops `events()` synchronously, then `await asyncio.sleep(0.05)`. That is a 50 ms poll, and each poll opens and closes a fresh SQLite connection inside the event loop (blocking).
  - fastapi 0.142.2 `EventSourceResponse` adds its own `: ping` keep-alive every 15 s (fastapi/sse.py:237-241). The service has no heartbeat of its own.
  - Browser-native `EventSource` cannot send the Bearer header. The UI must use fetch-based SSE.
  - CORS allows only GET/POST/PUT, with headers Authorization, Content-Type, Last-Event-ID, Mcp-Session-Id, Mcp-Protocol-Version (:239-251).
- Auth: two layers. `BearerGate` is ASGI middleware over everything including the mounted `/mcp`. `authenticate` is a `Depends(HTTPBearer)` on each REST route. Both use `secrets.compare_digest`.
- Runs and jobs (`RunIndex`, `CTL/runs.py`):
  - `record_work(kind, work_id, data, cancel=None)` upserts `work` and emits an event. For `kind=="runs"` it also merges into runs.db with defaults `{id, kind:"agent", target, node, model:{}, status:"running", cost:None, started, ended, artifacts:[]}`.
  - `_cancellers` is an in-memory dict, so cancel is lost on restart.
  - `RunIndex.refresh()` globs `home/runs/**/*.jsonl` and `home/journals/**/*.jsonl` and projects the hash-chained RunJournal records. It does this on `runs_list`, `runs_get` and `aggregates_get`, and from the 60 s maintenance loop. Journal format:
    - `{seq, run_id, time, event, payload, fingerprint=sha256(canonical json of the rest)}`.
    - `run_start` payload fields: kind, target, node, app_id, workflow_id, session_id.
    - `run_end` payload: `{status}`.
    - `model_call` payload: `{agent, model, metadata:{cost}}`. This is the only existing usage or cost path: cost is summed as a Decimal string into the run row.
    - `payload.artifact_ref` or `payload.result_ref` collects into `artifacts`.
  - A tampered or rewritten journal raises ControlError 409 `invalid_journal`.
  - Writer: `AG/guards/journal.py RunJournal(path, run_id).append(event, payload)`, fsync per record, and a `<path>.lock` file created with mode "x". A crashed writer leaves a stale lock that blocks reopening (reasoned).
- 501 routes (verified at :880-894, via `_unavailable` at :643-647, status 501, code `not_implemented`): `workflows_get`, `workflows_put`, `workflows_validate`, `workflows_run`.
  - `runs_cancel` and `jobs_cancel` (via `_cancel`, :604-633):
    - Unknown id gives 404.
    - A terminal-status run returns its data.
    - With no registered canceller it returns the 501 `{kind}.cancel`.
    - Otherwise it calls the canceller and emits `{id,status:"cancel_requested"}`.
    - The only `cancel=` ever registered is an app instance stop in `_app_event` (:850-852).
- Not present anywhere: turns, approvals, usage ledger, account router.
- `settings.toml` sections (`SettingsSection` Literal, :40-42): providers, mcp_servers, budgets, memory_provider, backup, brokers, remote.
  - `budgets` and `memory_provider` are never read by any code I found (no `settings_get("budgets")` call exists).
  - `providers.litestream` is read for T2.
  - Per-agent budgets live in agent YAML (`AG/spec.py:102,393,418-424`: model_calls and tool_calls limits).

**3. The database: every SQLite open**
- control.db: `ControlService._connect()` at service.py:153. This is a new `sqlite3.connect(home/"control.db", timeout=5)` per call, wrapped in `closing(...)` and `with db` (commit on exit). It is reached from sessions_*, events, settings_put, record_work, _refresh_runs, _cancel, aggregates, app events and backup events. Journal mode is set only in `__init__` (:120).
- runs.db: `RunIndex` (`CTL/runs.py`: :22 init, :31 record, :68 per-journal refresh, :143, :152, :159) and `service.py:422` (`_aggregate_counts`, no timeout argument, so the default 5 s).
- library.db: `Library.connect()` at library.py:64. `Library.save` uses `BEGIN IMMEDIATE`.
- qmx-apps:
  - apps.db: supervisor.py:121, 160, 167, 256, 267, 281, 305, 317, 351, 755. No timeout argument.
  - artifacts.db: artifacts.py:33, 68, 82.
  - apps.db is also opened in road/history.py:150.
  - Per-app app.db: volume.py:48 and store.py:18, with `busy_timeout=5000`.
- qmx-broker portfolio.db: service.py:107, 176 and a read-only open at :202.
- No connection pool, no `check_same_thread` handling. Pragmas in use: only `journal_mode=WAL` and `busy_timeout` via the Python `timeout`.
- Writers are:
  - FastAPI's sync-endpoint thread pool.
  - The async lifespan task `maintain()` (`server.py:152-165`), every 60 s via `asyncio.to_thread`: `runs_list`, and `backup_weekly` only if `settings backup.repository` is set. Failures are recorded as a `jobs` work item "maintenance".
  - Supervisor event callbacks (`_app_event`).
  - Any other process that builds a `ControlService` on the same home.
- Where a `ControlService` is constructed (each one is a separate writer):
  - `__main__.py:36,41` (serve, weekly-backup) and `node.py:156`.
  - `TOOLS/service.py:127`, in `DomainContext.__post_init__`. It runs in every `qmx-mcp-*` child, on `QMX_TOOLS_ROOT` or `~/.qmx` (:257), the same home as the server. Its `library_save` and `memoized_backtest` write control.db events from a second process. `__init__` takes `BEGIN IMMEDIATE` on control.db and replays all `runs` rows into runs.db on every child start.
  - `AG/spec.py:396` (when `ctx.control is None` and `qmx_home` is set) and `:417` (a fresh `ControlService` for `ResearchLibraryMiddleware` whenever firecrawl is a server).
- Two-process hazard:
  - Cross-process safety rests only on SQLite locking (WAL, 5 s timeout).
  - `self._lock` and `self.lock` are per-process.
  - Reasoned, not run: `sessions_append` reads `MAX(seq)` outside a write transaction. Python's legacy transaction mode issues `BEGIN` only before DML, and the code does not hold `BEGIN IMMEDIATE`. Two processes appending to one session can compute the same seq, and the loser hits `IntegrityError` on the (session_id, seq) primary key (surfacing as 500).
  - The existing concurrency test (test_control.py:283-297) covers two threads in one process only.
- The old in-process copilot did not hit this for tools: `build_copilot` (`AG/copilot.py:66-69`) mounts `create_mcp(ctx.control)` and `create_server(name, DomainContext(root=qmx_home/"domain"))` in-process. That is a separate `qmx_home/domain` tree, so a separate control.db and library.db.
- SQLite 3.50.4 (checked).

**4. MCP surface and how an agent calls QMX tools**
- `OPERATIONS` (`server.py:28-81`) is a tuple of `(name, HTTP method, path, destructive)`. It is the single registry. 52 rows, 19 flagged destructive, 33 not.
  - Destructive: apps_create, apps_update, apps_publish, apps_rollback, apps_start, apps_stop, apps_restart, apps_call, apps_restore, workflows_put, workflows_run, runs_start_remote, runs_resume, runs_stop, run_job, runs_cancel, jobs_cancel, backup_weekly, settings_put.
  - All four `sessions_*` rows and `library_*` rows are non-destructive.
  - `getattr(service, name)` is bound to REST via `app.add_api_route(path, method, operation_id=name)` (:206-213) and to MCP via `mcp.tool(name, annotations={"readOnlyHint": method=="GET", "destructiveHint": destructive}, meta={"interrupt_on": destructive})` (:120-129). Both doors call the same bound method.
  - MCP wrapping catches ControlError/AppError/RemoteError and raises `ToolError(json.dumps(error.document()))`.
  - REST errors come from an exception handler returning `error.document()` (`{"error":{"code","message"}}`) with `error.status`.
- Argument shapes differ by door:
  - REST uses a flat body for a single pydantic parameter: `POST /api/sessions {title,origin,parent_id}` and `POST /api/sessions/{id}/blocks {type,content}`.
  - MCP wraps by parameter name: `sessions_create {"session":{...}}` (test_control.py:332), `sessions_append {"session_id","block":{...}}`, `library_save {"item":{...}}`, `settings_put {"section","values"}`.
  - The OpenAPI operation ids equal the tool names, and a test enforces this (test_control.py:108-111).
- Mount: `/mcp` is FastMCP's `http_app(path="/")`, so the URL is `http://127.0.0.1:8766/mcp/` with `Authorization: Bearer`. `create_mcp(service)` is also usable in-process with no token (`fastmcp.Client(create_mcp(service))`, as in the tests). The docstring says in-process and stdio callers are trusted.
- `interrupt_on` meta:
  - It is only advertised on each tool.
  - The only test touching it checks it exists (test_control.py:106-107).
  - I found no reader of `.meta["interrupt_on"]` anywhere in the repo src.
  - Real approval gating in the old stack was the per-agent YAML map `interrupt_on: {apps_publish: true, apps_start: true}` (copilot.yaml:12, app-builder.yaml:6, overnight-builder.yaml:6), wired to LangGraph `HumanInTheLoopMiddleware` (`JournalApprovals`, `AG/guards/middleware.py:208-243`). It requires a checkpointer (`spec.py:251`).
- Operator-only precedent: `POST /api/apps/{id}/sign` (`server.py:184-196`) is a REST route outside `OPERATIONS`. It is never exported as an MCP tool and carries the docstring "Operator-only door: never exported as an agent MCP tool".
- Domain tools (qmx-tools): 13 functions in 4 groups (`TOOLS/registry.py:26-272`), served as stdio FastMCP servers (`servers.py`; console scripts `qmx-mcp-data|backtest|research|node`):
  - data: list_instruments, read_bars, read_features, calendar.
  - backtest: run_backtest, backtest_status, backtest_results, compare_runs.
  - research: qml_run, library_search, library_save.
  - node: node_state, propose_order.
  - `servers.py:16-20`: `readOnlyHint` is false only for run_backtest, library_save and propose_order. `destructiveHint` is always False. No `interrupt_on` meta.
  - `propose_order` only saves an `order-proposal` artifact with status `awaiting_operator_signature, executed: False`.
  - Repo docs mention no config that launches these `qmx-mcp-*` stdio commands; only the README does.
- `AG/spec.py:mcp_configuration` (:197-245) shows how MCP server configs are assembled today (firecrawl default plus settings.toml `mcp_servers`, `credential_ref` resolved through `credential()`).

**5. CI wiring a new package must join**
- `justfile:204-209`: `test-all` runs `uv run python tools/test_all.py`; `ci` runs `uv run python tools/ci.py`. The PR job `backend` in .github/workflows/battery.yml:19-51 runs `uv run --frozen python tools/ci.py` on ubuntu-24.04 and windows-2025 (uv 0.12.6, rclone v1.75.1 installed). The nested `agents-*` job runs `poe fmt-check|lint|types|test|cov-report` in qmx-agents. Per H3, GitHub Actions has never run.
- `tools/ci.py:23-38`:
  - Workspace variables `agents/core/control/domain/apps/broker/remote` are hard-coded.
  - Loop 1: `uv sync --frozen` at the root, then `uv sync --frozen --all-packages --all-groups` in qmx-agents.
  - Loop 2: for each of `(ROOT, agents, core, control, domain, apps, broker, remote)`, run poe `fmt-check`, `lint`, `types` (via `python -m poethepoet`).
  - Then `money-path-scan` and `secret-scan` at the root, then `tools/test_all.py`.
  - A new package needs its own entry in that tuple and its own `[tool.poe.tasks]` fmt-check/lint/types (control's: `ruff format --config pyproject.toml --check src tests`, `ruff check ...`, `python -m pyright`).
- `tools/test_all.py`:
  - Suites are hard-coded (:57-127). Each runs as `uv run [--all-packages --all-groups if under qmx-agents] <cmd> --basetemp ... --junitxml ...` with `-n 2 -m "not serial"`.
  - Then the serial pass `-n 0 --no-cov -m serial`, where exit 5 (no tests collected) is tolerated.
  - The "QMA" suite is `qmx-agents: pytest packages tests`, and its pytest `addopts` `--ignore`s each named package (`qmx-agents/pyproject.toml:67`).
  - A new `packages/<x>` directory not added to that `--ignore` list is swept into the QMA suite. It is also covered by `ruff ... packages` (`extend-exclude` at :86) and pyright (`include = ["packages", ...]`, `exclude` at :111).
  - qmx-agents `uv.workspace.members` is an explicit list (:17), so a new member must be added there and to `[tool.uv.sources]`.
  - qmx-agents `addopts` is `-n auto`. Per-package pyprojects set `-n 2 --dist worksteal`.
- Per-package pyproject pattern (qmx-control pyproject.toml): `requires-python=">=3.14,<3.15"`, uv_build backend, dev group (ruff 0.16.5, pyright 1.1.411, pytest 9, xdist, cov, poethepoet 0.48.0), `[tool.ruff] extend = "../../../pyproject.toml"` (the root config; qmx-tools and qmx-broker instead extend `../qmx-agents/pyproject.toml`), per-file-ignores for tests (S101 etc.), `[tool.pyright] include=["src","tests"] strict, pythonVersion 3.14`. The root pyproject excludes `qmx-agents` from root ruff (:277) and skylos (:428), and puts the qma src dirs on the pytest and pyright paths (:228-230, :360-362).
- Pins: claude-agent-sdk==0.2.163 sits in the qmx-agents workspace dev group (pyproject.toml:54). `openai-agents` is in no lockfile (H3's findings, not re-checked here).
- `secret_scan` (tools/secret_scan.py:103-113) walks the whole repo's text files, so a new package's tests must not contain literals like `token = "xxxxxxxx"` (the quoted-credential-assignment pattern needs 8+ non-space chars after `password|secret|token|api_key|...` followed by `=` or `:` and a quote). `money_path_scan` covers `packages, extensions, qml, qmb, qmn, tools`, not qmx-agents.

### Flow

Chat session today (what exists):
1. `qmb host start` → `qmx_control start` → detached `qmx_control serve` → uvicorn 127.0.0.1:8766 with `create_app(ControlService(home), token)`. Create_app also calls `service.app_runtime().road.signing_key(token)`, which creates the Supervisor and apps.db at start.
2. Client (UI or agent) sends `POST /api/sessions` (or MCP `sessions_create {session:{...}}`) and gets back `{id,title,origin,parent_id}`. An event `sessions/<sid>/{type:created}` is written.
3. The client opens `GET /api/events/sessions?subject=<sid>&after=<seq>` (SSE).
4. Anything that talks appends blocks with `POST /api/sessions/{sid}/blocks {type,content}`. Each append writes `blocks` and `events` atomically, and the SSE poll delivers it within about 50 ms.
5. Nothing in qmx-control today drives a model. The only code that did was `AG/copilot.py stream_turn`, which is reached only from `scripts/live/copilot_build_app.py`. It consumed a LangGraph stream and called `service.sessions_append(...)` for each message, tool call and interrupt. That is the sole example of the "turn → blocks" projection.
6. Approvals today: LangGraph `interrupt()` becomes a `permission` block `{interrupt_id, request}`, and a resume happens through a `Command` passed back to `stream_turn`. No route and no table exist for the answer.
7. Run records arrive by two routes: `record_work("runs", ...)`, or a RunJournal `.jsonl` file that `RunIndex.refresh()` projects. Both emit `runs` and `aggregates` events.

Where qma2 plugs in (my read of the code; this is design inference, not existing code):
- **Turn route**: add methods on `ControlService` and rows in `OPERATIONS` (e.g. a POST under `/api/sessions/{sid}/turns`). One row gives REST and MCP at once, the existing "no second implementation" rule. The turn host would call `sessions_append` for each block and `record_work`/a RunJournal for the run. It must be async or threaded, because the REST layer is sync and runs on a thread pool.
- **Approvals**:
  - The `permission` block kind and the `needs_you` kind already exist, free-form `content`.
  - Storage must be new: a table in control.db (the schema block at :119-128 is the one place) or a new db. The `work` table with kind runs|jobs is typed by `WorkKind` and is not a fit without widening.
  - The "answer" route should follow the `/sign` precedent (REST-only, outside `OPERATIONS`), so an agent cannot approve its own tool call over MCP.
  - `interrupt_on` map plus `destructiveHint` give the policy input: 19 destructive tools are already marked.
- **Usage ledger**: no ledger code exists in the control plane. `model_call.payload.metadata.cost` in RunJournal records is the one existing cost channel (summed as `runs.cost`). A ledger table or `usage` topic does not exist (`EventTopic` is a closed Literal at :43), and events have no timestamps.
- **Router across accounts**: nothing in control reads account or usage state. The `budgets` and `providers` settings sections exist but no code consumes `budgets`.
- **Secrets for engines**: use the `qmx/<name>` keyring convention and `settings_put`'s `credential_ref` pattern. Do not store keys in settings.toml or the DB.
- **Package**: the CI/exclude sweep list above, plus a new row in `tools/ci.py` and `tools/test_all.py`.

### Files Read
- D:/QMX-worktrees/agent-system/tracker/qma-v2/research/H3-code-map.md
- qmx-agents/packages/qmx-control/src/qmx_control/{server.py, __main__.py, service.py, models.py, runs.py, node.py, cache.py, library.py (1-80)} and pyproject.toml
- qmx-agents/packages/qmx-control/tests/test_control.py (lines 1-350)
- qmx-agents/packages/qmx-tools/src/qmx_tools/{service.py, servers.py, registry.py} and pyproject.toml
- qmx-agents/packages/qmx-agents/src/qmx_agents/{copilot.py, router.py (1-150), guards/journal.py, guards/middleware.py (195-243), guards/hooks.py (140-185), spec.py (190-250, 385-430)} and agents/*.yaml (interrupt_on greps)
- qmx-agents/packages/qmx-remote/src/qmx_remote/{worker.py (partial), models.py (1-80)}
- qmx-agents/packages/qmx-apps/src/qmx_apps/{supervisor.py (95-135, 660-730), volume.py, artifacts.py}
- qmx-agents/packages/qmx-broker/src/qmx_broker/{service.py (95-115), credentials.py}
- qmx-agents/pyproject.toml, root pyproject.toml (:92, :215-300, :341-362, :415-440, :512-535), tools/ci.py, tools/test_all.py, tools/secret_scan.py (40-200), justfile (200-215), .github/workflows/battery.yml
- qmb/src/qmb/doors/cli/__init__.py (1680-1725), qmb/src/qmb/doors/cli/host.py (1775-1840)
- Installed fastapi 0.142.2 sse.py, routing.py (keep-alive constants only)

### Boundaries
- REST/MCP ↔ `ControlService` methods only. `OPERATIONS` is the single list. The only extra REST routes are `/api/apps/{id}/sign` (operator), `/api/events/{topic}` (SSE) and `/api/health`.
- `ControlService` ↔ qmx-apps `Supervisor` (apps.db, `event_sink=_app_event`), qmx-remote `RemoteRuns` (settings `remote`), `Library`, `RunIndex`. The qmx-control package imports qmx_apps, qmx_broker and qmx_remote, and qmx_remote imports `qmx_agents.guards.journal` (models.py:11), so the control server's import graph already pulls the LangChain package (H3 §3 notes `import qmx_apps` loads LangChain/Deep Agents).
- Agents ↔ QMX tools: HTTP MCP with Bearer, in-process `create_mcp(service)`, or stdio `qmx-mcp-*` children (which make their own ControlService).
- Secrets boundary: keyring (`qmx/*`) on the laptop, a file vault on the T2 node.
- Hooks: `ControlService.watch_app_events(session_id, hook)` and `_app_hooks` are the only in-process observer mechanism. They are invoked from `_app_event` under `self._lock`. There is no general hook layer or policy engine in the control plane.

### Non-Obvious Things
1. `blocks` is never read back. History is served from the `events` log, stored twice, with no timestamps and no retention.
2. Session records have no status, no timestamp and no get-by-id route.
3. SSE sends only the inner `data`. Topic and subject are not in the payload, and the poll blocks the event loop with a fresh connection every 50 ms per subscriber.
4. `meta.interrupt_on` on MCP tools is dead metadata. The real approval map was the agent-YAML `interrupt_on`, wired through LangGraph.
5. `destructiveHint=True` covers `apps_call` and `settings_put`, but `sessions_append` and `library_save` are non-destructive, so any MCP caller can write blocks (including fake `permission` blocks) into any session.
6. `ControlService.__init__` takes `BEGIN IMMEDIATE` on control.db and rewrites runs.db at startup, so every tools child or agent build that constructs one repeats that work and contends with the server. `AG/spec.py:396,417` can create further instances.
7. `_aggregate_counts` opens runs.db and library.db inside the control.db write transaction (`_event` is called within the caller's transaction).
8. `qmb host start` passes no `--ui-origin`, so a UI on a different origin gets CORS 400. The README-level default is 5173.
9. The `blocks.type` Literal is closed: new kinds (e.g. a turn or usage block) need a change to `SessionBlock` and to the UI. The UI's names already differ (H3 §2).
10. `workflows_*` and cancel-after-restart are the only 501s. `workflows_*` fire for every call; cancel only when no in-memory canceller is registered.
11. `settings_put` writes settings.toml atomically (tmp + replace) under the in-process lock, and the `Literal` section list means a new settings section (e.g. accounts or usage config) needs a code change.
12. Test/run traps (from H3, still valid): rclone absent from PATH fails 1 of the control tests, and inside a Claude Code session `ANTHROPIC_BASE_URL` leaks into child processes.

### Open Questions
- The `sessions_append` cross-process seq collision is reasoned from the code, not reproduced. A small two-process script against a temp home would confirm.
- I did not read the UI wire code (apps/qmx-ui), qma-daemon `native_claude.py` or `native_sessions.py`, or `qmx-apps` Supervisor internals beyond signatures. Those are other explorers' slices.
- Not traced: whether any live path launches `qmx-mcp-*` stdio servers today (only the README references them); how `ui-review/repair` will name the SSE and turn routes (H3 says the UI calls no backend yet).
- The keyring backend and the exact Credential Manager target-name format on Windows were not inspected.
- The `qmx_agents` LangChain package is imported by qmx_remote and qmx_apps (H3 §3), and the planned deletion order is H3 §4. Which of these constraints applies to a new qma2 package's import graph (e.g. importing `qmx_control` from qma2) is a design call; H3's "Never" list says qma2 must not import qmx_tools, qmx_control or qma.*.