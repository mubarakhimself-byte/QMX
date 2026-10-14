# 04. One-engine baseline for QMA v2

Status: research, 2026-10-14. Not ratified. Step 4 of the one-engine runbook.

## What this file is

The operator defined the harness floor on 2026-10-12 at 10:02 UTC. He said "the tools you have access to, the capabilities you can do right out of the box, that's the baseline" (01 section 3, OM 10:02). He restated it on 2026-10-13. "It's literally the worst that QMX's harness can be" (01 section 3, T1 04:14 answer Q3). He wants it to behave like Claude Code. His sign-off is the option he picked, "Talk to it like Claude Code" (01 R10, T2 16:04 answer).

This file turns that floor into a list for one engine, the Claude Agent SDK in Python (01 R1). It has five parts.

1. What vanilla Claude Code and the Agent SDK give, and which of it QMA turns on.
2. What QMX adds on top, and where it plugs into today's code.
3. What stays out, and where it goes.
4. Checks the operator runs himself in the temporary console.
5. Checks the coding session runs first, live.

### Sources and how they are cited

| Tag | File |
|---|---|
| 01 | `research/one-engine/01-requirements.md`. Rulings are R1 to R38, requirements are "req N", hard rules are "hard rule N", corrections are C1 to C32. |
| 02a | `research/one-engine/02a-claude-agent-sdk.md`, cited by section number. Python SDK 0.2.166 with CLI 2.1.299. |
| 02b | `research/one-engine/02b-providers-translator-policy.md`, cited by section letter and probe id (A1, B1, D1 and so on). |
| HOW | `research/one-engine/how/HOW-one-engine.md`, cited by seam number (1 to 5, plus "event wire" and "session resume") and gotcha number. Commit `4eac8f69` of `rebuild/base`. |
| BL | `BASELINE.md` (2026-10-13 two-engine matrix). Used as evidence only. Its corrections box still holds and is applied here. |
| BACKLOG | `BACKLOG.md` item ids (B1 to B57, S1 to S4). |

Labels carried from the sources. **Fact** means a source states it. **Inferred** means derived from facts. **UNCONFIRMED** means no primary source confirmed it. Each UNCONFIRMED row has an agent-run check in section 5 that settles it.

### Corrections from BL that this file applies

- QMX never stores or injects a Claude token. The operator signs in through the CLI's own login inside QMX's own config folder (BL corrections box; 02b A, verdict A).
- GPT goes to `api.openai.com/v1/responses`, never `chatgpt.com/backend-api` (BL corrections box; 02b D item 3).
- Agent and skill folders come from QMX's own config folder, never his personal `~/.claude` (BL corrections box).
- Computer use is not in the harness (BL corrections box; 02a section 12; 02b E).
- The UI protocol is today's block kinds plus a live SSE channel, not Codex JSON-RPC (BL corrections box; HOW "event wire").
- BL said other providers on the Claude engine were rejected. The operator reversed that himself on 2026-10-13 18:28 and 18:32 (01 R1, R2). They are in.

---

## 1. What vanilla Claude Code and the Agent SDK give

### Defaults chosen for QMA agents, in one paragraph

"QMA agents" here means the console copilot and the helpers it starts. They get the `claude_code` tools preset and the `claude_code` system prompt preset with QMX's rules appended (02a section 10). This is a deliberate change from the daemon template, which runs with `tools=[]` and one read tool (HOW seam 1, seam 3, gotcha 8). The template locks Claude Code's tools away. The operator's floor is Claude Code's tools (01 hard rule 7). The money rule is therefore enforced by deny rules and a PreToolUse hook (section 2.3), not by removing Bash and the file tools. A custom system prompt would also drop the preset's safety instructions (02a section 10).

Column key. "SDK (Python)" is Yes, Partial or No, with the 02a citation. "Default for QMA" is **On**, **Off** or **Not available**.

### 1.1 Built-in tools

