# 22 — Vendor cookbooks and templates, read in full: what is already solved for QMA v2

Researched 2026-10-12. Research only. Nothing here is ratified, and no code was written or run.
Pages were read as whole pages (firecrawl full-page markdown, `onlyMainContent`). Long notebooks were read from the
read-only clones with `git show` (prose in full, code cells skimmed for structure). Context7 was not used.
Clones: `D:\QMX-research\sources\repos\openai-agents-python` (commit `125efa0`, 2026-10-08),
`D:\QMX-research\sources\repos\openai-cookbook` (partial), `D:\QMX-research\sources\repos\claude-cookbooks` (commit `9c1e493`, 2026-10-10).
Read count: about 31 (see §6 for what was skipped).

**Citation keys**
- `OAI-LOOP` = https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop
- `OAI-MIG` = https://developers.openai.com/cookbook/examples/agents_sdk/migrate-from-claude-agent-sdk/readme
- `OAI-MEM` = https://developers.openai.com/cookbook/examples/agents_sdk/building_reliable_agents_memory_compaction
- `OAI-COST` = https://developers.openai.com/cookbook/examples/agent_optimization/optimizing_agents_for_cost_and_quality
- `OAI-DATA` = https://developers.openai.com/cookbook/examples/agents_api/apps/data_analyst/readme
- `OAI-REPAIR` = https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex
- `OAI-BUDGET` = https://developers.openai.com/cookbook/articles/per_run_spending_controller_responses_api
- `OAI-AB` = https://developers.openai.com/api/docs/guides/agent-builder (+ `/agent-builder/migrate-from-agent-builder`, `/node-reference`)
- `OAI-PAT` = clone `openai-agents-python/examples/agent_patterns/*` ; `OAI-MA` = clone `docs/multi_agent.md`
- `OAI-PF` = clone `openai-cookbook/examples/agents_sdk/multi-agent-portfolio-collaboration/` (notebook + `prompts/*.md`)
- `A-DW` = https://claude.com/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code (served from claude.dev)
- `A-HAR` = https://claude.com/blog/harnessing-claudes-intelligence (the "three harness design patterns" post)
- `A-AUTO` = https://claude.dev/blog/building-effective-agent-automations/ (2026-10-08)
- `A-EVAL` = https://claude.dev/blog/automating-eval-design-and-hillclimbing/ (2026-09-28)
- `A-BEA` = https://www.anthropic.com/engineering/building-effective-agents
- `A-LONG` = https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- `A-CTX` = https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- `CB:<path>` = clone `claude-cookbooks/<path>`

---

## 1. Plain-words summary

1. The operator is right: most of the loop, graph, verifier, memory, cron and self-improvement patterns are already written down by both vendors, with code.
2. Both vendors now say the same thing: plan in code, let agents do only the judgment steps, and check results with something deterministic first.
3. Anthropic names six workflow shapes (classify-and-act, fan-out-and-synthesize, adversarial verification, generate-and-filter, tournament, loop-until-done). They map 1:1 onto QMX built-in templates.
4. OpenAI's agent patterns folder adds the same set in Python: chain with a gate, routing/handoff, agents-as-tools, judge loop, parallel best-of-N, guardrails, approvals.
5. OpenAI's visual Agent Builder (the thing that had "templates") is deprecated and shuts down on 2026-11-30. SDK users get example code, not templates.
6. The best self-improvement recipe is OpenAI's: traces, then human and model feedback, then generated evals a human checks, then a gate, then a ranked change list for a coding agent, then a reviewed PR.
7. Anthropic's hillclimb adds the guard rails: train and test split, one change per round, revert if only the train score rises, never paste failures into the prompt.
8. Long-running work survives on files, not on one immortal chat: a progress file, a feature list in JSON, git history, bookmarks, a ledger, and a run record.
9. Scheduled agents should read from bookmarks (not "last 24 hours"), report a failed read as a failure, re-check items before posting, and only record a post after it is confirmed.
10. Prompts: static part first, dynamic part last, preferences read fresh each run, prompt versioned together with model, tool policy and eval status.
11. Caching rule that changes the router design: never switch models inside a session; route at session or sub-agent boundaries.
12. Budgets: give each run its own budget, reserve the worst-case cost before each call, settle after, stop when unsure.
13. Measure "cost per verified result", counting failed attempts, not tokens per call.
14. The portfolio cookbook (PM plus quant, macro, fundamental specialists) and the data-analyst app are near-ready templates for QMX research agents.
15. Main corrections to the QMA v2 direction are in §5: verifiers must earn their cost, the orchestrator is a role with durable state rather than one session, OpenAI does have skills, and the router must respect caches.

---

## 2. Per-source sections

### 2.1 OpenAI: "Build an agent improvement loop with traces, evals, and Codex" (`OAI-LOOP`, 2026-05-12)
- **Shape.** Five traced runs of a diligence analyst, then human feedback (required observations, prohibited claims) and separate
  LLM insights per trace, then an LLM writes 5 to 7 eval definitions (deterministic, judge or hybrid, each with pass and fail
  examples), then Promptfoo runs them as a gate, then HALO reads harness config plus traces plus feedback plus eval results and
  writes `codex_handoff.md`, then Codex implements, then the same evals rerun.
- **Harness as data.** `AgentConfig(version, system_prompt, model_settings, tool_policy, eval_metadata)`; `eval_metadata` holds
  `version: v001`, `status: promoted`, `promotion_gate: manual_review`. `build_instructions()` = system prompt + tool policy
  rendered as text + a runtime line "Treat this config as the promoted runtime contract. Do not modify the runtime config".
- **Dynamic additions go in the user turn.** `build_user_prompt()` adds memo, risk-category or NRR rules only when the question asks
  for them. The system prompt stays static.
- **Validators as agent tools.** `check_evidence_coverage.py` (claims list must cite existing files) and
  `validate_output_contract.py` (required artifacts, JSON shape). The prompt says to run both and revise before finishing.
- **Required artifacts.** `summary_answer.md`, `investment_memo.md`, `risk_register.json`, `open_questions.md`, `citations.json`,
  `evidence_table.csv`. The final answer is not trusted alone.
- **Evidence rules (directly reusable for quant work).** Prefer structured CSV or JSON over narrative when they conflict; never
  fabricate numbers; state conflicts instead of reconciling them; keep facts, inferences and open questions separate.
