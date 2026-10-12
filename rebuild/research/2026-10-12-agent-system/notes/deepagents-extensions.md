# Deep Agents Extensions — Extraction Notes (for QMX copilots + node workflows)

Pins: deepagents 0.7.22, langchain 1.4.3, langgraph 1.2.14. Sources are markdown copies of
`https://docs.langchain.com/oss/python/deepagents/<name>`. One URL cited per fact group.
TS-only code skipped. "INFERRED" marks my inference, not doc text.

Cross-cutting: `create_deep_agent(model=, tools=, subagents=, middleware=, skills=, memory=,
backend=, permissions=, interrupt_on=, checkpointer=, store=, system_prompt=, context_schema=, name=)`.
Deep Agents stack = ordered middleware auto-attached per the args you pass (SkillsMiddleware when
`skills`, SubAgentMiddleware when ≥1 sync subagent, AsyncSubAgentMiddleware when async subagents, etc.).

========================================================================
## SKILLS  (src: .../deepagents/skills)
========================================================================
- A skill = a directory containing `SKILL.md` (YAML frontmatter + markdown instructions), optional
  `scripts/`, `references/`, `assets/`. Follows the Agent Skills spec (agentskills.io/specification).
- Frontmatter fields (spec): `name` (req; lowercase alphanumeric+hyphens, 1–64 chars, MUST match
  parent dir name), `description` (req; what+when, max 1024 chars — the ONLY text seen at discovery),
  `license` (opt), `compatibility` (opt, max 500 chars, env requirements), `metadata` (opt arbitrary
  key-values), `allowed-tools` (opt, space-separated, pre-approved, experimental).
- Progressive disclosure, 3 levels (`SkillsMiddleware` handles L1–L2, LLM handles L3):
  L1 Metadata (name+description) injected into system prompt at startup for every skill;
  L2 Instructions (full SKILL.md body) read via `read_file` when agent invokes the skill;
  L3 Resources (scripts/references/assets) read only when instructions reference them.
- Keep frontmatter concise; SKILL.md body < 5,000 tokens recommended, < 500 lines per spec.
  Deep Agents SKIPS any SKILL.md > 10 MB at discovery.
- Config: pass `skills=["<dir>/"]` (list[str]). Each path is a *container* dir whose SUBDIRS are
  skills; pointing directly at a skill dir loads nothing (no error). Paths use forward slashes,
  relative to backend root. Omitted = no skills. Last source wins on name collision (layering:
  base then project).
- Backends for skill files: `StateBackend` (default; in-thread state — seed via
  `invoke(files={...})` using `create_file_data()` from `deepagents.backends.utils`, virtual paths
  start with "/"); `StoreBackend` (durable cross-thread, LangGraph store; `backend.upload_files([(path, bytes)])`);
  `FilesystemBackend(root_dir=, virtual_mode=True)` reads from disk, `virtual_mode` sandboxes under root_dir.
  SDK loads ONLY sources you pass — it does NOT auto-scan `~/.deepagents` / `~/.agents`.
- Skill tools (Deep Agents feature, not spec; requires deepagents>=0.7.22): list under
  `metadata.include_tools: tool_a tool_b` (SPACE-separated string; a YAML list matches nothing).
  Tools are GATED — unavailable until agent reads the SKILL.md (or skill is pinned); summarization
  dropping that read removes them until re-read. To add them, construct `SkillsMiddleware(backend=,
  sources=[...], tools=[...])` yourself and pass in `middleware=` (passing `skills=` builds a
  SkillsMiddleware without tools). `tools` may be a list OR a resolver fn `(name, runtime)->list[BaseTool]`
  (maps readable names→real/MCP tool names, can be async→use ainvoke, runs every model call after read).
  `ProviderToolSearchMiddleware` + `@tool(extras={"defer_loading":True})` makes a tool findable by
  search AND revealed by reading the skill (deferred tool is NOT gated).
