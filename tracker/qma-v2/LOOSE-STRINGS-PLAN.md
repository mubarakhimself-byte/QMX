# QMX loose strings, build program

This program closes the backend gaps that stop QMX launching cleanly out of the box, so the UI agent who wires the separate UI design later finds no backend gap to fill.
He asked for it on 2026-10-27 ("the back end has no loose strings"). The triage of 208 findings against `629bea16` is `D:/QMX-worktrees/qma-ship/wrapup/evidence/loose-strings-triage-2026-10-27.md` (16 launch capabilities, C1 to C16).
There are 7 PRs. P1 runs the bring-in in the background, reports in plain words and hands the chosen folder to the desktop app. P2a makes every resumed run land. P2b gives a live run its inputs from REST and triggers. P3 makes cTrader work with no hand-set protocol files and says why a read failed. P4 refuses a demo row on an exchange with no demo mode. P5 runs template install as a job. P6 makes the host name what did not open.
The coordinator's closing lanes (V, C16) run after the stack. Local backup and restore (G1) is the next program, not this one (Appendix B).
The stack roots on `build/md3` at `629bea16`. Units, UI code, other machines and the real server are out of scope.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a test run, or a SHA. The body is a how-to. The appendices explain and record.

Each PR section opens with a preamble naming the triage capabilities and lines it closes, the rulings it serves, what the code does today, and its done line with the edge cases it must survive. Then come the nine blocks `check-plan.mjs` requires.

Path shorthands. `QA/` is `qmx-agents/packages/`. `HO/` is `QA/qmx-host/src/qmx_host/`, `E/` is `QA/qmx-engine/src/qmx_engine/`, `LB/` is `QA/qmx-library/src/qmx_library/`, `MM/` is `QA/qmx-memory/src/qmx_memory/`, `QX/` is `QA/qmx-control/src/qmx_control/`, `BR/` is `QA/qmx-broker/src/qmx_broker/` and `HM/` is `QA/qmx-home/src/qmx_home/`. Line numbers are at `629bea16`.

The store is `D:/QMX-worktrees/qma-ship/wrapup/` (the one the mock-data program used), with `QUEUE.md`, `BRIEF-BUILDER.md`, `REVIEWER-BRIEF.md`, `RESUME.md`, `BACKLOG.md`, `lows.md`, `ledger.tsv`, `dispatch/`, `review/` and `evidence/`.

The program follows `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md` with the overrides of `LOCAL-FIRST-PLAN.md`, as `MOCK-DATA-PLAN.md` did. Builders are Claude Opus 5.5 (`poteto-agent`, `model: opus`), at most two at once, never two on shared files. A fresh Opus reviewer agent reviews every diff and runs the edge-case lens of `bmad-review` on every PR (each touches data, the Library or connections). The coordinator runs the suites, `just ci` and the lanes in the background and allows one fix round. Low findings go to `lows.md`; anything new goes to `BACKLOG.md`. He lands the stack himself.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] Confirm the shell (Windows 11, PowerShell 7.6 and Git Bash; in PowerShell `$H` and `$h` are one variable) and the root (`git rev-parse origin/build/md3` is `629bea16`). Logged in `RESUME.md`.
- [ ] Read the trunk rules with `git show origin/main:CLAUDE.md`, then the rulings file `research/methodology/26-operator-rulings-and-alignment.md` (rulings 106, 135 and 141 to 145), then the triage file named above, then Appendix E of this plan.
- [ ] No hourly `/loop 1h` tick, because builder and background-job notifications wake the coordinator. Post a short status message to the operator only when a PR opens, a verdict lands or a blocker appears.
- [ ] Never stop to ask him during the build. Stop only for a credential, a real ambiguity in this plan, or a step only he can do (`QUEUE.md`).

### Spawn owners

| # | Id | PR | Wave | Branches from | Runs beside | Proving check |
|---|---|---|---|---|---|---|
| 1 | P1 | The bring-in runs in the background and hands over | 1 | `629bea16` | P2a | a 2,000-item bring-in shows rising counts, then the host starts on the same port |
| 2 | P2a | Every resumed run lands | 1 | `629bea16` | P1 | a run killed before its first summary lands its clippings on `main` after a resume |
| 3 | P2b | A live run takes its inputs | 2 | the stack tip after wave 1 | P3 | a REST run of "Clippings into research" reads the folder its body names |
| 4 | P3 | cTrader works out of the box | 2 | the stack tip after wave 1 | P2b | a sign-in with no protocol fields reads accounts, and an expired token is refreshed |
| 5 | P5 | Template install runs as a job | 3 | the stack tip after wave 2 | P6 | an install of three templates answers at once and reports each one |
| 6 | P6 | The host names what did not open | 3 | the stack tip after wave 2 | P5 | `/api/data/instruments` answers its reason when the price door is shut |
| 7 | P4 | A demo row with no demo mode is refused | 4 | the stack tip after wave 3 | none | a kraken demo row is refused by name when it is written |

- [ ] Spawn one fresh Opus builder per PR in the background with `subagent_type: poteto-agent` and `model: opus`, from a dispatch file saved in `dispatch/`. Its first words are exactly "Read the poteto-mode skill's SKILL.md in full, including its Principles section, before any work. Do not spawn sub-agents."
- [ ] Before each wave's second dispatch, record the empty Files intersection of its two PRs in `ledger.tsv` (Appendix C).
- [ ] No PR touches `apps/qmx-ui/`, `~/.claude`, his real home `~/.qmx`, his real QMX folder, `C:/Users/Mubarak/Documents`, `C:/Users/Mubarak/Desktop/DATA_NARL`, Credential Manager or any vault value. Lanes run on throwaway folders and a scratch profile only, and broker lanes inject a fake key store.

### PR mechanics, for every PR

