# QMX local backup and restore, build program

This program gives his QMX folder copies on This PC, on a second drive he picks and at an off-site place he names, and a restore from any of them, so the first start's "Restore from a backup" works. It is design 62 phase 2 (LF8 and LF9), sections B4, C, F and L, the program `LOOSE-STRINGS-PLAN.md` Appendix B calls G1.
The rules it enforces. Copies are on by default, to the quick undo on This PC, and a copy never stops QMX. A restore never loses or mixes data, because the folder's data before it is set aside whole. A key is never copied in clear; it goes only into the sealed key copy his passphrase opens.
There are 7 PRs. B1 makes copies on This PC and on a second drive. B2 restores a copy and runs the drill. B3 runs the copies on their own inside the host. B4 restores from the first-start card and the command line. B5 restores from Settings and rebuilds memory after a restore. B6 sends copies off-site through rclone. B7 adds the sealed key copy.
The stack roots on `build/ls4` at `6260fe1d`. UI code, the GitHub snapshot's reshape (design 62 C5), server homes and the real server are out of scope (Appendix B).

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a test run, or a SHA. The body is a how-to. The appendices explain and record.

Each PR section opens with a preamble naming the design 62 sections and rulings it serves, what the code does today, and its done line with the edge cases it must survive. Then come the nine blocks `check-plan.mjs` requires.

Path shorthands. `QA/` is `qmx-agents/packages/`. `HO/` is `QA/qmx-host/src/qmx_host/`, `HM/` is `QA/qmx-home/src/qmx_home/`, `BK/` is `HM/backup/` (new in B1), `QX/` is `QA/qmx-control/src/qmx_control/`, `R/` is `QA/qmx-router/src/qmx_router/`, `BR/` is `QA/qmx-broker/src/qmx_broker/`, `E/` is `QA/qmx-engine/src/qmx_engine/`, `LB/` is `QA/qmx-library/src/qmx_library/`, `MM/` is `QA/qmx-memory/src/qmx_memory/` and `AP/` is `QA/qmx-apps/src/qmx_apps/`. Line numbers are at `6260fe1d`.

The store is `D:/QMX-worktrees/qma-ship/wrapup/`, whose `QUEUE.md` names this program as its next item, with `BRIEF-BUILDER.md`, `REVIEWER-BRIEF.md`, `RESUME.md`, `BACKLOG.md`, `lows.md`, `ledger.tsv`, `dispatch/`, `review/` and `evidence/`.

The program follows `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md` with the overrides of `LOCAL-FIRST-PLAN.md`, as `LOOSE-STRINGS-PLAN.md` did. Builders are Claude Opus 5.5 (`poteto-agent`, `model: opus`), at most two at once, never two on one file. A fresh Opus reviewer agent reviews every diff and runs the edge-case lens of `bmad-review` on every PR, because each one reads or writes his data. The coordinator runs the suites, `just ci` and the lanes in the background and allows one fix round. Low findings go to `lows.md`; anything new goes to `BACKLOG.md`. He lands the stack himself.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] Confirm the shell (Windows 11, PowerShell 7.6 and Git Bash; in PowerShell `$H` and `$h` are one variable) and the root (`git rev-parse origin/build/ls4` is `6260fe1d`). Logged in `RESUME.md`.
- [ ] Read the trunk rules with `git show origin/main:CLAUDE.md`, then the rulings file `research/methodology/26-operator-rulings-and-alignment.md` (rulings 106, 116, 135 and 136 to 145), then design 62 sections B3, B4, C, F and L, then Appendices D to F of this plan.
- [ ] No hourly `/loop 1h` tick, because builder and background-job notifications wake the coordinator. Post a short status message to the operator only when a PR opens, a verdict lands or a blocker appears.
- [ ] Never stop to ask him during the build. Stop only for a credential, a real ambiguity in this plan, or a step only he can do (`QUEUE.md`).
- [ ] Before dispatch, add to `BACKLOG.md` the items this plan leaves out (Appendix B lists them).

### Spawn owners

| # | Id | PR | Wave | Branches from | Runs beside | Proving check |
|---|---|---|---|---|---|---|
| 1 | B1 | Copies on This PC and on a second drive | 1 | `6260fe1d` | none | a second round of an unchanged 2,000-file folder copies no file, and the target holds every file's hash |
| 2 | B2 | Restore a copy, and the drill | 2 | the stack tip after wave 1 | B3 | a folder restored from its second-drive copy matches every hash and every row count, and its earlier data is set aside whole |
| 3 | B3 | The host makes copies on its own | 2 | the stack tip after wave 1 | B2 | a host started on a throwaway folder makes its first copy within two minutes and answers `/api/health` in under 1 s throughout |
| 4 | B4 | Restore from the first-start card and the command line | 3 | the stack tip after wave 2 | B5 | the card restores a copy into a new folder on a scratch profile, hands it over, and the host starts on it |
| 5 | B5 | Restore from Settings, the monthly drill and the memory rebuild | 3 | the stack tip after wave 2 | B4 | a restore staged while the host serves is finished, and recall then finds a row only the copy held |
| 6 | B6 | Copies off-site through rclone | 4 | the stack tip after wave 3 | B7 | a round to a `:local:` rclone remote and a restore from it match every hash |
| 7 | B7 | The sealed key copy | 4 | the stack tip after wave 3 | B6 | a key copy sealed in a round opens with the passphrase on a second scratch profile and fills its fake key store |