- Skill availability / isolation: pick `skills` list per role/tenant before creating agent; OR route
  the same `/skills/` path to context-scoped storage via `CompositeBackend(default=StateBackend(),
  routes={"/skills/": StoreBackend(namespace=lambda rt: (...))})`. Compose multiple:
  `skills=["/skills/org/","/skills/team/","/skills/request/"]`. Route prefix (`/skills/`) is stripped
  before store read; store values need `content`+`encoding`.
- Permissions: read-only skills = `FilesystemPermission(operations=["write"], paths=["/skills/**"],
  mode="deny")`; writable = route writable paths to a persisting backend + pass in skills + deny
  specific paths (more specific rule first). Write approval = `mode="interrupt"` or
  `interrupt_on={"write_file":True,"edit_file":True}` (needs checkpointer; interrupts require
  deepagents>=0.6.8).
- Reload: skills load ONCE per thread, cached in state (when checkpointer present). To reload set
  `skills_metadata: None` (use None, NOT []; [] = "no skills for rest of thread") via run input or
  `agent.update_state`. Reset from `after_agent` not `after_model`. Requires deepagents>=0.7.16.
  Local runs w/o checkpointer reload every run (edits appear immediately). LangSmith Deployments have
  persistent checkpointer → skills held for life of thread.
- Pin skills (requires deepagents>=0.7.23): pass `pinned_skills=["name",...]` in run input. Middleware
  appends each skill's SKILL.md (frontmatter stripped) as a HumanMessage BEFORE next model call,
  wrapped `<skill name=".." path="..">...</skill>`, with `additional_kwargs["lc_source"]="pinned_skill"`
  and `additional_kwargs["skill"]={name,path,description}` (UI can render as a label). Pinning also
  makes the skill's tools available. Unknown/unreadable names skipped (DEBUG log). App parses the
  syntax (e.g. `/skill-name`) itself; Deep Agents does not scan messages.
- Per-agent/per-subagent skills: general-purpose subagent AUTO-inherits main agent's skills; custom
  subagents do NOT — give each `skills=["/skills/x/"]`. Skill state fully isolated both directions.
  Only subagents with a `skills` param get their own SkillsMiddleware.
- Executing skill scripts: agent can READ scripts from any backend but EXECUTING needs a shell =
  sandbox backend (`execute` tool). Sandbox backends run in isolated containers; skill files outside
  the sandbox must be copied in. Pattern: custom middleware `before_agent` uploads skill files into
  sandbox, `after_agent` downloads changed files back (e.g. LangSmithSandbox + StoreBackend route).

========================================================================
## MEMORY  (src: .../deepagents/memory)
========================================================================
- Long-term memory = filesystem-backed memory files the agent reads/writes via built-in `edit_file`.
  Pass file paths to `memory=["/memories/AGENTS.md"]`. A backend decides where files live/who sees them.
  (Short-term memory = conversation history + scratch files in state, managed automatically; separate.)
- AGENTS.md-style = semantic memory (facts/preferences) in a markdown file loaded into prompt at
  startup. Skills = procedural memory (how-to), on-demand. Episodic memory = full checkpointed threads
  (every conversation persisted); make searchable by wrapping `client.threads.search(metadata={...})`
  in a tool (scope by user_id/org_id from `runtime.server_info.user.identity`).
- Scoping via StoreBackend namespace (the routing mechanism):
  agent-scoped = `namespace=lambda rt: (rt.server_info.assistant_id,)` (shared across all users);
  user-scoped = `(rt.server_info.user.identity,)` (isolated per user);
  org-scoped/policies = `(rt.context.org_id,)` (typically read-only — prevents injection).
  Multi-agent deployment: add assistant_id to namespace tuple. `rt.server_info` needs deepagents>=0.5.0
  (older: `get_config()["metadata"]["assistant_id"]`).
- Pluggable: YES — memory is just filesystem paths + a backend. Standard pattern is
  `CompositeBackend(default=StateBackend(), routes={"/memories/": StoreBackend(...), "/policies/":
  StoreBackend(...), "/skills/": StoreBackend(...)})`. Seed via `store.put((ns,), "/path", create_file_data(txt))`
  or `client.store.put_item`. The `/memories/` route prefix convention is where long-term files live.
