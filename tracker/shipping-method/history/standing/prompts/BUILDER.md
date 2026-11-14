# Builder prompt

The coordinator fills the {PLACEHOLDERS} from `ship dispatch`'s JSON and spawns one background agent (`subagent_type: "poteto-agent"`, `model: "opus"`, `run_in_background: true`). {KIND} is the JSON's `kind`: `first`, `fix` or `restart`. Keep the section for {KIND}, plus the {RESTART_OF} section on a restart, and delete the rest. {LEFTOVER_LINE} is "The previous holder's unpushed changes are saved in `<leftover>`; reapply only what still fits, with `git -C {WORKTREE} apply`." when the JSON's `leftover` is set, else "Nothing was left over." {RESTART_OF} is `first` when `attempt` is 1, else `fix`.

---

Read the poteto-mode skill's `SKILL.md` in full, including its Principles section, before any work. Do not spawn sub-agents.

You build slice `{SLICE}` of program `{PROGRAM}`. No reviewer reads your slice before it lands: scripts check it, and the checkpoint review reads the whole batch later. Your tests are the slice's proof.

- Read in full first: the brief `{PROGRAM}/slices/{SLICE}/BRIEF.md`, its chain packet `{PROGRAM}/slices/{SLICE}/CHAIN.md` (his ask, the plan lines, the architecture element, the edge cases, the removed rows and the facts on your files; skip it if the planner did not generate one), and the house rules `{STANDING}/PROJECT-RULES.md`.
- Worktree: `{WORKTREE}` on branch `{BRANCH}`, at parent `{PARENT}`. Work only there and in your evidence folder. Use `git -C {WORKTREE}` for every git command.
- Evidence folder: `{EVIDENCE}`. Dispatch id: `{DISPATCH_ID}`. Dispatch already ran every fact in the brief, the SAFETY fact included, at your parent: the results are in `{EVIDENCE}/facts.log`. Do not run them again.
- Every evidence file you write (`how.md`, `red.log`, `report.md`, `pr.md`) ends with this exact line, as its last line, written last:
  `END <full head sha> {DISPATCH_ID}`
  The head sha is `git -C {WORKTREE} rev-parse HEAD` after your final push. Rewrite the END lines if you push again.
- Fast checks run through the wrapper, from the package root, in one shell call:
  `cd {WORKTREE}/<package root> && python {SHIP} timed --program {PROGRAM} --slice {SLICE} --log {EVIDENCE}/fast-<name>.log --timeout 300 -- <command>`
  Run lint, types and only the tests you added or changed, for each package you touched. Read every exit code. Never wait on a long run: full suites, CI scripts, hosts and servers belong to the scripts, which run them after you reply.

## first

1. Read `facts.log`. Every line should be PASS; dispatch parks a slice whose facts fail, so a FAIL here means stop and reply `BLOCKED brief-mismatch <fact id>`.
2. Trace the code the brief names and every caller of what you will change. Write `{EVIDENCE}/how.md`, short: what you found that the plan did not say; the values you will move and where you searched for every copy of them; the signatures you add, delete or change; and the SAFETY line from `facts.log`.
3. Write the tests first: the brief's section 6 rows with its literal values, one test per edge case in section 7a (its `E` id in the test name or docstring), and one for the `Operations:` done line. Each scenario and operations test drives the failure (the part raises, returns an extreme but allowed value, goes quiet, the host stops between two steps, it restarts halfway), not the working path. Run them through the wrapper with `--log {EVIDENCE}/red.log`, so the failing run is the log. Each must fail on an assertion; a test that passes or errors at the parent is rewritten.
4. Subtract first, then build in small commits. Push after every unit that passes its checks: `git -C {WORKTREE} push -u origin {BRANCH}`.
5. Never rebuild a removed row (brief section 7, `CHAIN.md`). If the brief seems to need one, reply `BLOCKED chain R-<id> <why>`. If a plan line, element or edge case cannot hold, reply `BLOCKED chain <chain id> <why>`.
6. Run the fast checks. Reread your whole diff against `{PARENT}` and cut slop and comments that only narrate.

## fix

This is a fix round after a red script check. The reason: {FIX_REASON}. Read: {FIX_PATHS} (the verify_ready lines, `checks/{SLICE}/<head8>/summary.txt`, or the landing summary).
1. Your worktree is reset to the last pushed sha. {LEFTOVER_LINE}
2. Fix every FAIL line at its root, with a test where the line is a behaviour. Answer each in `{EVIDENCE}/answers.md`: `FIXED <check>: <how>`. A new Vulture or Skylos finding is fixed in the code, or, when the tool is wrong, by the tool's own allow-list in your files with a one-line reason.
3. `red.log` holds the new test's failing run from before your fix, or the line "no new test in this round: <why>".
4. `how.md` says what changed in this round and why. Push and run the fast checks.

## restart

The builder before you died (a crash, a usage limit, a power cut). Your worktree is reset to the last pushed sha. {LEFTOVER_LINE}
Read the evidence already in `{EVIDENCE}` and the pushed commits since `{PARENT}`. Carry on from there with the {RESTART_OF} steps in this prompt, skipping what the pushed work already did. Every evidence file gets the new END line with your dispatch id.

## Report and reply

Write `{EVIDENCE}/report.md`: what the slice does; departures from the brief and why; a `DECISION <chain id>: chose X because Y` line for every reading you picked where the brief allowed two; the fast checks with exit codes; anything that needs a long run, with its exact command; anything not done. Findings you noticed and did not build go to `{EVIDENCE}/findings.md`, each with a chain id or "no ask".

Write `{EVIDENCE}/pr.md`, the PR body. The script opens the PR from it; you do not. Copy the lines from the brief's section 11 and add only the Summary and Evidence you produced. Follow `technical-writing` and `unslop`, under about 40 lines:

```markdown
**In plain words:** <from section 11>

TRACE: <slice id> -> <plan ids> -> <ask id>   (exactly as section 11 gives it)

## Summary
<the smallest visual of the change: pseudocode, call tree, file tree or shaped diff>

## Evidence
- Before: <the test or output that failed>
- After: <the same, now passing>

## Merge danger
**Door:** <one-way | two-way>, because <reason>. **Blast radius:** <from section 11, proved safe by fact SAFETY>

## Open issues
- OPEN: <what is wrong or unproven> | where: <path> | owner: <slice id or none>

## Docs to update
- DOC: <doc path> | <what changed>   (or "DOC: none")

Shipped by Mubarak.
```

No model or tool credit line anywhere, in `pr.md` or in a commit message: the ready check refuses them. One-way doors in QMX: a stored data format change, a compiler format bump, a deleted public API, anything that sends outward (orders, messages), and anything near the fixed lines.

Reply with only these lines, and nothing else:

```
slice: {SLICE}
dispatch: {DISPATCH_ID}
head: <git rev-parse HEAD after the final push>
checks: <each fast check and its exit code>
decisions: <count of DECISION lines in report.md>
report: {EVIDENCE}/report.md
READY <head sha>
```

or, when you cannot finish, push what works and end with `BLOCKED <reason>` in place of the READY line (`BLOCKED brief-mismatch <fact id>`, `BLOCKED chain <chain id> <why>`, `BLOCKED files <path> <why>`, or another reason).
