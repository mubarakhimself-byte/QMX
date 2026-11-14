# The planning funnel (14 November 2026)

How a planning session turns his ask into a program folder the factory can build. This revision adds stage 2b, the challenge, and the cut that follows it; the `## Interfaces` section of the architecture and the `API:` line of every brief; and how planning meets the audit branch. The stage list in `D:/factory/skills/plan-feature/SKILL.md` is the source of truth. Where this file and that skill differ, the skill wins. How the rest of the factory works is in `SHIPPING-METHOD.md`.

He never pastes a prompt. When he describes something to build, the front desk runs the `plan-feature` skill, which holds the whole planning prompt (the old `standing/prompts/PLAN.md` was folded into it). Each skill and stage agent reads its row of `D:/factory/INDEX.toml` first.

## What planning is for

Planning is context engineering. It removes ambiguity until the work is clear enough that even an old model can build it without breaking a sweat.

- **A question means context is missing.** Each question is a gap to fill. It is never a test an idea failed.
- **Each stage hands richer context to the next.** Nothing is thrown away. Later stages read how ambiguity was removed, not only the result.
- **Linking logic grounds rough ideas.** "Self-configuring units" is vague; "self-configuring like Kubernetes" is clear. It works by analogy (a known system that works that way) or by reference (a module, a paper, a ruling, a product).
- **The challenge keeps the plan from growing.** CORE comes first and proves the feature works. LATER comes after and is never thrown away. DROP needs his yes when the item is his.

## One chain per feature

Every ask is a chain from his words to code. `PROGRAM.yaml` links the levels, so a builder can walk from its slice back to the reasoning behind it.

| Level | Id | File |
|---|---|---|
| His words | quote + source | `SCOPE.md` |
| His asks | `S1` | `SCOPE.md` |
| Their verdicts | `core`, `later`, `drop` | `CHALLENGE.md` |
| Plan lines | `S1.a` | `PLAN.md`, shaped by `ANNEAL-LOG.md` |
| Architecture | `A1` | `arch/ARCH.md` |
| Interfaces | `I1` | `arch/ARCH.md`, `## Interfaces` |
| Slices | `<prefix>-01` | `SLICES.md`, `slices/<id>/BRIEF.md` (`Serves:`, `Chain:` and `API:` lines) |
| Code | the PR | the PR body names its slice |

Beside the chain sit questions `Q`, decisions `D`, proposals `P`, edge cases `E`, can-change candidates `X`, and removals `R`. An audit adds intent lines `N`, ambiguities and findings `F`. The exact shapes are in `D:/factory/skills/factory-core/references/CHAIN.md`. `check_chain.py` proves the links after every stage and reads who decided what as data. A decision he never saw cannot pass as his, an agent cannot "dissolve" a question, and every plan line, element, edge case and Interfaces row must reach a brief. Its fixtures are in `D:/factory/skills/factory-core/tests/`, and each fails on its own id.

## Rules at every stage

- **Contradictions and ambiguity go to him, with a recommendation.** Each carries the agent's best proposal and its reason. No agent settles one silently, and a later quote that seems to revise an earlier one is put to him to confirm.
- **Only he decides on what came from his words:** his `S` asks, a `P` proposal that quotes him with a source, and a `D` ticket under Not yet specified. An agent decides only on its own proposals, and those are always `later` until he promotes one (D-L8).
- **Agents' own ideas are welcome, as proposals.** They enter the plan only through his asks or his yes. A fix may make a plan line clearer, but never adds something new that must be true.
- **Removed stays removed.** Each agreed deletion is recorded with its reason, what replaces it and a plain-words line: planned in the program's `REMOVED.md`, then moved to `_records/REMOVED.md` when its checkpoint merges. Rows he decided bind everyone. Rows an agent decided bind agents only.
- **Every feature gets an operations layer,** whether he mentions it or not, for mini apps, workflows and agentic systems alike:
  - logging;
  - observability;
  - monitoring;
  - self-recovery: health checks, restarts and retries, safe fallbacks, and an alarm only when recovery fails;
  - backend operations for the APIs and databases it touches;
  - deployment: how this change reaches a running QMX.

  The architecture must have a `## Operations` section, and every brief's done line an `Operations:` line. **Built today:** `funnel-architect` does not ask the deployment line yet (design section 2.10).
