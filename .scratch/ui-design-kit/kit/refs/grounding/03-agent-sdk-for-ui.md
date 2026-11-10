# Does the Claude Agent SDK give QMX anything for the UI?

Date: 2026-11-09. Read-only grounding for the UI designer of QMX's copilot, sessions, approvals, sub-agents, usage and workflow screens.

## Direct answer

No widgets. The Claude Agent SDK is headless: it ships no components, no chat view and no Anthropic UI kit. What it gives a UI is **data and controls**: a typed live event stream, an approval callback, session files plus list, read, fork and rename functions, and a client that can interrupt, switch model and mode, and rewind files. A designer can build every screen on that. The ready-made visual pieces come from elsewhere:

- **MCP Apps** (official MCP extension, spec 2026-01-26) put sandboxed HTML apps inline in chat. They render in Claude, Claude Desktop, VS Code Copilot and others. The SDK does not render them. QMX would need to host them itself (AppBridge from `@modelcontextprotocol/ext-apps`, or `@mcp-ui/client`).
- **Third-party adapters** exist and are current: CopilotKit / AG-UI `@ag-ui/claude-agent-sdk` (TS and Python), and assistant-ui (generic chat kit with an MCP Apps renderer, not a direct Agent SDK adapter). I found none from Anthropic.

QMX already forwards most of what matters. It keeps chat, tools, plan, sub-agent cards, approvals, questions, live tokens, interrupt, model, effort and mode switch, file rewind, compaction and plan limits. It drops thinking at rest, the init frame (slash commands, skills, tools, MCP list), context-window usage, per-turn cost and duration, the "compacting" status, hook events, structured tool outputs, the rich permission titles, sub-agent text, and session fork.

## Sources

- SDK source as installed by QMX: `claude-agent-sdk==0.2.166` (pinned at `qmx-agents/packages/qma-harness/pyproject.toml:8`), read from `D:/QMX-worktrees/audit-head/qmx-agents/.venv/Lib/site-packages/claude_agent_sdk/` (same wheel, published 2026-10-14). Cited below as `sdk/types.py:N`, `sdk/client.py:N`.
- TS reference: https://code.claude.com/docs/en/agent-sdk/typescript
- Approvals and questions: https://code.claude.com/docs/en/agent-sdk/user-input
- Todo tracking: https://code.claude.com/docs/en/agent-sdk/todo-tracking
- MCP Apps: https://modelcontextprotocol.io/extensions/apps/overview, spec https://github.com/modelcontextprotocol/ext-apps
- AG-UI adapter: https://cdn.jsdelivr.net/npm/@ag-ui/claude-agent-sdk@0.0.3/README.md, CopilotKit https://docs.copilotkit.ai/claude-sdk-python
- assistant-ui MCP Apps: https://www.assistant-ui.com/docs/tools/mcp-apps.md
- QMX code: `D:/QMX-worktrees/engine-base-read` at `3ae41ffc`, paths below relative to `qmx-agents/packages/qma-harness/src/qma/harness/`.

## 1. What the SDK gives a UI, feature by feature

### Stream message types (Python union `sdk/types.py:1854`)

