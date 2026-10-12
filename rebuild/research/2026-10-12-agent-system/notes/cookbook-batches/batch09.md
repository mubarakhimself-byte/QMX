# batch09 notes — cookbook reader/extractor (NN=09)

Scope caveat: this batch is almost entirely **OpenAI** stack (Responses API, Agents SDK, GPT-5.x/o-series). QMX runs LangChain v1 + LangGraph + Deep Agents on Claude. The *prompt-engineering, guardrail, orchestration and cost/latency* patterns port cleanly; the *API-specific mechanisms* (verbosity param, apply_patch/shell tool types, CFG, `/responses/compact`, hosted MCP tool, `previous_response_id`) map to LangGraph/DeepAgents equivalents noted per file. All mappings below are my inference.

## PART A — INDEX

- openai-cookbook/examples/gpt-5/gpt-5-1_prompting_guide.ipynb — GPT-5.1 prompting: `none` reasoning, persona/verbosity steering, user-update preambles, plan tool, apply_patch & shell tool types, metaprompting loop.
- openai-cookbook/examples/gpt-5/gpt-5-2_prompting_guide.ipynb — GPT-5.2 prompting: verbosity clamps, scope discipline, long-context re-grounding, hallucination self-check, `/responses/compact` compaction, reasoning_effort migration table.
- openai-cookbook/examples/gpt-5/gpt-5_new_params_and_tools.ipynb — GPT-5 API features: `verbosity`, freeform/custom tool calls, context-free grammar (Lark/regex) constrained output, `minimal` reasoning.
- openai-cookbook/examples/gpt-5/gpt-5_prompting_guide.ipynb — GPT-5 agentic eagerness control, tool preambles, Responses API reasoning reuse (`previous_response_id`), coding/frontend prompts, Cursor tuning case study.
- openai-cookbook/examples/gpt-5/gpt-5_troubleshooting_guide.ipynb — GPT-5 failure-mode fixes: overthinking, laziness, deference, verbosity, latency, too-many-tools, malformed calls; all via params + metaprompting.
- openai-cookbook/examples/How_to_build_a_tool-using_agent_with_Langchain.ipynb — Classic LangChain ReAct agent: Tool, AgentExecutor, custom prompt/output parser, ConversationBufferWindowMemory, Pinecone RetrievalQA tool.
- openai-cookbook/examples/How_to_use_guardrails.ipynb — Input (topical/jailbreak) + output (moderation/G-Eval score) guardrails run async in parallel with main LLM call; threshold tuning.
- openai-cookbook/examples/mcp/building-a-supply-chain-copilot-with-agent-sdk-and-databricks-mcp/README.md — Setup README for Databricks MCP copilot (React UI + FastAPI streaming backend). (mostly setup, light agent-relevance)
- openai-cookbook/examples/mcp/databricks_mcp_cookbook.ipynb — Agents SDK copilot over Databricks Managed MCP (vector search + UC functions), output guardrail agent, FastAPI streaming, tracing.
- openai-cookbook/examples/mcp/mcp_tool_guide.ipynb — Responses API hosted MCP tool: `tools/list` caching, `allowed_tools` filtering, approvals, multi-server + code_interpreter/web_search composition.
- openai-cookbook/examples/o-series/o3o4-mini_prompting_guide.ipynb — o3/o4-mini function-calling: developer-prompt context, function-description contracts, hallucination guards, reasoning persistence, tool-count limits.
- openai-cookbook/examples/o1/Using_reasoning_for_routine_generation.ipynb — Use o1 to convert KB articles into executable step/IFTTT routines with function-call stubs for a service agent.
- openai-cookbook/examples/object_oriented_agentic_approach/Secure_code_interpreter_tool_for_LLM_agents.ipynb — Dynamic tool generation + sandboxed (Docker, no-net) code execution; two-agent file-access/code-exec separation; OO agent/tool registry.
- openai-cookbook/examples/Optimize_Prompts.ipynb — Multi-agent prompt optimizer (Agents SDK): parallel contradiction/format/few-shot checkers + conditional rewriters, tuned with Evals.
- openai-cookbook/examples/Orchestrating_agents.ipynb — Routines + handoffs from scratch: function→schema helper, tool loop, agents transfer by returning an Agent object; Swarm precursor.

