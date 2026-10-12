# 19 — Two-SDK study: Claude Agent SDK + OpenAI Agents SDK behind one QMX `Engine`

Researched 2026-10-12. Planning and research only. Nothing here is ratified. It is a factual baseline for the operator's proposal:
two engines (Claude Agent SDK, OpenAI Agents SDK), every other provider reached through an Anthropic- or OpenAI-compatible
base URL, a router that balances across endpoints, and a long-lived Claude orchestrator.

**How to read the citations**
- `OAI:<page> Lx` = OpenAI Agents SDK docs page `https://openai.github.io/openai-agents-python/<page>/`. The line numbers are from the
  docs source in a read-only sparse clone at `D:\QMX-research\sources\repos\openai-agents-python` (commit `125efa02`, 2026-10-08,
  package version `0.23.1`, `pyproject.toml` L3). `OAI-src:<file>` = source file in the same clone. Nothing was executed.
- `CC:<page> Lx` = `https://code.claude.com/docs/en/agent-sdk/<page>.md` fetched today. `CCH Lx` = `https://code.claude.com/docs/en/hooks.md`.
- `A01 §x` = `tracker/agent-system/research/01-agent-sdk-capability-audit.md` (the Claude Agent SDK audit; this file only adds to it).
- `HAR`, `MR`, `CB`, `LCS` = `rebuild/research/2026-10-12-agent-system/{harnesses,models-routing,cookbooks,langchain-stack}.md`.
- `H:<path>` = Hermes docs page, local copy `D:\QMX-research\sources\harnesses\hermes\pages\<path with __>.md`.
- `Pi:<file>` = `https://github.com/badlogic/pi-mono/blob/main/<file>` (fetched raw today).
- UNVERIFIED = not confirmed on a primary page. INFERRED = my reasoning from cited facts.
- Context7 needed re-authentication for most of the pass, so the docs source and official pages were used. After it reconnected,
  one query (`/websites/openai_github_io_openai-agents-python`, "per-agent client / API key") confirmed §1. Fetch count: about 30.

---

## 0. Plain-words summary

1. The OpenAI Agents SDK is a plain Python library. Agents are objects inside QMX's own process. There is no child program per session.
2. It talks to any OpenAI-compatible base URL out of the box. That covers GLM, DeepSeek, Kimi, MiniMax, OpenRouter, Ollama and similar.
3. It can mix providers per agent. A sub-agent can use a different model and a different provider from its parent.
4. Claude models inside the OpenAI SDK should go through its LiteLLM (or Any-LLM) adapter, not Anthropic's OpenAI-compatible endpoint.
   That endpoint drops prompt caching and does not return thinking.
5. Its approvals are the best part. A run pauses, QMX saves the whole state as JSON, and any process can resume it hours or days later.
6. Its hooks only observe. Blocking a tool is done with tool guardrails or approvals, so the QMX policy layer must live in QMX's tool wrappers.
7. It ships no Claude-Code-style toolset. Shell, file edit and computer use need executors QMX writes, or a "sandbox agent" (Docker on Windows).
8. Its compaction and hosted tools are OpenAI-server features. For GLM or DeepSeek workers QMX must write its own summariser.
9. Tracing goes to OpenAI's dashboard by default. QMX can switch that off and plug in its own exporter to files or OpenTelemetry.
10. The Claude Agent SDK stays as audit 01 found it: Claude Code in a box, one child process per session, one base URL per process.
11. New Claude facts: native OpenTelemetry, a `defer` decision that parks a tool call for later, and a Bash sandbox that is off on native Windows.
12. One `Engine` interface works if QMX owns four things itself: the event format, the approval queue, the usage ledger and tool policy.
13. Hard mismatches: live-callback approvals (Claude) vs pause-and-resume (OpenAI); a subprocess vs an object; who owns the history.
14. Cross-engine delegation is a QMX `delegate` tool given to the Claude orchestrator. It starts a job on the OpenAI engine and returns the result.
15. Neither SDK is a workflow engine for days-long, inspectable graphs. Keep LangGraph for the Lab graphs; Temporal or DBOS are later options.

---

## 1. Model and provider support

**OpenAI Agents SDK**
- Two built-in model shapes: `OpenAIResponsesModel` (recommended) and `OpenAIChatCompletionsModel` (OAI:models L3-6).
  The default model is `gpt-5.6-luna` with `reasoning.effort="none"` (OAI:models L26).
- Three ways to reach a non-OpenAI provider (OAI:models L311-337):
  - `set_default_openai_client(AsyncOpenAI(base_url, api_key))` sets one global endpoint.
  - A `ModelProvider` applies per run.
  - `Agent.model = OpenAIChatCompletionsModel(model=..., openai_client=AsyncOpenAI(base_url=..., api_key=...))` applies **per agent**.
    This is the documented way "to mix and match different providers for different agents" (L324).
- Most third-party providers lack the Responses API, so use Chat Completions for them (L339-341, L617-622).
  `set_default_openai_api("chat_completions")` switches globally.
- On Chat Completions the SDK **silently drops** Responses-only fields: `previous_response_id`, `conversation_id`, `prompt`, non-text tool outputs.
  `strict_feature_validation=True` makes this fail fast (L624-644).
- `buffer_streamed_tool_calls=True` handles unreliable streamed tool-call chunks (L650-661). `MultiProvider` routes by name prefix (`litellm/...`, `any-llm/...`) with OpenRouter-style pass-through (L187-222).
- **Adapters:** LiteLLM and Any-LLM are "best-effort, beta" (L683-713). Install `openai-agents[litellm]` and use `litellm/<provider>/<model>`
  or `LitellmModel`.
  - It keeps Anthropic thinking blocks (with signatures) across tool calls when `reasoning.effort` is set, and Gemini thought signatures
    (OAI-src:`extensions/models/litellm_model.py` L513-525, L684-731, L955-983).
- **Reasoning:** `reasoning.mode` and `reasoning.context="all_turns"` are Responses-only. Chat Completions sends only `effort`.
  With `store=False`, carry `reasoning.encrypted_content` items forward (OAI:models L95-97).
  `reasoning_item_id_policy="omit"` works around a Responses 400 about orphaned reasoning IDs (OAI:running_agents L256-274).
- **Prompt caching:** `ModelSettings.prompt_cache_options` sets implicit or explicit caching with a 30-minute TTL on GPT-5.6.
  Explicit breakpoints go on content parts and are passed through on both Responses and Chat Completions (OAI:models L419-468).
  Whether a non-OpenAI endpoint honours them is the provider's business: UNVERIFIED per provider.
  Whether Anthropic `cache_control` survives the LiteLLM adapter's message conversion is UNVERIFIED (no doc; the adapter source has no `cache_control` handling).
