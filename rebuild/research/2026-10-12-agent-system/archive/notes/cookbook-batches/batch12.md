> SUPERSEDED 2026-10-12 by `tracker/qma-v2/PRD.md` (see `tracker/qma-v2/FILE-INDEX.md`). Kept for history.

# Batch 12 notes — OpenAI cookbook (Responses API, caching, skills, multi-agent, memory, evals, finance)

## PART A — INDEX

- openai-cookbook/examples/Prompt_Caching101.ipynb — OpenAI automatic prompt caching basics; caching tools + multi-turn histories + images; `cached_tokens` usage field.
- openai-cookbook/examples/Prompt_Caching_201.ipynb — Deep prompt-caching playbook: stabilize prefix, `prompt_cache_key` routing, `allowed_tools`, Flex, extended 24h retention, Realtime `retention_ratio`.
- openai-cookbook/examples/reasoning_function_calls.ipynb — Function calling with reasoning models (o3/o4-mini) via Responses API; serial multi-tool loop; preserving reasoning items in manual orchestration.
- openai-cookbook/examples/responses_api/reasoning_items.ipynb — Why Responses API beats Chat Completions for reasoning: reasoning-item persistence, 40→80% cache, ~3% SWE-bench gain, encrypted reasoning for ZDR.
- openai-cookbook/examples/responses_api/responses_api_tool_orchestration.ipynb — Multi-tool RAG routing: hosted `web_search_preview` + custom Pinecone function tool, parallel tool calls, sequential tool chaining.
- openai-cookbook/examples/responses_api/responses_example.ipynb — Responses API primer: stateful conversations (`previous_response_id`), forking, hosted tools, one-call multimodal + web search.
- openai-cookbook/examples/skills_in_api.ipynb — Skills in OpenAI API: `SKILL.md` bundle, `POST /v1/skills`, mounting into hosted/local shell tool, versioning, routing best practices.
- openai-cookbook/examples/stripe_model_eval/selecting_a_model_based_on_stripe_conversion.ipynb — Model selection by business outcome: A/B test on Stripe conversion, two-proportion Z-test, non-inferiority design.
- openai-cookbook/examples/Structured_outputs_multi_agent.ipynb — Multi-agent system via Structured Outputs (`strict:true`); triage agent routes to specialized tool-grouped agents.
- openai-cookbook/examples/third_party/financial_document_analysis_with_llamaindex.ipynb — LlamaIndex RAG over 10-K PDFs; `SubQuestionQueryEngine` decomposes compare/contrast queries across per-doc query engines.
- openai-cookbook/examples/Using_tool_required_for_customer_service.ipynb — `tool_choice='required'` to force tool use for deterministic customer-service flow; GPT-vs-GPT simulated eval.
- openai-cookbook/examples/vector_databases/oracle_db/deep_research_openai_agents.ipynb — OpenAI Agents SDK `Session` protocol on Oracle AI Agent Memory; split of short-term session vs durable long-term findings via tools.

## PART B — PATTERN NOTES

### openai-cookbook/examples/Prompt_Caching101.ipynb
- Pattern: automatic prompt caching (cost/latency control) for agents with large tool/schema lists, coding assistants, chatbots.
- Mechanism: caching auto-activates for prompts ≥1024 tokens; no request-change needed. System matches a cached prompt PREFIX; hit reuses, miss processes full prompt and caches prefix.
- Place static content (instructions, examples, tools) at the START; variable/user content at the END. Images and tools must be IDENTICAL including ordering.
- Metric: `usage.prompt_tokens_details.cached_tokens` reports cached prompt tokens; zero for <1024-token requests.
- Numbers: up to 80% latency reduction for prompts >10,000 tokens; caching is org-scoped; eligible for zero data retention.
- Tools caching: tool definitions and their order must remain identical to be in the prefix. Multi-turn: append new elements to END of messages array; second run `run2` showed cached_tokens>0.
- Images: linked or base64 images qualify; `detail` parameter must stay consistent (affects tokenization). GPT-4o-mini adds extra tokens for image processing.
- Caveat/failure: changing the FIRST image URL (eggs_url vs veggie_url) broke the cache even with same user query. Unused prompts auto-evicted.
- Caveat: caching discounts based on actual tokens processed incl. image tokens, which count toward rate limits.
- QMX-fit: general + workflow/server agents (stable system prompts + large tool arrays benefit most). [inference]
- LangChain/DeepAgents mapping: no direct LangChain equivalent (provider-side); relevant to how middleware/prompt builders ORDER system vs volatile content; provider-agnostic, applies when QMX uses OpenAI-class cheap models. [inference]