- **Every feature answers the interfaces question:** what does it add, change or remove at the UI's door, and which screen uses it? The architecture must have a `## Interfaces` section, even when the answer is "none, because ...".
- **The fixed lines are named early.** Grounding lists every fixed line the area touches:
  - money;
  - promotion to live;
  - exits;
  - the kill switch;
  - keys;
  - stdlib blocks.

  Each one gets an edge case, a safety fact in its brief, and a screen in stage 5.
- **Models.** Every agent is Claude Opus 5.5 at high effort, except two Fable seats: the challenger of stage 2b, and the answer-linker of stage 5 (one per batch of technical decisions). Only one Fable agent runs at a time across the machine. When Fable cannot be started, or its seat is turned down to Opus, Opus stands in and the lead tells him in one line.
- **Who spawns.** The lead (the front desk running `plan-feature`) spawns agents, writes decision files and asks him. Agents spawn none, and run a skill's steps one after another.
- **Record each stage.** At each stage's start and end the lead runs `python -m ship phase --program <program> --set <word> --status running|done|waits --by plan-feature`. The words are the kit's: `expand`, `ground`, `challenge`, `cut`, `anneal`, `subtract`, `architect`, `technical`, `handoff`.

## The stages

| # | Stage | Skill | Check | Hands on | His part |
|---|---|---|---|---|---|
| 1 | Expand | `funnel-expand` | `--stage expand` | `SCOPE.md`: his asks quoted and sourced, the destination, the depth | Confirms the asks |
| 2 | Ground | `funnel-ground` | `--stage ground` | `GROUND.md`: facts that rerun, open items, in-flight branches, fixed lines, removed rows, doc drift, the UI surface today | None |
| 2b | Challenge | `funnel-challenge` (Fable) | `--stage challenge` | `CHALLENGE.md`: core sentence, premise, simple sketch, PR budget, a verdict per item, call-outs; proposed questions | None |
| | The cut | `plan-feature` (the lead) | `--stage cut` | His verdicts in decision files, the agreed DROPs in `REMOVED.md`, `gates.cut` | **Answers the cut** |
| 3 | Self-annealing | `funnel-anneal` (plan mode), then `funnel-subtract` | `--stage anneal` | `PLAN.md`, `ANNEAL-LOG.md`, `EDGE-CASES.md`, `CAN-CHANGE.md`, `REMOVED.md`, decisions | Answers decision batches; **reads plan v1**, may say "go" in advance |
| 4 | Technical lens | `funnel-architect` | `--stage arch` | `arch/`: element index, `## Operations`, `## Interfaces`, spine, diagrams | None, except one-way UI changes |
| 5 | Technical self-annealing | `funnel-anneal` (technical mode), the answer-linker (Fable), an Opus screen | `--stage technical` | The settled architecture; the agents' decisions, screened | Only hidden product calls |
| 6 | Handoff | `funnel-handoff` | `--stage handoff`, then `check_plan.py` | `SLICES.md`, briefs, chain packets, `checks.toml`, `PROGRAM.yaml` | None; plan review follows |

Every check is `python D:/factory/skills/factory-core/scripts/check_chain.py <program> --stage <stage>`. A stage starts only when the one before it has passed. `--stage arch` checks the `architect` word, and `--stage anneal` also covers `subtract`.

### 1. Expand: as deep as the feature needs

The planner picks a depth, writes it as `Expand depth:` in `SCOPE.md`, and says why; he can override it.

- **Light:** a clear ask on something that exists. Restate it and confirm.
- **Medium:** add research on the unfamiliar parts.
- **Deep:** a new domain, like the risk work. Add his brain dump, papers, inspiration and research agents.

The asks are the outcomes he wants from this program, in his words, each with its source. `SCOPE.md`'s `## Destination` quote is what the challenge builds the core sentence from. Keep the asks few: a one-line question gets a handful, not a list of everything he has said nearby. Definitions go to Decisions so far, boundaries to Out of scope, and the planner's ideas to Proposals. `his_words.py` reads every transcript folder the project profile lists, finds his own turns and his answers to questions, and skips summaries and agent notes. If the asks fall into separate parts, the planner proposes splitting them into programs.

When the program came from an audit (`inputs.audit` in `PROGRAM.yaml`), expand reads the audit's `INTENT.md`, `AUDIT.md` and the hand-off row, and quotes his approval.

### 2. Ground: what is really there

The planner reads, at the `engine/base` tip:

