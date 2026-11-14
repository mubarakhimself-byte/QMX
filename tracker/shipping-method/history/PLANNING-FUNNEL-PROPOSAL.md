# Planning funnel: proposal for his approval (revision 4, 12 November 2026)

> Superseded on 12 November by `PLANNING-FUNNEL.md`, the final method. Kept as history.

Status: proposal. Revision 4 folds in his answers of 12 November. It ends in the program folder that `SHIPPING-METHOD.md` describes. It is written for QMX. Only the house rules and the docs are QMX-specific, so the same funnel can later serve any project. The skills it needs are in `FUNNEL-SKILL-PLAN.md`.

## What planning is for: context engineering

Planning exists to remove ambiguity. The target is work so clear that even an old model can build it without breaking a sweat.

- **A question means context is missing.** Each question that comes up is a gap to fill, not a test the idea failed.
- **Stress-testing adds context.** It is not a filter that ideas must survive. Its job is to find what is still ambiguous and make it concrete.
- **Each stage hands richer context to the next.** Nothing is thrown away; later stages read the earlier ones, including *how* ambiguity was removed, not only the conclusions.

## The graph: one chain per feature

Every feature gets a chain of levels. `PROGRAM.yaml` links them, so a builder can walk from its slice back to the reasoning behind it, and a reviewer can walk the other way.

| Level | What it is | Lives in |
|---|---|---|
| L0 | His words, raw | `MAP.md`, quoted with where he said them |
| L1 | Core thing (C1, C2...) | `MAP.md` |
| L2 | Annealed plan line | `PLAN.md`, with its trail in `ANNEAL-LOG.md` |
| L3 | Architecture element | `docs/` (pointed at), with its trail in the technical `ANNEAL-LOG.md` |
| L4 | Slice brief | `slices/<id>/BRIEF.md` |
| L5 | Code | the PR, whose body names its slice |

Each feature has a row in `PROGRAM.yaml` listing its ids at every level, for example `C2 -> P2.1 -> ARCH-UNIT-04 -> rc-31 -> PR #812`.

## Rules at every stage

- **Contradictions and ambiguity go to him, with the agent's recommendation.** Agents are often right. The failure in the risk session was folding things he never saw. So each item that reaches him carries the agent's best proposal and the reason for it. No agent settles one silently, and nothing is marked "dissolved".
- **Agents' own ideas are welcome, as proposals.** An idea becomes plan only through his core things or his yes.
- **Agents:** every agent is Claude Opus 5.5, except the Fable answer-linker in stage 5, which he asked for. No subagent spawns its own subagents: skills that fan out are fanned out by the lead session and run one step after another inside an agent.

## The stages

| # | Stage | Hands on | His part |
|---|---|---|---|
| 1 | Expand | Core things, in his words | Brings information in; confirms the core things |
| 2 | Ground | Ground truth from the code | None |
| 3 | Self-annealing | Plan v1, its anneal log, edge cases, the can-change list, an architecture proposal | Answers contradictions and ambiguities (with recommendations); **reads plan v1** |
| 4 | Technical lens | Architecture, high and low level, with diagrams | None |
| 5 | Technical self-annealing | Settled architecture and its technical anneal log | Only non-technical items, with recommendations |
| 6 | Handoff | `PROGRAM.yaml`, map, slices, briefs | Gets the paste prompt |

### 1. Expand: as deep as the feature needs

Expand is circumstantial. Its depth depends on the feature, and the planner states the depth it picked and why.

| Depth | When | What runs |
|---|---|---|
| Light | The ask is clear and builds on something that exists | Restate his words, confirm the core things |
| Medium | Clear ask, unfamiliar parts | Plus targeted research on those parts |
| Deep | A new domain, like QMX's risk work | Plus his brain dump, papers (alphaXiv), inspiration from the web and browser, research agents |

- Output: a few core things (C1, C2...), each quoting his words. He confirms the list.
- Skills: `in-your-own-words` (upstream pstack, approved), `bro`, `research`, `bmad-domain-research`, `bmad-technical-research`, `grilling`, `domain-modeling`.

### 2. Ground: what is really there

- Reads the code of the area directly, with its PR history, the `OPEN:` lines of its PRs, and the program's past "removed, and why" lists. Docs count only where they match the code. Grounding does not wait for a docs refresh; docs catch up after each merge in a separate factory step.
- Each fact is one command plus its expected output, the form briefs need.
- Skill: `ground-area` (new). No stress test starts until grounding has finished.