## PART B — PATTERN NOTES

### openai-cookbook/examples/gpt-5/gpt-5-1_prompting_guide.ipynb
- Agent-loop steering via XML-tagged prompt blocks: `<solution_persistence>`, `<user_updates_spec>`, `<plan_tool_usage>`, `<tool_preambles>`-style sections. GPT-5.1 adds `none` reasoning (never emits reasoning tokens; replaces GPT-5 `minimal`).
- `none` mode supports hosted tools (web search, file search) and improved custom function-calling; treat like GPT-4.1 prompting (few-shot + strong tool descriptions).
- Persistence: GPT-5.1 under-runs on hard tasks; prompt it to not terminate prematurely, be "biased for action," treat "should we do x?"=yes as do-it.
- Tool-calling format: put *functionality* in tool `description`, *when/how* in prompt; worked `create_reservation` schema (name/datetime ISO8601, required).
- Parallel tool calls: enable + instruct ("Batch reads (read_file) and edits (apply_patch)"); reinforce with examples of permissible parallelism.
- Plan tool `update_plan`: params `merge` (bool) + `todos[]` {content, status, id}; rule: exactly one `in_progress`, 2–5 milestone items, update ≤8 tool calls apart, no micro-steps.
- New tool types (Responses API): `tools=[{"type":"apply_patch"}]` — named tool decreased apply_patch failure rate by **35%**; returns `apply_patch_call` with `operation.type` ∈ create_file/update_file/delete_file + diff; respond with `apply_patch_call_output` {status, output}.
- `tools=[{"type":"shell"}]` — returns `shell_call` {commands, timeout_ms (e.g.120000), max_output_length (e.g.4096)}; respond `shell_call_output` {stdout,stderr,outcome.exit_code}. Plan-execute loop.
- Design-system enforcement block: tokens-only colors (globals.css `--background` etc), Tailwind utilities wired to tokens.
- Metaprompting loop (2 calls): (1) diagnose failure modes from system prompt + logged failures (query/tools_called/final_answer/eval_signal) → structured `failure_modes:`; (2) surgical patch → `patch_notes` + `revised_system_prompt`. Group similar failures per call.
- Caveat: GPT-5.1 follows instructions tightly, so contradictions are costly; keep updates short; immediacy block emits commentary before analysis for perceived latency.
- Cited URLs: https://cookbook.openai.com/examples/gpt-5/codex_prompting_guide ; https://platform.openai.com/docs/models/gpt-5.2-codex ; https://github.com/openai/openai-cookbook/blob/main/examples/gpt-5/apply_patch.py ; https://openai.com/index/gpt-5-1-for-developers/
- QMX-fit: general copilot (Claude-Code-like) + Lab coding copilot. LangChain/DeepAgents mapping: `<plan_tool>`→DeepAgents write_todos/planning middleware; preambles→streamed assistant messages; persistence→system-prompt middleware; apply_patch/shell→DeepAgents filesystem + shell tools.