- Read-only vs writable: default read-write (agent uses edit_file). Read-only for org policies/compliance/
  developer skills — enforce with FilesystemPermission deny, or backend policy hooks
  (rate-limit/audit/content-inspect), or HITL interrupt before writes to sensitive paths.
- Background consolidation ("sleep-time compute"): a SEPARATE deep agent (the "consolidation agent")
  reads recent threads, extracts facts, merges into memory store on a cron. Register both graphs in
  `langgraph.json`; schedule via `client.crons.create(assistant_id="consolidation_agent", schedule=
  "0 */6 * * *", input={...})` (UTC). Cron interval MUST match the lookback window in the agent's
  thread-search tool. Hot-path (default, during conversation) vs background tradeoff table given.
- Concurrent writes = last-write-wins; mitigate by per-topic files or serializing via consolidation.
- See OpenWiki (below) for AGENTS.md-discovered repo wiki.

========================================================================
## SUBAGENTS — synchronous  (src: .../deepagents/subagents)
========================================================================
- Supervisor BLOCKS until sync subagent finishes. `subagents=` is a list of SubAgent dicts or
  `CompiledSubAgent` objects. Invoked by main agent via the `task(subagent_type=, description=)` tool
  (can issue several in one turn → parallel). Context quarantine: main agent gets only the final result.
- Default `general-purpose` subagent auto-added (unless you supply one named `general-purpose`): has
  filesystem tools + all same tools + same model + inherits skills. Replace by passing a subagent
  named `general-purpose`. Re-prompt/rename default via `general_purpose_subagent=
  GeneralPurposeSubagentProfile(...)` on the harness profile. Disable: set that profile's
  `enabled=False` AND pass no sync subagents (SubAgentMiddleware + `task` tool only attach when ≥1 sync
  subagent exists). Do NOT use `excluded_middleware` to remove SubAgentMiddleware (raises ValueError).