- **Observability.** A local trace processor writes one OpenTelemetry-style JSONL line per span (`set_trace_processors`), with
  model, tokens, tool calls and workflow name. The harness config and gate summary are added as synthetic spans so the optimizer
  sees everything in one file.
- **HALO output contract.** It must classify each failure as "requirement missing", "present but not followed" or
  "implementation/observability defect", then give a ranked table (impact, confidence, effort, evidence, validation).
- **Result worth noting.** Top recommendation was "add a deterministic fact ledger and domain checklist layer", and "upgrade
  validators to audit the real artifacts". Even with a 5/5 eval pass, the optimizer asked for more deterministic checks.
- **Human gates.** Humans can sit at trace review, eval refinement, PR approval, merge, deploy. "A common starting point is a
  reviewed loop." A closed loop can poll for new handoffs with a heartbeat.

### 2.2 OpenAI cookbook index, agent-related (https://developers.openai.com/cookbook/topic/agents, 34 items; + home page)
Read in full: marked **[R]**. Others are title-and-card only.
- **[R]** Cost and quality optimization (09-14) §2.6; **[R]** data analyst, Agents API (09-10) §2.7; **[R]** per-run spending
  controller (08-17) §2.9; **[R]** improvement loop (05-12) §2.1; **[R]** iterative repair loops with Codex (05-11) §2.8;
  **[R]** migrate from the Claude Agent SDK (05-07) §2.3; **[R]** memory and compaction (05-01) §2.4.
- Hosted Agents API (new, 2026-09): Lambda MicroVM sandboxes (09-29), SRE incident bot (09-10), Slack bot (09-10).
- Agents SDK + AWS AgentCore: ChatGPT plugin packaging (09-03), controlled payments (08-13), prior-authorization review (08-10),
  AML analysis on Bedrock (07-23, evidence-grounded finance agent), OpenAI models on Bedrock (05-31).
- Agents SDK building blocks: security scanners then agent triage (08-05), Oracle long-term memory (07-16), SchemaFlow SQL agent with
  eval gates (06-05), Deployment Manager (05-05), computer use in Daytona sandboxes (04-19), legacy-code migration with sandbox
  agents (04-07), long-term memory notes (2026-01-05), short-term memory with Sessions (2025-09-09).
- Codex and ChatGPT: iterating dev workflows (08-03), Goals in Codex (05-09), Codex prompting guide (02-25), workspace agents (04-22)
  and API trigger (06-18).
