# QMX local backup and restore, build program

This program gives his QMX folder copies on This PC, on a second drive he picks and at an off-site place he names, and a restore from any of them, so the first start's "Restore from a backup" works. It is design 62 phase 2 (LF8 and LF9), sections B4, C, F and L, the program `LOOSE-STRINGS-PLAN.md` Appendix B calls G1.
The rules it enforces. The quick undo on This PC is on by default and never pushes his drive below the host's floor; nothing is written outside the QMX folder except to a place he named. A restore shows what it replaces before he confirms it, never loses or mixes data, sets the folder's earlier data aside whole, and pauses server sync and fires until he carries on. A key, token or credential file is never in a copy in clear.
There are 7 PRs. B1 makes copies on This PC and on a second drive. B2 restores a copy and runs the drill. B3 runs the copies on their own inside the host. B4 restores from the first-start card and the command line. B5 restores from Settings and makes the first start after a restore safe. B6 sends copies off-site through rclone. B7 adds the sealed key copy.
The stack roots on `build/ls4` at `6260fe1d`. The review `D:/QMX-worktrees/qma-ship/wrapup/review/plan-backup-restore-edge-cases.md` is folded in (F1 to F15, E-M1 to E-M9, E-S1 to E-S19). UI code, the GitHub snapshot's reshape, server homes and the real server are out of scope (Appendix B).

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a test run, or a SHA. The body is a how-to. The appendices explain and record.

Each PR section opens with a preamble naming the design 62 sections, rulings and review findings it serves, what the code does today, and its done line with the edge cases it must survive. Then come the nine blocks `check-plan.mjs` requires.

Path shorthands. `QA/` is `qmx-agents/packages/`. `HO/` is `QA/qmx-host/src/qmx_host/`, `HM/` is `QA/qmx-home/src/qmx_home/`, `BK/` is `HM/backup/` (new in B1), `QX/` is `QA/qmx-control/src/qmx_control/`, `R/` is `QA/qmx-router/src/qmx_router/`, `BR/` is `QA/qmx-broker/src/qmx_broker/`, `E/` is `QA/qmx-engine/src/qmx_engine/`, `LB/` is `QA/qmx-library/src/qmx_library/`, `MM/` is `QA/qmx-memory/src/qmx_memory/` and `AP/` is `QA/qmx-apps/src/qmx_apps/`. Line numbers are at `6260fe1d`.

The store is `D:/QMX-worktrees/qma-ship/wrapup/`, whose `QUEUE.md` names this program as its next item, with `BRIEF-BUILDER.md`, `REVIEWER-BRIEF.md`, `RESUME.md`, `BACKLOG.md`, `lows.md`, `ledger.tsv`, `dispatch/`, `review/` and `evidence/`.

The program follows `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md` with the overrides of `LOCAL-FIRST-PLAN.md`, as `LOOSE-STRINGS-PLAN.md` did. Builders are Claude Opus 5.5 (`poteto-agent`, `model: opus`), at most two at once, never two on one file. A fresh Opus reviewer agent reviews every diff and runs the edge-case lens of `bmad-review` on every PR, because each one reads or writes his data. The coordinator runs the suites, `just ci` and the lanes in the background and allows one fix round. Low findings go to `lows.md`; anything new goes to `BACKLOG.md`. He lands the stack himself.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] Confirm the shell (Windows 11, PowerShell 7.6 and Git Bash; in PowerShell `$H` and `$h` are one variable) and the root (`git rev-parse origin/build/ls4` is `6260fe1d`). Logged in `RESUME.md`.
- [ ] Read the trunk rules with `git show origin/main:CLAUDE.md`, then the rulings file `research/methodology/26-operator-rulings-and-alignment.md` (rulings 106, 116, 135 and 136 to 145), then design 62 sections B3, B4, C, F and L, then the review file above, then Appendices D to F of this plan.
- [ ] No hourly `/loop 1h` tick, because builder and background-job notifications wake the coordinator. Post a short status message to the operator only when a PR opens, a verdict lands or a blocker appears.
- [ ] Never stop to ask him during the build. Stop only for a credential, a real ambiguity in this plan, or a step only he can do (`QUEUE.md`).
- [ ] Before dispatch, add to `BACKLOG.md` the items this plan leaves out (Appendix B lists them).

### Spawn owners

| # | Id | PR | Wave | Branches from | Runs beside | Proving check |
|---|---|---|---|---|---|---|
| 1 | B1 | Copies on This PC and on a second drive | 1 | `6260fe1d` | none | a second round of an unchanged 2,000-file folder copies no file, the target holds every file's hash, and no secret file is in either place |
| 2 | B2 | Restore a copy, and the drill | 2 | the stack tip after wave 1 | B3 | a folder restored from its second-drive copy matches every hash and row count, its earlier data is set aside whole, and the counts it replaces were shown first |
| 3 | B3 | The host makes copies on its own | 2 | the stack tip after wave 1 | B2 | a host started on a throwaway folder makes its first quick copy within two minutes and answers `/api/health` in under 1 s throughout |
| 4 | B4 | Restore from the first-start card and the command line | 3 | the stack tip after wave 2 | B5 | the card restores a confirmed copy into a new folder on a scratch profile, hands it over, and the host starts on it |
| 5 | B5 | Restore from Settings, and the first start after a restore | 3 | the stack tip after wave 2 | B4 | after a restore the host starts with server sync and fires paused, recall finds a row only the copy held, and carry-on resumes both |
| 6 | B6 | Copies off-site through rclone | 4 | the stack tip after wave 3 | B7 | a round to a `:local:` rclone remote and a restore from it match every hash |
| 7 | B7 | The sealed key copy | 4 | the stack tip after wave 3 | B6 | a key copy sealed in a round opens with the passphrase on a second scratch profile and fills its fake key store and `data/vault/` |

