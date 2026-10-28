# QMX sync to my storage and connect from the screen, build program

This program builds design 06 (`research/sync/06-sync-and-connect-design.md` at `14f9df14`, with its review folded in section 20). His work is kept on This PC first, sent as dated, packed copies to any storage he connects, and one step-by-step dialog connects storage, compute and deep logs, for the screen and the copilot alike.
The rules it enforces. Everything works with no cloud, and This PC is the first storage. No passphrase or lock of any kind. A secret never travels. No QMX cap. Every setting comes back with its default and is editable in the UI. No settings write replaces a section. Nothing beyond his seeds and the closed tickets is built.
There are 5 PRs in 3 waves. SY1 subtracts first, then decides what is saved by class and reshapes the copies on This PC. SY2 connects a storage from one dialog. SY3 packs, compresses and sends copies through rclone, with QMX's monthly upkeep. SY4 connects compute and deep logs. SY5 covers install and first start, sync before update, restore from a storage, and the folded UI gaps.
The stack roots on `build/br5` at `78587edc` (PRs 225 to 229, PR 229 after its fix round). Appendix B lists what stays out.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a test run, or a SHA. The body is a how-to. The appendices explain and record.

Each PR section opens with a preamble naming the design 06 sections, rulings and review findings it serves, what the code does today with its file and line at `78587edc`, and its done line with the edge cases it must survive. Then come the nine blocks `check-plan.mjs` requires.

Path shorthands. `QA/` is `qmx-agents/packages/`. `HO/` is `QA/qmx-host/src/qmx_host/`, `HM/` is `QA/qmx-home/src/qmx_home/`, `BK/` is `HM/backup/`, `QX/` is `QA/qmx-control/src/qmx_control/`, `E/` is `QA/qmx-engine/src/qmx_engine/`, `AP/` is `QA/qmx-apps/src/qmx_apps/`, `QH/` is `QA/qma-harness/src/qma/harness/`, `QR/` is `QA/qmx-remote/src/qmx_remote/` and `BR/` is `QA/qmx-broker/src/qmx_broker/`. Line numbers are at `78587edc` in `D:/QMX-worktrees/bld-br5`. "06 section N" is a section of the design.

The store is `D:/QMX-worktrees/qma-ship/wrapup/`, with `QUEUE.md`, `RESUME.md`, `BACKLOG.md`, `lows.md`, `ledger.tsv`, `stack-list.md`, `dispatch/`, `review/` and `evidence/`.

The program follows `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md` with the overrides of `LOCAL-FIRST-PLAN.md`, as `BACKUP-RESTORE-PLAN.md` did. Builders are Claude Opus 5.5 (`poteto-agent`, `model: opus`), at most two at once, never two on one file. A fresh Opus reviewer agent reviews every diff and runs the edge-case lens of `bmad-review` on every PR, because each one reads or writes his data. The coordinator runs the suites, `just ci` and the lanes in the background and allows one fix round. Low findings go to `lows.md`; anything new goes to `BACKLOG.md`. He lands the stack himself.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] Confirm the shell (Windows 11, PowerShell 7 and Git Bash; in PowerShell `$H` and `$h` are one variable) and the root (`git -C D:/QMX-worktrees/bld-br5 rev-parse build/br5` is `78587edc`). Logged in `RESUME.md`.
- [ ] Read the trunk rules with `git show origin/main:CLAUDE.md`, then rulings 105 to 145 of `research/methodology/26-operator-rulings-and-alignment.md` (106, 116, 135 to 137 and 140 to 145 above all), then design 06 sections 1 to 15 and 20, then the review `D:/QMX-worktrees/qma-ship/wrapup/review/design-sync-edge-cases.md`, then Appendices D to F of this plan.
- [ ] No hourly `/loop 1h` tick, because builder and background-job notifications wake the coordinator. Post a short status message to the operator only when a PR opens, a verdict lands or a blocker appears.
- [ ] Never stop to ask him during the build. Stop only for a credential, a real ambiguity in this plan, or a step only he can do (Appendix H).
- [ ] Before dispatch, add Appendix B's items to `BACKLOG.md`, and strike planned PRs 6 and 7 from `tracker/qma-v2/BACKUP-RESTORE-PLAN.md` on `plan/agent-system` (subtract item 3's plan text; PR 7 to the backlog).
- [ ] Before wave 2, fetch the pinned OpenObserve release once into `D:/Tools/openobserve/` and check it against its published sha256 (`research/sync/sources/openobserve-downloads.md`). Record the version and hash in `RESUME.md`. If it cannot be fetched, SY4's lanes 4 and 8 run against the fake binary and the real per-user run is logged as unproven (Appendix A).

### Spawn owners

| # | Id | PR | Wave | Branches from | Runs beside | Proving check |
|---|---|---|---|---|---|---|
| 1 | SY1 | Subtract, decide what is saved by class, and reshape the copies on This PC | 1 | `78587edc` | SY2 | a folder filled through every package's own writers has a rule for every path, and its copy holds exactly the four sent classes with no planted secret |
| 2 | SY2 | Connect a storage from one dialog | 1 | `78587edc` | SY1 | a folder storage and an rclone `local` storage connect through the routes, each writing one place row, with no planted secret in any command line, log or answer |
| 3 | SY3 | Pack, compress and send copies through rclone, with the monthly upkeep | 2 | the wave 1 tip | SY4 | two hosts on one `home_id` sync and re-pack at the same time twenty times and every manifest left restores hash-equal |
| 4 | SY4 | Connect compute and deep logs | 2 | the wave 1 tip | SY3 | the server kind runs its cards and checked steps against a fake shell and writes one `owned` row that can run and keep; deep logs on this PC answers its health on the loopback |
| 5 | SY5 | Install and first start, sync before update, restore from a storage, and the folded UI gaps | 3 | the wave 2 tip | none | a second scratch profile restores from an rclone `local` storage on the card, hands over, and the storage it restored from syncs again with no "connect again" |

