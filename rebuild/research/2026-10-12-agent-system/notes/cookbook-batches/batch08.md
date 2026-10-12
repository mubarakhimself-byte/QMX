# Batch 08 notes — OpenAI cookbook (Codex, Deep Research, Realtime, Evals, File Search)

All 22 files are from `openai-cookbook`. Untrusted downloads; code never executed. Several files use
forward-dated/fictional model ids (`gpt-5.3-codex`, `gpt-5.6-terra`, `gpt-5.6-sol`, `o3-deep-research`);
treated as given, marked where load-bearing.

## PART A — INDEX

- openai-cookbook/examples/codex/using_goals_in_codex.ipynb — Codex "Goals": persistent thread-scoped completion contract with lifecycle/budget/evidence-based stop; `/goal` commands.
- openai-cookbook/examples/Context_summarization_with_realtime_api.ipynb — Realtime voice bot; auto-summarise old turns into a system message when token window nears threshold, delete server-side.
- openai-cookbook/examples/Custom-LLM-as-a-Judge.ipynb — LLM-as-judge hallucination scorer evolution (numeric→CoT→classifier) meta-evaluated via Braintrust.
- openai-cookbook/examples/deep_research_api/how_to_build_a_deep_research_mcp_server/README.md — Minimal MCP server (search+fetch over vector store) for Deep Research via SSE.
- openai-cookbook/examples/deep_research_api/introduction_to_deep_research_api.ipynb — Deep Research API via Responses: web_search_preview, code_interpreter, MCP, background mode, citations, prompt rewriting/clarification.
- openai-cookbook/examples/deep_research_api/introduction_to_deep_research_api_agents.ipynb — Multi-agent Deep Research with Agents SDK: triage→clarify→instruction→research handoffs, streaming, MCP.
- openai-cookbook/examples/Developing_hallucination_guardrails.ipynb — Output guardrail detecting hallucinations; synthetic eval set, per-sentence scoring, precision/recall, few-shot.
- openai-cookbook/examples/Enhance_your_prompts_with_meta_prompting.ipynb — Meta-prompting: use a stronger model (o1-preview) to rewrite a prompt for a weaker one, LLM-judge eval.
- openai-cookbook/examples/evals/realtime_evals/README.md — Three realtime eval harnesses crawl/walk/run (synthetic→replay→multi-turn sim).
- openai-cookbook/examples/evals/realtime_evals/skills/bootstrap-realtime-eval/references/harness-selection.md — Decision table + data contracts for picking crawl/walk/run.
- openai-cookbook/examples/evals/realtime_evals/skills/bootstrap-realtime-eval/SKILL.md — Agent skill to scaffold a realtime eval folder; inputs, workflow, hard rules, learnings.
- openai-cookbook/examples/evaluation/Building_resilient_prompts_using_an_evaluation_flywheel.md — Eval flywheel (analyze/measure/improve); open+axial coding, graders, judge alignment TPR/TNR.
- openai-cookbook/examples/evaluation/Getting_Started_with_OpenAI_Evals.ipynb — OpenAI Evals framework basics; YAML eval, jsonl dataset, oaieval CLI, model-graded.
- openai-cookbook/examples/evaluation/use-cases/bulk-experimentation.ipynb — Hosted Evals API: test 9 prompt×model combos via label_model grader + completions run source.
- openai-cookbook/examples/evaluation/use-cases/completion-monitoring.ipynb — Grade stored production completions (store=True + metadata) by prompt_version to catch regressions.
- openai-cookbook/examples/evaluation/use-cases/mcp_eval_notebook.ipynb — Evals over MCP tool answers; LLM pass/fail grader + Python grader asserting tool use.
- openai-cookbook/examples/evaluation/use-cases/regression.ipynb — Detect prompt regression by comparing baseline vs broken-prompt eval runs.
- openai-cookbook/examples/evaluation/use-cases/responses-evaluation.ipynb — Eval a new model on stored Responses logs (data_source_config type "logs"); score_model grader.
- openai-cookbook/examples/evaluation/use-cases/tools-evaluation.ipynb — Eval tool/function-call structured extraction quality; score_model rubric over output_tools args.
- openai-cookbook/examples/evaluation/use-cases/web-search-evaluation.ipynb — Eval web_search_preview retrieval quality with custom QA dataset, pass/fail grader.
- openai-cookbook/examples/File_Search_Responses.ipynb — file_search hosted RAG tool over OpenAI vector store; retrieval eval (Recall/MRR/MAP).
- openai-cookbook/examples/gpt-5/codex_prompting_guide.ipynb — Codex (`gpt-5.3-codex`) harness/prompt guide: starter prompt, apply_patch, compaction, phase/preambles, parallel tools.

## PART B — PATTERN NOTES