- [ ] The coordinator creates `build/ls-<id>` from the branch the table names in `D:/QMX-worktrees/bld-ls-<id>` before the dispatch. Never `git stash`.
- [ ] The builder opens the PR ready with `gh pr create --base <parent-branch> --head build/ls-<id> --repo MubarakHimself/QMX`.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Set `TMP` and `TEMP` to `D:/Temp`, `UV_CACHE_DIR` to `D:/Caches/uv`, and put `D:/Tools/rclone` on `PATH`.
- [ ] The builder reads the code its Files block names before editing, reproduces each finding with a failing test first, then fixes it. It runs `fmt-check`, `lint` and `types` in each package it touched and `tools/secret_scan.py`, reads each exit code, runs only the fast tests it added or changed, and never waits on a long command. It runs the `blast-radius` skill on its diff before the last push and proves the one fact its Build block names.
- [ ] Every line a person reads (a refusal, a job's line, a report) is plain words, names the thing and says what to do next. No QMX-internal cap, ceiling or default-closed lock is added anywhere (ruling 106).
- [ ] Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. PR bodies end with the Claude Code line.

### Verdict and merge, for every PR (append to the stack, merge on his go)

- [ ] At the code-ready head the coordinator runs the touched suites with `-n 2` and lanes 1 to 4 in the background, reads every package block of each log (not its tail), and saves the logs. A fresh Opus reviewer agent (one per PR, `model: opus`, told not to spawn sub-agents) reads the PR section, the full diff, the edge-case lens and those logs, and writes `review/<id>-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] Blockers go back to the same builder for one fix round. Low findings go to `lows.md`.
- [ ] `ledger.tsv` gets head, parent and patch-id.
- [ ] Parallel PRs of one wave join the stack with merge commits, never a rebase. `just ci` runs at the stack tip once at the end, with `D:/Tools/rclone` on `PATH`, under `D:/QMX-worktrees/.ci-lock`.
- [ ] He lands the stack himself from the one full list the coordinator sends when `QUEUE.md` is empty.

### Boot recipe, for every live lane

- [ ] `git worktree add --detach D:/Temp/ls-<id>-check <head>`, then `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`.
- [ ] A lane runs on a throwaway QMX folder under `D:/QMX-worktrees/qma-ship/wrapup/homes/ls-<id>-<lane>/`, made with `qmx_home.resolve(..., create=True)`, with `USERPROFILE`, `APPDATA`, `LOCALAPPDATA` and `HOME` on a scratch profile under the same folder, so the pointer file lands there too.
- [ ] A lane that starts a host or a first-start card injects its bearer, turns the memory database off (`hindsight_runs` patched), and uses a port of its own, because on Windows pg0 writes his real profile (design 62 L7).
- [ ] A synthetic old folder is made by the bring-in tests' own builder (`old_home` in `QA/qmx-host/tests/test_bring_in.py`), never copied from `~/.qmx`.
- [ ] Save captures as `evidence/ls-<id>/check-<slug>.log`, then remove the check copy with `git worktree remove` and confirm no `qmx_host`, `claude` or `node` process from the lane is left.

## Run the bring-in in the background and hand the folder over (P1)

Triage C1 to C4 and G2 (B114, B116, L52a to L52c, L53, L54b, L59b, L60b, L66). Rulings 141 and 142 (his data is in one place, nothing he relies on is a stand-in) and 143 (nothing but the pointer sits beside the pointer). Today `POST /api/first-start/bring-in` runs `bring_in_old` inside the request (`HO/first_start.py:393-401`), so a 10,000-item bring-in holds one HTTP request for 663 s with no progress. An error before the unfinished marker (`HO/bring_in.py:295-310`, the survey, the room check and `resolve(create=True)`) escapes as a traceback and the card gets a 500. The removable-drive warning is printed only by the CLI (`HO/__main__.py:154-156`). `copy_file`, `sha256_of`, `listing` and `_survey` open plain paths, so a file whose path is over 260 characters ends the bring-in unfinished. The report counts versions as items (`_kinds_brought_in` counts `items` rows, one per version, and `_made_by_tests(len(tests))` counts version ids). After a choice finishes nothing starts the host (`HO/__main__.py:133-140`). Done when the bring-in runs as a job the card reads by id, with its step, files and bytes copied and items switched; the fast refusals still answer 409 at once; every other failure ends the job `stopped` with one plain line and no traceback, the folder marked unfinished only when copying began; a file path over 260 characters copies and hashes; the report counts items, not versions; the card shows the removable-drive warning on the drive row and on the chosen folder; and the card's server hands the chosen folder to the desktop app by the contract in Appendix E. Edge cases it must survive. A second bring-in while one runs answers 409 naming the running job. A choice of new or open while a bring-in runs answers 409. A card process killed mid copy leaves the folder marked unfinished, the old folder byte for byte unchanged, and an unknown job id answers 404 with a plain line. A rerun into a finished folder returns the saved report as a finished job and copies nothing. A file in the old folder that changes during the copy still stops the job by name. Handover before any choice, or after an unfinished bring-in, answers 409. Handover twice answers the same folder. The card's port already in use exits 2 before anything is served. A pointer that cannot be written (no `APPDATA`) still hands over by the printed folder line.

**Depends on.** The root `629bea16`.

**Files.**

- [ ] Create `HO/jobs.py`. One `Jobs` registry for long work the host runs in the background, read by id (Appendix F names its words). `start(kind, work)` runs `work(report)` on a daemon thread and returns the job's view; `get(id)` returns a snapshot under a lock. The view is `{id, kind, state, step, done, total, progress, line, result}` with `state` one of `running`, `finished` or `stopped`. Jobs live for the process's life and are never capped or pruned.
- [ ] Edit `HO/bring_in.py`. Split the fast refusals out of `_bring_in` into `refusal_before_copy(old, folder, place_refusal)` (old folder gate, running host, place refusal, overlap, a folder brought in from another old folder), called by the route and by `_bring_in`, so one rule serves both. Add a `progress` callback threaded through `_carry` and the switch (step name, files and bytes copied of total, items switched of total). Turn any `OSError` before the unfinished marker into `Refused` with `_reason`. Add one long-path helper used by `copy_file`, `sha256_of`, `listing`, `_walk`, `_survey`, `_first_change` and the target `mkdir` (the `\\?\` prefix on Windows for an absolute path, the path unchanged elsewhere), with report text that never shows the prefix. Count distinct `root_id` per kind in `_kinds_brought_in`, and count test-run items as distinct roots in the report and in `recheck_at_start`.
- [ ] Edit `HO/first_start.py`. `POST /api/first-start/bring-in` runs the fast refusals (409), then starts the job and answers 202 with its view. Add `GET /api/first-start/jobs/{job_id}` and `POST /api/first-start/handover`. `offer()` takes `places`, so each drive row and the default folder carry `warning`; each choice's answer carries `warning` for the chosen folder. `first_start_app` takes an `on_handover` callback.
- [ ] Edit `HO/__main__.py`. `first-start --serve` probes its port first (exit 2 when taken), passes `on_handover` to stop the server gracefully, prints the handover line last and exits 0, or exits 1 when it stopped with no handover. `serve`, `start`, `status` and `stop` exit 3 when no QMX folder is found, and also when the folder named holds old data (`_old_hint`).
- [ ] Edit `LB/migrate/from_library_b.py`. `import_library_b` and `switch_over` take an optional keyword `on_item(done, total)`, default None, so `scripts/data/switch_library.py`, `scripts/probes/data/p_rehearse.py` and `scripts/live/library/libm_lanes.py`, which pass only `redactor=`, are unchanged.
- [ ] Edit `QA/qmx-host/tests/test_bring_in.py` (the route test now reads the job, and the old-folder `serve` test expects exit 3) and add `QA/qmx-host/tests/test_jobs.py`, `QA/qmx-host/tests/test_handover.py` and `QA/qmx-library/tests/test_switch_progress.py`.

**Build.**

- [ ] Write the job registry and its tests first, then move the route onto it, then the handover. Each step ends with its own test run.
- [ ] The bring-in job's `progress` is `{files_copied, files_total, bytes_copied, bytes_total, items_switched, items_total}`, and its `step` is one of the plain steps "listing your old folder", "copying", "checking the copy", "moving your Library into the new one" and "opening the new folder's stores", one per stage the unfinished marker already names. Its `result` is the report document the route answers today (`finished`, `folder`, `report`, `facts`).
- [ ] A job's `line` is empty while it runs; a stopped job's line is the refusal or the report's why, one sentence, never a traceback or an exception class name alone.
- [ ] `POST /api/first-start/handover` answers `{folder, port}` when the pointer names a folder QMX would start on (`resolve(drives=[])` finds it and `old_library(layout.home)` is None) and no bring-in job is running, then calls `on_handover`. Anything else answers 409 with its line.
- [ ] Prove the one fact the handover rests on. A test serves the card with `uvicorn.Server`, posts the handover, and asserts the client got the 200 answer before `server.run()` returned.

**You see.**

- [ ] On a scratch profile, `python -m qmx_host first-start --serve --port <p>` with a synthetic old folder answers `POST /api/first-start/bring-in` with 202 and a job id, `GET /api/first-start/jobs/<id>` shows `files_copied` rising, then `items_switched`, then `finished`. After `POST /api/first-start/handover` the process prints `{"handover": {"folder": "<folder>", "port": <p>}}` as its last line and exits 0, and `python -m qmx_host serve --home <folder> --port <p>` answers `/api/health` on the same port.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A job that raises ends `stopped` with one line; two readers see the same snapshot; a refused bring-in answers 409 before any job exists; a second bring-in answers 409 naming the first; an `OSError` from `shutil.disk_usage` and from `resolve(create=True)` each end the job with one line and no marker; a 300-character path under `environments/` copies and hashes; the report of a three-item Library, one item with two versions and one two-version test item, says 3 items and 1 item made by test runs; the drive row of a removable drive carries the warning; handover answers 409 before a choice and the folder after one; `serve` with no folder and with the old folder exit 3; `switch_over` without `on_item` behaves as at the root. Run the host and Library suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The host and Library suites at parent and head. Save `p1-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. The card server on a scratch profile brings in a synthetic 2,000-item old folder, polled every second. Save `p1-job.log`. Pass when the POST answers 202 within 1 s, every poll answers within 1 s with counts that never fall, and the job ends `finished` with the report.
- [ ] Lane 3. The same with one file at a 300-character path under `environments/`. Save `p1-longpath.log`. Pass when the job finishes and the copy's sha256 matches the old file's.
- [ ] Lane 4. After lane 2, post the handover, then run `serve --home <folder> --port <same>`. Save `p1-handover.log`. Pass when the card exits 0, its last stdout line names the folder and port, and the host answers `/api/health` with the bearer on that port within the start budget `HO/host.py` uses (`START_S`).
- [ ] Lane 5. Kill the card process during the copy, then start it again. Save `p1-killed.log`. Pass when the folder reads unfinished by name, a snapshot of the old folder matches the one taken before, and the old job id answers 404 with its line.
- [ ] Lane 6. A target whose drive check raises `OSError` (patched `shutil.disk_usage`). Save `p1-early-error.log`. Pass when the job ends `stopped` with one line and the server log holds no traceback.
- [ ] Lane 7. The card with a fake removable drive (`Places.drive_type` answering 2). Save `p1-removable.log`. Pass when the drive row and the choice's answer carry the warning line.
- [ ] Lane 8. `serve` and `start` with no folder, then pointed at the old folder. Save `p1-exit3.log`. Pass when each exits 3 with its one line.
- [ ] Lane 9. The card started on a port already in use, then a handover posted before any choice. Save `p1-refusals.log`. Pass when the first exits 2 with the port named and the second answers 409.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, then remove the throwaway folders and list processes. Save `p1-processes.log`. Pass when every exit code is 0 and nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for a 2,000-item bring-in at parent (the CLI `bring-in`) and at head (the CLI and the job), and the job read's milliseconds while it copies.
- [ ] Probe. Lane 2's folder, brought in three times at each side, parent and head interleaved.
- [ ] Baseline. Record the parent's median first (LF4 measured 92.7 s for 2,000 items).
- [ ] Rule. Head's median is within 5 % of the parent's, or the PR fails. The job read is under 50 ms at its median, an absolute budget, because the parent has no job read.

**Review gate.** None. P1 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on `build/md3`; P2a joins it by a merge commit.

## Make every resumed run land (P2a)

Triage C5 and C6 (B120a, B121b, L58a to L58c). Rulings 141 and 142. Today a resumed run's summary is rebuilt from its last summary (`E/service/runs.py:425-445` `summarize_again`), so a run that died before its first summary returns None and its records never leave its run ref (MD1 lane 6 showed 2 clippings on the run ref, 0 on `main`). The cancel path does the same (`E/control_door.py` `_summarize`, near line 583). `run_created` records the mode, the item and the content hash but not the published version's `object_id` or who started the run (`E/runner.py:816-836`). A test run's memory rows sit on `refs/runs/<run_id>` (`MM/rows.py:56-60`) but `_archive_samples` skips every kind but `artifact` (`LB/adapter.py:378-386`), so recall can return a test run's note. Done when a run's summary is built from its `run_created` facts (item, version, mode, fake, starter), so a resume and a cancel of a run that died before its first summary both write the summary and land its records; a test or fake run's memory rows are archived with its other samples; and `check_built` and recall leave out what a test or fake run wrote. Edge cases it must survive. A run created before this PR (no `object_id` in `run_created`) falls back to its last summary, and with none it logs one line naming the run and why it cannot land, never a crash. A second resume of a landed run lands nothing twice. A fake live run still lands nothing. A failed live run's records stay visible, since they are his. A subworkflow child run is summarized only through its parent, as today. A test run that died and is never resumed stays visible until he resumes or cancels it, and both now land its summary.

**Depends on.** The root `629bea16`.

**Files.**

- [ ] Edit `E/runner.py` (`Engine.start` and `Run` take `object_id` and `started_by`, and `create` records both in `run_created`) and `E/service/runs.py` (`run_bundle` passes them; one `run_start(events)` reads the facts from `run_created`; `summarize_again` uses it and falls back to the last summary only for an older ledger).
- [ ] Edit `E/control_door.py` (`_summarize`, the cancel path, uses `run_start` too).
- [ ] Edit `LB/adapter.py` (`_archive_samples` archives `memory-row` heads on the run ref too).
- [ ] Edit `MM/engine.py` (`check_built`'s `built` rows and recall leave out rows whose `source_run_ids` name only test or fake runs). `E/ports/memory.py` is the port only and does not change.
- [ ] Add tests in the engine, Library and memory packages, against `EngineLibraryAdapter(Store.open(tmp))`, in new files `test_resume_lands.py` and `test_test_run_memory.py`.

**Build.**

- [ ] Reproduce first. A test kills the engine after the write node's attempt and before the first summary, resumes, and fails on the parent because no summary is written.
- [ ] Add the two `run_created` fields and `run_start`, then switch both callers onto it.
- [ ] Reproduce the memory low (a test run's `built` note counted by `check_built`, and its note returned by recall), then archive and filter.
- [ ] Prove the one fact. Older ledgers lack the two fields, so a test seeds a `run_created` without them and shows the fallback path.

**You see.**

- [ ] On a throwaway folder, "Clippings into research" killed before its first summary and resumed puts both clippings on `main`, and the run's view reads its summary.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A resumed run with no summary writes one and lands; a cancelled one does too; a second resume lands nothing new; an older `run_created` without the fields resumes by its last summary or logs one line; a test run's memory rows are archived at its summary; `check_built` ignores a test run's `built` row and still counts a live run's; recall leaves out a test run's note. Run the engine, Library, memory and control suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The four suites at parent and head. Save `p2a-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. MD1's lane 6 again. Kill the engine after the write node's attempt and before the first summary, then resume. Save `p2a-resume.log`. Pass when the summary exists and both clippings are on `main`; the parent records 0 on `main`.
- [ ] Lane 3. A test run killed the same way, then resumed. Save `p2a-test-resume.log`. Pass when its samples and memory rows are archived and Library search leaves them out.
- [ ] Lane 4. A run killed the same way, then cancelled. Save `p2a-cancel.log`. Pass when the cancelled run has its summary.
- [ ] Lane 5. A test run writes a `built` note, then `check_built` on its key. Save `p2a-built.log`. Pass when it returns nothing, and a live run's note on the same key is returned.
- [ ] Lane 6. Recall after a test run's note. Save `p2a-recall.log`. Pass when recall does not return it.
- [ ] Lane 7. Resume the run of lane 2 a second time. Save `p2a-twice.log`. Pass when `main` still holds each clipping once.
- [ ] Lane 8. A ledger made at the parent with a run that died early, resumed at head. Save `p2a-old-ledger.log`. Pass when the run resumes and either lands by its last summary or logs its one line, with no traceback.
- [ ] Lane 9. Gates in the touched packages and `tools/secret_scan.py`. Save `p2a-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the throwaway folders and list processes. Save `p2a-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from the resume call to the summary on `main` for lane 2's run, and seconds for a normal 50-clipping run at both sides.
- [ ] Probe. Lane 2 three times at head; the 50-clipping run three times at parent and head, interleaved.
- [ ] Baseline. Record the parent's 50-clipping median first. The parent never lands lane 2's run, so that number is recorded as never.
- [ ] Rule. The 50-clipping run at head is within 5 % of the parent, or the PR fails. Lane 2's resume reaches `main` within 10 s, an absolute budget.

**Review gate.** None. P2a is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Joined onto P1 by a merge commit (the two share no file).

## Give a live run its inputs from REST and from its trigger (P2b)

Triage C7 (B120b). Rulings 141 and 142, and his rule that what he can configure is editable from the UI. Today `POST /api/workflows/{workflow_id}/run` takes no body (`QX/service.py:1673-1676`, `E/control_door.py:480-491`), a trigger row stores no inputs (`E/triggers/rows.py`), and a fire's inputs are only the trigger block and the delivery payload (`E/triggers/ticker.py:491-505`), so "Clippings into research" cannot be given its folder in a live run. The workflow's `inputs` is a JSON Schema (`E/definition/model.py:220`, `E/templates/clippings-into-research/definition.json:5-11`), and the engine already ships `jsonschema` (`E/nodes/llm.py:30`). Done when the run route's body is the run's inputs; a trigger row stores inputs, set at create, that each fire passes under its delivery payload; every live start (REST, trigger, run now, webhook) checks the declared inputs against the workflow's `inputs` schema and refuses `inputs_invalid` naming the field before a run is created; and the ledger gains the column by an additive step that an older engine still opens. Edge cases it must survive. An empty body runs with no inputs, as today. The engine's own keys (`trigger`, `continuity`) are added after the check and never fail it. A webhook payload key wins over a stored input of the same name. A trigger created without a required input is refused at create. A schema that is empty checks nothing. A version 4 ledger upgrades with its pre-change copy and every trigger keeps `{}`; a version 5 ledger opens in the parent engine (`min_reader` stays 3). An agent's confirm card for a run carries the inputs it was asked with.

**Depends on.** P2a (both edit `E/control_door.py` and `E/service/runs.py`).

**Files.**

- [ ] Edit `QX/service.py` (`workflows_run` takes `inputs`, and the engine door protocol's `workflows_run` near line 2073 matches).
- [ ] Edit `E/control_door.py` (`workflows_run` passes the inputs and its confirm card carries them; `TriggerIn` gains `inputs`; `workflow_triggers_create` checks and stores them).
- [ ] Edit `E/service/runs.py` (`run_bundle` checks the declared inputs against the workflow's schema before `engine.start`).
- [ ] Edit `E/triggers/rows.py` (`Trigger.inputs`, its column in the row list near line 194, `create`) and `E/triggers/ticker.py` (`_inputs` merges stored inputs, then the payload, then the engine's keys).
- [ ] Edit `E/ledger/migrations.py` (step 5, `ALTER TABLE triggers ADD COLUMN inputs TEXT NOT NULL DEFAULT '{}'`; `TRIGGER_COLUMNS` stays as it is, because step 4's copy of a version 3 ledger uses it) and `HM/stores.py` (the engine's `Version(4, 3)` becomes `Version(5, 3)`).
- [ ] Add tests in the engine, control and home packages, in new files `test_run_inputs.py` and `test_trigger_inputs.py`.

**Build.**

- [ ] Reproduce first. A REST run of "Clippings into research" with a folder in the body fails on the parent because the folder never reaches `run_input`.
- [ ] Add the check, the route body, the trigger column and the merge, each with its test.
- [ ] Prove the one fact. A version 5 ledger written at head opens in the parent's `migrate` without a refusal, run by a test against the parent's `STEPS` copied into the test.

**You see.**

- [ ] `POST /api/workflows/clippings-into-research/run` with the body `{"folder": "<scratch folder>"}` starts a run whose `run_input` holds that folder, and its clippings land.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A REST run carries its body; an empty body still runs; `{"folder": 5}` is refused `inputs_invalid` naming `folder` with no run created; a trigger's stored inputs reach its fire under the trigger block; a webhook payload overrides a stored key; a create missing a required input is refused; step 5 upgrades a version 4 ledger and keeps every row; the parent opens a version 5 ledger. Run the engine, control and home suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The three suites at parent and head. Save `p2b-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host runs "Clippings into research" over REST with a scratch folder of two clippings. Save `p2b-rest.log`. Pass when `run_input` holds the folder and both clippings land; the parent records that the folder never arrives.
- [ ] Lane 3. A trigger created with the folder, fired by run now. Save `p2b-trigger.log`. Pass when the run's inputs hold the stored folder and the trigger block.
- [ ] Lane 4. A REST run with `{"folder": 5}`. Save `p2b-invalid.log`. Pass when it is refused by name and no run exists.
- [ ] Lane 5. A ledger made at the parent, opened by a head host. Save `p2b-migrate.log`. Pass when it reads version 5, `backups/` holds the pre-change copy, and every trigger's inputs read `{}`.
- [ ] Lane 6. The ledger of lane 5 opened again by the parent engine. Save `p2b-older-reader.log`. Pass when it opens and fires a trigger.
- [ ] Lane 7. A webhook delivery whose payload names `folder` on a trigger that stores another folder. Save `p2b-webhook.log`. Pass when the run reads the payload's folder.
- [ ] Lane 8. An agent asks for a run with inputs. Save `p2b-card.log`. Pass when its confirm card's body carries the inputs.
- [ ] Lane 9. Gates in the touched packages and `tools/secret_scan.py`. Save `p2b-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the throwaway folders and list processes. Save `p2b-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds from `POST /api/workflows/<id>/run` to its answer, without inputs at parent and head, and with inputs at head.
- [ ] Probe. Twenty calls at each side on lane 2's host with a fake model, interleaved.
- [ ] Baseline. Record the parent's median first.
- [ ] Rule. Head without inputs is within 20 ms of the parent's median, or the PR fails. Head with inputs is under 50 ms more than head without, an absolute budget for the check.

**Review gate.** None. P2b is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the wave 1 tip; P3 joins it by a merge commit.

## Make cTrader work out of the box and say why a read failed (P3)

Triage C8 to C11 (B78, B76, B69, L39a, L39b, with L38 folding in). Ruling 135 (a key that can trade live money is never kept on This PC) and his rule that he never sees a token. Today `compiled` refuses a connection with no `protocol_path` and `protocol_tag` (`BR/service.py:60-72`), the model defaults both to empty (`BR/models.py:69-70`), and the sign-in refuses `grant_unchecked` until he sets them (`HO/venue_session.py:536-551`); the only pinned descriptor set is the test fixture `QA/qmx-broker/tests/fixtures/tag91.pb`, under Spotware's MIT licence beside it. `join_ctrader_app` writes `qmx/read/ctrader-app` with keyring's `set_password` (`BR/credentials.py:205`), so a changed secret leaves the old pair in Windows' companion entry. `refresh_tokens` has no production caller (`BR/oauth.py:184-199`), and `open_adapter` reads the stored pair without looking at its expiry (`BR/service.py:145-160`). A failed read says only "Broker read failed" (`BR/service.py:290-296`), which swallows the named lines `open_adapter` already raises. Done when QMX ships the pinned descriptor set (tag 91) and uses it when a row names none; joining the app id and secret writes through `CredentialManager.replace`, so one copy remains; an access token at or past its expiry is refreshed from its refresh token before the read, and the new pair replaces the old one in the key store before the read goes on; and a failed read says which of not signed in, signed in on another machine, protocol files, ended sign-in, the exchange refusing the key, or the network. Never print a token. No token, refresh token, client secret, authorization code or token URL with its query appears in a log line, an exception message, a report, a job line or a test's captured output, and lane 8 greps for the fake values. Live refusal (ruling 135). A refreshed grant goes through the same `authenticate` check as a fresh one, and a grant that can trade a live account is refused by name and its pair deleted; the refresh never asks for the `trading` scope. Edge cases it must survive. A row that names a path that does not exist is refused by name. A row that names a tag without a path is refused unless the tag is the shipped one. A refresh refused by cTrader (revoked grant) says the sign-in has ended and to sign in again, and keeps nothing. A new pair that cannot be written says so and to sign in again, and the read does not go on with a pair the store does not hold. Two processes refreshing at once converge, because a refresh refused for a dead refresh token reads the store again and uses a pair another process wrote. A join whose primary already matches still removes a stale companion. A row with no expiry recorded (`expires_at` 0) is never refreshed on time alone.

**Depends on.** The wave 1 tip (P1 and P2a joined). It shares no file with P2b.

**Files.**

- [ ] Create `BR/protocol/openapi-91.pb` (a byte copy of `QA/qmx-broker/tests/fixtures/tag91.pb`) and `BR/protocol/Spotware-LICENSE.txt`. Edit `QA/qmx-broker/pyproject.toml` only when `uv build --wheel` leaves them out of the wheel.
- [ ] Edit `BR/service.py` (`compiled` uses the shipped set when a row names none; `open_adapter` refreshes a due pair and writes it through the key store; `read` maps each known failure to its line and anything else to "Broker read failed (<class name>)").
- [ ] Edit `BR/credentials.py` (`join_ctrader_app` writes through `CredentialManager.replace` and removes a stale companion) and `BR/oauth.py` (`Tokens` says whether it is due at a given time).
- [ ] Edit `HO/venue_session.py` (`one_session` reads with the shipped set when a row names none; `grant_unchecked` stays only for a read that fails).
- [ ] Add tests in the broker and host packages with a fake key store, a fake transport and a fake token endpoint, in new files `test_protocol_default.py`, `test_refresh.py` and `test_read_reasons.py`.

**Build.**

- [ ] Reproduce each finding first with its failing test (a row with no protocol fields, a changed secret on a store that keeps a companion, an expired pair, a swallowed reason).
- [ ] Ship the set, then the join, then the refresh, then the reasons.
- [ ] Prove the one fact. The shipped bytes are the fixture's bytes (equal sha256), so the transport tests that already pass on the fixture prove the shipped set.

**You see.**

- [ ] On a throwaway folder with fakes, a cTrader connection with no protocol fields signs in and reads its account, an expired pair is refreshed once, and a read with no sign-in says "Sign in to cTrader on This PC first".

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. 

- [ ] The shipped set compiles; a missing path and a stray tag are refused by name; a join with a changed secret leaves one copy and no companion; a due pair is refreshed and replaced before the read; a revoked refresh says the sign-in ended; a failed write stops the read with its line; a refreshed live grant is refused and deleted; each reason reads its own line; no fake secret value appears in any captured output. Run the broker and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The broker and host suites at parent and head. Save `p3-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. The PC sign-in through `HO/venue_session.py` with a fake consent code, a fake token endpoint and a fake transport, on a row with no protocol fields. Save `p3-signin.log`. Pass when the accounts are read on the shipped set and no `grant_unchecked` appears; the parent refuses `grant_unchecked`.
- [ ] Lane 3. An `account_state` read with a stored pair whose expiry has passed. Save `p3-refresh.log`. Pass when the fake endpoint saw one refresh, the fake store holds the new pair only, and the read answers with `environment: demo`.
- [ ] Lane 4. One read for each failure (no pair, homed on another machine, a missing protocol path, a revoked refresh, the network down). Save `p3-reasons.log`. Pass when each says its own line and none says only "Broker read failed".
- [ ] Lane 5. The join with a changed secret on a fake store that keeps a companion. Save `p3-join.log`. Pass when one copy holds the new pair and no companion is left.
- [ ] Lane 6. A refresh whose new grant reports a live account. Save `p3-live.log`. Pass when the read is refused by name and the pair is deleted.
- [ ] Lane 7. Two broker services refresh the same due pair at once, against a fake endpoint that kills a used refresh token. Save `p3-race.log`. Pass when both reads answer and the store ends with one pair.
- [ ] Lane 8. Grep every lane log, the host log and captured stderr for the fake access token, refresh token, client secret and code. Save `p3-leak.log`. Pass when none appears.
- [ ] Lane 9. `uv build --wheel` in `QA/qmx-broker/`, then list the wheel. Save `p3-wheel.log`. Pass when the descriptor set and the licence are in it.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, then remove the throwaway folders and list processes. Save `p3-processes.log`. Pass when every exit code is 0 and nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds for one `account_state` read through the fake transport with a pair that is not due, at parent (with the fixture path set) and head (with none), and with a due pair at head.
- [ ] Probe. Lane 3's read twenty times at each side, interleaved.
- [ ] Baseline. Record the parent's median first.
- [ ] Rule. Head's not-due read is within 20 ms of the parent's median, or the PR fails. A due read at head is under 2 s against the fake endpoint, an absolute budget.

**Review gate.** None. P3 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Joined onto P2b by a merge commit (the two share no file).

## Run template install as a job with progress (P5)

Triage C13 (B8). Ruling 106 (no QMX limit; an install takes as long as its models do). Today `POST /api/templates/install` awaits the whole install in one request (`HO/door.py:321-342`), which with real models can run many minutes, and the engine CLI posts to it with no timeout and reads the list it answers (`E/__main__.py:256-276`). Done when the route starts a job on P1's registry and answers 202 with its view at once; `GET /api/templates/install/{job_id}` reads which template it is on, how many of how many are done, and each finished row; the CLI posts, then reads the job until it ends and prints the same rows as today. Edge cases it must survive. An unknown template id is refused 404 by name before any job starts. A template whose test run fails is a `test failed` row in a `finished` job, not a stopped job. A second install while one runs answers 409 naming the running job, because two installs would write the same drafts. A host that stops mid install loses the job, and a rerun is idempotent (the finished templates read `unchanged`). The install still runs on the engine's loop in an empty context, so its test runs inherit no request principal.

**Depends on.** P1 (`HO/jobs.py`).

**Files.**

- [ ] Edit `HO/door.py` (`templates_router` owns a `Jobs` registry; `POST /api/templates/install` answers 202; add `GET /api/templates/install/{job_id}`; each template is one `install_one` hop on the engine loop, so the job reports between them).
- [ ] Edit `E/__main__.py` (`through_host` reads the job until it ends; still no timeout).
- [ ] Edit `QA/qmx-host/tests/test_templates_route.py` and add the engine CLI case in a new `QA/qmx-engine/tests/test_install_through_host.py`.

**Build.**

- [ ] Reproduce first. A test asserts the POST answers before a slow fake install finishes, and fails on the parent.
- [ ] Move the route onto the registry, then the CLI.
- [ ] Prove the one fact. `install` is a loop over `install_one` (`E/templates/install.py:38-40`), so one hop per template gives the same rows in the same order; a test compares the job's rows with `install()`'s on the same catalogue.

**You see.**

- [ ] With a head host on a throwaway folder, `python -m qmx_engine templates install --home <folder>` prints a line per template as before, and `GET /api/templates/install/<id>` showed `done` rising from 0 to 3 while it ran.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The POST answers 202 before a slow install ends; the job's rows equal `install()`'s; an unknown id is 404 with no job; a failed test is a row; a second install is 409; the CLI prints the parent's rows. Run the host and engine suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The host and engine suites at parent and head. Save `p5-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host installs three templates with a fake model, polled every second. Save `p5-job.log`. Pass when the POST answers within 1 s and `done` rises to 3 with three rows.
- [ ] Lane 3. The engine CLI install against the same host. Save `p5-cli.log`. Pass when it prints the rows the parent prints for the same templates.
- [ ] Lane 4. An install naming an unknown template. Save `p5-unknown.log`. Pass when it is 404 by name and no job exists.
- [ ] Lane 5. A template whose test fails. Save `p5-failed-test.log`. Pass when the job ends `finished` with a `test failed` row.
- [ ] Lane 6. A second install while lane 2's runs. Save `p5-second.log`. Pass when it is 409 naming the first job.
- [ ] Lane 7. Stop the host mid install, start it, read the old job, then install again. Save `p5-restart.log`. Pass when the old id is 404 with its line and the rerun reads `unchanged` for the finished templates.
- [ ] Lane 8. Job reads during lane 2's install. Save `p5-reads.log`. Pass when every read answers within 1 s.
- [ ] Lane 9. Gates in the touched packages and `tools/secret_scan.py`. Save `p5-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the throwaway folders and list processes. Save `p5-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for the three-template install end to end, and milliseconds to the POST's answer.
- [ ] Probe. Lane 2 three times at parent and head, interleaved.
- [ ] Baseline. Record the parent's median install first.
- [ ] Rule. Head's install is within 5 % of the parent's, or the PR fails. The POST answers in under 1 s at head, an absolute budget, because the parent answers only at the end.

**Review gate.** None. P5 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the wave 2 tip; P6 joins it by a merge commit.

## Make the host name what did not open (P6)

Triage C14 and C15 (B52, L50). Rulings 141 and 142, and his rule that a refusal says why in plain words. Today `market_door` prints its reason to stderr and returns None (`HO/host.py:955-977`), and the host then mounts no `/api/data/*` route (`HO/host.py:720-721`), so every data call answers 404. `serve_forever` catches only `HostRunning` and `PlaceRefused` (`HO/host.py:225-231`), so a store refused while the engine or the Library opens escapes as a traceback. Done when a shut price door answers every `/api/data/*` call with 503 and its reason (`{code, detail}`, the shape the door's own refusals use); and a `StoreRefused` or `LibraryRefused` raised while the host opens prints one line, `QMX did not start: <why>`, and exits 2, the code `HO/__main__.py` already uses for a refused store (Appendix E). Edge cases it must survive. An open door's routes answer as today. The closed-door route sits behind the same bearer and door as the open one. `start` in the background reports its child's failure and the one line is in `logs/host.log`. A refusal never prints a secret or a bearer. `HostRunning` and `PlaceRefused` keep exit 1.

**Depends on.** The wave 2 tip. It shares no file with P5.

**Files.**

- [ ] Edit `HO/host.py` (`market_door` returns the door or its reason; a `closed_market_router(reason)` on `/api/data/{rest:path}` for GET and POST; `serve_forever` catches the two refusals).
- [ ] Add tests in new files `QA/qmx-host/tests/test_closed_door.py` and `QA/qmx-host/tests/test_open_refusals.py`.

**Build.**

- [ ] Reproduce first. One test shows the 404 on a `[data]` the door cannot use; one shows the traceback from a refusal injected into the engine's ledger open.
- [ ] Add the closed-door router, then the catch.
- [ ] Prove the one fact. The closed router is appended to `answering` exactly where `market_router` is, so `compose` mounts it behind the bearer; a test calls it with no bearer and gets 401.

**You see.**

- [ ] A head host on a throwaway folder with an unusable `[data]` answers `GET /api/data/instruments` with 503 and the reason the log names.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A shut door answers 503 with its reason on a GET and a POST route; with no bearer it answers 401; an open door answers 200; an injected `StoreRefused` and `LibraryRefused` each print one line and return 2; `HostRunning` still returns 1. Run the host suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The host suite at parent and head. Save `p6-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host with a `[data]` the door cannot use, then `GET /api/data/instruments`. Save `p6-instruments.log`. Pass when it answers 503 with the reason; the parent answers 404.
- [ ] Lane 3. `POST /api/data/read` on the same host. Save `p6-read.log`. Pass when it answers 503 with the same reason.
- [ ] Lane 4. A host whose engine ledger open is refused (a ledger file that is not a ledger, placed after the start check). Save `p6-engine-refused.log`. Pass when stderr is one line starting "QMX did not start" and the exit code is 2.
- [ ] Lane 5. A host whose Library open is refused. Save `p6-library-refused.log`. Pass when stderr is one line and the exit code is 2.
- [ ] Lane 6. A head host with a healthy door. Save `p6-open.log`. Pass when `GET /api/data/instruments` answers 200 as at the parent.
- [ ] Lane 7. `start` in the background on lane 4's folder. Save `p6-start.log`. Pass when it reports the failed start and `logs/host.log` holds the one line.
- [ ] Lane 8. The closed-door route with no bearer. Save `p6-bearer.log`. Pass when it answers 401.
- [ ] Lane 9. Gates in the host package and `tools/secret_scan.py`. Save `p6-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the throwaway folders and list processes. Save `p6-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from `serve` to the first 200 on `/api/health` with a healthy door.
- [ ] Probe. Lane 6's start three times at parent and head, interleaved.
- [ ] Baseline. Record the parent's median first.
- [ ] Rule. Head is within 5 % of the parent's median, or the PR fails.

**Review gate.** None. P6 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Joined onto P5 by a merge commit (the two share no file).

## Refuse a demo row on an exchange with no demo mode (P4)

Triage C12 (B118a, B119). His rule that he never reads a demo number as his own, and ruling 106. Today a CCXT demo connection calls `exchange.set_sandbox_mode(True)` at read time (`BR/service.py:138-139`), which raises `TypeError` on 54 exchanges in ccxt 4.5.85 (kraken, coinbase and 52 more, listed in `BACKLOG.md` line 119), so such a row can be saved and then never read. The settings write parses rows with `BrokerSettings` and hides any parse error behind one generic line (`QX/service.py:813-821`). Done when one check, `demo_refusal(exchange)`, runs what the read path runs on a fresh exchange object with no keys and no network, and names an exchange with no demo mode; the `brokers` and `connections` settings write refuses a CCXT demo row on such an exchange by name ("<exchange> has no demo mode in CCXT, so QMX cannot read a demo account there; use a live read-only key or another exchange"), and the read path says the same line instead of a `TypeError`. Edge cases it must survive. The check is not a model validator, so a row saved before this PR still parses and the rest of his settings still load; that row reads with the named line. A live row is not checked. A row switched from live to demo is checked at that write. An unknown exchange id keeps its own refusal. A ccxt upgrade changes the answer by itself, because nothing is kept by hand. The check opens no socket.

**Depends on.** P3 (`BR/service.py`) and P2b (`QX/service.py`), so it branches from the wave 3 tip.

**Files.**

- [ ] Create `BR/sandbox.py` (`demo_refusal`, cached per exchange id for the process's life).
- [ ] Edit `BR/service.py` (`open_adapter` asks `demo_refusal` before `set_sandbox_mode`) and `QX/service.py` (the settings write near line 813 refuses by name with `ControlError("invalid_brokers", <line>)`).
- [ ] Add tests in new files `QA/qmx-broker/tests/test_sandbox.py` and `QA/qmx-control/tests/test_demo_rows.py`.

**Build.**

- [ ] Reproduce first. A test saves a kraken demo row and reads it, and fails on the parent with the generic line.
- [ ] Add the check, then the write refusal, then the read line.
- [ ] Prove the one fact. With ccxt pinned at 4.5.85 (`QA/qmx-broker/pyproject.toml`), a test computes `demo_refusal` over `ccxt.exchanges` and asserts the set is the 54 names of `BACKLOG.md` line 119.

**You see.**

- [ ] Saving a kraken demo row in Settings answers 400 with the named line, and nothing is saved.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The computed set equals the 54 names; a binance demo row saves; a kraken live row saves; a kraken demo row is refused at write; a kraken demo row already in `settings.toml` parses and reads with the line; a patched socket that raises on connect does not stop the check. Run the broker and control suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The broker and control suites at parent and head. Save `p4-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host saves a kraken demo row through `PUT /api/settings/connections`. Save `p4-refused.log`. Pass when it answers with the named line and the row is not saved; the parent saves it.
- [ ] Lane 3. A binance demo row through the same route. Save `p4-binance.log`. Pass when it is saved.
- [ ] Lane 4. A kraken demo row written into `settings.toml` by hand, then a broker read. Save `p4-old-row.log`. Pass when settings load and the read says the named line.
- [ ] Lane 5. A kraken live row. Save `p4-live.log`. Pass when it is saved.
- [ ] Lane 6. A row switched from live to demo on kraken. Save `p4-switch.log`. Pass when the switch is refused by name.
- [ ] Lane 7. The 54-name comparison script. Save `p4-list.log`. Pass when the computed set equals the list.
- [ ] Lane 8. The check with sockets patched to raise. Save `p4-offline.log`. Pass when it answers.
- [ ] Lane 9. Gates in the touched packages and `tools/secret_scan.py`. Save `p4-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the throwaway folders and list processes. Save `p4-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds for a connections settings write holding one CCXT demo row, first in a process and again.
- [ ] Probe. Lane 3's write ten times in fresh processes and ten times in one process, at parent and head, interleaved.
- [ ] Baseline. Record the parent's medians first.
- [ ] Rule. A repeat write at head is within 50 ms of the parent's median, or the PR fails. A first write at head is under 3 s, an absolute budget, because it may import ccxt.

**Review gate.** None. P4 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the wave 3 tip.

## Close the program

- [ ] Every PR is stacked with a CLEAN verdict, or skipped with its reason in `RESUME.md`.
- [ ] Closing lanes (V, triage C16), run by the coordinator at the stack tip on fresh throwaway folders, with no PR.
  - [ ] LF5 lane 3. `send_to = "this-pc"` with nothing listening. Save `evidence/ls-v/lf5-this-pc.log`. Pass when the chat still answers and the failed sends are counted, not raised.
  - [ ] LF5 lane 4. One downloader run on a fresh folder with no `[data] root`. Save `evidence/ls-v/lf5-download.log`. Pass when it writes under the folder's `market`.
  - [ ] One pass of each launch journey on a fresh scratch profile, in order. First start new, then handover, then the host; first start bring-in of a synthetic old folder, then handover, then the host; open an existing folder; a live "Clippings into research" run with its folder over REST; a template install job; a cTrader sign-in and read on fakes; a shut price door. Save `evidence/ls-v/journeys.log`. Pass when each ends in its expected state with no traceback in any log.
- [ ] `just ci` at the stack tip exits 0, or every failure is a named environmental gap.
- [ ] `QUEUE.md` moves on to its next item, the local backup and restore program (G1).

## Appendix A. Prototype evidence

- No prototype was run. Every fact in this plan was read in the code at `629bea16` in the read-only checkout `D:/Temp/ci6-check`, with nothing executed there, because a CI run may be using it. The file and line references in each preamble are those reads.
- Facts that changed the triage's file lists. The bring-in's version counting is in `HO/bring_in.py` (`_kinds_brought_in`, `_made_by_tests`), not in `from_library_b.py`, which P1 touches only for the progress hook. The memory filter lives in `MM/engine.py`, not in `E/ports/memory.py`. P2a and P2b share `E/control_door.py` and `E/service/runs.py`, and P4 shares `BR/service.py` with P3 and `QX/service.py` with P2b, so those pairs cannot run side by side as the triage proposed. P2b also needs `HM/stores.py` for the engine's version. P5 needs `E/__main__.py`, whose `through_host` reads the install route's answer.
- Facts the builders prove by running code (each PR's Build block). The handover answer reaches the client before the card's server stops (P1). A version 5 ledger opens in the parent engine (P2b). The shipped descriptor set is the fixture byte for byte (P3). The computed no-demo set equals the 54 names at ccxt 4.5.85 (P4). Job rows equal `install()`'s rows (P5).
- Unproven until lanes run. That Windows lets `serve` bind the card's port at once after the card exits (P1 lane 4). Which code path writes a test run's `built` row that `check_built` counts (P2a reproduces it first). That `uv_build` puts `BR/protocol/` in the wheel without a `pyproject.toml` change (P3 lane 9).

## Appendix B. Not in this program

- **G1, local backup and restore, is the next program.** `POST /api/first-start/restore` answers 501 (`HO/first_start.py:390-391`, `RESTORE_LATER`), and no quick undo, second-drive copy or restore exists. It is design 62 phase 2 (LF8 and LF9), whose defaults design 62 C2 already decides. It is a program of its own, not a PR here.
- The triage's 99 LATER lines and 52 OUT lines stay in `BACKLOG.md` and `lows.md`. Among them B111 (the bring-in imports private `qmx_home` names) is a rename that changes no behaviour; it stays out to keep P1 to its launch gaps. L60a (an older one-shot report keeps its inflated count) stays LATER, because P1 fixes the count for every bring-in from now on and no bring-in has run on his PC.
- The triage's idea of checking `urls['test']` for P4 is replaced by running the same call the read path runs, because the failure seen on kraken is a `TypeError`, which a URL check would not predict.
- How the desktop app's window gets the host's bearer belongs to the desktop packet (engine AD-48). The backend side is fixed (the keyring entry `qmx/control-token`, read as `HO/host.py` `health` reads it); see Appendix E.
- Units, UI code, other machines, Library attach and the real server.

## Appendix C. Files two PRs share

| Pair | Shared file | Order |
|---|---|---|
| P1, P2a | none (P1 edits `LB/migrate/from_library_b.py`, P2a edits `LB/adapter.py`) | wave 1, side by side |
| P2a, P2b | `E/control_door.py`, `E/service/runs.py` | P2a first |
| P2b, P3 | none | wave 2, side by side |
| P1, P5 | `HO/jobs.py` (P5 uses it and should not need to edit it) | P1 first |
| P5, P6 | none (P5 edits `HO/door.py`, P6 edits `HO/host.py`) | wave 3, side by side |
| P3, P4 | `BR/service.py` (`compiled` and `read` for P3, `open_adapter`'s CCXT branch for P4) | P3 first |
| P2b, P4 | `QX/service.py` (`workflows_run` for P2b, the settings write for P4) | P2b first |
| P1, P6 | none (P1 edits `HO/__main__.py`, P6 edits `HO/host.py`; both follow Appendix E's exit codes) | P1 first by wave |

## Appendix D. Defaults

- G2. The card's server exits with a code and the folder, and the desktop app starts the host. Claude's default. AD-48 already makes `qmx-desktop` the one that starts and watches `qmx_host`, and an exit keeps the card's process from having to scrub the environment, take the folder's lock and become the host mid run. Switching the card's server into the full host on the same port was weighed and rejected (Appendix G).
- The handover line goes to stdout and the pointer, never to a file. Claude's default, from ruling 143 (nothing but the pointer beside the pointer).
- A job ends `finished` or `stopped`, with one plain line. Jobs live for the process's life and are never capped. Claude's default, from ruling 106.
- The bring-in's fast refusals stay synchronous 409 answers, so the card can say no at once before any job exists. Claude's default.
- `serve`, `start`, `status` and `stop` exit 3 for no QMX folder. Claude's default, so the desktop app branches on a code, not on text.
- A refreshed cTrader pair is written before the read goes on, and a pair the store does not hold is never used. Claude's default, from ruling 135 and his rule that he never sees a token.
- The no-demo check runs at write and at read, never as a model validator. Claude's default, so his saved settings always load.

## Appendix E. The handover contract (reference)

The desktop app (`qmx-desktop`, engine AD-48) follows this contract. The UI agent wires the first-start card and the host against it.

| Step | The desktop app runs | It reads | Then |
|---|---|---|---|
| 1 | `python -m qmx_host serve --port <p> --ui-origin <origin>` | exit 3 means no QMX folder yet, or only his old data | step 2 |
| 1 | the same | the host answers `/api/health` with the bearer | the UI talks to the host on `<p>` |
| 1 | the same | exit 2 with one line on stderr, a store or the engine refused | show the line; QMX did not start |
| 1 | the same | exit 1 with one line, a host already runs or a bad place name | show the line |
| 2 | `python -m qmx_host first-start --serve --port <p> --ui-origin <origin>` | the card's routes on `<p>`, loopback only, no bearer | the UI shows the card |
| 2 | the same | exit 0, last stdout line `{"handover": {"folder": "<folder>", "port": <p>}}` | step 3 |
| 2 | the same | exit 1, stopped with no folder chosen | quit or run step 2 again |
| 2 | the same | exit 2, the port is in use | pick another port |
| 3 | `python -m qmx_host serve --home <folder> --port <p> --ui-origin <origin>` | the host answers `/api/health` with the bearer | the UI talks to the host on `<p>` |

- The card's routes are `GET /api/first-start`, `POST /api/first-start/new`, `/open`, `/restore` (501 until G1), `/bring-in` (202 with a job), `GET /api/first-start/jobs/{job_id}` and `POST /api/first-start/handover`. A refusal answers 409 with `detail`, its one line.
- The host's routes all need the bearer. The desktop app reads it from the keyring entry `qmx/control-token`, as `HO/host.py` `health` does, and hands it to its window. The UI never asks the host for it.
- The same port is used for the card and the host, so the UI keeps one base URL and polls `/api/health` until the host answers.

## Appendix F. Words

- **Bring-in.** Copying his old QMX data into a new QMX folder on the first start. The old folder is only read.
- **Job.** A piece of long work the host runs in the background and the UI reads by id. It is `running`, then `finished` or `stopped`.
- **Step.** Where a job is, in plain words, such as "copying".
- **Line.** The one plain sentence that says why a job stopped or a choice was refused, and what to do next.
- **Handover.** The first-start card's server giving the chosen folder to the desktop app and exiting, so the desktop app starts the host on it.
- **Card.** The first-start screen's backend, the routes under `/api/first-start`.

## Appendix G. Alternatives weighed

- G2 by switching the card's server into the full host in the same process on the same port. Rejected. The host's start order scrubs the environment before the harness is imported (`HO/__main__.py:22-24`), reads the keep list from the chosen folder's `settings.toml`, takes the folder's single-instance lock and records its process. Doing that inside a server that is already serving the card, with a bring-in thread just ended, is more moving parts than an exit, and AD-48 already gives start and supervision to the desktop app.
- G2 by the card starting `serve` as a child process. Rejected. Two parents would then supervise the host, the card and the desktop app.
- C1 by streaming progress on the held request. Rejected. A held request is what the triage found broken, and a job read survives a reload of the card.
- C12 as a pydantic validator on `Connection`. Rejected. One saved row would then stop every broker and connection read from loading.
- P2a by stamping the summary's facts on a second ledger event at start. Rejected. `run_created` is already the run's one start record, read by resume (`E/runner.py:449-470`).

## Appendix H. Gates and calls

- G-LAND. He lands the stack himself.
- No call needs him. No PR touches money, his vocabulary or irreversible scope. Shipping Spotware's MIT-licensed protocol files with QMX is a technical choice.