### openai-cookbook/examples/Prompt_Caching_201.ipynb
- Pattern: tactical cache-hit-rate optimization for long-running agents; cost control + observability.
- Mechanism basics: exact repeated-prefix match, cache hits in 128-token increments, min 1024 tokens. Cacheable prefix includes messages, images, audio, tool definitions, structured-output schemas. In-memory default; extended caching = 24h.
- `prompt_cache_key` (optional param): combined with the ~first-256-token hash to increase routing stickiness so same-prefix requests land on same engine. Think of it as a DB shard key.
- Numbers: TTFT reduced up to ~80%; input cost up to ~90%. Cache discount by model: gpt-4o 50%, gpt-4.1 75%, gpt-5-nano 90%, gpt-5.2 90%, gpt-realtime audio 98.75%. Latency test: 7% faster at 1024 tokens, 67% faster at 150k+. One customer 60%→87% hit rate using `prompt_cache_key`.
- Capacity: ~15 requests/minute per (prefix + prompt_cache_key) combination; excess load-balances to new machines (each a one-time miss). Choose key granularity to stay below ~15 RPM. Per-user keys = reuse across related convos; per-conversation keys scale for parallel unrelated threads.
- `allowed_tools` (tool_choice option `{"mode":"auto","tools":[...]}`): restrict callable tools per turn WITHOUT changing the tools array, preserving cache. Keep full toolkit in `tools`.
- Compaction config: `context_management=[{"type":"compaction","compact_threshold":100000}]` on `responses.create` (model `gpt-5.2-codex`, `store=False`). Caveat: compaction/summarization/truncation BREAKS the cache — context engineering vs caching are "inherently at odds."
- Codex learnings: keep system instructions, tool defs, sandbox config, env context identical and consistently ordered; APPEND new messages rather than modifying earlier ones when runtime config changes mid-conversation. Cited: https://openai.com/index/unrolling-the-codex-agent-loop/
- Tip: move timestamps/dynamic lookup data to `metadata` so they don't bust the cache.
- Flex Processing: `service_tier="flex"` on Responses API — 50% discount like Batch but allows RPM control, extended caching, `prompt_cache_key`. Test: 8.5% higher hit rate vs Batch → 23% input-token cost reduction. Pre-GPT-5 models (o3/o4-mini) lack Batch caching parity.
- Responses API gives 40–80% better cache utilization vs Chat Completions (persists raw CoT via `previous_response_id` / encrypted reasoning items).
- Extended caching: `prompt_cache_retention: "24h"`; offloads KV tensors to GPU-local storage; for gpt-5.5/5.5-pro+ default is 24h, `in_memory` unsupported. Only KV tensors persisted, never raw input text/multimodal.
- Realtime API (32k context): default `truncation:"auto"` causes frequent misses; `retention_ratio` (e.g. 0.7) keeps ~70% window, drops oldest 30% in one larger event → stable prefix, trades memory depth for cache stability.
- Troubleshooting lower caching: schema changes, naive truncation, instruction/system-prompt changes, reasoning-effort changes, cache expiration, added space/timestamp, Chat Completions with reasoning models.
- Cited: https://developers.openai.com/api/docs/guides/prompt-caching ; https://developers.openai.com/blog/responses-api/
- QMX-fit: workflow/server agents (long-running), Lab (long experiments), cost control for cheap background models. [inference]
- LangChain/DeepAgents mapping: LangGraph checkpointer/state design should keep stable prefix; compaction middleware at odds with caching — tune `compact_threshold` via evals; no direct key equivalent but QMX can pass provider cache keys. [inference]