### openai-cookbook/examples/codex/using_goals_in_codex.ipynb
- Pattern: long-running goal-directed agent loop — a persistent objective ("Goal") attached to a thread that keeps working across turns until an evidence-checked stop condition.
- Mechanism: slash commands `/goal <outcome>`, `/goal` (view), `/goal pause`, `/goal resume`, `/goal clear`. Available from Codex 0.128.0 (`npm i -g @openai/codex@latest`).
- Goal is **persisted thread-scoped state**, not global memory / not project instructions; records objective, lifecycle, budget, progress accounting.
- Lifecycle states: active, paused, complete, budget-limited. Model may only START a goal and MARK complete (with evidence); pause/resume/clear/budget transitions are user/system controlled.
- Continuation is event-driven at "safe boundaries": only when thread idle, no queued user input, no pending work. Plan-only turns don't trigger continuation; if a continuation turn makes no tool call, next auto-continuation is suppressed (anti-spin).
- Prompt=ask→work→result→wait; Goal=work→check→continue-or-complete. Completion must be evidence-based (files/tests/benchmarks/artifacts), not model's belief.
- A strong Goal defines six things: outcome, verification surface, constraints, boundaries (allowed files/tools/data), iteration policy, blocked-stop condition.
- Template: "<end state> verified by <evidence> while preserving <constraints>. Use <inputs/tools/boundaries>. Between iterations <choose next>. If blocked <report + what unlocks>."
- Budget limit ≠ completion: on budget exhaustion, stop substantive work, summarise progress/blockers, name next step.
- Case study: reproducing Buehler et al. "Deep Hedging" quant paper — goal decomposes claims into evidence channels (reproduced mechanics / approximate trained / blocked exact replay / remaining uncertainty); blocked by missing seeds, training paths, TF graph, optimizer state, checkpoints.
- Numbers: none reported.
- Caveats: not for one-line edits, vague finish lines ("make it better"), or to hide uncertainty; narrow enough to audit, broad enough to let model pick next action.
- QMX-fit: Lab copilot (long experiments), workflow/background agents (long-running autonomy). Also directly relevant to the quant-paper-reproduction use case.
- LangChain/DeepAgents mapping (inference): a StateGraph with a persistent goal field in state + checkpointer for durability; a conditional edge that loops only at idle boundaries; interrupt for pause; the "evidence audit before complete" is a grader node. No direct LangGraph primitive for budget — custom. (my inference)

### openai-cookbook/examples/Context_summarization_with_realtime_api.ipynb
- Pattern: voice agent (if-agentic) + context compaction/memory management on a stateful streaming session.
- Mechanism: WebSocket `wss://api.openai.com/v1/realtime?model=gpt-realtime`; session config via `session.update` (voice, `modalities:["audio","text"]`, `input_audio_format:"pcm16"`, `input_audio_transcription:{model:"gpt-4o-transcribe"}`).
- Audio pipeline: mic → `asyncio.Queue` → base64 → `input_audio_buffer.append` events; 24kHz mono PCM16, ~40ms chunks.
- Server events consumed: `session.created`, `session.updated`, `conversation.item.created`, `conversation.item.retrieved`, `response.audio.delta`, `response.done` (carries usage/token count), `conversation.item.deleted`.
- Compaction strategy: monitor `latest_tokens` from `response.done`; when ≥ `SUMMARY_TRIGGER` and history > `KEEP_LAST_TURNS`, summarise all but last turns into one paragraph via cheap model (`SUMMARY_MODEL="gpt-4o-mini"`, temperature 0), insert via `conversation.item.create` with `previous_item_id:"root"`, then delete old items with `conversation.item.delete`.
- Key implementation detail: insert summary as a **system** message, NOT assistant — assistant summaries caused the model to flip from audio to text output mid-conversation.
- New GA param `truncation` auto-optimises context truncation while maximizing cache hit rates (UNVERIFIED exact behaviour).
- Numbers: gpt-realtime 32k token window; audio ≈10× more tokens than same text; demo uses SUMMARY_TRIGGER=2000, KEEP_LAST_TURNS=2; production recommended 20,000–32,000 trigger.
- Caveats: instruction adherence drifts as context fills well before the 32k limit; transcripts may lag (retry `conversation.item.retrieve` up to 5×).
- Cited URLs: https://platform.openai.com/docs/guides/realtime ; /docs/guides/realtime-conversations ; /docs/api-reference/realtime ; https://voiceaiandvoiceagents.com/
- QMX-fit: general copilot voice mode (optional), long voice experiences; mechanism is the compaction pattern applicable to any long session.
- LangChain/DeepAgents mapping (inference): a summarization/trim middleware over message history; keep-last-N + summary-prepend is the classic `trim_messages` + summary node; Store for the summary. (my inference)

