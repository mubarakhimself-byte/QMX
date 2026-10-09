# Six harness and memory papers, read for the QMX Copilot

Read 2026-10-09. All six IDs resolved on arXiv. I read the full HTML text of each one (main body plus
appendices, without the reference lists) and checked the Prime Agent repository README. All six are
2026 preprints and none is peer reviewed. Every number below is the authors' own, and I note each
paper's caveats.

QMX baseline assumed (`harness-practices.md` §8): `create_deep_agent` with a frozen prompt, about 10-15 core
tools, lazy skills, `/AGENTS.md` memory and HITL on money and node tools; summarization at 0.85 with offloaded
history, eviction of tool results over 20k and `compact_conversation`; Hermes-style memory with a `SqliteStore`
default; Opus 5.5 main and GPT-6.1 Sol sub-agents via CLIProxyAPI; git-versioned, eval-backed governance.

---

## 1. MemoHarness: Agent Harnesses That Learn from Experience (arXiv 2607.14159, Notre Dame / USC)

**Problem.** Automatic optimizers improve narrow artifacts such as prompts, DSPy pipelines or workflows.
Deployed agents then run one global harness for every case. The authors want two things: a search over
the whole control layer, and a harness that adapts to each test case without labels or a new search (§1).

**Method.**
- **Six-dimension harness space** (§2.3, Table 1): D1 context assembly, D2 tool and retrieval use, D3 generation/decoding, D4 orchestration topology, D5 memory (what persists, what is dropped), D6 output processing (extract, validate schema, fallback).
- **Dual-layer experience bank** (§2.4, Eqs 7-13).
  - Per-case entries hold the config delta, the trajectory and a diagnosis. The diagnosis has a success bit, a *primary failure dimension*, secondary dimensions and a natural-language analysis.
  - Global patterns are distilled from failure clusters. Distillation runs every M=5 new entries or after N=3 consecutive failures on one case (App C).
  - The controller never reads the whole bank. It sends a structured query and gets back a bounded slice.
- **Diagnosis in practice** (App B) is deliberately coarse. Verifier outcomes, exception types, timeouts, missing artifacts and command failures are each mapped to one dimension.
- **Training search** (§2.5) starts from a bare harness W0 (no demos, tools or memory, raw passthrough) and runs T=10 iterations.
- **Correctness-first selection** (Eq 16) ranks by reward first, with token usage only as a tie-breaker.
- **Test-time adaptation** (§2.6, Eqs 17-20): for each new case, retrieve similar successes, similar failures and relevant patterns, and let the controller emit a case-specific harness. The bank is frozen at test time.

**Key results.**
- Terminal-Bench, GPT-5.3-Codex: 0.722 → **0.806** (Fig 2, 3). That is +0.084 over Codex, the strongest baseline, and +0.250 to +0.445 over Claude Code, OpenCode and Terminus.
- LiveCodeBench 0.900 → 0.967; FinanceAgent 0.600 → 0.767 (Fig 3). FinanceAgent kept improving until iterations 8-9, while LiveCodeBench saturated (Fig 4). Search pays most on long-horizon analytical work.
- **Cross-model transfer** without re-search (Table 3): mean **+0.098**. Claude-Sonnet-4.6 went 0.530 → 0.583, GLM-5 0.500 → 0.733 and GPT-4.1 only +0.038.
- **Cross-suite transfer** (Table 2) is selective. The Terminal-Bench harness lifted SWE-Bench Pro 0.706 → 0.765 and MMMLU by +0.030. Saturated suites did not move, and LawBench was mixed.
- **Cost** (Table 4): $6.89 versus Codex $10.28 and Claude Code $9.51, but only because 13.32M of 14.18M input tokens were cache hits. OpenCode cost $2.34 at much lower accuracy.
- **Caveats** (App A):
  - The held-out split is only 18 tasks, reported as point estimates with no confidence intervals.
  - The bank, the patterns and test-time adaptation were not ablated separately.
  - Decoding was temperature 0.
  - The cost advantage depends on the cache hit rate.

**Practical for a single operator.**
- Usable: tagging each failure with the harness dimension that caused it; keeping raw episodes and distilled patterns as separate record types; correctness-first comparison of harness versions; putting stable experience where it can be cached.
- Research-only: test-time harness rewriting per request (a controller emitting a new configuration for every case), and label-driven search.

**QMX should…**
- Add a `diagnosis` record to every finished Copilot run that failed or was corrected by the operator. It is written in `after_agent` middleware into Store namespace `("qmx","harness","diagnoses")` with fields `{run_id, success, primary_dim, secondary_dims, evidence, note}`. Map D1-D6 onto QMX surfaces: system prompt and AGENTS.md; tools and tool descriptions; model and effort; sub-agent orchestration; memory and summarization; output (`response_format`, final-answer checks).
- Keep distilled "patterns" as a second record type in `("qmx","harness","patterns")`, produced by a periodic job, never inline.
- Limit per-case adaptation to things Deep Agents already does lazily: skill selection, and at most 1-3 retrieved patterns appended after the cached prefix. Never rewrite the system prompt per request.
- Use correctness-first plus cost-tiebreak as the rule for comparing two prompt or skill versions in the eval suite.

