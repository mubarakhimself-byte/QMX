# Ten skills and tool-use papers, read for the QMX Copilot

Read 2026-10-09. All ten arXiv IDs resolved and the titles match the request. I read the full HTML text of each
paper (body and appendices, without the reference lists). Copies are in `scratchpad/papers/<id>.txt`. All ten are
2026 preprints, none is peer reviewed, and every number below is the authors' own. Paper 8 is a guidance note
with no experiments.

This file does not repeat `harness-practices.md` (no modes, HITL as permissions, 10-15 tools plus provider tool
search, caching, compaction, stop rules, RLM policy) or `papers-harness-memory.md` (three tiers: record, memory,
policy; RRSI acceptance rules; completion judges; pre-finalize probes; untrusted fencing; Raven skill admission).
It builds on both.

Deep Agents facts checked for this file (docs.langchain.com/oss/python/deepagents/skills): SKILL.md frontmatter has
`name` (1-64 chars, lowercase plus hyphens, must match the folder name), `description` (at most 1,024 chars),
`license`, `compatibility`, `metadata` and an experimental `allowed-tools`. Custom sub-agents take their own
`skills=[...]`, and skill state is isolated between the main agent and its sub-agents. There is **no**
`disable-model-invocation` field, so an "explicit-only" skill state has to be built by QMX itself (see synthesis a).

---

## 1. Prompt2Skill: unsupervised skill optimization from natural-language instructions (2609.38593, Vanderbilt / USC / Adobe)

**Problem.** Skill optimizers such as SkillOpt and Trace2Skill need a labelled, in-distribution training set. A real
user has only a sentence ("read a passage and answer questions about it") and perhaps a few examples (§1, §2).

**Method in plain words.**
- A **Data Agent** turns the sentence into a task spec (input/output contract, answer style, proxy metric) and a short seed skill. It then finds or builds practice data: Hugging Face datasets and Wikipedia, adapted to the format, or generated when nothing fits (§3.1-3.2).
- Items are screened before use. A source is dropped if the seed-equipped model fails every probe item (Eq 7). A generated item is kept only if the seeded or the direct model solves it (Eq 8).
- A **Skill Agent** runs the target model, collects failures, and asks a reflector (GPT-5.5) for candidate edits (§3.3).
- **Paired acceptance**: candidate and incumbent run on the *same fresh batch*. Count w = items only the candidate solves and l = items only the incumbent solves. Accept if w > l and z = (|w-l|-1)/sqrt(w+l) ≥ 1 (Eq 14).
- Every accepted version is kept. A **frozen selection set**, used exactly once, picks the export, so a late edit that generalises worse cannot win. Theorem 1 (App A) bounds the loss from this selection.
- Defaults: 400 proxy items, 150 reserved for selection, 120-item acceptance batches (App E.2).

**Key results.**
- Average relative gain over direct prompting (Table 1): Qwen3-8B +29.1%, Qwen3-32B +26.1%, Llama-3.2-1B +93.5%, Claude Haiku 4.5 +22.0%, GPT-5.5 +24.3%.
- Pooled over 19 model-benchmark pairs: +36.1% over direct and +83.0% over off-the-shelf skills. These are averages of *relative* changes, not percentage points (App E.4).
- **Off-the-shelf skills often hurt** (Table 1): Qwen3-32B −9.7%, Haiku −6.2%, Llama −30.4%. The Llama SQuAD score fell from 0.207 to 0.048.
- With matched budgets against SkillOpt (same proxy data, 7,400 solver evaluations; Table 2): SearchQA EM 48.71 vs 45.79, SQuAD EM 82.50 vs 81.30.
- **Caveats.**
  - The "never significantly regresses" claim sits beside per-cell drops: Haiku SearchQA 0.839 vs 0.857 direct, Haiku spreadsheet 0.269 vs 0.297, Qwen3-8B AIME 0.175 vs 0.208.
  - κ=1 is a screening threshold, not a 5% significance test, and nothing corrects for multiple comparisons (App D).
  - The ablations are single runs (Fig 3).
  - The tasks are QA and maths, not agentic workflows.

**Practical for a single operator?** The *acceptance discipline* is practical: a paired comparison on the same
items, fresh items for each decision, a frozen selection set, and keeping every accepted version. The full loop is
research-grade. It needs hundreds of proxy items per skill and a public dataset to mine, and QMX trading tasks
have no Hugging Face proxy.

**QMX should…**
- Use paired win/loss on the same eval items (the w, l, z rule) when comparing a skill against no skill, or v1 against v2. This complements RRSI's noise-band rule: z works at small n, while δ needs repeated runs.
- Keep every accepted skill version under git in `/skills/<name>/` and pick the release on a held-out set that is never used for editing. Never ship "the last edit" by default.
- Make the proxy data for QMX-owned skills from the operator's own past runs (backtests, job logs, approved answers), never from public datasets. Run this offline as a scheduled job, not inside the chat.

---

## 2. SkillGate: training in-policy skill selection in long-horizon agents (2608.18852, SJTU / Xiaohongshu)

**Problem.** Agents choose a skill from its name and one-line description, mid-episode, before they can read it.
Outcome-only RL cannot teach that choice (§1).

**Method in plain words.**
- The authors name the cause **selector credit starvation**. The tokens that name the chosen skill are a median 0.14% of the loss. About two in five correct reads get a negative signal, because execution failed afterwards. Yet a correct read is worth +11.2 pp of success (Fig 1, §4.6).
- SkillGate splits the credit. The task reward goes only to execution tokens. A separate reward goes only to the skill-name tokens, and it is positive only when the trajectory made exactly one read and that read was the right skill (Eq 1-3).
- Test setting: a 16-candidate slate of 1 correct skill, 5 misleading near-misses, and 5 relevant plus 5 irrelevant community skills (§4.1).

