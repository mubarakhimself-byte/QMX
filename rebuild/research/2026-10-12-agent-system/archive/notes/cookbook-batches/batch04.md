> SUPERSEDED 2026-10-12 by `tracker/qma-v2/PRD.md` (see `tracker/qma-v2/FILE-INDEX.md`). Kept for history.

# batch04 notes

Reader for QMX. 25 extracts (claude-cookbooks: skills, third_party connectors, tool_evaluation, tool_use). Heaviest value: the `tool_use/` cluster (compaction, context editing, memory, PTC, tool search, tool_choice, parallel/batch). Third-party (LlamaIndex/Pinecone/Wikipedia/Wolfram/ElevenLabs) are older RAG/connector recipes; mostly QMX-adjacent not QMX-core.

## PART A — INDEX

- claude-cookbooks/skills/README.md — Agent Skills overview: progressive-disclosure skill packages (xlsx/pptx/pdf/docx), beta headers, container `skills`, Files API download of generated docs.
- claude-cookbooks/third_party/ElevenLabs/low_latency_stt_claude_tts.ipynb — voice loop: ElevenLabs STT -> Claude (streaming) -> ElevenLabs TTS; sentence/websocket streaming to cut latency. (voice-if-agentic, borderline)
- claude-cookbooks/third_party/ElevenLabs/README.md — companion README for the voice assistant; setup, websocket script, troubleshooting. (mostly not agent-relevant)
- claude-cookbooks/third_party/LlamaIndex/Basic_RAG_With_LlamaIndex.ipynb — minimal LlamaIndex RAG pipeline (VectorStoreIndex, query_engine) on Claude. (RAG, not agentic)
- claude-cookbooks/third_party/LlamaIndex/Multi_Document_Agents.ipynb — per-doc ReActAgent + IndexNode top-level retriever to route across many docs (agentic RAG).
- claude-cookbooks/third_party/LlamaIndex/Multi_Modal.ipynb — AnthropicMultiModal image understanding + Pydantic structured output (ticker extraction). (multimodal/extraction)
- claude-cookbooks/third_party/LlamaIndex/ReAct_Agent.ipynb — ReActAgent over FunctionTool (calc) and QueryEngineTool (10-K RAG).
- claude-cookbooks/third_party/LlamaIndex/README.md — index of LlamaIndex recipes. (not agent-relevant)
- claude-cookbooks/third_party/LlamaIndex/Router_Query_Engine.ipynb — RouterQueryEngine + LLMSingleSelector routes query to summary vs vector tool.
- claude-cookbooks/third_party/LlamaIndex/SubQuestion_Query_Engine.ipynb — SubQuestionQueryEngine decomposes cross-doc queries into sub-queries.
- claude-cookbooks/third_party/Pinecone/claude_3_rag_agent.ipynb — "LangChain v1" XML agent + AgentExecutor, Voyage+Pinecone RAG tool, buffer memory. (LangChain, directly relevant)
- claude-cookbooks/third_party/Wikipedia/wikipedia-search-cookbook.ipynb — legacy stop-sequence search loop; scratchpad planning + info-extraction-before-answer. (research agent pattern)
- claude-cookbooks/third_party/WolframAlpha/using_llm_api.ipynb — single tool wrapping Wolfram LLM API; classic tool_use round-trip.
- claude-cookbooks/tool_evaluation/tool_evaluation.ipynb — harness: agents run eval tasks, score vs ground-truth, log tool timings + ask model for tool feedback.
- claude-cookbooks/tool_use/automatic-context-compaction.ipynb — SDK `tool_runner` `compaction_control` auto-summarizes history past a token threshold.
- claude-cookbooks/tool_use/calculator_tool.ipynb — minimal single-tool round-trip example.
- claude-cookbooks/tool_use/context_engineering/context_engineering_tools.ipynb — the key doc: compaction vs tool-result clearing vs memory, with exact API types/headers/knobs. (highest value)
- claude-cookbooks/tool_use/customer_service_agent.ipynb — client-side tools (lookup/cancel order) + while-loop agent. (cancel = side-effect/HITL)
- claude-cookbooks/tool_use/extracting_structured_json.ipynb — tool-use as structured-JSON extractor (summary/NER/sentiment/classify/open-schema).
- claude-cookbooks/tool_use/memory_cookbook.ipynb — memory_20250818 + context editing (clear_tool_uses, clear_thinking) via code-review agent; security caveats.
- claude-cookbooks/tool_use/parallel_tools.ipynb — `batch_tool` meta-tool to force parallel tool calls.
- claude-cookbooks/tool_use/programmatic_tool_calling_ptc.ipynb — PTC: `allowed_callers` + code_execution so Claude writes code calling tools, keeping big results out of context.
- claude-cookbooks/tool_use/threat_intel_enrichment_agent.ipynb — multi-source agentic loop over IOC tools + structured report. (finance-adjacent SOC pattern)
- claude-cookbooks/tool_use/tool_choice.ipynb — `tool_choice` auto/tool/any semantics and prompt caveats.
- claude-cookbooks/tool_use/tool_search_alternate_approaches.ipynb — tool discovery via `describe_tool` + `tool_reference` + `defer_loading=True` to scale to thousands of tools without breaking cache.