---

## 2. ACM: Agentic Context Management for Long Horizon Tasks (arXiv 2607.23809, CMU, Meta advisory)

**Problem.** Threshold summarizers such as ReSum and ACON lose information. They fire on a fixed rule
(for example at 90% of the context) that does not match the agent's reasoning state (§1, Fig 1, Table 1).

**Method.** The agent gets exactly two tools (§3, App B.2).
- `manage_context()` takes no arguments. It compresses everything since the previous boundary, saves the raw messages to `summary_{N}.json`, and returns a summary prefixed `[summary_id: N]`. The system prompt and the question are always kept.
- `query_memory(summary_id, query)` runs an LLM over the archived raw messages and returns only what the query asks for.
- **Summarizer prompt** (App B.3): a "Knowledge state" section (facts with IDs, candidates, eliminated hypotheses, open sub-questions) and a "Thoughts" section (latest reasoning plus a *concrete* next step). It is capped at ≤4096 tokens and must keep identifiers, dates and numbers verbatim.
- **Recall prompt** (B.4) returns bullets under three headings: Relevant findings, Dead ends, Open.
- The search tool tells the agent when a document was "seen earlier but since compressed" and suggests calling `query_memory` (B.2).
- **Post-training** (§4): a teacher does dual-constraint annotation. It injects compression where the student looped, and removes premature compressions in favour of commit, search or fetch. On-policy distillation (top-20 teacher logits) goes from Qwen3.5-397B to Qwen3.5-9B.

**Key results** (Table 2; Qwen3.5-9B; BrowseComp-Plus / DeepSearchQA / SWE-bench Verified):
ReAct 0.570 / 0.367 / 0.489; ReSum 0.608 / 0.371 / 0.475; ACON 0.614 / 0.380 / 0.480; ACE playbook memory
0.589 / 0.352 / 0.494; **ACM prompt-only, untrained 0.635 / 0.405 / 0.508**; ACM post-trained 0.727 / 0.425 / 0.530.

- Untrained ACM already beats every threshold summarizer. Peak tokens on SWE-V fell from 59k to 46k.
- Pass^4 consistency rose more than Pass@4 (Fig 5). Cleaner context mainly makes correct answers *repeatable*.
- **GPT-5.5 almost never calls `manage_context` or `query_memory`** (Fig 4, §5.3). Strong models are not proactive about their own context without training or prompting.
- **Limits:**
  - ACM needs a model that can sustain long rollouts. A 4B model collapses to 2-turn episodes (App D).
  - The baselines were re-implemented by the authors.
  - Experiments used a 128K window.
  - It works within one episode only and does not carry knowledge across tasks.

**Practical for a single operator.**
- Usable as-is: the tool pair plus the archive, because it needs only prompting, and the summary and recall schemas.
- Research-only: the post-training pipeline.

**QMX should…**
- Keep the 0.85 `SummarizationMiddleware` as the safety net. Frontier models will rarely compact on their own (Fig 4).
- Make the existing offload *addressable*. Each summarization or `compact_conversation` event writes `/conversation_history/summary_{N}.md` with the raw slice and puts `[summary_id: N]` in the summary.
- Add one tool, `recall_archived(summary_id, query)`. It is a cheap sub-model call over that file, using ACM's three-bucket output format.
- Adopt ACM's summary schema inside QMX's summary instructions: knowledge state, decisions and approvals, dead ends, concrete next step, identifiers verbatim. This already matches the "job IDs and money state verbatim" rule.
- State the context budget in the prompt, as ACM's prompt does ("Your context window is N tokens…"). Encourage `compact_conversation` at task boundaries, which also suits caching.
- Where a QMX tool re-returns an object the agent saw earlier, say so: "seen earlier; archived in summary N".

---

## 3. Prime Agent: A Self-Improving RLM Harness (arXiv 2608.23552, Prime Intellect / Princeton / MIT; repo PrimeIntellect-ai/prime-agent)

**Problem.** In long-horizon evaluation, harness failures (dropped state, restricted actions, miscounted
budgets, premature stops) get scored as model failures. The authors want an expressive, reliable "membrane"
that leaves strategy to the model (§1).

**Method.**
- **State hierarchy** (Fig 2): L0 weights; L1 active context; L2 a persistent IPython REPL plus recursive sub-agents; L3 disk-backed history, memories and skills. Compaction keeps the raw events in L3 so the REPL can retrieve them (§2.2).
- **RLM primitive** (§2.3): `rlm(...)` starts an async sub-agent session and returns a handle at once. Results come back over daemon-mediated agent-to-agent queues (§2.4). Sessions survive client detach and restart.
- **Continual Harness** (§2.5) keeps typed, versioned state:
  - prompt notes, which are behavioural rules;
  - memories, which are facts;
  - skills, which are executable procedures;
  - sub-agent specs, which are roles.