### openai-cookbook/examples/Custom-LLM-as-a-Judge.ipynb
- Pattern: evals/graders — LLM-as-judge for hallucination detection, iteratively improved and meta-evaluated.
- Mechanism: `braintrust.wrap_openai(AsyncOpenAI(...))`, `braintrust.login`, `@braintrust.traced`, `from braintrust import Eval`; grader returns score via forced function/tool call (`tool_choice={"type":"function","function":{"name":"rate"}}`).
- Three judge designs: (1) numeric 1–10 rater (normalise `(rating-1)/9`); (2) + chain-of-thought `reasons` field; (3) classifier into labeled choices A–E with `CHOICE_SCORES` mapping.
- Meta-eval: inject known hallucinations (confident fake answers), measure how often judge scores them 0; `normalized_diff = 1 - abs(output-expected)`.
- Codified via `autoevals.LLMClassifier(name, prompt_template, choice_scores, use_cot=True)`; dataset CoQA via DuckDB (`hf://datasets/stanfordnlp/coqa`).
- Numbers: numeric rater ≈94%; adding reasoning ~3% worse; **classifier 98%** (biggest win). Hallucinations generated with temperature=1, max_tokens=100.
- Caveats: numeric rating invites partial-credit drift for both models and humans; classification with explicit criteria is more reliable; public datasets may be memorised — test on private data; penalise superset (B) as much as disagreement (D) when testing hallucination.
- Cited URLs: https://www.braintrust.dev/ ; autoevals factuality.yaml on GitHub.
- QMX-fit: workflow/server (quality gates on any agent output), Lab (building evals).
- LangChain/DeepAgents mapping (inference): a grader sub-agent/tool; structured-output judge = `with_structured_output`; classification-over-rating is a reusable grading convention. (my inference)

### openai-cookbook/examples/deep_research_api/how_to_build_a_deep_research_mcp_server/README.md
- Pattern: research agent + MCP server (search/fetch) backed by a vector store.
- Mechanism: Deep Research relies on exactly two tools — **Search** (returns top-k object IDs) and **Fetch** (takes objectIds, returns resources). Server runs SSE transport at `http://0.0.0.0:8000/sse/`; expose via ngrok.
- Wired into Responses API as a tool: `{"type":"mcp","server_label":"internal_file_lookup","server_url":".../sse/","require_approval":"never"}` alongside `{"type":"web_search_preview"}`; model `o3-deep-research-2025-06-26`, `reasoning:{"summary":"auto"}`.
- System prompt instructs: don't re-fetch an already-retrieved file; include inline citations + source metadata.
- Numbers: none.
- Caveats: files must be vectorised in OpenAI Vector Storage first; untrusted-internet exposure if ngrok'd.
- Cited URLs: https://cookbook.openai.com/examples/deep_research_api/introduction_to_deep_research_api ; main.py on GitHub.
- QMX-fit: Lab copilot research; workflow/server research agents over QMX's own doc/corpus knowledge base.
- LangChain/DeepAgents mapping (inference): expose QMX corpus as MCP search/fetch tools; the two-tool contract maps cleanly to a retriever tool pair; DeepAgents research sub-agent consumes them. (my inference)

### openai-cookbook/examples/deep_research_api/introduction_to_deep_research_api.ipynb
- Pattern: single-call research agent via Responses API; planning/search/synthesis abstracted into one hosted model.
- Mechanism: `client.responses.create(model="o3-deep-research"| "o4-mini-deep-research-2025-06-26", input=[developer,user], reasoning={"summary":"auto"|"detailed"}, tools=[web_search_preview, code_interpreter{"container":{"type":"auto"}}, mcp], background=True)`.
- Intermediate steps exposed in `response.output` by `type`: `reasoning` (`.summary[].text`), `web_search_call` (`.action["query"]`, `.status`), `code_interpreter_call` (`.input`/`.output`), `mcp_call` (`.name`,`.server_label`,`.arguments`). Final report = `response.output[-1].content[0].text`.
- Citations: `annotations` with `title`, `url`, `start_index`, `end_index` for building bibliographies / clickable spans.
- API vs ChatGPT: API does NOT ask clarifying questions — expects fully-formed prompts. Recommended: (a) prompt-rewriter with lightweight model (`gpt-4.1-2025-04-14`) to expand query, and/or (b) clarifying-questions model first, then rewrite.
- Numbers: o3-deep-research = deeper/higher-quality; o4-mini = faster/latency-sensitive. Deep Research tasks take several minutes (use background mode to avoid timeouts).
- Caveats: broad/underspecified queries → verbosity, latency, token cost; don't use for trivial lookups.
- Cited URLs: the two rewriting/clarifying prompt texts (reusable); link to agents cookbook.
- QMX-fit: Lab copilot research; background/server research agents producing citation-rich reports.
- LangChain/DeepAgents mapping (inference): background=True ≈ long-running job on remote server; the rewriter/clarifier front-ends ≈ a preprocessing sub-agent or interrupt-for-clarification node. (my inference)

