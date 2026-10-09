# Cookbooks, loop engineering and graph engineering, read for the QMX Copilot

Scope: worked examples, not vendor advice pages. Read in full: nine LangChain posts and the Open Deep Research repo
(README, `configuration.py`, `deep_researcher.py`, `state.py`); about 30 Anthropic cookbook notebooks and 20 OpenAI
cookbook notebooks (markdown cells read, code cells skimmed); the current Claude and GPT-6 prompting pages; and the primary
loop and graph engineering write-ups. This file does not repeat `harness-practices.md` §8 or the two paper syntheses. It
adds to them and, in §6, corrects them. Stack assumed: Python, LangChain v1 + LangGraph + Deep Agents, Claude Opus 5.5 as
the main model, GPT-6.1 Sol for sub-agents, everything routed through CLIProxyAPI.

Tags: **VERIFIED** means I read it in the source. **UNVERIFIED** means it has to be checked against installed versions or
CLIProxyAPI behaviour before anyone codes against it.

---

## 1. LangChain posts: what each shows, the mechanism, and what QMX should do

### 1.1 How to Build a Model Router in the Harness (2026-10-01)
https://www.langchain.com/blog/how-to-build-a-model-router-in-the-harness
- **Shows.** Open SWE routed threads across three tiers: fast GLM-5.3-Flash, balanced GPT-5.6 Sol, performance GPT-6 Astra.
  - Over 973 A/B threads, median cost fell 64% ($0.94 vs $2.61), mean cost fell 42% and p90 fell 37%.
  - Merged-PR rate showed no measurable change (29.2% vs 27.3%, p = 0.49).
  - Routing split: 56% balanced, 34% fast, 10% performance.
  - A fast-only control arm was stopped within a day because quality was too low.
- **Mechanism.**
  - Middleware does dynamic model selection on the **first human message**, and that model stays for the whole thread.
  - The router has three parts: a base prompt ("cheapest model likely to complete"), criteria per tier, and a
    structured-output classifier. The criteria come from trace analysis plus each vendor's model guide.
  - Outcomes are tracked as merged PRs plus thumbs feedback.
  - Mid-thread re-routing is left open, because switching models discards the cache. Sub-agents are not routed yet.
- **QMX should…**
  - Keep the main thread on Opus 5.5. Switching mid-thread would cost both the prompt cache and the thinking-block chain
    (§5).
  - Tier only sub-agent and workflow-node models, chosen at spawn time with criteria taken from QMX traces: Luna for
    tagging and extraction, Sol by default, Opus for judgment calls.
  - Define the outcome metric first: artefact accepted, re-run requested, thumbs.

### 1.2 How we built LangChain's agent-first data stack (2026-07-27)
https://www.langchain.com/blog/agent-data-stack
- **Shows.** A data agent now handles about 40x the requests the three-person data team could answer.
  - Reliability came from **context layers, not table access**:
    - dbt column definitions with allowed values and default filters; a semantic model holding metric definitions; Git-synced "workspace guides", which work like skills; **endorsements**, a trust flag that only the data team can set; the dbt repo, which gives lineage.
  - An observability loop turns conversation gaps into fixes in those layers.
- **Mechanism.** None at the API level. The post describes a context architecture.
- **QMX should…** Build a **quant data catalogue** that the Copilot reads before it writes analysis code:
  - dataset cards stating grain, timezone, adjustments, survivorship and lookahead caveats, and default filters;
  - a metric registry with one canonical definition each for Sharpe, drawdown, USD PnL and fees;
  - an operator-only "endorsed" flag on datasets, strategies and backtest configs.
  Mine Copilot traces for catalogue gaps. Everything in the catalogue is UI-editable.

### 1.3 Introducing Dynamic Subagents in Deep Agents (2026-06-29)
https://www.langchain.com/blog/introducing-dynamic-subagents-in-deep-agents
- **Shows.** The agent writes a JavaScript orchestration script instead of turn-by-turn `task` calls.
  - Code guarantees **coverage**, so the "screening 75 of 500 items and calling it done" failure goes away.
  - Six patterns: classify-and-act, fan-out/synthesize, adversarial verification, generate/filter, tournament, and
    loop-until-done.