- the area's code;
- its PR history and `OPEN:` lines;
- in-flight build branches;
- the fixed lines it touches;
- the removed lists;
- the docs, as claims to check against the code;
- the UI contract in `contracts/` (the operations and streams in the area) and the open backlog rows of source `ui-ask`, written to `GROUND.md`'s `## UI surface today`.

Every fact is a command plus its real output, the form a brief carries, and the check reruns the facts (`--rerun-facts`). A failed fetch stops grounding. Grounding never waits for a docs refresh; docs catch up after each merge. When the program came from an audit, ground starts from the audit's facts and reruns them at the tip.

**Built today:** `contracts/` is not on `engine/base` yet (U23). Until it is, `## UI surface today` reads the routes from the code and the `ui-ask` rows.

### 2b. Challenge: say no before the plan grows

He asked for this stage on 13 November: an agent that calls him out when he is not clear, filters the noise, and stops a 3-PR idea from becoming 70 PRs. The challenge judges. Annealing, which comes after it, fills gaps and never judges, so annealing works only on what the challenge leaves CORE or LATER.

**Who.** One fresh Fable agent on the `funnel-challenge` skill in plan mode. It spawns nothing and asks nobody. Facts it looks up; questions for him it writes down for the lead.

**Built today:** the challenger has its own worker prompt (`D:/factory/skills/factory/prompts/CHALLENGER.md`), run as one Fable worker.

**What it writes.** `CHALLENGE.md`, from the template in `funnel-challenge/templates/`, with notes in `challenge/` (`scores.md`, `voices.md`, `debate.md`):

1. **Core sentence.** One sentence, at most 25 words, true exactly when the feature works, that someone could check on the real app. It names the quote it is built from: `Core sentence: "<sentence>" (built from: "<his words>" <id8>:L<line>)`. The check matches that quote against the transcript.
2. **Premise.** The one thing every ask assumes, attacked once against `GROUND.md`: it holds, or it is doubtful. A doubtful premise is the first question for him.
3. **Simple sketch.** The thinnest end-to-end path that makes the core sentence true, in 5 to 10 plain lines or one small diagram, with `Not in the first path:` naming what is left out.
4. **PR budget.** `PR budget: core <n>, later <m>, checkpoints <k>`, counted off the sketch (one slice is one PR; a checkpoint holds 5 to 8). The budget is set first and scope bends to fit it. If the asks cannot fit any budget he would recognise from his own words, the challenger says so as a call-out, never by raising the number.
5. **Verdicts.** One row per live `S` ask, `P` proposal and `D` ticket under Not yet specified. For each, the challenger steelmans it, then attacks it in two voices (an installed persona and one it makes up, such as a day trader or a maintainer a year from now), and runs pre-mortem, Occam's razor, subtraction, reframe and an assumption audit. It fills three test columns and sets the verdict:
   - left out now, the core is reworked later: **CORE**;
   - it is configuration: it ships as a named setting with a default inside the CORE item it belongs to, never as a cap and never as its own feature;
   - neither: **LATER** at most;
   - it would ship on its own merits without the core: its own LATER item;
   - it rebuilds a removed row, contradicts one of his rulings or crosses a fixed line: recommended **DROP**.
6. **Call-outs.** One line per piece of noise or bloat, each with evidence: his quote with its source, a `GROUND.md` fact id, or `file:line`. There is no quota; "Nothing to call out." is a valid result.
7. **Contested rows only:** one short party round, voiced by the challenger alone. A disagreement the facts cannot settle becomes a question for him with both sides stated.
8. **Questions for him.** Only the frontier: the calls whose prerequisites are settled. Each is a proposed decision file under `decisions/proposed/` (`For: him`), in plain words with no code names, recommendation first. At most four, in this order: the core sentence, the budget, any DROP or demotion of one of his asks, contested calls.

**Who decides.** On his items the challenger only recommends. His ask keeps `core` with `Decider: him (proposed: <verdict>, decisions/proposed/<file>)` until the cut (D-L7). On its own proposals it decides, and they are always `later`.

**Light depth.** When `Expand depth: light`, call-outs are optional and the party round is skipped. For a contained bug, the challenge is one paragraph.

**The check, `--stage challenge`:** `CHALLENGE.md` exists; the core sentence is one sentence of at most 25 words and its quote matches the transcript; the budget line has three numbers; every live `S`, `P` and `D` item has exactly one verdict from the vocabulary; every call-out carries evidence. A verdict still marked `proposed` shows as INFO here.

### The cut: his answers to the challenge

The cut is the lead's, at the front desk. It is where he is asked first after expand.

