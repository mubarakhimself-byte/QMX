# Reviewer prompt

The coordinator fills the {PLACEHOLDERS} and spawns one fresh background agent (`subagent_type: "poteto-agent"`, `model: "opus"`, `run_in_background: true`) per review. {MODE} is `round 1`, `round 2` or `range`. Keep the section for {MODE} and delete the other two.

- {HEAD} is the slice's `head` in `state.json` (full sha), {DISPATCH_ID} its `holder.dispatch_id`, {PARENT} its `parent`, {ATTEMPT} its `attempts`.
- {VERDICT} is `{PROGRAM}/review/{SLICE}-<first 8 of HEAD>.md`. In range mode it is the verdict path `land` printed (`review/{SLICE}-range-<patchid8>.md`), and {RANGE_DIFF} the `.diff` path it printed.
- {ROUND1} is the round-1 verdict path (round 2 only).
- {SHIP}, {STANDING} and {REPO} are as in `COORDINATOR.md`.

---

Read the poteto-mode skill's `SKILL.md` in full, including its Principles section, before any work. Do not spawn sub-agents.

You review slice `{SLICE}` of program `{PROGRAM}` at head `{HEAD}`. You write one file, `{VERDICT}`, plus the run logs the skill below writes under `{PROGRAM}/notes/review-{SLICE}-<first 8 of HEAD>/`. You change no code, make no commit and write no other file.

Read in full first: `{STANDING}/skills/slice-review/SKILL.md` (the method; follow it to its stop line), `{STANDING}/REVIEW.md` (what blocks and the verdict format), `{STANDING}/PROJECT-RULES.md`, `{PROGRAM}/slices/{SLICE}/BRIEF.md`, and the ask it cites in `{PROGRAM}/SCOPE.md`.

The check folder is `{PROGRAM}/tmp/check-{SLICE}-head`, which the slice checks left detached at the head. Confirm `git -C <that folder> rev-parse HEAD` prints `{HEAD}` before you use it.

## round 1

Read:
- the whole diff: `git -C {REPO} diff {PARENT} {HEAD}` (fetch first: `git -C {REPO} fetch -q origin`);
- `{PROGRAM}/evidence/{SLICE}/{ATTEMPT}/how.md`, `red.log`, `report.md` and `answers.md` if present;
- `{PROGRAM}/checks/{SLICE}/<first 8 of HEAD>/summary.txt` and any log it points to that holds a FAIL or NOTRUN line.

Run the skill's four passes, its proof pass and its triage on that diff.

## round 2

Round 1's verdict is `{ROUND1}`. Read it, the fixer's `{PROGRAM}/evidence/{SLICE}/{ATTEMPT}/answers.md` and `report.md`, the fix diff `git -C {REPO} diff <round-1 head from {ROUND1}> {HEAD}`, and the new checks summary. Judge only what `REVIEW.md` says round 2 judges, the way the skill's `references/later-rounds.md` says. Rerun the `SAFETY` fact in the check folder.

## range

The landing rebase changed this slice's patch, or slices landed since its review touched its files. Read `{RANGE_DIFF}` and the slice's last verdict in `{PROGRAM}/review/`. Judge only what `REVIEW.md` says a range review judges, the way the skill's `references/later-rounds.md` says. Your END line still names `{HEAD}` and `{DISPATCH_ID}`, the slice's reviewed head, not the rebased commit.

## Reply

Write `{VERDICT}` in the shape `REVIEW.md` gives, ending with the line `END {HEAD} {DISPATCH_ID}`, and run the skill's `check_verdict.py` until every line reads OK. Reply with only:

```
slice: {SLICE}
verdict: CLEAN | BLOCKED
counts: <n> Important, <n> Nit, <n> Pre-existing
disputes: <each DISPUTE id with accepted or upheld, or none>
file: {VERDICT}
```
