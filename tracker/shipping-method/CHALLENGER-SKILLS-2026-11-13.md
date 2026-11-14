# Challenger skills: grounding, 13 November 2026

Grounding only. Nothing was built or installed. Planning is on hold by his word (see `RESUME-2026-11-13.md`), so this file is input for the change list.

The ask: a **challenger** in planning. It grills him, calls out noise and bloat (YAGNI), and sorts ideas into **CORE** (first checkpoints, proving the feature works), **LATER** (nice-to-haves in later checkpoints, after the core is proven) and **DROP**. It should be made of existing skills, not a new method. A later word from him (via the coordinator): no limit on skills; existing skills may be rewritten, merged or created, and where a step can be deterministic, propose the script.

## 1. What already covers part of this

Read in full: `PLANNING-FUNNEL.md`, `funnel-expand`, `funnel-anneal` (with `references/lenses.md`), `funnel-subtract`, `plan-feature`, `plan-review`, `standing/prompts/PLAN.md` and `PLAN-REVIEW.md` (scope parts), `standing/PROJECT-RULES.md` (top), `standing/funnel/CHAIN.md`, `standing/templates/SCOPE.md`, and `check_chain.py` (expand and growth checks).

| Funnel piece | What it already does | What it does not do |
|---|---|---|
| `funnel-expand` step 5 | Sorts his statements into asks (kept few), Decisions so far, Out of scope, Restatement, Proposals. Proposals wait for his yes. Proposes a split past ~8 asks. | Never rules an ask CORE or LATER. No budget. |
| `funnel-anneal` lens 2 | Attack the premise of each plan line against the code. | Program-level premise ("does the whole idea hold?"). |
| `funnel-anneal` lens 5 | Party-mode debate in session mode: Winston, a trader, a skeptic, plus one. | Verdicts. Its rule is "a question is never a verdict on an idea". |
| `funnel-anneal` lens 6 | "Deeper, not bigger": anything new becomes a Proposal `P<n>`. | Says nothing about when a proposal would be built. |
| `funnel-anneal` lens 7 + `funnel-subtract` | Code that can be deleted, each justified; agreed removals in `REMOVED.md` (YAGNI on disk); guard against rebuilding removed rows. | Scope of the ask itself. It removes code, not ideas. |
| `check_chain.py` | Ask quotes match the transcript (`transcript_turn`); `SLICES_PER_ASK_WARN = 4` needs a `Growth:` line. | No verdicts, no PR budget, no checkpoint order. |
| `plan-review` scope.md | "Challenge any slice that only exists to split work." | Comes after the plan is written; too late to cut cheaply. |

**Fact that shapes the design.** Annealing fills gaps and must never judge. The challenger judges. Keep them in separate steps, the challenger first, so annealing works only on what survived. The challenger's DROP rows reuse funnel-subtract's `REMOVED.md` shape (`no code change`), so a dropped idea stays dropped.

**His rule that is already a CORE/LATER test** (`standing/PROJECT-RULES.md`, "What QMX is for"): he asks two things of an idea. Is it configuration? If it is left out now, does the core get reworked later? "An idea that passes neither test is content someone adds later." Memory `foundation-first-design` says the same: "what is the base that lets this grow on its own? ... cut the rest to the backlog", and never say "minimal viable" to him.

## 2. Candidates read, one by one

Columns: what it does; can it run headless in one agent that spawns nothing; what it gives the challenger; cost; overlaps and conflicts.

### Matt Pocock set (`~/.agents/skills`, linked into `~/.claude/skills`)

**`grilling`** (1.9 KB). Interviews the user as a design tree. Each round asks the whole **frontier** (decisions whose prerequisites are settled), numbered, each with a recommended answer, then waits. Facts are the agent's job (it dispatches a subagent); decisions are the user's. Done when the frontier is empty; act only after the user confirms.
- Headless: no as written (waits for answers, spawns fact-finders). Adapt: the agent builds the tree and frontier, looks facts up itself, and returns the frontier batch to the lead, who asks him. A fresh agent folds the answers and computes the next frontier.
- Gives: the question discipline and the stop rule (frontier empty). This is the "grills him" part.
- Overlap: the funnel already batches at 4 questions with a recommendation each, which is grilling's shape.

