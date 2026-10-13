## Scope and verification note

Read-only pass over the detached worktree `D:/QMX-worktrees/harness-survey` (origin/rebuild/base @ 4eac8f69). I re-read the code behind every H3 claim in this slice (`D:/QMX-worktrees/agent-system/tracker/qma-v2/research/H3-code-map.md`). I did NOT re-run the tests, so the "31 of 60 native tests fail when ANTHROPIC_BASE_URL is set" figure is H3's, not mine. I confirmed the cause in code: `check_environment` and `_preflight` both raise on any `ANTHROPIC_*` name.

All paths below are relative to `D:/QMX-worktrees/harness-survey/`. Path keys:
- `RR/` = `qmx-agents/packages/qma-daemon/src/qma/daemon/request_runtime/`
- `QA/` = `qmx-agents/packages/qmx-agents/src/qmx_agents/`
- `CTL/` = `qmx-agents/packages/qmx-control/src/qmx_control/`

**Main findings:**
- H3's file:line claims all held.
- The one real gap in H3: `native_claude.py` cannot be imported without dragging in the old daemon and LangChain (see Non-Obvious #1).
- A second gap: the "only working Claude recipe" has never run live (Non-Obvious #2).
- A third gap: `import qmx_control` transitively loads LangChain (Non-Obvious #3).

---

## Components Found

### 1. The Claude Agent SDK recipe (all in `RR/`)

**`native_claude.py` (435 lines).** Two classes.
- `_ClaudeSDKLifecycle` (`:55-355`) holds all the SDK logic.
- `ClaudeSessionBackend(_ClaudeSDKLifecycle)` (`:358-435`) adds the production gate:
  - `available` is true only if executable, dedicated_home, empty_workspace and `native_policy_reviewed=True` are all supplied.
  - Its `_preflight` runs `check_environment("Claude")`, `check_claude_managed_policy()` and `check_directories(...)` before calling `super()._preflight`.
  - Its `_connect` replaces `request.cwd` with the empty workspace.
- The test-only path subclasses `_ClaudeSDKLifecycle` directly and sets `available = True`.
- Constants:
  - `CLAUDE_SDK_VERSION = "0.2.163"`
  - `CLAUDE_CLI_VERSION = "2.1.286"`
  - `provider_id = "claude-agent-sdk:0.2.163:cli-2.1.286"`
  - `_API_ENV` frozenset (`:42-52`)

**How it spawns.**
- It does not spawn the CLI itself. It builds `ClaudeAgentOptions(cli_path=<claude.exe>, ...)` and instantiates `ClaudeSDKClient(options=...)` through an injectable `client_factory` (`:283`).
- Then: `await client.connect()`, then `await client.query(request.prompt)`.
- The SDK's `SubprocessCLITransport` does the actual `anyio.open_process(..., user=options.user)` (`claude_agent_sdk/_internal/transport/subprocess_cli.py:873-881`). `user=` is POSIX-only.
- The SDK merges `os.environ` into the child, plus the `env={...}` option.
- One client per turn. `NativeSessionProvider.execute` (`native_sessions.py:125-131`) runs `asyncio.run(self.activity(...))`. The client is built through `backend_factory()` and closed in `finally`. No client is held between turns. Continuity comes only from `resume=<session_id>`.
- The SDK doc says a client must stay in one async context from connect to disconnect (`claude_agent_sdk/client.py` docstring). The recipe respects this by using one `asyncio.run` per turn.

**Options passed (`native_claude.py:239-280`):**

| Option | Value |
|---|---|
| `cli_path` | the executable |
| `cwd` | `request.cwd` |
| `resume` | session_id or None |
| `model` | `request.model` |
| `system_prompt` | `request.instructions` |
| `tools` | `[]` |
| `skills` | `[]` |
| `agents` | `{}` |
| `plugins` | `[]` |
| `allowed_tools` | `mcp__qmx__<name>` for each host tool |
| `disallowed_tools` | Agent, Task, Skill, Bash, Read, Write, Edit, WebFetch, WebSearch, ToolSearch |
| `setting_sources` | `[]` |
| `strict_mcp_config` | True |
| `settings` | `json.dumps({"disableAllHooks": True, "autoMemoryEnabled": False})` |
| `permission_mode` | `"dontAsk"` |
| `can_use_tool` | `deny` returning `PermissionResultDeny` |
| `hooks` | `{"PreToolUse": [HookMatcher(hooks=[pre_tool])]}` |
| `mcp_servers` | `{"qmx": create_sdk_mcp_server(name="qmx", tools=native_tools)}` |
| `max_turns` | 8 |
| `include_partial_messages` | False |
| `max_buffer_size` | 262144 |
| `verbatim_prompts` | True |
| `extra_args` | `{"disable-slash-commands": None}` |
| `env` | `CLAUDE_CONFIG_DIR=<dedicated home>`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`, `CLAUDE_CODE_ENABLE_TELEMETRY=0` |

- **Host tools** (`:191-220`). Each `{name: json_schema}` becomes `tool(name, "Host-admitted QMX read operation", schema)(call)`.
  - `call` awaits `operation(op_name, arguments, uuid4().hex)`.
  - It returns `{"content":[{"type":"text","text": json.dumps(result)}]}`.
  - On any exception it stores `self.operation_error` and returns `{"is_error": True, "content": "Host operation refused"}`. Host exceptions never reach the model.
- **`pre_tool` hook** (`:225-237`). It denies if `payload.get("agent_id")` is set (a subagent) or `tool_name` is not in `{mcp__qmx__<name>}`. Otherwise it returns `{}`.
- **Preflight** (`_preflight`, `:97-160`), run through `call_blocking`:
  1. Env-name check: any `ANTHROPIC_*` or `CLAUDE_CODE_USE_{BEDROCK,VERTEX,FOUNDRY}` raises `ProviderError("subscription_required")`. Names only, never values.
  2. If `verify_runtime`: `version("claude-agent-sdk") == "0.2.163"`.
  3. `claude --version` must equal exactly `"2.1.286 (Claude Code)"` (`:114`).
  4. `claude auth status` runs with `CLAUDE_CONFIG_DIR=<home>`, a 10 s timeout, and `{**os.environ, ...}` as env. Its JSON stdout must show `loggedIn is True`, `authMethod == "claude.ai"`, `apiProvider in {None,"firstParty"}`, and `Path(configDirectory).resolve() == dedicated_home.resolve()`.
  5. The dedicated home and `cwd` must be directories.
  6. The home must not contain `settings.json`, `settings.local.json`, `hooks.json`, `plugins`, `agents` or `skills`.
- **Events** (`events()`, `:289-345`), over `client.receive_response()`:
  - `SystemMessage(subtype="init")`:
    - Takes `data["session_id"]`.
    - Refuses if a resume was requested and the id differs ("Claude resumed another session").
    - Refuses if `data["tools"]` contains anything outside the permitted `mcp__qmx__*` set.
    - Sets `initialized` and yields `SessionEvent("started", id)`.
  - `AssistantMessage`:
    - Refuses if not initialized, if `parent_tool_use_id is not None`, or if the session id differs.
    - `TextBlock` yields `SessionEvent("text", ...)`.
    - A `ToolUseBlock` outside the permitted set is an error.
    - A `ServerToolUseBlock` or `ServerToolResultBlock` is an error.
  - `ResultMessage`:
    - Refuses non-human `origin`.
    - Checks the session id matches.
    - `terminal_reason in {"aborted_streaming","aborted_tools"}` maps to `interrupted`.
    - `is_error` or `subtype != "success"` maps to `failed`. Otherwise `completed`.
    - Yields `SessionEvent("terminal", id, text=result, status=...)` and returns.
  - A `SystemMessage` with a `task_*` subtype raises "background task refused".
  - Not handled: `RateLimitEvent`, `StreamEvent`, `ThinkingBlock` and `ToolResultBlock` fall through silently. `ResultMessage.total_cost_usd`, `.usage`, `.model_usage`, `.errors`, `.api_error_status` and `.permission_denials` are read nowhere.
- **Cancel** (`:347-350`). `client.interrupt()`. If called before `turn_submitted` it raises `ProviderError("interrupt_pending")`, and the watcher retries every 50 ms.
- **Close**: `client.disconnect()`.

**`native_boundary.py` (123 lines).**
- `call_blocking(fn, *a)` (`:16-41`):
  - Runs `fn` in a daemon `threading.Thread(name="qmx-native-sdk")`.
  - Delivers the result through `loop.call_soon_threadsafe` into a future.
  - Purpose: cancelling the await must not strand `asyncio.run`'s default executor.
- `check_environment(provider=)` (`:44-75`) deny list:
  - OpenAI/Codex: `OPENAI_API_KEY`, `CODEX_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_API_BASE`, `CODEX_*` auth vars.
  - Network and TLS: `NODE_OPTIONS`, `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `SSL_CERT_FILE`, `SSL_CERT_DIR`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`.
  - Claude: `CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK`, `CLAUDE_CODE_USE_*`, `CLAUDE_CODE_OAUTH_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR`, `CLAUDE_CODE_SESSION_ACCESS_TOKEN`, `CLAUDE_CODE_CUSTOM_HEADERS`.
  - Prefixes: anything starting `ANTHROPIC_` or `AZURE_OPENAI_`.
  - It raises `ProviderError("subscription_required")`.
- `check_directories(home, workspace, configuration_names=...)` (`:78-96`) requires:
  - Absolute paths.
  - Existing directories.
  - Not symlinks or junctions (`Path.is_junction`, a Windows-aware check).
  - Home is not `Path.home()`.
  - Home and workspace are distinct and not nested.
  - Workspace is empty.
  - No config files in the home.
- `check_claude_managed_policy()` (`:99-123`):
  - Refuses if `C:/Program Files/ClaudeCode/managed-settings.json` or `managed-settings.d` exists.
  - On `os.name == "nt"`, refuses if `winreg` finds key `SOFTWARE\Policies\ClaudeCode` under HKLM or HKCU.
  - PermissionError also refuses.

**`native_sessions.py` (446 lines).**
- Dataclass `SessionEvent(kind: "started"|"text"|"terminal", session_id, turn_id="", text="", status: "completed"|"interrupted"|"failed"="completed")`.
- `SessionBackend` Protocol (`:39-63`): `provider_id`, `binding_identity`, `available`, `async start(request, operation, *, check)`, `async resume(session_id, request, operation, *, check)`, `events() -> AsyncIterator[SessionEvent]`, `async cancel()`, `async close()`.
- `NativeSessionProvider` (`:66-446`) is the daemon glue, tied to the old `RequestRuntime`. Its useful ideas:
  - Hard bounds: `request.timeout_seconds` in `(0, 600]`, wrapped in `asyncio.timeout(timeout + 2)`; `max_events=1024`; `max_result_bytes=65536`; `max_tool_calls=8`.
  - A `guard()` closure checks the cancellation token, the deadline and live scope. It runs before start, per text event, per tool call and after tool output.
  - A `watch()` task polls the guard every 50 ms and calls `backend.cancel()`, retrying on "interrupt pending".
  - Resume is journal-keyed. The key is a sha256 over the profile, instructions, model, backend binding, cwd, tool grants and so on. The record lives in `JournalRecords("native_session", key)` with statuses `pending | completed | interrupted | not_submitted | outcome_unknown`.
  - A previous record in any other state refuses the turn with `outcome_unknown`. It is never auto-replayed and never falls back to another provider.
  - Pre-turn refusals (`unsupported`, `unsafe_config`, `auth_required`, `subscription_required`, `invalid_input`, `interrupt_pending`, `scope_interrupt`, `cancellation_requested`) are retry-safe only if `backend.turn_submitted is False and calls == 0`.
  - Cleanup in `finally`: cancel the watcher, then `asyncio.timeout(2)` around cancel and `backend.close()`.
- One serialization lock (`_activity_lock`) per provider instance. A second concurrent activity raises `session_busy`.
- The host-tool dispatcher is `ToolLoopProvider.dispatch` (`tool_loop.py`), which imports LangChain.

**`native_codex.py` (553 lines).** Drives the Codex app-server through `openai_codex` (`CodexClient`, `CodexConfig`), pinned to `0.160.0`.
- It sets a locked-down `CONFIG` plus about 28 `DISABLED_FEATURES` (`:37-77`).
- It validates the effective config via `config/read`.
- It requires a ChatGPT account (`account_read`).
- It passes tools as `dynamicTools`.
- It declines command and file approvals through an `approval_handler`.
- It is not the planned OpenAI engine. The plan uses the `openai-agents` SDK. Reuse is limited to the idea of an effective-config readback.

**`native_composition.py` (84 lines).** `compose_native_metadata_provider(runtime, ...)` builds a `NativeSessionProvider` with one hard-coded tool, `research_browse`, tied to `qml.research.browse@1`. Daemon-specific; nothing to reuse.

**`native_configuration.py` (35 lines).** A frozen dataclass `NativeProviderConfiguration(identity, backend: "codex"|"claude", executable, dedicated_home, empty_workspace, native_policy_reviewed)`, with an `execute` that only raises `unbound_session`.

**`ProviderRequest`** (`RR/contracts.py:74-83`): frozen slots dataclass `(prompt, model=None, cwd="", thread_id=None, timeout_seconds=120, instructions="", request_id="", graph_thread_id=None)`.

**`ProviderError(RuntimeError)`** (`RR/providers.py:24-29`): has a `.code` string. Codes in use: `subscription_required`, `auth_required`, `unsupported`, `unsafe_config`, `invalid_input`, `protocol_error`, `outcome_unknown`, `interrupt_pending`, `scope_interrupt`, `cancellation_requested`, `tool_denied`, `session_busy`, `unbound_session`, `native_failed`. `ProviderCancelled` is a subclass.

**Tests that cover the native code** (`qmx-agents/packages/qma-daemon/tests/`):

| File | Test functions |
|---|---|
| `test_native_sessions.py` | 17 (parametrized, 604 lines) |
| `test_native_codex_bridge.py` | 14 |
| `test_native_operator_routing.py` | 5 |
| `test_native_configured_daemon.py` | 4 |
| fixtures `native_codex_fixture.py`, `native_daemon_fixture.py` | — |

- Both Claude test layers use a fake `client_factory`. In-file `FakeClaudeClient(options=...)` implements `connect`, `query`, `receive_response` (yielding `SystemMessage("init", {"session_id", "tools"})`, `AssistantMessage([TextBlock])`, `ResultMessage(...)`), `interrupt` and `disconnect`.
- Notable assertions:
  - `test_claude_sdk_options_remove_native_access_and_resume_verbatim` (`:256`) calls `SubprocessCLITransport("", options)._build_command()` and checks `--tools ""`, `--strict-mcp-config` and `--setting-sources=`.
  - `test_sdk_mcp_server_real_host_operation_and_resume` (`:415`) drives the real SDK MCP server through `mcp.shared.memory.create_client_server_memory_streams`.
  - `test_claude_refuses_api_environment_without_reading_values` (`:294`) is parametrized over four env names.
- Heavy helpers: `from test_research_workflow import compose, submit, supply, value` pulls in the full daemon `RequestRuntime`. The portable part is only `FakeClaudeClient` and the options-inspection tests.
- The tests `importorskip("claude_agent_sdk")` and `importorskip("openai_codex")`.
- Offline helpers: `qmx-agents/examples/native_sdk_offline_check.py` (builds the real command line without auth; asserts SDK 0.2.163 and CLI 2.1.286) and `examples/native-session-runtime-check.json`.
- That JSON records `authentication_performed: false`, `model_calls: 0`, `subscription_connection_verified: false`, `managed_policy_isolated: false`.
- The README for the lane is `qmx-agents/examples/NATIVE_AGENT_SESSIONS.md`. It states: "No live subscription connection, login, account-status call or model call was performed."

**Windows specifics found:**
- `cli_path` must be a native `.exe`. The SDK refuses npm `.cmd` shims and extensionless wrappers (`subprocess_cli.py:_find_cli`, `_is_windows_native_exe`).
- 0.2.163 has no Windows wheel, so no bundled CLI exists (H3; installed `claude_agent_sdk/` has no `_bundled`). It falls back to `shutil.which("claude")`.
- The CLI that `which` finds here is `C:\Users\Mubarak\.local\bin\claude.exe`, version 2.1.296 per H3. The pin is 2.1.286, so the exact-match check at `:114` would refuse this machine.
- `ClaudeAgentOptions.user` is POSIX-only (`:881`). The architecture plans a custom `SpawnTransport`, or a `cli_path` shim.
- `ClaudeSDKClient(options, transport=)` accepts a custom `Transport`. When one is used, "CLI-flag options in `options` are not applied to it".
- `call_blocking` exists because blocking SDK or subprocess calls must not strand `asyncio.run`'s executor.
- Windows managed-policy probing uses `winreg`, plus `Path.is_junction`.

### 2. `qmx_agents` copilot path (LangChain/LangGraph/Deep Agents)

Core is 4,090 lines. Entry points:
- `QA/spec.py` — `load_spec`, `build_agent`, `BuildContext`, `_build`
- `QA/copilot.py` — `build_copilot`, `stream_turn`, `AppSandbox`
- `QA/tasks.py` — `BackgroundTasks`

**`build_copilot(ctx: BuildContext, data: DomainContext|None=None) -> Any`** (`copilot.py:54-95`):
- Requires `ctx.control` (a `ControlService`), `ctx.qmx_home`, `ctx.checkpointer`, a `data-analyst` sandbox backend, and `ctx.run.session_id`.
- Creates a `RunJournal` at `<home>/runs/<session_id>/journal.jsonl`.
- Registers in-process MCP targets: `create_mcp(ctx.control)` as `qmx-control`, and `create_server(name, domain)` for `data`, `backtest` and `research`.
- Wires `memory_approval` to `langgraph.interrupt({"kind":"global_memory",...})`.
- Loads `QA/agents/copilot.yaml`. Its relevant fields: model `tier:reasoning_high`, `interrupt_on: {apps_publish: true, apps_start: true}`, `budget {model_calls:200, tool_calls:400}`, permissions, sub-agents (researcher, data-analyst, app-builder) and background task overnight-builder.
- Calls `build_agent(spec, ctx)`, which ends in `deepagents.create_deep_agent(...)` and returns a `CompiledStateGraph`.
- `spec._build` (`spec.py:246-499`):
  - Discovers MCP tools with `langchain.mcp.MCPAdapter`.
  - Runs `check_tool` on every tool.
  - Builds sub-agents recursively.
  - Opens `MemoryManager` and `StoreMemoryProvider` on SqliteStore.
  - Starts `watch_breakers(control, session_id)`.
  - Composes the middleware list: Journal, router, ContextEditing, memory, AdmissionState, MoneyPath, AppHooks, ResearchLibrary, ModelCallLimit, ToolCallLimit, JournalApprovals.

**`stream_turn(graph, service, session_id, prompt: str|Command, *, context=None, mode="do"|"plan") -> None`** (`copilot.py:98-213`) — the engine-events-to-blocks projector:
- Sets `request_model = "tier:reasoning_high"` if mode is `plan`, else `"tier:workhorse"`.
- A str prompt first appends a `user` block `{text}`. A `Command` resumes an interrupt.
- It iterates `graph.astream(inputs, config={"configurable":{"thread_id": session_id}}, context=run, stream_mode="updates", subgraphs=True, version="v2")`.
- A non-empty namespace (a subgraph) creates a child session via `service.sessions_create(SessionInput(title="Delegated task", parent_id=session_id))`. It appends an `agents` block `{session_id, state:"working", namespace}` to the parent.
- For each node update (`chunk["data"]`):
  - `__interrupt__` appends `permission` `{interrupt_id, request}` and adds the target to the `waiting` set.
  - Each message in `update["messages"]` is deduped by `f"{target}:{message.id}"`.
  - `AIMessage.text` becomes `text` `{text}`.
  - Each tool call becomes `tool` `{id, name, arguments, state:"started"}`. `write_todos` also appends `plan` `{todos}`. `task` and `start_task` also append `agents` `{name, state:"working"}`.
  - `ToolMessage` becomes `tool` `{id: tool_call_id, name, state: status, result: text}`. If status is not error and `artifact.structured_content` (or JSON text) is a dict with `artifact_id`, it also appends `artifact`.
- At the end, each child gets an `agents` block with `state` of `"needs_you"` if it was waiting, else `"complete"`.
- Blocks are written through `ControlService.sessions_append`, which emits the SSE event. Nothing is streamed token by token; blocks are completed messages.
- Block kinds produced: `user`, `text`, `tool`, `plan`, `agents`, `permission`, `artifact`. The service's 14-kind closed list is `user, text, plan, agents, tool, changed, artifact, table, entity, question, permission, panel, handoff, needs_you` (`CTL/service.py:54-71`, `SessionBlock`). The copilot never emits `changed`, `table`, `entity`, `question`, `panel` or `handoff`.

**Approval handling.** There are two interrupt shapes:
- LangChain `HumanInTheLoopMiddleware` via `JournalApprovals` (`guards/middleware.py:~200`). The resume payload is `{"decisions":[{"type":"approve"|"reject"}]}`.
- The global-memory interrupt, where the resume payload is a bare bool (see `scripts/live/copilot_build_app.py`).
- Pending approvals live in the LangGraph checkpointer, an `AsyncSqliteSaver` (`<home>/copilot/threads.db` in the script). The `permission` block is only a notification. There is no approvals table and no route.

**Who calls it.**
- Only `scripts/live/copilot_build_app.py` (operator-only, interactive `input()` loop: `stream_turn`, then `graph.aget_state(config).next`, then `Command(resume=...)`).
- `qmx_agents/tasks.py:107,136` (`BackgroundTasks._run` calls `build_agent` and `stream_turn` for `start_task`).
- Tests `QA/../tests/test_copilot.py` and `test_copilot_sandbox.py`.
- No `qmx-control` route calls it, and `CTL/server.py` does not import `qmx_agents`.
- **Live-model status.** The tests use fake models. `models.yaml` routes everything through CLIProxy (`http://127.0.0.1:8317`) or OpenRouter, i.e. API-style routes, not the subscription-native SDK. H3 says it never ran against a real model; I did not contradict that.

**`BackgroundTasks`** (`tasks.py`): `start_task`, `check_task`, `cancel_task`, `list_tasks`. Each run gets its own `AsyncSqliteSaver` DB at `<home>/copilot/tasks/<run_id>/threads.db` and its own `RunJournal`. Status goes to `service.record_work("runs", run_id, {...}, cancel=...)`. Statuses: `running | completed | needs_you | cancelled | failed`.

### 3. Reusable modules: LangChain import status

The table has one row per module. "Direct LC" means the file's module-level imports include langchain, langgraph or deepagents.

| Module | Direct LC? | Public API | qma2 verdict |
|---|---|---|---|
| `QA/guards/journal.py` (127) | No. Imports only stdlib and pydantic. | `encoded(value)->bytes`, `fingerprint(value)->str` (sha256 of canonical JSON), `timestamp()`, `RunJournal(path, run_id, *, clock)` with `.append(event, payload)->dict`, `.store_result(bytes)->path`, `.quarantine(bytes, reason)`, `.close()` and context manager | Copy as-is. Importing it from `qmx_agents` drags in `guards/__init__.py`, which imports `admission` (deepagents) and `money_path` (langchain_core). |
| `QA/guards/parent_surfaces.py` (96) | No. Imports only stdlib. | `is_parent_surface_permitted(library, kind)->bool`; `ParentLibrary`, `ParentSurfaceKind`, `ProhibitedRecordFamily` StrEnums; `PERMITTED_PARENT_SURFACES`; `ParentSurfaceError` | Copy as-is. |
| `QA/guards/experiments.py` (138) | No. Imports `journal` only. | `ExperimentLedger(path, experiment_id)`, SQLite append-only with triggers; `ExperimentEntry`; `EvidenceRejected` | Copy as-is. |
| `QA/guards/money_path.py` (279) | Yes at module level. `langchain_core.tools.BaseTool` and `qmx_broker.models/service`. | Neutral part: `MoneyPathAct`, `MoneyPathDeniedAct` StrEnums (9 + 29 acts), `MONEY_PATH_ACT_ALIASES`, `_normalize_act_token`, `match_money_path_act(act)->str|None`, `is_money_path_act_denied`, `check_descriptor(name, metadata)` (`:247-279`), `MoneyPathDenyError`. Bound part: `OrderProposalTool`, `BrokerOrderProposalTool`, `check_tool(BaseTool)`. | Copy lines 21-162 and 247-279. `check_descriptor` walks `mcp/tool/annotations/_meta` nested dicts. It collects `act/acts/name/tool_name` tokens, splits them on `_ . : /` to strip server prefixes, and refuses a `money_path` flag, a non-permitted `parent_library/parent_surface`, any `record_family`, or any token matching a denied act. Role prefixes `paper_/live_/demo_` (and `*_only_`) are stripped. Architecture note Z15: normalise the tool name before matching. Used live by `qmx-apps` `supervisor.py:473,671` on mini-app tool descriptors, and `qmx-broker/server.py:67` flags `propose_order` with `meta={"money_path": True, "proposal_only": True}`. |
| `QA/guards/admission.py` (277) | Yes. `deepagents.backends.protocol` | `AdmissionGate`, `WriteProposal`, `valid_path`, `AdmissionDenied`; `AdmissionBackend` / `AdmissionSandboxBackend` are Deep Agents backends | Copy only the content-plus-hash rule (`:34-113`). |
| `QA/guards/hooks.py` (179) — "P20 hooks" | Yes. `AppHooksMiddleware` is a LangChain `AgentMiddleware`. It imports `qmx_apps`, `qmx_control.service`. | `AppHooksMiddleware` (before apps_publish, require green tests for the current `definition_hash`; after apps_create/update, auto-run tests; clamp `auto_publish=False` if `explicit_publish`). `watch_breakers(service, session_id)` (`:153-179`): when a mini-app event has `status == "tripped"`, append a `needs_you` block and call `service.notify_app`. | Re-implement `AppHooksMiddleware` as policy rules. `watch_breakers` is plain code needing a `ControlService`. It is the only producer of `needs_you` blocks today. |
| `QA/guards/middleware.py` (237) | Yes | `JournalMiddleware` (logs `run_start/run_end/model_call/model_error/tool_start/tool_end`; `model_call` records `usage` = `AIMessage.usage_metadata` and `response_metadata`), `MoneyPathMiddleware`, `JournalApprovals(HumanInTheLoopMiddleware)`, `AdmissionStateMiddleware` | Reference for journal event vocabulary only. |
| `QA/memory.py` (678) | Yes at module level | Neutral: `Scope` StrEnum (task/workflow/session/global), `MemoryContext(profile,node,role,session_id,workflow_id,task_id)`, `MemoryRecord`, `ConfigField`, `Approval`, `MemoryProvider` Protocol (`:~105-135`: put/get/delete/search/system_block/prefetch/on_turn_end/on_pre_compress/on_scope_end/tools/config_schema), `namespace()`, `_INJECTION` regex. Bound: `tools() -> list[BaseTool]`, `StoreMemoryProvider` (LangGraph `SqliteStore`), `MemoryManager`, `MemoryMiddleware`, summarization. | Copy the protocol and dataclasses. Drop `tools()`. |
| `QA/router.py` (322) | Yes. `deepagents`, `langchain` middleware, `init_chat_model`. | Neutral: `Tier = fast|workhorse|coding|reasoning_high`, `Provider` Literal (anthropic/openai/openrouter/local/cliproxy), `model_selector(value)` (requires `tier:<tier>` or `provider:<exact id>`; rejects `~` and `*latest`), `ProviderConfig`, `RouterConfig` (profiles must define all four tiers; fallbacks; `max_retries`; `mcp_servers`), `load_config`, `credential(provider)` (keyring `qmx/<provider>`; CI env fallback `QMX_<PROVIDER>_API_KEY`), `RunContext` dataclass. Bound: `ModelRouter.resolve`, middleware. | Copy the neutral parts. `RunContext` is the per-call override ladder `model < node < app < workflow < agent_node < subagent < request_model`. |
| `QA/spec.py` (499) | Yes | `AgentSpec` (name, model, system_prompt, tools, mcp_servers, skills, memory, subagents, background_tasks, interrupt_on, permissions, budget), `MemorySpec`, `SubagentSpec`, `Permissions` (`.rules()` is Deep Agents `FilesystemPermission`), `Budget(model_calls, tool_calls)`, `load_spec`, `mcp_configuration`, `BuildContext` | Copy the fields, `load_spec` and `mcp_configuration` (`spec.py:108-143`, `:197-245`). Drop `_build`, `guards()`, and the `Permissions.rules()` method. |
| `QA/router.py` accounts and usage | n/a | `ModelRouter.list_models()`, `accounts()`, `quotas(plugin_id)` only call CLIProxy (`/v1/models`, `/v8/management/credentials`, `.../plugins/<id>/quota`) | Nothing reusable for subscription routing or usage ledgers. |

**Usage and cost tracking.** There is no usage ledger anywhere in the product code.
- Closest: `JournalMiddleware._model_response` journals `usage_metadata` per model call, and `Budget` caps call counts (not tokens or cost).
- `adws/adw_modules/agent_pi.py:189-200,369-378` accumulates per-turn tokens and `usage.cost.total` from the `pi` harness's `message_end` events. It is a different harness; reference only.
- The Claude SDK itself provides `ResultMessage.total_cost_usd`, `.usage`, `.model_usage` (per model), `.num_turns`, `.duration_api_ms`, `.api_error_status`, `.permission_denials` and `RateLimitEvent(rate_limit_info: RateLimitInfo{status: allowed|allowed_warning|rejected, rate_limit_type, overage_status})`. The existing recipe discards all of these.

**Money/broker refusal.**
- Barrier: `money_path.py` as above.
- Producer: `qmx_broker` writes unsigned proposals to a Portfolio queue for operator signature. No venue dependency.
- `qmx-tools` `registry.py:234` exposes `propose_order` on the `node` group.
- `qmx-control` `settings_put` rejects secret-looking keys (`_no_secrets`, `service.py:~79-91`).
- A tripwire test (`qmn/tests/test_qmn_fx_paper.py:~679`) asserts qma-core/wire/daemon, qmb and qml never import `qmf.venue`.

**`qmx-tools`** (`qmx-agents/packages/qmx-tools/src/qmx_tools/`):
- `registry.py` `domain_functions(ctx) -> dict[group, dict[name, fn]]` holds 13 functions over groups data/backtest/research/node.
- `servers.py` `create_server(name, ctx)` makes a FastMCP stdio server per group. `readOnlyHint` is false for `run_backtest`, `library_save` and `propose_order`.
- `registry.py:274-281` `default_tool_registry` wraps them as LangChain `BaseTool` named `qmx-<server>.<name>`.
- `service.py:126-128` `DomainContext.__post_init__` builds a `ControlService(self.root)`, so each MCP child process is a second writer on `control.db`.

### 4. The old QMA runtime (qma-core / qma-wire / qma-daemon)

Daemon subpackage sizes (lines): taskgraph 9,918; request_runtime 11,089; plugins 6,925; staging 5,113; sessions 4,200; backtest 3,489; envs 3,437; journal 2,879; artifacts 2,043; discovery 1,962; hooks 1,677; host_control 1,692; bus 1,544; ledgers 1,378; experiments 1,341; knowledge 1,278; and smaller ones.

**What still imports or references it outside the three packages** (verified with `git grep`; items marked NEW are not in H3):
- **QMB**
  - `qmb/src/qmb/doors/cli/host.py:104` `DAEMON_SPAWN_MODULE = "qma.daemon"`. Strings and helper code only; no `import qma`.
  - `qmb/src/qmb/analysis/variants.py:65-66,107` holds only schema-id and origin strings.
  - `qmb/tests/test_cli_host.py` (`-m qma.daemon` argv assertions at `:276,:331`) holds strings only.
  - `qmb/tests/test_operator_study_cli.py:21-27+` hard-imports `qma.core.*` and `qma.daemon.*` (12 hits).
  - `qmb/examples/host_lifecycle_usage.py:111` (NEW) asserts `argv[-2:] == ("-m","qma.daemon")`.
- **QMN**
  - `qmn/examples/spot_paper_journey.py:15-17` hard-imports `qma.daemon` (`AuthoritativeJournal`, `PersistenceSubstrate`, `ProductSessionService`, `SpotQueryDoor`) and `qma.wire.invocation_envelope`.
  - `qmn/tests/test_qmn_fx_paper.py:682-684` (NEW) is a path-only "no `qmf.venue` import" scan that skips missing roots (`if not root.is_dir(): continue`). It is safe after deletion.
- **QML**
  - `qml/tests/test_generation_gaps_unfilled.py:62,431-432` (NEW) scans `qma-daemon/src/qma/daemon/backtest` and `experiments`. It uses `rglob`, which yields nothing on a missing dir in 3.14, so it would pass vacuously.
  - `qml/tests/test_generation_ownership.py:274` (NEW) does `qma-core/src` `rglob` for forbidden tokens. It is also vacuous once deleted.
- **qa/**
  - `qa/integration/test_qma_authenticated_study.py` (17 hits) and `test_qma_registered_replay.py` (19 hits) hard-import qma.* and spawn `-m qma.daemon`. They are not run in CI.
  - `qa/backend-quality/ci-inventory.json:110,144-146` lists qma paths (NEW).
- **Root `pyproject.toml`**: `:228-230` pytest pythonpath, `:341` comment, `:360-362` pyright extraPaths.
- **`tools/`**
  - `backend-integration-check.ps1` (NEW; many `qma-daemon/tests/*` paths, including `test_native_sessions.py` and `test_native_codex_bridge.py`, plus coverage flags at `:130`).
  - `spot-paper-check.ps1:11-28,39` (NEW).
  - `backend-source-provenance.py:18-20`, `build_release.py:266` (bundled_packs), `nested_coverage_report.py:13`, `secret_scan.py:65`.
  - `tools/tests/test_qma_callers.py`.
- **`scripts/dev/qma_callers.py`**: the inventory script.
- **`qmx-agents/`**
  - `pyproject.toml:14,17,26-28,62-64,71-73,...`.
  - `examples/*.py` (native_daemon_proof, native_session_proof, scaffold_overview, scoped_tool_request).
  - `plugins/*/daemon/plugin.py` (5 desk packs) import `qma.core`.
  - `tests/test_workspace_scaffold.py`.
- **`apps/qmx-ui`**: strings only (`client-of-qma-wire`, a comment about DEC-0485). No imports.
- **Nothing in `qmx-control`, `qmx-apps`, `qmx-remote`, `qmx-broker` or `qmx-tools` imports `qma.*`.**

**Worth keeping as reference before deletion** (beyond the recipe):
- `native_sessions.py` — the guard/watch/cleanup structure, the journal-keyed `outcome_unknown` no-replay rule, the pre-turn retry-safe code list, and the bounds (events 1024, result 64 KiB, tool calls 8, timeout at most 600 s).
- `tool_loop.py` header — "model output never supplies envelope, grant, target; a lost tool outcome interrupts and needs reconciliation".
- `sdk_middleware.py` `HostScopeMiddleware` — revalidating live scope before and after every model or tool call.
- `native_codex.py` — the effective-config readback pattern, `DISABLED_FEATURES`, and `config/read` verification.
- `native_boundary.py` — as noted.
- Tests `test_native_sessions.py` — the `FakeClaudeClient` pattern and the `SubprocessCLITransport._build_command()` flag assertions.
- `examples/NATIVE_AGENT_SESSIONS.md`.
- `examples/native_sdk_offline_check.py`.
- Everything else in the 113k lines is daemon ontology and has no counterpart in qma2.

### 5. Mini apps: how they invoke agents

Both are in-process LangChain/Deep Agents with recorded fakes, inside the app's own venv.
- `examples/apps/weekend-watcher/server.py:10-52`:
  - FastMCP stdio server, tool `summarize(snapshot)`.
  - Builds `ModelRouter(RouterConfig(...local:recorded), {"local:recorded": RecordedModel(GenericFakeChatModel)})`, `load_spec("agents/watcher.yaml")`, then `await build_agent(spec, BuildContext(router, checkpointer=InMemorySaver()))` and `graph.ainvoke`. The fake emits a canned string.
  - Manifest: `risk=runs`, `kind=headless`, `entrypoints.agents=["agents/watcher.yaml"]`.
  - No secrets.
- `examples/apps/macro-daily-bias/macro_bias.py:15-122`:
  - `refresh(volume, data_target, model)` reads bars via fastmcp `Client` to qmx-data (token `QMX_DATA_TOKEN`).
  - Uses either a recorded fake model (when `QMX_STAGE in {"tests","sandbox"}`) or `init_chat_model(config["model"], base_url=config["model_url"], api_key=QMX_MODEL_KEY)`.
  - Builds `BuildContext(router, checkpointer=InMemorySaver(), general_purpose_subagent=False)`, runs `build_agent(load_spec("agents/analyst.yaml"))`, validates the JSON answer as a `Bias` model, and writes to `app.db`.
  - Manifest: `risk=shows`, `kind=both`, `schedule.interval_seconds=86400`, secrets `QMX_DATA_TOKEN="qmx/control-token"` and `QMX_MODEL_KEY="qmx/cliproxy"`.
- Both `pyproject.toml` files pin `qmx-agents` to old git commits (weekend `697b5a09`, macro `e27a5136`, subdirectory `qmx-agents/packages/qmx-agents`). Both commits exist in this repo (`git cat-file -t` returns `commit`), and each app ships its own `uv.lock`. So deleting the package from the tree does not break these apps. They keep running old LangChain from the pin.
- Things that do reference them in-tree:
  - `qmx-apps/tests/test_apps.py:358-392` installs and starts weekend-watcher via `uv sync` and asserts `apps/weekend-watcher/memory.db` exists (needs network or a warm cache).
  - `qmx-agents/packages/qmx-agents/tests/test_copilot.py:34,93-162` drives the macro-daily-bias app through a scripted copilot. This test goes with D2.
  - `qmx-apps/pyproject.toml:60` has pyright `extraPaths` for macro-daily-bias and mql5-articles.

---

## Flow

**Today's copilot turn (the only runnable path is a script, not the host):**
1. `scripts/live/copilot_build_app.py` makes `ControlService(home)`, `sessions_create(SessionInput(title=...))` and an `AsyncSqliteSaver` at `<home>/copilot/threads.db`.
2. It builds `BuildContext(ModelRouter(load_config()), run=RunContext(session_id=...), qmx_home, control, checkpointer, backend, agent_backends={"data-analyst": AppSandbox(...)})`.
3. `build_copilot(ctx)` then `build_agent(...)` returns the LangGraph.
4. `stream_turn(graph, service, session_id, text, context=ctx.run)`:
   - Appends the user block.
   - `graph.astream(..., stream_mode="updates", subgraphs=True)` projects completed messages into typed blocks via `service.sessions_append`.
   - Each append is one transaction in `control.db`: a `blocks` row plus an `events` row (topic `sessions`, subject = session id).
5. A paused graph leaves `graph.aget_state(config).next` non-empty. The script prints `task.interrupts`, asks `input()`, then calls `stream_turn(..., Command(resume=...))`.
6. Any SSE client sees blocks via `GET /api/events/sessions?subject=<session_id>`.

**Native Claude turn in the old daemon (for the recipe):**
1. `NativeSessionProvider.execute` calls `asyncio.run(activity)`.
2. `_activity` validates the request against the admitted `RequestRuntime` spec, builds a journal key, and refuses if the prior record is not terminal.
3. It writes `native_session` `pending`, then `backend.start` or `backend.resume(previous session_id)`:
   - `_connect` runs `call_blocking(_preflight)`.
   - It builds the options, calls `client_factory(options=...)`, then `connect()`, then the second `check()`, then `query(prompt)`.
4. `backend.events()` is read while `watch()` polls the guard; tool calls go through `operation()` into `ToolLoopProvider.dispatch`.
5. The terminal event writes the `native_session` record `completed|interrupted`, and `ProviderResult(content, session_id)` returns. `finally` cancels the watcher, then cancel and `close()` within 2 s.

---

## Files Read

- `qmx-agents/packages/qma-daemon/src/qma/daemon/request_runtime/`: `native_claude.py` (all), `native_boundary.py` (all), `native_sessions.py` (all), `native_codex.py` (1-330), `native_composition.py`, `native_configuration.py`, `contracts.py` (the ProviderRequest/Event/Result/Capabilities region), `providers.py` (head and ProviderError), `tool_loop.py` and `sdk_middleware.py` (heads), `durable_memory.py` and `scoped_memory.py` (heads).
- `qmx-agents/packages/qma-daemon/tests/test_native_sessions.py` (1-310, 380-490).
- `qmx-agents/examples/`: `native_sdk_offline_check.py` (head), `native-session-runtime-check.json`, `NATIVE_AGENT_SESSIONS.md`, `native-session-requirements.txt`.
- `QA/`: `copilot.py` (all), `spec.py` (60-499), `router.py` (all), `memory.py` (1-200 plus symbol index), `tasks.py` (1-152), `models.yaml`, `agents/copilot.yaml`, `guards/__init__.py`, `guards/journal.py`, `guards/money_path.py`, `guards/parent_surfaces.py`, `guards/hooks.py`, `guards/middleware.py` (28-237), `guards/experiments.py` (head); import scans of every module.
- `CTL/service.py` (1-360), `CTL/server.py` (1-135).
- `qmx-agents/packages/qmx-tools/src/qmx_tools/` (`servers.py`, parts of `service.py` and `registry.py`).
- `qmx-agents/packages/qmx-remote/src/qmx_remote/worker.py` (130-215).
- `qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py` (120-160, plus grep for `check_descriptor`).
- `scripts/live/copilot_build_app.py` (all).
- `examples/apps/weekend-watcher/{server.py,pyproject.toml,app.toml}` and `examples/apps/macro-daily-bias/{macro_bias.py,pyproject.toml,app.toml}`.
- `qmx-agents/.venv/Lib/site-packages/claude_agent_sdk/` (`types.py` ResultMessage, RateLimitEvent and Options field list; `_internal/transport/subprocess_cli.py` `_find_cli` and spawn at 870-885; `client.py` constructor; `_cli_version.py`).
- `adws/adw_modules/agent_pi.py` (usage accumulation).
- `scripts/dev/qma_callers.py` (head).
- Many `git grep` sweeps for `qma.*` references.
- In the agent-system worktree: `tracker/qma-v2/research/H3-code-map.md` (all), `tracker/qma-v2/ARCHITECTURE.md` §2.0, §2.3, §5 and headings.

## Boundaries

- **Engine seam (planned):** `qma2.engine.port.EngineAdapter` (`open/turn/answer/interrupt/close`), with `ClaudeAdapter` and `OpenAIAdapter` (ARCHITECTURE §2.3). The old `SessionBackend` Protocol (`start/resume/events/cancel/close`) is the nearest existing shape.
- **Block sink:** `ControlService.sessions_append(session_id, SessionBlock{type, content})` on a closed list of 14 kinds. The projector writes there. Today `qmx_agents` imports `qmx_control` directly; the architecture says `qma2` must not (it talks to the host through its own store and journal, and `qmx-control` registers new operations from `ctl/agent_ops.py`).
- **MCP/tool side:** domain tools only over FastMCP stdio (`qmx-mcp-data|backtest|research|node`). The in-process `create_mcp(ControlService)` exposes the 52 `OPERATIONS` tuples `(name, http_method, path, destructive)`. `check_descriptor` is the shared refusal gate for hosted and MCP tools.
- **Approvals:** nothing durable exists outside the LangGraph checkpointer. A turn route and an approvals table are both new.
- **Model path:** the old router assumes CLIProxy or API keys through `init_chat_model`. The subscription-native path exists only in `native_claude.py`/`native_codex.py` and was never run live.
- **Package edges that bind qma2:** `qmx_apps` imports `qmx_agents.guards.journal` (`road/history.py:13`, `road/validation.py:12`, `road/__init__.py:11`) and `...money_path.check_descriptor` (`supervisor.py:29`). `qmx_remote` imports `qmx_agents.guards.journal` (`models.py:11`, `runs.py:16`) and `router/spec/workflows/guards` in `worker.py:26-32` (executors at `:137-209`).

## Non-Obvious Things

1. **`native_claude.py` is not standalone.** It imports `.native_sessions.SessionEvent`, and `native_sessions` imports `.service.RequestRuntime`, `.tool_loop.ToolBinding/ToolLoopProvider` (LangChain, langsmith), `.graph_storage.JournalRecords`, `qma.core`/`qma.wire`/`qma.daemon`. Importing it loads the old daemon and LangChain. qma2 must copy the logic and substitute its own `SessionEvent`, `ProviderError` and `ProviderRequest`. `native_boundary.py` only needs `.providers.ProviderError` and is cheap to copy.
2. **The "working recipe" has never run live.** The docs and runtime-check JSON state `authentication_performed: false`, `model_calls: 0`, `subscription_connection_verified: false`. It is verified only against fake clients and SDK flag construction. Real behavior of hooks, `can_use_tool`, `dontAsk` and resume is unproven (the architecture's probes P3/P5 cover this).
3. **`import qmx_control` loads LangChain.** `CTL/service.py` imports `qmx_apps.supervisor`, which imports `qmx_agents.guards.money_path`, which imports `langchain_core`. `qmx_remote` imports `qmx_agents.guards.journal`, and `guards/__init__.py` pulls in `admission` (deepagents). So `qma2` could not import `qmx_control` without LangChain regardless of the policy ("never import"), until the guards move and the four `qmx_apps`/`qmx_remote` imports change.
4. **"Neutral" in H3 means the logic is neutral, not the file.** Every candidate that matters (`money_path.py`, `memory.py`, `router.py`, `spec.py`) imports LangChain/Deep Agents at module top. Reuse is by copy. Fully clean files: `journal.py`, `parent_surfaces.py`, `experiments.py`.
5. **`RunJournal` lock hazard.** Its constructor opens `<journal>.lock` with mode `"x"` (`journal.py:48`). A crash leaves a stale `.lock` file and the next open raises `FileExistsError`. There is no stale-lock recovery. It also fsyncs every append.
6. **Hooks and `can_use_tool` interplay.** The recipe's own comment (`native_claude.py:235-236`) says allow-rules can shadow `can_use_tool`, so the `PreToolUse` hook is the real gate. The SDK also warns when `can_use_tool` is shadowed (`types.py:1836-1896`).
7. **`permission_mode="dontAsk"`** is what makes `deny` the default for anything not allow-listed. A harness with approvals needs a different mode, plus the `deferred_tool_use` (`ResultMessage.deferred_tool_use`) path the architecture describes.
8. **Resume semantics.** Every turn builds a new client with `resume=<id>`; the `init` message's `session_id` must equal it. Resume is refused otherwise. Resume is also keyed by a binding hash, and changing any input starts a fresh native session instead of reusing context (`test_resume_binding_changes_start_fresh_instead_of_reusing_context`).
9. **Env inheritance.** The recipe refuses the environment instead of scrubbing it. The `env=` option adds to `os.environ`; it does not replace it. The preflight `claude auth status` call also passes `{**os.environ, ...}`. A qma2 allow-list scrub needs a custom transport or a launcher shim.
10. **The old UI-facing event shape is not the planned one.** `stream_turn` emits completed messages (no streaming deltas). Planned `QmaEvent` is in ARCHITECTURE §2.1.
11. **Copilot approvals shape depends on the middleware.** HITL resume is `{"decisions":[{"type":"approve"|"reject"}]}`; global memory resume is a bare bool; the `permission` block carries `{interrupt_id, request}`. There is no `answered` write-back.
12. **Child sessions.** `stream_turn` creates a `sessions` row per LangGraph subgraph namespace (`parent_id` set). This is the only parent/child session use and the closest analogue to qma2 delegation.
13. **`router.accounts()`/`quotas()`** talk to CLIProxy's `/v8/management/...`. The "router across accounts" concept does not exist in code for subscription accounts, and no code checks which subscription account is logged in beyond `claude auth status` for a single dedicated home.
14. **`openai-agents` is not installed** in `qmx-agents/.venv` (only `openai 3.28.0`, `openai_codex 0.160.0`, `langchain_openai`). It imports as top-level `agents`.
15. **`models.yaml` hardcodes model names** (`cliproxy:claude-opus-5-5`, `cliproxy:gpt-6.1-sol`, `gpt-6-luna`, plus OpenRouter test profile), used by the old router only.

## Open Questions

- I did not run any tests or probes (read-only). The 31/60 failure count under `ANTHROPIC_BASE_URL` rests on H3 plus code reading.
- I did not check how `qmx-apps` injects environment or tokens into mini-app processes, or how the `/mcp` mount authenticates agent principals. Others cover those slices.
- I did not read `native_codex.py` lines 330-553 (event loop and approval handler), nor `tool_loop.py` beyond its header, since neither feeds the chosen design.
- Whether `claude-agent-sdk` 0.2.165 (Windows wheel with bundled CLI) is acceptable under the project's two-week rule is the operator's call (per H3); I did not verify the wheel contents myself.
- The `qml`/`qmn` tests that scan qma paths pass vacuously after deletion. I read the scan code but did not run it; this assumes `Path.rglob` on a missing directory returns an empty iterator on 3.14 (which matches current behavior).
- I found no evidence of any live (non-fake) copilot or native-Claude turn ever succeeding, but absence in the files I read is not proof. H3 says the copilot never ran against a real model.