# QMX agent layer: what the LangChain stack gives us (LangChain v1 + LangGraph + Deep Agents + LangSmith)

Researched 2026-10-12 from primary sources. Every claim carries a URL or a local path.
Local copies of every page cited live under `D:\QMX-research\sources\langchain\` (docs as `.md`, blog posts under `blog\md\`,
release notes under `releases\`). Dense per-page extraction notes: `D:\QMX-research\notes\deepagents-core.md`,
`deepagents-extensions.md`, `langchain-langgraph-core.md`.
"UNVERIFIED" = not confirmed in a primary source or not tested against the pinned code. "INFERRED" = my reasoning from sourced facts.

Docs index used: https://docs.langchain.com/llms.txt -> https://docs.langchain.com/_llms/agent-development-lifecycle/build/python.txt
(saved as `sources\langchain\idx_*.txt`). There is no standalone "harness" page; harness content is spread across
`deepagents/overview`, `customization`, `context-engineering`, `profiles` (the blog still links a dead `/deepagents/harness` URL,
e.g. https://www.langchain.com/blog/autonomous-context-compression).

---------------------------------------------------------------------------------------------------

## 0. Pinned versions vs. what the docs describe

Source: `C:\Users\Mubarak\Desktop\QMX-worktrees\rebuild\qmx-agents\uv.lock` (branch `rebuild/base`),
`qmx-agents\packages\qmx-agents\pyproject.toml`, `qmx-agents\packages\qma-daemon\pyproject.toml`. Root `uv.lock` has no LangChain packages.
Latest versions from https://pypi.org/pypi/<pkg>/json (fetched 2026-10-12).

| Package | QMX pin | Latest (date) | Gap |
|---|---|---|---|
| deepagents | 0.7.22 (2026-10-05) | 0.7.24 (2026-10-12) | Missing `pinned_skills` (0.7.23) and async-subagent fork mode (0.7.24) |
| langchain | 1.4.3 (`langchain[mcp]`) | 1.4.4 (2026-10-08) | patch |
| langchain-core | 1.6.7 | 1.6.9 | patch |
| langgraph | 1.2.14 | 1.2.14 | none |
| langgraph-checkpoint / -sqlite | 4.2.0 / 3.1.1 | 3.1.1 (sqlite) | none |
| langgraph-prebuilt / langgraph-sdk | 1.1.0 / 0.4.6 | n/a | n/a |
| langchain-anthropic | 1.7.5 | 1.7.5 (2026-09-29) | none |
| langchain-openai | 1.6.7 | 1.7.0 (2026-10-08) | minor; changelog not read (UNVERIFIED what changed) |
| langsmith (SDK) | 0.14.4 | 0.14.7 | patch |
| langgraph-api / langgraph-cli / langgraph-runtime-inmem | NOT installed | 0.16.0 / 0.4.33 / 0.36.0 | Agent Server not in the stack at all |
| langchain-quickjs (interpreter) | NOT installed | 0.3.8 | interpreters / dynamic subagents / RLM unavailable |
| langgraph-checkpoint-postgres | NOT installed | n/a | SQLite only |
| langmem | NOT installed | 0.0.30 (2025-10-27) | n/a |
| mcp / fastmcp | 2.3.0 / 4.0.11 | n/a | `langchain.mcp` MCPAdapter path in use |

Python: QMX requires `>=3.14,<3.15` (`qmx-agents\packages\qmx-agents\pyproject.toml`).

Version floors the docs state, checked against the pins (all from the sources named; release list in
`sources\langchain\releases\deepagents-releases.md`, from https://github.com/langchain-ai/deepagents/releases):
- langgraph >= 1.2: DeltaChannel, per-node timeouts, node error handlers, graceful drain, `stream_events(version="v3")`
  (https://docs.langchain.com/oss/python/releases/changelog, entry "May 12, 2026 langgraph v1.2.0"). SATISFIED.
- langgraph >= 1.2.12: `interrupt(..., response_schema=...)` (https://docs.langchain.com/oss/python/langgraph/interrupts). SATISFIED.
- deepagents >= 0.6: harness profiles, CodeInterpreterMiddleware, DeltaChannel for messages/files, ContextHubBackend (changelog "May 12, 2026 deepagents v0.6.0"). SATISFIED.
  Warning in the same entry: rolling back below 0.6 after threads persist is NOT supported (DeltaChannel checkpoint format).
- deepagents >= 0.6.5 RubricMiddleware; >= 0.6.8 permission `interrupt` mode; >= 0.7.13 forked subagents; >= 0.7.16 skill reload;
  >= 0.7.21 binary offload; >= 0.7.22 skill-bound tools (`metadata.include_tools`) (notes `deepagents-extensions.md`, citing
  https://docs.langchain.com/oss/python/deepagents/skills, /subagents, /rubric, /permissions). SATISFIED.
- deepagents >= 0.7.23: `pinned_skills` (https://docs.langchain.com/oss/python/deepagents/skills#pin-skills; release
  https://github.com/langchain-ai/deepagents/releases tag `deepagents==0.7.23`, PR #6810). NOT SATISFIED by 0.7.22.
- deepagents 0.7.24: fork mode for async subagents (PR #6739), parent rubric preserved in parallel subagent calls (PR #6849). NOT SATISFIED.
- langchain >= 1.3.3 conditional HITL `when`; >= 1.3.14 ToolErrorMiddleware; >= 1.3.15 trace policy; >= 1.3.16 retry defaults;
  >= 1.4.0 `langchain.mcp` (beta) (https://docs.langchain.com/oss/python/langchain/middleware/built-in, /releases/changelog). SATISFIED.
- langchain-anthropic >= 1.3.0 server-side compaction; >= 1.4.0 automatic caching; >= 1.5.3 `reasoning_effort`;
  >= 1.7.3 mid-conversation system messages; >= 1.7.4 mid-conversation tool changes
  (https://docs.langchain.com/oss/python/integrations/chat/anthropic, saved `integrations\chat-anthropic.md`). SATISFIED.

---------------------------------------------------------------------------------------------------

## a. What the stack gives us out of the box

### a1. Copilot harness (interactive, Claude-Code-like)

- `create_deep_agent(model, tools, *, system_prompt, middleware, subagents, skills, memory, permissions, backend, interrupt_on,
  response_format, state_schema, context_schema, checkpointer, store, name, cache)` returns a compiled LangGraph graph
  (https://docs.langchain.com/oss/python/deepagents/customization).
- Default middleware stack, in order: Filesystem -> SubAgent -> Summarization -> PatchToolCalls -> [AsyncSubAgent] -> your middleware
  -> harness-profile extras -> Skills -> Anthropic + Bedrock prompt caching -> Memory -> HumanInTheLoop -> excluded-tool filter
  (https://docs.langchain.com/oss/python/deepagents/customization#deep-agents-stack).
- Built-in tools: `ls`, `read_file` (paginated, multimodal incl. PDF/audio/video), `write_file`, `edit_file`, `delete`, `glob`, `grep`,
  `execute` (sandbox backends only), `task` (subagents). `write_todos` is opt-in since v0.7
  (https://docs.langchain.com/oss/python/deepagents/overview; https://www.langchain.com/blog/deep-agents-v0-7).
- v0.7 removed the hidden base system prompt and trimmed tool descriptions 43%; default-turn input tokens fell 65% (5,395 -> 1,895)
  (https://docs.langchain.com/oss/python/releases/changelog "Jul 24, 2026"). Your `system_prompt` is now effectively the whole prompt.
- Any built-in middleware can be replaced in place by passing an instance with the same `.name` (deepagents >= 0.7; customization page).
- Streaming for a UI: `stream_events(..., version="v3")` gives typed projections (`stream.messages`, `stream.tool_calls`,
  `stream.subagents` with name/status/messages/tool_calls/output, `stream.interrupts`) and the same protocol over the wire via the
  Agent Server SDK (https://docs.langchain.com/oss/python/deepagents/event-streaming; https://www.langchain.com/blog/deep-agents-0-6).
- Editor/desktop surface: `deepagents-acp` (Agent Client Protocol, stdio) exposes a deep agent to Zed/JetBrains/VS Code
  (https://docs.langchain.com/oss/python/deepagents/acp).
- QMX already builds on this: `qmx-agents\packages\qmx-agents\src\qmx_agents\spec.py` (calls `create_deep_agent`),
  `copilot.py` (CompositeBackend + skills route), `router.py` (registers harness profiles, resolves models).

### a2. Background workflow agents

- Library level: any `create_deep_agent`/`create_agent`/StateGraph runs headless with a checkpointer; durability modes
  `"exit" | "async" | "sync"` per invocation (https://docs.langchain.com/oss/python/langgraph/persistence).
- Async subagents (deepagents >= 0.5): a supervisor gets `start_async_task`, `check_async_task`, `update_async_task`,
  `cancel_async_task`, `list_async_tasks`; tasks run as separate agents on an Agent Protocol server, task ids live in an
  `async_tasks` state channel that survives summarization (https://docs.langchain.com/oss/python/deepagents/async-subagents;
  https://www.langchain.com/blog/running-subagents-in-the-background). The changelog says they REQUIRE LangSmith Deployment / an
  Agent Protocol server ("Apr 7, 2026 deepagents v0.5.0"): ASGI transport when co-deployed (no `url`), HTTP transport when remote.
- LangGraph graph API is the right tool for deterministic node-editor workflows (nodes = code, LLM call, or a full agent; conditional
  edges) (https://docs.langchain.com/oss/python/langgraph/graph-api; https://www.langchain.com/blog/3-years-of-graph-engineering-with-langgraph).
- Fault tolerance (langgraph >= 1.2): per-node `timeout=`/`TimeoutPolicy`, `error_handler=`, `RunControl.request_drain()` graceful
  shutdown with resumable checkpoint (changelog "langgraph v1.2.0"; https://docs.langchain.com/oss/python/langgraph/fault-tolerance).

### a3. Remote / server execution

- Agent Server = API server + queue workers backed by Postgres (assistants, threads, runs, store, task queue with exactly-once
  semantics) + Redis (pub-sub for streaming background runs) (https://docs.langchain.com/langsmith/deploy-standalone-server).
- Deployment options: Cloud, Hybrid, Self-hosted with control plane, Standalone server
  (https://docs.langchain.com/langsmith/deployment, /data-plane, /control-plane). Standalone needs `LANGGRAPH_CLOUD_LICENSE_KEY`
  plus egress to `beacon.langchain.com` for license verification (deploy-standalone-server page). Self-hosted requires an Enterprise
  plan and license key (https://docs.langchain.com/langsmith/self-hosted; data-plane "Licensing").
- `langgraph-api` and `langgraph-runtime-inmem` are Elastic-2.0 licensed; `langgraph`, `deepagents`, `langgraph-cli`,
  `langchain-quickjs` are MIT (PyPI metadata, fetched 2026-10-12).
- Local: `langgraph dev` (no Docker, in-memory state pickled to a local dir, hot reload) and `langgraph up` (Docker + Postgres +
  Redis, custom auth only "with license key") (https://docs.langchain.com/langsmith/local-dev-testing). INFERRED: `langgraph dev`
  is a dev tool, not a supported production runtime for a 24/7 desktop daemon.
- Docker/Docker Compose standalone examples are "for local development and testing"; production path is Kubernetes + Helm;
  "Do not run standalone servers in serverless environments" (deploy-standalone-server page).
- Sandboxes for code execution are all remote (LangSmith, Daytona, E2B, Modal, Runloop, Vercel, AgentCore, NVIDIA OpenShell)
  (https://docs.langchain.com/oss/python/deepagents/sandboxes). No local Windows sandbox provider exists. QMX's own
  `AppSandbox(FilesystemBackend, SandboxBackendProtocol)` delegates `execute` to an installed app
  (`qmx-agents\packages\qmx-agents\src\qmx_agents\copilot.py`), which is the documented extension seam (custom backend implementing
  `execute`, https://docs.langchain.com/oss/python/deepagents/backends).

### a4. Scheduling

- Cron is an Agent Server feature only: `client.crons.create(...)` (stateless: new thread per run) and
  `client.crons.create_for_thread(...)` (same thread), cron syntax, all schedules in UTC, same input every time
  (https://docs.langchain.com/langsmith/cron-jobs). Assistants docs: assistants are "not available in the open source LangGraph
  library" (https://docs.langchain.com/langsmith/assistants); same is true for crons (INFERRED from the cron page being LangSmith-only).
- Deep Agents memory docs use a cron'd "consolidation agent" (`client.crons.create(assistant_id="consolidation_agent",
  schedule="0 */6 * * *")`) (https://docs.langchain.com/oss/python/deepagents/memory).
- Fleet and Managed Deep Agents have hosted schedules (https://docs.langchain.com/langsmith/fleet/schedules;
  https://www.langchain.com/blog/managed-deep-agents-schedules-per-run-configuration-slack) - cloud products, not local.
- No scheduler in the open-source libraries. QMX must own scheduling unless it runs Agent Server (see e).

### a5. Approvals (human-in-the-loop)

- `interrupt_on={tool: True | False | InterruptOnConfig}` -> decisions `approve | edit | reject | respond`; optional `when`
  predicate (langchain >= 1.3.3); checkpointer required; resume with `Command(resume={"decisions": [...]})` on the same thread
  (https://docs.langchain.com/oss/python/deepagents/human-in-the-loop).
- Filesystem permissions: `FilesystemPermission(operations=["read"|"write"], paths=[globs], mode="allow"|"deny"|"interrupt")`,
  first-match-wins, permissive default; covers only the 7 built-in fs tools, NOT custom tools, MCP tools, or `execute`
  (https://docs.langchain.com/oss/python/deepagents/permissions).
- MCP tools carry `destructive_hint` metadata usable for approval gating; MCP elicitation surfaces as a LangGraph `interrupt()`
  (changelog "Sep 1, 2026 langchain v1.4.0").
- Gaps that matter: interpreter PTC calls and `task()` dispatched from interpreter code bypass `interrupt_on`
  (https://docs.langchain.com/oss/python/deepagents/interpreters, /dynamic-subagents). `ShellToolMiddleware` "does not work with
  interrupts yet" (https://docs.langchain.com/oss/python/langchain/middleware/built-in).
- QMX wraps this already (`spec.py` refuses `interrupt_on` without a checkpointer; `guards\middleware.py` journals approvals).

### a6. Memory (short and long term; pluggable?)

- Short-term = thread state in a checkpointer: InMemorySaver, SqliteSaver/AsyncSqliteSaver, PostgresSaver, MongoDB, CosmosDB
  (https://docs.langchain.com/oss/python/langgraph/checkpointers).
- Long-term = LangGraph `BaseStore` (InMemoryStore, PostgresStore, MongoDB, Redis, Upstash, custom) with namespaces and optional
  vector index (https://docs.langchain.com/oss/python/langgraph/stores). No SQLite store is documented (notes
  `langchain-langgraph-core.md` §4). UNVERIFIED whether a community SqliteStore exists for the pinned versions.
- Deep Agents memory is files: `memory=["/memories/AGENTS.md"]` loaded into the prompt; `/memories/` routed via
  `CompositeBackend(default=StateBackend(), routes={"/memories/": StoreBackend(namespace=...)})`; scope by assistant, user or org;
  skills = procedural memory; threads = episodic memory (https://docs.langchain.com/oss/python/deepagents/memory).
  Fully pluggable: any `BackendProtocol` implementation (https://docs.langchain.com/oss/python/deepagents/backends).
- ContextHubBackend stores memory as versioned LangSmith Hub commits; needs `LANGSMITH_API_KEY` (cloud)
  (https://www.langchain.com/blog/deep-agents-0-6).
- LangMem: MIT, last PyPI release 0.0.30 on 2025-10-27, repo still pushed 2026-10-02 (GitHub API), provides
  `create_manage_memory_tool` / `create_search_memory_tool` over a LangGraph store (`sources\langchain\langmem\README.md`;
  https://github.com/langchain-ai/langmem). LangChain's 2026 memory guidance no longer centres it: the June 2026 post builds memory
  from LangSmith traces + Engine + Context Hub (https://www.langchain.com/blog/how-to-give-your-agent-memory), and Harrison Chase's
  "memory is the harness" argument (https://www.langchain.com/blog/your-harness-your-memory). INFERRED: LangMem is effectively legacy.

### a7. Skills

- Agent Skills spec (`SKILL.md` with `name`, `description`, optional `metadata`), three-level progressive disclosure, multiple sources
  layered (last wins), per-subagent skill sets (custom subagents do NOT inherit; general-purpose does)
  (https://docs.langchain.com/oss/python/deepagents/skills).
- Skill-bound tools: `metadata.include_tools: a b` (space separated) + pass tools to `SkillsMiddleware(tools=...)`; bound tools stay
  out of context until the skill is read; on Anthropic models they arrive as a mid-conversation system message so the cached prefix
  holds (>= 0.7.22) (https://www.langchain.com/blog/revamping-skills-in-deep-agents).
- Pinned skills for `/skill` UI commands (>= 0.7.23 - not in QMX pin); reload via `skills_metadata=None` (>= 0.7.16) (skills page).
- Executing skill scripts needs a sandbox/`execute` backend (skills page).

### a8. Subagents

- Sync subagents via `task` tool. Spec fields: `name, description, system_prompt, mode ("isolated"|"fork"), tools, model,
  middleware, interrupt_on, skills, response_format, permissions`; `CompiledSubAgent` wraps any graph
  (https://docs.langchain.com/oss/python/deepagents/subagents). Fork mode reuses the parent conversation and prompt cache
  (https://www.langchain.com/blog/organizing-context-in-a-multi-agent-harness).
- Runtime context propagates to all subagents; each run tagged `lc_agent_name` for tracing (subagents page).
- Async subagents: see a2. Dynamic subagents: see a9.

### a9. RLM / code interpreter

- `CodeInterpreterMiddleware` (package `langchain-quickjs`, extra `deepagents[quickjs]`): adds an `eval` tool running JS in QuickJS
  in the same process; no fs/network/shell/clock by default; PTC allowlist exposes tools as `tools.*`; `task()` gives dynamic
  subagents; defaults `memory_limit=64MB`, `timeout=5.0s`, `max_ptc_calls=256`, `mode="thread"` snapshots
  (https://docs.langchain.com/oss/python/deepagents/interpreters, /dynamic-subagents). Beta.
- LangChain calls this "adjacent to" RLM, not RLM as defined in the paper (https://www.langchain.com/blog/deep-agents-0-6;
  https://www.langchain.com/blog/how-to-use-rlms-in-deep-agents, arXiv 2512.24601).
- Security: "capability-scoped execution layer, NOT a host-memory isolation boundary" (interpreters page); PTC and `task()` bypass
  `interrupt_on` (see a5). https://www.langchain.com/blog/running-untrusted-agent-code-without-a-sandbox covers the rationale.
- Windows/Python 3.14 install risk: `langchain-quickjs` 0.3.8 depends on `quickjs-rs<0.3,>=0.2.5` (pure wheel, needs `wasmtime>=45`)
  and `bsdiff4` (PyPI has win_amd64 wheels only up to cp313; no cp314 wheel) (PyPI JSON for each, fetched 2026-10-12).
  UNVERIFIED whether bsdiff4 builds from source on QMX's Windows/3.14 toolchain.

### a10. Compaction - and Claude Opus 5.5's append-only thinking rule

What the stack does:
- Deep Agents `SummarizationMiddleware` is always in the stack: trigger at 85% of `max_input_tokens` from the model profile,
  keep 10% of tokens verbatim, fallback 170k/6 messages; on `ContextOverflowError` it summarizes and retries; full history is written
  to `/conversation_history/` (https://docs.langchain.com/oss/python/deepagents/context-engineering).
- Large tool results (>20k tokens) are offloaded to files; older write/edit tool-call inputs are truncated as context passes 85%
  (same page).
- Opt-in `compact_conversation` tool (`create_summarization_tool_middleware`) lets the model compact itself
  (https://www.langchain.com/blog/autonomous-context-compression).
- LangChain `SummarizationMiddleware(trigger, keep=("messages",20), ...)`, `ContextEditingMiddleware(ClearToolUsesEdit(...))`,
  `trim_messages`/`RemoveMessage` (https://docs.langchain.com/oss/python/langchain/middleware/built-in,
  /short-term-memory).
- `ChatAnthropic` also exposes Anthropic's SERVER-side compaction (`betas=["compact-2026-01-12"]`,
  `context_management={"edits":[{"type":"compact_20260112","trigger":{...}}]}`) and server-side tool-result clearing
  (`clear_tool_uses_20250919`); requires langchain-anthropic >= 1.3.0 (https://docs.langchain.com/oss/python/integrations/chat/anthropic
  "Context management").
- None of the LangChain/LangGraph/Deep Agents pages mention thinking-block signatures or preserving them through summarization
  (searched; notes `langchain-langgraph-core.md` §0). The Anthropic integration page shows the signature living in
  `extras={"signature": ...}` on thinking blocks (chat-anthropic.md line ~807).

The Anthropic rule (source: Claude API skill bundled with Claude Code, `shared/model-migration.md`, "Migrating to Claude Fable 5.1
from Claude Fable 5 -> Breaking change 3", which the Opus 5.5 section points to; public doc
https://platform.claude.com/docs/en/build-with-claude/extended-thinking - UNVERIFIED that the public page carries identical wording):
- Opus 5.5 runs "preserved thinking": a thinking block's signature binds the `system` prompt, the `tools` set and every earlier message.
  Editing, reordering or removing an earlier turn, rebuilding `system` or `tools`, or injecting-then-removing per-turn text invalidates
  every later thinking block. Enforced (400) for accounts created on or after 2026-08-31; otherwise dropped or let through depending on
  `thinking.block_binding.prefix_mismatch_behavior` (beta `thinking-binding-controls-2026-08-01`).
- Safe: append-only histories, appended `role:"system"` messages, mid-conversation `tool_addition`/`tool_removal`, cache_control
  changes, `output_config`/`effort` changes, SERVER-side compaction and context editing, and "simple compaction" (summarize everything
  into one message, replay nothing else).
- Unsafe: keep-tail compaction (summarize old, keep recent turns verbatim) unless the retained turns' thinking blocks are stripped;
  background compaction swapped in later; client-side deletion of old tool results.

Verdict per mechanism (INFERRED from the two sets of sources above):
- Deep Agents/LangChain `SummarizationMiddleware` = keep-tail compaction -> UNSAFE on an enforced account unless retained AI messages
  lose their thinking blocks. QMX's daemon uses exactly this shape: `SummarizationMiddleware(..., keep=("messages", 2))`
  (`qmx-agents\packages\qma-daemon\src\qma\daemon\request_runtime\deep_agent.py` ~line 180).
- `ContextEditingMiddleware` (client-side clearing), `trim_messages`, `RemoveMessage`, Deep Agents tool-input truncation at 85% -> edits
  -> UNSAFE.
- Anything that rewrites the system prompt per turn (`@dynamic_prompt`, MemoryMiddleware after an AGENTS.md edit, skill reload) or the
  tool list (`LLMToolSelectorMiddleware`, `request.override(tools=...)`, model-dependent tool filtering) -> UNSAFE. Deep Agents places
  MemoryMiddleware after caching to protect the cache (customization page) but a memory edit still changes the system prompt.
- Skill-bound tools added as a mid-conversation system message on Anthropic models, `AnthropicPromptCachingMiddleware`,
  `ProviderToolSearchMiddleware` (defer_loading) -> SAFE by the rule above.
- Server-side compaction via `ChatAnthropic(context_management=...)` -> SAFE, but: (1) it bypasses Deep Agents' history-offload to
  `/conversation_history/`; (2) whether CLIProxyAPI forwards `anthropic-beta` headers and `context_management`/`block_binding` fields
  to Anthropic for subscription traffic is UNVERIFIED; (3) whether QMX's subscription account is "enforced" (created before or after
  2026-08-31) is UNVERIFIED.
- `PatchToolCallsMiddleware` inserts synthetic tool results for dangling tool calls after interrupts (customization page); if it inserts
  before later turns it is an edit. UNVERIFIED in code.

### a11. Prompt caching

- Deep Agents applies provider caching automatically: Anthropic explicit breakpoints, OpenAI implicit, Bedrock, Fireworks session
  affinity; measured 49-80% token-cost cuts (https://www.langchain.com/blog/deep-agents-prompt-caching; changelog v0.7.0).
- `AnthropicPromptCachingMiddleware` default TTL `5m`, override by passing `AnthropicPromptCachingMiddleware(ttl="1h")`
  (https://docs.langchain.com/oss/python/deepagents/customization). It no-ops on non-Anthropic models (customization page).
  QMX routes Claude via CLIProxy's Anthropic endpoint into `ChatAnthropic` (`router.py` lines ~178-187), so the middleware should
  engage (INFERRED; whether CLIProxyAPI preserves `cache_control` is UNVERIFIED).
- Opus 5.5 cache reads are 0.05x base input (Claude API skill, "Claude Fable 5.1 ... Pricing" deltas). Model switches and system/tool
  edits discard the cache (https://www.langchain.com/blog/how-to-build-a-model-router-in-the-harness "What's next").

### a12. Model profiles per model

Two different "profile" concepts - do not confuse them in the UI:
- LangChain model profile (`model.profile`, langchain >= 1.1, beta): capability data from models.dev (max_input_tokens, reasoning,
  tool calling, effort levels); drives summarization fractions and structured-output strategy; override with
  `init_chat_model(..., profile=...)` (https://docs.langchain.com/oss/python/langchain/models#model-profiles). A model behind a proxy
  under a custom name has NO profile data unless supplied (INFERRED; then summarization falls back to 170k tokens).
- Deep Agents harness profile (`HarnessProfile`, >= 0.6): per provider or per model: `base_system_prompt`, `system_prompt_suffix`,
  `tool_description_overrides`, `excluded_tools`, `excluded_middleware`, `extra_middleware`, `general_purpose_subagent`; YAML form
  `HarnessProfileConfig`; plugin entry points; built-ins for Anthropic, OpenAI, Google, NVIDIA Nemotron
  (https://docs.langchain.com/oss/python/deepagents/profiles; https://www.langchain.com/blog/tuning-deep-agents-different-models).
  `ProviderProfile(init_kwargs=...)` applies only to string models (profiles page).
- Profile keys are `provider:model`; QMX registers keys from YAML in `router.py` (line ~106) and in `deep_agent.py`.
  A ChatAnthropic built for `cliproxy` resolves under provider `anthropic`, so built-in Anthropic profiles apply (INFERRED).

### a13. Tool search

- `ProviderToolSearchMiddleware(searchable_tools=[...])` defers tools behind the provider's server-side tool search; Anthropic
  (Sonnet 4+/Opus 4+/Haiku 4.5+) or OpenAI gpt-5.5+ only, else `ValueError`; tools with `extras={"defer_loading": True}` always deferred
  (https://docs.langchain.com/oss/python/langchain/middleware/built-in#provider-tool-search). Not usable with DeepSeek / other
  OpenAI-compatible models.
- Model-agnostic alternatives: `LLMToolSelectorMiddleware` (extra LLM call, rewrites tool list -> cache/thinking unsafe), skill-bound
  tools (a7), MCP tool groups behind a skill resolver (https://www.langchain.com/blog/revamping-skills-in-deep-agents).

---------------------------------------------------------------------------------------------------

## b. One deployment, several differently configured agents sharing memory and tools?

Yes, two documented ways, plus a library-only way.

1. Agent Server: several graphs in one `langgraph.json` (`"graphs": {"copilot": ..., "lab": ..., "portfolio": ..., "wf_x": ...}`),
   each gets a default assistant; extra assistants = versioned configurations of one graph (prompts, model, tools) editable via API/UI
   without redeploy (https://docs.langchain.com/langsmith/assistants). All graphs in a deployment share the deployment's Postgres
   store (store API at deployment level, https://docs.langchain.com/langsmith/custom-store; INFERRED that sharing is per-deployment).
   Memory scoping inside the shared store is by namespace: `rt.server_info.assistant_id`, `rt.server_info.user.identity`,
   `rt.context.<field>` (https://docs.langchain.com/oss/python/deepagents/memory). Async subagents call co-deployed graphs over ASGI
   by `graph_id` (async-subagents page). Crons target an assistant (cron-jobs page).
2. Supervisor + subagents in one graph: a general Copilot whose `subagents=` are the Lab and Portfolio specialists, each with own
   `model`, `tools`, `skills`, `permissions`, `interrupt_on`, `middleware` (subagents page). Fits "general Copilot can host any
   conversation"; less fit for a user talking directly and at length to the Portfolio copilot.
3. Library only (what QMX does today): build N `create_deep_agent` instances in one Python process sharing one checkpointer and one
   `BaseStore` instance; per-agent `CompositeBackend` routes decide what each sees, e.g. shared `/memories/org/` read-only via
   `FilesystemPermission(... mode="deny")`, private `/memories/lab/` (backends + permissions pages). Tools are plain Python objects, so
   sharing is trivial; MCP tools come from one `MCPAdapter` (changelog langchain v1.4.0).

Organogram split that the primitives support directly (INFERRED design, sources as above):
- Tools: per-agent `tools=`; per-subagent `tools` override; skill-bound tools for the long tail.
- Hooks: per-agent `middleware=`; subagent `middleware` does not inherit.
- Skills: per-agent `skills=[org, team, copilot]` source layering; custom subagents need explicit skills.
- Memory: namespace tuple `(copilot_id, user)` plus a shared `(org,)` namespace mounted read-only.
- Permissions: per-agent `permissions=`; subagent permissions REPLACE parent's.
- Models: per-agent `model=`, per-subagent `model`, harness profiles per model, runtime override via `@wrap_model_call` reading
  `runtime.context` (https://docs.langchain.com/oss/python/deepagents/models#select-a-model-at-runtime).

---------------------------------------------------------------------------------------------------

## c. LangSmith Gateway and Engine - what they add, overlap with CLIProxyAPI

LLM Gateway (beta) (https://docs.langchain.com/langsmith/llm-gateway, /llm-gateway-how-it-works):
- A hosted proxy: one LangSmith API key -> many providers; endpoints `/v1/chat/completions`, `/v1/messages`, `/v1/responses`,
  `/v1/models`; translates formats; fallbacks; spend, rate, model-access and data-protection (PII/secret redaction, Presidio) policies;
  traces every call.
- Runs on LangSmith Cloud (all regions), BYOC, or self-hosted LangSmith (Helm chart >= 0.17.1, K8s, Postgres + Redis)
  (https://docs.langchain.com/langsmith/llm-gateway-self-hosted). Self-hosted LangSmith is an Enterprise add-on
  (https://docs.langchain.com/langsmith/self-hosted). There is no single-binary/local gateway.
- Credentials: bring-your-own provider keys (workspace secrets) or Gateway Credits (LangChain-hosted Kimi K2.6/K3 at $1 per LSU;
  paid plans only) (https://docs.langchain.com/langsmith/llm-gateway-credits).
- Subscription traffic: supported only as a pass-through for the Claude Code CLI - the gateway forwards Claude Code's saved
  Plus/Max OAuth bearer to Anthropic, which bills the subscription; "Claude Desktop plugins break when the gateway is configured"
  (https://docs.langchain.com/langsmith/llm-gateway-coding-agents). Nothing documents using a Claude subscription from an arbitrary
  app/SDK through the gateway.
- Overlap with CLIProxyAPI: both are OpenAI/Anthropic-compatible proxies. CLIProxyAPI's job (turning a subscription into an API for
  QMX's own agents) is NOT covered by the gateway. The gateway adds governance + tracing that QMX does not need as a single operator,
  and moves all model traffic through LangChain's cloud. LangChain itself argues routing belongs in the harness, not a generic
  gateway (https://www.langchain.com/blog/how-to-build-a-model-router-in-the-harness). Verdict: no.

Engine (https://docs.langchain.com/langsmith/engine-overview, /engine):
- An agent that scans LangSmith tracing projects every ~6 hours, clusters recurring failures, diagnoses root cause against a connected
  GitHub repo, proposes fix PRs, generates dataset examples, reopens regressions; red teaming on Cloud only.
- Plus plan or Enterprise; $1/LSU, ~7-45 LSU per run (https://www.langchain.com/pricing, saved `langsmith\pricing.md`); self-hosted
  needs an Engine-entitled Enterprise license (https://docs.langchain.com/langsmith/engine-self-hosted).
- Requires traces in LangSmith. No overlap with CLIProxyAPI. Verdict: optional later, only if QMX ships traces to LangSmith Cloud.

Other LangSmith pieces (for completeness):
- Tracing: free Developer plan = 1 seat, 5k base traces/month, 14-day retention; Plus $39/seat, 10k traces, 1 free small deployment
  (https://www.langchain.com/pricing). Tracing is optional; set `LANGSMITH_TRACING` off to send nothing (standard SDK env var;
  https://docs.langchain.com/langsmith/observability-concepts). Self-hosted LangSmith = Enterprise.
- Fleet, Managed Deep Agents, Sandboxes: hosted products (https://docs.langchain.com/langsmith/fleet/index,
  https://www.langchain.com/blog/introducing-managed-deep-agents, https://docs.langchain.com/langsmith/sandboxes). Not usable locally.

---------------------------------------------------------------------------------------------------

## d. Use from the library vs build in QMX (concrete)

USE from the library (already pinned):
1. `create_deep_agent` as the harness for all three copilots and for agentic workflow nodes; `create_agent` for small single-purpose
   nodes; LangGraph `StateGraph` as the execution model behind the Lab node editor (deterministic nodes + agent nodes).
2. Checkpointing: `AsyncSqliteSaver` locally (pinned); keep DeltaChannel (default since deepagents 0.6) - it cut a 200-turn session from
   5.27 GB to 129 MB of checkpoints (https://www.langchain.com/blog/deep-agents-0-6).
3. Backends: `CompositeBackend` + `StoreBackend` namespaces for memory/skills; `FilesystemBackend(virtual_mode=True)` only for
   reviewed local roots; QMX's own sandbox backend for `execute`.
4. HITL middleware + `FilesystemPermission` + LangGraph `interrupt()` for all approvals; journal them in QMX (already done).
5. Harness profiles (YAML) per model, registered from QMX config - matches the UI need for per-model defaults.
6. `langchain.mcp.MCPAdapter` for MCP; `destructive_hint` -> approval policy.
7. Skills with skill-bound tools for the long tail of tools; `ProviderToolSearchMiddleware` only on Claude/OpenAI routes.
8. `stream_events(version="v3")` as the single event contract for the UI (messages, tool calls, subagent cards, interrupts).
9. Retry / fallback / call-limit middleware (`ModelRetryMiddleware`, `ToolRetryMiddleware`, `ModelFallbackMiddleware`,
   `ModelCallLimitMiddleware`, `ToolCallLimitMiddleware`) for background agents on cheap models.
10. `RubricMiddleware` for Lab long experiments that must meet a bar (beta).
11. Server-side Anthropic compaction (`ChatAnthropic(context_management=...)`) for Opus 5.5 copilots, IF CLIProxyAPI passes it through.

BUILD in QMX:
1. Scheduler + job queue + "where jobs run" registry (local daemon vs remote node). Open-source LangGraph has none; Agent Server's
   is licence-gated for production self-hosting (a3, a4).
2. A thinking-safe context policy for Opus 5.5: replace keep-tail `SummarizationMiddleware` on Claude routes with server-side
   compaction or "simple compaction" (summary-only restart); forbid per-turn system/tool rebuilds on Claude routes (append system
   messages instead); keep Deep Agents summarization for DeepSeek/GPT background routes. Add a regression test that diffs consecutive
   request bodies (the "three-step check" in the Claude API skill's preserved-thinking guide).
3. Model router: per-copilot defaults + per-run override in middleware (`@wrap_model_call`), choose once per thread (switching models
   resets cache and drops thinking). LangChain's own router is the same shape (Open SWE `model_selection.py`, linked from the router
   blog); the packaged `ModelRouterMiddleware` depends on the TypeSafe/Jev SaaS (https://docs.langchain.com/oss/python/integrations/providers/typesafe).
4. Model-profile data for proxy-served models (max_input_tokens, effort levels) so summarization thresholds and UI pickers are right.
5. Organogram config: which tools/skills/memory namespaces/permissions each copilot gets - QMX YAML specs (`qmx_agents\agents\*.yaml`)
   are the right place.
6. Remote node runtime: if workflow agents run on a VPS, a small QMX-owned runner (FastAPI + same graphs + Postgres/SQLite checkpointer)
   that speaks the subset of Agent Protocol QMX needs - or license Agent Server. Async subagents' HTTP transport speaks Agent Protocol,
   so a QMX runner that implements it would let Deep Agents supervisors drive remote nodes unchanged (INFERRED; the protocol is
   https://github.com/langchain-ai/agent-protocol).
7. Observability: local trace store or optional LangSmith Developer-plan tracing (5k traces/month is small for background agents).

DO NOT adopt: LLM Gateway (c), Engine (until traces live in LangSmith), ContextHubBackend (cloud-bound), Fleet/Managed Deep Agents,
LangMem (stale), `LocalShellBackend` (unsandboxed `subprocess.run(shell=True)` on the host; backends page says local dev only).

---------------------------------------------------------------------------------------------------

## e. Upgrade risks given the pinned versions

1. Pins are current (deepagents 0.7.22 is one week old). Moving to 0.7.23/0.7.24 adds `pinned_skills` and async-subagent fork mode;
   deepagents ships a patch every 1-5 days (release list, `releases\deepagents-releases.md`), and v0.7.0 had breaking changes inside a
   minor series (todos opt-in, backend factories removed, `StoreBackend` needs explicit `namespace`, `ls`/`read_file` output format
   changed) (changelog "Jul 24, 2026"). Treat every 0.x minor as breaking; pin exactly (QMX does).
2. DeltaChannel one-way door: once threads are persisted under deepagents >= 0.6, downgrading is unsupported (changelog "May 12, 2026").
   Same caution for any future checkpoint format change - keep a checkpoint-DB backup step in upgrades.
3. Beta surfaces QMX may lean on: DeltaChannel (beta), `stream_events` v3 (beta in langgraph 1.2.0 notes), `langchain.mcp` (beta,
   `LangChainBetaWarning`), interpreters, dynamic subagents, rubric, forked subagents (all beta per their pages). Expect API churn.
4. `langchain-mcp-adapters` -> `MCPAdapter` migration already made (pin `langchain[mcp]`); `MultiServerMCPClient` is gone
   (https://docs.langchain.com/oss/python/migrate/langchain-mcp-adapters).
5. Opus 5.5 preserved thinking (a10) is the largest functional risk and is independent of LangChain versions: QMX's keep-tail
   summarization (`deep_agent.py`) will 400 on an enforced account once a conversation crosses the trigger. UNVERIFIED whether
   `langchain-anthropic` 1.7.5 exposes `thinking.block_binding` - not found in its doc page.
6. Python 3.14 + Windows: `langchain-quickjs` pulls `bsdiff4` without cp314 Windows wheels (a9). Agent Server images are Linux/Docker;
   `langgraph dev` runs natively but is a dev server (a3).
7. Agent Server licensing: `langgraph-api` is Elastic-2.0 and production standalone requires a license key; adopting it later changes
   the cost/licence picture (a3; https://www.langchain.com/pricing: Developer plan has no Deployment).
8. Model naming in docs is ahead of QMX's models (docs examples cite gpt-5.6/gpt-6, claude-opus-5); built-in harness profiles are keyed by
   provider:model, so a proxied model ID that differs from the official ID silently misses its built-in model-level profile (profiles
   page: keys are exact; no wildcard). INFERRED.
9. TodoListMiddleware default flip (v0.7): any UI that shows a plan needs `TodoListMiddleware()` explicitly (blog v0.7; the Codex
   profile still enables it).

---------------------------------------------------------------------------------------------------

## f. LangChain blog 2026 - relevant posts (title, date, URL). Saved copies: `sources\langchain\blog\md\<slug>.md`

Saved = full text saved. Dates from each page's JSON-LD.

Harness / loop / graph engineering
- Building Multi-Agent Applications with Deep Agents (2026-01-21) https://www.langchain.com/blog/building-multi-agent-applications-with-deep-agents [saved]
- Context Management for Deep Agents (2026-01-28) https://www.langchain.com/blog/context-management-for-deepagents [saved]
- The two patterns by which agents connect sandboxes (2026-02-10) https://www.langchain.com/blog/the-two-patterns-by-which-agents-connect-sandboxes [saved]
- Improving Deep Agents with harness engineering (2026-02-17) https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering [saved]
- The Anatomy of an Agent Harness (2026-03-11) https://www.langchain.com/blog/the-anatomy-of-an-agent-harness [saved]
- Autonomous context compression (2026-03-11) https://www.langchain.com/blog/autonomous-context-compression [saved]
- How Middleware Lets You Customize Your Agent Harness (2026-03-26) https://www.langchain.com/blog/how-middleware-lets-you-customize-your-agent-harness [saved]
- Better Harness: A Recipe for Harness Hill-Climbing with Evals (2026-04-08) https://www.langchain.com/blog/better-harness-a-recipe-for-harness-hill-climbing-with-evals [saved]
- How to Build a Custom Agent Harness (2026-06-03) https://www.langchain.com/blog/how-to-build-a-custom-agent-harness [saved]
- The Art of Loop Engineering (2026-06-16) https://www.langchain.com/blog/the-art-of-loop-engineering [saved]
- 3 Years of Graph Engineering with LangGraph (2026-07-22) https://www.langchain.com/blog/3-years-of-graph-engineering-with-langgraph [saved]
- Organizing Context in a Multi-Agent Harness (2026-09-08) https://www.langchain.com/blog/organizing-context-in-a-multi-agent-harness [saved]
- What Is Jev? (Building a Harness with Jev) (2026-09-18) https://www.langchain.com/blog/building-a-harness-with-jev [saved]

Deep Agents releases and features
- Deep Agents v0.5 (2026-04-07) https://www.langchain.com/blog/deep-agents-v0-5 [saved]
- Deep Agents Deploy: an open alternative to Claude Managed Agents (2026-04-09) https://www.langchain.com/blog/deep-agents-deploy-an-open-alternative-to-claude-managed-agents [saved]
- Running Subagents in the Background (2026-04-16) https://www.langchain.com/blog/running-subagents-in-the-background [saved]
- The Runtime Behind Production Deep Agents (2026-04-20) https://www.langchain.com/blog/runtime-behind-production-deep-agents [saved]
- New in Deep Agents v0.6 (2026-05-13) https://www.langchain.com/blog/deep-agents-0-6 [saved]
- Interpreters in Deep Agents (2026-05-20) https://www.langchain.com/blog/give-your-agents-an-interpreter [saved]
- Interpreter Skills: Building Workflows for Agents (2026-05-29) https://www.langchain.com/blog/interpreter-skills [saved]
- Introducing Rubrics (2026-06-02) https://www.langchain.com/blog/introducing-rubrics-for-deepagents [saved]
- Prompt Caching with Deep Agents (2026-06-26) https://www.langchain.com/blog/deep-agents-prompt-caching [saved]
- Introducing Dynamic Subagents in Deep Agents (2026-06-29) https://www.langchain.com/blog/introducing-dynamic-subagents-in-deep-agents [saved]
- How Deep Agents Run Untrusted Code Without a Sandbox (2026-06-30) https://www.langchain.com/blog/running-untrusted-agent-code-without-a-sandbox [saved]
- How to Use RLMs in Deep Agents (2026-07-01) https://www.langchain.com/blog/how-to-use-rlms-in-deep-agents [saved]
- How We Benchmark Deep Agents (2026-07-23) https://www.langchain.com/blog/how-we-benchmark-deep-agents [saved]
- Deep Agents v0.7 (2026-07-29) https://www.langchain.com/blog/deep-agents-v0-7 [saved]
- Revamping Skills in Deep Agents (2026-10-07) https://www.langchain.com/blog/revamping-skills-in-deep-agents [saved]
- Evaluating Skills (2026-03-05) https://www.langchain.com/blog/evaluating-skills [saved]
- Delta channels (linked from v0.6 post, not fetched) https://www.langchain.com/blog/delta-channels-evolving-agent-runtime

Models, routing, multi-model tuning
- Open Models have crossed a threshold (2026-04-02) https://www.langchain.com/blog/open-models-have-crossed-a-threshold [saved]
- Tuning Deep Agents to Work Well with Different Models (2026-04-29) https://www.langchain.com/blog/tuning-deep-agents-different-models [saved]
- Model Neutrality (2026-06-04) https://www.langchain.com/blog/model-neutrality [saved]
- Tuning the harness, not the model: a Nemotron 3 Ultra playbook (2026-07-08) https://www.langchain.com/blog/tuning-the-harness-not-the-model-a-nemotron-3-ultra-playbook [saved]
- How many of your agent's calls actually need a frontier model? (Switchyard) (2026-08-11) https://www.langchain.com/blog/switchyard-agent-routing-benchmark [saved]
- How to Build a Model Router in the Harness (2026-10-01) https://www.langchain.com/blog/how-to-build-a-model-router-in-the-harness [saved]

Memory
- How we built Agent Builder's memory system (2026-02-22) https://www.langchain.com/blog/how-we-built-agent-builders-memory-system [saved]
- Your harness, your memory (2026-04-11) https://www.langchain.com/blog/your-harness-your-memory [saved]
- How to Build Memory into AI Agents (2026-06-24) https://www.langchain.com/blog/how-to-give-your-agent-memory [saved]
- Wiki Memory: File-Based Memory for AI Agents (2026-06-30) https://www.langchain.com/blog/wiki-memory [saved]
- OpenWiki Brains (2026-07-10) https://www.langchain.com/blog/introducing-openwiki-brains-general-purpose-wiki-memory-for-agents [saved]
- Building Self-Correcting Memory in OpenWiki (2026-08-25) https://www.langchain.com/blog/self-correcting-memory-openwiki [saved]

LangSmith platform (Engine, Gateway, Managed Deep Agents, Fleet, sandboxes)
- Introducing LangSmith Fleet (2026-03-19) https://www.langchain.com/blog/introducing-langsmith-fleet [saved]
- The Agent Improvement Loop Starts with a Trace (2026-03-31) https://www.langchain.com/blog/traces-start-agent-improvement-loop [saved]
- Human judgment in the agent improvement loop (2026-04-09) https://www.langchain.com/blog/human-judgment-in-the-agent-improvement-loop [saved]
- Introducing LangSmith Engine (2026-05-13) https://www.langchain.com/blog/introducing-langsmith-engine [saved]
- LangSmith LLM Gateway: runtime governance (2026-05-13) https://www.langchain.com/blog/introducing-llm-gateway [saved]
- LangSmith Sandboxes are GA (2026-05-13) https://www.langchain.com/blog/langsmith-sandboxes-generally-available [saved]
- Managed Deep Agents (2026-05-13) https://www.langchain.com/blog/introducing-managed-deep-agents [saved]
- LangSmith Engine: How We Built an Agent for Improving Agents (2026-05-19) https://www.langchain.com/blog/how-we-built-langsmith-engine-our-agent-for-improving-agents [saved]
- How to Choose the Right Sandbox (2026-06-12) https://www.langchain.com/blog/how-to-choose-the-right-sandbox-for-your-agent [saved]
- Why Fleet Has General Purpose Chat and Specialized Agents (2026-06-16) https://www.langchain.com/blog/why-fleet-has-both-general-purpose-chat-and-specialized-agents [saved] (relevant to the general vs specialist copilot split)
- IssueBench - How We Evaluate Engine (2026-07-20) https://www.langchain.com/blog/issuebench-how-we-evaluate-engine [saved]
- LangSmith LLM Gateway: Runtime Controls for Agents (2026-07-30) https://www.langchain.com/blog/langsmith-llm-gateway-runtime-controls-for-production-agents [saved]
- Managed Deep Agents is now in public beta (2026-08-07) https://www.langchain.com/blog/managed-deep-agents-is-now-in-public-beta [saved]
- LangSmith Engine Improves Agent Issue Detection by 2x (2026-08-25) https://www.langchain.com/blog/new-in-langsmith-engine-2x-better-issue-detection [saved]
- Managed Deep Agents delivers a better UX (2026-09-24) https://www.langchain.com/blog/langsmith-managed-deep-agents-whats-new [saved]
- New in LangSmith Engine: red teaming and automated testing (2026-09-24) https://www.langchain.com/blog/langsmith-engine-v2-redteam [saved]
- New in LangSmith: Engine v2, Managed Deep Agents, Fine-Tuning (2026-09-25) https://www.langchain.com/blog/langsmith-engine-agents-fine-tuning-trajectories [saved]
- What's New in Managed Deep Agents: schedules, per-run configuration (2026-10-07) https://www.langchain.com/blog/managed-deep-agents-schedules-per-run-configuration-slack [saved]

Pre-2026 background also saved: agent-middleware (2025-09-08), agent-frameworks-runtimes-and-harnesses-oh-my (2025-10-25),
doubling-down-on-deepagents (2025-10-28), execute-code-with-sandboxes-for-deepagents (2025-11-13), using-skills-with-deep-agents
(2025-11-25), memory-for-agents (2024-10-19), langmem-sdk-launch (2025-02-18).
Not found as a post: "rubrics" beyond the Rubrics launch, "multi-model tuning" beyond the tuning/Nemotron posts. Blog list taken from
https://www.langchain.com/sitemap.xml (534 blog URLs; filtered by keyword, so a relevant post with an unrelated slug could be missed).

---------------------------------------------------------------------------------------------------

## g. Where QMX's existing research is wrong or outdated

Skimmed only after sections 0-f were written. Files:
`C:\Users\Mubarak\Desktop\QMX-worktrees\rebuild\rebuild\research\harness-practices.md` (dated 2026-10-09) and
`...\rebuild\research\cookbooks-loops-graphs.md`. Both are largely accurate on API names and defaults; the problems are below.

harness-practices.md
1. §4 "QMX should" item 1 and §8 "Compaction policy" (lines ~309-311 and the blueprint): "Keep Deep Agents' SummarizationMiddleware
   as the single compaction mechanism ... Do not also turn on Anthropic server-side compaction". WRONG for Opus 5.5. Deep Agents
   summarization keeps a verbatim tail (10% / last messages); keep-tail compaction is one of the two shapes the Anthropic guide says
   break preserved thinking (400 on enforced accounts). Server-side compaction is the shape Anthropic recommends and does not count as
   an edit (section a10). The "two summarisers fight" point stands, so the fix is: on Claude routes use server-side or summary-only
   compaction and disable/replace Deep Agents' SummarizationMiddleware (same-name override, deepagents >= 0.7); keep Deep Agents'
   summarizer for non-Claude routes.
2. §4 item 4: adding `ContextEditingMiddleware(ClearToolUsesEdit(...))` "if traces show stale tool output". On Claude routes this is a
   client-side history edit and invalidates later thinking blocks; use Anthropic's server-side `clear_tool_uses_20250919` through
   `ChatAnthropic(context_management=...)` instead (https://docs.langchain.com/oss/python/integrations/chat/anthropic).
3. §4 (Deep Agents bullet): "It also truncates old tool-call args" is correct but is itself a history edit on Claude routes - not flagged.
4. §8 blueprint `interrupt_on={"propose_order": True, "node_*": True, ...}`: no doc shows glob keys; HITL matches each tool's `.name`
   (https://docs.langchain.com/oss/python/langchain/middleware/built-in; deepagents human-in-the-loop page). Treat `"node_*"` as
   UNVERIFIED/likely a no-op; use `InterruptOnConfig(when=...)` or enumerate tools.
5. §7 RLM policy: "Implement it as a dedicated async sub-agent with a REPL tool and a cheap sub-model" and "It needs a sandbox".
   OUTDATED: Deep Agents ships this as `CodeInterpreterMiddleware` + dynamic subagents (QuickJS, same process, not a sandbox), with
   LangChain's own RLM post (https://www.langchain.com/blog/how-to-use-rlms-in-deep-agents, 2026-07-01). cookbooks-loops-graphs.md §6
   item 7 already corrects this.
6. §8 loop rules and §6 rely on todos ("reconcile todos"); `write_todos` is opt-in since deepagents 0.7.0 - the blueprint's
   `middleware=[...]` list does not add `TodoListMiddleware()`, so the todo tool would not exist (changelog "Jul 24, 2026").
7. §8 `plan-a-change` skill as the replacement for plan mode: fine, but the UI-driven "/plan" path needs `pinned_skills`, which arrived in
   deepagents 0.7.23 - one patch above the QMX pin (section 0).
8. §3 caching: correct that `AnthropicPromptCachingMiddleware` only acts on `ChatAnthropic`. QMX's router already uses `ChatAnthropic` for
   `claude-*` models via CLIProxy (`router.py`), so the "silently does nothing" risk is handled for the copilot but would recur for any
   Claude model reached through the `openrouter`/`local` providers (they force `openai`).
9. Not covered at all: Opus 5.5 preserved-thinking rules for dynamic system prompts, memory edits, skill reload and tool-list changes
   (section a10). The document treats cache invalidation as the only cost of those edits; on Opus 5.5 they can also be hard 400s.

cookbooks-loops-graphs.md
1. §5 L1 "todos go through `write_todos`" and the L2 controller's "todos are open" checks: same opt-in issue as above.
2. §5 "Long jobs. These are async sub-agents with task IDs" and the L2 rule "poll `check_async_task`": async subagents require an Agent
   Protocol server (LangSmith Deployment or self-hosted Agent Server, changelog "Apr 7, 2026 deepagents v0.5.0"). QMX runs neither, so
   this needs either a QMX-built Agent-Protocol runner or QMX-native job tools with the same five-verb shape (section d BUILD 1 and 6).
3. §4.2 / §6 "QMX owns its scheduler but should keep those semantics" - correct, and confirmed: open-source LangGraph has no cron
   (section a4).
4. "Still UNVERIFIED" list: item 5 ("Whether the installed langgraph is >= 1.2") is now answered - pinned 1.2.14 (section 0). Item 2
   (profile-key resolution for model instances) is partly answered: keys are exact `provider:model`, no wildcard; a proxied model ID that
   differs from the official one misses model-level built-ins (profiles page). Item 4 (whole-history replacement via
   SummarizationMiddleware) stays UNVERIFIED - the docs say `keep` takes exactly one of fraction/tokens/messages but do not say whether
   `("messages", 0)` is allowed; server-side compaction avoids the question.
5. §1.3 interpreter facts and §1.5 rubric facts match the docs; `max_iterations` default is 3, not 5 (the 5 in §1.5 is an example value -
   fine if intentional) (https://docs.langchain.com/oss/python/deepagents/rubric).
6. Interpreter install on Windows + Python 3.14 (`bsdiff4` has no cp314 wheel) is not mentioned; it gates §6 item 7 (section a9).