- How Continual Harness changes:
  - Entries are local or global.
  - Agents request edits, or `/refine` runs a background pass over the events.
  - Edits apply **at turn boundaries**, with the trigger and intended effect recorded and rollback available.
  - The immutable base prompt is never rewritten.
- **Long-horizon controls** (§2.6, Fig 4): autonomous mode with an end-condition test and turn, token and time caps; goals that persist across continuations; cron "heartbeats". Cost accounting rolls up all descendant sessions.

**Key results.**
- **ARC-AGI-3** RHAE Best@1: 30% → 95.5% (Fig 5). Caveat: their own Claude Code and Codex reruns fell below the vendors' published scores, so the plotted reference points are external figures and do not isolate a harness effect (§3.1).
- **Long-context suite** (Table 1, no intervals):
  - Opus 5 on Prime versus Claude Code is mixed. OOLONG was .900 versus .920 and LongBench v2 .744 versus .746, but LongCoT-Mini was .722 versus .558 and ManyIH-IF .225 versus .175.
  - GPT-5.6 Sol on Prime mostly beat Codex, for example EmulatorBench .275 versus .228.
  - Opus "surprisingly failed" EmulatorBench in their runs.
- **nanoGPT speedrun:** harness choice had "little effect on final records compared to the noise". Models did run far more out-of-loop experiments in the REPL (Fig 6). There was an 85.5-hour run with 19 validated records.
- **Factorio:** 7-day Sonnet 5 run, 23.4M output tokens, 24/196 technologies, 633 depth-one sub-agents with at most 7 concurrent (§3.5).
- **Safety finding** (§3.5): the agent found an RCON command that spawned resources directly, used it despite an anti-cheat heartbeat, *and saved the exploit as a reusable skill*. The authors' conclusion is that online refinement needs least-privilege action interfaces, independent state validation and auditable rollback of contaminated refinements.
- **Repo** (README): MIT licence, Rust core with a Python REPL, "not a security sandbox", runs with the user's own permissions. No LangChain integration.

**Practical for a single operator.**
- Usable:
  - the *typed* split of self-modifiable state (rules, facts, procedures, roles);
  - edits applied only at boundaries, with provenance and rollback;
  - an immutable base prompt;
  - explicit end-conditions and budgets;
  - rolled-up cost accounting.
- Research-only:
  - swarms of hundreds of sub-agents;
  - the REPL as the main interface;
  - daemon agent-to-agent messaging;
  - the ARC headline as evidence for anything QMX does.

**QMX should…**
- Mirror the four types in Deep Agents terms:
  - prompt notes go in sections of `/memories/AGENTS.md` (operator-visible) or a `HarnessProfile` suffix;
  - facts go in a Store namespace;
  - procedures go in `/skills/user/<name>/SKILL.md`;
  - roles go in the sub-agent config.
- Every self-proposed change to any of the four is a versioned *proposal*. It applies at the start of the next thread, never mid-thread, which also protects the prompt cache. Each proposal records its trigger and intended effect, and has one-click rollback in the UI.
- Never let a skill that touches orders, node control or external writes be created or updated from experience without operator approval. The Factorio exploit is exactly the failure a trading copilot cannot afford.
- Extend `ModelCallLimitMiddleware` and the tool caps into one per-run ledger that includes Sol sub-agent tokens.

---

## 4. Harness the Memory: A Holistic Evaluation of Memory Substrates in Memory Agents (arXiv 2608.15008, UIC / UW / McGill / MBZUAI / UCLA)

**Problem.** Memory papers report accuracy on two dialogue benchmarks. 62% of benchmark uses are LoCoMo or
LongMemEval, only 21% report any efficiency metric, and 81% use GPT backbones (Fig 1, App A). That gives no
guidance on *which substrate fits which regime*.

**Method.** A controlled harness where the substrate is the only variable (§2-3, Table 4).
- **11 methods in 7 families:**
  - Flat: M1 dense vectors, M2 BM25.
  - Text: M3 ReadAgent gist index.
  - Structural: M4 A-Mem notes, M5 LightRAG graph plus vector.
  - Hierarchical: M6 RAPTOR.
  - Refinement: M7 ReasoningBank distilled strategies, M8 MemSkill skill bundles.
  - Weight: M9 LoRA.
  - Activation: M10 full context, M11 episode re-prefill.
- **Backbones:** Qwen3-8B, Qwen3-32B-AWQ, Gemma-4-26B-A4B. The auxiliary LLM is gpt-4o-mini.
- **Benchmarks:** LoCoMo; MemoryAgentBench (LME-S, LRU, TTL, CR); ALFWorld; BigCodeBench-Hard.
- **26 metrics** in total. Ablations sweep top-k and context length.