### openai-cookbook/examples/deep_research_api/introduction_to_deep_research_api_agents.ipynb
- Pattern: multi-agent research pipeline (triage → clarify → instruction → research) with handoffs, streaming, MCP; OpenAI Agents SDK.
- Mechanism: `from agents import Agent, Runner, WebSearchTool, RunConfig, set_default_openai_client, HostedMCPTool`. Agents declare `handoffs=[...]`; triage picks `transfer_to_*`. Clarifier uses `output_type=Clarifications` (pydantic structured output).
- Research agent: `Agent(model="gpt-5.6-sol", tools=[WebSearchTool(), HostedMCPTool(tool_config={"type":"mcp","server_label":"file_search","server_url":".../sse","require_approval":"never"})])`.
- Streaming: `Runner.run_streamed(agent, query)`, iterate `result_stream.stream_events()`; event types `agent_updated_stream_event`, `raw_response_event` (inspect `ev.data.item.action["type"]=="search"`).
- Interaction flow printing: iterate `stream.new_items`, item `.type` in {`handoff_call_item`, `handoff_output_item`, `mcp_list_tools_item`, `reasoning_item`, `tool_call_item`, `message_output_item`}. Citations via `url_citation` annotations.
- ZDR: `os.environ["OPENAI_AGENTS_DISABLE_TRACING"]="1"` disables tracing for Zero Data Retention orgs; `AsyncOpenAI(timeout=600.0)`.
- Sub-agent prompts (CLARIFYING_AGENT_PROMPT, RESEARCH_INSTRUCTION_AGENT_PROMPT) are reusable; instruction agent = `gpt-4o-mini`, clarifier = `gpt-4o-mini`.
- Numbers: install `openai>=1.88`, `openai-agents>=0.0.19`. Models fictional (gpt-5.6-sol/terra).
- Caveats: don't use Deep Research for trivial Q&A; disabling tracing loses eval/finetune integration.
- QMX-fit: Lab/general copilot multi-agent orchestration; workflow agents.
- LangChain/DeepAgents mapping (inference): Agents-SDK handoffs ≈ LangGraph multi-agent handoff / supervisor edges; `output_type` ≈ structured output; triage ≈ router node; HostedMCPTool ≈ MCP tool binding. (my inference)

### openai-cookbook/examples/Developing_hallucination_guardrails.ipynb
- Pattern: output guardrail + eval-set construction for a policy-following support agent (HITL-adjacent safety check).
- Mechanism: synthetic data gen with GPT-4o (policies → simulated interactions with `accurate` boolean, `kb_article`, `chat_history`, `assistant_response`); `n=10` sampling, `ThreadPoolExecutor` parallelism.
- Guardrail prompt scores EACH sentence on 4 binary dims: `factualAccuracy` (+ `factualReference` citation/rationale), `relevance`, `policyCompliance`, `contextualCoherence`; returns JSON array. Pass only if score_sum==4 for all sentences.
- Few-shot: embed clear pass/fail examples (fs_user_1/fs_assistant_1 ...) in the prompt.
- Evaluate guardrail itself with `precision_score`/`recall_score` (sklearn) against `accurate` ground truth.
- Guiding principles: descriptive measurable metrics, consistent terminology, start with strongest model then downgrade for cost (GPT-4o→gpt-3.5-turbo), evaluate per-sentence AND whole-response.
- Numbers: reported "high precision and recall" (no exact figure in extract).
- Caveats: "truth"/relevance hard to measure directly — decompose into concrete scores; terminology drift (assistant vs agent) confuses the model.
- Cited URLs: https://cookbook.openai.com/examples/how_to_use_guardrails ; sdg1 synthetic data cookbook.
- QMX-fit: Portfolio/workflow (policy/risk compliance checks on agent outputs), general copilot safety.
- LangChain/DeepAgents mapping (inference): post-model guardrail middleware; per-sentence scoring = a validator node that can trigger interrupt/retry. (my inference)

### openai-cookbook/examples/Enhance_your_prompts_with_meta_prompting.ipynb
- Pattern: meta-prompting / automated prompt optimization + LLM-as-judge eval.
- Mechanism: stronger reasoning model (`o1-preview`) rewrites a simple prompt into a detailed one ("Only return the prompt."); weaker model (`gpt-4o-mini`) runs the task; judge (`gpt-4o` via `client.beta.chat.completions.parse(response_format=ScoreCard)`) scores 1–5 across 5 criteria.
- ScoreCard pydantic: justification, categorization, keyword_extraction, sentiment_analysis, clarity_structure, detail_completeness.
- Data: `RealTimeData/bbc_news_alltime` (HF), sample 100; ThreadPoolExecutor concurrency.
- Numbers: improved prompt beat baseline on categorization, keywords/tags, sentiment, detail/completeness; baseline comparable only on clarity/structure.
- Caveats: "generate N examples" yields homogeneous data (tie-in to flywheel); meta-prompt the evaluation prompt too.
- Cited URLs: https://platform.openai.com/docs/guides/prompt-generation ; getting-started evals cookbook.
- QMX-fit: Lab copilot (prompt/workflow building), workflow agents self-improving prompts.
- LangChain/DeepAgents mapping (inference): offline optimizer step; no runtime graph equivalent — a build-time tool. (my inference)