### openai-cookbook/examples/reasoning_function_calls.ipynb
- Pattern: agent loop with reasoning models + custom function tools; serial (not parallel) tool execution; manual stateless conversation orchestration.
- Mechanism: `client.responses.create(input=..., reasoning={"effort":"low","summary":"auto"}, model="o4-mini", tools=tools)`. `effort` options low/medium/high; `summary` auto/detailed/none. o4-mini = 200,000-token context.
- Multi-turn state: `previous_response_id` lets OpenAI auto-manage history incl. reasoning items. Reasoning tokens are hidden, consume context faster; visible as summary via `response.output` reasoning item `.summary[0].text`.
- Tool schema (Responses flavor): top-level `{"type":"function","name":...,"description":...,"parameters":{...}}` (NOT nested under "function"). `tool_mapping` dict maps names→callables.
- Function result message shape: `{"type":"function_call_output","call_id":<call_id>,"output":<tool_output>}`.
- Loop pattern: at each step, extract `response.output` items of type `function_call`; execute; feed outputs back with `previous_response_id`; break when output has a `message` type and no function calls. `invoke_functions_from_response` helper iterates output, handles errors per call.
- Reasoning models may emit a SEQUENCE of serial tool calls (dependent steps), unlike `parallel_tool_calls`; number of steps unknown → must loop.
- Custom web_search: wrap a `gpt-4o-mini` call with `tools=[{"type":"web_search_preview"}]` since web search was not available out-of-box for reasoning models (as of May 2025, UNVERIFIED whether still true).
- Manual (stateless) orchestration: treat API stateless, maintain `conversation` array; MUST preserve reasoning items and function_call items in history or the API errors. Interleave function_calls with function_outputs to preserve order/CoT.
- Numbers: tracked total_tokens vs 200,000 context window (`total_tokens/200_000`).
- QMX-fit: general copilot + Lab copilot (multi-step reasoning + tools); workflow agents. [inference]
- LangChain/DeepAgents mapping: StateGraph agent loop / ReAct; preserving reasoning items ≈ keeping message history in checkpointer; tool_mapping ≈ LangChain tool registry. [inference]

### openai-cookbook/examples/responses_api/reasoning_items.ipynb
- Pattern: maximize reasoning-model intelligence/cost/latency by passing back reasoning items; encrypted reasoning for ZDR; reasoning summaries for UX.
- Mechanism: Responses API is stateful; each response includes a `reasoning` item exposed as an ID (e.g. `rs_6820f383...`). Pass IDs back in subsequent messages, or use `previous_response_id` to auto-include prior reasoning items.
- Key rule: in plain multi-turn you don't need reasoning items, but when a turn includes a FUNCTION CALL you MUST include reasoning items (via `previous_response_id` or by adding the reasoning item to `input`); add all `response.output` back into context.
- Function flow: `context += response.output` (incl. reasoning item), then append `{"type":"function_call_output","call_id":tool_call.call_id,"output":str(result)}`, call again — counts as single turn.
- Numbers: 148 output tokens for 10 input, 128 of which reasoning tokens (hidden). Including reasoning items → ~3% improvement on SWE-bench. Chat→Responses boosted cache utilization 40%→80%. Cached input for o4-mini 75% cheaper than uncached.
- Encrypted reasoning items (for ZDR orgs, stateless): add `include=["reasoning.encrypted_content"]` and `store=false`; API returns `encrypted_content` field in reasoning item, pass back in future requests. Decrypted in-memory, never written to disk, discarded after use. ZDR auto-enforces `store=false`.
- Reasoning summaries: `reasoning={"summary":"auto"}`; access `response.output[0].summary[0].text`. Gives users visibility into which functions called + why before final message.
- Caveat: in turn 2 reasoning items from turn 1 are ignored/removed by model (not reused across turns), so a later call can't achieve full cache hit; passing them is harmless (API discards irrelevant ones). Caching only impacts prompts >1024 tokens.
- Cited: https://platform.openai.com/docs/guides/reasoning?api-mode=responses ; https://openai.com/enterprise-privacy/
- QMX-fit: all copilots using Opus/reasoning via proxy; server agents with ZDR-like stateless needs. [inference]
- LangChain/DeepAgents mapping: encrypted reasoning ≈ stateless checkpointing of opaque model state; summaries ≈ streaming intermediate steps to UI; no direct equivalent (provider feature). [inference]