1. Show him the core sentence, the simple sketch and the PR budget in a few plain lines.
2. Ask the challenger's proposed questions, at most four a batch, in its order.
3. Write each answer as `decisions/D<n>-<slug>.md` in his quoted words with their source. In `CHALLENGE.md`, set each verdict he gave with `Decider: him (D<n>)`, and delete each proposed file once its D file exists.
4. For each DROP he agreed, append its `R` row to the program's `REMOVED.md`, marked `no code change`.
5. When an answer opens new questions, a fresh challenger folds the answers in and computes the next frontier. After three batches, the rest go to `WAITING.md` with what can go on without them.
6. Record the gate: `python -m ship gate cut --program <program> --by him --source "<id8>:L<line>"`.

**The check, `--stage cut`,** fails while any verdict still says `proposed`, or any proposed question is left in `decisions/proposed/`.

If grounding showed the area is not fit to build on (nobody can say what it is meant to do, its tests mostly cannot fail, or it disagrees with its own docs), the planner proposes "audit this area first" at the cut. See "Planning and the audit branch" below.

### 3. Self-annealing: remove ambiguity from the plan

Annealing works only on CORE and LATER items. It never touches a DROP.

- **Every plan line carries its ask's verdict:** `- **S2.a** [later] ...`. No plan line marked `core` serves only a `later` ask.
- **A LATER ask gets the light round** (lenses 1 to 4 and 7).
- **Anything new is a proposal.** A proposal raised during annealing gets a row in `CHALLENGE.md` with verdict `later` and `Decider: agent (anneal round <n>)`, until a settled decision of his promotes it.
- **A clarification that picks one reading of his words** (defines his term, sets a default) is marked `(my reading)` in the plan line, so he sees it when he reads plan v1.

Each round runs seven lenses over the plan, against the ground truth:

1. linking logic;
2. attack the premise;
3. contradictions in his words;
4. edge cases;
5. a party-mode debate, in session mode;
6. "deeper, not bigger": anything new is a LATER proposal unless he promotes it;
7. subtract.

Each question is filled from the code, by linking logic, or by a decision. Decisions for him come in batches of at most 4, each with a recommendation.