| Message | What it carries | Screen use |
|---|---|---|
| `AssistantMessage` (`types.py:1378`) | content blocks, `model`, `parent_tool_use_id`, `error` (auth, billing, rate_limit, ...), per-message `usage`, `stop_reason` | Chat bubble; error banner; a model badge per reply |
| `TextBlock` / `ThinkingBlock` (`types.py:1194-1206`) | final text; thinking text plus signature. Opus 4.7+ omit thinking text unless `display="summarized"` (`types.py:2169`) | Collapsible "thinking" section |
| `ToolUseBlock` / `ToolResultBlock` (`types.py:1209-1223`) | tool id, name, input; result content, `is_error` | Tool cards that go started, then finished or error |
| `ServerToolUseBlock` / `ServerToolResultBlock` (`types.py:1239-1263`) | web_search, web_fetch, code_execution, advisor | Same tool card, a "server" variant |
| `UserMessage` (`types.py:1363`) | tool results, `tool_use_result` (the tool's structured output), `origin` (human, task-notification, peer, scheduled...) | Tells "your prompt" apart from injected turns |
| `StreamEvent` (`types.py:1736`) | raw API deltas (text_delta, thinking_delta, input_json_delta) with `parent_tool_use_id`; needs `include_partial_messages` | Live typing, and tool input filling in as it streams |
| `SystemMessage` init (`types.py:1461`) | session_id, model, cwd, tools, mcp_servers with status, permissionMode, slash_commands, skills, plugins, plugin_errors, agents, output_style, fast mode, capabilities | Session header; slash menu; "what this agent can use" panel; plugin error toast |
| `compact_boundary` (TS `SDKCompactBoundaryMessage`; Python arrives as plain `SystemMessage`) | trigger manual or auto, `pre_tokens` | Divider in the transcript: "context compacted from 182k" |
| `status` (TS `SDKStatusMessage`) | `status: "compacting" or null`, `permissionMode` | "Compacting..." spinner; mode chip that stays in sync |
| `TaskStarted / TaskProgress / TaskNotification / TaskUpdated` (`types.py:1549-1635`) | task id, description, `usage` (tokens, tool uses, ms), `last_tool_name`, status, summary, output_file | Sub-agent and background-job cards with a live meter |
| `ResultMessage` (`types.py:1695`) | subtype, is_error, duration_ms, duration_api_ms, num_turns, `total_cost_usd`, `usage`, `model_usage` per model (tokens, cost, contextWindow), `permission_denials`, `structured_output`, `terminal_reason`, `deferred_tool_use`, `api_error_status` | End-of-turn footer: cost, time, tokens; "stopped by you" vs "failed" |
| `RateLimitEvent` (`types.py:1753-1791`) | status allowed / warning / rejected, window five_hour / seven_day / opus / sonnet / overage, utilization, resets_at | Plan meter and a "near limit" warning |
| `ConversationResetMessage` (`types.py:1794`) | new conversation id after `/clear` | Empty the transcript; snapshot running totals |
| `HookEventMessage` (`types.py:1821`), needs `include_hook_events` | hook_started / hook_response with output and exit code | Activity log of guard decisions |
| TS-only extras (TS union) | `SDKToolProgressMessage`, `SDKToolUseSummaryMessage` (one-line summary of a run of tools), `SDKAPIRetryMessage`, `SDKPromptSuggestionMessage`, `SDKFilesPersistedEvent`, `SDKPermissionDeniedMessage`, `SDKNotificationMessage`, `SDKSessionStateChangedMessage`, `SDKCommandsChangedMessage`, `SDKElicitationCompleteMessage` and more | Retry toast, suggested next prompt chips, collapsed tool-run summaries |

### Permission flow

- `can_use_tool(tool_name, input, context)` (`types.py:278`) pauses the agent until the host answers; it may wait forever (user-input doc). `context` gives `suggestions` (ready rules for "always allow"), `tool_use_id`, `agent_id` (asked from inside a sub-agent), `blocked_path`, `decision_reason`, and display text: `title` ("Claude wants to read foo.txt"), `display_name` ("Read file"), `description` (`types.py:223-255`).
- Answers: allow, allow with edited input, allow and remember (`updated_permissions`), deny with a message, deny and interrupt (`types.py:259-274`).
- Modes: `default, acceptEdits, plan, bypassPermissions, dontAsk, auto` (`types.py:25`); live switch via `set_permission_mode` (`client.py:314`).
- `AskUserQuestion` arrives through the same callback: 1-4 questions, 2-4 options each, `header` up to 12 chars, `multiSelect`, optional `preview` (markdown or HTML, TypeScript only via `toolConfig.askUserQuestion.previewFormat`), free-text `response`. Not available inside sub-agents (user-input doc).
- Plan mode ends with the `ExitPlanMode` tool call, which comes through the same approval path.
- A `PreToolUse` hook can return `defer`, so the process exits and the session resumes later; the result carries `deferred_tool_use` (`types.py:1656`).
- Screen use: an approval card with title, subtitle, the diff or command, and buttons Once / Always / Edit / Reject; a question card with option chips and an "Other" field.

### Hooks useful to a UI

Python events (`types.py:284`): PreToolUse, PostToolUse, PostToolUseFailure, UserPromptSubmit, Stop, SubagentStart, SubagentStop, PreCompact, Notification, PermissionRequest. Output types also exist for model switch, elicitation, file changed, worktree create and message display (`types.py:645-725`). Screen use: a "waiting for you" notification from `PermissionRequest`/`Notification`; a sub-agent row appears on `SubagentStart`.

### Todo / plan tracking

The Task tools (`TaskCreate`, `TaskUpdate`, `TaskGet`, `TaskList`) or `TodoWrite` show up as plain `tool_use` blocks. The created task id comes back in `tool_use_result`. Status goes pending, in_progress, completed, deleted, and `activeForm` is the "now doing" label. **They are on by default only on Opus 4.7, Sonnet 4.6, Haiku 4.5 and earlier.** On newer models (Opus 5.5) they are off unless opted in with `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` or by listing them in tools (todo-tracking doc). Screen use: a checklist panel beside the chat.

### Sub-agents

- Define in code: `AgentDefinition` with description, prompt, tools, model, skills, mcpServers, maxTurns, background, effort, permissionMode (`types.py:108`). Agent tool input: description, prompt, subagent_type, model, effort, run_in_background, name, isolation worktree (TS reference).
- How progress looks: child tool calls arrive with `parent_tool_use_id` set to the spawning Agent call. Child text and thinking arrive only with `forward_subagent_text=True` (`types.py:2562`). `TaskStarted` / `TaskProgress` give description, tokens, tool count and the last tool. `stop_task(task_id)` stops one (`client.py:443`). After the fact, `list_subagents` and `get_subagent_messages` read child transcripts (`sdk/_internal/sessions.py:1286,1328`).
- Screen use: a sub-agent tree with a live "Read file x, 12k tokens, 40s" line, plus a drill-in to the child's own transcript.

### Sessions

Transcripts are JSONL on disk under the Claude config projects folder. The functions are: `list_sessions`, which returns title, first prompt, branch, cwd, tag and times (`types.py:2098`, `sessions.py:680`); `get_session_info` and `get_session_messages` (`sessions.py:739,1059`); and `rename_session`, `tag_session`, `delete_session` and `fork_session` (`session_mutations.py:53-240`). Options are `resume`, `fork_session`, `resume_session_at` (branch at a message), `continue_conversation` (`types.py:2391-2620`) and an optional external `session_store`. Screen use: a sessions sidebar with search, rename, tag, delete, and "branch from here" on any message.

### Interrupt and steer

`interrupt()` (`client.py:308`). The result's `terminal_reason` is aborted_streaming or aborted_tools. In streaming-input mode a new `query()` mid-turn steers the agent; the CLI folds it into the running turn. Screen use: a Stop button, and a composer that stays enabled while the agent works.

### Model, effort, thinking

`set_model` live (`client.py:341`); `model`, `fallback_model`, `effort` low / medium / high / xhigh / max (`types.py:2727`), `thinking` adaptive / enabled / disabled (`types.py:2714`). TS adds `supportedModels()`, `supportedCommands()`, `supportedAgents()` and `accountInfo()`. Screen use: a model and effort picker in the composer.

### Usage, cost and rate limits

Per turn: `ResultMessage.total_cost_usd`, `usage`, `model_usage[model].contextWindow`, durations. Per message: `AssistantMessage.usage`. Live context: `get_context_usage()` returns categories, total and max tokens, percentage, autocompact threshold, and the token cost of MCP tools, memory files and agents. It is the same data as `/context` (`types.py:1024`, `client.py:504`). Plan windows come from `RateLimitEvent`. Budgets: `max_budget_usd`, `max_turns`, `task_budget`. Screen use: a context ring in the composer, a cost line per turn, and a plan meter with reset time.

### Slash commands, skills, plugins

Init lists `slash_commands`, `skills`, `plugins`, `plugin_errors`; `get_server_info()` returns the commands and output styles (`client.py:540`). `skills=[...]|"all"` filters the skills (`types.py:2664`). Plugins are loaded locally via `plugins=[{"type":"local","path":...}]` (`types.py:1089`); a plugin bundles skills, agents, commands, hooks and MCP servers. Screen use: a "/" palette and an extensions page showing what loaded and what failed.

### MCP servers, including MCP Apps

Server types are stdio, SSE, HTTP and in-process SDK servers (`types.py:857-900`). Controls: `get_mcp_status()` (per-server status and tools), `toggle_mcp_server` and `reconnect_mcp_server` (`client.py:395-471`). TS adds `readMcpResource` and `setMcpServers`. The SDK forwards MCP Apps metadata but does **not render** an app. The in-process Python bridge drops server-to-client requests such as elicitation and sampling (`sdk/__init__.py:584`, `sdk_mcp_bridge.py:221`). To show an MCP App, the host reads the tool's `_meta.ui.resourceUri`, fetches the `ui://` HTML and renders it in a sandboxed iframe through AppBridge. Screen use: a connectors page (status, on/off, reconnect) and, if QMX hosts MCP Apps, live mini-apps inline in chat.

### Structured output

`output_format={"type":"json_schema","schema":...}` returns the data on `ResultMessage.structured_output` (`types.py:2742`). Screen use: a workflow step that fills a table or form instead of prose.

### File checkpointing and rewind

`enable_file_checkpointing=True` plus `rewind_files(user_message_id)` (`client.py:364`) restores files only. To rewind the conversation as well, use `resume_session_at` with a fork. Screen use: an "undo changes since this message" control on each prompt.

## 2. Known UI pieces: which are real and current

| Piece | Real? | What it is |
|---|---|---|
| Anthropic UI kit for Agent SDK | Not found | The SDK docs show terminal examples only; the UI is the host's job |
| MCP Apps (`@modelcontextprotocol/ext-apps`, spec 2026-01-26) | Real, current | Official extension. Hosts: Claude, Claude Desktop, VS Code Copilot, M365 Copilot, Goose, Postman and others. Host side uses AppBridge or `@mcp-ui/client` |
| AG-UI `@ag-ui/claude-agent-sdk` + CopilotKit | Real, early (0.0.x) | Adapter that turns Agent SDK events into AG-UI events for CopilotKit React components; Python variant exists |
| assistant-ui | Real | React chat kit with an MCP Apps renderer; wired to AI SDK, not directly to the Agent SDK |
| Community demos (e.g. Ridter/ChatAgentDemo) | Real, unofficial | FastAPI and React examples; reference only |

## 3. How QMX uses it (engine-base-read @ 3ae41ffc)

### Shape

One `ClaudeSDKClient` per chat (`chat.py:1-38`). A pure function `project()` turns every SDK message into "facts" (`project.py:239`). The facts become 14 stored `SessionBlock` kinds: user, text, plan, agents, tool, changed, artifact, table, entity, question, permission, panel, handoff, needs_you (`qmx-control/src/qmx_control/service.py:158-176`). They also become live-only `Delta`s on `GET /api/sessions/{sid}/live` (SSE, `routes.py:356-363`). Stored blocks are served by the qmx-control events route (`qmx-control/.../service.py:1440`). Options are built in `launch.py:708-741`.

### Passed through to the UI

| SDK feature | QMX carries it as | Where |
|---|---|---|
| Live text and thinking deltas (incl. sub-agent target) | SSE `delta` {kind text/thinking, tool_use_id} after token redaction | `project.py:383-397`, `routes.py:356-363`, `launch.py:732` |
| Final text | `text` block | `project.py:308-309` |
| Tool use / result, server tools | `tool` block, states started / finished / error | `project.py:312-321,329-380` |
| Plan tools TodoWrite / TaskCreate / TaskUpdate | `plan` block with raw input | `project.py:70,337-338` |
| Sub-agents (Agent/Task call, TaskStarted / Updated / Notification) | `agents` card; child tool blocks go into a child session | `project.py:339-351,517-553`, `chat.py:~1470-1490` |
| Sub-agent progress | SSE `tool_progress` delta "description: last tool" | `project.py:532-539` |
| Model error, failed turn | `needs_you` block | `project.py:324-325,409-411` |
| Compaction boundary | `changed` {kind compacted, trigger} | `project.py:554-556`, `chat.py:1440-1441` |
| Approvals (`can_use_tool`) | `permission` block {tool, input, reason, always rules, workspace}; answered at `POST /api/approvals/{ask_id}` with once, always, edit or reject | `chat.py:1495-1540`, `routes.py:365-371` |
| AskUserQuestion | `question` block; `Answers` by question text | `chat.py:270-301,1501` |
| Interrupt | `POST /api/sessions/{sid}/interrupt` | `chat.py:990-993`, `routes.py:306-309` |
| Model / effort / mode switch | quote-then-apply with a cache-loss warning; `set_model` and `set_permission_mode` live | `chat.py:396-414,923-925`, `routes.py:311-331` |
| File rewind | `GET`/`POST /api/sessions/{sid}/rewind`, `changed` {kind rewind} | `chat.py:995-1008`, `routes.py:339-350` |
| Resume | `resume=` when the transcript exists; chat list at `GET /api/chats` | `launch.py:730-731`, `routes.py:240-254,283-293` |
| Rate limits and plan meter | `Limits` into the usage ledger; `GET /api/usage` windows, readings, token sums, overage stop | `project.py:476-514`, `chat.py:1444-1445`, `qmx-router/.../readings.py:305-406` |
| MCP status | used inside launch (settle, toggle off failed servers, `needs_you`) | `chat.py:480-516,1200-1217` |
| Hooks | PreToolUse guard first on every call; optional observers on PreToolUse, PostToolUse, PreCompact, Stop | `launch.py:154-157,513-515,694-697` |

### Dropped or not exposed

| SDK feature | Status in QMX | Effect on screens |
|---|---|---|
| `ThinkingBlock` at rest | Dropped (`project.py:322`), only live deltas | Thinking is gone after reload |
| `system/init` (slash_commands, skills, tools, mcp_servers, plugins, agents, model, output_style) | Read only to catch unexpected plugins (`chat.py:1363-1368`); not sent to the UI (`project.py:557`) | No data for a "/" palette, a skills list or a "what's loaded" panel |
| `status` "compacting" | Dropped (`project.py:557`) | No compaction spinner, only the boundary afterward |
| `ResultMessage` cost, durations, usage, `permission_denials`, `structured_output` | Cost only goes to the ledger on plan chats (`chat.py:1442-1447`); the rest is not forwarded (`project.py:400-420`) | No per-turn cost/time footer; no denials list |
| `AssistantMessage.usage`, `get_context_usage()` | Unused; QMX estimates context tokens from the JSONL itself (`chat.py:363-389`) | No live context ring or breakdown |
| `TaskProgress.usage` (tokens, tool uses, ms) | Dropped; only the description and last tool | Sub-agent cards cannot show tokens or elapsed time |
| `tool_use_result` (structured tool output, e.g. TaskCreate's id) | Dropped (`project.py:364-380` uses text only) | The plan panel cannot pair task ids; it gets raw inputs |
| Permission `title`, `display_name`, `description`, `blocked_path`, `agent_id`, `tool_use_id` | Not copied into the `permission` block (`chat.py:1502-1507`) | The approval card must build its own wording; it cannot say which sub-agent asked |
| `forward_subagent_text` | Not set (`launch.py:708-741`) | Child sessions show tool calls but not the sub-agent's prose |
| `include_hook_events` | Not set | No hook activity log |
| `ConversationResetMessage` | Dropped (`project.py:281-282`) | Fine while `/clear` is not offered |
| `fork_session`, `resume_session_at`, `rename_session`, `tag_session`, `delete_session`, `list_sessions` | Unused; QMX keeps its own chat records and titles in qmx-control | No "branch from here"; rename and delete go through qmx-control, not the SDK |
| `output_format` structured output | Unused | |
| `stop_task(task_id)` | Unused; interrupt leaves background agents running (`chat.py:990-993`) | No per-sub-agent Stop button |
| `RateLimitEvent` utilization | Forwarded, via `/api/usage` only (not per chat) | |
| AskUserQuestion `preview` | TS-only feature; QMX is Python | No visual previews on question cards |
| MCP Apps | Not hosted | No inline app iframes |
| Todo tools on Opus 5.5 | QMX maps them (`project.py:70`) but does not opt in, as far as `launch.py:708-741` shows | The `plan` block may never appear on newer models; verify with a live session |

### Notes for the designer

- The 14 block kinds are fixed by design ("New meaning goes inside `content`, never a new block type", `project.py:3-5`). New screens should ask for fields inside the existing blocks, for example `cost` on a turn-end note or `title` on `permission`.
- Approvals and questions are durable blocks with ids that survive restarts (`chat.py:235-250`). An approvals inbox can list every `permission` and `question` block whose state is `asking`.
- Background and Child chats answer by policy or time out after `unattended_ask_seconds` (`chat.py:27-29`). The UI should show "answered by policy" and "expired" states (`console.py:265`).