## PART B — PATTERN NOTES

### claude-cookbooks/tool_use/context_engineering/context_engineering_tools.ipynb
- Single best reference in batch: three first-party context-management primitives contrasted on a long-running research agent (reads 8 ~40K-token docs, ~320K total).
- **Compaction**: whole-transcript summarization. Type `compact_20260112`, beta header `compact-2026-01-12`. Server-side token trigger, min 50K, default `trigger` 150K. Knobs: `trigger` (`{"type":"input_tokens","value":N}`), `instructions` (fully REPLACES default prompt), `pause_after_compaction`.
- When compaction fires it returns a typed `compaction` content block; you serialize it back as `{"type":"compaction","content": block.content}` and API drops everything before it.
- **Tool-result clearing**: sub-transcript op. Type `clear_tool_uses_20250919`, beta header `context-management-2025-06-27`. Default `trigger` 100K, `keep` default 3 tool uses. Knobs: `keep` (`{"type":"tool_uses","value":N}`), `clear_at_least` (`{"type":"input_tokens",...}`), `exclude_tools`, `clear_tool_inputs`. Replaces old `tool_result` bodies with placeholder, keeps the `tool_use` record; lossless because re-fetchable.
- Also `clear_thinking_20251015` for extended-thinking blocks; MUST be first entry in `edits` array when combined.
- Response reports `context_management.applied_edits` (tool uses cleared, tokens freed) — observable for tuning.
- Caveat: clearing INVALIDATES cached prompt prefixes; use `clear_at_least` so each clear frees enough to be worth the cache-write cost.
- **Memory tool**: type `memory_20250818`, NO beta header (standalone). Client implements commands: `view, create, str_replace, insert, delete, rename` under `/memories`. Auto-injected system prompt: "ALWAYS VIEW YOUR MEMORY DIRECTORY BEFORE DOING ANYTHING ELSE... context window might be reset at any moment".
- Config shape example given inline (`context_management={"edits":[{...}]}`), plus betas list `["context-management-2025-06-27","compact-2026-01-12"]` when combining.
- `exclude_tools: ["memory"]` recommended when clearing + memory active, so memory reads/writes aren't cleared.
- Numbers/claims: compaction preserves high-level facts, drops obscure specifics (appendix cells); clearing is lossless-if-recallable; memory lossless on what was saved. Context rot cited: recall degrades as window fills even under 1M (Sonnet 4.6 / Opus 4.6 = 1M window). Prefill latency scales with context size regardless of limit.
- Effective-memory prompting: topical guidance ("Only write down information relevant to <topic>"), keep-organized instruction, initializer-session structure (progress log/checklist), storage hygiene (cap sizes, path-traversal guard).
- Mapping table restated: compaction=all in-session growth; clearing=tool-result bloat; memory=cross-session.
- Cited URLs (verbatim): https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents ; https://research.trychroma.com/context-rot ; https://platform.claude.com/docs/en/build-with-claude/compaction ; https://platform.claude.com/docs/en/build-with-claude/context-editing ; https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool ; https://www.anthropic.com/engineering/advanced-tool-use ; https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Default compaction prompt quoted (short): write a `<summary></summary>` of the transcript for continuity.
- QMX-fit: all lanes, esp. Lab copilot long experiments + background/server workflow agents. LangChain/DeepAgents mapping (inference): compaction -> LangGraph pre-model-hook/summarization node + checkpointer; clearing -> custom message-trimming middleware on state; memory -> LangGraph Store (`/memories` = namespaced store backend). UNVERIFIED mapping.