- SubAgent (dict) fields:
  `name` (req, unique; becomes AIMessage metadata + stream label),
  `description` (req, action-oriented; main agent uses it to decide delegation),
  `system_prompt` (req for mode="isolated"; does NOT inherit from main agent),
  `mode` ("isolated" default | "fork"),
  `tools` (opt; OVERRIDES inherited entirely when set; inherits main agent's by default),
  `model` (opt; "provider:model" string or BaseChatModel; inherits main agent's by default),
  `middleware` (opt; does NOT inherit; merged into sync-subagent stack — name match replaces in place,
     else lands after core middleware before profile/caching/memory; e.g. FilesystemMiddleware with a
     tools allowlist to restrict the subagent's fs tools),
  `interrupt_on` (opt; dict[str, bool|InterruptOnConfig]; needs checkpointer; inherits, subagent overrides),
  `skills` (opt; list[str] source paths; does NOT inherit; own isolated SkillsMiddleware),
  `response_format` (opt; structured output — Pydantic/ToolStrategy/ProviderStrategy/raw schema),
  `permissions` (opt; list[FilesystemPermission]; REPLACES parent's entirely when set).
- CompiledSubAgent fields: `name`, `description`, `runnable` (a compiled LangGraph graph — call
  `.compile()`; must have a state key `"messages"`), `mode` ("isolated"|"fork"; keeps own system prompt).
  Build via `create_agent(...)` or custom graph.
- Forked subagents (mode="fork"; requires deepagents>=0.7.13, BETA): inherit parent's FULL conversation
  history + exact system prompt (not a fresh task desc). Delegating call dropped + replaced with a short
  "Continuing as the subagent…" HumanMessage preamble → reuses parent prompt cache. `skills` REJECTED
  for forks; `system_prompt` allowed but appended as addendum (breaks cache — usually omit). Fork CANNOT
  use `task` (must finish work itself); isolated CAN. Use fork to continue parent's in-progress work.
- Structured output (requires deepagents>=0.5.3): set `response_format`; subagent result returned to
  parent as JSON-serialized ToolMessage content. Without it, parent gets subagent's last message text.
- Runtime context: parent `invoke(context=...)` auto-propagates to ALL subagents + their tools. Same
  context for every subagent; per-subagent config via namespaced/extra context fields. Identify caller
  via `runtime.config["metadata"]["lc_agent_name"]`.
- LangSmith: every subagent/coordinator run tagged metadata `lc_agent_name: <name>`; filter in UI or
  SDK (`filter='has(metadata, \'{"lc_agent_name":"research-agent"}\')'`).

### DYNAMIC subagents  (src: .../deepagents/dynamic-subagents + interpreters)
- Dispatch subagents FROM interpreter CODE (loops/branches/parallel batches) instead of one
  model-chosen `task` call at a time. Requires subagents + interpreter middleware (`CodeInterpreterMiddleware`).
  BETA. Needs `langchain-quickjs>=0.2.0` + Python ≥3.11. Install `pip install -U "deepagents[quickjs]"`.
- On by default when agent has subagents + interpreter. Disable with `CodeInterpreterMiddleware(subagents=False)`.
  Trigger word "workflow" in the user prompt signals the interpreter system prompt to fan out via code.
  `dcode` (LangChain terminal coding agent) ships with it enabled.
- Built-in `task()` global (JS): `task({description, subagentType, responseSchema?})` runs a full
  agentic loop, resolves to the subagent's result (typed object if responseSchema given — no JSON.parse).
- Patterns (emergent, from code shape): classify-and-act, fan-out-and-synthesize (needs PTC `glob` to
  discover files), adversarial verification (2-pass find→verify, majority vote), generate-and-filter,
  tournament (pairwise judge elimination), loop-until-done (dedupe until converged).
- Supports RLM (Recursive Language Model) workflows per arXiv:2512.24601 (cited): keep working set in
  interpreter vars, select slices, call subagents with task(), synthesize. Often combined with PTC.
- SECURITY: `task()` dispatches from inside a running `eval` — it does NOT go through the normal tool
  path, so parent `interrupt_on` approval is NOT enforced per-dispatch. Gate the `eval` tool itself if
  you need approval before orchestration runs.

### ASYNC subagents  (src: .../deepagents/async-subagents)
- Background tasks that return a task-id immediately so the supervisor keeps talking to the user;
  stateful (own thread), supports mid-flight updates + cancellation. Builds on Agent Protocol
  (github.com/langchain-ai/agent-protocol); any Agent-Protocol server works (LangSmith Deployments or
  self-host). AsyncSubAgentMiddleware auto-added when async subagents configured.
- `AsyncSubAgent(name, description, graph_id, url?, headers?)`:
  `graph_id` = graph/assistant id on the server (must match `langgraph.json` for co-deployed);
  `url` OMITTED → ASGI transport (in-process, co-deployed, no network latency, recommended default);
  `url` SET → HTTP transport to remote Agent Protocol server (auth via LANGSMITH_API_KEY /
  LANGGRAPH_API_KEY env, or custom `headers`); hybrid mix allowed.
- Supervisor gets 5 tools: `start_async_task` (→task_id now), `check_async_task` (status+result),
  `update_async_task` (new run on same thread, interrupt multitask strategy, restarts w/ full history +
  new instructions, same task_id), `cancel_async_task` (runs.cancel → "cancelled"), `list_async_tasks`
  (live statuses, parallel fetch for non-terminal; terminal cached).
- State: task metadata in a dedicated `async_tasks` state channel (separate from message history) so
  task IDs survive context compaction/summarization. Each task tracks task_id, agent name, thread_id,
  run_id, status, created_at/last_checked_at/last_updated_at.
- Topologies: single (all ASGI, one langgraph.json — recommended start), split (supervisor + remote via
  HTTP), hybrid. Local: `langgraph dev --n-jobs-per-worker 10` (1 supervisor + N subagents = N+1 slots;
  under-provision → launches queue). Reference repo: langchain-ai/async-deep-agents.
- Troubleshooting prompts: middleware injects rules "don't poll right after launch", "statuses in
  history are always stale — re-check", "use full task_id, never truncate".
- QMX fit (INFERRED): async subagents = the "long-running background/remote workflow agents built in a
  node editor" — each node = an AsyncSubAgent graph_id, remote execution = HTTP transport to a VPS/node.

### STREAMING subagent events to a UI
- Legacy (`agent.stream(..., subgraphs=True, version="v2")`): events carry a `ns` namespace path —
  `()` = main agent, `("tools:<callid>",)` = a subagent, nested `("tools:<id>","model_request:<id>")`.
  stream_mode "updates"/"messages"/"custom". Chunk shape: single mode = `(namespace, data)`, multiple =
  `(namespace, mode, data)`. Subagent tools can emit custom progress via
  `get_stream_writer()(...)`. `__interrupt__` key in updates = HITL pause; resume with
  `{"decisions":[...]}`. (src: .../deepagents/streaming)
- RECOMMENDED (Deep Agents v0.6+, `stream_events(input, version="v3")`): typed projections —
  `stream.subagents` (one handle per `task` call), `stream.messages`, `stream.tool_calls`,
  `stream.values`. Subagent handle fields: `.name` (= subagent_type), `.messages`, `.subagents`
  (nested), `.output` (final state/completion), `.path` (namespace), `.status` (started/completed/
  failed/interrupted), `.tool_calls` (each with `.tool_name`, `.input`, `.output_deltas`, `.completed`,
  `.error`, `.output`). Projections lazy (opened on access). Consume concurrently: async `astream_events`
  + `asyncio.gather`, OR sync `stream.interleave("messages","subagents")`, OR raw iterate `for event in
  stream` keyed on `event["params"]["namespace"]` for exact arrival order. `stream.subagents` (product-
  level task delegations, hides graph nodes) vs `stream.subgraphs` (raw graph structure) — use subagents
  for user-facing UI. (src: .../deepagents/event-streaming)

========================================================================
## INTERPRETERS / code interpreter / RLM  (src: .../deepagents/interpreters)
========================================================================
- In-memory JS workspace inside the agent loop; intermediate results stay OUT of model context. BETA.
  `langchain-quickjs>=0.2.0`, Python ≥3.11. Adds an `eval` tool; agent writes JS, runtime runs it in a
  QuickJS context, returns the last expression + captured console.log/warn/error.
- Runtime = QuickJS (quickjs-ng), embedded via `quickjs-rs` — SAME-PROCESS, not a VM/container.
  "Capability-scoped execution layer, NOT a host-memory isolation boundary." For untrusted code run the
  whole agent in isolated worker processes/containers; keep PTC allowlist narrow.
- Default capabilities: JS exec YES, top-level await YES, console capture YES. NO filesystem, network,
  shell, package manager, or clock by default. Two explicit bridges: PTC (tools) + dynamic subagents (task()).
- PTC (programmatic tool calling): `CodeInterpreterMiddleware(ptc=["web_search", ...])` or BaseTool
  instances. Exposes each allowlisted tool as async fn under `tools.*`, names camelCased
  (`web_search`→`tools.webSearch({...})`, input object follows tool schema). Off by default. SECURITY:
  PTC calls bypass the normal tool path → `interrupt_on` NOT enforced per PTC call. Treat allowlist as
  a permission boundary. Expose fs tools via PTC to give the interpreter file access; time/network only
  via explicit tools.
- Persistence `mode`: "thread" (default — snapshot after each turn, restore before next; survives
  across turns, no checkpointer required but checkpointer also captures snapshots for time-travel);
  "turn" (within one turn only); "call" (fresh REPL every eval). Snapshots store SERIALIZABLE data only
  — functions/classes become inaccessible after restore (error on access). Snapshots preserve interpreter
  memory, NOT outside-world side effects.
- `CodeInterpreterMiddleware` kwargs + defaults: `memory_limit`=64MB (QuickJS heap/thread),
  `timeout`=5.0s per eval, `tool_name`="eval", `capture_console`=True, `max_result_chars`=4000,
  `ptc`=None, `max_ptc_calls`=256 (None only in trusted env), `subagents`=True, `mode`="thread",
  `max_snapshot_bytes`=None (defaults to memory_limit; drops larger snapshots).
- RLM (Recursive Language Model): the approach in the dynamic-subagents page — orchestrate subagents
  over large inputs recursively from interpreter code. Sandbox requirement = QuickJS interpreter
  middleware (not a separate OS sandbox); for shell/installs/tests use sandbox BACKENDS instead.
- Choose: 1–2 external calls → normal tools; pure in-memory JS → interpreter; many tool calls from code
  → interpreter+PTC; many units/perspectives/recursion → interpreter+dynamic subagents; shell/OS →
  sandboxes.

========================================================================
## RUBRIC  (src: .../deepagents/rubric)
========================================================================
- `RubricMiddleware` = LLM-as-a-judge self-check/iterate middleware. Requires deepagents>=0.6.5, BETA.
  After the deep agent produces output, a dedicated grader SUBAGENT reviews the transcript vs a rubric;
  on `needs_revision` per-criterion feedback is injected and the agent reruns, until satisfied or cap.
- Config: `RubricMiddleware(model=, system_prompt=None, tools=None, max_iterations=3, on_evaluation=None)`.
  `model` (req; grader chat model — often smaller/cheaper, e.g. claude-haiku); `system_prompt` falls back
  to built-in grader prompt; `tools` = tools the grader can call to gather evidence (run tests, count
  tokens, read files) else reasons from transcript alone; `max_iterations` positive int (default 3);
  `on_evaluation` callback fired after each pass with a `RubricEvaluation` (works w/ invoke/stream/
  stream_events; exceptions in it are logged+suppressed — don't use for control flow).
- Pass `rubric` (newline-delimited string) in invocation STATE. No rubric on input → middleware does not
  run. Needs a checkpointer; on a checkpointed thread the same `rubric` persists across follow-up calls
  until replaced; KeyboardInterrupt/CancelledError propagate uncaught and resume on next same-rubric call.
- Verdicts: `satisfied` (done), `needs_revision` (loops), `max_iterations_reached` (stops),
  `failed` (rubric malformed/impossible), `grader_error` (grader raised — provider timeout etc, stops).
  On cap-reached the callback still gets `result:"needs_revision"`; terminal status is on private state
  `_rubric_status` (also `_rubric_evaluations`, `_rubric_iterations`).
- `RubricEvaluation` dict: `grading_run_id`, `iteration` (0-based), `result`, `explanation`,
  `criteria` (list of `{name, passed:true}` or `{name, passed:false, gap}`).
- stream_events custom events (version="v3", `CustomTransformer`): `rubric_evaluation_start`
  {type, grading_run_id, iteration}, `rubric_evaluation_end` {…, result, explanation, criteria}.
- QMX fit (INFERRED): rubric = the "iterate until done" gate for Lab copilot long experiments / vetted
  code; standing CLAUDE.md reviewer tiers map to grader-model selection.

========================================================================
## MCP integration  (src: .../deepagents/tools + langchain/mcp)
========================================================================
- `pip install "langchain[mcp]"`. `langchain.mcp.MCPAdapter` (requires langchain[mcp]>=1.4.0, BETA,
  LangChainBetaWarning once/process; built on FastMCP). Usage:
  `async with MCPAdapter(target) as adapter: tools = await adapter.list_tools()` then pass `tools=` to
  `create_deep_agent`. Tools hold the client so the agent stays usable after context exits.
- Target forms: http/https URL str (Streamable HTTP); `Path` to script (stdio subprocess); FastMCP
  instance (in-memory, no subprocess — ideal for tests); `StreamableTransport`; MCPConfig dict
  `{"mcpServers": {"name": {"url": "http://localhost:8000/mcp"}}}` (several servers, one adapter);
  prebuilt `fastmcp.Client`. A `str` MUST be an http(s) URL (MCPAdapter rejects non-URL strings — FastMCP
  would otherwise launch a matching .py/.js file as a subprocess).
- Public LangChain docs MCP server: `https://docs.langchain.com/mcp` (no key); tools
  `search_docs_by_lang_chain`, `query_docs_filesystem_docs_by_lang_chain`, `submit_feedback`.
- Deep Agents built-in harness tools: `ls`, `read_file` (paginated+multimodal), `write_file`,
  `edit_file`, `delete` (needs deepagents>=0.7; recursive), `glob`, `grep`, `execute` (sandbox backends
  only), `task` (spawn subagent). `write_todos` is opt-in via `TodoListMiddleware`. Tools can return
  text or standard content blocks (multimodal) when model supports it.

========================================================================
## ACP — Agent Client Protocol (editor integration)  (src: .../deepagents/acp)
========================================================================
- ACP = standard between coding agents and code editors/IDEs (agentclientprotocol.com). For AGENT↔EDITOR
  (editor supplies project context + receives rich updates). For AGENT↔external tool servers use MCP instead.
- `pip install deepagents-acp`. Expose a deep agent:
  `from deepagents_acp.server import AgentServerACP; server = AgentServerACP(agent); await run_agent(server)`
  (`from acp import run_agent`). Runs an ACP server in STDIO mode (reads stdin / writes stdout); normally
  launched as a command by the ACP client (editor). Pass a checkpointer (MemorySaver) to the agent.
- Clients: Zed, JetBrains IDEs, VS Code (via vscode-acp), Neovim (ACP plugins). Zed config: register a
  custom `agent_servers` command pointing at a launcher script (repo ships `run_demo_agent.sh`, needs
  ANTHROPIC_API_KEY in .env). Toad (`batrachian-toad`) can manage the ACP server process for local dev.
- QMX fit (INFERRED): ACP = how the "general Copilot" / Lab copilot could live inside a Codex/Claude-
  desktop-style app or editor pane (matches memory note qmx-agentic-langgraph-shift: copilot = Codex/
  Claude-desktop app with real terminal). Dynamic subagents work over ACP too (e.g. Zed).

========================================================================
## A2A — Agent2Agent (src: .../langsmith/server-a2a, the a2a.md copy)
========================================================================
- Google's agent↔agent protocol. LangSmith Agent Server exposes `/a2a/{assistant_id}`; speaks A2A v1.0
  JSON-RPC binding, also accepts v0.3 method names. Only JSON-RPC (no gRPC/HTTP+JSON). Method name family
  selects response enum casing (v1.0 SCREAMING_SNAKE vs v0.3 lowercase) — pick one family per client.
- Supported: SendMessage/message/send, SendStreamingMessage/message/stream (SSE), GetTask/tasks/get,
  CancelTask/tasks/cancel, ListTasks, GetExtendedAgentCard. NOT yet: SubscribeToTask,
  *TaskPushNotificationConfig (return -32601). Graph state MUST have a `messages` key.
- Continuity: `contextId` = conversation thread (used directly as LangGraph `thread_id`, MUST be a UUID —
  echo back the server's, don't mint your own); `taskId` = one request. First message omit both (server
  mints + returns). Follow-ups: resend contextId, omit taskId (each turn = new task in same context).
  contextId→thread_id auto-maps for LangSmith distributed tracing (group multi-agent convo in one thread).
- `historyScope` ("context" default | "task") controls returned history scope; caps `historyLength`≤10.
  Streaming ignores both. Agent card discovery: `GET /.well-known/agent-card.json?assistant_id=`.
  Optional capabilities via `metadata.a2a` (input/output modes, FilePart, A2UI v0.9, tool-result DataPart
  allowlist `A2A_ALLOWED_TOOL_CALL_RESULTS`). Disable: `langgraph.json` `{"http":{"disable_a2a":true}}`.
- Requirements (min versions): A2A endpoint `langgraph-api>=0.4.21`; inbound FilePart 0.12.0;
  tool-result DataParts 0.12.2; A2A_ALLOWED_TOOL_CALL_RESULTS 0.12.4; outbound FilePart + configurable card
  modes 0.13.0; A2UI v0.9 + historyScope 0.15.0 (not stable-released yet).
- QMX fit (INFERRED): A2A = how a QMX copilot (e.g. Portfolio) could talk to an external/third-party
  agent across the organogram, or how node-editor workflow agents expose themselves for cross-agent calls.

========================================================================
## RETRIEVAL / RAG  (src: .../deepagents/retrieval)
========================================================================
- Conceptual page (not a deepagents API). Knowledge base = docs/structured data for retrieval; reuse an
  existing one as a TOOL (Agentic RAG) or query + supply as context (2-Step RAG).
- Building blocks: document loaders → `Document` objects; text splitters → chunks; embedding models →
  vectors; vector stores; retrievers. Pipeline: sources→load→split→embed→vector store; query→embed→
  retrieve→LLM→answer. Modular (swap any component).
- Architectures: 2-Step RAG (retrieve-then-generate; high control, low flexibility, fast — FAQ/doc bots);
  Agentic RAG (LLM agent decides when/how to retrieve; low control, high flexibility, variable latency —
  only needs a tool that fetches knowledge, e.g. `@tool fetch_url`/`fetch_documentation` with an
  ALLOWED_DOMAINS guard); Hybrid RAG (query enhancement + retrieval validation + answer validation, loops).
- Deep Agents RAG tutorial (linked): retrieve chunks at query time, OFFLOAD to filesystem, DELEGATE
  analysis to subagents — this is the canonical Deep Agents RAG shape (combine with memory offloading).
- QMX fit (INFERRED): Agentic RAG over the GitBook/wiki/QMX-discussion corpus = the copilots' knowledge
  access; offload-to-filesystem + subagent analysis keeps copilot context lean.

========================================================================
## OPENWIKI  (src: .../openwiki/overview)
========================================================================
- Open-source CLI that writes/maintains a Markdown wiki about a codebase (or personal knowledge) so
  CODING AGENTS use it as durable context (read curated wiki first, inspect source only where needed).
  Built ON Deep Agents; supports LangSmith tracing. `npm install -g openwiki`; `openwiki --init` /
  `openwiki --update`.
- Modes: Code (default, `openwiki`/`openwiki code`) → `openwiki/` in the repo, wired into AGENTS.md +
  CLAUDE.md so agents find it; Personal (`openwiki personal`) → `~/.openwiki/wiki` from configured
  sources (git repos, Custom MCP, Gmail, Notion, web search, Hacker News, X/Twitter).
- Capabilities: repository wikis, coding-agent integrations (run INSIDE Codex/Claude Code/OpenCode/Cursor
  using host model+tools), Grounded Claims (facts tracked to versioned source evidence, refresh when
  evidence changes), automatic updates (GitHub Actions/GitLab CI/Bitbucket → open a PR on change), many
  model providers (OpenAI/Anthropic/Gemini/Bedrock/OpenRouter/GitHub Copilot), Open Knowledge Format
  (OKF v0.2 Markdown bundles with front matter + indexes + linked concepts).
- QMX fit (INFERRED): OpenWiki = a way to auto-maintain the QMX `docs/` knowledge base discovered via
  AGENTS.md — complements documentation-factory; agents consume wiki as durable context.

========================================================================
## QMX ORGANOGRAM MAPPING (INFERRED synthesis — verify before building)
========================================================================
- Copilots (general / Lab / Portfolio) = top-level Deep Agents with per-copilot splits: own `skills`
  sources, own `memory` namespace (StoreBackend scoped by copilot id = assistant_id), own `tools`,
  `permissions`, `interrupt_on`, `middleware`. Skills/memory/permissions ARE splittable per copilot and
  per subagent exactly as the docs require.
- Lab copilot (research/coding/workflow-building/long experiments): interpreter middleware + dynamic
  subagents (fan-out code review/analysis), RubricMiddleware for "iterate until done" long experiments,
  Agentic RAG over corpus, skill scripts in sandbox backend for deterministic pipelines.
- Portfolio copilot (risk/sizing): minimal focused tool set, read-only org-policy memory for risk
  authority, HITL interrupts on any sizing/trade-shaped tool.
- Long-running background/remote workflow agents (node editor): AsyncSubAgent per node (graph_id),
  HTTP transport to remote nodes/VPS, `async_tasks` state channel survives compaction, stream_events
  `stream.subagents` drives the node-editor live UI (status/messages/tool_calls per node).
- Editor/desktop copilot surface = ACP (`deepagents-acp` AgentServerACP, stdio). Cross-agent calls
  across the organogram or to third parties = A2A `/a2a/{assistant_id}`.