### openai-cookbook/examples/responses_api/responses_api_tool_orchestration.ipynb
- Pattern: multi-tool orchestration + RAG routing; hosted web_search + external vector DB (Pinecone) as function tool; parallel and sequential tool calls.
- Mechanism: `tools=[{"type":"web_search_preview","user_location":{...},"search_context_size":"medium"}, {"type":"function","name":"PineconeSearchDocuments",...}]`; call `client.responses.create(model="gpt-4o", input=[system,user], tools=tools, parallel_tool_calls=True)`.
- Routing: system prompt instructs model to pick the right tool per question; model routes general knowledge → web search, domain query → Pinecone semantic search, else answers directly.
- Tool-output loop: inspect `response.output[i].type` ("web_search_preview"/"function_call"); run function; append the tool call and `{"type":"function_call_output","call_id":tool_call.call_id,"output":str(result)}`; call again for final answer.
- Forced sequence: system prompt "first call the web search tool...then call PineconeSearchDocuments" demonstrates a tool-calling SEQUENCE in one response.output.
- Embeddings/vector store: `text-embedding-3-small`, Pinecone serverless (AWS us-east-1), `metric='dotproduct'`, `top_k` retrieval with `include_metadata=True`.
- Caveat: `response.output` ordering matters — must map `call_id` back to the correct function call; web_search item uses `id`, function_call uses `call_id`.
- QMX-fit: Lab copilot (research/RAG), general copilot (tool routing), workflow agents. [inference]
- LangChain/DeepAgents mapping: StateGraph/ReAct agent + retriever tools; hosted web_search ≈ a LangChain web tool; Pinecone function tool ≈ retriever tool node. [inference]

### openai-cookbook/examples/responses_api/responses_example.ipynb
- Pattern: Responses API fundamentals — stateful multi-turn, forking, hosted tools, one-call multimodal + tool augmentation.
- Mechanism: `client.responses.create(model=..., input="...")`; output at `response.output[0].content[0].text`. Stateful: `client.responses.retrieve(response_id=...)` returns full history.
- Multi-turn: `previous_response_id=response.id` continues conversation; can FORK by referencing an earlier response id and sending a different follow-up.
- Hosted tools: pass `tools=[{"type":"web_search"}]` or `file_search`; API decides and invokes automatically (vs manual tool loop in Chat Completions).
- Multimodal: single `input` with mixed `input_text` + `input_image` (image_url) content plus `tools=[{"type":"web_search"}]` → analyze image, search web, summarize in ONE API call (Chat Completions would need multiple round trips).
- Contrast: designed for async + stateful long-running reasoning; simpler than Assistants API, more flexible than Chat Completions.
- QMX-fit: general copilot (conversation hosting), Lab (mini-app building). [inference]
- LangChain/DeepAgents mapping: `previous_response_id` statefulness ≈ checkpointer/thread; forking ≈ branching a checkpoint thread; hosted tools ≈ prebuilt tools. [inference]

