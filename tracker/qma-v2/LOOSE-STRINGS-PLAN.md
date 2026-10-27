# QMX loose strings, build program

This program closes the backend gaps that stop QMX launching cleanly out of the box, so the UI agent who wires the separate UI design later finds no backend gap to fill.
He asked for it on 2026-10-27 ("the back end has no loose strings"). The triage of 208 findings against `629bea16` is `D:/QMX-worktrees/qma-ship/wrapup/evidence/loose-strings-triage-2026-10-27.md` (16 launch capabilities, C1 to C16), and the plan review is `D:/QMX-worktrees/qma-ship/wrapup/review/plan-loose-strings-edge-cases.md`.
There are 7 PRs. P1 runs the bring-in in the background, reports in plain words and hands the chosen folder to the desktop app. P2a makes every resumed run land. P2b gives a live run its inputs from REST and triggers. P3 makes cTrader work with no hand-set protocol files and says why a read failed. P4 refuses a demo row on an exchange with no demo mode. P5 runs template install as a job. P6 makes the host name what did not open.
The coordinator's closing lanes (V, C16) run after the stack. Local backup and restore (G1) is the next program, not this one (Appendix B).
The stack roots on `build/md3` at `629bea16`. Units, UI code, other machines and the real server are out of scope.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a test run, or a SHA. The body is a how-to. The appendices explain and record.

Each PR section opens with a preamble naming the triage capabilities and lines it closes, the rulings it serves, what the code does today, and its done line with the edge cases it must survive. Then come the nine blocks `check-plan.mjs` requires. Review findings are cited as F1 to F24 and E1 to E24 from the review file above.

Path shorthands. `QA/` is `qmx-agents/packages/`. `HO/` is `QA/qmx-host/src/qmx_host/`, `E/` is `QA/qmx-engine/src/qmx_engine/`, `LB/` is `QA/qmx-library/src/qmx_library/`, `MM/` is `QA/qmx-memory/src/qmx_memory/`, `QX/` is `QA/qmx-control/src/qmx_control/`, `BR/` is `QA/qmx-broker/src/qmx_broker/` and `HM/` is `QA/qmx-home/src/qmx_home/`. Line numbers are at `629bea16`.

The store is `D:/QMX-worktrees/qma-ship/wrapup/` (the one the mock-data program used), with `QUEUE.md`, `BRIEF-BUILDER.md`, `REVIEWER-BRIEF.md`, `RESUME.md`, `BACKLOG.md`, `lows.md`, `ledger.tsv`, `dispatch/`, `review/` and `evidence/`.

The program follows `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md` with the overrides of `LOCAL-FIRST-PLAN.md`, as `MOCK-DATA-PLAN.md` did. Builders are Claude Opus 5.5 (`poteto-agent`, `model: opus`), at most two at once, never two on shared files. A fresh Opus reviewer agent reviews every diff and runs the edge-case lens of `bmad-review` on every PR (each touches data, the Library or connections). The coordinator runs the suites, `just ci` and the lanes in the background and allows one fix round. Low findings go to `lows.md`; anything new goes to `BACKLOG.md`. He lands the stack himself.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] Confirm the shell (Windows 11, PowerShell 7.6 and Git Bash; in PowerShell `$H` and `$h` are one variable) and the root (`git rev-parse origin/build/md3` is `629bea16`). Logged in `RESUME.md`.
- [ ] Read the trunk rules with `git show origin/main:CLAUDE.md`, then the rulings file `research/methodology/26-operator-rulings-and-alignment.md` (rulings 106, 135 and 141 to 145), then the triage and review files named above, then Appendices D and E of this plan.
- [ ] No hourly `/loop 1h` tick, because builder and background-job notifications wake the coordinator. Post a short status message to the operator only when a PR opens, a verdict lands or a blocker appears.
- [ ] Never stop to ask him during the build. Stop only for a credential, a real ambiguity in this plan, or a step only he can do (`QUEUE.md`).
- [ ] Before dispatch, add to `BACKLOG.md` the review items this plan leaves out (Appendix B lists them).

### Spawn owners

| # | Id | PR | Wave | Branches from | Runs beside | Proving check |
|---|---|---|---|---|---|---|
| 1 | P1 | The bring-in runs in the background and hands over | 1 | `629bea16` | P2a | a 2,000-item bring-in shows rising counts, then the host starts on the same port |
| 2 | P2a | Every resumed run lands | 1 | `629bea16` | P1 | a trigger-fired run killed before its first summary lands its clippings on `main` |
| 3 | P2b | A live run takes its inputs | 2 | the stack tip after wave 1 | P3 | a REST run of "Clippings into research" reads the folder its body names |
| 4 | P3 | cTrader works out of the box | 2 | the stack tip after wave 1 | P2b | a sign-in with no protocol fields reads accounts, and an expired token is refreshed |
| 5 | P5 | Template install runs as a job | 3 | the stack tip after wave 2 | P6 | an install of three templates answers at once and reports each one |
| 6 | P6 | The host names what did not open | 3 | the stack tip after wave 2 | P5 | `/api/data/instruments` answers its reason when the price door is shut |
| 7 | P4 | A demo row with no demo mode is refused | 4 | the stack tip after wave 3 | none | a new kraken demo row is refused by name when it is written |

- [ ] Spawn one fresh Opus builder per PR in the background with `subagent_type: poteto-agent` and `model: opus`, from a dispatch file saved in `dispatch/`. Its first words are exactly "Read the poteto-mode skill's SKILL.md in full, including its Principles section, before any work. Do not spawn sub-agents."
- [ ] Before each wave's second dispatch, record the empty Files intersection of its two PRs in `ledger.tsv` (Appendix C).
- [ ] No PR touches `apps/qmx-ui/`, `~/.claude`, his real home `~/.qmx`, his real QMX folder, `C:/Users/Mubarak/Documents`, `C:/Users/Mubarak/Desktop/DATA_NARL`, Credential Manager or any vault value. Lanes run on throwaway folders and a scratch profile only, and broker lanes inject a fake key store.

### PR mechanics, for every PR

