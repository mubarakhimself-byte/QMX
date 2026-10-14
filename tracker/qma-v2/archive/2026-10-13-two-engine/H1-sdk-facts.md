# H1 — SDK facts the harness plan depends on (primary sources, 2026-10-13)

Status: research, not ratified. Checks `BASELINE.md` (2026-10-13) fact by fact.

How this was read:
- **Browser** = the built-in browser, live page, read on 2026-10-13. This is the default for every row.
- **Raw** = a GitHub raw file opened in the built-in browser (source code or notebook JSON).
- **Exa** = the Exa page fetcher. Used only for Meta pages, because `*.meta.ai` and `ai.developer.meta.com`
  refused the browser, WebFetch (ECONNREFUSED) and Firecrawl ("site not supported").
- Doc sites show no page dates except where noted. "Read 2026-10-13" means the live version on that day.
- Short-hands: `cc:` = `https://code.claude.com/docs/en/`, `oa:` = `https://openai.github.io/openai-agents-python/`,
  `siwc:` = `https://developers.openai.com/siwc/`, `meta:` = `https://dev.meta.ai/docs/`.

---

## 1. What changed versus BASELINE.md (one screen)

1. **Claude credentials: stricter than BASELINE says.** The legal page now also says developers "may not collect,
   store, or intermediate Claude.ai credentials or session tokens". Sign-in "must complete through Anthropic's own flow".
   So QMX must **not** keep a Claude `setup-token` in its SecretStore and inject it. Safe route: the operator runs
   `/login` himself inside the Claude engine's own `CLAUDE_CONFIG_DIR`. QMX never touches the token. (Fact 4.)
2. **Python SDK hooks are a subset.** As in-code callbacks, Python has PreToolUse, PostToolUse, PostToolUseFailure,
   UserPromptSubmit, Stop, SubagentStart/Stop, PreCompact, PermissionRequest and Notification only. SessionStart,
   SessionEnd, PostCompact, Pre/PostModelSwitch, StopFailure, PermissionDenied and PostToolBatch are TypeScript-only
   callbacks. In Python they run only as shell hooks from settings files. (Fact 2.)
3. **Default permission mode can be `auto`** when the app sets none. QMX must always pass `default` (or its chosen
   mode) explicitly. (Fact 1.)
4. **`can_use_tool` needs streaming input plus a dummy PreToolUse hook** in Python ("Required workaround"). (Fact 1.)
5. **`setting_sources=[]` is not full isolation.** `~/.claude.json`, auto memory, claude.ai connectors and managed
   settings still load. Isolation needs `CLAUDE_CONFIG_DIR` plus env flags. (Fact 3.)
6. **Computer use is not available through the Claude Agent SDK.** The CLI feature is macOS-only, interactive-only and
   not in `-p` mode. The API toolset (`computer_toolset_20260801`) needs an API key and QMX-built execution. (Fact 8.)
7. **Sign in with ChatGPT is real and fits QMX.** OpenAI says plan usage is available to "personal projects that run
   locally". The legitimate route is OAuth to `https://api.openai.com/v1/responses`, or Codex app-server with that
   token. Do **not** use `chatgpt.com/backend-api/codex` (BASELINE open item 1); OpenAI says not to. (Fact 17.)
8. **The ChatGPT-plan route has hard limits:** `store:false`, `stream:true`, no `previous_response_id`, no
   `prompt_cache_retention`, no `truncation`, no hosted tools, no native computer use, no `tool_search`, and function
   tools must be grouped in namespaces. (Fact 17.)
9. **OpenAI Agents SDK default `max_turns` is 10** (BASELINE open item 4, now settled). Too low for coding work.
10. **No compaction exists for non-OpenAI models in the OpenAI SDK.** BASELINE's local-compactor plan stands. (Fact 13.)
11. **Meta Muse is real.** Meta Model API serves `muse-spark-1.x` over OpenAI Responses, Chat Completions **and**
    Anthropic Messages. It is on OpenRouter and OpenCode. (Fact 19.)
12. **Claude rate-limit events come only on status change.** A usage page must cache the last event per window. (Fact 10.)