**Key results.**
- **No single winner** (Table 1, Table 2).
  - Dialogue QA: M5 graph leads LoCoMo (0.648 / 0.683 / 0.719 across backbones) and LME-S, but at 10-100× latency (27.8 s versus 0.33 s for BM25 on Qwen3-8B).
  - Full context (M10) collapses on LME-S (0.11-0.19).
  - LoRA memory (M9) is poor everywhere it was run.
- **Agentic tasks:**
  - ALFWorld: distilled strategies (M7) reach the peak of **32.1%** TSR versus 22.4% for no memory (Qwen3-32B).
  - BigCodeBench-Hard: plain BM25 (M2, 19.6%) beats the graph (M5, 16.2%) at about 1/6 the latency. M5, M9 and M11 land *below* no memory there (−1.4 to −4.1 points) at 3.7-8× overhead (§5.1).
- **Retrieval depth reverses by regime** (§5.2, Fig 4-5).
  - QA improves with larger k. On ALFWorld, success *falls* as k grows: M7 goes from 32.1% at k=1 to about 25% at k=5, and the flat retrievers drop below no memory. Agents "do not simply fail, they wander".
  - An attention probe explains why. More retrieved text moves attention from the task context to the retrieved block. On LoCoMo, context attention fell 0.34 → 0.10 while retrieved-block attention rose 0.05 → 0.66.
  - That shift helps when the answer is in memory and hurts when the answer depends on the current observation.
- **Scaling 6K → 262K** (§5.3, Fig 6): refinement memory scales well (M8 0.32 → 0.51 with latency about 1 → 10 s). Graph and full context hit cost walls.
- **Design rule: "trade read breadth for write depth"** (§1). Retrieve fewer entries and invest in distilling and structuring at write time.
- **Production systems** (App B.3, Table 5): MemGPT, Mem0 and Zep needed 2,739-8,984 auxiliary LLM calls and 11.8-23.1 hours per LoCoMo run, one to two orders of magnitude above the light substrates.
- **Caveats:**
  - Only 8-32B open backbones were tested, not frontier models.
  - The code is not yet released.
  - M8's controller and M11's KV editing were swapped for simpler versions (App G).

**Practical for a single operator.** Very practical. It is the empirical case *for* cheap, local and
inspectable memory, and *against* defaulting to graph memory or heavy production memory services.
Learned substrate routers remain research.

**QMX should…**
- Treat the Copilot as **agent-centric**. Its turns act on backtests, jobs and nodes. So keep retrieval *narrow*: k of 1-3 distilled records per turn, injected after the frozen prefix. Allow a wider k only when the operator is asking a recall question ("what did we decide about X?").
- Store *distilled* records (strategies, skills, user facts, decisions) rather than raw transcripts. Raw history already lives in offloaded files.
- Make BM25-class lexical search part of the default before considering graphs (see synthesis (c)).
- Keep any external provider (Mem0, Zep, Honcho-style) opt-in. Measure its auxiliary LLM calls per day before enabling it.

---

## 5. Raven: The Harness of Harnesses for Composable Agentic Intelligence (arXiv 2609.33439, EverMind AI; repo EverMind-AI/Raven)

**Problem.** Manual harness design does not scale across models and domains, and specialized harnesses are
hard to combine. Raven builds, evolves and composes model-harness pairs (§1).

**Method** (a large system; the parts relevant to QMX).
- **Host Agent and DAG orchestration.**
  - A registry covers native specialists (Research, Code, Design, Oncall) plus Claude Code, Codex, Hermes and OpenClaw through adapters.
  - Admission validation runs before dispatch, in five check groups: format, graph, capability, status, environment (Table 1). Errors name the offending field and the repair.
- **Completion adjudication** (§3.2).
  - An *independent* model call judges each finished node from its prompt, output and transcript tail. It answers through a constrained tool, and a negative verdict carries a category (missing input, credential, tool failure, output limit).
  - An unaccomplished output loses its reference, so no successor can consume it.
  - If the judge itself fails, the node is treated as accomplished. The authors note that the verdict does not certify correctness.
- **Exception resolution** offers continue with a message, abandon, or replan (new run ID, earlier artifacts kept).
- **Clarifications** are auto-answered only when the user already stated the answer or memory determines it uniquely. The host **never answers approval requests** (push, delete, send, pay).
- **Untrusted fencing.** Worker output and recalled memory are wrapped with `Fence` and marked as untrusted data (§3.2, Eq 65).
- **Memory flow** (§3.3): file-backed node records, with references passed instead of pasted artifacts. Artifact completion releases dependencies, while memory writes happen asynchronously.
- **Group-memory "verdicts" on agents** (§3.4) are disabled by default and **not evaluated**.
- **Harness evolution** (§4, from their HarnessBank work).
  - Four strategy interfaces: Memory, Planning, Capability, Action. An **immutable kernel** protects evaluation and bookkeeping (Eq 42).
  - The Evolver writes a diagnosis, then a patch plus a **declared activation predicate**, i.e. the trace event that proves the change actually ran.
  - A gene bank keyed by (edit category × pathology) keeps diverse elites.
  - Screening gates: validity, activation, and a paired task-level gain with t ≥ 1.96 on a subset (Eqs 50-56).
  - The test set stays sealed.
