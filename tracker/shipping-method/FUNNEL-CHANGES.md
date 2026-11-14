# Planning funnel: what changed (12 November 2026)

For him to skim. Under his standing rule, any skill may be rewritten or combined if it serves better; this note is the alert for each change. No existing skill was edited or overwritten, nothing is committed, and `CLAUDE.md` is untouched.

## Skills created (in `C:/Users/Mubarak/Desktop/QMX/.claude/skills/`)

| Skill | Stage | What it does | Built from, and why a new one |
|---|---|---|---|
| `funnel-expand` | 1 | Picks the depth (light, medium or deep), restates the ask, gathers context, and writes `SCOPE.md`. His asks are kept few, in his words, and checked against the transcript line each one cites | pstack's `in-your-own-words` (one line, folded in), `grilling` and the research skills. Nothing existing wrote his asks in the shape the ship scripts read |
| `funnel-ground` | 2 | Reads the area's code at the tip, its PR history, `OPEN:` lines and in-flight branches, the fixed lines it touches, the removed lists, and the docs as claims. Writes `GROUND.md` as facts the ship kit reruns | pstack's `how`, `why` and `blast-radius`, plus PR-history reading. Nothing existing read PR history or wrote facts in brief form |
| `funnel-anneal` | 3 and 5 | Removes ambiguity in rounds until a round raises no new question, and logs every question, what filled it and who answered | Combines grilling's stop rule, the hillclimb loop, linking logic (new, his idea), attack-the-premise, the bmad-review edge-case lens, party mode (session mode), pstack's `sharpen` questions (folded in), and the Fable answer-linker with an Opus screen. Every existing piece was either human-driven or ran once |
| `funnel-subtract` | 3 | Justified can-change candidates, and planned removals that later move to `tracker/REMOVED.md` so they are not rebuilt | pstack's `principle-subtract-before-you-add` as a procedure, with the deletion test, migrate-callers-then-delete and the dead-code tools. The justification and the removed list are his additions |
| `funnel-architect` | 4 | Runs `bmad-architecture` headless on the annealed plan and its log, picks deepening opportunities by rubric, and writes an element index tied to plan lines and edge cases, plus the operations layer | Wraps `bmad-architecture`, Matt Pocock's `improve-codebase-architecture` (the agent picks by rubric where it would ask the user) and `blast-radius`. Edits none |
| `funnel-handoff` | 6 | Slices by the vertical-slice rule; writes briefs, `SLICES.md`, `checks.toml` and `PROGRAM.yaml` with chains; runs both checks | Matt Pocock's `to-tickets` rule (its "quiz the user" is replaced by the checks and a fresh reader), plus the standing templates |

## Other files

| File | What |
|---|---|
| `tracker/shipping-method/PLANNING-FUNNEL.md` | The final method. Replaces the proposal and the skill plan, which stay as history |
| `standing/prompts/PLAN.md` | The paste prompt that starts, or resumes, a planning session for the whole funnel |
| `standing/funnel/CHAIN.md` | The ids and file shapes all six skills share |
| `standing/funnel/check_chain.py` | Proves the chain after each stage, and reads who decided what as data. `--rerun-facts` reruns grounding facts with the ship kit's runner |
| `standing/funnel/his_words.py` | Finds his own words in transcripts, including his answers to questions. Skips summaries, tool output and relayed messages, and gives each quote a citable source |
| `standing/funnel/tests/` | 16 fixtures and a runner that prove the checker (16 of 16 pass) |
| `standing/PREFIXES.md` | Register of slice prefixes, so two programs never collide |
| `tracker/REMOVED.md` | Project-wide "removed, and why" list, for merged removals only |

## Decided for him (he handed these over)

