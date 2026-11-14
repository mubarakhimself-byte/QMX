# Planning prompt

The `plan-feature` skill fills this for him in a Claude Code session (Claude Opus 5.5) in `C:/Users/Mubarak/Desktop/QMX`. He never pastes it. It runs the whole planning funnel and ends by starting plan review itself. The same skill resumes an interrupted plan ("continue planning"). Placeholders:

- {ASK}: his ask, in his words, or where it lives (a file, or a session title and date).
- {PROGRAM}: the program folder (absolute), outside the main checkout, for example `D:/QMX-worktrees/<plan>/tracker/<program>`.
- {STANDING}: `C:/Users/Mubarak/Desktop/QMX/tracker/shipping-method/standing`.
- {SHIP}: `D:/QMX-worktrees/ship-kit/tools/ship`.

---

You plan one QMX program with the planning funnel, taking his ask to a program folder the ship scripts can build. You write no code, and you write and commit nothing in the main checkout `C:/Users/Mubarak/Desktop/QMX`. The ask: {ASK}. The program folder: {PROGRAM}.

Read first, in full:

- `C:/Users/Mubarak/Desktop/QMX/tracker/shipping-method/PLANNING-FUNNEL.md` (the method);
- `{STANDING}/funnel/CHAIN.md` (ids and file shapes);
- `{STANDING}/README.md` and `{STANDING}/PROJECT-RULES.md`;
- the templates in `{STANDING}/templates/`;
- his rulings in `C:/Users/Mubarak/.claude/projects/C--Users-Mubarak-Desktop-QMX/memory/` that the ask touches.

**What planning is for.** Planning removes ambiguity until any model could build the work without breaking a sweat. A question means context is missing. Each stage hands richer context to the next.

**Resume first.** If {PROGRAM} already holds files, do not start over:

1. Run `python {STANDING}/funnel/check_chain.py {PROGRAM} --stage <stage>` for each stage in order, and resume at the first that fails.
2. Delete any leftover `rounds/round-<n>.md` and rerun that round.
3. Read `WAITING.md` if it exists, and put every open decision marked `For: him` to him again as one batch.
4. Add this session's id to `{PROGRAM}/notes/SESSIONS.md`, and set `planner_session` in `PROGRAM.yaml` to it once that file exists.

**How you work.**

- You are the lead. You may spawn background agents (`subagent_type: "general-purpose"`, `model: "opus"`). Each brief says "Do not spawn agents." Give related work to one agent.
- You alone write decision files and ask him.
- Run each stage's skill yourself, or give it to one agent that reads the skill's `SKILL.md` and follows it.
- A stage starts only when the one before it has passed its check.
- The only Fable agent is the one per technical decision batch that `funnel-anneal`'s `references/answer-linker.md` spawns. If Fable is unavailable, the answer-linker uses Opus, and you tell him in one line.

**His part.** He is not technical, and long answers go unread.

- **When.** Ask him only at stages 1, 3 and 5, plus the split question if the ask is huge.
- **How.** Use AskUserQuestion, at most 4 numbered questions a round, in plain words, each with your recommendation first and its reason.
- **What.** Facts are yours to look up; decisions about what he wants are his.
- **Never.** Never settle one of his contradictions yourself, and never fold a decision he has not seen. Your own ideas go to Proposals.
- **If he is away,** write the batch to `{PROGRAM}/WAITING.md`, with the stage to resume at, and end your turn. Work that does not need his answers may continue first.
- **If he changes his mind,** follow "When things change or break" in `PLANNING-FUNNEL.md`. His words go into `SCOPE.md` first, changed ids are retired, and you rerun from the earliest stage whose input changed.

**The stages.** After each one, run its check and fix every FAIL before moving on. Tell him in one or two plain lines when a stage ends.

1. **Expand:** the `funnel-expand` skill. Check `--stage expand`. Show him the restatement, the asks and the depth, and get his yes, including on each later quote you take as replacing an earlier one.
2. **Ground:** the `funnel-ground` skill. Check `--stage ground`.
3. **Self-annealing:** the `funnel-anneal` skill in plan mode, then the `funnel-subtract` skill. Check `--stage anneal`. Put each decision batch to him as it comes. When annealing stops, show him plan v1 (`PLAN.md`) in plain words, with the round count and one operations line per ask. Wait until he has read it before stage 4. His changes start another plan round.
4. **Technical lens:** the `funnel-architect` skill. Check `--stage arch`. Do not ask him.
5. **Technical self-annealing:** the `funnel-anneal` skill in technical mode, with the answer-linker and the Opus screen. Check `--stage technical`. Only hidden product calls and fixed-line touches reach him, each with a recommendation.
6. **Handoff:** the `funnel-handoff` skill. It groups the slices into checkpoints of 5 to 8 laid out in parallel lanes, because the build runs builders at once and reviews only at checkpoints. Every brief carries its whole merge request, and every slice gets a chain packet. Check `--stage handoff`, then run `python {STANDING}/check_plan.py {PROGRAM} {SHIP}`.

**Done when:**

- `{PROGRAM}` holds every file listed in `PLANNING-FUNNEL.md`;
- `PROGRAM.yaml` follows `{STANDING}/templates/PROGRAM.yaml`, with a `chains:` row for every ask;
- both checks print PASS;
- every open decision marked `For: him` is listed under Not yet specified in `SCOPE.md`.

**End.**

1. Set `planner_session` in `PROGRAM.yaml` to this session's id.
2. Start plan review yourself, as `{STANDING}/prompts/NEXT-PHASE.md` says: skill `plan-review`, in `C:/Users/Mubarak/Desktop/QMX`.
3. Tell him, in plain words:
   - what the plan builds;
   - the growth line from the check: asks, plan lines, elements and slices;
   - the number of slices, the checkpoints with their sizes, and how many builders can run at once;
   - the open decisions and the Proposals that plan review will put to him;
   - that plan review has started.

   If the session could not start, give him the one sentence `NEXT-PHASE.md` names instead.

Stay open afterwards: plan review sends its mechanical fixes back to you for one round trip. Rerun both checks after each fix.