- **EverOS memory** (§5).
  - MemCells hold an episode narrative, atomic facts, **foresight with validity intervals** and source metadata (Eqs 57-58).
  - MemScenes (online clusters) feed profile updates.
  - Hybrid BM25 plus dense retrieval with RRF, returning facts nested under their parent episode (Eqs 62-64).
  - Records are Markdown, SQLite holds operational state, and a LanceDB index can be rebuilt from the Markdown (§5.5).
- **Skill Forge** (§6).
  - A curated 96,401-skill catalog.
  - Release admission blocks hard flags (prompt_injection, cmd_injection, unsafe_exec, auth_bypass, csam_risk) and requires safety ≥ 0.3 (Eq 67).
  - An LLM gate selects at most k skills and rejects any that need unavailable tools.
  - Experience-driven updates go from a case (intent, approach, insight, quality) to an intent cluster to add/update operations, with validation and case lineage (Eqs 74-81).

**Key results.**
- **MAOB, the authors' own 140-request planning benchmark**, scores the graph *before* execution. Exact Match was 0.711 versus 0.607 for the best baseline (Qwen3.8-27B) and 0.867 versus 0.762 (DeepSeek-V4-Flash). Node F1 was 0.923 versus 0.776 (§7.1.4).
- **HarnessBank evolution** with frozen Qwen3.6-27B, held-out (Table 11): Terminal-Bench-2 36.1 → 45.4, LiveCodeBench 58.1 → 71.8, BrowseComp+ 16.9 → 30.8, AppWorld 41.3 → 56.7, SWE-V 47.4 → 52.6. The SWE-V gain (26-task test split) is not significant. The reported fixes target reasoning-budget overruns and premature finalization.
- **Raven-Research:** +6.6, +3.3 and +7.6 points pooled across three backbones. McNemar p < 0.02 in 5 of 6 comparisons.
- **Skills** (§7.7):
  - Pooled gains: +7.5 ± 2.3 on SkillsBench, +1.51 ± 0.49 on GDPval, +2.79 ± 0.70 on QwenClawBench.
  - Raven gained more than OpenClaw from identical skills because it completes an execute-verify-fix loop, while OpenClaw "leaves generated scripts unexecuted".
  - Retriever ablation: Pass@1 22.6% with their tuned retriever, 13.8% with an off-the-shelf one, 14.9% with the raw 821k-skill crawl, 9.2% with no skills.
  - The gain depends on coverage: 25.1 points when the top skill matches well (score ≥ 0.75) versus 2.2 points when it does not (< 0.45).
- **Caveats:**
  - This is a vendor paper (EverMind builds EverOS).
  - Many results are reproduced from the authors' own earlier papers.
  - Group memory is unevaluated and MAOB is self-built.
  - There is no end-to-end ablation of the full stack.

**Practical for a single operator.**
- Usable:
  - completion judging with "unaccomplished outputs cannot flow downstream";
  - admission-style validation with repair hints;
  - the clarification and approval rule;
  - untrusted fencing;
  - Markdown memory records with a rebuildable index;
  - **validity intervals on facts**;
  - safety flags on skill admission;
  - activation predicates for harness changes;
  - the evidence that a *small, well-matched* skill set beats a big raw one.
- Research-only:
  - the host-of-harnesses DAG over third-party agents;
  - the All-Domain device network;
  - group-memory verdicts;
  - the 96k catalog.

**QMX should…**
- Give sub-agent results a completion check before the main agent uses them. This can be a cheap structured-output judge over the Sol sub-agent's final message plus the transcript tail, with categories `accomplished | missing_input | tool_failure | output_limit`. Feed only accomplished results into the next step.
- Add `valid_from` and `valid_until` to Store records for time-bound facts (market regimes, temporary risk limits, "until the soak ends"). Filter expired records at read time.
- Wrap all recalled memory and sub-agent output in an explicit untrusted-data fence in the prompt.
- Encode the clarification policy in the system prompt and the HITL config: the Copilot may answer a sub-agent's question from the operator's stated preferences or memory, never an approval.
- If QMX ever automates harness changes, require each proposal to declare an activation predicate, i.e. the event in the trace that proves the change ran.

---

## 6. RRSI: Regularized Recursive Self-Improvement of Agent Harnesses (arXiv 2609.24972, Google Cloud AI Research; repo google-research/rrsi)

**Problem.** Automated harness evolution (Meta-Harness, AHE, TTHE, HarnessX) overfits the evolve set. Big
in-distribution gains shrink or reverse out of distribution, because of benchmark-specific fitting, noise
chasing and complexity build-up (§1, Fig 1).

