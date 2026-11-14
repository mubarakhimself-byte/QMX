# Drills on the real machine

FACTORY-DESIGN section 13.5 (unit U12). The chaos suite (`tests/test_chain_chaos.py`) proves the conveyor's
answers with fakes. These drills prove the parts only the real laptop can show: its power line, Windows
restarting, Claude Desktop, a real usage limit, the real network, GitHub's branch protection, the front desk
waking, Fable's real decisions and two real programs at once. They are done once by hand during U19 and
recorded here.

The coverage table for every matrix row, loop and hand-off (test, drill, or "not testable here") is at the top
of `tests/test_chain_chaos.py`.

## How to record a drill

Each drill has a **Result** block. Fill it in when the drill is done:

- **Date:** the day and time.
- **Program:** the program folder the drill ran on.
- **Seen:** what happened, in a few plain lines, with the file or log line that shows it.
- **Verdict:** PASS or FAIL. A FAIL gets a line in `BUILD-LOG` and a backlog row; it is not fixed during the drill.

Commands are for PowerShell 7 in the main checkout. `P` is the program folder
(`D:/QMX-worktrees/plans/<program>`), `PLANS` is `D:/QMX-worktrees/plans`. The kit is `python tools/ship`.

## Before any drill

1. A small real program is armed and building, with at least two slices still to build. The first program of
   U19 (`ci-green`) is the one the design names.
2. `python tools/ship phase --program P` prints `next: build` and `status: running`.
3. Note the time, and the last line of `P/notes/chain.log`.

---

## D1. Power

Matrix row 1. Chaos twin: `Power.test_battery_holds_then_resumes`.

**Do**

1. While builders run, pull the charger. Leave it out for ten minutes.
2. Watch `P/HOLD` and `P/notes/chain.log`.
3. Plug the charger back in. Wait for the settle time (`power_settle_s`, 10 minutes by default).

**Expect**

- `P/HOLD` appears within a minute (`power_poll_s`), and its first word is `power:`.
- No `START` line in `chain.log` while HOLD is there: no builder, no `verify_ready`, no review, no merge.
- The builders that were running finish and push; their `WORKER builder ... ended` lines appear.
- After mains returns and the settle time passes, HOLD is gone without anyone touching it, and the run goes on.
- In `P/state.json`, no slice's `attempts` grew because of the power cut.

**Result**

- Date:
- Program:
- Seen:
- Verdict:

## D2. Restart (the logon task)

Matrix row 2. Chaos twin: `DeadLaptop.test_dead_laptop_resume_all`.

**Do**

1. Once, before the drill: `python tools/ship chain --install-task --plans PLANS --install`. Check it with
   `schtasks /Query /TN factory-resume`.
2. While a builder runs, restart Windows from the Start menu.
3. Log on. Do not open Claude Desktop.

**Expect**

- Within a minute of logon the `factory-resume` task runs `chain --resume-all`; a new conveyor holds
  `P/chain.lock`.
- `P/notes/chain.log` shows the recovery: `RESET <slice> to <sha>`, and `leftovers in .../leftover.patch` for a
  builder that had unpushed work.
- The run carries on from the first step with no done-file.
- Nothing is landed twice: `git log --first-parent --format=%s origin/<build branch>` names each slice once.
- The restarted slice has `restarts` one higher and the same `attempts`.

**Result**

- Date:
- Program:
- Seen:
- Verdict:

## D3. The app closed mid-build

Matrix row 5. Chaos twin: `Detach.test_detached_conveyor_outlives_parent`.

**Do**

1. While builders run, quit Claude Desktop (tray icon, Quit), not just its window.
2. Wait five minutes.
3. In a plain terminal: `python tools/ship phase --program P`.

**Expect**

- The conveyor and its workers keep running (`Get-Process python` still lists them; `chain.log` keeps growing).
- `ship phase` shows progress: slices land, `next` moves on.
- Questions for him, if any, wait in `P/notes/WAITS-ON-YOU.md`.

**Result**

- Date:
- Program:
- Seen:
- Verdict:

## D4. A real usage limit

Matrix row 4. Chaos twin: `Limits.test_usage_limit_sleeps`. This drill is done the first time it happens, not
on purpose.

**Do**

1. When a worker ends on a usage limit, open its `P/workers/<id>/stdout.log` and `result.json`.
2. Copy the raw result into `tools/ship/roles/RESULT-SHAPE.md` under a new heading with the date.
3. Compare the reset time in the message with `usage_reset_at` in `P/state.json`.

**Expect**

- `result.json` says kind `limit` (D-L12: the text names a limit and the run ended in an error).
- `usage_reset_at` is the reset time the message names. If it is not, add the message's pattern to
  `limit_patterns` and say so in `BUILD-LOG`.
- No worker starts before the reset; nothing polls the agent meanwhile.
- After the reset the slice restarts: `restarts` one higher, `attempts` and `deaths` the same.

**Result**

- Date:
- Program:
- Seen:
- Verdict:

## D5. Network down

Matrix row 3. Chaos twin: `Network.test_remote_down_is_not_a_failure`.

