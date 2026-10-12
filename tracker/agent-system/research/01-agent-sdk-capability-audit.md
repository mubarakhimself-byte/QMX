# 01 — Claude Agent SDK as the base harness: capability audit

Ticket: `tracker/agent-system/tickets/01-agent-sdk-capability-audit.md`. Feeds ticket 02 (harness choice). Nothing here is ratified.
Researched 2026-10-12 from primary sources only. Doc pages were fetched as their `.md` form (for example
`https://code.claude.com/docs/en/llm-gateway.md`). A citation like `llm-gateway.md L17` means line 17 of that page as fetched today.
GitHub facts come from `gh api` on 2026-10-12. "UNVERIFIED" = not confirmed on a primary page. "INFERRED" = my reasoning from sourced facts.
The LangGraph + Deep Agents column relies on `rebuild/research/2026-10-12-agent-system/langchain-stack.md` (cited as LCS §x) rather than re-fetching.

Versions measured: `claude-agent-sdk` 0.2.165 (PyPI, 2026-10-08; bundles Claude Code CLI 2.1.294, CHANGELOG.md L3-7), MIT licence,
8,252 stars, 542 open issues (GitHub API). QMX pins: deepagents 0.7.22, langgraph 1.2.14, langchain 1.4.3 (LCS §0).

---

## 0. Bottom line in plain words

1. **The Agent SDK is Claude Code in a box.** Each agent session is a separate `claude` program that Python drives over a pipe.
   You get Claude Code's tools, sub-agents, hooks, skills, compaction and caching without building them.
2. **It can be pointed at other models, but Anthropic does not support that.** DeepSeek, Z.ai GLM, Kimi and OpenRouter
   publish Anthropic-style endpoints and their own Claude Code setup guides. GPT needs a translating proxy such as LiteLLM.
   Anthropic's own page says it does not support "routing Claude Code to non-Claude models through any gateway" (llm-gateway.md L17).
   Several features switch off or degrade away from Anthropic's servers (section 1).
3. **It is not a graph engine.** Claude Code's dynamic workflows are scripts that run many agents in the background.
   They do not stop mid-run for a human sign-off, keep no typed state and resume only inside the same session.
   The Lab node editor still needs LangGraph or something like it (section 2).
4. **So "the Agent SDK for every QMX agent" does not fit as-is.** It fits Claude-model copilots and heavy Claude workers well.
   It fits cheap non-Claude background agents poorly, and the Lab workflow graph not at all.
5. Ticket 02 decides. Section 8 sets out the three options and what each one costs.

---

## 1. Models: non-Claude models through `ANTHROPIC_BASE_URL`

**What works (evidence)**
- Claude Code treats any `ANTHROPIC_BASE_URL` host as the Claude API. It "can't tell which upstream you forward to"
  (llm-gateway-protocol.md L92). The SDK passes `env` into the CLI process, merged over the parent environment
  (python.md, `ClaudeAgentOptions.env`; transport source `src/claude_agent_sdk/_internal/transport/subprocess_cli.py` L814-825).
  **So each session (each process) can have its own base URL and key.**