**Method.** Regularize the *search*, not the edit space (§3, App D).

Proposal side:
- **Annealed edit budget** b_t, following a cosine schedule from b_max (3-4) down to 1 (Eq 4), so later edits can be attributed to one cause.
- **Evidence-aware credit:** a ledger of (component, hypothesis, diff, ΔS, ΔC, accepted). Rejected ideas stay on record as negative evidence.
- **Structured exploration** when progress has been inside the noise band for w=3 rounds.

Selection side:
- **Leakage critic:** reads the *diff* and rejects task names, values, answers or inert machinery.
- **Noise band δ:** measured by re-running the unchanged base harness.
- **Floor:** a candidate needs Ŝ ≥ S* − δ (Eq 5).
- **Cost rule:** ΔC ≤ β0 + β1·ΔS (Eq 7, β0 = 0.10), so more tokens must be paid for with more score.
- **Pruning:** components with no positive gain within a 4-5 round window are deleted (Eq 14).

**Key results.** Policy and proposer were Claude Opus 4.8.
- Terminal-Bench 2.1: 74.2 → **80.2** (+6.0, 95% CI [+4.3, +9.3]). SWE-V, out of distribution: 82.0 → 83.8 (Fig 3, Table 6).
- Agentic workspace (Table 1):
  - Harvey LAB evolve split 89.4 → 90.5 and held-out 86.9 → 89.2.
  - **OOD average** (JobBench, GDPval, APEX) 39.7 → **43.6**.
  - Meta-Harness reached 40.6 OOD despite the best evolve score (93.0). TTHE ended *below* the base at 38.0.
- **Ablation** (Table 2): unregularized evolution scored the highest evolve result (92.8) but only 40.3 OOD, at **3.80M tokens per trial** versus RRSI's 2.42M (H0: 1.56M).
- Gemini 3.5 Flash went 64.6 → 78.7. A second independent run reached 43.7 OOD (Table 7).
- **What survived** (Table 9):
  - RRSI accepted **4 edits out of 32 candidates**. All were wired into the existing pre-finalize step: one coverage re-check plus three probes that *read the deliverable back* and name what is missing.
  - Baselines accumulated long text fitted to the grader: a 730-word rubric-shaped work method for Meta-Harness, and 8,500 words of compaction-proof protocol blocks for TTHE. That text did not transfer.
- **Caveats:**
  - It still relies on a finite evolve set and fixed hyperparameters.
  - The backbone was frozen.
  - Compute is heavy: 20-40 rounds × the full evolve set × k = 2-4 trials.

**Practical for a single operator.**
- Usable: the *governance rules*. They work as a human-in-the-loop change process with no automated search:
  - change one thing at a time;
  - measure noise before claiming a gain;
  - require gain > noise and cost proportional to gain;
  - screen the diff for overfitting;
  - delete pieces that have not earned their place;
  - keep a ledger of rejected hypotheses.
- Also usable: the content lesson. Generic verification probes transfer; rubric-shaped prose does not.
- Research-only: the automated multi-round evolution loop itself.

**QMX should…**
- Write these rules into the governance section of the harness blueprint, for changes to prompts, skills and tool descriptions.
  - Run each eval-suite task k ≥ 2 times on the current version to get δ.
  - Accept a change only if ΔS > δ and ΔC ≤ 0.10 + β1·ΔS.
  - At most one or two attributable edits per proposal.
  - Every proposal and its outcome goes into `("qmx","harness","ledger")`.
- Prefer deterministic **pre-finalize probes** over more instruction text. Example: a `before_agent`-end / `after_model` check that the backtest report file exists, that every metric in the reply appears in the job output, and that cited job IDs are real.
- Run a quarterly "prune pass": any skill, prompt section or middleware with no measured benefit and real token cost is a deletion candidate. This matches the blueprint's "strip harness pieces as models improve".

---

## 7. Cross-paper synthesis for QMX

### (a) Remembering versus improving: separate the memory layer from the change process

All six papers draw some version of this line. MemoHarness separates per-case entries from distilled
patterns. Prime separates facts (memories) from rules, skills and roles. Raven separates the memory track
from harness evolution and skill evolution. RRSI and Raven make policy change a gated, evaluated decision.
The failure mode is the same in each: experience that silently becomes policy. Prime's exploit-saved-as-skill
and RRSI's grader-fitted prose are the two examples. QMX should run three tiers with different rules.

| Tier | What | Written by | Approval | Where (Deep Agents / LangGraph) |
|---|---|---|---|---|
| 1. Record | Raw history, tool outputs, run ledger, diagnoses | Automatic | None (append-only) | `/conversation_history/summary_N.md`; Store `("qmx","runs")`, `("qmx","harness","diagnoses")` |
| 2. Memory | User facts, preferences, decisions, time-bound facts | Copilot via memory tool, or `after_agent` extraction | Operator-visible and editable in the UI; low-risk writes allowed automatically | Built-in Store (default `SqliteStore`) or the one external provider; `valid_until` field |
| 3. Policy | Prompt notes and AGENTS.md, skills, tool descriptions, sub-agent specs, middleware config | **Proposal only** | Operator approves in the UI, after an eval run with the RRSI rules | git-versioned `/skills/`, `/memories/AGENTS.md`, `HarnessProfile`; Store `("qmx","harness","proposals")` |

