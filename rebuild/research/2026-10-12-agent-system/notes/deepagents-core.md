# Deep Agents — core harness notes (for QMX agent layer)

Source corpus: saved markdown copies of https://docs.langchain.com/oss/python/deepagents/<page>.
Package: `deepagents` (PyPI), built on LangChain core + LangGraph runtime. These docs ship forward-looking
model ids (e.g. `claude-sonnet-5`, `gpt-5.5`, `gemini-3.6-flash`); treat model-name strings as examples,
not version gates. Version-requirement notes below are what the docs state explicitly.

NOTE ON PINS: QMX pins `deepagents 0.7.22`, so every "requires deepagents>=0.7.x" feature below is satisfied.

---

## 1. What a deep agent IS and how it is built
src: https://docs.langchain.com/oss/python/deepagents/overview

- Deep Agents is an "agent harness": the same tool-calling loop as other frameworks + built-in capabilities.
  Standalone lib built on LangChain building blocks; uses LangGraph runtime for durable execution, streaming,
  HITL. (overview)
- Four capability groups: Execution environment (tools, virtual filesystem, optional sandbox, interpreter/REPL);
  Context management (skills, memory, summarization, offloading, prompt caching); Delegation (subagents + opt-in
  task planning); Steering (human-in-the-loop, filesystem permissions). (overview)

### create_deep_agent signature
src: https://docs.langchain.com/oss/python/deepagents/customization  (reference.langchain.com/python/deepagents/graph/create_deep_agent)

```
create_deep_agent(
    model: str | BaseChatModel | None = None,
    tools: Sequence[BaseTool | Callable | dict] | None = None,
    *,
    system_prompt: str | SystemMessage | None = None,
    middleware: Sequence[AgentMiddleware] = (),
    subagents: Sequence[SubAgent | CompiledSubAgent | AsyncSubAgent] | None = None,
    skills: list[str] | None = None,
    memory: list[str] | None = None,
    permissions: list[FilesystemPermission] | None = None,
    backend: BackendProtocol | None = None,
    interrupt_on: dict[str, bool | InterruptOnConfig] | None = None,
    response_format: ResponseFormat | type | dict | None = None,
    state_schema: type[DeepAgentState] | None = None,
    context_schema: type[ContextT] | None = None,
    checkpointer: Checkpointer | None = None,
    store: BaseStore | None = None,
    debug: bool = False,
    name: str | None = None,
    cache: BaseCache | None = None,
) -> CompiledStateGraph
```
- `model` as `provider:model` string is resolved via `init_chat_model`; or pass an initialized `BaseChatModel`.
- `memory=` is a list of AGENTS.md file paths; `skills=` is a list of skills directories. (customization)

---

## 2. Default harness / middleware stack (ORDER MATTERS)
src: https://docs.langchain.com/oss/python/deepagents/customization  (#deep-agents-stack)

Bare stack (model only, no optional args), main agent typically:
1. `FilesystemMiddleware`
2. `SubAgentMiddleware` (present because the general-purpose subagent is auto-added unless a harness profile disables it)
3. `SummarizationMiddleware`
4. `PatchToolCallsMiddleware`
5. Prompt-caching middleware (always registered; no-ops on unsupported models)
6. Harness-profile extras + excluded-tool filtering (if resolved model profile defines them)

Full stack, first→last:
1. `FilesystemMiddleware` — file ops (ls/read/write/edit/delete/glob/grep); when `permissions=` passed, permission enforcement lives here.
2. `SubAgentMiddleware` — only when ≥1 synchronous subagent available; provides the `task` tool (parent only).
3. `SummarizationMiddleware` — via `create_summarization_middleware`.
4. `PatchToolCallsMiddleware` — repairs dangling/malformed tool calls after interrupt/resume. Runs BEFORE Anthropic caching + tail.
5. `AsyncSubAgentMiddleware` — only when async subagents configured.
6. Your `middleware=` argument — merged after Patch; an instance whose `.name` matches a built-in REPLACES it in place; otherwise inserted here (after last core entry, before profile/caching/memory).
7. Harness profile extras (provider-specific middleware from resolved profile).
8. `SkillsMiddleware` — only when `skills=` passed; runs after your middleware, directly before prompt caching.
9. Prompt caching: `AnthropicPromptCachingMiddleware` + `BedrockPromptCachingMiddleware` — both always registered, run after Patch + your middleware; each no-ops on unsupported models (`unsupported_model_behavior="ignore"`).
10. `MemoryMiddleware` — only when `memory=` passed; placed AFTER profile extras + caching so memory updates don't invalidate cache prefix.
11. `HumanInTheLoopMiddleware` — only when `interrupt_on=` set.
12. Excluded-tool filtering — when harness profile lists excluded tools.

