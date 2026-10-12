# Batch 03 notes — cookbook reader/extractor for QMX

Scope: 29 extracts (all claude-cookbooks). Focus families: caching, compaction,
multi-agent orchestration, workflow primitives, skills, multimodal subagents,
usage/cost observability, research-agent prompts.

## PART A — INDEX

- claude-cookbooks/misc/how_to_make_sql_queries.ipynb — NL→SQL via one Messages call feeding schema string into prompt; executes result on SQLite. (barely agent-relevant: text-to-tool-arg pattern)
- claude-cookbooks/misc/metaprompt.ipynb — prompt-generator: a long multishot "metaprompt" writes a `{$VAR}` prompt template for a task; notes no-prefill on 4.6+ models. (prompt-engineering)
- claude-cookbooks/misc/prompt_caching.ipynb — automatic vs explicit `cache_control` breakpoints; multi-turn moving breakpoint; pricing/TTL/min-length numbers.
- claude-cookbooks/misc/read_web_pages_with_haiku.ipynb — fetch URL with requests, summarize with Haiku. (not agent-relevant beyond cheap-model summarization)
- claude-cookbooks/misc/sampling_past_max_tokens.ipynb — continue a max_tokens-truncated reply by feeding partial text back as assistant turn (prefill). (small mechanism)
- claude-cookbooks/misc/session_memory_compaction.ipynb — manual conversation compaction: traditional (blocking) vs instant (background-thread proactive), with caching to cut cost ~80%.
- claude-cookbooks/misc/speculative_prompt_caching.ipynb — warm cache with 1-token request while user types to cut TTFT on large reused context.
- claude-cookbooks/multimodal/crop_tool.ipynb — agentic zoom/crop tool for fine image detail; `tool_runner`, `@beta_tool`, pixel-coordinate resizing, chart-reading accuracy numbers.
- claude-cookbooks/multimodal/reading_charts_graphs_powerpoints.ipynb — PDF/vision for charts & slide decks; narrate-deck-to-text for RAG; pdfs beta header. (multimodal finance-doc)
- claude-cookbooks/multimodal/using_sub_agents.ipynb — Opus orchestrator writes prompt, parallel Haiku subagents extract per-PDF, Opus synthesizes + matplotlib. (orchestrator/worker)
- claude-cookbooks/observability/usage_cost_api.ipynb — Admin API for token usage & USD cost; buckets, group_by, pagination, CSV export.
- claude-cookbooks/patterns/agents/async_multi_agent_orchestration.ipynb — async subagent orchestration: message hub, send/wait tools, spawn/status/kill subagent tools.
- claude-cookbooks/patterns/agents/basic_workflows.ipynb — three primitives: prompt chaining, parallelization, routing.
- claude-cookbooks/patterns/agents/evaluator_optimizer.ipynb — generator+evaluator loop until PASS.
- claude-cookbooks/patterns/agents/latency_multi_agent.ipynb — shared team clock + latency pressure/budget to steer multi-agent speed.
- claude-cookbooks/patterns/agents/orchestrator_workers.ipynb — FlexibleOrchestrator: orchestrator LLM emits XML subtasks, workers execute.
- claude-cookbooks/patterns/agents/prompts/citations_agent.md — prompt for a citations subagent that adds citation tags without altering text.
- claude-cookbooks/patterns/agents/prompts/research_lead_agent.md — full lead research-agent system prompt (query typing, subagent counts, delegation).
- claude-cookbooks/patterns/agents/prompts/research_subagent.md — research subagent system prompt (OODA loop, tool budget, source quality).
- claude-cookbooks/patterns/agents/README.md — index of the Building Effective Agents patterns. (index)
- claude-cookbooks/README.md — cookbook table of contents. (index, not agent-relevant)
- claude-cookbooks/skills/CLAUDE.md — skills cookbook repo guide: beta headers, Files API gotchas, container param. (skills infra)
- claude-cookbooks/skills/custom_skills/analyzing-financial-statements/SKILL.md — custom skill: financial-ratio calculator (SKILL.md anatomy + quant content).
- claude-cookbooks/skills/custom_skills/applying-brand-guidelines/REFERENCE.md — brand reference file (second .md loaded by a skill). (skill content, light agent-relevance)
- claude-cookbooks/skills/custom_skills/applying-brand-guidelines/SKILL.md — brand-styling skill applied to generated docs.
- claude-cookbooks/skills/custom_skills/creating-financial-models/SKILL.md — DCF/sensitivity/Monte-Carlo/scenario modeling skill (multi-file, scripts).
- claude-cookbooks/skills/notebooks/01_skills_introduction.ipynb — Skills API basics: container.skills, code_execution tool, betas, Files API download.
- claude-cookbooks/skills/notebooks/02_skills_financial_applications.ipynb — Skills for finance dashboards/portfolio decks + multi-doc pipeline pattern.
- claude-cookbooks/skills/notebooks/03_skills_custom_development.ipynb — build/upload/version custom skills: `files_from_dir`, `beta.skills.create/versions.create`, compose custom+anthropic skills.