### openai-cookbook/examples/evals/realtime_evals/README.md
- Pattern: tiered eval harnesses for a realtime/voice agent — crawl→walk→run.
- Mechanism: crawl = synthetic single-turn (TTS→stream→grade tool-call correctness); walk = deterministic replay of saved G.711 mu-law 8kHz phone audio (VAD off, fixed chunking); run = model-simulated multi-turn (simulator model generates user turns, assistant under test, mocked tool outputs, LLM-as-judge grading).
- CLI flags shared: `--data-csv`, `--results-dir`, `--run-name`, `--model`, `--system-prompt-file`, `--tools-file`, `--chunk-ms`, `--sample-rate-hz`, `--real-time`, `--max-examples`, `--skip-plots`.
- Outputs per run: `results.csv`, `summary.json`, `plots/*.png`, `events/*.jsonl`; shared typed artifacts in `shared/result_types.py`; Streamlit results viewer (comparison + run viewer). Python 3.12+, uv or venv.
- Numbers: none.
- Caveats: realism vs reproducibility tradeoff; walk needs ffmpeg.
- QMX-fit: workflow/server (eval infra for any agent); only if QMX adds voice.
- LangChain/DeepAgents mapping (inference): harness is external test infra, not a graph; the simulator-model-vs-model pattern maps to a two-agent eval graph. (my inference)

### openai-cookbook/examples/evals/realtime_evals/skills/bootstrap-realtime-eval/references/harness-selection.md
- Pattern: decision table + data contracts for harness choice (supports the SKILL).
- Mechanism/data contracts: crawl needs `example_id`,`user_text` (+ optional `gt_tool_call`,`gt_tool_call_arg`); walk adds `audio_path`; run needs index `simulation_id`,`simulation_path` and per-sim JSON (assistant config, simulator prompt, audio config, turn config, tool mocks, grader config).
- Rules: default crawl for text/rough tasks; crawl for synthetic audio unless replay-specific traits (noise/telephony/speaker) → walk; run only when target depends on multi-turn/tool outputs/conversation-level completion.
- README must explain why harness chosen, files to edit first, smoke+full commands, data shape, OPENAI_API_KEY/ffmpeg troubleshooting.
- QMX-fit: workflow/server eval tooling (pattern of documented decision tables for agent config).
- LangChain/DeepAgents mapping: no direct equivalent (doc/skill artifact). (my inference)

### openai-cookbook/examples/evals/realtime_evals/skills/bootstrap-realtime-eval/SKILL.md
- Pattern: an Agent Skill (SKILL.md with name/description frontmatter) that scaffolds eval folders — a concrete skills example.
- Mechanism: collect inputs first (eval name, goal, harness, system prompt, tools JSON, data, graders); run `scripts/bootstrap_realtime_eval.py --name --harness`; don't duplicate harness code (point at shared harnesses); author realistic starter data (crawl 3 rows, walk 3 rows+audio step, run 2 sims).
- Validation gate: smoke eval → if green auto-run full eval → `pytest examples/evals/realtime_evals/tests -q`.
- "Learnings" section accrues reusable constraints (Problem→Fix→Why), e.g. `gpt-realtime` temperature unsupported; starter samples from model not script; smoke-only leaves scaffolds half-proven.
- Hard rules: ask before scaffolding; no generic placeholder data; use `--assistant-system-prompt-file`/`--assistant-tools-file` for run harness.
- QMX-fit: Lab copilot (building skills / mini-apps), general copilot that authors skills.
- LangChain/DeepAgents mapping (inference): this is the "skills" concept directly — a progressive-disclosure instruction file + references + scripts; maps to DeepAgents skill files / a tool that scaffolds. (my inference)