- [ ] Spawn one fresh Opus builder per PR in the background with `subagent_type: poteto-agent` and `model: opus`, from a dispatch file saved in `dispatch/`. Its first words are exactly "Read the poteto-mode skill's SKILL.md in full, including its Principles section, before any work. Do not spawn sub-agents."
- [ ] Before each wave's second dispatch, record the empty Files intersection of its two PRs in `ledger.tsv` (Appendix C).
- [ ] No PR touches `apps/qmx-ui/`, `~/.claude`, his real home `~/.qmx`, his real QMX folder, `C:/QMX-backup`, `C:/Users/Mubarak/Documents`, `C:/Users/Mubarak/Desktop/DATA_NARL`, his rclone configs (`D:/Tools/rclone/rclone-qmx.conf` and the profile's), Credential Manager or any vault value. Lanes run on throwaway folders and a scratch profile only, and key lanes inject a fake key store.

### PR mechanics, for every PR

- [ ] The coordinator creates `build/br-<id>` from the branch the table names in `D:/QMX-worktrees/bld-br-<id>` before the dispatch. Never `git stash`.
- [ ] The builder opens the PR ready with `gh pr create --base <parent-branch> --head build/br-<id> --repo MubarakHimself/QMX`.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Set `TMP` and `TEMP` to `D:/Temp`, `UV_CACHE_DIR` to `D:/Caches/uv`, put `D:/Tools/rclone` on `PATH`, and set `RCLONE_CONFIG` to an empty file in the worktree, so no rclone call reads his configs.
- [ ] The builder reads the code its Files block names before editing, reproduces each gap with a failing test first, then closes it. It runs `fmt-check`, `lint` and `types` in each package it touched and `tools/secret_scan.py`, reads each exit code, runs only the fast tests it added or changed, and never waits on a long command. It runs the `blast-radius` skill on its diff before the last push and proves the one fact its Build block names.
- [ ] Every line a person reads (a refusal, a job's line, a round's line, a doctor row) is plain words, names the folder or place, and says what to do next. No QMX-internal cap, ceiling or default-closed lock is added anywhere (rulings 106 and 137). A mutex that two writers take in turn is not a default-closed lock, and a refusal he can pass with an explicit choice is not one either.
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
- [ ] Every lane target is a folder under the lane's own folder, or a `:local` rclone remote there with `config` naming the lane's empty file. The default second drive is only ever a proposal (Appendix D), and lane 10 of each PR checks `C:/QMX-backup` is as it was.
- [ ] A lane that starts a host or a first-start card injects its bearer, turns the memory database off (`hindsight_runs` patched), and uses a port of its own, because on Windows pg0 writes his real profile (design 62 L7).
- [ ] A synthetic folder is made by B1's test builder (`filled_folder` in `QA/qmx-home/tests/backup_fixtures.py`, with `files`, `stores`, `once_bytes`, `long_path` and `secrets` parameters; `secrets` writes fake files at every secret path of Appendix D), never copied from `~/.qmx` or his QMX folder.
- [ ] Save captures as `evidence/br-<id>/check-<slug>.log`, then remove the check copy with `git worktree remove` and confirm no `qmx_host`, `claude`, `rclone` or `node` process from the lane is left.

## Make copies on This PC and on a second drive (B1)

Design 62 C1, C2 and B3, with guards L1 and L6. Rulings 106, 135, 136, 141 and 143. Review F1 to F4, F12, F13, E-M4 to E-M8, E-S4, E-S5, E-S7 and E-S10. Today `backups/` holds only LF3's pre-change copies of the one store an upgrade changes (`snapshot`, `HM/versions.py:235-302`), logged in `backups/backups.jsonl` (`_log`, `HM/versions.py:729-734`), and nothing removes them. Nothing copies the folder's data on a schedule or to another drive. The weekly GitHub snapshot copies only small stores (`QX/backup.py:60-198`), and each mini app's volume backup goes to an rclone remote (`AP/backup.py:122-165`). The copy and hash helpers a copy needs live in the bring-in (`long_path`, `_plain`, `copy_file` and `sha256_of` at `HO/bring_in.py:195-249`, with `CHUNK` and `PARTIAL` at `:123-124`; `Held` and `hold` at `HO/bring_in.py:817-857`, `_locked` and `_lock` at `HO/bring_in.py:968-994`); `_locked` raises the bring-in's own `Refused` (`:140`), and the card imports `copy_file`, `Refused`, `Held` and `hold` from there and catches `Refused` around the lock (`HO/first_start.py:50-64,577-593,667,683-684`). Secret files sit inside `data/`, not only in `keys/`. `data/vault/` holds `pairing-key`, `pairing-key.previous` and `run-pass-key` (`R/passes.py:72-75`) and, on a home that is not This PC, `tokens.json` (`HomeKeyStore`, `HO/venue_session.py:91,133-139`); the harness names `rclone.conf` and both Claude homes' `.credentials.json` and `.claude.json` as files that hold or may hold a login or a key (`secret_files`, `QA/qma-harness/src/qma/harness/tools.py:909-923`). The host deletes the oldest files of `cache/prices`, `library/blobs/transient`, `queue/telemetry` and `library/blobs/fetched` whenever the drive is below its floor (`give_way`, `HO/disk.py:41-46,86-110`), and that floor is a twentieth of the free space at start or his `disk.floor_gb` (`floor_bytes`, `HO/disk.py:55-62`). Done when one standard-library module under `BK/` makes a copy of `data/` into the quick undo in `backups/quick/`, sends it to a folder target he named at `<target>/QMX-backup/<home_id>/` holding each file once by sha256 in a pool and one manifest per copy, thins every place by its keep rule, refuses whole before writing when room is short, and logs every round in `backups/backups.jsonl`; the helpers live in `HM/files.py` and the bring-in and the card import them; and `[backup]` parses into one plan whose default second drive is a proposal he accepts, never a target by itself. Edge cases it must survive. No file of Appendix D's secret list is ever in a copy, in the quick undo, on a target or off-site (they are sealed by B7 or carried over by B2). A SQLite store written during the copy is copied as committed, through `VACUUM INTO` from a `mode=ro` connection into a fresh `.qmx-copying` name, so the copy never checkpoints his live store and never meets "output file already exists" (probe in Appendix A). A Library put during a round never leaves a copied ref naming an object the copy lacks, and a price month frozen during a round never leaves a copied `state.json` naming a file the copy lacks (Appendix D, the order). A file whose size and `mtime_ns` match the last manifest is not read again (L6, every file, not only the ones written once), and the log records each copy's seconds and bytes. A second round of an unchanged folder writes nothing but its log line. A round killed mid copy leaves only names ending `.qmx-copying` and a copy folder with no `manifest.jsonl`, which the next round removes before anything else. A manifest ends with a trailer line naming its line count and sha256, and one without a whole trailer is unreadable; thinning never removes a copy whose manifest is unreadable, and the pool sweep does not run at all while one is, with one line naming it (E-M4). The keep rule counts the newest days, weeks and months that hold a copy, never windows back from the clock, always keeps the newest copy and the newest one that passed a drill, and runs only after the new copy's manifest is in place, so a clock jump or a year away never empties a place (E-M5). The quick undo refuses a copy that would leave the folder's drive below the larger of 1 GiB (`FLOOR_BYTES`, `HM/versions.py:39`) and the host's floor, so a copy never makes a writer refuse `disk_full` (E-M7). A target with too little room refuses whole with one line and writes nothing. A target inside the QMX folder is refused by name; a target on the folder's own drive is kept with a line saying it does not survive a dead disk. A link or junction is never followed and never copied; the harness makes `claude-relayed/projects` again at launch (`_link_projects`, `QA/qma-harness/src/qma/harness/home.py:219-234`). A path over 260 characters copies (`long_path`). A target another QMX folder wrote to since this one last did, or a place the log has copied to before whose `<home_id>/backup.toml` is missing (another disk on the same letter), is refused by name until he carries on (E-S7). An exFAT USB disk works, because nothing on a target needs a hard link. A round with a key copy makes a new copy when the sealed names or their in-memory digest changed, even when the data did not (E-S10).

**Depends on.** The root `6260fe1d`.

**Files.**

- [ ] Create `HM/files.py` with `long_path`, `plain` (today `_plain`), `copy_file`, `sha256_of`, `CHUNK`, `PARTIAL`, `Held`, `hold`, `_locked`, `_lock` and `class Busy(Exception)`, which `_locked` raises. `HO/bring_in.py` defines `class Refused(Busy)` and imports the rest, its own copies deleted. `HO/first_start.py` imports `Held`, `hold` and `copy_file` from `qmx_home.files` and catches `Busy` where it caught a lock refusal (`:577-593`, `:683-684`) and in `_answer` (`:664-668`), which is where `make_new` and `open_existing` send a busy lock taken inside them, so a busy lock is still its 409 and never a 500 (F1, R-S1). `HO/__main__.py` catches `Busy` beside `Refused` in `first_start` (`:192`), so the command line still prints its one line.
- [ ] Edit `HM/versions.py`. `_log` becomes the public `log_line(layout, record)` and a reader `log_lines(layout)` returns the parsed lines, skipping a torn last line; `snapshot`, `_step_failed` and `completed_copies` use them.
- [ ] Create `BK/__init__.py` (the module's words, Appendix F) and `BK/plan.py`. `parse(section) -> Plan` reads `[backup]` (Appendix D shape) into `quick_undo`, `targets`, `leave_out`, `drill` and `keys` (kept raw for B7), ignores the mini-app volume keys and `repository` (`APP_KEYS`), and refuses a bad row by name with `PlanRefused`. An absent `targets` means none. A `Target` has `id`, `kind` (`folder` here), `path`, `every` (`hour`, `day` or `week`), `at`, `keep` and `on`. `proposal(layout, drives, free) -> Proposal | None` is the default second drive he may accept, read through `qmx_home._fixed_drives` (`HM/__init__.py:732-738`), with its line. `repository_of(target, layout)` and `source_of(document)` build a repository from a target row or from a card's `source`, the one factory B4 and B6 use.
- [ ] Create `BK/snapshot.py`. `LEFT_OUT`, `SECRET` and `WRITE_ONCE` as tables (Appendix D), `SECRET` being the files B2 carries over and B7 seals. `make(layout, *, previous, progress) -> Manifest` walks `data/`; copies each SQLite file by `VACUUM INTO` from a `mode=ro` connection (as `_reader` opens one, `HM/versions.py:697-698`) into a fresh `.qmx-copying` name, recording its row count per table and its own `user_version` and `min_reader`; copies each `*.jsonl` up to its last full line; copies each price month folder's data files before its `state.json`, reads `state.json` again, and copies the folder again when it changed; copies every other mutable file whole; reuses the previous manifest's hash for any file whose size and `mtime_ns` match; and lists the files written once last, in the order of Appendix D. The first line is a header (`format` `qmx-backup/1`, `home_id`, `stamp`, `why`, the release that made it, `platform.node()`, the folder's path, and the label's `format_version`, `min_reader`, `last_written_by` and `[stores]`); the last line is the trailer.
- [ ] Create `BK/repository.py`. The `Repository` protocol (`pool_has`, `put_pool`, `put_copy`, `copies`, `manifest`, `read_extra`, `fetch`, `drop`, `sweep`, `room`) and `FolderRepository`, used for `backups/quick/` and for a folder target, with `backup.toml`, `pool/ab/cd/<sha256>` and `snapshots/<stamp>/manifest.jsonl` written last through a `.new` rename. In the quick undo a file written once stays where it is in `data/` and its line says `at: live`; on a target every file is pooled. `sweep` runs only when every copy folder's manifest reads whole.
- [ ] Create `BK/keep.py` with the pure `kept(copies, keep, *, drilled) -> frozenset[str]` (counts by the newest buckets that hold a copy, the newest copy and the newest drill-passed copy always kept, LF3's `pre-*` copies and `before-upgrade` copies kept until 30 days after the first target copy made after them), and `BK/round.py` with the pure `due(last, now, every, at)`, `run_round(layout, plan, *, now, floor, only=None, sealed_keys=None, progress=None) -> RoundReport` under `backups/backups.lock` (taken with `hold`), `quick(layout, why, *, floor)` for one copy at once, the fork guard read from the log, and the round's log lines. `sealed_keys` returns the sealed bytes and a digest; the bytes go beside a target copy's manifest as `keys.sealed.json`, never in the quick undo, and a changed digest makes a new copy. B7 passes it, and B1 tests it with a fake.
- [ ] Add `QA/qmx-home/tests/backup_fixtures.py` (`filled_folder`), `test_backup_plan.py`, `test_backup_snapshot.py`, `test_backup_round.py`, `test_backup_keep.py` and `test_backup_secrets.py`. Edit `QA/qmx-host/tests/test_bring_in.py` only where it imports a moved name.

**Build.**

- [ ] Move the helpers first and run the host suite, so the move alone changes nothing; a test holds the first-start lock from a second handle and asserts the card still answers 409.
- [ ] Then the plan, the snapshot, the folder repository, the keep rule and the round, each step ending with its own test run.
- [ ] Prove the one fact the copy rests on. A test runs `make` with a hook that puts a Library item through `Store` and freezes a price month through the series store at each step boundary, and asserts that every object any copied `refs/` line names, and every file any copied `state.json` names, is in the manifest. It also runs `make` while a second thread commits to the engine ledger in a loop, and each copied store passes `PRAGMA quick_check` with the committed rows, while the live store's `-wal` size and `mtime_ns` are unchanged by the copy.

**You see.**

- [ ] On a throwaway folder with `filled_folder(secrets=True)`, `run_round` with one folder target writes `backups/quick/snapshots/<stamp>/manifest.jsonl` and `<target>/QMX-backup/<home_id>/snapshots/<stamp>/manifest.jsonl`, neither naming a secret file, and a second call with nothing changed logs a round line with `"result": "unchanged"` and copies no file.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The moved helpers behave as at the root and a busy lock is still the card's 409; the plan parses a full section, refuses an unknown kind, a duplicate id, a target inside the folder and a bad `at`, leaves the app keys alone, and makes no target when `targets` is absent; `proposal` gives none for his drive sizes and `C:/QMX-backup` for a roomy fake C:; a copy holds every file but `LEFT_OUT` and `SECRET`, no link, no writer's temporary file and no evictable blob, while a working copy's `.checkout.json` is copied; a 300-character path copies; each store's row counts equal the live store's and the live store is not checkpointed; an unchanged file of any kind is not read again; a month frozen mid copy leaves a consistent folder; `due` answers for hour, day and week across a PC that was off; `kept` keeps the newest buckets that hold copies after a two-year gap and after a clock jump, always the newest and the newest drilled copy; a sweep with one torn manifest removes nothing and names it; a full target refuses before writing; the quick undo refuses below the host's floor; a killed round's leftovers are removed by the next; the fork guard and the missing `backup.toml` refuse and carry-on clears them; `keys.sealed.json` lands beside a target manifest, never in the quick undo, and a changed digest makes a new copy of unchanged data. Run the home and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The home and host suites at parent and head. Save `b1-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A first round of `filled_folder(secrets=True)` (2,000 files, three 50 MB SQLite stores, 1 GB written once, one 300-character path, one junction, fake files at every secret path) to a folder target in the lane folder, then a grep of every byte under `backups/quick/` and the target for each fake secret value. Save `b1-first.log`. Pass when the target manifest lists every file not left out, each pooled file's sha256 equals its source's, each store's row counts equal the live store's, no junction and no secret path is listed, and the grep finds nothing.
- [ ] Lane 3. A second round with nothing changed, then a third after one row is added to one store. Save `b1-unchanged.log`. Pass when the second reads no file but the stores' stats, writes no pool file and logs `unchanged`, and the third pools exactly one new file.
- [ ] Lane 4. A round while one process commits to the engine ledger, another puts Library items and a third commits and freezes price months, each in a loop. Save `b1-live-writes.log`. Pass when every copied store passes `PRAGMA quick_check`, every object the copied `refs/log.jsonl` names is in the manifest, and every file each copied `state.json` names is in it.
- [ ] Lane 5. Kill the round's process during the send, then run a round again. Save `b1-killed.log`. Pass when the first leaves only `.qmx-copying` names and a copy folder with no manifest, and the second removes them and finishes.
- [ ] Lane 6. A target whose free space is patched to less than the copy needs, then a quick undo whose drive is patched to just above the host's floor. Save `b1-room.log`. Pass when both refuse with one line naming the room and neither place holds a new file.
- [ ] Lane 7. `proposal` in process with fake drives, once with his sizes (the folder on drive D, drive C with 22 GB free of 237 GB) and once with a roomy C, then a round with no `targets`. Save `b1-proposal.log`. Pass when the first gives no proposal with the warning line, the second proposes `C:\QMX-backup` as a value only, and the round writes only the quick undo.
- [ ] Lane 8. Sixty days of fake copies on a target, then a round; then the clock moved two years ahead, then a round; then one manifest truncated, then a round. Save `b1-keep.log`. Pass when the first keeps 14 daily, 8 weekly and 12 monthly copies, the second still keeps the newest buckets that hold copies, and the third removes no pool file and names the torn manifest.
- [ ] Lane 9. Two folders with one `home_id` send to one target in turn; then the target's `<home_id>/backup.toml` is removed and the first folder sends again. Save `b1-fork.log`. Pass when the second folder is refused by name with the first folder's machine and path, the missing `backup.toml` is refused as another disk, and each round after carry-on sends.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, then remove the throwaway folders, list processes and list `C:/QMX-backup`. Save `b1-processes.log`. Pass when every exit code is 0, nothing from the lanes is left, and `C:/QMX-backup` is as it was before the lanes.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for lane 2's first round to a folder target, for lane 3's unchanged round, and for a plain `shutil.copytree` of the same `data/` to the same drive. The parent has no copies, so the plain copy is the baseline of the same work.
- [ ] Probe. Each of the three, three times, interleaved, on fresh target folders.
- [ ] Baseline. Record the plain copy's median first.
- [ ] Rule. The first round's median is within 8 times the plain copy's, or the PR fails; the unchanged round is under 2 s at its median, an absolute budget. (Coordinator ruling 2026-10-27 at B1: the earlier 1.5 times cannot be met by the design itself, since `VACUUM INTO` of the stores and one sha256 of every byte take more than 1.5 times the plain copy before any file is written, and the quick undo stages every changed file once more. The first round happens once per place, runs as a background job, and never holds a request; every later round is the unchanged or nearly unchanged one. B1 measured 6.46 times on lane 2.)

**Review gate.** None. B1 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on `build/ls4`.

## Restore a copy, and run the drill (B2)

Design 62 C3 and B4, with guard L2. Rulings 136, 137 and 141. Review F2, F3, F5, F13, F15, E-M1, E-M2, E-M6, E-M9, E-S1 to E-S3, E-S8, E-S9, E-S14, E-S17 and E-S19. Today nothing restores; the card's restore answers 501 (`RESTORE_LATER`, `HO/first_start.py:80-83,561-562`). The store refusals tell him to "restore the copy taken before the upgrade" (`_too_new` and `_unreadable_entry`, `HM/versions.py:432-439,639-649`), which no tool does. A store of plain files keeps its version only in the label, outside `data/` (`HM/stores.py:1-7`, `_entry` at `HM/versions.py:660-667`), and a folder refused for a newer `format_version` is refused by the label alone (`HM/__init__.py:341-348`). The host's lock is `data/engine.lock`, taken by `single_instance` inside `serve_forever` (`HO/host.py:135,184-200,223`), well after `main` resolves the folder (`HO/__main__.py:82`). The engine ledger's events carry `at` (`E/ledger/migrations.py:41-43`) and so do the Library's ref moves (`LB/store.py:815,826`). A purge leaves `blobs/tombstones/<hex>.json` and moves `refs/purges/<hex>` (`LB/store.py:2175-2203`). Each app's lease generation is in `data/locks/<app>.lock` (`AP/volume.py:150-157`). Done when `BK/restore.py` offers `copies(repository)` (each copy by date, with why, files, bytes, the release that made it and its machine); `newer_than(layout, stamp) -> Newer`, read only, counting the runs started, Library ref moves, chats and price months in the folder newer than a copy (design 62 B4's list); `stage(layout, repository, stamp, *, replace=False, progress) -> Staged`, which rebuilds `data/` from the copy into `backups/restoring-<stamp>/data/`, checks every file's sha256 and every store's row counts against the manifest, and returns `Newer` with it; `finish(layout) -> Finished | None`, which takes the locks of Appendix D, sets the folder's `data/` aside whole into `backups/before-restore-<stamp>/data/` with a copy of the label, moves the staged `data/` in, carries the secret and lease files of Appendix D over from the set-aside data, writes the copy's `format_version`, `min_reader`, `last_written_by` and `[stores]` into the label keeping `home_id` and its other keys, records an `after_restore` entry (sync paused, fires paused, the blobs to purge again) and logs the restore, every step journalled in `backups/restore.json`; `cancel(layout)`; the readers `after_restore(layout)` and `pending_reindex(layout)` and the writers `carried_on(layout)` and `reindexed(layout)` that B5 calls; and `drill(layout, repository, *, sample, rng)`. Edge cases it must survive. A copy made by a newer QMX whose manifest format this release does not read is refused by name. A copy whose own SQLite versions need a newer QMX (the `_closed` rule, `HM/versions.py:442-443`, read from the manifest's per-file versions) is refused before anything is written. A copy of another QMX folder is refused by name unless he passes `replace`, or the folder's `data/` is new and empty; then the label takes the copy's `home_id` and his data is still set aside whole (E-S8). A manifest path that is absolute, holds `..`, a drive or a backslash, or leaves `data/` is refused, because a target is a disk he plugs in. A quick-undo file written once that is gone with a tombstone in the folder is skipped and its tombstone placed; only one gone with no tombstone, or one whose hash changed, refuses the copy, naming the file and offering the second drive (E-M6). A quick copy made before an earlier restore resolves its `at: live` files from the set-aside folder of the first restore after it (E-S14). A blob tombstoned in the folder or in the copy is never placed, its tombstone file is, and `after_restore` names it so B5 purges it again, moving `refs/purges/<hex>` on a writer and applying the purge on a replica (E-S17, R-S3). A file written once whose sha256 matches the folder's own is hard-linked from it, falling back to a copy where the drive refuses links. Room is checked before the first write. A second staged restore is refused while one waits. `finish` refuses with the host's line when `recorded_host` names a live process or `data/engine.lock` is held (F5). When a rename fails (a stray `postgres`, any open handle), `finish` changes nothing, keeps the staging and answers one line naming the folder and what to close (E-S2). A kill at any journalled step, the carry-overs and the tombstone list included, is completed by the next `finish` (E-S1). No link is ever placed. `after_restore` leaves the copy's runs and triggers as they are and B5 pauses fires until he carries on, so nothing from the copy re-runs by itself (E-S3). The drill takes each target in turn and a random copy on it, restores its mutable files and a random sample of its pooled files into `cache/restore-drill/`, checks their hashes, `PRAGMA quick_check` and row counts, checks room first, removes its folder when it ends, never reads or writes `data/` (L2), and deletes a pooled file whose hash is wrong, so the next round that holds that file pools it again and the copies naming it read whole again (E-S9).

**Depends on.** B1 (`BK/`, `HM/files.py`).

**Files.**

- [ ] Create `BK/restore.py` with `copies`, `newer_than`, `stage`, `finish`, `cancel`, `drill`, `after_restore`, `pending_reindex`, `carried_on`, `reindexed` and their result types; `finish` under `backups/restore.lock` and `backups/backups.lock`, its journal at `backups/restore.json` (F15).
- [ ] Edit `BK/repository.py` and `BK/snapshot.py` only where restore needs a read B1 left out (`fetch` into a staging folder).
- [ ] Add `QA/qmx-home/tests/test_backup_restore.py`, `QA/qmx-home/tests/test_backup_finish.py` and `QA/qmx-home/tests/test_backup_drill.py`.

**Build.**

- [ ] Reproduce first. A test copies a filled folder with B1, changes and deletes files in it, and fails because no restore exists.
- [ ] Add `copies`, `newer_than` and `stage` with every check, then `finish`, `cancel` and the readers, then the drill, each with its test.
- [ ] Prove the one fact. `finish` is idempotent and never races a host. A test kills it after each journalled step (journal written, `data/` set aside, staged `data/` moved in, each carry-over, label written, `after_restore` written, log line written), runs it again, and asserts one end state each time; another test holds `data/engine.lock` from a second process and asserts `finish` refuses and renames nothing.

**You see.**

- [ ] On a throwaway folder with a second-drive copy and 3 runs and 12 Library ref moves made after it, `stage` answers those counts, and `finish` then leaves `data/` equal to the copy file for file and hash for hash, `backups/before-restore-<stamp>/data/` equal to the folder's data before, and `data/vault/` and the plan login as they were.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A restore reproduces every hash and every row count; `newer_than` counts runs, ref moves, chats and price months; the earlier data is set aside whole; the secret and lease files of Appendix D are carried over; a new folder takes the copy's `home_id`; another home's copy is refused, and passes with `replace`; a newer format, stores too new by their own files, and an escaping path are refused; a folder refused for a newer `format_version` opens after the restore; a purged blob is skipped in a quick copy and named for a new purge; a quick copy from before an earlier restore reads its files from the set-aside folder; links are made where they can be and copies elsewhere; short room refuses before writing; a second stage is refused; `finish` refuses under a held `engine.lock` and a live recorded host; a failed rename changes nothing; each kill point resumes; the drill passes on a good copy, deletes a damaged pooled file and names it, and leaves `data/` as it was. Run the home suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The home and host suites at parent and head. Save `b2-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. B1's lane 2 folder, copied to a target, then 100 files changed, 20 deleted and 3 runs started, then staged and finished from the target into the same folder. Save `b2-same-folder.log`. Pass when `stage` reported the 3 runs, every file's sha256 and row count equals the manifest, the set-aside data's listing equals the listing taken before, and the fake `data/vault/` files and plan login are in the restored `data/` unchanged.
- [ ] Lane 3. The same copy restored into a fresh folder on a second scratch profile. Save `b2-new-folder.log`. Pass when the label's `home_id` equals the copy's, `data/` matches the manifest, and no secret path exists in it.
- [ ] Lane 4. `finish` killed after each journalled step in turn, then run again; then `finish` while a second process holds `data/engine.lock`. Save `b2-killed.log`. Pass when each resume ends with `data/` the copy and the set-aside folder whole, and the held lock refuses with nothing renamed.
- [ ] Lane 5. A quick-undo copy restored after one of its files written once was deleted with no tombstone, then after a blob was purged through `Store.purge`. Save `b2-quick-gone.log`. Pass when the first is refused naming the file with `data/` unchanged, and the second restores without the blob's bytes and names it for a new purge.
- [ ] Lane 6. Another folder's copy restored into a folder with data, without and then with `replace`. Save `b2-other-home.log`. Pass when the first is refused by name with nothing written, and the second restores with the copy's `home_id` and the earlier data set aside.
- [ ] Lane 7. A copy whose manifest is edited to name `../outside.txt`. Save `b2-escape.log`. Pass when it is refused and no file appears outside the staging folder.
- [ ] Lane 8. A folder whose label is marked format 3 with `min_reader` 3, and a copy from before. Save `b2-newer-format.log`. Pass when after the restore `resolve` opens the folder.
- [ ] Lane 9. The drill on lane 2's target, then on a target with one pooled file truncated, then a round. Save `b2-drill.log`. Pass when the first passes, the second deletes and names the file, the round pools it again, `cache/restore-drill/` is gone after each, and `data/` hashes as before.
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

Design 62 C2 (when) and F step 14, with guards L1 and L6. Rulings 106, 136, 137 and 140. Review F8, F9, E-M7, E-M8, E-S6 and E-S18. Today the host starts no backup of the folder (`serve`, `HO/host.py:704-844`). The control service's `BackupSchedule` sweeps mini-app volumes only, and only once `[backup] remote` is set (`QX/service.py:1600-1613`, `AP/backup_schedule.py`). `_settings_put` passes every `[backup]` key but `repository` to the volumes' `BackupSettings` (`QX/service.py:845-854`), a strict model (`extra="forbid"`, `AP/manifest.py:63-64`), so any new key there is refused today. `main`'s `match` ends in `case _: return host.stop(home)` after the environment is scrubbed (`HO/__main__.py:101-125`), so a new command added to `choices` and left to fall through would stop a running host. The host measures its floor once at start (`floor_bytes(section(control, "engine"), free_bytes(home))`, `HO/host.py:751`). An incident opens and resolves by its trigger id (`incident` and `resolve_incident`, `E/ledger/inbox_table.py:220,262`). Done when the host runs one `Backups` service (`HO/backups.py`) that reads the plan from `control.settings_get("backup")` every minute, runs every round, scheduled or asked for, as a `backup` job on `HO/jobs.py` on its own thread, never holds a request, and passes the host's floor; a round he must act on (a full target, a refused row, the fork guard) opens an incident `backup:<target>` through its own `InboxTable.open(home)` and the next copy to that place resolves it; a place with no copy for seven of its intervals (an unplugged disk) opens the same incident; one doctor row `backups` (`harness.doctor_from`, `HO/host.py:755`) names each place's last copy, the quick undo's size and the proposal while there is one; routes under `/api/backups` read the plan, the targets and their copies, start a round, carry on, and accept the proposal as a target; `python -m qmx_host backup` runs one round in the foreground; and the control service checks `[backup]` with `BK/plan.parse` and passes only `APP_KEYS` to the volumes' model. Edge cases it must survive. A folder with no `targets` gets only the quick undo, every hour, and the doctor row says his work has no copy on another drive and names the proposal; nothing is written outside the QMX folder until he accepts it or names a target (E-M8). Accepting writes one `[[backup.targets]]` row with the proposal's path, so the place never moves with free space afterwards. A round asked for while another runs answers 409 naming the running job, scheduled or not (E-S18). An unplugged target is skipped with a line and stays due; its incident opens only after seven intervals with no copy (E-S6). A host stopped mid round leaves what B1's killed round leaves, and the next round cleans it. Settings edited while the host runs take effect at the next sweep, as `BackupSchedule` reloads its own (`AP/backup_schedule.py:27-28`). A `PUT /api/settings/backup` with a bad target answers 400 naming the row, and the volumes' keys save as before. Every route sits behind the bearer, because `create_app` includes each extra router with `Depends(authenticate)` (`QX/server.py:462-463`). The first sweep runs one sweep after the host serves, so a start is never slowed by a copy. The service runs on every role; a proposal exists only where `_fixed_drives` lists drives, which is Windows. `backup` branches right after `resolve`, before `read_keep_names`, and never imports `qmx_host.host` (F8); its floor is `floor_bytes` read from the folder's `[engine]` section (`HO/disk.py` is standard library).

**Depends on.** B1 (`BK/round.py`, `BK/plan.py`). It shares no file with B2.

**Files.**

- [ ] Create `HO/backups.py`. `Backups(layout, control, *, clock, floor, sealed_keys=None)` with `run()` (the sweep), `doctor_line()`, `view()`, its own `Jobs`, and `backups_router(backups)` with `GET /api/backups`, `GET /api/backups/targets/{target_id}/copies`, `POST /api/backups/run` (202 with a job, body `{target}` optional), `GET /api/backups/jobs/{job_id}`, `POST /api/backups/targets/{target_id}/carry-on` and `POST /api/backups/targets/default/accept`.
- [ ] Edit `HO/host.py`. In `serve` build `Backups` with the floor from line 751, append `backups_router` to `answering` (near line 781), start `backups.run()` beside `replicator.run()` (near line 806) and cancel it with the other tasks (near line 822), and add `harness.doctor_from(backups.doctor_line)` beside the Library's row (near line 755).
- [ ] Edit `HO/__main__.py`. A `backup` command (`--home`, `--target`) branches right after `resolve`, runs one round in the foreground with the floor of `[engine]`, prints its lines, and exits 0 when it copied or had nothing to copy and 1 when a round was refused or another round holds `backups/backups.lock`.
- [ ] Edit `QX/service.py`. `_settings_put` for `backup` (near line 845) checks the section with `BK/plan.parse` and validates only `APP_KEYS` with `BackupSettings`; `_backup_settings` (near line 1609) reads only `APP_KEYS`.
- [ ] Add `QA/qmx-host/tests/test_backups_service.py` and `QA/qmx-host/tests/test_backups_routes.py`, and the settings cases in a new `QA/qmx-control/tests/test_backup_section.py`.

**Build.**

- [ ] Reproduce first. A test writes a `[backup.quick_undo]` table through the settings route and fails on the parent with `invalid_backup_settings`.
- [ ] Add the settings check, then the service and its sweep with an injected clock, then the routes, the doctor row, the incidents and the command.
- [ ] Prove the one fact. A round never holds a request. A test starts the host app with a round of B1's lane 2 folder running on its thread and asserts every `/api/health` call during it answers in under 1 s; another asserts `main(["backup", ...])` never imports `qmx_host.host`.

**You see.**

- [ ] A head host on a throwaway folder with one folder target answers `GET /api/backups` with the quick undo and the target, each with its last copy's time and `"result": "copied"`, within two minutes of its start.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The sweep runs a round when due and not otherwise, as a job; a run asked for during any round answers 409 naming its job; with no targets only the quick undo is written and the proposal is shown; accepting writes one target row; an unplugged target is skipped with no incident until seven intervals; a full target opens one incident and the next copy resolves it; the doctor row reads each place's age and the quick undo's size; a bad target is refused 400 by name; the volumes' keys still validate and save; the routes answer 401 with no bearer; the command exits 0, 1 when the lock is held, and never imports the host. Run the host, control and home suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The host, control and home suites at parent and head. Save `b3-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host on a filled throwaway folder with one folder target in the lane folder. Save `b3-first.log`. Pass when `GET /api/backups` shows a copy in the quick undo and the target within two minutes of start; the parent host makes none.
- [ ] Lane 3. `/api/health` polled every 200 ms during lane 2's first round. Save `b3-health.log`. Pass when every call answers in under 1 s.
- [ ] Lane 4. `POST /api/backups/run` during a scheduled round and again after it. Save `b3-run.log`. Pass when the first answers 409 naming the scheduled job and the second 202, and its job ends `finished` with each place's line.
- [ ] Lane 5. The target folder renamed away for eight of its intervals (clock patched), then back. Save `b3-unplugged.log`. Pass when no incident opens for seven intervals, one opens at the eighth, and the next copy after it is back resolves it.
- [ ] Lane 6. A target whose drive check is patched to too little room. Save `b3-full.log`. Pass when an incident `backup:<target>` is open and the doctor row is not ok.
- [ ] Lane 7. `PUT /api/settings/backup` with a target of kind `tape`, then one with the volumes' `remote` and `bucket`. Save `b3-settings.log`. Pass when the first answers 400 naming the row and the second saves as at the parent.
- [ ] Lane 8. `python -m qmx_host backup --home <folder>` with no host, then while a host's round holds the lock, then with a host running and no round. Save `b3-command.log`. Pass when the first exits 0 with its lines, the second exits 1 with one line, and the third copies while the host keeps answering `/api/health`.
- [ ] Lane 9. A head host with no `targets` and a proposal patched in, then `POST /api/backups/targets/default/accept`. Save `b3-proposal.log`. Pass when before the accept only the quick undo is written and the doctor row names the proposal, and after it the settings hold one target row and the next round sends there.
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

Design 62 F step 2, C3 and B4. Rulings 139, 141 and 142. Review F5 to F8, E-M1, E-M3, E-S2 and E-S16. Today `POST /api/first-start/restore` answers 501 (`HO/first_start.py:561-562`) and `python -m qmx_host restore` prints `RESTORE_LATER` and exits 2 (`HO/__main__.py:175-177`). The card offers restore only when no folder is found or a bring-in did not finish (`HO/first_start.py:336-341`). A found folder that is refused gets only "open" (`HO/first_start.py:336-337`), and `serve` exits 2 for a refused store (`HO/__main__.py:94-98`), so a store too new is a dead end although its line says to restore the copy taken before the upgrade (`HM/versions.py:639-649`, `HM/__init__.py:341-348`). Before an upgrade only the changed store is copied (`_copy_first`, `HM/versions.py:520-537`). `make_new` writes the pointer as soon as the folder exists (`HO/first_start.py:379-388`), and only the bring-in holds `first-start.lock` across its work (`HO/first_start.py:577`). Done when the card lists the copies a source holds (`POST /api/first-start/copies`), shows what a copy would replace (`POST /api/first-start/restore/check`, answering B2's `newer_than` counts for the chosen folder), and restores one as a job (`POST /api/first-start/restore` with `confirmed: true`, 202, read by `GET /api/first-start/jobs/{job_id}`) into a new folder or into the found folder it refused; a new folder is made with `qmx_home.resolve(folder, create=True)`, marked with `data/migration/restore-unfinished.txt` before the stage, and pointed at only after `finish`, so a restore that fails leaves a folder the card offers the restore for again and `serve` treats as a first start due (E-M3); the restore then counts as a finished choice and the handover answers it; `GET /api/first-start` offers restore for a refused folder, a folder with a refused store and a folder with an unfinished restore, and carries `second_drive`, the proposal and its line; `python -m qmx_host restore` lists, shows what a copy replaces, and restores only with `--yes`; `serve` and `start` finish a staged restore before they read the folder's stores, under B2's locks, and exit 2 with `finish`'s line when it cannot rename; when `check_open` says a store upgrades, `serve` first takes a quick copy of the whole folder tagged `before-upgrade`; and the refusal lines name the restore. Edge cases it must survive. A restore while a host serves the folder answers 409 naming its process. A restore while a bring-in or another restore runs in the card answers 409 naming the job, and the restore holds `first-start.lock` as the bring-in does (F7). A restore without `confirmed: true` answers 400 and changes nothing. A restore into one of A1's never places is refused by `Places.refusal`, and a removable drive gets its warning. A copy of another folder into a found folder answers 409 by name unless the body carries `replace: true`. A card killed mid stage leaves the folder's data unchanged and no `first-start.lock`; the next restore clears the unfinished staging. A card or host killed mid finish is completed by the next `serve`. A `before-upgrade` copy that cannot be made (room, or the host's floor) is one line on stderr and the start goes on, because the store's own pre-change copy still guards its upgrade. Restoring a `before-upgrade` copy on the same release says that the next start upgrades the stores again, and to install the older QMX first to stay on them (E-S16). The card answers with no bearer on the loopback only, as today.

**Depends on.** B2 (`BK/restore.py`) and B3 (`HO/__main__.py`).

**Files.**

- [ ] Edit `HO/first_start.py`. Delete `RESTORE_LATER`; add `POST /api/first-start/copies` (`{source}`) and `POST /api/first-start/restore/check` (`{folder, source, copy}`); `restore` (near line 561) takes `{folder, source, copy, confirmed, replace}`, refuses fast cases with 409 or 400, takes `first-start.lock`, makes and marks a new folder, and starts a `restore` job that stages and finishes, then writes the pointer; `offer()` adds restore to the choices for a refused folder, for a folder whose `check_open(layout).held_back` holds a refused store and for a folder marked `restore-unfinished.txt`, and carries `second_drive` from `BK/plan.proposal`; `Offer.lines` names the restore command; the card's job check covers both kinds.
- [ ] Edit `HO/__main__.py`. `restore` takes `--home`, `--from` (`dest="source"`, a folder target's path), `--copy`, `--yes`, `--replace` and `--create`, lists when `--copy` is left out, prints `newer_than` and changes nothing without `--yes`, and exits 0 restored, 1 when a host serves the folder, and 2 when refused; `serve` and `start` call `BK/restore.finish(layout)` right after `resolve` (near line 82), exit 2 with its line when it cannot finish, exit 3 for a folder marked `restore-unfinished.txt`, and take `BK/round.quick(layout, "before-upgrade", floor=...)` when `check_open` has an `upgrades` verdict, before the host opens any store.
- [ ] Edit `HM/versions.py` (`_too_new` and `_unreadable_entry` say "restore a copy from before the upgrade, with Restore from a backup on the start screen or python -m qmx_host restore") and `HM/__init__.py` (the newer-format line in `_opened`, near line 341, the same).
- [ ] Edit the tests that pin those lines and the 501. `QA/qmx-home/tests/test_versions.py:102,257,286`, `QA/qmx-engine/tests/test_ledger_versions.py:76,147` and `QA/qmx-host/tests/test_bring_in.py:458-471`. Add `QA/qmx-host/tests/test_card_restore.py` and `QA/qmx-host/tests/test_restore_command.py`.

**Build.**

- [ ] Reproduce first. A test posts a restore to the card and gets 501 on the parent.
- [ ] Add the card's routes and the offer, then the command, then the finish at start, then the `before-upgrade` copy, then the lines, each with its test.
- [ ] Prove the one fact. `serve` finishes a staged restore before any store opens, and never under a host. A test stages a restore whose engine ledger differs from the folder's, runs `main(["serve", ...])` with the host's `serve_forever` patched to read the ledger's row count and stop, and asserts it read the copy's count; a second test holds `data/engine.lock` from another process and asserts `serve` exits 2 with the host's line and the staging is kept.

**You see.**

- [ ] On a scratch profile with no QMX folder, the card lists the copies of a lane target, `POST /api/first-start/restore/check` answers what the copy replaces, `POST /api/first-start/restore` with `confirmed: true` answers 202, the job ends `finished`, the handover prints `{"handover": {"folder": "<folder>", "port": <p>}}`, and `serve --home <folder>` answers `/api/health` on that folder.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The card lists copies and shows what one replaces; an unconfirmed restore is 400; restore into a new folder takes the copy's `home_id`, writes the pointer only after finish, and then hands over; a failed restore leaves the marker, no pointer, and the restore offered again; restore into a refused folder works; another home's copy is 409, and passes with `replace`; a host on the folder is 409; a running bring-in is 409; a never place is refused; a refused store gets the restore choice; the command lists, shows counts, restores only with `--yes`, and exits 1 with a host up; `serve` finishes a staged restore first, exits 2 under a held lock or a failed rename, and exits 3 for an unfinished restore; a store that upgrades gets a `before-upgrade` copy first, and a failed copy is one line and the start goes on; each refusal line names the restore. Run the host, home and engine suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The host, home and engine suites at parent and head. Save `b4-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. The card on a scratch profile with no folder lists a lane target's copies, checks one, restores it confirmed into a new folder, and hands over; then `serve --home <folder>`. Save `b4-card.log`. Pass when the check answers counts, the job ends `finished`, the handover line names the folder, the host answers `/api/health`, and `data/` matches the manifest; the parent answers 501.
- [ ] Lane 3. A folder whose engine ledger is marked one version past this release with `min_reader` above it, and a `before-upgrade` copy from before. Save `b4-too-new.log`. Pass when `serve` exits 2 with the line naming the restore, the card shows the folder refused with open and restore, the restore says the next start upgrades again, finishes, and `serve` then starts.
- [ ] Lane 4. A folder whose engine ledger is one version behind this release, then `serve`. Save `b4-before-upgrade.log`. Pass when the quick undo holds a copy tagged `before-upgrade` whose ledger is at the older version, and the host starts with the ledger upgraded.
- [ ] Lane 5. `python -m qmx_host restore --home <folder> --from <target>` with no `--copy`, then with one and no `--yes`, then with `--yes`, then again while a host serves the folder. Save `b4-command.log`. Pass when the first lists, the second prints the counts, both change nothing, the third exits 0 with `data/` matching, and the fourth exits 1 with one line.
- [ ] Lane 6. A restore staged with `BK/restore.stage`, then `serve`; then a second staged restore with a process holding a file open in `data/`, then `serve`. Save `b4-finish-at-start.log`. Pass when the first `data/` is the copy before the host answers, and the second `serve` exits 2 naming what to close with the staging kept and `data/` unchanged.
- [ ] Lane 7. The card killed mid stage of a restore into a new folder, then started again. Save `b4-killed.log`. Pass when no `first-start.lock` and no pointer is left, the card offers the restore again for that folder, `serve` exits 3, and a new restore finishes.
- [ ] Lane 8. A copy of another folder restored through the card into a found folder, without and then with `replace: true`. Save `b4-other-home.log`. Pass when the first answers 409 by name with nothing written and the second finishes with the earlier data set aside.
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

## Restore from Settings, and make the first start after a restore safe (B5)

Design 62 C3 (from Settings, the drill, server sync paused) and B4, with guard L2. Rulings 136, 137 and 141. Review F5, E-M1, E-M2, E-S3, E-S13, E-S15, E-S17 and E-S19. Today the host has no restore and no drill. At every start with a Library server, `Replicator.for_home` replays `library/outbox.jsonl` and pulls the server's newer ref moves (`HO/host.py:804-806,1507-1516`), so a restored store would be mixed with the server's state. The engine's `autonomy.paused` setting stops the ticker claiming any fire or wake, and clearing it gives each clocked trigger at most one catch-up fire (`E/triggers/ticker.py:21-23`, `E/settings.py:132`, read at use by `E/runner.py:351-352`). `rebuild("all")` wipes both memory indexes and Hindsight's banks before it indexes (`MM/engine.py:312-320`), and the FTS file sits at `<home>/memory/fts.db` (`MM/engine.py:67,102`, `HO/host.py:525`). The host takes `data/engine.lock` in `single_instance` (`HO/host.py:184-200`). Done when `POST /api/backups/restore/check {target, copy}` answers what a copy would replace and `POST /api/backups/restore {target, copy, confirmed: true}` stages it as a job while the host keeps serving, its result naming the restart and the set-aside folder (Appendix E); `POST /api/backups/restore/cancel` removes a staged restore; `single_instance` takes `backups/restore.lock` without waiting before `data/engine.lock`, refusing with one line while a `finish` holds it, and lets it go once it holds `engine.lock`, so no host starts while a `finish` runs (F5); at the first start after a finished restore the host skips `Replicator.for_home`, sets `autonomy.paused` by a merge into `[engine]`, keeps its earlier value in B2's `after_restore` record, stops `hear` writing the Hub's flag, purges again each blob it names (on a replica through `apply_purge`), and rebuilds memory on its own thread, writing `reindexed` only when the rebuild succeeds and trying again at the next start; the doctor row says server sync and fires are paused after a restore and, while the rebuild runs, that recall is partial; `POST /api/backups/restore/carry-on` resumes sync and gives `autonomy.paused` back its earlier value; `GET /api/backups` shows a staged restore, the copy's runs that read `interrupted` and will resume on carry-on, and the folders set aside by earlier restores with their total size beside the drive's free room (E-S13); and the drill runs once a month on each target in turn, its result in the doctor row, a failed drill an incident, and the row says a bucket's drill downloads (E-S19). Edge cases it must survive. A stage while a round runs answers 409 naming the round's job, and a round while a stage runs waits for the next sweep. A second stage answers 409. An unconfirmed stage answers 400. The host keeps answering while it stages. Cancel with nothing staged answers 404 with its line. The drill checks room first and is skipped with a line when short. A rebuild with Hindsight on starts pg0 and embeds every row again, which the doctor row says. A restore log line already followed by `reindexed` starts nothing. The routes are POST and GET only, because the REST app's CORS allows GET, POST and PUT (`QX/server.py:475`).

**Depends on.** B2 (`BK/restore.py`) and B3 (`HO/backups.py`, `HO/host.py`). It shares no file with B4.

**Files.**

- [ ] Edit `HO/backups.py`. `POST /api/backups/restore/check`, `POST /api/backups/restore` (202 with a `restore` job), `POST /api/backups/restore/cancel` and `POST /api/backups/restore/carry-on`; the staged restore, the interrupted runs and the set-aside folders in `view()`; and the monthly drill in the sweep with its doctor row and incident.
- [ ] Edit `HO/host.py`. `single_instance` (near line 184) takes `backups/restore.lock` before `data/engine.lock`; in `serve`, while `BK/restore.after_restore(layout)` is set, skip `Replicator.for_home` (near line 804); set the pause with `control.settings_update("engine", ...)`, merging `{"autonomy": {**s.get("autonomy", {}), "paused": True}}` into the section, the nested form `hear` writes (`HO/host.py:977-981`), and never `settings_put`, which replaces the whole section (`QX/service.py:888`, R-M2); have `hear` push its row but write no flag (near line 979), so a Hub's `autonomy_paused: false` cannot clear the pause before carry-on (R-M1); and purge again the blobs it names, through `Store.purge` when `store.role` is `writer` and `Store.apply_purge` otherwise (`LB/store.py:891-894,2205-2209`, R-S3); after `compose_memory` (near line 758), when `BK/restore.pending_reindex(layout)`, run `memory.rebuild("all")` on its own thread and call `BK/restore.reindexed` only on success.
- [ ] Add `QA/qmx-host/tests/test_backups_restore.py`, `QA/qmx-host/tests/test_after_restore.py` and `QA/qmx-host/tests/test_restore_reindex.py`.

**Build.**

- [ ] Reproduce first. A test posts a restore to the host and gets 404 on the parent.
- [ ] Add the check, restore and cancel routes, then the lock order in `single_instance`, then the first start after a restore and carry-on, then the drill, each with its test.
- [ ] Prove the one fact. Nothing from a server or a trigger reaches a restored folder before he carries on. A test restores a copy into a folder whose fake Library server holds newer ref moves and whose copy holds an interval trigger past due, starts the host with its clock patched, and asserts no ref move from the server and no fire until carry-on, then one catch-up fire and the sync after it. B4's finish at start lands in the same wave, so this PR's tests call `BK/restore.finish` themselves.

**You see.**

- [ ] A head host answers `POST /api/backups/restore` with 202 and a job that ends `finished` with "Restart QMX to finish the restore; the work it replaces is set aside in backups/before-restore-<stamp>", and after `finish` and a new start the doctor row says sync and fires are paused, recall finds a row only the copy held, and carry-on resumes both.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The check answers counts; the restore route stages only when confirmed and answers with a job; a second stage, a stage during a round and a cancel with nothing staged each answer with their line; cancel removes the staging; a host does not start while `restore.lock` is held; after a restore the replicator is not built, `autonomy.paused` is set by a merge that keeps every other `[engine]` key, a Hub heartbeat does not clear it, and its earlier value comes back on carry-on the same way; each named blob is purged again, on a writer with its ref and on a replica through `apply_purge`; the view shows the staged restore, the interrupted runs and the set-aside total; the drill runs once a month on each target in turn by the injected clock, writes its result, and opens an incident on failure; the memory rebuild runs after a finished restore, writes `reindexed` only on success, and runs again after a failure. Run the host and home suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The host and home suites at parent and head. Save `b5-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host on a filled folder checks, then stages, a restore of its target's copy while `/api/health` is polled. Save `b5-stage.log`. Pass when the check names the counts, the job ends `finished` with the restart line, and every health call answers in under 1 s; the parent answers 404.
- [ ] Lane 3. Lane 2's host stopped, `BK/restore.finish` run, the host started, then a recall for a row only the copy held. Save `b5-recall.log`. Pass when recall returns the row and the log holds a `reindexed` line.
- [ ] Lane 4. A folder paired with a fake Library server holding newer ref moves and a fake Hub answering `autonomy_paused: false`, and a copy holding a past-due interval trigger, restored, started, then carry-on. Save `b5-paused.log`. Pass when before carry-on no ref move arrives, no fire runs and the `[engine]` section keeps every other key it held, and after it the sync runs, the pause takes its earlier value, and the trigger fires once.
- [ ] Lane 5. A stage, then cancel; then a second stage while one waits; then a stage while a round runs. Save `b5-refusals.log`. Pass when cancel removes the staging with `data/` unchanged, and the other two answer 409 naming the staged restore and the round's job.
- [ ] Lane 6. `finish` held at its first step while a second `serve` starts on the folder. Save `b5-lock-order.log`. Pass when the second `serve` refuses with one line saying a restore is finishing, exits 1, and opens no store.
- [ ] Lane 7. The clock patched to a month after the last drill, with two targets. Save `b5-drill.log`. Pass when the drill runs on one target, the next month's on the other, the doctor row carries each result, and `cache/restore-drill/` is gone.
- [ ] Lane 8. A memory rebuild made to fail once (patched index), then a second start. Save `b5-reindex-retry.log`. Pass when the first start writes no `reindexed` line and says recall is partial, and the second rebuilds and writes it.
- [ ] Lane 9. `GET /api/backups` after two finished restores. Save `b5-view.log`. Pass when it lists both set-aside folders, their total size and the drive's free room.
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

Design 62 C2's off-site row and D2 (each off-site backup target names a place). Rulings 136, 140 and 144. Review F11, E-M4 and E-S12. Today the only rclone use is a mini app's volume, sent with `rclone sync` or `copy --checksum` and never with rclone's own output in an answer, because that output can hold credentials (`AP/backup.py:41-61`). The review's probe found that `rclone copy --files-from` naming a file the source lacks exits 0. Done when a target of kind `rclone` (`remote`, `path`, optional `config`) holds the same layout as a folder target under `<remote>:<path>/<home_id>/`, through an `RcloneRepository` in `BK/rclone.py`. A copy is sent by one `rclone copy --files-from` from a tree of hard links in `cache/backup-send/` (a file copy where the drive refuses links); an `lsf` of the remote pool then checks every file arrived before `manifest.jsonl` goes up last; thinning is `rclone purge` of each dropped copy, its stamp checked against `^\d{8}T\d{6,12}Z$` first, and a `rclone delete --files-from` of the pool files no kept manifest names, only when every manifest read whole; a restore and the drill fetch the pool files they need with `rclone copy --files-from` into the staging folder and count any that did not arrive, by name; and `BK/plan.py` parses the kind and `repository_of` and `source_of` build it, so the host and the card need no change. Edge cases it must survive. rclone missing from `PATH` is one line saying to install it. A remote rclone cannot reach, or refuses, is one line naming the remote, never rclone's own text. Nothing is ever deleted outside `<path>/<home_id>/`, and `rclone sync` is never run. An upload killed mid way leaves a copy with no manifest, which listing ignores and the next round removes. A pool file the `lsf` check does not find stops the copy with a line and no manifest. The fork guard holds as on a folder target. `config`, when set, is passed as `--config`, and with none rclone reads only `RCLONE_CONFIG` or its own default; QMX never stores a remote's secret. Room is not checked, because the provider's own limit is the only limit (ruling 106), and a failed upload is its line. `cache/backup-send/` is emptied after each send. A remote name is checked against `^:?[A-Za-z0-9_-]+$`, and a one-letter name is refused on Windows, because `e:x` is drive E; the on-the-fly `:local` backend serves the lanes.

**Depends on.** B1 and B2 (`BK/plan.py`, `BK/repository.py`, `BK/restore.py`).

**Files.**

- [ ] Create `BK/rclone.py` with `RcloneRepository`, one `run(args)` that maps every failure to a plain line and records each command's arguments (which hold no secret) in the round's log line, the `lsf` arrival check, and the link tree.
- [ ] Edit `BK/plan.py` (the `rclone` kind and its checks, and its case in `repository_of` and `source_of`).
- [ ] Add `QA/qmx-home/tests/test_backup_rclone.py`, which skips by name when `rclone` is not on `PATH`.

**Build.**

- [ ] Reproduce first. A test parses a `kind = "rclone"` target and is refused on the parent.
- [ ] Add the repository's reads, then the send with its arrival check, then thinning and the sweep, then the fetch for restore.
- [ ] Prove the one fact. A copy counts only once every pool file and then its manifest are up. A test removes one pool file from the link tree after the batch is listed, and asserts the round stops with no manifest; another kills the send before the manifest, and asserts `copies` does not list it and the next round removes it.

**You see.**

- [ ] With `RCLONE_CONFIG` on an empty file, a round to the target `{kind = "rclone", remote = ":local", path = "<lane folder>/remote", config = "<lane empty file>"}` writes `<lane folder>/remote/<home_id>/snapshots/<stamp>/manifest.jsonl`, and a restore from it matches every hash.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The kind parses, a bad remote and a one-letter remote are refused; a round sends pool files, checks them, then the manifest; an unchanged round sends nothing; thinning purges dropped copies only after the stamp check and sweeps unnamed pool files only when every manifest read whole; a killed send is not listed and is removed; a missing pool file stops the copy; a fetch names each file that did not arrive; rclone missing and a failing remote each give one line with no rclone text; the fork guard refuses. Run the home suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The home and host suites at parent and head. Save `b6-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A round of B1's lane 2 folder to a `:local` rclone target in the lane folder. Save `b6-send.log`. Pass when the remote holds the manifest and every pooled file with its sha256, and no secret path.
- [ ] Lane 3. A restore from that target into a fresh folder. Save `b6-restore.log`. Pass when every hash and row count matches the manifest.
- [ ] Lane 4. The send killed after the pool upload, then a round; then a pool file removed from the link tree mid send. Save `b6-killed.log`. Pass when the first copy is not listed and the second round removes it and sends a whole copy, and the third stops with a line and no manifest.
- [ ] Lane 5. `rclone` taken off `PATH`. Save `b6-missing.log`. Pass when the round says to install rclone and the quick undo still gets its copy.
- [ ] Lane 6. A target naming `:sftp` at `127.0.0.1` port 1, and one with remote `e`. Save `b6-unreachable.log`. Pass when the first line names the remote and holds none of rclone's own output, and the second is refused by name.
- [ ] Lane 7. Sixty days of fake copies on the remote, then a round; then one remote manifest truncated, then a round. Save `b6-keep.log`. Pass when the kept set matches B1's rule, and the second round removes no pool file and names the torn manifest.
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

Design 62 C4, C3 (restore on a new PC) and F step 6. Rulings 116 and 135. Review F2, F3, F10, F14, E-S10 and E-S11. Today `R/vault.py` seals static keys per machine with X25519, HKDF-SHA256 and AES-256-GCM, the name as associated data (`VaultKey.seal` and `open`, `R/vault.py:154-185`), allows only model-provider rows, `qmx/read/*` and `qmx/data/*` and never a token name (`is_replicable`, `R/vault.py:89-104`), and reads Credential Manager by name without ever writing it (`KeyringSource`, `R/vault.py:494-513`). This PC's key store's `replace` overwrites a different value and removes keyring's stale companion entry (`CredentialManager`, `BR/credentials.py:47-75`). The key files sit in `keys/vault.key` (`R/vault.py:196`) and in `data/vault/` (`pairing-key`, `pairing-key.previous`, `run-pass-key`, `R/passes.py:72-75`), and `data/rclone.conf` may hold a bucket's key (`secret_files`, `QA/qma-harness/src/qma/harness/tools.py:909-923`). `qmx-router` gets `cryptography` only through `pyjwt[crypto]` (`QA/qmx-router/pyproject.toml`). Nothing seals keys for a backup. Done when `PUT /api/backups/passphrase` reads its body raw (so no 422 can echo it), takes the passphrase twice, says in plain words that a forgotten passphrase cannot be recovered and the copies it sealed stay closed, derives a key pair with Argon2id (cryptography 50.0.1, Appendix A), keeps only the public half, the salt and the costs in `[backup.keys]`, and answers the names that are never in the copy (Appendix D) so he knows what to type again on a new PC; each round seals, to that public half, the values `is_replicable` allows (the names of `PROVIDERS`, his `[providers]` rows, `qmx/read/ctrader-app` and the `credential_ref` of his `[connections]` rows, the names `pc_vault_document`'s caller seals today, `QX/node.py:1100-1104`) and the sealed files of Appendix D, as `keys.sealed.json` beside every target copy's manifest through B1's `sealed_keys`, with a digest of the sealed names and values kept only in memory; `POST /api/first-start/keys {source, copy, folder, passphrase}` opens it after a restore on a new PC, reads each name first and calls `CredentialManager.replace` only for names that read None, and writes each missing file with the modes `write_machine_key` uses (`R/vault.py:199`); `POST /api/backups/passphrase/off` removes `[backup.keys]`; and while it is off the doctor row says his keys are not in the backup. Edge cases it must survive. A wrong passphrase is refused by name and nothing is written. Two different entries of the passphrase are refused. The passphrase is never logged, stored, put in a job line, an error answer or a file; lane 5 greps for it. No key value or sealed file's content is in clear in any file under a target; lane 2 greps for each fake value. A token, an OAuth pair, `data/vault/tokens.json` and a live-trading key are never sealed (ruling 135). A changed passphrase seals new copies to the new key, and an older copy still opens with the passphrase it was sealed under, because its file carries its own salt and costs. A key he adds while the data is unchanged reaches the next target copy, because the digest changed (E-S10). An entry or a file this PC already holds is kept, never overwritten, and the answer names it (F10). A name Credential Manager cannot read is left out of the copy with a line. A copy with no key copy makes the card say his keys were not in that copy. The quick undo never holds a key copy.

**Depends on.** B4 (`HO/first_start.py`) and B5 (`HO/backups.py`). It shares no file with B6.

**Files.**

- [ ] Create `R/key_copy.py` with `derive(passphrase, salt, costs) -> VaultKey`, `seal_copy(public, salt, costs, values, files) -> Sealed` (bytes and digest) and `open_copy(sealed, passphrase) -> Opened`, each value sealed with `VaultKey.seal` under its own name and each file under `file:<path in the QMX folder>`.
- [ ] Edit `QA/qmx-router/pyproject.toml` to declare `cryptography==50.0.1`, because Argon2id needs 44 or newer (F14), and run `uv lock` so `qmx-agents/uv.lock` lists it among `qmx-router`'s dependencies (R-S2).
- [ ] Edit `HO/backups.py` (`PUT /api/backups/passphrase` and `POST /api/backups/passphrase/off`, the names gathered from settings, and the `sealed_keys` callable passed to every round, reading through `KeyringSource`).
- [ ] Edit `HO/first_start.py` (`POST /api/first-start/keys`, writing through `CredentialManager` and into the restored folder's `keys/` and `data/vault/`).
- [ ] Add `QA/qmx-router/tests/test_key_copy.py` and `QA/qmx-host/tests/test_key_copy_routes.py`, both with a `MemorySource` and a fake `SecretStore`.

**Build.**

- [ ] Reproduce first. A test runs a round with a passphrase set and finds no `keys.sealed.json` on the parent.
- [ ] Add `derive`, `seal_copy` and `open_copy`, then the passphrase routes, then the round's sealer, then the card's route.
- [ ] Prove the one fact. Only the passphrase opens the copy. A test seals with the public half alone, then asserts `open_copy` with the passphrase returns every value and file, a wrong passphrase raises by name, and no byte string of any value or file appears in the sealed file.

**You see.**

- [ ] On a second scratch profile with a fake key store, after the card restores a copy, `POST /api/first-start/keys` with the passphrase answers the names and files it wrote, and the fake store holds each provider key the first profile held while the new folder holds `keys/vault.key` and `data/vault/pairing-key`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Derive and open round-trip; a wrong passphrase and two different entries are refused; a body the route cannot parse is answered without the passphrase; a token name, `tokens.json` and a live-trading name are never sealed; `keys/vault.key`, `data/vault/pairing-key`, `pairing-key.previous`, `run-pass-key` and `data/rclone.conf` are sealed when present; a changed passphrase leaves older copies opening with the older one; a changed key makes a new copy of unchanged data; existing entries and files are kept and named; an unreadable name is left out with a line; the quick undo holds no key copy; off removes the table and the doctor row says so. Run the router and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The router and host suites at parent and head. Save `b7-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host with a fake key store holding three provider keys, one `qmx/read/*` key and one `qmx/token/*` pair, `filled_folder(secrets=True)`, a passphrase set, then a round. Save `b7-seal.log`. Pass when the target copy holds `keys.sealed.json` with the four static names and the sealed files, no token name and no `tokens.json`, and a grep of every file under the target finds none of the fake values or file contents.
- [ ] Lane 3. A second scratch profile with an empty fake key store restores that copy through the card, then posts the passphrase. Save `b7-open.log`. Pass when the fake store holds the four values and the new folder holds `keys/vault.key` and the three `data/vault/` key files.
- [ ] Lane 4. The same with a wrong passphrase. Save `b7-wrong.log`. Pass when it is refused by name and the fake store, `keys/` and `data/vault/` are unchanged.
- [ ] Lane 5. A grep of the host log, captured stderr, every job view, every answer (a malformed body's included) and every file in the folder and the target for the passphrase. Save `b7-leak.log`. Pass when it appears nowhere.
- [ ] Lane 6. The passphrase changed, then a round; then both copies opened; then one provider key added with no data change, then a round. Save `b7-change.log`. Pass when the older copy opens only with the older passphrase and the newer only with the newer, and the last round makes a new copy holding the added key.
- [ ] Lane 7. `POST /api/backups/passphrase/off`, then a round. Save `b7-off.log`. Pass when the new copy holds no key copy and the doctor row says the keys are not in the backup.
- [ ] Lane 8. The card's keys route on a profile whose fake store already holds one of the names with another value and whose folder already holds a `keys/vault.key`. Save `b7-kept.log`. Pass when that value and that file are kept and the answer names both.
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
  - [ ] One pass of each journey, in order, by the routes and commands of Appendix E. A host makes its quick copy, he accepts a patched proposal, and the target gets a copy; a restore checked and staged from Settings is finished by `serve`, sync and fires stay paused until carry-on, and recall finds a row only the copy held; a second scratch profile's card restores the target's copy into a new folder, opens the key copy with the passphrase, hands over, and the host starts; an rclone `:local` target gets a copy and a fresh folder is restored from it with `python -m qmx_host restore --yes`. Save `evidence/br-v/journeys.log`. Pass when each ends in its expected state, no secret value is in any target, no traceback is in any log, and `C:/QMX-backup` is as it was.
- [ ] Design 62 A3's tree, on `plan/agent-system`, gains the rows this program adds (`backups/quick/`, `backups/backups.lock`, `backups/restore.lock`, `backups/restore.json`, `backups/restoring-<stamp>/`, `backups/before-restore-<stamp>/`, `cache/backup-send/`, `cache/restore-drill/`, `data/migration/restore-unfinished.txt`), so every file has its documented home (ruling 143).
- [ ] `RESUME.md` names the restart contract of B5, the carry-on after a restore, and that his PC gets no second-drive proposal today (Appendix D).
- [ ] `just ci` at the stack tip exits 0, or every failure is a named environmental gap.
- [ ] `QUEUE.md` moves on to its next item.

## Appendix A. Prototype evidence

- Probes run on 2026-10-27 from `D:/Temp/g1-probe` with the `bld-ls4` venv's Python (`-I -B`). Nothing of QMX was started; no host, pg0, Hindsight, browser or Credential Manager was touched, and the folder was removed afterwards. The review re-ran each one and added three facts.
  - Argon2id from `cryptography` 50.0.1 (the locked version, `uv.lock`) derives 32 bytes at 256 MiB, 3 passes and 4 lanes in 0.3 s, and `X25519PrivateKey.from_private_bytes` takes them. B7's costs and budget rest on this.
  - SQLite 3.50.4. `VACUUM INTO` from a second connection while a first holds `BEGIN IMMEDIATE` with an uncommitted insert succeeds in 0.03 s and copies the committed rows only; the copy's journal mode is `delete`, which the store's opener sets back to WAL. It also works from a `mode=ro` connection, keeps `application_id` and `user_version`, and refuses an output file that already exists (the review's probe). B1's copy of a live store rests on this.
  - `os.link` on drive D (NTFS) works, and removing one name keeps the other. B2's links from the folder's own files rest on this.
  - rclone 1.75.2 at `D:/Tools/rclone`, run with `--config` on an empty file and the on-the-fly `:local:` backend, did `copy`, `copy --checksum`, `copy --ignore-existing`, `lsf -R`, `cat`, `copy --files-from`, `delete --files-from` and `purge` with no config and no network; an empty `--files-from` deletes nothing; `copy --files-from` naming a file the source lacks exits 0 (the review's probe), which is why B6 checks arrivals with `lsf`.
- Facts read in the code at `6260fe1d`, in `D:/Temp/g1-plan` and again in `D:/Temp/g1-fix` for the review's findings, each with its line in the PR that uses it. The pre-change copy and the backup log (`HM/versions.py`). The resolver, the label and the drive list (`HM/__init__.py`). The store table (`HM/stores.py`). The bring-in's helpers, `Refused` and lock, and the card's uses of them (`HO/bring_in.py`, `HO/first_start.py`). The command's `match` and exit codes (`HO/__main__.py`). The host's lock, start order, routers, tasks, floor and doctor rows (`HO/host.py`). The giving-way classes and the floor (`HO/disk.py`). The secret files (`R/passes.py`, `HO/venue_session.py`, `QA/qma-harness/src/qma/harness/tools.py`). The app leases (`AP/volume.py`). The `[backup]` section's strict app model (`QX/service.py`, `AP/manifest.py`). The REST app's CORS and the bearer on extra routers (`QX/server.py`). The vault's seal and allow-list (`R/vault.py`). The key store's replace (`BR/credentials.py`). The Library's layout, temporary names (`.<name>.<hex>`, `LB/store.py:331`), purge and catalogue rebuild (`LB/store.py`). Price months frozen by fingerprint, `open.parquet` and `state.json` written through `.state.tmp` (`packages/qmf-data/src/qmf/data/series.py:95-96,545-573,684-692`). Memory's FTS file and rebuild (`MM/engine.py`). The replicator (`HO/host.py:1507-1516`). The pause flag (`E/triggers/ticker.py:21-23`, `E/settings.py:132`, `E/runner.py:351-352`). The inbox incident and its resolve (`E/ledger/inbox_table.py:220,262`).
- Facts the builders prove by running code (each PR's Build block). The copy order leaves no copied ref or price state without its file, and the copy never checkpoints a live store (B1). `finish` resumes from every kill point and never runs under a host (B2). A round never holds a request, and `backup` never imports the host (B3). `serve` finishes a staged restore before any store opens, and exits 2 under a held lock (B4). Nothing from a server or a trigger reaches a restored folder before carry-on (B5). A copy is listed only once every pool file and its manifest are up (B6). Only the passphrase opens the key copy (B7).
- Unproven until lanes run. That a mini app's `road/` copied by B1's order rule restores consistently without the lease the volume backup takes (`AP/backup.py:135-142`); B1 lane 2's folder holds one mini app, and a failure there sends `apps/<id>/road/` to a lease-held copy. That rclone behaves against a real bucket or a server over SFTP as it does with `:local`. That the engine reads the nested `[engine.autonomy] paused` that `hear` writes (`HO/host.py:979-981`) as its dotted `autonomy.paused` (`E/runner.py:351-352`); B5's builder proves it with one test before relying on it, since `hear` itself compares the dotted key against the nested write.

## Appendix B. Not in this program

- **Design 62 C5, the GitHub snapshot reshaped to settings and definitions only.** The weekly template (`E/templates/backup-weekly/`, `QX/backup.py`) stays as built. Its reshape needs a Library-level meaning of "his published definitions" that is not built, and nothing in this program's journeys needs it. Logged to `BACKLOG.md`, with its two files inside `data/` (`weekly-backup.json`, `weekly-backup.lock`) that ruling 143 wants moved.
- Logged to `BACKLOG.md` at program start. Undoing a restore from `backups/before-restore-<stamp>/`, and removing such a folder on his click in Settings (B5 shows their size). A purge reaching the copies already in a pool. The agent guard protecting target folders outside the QMX folder (`guard_rules`, `QA/qma-harness/src/qma/harness/tools.py:930-975`, covers the QMX folder only). A dump of Hindsight's database (`pg_dump`, probe P-PGDUMP), instead of the rebuild B5 runs. A mini app's `road/` copied under its lease, if B1's lane fails. A copy when QMX closes and a second-drive copy before every migration (only the quick copy before an upgrade is built). A copy before a folder move (no folder move exists yet). Copying an append-only log by its new tail only, instead of whole when it grew. Sealing static keys outside `is_replicable`'s list (`qmx/firecrawl`, `qmx/tool/*`, `qmx/ctrader-client-id`, `qmx/ctrader-client-secret`); B7 names them as left out instead.
- `hear` compares the dotted `autonomy.paused` against the nested section it writes (`HO/host.py:979-981`), so with a Hub it may write the flag at every heartbeat; B5 only stops the write after a restore. Logged to `BACKLOG.md`.
- LF12, targets named from the place list and shown on the place screens (design 62 D4). Server homes and `qmx-recover`. The UI rows (UI session).

## Appendix C. Files two PRs share

| Pair | Shared file | Order |
|---|---|---|
| B1, B2 | `BK/repository.py`, `BK/snapshot.py` (B2 adds reads only) | B1 first |
| B2, B3 | none (B2 is `BK/` only; B3 is `HO/backups.py`, `HO/host.py`, `HO/__main__.py`, `QX/service.py`) | wave 2, side by side |
| B1, B4 | `HO/first_start.py` (B1 changes imports and the caught class), `HM/versions.py` (B1 the log helpers, B4 the lines) | B1 first |
| B1, B3 | `HO/__main__.py` (B1 catches `Busy`, B3 adds `backup`) | B1 first |
| B3, B4 | `HO/__main__.py` (B3 `backup`, B4 `restore` and the finish at start) | B3 first |
| B3, B5 | `HO/host.py` `hear` (B3 leaves it; B5 stops its write after a restore) | B3 first |
| B3, B5 | `HO/backups.py`, `HO/host.py` (B5 `single_instance` and the start after a restore) | B3 first |
| B4, B5 | none (B4 is `HO/first_start.py`, `HO/__main__.py`, `HM/versions.py`, `HM/__init__.py`; B5 is `HO/backups.py`, `HO/host.py`; B2 already holds every `BK/restore.py` reader B5 calls) | wave 3, side by side |
| B1, B6 | `BK/plan.py` (B6 adds the kind) | B1 first |
| B5, B7 | `HO/backups.py` | B5 first |
| B4, B7 | `HO/first_start.py` | B4 first |
| B6, B7 | none (B6 is `BK/rclone.py`, `BK/plan.py`; B7 is `R/key_copy.py`, `QA/qmx-router/pyproject.toml`, `qmx-agents/uv.lock`, `HO/backups.py`, `HO/first_start.py`) | wave 4, side by side |

## Appendix D. Defaults

Each is Claude's default, with the reason. He can overrule any of them, and each lives in `[backup]` where Settings edits it.

- The settings shape. The volume keys and `repository` stay where they are.

```toml
[backup.quick_undo]           # in <QMX>/backups/quick on the folder's own drive, always on
hours = 48                    # the newest 48 hours that hold an hourly copy
days = 7                      # then the newest copy of each of the newest 7 days that hold one

[[backup.targets]]            # none until he names one or accepts the proposal
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

- The second drive is a proposal (E-M8). The largest fixed drive that is not the folder's own, as `<drive>:\QMX-backup`, and never one the first copy would leave below the larger of 1 GiB and 10 % free (L1). It is shown by the card, `GET /api/backups` and the doctor row, and becomes a target only when he accepts it, so nothing is written outside the QMX folder to a place he did not name, and the place never moves with free space. On his PC there is no proposal today; naming a USB disk is his step.
- The quick undo keeps the folder's drive above the larger of 1 GiB and the host's floor (a twentieth of the free space at start, or his `disk.floor_gb`, `HO/disk.py:55-62`), and the doctor row shows its size (E-M7).
- One snapshot per round, sent to every due place. The quick undo is the round's own staging. Its files written once stay in `data/` and are named in place; its other files sit in `backups/quick/pool/`. A target pools every file. A file unchanged since the last copy is not read again (L6). This differs from design 62 C2's layout only in that mutable files are pooled by hash too, so an unchanged store is never copied twice to a target.
- `SECRET`, paths that are never in a copy in clear. `vault/` and everything in it (the pairing and run-pass keys, and on a home that is not This PC `tokens.json`), `rclone.conf`, `claude/.credentials.json`, `claude/.claude.json`, `claude-relayed/.credentials.json` and `claude-relayed/.claude.json` in `data/`, and the whole of `keys/` outside it. B2 carries them over from the set-aside data on a restore into the same folder. B7 seals `keys/vault.key`, `data/vault/pairing-key`, `data/vault/pairing-key.previous`, `data/vault/run-pass-key` and `data/rclone.conf`; never `data/vault/tokens.json` (ruling 135), the Claude login files (he signs in again), `keys/control-token` (the host makes one) or a lock.
- `LEFT_OUT`, other paths in `data/` never in a copy. `library/catalog.db` and `memory/fts.db` (indexes, rebuilt); `memory/hindsight/pg/` (rebuilt from Library rows by B5); the expendable classes the host deletes to make room, `library/blobs/fetched/`, `library/blobs/transient/`, `cache/prices/` and `queue/telemetry/` (`HO/disk.py:41-46`); `library/uploads/*.part`, `market/.staging/`; under `library/`, only a writer's temporary names `.<name>.<32 hex>` (`LB/store.py:331,2168,2553`, `LB/outbox.py:186`), so the durable `checkout/<ref>/<item>/.checkout.json` that `commit` reads back is copied (`LB/store.py:90,1509`); under `market/`, `.state.tmp`, `.incoming.parquet` and `.verify-*`; `settings.tmp`; the folders under `chats/` (launch files, rebuilt per launch); `apps/*/data/heartbeat-*` and `apps/*/data/tmp/` (as the volume backup leaves them, `AP/backup.py:101-107`); `*.lock`, `control-process.json`, `router.port`, `node.port` and SQLite's `-wal`, `-shm` and `-journal`; names ending `.qmx-copying`; every link and junction; and the `leave_out` globs he sets. `data/vault-store.json` and `data/passes/revoked.json` are copied, because they are ciphertext and a list, not secrets.
- Carried over on a restore into the same folder. `SECRET`'s paths in `data/` and `locks/` (each app's lease generation, `AP/volume.py:150-157`), from the set-aside data, so his sign-ins, pairing and app leases stay as they were (F2, F3, F13).
- `WRITE_ONCE`, paths in `data/` never rewritten in place. `library/objects/**`, the born blobs `library/blobs/??/**`, `library/blobs/tombstones/**`, `market/**/*.parquet` but `open.parquet` and dot names (frozen partitions are named by fingerprint), `migration/pre/**` and `migration/retired/**`.
- The order, so a copy is never mixed. First every SQLite store (the engine's ledger and inbox, then control, runs, apps, portfolio, then any other SQLite file), then the Library's `refs/`, `edges/` and `annotations/` files, then every other mutable file, each price month folder's data files before its `state.json`, which is read again and the folder copied again when it changed, and last the listing of the files written once. Each step copies a moment no earlier than the step before, so the ledger never names a Library object the copy lacks and no copied ref or price state names a file the copy lacks.
- The manifest's trailer and the sweep (E-M4). The last line is `{"end": true, "lines": n, "sha256": ...}`. A manifest without it is unreadable. Thinning never removes that copy, and the pool sweep does not run while one exists, with a line naming it. A copy folder with no manifest at all is a killed round's, removed at the next round's start.
- Keep rules (E-M5). Counts are of the newest days, weeks and months that hold a copy, never windows back from the clock. The newest copy and the newest copy that passed a drill are always kept. Thinning runs only after the new copy's manifest is in place. The quick undo keeps the newest 48 hours that hold an hourly copy, then the newest copy of each of the newest 7 days. A target keeps 14 daily, 8 weekly and 12 monthly. A `before-upgrade` copy, and each of LF3's `pre-*` copies, is kept until 30 days after the first target copy made after it (design 62 B3).
- The fork guard (E-S7). A round to a target first reads the target's newest copy. When the target holds copies and its newest is not the one this folder last sent there, restored from there, or carried on from, the round refuses by name; so does a place the log has copied to whose `<home_id>/backup.toml` is missing. Carry-on is his click (`POST /api/backups/targets/{id}/carry-on`). The log in `backups/backups.jsonl` is the record, keyed by the place's path, or its remote and path, and the `home_id`, so a restore on a new PC from a USB disk lets that disk carry on with no click. No new state file is added.
- A restore is checked, then confirmed (E-M1). Every restore path shows `newer_than` (the runs started, Library ref moves, chats and price months the folder holds that are newer than the copy) and needs `confirmed: true` or `--yes`.
- A restore sets the folder's `data/` aside whole in `backups/before-restore-<stamp>/`, never deleted by QMX, so nothing a restore replaces is lost. It never brings back a purged blob. It restores whole copies only; LF3's store-level pre-change copies stay the opener's own safety net and are never offered alone, because putting one store back would leave the others at a later moment. A copy of another folder replaces his data only with `replace`.
- The locks of a finish (F5). `finish` takes `backups/restore.lock`, then `backups/backups.lock`, refuses when `recorded_host` names a live process, takes `data/engine.lock` without waiting and refuses with the host's line when it is held, and lets it go right before the first rename. The host's `single_instance` takes `backups/restore.lock` before `data/engine.lock`, so no host starts in between. A rename that fails changes nothing and `serve` exits 2 with the line.
- After a restore (E-M2, E-S3). Until he presses carry on, the host builds no replicator, so nothing moves to or from a server, and `autonomy.paused` is set by a merge into `[engine]` that a Hub heartbeat cannot undo, so no trigger fires and no run the copy held resumes; carry-on gives `autonomy.paused` its earlier value, the ticker then makes at most one catch-up fire per clocked trigger, and the copy's interrupted runs resume as P2a made them land once. `GET /api/backups` names those runs first.
- Before an upgrade, `serve` takes one quick copy of the whole folder tagged `before-upgrade`, and B4's card offers it when a store later refuses (design 62 B4). The second drive gets its normal daily copy, so a start is never held by a slow USB disk.
- Copies run inside the host on their own thread, not as a workflow (Appendix G). A round he must act on opens an inbox incident; an unplugged disk opens one after seven of its intervals with no copy.
- A restore from Settings stages while QMX runs and finishes at the next start, so no store is ever replaced under an open connection.
- The sealed key copy holds what a new PC needs to be a restore, not a re-entry (design 62 C4), and seals exactly `is_replicable`'s names, the one allow-list servers already trust. Off until he sets a passphrase.

## Appendix E. The backup and restore contract (reference)

The UI agent and the desktop app (`qmx-desktop`, engine AD-48) follow this contract.

| Step | The desktop app runs | It reads | Then |
|---|---|---|---|
| 1 | `python -m qmx_host serve --port <p> --ui-origin <origin>` | a staged restore is finished first, then the start goes on as in the loose-strings contract | as there |
| 1 | the same | exit 2 with one line, a refused folder, a refused store, or a restore that could not finish | show the line, and offer the card, which offers restore |
| 1 | the same | exit 3 with a restore into a new folder that did not finish | step 2 |
| 2 | `python -m qmx_host first-start --serve --port <p> --ui-origin <origin>` | `GET /api/first-start` with `restore` in `choices` and `second_drive` | the UI shows the card |
| 2 | the same | the copies, the check's counts shown to him, his confirm, a finished restore job, then `POST /api/first-start/handover` | step 3 of the loose-strings contract |
| 4 | the UI's restore in Settings | the check's counts shown to him, his confirm, then the restore job ends `finished` with `restart` true | stop the host, then step 1 |
| 5 | the UI after a restore | `GET /api/backups` says sync and fires are paused and names the copy's interrupted runs | his carry-on, `POST /api/backups/restore/carry-on` |

- The host's routes, all behind the bearer. `GET /api/backups` (the plan, the proposal, each place's last copy and line, the quick undo's size, a staged restore, the pause after a restore, the folders set aside and their total). `GET /api/backups/targets/{target_id}/copies` (each copy by date). `POST /api/backups/run` (202 with a `backup` job; body `{target}` optional). `GET /api/backups/jobs/{job_id}`. `POST /api/backups/targets/{target_id}/carry-on`. `POST /api/backups/targets/default/accept`. `POST /api/backups/restore/check` (body `{target, copy}`). `POST /api/backups/restore` (202 with a `restore` job; body `{target, copy, confirmed}`). `POST /api/backups/restore/cancel`. `POST /api/backups/restore/carry-on`. `PUT /api/backups/passphrase` (body `{passphrase, again}`). `POST /api/backups/passphrase/off`. The plan itself is edited with `PUT /api/settings/backup`.
- The card's routes, on the loopback with no bearer. `POST /api/first-start/copies` (body `{source}`, the copies by date). `POST /api/first-start/restore/check` (body `{folder, source, copy}`). `POST /api/first-start/restore` (202 with a `restore` job; body `{folder, source, copy, confirmed, replace}`). `POST /api/first-start/keys` (body `{source, copy, folder, passphrase}`). A `source` is `{kind: "folder", path}` or `{kind: "rclone", remote, path, config}`.
- The commands. `python -m qmx_host backup --home <folder> [--target <id>]` exits 0 when it copied or had nothing to copy and 1 when refused. `python -m qmx_host restore --home <folder> --from <path> [--copy <stamp>] [--yes] [--replace] [--create]` lists with no `--copy`, prints what the copy replaces and changes nothing without `--yes`, and exits 0 restored, 1 when a host serves the folder, 2 when refused.
- A refusal answers 409 with `detail`, its one line; a bad or unconfirmed body answers 400, never echoing a passphrase.

## Appendix F. Words

- **Backup.** Keeping copies of his QMX folder's data so he can go back to one.
- **Copy.** One dated moment of his data in one backup place, picked by date. Code and disk call it a snapshot (`snapshots/<stamp>/`).
- **Quick undo.** The copies in `backups/quick/` on the folder's own drive, every hour. They undo a bad edit or a bad upgrade and do not survive a dead disk.
- **Target.** A backup place outside the folder that he named and that holds copies, a folder on another drive (the second drive) or an rclone remote (off-site).
- **Proposal.** The second drive QMX suggests. It is not a target until he accepts it.
- **Round.** One pass that makes a copy and sends it to every place that is due.
- **Pool.** The files a place holds once each, by sha256, which every copy's manifest names.
- **Restore.** Rebuilding `data/` from one copy he confirmed, with the folder's earlier data set aside whole.
- **Set aside.** Moved, never deleted, into `backups/before-restore-<stamp>/`.
- **Carry on.** His click after a restore that lets server sync and fires start again, or that lets this folder keep sending to a target another folder wrote to.
- **Drill.** QMX restoring a sample of one copy into `cache/restore-drill/` once a month to prove it can.
- **Passphrase.** His words that open the sealed key copy. QMX keeps only the public half derived from it, and cannot recover a forgotten one.
- **Sealed key copy.** His static keys and key files sealed to that public half, beside each target copy.
- **Pre-change copy.** LF3's copy of the one store an upgrade changes, kept in `backups/pre-*`. QMX's own safety net, not a copy he restores.

## Appendix G. Alternatives weighed

- The round as the `backup` script workflow that replaces `backup-weekly` (design 62 G's LF8 row). Rejected. A template's triggers install disabled (`add_disabled_trigger`, `E/templates/install.py:92`); a script run needs a work zone and an environment; and the host already runs its own timed work beside the engine (`Replicator.run`, `HO/host.py:806`).
- A new `qmx-backup` workspace package. Rejected. `qmx_home` already owns `backups/` and its log, the module needs only the standard library, and a new package adds workspace members, sources, test ignores and CI rows for no reader.
- Hashing every file every round. Rejected. A file whose size and `mtime_ns` match the last manifest keeps its hash, as rsync does; a restore and the drill hash every file they place.
- A separate hash cache file. Rejected. The newest manifest is the cache, so no file is added (ruling 143).
- Restoring in place by moving only the files that differ. Rejected. It leaves no whole earlier state to go back to; setting `data/` aside whole is one rename on the same drive and loses nothing.
- Restoring a single store from LF3's pre-change copy. Rejected. The other stores would stay at a later moment, which mixes the folder.
- `rclone sync` to a remote. Rejected. Run from a new or empty pool it would delete the remote's copies; `copy`, `purge` and `delete --files-from` delete only what a keep rule names.
- Storing the passphrase or its private half. Rejected. A daily copy needs only the public half to seal, so nothing that opens the keys sits on the PC (design 62 C4).

Choices where the review offered options, each with why.

- F1, the lock refusal. `HM/files.py` raises `Busy` and the bring-in's `Refused` subclasses it, so the card keeps one `except` and every old catch still works.
- F2 and F3, the secret files. Left out of every copy, carried over on a same-folder restore, and the key files sealed by B7, rather than sealing the whole `data/vault/`, because `tokens.json` must never leave its home (ruling 135).
- F11, B6's lane 8. The lane targets set `config` to the lane's empty file, so the lane checks the mechanism as written rather than an environment variable.
- E-M1, showing what a restore replaces. A separate check route plus `confirmed: true` (and `--yes` on the command), not a one-route preview, so an old client that never shows the counts cannot restore by accident.
- E-M2 and E-S3, the start after a restore. One pause covering server sync and fires, ended by one carry-on, using the engine's own `autonomy.paused` rather than marking the copy's runs, because the engine already defines what clearing it does (one catch-up fire, held runs resumed) and he sees the runs before he carries on.
- E-M5, the drilled copy. The newest drill-passed copy is kept, not every copy newer than it, because on the quick undo that would keep a month of hourly copies.
- E-S8, another folder's copy. An explicit `replace` rather than a fixed refusal (ruling 137), since his data is set aside whole either way.
- E-S9, a damaged pool file. The drill deletes it, and copies naming it read as missing that file until a round pools it again, so no mark file is added.
- E-S14, quick copies after a restore. They read their files from the set-aside folder of the first restore after them, which holds exactly the data they were taken of, rather than being dropped.
- E-S11, keys outside the vault's allow-list. Named as left out, not sealed, so the backup trusts the same list servers already do (Appendix B logs the wider list).
- The wave overlap the review found. B2 adds every `BK/restore.py` reader B5 calls, and B5 owns the `single_instance` change, so wave 3 stays disjoint.

## Appendix H. Gates and calls

- G-LAND. He lands the stack himself.
- No call needs him. No PR touches money, his vocabulary or irreversible scope. The words are design 62 H's, which he read; deleting a set-aside folder stays his click and is not built here; setting a passphrase is his choice whenever he wants his keys in the backup. Accepting a second drive, or naming a USB disk, is a step only he can do, and the doctor row asks for it in plain words.