---

## 2. The 21 facts

Verdicts: **VERIFIED** (BASELINE or earlier research matches the source), **CORRECTED** (source differs; new answer
given), **NEW** (not in BASELINE, settled here), **UNVERIFIED** (no primary source found).

### Claude Agent SDK (Python)

| # | Fact | Verdict | Answer (≤3 lines) | Source | Read via |
|---|---|---|---|---|---|
| 1 | Permission modes, `can_use_tool`, rules | VERIFIED + CORRECTED | Modes: `default`, `dontAsk`, `acceptEdits`, `bypassPermissions`, `plan`, `auto`. Order: hooks, deny, ask, mode, allow, `can_use_tool`. Callback returns `PermissionResultAllow(updated_input=…)` or `PermissionResultDeny(message=…)`. Rules come from code (`allowed_tools`/`disallowed_tools`) and from settings.json (needs `"project"` in `setting_sources`). **New:** unset mode can start as `auto`; Python callback needs streaming input + dummy PreToolUse hook. | `cc:agent-sdk/permissions`; `cc:agent-sdk/user-input` ("Required workaround"); `cc:agent-sdk/python` (`CanUseTool`) | Browser |
| 2 | Hooks | CORRECTED | In-code callbacks (Python): PreToolUse (block, `updatedInput`, allow/deny/ask/defer), PostToolUse (`additionalContext`, `updatedToolOutput`), PostToolUseFailure, UserPromptSubmit, Stop, SubagentStart/Stop, PreCompact, PermissionRequest, Notification. Others are TS-only; in Python only as settings-file shell hooks. Deny beats defer beats ask beats allow. | `cc:agent-sdk/hooks` (table "Available hooks"); `cc:agent-sdk/claude-code-features` ("Hooks") | Browser |
| 3 | Isolation from personal Claude Code | CORRECTED | Omitting `setting_sources` = `["user","project","local"]`. `[]` drops those, but `~/.claude.json`, auto memory, claude.ai connectors, managed policy still load. Recipe: `env={CLAUDE_CONFIG_DIR: <qmx dir>, CLAUDE_CODE_DISABLE_AUTO_MEMORY: "1" (or keep, in that dir), ENABLE_CLAUDEAI_MCP_SERVERS: "false"}`, `setting_sources=[]` or `["project"]`, explicit `plugins=[…]`, `skills=[…]`. Whether `"user"` follows `CLAUDE_CONFIG_DIR`: UNVERIFIED. | `cc:agent-sdk/claude-code-features` ("What settingSources does not control"); `cc:authentication` ("multiple accounts") | Browser |
| 4 | Auth on Max, terms | CORRECTED | `claude setup-token` mints a one-year token for `CLAUDE_CODE_OAUTH_TOKEN` (Pro/Max/Team/Ent; model requests only; "Bare mode does not read" it). Terms: "Anthropic does not permit third-party developers to offer Claude.ai login into their own applications" and developers "may not collect, store, or intermediate Claude.ai credentials or session tokens". Allowed: a user signing in "to the unmodified Claude Code binary with their own Claude subscription"; limits "assume ordinary, individual usage of Claude Code and the Agent SDK". Overview: no claude.ai login or rate limits for third-party products "Unless previously approved". | `cc:legal-and-compliance`; `cc:agent-sdk/overview`; `cc:authentication`; Consumer Terms (effective 2025-10-08): no "automated or non-human means" except via API key "or where we otherwise explicitly permit it" | Browser |
| 5 | Sessions | VERIFIED | `continue_conversation=True` (most recent in cwd, survives restart), `resume=<id>`, `fork_session=True`. Transcripts: `~/.claude/projects/<encoded-cwd>/*.jsonl`, or under `$CLAUDE_CONFIG_DIR/projects/`. Export: `list_sessions()`, `get_session_messages()`, `rename_session`, `tag_session`, `delete_session`; `session_store=` mirrors to your own backend. Resume is same-machine unless mirrored. | `cc:agent-sdk/sessions`; `cc:agent-sdk/python` (`list_sessions`, `get_session_messages`); cookbook `05_Building_a_session_browser` | Browser + Raw |
| 6 | Compaction, caching, effort, model switch | VERIFIED | Auto compaction emits `SystemMessage` subtype `compact_boundary`; manual = send `/compact` as prompt; PreCompact sees `trigger`. `effort` = low/medium/high/xhigh/max; `thinking` = adaptive/enabled/disabled. Mid-session `ClaudeSDKClient.set_model()`; each model has its own cache, so a switch recomputes the whole request. Effort change keeps cache on Opus/Sonnet/Haiku 5.5 and Fable 5.1. No `set_effort` method in the Python client (UNVERIFIED how to change effort mid-session). | `cc:agent-sdk/agent-loop`; `cc:prompt-caching` ("Switching models", "Changing effort level"); `cc:agent-sdk/python` (client methods) | Browser |
| 7 | Sub-agents, skills, commands, MCP, memory | VERIFIED + NEW | `agents={name: AgentDefinition(description, prompt, tools, disallowedTools, model, skills, mcpServers, maxTurns, background, effort, permissionMode…)}`. Skills: filesystem only (`.claude/skills/<name>/SKILL.md`), "no programmatic API for registering skills"; `skills="all"`/list/`[]`. Plugins load by local path only. Custom tools: `@tool` + `create_sdk_mcp_server` (in-process). Commands: send `/name` as prompt. Memory: auto memory at `~/.claude/projects/<project>/memory/`, loaded regardless of `setting_sources`. | `cc:agent-sdk/python` (`AgentDefinition`, `@tool`); `cc:agent-sdk/claude-code-features`; `cc:agent-sdk/plugins` | Browser |
| 8 | Computer use | CORRECTED | Not through the Agent SDK. CLI computer use is "a research preview on macOS", needs Pro/Max, "not available in non-interactive mode with the -p flag", Windows only in the Desktop app. API path: `{"type":"computer_toolset_20260801"}` (17 member tools, your app executes them) on the Claude API with an **API key**. Subscription path for QMX: build QMX's own screenshot/click tools as SDK MCP tools (UNVERIFIED quality). | `cc:computer-use`; `https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool` | Browser |
| 9 | Process model, memory, OS | VERIFIED + NEW | "the SDK spawns a separate claude CLI process and talks to it over stdio"; one session = one subprocess. Bundled native binary, pinned to SDK version. Starting point "1 GiB RAM, 5 GiB disk, and 1 CPU per agent", grows with session length. Python 3.10+. OS: macOS 13+, Windows 10 1809+, Ubuntu 20.04+, Debian 10+, Alpine 3.19+; ARM64 Windows pip gets no bundled binary. | `cc:agent-sdk/hosting`; `cc:agent-sdk/quickstart`; `cc:setup` | Browser |
| 10 | Usage and rate limits | VERIFIED + NEW | `RateLimitEvent.rate_limit_info`: `status` (allowed / allowed_warning / rejected), `rate_limit_type` (five_hour, seven_day, seven_day_opus, seven_day_sonnet, overage), `utilization`, `resets_at`. "Emitted when rate limit status changes", so cache the last one. `ResultMessage`: `usage` (main loop only), `model_usage` (whole tree incl. compaction), `total_cost_usd`. `get_context_usage()` = `/context` data. | `cc:agent-sdk/python` (`RateLimitEvent`, `RateLimitInfo`, `ResultMessage`) | Browser |