- [ ] Spawn one fresh Opus builder per PR in the background with `subagent_type: poteto-agent` and `model: opus`, from a dispatch file saved in `dispatch/`. Its first words are exactly "Read the poteto-mode skill's SKILL.md in full, including its Principles section, before any work. Do not spawn sub-agents."
- [ ] Before each wave's second dispatch, record the empty Files intersection of its two PRs in `ledger.tsv` (Appendix C).
- [ ] No PR touches `apps/qmx-ui/`, `~/.claude`, his real home `~/.qmx`, his real QMX folder, `C:/QMX-backup`, `C:/Users/Mubarak/Documents`, `C:/Users/Mubarak/Desktop/DATA_NARL`, his rclone configs (`D:/Tools/rclone/rclone-qmx.conf` and the profile's), Credential Manager or any vault value. Lanes run on throwaway folders and a scratch profile only, and key lanes inject a fake key store.

### PR mechanics, for every PR

- [ ] The coordinator creates `build/br-<id>` from the branch the table names in `D:/QMX-worktrees/bld-br-<id>` before the dispatch. Never `git stash`.
- [ ] The builder opens the PR ready with `gh pr create --base <parent-branch> --head build/br-<id> --repo MubarakHimself/QMX`.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Set `TMP` and `TEMP` to `D:/Temp`, `UV_CACHE_DIR` to `D:/Caches/uv`, put `D:/Tools/rclone` on `PATH`, and set `RCLONE_CONFIG` to an empty file in the worktree, so no rclone call reads his configs.
- [ ] The builder reads the code its Files block names before editing, reproduces each gap with a failing test first, then closes it. It runs `fmt-check`, `lint` and `types` in each package it touched and `tools/secret_scan.py`, reads each exit code, runs only the fast tests it added or changed, and never waits on a long command. It runs the `blast-radius` skill on its diff before the last push and proves the one fact its Build block names.
- [ ] Every line a person reads (a refusal, a job's line, a round's line, a doctor row) is plain words, names the folder or place, and says what to do next. No QMX-internal cap, ceiling or default-closed lock is added anywhere (rulings 106 and 137). A mutex that two writers take in turn is not a default-closed lock.
- [ ] Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. PR bodies end with the Claude Code line.

### Verdict and merge, for every PR (append to the stack, merge on his go)

- [ ] At the code-ready head the coordinator runs the touched suites with `-n 2` and lanes 1 to 4 in the background, reads every package block of each log (not its tail), and saves the logs. A fresh Opus reviewer agent (one per PR, `model: opus`, told not to spawn sub-agents) reads the PR section, the full diff, the edge-case lens and those logs, and writes `review/<id>-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] Blockers go back to the same builder for one fix round. Low findings go to `lows.md`.
- [ ] `ledger.tsv` gets head, parent and patch-id.
- [ ] Parallel PRs of one wave join the stack with merge commits, never a rebase. `just ci` runs at the stack tip once at the end, with `D:/Tools/rclone` on `PATH`, under `D:/QMX-worktrees/.ci-lock`.
- [ ] He lands the stack himself from the one full list the coordinator sends when `QUEUE.md` is empty.

### Boot recipe, for every live lane

- [ ] `git worktree add --detach D:/Temp/br-<id>-check <head>`, then `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`. A lane that needs the parent adds a second worktree at the parent the same way.
- [ ] A lane runs on a throwaway QMX folder under `D:/QMX-worktrees/qma-ship/wrapup/homes/br-<id>-<lane>/`, made with `qmx_home.resolve(..., create=True)`, with `USERPROFILE`, `APPDATA`, `LOCALAPPDATA` and `HOME` on a scratch profile under the same folder, so the pointer file lands there too, and with `QMX_HOME` unset.
- [ ] Every lane's `settings.toml` names its targets explicitly (`[[backup.targets]]` under the lane's own folder, or `targets = []`), so the default second drive is never computed against this PC's real drives and nothing is written to `C:/QMX-backup`. The default target is checked only in process, with fake drives and fake free space.
- [ ] A lane that starts a host or a first-start card injects its bearer, turns the memory database off (`hindsight_runs` patched), and uses a port of its own, because on Windows pg0 writes his real profile (design 62 L7).
- [ ] A synthetic folder is made by B1's test builder (`filled_folder` in `QA/qmx-home/tests/backup_fixtures.py`, with `files`, `stores`, `once_bytes` and `long_path` parameters), never copied from `~/.qmx` or his QMX folder.
- [ ] Save captures as `evidence/br-<id>/check-<slug>.log`, then remove the check copy with `git worktree remove` and confirm no `qmx_host`, `claude`, `rclone` or `node` process from the lane is left.

## Make copies on This PC and on a second drive (B1)

Design 62 C1, C2 and B3, with guards L1 and L6. Rulings 106, 136, 141 and 143. Today `backups/` holds only LF3's pre-change copies of the one store an upgrade changes (`snapshot`, `HM/versions.py:235-302`), logged in `backups/backups.jsonl` (`_log`, `HM/versions.py:729-734`). Nothing copies the folder's data on a schedule or to another drive. The weekly GitHub snapshot copies only small stores (`QX/backup.py:60-198`), and each mini app's volume backup goes to an rclone remote (`AP/backup.py:122-165`); neither holds the Library's blobs, the prices, the chats or the ledger. The copy and hash helpers a copy needs live in the bring-in (`long_path`, `_plain`, `copy_file` and `sha256_of` at `HO/bring_in.py:195-249`, `Held` and `hold` at `HO/bring_in.py:817-857`, `_locked` and `_lock` at `HO/bring_in.py:968-994`), where `qmx_home` cannot import them. Done when one standard-library module under `BK/` makes a copy of `data/` into the quick undo in `backups/quick/`, sends it to a folder target at `<target>/QMX-backup/<home_id>/` holding each file once by sha256 in a pool and one manifest per copy, thins every place by its keep rule, refuses whole before writing when room is short, and logs every round in `backups/backups.jsonl`; the helpers live in `HM/files.py` and the bring-in imports them; and `[backup]` parses into one plan with a default second drive when he names none. Edge cases it must survive. A SQLite store written during the copy is copied as committed, through `VACUUM INTO` (probe in Appendix A). A Library put during a round never leaves a copied ref naming an object the copy lacks, because the stores and the Library's logs are copied before the files written once are listed (Appendix D, the order). A store whose file and `-wal` are unchanged since the last copy is not copied again (L6), and the log records each copy's seconds and bytes. A second round of an unchanged folder writes nothing but its log line. A round killed mid copy leaves only names ending `.qmx-copying` and a copy folder with no `manifest.jsonl`, which the next round removes; a copy counts only once its manifest is in place, and the manifest is written last. A target with too little room refuses whole with one line and writes nothing. The default target is the largest fixed drive that is not the folder's own drive, and never a drive the first copy would leave below the larger of 1 GiB (`FLOOR_BYTES`, `HM/versions.py:39`) and 10 % free (L1); on his PC, with the folder on drive D and drive C short of room, no default is set, and the plan's line says "your work has no copy on another drive". A target inside the QMX folder is refused by name; a target on the folder's own drive is kept with a line saying it does not survive a dead disk. A link or junction is never followed and never copied; the harness makes `claude-relayed/projects` again at launch (`_link_projects`, `QA/qma-harness/src/qma/harness/home.py:219-234`). A path over 260 characters copies (`long_path`). A target that another QMX folder wrote to since this folder last did is refused by name until he carries on (the fork guard, Appendix D). An exFAT USB disk works, because nothing on a target needs a hard link. The plan login files and every file of `LEFT_OUT` (Appendix D) are never in a copy.

**Depends on.** The root `6260fe1d`.

**Files.**

- [ ] Create `HM/files.py` with `long_path`, `plain` (today `_plain`), `copy_file`, `sha256_of`, `Held` and `hold` (with `_locked` and `_lock`), moved from `HO/bring_in.py` unchanged. `HO/bring_in.py` and `HO/first_start.py` (which imports `Held` and `hold` at `HO/first_start.py:50-64`) import them from there, and the bring-in's own copies are deleted.
- [ ] Edit `HM/versions.py`. `_log` becomes the public `log_line(layout, record)` and a reader `log_lines(layout)` returns the parsed lines, skipping a torn last line; `snapshot`, `_step_failed` and `completed_copies` use them.
- [ ] Create `BK/__init__.py` (the module's words, Appendix F) and `BK/plan.py`. `parse(section) -> Plan` reads `[backup]` (Appendix D shape) into `quick_undo`, `targets`, `leave_out`, `drill` and `keys` (kept raw for B7), ignores the mini-app volume keys and `repository` (`APP_KEYS`), and refuses a bad row by name with `PlanRefused`. A `Target` has `id`, `kind` (`folder` here), `path`, `every` (`hour`, `day` or `week`), `at`, `keep` and `on`. `default_target(layout, drives, free)` is A1's drive list read through `qmx_home._fixed_drives` (`HM/__init__.py:732-738`). `repository_of(target, layout)` and `source_of(document)` build a repository from a target row or from a card's `source`, the one factory B4 and B6 use.
- [ ] Create `BK/snapshot.py`. `LEFT_OUT` and `WRITE_ONCE` as tables (Appendix D). `make(layout, *, previous, progress) -> Manifest` walks `data/`, copies each SQLite file by `VACUUM INTO` through a connection opened as `snapshot` opens one (`HM/versions.py:279-280`) and records its row count per table, copies each `*.jsonl` up to its last full line, copies every other mutable file whole, hashes each copy as it is written and moves it into the quick pool by sha256, then lists the files written once, taking a hash from the previous manifest when size and `mtime_ns` match and hashing the file otherwise, in the order of Appendix D. The manifest's first line is its header (`format` `qmx-backup/1`, `home_id`, `stamp`, `why`, the release that made it, `platform.node()`, the folder's path, and the label's `[stores]`).
- [ ] Create `BK/repository.py`. The `Repository` protocol (`pool_has`, `put_pool`, `put_copy`, `copies`, `manifest`, `read_extra`, `fetch`, `drop`, `sweep`, `room`) and `FolderRepository`, used for `backups/quick/` and for a folder target, with `backup.toml`, `pool/ab/cd/<sha256>` and `snapshots/<stamp>/manifest.jsonl`. In the quick undo a file written once stays where it is in `data/` and its manifest line says so (`at: live`); on a target every file is pooled.
- [ ] Create `BK/keep.py` with the pure `kept(copies, now, keep) -> frozenset[str]`, which also ends LF3's `backups/pre-*` copies 30 days after the first target copy made after them (design 62 B3; nothing removes them today), and `BK/round.py` with the pure `due(last, now, every, at)`, `run_round(layout, plan, *, now, only=None, sealed_keys=None, progress=None) -> RoundReport` under `backups/backups.lock` (taken with `hold`), `quick(layout, why)` for one copy at once, the fork guard read from the log, and the round's log lines. `sealed_keys` returns bytes written beside a target copy's manifest as `keys.sealed.json`, never in the quick undo; B7 passes it, and B1 tests it with a fake.
- [ ] Add `QA/qmx-home/tests/backup_fixtures.py` (`filled_folder`), `test_backup_plan.py`, `test_backup_snapshot.py`, `test_backup_round.py` and `test_backup_keep.py`. Edit `QA/qmx-host/tests/test_bring_in.py` only where it imports a moved name.

**Build.**

- [ ] Move the helpers first and run the host suite, so the move alone changes nothing.
- [ ] Then the plan, the snapshot, the folder repository, the keep rule and the round, each step ending with its own test run.
- [ ] Prove the one fact the copy rests on. A test runs `make` with a hook that puts a Library item through `Store` at each step boundary, and asserts that every object any copied `refs/` line names is in the manifest. It also runs `make` while a second thread commits to the engine ledger in a loop, and each copied store passes `PRAGMA quick_check` with the committed rows.

**You see.**

- [ ] On a throwaway folder, `run_round` with one folder target writes `backups/quick/snapshots/<stamp>/manifest.jsonl` and `<target>/QMX-backup/<home_id>/snapshots/<stamp>/manifest.jsonl`, and a second call with nothing changed logs a round line with `"result": "unchanged"` and copies no file.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The moved helpers behave as at the root; the plan parses a full section, refuses an unknown kind, a duplicate id, a target inside the folder and a bad `at`, and leaves the app keys alone; `default_target` gives none for his drive sizes and `C:/QMX-backup` for a roomy fake C:; a copy holds every file but `LEFT_OUT`, no link and no plan login; a 300-character path copies; each store's row counts equal the live store's; an unchanged store reuses its pool entry; `due` answers for hour, day and week across a PC that was off; `kept` keeps 48 hours of hourly copies then one a day for 7 days, and 14 daily, 8 weekly and 12 monthly on a target; a `before-upgrade` copy and an LF3 `pre-*` copy are kept until 30 days after the next target copy; a sweep removes only pool files no kept manifest names; a full target refuses before writing; a killed round's leftovers are removed by the next; the fork guard refuses and carry-on clears it; `keys.sealed.json` lands beside a target manifest and never in the quick undo. Run the home and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The home and host suites at parent and head. Save `b1-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A first round of a synthetic folder (2,000 files, three 50 MB SQLite stores, 1 GB written once, one 300-character path, one junction, one plan login file) to a folder target in the lane folder. Save `b1-first.log`. Pass when the target manifest lists every file not left out, each pooled file's sha256 equals its source's, each store's row counts equal the live store's, and no junction and no `.credentials.json` is listed.
- [ ] Lane 3. A second round with nothing changed, then a third after one row is added to one store. Save `b1-unchanged.log`. Pass when the second writes no pool file and logs `unchanged`, and the third pools exactly one new file.
- [ ] Lane 4. A round while one process commits to the engine ledger and another puts Library items in a loop. Save `b1-live-writes.log`. Pass when every copied store passes `PRAGMA quick_check` and every object the copied `refs/log.jsonl` names is in the manifest.
- [ ] Lane 5. Kill the round's process during the send, then run a round again. Save `b1-killed.log`. Pass when the first leaves only `.qmx-copying` names and a copy folder with no manifest, and the second removes them and finishes.
- [ ] Lane 6. A target whose free space is patched to less than the copy needs. Save `b1-full.log`. Pass when the round refuses with one line naming the room and the target holds no new file.
- [ ] Lane 7. `default_target` in process with fake drives, once with his sizes (the folder on drive D, drive C with 22 GB free of 237 GB) and once with a roomy C:. Save `b1-default.log`. Pass when the first gives no default with the warning line, the second gives `C:\QMX-backup` as a plan value only, and nothing is written outside the lane folder.
- [ ] Lane 8. Sixty days of fake copies on a target, then a round. Save `b1-keep.log`. Pass when the kept set is 14 daily, 8 weekly and 12 monthly copies and the target's pool holds only files a kept manifest names.
- [ ] Lane 9. Two folders with one `home_id` send to one target in turn. Save `b1-fork.log`. Pass when the second is refused by name with the first folder's machine and path, and after carry-on its round sends.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, then remove the throwaway folders, list processes and list `C:/QMX-backup`. Save `b1-processes.log`. Pass when every exit code is 0, nothing from the lanes is left, and `C:/QMX-backup` is as it was before the lanes.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for lane 2's first round to a folder target, for lane 3's unchanged round, and for a plain `shutil.copytree` of the same `data/` to the same drive. The parent has no copies, so the plain copy is the baseline of the same work.
- [ ] Probe. Each of the three, three times, interleaved, on fresh target folders.
- [ ] Baseline. Record the plain copy's median first.
- [ ] Rule. The first round's median is within 1.5 times the plain copy's, or the PR fails. The unchanged round is under 2 s at its median, an absolute budget.

**Review gate.** None. B1 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on `build/ls4`.

## Restore a copy, and run the drill (B2)

Design 62 C3 and B4, with guard L2. Rulings 136 and 141. Today nothing restores; the card's restore answers 501 (`RESTORE_LATER`, `HO/first_start.py:80-83,561-562`). The store refusals tell him to "restore the copy taken before the upgrade" (`_too_new` and `_unreadable_entry`, `HM/versions.py:432-439,639-649`), which no tool does. A store of plain files (the Library, the prices, chats, settings) keeps its version only in the label, outside `data/` (`HM/stores.py:1-7`, `_entry` at `HM/versions.py:660-667`), so a restore that copies `data/` alone would leave the label naming the wrong versions. The Library rebuilds `catalog.db` whenever it is missing (`LB/store.py:17`), and an operator purge leaves `blobs/tombstones/<hex>.json` and removes the bytes (`LB/store.py:2175-2217`). Done when `BK/restore.py` offers `copies(repository)` (each copy by date, with why it was made, files, bytes, the release that made it and its machine), `stage(layout, repository, stamp, *, progress) -> Staged`, which rebuilds `data/` from the copy into `backups/restoring-<stamp>/data/` and checks every file's sha256 and every store's row counts against the manifest, `finish(layout) -> Finished | None`, which sets the folder's `data/` aside whole into `backups/before-restore-<stamp>/data/` with a copy of the label, moves the staged `data/` in, writes the copy's plain-file store versions into the label and logs the restore, `cancel(layout)`, and `drill(layout, repository, *, sample, rng)`. Edge cases it must survive. A copy made by a newer QMX whose manifest format this release does not read is refused by name. A copy whose stores need a newer QMX (the `_closed` rule, `HM/versions.py:442-443`) is refused by name before anything is written. A copy of another QMX folder (another `home_id`) is refused, unless the folder's `data/` is new and empty, and then the label takes the copy's `home_id`. A manifest path that is absolute, holds `..`, a drive or a backslash, or leaves `data/` is refused, because a target is a disk he plugs in. A quick-undo copy whose file written once is gone or changed is refused whole, naming the file and offering the second drive. A blob tombstoned in the folder or in the copy is never placed, and its tombstone is; `finish` drops again any blob the folder tombstoned between the stage and the finish. A file written once whose sha256 matches the folder's own file is hard-linked from it, falling back to a copy where the drive refuses links. The plan login files are carried over from the set-aside data, because they are This PC's sign-in and never in a copy. Room is checked before the first write. A second staged restore is refused while one waits. A kill at any step leaves `restore.json` naming where each folder is, and the next `finish` completes the same restore; a staging that never finished is cleared by the next `stage`. No link is ever placed. The drill restores one copy's mutable files and a random sample of its pooled files into `cache/restore-drill/`, checks their hashes, `PRAGMA quick_check` and row counts, checks room first, removes its folder when it ends, and never reads or writes `data/` (L2).

**Depends on.** B1 (`BK/`, `HM/files.py`).

**Files.**

- [ ] Create `BK/restore.py` with `copies`, `stage`, `finish`, `cancel`, `drill` and their result types, under `backups/backups.lock`.
- [ ] Edit `BK/repository.py` and `BK/snapshot.py` only where restore needs a read B1 left out (the manifest header's label and store versions, `fetch` into a staging folder).
- [ ] Add `QA/qmx-home/tests/test_backup_restore.py` and `QA/qmx-home/tests/test_backup_drill.py`.

**Build.**

- [ ] Reproduce first. A test copies a filled folder with B1, changes and deletes files in it, and fails because no restore exists.
- [ ] Add `copies` and `stage` with every check, then `finish` and `cancel`, then the drill, each with its test.
- [ ] Prove the one fact. `finish` is idempotent, so a test kills it after each of its steps (journal written, `data/` set aside, staged `data/` moved in, label written, log line written), runs it again, and asserts one end state each time.

**You see.**

- [ ] On a throwaway folder with a second-drive copy, `stage` then `finish` leave `data/` equal to the copy file for file and hash for hash, and `backups/before-restore-<stamp>/data/` equal to the folder's data before the restore.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A restore reproduces every hash and every row count; the earlier data is set aside whole; a new folder takes the copy's `home_id`; another home's copy is refused; a newer format and stores too new are refused; an escaping path is refused with nothing written outside the staging folder; a quick copy missing a file written once is refused whole; a tombstoned blob is not placed; the plan login is carried over; links are made from matching files and copies made where a link is refused; short room refuses before writing; a second stage is refused; each kill point resumes; the label's plain-file store entries equal the copy's; the drill passes on a good copy, fails by name on a damaged pooled file, and leaves `data/` and its own folder as they were. Run the home suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The home and host suites at parent and head. Save `b2-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. B1's lane 2 folder, copied to a target, then 100 files changed and 20 deleted, then restored from the target into the same folder. Save `b2-same-folder.log`. Pass when every file's sha256 and every row count equals the manifest, and the set-aside data's listing equals the listing taken before the restore.
- [ ] Lane 3. The same copy restored into a fresh folder on a second scratch profile. Save `b2-new-folder.log`. Pass when the label's `home_id` equals the copy's and `data/` matches the manifest.
- [ ] Lane 4. `finish` killed after it set `data/` aside, then run again. Save `b2-killed.log`. Pass when `data/` is the copy and the set-aside folder holds the earlier data whole.
- [ ] Lane 5. A quick-undo copy restored after one of its files written once was deleted. Save `b2-quick-gone.log`. Pass when the restore is refused naming the file and `data/` is unchanged.
- [ ] Lane 6. Another folder's copy restored into a folder with data. Save `b2-other-home.log`. Pass when it is refused by name and nothing is written.
- [ ] Lane 7. A copy whose manifest is edited to name `../outside.txt`. Save `b2-escape.log`. Pass when it is refused and no file appears outside the staging folder.
- [ ] Lane 8. A blob purged through `Store.purge` after the copy, then the restore. Save `b2-purged.log`. Pass when the blob's bytes are not in `data/` and its tombstone is.
- [ ] Lane 9. The drill on lane 2's target, then on a target with one pooled file truncated. Save `b2-drill.log`. Pass when the first passes, the second fails naming the file, `cache/restore-drill/` is gone after both, and `data/` hashes as before.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, then remove the throwaway folders and list processes. Save `b2-processes.log`. Pass when every exit code is 0 and nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for lane 3's restore into a fresh folder and for a plain `shutil.copytree` of the target's pool to the same drive, and seconds for a restore from the quick undo of lane 2's folder (links plus hashes). The parent has no restore, so the plain copy is the baseline of the same bytes.
- [ ] Probe. Each three times, interleaved, on fresh folders.
- [ ] Baseline. Record the plain copy's median first.
- [ ] Rule. The fresh-folder restore is within 2 times the plain copy's median, or the PR fails. The quick-undo restore is under 30 s for lane 2's folder, an absolute budget.

**Review gate.** None. B2 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the wave 1 tip; B3 joins it by a merge commit.

## Make copies on their own inside the host (B3)

Design 62 C2 (when) and F step 14, with guards L1 and L6. Rulings 106, 136, 137 and 140. Today the host starts no backup of the folder (`serve`, `HO/host.py:704-844`). The control service's `BackupSchedule` sweeps mini-app volumes only, and only once `[backup] remote` is set (`QX/service.py:1600-1613`, `AP/backup_schedule.py`). `_settings_put` passes every `[backup]` key but `repository` to the volumes' `BackupSettings` (`QX/service.py:845-854`), a strict model (`extra="forbid"`, `AP/manifest.py:63-64`), so any new key there is refused today. Done when the host runs one `Backups` service (`HO/backups.py`) that reads the plan from `control.settings_get("backup")` every minute, runs a round on its own thread when the quick undo or a target is due, and never holds a request; a round he must act on (a full target, a refused row, the fork guard) opens an inbox incident `backup:<target>` through `InboxTable.incident` (`E/ledger/inbox_table.py:220`); one doctor row `backups` (`harness.doctor_from`, `HO/host.py:755`) says when each place last got a copy; routes under `/api/backups` read the plan, the targets and their copies and start a round now as a job (`HO/jobs.py`); `python -m qmx_host backup` runs one round in the foreground; and the control service checks `[backup]` with `BK/plan.parse` and passes only `APP_KEYS` to the volumes' model. Edge cases it must survive. A folder with no `[backup]` gets the quick undo every hour and the default second drive when one has room. A target he set `on = false`, or `targets = []`, is never written, and the doctor row says the work has no copy on another drive. A round started while another runs answers 409 naming the running job. A target that is not there (an unplugged USB disk) is skipped with a line and stays due, with no incident, and the doctor row names how long ago it last got a copy. A host stopped mid round leaves what B1's killed round leaves, and the next round cleans it. Settings edited while the host runs take effect at the next sweep, as `BackupSchedule` reloads its own (`AP/backup_schedule.py:27-28`). A `PUT /api/settings/backup` with a bad target answers 400 naming the row, and the volumes' keys save as before. Every route sits behind the bearer, because `create_app` includes each extra router with `Depends(authenticate)` (`QX/server.py:462-463`). The first sweep runs one sweep after the host serves, so a start is never slowed by a copy. The service runs on every role; only This PC gets a default second drive, because `_fixed_drives` lists none off Windows.

**Depends on.** B1 (`BK/round.py`, `BK/plan.py`). It shares no file with B2.

**Files.**

- [ ] Create `HO/backups.py`. `Backups(layout, control, *, clock, sealed_keys=None)` with `run()` (the sweep), `doctor_line()`, `view()`, and `backups_router(backups)` with `GET /api/backups`, `GET /api/backups/targets/{target_id}/copies`, `POST /api/backups/run` (202 with a job, body `{target}` optional), `GET /api/backups/jobs/{job_id}` and `POST /api/backups/targets/{target_id}/carry-on`.
- [ ] Edit `HO/host.py`. In `serve` (near line 781) append `backups_router` to `answering`, start `backups.run()` beside `replicator.run()` (near line 804) and cancel it with the other tasks (near line 822), and add `harness.doctor_from(backups.doctor_line)` beside the Library's row (near line 755).
- [ ] Edit `HO/__main__.py`. A `backup` command (`--home`, `--target`) runs one round in the foreground, prints its lines, and exits 0 when it copied or had nothing to copy and 1 when a round was refused or another round holds `backups/backups.lock`.
- [ ] Edit `QX/service.py`. `_settings_put` for `backup` (near line 845) checks the section with `BK/plan.parse` and validates only `APP_KEYS` with `BackupSettings`; `_backup_settings` (near line 1609) reads only `APP_KEYS`.
- [ ] Add `QA/qmx-host/tests/test_backups_service.py` and `QA/qmx-host/tests/test_backups_routes.py`, and the settings cases in a new `QA/qmx-control/tests/test_backup_section.py`.

**Build.**

- [ ] Reproduce first. A test writes a `[backup.quick_undo]` table through the settings route and fails on the parent with `invalid_backup_settings`.
- [ ] Add the settings check, then the service and its sweep with an injected clock, then the routes, the doctor row, the incident and the command.
- [ ] Prove the one fact. A round never holds a request. A test starts the host app with a round of B1's lane 2 folder running on its thread and asserts every `/api/health` call during it answers in under 1 s.

**You see.**

- [ ] A head host on a throwaway folder with one folder target answers `GET /api/backups` with the quick undo and the target, each with its last copy's time and `"result": "copied"`, within two minutes of its start.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The sweep runs a round when due and not otherwise; a second run answers 409; an unplugged target is skipped with a line and no incident; a full target opens one incident and counts a second failure on it; the doctor row reads each place's age; a bad target is refused 400 by name; the volumes' keys still validate and save; the routes answer 401 with no bearer; the command exits 0, and 1 when the lock is held. Run the host, control and home suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The host, control and home suites at parent and head. Save `b3-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host on a filled throwaway folder with one folder target in the lane folder. Save `b3-first.log`. Pass when `GET /api/backups` shows a copy in the quick undo and the target within two minutes of start; the parent host makes none.
- [ ] Lane 3. `/api/health` polled every 200 ms during lane 2's first round. Save `b3-health.log`. Pass when every call answers in under 1 s.
- [ ] Lane 4. `POST /api/backups/run` twice in a row, then the job read until it ends. Save `b3-run.log`. Pass when the first answers 202, the second 409 naming the first job, and the job ends `finished` with each place's line.
- [ ] Lane 5. The target folder renamed away while the host runs, then back. Save `b3-unplugged.log`. Pass when the round skips it with a line, no incident opens, the doctor row names its age, and the next round after it is back sends.
- [ ] Lane 6. A target whose drive check is patched to too little room. Save `b3-full.log`. Pass when an incident `backup:<target>` is open and the doctor row is not ok.
- [ ] Lane 7. `PUT /api/settings/backup` with a target of kind `tape`, then one with the volumes' `remote` and `bucket`. Save `b3-settings.log`. Pass when the first answers 400 naming the row and the second saves as at the parent.
- [ ] Lane 8. `python -m qmx_host backup --home <folder>` with no host, then again while a host's round holds the lock. Save `b3-command.log`. Pass when the first exits 0 with its lines and the second exits 1 with one line.
- [ ] Lane 9. A head host with `targets = []`. Save `b3-no-target.log`. Pass when the quick undo gets a copy, nothing else is written, and the doctor row says the work has no copy on another drive.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, then remove the throwaway folders, list processes and list `C:/QMX-backup`. Save `b3-processes.log`. Pass when every exit code is 0, nothing from the lanes is left, and `C:/QMX-backup` is as it was.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from `serve` to the first 200 on `/api/health` at parent and head, and `/api/health`'s median milliseconds at head during a round and with no round.
- [ ] Probe. Three host starts at each side, interleaved, then fifty health calls at head during lane 2's round and fifty after it.
- [ ] Baseline. Record the parent's median start first.
- [ ] Rule. Head's start is within 5 % of the parent's median, or the PR fails. Health during a round is within 50 ms of health with no round, an absolute budget, because the parent has no round.

**Review gate.** None. B3 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Joined onto B2 by a merge commit (the two share no file).

## Restore from the first-start card and the command line (B4)

Design 62 F step 2, C3 and B4. Rulings 139, 141 and 142. Today `POST /api/first-start/restore` answers 501 (`HO/first_start.py:561-562`) and `python -m qmx_host restore` prints `RESTORE_LATER` and exits 2 (`HO/__main__.py:175-177`). The card offers restore only when no folder is found (`HO/first_start.py:336-341`). A found folder that is refused gets only "open" (`HO/first_start.py:336-337`), and `serve` exits 2 for a refused store (`HO/__main__.py:94-98`), so a store too new is a dead end although its line says to restore the copy taken before the upgrade (`HM/versions.py:639-649`, `HM/__init__.py:341-348`). Before an upgrade only the changed store is copied (`_copy_first`, `HM/versions.py:520-537`), so going back one store would leave the others at a later moment. Done when the card lists the copies a source holds (`POST /api/first-start/copies`) and restores one as a job (`POST /api/first-start/restore`, 202, read by `GET /api/first-start/jobs/{job_id}`) into a new folder, made as `new` makes it, or into the found folder it refused, then counts it as a finished choice so the handover answers it; `GET /api/first-start` offers restore for a refused folder and for a folder with a refused store, and carries `second_drive`, the default target and its line; `python -m qmx_host restore` lists and restores from the command line; `serve` and `start` finish a staged restore before they read the folder's stores; when `check_open` says a store upgrades, `serve` first takes a quick copy of the whole folder tagged `before-upgrade`; and the refusal lines name the restore. Edge cases it must survive. A restore while a host serves the folder answers 409 naming its process (`recorded_host`, `HO/process_record.py:16-29`). A restore while a bring-in or another restore runs in the card answers 409 naming the job, and the card takes `first-start.lock` as every other choice does. A restore into one of A1's never places is refused by `Places.refusal`, and a removable drive gets its warning. A copy of another folder into a found folder answers 409 by name. A card killed mid stage leaves the folder's data unchanged and no `first-start.lock`; the next restore clears the unfinished staging. A card or host killed mid finish is completed by the next `serve`. A `before-upgrade` copy that cannot be made (room) is one line on stderr and the start goes on, because the store's own pre-change copy still guards its upgrade. `restore` with no `--copy` lists the copies and changes nothing. The card answers with no bearer on the loopback only, as today.

**Depends on.** B2 (`BK/restore.py`) and B3 (`HO/__main__.py`).

**Files.**

- [ ] Edit `HO/first_start.py`. Delete `RESTORE_LATER`; `restore` (near line 561) takes `{folder, source, copy}`, refuses fast cases with 409, and starts a `restore` job that stages and finishes under the held lock; add `POST /api/first-start/copies` (`{source}`, answering the copies by date); `offer()` adds restore to the choices for a refused folder and for a folder whose `check_open(layout).held_back` holds a refused store, and carries `second_drive` from `BK/plan.default_target`; `Offer.lines` names the restore command; the card's job check covers both kinds.
- [ ] Edit `HO/__main__.py`. `restore` takes `--home`, `--from` (a folder target's path), `--copy` and `--create`, lists when `--copy` is left out, exits 0 restored, 1 when a host serves the folder, and 2 when refused; `serve` and `start` call `BK/restore.finish(layout)` right after `resolve` (near line 82), and take `BK/round.quick(layout, "before-upgrade")` when `check_open` has an `upgrades` verdict, before the host opens any store.
- [ ] Edit `HM/versions.py` (`_too_new` and `_unreadable_entry` say "restore a copy from before the upgrade, with Restore from a backup on the start screen or python -m qmx_host restore") and `HM/__init__.py` (the newer-format line in `_opened`, near line 341, the same).
- [ ] Edit the tests that pin those lines and the 501. `QA/qmx-home/tests/test_versions.py:102,257,286`, `QA/qmx-engine/tests/test_ledger_versions.py:76,147` and `QA/qmx-host/tests/test_bring_in.py:458-471`. Add `QA/qmx-host/tests/test_card_restore.py` and `QA/qmx-host/tests/test_restore_command.py`.

**Build.**

- [ ] Reproduce first. A test posts a restore to the card and gets 501 on the parent.
- [ ] Add the card's routes and the offer, then the command, then the finish at start, then the `before-upgrade` copy, then the lines, each with its test.
- [ ] Prove the one fact. `serve` finishes a staged restore before any store opens. A test stages a restore whose engine ledger differs from the folder's, runs `main(["serve", ...])` with the host's `serve_forever` patched to read the ledger's row count and stop, and asserts it read the copy's count.

**You see.**

- [ ] On a scratch profile with no QMX folder, the card lists the copies of a lane target, `POST /api/first-start/restore` answers 202, the job ends `finished`, the handover prints `{"handover": {"folder": "<folder>", "port": <p>}}`, and `serve --home <folder>` answers `/api/health` on that folder.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. 

- [ ] The card lists copies; restore into a new folder takes the copy's `home_id` and then hands over; restore into a refused folder works; another home's copy is 409; a host on the folder is 409; a running bring-in is 409; a never place is refused; a refused store gets the restore choice; the command lists, restores, and exits 1 with a host up; `serve` finishes a staged restore first; a store that upgrades gets a `before-upgrade` copy first, and a failed copy is one line and the start goes on; each refusal line names the restore. Run the host, home and engine suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The host, home and engine suites at parent and head. Save `b4-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. The card on a scratch profile with no folder lists a lane target's copies, restores one into a new folder, and hands over; then `serve --home <folder>`. Save `b4-card.log`. Pass when the job ends `finished`, the handover line names the folder, the host answers `/api/health`, and `data/` matches the manifest; the parent answers 501.
- [ ] Lane 3. A folder whose engine ledger is marked one version past this release with `min_reader` above it, and a `before-upgrade` copy from before. Save `b4-too-new.log`. Pass when `serve` exits 2 with the line naming the restore, the card shows the folder refused with open and restore, the restore of that copy finishes, and `serve` then starts.
- [ ] Lane 4. A folder whose engine ledger is one version behind this release, then `serve`. Save `b4-before-upgrade.log`. Pass when the quick undo holds a copy tagged `before-upgrade` whose ledger is at the older version, and the host starts with the ledger upgraded.
- [ ] Lane 5. `python -m qmx_host restore --home <folder> --from <target>` with no `--copy`, then with one, then again while a host serves the folder. Save `b4-command.log`. Pass when the first lists and changes nothing, the second exits 0 with `data/` matching, and the third exits 1 with one line.
- [ ] Lane 6. A restore staged with `BK/restore.stage`, then `serve`. Save `b4-finish-at-start.log`. Pass when `data/` is the copy before the host answers and the earlier data is set aside.
- [ ] Lane 7. The card killed mid stage, then started again. Save `b4-killed.log`. Pass when no `first-start.lock` is left, `data/` is unchanged, and a new restore finishes.
- [ ] Lane 8. A copy of another folder restored through the card into a found folder. Save `b4-other-home.log`. Pass when it answers 409 by name and nothing is written.
- [ ] Lane 9. A folder on a drive patched as removable, and a folder inside `APPDATA`. Save `b4-places.log`. Pass when the first restores with its warning and the second is refused by name.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, then remove the throwaway folders and list processes. Save `b4-processes.log`. Pass when every exit code is 0 and nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from `serve` to the first 200 on `/api/health` with nothing staged, at parent and head, and seconds for lane 2's card restore end to end.
- [ ] Probe. Three starts at each side, interleaved, and lane 2's restore three times on fresh scratch profiles.
- [ ] Baseline. Record the parent's median start first.
- [ ] Rule. Head's start with nothing staged is within 5 % of the parent's, or the PR fails. The card restore is within 5 s of B2's fresh-folder restore median for the same copy, an absolute budget for the card's own work.

**Review gate.** None. B4 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the wave 2 tip; B5 joins it by a merge commit.

## Restore from Settings, run the monthly drill and rebuild memory (B5)

Design 62 C3 (from Settings, the drill), with guard L2. Rulings 136 and 141. Today the host has no restore and no drill. The memory engine rebuilds both its indexes from the Library's live rows with `rebuild("all")` (`MM/engine.py:312-320`), its FTS file sits at `<home>/memory/fts.db` (`MM/engine.py:67,102`, `HO/host.py:525`), and a copy holds neither that file nor Hindsight's database (B1's `LEFT_OUT`), so a restored folder's recall is empty until something rebuilds it. Done when `POST /api/backups/restore {target, copy}` stages a restore as a job while the host keeps serving, and its result says to restart QMX to finish it (Appendix E); `POST /api/backups/restore/cancel` removes a staged restore; `GET /api/backups` shows a staged restore and the folders set aside by earlier restores with their sizes; the drill runs once a month under the `Backups` service, its result goes into the doctor row, and a failed drill opens an incident; and the first host start after a finished restore rebuilds memory once on its own thread and logs it. Edge cases it must survive. A stage while a round runs answers 409 naming the round's job, and a round while a stage runs waits for the next sweep. A second stage answers 409. The host keeps answering while it stages. Cancel with nothing staged answers 404 with its line. The drill checks room first and is skipped with a line when short. The memory rebuild uses the built-in FTS index when Hindsight is off, and a rebuild that fails leaves recall as it is with a doctor line. A restore log line already followed by a `reindexed` line starts nothing. The routes are POST and GET only, because the REST app's CORS allows GET, POST and PUT (`QX/server.py:475`).

**Depends on.** B2 (`BK/restore.py`) and B3 (`HO/backups.py`, `HO/host.py`). It shares no file with B4.

**Files.**

- [ ] Edit `HO/backups.py`. `POST /api/backups/restore` (202 with a `restore` job), `POST /api/backups/restore/cancel`, the staged restore and the set-aside folders in `view()`, and the monthly drill in the sweep with its doctor row and incident.
- [ ] Edit `HO/host.py`. After `compose_memory` (near line 758), when `BK/restore` reports a finished restore not yet reindexed, run `memory.rebuild("all")` on its own thread and log `reindexed`.
- [ ] Add `QA/qmx-host/tests/test_backups_restore.py` and `QA/qmx-host/tests/test_restore_reindex.py`.

**Build.**

- [ ] Reproduce first. A test posts a restore to the host and gets 404 on the parent.
- [ ] Add the restore and cancel routes, then the drill, then the memory rebuild, each with its test.
- [ ] Prove the one fact. Recall after a restore finds what the copy held. A test saves a memory row, copies the folder, forgets the row, restores the copy, starts the memory engine as the host does, and asserts `recall` returns the row once the rebuild ends. B4's finish at start lands in the same wave, so this PR's tests call `BK/restore.finish` themselves.

**You see.**

- [ ] A head host answers `POST /api/backups/restore` with 202 and a job that ends `finished` with the line "Restart QMX to finish the restore", and after `finish` and a new start, recall finds a row only the copy held.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The restore route stages and answers with a job; a second stage, a stage during a round and a cancel with nothing staged each answer with their line; cancel removes the staging; the view shows the staged restore and the set-aside folders; the drill runs once a month by the injected clock, writes its result, and opens an incident on failure; the memory rebuild runs once after a finished restore and not again. Run the host and home suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The host and home suites at parent and head. Save `b5-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host on a filled folder stages a restore of its target's copy while `/api/health` is polled. Save `b5-stage.log`. Pass when the job ends `finished` with the restart line and every health call answers in under 1 s; the parent answers 404.
- [ ] Lane 3. Lane 2's host stopped, `BK/restore.finish` run, the host started, then a recall for a row only the copy held. Save `b5-recall.log`. Pass when recall returns the row and the log holds a `reindexed` line.
- [ ] Lane 4. A stage, then cancel. Save `b5-cancel.log`. Pass when the staging folder is gone and `data/` hashes as before.
- [ ] Lane 5. A second stage while one waits. Save `b5-twice.log`. Pass when it answers 409 naming the first.
- [ ] Lane 6. A stage while a round runs. Save `b5-during-round.log`. Pass when it answers 409 naming the round's job.
- [ ] Lane 7. The clock patched to a month after the last drill. Save `b5-drill.log`. Pass when the doctor row carries the drill's result and `cache/restore-drill/` is gone.
- [ ] Lane 8. The drill on a target with one pooled file truncated. Save `b5-drill-failed.log`. Pass when an incident names the file.
- [ ] Lane 9. `GET /api/backups` after two finished restores. Save `b5-view.log`. Pass when it lists both set-aside folders with their sizes.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, then remove the throwaway folders and list processes. Save `b5-processes.log`. Pass when every exit code is 0 and nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. `/api/health`'s median milliseconds during lane 2's staging and with nothing running, and seconds for the memory rebuild of 1,000 rows on the FTS index.
- [ ] Probe. Fifty health calls during staging and fifty after, three times; the rebuild three times on fresh copies.
- [ ] Baseline. Record the idle health median first. The parent has no staging and no rebuild after a restore.
- [ ] Rule. Health during staging is within 50 ms of idle, or the PR fails. The rebuild of 1,000 rows is under 30 s, an absolute budget.

**Review gate.** None. B5 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Joined onto B4 by a merge commit (the two share no file).

## Send copies off-site through rclone (B6)

Design 62 C2's off-site row and D2 (each off-site backup target names a place). Rulings 136, 140 and 144. Today the only rclone use is a mini app's volume, sent with `rclone sync` or `copy --checksum` and never with rclone's own output in an answer, because that output can hold credentials (`AP/backup.py:41-61`). Done when a target of kind `rclone` (`remote`, `path`, optional `config`) holds the same layout as a folder target under `<remote>:<path>/<home_id>/`, through an `RcloneRepository` in `BK/rclone.py`. A copy is sent by one `rclone copy --files-from` from a tree of hard links in `cache/backup-send/` (a file copy where the drive refuses links), its `manifest.jsonl` uploaded last; thinning is `rclone purge` of each dropped copy and a `rclone delete --files-from` of the pool files no kept manifest names; a restore and the drill fetch the pool files they need with `rclone copy --files-from` into the staging folder; and `BK/plan.py` parses the kind and `repository_of` and `source_of` build it, so the host and the card need no change. Edge cases it must survive. rclone missing from `PATH` is one line saying to install it. A remote rclone cannot reach, or refuses, is one line naming the remote, never rclone's own text. Nothing is ever deleted outside `<path>/<home_id>/`, and `rclone sync` is never run. An upload killed mid way leaves a copy with no manifest, which listing ignores and the next round removes. The fork guard holds as on a folder target. `config`, when set, is passed as `--config`, and with none rclone reads only `RCLONE_CONFIG` or its own default; QMX never stores a remote's secret. Room is not checked, because the provider's own limit is the only limit (ruling 106), and a failed upload is its line. `cache/backup-send/` is emptied after each send. A remote name is checked against `^:?[A-Za-z0-9_-]+$`, so the on-the-fly `:local` backend serves the lanes.

**Depends on.** B1 and B2 (`BK/plan.py`, `BK/repository.py`, `BK/restore.py`).

**Files.**

- [ ] Create `BK/rclone.py` with `RcloneRepository`, one `run(args)` that maps every failure to a plain line and records each command's arguments (which hold no secret) in the round's log line, and the link tree.
- [ ] Edit `BK/plan.py` (the `rclone` kind and its checks, and its case in `repository_of` and `source_of`).
- [ ] Add `QA/qmx-home/tests/test_backup_rclone.py`, which skips by name when `rclone` is not on `PATH`.

**Build.**

- [ ] Reproduce first. A test parses a `kind = "rclone"` target and is refused on the parent.
- [ ] Add the repository's reads, then the send, then thinning and the sweep, then the fetch for restore.
- [ ] Prove the one fact. A copy counts only once its manifest is up. A test kills the send after the pool files and before the manifest, and asserts `copies` does not list it and the next round removes it.

**You see.**

- [ ] With `RCLONE_CONFIG` on an empty file, a round to the target `{kind = "rclone", remote = ":local", path = "<lane folder>/remote"}` writes `<lane folder>/remote/<home_id>/snapshots/<stamp>/manifest.jsonl`, and a restore from it matches every hash.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The kind parses and a bad remote is refused; a round sends pool files then the manifest; an unchanged round sends nothing; thinning purges dropped copies and sweeps unnamed pool files only; a killed send is not listed and is removed; rclone missing and a failing remote each give one line with no rclone text; the fork guard refuses; a restore and the drill fetch only the files they need. Run the home suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The home and host suites at parent and head. Save `b6-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A round of B1's lane 2 folder to a `:local` rclone target in the lane folder. Save `b6-send.log`. Pass when the remote holds the manifest and every pooled file with its sha256.
- [ ] Lane 3. A restore from that target into a fresh folder. Save `b6-restore.log`. Pass when every hash and row count matches the manifest.
- [ ] Lane 4. The send killed after the pool upload, then a round. Save `b6-killed.log`. Pass when the first copy is not listed and the second round removes it and sends a whole copy.
- [ ] Lane 5. `rclone` taken off `PATH`. Save `b6-missing.log`. Pass when the round says to install rclone and the quick undo still gets its copy.
- [ ] Lane 6. A target naming `:sftp` at `127.0.0.1` port 1. Save `b6-unreachable.log`. Pass when the line names the remote and holds none of rclone's own output.
- [ ] Lane 7. Sixty days of fake copies on the remote, then a round. Save `b6-keep.log`. Pass when the kept set matches B1's rule and the remote pool holds only named files.
- [ ] Lane 8. Every rclone command the lanes ran, read from the round log. Save `b6-config.log`. Pass when each carries `--config` with the lane's empty file and none names `D:/Tools/rclone/rclone-qmx.conf`.
- [ ] Lane 9. Two folders with one `home_id` on one remote in turn. Save `b6-fork.log`. Pass when the second is refused by name until carry-on.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, then remove the throwaway folders and list processes. Save `b6-processes.log`. Pass when every exit code is 0 and no `rclone` process from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for lane 2's first round and for an unchanged round to the `:local` rclone target, against the same rounds to a folder target.
- [ ] Probe. Each three times, interleaved, on fresh targets.
- [ ] Baseline. Record the folder target's medians first. The parent has no off-site copy.
- [ ] Rule. The rclone first round is within 3 times the folder target's median, or the PR fails. The unchanged rclone round is under 5 s, an absolute budget.

**Review gate.** None. B6 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the wave 3 tip; B7 joins it by a merge commit.

## Seal his keys into the copies with his passphrase (B7)

Design 62 C4, C3 (restore on a new PC) and F step 6. Rulings 116 and 135. Today `R/vault.py` seals static keys per machine with X25519, HKDF-SHA256 and AES-256-GCM, the name as associated data (`VaultKey.seal` and `open`, `R/vault.py:154-185`), allows only model-provider rows, `qmx/read/*` and `qmx/data/*` and never a token name (`is_replicable`, `R/vault.py:89-104`), and reads Credential Manager by name without ever writing it (`KeyringSource`, `R/vault.py:494-513`). This PC's key store writes through `CredentialManager.replace`, which also removes keyring's stale companion entry (`BR/credentials.py:47-75`). Nothing seals keys for a backup. Done when `PUT /api/backups/passphrase {passphrase}` derives a key pair from his passphrase with Argon2id (cryptography 50.0.1, Appendix A) and keeps only the public half, the salt and the costs in `[backup.keys]`; each round seals, to that public half, the values `is_replicable` allows (the names of `PROVIDERS`, his `[providers]` rows, `qmx/read/ctrader-app` and the `credential_ref` of his `[connections]` rows, the names `pc_vault_document`'s caller seals today, `QX/node.py:1100-1104`) and the files in `keys/` except `tokens.json` and `control-token`, as `keys.sealed.json` beside every target copy's manifest through B1's `sealed_keys`; `POST /api/first-start/keys {source, copy, folder, passphrase}` opens it after a restore on a new PC and writes each missing entry through `CredentialManager.replace` and each missing `keys/` file with the modes `write_machine_key` uses (`R/vault.py:199`); `POST /api/backups/passphrase/off` removes `[backup.keys]`; and while it is off the doctor row says his keys are not in the backup. Edge cases it must survive. A wrong passphrase is refused by name and nothing is written. The passphrase is never logged, stored, put in a job line or in a file; lane 5 greps for it. No key value is in clear in any file under a target; lane 2 greps for each fake value. A token, an OAuth pair and a live-trading key are never sealed, because none is on `is_replicable`'s list. A changed passphrase seals new copies to the new key, and an older copy still opens with the passphrase it was sealed under, because its file carries its own salt and costs. An entry or a `keys/` file this PC already holds is kept, never overwritten, and the answer names it. A name Credential Manager cannot read is left out of the copy with a line. A copy with no key copy makes the card say his keys were not in that copy. The quick undo never holds a key copy.

**Depends on.** B4 (`HO/first_start.py`) and B5 (`HO/backups.py`). It shares no file with B6.

**Files.**

- [ ] Create `R/key_copy.py` with `derive(passphrase, salt, costs) -> VaultKey`, `seal_copy(public, salt, costs, values, files) -> bytes` and `open_copy(sealed, passphrase) -> Opened`, each value sealed with `VaultKey.seal` under its own name and each file under `file:keys/<name>`.
- [ ] Edit `HO/backups.py` (`PUT /api/backups/passphrase` and `POST /api/backups/passphrase/off`, the names gathered from settings, and the `sealed_keys` callable passed to every round, reading through `KeyringSource`).
- [ ] Edit `HO/first_start.py` (`POST /api/first-start/keys`, writing through `CredentialManager`).
- [ ] Add `QA/qmx-router/tests/test_key_copy.py` and `QA/qmx-host/tests/test_key_copy_routes.py`, both with a `MemorySource` and a fake `SecretStore`.

**Build.**

- [ ] Reproduce first. A test runs a round with a passphrase set and finds no `keys.sealed.json` on the parent.
- [ ] Add `derive`, `seal_copy` and `open_copy`, then the passphrase routes, then the round's sealer, then the card's route.
- [ ] Prove the one fact. Only the passphrase opens the copy. A test seals with the public half alone, then asserts `open_copy` with the passphrase returns every value, a wrong passphrase raises by name, and no byte string of any value appears in the sealed file.

**You see.**

- [ ] On a second scratch profile with a fake key store, after the card restores a copy, `POST /api/first-start/keys` with the passphrase answers the names it wrote, and the fake store holds each provider key the first profile held.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Derive and open round-trip; a wrong passphrase is refused; a token name and a live-trading name are never sealed; files in `keys/` but `tokens.json` and `control-token` are sealed; a changed passphrase leaves older copies opening with the older one; existing entries and files are kept and named; an unreadable name is left out with a line; the quick undo holds no key copy; off removes the table and the doctor row says so. Run the router and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The router and host suites at parent and head. Save `b7-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host with a fake key store holding three provider keys, one `qmx/read/*` key and one `qmx/token/*` pair, a passphrase set, then a round. Save `b7-seal.log`. Pass when the target copy holds `keys.sealed.json` with the four static names and the `keys/` files, no token name, and a grep of every file under the target finds none of the fake values.
- [ ] Lane 3. A second scratch profile with an empty fake key store restores that copy through the card, then posts the passphrase. Save `b7-open.log`. Pass when the fake store holds the four values and the new folder's `keys/` holds the sealed files.
- [ ] Lane 4. The same with a wrong passphrase. Save `b7-wrong.log`. Pass when it is refused by name and the fake store and `keys/` are unchanged.
- [ ] Lane 5. A grep of the host log, captured stderr, every job view and every file in the folder and the target for the passphrase. Save `b7-leak.log`. Pass when it appears nowhere.
- [ ] Lane 6. The passphrase changed, then a round; then both copies opened. Save `b7-change.log`. Pass when the older copy opens only with the older passphrase and the newer only with the newer.
- [ ] Lane 7. `POST /api/backups/passphrase/off`, then a round. Save `b7-off.log`. Pass when the new copy holds no key copy and the doctor row says the keys are not in the backup.
- [ ] Lane 8. The card's keys route on a profile whose fake store already holds one of the names with another value. Save `b7-kept.log`. Pass when that value is kept and the answer names it.
- [ ] Lane 9. The quick undo's newest copy after lane 2's round. Save `b7-quick.log`. Pass when it holds no `keys.sealed.json`.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, then remove the throwaway folders and list processes. Save `b7-processes.log`. Pass when every exit code is 0 and nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for a round with a passphrase set and without one, at head, on lane 2's folder, and seconds for the passphrase route and for opening a copy.
- [ ] Probe. Each three times, interleaved.
- [ ] Baseline. Record the round without a passphrase first. The parent has no key copy.
- [ ] Rule. A round with the key copy is within 1 s of one without, or the PR fails. Setting the passphrase and opening a copy each take under 2 s, an absolute budget (Argon2id measured 0.3 s, Appendix A).

**Review gate.** None. B7 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Joined onto B6 by a merge commit (the two share no file).

## Close the program

- [ ] Every PR is stacked with a CLEAN verdict, or skipped with its reason in `RESUME.md`.
- [ ] Closing lanes, run by the coordinator at the stack tip on fresh throwaway folders and scratch profiles, with no PR.
  - [ ] One pass of each journey, in order, by the routes and commands of Appendix E. A host makes its quick copy and a folder target copy; a restore staged from Settings is finished by `serve` and recall finds a row only the copy held; a second scratch profile's card restores the target's copy into a new folder, opens the key copy with the passphrase, hands over, and the host starts; an rclone `:local` target gets a copy and a fresh folder is restored from it with `python -m qmx_host restore`. Save `evidence/br-v/journeys.log`. Pass when each ends in its expected state with no traceback in any log and `C:/QMX-backup` is as it was.
- [ ] Design 62 A3's tree, on `plan/agent-system`, gains the rows this program adds (`backups/quick/`, `backups/backups.lock`, `backups/restoring-<stamp>/`, `backups/before-restore-<stamp>/`, `cache/backup-send/`, `cache/restore-drill/`), so every file has its documented home (ruling 143).
- [ ] `RESUME.md` names the restart contract of B5 and the default second drive his PC gets (none until he names one, Appendix D).
- [ ] `just ci` at the stack tip exits 0, or every failure is a named environmental gap.
- [ ] `QUEUE.md` moves on to its next item.

## Appendix A. Prototype evidence

- Probes run on 2026-10-27 from `D:/Temp/g1-probe` with the `bld-ls4` venv's Python (`-I -B`). Nothing of QMX was started; no host, pg0, Hindsight, browser or Credential Manager was touched, and the folder was removed afterwards.
  - Argon2id from `cryptography` 50.0.1 (the locked version, `uv.lock`) derives 32 bytes at 256 MiB, 3 passes and 4 lanes in 0.3 s, and `X25519PrivateKey.from_private_bytes` takes them. B7's costs and budget rest on this.
  - SQLite 3.50.4. `VACUUM INTO` from a second connection while a first holds `BEGIN IMMEDIATE` with an uncommitted insert succeeds in 0.03 s and copies the committed rows only; the copy's journal mode is `delete`, which the store's opener sets back to WAL. B1's copy of a live store rests on this.
  - `os.link` on drive D (NTFS) works, and removing one name keeps the other. B2's links from the folder's own files rest on this.
  - rclone 1.75.2 at `D:/Tools/rclone`, run with `--config` on an empty file and the on-the-fly `:local:` backend, did `copy`, `copy --checksum`, `copy --ignore-existing`, `lsf -R`, `cat`, `copy --files-from` and `purge` with no config and no network. B6's lanes rest on this.
- Facts read in the code at `6260fe1d` in the read-only checkout `D:/Temp/g1-plan`, each with its line in the PR that uses it. The pre-change copy and the backup log (`HM/versions.py`). The resolver, the label and the drive list (`HM/__init__.py`). The store table and plain-file stores' versions in the label (`HM/stores.py`). The bring-in's helpers and lock (`HO/bring_in.py`). The card, its jobs and its CORS (`HO/first_start.py`, `HO/jobs.py`). The command's exit codes (`HO/__main__.py`). The host's start order, routers, tasks and doctor rows (`HO/host.py`). The `[backup]` section's strict app model (`QX/service.py`, `AP/manifest.py`). The REST app's CORS and the bearer on extra routers (`QX/server.py`). The volume backup's rclone use (`AP/backup.py`). The vault's seal and allow-list (`R/vault.py`). The key store's replace (`BR/credentials.py`). The Library's layout, purge and catalogue rebuild (`LB/store.py`). Frozen price partitions named by fingerprint and the open month at `open.parquet` (`packages/qmf-data/src/qmf/data/series.py:95`, `HO/market_data.py:504-506`). Memory's FTS file and rebuild (`MM/engine.py`). The relayed projects junction (`qma/harness/home.py`). The inbox incident (`E/ledger/inbox_table.py`).
- Facts the builders prove by running code (each PR's Build block). The copy order leaves no copied ref without its object (B1). `finish` resumes from every kill point (B2). A round never holds a request (B3). `serve` finishes a staged restore before any store opens (B4). Recall finds the copy's rows after a restore (B5). A copy without its manifest is never listed (B6). Only the passphrase opens the key copy (B7).
- Unproven until lanes run. That a mini app's `road/` copied by B1's order rule restores consistently without the lease the volume backup takes (`AP/backup.py:135-142`); B1 lane 2's folder holds one mini app, and a failure there sends `apps/<id>/road/` to a lease-held copy. That rclone behaves against a real bucket or a server over SFTP as it does with `:local:`. That Windows refuses to rename `data/` while another process holds a file in it, which B4 relies on to refuse a restore under a running host with a line rather than a half swap.

## Appendix B. Not in this program

- **Design 62 C5, the GitHub snapshot reshaped to settings and definitions only.** The weekly template (`E/templates/backup-weekly/`, `QX/backup.py`) stays as built. Its reshape needs a Library-level meaning of "his published definitions" that is not built, and nothing in this program's journeys needs it. Logged to `BACKLOG.md`, with its two files inside `data/` (`weekly-backup.json`, `weekly-backup.lock`) that ruling 143 wants moved.
- Logged to `BACKLOG.md` at program start. Undoing a restore from `backups/before-restore-<stamp>/`, and removing such a folder on his click in Settings. A purge reaching the copies already in a pool. The agent guard protecting target folders outside the QMX folder (`guard_rules`, `QA/qma-harness/src/qma/harness/tools.py:930-975`, covers the QMX folder only). A dump of Hindsight's database (`pg_dump`, probe P-PGDUMP), instead of the rebuild B5 runs. A mini app's `road/` copied under its lease, if B1's lane fails. A copy when QMX closes and a second-drive copy before every migration (only the quick copy before an upgrade is built). A copy before a folder move (no folder move exists yet). Copying an append-only log by its new tail only, instead of whole when it grew.
- LF12, targets named from the place list and shown on the place screens (design 62 D4). Server homes and `qmx-recover`. The UI rows (UI session).

## Appendix C. Files two PRs share

| Pair | Shared file | Order |
|---|---|---|
| B1, B2 | `BK/repository.py`, `BK/snapshot.py` (B2 adds reads only) | B1 first |
| B2, B3 | none (B2 is `BK/` only; B3 is `HO/backups.py`, `HO/host.py`, `HO/__main__.py`, `QX/service.py`) | wave 2, side by side |
| B1, B4 | `HO/first_start.py` (B1 changes two imports), `HM/versions.py` (B1 the log helpers, B4 the lines) | B1 first |
| B3, B4 | `HO/__main__.py` (B3 `backup`, B4 `restore` and the finish at start) | B3 first |
| B3, B5 | `HO/backups.py`, `HO/host.py` | B3 first |
| B4, B5 | none (B4 is `HO/first_start.py`, `HO/__main__.py`, `HM/versions.py`, `HM/__init__.py`; B5 is `HO/backups.py`, `HO/host.py`) | wave 3, side by side |
| B1, B6 | `BK/plan.py` (B6 adds the kind) | B1 first |
| B5, B7 | `HO/backups.py` | B5 first |
| B4, B7 | `HO/first_start.py` | B4 first |
| B6, B7 | none (B6 is `BK/rclone.py`, `BK/plan.py`; B7 is `R/key_copy.py`, `HO/backups.py`, `HO/first_start.py`) | wave 4, side by side |

## Appendix D. Defaults

Each is Claude's default, with the reason. He can overrule any of them, and each lives in `[backup]` where Settings edits it.

- The settings shape. The volume keys and `repository` stay where they are.

```toml
[backup.quick_undo]           # in <QMX>/backups/quick on the folder's own drive
hours = 48                    # every hourly copy for 48 hours
days = 7                      # then the newest of each day for 7 days

[[backup.targets]]            # left out: the default second drive; targets = [] means none
id = "usb"
kind = "folder"               # folder (B1) or rclone (B6)
path = 'E:\QMX-backup'        # rclone instead: remote = "b2", path = "bucket/qmx", config = optional
every = "day"                 # hour, day or week
at = "03:00"                  # local time; a PC that was off copies at its next start
keep = { daily = 14, weekly = 8, monthly = 12 }
on = true

[backup.drill]
every = "month"
sample = 200                  # pooled files checked besides every mutable file

[backup.keys]                 # written only by the passphrase route (B7); public half, never a secret
```

- The default second drive. The largest fixed drive that is not the folder's own, as `<drive>:\QMX-backup`, and never one the first copy would leave below the larger of 1 GiB and 10 % free (L1). On his PC that gives none today, so the card and the doctor row say his work has no copy on another drive until he names one. Plugging in a USB disk and naming it is his step, not a decision.
- One snapshot per round, sent to every due place. The quick undo is the round's own staging. Its files written once stay in `data/` and are named in place, and its other files sit in `backups/quick/pool/`. A target pools every file. A store unchanged since the last copy is not copied again (L6). This differs from design 62 C2's layout only in that mutable files are pooled by hash too, so an unchanged store is never copied twice to a target.
- `LEFT_OUT`, paths in `data/`, never in a copy. `library/catalog.db` and `memory/fts.db` (indexes, rebuilt); `memory/hindsight/pg/` (Hindsight's database, rebuilt from Library rows by B5); `library/uploads/*.part`, `market/.staging/`, `market/**/.incoming.parquet` and `market/**/.verify-*` (work in progress); the folders under `chats/` (launch files, rebuilt per launch); `*.lock`, `control-process.json`, `router.port`, `node.port` and SQLite's `-wal`, `-shm` and `-journal` (a running process's state); `claude/.credentials.json` and `claude-relayed/.credentials.json` (the plan login); names ending `.qmx-copying`; every link and junction; and the `leave_out` globs he sets.
- `WRITE_ONCE`, paths in `data/` that are never rewritten in place. `library/objects/**` and `library/blobs/**` (written once, `LB/store.py:2-14`), `market/**/*.parquet` but `open.parquet` and names starting with a dot (frozen partitions are named by fingerprint), `migration/pre/**` and `migration/retired/**`.
- The order, so a copy is never mixed. First every SQLite store (the engine's ledger and inbox, then control, runs, apps, portfolio, then any other SQLite file), then the Library's `refs/`, `edges/` and `annotations/` files, then every other mutable file, and last the listing of the files written once. Each step copies a moment no earlier than the step before, so the ledger never names a Library object the copy lacks, and no copied ref names an object the copy lacks.
- The fork guard. A round to a target first reads the target's newest copy. When the target holds copies and its newest is not the one this folder last sent there, restored from there, or carried on from, the round refuses by name. Carry-on is his click (`POST /api/backups/targets/{id}/carry-on`). The log in `backups/backups.jsonl` is the record, keyed by the place's path, or its remote and path, and the `home_id`, so a restore on a new PC from a USB disk lets that disk carry on with no click. No new state file is added.
- Keep rules. The quick undo keeps every copy for 48 hours, then the newest of each day for 7 days; a `before-upgrade` copy, and each of LF3's `pre-*` copies, is kept until 30 days after the first target copy made after it (design 62 B3). A target keeps the newest of each day for 14 days, of each week for 8 weeks and of each month for 12 months. A sweep after thinning removes only pool files no kept manifest names.
- A restore sets the folder's `data/` aside whole in `backups/before-restore-<stamp>/`, never deleted by QMX, so nothing a restore replaces is lost. It carries over This PC's plan login. It never brings back a purged blob. It restores whole copies only; LF3's store-level pre-change copies stay the opener's own safety net and are never offered alone, because putting one store back would leave the others at a later moment.
- Before an upgrade, `serve` takes one quick copy of the whole folder tagged `before-upgrade`, and B4's card offers it when a store later refuses (design 62 B4). The second drive gets its normal daily copy, so a start is never held by a slow USB disk.
- Copies run inside the host on their own thread, not as a workflow (Appendix G). A round he must act on opens an inbox incident; an unplugged disk is only a doctor row.
- A restore from Settings stages while QMX runs and finishes at the next start, so no store is ever replaced under an open connection.
- The sealed key copy holds what a new PC needs to be a restore, not a re-entry (design 62 C4). Static keys `is_replicable` allows and `keys/` files but `tokens.json` and `control-token`, which the host makes again (`local_token(create=True)`). OAuth tokens and live-trading keys are never in it (ruling 135); those connections are signed into again on their home. Off until he sets a passphrase.

## Appendix E. The backup and restore contract (reference)

The UI agent and the desktop app (`qmx-desktop`, engine AD-48) follow this contract.

| Step | The desktop app runs | It reads | Then |
|---|---|---|---|
| 1 | `python -m qmx_host serve --port <p> --ui-origin <origin>` | a staged restore is finished first, then the start goes on as in the loose-strings contract | as there |
| 1 | the same | exit 2 with one line, a refused folder or a refused store | show the line, and offer the card, which offers restore |
| 2 | `python -m qmx_host first-start --serve --port <p> --ui-origin <origin>` | `GET /api/first-start` with `restore` in `choices` and `second_drive` | the UI shows the card |
| 2 | the same | a finished restore job, then `POST /api/first-start/handover` | step 3 of the loose-strings contract |
| 4 | the UI's restore in Settings | the restore job ends `finished` with `restart` true | stop the host, then step 1 |

- The host's routes, all behind the bearer. `GET /api/backups` (the plan, each place's last copy and line, a staged restore, the folders set aside). `GET /api/backups/targets/{target_id}/copies` (each copy by date). `POST /api/backups/run` (202 with a `backup` job; body `{target}` optional). `GET /api/backups/jobs/{job_id}`. `POST /api/backups/targets/{target_id}/carry-on`. `POST /api/backups/restore` (202 with a `restore` job; body `{target, copy}`). `POST /api/backups/restore/cancel`. `PUT /api/backups/passphrase` (body `{passphrase}`). `POST /api/backups/passphrase/off`. The plan itself is edited with `PUT /api/settings/backup`.
- The card's routes, on the loopback with no bearer. `POST /api/first-start/copies` (body `{source}`, the copies by date). `POST /api/first-start/restore` (202 with a `restore` job; body `{folder, source, copy}`). `POST /api/first-start/keys` (body `{source, copy, folder, passphrase}`). A `source` is `{kind: "folder", path}` or `{kind: "rclone", remote, path, config}`.
- The commands. `python -m qmx_host backup --home <folder> [--target <id>]` exits 0 when it copied or had nothing to copy and 1 when refused. `python -m qmx_host restore --home <folder> --from <path> [--copy <stamp>] [--create]` lists with no `--copy`, and exits 0 restored, 1 when a host serves the folder, 2 when refused.
- A refusal answers 409 with `detail`, its one line; a bad body answers 400.

## Appendix F. Words

- **Backup.** Keeping copies of his QMX folder's data so he can go back to one.
- **Copy.** One dated moment of his data in one backup place, picked by date. Code and disk call it a snapshot (`snapshots/<stamp>/`).
- **Quick undo.** The copies in `backups/quick/` on the folder's own drive, every hour. They undo a bad edit or a bad upgrade and do not survive a dead disk.
- **Target.** A backup place outside the folder that holds copies, a folder on another drive (the second drive) or an rclone remote (off-site).
- **Round.** One pass that makes a copy and sends it to every place that is due.
- **Pool.** The files a place holds once each, by sha256, which every copy's manifest names.
- **Restore.** Rebuilding `data/` from one copy, with the folder's earlier data set aside whole.
- **Set aside.** Moved, never deleted, into `backups/before-restore-<stamp>/`.
- **Drill.** QMX restoring a sample of one copy into `cache/restore-drill/` once a month to prove it can.
- **Passphrase.** His words that open the sealed key copy. QMX keeps only the public half derived from it.
- **Sealed key copy.** His static keys and key files sealed to that public half, beside each target copy.
- **Pre-change copy.** LF3's copy of the one store an upgrade changes, kept in `backups/pre-*`. QMX's own safety net, not a copy he restores.
- **Carry on.** His click that lets this folder keep sending to a target another folder wrote to.

## Appendix G. Alternatives weighed

- The round as the `backup` script workflow that replaces `backup-weekly` (design 62 G's LF8 row). Rejected. A template's triggers install disabled (`add_disabled_trigger`, `E/templates/install.py:92`), so copies would not be on by default; a script run needs a work zone and an environment; and the host already runs its own timed work beside the engine (`Replicator.run`, `HO/host.py:804`).
- A new `qmx-backup` workspace package. Rejected. `qmx_home` already owns `backups/` and its log, the module needs only the standard library, and a new package adds workspace members, sources, test ignores and CI rows for no reader.
- Hashing every file every round. Rejected. A file whose size and `mtime_ns` match the last manifest keeps its hash, as rsync does; a restore and the drill hash every file they place.
- A separate hash cache file. Rejected. The newest manifest is the cache, so no file is added (ruling 143).
- Restoring in place by moving only the files that differ. Rejected. It leaves no whole earlier state to go back to; setting `data/` aside whole is one rename on the same drive and loses nothing.
- Restoring a single store from LF3's pre-change copy. Rejected. The other stores would stay at a later moment, which mixes the folder.
- `rclone sync` to a remote. Rejected. Run from a new or empty pool it would delete the remote's copies; `copy`, `purge` and `delete --files-from` delete only what a keep rule names.
- Storing the passphrase or its private half. Rejected. A daily copy needs only the public half to seal, so nothing that opens the keys sits on the PC (design 62 C4).

## Appendix H. Gates and calls

- G-LAND. He lands the stack himself.
- No call needs him. No PR touches money, his vocabulary or irreversible scope. The words are design 62 H's, which he read; deleting a set-aside folder stays his click and is not built here; setting a passphrase is his choice whenever he wants his keys in the backup. Naming a USB disk as his second drive is a step only he can do, and the doctor row asks for it in plain words.