- **Removed lists:** planned removals live in each program; they move to `tracker/REMOVED.md` when their stop point merges. Rows he decided bind everyone; rows an agent decided bind agents.
- **Expand depth:** the planner picks it and says why; he can override it.
- **Ask ids:** his asks are `S1`, `S2`, the ids the ship scripts and plan review already read. There is no separate map file.
- **Where the architecture lives:** in the program folder, under `arch/`. Docs catch up after merges.
- **When Fable is unavailable,** Opus stands in, and the log says so.
- **Question batches** hold at most 4, the question tool's limit.

## Stress test of the funnel (one Opus agent, edge-case, adversarial and CIS lenses)

It found 5 blockers, 17 shoulds and 9 nits, with test fixtures to prove them. All blockers and shoulds inside the funnel's own files are fixed. The 16 fixtures became the checker's regression test.

| # | Finding | Fix |
|---|---|---|
| 1 | Decisions made in the headless architecture run skipped the product-call screen | Its assumptions and open questions become decisions, and the Opus screen reads the spine and the element index |
| 2 | A later quote with "now" or "actually" counted as settling his earlier words: "dissolved" under a new name | A later reading is only a recommendation, put to him to confirm, and the checker demands it |
| 3 | No resume after a crash or compaction; a lost question batch was never asked again | Resume rules in the prompt; rounds are written to a file first; open questions to him are asked again |
| 4 | Open Fable decisions reached the handoff, with no fallback when Fable is unavailable | Fable runs first in every technical round, Opus stands in when needed, and an open Fable decision fails from stage 5 on |
| 5 | The checker could not see the three past failures | Who decided is now checked as data: "dissolved" fails, his answers must quote him with a source, and every plan line, element and edge case must reach a brief |
| 6-9 | Re-anneal numbering; a stage-4 deadlock; regex misses and crashes | Global round numbers with mode-named stop lines; a separate `technical` stage; the ship kit's own parsers |
| 11-12 | His question answers were invisible, and agent notes passed as his words | `his_words.py` reads his answers; asks need his words, checked against the transcript line cited |
| 13 | Removed list unversioned and written too early, in the main checkout | Planned in the program, moved on merge, agent rows bind only agents |
| 14-17 | Routes for scope to grow; tiny asks paying full ceremony; huge asks; his absence | "Clarify, never add"; a growth line he sees; a light path; a split proposal; `WAITING.md` |
| 18-22 | Stale ground truth, money and exits, prefix clashes, stage 6 folding his calls | Fetch must succeed and the tip is rechecked at handoff; fixed lines get an edge case, a safety fact and a screen; a prefix register; reader findings become his decisions |

## Operations layer (his addition)

Every feature gets logging, observability, monitoring, self-recovery and backend operations, whether or not he mentions them. It is a standing question in stage 4, a required `## Operations` section in the architecture (checked), and an `Operations:` line in every brief's done line (checked). It builds on the node's journals and the fleet watch.

## Dry run: "Which pod rules should a scalping pod carry?"

- **Stage 1, expand.** The first run produced 9 asks from a one-line question: the old widening. After the fix, it produced 3, with the rest sorted into decisions, out of scope and proposals. It also caught a quote that had come from a paste, not from him. Two contradictions became decisions for him, each with a recommendation.
- **Stage 2, ground.** 32 facts at the `engine/base` tip, all rerun cleanly through the ship kit's runner. It found that every brake shipped today closes trades, against his ruling. It also found that the unit's logic/risk split (rc-03) is not merged yet, so `POD-DEFINITION.md` overstates what exists.
- **Stage 3, self-annealing and subtract.** Four rounds raised 27, 5, 1 and then 0 new questions, and annealing stopped by its rule.
  - **Scope:** the 3 asks stayed 3 plan lines. The agent's own ideas became 7 proposals, all parked for his pick.
  - **Records:** 16 edge cases, four of them guarding fixed lines; 4 justified can-change rows; 1 planned removal.
  - **His decisions:** five wait for him in `WAITING.md`, each with a recommendation. Three are new: whether to keep the sweep cap, whether the breaker stops trades or moves the unit to demo, and changing today's brakes so they stop rather than close. One technical decision waits for stage 5.
  - **Nothing settled without him;** the checker passes.
  - **Skill friction fixed:**
    - each lens must say what it checked before "none" counts toward the stop rule;
    - a plan line that picks one reading of his words is marked "my reading" for plan v1;
    - a must-hold that decides behaviour he would notice goes to him;
    - the lead batches every decision for him;
    - subtract sends anything touching fixed lines or rulings to him.