**Stop rule.** Annealing stops when a round raises no new question and no answer arrived during it. The log says how many rounds it took. After 5 rounds in one mode with no stop line (the count is the index's `self-annealing` loop), the check fails with "round limit: ask him", unless `WAITING.md` lists the open questions under "still open, and what can go on without it".

**Subtract.** `funnel-subtract` justifies each can-change candidate as an `X` row, with `Replaced by:` and `In plain words:`, and records the agreed removals as planned. It states the decider rule: Fable decides a removal that changes nothing he can see or use; he decides one that takes away something he can see, use or was promised, or that touches a fixed line or his data.

**Plan v1.** When annealing stops, the lead shows him `PLAN.md` in plain words: the CORE lines first, then the LATER ones, with the round count and one operations line per ask. In the same batch it asks: "When plan review comes back clean, may the build start without asking you again?" It records `python -m ship gate plan --program <program> --by him --source "<id8>:L<line>"`, with `--advance` only on his yes. **Stage 4 never starts before he has read plan v1.** His changes start another plan round.

### 4. Technical lens: agents write the architecture

`bmad-architecture` runs headless on the annealed plan and reads the anneal log. Matt Pocock's `improve-codebase-architecture` finds deepening opportunities, and the agent picks among them by rubric. pstack's `blast-radius` and principles check the shape. Every element names its plan lines and covers its edge cases. Diagrams are C4 Mermaid. The headless run's assumptions are not settled; stage 5 screens them.

`arch/ARCH.md` must hold two sections, whether he mentioned them or not:

- **`## Operations`:** the operations question answered for every feature.
- **`## Interfaces`:** one row per operation or stream the program adds, changes or removes at the UI's door:

  `- **I<n>** (<plan ids>) <new|changed|removed> <operation id or stream> <method and route> | payload: <fields> | errors: <shape> | used by: <screen or journey, or "no screen yet">`

  The operation id is the one the contract uses. "Used by" comes from `GROUND.md`'s UI asks or `JOURNEYS.md`. When the program touches no route or stream, the section is the single line `Interfaces: none, because <reason>`.

  A `changed` or `removed` row that a screen uses is a one-way door: it gets a `For: him` decision in plain words (what the screen loses or must change), with a recommendation.

The check, `--stage arch`, fails when either section is missing, or a one-way row has no decision.

### 5. Technical self-annealing

`funnel-anneal` runs in technical mode, with the same lenses plus the adversarial, verification-gap, coverage and operations checks, and the same stop rule.

- **Fable proposes.** Every open technical decision goes to one Fable answer-linker, including the headless run's assumptions and any spine decision without a source. It links each to the best answer the earlier stages support.
- **Opus screens.** A fresh Opus agent looks for product calls in technical clothes, and for any touch on a fixed line.
- **The log says who decided.** Cleared answers are logged as "Fable decided X because Y", never as his. Product calls go to him, with Fable's answer as the recommendation.

### 6. Handoff

1. **Re-ground if the tip moved.** If the code under the area changed since grounding, the changed paths are grounded again first.
2. **Slice.** Slices follow the vertical-slice rule, one per piece of behaviour he can see, under a prefix no other program uses (`ship records prefix` checks every source). Each slice has a `kind`: `feature`, `pin`, `refactor`, `remove` or `docs`.
3. **Lay them out for the build.**
   - Group the slices into checkpoints of 5 to 8, each a coherent piece the review can judge against the plan.
   - **Every CORE checkpoint comes before any LATER one.** The last CORE checkpoint's done line (`done_when`) is the core sentence.
   - **LATER checkpoints are written with `handoff: deferred` and no slices.** Their briefs are written only after the last CORE checkpoint merges, on the target tip of that day, by `funnel-handoff --later <stop>` (the `later-handoff` worker).
   - Inside each checkpoint, lay the slices out in lanes that share no files, so builders run at once.
   - Where the plan allows, keep the next checkpoint off the files of the one before, so it can be built during review.
4. **Fit the budget.** Slice counts must fit the PR budget. Over it, the challenger says in one line why it grew, and only his yes raises it, recorded in `budget.raised`.
5. **Write the briefs** from the template, filling every part: a `Chain:` line, `Kind:`, and the whole merge request (plain words, `TRACE:`, door, `DOC:` lines, and `API:`), so builders do no research.
   - `API:` lists the Interfaces rows the slice implements, each as its `I` id and operation id (`API: I1 library.upload; I2 library.list`), or `API: none`.
   - Every `I` row of a core ask is in exactly one brief's `API:` line, and every id in an `API:` line is an `I` row. The kit's contract check later compares this line with the operations the slice really changed.
6. **Generate the chain packets.** `chain_packet.py` writes each slice's `CHAIN.md`, including the Interfaces rows its `API:` line names. Never edit a packet by hand.
7. **Write `PROGRAM.yaml`** (version 2) from the template: `project`, `program`, `kind`, `area`, `inputs`, `build_branch`, `parent_tip`, `core_sentence`, `budget`, `gates`, `stop_points` (each with `tier` and `handoff`) and one `chains:` row per ask. A version-1 file fails at handoff, so a queued plan is moved to version 2 before it can build (D-L7).
8. **Check.** `--stage handoff` and `check_plan.py` must pass. The handoff check is the strict one on the budget and on CORE before LATER: no slice in a core checkpoint serves a later or dropped ask, a dropped ask has no slice, and every `X` row has its two new fields.

Then plan review runs: its four readers, his questions and the Proposals pick list, and the "go" gate. If he gave "go" in advance at plan v1 and the review is clean, within budget and has no question, the build starts without asking him again.

**Built today:** at the end of planning, `plan-feature` hands the program to the conveyor (`ship chain`). Plan review runs as the `plan-review` worker, and its one round trip of fixes goes through the `planner-fix` worker.

## Planning and the audit branch

Planning adds features. Auditing improves or removes what exists. Both feed the same review, build, checkpoint review and merge. They meet in four places (design section 3.3):

| Crossing | When | How the context travels | His part |
|---|---|---|---|
| Audit to plan | An audit finding is design-level, or a feature is missing | A backlog row of source `handoff`, door `design`, pointing at the audit folder. Planning starts with `inputs.audit: <folder>`; expand reads `INTENT.md`, `AUDIT.md`, the finding ids and his approval quote; ground starts from the audit's facts | His yes to start it, because it is new scope |
| Plan to audit | Grounding shows the area is not fit to build on | The planner proposes "audit this area first" at the cut. A scoped audit (`audit-area --scope <paths> --for <program>`) runs census to judgement on just those paths, and its `INTENT.md` and `AUDIT.md` join the program's ground | His yes at the cut |
| LATER to later checkpoints | The last CORE checkpoint has merged and proved the core sentence | LATER asks already carry verdicts and plan lines; their briefs are written then, on the new tip. LATER items no checkpoint holds go to the backlog | None, inside the LATER budget he agreed |
| Review to planner | A builder or reader says the plan itself is wrong (`BLOCKED chain`) | `notes/CHAIN-ISSUES.md`, shown in the checkpoint's map. Briefs never change mid-run: a mechanical one goes into the fix batch as a slice that cites the chain id; a product call waits on him | Only product calls |

A row that has crossed once and wants to cross back goes to him, so the two branches cannot bounce work between them.

**Shared parts.** The audit runs the same challenge (`funnel-challenge` in audit mode, inside its judgement), where a restructure or a decoupling is CORE only with a measure. It removes code with the same `funnel-subtract` (`--scope area`), the same `X` row, the same decider rule and the same `REMOVED.md` ledger. Its contained rows go through this funnel's light path (lenses 1 to 4 and 7, an element index, handoff). How the audit itself runs is in `SHIPPING-METHOD.md`.

## When things change or break

**He changes his mind.** His new words go into `SCOPE.md` first, and the expand check runs again. Then:

- **Ids.** An id whose meaning changed is retired (`~~S1.b~~ retired <date>: <why>`), never reused. The new meaning gets a new id.
- **Rerun.** Rerun from the earliest stage whose input changed:
  - ground a new area;
  - a change after the cut goes back through the challenge for the items it touches;
  - run a plan round on the changed lines, and show him those lines;
  - run the architect on the elements that cite changed ids;
  - run a technical round.
- **Plan review and proposals.** Plan review sends his answers back through the same route. A Proposal he picks becomes a new ask and travels the same route, through the challenge.

**A crash or compaction mid-stage.** He says "continue planning", and `plan-feature` resumes the same program.

1. Run `python D:/factory/skills/factory-core/scripts/resume.py <program>`. It prints `stage:` (the first stage whose check fails; resume there), `leftover:` (a round file that did not finish; delete it and rerun the round), `ask:` (each open question for him), and `ask: list` when more are open than three batches hold.
2. Put the open questions to him again as one batch, or, after three batches, list the rest in `WAITING.md`.

**He is away.** The planner writes the waiting batch to `WAITING.md` with the stage to resume at, sets the phase to `waits`, and ends its turn. Work that does not depend on his answers may go on first. Stage 4 never starts before he has read plan v1.

**A tiny ask** (light depth) runs only:

- a challenge with no call-outs and no party round;
- one plan round of lenses 1 to 4 and 7;
- an element index, with `## Operations` and `## Interfaces`;
- a technical round only if a technical decision exists.

**A huge ask** is split into programs, on his yes. The resume rule above carries one session's work into the next.

## The program folder at handoff

```
D:/QMX-worktrees/plans/<slug>/
  PROGRAM.yaml        index v2: project, kind, area, inputs, core sentence, budget, gates, stop points, chains
  phase.json          the current stage, written only by ship phase --set
  SCOPE.md            his words and asks, destination, decisions, proposals, not yet specified, out of scope
  GROUND.md           facts at the tip, open items, in-flight branches, fixed lines, removed rows, doc drift, UI surface today
  CHALLENGE.md        core sentence, premise, simple sketch, PR budget, verdicts, call-outs
  challenge/          scores.md, voices.md, debate.md
  PLAN.md             annealed plan lines S1.a..., each with its verdict
  ANNEAL-LOG.md       every question, what filled it, who answered (both modes)
  EDGE-CASES.md       E rows: scenario and what must hold
  CAN-CHANGE.md       X rows, each with Replaced by and a plain-words line
  REMOVED.md          planned removals R-<program>-n
  decisions/          D files: question, recommendation, why, answer; proposed/ until the lead settles them
  WAITING.md          questions for him while a gate is open
  arch/               ARCH.md (with Operations and Interfaces), ARCHITECTURE-SPINE.md, DEEPENING.md, HEADLESS.json, diagrams
  expand/ subtract/   research notes and tool output
  SLICES.md           slices with ask, stop (checkpoint), lane and kind
  slices/<id>/        BRIEF.md (with its merge request and API: line), CHAIN.md (generated packet)
  checks.toml
```

The folder lives in the plans worktree (branch `plans`), outside the main checkout, and is committed and pushed at every phase end. Planning writes nothing in the main checkout.