### 3. Self-annealing: remove ambiguity from the plan

Rounds of stress tests on the core things against the ground truth. Each finding is missing context, and the round fills it. **Stop rule:** it stops when a round produces no new question. This is a stop rule, not a cap; the output says how many rounds it took.

**Linking logic is a named technique here,** in two forms:

- **By analogy:** "self-configuring units" is vague; "self-configuring like Kubernetes" is clear, because the analogy brings a known model with it.
- **By reference:** tie the rough idea to something concrete that exists: a module in the code, a paper, a ruling, another product.

Each round produces:

| Output | What happens to it |
|---|---|
| **Questions** | Facts are looked up, never asked. Non-technical items go to him, at most 5 a round, each with a recommendation and its reason. Technical ones wait for stage 5. |
| **Edge cases** | Written to `EDGE-CASES.md`. Architecture, review and each slice's tests must cover them. |
| **Can-change list** | Code that could be deleted or changed, each with its justification and evidence. Deletions he would see in the app need his yes; agents decide the rest. |
| **The anneal log** | `ANNEAL-LOG.md`: each round's questions, the context that answered them, and who answered (him or an agent). Later stages read it. |

At the end: **plan v1** (one page, plain words: what will be true when each core thing is done) and a separate **architecture proposal** from the party-mode debate. **He reads plan v1 before the technical lens starts.** Party mode ends here. Winston, BMad's architect, speaks only as a persona inside it, so his proposal is input to stage 4, not the architecture.

**Removed, and why.** Every deletion or change that is agreed goes into `REMOVED.md` with its reason. Later loops and later programs read it, so nothing deliberately removed gets rebuilt. That is YAGNI, kept on disk.

- Skills: `self-anneal` (new, plan mode), `can-change-scan` (new, built on pstack's subtract-before-you-add), with party mode, CIS, forge-idea and the `bmad-review` edge-case lens inside it.

### 4. Technical lens: agents write the architecture

- `bmad-architecture`, run directly, writes the high- and low-level architecture: the design and who does what. C4 Mermaid diagrams follow `documentation-factory`'s conventions.
- **It reads the anneal log, not only plan v1,** so it knows which ambiguities were removed and how.
- Every architecture element names the plan line it serves.
- Skills: `bmad-architecture`, `improve-codebase-architecture`, `codebase-design`, pstack `architect` and `blast-radius`, through pstack's principles.

### 5. Technical self-annealing: remove ambiguity from the architecture

- `self-anneal` in technical mode, with the same stop rule. Every edge case must be covered.
- Technical questions go to a Fable answer-linker, which proposes the best answer from the earlier stages' files. **A fresh Opus agent checks those answers for hidden product calls** before they are logged. Hidden product calls go to him with a recommendation.
- The rest are logged in `ANNEAL-LOG.md` as "Fable decided X because Y". None is presented as his.

### 6. Handoff: the index

- Slice with `to-tickets`' rule: one slice per piece of behaviour he can see. Briefs follow the shipping method's 10-part form. Each brief names its chain: core thing, plan line, architecture element, edge cases.
- Write `PROGRAM.yaml`: which file serves which agent, and one row per feature linking its levels.
- Check: a script fails any slice with a broken chain or any edge case no slice covers; a fresh Opus reader reads each brief against the code it names; one fix round.
- Give him the short paste prompt, pointing at `PROGRAM.yaml`.

**The program folder:** `PROGRAM.yaml`, `MAP.md`, `PLAN.md`, `ANNEAL-LOG.md` (both modes), `EDGE-CASES.md`, `REMOVED.md`, `SLICES.md` and `slices/<id>/BRIEF.md`. The architecture lives in `docs/`, and the standing `PROJECT-RULES.md` and `RULES-CARD.md` are pointed at.

## Settled by his answers (12 November)

1. He reads plan v1 before the technical lens.
2. Each deletion or change is justified, and `REMOVED.md` keeps them so later loops don't rebuild them.
3. Opus checks Fable's technical answers for hidden product calls before they are logged.
4. The four upstream pstack skills are approved for install (not installed yet).

## Questions for him

1. **Expand depth.** The planner picks light, medium or deep and says why in its first message, and you can override. Recommended: yes.
2. **Where "removed, and why" lives.** One list per program, or one project-wide list that every program adds to? Recommended: project-wide, so a later program sees what an earlier one removed.
3. **The last link of the chain.** PR body v2 gains a `TRACE:` line naming the slice and core thing, so code links back to its plan. Recommended: yes.
