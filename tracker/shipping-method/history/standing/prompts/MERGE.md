# Merge prompt (manual entry only)

Merging is the last step of the checkpoint review session (`STOP-REVIEW.md`, section **Merge**), not a phase of its own. The `ship-merge` skill fills this prompt only when he asks by hand, for example "merge stop <X> of <program>", after a review ended CLEAN but its merge did not finish (a refusal from GitHub, a power cut, a session that ended early). The session runs in `{WORKTREE_ROOT}`. Placeholders as in `COORDINATOR.md` and `STOP-REVIEW.md`, plus {STOP}, {TARGET} (`target_branch` in `PROGRAM.yaml`, normally `engine/base`) and {REVIEWED_TIP} (the sha in the END line of the last CLEAN review, `stop-review/{STOP}/REVIEW.md` or `REVIEW-2.md`).

---

Read the poteto-mode skill's `SKILL.md` in full, including its Principles section, before any work. Agents you spawn do not spawn their own.

You land checkpoint `{STOP}` of program `{PROGRAM}` in `{TARGET}`. Read `{STANDING}/prompts/STOP-REVIEW.md` in full, then run its **Power cuts and restarts** section and its **Merge** section, steps 1 to 8, with the placeholders above. Every step is safe to run again: skip a step whose result is already on disk (an open or merged PR, `merge/{STOP}.md` reading `MERGED`, `ship merged {STOP}` printing "already recorded").

If no CLEAN review exists for {STOP}, merge nothing: start the review instead, as `{STANDING}/prompts/NEXT-PHASE.md` says (skill `stop-review`, in `{WORKTREE_ROOT}`, stop {STOP}), and end.

End by telling him in plain words what merged, what is parked, and what waits on him.
