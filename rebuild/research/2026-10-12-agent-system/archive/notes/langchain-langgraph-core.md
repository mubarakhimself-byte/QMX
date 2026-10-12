> SUPERSEDED 2026-10-12 by `tracker/qma-v2/PRD.md` (see `tracker/qma-v2/FILE-INDEX.md`). Kept for history.

# LangChain v1 + LangGraph — Core Notes for QMX Agent Layer
Scope: LangChain (Python) agents/middleware/memory/models + LangGraph persistence/
interrupts/streaming/durability. Pins in use: langchain 1.4.3, langchain-core 1.6.7,
langgraph 1.2.14, langgraph-checkpoint 4.2.0, langgraph-checkpoint-sqlite 3.1.1,
langchain-anthropic 1.7.5. Daily model: Claude Opus 5.5 (thinking blocks in history
must be preserved append-only). Each fact cites its source doc URL. "_" in URLs = "/".
Doc version note: these are "next"/future-dated docs (examples show gpt-5.5, claude-sonnet-5,
claude-opus-4-8, langchain v1.2/1.4), so version floors quoted below are authoritative.
## 0. CRITICAL FINDING — reasoning / thinking-block preservation
QUESTION: Do summarization / context-editing (or memory trimming) preserve
reasoning/thinking blocks, and are Anthropic thinking-block *signatures* preserved?
ANSWER: **NOT ADDRESSED.** Across all core pages read (middleware/built-in,
middleware/custom, short-term-memory, long-term-memory, context-engineering, models,
persistence, checkpointers, stores, interrupts, streaming, event-streaming), there is
NO statement that SummarizationMiddleware or ContextEditingMiddleware preserve,
re-attach, or protect reasoning/`thinking` content blocks or their Anthropic
cryptographic *signatures*. The word "signature" never appears in a reasoning-block
sense (only Python function signatures and an unrelated LangSmith usage-signing secret).
  - SummarizationMiddleware is explicitly described as *text-oriented*: "Summarization
    is text-oriented context compression. It does not resize, downsample, or otherwise
    compress image/audio/video payloads." — older multimodal/other blocks that are
    summarized are "represented only by the generated text summary." (middleware/built-in).
    By implication, summarized older messages (incl. any reasoning blocks in them) are
    replaced by text; whether `keep`-retained recent messages keep reasoning blocks
    intact is NOT stated. [INFERRED risk: summarization that rewrites message history
    could strip thinking-block signatures on retained AI messages — verify in code.]
  - ContextEditingMiddleware / ClearToolUsesEdit only clears *tool* outputs/inputs, not
    reasoning blocks (middleware/built-in). Does not touch reasoning content.
  - Reasoning IS a first-class content-block type: `content_blocks` entries with
    `{"type": "reasoning", "reasoning": "..."}` (models; event-streaming `reasoning-delta`).
    But nothing documents signature round-tripping through checkpointers/summarization.
  - Adjacent (OpenAI, not Anthropic): deep-agents can disable Responses-API data
    retention and still carry reasoning via `include=["reasoning.encrypted_content"]`
    with `use_responses_api=True, store=False` (releases_changelog, Dec 2025). This is
    OpenAI encrypted reasoning, NOT Anthropic thinking signatures.
  - JsonPlusSerializer (default checkpointer serde) round-trips LangChain message
    primitives (checkpointers), so a thinking block stored verbatim in a persisted
    AIMessage should survive a checkpoint round-trip — but this is about serialization
    fidelity, not about summarization/trimming re-writes. [INFERRED]
ACTION FOR QMX: Opus 5.5's append-only thinking-history rule is a risk wherever
middleware rewrites `messages` (summarization, trim, delete, context-editing). Must be
validated against langchain-anthropic 1.7.5 behavior directly; docs give no guarantee.
## 1. MIDDLEWARE — overview & architecture
Source: /oss/python/langchain/middleware (overview), .../middleware/built-in, .../middleware/custom
- Middleware tightly controls the agent loop (model call -> tool selection -> finish).
  Added via `create_agent(model, tools, middleware=[...])`. (overview)
- Not a separate runtime: hooks run inside the compiled LangGraph that create_agent
  returns; the whole agent (with middleware) can be dropped into a larger StateGraph as
  a node/subgraph and all hooks still run. (overview)
- Execution order (overview/custom "Execution order"): `before_*` run first→last across
  the middleware list; `after_*` run last→first (reverse); `wrap_*` nest like function
  calls (first middleware is outermost, wraps all others). Order: before_agent (once) →
  [loop: before_model → wrap_model_call(nested) → model → after_model(reverse)] →
  after_agent (once, reverse).
### 1a. CUSTOM MIDDLEWARE HOOKS (middleware/custom)
Node-style hooks (return a dict merged into state via reducers; or None):
  - `before_agent`  — before agent starts (once per invocation)
  - `before_model`  — before each model call
  - `after_model`   — after each model response
  - `after_agent`   — after agent completes (once per invocation)
Wrap-style hooks (control whether/how many times handler runs — short-circuit/retry):
  - `wrap_model_call(request: ModelRequest, handler) -> ModelResponse`  — around each model call
  - `wrap_tool_call(request: ToolCallRequest, handler) -> ToolMessage | Command` — around each tool call
Both decorator form (`@before_model`, `@after_model`, `@wrap_model_call`,
  `@wrap_tool_call`, plus convenience `@dynamic_prompt`) and class form
  (`AgentMiddleware` subclass, sync+async e.g. `abefore_model`/`aafter_model`).
Class attributes picked up at compile time: `state_schema` (extend AgentState),
  `tools` (ship extra tools, e.g. write_todos), `transformers` (stream transformer factories).
- **Dynamic model selection**: in `wrap_model_call`, `return handler(request.override(model=...))`
  (e.g. pick complex vs simple model by `len(request.messages)`). (custom)
- **Dynamic prompt**: `request.system_message` is ALWAYS a SystemMessage (even if agent
  made with a string); use `.content_blocks`; `request.override(system_message=...)`.
- **Dynamic tool selection**: `request.override(tools=relevant_tools)` (all tools must be
  registered upfront). (custom)
- **Anthropic prompt caching (manual)**: append a content block with
  `"cache_control": {"type": "ephemeral"}` to system_message content_blocks in
  wrap_model_call — content up to that block is cached. (custom)
- State updates: node hooks return dict; wrap_model_call can return `ExtendedModelResponse(
  model_response=..., command=Command(update={...}))`; wrap_tool_call returns `Command`.
  Composition: commands applied through reducers (messages additive); OUTER wins on
  non-reducer conflicts; retry-safe (earlier handler() commands discarded on re-call).
- **Agent jumps**: return `{"jump_to": "end"|"tools"|"model", ...}`; must declare
  `@hook_config(can_jump_to=[...])` (or `can_jump_to=` on decorator). (custom)
- Custom state schema: subclass `AgentState` (TypedDict, NotRequired fields); pass via
  `state_schema=` on decorator/class or create_agent. (custom / short-term-memory)
