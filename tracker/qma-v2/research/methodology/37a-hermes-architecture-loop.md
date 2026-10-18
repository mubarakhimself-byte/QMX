# 37a. Hermes Agent: architecture and agent-loop internals, mapped onto QMX

Date: 2026-10-18. Study 37a of two (37b covers tools, providers and plugins).

**How this was read.** Every docs page was opened in the built-in browser and read as a page; no bulk dumps and no sign-in. Where the docs were thin, the source was read file by file from `raw.githubusercontent.com` in the same browser tab (`agent/AGENTS.md`, `agent/turn_api_error.py`, `agent/error_classifier.py`, `agent/chat_completion_stream_monitor.py`, `website/docs/developer-guide/subagent-lifecycle-api.md`). Firecrawl was not needed. Study 25 already covered credential pools, cron, plugins, skills and memory; this study does not repeat them.

**The one difference that shapes every section.** Hermes owns its model loop: it builds the request, calls the provider, parses tool calls, compacts and retries itself. QMX does not. QMA v2 runs every agent as a Claude Code CLI process through the Claude Agent SDK (`research/one-engine/architect/DESIGN.md` §3, "No local compactor", "No QMX permission engine"). So each section splits Hermes' logic into:

- **Copy**: logic that lives above the loop and fits the engine, the harness wrapper, the Library or the UI.
- **SDK owns it**: the CLI already does this, or forbids us from doing it (we cannot rewrite history, place cache markers or reorder messages inside the CLI).

Labels: **[retrieved]** read today at the cited place; **[inferred]** reasoned here.

Sources (all retrieved 2026-10-18):

| Short name | URL |
|---|---|
| ARCH | https://hermes-agent.nousresearch.com/docs/developer-guide/architecture |
| LOOP | https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop |
| PROMPT | https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly |
| COMPRESS | https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching |
| MICRO | https://hermes-agent.nousresearch.com/docs/developer-guide/micro-compaction |
| GW | https://hermes-agent.nousresearch.com/docs/developer-guide/gateway-internals |
| GWLIFE | https://hermes-agent.nousresearch.com/docs/developer-guide/gateway-session-lifecycle |
| MUX | https://hermes-agent.nousresearch.com/docs/developer-guide/multiplexing-gateway |
| BACKLOG | https://hermes-agent.nousresearch.com/docs/developer-guide/completion-backlog-delivery |
| STORE | https://hermes-agent.nousresearch.com/docs/developer-guide/session-storage |
| RECOVER | https://hermes-agent.nousresearch.com/docs/developer-guide/state-db-recovery |
| PROV | https://hermes-agent.nousresearch.com/docs/developer-guide/provider-runtime |
| API | https://hermes-agent.nousresearch.com/docs/developer-guide/programmatic-integration |
| DELEG | https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation |
| LIFE | https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/subagent-lifecycle-api.md |
| SRC | https://github.com/NousResearch/hermes-agent/tree/main/agent (files named per section) |

QMX sources: `architecture/workflow-engine/ARCHITECTURE-SPINE.md` (AD-n), `architecture/workflow-engine/PLAIN-WORDS.md`, `research/one-engine/architect/DESIGN.md` (DESIGN), `research/methodology/34-engine-run-triage.md` (B-n, L-n, HG3 list).

---

## 1. Architecture

**How Hermes does it.** One class, `AIAgent`, serves every door: CLI, messaging gateway, IDE (ACP), batch runner, HTTP API server and in-process Python (ARCH, "System Overview"). Doors differ only in how text comes in and how replies go out: "Platform differences live in the entry point, not the agent" (ARCH, "Design Principles"). `run_agent.py` is a thin facade; the loop is `agent/conversation_loop.py`, and each phase of a turn is its own file `agent/turn_*.py` (preflight, request assembly, API call, API error, overflow, truncation, recovery, tool round, finalizer) so a change touches one ~600-line file (SRC `agent/AGENTS.md`, "Agent loop"). Six design rules are stated as a table: prompt stability, observable execution, interruptible, platform-agnostic core, loose coupling through registries, profile isolation (ARCH).

**What QMX has.** The same "one core, many doors" idea, split in two: the harness (`qma.harness.Harness`, one class, eleven methods; DESIGN §3 "Interface depth") runs chats; the engine (`qmx_engine.service`, AD-21 "Three surfaces, one Engine API") runs workflows. The engine is hexagonal with ports (AD-1, "Design Paradigm" table).

**Gap.** Small. QMX already has the shape. What Hermes adds is the habit of one file per turn phase and a written list of message-flow invariants that every change is reviewed against (SRC `agent/AGENTS.md`, "Message-flow invariants").

**Proposal: adapt.** Add a short "flow invariants" block to the engine's and harness's `AGENTS.md`: the prompt is byte-stable per chat; compaction is the only sanctioned cache break; injected context rides a user message or tool result, never the system prompt; one writer per store. Lands in: **engine** and **harness** (docs + review rubric). Effort: tiny.

---

## 2. Agent loop internals

**How Hermes does it.** (LOOP; SRC `agent/AGENTS.md`)
- A synchronous `while` loop bounded by `max_iterations` (default 500) and an `IterationBudget`, with a **one-turn grace call** when the budget runs out: "At 100%, the agent stops and returns a summary of work done" (LOOP, "Iteration Budget").
- Model calls run in a background thread so the main thread can watch an interrupt event; an interrupted call is abandoned and "No partial response is injected into conversation history" (LOOP, "Interruptible API Calls").
- Several tool calls in one reply run in a thread pool; interactive tools force sequential runs; results go back in the original order (LOOP, "Tool Execution").
- Some tools (`todo`, `memory`, `session_search`, `delegate_task`) are intercepted before the registry because they change agent state (LOOP, "Agent-Level Tools").
- Context pressure warnings were removed: "they caused models to 'give up' prematurely on complex tasks" (COMPRESS, "Context Pressure Warnings").
- `/steer` text is delivered as a standalone user row right after a tool result, never merged into the tool row (SRC `agent/AGENTS.md`).