**Do**

1. While builders run, turn Wi-Fi off (and unplug any cable). Leave it off for five minutes.
2. Turn it back on.

**Expect**

- `P/HOLD` appears, its first word `network:`.
- No slice is parked and no `attempts` grows. `verify_ready` and `land` that were running return
  `unreachable` (exit 3) and are tried again; they never become a fix round.
- When the network is back, the next good probe removes HOLD (no settle wait) and the run goes on.

**Result**

- Date:
- Program:
- Seen:
- Verdict:

## D6. Branch protection

Matrix rows 2 and 33 (no local-only merge). No chaos twin: only GitHub can refuse.

**Do**

1. `python tools/ship preflight --program P --protection-push-test`.

**Expect**

- The push to `engine/base` is rejected, and preflight passes that check.
- If the push is accepted, preflight fails, puts the branch back, and nothing may merge until protection is
  fixed.

**Result**

- Date:
- Program:
- Seen:
- Verdict:

## D7. The front desk wakes

Matrix rows 9 and 10. Chaos twins: `Gates.test_away_at_go`, `Gates.test_answer_then_go`.

**Do**

1. In a front-desk session, start the program with `chain --detach`, then `chain --follow P` as a background
   command, as the `factory` skill does.
2. Leave the session alone until the program finishes or asks him something.

**Expect**

- When the conveyor finishes, writes WAITS, or dies, `--follow` exits (0, 10 or 1) and the session wakes.
- The session says one line, or asks with at most four questions, recommendation first.
- An answer goes in through the desk (`.desk/answers.md`, D-L25) and `ship gate`, never by editing
  `PROGRAM.yaml`.

**Result**

- Date:
- Program:
- Seen:
- Verdict:

## D8. The first Fable-decided removals

Matrix row 54. No chaos twin: only a real Fable judgement and his reading of it show this.

**Do**

1. At the first audit checkpoint's merge, open `P/merge/<X>-pr.md` and the merge note.
2. Ask him whether any removal Fable decided surprised him.

**Expect**

- Every removal Fable decided is listed in plain words, each one its own revertable commit.
- If he says one surprised him, that becomes a line in the screen prompt (skills lane) and a backlog row.

**Result**

- Date:
- Program:
- Seen:
- Verdict:

## D9. Two programs at once

Matrix rows 46 to 50. Chaos and kit twins: `test_claims.Build`, `test_claims.Merges`, `test_locks.MergeQueue`.

**Do**

1. While one program builds, start a second small program on other files (`chain --detach`).
2. Let both run to the end.

**Expect**

- Both finish. Their merges took turns: `merge-qmx.lock` named one, then the other; the second merge commit
  contains the first's code and had its own deep run.
- No more workers ran at once than the pool allows (`[pool] workers`).
- A slice naming a file the other program claims waited (`WAIT <slice> blocked-by claim`) and was not counted
  as a failure.

**Result**

- Date:
- Program:
- Seen:
- Verdict:

## D10. The conveyor killed by hand

Matrix rows 2 and 36. Chaos twins: `DeadLaptop`, and `test_chain.Waits.test_a_second_conveyor_...`.

**Do**

1. While builders run, start a second conveyor: `python tools/ship chain --program P`.
2. End the first conveyor's `python` process in Task Manager (only that one; leave its workers).
3. Say "continue" at the front desk, or run `python tools/ship chain --resume-all --plans PLANS`.

**Expect**

- Step 1 exits 11 at once and the first conveyor is undisturbed.
- After step 3 a new conveyor stops the dead one's workers (matched by pid and creation time, D-L14), saves
  their leftovers, resets them to their last push, and carries on. Nothing lands twice.

**Result**

- Date:
- Program:
- Seen:
- Verdict:

## D11. His HOLD during a power blip

D-L25 (HOLD stops everything new; the power watch never removes his HOLD). Kit twins:
`test_k4.HoldRelease`, `test_k4a.PowerRace`.

**Do**

1. While builders run: `python tools/ship hold --program P --why "drill"`.
2. Pull the charger for two minutes, then plug it back in, and wait past the settle time.
3. `python tools/ship release --program P`.

**Expect**

- After step 1 nothing new starts; running workers finish and their results are read.
- Through step 2 `P/HOLD` keeps his text: the watcher neither writes over it nor removes it.
- After step 3 the run goes on.

**Result**

- Date:
- Program:
- Seen:
- Verdict:

## D12. GitHub's queue stuck

Matrix row 33. Chaos twin: `Ci.test_ci_stuck_waits_no_local_merge`. Done the first time a deep run sits queued
for real, not on purpose.

**Do**

1. When a checkpoint's deep run stays queued, watch `P/notes/chain.log` and `P/notes/WAITS-ON-YOU.md`.

**Expect**

- The conveyor waits up to `ci_wait_timeout_s` (12 hours), starts the run once more, waits again, then writes
  one WAITS line with the run's URL and exits 10.
- No local run stands in and nothing merges.

**Result**

- Date:
- Program:
- Seen:
- Verdict:
