# Vendor cookbooks: worked agent patterns for QMX

Date: 2026-10-12. Researcher lane: worked examples (cookbooks), not advice pages.

## 0. Scope, sources and honesty notes

- Sources were cloned shallowly to `D:\QMX-research\sources\repos\claude-cookbooks` (full) and
  `D:\QMX-research\sources\repos\openai-cookbook` (123 agent-relevant `.ipynb`/`.md` files extracted from git
  objects; a full checkout fails on Windows because of an invalid path under `examples/data/hotel_invoices/`).
  Code was read, never executed.
- Index of every agent-relevant item (147 Claude + 123 OpenAI files, one line each):
  `D:\QMX-research\sources\cookbooks-index.md`. The one-liners are generated from each file's title and lead
  sentence, so they describe what the author says the item shows.
- Text extracts (markdown cells in full, code cells cut at 60 lines) are in `D:\QMX-research\sources\text\`.
  Per-batch reading notes are in `D:\QMX-research\sources\notes\batch00,03,04,05,07,08,09,10,11,12.md`.
- **Scope was narrowed mid-task** after a usage-limit stop from the coordinator. Fully covered: prompt caching,
  compaction, context editing, memory, subagents, long-running/scheduled agents, model routing, budgets, plus
  everything in the ten batch-note files. **Gaps:** reader batches 01, 02 and 06 were stopped before writing notes.
  I read their highest-priority items myself (`claude_agent_sdk/08_Dynamic_workflows`, `managed_agents/CMA_*`
  plan-big/advisor/budget/memory/production/gate/grader, OpenAI `agents_sdk/building_reliable_agents_memory_compaction`,
  `session_memory`, `context_personalization`, `parallel_agents`, `multi-agent-portfolio-collaboration`), but these
  were **not** read in depth: `CMA_coordinate_specialist_team`, `CMA_watch_subagents_live`, `CMA_orchestrate_issue_to_pr`,
  `CMA_iterate_fix_failing_tests`, `CMA_explore_unfamiliar_codebase`, `CMA_prompt_versioning_and_rollback`,
  `CMA_use_skills_from_a_repo`, `CMA_pin_inference_geo`, `CMA_with_mongodb_atlas`, `data_analyst_agent`,
  `slack_data_bot`, `sre_incident_responder`, `misc/batch_processing`, `misc/building_evals`, OpenAI
  `agents_sdk/dispute_agent`, `evaluate_agents`, `security_scanners_with_agents_sdk`,
  `sandboxed-code-migration`, `migrate-from-claude-agent-sdk`, `computer_use_with_daytona`.
- **The engineering-blog and Codex-docs reader was stopped before writing its notes.** Claims below about
  Anthropic engineering posts and Codex hooks/skills/automations/memories docs come only from what the
  cookbooks themselves say and cite. Treat any such claim as UNVERIFIED against the post itself.
- Model names, prices and beta headers below are quoted from the cookbooks as of the clone date
  (2026-10-12). Several (e.g. Fable 5, Opus 4.8, GPT-5.6 Luna/Sol) are newer than my training data; I report
  them as the source states them.
- LangChain/Deep Agents class names were checked against the local clones in
  `D:\QMX-research\sources\repos\langchain` and `...\deepagents` (paths given where cited).

### The QMX-specific caveat that governs everything below

QMX's main model runs on the operator's subscription through CLIProxyAPI. Most of the **server-side**
features in the Claude cookbooks (Managed Agents sessions, `budget`, `multiagent` rosters, advisor entries,
memory stores, server-side compaction, context-editing betas, Batch API, server-side fallback) are Claude API
features billed per token and gated by `anthropic-beta` headers. Whether CLIProxyAPI forwards those headers and
bodies to a subscription-authenticated backend is **UNVERIFIED**. Also, on a subscription the "cost" of a token
is quota and rate-limit consumption, not dollars. The practical rule this produces: **build every pattern
client-side in LangChain middleware, so it works on any provider; use the vendor's server-side version only
where it is proven to pass through the proxy.** The cheap background models (DeepSeek, GPT-6 Luna/Sol) are
per-token, so the dollar figures do apply to them.

---

## 1. Prompt caching (the largest cost lever in both cookbooks)

**What it does.** The provider reuses the computed prefix of a prompt (system prompt, tools, earlier turns),
so later calls skip re-processing it. Claude: reads cost 0.1x base input, writes cost 1.25x, a 1-hour TTL costs 2x;
"reducing latency by >2x and costs by up to 90%" (`claude-cookbooks/misc/prompt_caching.ipynb`). OpenAI:
automatic from 1,024 tokens, hits in 128-token increments, up to ~80% lower TTFT and up to 90% lower input
cost; the measured TTFT gain was 7% at 1,024 tokens and 67% at 150k+ (`openai-cookbook/examples/Prompt_Caching_201.ipynb`).

**Minimal mechanism.**
- Claude automatic: top-level `cache_control={"type": "ephemeral"}` on `messages.create`; the breakpoint slides
  to the last cacheable block each turn. Explicit: put `cache_control` on up to 4 content blocks, with mixed
  TTLs. Minimum cacheable length is 1,024 tokens for Sonnet and 4,096 for Opus and Haiku 4.5; default TTL 5 min,
  refreshed on each hit (`claude-cookbooks/misc/prompt_caching.ipynb`).
- OpenAI: nothing to switch on. `prompt_cache_key` improves routing stickiness to the same engine (notes say
  about 15 RPM per prefix+key, `notes/batch12.md`). `prompt_cache_retention: "24h"` extends retention.
  `tool_choice.allowed_tools` restricts which tools may be called **without changing the cached tool list**
  (`Prompt_Caching_201.ipynb`).
- Cache breakers, listed by both vendors: a timestamp or request ID in the system prompt; changing the tool set
  or tool order; **switching model mid-conversation (caches are per model)**; changing `effort` /
  reasoning effort mid-conversation; and compacting or rewriting history on every turn
  (`claude-cookbooks/cost_optimization/cost_optimization.ipynb`; `Prompt_Caching_201.ipynb` §4).
  OpenAI's advice for debug timestamps: move them into `metadata`.
- Measured result: the Claude cost notebook ends at "`sonnet · medium` with explicit breakpoints", a **13x**
  reduction against the unoptimised Opus-high baseline of about $0.29 per task
  (`cost_optimization/cost_optimization.ipynb`).

**QMX fit.** Every agent. It matters most for the general copilot (long system prompt plus many tools) and for
background workflow agents on cheap per-token models.

**LangChain/Deep Agents mapping.** `AnthropicPromptCachingMiddleware`
(`langchain/libs/partners/anthropic/langchain_anthropic/middleware/prompt_caching.py`) places breakpoints. There
is also a `FireworksPromptCachingMiddleware` in the clone. For OpenAI-class and DeepSeek models caching is
implicit; QMX has to keep the prefix byte-stable itself.

**Design rules for QMX that follow from this.**
1. Assemble the prompt in a fixed order: static persona and rules, then the tool list (a stable,
   alphabetised superset), then skill metadata, then session memory, then the conversation, then volatile
   state (clock, prices, positions) **in the newest user turn only**.
2. Never put the live market clock or account equity in the system prompt.
3. When the user switches model in the UI, show "cache will be rebuilt" (because caches are per model).
4. Pin `effort` for the life of a thread.

**Cost implication.** This is the cheapest win available. One caveat from `cost_optimization.ipynb`: dynamic
tool loading (tool search) and frequent compaction both work against the cache, so tune them together, not
separately.

## 2. Speculative cache warming (latency trick for the desktop UI)

**What.** While the user is still typing, send a `max_tokens=1` request with the same context, so the cache is
warm by the time they press Enter (`claude-cookbooks/misc/speculative_prompt_caching.ipynb`). The authors'
advice: start warming when the input field gets focus; use byte-identical context; check
`cache_read_input_tokens`.

**QMX fit.** General, Lab and Portfolio copilots. On a large prefix (an attached backtest report or a
strategy file) this hides most of the time to first token.

**Mapping.** No built-in equivalent. It is a few lines in the copilot UI controller, calling the same
`ChatAnthropic` with `max_tokens=1`.

**Cost.** One cache write per focus event (1.25x on the prefix). Debounce it, and warm only when the prefix
is above the minimum and has changed since the last warm.

## 3. Compaction (keeping long runs alive)

**What.** When the context grows past a threshold, replace the history with a model-written summary and
carry on.

**Minimal mechanisms shown.**
- SDK-side (Claude `tool_runner`): `compaction_control={"enabled": True, "context_token_threshold": N,
  "model": "claude-haiku-4-5", "summary_prompt": ...}`. It injects a summary request as a user turn, the model
  replies inside `<summary>` tags, history is cleared, and the run resumes. In the 5-ticket demo, cumulative
  input dropped from about 150k to 79k tokens. Threshold guidance: 5k–20k for sequential per-item work, 50k–100k
  for multi-phase work, default 100k. Stated limitation: it misbehaves with server-side tools such as web search
  and server-side thinking, because cache tokens accumulate and trigger it early
  (`claude-cookbooks/tool_use/automatic-context-compaction.ipynb`).
- Server-side (Claude): the notebook recommends server-side compaction on Opus 4.6+. The batch-04 notes record
  the type `compact_20260112`, header `compact-2026-01-12`, a minimum trigger of 50K and a default of 150K
  (`tool_use/context_engineering/context_engineering_tools.ipynb`, `notes/batch04.md`).
- OpenAI: `context_management=[{"type":"compaction","compact_threshold":N}]` on `responses.create`
  (`Prompt_Caching_201.ipynb`). The Agents SDK offers `Compaction()` (automatic), `StaticCompactionPolicy`
  (a threshold) and forced checkpoints via `OpenAIResponsesCompactionSession.run_compaction({"force": True})`
  at phase boundaries. The authors' advice: "Keep cited facts in generated artifacts, not only in compacted
  conversation state" (`openai-cookbook/examples/agents_sdk/building_reliable_agents_memory_compaction.ipynb`).
- Manual chat-loop compaction for tool-less chat: track tokens, summarise at the threshold, replace history,
  and **show "Summarizing conversation..." in the UI** (`automatic-context-compaction.ipynb`).

**When not to compact** (the authors' list): short tasks, tasks that need a full audit trail, and iterative
refinement where every step depends on exact earlier detail.

**QMX fit.** Lab long experiments and background workflow agents (per-item loops such as "scan 40 symbols"),
plus the general copilot's long chats.

**Mapping.** `SummarizationMiddleware`
(`langchain/libs/langchain_v1/langchain/agents/middleware/summarization.py`). It takes a separate summariser
model, so the summary can run on a cheap model, as the cookbook does with Haiku. Deep Agents enables
summarisation by default (its middleware list also has `CompactSummarizationMiddleware`, found in the clone).

**Cost.** Compaction invalidates the cache from the rewrite point onward. "Jagged compaction" (let bulky
results pile up, then prune in one pass at a natural boundary) keeps the array byte-stable between prunes
(`cost_optimization.ipynb` §Agent-loop efficiency). Use a cheap summariser.

## 4. Instant (background) session-memory compaction

**What.** Rather than making the user wait about 40 seconds at the limit, a background thread starts building
`session-memory.md` once a **soft** threshold is crossed and keeps updating it (every turn, or about every 10k
tokens / 3+ tool calls). At the hard limit the prebuilt memory is swapped in instantly. The background
summariser sends the **same prefix with `cache_control`**, so it hits the main chat's cache: about $0.00285
instead of $0.015 per update, roughly 80% cheaper. The prompt rules: weight recency heavily, keep user
corrections verbatim, and record intent, completed work, errors, active work and key references
(`claude-cookbooks/misc/session_memory_compaction.ipynb`).

**QMX fit.** The general copilot and Lab copilot. This is the right UX for a desktop app because the user never
sees a compaction stall.

**Mapping.** No off-the-shelf middleware does this asynchronously (UNVERIFIED; `SummarizationMiddleware` runs
inline before the model call). Build it as a custom `AgentMiddleware` that launches an asyncio task after each
model call and writes into the Deep Agents filesystem/store; a `before_model` hook swaps it in at the hard limit.

**Cost.** One extra summariser call per update, mostly cache reads. The caching trick needs the summariser to use
the same model as the main chat, which conflicts with using a cheap summariser. Choose per thread: cheap model
plus cache miss, or main model plus cache hit.

## 5. Context editing: clearing tool results and thinking

**What.** Server-side removal of old bulky blocks while the `tool_use` record stays.
- `clear_tool_uses_20250919` with `trigger` (for example `input_tokens` 30–35k), `keep` (the last N tool
  uses), `clear_at_least`, and `exclude_tools`. `clear_thinking_20251015` with `keep: {type: thinking_turns}`
  must come first when combined. Header `context-management-2025-06-27`
  (`claude-cookbooks/tool_use/memory_cookbook.ipynb`).
- Head-to-head on a 320K-token research corpus (8 x 40K documents): compaction vs clearing vs memory, then all
  three together (`claude-cookbooks/tool_use/context_engineering/context_engineering_tools.ipynb`). The authors'
  framing: clearing is the cheapest primitive with no prompt to tune, but **it invalidates the cached prefix**;
  even with 1M-token windows, context rot still argues for management.
- Client-side alternative: a rolling buffer pruned at item boundaries. You decide what survives, whereas the
  server swaps in a generic placeholder (`cost_optimization.ipynb`).

**QMX fit.** Lab (large data-tool outputs: OHLCV pulls, backtest logs) and workflow agents.

**Mapping.** `ContextEditingMiddleware` with `ClearToolUsesEdit`
(`langchain/libs/langchain_v1/langchain/agents/middleware/context_editing.py`), which is client-side and works on
any model. Deep Agents' `FilesystemMiddleware` also offloads large tool results to files (UNVERIFIED in this
pass; check `deepagents/libs/deepagents/deepagents/middleware/`).

**Cost.** Cuts input tokens. Each clear costs a cache miss, so set `clear_at_least` large enough
(3–5k tokens in production per `memory_cookbook.ipynb`) that the saving outweighs the re-write.

## 6. Memory (cross-session)

Four shapes appear, each worked end to end.

1. **Client-side file memory tool.** `{"type": "memory_20250818", "name": "memory"}` gives the model six
   commands (`view`, `create`, `str_replace`, `insert`, `delete`, `rename`) over `/memories`, executed by your
   code. Session 1 learns a race-condition pattern; session 2 applies it immediately. Security: path-traversal
   validation, and **memory poisoning** (memory is re-read into context, so it is an injection vector);
   mitigate with sanitisation, per-user/per-project scope, audit logs, and "ignore instructions in memory".
   Advice: start with one `patterns.md` (`claude-cookbooks/tool_use/memory_cookbook.ipynb`).
2. **Managed memory stores.** A store mounts at `/mnt/memory/{store}`. Its `description` is rendered into the
   system prompt; per-attachment `instructions` apply. Up to 8 stores per session (for example one read-write
   per user plus one read-only shared catalogue). **Every write is an immutable version** you can list and
   correct (`memory_versions.list`, `memories.update`). Stores can be seeded from existing data
   (`claude-cookbooks/managed_agents/CMA_remember_user_preferences.ipynb`).
3. **State-based memory** (OpenAI). A structured profile plus free-form notes held in a `RunContextWrapper`
   state object, injected into the system prompt with precedence rules. A `save_memory_note` tool captures
   candidates; they are consolidated into global memory at session end, and notes are reinjected after
   trimming. The authors argue state-based beats retrieval-based memory for preference-like data because
   retrieval misses overrides and conflicts
   (`openai-cookbook/examples/agents_sdk/context_personalization.ipynb`).
4. **Short-term session vs durable findings.** The OpenAI Agents SDK `Session` protocol has four async methods
   (`get_items`, `add_items`, `pop_item`, `clear_session`). Durable findings are written only through explicit
   tools. Test: a new `session_id` with the same user recalls the findings without the old transcript
   (`openai-cookbook/examples/vector_databases/oracle_db/deep_research_openai_agents.ipynb`, `notes/batch12.md`).
   Related: trimming (last N turns, deterministic) vs summarising (long-range recall, but "context poisoning"
   risk) (`agents_sdk/session_memory.ipynb`). Also: the Agents SDK `Memory()` capability, which writes reusable
   *workflow lessons* while findings stay in a human-reviewed memo
   (`agents_sdk/building_reliable_agents_memory_compaction.ipynb`).

Also: the Claude Agent SDK treats `CLAUDE.md` as memory loaded from `cwd` ("context, not constraint"), and
`setting_sources` must include `"project"`/`"local"` for it to load (`claude_agent_sdk/01_The_chief_of_staff_agent.ipynb`,
`notes/batch00.md`).

**QMX fit.**
- Shape 2 (versioned, user-auditable store) is the right model for the general and Portfolio copilots: the
  operator can see and correct what the agent "knows".
- Shape 4 (session vs durable) suits Lab and workflow agents.
- Portfolio memory must never hold risk or sizing rules; those live in the governing docs (operator ruling,
  memory index).

**Mapping.**
- LangGraph checkpointer = session; LangGraph `Store` = durable.
- Deep Agents `MemoryMiddleware` (`deepagents/libs/deepagents/deepagents/middleware/memory.py`) plus a
  `CompositeBackend` routing `/memories/` to a store (UNVERIFIED in this pass).
- Versioning is not built in: QMX should write every memory change as an append-only row (who, which session,
  diff) so it can show a memory history panel.

**Cost.** Small: memory files are short. The risk is unbounded growth, so cap size and run a periodic cheap
consolidation job.

## 7. Subagents (clean-context delegation)

**What.** A parent hands a self-contained subtask to a fresh context and gets back a distilled result.

**Worked forms.**
- Claude Agent SDK: subagents via the Task tool, defined in `.claude/agents/*.md` or as a programmatic
  `AgentDefinition` (for example `financial-analyst` and `recruiter` with their own tools and scripts). Hooks
  log every subagent tool use to an audit file (`claude_agent_sdk/01_The_chief_of_staff_agent.ipynb`,
  `chief_of_staff_agent/.claude/agents/`).
- Opus writes a targeted prompt, Haiku subagents extract from each PDF page in parallel, Opus synthesises
  (`claude-cookbooks/multimodal/using_sub_agents.ipynb`).
- In-memory hub with `send_message`/`wait_for_message` (messages appended to the next tool result, no polling),
  `create_subagents`/`get_status`/`kill_subagents`, an Opus lead with Haiku workers, and a shared "TeamClock"
  latency budget (`patterns/agents/async_multi_agent_orchestration.ipynb`, `latency_multi_agent.ipynb`,
  `notes/batch03.md`).
- Research lead/subagent prompts with tool and source budgets per subagent and a maximum of 20 subagents
  (`patterns/agents/prompts/research_lead_agent.md`, `research_subagent.md`).
- Cost view: "a subagent is an independent call, so you can give it a different (often cheaper) model string",
  but it "starts from a fresh prefix with no cache shared with the parent", so it wins only when the subtask's
  intermediates are bulky and the parent does not need them (`cost_optimization.ipynb`).
- OpenAI: **agents-as-tools** (the manager stays in control and calls specialists as tools; used for
  auditability) vs **handoffs** (control transfers). The Head PM runs fundamental, macro and quant specialists
  in parallel via a `run_all_specialists_parallel` tool with `parallel_tool_calls=True`
  (`openai-cookbook/examples/agents_sdk/multi-agent-portfolio-collaboration/multi_agent_portfolio_collaboration.ipynb`).
  Use `asyncio.gather` when the fan-out should be deterministic and low-latency; use agents-as-tools when the
  planner should decide (`agents_sdk/parallel_agents.ipynb`).

**QMX fit.** All three copilots delegate. The Lab copilot uses research, data-pull and backtest-runner
subagents. The Portfolio copilot uses fundamental, macro and quant specialists, which is a near-direct template
from the OpenAI portfolio notebook. The general copilot delegates to the Lab and Portfolio subgraphs.

**Mapping.** Deep Agents `SubAgentMiddleware` (the `task` tool;
`deepagents/libs/deepagents/deepagents/middleware/subagents.py`) and `AsyncSubAgentMiddleware`
(`async_subagents.py`, for background subagents; behaviour UNVERIFIED in this pass). Each subagent can bind its
own model, so cheap models can do the reading.

**Cost.** Delegation saves money only when the subtask's reading is heavy. Each worker has a fixed setup
overhead (see §8).

## 8. Coordinator / "plan big, execute small"

**What.** A frontier coordinator with **no tools of its own**, only a `multiagent` roster, gets
`create_agent`, `send_to_agent`, `wait_for_agents` and `list_agents`. Cheap workers scoped to
`web_search`/`web_fetch` do all the reading in parallel and return distilled reports. The megabytes of fetched
pages never enter the coordinator's context. Per-thread cumulative `usage.list_cost` meters each worker, and a
session `budget` caps the whole team.

**Findings stated by the authors** (`claude-cookbooks/managed_agents/CMA_plan_big_execute_small.ipynb`):
- Compare the team against a solo frontier agent only at **matched verification rigor**.
- **Delegation has a floor cost**: splitting into more, narrower briefs raised the bill.
- The split does not pay on narrow questions, or when the coordinator answers from memory. Watch for runs with
  no spawns.
- The roster is snapshotted at coordinator creation.

**QMX fit.** Lab research ("survey 20 papers / 30 symbols") and background workflow agents. This is the
canonical shape for "Opus main, cheap models for background work".

**Mapping.** Deep Agents with a main agent on Opus and `SubAgent` specs on DeepSeek or GPT-6 Luna. For fan-out
the script controls, use LangGraph `Send` (map-reduce) instead (see §10).

**Cost.** Token-heavy reading moves to models priced several times lower. Worth it for coverage tasks;
counterproductive for narrow ones.

## 9. Advisor (a cheap driver consults a strong model mid-turn)

**What.** Add `{"type": "advisor", "model": ...}` to the roster. The working model gets a no-argument `advisor`
tool; the advisor reads the whole conversation up to the call and its advice is injected. At most one advisor;
only the primary thread consults. Advisor tokens bill on top, with no per-consultation cap, so use a session
budget. Output may come back `redacted` for some advisor models, but the driver still reads it
(`claude-cookbooks/managed_agents/CMA_consult_an_advisor.ipynb`).

**Measured.** In the claims eval, a Haiku driver with an Opus advisor recovered some misses; a Sonnet driver did
no better than alone. Without a cheap signal to gate the consult, the driver has to recognise hard cases
itself (`cost_optimization.ipynb`).

**QMX fit.** Background workflow agents on DeepSeek/GPT-6 Luna that occasionally meet a judgment call (for
example "is this anomaly a data error or a regime change?").

**Mapping.** No built-in. It is a small custom tool that calls Opus with the serialized thread. Through
CLIProxyAPI this costs subscription quota rather than dollars (UNVERIFIED).

**Cost.** Cheap when rare. Put a hard per-run cap on consultations.

## 10. Dynamic workflows (code-orchestrated fan-out)

**What.** Claude writes a JavaScript orchestration script and launches it with the `Workflow` tool, which runs
in the background. `agent(prompt, {label, phase, schema, model})` spawns a clean-context worker,
`parallel()` is a barrier, `pipeline()` streams items through stages, and plain JS between calls does exact,
free filtering and merging. Results come back as return values, not files. Failed stages resume without
re-running completed agents.

**Key contrast** (the authors'): with subagents "nothing guarantees that it delegates every piece"; a workflow
makes verification structural and turns the orchestration into a re-runnable artifact. The price is tokens:
the demo cost about $2–4 (`claude-cookbooks/claude_agent_sdk/08_Dynamic_workflows.ipynb`).

**QMX fit.** Lab copilot ("check every claim in this research note", "run this analysis over the whole
watchlist") and background workflow agents. This is very close to QMX's own notion of workflows the operator
can see and re-run.

**Mapping.** A LangGraph `StateGraph` with `Send` fan-out is the native equivalent. The Lab copilot can **emit
a graph or workflow definition** for the UI to show, save and re-run, rather than doing ad-hoc delegation.

**Cost.** Highest token use of the multi-agent patterns. Reserve it for tasks where coverage must be
guaranteed.

## 11. Model routing, effort and fallback

**Worked evidence.**
- Effort sweep, then a drop in tier: Opus high → … → `sonnet · medium` held 10/10 and `sonnet · low` slipped.
  Decomposing to cheap subagents came out about 90% under the Opus baseline but missed one claim. Batch
  restructuring came to about half of the interactive frontier cost. "Measure cost per completed task", not
  per token (`claude-cookbooks/cost_optimization/cost_optimization.ipynb`).
- OpenAI tiering: nano for triage, extraction and tags; mini for routine work; the full model for high-risk
  cases. The notebook maps GPT-5.6 Luna to the nano tier and Sol to the full tier (Terra = mini per
  `notes/batch05.md`). Metric: "blended cost per verified resolution"
  (`openai-cookbook/examples/agent_optimization/optimizing_agents_for_cost_and_quality.ipynb`).
- Escalation ladder: a cheap model for breadth and filtering, a strong model for depth and critique. Pairwise
  tournament ranking beats absolute 1–10 scoring; a separate critic persona avoids self-justification
  (`openai-cookbook/examples/partners/model_selection_guide/model_selection_guide.ipynb`, `notes/batch11.md`).
- Server-side fallback: `fallbacks: [{"model": ...}]` plus header `server-side-fallback-2026-06-01`. A
  `{"type":"fallback"}` content block marks each switch; `usage.iterations` gives per-model usage; a cached
  prefix carried to the fallback bills as a cache read
  (`claude-cookbooks/fable_5_fallback_billing/guide.ipynb`).
- A model-improvement order before fine-tuning: model and reasoning budget → prompt → examples/context →
  tools → guardrail models → fine-tuning (`partners/eval_driven_system_design/receipt_inspection.ipynb`,
  `notes/batch10.md`).

**QMX fit.**
- The general copilot routes by intent: cheap classifier, then Opus for real work.
- Workflow agents default to cheap models with escalation.
- The Portfolio copilot stays on the strong model for anything touching sizing.
- Show the active model and the reason for any switch in the UI.

**Mapping.**
- `ModelFallbackMiddleware`: `langchain/libs/langchain_v1/langchain/agents/middleware/model_fallback.py`.
- Retries: `ModelRetryMiddleware` and `ToolRetryMiddleware`.
- Per-node model binding in LangGraph.
- A dynamic-model middleware (`ConfigurableModelMiddleware` exists in the clone; exact API UNVERIFIED).
- Use the fallback chain Opus via proxy → Opus via API key, or Opus → a cheap model, so a proxy or quota outage
  never stops a background run.

**Cost.** Remember that a route change breaks the cache (§1). Route at the start of a thread or subagent, not
per turn.

## 12. Budgets and spend caps

**Mechanisms.**
- **Managed session budget** (`claude-cookbooks/managed_agents/CMA_cap_session_spend.ipynb`):
  - Set at creation: `budget={"type":"limit","max_list_cost":{"currency":"USD","amount":"10"}}`. The amount is
    in minor units, so `"10"` means $0.10.
  - The cap covers every thread, including subagents, and is checked between model requests, so expect
    one-request overshoot.
  - Hitting it gives `budget_reached`, which is a **pause, not a failure**. Raising the cap resumes the turn.
  - A budget cannot be added after creation, and removing it is one-way.
  - There is a `session.budget_reached` webhook.
- **Client-side Agent SDK** caps: `max_turns` and `max_budget_usd`, which raise `ResultError`
  (`error_max_turns` / `error_max_budget_usd`)
  (`claude_agent_sdk/scheduled_repository_reviewer/scheduled_repository_reviewer.ipynb`).
- **Per-run spending controller** (OpenAI): before each call, count input tokens and **reserve the worst-case
  cost**; after it, settle the actual cost and release the rest. Block when the remaining budget cannot cover
  the reserve. Uses exact `Fraction` money and a lock
  (`openai-cookbook/articles/per_run_spending_controller_responses_api.md`).
- Codex Goals have a "budget-limited" state that is not completion: stop substantive work, summarise, and name
  the next step (`openai-cookbook/examples/codex/using_goals_in_codex.ipynb`).

**QMX fit.** Every background and server agent, and long Lab experiments. The budget pause-and-resume UX maps
well to a desktop "this run is paused at its $X cap: raise / stop" card.

**Mapping.**
- `ModelCallLimitMiddleware` and `ToolCallLimitMiddleware` (`.../middleware/model_call_limit.py`,
  `tool_call_limit.py`) cap call counts. There is no built-in dollar cap.
- Build a `CostTrackingMiddleware`-style reserve/settle controller (a class with that name exists in the clone,
  apparently in tests/examples; UNVERIFIED) and record spend per run in LangGraph state.
- For Opus via subscription, track tokens and quota windows rather than dollars.

**Cost.** This pattern is what makes unattended agents safe to leave running.

## 13. Long-running and scheduled agents

**Worked forms.**
- **Scheduled reviewer** (`claude_agent_sdk/scheduled_repository_reviewer/scheduled_repository_reviewer.ipynb`):
  - cron runs a script.
  - `permission_mode="dontAsk"` (deny anything not pre-approved).
  - Read-only `tools=[Read, Glob, Grep]`, plus a `PreToolUse` hook denying paths outside scope.
  - `setting_sources=[]` so the run is machine-independent.
  - A pinned `model`, plus `max_turns` and `max_budget_usd`.
  - An `output_format` JSON schema reply with a greppable `VERDICT` line.
  - **Continuity by `resume=<previous session_id>`**, with schema fields `previous_review_id`,
    `previous_finding_ids` and `resolved` proving the follow-up remembered.
  - The prompt makes the agent re-list the repo first so it doesn't answer from stale reads.
  - Points to Claude Code routines and Managed Agents scheduled deployments as the hosted alternatives.
  - About $0.10 per run.
- **Hosting tiers** (`claude_agent_sdk/07_Hosting_the_agent.ipynb`): ephemeral container → hybrid HTTP server
  that keeps a `session_id` → SDK session map (the SDK picks its own IDs) → Modal (public URL, so a bearer
  token is needed) → Kubernetes. Kubernetes adds an auth gateway and **egress lockdown** so an injected agent
  can reach only the model API.
- **Production operation** (`managed_agents/CMA_operate_in_production.ipynb`): vaults hold per-user MCP
  credentials (the agent never sees tokens); webhooks (`session.status_idled`, `session.budget_reached`) replace
  held-open streams; resources follow a list/retrieve/update/archive lifecycle.
- **Codex Goals**: a durable, thread-scoped objective (active/paused/complete/budget-limited). The model may
  only start a goal and mark it complete with evidence; pause, resume, clear and budget are user/system
  controlled. Continuation happens only when the thread is idle. Template:
  "`/goal` <end state> verified by <evidence> while preserving <constraints> … if blocked …"
  (`codex/using_goals_in_codex.ipynb`).
- **ExecPlans**: a self-contained living `PLANS.md` with milestones, a decision log and observable acceptance.
  The agent proceeds milestone to milestone without asking "next steps?" (`openai-cookbook/articles/codex_exec_plans.md`).
- **Self-evolving loop**: `continuous_monitoring(interval_hours=24)` re-runs eval plus prompt optimisation when
  new data is detected, with versioned prompts and rollback (`partners/self_evolving_agents/autonomous_agent_retraining.ipynb`).
- **Scheduled workspace agents** (daily/weekly schedule, per-user memory folder) as a product-shape reference
  (`openai-cookbook/articles/chatgpt-agents-sales-meeting-prep.md`).
- Remote sandbox **webhook-managed** mode: paused workers resume when a connection is needed
  (`openai-cookbook/examples/agents_api/sandboxes/webhook_managed.md`, `notes/batch05.md`).
- Batch API and Flex for non-urgent work: batches are single-shot (no tool loop) and complete within a 24-hour
  expiry window (not an SLA). `service_tier="flex"` gives about 50% off with RPM control
  (`cost_optimization.ipynb`; `Prompt_Caching_201.ipynb`).

**QMX fit.** Background workflow agents and the server agent on the VPS. Examples: a nightly "what changed in
my strategies' data" review that resumes yesterday's findings; a weekend research sweep; a liveness/soak
reviewer. The Goal pattern fits the Lab copilot's long experiments ("keep tuning until out-of-sample Sharpe >
X verified by walk-forward, or report blocked").

**Mapping.**
- LangGraph checkpointer plus `thread_id` = resume.
- `interrupt()` = pause or approval.
- A goal object in graph state plus a conditional edge looping only at idle = Goals.
- Scheduling: an external scheduler (Windows Task Scheduler / APScheduler on the desktop; systemd timer or the
  LangGraph server's cron on the VPS; LangGraph Platform cron existence UNVERIFIED in this pass).
- Structured output on the final node gives the machine-readable verdict.

**Cost.** Bounded by the caps in §12. Re-reading state on resume is cheap. The re-list-first rule costs a little
but prevents stale answers.

## 14. Human-in-the-loop gates and money-path boundaries

**Worked forms.**
- Custom tools `decide()` and `escalate()`: when the agent calls one, the session waits for your code to return
  `user.custom_tool_result`. In development you stream; in production you use webhooks so no connection is held
  open while a human thinks (`managed_agents/CMA_gate_human_in_the_loop.ipynb`; `CMA_operate_in_production.ipynb`).
- **Proposal-only finance agent**: the model only proposes. Application code recomputes every material number;
  a Pydantic schema field `drafting_authorized: Literal[False]` makes self-granted authority impossible; human
  approval is persisted in `review_history` before any downstream action
  (`openai-cookbook/examples/partners/AWS/evidence_grounded_aml_agent_with_bedrock.ipynb`, `notes/batch10.md`).
- Per-tool uncertainty thresholds in GPT-5 prompting: low tolerance for trade/delete actions, high for
  read/search (`gpt-5/gpt-5_prompting_guide.ipynb`, `notes/batch09.md`).
- SRE agent: read-only evidence tools; the rollback is *proposed* and needs webhook approval, and "approval ≠
  execution" (`agents_api/apps/sev_bot/README.md`, `notes/batch05.md`).
- `PreToolUse` hooks deny or block deterministically; `AskUserQuestion` gates in slash commands
  (`claude_agent_sdk/01`, `03_The_site_reliability_agent.ipynb`, `notes/batch00.md`).

**QMX fit.** The Portfolio copilot above all. Any order, sizing change or node configuration change is a
proposal object that code validates and the operator clicks. This matches the standing money-path boundary.

**Mapping.** `HumanInTheLoopMiddleware` (`.../middleware/human_in_the_loop.py`) with per-tool `interrupt_on`
plus LangGraph `interrupt()`. The approval card is rendered in the desktop UI from the interrupt payload.

**Cost.** None. Waiting costs nothing when state is checkpointed.

## 15. Verification loops: outcome graders, evaluator-optimizer, review/repair

- **Outcomes** (`managed_agents/CMA_verify_with_outcome_grader.ipynb`): `define_outcome` gives the writer a
  *description* and a stateless grader a *rubric*. After each writer turn the grader checks it.
  `max_iterations` defaults to 3 (max 20). Advice: make every criterion checkable and make the grader earn
  `satisfied` with concrete evidence (a fetched page, a `file:line`).
- Evaluator-optimizer and orchestrator-workers as plain API loops (`patterns/agents/evaluator_optimizer.ipynb`,
  `orchestrator_workers.ipynb`, `basic_workflows.ipynb`).
- Review → repair → validate with a per-iteration `record.json` and explicit stop conditions
  (`openai-cookbook/examples/codex/Build_iterative_repair_loops_with_Codex.ipynb`). Headless
  `codex exec --output-schema` produces a strict JSON verdict (`codex/build_code_review_with_codex_sdk.md`,
  `notes/batch07.md`).

**QMX fit.** Lab (a strategy-code reviewer; a "did the backtest actually use out-of-sample data?" grader).
Workflow agents (report quality gates).

**Mapping.** A two-node LangGraph cycle (writer → grader → conditional edge) with a cheap-model grader where
the rubric is mechanical.

**Cost.** Each iteration costs a full grader pass. Cap iterations, and fail loudly if every run hits the cap.

## 16. Evals as the cost-optimisation instrument

- Measure **pass rate and cost per task together** before optimising, and run each configuration more than
  once (`cost_optimization.ipynb`).
- Harness-aware evals: score the same cases at three levels (tool unit → standalone loop → full product
  harness), because "a score measures the harness as much as the model". Pass rates are relative; measure
  per-case churn (`partners/harness_aware_plugin_evals/harness_aware_plugin_evals.ipynb`, `notes/batch10.md`).
- Macro-evals over about 1,000 traces: Promptfoo labels → topic clustering → backward root cause
  (`partners/macro_evals_for_agentic_systems/macro_evals_for_agentic_systems.ipynb`).
- Agentic-search benchmark reproduction (`claude-cookbooks/evals/agentic_search/reproduce_agentic_search_benchmarks.ipynb`)
  and tool-evaluation harness (`tool_evaluation/tool_evaluation.ipynb`). Not read in depth; see `notes/batch04.md`.

**QMX fit.** The QA phase and every routing decision in §11. **Mapping.** LangSmith datasets/evaluators or a
plain pytest battery, which fits the deterministic-first QA ruling.

## 17. Tool scaling: tool search and programmatic tool calling

- **Tool search.** Start with only a `tool_search` tool; return matching definitions on demand. "Cutting context
  usage by 90%+" in the embeddings demo (`tool_use/tool_search_with_embeddings.ipynb`). `defer_loading=True` and
  `tool_reference` variants scale to thousands of tools without breaking the cache
  (`tool_use/tool_search_alternate_approaches.ipynb`, `notes/batch04.md`). Caveat from the cost notebook:
  progressive disclosure can cost more tokens hunting than it saves.
- **Programmatic tool calling (PTC).** Mark tools `allowed_callers: ["code_execution_20250825"]` (header
  `advanced-tool-use-2025-11-20` per `notes/batch04.md`). The model writes code that calls tools in a sandbox,
  so large intermediate results never enter its context; `caller` on `tool_use` distinguishes direct from
  programmatic calls (`tool_use/programmatic_tool_calling_ptc.ipynb`). The same idea appears as "keep large
  artifacts out of context and give a query tool": aggregating a 5,000-row ledger via a tool instead of pasting
  the CSV (`cost_optimization.ipynb`).

**QMX fit.** General copilot (the "Lego" tool catalogue grows unbounded). Lab and Portfolio (OHLCV, trade
logs and optimiser outputs should be queried, never pasted).

**Mapping.**
- `LLMToolSelectorMiddleware` (`.../middleware/tool_selection.py`) pre-selects tools with a cheap model.
  Note that this changes the tool list per call and so **breaks caching**; `ClientToolSearchMiddleware` exists
  in the clone (UNVERIFIED API).
- The PTC equivalent is Deep Agents' sandbox/code-execution tooling or a QMX "python over the data store" tool.

**Cost.** Large savings on data-heavy turns. Measure against caching.

## 18. Skills

- Claude Skills: a `SKILL.md` folder with progressive disclosure (metadata ≤64/1024 characters → instructions
  under about 5k → resources); `container={"skills":[...]}` with code execution and betas
  `code-execution-2025-08-25`, `files-api-2025-04-14`, `skills-2025-10-02`. Finance examples:
  `analyzing-financial-statements`, `creating-financial-models` (DCF), Excel/PowerPoint outputs
  (`skills/notebooks/01–03`, `skills/custom_skills/`, `notes/batch03.md`). Managed sessions discover skills from a
  mounted repo's `.claude/skills/` (`managed_agents/CMA_use_skills_from_a_repo.ipynb`, per README; not read in depth).
- OpenAI Skills API: `POST /v1/skills`, versioned, mounted into the shell tool. Advice: "Use when / Don't use
  when" plus negative examples; design skills like tiny CLIs (deterministic stdout, fail loudly); don't
  duplicate the procedure in the system prompt (`openai-cookbook/examples/skills_in_api.ipynb`, `notes/batch12.md`).

**QMX fit.** Lab (house procedures: "walk-forward test", "regime report"); the Portfolio copilot's report
generation; operator-addable skills in the Lego vision.

**Mapping.** Deep Agents `SkillsMiddleware` (`deepagents/libs/deepagents/deepagents/middleware/skills.py`)
reads `SKILL.md` folders client-side, so it works on any model.

**Cost.** Low. Only metadata is resident.

## 19. Observability and the session browser (desktop-UI patterns)

- Per-thread `usage` and `list_cost`; live subagent streaming via per-thread event deltas
  (`CMA_plan_big_execute_small.ipynb`; `CMA_watch_subagents_live.ipynb` per README).
- A session browser over SDK sessions on disk (list/get/read/rename/tag/fork/delete)
  (`claude_agent_sdk/05_Building_a_session_browser.ipynb`, `notes/batch00.md`), which is exactly a copilot
  sidebar.
- Usage/Cost Admin API for org-level reporting (`observability/usage_cost_api.ipynb`, `misc/admin_api.ipynb`).
- Agent Hub messages arrive in the next tool result (§7). OpenAI apps update **one** progress message from
  `turn.item.added` and `subagent.created` events (`agents_api/apps/slack_bot/README.md`, `notes/batch05.md`).

**QMX fit.** Every agent surface. The UI should show threads and subagents as a tree, with tokens and cost per
node, plus fork and resume.

**Mapping.** LangGraph `stream_mode` (`updates`/`messages`/`custom`) with subgraph streaming, plus checkpoint
history for fork and time-travel.

## 20. Finance and quant worked examples (domain templates)

- Multi-agent portfolio collaboration: a Head PM with fundamental, macro and quant specialists (agents-as-tools,
  run in parallel) producing an investment memo; prompts live in `prompts/*.md` including a `tool_retry_prompt.md`
  (`openai-cookbook/examples/agents_sdk/multi-agent-portfolio-collaboration/`).
- Temporal knowledge graph over earnings calls: atomic statements → time-bounded triplets → an invalidation
  agent → a multi-hop retrieval planner (`partners/temporal_agents_with_knowledge_graphs/temporal_agents.ipynb`,
  `notes/batch11.md`).
- Financial statement and DCF skills (`claude-cookbooks/skills/custom_skills/`), and a chief-of-staff agent with
  burn/runway scripts behind a financial-analyst subagent (`claude_agent_sdk/01`).
- Financial document analysis with sub-question decomposition (`third_party/financial_document_analysis_with_llamaindex.ipynb`).

**QMX fit.** The Portfolio copilot (the PM pattern; numbers computed by code, never by the model) and the Lab
copilot (temporal KG for the free-news timeline). Caveat: none of these trade. All execution must stay behind
§14.

---

## 21. Cross-cutting tensions the cookbooks surface

1. **Caching vs context management.** Compaction, clearing, tool search, model routing and effort changes all
   break the cache. Both vendors say so explicitly (`cost_optimization.ipynb`; `Prompt_Caching_201.ipynb`).
   QMX needs one owner for prompt layout.
2. **Subagent savings vs cache loss and floor cost.** A fresh prefix per worker plus fixed per-thread overhead
   (`CMA_plan_big_execute_small.ipynb`; `cost_optimization.ipynb`).
3. **Summaries poison.** A bad fact in a summary or in memory persists (`session_memory.ipynb`;
   `memory_cookbook.ipynb`). Keep facts in artifacts and files; summaries carry only pointers.
4. **Unattended means bounded.** Every scheduled example pins the model, caps turns and spend, uses
   deny-by-default permissions and returns a schema verdict (`scheduled_repository_reviewer.ipynb`).

---

## 22. The 10 patterns QMX should copy first

1. **Byte-stable prompt layout plus provider caching** (§1). Biggest saving for the least work. Use
   `AnthropicPromptCachingMiddleware`, a fixed tool superset with `allowed_tools`-style restriction, volatile
   state in the last turn, and effort pinned per thread.
2. **Caps on every unattended run** (§12): model/tool call limits plus a reserve-and-settle spend controller,
   with a pause card in the UI (raise / stop) modelled on `budget_reached`.
3. **Scheduled-and-resumable agent template** (§13): pinned model, deny-by-default tools, `PreToolUse`-style
   path and tool guards, a schema verdict, and resume by `thread_id` with prior-finding IDs echoed. Reuse it
   for every background workflow agent.
4. **Proposal-only money path with HITL** (§14): `HumanInTheLoopMiddleware` and `interrupt()`; code recomputes
   numbers; an authority field fixed by the schema (the `Literal[False]` idea).
5. **Plan big, execute small** (§8): Opus coordinator, DeepSeek/GPT-6 Luna readers via Deep Agents subagents,
   used only for coverage-heavy tasks.
6. **Session vs durable memory split, with versioned writes** (§6): checkpointer for the thread, Store for
   facts and preferences, an append-only memory history the operator can audit and edit, and a poisoning guard.
7. **Instant background session memory** (§4): prebuilt summary swapped in at the limit, so there are no
   compaction stalls in the desktop UI.
8. **Client-side context editing at natural boundaries** (§5): `ContextEditingMiddleware` with large
   `clear_at_least` (jagged pruning), and data offloaded to files or query tools instead of pasted (§17).
9. **Goal objects for long Lab experiments** (§13, Codex Goals): end state plus evidence plus constraints plus a
   blocked rule; the model can only start a goal or mark it complete; the user controls pause, resume and
   budget; displayed as a goal chip on the thread.
10. **Cost-per-verified-task evals before any routing change** (§11, §16): an effort/tier sweep with a
    cheap-model escalation ladder, judged on a fixed QMX case set run more than once.

## 23. Attractive patterns QMX should skip (or defer)

- **Claude Managed Agents as the runtime** (`managed_agents/*`). Excellent reference designs, but they move
  the agent loop, sandbox and memory onto Anthropic's servers, bypass LangGraph, are API-billed (not the
  subscription), and lock QMX to one vendor. Copy the designs (budgets, advisor, outcomes, memory versions),
  not the runtime.
- **OpenAI Agents SDK / Agents API / AgentKit as the runtime** (`agents_sdk/*`, `agents_api/*`,
  `agentkit/agentkit_walkthrough.ipynb`). Same reason. They duplicate what LangGraph and Deep Agents already
  give QMX.
- **Server-side compaction, context-editing and fallback betas through CLIProxyAPI.** Skip until proven to pass
  through the proxy (UNVERIFIED). Use the client-side middleware equivalents.
- **Speculative cache warming everywhere.** Use it only on large, changed prefixes; elsewhere it burns writes.
- **Dynamic workflows written by the model as JavaScript** (`08_Dynamic_workflows.ipynb`). Keep the idea
  (code-orchestrated, re-runnable fan-out), but QMX should express it as LangGraph graphs the UI can render,
  not opaque model-written JS. The token cost is high.
- **Tool search / `LLMToolSelectorMiddleware` on small tool sets.** Below roughly 30–50 tools the cache loss
  and hunting overhead outweigh the saving (`cost_optimization.ipynb` caveat; the threshold is my estimate,
  UNVERIFIED).
- **Self-evolving prompt retraining loops** (`autonomous_agent_retraining.ipynb`, HALO in
  `agent_improvement_loop.ipynb`). Prompts changing unattended conflict with the operator's change control.
  Defer until the eval battery exists; even then, propose changes for review rather than auto-applying them.
- **Advisor on every agent.** It has no per-consult cap and helped only weak drivers in the measured eval.
  Use it only on cheap background drivers.
- **Voice and realtime agents** (`app_assistant_voice_agents.ipynb`, realtime evals). Not a QMX need.
- **Batch API for interactive agents.** Batch is single-shot with no tool loop. Use it only for offline
  classification or eval sweeps.
- **Retrieval-based memory for preferences.** Both vendors' examples favour state/file memory for preferences
  (`context_personalization.ipynb`). Keep vector retrieval for documents, not for "what the operator likes".

---

## 24. Check against `rebuild/research/cookbooks-loops-graphs.md`

I read this file only after writing everything above. It catalogues 34 cookbook patterns
(`C:\Users\Mubarak\Desktop\QMX-worktrees\rebuild\rebuild\research\cookbooks-loops-graphs.md` §2) and is accurate
where I could check it. I spot-checked two numbers and both are correct: dynamic workflows run "up to 16 agents
… concurrently … at most 1,000 agents per run" (`08_Dynamic_workflows.ipynb`), and plan-big-execute-small billed
"84-98% of the team's input tokens … at the worker rate" (`CMA_plan_big_execute_small.ipynb`). It covers more
LangChain blog material than this file does.

**What it missed** (keyword absent from the file, checked by grep):
1. **`claude-cookbooks/cost_optimization/cost_optimization.ipynb`, the single most decision-relevant cookbook for
   QMX's model split.** Missing from it:
   - the 13x Opus-high → `sonnet · medium` result;
   - the explicit cache-breaker list (model switch, effort change, per-turn compaction, dynamic text above the
     breakpoint);
   - jagged compaction;
   - "subagents share no cache with the parent";
   - the advisor-vs-subagent-routing comparison;
   - batch restructuring at about half the cost;
   - "measure cost per completed task".
2. **Server-side fallback** (`fable_5_fallback_billing/guide.ipynb`: `fallbacks`, `usage.iterations`, a cached
   prefix billed as a cache read on fallback). It is the vendor-blessed route-on-failure mechanism; the closest
   LangChain piece, `ModelFallbackMiddleware`, is also not named.
3. **Reserve-before-call budgeting** (`openai-cookbook/articles/per_run_spending_controller_responses_api.md`).
   The proposed `BudgetMiddleware` charges usage × rate card *after* the call, so it can overshoot by a whole
   request; reserving the worst case first closes that gap.
4. **Hosting and production-operation patterns**: `claude_agent_sdk/07_Hosting_the_agent.ipynb` (session-id
   mapping, auth gateway, **egress lockdown** so an injected agent reaches only the model API) and
   `CMA_operate_in_production.ipynb` (**vaults**: the agent never sees per-user credentials; idle and budget
   webhooks). These matter for the VPS server agent and broker credentials.
5. **Session browser** (`claude_agent_sdk/05_Building_a_session_browser.ipynb`): the reference for the copilot
   sidebar (list, rename, tag, fork, resume).
6. **Concrete LangChain middleware names** for the cookbook patterns: `AnthropicPromptCachingMiddleware`,
   `ContextEditingMiddleware`, `HumanInTheLoopMiddleware`, `ModelFallbackMiddleware`,
   `LLMToolSelectorMiddleware`. It names only `ModelCallLimitMiddleware`, `ToolCallLimitMiddleware` and
   Summarization. That pushes it toward building new middleware where stock middleware exists.
7. **Finance and eval templates**: the temporal knowledge graph over earnings calls (`temporal_agents.ipynb`),
   harness-aware three-level evals (`harness_aware_plugin_evals.ipynb`), and the chief-of-staff
   hooks-plus-subagent audit log (`claude_agent_sdk/01`).
8. **The cache tension in background session memory.** Its row 11 says "cache the background calls", but the
   cache hit needs the *same model* as the main chat, which conflicts with using a cheap summariser
   (`session_memory_compaction.ipynb` cost box). This is a real choice QMX has to make per thread.

**Possibly wrong or over-stated:**
- Row 17 says warming is "Anthropic only". OpenAI caching is automatic, so the same trick plausibly works there
  too (UNVERIFIED; no OpenAI cookbook shows it).
- It names "GPT-6.1 Sol" for sub-agents. The cookbooks I read name GPT-5.6 Luna/Terra/Sol tiers
  (`optimizing_agents_for_cost_and_quality.ipynb`). I could not verify the 6.1 name from the cookbooks; it may
  come from another source.
- Nothing I found contradicts its LangGraph facts.