**What QMX has.** The CLI owns the loop. The engine sets `max_turns` and `max_tool_calls` per agent node (AD-4) and stops an attempt at those limits (AD-16). The harness forwards blocks and deltas (DESIGN §3 "One turn, end to end").

**SDK owns it.** Thread pools for tool calls, interrupt mechanics, role alternation and the steer row are inside the CLI. Do not rebuild them.

**Gap.**
1. When an agent node hits `max_turns`, QMX gets an error result and no summary. Hermes always gets one grace call that writes "what I did".
2. AD-34's no-harness-edit fallback injects "one instruction to `memory_note` the working state and summarise" at 40%. That is close to the pressure warning Hermes removed for making models quit early. [inferred]

**Proposal.**
- **Adopt** a grace turn: when an agent attempt ends by `max_turns` or `max_tool_calls`, the engine resumes the same chat once with a fixed prompt ("Stop working. Write the structured result with what is done, what is not, and why.") with tools denied, and saves that as the attempt's partial output with `exit_reason: max_turns, truncated: true` (the same flags Hermes returns, DELEG "Max Iterations"). Lands in: **engine** (`nodes.agent`), needs HG3 item 1 (per-chat tools allow-list) for "tools denied". Effort: small.
- **Adapt** the AD-34 fallback wording: the injected instruction should say "save state, then continue", never "you are near the limit". Lands in: **engine**. Effort: tiny.

---

## 3. Prompt assembly