---

## PART B — PATTERN NOTES

### claude-cookbooks/misc/how_to_make_sql_queries.ipynb
- Pattern: natural-language→SQL by injecting the DB schema string into a single `client.messages.create` prompt, then executing the returned SQL on SQLite.
- Mechanism: schema derived via `PRAGMA table_info`; prompt: schema + "Only output the SQL query and nothing else"; `max_tokens=2048`; `MODEL="claude-opus-4-8"`.
- Caveat (inferred): no tool-use/validation; model output executed directly — injection/accuracy risk; no sandbox.
- QMX-fit: Lab copilot (query a user's local data/db). LangChain/DeepAgents mapping (inferred): a single tool whose body runs parameterized SQL; prefer a `@tool` with validation over raw exec.

### claude-cookbooks/misc/metaprompt.ipynb
- Pattern: meta-prompting — a long multishot "metaprompt" instructs the model to author a reusable prompt *template* for a given `TASK`, emitting `<Inputs>`/`<Instructions>` blocks with `{$VAR}` placeholders.
- Mechanism: `MODEL="claude-sonnet-4-6"` writes the template at `temperature=0`; `TEST_MODEL_NAME="claude-haiku-4-5"` test-runs it; `MAX_TOKENS=4096`; variables extracted via regex `{([^}]+)}`.
- Key caveat stated: Claude 4.6-generation-onward models **reject assistant-message prefill** ("putting words in Claude's mouth"); steer from the user turn instead ("Start your response directly with the `<Inputs>` block").
- Also: checks `stop_reason == "max_tokens"` and raises rather than failing later; square-bracket `[Your Name]` placeholders are human-fill, not substituted.
- Cited: platform.claude.com/docs/en/build-with-claude/working-with-messages#putting-words-in-claudes-mouth
- QMX-fit: Lab copilot (help users author prompts/mini-app prompts). LangChain mapping (inferred): a prompt-authoring chain; no direct DeepAgents equivalent.

### claude-cookbooks/misc/prompt_caching.ipynb
- Patterns: (1) automatic caching — single top-level `cache_control={"type":"ephemeral"}` on `messages.create`, system auto-places breakpoint on last cacheable block and moves it forward across turns; (2) explicit breakpoints on individual content blocks / system blocks for mixed TTLs.
- Mechanism: `cache_control={"type":"ephemeral"}`; usage fields `cache_creation_input_tokens`, `cache_read_input_tokens`; multi-turn auto-cache needs no per-block markers; up to 4 explicit breakpoints (auto uses one slot); can combine auto + explicit.
- Numbers (stated): latency >2x faster, cost up to 90% cheaper for repetitive tasks; min cacheable length 1,024 tokens (Sonnet) / 4,096 (Opus & Haiku 4.5); TTL 5 min default (refreshed on hit), 1-hour TTL at 2x base input price; cache writes 1.25x base input, cache reads 0.1x base input. Pride-and-Prejudice context ~187k tokens.
- Requires `anthropic>=0.83.0`; `MODEL="claude-sonnet-4-6"`.
- Cited: docs.anthropic.com/en/docs/build-with-claude/prompt-caching
- QMX-fit: all agent types + server workflows (reuse large system prompts/corpus). LangChain/DeepAgents mapping (inferred): caching is an API-level concern; wire via the Anthropic client; keep a stable prefix (system + corpus) so checkpointer/middleware don't invalidate the cache prefix.

### claude-cookbooks/misc/read_web_pages_with_haiku.ipynb
- Pattern: cheap-model web-page summarization — requests.get URL → pass raw HTML in `<content>` tags → Haiku summarizes.
- Mechanism: `MODEL="claude-haiku-4-5"`, `max_tokens=1024`; no HTML cleaning.
- Caveat (inferred): raw HTML wastes tokens; no robots/trust handling.
- QMX-fit: background workflow / cheap-model news digestion (QMX free-news path). LangChain mapping (inferred): a fetch+summarize tool on a cheap model (DeepSeek/mini).

### claude-cookbooks/misc/sampling_past_max_tokens.ipynb
- Pattern: continue past `max_tokens` by appending the truncated reply as an assistant message and re-requesting (prefill continuation).
- Mechanism: inspect `message.stop_reason == "max_tokens"`; feed `message.content[0].text` back as `{"role":"assistant",...}`; `MODEL="claude-sonnet-4-6"`.
- Caveat (stated verbatim-ish): you are double-charged for input tokens and the prior 4096-token output is re-read as input tokens (not double-charged as output). NOTE: conflicts with metaprompt notebook's "4.6+ reject prefill" — UNVERIFIED which models still allow this; treat as model-dependent.
- QMX-fit: any long-generation agent. LangChain mapping (inferred): loop handling finish_reason=length; no direct DeepAgents equivalent.

### claude-cookbooks/misc/session_memory_compaction.ipynb
- Patterns: proactive conversation compaction for long sessions — (1) traditional: summarize only when token threshold hit (user waits); (2) **instant compaction**: background `threading.Thread` builds/updates a session-memory summary proactively so compaction is an instant swap.
- Mechanism: `SESSION_MEMORY_PROMPT` with structured sections (User Intent / Completed Work / Errors & Corrections / Active Work / Pending Tasks / Key References) and `<think>` analysis; `InstantCompactingChatSession(context_limit=12000, min_tokens_to_init=7500, min_tokens_between_updates=2000)`; `threading.Lock`, daemon threads; `add_cache_control()` puts `cache_control` on last user message + system block.
- Numbers (stated): traditional compaction took **>40s** of user wait; summary compressed to <2K tokens; caching cuts background-update cost ~80% (e.g. $0.015 → ~$0.003 per update); writes to a `session-memory.md` file in production.
- Key takeaways stated: weight recency heavily; preserve user corrections verbatim; build memory proactively; keep an identical message prefix for cache hits.
- Related pointer: ../tool_use/automatic-context-compaction.ipynb (SDK auto-compaction with tool use).
- QMX-fit: general copilot + Lab copilot long experiments; server workflow agents. LangChain/DeepAgents mapping (inferred): maps to a summarization middleware + checkpointer/store; a background pre-summarizer keeps a `session-memory.md` in the store; strongly relevant to QMX's long-running/background agents.

### claude-cookbooks/misc/speculative_prompt_caching.ipynb
- Pattern: speculative cache warming — fire a 1-token request over the large reused context while the user is still typing, so the real request hits a warm cache (lower TTFT).
- Mechanism: `AsyncAnthropic`; `asyncio.create_task(sample_one_token(...))`; `cache_control={"type":"ephemeral"}` on the big context block; `max_tokens=1` for the warmer; reuse *exactly* the same initial message; add timestamps to avoid cross-session cache sharing; monitor `cache_read_input_tokens`. `MODEL="claude-sonnet-4-6"`.
- Best practice stated: start warming on input-field focus; most effective for contexts >1000 tokens reused across queries.
- Numbers: no fixed figures (TTFT improvement computed at runtime); SQLite btree context ~150k tokens.
- QMX-fit: desktop UI responsiveness — warm cache when a copilot/lab panel opens over a large corpus or dataset. LangChain mapping (inferred): client-level optimization, no graph equivalent.

### claude-cookbooks/multimodal/crop_tool.ipynb
- Pattern: agentic **zoom tool** so the model can "lean in" on small image detail; full agentic tool-use loop with image tool results.
- Mechanism: `@beta_tool` builds schema from function signature+docstring; SDK `tool_runner` drives call/feed/stop (`max_iterations`, runner caps iterations at 20 and pause-turn re-entries at 5); `zoom(x1,y1,x2,y2,image_index)` crops from full-res original and upscales to image budget; pre-resize with docs' `resized_size()` so pixel coords map 1:1; crops returned as JPEG to stay under 32MB request limit; uses `anthropic.types.beta` `BetaContentBlockParam`/`BetaMessageParam`.
- Vision facts: 1 visual token per 28×28 patch; standard tier max 1568px/1568 tokens; high-res tier (`claude-fable-5`, `claude-sonnet-5`) 2576px/4784 tokens; handle `stop_reason` values `pause_turn` (resume by replaying transcript) and token-capped turns.
- Numbers (stated): demo problem no-tool 36/40 wrong (90%), with-tool 40/40 correct. Chartography (100 Qs, Surge AI): claude-fable-5 29%→73% (+44pts), claude-sonnet-5 13%→44% (+31pts); mean cost/question fable $0.08→$0.95, sonnet $0.02→$0.64; zoom arm uses prompt caching.
- Caveats: tool buys accuracy with extra tokens/latency (each zoom re-sends convo + crop); near-tie crossing still needs model visual reasoning (sonnet-5 1/10 even with tool). If agent has code execution it may self-serve the crop.
- Cited: huggingface.co/datasets/surgeai/chartography; platform.claude.com/docs/en/build-with-claude/vision#evaluate-image-size; .../vision-coordinates; .../files; agents-and-tools/tool-use/overview.
- QMX-fit: Lab copilot reading dense charts/screenshots; general copilot UI inspection. LangChain/DeepAgents mapping (inferred): a `@tool` returning image content blocks inside the agent loop; `tool_runner` ≈ the agent executor.

### claude-cookbooks/multimodal/reading_charts_graphs_powerpoints.ipynb
- Patterns: pass PDFs of charts/slide decks to Claude via vision+text; narrate a deck slide-by-slide into text for text-only RAG.
- Mechanism: `Anthropic(default_headers={"anthropic-beta":"pdfs-2024-09-25"})`; content block `{"type":"document","source":{"type":"base64","media_type":"application/pdf","data":...}}`; `MODEL="claude-sonnet-4-6"`, `max_tokens=8192`, `temperature=0`; narration parsed from `<narration>`/`<page_narration id=N>` tags.
- Tips (stated): give Claude a calculator tool to avoid arithmetic errors on chart math; prompt "First describe every data point you see"; ask for HEX color identification on color-dependent charts.
- Caveats: ≤100 pages per request across all docs; multimodal PDFs in embeddings cause RAG problems; narration "far from perfect"; narration can take up to ~10 min.
- QMX-fit: Lab/Portfolio copilots ingesting broker statements, research PDFs, earnings decks. LangChain mapping (inferred): document loader + vision model node; the narrate-to-text step feeds a vector store.

### claude-cookbooks/multimodal/using_sub_agents.ipynb
- Pattern: orchestrator/worker multi-agent — Opus writes a tailored extraction prompt, parallel Haiku subagents each read one PDF (as PNG images), Opus synthesizes + writes matplotlib.
- Mechanism: `ThreadPoolExecutor` for concurrent downloads and subagent calls; PDFs→base64 PNGs via PyMuPDF (`fitz`, 300dpi, thumbnail to 1024); orchestrator `generate_haiku_prompt` on `claude-opus-4-8`; workers on `claude-haiku-4-5` (`max_tokens=2048`); results wrapped in `<info quarter="...">` XML; final Opus call emits code in `<code>` tags.
- Caveat (stated): never `exec()` model-written code outside a sandbox (demo does for convenience).
- QMX-fit: Lab/Portfolio copilots doing fan-out document extraction; cheap-model (Haiku/DeepSeek) workers under Opus lead — directly matches QMX main-Opus + cheap-background model split. LangChain/DeepAgents mapping (inferred): subagents (DeepAgents sub-agents) + a synthesis node; ThreadPoolExecutor ≈ parallel subagent spawn.

### claude-cookbooks/observability/usage_cost_api.ipynb
- Pattern: programmatic cost/usage observability via Admin API (not an agent, but QMX cost-control infra).
- Mechanism: Admin key `sk-ant-admin...`; base `https://api.anthropic.com/v1/organizations`; endpoints `usage_report/messages` and `cost_report`; header `anthropic-version: 2023-06-01`, `x-api-key`; params `starting_at`/`ending_at`/`bucket_width`/`group_by[]`/`limit`/`page`; usage fields `uncached_input_tokens`, `output_tokens`, `cache_creation.{ephemeral_1h_input_tokens,ephemeral_5m_input_tokens}`, `cache_read_input_tokens`, `server_tool_use.web_search_requests`; cost in minor units (÷100 = USD).
- Limits (stated): usage granularity `1m` (≤1440 buckets), `1h` (≤168), `1d` (≤31); cost API only `1d`, ≤31 days/request; pagination via `has_more`/`next_page`; group_by model/service_tier/workspace_id.
- Caveats: Priority Tier costs never appear in cost endpoint (usage only); API is for historical analysis not real-time; field names may evolve.
- QMX-fit: server/observability layer — the "what it cost" numbers for QMX's morning-brief/cost-control; subscription-proxy usage won't surface here (UNVERIFIED for proxy). LangChain mapping: no equivalent — external admin reporting.

### claude-cookbooks/patterns/agents/async_multi_agent_orchestration.ipynb
- Patterns: two orchestration shapes behind the Opus 4.8 system card — fixed N-agent team, and dynamic async subagent spawn. Pure messaging mechanics, no domain task.
- Mechanism: in-memory `Hub` (per-agent `inbox` list + `asyncio.Event`, `status`, id counter); tools `send_message`(recipient_ids, content), `wait_for_message`() — messages auto-appended to the next tool result so agents never poll; subagent tools `create_subagents`(base_instruction, per_subagent_instructions[≤10]) returns immediately/non-blocking, `get_status` (active/idling/done/crashed), `kill_subagents`(subagent_ids); base loop `run_agent` is a standard tool-use loop handling `stop_reason` end_turn/tool_use, `max_turns=20`; `AsyncAnthropic`, `MODEL="claude-opus-4-8"`, `max_tokens=2048`; `extra_dispatch` maps tool name→async handler.
- Key design: "appends the drained inbox to the last tool result" — inter-agent messages arrive inline, not via polling.
- Cited: github.com/anthropics/anthropic-sdk-python; docs.claude.com/en/docs/tool-use.
- QMX-fit: background workflow agents + multi-agent lab/portfolio teams on a server. LangChain/DeepAgents mapping (inferred): Hub ≈ LangGraph shared state / message channel; create_subagents ≈ DeepAgents subagents; wait/send ≈ interrupts or custom channels; run_agent ≈ a React agent node.

### claude-cookbooks/patterns/agents/basic_workflows.ipynb
- Patterns (3 primitives, "not production code"): prompt-chaining (`chain`: sequential llm_call passing result forward), parallelization (`parallel`: ThreadPoolExecutor, same prompt over many inputs), routing (`route`: classifier LLM picks a specialized prompt via `<reasoning>`/`<selection>` XML).
- Mechanism: helpers `llm_call` and `extract_xml` from `util.py`; `n_workers=3`; routes are a dict of specialized system prompts keyed by route name.
- QMX-fit: all copilots — routing to Lab vs Portfolio handlers; parallel fan-out for independent subtasks. LangChain/DeepAgents mapping (inferred): chain=sequential StateGraph edges; parallel=fan-out/fan-in nodes; route=conditional edge / router node.

### claude-cookbooks/patterns/agents/evaluator_optimizer.ipynb
- Pattern: generator↔evaluator loop — `generate` emits `<thoughts>`/`<response>`, `evaluate` emits `<evaluation>` (PASS/NEEDS_IMPROVEMENT/FAIL) + `<feedback>`; loop feeds prior attempts + feedback back until PASS.
- Mechanism: `memory` list of attempts appended into context; `llm_call`/`extract_xml`; loops forever until PASS (no max cap shown).
- When-to-use (stated): clear eval criteria + value from iterative refinement + LLM can give meaningful feedback.
- Caveat (inferred): no iteration cap → runaway risk; needs a bound.
- QMX-fit: Lab copilot code/strategy refinement; reviewer-style loops (matches QMX factory reviewer tier). LangChain/DeepAgents mapping (inferred): a two-node cycle in StateGraph with a conditional "PASS" exit edge.

### claude-cookbooks/patterns/agents/latency_multi_agent.ipynb
- Pattern: steer a lead+helpers team's speed with one shared team clock plus either latency "pressure" (one sentence) or a latency "budget" (number on the clock line). Three comparison arms: no clock / pressure / budget.
- Mechanism: `TeamClock` (monotonic, optional `budget`); `clock_line` renders `[elapsed 252s]` or `[elapsed 252s / 600s]`; `stamp_elapsed` appends the line to the newest user message (own text block after task prompt, or extends last tool_result) right before every API call so caching prefix stays intact; one clock object shared so late-spawned helpers see team elapsed, not 0s; `TIME_MATTERS` sentence appended to lead task + every helper brief; budget adds no prompt text; top-level `cache_control` for auto caching; `MODEL` default `claude-fable-5-1`, `EFFORT="xhigh"`, `MAX_HELPERS=4`, `max_tokens=16000`, helper cap 15 calls / lead 40.
- Caveats (stated): approach "newly emerging", not fully tested on Opus 5/earlier — effect varies; client-side tools keep clock fresher (nothing injectable during server-side sampling); budget suits longer tasks (short tasks may overrun rather than abandon); verify answer quality on faster arms; pressure effect on quality unmeasured here.
- Cited: platform.claude.com/docs/en/build-with-claude/prompt-caching; async_multi_agent_orchestration.ipynb.
- QMX-fit: background/server workflow agents where latency vs thoroughness matters; portfolio copilot under time pressure. LangChain/DeepAgents mapping (inferred): inject the clock line via a pre-model middleware that mutates the last message; shared clock in graph state.

### claude-cookbooks/patterns/agents/orchestrator_workers.ipynb
- Pattern: orchestrator-workers — orchestrator LLM decides subtasks *at runtime* (vs hardcoded parallelization), emits `<analysis>` + `<tasks><task><type>/<description></task></tasks>`; workers each get original task + their type/description.
- Mechanism: `FlexibleOrchestrator(orchestrator_prompt, worker_prompt, model)`; `parse_tasks` parses XML; `MODEL="claude-sonnet-4-6"`; workers run sequentially in this impl; response validation for empty worker output.
- When NOT to use (stated): simple single-output tasks, latency-critical, predictable subtasks (use plain parallelization).
- Costs/limitations (stated): N+1 LLM calls; sequential here (suggest asyncio/threadpool); XML parse can fail (consider JSON); orchestrator may decompose poorly. Suggests Opus orchestrator + Haiku workers for cost.
- QMX-fit: Lab copilot workflow-building / dynamic decomposition; mirrors QMX bulk-worker fan-out. LangChain/DeepAgents mapping (inferred): orchestrator node → spawn N worker subagents → synthesis node.

### claude-cookbooks/patterns/agents/prompts/citations_agent.md
- Pattern: dedicated citations subagent — adds citation tags to a `<synthesized_text>` report without altering any content/whitespace; outputs `<exact_text_with_citation>`.
- Mechanism/rules: keep text 100% identical (rejected if not); cite only source-supported claims; cite complete semantic units at sentence ends; no redundant same-source citations; preamble must go before the opening tag; citations render as interactive elements at closing tag.
- QMX-fit: Lab/research copilot final-report citation pass. LangChain/DeepAgents mapping (inferred): a terminal subagent node after report synthesis; relevant to QMX research outputs needing provenance.

### claude-cookbooks/patterns/agents/prompts/research_lead_agent.md
- Pattern: lead research-agent system prompt (the multi-agent research architecture). Plans, classifies, delegates to subagents, synthesizes, never researches the bulk itself.
- Mechanism/structure: `{{.CurrentDate}}` template; query typing — depth-first / breadth-first / straightforward; `<subagent_count_guidelines>` 1 (simple) / 2-3 (standard) / 3-5 (medium) / 5-10 (high, **max 20**); tools `run_blocking_subagent(prompt=...)` and `complete_task` (submits final Markdown report); use parallel tool calls to spawn ~3 subagents at once; read-only use of internal tools (Slack/Asana/Gdrive/Github/Gmail/Gcal) but never write/create/update.
- Stated rules: lead must write the report itself (never delegate report writing); emit no Markdown citations (separate citations agent); stop when diminishing returns; use Bayesian updating; refuse harmful subagent topics; high information density to subagents.
- Cited (in-prompt examples): commerce.gov, ec.europa.eu, SEC EDGAR (illustrative only).
- QMX-fit: Lab copilot "research agent" + server long-running research workflow — directly transferable to QMX free-news/research. LangChain/DeepAgents mapping (inferred): lead = orchestrator React agent; `run_blocking_subagent` = DeepAgents blocking subagent; `complete_task` = structured final-output tool; parallel spawns = fan-out.

### claude-cookbooks/patterns/agents/prompts/research_subagent.md
- Pattern: research subagent system prompt — executes one clear `<task>` via an OODA loop under a tool budget.
- Mechanism/structure: plan a "research budget" of tool calls scaled to difficulty (<5 simple, ~5 medium, ~10 hard, up to 15 very hard); hard cap **20 tool calls / ~100 sources** or subagent terminated; tools web_search (snippets), web_fetch (full pages — always use for URLs/followups), repl (JS-only calcs, no DOM), internal tools (google_drive_search, gmail, gcal, Slack) prioritized when present; parallel tool calls (2 at a time); `complete_task` to report back.
- Stated caveats: short queries (<5 words) return better results; flag speculation/low-quality sources (aggregators, passive voice + nameless sources, marketing/spin); never reuse identical queries; "DO NOT use the evaluate_source_quality tool ever — it is broken".
- QMX-fit: the worker tier of QMX's research/news agents; cheap models can run these. LangChain/DeepAgents mapping (inferred): a subagent with a tool-call budget guard (middleware counting calls) + web_search/web_fetch tools.

### claude-cookbooks/patterns/agents/README.md
- Index of Building Effective Agents patterns (Schluntz & Zhang): prompt chaining, routing, parallelization, orchestrator-subagents, evaluator-optimizer, async multi-agent, latency multi-agent.
- Cited: anthropic.com/research/building-effective-agents.
- QMX-fit: conceptual map for QMX agent layer. Mapping: these are the canonical LangGraph/DeepAgents patterns.

### claude-cookbooks/README.md
- (not agent-relevant) Cookbook table of contents; links classification, RAG, summarization, tool_use (customer_service_agent, calculator_tool), cost_optimization.ipynb (Pareto pass-rate-vs-cost tuning). Useful pointer: cost_optimization cookbook for agent cost/pass-rate tradeoff.

### claude-cookbooks/skills/CLAUDE.md
- Pattern: operational guide for the Agent Skills feature (document generation via code execution).
- Mechanism/beta: all Skills calls use `client.beta.*`; beta headers `code-execution-2025-08-25`, `files-api-2025-04-14`, `skills-2025-10-02`; use `client.beta.messages.create(container={"skills":[...]})` with code execution tool `code_execution_20250825` REQUIRED; pass `betas=[...]` per-request (not default_headers, which forces code_execution on ALL requests); built-in skills `xlsx`/`pptx`/`pdf`/`docx`.
- File gotchas: file IDs at `bash_code_execution_tool_result.content.content[0].file_id`; download with `client.beta.files.download(file_id).read()` (not `.content`); metadata `.size_bytes` (not `.size`), `retrieve_metadata`; SDK >=0.71.0 (text inconsistently also says 0.69.0 — UNVERIFIED).
- Numbers: Excel ~2 min, PPTX ~1-2 min, PDF ~1-2 min generation.
- Cited: docs.claude.com/en/api/messages, /en/api/files-content, /en/docs/agents-and-tools/agent-skills/overview.
- QMX-fit: Lab/Portfolio copilots producing xlsx/pptx/pdf deliverables inside the desktop app. LangChain/DeepAgents mapping (inferred): Skills = server-side container tool; no direct LangGraph node — it's an Anthropic-API container capability (would be called as a tool/managed-agent).

### claude-cookbooks/skills/custom_skills/analyzing-financial-statements/SKILL.md
- Pattern: custom skill anatomy for a quant task — financial-ratio calculator.
- Mechanism: YAML frontmatter `name`/`description`; sections Capabilities / How to Use / Input Format / Output Format / Example Usage / Scripts (`calculate_ratios.py`, `interpret_ratios.py`) / Best Practices / Limitations.
- Content (quant): profitability (ROE/ROA/margins), liquidity (current/quick/cash), leverage (D/E, interest coverage), efficiency (turnovers), valuation (P/E, P/B, P/S, EV/EBITDA, PEG), per-share (EPS, BVPS, DPS); industry benchmarks.
- QMX-fit: Portfolio copilot — reusable ratio/benchmark skill. LangChain/DeepAgents mapping (inferred): package as a skill/tool the agent loads; the `.py` scripts are deterministic calculators the agent calls rather than hand-computing.

### claude-cookbooks/skills/custom_skills/applying-brand-guidelines/REFERENCE.md
- Pattern: a second `.md` file bundled in a skill (all top-level `.md` files load when skill loads) — reference card of colors/fonts/templates/accessibility/file-naming.
- Mechanism: demonstrates progressive-disclosure structure (SKILL.md + REFERENCE.md); content is Acme brand hex/CMYK/Pantone, contrast ratios (4.5:1 body / 3:1 large), file-naming `YYYY-MM-DD_DocumentType_Version_Status.ext`.
- QMX-fit: minor — a styling skill for QMX-generated reports/decks. Mapping (inferred): supporting resource file in a skill bundle.

### claude-cookbooks/skills/custom_skills/applying-brand-guidelines/SKILL.md
- Pattern: brand-consistency skill applied across generated docs (xlsx/pptx/pdf).
- Mechanism: SKILL.md with color palette, typography hierarchy, logo rules, per-format layout standards, tone/data-presentation rules, prohibited elements, `apply_brand.py`/`validate_brand.py` scripts.
- QMX-fit: composed with built-in doc skills to brand QMX outputs (see 03 notebook composing custom+pptx). Mapping (inferred): a skill composed alongside `pptx`/`xlsx`.

### claude-cookbooks/skills/custom_skills/creating-financial-models/SKILL.md
- Pattern: advanced multi-file quant skill — financial modeling suite.
- Mechanism: capabilities DCF (terminal value via perpetuity-growth & exit-multiple, WACC), sensitivity (data tables, tornado charts), Monte Carlo (1,000-10,000 iters, VaR, confidence intervals), scenario planning (best/base/worst, probability weights); scripts `dcf_model.py`, `sensitivity_analysis.py`; auto quality checks (balance-sheet balancing, cash-flow reconciliation, circular-reference resolution, MC statistical validation); model types corporate/project-finance/M&A/LBO.
- Caveats (stated): models only as good as assumptions; not professional financial advice. (Aligns with QMX rule: no personalized investment advice.)
- QMX-fit: Portfolio copilot (risk/sizing/optimization) + Lab copilot modeling. Mapping (inferred): skill bundling deterministic Python models the agent invokes; matches QMX's "risk/sizing authority lives in docs, deterministic" posture.

### claude-cookbooks/skills/notebooks/01_skills_introduction.ipynb
- Pattern: Skills API fundamentals + progressive disclosure.
- Mechanism: `container={"skills":[{"type":"anthropic","skill_id":"xlsx","version":"latest"}]}`; tool `{"type":"code_execution_20250825","name":"code_execution"}`; `betas=["code-execution-2025-08-25","files-api-2025-04-14","skills-2025-10-02"]`; discover via `client.beta.skills.list(source="anthropic")` and `beta.skills.versions.retrieve`; download via `extract_file_ids`/`download_all_files` (Files API); reuse `container.id` to avoid reloading skills.
- Progressive disclosure (3 tiers): metadata (name ≤64 chars, description ≤1024) always visible; full instructions (<5k tokens) loaded when relevant; linked files on demand.
- Numbers (stated): manual instructions ~5,000-10,000 tokens/request vs skills minimal metadata until used (~5k when invoked); claimed ~90-98% initial-context savings.
- Cited: anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills; anthropic.com/news/create-files; docs.claude.com agent-skills overview/best-practices.
- QMX-fit: desktop copilots creating files. Mapping (inferred): Skills = Anthropic container capability; conceptually analogous to DeepAgents/Claude skills but API-hosted (code execution server-side).

### claude-cookbooks/skills/notebooks/02_skills_financial_applications.ipynb
- Pattern: Skills for finance deliverables + multi-document **pipeline** pattern (Excel analysis → PPTX summary → PDF report from one data source).
- Mechanism: `create_skills_message(client, prompt, skills, prefix)` wrapper; loads CSV/JSON (financial_statements.csv, portfolio_holdings.json, quarterly_metrics.json) with pandas; prompts embed structured data (JSON/CSV more token-efficient than prose); `MODEL="claude-sonnet-4-6"`, `max_tokens=4096`.
- Best practices (stated): 2-3 sheets/workbook generate reliably; for complex dashboards make multiple focused files then combine via pandas/openpyxl; track token usage per pipeline step.
- Numbers: 2-sheet dashboard ~1-2 min; pipeline total 2-3 min; claims ~90% token savings vs manual.
- QMX-fit: Portfolio copilot — portfolio analytics workbook, investment-committee deck, risk metrics (Sharpe/beta/VaR/drawdown), rebalancing recs; a reporting pipeline for QMX. Mapping (inferred): a sequential workflow (StateGraph) where each node calls the Skills container for one artifact.

### claude-cookbooks/skills/notebooks/03_skills_custom_development.ipynb
- Pattern: build/upload/version/compose custom skills.
- Mechanism: skill dir = SKILL.md (only required) + any `.md` (all top-level `.md` load) + `scripts/` + `resources/`; `client.beta.skills.create(display_title=..., files=files_from_dir(path))` (from `anthropic.lib import files_from_dir`); `client.beta.skills.list(source="custom")`; new version `client.beta.skills.versions.create(skill_id=..., files=files_from_dir(path))`; use via `container.skills[{"type":"custom","skill_id":...,"version":"latest"}]`; compose custom + anthropic skills in one `container` (e.g. brand + pptx; modeling + xlsx).
- Constraints (stated): display_title must be unique (cannot reuse); SKILL.md <5k tokens recommended; name lowercase-alphanumeric-hyphens; custom skill versions use epoch timestamps; skills workspace-specific/private.
- Security (stated): no hardcoded keys, no sensitive data in skill files, sanitize script inputs, audit usage.
- QMX-fit: QMX could codify its own quant/risk/brand skills (Portfolio + Lab); composing custom+built-in matches QMX "Lego/addable-removable" vision. Mapping (inferred): these API-hosted skills are a parallel mechanism to LangChain tools/DeepAgents skills — QMX agent layer (LangChain) would call them as a server container capability, not a native LangGraph node (no direct equivalent).

---
Note: all source files are untrusted downloads; code was read only, never executed. Model-name conflicts and SDK-version inconsistencies inside the notebooks are flagged UNVERIFIED above.