**`grill-me`, `grill-with-docs`** (wrappers). `disable-model-invocation: true`, so an agent cannot call them. `grill-me` just runs `grilling`; `grill-with-docs` adds `domain-modeling`. Nothing extra to borrow.

**`wayfinder`** (12 KB). Charts a huge, foggy effort as a map issue on a tracker with child decision tickets (research, prototype, grilling, task), resolves one ticket per session. `disable-model-invocation: true`. Grilling tickets are human-in-the-loop: "a grilling agent that answers its own questions has broken this."
- Headless: no. Needs a tracker and a human per ticket. `ask-matt` itself says save it for huge foggy efforts, never a well-scoped feature.
- Gives vocabulary that `SCOPE.md` already uses (its template says "shaped like a Wayfinder map"): **Destination** (source of the core sentence), **Out of scope** ("never graduates", the model for DROP), **Not yet specified** (fog). Note: LATER is not fog. LATER is sharp but deferred; fog is in scope but unsharp. Keep them apart.
- The HITL rule above is the guard for the challenger: it recommends, he decides.

**`domain-modeling`** (3.5 KB). Challenges fuzzy terms, invents edge scenarios, writes `CONTEXT.md` and sparse ADRs. QMX has no `CONTEXT.md` or `docs/adr/` (checked). Use only the "sharpen fuzzy language" move on the core sentence (unit, pod, book). Do not create `CONTEXT.md`.

**`codebase-design`** (6.6 KB). Deep-module vocabulary and the deletion test. Already used by funnel-subtract. Little for scope verdicts.

**Not on the list but found:** `ask-matt` (router), `to-questionnaire` (async question document; could shape `WAITING.md`), `loop-me` ("push right": ask once, late, with a decision-ready brief). Only `loop-me`'s "push right" idea matters: put his questions at the end of the run, all prepared.

### pstack (`~/.claude/skills`, Cursor's poteto set)

**`poteto-mode`** (24 KB plus playbooks). A style and router. Two parts matter:
- Autonomy: "No is an acceptable answer ... say 'this doesn't earn its place' when true ... candor over sycophancy." This is the challenger's tone.
- The question trigger: before asking, classify it. A fact you can observe is not his to answer; ask only real product or preference calls.
- Headless: yes (it is a style). Cost: read the Non-negotiables, Principles list and Autonomy only (about 5 KB); skip playbooks. The `multi-phase-plan` playbook's step 1 ("one or two files with an obvious approach: skip the plan") is a useful DROP-the-process check for tiny asks.

**`principle-attack-the-premise`** (1.9 KB). Built for "two fixes that share a premise failed the same gate": write the premise down, census, remove the asymmetry. Only its first move fits planning: write down the one sentence every ask assumes. Anneal lens 2 already applies it per plan line. The challenger applies it once, to the whole program (the 13 Nov unit-versus-book doubt is exactly this kind of premise).

**`principle-subtract-before-you-add`** (1.1 KB). "Cut before you polish", "design for observed usage, not speculative edge cases", "no speculative validators". Gives LATER its reason. Overlap: funnel-subtract applies it to code.

**`principle-laziness-protocol`** (1.4 KB). Smallest change, consolidate decisions, question signal threading. Gives the pressure behind the PR budget.

**`principle-exhaust-the-design-space`** (1.1 KB). Build 2 to 3 prototypes when there is no precedent. Pushes the other way (more work). Conflicts with his 31 Oct ruling "no throwaway prototypes". Not part of the challenger; at most a call-out "this CORE item has no precedent".