### openai-cookbook/examples/evaluation/Building_resilient_prompts_using_an_evaluation_flywheel.md
- Pattern: eval methodology — the "evaluation flywheel" (Analyze→Measure→Improve), error analysis, judge alignment.
- Mechanism: open coding (read ~50 failing traces, descriptive labels via Feedback annotation column `open_coding`) → axial coding (group into categories, Label column `axial_coding`) → automatic graders (Python + LLM) run in bulk → prompt optimizer tool uses outputs+annotations+graders to propose improved prompt; graders/annotations preserved across tabs for comparison.
- Judge alignment: measure against SME gold set; imbalanced sets make accuracy misleading — use TPR (catch failures) and TNR (catch passes); split Train ~20% (few-shot), Validation ~40% (tune), Test ~40% (held-out report card).
- Synthetic data: define dimensions (Channel/Intent/Persona), generate tuples for coverage; add perturbations (irrelevant info, mistakes, slang).
- Numbers: example "35% failures tour scheduling, 10% formatting".
- Cited URLs: hamel.dev/blog/posts/evals-faq ; .../llm-judge ; platform.openai.com/docs/guides/graders ; /prompt-optimizer ; youtu.be/qH1dZ8JLLdU.
- QMX-fit: workflow/server (continuous eval of QMX agents), Lab (eval building). Integrate graders into CI/CD.
- LangChain/DeepAgents mapping (inference): process, not graph; graders map to LangSmith evaluators; flywheel is the ops loop around any agent. (my inference)

### openai-cookbook/examples/evaluation/Getting_Started_with_OpenAI_Evals.ipynb
- Pattern: foundational evals framework (older open-source `openai/evals`, now superseded by hosted Evals API — notebook says use hosted).
- Mechanism: eval = jsonl dataset + YAML class; dataset format `{"input":[{role,content}...],"ideal":"answer"}`; metrics match/includes/fuzzyMatch; model-graded via `evals.elsuite.modelgraded.classify:ModelBasedClassify` with `eval_type: cot_classify`.
- CLIs: `oaieval <model> <eval>` (single), `oaievalset` (set); logs at `/tmp/evallogs/*.jsonl` (spec, sampling, metrics, final_report entries).
- Two eval types: code logic checking (string match, JSON parse) vs model grading (two-stage: answer then judge, prefer a different model to grade, e.g. GPT-4 grades GPT-3.5).
- Synthetic SQL data gen with `n=5` completions; Spider Text-to-SQL example.
- Caveats: model grading has error rate — validate against humans before scaling; minor syntax diffs cause false negatives (argues for model-graded).
- Cited URLs: github.com/openai/evals ; platform.openai.com/docs/guides/evals.
- QMX-fit: workflow/server eval infra.
- LangChain/DeepAgents mapping: external test harness; no graph equivalent. (my inference)

### openai-cookbook/examples/evaluation/use-cases/bulk-experimentation.ipynb
- Pattern: hosted Evals API — bulk test many prompt×model variants.
- Mechanism: Eval = `data_source_config` + `testing_criteria`; `has_many` Runs. `data_source_config={"type":"custom","item_schema":Model.model_json_schema(),"include_sample_schema":True}` exposes `{{item.*}}` and `{{sample.output_text}}`.
- Grader: `{"type":"label_model","model":"o3-mini","input":[dev,user],"passing_labels":[...],"labels":[...]}` — uses structured outputs so labels always valid.
- Run data source `{"type":"completions","input_messages":{"type":"template","template":[...]},"model":..., "source":{"type":"file_content","content":[{"item":...}]}}`; OpenAI makes completions and fills `sample.output_text`. Each run has `report_url`.
- Tested 3 prompts (basic / with positive examples / with pos+neg examples) × 3 models (gpt-4o, gpt-4o-mini, o3-mini) = 9 runs.
- QMX-fit: Lab (experimentation), workflow (model/prompt selection for background agents).
- LangChain/DeepAgents mapping (inference): offline experimentation; grader = evaluator. (my inference)

### openai-cookbook/examples/evaluation/use-cases/completion-monitoring.ipynb
- Pattern: production monitoring / regression detection over stored completions.
- Mechanism: log with `store=True, metadata={"prompt_version":..,"usecase":..}`; `client.chat.completions.list()`; eval `data_source_config={"type":"stored_completions","metadata":{...}}` → vars `{{item.input}}`,`{{sample.output_text}}`.
- Runs filter by metadata: `data_source={"type":"completions","source":{"type":"stored_completions","metadata":{"prompt_version":"v1"}}}`; to re-run on a new model use `input_messages:{"type":"item_reference","item_reference":"item.input"}`,`"model":"gpt-4o"`.
- Finds a planted v2 regression (longer-than-needed summaries).
- Caveats: needs logging enabled (admin data-retention panel); not ZDR-compatible.
- QMX-fit: workflow/server monitoring of background agents.
- LangChain/DeepAgents mapping (inference): LangSmith trace logging + offline eval over stored runs. (my inference)

