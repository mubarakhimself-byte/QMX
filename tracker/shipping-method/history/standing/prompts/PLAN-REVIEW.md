# Plan review prompt

The `plan-review` skill fills this in a fresh Claude Code session (Claude Opus 5.5), which the planner starts when it hands off. He never pastes it; he can also start it by saying "review the plan for <program>". Placeholders as in `COORDINATOR.md`, plus {PLANNER_SESSION} (the planning session's id, or `none`).

---

Read the poteto-mode skill's `SKILL.md` in full, including its Principles section, before any work. Agents you spawn do not spawn their own.

You review the plan in `{PROGRAM}` before anything is built. You change no plan file except `scope_gate` in `PROGRAM.yaml`. Mechanical fixes go back to the planner. Only open questions and ambiguity go to him.

Read first, in full: `{PROGRAM}/PROGRAM.yaml`, `{PROGRAM}/SCOPE.md`, `{PROGRAM}/SLICES.md`, the files in `{PROGRAM}/decisions/`, `{STANDING}/PROJECT-RULES.md`, and his rulings in `C:/Users/Mubarak/.claude/projects/C--Users-Mubarak-Desktop-QMX/memory/` that the plan touches. Skim the briefs.

1. **Mechanical check.** Run both:
   - `python {STANDING}/check_plan.py {PROGRAM} {SHIP}` parses the plan with the ship scripts' own parser. It checks that every slice cites an ask and a stop point, that every brief has code facts and a `SAFETY` fact, and that no placeholder or agent-spawning skill is left.
   - `python {STANDING}/funnel/check_chain.py {PROGRAM} --stage handoff` checks the chain from his words to every brief. It also checks:
     - that lanes in a checkpoint share no files;
     - that the slice count is justified against the asks;
     - that every brief carries its merge request (`TRACE:`, door, `DOC:`) and its chain packet.

   Every FAIL line is a mechanical fix. WARN and INFO lines go to the `prs.md` reviewer.
2. **Four reviews**, each by a fresh background agent (`subagent_type: "poteto-agent"`, `model: "opus"`), each writing its findings to `{PROGRAM}/plan-review/<name>.md` and replying with the path and counts:
   - `scope.md`. The plan against his words. Every slice traces to an ask in `SCOPE.md`, quoted from him, with where he said it. A slice that serves no ask belongs in Proposals. The slice count follows his asks: challenge any slice that only exists to split work. His contradictions are open questions, never settled by an agent. His rulings hold: demo is a broker demo account, brakes prevent and never close, no fixed unit journey.
   - `logic.md`. Logical holes, edge cases and verification gaps, through `bmad-review`'s adversarial, edge-case and verification-gap lenses run in one agent, and `principle-attack-the-premise`. Plus the architecture: do the decision files hold together, and does each slice respect dependency direction and the fixed lines? Use `codebase-design`'s vocabulary.
   - `prs.md`. The PR plan, laid out for a build with no reviewer per slice, review at each checkpoint, and builders in parallel lanes:
     - **Dependencies:** complete and acyclic.
     - **Checkpoints** (stop points): 5 to 8 slices each, each a coherent piece the checkpoint review can judge against the plan lines and elements it covers, each ending in something he can see, in a sensible order.
     - **Lanes:** slices in different lanes of a checkpoint share no file, including forced files the brief may have missed; a dependency across lanes is rare and has a reason.
     - **Pre-build:** each `prebuild-<X>` line shows how much of the next checkpoint can be built during review; propose a re-layout where little can.
     - **Count:** the slice count is justified against the asks, and no slice exists only to split work.
     - **Merge request:** each brief's section 11 holds a plain-words line he would understand, a true door call, and every `DOC:` line.
     - **Sizes:** honest.
   - `grounding.md`. Every brief's code facts and files, with `{STANDING}/prompts/GROUNDING.md`: {TIP} is `parent_tip`, {REPORT} `{PROGRAM}/plan-review/grounding.md`, {CHECKOUT} `{WORKTREE_ROOT}/plan-review-<program>`. It changes no brief at this stage: tell it to list every FIXED item as a proposed change instead.
3. **Sort every finding.** A finding is mechanical when his intent is clear and only a name, path, value, fact, edge or forced file is wrong. Anything that needs his intent is an open question, as is any ambiguity, any of his contradictions, and the Proposals pick list.
4. **One round trip with the planner.** Send all mechanical fixes in one message (SendMessage to {PLANNER_SESSION}), each with its evidence. Wait for its reply, then rerun step 1 (the planner reruns `chain_packet.py` after changing a brief) and check each fix landed. When {PLANNER_SESSION} is `none` or no longer running, write them to `{PROGRAM}/plan-review/FIXES.md`. Then start a planning session yourself, as `{STANDING}/prompts/NEXT-PHASE.md` says, with skill `plan-feature` in `C:/Users/Mubarak/Desktop/QMX` and the brief "resume {PROGRAM} and apply `plan-review/FIXES.md`". Wait for it.
5. **His turn.** Ask the open questions with AskUserQuestion, in rounds of at most 4 numbered questions, each in plain words with your recommended answer first. Put the Proposals to him as a pick list; anything he does not pick stays parked. Send his answers to the planner to fold into `SCOPE.md` and the briefs, then check they landed.
6. **The scope gate.** Nothing ships before his go. When he says go, set `scope_gate: {by: him, at: <date>, where: <this session's title>}` in `PROGRAM.yaml`. Then start the build yourself, as `{STANDING}/prompts/NEXT-PHASE.md` says: skill `ship-build`, in `{PROGRAM}`.

End by telling him in plain words what the plan builds, how many slices and stop points, and that the run has started.
