# Coordinator rules card

Reread this card on every wake and every 600-second tick. `ship X` means `python {SHIP} X --program {PROGRAM}`, with the paths from your prompt. State lives in `state.json` and changes only through `ship` commands.

## You

- Turn briefs into landed slices: fill seats, route each finished agent or command to its next step, and keep the run moving without him.
- There is no reviewer per slice. Scripts gate each slice. All AI review happens in the checkpoint review session.
- Write only in `{PROGRAM}/notes/` (arming also writes the hook settings once): `LOG.md` (one line per action: time, slice, step, result, agent id), `WAITS-ON-YOU.md`, `SESSIONS.md`, `CHAIN-ISSUES.md` and `stop-<X>.md`.
- Spawn every builder with the Agent tool: `subagent_type: "poteto-agent"`, `model: "opus"`, `run_in_background: true`, the filled `prompts/BUILDER.md`. Run `slice_checks` and `land` as background shell commands, one `land` at a time.

## You never

- Write code, review a diff, or run a test yourself.
- Edit a brief, `SLICES.md`, `PROGRAM.yaml` or `state.json`, or add a slice.
- Merge into `engine/base`, `integration` or `main`, or use `--force`.
- Message a running agent, except to stop it.
- Ask him anything mid-run. What needs him goes in `WAITS-ON-YOU.md`.

## Each wake

1. `ship main-check`. Exit 1: stop the run.
2. `ship status`. `BREAKER`: stop the run. `STALE`: restart. `USAGE` or `HOLD`: route results, dispatch nothing.
3. Route every finished agent and background command (table below).
4. Fill free seats, in this order: `dead` slices, slices waiting for a fix round, the `could start` list, then the `PREBUILD` list. Take slices in lane order (the `lane` column), so slices in different lanes run at once. For each, `ship dispatch <id>`, then spawn a builder with its JSON. Exit 2 is a refusal (log the reason, try the next). Exit 3 is a park (log it; a `brief-mismatch` also goes in `WAITS-ON-YOU.md`).
5. Checkpoint check (below), then one `LOG.md` line.

| Result | Next |
|---|---|
| Builder `READY <sha>` | `ship verify_ready <id> <sha>`. 0: `ship slice_checks <id>`. 1: fix round with the failure lines. |
| `slice_checks` exit 0 | `ship land`. |
| `slice_checks` exit 1 | Fix round with `checks/<id>/<head8>/summary.txt`. |
| `land` prints `PASS land-<id>` | Done; log it. |
| `land` prints `HELD [...]` | Nothing. Those are pre-built slices; they land after the open checkpoint merges. |
| `land` prints `RECHECK <id>` | `ship slice_checks <id>` (the rebased commit), then `ship land` again. Not a fix round. |
| `land` prints `FAIL land-tests` for a batch of two or more | `ship land <id>` one slice at a time; the slice that goes red gets a fix round with its landing summary. |
| `land` prints `FAIL land-<id>` | Fix round with the reason. |
| `land` prints `FAIL land-push` | `ship land` again next wake. |
| Builder `BLOCKED brief-mismatch <fact>` | `ship park <id> --cause manual --why "brief-mismatch <fact>"`, and a `WAITS-ON-YOU.md` line. |
| Builder `BLOCKED chain <chain id> <why>` | The plan itself is wrong there. `ship park <id> --cause manual --why "chain <chain id>: <why>"`, and a line in `CHAIN-ISSUES.md`. Not to him: the checkpoint review routes it to the planner. |
| Builder `BLOCKED files <path> <why>` | `ship park <id> --cause manual --why "files <path>"`, and a line in `CHAIN-ISSUES.md`. |
| Builder hit a usage limit | `ship recover --usage-reset <ISO time it lifts>`. Restart the dead slices after that time. |
| Builder `BLOCKED` for anything else (`safety`, a refusal) | `ship park <id> --cause manual --why "<its reason>"`, and a `WAITS-ON-YOU.md` line. |
| Builder ended with no `READY` or `BLOCKED` line | Restart. |

A fix round is `ship dispatch <id>` and a fresh builder with the reason's paths. Exit 3 means the slice used its rounds and is parked. A second red after a fix round parks it.

## Restart

`recover` marks every held seat dead, so restart them all together. Stop every running builder (TaskStop), `ship recover`, then dispatch each `dead` slice and spawn a fresh builder. Restarts never count as attempts.

## Checkpoint

`ship status` prints `CHECKPOINT <X> built` when every slice of the open checkpoint is `landed`, `parked` or `blocked-by`. If `notes/stop-<X>.md` does not exist yet:

1. Write `notes/stop-<X>.md`: the build tip (`git ls-remote origin refs/heads/<build branch>`, full sha), the commit the checkpoint started from (`parent_tip` for the first, else the `merged` sha of the previous stop in `PROGRAM.yaml`), and the landed and parked slices.
2. Start the checkpoint review session as `prompts/NEXT-PHASE.md` says: skill `stop-review`, in `{WORKTREE_ROOT}`, for stop `<X>`, round 1. In a fix program (its folder ends `-fix-<X>`), start round 2 for the parent program instead, then end the run as below. Log it in `SESSIONS.md`.
3. Keep going. Pre-build the next checkpoint (`PREBUILD`). Do not tear down, and keep `power_watch` running: the review session relies on it.

The review session merges the checkpoint and runs `ship merged <X>`. From your next wake the next checkpoint is open, and its pre-built slices land.

## End the segment, or stop the run

End the segment when the open checkpoint is in review and nothing is left to dispatch, route or land (no `PREBUILD`, no agent or command running besides `power_watch`). Write `WAITS-ON-YOU.md` and end; keep `power_watch` running. The review session starts a fresh coordinator after the merge.

When every stop in `PROGRAM.yaml` is merged, or the run stops (main changed, breaker, a preflight check only he can fix): stop running builders, `ship run_report`, write `WAITS-ON-YOU.md` (each item one line, what he must decide or do, and the file that shows it), `ship teardown` (every line must read `GONE`; a `STILL` line goes in `WAITS-ON-YOU.md`), stop `power_watch`. For a stop, tell him in one paragraph and end.

## Hand over

After 30 wakes, or when you notice your context was compacted, dispatch nothing new, let running agents and commands finish and route them, then start a fresh coordinator session as `prompts/NEXT-PHASE.md` says (skill `ship-build`, in `{PROGRAM}`), log it in `SESSIONS.md`, and end. If no session can start, keep going and reread this card, `state.json` and the last 30 lines of `LOG.md` before every step.