**Key results** (Table 1, 385 trials).
- A 9B policy rose from 40.8% to **53.2%** trial success, against 47.0% for outcome-only RL on an identical budget. Correct-skill reads went 54.3 → 83.9% and misleading reads 69.6 → 21.8%.
- **No frontier model read the correct skill in even half the trials**: DeepSeek-V4-Flash 40.8%, Kimi-K2.6 45.7%, GLM-5 39.0%.
- External selection (Table 3):
  - A "read only one skill" prompt changed nothing (35.0 vs 37.1).
  - A more accurate 27B router (68.6% top-1) produced *lower* downstream success than a 9B router (36.8 vs 40.7). Routing accuracy, whether the executor reads what it is handed, and execution quality are three separate quantities.
  - A reranker scoring candidates one at a time was worst (31.8), because a slate of near-duplicates defeats independent scoring.
- Cost (Fig 4b): on-demand reading loads about as many body tokens as preloading *one* skill. Preloading k skills grows linearly, to 16x at k=16. This is direct evidence for progressive disclosure.
- **Caveats.** Single training run per configuration. The trial-level gain is +7.9 pp, CI [2.1, 14.3]; pass@4 is not significant (App E). The method needs tasks with a known-correct skill and cannot reward correct abstention (§6).

**Practical for a single operator?** The training is research-only, since QMX does not train models. The
*measurements* transfer directly: frontier models misselect when near-miss skills sit side by side, and neither
prompting nor a separate router fixes that.

**QMX should…**
- Treat **skill selection as something to test and measure**. Every skill's eval set includes near-miss prompts that should *not* trigger it, and each eval run reports correct-read, misleading-read and reads-per-task.
- Fix misselection at the catalog, not in the prompt. Merge or rename near-duplicate skills and make descriptions discriminative. Do not add "read only one skill" instructions.
- Not build a separate skill-router model. Let Opus read the slate inside the loop, which is what Deep Agents `SkillsMiddleware` already does.

---

## 3. SkillAligner: retrieved skills as adaptable drafts at execution time (2608.06880, Zhejiang University)

**Problem.** A relevant skill can still break a task that the model solves on its own. The authors call this
**skill-execution misfit** (§1-2).

**Method in plain words.** One structured LLM call before execution takes three inputs: the task, the top-k
retrieved skills, and an *execution spec* (available tools, action formats, permissions). It runs three steps (§3):
- **Task grounding**: extract a task contract (goal, hard constraints, preferences, underspecified conditions). Split each skill into fragments and tag each fragment core, task-bound, weak (compressed) or dropped.
- **Environment alignment**: check each fragment against the real tools. Repair it if a semantics-preserving fix exists. Mark each skill Direct, Guarded (kept as a runtime check) or Abstain.
- **Composition**: resolve the order skills must run in, and any conflicts or overlaps between them. Output a compact guide with four fields, **Primary / Checks / Avoid / Fallback**. That guide *replaces* the raw skills for the whole run.

**Key results.**
- Raw top-5 injection causes regressions on **5.8-17.9%** of instances that the model solved without skills. Gemini 2.5 Pro was no more robust (11.42% pooled; Table 1).
- Causes of those regressions (GPT-5.5 judge, Table 2): **task misfit 38.6%**, clash between skills 28.6%, environment misfit 26.7%.
- Average score: 58.17 against 47.07 for raw top-k, 40.94 for no skill and 54.25 for the strongest baseline, SkillPyramid (Table 3).
- Qwen3-8B regressions fell from 17.91/9.40/10.29 to 2.24/2.80/3.57 (Table 4).
- Cost: adaptation adds 8.3% tokens, cuts execution tokens by 46.6%, and saves 38.3% net (Table 5).
- A guide built *without* skills scores 45.99, so the retrieved content is what matters (+12.18).
- Case study (App D): a generic "shorten the query" rule dropped a product type the task required, and the agent bought the wrong item.
- **Caveats.** ALFWorld, WebShop and QA only. Backbones up to Gemini 2.5 Pro. No confidence intervals. The guide is fixed once and cannot adapt to mid-run surprises (§6).

**Practical for a single operator?** Yes, in a light form. It is one call, it pays for itself in tokens, and its
output format is reusable.