- Tracing: `trace_policy = TracePolicy(process_inputs=omit_payload)`; global
  `configure_trace_policy(...)`. Requires **langchain>=1.3.15**. (custom)
- Custom stream transformers: `transformers` class attr = tuple of
  `Callable[[scope_tuple], StreamTransformer]`. Requires **langchain>=1.3.2**. (custom)
### 1b. BUILT-IN MIDDLEWARE (middleware/built-in) — provider-agnostic
(one line + key params each)
- **ToolErrorMiddleware(on_error, aon_error, tools)** — catch tool exceptions → error
  ToolMessage(status="error"); return None to propagate. Does NOT retry. Requires
  **langchain>=1.3.14**.
- **ToolRetryMiddleware(max_retries=2, tools, retry_on=default, on_failure="continue"|
  "error"|callable, backoff_factor=2.0, initial_delay=1.0, max_delay=60.0, jitter=True)**
  — retry failed tool calls w/ exp backoff. Default retry_on (**langchain>=1.3.16**)
  retries retryable model errors + unclassified, skips non-retryable. Place retry INNER
  of ToolError, with on_failure="error".
- **ModelRetryMiddleware(max_retries=2, retry_on, on_failure="continue"|"error"|callable,
  backoff_factor=2.0, initial_delay=1.0, max_delay=60.0, jitter=True)** — retry model
  calls; on_failure="continue" returns AIMessage w/ error. backoff_factor=0.0 = constant.
- **ModelFallbackMiddleware(first_model, *additional_models)** — fall back to alt models
  in order when primary fails; models = id string or BaseChatModel. (For model outages /
  cost / provider redundancy.)
- **SummarizationMiddleware(model, trigger, keep=("messages",20), token_counter,
  summary_prompt, trim_tokens_to_summarize=4000)** — auto-summarize older history near
  token limits. `trigger` = ContextSize tuple ("tokens",N)/("messages",N)/("fraction",0-1),
  or TriggerClause dict (AND of thresholds), or list of them (OR). `keep` = exactly one of
  fraction/tokens/messages. `fraction` conditions need model **profile data (langchain>=1.1)**.
  Deprecated: summary_prefix, max_tokens_before_summary, messages_to_keep.
  TEXT-ONLY compression (see §0).
- **HumanInTheLoopMiddleware(interrupt_on={tool_name: True|False|{allowed_decisions:[...]}})**
  — pause for approve/edit/reject of tool calls. Matches each tool's `.name`. REQUIRES a
  checkpointer. (full detail in §5)
- **ModelCallLimitMiddleware(thread_limit, run_limit, exit_behavior="end"|"error")** —
  cap model calls per thread/run. thread_limit needs checkpointer.
- **ToolCallLimitMiddleware(tool_name=None, thread_limit, run_limit, exit_behavior=
  "continue"|"error"|"end")** — cap tool calls globally or per-tool; ≥1 of thread/run
  limit required; thread_limit needs checkpointer; "end" only for single-tool scenarios
  (else NotImplementedError). Compose multiple instances for per-tool limits.
- **PIIMiddleware(pii_type, strategy="redact"|"block"|"mask"|"hash", detector=None,
  apply_to_input=True, apply_to_output=False, apply_to_tool_results=False)** — detect/
  handle PII. Built-in types: email, credit_card, ip, mac_address, url; custom via regex
  string / compiled regex / fn returning list[PIIMatch]. With apply_to_output=True also
  redacts streamed wire output via a registered stream transformer — requires **langchain>=1.3.2**.
- **TodoListMiddleware(system_prompt, tool_description)** — gives agent a `write_todos`
  tool + planning prompt for multi-step tasks.