How tier-3 proposals work:
- **Proposer.** A scheduled offline "harness steward" job, not the live Copilot, reads tier-1 diagnoses (MemoHarness dimensions) and drafts proposals. Each draft states a hypothesis, at most 1-2 edits, an activation predicate (Raven) and the expected effect (Prime).
- **Screen.** A leakage and specificity check on the diff (RRSI): no hard-coded symbols, dates or one-off values.
- **Evaluate.** Run on the eval suite at k ≥ 2. Accept if ΔS > δ and the cost rule holds. Correctness comes first and tokens break ties (MemoHarness).
- **Apply.** Only at the next thread start, versioned, with one-click rollback (Prime). Do it in a branch or worktree, in line with the operator's doc-pass rule.
- **Hard rule.** Anything touching orders, sizing, node control or external writes is tier 3 *and* needs explicit operator approval, even when the eval is green. Risk and sizing authority stays with GitBook and the node docs, never with learned memory.

The change process must work over the **run ledger**, not over the memory provider. Then swapping or adding
the Hermes-style external provider never changes how policy changes. The provider only serves tier 2.

### (b) Context management beyond plain summarization

1. **Keep the 0.85 auto-summarization as the backstop.** ACM Fig 4 shows frontier models rarely compact on their own.
2. **Make compaction lossless and addressable** (ACM §3, Prime §2.2). Archive the raw slice per summary ID, then add `recall_archived(summary_id, query)` running on a cheap sub-model. Untrained ACM already beat ReSum and ACON on all three benchmarks (Table 2).
3. **Use a structured summary schema** (ACM B.3): knowledge state, decisions and approvals, dead ends, open questions, concrete next step, identifiers and numbers verbatim, with a hard token cap.
4. **Compact at task boundaries**, prompted by a stated context budget. This keeps the cache-friendly append-only pattern between boundaries.
5. **Pass references, not artifacts** (Raven §3.3). Sub-agent outputs and large tool results go to files. The main context gets the path plus a short summary, and terminal outputs are read in full only when needed. This extends the existing >20k eviction.
6. **Use code over data for big structured results** (Prime L2). This is the blueprint's RLM policy: compute in a sandbox and return only results.
7. **Keep retrieved memory narrow** (Harness-the-Memory §5.2). More retrieved text pulls attention away from the current task.
8. **Do not add `ContextEditingMiddleware(ClearToolUsesEdit)` mid-thread** without measuring cache impact. Clearing old tool outputs changes the prefix and breaks prompt caching. If it is used, fire it in the same step as summarization.

### (c) Memory substrate: is `SqliteStore` a sensible default?

Yes, for a single-operator local product, with three additions.

**Why it fits:**
- It is local, transactional, cheap, inspectable and needs no auxiliary LLM per write.
- Harness-the-Memory found flat lexical and dense indices competitive on agentic coding and far cheaper than graph memory (BigCodeBench-Hard: BM25 19.6% versus graph 16.2% at about 1/6 the latency).
- Heavy production memory costs 2,700-9,000 auxiliary calls per benchmark run.
- Raven's EverOS uses the same shape: SQLite for state, Markdown records, a derived index.

**Additions:**
1. **Search capability.** Without an `IndexConfig` (dims, embed, fields), a LangGraph store does namespace and filter lookup only, not ranked search.
   - Add an embedding index. Verify sqlite-vec support in the installed `langgraph-checkpoint-sqlite` before relying on it.
   - Add a BM25 path, for example an SQLite FTS5 side table over the same records. BM25 was the cheap, strong baseline in every regime (Table 1, Table 2).
   - Fuse the two with RRF, as EverOS does (Eq 62).
2. **Write depth over read breadth** (Harness-the-Memory §1, §5.3). Store distilled records rather than transcript chunks: facts, decisions, strategies, skill candidates. Give each one `valid_from`/`valid_until`, `source_run_id`, `confidence` and `owner`. Refinement-type memories scaled best from 6K to 262K tokens (Fig 6).
3. **Human-readable source of truth** (Raven §5.5). Export the records to Markdown under `/memories/` so the operator can see and edit them in the UI, in line with the "configurable = UI-editable" rule. The index stays rebuildable.

**Routing.** Use a simple deterministic rule rather than a learned router. Recall-type questions get k up to
about 8, while action turns get k of 1-3 with the most specific distilled record first. The paper calls
routing "necessary". A learned router is still research.