### claude-cookbooks/tool_use/programmatic_tool_calling_ptc.ipynb
- Pattern: PTC — Claude writes Python in the Code Execution sandbox that calls your tools, so large/metadata-heavy tool results never enter the model context.
- Mechanism: add `allowed_callers` to each tool, value `["code_execution_20250825"]` (or `["direct","code_execution_20250825"]` for both). Append the code-execution tool `{"type":"code_execution_20250825","name":"code_execution"}`. Beta header `advanced-tool-use-2025-11-20`. Use `client.beta.messages.create`.
- `caller` field on each `tool_use` block tells direct vs programmatic; results for `code_execution_20250825` are seen only by the container, not the model. Pass `container`/`container_id` across turns for stateful workflows (single-turn doesn't need it); container has `expires_at`.
- `input_examples` provided on tool defs to steer calls. Tools opted in should be safe for repeated unsupervised execution.
- Use cases named: large metadata-rich datasets needing filter/aggregate; sequential dependency chains (e.g. only check custom budget after finding over-budget employees); loops over many entities.
- Numbers: reports "significant"/"dramatic" token reduction; demo computes Token Reduction % and Time Reduction % live (exact figures not in extract). Caveat: PTC may use MORE API round-trips (more structured sequential code) but far fewer tokens.
- Cited URLs: https://docs.claude.com/en/docs/agents-and-tools/tool-use/implement-tool-use ; https://www.anthropic.com/engineering/advanced-tool-use
- QMX-fit: Lab copilot (coding/workflow building, large market/expense/backtest datasets), Portfolio copilot (optimisation over many positions), background workflow. LangChain/DeepAgents mapping (inference): closest to a sandboxed code-interpreter tool node; no direct LangGraph equivalent — would wrap a Python sandbox tool. UNVERIFIED.

### claude-cookbooks/tool_use/tool_search_alternate_approaches.ipynb
- Pattern: scale to thousands of tools without bloating context or breaking cache, via tool DISCOVERY rather than embedding search.
- Mechanism: system prompt lists only tool NAMES; a `describe_tool` tool loads a tool's full def on demand. On call, return a `tool_result` of type `tool_reference` (`{"type":"tool_reference","tool_name":...}`) AND append the real tool to `tools` with `defer_loading=True`. Beta header `advanced-tool-use-2025-11-20`.
- `defer_loading=True` keeps the tool definition OUT of the cached prompt prefix; it's injected only where Claude sees the `tool_reference`, so discovering tools doesn't invalidate the system-prompt cache.
- Alternatives listed: `list_tools` (names by category/keyword), hierarchical browse-then-load, hybrid with semantic search. Points at companion "Tool Search with Embeddings".
- QMX-fit: general copilot and Lab copilot (can host any tool), the whole QMX "Lego" add/remove-tools vision. LangChain/DeepAgents mapping (inference): dynamic tool binding / a tool-registry retriever that binds tools into the agent at runtime; LangGraph has no native `defer_loading` equivalent. UNVERIFIED.

### claude-cookbooks/tool_use/automatic-context-compaction.ipynb
- Pattern: SDK-side automatic compaction in the agentic loop via `client.beta.messages.tool_runner(...)` with `compaction_control`.
- Mechanism: `compaction_control={"enabled":True,"context_token_threshold":N,"model":...,"summary_prompt":...}`. Only `enabled` required. Default threshold 100,000. Optional `model` (e.g. `claude-haiku-4-5` for cheaper summaries), `summary_prompt`. Summary wrapped in `<summary></summary>`.
- `beta_tool` decorator turns a Python fn (args+docstring) into a tool. Uses `anthropic.types.beta.BetaMessageParam`. Detect compaction by message-count DECREASE between turns.
- Server-side compaction recommended instead for Opus 4.6; this SDK path is for older models or using a different/cheaper summarizer.
- Numbers (demo, 5 tickets × 7 tool calls = 35 calls): baseline ~150,000 cumulative input by turn 27; with 5K threshold total ~79,000 tokens; two compaction events.
- Threshold guidance: 5k-20k sequential item processing; 50k-100k multi-phase; 100k-150k needs history; default 100k. Don't set too low or the summary itself re-triggers.
- Caveats: does NOT work well with server-side sampling loops (web search, server-side extended thinking) — cache tokens accumulate and trigger prematurely. Lossy: KB article text / full drafts dropped; IDs/categories/priorities kept.
- For no-tool chat loops you implement compaction manually (track tokens, request SUMMARY_PROMPT, replace history).
- Cited URL: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- QMX-fit: background workflow agents processing queues (tickets ~ trade signals / symbols), Lab long experiments. LangChain/DeepAgents mapping (inference): LangGraph summarization/pre-model hook + checkpointer; `tool_runner` ~ the prebuilt react loop. UNVERIFIED.

### claude-cookbooks/tool_use/memory_cookbook.ipynb
- Pattern: cross-session learning (memory) + in-session context editing, via a code-review agent that learns bug patterns.
- Mechanism: tool `{"type":"memory_20250818","name":"memory"}`; `client.beta.messages.create(betas=["context-management-2025-06-27"], context_management={...})`. Six commands table (view/create/str_replace/insert/delete/rename), file-backed `/memories`.
- Context editing config: `clear_thinking_20251015` (`keep`:`{"type":"thinking_turns","value":1}`, `"keep":"all"` for max cache hits, requires `thinking={"type":"enabled","budget_tokens":N}`) MUST be first; then `clear_tool_uses_20250919` (`trigger` input_tokens, `keep` tool_uses, `clear_at_least`).
- Loop pattern: keep calling API while response has tool_use, execute, feed results back.
- Numbers: Claude 4 family = 200k context; demo `clear_at_least: 50` tokens (memory results tiny ~50-150 tokens); production triggers 30-40k tokens, clear_at_least 3000-5000.
- Supported models listed: Opus 4.1, Opus 4, Sonnet 4.6, Sonnet 4, Haiku 4.5 (memory); claims Opus 4.1 & Sonnet 4.6.
- Security caveats (important for QMX): memory poisoning (files re-enter context = prompt-injection vector) — sanitize, per-user/per-project isolation, audit/log, instruct Claude to ignore instructions in memory; path-traversal protection; don't store secrets/PII; bound growth.
- Cited URLs: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents ; https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool ; https://github.com/anthropics/claude-code-action
- QMX-fit: Lab copilot (learns analysis/coding patterns across sessions), Portfolio (remembers risk conventions), general copilot. LangChain/DeepAgents mapping (inference): LangGraph Store with namespaces = per-user/per-project memory isolation. UNVERIFIED.

### claude-cookbooks/tool_use/tool_choice.ipynb
- Pattern: control tool invocation. `tool_choice` options: `{"type":"auto"}` (default, model decides), `{"type":"tool","name":X}` (force specific tool — classic structured-output trick, e.g. `print_sentiment_scores`), `{"type":"any"}` (must call some tool, model picks — e.g. SMS-only chatbot).
- Mechanism: pass `tool_choice` to `messages.create`. Caveat: with `auto`, Claude over-eager to call tools; detailed system prompt matters ("only search queries you can't confidently answer", provide today's date, future-event rule).
- Even when forcing a tool, still prompt-engineer the content.
- QMX-fit: general/Lab/Portfolio copilots — force structured outputs (risk JSON, order drafts) and gate "must act" assistants. LangChain/DeepAgents mapping (inference): `llm.bind_tools(..., tool_choice=...)`. UNVERIFIED.

### claude-cookbooks/tool_use/parallel_tools.ipynb
- Pattern: force parallel tool calls when model (then-3.7 Sonnet) is reluctant even without `disable_parallel_tool_use`, by adding a `batch_tool` meta-tool wrapping multiple invocations.
- Mechanism: `batch_tool` schema has `invocations: [{name, arguments(string)}]`; client dispatcher iterates invocations, `json.loads` arguments, runs each real tool, joins results into one tool_result. Default `tool_choice` auto + default parallel allowed.
- Benefit: one round-trip instead of sequential back-and-forth -> lower latency.
- QMX-fit: Portfolio/Lab fan-out (quote many symbols at once), background workflow. LangChain/DeepAgents mapping (inference): native parallel tool nodes / a batched tool; largely obsoleted by newer models' native parallel calls. UNVERIFIED.

### claude-cookbooks/tool_use/customer_service_agent.ipynb
- Pattern: client-side tools + while-loop agent (`while response.stop_reason == "tool_use"`). Tools: `get_customer_info`, `get_order_details`, `cancel_order`.
- Mechanism: tools as JSON schemas; `process_tool_call` dispatch; append assistant content then `tool_result` (`tool_use_id`) and re-call. `client.messages.create` with `tools`.
- Note for QMX: `cancel_order` is an irreversible side-effect — in QMX any trade/cancel tool must be HITL-gated.
- QMX-fit: general copilot shape; Portfolio order ops (gated). LangChain/DeepAgents mapping (inference): standard ReAct tool loop; HITL = LangGraph `interrupt` before side-effect tools. UNVERIFIED.

### claude-cookbooks/tool_use/extracting_structured_json.ipynb
- Pattern: tool-use coerces well-structured JSON (no JSON-mode). Examples: article summary (author/topics/summary/coherence int/persuasion float), NER (entities array), sentiment scores, classification, and open-ended schema via `input_schema:{"type":"object","additionalProperties":True}`.
- Mechanism: define a `print_*` tool; read `content.type=="tool_use"` `.input`. For open schema, force with `tool_choice={"type":"tool","name":...}` + prompt describing key/value convention.
- QMX-fit: all copilots (extract risk params, trade intents, news entities into typed objects). LangChain/DeepAgents mapping (inference): `with_structured_output` / Pydantic output schema. UNVERIFIED.

### claude-cookbooks/tool_use/threat_intel_enrichment_agent.ipynb
- Pattern: agentic multi-source enrichment loop (SOC analogue of QMX market-research): IOC in -> Claude chooses/chains tools -> correlate -> structured report. `for _turn in range(MAX_TURNS=10)` caps cost.
- Mechanism: four tools (lookup_ip_reputation, lookup_file_hash, lookup_domain, get_mitre_techniques) as swappable mock backends; system prompt frames "senior analyst", instructs cross-source pivoting (hash->contacted IPs->IP rep->MITRE). Second pass transforms free text into JSON via `REPORT_SCHEMA` (severity enum, confidence int, mitre_techniques array...).
- Production notes: swap mocks for real APIs (VirusTotal/AbuseIPDB/Shodan), asyncio for bulk + caching TTLs, force JSON via tool-use, STIX export, confidence calibration by source reliability.
- Cited URLs: https://anthropic.com/research/building-effective-agents ; https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview ; https://attack.mitre.org/
- QMX-fit: Lab research copilot and background workflow (news/signal enrichment, multi-source correlation), strong template for a QMX "market intel" agent. LangChain/DeepAgents mapping (inference): ReAct agent + tool fan-out; report step = structured-output node; MAX_TURNS = recursion_limit. UNVERIFIED.

### claude-cookbooks/tool_evaluation/tool_evaluation.ipynb
- Pattern: eval harness for TOOL quality. Agent runs each task from an XML eval file, scores exact-match vs ground truth, and asks the model itself for `<feedback>` on tool names/params/descriptions/errors.
- Mechanism: `EVALUATION_PROMPT` requires `<summary>`/`<feedback>`/`<response>` tags; `agent_loop` while `stop_reason=="tool_use"`, times each tool call (`tool_metrics`: count + durations). Report: accuracy, avg duration, avg tool calls. `claude-sonnet-4-6`. Caveat: demo uses `eval()` to dispatch tools (flags "use safe dispatch in production"); deliberately empty tool/param descriptions to test feedback.
- QMX-fit: Lab/workflow — regression-grade eval of QMX's own tool suite (broker/CCXT tool clarity, latency). LangChain/DeepAgents mapping (inference): LangSmith eval dataset + graders; no state primitive. UNVERIFIED.

### claude-cookbooks/skills/README.md
- Pattern: Agent Skills — progressive-disclosure packages (SKILL.md + optional scripts/ + resources/) loaded only when needed to save tokens. Built-ins: xlsx, pptx, pdf, docx.
- Mechanism: beta header `anthropic-beta: code-execution-2025-08-25,files-api-2025-04-14,skills-2025-10-02`. `container={"skills":[{"type":"anthropic","skill_id":"xlsx","version":"latest"}]}` + tool `{"type":"code_execution_20250825","name":"code_execution"}`. Generated files return `file_id`; download via Files API `client.beta.files.download(file_id)` (`.read()`), `retrieve_metadata` (`size_bytes`), `list`, `delete`.
- Perf tips: reuse container IDs to reuse loaded skills; compose skills; files overwritten by default.
- Cited URLs: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills ; https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview ; best-practices docs.
- QMX-fit: Lab/Portfolio report generation (Excel/PPT/PDF financial reports), general copilot. LangChain/DeepAgents mapping (inference): DeepAgents has its own "skills"/subagent concept; closest mapping is a skill registry or a report-building tool, plus a code sandbox. UNVERIFIED.

### claude-cookbooks/third_party/Pinecone/claude_3_rag_agent.ipynb
- Pattern: RAG agent on "LangChain v1" (note: pins LangChain 0.1.11 — older than QMX's v1 target; treat as historical LCEL, UNVERIFIED relevance). XML agent preferred for Anthropic models over ReAct text format.
- Mechanism: `@tool arxiv_search` embeds query (Voyage `voyage-2`) -> Pinecone `index.query(top_k=5)`; agent built with LCEL pipe: input/chat_history/agent_scratchpad -> `hub.pull("hwchase17/xml-agent-convo")` -> `ChatAnthropic(...).bind(stop=["</tool_input>","</final_answer>"])` -> `XMLAgentOutputParser()`; wrapped in `AgentExecutor`. `convert_intermediate_steps` renders `<tool>/<tool_input>/<observation>` XML.
- Memory: `ConversationBufferWindowMemory(k=5)`, manually added; `memory2str` -> "Human:/AI:" string (XML agent can't take message objects directly).
- Pinecone `ServerlessSpec(cloud="aws", region="us-west-2")`, metric dotproduct/cosine, dim from embed length.
- QMX-fit: Lab/general copilot RAG over QMX corpus (GitBook/wiki). LangChain/DeepAgents mapping: this IS LangChain — but legacy AgentExecutor/LCEL; QMX should use LangGraph `create_react_agent` + a retriever tool + checkpointer memory instead. UNVERIFIED version gap.

### claude-cookbooks/third_party/Wikipedia/wikipedia-search-cookbook.ipynb
- Pattern (LEGACY, Claude 2): iterative research/search loop via stop-sequence tool-calling before native tool use existed. Scratchpad planning, `<search_query>` stop sequence, `<search_quality>` reflection, then extract `<information>` and answer in a SEPARATE prompt so Claude doesn't pre-commit to an answer.
- Mechanism: `completions.create` with `stop_sequences=[...,"</search_query>"]`, loop up to `max_searches_to_try`; `WikipediaSearchTool` truncates pages to N tokens via tokenizer; abstract `SearchTool` base swappable for any search API.
- Insight worth keeping: separating information-gathering from final synthesis improves ordering/accuracy (movies-release-order example).
- QMX-fit: research/Lab agent design principle (plan -> gather -> synthesize separately). LangChain/DeepAgents mapping (inference): multi-step research subagent; the separate-synthesis step maps to a final node reading isolated findings. Mechanism itself obsolete (use native tool use). UNVERIFIED.

### claude-cookbooks/third_party/WolframAlpha/using_llm_api.ipynb
- Pattern: single external-knowledge tool (Wolfram LLM API) via classic tool_use round-trip. `claude-haiku-4-5`, `client.beta.tools.messages.create` (older beta namespace). Handles `stop_reason=="tool_use"`, returns `tool_result`.
- Minor schema bug in extract: property is `search_query` but `required:["query"]` — note as example of description/param mismatch.
- QMX-fit: Lab copilot (quant math / data lookups). LangChain/DeepAgents mapping: a single function tool. UNVERIFIED.

### claude-cookbooks/third_party/LlamaIndex/Multi_Document_Agents.ipynb
- Pattern: agentic RAG over many docs. Per-doc `ReActAgent.from_tools([vector_tool, summary_tool])`; wrap each agent as `IndexNode(obj=agent)`; top-level `VectorStoreIndex(objects=...)` with `as_query_engine(similarity_top_k=1)` routes a query to the right doc-agent, which then picks vector vs summary tool.
- Mechanism: `QueryEngineTool` + `ToolMetadata(name, description)`; HuggingFace embeddings (bge-base), `Settings.chunk_size=512`.
- QMX-fit: Lab copilot RAG over segmented QMX corpus (one agent per doc/domain). LangChain/DeepAgents mapping (inference): subagents-per-domain + a router node; IndexNode routing ~ a supervisor selecting a subagent. UNVERIFIED.

### claude-cookbooks/third_party/LlamaIndex/ReAct_Agent.ipynb
- Pattern: ReActAgent over `FunctionTool` (add/multiply) and over `QueryEngineTool` (Uber/Lyft 10-K RAG). `agent.chat(...)`, `agent.get_prompts()` exposes the tool-selection prompt.
- QMX-fit: baseline agent-loop shape; Lab/Portfolio financial-doc Q&A. LangChain/DeepAgents mapping: `create_react_agent` + function tools + retriever tools. UNVERIFIED.

### claude-cookbooks/third_party/LlamaIndex/Router_Query_Engine.ipynb
- Pattern: RouterQueryEngine + `LLMSingleSelector` routes to summary (tree_summarize) vs vector query engine per query. Lightweight alternative to a full agent for "which index?".
- QMX-fit: cheap routing inside Lab RAG. LangChain/DeepAgents mapping (inference): conditional edge / classifier node choosing a retriever. UNVERIFIED.

### claude-cookbooks/third_party/LlamaIndex/SubQuestion_Query_Engine.ipynb
- Pattern: `SubQuestionQueryEngine.from_defaults(query_engine_tools=[...])` decomposes a cross-document comparative query into per-tool sub-questions, then combines. (e.g. compare Uber vs Lyft revenue growth.)
- QMX-fit: Lab copilot multi-asset / multi-doc comparison. LangChain/DeepAgents mapping (inference): planner that emits sub-queries fanned to retriever tools, then synthesis node. UNVERIFIED.

### claude-cookbooks/third_party/LlamaIndex/Multi_Modal.ipynb
- Pattern: `AnthropicMultiModal` for image understanding (alt-text from local/URL images) and structured extraction from an image via `MultiModalLLMCompletionProgram.from_defaults(output_cls=PydanticModel)`. Example extracts stock ticker list (direction/ticker/company/shares/percent) from an ARK email screenshot — QMX-relevant (chart/screenshot ingestion).
- QMX-fit: Lab copilot ingesting chart images / broker screenshots into typed data. LangChain/DeepAgents mapping (inference): multimodal message + structured output. UNVERIFIED.

### claude-cookbooks/third_party/LlamaIndex/Basic_RAG_With_LlamaIndex.ipynb
- Pattern: minimal RAG — `SimpleDirectoryReader` -> `VectorStoreIndex.from_documents` -> `as_query_engine(similarity_top_k=3)`. HuggingFace bge-base embeddings, chunk 512. Not agentic (no loop/tools). QMX-fit: baseline retrieval only. Mapping: a retriever, not an agent.

### claude-cookbooks/third_party/ElevenLabs/low_latency_stt_claude_tts.ipynb
- Pattern: voice assistant loop (agentic-adjacent): ElevenLabs STT (`scribe_v1`) -> Claude (`claude-haiku-4-5`) -> ElevenLabs TTS. Latency optimizations: Claude `messages.stream` (time-to-first-token), sentence-boundary chunking to TTS, then WebSocket streaming (best latency+prosody; per-sentence synthesis sounds disconnected).
- Mechanism: `messages.stream(...).text_stream`; measures time-to-first-token reduction %; models `eleven_v3`/`eleven_turbo_v2_5`. Conversation history across turns for context.
- QMX-fit: optional voice front-end for general copilot (desktop); low priority. LangChain/DeepAgents mapping: streaming LLM node + external STT/TTS tools; no state equivalent. UNVERIFIED / borderline agent-relevant.

### claude-cookbooks/third_party/ElevenLabs/README.md
- Companion setup/troubleshooting for the voice notebook + a production `stream_voice_assistant_websocket.py` (mic record, gapless playback, conversation state). Mostly ops/not-agent-core; same QMX-fit note as above.

### claude-cookbooks/third_party/LlamaIndex/README.md
- (not agent-relevant) Index listing the six LlamaIndex recipes; links to docs/discord.

### claude-cookbooks/tool_use/calculator_tool.ipynb
- Pattern: canonical single-tool round-trip (define calculator schema, detect `tool_use`, return `tool_result`, re-call). Uses `eval()` (flagged unsafe). Teaching baseline only.
- QMX-fit: baseline tool-loop reference. LangChain/DeepAgents mapping: one function tool. UNVERIFIED.