**`principle-experience-first`** (1.2 KB). "Every feature, control, and option must be justified", "ship less, ship better", "tighten the core loop". The best single verdict lens. Conflict to state: in QMX every threshold is a named setting ("configuration, never caps"), so "every option must be justified" applies to features, not to settings.

**`figure-it-out`** (4 KB). Designs a bespoke playbook for a big run. Phase A "Frame" is the napkin: done as a falsifiable predicate, "scope, quantified: rough units and effort", present before committing. Headless: yes for Phase A only. The rest (logs, hypothesis loop) is for execution.

**`why`** (11 KB). Rationale investigator; spawns parallel investigators by default. Not needed: grounding already reads PR history. Skip.

**`interrogate`** (5.6 KB). Multi-model review of code diffs; spawns. Code, not scope. Skip.

### BMad (QMX `.claude/skills`)

**`bmad-forge-idea`** (10 KB). Pressure-tests an idea one question at a time, until it is **Hardened**, **Killed** or **Clearer**. Modes the user can call: "attack this", "defend this", "switch roles". Each turn uses two voices: one installed persona plus one generated outside voice (competitor, buyer, finance reviewer). Logs `decision | assumption | crack | kill | lock` lines via `_bmad/scripts/memlog.py` (exists). Writes `forged-idea.md` and a sealed `forge-report.html`.
- Headless: no mode for it; it asks one question at a time and greets. Adapt: run attack mode on each ask yourself, voice both personas inline (the skill allows "voice the personas yourself by default"), log with memlog, skip greeting and the HTML.
- Gives: the verdict language. Killed maps to DROP, locked to CORE. The two-voice method is cheaper than a full party.
- Overlap: anneal lens 5's debate. Use forge voices in the challenger and leave the party to annealing.

**`bmad-advanced-elicitation`** (5 KB, 71 methods in `assets/methods.csv`). Serves a 5-method menu, runs the pick, waits for y/n before applying. `scripts/pick_methods.py show <name>` serves any row.
- Headless: the menu and y/n are interactive; the catalog is not. Adapt: name the methods, run them, record results instead of asking.
- Methods that fit the challenger: 59 Pre-mortem, 31 Inversion, 51 Occam's Razor, 43 Subtraction, 45 Reframe the Question, 64 Assumption Audit, 22 Shark Tank Pitch, 24 First Principles. Each is a few lines.

**`bmad-party-mode`** (9.6 KB plus references). Round-table of distinct voices. `session` mode voices everyone inline. Normally runs until the user says done, but "an explicit `--non-interactive`" runs one intent to a natural close. No custom party exists in `_bmad/custom` (checked), so the roster is the installed agents.
- Headless: yes, in `session` mode with `--non-interactive`.
- Gives: a scope court for the few contested calls only.
- Overlap: anneal lens 5 already seats Winston, a trader and a skeptic every round. Running a second full party is duplication; one short round on contested items is enough.

**`bmad-cis-problem-solving`** (13 KB, 30 methods). A 9-step facilitated workflow (define, diagnose, root cause, forces, options, select, implement, monitor, lessons). After each template output it saves and waits on `[a] [c] [p] [y]`.
- Headless: poor. It is a long, gated document workflow. Its method list is the useful part: Problem Statement Refinement, Is/Is Not Analysis (boundaries, feeds DROP), Pareto Analysis (the vital few, feeds CORE), Constraint Identification, Assumption Busting.

**`bmad-cis-design-thinking`** (10 KB). Empathize, define, ideate, prototype, test, with users. Low fit: QMX's user is him, and he is in the room. Skip.

**`bmad-cis-agent-*`** (4.4 KB each). Personas that route to the CIS workflows: Dr. Quinn (problem solver), Victor (innovation strategist, "devastatingly simple questions"), Maya (design thinking), Carson (brainstorming, "YES AND everything"), Sophia (storyteller), Caravaggio (presentations). Interactive persona menus. Only Victor and Dr. Quinn are useful, as forge voices. Carson is the opposite of a challenger.