**QMX should…**
- Make Opus restate the **task contract** (the hard constraints, such as symbol, budget, risk limits, deadline) before following any skill body. Write it into the existing precedence rule: task constraints > skill steps. This targets the largest failure class at zero cost.
- For **user-created and imported skills** (not QMX's own curated ones), add an `adapt_skill` step. When the skill is first activated in a task, write `/work/<thread>/skill_plan.md` with Primary / Checks / Avoid / Fallback, checked against the tools in this thread. Use a cheap Sol call and write the result to a file, so the cached prefix stays untouched.
- When a skill names a tool QMX lacks, mark that skill Guarded or Abstain, never "improvise".

---

## 4. SkillCoach: self-evolving rubrics for evaluating skill use (2607.01874, HKUST-GZ / JD)

**Problem.** Passing the verifier does not show that a skill was used well. Agents pass by trial and error,
pick distractor skills, skip steps or skip final checks (§1).

**Method in plain words.**
- Skill use is scored on four dimensions, kept separate from the verifier (§3.3, App B; default weights in brackets):
  - **selection**: F1 against the gold skills, plus credit for correctly abstaining (0.40);
  - **following**: weighted key steps, counted only if there is *visible evidence*, never a claim (0.30);
  - **composition**: order and hand-off of artifacts between skills (0.20);
  - **reflection**: explicit checks before finishing (0.10).
- A rubric is first generated from the gold skill, an oracle solution and sample rollouts. The key-step schema (App D) has `step_id`, `critical`, `positive_evidence`, `negative_evidence`, `required_before` and `expected_artifact`.
- The rubric then evolves through local patches. A patch is accepted only if it passes a hard gate (no credit without evidence, distractors not ignored) and improves a soft score on held-out rollouts. Limits: 6 rounds, 10 calibration rollouts, 5 validation rollouts (§3.4, App D).

**Key results.**
- Rubric quality against human gold (Table 2): key-point coverage 71.6 → 83.7, usability 81.5 → 94.3, filtering agreement 82 → 96.
- Skill dependence (Table 3): Opus 4.7 scored 18 with no skills, 88 with gold skills and 80 with distractors added. GPT-5.5 went 24 → 80 → 76. Distractors cut Gemini 3.1 Pro's selection score from 98 to 78.
- **Distractor boundary** (§4.4, Fig 4), the most useful number for QMX: selection F1 first drops by ≥0.10 at about 26 distractors (DeepSeek-V4-Flash), 45 (Gemini 3.1 Pro), **55 (GPT-5.5)** and **195 (Opus 4.7)**.
  - At 50 distractors, near-duplicate skills hurt most. GPT-5.5 falls from F1 0.84 with random distractors to 0.59 with highly similar ones, and Opus 4.7 from 0.87 to 0.71.
  - Most models abstain well when no skill applies.
- Training data (Table 4): rubric-filtered SFT beats outcome-only SFT (9B: 32 vs 18). Dropping the key-step criterion hurts most (to 16).
- **Caveats.** 50 test instances. The human-gold audit is judge-assisted. SFT only, no RL. The boundary study isolates selection behind a browse-and-read interface rather than running full tasks.

**Practical for a single operator?** The rubric schema and the evidence rule are practical now. The rubric
evolution loop needs rollouts and suits an offline eval job. The SFT part is research-only.

**QMX should…**
- Store a `evals/rubric.json` in every skill folder, using SkillCoach's key-step schema with evidence fields. Score each trace on selection, following, composition and reflection in LangSmith, *separately* from "did the job succeed".
- Count a step only when the trace shows it: a tool call, a file, an artifact. This is the same rule as the existing pre-finalize probes.
- Size skill catalogs by the sub-agent model. Opus held up to about 195 distractors, but GPT-family models degraded near 55. Keep each Sol sub-agent's skill list short and specific (Deep Agents per-sub-agent `skills=`), and remove near-duplicates everywhere.

---

## 5. RASO: retrieval-augmented skill optimization via cross-harness adaptation (2609.38024, Korea University / KAIST / Meta)

**Problem.** Millions of public skills exist, yet optimizers rebuild each skill from scratch with expensive
rollouts. Reusing a public skill as-is fails, because it was written for another tool set (§1).

**Method in plain words.**
- Split a corpus (GitSkills) into heading-level *sections* and search them with BM25, top K=5 (§4.1).
- **Cross-harness adaptation** rewrites each retrieved section into a short "lesson" under three rules:
  1. remove source-domain nouns and drop steps that have no counterpart in the target tools;
  2. address only the stated requirement;
  3. keep a claim about a tool's behaviour only if the target harness description confirms it.
- **RASI** builds the first skill from the task and harness descriptions plus these lessons, with *no rollouts*.
- **RASU** runs the skill, turns failures into retrieval queries, adapts the results, and accepts an edit only if validation improves (§4.2-4.3).

**Key results** (Table 1, three seeds).
- With no rollouts, on GPT-5.6-Luna, RASI beat LLM-only initialization: OfficeQA 45.74 vs 40.11, spreadsheets 49.17 vs 44.40.
- **Reusing a retrieved skill directly** (SkillRouter) scored below no skill on ALFWorld (55.97 vs 64.43).
- On SpreadsheetBench, 92.9% of retrieved skills came from a different harness (Fig 1).
- Full RASO against the best baseline: spreadsheets 63.33 vs 57.02 (SkillOpt). On Qwen-3.5-9B WebShop, 24.73 vs 13.43.
- Dropping the adaptation step costs a lot (Table 3): RASI on spreadsheets falls from 49.17 to 41.43.
- K=10 retrieved sections was slightly worse than K=5 (Fig 3). Retrieving from just 1% of the corpus already helps (Fig 4).
- Optimization cost was lowest or near-lowest at matched rollouts: WebShop $10.28 vs $41.03 for TextGrad (Table 9).
- **Caveats.**
  - Validation sets are small (24 tasks for OfficeQA, 18 for ALFWorld).
  - The task and harness descriptions were written by a Codex agent from the harness code.
  - Repository-level blocklists were needed to keep benchmark-specific skills out of the corpus.

**Practical for a single operator?** The adaptation rules are practical immediately, for any external skill QMX
imports. A million-skill public corpus is not, because of supply-chain risk and noise.

**QMX should…**
- Run RASO's three rules whenever the Copilot imports an outside skill (a Claude Code, Codex or community SKILL.md) or drafts from one. Remove foreign tool names, drop steps without a QMX tool, and keep tool claims only if QMX's own tool docs confirm them.
- Write and keep a **harness description** for QMX: the tool list with semantics, file layout, budgets and approval rules. Give it to every skill-creation and skill-adaptation call. RASO and SkillAligner both depend on it.
- If retrieval is used, retrieve *sections*, not whole skills, from a curated QMX corpus (QMX docs, the operator's approved skills), with BM25 and K≈5.

---

## 6. SkillAlchemy: open-world agent skill creation (2608.23417)

**Problem.** A short brief leaves out the requirements that matter. Web sources mix reusable practice with
details that apply only locally. Copying either into a skill produces brittle instructions (§1, Fig 2).

**Method in plain words** (§3). The method has three stages.
1. **Implicit requirement discovery.** Turn the specific values in the brief into parameters (a 7-day family trip becomes duration, traveller type and destination). Build contrastive probes that vary one factor at a time:
   - substitution (swap a subject, method or tool within the same family);
   - boundary (add an omitted precondition, failure or constraint);
   - neighbour (compare with a sibling capability).
   Then ask whether the change alters any of four components: conditions, action, recovery or verification.
2. **Evidence-grounded admission.** Group findings by the decision they inform. A candidate procedure is admitted as a **General** instruction only if it is supported, consistent and shown to apply beyond one source. It becomes a **Scoped** example if it is supported and consistent but local. Otherwise it is **Excluded**, and it stays in the audit record (Eq 5).
3. **Compilation** into SKILL.md with references, scripts and assets, guided by a "skill grammar" mined from first-party skills. The grammar covers activation metadata, workflow form, executable procedures (condition, action, observable output, failure route), applicability limits, verification form, output contract and progressive disclosure (App C, Table A.2).

**Key results** (87 SkillsBench v1.1 tasks, four agent/model configurations, avg@5).
- Pilot study: the official Anthropic and OpenAI skill creators **without web access scored 1.4 pp below no skill**. Web access added 6.9 pp, but they stayed about 14 pp behind human-written skills (§1).
- Pooled pass rates (Table 2): no skill 35.9, Anthropic creator 40.6, OpenAI creator 42.2, OpenSkill 46.0, MUSE 47.2, human-curated 54.4, **SkillAlchemy 55.8 [53.5, 58.1]**.
- It beat human skills on Codex+GPT-5.5 (63.7 vs 60.9) and Claude Code+Opus 4.8 (60.9 vs 59.5), but not on Codex+DeepSeek (43.9 vs 45.7).
- Each ablated component costs 5.0-15.7 pp (Fig 5).
- **Robustness** (Table 4): the baseline creators promoted 9 of 16 *conflicting* payloads into runtime instructions, and their pass count fell from 58/80 to 35/80. SkillAlchemy promoted **0 of 12** injected payloads and kept 17-18 of 20 passes.
- Cost (Table 3): 23 minutes of creation per task, against about 7 for the official creators.
- Median top-level SKILL.md length was 144-157 lines (App B).
- **Caveats.** Skills were created per task, not as general capabilities. The perturbation test covers only 4 tasks. No author affiliations are shown. The Media domain lagged human skills.

**Practical for a single operator?** Yes. This is the best template in the set for **user-created skills through
the Copilot**. It needs no training and runs as one agentic workflow with research sub-agents, and its
admission step doubles as an injection filter.

**QMX should…**
- Ship a QMX-owned `skill-creator` skill that follows SkillAlchemy-lite:
  1. turn the brief into parameters;
  2. ask about 5-8 boundary questions (market closed, data missing, broker rejects, partial fills, stale prices, the user lacks a connector);
  3. collect evidence from QMX docs, the user's run history and allowed web pages;
  4. tag every instruction General, Scoped or Exclude, with its provenance, in `skills/<name>/provenance.json`;
  5. render with the grammar.
- Make every verification step check the **final delivered artifact** (the saved workflow, the mini-app build, the backtest report file), not an intermediate state. App D.2 shows that only artifact-level checks passed (5/5 vs 0/5).
- Treat web text as evidence, never as instruction. Conflicting sources produce a recorded conflict, not an instruction.

---

## 7. ExpG: robust tool use via experience-driven adaptive guidance (2608.03403, Alibaba Token Hub / Shandong)

**Problem.** Tools behave differently by context and drift over time, and their failure signals are coarse
("error", or "success" with a wrong value). Agents fall back on trial and error (§1, Fig 1).

**Method in plain words.**
- **Acquire.** For each tool call in past trajectories, an LLM judge answers 10 yes/no questions in three groups (§3.2):
  - *use*: right tool, right time;
  - *input*: syntactically and semantically correct;
  - *response*: the tool ran stably and returned what was expected.
  It also writes a short explanation. Records are indexed by tool, and identical score vectors form an "invocation pattern" class.
- **Distil.** Remove duplicates and stale records, and drop records that preceded three consecutive worse scores. Skip tools with only one record. For tools with many records, sample across classes in proportion to their size (Algorithm 1). Then summarise per tool: core function, success patterns, common issues, best practices, plus success rate, latency and token stats (§3.3).
- **Reuse.** *Dynamic* guidance is appended to the tool description as "optional guidance". *Stable* guidance (a single dominant failure class, at least Q/2 records) goes into the schema as "you must follow" (§3.4, Eq 2, App E.3).

**Key results** (Table 1, Avg@3 totals).
- GPT-5 nano 70.62 → 79.22, DeepSeek-V3 78.66 → 82.61, Qwen3-8B 74.41 → 81.82, Qwen3-235B 78.49 → 84.98.
- It beat few-shot examples, DRAFT doc-rewriting and Mem0 procedural memory.
- The biggest gains came where tools are similar (+16.3 on MetaTool's "similar tools") and in faulty settings (+13.1 single-turn and +10.3 multi-turn on BFCL with missing parameters or tools, §4.2).
- Steps fell in normal multi-turn tasks (10.14 → 9.02) and rose by 2.4 in faulty ones, which is the deliberate behaviour wanted there.
- About 9 records per tool is the sweet spot (Table 2).
- A weak model can act as its own judge: Qwen3-8B judging itself still gained +4.9 on MetaTool (Table 4).
- Ablation (Table 6): passing raw trajectories instead of distilled records costs −7.4. "Stable-only" guidance costs −3.9.
- Putting guidance in the system prompt rather than in the tool description was slightly worse (App E.4).
- 98.7% of the guidance was judged reliable by humans. Online cost: $0.0018 and about 2.5 s per call, with "generate once, reuse many" recommended (App G).
- **Failure modes (App F.2)**: unseen tools, misread intent, **incorrect attribution** (a schema/behaviour mismatch in the tool was blamed on the agent) and **over-reaction** (a rule that held by coincidence: "always prefix Dr.").
- **Caveats.** Mostly small or older models. MetaTool tasks do not execute tools. Tasks ran sequentially to support time filtering. Gains are likely smaller on Opus 5.5.

**Practical for a single operator?** Yes, run as an **offline batch** over QMX's own tool logs. The per-call
online judge is not worth it.

**QMX should…**
- Log every tool call in a `wrap_tool_call` middleware: tool, args hash, outcome, error class, latency.
- Run a weekly offline job that scores calls on ExpG's three groups, groups them, and drafts per-tool guidance. Treat the drafts as **tier-3 policy proposals** (prior synthesis): they ship in the next version of the tool description, never mid-thread, because tool definitions sit at the top of the cache prefix.
- Guard against the two failure modes. Require evidence from more than one context before writing a rule (SkillAlchemy's "reusable" test), so coincidences do not become rules. Route repeated "agent misuse" on one tool to a *tool fix* (schema, error text) before writing guidance about it.
- Use "must" wording only for stable failure patterns. Everything else stays as "use when…" guidance (this matches the Anthropic over-triggering note in `harness-practices.md` §2).

---

## 8. Authoring Agent Skills: a software-engineering approach (2607.25032, UCL)

**Problem.** A skill is chosen probabilistically, and no compiler checks that the right one fired. Authors also put
guarantees in the wrong mechanism (§1-2).

**Content** (guidance distilled from Anthropic docs and the open spec; no experiments).
- **A skill is software.** It should have one responsibility, a separate interface (the description) and implementation (the body), low coupling to other skills, and an economical share of the token budget. Testing becomes *behavioural evaluation*: a pass rate over several runs, scored by a rubric or judge. Bundled scripts get ordinary unit tests (§2).
- **Staged loading** (§4): metadata costs about 100 tokens per skill, the body should stay under about 500 lines, and bundled files cost nothing until read. Scripts are *executed*, so their source stays out of context.
- **Description** (§5): third person, saying what the skill does and when to use it, with the concrete words a matching task would contain. Name ≤64 chars, lowercase and hyphens. Description ≤1,024 chars.
- **Body rules** (§6): add only what the model does not already know. Link reference files one level deep only, with a table of contents for files over 100 lines. One term per concept. Forward slashes in paths. Constrain the procedure tightly only where it is fragile.
- **The mechanism table** (Table 1) sorts mechanisms by who decides that they run and what they guarantee: memory file (always loaded, advisory), skill (model-chosen, advisory), command (user-chosen), sub-agent (isolated context), MCP (external action), **hook (runtime-run, deterministic, can block)**. **Rule: judgement goes in a skill; anything that must happen every time goes in a hook** (§8).
- **Process** (§9): write evals first, measure the no-skill baseline, write the minimum instructions that pass, then test with a *fresh* instance. Watch the read order: a file the model ignores is unnecessary, and a file it keeps rereading belongs in the body.
- **Patterns and faults** (§10): checklists; validate-fix-repeat loops; for batch or destructive work, write a plan file, validate it with a script, then apply. Faults: offering many alternatives with no default, nested references, assumed packages, scripts that do not handle their own errors, unexplained constants.
- **Trust** (§11): treat third-party skills as dependencies. Read everything, including scripts and external URLs.

**Practical for a single operator?** Fully. It is a style guide.

**QMX should…**
- Turn §3-6 into a deterministic `skill_lint` that runs on every created or edited skill: frontmatter limits, body ≤500 lines, references one level deep, TOC on long references, no backslash paths, declared dependencies, third-person description containing both "what" and "when".
- Apply the hook rule strictly. Interrupts on money and node tools, deny-lists and audit logging live in middleware and HITL, never in skill prose. A skill can never remove an interrupt.
- Put destructive or batch workflows (bulk order edits, mass alert changes) through "plan file → script validation → HITL → apply".

---

## 9. Harness Engineering: a source-code study of eleven coding agents (2609.00006, Inclusive Brains / Wavestone AI Lab)

**Problem.** "Harness engineering" had no grounded reference for what production harnesses actually contain (§1).

**Method.** Source-code anatomy of 11 systems pinned to July-2026 releases, with April snapshots kept for a
90-day diff. Seven subsystems: loop, LLM integration, tools, memory and context, safety, orchestration,
extensibility (Table 1). The study is descriptive and runs no benchmarks. Claude Code is read from a circulated
March-2026 snapshot, which the authors call the weakest link (§15.6).

**Key findings** (13 observations, 29 patterns in Tables 11-12, 18 recommendations).
- **Loop size does not predict benchmark results.** Mini-SWE-Agent's roughly 100-line loop reports results in the frontier range. Production code mass goes to safety, UX, extensibility and clients (Obs 1).
- **No runtime imports an agent framework.** That includes LangChain/LangGraph, and Gemini CLI uses neither of Google's own. None uses embedding RAG over code (Obs 9, Rec 15-16). The authors resolve this through the **harness-framework merger**: Deep Agents is cited as the framework that "independently converges" on the corpus's conventions (SKILL.md progressive disclosure, AGENTS.md, sub-agents, todos; §14.2, Table 15).
- **Skills lead MCP** (9/11 vs 8/11).
  - 8 of 9 adopters load skills lazily.
  - Skills can be gated by conditions: Claude Code `paths`, OpenHands PathTrigger, OpenClaw `requires` (binaries, env, OS).
  - A supply chain has appeared: registries in four systems; Hermes trust tiers with scan and quarantine; an OpenClaw approval workflow.
  - **Agent-authored skills** exist: Hermes `skill_manage`, and Gemini CLI's extraction sub-agent, which writes patches into a **user-reviewed inbox** (§12.5, Obs 8).
- **Hooks are the extension substrate in 9/11.** Codex copied Claude Code's hook names verbatim (§14.1-14.5).
- **Memory write paths** have four governance models: agent-maintained (Codex), human-gated inbox (Gemini CLI), bounded snapshot files (Hermes: 2,200- and 1,375-char files, frozen per session for the cache), and pre-turn recall (OpenClaw). None uses embeddings as the main memory store; Hermes uses SQLite FTS5 (Obs 5).
- **Seven of 11 systems compact at a threshold.** The best compact incrementally (merging the previous summary) and also compact reactively on overflow (Rec 7).
- **Plan modes spread** to all four provider-native systems in one quarter, but as permission or approval levels (§10.2, §14.5).
- **Policy is moving out of prompts into configuration** (Obs 3).

**Comparison table** (§6-12, Tables 4, 5, 8, 9, 10). Codes: CC = Claude Code; Vibe = Mistral Vibe; OH = OpenHands;
OC = OpenCode; OClaw = OpenClaw.

| System | Agent loop | Context / compaction | Tools (count, design) | Permissions / safety | Extension points | Sub-agents | Modes |
|---|---|---|---|---|---|---|---|
| CC | Streaming ReAct; concurrency-safe batches (default unsafe); no stuck detection | Compact 13K below window; restore 5 files; skills capped 25K | 43 typed; **deferred + ToolSearch**; exact-substring edit | Hooks → LLM classifier → dialog; opt-in OS sandbox; worktrees | Hooks, skills (`paths` gating), MCP, plugins, agent defs | Recursive; forks share prompt cache; 16-tool worker whitelist | Plan (read-only permission mode); coordinator mode (gated) |
| Codex | Tokio state machine; FuturesOrdered; no stuck detection | Local or `/responses/compact`; **agent-maintained memory** | 25-30; BM25 `tool_search` for MCP; patch DSL; V8 code mode | Starlark rules → hooks → Guardian LLM (fail-closed) → OS sandbox (3 OS) | Hooks (CC names), skills (auto-installs deps), MCP, marketplace plugins | Thread tree; fork modes; CSV fan-out; TOML roles | Plan/Default presets; effort dial (ultra auto-delegates) |
| Gemini CLI | Async generator; hash + LLM loop check after 30 turns; 100-turn cap | Compress at 50%, keep 30%; distillation pipeline; **memory inbox** | 35+; edits forced sequential; model-visible `wait_for_previous` | Approval modes; TOML per-mode sandbox; credential env scrubbing | 11 hook events, extensions, skills, MCP (full spec) | Registry + `invoke_agent`; only A2A server | PLAN / DEFAULT / AUTO_EDIT / YOLO approval modes |
| Vibe | Async loop + **middleware pipeline** (turn/price/token/compact/read-only) | Middleware auto-compact; re-injects user messages; rewind checkpoints | 12+; exact edit (moved off fuzzy) | ALWAYS/ASK/NEVER per tool; patterns; shell hooks; no sandbox | Skills (registry), MCP, custom tools/agents, hooks | Sequential `task` to "explore" only | 6 agent profiles (default, plan, accept-edits, auto-approve, explore, lean) |
| OH | Event-sourced log; parallel batches with resource locks; 5-scenario StuckDetector | Pluggable condensers; overflow → condense | 25+; 3 edit dialects | Ensemble analyzers (LLM + pattern + rails), worst wins; `<UNTRUSTED_CONTENT>` | Plugins (reads CC format), skills, hooks, MCP; hosts rival harnesses | Parallel child conversations; `/goal` judge loop | Confirm policies; model tool presets incl. "planning" |
| Aider | Generator + lint/test reflection (max 3) | Recursive halving summary | 13 edit formats; ranked repo map | Confirm prompts only | Model registry (350+ models) | None | Edit formats include architect/ask/help |
| Mini-SWE | ~100-line while; step/cost/time/format caps | None (linear history) | 1 (bash) | Limits only | Python protocols | None | None |
| Hermes | Budgeted loop (90); **verify-on-stop guard**; hash stuck detection (warns first) | **Lineage compaction** (new child session); FTS5 recall | 69, scoped per platform; BM25 bridge when schemas >10% of window; 9-strategy fuzzy edit | Config-as-policy; **hard floor survives --yolo**; promptware scan; untrusted delimiters | Skills hub with trust tiers and **self-authoring**; MCP client and server | Fresh-context forks; toolsets intersected with parent; 6-tool blocklist; Kanban swarm | None; posture auto-detected; --yolo flag |
| Pi | ~790-line core; steer/followUp queues; truncation-poisoning guard | Compaction over session tree; iterative merge | 7 built, 4 exposed | None by design; project trust gate | ~33-event extension bus; skills; **no MCP** | Extension spawns processes | None in core; plan mode is an extension |
| OC | Log-as-queue while(true); doom-loop → permission ask | Anchored incremental summary (Objective / Details / Work State / Next Move / Files) | 17; tool surface swapped per model family | tree-sitter command parsing; arity-scoped grants; no sandbox | ~20 plugin hooks, skills (reads `~/.claude/skills`), MCP | Child sessions inherit deny rules | Agents = modes (build, plan, explore); plan = ruleset + reminder |
| OClaw | Event-driven ACP gateway | JSONL transcripts; Active Memory sub-agent | 109+ (channels) | Scope auth, rate limits, SSRF guard | Manifest plugins, skills (`requires` gating), MCP | ACP child processes | Per-agent configuration |

**Practical for a single operator?** Very. It is a survey of decisions that others have already paid for. Inventory
details (counts, versions) go stale within weeks. The structural claims are the durable part (§14.5).

**QMX should…** see synthesis (c). In short: keep the blueprint, and add a truncation guard, concurrency flags,
identical-call detection, a policy floor, a verify-on-stop hook, workspace checkpoints, a skills inbox with trust
tiers, and sub-agent tool intersection. Accept the framework risk knowingly.

---

## 10. Natural-Language Agent Harnesses, NLAH (2603.25723 v2, Tsinghua SIGS / HIT Shenzhen)

**Problem.** Harness policy (stages, state, verification, retries, stopping) is buried in controller code, so it
is hard to inspect, port or ablate (§1).

**Method in plain words.**
- Write the harness *policy* as a short natural-language document (an NLAH). Keep exact *mechanisms* (tests, parsers, sandboxing, validators) in code.
- A thin runtime (IHR: Codex CLI plus a fixed runtime prompt) reads the document and launches child agents with file-based task packets (§3.1, App E).
- Writing rules (§3.2):
  - state the task contract first;
  - separate stages from mechanisms;
  - make state and evidence explicit;
  - give modules clear boundaries so they can be ablated;
  - prefer enforceable clauses ("write a state file before delegating") over vague ones ("be careful").

**Key results** (gpt-5.4-mini, effort xhigh).
- Score by version, code / prompted / NLAH (Table 1): Live-SWE 67.0 / 77.0 / 73.0; Terminal-Bench (MHTBA) 36.0 / 57.3 / 53.9; OSWorld 47.1 / 47.9 / 46.3. *The same text given as an ordinary prompt did as well as or better than the full runtime on 2 of 3.*
- The policy shrank from 60.1K tokens of code to 2.9K of text (Live-SWE) and from 10.5K to 0.8K (MHTBA) (Table 2).
- Weakness: parent-to-child **handoff recall was only 0.32 and 0.55** (Table 4).
- Effect of adding one module at a time, SWE / OSWorld (Table 5):
  - **file-backed state** +2.6 / +13.9;
  - **evidence-backed answering** +2.8 / +2.8;
  - self-evolution retry loop +5.8 / +8.4;
  - verifier +0.2 / +8.4;
  - multi-candidate search −1.6 / +2.8, while agent calls grew from 1.1 to 5.7;
  - **context compression −1.0 / −8.3**;
  - Markdown memory −2.8 / +5.6.
- App C: a code harness tuned on Claude Opus 4.6, run on GPT, timed out in 66 of 89 runs. **21 of those had already passed the verifier**. The cause was the harness's exact two-call stop protocol, which GPT did not follow.
- **Caveats.** One model. Sample sizes are not reported in the main text. The runtime costs more calls and tokens.

**Practical for a single operator?** The writing rules and module findings are practical. The parent/child runtime
is not, because of the handoff loss and the extra calls.

**QMX should…**
- Write each QMX workflow skill as a mini-NLAH: contract → stages → state files → evidence gate → stop condition, with exact checks in scripts.
- Prefer **path-addressable state** (`progress.md`, `skill_plan.md`, artifact manifests) over extra summarisation. This backs the blueprint's "re-inject from files, not summaries".
- Send Sol sub-agents a task packet *file* and require a result *file* (`children/<id>/TASK.md`, `RESPONSE.md`), to counter handoff loss.
- Never build a stop protocol that depends on one model's tool-calling habits. Test every sub-agent loop on GPT-6.1 Sol itself.

---

## Synthesis

### (a) How QMX should author, select, adapt, evaluate and create skills

**Author.** One standard for QMX-owned and user-created skills alike:
- the paper 8 rules, checked by `skill_lint`;
- the SkillAlchemy grammar (each procedure as condition → action → observable output → failure route; explicit limits; verification of the final artifact);
- the NLAH layout (contract first, state files, evidence gate, stop condition).

Body ≤500 lines with key instructions at the top (the blueprint already notes truncation from the end).
Descriptions are third person, state what and when, and are written to *differ* from neighbouring skills.

**Select.**
- Keep catalogs small and distinct. SkillCoach puts GPT-5.5 degradation near 55 distractors and Opus 4.7 near 195. Near-duplicates hurt most, and frontier models still miss the correct skill in a 16-skill slate with 5 near-misses (SkillGate).
- Working targets (my heuristic, not a paper number): about 30 or fewer model-visible skills on the main agent and about 10 or fewer per Sol sub-agent.
- The CI lint includes a lexical similarity check of each new description against the catalog.
- Gate skills by condition at **thread start** only, which keeps the cache stable: skills whose `compatibility`/`metadata` names a connector or tool the user lacks are left out of that thread's catalog (the OpenClaw `requires` idea).
- Use no router model and no "read only one" prompt.

**Adapt.**
- Opus restates the hard constraints before following any skill, and task constraints win over skill steps.
- User-created and imported skills get the one-shot `adapt_skill` → `skill_plan.md` (Primary / Checks / Avoid / Fallback), checked against the QMX harness description (SkillAligner).
- Imported skills also go through RASO's three rewrite rules at import time.

**Evaluate.** Each skill folder holds `evals/`:
1. 5-10 trigger prompts plus 3-5 near-miss prompts that must *not* trigger it;
2. `rubric.json` with SkillCoach key steps and evidence fields;
3. a paired **with-skill vs no-skill** run on the same items, judged by w/l/z (Prompt2Skill), with RRSI's δ/cost rule from the prior synthesis applied when the suite is large enough.

Scores are kept separately for selection, following, composition, reflection and outcome. A skill that loses to
no skill is not shipped. That happens often: off-the-shelf skills regressed in Prompt2Skill, raw skills caused
5.8-17.9% regressions in SkillAligner, and official creators without web sat −1.4 pp below no skill in
SkillAlchemy.

**Create (user-created skills and the approval gate).** The pipeline runs inside the Copilot through a
`skill-creator` skill.
1. **Draft.** SkillAlchemy-lite: brief → parameters → boundary questions → evidence (QMX docs, the user's history, allowed web) → General / Scoped / Exclude with `provenance.json` → render. If an outside skill exists, adapt it RASO-style instead of copying it.
2. **Static gate (deterministic).**
   - `skill_lint`, plus a near-duplicate check against the catalog;
   - a promptware/injection scan of the body, references and URLs (Hermes);
   - a static scan of scripts and path-traversal checks (Gemini CLI);
   - a declared-tools check. `allowed-tools` is experimental in Deep Agents, so QMX enforces the declared tool list itself in a tool-wrapper middleware.
3. **Behavioural gate.** Run the evals in a sandboxed throwaway thread and show the result card in the UI: trigger accuracy, with/without delta, rubric dimensions, regressions.
4. **Risk tier and approval.**
   - **R0** (read and analyse only): the user approves from the card.
   - **R1** (writes workflows, mini-apps or files): user approval, sandboxed execution and workspace checkpoints.
   - **R2** (anything near orders, sizing, node control or external writes): explicit operator approval per the standing rule, and runtime HITL still applies (paper 8: guarantees live in hooks).
5. **Staged activation.** Lifecycle: `draft → trial → active → retired`.
   - A *trial* skill is explicit-only. Deep Agents has no `disable-model-invocation` field, so trial skills live outside the `skills=` paths and load only through a small `use_skill(name)` tool or a UI command.
   - A skill is promoted after N clean uses with rubric scores above threshold.
   - Activation takes effect at the next thread start (cache) and is versioned in git, with one-click rollback.
6. **Learning from use.** Copilot-proposed skill edits (Hermes-style self-authoring) land in a **review inbox** as patches (Gemini CLI's model), never applied directly. This is the tier-3 proposal path of the prior synthesis. Unused or never-winning skills are retired in the quarterly prune pass.

### (b) Robust tool use

1. **Truncation-poisoning guard** (Pi). If a model message hit the output-length limit, fail all of its tool calls unexecuted. Partly streamed arguments can validate while incomplete. This matters most for `propose_order` and node tools. Implement as an `after_model` check on the stop reason.
2. **Concurrency flags** (Claude Code, Gemini CLI). Reads run in parallel, writes and money tools run serially, and the default is serial. (To verify: whether the installed LangGraph/Deep Agents tool executor runs parallel tool calls concurrently. If it does, wrap write tools in a lock.)
3. **Identical-call detection** (OpenCode, Hermes). Hash the tool name plus sorted arguments. Warn after 2 identical failures, and at 3 identical calls raise a HITL "looks stuck, continue?" (paper 9 Rec 18: a dozen lines).
4. **Policy floor** (Hermes). Keep a short deny-list (for example orders above a hard size, node shutdown, credential reads) that no approval setting, skill or prompt can relax, loaded once at process start.
5. **Tool-side robustness** (Hermes, OpenCode). Availability probes with a short TTL and last-good grace; coercion of schema drift from Sol output ("42" → 42); distinct errors for "not found" and "ambiguous"; data tools return validation metadata (row count, date range, staleness) so a silent wrong "success" can be caught (ExpG's coarse-feedback problem).
6. **Per-tool guidance from experience** (ExpG). An offline weekly batch distils `wrap_tool_call` logs into description updates. They ship versioned at thread boundaries, with "must" wording only for stable failure patterns, an over-reaction guard, and tool fixes before guidance.
7. **Evidence-backed answers** (NLAH +2.8 on both benchmarks; SkillAlchemy artifact checks). These reinforce the prior synthesis's pre-finalize probes. Add Hermes's **verify-on-stop** form: if a turn changed a workflow, mini-app or skill without fresh verification output, the final answer becomes a continuation (an `after_model` hook).
8. **Sub-agent tool containment** (Hermes, OpenCode, Claude Code). A Sol sub-agent gets at most the parent's tools, never money, node or memory-write tools, never `task` (no recursion), and never user interaction. Containment is set in each sub-agent's `tools=`.

### (c) The no-modes blueprint against the eleven systems

| QMX choice | Corpus evidence | Verdict |
|---|---|---|
| No modes; risk as HITL permissions | All four vendor harnesses ship a read-only plan mode, but as a permission or approval level (CC permission mode, Codex presets, Gemini approval modes, OC plan = ruleset); Hermes, Pi and Mini-SWE ship none | **Keep.** Consistent with the minimal-core camp. Gemini/Vibe "auto-edit vs ask" is an approval *posture*; if wanted, offer it as one per-thread approval setting that never changes tools or prompt |
| LangChain / LangGraph / Deep Agents runtime | 0/11 production harnesses import a framework (Obs 9), yet Deep Agents is cited as converging on the corpus's conventions (§14.2) | **Keep** (operator decision, 2026-10-04), with eyes open. Log the full assembled request every turn, pin versions, keep the middleware list explicit and owned. The risk is opacity, not capability |
| 10-15 visible tools + provider tool search | Defer above ~15 (Rec 4); CC, Codex BM25, Hermes 10% threshold | **Matches** |
| Hooks as internal middleware | Hooks are the extension substrate in 9/11, mostly *user-facing* shell hooks | Keep internal. User-authored code hooks would be an injection and safety hole; expose declarative rules in the UI instead |
| Skills via SkillsMiddleware | 9/11; lazy loading is universal | **Matches.** **Missing:** trust tiers, quarantine, review inbox, trial state, conditional gating (synthesis a) |
| Single summarizer + offloaded history | 7/11 compact at a threshold; best compact incrementally and reactively; NLAH shows compression hurts while file state helps | Keep. **Add** "previous summary in, merged out" to the summary instructions (OC sections), and confirm the overflow path compacts rather than crashes |
| Opus main + Sol sub-agents | Coordinator-worker in 7 systems, used mainly for breadth-first research (§15.1); Rec 12: stay single-agent otherwise | Keep for research fan-out only. **Add** tool intersection and file-based handoff (NLAH recall 0.32-0.55) |
| Memory provider, SqliteStore default | No system uses embeddings as its main memory; Hermes uses FTS5 with bounded snapshots frozen per session | Matches the prior synthesis (FTS5 + small frozen snapshot) |
| Sandboxed code-over-data tool only | Rec 10: shared or automated contexts need OS-level isolation; Pi refuses partial sandboxes | **Gap.** Users building mini-apps and workflows means arbitrary code. Run all user-authored code in a real isolated runner (container or VM service), not in-process |
| — | Checkpoint/rewind in Vibe, OC (shadow git), Pi, Hermes | **Missing.** Per-turn shadow-git snapshots of the user workspace (mini-apps, workflows, skills) with "undo this turn" in the UI. A LangGraph checkpoint restores graph state, not files |
| — | Truncation guard, concurrency flags, stuck counter, policy floor, verify-on-stop | **Missing**; all cheap (synthesis b) |
| Rubric grader, completion judge, `recall_archived` (prior files) | CC and Codex ship *no* stuck detection or judge loops and still work; NLAH verifier +0.2 on SWE | Possible **overbuild**. Keep judges only on high-stakes deliverables; deterministic probes come first |

### (d) What NOT to adopt yet

- **RL selection training** (SkillGate) and rubric-filtered SFT (SkillCoach §3.5). QMX does not train models.
- **The full Prompt2Skill / RASU optimization loops** as an interactive feature. 400 proxy items and 120-item acceptance batches per skill, with no trading proxy data. Use them later for a few QMX-owned skills, offline, once the eval suite exists.
- **A public million-skill retrieval corpus** (RASO's GitSkills, Raven's crawl). Supply-chain and injection exposure. Retrieve only from curated QMX sources.
- **Per-turn skill adaptation or per-call ExpG judging.** Adapt once per task and judge offline in batches. Doing either per turn breaks caching and adds cost (about $0.0018 and 2.5 s per call).
- **NLAH's parent/child runtime for every task, and multi-candidate search.** Handoff loss, 5x the agent calls, and −1.6 on SWE.
- **"Context compression" as an extra module** beyond the single summarizer (NLAH −8.3 on OSWorld).
- **User-facing code hooks, ACP/A2A servers, a meta-harness, model routers.** No QMX need today (paper 9 Rec 12-13).
- **Building an OS sandbox in-house.** Use an existing isolated runner. The paper calls native sandboxing a multi-thousand-line investment.
- **Auto-applying agent-authored skill or tool-guidance edits.** Everything goes through the inbox and approval gate (Prime's exploit-as-skill and SkillAlchemy's payload results).
- **Taking magnitudes literally.** Most gains come from 8-32B or older models, single runs or small test sets: SkillCoach 50 instances, SkillGate one run, RASO validation sets of 18-24, NLAH sample sizes unreported. Read them as direction, not size.