- **LLMToolSelectorMiddleware(model=agent's model, system_prompt, max_tools, always_include)**
  — LLM pre-selects relevant tools before main model (for 10+ tools). always_include
  bypasses max_tools.
- **ProviderToolSearchMiddleware(searchable_tools=[])** — defer tools behind provider
  server-side tool search; surfaced on demand. Needs Anthropic (Claude Sonnet 4+/Opus 4+/
  Haiku 4.5+) or OpenAI (gpt-5.5+); else ValueError. Tools w/ `extras={"defer_loading":True}`
  always deferred. (This is the "tool search" feature.)
- **ShellToolMiddleware(workspace_root, startup_commands, shutdown_commands,
  execution_policy=HostExecutionPolicy()|DockerExecutionPolicy()|CodexSandboxExecutionPolicy(),
  redaction_rules, tool_description, shell_command="/bin/bash", env)** — persistent shell
  session. Does NOT work with interrupts yet.
- **FilesystemMiddleware(backend=StateBackend, system_prompt, custom_tool_descriptions,
  tools=["read_file","ls","glob","grep",...])** — from Deep Agents; tools ls/read_file/
  write_file/edit_file. Short-term = graph state (StateBackend); long-term persistence via
  `CompositeBackend(default=StateBackend(), routes={"/memories/": StoreBackend()})` —
  files under /memories/ persist across threads via the store.
- **SubAgentMiddleware(default_model, default_tools, subagents=[...])** — from Deep Agents;
  exposes a `task` tool to spawn subagents. (detail in §9)
- **RubricMiddleware(model, max_iterations=3)** — LLM-as-judge self-eval loop until rubric
  satisfied. Requires **deepagents>=0.6.5**; BETA.
- **FilesystemFileSearchMiddleware(root_path, use_ripgrep=True, max_file_size_mb=10)** —
  adds glob_search + grep_search tools.
- **ContextEditingMiddleware(edits=[ClearToolUsesEdit(trigger=100000, clear_at_least=0,
  keep=3, clear_tool_inputs=False, exclude_tools=(), placeholder="[cleared]")],
  token_count_method="approximate"|"model")** — clear older TOOL outputs at token
  threshold, keep recent N. (Does not touch reasoning — see §0.)
- **LLMToolEmulator(tools=None, model=agent's model)** — emulate tool execution via LLM
  for testing (None = emulate all, [] = none).
Provider-specific middleware (built-in "Provider-specific" section):
  - Anthropic: `AnthropicPromptCachingMiddleware` (prompt caching), bash tool, text editor,
    memory, file search middleware for Claude.
  - AWS: `BedrockPromptCachingMiddleware` (Bedrock prompt caching).
  - OpenAI: content moderation middleware.
## 2. MODELS (/oss/python/langchain/models)
- `init_chat_model("provider:model" | "model", model_provider=..., ...)` — single entry
  point. `{model_provider}:{model}` format e.g. "openai:o1", "anthropic:claude-sonnet-5".
- **Custom base_url** (OpenAI-compatible APIs, e.g. Together AI, vLLM):
  `init_chat_model(model="MODEL_NAME", model_provider="openai", base_url="BASE_URL",
  api_key="YOUR_API_KEY")`. Warning: model_provider="openai" targets official OpenAI
  spec; router/proxy-specific fields may not be preserved.
- **Configurable models**: `init_chat_model(temperature=0)` with no model → `model` and
  `model_provider` configurable by default; select at call time via
  `config={"configurable": {"model": "..."}}`. `configurable_fields=("model",
  "model_provider","temperature","max_tokens")` + `config_prefix="first"`. Supports
  declarative bind_tools/with_structured_output on configurable models.
- **Model profiles (langchain>=1.1, BETA)**: `model.profile` dict — max_input_tokens,
  image_inputs, reasoning_output, tool_calling, structured_output,
  reasoning_effort_levels, reasoning_effort_default, etc. Powered by models.dev data +
  LangChain augmentations. Used by SummarizationMiddleware fraction triggers, structured
  output strategy inference, modality gating. Override via `init_chat_model(..., profile=
  custom_profile)` or mutate the dict (use model_copy to avoid shared-state mutation).
  CLI: `langchain-model-profiles` / `langchain-profiles refresh --provider <p> --data-dir`.
- **Reasoning**: surface via `content_blocks` entries `{"type":"reasoning","reasoning":...}`
  (stream or complete). `reasoning_effort` standard param (low/medium/high tiers or int
  token budget; or turn off) — requires **langchain-core>=1.5.2** + partner pkg
  (langchain-anthropic>=1.5.3, langchain-openai>=1.4.1, -fireworks>=1.5.2, -xai>=1.3.0,
  -google-genai>=4.3.1, -aws>=1.7.0). Native aliases: ChatAnthropic `effort`,
  ChatGoogleGenerativeAI `thinking_level`. Check model.profile["reasoning_effort_levels"]/
  ["reasoning_effort_default"].
- **Model fallback** at model layer = ModelFallbackMiddleware (§1b) for agents.
  (Standalone `.with_fallbacks` not covered on this page.) [INFERRED: use middleware for agents.]
- Structured output: `with_structured_output(Schema, include_raw=False, method=
  'json_schema'|'function_calling'|'json_mode')`. Pydantic validates; TypedDict/JSON schema
  need manual validation. Nested schemas supported.
- Prompt caching: implicit (OpenAI/Gemini auto), provider-explicit (OpenAI
  prompt_cache_key, Anthropic content-block cache_control, Gemini, Bedrock cachePoint),
  or LangChain middleware (Anthropic/Bedrock). Cache usage in response usage metadata.
- Multimodal in/out via content blocks; cross-provider standard + OpenAI + native formats.
- Local models via Ollama. rate_limiter param supported.
## 3. SHORT-TERM MEMORY (/oss/python/langchain/short-term-memory)
- = thread-scoped conversation state. Enable by passing `checkpointer=` to create_agent.
  State read at start of each step, updated after invoke / each step (e.g. tool call).
- Dev: `InMemorySaver()` (langgraph.checkpoint.memory). Prod: DB-backed, e.g.
  `PostgresSaver.from_conn_string(DB_URI)` then `checkpointer.setup()`
  (pip install -U langgraph-checkpoint-postgres "psycopg[binary]"). SQLite also available.
- Thread: `config={"configurable": {"thread_id": "1"}}`.
- Custom state: subclass `AgentState` with extra fields; pass `state_schema=`; extra keys
  passed in `agent.invoke({...})`.
- Common patterns to stay in context window:
  - **Trim messages**: `@before_model` returns `{"messages":[RemoveMessage(id=
    REMOVE_ALL_MESSAGES), *kept]}` (langgraph.graph.message.REMOVE_ALL_MESSAGES). LangChain
    `trim_messages` util (max_tokens + strategy) also available.
  - **Delete messages**: `RemoveMessage(id=m.id)` or REMOVE_ALL_MESSAGES; state key must use
    `add_messages` reducer (default AgentState has it). WARNING: keep history valid for
    provider (start with user msg; assistant tool_calls must be followed by tool results).
  - **Summarize**: use SummarizationMiddleware (§1b).
- Access state: in tools via `runtime: ToolRuntime` (hidden from model) — `runtime.state[...]`,
  write via returning `Command(update={...})`; in middleware via `@dynamic_prompt` /
  before_model / after_model.
## 4. LONG-TERM MEMORY (/oss/python/langchain/long-term-memory) + STORES (/oss/python/langgraph/stores)
- Cross-thread persistence, built on LangGraph **stores** (JSON docs by namespace+key).
  Pass `store=` to create_agent; tools access via `runtime.store`.
- Namespace = tuple[str,...] (e.g. ("users",) or (user_id,"memories")); key = unique id.
  Prefix matching on search; hierarchical org.
- Store API: `put(ns, key, value, index=None)`, `get(ns, key)->Item|None`,
  `search(ns_prefix, query=None, filter=None, limit=10, offset=0)`, `delete(ns,key)`,
  `list_namespaces(prefix,suffix,max_depth,limit,offset)`. Async: aput/aget/asearch/
  adelete/alist_namespaces. Item attrs: value, key, namespace, created_at, updated_at.
- Backends: **InMemoryStore** (dev/test), **PostgresStore**/AsyncPostgresStore (prod,
  used by LangSmith), MongoDBStore, RedisStore, UpstashStore, custom (subclass BaseStore —
  5 async methods required, sync optional). SqliteStore: NOT listed as a built-in store
  (SQLite exists for *checkpointers* only — see §6). [note: task asked "SqliteStore?" → not documented]
- Semantic search: configure `index={"embed": init_embeddings("openai:text-embedding-3-small"),
  "dims":1536, "fields":["food_preference","$"]}` (or IndexConfig(embed, dims)); per-item
  `index=[...]` or `index=False`. Query: `store.search(ns, query="...", limit=3)`. Custom
  backends raise NotImplementedError if query passed w/o vector support; include `score`.
- Ordering: PostgresStore ordered by updated_at DESC; InMemoryStore insertion order; do
  not rely on order across backends. Results past `limit` silently truncated; paginate
  via offset.
- In LangGraph: compile with both `checkpointer=` and `store=`; access via Runtime in
  nodes (`runtime.store.aput/asearch`, `runtime.context.user_id`). On Agent Server, base
  store auto-available; configure semantic search in langgraph.json "store.index".
## 6. LANGGRAPH PERSISTENCE / CHECKPOINTERS (/oss/python/langgraph/persistence, .../checkpointers)
Two systems: **Checkpointers** (thread-scoped state snapshots) + **Stores** (cross-thread).
- Checkpoint = StateSnapshot per super-step boundary. Fields: values, next (tuple; () =
  done), config (thread_id/checkpoint_ns/checkpoint_id), metadata (source input|loop|update,
  writes, step), created_at, parent_config, tasks (PregelTask: id,name,error,interrupts,state).
- Required for: human-in-the-loop, memory, time travel, fault-tolerance, **pending writes**
  (completed nodes' writes in a failed super-step are stored so resume doesn't re-run them).
- Per-task writes stored in `checkpoint_writes` as tasks complete (node-level durability),
  separate from full super-step snapshot.
- `thread_id` is the persistent cursor (reuse = resume; new = fresh). PostgresSaver:
  keep thread_id < 255 chars (use uuid7).
- Get/update state: `graph.get_state(config)`, `graph.get_state_history(config)` (newest
  first), `graph.update_state(config, values, as_node=...)` (new checkpoint; reducers
  accumulate). Replay: invoke with a prior `checkpoint_id` — nodes before skipped, after
  re-executed (incl LLM calls, interrupts always re-trigger).
- **DURABILITY MODES** (pass `durability=` to invoke/stream/stream_events):
  - `"exit"` — persist only when execution exits (success/error/interrupt); best perf for
    long graphs; no mid-execution crash recovery.
  - `"async"` — persist asynchronously while next step runs; good perf+durability; small
    risk of lost checkpoint on crash.
  - `"sync"` — persist synchronously before next step; highest durability, some overhead.
- Checkpointer libraries (all conform to BaseCheckpointSaver; methods put/put_writes/
  get_tuple/list + async aput/aput_writes/aget_tuple/alist + adelete_thread):
  - `langgraph-checkpoint` — base + **InMemorySaver** (bundled).
  - `langgraph-checkpoint-sqlite` — **SqliteSaver** / **AsyncSqliteSaver** (dev/local;
    separate install). [matches QMX pin langgraph-checkpoint-sqlite 3.1.1]
  - `langgraph-checkpoint-postgres` — **PostgresSaver** / **AsyncPostgresSaver** (prod).
  - `langgraph-checkpoint-mongodb` — MongoDBSaver / AsyncMongoDBSaver.
  - `langchain-azure-cosmosdb` — CosmosDBSaverSync / CosmosDBSaver (Entra ID auth).
  (MemorySaver/InMemorySaver are RAM-only, lost on restart.)
- Serializer: default **JsonPlusSerializer** (ormsgpack+JSON; handles LangChain/LangGraph
  primitives, datetimes, enums, pydantic v2, dataclasses, numpy). `pickle_fallback=True`
  for unsupported types (e.g. pandas). Encryption: `EncryptedSerializer.from_pycryptodome_aes()`
  reads `LANGGRAPH_AES_KEY`; auto-enabled on LangSmith when key present.
- **DeltaChannel** (storage optimization): stores incremental deltas not full channel
  value; O(1) checkpoint blobs for append-heavy channels (messages). Requires **langgraph>=1.2**
  and is BETA. Reconstructed by replaying ancestor writes; custom checkpointers need
  correct specific-id get_tuple + optional get_delta_channel_history.
- Subgraph checkpoint_ns: "" = root; "node_name:uuid" (nested joined with "|").
## 7. INTERRUPTS (/oss/python/langgraph/interrupts)
- `interrupt(value, response_schema=None)` (langgraph.types) pauses a node, persists state
  via checkpointer, surfaces `value` to caller, waits indefinitely. Needs: checkpointer +
  thread_id. Payload must be JSON-serializable.
- Resume: re-invoke with `Command(resume=<value>)` — becomes the return value of
  interrupt(). SAME thread_id required. `Command(resume=...)` is the ONLY Command form
  valid as input to invoke/stream/stream_events (update/goto/graph are for node returns;
  for multi-turn pass a plain input dict, NOT Command(update=...)).
- Surfacing: with event streaming `graph.stream_events(..., version="v3")` → payloads on
  `stream.interrupts`, `stream.interrupted` True when paused, final state on `stream.output`.
  With plain `invoke()` → `result["__interrupt__"]`.
- **response_schema** (Pydantic/TypedDict/dataclass) — validates resume value; exposed as
  JSON Schema in `Interrupt.response_schema`; returns validated object; invalid →
  pydantic.ValidationError (retry with same thread_id). JSON-schema dict passed through but
  NOT validated. Requires **langgraph>=1.2.12**.
- **Multiple interrupts** (parallel fan-out): `stream.interrupts` = tuple of Interrupt
  (each has `.id`,`.value`); resume all via `Command(resume={id: value, ...})` — matching
  is by id for the map form.
- Rules (node RE-RUNS from start on resume):
  - Multiple interrupts in one node matched STRICTLY BY INDEX — never reorder/conditionally
    skip/non-deterministically loop interrupt() calls.
  - Do NOT wrap interrupt() in bare try/except (catches the control exception); use
    specific exception types, or separate the interrupt from error-prone code.
  - Side effects before interrupt must be idempotent (place them after interrupt or in a
    separate node). Avoid `while True`+interrupt loops (exponential replay) — use a
    conditional edge that re-enters the node, calling interrupt() exactly once per invocation.
  - Pass only JSON-serializable values (no functions/class instances).
- Interrupts can live inside @tool functions (approval travels with the tool). Resume value
  can override tool args before execution.
- Subgraph-as-function: both parent node and subgraph node resume from their node start.
- Static breakpoints (debug only, NOT for HITL): `interrupt_before=[...]`,
  `interrupt_after=[...]` at compile or runtime; resume by invoking with `None` input.
## 8. STREAMING (/oss/python/langgraph/streaming) + EVENT STREAMING (/oss/python/langgraph/event-streaming)
### 8a. graph.stream()/astream() stream_mode values (streaming)
- `values` — full state snapshot after each step (ValuesStreamPart).
- `updates` — only changed keys per node after each step; multiple updates same step
  streamed separately (UpdatesStreamPart).
- `messages` — 2-tuple `(message_chunk, metadata)` LLM tokens; metadata has graph node +
  LLM invocation info; emitted even if LLM run via .invoke (MessagesStreamPart).
- `custom` — arbitrary user data from nodes/tools via get_stream_writer (CustomStreamPart).
- `checkpoints` — checkpoint events (get_state format); needs checkpointer.
- `tasks` — task start/finish (node, results, errors); needs checkpointer.
- `debug` — everything (checkpoints + tasks + extra metadata).
- Combine via list: `stream_mode=["updates","custom"]`.
- **Versioned output format of stream()**: `version="v2"` → every chunk is a StreamPart
  dict `{type, ns, data}` regardless of mode count/subgraphs (filter on chunk["type"]);
  "Requires LangGraph 1.1 or later." v1 (default) shape varies: single mode→raw dict;
  multi→(mode,data); subgraphs→(ns,data); multi+subgraphs→(ns,mode,data).
  `invoke(..., version="v2")` → GraphOutput with `.value` + `.interrupts`; dict access deprecated.
- Subgraphs: `subgraphs=True` on parent .stream() streams parent+subgraph; ns tuple path
  `("parent_node:<task_id>","child_node:<task_id>")`; applies to all modes incl messages.
  A create_agent added as a node is a subgraph — without subgraphs=True its inner LLM
  token chunks are NOT emitted on `stream_mode="messages"`.
- Token filtering: by `tags` (init_chat_model(tags=[...]) → metadata["tags"]); by node
  (metadata["langgraph_node"]); exclude an invocation with `nostream` tag via
  `.with_config({"tags":["nostream"]})`. Disable streaming: `streaming=False` at init, or
  `disable_streaming=True` (base-class, all chat models).
- Custom writer: `from langgraph.config import get_stream_writer`; `writer({...})`; needs
  `stream_mode="custom"`. Python<3.11 async: add a `writer: StreamWriter` param to the
  node/tool signature instead (get_stream_writer doesn't work), and pass RunnableConfig
  explicitly into async LLM calls.
### 8b. Event streaming API — stream_events(..., version="v3") (event-streaming)
- Typed-projection API "introduced in LangGraph v1.2". All examples use version="v3"
  (v1/v2 of stream_events not separately documented; only stream()'s v1/v2 are). Sync
  `stream_events`, async `astream_events`; returns a run-stream object read many ways
  concurrently (reading one projection doesn't consume others).
- Projections on the run stream: `stream` (every event), `stream.messages`, `stream.values`
  (iterate snapshots; final awaitable), `stream.output` (await final state),
  `stream.subgraphs`, `stream.interrupts`, `stream.interrupted` (bool),
  `stream.extensions` (custom transformer projections). (Task's `run.values/run.messages/
  run.lifecycle/run.subgraphs` groupings NOT present as such — exposed as `stream.*`.)
- Per-message (ChatModelStream): `message.text` (iterate for tokens / str() for full),
  `message.output.usage_metadata`, `message.reasoning` (reasoning deltas),
  `message.tool_calls` (tool-call arg chunks), `message.node`. For exact arrival order of
  text+reasoning+tool-calls, iterate raw events not separate projections.
- Subgraph projection: `subgraph.graph_name` (compiled graph/agent name; create_agent(name=)
  via Deep Agents task tool surfaces here), `subgraph.path`, `subgraph.messages`.
- Concurrent: async astream_events + asyncio.gather over async-for; sync
  `stream.interleave("values","messages","subgraphs")` yields (name,item) in arrival order.
- Resume: check stream.interrupted/stream.interrupts → call stream_events(Command(resume=...),
  version="v3") again; needs checkpointer + thread_id.
- **Raw v3 protocol**: ProtocolEvent `{seq (strictly increasing — use for ordering),
  method (channel), params}`; params = `{namespace (list["<name>:<runtime_id>"]; []=root),
  timestamp (ms, may drift — don't order by it), data}`.
- Channels (= method): values, updates, messages, tools, lifecycle, checkpoints, input
  (HITL), tasks, custom, `custom:<name>` (transformer output).
- **messages channel content-block protocol**: `data["event"]` ∈ {message-start,
  content-block-start, content-block-delta, content-block-finish, message-finish}.
  Blocks have explicit boundaries (start → 0+ deltas → finish before next block), making
  token/reasoning/tool-call/multimodal explicit "without requiring provider-specific
  formats". Delta block["type"]: `text-delta`(→block["text"]), `reasoning-delta`
  (→block["reasoning"]; example prints `[thinking]...`). message-finish may carry usage.
- tools channel events: tool-started, tool-output-delta, tool-finished, tool-error
  (correlated by tool call id). lifecycle events: started/running/completed/failed/
  interrupted (+ optional graph_name, error, cause).
- **Stream transformers**: two-layer (streaming emits raw Pregel events → event streaming
  normalizes, runs transformers, exposes typed projections). `StreamTransformer` interface
  (from langgraph.stream): init() / process(event)->bool (return False to suppress) /
  finalize() / fail(err); observational only. Class attr `required_stream_modes` (tuple);
  runtime uses the UNION across transformers as stream()'s stream_mode. `StreamChannel`:
  unnamed = side-channel at stream.extensions.<name>; `StreamChannel("name")` also forwards
  push() as `custom:<name>` protocol events (payload must be serializable).
  Registration: call-time `stream_events(..., transformers=[...])` or compile-time
  `builder.compile(transformers=[...])`. Ordering: transformers run in registration order;
  built-in projections first, then user transformers; built-in `ToolCallTransformer` (from
  langgraph.prebuilt) exposes `stream.tool_calls`; LangChain adds stream.tool_calls,
  Deep Agents stream.subagents.
- NOTE: the PII-redaction stream transformer the master task mentioned is NOT in these two
  files (it is referenced only from middleware/built-in + event-streaming "register
  transformers on middleware", requiring langchain>=1.3.2 per §1b).
- Version strings in these pages: only "Requires LangGraph 1.1 or later" (stream v2) and
  "typed-projection API introduced in LangGraph v1.2" (event streaming). No langchain>=1.3.2
  string here.
## 10. DURABLE EXECUTION — fault-tolerance, functional API, time travel, subgraphs
Sources: /oss/python/langgraph/{fault-tolerance, functional-api, use-time-travel, use-subgraphs}
### 10a. Fault tolerance (fault-tolerance) — MANY features require langgraph>=1.2
- Three composable mechanisms with FIXED order: node raises (incl NodeTimeoutError) →
  retry_policy decides retry → only after retries exhausted does error_handler run → else
  exception bubbles up.
- `set_node_defaults(retry_policy, error_handler, timeout, cache_policy)` — defaults for
  all nodes, resolved at compile(), order-independent; per-node add_node overrides. NOT
  inherited by subgraphs. (Requires langgraph>=1.2.)
- **RetryPolicy** (langgraph.types) via `retry_policy=` on add_node (also on @task/@entrypoint):
  max_attempts=3 (incl first), initial_interval=0.5s, backoff_factor=2.0, max_interval=128s,
  jitter=True, retry_on=default_retry_on. default_retry_on retries ANY exception EXCEPT
  (+subclasses) ValueError, TypeError, ArithmeticError, ImportError, LookupError, NameError,
  SyntaxError, RuntimeError, ReferenceError, StopIteration, StopAsyncIteration, OSError;
  for requests/httpx only retries 5xx; NodeTimeoutError retryable by default. Inspect via
  `runtime.execution_info` (node_attempt 1-indexed, node_first_attempt_time, thread_id,
  run_id, checkpoint_id, task_id).
- **Timeouts** (langgraph>=1.2, ASYNC-ONLY; sync node+timeout rejected at compile):
  `timeout=` seconds|timedelta|TimeoutPolicy(run_timeout, idle_timeout). run_timeout = hard
  per-attempt wall-clock; idle_timeout = progress-resetting (refresh_on="auto" default
  resets on state writes/stream output/child scheduling/stream-writer/callback events;
  "heartbeat" = only `runtime.heartbeat()`). On timeout → NodeTimeoutError (node, elapsed,
  kind "idle"|"run", idle_timeout, run_timeout), writes cleared, retry decides, clock resets
  per attempt. Dynamic per-push: `Send("node",{...}, timeout=TimeoutPolicy(...))`.
- **Error handling** (langgraph>=1.2) via `error_handler=` on add_node: runs after retries
  exhausted; signature `(state, error: NodeError)` (NodeError injected by annotation; also
  optional 3rd RunnableConfig arg; simpler (state) or (state, runtime) allowed). NodeError
  (langgraph.errors) = frozen dataclass {node: str, error: BaseException}. Handler returns
  `Command(update=..., goto=...)` → Saga/compensation. `interrupt()` BYPASSES retry+error
  handlers (GraphBubbleUp). Subgraph failure surfaces to parent node's error_handler
  (error.error). Resume-safe: failure provenance is checkpointed — handler sees same
  NodeError on resume after a crash. set_node_defaults matrix: retry/timeout apply to both
  regular & error-handler nodes; error_handler & cache_policy do NOT apply to handler nodes.
- **cache_policy** is a set_node_defaults/add_node param (node caching); CachePolicy detail
  not on this page.
- Pending-writes: writes from a failed/timed-out attempt are CLEARED before retry.
- **Named durability modes ("exit"/"async"/"sync") NOT covered by name here** (they are in
  checkpointers §6). This page covers retries/timeouts/error-handling + graceful shutdown.
- **Graceful shutdown** (langgraph>=1.2): pass `control=RunControl()` to invoke/stream;
  `request_drain(reason)` from any thread → cooperative, between supersteps, raises
  GraphDrained(reason) on remaining supersteps + saves resumable checkpoint; resume with
  `graph.invoke(None, config)` same thread_id; read `runtime.drain_requested`/`drain_reason`.
  Does NOT cancel asyncio tasks/kill threads.
### 10b. Functional API (functional-api)
- `@entrypoint(checkpointer=..., store=...)` (langgraph.func) → Pregel instance; exec via
  invoke/stream/stream_events(version="v3"); function takes ONE positional arg (use dict).
- `@task` (langgraph.func) → future-like; `.result()` / `await`; callable ONLY from inside
  an entrypoint/another task/a state-graph node (not from main app code). Task results
  saved to checkpoint, restored (not recomputed) on resume.
- Injectable entrypoint params by name+annotation: `previous` (prev checkpoint state),
  `store` (BaseStore), `writer` (StreamWriter, async<3.11), `config` (RunnableConfig).
- `entrypoint.final[return_type, save_type]` + `entrypoint.final(value=..., save=...)` —
  decouple returned value from checkpointed value; `save` becomes next invocation's `previous`.
- Short-term memory: with checkpointer, `previous` = prev invocation's return on same thread_id.
- Interrupts: `interrupt(payload)` inside entrypoint; resume `Command(resume=value)`; resume
  after error = invoke(None) same thread_id. Interrupt/resume matching is INDEX-BASED per task.
- Checkpointing difference: Graph API makes a new checkpoint after EVERY superstep;
  Functional API saves task results to the EXISTING entrypoint checkpoint (no per-task
  checkpoint). On resume, execution REPLAYS from entrypoint start; completed task/subgraph
  results restored from checkpointer, not recomputed → put non-deterministic work in @task,
  make started-but-unfinished tasks idempotent. Entrypoint I/O + task outputs must be
  JSON-serializable. @task supports retry_policy/timeout (same as nodes).
### 10c. Time travel (use-time-travel)
- Replay vs Fork, both from a prior checkpoint. Nodes BEFORE checkpoint not re-run; nodes
  AFTER re-execute (LLM/API/interrupts re-run, may differ). Replaying from final checkpoint
  (no `next`) is a no-op.
- `get_state_history(config)` → StateSnapshots reverse-chronological; each has `.next` and
  `.config[...]['checkpoint_id']`.
- Replay: pick checkpoint by `.next`, then `graph.invoke(None, checkpoint.config)`.
- Fork: `fork_config = graph.update_state(checkpoint.config, values={...})` then
  `graph.invoke(None, fork_config)`. update_state does NOT roll back — creates a new branch
  checkpoint; original history intact; applies via that node's writers/reducers; resumes
  from that node's SUCCESSORS.
- `as_node`: usually inferred; specify for parallel branches (else InvalidUpdateError), no
  history (fresh thread), or to skip nodes.
- Interrupts always re-trigger on time travel; fork from BETWEEN interrupts to change a later
  answer without re-asking earlier.
- Subgraph granularity: inherited checkpointer (default) → whole subgraph = one parent
  super-step, can't travel between its nodes; `checkpointer=True` on subgraph → own history,
  travel inside, inspect via `graph.get_state(config, subgraphs=True)` and
  `parent_state.tasks[0].state.config`.
### 10d. Subgraphs persistence (use-subgraphs)
- Subgraph = graph used as a node. Two patterns: (1) call inside a node (different schemas,
  wrapper maps I/O, `subgraph.invoke({...})`); (2) add compiled subgraph AS a node (shared
  state keys, no wrapper, reads/writes parent channels).
- **Persistence via `checkpointer=` on subgraph .compile()**:
  - None (default) = **per-invocation**: fresh each call BUT inherits parent's checkpointer
    for that call → supports interrupts + durable execution per call; supports parallel +
    repeated same-subgraph calls (each gets own checkpoint namespace). Recommended default.
  - `True` = **per-thread**: state accumulates across calls on same thread (multi-turn
    memory); does NOT support parallel tool calls (namespace checkpoint conflict → use
    ToolCallLimitMiddleware(run_limit=1) or disable parallel tool calling).
  - `False` = **stateless**: no checkpointing, runs like a plain function, NO interrupts, NO
    durable execution.
  - Parent graph MUST have a checkpointer for any subgraph persistence feature to work.
- Capability matrix (per-invocation/per-thread/stateless): interrupts ✅/✅/❌; multi-turn
  memory ❌/✅/❌; multiple calls diff subgraphs ✅/⚠️/✅; multiple calls same subgraph ✅/❌/✅;
  state inspection ⚠️(current invocation, while interrupted)/✅/❌.
- `get_state(config, subgraphs=True)` inspects subgraph state (access `.tasks[0].state`);
  requires LangGraph to statically discover the subgraph (added as node or called in a node);
  does NOT work when a subgraph is called inside a TOOL fn / other indirection (e.g. the
  subagents pattern) — but interrupts still propagate to top level regardless of nesting.
- Separate schemas → cross-level keys inaccessible; shared schema → private keys internal +
  shared keys written. Streaming subgraphs via stream_events v3 `stream.subgraphs`.
- create_agent produces a LangGraph graph → all these subgraph persistence concepts apply.
## 5. HUMAN-IN-THE-LOOP MIDDLEWARE (/oss/python/langchain/human-in-the-loop)
- `HumanInTheLoopMiddleware` (langchain.agents.middleware): after_model hook inspects the
  model response, builds a HITLRequest (action_requests + review_configs), calls LangGraph
  `interrupt`, waits, then executes approved/edited calls, synthesizes ToolMessages for
  rejected, returns human replies as ToolMessages for respond.
- **Four decision types**: `approve` (run as-proposed); `edit` (modify tool args first);
  `reject` (skip call, return rejection feedback to agent); `respond` (return human's
  message directly as a synthetic ToolMessage — tool NOT executed; ONLY for "ask user"
  tools). Do NOT use `respond` to deny a side-effecting tool (its message reads as success);
  use `reject` to deny.
- `interrupt_on` (dict, required): tool name → `True` (interrupt, all decisions),
  `False` (auto-approve), or `InterruptOnConfig`. Matches each tool's `.name`
  (@tool fn name).
- `InterruptOnConfig`: `allowed_decisions` (subset of approve/edit/reject/respond);
  `description` (string or callable); `when` (predicate on ToolCallRequest → True
  interrupts / False auto-approves — gates on args; **requires langchain>=1.3.3**).
  Middleware-level `description_prefix` default "Tool execution requires approval".
- REQUIRES a checkpointer (InMemorySaver dev; AsyncPostgresSaver/MongoDBSaver prod) + a
  `config` with `thread_id`.
- Interrupt `value` carries `action_requests` (name, arguments, description) and
  `review_configs` (action_name, allowed_decisions). Resume via
  `Command(resume={"decisions": [...]})` on the SAME thread_id. Decision shapes:
  `{"type":"approve"}`, `{"type":"edit","edited_action":{"name":...,"args":{...}}}`,
  `{"type":"reject","message":...}`, `{"type":"respond","message":...}`.
- MULTIPLE paused tool calls: one decision each, as a LIST in the SAME ORDER as the
  actions. Keep edits conservative (big arg changes may make the model re-run tools).
- Streaming: stream_events(version="v3"); check stream.interrupted/stream.interrupts;
  resume with Command(resume=...).
## 9. MULTI-AGENT (/oss/python/langchain/multi-agent[/subagents|/skills|/router])
- Not every task needs multi-agent; single agent + dynamic tools/prompt often suffices.
  Reasons to split: context management, distributed dev, parallelization.
- **Five patterns**: Subagents (supervisor calls subagents as tools; centralized routing);
  Handoffs (tool call updates a state var that triggers routing/config switch; agents can
  reply to user directly); Skills (on-demand specialized prompts/knowledge; single agent
  stays in control); Router (classify input → dispatch to specialized agent(s) → synthesize);
  Custom workflow (bespoke LangGraph, mix deterministic+agentic, embed other patterns).
- Fit: Subagents=distributed dev+parallel+multi-hop (weak direct user interaction);
  Handoffs=multi-hop+direct user; Skills=distributed dev+multi-hop+direct user;
  Router=parallelization. Mixable/nestable. (Model-call cost table shows subagents cost +1
  per task vs others because results route back through the supervisor; stateful patterns
  (handoffs/skills) are cheaper on repeat requests.)
- **Subagents** (multi-agent/subagents): supervisor calls subagents as tools; subagents
  STATELESS BY DEFAULT (memory held by supervisor → context isolation). **Main agent sees
  ONLY the subagent's FINAL message** (`result["messages"][-1].content`) — common failure:
  subagent does work but omits it from final message; must prompt it. Basic impl: wrap
  `subagent = create_agent(...)` in a `@tool` that calls `subagent.invoke(...)`. Patterns:
  tool-per-agent vs single-dispatch `task(agent_name, description)` tool; surface agent list
  via system-prompt enum / `Enum` constraint (<10) / `list_agents`/`search_agents` discovery
  tool (>10). Subagent inputs via `ToolRuntime[None, State]`. Deep Agents modes:
  `mode:"isolated"` (default, only task description) vs `mode:"fork"` (full parent message
  history + system prompt). Outputs can return `Command(update=...)` + ToolMessage
  (InjectedToolCallId). Checkpointing: inherited (default, fresh per invocation, interrupts
  + parallel-safe) vs `checkpointer=True` (persistent per-subagent history). Subagents called
  inside tool fns are NOT statically discoverable (get_state subgraphs won't see them).
  `langgraph-supervisor`/`create_supervisor` deprecated → use subagents pattern.
- **SubAgentMiddleware** / Deep Agents (middleware/built-in + agents): `SubAgentMiddleware(
  default_model, default_tools, subagents=[{name, description, system_prompt, tools, model,
  middleware}])` exposes a `task` tool; `CompiledSubAgent(name, description, runnable=<graph>)`
  wraps a prebuilt LangGraph as a subagent; a built-in `general-purpose` subagent (same
  instructions+tools as main) is always available for context isolation. (These names live
  in the built-in-middleware/agents docs, NOT the multi-agent/subagents page.)
- **Skills** (multi-agent/skills): prompt-driven specializations loaded on-demand via a
  `load_skill(skill_name)` tool (progressive disclosure, à la Agent Skills/llms.txt); can
  also register skill-specific tools + reference external assets. Ready-made
  langchain-ai/langchain-skills repo.
- **Router** (multi-agent/router): a classify step → `Command(goto=agent)` (single) or
  `Send(agent, {...})` list (parallel fan-out), both from langgraph.types; stateless by
  default; make stateful by wrapping as a tool a conversational agent calls, or full
  persistence (custom history). Router = lightweight classification; subagents/supervisor =
  conversation-aware orchestration.
## 11. RUNTIME / GUARDRAILS / CONTEXT-ENGINEERING / AGENTS / TOOLS / MEMORY CONCEPTS
### 11a. create_agent (/oss/python/langchain/agents)
- Agent = Model + Harness. `create_agent(model, tools, system_prompt=, response_format=,
  state_schema=, context_schema=, checkpointer=, store=, middleware=[...])`. model = "provider:
  model" string or instance. response_format=PydanticModel → `result["structured_response"]`.
- Agent loop: model call → tool execution, until model stops calling tools.
- `AgentState` (TypedDict) has append-only `messages: list[BaseMessage]`; it is the type for
  node-style hooks; subclass + state_schema= for custom fields.
- Invoke: `agent.invoke({"messages":[{"role":"user","content":...}]}, config={"configurable":
  {"thread_id":...}}, context=Context(...))`. Stream: `stream_events({...}, version="v3")`
  (iterate stream.values; invoke returns final only).
- Harness middleware categories: execution env (FilesystemMiddleware(backend=StateBackend())),
  context mgmt (FilesystemMiddleware, SummarizationMiddleware, MemoryMiddleware(backend=,
  sources=["./AGENTS.md"]), SkillsMiddleware(backend=, sources=["./skills/"])), planning/
  delegation (TodoListMiddleware, SubAgentMiddleware), fault tolerance (ModelRetryMiddleware,
  ToolRetryMiddleware), guardrails (PIIMiddleware), steering (HumanInTheLoopMiddleware).
- `create_deep_agent` pre-assembles filesystem+summarization+subagents+prompt caching;
  `deepagents` installed separately.
### 11b. Runtime (/oss/python/langchain/runtime)
- LangGraph `Runtime` provides: Context (static per-invocation: user id, db conns, deps),
  Store (BaseStore, long-term memory), Stream writer ("custom" stream mode), Execution info
  (thread_id, run_id, attempt), Server info (assistant/graph id, authed user on LangGraph
  Server). DI for tools/middleware instead of globals.
- `context_schema` on create_agent; pass `context=` at invoke; context is immutable per run.
- Tools: add `ToolRuntime[Context]` param → runtime.context/.store/.stream_writer/
  .execution_info/.server_info/.tool_call_id. Middleware node hooks take
  `(state, runtime: Runtime[Context])`; wrap hooks use `request.runtime`; `@dynamic_prompt`
  reads `request.runtime.context`.
- `runtime.execution_info` / `runtime.server_info` require **deepagents>=0.5.0 (or
  langgraph>=1.1.5)**.
### 11c. Guardrails (/oss/python/langchain/guardrails)
- Validate/filter content via middleware (before agent / after agent / around model & tool).
  Two approaches: deterministic (regex/keyword — fast, cheap) and model-based (LLM/classifier
  — semantic, slower/costlier).
- Built-in: PIIMiddleware (strategies redact/mask/hash/block; types email/credit_card(Luhn)/
  ip/mac_address/url; apply_to_input/output/tool_results; custom regex detectors;
  apply_to_output=True redacts streamed wire output — **requires langchain>=1.3.2**) and
  HumanInTheLoopMiddleware (approval before sensitive ops).
- Custom: `before_agent` hook with `@hook_config(can_jump_to=["end"])` returning a message +
  `"jump_to":"end"` to block input (e.g. banned keywords); `after_agent` hook to validate/
  rewrite final output (e.g. a separate model classifies SAFE/UNSAFE). Stack multiple for
  layered defense. Prompt-injection/jailbreak = a use case handled via these patterns (no
  dedicated built-in jailbreak detector).
### 11d. Context engineering (/oss/python/langchain/context-engineering)
- Goal: right info + tools + format. Three context types: Model Context (transient: instr/
  messages/tools/response format), Tool Context (persistent: tool reads/writes state/store/
  runtime), Life-cycle Context (persistent: summarization/guardrails/logging between calls).
- Three data sources: Runtime Context (static, conversation-scoped), State (short-term),
  Store (long-term, cross-conversation).
- Middleware is the mechanism. Model-context levers (all via middleware): system prompt
  (`@dynamic_prompt`), messages (`@wrap_model_call` + `request.override(messages=...)`;
  transient by default — for persistent return ExtendedModelResponse+Command or use
  before/after_model), tools (`request.override(tools=...)`), model
  (`request.override(model=...)`), response format (`request.override(response_format=...)`
  — final response guaranteed to conform; loop runs to completion then coerces).
- Tool context: read runtime.state/context/store; write via `Command(update=...)` (state)
  or `store.put(...)` (store). Life-cycle: SummarizationMiddleware permanently replaces old
  messages with a summary in state.
### 11e. Tools (/oss/python/langchain/tools)
- `@tool` (langchain.tools); docstring=description; TYPE HINTS REQUIRED; snake_case names.
  `@tool("name", description=..., parse_docstring=True, args_schema=Model|dict,
  return_direct=True)`. RESERVED arg names: `config`, `runtime`.
- `ToolRuntime` / `ToolRuntime[Context]` / `[Context, State]` param — auto-injected by
  ToolNode, hidden from model schema. Provides state, context, store (get/put), stream_writer,
  execution_info (thread_id/run_id/node_attempt), server_info, config, tool_call_id.
  execution_info+server_info require **deepagents>=0.5.0 (or langgraph>=1.1.5)**. Replaces
  older InjectedState/InjectedStore/get_runtime()/InjectedToolCallId.
- Return types: str→ToolMessage; dict/object→serialized; multimodal content blocks→ToolMessage
  w/ multimodal content; `Command`→update graph state (MUST include a ToolMessage matching
  runtime.tool_call_id or ToolNode raises ValueError; `graph=Command.PARENT` lifts that).
- `return_direct=True` short-circuits loop (final response, no extra model call); in mixed
  parallel batch, agent exits only if ALL calls are return_direct.
- Tool error handling via `@wrap_tool_call` (request: ToolCallRequest, handler) try/except →
  ToolMessage. Dynamic tool selection: (1) filter pre-registered via wrap_model_call +
  override(tools=...); (2) RUNTIME registration (e.g. MCP) needs BOTH wrap_model_call (add
  tool) AND wrap_tool_call (execute it). MCP: `MCPAdapter` (langchain.mcp) — requires
  **langchain[mcp]>=1.4.0 (beta)**. Headless tools: schema-only, implemented client-side via
  interrupt/resume handshake. ToolNode executes tools with state+context access.
### 11f. Memory concepts (/oss/python/concepts/memory)
- Short-term = thread-scoped message history in agent state, persisted via checkpointer.
  Long-term = cross-thread, in a Store, scoped by namespace. Three types (CoALA): Semantic
  (facts), Episodic (past experiences / few-shot), Procedural (rules = system prompt,
  updated via reflection/meta-prompting). Semantic mgmt: Profile (single JSON doc) vs
  Collection (many docs + semantic search; Trustcall helps).
- Writing memories: hot-path (during runtime — real-time/transparent but adds latency +
  multitasking) vs background (async task — no latency but timing/frequency choices).
  Store API: put/get/search(namespace, filter, query) with optional embedding index.
## 12. QMX RELEVANCE / ACTION FLAGS
- Pins match docs: langgraph-checkpoint-sqlite 3.1.1 → SqliteSaver/AsyncSqliteSaver for
  dev/local checkpointing (§6). No SqliteStore for long-term memory is documented — use
  Postgres/Mongo/Redis/Upstash or custom BaseStore for cross-thread memory (§4).
- Daily model Claude Opus 5.5 append-only thinking rule: NO doc guarantees that
  SummarizationMiddleware / ContextEditingMiddleware / trim/delete message ops preserve
  Anthropic thinking-block signatures (§0). Treat any `messages`-rewriting middleware as a
  risk; validate against langchain-anthropic 1.7.5 directly. Reasoning IS a content-block
  type and streams as `reasoning`/`reasoning-delta`, but signature round-trip is unspecified.
- Background/cheap-model agents: SubAgentMiddleware per-subagent `model=` + dynamic model
  selection in wrap_model_call (§1a, §9) let you route cheap models to background subagents;
  ModelFallbackMiddleware for provider redundancy.
- Durability for long/soak runs (QMX week-long soak): durability="sync" (§6) + a DB
  checkpointer + RetryPolicy/timeouts/error_handler + graceful shutdown (RunControl) — all
  require langgraph>=1.2 for timeouts/error-handlers/shutdown (§10a). DeltaChannel
  (langgraph>=1.2, beta) curbs checkpoint growth for the messages channel.
- HITL for money-path approvals: HumanInTheLoopMiddleware(interrupt_on={...}) needs a
  checkpointer + thread_id; `when` predicate (langchain>=1.3.3) gates on tool args (§5).
=== END ===