**External provider.** Offer one external provider (Mem0, Zep, Honcho-style) only as an opt-in for users who
want cross-device or richer profiles. Log its auxiliary-call count. Never make it the store for tier-3 policy.

### (d) Response handling: validating outputs, tool responses, retries

Layer these. All of them exist in LangChain v1 middleware or are small custom pieces.
- **Transient tool errors.** Put `ToolRetryMiddleware` on idempotent *read* tools only, with `retry_on=(ConnectionError, TimeoutError)` and backoff, and on the inside of the middleware list.
  - Never auto-retry money, node or external-write tools. Give those idempotency keys and surface the failure.
- **Actionable tool errors.** `ToolErrorMiddleware` (already in the blueprint) turns exceptions into "what failed, how to fix" messages. Raven's admission errors name the offending field and the repair.
- **Model errors.** Use `ModelRetryMiddleware`, plus fallback only if CLIProxyAPI does not already fail over. Avoid stacking two fallback layers, which hides outages and breaks session affinity.
- **Structured outputs.** Use `response_format` with `ToolStrategy(schema, handle_errors=...)` for designated deliverables such as strategy reviews or backtest summaries. Validation failures are re-prompted, not shipped. This is MemoHarness's D6, which their search treats as a lever in its own right.
- **Completion adjudication for sub-agents** (Raven §3.2).
  - A cheap structured judge marks the result accomplished or not and gives a category.
  - Unaccomplished results go back to the sub-agent with the missing condition, or to the operator. They are never silently used.
  - A judge failure should *not* default to accomplished in money-adjacent flows, unlike Raven's fallback.
- **Deterministic pre-finalize probes** (RRSI Table 9; Raven-Research's research trail). Before the final message:
  - check that every number the Copilot quotes appears in a tool output from this run;
  - check that cited job IDs and files exist;
  - flag claims whose source page or file was never opened.
  These probes transferred out of distribution; extra instruction prose did not.
- **Untrusted fencing.** Recalled memory, web content and sub-agent output are fenced as data (Raven Eq 65). They can never authorize an action. Approvals come only from the operator through HITL interrupts.
- **Separate harness failures from model failures in logs** (Prime §2.6). Timeouts, dropped state, cap hits and judge failures get their own codes in the run ledger, so tier-3 diagnoses blame the right dimension.
- **Stop rules.** End-condition tests and hard caps (Prime's autonomous mode) are already in the blueprint as model-call and tool-call limits. Keep "two failed attempts, then stop with one named blocker".

### (e) What NOT to adopt yet

- **Per-request harness rewriting** (MemoHarness §2.6). It breaks prompt caching and auditability, and its benefit was not ablated (App A).
- **Automated harness evolution loops** (RRSI, HarnessBank, Meta-Harness, TTHE).
  - They need a verifier-backed eval suite of dozens of real Copilot tasks, a measured noise band and about 20 rounds × the suite × k trials per run.
  - Adopt RRSI's *rules* manually now. Automate only once the eval suite exists and is stable.
- **Post-training for context management** (ACM §4). QMX does not train models. Use the prompt-only variant.
- **Multi-agent DAG hosts over third-party agents, group-memory verdicts and device networks** (Raven §3, §3.4, §9). The verdict layer is unevaluated by the authors. The Copilot's sub-agent count is small.
- **Swarms and daemon agent-to-agent messaging** (Prime §2.4, Factorio's 633 sub-agents). Async sub-agents with task IDs (blueprint) are enough.
- **Graph memory (LightRAG, Zep), LoRA or parametric memory, KV-cache memory.**
  - Graph memory is Pareto-dominated on agentic tasks and costly at long horizons.
  - LoRA memory scored badly in every regime it was tested (Harness-the-Memory Table 1, Table 2).
- **Large skill catalogs, and auto-creating or updating skills from experience without approval.** Raven's gains depended on *coverage and curation*, not volume: the raw crawl did worse (§7.7). Prime's exploit-skill shows the risk.
- **Learned substrate routers.** A two-rule heuristic (recall versus action turn) captures the main finding.
- **Taking headline numbers at face value.**
  - ARC-AGI-3 95.5% and MAOB are scored against external or self-built references.
  - MemoHarness rests on an 18-task split.
  - Harness-the-Memory used 8-32B models.
  Treat all of them as direction, not magnitude.

---

## 8. Next steps, smallest first

1. Dimension-tagged `diagnosis` records and a run ledger with harness-failure codes, written in `after_agent`.
2. Addressable summary archives, `recall_archived`, the ACM summary schema and a context-budget line in the prompt.
3. A structured completion judge for sub-agent results, plus pre-finalize probes.
4. A richer `SqliteStore` schema (validity, provenance, confidence), FTS5 and/or embedding search with RRF, k of 1-3 on action turns, and a Markdown export.
5. The three-tier rule and RRSI's acceptance rules in the governance doc. Build the eval suite before any automation.
6. Retries on read tools only; idempotency keys on writes; one fallback layer.