### openai-cookbook/examples/gpt-5/gpt-5-2_prompting_guide.ipynb
- GPT-5.2: lower default verbosity, stronger instruction adherence, more tool actions than 5.1 (needs reining), conservative grounding. Reuse 5.1's `<user_updates_spec>`/`<solution_persistence>` blocks.
- `<output_verbosity_spec>` clamp with concrete sentence/bullet budgets; `<design_and_scope_constraints>` forbids extra features/invented tokens — "simplest valid interpretation."
- Long-context `<long_context_handling>`: for >~10k tokens, build internal outline, restate constraints, anchor claims to named sections, quote fine details — reduces "lost in the scroll."
- `<uncertainty_and_ambiguity>` + `<high_risk_self_check>`: for legal/financial/compliance, re-scan for unstated assumptions, ungrounded numbers, overly strong language; soften. **Directly relevant to Portfolio copilot risk disclaimers.**
- Compaction (key mechanism): `POST /v1/responses/compact`, `client.responses.compact(model, input=[...])`. Loss-aware compression → opaque encrypted items for continuation (not inspection). Compact after milestones/tool-heavy phases, keep prompts identical when resuming, safe to repeat. GPT-5.2 + Responses API only.
- Structured extraction: always supply schema/JSON shape, required vs optional, null for missing (don't guess), re-scan for omissions; per-document stable IDs.
- reasoning_effort knob: none|minimal|low|medium|high|xhigh. Migration table: GPT-4o/4.1→5.2 `none`; GPT-5→5.2 same except minimal→none; GPT-5.1→5.2 same. Default effort: 5=medium, 5.1/5.2=none.
- Migration method: switch model first (no prompt change), pin reasoning_effort, run evals, then tune only on regression. Prompt Optimizer in Playground.
- `<web_search_rules>` research agent block: comprehensive, cite web-derived facts, resolve contradictions, follow second-order leads until marginal value drops, no clarifying questions (cover all intents). Full web-research-agent system prompt in appendix (persona, factuality non-negotiable, citations required, value-add behavior).
- Cited URLs: https://platform.openai.com/docs/guides/conversation-state?api-mode=responses ; https://platform.openai.com/docs/api-reference/responses/compact ; https://platform.openai.com/chat/edit?optimize=true
- QMX-fit: all four; compaction = workflow/server long-running agents; web_search_rules = Lab research. LangChain/DeepAgents mapping: compaction→LangGraph summarization/compaction middleware + checkpointer; high_risk_self_check→output-guardrail middleware; extraction schema→structured output / with_structured_output.

### openai-cookbook/examples/gpt-5/gpt-5_new_params_and_tools.ipynb
- `verbosity` param (text={"verbosity": low|medium|high}): scales output length ~linearly (reported low 560 → medium 849 → high 1288 output tokens on a poem) without prompt change; low=terse UX, high=audits/teaching. Supported gpt-5/mini/nano, Responses + Chat Completions.
- Freeform/custom function calling: `tools=[{"type":"custom","name":"code_exec","description":...}]` sends raw text payload (Python/SQL/shell/config) with no JSON wrapping; `text={"format":{"type":"text"}}`. **Does NOT support parallel tool calling.** Chain outputs back via `previous_response_id`.
- Context-Free Grammar constrained output: custom tool with `"format":{"type":"grammar","syntax":"lark"|"regex","definition":...}`; uses LLGuidance under the hood. Forces only grammar-valid strings (worked MS-SQL `TOP` vs PostgreSQL `LIMIT` grammars; a timestamp regex). `parallel_tool_calls=False`.
- CFG caveats: no lookaround/lazy modifiers/terminal-priorities/%import (except %import common); greedy longest-match lexer; keep terminals bounded (`/[^.\n]{0,10}*\./`), explicit char classes over `.`, explicit whitespace `SP=" "` not `%ignore`; drift = long/repetitive valid-but-wrong output → tighten grammar / few-shot / raise reasoning_effort.
- `minimal` reasoning: `reasoning={"effort":"minimal"}` — few/no reasoning tokens, fast TTFT, for extraction/formatting/classification; default is medium if unset. Avoid for multi-step/tool-heavy.
- Cited URLs: lark-parser.readthedocs.io ; github.com/guidance-ai/llguidance ; docs.rs/regex ; lark-parser.org/ide
- QMX-fit: Lab coding copilot (CFG→only-valid SQL/DSL against market DBs), workflow (minimal for cheap classify/extract). LangChain/DeepAgents mapping: verbosity/minimal→Claude has no direct param (use prompt + model choice); CFG→no direct Claude equivalent (closest: structured output / tool schema, UNVERIFIED); freeform custom tool→LangChain tool taking raw string.

### openai-cookbook/examples/gpt-5/gpt-5_prompting_guide.ipynb
- Agentic eagerness spectrum. Less eager: lower reasoning_effort + `<context_gathering>` with early-stop criteria (stop at ~70% hit convergence) and fixed tool budgets (e.g. "absolute maximum 2 tool calls"), plus escape hatch ("even if it might not be fully correct"). More eager: raise reasoning_effort + `<persistence>` block.
- Per-tool uncertainty thresholds: checkout/payment/delete-file = low threshold (require confirm), search/grep = high threshold. **Maps to QMX trade-execution vs read-only tools.**
- Tool preambles `<tool_preambles>`: rephrase goal, outline plan, narrate steps, summarize — big UX win on long rollouts.
- Responses API reasoning reuse: pass `previous_response_id` to persist reasoning items across tool calls → Tau-Bench Retail **73.9%→78.2%** just from switching to Responses API; available to ZDR orgs; conserves CoT tokens, cuts latency.
- Frontend defaults: Next.js/TS, Tailwind, shadcn/ui, Radix, Lucide, Zustand; `<self_reflection>` rubric (5–7 categories, hidden) for zero-to-one app quality; `<code_editing_rules>` to blend into codebase.
- Cursor case study: set `verbosity=low` globally but prompt high verbosity for coding tools → concise chat + readable diffs; added product-behavior detail (Undo/Reject) to reduce deferral; removed `maximize_`-prefix thoroughness language that caused over-searching; XML `<[x]_spec>` tags improve adherence.
- Instruction-following: contradictions hurt GPT-5 more (burns reasoning reconciling); worked CareFlow healthcare example of conflicting consent/lookup/emergency rules + fixes.
- `minimal` reasoning tips: brief bullet summary at start, descriptive preambles, disambiguated tools, explicit planning prompt. Markdown off by default in API; re-inject markdown instruction every 3–5 messages if adherence decays.
- Appendix: SWE-Bench apply_patch instructions, V4A diff format (`*** Begin Patch`/`@@ class`/context lines, no line numbers), agentic tool definitions (apply_patch/read_file/list_files/find_matches or run/send_input terminal-native), Tau-Bench retail routine, Terminal-Bench prompt (`rg` not grep/find, persistence/exploration/verification/efficiency blocks).
- Cited URLs: https://cursor.com/blog/gpt-5 ; https://cookbook.openai.com/examples/gpt4-1_prompting_guide ; github apply_patch.py
- QMX-fit: general + Lab + workflow; per-tool thresholds critical for Portfolio/trade tools. LangChain/DeepAgents mapping: previous_response_id reasoning reuse→LangGraph checkpointer/state persistence (Claude extended-thinking blocks across tool calls, UNVERIFIED analog); context_gathering budgets→recursion/step limits + middleware; preambles→streamed messages.

### openai-cookbook/examples/gpt-5/gpt-5_troubleshooting_guide.ipynb
- Catalog of failure modes + fixes, all via reasoning_effort/verbosity params + prompt blocks + metaprompting. Measure before tuning.
- Overthinking: lower effort to minimal/low, explicit stop condition + single self-check, route trivial asks (use mini/nano classifier), `<efficient_context_understanding_spec>` (parallel 4–8 queries, read top 3–5, early stop), fast-path block for trivial Q&A (no tools/todos/summaries).
- Laziness/underthinking: raise effort one notch; `<self_reflection>` 5–7 item rubric, iterate once.
- Over-deferential: `<persistence>` block, easier at effort ≥ low.
- Verbose: verbosity=low + coding-verbosity prompt.
- Latency: measure TTFT / time-to-first-action / total at P50/P95, separate model vs tool/network; `<parallelization_spec>`; show reasoning summaries + preambles; prompt/reasoning/tool-result caching; `service_tier="priority"` (premium per-token) for latency-critical; escalate high-TTFT request_id to support@openai.com.
- Too many tools: `<tool_use_policy>` ("select one tool or none… cap at 2 per request"); one job per tool with "don't use for…" notes; short playbooks; use Responses API to carry reasoning. Monitor tool_calls_per_turn, duplicate calls, no-tool answer share.
- Malformed tool calling (mode-collapse / repeating garbage): almost always a prompt contradiction; use metaprompt to analyze `<System Prompt>` + `<Tool Config>`.
- General metaprompt: ask model at end of a slow turn how to speed up next time while holding quality; sample several times, keep common suggestions, build an eval.
- QMX-fit: all; latency/observability metrics = server/workflow agents. LangChain/DeepAgents mapping: routing classifier→cheap-model router node; parallelization→parallel tool nodes; caching→Anthropic prompt caching; tool_use_policy→middleware/system prompt.

### openai-cookbook/examples/How_to_build_a_tool-using_agent_with_Langchain.ipynb
- Classic (legacy) LangChain ReAct agent — directly QMX-stack-relevant though pre-v1 API. Components: `Tool(name,func,description)`, `LLMSingleActionAgent`, `AgentExecutor.from_agent_and_tools`, custom `BaseChatPromptTemplate` + `AgentOutputParser`.
- ReAct prompt scaffold: Question/Thought/Action/Action Input/Observation/Final Answer loop; `stop=["\nObservation:"]` so model halts for tool output; regex parser `Action: (.*?)\nAction Input:[\s]*(.*)`.
- Memory: `ConversationBufferWindowMemory(k=2)` rolling window of last 2 turns, passed to AgentExecutor; interpolated via `{history}`.
- Tools: SerpAPI search (`SERPAPI_API_KEY`); Pinecone vectorstore (dim 1536, text-embedding-3-small) wrapped as `RetrievalQA.from_chain_type(chain_type="stuff")` → a "Knowledge Base" Tool. Tool description quality drives routing.
- Caveat: hand-rolled output parser raises on unparseable output; brittle vs native tool-calling. Modern LangChain v1 uses tool-calling agents, not this ReAct-string pattern.
- QMX-fit: Lab copilot (RAG over corpus), general. LangChain/DeepAgents mapping: direct — Tool→@tool, AgentExecutor→create_agent/StateGraph, BufferWindowMemory→checkpointer/trimming, RetrievalQA→retriever tool. (Modernize off this legacy shape.)

### openai-cookbook/examples/How_to_use_guardrails.ipynb
- Guardrails = detective controls. Input (topical / jailbreak / prompt-injection) run before/parallel to main LLM; output (hallucination/fact-check, moderation, syntax/schema check on function_call args).
- Async parallel pattern: `asyncio.create_task` both the guardrail and `get_chat_response`; `asyncio.wait(..., return_when=FIRST_COMPLETED)`; if guardrail returns `not_allowed`, cancel chat task and return canned message — minimizes added latency.
- Topical guardrail = cheap `gpt-4o-mini` prompt returning allowed/not_allowed. Moderation guardrail = G-Eval-style 1–5 score (domain + criteria + steps + content), block if ≥3.
- Threshold tuning: build eval set, confusion matrix; low threshold for jailbreak (high business risk), tolerate false negatives where harm is low. Design trade-off = accuracy vs latency vs cost.
- Caveats: LLM guardrail shares base-model vulnerabilities (injection can evade both); long conversations dilute instructions → easier jailbreak; over-restrictive → over-refusals. Mitigation: combine with rules/ML, judge only latest message, gradual rollout + monitoring.
- Cited URLs: github.com/NVIDIA/NeMo-Guardrails ; github.com/ShreyaR/guardrails ; arxiv.org/abs/2303.16634 (G-Eval)
- QMX-fit: Portfolio (block out-of-domain/risky advice), general (injection defense on untrusted web/news), workflow. LangChain/DeepAgents mapping: input/output guardrails→pre/post-model middleware (guardrail nodes) running a cheap model in parallel; tripwire→interrupt/early-exit.

### openai-cookbook/examples/mcp/building-a-supply-chain-copilot-with-agent-sdk-and-databricks-mcp/README.md
- Mostly setup; light agent-relevance. Architecture signal only: full-stack copilot = React chat UI + FastAPI backend streaming `/chat`, Agents SDK agent hard-scoped to a domain over Databricks Managed MCP.
- Stack: Python 3.10+, Node 18+, creds in `~/.databrickscfg`, OpenAI key. Streaming endpoint pattern; customization via ChatUI.jsx / api_server.py.
- QMX-fit: general/Portfolio copilot desktop UI shape (chat UI + streaming backend + domain-scoped agent). LangChain/DeepAgents mapping: FastAPI stream→LangGraph `astream` events to desktop UI; MCP→LangChain MCP adapters.

### openai-cookbook/examples/mcp/databricks_mcp_cookbook.ipynb
- OpenAI Agents SDK copilot over enterprise data via **Databricks Managed MCP** (Streamable HTTP transport). Agent decides at runtime whether to forecast / trace BOM / gauge revenue risk / fetch history / search emails — all within caller's data-access rights (Unity Catalog governance).
- Core SDK classes: `Agent(name, instructions, tools, model_settings, output_type)`, `Runner.run`, `function_tool`, `gen_trace_id`, `trace`; `ModelSettings`; exceptions `InputGuardrailTripwireTriggered`/`OutputGuardrailTripwireTriggered`.
- Two `@function_tool`s: `vector_search(query)` POST `/api/2.0/mcp/vector-search/{CATALOG}/{SCHEMA}`; `uc_function(function_name, params)` POST `/api/2.0/mcp/functions/{FUNCTIONS_PATH}`. Auth via `WorkspaceClient(profile=...)` + PAT (`ws.config.token`) through `DatabricksOAuthClientProvider`, httpx async POST.
- Output guardrail = second agent "Supply-chain check" with `output_type=SupplyChainCheckOutput(reasoning:str, is_supply_chain:bool)`; `@output_guardrail` raises tripwire when flag false → caller swaps refusal.
- FastAPI server: `build_mcp_servers()` constructs `MCPServerStreamableHttp(MCPServerStreamableHttpParams)` pre-connected for low latency; per-POST spins a fresh Agent with `mcp_servers` + `ModelSettings(tool_choice forced)`; streams tokens to React.
- MCP transports (3): stdio (local subprocess), HTTP-over-SSE (remote URL), Streamable HTTP (remote, spec transport). Databricks endpoints = Streamable HTTP behind HTTPS; requires serverless + Unity Catalog.
- Tracing: Traces view in platform dashboard shows each tool invoked (e.g. raw_from_product → revenue_risk).
- Caveat: every response forced to call a tool; guardrail is a full extra LLM call. Finance/quant relevance: revenue_risk, demand forecasting, BOM graph = analogous to Portfolio risk/optimization tools.
- Cited URLs: openai.github.io/openai-agents-python ; docs.databricks.com/.../agent-framework/mcp ; openai.github.io/openai-agents-python/mcp/ ; openai.github.io/openai-agents-python/guardrails/
- QMX-fit: Portfolio copilot (governed quant tools), workflow/server (remote MCP data). LangChain/DeepAgents mapping: MCPServerStreamableHttp→LangChain MCP client adapter; function_tool→@tool; output_guardrail agent→post-model guardrail subagent; trace→LangSmith.

### openai-cookbook/examples/mcp/mcp_tool_guide.ipynb
- Hosted MCP tool in Responses API: `{"type":"mcp","server_label","server_url","allowed_tools":[...],"require_approval":"never"}`. Runtime auto-detects transport (Streamable HTTP vs SSE).
- Lifecycle: declare server → runtime calls `tools/list` → writes `mcp_list_tools` item to context (cached while present, not re-fetched) → model invokes → `mcp_tool_call` item → by default pauses for approval (disable via `require_approval:"never"` once trusted) → executes, streams result, chains or finishes.
- Security: OpenAI discards header values + all but schema/domain/subdomain of server_url after each request; auth keys + URL must be resent every call; not returned in response objects; strict schema when possible.
- Cost/latency levers: `allowed_tools` trims ballooning payloads (dozens of verbose defs = hundreds of tokens); caching via keeping `mcp_list_tools` in context (pass `previous_response_id` or items manually); reasoning models produce far more tokens — reported non-reasoning 945 total tokens vs o4-mini reasoning 38,022 total (22,964 cached) for same tiktoken query.
- Composition: MCP is just a tools-array entry; mix with `code_interpreter`, `web_search_preview`, `image_generation`, custom tools, and multiple MCP servers. Worked pricing-analyst example (Alo Yoga MCP + Uniqlo web search + CSV code_interpreter → flag ≥15% price gaps).
- Prompting to limit calls: cap catalog search to N results then ask to continue; few-shot examples for choosing correct server + stopping; ask follow-up for missing details rather than broad search.
- QMX-fit: general + Lab + Portfolio (external data/broker/exchange MCP servers), workflow. LangChain/DeepAgents mapping: hosted MCP→LangChain MCP adapters (tool list caching manual); require_approval→LangGraph interrupt/HITL; allowed_tools→tool filtering before binding.

### openai-cookbook/examples/o-series/o3o4-mini_prompting_guide.ipynb
- Reasoning-model function calling. o3/o4-mini use tools natively within CoT. Developer messages (system auto-converted to developer internally) set role/context; function `description` is the durable interface contract (when to call + how to build args).
- Call ordering: spell out explicit sequences for well-defined tasks (e.g. refund: order_status_check→refund_policy_check→refund_create→user_notify); "check dirs exist before making files."
- Boundaries: list when to use vs not-use tools at both developer-prompt and tool-description level; put key rules/arg-escaping up front — a front-loaded ripgrep tool description scored **6% higher** on a tool-calling eval than a verbose one.
- Hallucination guards: "Do NOT promise to call a function later… emit it now"; `strict:true` for schema adherence; validate args before sending. o3 more hallucination-prone (promising background/future calls).
- Laziness fixes: start fresh conversation for unrelated topics; drop stale tool outputs and summarize into user message.
- **Avoid CoT prompting** — don't ask reasoning models to plan more before each call; it can hurt. Reasoning summaries need a minimum material-token threshold to appear.
- Responses API: persist reasoning items between tool calls → higher intelligence; ZDR path via `include=["reasoning.encrypted_content"]`, `store=False`, append `response.output` (incl. encrypted CoT) to context across calls.
- FAQ numbers: <~100 tools and <~20 args/tool = in-distribution (as of May 2025); prefer flat over deeply nested schemas; guidance assumes standard `tools` param (not free-text tool defs).
- Cited URLs: cookbook.openai.com/examples/reasoning_function_calls ; /responses_api/reasoning_items ; /mcp/mcp_tool_guide ; platform.openai.com/docs/guides/function-calling
- QMX-fit: cheap background/workflow agents (o3/o4-mini analog = DeepSeek/mini models), Lab coding. LangChain/DeepAgents mapping: reasoning persistence→Claude thinking blocks preserved across tool calls (checkpointer); function-description-as-contract→careful @tool docstrings; strict→tool arg schema validation.

### openai-cookbook/examples/o1/Using_reasoning_for_routine_generation.ipynb
- Pattern: use a reasoning model (o1-preview) zero-shot to convert human-oriented KB articles into LLM-executable **routines** (numbered main actions, lettered sub-actions, if/then/else IFTTT logic, function-call stubs with purpose+params, always end `case_resolution`).
- `CONVERSION_PROMPT` encodes the routine format rules; run articles in parallel via `ThreadPoolExecutor`. Output includes sample agent responses, discrete steps, defined functions (e.g. review_and_apply_tax_exemption, get_billing_plan, update_payment_method).
- Downstream: classifier picks the routine, LLM executes it conversationally + performs actions on the user's behalf. Build evals before production.
- Caveat: routines handle complex human diagrams/decision-trees better as explicit IFTTT; reduces hallucination/path deviation. "If uncertain, respond 'I don't know.'"
- QMX-fit: Lab (turn QMX GitBook/wiki corpus into agent-runnable SOPs), general. LangChain/DeepAgents mapping: offline generation step feeding prompt/subagent instructions; routine→StateGraph or structured system prompt; classifier→router node.

### openai-cookbook/examples/object_oriented_agentic_approach/Secure_code_interpreter_tool_for_LLM_agents.ipynb
- Dynamic tool generation: LLM (o3-mini) writes Python at runtime and executes it in a code interpreter — no predefined per-question functions. For data analysis/viz/ML/automation.
- Security sandbox (central lesson): Docker container, `--network none --cap-drop all --pids-limit 64 --tmpfs /tmp:rw,size=64M`, non-root user, pre-installed requirements (no runtime pip, no host FS/network). "Isolate; never run LLM code on host."
- Two-agent separation of concerns: FileAccessAgent (gpt-4o, pre-defined tools, host FS read→copy into container, no interpreter) vs PythonExecAgent (o3-mini, `reasoning_effort='high'`, dynamic tools + interpreter, container FS only, no host/net). Table enumerates each agent's access rights.
- OO scaffolding: BaseAgent (abstract `task()`, logger, LLM interface, `add_context()`), ChatMessages (history, since ChatCompletions stateless), ToolManager, ToolInterface (abstract `get_definition()`+`run()`); agents/tools in a `registry/` for reuse.
- Orchestration: sequential — FileAccessAgent reads file → context added to PythonExecAgent → REPL loop runs user questions. o3-mini tried multiple methods (correlation, linear regression, random forest) at high effort.
- QMX-fit: **Lab copilot** (code interpreter for research/backtests on market CSVs), workflow. LangChain/DeepAgents mapping: sandboxed exec→DeepAgents sandbox/code tool; agent separation→subagents with scoped tools; ToolInterface/registry→@tool + tool registry; high-privilege file agent vs low-privilege exec agent = HITL/permission boundary.

### openai-cookbook/examples/Optimize_Prompts.ipynb
- Multi-agent prompt optimizer on Agents SDK: 5 specialized agents — Dev-Contradiction-Checker, Format-Checker, Few-Shot-Consistency-Checker (detectors) + Dev-Rewriter, Few-Shot-Rewriter (fixers). All `Agent(name, model="gpt-4.1", output_type=<Pydantic>, instructions=...)`.
- Pydantic structured I/O: `Issues(has_issues:bool, issues:List[str])`, `FewShotIssues(+rewrite_suggestions)`, `MessagesOutput`, `DevRewriteOutput(new_developer_message)`. Strict-JSON output contracts.
- Orchestration `optimize_prompt_parallel`: `with trace(...)`, run 3 checkers via `asyncio.gather([Runner.run(...)])` in parallel; conditionally run dev_rewriter (if contradiction/format issues) then fewshot_rewriter (depends on rewritten prompt). Clear dependency graph.
- Agent-instruction best practices: narrow scope, explicit definitions (contradiction = two clauses that can't both hold; overlaps ≠ contradictions), step-by-step method, out-of-scope boundaries to prevent over-flagging, strict output format, be conservative flagging format issues.
- Evals: 20 hand-labeled golden pairs (input_payload + golden_output with changes/new_developer_message/issue categories); string-check grader verifying detection + match; tuned instructions + model → chose gpt-4.1 (accuracy/cost/speed), 20/20 correct.
- QMX-fit: Lab (prompt/agent authoring), workflow (self-improving agents). LangChain/DeepAgents mapping: parallel checkers→parallel subagent/tool nodes with `gather`; output_type→with_structured_output; trace→LangSmith; conditional rewriters→conditional edges in StateGraph.

### openai-cookbook/examples/Orchestrating_agents.ipynb
- From-scratch routines + handoffs (Swarm precursor), model-agnostic plain Chat Completions — highly portable concept.
- Routine = system prompt (natural-language numbered steps with conditionals) + tools; LLM gives "soft" state-machine adherence without dead-ends.
- `function_to_schema(func)`: introspects signature/annotations/docstring → OpenAI function schema (type_map, required = params with no default). Lets you define tools as plain Python functions.
- Agent loop `run_full_turn(agent, messages)`: build tool_schemas + tools_map from agent.tools, call model, append message, execute each tool_call (`execute_tool_call` → json.loads args → tools_map[name](**args)), add tool result, loop until no tool_calls.
- `Agent(BaseModel)` = {name, model, instructions, tools}. Handoff mechanism (clean trick): a `transfer_to_X()` tool **returns an Agent object**; loop checks `if type(result) is Agent: current_agent = result` and replies "Transfered… adopt persona immediately." `Response(agent, messages)` carries the active agent back.
- Worked triage→sales/issues agents with `escalate_to_human(summary)`, order confirmation HITL (`input("Confirm order? y/n")`). Models reliably self-trigger handoffs.
- Caveat: routines struggle when overloaded with too many tasks/tools → split into multiple agents and hand off. Swarm is example-only, not production.
- Cited URL: github.com/openai/swarm
- QMX-fit: all — triage/handoff = general copilot routing to Lab/Portfolio sub-copilots; order-confirm HITL = trade approval. LangChain/DeepAgents mapping: handoff-by-returning-agent→LangGraph Command(goto=...) / subagent delegation; triage agent→supervisor/router node; function_to_schema→@tool auto-schema; confirm input→interrupt HITL.
