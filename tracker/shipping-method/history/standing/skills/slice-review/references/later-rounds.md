# Round 2 and range reviews

Both modes judge less than round 1. The proof pass, triage and the verdict rules from `SKILL.md` still apply to everything you raise.

## Round 2

Read round 1's verdict, the fixer's `answers.md` and `report.md`, the fix diff (`git diff <round-1 head> <head>`, the round-1 head is in round 1's END line), and the new checks summary.

Round 2 judges two things. A slice blocked in round 2 parks and goes to him, since there is no third round.

### 1. Each round-1 Important

Find its answer in `answers.md`.

- **`FIXED <id>`, or no answer.** Rerun the finding's round-1 evidence at the new head, or reread its line. It is FIXED when the defect no longer shows. It STANDS when it still shows.
- **`DISPUTE <id> <reason>`.** Rerun the round-1 evidence at the new head, then test the reason's claim against the code with the proof pass.
  - **Accepted** when the round-1 evidence no longer reproduces, or the reason is backed by a `file:line` or a run showing the finding was wrong: handled outside the hunk, allowed by the brief, or outside the blocker's words. The finding is withdrawn.
  - **Upheld** when the round-1 evidence reproduces at the head and the reason brings nothing that refutes it. The finding stays Important.
  - The finding carries the burden. A dispute you cannot refute with proof is accepted.

Record every round-1 Important in a `## Round 1` section, placed between the count line and `## Important`, one line each:

```
- I1 FIXED. Evidence: <command and output at the new head>.
- I2 STANDS. Evidence: <...>.
- I3 DISPUTE accepted: <why, in one line>. Evidence: <...>.
- I4 DISPUTE upheld: <why the reason fails, in one line>. Evidence: <...>.
```

Each STANDS and DISPUTE upheld line also goes under `## Important` with its round-1 id and blocker number.

Round-1 Nits and Pre-existing findings are closed by the fixer's `FIXED` or `CLOSED` answers. Leave them closed.

### 2. A new Important in the fix diff

Run passes 1 to 4 on the fix diff only, then the proof pass and triage. Keep only Important findings. Number them after round 1's highest id.

Code that round 1 passed stays passed, even when you notice something there. The stop review reads the whole stop point.

### Round 2 verdict

- `## Important`: the STANDS and upheld findings, plus new ones.
- `## Nits` and `## Pre-existing`: "none".
- Rerun the `SAFETY` fact at the new head for the safety section. Fill the rubric for the head as it now stands.
- The title reads `round 2`.

## Range

The landing rebase changed the patch, or slices landed since the review touched its files. Read the range-diff and the slice's last verdict.

Range judges one thing: does the rebased change still meet the brief and keep the fixed lines?

1. Run pass 3 on the parts of the range-diff that changed, and pass 1 steps 3 and 4 on the same parts.
2. Run the proof pass and triage. Keep only Important findings.
3. For the safety section, say whether the range-diff touches the files the `SAFETY` fact reads. When it does not, carry the last verdict's command and output. End the section with "matches the brief" or "differs".

The title reads `round range`. The END line names the reviewed head and dispatch id your prompt gives, not the rebased commit.