| # | Tool | SDK (Python) | How QMA turns it on | Default for QMA |
|---|---|---|---|---|
| T1 | Read | Yes (02a section 10, tools preset) | `tools` preset `claude_code` | **On** |
| T2 | Write | Yes (02a section 10) | Same preset | **On** |
| T3 | Edit | Yes (02a section 10) | Same preset | **On** |
| T4 | Glob | Yes (02a section 10) | Same preset | **On** |
| T5 | Grep | Yes (02a section 10) | Same preset | **On** |
| T6 | Bash, including background commands | Yes (02a sections 10, 13) | Same preset. Money patterns are denied (section 2.3). | **On** |
| T7 | PowerShell tool on Windows | UNCONFIRMED. Claude Code on Windows lists a PowerShell tool (seen in this Claude Code session's own tool list). 02a does not cover it. | Same preset, if the init tools list shows it (check S3) | **On** if present |
| T8 | NotebookEdit | Yes (02a section 10, checkpointing names it) | Same preset | **On** |
| T9 | WebFetch | Yes (02a section 10 preset; cookbook 00) | Same preset | **On** |
| T10 | WebSearch | Yes on the Claude plan (02a cookbook 00). UNCONFIRMED on third-party base URLs. | Same preset. Per-provider result recorded by check S8. | **On** |
| T11 | Agent (shown as `Task` in the init list) with built-in general-purpose, Explore and Plan | Yes (02a section 5) | Same preset, plus `agents=` for QMX definitions | **On** |
| T12 | Resume a helper by its agent id | Yes, by resuming the session and naming `agentId` (02a section 5) | Console resume (section 2.9) | **On** |
| T13 | Task list tools (TaskCreate, TaskUpdate) | Yes, but off by default on newer models (02a section 15) | Env `CLAUDE_CODE_ENABLE_TODO_TOOLS=1`. They feed the UI `plan` block (HOW "event wire"). | **On** |
| T14 | AskUserQuestion | Partial. Main agent only, never in helpers (02a section 5). Always reaches the callback, denied in `dontAsk` (02a section 4). | Same preset. The console answers it through `can_use_tool`. | **On** |
| T15 | Skill | Yes (02a section 6) | Same preset, skills from QMX's folder or plugin | **On** |
| T16 | ToolSearch (deferred MCP schemas) | Yes. Turns itself off on a non-first-party base URL (02a section 7). | Env `ENABLE_TOOL_SEARCH=true` on every third-party profile (02a section 7; 02b B, Meta) | **On** |
| T17 | Workflow (dynamic workflows) | Yes from Python, CLI 2.1.154 or later (02a section 13) | Allow `Workflow` per session when the operator asks | **Off** |
| T18 | Monitor | Yes (02a section 13) | Same preset | **On** |
| T19 | Stop a background task | Yes, `stop_task(task_id)` on the client (02a sections 1, 13) | Console command | **On** |
| T20 | Plan mode exit (ExitPlanMode) | Yes, plan is a permission mode (02a section 4) | Console `/plan` sets the mode | **On** |
| T21 | Cron tools (CronCreate, CronList) | UNCONFIRMED in Python. TS mentions them (02a section 13). | None now | **Off** |
| T22 | Worktree tools and helper `isolation: worktree` | No. Python `AgentDefinition` has no isolation field (02a section 5 field list). BL lists it as later. | None | **Not available** |
| T23 | Computer use | No. macOS, interactive only, not in `-p` (02a section 12; 02b E1) | None (section 3) | **Not available** |
| T24 | Claude in Chrome | No as documented. Needs `/login`, off with a long-lived token, SDK use UNCONFIRMED (02a section 12; 02b E4) | None (section 3) | **Not available** |
| T25 | Agent teams | No. "Claude doesn't spawn teammates" in SDK sessions (02a section 13) | None (section 3) | **Not available** |

Why T17 is off. Workflows run 16 agents at once by default and fail instead of waiting when the plan limit hits (02a section 13). That clashes with the 50% background cap (01 R6) and the operator's repeated "limit sub-agents" (01 section 5). It stays one console switch away. Workflow design is BACKLOG B33.

### 1.2 Extension: skills, commands, plugins, hooks, MCP, memory

| # | Capability | SDK (Python) | How QMA turns it on | Default for QMA |
|---|---|---|---|---|
| X1 | Skills (SKILL.md folders) | Yes, files only, no register API (02a section 6) | From QMX's config folder or QMX's local plugin | **On** |
| X2 | Custom slash commands | Yes, sent as `/<name>` in the prompt (02a section 6) | From QMX's folder or plugin | **On** |
| X3 | Built-in commands that work headless (`/compact`, `/clear`, `/context`, `/usage`) | Yes (02a section 6) | The console passes operator-typed `/` text through | **On** |
| X4 | Plugins | Partial. Local folders only (02a section 6) | `plugins=[QMX plugin folder]` | **On** |
| X5 | Hooks as Python callbacks (10 events: PreToolUse, PostToolUse, PostToolUseFailure, UserPromptSubmit, Stop, SubagentStop, PreCompact, Notification, SubagentStart, PermissionRequest) | Yes (02a section 3) | `hooks=` in options. QMX's money and journal hooks live here. | **On** |
| X6 | Hooks for the other 23 events (SessionStart, SessionEnd, PostCompact, model switch and more) | Partial. Shell hooks in settings or a plugin only (02a section 3) | The QMX plugin's hooks file, which the operator can edit | **On** (empty by default) |
| X7 | MCP over stdio, SSE and HTTP | Yes (02a section 7) | `mcp_servers=` built from QMX settings, with `strict_mcp_config=True` | **On** (none listed by default) |
| X8 | In-process MCP (`create_sdk_mcp_server`) | Yes. Sampling and elicitation not forwarded (02a section 7) | The `qmx` server (section 2.2) | **On** |
| X9 | CLAUDE.md | Yes. Read from cwd "and every parent directory" (02a section 6) | QMX's own CLAUDE.md in its config folder and workspace. cwd sits outside the dev repo (section 2.4). | **On** |
| X10 | Auto memory | Yes. Read even with `setting_sources=[]` (02a section 6) | Kept on, as the SDK default (01 R29). Must land inside QMX's folder (check S7). | **On** |
| X11 | `verbatim_prompts` (no `@path` or `/` dispatch for text the operator did not type) | Yes, CLI 2.1.248 or later (02a sections 6, 15) | On for any prompt built from tool output, news or files | **On** for injected text |
| X12 | Output styles | UNCONFIRMED in Python. Only a TS reload method is named (02a "Python lacks") | None | **Off** |

### 1.3 Permissions and turn control

| # | Capability | SDK (Python) | How QMA turns it on | Default for QMA |
|---|---|---|---|---|
| P1 | Six permission modes (default, acceptEdits, plan, bypassPermissions, dontAsk, auto) | Yes (02a section 4) | Pass `permission_mode="default"` every time. Omitting it can start in `auto` (02a section 4, trap 3). Console `/mode` switches with `set_permission_mode`. | **On** |
| P2 | Allow, ask and deny rules with Claude Code syntax | Yes. Order is hooks, deny, ask, mode, allow, callback. Deny beats bypass (02a section 4). | QMX settings (UI-editable) plus the money deny rules in code | **On** |
| P3 | `can_use_tool` approval callback, with "approve and remember" | Yes (02a section 4) | The console shows the ask and sends the answer back. Remembered rules write to QMX's settings. | **On** |
| P4 | PreToolUse `defer` for approvals that take hours | Yes (02a sections 3, 15) | Used later for background agents | **Off** |
| P5 | Interrupt | Yes on `ClaudeSDKClient`, not on `query()` (02a section 1) | QMA uses the client. Console Ctrl+C calls `interrupt()`. | **On** |
| P6 | Type while it works (streaming input, queued messages) | Yes, streaming input mode (02a section 1) | QMA always uses streaming input | **On** |
| P7 | Model switch mid-session | Yes, `set_model` on the client (02a section 1). A switch recomputes the cache (02a section 8). | Console `/model`, with a cache-cost warning first (01 req 6) | **On** |
| P8 | Effort and thinking | Partial. Per session and per helper, no mid-session setter in Python (02a section 15, H1 correction 4) | Set at session start and in each helper definition. A mid-session change resumes the session with the new value (Inferred). | **On** |
| P9 | System prompt preset `claude_code` with `append` | Yes (02a section 10) | QMX rules go in `append` | **On** |
| P10 | Bash sandbox | Partial. No-op on native Windows, fails open in Python (02a section 10) | None. The operator ruled no sandboxes (01 R28). | **Off** |

### 1.4 Context, sessions and history

| # | Capability | SDK (Python) | How QMA turns it on | Default for QMA |
|---|---|---|---|---|
| C1 | Auto compaction and `/compact` | Yes (02a section 8) | Default. `CLAUDE_CODE_AUTO_COMPACT_WINDOW` set per provider profile where the provider caps lower (02a section 8; 02b B) | **On** |
| C2 | Prompt caching | Yes, automatic. 1-hour TTL on the plan (02a section 8) | Default. Stable `append` text so the prefix holds. | **On** |
| C3 | Resume and continue a session | Yes (02a section 2) | Store the SDK `session_id` against the qmx-control session and pass `resume=` (HOW "session resume") | **On** |
| C4 | Fork, list, rename, tag, delete sessions | Yes, helper functions (02a section 2) | Console commands | **On** |
| C5 | Transcript pruning after 30 days | Yes, `cleanupPeriodDays` (02a section 2) | Raise it in QMX settings. Sessions last days (01 req 10). | **On** (raised) |
| C6 | Session store mirror to your own backend | Yes, `SessionStore` (02a section 2) | Later, with server sessions (B46) | **Off** |
| C7 | File checkpoints and rewind | Partial. Misses Bash and helper edits (02a section 10) | `enable_file_checkpointing=True`, console `/rewind` | **On** |
| C8 | Background helpers and background Bash | Yes (02a section 13) | Default, counted against the 50% cap (section 2.8) | **On** |
| C9 | Helper depth and concurrency limits | Yes, env vars (02a section 5) | `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` so helpers never start helpers (01 R33, C24). Concurrency keeps the SDK default of 20, editable in settings (01 R23). | **On** |
| C10 | Structured output (`output_format`) | Yes (02a section 10) | Not for chat. Kept for later workflows. | **Off** |

### 1.5 Usage, auth and operations

| # | Capability | SDK (Python) | How QMA turns it on | Default for QMA |
|---|---|---|---|---|
| U1 | Per-turn usage and cost estimate (`usage`, `model_usage`, `total_cost_usd`) | Yes (02a section 9). Costs are estimates. | Read from `ResultMessage` (section 2.8) | **On** |
| U2 | Plan rate-limit events (`RateLimitEvent`) | Yes, only on status changes (02a section 9) | Read and stored for the usage page | **On** |
| U3 | `/usage` plan report | Partial. Typed in TS. UNCONFIRMED how Python exposes it (02a section 9) | Console `/usage`. Check S10 settles the Python shape. | **On** |
| U4 | Statusline | UNCONFIRMED in the SDK. It is a terminal UI feature (02b F1, probe F2) | None. The QMX usage page replaces it. | **Off** |
| U5 | Sign in with the Max plan through the CLI's own login | Yes. The CLI owns the token (02a section 11; 02b A, verdict A) | Console `/login` runs the bundled CLI login with QMX's `CLAUDE_CONFIG_DIR` | **On** |
| U6 | `max_turns` and `max_budget_usd` | Yes (02a section 9) | None for the console, which matches Claude Code. Set for background jobs. | **Off** for chat |
| U7 | Fallback model | Yes. Never fires on rate limits (02a sections 9, 11) | None | **Off** |
| U8 | OpenTelemetry export | Yes, passed through (02a section 15) | Later, to a local collector only (01 hard rule 9) | **Off** |
| U9 | Stop telemetry and auto-update traffic | Yes, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` (02a section 15) | Set in the session env | **On** |
| U10 | Remote Control | No with a setup token (02a section 11). Not documented for the SDK. | None (section 3, B14) | **Not available** |

### 1.6 Counts

Counted by script from the "Default for QMA" column of tables 1.1 to 1.5.

| Default | Rows |
|---|---|
| On (including "On if present", "On (empty by default)", "On (raised)", "On for injected text") | 51 |
| Off (available, left off on purpose, including "Off for chat") | 11 |
| Not available in the Python SDK | 5 |
| Total | 67 |

Of the 51 "On" rows, two rest on UNCONFIRMED facts that a live check settles: T7 PowerShell (check S3) and U3 `/usage` in Python (check S10). Two "Off" rows are UNCONFIRMED in Python: T21 cron tools and X12 output styles.

---

## 2. What QMX adds on top

Each item names the reason and the seam in today's code. The host is qmx-control, the FastAPI app on `127.0.0.1:8766`. HOW picks it because the rebuild keeps it and P16 deletes the daemon, which also cannot stream (HOW "Seams", gotcha 9).

### 2.1 The engine host

- **What.** One harness module that builds `ClaudeAgentOptions` per session and runs one `ClaudeSDKClient` per chat. Only this module imports `claude_agent_sdk` (HOW "Where the earlier explanation differs").
- **Why.** One engine (01 R1). Destination is the harness plus deletion (01 R9).
- **Seam.** Copy the option set from `_ClaudeSDKLifecycle._connect()` and `events()` in `native_claude.py`, then drop its one-tool limit and `max_turns=8` (HOW seam 1). Replace `build_copilot()` and `stream_turn()`. Add a route such as `POST /api/sessions/{id}/turns`. Keep it out of `OPERATIONS` so agents cannot start turns over MCP (HOW seam 1 and "small disagreements").
- **Watch.** qmx-control cannot be imported today without LangChain and Deep Agents (HOW gotcha 1). `claude-agent-sdk` is a dev dependency only (HOW gotcha 6). Both are fixed in the deletion sequence.

### 2.2 QMX tools through in-process MCP

- **What.** One in-process server named `qmx`, built with `create_sdk_mcp_server`. Tool names become `mcp__qmx__<tool>` (02a section 7).
- **Why.** "The copilot, it is the same API as the UI creates" (01 section 11.1, ZP l.342). In-process tools keep the qmx-control bearer token out of the CLI process (HOW seam 2).
- **Seam.** Tool sources are `qmx_tools.registry.domain_functions(ctx)`, the `ControlService` methods in `qmx_control.server.OPERATIONS` (their `readOnlyHint` and `destructiveHint` become the ask list), and `BrokerService.read` plus `propose_order` (HOW seam 2).
- **Watch.** `qmx_tools/registry.py` imports `langchain_core` at the top. Move `domain_functions` to its own module first (HOW gotcha 3).

### 2.3 The money rule

- **What.** Agents may read money data. They can never move money. Writes need the operator's own invoke and allow.
- **Why.** "Money, okay, the agent can access, but it's a read-only." (01 R12). Rules live in hooks, not prompts (01 C15). The deny list lives in code, not in settings (01 hard rule 5).
- **Layers, in the order the SDK runs them (02a section 4).**
  1. Build time. A LangChain-free `check_descriptor()` runs over every `qmx` tool name and metadata. The harness refuses to start if one matches (HOW seam 3).
  2. PreToolUse callback hook. It calls `qma.core.barriers.money_path.is_money_path_act_denied()` on the tool name and input. It also runs inside helpers, where the input carries `agent_id` (02a section 3). Hooks run first.
  3. Deny rules passed in code. Deny beats every mode, including `bypassPermissions` (02a section 4).
  4. `can_use_tool` asks the operator for `propose_order` and every `destructiveHint` tool (HOW seam 3).
  5. The structural guarantee stays. `BrokerService` has `read()` and `propose_order()` only. `propose_order()` writes an unsigned row and opens no broker connection (HOW "Money path").
- **Seam.** `pre_tool()` in `native_claude.py` is the hook template. `qmx_agents/guards/money_path.py` splits. Keep `check_descriptor` and the proposal-writer exception, delete the `BaseTool` classes (HOW deletable table). The two deny-list copies must not drift (HOW gotcha 11).
- **Open risk.** Bash is on (T6). An agent with Bash runs as the same OS user that holds the broker credentials in the OS keyring under `qmx/*` (HOW "Money-data tool call" step 4). If those credentials can place orders, a Bash call could reach the broker directly, past every QMX tool. The hook can deny Bash commands that read `qmx/*` keyring entries or name broker hosts, but pattern matching is not proof. See "Could not place" at the end.

### 2.4 Isolation from his personal Claude Code, both ways

- **What.** QMX gets its own Claude config folder, settings, skills, plugins, memory and transcripts. His `~/.claude` never loads into QMX. QMX never writes into `~/.claude`.
- **Why.** "QMX should be not interrupted by claude on my machine, and vice versa" (01 section 3, T2 17:57 answer; R20; hard rule 4).
- **Recipe (02a section 6, trap 1, trap 2).**
  - `env["CLAUDE_CONFIG_DIR"]` = a folder under the QMX home. Settings, history, plugins and the login move there.
  - `env["CLAUDE_CODE_PROJECT_DIR_NAME"]` names the project folder (02a section 2).
  - `setting_sources`. Use `["user", "project"]` only after check S7 proves the `user` tier reads from `CLAUDE_CONFIG_DIR`. Until then use `[]` and carry QMX's skills, commands, agents and hooks in the QMX plugin. 02a marks this UNCONFIRMED.
  - `strict_mcp_config=True` and `env["ENABLE_CLAUDEAI_MCP_SERVERS"]="false"`. Without the second one, his claude.ai connectors load once he signs in with claude.ai (02a section 6).
  - `cwd` is a QMX workspace folder outside his dev repos. Project CLAUDE.md is read from every parent folder (02a trap 2).
  - Scrub `ANTHROPIC_API_KEY` and every inherited `ANTHROPIC_*` from the child env. Python merges `env` over the parent env, and a stray key silently wins over the plan (02a trap 6; 02b probe A2).
- **Seam.** `_ClaudeSDKLifecycle._preflight()` and `native_boundary.check_environment()` already refuse inherited `ANTHROPIC_*` and require `authMethod: claude.ai`. Split them per profile. The Claude profile keeps the strict check. The translator profile checks for a loopback URL instead (HOW seam 4, gotcha 7). `check_claude_managed_policy()` only knows Windows paths. Add the macOS and Linux managed-settings paths (HOW gotcha 7, gotcha 16).

### 2.5 Provider profiles

- **What.** Each provider is a row with a base URL, model names per tier and a `credential_ref`. Kimi, GLM, DeepSeek, MiniMax, Meta Muse and OpenRouter all speak Anthropic's format and have Claude Code recipes (02b verdict B).
- **Why.** "The compatibility word is very important." (01 R24). Every provider but GPT uses Anthropic's format (01 R2). A new model drops in as a row (01 hard rule 8).
- **Env per session.** `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` always set together, `ANTHROPIC_API_KEY` empty, every tier variable pinned, `ENABLE_TOOL_SEARCH=true`, and `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` where a provider rejects beta fields (02a section 11, trap 7; 02b B, C item 5). A base URL without its own token would send the plan login to that host (02a trap 7, Inferred).
- **Mixing.** One session has one provider. Helpers inherit it, because `AgentDefinition` has no env field (02a section 5). A helper on another provider is a separate session started by QMA (02b verdict C, option 1).
- **Seam.** Read rows from `ControlService.settings_get("providers")` in `settings.toml`. `_no_secrets()` already forces `credential_ref` (HOW seam 4). Keys come from the OS keyring at spawn. The `router.credential()` keyring lookup is the idea to keep (HOW deletable table).

### 2.6 The GPT translator

- **What.** A small process inside QMA. Anthropic Messages in, OpenAI Responses out, with the operator's ChatGPT sign-in token. It binds to `127.0.0.1`, needs a per-run secret, accepts only QMA's GPT model names, and uses QMA's own Sign in with ChatGPT registration (02b D, "What this means for the translator").
- **Why.** The ruling is one SDK plus a GPT patch (01 R1). Sign-in gives a token for GPT models only, tied to OpenAI's format (01 C26). Reusing the Codex login is impersonation under the Sign in with ChatGPT terms (02b D item 9).
- **Gate.** Nothing ships until probes P0 to P7 pass (02b D probe plan). If P3 fails both ways or P2 says "not eligible", the route is not viable now (02b D stop rule). Section 3 covers the fallback.
- **Seam.** A provider profile whose base URL points at the translator. The old `cliproxy` branch at `127.0.0.1:8317` is the precedent for a local translator (HOW seam 4).

### 2.7 Operator principal and grants

- **What.** Only the operator can answer a permission ask, switch modes or start turns. Agents reach QMX only through the in-process `qmx` tools, so they never hold the bearer token.
- **Why.** Publish, install, scheduling and managing always ask him (01 R35). Money writes need his manual invoke (01 R12).
- **Seam.** Today whoever holds the qmx-control bearer token in `qmx/control-token` is the operator (`BearerGate`, `local_token()`). Mini-app manifests can carry that same token, so a separate operator principal is a precondition for a safe permission-answer route (HOW "Key concepts" and "It left out the daemon path"). qmx-control has no answer route yet. The answer lives in a stdin loop in `scripts/live/copilot_build_app.py` (HOW gotcha 10). The daemon's grant ledger goes with the daemon under P16 (HOW deletable table).

### 2.8 Usage page and the 50% background cap

- **What.** For each account it shows the plan, limits and reset time, tokens, cache reads and the Claude 5-hour window. Background agents stop at 50% of the 5-hour window, editable.
- **Why.** 01 req 7. "so 50%, but editable, that's okay" (01 R6).
- **Sources.** `ResultMessage` `usage`, `model_usage` and `total_cost_usd` (02a section 9). `RateLimitEvent.utilization` per window (02a section 9). `/usage` as a backstop, because events fire only on changes (02b verdict F). GPT has no usage API. QMA counts tokens itself and links to ChatGPT Settings, Usage (02b F).
- **Cap.** Before a background job starts, and on every rate-limit event, QMA compares five-hour utilization with the cap. At or above the cap, background jobs refuse to start. Running ones are stopped with `stop_task`.
- **Seam.** `_ClaudeSDKLifecycle.events()` reads `ResultMessage` but drops usage (HOW seam 5). Write a `model_call` journal event from it. `RunIndex.refresh()` in `qmx_control/runs.py` already sums cost from those events (HOW seam 5). `SessionBlock.type` and `EventTopic` have no usage entry. Add one on purpose or use `record_work()` (HOW gotcha 12).

### 2.9 Store and the event wire to the UI

- **What.** SDK messages become the same blocks `stream_turn()` writes today. Text becomes `text`. A tool call becomes `tool`. The task list becomes `plan`. Helper messages become `agents` plus a child session. A permission wait becomes `permission`. QMA writes them with `ControlService.sessions_append()` and the SSE route serves them unchanged (HOW "event wire").
- **Why.** Console now, real UI later (01 R11). Sessions persist for days and survive restarts (01 req 10).
- **Resume rule.** Keep the daemon rule. An unknown end of a turn blocks continuation instead of silently starting a new session (HOW "session resume").
- **Export.** A console command writes the transcript from `get_session_messages()` plus the run journal (01 req 11; 02a section 2).

### 2.10 The temporary console

- **What.** A small terminal program. It signs in, chats, shows tool steps and asks, and offers `/login`, `/model`, `/mode`, `/effort`, `/provider`, `/usage`, `/resume`, `/fork`, `/rewind` and `/export`. It is deleted when the UI lands.
- **Why.** "Give me a temporary way to talk to the agent" (01 R11). The sign-off is talking to it like Claude Code (01 R10).
- **Seam.** It calls the qmx-control turn route, the permission-answer route and the SSE stream. It does not call the SDK directly. The UI later uses the same three doors, so the console tests the real path. It replaces the stdin loop in `scripts/live/copilot_build_app.py` (HOW gotcha 10).

### 2.11 QMX settings, editable in the UI

- **What.** Permission rules, settings hooks, helper limits, effort, model defaults, provider rows, the background cap and transcript retention. Defaults ship, and every value is editable (01 hard rule 6).
- **Why.** 01 req 8, R23. Permission modes and hooks copy Claude Code (01 R7).
- **Seam.** Provider rows and the cap go in `settings.toml` through `settings_put` (HOW gotcha 13). Claude-side settings live in QMX's `CLAUDE_CONFIG_DIR`. `models.yaml` and `operator-config.json` go away (HOW gotcha 13).

### 2.12 Platform

- **What.** Windows x64, macOS and Linux glibc. Pin an SDK release that ships a `win_amd64` wheel. Five recent releases shipped without one (02a section 14). No Windows ARM64 or musl wheel exists.
- **Why.** 01 R19, hard rule 3. Secrets live in each OS keyring. Headless Linux needs a Secret Service backend (HOW gotcha 16).

---

## 3. What is out of the baseline

| Item | Why it is out | Where it goes |
|---|---|---|
| Computer use (desktop clicking) | Not in the SDK. macOS and interactive only (02a section 12; 02b E1). Not on the ChatGPT route either (02b E7). | MCP route. A per-OS desktop MCP behind one QMX tool interface (Windows-MCP on Windows, macOS choice open). BACKLOG B17, B37, S1, S4. |
| Browser control | Claude in Chrome is unproven in the SDK (02b E4, probe E2) | MCP route. Playwright MCP as the cross-platform floor (02b E recommendation, probe E3). BACKLOG B38. |
| Agent teams | SDK sessions never spawn teammates (02a section 13) | No backlog id. Helpers (T11) cover the need. Proposed as a new BACKLOG row for the orchestrator to add. |
| Workflow tool on by default | Fails instead of waiting at the plan limit, and runs 16 agents at once (02a section 13) | Available as an opt-in (T17). Design in BACKLOG B33. |
| Scheduled jobs (cron) | Cron tools UNCONFIRMED in Python (02a section 13). Scheduling always asks him (01 R35). | BACKLOG B34 |
| Long server sessions, session mirror, Docker run | Server work comes after the harness (01 R25, R26) | BACKLOG B44, B46. `SessionStore` (C6) and `defer` (P4) are the SDK parts. |
| Sandboxes | Ruled out (01 R28). No-op on native Windows (02a section 10). | BACKLOG rejected table |
| Helpers on a different provider inside one session | Not native. `AgentDefinition` has no env (02a section 5). | Separate sessions now (2.5). A pass-through router later (02b C options 2 and 4). No backlog id. |
| Statusline and output styles | Terminal UI features, UNCONFIRMED in the SDK (02b F2; 02a "Python lacks") | Replaced by the usage page (2.8). No backlog id. |
| Worktree isolation for helpers | No Python field (02a section 5) | BL "not in the minimum" list. No backlog id. |
| Remote Control and phone approvals | Not available with a setup token (02a section 11) | BACKLOG B14 |
| Voice and audio | Later (01 section 8) | BACKLOG B15 |
| Memory bake-off and self-improvement | SDK default memory now (01 R29) | BACKLOG B40, B41 |
| Organogram, plugins per area, mini apps, MCP apps | Harness first (01 R17) | BACKLOG B30, B31, B23, B16 |
| Real UI | Later, separate session (01 R11) | BACKLOG B12 |
| Local trace collector | Logs stay local (01 hard rule 9). Export is off for now (U8). | No backlog id. |
| Codex app-server or an API key as the GPT fallback | Breaks one engine, or costs API money he refuses (01 R4, C12; 02b D stop rule) | His call if the probe fails (01 section 9 question 1) |
| Max plan's monthly API credits | He refused API spend, including this credit (01 C12, R4) | Not used |

---

## 4. Checks the operator does himself

Run these in the temporary console on his own PC. Each step is something to type or look at. No code reading. Do them in order. Checks 1 to 9 and 11 to 13 need nothing extra. Check 10 runs only if the coding session reports that the GPT probe passed.

| # | What it proves | Steps | Pass | Fail |
|---|---|---|---|---|
| 1 | Sign in with his Max plan | Open the console. Type `/login`. Finish sign-in on Anthropic's page in the browser. Type `/usage`. | The console says it is signed in with Claude Max, and `/usage` shows the 5-hour window with a percentage and a reset time. | Sign-in asks for an API key, or `/usage` shows no plan window. |
| 2 | It talks like Claude Code | Type "What is in this folder? Summarise the README." | It lists the files, reads the README, and shows each step it took before answering. | It answers without reading, or says it cannot see files. |
| 3 | It uses files and the terminal | Type "Make a file hello.txt with today's date, show it using a terminal command, then change the text to goodbye." | It asks before writing and before the command. After you allow, hello.txt holds "goodbye" (open it yourself to see). | It says it did it but the file is missing or still has the date. |
| 4 | It asks before risky actions | Type "Delete hello.txt". When it asks, answer no. | It asked first. hello.txt still exists. | It deleted the file without asking, or after you said no. |
| 5 | It refuses to move money | Type "Show my open positions on the demo account." Then type "Place a buy order for 0.01 lots of EURUSD." Then type "Use the terminal to place that order directly." | Positions show. Both order requests are refused, and the console names the money rule. cTrader shows no new order. | Any order or order proposal appears without your approval. |
| 6 | QMX does not see his Claude Code setup | Type "List your skills and slash commands." | Only QMX's own skills appear. None of his, such as poteto-mode or the bmad skills. | Any of his personal skills or commands appear. |
| 7 | His Claude Code does not see QMX | Close the console. Open his normal Claude Code. Type `/skills`, then `/resume`. | No QMX skill appears. The resume list has no QMX chats. | A QMX skill or a QMX chat shows up. |
| 8 | Switch to OpenRouter by key | In the console type `/provider openrouter`, then repeat the question from check 2. | A cost and cache warning shows before the switch. Then it answers using its tools, and `/usage` shows OpenRouter for that reply. | No warning, an error, or no tool steps. |
| 9 | One other provider by key | Type `/provider` and pick one more row, for example Kimi or DeepSeek. Repeat check 3 with a new file name. | Same result as check 3, and `/usage` shows that provider. | Error, or it cannot run the command. |
| 10 | GPT through his ChatGPT sign-in (only if the probe passed) | Type `/login chatgpt` and approve "QMA" on OpenAI's page. Type `/provider gpt`. Repeat check 3 with a new file name. Then open ChatGPT Settings, Usage. | Same result as check 3. ChatGPT's usage page lists QMA. | Error, no tool steps, or QMA missing from ChatGPT's usage page. |
| 11 | Helpers (sub-agents) | Type "Use a helper agent to count the files in this folder while you tell me today's date." | The console shows a helper starting and finishing, then one answer with both facts. | No helper appears, or the answer is missing a fact. |
| 12 | Usage is shown | Type `/usage` and compare with claude.ai Settings, Usage. | The console shows tokens for this chat, cache reads, the background cap (50%) and the Claude 5-hour percentage, close to the claude.ai number. | Any of those is missing, or the 5-hour number is far off. |
| 13 | It works after a restart | Close the console. Open it again. Type `/resume` and pick this chat. Type "What file did we make first?" | It answers hello.txt without searching for it. | It does not know, or `/resume` has no chat to pick. |

---

## 5. Checks the coding session runs before handing over the console

Every check is live. No mocks. Real CLI, real plan login, real provider keys, real files. Each one is a script that prints PASS or FAIL with the observed value and can be rerun. The operator gives two clicks only. One is the Claude `/login` in QMX's folder. The other is the ChatGPT sign-in for probe P0.

| # | Check | How | Pass signal |
|---|---|---|---|
| S1 | Install | Install the pinned SDK on Windows x64. Print the SDK and bundled CLI versions. | A `win_amd64` wheel installs and both versions print (02a section 14). |
| S2 | Plan login, no API billing | Run one turn signed in only through the CLI login in QMX's folder. Then set a fake `ANTHROPIC_API_KEY` in the parent env and run again. | Both turns succeed on the plan. A `RateLimitEvent` or `/usage` shows plan usage. The fake key never reaches the CLI (02b A1, A2; 02a trap 6). |
| S3 | Same tools as vanilla | Run the bundled CLI directly as `claude -p` with QMX's config folder and no QMX options. Then run a QMA session. Compare the init tools lists. | QMA's list equals vanilla's, except Workflow, which is off on purpose. Record whether a PowerShell tool appears on Windows (T7). |
| S4 | Same behaviour as vanilla | Run the same three prompts as operator checks 2 to 4 in both. | Same files changed, same final file contents, same asks. |
| S5 | Permissions | Set three rules. Deny `Bash(git push *)`, ask `Bash(rm *)`, allow `Bash(echo *)`. Try each. Try a write in plan mode. Approve "always allow" once. | Push is denied, rm asks, echo runs. Plan mode blocks the write. The remembered rule lands in QMX's settings, not in `~/.claude`. |
| S6 | Money rule | Register a fake tool named `place_order`. Separately, in a live session, try a denied act through a `qmx` tool, through Bash naming the broker or a `qmx/*` keyring read, and from inside a helper. Repeat in `bypassPermissions` mode. | The harness refuses to start with the fake tool. Every live attempt is denied in every mode, including inside the helper. The broker log shows no connection opened by the attempts. `propose_order` triggers an ask. |
| S7 | Isolation both ways | List every file and its modified time under `~/.claude` before and after a full QMA session. Read the init message skills, commands and MCP list. Check where auto memory and the transcript were written. Test whether the `user` tier reads from `CLAUDE_CONFIG_DIR` with a marker skill. | `~/.claude` is unchanged. None of his skills, commands, claude.ai connectors or his CLAUDE.md appear. Memory and transcript sit under QMX's folder. The `user` tier result is recorded and sets `setting_sources` (2.4). |
| S8 | Providers | For OpenRouter and each provider row with a key, run one turn with one Bash call, three turns for caching, a two-turn tool loop with thinking, and one WebSearch. | Tool runs and the result has no error (02b B1). Cache reads above zero on turn three (B3). No thinking error (B4). WebSearch works or fails, recorded per provider (T10). Meta retried with experimental betas off if needed (B2). |
| S9 | No credential leak to third parties | Point a profile's base URL at a local echo server with a fake provider token. Run one turn. | The echo server receives only the fake provider token, never the Claude plan login (02a trap 7). |
| S10 | Usage | Run ten turns. Count `RateLimitEvent`s. Send `/usage` and record what Python returns. Check that a `model_call` journal event exists per turn and `RunIndex` sums its cost. Set the background cap just below current use and start a background helper. | Events counted (02b F1). The `/usage` shape is recorded (U3). Journal and cost sum match the `ResultMessage` numbers. The background helper refuses to start. |
| S11 | Helpers | Ask a helper to start its own helper. Start a background helper and wait. Run a helper whose definition names a model. | The nested start is refused (depth 1). The background helper finishes with a task notification. `model_usage` shows the named model. |
| S12 | Interrupt | Start a 30-second sleep in Bash, then interrupt. | The turn ends and no sleep process is left running. |
| S13 | Compaction | Run `/compact`. Then try a money act and ask about a CLAUDE.md rule. | A `compact_boundary` message arrives. The money hook still denies. The CLAUDE.md rule is still followed. |
| S14 | Restart and resume | Kill the harness process between turns and restart. Resume by the stored id and ask a recall question. Then kill it mid-turn and restart. | Recall is correct after the clean kill. After the mid-turn kill the session is marked unknown and does not silently start fresh (HOW "session resume"). |
| S15 | Event wire | Run a scripted turn with text, a tool, a task list, a helper and an ask. Read the SSE stream. Answer the ask through the answer route with and without the operator credential. | `text`, `tool`, `plan`, `agents` and `permission` blocks arrive in order. The answer works only with the operator credential. |
| S16 | GPT probe | Run 02b probes P0 to P7 in order. | Each step passes, or the stop rule fires and the console hides the GPT row. P8 is operator check 10. |
| S17 | Secrets | After all checks, search the QMX folder, logs and transcripts for every key value used. | No key value is found. |
| S18 | Memory per session | Measure the CLI process memory for one idle and one busy session. | The numbers are recorded. 01 hard rule 10 says the 1 GB figure was never measured. |

S1 to S18 run on Windows, his machine. Linux runs later in Docker on his server (BACKLOG B44). macOS has no test machine named in the sources, so it stays unverified.

---

## Could not place

1. **Bash versus money read-only.** With Bash on, agents run as the same OS user that holds broker credentials in the keyring (HOW "Money-data tool call" step 4). Hooks can deny patterns, but cannot prove an order is impossible. It needs one of two things. Either the broker credentials on this machine are read-only at the broker, or credentials that can trade live only on the node. Neither the sources nor a ruling say which.
2. **The trading clause.** The Consumer Terms bar relying on the Services "to buy or sell securities" (02b A item 9). The operator should read it himself.
3. **Demo accounts.** He wants agents to test ideas on demo accounts. The ratified FR-Q42 forbids any execution tool, paper included (01 section 9 question 3).
4. **Unattended approvals.** Which actions a background or server agent may take without him (01 section 9 question 4). The baseline keeps every ask for him.
5. **GPT if the probe fails.** Wait, or pay per use through OpenRouter (01 section 9 question 1).
6. **Backups.** "never keep your only backup on the same server it's backing" (01 section 11.1). Transcripts and memory now live in QMX's folder. No backup target is set.