- **Usage per call:**
  - `result.context_wrapper.usage` holds `requests`, input, output and total tokens, plus `input_tokens_details.cached_tokens` and
    `cache_write_tokens`, `output_tokens_details.reasoning_tokens`, and `request_usage_entries` (one per request) (OAI:usage L5-14, L48-54).
  - `ModelSettings.preserve_raw_usage=True` keeps the provider's raw usage payload per response (L56-76).
  - LiteLLM often needs `ModelSettings(include_usage=True)`, and `LitellmModel` never fills `raw_usage` (OAI:usage L36-46, L72).
  - The LiteLLM adapter maps `cached_tokens` and `cache_write_tokens` into `Usage` (OAI-src:`litellm_model.py` L281-285).
- **Mixing caveat:** do not send hosted tools, multimodal input or JSON-schema outputs to providers that lack them (OAI:models L675-681).
  Pick one model shape per workflow where possible (L351-353).
- **Claude via Anthropic's own OpenAI-compatible endpoint (`https://api.anthropic.com/v1/`) is a poor route:**
  - "not considered a long-term or production-ready solution"; "Prompt caching is not supported"; thinking is not returned; `strict` ignored;
    `usage.prompt_tokens_details` always empty; Opus/Sonnet 5.5 reject forced `tool_choice` (https://platform.claude.com/docs/en/cli-sdks-libraries/libraries/openai-sdk).
  - So inside the OpenAI engine, Claude goes through LiteLLM's native Anthropic path, or Claude work goes to the Claude engine (INFERRED).

**Account rotation (several keys or accounts per provider)**
- OpenAI SDK: a key is bound to an `AsyncOpenAI` client. QMX can therefore pick the account per agent (`OpenAIChatCompletionsModel(openai_client=…)`),
  per run (`RunConfig(model_provider=…)`), or per adapter call (`LitellmModel(model, base_url=, api_key=)`).
  - Sources: OAI:models L311-324; OAI-src:`litellm_model.py` L153-163.
  - `set_default_openai_client(client, use_for_tracing=False)` keeps the tracing key separate (Context7 `/websites/openai_github_io_openai-agents-python`, config).
  - A per-run tracing key goes through `RunConfig(tracing={"api_key": …})` (OAI:tracing L178-200).
- Claude SDK: the account is per process. `ClaudeAgentOptions.env` sets `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` and its own
  `CLAUDE_CONFIG_DIR` (separate login) for each session (A01 §1, §4). Rotation happens at session start, not mid-session.
- Terms decide what may rotate: API keys yes; pooling or rotating subscription and coding-plan accounts no (MR §1).
  Rotating mid-thread also breaks caches (MR §6), so rotate per session (INFERRED).

**Claude Agent SDK (delta):** A01 §1 stands: Anthropic-format endpoints via `ANTHROPIC_BASE_URL` per process, GPT only through a proxy, non-Claude routing unsupported.

**How Hermes and Pi handle "both formats, any provider" (for the QMX router design)**
- **Hermes:** every provider resolves to `(provider, api_mode, base_url, api_key)` (H:developer-guide/provider-runtime "Output of runtime resolution").
  - `api_mode` is one of `chat_completions`, `codex_responses`, `anthropic_messages` or `bedrock_converse`, or a mode a plugin registers.
  - It is auto-detected from the URL, for example a `/anthropic` suffix gives `anthropic_messages` (H:developer-guide/model-provider-plugin L95, L335-339).
  - History is stored in OpenAI chat-completions shape and each transport converts from it (H:developer-guide/adding-providers "Tool-call wire format").
  - Each key is scoped to its own base URL so keys do not leak to the wrong host (provider-runtime, "OpenRouter, AI Gateway…").
  - A fallback chain swaps `api_mode` and client in place on 401/403/404/429/5xx (provider-runtime "Fallback models").
- **Pi:** each model in `models.json` declares `baseUrl` and `api` (`openai-completions`, `openai-responses`, `anthropic-messages`, …)
  plus verified `compat` flags. Pi warns not to enable them "based only on an endpoint advertising OpenAI or Anthropic compatibility"
  (Pi:packages/coding-agent/docs/models.md L12, L45-55, L128).
  - Pi converts history across providers in one conversation. Another provider's thinking becomes `<thinking>`-tagged text
    (Pi:packages/ai/README.md "Cross-Provider Handoffs").
- **Lesson for QMX (INFERRED):** a router entry should be `{endpoint id, base_url, key reference, wire format, model id, capability flags,
  price row}`. The engine is chosen by wire format:
  - Anthropic-format endpoints can feed either engine (Claude natively, OpenAI through LiteLLM).
  - OpenAI-format endpoints feed only the OpenAI engine (Claude needs a proxy, A01 §1).
- **Formats per vendor:** DeepSeek, Z.ai and Kimi have Anthropic endpoints (A01 §1); MiniMax, Ollama Cloud and OpenCode Zen Anthropic endpoints
  UNVERIFIED. All named vendors offer OpenAI-compatible endpoints (MR §1; UNVERIFIED for MiniMax and Ollama Cloud).

---

## 2. The agent loop and tools

**OpenAI Agents SDK**
- **Loop:** call the model. A final typed output with no tool calls ends the run. A handoff swaps the agent. Tool calls run and the loop repeats.
  `max_turns` raises `MaxTurnsExceeded`, or `None` disables it (OAI:running_agents L27-46). Error handlers exist for `max_turns`,
  `model_refusal` and `invalid_final_output` (L478-500).
- **Function tools:** `@function_tool` or `@tool` with Pydantic schemas and docstring parsing, plus per-tool timeouts and error formatters
  (OAI:tools L360-678).
- **MCP:** hosted MCP (`HostedMCPTool`, runs on OpenAI's side) and local stdio, SSE and Streamable HTTP servers (OAI:mcp L16-30).
  - Also a server manager, static and dynamic tool filtering, tool-list caching, and per-server `require_approval` (OAI:mcp L261-283, L372-535).
- **Hosted tools (OpenAI Responses only):** web search, file search, code interpreter, hosted MCP, image generation, tool search and
  programmatic tool calling (OAI:tools L25-34). Tool search, namespaces, deferred loading and programmatic tool calling are rejected on
  Chat Completions and non-Responses backends (OAI:models L113-122). **So GLM, DeepSeek and Kimi agents get none of them.**
- **Shell:**
  - `ShellTool` runs either in an OpenAI-hosted container (`container_auto`, network policy, skills) or locally through an executor
    that QMX supplies (OAI:tools L187-260).
  - Local shell and `ApplyPatchTool` default to `needs_approval=False`. The docs say "SDK approval does not provide a sandbox" (L252-256).
- **Computer use:** `ComputerTool` needs QMX's own `Computer` or `AsyncComputer` implementation. The GA `computer` tool payload depends
  on an OpenAI model (OAI:tools L236-250; OAI:models L99-107).
- **Sandbox agents (real, new):**
  - `SandboxAgent` is an `Agent` with a `Manifest` workspace, capabilities (`Shell`, `Filesystem`, `Skills`, `Memory`, `Compaction`),
    and resumable sandbox sessions and snapshots (OAI:sandbox/guide L1-25, L178-196).
  - Clients: `UnixLocalSandboxClient` (macOS/Linux, no isolation on Linux) and `DockerSandboxClient`. Hosted clients: Blaxel, Cloudflare,
    Daytona, E2B, Modal, Runloop and Vercel (OAI:sandbox/clients L5-24, L135-155).
  - "On Windows, use Docker or a hosted provider" (OAI:sandbox/guide L73).
- **Codex as a tool (experimental):** `codex_tool()` wraps the Codex CLI as one tool call.
  - It takes thread options (model, effort, approval policy, sandbox mode) and keeps a thread across calls.
  - Its usage is added to the run's usage (OAI:tools L917-979). **This is the exact pattern for QMX's cross-engine delegate tool** (section 12).
- **Parallel tool calls:**
  - `ModelSettings.parallel_tool_calls` lets the model emit several calls at once.
  - `RunConfig.tool_execution.max_function_tool_concurrency` caps how many local calls run together. The default starts all of them
    (OAI:running_agents L171-196).

**Claude Agent SDK (delta)**
- Full Claude Code toolset plus in-process `@tool` MCP servers (A01 §5).
- Parallel execution: read-only tools, and MCP tools marked `readOnlyHint`, run concurrently. Tools that change state run one at a time.
  Custom tools default to sequential (CC:agent-loop L184-188).

**Built-in tools ready to use**

| Tool | Claude Agent SDK (runs locally in the CLI) | OpenAI Agents SDK |
|---|---|---|
| Web search / fetch | `WebSearch` (Anthropic server tool; may be missing on third-party endpoints, A01 §1), `WebFetch` | `WebSearchTool`, hosted, OpenAI Responses only |
| Computer use | Not built in; via MCP (A01 §8 row 25) | `ComputerTool`; QMX implements the `Computer`, and the model must be OpenAI |
| Code execution | `Bash` on the host (sandbox optional, below) | `CodeInterpreterTool` (hosted), hosted or local `ShellTool`, sandbox `Shell` |
| Files | `Read`, `Edit`, `Write`, `Glob`, `Grep` | `FileSearchTool` (OpenAI vector stores), `ApplyPatchTool` (QMX editor), sandbox `Filesystem` |
| MCP | stdio/HTTP/SDK servers, tool search | Local stdio/SSE/HTTP + `HostedMCPTool` |
| Skills / plugins | Agent Skills, plugins, slash commands (A01 §8 row 23) | Hosted-shell skills, local-shell skills, sandbox `Skills`; no plugin system |
| Sub-agents / tasks | `Agent`, `Skill`, `AskUserQuestion`, `TaskCreate`/`TaskUpdate`, `ToolSearch` | `as_tool`, handoffs; `codex_tool` (experimental) |

Sources: CC:agent-loop L151-170; OAI:tools L25-34, L187-260; OAI:sandbox/guide L178-196.

**Sandboxes, and whether they run locally on Windows**
- OpenAI `SandboxAgent`:
  - Locally on Windows it needs `DockerSandboxClient`. Unix-local is macOS/Linux only (OAI:sandbox/guide L73).
  - Remotely it runs on Blaxel, Cloudflare, Daytona, E2B, Modal, Runloop or Vercel. Sandbox state and snapshots can resume later (§2 above).
  - The hosted container `ShellTool` runs on OpenAI's side whatever the OS.
- Claude Agent SDK: `ClaudeAgentOptions.sandbox = SandboxSettings(enabled, network, excludedCommands, allowUnsandboxedCommands, …)`
  sandboxes `Bash` (CC:python L858-911, L3536-3561).
  - It works on macOS (Seatbelt), Linux and WSL2 (bubblewrap + socat).
  - "On native Windows, Claude Code runs commands unsandboxed" (https://code.claude.com/docs/en/sandboxing.md L13, L57-58).
  - So on the QMX Windows desktop, Claude workers that need isolation run in WSL2, Docker or a Linux server (INFERRED).
  - For remote isolation, Anthropic's options are Managed Agents' cloud or self-hosted sandbox, or QMX's own containers (A01 §3; CC:overview L20).

---

## 3. Sub-agents, handoffs and agents-as-tools

**OpenAI Agents SDK**
- **Agents as tools:** `agent.as_tool()` runs a nested run with its own `max_turns`, `run_config`, `hooks`, `session` and `needs_approval`.
  The parent's conversation state "is not inherited automatically" (OAI:tools L679-735). Nested turns do not count toward the outer turn
  limit (OAI:sandbox/guide L877-883).
- **Handoffs:** the receiving agent takes over the same run and sees the full history unless an `input_filter` trims it.
  Opt-in beta "nested handoff history" summarises it (OAI:handoffs L110-121; OAI:multi_agent L20-28).
- **Different model or provider per sub-agent: yes.** Each `Agent` carries its own `model` string or `Model` object. The docs' own example
  mixes `gpt-5-mini`, a Chat Completions model object and `gpt-5.6-sol` in one triage graph (OAI:models L343-389; L317, L324).
  - Caveat: Responses-only features and model shapes must match what both sides support (L351-353).
- **Code orchestration:** structured-output routing, chaining, evaluator loops and `asyncio.gather` are recommended for deterministic flows
  (OAI:multi_agent L43-52).
- **Hosted multi-agent (experimental):** a GPT-5.6 root creates sub-agents on OpenAI's servers.
  - SDK handoffs are rejected, and `needs_approval` tools are refused.
  - An in-flight hosted response cannot be restored in another process (OAI:models L238-305). Not useful for QMX's mixed providers (INFERRED).

**Claude Agent SDK (delta):**
- Sub-agents (`AgentDefinition`, `.claude/agents`) are confirmed in A01 §2. They share the parent process's single base URL, so a
  different provider per sub-agent needs a routing gateway keyed by model name (A01 §1).
- There is no handoff primitive. The main agent can only `set_model()` mid-session (A01 §3), which MR §6 forbids for QMX.

---

## 4. Human-in-the-loop, approvals, guardrails, hooks

**OpenAI Agents SDK: approvals**
- `needs_approval=True` or an async predicate works on function tools, `Agent.as_tool`, `ShellTool` and `ApplyPatchTool`.
  Local MCP servers use `require_approval`; hosted MCP uses `require_approval` plus `on_approval_request` (OAI:human_in_the_loop L11-45).
- Predicates **fail closed** on malformed arguments (L15).
- **Flow:**
  - The run stops with `result.interruptions` (a list of `ToolApprovalItem`).
  - QMX calls `state = result.to_state()`, then `state.approve(item)` or `state.reject(item, rejection_message=...)`,
    then `Runner.run(agent, state)`.
  - Sticky `always_approve` and `always_reject` decisions survive serialisation (L49-61).
  - Approvals raised inside handoffs and nested `as_tool` runs surface on the **outer** run (L5-7).
- **Durable and cross-process:** `RunState` "is designed to be durable". Use `state.to_json()` or `to_string()`, store it, and rebuild it
  later with `RunState.from_json(agent, ...)`; "could be a different process" (L113-174, L191-193).
  - Security rules: deserialise only trusted, server-owned snapshots. Authenticate the reviewer. Consume each pending request atomically
    so it cannot be replayed (L195-210).
  - Store a version marker for agent and tool definitions alongside the state (L224-226).
  - The serialized state includes the app context, usage, nested agent-tool state and trace metadata, so keep secrets out of the context (L222).
- `RunState.add_input()` stages new user input before the next model call while the run is paused (OAI:results L146-166).
- Streaming runs: drain `stream_events()`, then read `interruptions` (OAI:streaming L39-58).
- Cancel: `result.cancel()` stops now; `cancel(mode="after_turn")` stops cleanly after the turn (OAI:streaming L59-69).

**Guardrails**
- Input guardrails run only on the **first** agent, and can run in parallel or blocking. Output guardrails run only on the agent that
  produces the final output (OAI:guardrails L10-18, L32-38).
- **Tool guardrails** run on every function-tool call, before and after. They can skip the call, replace the output or trip.
  They also attach to local MCP servers (L71-80).
- They do **not** cover hosted tools, `ComputerTool`, `ShellTool`, `ApplyPatchTool`, `LocalShellTool` or `as_tool` (L80).
- `pre_approval_tool_input_guardrails=True` runs the input check before the approval prompt too (OAI:running_agents L194-196).

**Lifecycle hooks: observe only (all methods return `None`)**
- `RunHooks`: `on_llm_start/end`, `on_agent_start/end`, `on_handoff`, `on_tool_start/end`. `AgentHooks`: `on_start/end`, `on_handoff`,
  `on_tool_start/end`, `on_llm_start/end` (OAI-src:`lifecycle.py` L13-110, L119-219; OAI:agents L262-305).
- Other hook-like points: `call_model_input_filter` rewrites model input (OAI:running_agents L441-475), and `session_input_callback`
  (OAI:streaming L69).
- **Nothing here can deny or rewrite a tool call. Use approvals or tool guardrails for that** (INFERRED from the signatures).

**Claude Agent SDK (delta to A01 §5)**
- **New: `defer`.**
  - A `PreToolUse` hook returning `permissionDecision: "defer"` ends the turn with `stop_reason: "tool_deferred"` and a
    `deferred_tool_use {id, name, input}`.
  - The caller collects the answer and resumes the session. The same hook fires again and returns `allow` with `updatedInput`.
  - There is "no timeout or retry limit"; sessions are swept after 30 days by default (CCH L1980-2006).
  - **Limits:** non-interactive (`-p`/SDK) only. It is ignored when Claude makes several tool calls in one turn (CCH L1980, L2008).
  - Precedence is deny > defer > ask > allow (CCH L1914).
- This is the closest Claude equivalent to OpenAI's serialised `RunState`. It is narrower: one pending call, and resume is by session ID
  on a host that can read the transcript (needs a `SessionStore` across hosts; CC:session-storage L1-20).
- Hook callbacks default to a 600-second timeout. `SessionStart` and `SessionEnd` are not Python callbacks (CC:hooks L147-167, L789, L831-849).
- A `permission_prompt` notification fires after about six seconds of waiting on `can_use_tool` (CC:hooks L657).
  How long `can_use_tool` itself may block before something times out: UNVERIFIED.

---

## 5. Sessions and memory

**OpenAI Agents SDK**
- The `Session` protocol: before each run, history is loaded and prepended; after each run, new items are stored
  (OAI:sessions/index L52-60). Four methods (CB §6).
- **Backends:** `SQLiteSession`, `AsyncSQLiteSession`, `RedisSession`, `SQLAlchemySession` (any SQLAlchemy DB), `MongoDBSession`,
  `DaprSession` (30+ stores, TTL), `OpenAIConversationsSession` (server-side), `AdvancedSQLiteSession` (branching, usage analytics),
  `EncryptedSession` (wrapper: encryption + TTL), or a custom implementation (OAI:sessions/index L174-197, L487-498, L588-628).
- Alternatives to sessions: `to_input_list()` (QMX owns the history), `conversation_id`, or `previous_response_id`. The last two are
  OpenAI-server-only. Choose one per conversation (OAI:running_agents L275-294).
- **Compaction:**
  - `OpenAIResponsesCompactionSession` wraps any session. It calls OpenAI's `responses.compact` between turns, or on demand with
    `run_compaction({"force": True})` (OAI:sessions/index L227-281).
  - Server-side `context_management=[{"type":"compaction","compact_threshold":N}]` is a Responses request field (OAI:models L476).
  - **Both are OpenAI Responses features.** For DeepSeek, GLM or Kimi workers QMX must write its own summarising `Session` wrapper or a
    `call_model_input_filter` (INFERRED; no provider-neutral summariser is documented).
  - `truncation="auto"` is also Responses-only (OAI:models L416).
- Handoff-time history summarisation is a beta (section 3).
- **Trust:** SQLite rows are not authenticated, and a session ID is not authorisation (OAI:sessions/index L500-506).
- **Over days:** any durable backend plus a serialised `RunState` covers multi-day threads (INFERRED). There is no context-window manager
  beyond the compaction above.
- A sandbox `Memory` capability writes "lessons" files that later runs read (OAI:sandbox/guide L855-859).

**Claude Agent SDK (delta):**
- JSONL transcripts per machine. A `SessionStore` adapter (`append`/`load` plus optional list/delete) mirrors them to QMX's own storage
  for multi-host resume (CC:session-storage L1-20; A01 §3).
- Compaction is automatic, model-neutral and summary-only (A01 §5).

---

## 6. Durable long-running execution

**OpenAI Agents SDK**
- The core gives a resumable `RunState` but no scheduler or worker. Four official integrations are listed (OAI:running_agents L575-593):
  - **Temporal:** the agent loop, tool selection and handoffs run in a Workflow. Model calls run as Activities, so they "retry durably and
    are not repeated during Workflow replay".
    - I/O tools must be `activity_as_tool()`. Plain function tools run inside the deterministic workflow. Hosted tools run in the model
      activity. `Agent.as_tool` works unchanged (https://docs.temporal.io/develop/python/integrations/openai-agents).
    - The integration moved to the standalone package `temporalio-openai-agents` (https://github.com/temporalio/sdk-python/tree/main/temporalio/contrib/openai_agents).
    - A sandbox-agent Temporal example exists (OAI-src:`examples/sandbox/extensions/temporal/README.md`).
  - **DBOS:** needs only SQLite or Postgres. It covers long-running agents, HITL and handoffs.
  - **Restate:** a single-binary runtime. **Dapr (Diagrid):** durable agents plus a `DaprSession`.
- Background runs: run `Runner.run` in a FastAPI background task, Celery or similar, and call `flush_traces()` at the end
  (OAI:tracing L61-104).
- **Cron:** none in the SDK (INFERRED; nothing documented). Use the OS, Railway cron or Temporal schedules.

**Claude Agent SDK:**
- No durable-execution integration documented. Durability = session resume + `SessionStore` + `defer`; dynamic workflows resume only
  "within the same Claude Code session" and accept no mid-run input (A01 §2).
- Managed Agents is Anthropic's hosted harness, with sessions in Anthropic's cloud or a self-hosted sandbox. It is a different product
  (CC:overview L13-20; CB §23 advises against it as the runtime).

**Comparison (short)**

| | OpenAI SDK `RunState` | + Temporal / DBOS | Claude Agent SDK | LangGraph |
|---|---|---|---|---|
| Resume after crash mid-run | Only from the last saved state; QMX saves it | Yes, replay skips finished model calls | Session resume; mid-turn work lost (INFERRED) | Yes, from the last node checkpoint (LCS §a2) |
| Human gate, days long | Yes, interruptions + JSON state | Yes (workflow waits; Temporal signals UNVERIFIED here) | `defer` (single call) or live callback | `interrupt()` + checkpointer (LCS §a5) |
| Typed multi-step graph | No; code orchestration | Workflow code is the graph (not visual) | No (dynamic workflows are model-written JS) | Yes, `StateGraph`; QMX P10 compiler exists (A01 §2) |
| Inspectable state | JSON blob | Event history in the Temporal UI (UNVERIFIED for DBOS) | JSONL transcript | Checkpoints per node, time travel (LCS) |
| Extra infrastructure | None | Temporal server, or a DB for DBOS | None | SQLite / Postgres checkpointer |

---

## 7. Tracing and logs

**OpenAI Agents SDK**
- Tracing is **on by default** and uploads to the OpenAI Traces dashboard. Switch it off with `OPENAI_AGENTS_DISABLE_TRACING=1`,
  `set_tracing_disabled(True)` or per run. It is unavailable under ZDR (OAI:tracing L1-12).
- Spans: trace, `task_span`, `turn_span`, agent, generation, function, guardrail, handoff, transcription, speech and custom spans (L29-44).
- **Without the OpenAI dashboard:** `set_trace_processors([...])` **replaces** the exporter, and `add_trace_processor` adds one (L155-165).
  - Run redaction inside the same exporter, because processors are independent (L167-176).
  - With non-OpenAI models and no OpenAI key, the docs say to disable tracing or use a custom processor (OAI:models L326, L609-615).
- **Local files or OpenTelemetry:** no built-in OTel exporter is documented. Listed integrations include Logfire, Arize Phoenix, MLflow (OSS),
  Langfuse, LangSmith and Datadog (OAI:tracing L217-250).
  - OpenAI's cookbook writes a custom exporter that turns SDK spans into OpenTelemetry-style JSONL
    (https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop). **QMX writes one small `TracingProcessor` → JSONL/OTLP** (INFERRED).
- Python `logging` debug logs, with a sensitive-data section (OAI:config L203-252).

**Claude Agent SDK (new, beyond A01)**
- Native OpenTelemetry: metrics, log events and traces. Traces are beta and need `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`.
  All are configured by env vars per process or per `options.env` (CC:observability L20-37).
- Spans: `claude_code.interaction`, `llm_request`, `tool` (with `blocked_on_user` and `execution` children) and `hook`.
  Sub-agent spans nest under the parent's tool span (L141-150).
- The SDK injects W3C `TRACEPARENT` from QMX's active span, so Claude spans join QMX's own trace (L160-166).

---

## 8. Voice and realtime; evals

- **OpenAI voice:**
  - Realtime agents on `gpt-realtime-2.1` with interruption detection, guardrails and handoffs (OAI:index L22).
  - Realtime tool approvals emit `tool_approval_required`; answer with `approve_tool_call()` (OAI:realtime/guide L283-292). SIP and telephony are supported (L349).
  - A voice pipeline (speech-to-text → workflow → text-to-speech) is separate (OAI:voice/pipeline).
- **Claude voice:** no voice or realtime page among the Agent SDK docs (CC llms.txt index, 32 agent-sdk pages). UNVERIFIED that none exists.
- **Evals (OpenAI):**
  - Trace grading and eval runs live in the OpenAI dashboard, which needs traces uploaded to OpenAI
    (https://developers.openai.com/api/docs/guides/agent-evals; .../trace-grading).
  - In-SDK there are deterministic, provider-neutral test utilities (`ScriptedModel`, scripted sandbox, realtime and voice) that make no
    model calls (OAI:testing L1-24, L547-560).
- **Evals (Claude):** no eval framework in the Agent SDK docs. CB §16 covers eval patterns. QMX's eval battery stays QMX-owned either way.

---

## 9. Windows vs Linux

**OpenAI Agents SDK**
- Pure Python, "OS Independent", classifiers up to 3.14, `requires-python >=3.10` (OAI-src:`pyproject.toml` L6, L27-33).
- The quickstart has PowerShell and cmd steps (OAI:quickstart L23-53).
- **Sandbox agents:** the Unix-local client is macOS/Linux only. "On Windows, use Docker or a hosted provider" (OAI:sandbox/guide L73).
- Local `ShellTool` on Windows needs a QMX executor that runs PowerShell (INFERRED).
- `codex_tool` needs a Codex binary. Codex's install docs give Windows support only through WSL2 (HAR §1).
- Version 0.21 moved to `openai` v3 and HTTPX2. Custom `httpx` clients must migrate (OAI:release L35-46). Breaking notes arrive with each minor version.
- Temporal or DBOS on the Windows desktop: UNVERIFIED. Treat them as a Linux-server lane (INFERRED).

**Claude Agent SDK:** see A01 §3:
- The Windows wheel bundles `claude.exe` (105 MB).
- Open Windows issues: #480, #883, #902 and #1239.
- Linux is first-class, but has the non-TTY hang (#926) and the dead-CLI hang (#1110).

---

## 10. Mapping table: Claude Agent SDK vs OpenAI Agents SDK

Rebuild key:
- **⇄** = QMX can rebuild one side's feature on the other with ordinary code.
- **→C** = only the Claude side has it, and QMX cannot rebuild it in the OpenAI SDK at equal quality.
- **→O** = only the OpenAI side has it, and QMX cannot rebuild it in the Claude SDK.
- **✗** = neither has it; QMX builds it outside both.

| Concern | Claude Agent SDK | OpenAI Agents SDK | Rebuild |
|---|---|---|---|
| Loop | Claude Code's loop in a CLI child process | `Runner` loop in-process; handoffs swap the agent (OAI:running_agents L27-46) | ⇄ (both are model→tools→repeat) |
| Tools | Full Claude Code set + in-process `@tool` MCP (A01 §5) | Function tools, MCP; shell/patch/computer need QMX executors or a `SandboxAgent`; hosted tools only on OpenAI Responses (§2) | →C for the tuned built-in set (wrap Claude Code as a tool instead, like `codex_tool`); hosted OpenAI tools →O |
| Hooks | 10 Python events; can deny, rewrite input or output, defer (A01 §5; CCH L1909-1914) | Observe-only Run/Agent hooks; blocking via tool guardrails and approvals (§4) | ⇄ if QMX puts policy inside its own tool wrappers; not for OpenAI hosted or shell tools |
| Approvals | Live `can_use_tool` callback; `defer` for one parked call | Interruptions + serialisable `RunState`, many pending, cross-process (§4) | Partly →O (Claude cannot park a multi-call batch) |
| Sub-agents | Agent tool, background, same base URL; no handoff | `as_tool` and handoffs; any model or provider per agent (§3) | Per-agent provider →O, unless Claude goes through a gateway keyed by model name (A01 §1) |
| Sessions | JSONL + `SessionStore`, resume/fork by ID (A01 §3) | `Session` protocol, 10 backends, QMX-owned items (§5) | ⇄ (Claude history stays opaque CLI format) |
| Compaction | Automatic, any model, summary-only (A01 §5) | OpenAI Responses-only (compact endpoint or server field) (§5) | ⇄ with QMX code: OpenAI side needs a custom summarising Session for non-OpenAI models |
| Caching | Automatic `cache_control`, 5m/1h TTL (A01 §5) | `prompt_cache_options` on OpenAI; others provider-defined; Claude via LiteLLM UNVERIFIED (§1) | →C for Claude cache control; ⇄ otherwise |
| Usage | Per message and `model_usage` per model incl. sub-agents; cost estimate (A01 §5) | Per request with cache read/write and reasoning tokens; LiteLLM needs `include_usage` (§1) | ⇄ (QMX ledger normalises both) |
| Tracing | Native OTel export + `TRACEPARENT` (§7) | Own trace model; custom processor needed off-OpenAI (§7) | ⇄ |
| Durable runs | Session resume, `defer`; no integration (§6) | `RunState` + Temporal/DBOS/Restate/Dapr (§6) | →O for official durable integrations |
| Remote execution | Linux/Docker hosting guide; Managed Agents hosted (A01 §3; CC:overview) | Hosted sandbox clients, hosted container shell, Agents API (managed Codex harness) (§2; developers.openai.com/api/docs/guides/agents) | ⇄ at the QMX level: both run on a Linux box QMX controls |
| RAM / process | One child process per session, ~1 GiB guidance (A01 §3) | Objects in one asyncio process; footprint not measured (UNVERIFIED) | Structural; cannot be rebuilt |

**What cannot cross at all (INFERRED):**
- Claude-only server features (Anthropic tool search, Claude-tuned prompts, auto mode) do not move into the OpenAI SDK.
- OpenAI server features (hosted tools, `responses.compact`, Conversations, hosted multi-agent) do not work on GLM, DeepSeek or Kimi in either SDK.
- The Claude subscription may only drive the unmodified Claude Code binary or Agent SDK (MR §0-1). It can never feed the OpenAI engine.
- History cannot move between engines mid-thread (MR §6). Switching engine means a new session or a sub-task.

---

## 11. OOP design check: a QMX `Engine` both SDKs can implement

**Interface sketch (prose).** One `Engine` per SDK. Each method works on a QMX `SessionRef`, made of engine name, endpoint id,
model id, the engine's own native resume token, and a spec version.

| QMX method | What it does | Claude Agent SDK mapping | OpenAI Agents SDK mapping |
|---|---|---|---|
| `start_session(spec)` | Build an agent from a QMX AgentSpec (instructions, tools, policy, model, endpoint) | `ClaudeSDKClient(ClaudeAgentOptions(env=…, model=…, mcp_servers={qmx: sdk server}, hooks=…, can_use_tool=…, setting_sources=[]))`, then `connect()`; record `session_id` from the init message (A01 §3-4) | `Agent(model=<Model obj for endpoint>, tools=…, hooks=…)` plus a `Session` keyed by a QMX thread id (§1, §5) |
| `resume_session(ref)` | Reattach after restart, or on another host | `ClaudeAgentOptions(resume=session_id)`; cross-host needs a `SessionStore` (§5) | Same `Session` id; if paused, `RunState.from_json(agent, stored)` (§4) |
| `send_turn(ref, input)` | One user turn | `client.query(input)` | `Runner.run_streamed(agent, input, session=…)`; if paused, `state.add_input()` then resume (OAI:results L146-166) |
| `stream_events(ref)` | Normalised QMX events: text delta, tool start/end, approval request, usage, sub-agent, done | `receive_response()` messages + `StreamEvent` + `TaskStarted/Progress` (A01 §3) | `stream_events()`: raw response, run-item and agent-updated events (OAI:streaming L9-75) |
| `approve(ref, request_id, decision)` | Answer a pending approval | Resolve the Future that `can_use_tool` is awaiting (live); or for parked calls resume after `defer` with `allow`+`updatedInput` (§4) | `state.approve/reject(item)`, then `Runner.run(agent, state)` (§4) |
| `interrupt(ref, mode)` | Stop now or after the turn | `client.interrupt()`; per-task `stop_task(id)` (A01 §3) | `result.cancel()` / `cancel(mode="after_turn")` (§4) |
| `delegate(ref, task)` | Hand a bounded task to another agent or engine | Native sub-agent (same endpoint) or the QMX `delegate` MCP tool (§12) | `Agent.as_tool()` (any provider) or the same QMX `delegate` function tool |
| `usage(ref)` | Tokens, cache read/write, cost, per model | `AssistantMessage.usage`, `ResultMessage.model_usage`, `total_cost_usd` (estimate), `RateLimitEvent` (A01 §5) | `context_wrapper.usage.request_usage_entries`, cached and cache-write tokens (§1); QMX prices it |
| `checkpoint(ref)` | Durable snapshot for crash or day-long pause | Session id + transcript (SessionStore); nothing mid-turn (INFERRED) | `result.to_state().to_json()` stored server-side (§4) |
| `close(ref)` | Free resources | `disconnect()`; watch MCP grandchild reaping (#889, A01 §7) | Close the session or DB; nothing to reap |

**Hard mismatches QMX must design around**
1. **Approval timing.**
   - Claude asks *inside* a live process. `can_use_tool` must block while the human decides, and the session's process stays alive.
     `defer` parks only a single-call turn.
   - OpenAI returns and lets QMX persist. QMX's approval queue must accept both a "live waiting" and a "parked, resumable" request,
     and the UI must not care which one it is (INFERRED).
2. **Policy enforcement point.** Claude can deny in a hook. OpenAI hooks cannot, and tool guardrails skip hosted, shell, patch and computer tools.
   - Put the money-path and admission checks **inside QMX's own tool implementations** (the shared `qmx_tools` registry).
   - Give the OpenAI engine only QMX-wrapped shell and patch executors, never raw ones.
   - Engine hooks then only report (INFERRED; matches A01 §9 option C's "one rule code, tested on both").
3. **Process model.** Claude gives N sessions = N child processes (~1 GiB each), so the orchestrator plus a few Claude workers is the ceiling.
   OpenAI gives N sessions = N objects. Admission control must count them differently (INFERRED).
4. **History ownership.** Claude history is an opaque CLI transcript; OpenAI history is items QMX can read and edit. Cross-engine
   continuation of one thread is out (MR §6). The UI's session browser must index two formats.
5. **Compaction parity.** Claude compacts on any model. OpenAI compacts only on OpenAI. Non-OpenAI OpenAI-engine threads need a QMX
   summariser or must be kept short (task-scoped workers).
6. **Tool parity.** A "Claude-Code-like" worker on GLM via the OpenAI engine is not Claude Code. Either accept a smaller toolset, or use a
   `SandboxAgent` (Docker on Windows), or route coding tasks to the Claude engine with an Anthropic-format GLM/DeepSeek endpoint (A01 §1).
7. **Provider per sub-agent.** Free on OpenAI. On Claude it needs a LiteLLM-style gateway mapping model names to providers, which
   Anthropic does not support (A01 §1).

**Verdict on the OOP model:**
- Sound, as long as the `Engine` is thin and QMX owns events, approvals, ledger, policy and the router.
- The router should pin an endpoint per session ("sticky"), not balance per request. Caches and thinking are per model and provider
  (MR §0 item 6, §6). Fail over only at session or task boundaries.

---

## 12. Cross-engine delegation: Claude orchestrator → GPT/GLM worker on the OpenAI engine

**Shape (INFERRED from the `codex_tool` precedent, OAI:tools L917-979, and A01 §5)**
- The orchestrator is a long-lived `ClaudeSDKClient` session on Opus 5.5. It gets an in-process SDK MCP server `qmx` (`@tool` +
  `create_sdk_mcp_server`) with:
  - `qmx_models_status()`: the router's catalogue of endpoints, models, strengths, prices, remaining budget, and plan limits from
    `RateLimitEvent` and the QMX ledger (see `05-usage-limits-telemetry.md`).
  - `qmx_delegate(task, role, model_hint?, output_schema?, budget_usd?, max_turns?, wait?)`: returns `{job_id}`, or the result if
    `wait` is set and the job is short.
  - `qmx_job_status(job_id)` and `qmx_job_result(job_id)`: poll, so a days-long orchestrator never blocks one tool call for hours.
    Whether Claude Code has a hard MCP tool-call timeout is UNVERIFIED.
- **QMX side (the handler):**
  1. The router picks an endpoint and model.
  2. The OpenAI engine builds `Agent(model=OpenAIChatCompletionsModel(model, AsyncOpenAI(base_url, api_key)))` or a `LitellmModel`,
     with `output_type` set to the Pydantic model compiled from `output_schema`. Tools come from the same QMX registry, filtered by role.
  3. It runs `Runner.run(..., session=SQLAlchemySession(job_id), max_turns=…)` in a background task.
  4. It stores `to_state().to_json()` whenever interruptions appear. Interruptions become QMX approval-queue items.
  5. When the run finishes, it writes the final output plus normalised usage to the job record and the ledger.
- **Back to the orchestrator:** `qmx_job_result` returns compact JSON: the result, a short summary, files or artifact paths, usage and
  cost, and the approvals that happened. Large outputs go to files, not into the orchestrator's context (CB §7 clean-context delegation).
- **What each side needs:**
  - Claude side: the `qmx` MCP server, `allowed_tools` including `mcp__qmx__*`, a `PreToolUse` hook that checks the delegate budget,
    and an isolated env and `CLAUDE_CONFIG_DIR` (A01 §4).
  - OpenAI side: a job runner (asyncio task or worker process), a durable session backend, `RunState` storage, a trace processor writing
    to QMX logs, and `set_tracing_disabled` or a replacement exporter so traces never leave for OpenAI by accident (§7).
- **Reverse direction (OpenAI orchestrator → Claude worker):** a function tool that runs a `ClaudeSDKClient` job, exactly like `codex_tool`.
  It costs one Claude process per job (§11 item 3).
- **Sub-agents "following the engine the router picks":** OpenAI-engine sub-agents can each take any endpoint. Claude-engine sub-agents
  inherit the parent's base URL, so they should call `qmx_delegate` when they need a different provider. Removing `Agent` from their tools
  enforces "sub-agents do not spawn sub-agents" (A01 §2).

---

## 13. Workflows: does either SDK give durable, inspectable, multi-step workflows?

- **OpenAI Agents SDK alone:** no.
  - It gives resumable single runs (`RunState`), code orchestration and HITL.
  - It does not give a typed multi-step workflow with per-step checkpoints, retries or an inspectable graph (OAI:multi_agent L43-52; §6).
  - With **Temporal**, the workflow is durable and days-long: model calls are replay-safe activities and tools can be activities.
    But it is code, not a visual graph, and it needs a Temporal server (§6). **DBOS** gives similar durability on SQLite or Postgres only.
- **Claude Agent SDK alone:** no. Dynamic workflows have no mid-run input, no typed state, and resume only in the same session (A01 §2).
- **LangGraph:**
  - Typed state, deterministic and agentic nodes, `interrupt()` gates, SQLite checkpointer, per-node timeouts and drain (LCS §a2, §a5).
  - QMX already ships a compiler from its 10 node kinds to LangGraph (A01 §2, P10).

**Official orchestration guidance ("graph engineering" and "loop engineering")**
- Anthropic separates *workflows*, where LLMs and tools follow "predefined code paths", from *agents*, which direct their own tool use.
  - It names five workflow patterns: prompt chaining, routing, parallelisation, orchestrator-workers and evaluator-optimizer.
  - It advises starting with direct API calls, and understanding any framework's underlying code.
  - Source: https://www.anthropic.com/engineering/building-effective-agents.
- OpenAI separates "orchestrating via LLM" (agents as tools, handoffs) from "orchestrating via code". Code orchestration covers
  structured-output routing, chaining, evaluator loops and `asyncio.gather`, and is "more deterministic and predictable" (OAI:multi_agent L1-52).
- Neither vendor ships a graph engine. Both treat code orchestration as plain host code.
- **Could QMX drop LangGraph and run workflows on the two SDKs itself?** Technically yes: a QMX runner that walks the node graph,
  calls `Engine` per agent node and persists each node's output plus the engine resume token.
  - But QMX would then rebuild what LangGraph already gives it: typed state, checkpoints, `interrupt()`, retries/timeouts/drain,
    and the existing P10 compiler (LCS §a2).
  - **Not this week** (INFERRED). Revisit only if LangGraph's dependency weight or the Opus compaction issue (LCS §a10) bites outside the Lab.

**Codex and cookbook data, analytics and quant patterns (only what bears on the SDK choice)**
- Codex use cases lean on data work: dashboards, cleaning data, DCF models, forecasts, KPI root-cause, variance bridges
  (https://developers.openai.com/codex/use-cases). They run in OpenAI's own apps with skills such as "Data Analytics", not on the Agents SDK.
  The SDK's path to the same harness is `codex_tool` (§2).
- The OpenAI Agents SDK portfolio cookbook (a PM agent with fundamental, macro and quant specialists run as tools, plus code interpreter)
  is a Python-native template for QMX's Portfolio copilot. The Claude side offers financial-statement and DCF skills and a
  financial-analyst sub-agent (CB §20).
- Bearing on the choice (INFERRED): quant work needs code execution. The OpenAI engine has the hosted code interpreter only on OpenAI
  models (GLM/DeepSeek need a QMX tool or Docker sandbox); the Claude engine has local `Bash`/Python, unsandboxed on Windows (§2).

**Recommendation (not ratified):**
- **Keep LangGraph as the Lab workflow engine** and make "agent step" a node kind that calls the QMX `Engine` (`engine: claude | openai`, `endpoint`, `model`).
  - Inside an agent node, store the engine's native resume token (Claude `session_id`, OpenAI serialised `RunState` or session id) in
    graph state. A node retry after a crash then resumes the agent instead of restarting it (INFERRED).
  - A human gate between steps is a LangGraph `interrupt()`. An approval inside an agent step is the engine's own pause, surfaced as the
    same QMX approval item.
- **Use LangGraph only there.** Copilots and the orchestrator run directly on the engines.
- **Defer Temporal.** It is the strongest durable runtime and OpenAI-endorsed, but it is a server to run and learn.
  Reconsider for the Linux orchestrator lane if LangGraph's resume proves insufficient.
  - DBOS is the lighter candidate to evaluate first: SQLite or Postgres only (OAI:running_agents L591-593). Windows support UNVERIFIED.
- **Reasons:** the QMX compiler and checkpointer already exist; neither SDK offers typed, inspectable graphs; engines behind one
  interface keep the graph engine swappable later.

---

## Appendix A — Server lanes (one page each)

- **Amp "orbs" (confirmed name):** "Orbs are remote machines where Amp agents work without using your computer".
  - Each orb thread gets a fresh, isolated environment; it sleeps when idle at no cost and wakes with files and services in place.
    Burst of 20 orbs, then one per five minutes. `amp -ox "<task>"` starts one; `amp sync` mirrors changes (https://ampcode.com/docs/orbs, 2026-09-14).
  - They run **Amp's** agent, not arbitrary QMX code (INFERRED from the page). For QMX they are a product reference for
    "send a prompt, close the laptop", not a host.
- **Railway:**
  - Cron services start on a crontab expression (UTC, at least 5 minutes apart). They must exit when done. If the previous run is still
    active, the next is **skipped**. Timing can drift by minutes (https://docs.railway.com/reference/cron-jobs).
  - Fit (INFERRED): run the long-lived orchestrator as a normal always-on Railway service, and scheduled QMX jobs as cron services.
  - Persistent volumes for SQLite sessions and transcripts: UNVERIFIED (page not fetched).
  - Claude's non-TTY hang (#926) applies to any container lane (A01 §3).

## Appendix B — Open items

- Measure an OpenAI-engine session's RAM and a Claude session's cold start on this PC before sizing the orchestrator host.
- Verify Anthropic `cache_control` and cache-write usage through `LitellmModel` with Opus 5.5.
- Verify GLM, DeepSeek and Kimi tool-calling and streaming on `OpenAIChatCompletionsModel` (`buffer_streamed_tool_calls`?).
- Check how long `can_use_tool` may block and whether Claude Code has an MCP tool-call timeout (shapes `qmx_delegate` wait vs poll).
  Confirm MiniMax, Ollama Cloud and OpenCode Zen endpoint formats and terms (MR §1).