- **DeepSeek:** `https://api.deepseek.com/anthropic`. Their Claude Code guide sets `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL=deepseek-flash[1m]`,
  the `ANTHROPIC_DEFAULT_*_MODEL` aliases and `CLAUDE_CODE_SUBAGENT_MODEL=deepseek-flash`. A PowerShell variant is given
  (https://api-docs.deepseek.com/guides/coding_agents). Unknown model names silently map to `deepseek-flash`.
  `claude-opus*` maps to `deepseek-v4-pro` (https://api-docs.deepseek.com/guides/anthropic_api).
- **Z.ai GLM:** `https://api.z.ai/api/anthropic` with `ANTHROPIC_AUTH_TOKEN` (https://docs.z.ai/scenario-example/develop-tools/claude).
  That page is written for the **GLM Coding Plan**, which models-routing.md §1 says QMX's own apps may not use. A general API key is needed.
  The page says its one-line setup script supports only macOS and Linux, not Windows.
- **Kimi:** the platform API offers an "Anthropic Messages API compatible" format for "Claude Code, and similar tools"
  (https://platform.kimi.ai/docs/guide/agent-support, quickstart section). The exact base URL was not captured: UNVERIFIED.
- **OpenRouter:** `ANTHROPIC_BASE_URL=https://openrouter.ai/api`, `ANTHROPIC_AUTH_TOKEN`, empty `ANTHROPIC_API_KEY`. Their page says it is
  "only guaranteed to work with the Anthropic first-party provider" (https://openrouter.ai/docs/guides/guides/claude-code-integration).
  So OpenRouter is a Claude failover route, not a way to run other models.
- **LiteLLM:** a published tutorial "Use Claude Code with Non-Anthropic Models" (OpenAI, Gemini, Azure, Vertex). LiteLLM translates
  `/v1/messages` to each provider (https://docs.litellm.ai/docs/tutorials/claude_non_anthropic_models).
- **GPT models:** only through a translating proxy (LiteLLM or similar). There is no OpenAI or "Sign in with ChatGPT" path in Claude Code.
  The connection methods are Anthropic Messages, Bedrock, Agent Platform and Foundry formats only (llm-gateway-protocol.md L43, L89-92).

**What breaks or degrades (evidence)**
- **Support:** "Anthropic … doesn't support routing Claude Code to non-Claude models through any gateway" (llm-gateway.md L17).
- **Thinking:** for unknown model IDs Claude Code sends `thinking: {"type":"adaptive"}` plus effort and context-management fields
  (llm-gateway-protocol.md L103, L216). DeepSeek accepts `thinking` and ignores `budget_tokens`. Of `output_config`, it supports only `effort`.
  It does not support `redacted_thinking` (DeepSeek anthropic_api page, compatibility table).
  - When the upstream rejects `thinking` or a thinking signature, Claude Code retries and disables it for the rest of the conversation
    (llm-gateway-protocol.md L230-231). That recovery depends on the upstream's exact error wording (L238). Whether DeepSeek, GLM or Kimi
    word their errors so it triggers is UNVERIFIED.
- **Caching:** DeepSeek ignores every `cache_control` marker and caches on its own (anthropic_api table). That is fine for cost
  (DeepSeek bills cache hits, models-routing.md §3), but Claude Code's 1-hour TTL and breakpoint control do nothing there.
  Through a gateway that drops `cache_control`, "the conversation bills as uncached input on every turn" (llm-gateway-protocol.md L221).
- **Beta headers:** DeepSeek ignores `anthropic-beta` on `/messages` (anthropic_api table). A capability whose body field arrives
  without its beta header gives hard 400s (llm-gateway-protocol.md L210). `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` stops most of them
  (L240-254). Whether DeepSeek, GLM or Kimi tolerate the leftover `context_management` and `defer_loading` fields is UNVERIFIED.
- **Tool search:** off by default whenever `ANTHROPIC_BASE_URL` is not first-party (feature-availability.md L37). Every MCP tool then
  loads upfront. QMX's large tool surface costs more context on non-Claude routes. INFERRED.
- **Built-in WebSearch:** an Anthropic server tool. It is unavailable on some providers (feature-availability.md L81, L230).
  Support on DeepSeek, GLM or Kimi is UNVERIFIED. QMX plans Firecrawl as its own tool anyway.
- **Context window:** unknown IDs are assumed 200K, or 1M with `[1m]`. Fix it with `CLAUDE_CODE_MAX_CONTEXT_TOKENS`; auto-compaction
  keys off that number (model-config.md L805-816; llm-gateway-protocol.md L113).
- **Cost numbers:** `total_cost_usd` comes from a bundled Claude price table. Other models show `costBasis: "unknown"` unless a
  `modelPricing` table is set (cost-tracking.md L16, L199; python.md L1753). QMX would supply prices.
- **Features Claude Code turns off off-first-party:** Remote Control, server-managed settings and more (feature-availability.md L219).
  Auto mode only runs on Claude models (feature-availability.md L235).
- **Prompts:** Claude Code's system prompt and tool descriptions are written for Claude. No primary source measures tool-use quality
  of DeepSeek, GLM or Kimi inside Claude Code: UNVERIFIED. QMX would need its own eval (models-routing.md V-12).
- **Compaction:** client-side. Claude Code sends a summarisation request with the same model and replaces the history with the summary
  (prompt-caching.md L174-176). It should work on any model that follows instructions (INFERRED). Summary quality on cheap models is UNVERIFIED.
- **Sub-agents:** they inherit the session's base URL. A sub-agent `model` is just a string sent to that same endpoint
  (python.md `AgentDefinition.model`; sub-agents.md L307). DeepSeek's own guide sets `CLAUDE_CODE_SUBAGENT_MODEL=deepseek-flash`,
  so non-Claude sub-agent IDs pass through.

**Different providers per sub-agent in one session?**
- Not directly: one process has one `ANTHROPIC_BASE_URL` (env is per process, transport L814-825).
- Yes through a router: put LiteLLM in front and let each model name route to a different provider
  (main model `claude-opus-5-5` to Anthropic, sub-agent `deepseek-v4-pro` to DeepSeek). Claude Code also sends a
  `x-claude-code-request-class` header (main / subagent / workflow / compaction / auxiliary) a router can use (llm-gateway-protocol.md L149-152).
- Caveats: `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` and context-window settings are per process, not per model (INFERRED).
  The `ANTHROPIC_DEFAULT_*_MODEL_SUPPORTED_CAPABILITIES` variables "have no effect behind an `ANTHROPIC_BASE_URL` gateway" (L224).
  The mixed-provider setup is unsupported by Anthropic (llm-gateway.md L17) and untested by me: UNVERIFIED end to end.
- Deep Agents does this natively: `SubAgent.model` takes any LangChain chat model per sub-agent (LCS §a8; models-routing.md §4.1).

---

## 2. Workflows and graphs: can Claude Code back the Lab node editor?

**What Claude Code offers for many agents**
- **Sub-agents** (Agent tool): defined in code (`AgentDefinition`: tools, model, skills, mcpServers, maxTurns, background, effort,
  permissionMode; python.md L1126-1166) or as `.claude/agents/*.md`. Foreground or background (sub-agents.md L895-917).
  Removing `Agent` from a sub-agent's tools stops it spawning more (sub-agents.md L508), which matches the cost rule "a sub-agent never spawns sub-agents".
- **Background agents and agent teams:** separate sessions with a shared task list and messaging (agents.md; agent-teams.md).
  These are mainly interactive-CLI features.
- **Dynamic workflows:** a JavaScript script run by a background runtime: `agent()`, `parallel()`, `pipeline()`, JSON-schema outputs,
  a per-agent `model` (workflows.md L13, L313). Up to 16 concurrent agents by default (max 256), 4,096 items per `parallel()`,
  1,000 agents per run (L357-366).
  - Reachable from the SDK: allow the `Workflow` tool. Its input takes `script`, `name`, `scriptPath`, `args`, `resumeFromRunId`
    (typescript.md L3263-3275). Saved scripts live in `.claude/workflows/` or a plugin (workflows.md L200-226).
  - Cookbook: `D:\QMX-research\sources\repos\claude-cookbooks\claude_agent_sdk\08_Dynamic_workflows.ipynb` (cells 1, 8, 16).
    It needs CLI ≥ 2.1.154, which SDK ≥ 0.2.90 bundles.
- **Hooks:** deterministic code at tool, prompt, stop, sub-agent and compaction points (section 5).

**Limits that matter for a node editor (evidence)**
- "No mid-run user input". A run pauses only for permission prompts or a usage-limit wait. "For sign-off between stages,
  run each stage as its own workflow" (workflows.md L360).
- Resume replays by start order. A failed or edited agent reruns itself **and every agent after it**, even completed ones (workflows.md L384-394).
- Results persist under the session directory. Resume works "within the same Claude Code session" (L396-404).
- No filesystem, shell or module imports in the script itself (L361-362). `Date.now()` and `Math.random()` throw (L334).
- Who writes the plan: normally Claude writes the script. A host can pass `script` or `scriptPath` but must still ask the model to call the tool
  (cookbook cell 8). A deterministic, host-triggered run is UNVERIFIED.

**Against LangGraph `StateGraph`** (LCS §a2, §a5, §d)
- Typed state channels, conditional edges, `interrupt()` human gates with resume on the same thread.
- Checkpointers (SQLite or Postgres) keep each node's output across process restarts. Per-node timeouts, error handlers and graceful drain.
- Any model per node.
- QMX already has a compiler from its 10 node kinds to LangGraph with `human_gate = interrupt` (P10, `qmx_agents/workflows/compiler.py`,
  375 lines). It is not yet reachable through the API (`qmx-internal.md` §d).

**Verdict:** Claude Code workflows are a strong fan-out tool (research sweeps, cross-checked review). They cannot back a visual node editor
with typed nodes, durable checkpoints and human gates. QMX would keep LangGraph (or a QMX-owned runner) for Lab graphs either way.
An Agent SDK session can be one **node kind** inside such a graph (INFERRED, the Sandcastle pattern in section 7).

---

## 3. Lifecycle

- **Sessions:**
  - Create; continue the most recent; resume by ID; fork to a new ID (sessions.md L26-41, L215-310).
  - Branch from an earlier message with `resume_session_at` (python.md options table, SDK ≥ 0.2.137).
  - `list_sessions()`, `get_session_messages()`, `get_session_info()`, `rename_session()`, `tag_session()`, `fork_session()` (python.md L254-495).
  - Stored as JSONL under `~/.claude/projects/<encoded-cwd>/`, or under `$CLAUDE_CONFIG_DIR/projects/` (sessions.md L272).
    "Same machine only" unless a `SessionStore` adapter mirrors transcripts (L281-286; session-storage.md).
  - Forking copies history, not files (sessions.md L293). File rewind needs `enable_file_checkpointing`.
- **Concurrency and cost:**
  - "One agent session maps to one subprocess. Running N concurrent sessions means N subprocesses" (hosting.md L23).
  - Sizing: "1 GiB RAM, 5 GiB disk, and 1 CPU per agent is a reasonable starting point"; memory grows with session length (L210).
    Hosts are bounded by RAM: agents per host = (RAM − overhead) / per-session peak (L260-268).
  - Sub-agents and workflow agents run inside their parent session (INFERRED from hosting.md L23 and workflows.md L357; not measured).
  - Python has no pre-warm or `startup()`; that is TypeScript-only (hosting.md L120-125). Each new session pays a process cold start (size not measured: UNVERIFIED).
  - Open issue #1035 asks for warm-subprocess reuse (GitHub).
  - The Windows x64 wheel is 105 MB because it bundles `claude.exe` (PyPI JSON, 0.2.165).
  - For comparison, Deep Agents sessions are objects in one Python process sharing a checkpointer (LCS §b.3).
- **Streaming to a custom UI:**
  - Assistant, user, system and result messages; token-level `StreamEvent` with `include_partial_messages` (python.md L1755).
  - `TaskStarted`, `TaskProgress` and `TaskNotification` messages for background sub-agents, shells and workflows, with usage (L1845-1936).
  - Hook events in the stream with `include_hook_events`; sub-agent text with `forward_subagent_text`.
  - `RateLimitEvent`. A `compact_boundary` system message after compaction (agent-loop.md L57, L270).
- **Interrupt and steer:** `ClaudeSDKClient.interrupt()`, `set_model()`, `set_permission_mode()`, `stop_task(task_id)` (python.md L498-541).
  Streaming input queues messages that "process sequentially, with ability to interrupt" (streaming-vs-single-mode.md L27).
  Injecting a message mid-turn without interrupting is UNVERIFIED.
- **Windows:**
  - Supported. The x64 wheel bundles `claude.exe`. The SDK refuses npm's `claude.cmd` shim for command-injection safety (troubleshooting.md L50-67).
  - Open Windows issues: #480 (console window flashes on spawn), #883 (long system prompt overflows the Windows command line;
    a `SystemPromptFile` exists, python.md L1004), #902 (MCP tools fail to register on Windows), #1239 (import hang under a TS watcher).
  - `requires-python >=3.10` and the wheel is `py3-none`, so Python 3.14 installs (pyproject.toml; PyPI).
- **Linux server or Docker:** first-class. The hosting page covers ephemeral, long-running, hybrid and multi-agent container patterns
  (hosting.md L71-181), and the cookbook ships Docker, Modal and Kubernetes code (`claude_agent_sdk/hosting/`, `07_Hosting_the_agent.ipynb`).
  - Open issue #926: the bundled binary hangs when stdout is not a TTY (pipe, cron, Docker).
  - Issue #1110: `query()` hangs forever if the CLI dies mid-run. Both matter for 24/7 agents.
- **Headless sign-in:**
  - `claude setup-token` mints a one-year OAuth token for `CLAUDE_CODE_OAUTH_TOKEN`; it needs Pro, Max, Team or Enterprise (authentication.md L276-306).
  - That token "can only make model requests": no Remote Control, no claude.ai connectors (L306; claude-code-features.md L95).
  - Sandcastle uses exactly this (README L42). API keys are the documented route for products (section 6).

---

## 4. Isolation from the operator's own Claude Code on the same PC

| Lever | What it isolates | Evidence |
|---|---|---|
| `setting_sources=[]` | Skips user, project and local `settings.json`, CLAUDE.md, rules, `.claude/` skills, agents, commands and filesystem hooks. Python ≤ 0.1.59 ignored an empty list | python.md L1019-1110; claude-code-features.md L11, L78 |
| `CLAUDE_CONFIG_DIR` in `env` | Moves `~/.claude.json`, settings, session history, plugins, saved workflows and `.credentials.json` (separate login) | env-vars.md L430; authentication.md L37, L205; workflows.md L205 |
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` | Auto memory loads "regardless of settingSources" otherwise | claude-code-features.md L94; hosting.md L283 |
| `strict_mcp_config=True` | Only the MCP servers QMX passes; ignores `.mcp.json`, user, plugin and claude.ai connectors | python.md options table; claude-code-features.md L95 |
| `plugins=[...]` | SDK loads only local-path plugins you list. Marketplace plugins from the operator's settings stay out when `user` is not a source (INFERRED) | plugins.md L18-22 |
| `hooks=` callbacks | Programmatic hooks run in QMX's process. Filesystem hooks load only with their setting source | claude-code-features.md L180-187 |
| `permission_mode`, `allowed_tools`, `disallowed_tools`, `can_use_tool` | Per session | python.md L812-920 |
| Not removable | Managed policy (MDM/registry), and the `sandbox.credentials` deny/mask entries in `~/.claude/settings.json` | claude-code-features.md L86-99 |

Two warnings:
- The docs say not to rely on defaults for isolation (claude-code-features.md L99).
- The SDK strips `CLAUDECODE` from the inherited environment (transport L818-820). But if QMX is launched from inside the operator's
  Claude Code session, other inherited variables such as `ANTHROPIC_*` and `CLAUDE_CODE_*` still pass through unless QMX scrubs them (INFERRED).
  QMX should build each session's env explicitly.
- Auth precedence order: `ANTHROPIC_AUTH_TOKEN`, then `ANTHROPIC_API_KEY`, then `apiKeyHelper`, then `CLAUDE_CODE_OAUTH_TOKEN`, then `/login`
  (authentication.md L229-240). A leaked operator variable changes who pays.

---

## 5. Tools, hooks, permissions, compaction, caching, usage

- **In-process custom tools:** `@tool(name, description, input_schema)` plus `create_sdk_mcp_server()`. They run in QMX's Python process
  with no separate MCP server (python.md L88-245; custom-tools.md). `ToolAnnotations` carry read-only and destructive hints (L169).
  This matches "tools are mostly local QMX code". They are surfaced to the model as `mcp__<server>__<tool>` names.
- **Hooks (Python):** `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `UserPromptSubmit`, `Stop`, `SubagentStart`, `SubagentStop`,
  `PreCompact`, `Notification`, `PermissionRequest` (python.md L2090-2108).
  - TypeScript-only: `SessionStart`, `SessionEnd`, `PostCompact`, `PostToolBatch`, `PreModelSwitch`, `TaskCreated`, `TaskCompleted`,
    `ConfigChange` and more (hooks.md L145-181).
  - Decisions: `permissionDecision` allow, deny, ask or defer; `updatedInput`; `additionalContext`; `updatedToolOutput`; `continue_=False`
    to stop; async hooks (python.md L2405-2498).
  - Filesystem hooks also offer `http`, `prompt` and `agent` types, firing in sub-agents too (claude-code-features.md L276).
  - Fit for QMX: the money-path guard (`guards/money_path.py`) maps onto a `PreToolUse` deny hook plus `disallowed_tools` scoped rules,
    which deny "in every permission mode, including `bypassPermissions`" (python.md options table) (INFERRED).
- **Approvals:** `can_use_tool(tool_name, input, context)` returns allow (optionally with `updated_input`) or deny. It is called only when
  the permission flow falls through to a prompt (python.md L1197-1290; user-input.md).
  `AskUserQuestion` reaches the host the same way (user-input.md). A background sub-agent's prompts surface in the parent (sub-agents.md L913).
- **Compaction:**
  - Automatic near the window. History is replaced by one summary from the same model (agent-loop.md L268-278; prompt-caching.md L174-176).
    That is the "summary-only" shape LCS §a10 calls safe for Opus 5.5 preserved thinking. Deep Agents' default keeps a verbatim tail, which LCS flags unsafe.
  - Controls: `CLAUDE_CODE_AUTO_COMPACT_WINDOW` (100K-1M), `DISABLE_AUTO_COMPACT`, `DISABLE_COMPACT`, a "what to keep" section in CLAUDE.md,
    the `PreCompact` hook (archive before summary), and `/compact` sent as a prompt (env-vars.md L220, L445-446; agent-loop.md L274-278).
  - No custom summariser function and no keep-tail option (UNVERIFIED that none exists; none documented).
  - Open issues #531 (no mid-loop compaction during custom MCP tool batches) and #772 (lifecycle hooks for compaction thresholds).
- **Caching:** automatic `cache_control` on system and messages (llm-gateway-protocol.md L221). TTL 5m or 1h via `CLAUDE_CODE_PROMPT_CACHE_TTL`
  and `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL`. Disable switches exist (env-vars.md L365, L401, L458-469).
  `exclude_dynamic_sections` moves per-user context out of the system prompt for cross-session reuse (python.md L966-985).
  Workflow fan-outs share a prefix and stagger first requests (workflows.md L347-353).
- **Usage and cost:**
  - Per step: `AssistantMessage.usage` and `message_id`. Per call: `ResultMessage.total_cost_usd`, plus `model_usage` per model,
    including sub-agents, compaction and workflow agents (cost-tracking.md L27-98; python.md L1734).
  - The top-level `usage` excludes sub-agents (cost-tracking.md L96). Costs are client-side estimates, "not authoritative billing data" (L16).
  - `max_budget_usd` and `task_budget` caps (python.md options table). `RateLimitEvent` covers plan limits. OpenTelemetry export (hosting.md L234-250).
  - Open issue #435: "20-70% of concurrently ran chats fail to provide usage data and StreamEvents". It is directly relevant to a T3-style usage page.

---

## 6. Terms (quotes under 15 words)

- Agent SDK overview note: Anthropic does "not allow third party developers to offer claude.ai login or rate limits"
  for products built on the SDK. It points to API keys instead (https://code.claude.com/docs/en/agent-sdk/overview).
- Legal page: "Anthropic does not permit third-party developers to offer Claude.ai login into their own applications"
  (https://code.claude.com/docs/en/legal-and-compliance). The same page says developers using the Agent SDK "should use API key authentication".
- The same page allows an end user signing in to the **unmodified** binary with their own subscription. It also says plan limits
  "assume ordinary, individual usage of Claude Code and the Agent SDK".
- Read for QMX (INFERRED, not legal advice):
  - QMX has one user, who is also its developer. Running the SDK's bundled, unmodified binary signed in with his own plan
    (separate `CLAUDE_CONFIG_DIR`, his own `/login` or `setup-token`) is the closest fit to the allowed case.
  - Using that plan for every always-on QMX agent stretches "ordinary, individual usage". models-routing.md §4.4 already flags this as a grey zone.
  - API keys are the clean route for 24/7 and server agents. Non-Claude providers fall under their own API terms; coding plans such as the
    GLM Coding Plan are excluded (models-routing.md §1).
  - Branding: the product must not appear to be Claude Code (overview, branding section).

---

## 7. Maturity, and how the reference projects drive Claude Code

**Cadence and breakage**
- About 60 Python releases from 2026-07-21 to 2026-10-08, every 1-4 days. Most only bump the bundled CLI (GitHub releases; CHANGELOG.md).
- Two "Breaking Changes" sections in the changelog. 0.1.0 renamed Claude Code SDK to Agent SDK (L1400-1406). 0.2.129 made malformed skill names
  raise `ValueError` (L261).
- Behaviour changes ride in the bundled CLI and are documented as per-version notes ("Requires Claude Code v2.1.x").
  Pin the SDK exactly and treat every bump as a CLI upgrade (INFERRED).
- `Transport` is marked "a low-level internal API. The interface may change" (python.md L771).
- Python lags TypeScript on hooks and pre-warm (section 5; hosting.md L122).

**Open issues that would bite QMX** (GitHub, open on 2026-10-12)
- #1110: `query()` hangs if the CLI dies mid-run.
- #926: hang when stdout is not a TTY (cron, Docker).
- #1162: CLI version check can hang.
- #576: `ClaudeSDKClient` hangs when reused across FastAPI request tasks. `qmx-control` is FastAPI.
- #435: missing usage under concurrency.
- #889: `close()` does not reap MCP grandchildren.
- #434: memory spike spawning helper processes.
- #902, #883 and #480: Windows (section 3).
- #531: compaction gap.
- Mitigations exist (`CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK`, a watchdog per session) but each is QMX work.

**Reference projects (all MIT, TypeScript)**
- **T3 Code** (pingdotgg/t3code, `apps/server/src/orchestration-v2/Adapters/ClaudeAdapterV2.ts`, 9,304 lines):
  - Uses the TS Agent SDK `query()` with the `claude_code` preset plus an appended T3 block (L1052-1058), `includePartialMessages: true` (L1015),
    `canUseTool`, `resume`, `resumeSessionAt` and `forkSession` (L20, L1022-1025), and adaptive thinking with summaries (L1029-1031).
  - Sets per-provider `env`, including `CLAUDE_CONFIG_DIR` (L4740-4745, L1050). It is one adapter among several harnesses (Codex etc.).
- **bb** (get-bb/bb, `plugins/provider-claude-code`): a plugin depending on `@anthropic-ai/claude-agent-sdk ^0.3.245` (package.json).
  - Its overview exposes permission modes, Ultracode workflows, checkpoint forks, manual compaction and native questions.
  - Settings can disable the native Task tool "so the agent delegates through bb", and the Workflow tool (PLUGIN_OVERVIEW.md).
  - It reads the host's own `claude` sign-in.
  - Claude Code is one provider next to Codex, Pi, Hermes and ACP agents (harnesses.md §4).
- **Sandcastle** (mattpocock/sandcastle, `src/AgentProvider.ts`): no SDK.
  - It shells out `claude --print --verbose --output-format stream-json --model … [--resume] [--fork-session] -p -` (L1213)
    inside Docker or Podman sandboxes.
  - Auth is `CLAUDE_CODE_OAUTH_TOKEN` from `setup-token` or an API key (README L42).
  - `AgentProvider` is a small interface (`buildPrintCommand`, `parseStreamLine`, `sessionStorage`, L264-277) with `codex()`, `pi()`,
    `cursor()` and `copilot()` peers. This is the "harness = swappable provider" pattern.
- Common pattern: none of the three makes Claude Code its universal base. All three put it behind an adapter next to other harnesses.

---

## 8. Capability table: Agent SDK vs LangGraph + Deep Agents

Verdict key: **SDK** = the Agent SDK is clearly better for QMX; **LG** = LangGraph + Deep Agents clearly better; **≈** = comparable; **gap** = neither is enough alone.

| # | Capability | Claude Agent SDK (Python 0.2.165) | LangGraph + Deep Agents (QMX pins) | Verdict |
|---|---|---|---|---|
| 1 | Claude models | Native: adaptive thinking, effort, summary-only compaction, caching, tool search | Native through `ChatAnthropic` plus caching middleware; keep-tail summarisation unsafe for Opus 5.5 until replaced (LCS §a10) | SDK |
| 2 | DeepSeek / GLM / Kimi | Via their Anthropic endpoints; unsupported by Anthropic; caching markers ignored; some features off (§1) | Native provider classes (`ChatDeepSeek`, OpenAI-compatible) (models-routing §4.1) | LG |
| 3 | GPT models | Only via LiteLLM-style translator | Native `ChatOpenAI` Responses API with reasoning replay | LG |
| 4 | Different provider per sub-agent | Only through a routing gateway; one base URL per process | `SubAgent.model` per sub-agent, any provider | LG |
| 5 | Built-in tools (shell, files, web, edit, todo, sub-agents) | Full Claude Code set, tuned and maintained by Anthropic | fs tools, `execute` via a backend QMX builds, `task`; shell or web are QMX's job (LCS §a1, §a3) | SDK |
| 6 | In-process custom tools | `@tool` + SDK MCP server, `mcp__` names | Plain Python tools | ≈ |
| 7 | Hooks | 10 Python events; allow/deny/ask/defer, input rewrite, output rewrite | Middleware wraps model and tool calls; any logic (LCS §b) | ≈ (SDK closer to what the operator likes; LG more flexible) |
| 8 | Approvals | `can_use_tool`, `AskUserQuestion`, permission modes, scoped deny rules | `interrupt_on` approve/edit/reject/respond, `interrupt()`; checkpoint needed (LCS §a5) | ≈ |
| 9 | Compaction | Automatic summary-only (thinking-safe); window, off switches, PreCompact; no custom summariser | Configurable middleware, keep-tail default (unsafe on Opus 5.5), server-side option via ChatAnthropic | SDK for Claude; LG for others |
| 10 | Prompt caching | Automatic, 5m/1h, workflow prefix sharing | Automatic per provider (LCS §a11) | ≈ |
| 11 | Usage and cost | Per step and per model incl. sub-agents; estimates; Claude price table; issue #435 | `usage_metadata` per call into QMX's own ledger and price table (models-routing §5) | ≈ |
| 12 | Sub-agents | Agent tool, background, fork mode, per-agent tools/model/skills/MCP | `task`, isolated or fork, async sub-agents need an Agent Protocol server (LCS §a2, §a8) | SDK |
| 13 | Many-agent fan-out | Dynamic workflows (16 to 256 concurrent, 1,000 per run) | Hand-built `Send`/map-reduce or interpreter-dynamic sub-agents (beta) | SDK |
| 14 | Lab node editor (typed state, durable checkpoints, human gates, any model per node) | No: no mid-run input, same-session resume, no typed state | `StateGraph` + checkpointer + `interrupt()`; QMX P10 compiler exists | LG |
| 15 | Sessions: resume, fork, list | Yes; JSONL per machine; `SessionStore` for other hosts | Threads in a checkpointer; fork by checkpoint; any host with the DB | ≈ |
| 16 | Many concurrent sessions | One process each, ~1 GiB floor; no Python pre-warm | Objects in one process | LG |
| 17 | Streaming to a custom UI | Rich typed messages, partial tokens, task progress | `stream_events` v3 typed projections (beta) | ≈ |
| 18 | Interrupt / steer | `interrupt()`, queued input, `set_model`, `stop_task` | Interrupt by run control; resume with `Command` | ≈ |
| 19 | Windows desktop | Supported; bundled `claude.exe`; open Windows issues | Pure Python; QuickJS interpreter lacks a cp314 Windows wheel (LCS §a9) | ≈ |
| 20 | Linux server / Docker | First-class hosting guide and cookbook; TTY-hang issue #926 | Library anywhere; Agent Server licence-gated (LCS §a3) | SDK |
| 21 | Scheduling (cron) | None in the SDK (routines are a cloud product) | None open-source (LCS §a4) | gap: QMX builds it either way |
| 22 | Isolation from the operator's Claude Code | `setting_sources=[]`, `CLAUDE_CONFIG_DIR`, strict MCP, auto-memory off; managed policy leaks through | Nothing shared by default | LG (simpler) |
| 23 | Skills | Agent Skills, plugins, slash commands | Agent Skills spec, skill-bound tools (LCS §a7) | ≈ |
| 24 | Memory | CLAUDE.md + auto memory (files) | Store + file backends, namespaces (LCS §a6); QMX `memory.py` built | LG (QMX already built on it) |
| 25 | Computer use / browser | Via MCP (Claude in Chrome needs claude.ai login, per bb overview) | Via MCP or QMX tools | ≈ |
| 26 | Subscription use | Legitimate only as the unmodified binary under the operator's own sign-in; grey zone at scale (§6) | Not allowed (models-routing §1) | SDK |
| 27 | Release risk | Bundled CLI moves every few days; Transport internal | Deep Agents 0.x patches every 1-5 days; betas (LCS §e) | ≈ |
| 28 | Fit with code already shipped | ~4,060 lines in qmx-agents, tools and remote import LangChain/LangGraph (§9) | Zero rewrite | LG |

---

## 9. The three harness options from ticket 02, and what each costs QMX

LangChain-coupled code today (`D:\QMX-worktrees\agent-system\qmx-agents\packages`, grep for langchain|langgraph|deepagents):
- `spec.py` 499, `memory.py` 678, `router.py` 322, `copilot.py` 213, `workflows/compiler.py` 375, `workflows/runs.py` 124, `tasks.py` 152.
- `guards/{middleware 237, money_path 279, admission 277, hooks 179}`, `research.py` 60.
- `qmx_tools/registry.py` 281, `qmx_remote/worker.py` 385.
- About 4,060 lines in total.

Harness-neutral and kept in every option: qmx-control (FastAPI and FastMCP), qmx-apps (mini-app runtime, Docker tier), qmx-broker,
the library and run index, journal, and the money-path rules themselves (the logic, not the LangChain wrapper). `qma-daemon` is being retired (P16) regardless.

**Option A: the Agent SDK is the base for every agent**
- What changes:
  - `spec.py`/`copilot.py` become builders of `ClaudeAgentOptions`.
  - `router.py` becomes per-session env plus a LiteLLM gateway for non-Claude models, a new always-on service with its own config.
  - `guards/middleware.py` becomes hooks plus `can_use_tool`, and `qmx_tools/registry.py` becomes an SDK MCP server.
  - `memory.py` (Store-based) becomes files and a memory MCP tool, or is re-hosted.
  - `tasks.py` and `qmx_remote/worker.py` re-target to SDK processes.
- What has no home: the P10 workflow compiler (LangGraph). Either LangGraph stays for the Lab, so this option collapses into C,
  or Lab graphs are rewritten as workflow scripts and lose human gates and durable checkpoints (§2).
- Costs:
  - Most of the ~4,060 lines are rewritten.
  - DeepSeek, GLM and GPT background agents run on an Anthropic-unsupported path with Claude-tuned prompts; quality UNVERIFIED.
  - One process per session, so 24/7 agents and many sessions cost RAM (~1 GiB floor each).
  - Python lags TypeScript on hooks. Open hang issues need QMX watchdogs.
- Gains:
  - Claude-Code-level tools, sub-agents, workflows, compaction and caching on day one, which matches the operator's stated preference.
  - The Opus 5.5 compaction problem (LCS §a10) disappears on Claude routes.

**Option B: LangGraph + Deep Agents is the base; Claude Code (Agent SDK or `claude -p`) is a swappable worker node (the Sandcastle pattern)**
- What changes: one new adapter, `engine:claude-code`. It maps a QMX job to `ClaudeAgentOptions`, the SDK stream to QMX's event protocol
  (ticket 11), and `can_use_tool`/hooks to QMX approvals. models-routing.md §4.4 already sketches it. Codex can be a second worker of the same shape.
- Costs:
  - QMX must still build Claude-Code-level capability into Deep Agents for every non-worker agent: shell or sandbox backend, web, computer use.
  - QMX must fix keep-tail summarisation on Claude routes (LCS §d BUILD 2).
  - Copilots on Deep Agents will not feel exactly like Claude Code. The worker's sessions sit in a separate store that QMX must index for the UI.
- Shipped code: kept, about 0 lines rewritten. The worker adapter is new (T3's is 9k lines in TS; a minimal Python one is far smaller, size UNVERIFIED).

**Option C: split by agent type**
- One possible split (INFERRED, not a decision):
  - Interactive copilots on Claude, plus heavy Lab coding and research jobs: Agent SDK sessions (API key, or the operator's own sign-in for his own jobs).
  - Lab node-editor workflows: LangGraph `StateGraph`, keeping P10. Agent SDK sessions and Deep Agents can both be node kinds.
  - Cheap background and server agents on DeepSeek, GLM or GPT: Deep Agents with native provider classes.
- What changes:
  - `copilot.py` and part of `spec.py` move to an SDK builder.
  - `qmx_tools` is exposed twice: as LangChain tools, and as one SDK MCP server from the same registry. P11 already runs FastMCP, so this is cheap (INFERRED).
  - Money-path guards must exist as both middleware and a `PreToolUse` hook, fed by the same rule code and tested on both.
  - The UI event protocol (ticket 11) normalises two streams.
  - The usage ledger reads SDK `model_usage` and LangChain `usage_metadata`.
- Costs: two harnesses to upgrade and two hook or approval systems to keep identical. A copilot cannot hand a thread to a non-Claude model
  mid-conversation, which models-routing §6 forbids anyway.
- Shipped code: P10 (workflows), P07 (memory), P09 (tools) and P08 (guards) kept. P06 router and P15 copilot partly reworked.

---

## 10. Verdict (plain words, not ratified)

- **Can the Agent SDK be the base for every QMX agent?** Technically it can start any agent, but it is not a good base for all of them.
- **It is the best tool QMX can get for Claude-model agents.** It gives Claude Code's own tools, sub-agents, hooks, safe compaction, caching
  and fan-out workflows, with no harness code to write.
- **It is a weak base for non-Claude models.** That path works through vendor endpoints and LiteLLM, but Anthropic says it does not support it.
  Caching control, tool search, web search and some betas drop out, and the prompts are tuned for Claude.
- **It cannot be the Lab's workflow engine.** It has no human gates mid-run, no durable typed state and resumes only in the same session.
  QMX keeps LangGraph (or its own runner) for graphs in any option.
- **The evidence points away from option A.** The real choice for ticket 02 is between B (LangGraph base, Claude Code as a worker)
  and C (Agent SDK for Claude copilots and heavy jobs, LangGraph for Lab graphs and cheap background agents).
- **C costs a second harness. B costs building Claude-Code-like tools in Deep Agents.**
- **Before choosing, measure three things:**
  - real per-session RAM and cold start of an SDK session on the operator's Windows PC;
  - whether DeepSeek V4 Pro through `api.deepseek.com/anthropic` completes a 10-turn tool task in an SDK session with
    `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1`;
  - whether `setting_sources=[]` plus a QMX `CLAUDE_CONFIG_DIR` keeps the operator's own hooks, plugins and memory out of a QMX session.

---

## 11. Open and UNVERIFIED items

1. Kimi's exact Anthropic base URL and its handling of `thinking`, `context_management` and `defer_loading`. The same applies to DeepSeek and GLM.
2. Whether the thinking or capability-rejection retry (llm-gateway-protocol.md L230-238) triggers on non-Anthropic error wording.
3. Tool-use quality of DeepSeek V4 Pro, GLM-5.3 and Kimi K3 inside Claude Code's prompt. No primary benchmark exists; QMX eval needed.
4. Per-session RAM, CPU and cold start on Windows (hosting.md gives only a container starting point).
5. Whether a host can launch a saved workflow deterministically without the model choosing to call the `Workflow` tool.
6. Whether Anthropic regards one operator's QMX dispatching many SDK sessions on his own plan as "ordinary, individual usage".
   Ask Anthropic in writing (models-routing.md §10 item 1).
7. Mid-turn message injection without `interrupt()`.
8. Whether marketplace plugins enabled in the operator's user settings load when `setting_sources` omits `user` (believed no, INFERRED).

Consistency with earlier research:
- `models-routing.md` §1 and §4.4 match the legal and overview pages fetched today.
- `langchain-stack.md` §a10 (keep-tail compaction unsafe on Opus 5.5) is unaffected. Claude Code's own compaction is summary-only (prompt-caching.md L174-176).
- No corrections needed.