- [ ] Spawn one fresh Opus builder per PR in the background with `subagent_type: poteto-agent` and `model: opus`, from a dispatch file saved in `dispatch/`. Its first words are exactly "Read the poteto-mode skill's SKILL.md in full, including its Principles section, before any work. Do not spawn sub-agents."
- [ ] Before each wave's second dispatch, record the empty Files intersection of its two PRs in `ledger.tsv` (Appendix C).
- [ ] No PR touches `apps/qmx-ui/`, `~/.claude`, his real home `~/.qmx`, his real QMX folder, `C:/QMX-backup`, `C:/Users/Mubarak/Documents`, `C:/Users/Mubarak/Desktop/DATA_NARL`, his rclone configs (`D:/Tools/rclone/rclone-qmx.conf` and the profile's), Credential Manager, a Google account, his server or any vault value. Lanes run on throwaway folders and a scratch profile only, and every key lane injects a fake key store (`SecretStore`, `BR/credentials.py:33-36`).

### PR mechanics, for every PR

- [ ] The coordinator creates `build/sy<n>` from the branch the table names in `D:/QMX-worktrees/bld-sy<n>` before the dispatch. Never `git stash`.
- [ ] The builder opens the PR ready with `gh pr create --base <parent-branch> --head build/sy<n> --repo MubarakHimself/QMX`. SY1 and SY2 take `build/br5` as their base.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Set `TMP` and `TEMP` to `D:/Temp`, `UV_CACHE_DIR` to `D:/Caches/uv`, put `D:/Tools/rclone` on `PATH`, and set `RCLONE_CONFIG` to an empty file in the worktree, so no rclone call reads his configs.
- [ ] The builder reads the code its Files block names before editing, reproduces each gap with a failing test first, then closes it. It runs `fmt-check`, `lint` and `types` in each package it touched and `tools/secret_scan.py`, reads each exit code, runs only the fast tests it added or changed, and never waits on a long command. It runs the `blast-radius` skill on its diff before the last push and proves the one fact its Build block names.
- [ ] Removals land as the PR's first commits, before the additions they make room for (principle subtract-before-you-add). A caller moves to a new API in the same PR that deletes the old one.
- [ ] Every line a person reads (a refusal, a job's line, a card, a doctor row) is plain words, names the folder, storage or place, and says what to do next. No QMX-internal cap, ceiling or default-closed lock is added anywhere (rulings 106 and 137). A floor that protects his drive is not a cap. A refusal he can pass with an explicit choice is not a lock.
- [ ] Every settings write merges (I14). Every new setting has a default the `GET` returns and the UI can edit.
- [ ] Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. PR bodies end with the Claude Code line.

### Verdict and merge, for every PR (append to the stack, merge on his go)

- [ ] At the code-ready head the coordinator runs the touched suites with `-n 2` and lanes 1 to 4 in the background, reads every PASS and FAIL line of each log (not its tail or its exit code alone), and saves the logs. A fresh Opus reviewer agent (one per PR, `model: opus`, told not to spawn sub-agents) reads the PR section, the full diff, the edge-case lens and those logs, and writes `review/sy<n>-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] Blockers go back to a fresh builder with the consolidated brief for one fix round. Low findings go to `lows.md`.
- [ ] `ledger.tsv` gets head, parent and patch-id.
- [ ] The two PRs of a wave join with a merge commit on the second PR's branch, never a rebase, and that PR's base becomes the first's branch. The join gets the wave's join lane (each wave's second PR, Merge block). `just ci` runs at the stack tip once at the end, with `D:/Tools/rclone` on `PATH`, under `D:/QMX-worktrees/.ci-lock`.
- [ ] He lands the stack himself from the one full list the coordinator sends when `QUEUE.md` is empty.

### Boot recipe, for every live lane

- [ ] `git worktree add --detach D:/Temp/sy<n>-check <head>`, then `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`. A lane that needs the parent adds a second worktree at the parent the same way.
- [ ] A lane runs on a throwaway QMX folder under `D:/QMX-worktrees/qma-ship/wrapup/homes/sy<n>-<lane>/`, made with `qmx_home.resolve(..., create=True)`, with `USERPROFILE`, `APPDATA`, `LOCALAPPDATA` and `HOME` on a scratch profile under the same folder, so the pointer file lands there too, and with `QMX_HOME` unset.
- [ ] Every lane script starts from the guard of PR 229's lanes (`HOMES` at `wrapup/evidence/br5/owner_lanes.py:72`). It refuses a `--home` outside `homes/`, prints one `PASS` or `FAIL` line per check, and exits non-zero when any check failed.
- [ ] Every storage is a folder under the lane's own folder, or an rclone remote of type `local` named in the lane's own `rclone.conf`. No lane uses a real account, server, browser or Credential Manager. Keys go to a fake `SecretStore`. Fake secrets are planted in the lane's `rclone.conf`, in one question-loop answer and in a hand-edited `settings.toml`, and lane 10 of each PR greps for them.
- [ ] A lane that starts a host or a first-start card injects its bearer, turns the memory database off (`hindsight_runs` patched), and uses a port of its own, because on Windows pg0 writes his real profile (design 62 L7).
- [ ] A synthetic folder comes from `filled_folder` in `QA/qmx-home/tests/backup_fixtures.py`, never from `~/.qmx` or his QMX folder. SY1 adds a `writers=True` parameter that also writes through each package's own writers (a chat transcript, a mini-app volume, a Library put, a price month).
- [ ] Save captures as `evidence/sy<n>/check-<slug>.log`. Then remove the check copy with `git worktree remove`, and confirm no `qmx_host`, `claude`, `rclone`, `node`, `postgres`, `pg0`, `hindsight` or `openobserve` process from the lane is left.

## Subtract, decide what is saved by class, and reshape the copies on This PC (SY1)

Design 06 sections 2, 4 (the floor, the place filter, stamps), 5 (This PC's copies), 13 (items 1, 2, 3, 5, 6 and 7) and 15 (the settings route). Rulings 106, 116, 135, 136, 137, 141 and 143. Review M1 (the filter), M2, M3, M4, M5, M11, S6, S9 (the floor), S13 and N4, N7, N9. Today a copy holds everything in `data/` but `LEFT_OUT` and `SECRET` (`BK/snapshot.py:37-80`), so no file has a class and a storage cannot be told which kinds to keep. `settings.toml` is copied whole although the harness counts it among files that may hold a key (`QH/tools.py:909-923`), and the settings writer checks only a few key names (`_no_secrets`, `QX/service.py:305-317`). This PC's copy is fixed at hourly with no off switch (`QUICK_KEEP`, `BK/plan.py:82`). Write-once files there are named `at: live` (`BK/snapshot.py:282`, `:291`), so a file removed outside QMX's writers makes the copy refuse (`BK/restore.py:644-651`). Three floors disagree (`FLOOR_BYTES`, `HM/versions.py:39`; `floor_bytes`, `HO/disk.py:55-62`; the proposal's, `BK/plan.py:320`). `PUT /api/settings/{section}` replaces the section it is sent (`QX/service.py:918`). `[remote]` has no reader but its write check (`QX/service.py:840-846`, `QR/models.py:124-142`). The weekly GitHub snapshot (`QX/backup.py`, `QX/service.py:1346-1360`, `E/templates/backup-weekly/`, `E/templates/catalog.py:397-401`) and the mini-app volume backup (`AP/backup.py:26-196`, `AP/backup_schedule.py`, `QX/service.py:26-27`, `:300-302`, `:630`, `:880`, `:1628`, `:1638`, `:1703-1705`) copy what the copies already hold. The sealed key hook waits for a PR he never asked for (`BK/round.py:40-45`, `:137`; `HO/backups.py:266-282`, `:408`). `places()` lists every placement row (`E/settings.py:56-65`) and `placement_rows` too (`E/service/forward.py:160-176`), so a storage row would read as a place to run. Done when the subtract items are gone first; `qmx_home.classes` answers `class_of(path, kind=None)` for every path relative to the QMX folder, with `content` for a path no rule names, and `secret_values(settings)` for key-named or key-shaped values; the snapshot, the round, the host's room-making list and the harness guard read it; a copy leaves out every key-shaped value of `settings.toml` by key path and lists it as a key to fill in; `[backup]` reads its new shape (`on`, `place.<id>` policies, `upkeep`) and finds its storages as `[engine]` place rows that can keep; This PC's copy has an off switch and a cadence, stages in `cache/sync-staging/` when off, and hard-links write-once files; one local floor guards every local write; the settings route merges; `GET /api/settings/backup` returns every default; and `places()` and `placement_rows` list only rows that can run. Edge cases it must survive. A path no rule names reads `content`, and a lane fills a folder through each package's writers and finds none such (M2). Every `market/` file is `prices` (M4). The Library's logs travel whole with any Library class, and a copy with a Library kind switched off still restores, naming the objects it left out (06 section 2). A mini app's `road/` is copied under the road lease, which the host hands the round as a hook because `qmx-home` cannot import `qmx-apps` (`VolumeLease(home / "road-locks", app_id)`, `AP/backup.py:135-143`); its stores are copied by `VACUUM INTO` as every SQLite file is (`BK/snapshot.py:339`, `:489`); `snapshot` and `checksum` stay for the supervisor and the road check (`AP/supervisor.py:34`, `AP/road/validation.py:14`) (M5). An old `repository` key and the old volume keys in `[backup]` are kept word for word and read by nothing, never refused. A link refused by the drive keeps `at: live` with a doctor line (M11). With This PC's copies off and no other storage, the doctor row says his work has no copy anywhere. A stamp is later than the newest copy on every storage it joins and the log's last stamp (S6). A policy with no place row is ignored and removed at the next write; a keeping row with no policy reads every default (N9). `observers.json` keeps the new machine's own on a restore (N4). The 30-day hold of a pre-change copy ends when the first whole copy reaches a storage on another disk (`HELD_AFTER`, `BK/keep.py:16`).

**Depends on.** The root `78587edc`.

**Files.**

- [ ] Delete `QX/backup.py`, `QX/__main__.py` (its one command is `weekly-backup`, `QX/__main__.py:15`), `E/templates/backup-weekly/`, `AP/backup_schedule.py`, and the tests `QA/qmx-control/tests/test_weekly_backup.py`, `QA/qmx-control/tests/test_backup.py` and `QA/qmx-control/tests/test_remote.py` where they test only what is removed.
- [ ] Edit `QR/models.py` (delete `RemoteSettings`, `:124-142`; `Target` stays), `E/templates/catalog.py` (delete the `backup-weekly` row, `:397-401`), and `QX/service.py`. In it delete the imports at `:26-27`, `:44` and `:46`, `"remote"` at `:65`, the remote check at `:840-846`, `backup_weekly` at `:1346-1360`, `_volume_keys` at `:300-302` and its uses at `:880` and `:1638`, and `BackupSchedule` at `:630`, `:1628` and `:1703-1705`; make `_no_secrets` (`:305-317`) read its names from `qmx_home.classes`; make the REST `PUT /api/settings/{section}` merge the keys it is sent into the stored section and remove only the dotted keys its body names in `remove` (replacing `settings[section] = values`, `:918`), while `settings_update` (`:782-790`) keeps its read-change-write; make `settings_get("backup")` (`:751`) return the parsed plan with every default.
- [ ] Edit `AP/backup.py` (delete `BackupSettings`, `_rclone`, `backup()`, `restore()` and the rest of the module once `snapshot` and `checksum` have moved), `AP/volume.py` (gains `snapshot` and `checksum`), `AP/supervisor.py:34` and `AP/road/validation.py:14` (import from `qmx_apps.volume`).
- [ ] Create `HM/classes.py` (standard library only) with `Class`, the table, `class_of`, `SECRET_NAMES`, `secret_values` and `PER_MACHINE`. Edit `HM/files.py` with `local_floor(settings, free) -> int`, the larger of 1 GiB and `disk.floor_gb` or a twentieth of free space; `HM/versions.py` (`FLOOR_BYTES`, `:39`, reads it) and `HO/disk.py` (`floor_bytes`, `:55-62`, calls it).
- [ ] Edit `BK/snapshot.py` (`LEFT_OUT`, `SECRET` and `WRITE_ONCE`, `:37-89`, become readers of the class table; `make` filters by the classes it is asked for, scans `settings.toml` and writes the copy's `keys_to_fill`), `BK/repository.py` (`put_pool` hard-links a write-once file into This PC's pool and falls back to `at: live`), `BK/plan.py` (the new `[backup]` shape, storages read from `[engine]` rows with `can` holding `keep` and `via = "folder"`, `APP_KEYS` at `:49` deleted, `[[backup.targets]]` no longer read, the proposal's floor at `:320` from `local_floor`), `BK/round.py` (the `sealed_keys` hook and `SEALED` deleted, `:40-45`, `:137`, `:145`; This PC's policy and staging; the road hook; `_stamp`, `:604-610`, across storages and the log) and `BK/keep.py` (the hold ends on an event, `:16`, `:57-61`).
- [ ] Edit `QH/tools.py` (`secret_files`, `:909-923`, adds `classes`' secret paths beside its own extras).
- [ ] Edit `E/settings.py` (`places`, `:56-65`, lists only rows whose `can` holds `run`, a row with no `can` reading `["run"]`) and `E/service/forward.py` (`placement_rows`, `:160-176`, the same filter).
- [ ] Edit `HO/backups.py` (the `sealed_keys` parameter deleted, `:266-282`, `:408`; `accept`, `:741-776`, writes a place row into `[engine]` through `settings_update`; `view`, `:526`, and `doctor_line`, `:644`, show This PC's policy and the no-copy line; the road-lease hook from `qmx_apps.volume.VolumeLease`) and `HO/__main__.py` (`backup` and `_copy_before_upgrade`, `:218-245`, pass the hook and `local_floor`).
- [ ] Add `QA/qmx-home/tests/test_classes.py`, `QA/qmx-home/tests/test_backup_pc_policy.py`, `QA/qmx-control/tests/test_settings_merge.py` and `QA/qmx-engine/tests/test_places_can.py`; extend `QA/qmx-home/tests/backup_fixtures.py` (`writers=True`) and edit the tests that pin removed names.

**Build.**

- [ ] Subtract first, in its own commits. Items 1, 2, 3 and 6 of 06 section 13, then the volume backup (item 7) only after the round copies `road/` under the hook, each commit followed by the touched suites.
- [ ] Reproduce first. A test fills a folder with `writers=True` and a key pasted into `settings.toml`, and fails on the parent because the copy holds that key; a second test `PUT`s one key of `[engine]` and fails on the parent because the other keys are gone.
- [ ] Add the class table, then its readers, then the settings scan, then This PC's policy, staging and links, then the one floor, then the place filter, each with its test.
- [ ] Prove the one fact. Every path the code writes has a rule. A test walks a folder filled through each package's own writers and asserts `class_of` answers from a named rule for every path, never from the default; it also asserts the union of the sent classes' paths plus the never-sent ones is the whole walk.

**You see.**

- [ ] On a throwaway folder with `filled_folder(secrets=True, writers=True)`, a round to one folder storage logs `copied` for This PC and the storage, the storage's manifest lists no path of `rebuildable`, `secret` or `scratch`, its `settings.toml` lacks the pasted key, and its header lists that key path under `keys_to_fill`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `class_of` answers every row of 06 section 2 and `content` for an unnamed path; `secret_values` finds key-named and `sk-ant-` values at any depth and nothing else; `_no_secrets` refuses the same names as before; a copy filtered to `recipe` only holds recipe paths and the Library logs; a restore of it names the objects left out and opens; This PC off stages, sends and removes the staging; both off gives the no-copy doctor line; a write-once file is linked, and a refused link keeps `at: live`; a stamp after a clock moved back is later than every storage's newest copy; the hold ends at the first whole copy on another disk; the merge `PUT` keeps every other key and `remove` drops only what it names; `GET /api/settings/backup` returns every default; `places()` and `placement_rows` skip a keep-only row and keep a row with no `can`; the preflight refusal still fires for a `serverless` row; the weekly route answers 404; old volume and `repository` keys survive a write untouched. Run the home, host, control, engine, apps and harness suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The home, host, control, engine, apps and harness suites at parent and head. Save `sy1-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A folder made with `filled_folder(secrets=True, writers=True)`, then `class_of` over every path, then a round to a folder storage in the lane folder. Save `sy1-classes.log`. Pass when every path is answered by a named rule, the storage's manifest holds exactly the paths of the four sent classes plus the Library logs, and a grep of every byte under This PC's copy and the storage finds none of the planted secrets.
- [ ] Lane 3. `settings.toml` hand-edited with a provider `api_key`, a `token` and a bare `sk-ant-` value under an innocent key, then a round, then a restore into a fresh folder. Save `sy1-settings-keys.log`. Pass when the copied `settings.toml` holds none of the three, the header lists the three key paths under `keys_to_fill`, and the restored `settings.toml` keeps every other key.
- [ ] Lane 4. `[backup.place.pc] on = false` with one folder storage, a round; then This PC on, a round; then both off with no storage, a round. Save `sy1-pc-policy.log`. Pass when the first round writes the storage's copy and none on This PC and leaves no `cache/sync-staging/`, the second writes both, and the third's doctor row says his work has no copy anywhere.
- [ ] Lane 5. A round, then one Library object file and one frozen price month removed by hand, then a restore from This PC's copy into the same folder. Save `sy1-links.log`. Pass when the restore finishes with every hash equal, and This PC's pool file for each write-once file has a link count of 2 before the removal.
- [ ] Lane 6. A mini app running under its supervisor with a writer committing to its `app.db` in a loop and a road step holding the road lease, then a round, then a handover. Save `sy1-apps.log`. Pass when the copied `app.db` passes `PRAGMA quick_check`, the round's road copy started only after the road step let the lease go, and the handover's `checksum` and `snapshot` calls succeed.
- [ ] Lane 7. A head host with `host_name`, `disk.floor_gb` and one place row in `[engine]`, then `PUT /api/settings/engine` with only one scheduler key, then one with `remove` naming the place row, then `GET /api/settings/backup`. Save `sy1-settings-merge.log`. Pass when the first keeps every key, the second removes only that row, and the `GET` names every default of Appendix D.
- [ ] Lane 8. `POST /api/backup/weekly`, `PUT /api/settings/remote` with a bucket, the template list, then a round with `disk.floor_gb` set above the lane drive's free space for This PC, a folder storage on the same drive and a store's pre-change copy. Save `sy1-subtract.log`. Pass when the route answers 404, the remote section is stored word for word, `backup-weekly` is not listed, and all three writes refuse with the same floor named.
- [ ] Lane 9. `[engine]` with a run row, a keep-only row (`via = "folder"`, `can = ["keep"]`) and a `serverless` row with `via = "modal"`, then `GET /api/places`, the forwarder's rows and a plan-login node placed on the Modal row. Save `sy1-places.log`. Pass when the keep-only row is in neither list, the run row is in both, and the plan-login node is refused with the provider line.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, a grep of every lane log for the planted secrets, then remove the throwaway folders, list processes and list `C:/QMX-backup`. Save `sy1-processes.log`. Pass when every exit code is 0, no grep matches, nothing from the lanes is left, and `C:/QMX-backup` is as it was.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for a first round of lane 2's folder to This PC and one folder storage, and seconds for a second round with nothing changed, at parent and head. Both sides write every file durably to the same kind of place, so this is the same work.
- [ ] Probe. Each round three times at each side, interleaved, on fresh lane folders and storages.
- [ ] Baseline. Record the parent's first-round median first.
- [ ] Rule. Head's first-round median is at most 1.15 times the parent's, or the PR fails. The unchanged round is under 2 s at its median at head, an absolute budget.

**Review gate.** None. SY1 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on `build/br5`.

## Connect a storage from one dialog (SY2)

Design 06 sections 3 (the PC runner), 9 (the dialog and the storage kind) and 12 (UI gap 3). Rulings 116, 135, 140, 142, 144 and 145. Review M12, M13 (the client field), S1, S2, S4, S10, S11 and his E1 answer. Today nothing connects a storage from the screen; a backup place is a `[[backup.targets]]` row he types (`BK/plan.py:64`, `:149-195`). Only the volume backup runs rclone on the PC (`AP/backup.py:42-60`), and no PC code finds, checks or fetches an rclone binary. The host's job runner runs one kind of work at a time with steps and counts (`Jobs`, `HO/jobs.py:77-133`), and a card's job is read at `/api/first-start/jobs/{id}` (router at `HO/first_start.py:996`). No route writes a key; he types the cTrader app id and secret into Credential Manager himself (UI-HANDOFF section 26 gap 3). The key store is `CredentialManager` over `keyring` (`BR/credentials.py:47-58`). Done when `HM/rclone.py` runs rclone on this PC (finds it on `PATH`, at a Settings path, or as the pinned release fetched into `cache/tools/rclone/` and checked, refuses one older than the pinned minimum, passes `--config data/rclone.conf` with `RCLONE_PASSWORD_COMMAND`, hands every secret to the one call by environment, never by argument, returns an exit result and one plain line, sorts a failure into offline, sign-in expired, full or not found, and records argument names only); `HO/connect.py` runs a connection kind as `(name, who, check, do)` steps on the job runner, rerun to resume, ending at `{needs: <card>}` for his step and writing one place row last; the storage kinds folder, Drive, R2, SFTP and any other rclone kind run, the generic one through rclone's own question loop; the Drive sign-in is its own long job with `--auth-no-open-browser`; `PUT /api/keys/{name}` writes a key and `GET /api/keys` lists only the names set; and the card's job route runs the storage kinds before any folder is served. Edge cases it must survive. A folder kind connects offline with no rclone (S10). An `IsPassword` answer reaches rclone as `RCLONE_RESULT` in that call's environment, never in its command line (measured, Appendix A); the stored conf is encrypted (M12). A card shows only `Name`, `Help`, `Examples` and `Type`; `Error` is one fixed line; an `IsPassword` question's `Default` is never shown (S1). The Drive sign-in card holds a `127.0.0.1` link and starts no browser; cancelling it stops the rclone process (S2). Until QMX ships its own Google client, the Drive card asks for the client id and secret, says it takes about ten minutes in Google Cloud, says the client must be "In production", and offers another drive or his server (S4, S3); the client id and secret are stored in the place row, because a Desktop client is public (M13). A conf whose password Credential Manager no longer holds is set aside as `rclone.conf.unreadable-<stamp>` once, each storage reads "connect again", and the runner makes no second call (S11). A folder inside the QMX folder is refused; one on the folder's own drive is kept with a warning. A rerun after a kill at any step converges on one place row (I12). The key route never reads a value back and answers 401 without the bearer. No step writes `[backup]`; a keeping row with no policy reads its defaults (SY1).

**Depends on.** The root `78587edc`. It shares no file with SY1 (Appendix C).

**Files.**

- [ ] Create `HM/rclone.py`. `Rclone(layout, *, keys, which=shutil.which, fetch=...)` with `binary()`, `version()`, `run(args, *, secrets: Mapping[str, str] = {}, answer: str | None = None) -> Ran`, `Ran(code, line, failure)`, `failure` one of `offline`, `signin`, `full`, `missing`, `other`, the masked argument record, `PINNED` (version, URL, sha256 per platform) and `MINIMUM`.
- [ ] Create `HO/connect.py`. `Step`, `Kind`, `KINDS`, `run_kind(kind, place, answer, *, report) -> Mapping`, `connect_router(connect)` with `GET /api/connect/kinds`, `POST /api/connect/jobs` (202, body `{kind, place, answer}`), `GET /api/connect/jobs/{job_id}` and `POST /api/connect/jobs/{job_id}/cancel`. The place row write goes through `control.settings_update("engine", ...)`, once, last.
- [ ] Create `HO/connect_storage.py` with the kinds `folder`, `drive`, `r2`, `sftp` and `rclone`, the question-loop step, the sign-in job and the test step (free space where reported, then a small write, read and delete under `QMX-backup/`).
- [ ] Create `HO/keys.py` with `keys_router(store)`, `PUT /api/keys/{name}` (body `{value}`, 204) and `GET /api/keys` (the names set), over `BR/credentials.CredentialManager`, never reading a value back.
- [ ] Edit `HO/host.py`. Mount `connect_router` and `keys_router` beside `backups_router` (`:813-816`), handing the storage kind a first-sync port that calls `backups.start(place_id, asked=True)` (`HO/backups.py:347`).
- [ ] Edit `HO/first_start.py`. `POST /api/first-start/connect` (body `{folder, kind, place, answer}`) runs a storage kind as a card job read at `/api/first-start/jobs/{job_id}`, writes the remote into the chosen folder's `data/rclone.conf`, and answers the `source` the restore takes.
- [ ] Add `QA/qmx-home/tests/test_rclone_runner.py`, `QA/qmx-host/tests/test_connect.py`, `QA/qmx-host/tests/test_connect_storage.py` and `QA/qmx-host/tests/test_keys_route.py`.

**Build.**

- [ ] Reproduce first. A test posts a connect job for a folder storage and gets 404 on the parent.
- [ ] Add the runner with a fake binary first, then the step runner and its rerun, then the folder kind, then the question loop, then the Drive sign-in job, R2 and SFTP, then the key route, then the card's route, each with its test.
- [ ] Prove the one fact. No secret reaches a command line. A test drives a `crypt` remote over a local folder through the question loop (a test vehicle only, never offered), answers its `password` question with a planted value through the key route, captures every rclone child's command line through `psutil` while it runs, and asserts the planted value is in none of them, in no job line and in no log, while `rclone config show` for that remote holds it in the encrypted conf.

**You see.**

- [ ] A head host on a throwaway folder answers `POST /api/connect/jobs` for kind `folder` with a path in the lane folder with 202, the job ends `finished` with one line per step, `[engine]` gains one row with `via = "folder"` and `can = ["keep"]`, and the job's last step names the first sync it started.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The runner finds rclone on `PATH`, at a Settings path and in `cache/tools/rclone/`, fetches the pinned release from a loopback server and refuses a wrong hash, refuses an rclone below the minimum, never puts a secret in `args`, records names only, and sorts a fake rclone's exit codes and JSON log lines into the five failures; a kind's rerun skips every passing check; a kill after each step converges on one row; the folder kind refuses a folder inside the QMX folder and warns for the same drive; a card carries only the four parsed fields; the Drive kind ends at its sign-in card with a `127.0.0.1` link; the key route writes, lists names and never answers a value; an unreadable conf is set aside once. Run the home and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The home and host suites at parent and head. Save `sy2-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. `GET /api/connect/kinds`, then a folder storage connected through `POST /api/connect/jobs` on a head host with `rclone` removed from `PATH`. Save `sy2-folder.log`. Pass when the kinds list names folder, Drive, R2, SFTP and another rclone kind with what each can do, the job ends `finished` with no rclone call, `settings.toml` was written once for the row, the test step left nothing under `QMX-backup/`, and the first-sync port was called with the place id.
- [ ] Lane 3. An rclone kind of type `local` and the `crypt` test vehicle driven through the question loop, its password answered through the key route with a planted value. Save `sy2-loop.log`. Pass when both rows are written, each card holds only `Name`, `Help`, `Examples` and `Type`, and the planted value is in no captured command line, job line, log line or answer.
- [ ] Lane 4. The Drive kind on a head host with no account. Save `sy2-drive.log`. Pass when the job stops at the client card, and with a fake client id given it starts the sign-in job whose card holds a `http://127.0.0.1:53682/` link, no browser process is a child of the host, cancelling stops the rclone process, and no place row is written.
- [ ] Lane 5. A folder storage job with the host killed after the test step, then a new host and the same job again. Save `sy2-rerun.log`. Pass when the second job's lines name every passing step as skipped and `[engine]` holds one row for the place.
- [ ] Lane 6. `PUT /api/keys/qmx/ctrader-client-id` and `PUT /api/keys/qmx/r2-lane`, then `GET /api/keys`, then each route without the bearer. Save `sy2-keys.log`. Pass when both answer 204, the list holds both names and no value, the fake store holds both, and every call without the bearer answers 401.
- [ ] Lane 7. No rclone on `PATH` or in Settings, with a loopback server offering a fake release, once with the pinned hash and once with a wrong one, then a fake rclone that reports a version below the minimum. Save `sy2-fetch.log`. Pass when the first lands in `cache/tools/rclone/` and runs, the second is refused naming the hash, and the third is refused naming the minimum.
- [ ] Lane 8. The first-start card on a scratch profile with no folder, `POST /api/first-start/connect` for an rclone `local` storage into a chosen folder. Save `sy2-card.log`. Pass when the card job ends `finished` with a `source` naming that remote, the chosen folder's `data/rclone.conf` holds it encrypted, and no host was started.
- [ ] Lane 9. A folder with an encrypted conf whose password is in the fake store, opened with an empty fake store, then a connect job. Save `sy2-unreadable.log`. Pass when the conf is set aside as `rclone.conf.unreadable-<stamp>`, each storage row reads "connect again" with one line, the runner made exactly one rclone call, and the new job connects with a new conf.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, a grep of every lane log and capture for the planted secrets, then remove the throwaway folders and list processes. Save `sy2-processes.log`. Pass when every exit code is 0, no grep matches, and no `rclone` or host process from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from `serve` to the first 200 on `/api/health` at parent and head; seconds for lane 2's folder connect job up to the first-sync step at head; `/api/health`'s slowest call during lane 3's loop at head. The parent has no connect job, so the job and the health budget are absolute.
- [ ] Probe. Three host starts at each side, interleaved, then lane 2's job three times and lane 3's loop once with health polled every 200 ms.
- [ ] Baseline. Record the parent's median start first.
- [ ] Rule. Head's start is within 5 % of the parent's median, or the PR fails. The folder connect job is under 5 s at its median, and every health call during the loop answers in under 1 s, both absolute budgets.

**Review gate.** None. SY2 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Joined onto SY1 by a merge commit on `build/sy2` (the two share no file); its PR base becomes `build/sy1`.
- [ ] Wave 1 join lane at the merge commit. A folder storage connected through `POST /api/connect/jobs` gets its first copy from the round SY1 reshaped, filtered by its default policy. Save `evidence/sy-w1/join.log`. Pass when the job ends `finished`, the storage holds a whole copy of the four sent classes, and `GET /api/places` does not list the storage.

## Pack, compress and send copies through rclone, with the monthly upkeep (SY3)

Design 06 sections 3 (the seam, packs, indexes, the format), 4 (the safety window and the guard read again), 5 (one send per storage, torn manifests), 6 (re-pack and check), 8 (a storage as a source) and 14. Rulings 106, 136, 137 and 140. Review M8, M9, M10, S5, S7, S8, S9, S15, S16 and N3. Today every storage is a folder of loose pool files named by sha256 (`FolderRepository`, `BK/repository.py:258`), nothing is compressed (06 `inv:` section 3), and the format string is `qmx-backup/1` (`BK/repository.py:42`). The sweep deletes any pool file no manifest names at once (`BK/repository.py:372-385`) and stops for good while one manifest is torn (`:373-378`), and `clean` removes only folders with no manifest (`:391-404`). The fork guard checks before it acts (`BK/round.py:443-466`). The drill deletes a damaged pool file (`BK/restore.py:1066`, `BK/repository.py:370-371`). One round sends to every target in turn on one job (`_round`, `BK/round.py:187`; `Backups.start`, `HO/backups.py:347`). The factory that builds a repository knows only folders (`repository_of` and `source_of`, `BK/plan.py:256-283`), and nine sites build a `FolderRepository` themselves (`BK/round.py:173`, `:203`, `:305`, `:619`; `BK/snapshot.py:183`; `HO/backups.py:434`, `:971`, `:1028`, `:1046`); the restore's `_key` falls back to `where` for any other adapter (`BK/restore.py:1151-1158`). The monthly drill runs per target (`_drill_if_due`, `HO/backups.py:953`). Done when one `open_storage(place, layout)` builds a `FolderRepository` or an `RcloneRepository` by `via` for every site; both adapters hold packs (one zstd frame per file with its checksum, about 16 MiB per pack, Parquet, PDF and images stored raw) behind the built `Repository` protocol, with an index file per confirmed batch, a bad list and manifests marked `qmx-backup/2`, while reading `qmx-backup/1` loose pools as before; This PC's mutable files are packed and its write-once files stay linked; a round writes This PC's copy, then starts one send job per due storage from that pinned copy; a send reads the newest manifest again before writing its own and writes none when another machine wrote since; prune and re-pack never delete a pack younger than the safety window; dropping a copy removes only its manifest; the monthly upkeep per storage re-packs, checks a twelfth of the packs and drills; and a restore, the drill and the check fetch one pack at a time into `cache/sync-fetch/` and report `done` of `total`. Edge cases it must survive. A killed send leaves every arrived pack named by a batch index, and the next send uploads none of them again (M10). Two hosts on one `home_id` running rounds and a re-pack at once never leave a manifest that names a deleted pack (M8). A re-pack killed after any step leaves every index naming only packs that exist and every pack a kept copy uses named (M9). A slow storage never holds This PC's copy, the drill or a restore (S5). A damaged pack's files go on the bad list, the next round packs them again, and the next re-pack drops the pack (S7). An index without its trailer is skipped with an incident and rebuilt; a torn manifest older than the newest whole copy is removed by `clean` with an incident (S7, S8). Staging and fetched packs count against the one local floor and are emptied at start (S9). A storage at its floor refuses before writing with one incident naming its biggest class; `RCLONE_MAX_TRANSFER` cut off mid send leaves no manifest and the next send converges. An offline storage reads "not reached" and a sign-in expired reads "sign in again", each tried at its next due round while This PC goes on. A folder storage on a drive pulled mid send leaves no copy and converges when it is back. Every adapter gives a stable place key from the place id (S16). An older QMX refuses a packed copy by its format line (S15). No `rclone sync` or `bisync` is ever run (I6).

**Depends on.** SY1 (the class table, the place rows read by `BK/plan.py`, This PC's policy) and SY2 (`HM/rclone.py`).

**Files.**

- [ ] Edit `BK/repository.py`. Packs, batch indexes, the merged index, the bad list and `FORMAT` `qmx-backup/2` inside `FolderRepository`, loose `qmx-backup/1` pools still read; a new `RcloneRepository(runner, remote, root)` that writes only with `rclone copy`, checks arrivals with `lsf`, deletes only through `sweep` and `repack`, and fetches one pack at a time; `sweep` honours the safety window; `clean` removes a torn manifest older than the newest whole copy; `place_key` from the place id.
- [ ] Edit `BK/plan.py`. `repository_of` and `source_of` (`:256-283`) become `open_storage(place, layout)` and `source_of(document, layout)` for `via` `folder` and `rclone`.
- [ ] Edit `BK/round.py`. `_round` (`:187`) writes This PC's copy and returns the pinned stamp; a new `send(layout, plan, place_id, stamp, *, progress)` sends one storage, reads the guard again before the manifest, and writes batch indexes; `carry_on` (`:170-184`), `_send` (`:291`), `_target_key` (`:618-619`) and `place_key` (`:613-615`) go through `open_storage`; dropping a copy removes only its manifest.
- [ ] Create `BK/upkeep.py` with `repack(repo, kept, *, past, per_run, safety, now)`, `check(repo, *, slice, month)` and their reports.
- [ ] Edit `BK/restore.py`. Read `qmx-backup/2` (`:503-508`), fetch packs one at a time under the floor, `progress(step, done=, total=)` in bytes then in files, `_key` (`:1151-1158`) from the place key, and the drill (`:1055-1066`) writing the bad list instead of `discard`.
- [ ] Edit `HO/backups.py`. `start` (`:347`) runs This PC's copy as one job and each due storage's `send` as its own job, one job per storage at a time and 409 for a second; the monthly upkeep per storage beside `_drill_if_due` (`:953`); `_repository` (`:1044-1047`) and the quick sites (`:434`, `:971`, `:1028`) through `open_storage`; incidents for a full storage, sign-in expired, a torn index and a damaged pack.
- [ ] Add `QA/qmx-home/tests/test_backup_packs.py`, `QA/qmx-home/tests/test_backup_rclone.py`, `QA/qmx-home/tests/test_backup_upkeep.py`, `QA/qmx-home/tests/test_backup_two_writers.py` and `QA/qmx-host/tests/test_backups_sends.py`, with a folder adapter slow-down seam in `QA/qmx-home/tests/backup_fixtures.py`.

**Build.**

- [ ] Reproduce first. A test kills a send after half its packs arrived and fails on the parent because the next round sends them again; a second test runs two writers on one `home_id` and fails on the parent because a manifest names a deleted pool file.
- [ ] Add packs and the format in `FolderRepository`, then batch indexes, then `open_storage` and every call site, then `RcloneRepository`, then one send per storage, then the safety window and the guard read again, then the upkeep, then the restore's reads and counts, each with its test.
- [ ] Prove the one fact. No kept copy ever names a pack that is gone. A test runs two writers and a re-pack on one storage in threads with random kill points for 200 iterations, and after each iteration restores every manifest on the storage and asserts every hash.

**You see.**

- [ ] A round of lane 2's folder to an rclone `local` storage leaves `QMX-backup/<home_id>/packs/`, `index/` and `snapshots/<stamp>/manifest.jsonl` whose header says `qmx-backup/2`, and a restore of that copy into a fresh folder matches every hash and row count.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A pack round-trips every file with its zstd checksum and stores Parquet raw; a loose `qmx-backup/1` pool still restores; a batch index is written after each confirmed batch and a killed send's packs are reused; the guard read again refuses a second writer before its manifest; no pack younger than the safety window is swept; dropping a copy keeps its index; the re-pack's order holds at every kill point; the check names a flipped byte and writes the bad list; `pool_has` reads the bad list; a torn index is skipped and a torn manifest older than the newest copy is cleaned; a fetch holds one pack at a time and staging is emptied at start; the rclone adapter never calls `sync` and checks arrivals with `lsf`; a full storage refuses before writing; a second send to one storage answers 409 while This PC's copy runs; restore counts move in bytes then files. Run the home and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The home and host suites at parent and head. Save `sy3-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A first round of `filled_folder(secrets=True, writers=True)` to a folder storage, then a restore into a fresh folder. Save `sy3-packs.log`. Pass when the manifest says `qmx-backup/2`, every pooled file is in a pack, every index has its trailer, every restored hash and row count matches, and the storage's bytes are below the parent's for the same folder.
- [ ] Lane 3. The same to an rclone `local` storage named in the lane's conf with a planted token. Save `sy3-rclone.log`. Pass when the copy restores hash-equal, every arrival was checked with `lsf`, no line from rclone reached a job line or log, and the planted token is nowhere on the storage or in a log.
- [ ] Lane 4. Two host processes on one `home_id` and one folder storage, each running rounds and one a re-pack, started together twenty times. Save `sy3-two-writers.log`. Pass when every manifest left restores hash-equal, every refused writer wrote no manifest, and no pack younger than the safety window was deleted.
- [ ] Lane 5. A send slowed by the folder seam and one slowed by `RCLONE_BWLIMIT`, each killed halfway, then a new host and a round. Save `sy3-killed.log`. Pass when the second send uploads no pack a batch index already names, and every kept copy restores hash-equal.
- [ ] Lane 6. A re-pack killed after each of its four steps in turn, then a re-pack run whole. Save `sy3-repack.log`. Pass when after each kill every index names only packs that exist, every kept copy restores, and the whole run leaves packs under 5 % unused.
- [ ] Lane 7. One byte flipped in one pack, then the check, a restore of a copy that needs it, a round and a re-pack; then one index and one manifest truncated, then a round and a re-pack. Save `sy3-damage.log`. Pass when the check names the pack and writes the bad list with one incident, the restore stops naming the file, the round packs it again, the re-pack drops the damaged pack, the torn index is skipped with an incident and rebuilt, and the torn manifest is removed with an incident while the sweep runs.
- [ ] Lane 8. A folder storage on `subst Q:` pulled mid send and put back, a storage folder deleted between rounds, and the remote removed from the lane's conf. Save `sy3-disappear.log`. Pass when the pulled send leaves no copy and the next converges, the deleted folder makes the guard refuse until carry on and then a whole copy is sent, and the removed remote reads "not reached, connect it again" while This PC goes on.
- [ ] Lane 9. One storage slowed to 30 s per pack; during its send This PC's round, a drill and fifty health calls; then an rclone `sftp` remote at `127.0.0.1` on a closed port, a fake rclone answering sign-in expired, a storage floor above its free space, and `RCLONE_MAX_TRANSFER=1M` with hard cutoff. Save `sy3-slow-offline-full.log`. Pass when This PC's round and the drill finish during the slow send with every health call under 1 s, the closed port reads `skipped` for that storage only, the sign-in line names the sign-in, the floor refuses before any file is written with the biggest class named, and the cut-off send leaves no manifest and the next converges.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, a grep of every lane log and storage for the planted secrets, then remove the throwaway folders, `subst Q: /d`, and list processes. Save `sy3-processes.log`. Pass when every exit code is 0, no grep matches, no `Q:` is left, and no `rclone` or host process from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for a first round of lane 2's folder to a folder storage and for a restore of that copy into a fresh folder, at parent (loose pool) and head (packs); seconds for an unchanged round at head; seconds for lane 3's first round to an rclone `local` storage at head; bytes on each storage. Both sides write every file durably, so the folder rounds and restores are the same work.
- [ ] Probe. Each folder round and restore three times at each side, interleaved, on fresh storages; the unchanged round and lane 3's round three times at head.
- [ ] Baseline. Record the parent's first-round and restore medians first.
- [ ] Rule. Head's first round and its restore are each at most 1.5 times the parent's median and under 90 s, or the PR fails. The unchanged round is under 2 s and the rclone `local` round under 180 s at their medians, absolute budgets. Head's storage bytes are below the parent's, with the ratio recorded.

**Review gate.** None. SY3 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the wave 1 tip.

## Connect compute and deep logs (SY4)

Design 06 sections 9 (compute kinds and deep-logs kinds) and 12 (UI gaps 6 and 7). Rulings 117, 123, 126, 135, 139, 140, 142, 144 and 145, and his words on OpenObserve (`words:219`). Review M1 (the row's fields). Today a server is set up only by `qmx node setup` from a terminal (`setup_steps`, `QX/node.py:616-652`; `setup`, `:654`), the status ladder has no caller (`placement_state`, `E/triggers/preflight.py:231`), and a placement row needs `kind`, `attempt_cpus` and `attempt_timeout` to read configured (`NEEDS`, `:225`). Telemetry is configured from `[telemetry] send_to` (`E/telemetry.py:550`, read by the host at `HO/host.py:573`), and `PUT /api/settings/telemetry` stores any value (gap 6). No OpenObserve runs on This PC (gap 7). Done when the connect dialog of SY2 also runs a server kind (his cards for choose and pay, the address, a Tailscale one-off key, the server password typed in the terminal QMX opens and the firewall step; then the setup sequence as checked steps, one place row with `via = "ssh"`, `kind = "owned"`, `can = ["run", "keep"]` and the fields `NEEDS` names, the status ladder read through `placement_state`, a one-node smoke test on the server's own engine, and `qmx-recover status` read back in plain words), a key-compute kind for Modal and E2B (his key card, one provider test call, a row with its provider `kind` and `can = ["run"]`), and the deep-logs kinds (on this PC, OpenObserve from its pinned release in `cache/openobserve/`, checked, run under the host on the loopback with `ZO_TELEMETRY=false`, a 1 GB disk cache and 30 days kept, both editable, its root password in Credential Manager and an agent login for its MCP door; on a server, the shipped unit files as the server kind's monitoring step; on every other machine, an OpenTelemetry Collector with an on-disk queue); and `PUT /api/settings/telemetry` refuses a `send_to` that is not `off`, `this-pc` or a place name. Edge cases it must survive. No server step is part of a first start (R142). A rerun after any step converges on one row (I12). The server password is typed by him in a terminal QMX opens and never passes through QMX; the Tailscale key and a Modal or E2B key go through the key route and reach their tool by environment. A Modal or E2B row still meets the refusal that keeps his plan login off provider machines (`E/triggers/preflight.py:256`, `:283-290`). OpenObserve's data lives in `cache/` and is `rebuildable`, never sent. A per-user OpenObserve that needs admin shows one approval card. A host stopped with deep logs on leaves no OpenObserve process. `send_to` set to a place that cannot run is refused.

**Depends on.** SY2 (`HO/connect.py`, `HO/keys.py`, `HM/rclone.py`) and SY1 (the place rows read by `can`). It shares no file with SY3 (Appendix C).

**Files.**

- [ ] Create `HO/connect_compute.py` with the kinds `server`, `modal` and `e2b`, their cards, the setup steps through a `Shell` port (real over SSH, fake in tests), the ladder step and the smoke step.
- [ ] Create `HO/connect_logs.py` with the kinds `deep-logs-pc`, `deep-logs-server` and `collector`, the pinned OpenObserve release (version, URL, sha256), its fetch and check, its settings, its agent login, and `OpenObserveProcess` that the host starts and stops.
- [ ] Edit `HO/connect.py` (`KINDS` gains the five kinds) and `HO/host.py` (start `OpenObserveProcess` when `send_to` is `this-pc`, near the telemetry read at `:573`, and stop it with the other tasks).
- [ ] Edit `QX/node.py`. `setup_steps` (`:616-652`) returns named steps each with its check, so the server kind and `qmx node setup` (`:654`) run the same list.
- [ ] Edit `QX/service.py`. `_settings_put` (`:823`) checks `[telemetry] send_to` against `off`, `this-pc` and the place names that can run, and answers 400 naming the value.
- [ ] Add `QA/qmx-host/tests/test_connect_compute.py`, `QA/qmx-host/tests/test_connect_logs.py`, `QA/qmx-control/tests/test_telemetry_section.py` and edit `QA/qmx-control/tests/test_node_setup.py` where `setup_steps` changed shape.

**Build.**

- [ ] Reproduce first. A test `PUT`s `send_to = "banana"` and gets 200 on the parent; a second posts a connect job for kind `server` and gets an unknown kind.
- [ ] Split `setup_steps` into checked steps with `qmx node setup` unchanged in what it runs, then the server kind against the fake shell, then the key-compute kinds, then the telemetry check, then deep logs on this PC, on a server and the collector, each with its test.
- [ ] Prove the one fact. The server kind and `qmx node setup` run one list. A test records the scripts both send to the fake shell and asserts the two lists are equal, and that a rerun after a kill at each step sends only the steps whose check failed.

**You see.**

- [ ] On a head host with the fake shell, a server connect job stops at each of his five cards in order, then runs the setup steps, then writes one `[engine]` row with `via = "ssh"`, `kind = "owned"` and `can = ["run", "keep"]`, and the job's last lines read the ladder as `healthy` and the recovery status in plain words.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. 

- [ ] `setup_steps` and the server kind send one list; each card appears once and a rerun skips what passed; the row carries the fields `NEEDS` names; the ladder reads every rung; a Modal row's provider kind meets the plan-login refusal; a Modal and an E2B test call against a loopback stub pass and a bad key fails with one line; `send_to` refuses an unknown value and a keep-only place; the OpenObserve settings bind the loopback with telemetry off and the cache and retention defaults; a binary that needs admin gives one approval card; the collector config carries an on-disk queue. Run the host and control suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The host, control and engine suites at parent and head. Save `sy4-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A server connect job on a head host with the fake shell, answered card by card, then killed after the third setup step and run again. Save `sy4-server.log`. Pass when the cards came in order, the second run sent only the steps not yet passed, one row was written with the three fields, and the ladder read `healthy`.
- [ ] Lane 3. The smoke step against a second throwaway engine on the loopback standing in for the server's, and the recovery step against the fake shell's `qmx-recover status`. Save `sy4-smoke.log`. Pass when a one-node workflow ran on the second engine and its run is read back, and the recovery line is plain words with no shell text.
- [ ] Lane 4. `send_to = "this-pc"` on a head host with the pinned OpenObserve binary from `D:/Tools/openobserve/` (or the fake binary when Arm logged none), data under the lane folder, then one span sent, then the host stopped. Save `sy4-deep-logs-pc.log`. Pass when OpenObserve answers its health on `127.0.0.1` only, the span is found by its search route, its root password is in the fake store and in no log, and no OpenObserve process is left after the stop.
- [ ] Lane 5. `PUT /api/settings/telemetry` with `banana`, a keep-only place, `off`, `this-pc` and a run place. Save `sy4-telemetry.log`. Pass when the first two answer 400 naming the value and the other three answer 200.
- [ ] Lane 6. Modal and E2B connect jobs with keys through the key route and a loopback stub for each provider, then a plan-login node placed on the Modal row. Save `sy4-key-compute.log`. Pass when each row carries its provider kind and `can = ["run"]`, each key is in no command line or log, and the plan-login node is refused with the provider line.
- [ ] Lane 7. The deep-logs server kind as a step after lane 2's server, and the collector kind for This PC sending to that place. Save `sy4-deep-logs-server.log`. Pass when the fake shell received the shipped unit files, and the collector's config names the place and an on-disk queue under `cache/`.
- [ ] Lane 8. Deep logs on this PC with a fake binary that exits with access denied. Save `sy4-admin.log`. Pass when the job ends at one approval card naming why, and nothing is left running.
- [ ] Lane 9. A first start on a scratch profile with the card, then the offer read. Save `sy4-first-start.log`. Pass when no compute or deep-logs kind is offered on the card and `GET /api/connect/kinds` on the host lists all of them.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, a grep of every lane log for the planted secrets and the fake keys, then remove the throwaway folders and list processes. Save `sy4-processes.log`. Pass when every exit code is 0, no grep matches, and no `openobserve`, `otelcol`, engine or host process from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from `serve` to the first 200 on `/api/health` with `send_to = "off"` at parent and head; seconds from `send_to = "this-pc"` to OpenObserve's health answering at head; seconds for lane 2's QMX steps against the fake shell at head. The parent has neither kind, so those two are absolute.
- [ ] Probe. Three host starts at each side, interleaved, then lane 4's start three times and lane 2's steps three times at head.
- [ ] Baseline. Record the parent's median start first.
- [ ] Rule. Head's start with deep logs off is within 5 % of the parent's median, or the PR fails. OpenObserve answers within 30 s of the setting with the real binary, and the server kind's QMX steps take under 5 s against the fake shell, both absolute budgets. With only the fake binary, the 30 s budget is recorded as unproven in Appendix A.

**Review gate.** None. SY4 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Joined onto SY3 by a merge commit on `build/sy4` (the two share no file); its PR base becomes `build/sy3`.
- [ ] Wave 2 join lane at the merge commit. Lane 2's server row, connected through the fake shell, is listed as a storage that keeps, and a send to an rclone `local` storage runs beside a server connect job. Save `evidence/sy-w2/join.log`. Pass when both jobs end `finished`, `GET /api/places` lists the server and not the storage, and the storage's copy restores hash-equal.

## Install and first start, sync before update, restore from a storage, and the folded UI gaps (SY5)

Design 06 sections 6 (the maintenance list and its event), 7, 8, 10 and 12 (gaps 1, 4, 5 and 8). Rulings 136, 139, 140, 141, 142, 144 and 145. Review M13 (the restore card's client), S12 and N6. Today the card offers new, open, bring-in and restore from a folder (`offer`, `HO/first_start.py:354-414`), and a failed restore into a non-default folder is not offered again by a fresh card (PR 228 review low 1). `serve` takes one local `before-upgrade` copy before a store upgrades (`_copy_before_upgrade`, `HO/__main__.py:143`, `:218-245`), and each store's own `pre-*` copy is kept besides (`HM/versions.py:235-302`). A restore from Settings takes a target id (`stage_restore`, `HO/backups.py:812`), and its progress counts stay at 0 (06 section 8). After a restore the copy's place rows name remotes the new PC's conf lacks. `GET /api/inbox` lists no backup incidents (`inbox_list`, `QX/service.py:1944`), the run read carries no `placement` (`runs_get`, `QX/service.py:1801`), and nothing says a store opened read-only until a write is refused (`/api/health`, `QX/server.py:458`). No list tells QMX's own maintenance from his workflows. Done when the card offers "Restore from my storage" (connect the storage through SY2's card route, pick a copy by machine, time and counts, see what it replaces, restore with steps and counts, hand over, keys to fill in, carry on) and, for a new folder, the line "Your work is kept on this PC" with one optional card "Keep your work in another storage too" that runs the storage kind and the first sync; a fresh card offers again a failed restore into any folder; after a restore the row of the storage it came from replaces the copy's row for that storage and every other storage reads "connect again"; `GET /api/backups/keys-to-fill` lists the key names the copy needs and each one written through the key route leaves the list; `sync_now(why)` sends to every storage that is on and waits `before_update_wait`; `serve`'s store upgrade calls it first and falls back to the local `before-upgrade` copy with one line; a store's `pre-*` copy is released once a `before-upgrade` copy of the same moment exists; Settings' restore takes any storage; `GET /api/maintenance` lists the host's jobs and the shipped workflows marked `meta.kind = "maintenance"`, each with its own off switch, and each host job ends with an event a workflow can trigger on; `GET /api/inbox` lists every open incident; the run read carries `placement`; and `/api/health` names a store opened read-only. Edge cases it must survive. A restore never writes into a folder a host serves. With only This PC on, `sync_now` copies to This PC alone and the update goes on. A storage that does not answer within the wait falls back to the local copy in `serve` and never stops the start (I1). A restore from Drive when QMX ships no client asks for the same client id and says where it is (M13). A restored storage row matched by `via` and where it points replaces the old row only for that storage (S12). A key-to-fill list never holds a value. Turning off a maintenance item stops it and nothing else. The card offers nothing about deep logs, servers or GPUs (06 section 10). UI gaps 1, 3 and 5 ride along through the closed ticket, and the coordinator tells him so in one line (N6).

**Depends on.** SY3 (storages as sources, the send jobs, progress counts) and SY4 (the wave 2 tip). It runs alone in wave 3.

**Files.**

- [ ] Edit `HO/first_start.py`. `offer` (`:354-414`) gains `restore-storage` and the keep-your-work card, and offers a failed restore into any folder again; the restore route takes a storage `source` from `POST /api/first-start/connect`; after `finish` the source storage's row is merged into the restored `[engine]`.
- [ ] Edit `HO/__main__.py`. `_copy_before_upgrade` (`:218-245`) calls `sync_now(why="before-update")` first, then the local copy, with one line on a fallback.
- [ ] Edit `HO/backups.py`. `sync_now(why, *, wait)`, `stage_restore` (`:812`) for any storage, `GET /api/backups/keys-to-fill`, the row merge after carry-on (`carry_on_restore`, `:898`), and the end event of each host job.
- [ ] Create `HO/maintenance.py` with `maintenance_router` and `GET /api/maintenance`; mount it in `HO/host.py` beside `backups_router` (`:815`).
- [ ] Edit `HM/versions.py` (`snapshot`, `:235-302`, releases a store's `pre-*` copy once a `before-upgrade` copy of the same moment exists).
- [ ] Edit `QX/service.py` (`inbox_list`, `:1944`, lists open incidents; `runs_get`, `:1801`, carries `placement` from the run's Library object) and `QX/server.py` (`/api/health`, `:458`, names a store opened read-only).
- [ ] Edit `E/templates/connections-health/definition.json` and `E/templates/gw-guard-watchdogs/definition.json` to carry `meta.kind = "maintenance"`, outside the content hash (`Meta` keeps any other key, `E/definition/model.py:207-212`).
- [ ] Add `QA/qmx-host/tests/test_card_restore_storage.py`, `QA/qmx-host/tests/test_sync_before_update.py`, `QA/qmx-host/tests/test_maintenance.py` and `QA/qmx-control/tests/test_inbox_incidents.py`.

**Build.**

- [ ] Reproduce first. A test asks the card's offer for a scratch profile with a storage source and finds no `restore-storage`; a second runs `serve` on a folder that needs an upgrade with an rclone `local` storage on and finds no copy on the storage.
- [ ] Add `sync_now` and the update order, then the card's restore from a storage and its row merge, then keys to fill in, then the keep-your-work card, then the maintenance list and its event, then the inbox, run read and health changes, each with its test.
- [ ] Prove the one fact. An update never waits on a cloud it cannot reach. A test runs `serve` on a folder that needs an upgrade with one storage behind a fake runner that never answers, sets the wait to 2 s, and asserts the store upgraded, the local `before-upgrade` copy exists, the line names the storage, and the start took under 2 s plus the parent's start.

**You see.**

- [ ] On a second scratch profile, the card lists `restore-storage`, connects an rclone `local` storage, lists its copies with machine, time and counts, restores one with moving counts, hands over, and the host's `GET /api/backups` shows that storage connected with its next copy due, while `GET /api/backups/keys-to-fill` lists the copy's key names.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The offer holds `restore-storage` and the keep-your-work card for a new folder and nothing about compute; a failed restore is offered again; the row merge matches by `via` and where it points and touches no other row; keys to fill list names only and shrink as keys are written; `sync_now` with only This PC copies once, with a storage sends there first, and falls back after the wait; a `pre-*` copy is released only when a `before-upgrade` copy of the same moment exists; Settings' restore takes an rclone storage; the maintenance list names host jobs and marked workflows, each switchable; a host job's end event fires a trigger; the inbox lists open incidents; the run read has `placement`; health names a read-only store. Run the host, home, control and engine suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The host, home, control and engine suites at parent and head. Save `sy5-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A first folder with an rclone `local` storage and two copies on it; then a second scratch profile with no folder restores the newer copy through the card, hands over, starts a host, writes one key from the list and runs a round. Save `sy5-new-pc.log`. Pass when the copies list machine, time and counts, the check shows what the copy replaces, the counts move in bytes then files, the host reads that storage connected and its round sends there, every other storage row reads "connect again", and the key list shrinks by one.
- [ ] Lane 3. A folder whose ledger is one version behind this release with an rclone `local` storage on, then `serve`; then the storage's remote broken and the same again on a fresh copy of the folder. Save `sy5-before-update.log`. Pass when the first sends a copy tagged `before-update` to the storage before the upgrade and releases the store's `pre-*` copy, and the second upgrades with one fallback line naming the storage and a local `before-upgrade` copy.
- [ ] Lane 4. A restore from Settings with an rclone storage as the source, cancelled before the next start, then staged again and finished by a restart, then carry on. Save `sy5-settings-restore.log`. Pass when the cancel leaves no staging, the restart finishes with every hash equal, the job's counts were not 0, and sync and fires resume only after carry on.
- [ ] Lane 5. A first start on a scratch profile choosing a new folder, then the keep-your-work card with a folder storage, then a second profile that skips the card. Save `sy5-first-start.log`. Pass when the first shows "Your work is kept on this PC", the card's job ends with a first copy on the storage, the second holds only This PC's copy, and neither offer names deep logs, a server or a GPU.
- [ ] Lane 6. A card restore into a non-default folder killed mid stage, then a fresh card. Save `sy5-offered-again.log`. Pass when the fresh card offers that folder's restore again.
- [ ] Lane 7. A full storage, then `GET /api/inbox`, `GET /api/maintenance`, the upkeep switched off, and a test workflow triggered on a host job's end event. Save `sy5-maintenance.log`. Pass when the inbox lists the storage's incident, the list names the host's jobs and the marked workflows each with its switch, the upkeep does not run while off, and the test workflow ran once after the job ended.
- [ ] Lane 8. A run placed on a fake second place, then its read; a Library opened read-only, then `/api/health`. Save `sy5-run-place-health.log`. Pass when the run read carries `placement` and health names the read-only store before any write.
- [ ] Lane 9. A restore of the first folder's copy on a second folder that then keeps syncing beside the first. Save `sy5-two-pcs.log`. Pass when the second writer is refused by name with the first's machine and folder, carry on lets it send, and every manifest on the storage restores hash-equal.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, a grep of every lane log, card answer and storage for the planted secrets, then remove the throwaway folders and list processes. Save `sy5-processes.log`. Pass when every exit code is 0, no grep matches, and nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for `serve` to answer `/api/health` on a folder that needs an upgrade with only This PC on, at parent and head (one `before-upgrade` copy each, the same work); seconds `sync_now` adds with an rclone `local` storage on at head; seconds for lane 2's card restore end to end at head.
- [ ] Probe. Three starts at each side, interleaved, on fresh copies of the folder, then the storage start and lane 2's restore three times each at head.
- [ ] Baseline. Record the parent's median start first.
- [ ] Rule. Head's start with only This PC is within 10 % of the parent's median, or the PR fails. `sync_now` with the storage adds under 60 s, and the card restore ends under 120 s, both absolute budgets on lane 2's folder.

**Review gate.** None. SY5 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the wave 2 tip.

## Close the program

- [ ] Every PR is stacked with a CLEAN verdict, or skipped with its reason in `RESUME.md`.
- [ ] Closing lanes, run by the coordinator at the stack tip on fresh throwaway folders and scratch profiles, with no PR.
  - [ ] One pass of each journey of 06 sections 7, 8, 9 and 10, in order, through the routes of Appendix E. A first start keeps his work on This PC; the keep-your-work card connects a folder storage; an rclone `local` storage connects through the dialog and gets a packed copy; a second scratch profile restores from it on the card and syncs again; `serve` on an upgrade sends first; a server kind runs against the fake shell. Save `evidence/sy-v/journeys.log`. Pass when each ends in its expected state, no planted secret is anywhere, no traceback is in any log, and `C:/QMX-backup` is as it was.
- [ ] Design 62 A3's tree, on `plan/agent-system`, gains the rows this program adds (`cache/sync-staging/`, `cache/sync-fetch/`, `cache/tools/rclone/`, `cache/openobserve/`, `data/rclone.conf.unreadable-<stamp>`, and a storage's `QMX-backup/<home_id>/` with `backup.toml`, `packs/`, `index/`, `bad/` and `snapshots/`), so every file has its documented home (ruling 143).
- [ ] `UI-HANDOFF.md` gains the sync, storage, maintenance and deep-logs section the coordinator owns (06 section 12), with the routes of Appendix E and every default of Appendix D.
- [ ] `RESUME.md` names his remaining steps (Appendix H) and that UI gaps 1, 3 and 5 rode along.
- [ ] `just ci` at the stack tip exits 0, or every failure is a named environmental gap.
- [ ] The landing list. `stack-list.md` gains five rows in landing order, SY1, SY2 (with its wave 1 merge commit), SY3, SY4 (with its wave 2 merge commit) and SY5, each with its PR link, head and patch-id. The coordinator sends him the whole list to his phone and stops. He lands the stack himself.
- [ ] `QUEUE.md` moves on to its next item.

## Appendix A. Prototype evidence

- Probes run on 2026-10-28 by the planner, from the scratchpad, with the `bld-br5` venv's Python (`-I -B`) and `D:/Tools/rclone` v1.75.2, on a throwaway config. Nothing of QMX was started, and no account, Credential Manager entry or browser was touched.
  - Python 3.14.6 in the venv has `compression.zstd`. A 300,000-byte text compressed with `checksum_flag` on came back equal (51 bytes). SY3's packs rest on this.
  - rclone's question loop for a `crypt` remote (`config create ... --non-interactive --all`, then `config update ... --continue --state ...`) asks `filename_encryption`, `directory_name_encryption`, `password` (`IsPassword` true), `password2` and `config_fs_advanced`. Answering `password` with `RCLONE_RESULT` in that call's environment and no `--result` argument stored the planted value, the same as passing `--result` on the command line. So an answer reaches rclone with nothing in its command line. SY2's M12 fix rests on this. rclone stored that answer unobscured in the conf, so the conf's encryption is what protects it, and the runner passes `--obscure` (the builder checks that the two together store an obscured value).
- Facts read in the code at `78587edc`, each with its line in the PR that uses it. The class sources (`BK/snapshot.py`, `HM/stores.py`, `AP/volume.py`, `QH/chat.py`, `QH/home.py`, `QH/tools.py`). The placement fields (`E/triggers/preflight.py`, `E/service/forward.py`, `E/settings.py`). The settings writers (`QX/service.py:782-790`, `:800-803`, `:918`) and the heartbeat's merge (`HO/host.py:1024-1038`). The volume backup's imports and leases (`AP/backup.py`, `AP/supervisor.py`, `AP/road/validation.py`). The server runners (`QX/node.py`, `QA/qmx-hub/src/qmx_hub/bucket.py`). The sweep, clean, guard and stamp (`BK/repository.py`, `BK/round.py`). The repository sites and factory (`BK/plan.py`, `BK/round.py`, `BK/snapshot.py`, `HO/backups.py`, `BK/restore.py`). The old installer's builder (`tools/build_release.py`, `tools/tests/test_runtime_wheel_closure.py`). The key store (`BR/credentials.py`). The routes (`HO/first_start.py`, `HO/host.py`, `QX/service.py`, `QX/server.py`).
- PR 229's fix round is the base, and its evidence holds. Lanes 2 to 4 pass at `78587edc` (`wrapup/evidence/br5/lanes-fix.log`), including "no fire ran before carry-on" and `[engine]` keeping every key beside the pause; the recheck is CLEAN (`wrapup/review/br5-check-78587edc.md`).
- Facts the builders prove by running code (each PR's Build block). Every path the writers make has a rule (SY1). No secret reaches a command line (SY2). No kept copy names a gone pack under two writers and kills (SY3). The server kind and `qmx node setup` send one list (SY4). An update never waits on an unreachable cloud (SY5).
- Unproven until the program or his steps run. That the Library opens a folder whose refs name objects a switched-off class left out (SY1's first check). That OpenObserve runs per-user on Windows without admin, and starts within 30 s (SY4, with the binary Arm fetches). That rclone behaves against Drive, R2 and an SFTP server as it does with `local` (no real account in any lane). That a Google client registered once sees its copies from a new PC and another client does not (06 section 8; his step on a throwaway Google account, Appendix H).

## Appendix B. Not in this program

- Logged to `BACKLOG.md` at program start. The sealed key copy (planned PR 7); he never asked for it. "Make this a new home" (review N5, in no ticket). Restore one mini app, undo a restore, and remove a set-aside folder on his click. Finding a folder storage that came back under another drive letter by its `backup.toml`. Sizes from his real folder, and anything they would call for (append-only run results, chunking, a dictionary, spreading over accounts). Encryption that needs no memory. Exporting OpenObserve dashboards and alert rules. A per-series "can be downloaded again" mark for prices.
- Kept as built, outside this program. The old bundle installer and its builder (`release/install.py`, `release/launcher.py`, `tools/build_release.py:207-208`, `:255-256`) until the desktop session replaces them (review M6). The node rebuild's runner and the Hub's runner on the server (review M7). The trading node's backup and its monitoring stack. QMF's backup block. The Hub's bucket push and Litestream. The second-drive proposal, now a suggestion inside the dialog.
- Other sessions' work. The desktop installer and updater themselves (they call this program's routes, Appendix E). Engine dispatch of PC-started work to a named place. Broker reads over REST (UI gap 2). The attach route and `@file` (UI gap 9). Every UI screen (the UI session reads Appendix E and the UI notes).

## Appendix C. Files two PRs share

| Pair | Shared file | Order |
|---|---|---|
| SY1, SY2 | none (SY1 is `BK/`, `HM/classes.py`, `HM/files.py`, `HM/versions.py`, `HO/backups.py`, `HO/__main__.py`, `HO/disk.py`, `QX/service.py`, `QX/backup.py`, `QX/__main__.py`, `QR/models.py`, `AP/`, `QH/tools.py`, `E/settings.py`, `E/service/forward.py`, `E/templates/`; SY2 is `HM/rclone.py`, `HO/connect.py`, `HO/connect_storage.py`, `HO/keys.py`, `HO/host.py`, `HO/first_start.py`) | wave 1, side by side |
| SY1, SY3 | `BK/repository.py`, `BK/plan.py`, `BK/round.py`, `BK/snapshot.py` (SY3 reads only), `HO/backups.py` | SY1 first |
| SY2, SY3 | `HM/rclone.py` (SY3 calls it, never edits it) | SY2 first |
| SY3, SY4 | none (SY3 is `BK/`, `HO/backups.py`; SY4 is `HO/connect_compute.py`, `HO/connect_logs.py`, `HO/connect.py`, `HO/host.py`, `QX/node.py`, `QX/service.py`) | wave 2, side by side |
| SY2, SY4 | `HO/connect.py` (SY4 adds kinds to `KINDS`), `HO/host.py` | SY2 first |
| SY1, SY4 | `QX/service.py` (SY1 the subtract and the merge route, SY4 the telemetry check) | SY1 first |
| SY2, SY5 | `HO/first_start.py`, `HO/host.py` | SY2 first |
| SY3, SY5 | `HO/backups.py`, `BK/restore.py` (SY5 reads only) | SY3 first |
| SY1, SY5 | `HO/__main__.py`, `HM/versions.py`, `QX/service.py`, `E/templates/` | SY1 first |
| SY4, SY5 | `HO/host.py`, `QX/service.py` | SY4 first |

## Appendix D. Defaults

Each is Claude's default, with its reason. He can overrule any of them, and each lives in `settings.toml` where Settings edits it and the `GET` returns it.

- The settings shape. `[backup]` keeps its code name; the screen says "Sync to my storage".

```toml
[engine.placement.usb]             # a folder storage he connected (SY2) or accepted (SY1)
id = "01J..."                      # stable, so a rename keeps its history
via = "folder"                     # folder | rclone | ssh | modal | e2b
can = ["keep"]                     # a storage writes no kind; a server writes kind = "owned"
path = 'E:\'                       # copies go to <path>\QMX-backup\<home_id>\

[engine.placement.gdrive]
id = "01J..."
via = "rclone"
can = ["keep"]
remote = "qmx-01J..."              # its remote in data/rclone.conf, which never travels
client_id = "...apps.googleusercontent.com"   # Drive only; public, so it travels

[backup]
on = true                          # "Sync to my storage"; off pauses every storage, deletes nothing

[backup.place.pc]                  # This PC, "Copies on this PC", always the first row
on = true
save = ["recipe", "content", "result", "prices"]
every = "1h"                       # when something changed
keep = { hours = 48, days = 7 }

[backup.place.01J...]              # any other storage; absent means these defaults
save = ["recipe", "content", "result", "prices"]
every = "1d"                       # when something changed; any cadence down to hourly
at = "03:00"                       # local time; a PC that was off syncs at its next start
keep = { days = 14, weeks = 8, months = 12 }
floor = "auto"                     # the larger of 2 GB and a tenth, where the kind reports free space

[backup.upkeep]                    # QMX's own maintenance, per storage, This PC included
on = true
every = "1mo"
repack_past = 0.05
repack_per_run = "all"
safety = "24h"
check_slice = 12
drill = true
before_update_wait = "10m"

[telemetry]
send_to = "off"                    # off | this-pc | a place that can run

[telemetry.openobserve]            # on this PC
cache_gb = 1
keep_days = 30
```

- The local floor is the larger of 1 GiB and `disk.floor_gb`, or a twentieth of the free space when that is unset. It covers This PC's copies, a folder storage on any local drive, `cache/sync-staging/` and `cache/sync-fetch/`. It protects his drive and is not a cap.
- A pack closes at about 16 MiB or at the end of a send; a larger file has a pack of its own. Each file is one zstd frame at the library's default level with its checksum. Parquet, PDF and images are stored raw. The pack size is internal and never a setting.
- The safety window is 24 hours and two rounds of this home, whichever is later. A pack younger than it is never deleted.
- A send to a storage that refused is tried at its next due round. After seven missed rounds the incident says so. Retry is not a setting.
- The pinned rclone is v1.75.2 (the version on his PC, `D:/Tools/rclone`), and the minimum is the same until a build needs a newer one. The pinned OpenObserve is the version Arm fetches.
- Keys are named under `qmx/` in Credential Manager. The rclone conf's own password is `qmx/rclone-config`, made on first use, never typed by him.
- The first-start card's choices are new, open, bring in, restore from my storage and restore from a folder, then for a new folder one optional card, "Keep your work in another storage too". Deep logs, compute and GPUs come later from Settings or the copilot.

## Appendix E. The sync and connect contract (reference)

The UI agent, the copilot and the desktop app follow this contract. Every host route sits behind the bearer; the card's routes answer on the loopback with no bearer, as today.

| Step | The caller runs | It reads | Then |
|---|---|---|---|
| Install | the desktop installer's steps (06 section 10) | `python -m qmx_host first-start --serve` answering | the card |
| First start | `GET /api/first-start` | `choices` with `restore-storage`, and the keep-your-work card for a new folder | his choice |
| Restore from my storage | `POST /api/first-start/connect`, then `POST /api/first-start/copies`, `/restore/check`, `/restore` | a `source`, the copies, the counts, a finished job | the handover, then `GET /api/backups/keys-to-fill` |
| Connect | `GET /api/connect/kinds`, `POST /api/connect/jobs`, `GET /api/connect/jobs/{job_id}` | `needs` with a card, or `finished` with the place | his card, then the same `POST` again |
| A key | `PUT /api/keys/{name}` | 204 | `GET /api/keys` lists the name |
| Update | `sync_now` inside `serve`, and the desktop updater's call when it exists | one line on a fallback | the upgrade goes on |

- The host's routes. `GET /api/connect/kinds` (each kind with its id, name, `can` and whether it needs rclone). `POST /api/connect/jobs` (202 with a job; body `{kind, place, answer}`, where `answer` is `{state, result}` for a question card, `{key}` naming a key written through the key route for a secret card, or `{fields}` for any other card). `GET /api/connect/jobs/{job_id}` (`step`, `done`, `total`, `needs` with the card's fields, link or approval). `POST /api/connect/jobs/{job_id}/cancel`. `PUT /api/keys/{name}` (body `{value}`). `GET /api/keys`. `GET /api/backups/keys-to-fill`. `GET /api/maintenance`. The routes of `BACKUP-RESTORE-PLAN.md` Appendix E stay, with `target` meaning a place id.
- The card's routes. `POST /api/first-start/connect` (body `{folder, kind, place, answer}`, read at `/api/first-start/jobs/{job_id}`, ending with a `source`). A `source` is `{kind: "folder", path}` or `{kind: "rclone", remote, path}` with the folder's own conf.
- The settings route. `PUT /api/settings/{section}` merges the keys it is sent; `remove` lists dotted keys to delete. `GET /api/settings/{section}` returns every value with its default. `PUT /api/settings/telemetry` refuses a `send_to` that is not `off`, `this-pc` or a place that can run.
- The reads. `GET /api/inbox` lists open incidents. `GET /api/workflow-runs/{run_id}` carries `placement`. `/api/health` names a store opened read-only.
- A refusal answers 409 with `detail`, its one line; a bad body answers 400; no answer echoes a key, a token or an answer to a secret card.

## Appendix F. Words

- **Sync to my storage.** The one switch. QMX sending his saved set to his storages as dated copies.
- **Storage.** A place that keeps copies. The first row is always This PC ("Copies on this PC").
- **Machines.** The places that can run, beside Storage.
- **Saved set.** The four classes that are sent, recipes, his content, run results and prices that can't be downloaded again.
- **Copy.** One dated manifest of his saved set in one storage. Never a mirror.
- **Pack.** Many files in one compressed file on a storage. He never sees the word.
- **Restore.** Rebuilding `data/` from one copy he confirmed.
- **Keys to fill in.** The key names a restored copy needs, typed again through the key route. Keys never travel.
- **Maintenance.** QMX's own jobs and marked workflows, listed apart from his workflows, each with its off switch.
- **Connect.** The step-by-step dialog, the same for the screen and the copilot.
- **Deep logs.** The monitoring viewer, OpenObserve.
- **Server link.** The Library's link with a server. On the screen "sync" never means this.

## Appendix G. Alternatives weighed

- Five PRs, against the coordinator's expected five in a different cut. His expected cut was subtract first; the class table and This PC; packs and rclone; one connect dialog; install, update and the gaps. Subtract and the class table share `QX/service.py`, `BK/round.py`, `BK/plan.py` and `HO/backups.py`, so as two PRs they could only run one after the other, and the subtraction's own reason (the volume backup goes only after the road-lease copy exists) ties them. So they are one PR, SY1, with the removals as its first commits. The connect dialog's compute and deep-logs kinds share no file with packs, and its storage kind shares none with SY1, so the dialog is cut into its storage half (SY2, beside SY1) and its compute half (SY4, beside SY3). The count stays five, and the waves become three instead of five.
- One connect PR for every kind. Rejected. It would serialize behind packs, and its storage half is what SY3's rclone adapter needs first.
- rclone's remote-control server (`rclone rcd`) for the question loop, so no answer is ever a command-line argument. Rejected. Its access is all or nothing and it can read back every stored credential (`research/sync/sources/rclone-rc.md:31-44`); `RCLONE_RESULT` in one call's environment does the same job with no server (Appendix A).
- A lock between machines on one storage. Rejected. Each home writes only its own folder, and the safety window plus the guard read again before the manifest keep two writers on one `home_id` safe (principle separate-before-serializing-shared-state).
- Keeping `at: live` on This PC. Rejected for the files a hard link can keep, because a file removed outside QMX would leave no undo; kept only where the drive refuses links.
- Sending a pool file whole beside packs on cloud storages. Rejected. Packs cut the file count the storage and rclone must list, and one format for every storage keeps one restore.
- Splitting `[backup]` policies into `[engine]` rows. Rejected. One row write per connect keeps a crash between two writes harmless, and a policy by place id keeps the run registry free of sync keys.

Choices where the review offered options, each with why.

- M5. Keep `snapshot` and `checksum` in `volume.py` and hand the round a road-lease hook, rather than teach `qmx-home` the apps' lease, because `qmx-home` is the leaf the apps package builds on.
- M6. Keep the old installer, rather than reshape its builder here, because the desktop session owns the builder.
- M8. A safety window and a second guard read, rather than kopia's full epoch scheme, because each home writes only its own folder and the window covers the one shared case.
- M12. The environment for every secret, with the generic loop's `IsPassword` answers through `RCLONE_RESULT`, rather than refusing the generic loop, because the probe shows it works.
- M13. The client id in the place row and a card that asks for it, rather than a QMX client shipped now, because registering QMX's client is his step (Appendix H).
- S13. A merging `PUT` with a named `remove`, rather than a version check, because the rule is that no settings write replaces a section.

## Appendix H. Gates and calls

- G-LAND. He lands the stack himself, from the landing list in Close the program.
- His steps, none of which blocks a builder. Registering QMX's own Google "Desktop app" client once and setting it to "In production", after which the program ships its id and Drive becomes one click. Proving Drive on a new PC with a throwaway Google account he signs in to. Typing his server's password in the terminal QMX opens, and approving the firewall step, when he connects a server.
- Coordinator calls, made without him. Fetching the pinned OpenObserve release once (Arm). Telling him in one line that UI gaps 1, 3 and 5 ride along (review N6).
- No call needs him. No PR touches money, his vocabulary or irreversible scope. The words are 06 section 11's, which he chose (E3). Nothing is deleted from his data; every removal is code or plan text.