### OpenAI Agents SDK (Python)

| # | Fact | Verdict | Answer (≤3 lines) | Source | Read via |
|---|---|---|---|---|---|
| 11 | Sessions, long runs, RunState | VERIFIED + NEW | `SQLiteSession(id)` and other backends; `OpenAIResponsesCompactionSession` wraps one. Paused run: `result.to_state()` → `state.to_string()`/`to_json()` → `RunState.from_json(agent, data)` → `Runner.run(agent, state)`, works across processes. Durable runs: Dapr, Temporal, Restate, DBOS integrations. **Default `max_turns` = 10** (`DEFAULT_MAX_TURNS = 10`, `run_config.py:45`); `None` disables. | `oa:sessions/`; `oa:human_in_the_loop/`; `oa:running_agents/`; Raw `src/agents/run_config.py` (main, 2026-10-13) | Browser + Raw |
| 12 | Approvals, guardrails, hooks: can any block? | VERIFIED | Blocks: `needs_approval` on function tools, `Agent.as_tool`, `ShellTool`, `ApplyPatchTool` (Shell/ApplyPatch default False; `on_approval` decides in code); MCP `require_approval`. Tool input guardrails block function tools and local MCP tools only, not ComputerTool/ShellTool/ApplyPatchTool/LocalShellTool/hosted tools. `RunHooks`/`AgentHooks` only observe. ComputerTool: only `on_safety_check`. `always_approve` sticks for the rest of the run only. | `oa:human_in_the_loop/`; `oa:guardrails/` ("Tool guardrails"); `oa:agents/` ("Lifecycle events") | Browser |
| 13 | Compaction | VERIFIED | Two OpenAI-only options: `OpenAIResponsesCompactionSession` (calls `responses.compact` between turns; `run_compaction()` manual) and `ModelSettings(context_management=[{"type":"compaction","compact_threshold":N}])` (server-side). Nothing for Chat Completions or other providers; only trimming hooks (`session_input_callback`, `call_model_input_filter`, ToolOutputTrimmer). On the ChatGPT-plan route: `previous_response_id` and `truncation` unsupported; whether compaction works there is UNVERIFIED. | `oa:sessions/` ("OpenAI Responses compaction sessions"); `oa:models/`; clone `docs/models/index.md:417-476`; `siwc:token-sharing-open-source/preview-limitations` | Browser + clone |
| 14 | Non-OpenAI models, OpenRouter | VERIFIED | Built-in: `set_default_openai_client`, `ModelProvider`, `Agent.model=OpenAIChatCompletionsModel(model, openai_client=AsyncOpenAI(base_url, api_key))`. Adapters "best-effort, beta": LiteLLM, Any-LLM. Streamed usage may need `ModelSettings(include_usage=True)`. OpenRouter: plain OpenAI-compatible base `https://openrouter.ai/api/v1`; tools listed per model in `/api/v1/models` `supported_parameters`; caching passes through (implicit for OpenAI/DeepSeek/Gemini, `cache_control` for Anthropic) with sticky routing, `prompt_tokens_details.cached_tokens` in usage. | `oa:models/` ("Non-OpenAI models", "Third-party adapters"); `https://openrouter.ai/docs/guides/best-practices/prompt-caching`; `https://openrouter.ai/api/v1/models` | Browser |
| 15 | Tracing off / local | VERIFIED | On by default, exports to OpenAI. Off: `OPENAI_AGENTS_DISABLE_TRACING=1`, `set_tracing_disabled(True)`, or `RunConfig.tracing_disabled`. Local only: `set_trace_processors([...])` replaces the OpenAI exporter; `add_trace_processor()` adds beside it (still sends). `trace_include_sensitive_data=False` drops inputs/outputs. | `oa:tracing/` | Browser |
| 16 | Computer use, shell, apply_patch, hosted | VERIFIED + NEW | `ComputerTool` needs your `Computer`/`AsyncComputer`; runs on OpenAI Responses only. Default SDK model `gpt-5.6-luna` supports it; GA tool `{"type":"computer"}` on `gpt-5.6` (Sol), Terra, Luna; `computer-use-preview` is legacy. `ShellTool` (local or hosted container), `ApplyPatchTool` (your `ApplyPatchEditor`). Hosted tools (web/file search, code interpreter, hosted MCP, image gen, tool search) are Responses-only. Not available on the ChatGPT-plan route. | `oa:tools/` ("ComputerTool and the Responses computer tool", "Local runtime tools"); `siwc:token-sharing-open-source/preview-limitations` | Browser |
| 17 | Sign in with ChatGPT | NEW (replaces BASELINE open item 1) | Real (launch Sept 2026). Plan usage "is available to open-source projects, personal projects that run locally, and selected private apps"; paid or remotely hosted apps must join a waitlist. Flow: dynamic client registration (`client_id=dynamic_agent_client`, no secret), PKCE, scopes `offline_access resource.invoke chatgpt.tokens.use.direct`, then Bearer token to `https://api.openai.com/v1/responses` with `store:false`, `stream:true`. "do not point it at ChatGPT's backend-api endpoints". Codex app-server: `-c model_providers.<x>.env_key="ACCESS_TOKEN"` + `wire_api="responses"`. Agents SDK with this token: UNVERIFIED (no page says so; plausible with `AsyncOpenAI(api_key=token)`, `ModelSettings(store=False)`, `run_streamed`, `tool_namespace`). QMX stores and refreshes the token itself (allowed). | `https://developers.openai.com/cookbook/articles/sign-in-with-chatgpt` (2026-09-28, "Usage policy and terms"); `siwc:token-sharing-open-source`, `/sign-in`, `/models-and-inference`, `/codex-app-server`, `/preview-limitations`; Help Center 20001542 ("Updated: 6 days ago") | Browser |
| 18 | Sub-agents, MCP, skills | VERIFIED | Agents-as-tools (`Agent.as_tool(..., needs_approval=…)`, nested approvals surface on the outer run) and handoffs. MCP: stdio, SSE, streamable HTTP, hosted MCP, per-server `require_approval` and tool guardrails. Skills: sandbox `Skills` capability or `ShellTool(environment={"type":"local","skills":[...]})`. Experimental `codex_tool` wraps the Codex CLI. Also new: experimental "hosted multi-agent" Responses model. | `oa:human_in_the_loop/`; `oa:tools/` ("Experimental: Codex tool"); `oa:models/` ("Hosted multi-agent"); `oa:guardrails/` | Browser |