### openai-cookbook/examples/skills_in_api.ipynb
- Pattern: Skills — reusable versioned procedure bundles (instructions + scripts + assets) mounted into a shell tool; keep system prompts lean; invoked only when needed.
- Mechanism: a skill is a folder anchored by required `SKILL.md` (frontmatter `name`, `description`). Service unzips into runtime, reads frontmatter, adds name/description/path to user prompt context; model reads SKILL.md via path and runs scripts via shell tool. Skill instructions have same priority as user instructions.
- Create: `POST /v1/skills` (multipart files[] OR zip upload). Response returns `id`, `default_version`, `latest_version`.
- Mount (Responses API): attach via `tools[].environment.skills`. Hosted shell `environment.type="container_auto"`: `{"type":"skill_reference","skill_id":...,"version":"..."}` or `inline` base64 zip. Local shell `environment.type="local"`: provide `name`,`description`,`path`; app executes `shell_call` commands and returns `shell_call_output` with matching `call_id`. Local shell does NOT accept hosted skill_reference.
- Example used `model="gpt-6-astra"` with `tools=[{"type":"shell","environment":{...}}]`; hosted shell network access DISABLED by default; save artifacts to `/mnt/data`.
- When to use: reusable/versioned behaviors, conditional/branching workflows, needs code execution + local artifacts, shared "house style", reproducibility. NOT for one-off tasks, live-data/side-effects (use tools), daily-changing procedures.
- Skills vs tools vs system prompts: system prompt=always-on global behavior; tools=atomic capabilities + side effects (narrow, strongly typed); skills=packaged procedures run sometimes.
- Versioning: `POST /v1/skills/{skill_id}/versions`; pin `version:"2"`, float `version:"latest"`, omit → default_version. Pin model + skill version together for reproducibility.
- Best practices: clear name/description + "Use when"/"Don't use when" + negative examples for routing; prefer zip uploads; design skills like tiny CLIs (deterministic stdout, fail loudly, known output paths); don't duplicate procedure in system prompt; network access high-risk → strict allowlists, treat tool output as untrusted.
- Limits: SKILL.md case-insensitive match, exactly one manifest, max zip 50 MB, max 500 files per version, max uncompressed file 25 MB.
- Cited: https://developers.openai.com/api/docs/guides/tools-skills ; https://developers.openai.com/api/docs/guides/tools-shell
- QMX-fit: Lab copilot (workflow building, mini-apps), workflow/server agents (reusable quant procedures, report generators). [inference]
- LangChain/DeepAgents mapping: strongly parallels DeepAgents/Claude "skills" (SKILL.md) + sandbox; LangGraph tool node executing a sandboxed CLI; no built-in LangChain skill registry but directly portable concept. [inference]

### openai-cookbook/examples/stripe_model_eval/selecting_a_model_based_on_stripe_conversion.ipynb
- Pattern: eval/model-selection by real business outcome (payment conversion) rather than offline benchmarks; classic A/B testing.
- Mechanism: randomize users by `user_id` at signup into control (current model) vs variant(s); hold onboarding/features/prompts constant; apply consistent rate-limit paywall as the standardized upgrade moment; track Stripe `checkout.session.completed` webhook → mark user converted.
- Stats: two-proportion Z-test (`statsmodels.stats.proportion.proportions_ztest`, `alternative="larger"`). One-tailed = better/non-worse; two-tailed = any difference; A/B/n = ≥3 models.
- HyperWrite params (non-inferiority, cost-savings): one-tailed two-proportion Z-test, alpha=0.15 (85% confidence), power=0.60, MDE=30% drop, randomized by user_id.
- Numbers: GPT-4.1 matched Claude 3.5 Sonnet control conversion at lower cost (control 0.92%, gpt-4.1 1.29%, gpt-4.1-mini 0.99%; Req N=3378/arm). Example run: 1500/group ~75% power; variant 2.0% vs control 1.0%, p=0.012.
- A/B/n note: each candidate vs production control, not vs each other; variant-specific launch decision → skipped family-wise correction (standard for small-k control-centric tests).
- Caveats: avoid p-hacking (fix one/two-tailed before start); <~10 conversions → Fisher's exact / Wilson CIs; early peeking inflates false positives (use fixed sample or group-sequential); prevent user cross-arm contamination; multiple challengers → Bonferroni/Holm or multi-armed bandit; ensure caching/prompt drift doesn't leak one model's response into another's cache.
- Cited: https://www.evanmiller.org/how-not-to-run-an-ab-test.html
- QMX-fit: cost control / model-tier selection (Opus vs cheap DeepSeek/mini for background work); Portfolio/workflow could reuse the A/B harness concept but QMX has no "payment conversion" — fit is weak on the metric. [inference]
- LangChain/DeepAgents mapping: no direct equivalent; relates to QMX observability/eval harness choosing background model tier; offline-eval graders are the closer analog. [inference]

