# Standing files for the shipping method

The files every QMX program shares, and the prompts for the sessions and agents of `../SHIPPING-METHOD.md`. They match the ship scripts in `D:/QMX-worktrees/ship-kit/tools/ship` (branch `ship/kit`) and its `README.md`. Where the method and the scripts differ, these files follow the scripts.

## Who reads what

| File | Used by | For |
|---|---|---|
| `PROJECT-RULES.md` | builders, checkpoint readers, grounding agents | House rules, his rulings, the fixed lines, the QMX traps, environment and safety |
| `REVIEW.md` | the checkpoint review and its readers | What failure looks like, the blockers and the severity rule, the fault kinds, the tags, the verdict format |
| `skills/slice-review/` | every checkpoint reader | The reading method: passes over an element's slices and seams, proof or drop, triage. Draft, not installed. `check_verdict.py` and `references/later-rounds.md` serve only the old per-slice verdict mode (`slice_verdict_required`) |
| `RULES-CARD.md` | coordinator, every wake | What it does and never does, which script for which result, pre-building, the checkpoint hand-off, restart, hand over |
| `check_plan.py` | plan review | Parses a program with the ship parser and checks asks, stop points, facts and placeholders |
| `phase_state.py` | the phase skills, `ship-next` | Says which phase a program is in, with the stop, round and commits the next prompt needs |
| `funnel/` | planner, plan review | `CHAIN.md` (ids and shapes), `check_chain.py`, `chain_packet.py` (each slice's `CHAIN.md`), `his_words.py`, and their tests |
| `PREFIXES.md` | planner | Slice prefixes in use |
| `templates/` | planner | `PROGRAM.yaml`, `SCOPE.md`, `SLICES.md` (with `ask`, `stop` and `lane`), `BRIEF.md` (with the merge request in section 11), `checks.toml` |
| `prompts/NEXT-PHASE.md` | every phase session | How a phase starts the next session itself (skill, folder, record, the one-sentence fallback). He never pastes a prompt |
| `prompts/PLAN.md` | session 1, filled by `plan-feature` | Runs the planning funnel (`../PLANNING-FUNNEL.md`) and starts plan review |
| `prompts/PLAN-REVIEW.md` | session 2, filled by `plan-review` | Reviews the plan, one round trip with the planner, his questions, the scope gate |
| `prompts/GROUNDING.md` | agent, from plan review; from the coordinator only when the code moved since | Briefs against the code |
| `prompts/COORDINATOR.md` | session 3, filled by `ship-build` | Arms the run, then builds checkpoint after checkpoint, pre-building the next during each review |
| `prompts/BUILDER.md` | agent, from the coordinator | Builds one slice: first attempt, fix round after a red check, or restart. Writes its own PR body with the `TRACE:` line |
| `prompts/STOP-REVIEW.md` | session 4, filled by `stop-review`, started by the coordinator | Reviews a checkpoint as a whole (deep run, map, readers, one verdict, one fix batch), then merges it |
| `prompts/MERGE.md` | filled by `ship-merge`, only when he asks | Runs STOP-REVIEW's Merge section after a merge that did not finish |
| `prompts/REVIEWER.md` | nobody, unless `slice_verdict_required` is turned on | The retired per-slice reviewer |

## The order

Each phase starts the next session itself (`prompts/NEXT-PHASE.md`), and each phase has a project skill that fills its prompt from the program folder: `plan-feature`, `plan-review`, `ship-build`, `stop-review`, and `ship-next` for "continue". `ship-merge` is a manual entry only. He never pastes a prompt.

1. **Plan.** The planner writes the program folder from `templates/` and starts plan review.
2. **Plan review.** It checks the plan and the briefs against the code, makes one round trip with the planner, asks him the open questions, and starts the coordinator on his go.
3. **Build.** The coordinator arms, restarts itself so the ship hook loads, and builds the first checkpoint. Builders and scripts only: no reviewer per slice. When a checkpoint is built, it starts that checkpoint's review and keeps pre-building the next checkpoint on files the review cannot touch.
4. **Checkpoint review, then merge.** The review runs the deep run (the whole suite on Windows plus the quality tools), its readers, and one verdict. Blocked: one fix batch as a fix program, whose coordinator starts round 2. Clean: the same session merges into `engine/base`, records `ship merged <X>`, and starts a coordinator only if none is running.

Every role is Claude Opus 5.5 in Claude Code. Builders, readers and grounding agents are background agents and spawn none of their own.