### Providers

| # | Fact | Verdict | Answer (≤3 lines) | Source | Read via |
|---|---|---|---|---|---|
| 19 | Meta Muse | NEW | Meta Model API, public preview since 2026-07-09. Base `https://api.meta.ai/v1` for Responses and Chat Completions; Anthropic Messages at `https://api.meta.ai` (`/v1/messages`, stateless). Models `muse-spark-1.1/1.2/1.3`, `-contributor` variants (train on your data), `muse-image-1.0`, open-weight `muse-glimmer`; 1,048,576-token context. Pay-as-you-go standard: $1.25 in / $4.25 out / $0.15 cached per 1M; contributor $0.10/$0.20/$0.002. Muse Code subscriptions ("10-50 prompts every 5 hours" up to 80x) work "only through the Muse Code CLI". On OpenRouter (`meta/muse-spark-1.1…1.3`, `meta/muse-wonder` added 2026-10-12, tools + reasoning_effort) and OpenCode Console (`muse-spark-1.2/1.3`, Responses) and Go (contributor variants, "limited regions"). Docs pages disagree on which ids are standard tier (pricing page lists 1.1/1.2, overview adds 1.3). Region limits: UNVERIFIED. | `meta:overview`, `meta:quickstart`, `meta:pricing-rate-limits.md`, `meta:muse-code/subscriptions.md`, `meta:protocols/messages.md`; `https://ai.meta.com/blog/introducing-muse-spark-meta-model-api/` (2026-07-09); `https://openrouter.ai/api/v1/models`; `https://opencode.ai/v2/docs/console/models/`, `/console/go/` | Exa (Meta); Browser (OpenRouter, OpenCode) |
| 20 | OpenRouter Anthropic endpoint, usage API | VERIFIED | Anthropic-compatible "Anthropic Skin" at `ANTHROPIC_BASE_URL=https://openrouter.ai/api` with `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_API_KEY=""`; "only guaranteed to work with the Anthropic first-party provider". Usage page: `GET https://openrouter.ai/api/v1/key` returns `limit`, `limit_remaining`, `usage`, `usage_daily/weekly/monthly`, `budgets[]` with `resets_at`. Rate limits: `X-RateLimit-*` headers on 429. | `https://openrouter.ai/docs/cookbook/coding-agents/claude-code-integration`; `https://openrouter.ai/docs/api_reference/limits` | Browser |
| 21 | Cookbooks | VERIFIED | See section 3. 13 opened in the browser (raw notebook JSON); function names below. | section 3 | Raw |