- **Mechanism.**
  - Install `pip install "deepagents[quickjs]"`, then pass `create_deep_agent(..., middleware=[CodeInterpreterMiddleware()])`.
  - The interpreter's `task({description, subagentType, responseSchema})` returns a typed object.
  - Users trigger it by asking for a "workflow".
  - Interpreter limits (https://docs.langchain.com/oss/python/deepagents/interpreters): heap 64 MB, `timeout` 5 s per
    `eval`, `max_result_chars` 4000, `max_ptc_calls` 256.
  - There is no filesystem, network or clock unless granted. Tools are opt-in with `CodeInterpreterMiddleware(ptc=[...])`.
- **QMX should…**
  - Use it as the fan-out primitive for research sweeps: per symbol, per strategy, per news item, and claim verification.
  - List only read tools in `ptc=`, and require a `responseSchema` on every dispatch.
  - **UNVERIFIED:** whether the 5 s `eval` timeout cuts off long awaited `task()` calls.

### 1.4 How to Use RLMs in Deep Agents (2026-07-01)
https://www.langchain.com/blog/how-to-use-rlms-in-deep-agents
- **Shows.** Deep Agents ships "recursive agents": sub-agents that have tools and are dispatched from code.
  - This is milder than the paper's plain-LM recursion over a prompt held in a REPL.
  - OOLONG/AgNews proof of concept: 0.58 vs 0.67 at 64k tokens; 0.44 vs 0.79 at 128k.
  - At 128k the plain agent "gives up outright". The REPL agent is slower and costs more because of output tokens.
- **Mechanism.** The same interpreter. Orchestrator and workers can run on different models.
- **QMX should…** Treat this as the blueprint §7 recursive path, which is now built in (§6). Keep the gating rule:
  dense semantic aggregation, async, budget-capped. The canonical QMX case is labelling every headline across a
  backtest window, then aggregating.

### 1.5 Introducing Rubrics (2026-06-02)
https://www.langchain.com/blog/introducing-rubrics-for-deepagents
- **Shows.** `RubricMiddleware(model, system_prompt, tools=[...], max_iterations=5)`.
  - The rubric is passed **at invoke time** (`{"messages":…, "rubric":"- …"}`). With no rubric, the middleware does
    nothing.
  - A separate grader sub-agent returns a verdict per criterion.
  - The loop ends on `satisfied`, `max_iterations_reached`, `failed` or `grader_error`. The API is beta.
- **QMX should…** Treat rubrics as per-deliverable data, supplied by the backtest-report and strategy-review skills.
  - Give the grader evidence tools; write rubrics with the rules in §2 row 3; treat `grader_error` as not accepted.

### 1.6 Interpreter Skills (2026-05-29)
https://www.langchain.com/blog/interpreter-skills
- **Shows.** A skill can ship a TypeScript module (`metadata.module: ./index.ts`).
  - The agent loads it with `await import("@/skills/x")`. The module can spawn sub-agents (`tools.task`) and return
    structured data plus `toMarkdown()`.
  - The stated aim is "discretion on the outside, determinism on the inside".
  - Evals become concrete: was the expected function called with the expected inputs?
- **Caveat.** The module runs as JS/TS in QuickJS, while QMX tooling is Python.
- **QMX should…** Take the idea, not the runtime.
  - A **workflow skill** is a `SKILL.md` that names a compiled LangGraph workflow. The Copilot invokes it through
    `run_workflow(name, inputs)`.
  - Node-editor workflows become skills automatically, with the description generated from workflow metadata.
  - Keep TypeScript modules for pure data helpers only.

### 1.7 Tuning Deep Agents to Work Well with Different Models (2026-04-29)
https://www.langchain.com/blog/tuning-deep-agents-different-models
- **Shows.** Per-model harness profiles raised tau2-bench subset scores: GPT-5.3 Codex 33→53%, Opus 4.7 43→53%.
  - The harness matters on its own: Claude Code ranked last among Opus 4.6 entries on Terminal-Bench 2.0.
  - The Codex profile used `apply_patch` instead of `edit_file`, an `execute`→`shell_command` alias, and a "batch all
    reads in parallel" instruction.
  - The Opus profile was prompt-only: `<tool_result_reflection>` and `<tool_usage>` ("observe state directly… Run tests
    before claiming they pass").
- **Mechanism** (https://docs.langchain.com/oss/python/deepagents/profiles, VERIFIED):
  - `HarnessProfile` fields: `base_system_prompt`, `system_prompt_suffix`, `tool_description_overrides`,
    `excluded_tools`, `excluded_middleware`, `extra_middleware`, `general_purpose_subagent`.
  - `ProviderProfile` fields: `init_kwargs`, `pre_init`, `init_kwargs_factory`.
  - Keys are `"provider"` or `"provider:model"` and are merged. Profiles can load from YAML or ship as a plugin.
- **QMX should…** Follow §5.
  - **UNVERIFIED:** whether a model *instance* such as `ChatOpenAI(base_url=CLIPROXY)` resolves to the
    `openai:gpt-6.1-sol` key.
  - The preferred route is the string `"openai:gpt-6.1-sol"` plus
    `register_provider_profile("openai", ProviderProfile(init_kwargs={"base_url": CLIPROXY_URL}))`.

### 1.8 Agent Middleware (2025-09-08)
https://www.langchain.com/blog/agent-middleware
- **Shows.** The design rationale. The loop is a model node plus a tools node. Middleware wraps it like web-server
  middleware: in order going in, reversed coming out. Middleware can add state schema and tools, and it replaced the
  separate supervisor, swarm, bigtool and reflection agents.
- **QMX should…** Treat the middleware list as **the loop specification** (§3.3). Guards go outermost; retries and
  caching go next to the call.

### 1.9 Open Deep Research (2025-07-16) and its repo
https://www.langchain.com/blog/open-deep-research · https://github.com/langchain-ai/open_deep_research
- **Shows.** Read the code for the details.
  - **Scope:** `clarify_with_user` asks once, then `write_research_brief` produces the brief, which serves as the
    "north star".
  - **Research:** a supervisor subgraph with tools `ConductResearch`, `ResearchComplete` and `think_tool`. Researcher
    subgraphs run in parallel via `asyncio.gather`, and each ends in `compress_research` (cleaned, cited findings).
  - **Write:** the report is written one-shot. Parallel section writing was dropped because it produced disjointed
    reports.
- **Caps** (all configurable):
  - `max_concurrent_research_units=5`, `max_researcher_iterations=6`, `max_react_tool_calls=10`,
    `max_structured_output_retries=3`.
  - Overflow calls get an error tool message: "retry with ≤5".
  - When compression hits a token limit, it drops messages up to the last AI message.
  - An `override_reducer` lets a list be either appended to or replaced.
- **Lessons.**
  - Use multi-agent only for parallelizable research.
  - Sub-agents isolate sub-topic context. A single agent spreads itself thinner across sub-topics.
  - The supervisor tunes research depth. Research costs about 15x the tokens of chat.
  - LangChain and GPT Researcher later moved generic deep research from fixed graphs to an agent harness (§4.1).
- **QMX should…** Shape the quant-research skill the same way: brief → Opus supervisor → ≤5 Sol researchers →
  compressed, cited findings → one-shot report.
  - Use the caps above as UI-editable defaults.
  - Keep raw notes in files for audit.

---

## 2. Cookbook pattern catalogue

Anthropic = https://github.com/anthropics/claude-cookbooks (paths relative to it). OpenAI = https://github.com/openai/openai-cookbook/tree/main/examples.

| # | Pattern | Source | What it does (concrete shape) | QMX use |
|---|---|---|---|---|
| 1 | Dynamic workflow (script-held plan) | Anthropic `claude_agent_sdk/08_Dynamic_workflows.ipynb` | Claude writes a JS script for the `Workflow` tool. `agent(prompt,{schema,model,phase})`, `parallel()` (barrier), `pipeline(items, stages)` (per-item streaming), plain JS between calls. Up to 16 concurrent, 1000 agents per run. Resumable; completed agents return cached results. Script saved as a file that can be re-run. Plan held in code. | The "who holds the plan?" table decides the tier: single agent → sub-agents → workflow. Saved scripts become reusable QMX workflows |
| 2 | Fan-out + adversarial verification | same; LangChain dynamic sub-agents | Extract claims → one verifier per claim in a clean context → skeptic challenges each verdict → compile. Caught "one of the fastest-growing" vs "the fastest-growing" | Verify research reports and strategy memos claim by claim against data and sources |
| 3 | Outcome grader with rubric | Anthropic `managed_agents/CMA_verify_with_outcome_grader.ipynb` | Writer gets a *description*; an independent grader gets a *rubric*, a fresh context and the same tools. `max_iterations` defaults to 3 (max 20). Rubric rules: each criterion checkable; the grader must **earn** `satisfied` with evidence (fetched page, `file:line`); describe the goal, not steps; anticipate shortcuts ("no mirrors"); mandated feedback format (scoreboard + one bullet per failure); a no-fire list. Description and rubric must agree or the loop returns `failed` | Rubric template for QMX `RubricMiddleware` deliverables. Build first rubrics by analysing a known-good artefact |
| 4 | Session budget | Anthropic `managed_agents/CMA_cap_session_spend.ipynb` | `budget={"type":"limit","max_list_cost":{"currency":"USD","amount":"1000"}}` (minor units, string). `budget_reached` is a **pause**, not a failure. Checked between model requests, so expect one request of overshoot. Raise to resume. Create-only; removal is one-way | Per-run USD caps on Copilot jobs and workflows, shown in UI; cap pauses and asks the operator |
| 5 | Plan big, execute small | Anthropic `managed_agents/CMA_plan_big_execute_small.ipynb` | Frontier coordinator with **no tools**; cheap workers with web tools only. 84-98% of input tokens billed at the worker rate. Caveats: compare at matched rigor; delegation has a floor cost (narrower briefs cost more); the coordinator knows workers only from its own prompt; verify the decomposition premise too | Opus main + Sol researchers. Describe Sol workers inside the Opus prompt or skill; tune brief granularity |
| 6 | Advisor consult | Anthropic `managed_agents/CMA_consult_an_advisor.ipynb` | A mid-tier worker gets an `advisor` tool (no input; the advisor reads the whole conversation). The system prompt sets the consultation policy. Each consult is a metered thread | Option for Sol sub-agents on hard calls ("consult lead"), instead of routing whole tasks to Opus |
| 7 | HITL via custom tools | Anthropic `managed_agents/CMA_gate_human_in_the_loop.ipynb` | `decide()` for clear cases and `escalate()` for ambiguous ones; both round-trip through the app; webhook on idle in production | Money-path: `propose_order` = escalate shape; calibrate so the Copilot neither escalates everything nor nothing |
| 8 | Prompt versioning and rollback | Anthropic `managed_agents/CMA_prompt_versioning_and_rollback.ipynb` | Every update = new version; production **pins** a version; the pin is the reviewed gate; canary a slice; score each version on a labelled set | Matches tier-3 policy: `HarnessProfile`, prompt and skills pinned per thread, promotion via eval |
| 9 | Per-user memory store | Anthropic `managed_agents/CMA_remember_user_preferences.ipynb` | Memory as a mounted directory of files; app can seed, audit and edit; one RW per-user store plus RO shared stores; store description injected into prompt | "What QMX knows about you" page = Markdown export of the memory store |
| 10 | Compaction vs clearing vs memory | Anthropic `tool_use/context_engineering/context_engineering_tools.ipynb` | Compaction `compact_20260112` (trigger default 150K, custom `instructions` *replace* the default prompt). Clearing `clear_tool_uses_20250919` (`keep`, `clear_at_least`, `exclude_tools`; **invalidates cache**). Memory tool `memory_20250818`. Workload table: re-fetchable bulky results → clearing; dialogue → compaction; cross-session → memory; non-refetchable results → compaction over clearing. Exclude `memory` from clearing | Decide per QMX workload. Backtest outputs are re-fetchable (clear); operator dialogue → compaction; strategy lessons → memory |
| 11 | Instant (background) compaction | Anthropic `misc/session_memory_compaction.ipynb` | Build session memory proactively past a soft threshold in a background thread, so the hard limit swaps instantly (traditional compaction took 40 s); cache the background calls | Operator never waits on compaction; precompute the summary at about 60-70% |
| 12 | SDK compaction for queue processing | Anthropic `tool_use/automatic-context-compaction.ipynb` | `compaction_control`: threshold → summary prompt → `<summary>` → history cleared → continue. Demo: a 20-30 ticket queue | Long batch jobs (labelling 500 news items) when not using dynamic sub-agents |
| 13 | Memory tool + context editing | Anthropic `tool_use/memory_cookbook.ipynb` | Client-side `/memories` handler (view/create/str_replace/insert/delete/rename); auto-injected "check memory first, assume interruption"; topical write guidance; keep folder organized; path-traversal checks | Tier-2 memory implementation detail (paths, hygiene) |
| 14 | Programmatic tool calling | Anthropic `tool_use/programmatic_tool_calling_ptc.ipynb`; OpenAI GPT-6 guide | `allowed_callers=["direct","code_execution_20250825"]`; the `caller` field tells which path ran; only safe-to-repeat tools opt in. OpenAI: use PTC for filter/join/rank/aggregate; **not** when one call suffices, each result changes the next decision, approval is needed, or citations must be kept | Code-over-data for prices and fills: tools opt in; order tools never |
| 15 | Tool search, deferred | Anthropic `tool_use/tool_search_with_embeddings.ipynb`, `tool_search_alternate_approaches.ipynb` | Embedding search over tool text, or names listed in system + `describe_tool` → `tool_reference` with **`defer_loading=True` so the cached prefix survives** | Long-tail QMX tools behind search; never append to `tools` mid-thread (§5) |
| 16 | Prompt caching | Anthropic `misc/prompt_caching.ipynb`; OpenAI `Prompt_Caching_201.ipynb` | Anthropic: top-level automatic `cache_control` moves the breakpoint forward each turn. OpenAI: ≥1024 tokens, 128-token increments; `prompt_cache_key` per conversation or user as shard key; keep tools and schemas byte-identical; use per-call `allowed_tools` instead of changing the tool list; put timestamps in `metadata`, not the prefix | Cache invariants for both providers through CLIProxyAPI |
| 17 | Speculative cache warming | Anthropic `misc/speculative_prompt_caching.ipynb` | Send a 1-token request with the exact context when the user focuses the input; the real request hits a warm cache | Copilot UI: warm when the operator starts typing (Anthropic only; check cost) |
| 18 | Evaluator-optimizer, orchestrator-workers, basic workflows | Anthropic `patterns/agents/*.ipynb` | Messages-API-only versions: `generate`/`evaluate` with `PASS / NEEDS_IMPROVEMENT / FAIL`; orchestrator emits XML subtasks; chaining, routing, parallelization | Reference shapes for node-editor templates |
| 19 | Async multi-agent messaging | Anthropic `patterns/agents/async_multi_agent_orchestration.ipynb` | Hub with inboxes; `send_message`/`wait_for_message`; **drained inbox appended to the last tool result** (no polling); spawn/get_status/kill | Only if QMX ever needs agent-to-agent messaging; today async sub-agents with task IDs are enough |
| 20 | Lead-researcher prompt | Anthropic `patterns/agents/prompts/research_lead_agent.md` | Query typing (depth-first, breadth-first, straightforward); sub-agent counts 1 / 2-3 / 3-5 / up to 10 or more by complexity; "stop deploying and write" when time runs long | Seed text for the QMX research supervisor skill |
| 21 | Scheduled, resumable reviewer | Anthropic `claude_agent_sdk/scheduled_repository_reviewer/...ipynb` | Cron runs `query()` with `permission_mode="dontAsk"`, `max_turns`, `max_budget_usd`; `resume=` previous session; schema output with `previous_finding_ids` / `resolved`; `ResultError` → greppable `REVIEW-CYCLE-INCOMPLETE` + non-zero exit | Template for QMX scheduled jobs (nightly data QA, strategy drift review) |
| 22 | Skills from a repo | Anthropic `managed_agents/CMA_use_skills_from_a_repo.ipynb`; `skills/notebooks/03_skills_custom_development.ipynb` | Scanner reads only `.claude/skills/<name>/SKILL.md` at session start; description must read like a trigger; read-then-follow protocol; layout rules strict | Same discovery rule for `/skills/qmx/` and `/skills/user/` |
| 23 | Building evals / tool eval | Anthropic `misc/building_evals.ipynb`, `tool_evaluation/tool_evaluation.ipynb` | Code-graded > model-graded > human; prefer many automatable items; reformat to multiple choice to automate; per-task agent loop over an eval file | QMX eval suite: code graders first (metric equality, file exists, schema valid) |
| 24 | Goals (completion contract) | OpenAI `codex/using_goals_in_codex.ipynb` | Six parts: outcome, verification surface, constraints, boundaries, iteration policy, **blocked stop condition**. Continuation only when idle, with no queued input or pending work. A continuation turn with **no tool call suppresses the next continuation**. Budget-limited ≠ complete. The model may mark complete only on evidence; pause, resume and clear are user/system | Core of the QMX Copilot goal loop (§3) |
| 25 | Iterative repair loop | OpenAI `codex/Build_iterative_repair_loops_with_Codex.ipynb` | Review (structured findings, no edits) → repair (copy + findings + last validation delta) → validate (execute + judge) → `record.json` per iteration; the signal is a **shrinking remaining delta** | Strategy-code repair loop: backtest must run and metrics must match the spec |
| 26 | Short-term memory: trim vs summarize | OpenAI `agents_sdk/session_memory.ipynb` | Trimming = lowest cost but context loss; summarizing = recall but **distortion/poisoning** risk, needs summary evals. Summary prompt principles: milestones, use-case specificity, contradiction check, timestamps, chunked sections, tool-performance insights | Adds the contradiction-check and timestamp rules to the ACM summary schema |
| 27 | Long-term memory lifecycle | OpenAI `agents_sdk/context_personalization.ipynb` | Structured profile + unstructured notes; global vs session scope; distillation → **async consolidation at session end** (most error-prone stage) → injection with precedence: latest user instruction > structured profile > advisory notes; conflict → ask; `<memory_policy>` block | Tier-2 memory consolidation job and injection block |
| 28 | Compaction vs memory | OpenAI `agents_sdk/building_reliable_agents_memory_compaction.ipynb` | Memory stores **workflow lessons, not case facts**; the reviewed artefact is the source of truth | Backtest conclusions live in reports; memory holds operator preferences and process lessons only |
| 29 | Cost and quality optimization | OpenAI `agent_optimization/optimizing_agents_for_cost_and_quality.ipynb` | Knob table: verbosity low plus capped output; effort low for routine and high for risky; stable tools + per-call `allowed_tools`; slim tool payloads; nano/mini/full routing; volatile data last; split sync answer from async QA (Batch/flex) | Background QA, tagging and report polishing off the operator path |
| 30 | Improvement loop from traces | OpenAI `agents_sdk/agent_improvement_loop.ipynb` | A **financial analyst** agent emits `risk_register.json`, `citations.json`, `evidence_table.csv`, `open_questions.md`; named failure modes (management narrative taken as metric, unvalidated estimate reported as fact); feedback → Promptfoo evals → HALO ranks harness changes → Codex handoff | Template for QMX research deliverables plus the tier-3 hill-climbing loop |
| 31 | Macro evals | OpenAI `partners/macro_evals_for_agentic_systems/...ipynb` | Lower-level evals per run → trace → compact document → topic clustering of recurring patterns → drill into suspects | Later: cluster Copilot traces to find recurring failure modes |
| 32 | Agents-as-tools quant team | OpenAI `agents_sdk/multi-agent-portfolio-collaboration/...ipynb` | PM agent calls Macro/Fundamental/Quant specialists as tools via `run_all_specialists_parallel`; prompts in Markdown files; `tool_retry_prompt.md`: retry 5xx/timeouts up to 2 more times, **never retry not-found inputs** | Quant research specialists; tool retry wording for Sol |
| 33 | Reasoning items | OpenAI `responses_api/reasoning_items.ipynb` | Pass reasoning items back across tool calls (about 3% on SWE-bench); encrypted items for `store=false` / ZDR | CLIProxyAPI must round-trip GPT reasoning items (§5) |
| 34 | Skills in the OpenAI API | OpenAI `skills_in_api.ipynb` | Same `SKILL.md` format; name/description/path injected; skills = procedures, tools = boundaries, system prompt = global behaviour | One skill format for both model families |

---

## 3. Loop engineering

### 3.1 Primary definitions
- **Anthropic** (https://claude.com/blog/getting-started-with-loops, 2026-06-30) defines loops as "agents repeating cycles of work until a stop
  condition is met". There are four kinds, distinguished by what you hand off:
  - **turn-based**: you hand off the check;
  - **goal-based** (`/goal`): you hand off the stop condition, and an evaluator model checks it at every stop attempt, e.g. "stop after 5 tries";
  - **time-based** (`/loop`, `/schedule`): you hand off the trigger;
  - **proactive**: you hand off the prompt.
  Its rules: "loops that write code need loops that check it", prefer deterministic criteria and scripts, pilot before large runs, and encode
  every failure into the system.
- **LangChain** (https://www.langchain.com/blog/the-art-of-loop-engineering) describes a stack of four loops, with a human touchpoint at each:
  agent → verification (`RubricMiddleware` or an `after_agent` grader) → event-driven (cron, webhooks) → hill-climbing (traces rewrite the harness).
- **Addy Osmani** (https://addyosmani.com/blog/loop-engineering/) names five primitives (automations, worktrees, skills, connectors,
  sub-agents), with on-disk state as the spine. The maker stays separate from the checker, and that includes the stop check.
- **Opus 5.5** (https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5):
  - It ends long-task turns with text-only progress reports. Treat these "as a report rather than as proof the task is done".
  - Keep a checklist. Continue by naming the open items, or have a smaller model check the completion condition.
  - Stop after 2-3 automatic continuations, and wait for running background jobs.
  - An `elapsed 340s / 1200s` time signal makes agent teams finish sooner.
- **Codex Goals** (row 24): continuation happens only at idle boundaries. A turn with no tool call suppresses the next continuation, and
  budget-limited is a separate terminal state.

### 3.2 Principles distilled
1. **Contract before work.** Fix the outcome, evidence surface, constraints, boundaries, iteration policy and blocked condition up front.
   Evidence decides "done"; the model saying it is done does not.
2. **Separate maker from checker, but spend checkers selectively.** Opus 5.x already self-verifies, and extra "double-check" prose causes
   over-verification (§5). External graders pay only where the rubric draws lines the task did not.
3. **Bound every loop on three axes:** iterations, money (a list-cost cap that pauses the run) and wall clock (an advisory signal plus a hard
   timeout). When a cap fires, the run is paused or budget-limited. It is neither done nor failed.
4. **Detect non-progress, not just failure.** Signals: identical-call hashes; continuations with no tool call; a delta that stops shrinking;
   the same grader criterion failing again.
5. **Keep state outside the context.** Todos, `progress.md`, run records and ledgers live there, and every loop resumes from them.
6. **Put humans at irreversible boundaries,** and ask them only after a concrete, reviewable result exists (GPT-6 guide).
7. **Encode failures into the system** through the tier-3 proposal path, never in a live session.

### 3.3 Concrete loop design for the QMX Copilot
Four nested loops. Each one is a named middleware or job, so the middleware list *is* the loop specification.

**L1, agent turn.**
- Opus 5.5 at effort `medium`, fixed per thread. Escalate with a per-message effort change (beta).
- Tools are fixed per thread, and todos go through `write_todos`. Set `max_tokens` high: Anthropic suggests 128k, because thinking counts
  against it.
- Add the Opus 5.5 "unattended" stop-pattern paragraph from the first request, for background jobs only.
- Middleware, outermost to innermost:
  1. policy-floor deny-list;
  2. truncation guard: a `max_tokens` stop drops that turn's tool calls;
  3. identical-call counter: warn at 2, HITL at 3;
  4. `ModelCallLimitMiddleware(run_limit≈80)`, plus `ToolCallLimitMiddleware` per costly tool;
  5. **new `BudgetMiddleware`**: usage × rate card per thread. At the cap it raises `interrupt({"kind":"budget_reached","spent":…})`.
     The operator can raise the cap and resume. It never auto-fails;
  6. `ToolRetryMiddleware` on read tools only.

**L2, goal controller** (new; runs as `after_agent` on any turn without a tool call). It only acts when the thread has a Goal, set by a
skill or by the operator; the six-part contract is held in state. It checks, in order:
1. A job or sub-agent is still pending: poll `check_async_task` and feed the output back.
2. Todos are open and no blocker is named: append a continuation that names them.
3. All todos are closed: run a cheap structured check (Luna or Sol, returning `met | not_met | blocked` plus a reason). The check is made
   against the **artefacts on disk**, not against what the transcript claims. Designated deliverables use `RubricMiddleware` instead.

Terminal states:

| State | Meaning |
|---|---|
| `complete` | Evidence is cited |
| `blocked` | Names the blocker and the question that would unlock it |
| `budget_limited` | A cost cap was reached |
| `stalled` | 3 continuations, or 2 continuations without a tool call, or the same grader failure twice |

Each state gets its own UI card, and only `complete` says "done". Continuations are appended as new messages; history is never edited (§5).

**L3, jobs and events** (the QMX jobs service).
- Triggers: cron, market calendar, data-arrival webhooks, Copilot async tasks.
- Every run gets a fresh thread with:
  - a pinned harness version; a USD budget, starting at 3-5x a normal run; `max_turns`; read-only credentials wherever the run only reads.
- Apply the six rules from https://claude.dev/blog/building-effective-agent-automations/:
  - read from per-source bookmarks, not "last 24h" windows;
  - a failed read is reported as unreadable, never as a quiet day, and its bookmark does not move;
  - re-check live state just before acting;
  - count an external write only after confirmation, then update the ledger and bookmarks; otherwise mark it "maybe-sent" and change
    nothing else;
  - re-read preferences each run from a store the agent cannot edit;
  - state the timezone in the trigger message.
- Run records (`posting → posted | maybe-posted`) make reruns idempotent.

**L4, hill-climbing** (offline, tier 3). The existing steward, plus:
- macro-eval trace clustering;
- evals that compare with-skill and no-skill runs;
- promotion by changing the pinned version (the CMA pattern), canaried on background jobs first.

**Human checkpoints.**
- L1: HITL on money, node and external writes, once the diff or ticket is ready.
- L2: `blocked` cards; L3: a triage inbox for job findings; L4: proposal approval.

**Long jobs.** These are async sub-agents with task IDs, or QMX jobs. The thread never blocks on them. L2 keeps the goal open while a job is
pending, and the UI shows where each job runs.

---

## 4. Graph engineering

### 4.1 Primary definitions
- **LangChain** (https://www.langchain.com/blog/3-years-of-graph-engineering-with-langgraph, 2026-07-22).
  - A node is code, one LLM call, a tool call, or a whole agent. Edges are fixed or conditional.
  - Agent graphs are **not DAGs**: they need retries, clarification, revision and HITL steps.
  - **A loop is the simplest cyclic graph.** Dynamic transitions (`Send` map-reduce) are essential.
  - What is new is that **a node can now be a whole agent run**.
  - Don't use graphs for open-ended work. LangChain and GPT Researcher both moved deep research back to an agent harness.
- **The loop-versus-graph test** (via https://www.aibuilderclub.com/blog/graph-engineering-guide-2026): "the difference is who decides the
  path, the agent or you".
- **Survey** (https://arxiv.org/abs/2608.21156). It defines graph engineering as "explicit, dynamic, evolving graph structures
  representing tasks, agents, and system states". The fit is work that needs heterogeneous expertise, interdependent subtasks,
  parallelism, independent verification and persistent state. It is a review, with no QMX-grade numbers.
- **Practitioner rules** (https://towardsdatascience.com/graph-engineering-for-ai-agents-from-prompts-and-loops-to-workflows/):
  - Edges come in seven kinds: direct, conditional, parallel, looping, error, human and event.
  - Use reducers at parallel joins, plus checkpoints; keep side effects idempotent around retries and interrupts; a low-confidence router falls back to the broader path; cap fan-out; give evaluator loops both a round cap **and** a no-improvement detector; "Prove the shape by hand" before automating it.

### 4.2 LangGraph facts that constrain the design (VERIFIED)
Sources: https://docs.langchain.com/oss/python/langgraph/graph-api, `/use-graph-api`, `/interrupts`, `/persistence`.
- **Checkpoints and resume.**
  - Checkpoints land at super-step boundaries. On resume after an interrupt or retry, the node **re-runs from the top**, so side effects
    before the pause repeat.
  - The fix is idempotency: keys, upserts, or read-before-write.
  - `@task` results are checkpointed, but reordering tasks or interrupts breaks them.
  - Editing nodes or edges does not break resume.
  - Never wrap `interrupt()` in a bare `try/except`. Resume parallel interrupts with an id → value map.
- **Node policies.**
  - `RetryPolicy(max_attempts, retry_on)`.
  - `TimeoutPolicy(run_timeout, idle_timeout)`: async nodes only; timed-out writes are not committed.
  - `CachePolicy(ttl)`; `error_handler=`, which returns `Command(update, goto)` for compensation; `set_node_defaults(...)`; the timeout, error-handler and defaults features need `langgraph>=1.2`.
- **Flow and state.**
  - `recursion_limit` and `RemainingSteps` allow a graceful wind-down.
  - `Send` for dynamic fan-out; `Command(goto=…)` for routing decided inside a node.
  - `Overwrite` bypasses a reducer, once per key per super-step.
  - `input_schema`/`output_schema` form the public contract; `context_schema`/`Runtime` carry run config (model, user, budget).
  - LangSmith cron runs in UTC with the same input every time. QMX owns its scheduler but should keep those semantics.

### 4.3 Concrete rules for QMX workflows and the node editor
Every node declares a `kind` and an `effect` (`pure | read | write_internal | external_write | money`). The compiler enforces policy
from both.

| kind | examples | model | default policy |
|---|---|---|---|
| `code` | resample, metrics, risk check, threshold gate | none | pure; `CachePolicy` ok; retry transient I/O only |
| `llm` | classify headline, extract fields | one structured call | `RetryPolicy(3)`; schema-validated, re-prompt on failure |
| `agent` | research a sector, repair strategy code | Deep Agent subgraph | own caps, budget, timeout and `error_handler`; typed output; resume from checkpoint |
| `tool` | fetch prices, run backtest, query catalogue | none | retry by effect class |
| `human` | approve order or publish, pick candidate | none | `interrupt()` with typed response schema |
| `trigger` | cron, market calendar, webhook, data arrival, manual, Copilot | none | entry only; carries bookmark and timezone |
| `subworkflow` | saved workflow | — | pinned version; own budget slice |

**Compiler rules.**
1. `money` and `external_write` nodes must be dominated by a `human` node, unless the policy floor whitelists them. They carry an
   idempotency key `(workflow_version, run_id, node_id, business_key)` and are never auto-retried: `RetryPolicy(max_attempts=1)`, with an
   `error_handler` that routes to a human.
2. Every cycle has a counter in state, plus exit edges on `counter ≥ N` and on "no improvement" (the delta is unchanged).
   `recursion_limit` is only a backstop.
3. Every `Send` has `max_fanout` (default 8, UI-editable) and a run-level USD budget. Overflow is batched, or rejected with a message as
   in Open Deep Research.
4. A node has at most one side effect, and it is the node's last action. Interrupts sit in a separate node before it, so a resume repeats
   only pure work.
5. Ports are typed, and the state schema is the union of ports. Parallel joins must name a reducer (`append`, `merge_by_key`,
   `override`).
6. Price frames and backtest results move as references (a path or dataset ID plus a summary), never as state payloads.
7. Kind choice:
   - `code` when the rule can be written down;
   - `llm` for one judgment with a schema;
   - `agent` only when the path is unknown. A whole "plan, search, read, synthesize" job is one `agent` node calling the research skill,
     not a graph.
8. Model is a node property: Sol by default, Luna for bulk tagging. This is static harness routing, with no gateway routing.

**Triggers.**
- Cron is stored in UTC, displayed in the operator's timezone, and the timezone is stated in the trigger message.
- Overlapping runs follow a per-workflow policy: `skip`, `queue` or `cancel_old`. Market jobs default to `skip`.
- Bookmarks are kept per source. Events dedupe on event ID.
- Each run carries a budget, `max_turns`, read-only credentials and a heartbeat record, so the UI can flag silence. A failed read is never
  a quiet run.
- Rollout order: by hand first, then a sample slice, then the schedule.

**Testing.**
1. Node tests: fixtures for `code` nodes; 5-10 labelled cases per `llm` node, code-graded where possible.
2. Contract tests: compile-time checks on rules 1-5, plus a dry run with a fake model and record/replay tool fixtures. The dry run asserts
   the path taken and the final state shape.
3. Resume tests: interrupt or fail at every write and money node, resume, and assert no side effect repeated.
4. Golden runs: 2-3 real past runs saved as eval items. A version is promoted (its pin changed) only if they still pass.
5. Step-through mode: run node by node before scheduling.

**Copilot and workflows.**
- The Copilot is the loop; workflows are graphs.
- The Copilot writes editor JSON, which passes through the same compiler, and runs workflows with `run_workflow` (§1.6).
- Workflows embed Copilot skills as `agent` nodes.
- Useful dynamic sub-agent scripts become saved workflows once the operator approves (the `.claude/workflows/` idea).

---

## 5. Multi-model tuning: Claude Opus 5.5 main, GPT-6.1 Sol sub-agents, one harness

Sources:
- https://www.langchain.com/blog/tuning-deep-agents-different-models
- https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- `/prompting-claude-opus-5-5`, `/prompting-claude-opus-5`, `/prompting-claude-fable-5-1#keep-the-conversation-history-append-only`
- https://developers.openai.com/api/docs/guides/latest-model (GPT-6 and GPT-5.6 sections)

**Mechanics.**
- Use one `HarnessProfile` per model key. Everything model-specific lives there: prompt suffix, tool description
  overrides, excluded tools and middleware, extra middleware. The shared system prompt stays model-neutral.
- Provider transport settings (base URL to CLIProxyAPI, headers) go in `ProviderProfile.init_kwargs`.
- Eval every profile change on the same suite, with k ≥ 2.

| Dimension | Claude Opus 5.5 (main) | GPT-6.1 Sol (sub-agents) |
|---|---|---|
| Effort | Thinking always on. Start `medium` (the default). `xhigh`/`max` only on measured gains. Changing top-level `effort` invalidates the cache; use the per-message effort change (beta) | `reasoning.effort` low/medium(default)/high/xhigh/max; `none`/`minimal` unsupported. Change mid-conversation with `configuration_update` items and keep request-level effort fixed |
| Reasoning state | **History must be append-only.** On Opus 5.5, editing earlier messages, rebuilding `system`/`tools`, or summarizing older turns in place invalidates later thinking blocks (an error, or blocks dropped with `prefix_mismatch_behavior: "drop_block"`) | Pass reasoning items back across tool calls (Responses API, `previous_response_id`, or encrypted items when `store=false`). Persisted reasoning `reasoning.context` defaults to `all_turns` on 5.6+ |
| Tool calling | Parallel by default; promptable. Opus profile snippets: `<tool_result_reflection>`, `<tool_usage>` ("observe state directly…") | Tool calling **requires the Responses API**. Codex-style tool names (`apply_patch`, `shell_command`) helped Codex models; consider `tool_description_overrides` for Sol |
| Verification | **Remove** "double-check" and "add a verification step" instructions: Opus 5.x self-verifies, and these cause over-verification. Keep the *evidence* rule (cite tool output) | Calibrate testing: "Run tests appropriate to the change… broaden only when failures justify it" |
| Delegation | Opus 5.x **over-delegates**. Add the damping prompt: "Delegate … only for large tasks that are genuinely independent … do not use subagents to verify… keep spawn counts low"; plus deterministic caps | Astra-family models **under-delegate**, but Sol sub-agents get no `task` tool anyway. Add "messages to other agents … must be legible" for handoffs |
| Scope and autonomy | Scope prompt: "Deliver what was asked, at the scope intended … check in only when readings would lead to materially different work" | Asks clarifying questions more than earlier models. Add the "complete authorized work, then ask approval on a concrete result" prompt and **one** compact autonomy/approval policy |
| Skills and instructions | Literal instruction following; keep skills precise | **More sensitive to skills and AGENTS.md text**: audit them. Add "user instructions take precedence over a skill" and "name the SKILL.md line that made you pause" |
| Progress UI | Progress updates arrive as **thinking blocks with empty text** unless `thinking.display: "updates"` (beta header `thinking-display-updates-2026-08-18`); the UI must render them or it looks silent. Nudge after about 5 silent tool steps with a **turn-scoped system message** (`clear_at: "next_user_message"`) | `text.verbosity` low/medium/high as the default; prompt for task-specific length |
| Prompt size | Effort is the main thinking lever; prompts can stay compact | "Favor leaner prompts": removing repeated instructions gave +10-15% score with 41-66% fewer tokens in OpenAI's coding evals. State each rule once |
| Caching | `cache_control` (automatic or breakpoints), 5m/1h TTL; deferred tool loading keeps the prefix | ≥1024-token prefix, `prompt_cache_key` per thread, `prompt_cache_options.ttl: "30m"` (GPT-6); **cache writes bill 1.25x** on 5.6+, so track `cache_write_tokens`; `allowed_tools` per call instead of changing `tools` |
| Time and budget | Time signal line `elapsed Ns / Ms` speeds agent teams | Async tool calling (`async: true`) and mid-turn steering exist; not needed for sub-agents now |

**Shared harness rules that follow from the table:**
1. **Never mutate the prefix mid-thread**, for either provider. Reminders and new instructions go in as appended
   (turn-scoped) system messages. Tools and skills are fixed at thread start. Tool search uses deferred loading.
2. **Compaction must be whole-history replacement on Claude** (one summary message plus the new user turn, replay no
   thinking blocks), or server-side compaction. The blueprint's in-place keep-tail summarization conflicts with this (§6).
3. **Cross-model grading.** Sol grading Opus deliverables (and the reverse for Sol research) uses one rubric format.
   Graders get evidence tools and a fresh context.
4. **CLIProxyAPI must be transparent** to the features above. These are all **UNVERIFIED**:
   - Anthropic beta headers: per-message effort, `thinking.display`, mid-conversation system messages, compaction and
     context editing;
   - thinking-block round-trip byte-for-byte;
   - OpenAI Responses passthrough with reasoning items, `prompt_cache_key` and `configuration_update`.
   Test each with a captured-request diff: consecutive requests must be byte-identical up to the appended turn.
5. **Profile drift test.** For each profile, log the full assembled request on turn 1 and turn N, and diff in CI.

---

## 6. What this changes or adds to the earlier blueprint and paper syntheses

**Corrections (blueprint §8 is risky as written):**
1. **Compaction on Opus 5.5 (most important).** The blueprint's `SummarizationMiddleware` (0.85 trigger, 0.10 keep) summarizes
   older turns *in place* and keeps a tail. On Opus 5.5, editing the prefix ahead of retained thinking blocks causes 400 errors or
   dropped blocks. Fable 5.1 enforces this for new accounts, and the docs list Opus 5.5 with it. **Change:** at task boundaries,
   replace the *whole* history with one structured summary plus the new turn, or use server-side `compact_20260112`. It is still a
   single summarizer. Verify with `prefix_mismatch_behavior: "drop_block"` and log `input_transformations`. The same applies to
   context editing, dynamic system prompts and per-turn memory injection into `system`.
2. **Remove "verify / double-check" prose** from the Opus prompt, because it causes over-verification. Keep the evidence-based finish
   rules and the deterministic probes. Use the rubric grader only for designated deliverables, which confirms the paper synthesis
   "possible overbuild" flag.
3. **Enforce "stop after two failed attempts" in L2 code,** with distinct terminal states. An Opus 5.5 text-only `end_turn` is a
   report, not completion.
4. **Effort stays fixed per thread**, but escalation is allowed by cache-safe means: a per-message effort change on Anthropic, or
   `configuration_update` on OpenAI.

**Additions:**
5. **L2 goal controller:** a six-part contract, completion checked against artefacts, and a cap of 2-3 continuations.
6. **`BudgetMiddleware`:** a per-run USD cap that pauses the run through an interrupt and shows in the UI. Workflows carry budgets
   too.
7. **Dynamic sub-agents** (`CodeInterpreterMiddleware`, QuickJS) become the fan-out and RLM path, replacing blueprint §7's custom
   recursive sub-agent. The gating rule stays.
8. **Workflow skills:** node-editor workflows are exposed to the Copilot as skills plus `run_workflow`, the Python form of
   interpreter skills.
9. **Quant data catalogue:** dataset cards, a metric registry, and operator-only endorsements, read by both the Copilot and the
   graders.
10. **Research skill** shaped like Open Deep Research: brief → supervisor → ≤5 researchers → compress → one-shot report, with its
    caps as defaults.
11. **Automation rules** for every scheduled or event job:
    - read from bookmarks; report a failed read as a failure, never as a quiet day; update the ledger only after a write is confirmed; re-check live state before acting; keep preferences in a read-only store; state the timezone; set the budget at 3-5x a normal run.
12. **Node-editor compiler rules** (§4.3):
    - a kind/effect taxonomy; a human node must dominate money and external writes; idempotency keys; cycle caps plus no-improvement exits; fan-out caps; reducers at joins; references, not payloads; resume tests.
13. **UI:**
    - render Opus 5.5 progress-update thinking blocks (`display: "updates"`), or long turns look silent;
    - terminal-state cards; a triage inbox; optional speculative cache warming when the operator focuses the input.
14. **Deliverable artefacts** (the OpenAI financial-analyst pattern): `evidence_table.csv`, `citations.json`, `risk_register.json` and
    `open_questions.md`, checked mechanically by probes and graders.
15. **Memory:**
    - consolidate asynchronously at session end;
    - precedence runs latest instruction > profile > advisory notes, and a conflict means ask the operator;
    - store lessons and preferences, never case conclusions; summaries get a contradiction check and timestamps; memory tools are excluded from clearing.
16. **Tiering** applies to sub-agents and workflow nodes only (Luna, Sol, Opus), chosen at spawn time after outcome metrics are
    defined. The main model is never switched mid-thread.
17. **`ProviderProfile` + `HarnessProfile`** handle CLIProxyAPI transport and per-model prompts. A CI test diffs assembled requests
    across turns to check that the prefix stays stable.

**Confirmed, no change:**
- no modes; 10-15 visible tools plus a deferred long tail; lazy skills; HITL on money, node and external writes; async jobs with task IDs; tier-3 governance with pinned versions; probes run before LLM judges; multi-agent only for parallel research, never for co-writing.

**Still UNVERIFIED** (smallest first):
1. CLIProxyAPI passthrough of Anthropic betas, thinking blocks, OpenAI reasoning items and cache keys.
2. Profile-key resolution for model instances.
3. Interpreter `eval` timeout vs long `task()` awaits.
4. Whether `SummarizationMiddleware` can do whole-history replacement, or needs a custom middleware.
5. Whether the installed langgraph is ≥1.2.