### openai-cookbook/examples/evaluation/use-cases/mcp_eval_notebook.ipynb
- Pattern: evaluate MCP-tool-using answers + assert tool actually used.
- Mechanism: two graders — (1) `label_model` pass/fail LLM grader; (2) **python grader** `{"type":"python","image_tag":"2025-05-08","pass_threshold":1.0,"source":"def grade(sample,item): return 1.0 if len(sample.get('output_tools',[]))>0 else 0.0"}`.
- Run data source `{"type":"responses",...,"sampling_params":{"seed":42,"max_completions_tokens":10000,"tools":[{"type":"mcp","server_label":"gitmcp","server_url":"https://gitmcp.io/openai/tiktoken","allowed_tools":[...],"require_approval":"never"}]}}`.
- Poll `client.evals.runs.retrieve(rid,eval_id)` on `.status`/`.result_counts`.
- Findings: gpt-4.1 told "never use tools" → never called MCP, scored worse; o4-mini not forbidden → called MCP 3×, better; its only failure was the one where MCP wasn't used. Adding "Always use your tools" made o4-mini call MCP every time and get all correct.
- QMX-fit: workflow/server (verify tool-use behaviour of agents), Lab.
- LangChain/DeepAgents mapping (inference): Python grader asserting `output_tools` ≈ a trajectory/tool-call assertion in LangSmith. (my inference)

### openai-cookbook/examples/evaluation/use-cases/regression.ipynb
- Pattern: prompt-regression gate (baseline vs changed run).
- Mechanism: same Evals API shape as bulk-experimentation; run source `{"type":"jsonl","source":{"type":"file_content","content":[{"item":..,"sample":completion.model_dump()}]}}`. label_model grader `o3-mini`, passing_labels ["correct"].
- Responses→completions shim: build `{"model":..,"choices":[{"index":0,"message":{"role":"assistant","content":response.output_text},"finish_reason":"stop"}]}` because Evals didn't natively accept Responses then (UNVERIFIED current).
- QMX-fit: workflow/server CI gate.
- LangChain/DeepAgents mapping: offline eval; no graph. (my inference)

### openai-cookbook/examples/evaluation/use-cases/responses-evaluation.ipynb
- Pattern: evaluate a new model on existing stored Responses logs (zero extra eval-building).
- Mechanism: `data_source_config={"type":"logs"}`; grader `{"type":"score_model","model":"o3","range":[1,7],"pass_threshold":5.5}` with a detailed weighted rubric (Correctness 45% / Completeness 25% / Clarity 20% / Insight 10%) returning JSON `{steps:[{description,result}],result:"float-as-string"}`.
- Baseline run: `data_source={"type":"responses","source":{"type":"responses","limit":N}}`; new-model run adds `input_messages:{"type":"item_reference","item_reference":"item.input"},"model":"gpt-4.1-mini"`.
- Caveats: requires data logging enabled (not ZDR); compares gpt-4o-mini vs gpt-4.1-mini on code explanation.
- QMX-fit: workflow/server (model migration testing on real traffic).
- LangChain/DeepAgents mapping (inference): score_model weighted rubric = a scalar LLM evaluator over logged traces. (my inference)

### openai-cookbook/examples/evaluation/use-cases/tools-evaluation.ipynb
- Pattern: evaluate structured extraction via tool/function calls; compare Completions vs Responses endpoints.
- Mechanism: grader `score_model` o3, range[1,7], pass_threshold 5.0; grader reads `{{sample.output_tools[0].function.arguments.symbols}}`; rubric = completeness(1–7) × quality-modifier(0–1).
- Tool schema `extract_symbols` (array of {name, symbol_type}, additionalProperties False). Runs pass `tools:[{"type":"function","function":symbol_tool}]` in `sampling_params` (seed 42, temp 0.7, top_p 0.9, max_completions_tokens 10000).
- Extract results from `item.sample.output[0].tool_calls[0]["function"]["arguments"]`; can compute precision/recall vs reference.
- QMX-fit: Lab/Portfolio/workflow — directly relevant to grading tool-calling agents (e.g., sizing/optimisation tool args).
- LangChain/DeepAgents mapping (inference): grade on tool args = structured-output / tool-call evaluator. (my inference)

### openai-cookbook/examples/evaluation/use-cases/web-search-evaluation.ipynb
- Pattern: evaluate `web_search_preview` retrieval quality with custom QA set.
- Mechanism: label_model grader o3, passing_labels ["pass"]; responses run with `tools:[{"type":"web_search_preview"}]`, template messages referencing `{{item.query}}`; compare gpt-4.1 vs gpt-4.1-mini; poll runs; display outputs side-by-side.
- QMX-fit: Lab/workflow (news/web research quality — note QMX uses free news sources only per project memory).
- LangChain/DeepAgents mapping (inference): search tool + pass/fail evaluator. (my inference)