---

## 3. Cookbooks (fact 21)

Anthropic: `github.com/anthropics/claude-cookbooks` (clone commit `9c1e493`, 2026-10-10).
OpenAI: `github.com/openai/openai-cookbook` (clone commit `5bd6cb4`, 2026-10-09), also served at `developers.openai.com/cookbook`.
"Opened" = read in the built-in browser on 2026-10-13 via raw GitHub.

| Area | Notebook | Pattern it shows (function names) | Opened |
|---|---|---|---|
| SDK migration | [claude_agent_sdk/04_migrating_from_openai_agents_sdk](https://github.com/anthropics/claude-cookbooks/blob/main/claude_agent_sdk/04_migrating_from_openai_agents_sdk.ipynb) | `@function_tool` → `@tool` + `create_sdk_mcp_server`; `Agent` → `ClaudeAgentOptions`; guardrails → `HookMatcher` (UserPromptSubmit); `Runner.run` → `ClaudeSDKClient`; sessions → `resume=`; handoffs → `AgentDefinition` | yes |
| SDK migration | [examples/agents_sdk/migrate-from-claude-agent-sdk](https://github.com/openai/openai-cookbook/blob/main/examples/agents_sdk/migrate-from-claude-agent-sdk/README.md) | the reverse map: PreToolUse → `input_guardrail`/`needs_approval`; subagents → `as_tool` or `handoffs`; built-ins → `ShellTool`/`ApplyPatchTool`/`SandboxAgent`; approvals via `interruptions`, `to_state`, `RunState` | yes |
| Sessions | [claude_agent_sdk/05_Building_a_session_browser](https://github.com/anthropics/claude-cookbooks/blob/main/claude_agent_sdk/05_Building_a_session_browser.ipynb) | `list_sessions`, `get_session_messages`, `rename_session`, `tag_session`, `fork_session`, `resume`, `delete_session` | yes |
| Permissions, hooks, plan, sub-agents | [claude_agent_sdk/01_The_chief_of_staff_agent](https://github.com/anthropics/claude-cookbooks/blob/main/claude_agent_sdk/01_The_chief_of_staff_agent.ipynb) | CLAUDE.md via `setting_sources`, `permission_mode="plan"`, output styles, slash commands, settings-file hooks, sub-agents | yes |
| Long-running / hosting | [claude_agent_sdk/07_Hosting_the_agent](https://github.com/anthropics/claude-cookbooks/blob/main/claude_agent_sdk/07_Hosting_the_agent.ipynb) | ephemeral vs hybrid vs Modal vs Kubernetes tiers; liveness, persistence beyond a volume, wire format (code lives in `hosting/`) | yes |
| Compaction | [tool_use/automatic-context-compaction](https://github.com/anthropics/claude-cookbooks/blob/main/tool_use/automatic-context-compaction.ipynb) | Messages API `beta.messages.tool_runner(..., compaction_control={...})`, threshold, summary model, custom summary prompt | yes |
| Caching | [misc/prompt_caching](https://github.com/anthropics/claude-cookbooks/blob/main/misc/prompt_caching.ipynb) | automatic caching vs explicit `cache_control: {"type":"ephemeral"}`; read `cache_read_input_tokens`, `cache_creation_input_tokens` | yes |
| Observability / usage | [observability/usage_cost_api](https://github.com/anthropics/claude-cookbooks/blob/main/observability/usage_cost_api.ipynb) | Admin API usage and cost reports (API-key orgs only; does not cover Max plans) | yes |
| Compaction + memory | [agents_sdk/building_reliable_agents_memory_compaction](https://github.com/openai/openai-cookbook/blob/main/examples/agents_sdk/building_reliable_agents_memory_compaction.ipynb) | `SandboxAgent` with `Compaction` and `Memory` capabilities; `OpenAIResponsesCompactionSession` over `SQLiteSession`; `run_compaction` | yes |
| Context trimming / summary (any model) | [agents_sdk/session_memory](https://github.com/openai/openai-cookbook/blob/main/examples/agents_sdk/session_memory.ipynb) | custom `SessionABC`: `TrimmingSession` (`max_turns`) and `SummarizingSession` (`context_limit`, `keep_last_n_turns`, `LLMSummarizer`) — the closest model for QMX's local compactor | yes |
| Computer use | [agents_sdk/computer_use_with_daytona](https://github.com/openai/openai-cookbook/blob/main/examples/agents_sdk/computer_use_with_daytona/computer_use_with_daytona.ipynb) | `ComputerTool(DaytonaAsyncComputer)` implementing `AsyncComputer`; model `gpt-5.4`; recording | yes |
| Caching | [Prompt_Caching_201](https://github.com/openai/openai-cookbook/blob/main/examples/Prompt_Caching_201.ipynb) | `cached_tokens`, stable prefix, identical tools, `prompt_cache_key`, `prompt_cache_retention` (`in_memory`/`24h`), compaction vs cache | yes |
| Sub-agents | [agents_sdk/parallel_agents](https://github.com/openai/openai-cookbook/blob/main/examples/agents_sdk/parallel_agents.ipynb) | `asyncio.gather` over `Runner.run` vs `as_tool` with `parallel_tool_calls` | yes |
| Compaction (session) | [misc/session_memory_compaction](https://github.com/anthropics/claude-cookbooks/blob/main/misc/session_memory_compaction.ipynb) | session memory plus compaction on the Messages API | no (listed from clone) |
| Approvals | [managed_agents/CMA_gate_human_in_the_loop](https://github.com/anthropics/claude-cookbooks/blob/main/managed_agents/CMA_gate_human_in_the_loop.ipynb) | approval gate, but on Managed Agents (not the SDK) | no |
| Observability | [claude_agent_sdk/02_The_observability_agent](https://github.com/anthropics/claude-cookbooks/blob/main/claude_agent_sdk/02_The_observability_agent.ipynb) | SDK agent with MCP servers for monitoring | no |
| Dynamic workflows | [claude_agent_sdk/08_Dynamic_workflows](https://github.com/anthropics/claude-cookbooks/blob/main/claude_agent_sdk/08_Dynamic_workflows.ipynb) | multi-agent workflow scripts | no |
| Codex as a tool | [codex/codex_mcp_agents_sdk](https://github.com/openai/openai-cookbook/tree/main/examples/codex/codex_mcp_agents_sdk) | Codex CLI as an MCP server inside an Agents SDK run | no |
| Evals / tracing | [agents_sdk/evaluate_agents](https://github.com/openai/openai-cookbook/blob/main/examples/agents_sdk/evaluate_agents.ipynb) | trace export to a third-party backend for evals | no |
| Sign in with ChatGPT | [cookbook/articles/sign-in-with-chatgpt](https://developers.openai.com/cookbook/articles/sign-in-with-chatgpt) | full OSS desktop integration ("Paste Perfect"): host id, PKCE, token storage, usage UI | yes (Browser) |

Not found: an Anthropic cookbook for Agent SDK `can_use_tool` approvals as a UI flow (the docs page
`cc:agent-sdk/user-input` is the reference), and an OpenAI cookbook on tracing to a local processor only.

---

## 4. Builder reading list (read these yourself; ≤6 per area)

**Engine (Claude)**
1. https://code.claude.com/docs/en/agent-sdk/agent-loop
2. https://code.claude.com/docs/en/agent-sdk/python (options, `ClaudeSDKClient` methods, message types)
3. https://code.claude.com/docs/en/agent-sdk/hosting (subprocess model, sizing)
4. https://code.claude.com/docs/en/agent-sdk/claude-code-features (`setting_sources`, isolation table)
5. https://code.claude.com/docs/en/legal-and-compliance (auth rules; read before touching login)
6. https://code.claude.com/docs/en/agent-sdk/streaming-vs-single-mode

**Engine (OpenAI)**
1. https://openai.github.io/openai-agents-python/running_agents/
2. https://openai.github.io/openai-agents-python/models/
3. https://openai.github.io/openai-agents-python/streaming/
4. https://openai.github.io/openai-agents-python/results/
5. https://developers.openai.com/siwc/token-sharing-open-source (ChatGPT plan route; then its sub-pages)
6. https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations

**Permissions and hooks**
1. https://code.claude.com/docs/en/agent-sdk/permissions
2. https://code.claude.com/docs/en/agent-sdk/user-input
3. https://code.claude.com/docs/en/agent-sdk/hooks
4. https://code.claude.com/docs/en/hooks (wire format for the QMX hook runner)
5. https://openai.github.io/openai-agents-python/human_in_the_loop/
6. https://openai.github.io/openai-agents-python/guardrails/

**Sessions**
1. https://code.claude.com/docs/en/agent-sdk/sessions
2. https://code.claude.com/docs/en/agent-sdk/session-storage
3. https://openai.github.io/openai-agents-python/sessions/
4. https://openai.github.io/openai-agents-python/ref/run_state/
5. cookbook `claude_agent_sdk/05_Building_a_session_browser.ipynb`

**Compaction and caching**
1. https://code.claude.com/docs/en/prompt-caching
2. https://code.claude.com/docs/en/context-window
3. https://openai.github.io/openai-agents-python/sessions/ (section "OpenAI Responses compaction sessions")
4. cookbook `examples/agents_sdk/session_memory.ipynb` (local trim/summary sessions)
5. cookbook `examples/Prompt_Caching_201.ipynb`
6. https://openrouter.ai/docs/guides/best-practices/prompt-caching

**Router and providers**
1. https://openai.github.io/openai-agents-python/models/ (sections "Non-OpenAI models", "Third-party adapters")
2. https://openrouter.ai/docs/api_reference/limits (usage and credits)
3. https://openrouter.ai/docs/cookbook/coding-agents/claude-code-integration
4. https://dev.meta.ai/docs/protocols.md (Muse: choosing Responses / Chat / Messages)
5. https://dev.meta.ai/docs/pricing-rate-limits.md
6. https://opencode.ai/v2/docs/console/go/ (Go plan rules: own user agent, coding traffic)

**Sub-agents and skills**
1. https://code.claude.com/docs/en/agent-sdk/subagents
2. https://code.claude.com/docs/en/agent-sdk/skills
3. https://code.claude.com/docs/en/agent-sdk/custom-tools
4. https://code.claude.com/docs/en/agent-sdk/mcp
5. https://openai.github.io/openai-agents-python/tools/ (agents as tools, Codex tool, shell skills)
6. https://openai.github.io/openai-agents-python/mcp/

**Computer use**
1. https://code.claude.com/docs/en/computer-use (why the SDK path is closed)
2. https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool (API key path)
3. https://openai.github.io/openai-agents-python/tools/ (section "ComputerTool and the Responses computer tool")
4. cookbook `examples/agents_sdk/computer_use_with_daytona`
5. https://dev.meta.ai/docs/computer-use.md (Muse guide; not read in this pass)

**Tracing, usage and export**
1. https://openai.github.io/openai-agents-python/tracing/
2. https://code.claude.com/docs/en/agent-sdk/observability
3. https://code.claude.com/docs/en/agent-sdk/cost-tracking
4. https://code.claude.com/docs/en/agent-sdk/python (`RateLimitEvent`, `ResultMessage.model_usage`)
5. https://openai.github.io/openai-agents-python/usage/

---

## 5. Still UNVERIFIED after this pass

1. The OpenAI Agents SDK running on a Sign-in-with-ChatGPT token (no page says yes or no). Test it before building on it.
2. Responses compaction (`responses.compact` or `context_management`) on the ChatGPT-plan route.
3. Whether the `"user"` setting source follows `CLAUDE_CONFIG_DIR`.
4. How to change effort mid-session from the Python Claude client (no `set_effort` method listed).
5. Muse region limits for the Meta Model API itself (OpenCode Go says "limited regions" for contributor models).
6. Quality of QMX-built computer-use tools on Claude via a subscription (no Anthropic doc covers it).
