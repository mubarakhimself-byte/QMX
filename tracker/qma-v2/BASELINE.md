# QMA v2 harness baseline: Claude Code / Codex / OpenAI Agents SDK parity

> **Known corrections (2026-10-13 evening).** This file is the base for the harness, but these points are wrong or open. Where they conflict, `research/H1-sdk-facts.md` and `reviews/2026-10-13-*.md` win.
> - Claude sign-in: QMX never stores or injects a Claude token. The operator runs `/login` in QMX's own `CLAUDE_CONFIG_DIR` (H1 fact 4). H17's "ChatGPT token refresh" stays for the OpenAI route only.
> - ChatGPT plan route: use `api.openai.com/v1/responses` with the OAuth token, never `chatgpt.com/backend-api` (H1 fact 17). Probe it first.
> - Agent and skill folders come from QMX's own config home, never the operator's personal `~/.claude` (lines ~206, ~253).
> - Line ~360 (other providers on the Claude engine) is rejected by the operator.
> - Computer use is not in the harness: no subscription route offers it (H1 facts 8, 16).
> - The UI protocol is research 32 Part B (today's 14 block kinds plus a live SSE channel), not Codex JSON-RPC (H2 row).
> - Missing here and required: router and accounts, the money read-only hook, long-lived sessions with transcript export.


Status: research, 2026-10-13. Not ratified. Feeds the "harness first" ruling.

Sources read:

- **Codex** clone `D:\QMX-research\sources\repos\codex`, commit `a9b0815` (2026-10-11). Paths below are relative to `codex-rs/`. Studied only; nothing was built or run.
- **OpenAI Agents SDK** clone `D:\QMX-research\sources\repos\openai-agents-python`, commit `125efa0` (2026-10-08). Paths are relative to `docs/`. The clone holds docs and a few `src` files, so SDK claims rest on its docs.
- **Claude Code / Claude Agent SDK** docs at `https://code.claude.com/docs/en/<page>`, fetched 2026-10-13. Cited as `cc:<page>`. Pages: hooks, permissions, sub-agents, model-config, prompt-caching, agent-sdk/permissions, agent-sdk/sessions, agent-sdk/agent-loop, agent-sdk/modifying-system-prompts, context-window, memory, authentication, settings, sandboxing.

`UNVERIFIED` means no primary source confirmed the claim in this pass.

How to read the matrix (section 2). Each capability has four entries:

- **Claude:** how Claude Code or the Claude Agent SDK does it, cited to the docs.
- **Codex:** how Codex does it, cited to `file:line` in the clone.
- **OpenAI SDK:** what the OpenAI Agents SDK gives, cited to its docs.
- **QMA v2 rule:** what QMX must provide so both engines reach the baseline, and where Claude's design is rebuilt on the OpenAI side.

---

## 1. Summary in plain words

1. Claude Code already gives us the "structure": rules, modes, hooks, sub-agent files, CLAUDE.md, memory, compaction and caching all work out of the box. The Claude Agent SDK runs the same loop, so the Claude engine needs **adapting, not rebuilding**.
2. The OpenAI Agents SDK gives "freedom" but very little structure. It has a loop, sessions, approvals that pause a run, tracing and MCP. It has **no** permission rules, no blocking hooks, no CLAUDE.md, no sub-agent depth limits, no compaction for non-OpenAI models, and no local sandbox on Windows.
3. Codex is the proof that an OpenAI-model harness can match Claude Code. Its source shows how. Its hooks even speak Claude Code's JSON format, including `hookSpecificOutput`, `permissionDecision`, `updatedInput` and "exit code 2 blocks".
4. So the rule is: **QMX owns one copy of each piece of structure.** The Claude engine uses Claude's native version. The OpenAI engine gets a QMX rebuild of Claude's design, using Codex's code as the reference.
5. The rebuilt pieces are: a permission gate (Claude's deny, then ask, then allow), a hook runner (Claude's wire format), project instructions (CLAUDE.md plus AGENTS.md), a sub-agent tool, local compaction, a skill loader, memory files and a thread store.
6. On the OpenAI side, QMX must own the shell, file and edit tools. The SDK's lifecycle hooks only observe; they cannot block. Its tool guardrails do not cover `ShellTool` or `ApplyPatchTool`. A gate inside our own tools is the only place every call can be stopped.
7. The UI talks to both engines through one protocol: Codex's thread, turn and item model, with approvals sent as server-to-client requests.
8. Credentials go in the OS keyring (Windows Credential Manager on this machine), the way Codex's `auto` mode does it. They never go in files or `.env`.
9. No sandbox by default (operator ruling). Each engine runs in its own child process, with a scrubbed environment and a kill-tree. The permission gate is the main safety control.
10. Effort and model switches cost a cache rebuild on most setups, so the UI warns before a mid-session switch, as Claude Code does.
11. Usage is normalised into one event shape. Rate-limit windows come from Claude's rate-limit events and from Codex-style `x-codex-*` headers on the ChatGPT route.
12. OpenAI's tracing sends data to OpenAI by default. QMX must replace the trace processors and keep traces local.
13. Risk on the record (not re-asked): Anthropic's docs say third-party products must not offer claude.ai login, and plan limits assume "ordinary, individual usage" (research `01` §6). A one-user QMX on his own Max plan is the closest fit to that allowance.
14. Biggest gaps between the OpenAI SDK and the baseline: blocking hooks, rule-based permissions, compaction on DeepSeek/GLM/Kimi/MiniMax, sub-agent limits, and remembered "always allow" decisions.
15. Section 3 lists 18 items that must ship before anything else. Each one has a side-by-side check against vanilla Claude Code or Codex.

---

## 2. Parity matrix

### 2.0 At a glance

| # | Capability | Claude engine | OpenAI engine needs | Rebuild from |
|---|---|---|---|---|
| 1 | Loop, interrupt, steer | native | thin adapter | Codex `turn/steer` semantics |
| 2 | Sessions / threads | native (JSONL) | QMX thread store | Claude list/fork API shape |
| 3 | Built-in tools | native | QMX tool set | Claude tool set, plus Codex `apply_patch` for GPT |
| 4 | Permissions | native | QMX gate | Claude rules, plus Codex amend-on-approve |
| 5 | Hooks | native | QMX hook runner | Claude wire format (Codex already copies it) |
| 6 | Sub-agents | native | QMX `Agent` tool | Claude definitions, plus Codex limits |
| 7 | Effort / thinking | native | ModelSettings mapping | Claude levels and cache warning |
| 8 | Compaction | native | QMX compactor | Codex local and remote compaction |
| 9 | Caching / prompt layers | native | QMX prompt builder | Claude layers, plus Codex `prompt_cache_key` |
| 10 | Skills / plugins / MCP | native | QMX skill loader; SDK MCP | Claude skill dirs |
| 11 | Memory | native | QMX memory files | Claude MEMORY.md; Codex phases later |
| 12 | Config layering | native | QMX layers | Claude scopes, plus Codex profiles |
| 13 | Credentials | native (file/Keychain) | QMX SecretStore | Codex keyring `auto` |
| 14 | Process separation | partial | QMX supervisor | Codex env policy; sandbox deferred |
| 15 | Usage / limits | native events | header parsing | Codex `rate_limits.rs` |
| 16 | Observability | OTel | replace SDK trace export | Codex otel config |
| 17 | UI protocol | message stream | adapter | Codex app-server v2 |

### 2.1 Agent loop, turns, interrupt and steer

- **Claude:** prompt, then tool calls, then results, repeated until a reply has no tool calls. Each cycle is a turn. `max_turns` and `max_budget_usd` cap the loop, and the result subtypes are `success`, `error_max_turns`, `error_max_budget_usd` and `error_during_execution` (cc:agent-sdk/agent-loop). Streaming input keeps the session alive; a message queued mid-turn starts a new turn (same page, "Turns and budget"). Interrupt: `ClaudeSDKClient.interrupt()` (UNVERIFIED in this pass; noted in research `01`).
- **Codex:** `Op::Interrupt` aborts the current task (`protocol/src/protocol.rs:653`). `Op::TurnInput` submits input with a routing behaviour (`protocol.rs:703`). The app server exposes `turn/start`, `turn/steer` and `turn/interrupt` (`app-server-protocol/src/protocol/common.rs:1057,1069,1075`). `TurnSteerParams` adds input to the active turn (`v2/turn.rs:311`). `TurnStartParams` can override model, effort and sandbox for this turn and later turns (`v2/turn.rs:240-266`).
- **OpenAI SDK:** `Runner.run/run_streamed` loops through model, handoff and tool calls until a final output, raising `MaxTurnsExceeded` (running_agents.md:27-46). `result.cancel()` stops at once; `cancel(mode="after_turn")` lets the turn finish (streaming.md:61). `RunState.add_input()` stages input that is admitted "immediately before the next model call" (results.md:146-158), which is the steer equivalent. Default `max_turns` value: UNVERIFIED.
- **QMA v2 rule:** one `Engine.turn()` contract with `interrupt()` and `steer(input)`. On OpenAI, steer = `cancel(after_turn)`, then `to_state()`, then `add_input()`, then resume. That matches Codex's "inject before next sampling". Turn caps (`max_turns`, budget) are QMX settings applied to both engines.

### 2.2 Sessions and threads: resume, fork, list, storage

- **Claude:** `continue`, `resume=<id>` and `fork_session=True`. `list_sessions()`, `get_session_messages()`, `rename_session()`, `tag_session()`. Stored at `~/.claude/projects/<encoded-cwd>/<id>.jsonl`; `SessionStore` adapters mirror them elsewhere (cc:agent-sdk/sessions). Forking copies the conversation, not the files.
- **Codex:** rollouts are JSONL under `~/.codex/sessions` and `archived_sessions` (`rollout/src/lib.rs:86-87`), with an SQLite state DB beside them (`state/src/lib.rs:149-155`). The app server has `thread/start`, `thread/resume`, `thread/fork`, `thread/list`, `thread/read`, `thread/archive`, `thread/revert` and `thread/search` (`common.rs:552,558,564,772`). `spawn_agent` can fork full history (`fork_context`, `core/src/tools/handlers/multi_agents/spawn.rs:103,227`).
- **OpenAI SDK:** a `Session` stores items by `session_id`. Backends: SQLite, Redis, SQLAlchemy, Dapr, MongoDB, Encrypted, and OpenAI Conversations (sessions/index.md:174-473). Branching only exists in `AdvancedSQLiteSession` (advanced_sqlite_session.md:119-187). There is no list API. A paused run is serialised with `RunState.to_json()` (human_in_the_loop.md:59).
- **QMA v2 rule:** QMX owns the thread index: id, engine, model, cwd, title, tags, parent, and fork point. On Claude, it stores the SDK session id and calls resume/fork. On OpenAI, it stores items in a QMX SQLite session and does fork by copying items up to a turn. List, rename, fork and archive come from QMX for both engines. Claude's API shape is the spec.

### 2.3 Built-in tools: shell, files, edit/patch, web, search, todo, plan

- **Claude:** `Read`, `Edit`, `Write`, `Glob`, `Grep`, `Bash`, `WebSearch`, `WebFetch`, `ToolSearch`, `Agent`, `Skill`, `AskUserQuestion`, `TaskCreate` and `TaskUpdate`. Read-only tools run in parallel; mutating tools run in order (cc:agent-sdk/agent-loop "Built-in tools", "Parallel tool execution"). Plan is a permission mode (cc:permissions:84).
- **Codex:** `exec_command` plus `write_stdin` (unified exec with PTY, `core/src/tools/handlers/shell_spec.rs:96,146`), legacy `shell` (`shell_spec.rs:67`), `apply_patch` (`handlers/apply_patch_spec.rs:19`), `update_plan` (`handlers/plan_spec.rs:43`), `view_image` (`handlers/view_image.rs:74`), `request_user_input` (`handlers/request_user_input_spec.rs:9`), `tool_search`, and hosted `web_search` (`tools/src/tool_search.rs:158`).
- **OpenAI SDK:** hosted tools (`WebSearchTool`, `FileSearchTool`, `CodeInterpreterTool`, hosted MCP, tool search) on the Responses API only. Local `ShellTool` and `ApplyPatchTool` need executors or editors **you** implement, and "SDK approval does not provide a sandbox" (tools.md:236-260). Function tools via `@function_tool`. The sandbox capabilities expose Codex-named `exec_command`, `write_stdin`, `apply_patch` and `view_image` (sandbox/guide.md:178-191).
- **QMA v2 rule:** QMX ships one tool package for the OpenAI engine, written as function tools so the QMX gate (2.4) and hooks (2.5) wrap every call. The set: Read, Write, Edit, Glob, Grep, Bash (PowerShell on Windows), WebFetch, TodoWrite or `update_plan`, AskUser, and `apply_patch` for GPT models, since Codex models are trained on it. Web search on DeepSeek, GLM, Kimi and MiniMax needs a QMX-provided search backend (UNVERIFIED which free one). Tool names and argument shapes copy Claude's, so hook matchers and rules are written once.

**Tool map** (Claude name is canonical; GPT models may also see the Codex-native name):

| Claude Code | Codex | OpenAI SDK primitive | QMX OpenAI engine |
|---|---|---|---|
| Bash / PowerShell | `exec_command`, `write_stdin`, `shell` | `ShellTool` (your executor) | function tool `Bash`, PTY optional; gate plus hooks |
| Read | (via shell) | none | function tool `Read` (line ranges, images) |
| Write / Edit | `apply_patch` | `ApplyPatchTool` (your editor) | `Edit` and `Write`, plus `apply_patch` for GPT |
| Glob / Grep | (via shell, `rg`) | none | function tools backed by ripgrep |
| WebFetch | none (network via shell) | none | function tool, domain rules |
| WebSearch | hosted `web_search` | `WebSearchTool` (Responses only) | hosted on OpenAI; QMX backend elsewhere (UNVERIFIED) |
| TaskCreate / TaskUpdate (todo) | `update_plan` | none | `TodoWrite`, emits `turn/plan/updated` |
| AskUserQuestion | `request_user_input` | none (approval interruptions only) | `AskUser`, sent as a server-to-client request |
| Agent | `spawn_agent` and companions | `Agent.as_tool()` | QMX `Agent` tool (2.6) |
| Skill | skill mentions | sandbox `Skills` capability | QMX `Skill` tool (2.10) |
| ToolSearch | `tool_search` | hosted tool search (Responses only) | defer MCP schemas; later |
| (image view via Read) | `view_image` | sandbox `view_image` | handled by `Read` |

### 2.4 Permissions: allow / ask / deny, modes, syntax, scopes, remembered decisions

- **Claude:**
  - Rules are evaluated deny, then ask, then allow; the first match wins and specificity does not matter (cc:permissions:62-64).
  - Syntax: `Tool` or `Tool(specifier)`, e.g. `Bash(npm run *)`, `Read(./src/**)`, `Edit(//abs/**)`, `WebFetch(domain:x)`, `mcp__server__tool`, `Agent(Explore)` (cc:permissions:95-568).
  - Modes: `default` (alias manual), `acceptEdits`, `plan`, `auto`, `dontAsk` and `bypassPermissions` (cc:permissions:79-87).
  - The SDK order is hooks, deny, ask, mode, allow, then `canUseTool` (cc:agent-sdk/permissions). The callback can allow with updated input or permissions, or deny with an interrupt (callback shape from research `01`; not re-fetched).
  - "Don't ask again" is permanent per repository and command for Bash, until session end for edits, and per repository and domain for WebFetch (cc:permissions table at line 15).
  - Scopes follow settings precedence: managed, CLI, local, project, user. Managed rules cannot be overridden (cc:permissions:697-699).
- **Codex:**
  - Three axes. **AskForApproval** is `untrusted`, `on-request` (default), `granular{sandbox_approval, rules, skill_approval, request_permissions, mcp_elicitations}` or `never` (`protocol/src/protocol.rs:1092-1128`).
  - **SandboxPolicy** is `danger-full-access`, `read-only{network_access}`, `external-sandbox` or `workspace-write{writable_roots, network_access, exclude_tmpdir_env_var, exclude_slash_tmp}` (`protocol.rs:1178-1226`). `.git` and `.codex` stay read-only inside writable roots (`protocol.rs:1228-1240`).
  - **execpolicy** uses Starlark `prefix_rule(pattern, decision=allow|prompt|forbidden, justification, match, not_match)` and `host_executable()` (`execpolicy/README.md`; parser `execpolicy/src/parser.rs:349,437`; `Decision` `execpolicy/src/decision.rs:9-16`). Rules live in `<codex_home>/rules/*.rules`, default `default.rules` (`core/src/exec_policy.rs:54-56`).
  - Remembered decisions are `ReviewDecision::{Approved, ApprovedForSession, ApprovedExecpolicyAmendment, ApprovedMcpPolicyAmendment, NetworkPolicyAmendment, Denied, TimedOut, Abort}` (`protocol.rs:4245-4280`). "Always" appends a `prefix_rule` to `default.rules` (`execpolicy/src/amend.rs:65`).
- **OpenAI SDK:** `needs_approval=True` or a callable per tool; it fails closed on unreadable arguments (human_in_the_loop.md:11-17). The run pauses with `interruptions`, and `state.approve/reject` resolves them. `always_approve` and `always_reject` are sticky **only inside that run state** (human_in_the_loop.md:49-61). `on_approval` callbacks give programmatic decisions for Shell and ApplyPatch (human_in_the_loop.md:93-101). Local MCP servers have `require_approval` (mcp.md:261). No rule language, no modes, no scopes.
- **QMA v2 rule:**
  - QMX ships **one PolicyEngine** using Claude's syntax and Claude's evaluation order (hooks, deny, ask, mode, allow, ask the user). It supports the same modes except `auto`, whose classifier is a later item.
  - **Claude engine:** QMX writes rules into the session's settings and answers `can_use_tool` from the same engine.
  - **OpenAI engine:** every QMX tool calls `gate(tool, input)` before running. "Ask" becomes `needs_approval=True`, and the UI answer flows back through `RunState.approve/reject`.
  - Codex's best idea is ported to both engines: approval choices are once, this session, always (writes a rule to `.qmx/settings.local.json`), deny with a message, and abort the turn.
  - Codex `prefix_rule` maps to `Bash(<prefix> *)`. Compound commands are split and checked per sub-command, as Claude does (cc:permissions:221-227).

**Codex-to-QMX permission mapping** (to import a Codex user's settings, and to keep the GPT side familiar):

| Codex setting | QMX equivalent (Claude vocabulary) |
|---|---|
| `approval_policy = "untrusted"` | mode `default`, plus a built-in read-only allowlist (Claude's read-only commands) |
| `approval_policy = "on-request"` | mode `default`; the model may ask to escalate via AskUser |
| `approval_policy = "never"` | mode `dontAsk` (failures go back to the model, never to the user) |
| `granular{...}` | per-category switches in the gate: shell, rules, skill scripts, MCP elicitation |
| `sandbox = "read-only"` | mode `plan` (writes ask or are refused) |
| `sandbox = "workspace-write"` | gate boundary: writes inside cwd and `additionalDirectories` are allowed in `acceptEdits` |
| `sandbox = "danger-full-access"` | mode `bypassPermissions` (deny and ask rules still apply) |
| `network_access = false` | `WebFetch` and network-command rules set to ask (not enforced by the OS without a sandbox) |
| `prefix_rule(decision="allow")` | `allow: Bash(<tokens> *)` |
| `prefix_rule(decision="prompt")` | `ask: Bash(<tokens> *)` |
| `prefix_rule(decision="forbidden", justification=...)` | `deny: Bash(<tokens> *)`, with the justification shown to the model |
| `ApprovedForSession` | session-scoped allow, kept in memory |
| `ApprovedExecpolicyAmendment` | "always" writes a rule to `.qmx/settings.local.json` |

### 2.5 Hooks: events, inputs and outputs, block / allow / modify, exit codes

- **Claude:**
  - 33 events (cc:hooks), including `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PermissionDenied`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `SubagentStart`, `SubagentStop`, `Stop`, `StopFailure`, `PreCompact`, `PostCompact`, `PreModelSwitch`, `PostModelSwitch`, `Notification`, `ConfigChange`, `CwdChanged`, `FileChanged`, `WorktreeCreate`, `Elicitation` and `SessionEnd`.
  - Exit 0: stdout is parsed as JSON. Exit 2: block, with stderr as the reason. Any other code: non-blocking error.
  - JSON fields: `continue`, `stopReason`, `systemMessage`, `decision:"block"`, and `hookSpecificOutput{hookEventName, additionalContext}`.
  - PreToolUse returns `permissionDecision` of allow, deny, ask or defer, plus `updatedInput`. PermissionRequest returns `decision.behavior` allow or deny, plus `updatedInput`.
  - Handler types: `command`, `http`, `mcp_tool`, `prompt` and `agent`. Sources: user, project, local, managed, plugin `hooks/hooks.json`, and skill and sub-agent frontmatter.
  - A hook "allow" never overrides deny or ask rules (cc:permissions:589).
- **Codex:**
  - 12 events: `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `SubagentStart`, `SubagentStop`, `Stop` and `Interrupt` (`protocol/src/protocol.rs:1688-1701`).
  - Handlers: `command`, `mcp_tool`, `prompt` and `agent`, run sync or async (`protocol.rs:1705-1717`). Config comes from `hooks.json` in each config folder plus TOML, with a trust identity per hook (`hooks/src/engine/discovery.rs:94,339,769`). JSON schemas for every event are in `hooks/schema/generated/`.
  - The output schema matches Claude's: `continue`, `stopReason`, `suppressOutput`, `systemMessage`, `decision`, and `hookSpecificOutput{permissionDecision, permissionDecisionReason, updatedInput, additionalContext}` (`pre-tool-use.command.output.schema.json`). Exit 2 blocks, with stderr as the reason (`hooks/src/events/pre_tool_use.rs:261-276`).
  - **Differences from Claude:** PreToolUse `ask` is rejected, plain `allow` without `updatedInput` is rejected, and `continue:false` is rejected (`hooks/src/engine/output_parser.rs:369-375,441-460`). PermissionRequest ignores `updatedInput` and `updatedPermissions` (`output_parser.rs:401-410`). PostToolUse cannot rewrite MCP output (`output_parser.rs:430-438`).
- **OpenAI SDK:** `RunHooks` and `AgentHooks` (`on_agent_start/end`, `on_llm_start/end`, `on_tool_start/end`, `on_handoff`) are observers with no return value that blocks (agents.md:262-302). Blocking exists only as input and output guardrails (tripwires) and as tool guardrails. Tool guardrails cover function tools and local MCP tools only, not Shell, ApplyPatch, Computer, hosted tools or `Agent.as_tool` (guardrails.md:71-78). `call_model_input_filter` can edit the prompt before each model call (running_agents.md:149).
- **QMA v2 rule:**
  - QMX ships **one hook runner** that reads Claude-format hook config (settings `hooks` blocks and plugin `hooks.json`) and speaks Claude's stdin/stdout/exit-code contract. Because Codex copied that contract, scripts written for either tool work unchanged.
  - **Claude engine:** native hooks; QMX only adds UI notifications.
  - **OpenAI engine:** the runner fires from QMX code. `SessionStart` and `SessionEnd` fire from the engine host. `UserPromptSubmit` fires before `Runner.run`. `PreToolUse`, `PostToolUse` and `PermissionRequest` fire inside the gate wrapper of every QMX tool. `Stop` fires on the final output; a `decision:block` there re-enters the loop with the reason as input. `Pre/PostCompact` fire in the QMX compactor. `SubagentStart/Stop` fire in the QMX `Agent` tool.
  - Claude's full semantics (including `ask` and `updatedInput`) are the target, not Codex's subset.

**Hook event map.** "Fires from" says where the QMX OpenAI engine must raise each event.

| Claude Code event | Codex | QMX OpenAI engine fires from | Baseline? |
|---|---|---|---|
| SessionStart | yes | engine host, on thread open or resume | yes |
| SessionEnd | yes | engine host, on close | yes |
| UserPromptSubmit | yes | before `Runner.run`; may block or add context | yes |
| PreToolUse | yes (no `ask`; allow needs `updatedInput`) | QMX tool gate, before the rules | yes |
| PermissionRequest | yes (no `updatedInput`) | QMX gate, before the UI approval request | yes |
| PostToolUse | yes | QMX tool wrapper, after the result | yes |
| PostToolUseFailure | no | QMX tool wrapper, on exception | yes |
| Stop | yes | final output; `block` re-enters the loop | yes |
| SubagentStart / SubagentStop | yes | QMX `Agent` tool | yes |
| PreCompact / PostCompact | yes | QMX compactor | yes |
| Interrupt (Codex only) | yes | engine host `interrupt()` | yes (QMX extension) |
| PermissionDenied | no | QMX gate, on a rule deny | later |
| PostToolBatch | no | after parallel tool calls finish | later |
| PreModelSwitch / PostModelSwitch | no | `/model` handler | later |
| Notification, MessageDisplay | no | UI layer | later |
| StopFailure | no | loop error handler | later |
| ConfigChange, CwdChanged, FileChanged, DirectoryAdded | no | config and file watchers | later |
| WorktreeCreate / WorktreeRemove | no | worktree feature, when built | later |
| InstructionsLoaded | no | project-instructions loader | later |
| Elicitation / ElicitationResult | MCP elicitation via app server | MCP client | later |
| TaskCreated / TaskCompleted, TeammateIdle, Setup, UserPromptExpansion | no | none for now | no |

### 2.6 Sub-agents: definition, roles, depth and thread limits, model per agent, background

- **Claude:**
  - Markdown with frontmatter. Locations by priority: managed, then `--agents`, then `.claude/agents/`, then `~/.claude/agents/`, then plugin `agents/`.
  - Fields: `name`, `description`, `tools`, `disallowedTools`, `model` (alias, full id or `inherit`), `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation: worktree` and `omitClaudeMd`.
  - Nesting defaults to 3 levels (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`). At most 20 run at once (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`). Background agents surface their permission prompts in the main session.
  - Each sub-agent starts with a fresh context and returns only its summary. It can be resumed by agent id via `SendMessage`. Transcripts are kept under the session's `subagents/` folder. Built-ins: Explore, Plan and general-purpose (cc:sub-agents).
  - A sub-agent never inherits `bypassPermissions` unless the parent has it (cc:agent-sdk/permissions, "Subagent inheritance").
- **Codex:**
  - V1 tools: `spawn_agent`, `send_input`, `resume_agent`, `wait_agent` and `close_agent` (`core/src/tools/handlers/multi_agents/*.rs`). V2 tools: `spawn_agent`, `send_message`, `followup_task`, `wait_agent`, `list_agents` and `interrupt_agent` (`multi_agents_v2/*.rs`).
  - Spawn arguments: `agent_type` (role), `model`, `reasoning_effort` and `fork_context` (`multi_agents/spawn.rs:223-227`).
  - Config: `[agents] enabled`, `max_concurrent_threads_per_session` (alias `max_threads`), `max_depth`, `default_subagent_model`, `default_subagent_reasoning_effort`, and roles as `[agents.<role>] description / config_file / nickname_candidates` (`config/src/config_toml.rs:757-796`). Role files are discovered in `<config>/agents/` (`agent-roles/src/loader.rs:78`).
  - Defaults: 6 threads (`core/src/config/mod.rs:254`) and depth 1 (`mod.rs:264`). The limit raises `AgentLimitReached` (`core/src/agent/control/execution.rs:42-47`).
- **OpenAI SDK:** `Agent.as_tool()` (manager pattern) and handoffs (agents.md:185-242). A different model per agent works via `Agent.model` or a `ModelProvider` (models/index.md:343-360). Approvals from nested agents surface on the outer run (human_in_the_loop.md:5-7). No depth limit, no concurrency limit, no background registry, no definition files. The experimental `codex_tool` wraps the Codex CLI as a tool (tools.md:917-945).
- **QMA v2 rule:**
  - One definition format: Claude's markdown and frontmatter, from `.claude/agents/` and `~/.claude/agents/` plus QMX's own store.
  - **Claude engine:** passes definitions natively.
  - **OpenAI engine:** QMX provides an `Agent` function tool (Claude's name and shape). It builds a nested `Agent` with the definition's prompt, tools, model and effort, runs it with its own QMX session, and returns the final text. The tool enforces depth (default 3, as Claude), a concurrency cap (default 6, as Codex, configurable), and permission-mode inheritance (never escalate to bypass).
  - `background: true` runs as an asyncio task in a QMX registry, with `SendMessage` and `wait`/`list`/`interrupt` tools that copy Codex V2. Its approvals route to the main thread's UI with the agent's name.
  - A different model per sub-agent works across engines only within one engine per turn. Cross-engine delegation (Claude parent, GPT child) goes through a QMX tool that starts a new thread on the other engine (research `19` §12).

### 2.7 Effort and thinking

- **Claude:** levels are `low`, `medium`, `high`, `xhigh` and `max`, with a per-model default (`medium` on the 5.5 family). Set it with `/effort`, `--effort`, `CLAUDE_CODE_EFFORT_LEVEL`, `effortLevel` or frontmatter `effort` (cc:model-config). Adaptive thinking applies on newer models; `ultrathink` affects one turn. Cache impact: most models keep one cache per effort level, but on Opus/Sonnet/Haiku 5.5 and Fable 5.1, with an API key or subscription, a change keeps the cache. Claude Code asks for confirmation while the cache is warm (cc:prompt-caching "Changing effort level"). Model switches always miss the cache (same page, "Switching models").
- **Codex:** `ReasoningEffort` is `none`, `minimal`, `low`, `medium` (default), `high`, `xhigh`, `max`, `ultra`, `persistent` or `Custom(String)` (`protocol/src/openai_models.rs:62-75`). It can be overridden per turn and kept for later turns through `TurnStartParams.effort` (`v2/turn.rs:263-265`); sub-agents take `reasoning_effort` at spawn. A reasoning change counts as `reasoning_changed`, which stops reuse of the previous websocket response (`core/src/client.rs:434`). Whether the server prompt cache survives is UNVERIFIED.
- **OpenAI SDK:** `ModelSettings(reasoning=Reasoning(effort=..., mode=..., context=...))`, with GPT-5.6 supporting `max`, `mode="pro"` and `context="all_turns"`. Mode and context work on Responses only; Chat Completions takes only `effort` (models/index.md:56-96). Mid-session change: pass new `ModelSettings` on the next run. No cache-aware warning.
- **QMA v2 rule:** QMX exposes Claude's five levels as the UI vocabulary and maps them per provider. For OpenAI it passes the value through, plus `none` and `ultra` where the model lists them. For Chat Completions providers it sends `reasoning.effort` only where the provider accepts it (UNVERIFIED for DeepSeek, GLM, Kimi and MiniMax). Changes apply from the next request. The UI shows Claude's cache warning for any model switch and for effort changes on models where the provider documents a cache split.

### 2.8 Compaction

- **Claude:** compaction runs automatically near the limit. The window is set by `/autocompact <n>`, `autoCompactWindow`, `--autocompact` or `CLAUDE_CODE_AUTO_COMPACT_WINDOW`, from 100K to 1M (cc:model-config "Auto-compact window"). `/compact <focus>` is manual. After compaction, CLAUDE.md, memory and MCP tools reload, the 5 most recent files are re-read, and invoked skills are re-injected (cc:context-window "What survives compaction"). The SDK emits `compact_boundary`. Summary instructions can live in CLAUDE.md, and `PreCompact` sees `trigger` manual or auto (cc:agent-sdk/agent-loop "Automatic compaction"). The summary request reuses the cached prefix (cc:prompt-caching "Compacting the conversation").
- **Codex:**
  - Local compaction uses the `SUMMARIZATION_PROMPT` template, a handoff summary of progress, decisions, constraints, next steps and critical data (`prompts/templates/compact/prompt.md`; `prompts/src/compact.rs:1-2`). It inserts `SUMMARY_PREFIX` plus the summary as a new history (`core/src/compact.rs:383`) and keeps recent user messages (`compact.rs:567-677`).
  - Remote compaction is used when `provider.capabilities().remote_compaction` is `V2` (`core/src/tasks/compact.rs:62-75`; `core/src/compact_remote_v2.rs`).
  - Thresholds: `model_auto_compact_token_limit`, its scope, and an optional turn-end percentage (`config/src/config_toml.rs:181-190`). The default is 90% of the context window (`openai_models.rs:461`). The prompt can be overridden with `compact_prompt` or `experimental_compact_prompt_file` (`config_toml.rs:278,562`). Sub-agents drop the auto limit (`core/src/agent/child_config.rs:140`).
- **OpenAI SDK:** `OpenAIResponsesCompactionSession` wraps any session and calls `responses.compact` after a turn when `should_trigger_compaction` fires. `run_compaction({"force": True})` is manual. It works on the **OpenAI Responses API only** (sessions/index.md:227-281). `ModelSettings.context_management` takes `compact_threshold` (models/index.md:418). Nothing exists for Chat Completions providers.
- **QMA v2 rule:** QMX owns a compactor for the OpenAI engine. It uses server compaction where the provider supports it (OpenAI API key; ChatGPT route UNVERIFIED). Otherwise it uses a **local summary**, porting Codex's prompt, prefix and kept-user-messages logic, plus Claude's re-injection of project docs, memory, recent files and invoked skills. Default threshold: 90% of the model window (Codex), overridable per model (Claude's `autoCompactWindow`). `/compact <focus>` and the `Pre/PostCompact` hooks work on both engines. The UI shows a compaction item in the thread.

### 2.9 Prompt caching and system-prompt layering

- **Claude:**
  - Layers, most stable first: system prompt and tool definitions; then project context (CLAUDE.md, auto memory, rules); then the conversation.
  - Cache breakers: model switch, effort change on older models, fast mode, adding or removing MCP tools when tool search is off, enabling plugins with MCP, denying a whole tool, compaction, and upgrades.
  - Cache-safe: editing CLAUDE.md mid-session (it only applies after `/clear` or `/compact`), changing mode or output style, invoking skills, rewinding, and spawning sub-agents.
  - TTL is 1h for the main conversation on a subscription and 5m for sub-agents (cc:prompt-caching).
  - Agent SDK: preset `claude_code` with `append`. `exclude_dynamic_sections` moves per-user memory paths out of the system prompt so many sessions share one cache entry. CLAUDE.md is injected as conversation context, not system prompt (cc:agent-sdk/modifying-system-prompts).
- **Codex:**
  - Base instructions are per-model prompt files (`core/gpt_5_codex_prompt.md`, `core/gpt_5_2_prompt.md`, `models-manager/prompt.md`). They can be overridden by `model_instructions_file` and extended by `developer_instructions` (`config/src/config_toml.rs:254,275`).
  - AGENTS.md is read from the project root (marker `.git`) down to the cwd and concatenated; `AGENTS.override.md` wins; fallback names and a byte cap are configurable; user and project docs are joined with a separator (`core/src/agents_md.rs:1-18,42-49,68`).
  - `prompt_cache_key` is the session id, or `<source>:<parent_thread_id>` for internal sub-sessions (`core/src/client.rs:641-653`). Request changes that break websocket reuse are listed in `client.rs:384-447`.
- **OpenAI SDK:** `instructions` (static or dynamic function, agents.md:244), `prompt_cache_retention` and `prompt_cache_options` (explicit breakpoints, 30m TTL on GPT-5.6) (models/index.md:419-460). Third-party prefix caching: UNVERIFIED per provider.
- **QMA v2 rule:**
  - QMX builds the OpenAI-engine prompt in Claude's order: (1) a fixed base prompt per model family, ported from Codex's model prompt files for GPT and written once for others; (2) tool definitions in fixed order; (3) the project-context block (CLAUDE.md, AGENTS.md, MEMORY.md) as the **first user message**, which is Claude's `exclude_dynamic_sections` behaviour; (4) the conversation.
  - Dynamic notes (file changed, mode changed) are appended as system-reminder messages and never edit earlier blocks.
  - Set `prompt_cache_key = thread_id` (Codex). Set explicit breakpoints after block 3 where the provider supports them.
  - The Claude engine uses preset `claude_code` with `append` and `exclude_dynamic_sections=True`.

### 2.10 Skills, plugins and MCP

- **Claude:** skills are `SKILL.md` folders in user, project and plugin dirs. Only names and descriptions load at start; the body loads on invocation through the `Skill` tool or `/name`. After compaction, invoked skills are re-injected, capped at 5,000 tokens each (cc:context-window). Plugins bundle skills, agents, hooks and MCP servers. MCP tools are deferred behind tool search by default (cc:prompt-caching "Connecting or removing an MCP server").
- **Codex:** skills from `SKILL.md` (`skills/src/parser.rs:22-43`) with `SkillScope` User, Repo, System or Admin (`protocol/src/protocol.rs:3979-3984`), `skills/list` on the app server, and skill-script approvals in `GranularApprovalConfig.skill_approval` (`protocol.rs:1124`). Plugins use `.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json` (`core-plugins/src/agent_plugin_mcp_overlay.rs:21`; `core-plugins/src/loader.rs:486`). MCP runs through `rmcp-client` and `codex-mcp`.
- **OpenAI SDK:** first-class MCP over stdio, streamable HTTP and SSE, plus hosted MCP, a server manager, tool filtering and per-server `require_approval` (mcp.md). Skills only exist as a sandbox `Skills` capability or `ShellTool(environment={"type":"local","skills":[...]})` (sandbox/guide.md:178-208; tools.md:249).
- **QMA v2 rule:** one QMX skill loader scans `.claude/skills/`, `~/.claude/skills/` and `.agents/skills/` (Codex and SDK convention). For the OpenAI engine it injects the name and description list into the context block and exposes a `Skill` tool that returns the body. MCP config is read once by QMX and passed to both SDKs. Plugins: Claude's plugin layout is the QMX format; Codex's marketplace is reference only.

### 2.11 Memory

- **Claude:** CLAUDE.md is user-written, at managed, user, project, local and nested levels, plus `.claude/rules` with `paths:`. Claude Code can read AGENTS.md directly (v2.1.277+) or via an `@AGENTS.md` import (cc:memory). Auto memory is written by Claude, per repository, and loaded at start (the first 200 lines or 25KB of MEMORY.md, cc:memory table and cc:context-window).
- **Codex:** a two-phase pipeline when the feature is on, only for root, non-ephemeral sessions. Phase 1 extracts `raw_memory` and `rollout_summary` per rollout in parallel, redacting secrets. Phase 2 has one consolidation sub-agent, with no approvals and no network, that rewrites `~/.codex/memories/` (git-baselined) from a workspace diff (`memories/README.md`; runtime in `core/src/memories/`).
- **OpenAI SDK:** a sandbox-only `Memory()` capability with the same two phases, producing `MEMORY.md`, `memory_summary.md` and `rollout_summaries/` (sandbox/memory.md:51-94). Sessions are conversation history, not memory.
- **QMA v2 rule:** QMX keeps memory in **Claude's file layout** so both engines read the same notes. The OpenAI engine loads MEMORY.md (200 lines or 25KB) into the context block and writes through normal Edit calls under the gate. Codex-style phase-2 consolidation is a later item, not baseline.

### 2.12 Config layering: user, project, managed; profiles

- **Claude:** precedence is managed (file, MDM or server), then CLI `--settings`, then `.claude/settings.local.json`, then `.claude/settings.json`, then `~/.claude/settings.json` (cc:settings). There are no profiles; a separate `CLAUDE_CONFIG_DIR` acts as one, per account (cc:authentication "multiple accounts").
- **Codex:** `ConfigLayerSource` is PackagedDefaults, Mdm, System, EnterpriseManaged, User (plus a selected profile), Project (`.codex/`), SessionFlags, and legacy managed (`config/src/config_layer_source.rs:4-60`). Profiles are `[profiles.<name>]` plus `profile = "<name>"` (`config/src/config_toml.rs:363-367`; `config/src/profile_toml.rs:24`). Policy constraints live in `requirements.toml` (`hooks/src/engine/discovery.rs:318-334`).
- **OpenAI SDK:** none. Everything is code (`RunConfig`, `ModelSettings`).
- **QMA v2 rule:** QMX uses Claude's five layers (managed is optional for one user), and every setting is UI-editable (operator standing rule). Codex-style **profiles** are added as named presets bundling engine, model, effort, mode and tool set. The OpenAI engine reads only QMX config. The Claude engine gets QMX config injected through `settings` and `setting_sources`.

### 2.13 Credentials storage per OS

- **Claude:** macOS uses the Keychain, falling back to `~/.claude/.credentials.json` (0600). Linux uses `~/.claude/.credentials.json` (0600). Windows uses `%USERPROFILE%\.claude\.credentials.json` with profile ACLs. `CLAUDE_CONFIG_DIR` relocates it. Precedence: cloud provider, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_API_KEY`, `apiKeyHelper`, `CLAUDE_CODE_OAUTH_TOKEN` (one-year token from `setup-token`), profiles, then `/login` (cc:authentication).
- **Codex:** `AuthCredentialsStoreMode` is `file` (default, `CODEX_HOME/auth.json`), `keyring` (fail if unavailable), `auto` (keyring, else file) or `ephemeral` (memory only) (`config/src/types.rs:136-146`). MCP OAuth defaults to `auto` (`types.rs:151-163`). `AuthKeyringBackendKind` is `direct` or `secrets` (an encrypted local file whose key sits in the keyring) (`types.rs:168-173`). Keyring backends per OS: windows-native (Credential Manager), apple-native (Keychain), Linux secret-service, BSD sync-secret-service (`keyring-store/Cargo.toml:14-26`). The `secrets` crate uses age with scrypt and a `SecretsManager` set/get/delete/list per scope (`secrets/src/local.rs:14-18`; `secrets/src/lib.rs:91-157`).
- **OpenAI SDK:** none. The caller passes `AsyncOpenAI(api_key=...)`.
- **QMA v2 rule:** QMX `SecretStore` copies Codex's design:
  - (a) the backend is the OS keyring by default (Windows Credential Manager, macOS Keychain, Linux Secret Service), with labels `qmx/<provider>/<name>` (matching the existing `qmx/*` labels);
  - (b) `ephemeral` mode for tests and CI;
  - (c) an age-encrypted file fallback with its key in the keyring, for headless Linux without Secret Service, never plain JSON;
  - (d) scoped `set/get/delete/list`;
  - (e) ChatGPT sign-in tokens and refresh tokens stored the same way, with refresh owned by QMX;
  - (f) secrets reach the Claude child process only through env injection at spawn. The Claude engine's own `/login` stays in its own `CLAUDE_CONFIG_DIR`.

### 2.14 Process separation and sandboxing per OS

- **Claude:** the Bash sandbox is **off by default**. macOS uses Seatbelt; Linux and WSL2 use bubblewrap plus socat, with network through a local proxy and allowed domains starting empty. Native Windows runs unsandboxed. File tools, MCP and hooks run outside the sandbox (cc:sandboxing). `bypassPermissions` refuses root outside a recognised sandbox (cc:agent-sdk/permissions).
- **Codex:** `get_platform_sandbox` picks `MacosSeatbelt`, `LinuxSeccomp`, or `WindowsRestrictedToken` only if enabled (`sandboxing/src/manager.rs:50-63`). macOS runs `/usr/bin/sandbox-exec` with `.sbpl` policies (`sandboxing/src/seatbelt.rs:62`; `sandboxing/src/seatbelt_*.sbpl`). Linux uses bwrap plus `no_new_privs` plus seccomp, with legacy Landlock (`linux-sandbox/README.md`; `linux-sandbox/src/seccomp.rs:1`). Windows uses a restricted token, ACLs, WFP network filtering, and an elevated mode with sandbox users (`windows-sandbox-rs/src/token.rs:501`, `wfp.rs:67`, `acl.rs`, `elevated/`). `WindowsSandboxLevel` is Disabled (default), RestrictedToken or Elevated (`protocol/src/config_types.rs:297-302`).
- **OpenAI SDK:** none for local tools. `SandboxAgent` offers `UnixLocalSandboxClient` (macOS and Linux, "trusted local development"), Docker, or hosted providers (sandbox/clients.md:25-40).
- **QMA v2 rule:**
  - Not sandboxed by default (ruling); the realistic baseline is process separation. Each engine session runs in its **own child process** under a QMX supervisor, so a crash or hang kills one thread, not the app.
  - The environment is an **allowlist**, so keys are injected per provider and nothing else leaks. The supervisor kills the whole process tree (a Job Object on Windows, a process group on POSIX).
  - The cwd is pinned to the thread's workspace. Shell commands get a timeout and an output cap.
  - The PolicyEngine (2.4) is the control: the workspace-write-style boundary is enforced in the QMX gate (writes outside the workspace and additional dirs ask). Protected paths (`.git`, `.claude`, `.qmx`) always ask, as in Codex `WritableRoot` (`protocol.rs:1228`).
  - Later, opt-in: Seatbelt on macOS and bwrap on Linux (ported from Codex). The Windows restricted token is the hardest (needs elevation and WFP); treat it as a separate project. Claude's sandbox can be switched on for the Claude engine on macOS and Linux.

### 2.15 Usage and limits reporting

- **Claude:** every `ResultMessage` has `usage`, `model_usage` (the whole tree), `total_cost_usd` and `num_turns`. Rate-limit status events stream as observability events (cc:agent-sdk/agent-loop "Message types", "Handle the result"). `/usage` shows the session's cache hit ratio (cc:prompt-caching). Research `01` notes SDK issue #435: usage is missing in 20-70% of concurrent chats.
- **Codex:** `TokenUsage` and `TokenUsageInfo` (`protocol/src/protocol.rs:2363,2398`). `RateLimitSnapshot{primary, secondary, credits, plan_type, rate_limit_reached_type}` (`protocol.rs:2471-2486`) is parsed from `x-codex-primary-used-percent` and `secondary` headers (`codex-api/src/rate_limits.rs:57-80`) and from stream events (`rate_limits.rs:135`). App-server surfaces: `account/rateLimits/read`, `account/rateLimits/updated`, `thread/tokenUsage/updated` and `account/usage/read` (`common.rs:1341,1979,2020`).
- **OpenAI SDK:** `Usage` covers requests, input and output tokens, cached and cache-write tokens, reasoning tokens, and per-request entries (usage.md). There are no rate-limit windows. Compaction usage is added to the run (sessions/index.md:237).
- **QMA v2 rule:** one `UsageEvent{thread, turn, engine, model, input, cached_read, cache_write, output, reasoning, cost?}` and one `LimitEvent{window: 5h|weekly|…, used_pct, resets_at}`. Claude: from result and rate-limit messages, recomputed from per-message usage when the result is missing. ChatGPT route: parse `x-codex-*` headers, if the transport exposes response headers (UNVERIFIED for the Agents SDK model classes). API-key providers: tokens and cost only.

### 2.16 Observability: traces and logs

- **Claude:** OpenTelemetry metrics and events, with cache tokens per session (cc:prompt-caching "Check cache performance"). `OTEL_LOG_RAW_API_BODIES=file:<dir>` dumps request bodies, which is the only way to see system reminders (cc:agent-sdk/modifying-system-prompts "See what Claude received"). Transcripts are JSONL.
- **Codex:** `[otel]` config with `log_user_prompt`, `log_agent_responses` and tool-result byte caps (`config/src/types.rs:623-635`), tracing spans such as `codex.sampling` with conversation and turn ids (`core/src/session/turn.rs:2550-2555`), the rollout JSONL, and `rollout-trace`.
- **OpenAI SDK:** tracing is **on by default and exports to OpenAI**. Spans: trace, task, turn, agent, generation, function, guardrail and handoff. It is off for ZDR orgs. Replace it with `set_trace_processors()`, or disable it with `OPENAI_AGENTS_DISABLE_TRACING=1`. The docs recommend disabling it for non-OpenAI keys (tracing.md:1-40,164-171; models/index.md:326).
- **QMA v2 rule:** at engine start, QMX calls `set_trace_processors([QmxLocalProcessor])`, so nothing goes to OpenAI unless the operator turns it on. One trace id per turn, shared with the UI's turn id. The Claude engine's OTel goes to the same local collector. Logs never contain secrets; Codex's redaction (`secrets/src/sanitizer.rs`) is the model.

### 2.17 The UI protocol

- **Claude:** an async message stream: `system/init`, `assistant` (one block each), `user` (tool results), `stream_event` (partials), `system/compact_boundary` and `result`. Approvals are the `can_use_tool` callback inside the SDK process (cc:agent-sdk/agent-loop "Message types").
- **Codex:** app-server v2 JSON-RPC.
  - Requests: `thread/start`, `thread/resume`, `thread/fork`, `thread/list`, `thread/compact/start`, `turn/start`, `turn/steer`, `turn/interrupt`, `turn/settings/update`, `model/list`, `skills/list`, `hooks/list` and `config/*` (`app-server-protocol/src/protocol/common.rs:552-1341`).
  - Notifications: `thread/started`, `turn/started`, `turn/completed`, `item/started`, `item/completed`, `item/agentMessage/delta`, `item/commandExecution/outputDelta`, `item/reasoning/*`, `turn/plan/updated`, `turn/diff/updated`, `hook/started`, `hook/completed`, `thread/compacted` and `thread/tokenUsage/updated` (`common.rs:1979-2030`).
  - **Approvals are server-to-client requests**: `item/commandExecution/requestApproval`, `item/fileChange/requestApproval`, `item/permissions/requestApproval`, `item/tool/requestUserInput` and `mcpServer/elicitation/request` (`common.rs:1797-1828`). `serverRequest/resolved` closes them. Answers use `ReviewDecision` (2.4).
- **OpenAI SDK:** `stream_events()` (raw response, run item, agent updated) and `interruptions` after the stream drains (streaming.md; human_in_the_loop.md:103-107).
- **QMA v2 rule:** QMX's UI protocol **is** Codex's thread / turn / item model. Both engines are adapted into it: Claude messages become items, and SDK run items become items. Approvals and AskUser are server-to-client requests with Codex's decision set. Plan, diff, hook-run, compaction and usage notifications use the same names. The UI never knows which engine it is talking to, apart from a badge.

### 2.18 Where Claude's design is rebuilt on the OpenAI side

Each module is built once in QMX. The Claude engine uses the SDK's native feature, and QMX only configures it. The OpenAI engine runs the QMX module.

| QMX module | Claude engine (native, configured by QMX) | OpenAI engine (QMX code) | Codex reference to study |
|---|---|---|---|
| `engine.host` | `ClaudeSDKClient` in a child process | `Runner.run_streamed` in a child process | `core/src/codex_thread.rs`, `app-server` |
| `protocol` | message-to-item adapter | run-item-to-item adapter | `app-server-protocol/src/protocol/common.rs`, `v2/` |
| `threads` | session id, `list_sessions`, `fork_session` | QMX SQLite session plus fork-by-copy | `rollout/`, `thread-store/`, `state/` |
| `policy` | settings rules plus `can_use_tool` | gate in every tool plus `needs_approval` | `execpolicy/`, `core/src/exec_policy.rs`, `core/src/tools/approvals.rs` |
| `hooks` | native settings hooks | QMX runner (Claude wire format) | `hooks/src/engine/`, `hooks/schema/generated/` |
| `tools` | built-ins | QMX function tools | `core/src/tools/handlers/`, `apply-patch/` |
| `prompt` | preset `claude_code`, `append`, `exclude_dynamic_sections` | base prompt plus context block plus reminders | `core/src/agents_md.rs`, `core/*_prompt.md`, `core/src/client.rs:641` |
| `compact` | native auto and `/compact` | QMX compactor (remote where offered, else local) | `core/src/compact.rs`, `compact_remote_v2.rs`, `prompts/templates/compact/` |
| `agents` | `agents=` definitions, Agent tool | QMX `Agent` tool plus background registry | `core/src/agent/`, `tools/handlers/multi_agents_v2/`, `agent-roles/` |
| `skills` | `setting_sources` | QMX loader plus `Skill` tool | `skills/src/` |
| `memory` | auto memory | MEMORY.md load plus gated edits | `memories/` (later) |
| `config` | `settings` / `setting_sources` injection | QMX layered config | `config/src/config_layer_source.rs`, `profile_toml.rs` |
| `secrets` | env injection at spawn | same store; ChatGPT token refresh | `keyring-store/`, `secrets/`, `login/` |
| `usage` | result plus rate-limit messages | `Usage` plus header parsing | `codex-api/src/rate_limits.rs` |
| `telemetry` | OTel to local collector | `set_trace_processors` (local) | `otel/`, `core/src/otel_init.rs` |
| `supervisor` | same | same | `process-hardening/`, `core/src/exec_env.rs` |

### 2.19 What each OpenAI-engine route gets from the SDK, and what QMX fills in

The OpenAI engine is really several routes. The Responses API gets the most from the SDK. Chat Completions routes need QMX to fill every gap.

| Route | API shape | Server compaction | Hosted web search | Reasoning control | Rate-limit windows | QMX fills in |
|---|---|---|---|---|---|---|
| GPT via ChatGPT sign-in | Responses (Codex backend; UNVERIFIED via SDK) | UNVERIFIED | UNVERIFIED | effort, maybe mode | yes via `x-codex-*` headers (if exposed) | token refresh, header parsing, local compaction fallback |
| GPT via OpenAI API key | Responses | yes (`responses.compact`) | yes | effort, mode, context | no (org limits only) | trace export off, tool set, gate |
| OpenRouter | Chat Completions (OpenAI-compatible) | no | no | per model (UNVERIFIED) | no | local compaction, search backend, cost from `usage` |
| DeepSeek | Chat Completions | no | no | UNVERIFIED | no | local compaction, search backend |
| GLM (Z.ai) | Chat Completions | no | no | UNVERIFIED | no | same |
| Kimi | Chat Completions | no | no | UNVERIFIED | no | same |
| MiniMax | Chat Completions | no | no | UNVERIFIED | no | same |

Rules that follow:

- Use one model shape per workflow; the SDK warns that the two shapes support different features (models/index.md:343-360).
- Turn on `strict_feature_validation` so Responses-only settings sent to Chat Completions raise an error instead of a warning (models/index.md:95).
- Set `set_tracing_disabled()` or a local processor for every non-OpenAI key (models/index.md:326).
- Anthropic-compatible endpoints from DeepSeek, GLM, Kimi and OpenRouter (research `01` §1) are a second option: run those models on the **Claude** engine and get Claude's structure for free. This trades provider-native features for harness parity. Decide per provider after H5 and H11 pass.

---

## 3. The harness minimum

Ship these before anything else. Each check runs the same task side by side: QMX on the Claude engine, QMX on the OpenAI engine (GPT via ChatGPT sign-in, plus one API-key provider), and vanilla Claude Code or Codex. Pass = QMX behaves the same as the vanilla tool on both engines.

| # | Item | Acceptance check (side by side) |
|---|---|---|
| H1 | **Engine host + supervisor**: one child process per thread, env allowlist, kill-tree, crash isolation | Kill one thread's process mid-turn: the other threads keep running and the UI marks that thread failed. Codex app-server behaves the same per thread. |
| H2 | **UI protocol** (Codex v2 thread/turn/item, deltas, server-to-client approvals) | "List the files and summarise README": the item sequence (message, command, message) and streaming deltas match a recorded Codex app-server run on both engines. |
| H3 | **Interrupt and steer** | Start `ping -n 30 localhost` (Windows) or `sleep 30`, then steer "stop and say done": the turn ends with "done" within one model call on both engines, as with Codex `turn/steer`. Interrupt leaves no orphan process. |
| H4 | **Thread store**: list, resume, fork, rename, archive | Fork after turn 2 and continue both branches: the histories diverge and the original is untouched. Resume after a QMX restart keeps full context, matching Claude SDK `fork_session` and `resume`. |
| H5 | **Core tool set on the OpenAI engine** (Read, Write, Edit, Glob, Grep, Bash/PowerShell, WebFetch, TodoWrite, AskUser, apply_patch for GPT) | Run the same 5-step refactor script in Claude Code and on QMX-OpenAI: same files changed, same test result, and edits shown as diffs. |
| H6 | **PolicyEngine** (Claude syntax and order; modes default, acceptEdits, plan, dontAsk, bypass) on both engines | Rules `deny: Bash(git push *)`, `ask: Bash(rm *)`, `allow: Bash(npm test *)`: the outcomes for `git push`, `cd x && rm -f y` and `npm test` match vanilla Claude Code on both engines. Plan mode blocks writes. |
| H7 | **Approvals with memory** (once, session, always writes a rule, deny with message, abort) | "Always allow `npm run lint *`" writes a rule. A new session does not ask again. Matches Claude's "don't ask again" and Codex `ApprovedExecpolicyAmendment`. |
| H8 | **Hook runner** (Claude wire format; PreToolUse, PostToolUse, PermissionRequest, UserPromptSubmit, Stop, SessionStart, SessionEnd, Pre/PostCompact, SubagentStart/Stop) | One script that exits 2 on `rm -rf` blocks the call in Claude Code, Codex and QMX-OpenAI. A PreToolUse `updatedInput` rewrite and `additionalContext` injection reach the model on both QMX engines. |
| H9 | **Project instructions** (CLAUDE.md plus AGENTS.md, root to cwd, as the first user message) | A repo with a rule only in AGENTS.md and one only in CLAUDE.md: both rules are obeyed on both engines, as in Claude Code and Codex. |
| H10 | **Prompt builder and caching** (stable order, reminders appended, `prompt_cache_key=thread_id`) | 10-turn session: from turn 2 on, cached-read tokens are at least 80% of input on the Claude engine and on GPT, the same order as vanilla Claude Code `/usage` and Codex. |
| H11 | **Compaction** (auto at 90% or a per-model window; `/compact <focus>`; local summariser for non-OpenAI) | Fill the context on a 128K model: auto-compaction fires, the task continues and CLAUDE.md rules still hold afterwards. `/compact focus on X` keeps X. Compare with Claude Code `/compact`. |
| H12 | **Model and effort switch** with cache warning | Mid-session `/model` and `/effort` apply to the next request on both engines. The UI warns while the cache is warm, as Claude Code does. |
| H13 | **Sub-agents** (Claude definitions; `Agent` tool on OpenAI; depth 3; cap 6; per-agent model and effort; background with SendMessage, wait, list, interrupt) | One `.claude/agents/reviewer.md` with `model:` and `tools: Read, Grep` runs read-only on both engines. A 4th nesting level is refused. A background agent's approval reaches the main UI with its name. Compare with Claude Code and Codex `spawn_agent`. |
| H14 | **Skills and MCP** (shared loader; `Skill` tool on OpenAI; one MCP config) | The same `SKILL.md` is listed and invoked by name on both engines. The same stdio MCP server's tool runs under the PolicyEngine on both. |
| H15 | **Memory files** (Claude layout; 200 lines or 25KB loaded) | A preference saved in MEMORY.md in one session is followed in a new session on both engines, as with Claude Code auto memory. |
| H16 | **Config layers and profiles** (user, project, local, plus named profiles; all UI-editable) | A project setting overrides a user setting, and a profile switch changes engine, model, effort and mode in one click. Matches Claude precedence and Codex `--profile`. |
| H17 | **SecretStore** (keyring default, ephemeral, encrypted-file fallback; ChatGPT token refresh) | No secret appears in any file, log or trace (grep the QMX data dir). Keys survive a restart. Codex `auto` mode behaves the same. |
| H18 | **Usage, limits and local tracing** (UsageEvent and LimitEvent; OpenAI trace export off) | Per-turn tokens and cache numbers match each provider's own report within 1%. 5h and weekly windows show for Claude and the ChatGPT route. A network capture shows no request to OpenAI's trace endpoint. |

Build order (dependencies): H1, H2 and H17 first (process, wire and secrets). Then H4, H5 and H6 with H7 (threads, tools, gate). Then H8 and H9 with H10 (hooks and prompt). Then H11 and H12, then H13, H14 and H15, and finally H16 and H18. Every item lands with its side-by-side check recorded in the thread log. "Done" means the QMX column and the vanilla column agree.

Not in the minimum (later, by design): the auto-mode classifier, OS sandboxes (Seatbelt, bwrap, Windows restricted token), Codex-style phase-2 memory consolidation, a plugin marketplace, worktree isolation for sub-agents, and cross-engine delegation (research `19` §12).

### Open items carried as UNVERIFIED

1. "Sign in with ChatGPT" driving the Agents SDK: taken as given by the operator. The mechanism (Codex uses `https://chatgpt.com/backend-api/codex`, `agent-identity/src/lib.rs:61`) and whether response headers reach QMX are not confirmed.
2. Server-side compaction on the ChatGPT route.
3. Reasoning-effort support and prefix caching on DeepSeek, GLM, Kimi and MiniMax via Chat Completions.
4. The Agents SDK's default `max_turns`.
5. A free web-search backend for non-OpenAI providers.
6. Whether a Codex effort change splits the OpenAI server prompt cache.
7. The exact `can_use_tool` return types and the `interrupt()` method name in the current Python Claude Agent SDK. They were taken from research `01`, not re-fetched.