**`bmad-brainstorming`** (9.7 KB). Divergent ideation. Has a real headless mode (`references/headless.md`). Its `references/converge.md` holds the convergence moves: Affinity Clustering, Impact–Effort, NUF, Forced Ranking, PMI, **MoSCoW** (Must, Should, Could, Won't this time).
- Gives: MoSCoW maps straight onto the verdicts (Must = CORE, Should and Could = LATER, Won't = DROP). Impact–Effort helps rank LATER.
- Conflict: memory `generative-steps-unbounded` says divergent steps get full freedom first, then sorting. The challenger is the sorting; it must not run while expand is still diverging.

**`bmad-review-adversarial-general`**: a deprecated shim to `bmad-review`'s adversarial lens, which must produce at least ten findings. Forced findings are padding, the noise the challenger is meant to cut. Already used in plan review and technical annealing. Not part of the challenger.

**`find-skills`**: uses `npx skills find`, or the skills.sh leaderboard. I used the skills.sh search API through a web fetch instead (nothing installed or executed).

### Plugin skill folders (`~/.claude/plugins`)

Searched every `SKILL.md` under `cache/` and `marketplaces/` for wayfinder, grill, YAGNI and pre-mortem. No match. Nothing named Wayfinder exists outside `~/.agents/skills/wayfinder`.

## 3. skills.sh finds (nothing installed)

Searched `yagni`, `grill`, `premortem`, `scope`, `shape up` through `https://skills.sh/api/search?q=...`. Two more searches returned HTTP 503. Install counts as shown on 13 Nov.

| Skill | Installs | What it is | Use for the challenger |
|---|---|---|---|
| [mattpocock/skills/batch-grill-me](https://skills.sh/mattpocock/skills/batch-grill-me) | 61k | Grilling with the whole frontier per round, recommended answers. | Same as our installed `grilling`. Nothing new. |
| [addyosmani/agent-skills/interview-me](https://skills.sh/addyosmani/agent-skills/interview-me) | 69k | One question at a time, with a guess, until it can predict the answer; asks for the binding constraint. | Concept: stop when you can predict his answer. |
| [addyosmani/agent-skills/idea-refine](https://skills.sh/addyosmani/agent-skills/idea-refine) | 71k | Diverge, converge, one-pager. | Overlaps expand plus brainstorming. Skip. |
| [riekelt/principal-engineer/scoping-changes](https://skills.sh/riekelt/principal-engineer/scoping-changes) | 24k | Size each change to its trigger. Test: would the addition ship on its own merits without the main fix? If yes, it is a separate change. No structure until a second real case. | The cleanest LATER test. Borrow the sentence. |
| [juliusbrussee/caveman/lean-build](https://skills.sh/juliusbrussee/caveman/lean-build) | 123k | Code-level: acceptance criteria plus explicit non-goals; one coherent end-to-end path; report material omissions. | Concept for the CORE checkpoint: the thinnest end-to-end path, with non-goals named. |
| [phuryn/pm-skills/pre-mortem](https://skills.sh/phuryn/pm-skills/pre-mortem) | 10.6k | Launch pre-mortem from a PRD; separates real risks from worries, plans for launch-blocking ones. Snyk warns. | Concept: launch-blocking risk is CORE, the rest LATER. Our elicitation method 59 covers it. |
| [jeffallan/claude-skills/the-fool](https://skills.sh/jeffallan/claude-skills/the-fool) | 4.8k | Five modes: expose assumptions, argue the other side, failure modes, attack, test the evidence. Asks the user to pick a mode. Gen Agent Trust Hub audit: Fail. | Concept only: "steelman the thesis first, then attack". Do not install (audit fail). |
| [sd0xdev/sd0x-harness/necessity-audit](https://skills.sh/sd0xdev/sd0x-harness/necessity-audit) | 17 | YAGNI audit of specs. Six dimensions scored Clean/Low/Med/High: necessity now, abstraction (two real consumers), extensibility speculation, configurability excess, premature optimization, scope drift. **Cut** if any High, **Review** if two Med, else **Keep**; stricter wins. Phase B needs a Codex debate. | Best rubric found. Deterministic mapping; borrow it into a script. Drop "configurability excess" (clashes with "configuration, never caps"). Low installs, so borrow, don't install. |
| [wondelai/skills/37signals-way](https://skills.sh/wondelai/skills/37signals-way) | 4.7k | Scores a plan 0–10 against Getting Real, Rework, Shape Up: fixed time, flexible scope. | Concept: the PR budget is Shape Up's **appetite** (fixed budget, scope bends to fit). |
| [sentimony/skills/scope-triage](https://skills.sh/sentimony/skills/scope-triage) | 3.8k | One-turn scope check that routes to a contract or a full design. | Similar to our light/medium/deep depth. Skip. |
| [jsmastery-pro/skills/scope](https://skills.sh/jsmastery-pro/skills/scope) | 4.9k | Coarse ordered feature plan in phases with "Done when"; replan mode reconciles what shipped. | Overlaps handoff. Skip. |
| [softaworks/agent-toolkit/requirements-clarity](https://skills.sh/softaworks/agent-toolkit/requirements-clarity) | 1k | 100-point clarity score, then a PRD. | Overlaps annealing. Skip. |

Shape Up concepts worth naming (from the book, not from a fetched skill): **appetite** (the budget is set first), **scope hammering** (cut to fit the budget), nice-to-haves marked `~` inside a scope, **rabbit holes** and **no-gos** written down before building. LATER is `~`; DROP is a no-go.

## 4. The recommended composition

### Where it sits

A new stage between Ground (2) and Self-annealing (3): **2b. Challenge**, skill `funnel-challenge`, run by one fresh Fable agent, headless, spawning nothing. Reasons:
- After grounding, so the PR budget is sized against real code, and the challenger can cite facts instead of asking him.
- Before annealing, so annealing (which grows plans with edge cases, operations and proposals) works only on CORE and LATER, and the budget already exists to hold it.

It reads: `SCOPE.md`, `GROUND.md` (with its `## Removed` rows), `decisions/`, `standing/PROJECT-RULES.md`, and the memory notes `foundation-first-design`, `count-whole-queue-no-widening`, `generative-steps-unbounded`, `dont-reask-settled-decisions`.

It writes: `CHALLENGE.md` (core sentence, premise, napkin with PR budget, verdict table, call-outs), `challenge/` notes, and decision files `For: him` (returned to the lead, who writes them, as in annealing).

### The steps, in order, and what each hands on

| # | Step | Skills used (as concepts, adapted) | Hands to the next step |
|---|---|---|---|
| 0 | **Posture.** Read poteto-mode's Autonomy ("No is an acceptable answer") and its question-classification trigger; PROJECT-RULES' two tests; the four memory notes. | `poteto-mode` (sections only) | The tone, and the rule: facts are looked up, never asked. |
| 1 | **Core sentence and premise.** One plain sentence, at most 25 words, saying what is true when the feature works, as a falsifiable predicate, built from the `Destination` quote. Below it, the one premise every ask assumes, written down. Sharpen any fuzzy term. | `figure-it-out` Phase A, Wayfinder Destination, `principle-attack-the-premise` (first move only), `domain-modeling` (sharpen only) | The yardstick every verdict is measured against. |
| 2 | **Napkin and PR budget.** The thinnest end-to-end path that proves the core sentence, as checkpoints of 5 to 8 slices with named non-goals; then the LATER checkpoints. Budget line: `PR budget: core <n>, later <m>, checkpoints <k>`. The budget is fixed first; scope bends to fit. | Shape Up appetite, `lean-build` (end-to-end path, non-goals), `principle-laziness-protocol` | The budget the verdicts must fit, and the CORE path. |
| 3 | **Verdicts.** One row per ask `S`, proposal `P` and Not-yet-specified item: CORE, LATER or DROP, with one line of reason and evidence. Score with the rubric below; `verdict.py` maps scores to the verdict. Steelman each ask first, then attack it in forge's two voices (one installed persona such as Victor or the PM, one generated voice such as a day trader). Run elicitation methods by name, no menu: Pre-mortem (59), Occam (51), Subtraction (43), Reframe (45), Assumption Audit (64). Present as MoSCoW. | `bmad-forge-idea` (attack mode, two voices, memlog), `bmad-advanced-elicitation` (named methods), `bmad-brainstorming` `converge.md` (MoSCoW), `principle-experience-first`, `principle-subtract-before-you-add`, scoping-changes' test, necessity-audit's rubric | The verdict table; contested rows marked. |
| 4 | **Call-outs.** Noise and bloat, one line each: what, why it is bloat, the evidence (his quote with source, a `GROUND.md` fact, or file and line), and the recommended verdict. Only real items; no quota. | `principle-subtract-before-you-add`, `principle-laziness-protocol` | Items for his batch. |
| 5 | **Contested rows only.** One party round, `session` mode, `--non-interactive`: a skeptic, a trader, the PM. Saved to `challenge/debate.md`; the room's disagreement becomes a question for him. Skip when no row is contested. | `bmad-party-mode` | Questions with both sides stated. |
| 6 | **Questions for him.** Build the design tree; ask only the frontier; each question has a recommended answer first; at most 4 per batch; facts never asked. Order: core sentence, budget, any DROP of his own ask, contested CORE/LATER calls. Return the batch to the lead. | `grilling` (frontier, recommendation, stop rule), `loop-me` ("push right") | The lead asks him (AskUserQuestion). A fresh agent folds the answers and recomputes the frontier. Done when the frontier is empty. |
| 7 | **Record.** DROP rows he agreed go to `REMOVED.md` as `no code change` rows. Run the check. | `funnel-subtract` row shape | `CHALLENGE.md` to annealing. |

**The verdict rubric.** His two tests come first and set a floor:
- "If it is left out now, does the core get reworked later?" Yes means CORE.
- "Is it configuration?" Yes means it ships as a named setting with a default inside the CORE item it belongs to, never as its own feature.
- Neither test passes: LATER at most ("content someone adds later").

Then necessity-audit's dimensions, scored Clean, Low, Med or High: necessity now, abstraction with two real consumers, extensibility speculation, premature optimization, scope drift from the core sentence. Add the scoping-changes test (would it ship on its own merits without the core? then it is its own LATER item). Any High means DROP is recommended; two Med means contested; the stricter result wins. DROP is also recommended when an item rebuilds a removed row, contradicts a ruling, or crosses a fixed line.

**Who decides.** Only he can DROP or demote one of his own asks; the agent recommends (`For: him`, as funnel-subtract does). The agent decides on its own proposals (park as LATER, or DROP). This follows Wayfinder's rule that the agent never answers its own grilling question, and the funnel rule that no agent settles his words.

### Where interactive skills need adapting

- `grilling`: return the frontier batch to the lead; look facts up instead of spawning a fact-finder; one fresh agent per answer round.
- `bmad-forge-idea`: no greeting, no "attack/defend" prompt to the user, no HTML seal; attack mode is fixed; voice both personas inline; keep the memlog.
- `bmad-advanced-elicitation`: no menu, no y/n; call methods by name with `pick_methods.py show`.
- `bmad-party-mode`: `session` mode with `--non-interactive`, one round, contested rows only.
- `bmad-brainstorming`: use only `references/converge.md`; never the divergent session.
- Not adapted, not used: `wayfinder` (tracker, one ticket per session), `bmad-cis-problem-solving` and `bmad-cis-design-thinking` (gated document workflows; borrow only Is/Is Not and Pareto), `bmad-review` adversarial lens (forced ten findings is padding), `why` and `interrogate` (spawn; code-focused), `principle-exhaust-the-design-space` (pushes for more prototypes, against his no-prototypes ruling).

### Cost

The Fable agent's skill reading is about 30 KB: grilling, forge, the named principles, poteto's Autonomy and Principles, `converge.md`, about eight elicitation rows, and PROJECT-RULES. The program inputs come on top. The party round adds about one turn, only when a row is contested. Each answer round needs one fresh agent; most programs should need one or two rounds.

### Changes to existing skills (recommend, not built)

| Skill | Change |
|---|---|
| New `funnel-challenge` | Steps 0 to 7 above, with `scripts/verdict.py`. Written to `writing-for-agents`. |
| `plan-feature`, `standing/prompts/PLAN.md`, `PLANNING-FUNNEL.md` | Insert stage 2b; he reads the verdicts and the budget with the first decision batch. |
| `funnel-anneal` | Lens 6: a new proposal is LATER by default unless he promotes it. Plan lines inherit their ask's verdict (`S1.a` of a LATER ask is LATER). A light round for LATER-only asks (lenses 1 to 4 and 7). |
| `funnel-handoff` | Order checkpoints: every CORE checkpoint before any LATER one. The last CORE checkpoint's done line is the core sentence's predicate. |
| `plan-review` (`scope.md` part) | Read `CHALLENGE.md`; check slices against the verdicts and the budget. |
| `stop-review` | At the last CORE stop: is the core sentence true on the real app? LATER checkpoints start only after that. |
| `standing/templates/SCOPE.md` or a new `CHALLENGE.md` template | Core sentence, premise, napkin, budget line, verdict table, call-outs. |

## 5. Scripts that make the challenger deterministic

| Script | Belongs to | What it checks |
|---|---|---|
| `funnel-challenge/scripts/verdict.py` | `funnel-challenge` | Reads the rubric table in `CHALLENGE.md`; applies the two-test floor and the High/Med mapping; writes the verdict column; fails if a hand-written verdict disagrees with the scores without a `(his call, D<n>)` note. |
| `check_chain.py --stage challenge` (new stage) | `standing/funnel/` (shared by all funnel skills) | Every live `S`, `P` and Not-yet-specified item has exactly one verdict. The core sentence exists, is one sentence, is at most 25 words, and quotes him with a source. The `PR budget:` line exists with numbers. Every call-out carries evidence (a quote with source, a `GROUND.md` fact, or `file:line`). A DROP of one of his asks has a decision file `For: him`, and once answered an `R` row in `REMOVED.md`. Every quote of his words in `CHALLENGE.md` matches the transcript, reusing `transcript_turn` and the quote-matching code already in `check_expand`. |
| `check_chain.py --stage anneal` (extend) | `standing/funnel/` | Every plan line carries its ask's verdict. A new `P` after the challenge is LATER until he promotes it. No CORE plan line serves only a LATER ask. |
| `check_chain.py --stage handoff` and `check_plan.py` (extend) | `standing/funnel/`, `standing/` | Slice count per verdict is within the budget, unless `Budget raised: D<n>` cites his yes. This replaces the soft `SLICES_PER_ASK_WARN` growth line with a hard budget. No slice in a CORE checkpoint serves a LATER ask (no LATER item hidden in a core slice). Every CORE checkpoint comes before any LATER one in `PROGRAM.yaml`'s `stop_points`. A DROP ask has no slice. |
| `his_words.py` (exists) | `standing/funnel/` | Already finds his own turns; the challenge check reuses it. On 13 Nov it returned 0 turns for every pattern tried (`napkin`, `challeng`, `grill`, `wayfinder`, even with `--since 2026-11-12 --pastes`). Either today's turns are not in its transcript folders yet, or the folders moved. Check that before the challenge stage relies on it. |