- **Where the outputs are:** `D:/QMX-worktrees/funnel-dry-run/pod-scalping/`, outside the repo, with the first stage-1 run kept beside it as `pod-scalping-v1` for comparison. The pod design session can reuse its `GROUND.md` and `WAITING.md`.
- **Not run:** stages 4 to 6 (architecture, technical annealing, handoff), as asked. Their skills are written, and the checker's later stages are proven only on the 16 fixtures.

## The five phases now chain themselves (his ruling, 12 November)

He never pastes a prompt at any phase. Each phase has a project skill that fills its prompt from the program folder, and each phase starts the next session itself.

**Skills created** (in `QMX/.claude/skills/`, beside the existing `plan-feature`):

| Skill | He can say | Fills | Why |
|---|---|---|---|
| `plan-review` | "review the plan for X" | `PLAN-REVIEW.md` | So plan review starts without a paste |
| `ship-build` | "start building X", "continue the run" | `COORDINATOR.md` | The same for the coordinator. It moves itself into the program folder, where the ship hook loads |
| `stop-review` | "review stop A of X" | `STOP-REVIEW.md` | Round 1 or round 2, worked out from disk |
| `ship-merge` | "merge stop A of X" | `MERGE.md` | It also takes his word when a merge waits for him |
| `ship-next` | "continue", "what's next" | the right phase skill | One phrase that always works |

**Other files:**

- `standing/prompts/NEXT-PHASE.md` (new) is the one procedure every phase uses to start the next session:
  - the skill and its folder;
  - a brief that names the skill file by its full path, because sessions outside the repo don't see project skills;
  - a line in `notes/SESSIONS.md`.

  When the app can't or won't start a session, as on the coordinator's automated heartbeat turns, it proposes a one-click card and gives him one plain sentence to say. Never a prompt to paste.
- `standing/phase_state.py` (new) reads a program folder and says which phase is next, with the stop, round, commits and fix program the prompt needs. Tested through one whole stop: build, review, a blocked review, the fix program, round 2, merge, and the next stop.
- The other prompts and files changed:
  - `PLAN.md`: ends by setting `planner_session` and starting plan review, instead of giving him a paste line.
  - `PLAN-REVIEW.md`, `COORDINATOR.md`, `STOP-REVIEW.md`, `MERGE.md`: each says which skill fills it, and starts the next phase through `NEXT-PHASE.md`.
  - `RULES-CARD.md`: the coordinator's handover uses the same route.
  - `standing/README.md`: lists the new files.
  - `PLANNING-FUNNEL.md` and `funnel-handoff`: no paste lines remain.

**CLAUDE.md: drafted, not applied.** This session does not edit CLAUDE.md at another session's request. Lines for the shipping section, to apply by hand or from the coordinating session:

- Replace "It then gives the operator a short paste prompt in chat that points at `PROGRAM.md`." with: "It then starts plan review itself. Every phase starts the next session itself (`tracker/shipping-method/standing/prompts/NEXT-PHASE.md`); he never pastes a prompt. When he names a phase in plain words, use its skill: `plan-review` ("review the plan"), `ship-build` ("start building", "continue the run"), `stop-review` ("review stop A"), `ship-merge` ("merge stop A"), or `ship-next` ("continue", "what's next")."
- In the same bullet, `PROGRAM.md` is now `PROGRAM.yaml`, the program's one index.

## Planning feeds the redesigned build (12 November, late)