**How Hermes does it.** (PROMPT)
- The cached system prompt is built once from three ordered tiers: **stable** (identity, tool guidance), **context** (caller system message, project files, then anything naming the current worktree), **volatile** (skills index, frozen memory snapshot, user profile, timestamp, runtime environment last). Shared project files come before worktree-specific lines so sessions in different worktrees share a longer cache prefix.
- Anything that changes mid-session never touches the system prompt. It rides "the per-turn user-message channel" as a **one-shot note**: a surface switch, a changed skills index (new or removed skills, computed by diff each turn, `agent/skills_index_delta.py`), plugin context from `pre_llm_call`, and memory recall. The note is sent only when the difference changes.
- Only one project context file type is loaded (first match wins: `.hermes.md`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`). Each is **scanned for injection** (a hit becomes a `[BLOCKED: …]` marker) and **truncated** 70/20 head/tail with a cap that scales with the model window.
- **The prompt surface is a reviewed artifact.** `scripts/ci/prompt_surface.py render` builds the real system prompt and `tools[]` for nine surfaces with clock, OS and paths pinned, and commits them under `tests/fixtures/prompt_surface/`; a test fails when the snapshot is stale; CI posts token deltas and added or removed tools per surface on each PR (PROMPT, "Reviewing changes to the prompt surface").

**What QMX has.** AD-34 fixes a cache-friendly order: harness preset → skills → frozen memory snapshot → node brief → chunk payload last. AD-18: recalled memory reaches a model only as a tool result or fenced block. DESIGN: QMX rules and the workspace CLAUDE.md go into the preset's `append`; skills do not hot-reload (DESIGN "Departures" items 1 and 11). Triage: B-51 and B-70 (an `llm` chat still carried Claude Code tools; a resumed `tools: []` chat still called Glob, Bash and TaskList) and B-53 (the node brief cannot be cached across chunks).

**SDK owns it.** The CLI builds its own system prompt from the preset plus `append`. We cannot reorder its internal tiers.

**Gap.** Nobody can see the exact prompt and tool list a given chat kind actually sends. B-51 and B-70 are exactly the class of bug a prompt-surface snapshot would have caught before a run. Also, a skill created mid-session is invisible until relaunch.

**Proposal.**
- **Adopt** a prompt-surface snapshot test. For each chat kind (Interactive copilot, Background agent node, `llm` node, Child) build the `ClaudeAgentOptions` through the production `build_options`, render the `--append-system-prompt` text, the allowed and disallowed tool lists and the MCP tool schemas, pin clock and paths, commit the result, and fail CI when it is stale. Lands in: **harness** (CI) and **engine** (one surface per node kind). Effort: small. Highest value per effort in this study.
- **Adapt** the one-shot note: when the skills list or packs change mid-session, the harness prepends one short note to the next operator turn ("new skill available: X"), sent once per change. The preset stays byte-stable. Lands in: **harness**. Effort: small.
- **Adopt** the injection scan and head/tail truncation for workspace `CLAUDE.md`/`AGENTS.md` before they go into `append` (DESIGN loads them raw). Reuse the AD-36 scanner. Lands in: **harness**. Effort: small.

---

## 4. Context compression

**How Hermes does it.** (COMPRESS; SRC `agent/context_compressor*.py`)
- **Two layers.** The agent's compressor fires at 50% of the main model's window (configurable, per-model overrides by substring, longest match wins). A gateway "hygiene" safety net fires at 85% before a turn starts. Setting the gateway at 50% "caused premature compression on every turn".
- **Small windows get a floor.** For models under 512K, the threshold is raised to at least 0.75. A 16K local model's protected tail would otherwise be the whole request.
- **Usage anchor.** Every compaction gate first asks the provider's last real token counts plus a rough estimate of only the messages added since. With no real count yet, a rough estimate over threshold **waits one request** for provider evidence instead of compacting on a guess. The anchor is persisted on the session row so a restart keeps it.
- **Algorithm.** (1) Replace old tool outputs over 200 characters with a one-line stub, no model call. (2) Pick boundaries: protect the head (system + first exchange) and a token-budgeted tail, never split a tool call from its result. (3) Summarize the middle with a cheap side model using a fixed template: Goal, Constraints & Preferences, Progress (Done / In Progress / Blocked), Key Decisions, Relevant Files, Next Steps, Critical Context. (4) Reassemble and fix orphaned tool pairs. On later compactions the previous summary is **updated**, not rewritten.
- **Lean tail (default).** Keep a small verbatim tail (2.5% of window, 10K to 25K tokens) and carry continuity in the summary: an identifier-preserving session log, a **regex-extracted anchor index** (PR numbers, SHAs, paths, error strings, "never paraphrased"), **every real user message quoted verbatim**, and a `session_search` recovery pointer. Measured: ~49K kept instead of ~162K on 500K-token sessions, with higher recall.
- **Skills across a boundary.** Every pruned skill body leaves `[SKILL_PRUNED: … reload with skill_view(name='…')]` and the summary lists them under "Pruned Skills".
- **Failure handling.** A failed summary arms a per-session cooldown (60 s → 300 s → 900 s, persisted). A second stall ends in a **deterministic fallback summary** (static anchors, no model) committed through the normal path. A provider overload aborts and keeps the transcript, but three overload aborts in a row commit the deterministic fallback so the session does not grow until it dies. A provider-proven overflow ignores the cooldown for one bounded attempt.
- **In-place compaction.** Same session id; old rows are soft-archived (`active=0, compacted=1`), still searchable, never deleted.
- **Telemetry.** One content-free log line per attempt: trigger source, route, commit status, method (`llm_summary`, `aux_fallback_main`, `deterministic_fallback`), messages and tokens before and after.
- **Pluggable.** A `ContextEngine` ABC (`should_compress()`, `compress()`, optional tools) lets a plugin replace the default; never auto-activated.

**What QMX has.** AD-34: compact at `agent.compact_at` 0.40 through HARNESS-REQUESTS H15; fallback for plan rows: watch turn usage, inject a "save and summarise" instruction, continue in a fresh Background chat seeded with the summary. Each compaction is a `compacted` span event. Triage B-6/L-7: `compact_at` is lost when a chat reloads after a restart.

**SDK owns it.** The CLI has its own auto-compaction, its own summary prompt and its own history rewrite. QMX can set the threshold (H15, or `CLAUDE_CODE_AUTO_COMPACT_WINDOW` for key rows per AD-34) but cannot change the algorithm or the template inside the CLI.

**Gap.**
1. The AD-34 fallback re-seeds a fresh chat from a summary the agent writes freely. Hermes shows what a good re-seed carries: a fixed template, the brief and every operator instruction verbatim, a mechanical anchor index, and a pointer to where the full history lives.
2. 0.40 for every model. Hermes found low thresholds harmful on small windows and floors at 0.75 below 512K. QMX's key providers include smaller-window models (Kimi, GLM, DeepSeek). [inferred: a 128K model at 0.40 compacts at ~51K, often before the node brief and one chunk are even read.]
3. The fallback decides from turn usage, which is real usage; good. But there is no rule for the first turn of a resumed chat, where no usage exists yet.
4. No failure path is written for the fallback: what happens when the summary turn itself fails or stalls.

**Proposal.**
- **Adopt** the re-seed template for the AD-34 fallback. The engine builds the seed itself, not the agent: (a) the node brief verbatim, (b) every operator or upstream instruction verbatim, (c) the agent's own summary in Hermes' seven headings, (d) an anchor index the engine extracts by regex from the old transcript (paths, SHAs, run ids, Library object ids, error strings), (e) "full history: Library trace `<run_id>` span `<span>`; use `memory.search_runs` to recall". Lands in: **engine** (`nodes.agent`), reads from **Library**. Effort: small to medium.
- **Adopt** a per-model threshold map with a small-window floor: `agent.compact_at` stays 0.40, plus `agent.compact_at_by_model` (substring keys, longest wins), plus a floor of 0.75 for windows under 512K unless set explicitly. Lands in: **engine** settings (AD-34 amendment). Effort: tiny.
- **Adopt** the "wait one request for real usage" rule in the fallback watcher. Lands in: **engine**. Effort: tiny.
- **Adopt** the failure ladder for the fallback: on a failed or stalled summary turn, keep the chat, wait (60 → 300 → 900 s), and on the second failure re-seed from the engine-built deterministic seed without the agent's summary (items a, b, d, e above). Record `method` on the `compacted` span (`agent_summary | deterministic`). Lands in: **engine**. Effort: small.
- **Skip** a pluggable context engine. The CLI owns context; QMX would have nothing to plug into.

---

## 5. Micro-compaction

**How Hermes does it.** (MICRO) Off by default. After each finished turn, fold the single oldest un-summarized exchange into one running summary; user messages are never compacted ("compact the derived material, keep the source of truth"); defrag the summary when it passes 2,000 tokens; skip an exchange after three failed tries. The page is candid: each pass "breaks the provider prompt-cache prefix every turn", and on a deep cache discount the cost "can plausibly cost more than the stall it removes". The measure that matters is occupancy, not tokens saved.

**What QMX has.** Nothing similar. AD-34 uses one-shot compaction.

**SDK owns it / forbids it.** QMX cannot rewrite already-sent history inside a CLI session.

**Gap and proposal: skip.** It cannot be built on the SDK, and on the Claude plan the cache break is the expensive part. Keep one idea: **report occupancy** (context tokens as a share of the compaction threshold) on the agent span and the run card, so a node that sits at 90% is visible before it compacts. Lands in: **engine** span field + **UI** run card. Effort: tiny.

---

## 6. Prompt caching

**How Hermes does it.** (COMPRESS, "Prompt Caching")
- `system_and_3`: four Anthropic cache breakpoints, one on the system prompt and a rolling three on the last three messages.
- TTL `auto` per source: 1 h for human-paced sessions, 5 min for machine-paced ones (subagent, cron, webhook, batch, API).
- A hard rule: "Model identity is part of the cache key … Don't add features that silently swap the model or credentials mid-session." Compression is the only sanctioned cache break (SRC `agent/AGENTS.md`).
- `api_content` stores the exact bytes sent when they differ from what is displayed, so replay is byte-identical and the cache keeps hitting (STORE, "Messages Table").

**What QMX has.** AD-34 cache-stable order and pool affinity on `run_id:node_id`, with `uncached_resend: true` on a forced rotation. AD-12: a running chat moves account only on a quota or auth error.

**SDK owns it.** The CLI places its own cache markers and chooses TTL. QMX cannot put breakpoints.

**Gap.** Small. Two things are not written down: (1) whether a long-paced copilot chat should ask for the 1 h cache [inferred: check whether the CLI exposes a TTL setting; if it does, set it per chat kind]; (2) the chunk-to-chunk cache depends on B-53 (the brief must be in a per-chat appended system prompt).

**Proposal.**
- **Adapt** TTL by chat kind if the CLI exposes it: Interactive 1 h, Background and Child default. Lands in: **harness** (`build_options`). Effort: tiny, after a probe.
- **Adopt** the "no silent model or account swap" rule as a stated harness invariant, with the one exception AD-12 already allows. Lands in: **harness** docs. Effort: tiny.
- Push HG3 item 4 (B-53, per-chat appended system prompt) because the AD-34 cache saving depends on it.

---

## 7. Provider runtime

**How Hermes does it.** (PROV)
- One resolver turns `(provider, model)` into `(api_mode, base_url, api_key, source)` for every door, cron and side tasks alike. Precedence: explicit request > config > env > defaults, so "a stale shell export" cannot override the saved choice.
- Each key is scoped to its own base URL, so the wrong key never goes to a custom endpoint.
- **Side ("auxiliary") tasks** (vision, compression summaries, web extraction, memory flush, title, session search) each pick their own provider and model and have their own fallback chain.
- **Fallback chain.** On max retries, non-retryable client errors (401/403/404) or exhausted transient errors, the agent swaps provider, model, client and api mode **in place**, once per session, resets the retry count and continues. A fix from #84733: every fallback activation must re-run the pre-API preflight "against the fallback's context window" (SRC `agent/turn_api_error.py`, `handle_api_error` docstring). Subagents do not inherit the fallback chain.
- **Learned limits.** A context length learned from a provider error or probe is persisted and wins over the static table (COMPRESS, "Bedrock context window cache").
- **Field self-heal.** When a route rejects a field by name, Hermes records it for that provider, host and model, strips it and retries once; the record lasts for the session (STORE, "Messages Table" notes).

**What QMX has.** `profiles.py` (`ClaudePlan | KeyProvider | GptPlan`, `resolve_model`), the relay with wire quirks per profile (DESIGN), roles mapped to ordered candidate lists (AD-13), the relay routing by model id (AD-29), and the failure ladder walking role candidates (AD-16).

**SDK owns it.** Within one CLI process the provider is fixed by its launch env; a provider switch is a relaunch with `resume=` (DESIGN "Two homes, one transcript folder").

**Gap.**
1. When AD-16 moves an attempt to the next role candidate, nothing says the chunk plan and the compaction threshold are recomputed for the new model's window. AD-34 computes the chunk plan once at dispatch. [inferred: a fallback from a 1M model to a 200K model reuses a 300K-token chunk.]
2. Wire quirks are static per profile. A new rejection teaches nothing.
3. Context windows come from a static table.

**Proposal.**
- **Adopt** "fallback re-runs preflight": on a ladder step to another model, re-resolve the window, recompute `compact_at` in tokens, and if the chunk no longer fits, re-chunk that partition (new partitions, recorded on a `ladder_step` event so replay stays deterministic under AD-6). Lands in: **engine** (AD-16, AD-34 amendment). Effort: medium.
- **Adapt** learned quirks in the relay: on a 400 naming a field, strip that field for that provider and model, retry once, and journal a `quirk_learned` line the operator can promote to the profile in Settings. Lands in: **harness** relay. Effort: small.
- **Adopt** learned context windows: store a provider-reported window per `(provider, model)` in the relay journal and let `resolve` prefer it. Lands in: **harness** relay + **engine** chunk planner. Effort: small.

---

## 8. Error handling and retries

**How Hermes does it.** (SRC `agent/error_classifier.py`, `agent/turn_api_error.py`; PROV)
- **One classifier.** `classify_api_error` maps any exception to a `ClassifiedError` with a reason from a closed enum and four **recovery hints**: `retryable`, `should_compress`, `should_rotate_credential`, `should_fallback`. "The retry loop … consults [these] instead of re-matching strings itself." Reasons include `auth`, `auth_permanent`, `billing`, `rate_limit`, `upstream_rate_limit` (aggregator's model is limited, the key is fine), `upstream_blocked` (a WAF in front of the provider), `overloaded`, `server_error`, `timeout`, `context_overflow`, `payload_too_large`, `model_not_found`, `content_policy_blocked` ("don't retry unchanged"), `format_error`, `role_alternation`, `thinking_signature`, `unknown`.
- Pattern tables are data, with provider-scoped exceptions (xAI credit exhaustion arrives as 403) and **unverified verdicts** (Anthropic's "out of extra usage" body also appears on a content-filter rejection, so the billing verdict is marked `billing_unverified` and gets a short cooldown).
- **One ordered handler.** Recover before classification, classify, fire an observer hook, recover after classification (pool rotation), check for interrupt (a pending steer rebuilds the turn instead of aborting), route by class, try overflow recovery (compress), then settle: non-retryable → fallback → terminal result; max retries → fallback → terminal; else an interruptible backoff. 402 billing is deliberately non-retryable. A process shutting down mid-call abandons with one log line.
- Local bugs (`ValueError`, `TypeError`) are not retried, except the listed transient shapes (corrupt stream chunk, SSL, a `None` from an upstream).

**What QMX has.** AD-16 ladder: retry (retryable only) → other account → other model → run doctor → park. AD-12: cooldown from reset time else 1 h on 429/402; 401 benches. AD-9: a rate limit inside a node is `waiting`, not failed. AD-4: `NodeResult.failed(error, signature, retryable)`. The doctor classifies `transient | bad_input | bad_output | logic` with a model call.

**SDK owns it.** The CLI retries transient API errors itself before the SDK reports anything. QMX sees only the final result (and, for key rows, the relay sees every HTTP status).

**Gap.** AD-16 has the ladder but no classifier: who decides `retryable`, and which rung to skip to? Today each executor must guess from SDK result text. Hermes shows that a zero-token classifier with hints does most of the work the "doctor" would otherwise pay a model for.

**Proposal: adopt.**
- Add `qmx_engine.core.failure` (pure, so AD-1 holds): `FailureClass` enum plus `Hints(retryable, rotate_account, next_model, compress, park_now)`. Inputs: the SDK result subtype and error text (plan rows) and the relay's journaled status and body code (key rows). Pattern tables live as data in Settings defaults, provider-scoped, with an `unverified` flag. The ladder reads hints: `billing` and `auth_permanent` skip retry and go straight to another account; `content_policy_blocked` skips retry and goes to another model; `context_overflow` triggers compaction then one retry; `upstream_rate_limit` goes to another model, not another account.
- The doctor runs only when the class is `unknown` or the same signature failed twice. That keeps the doctor's spend for real puzzles.
- Every classification is a span field (`failure_class`, `hints`), so the digest line says why each rung was taken.
- Lands in: **engine** (core + ladder), fed by **harness** relay journal. Effort: medium. Value: high.

---

## 9. Streaming

**How Hermes does it.** (LOOP "Callback Surfaces"; SRC `agent/chat_completion_stream_monitor.py`, `agent/error_classifier.py`)
- Eight callbacks carry progress to each door: tool progress, thinking, reasoning, clarify, step, stream delta, tool-call-being-generated, status.
- A request-local **stream monitor** touches an activity clock every 30 s so gateway watchdogs do not kill a slow first token. After 60 s with no chunk it emits one **wait notice per silence** that says what the wait is (first chunk or mid-stream) and when stale-stream recovery will start.
- **Sleep-aware stall clock**: if the computer slept, the stall timer skips the sleep, "so the request gets its full patience again after wake".
- A provider that answers streams with only empty SSE frames makes the session **switch to non-streaming** instead of re-streaming into the same failure (`PROVIDER_STREAM_EMPTY_FRAME_ERROR_CODE`).
- An interrupted stream injects no partial text into history (LOOP).

**What QMX has.** The harness reader routes `Delta` facts to the live channel (DESIGN step 4). The engine watchdog counts "a tool call, a log line, a turn or a chunk event" as progress and never the worker heartbeat (AD-16, B-55).

**SDK owns it.** Streaming and partial-message handling inside the CLI.

**Gap.**
1. The PC sleeps; the watchdog's idle timer would count sleep as idleness and could park a healthy node after wake. [inferred]
2. A long first-token wait (slow model, long prefill) looks like "stuck" on a run card with no explanation.

**Proposal.**
- **Adopt** a sleep-aware idle clock in the engine watchdog: detect a wall-clock jump larger than the tick, and move every attempt's idle timer forward by the slept time. Lands in: **engine** (runner/watchdog; the core never reads clocks per AD-6, so this lives in the runner). Effort: small.
- **Adapt** the wait notice: the harness emits a `waiting_on_model{seconds, phase}` fact after 60 s of silence (once per silence); the run card shows "waiting on <model> for 2 min (first token)". Lands in: **harness** + **UI**. Effort: small.

---

## 10. Gateway and multiplexing

**How Hermes does it.**
- **Gateway** (GW, GWLIFE). Each platform adapter turns an event into a `MessageEvent`; the runner authorizes, builds a session key `agent:{namespace}:{platform}:{chat_type}:{chat_id}[:thread][:user]`, and runs an `AIAgent`. A **two-level guard** handles messages that arrive while a turn runs: the adapter queues the message and sets an interrupt; the runner lets `/stop`, `/approve`, `/deny`, `/status`, `/queue` through inline and routes everything else by a per-command **busy policy**. Each session has a `busy` input mode: `interrupt`, `steer` (deliver at the next tool boundary) or `queue`. `steer` and `redirect` require the current `execution_generation`, so a stale control is refused with `stale_generation`.
- **Multiplexing** (MUX) means **one gateway process serves every profile** (separate homes, keys, sessions, adapters, cron ticks) on one event loop and one HTTP listener. The constraint: "profile A's turns must never observe profile B's state." The mechanism is two **context variables** set around every seam where profile code runs: a home override (config, `state.db`, skills, memory resolve under it) and a **secret scope** (the profile's `.env` and secret sources). Nothing is written to `os.environ`. Under multiplexing, a secret read with no scope installed raises `UnscopedSecretError` instead of falling back to the process environment: "An un-migrated call site fails loud at that exact line instead of leaking another profile's value." Child processes get the scope's env explicitly; background threads copy the context. A route to an unserved profile is dropped, never delivered to the default.

**What QMX has.** No messaging gateway; the inbox is the one notification channel (AD-17). One engine instance per home (AD-3); per-attempt run passes (AD-28); script isolation tiers (AD-24); env scrub at boot (DESIGN "Boot and the environment").

**Gap.**
1. The engine runner executes many runs in one process (AD-3: task group plus threads in `qma.serve`). Nothing structural stops one run's executor from reading another run's pass, workspace or Library prefix by accident; isolation rests on each call site passing the right `run_id`. Hermes' answer is a context-local scope that fails closed.
2. The copilot chat has no stated busy policy: what happens to an operator message sent while a turn runs.

**Proposal.**
- **Adopt** a `run_scope` context variable in the engine runner: set at attempt start (run id, attempt, pass, write prefix, zone path), copied into worker threads with `copy_context()`, unwound in `finally`. `LibraryPort`, the relay client and the zone resolver read it; a call with no scope raises `UnscopedRunError`. Lands in: **engine** (runner, ports). Effort: small to medium. It is a structural backstop for AD-24 and AD-28.
- **Adapt** a busy policy for copilot chats: default `queue`, with `/stop` and approvals passing through. Whether the SDK lets QMX inject text mid-turn as a steer is [inferred: the CLI supports queued input; probe before promising `steer`]. Lands in: **harness** + **UI**. Effort: small after the probe.
- **Skip** the messaging gateway and its platform adapters. If a phone channel is ever wanted, study 37b covers adapters.

---

## 11. Session storage

**How Hermes does it.** (STORE)
- One SQLite file per profile (`state.db`, WAL mode) with `sessions`, `messages`, three FTS5 indexes (word, trigram, CJK) and the runtime ledgers (admissions, worker executions and receipts, delivery obligations). **The gateway is the only writer**; CLI, desktop, API server, cron and workers are clients that write through it.
- Each message has a durable `message_uid` that survives compaction copies, plus `absorbed_message_uids` when rows are merged and per-occurrence `tool_call_uids` (provider tool-call ids repeat).
- `api_content` keeps the exact bytes sent when they differ from what is shown.
- Compaction archives rows (`active=0`); "Do not delete these archive rows as duplicates."
- Session lineage via `parent_session_id`; token, cache and cost counters per session; source tagging per door.
- Browsing opens the database **read-only** and never creates, repairs or migrates it; only the owner does.

**What QMX has.** SDK JSONL is the transcript, with no QMX copy; the block log in `control.db` is written only through `ControlService` (DESIGN "Single owner per state"). Engine ledger in `engine.sqlite`, one writer (AD-23). Memory rows are Library objects with an FTS5 recall index (AD-18). `MemoryPort.search_runs` exists.

**SDK owns it.** The transcript format and its compaction copies.

**Gap.** Small. QMX already has single writers. What is missing: a search tool over past chats for agents (Hermes' `session_search`, which the compaction summary points to), and a read-only rule for UI browsing of `engine.sqlite`.

**Proposal.**
- **Adapt** `session_search`: a `qmx` read tool over the block log's FTS (copilot chats) and `search_runs` (workflow runs), used as the recovery pointer in §4. Lands in: **harness** tools + **Library**. Effort: small.
- **Adopt** "browsing is read-only": UI and REST reads open `engine.sqlite` with `mode=ro` and return 503 when the schema is not ready; only the engine migrates. Lands in: **engine** service. Effort: tiny.

---

## 12. State DB and recovery

**How Hermes does it.**
- **Durable admission FIFO** (GW "Shared authority pending-input snapshots", STORE): every input is a row `queued → started → terminal`. A turn that was `started` when its owner died becomes **`unknown`** at the next start: Hermes "cannot prove which side effects happened, so it neither replays the input nor lets the queued turns behind it run." The operator resolves it with `prompt.resolve_unknown(admission_id, execution_generation)` (desktop shows "Turn lost during restart" with a Discard button); the follower then runs exactly once.
- **Active-turn marker and delivery ledger** (GWLIFE §7): a marker is set at turn start and held until the reply is in the delivery ledger. On start after a crash (no `.clean_shutdown` file): reply persisted but not ledgered → deliver it once with a "Recovered reply" notice; no reply persisted → `resume_pending`, auto-continue once. Markers are compared as UTC epoch seconds so a time-zone change cannot mis-match them.
- **Stuck-loop detection**: a session active across 3 consecutive restarts is suspended (fresh session next time) (GWLIFE).
- **Derived vs canonical data** (RECOVER): if the FTS index is corrupt, record `fts_stale`, drop the FTS triggers in the same transaction, keep canonical writes going, and serve search from a `LIKE` fallback; never rebuild inside a live write. If the file itself is corrupt, **quarantine the handle**: fail every later write at once, never reopen, and skip the WAL checkpoint on close. The page explains why: a handle that kept writing for ~50 minutes after a structural error "turned a damaged-but-readable file into one that no longer opened at all". Repair runs only with every writer stopped, takes a backup first, and must never lower canonical row counts.
- **Durable background completions** (DELEG, BACKLOG): a finished delegation is stored before it is announced; consumers take a durable claim; delivery is at least once; a delegation whose owner died mid-run is `unknown`, never resumed.

**What QMX has.** AD-7 node memos (finished work never reruns); AD-8 unknown outcomes (`irreversible_external` never retried; a model call retried once); the harness "unknown-outcome resume rule" (DESIGN §3 "Constraints"); B-6/L-7 (chat options lost on restart); AD-18 says the memory index is rebuildable.

**Gap.**
1. The engine handles unknown node outcomes, but a **whole host restart** in the middle of runs has no counter: a run that crashes the host each time it resumes will crash it forever. [inferred]
2. Copilot chats: if `qma.serve` dies mid-turn, there is no marker, so the operator's last message may silently have no reply.
3. No live behavior is written for a corrupt `engine.sqlite`, a corrupt Library FTS index or a corrupt `control.db`.

**Proposal.**
- **Adopt** a restart counter per run: on each boot, a run that was `running` gets `restart_count += 1`; at 3 it is parked with reason `crash_loop` and one inbox item, never resumed again. Lands in: **engine** (runner boot, AD-16 watchdog). Effort: small.
- **Adopt** the active-turn marker for copilot chats: write `turn_started` in the chat record before `client.query`, clear it on the `ResultMessage`. On boot, a chat with a marker and no result shows a "turn lost during restart" block with "resend" and "discard" buttons; nothing is replayed automatically, because the turn may have run tools. Lands in: **harness** (`home.py` chat record) + **UI**. Effort: small.
- **Adopt** the derived-index rule for the Library FTS and memory recall index (detach on corruption, `LIKE` fallback, rebuild only offline) and the quarantine rule for `engine.sqlite` and `control.db` (fail writes, no checkpoint, keep the WAL for forensics, one `urgent` inbox item). Lands in: **engine** ledger, **Library**, **harness**. Effort: small.
- Fix B-6/L-7 (HG3 item 2) in the same round: options that must survive a restart belong in the chat record, the same lesson Hermes learned with "frozen local launch credentials" (GW).

---

## 13. Programmatic integration (API and SDK)

**How Hermes does it.** (API)
- Three protocols, one core: ACP over stdio for IDEs; a JSON-RPC protocol (stdio or WebSocket) for custom hosts with every feature; an OpenAI-compatible HTTP server with SSE. In-process Python is the fourth.
- **Questions the agent asks are server→client requests**, not events: approval, clarify, sudo, secret. The client answers with a JSON-RPC response bearing the same id. A client must advertise once that it answers them (`client.capabilities {server_requests: true}`); otherwise every such request fails at once "instead of stalling for the full deadline". A withdrawn question emits `request.cancel {id, reason}`.
- **Reconnect** returns `open_requests` (still-open questions, so a new client can answer) and `inflight` (the running turn: user text, assistant text so far, corrections, errors), with the same display metadata the stored row will get.
- **Runs API**: `POST /v1/runs` (202 + `run_id`), `GET …/events` (SSE), `…/approval`, `…/steer` (text lands at the next tool boundary; a steer that arrives after the final answer comes back as `pending_steer` on the terminal event so it is not lost), `…/stop`, `…/resolve-unknown`, `GET /v1/capabilities`.
- **Terminal status is honest**: "A run is never reported as completed with `completed: false` or `partial: true` in the same payload." Budget exhaustion is `failed` with `turn_exit_reason: max_iterations_reached(60/60)`; a watchdog stop names its issuer.
- **Destructive writes need a stated intent**: a rewind is a `prompt.submit` with `truncate_before_row_id` plus `confirm_truncate`; deep cuts need `confirm_deep_truncate`; a rewind while busy is refused with `4009`, never queued.
- **Idempotent mutations** with `request_id` and `expected_revision`; replaying the same request returns the original result; a stale revision returns `revision_conflict` (GW "Revision-checked session metadata").

**What QMX has.** AD-21: one Engine API for three surfaces. The harness's HTTP routes, asks with `AskId` and `Answer`, `Quote` with epochs (DESIGN). AD-11 status table shared with the Library.

**Gap.**
1. A UI that reconnects mid-turn cannot rebuild the live turn or the open asks from one call. [inferred from DESIGN: asks are blocks in the block log; the live channel carries deltas]
2. No rule says a run status can never claim success with partial output.
3. No steer for running engine agents and no `pending_steer` return.

**Proposal.**
- **Adopt** a reconnect snapshot: `GET /api/sessions/<id>/live` returns `inflight` (text so far) and `open_asks` alongside the stream. Lands in: **harness** routes + **UI**. Effort: small.
- **Adopt** the honest terminal rule as a test on the engine's status table: `passed` implies no `partial`, no `truncated`; `max_turns` exits map to `failed` with `exit_reason`. Lands in: **engine** service. Effort: tiny.
- **Adopt** `request_id` + `expected_revision` on every mutating Engine API call (draft save, publish, trigger enable). Lands in: **engine** service + **UI**. Effort: small.
- **Skip** ACP and the OpenAI-compatible server for now; nothing in QMX consumes them.

---

## 14. Sub-agents and delegation

**How Hermes does it.** (DELEG, LIFE, LOOP)
- `delegate_task` spawns child agents with a **fresh conversation**: "Subagents know nothing." The parent must pass `goal` and `context`; the child also gets the workspace's project files. Only the child's final summary enters the parent.
- **Batch**: up to 10 children in parallel (configurable). A top-level call returns a **handle at once** and the results arrive later as a new message between the parent's turns; the parent is told to end its turn rather than poll. An orchestrator child waits for its own workers.
- **Structured output contract**: each task may carry `output_schema`. The parent validates; on failure it sends **exactly one correction turn** with the validation errors verbatim. If that fails too, the result keeps `status: completed`, the raw text, `schema_valid: false` and the errors: the work is never thrown away.
- **Inherited tools only**: a child cannot be granted tools the parent lacks. Blocked in children: `delegate_task` (except orchestrator roles, bounded by depth), `clarify`, `memory` writes, `send_message`, `cronjob`.
- **No wall-clock timeout by default.** Earlier fixed caps "kept killing legitimately busy children". Instead a heartbeat staleness monitor interrupts a child with no progress for 450 s between turns or 1,200 s inside a tool; a model wait counts as progress.
- **Process ownership**: a child's background processes die with it; it must wait, kill or **hand off** a process to the parent (max 3), and anything left running is named on the result as `orphaned_processes`, "so the parent hears from the runtime, never from the child's prose".
- **Durable completions**: stored before announcement, claimed once, delivered at least once; a child whose owner died mid-run is `unknown`.
- **Lifecycle API for plugins** (LIFE): `launch`, `status`, `wait`, `cancel`, `steer`, `result`, `reconnect`; states `PENDING, STARTING, RUNNING, SUCCEEDED, FAILED, INTERRUPTED, CANCEL_REQUESTED, CANCELLED, UNKNOWN`; cancel is cooperative; results are immutable, bounded to 32k characters, carry a hash, and omit transcripts and hidden reasoning; handles are opaque and unforgeable.
- **Cost pattern**: frontier planner, inexpensive workers (`delegation.model`), because "a parallel batch of subagents typically burns the large majority of a run's total tokens".
- `/review` starts a full-privilege reviewer child over the last 10 messages; its findings come back into the same session.

**What QMX has.** AD-4: an agent node declares `subagents` (`max_concurrent` 3-5, depth 1, each with a role and `max_turns`, tokens carved from the node's runaway allowance); they run in the same chat tree and sandbox. AD-29: sub-agents may use other providers through the relay. DESIGN: `mcp__qmx__delegate` starts a `Child` chat and **blocks** the parent's tool call until the child ends; the gate denies `delegate` inside native sub-agents. AD-5: `agent` nodes return structured output. Engine `chunk` edges give wider fan-out than sub-agents (AD-34).

**SDK owns it.** Native Claude Code sub-agents (Task tool): fresh context, own tools list, final report only, injection scan of reports (DESIGN "Untrusted content").

**Gap.**
1. Structured output: no rule for a schema miss. [inferred: today a node either fails or parses loosely]
2. `delegate` blocks the parent and may need `MCP_TOOL_TIMEOUT` raised (DESIGN "Tradeoffs").
3. Sandbox processes a sub-agent starts have no ownership rule.
4. No reviewer pattern as a first-class step.

**Proposal.**
- **Adopt** the output contract on `agent` and `llm` nodes: validate against the node's output schema; on failure resume the same chat once with the errors verbatim (no schema re-paste); on a second miss finish the attempt `ok` on a `raw` port with `schema_valid: false` and `schema_errors`, and let a downstream `rule` or `grader` decide. Never rerun the whole attempt for a format slip. Lands in: **engine** (`nodes.agent`, `nodes.llm`). Effort: small. Value: high (saves whole agent attempts).
- **Adopt** the lifecycle states and result rules for `delegate`: make it return a handle at once, deliver the result as an `InjectedText` turn between the parent's turns, store completions durably before announcing them, and bound results (32k, hash, no transcript). Lands in: **harness** (`delegate`). Effort: medium. It removes the blocking trade-off.
- **Adopt** process ownership in the sandbox: processes started in an attempt's container belong to that attempt; on attempt end the sidecar kills them and lists `orphaned_processes` on the result. Lands in: **engine** workers (sandbox tool server). Effort: small.
- **Adopt** the blocked-tools list for engine sub-agents: no `irreversible_external` tools, no memory scope above `run`, no publish or trigger tools. Most of this is already true through AD-18 and AD-22; write it once as a deny list on sub-agent definitions. Lands in: **engine** + **harness** plugin agent definitions. Effort: tiny.
- **Adapt** `/review` as a template, not a feature: a `grader` node in `llm` mode on the `judge` role, wired after any node that produces a PR or a report. Lands in: **Library** (template) + **mini apps**. Effort: small.
- The heartbeat-staleness idea is already AD-16's idle timeout; keep it and keep "no wall clock while waiting" (L-48).

---

## Top 10 ideas to adopt (ranked by value per effort)

| Rank | Idea | From | Lands in | Effort | Why it ranks here |
|---|---|---|---|---|---|
| 1 | **Prompt-surface snapshot test** per chat kind and node kind (system text, tool lists, MCP schemas), committed and checked in CI | §3 | harness + engine CI | small | Would have caught B-51, B-70 and B-53 before a run; makes every prompt change reviewable |
| 2 | **Failure classifier with recovery hints** feeding the AD-16 ladder; doctor only for `unknown` or repeats | §8 | engine core + relay journal | medium | Turns guesses into rules; saves doctor spend; every rung explained in the digest |
| 3 | **Output contract with one correction turn**, never discard the work | §14 | engine `agent`/`llm` nodes | small | Saves whole agent attempts lost to a format slip |
| 4 | **Engine-built re-seed for the AD-34 fallback**: brief and instructions verbatim, seven-heading summary, regex anchor index, pointer to the Library trace | §4 | engine + Library | small-medium | Keeps the operator's intent intact across compaction; Hermes measured better recall with a third of the tokens |
| 5 | **Grace turn at `max_turns`** that writes a partial result, with `exit_reason` and `truncated` | §2 | engine | small | A budget stop leaves usable output instead of an error |
| 6 | **Crash-loop counter** (park a run after 3 host restarts) and **active-turn marker** for copilot chats ("turn lost during restart") | §12 | engine runner + harness + UI | small | Stops endless crash loops; no silent lost turns |
| 7 | **Per-model compaction thresholds with a small-window floor** and "wait for real usage" | §4 | engine settings | tiny | One config change; avoids early compaction on 128K-window key models |
| 8 | **Fallback re-runs preflight**: on a ladder step to another model, recompute window, `compact_at` and chunk fit | §7 | engine ladder + chunk planner | medium | Prevents a 300K chunk going to a 200K model after a fallback |
| 9 | **Derived-index and corrupt-file rules**: detach a corrupt FTS and keep writing; quarantine a corrupt database handle, no checkpoint | §12 | engine ledger, Library, harness | small | Cheap insurance against turning a damaged file into a lost one |
| 10 | **`run_scope` context variable that fails closed** for passes, write prefixes and zones in the runner | §10 | engine runner + ports | small-medium | A structural backstop for the AD-24/AD-28 security findings |

Next tier, worth a line each: sleep-aware watchdog clock (§9); wait notice "waiting on model, first token" (§9); reconnect snapshot with `inflight` and `open_asks` (§13); honest terminal-status test (§13); non-blocking `delegate` with durable completions (§14); learned relay quirks and context windows (§7); one-shot note for mid-session skill changes (§3); flow-invariants block in `AGENTS.md` (§1).

Skipped on purpose: micro-compaction (needs history rewrites the SDK forbids, and breaks the plan's cache every turn); a pluggable context engine; the messaging gateway and its adapters; ACP and the OpenAI-compatible server.