- Overriding a built-in by matching `.name` requires **deepagents>=0.7**. (customization #override-a-default-middleware-instance)
- Synchronous subagent stack mirrors main agent shape (filesystem, summarization, Patch, profile extras, skills, Anthropic+Bedrock caching, optional permissions) but has NO `SubAgentMiddleware` inside a subagent graph.
- Built-in filesystem tools: `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`, plus `execute` (sandbox backends only). `delete` requires **deepagents>=0.7**; auto-hidden on backends that don't support deletion. (overview #virtual-filesystem-access)
- `read_file` supports offset/limit and returns multimodal content blocks for images/video/audio/pdf/ppt/pptx (extension list in overview + multimodal).
- Task planning (`write_todos` via `TodoListMiddleware`) is **opt-in only starting v0.7** (was default-on earlier). Status values: `pending`/`in_progress`/`completed`. (overview #task-planning)
- On-demand compaction tool: `create_summarization_tool_middleware(model, backend)` adds a `compact_conversation` tool (shares the summarization engine/state with the automatic 85% trigger; does not disable it). (customization, context-engineering)

---

## 3. Models + profiles (per-model defaults; OpenAI-compatible base_url)
src: https://docs.langchain.com/oss/python/deepagents/models and .../profiles

- Any LangChain chat model with tool calling works. `provider:model` prefix selects the integration; everything after first colon is the model id passed through. Resolved via `init_chat_model`. (models)
- Configure model params either via `init_chat_model(...)` or a provider model class, then pass the instance to `create_deep_agent(model=...)`. (models #configure-model-parameters)
- Runtime model swap: `@wrap_model_call` middleware reads `request.runtime.context.model` and calls `handler(request.override(model=init_chat_model(model_name)))`; pair with `context_schema`. Lets a UI dropdown pick model per invocation without rebuilding the agent. (models #select-a-model-at-runtime) — RELEVANT for QMX's Opus-5.5-daily vs cheap-background routing.
- OpenAI strings auto-enable the Responses API via a built-in OpenAI provider profile. To use Chat Completions, pass a pre-initialized model with `use_responses_api=False`. To keep Responses but disable retention: `store=False, include=["reasoning.encrypted_content"]` (returns encrypted reasoning). (models #openai-and-the-responses-api)

### Custom / OpenAI-compatible base_url (CLIProxyAPI case)
- The docs do not show a dedicated `base_url` parameter for `create_deep_agent`. INFERRED: to hit a local
  OpenAI/Anthropic-compatible proxy (CLIProxyAPI for Claude Opus 5.5), construct the provider model instance
  yourself and pass it in — e.g. `ChatOpenAI(model=..., base_url="http://localhost:<port>/v1", api_key=...)`
  or `ChatAnthropic(model=..., base_url=...)` — then `create_deep_agent(model=that_instance)`. The "Other"
  provider tab explicitly shows the `Chat<Provider>(model=...)` → `create_deep_agent(model=model)` pattern.
  `base_url` is a standard LangChain chat-model kwarg, not a deepagents feature. (customization #model, models)
- A `ProviderProfile(init_kwargs={...})` can carry `base_url`/`temperature`/`timeout`/etc. but ONLY applies
  when you pass a `provider:model` STRING (not a pre-built instance). (profiles, models #provider-profiles)

### Harness profiles (per-model/provider harness tuning)
src: https://docs.langchain.com/oss/python/deepagents/profiles
- `HarnessProfile` fields: `base_system_prompt` (replaces base instructions; for declarative subagents replaces their authored prompt), `system_prompt_suffix` (appended after caller + base; applies to main, declarative subagents, and GP subagent), `tool_description_overrides` (Mapping[str,str] by tool name), `excluded_tools` (frozenset[str], post-injection filter — drops user and middleware-added tools), `excluded_middleware` (frozenset of classes or string names), `extra_middleware` (Sequence or zero-arg callable), `general_purpose_subagent` (`GeneralPurposeSubagentProfile` — disable/rename/re-prompt; `enabled=False` removes GP subagent).
- `register_harness_profile(key, HarnessProfile(...))`. Keys: provider-level (`"openai"`) applies to all its models; model-level (`"openai:gpt-6-astra"`) applies to one, merges on top of provider-level. Only first colon splits provider/model. NO wildcard-all key. Re-registering under an existing key MERGES (additive), does not replace — this is how you customize a built-in profile.
- Built-in profiles exist for providers incl. Anthropic and OpenAI; built-in Anthropic/OpenAI profiles commonly ship only a `system_prompt_suffix`.
- Listing `FilesystemMiddleware`, `SubAgentMiddleware`, or the internal permission middleware in `excluded_middleware` raises `ValueError` (required scaffolding). Hide their TOOLS via `excluded_tools` instead.
- Merge semantics: prompts new-wins-else-inherit; `tool_description_overrides` per-key merge; `excluded_*` = set union; `extra_middleware` merged by concrete type; `general_purpose_subagent` field-wise; provider `init_kwargs` dict merge; `pre_init` callables chain; `init_kwargs_factory` chain + merge.
- Config-file form: `HarnessProfileConfig` (YAML/JSON; `to_dict`/`from_dict`; declarative subset only). `register_harness_profile` accepts either type. Plugins register via `importlib.metadata` entry points (`deepagents.harness_profiles` / `deepagents.provider_profiles`). Load order: built-ins → entry-point plugins → direct `register_*` calls.
- GP-subagent prompt resolution: `general_purpose_subagent.system_prompt` (if set) → `HarnessProfile.base_system_prompt` → SDK GP default, with suffix layered on top; GP-specific override wins over base when both set. (customization)
- `ProviderProfile` (model-construction only, string-model only): `init_kwargs` (static, forwarded to init_chat_model), `pre_init` (Callable[[str],None], e.g. credential checks), `init_kwargs_factory` (Callable[[],dict], runtime-derived kwargs).

### Suggested / tested models (models #suggested-models, #model-evaluations)
- Google `gemini-3.1-pro-preview`, `gemini-3.6-flash`; OpenAI `gpt-5.5`, `gpt-5.4`; Anthropic `claude-opus-4-8`, `claude-opus-4-7`, `claude-opus-4-6`; open-weight `GLM-5.2`, `Kimi-K2.7 Code`, `MiniMax-M3` (via Baseten/Fireworks/OpenRouter/Ollama). DeepSeek available via `langchain[deepseek]` / OpenRouter (`openrouter:deepseek/deepseek-v4-flash` scored 81% overall). Eval suite tests basic ops only — necessary not sufficient.

---

## 4. Context engineering
src: https://docs.langchain.com/oss/python/deepagents/context-engineering  (+ overview, multimodal)

### Assembled system prompt order (context-engineering #complete-system-prompt)
1. Custom `system_prompt` (if provided) 2. Base agent prompt 3. Memory prompt (AGENTS.md + guidelines, only if `memory`) 4. Skills prompt (locations + frontmatter list + usage, only if `skills`) 5. Virtual filesystem prompt (+ execute docs if sandbox) 6. Subagent/task-tool prompt 7. user middleware prompts 8. HITL prompt (if `interrupt_on`).
- Caller `system_prompt=` always at front; `system_prompt_suffix` always at end. Dynamic prompts via `@dynamic_prompt` middleware reading `request.runtime.context`/`.store`.

### Summarization (context-engineering #summarization)
- `SummarizationMiddleware` is in the bare stack (always present).
- Triggers at **85% of model's `max_input_tokens`** (from model profile). Keeps **10% of tokens** as recent context. Fallback if model profile unavailable: **170,000-token trigger / 6 messages kept**.
- On any `ContextOverflowError` from a model call → immediate fallback to summarization + retry with summary + recent preserved messages.
- Two outputs: (a) in-context structured summary (session intent, artifacts created, next steps) replaces full history; (b) full original conversation text written to filesystem (canonical record, recoverable via grep/read).
- Summarization tokens show up in streamed `messages`; filter via `metadata.get("lc_source") == "summarization"`.

### Offloading (context-engineering #offloading)
- Automatic; uses built-in filesystem tools. Threshold default **20,000 tokens**.
  - Tool-call INPUTS >20k tokens: as session context crosses **85% of window**, older write/edit tool calls truncated → replaced with pointer to file on disk.
  - Tool-call RESULTS >20k tokens: offloaded to configured backend, substituted with a file-path reference + preview of first 10 lines; agent can re-read/grep.
- Offloaded large results live under `/large_tool_results/`; conversation history under `/conversation_history/` (backends doc). Internal data is written to the DEFAULT backend — keep default = `StateBackend` to keep these ephemeral.
- Reasoning/thinking blocks: NOT specifically addressed by summarization/offloading docs. Multimodal doc notes offloading measures TEXT tokens only and non-text blocks are preserved, not compressed; summarization produces text-only summaries so media blocks in older turns DROP OUT. For OpenAI Responses encrypted reasoning see §3. (multimodal, models)
- Binary content offloading (base64 media out of message history, stored under `/blobs/<sha256>` or `artifacts_root`): opt-in via `FilesystemMiddleware(offload_binary_content=True)`, requires **deepagents>=0.7.21**; no effect when blob path routes to StateBackend — route blobs to Filesystem/sandbox. (backends #offload-binary-content)

### Prompt caching (overview #prompt-caching; customization)
- For Anthropic + Amazon Bedrock (Claude/Nova) models, caching is applied automatically to static prompt sections (base instructions, memory, skills). Enabled by default, no config.
- `AnthropicPromptCachingMiddleware` default TTL = **`5m`**; override by passing your own instance, e.g. `AnthropicPromptCachingMiddleware(ttl="1h")` (replaces default). (customization accordion "Update the prompt cache TTL")
- Other providers: see provider-specific caching middleware (integrations).
- Tool-search / deferred tools: NOT a deepagents feature in these pages. The lever to shrink per-turn tool schemas is `excluded_tools` on a harness profile (static, not runtime). (context-engineering #tool-prompts)

### Runtime context + custom state
- `context_schema` (dataclass/TypedDict) + `context=` on invoke/ainvoke; read via injected `ToolRuntime` (`runtime.context`, `runtime.store`). Runtime context PROPAGATES to all subagents. (context-engineering #runtime-context)
- `state_schema` must subclass `DeepAgentState` (preserves `DeltaChannel` reducer on `messages` → linear checkpoint growth). Requires **deepagents>=0.6.6**. Declarative SubAgent specs inherit parent `state_schema`; CompiledSubAgent/AsyncSubAgent do NOT.
- Long-term (cross-thread) memory: route a path (typically `/memories/`) to a `StoreBackend` via `CompositeBackend`; needs a `store`. (context-engineering #long-term-memory)

---

## 5. Permissions (filesystem allow/deny/interrupt)
src: https://docs.langchain.com/oss/python/deepagents/permissions

- Requires **deepagents>=0.5.2**. `interrupt` mode requires **>=0.6.8**. `delete` exact-match-for-files behavior requires **>=0.7.3**.
- `permissions=[FilesystemPermission(operations=[...], paths=[...], mode=...)]`.
  - `operations`: `"read"` (covers ls/read_file/glob/grep) and/or `"write"` (covers write_file/edit_file/delete).
  - `paths`: glob patterns, `**` recursive, `{a,b}` alternation.
  - `mode`: `"allow"` | `"deny"` | `"interrupt"` (default `"allow"`).
- Evaluated in declaration order, FIRST-MATCH-WINS; if no rule matches → ALLOWED (permissive default). Put specific rules before broad ones.
- Only applies to the 7 built-in filesystem tools. Does NOT cover custom tools, MCP tools, or sandbox `execute`. For custom validation use backend policy hooks.
- `mode="interrupt"` raises a HITL interrupt on matching write/edit/delete; requires a checkpointer; merges with `interrupt_on`. Directory delete is all-or-nothing (checks write on target + every descendant). Anchor interrupt patterns with a literal leading segment (bulk tools over-fire on unanchored patterns).
- Subagents INHERIT parent permissions by default; setting a subagent's `permissions` REPLACES parent rules entirely.
- CompositeBackend with a sandbox default: every permission path must be scoped under a known route prefix, else `NotImplementedError` (sandboxes allow arbitrary shell, so path rules alone can't contain them).

---

## 6. Human-in-the-loop
src: https://docs.langchain.com/oss/python/deepagents/human-in-the-loop

- `interrupt_on={tool_name: True | False | InterruptOnConfig}`. Adds `HumanInTheLoopMiddleware`. **Checkpointer REQUIRED** (e.g. `MemorySaver`/`InMemorySaver`).
- Decisions (`allowed_decisions`): `approve` (run as proposed), `edit` (modify args then run — edit conservatively), `reject` (skip + feedback to model), `respond` (synthetic tool result for "ask_user" tools). Default (`True`) allows all four. Do not use `respond` to deny side-effecting tools.
- `InterruptOnConfig` supports `allowed_decisions` and an optional `when` predicate (Python) receiving a `ToolCallRequest` → `True` interrupts, `False` auto-approves. Conditional interrupts require **langchain>=1.3.3**.
- Handle: check `result.get("__interrupt__")`, read `value["action_requests"]` + `["review_configs"]`, resume with `agent.invoke(Command(resume={"decisions": [...]}), config=<same thread_id>)`. Decisions must match action_requests order. Multiple pending interrupts batch together.
- Streaming: use `stream_mode=["messages","updates"]`; interrupts arrive as `__interrupt__` in `updates`. Subagent interrupts surface in parent `updates` without `subgraphs=True`; set `subgraphs=True` only to also stream subagent tokens.
- Subagents can each have their own `interrupt_on` (overrides main); subagent tools can also call `interrupt()` directly (resume with `Command(resume={...})`).

---

## 7. Backends (filesystem) + Windows notes
src: https://docs.langchain.com/oss/python/deepagents/backends

- `backend=` must implement `BackendProtocol`; default is `StateBackend()`.
- Built-ins:
  - `StateBackend` (default): thread-scoped, in LangGraph state, persists across turns via checkpointer, NOT across threads. Shared between supervisor + subagents. Avoid writing large files (checkpointed each step).
  - `FilesystemBackend(root_dir=<ABSOLUTE>, virtual_mode=True)`: real disk under root. `virtual_mode=True` sandboxes/normalizes paths (blocks `..`, `~`, absolute paths outside root); default `virtual_mode=False` gives NO security. Can use ripgrep for grep. Wrap in CompositeBackend so internal data stays in StateBackend. DON'T use in deployed/web-server agents.
  - `LocalShellBackend(root_dir=".", virtual_mode=..., env={...})`: extends FilesystemBackend + `execute` tool via `subprocess.run(shell=True)`, NO sandbox. Supports `timeout` (default 120s), `max_output_bytes` (default 100,000), `env`, `inherit_env`. Host-level; local dev only. DON'T deploy.
  - `StoreBackend(namespace=lambda rt: (...), store=...)`: cross-thread durable via LangGraph BaseStore. Omit `store` on LangSmith Deployment (auto-provisioned). `namespace` becomes REQUIRED (docs flag v0.5.0); namespace chars limited to alnum/`-_.@+:~`, wildcards rejected.
  - `ContextHubBackend("owner/name")`: durable files in a LangSmith Hub repo; needs `LANGSMITH_API_KEY`; optimistic parent-commit writes.
  - `CompositeBackend(default=..., routes={prefix: backend})`: path-prefix routing, longer prefix wins; preserves path prefixes in listings.
- Namespace factory `Callable[[Runtime], tuple[str,...]]`; `rt.context` / `rt.server_info` (assistant_id, user.identity) / `rt.execution_info` (thread_id, run_id, checkpoint_id). `server_info`/`execution_info` require **deepagents>=0.5.0**; Runtime arg (vs old BackendContext) requires **>=0.5.2** (BackendContext removed in >=0.7). Backend factory (`lambda rt: ...`) pattern DEPRECATED as of 0.5.0 — pass instances.
- Custom backend: subclass `BackendProtocol`, implement `ls/read/write/edit/glob/grep` (+ optional `delete`); implement `SandboxBackendProtocol` to add `execute`. Return structured result types with `error` field, never raise. Policy hooks: subclass or wrap a backend to block writes/edits by prefix.
- WINDOWS caveats: docs give no Windows-specific guidance. INFERRED for QMX (Windows 11 desktop host): `FilesystemBackend`/`LocalShellBackend` run on the host OS, so `root_dir` must be an absolute Windows path and `execute` runs Windows shell via `subprocess.run(shell=True)` (cmd semantics) — POSIX assumptions in agent-generated shell scripts may break. `execute` otherwise only exists on sandbox backends, which are remote/containerized (Linux) so Windows host doesn't affect them. StateBackend/StoreBackend are OS-agnostic (virtual). No sandbox provider is local-to-Windows; all are remote (LangSmith/Daytona/E2B/Modal/Runloop/Vercel/AgentCore/NVIDIA OpenShell).

---

## 8. Sandboxes + code execution
src: https://docs.langchain.com/oss/python/deepagents/sandboxes  (+ overview #code-execution)

- Sandbox backends ARE backends that also expose `execute`. Implement `SandboxBackendProtocolV2` (overview) / `SandboxBackendProtocol`; `execute` availability is checked on every model call and the tool is filtered out if unsupported.
- Only `execute()` must be implemented by a provider; all other file ops are built on it by `BaseSandbox`. Large output auto-saved to a file + agent told to `read_file`.
- Providers: LangSmith (`langsmith[sandbox]`), Daytona, E2B, Modal, Runloop, Vercel, AgentCore (Bedrock), NVIDIA OpenShell.
- File transfer (app-side, not agent tools): `upload_files([(abs_path, bytes)])` / `download_files([paths])` via provider native APIs.
- Interpreters (separate from sandboxes): `eval` tool running JS in a scoped QuickJS runtime — loops, batching, deterministic transforms, programmatic tool calling; NO shell/package/filesystem/network. (overview #code-execution, /deepagents/interpreters)
- Two patterns: agent-in-sandbox vs sandbox-as-tool (docs favor sandbox-as-tool: keeps API keys out of sandbox).
- SECURITY: sandboxes isolate the host but NOT against context injection / network exfiltration. NEVER put secrets inside a sandbox; keep secret-handling tools on the host, or use an auth proxy (LangSmith sandbox-auth-proxy injects headers). Relevant to QMX broker creds (which live in Windows Credential Manager — must never enter a sandbox or chat).

---

## 9. Going to production + durability / fault tolerance
src: https://docs.langchain.com/oss/python/deepagents/going-to-production and .../fault-tolerance

Durable execution (going-to-production #durability):
- Deep Agents run on LangGraph → durable execution out of the box. Persistence layer checkpoints state each step; a run interrupted by failure/timeout/HITL resumes from last checkpoint without reprocessing. Mid-run subagent failures don't lose completed work.
- Enables indefinite interrupts, time-travel (rewind to any checkpointed step), audit trail for sensitive ops.
- LangSmith Deployments configure a persistent checkpointer automatically; self-host → set up persistence yourself.
- Every production invocation carries `thread_id` (via `config={"configurable":{"thread_id":...}}`, scopes conversation/checkpoints) and `context` (per-run data, `context_schema`). Independent.
- Recommended deploy path: Managed Deep Agents (LangSmith, public beta) or a LangSmith Deployment (`langgraph build` → standalone Docker image). `langgraph.json` declares dependencies/graphs/env. Async: prefer native async tools + `a*` middleware hooks; sandbox/MCP creation should be awaited (async graph factories).
- Multi-tenancy: custom auth + authorization handlers; RBAC (Workspace Admin/Editor/Viewer); end-user creds via Agent Auth OAuth or sandbox auth proxy; workspace secrets for shared keys.
- Frontend: `useStream` hook (React/Vue/Svelte/Angular); set high `recursionLimit` (e.g. 10000) + `streamSubgraphs: true` for many-subagent workflows.

Fault-tolerance middleware (fault-tolerance) — all from `langchain.agents.middleware`, pass via `middleware=`:
- `ModelRetryMiddleware(max_retries, backoff_factor, initial_delay)` + `ToolRetryMiddleware(max_retries, tools=[...], retry_on=(...))` — transient errors, exponential backoff. Scope tool retries to network tools.
- `ToolErrorMiddleware(on_error)` — convert chosen tool exceptions to error ToolMessages (LLM recovers); unlisted exceptions propagate. Requires **langchain>=1.3.14**.
- `ModelFallbackMiddleware("<fallback-model>")` — provider outage failover.
- `ModelCallLimitMiddleware(run_limit=, thread_limit=)` + `ToolCallLimitMiddleware(run_limit=, thread_limit=)` — cap runaway loops (`thread_limit` needs checkpointer).
- Provider rate limiting: init model with `rate_limiter=InMemoryRateLimiter(requests_per_second, check_every_n_seconds, max_bucket_size)`.
- Chat models auto-retry transient API failures with backoff; integration packages raise typed exceptions (`ModelRateLimitError`, `ModelTimeoutError`, ...) carrying `is_retryable` respected by retry middleware. (customization tip, fault-tolerance note)
- PII: `PIIMiddleware("email", strategy="redact"|"mask"|"hash"|"block", apply_to_input=True)`.

---

## 10. Structured output + MCP + subagents (brief)
- Structured output: pass `response_format=<pydantic/schema>`; result in `result["structured_response"]`. (customization #structured-output)
- MCP: install `langchain[mcp]`; load tools via `MCPAdapter(config)` → `await adapter.list_tools()` → `tools=`. Full support (stdio/OAuth/filtering/stateful). (customization #mcp-tools)
- Subagents: built-in `task` tool spawns ephemeral subagents (fresh isolated context, autonomous, single final report, stateless). Default general-purpose subagent auto-added. To run WITHOUT the `task` tool: set `general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False)` AND pass no synchronous `subagents=` (do NOT exclude SubAgentMiddleware — raises ValueError). Declarative subagent dict: `{name, description, system_prompt, tools, permissions?, interrupt_on?, model?}`. (overview #subagents, subagents, profiles)

---

## 11. QMX-relevant takeaways (INFERRED application, not doc claims)
- Interactive copilots (general/Lab/Portfolio) map to separate `create_deep_agent` instances or declarative subagents under one supervisor; organogram = parent agent + `task`-spawned subagents each with own model/tools/skills/permissions.
- Daily model Claude Opus 5.5 via CLIProxyAPI (OpenAI/Anthropic-compatible local proxy): build a `ChatAnthropic`/`ChatOpenAI` instance with `base_url` → pass as `model=`. Cheap background models (DeepSeek, GPT-6 Luna/Sol) selectable per-run via `@wrap_model_call` + runtime context, or as distinct background-agent instances. Anthropic-path models get free automatic prompt caching (5m, bump to 1h); OpenAI-compatible proxy likely won't trigger Anthropic cache middleware (it no-ops on non-Anthropic) — INFERRED.
- Long-running background/remote workflow agents: lean on LangGraph durable execution + checkpointer + call limits + retries; run heavy/code work in a remote sandbox (sandbox-as-tool), keep broker creds OFF the sandbox and out of chat (Windows Credential Manager rule).
