# 02a. Claude Agent SDK: the whole surface, for a one-engine harness

Researched 2026-10-14. Primary sources only. Docs were read in the built-in browser. Source code, changelogs and package metadata were read as raw files from GitHub, PyPI and npm. No page needed the firecrawl fallback.

Versions at the time of reading:

- Python `claude-agent-sdk` 0.2.166, uploaded to PyPI 2026-10-14 03:43 UTC. It bundles Claude Code CLI 2.1.299. ([CHANGELOG](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/CHANGELOG.md), [PyPI JSON](https://pypi.org/pypi/claude-agent-sdk/json))
- TypeScript `@anthropic-ai/claude-agent-sdk` 0.3.299, published 2026-10-14 00:23 UTC. ([npm registry](https://registry.npmjs.org/@anthropic-ai/claude-agent-sdk))

Ground truth for Python is `src/claude_agent_sdk/types.py`, `client.py`, `_internal/*` on the `main` branch ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)).

Labels used below. **Fact** means a source states it. **Inferred** means I derived it from facts. **UNCONFIRMED** means I could not confirm it from a primary source.

## Summary table

| # | Area | What exists | Python status | Main source |
|---|---|---|---|---|
| 1 | query() vs ClaudeSDKClient | One-shot iterator vs a stateful client with control methods | Both. Interrupt, set_model, set_permission_mode only on the client | [python ref](https://code.claude.com/docs/en/agent-sdk/python) |
| 2 | Sessions | continue, resume, fork, custom ID, truncating resume, session store, list/read/rename/tag/delete/fork helpers | Full | [sessions](https://code.claude.com/docs/en/agent-sdk/sessions) |
| 3 | Hooks | 33 Claude Code events. Callback hooks plus settings hooks run side by side | Only 10 events as callbacks. The other 23 only as settings shell hooks | [SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks), [hooks ref](https://code.claude.com/docs/en/hooks) |
| 4 | Permissions | 6 modes, allow/deny/ask rules, can_use_tool, fixed evaluation order | Full. TS-only: `permissionPrompts` | [permissions](https://code.claude.com/docs/en/agent-sdk/permissions) |
| 5 | Subagents | `agents` option, per-agent model/tools/skills/MCP/maxTurns/effort/permissionMode/background, depth and concurrency env vars | Full. No per-agent provider or env | [subagents](https://code.claude.com/docs/en/agent-sdk/subagents) |
| 6 | Skills, plugins, commands, CLAUDE.md | Filesystem discovery via `setting_sources`, `skills` filter, local `plugins`, slash commands in prompts | Full. Default loads `~/.claude` | [claude-code-features](https://code.claude.com/docs/en/agent-sdk/claude-code-features) |
| 7 | MCP | stdio, SSE, HTTP, in-process SDK servers, tool search on by default | Full except runtime `setMcpServers` | [mcp](https://code.claude.com/docs/en/agent-sdk/mcp), [tool-search](https://code.claude.com/docs/en/agent-sdk/tool-search) |
| 8 | Context | Auto compaction, `/compact`, PreCompact hook, native 1M on newer models, automatic prompt caching | Full. PostCompact hook TS only. No context-editing option found | [agent-loop](https://code.claude.com/docs/en/agent-sdk/agent-loop), [model-config](https://code.claude.com/docs/en/model-config) |
| 9 | Cost, usage, rate limits | Result cost estimate, per-model usage, RateLimitEvent, `/usage` report, max_budget_usd, max_turns | RateLimitEvent typed. `usage_report` typed only in TS | [cost-tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking) |
| 10 | Structured output, checkpointing, sandbox, presets | output_format, rewind_files, SandboxSettings, claude_code system prompt and tools presets | Full. Sandbox fails open by default in Python | [python ref](https://code.claude.com/docs/en/agent-sdk/python) |
| 11 | Auth and providers | API key, bearer token, apiKeyHelper, setup-token OAuth, subscription login, Bedrock/Vertex/Foundry/Claude Platform on AWS, gateways | Full. Policy limits subscription use in products | [authentication](https://code.claude.com/docs/en/authentication), [legal](https://code.claude.com/docs/en/legal-and-compliance) |
| 12 | Computer use, browser | CLI computer use (macOS, interactive only), Chrome extension (needs /login) | Not usable from the SDK as documented | [computer-use](https://code.claude.com/docs/en/computer-use), [chrome](https://code.claude.com/docs/en/chrome) |
| 13 | Workflow tool, background tasks, agent teams | Dynamic workflows, background subagents and Bash, Monitor tool, task messages, agent teams (CLI only) | Workflow tool works from Python. Agent teams do not | [workflows](https://code.claude.com/docs/en/workflows), [cookbook 08](https://github.com/anthropics/claude-cookbooks/blob/main/claude_agent_sdk/08_Dynamic_workflows.ipynb) |
| 14 | Platform | Wheels for macOS arm64/x64, Linux glibc x64/arm64, Windows x64. Bundled CLI | Python >= 3.10. No Windows ARM64 wheel, no musl wheel | [PyPI JSON](https://pypi.org/pypi/claude-agent-sdk/json), [troubleshooting](https://code.claude.com/docs/en/agent-sdk/troubleshooting) |
| 15 | Easy to forget | verbatim_prompts, defer decision, message origin, session store, OTel, retry watchdog, system reminders, Monitor tool | Mostly present | various, below |

## 1. query() vs ClaudeSDKClient

- **Fact.** `query()` creates a new session by default. `ClaudeSDKClient` reuses one session across calls. The docs table marks interrupts as "Not supported" for `query()` and "Supported" for the client ([python ref](https://code.claude.com/docs/en/agent-sdk/python)).
- **Fact.** Both accept streaming input (a string or an async iterable of message dicts), hooks and custom tools. `query()` continues only by passing `continue_conversation` or `resume`; the client continues automatically (same table).
- **Fact.** Client methods: `connect`, `query(prompt, session_id="default")`, `receive_messages`, `receive_response`, `interrupt`, `set_permission_mode`, `set_model`, `rewind_files`, `get_mcp_status`, `get_context_usage`, `reconnect_mcp_server`, `toggle_mcp_server`, `stop_task`, `get_server_info`, `disconnect` ([client.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/client.py)).
- **Fact.** Python `query()` "returns a plain iterator without control methods", so mid-session setters live on the client ([configuration](https://code.claude.com/docs/en/agent-sdk/configuration)).
- **Fact.** Streaming input is the recommended mode. Single message mode lacks image attachments, queueing, "Real-time interruption" and natural multi-turn ([streaming-vs-single-mode](https://code.claude.com/docs/en/agent-sdk/streaming-vs-single-mode)).
- **Fact.** A single-shot `query()` yields the error result, then raises. A streaming session stays alive past `error_max_turns` and budget results ([configuration](https://code.claude.com/docs/en/agent-sdk/configuration)).
- **Fact.** In Python, if your prompt generator throws, "the session stalls without raising" ([streaming-vs-single-mode](https://code.claude.com/docs/en/agent-sdk/streaming-vs-single-mode)).
- **Fact.** The docs warn against `break` inside the client's message loop: "avoid using break to exit early" ([python ref](https://code.claude.com/docs/en/agent-sdk/python)).
- **Fact.** `can_use_tool` works with `query()` and string prompts since 0.2.140, not only the client ([CHANGELOG](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/CHANGELOG.md)). The docs examples still show a "Required workaround" dummy hook; the docs lag the code (see the H1 section).
- **Fact.** `UserMessage.origin` and `ResultMessage.origin` tell your own prompt's result apart from injected turns such as background task notifications ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)).

## 2. Sessions

- **Fact.** Options: `continue_conversation`, `resume`, `fork_session`, `session_id` (custom UUID), `resume_session_at` (load only up to a message UUID) and `resume_drops_turn` (validate the truncation) ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)).
- **Fact.** Location: "Claude Code stores sessions under ~/.claude/projects/<encoded-cwd>/*.jsonl". With `CLAUDE_CONFIG_DIR` set, look under `$CLAUDE_CONFIG_DIR/projects/` ([sessions](https://code.claude.com/docs/en/agent-sdk/sessions)).
- **Fact.** The encoded name replaces every non-alphanumeric character with `-`. Names over 200 characters are truncated plus a hash (same page).
- **Fact.** `CLAUDE_CODE_PROJECT_DIR_NAME`, set beside `CLAUDE_CONFIG_DIR`, names the project folder. It needs CLI 2.1.234+ and Python SDK 0.2.140+. It is read "only from the environment you start claude from" ([env-vars](https://code.claude.com/docs/en/env-vars)).
- **Fact.** Python has no `persistSession: false`. Use `CLAUDE_CODE_SKIP_PROMPT_HISTORY` in `env` to "suppress transcript writes" ([sessions](https://code.claude.com/docs/en/agent-sdk/sessions)).
- **Fact.** Resume searches beyond the current project directory since CLI 2.1.223, but the file must be on the same machine ([sessions](https://code.claude.com/docs/en/agent-sdk/sessions)).
- **Fact.** Fork copies conversation history, not files: "Forking branches the conversation history, not the filesystem" (same page).
- **Fact.** A `SessionStore` adapter mirrors transcripts to your own backend. Two required methods (`append`, `load`) and optional `list_sessions`, `list_session_summaries`, `delete`, `list_subkeys`. The mirror is best effort and keyed by working directory ([session-storage](https://code.claude.com/docs/en/agent-sdk/session-storage)). `InMemorySessionStore` ships in the package; S3 and Redis reference adapters live in `examples/session_stores/` ([CHANGELOG](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/CHANGELOG.md)).
- **Fact.** Helpers: `list_sessions`, `get_session_info`, `get_session_messages`, `list_subagents`, `get_subagent_messages`, `rename_session`, `tag_session`, `delete_session`, `fork_session`, plus `*_from_store` and `*_via_store` variants and `import_session_to_store` ([__init__.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/__init__.py)).
- **Fact.** The Python session helpers honour `CLAUDE_CONFIG_DIR`, including one passed through `options.env` ([_internal/sessions.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/_internal/sessions.py)).
- **Fact.** Session data is pruned at startup: Claude Code "removes files older than cleanupPeriodDays, 30 days by default" ([costs](https://code.claude.com/docs/en/costs)).
- **Fact.** The system prompt is recorded on the first request and reused until compaction. A changed `append` on resume is not seen "until the session is compacted" ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py), `SystemPromptPreset.snapshot`).

## 3. Hooks

**Claude Code event list (33).** SessionStart, Setup, UserPromptSubmit, UserPromptExpansion, PreToolUse, PermissionRequest, PermissionDenied, PostToolUse, PostToolUseFailure, PostToolBatch, Notification, MessageDisplay, SubagentStart, SubagentStop, TaskCreated, TaskCompleted, Stop, StopFailure, TeammateIdle, InstructionsLoaded, ConfigChange, CwdChanged, DirectoryAdded, FileChanged, WorktreeCreate, WorktreeRemove, PreCompact, PostCompact, PreModelSwitch, PostModelSwitch, Elicitation, ElicitationResult, SessionEnd ([hooks ref](https://code.claude.com/docs/en/hooks)).

**Python callback events (10).** PreToolUse, PostToolUse, PostToolUseFailure, UserPromptSubmit, Stop, SubagentStop, PreCompact, Notification, SubagentStart, PermissionRequest. This is the `HookEvent` Literal in [types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py) and matches the "Python SDK" column on the [SDK hooks page](https://code.claude.com/docs/en/agent-sdk/hooks).

- **Fact.** SessionStart and SessionEnd "aren't available in the Python SDK because its HookEvent type omits them". In Python they work only as shell hooks in settings files ([SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)).
- **Fact.** Python 0.2.166 already ships typed output classes for 21 events, including SessionStart, PostToolBatch, PreModelSwitch and Elicitation, and `_hooks_to_internal_format` forwards any dict key without checking it ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)). **UNCONFIRMED** whether the CLI honours a Python callback registered under one of the 23 TS-only names. The docs say it does not.
- **Fact.** What a callback can return. Top level: `continue_`, `stopReason`, `suppressOutput`, `systemMessage`, `decision: "block"`, `reason`. PreToolUse: `permissionDecision` (allow, deny, ask, defer), `permissionDecisionReason`, `updatedInput`, `additionalContext`. PostToolUse: `additionalContext`, `updatedToolOutput` (any tool). UserPromptSubmit: `additionalContext`. Async: `{"async_": True, "asyncTimeout": ms}` (types.py, [SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)).
- **Fact.** Precedence: "deny takes priority over defer, which takes priority over ask" ([SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)).
- **Fact.** `defer` ends the turn with `stop_reason` `"tool_deferred"` so the call can be resumed later; `ResultMessage.deferred_tool_use` carries it (same page, types.py).
- **Fact.** Multiple matchers on one event "are dispatched concurrently" ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py), `hooks` docstring).
- **Fact.** Callback hooks also fire inside subagents; the input carries `agent_id` and `agent_type` ([claude-code-features](https://code.claude.com/docs/en/agent-sdk/claude-code-features)).
- **Fact.** Settings hooks and callback hooks "run side by side". Settings hooks support types `command`, `http`, `mcp_tool`, `prompt`, `agent` (same page).
- **Fact.** Async outputs "can't block, modify, or inject context" ([SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)).
- **Fact.** Timeout behaviour differs by event. A timed-out UserPromptSubmit callback blocks the prompt. A timed-out PreModelSwitch blocks the switch. A timed-out Stop counts as no decision (same page).
- **Fact.** `include_hook_events=True` streams `HookEventMessage` objects ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)).
- **Fact.** In Python, the hook context `signal` is reserved and not wired (`signal: Any | None  # Future: abort signal support`, types.py).

## 4. Permissions

- **Fact.** Evaluation order: 1 hooks, 2 deny rules, 3 ask rules, 4 permission mode, 5 allow rules, 6 `can_use_tool` ([permissions](https://code.claude.com/docs/en/agent-sdk/permissions)).
- **Fact.** A hook allow does not skip later rules: "A hook that returns allow does not skip the deny and ask rules" (same page).
- **Fact.** Deny rules beat every mode: blocked "even in bypassPermissions mode". A bare-name deny such as `Bash` removes the tool from the request (same page).
- **Fact.** Modes in Python: `default`, `acceptEdits`, `plan`, `bypassPermissions`, `dontAsk`, `auto` ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)).
- **Fact.** If you omit the mode, the start mode comes from settings `permissions.defaultMode`, otherwise the built-in default, "which can be auto mode". Auto mode drops broad allow rules, so "pass default explicitly" ([permissions](https://code.claude.com/docs/en/agent-sdk/permissions)).
- **Fact.** `dontAsk` turns every would-be prompt into a deny and never calls `can_use_tool` (same page).
- **Fact.** `can_use_tool` runs only when nothing earlier resolved the call. "Auto-approved tools never reach canUseTool" (same page). The SDK emits `CanUseToolShadowedWarning` when `allowed_tools` or bypass shadow it (types.py).
- **Fact.** `allowed_tools` does not limit `bypassPermissions`: "allowed_tools does not constrain bypassPermissions" ([permissions](https://code.claude.com/docs/en/agent-sdk/permissions)).
- **Fact.** Rule syntax traps: allow globs work only after a literal `mcp__<server>__` prefix; `allowed_tools=["*"]` is ignored. `Edit(//path)` is absolute; `Edit(/path)` is relative to the cwd (same page).
- **Fact.** `AskUserQuestion` and MCP tools marked `_meta["anthropic/requiresUserInteraction"]` always reach the callback, and are denied in `dontAsk` (same page).
- **Fact.** Subagents run in the parent's mode. `AgentDefinition.permissionMode` applies only when the parent is in default, dontAsk or plan, and bypass is never taken from an agent definition (same page).
- **Fact.** The callback "can stay pending indefinitely". For long human waits, return `defer` from a PreToolUse hook instead ([user-input](https://code.claude.com/docs/en/agent-sdk/user-input)).
- **Fact.** Callback returns `PermissionResultAllow(updated_input=...)` or `PermissionResultDeny(message=...)`. Suggestions in the context are `PermissionUpdate` entries you can echo back to "approve and remember" (same page). The context carries `tool_use_id`, `agent_id`, `decision_reason`, `blocked_path`, `title`, `display_name`, `description` (types.py).
- **Fact.** bypass refuses to start as root or under sudo on Linux and macOS outside a recognised sandbox ([permissions](https://code.claude.com/docs/en/agent-sdk/permissions)).
- **Fact.** Bash commands are parsed into an AST for rule matching; `eval` and similar always need approval ([secure-deployment](https://code.claude.com/docs/en/agent-sdk/secure-deployment)).

## 5. Subagents

- **Fact.** Define them with `agents={name: AgentDefinition(...)}`. Fields: `description`, `prompt`, `tools`, `disallowedTools`, `model`, `skills`, `memory`, `mcpServers`, `initialPrompt`, `maxTurns`, `background`, `effort`, `permissionMode` ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)).
- **Fact.** `model` takes "an alias such as "sonnet", "opus", "haiku", or "inherit", or a full model ID" ([python ref](https://code.claude.com/docs/en/agent-sdk/python)).
- **Fact.** Omitting `tools` gives the agent every tool available to subagents. A left-out tool "isn't in the subagent's session at all" ([subagents](https://code.claude.com/docs/en/agent-sdk/subagents)).
- **Fact.** Limits (CLI 2.1.219+, Python SDK 0.2.127+): `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` default 3 layers, 1 turns nesting off. `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` default 20. `max_budget_usd` counts subagent spend and stops background subagents (same page). The env vars "can be adjusted but not removed" ([env-vars](https://code.claude.com/docs/en/env-vars)).
- **Fact.** Default subagent model: `CLAUDE_CODE_SUBAGENT_MODEL`. A model passed at spawn and the definition's `model` both take precedence. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` forces one model (CLI 2.1.257+) ([env-vars](https://code.claude.com/docs/en/env-vars)).
- **Fact.** `AgentDefinition` has no `env`, base URL or credential field (types.py). **Inferred:** every subagent uses the session's provider and credential. A different provider needs a separate `query()` or client with its own `env`.
- **Fact.** A non-fork subagent gets its own prompt, the Agent tool prompt, project CLAUDE.md and its tools. It does not get the parent history or system prompt ([subagents](https://code.claude.com/docs/en/agent-sdk/subagents)).
- **Fact.** The built-in `general-purpose` agent always exists; `CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS=1` removes it and Explore and Plan (same page, [env-vars](https://code.claude.com/docs/en/env-vars)).
- **Fact.** Resume a subagent by resuming the same session and naming its `agentId` from the Agent tool result. Explore and Plan are one-shot ([subagents](https://code.claude.com/docs/en/agent-sdk/subagents)).
- **Fact.** Since CLI 2.1.210, the subagent's final report is scanned for injection-shaped text (fake `<system-reminder>`, turn markers) before the parent reads it (same page).
- **Fact.** Claude Opus 5 delegates "more readily than earlier models"; the `claude_code` preset adds a line against unrequested Agent calls; a custom prompt does not (same page).
- **Fact.** `forward_subagent_text=True` streams subagent text and thinking; by default only tool blocks are forwarded ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)).
- **Fact.** `AskUserQuestion` "is not currently available in subagents" ([user-input](https://code.claude.com/docs/en/agent-sdk/user-input)).
- **Fact.** The Agent tool shows as `Agent` in tool_use blocks but as `Task` in the init tools list ([subagents](https://code.claude.com/docs/en/agent-sdk/subagents)).

## 6. Skills, plugins, slash commands, CLAUDE.md, and isolation

- **Fact.** Default is to load everything: "Omitting settingSources is equivalent to ["user", "project", "local"]" ([claude-code-features](https://code.claude.com/docs/en/agent-sdk/claude-code-features)). The Python docstring agrees: `None` means all sources ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)).
- **Fact.** The v0.1.0 "load nothing" default "was briefly changed ... and then reverted" ([migration-guide](https://code.claude.com/docs/en/agent-sdk/migration-guide)). Python 0.1.59 and earlier treated `[]` like omitted (same page).
- **Fact.** What each source loads. `user`: `~/.claude/settings.json`, `~/.claude/CLAUDE.md`, rules, skills, commands, agents. `project`: `<cwd>/.claude/settings.json` and hooks, CLAUDE.md in cwd "and every parent directory", skills up to the repo root. `local`: `CLAUDE.local.md`, `settings.local.json` ([claude-code-features](https://code.claude.com/docs/en/agent-sdk/claude-code-features)).
- **Fact.** Read regardless of `setting_sources`: managed policy, `~/.claude.json` ("Relocate with CLAUDE_CONFIG_DIR in env"), auto memory under `~/.claude/projects/<project>/memory/`, claude.ai MCP connectors when signed in with claude.ai, and sandbox credential deny entries in `~/.claude/settings.json` (same page).
- **Fact.** "Do not rely on default query() options for multi-tenant isolation" (same page).
- **Fact.** `CLAUDE_CONFIG_DIR`: "All settings, session history, and plugins are stored under this path." It is ignored in project and local settings ([env-vars](https://code.claude.com/docs/en/env-vars)). Credentials move with it, and on macOS the Keychain entry is keyed to that directory ([authentication](https://code.claude.com/docs/en/authentication)).
- **Inferred.** With `CLAUDE_CONFIG_DIR` pointing at a QMX-owned folder, the `user` source becomes a QMX user tier. **UNCONFIRMED** that user skills, agents and commands are read from `$CLAUDE_CONFIG_DIR/skills` and siblings; the docs only state settings, history, plugins and credentials.
- **Fact.** Skills are files only: "The SDK doesn't provide a programmatic API for registering them" ([skills](https://code.claude.com/docs/en/agent-sdk/skills)).
- **Fact.** `skills` is a filter, "not a sandbox". Unlisted skill files stay readable via Read and Bash ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)). "Restricting the list doesn't restrict dispatch by name" ([skills](https://code.claude.com/docs/en/agent-sdk/skills)).
- **Fact.** Plugins: `plugins=[{"type": "local", "path": ...}]`, local only. A plugin brings skills, agents, hooks, MCP servers and commands; skills are namespaced `plugin:skill` ([plugins](https://code.claude.com/docs/en/agent-sdk/plugins)).
- **Fact.** Commands are sent as `/<name>` in the prompt. The init message lists them in `slash_commands`. Built-ins such as `/compact`, `/clear`, `/context`, `/usage` work headless ([skills](https://code.claude.com/docs/en/agent-sdk/skills)).
- **Fact.** `verbatim_prompts=True` disables `@path` expansion and slash dispatch for text you did not type yourself. It needs CLI 2.1.248+ ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)).
- **Fact.** Kill switches: `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `CLAUDE_CODE_DISABLE_ATTACHMENTS=1`, `strict_mcp_config=True`, `ENABLE_CLAUDEAI_MCP_SERVERS=false` ([modifying-system-prompts](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts), [claude-code-features](https://code.claude.com/docs/en/agent-sdk/claude-code-features)).

**Inferred isolation recipe for QMX, both directions.** Set `env={"CLAUDE_CONFIG_DIR": <QMX folder>, "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1" or keep memory inside that folder}`, `setting_sources=[]` (or `["user"]` once the QMX user tier is confirmed), `strict_mcp_config=True`, `plugins=[QMX local plugin]`, an explicit `skills` list, and an explicit `cwd` that is not inside the operator's dev repo. Writes then land under the QMX folder, not `~/.claude`. Managed policy settings still apply because they are machine-wide.

## 7. MCP

- **Fact.** Four config types: stdio, SSE, HTTP, and `sdk` (in-process) ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)). In-process servers come from `create_sdk_mcp_server()` and the `@tool` decorator ([python ref](https://code.claude.com/docs/en/agent-sdk/python)).
- **Fact.** In-process servers do not forward server-to-client requests: sampling and elicitation "are not forwarded yet" (types.py, `McpSdkServerConfig`).
- **Fact.** Naming: "mcp__<server-name>__<tool-name>" ([mcp](https://code.claude.com/docs/en/agent-sdk/mcp)).
- **Fact.** `.mcp.json` in the project loads with the project source. `strict_mcp_config=True` ignores every MCP config not passed in code ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)).
- **Fact.** Tool search is on by default and defers MCP schemas, loading up to five per search ([tool-search](https://code.claude.com/docs/en/agent-sdk/tool-search)).
- **Fact.** Tool search turns off when `ANTHROPIC_BASE_URL` is not first party; `ENABLE_TOOL_SEARCH=true` forces it back on. Other values: `auto`, `auto:N`, `false` (same page).
- **Fact.** First turn waits for stdio and in-process servers up to `MCP_TIMEOUT` (30 s). `CLAUDE_CODE_MCP_STARTUP_WAIT_MS` overrides it. `alwaysLoad: true` exempts a server from deferral ([mcp](https://code.claude.com/docs/en/agent-sdk/mcp)). `alwaysLoad` is not declared on the Python TypedDicts (types.py).
- **Fact.** `ToolAnnotations.maxResultSizeChars` keeps large results inline up to 500,000 characters (Python 0.2.140+) ([python ref](https://code.claude.com/docs/en/agent-sdk/python)).
- **Fact.** `toggle_mcp_server` and `reconnect_mcp_server` work mid-session on the client. `permission_prompt_tool_name` routes permission prompts to an MCP tool (client.py, types.py).

## 8. Context, compaction, caching

- **Fact.** Auto compaction emits a `system` message with subtype `compact_boundary` (a plain `SystemMessage` in Python). Manual: send `/compact`. PreCompact hook gets `trigger` manual or auto ([agent-loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)).
- **Fact.** CLAUDE.md is "re-injected on every request", so durable rules belong there, not in the first prompt (same page).
- **Fact.** Knobs: `CLAUDE_CODE_AUTO_COMPACT_WINDOW` (100,000 to 1,000,000), `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`, `DISABLE_AUTO_COMPACT`, `DISABLE_COMPACT` ([env-vars](https://code.claude.com/docs/en/env-vars)).
- **Fact.** Fable, Sonnet 5+, Haiku 5.5 and Opus 4.7+ "run with the 1M window by default". They compact at about 967K ([model-config](https://code.claude.com/docs/en/model-config)).
- **Fact.** The Python `betas` option only knows `context-1m-2025-08-07`, documented for "Sonnet 4/4.5 only" ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)). It is legacy for current models.
- **Fact.** Behind a gateway, Claude Code assumes the API's window. Set `CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000` if the gateway caps lower ([model-config](https://code.claude.com/docs/en/model-config)).
- **Fact.** Prompt caching is automatic for stable prefixes ([agent-loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)). Subscription users within included usage get the 1-hour TTL automatically on the main conversation ([env-vars](https://code.claude.com/docs/en/env-vars)).
- **Fact.** "Each model has its own prompt cache", so a mid-session model switch recomputes the whole conversation uncached ([configuration](https://code.claude.com/docs/en/agent-sdk/configuration)).
- **Fact.** `SystemPromptPreset.exclude_dynamic_sections` moves cwd, memory and git status out of the system prompt for cross-user cache hits ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)).
- **Fact.** `get_context_usage()` returns the `/context` breakdown and makes extra token-counting requests ([python ref](https://code.claude.com/docs/en/agent-sdk/python)).
- **Fact.** `task_budget={"total": N}` tells the model its remaining token budget (beta `task-budgets-2026-03-13`) (types.py).
- **UNCONFIRMED.** I found no SDK option for the API's context-editing feature (server-side clearing of old tool results). Compaction is the documented mechanism.

## 9. Cost, usage and rate limits

- **Fact.** `ResultMessage` carries `subtype`, `duration_ms`, `duration_api_ms`, `is_error`, `num_turns`, `session_id`, `stop_reason`, `total_cost_usd`, `usage`, `result`, `structured_output`, `model_usage`, `permission_denials`, `deferred_tool_use`, `errors`, `api_error_status`, `terminal_reason`, `origin` ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)).
- **Fact.** Costs are "client-side estimates, not authoritative billing data" ([cost-tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking)).
- **Fact.** `usage` covers the main loop only; `model_usage` covers the whole tree ([agent-loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)). A resumed call reports the whole session's spend ([cost-tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking)).
- **Fact.** `RateLimitEvent` exists in Python with `status` (allowed, allowed_warning, rejected), `resets_at`, `rate_limit_type` (five_hour, seven_day, seven_day_opus, seven_day_sonnet, overage), `utilization`, overage fields and `raw`. The CLI "emits this whenever the rate limit status transitions" (types.py docstring).
- **Fact.** TS documents `errorCode: "credits_required"` when a subscription's included usage is exhausted (CLI 2.1.181+) ([TS ref](https://code.claude.com/docs/en/agent-sdk/typescript)). In Python it would sit in `RateLimitInfo.raw` (types.py, Inferred).
- **Fact.** Sending `/usage` as a prompt returns the plan usage report. TS types it as `usage_report` on the assistant message, with `rate_limits.limits` rows. It is `null` if the OAuth token lacks the `user:profile` scope ([TS ref](https://code.claude.com/docs/en/agent-sdk/typescript)). **UNCONFIRMED** how Python exposes `usage_report`; the Python parser has no field for it ([message_parser.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/_internal/message_parser.py)).
- **Inferred.** A `setup-token` OAuth token is limited to model requests ([authentication](https://code.claude.com/docs/en/authentication)), so it may lack `user:profile`, leaving `/usage` rate rows null. UNCONFIRMED.
- **Fact.** `api_error_status` gives the HTTP status (429, 500, 529) on error results (types.py). TS errors distinguish `rate_limit` (429) from `overloaded` (529) ([TS ref](https://code.claude.com/docs/en/agent-sdk/typescript)).
- **Fact.** `max_budget_usd` counts subagents, can overshoot by one response plus running subagents, and `0` is rejected at startup ([agent-loop](https://code.claude.com/docs/en/agent-sdk/agent-loop), [configuration](https://code.claude.com/docs/en/agent-sdk/configuration)). `max_turns` counts tool-use round trips; `0` means no limit (same pages).
- **Fact.** The fallback model does not help with rate limits: rate-limit errors "never trigger a switch" ([model-config](https://code.claude.com/docs/en/model-config)).
- **Fact.** "Large parallel-subagent fanouts can hit rate limits" ([hosting](https://code.claude.com/docs/en/agent-sdk/hosting)).
- **Fact.** Retry knobs: `API_TIMEOUT_MS` (default 600000), `CLAUDE_CODE_MAX_RETRIES` (default 10, cap 15), `CLAUDE_CODE_RETRY_WATCHDOG=1` retries capacity errors indefinitely ([python ref](https://code.claude.com/docs/en/agent-sdk/python)).

## 10. Structured outputs, checkpointing, sandbox, presets

- **Fact.** `output_format={"type": "json_schema", "schema": ...}`. Validated data arrives in `ResultMessage.structured_output`. Failure ends with `error_max_structured_output_retries` ([structured-outputs](https://code.claude.com/docs/en/agent-sdk/structured-outputs)).
- **Fact.** Checkpointing: `enable_file_checkpointing=True`, then `client.rewind_files(user_message_id)`. It tracks only Write, Edit and NotebookEdit. Bash edits and subagent edits are not tracked. Rewind restores files, not the conversation ([file-checkpointing](https://code.claude.com/docs/en/agent-sdk/file-checkpointing)).
- **Fact.** User message UUIDs need `extra_args={"replay-user-messages": None}` (same page).
- **Fact.** Sandbox fields: `enabled`, `autoAllowBashIfSandboxed`, `excludedCommands`, `allowUnsandboxedCommands`, `network`, `ignoreViolations`, `enableWeakerNestedSandbox` ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)).
- **Fact.** In Python a sandbox that cannot start lets commands "run unsandboxed with a warning". Set `"failIfUnavailable": True` to stop instead; TS defaults to true ([python ref](https://code.claude.com/docs/en/agent-sdk/python)).
- **Fact.** "On native Windows, Claude Code runs commands unsandboxed." The sandbox runs on macOS, Linux and WSL2 ([sandboxing](https://code.claude.com/docs/en/sandboxing)).
- **Fact.** `dangerouslyDisableSandbox` requests fall back to the permission flow and reach `can_use_tool` ([python ref](https://code.claude.com/docs/en/agent-sdk/python)).
- **Fact.** System prompt choices. No `system_prompt` gives a minimal prompt that omits the preset's "security and safety instructions". `{"type": "preset", "preset": "claude_code", "append": ...}` gives the CLI prompt plus your text. A string replaces everything ([modifying-system-prompts](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts)). `SystemPromptFile` reads a file (types.py).
- **Fact.** A custom prompt should explain system reminders, because CLAUDE.md, hook output and skill lists arrive as reminders ([modifying-system-prompts](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts)).
- **Fact.** Tools: `tools=["Read", ...]` sets which built-ins exist, `[]` removes all, `{"type": "preset", "preset": "claude_code"}` gives all ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)). `allowed_tools` only pre-approves.

## 11. Auth and providers

- **Fact.** Docs quote on subscriptions, as written: "Unless previously approved, Anthropic does not allow third party developers to offer claude.ai login or rate limits for their products, including agents built on the Claude Agent SDK." ([overview](https://code.claude.com/docs/en/agent-sdk/overview), repeated on [quickstart](https://code.claude.com/docs/en/agent-sdk/quickstart)). This quote is longer than 15 words because the brief asked for it exactly.
- **Fact.** Legal page: OAuth is "designed to support ordinary use of Claude Code" and native apps. Developers using the Agent SDK "should use API key authentication". Advertised Pro and Max limits "assume ordinary, individual usage of Claude Code and the Agent SDK" ([legal-and-compliance](https://code.claude.com/docs/en/legal-and-compliance)).
- **Inferred.** The operator running QMX for himself on his own Max login sits closest to "ordinary, individual usage". Shipping QMX to anyone else on his credential is not allowed. This is a policy reading, not a ruling.
- **Fact.** Credential precedence: cloud provider flags, then `ANTHROPIC_AUTH_TOKEN`, then `ANTHROPIC_API_KEY`, then `apiKeyHelper`, then `CLAUDE_CODE_OAUTH_TOKEN`, then Anthropic profiles, then `/login` subscription OAuth ([authentication](https://code.claude.com/docs/en/authentication)).
- **Fact.** "In non-interactive mode (-p), the key is always used when present" (same page). The SDK runs non-interactive.
- **Fact.** `claude setup-token` makes a one-year OAuth token for `CLAUDE_CODE_OAUTH_TOKEN`. It "can only make model requests": no Remote Control, no claude.ai connectors. Local MCP servers still work. Bare mode ignores it (same page).
- **Fact.** Python `env` merges over the inherited environment; TS replaces it ([configuration](https://code.claude.com/docs/en/agent-sdk/configuration)). So `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_MODEL` can be set per `query()`.
- **Fact.** Base URL alone does not switch billing: "Setting only that variable, without a gateway credential, doesn't replace the subscription" ([llm-gateway](https://code.claude.com/docs/en/llm-gateway)).
- **Fact.** Anthropic "doesn't support routing Claude Code to non-Claude models through any gateway" (same page).
- **Fact.** Per-query model: `model`, plus alias env vars `ANTHROPIC_DEFAULT_OPUS_MODEL`, `_SONNET_`, `_HAIKU_`, `_FABLE_`. `ANTHROPIC_SMALL_FAST_MODEL` is deprecated; the haiku variable drives background work ([env-vars](https://code.claude.com/docs/en/env-vars)).
- **Fact.** `fallback_model` accepts a comma list, capped at three. It switches only on overload, unavailability or non-retryable server errors, for one turn, and also covers subagents ([configuration](https://code.claude.com/docs/en/agent-sdk/configuration), [model-config](https://code.claude.com/docs/en/model-config)).
- **Fact.** Provider switches: `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`, `CLAUDE_CODE_USE_FOUNDRY`, and `CLAUDE_CODE_USE_ANTHROPIC_AWS` with `ANTHROPIC_AWS_WORKSPACE_ID` ([quickstart](https://code.claude.com/docs/en/agent-sdk/quickstart)).
- **Fact.** Aliases differ by provider. On the Anthropic API, opus, sonnet and haiku resolve to the 5.5 models; on Foundry, opus is Opus 4.6 ([model-config](https://code.claude.com/docs/en/model-config)).
- **Fact.** `CLAUDE_AGENT_SDK_CLIENT_APP` adds your app name to the User-Agent ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)).

## 12. Computer use and browser

- **Fact.** CLI computer use "is a research preview on macOS that requires a Pro or Max plan". It is "not available in non-interactive mode with the -p flag" ([computer-use](https://code.claude.com/docs/en/computer-use)). **Inferred:** not available through the SDK.
- **Fact.** The Desktop app has computer use on macOS and Windows (same page). That is not the SDK.
- **Fact.** Chrome integration needs a direct plan and `/login`. With "an API key or a long-lived token from claude setup-token", Chrome stays off ([chrome](https://code.claude.com/docs/en/chrome)). It is not supported in WSL or through Bedrock, Vertex or Foundry (same page).
- **UNCONFIRMED.** Whether an SDK session signed in through `/login` under its own `CLAUDE_CONFIG_DIR` can enable Chrome via `extra_args={"chrome": None}`. Not documented for the SDK.
- **Inferred.** For a platform-neutral harness, browser control has to come through an MCP server you choose, not a built-in tool.

## 13. Workflow tool, background tasks, agent teams

- **Fact.** Dynamic workflows "are available on all paid plans, with Anthropic API access", and on Bedrock, Vertex and Foundry ([workflows](https://code.claude.com/docs/en/workflows)).
- **Fact.** Python can trigger them: allow `Workflow` in `allowed_tools` and ask for a workflow in the prompt. Needs CLI 2.1.154+, "which claude-agent-sdk 0.2.90 and up bundle" ([cookbook 08](https://github.com/anthropics/claude-cookbooks/blob/main/claude_agent_sdk/08_Dynamic_workflows.ipynb)). The SDK subagents page only names the TS floor, v0.3.149 ([subagents](https://code.claude.com/docs/en/agent-sdk/subagents)).
- **Fact.** Limits: no mid-run user input, no filesystem or shell from the script, no `import()`, 16 concurrent agents by default (`CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` 1 to 256), 4,096 items per `parallel()`, 1,000 agents per run ([workflows](https://code.claude.com/docs/en/workflows)).
- **Fact.** A run does not pause for a usage-limit reset "in non-interactive mode with claude -p or the Agent SDK". The agent fails instead (same page).
- **Fact.** Scripts and saved results live under the session directory in `~/.claude/projects/`. Runs are resumable within the same session (same page).
- **Fact.** Background work surfaces as `TaskStartedMessage`, `TaskProgressMessage`, `TaskNotificationMessage`, `TaskUpdatedMessage`; `stop_task(task_id)` stops one ([__init__.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/__init__.py), [python ref](https://code.claude.com/docs/en/agent-sdk/python)). `BackgroundTaskSummary.type` includes `"workflow"` (types.py).
- **Fact.** Python keeps stdin open until the CLI reports idle, bounded by `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` (default 10 minutes) ([CHANGELOG 0.2.160](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/CHANGELOG.md)).
- **Fact.** The Monitor tool runs a command or WebSocket in the background and feeds each line or frame to Claude ([python ref](https://code.claude.com/docs/en/agent-sdk/python)).
- **Fact.** `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` turns off all background work ([env-vars](https://code.claude.com/docs/en/env-vars)).
- **Fact.** Agent teams are experimental, and in "-p flag, including Agent SDK sessions, Claude doesn't spawn teammates" ([agent-teams](https://code.claude.com/docs/en/agent-teams)).
- **Fact.** TS 0.3.299 mentions `CronCreate` and `CronList` tools ([TS CHANGELOG](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-typescript/main/CHANGELOG.md)). Python Stop hook input has `session_crons` (types.py). **UNCONFIRMED** how in-session crons behave in an SDK session.

## 14. Platform

- **Fact.** 0.2.166 wheels: macOS 11 arm64 and x86_64, manylinux 2.17 x86_64 and aarch64, win_amd64, each about 100 to 110 MiB, plus an sdist ([PyPI JSON](https://pypi.org/pypi/claude-agent-sdk/json)).
- **Fact.** No Windows ARM64 wheel and no musllinux wheel are published (same source). On ARM64 Windows, "no binary is bundled"; install Claude Code natively ([quickstart](https://code.claude.com/docs/en/agent-sdk/quickstart)). **UNCONFIRMED** whether Alpine or musl works via the sdist plus a native CLI.
- **Fact.** Releases 0.2.157 and 0.2.160 to 0.2.163 shipped without a Windows wheel, after the CI change to "skip wheels over PyPI's per-file limit" (PyPI JSON, [CHANGELOG](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/CHANGELOG.md)).
- **Fact.** CLI lookup order: bundled `_bundled/claude`, then `claude` or `claude.exe` on PATH, then `~/.npm-global/bin/claude`, `~/.claude/local/claude` and others ([subprocess_cli.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/_internal/transport/subprocess_cli.py)). `cli_path` overrides it.
- **Fact.** On Windows the SDK refuses `.bat` and `.cmd` CLIs, including npm's `claude.cmd`. "The Windows x64 wheel of claude-agent-sdk bundles a claude.exe" ([troubleshooting](https://code.claude.com/docs/en/agent-sdk/troubleshooting)).
- **Fact.** On Windows, `resume` and `session_id` values with cmd.exe metacharacters raise `ValueError` ([CHANGELOG](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/CHANGELOG.md)).
- **Fact.** Python `>=3.10`. Dependencies: `anyio>=4`, `sniffio`, `mcp>=1.23,<3`, `jsonschema>=4.20` ([pyproject.toml](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/pyproject.toml)). asyncio and trio both work (CHANGELOG).
- **Fact.** Minimum CLI the SDK accepts: `MINIMUM_CLAUDE_CODE_VERSION = "2.0.0"` (subprocess_cli.py). Features have their own floors, for example `verbatim_prompts` needs 2.1.248.
- **Fact.** Credentials file: `%USERPROFILE%\.claude\.credentials.json` on Windows, `~/.claude/.credentials.json` on Linux, Keychain on macOS; all move under `CLAUDE_CONFIG_DIR` ([authentication](https://code.claude.com/docs/en/authentication)).
- **Fact.** Hosting guide: "One agent session maps to one subprocess". Start at 1 GiB RAM, 5 GiB disk, 1 CPU per agent ([hosting](https://code.claude.com/docs/en/agent-sdk/hosting)).

## 15. Things a harness should use that plans forget

- `verbatim_prompts=True` for any prompt built from untrusted text (market news, tool output). It stops `@path` reads and slash dispatch (types.py).
- PreToolUse `defer` plus `deferred_tool_use` for approvals that take hours: the process can exit and resume ([SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks)).
- `ResultError` and `terminal_reason` for typed failure paths ([CHANGELOG](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/CHANGELOG.md), types.py).
- `ConversationResetMessage` after `/clear`, which also zeroes running totals (types.py).
- `include_partial_messages=True` for token streaming to a UI (`StreamEvent`) (types.py).
- `effort` (`low` to `max`, `xhigh`) and `thinking` per session and per agent (types.py).
- OpenTelemetry: the CLI exports traces, metrics and log events from env vars; the SDK passes them through and propagates `TRACEPARENT` ([observability](https://code.claude.com/docs/en/agent-sdk/observability)).
- `stderr` callback for CLI logs; `max_buffer_size`; `load_timeout_ms` for slow session stores (types.py).
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` to stop telemetry, auto-updates and feature-flag fetches ([env-vars](https://code.claude.com/docs/en/env-vars)).
- `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1` and empty `attribution` to stop built-in commit rules from fighting yours ([modifying-system-prompts](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts)).
- `CLAUDE_CODE_SIMPLE=1` (same as `--bare`): minimal prompt, only Bash, read and edit tools, no OAuth read ([env-vars](https://code.claude.com/docs/en/env-vars)).
- Task-tracking tools are off by default on newer models. Opt in with `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` or by naming them, if the UI wants a live todo list ([todo-tracking](https://code.claude.com/docs/en/agent-sdk/todo-tracking)).
- `get_server_info()` and the init `SystemMessage.data` (typed `SystemInitData` in 0.2.166) list tools, skills, plugins, commands, MCP status and fast-mode state ([CHANGELOG](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/CHANGELOG.md)).
- No top-level session timeout and no per-subagent wall clock. Bound with `max_turns`, `AgentDefinition.maxTurns` and `CLAUDE_ASYNC_AGENT_STALL_TIMEOUT_MS` ([hosting](https://code.claude.com/docs/en/agent-sdk/hosting)).

## Python lacks vs TypeScript

From the [TS reference](https://code.claude.com/docs/en/agent-sdk/typescript) Options table and `Query` interface, compared with Python [types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py) and [client.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/client.py).

- **Hooks.** 23 events: PostToolBatch, UserPromptExpansion, MessageDisplay, StopFailure, PostCompact, PreModelSwitch, PostModelSwitch, PermissionDenied, SessionStart, SessionEnd, Setup, TeammateIdle, TaskCreated, TaskCompleted, Elicitation, ElicitationResult, ConfigChange, InstructionsLoaded, WorktreeCreate, WorktreeRemove, CwdChanged, FileChanged, DirectoryAdded. Also the hook AbortSignal and PostToolUse `classifierContext`.
- **Options.** `abortController`, `agent` (run a defined agent as the main thread), `agentProgressSummaries`, `allowDangerouslySkipPermissions`, `debug`/`debugFile`, `executable`/`executableArgs`, `managedSettings` (host-supplied policy tier), `onElicitation`, `permissionPrompts` (`'none'`), `persistSession`, `planModeInstructions`, `projectConfigRoot` (read project config from a trusted checkout when cwd is a worktree), `promptSuggestions`, `spawnClaudeCodeProcess` (run the CLI in a VM, container or remote host), `title`, `toolAliases` (map a built-in such as Bash to your MCP tool), `toolConfig`, `perTaskStopAffordance` (from the TS CHANGELOG).
- **Query methods.** `setMaxThinkingTokens`, `applyFlagSettings`, `updateSettings`, `initializationResult`, `reinitialize`, `supportedCommands`, `supportedModels`, `supportedAgents`, `readFile`, `reloadPlugins`, `reloadSkills`, `reloadOutputStyles`, `accountInfo`, `setMcpServers`, `readMcpResource`, `streamInput`, `rewindFiles(dryRun)`, interrupt receipts.
- **Process control.** `startup()`, `prewarm()` and `SpareProcess.claim()` to pre-warm processes ([TS CHANGELOG](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-typescript/main/CHANGELOG.md)).
- **Messages.** TS types about 36 message kinds, including `SDKStatusMessage`, `SDKToolProgressMessage`, `SDKAuthStatusMessage`, `SDKAPIRetryMessage`, `SDKPermissionDeniedMessage`, `SDKFilesPersistedEvent`, `SDKMemoryRecallMessage`, `SDKInformationalMessage`, and `usage_report` on assistant messages. Python turns unknown `system` subtypes into a raw `SystemMessage(subtype, data)` but **silently skips unknown top-level message types** ([message_parser.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/_internal/message_parser.py)).
- **Sandbox default.** TS `failIfUnavailable` defaults to true; Python fails open ([python ref](https://code.claude.com/docs/en/agent-sdk/python)).
- **Session object.** Python has `ClaudeSDKClient`; TS has no client object, and its V2 session API was removed in 0.3.142 ([sessions](https://code.claude.com/docs/en/agent-sdk/sessions)). Not a Python gap.

## Cookbook notebooks

From [claude-cookbooks/claude_agent_sdk](https://github.com/anthropics/claude-cookbooks/tree/main/claude_agent_sdk) and its README. All are Python.

| Notebook | Pattern it teaches |
|---|---|
| 00 The one-liner research agent | `query()` loop, WebSearch, multimodal Read, `ClaudeSDKClient` for context, system prompts |
| 01 The chief of staff agent | CLAUDE.md memory, output styles, plan mode, custom slash commands, audit hooks, subagent orchestration, Bash running Python scripts |
| 02 The observability agent | Git and GitHub MCP servers (100+ tools), CI failure analysis |
| 03 The site reliability agent | Custom MCP tool server, Prometheus queries, read-write remediation guarded by PreToolUse safety hooks |
| 04 Migrating from OpenAI Agents SDK | Primitive mapping (tools, guardrails, runner), sessions and resume, OpenTelemetry |
| 05 Building a session browser | `list_sessions`, read transcripts without spawning, rename, tag, fork |
| 06 The vulnerability detection agent | Interview-style client session, chained `query()` stages emitting schema JSON |
| 07 Hosting the agent | Same image on Docker, Modal and Kubernetes |
| 08 Dynamic workflows | Trigger the Workflow tool from Python, fan-out plus adversarial verification, reading `agent()`/`parallel()`/`pipeline()` scripts |
| Standalone: scheduled repository reviewer | Read-only `tools` plus `allowed_tools`, `dontAsk`, `max_turns` and `max_budget_usd`, resume between runs, schema-checked continuity, `ResultError` handling |

## Surprises and traps

1. **Defaults leak the operator's setup.** Omitted `setting_sources` loads `~/.claude` settings, CLAUDE.md, skills, agents, commands and hooks. Auto memory, `~/.claude.json` and claude.ai connectors load even with `[]`. Isolation needs `CLAUDE_CONFIG_DIR` plus explicit options (section 6).
2. **Parent-directory CLAUDE.md.** The project source reads CLAUDE.md in cwd "and every parent directory". An agent whose cwd sits inside the dev repo picks up the developer CLAUDE.md (section 6).
3. **Omitted permission mode may be `auto`.** Pass the mode every time (section 4).
4. **`allowed_tools` is not a whitelist.** It pre-approves. Use `tools` to define what exists and `disallowed_tools` to remove (sections 4, 10).
5. **`can_use_tool` is silently skipped** for anything an earlier step approved. Gate money paths in a PreToolUse hook or with deny rules, which run first and beat bypass (section 4).
6. **Python env merges.** An `ANTHROPIC_API_KEY` in the parent process reaches the CLI, and in `-p` mode the key "is always used when present", overriding the subscription. **Inferred** risk of silent API billing (section 11).
7. **Base URL without a credential keeps the subscription login active.** **Inferred:** pointing `ANTHROPIC_BASE_URL` at a third-party Anthropic-compatible host without setting `ANTHROPIC_AUTH_TOKEN` would send the subscription OAuth credential there. Always pair the two (section 11).
8. **Tool search turns off on non-first-party base URLs.** Large MCP catalogs then load upfront on every request (section 7).
9. **Fallback models do not cover rate limits** (section 9).
10. **Sandbox is a no-op on native Windows**, and Python fails open by default (section 10).
11. **Hooks gap.** No SessionStart, SessionEnd, PostCompact, model-switch or elicitation callbacks in Python (section 3).
12. **Checkpointing misses Bash edits and subagent edits** (section 10).
13. **Task tools are off on newer models** unless you opt in (section 15).
14. **Workflows and usage limits.** In the SDK, a workflow agent that hits the subscription limit fails rather than waits (section 13).
15. **Windows wheel gaps.** Some recent releases shipped without a Windows wheel. Pin an exact version that has `win_amd64` (section 14).
16. **30-day transcript pruning** by `cleanupPeriodDays` unless changed (section 2).
17. **No context-editing option**, only compaction (section 8, UNCONFIRMED).
18. **Policy.** The docs steer SDK products to API keys. Running on one Max login fits only personal, ordinary use (section 11).
19. **Cost figures on a subscription are list-price estimates.** `max_budget_usd` still enforces against that estimate (Inferred from [cost-tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking)).
20. **Python drops unknown top-level message types** without error, so new TS-era events are invisible until Python adds them (Python lacks section).

## Where H1 was wrong or stale

Compared with `tracker/qma-v2/archive/2026-10-13-two-engine/H1-sdk-facts.md` (2026-10-13), Claude rows 1 to 10 only. Most of H1's Claude facts hold. These do not.

1. **`can_use_tool` "needs streaming input plus a dummy PreToolUse hook" (H1 item 4, fact 1). Stale.** The Python CHANGELOG for 0.2.140 (PyPI 2026-08-18) says the callback "now works with string prompts (not just ClaudeSDKClient)", with stdin kept open ([CHANGELOG](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/CHANGELOG.md)). The docs examples on [user-input](https://code.claude.com/docs/en/agent-sdk/user-input) and the [python ref](https://code.claude.com/docs/en/agent-sdk/python) still carry the "Required workaround" comment, so the docs lag the code. The dummy hook is harmless; the claim that it is required is out of date. A one-line test on 0.2.166 would settle it.
2. **"QMX must not keep a setup-token and inject it" (H1 item 1, fact 4). Overstated.** The legal text it quotes is aimed at developers who intermediate *their users'* credentials. The env-vars page documents `CLAUDE_CODE_OAUTH_TOKEN` as an "Alternative to /login for SDK and automated environments" ([env-vars](https://code.claude.com/docs/en/env-vars)). For the operator's own token in his own app, the docs do not forbid it. H1's "/login inside the engine's own `CLAUDE_CONFIG_DIR`" is a valid, more conservative option, not the only allowed one. Two practical differences H1 missed: a setup-token "can only make model requests" (no claude.ai connectors, no Remote Control), and Chrome integration stays off with it ([authentication](https://code.claude.com/docs/en/authentication), [chrome](https://code.claude.com/docs/en/chrome)). This is a policy reading; the operator decides.
3. **OS list "Alpine 3.19+" for the SDK (fact 9). Misleading for Python.** That list is the Claude Code CLI's. The Python package publishes no musllinux wheel and no Windows ARM64 wheel, and five recent releases shipped with no Windows wheel at all ([PyPI JSON](https://pypi.org/pypi/claude-agent-sdk/json)). Alpine needs the sdist plus a native CLI (UNCONFIRMED that it works).
4. **Effort mid-session (fact 6, UNVERIFIED there).** Still no Python method. TS has `applyFlagSettings({ effortLevel })` ([configuration](https://code.claude.com/docs/en/agent-sdk/configuration)). So this is a confirmed Python gap, not an unknown. Per-agent `effort` on `AgentDefinition` and per-query `effort` do exist ([types.py](https://raw.githubusercontent.com/anthropics/claude-agent-sdk-python/main/src/claude_agent_sdk/types.py)).
5. **Rate limits (fact 10). Incomplete.** H1 lists `RateLimitEvent` only. It misses the `credits_required` rejection, the headless `/usage` report with plan rows ([TS ref](https://code.claude.com/docs/en/agent-sdk/typescript)), and that fallback models never fire on rate limits ([model-config](https://code.claude.com/docs/en/model-config)).
6. **Cookbook 08 "multi-agent workflow scripts", marked not opened.** It is the primary evidence that the Workflow tool runs from Python (`claude-agent-sdk>=0.2.90`). H1 had no row on workflows; the SDK docs alone suggest TS only ([cookbook 08](https://github.com/anthropics/claude-cookbooks/blob/main/claude_agent_sdk/08_Dynamic_workflows.ipynb)).
7. **Isolation recipe (fact 3). Missing two leaks.** Project CLAUDE.md is read from cwd "and every parent directory", so cwd placement matters. A parent-process `ANTHROPIC_API_KEY` reaches the CLI through Python's merged `env` and wins over the subscription in `-p` mode (sections 6 and 11). H1's `["project"]` option also re-opens `.mcp.json`, project hooks and project skills.
8. **Not wrong, still open.** Whether the `user` source follows `CLAUDE_CONFIG_DIR` remains UNCONFIRMED here too. The env-vars page says settings, history and plugins live there, which supports it but does not name skills and agents.
