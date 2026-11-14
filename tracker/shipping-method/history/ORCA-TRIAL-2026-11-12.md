# Orca trial, 2026-11-12

One coordinator (Claude Opus 5.5, this session) and one Orca worker (Claude Sonnet 5.5, current worktree) reviewed `ROLES-2026-11-12.md`.

## Commands and results

| # | Command | Worked |
|---|---------|--------|
| 1 | `orca skills get orchestration` | Yes. Printed the skill. It does not name the run-create command; I found it with `orca orchestration --help`. |
| 2 | `orca orchestration --help` | Yes. |
| 3 | `orca orchestration run-create --objective "Trial: one Claude worker reviews the shipping roles draft"` | Yes. `runId=run_c1b0cb654385` |
| 4 | `orca orchestration worker-start --agent claude --model claude-sonnet-5-5 --worktree current --spec "..."` | Yes. `dispatchId=ctx_92d07ec1a720`, `taskId=task_5840e938422c`, state=ready, mode=structured |
| 5 | `orca orchestration check --run run_c1b0cb654385` (after the wake) | Yes. Returned one `worker_done` with outcome=succeeded |
| 6 | `orca orchestration worker-release --dispatch ctx_92d07ec1a720` | Yes. state=released, agent terminal closed, transcript archived |

## Timing

- Skill fetched: 13:13:52 (+03:00)
- Worker started: 13:14:20
- Woken by Orca and report read: 13:14:34
- From worker start to report: about **14 seconds**. From the first command to the report: about 42 seconds.

## Wake without polling

Yes. I ended my turn after `worker-start`. Orca woke me with "You have 1 orchestration message. Run `orca orchestration check --run ...`". I did not poll.

## Worker report (verbatim)

> ROLES review done
> Read ROLES-2026-11-12.md, no edits. Findings: (1) Builder step 6 opens the PR before step 7 writes report.md, and the doc never says who creates the PR or whether READY is posted there; PR-BODY-AND-SKILLS file is referenced but not checked. (2) 'Fix builder' is unclear on branch and model: same branch? same roster model? And 'second small round' has no size definition, and 'parks' has no state.json status named. (3) Landing step 1 says rebase, but builders must never rebase or force-push; who rebases (script) and how the rebased head gets re-checked/re-reviewed is unstated, and a conflict-fix builder is told nothing about re-review. (4) Reviewer 'reruns the safety fact' but the fact lives in the brief/how.md with no stated exact format; 'brief not met' and 'size limit' lack a measured definition. (5) Orca-specific: coordinator wake relies on worker_done while the fallback 10-min timer duplicates it, with no rule against double-starting a seat; seat/lock holder field in state.json is vague. Clear: the blocker list, the 'never' lists, and the end-of-run ARMED.md teardown rule are unambiguous.
>
> payload: taskId=task_5840e938422c dispatchId=ctx_92d07ec1a720 outcome=succeeded

## Failures and surprises

- Nothing failed.
- The skill text does not name `run-create`. A coordinator must look at `--help` to find it.
- The 14-second turnaround is fast for reading a file and writing a review. The findings cite specific steps, so the worker did read the file.
- The worker ignored the "at most 6 lines" limit. It sent one long paragraph with five findings. A coordinator brief needs a hard output format, not a soft limit.
- `check` printed a ready-made `send` command, which makes follow-up easy.
- Finding 5 bears directly on Orca: if the coordinator wakes on `worker_done`, the 10-minute fallback timer in ROLES can start a seat a second time. ROLES needs a rule against that.