- [ ] The coordinator creates `build/ls-<id>` from the branch the table names in `D:/QMX-worktrees/bld-ls-<id>` before the dispatch. Never `git stash`.
- [ ] The builder opens the PR ready with `gh pr create --base <parent-branch> --head build/ls-<id> --repo MubarakHimself/QMX`.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Set `TMP` and `TEMP` to `D:/Temp`, `UV_CACHE_DIR` to `D:/Caches/uv`, and put `D:/Tools/rclone` on `PATH`.
- [ ] The builder reads the code its Files block names before editing, reproduces each finding with a failing test first, then fixes it. It runs `fmt-check`, `lint` and `types` in each package it touched and `tools/secret_scan.py`, reads each exit code, runs only the fast tests it added or changed, and never waits on a long command. It runs the `blast-radius` skill on its diff before the last push and proves the one fact its Build block names.
- [ ] Every line a person reads (a refusal, a job's line, a report) is plain words, names the thing and says what to do next. No QMX-internal cap, ceiling or default-closed lock is added anywhere (ruling 106). A mutex that two writers take in turn is not a default-closed lock.
- [ ] Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. PR bodies end with the Claude Code line.

### Verdict and merge, for every PR (append to the stack, merge on his go)

- [ ] At the code-ready head the coordinator runs the touched suites with `-n 2` and lanes 1 to 4 in the background, reads every package block of each log (not its tail), and saves the logs. A fresh Opus reviewer agent (one per PR, `model: opus`, told not to spawn sub-agents) reads the PR section, the full diff, the edge-case lens and those logs, and writes `review/<id>-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] Blockers go back to the same builder for one fix round. Low findings go to `lows.md`.
- [ ] `ledger.tsv` gets head, parent and patch-id.
- [ ] Parallel PRs of one wave join the stack with merge commits, never a rebase. `just ci` runs at the stack tip once at the end, with `D:/Tools/rclone` on `PATH`, under `D:/QMX-worktrees/.ci-lock`.
- [ ] He lands the stack himself from the one full list the coordinator sends when `QUEUE.md` is empty.

### Boot recipe, for every live lane

- [ ] `git worktree add --detach D:/Temp/ls-<id>-check <head>`, then `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`. A lane that needs the parent adds a second worktree at the parent the same way.
- [ ] A lane runs on a throwaway QMX folder under `D:/QMX-worktrees/qma-ship/wrapup/homes/ls-<id>-<lane>/`, made with `qmx_home.resolve(..., create=True)`, with `USERPROFILE`, `APPDATA`, `LOCALAPPDATA` and `HOME` on a scratch profile under the same folder, so the pointer file lands there too, and with `QMX_HOME` unset.
- [ ] A lane that starts a host or a first-start card injects its bearer, turns the memory database off (`hindsight_runs` patched), and uses a port of its own, because on Windows pg0 writes his real profile (design 62 L7).
- [ ] A synthetic old folder is made by the bring-in tests' own builder (`old_home` in `QA/qmx-host/tests/test_bring_in.py`, which P1 gives `count` and `versions` parameters), never copied from `~/.qmx`.
- [ ] Save captures as `evidence/ls-<id>/check-<slug>.log`, then remove the check copy with `git worktree remove` and confirm no `qmx_host`, `claude` or `node` process from the lane is left.

## Run the bring-in in the background and hand the folder over (P1)

Triage C1 to C4 and G2 (B114, B116, L52a to L52c, L53, L54b, L59b, L60b, L66), with review F1 to F7 and E1 to E8. Rulings 141 and 142 (his data is in one place, nothing he relies on is a stand-in) and 143 (nothing but the pointer sits beside the pointer). Today `POST /api/first-start/bring-in` runs `bring_in_old` inside the request (`HO/first_start.py:393-401`), so a 10,000-item bring-in holds one HTTP request for 663 s with no progress. An error before the unfinished marker (`HO/bring_in.py:295-310`, the survey, the room check and `resolve(create=True)`) escapes as a traceback and the card gets a 500. The removable-drive warning is printed only by the CLI (`HO/__main__.py:154-156`), and the card's drive rows hold only fixed drives (`_fixed_drives`, `HM/__init__.py:702-708`). `copy_file` (with its `source.stat()` and `os.utime`), `sha256_of`, `listing`, `_walk`, `_survey`, the folder `mkdir` at `bring_in.py:359-360` and `_room`'s `exists()` walk open plain paths, so a path over 260 characters ends the bring-in unfinished. The report counts versions as items (`_kinds_brought_in` counts `items` rows, one per version, and `_made_by_tests(len(tests))` counts version ids). `NoQmxFolder` is one exception for nothing found, for his old flat data and for a found folder that is refused (unreadable pointer, a newer format, a nested folder, a `QMX_HOME` that is not a folder; `HM/__init__.py:285-337,383-390`), and `HO/__main__.py:64-67` exits 2 for all of them. A folder holding an unfinished bring-in is labelled, so the drive scan finds it; `serve` then exits 2 (`HO/__main__.py:71-73`), and the card shows it as `found` with only "open" (`first_start.py:259-267`), which refuses it. After a choice finishes nothing starts the host (`HO/__main__.py:133-140`). Done when the bring-in runs as a job the card reads by id, with its step, files hashed, files and bytes copied and versions switched; the fast refusals still answer 409 at once; every other failure ends the job `stopped` with one plain line and no traceback, the folder marked unfinished only when copying began; a path over 260 characters copies and hashes; the report counts items, not versions; the card shows the removable-drive warning on the default folder and on the chosen folder; no outcome steers him to make a second folder while his data sits in another (Appendix D, P1 decisions); and the card's server hands over the folder of its own last finished choice by the contract in Appendix E. Edge cases it must survive. Two bring-in POSTs at once give one 202 and one 409 naming the running job, and a CLI bring-in in another process makes the card's POST answer 409 too, because the route takes the per-user `first-start.lock` before it answers. A choice of new or open while a bring-in runs answers 409. A reloaded card finds the running or last job in `GET /api/first-start`. A card killed mid copy leaves the folder marked unfinished, the old folder byte for byte unchanged, and no `first-start.lock` beside the pointer once the card starts again; the card then shows that folder as `unfinished` and offers the bring-in into the same folder again, which clears only QMX's own unfinished copy, on his click. A rerun into a finished folder returns the saved report as a finished job and copies nothing. A file in the old folder that changes during the copy still stops the job by name. Handover before any finished choice in this card, or after an unfinished bring-in, answers 409, whatever an older pointer, a `QMX_HOME` or a `~/QMX` folder holds. Handover twice answers the same folder. The card's port already taken exits 4 before anything is served. A pointer that cannot be written (no `APPDATA`) still hands over, because the card keeps the folder itself and the handover line names it. A found folder that is refused shows its line on the card with only "open", never "new" or "bring-in". With no `APPDATA` there is no pointer file and so no place beside it for `first-start.lock`, so the lock falls back to `qmx-first-start.lock` in the system temp folder, and the 409 for a bring-in in another process still holds (review R5).

**Depends on.** The root `629bea16`.

**Files.**

- [ ] Create `HO/jobs.py`. One `Jobs` registry for long work the host runs in the background, read by id (Appendix F names its words). `start(kind, work, *, alone=True)` checks for a running job of that kind and starts the new one under the registry's lock, returning the running job instead when `alone` refuses; `work(report)` runs on a daemon thread. `get(id)` and `latest(kind)` return snapshots under the lock. The view is `{id, kind, state, step, done, total, progress, line, result}` with `state` one of `running`, `finished` or `stopped`. Jobs live for the process's life and are never capped or pruned.
- [ ] Create `HO/process_record.py` with `recorded_host` and the record's file name, moved from `HO/host.py` (which imports them from there, its own copies deleted), so `bring_in._running` no longer imports the whole host module (E7).
- [ ] Edit `HO/bring_in.py`. Split the fast refusals out of `_bring_in` into `refusal_before_copy(old, folder, place_refusal)` (old folder gate, running host, place refusal, overlap, a folder brought in from another old folder), called by the route and by `_bring_in`. `bring_in` takes an already held lock handle from the route instead of taking `first-start.lock` itself when one is given. Add a `progress` callback threaded through `listing`, `_carry` and the switch. Turn any `OSError` before the unfinished marker into `Refused` with `_reason`, whose text drops a `\\?\` prefix. Add one long-path helper (the `\\?\` prefix on Windows for an absolute path, the path unchanged elsewhere) used by `copy_file` (its opens, `source.stat()` and `os.utime`), `sha256_of`, `listing`, `_walk`, `_survey`, the folder `mkdir` in `_carry` and `_room`'s `exists()` walk; `_first_change` opens no path and is left alone. Count distinct `root_id` per kind in `_kinds_brought_in`, and count test-run items as distinct roots in the report and in `recheck_at_start`. Right after the unfinished marker is written (`bring_in.py:327`), write the start facts (`old`, `old_is`, `folder`, `started`, `finished: false`) to `data/migration/bring-in-report.json`, so a bring-in killed mid copy still names its old folder; `_finished` already requires `finished: true`, so no reader changes (review R1). Add `again`, which clears a folder only when it is marked unfinished, its saved facts name the same old folder, and the old folder still passes `old_refusal` and, when `old-layout-list.json` exists, still matches that list, then brings in again.
- [ ] Edit `HO/first_start.py`. `POST /api/first-start/bring-in` takes `first-start.lock` (beside the pointer, or in the system temp folder when there is no pointer file), runs the fast refusals (409), then starts the job with the lock handle and answers 202 with its view; `new` and `open` take the same lock. Add `GET /api/first-start/jobs/{job_id}` and `POST /api/first-start/handover`. `GET /api/first-start` carries `job` (the running or last bring-in job's view, or null). `offer()` takes `places` and reads `NoQmxFolder.kind` (Appendix D, P1 decisions); the default folder carries `warning`, and each choice's answer carries `warning` for the chosen folder. `first_start_app` takes an `on_handover` callback. At card start a stale `first-start.lock` that no process holds is removed.
- [ ] Edit `HO/__main__.py`. `first-start --serve` binds its socket once (exit 4 when the port is taken, with the port named), runs `uvicorn.Server(...).run(sockets=[sock])` with `timeout_graceful_shutdown` of a few seconds so a hung client cannot hold the handover open, prints the handover line last and exits 0, or exits 1 when it stopped with no handover. `serve`, `start`, `status` and `stop` exit 3 for `NoQmxFolder` of kind `missing` or `old` and for a folder `old_library` refuses because its bring-in is unfinished, and exit 2 with the line for kind `refused` and for an unswitched `library.db`.
- [ ] Edit `HM/__init__.py`. `NoQmxFolder` gains `kind`, one of `missing`, `old` and `refused`, default `refused` (so `E/workers/zones.py:102` and any other raiser stay refused). `NOT_FOUND`, a flag folder that is missing and a labelless empty folder raise `missing`; `old_flat` raises `old`; every other raise stays `refused`.
- [ ] Edit `LB/migrate/from_library_b.py`. `import_library_b` and `switch_over` take an optional keyword `on_item(done, total)` over version rows, default None, so `scripts/data/switch_library.py`, `scripts/probes/data/p_rehearse.py` and `scripts/live/library/libm_lanes.py:191`, which pass no `on_item`, are unchanged.
- [ ] Edit `QA/qmx-host/tests/test_bring_in.py` (`old_home` gains `count` and `versions`; the route test reads the job; the old-folder `serve` test expects exit 3) and `QA/qmx-home/tests/test_resolve.py` (the kind of each raise), and add `QA/qmx-host/tests/test_jobs.py`, `QA/qmx-host/tests/test_handover.py` and `QA/qmx-library/tests/test_switch_progress.py`.

**Build.**

- [ ] Write the job registry and its tests first, then the `NoQmxFolder` kind and the exit codes, then move the route onto the job, then the handover. Each step ends with its own test run.
- [ ] The bring-in job's `progress` is `{files_hashed, files_total, files_copied, bytes_copied, bytes_total, versions_switched, versions_total}`, `files_total` coming from the survey, and its `step` is one of "listing your old folder", "copying", "checking the copy", "moving your Library into the new one" and "opening the new folder's stores", one per stage the unfinished marker already names. Its `result` is the report document the route answers today (`finished`, `folder`, `report`, `facts`).
- [ ] A job's `line` is empty while it runs; a stopped job's line is the refusal or the report's why, one sentence, never a traceback or an exception class name alone.
- [ ] The card keeps, in its process, the folder of its last finished choice (new, open, or a finished bring-in job). `POST /api/first-start/handover` answers `{folder, port}` when that folder is set, `resolve(folder)` opens it, `old_library(layout.home)` is None and no bring-in job runs, then calls `on_handover`. Anything else answers 409 with its line.
- [ ] Prove the one fact the handover rests on. A test serves the card with `uvicorn.Server` on a bound socket, posts the handover, and asserts the client got the 200 answer before `server.run()` returned.

**You see.**

- [ ] On a scratch profile, `python -m qmx_host first-start --serve --port <p>` with a synthetic old folder answers `POST /api/first-start/bring-in` with 202 and a job id, `GET /api/first-start/jobs/<id>` shows `files_hashed`, then `files_copied`, then `versions_switched` rising, then `finished`. After `POST /api/first-start/handover` the process prints `{"handover": {"folder": "<folder>", "port": <p>}}` as its last line and exits 0, and `python -m qmx_host serve --home <folder> --port <p>` answers `/api/health` on the same port.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A job that raises ends `stopped` with one line; two starts of one kind give one job and one refusal; a refused bring-in answers 409 before any job exists; a POST while another process holds `first-start.lock` answers 409; an `OSError` from `shutil.disk_usage` and from `resolve(create=True)` each end the job with one line and no marker; a 300-character path under `environments/` copies and hashes, and no line shows `\\?\`; the report of a three-item Library, one item with two versions and one two-version test item, says 3 items and 1 item made by test runs; handover answers 409 before a choice, with a pointer to another folder, and the folder after one; each `NoQmxFolder` raise carries its kind; `serve` exits 3 with no folder, with the old folder and with an unfinished bring-in, and 2 for a newer-format folder; `offer()` shows a refused folder with only "open" and an unfinished one with `unfinished` and the bring-in again; a bring-in stopped mid copy leaves start facts with `finished: false`, and `_finished` still reads it as not finished; `again` clears only an unfinished folder whose facts name the same old folder; with no `APPDATA` a second bring-in in another process still gets 409; `switch_over` without `on_item` behaves as at the root. Run the host, home and Library suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The host, home and Library suites at parent and head. Save `p1-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. The card server on a scratch profile brings in a synthetic 2,000-item old folder, polled every second, and the card is reloaded once mid copy. Save `p1-job.log`. Pass when the POST answers 202 within 1 s, every poll answers within 1 s with counts that never fall, the reloaded `GET /api/first-start` carries the job, and the job ends `finished` with the report.
- [ ] Lane 3. The same with one file at a 300-character path under `environments/`. Save `p1-longpath.log`. Pass when the job finishes and the copy's sha256 matches the old file's.
- [ ] Lane 4. After lane 2, post the handover, then run `serve --home <folder> --port <same>`. Save `p1-handover.log`. Pass when the card exits 0, its last stdout line names the folder and port, and the host answers `/api/health` with the bearer on that port within the start budget `HO/host.py` uses (`START_S`, 30 s).
- [ ] Lane 5. Kill the card process during the copy, then start it again. Save `p1-killed.log`. Pass when no `first-start.lock` is left beside the pointer, a snapshot of the old folder matches the one taken before, the old job id answers 404 with its line, `GET /api/first-start` shows the folder as `unfinished`, `serve` exits 3, and the bring-in again into the same folder finishes.
- [ ] Lane 6. A target whose drive check raises `OSError` (patched `shutil.disk_usage`). Save `p1-early-error.log`. Pass when the job ends `stopped` with one line and the server log holds no traceback.
- [ ] Lane 7. The card with a fake removable default drive (`Places.drive_type` answering 2), then a choice on that drive. Save `p1-removable.log`. Pass when the default folder and the choice's answer carry the warning line.
- [ ] Lane 8. `serve` and `start` with no folder, pointed at the old folder, and pointed by the pointer at a folder labelled with a newer format. Save `p1-exit-codes.log`. Pass when the first two exit 3 and the third exits 2, each with its one line, and the card on the third shows its line with only "open".
- [ ] Lane 9. The card started on a port already in use, a handover posted before any choice, and a handover with an older pointer naming another labelled folder. Save `p1-refusals.log`. Pass when the first exits 4 with the port named and both handovers answer 409.
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

Triage C5 and C6 (B120a, B121b, L58a to L58c), with review F8, F9, E10 and E11. Rulings 141 and 142. Today four paths resume or end a run, and none can summarize a run that died before its first summary. `summarize_again` rebuilds the summary from the last one (`E/service/runs.py:425-445`) and returns None when there is none; the REST resume (`E/control_door.py:614-620`) and the adopt path (`E/service/runs.py:603-604`) call it. The cancel path's `_summarize` (`E/control_door.py:583-600`) returns when there is none. The ticker resumes a fire left `running` with `engine.resume` and never summarizes (`E/triggers/ticker.py:309-313`), and the CLI `resume` (`E/__main__.py:192-202`) does the same. So a trigger-fired run killed mid run, the commonest case, never lands (MD1 lane 6 showed 2 clippings on the run ref, 0 on `main`). `run_created` records mode, fake, item and content hash but not the published version's `object_id` or who started it (`E/runner.py:816-836`). A run's memory rows sit on `refs/runs/<run_id>` (`MM/rows.py:56-60`), and an agent node's compaction note is one of them (`E/nodes/agent.py:384-395`), but `_archive_samples` skips every kind but `artifact` (`LB/adapter.py:378-386`), so recall over run scope can return a test run's note. Recall, `_rows` and `check_built` already leave archived rows out (`MM/engine.py:336-345,372-374,414-421`). `check_built` reads only home, workflow and operator rows (`MM/engine.py:167-177`); a test run's row reaches those scopes only through `consolidate`, which writes one row `derived-from` the run's rows (`MM/engine.py:241-258`) and has no production caller at `629bea16`. Done when one function builds a run's summary from its `run_created` facts (item, version, mode, fake, starter); all four paths (REST resume and adopt, cancel, the ticker's resume, the CLI resume) call it, so a run that died before its first summary lands its records; and a test or fake run's memory rows, and any row derived from them, are archived with its other samples, so recall and `check_built` leave them out with no change to `MM/`. Edge cases it must survive. A run created before this PR (no `object_id` in `run_created`) falls back to its last summary, and with none it logs one line naming the run and why it cannot land, never a crash. A run that dies again during its first resume and is resumed a second time lands each record once. A fake live run still lands nothing. A failed live run's records stay visible, since they are his. A subworkflow child run is summarized only through its parent, as today. A test run that died before its first summary gets its summary and its archive but no test report, because `run_created` does not hold the test's subgraph or caller (Appendix D); its draft stays untested until the next test. A test run that died and is never resumed stays visible until he resumes or cancels it.

**Depends on.** The root `629bea16`.

**Files.**

- [ ] Edit `E/runner.py` (`Engine.start` and `Run` take `object_id` and `started_by`, and `create` records both in `run_created`) and `E/service/runs.py` (`run_bundle` passes them; one `run_start(events)` reads the facts from `run_created`; one `summarize_resumed(ctx, outcome)` replaces `summarize_again`, using `run_start` and falling back to the last summary only for an older ledger).
- [ ] Edit `E/control_door.py` (`_resumed` and `_summarize`, the cancel path, call `summarize_resumed`).
- [ ] Edit `E/triggers/ticker.py` (`_fire`'s resume branch near line 309 calls `summarize_resumed` before `_ended`).
- [ ] Edit `E/__main__.py` (`resume` opens `EngineService.open(home, library=library)` as the other commands do, and calls `summarize_resumed`).
- [ ] Edit `LB/adapter.py` (`_archive_samples` also archives the `memory-row` heads on the run ref, and each `memory-row` with a `derived-from` edge into one of them, found by `Store.edges_of(row, reverse=True)`, when every row it derives from is that run's). `MM/engine.py` and `E/ports/memory.py` do not change.
- [ ] Add tests in the engine and Library packages, against `EngineLibraryAdapter(Store.open(tmp))`, in new files `test_resume_lands.py` and `test_test_run_memory.py`.

**Build.**

- [ ] Reproduce first. A test kills the engine after the write node's attempt and before the first summary, resumes through the ticker, and fails on the parent because no summary is written.
- [ ] Add the two `run_created` fields, `run_start` and `summarize_resumed`, then move all four paths onto it and delete `summarize_again`.
- [ ] Reproduce the recall low (a test run's compaction note returned by recall over run scope), then archive.
- [ ] Prove the one fact. Older ledgers lack the two fields, so a test seeds a `run_created` without them and shows the fallback path.

**You see.**

- [ ] On a throwaway folder, an interval trigger's "Clippings into research" run killed before its first summary is resumed by the ticker at the next host start, and both clippings are on `main` with the run's summary.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A run with no summary resumed by REST, by the ticker and by the CLI writes one and lands; a cancelled one does too; a run that dies again in its first resume and is resumed again lands each record once; an older `run_created` without the fields resumes by its last summary or logs one line; a test run's memory rows and a row derived from them are archived at its summary; recall leaves out a test run's note; `check_built` still counts a live run's `built` row. Run the engine, Library, memory and control suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The four suites at parent and head. Save `p2a-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A trigger-fired "Clippings into research" run killed after the write node's attempt and before the first summary, then a host start. Save `p2a-ticker-resume.log`. Pass when the summary exists and both clippings are on `main`; the parent records 0 on `main`.
- [ ] Lane 3. MD1's lane 6 again through the REST resume route. Save `p2a-rest-resume.log`. Pass when the summary exists and both clippings are on `main`.
- [ ] Lane 4. A test run killed the same way, then resumed. Save `p2a-test-resume.log`. Pass when its samples and memory rows are archived and Library search and recall leave them out.
- [ ] Lane 5. A run killed the same way, then cancelled. Save `p2a-cancel.log`. Pass when the cancelled run has its summary.
- [ ] Lane 6. A run killed the same way, resumed with `python -m qmx_engine resume`. Save `p2a-cli-resume.log`. Pass when the summary exists.
- [ ] Lane 7. A run killed during its first resume, then resumed again. Save `p2a-twice.log`. Pass when `main` holds each clipping once.
- [ ] Lane 8. A ledger made at the parent with a run that died early, resumed at head. Save `p2a-old-ledger.log`. Pass when the run resumes and either lands by its last summary or logs its one line, with no traceback.
- [ ] Lane 9. Gates in the touched packages and `tools/secret_scan.py`. Save `p2a-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the throwaway folders and list processes. Save `p2a-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from the resume to the summary on `main` for lane 3's run, and seconds for a normal 50-clipping run at both sides.
- [ ] Probe. Lane 3 three times at head; the 50-clipping run three times at parent and head, interleaved.
- [ ] Baseline. Record the parent's 50-clipping median first. The parent never lands lane 3's run, so that number is recorded as never.
- [ ] Rule. The 50-clipping run at head is within 5 % of the parent, or the PR fails. Lane 3's resume reaches `main` within 10 s, an absolute budget.

**Review gate.** None. P2a is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Joined onto P1 by a merge commit (the two share no file).

## Give a live run its inputs from REST and from its trigger (P2b)

Triage C7 (B120b), with review F10 to F16 and E12 to E14. Rulings 141 and 142, and his rule that what he can configure is editable from the UI. Today `POST /api/workflows/{workflow_id}/run` takes no body (`QX/service.py:1673-1676`, its protocol line at `QX/service.py:2059`, `E/control_door.py:480-491`). Triggers have list, create, enable, disable and run now, and no edit (`QX/service.py:2072-2076`); a trigger row stores no inputs (`E/triggers/rows.py`), and template install writes its triggers with none (`add_disabled_trigger`, `E/templates/install.py:93-107`). The ticker builds a fire's inputs with `_inputs` (the `trigger` block, then the fire's payload, then `continuity`, and later `precheck`) before it calls `run_bundle` (`E/triggers/ticker.py:347,366,491-505`). A webhook fire's payload is `{"webhook": {"delivery_id", "body"}}` (`ticker.py:573`) and an `after` fire's is `{"upstream": ...}` (`E/service/runs.py:375-380`), so neither sets a top-level key. `run_bundle` also serves test runs, and the catalogue's test inputs `{"dry_run": true}` for the three download templates (`E/templates/catalog.py:450-475`) do not meet those workflows' `required: ["source"]`. The workflow's `inputs` is a JSON Schema (`E/definition/model.py:220`), and the engine already ships `jsonschema` (`E/nodes/llm.py:30`). A blocked fire already settles `blocked_config` through `_blocked` and `_failed` (`ticker.py:416-429`). Done when the run route's body is the run's inputs; a trigger row stores inputs, set at create and edited by `PUT /api/triggers/{trigger_id}/inputs`; a live start checks only the declared inputs (the REST body, or a trigger's stored inputs) against the workflow's `inputs` schema, in `Runs.start` and in the ticker before any engine key is merged, never in `run_bundle` and never for a test run; a fire whose stored inputs fail settles `blocked_config` with a line naming the trigger and the field; and the ledger gains the column by an additive step that an older engine still opens. Edge cases it must survive. An empty body runs with no inputs, as today. The engine's own keys (`trigger`, `continuity`, `webhook`, `upstream`, `precheck`) are never checked. A webhook's body stays at `webhook.body` and is not lifted (Appendix D, P2b decisions). `required` is checked at create, at edit and at enable only for `cron`, `interval` and `manual` triggers, and at fire time only for those kinds; a `webhook`, `event`, `after` or `session` trigger may leave a required input missing, since its data arrives with each fire, and only the type of its stored keys is checked. A template's installed trigger whose workflow needs an input is refused at enable by name until he sets it, which is an ask for a value, not a lock. A newer published version whose schema rejects a trigger's stored inputs blocks that trigger's fires with the line, counted in its failure streak. A workflow whose `inputs` is not a valid JSON Schema is refused by name, never a 500. Template test runs with `{"dry_run": true}` are not checked, so install is unchanged. A version 4 ledger upgrades with its pre-change copy and every trigger keeps `{}`; a version 5 ledger opens in the parent engine (`min_reader` stays 3), which then fires triggers without their stored inputs (Appendix D). An agent's confirm card for a run, an edit or an enable carries the inputs it was asked with.

**Depends on.** P2a (both edit `E/control_door.py`, `E/service/runs.py` and `E/triggers/ticker.py`).

**Files.**

- [ ] Edit `QX/service.py` (`workflows_run` takes `inputs`, and its protocol line near 2059 matches; add `workflow_triggers_inputs(trigger_id, inputs)` at `PUT /api/triggers/{trigger_id}/inputs`, `manage`, with its protocol line). The route uses PUT because the REST app's CORS allows only GET, POST and PUT (`QX/server.py`).
- [ ] Edit `E/control_door.py` (`workflows_run` passes the inputs and its confirm card carries them; `TriggerIn` gains `inputs`; `workflow_triggers_create` checks and stores them; `workflow_triggers_inputs` checks against the pinned version's schema and writes them; `workflow_triggers_enable` refuses a missing required input for the three timed kinds).
- [ ] Edit `E/service/runs.py` (`Runs.start` checks the inputs before `run_bundle`; one pure `input_refusal(schema, inputs, *, required)` holds the check, reused by the door and the ticker).
- [ ] Edit `E/triggers/rows.py` (`Trigger.inputs`, its column in the row list near line 194, `create`, and one `set_inputs` operation) and `E/triggers/ticker.py` (`_fire` checks the stored inputs before `_inputs` and blocks on a refusal; `_inputs` starts from the stored inputs, then the payload, then the engine's keys).
- [ ] Edit `E/ledger/migrations.py` (step 5, `ALTER TABLE triggers ADD COLUMN inputs TEXT NOT NULL DEFAULT '{}'`; `TRIGGER_COLUMNS` stays as it is, because step 4's copy of a version 3 ledger uses it) and `HM/stores.py` (the engine's `Version(4, 3)` becomes `Version(5, 3)`).
- [ ] Edit the tests that pin ledger version 4. `QA/qmx-engine/tests/test_ledger.py:79`, `QA/qmx-engine/tests/test_ledger_versions.py:75,99,129` (the "needs reader 5" case becomes 6, because release 5 meets `min_reader` 5) and `QA/qmx-home/tests/test_versions.py:260`.
- [ ] Add tests in the engine, control and home packages, in new files `test_run_inputs.py` and `test_trigger_inputs.py`.

**Build.**

- [ ] Reproduce first. A REST run of "Clippings into research" with a folder in the body fails on the parent because the folder never reaches `run_input`.
- [ ] Add the check, the route body, the trigger column, the edit route, the enable refusal and the ticker's check, each with its test.
- [ ] Prove the one fact. A version 5 ledger written at head opens in the parent engine. Lane 6 runs the parent's own worktree on it, and a unit test runs the parent's four `STEPS` with `STORES["engine"]` patched to the parent's `Version(4, 3)`, since head's `open_sqlite` refuses a step count that differs from the release (`HM/versions.py:139-140`).

**You see.**

- [ ] `POST /api/workflows/clippings-into-research/run` with the body `{"folder": "<scratch folder>"}` starts a run whose `run_input` holds that folder, and its clippings land. `PUT /api/triggers/<id>/inputs` with the same body changes what the trigger's next fire reads.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A REST run carries its body; an empty body still runs; `{"folder": 5}` is refused `inputs_invalid` naming `folder` with no run created; a broken schema is refused by name; a trigger's stored inputs reach its fire under the engine's keys; a webhook fire keeps its body at `webhook.body`; a cron trigger missing a required input is refused at create, at edit and at enable; a webhook trigger missing it is created; a stored input a newer version rejects blocks the fire with its line; the three download templates still install their tests; step 5 upgrades a version 4 ledger and keeps every row; the patched parent steps open a version 5 ledger. Run the engine, control and home suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The three suites at parent and head. Save `p2b-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host runs "Clippings into research" over REST with a scratch folder of two clippings. Save `p2b-rest.log`. Pass when `run_input` holds the folder and both clippings land; the parent records that the folder never arrives.
- [ ] Lane 3. A trigger created with the folder, fired by run now, then its inputs edited to a second folder and fired again. Save `p2b-trigger.log`. Pass when each run's inputs hold the folder stored at its fire and the trigger block.
- [ ] Lane 4. A REST run with `{"folder": 5}`. Save `p2b-invalid.log`. Pass when it is refused by name and no run exists.
- [ ] Lane 5. A ledger made at the parent, opened by a head host. Save `p2b-migrate.log`. Pass when it reads version 5, `backups/` holds the pre-change copy, and every trigger's inputs read `{}`.
- [ ] Lane 6. The ledger of lane 5 opened again by the parent engine in its own worktree. Save `p2b-older-reader.log`. Pass when it opens and fires a trigger.
- [ ] Lane 7. A webhook delivery on a trigger that stores a folder. Save `p2b-webhook.log`. Pass when the run reads the stored folder at the top level and the delivery at `webhook.body`.
- [ ] Lane 8. A head host installs the download templates, then enables one of their cron triggers. Save `p2b-enable.log`. Pass when the tests pass as at the parent and the enable is refused naming `source`.
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

Triage C8 to C11 (B78, B76, B69, L39a, L39b, with L38 folding in), with review F17 to F21 and E16 to E18. Ruling 135 (a key that can trade live money is never kept on This PC) and his rule that he never sees a token. Today `compiled` refuses a connection with no `protocol_path` and `protocol_tag` (`BR/service.py:60-72`), the model defaults both to empty (`BR/models.py:69-70`), and the sign-in refuses `grant_unchecked` until a row has them (`HO/venue_session.py:537-560`), also when no cTrader row exists at all; the only pinned descriptor set is the test fixture `QA/qmx-broker/tests/fixtures/tag91.pb`, under Spotware's MIT licence beside it. `join_ctrader_app` writes `qmx/read/ctrader-app` with keyring's `set_password` (`BR/credentials.py:205`), so a changed secret leaves the old pair in Windows' companion entry. `refresh_tokens` has no production caller (`BR/oauth.py:184-199`; only `scripts/probes/data/p_ctrefresh.py:75`). `_token_call` sets `expires_at` to `now + 0` when `expiresIn` is missing (`BR/oauth.py:160-161`). `urllib_fetch` catches only `HTTPError` and `OSError` (`BR/oauth.py:125-135`), so a token URL with no scheme raises a `ValueError` whose text holds the URL and its query, the client secret and refresh token among it. The sign-in lists the grant's accounts, refuses a live grant, and only then keeps the pair (`HO/venue_session.py:274-285`), and it reads the `[ctrader] token_url` setting (`venue_session.py:569`); `open_adapter` reads the stored pair without looking at its expiry and has no token URL (`BR/service.py:145-160`). A failed read says only "Broker read failed" (`BR/service.py:291-296`), which swallows the named lines `open_adapter` raises. Done when QMX ships the pinned descriptor set (tag 91) and uses it when a row names none, and the tests load that one copy; the sign-in with no cTrader row lists accounts on the demo endpoint with it; joining the app id and secret writes through `CredentialManager.replace`, so one copy remains; a token pair whose expiry has passed is refreshed before the read, under a file lock, in the same order the sign-in uses; and a failed read raises a typed `ReadRefused(code, line)` that says, in plain words, which of not signed in, signed in on another machine, protocol files, ended sign-in, the exchange refusing the key, or the network. Never print a token. No token, refresh token, client secret, authorization code or token URL with its query appears in a log line, an exception message, a report, a job line or a test's captured output; a bad token URL is refused as `token_url_invalid` with no URL in it; lane 8 greps for the fake values. Live refusal (ruling 135). After a refresh, the new access token's accounts are listed and `can_trade_live` runs first; a grant that can trade live money is refused by name and the stored pair deleted (cTrader already killed it), and nothing new is written; only a view-only grant is written with `replace`, then `authenticate` runs and the read goes on. The refresh never asks for the `trading` scope. Edge cases it must survive. A row that names a path that does not exist is refused by name. A row with a path and no tag, or a tag and no path other than the shipped one, is refused by name. A pair with no expiry recorded (`expires_at` 0, now stored when `expiresIn` is missing) is never refreshed on time alone; due means `0 < expires_at <= now`. A refresh refused by cTrader (revoked grant) says the sign-in has ended and to sign in again, and deletes the stored pair only when the store still holds the pair that was refused. A new pair that cannot be written says so and to sign in again, and the read does not go on with a pair the store does not hold. Two processes refreshing at once converge, because read, refresh and write run under one OS file lock in the QMX folder (`keys/ctrader-refresh.lock`, the `_held` pattern of `HO/bring_in.py`), and the second process finds the first one's new pair. A join whose primary already matches still removes a stale companion. The refresh uses the `[ctrader] token_url` setting, as the sign-in does.

**Depends on.** The wave 1 tip (P1 and P2a joined). It shares no file with P2b.

**Files.**

- [ ] Create `BR/protocol/openapi-91.pb` and `BR/protocol/Spotware-LICENSE.txt` by moving `QA/qmx-broker/tests/fixtures/tag91.pb` and its licence (`git mv`), create `BR/protocol/.gitattributes` holding `openapi-91.pb binary` (the line `tests/fixtures/.gitattributes` holds for `tag91.pb`, so line-ending conversion never changes its bytes; review R4), and point `QA/qmx-broker/tests/test_transport.py` and `QA/qmx-broker/tests/test_pc_home.py` at the shipped path, so one copy exists. Edit `QA/qmx-broker/pyproject.toml` only when `uv build --wheel` leaves them out of the wheel.
- [ ] Edit `BR/service.py` (`compiled` uses the shipped set when a row names neither field and refuses a half-set row; `open_adapter` takes the QMX folder and a `token_url`, refreshes a due pair under the lock, checks the new grant before `replace`, then authenticates; `read` raises `ReadRefused`; `BrokerService` takes an optional `ctrader` settings reader and passes the folder and `[ctrader] token_url` to `open_adapter`, using `TOKEN_URL` when it has none).
- [ ] Edit `QA/qma-harness/src/qma/harness/harness.py` (near line 414, where production builds `BrokerService` with only a `brokers` reader, also pass `functools.partial(control.settings_get, "ctrader")`) and `BR/server.py` (near line 81, `BrokerService(home)` with no settings, which then uses `TOKEN_URL`) (review R2).
- [ ] Edit `BR/oauth.py` (`_token_call` stores 0 when `expiresIn` is missing or not an int; `Tokens.due(now)`; `urllib_fetch` maps `ValueError` to `OAuthRefused("token_url_invalid")` with no URL) and `BR/credentials.py` (`join_ctrader_app` writes through `CredentialManager.replace` and removes a stale companion).
- [ ] Edit `HO/venue_session.py` (`one_session` reads with the shipped set when a row names none, and lists on the demo endpoint with the shipped set when no cTrader row exists; `grant_unchecked` stays only for a read that fails).
- [ ] Add tests in the broker and host packages with a fake key store, a fake transport and a fake token endpoint, in new files `test_protocol_default.py`, `test_refresh.py` and `test_read_reasons.py`.

**Build.**

- [ ] Reproduce each finding first with its failing test (a row with no protocol fields, a changed secret on a store that keeps a companion, an expired pair, a swallowed reason, a token URL with no scheme).
- [ ] Ship the set, then the join, then the expiry and the bad URL, then the refresh, then the typed reasons.
- [ ] Prove the one fact. The sign-in's order (list accounts, refuse live, then `replace`) is the refresh's order; a test drives both with the same fake live grant and asserts the fake store never holds its pair at any write.

**You see.**

- [ ] On a throwaway folder with fakes, a cTrader connection with no protocol fields signs in and reads its account, an expired pair is refreshed once, and a read with no sign-in says "Sign in to cTrader on This PC first".

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The shipped set compiles and the fixture copy is gone; a missing path and each half-set row are refused by name; a join with a changed secret leaves one copy and no companion; a token answer without `expiresIn` stores 0 and is never due; a due pair is refreshed and replaced before the read; a refreshed live grant is refused, deleted and never written; a revoked refresh says the sign-in ended and deletes only the refused pair; a failed write stops the read with its line; a token URL with no scheme is `token_url_invalid` and no captured output holds the secret; each reason reads its own line. Run the broker and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The broker and host suites at parent and head. Save `p3-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. The PC sign-in through `HO/venue_session.py` with a fake consent code, a fake token endpoint and a fake transport, once on a row with no protocol fields and once with no cTrader row. Save `p3-signin.log`. Pass when both list accounts on the shipped set and no `grant_unchecked` appears; the parent refuses `grant_unchecked`.
- [ ] Lane 3. An `account_state` read with a stored pair whose expiry has passed. Save `p3-refresh.log`. Pass when the fake endpoint saw one refresh, the fake store holds the new pair only, and the read answers with `environment: demo`.
- [ ] Lane 4. One read for each failure (no pair, homed on another machine, a missing protocol path, a revoked refresh, the network down). Save `p3-reasons.log`. Pass when each says its own plain line and none says only "Broker read failed".
- [ ] Lane 5. The join with a changed secret on a fake store that keeps a companion. Save `p3-join.log`. Pass when one copy holds the new pair and no companion is left.
- [ ] Lane 6. A refresh whose new grant reports a live account. Save `p3-live.log`. Pass when the read is refused by name, the stored pair is deleted, and the fake store's write log never shows the new pair.
- [ ] Lane 7. Two broker services in two processes read the same due pair at once, against a fake endpoint that kills a used refresh token. Save `p3-race.log`. Pass when both reads answer, the endpoint saw one refresh, and the store ends with the new pair.
- [ ] Lane 8. A `[ctrader] token_url` with no scheme, then a grep of every lane log, the host log and captured stderr for the fake access token, refresh token, client secret and code. Save `p3-leak.log`. Pass when the read says `token_url_invalid` and none of the values appears.
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

Triage C13 (B8), with review F22 and E21 to E23. Ruling 106 (no QMX limit; an install takes as long as its models do). Today `POST /api/templates/install` awaits the whole install in one request (`HO/door.py:321-342`), which with real models can run many minutes. The engine CLI posts to it with no timeout and reads the list it answers (`E/__main__.py:256-276`); when `through_host` returns None on `URLError`, the CLI runs the whole install in its own process with the harness and real models (`E/__main__.py:315-345`). Done when the route starts a job on P1's registry and answers 202 with its view at once; `GET /api/templates/install/{job_id}` reads which template it is on, how many of how many are done, and each finished row; the CLI posts, then reads the job until it ends and prints the same rows as today, and runs the in-process install only when its first POST cannot connect. Edge cases it must survive. An unknown template id is refused 404 by name before any job starts. A template whose test run fails is a `test failed` row in a `finished` job. A hop that raises one of the route's `FAILURES` ends the job `stopped` with its code and line and the rows finished so far in `result`. A second install while one runs answers 409 naming the running job, because two installs would write the same drafts. A host that stops while the CLI polls makes the CLI print "the host stopped during the install; start it and run the install again" and exit 1, never a second install. A rerun is idempotent (the finished templates read `unchanged`). The install still runs on the engine's loop in an empty context, so its test runs inherit no request principal. A head CLI accepts a parent host's list answer as well as a job; a parent CLI against a head host fails on the job view, which `RESUME.md` names. `templates_router(engine)` keeps its signature, so `HO/host.py` is not touched.

**Depends on.** P1 (`HO/jobs.py`) and P2a (`E/__main__.py`).

**Files.**

- [ ] Edit `HO/door.py` (`templates_router` owns a `Jobs` registry; `POST /api/templates/install` answers 202; add `GET /api/templates/install/{job_id}`; each template is one `install_one` hop on the engine loop, so the job reports between them).
- [ ] Edit `E/__main__.py` (`through_host` reads the job until it ends, still with no timeout, and tells a failed first connect from a lost host).
- [ ] Edit `QA/qmx-host/tests/test_templates_route.py` and add the engine CLI cases in a new `QA/qmx-engine/tests/test_install_through_host.py`.

**Build.**

- [ ] Reproduce first. A test asserts the POST answers before a slow fake install finishes, and fails on the parent.
- [ ] Move the route onto the registry, then the CLI.
- [ ] Prove the one fact. `install` is a loop over `install_one` (`E/templates/install.py:38-40`), so one hop per template gives the same rows in the same order; a test compares the job's rows with `install()`'s on the same catalogue.

**You see.**

- [ ] With a head host on a throwaway folder, `python -m qmx_engine templates install --home <folder>` prints a line per template as before, and `GET /api/templates/install/<id>` showed `done` rising from 0 to 3 while it ran.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The POST answers 202 before a slow install ends; the job's rows equal `install()`'s; an unknown id is 404 with no job; a failed test is a row; a raising hop stops the job with the rows so far; a second install is 409; the CLI prints the parent's rows; the CLI that loses the host after the 202 exits 1 with its line and starts no install; the CLI accepts a list answer. Run the host and engine suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The host and engine suites at parent and head. Save `p5-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host installs three templates with a fake model, polled every second. Save `p5-job.log`. Pass when the POST answers within 1 s and `done` rises to 3 with three rows.
- [ ] Lane 3. The engine CLI install against the same host. Save `p5-cli.log`. Pass when it prints the rows the parent prints for the same templates.
- [ ] Lane 4. The CLI install, then the host stopped mid install. Save `p5-lost-host.log`. Pass when the CLI exits 1 with its line and no second install process ran.
- [ ] Lane 5. A template whose test fails. Save `p5-failed-test.log`. Pass when the job ends `finished` with a `test failed` row.
- [ ] Lane 6. A second install while lane 2's runs, and an install naming an unknown template. Save `p5-refusals.log`. Pass when the first is 409 naming the job and the second is 404 by name with no job.
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

Triage C14 and C15 (B52, L50), with review F23, F24, E8 and E24. Rulings 141 and 142, and his rule that a refusal says why in plain words. Today `market_door` prints its reason to stderr and returns None (`HO/host.py:955-977`), and the host then mounts no `/api/data/*` route (`HO/host.py:720-721`), so every data call answers 404. The door's own refusals answer `detail: {refused, retryability, context}` (`HO/market_data.py:1036-1045`). `serve_forever` catches only `HostRunning` and `PlaceRefused` (`HO/host.py:225-231`), so a `StoreRefused` (`HM/versions.py:49`) or either `LibraryRefused` (`qmx_library.port`, `qmx_engine.ports.library`) raised while the host opens escapes as a traceback. `start` probes the port and returns 1 when it is taken, and returns 1 when its child exits with any code (`HO/host.py:1194-1221`). Done when a shut price door answers every `/api/data/*` call with 503 and `detail: {refused, retryability, context, line}`, built from the `TypedRefusal` `market_door` already holds, `line` being plain words saying what is wrong and what to do; `RecordedHarness.open(market=...)` still gets a door or None; a `StoreRefused` or either `LibraryRefused` raised while the host opens prints one line, `QMX did not start: <why>`, and exits 2; `serve` binds its port once before it opens anything and exits 4 when it is taken; and `start` returns its child's exit code (Appendix E). Edge cases it must survive. An open door's routes answer as today. The closed-door route sits behind the same bearer and door as the open one. `start` reports its child's failure, and the one line is in `logs/host.log`. A refusal never prints a secret or a bearer. `HostRunning` and `PlaceRefused` keep exit 1.

**Depends on.** The wave 2 tip, including P1's `HO/process_record.py` change to `HO/host.py`. It shares no file with P5.

**Files.**

- [ ] Edit `HO/host.py` (`market_door` returns the door or its `TypedRefusal`; a `closed_market_router(refusal)` on `/api/data/{rest:path}` for GET and POST; `serve_forever` catches the three refusals by module; `serve` takes a bound socket and `uvicorn.Server.serve(sockets=[sock])`; `start` returns the child's code and 4 for a taken port).
- [ ] Add tests in new files `QA/qmx-host/tests/test_closed_door.py` and `QA/qmx-host/tests/test_open_refusals.py`.

**Build.**

- [ ] Reproduce first. One test shows the 404 on a `[data]` the door cannot use; one shows the traceback from a refusal injected into the engine's ledger open.
- [ ] Add the closed-door router, then the catch, then the port and exit codes.
- [ ] Prove the one fact. The closed router is appended to `answering` exactly where `market_router` is, and `create_app` includes every extra router with `Depends(authenticate)` (`QX/server.py:462-463`); a test calls it with no bearer and gets 401.

**You see.**

- [ ] A head host on a throwaway folder with an unusable `[data]` answers `GET /api/data/instruments` with 503, the refusal's category and a plain line.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A shut door answers 503 with `refused`, `retryability`, `context` and `line` on a GET and a POST route; with no bearer it answers 401; an open door answers 200; an injected `StoreRefused` and each `LibraryRefused` print one line and return 2; a taken port returns 4; `start` returns a child's 2; `HostRunning` still returns 1. Run the host suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The host suite at parent and head. Save `p6-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host with a `[data]` the door cannot use, then `GET /api/data/instruments`. Save `p6-instruments.log`. Pass when it answers 503 with the refusal and its line; the parent answers 404.
- [ ] Lane 3. `POST /api/data/read` on the same host. Save `p6-read.log`. Pass when it answers 503 with the same refusal.
- [ ] Lane 4. A host whose engine ledger open is refused (a ledger file that is not a ledger, placed after the start check). Save `p6-engine-refused.log`. Pass when stderr is one line starting `QMX did not start` and the exit code is 2.
- [ ] Lane 5. A host whose Library open is refused. Save `p6-library-refused.log`. Pass when stderr is one line and the exit code is 2.
- [ ] Lane 6. A head host with a healthy door. Save `p6-open.log`. Pass when `GET /api/data/instruments` answers 200 as at the parent.
- [ ] Lane 7. `start` in the background on lane 4's folder. Save `p6-start.log`. Pass when it returns 2 and `logs/host.log` holds the one line.
- [ ] Lane 8. `serve` on a port already in use, and the closed-door route with no bearer. Save `p6-port.log`. Pass when the first exits 4 with the port named and the second answers 401.
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

Triage C12 (B118a, B119), with review E20. His rule that he never reads a demo number as his own, and ruling 106. Today a CCXT demo connection calls `exchange.set_sandbox_mode(True)` at read time (`BR/service.py:138-139`), which raises `TypeError` on 54 exchanges in ccxt 4.5.85 (kraken, coinbase and 52 more, listed in `BACKLOG.md` line 119; the review's probe confirmed the list and that construction opens no socket), so such a row can be saved and then never read. The settings write parses the whole section with `BrokerSettings` and hides any parse error behind one generic line (`QX/service.py:813-821`). Done when one check, `demo_refusal(exchange)`, runs what the read path runs on a fresh exchange object with no keys and no network, and names an exchange with no demo mode; the `brokers` and `connections` settings write refuses, by name, a CCXT demo row on such an exchange only when the row is new or was switched to demo, compared with the stored section ("<exchange> has no demo mode in CCXT, so QMX cannot read a demo account there; use a live read-only key or another exchange"); and the read path raises P3's `ReadRefused` with the same line instead of a `TypeError`. Edge cases it must survive. The check is not a model validator, so a row saved before this PR still parses and the rest of his settings still load; that row reads with the named line, and an edit to any other connection in the same section still saves. A live row is not checked. An unknown exchange id keeps its own refusal. A ccxt upgrade changes the answer by itself, because nothing is kept by hand. The check opens no socket.

**Depends on.** P3 (`BR/service.py`, `ReadRefused`) and P2b (`QX/service.py`), so it branches from the wave 3 tip.

**Files.**

- [ ] Create `BR/sandbox.py` (`demo_refusal`, cached per exchange id for the process's life).
- [ ] Edit `BR/service.py` (`open_adapter` asks `demo_refusal` before `set_sandbox_mode` and raises `ReadRefused`) and `QX/service.py` (the settings write near line 813 reads the stored section first and refuses a new or newly demo row by name with `ControlError("invalid_brokers", <line>)`).
- [ ] Add tests in new files `QA/qmx-broker/tests/test_sandbox.py` and `QA/qmx-control/tests/test_demo_rows.py`.

**Build.**

- [ ] Reproduce first. A test saves a kraken demo row and reads it, and fails on the parent with the generic line.
- [ ] Add the check, then the write refusal, then the read line.
- [ ] Prove the one fact. With ccxt pinned at 4.5.85 (`QA/qmx-broker/pyproject.toml`), a test computes `demo_refusal` over `ccxt.exchanges` and asserts the set is the 54 names of `BACKLOG.md` line 119.

**You see.**

- [ ] Saving a new kraken demo row in Settings answers 400 with the named line, and nothing is saved.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The computed set equals the 54 names; a binance demo row saves; a kraken live row saves; a new kraken demo row is refused at write; a kraken row switched to demo is refused; an edit to another row while an old kraken demo row is stored saves; that old row parses and reads with the line; a patched socket that raises on connect does not stop the check. Run the broker and control suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The broker and control suites at parent and head. Save `p4-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host saves a new kraken demo row through `PUT /api/settings/connections`. Save `p4-refused.log`. Pass when it answers 400 with the named line and the row is not saved; the parent saves it.
- [ ] Lane 3. A binance demo row through the same route. Save `p4-binance.log`. Pass when it is saved.
- [ ] Lane 4. A kraken demo row written into `settings.toml` by hand, then a broker read, then an edit to another connection. Save `p4-old-row.log`. Pass when settings load, the read says the named line, and the edit saves.
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
  - [ ] One pass of each launch journey on a fresh scratch profile, in order, driven by the commands of Appendix E. `serve` exits 3, then the card makes a new folder, hands over, and the host starts; the card brings in a synthetic old folder, hands over, and the host starts; the card opens an existing folder; a live "Clippings into research" run with its folder over REST; a trigger whose inputs are edited; a template install job; a cTrader sign-in and read on fakes; a shut price door. Save `evidence/ls-v/journeys.log`. Pass when each ends in its expected state with no traceback in any log.
- [ ] `RESUME.md` names the mixed-version note of P5 (a parent CLI against a head host fails on the job view).
- [ ] `just ci` at the stack tip exits 0, or every failure is a named environmental gap.
- [ ] `QUEUE.md` moves on to its next item, the local backup and restore program (G1).

## Appendix A. Prototype evidence

- No prototype was run. Every fact in this plan was read in the code at `629bea16` in the read-only checkout `D:/Temp/ci6-check`, with nothing executed there, because a CI run may be using it. The plan review (`review/plan-loose-strings-edge-cases.md`) checked every line reference and ran one probe from its own scratch folder, which confirmed the 54 no-demo exchanges.
- Facts that changed after the review, each re-read in the code. The handover keeps the card's own last choice, because `resolve` reads `QMX_HOME`, then the pointer, then `~/QMX` (`HM/__init__.py:285-311`). `NoQmxFolder` covers nothing found, old data and refused folders alike. Four paths resume or end a run (REST and adopt, cancel, the ticker, the CLI). A memory row's `source_run_ids` is an annotation, not a field (`MM/engine.py:47-60,437-450`), so the archive follows `derived-from` edges (`Store.edges_of`, `LB/store.py:2007`) instead. A webhook body sits at `webhook.body`. The download templates' test inputs do not meet their schemas. `open_sqlite` refuses a step count that differs from the release. The sign-in checks a grant before it keeps it. A missing `expiresIn` makes a pair due at once. The door's refusals answer `{refused, retryability, context}`. The REST app's CORS allows no PATCH.
- Facts the builders prove by running code (each PR's Build block). The handover answer reaches the client before the card's server stops (P1). A version 5 ledger opens in the parent engine (P2b). The refresh never writes a live grant (P3). The computed no-demo set equals the 54 names at ccxt 4.5.85 (P4). Job rows equal `install()`'s rows (P5). The closed-door route needs the bearer (P6).
- Unproven until lanes run. That Windows lets `serve` bind the card's port at once after the card exits (P1 lane 4). That `uv_build` puts `BR/protocol/` in the wheel without a `pyproject.toml` change (P3 lane 9). That no production path today writes a test run's row into home, workflow or operator scope; `consolidate` has no caller at `629bea16`, and P2a's archive covers it if one appears.

## Appendix B. Not in this program

- **G1, local backup and restore, is the next program.** `POST /api/first-start/restore` answers 501 (`HO/first_start.py:390-391`, `RESTORE_LATER`), and no quick undo, second-drive copy or restore exists. It is design 62 phase 2 (LF8 and LF9), whose defaults design 62 C2 already decides. It is a program of its own, not a PR here.
- Logged to `BACKLOG.md` at program start, from the review. E9 (a copied file whose path is over 260 characters may still fail when the host or a worker opens it later). E15 (a trigger homed on another place can store a This PC path; machines item). E19 (`file_credential` and `refile` also write with `set_password` and leave companion entries). E12's second half (publishing a version could list the triggers its schema breaks). E10's rebuild of a lost test report.
- The triage's 99 LATER lines and 52 OUT lines stay in `BACKLOG.md` and `lows.md`. Among them B111 (the bring-in imports private `qmx_home` names) is a rename that changes no behaviour, and L60a (an older one-shot report keeps its inflated count) stays LATER, because no bring-in has run on his PC.
- How the desktop app's window gets the host's bearer belongs to the desktop packet (engine AD-48). The backend side is fixed in Appendix E.
- Units, UI code, other machines, Library attach and the real server.

## Appendix C. Files two PRs share

| Pair | Shared file | Order |
|---|---|---|
| P1, P2a | none (P1 edits `LB/migrate/from_library_b.py`, P2a edits `LB/adapter.py`) | wave 1, side by side |
| P2a, P2b | `E/control_door.py`, `E/service/runs.py` | P2a first |
| P2a, P2b | `E/triggers/ticker.py` (the resume branch for P2a, `_fire`'s check and `_inputs` for P2b) | P2a first |
| P2b, P3 | none (P3's `QA/qma-harness/src/qma/harness/harness.py`, `BR/server.py` and `HO/venue_session.py` are in no other PR of wave 2) | wave 2, side by side |
| P1, P5 | `HO/jobs.py` (P5 uses it and should not need to edit it) | P1 first |
| P2a, P5 | `E/__main__.py` (`resume` for P2a, `through_host` for P5) | P2a first |
| P5, P6 | none (P5 edits `HO/door.py` and keeps `templates_router`'s signature, P6 edits `HO/host.py`) | wave 3, side by side |
| P1, P6 | `HO/host.py` (P1 moves `recorded_host` out; P6 changes `market_door`, `serve`, `serve_forever` and `start`) | P1 first |
| P3, P4 | `BR/service.py` (`compiled`, the cTrader branch and `read` for P3, the CCXT branch for P4) | P3 first |
| P2b, P4 | `QX/service.py` (`workflows_run` and the trigger edit for P2b, the settings write for P4) | P2b first |

## Appendix D. Defaults

Each is Claude's default, with the reason. He can overrule any of them.

- G2. The card's server exits with a code and the folder, and the desktop app starts the host. AD-48 already makes `qmx-desktop` the one that starts and watches `qmx_host`, and an exit keeps the card's process from having to scrub the environment, take the folder's lock and become the host mid run (Appendix G).
- P1, what the card hands over. The folder of the card's own last finished choice in this process, never what `resolve` finds, so an older pointer, a `QMX_HOME` or a `~/QMX` folder can never be handed over in his name. The handover line goes to stdout, never to a file beside the pointer (ruling 143).
- P1, a found folder that is refused (`NoQmxFolder` kind `refused`, or an unswitched `library.db`). `serve` exits 2 with the line, and the card shows the line with only "open an existing folder" (and restore once G1 lands). It never offers "new" or "bring-in", because his data may sit in that folder (ruling 141).
- P1, his old flat data named by the pointer or the flag (`kind` `old`). `serve` exits 3 and the card offers the bring-in from that folder.
- P1, an unfinished bring-in. `serve` exits 3, and the card shows `unfinished: {folder, line}` and offers the bring-in again into the same folder, which clears only QMX's own unfinished copy there, on his click, after checking that the copy's facts name the same old folder and the old folder is unchanged. It never offers a new folder beside it. His old folder is never touched.
- P1, jobs. A job ends `finished` or `stopped`, with one plain line, and jobs live for the process's life and are never capped (ruling 106). The fast refusals stay synchronous 409 answers.
- P1, exit codes. `serve` and `start` exit 3 only when a first start is due, so the desktop app branches on a code, not on text.
- P2a, a lost test report. A test run that died before its first summary gets its summary and its archive but no test report, because `run_created` holds neither the subgraph nor the caller; the next test of that draft writes one.
- P2b, editing stored inputs. `PUT /api/triggers/{trigger_id}/inputs` replaces the trigger's stored inputs, checked against its pinned version's schema; PUT because the REST app's CORS allows no PATCH. Enabling a timed trigger that misses a required input is refused by name, so an installed download template asks for its `source` instead of failing every night.
- P2b, what a webhook trigger may leave missing. Any required input, since its data arrives with each delivery at `webhook.body`; only the type of its stored keys is checked. The body is not lifted to the top level, so no workflow that reads `inputs.webhook.body` changes. `event`, `after` and `session` triggers follow the same rule (review R3).
- P1, the first-start lock with no `APPDATA`. It falls back to `qmx-first-start.lock` in the system temp folder, so two first starts still exclude each other; nothing is written beside a pointer that does not exist (ruling 143).
- P2b, a rollback to the parent. The parent opens a version 5 ledger (`min_reader` 3) and fires triggers without their stored inputs, which it cannot read. Accepted, because raising `min_reader` would lock the parent out of his ledger.
- P3, the refreshed pair. Checked for a live grant before it is written, written before the read goes on, and never used when the store does not hold it (ruling 135). The refresh lock is a mutex in `keys/`, not a default-closed lock.
- P3, one descriptor copy. The fixture is moved into the package and the tests load the shipped file, so the two cannot drift.
- P4, where the check runs. At write, for new or newly demo rows only, and at read; never as a model validator, so his saved settings always load and an old row never blocks other edits.

## Appendix E. The handover contract (reference)

The desktop app (`qmx-desktop`, engine AD-48) follows this contract. The UI agent wires the first-start card and the host against it.

| Step | The desktop app runs | It reads | Then |
|---|---|---|---|
| 1 | `python -m qmx_host serve --port <p> --ui-origin <origin>` | exit 3, no QMX folder yet, only his old data, or an unfinished bring-in | step 2 |
| 1 | the same | the host answers `/api/health` with the bearer | the UI talks to the host on `<p>` |
| 1 | the same | exit 2 with one line on stderr, a refused folder, store, engine or Library, or bad arguments | show the line; QMX did not start |
| 1 | the same | exit 1 with one line, a host already runs or a bad place name | show the line |
| 1 | the same | exit 4, the port is in use | pick another port, or stop what holds it |
| 2 | `python -m qmx_host first-start --serve --port <p> --ui-origin <origin>` | `GET /api/first-start` answers 200 with no bearer, which only the card does | the UI shows the card |
| 2 | the same | exit 0, last stdout line `{"handover": {"folder": "<folder>", "port": <p>}}` | step 3 |
| 2 | the same | exit 1, stopped with no folder handed over | quit or run step 2 again |
| 2 | the same | exit 2, bad arguments | show the line |
| 2 | the same | exit 4, the port is in use | pick another port |
| 3 | `python -m qmx_host serve --home <folder> --port <p> --ui-origin <origin>` | the host answers `/api/health` with the bearer | the UI talks to the host on `<p>` |

- `start` runs `serve` in the background and returns the same codes, its child's code passed through (P6).
- The card's routes are `GET /api/first-start` (the offer, with `job`, `unfinished` or `refused` when they apply), `POST /api/first-start/new`, `/open`, `/restore` (501 until G1), `/bring-in` (202 with a job; `again` for an unfinished folder), `GET /api/first-start/jobs/{job_id}` and `POST /api/first-start/handover`. A refusal answers 409 with `detail`, its one line. The card binds the loopback only and needs no bearer.
- The host's routes all need the bearer. The desktop app reads it from the keyring entry `qmx/control-token`, as `HO/host.py` `health` does, and hands it to its window. The entry does not exist until the host's first start makes it (`local_token(create=True)`), so the desktop app keeps polling until it reads one. The UI never asks the host for it.
- The same port is used for the card and the host, so the UI keeps one base URL and polls `/api/health` until the host answers.

## Appendix F. Words

- **Bring-in.** Copying his old QMX data into a new QMX folder on the first start. The old folder is only read.
- **Job.** A piece of long work the host runs in the background and the UI reads by id. It is `running`, then `finished` or `stopped`.
- **Step.** Where a job is, in plain words, such as "copying".
- **Line.** The one plain sentence that says why a job stopped or a choice was refused, and what to do next.
- **Handover.** The first-start card's server giving the folder of its last finished choice to the desktop app and exiting, so the desktop app starts the host on it.
- **Card.** The first-start screen's backend, the routes under `/api/first-start`.
- **Unfinished copy.** A folder a bring-in started and did not finish, marked by `data/migration/bring-in-unfinished.txt`. It holds only QMX's copies; his old folder is the original.
- **Stored inputs.** The inputs a trigger keeps and passes to each run it fires, under the payload of that fire.

## Appendix G. Alternatives weighed

- G2 by switching the card's server into the full host in the same process on the same port. Rejected. The host's start order scrubs the environment before the harness is imported (`HO/__main__.py:22-24`), reads the keep list from the chosen folder's `settings.toml`, takes the folder's single-instance lock and records its process. Doing that inside a server that is already serving the card, with a bring-in thread just ended, is more moving parts than an exit, and AD-48 already gives start and supervision to the desktop app.
- G2 by the card starting `serve` as a child process. Rejected. Two parents would then supervise the host, the card and the desktop app.
- G2 by handing over whatever `resolve` finds. Rejected (review F1). It could hand over a folder he never chose in this card.
- C1 by streaming progress on the held request. Rejected. A held request is what the triage found broken, and a job read survives a reload of the card.
- C7 by checking inputs in `run_bundle`. Rejected (review F10). It sees the engine's merged keys and serves test runs, whose catalogue inputs do not meet three schemas.
- C7 by lifting a webhook's body to the top level. Rejected for now. It changes what existing workflows read for a gain no launch journey needs.
- C12 as a pydantic validator on `Connection`. Rejected. One saved row would then stop every broker and connection read from loading.
- C6 by filtering in `MM/engine.py`. Rejected (review F9). Recall and `check_built` already leave archived rows out, so archiving at the summary is the one change.
- P2a by stamping the summary's facts on a second ledger event at start. Rejected. `run_created` is already the run's one start record, read by resume (`E/runner.py:449-470`).

## Appendix H. Gates and calls

- G-LAND. He lands the stack himself.
- No call needs him. No PR touches money, his vocabulary or irreversible scope. Shipping Spotware's MIT-licensed protocol files with QMX is a technical choice. Clearing an unfinished copy happens only on his click in the card.