- Evals and prompts: macro evals for agentic systems (05-19), realtime eval guide (01-25), GPT-5 prompt optimizer (2025-08-07);
  Skills in OpenAI API (02-10, OpenAI's own `SKILL.md`); temporal agents with knowledge graphs (2025-07-22).
- Home page extra: harness-aware evaluation of plugins (2026-09-23), directly relevant to QMX plugins, not read (§6).
- Also read in full: multi-agent portfolio collaboration (§2.5) and the Agent Builder docs (§2.10).

### 2.3 OpenAI: migrate from the Claude Agent SDK (`OAI-MIG`)
- **Core architectural claim.** Claude Agent SDK puts the harness inside the sandbox. OpenAI's SDK keeps the harness in the
  trusted app (loop, tools, approvals, secrets, guardrails, tracing) and treats the sandbox as a tool.
- **Mapping table (reusable for the QMX plugin loader).** `CLAUDE.md` product behavior to `Agent.instructions`; `CLAUDE.md` repo
  guidance to `AGENTS.md`; `.claude/skills/*/SKILL.md` to `.agents/skills/*/SKILL.md`; skill references to `references/` or
  `assets/`; skill scripts to sandbox-backed skill execution; `.claude/agents/*.md` to explicit `Agent(...)`.
- **Callbacks.** Logging callbacks go to `RunHooks`/`AgentHooks`. Anything that blocks or asks permission goes to tool guardrails
  or `needs_approval` plus `RunState` resume.
- **Ownership rule.** `agent.as_tool()` when the lead keeps the final answer; `handoffs=[...]` when the specialist owns it.
- **State.** Pick one per conversation: local `Session`, `previous_response_id`, server `conversation_id`, or explicit history.
  "Conversation continuation" and "run-state resume" are different things.
- **Do not port generic file/shell helpers as business tools.** Business actions become typed `@function_tool`s. Test order ends with
  Claude and OpenAI runs side by side, comparing answers, tool calls, safety and state.

### 2.4 OpenAI: reliable agents with memory and compaction (`OAI-MEM`)
- **Split of duties.** Compaction keeps the current run alive. Memory carries workflow lessons to future runs. The reviewed
  artifact (the memo) is the system of record. "Do not treat Memory() as an unreviewed fact database."
- **Memory prompt.** `MemoryGenerateConfig(extra_prompt=...)`: store reusable workflow lessons only; never case facts, citations or
  conclusions. Good memory: "use the manifest first", "preserve uncertainty". Bad memory: "vendor X violated policy".
- **Compaction modes.** Automatic `Compaction()`; threshold `StaticCompactionPolicy(threshold=...)`; forced checkpoint at a phase
  boundary (`OpenAIResponsesCompactionSession.run_compaction({"force": True})`), using a cheaper compaction model. "Compact at
  meaningful workflow boundaries, not after every turn." Instruction: "When context is compacted, preserve the current batch, cited
  facts, open questions, artifact paths, and unresolved reviewer concerns."
- **Workspace manifest.** Inputs, a machine-readable `manifest.csv` with stable doc IDs, `outputs/`, and SDK-owned `memories/` and
  `sessions/`. Long task text goes in workspace files (`README.md`, `task.md`, `AGENTS.md`); instructions stay about behavior.

### 2.5 OpenAI: multi-agent portfolio collaboration (`OAI-PF`)
- **Shape.** Hub-and-spoke. Head PM agent (temperature 0, `parallel_tool_calls=True`) calls quant, fundamental and macro
  specialists as tools, or all three at once through a `run_all_specialists_parallel` tool, then a `memo_editor` tool.
- **Repair loop by contract.** If `memo_editor` returns `missing` or `incomplete` keys, the PM re-calls only the specialist that
  owns the gap, re-assembles, and calls the editor again "until complete".
- **PM prompt (`prompts/pm_base.md`).** Firm philosophy, tool list, tool usage rules, input schema (user question verbatim plus
  per-section guidance that must include a counter-thesis), a 6-step workflow, a JSON template, worked examples. "Do not summarize
  or alter specialist outputs; pass them verbatim."
- **Quant prompt (`prompts/quant_base.md`).** THINK, PLAN (at most 3 bullets, multiple analyses, "do not just use historical
  data"), ACT (batch all known fetches in parallel; confirm files exist before calling the code interpreter; never parallelize
  dependent calls), REFLECT. Required headers include "Data quality and gaps" and "PM pushback". Must run at least one numeric or
  simulation analysis and produce a chart. Ends with `END_OF_SECTION`.
- **Code-interpreter contract.** Every file the request mentions must be in `input_files`; print schema first; return only a
  `<reason>` tag when data is empty.
- **Retry prompt.** Retry a failed tool call up to 2 more times for server, auth, timeout or network errors; do not retry with the
  same input when the resource does not exist (bad ticker, missing series).
- **Tracing to file.** `add_trace_processor(BatchTraceProcessor(FileSpanExporter()))`. Note: `add_` keeps the default uploader;
  `OAI-LOOP` uses `set_trace_processors([...])`, which replaces it.

### 2.6 OpenAI: optimizing agents for cost and quality (`OAI-COST`)
- **Safe tuning order:** baseline, prompt and output controls, tool control, context hygiene, model routing, prompt caching,
  cache-aware context, split sync/async workflow, processing tier (Batch or flex).
- **Per-step routing.** Nano for triage and tags, mini for routine resolution, full model for high-risk cases; low reasoning for
  routine, higher only for high-risk; `tool_choice.allowed_tools` per task while keeping the full tool list stable for caching.
- **Caching.** Stable instructions, tools, policy framing and schema first; ticket data last.
- **Metric.** "Blended cost per verified resolution" = all model, tool, retry, human-review and rework cost divided by verified
  resolutions, counting failed attempts. Hard gates (policy, action correctness, escalation) before comparing cost or latency.
- **Judge rules.** A judge pass never overrides a deterministic failure; judge is blind to variant and model; label a small sample
  yourself and check judge agreement before using it as a release gate.

### 2.7 OpenAI: data analyst with the Agents API (`OAI-DATA`)
- Four tools: `search_tables` (real columns), `search_context` (metric definitions, past queries, documents, saved corrections),
  `query_warehouse` (one read-only query, at most 100 rows), `save_memory` (only when the user explicitly asks; personal or team
  scope; loaded on demand with `tool_search` and `defer_loading`). Programmatic tool calling lets the model combine several calls.
- App owns the database URL; read-only role; query timeout; every executed SQL shown with the answer. "Treat the narrative as a
  conclusion to verify against those records."
- Uses the new hosted **Agents API** (`client.beta.agents.sessions`, `environment={"type": "none"}`), released 2026-09.

### 2.8 OpenAI: iterative repair loops with Codex (`OAI-REPAIR`)
- Three phases with JSON-schema outputs: **Review** (findings only, no edits, "three strong findings beat a long list"),
  **Repair** (smallest useful edit to a copy, given findings plus last validation delta; "do not claim it passes"),
  **Validate** (execute first, then a judge scores cases; failures become `remaining_delta`).
- A shared "business rules" contract is given to all three phases.
- `record.json` per iteration and artifact: review, repair, validation. "That is the audit trail."
- **Stop rules:** validation passes; max attempts; remaining delta stops changing; next decision needs a human.

### 2.9 OpenAI: per-run spending controller (`OAI-BUDGET`)
- Each run has a budget. Before each call, reserve the worst case (all input at the highest input price plus max output); after,
  settle the real cost. Stop before a call would exceed the balance; block the run when cost is uncertain (interrupted call, missing
  usage, wrong model returned). Many workers need a shared atomic check-and-reserve. Project spend limits do not stop a single task.

### 2.10 OpenAI: Agent Builder "templates" (`OAI-AB`)
- Agent Builder had a template gallery (example: homework helper) and nodes: Start, Agent, Note, File search, Guardrails, MCP,
  If/else and While (both CEL expressions), Human approval, Transform, Set state. Edges are typed; workflows are versioned on
  publish; "Evaluate" runs trace graders.
- **Deprecated; shuts down 2026-11-30.** Migration exports Agents SDK code (TypeScript or Python) or converts to a ChatGPT workspace
  agent. "This process does not convert your workflow graph." "Workflows with strong determinism at their core may not migrate
  faithfully to a workspace agent."
- **Answer to the brief:** no maintained templates for SDK users; only `examples/agent_patterns/` (§2.11) and cookbooks.

### 2.11 OpenAI Agents SDK pattern examples (`OAI-PAT`, `OAI-MA`)
`OAI-MA` splits orchestration into "via LLM" (agents-as-tools, handoffs) and "via code" (structured-output classification then
branch, chaining, evaluator `while` loop, `asyncio.gather`). Each example as a QMX template:
- `deterministic.py` — outline agent, checker agent with `output_type` booleans, code gate exits early, writer agent. One trace.
  **QMX:** "chain with gate" template; the gate is a code node reading a typed field.
- `routing.py` — triage agent with `handoffs`; next turn continues with `result.current_agent`; `group_id` links turns.
  **QMX:** "router" template where the chosen specialist owns the conversation.
- `agents_as_tools*.py` — manager calls specialists via `as_tool()`; variants: streaming nested events, structured input,
  conditional `is_enabled(ctx)` per user tier, `needs_approval` on an agent-tool. **QMX:** "manager with specialists" template; tool
  visibility per plugin or entitlement.
- `llm_as_a_judge.py` — generator and evaluator (`pass | needs_improvement | fail` plus feedback); loop appends feedback; caps rounds
  in auto mode. README: small model generates, larger model judges. **QMX:** "judge loop" template; always cap rounds.
- `parallelization.py` — same agent 3x in parallel, picker agent chooses. **QMX:** "best-of-N" template.
- `input_guardrails.py` / `output_guardrails.py` / `streaming_guardrails.py` — tripwire raises and stops the run; a fast model can
  guard a slow one. **QMX:** guard nodes before and after any agent node.
- `forcing_tool_use.py` — `tool_choice="required"` plus `tool_use_behavior` (`stop_on_first_tool` or a custom function that turns tool
  output into final output). **QMX:** "deterministic finish" option: an agent picks arguments, code produces the result.
- `human_in_the_loop*.py` — pause, approve or reject, resume from `RunState`; the server variant keeps state server-side, issues
  single-use decision IDs, checks owner, "never deserialize an unverified client-supplied RunState". **QMX:** approval node.
- `hosted_multi_agent_beta.py` — server-hosted sub-agents (`OpenAIHostedMultiAgentModel`, `max_concurrent_subagents`) while local
  function tools still run in the app. Experimental.

### 2.12 Anthropic: "A harness for every task: dynamic workflows" (`A-DW`, 2026-06-02)
- Script primitives: `agent(prompt, {schema, model, isolation: worktree|remote, agentType})`, `parallel()` (wait for all),
  `pipeline()` (each item flows through stages). Interrupted workflows resume.
- Why: single-context failure modes are **agentic laziness** (stops at 35 of 50), **self-preferential bias** (grades its own work
  kindly), **goal drift** (lossy after compaction).
- Six patterns: classify-and-act, fan-out-and-synthesize (synthesis is a barrier), adversarial verification, generate-and-filter,
  tournament (pairwise judging), loop until done (stop on no new findings or no more errors).
- Use cases: migrations (worktree per fix plus adversarial reviewer), deep research, deep verification (one checker per claim,
  optional source auditor), tournament sort ("comparative judgment is more reliable than absolute scoring"), rule-by-rule review
  (one verifier per rule plus a skeptic), session mining into `CLAUDE.md` rules ("would this rule have prevented a real mistake?"),
  root cause from disjoint evidence, quarantine triage (readers of untrusted content have no privileges; an actor sees only their
  summaries), taste exploration, lightweight evals, model routing by a classifier agent.
- When not: "most traditional coding tasks do not need a panel of 5 reviewers". Token budgets can be set in the prompt. Pair with
  `/loop` (recurring) and `/goal` (hard completion). Saved workflows live in `~/.claude/workflows` or inside a skill folder as a
  template, "instead of a script that needs to be run verbatim".

### 2.13 Anthropic: three harness design patterns (`A-HAR`)
1. **Use what Claude knows** — bash and a text editor; skills, programmatic tool calling and memory are compositions of them.
2. **Ask what you can stop doing** — let Claude write code that chains tool calls so raw results never enter context (BrowseComp
   45.3% to 61.6%); progressive disclosure through skills; context editing removes stale tool results; Claude chooses what to persist
   (compaction, memory folder). Example of dead weight: context resets added for Sonnet 4.5 became unnecessary with Opus 4.5.
3. **Set boundaries carefully** — cache table: static first, dynamic last; updates as an appended `<system-reminder>` message, not by
   editing the prompt; **do not change models mid-session (caches are per model; use a sub-agent for a cheaper model)**; adding or
   removing tools breaks the cache (use tool search); move the breakpoint forward (auto-caching). Promote actions to typed tools
   when you need a security gate, a UI render, or an audit log; reversibility is the test.

### 2.14 Anthropic: building effective agent automations (`A-AUTO`, 2026-10-08)
- Reference implementation: `claude-quickstarts/managed-agents/daily-brief` on Claude Managed Agents (beta). Files: `agent.md`
  (model, tools, run steps), `deployment.md` (cron, timezone, budget, first message), `environment.yaml` (network allowlist), two
  memory stores (`preferences` read-only to the agent; `state` read-write), `vault.yaml` (credentials outside the sandbox).
- **Six rules:** read each source from a bookmark, not a fixed window; report a failed read as unreadable, never as a quiet day;
  re-check every item right before posting; count a post as sent only when the destination confirms, then update bookmarks and
  ledger; re-read preferences every run from a store the agent cannot edit; read-only access where it only reads, plus a spend cap.
- **Run record** `runs/<date>.md`: "posting", then "posted" with message ID, or "maybe posted" (change nothing else).
- **Ledger** of reported items with stable IDs and last status; carry open items as one line ("still waiting, day 3").
- **Budget:** start at 3 to 5x a normal run; a capped run pauses, which can look like a quiet brief. Timezone set twice (schedule and
  prompt). Prompt rule: "assert it or drop it"; links copied from source fields, never assembled by hand.

### 2.15 Anthropic: automating eval design and hillclimbing (`A-EVAL`, 2026-09-28)
- **Good eval:** tasks mirror production; stronger model and more effort score higher; headroom below 100% at the frontier; low
  run-to-run variance. Pick hard cases because a human can say why they are hard, not because today's model fails them.
- **Input order:** production transcripts, bug reports and tickets, 5 to 10 hand-written, then synthetic from the codebase. A review
  page shows all inputs and waits for confirmation.
- **Grader:** cheapest that fits (code check first; else LLM judge with a rubric of checkable claims, not a 1-to-5 scale; pairwise
  blind comparison against a baseline); judge model is not the tested model. Diagnostics: grade the same output twice, check
  plumbing (timeouts, cut-offs), warn at about 95% baseline.
- **Hillclimb:** pick a surface that is cheap to change and attributable (prompts, skills, tool descriptions, model and effort).
  Random train and test split; check noise is smaller than the smallest gain you would act on; one patch per round aimed at a root
  cause; keep if train and test rise; revert if only train rises or anything drops; never paste failures into the prompt; after 2 to
  3 stalled rounds, sort remaining failures by cause (catches broken tasks and graders). Final report against baseline with
  confidence intervals; "if the gain is within noise, it says so and recommends against merging".
- **Cost example:** Opus 4.8 high effort 74.4% at 4.6 cents; Opus 5.5 low effort 87.8% at 1.9 cents; Sonnet 5 low effort with an
  improved prompt 98.9% at 1 cent; held-out 90.5% vs 78.6% at about one fifth of the cost.

### 2.16 Anthropic engineering posts (`A-BEA`, `A-LONG`, `A-CTX`)
- `A-BEA` (note at top: tooling has changed; see Managed Agents): workflows (predefined code paths) vs agents (model directs);
  start with the simplest thing; patterns: prompt chaining with gates, routing (including small vs large model), parallelization
  (sectioning and voting), orchestrator-workers, evaluator-optimizer, autonomous agent with stop conditions. Principles: simplicity,
  transparency of planning, careful tool docs ("poka-yoke": absolute file paths fixed a whole class of errors).
- `A-LONG`: **initializer agent** writes `init.sh`, `claude-progress.txt`, a first git commit, and a JSON feature list (200+ items,
  all `passes: false`; JSON because the model is less likely to rewrite it than Markdown). **Coding agent** each session: `pwd`, read
  progress and git log, read the feature list, run a basic end-to-end check, do one feature, test as a user would, commit, update
  progress. Same system prompt and tools for both; only the first user prompt differs. Compaction alone was not enough.
- `A-CTX`: context is a finite attention budget ("context rot"). System prompt at the "right altitude"; sections with XML tags or
  Markdown headers; start minimal on the best model and add instructions from observed failures; canonical examples, not edge-case
  lists; minimal tool set with no overlap; just-in-time retrieval with lightweight references; long-horizon tools: compaction (tune
  for recall first, then precision; clear old tool results), structured note-taking, sub-agents that return 1,000 to 2,000-token
  summaries.

### 2.17 Anthropic `claude-cookbooks` patterns and Agent SDK notebooks
- `CB:patterns/agents/basic_workflows.ipynb` — `chain()`, `parallel()`, `route()` in a few lines each; the router asks for
  `<reasoning>` then `<selection>` in XML. `evaluator_optimizer.ipynb` — generator returns `<thoughts>` and `<response>`; evaluator
  returns `<evaluation>PASS|NEEDS_IMPROVEMENT|FAIL</evaluation>` and `<feedback>`; "evaluate only, do not solve"; loop keeps memory
  of prior attempts. `orchestrator_workers.ipynb` — orchestrator emits `<analysis>` and a `<tasks>` list; each worker gets the original
  task plus its subtask; suggests Opus orchestrator, Haiku workers.
- `CB:patterns/agents/prompts/research_lead_agent.md` and `research_subagent.md` — the best per-role prompt pair found. Lead:
  `<research_process>` (classify as depth-first, breadth-first or straightforward, then plan), `<subagent_count_guidelines>` (1 to
  20, "prefer fewer, more capable"), `<delegation_instructions>` (each sub-task gets objective, output format, background, key
  questions, sources and their quality bar, tools, scope boundaries). Sub-agent: an OODA loop, a tool-call budget (under 5 simple,
  about 10 hard, hard cap 20), `<think_about_source_quality>`, parallel tool calls, stop on diminishing returns.
- `CB:claude_agent_sdk/01_The_chief_of_staff_agent.ipynb` — `CLAUDE.md` as orientation ("context, not constraint"); Bash runs
  deterministic Python scripts for finance math (`hiring_impact.py`, `financial_forecast.py`, `decision_matrix.py`); output styles
  per audience; plan mode then save plan then approve then execute; slash commands as vetted prompts; `PostToolUse` hook writes an
  audit log of every file write; sub-agents in `.claude/agents/*.md`. SDK loads none of this unless `setting_sources` is set.
- `02_The_observability_agent.ipynb` — MCP-only agent (`disallowed_tools` removes Bash so it cannot bypass MCP); CI-health monitor.
- `03_The_site_reliability_agent.ipynb` — 12 MCP tools; write tools scoped (config dir only, docker-only commands, container
  allowlist); `PreToolUse` hooks validate the value (pool size 5 to 100) and block; aggregated `get_service_health` tool first;
  investigate-only run before any remediation run; "clear tool descriptions drive behavior more than elaborate prompts".
- `05_Building_a_session_browser.ipynb` — `list_sessions`, `get_session_messages`, `rename_session`, `tag_session` (soft delete via
  `__hidden`), `fork_session(up_to_message_id=...)` then `resume=`. All pure file reads on `~/.claude/projects/`.
- `07_Hosting_the_agent.ipynb` — "a Claude Agent SDK agent is a process". Four jobs: spawn, route, lifecycle, persist. Interface:
  `GET /health`, `POST /sessions/{id}/messages` (SSE). Map your session ID to the SDK's. Tiers: Docker, Modal, Kubernetes
  (gateway auth, pod per session, warm pool, egress allowlist). OTel via `OTEL_EXPORTER_OTLP_ENDPOINT`; `SessionStore` mirrors
  transcripts to shared storage.
- `08_Dynamic_workflows.ipynb` — "who holds the plan?" table (single agent, sub-agents, workflow). Fact-check example: extract,
  verify one agent per claim, skeptic on every "confirmed", report. Up to 16 concurrent agents, 1,000 per run; completed agents
  return cached results on relaunch; the script cannot touch files or shell; agents return values instead of writing report files;
  save to `.claude/workflows/`.
- `scheduled_repository_reviewer/` — cron-run, read-only reviewer: `permission_mode="dontAsk"`, `max_turns`, `max_budget_usd`,
  `setting_sources=[]` (the reviewed repo cannot configure its reviewer), `strict_mcp_config=True`, a path-confinement hook,
  `output_format` JSON schema with review ID, verdict and finding IDs; the next run resumes the session and must echo the prior IDs
  and list `resolved`; failures exit non-zero via `ResultError`; greppable `VERDICT` lines.

---

## 3. Template catalogue (seed for QMX built-in workflow templates)

Shape legend: `C` = code node, `A` = agent node, `J` = judge or verifier agent, `H` = human gate, `->` = edge, `||` = parallel
barrier, `|>` = per-item pipeline, `loop{}` = loop with the stop rule named.

| # | Name | What it does | Nodes / loop shape | When to use | Source |
|---|---|---|---|---|---|
| 1 | Chain with gate | Fixed steps; code checks a typed field between steps | A -> C(gate) -> A -> A | Task splits into known steps | `A-BEA`; `OAI-PAT` deterministic.py |
| 2 | Classify and act | Classifier picks a branch or specialist | A(classify, schema) -> C(switch) -> A_k | Distinct input types | `A-DW`; `CB:basic_workflows` route |
| 3 | Model router | Classifier studies the task, picks model and effort | A(small, research) -> C(pick model) -> A(model_k) | Cost varies a lot by task | `A-DW`; `OAI-COST` |
| 4 | Handoff triage | Specialist takes over the conversation | A(triage) -> handoff -> A(owner) | Specialist should answer directly | `OAI-PAT` routing.py |
| 5 | Manager with specialists | Lead keeps the final answer, calls specialists as tools | A(lead) <-> {A_i as tools} | One owner, several lenses | `OAI-PAT` agents_as_tools; `OAI-PF` |
| 6 | Fan-out and synthesize | Split into sections, run each clean, merge | C(split) -> A_1..n `||` -> A(synthesize) | Many independent parts | `A-DW`; `A-BEA` sectioning |
| 7 | Best-of-N | Same task N times, pick the best | A x N `||` -> J(pick) | Variance is high, picking is easy | `OAI-PAT` parallelization.py |
| 8 | Orchestrator-workers | Orchestrator invents the subtasks at runtime | A(plan, task list) -> A_i `||` -> A(merge) | Subtasks unknown in advance | `A-BEA`; `CB:orchestrator_workers` |
| 9 | Judge loop (evaluator-optimizer) | Generate, judge, feed back | loop{A(gen) -> J(pass/needs/fail)} stop: pass or max rounds | Clear criteria, feedback helps | `OAI-PAT` llm_as_a_judge; `CB:evaluator_optimizer` |
| 10 | Review-repair-validate | Find issues, fix a copy, execute, carry the delta | loop{A(review) -> A(repair copy) -> C(execute) -> J(score)} stop: pass, max, delta flat, needs human | Artifact can be executed or tested | `OAI-REPAIR` |
| 11 | Adversarial verification | A skeptic attacks each output | A_i -> J_i(refute) | Self-grading bias is a risk | `A-DW` |
| 12 | Deep verification | One checker per claim, optional source auditor | A(extract claims) -> J(claim_k) `|>` J(skeptic) -> A(report) | Reports, memos, investor-style docs | `A-DW`; `CB:08_Dynamic_workflows` |
| 13 | Rule-by-rule review | One verifier per rule, then a skeptic filters flags | C(rules) -> J(rule_k) `||` -> J(skeptic) | Rules the model keeps missing | `A-DW` |
| 14 | Generate and filter | Many ideas, dedupe, keep tested ones | A(gen many) -> C(dedupe) -> J(rubric) | Ideation with a quality bar | `A-DW` |
| 15 | Tournament / pairwise sort | Fresh agent per comparison holds no list | C(bracket) -> J(pair) rounds -> C(order) | Ranking many items by judgment | `A-DW` |
| 16 | Loop until done | Keep spawning until nothing new | loop{A(find) -> C(new?)} stop: no new findings or errors | Unknown amount of work | `A-DW` |
| 17 | Competing hypotheses | Theories from disjoint evidence face refuters | A(logs), A(data), A(files) -> J(refute each) -> A(verdict) | Root cause, "why did X drop" | `A-DW` |
| 18 | Quarantine triage | Untrusted readers have no privileges; actor sees summaries only | A(read, read-only) `|>` C(dedupe) -> A(act, privileged) -> H | Inbound queues, web content | `A-DW` |
| 19 | Scheduled brief | Cron run from bookmarks, ledger, re-check, confirm then record | C(cron) -> C(load prefs, bookmarks) -> A(read, decide) -> A(re-verify) -> C(post) -> C(confirm) -> C(ledger, run record) | Recurring digests and monitors | `A-AUTO` |
| 20 | Scheduled reviewer (resumed) | Each run resumes last session, echoes prior finding IDs | C(cron) -> A(resume, read-only, schema) -> C(continuity check) -> C(log VERDICT) | Recurring audits with memory | `CB:scheduled_repository_reviewer` |
| 21 | Initializer + incremental worker | First run builds the plan files; later runs do one item each | A(init: feature list JSON, progress file, init.sh) ; loop{A(bearings -> check -> one item -> test -> commit -> progress)} stop: all items pass | Multi-session builds | `A-LONG` |
| 22 | Investigate then remediate | Read-only diagnosis, human approves, scoped fix, verify | A(investigate, read tools) -> H -> A(fix, scoped write tools + PreToolUse validation) -> C(health check) | Ops and incidents | `CB:03_SRE` |
| 23 | Plan, approve, execute | Plan mode output saved, approved, then executed | A(plan mode) -> C(save plan) -> H -> A(execute, continue) | High-stakes or costly actions | `CB:01_chief_of_staff` |
| 24 | Approval gate | Pause a tool call, serialize state, resume later | A -> tool(needs_approval) -> C(save RunState) -> H -> A(resume) | Side effects, spending, deletion | `OAI-PAT` human_in_the_loop_server |
| 25 | Guardrail tripwire | Fast check before or after an agent; stop on trip | C/A(guard, fast model) -> A ; A -> C/A(output guard) | Input validation, leakage checks | `OAI-PAT` guardrails; `OAI-MIG` |
| 26 | Evidence-grounded analyst | Answer plus required artifacts, validators run as tools | A(analyst) -> C(evidence coverage) -> C(output contract) -> loop until clean | Finance and diligence answers | `OAI-LOOP` |
| 27 | Hub PM memo | Parallel specialists, editor flags missing parts, PM re-calls owner | A(PM) -> {quant, fundamental, macro} `||` -> A(editor) -> loop{missing? re-call owner} | Multi-lens research memo | `OAI-PF` |
| 28 | Data analyst | Discover tables, read definitions and corrections, read-only SQL, explain with SQL | A <-> {search_tables, search_context, query(read-only, 100 rows), save_memory(on request)} | Questions over QMX data stores | `OAI-DATA` |
| 29 | Research lead + sub-agents | Classify query type, size the team, delegate with full briefs | A(lead) -> A(sub_k, tool budget) `||` -> A(lead synth) -> A(citations) | Open research | `CB:patterns/agents/prompts` |
| 30 | Improvement loop | Traces to feedback to evals to gate to ranked changes to PR | C(collect traces) -> H + J(feedback) -> A(gen evals) -> H(review evals) -> C(eval gate) -> A(diagnose) -> A(code change) -> H(PR) | Any agent in production | `OAI-LOOP` |
| 31 | Hillclimb | One patch per round with held-out test | C(split) -> loop{A(analyze train fails) -> A(1 patch) -> C(run evals) -> C(keep/revert)} stop: stall 2-3 rounds -> A(bucket causes) | Tuning prompts, skills, model and effort | `A-EVAL` |
| 32 | Eval builder | Gather inputs, human confirms, choose cheapest grader, run diagnostics | A(gather) -> H(confirm inputs) -> A(grader) -> H(calibrate) -> C(baseline, CI, variance) | Before any optimization | `A-EVAL` |
| 33 | Session mining to rules | Mine corrections, cluster, verify each, distill | A(mine sessions) `||` -> A(cluster) -> J("would it have prevented a real mistake?") -> H -> C(write rule) | Turning repeated feedback into skills | `A-DW` |
| 34 | Split sync / async | Customer path minimal; QA and tags go to batch | A(sync answer) ; C(queue) -> A(batch tags, cheap model) | Latency-sensitive surfaces | `OAI-COST` |
| 35 | Run budget guard | Reserve worst case before each call, settle after | C(reserve) -> A(call) -> C(settle / block) wraps every A | Every unattended run | `OAI-BUDGET`; `A-AUTO` |

---

## 4. System-prompt design rules (collected)

**Structure**
1. Sections with XML tags or Markdown headers: background, instructions, tool guidance, output description (`A-CTX`). The research
   pair uses `<research_process>`, `<delegation_instructions>`, `<think_about_source_quality>`, `<maximum_tool_call_limit>`
   (`CB:patterns/agents/prompts`).
2. Write at the "right altitude": not hard-coded if-else logic, not vague slogans; heuristics plus concrete signals (`A-CTX`).
3. Start minimal on the strongest model; add rules only for failures you observed (`A-CTX`; `A-EVAL` fixes the root cause by
   rewriting the section, not rewording a line).
4. A few canonical examples, not a laundry list of edge cases (`A-CTX`). Worked examples per task type are fine (`OAI-PF` PM prompt).
5. State the output contract: required headers, a terminator (`END_OF_SECTION`), or a JSON schema via structured output (`OAI-PF`,
   `CB:scheduled_repository_reviewer`).
6. Put unknown-handling rules in writing: say "unknown", never fabricate, show conflicts, keep facts, inferences and questions apart
   (`OAI-LOOP`).
7. Give budgets in plain numbers: tool-call budgets by difficulty and a hard cap (`CB:research_subagent.md`), or tokens (`A-DW`).

**Static vs dynamic**
8. Static first, dynamic last: system prompt and tools are the cached prefix; task data goes last (`A-HAR`, `OAI-COST`).
9. Do not edit the system prompt mid-session; append updates as `<system-reminder>` messages (`A-HAR`).
10. Add task-specific rules in the user turn, only when the task triggers them (`OAI-LOOP` `build_user_prompt`).
11. Keep tool lists stable within a session; restrict per task with allowed-tools or tool search rather than adding or removing tools
    (`A-HAR`, `OAI-COST`, `OAI-DATA` `defer_loading`).
12. Operator preferences live in a file read fresh every run, from a store the agent cannot write; never copy them into the prompt
    (`A-AUTO`). If the file cannot be read, stop and say so.
13. Long task text goes in workspace files (`README.md`, `task.md`, `AGENTS.md`); instructions stay about behavior (`OAI-MEM`).

**Per-role prompts**
14. Lead and worker prompts differ. Lead: classify the task, size the team, write full briefs (objective, output format, context,
    key questions, sources and quality bar, tools, scope limits). Worker: plan, budget, OODA loop, source quality, stop on
    diminishing returns (`CB:patterns/agents/prompts`).
15. Manager prompts name each specialist tool, when to use the parallel tool vs the single one, the exact input schema, and "pass
    outputs verbatim" (`OAI-PF`).
16. Judges: "evaluate only, do not solve" (`CB:evaluator_optimizer`); rubric as checkable claims; judge is a different model; blind
    to variant (`A-EVAL`, `OAI-COST`). Do not copy the demo line "never give it a pass on the first try" (`OAI-PAT`) into production.
17. Specialist prompts may include an explicit "pushback" or "counter-thesis" section (`OAI-PF`).
18. Write tool descriptions as carefully as prompts; they drive behavior more than long prompts (`CB:03_SRE`, `A-BEA` appendix 2).

**Lifecycle prompts**
19. Compaction instruction names what must survive: current phase, cited facts, open questions, artifact paths, unresolved concerns
    (`OAI-MEM`).
20. Memory-writing instruction: workflow lessons only, never case facts (`OAI-MEM`).
21. Retry instruction: retry transient errors up to 2 more times; never retry a non-existent resource with the same input (`OAI-PF`).
22. Hillclimb rule: never paste failing transcripts into the prompt (`A-EVAL`).

**Versioning**
23. Version the whole harness, not the text: prompt + model + effort + tool policy + eval status (`promoted`, gate type) as one record
    (`OAI-LOOP` `AgentConfig`). Put a "do not modify the runtime config" line in the rendered instructions.
24. Emit the active harness version into every trace (`OAI-LOOP` synthetic `harness.config` span).
25. Keep prompts as files loaded at runtime with template variables like `{{.CurrentDate}}` (`OAI-PF`, `CB:research_lead_agent.md`).

---

## 5. Patterns that contradict or refine the QMA v2 direction (`20-qma-v2-direction.md` §3)

**§3.1 Two engines behind one `Engine` shape — refine.**
- OpenAI's own migration guide names the real difference: Claude Agent SDK puts the harness inside the sandbox, OpenAI keeps the
  harness in the trusted app and calls the sandbox as a tool (`OAI-MIG`). The `Engine` shape should declare where the loop runs and
  where compute runs. Secrets and approvals stay in the QMX process for both engines (vault outside sandbox in `A-AUTO` is the same
  idea).
- Anthropic's hosting notebook: "a Claude Agent SDK agent is a process"; hosting is spawn, route, lifecycle, persist
  (`CB:07_Hosting`). Confirms the RAM argument; QMX needs the session-ID map and a `SessionStore` mirror.
- New since §3 was written: OpenAI's hosted **Agents API** sessions (`OAI-DATA`) and an experimental hosted multi-agent model
  (`OAI-PAT`); Anthropic's **Managed Agents** with cron deployments, vaults, memory stores and budgets (`A-AUTO`). These are
  already-solved hosted versions of parts of the "orb". Not a contradiction; a buy-vs-build line item.

**§3.2 Long-running orchestrator kept alive by resume plus progress file — refine, partly contradict.**
- Confirmed: compaction is not enough; progress file plus git history plus a JSON feature list is what worked (`A-LONG`).
- Contradiction in emphasis: Anthropic's scheduled automations start a **fresh session every run** and keep continuity in memory
  stores (`A-AUTO`); the scheduled reviewer resumes but calls a scheduled session reset a safeguard (`CB:scheduled_repository_reviewer`);
  goal drift grows with each compaction (`A-DW`). Proposed reading: the orchestrator is a **role with durable state**, served by a
  chain of sessions that rotate on a schedule or at phase ends, not one immortal session.
- Split its state three ways: operator preferences (read-only to the agent), agent state (bookmarks, ledger, run records, notes),
  reviewed artifacts (the source of truth) (`A-AUTO`, `OAI-MEM`).
- Use JSON for the item list the agent must not rewrite (`A-LONG`), and a "get your bearings" ritual at the start of every session.

**§3.3 Plugins as the organogram unit; OpenAI "has no plugin system" — refine.**
- OpenAI has no plugins, but it now has **skills** in the same `SKILL.md` format (`.agents/skills/*/SKILL.md`, sandbox-backed skill
  execution) and publishes the mapping from `.claude/` to its own layout (`OAI-MIG`). Half the loader is a documented mapping.
- Hooks do not map 1:1: OpenAI hooks only observe; blocking goes to guardrails or `needs_approval` (`OAI-MIG`). The QMX plugin hook
  format needs a "policy" kind that compiles to a Claude `PreToolUse` hook or an OpenAI tool guardrail.
- Workflow templates can ship inside a plugin's skill folder, read as templates, not scripts (`A-DW`).
- Plugin loading needs explicit `setting_sources` in the Claude SDK, or nothing loads (`CB:01_chief_of_staff`).

**§3.4 QMX's own graph instead of LangGraph — confirmed, with a warning and a vocabulary.**
- OpenAI built a hosted visual graph (Agent Builder: typed edges, CEL if/else and while, human approval, transform, set state) and is
  **shutting it down on 2026-11-30**; its export "does not convert your workflow graph" (`OAI-AB`). Both vendors now keep the plan in
  code (`OAI-MA` "orchestrating via code"; `A-DW` scripts). QMX graph JSON should therefore be a **view and storage of code-level
  primitives**, not a separate engine: `agent(schema, model, isolation)`, `parallel` (barrier), `pipeline` (per item), `phase`, plain
  code between nodes.
- Node vocabulary to borrow: Agent Builder's nodes plus Claude's primitives. Runner limits to copy: concurrency cap (Claude uses 16),
  run cap (1,000), cached results for completed nodes on resume, nodes return values rather than writing report files, the
  orchestration layer itself cannot touch files or shell (`CB:08_Dynamic_workflows`).
- The six built-in patterns in §3.4 are confirmed exactly (`A-DW`); this file's §3 catalogue adds about 29 more.

**§3.5 Every agent node is a loop with an evidence stop rule and a separate verifier — refine.**
- Stop rules are now concrete: pass; max attempts; delta stopped shrinking; needs a human (`OAI-REPAIR`). Add "no new findings"
  (`A-DW`) and budget reached (`A-AUTO`, `OAI-BUDGET`).
- "Every node gets a separate verifier" is too strong. "Most traditional coding tasks do not need a panel of 5 reviewers" (`A-DW`);
  `A-BEA` says add complexity only when it measurably helps. Use a deterministic validator by default (execute, schema, evidence
  coverage); add an agent verifier where self-preferential bias matters or stakes are high. A judge pass never overrides a code
  failure (`OAI-COST`).
- Self-improvement "lessons write back to skills with approval" — refine: human approval alone is not enough. Changes should pass an
  eval gate with a held-out split and noise check (`A-EVAL`), and memory must hold workflow lessons only (`OAI-MEM`). Candidate rules
  from session mining are adversarially checked first (`A-DW`).

**§3.6 Contabo server as QMX's own orb — confirmed; add specifics.**
- Health route, session map, transcript mirror, OTel env vars, egress allowlist, gateway auth outside the agent (`CB:07_Hosting`).
- Unattended runs: read-only tools where only reading, `dontAsk` permission mode, turn and dollar caps, path-confinement hook,
  `setting_sources=[]` for anything that reads untrusted repos (`CB:scheduled_repository_reviewer`); per-run budget at 3 to 5x a
  normal run (`A-AUTO`).

**§3.7 Memory — refine.** Preferences read-only to the agent and re-read each run (`A-AUTO`); SDK memory for workflow lessons only
(`OAI-MEM`); app-owned corrections store with personal/team scope, written only on explicit request (`OAI-DATA`).

**§3.8 Tracing — confirmed; one trap.** OpenAI: use `set_trace_processors([local_exporter])` to replace the uploader
(`OAI-LOOP`); `add_trace_processor` keeps uploading (`OAI-PF`). Or disable tracing entirely (`OAI-MEM`). Claude: OTel env vars
(`CB:07_Hosting`). Log the harness version with every trace (`OAI-LOOP`).

**Usage-balancing router (direction item, not in §3) — refine.**
- Caches are per model; switching models mid-session breaks them; use a sub-agent for the cheaper model (`A-HAR`). The router should
  choose at session start or sub-agent spawn, never per turn.
- Route by step and by effort level, not only by provider: nano/mini/full per step and low/high effort (`OAI-COST`); a lower effort on
  a stronger model can beat a higher effort on an older one (`A-EVAL`).
- Balance on "cost per verified result" including failed attempts (`OAI-COST`), and wrap every unattended run in a reserve-and-settle
  budget guard with a shared atomic store (`OAI-BUDGET`).

**Deterministic first — confirmed by both vendors.** Code gates between agents (`OAI-PAT`), deterministic scripts for finance math
(`CB:01_chief_of_staff`), aggregated health tool before agent reasoning (`CB:03_SRE`), execute-first validation (`OAI-REPAIR`), and the
optimizer's own top recommendation to add a deterministic fact ledger (`OAI-LOOP`). Let the model write code that chains tool calls
so raw data never enters context (`A-HAR`; `OAI-DATA` programmatic tool calling).

---

## 6. What could not be read, or was read only in part

- **OpenAI, title only:** every §2.2 item not marked [R]. The one most worth reading next is harness-aware evaluation of plugins.
- **Agent Builder template gallery** needs a platform login; only the docs pages were read (not the safety page).
- **Partly read:** `OAI-COST` round 1 to 4 prose was partly lost in extraction (tables, knobs, tuning order and conclusions were read);
  long code cells in `OAI-LOOP`, `OAI-PF` and the Claude notebooks were skimmed for structure, not read line by line.
- **Claude cookbooks not read:** `00` research agent, `04_migrating_from_openai_agents_sdk` (reverse mapping, worth a later read), `06`
  vulnerability agent, `async_multi_agent_orchestration`, `latency_multi_agent`, `prompts/citations_agent.md`.
- **Anthropic posts linked but not read:** how Managed Agents was built, the multi-agent research system, harness design for
  long-running apps, writing tools for agents, and the `code.claude.com/docs/en/workflows` reference page.
- Browser tools were not used; firecrawl full-page scrape was used instead (one rate-limit pause, both pages retried and read).
  Model names and prices are quoted as the sources state them and were not checked against price pages.