### openai-cookbook/examples/File_Search_Responses.ipynb
- Pattern: hosted RAG — `file_search` tool over an OpenAI vector store; plus retrieval-quality eval.
- Mechanism: `client.vector_stores.create`, `client.files.create(purpose="assistants")`, `client.vector_stores.files.create`; standalone `client.vector_stores.search(vector_store_id, query)` returns hybrid-ranked results with `.score`,`.filename`,`.content`.
- In-LLM: `client.responses.create(input=query, model="gpt-4o-mini", tools=[{"type":"file_search","vector_store_ids":[id],"max_num_results":k}], tool_choice="required")`; annotations at `response.output[1].content[0].annotations`; add `include=["output[*].file_search_call.search_results"]` to inspect chunks.
- Eval: generate one question per PDF (ground truth doc), measure Recall@k, Precision@k, MRR, MAP (k=5).
- Caveats: auto-generated questions can be generic → unfair retrieval scoring; recommend human-verified eval set.
- Cited URLs: platform.openai.com/docs/api-reference/vector-stores/search.
- QMX-fit: Lab/general copilot (RAG over QMX docs/GitBook corpus); workflow research agents.
- LangChain/DeepAgents mapping (inference): file_search ≈ a retriever tool / VectorStore; `tool_choice="required"` ≈ forcing a retrieval node; metrics are offline retrieval eval. (my inference)

### openai-cookbook/examples/gpt-5/codex_prompting_guide.ipynb
- Pattern: coding-agent harness/prompt engineering — the most QMX-factory-relevant file. Agent loop shape, tools, compaction, parallel tool calls, preambles.
- Model: `gpt-5.3-codex` (also `gpt-5.1-Codex-Max`); recommend "medium" reasoning for interactive, `high`/`xhigh` for hardest/long autonomous tasks; "much better in PowerShell and Windows environments."
- Starter prompt sections (reusable, battle-tested): General, Autonomy and Persistence, Code Implementation, Editing constraints, Exploration/reading files, Plan tool, Special user requests, Frontend tasks, Presenting work/final message.
- Tool-use directives: prefer dedicated tools over raw shell (`read_file` over `cat`, `rg` over grep); `git`/`rg`/`read_file`/`list_dir`/`glob_file_search`/`apply_patch`/`todo_write/update_plan`. Parallelize via `multi_tool_use.parallel` only. For evals: turn up autonomy / "non-interactive" mode; REMOVE prompting for upfront plan/preambles/status (causes early stop).
- apply_patch: first-class Responses tool `{"type":"apply_patch"}` → returns `apply_patch_call` item with `.operation` ({diff, path, type:"update_file"}); OR freeform custom tool with Lark context-free grammar (`"format":{"type":"grammar","syntax":"lark","definition":...}`) → `custom_tool_call`. `parallel_tool_calls=False` used in examples.
- shell tool: command as a single **string** performs better than a list; params command/workdir/timeout_ms/with_escalated_permissions/justification; PowerShell variant wraps `["pwsh","-NoLogo","-NoProfile","-Command","<cmd>"]`, always set workdir, avoid `cd`.
- update_plan tool: plan items {step,status(pending/in_progress/completed)}, at most one in_progress.
- Compaction: `/compact` endpoint (`/responses/compact`), ZDR-compatible, returns `encrypted_content` item to pass into future requests; enables multi-hour reasoning beyond context limits; superior to ad-hoc summarization.
- AGENTS.md: auto-enumerated from `~/.codex` plus repo-root→CWD, merged later-overrides-earlier, each injected as its own user-role message `# AGENTS.md instructions for <dir>` near top of history.
- GPT-5.3 new: `phase` param on assistant output items (`null`/`"commentary"`/`"final_answer"`) — MUST persist and pass back assistant items incl. phase or "significant performance degradation"; only on assistant items, never user messages.
- Preambles/personality: acknowledge+plan before tool calls (1 sentence + 1–2 sentence plan); updates 1–2 sentences; cadence every 1–3 steps, hard floor every 6 steps / 10 tool calls; two personalities Friendly vs Pragmatic (example prompt snippets given).
- Tool response truncation: limit ~10k tokens (`num_bytes/4`); keep half head/half tail, middle `…N tokens truncated…`.
- Custom tool advice: semantically correct names (`semantic_search` not `search`), explicit when/why/how + good/bad examples, make outputs visually distinct to avoid habit collapse.
- Metaprompting: ask the model at end of a weak turn to rewrite its own instructions for speed/quality; run several times, keep common suggestions, build an eval to measure.
- Failure modes tracked: overthinking/slow first action, loggy status updates, awkward preamble tics ("Good catch","Aha").
- Cited URLs: github.com/openai/codex ; codex-rs gpt-5.1-codex-max_prompt.md ; developers.openai.com/codex/sdk ; apply_patch.py cookbook/agents-python examples.
- QMX-fit: workflow/server (the factory coding lanes), general copilot (Codex/Claude-Code-style app with real terminal — matches QMX memory note).
- LangChain/DeepAgents mapping (inference): starter-prompt sections ≈ system prompt + middleware policies; apply_patch/shell/update_plan ≈ agent tools; compaction ≈ summarization middleware/checkpointer; AGENTS.md injection ≈ loading project context into state; phase ≈ message metadata that must survive checkpointing. (my inference)