### openai-cookbook/examples/Structured_outputs_multi_agent.ipynb
- Pattern: multi-agent system built on Structured Outputs (`strict:true`); a triage agent routes queries to specialized tool-grouped agents (data processing / analysis / visualization).
- Mechanism: each agent = own system prompt + own tool subset passed to `client.chat.completions.create(model="gpt-4o-2024-08-06", tools=..., temperature=0)`. Triage tool `send_query_to_agents` returns `{agents:[...], query}`; also `speak_to_user`.
- Structured Outputs: set `"strict": True` on each tool/function to guarantee the response abides by the JSON schema (builds on JSON mode + function calling).
- Rationale: as number of functions/tools grows, performance suffers; grouping tools under specialized agents increases overall system performance.
- Execution: `execute_tool(tool_calls, messages)` maps tool name → Python function (pandas clean_data/stat_analysis/plot_line_chart), appends `{"role":"tool","name":...,"content":json}` to shared conversation history.
- Caveat: Structured Outputs enforces SCHEMA only; application code must still validate argument semantics and business rules.
- QMX-fit: Lab copilot (data analysis), Portfolio (grouping risk/sizing tools), general copilot as triage/orchestrator. [inference]
- LangChain/DeepAgents mapping: DeepAgents subagents / LangGraph supervisor-router (triage) with specialized worker subgraphs; strict schema ≈ structured output / Pydantic tool args. [inference]

### openai-cookbook/examples/third_party/financial_document_analysis_with_llamaindex.ipynb
- Pattern: finance/quant RAG over long 10-K SEC filings; compare-and-contrast across multiple documents via sub-question decomposition.
- Mechanism: LlamaIndex `SimpleDirectoryReader` loads PDFs → `VectorStoreIndex.from_documents` (in-memory, OpenAI embeddings); per-doc `as_query_engine(similarity_top_k=3)`. `ServiceContext.from_defaults(llm=...)` set global.
- Multi-doc: wrap each engine as `QueryEngineTool` with `ToolMetadata(name,description)`; `SubQuestionQueryEngine.from_defaults(query_engine_tools=...)` breaks a complex compare/contrast query into sub-questions routed to per-doc engines.
- Models: `gpt-3.5-turbo-instruct` (temperature=0) as LLM in this (older) notebook.
- Queries demonstrated: revenue extraction with page reference; compare fastest-growing segments/geographies; compare revenue growth 2020→2021 across Uber/Lyft.
- Caveat: docs are 100+ pages; loading/indexing slow; relies on top_k retrieval quality.
- QMX-fit: Lab copilot (research/analysis over filings/reports); Portfolio (fundamental doc analysis). [inference]
- LangChain/DeepAgents mapping: retriever tools + a decomposition/planner node; SubQuestionQueryEngine ≈ LangGraph sub-query fan-out subagents; VectorStoreIndex ≈ LangChain vector store retriever. [inference]