The build now has no reviewer per slice. Review runs at checkpoints every 5 to 8 slices, and builders pre-build one checkpoint ahead in lanes that don't overlap (`BUILD-PHASE-REDESIGN.md`). Planning changed to feed that:

- **Checkpoints.** The `stop` column is the checkpoint, because the redesign defines a checkpoint as a stop point. No second column, so the two can never disagree, and `check_plan.py` and the coordinator keep reading `stop`. The handoff aims for 5 to 8 slices per checkpoint, each a coherent piece the review can judge against the plan. Both checkers warn above 8; neither refuses.
- **Lanes.** A new `lane` column says who does what.
  - `check_chain.py` fails on any two lanes of one checkpoint that share a file, using the ship kit's own overlap rule.
  - It warns on a dependency across lanes.
  - It prints how many of the next checkpoint's slices can be built during review.
  - The ship kit's `parse_slices` finds columns by name, so extra columns are ignored. Tested on the new template: `ship init` reads it unchanged.
- **Slice-count discipline.** The setting `SLICES_PER_ASK_WARN = 4` sits in `check_chain.py`, labelled as a setting. Past it, `SLICES.md` needs a `Growth:` line saying why, or the check fails. It is not a cap: any count passes once the reason is written.
- **Briefs carry the merge request.** `templates/BRIEF.md` gains:
  - the `Lane:` and `Chain:` lines;
  - removed rows under "Never rebuild" in part 7;
  - part 7a lines that start with their `E` id and name a test;
  - an operations line that names its test;
  - a new part 11, "Merge request": title, plain words, `TRACE: <slice> -> <plan ids> -> <ask>`, the door call, the `DOC:` lines and the known open items.

  The builder adds only its summary and evidence. `check_chain.py` checks part 11 against the chain.
- **Chain packet** (`standing/funnel/chain_packet.py`, new). It generates `slices/<id>/CHAIN.md`, holding only what that slice needs:
  - his ask, the plan lines, the elements and their operations, and the edge cases;
  - the can-change rows it carries out;
  - the removed rows, fixed lines and facts on its files;
  - its neighbours.
- **Handoff.** It drops its own fresh brief reader, which plan review's grounding agent duplicates.
- **Plan review.** It now also runs `check_chain.py --stage handoff`. Its PR-plan reviewer judges the checkpoints, the lanes, how much can be pre-built, the slice count and each part 11.
- **`check_plan.py`** fixes:
  - Fact blocks are stripped before the placeholder scan, so real output like Svelte markup no longer fails a UI slice.
  - A checkpoint over 8 slices gets a WARN.
- **Tests.** Four new fixtures, for lanes sharing a file, growth with and without a reason, and a wrong trace line. 20 of 20 pass.

## Not done, for the coordinating session

- **Upstream pstack skills** (`statechart`, `ketchup`): not downloaded. `in-your-own-words` and `sharpen` are folded into the funnel skills in our own words.
- **`check_plan.py`** flags real fact output that contains `<...>` (for example Svelte markup), so every UI slice will fail it. Fix: strip fact blocks before the placeholder scan.
- **`PLAN-REVIEW.md`** should also run `check_chain.py --stage handoff`, and send his changes back through the planner's change route.
- **Merge step:** `MERGE.md` should move the program's planned removal rows to `tracker/REMOVED.md`.
- **PR body v2:** add a `TRACE:` line (slice id and ask), the last link of the chain.
- **`SHIPPING-METHOD.md`** still names `PROGRAM.md`, `PROPOSALS.md` and `arch/final/SPINE.md`.
- **`standing/README.md`** should list `prompts/PLAN.md`, `funnel/` and `PREFIXES.md`.
- **The docs step** (applying `DOC:` lines after each merge, plus a backfill) is designed in `FUNNEL-SKILL-PLAN.md` section 4, not built.
- **His Fable ruling** for this funnel's answer-linker belongs in `CLAUDE.md`, which I did not touch.