### openai-cookbook/examples/Using_tool_required_for_customer_service.ipynb
- Pattern: forced tool use for deterministic bounded flows; HITL-style confirmation before permanent ops; GPT-vs-GPT simulated eval.
- Mechanism: `tool_choice='required'` on `chat.completions.create` guarantees a tool is called every turn → defined exit points / control. Tools: `speak_to_user(message)` (the response/exit), `get_instructions(problem enum: fraud/refund/information)`.
- Loop: `submit_user_message` loops executing tool calls until one requires a user response (`respond=True` when speak_to_user fires); `execute_function` dispatches by `function.name`, appends `{"role":"tool",...}`.
- System prompt enforces: get instructions, follow them, get confirmation before permanent op (refund), only call one tool per message.
- Eval pattern: a "customer GPT" (`customer_system_prompt` with query + chat_history) role-plays the user; `execute_conversation` loops until the customer emits "DONE". Automated multi-turn test cases.
- Caveat: model told to invent dummy values when it lacks a backend — fine for demo, not production.
- Model: `gpt-4-turbo`, temperature=0 (agent), 0.5 (customer sim).
- QMX-fit: general copilot guardrails; HITL approvals before irreversible trade/order actions; workflow agents with bounded exit points. [inference]
- LangChain/DeepAgents mapping: LangGraph `interrupt` for HITL confirmation; forced tool use ≈ tool_choice binding; GPT-vs-GPT ≈ simulated-user eval harness. [inference]

### openai-cookbook/examples/vector_databases/oracle_db/deep_research_openai_agents.ipynb
- Pattern: long-term agent memory + deep-research agent on OpenAI Agents SDK; custom `Session` backend over Oracle AI Agent Memory; short-term session vs durable long-term findings separated.
- Mechanism: implement Agents SDK `Session` protocol — four async methods `get_items`, `add_items`, `pop_item`, `clear_session` (subclass `agents.memory.session.SessionABC`); pass instance via `session=` to `Runner.run(agent, q, session=session)`; runner auto-injects prior items and persists new ones.
- Three operational modes framed: Assistant (turn-by-turn), Deep Research (multi-step autonomous), Workflow (predetermined steps w/ branches). Notebook = Deep Research.
- Memory split: session items stored as `message` records `metadata={"session_item":true}` scoped by session_id/user_id/agent_id (short-term replay); durable findings stored as `memory` records via explicit tools. Different lifecycles, one Oracle substrate.
- Tools via `@function_tool` decorator (auto-generates JSON schema from type hints, uses docstring as description): `tavily_search(query,max_results)` (web, Tavily `search_depth="advanced", include_answer=True`), `save_research_finding(topic,finding)` → `memory_client.add_memory(..., metadata={"kind":"research_finding","durable":True})`, `recall_research_findings(query,max_results)` semantic search.
- Memory client: `OracleAgentMemory(connection, embedder="text-embedding-3-small" (1536 dims), extract_memories=False, schema_policy=SchemaPolicy.CREATE_IF_NECESSARY, table_name_prefix=...)`. Register `add_user`/`add_agent`.
- `schema_policy`: `REQUIRE_EXISTING` (no DDL), `CREATE_IF_NECESSARY` (fills missing, safe for dev), `RECREATE` (drops+rebuilds, avoid as default).
- Agent: `Agent(name, instructions, tools=[...], model=MODEL)`, `Runner.run(...)` (async; `nest_asyncio` for Jupyter). Default model `gpt-5.4`.
- Key design: instructions must say "recall before research" and "save durable conclusions" (one atomic finding per call); else store fills with low-value content. Raw tool/session JSON must NOT be promoted to long-term findings.
- Continuity test: new `session_id` + same user_id/agent_id → agent reasons over prior durable findings without old transcript = end-to-end durable memory proof.
- Caveats: Colab can't reach local Docker DB via localhost; this is NOT a general OpenAI memory impl, it's an Oracle-specific Session backend.
- Cited: https://www.oracle.com/database/ai-agent-memory/ ; tavily.com
- QMX-fit: Lab copilot (long experiments, durable findings), workflow/server agents (resume across sessions, remote server). STRONG fit for QMX's long-running background workflow agents. [inference]
- LangChain/DeepAgents mapping: Session protocol ≈ LangGraph checkpointer (thread/short-term); durable findings ≈ LangGraph Store (long-term, cross-thread memory); recall/save tools ≈ store-backed memory tools; `@function_tool` ≈ LangChain `@tool`. [inference]
