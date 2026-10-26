# QMX local first, phase 1 build program

This program builds phase 1 of `research/methodology/62-local-first-design.md` (section G, with the guards of section L), so the first real start happens on his PC with no server.
It carries out rulings 136 to 145, which say the PC is home, his data lives in one folder of its own, setup is local first, no messy files, and a server is an optional extra.
There are 8 PRs. Seven are LF5, LF1, LF2, LF3, LF4, LF6 and LF7 of design 62, and one is WU11 from `WRAPUP-PLAN.md`, the price door that opens by default.
The stack roots on `origin/engine/base` at `d82be318`, where the wrap-up stack (PRs 198 to 206) landed on 2026-10-26.
Code truth for every Files block is design 62 sections A to G and the walk `62a-local-first-rubric-walk.md`, read at `d7391716`, equal to `d82be318` apart from merges.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a test run, or a SHA. The body is a how-to. The appendices explain and record.

Each PR section opens with a preamble naming its design 62 piece, the rulings it serves, its real step and its done line. Then come the nine blocks `check-plan.mjs` requires.

Path shorthands are those of `DATA-PLAN.md` "How to read this". `QA/` is `qmx-agents/packages/`, `E/` the engine source, `T/` its templates, `H/` the harness source, `HO/` the host source, `QX/` the control source, `LB/` the Library, `HB/` the Hub, `R/` the router, `BR/` the broker, `TL/` the tools, `RM/` the remote worker, `AP/` the apps, `MM/` the memory source. Test folders are each package's `tests/`.

The store is `D:/QMX-worktrees/qma-ship/wrapup/` (the same one the wrap-up used), with `decisions.md`, `BRIEF-BUILDER.md`, `RESUME.md`, `BACKLOG.md`, `lows.md`, `ledger.tsv`, `dispatch/`, `review/` and `evidence/`.

The program follows `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md` with the same overrides as `WRAPUP-PLAN.md`. Builders are Claude Opus 5.5 (`poteto-agent`, `model: opus`), at most two at once, never two on shared files, never two agents on one job. A fresh Opus reviewer agent reviews every diff and runs `bmad-review-edge-case-hunter` on any PR that touches data, sync, the vault or connections; the coordinator runs the full suites, `just ci` and the lanes in the background and allows one fix round. Low findings go to `lows.md`; anything new goes to `BACKLOG.md`. See `playbooks/` in the poteto-mode skill for the rest.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] Confirm the shell (Windows 11, PowerShell 7.6 and Git Bash) and the root (`git rev-parse origin/engine/base` is `d82be318`). Logged in `RESUME.md`.
- [ ] Read the trunk rules with `git show origin/main:CLAUDE.md`, then the rulings file `research/methodology/26-operator-rulings-and-alignment.md` (rulings 136 to 145 drive this), then design 62 sections A to G and L.
- [ ] No hourly `/loop 1h` tick, because builder and background-job notifications wake the coordinator. Post a short status message to the operator only when a PR opens, a verdict lands or a blocker appears.
- [ ] Never stop to ask him during the build. A question goes to `D:/QMX-worktrees/qma-ship/data/QUESTIONS-FOR-OPERATOR.md` and the build goes on. Only his intent, money or irreversible scope is his.

### Spawn owners

| # | Id | Chain | PR | Runs beside | Proving check |
|---|---|---|---|---|---|
| 1 | LF5 | foundation | No server in the defaults | WU11 | a chat's launch has no telemetry address when sending is off |
| 2 | WU11 | data | The price door opens by default | LF5 | a 1996 read with no holdout answers rows |
| 3 | LF1 | foundation | One resolver | LF6 | every entry point finds the same folder |
| 4 | LF6 | data | Places he names | LF1 | a trigger homed on a named place |
| 5 | LF2 | foundation | The folder tree | LF7 | a scratch boot writes nothing outside the folder |
| 6 | LF7 | data | cTrader homed on This PC | LF2 | a demo sign-in lane with no server |
| 7 | LF3 | foundation | Versions | none | a newer store opens or refuses by name |
| 8 | LF4 | foundation | Bringing in the old data | none | the old folder is unchanged after the switch |

- [ ] Spawn one fresh Opus builder per PR in the background with `subagent_type: poteto-agent` and `model: opus`, from a dispatch file saved in `dispatch/`. Its first words are exactly "Read the poteto-mode skill's SKILL.md in full, including its Principles section, before any work. Do not spawn sub-agents."
- [ ] Record the empty Files intersection of each parallel pair in `ledger.tsv` before the second dispatch (Appendix C).
- [ ] No PR touches `apps/qmx-ui/`, `~/.claude`, his real home `~/.qmx`, `C:/Users/Mubarak/Documents`, `C:/Users/Mubarak/Desktop/DATA_NARL`, or any vault value. Lanes run on throwaway folders and a scratch profile only.

### PR mechanics, for every PR

- [ ] The coordinator creates `build/<id>` from the right parent in `D:/QMX-worktrees/bld-<id>` before the dispatch. Never `git stash`.
- [ ] The builder opens the PR ready with `gh pr create --base <parent-branch> --head build/<id> --repo MubarakHimself/QMX`.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Set `TMP` and `TEMP` to `D:/Temp` and `UV_CACHE_DIR` to `D:/Caches/uv`.
- [ ] The builder runs `fmt-check`, `lint` and `types` in each package it touched and `tools/secret_scan.py`, reads each exit code, runs only the fast tests it added or changed, and never waits on a long command. It runs the `blast-radius` skill on its diff before the last push and reads the `codebase-design` skill first where a seam moves.
- [ ] Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. PR bodies end with the Claude Code line.

### Verdict and merge, for every PR (append to the stack, merge on his go)

- [ ] At the code-ready head the coordinator runs the touched suites with `-n 2` and lanes 1 to 4 in the background and saves their logs. A fresh Opus reviewer agent (one per PR, `model: opus`, told not to spawn sub-agents) reads the PR section, the full diff, the edge-case lens where the PR touches data, sync, the vault or connections, and those logs, and writes `review/<id>-check-<head8>.md`, first line CLEAN or NOT CLEAN. The coordinator does not review diffs (his word, 2026-10-26).
- [ ] Blockers go back to the same builder for one fix round. Low findings go to `lows.md`.
- [ ] `ledger.tsv` gets head, parent and patch-id.
- [ ] `just ci` runs at the stack tip once both chains meet and once at the end, with `D:/Tools/rclone` on `PATH`, under `D:/QMX-worktrees/.ci-lock`.
- [ ] Stacks join with merge commits, never a rebase, so each verdict stands. He lands the stack himself from the list the coordinator sends; nobody else merges.

### Boot recipe, for every live lane

- [ ] `git worktree add --detach D:/Temp/<id>-check <head>`, then `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`.
- [ ] A lane runs on a throwaway QMX folder under `D:/QMX-worktrees/qma-ship/wrapup/homes/<id>-<lane>/`. A lane that checks for stray files points `USERPROFILE`, `APPDATA`, `LOCALAPPDATA` and `HOME` at a scratch profile under the same folder.
- [ ] A lane with a model uses the ship home's plan login on haiku, holding `D:/QMX-worktrees/.engine-lane-lock`.
- [ ] Never name a PowerShell variable `$home`. Save captures as `evidence/<id>/check-<slug>.log`, then remove the check copy with `git worktree remove` and confirm no `qmx_host`, `claude` or `node` process from the lane is left.

## Stop sending monitoring to the server, and no server in the defaults (LF5)

Design 62 LF5 and section L guard 3 (it lands first). Rulings 136, 140, 142. Today every chat, the engine's exporter and Hindsight's tracing fall back to the server's public address, and several defaults name the server. Real step none. Done when a host started with no settings opens no connection to any address that is not a model provider, telemetry is off until `[telemetry] send_to` names a target, and every default names This PC.

**Depends on.** The root `d82be318`.

**Files.**

- [ ] Edit the three telemetry sites, `H/launch.py` (lines about 404 to 414 and 562), `E/telemetry.py` (about line 49) and `MM/hindsight.py` (about lines 63 and 227), reading one `[telemetry] send_to` setting (`off` by default).
- [ ] Edit `QX/node.py` (the vault machine default near line 177), `RM/models.py` (the `vps` bucket, root and target defaults near lines 103, 123 and 124), `HB/server.py` (the standalone Hub's `primary` default near line 969) and `QX/node-bootstrap.sh` (the `primary = "server"` line).
- [ ] Edit the three downloaders under `T/download-dukascopy/`, `T/download-binance/` and `T/download-ccxt/` (`[data] root` defaults to the folder's `market`, placement defaults to the host's place) and the comment in `QX/lab.py` near line 17.
- [ ] Add tests in the harness, engine, memory, remote and Hub packages, and one grep test in `tools/tests/` that finds no IP address literal in production code.

**Build.**

- [ ] Remove the server address from code and add `[telemetry] send_to` (`off`, `this-pc`, or a place name), so a chat gets telemetry variables only from that setting.
- [ ] Change every default above to This PC or to none.
- [ ] Add the grep guard.

**You see.**

- [ ] On a fresh throwaway folder the host starts and runs one chat, and no connection to `155.133.27.86` or any address but the model provider's is attempted.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A chat's launch environment has no OTLP variable with `send_to = "off"` and has one with `send_to = "this-pc"`; the grep test passes. Run the harness, engine, memory, remote, Hub and control suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The six suites at parent and head. Save `lf5-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A host on a throwaway folder runs one chat while `netstat` samples its connections. Save `lf5-connections.log`. Pass when no connection goes to the server's address.
- [ ] Lane 3. The same with `send_to = "this-pc"` and nothing listening. Save `lf5-this-pc.log`. Pass when the chat still answers and the failed sends are counted, not raised.
- [ ] Lane 4. One downloader run on a throwaway folder with no `[data] root` set. Save `lf5-download.log`. Pass when it writes under the folder's `market`.
- [ ] Lane 5. `qmx node setup --dry-run`. Save `lf5-setup.log`. Pass when no line writes `primary = "server"`.
- [ ] Lane 6. Grep the lane logs for the server address. Save `lf5-grep.log`. Pass when it appears only in the server-setup lines.
- [ ] Lane 7. Grep lane logs for key values. Save `lf5-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `lf5-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the touched packages. Save `lf5-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the throwaway folder and list processes. Save `lf5-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from host start to the first chat answer.
- [ ] Probe. Lane 2.
- [ ] Baseline. The same at the parent.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked first on the foundation chain.

## The price door opens by default (WU11)

As planned in `WRAPUP-PLAN.md` section "The price door opens by default, and a holdout is his choice per study (WU11)", with design 62 section E2's market-door lines folded in. Ruling 137. Real step none. Done as that section says, and also when a commit's `born_on` defaults to the host's own place, the `Placement` enum's "the server holds the main copy" wording is gone, and the old-ticks import defaults to the folder's `market` with no raw-backup copy.

**Depends on.** The root `d82be318`.

**Files.**

- [ ] The Files block of WRAPUP-PLAN's WU11 section.
- [ ] Also in `HO/market_data.py` lines near 106, 495 and 953 (`born_on` and the `Placement` wording) and `scripts/data/import_old_ticks.py` lines near 771 and 781 (`--market` and `--raw-backup` defaults).

**Build.**

- [ ] Build WRAPUP-PLAN's WU11 boxes, its edge cases 10 and 11 included.
- [ ] Default `born_on` to the host's place and reword the enum.
- [ ] Default the import to the folder's `market` with no raw backup.

**You see.**

- [ ] From a chat, `read_bars` for a 1996 window answers rows on a throwaway folder with an empty `[data]`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] WRAPUP-PLAN's three WU11 tests, plus one that a commit on a PC host records `born_on = pc`. Run the host, tools, control and engine suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The four suites at parent and head. Save `wu11-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A chat reads a synthetic 1996 window on a throwaway folder. Save `wu11-1996.log`. Pass when rows come back.
- [ ] Lane 3. Settings `data.holdout` on for 2025. Save `wu11-default-on.log`. Pass when a 2025 read is refused by name and a 1996 read still answers.
- [ ] Lane 4. One run asking for two different holdouts. Save `wu11-mixed.log`. Pass when the second is refused by name.
- [ ] Lane 5. A dry old-ticks import with no seal flag. Save `wu11-import.log`. Pass when it targets the folder's `market`.
- [ ] Lane 6. `PUT /api/settings/data` with a bad month. Save `wu11-settings.log`. Pass when it is refused by name.
- [ ] Lane 7. Grep lane logs for key values. Save `wu11-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `wu11-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the touched packages. Save `wu11-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the throwaway folder and list processes. Save `wu11-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds for one unsealed month read.
- [ ] Probe. Lane 2.
- [ ] Baseline. The same read through a sealed door at the parent.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. The Settings row on screen belongs to the UI session.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked first on the data chain.

## One way to find his QMX folder (LF1)

Design 62 section A2 and LF1. Rulings 141 and 143. Real step none. Done when one stdlib-only package, `qmx-home`, resolves the folder in A2's order (the `--home` flag, `QMX_HOME`, the pointer `%APPDATA%\QMX\home.toml`, A1's default if it holds `qmx-home.toml`, then each fixed drive's `QMX\qmx-home.toml`), every entry point uses it, and nothing creates a folder implicitly anywhere.

**Depends on.** LF5.

**Files.**

- [ ] Add the leaf package `QA/qmx-home/` (`resolve()`, `Layout`, `Label`, stdlib only) with its tests, and declare it in the packages that import it and in `qmx-agents/uv.lock`.
- [ ] Edit every entry point, `HO/__main__.py`, `QA/qma-harness/src/qma/console.py`, `QX/server.py` (its default home only), `TL/servers.py`, `BR/server.py`, `QX/node.py` (the `./qmx-home` defaults near lines 857, 874 and 898) and `E/__main__.py` (the temp home near line 133).
- [ ] Add one grep test in `tools/tests/` that finds no `Path.home() / ".qmx"` and no current-folder default outside `qmx-home`.

**Build.**

- [ ] Write the resolver and its `--create` rule (only an explicit create makes a folder).
- [ ] Route every entry point through it. A program that finds no folder refuses with one plain line.
- [ ] Read the `codebase-design` skill first; `qmx-home` is a new deep module with a small interface.

**You see.**

- [ ] `python -m qmx_engine templates list` with no folder anywhere answers in one line that no QMX folder was found and to start QMX once or pass `--home`, and creates nothing.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Each entry point resolves the same path with a pointer, with `QMX_HOME` and with a flag; the grep test passes. Run the home, host, harness, control, tools, broker and engine suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The suites at parent and head. Save `lf1-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. Every entry point on a scratch profile with only a pointer. Save `lf1-pointer.log`. Pass when all name the same folder.
- [ ] Lane 3. Every entry point with no pointer and no folder. Save `lf1-none.log`. Pass when each refuses in one line and no folder appears anywhere.
- [ ] Lane 4. A lost pointer with the folder on a scratch drive path. Save `lf1-scan.log`. Pass when the scan finds it.
- [ ] Lane 5. `qmx node setup --dry-run` in a scratch current folder. Save `lf1-node.log`. Pass when no `qmx-home` folder appears there.
- [ ] Lane 6. The host started with `--home` on a throwaway folder. Save `lf1-host.log`. Pass when it answers.
- [ ] Lane 7. Grep lane logs for key values. Save `lf1-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `lf1-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the touched packages and `uv lock --check`. Save `lf1-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the scratch profile and list processes. Save `lf1-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds for one resolve with the drive scan.
- [ ] Probe. Lane 4.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on LF5.

## Places he names instead of a fixed list (LF6)

Design 62 sections D2, D3 and LF6 (engine AD-72, AD-30). Ruling 140. Real step none. Done when a place he adds under any name can home a trigger and be named in `runs_on`, no `placement.contabo` row ships as a default, a host started for a server takes its place name from setup, and every run records `place`, `place_id`, `machine` and `placed_by`.

**Depends on.** WU11.

**Files.**

- [ ] Edit `E/ledger/migrations.py` (a forward step rebuilding `triggers` without the `home_engine` CHECK), `E/triggers/rows.py` (near line 37), `E/definition/validate.py` (near line 29), `E/settings.py` (the `placement.contabo.*` defaults near lines 134 to 138), `HO/host.py` (near lines 879 to 883, `--place`), and `T/run-on-a-machine/definition.json` (a `place` slot).
- [ ] Add the run fields of D3 where a node attempt and a `workflow-run` object are written, and tests in the engine and host packages.

**Build.**

- [ ] Write the ledger step and check names against the place list when writing.
- [ ] Remove the shipped server rows and the nameless-host rule.
- [ ] Record where every run ran.

**You see.**

- [ ] A run card's record says "ran on pc, by default".

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] After the step, a trigger homed on `home-server` inserts, and reads `blocked_config` when that place is removed. Run the engine and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The two suites at parent and head. Save `lf6-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A parent-built ledger opened at head. Save `lf6-migrate.log`. Pass when the step runs once and its triggers survive.
- [ ] Lane 3. A workflow run on a throwaway folder. Save `lf6-record.log`. Pass when its record carries the four place fields.
- [ ] Lane 4. A trigger on a removed place. Save `lf6-removed.log`. Pass when it reads `blocked_config` with the plain line.
- [ ] Lane 5. A fresh settings read. Save `lf6-defaults.log`. Pass when no `contabo` row appears.
- [ ] Lane 6. `run-on-a-machine` with no place set. Save `lf6-template.log`. Pass when it asks for a place by name.
- [ ] Lane 7. Grep lane logs for key values. Save `lf6-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `lf6-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the two packages. Save `lf6-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the throwaway folder and list processes. Save `lf6-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for the ledger step on a ledger of 10,000 triggers.
- [ ] Probe. Lane 2 with a generated ledger.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on WU11.

## The QMX folder's layout (LF2)

Design 62 sections A3 and A5 and LF2, with section L guard 4. Rulings 141 and 143. Real step none. Done when a fresh folder holds exactly the label and the five parts (`data`, `keys`, `backups`, `cache`, `logs`), every file A5 names lands where it says, the work zones and memory's database sit inside the folder, script children's caches go to `cache/models`, and the agent guard protects the whole folder plus `keys/`, `cache/run/` and `cache/plugins/`.

**Depends on.** LF1.

**Files.**

- [ ] Edit `H/home.py` (`QmxHome` takes the `Layout`), `H/tools.py` (the guard's homes and protected list, near lines 933 to 955), `E/workers/zones.py` (`zones_root` and `home_of`), `E/nodes/script.py` (the child cache variables), `AP/supervisor.py` (environments, images and runtime folders to `cache/`), `R/vault.py` and `QX/server.py` (`keys/`), `HO/host.py` (logs and `cache/run`), and `MM/hindsight.py` (pg0's data folder, model cache and log folder).
- [ ] Add a format 1 to 2 layout step in `QA/qmx-home/` that runs on a test home and on a server home (guard 4), and tests in each touched package.

**Build.**

- [ ] Build the tree of A3 and move every A5 row.
- [ ] Start pg0 with its data in `data/memory/hindsight/pg` and hand Hindsight its database address.
- [ ] Widen the guard and add one guard test per protected path.

**You see.**

- [ ] A throwaway folder after one chat, one recall, one script workflow and one mini app shows only the five parts and the label.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `home_of` returns the folder's `data/` from a zone; the guard refuses a shell write into `keys/`; the layout step moves a flat test home. Run the harness, engine, apps, router, control, host and memory suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The suites at parent and head. Save `lf2-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A throwaway folder on a scratch profile runs a chat, a recall, a script workflow and a mini app. Save `lf2-strays.log`. Pass when the only files outside the folder are Credential Manager entries, uv's cache and OS temp scratch.
- [ ] Lane 3. Hindsight starts on that folder. Save `lf2-memory.log`. Pass when its database is under `data/memory/hindsight/pg` and `~/.pg0` of the scratch profile stays empty.
- [ ] Lane 4. The layout step on a copy of a flat test home. Save `lf2-layout.log`. Pass when every file lands per A5 and a host opens it.
- [ ] Lane 5. A template calling `home_of`. Save `lf2-homeof.log`. Pass when it reads the ledger.
- [ ] Lane 6. Delete `cache/` with QMX closed, then start. Save `lf2-cache.log`. Pass when QMX rebuilds it and loses nothing.
- [ ] Lane 7. Grep lane logs for key values. Save `lf2-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `lf2-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the touched packages. Save `lf2-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the scratch profile and list processes. Save `lf2-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for the layout step on a home of 10,000 Library objects.
- [ ] Probe. Lane 4 with a generated home.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on LF1.

## cTrader signed in on This PC when there is no server (LF7)

Design 62 section E1 and LF7 (engine AD-67). Rulings 135, 136 and 142. Real step his cTrader demo sign-in on This PC (gate G-CT), with the coordinator walking him through it. Done when a connection's home is `pc` when he names no other, This PC exchanges the sign-in code itself and keeps the tokens in Credential Manager as `qmx/token/ctrader-app`, the refusals that need a server go, and ruling 135 holds unchanged (a sign-in whose accounts can trade live money is still refused off a trading server).

**Depends on.** LF6.

**Files.**

- [ ] Edit `HO/venue_session.py` (the home default near line 68, the refusals near lines 304 to 309 and 347, the PC token store) and the broker reads under `BR/`.
- [ ] Add tests in the host and broker packages.

**Build.**

- [ ] Home a connection on `pc` by default and run the code exchange and the venue session on This PC.
- [ ] Keep the one-home rule. Moving a home is a fresh sign-in there, after which This PC deletes its tokens.

**You see.**

- [ ] On a throwaway folder with a fake token endpoint, the sign-in completes with no server and the connection reads `ok`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A PC-homed sign-in stores the tokens once; a live-trading grant is refused; moving the home deletes the PC's tokens. Run the host and broker suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The two suites at parent and head. Save `lf7-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. WU8's sign-in lane with no server and the home `pc`, against the fake endpoint. Save `lf7-signin.log`. Pass when it completes.
- [ ] Lane 3. List where `qmx/token/ctrader-app` exists. Save `lf7-onehome.log`. Pass when exactly one store holds it.
- [ ] Lane 4. A grant marked as able to trade live money. Save `lf7-live.log`. Pass when it is refused by name.
- [ ] Lane 5. A refresh on the PC home. Save `lf7-refresh.log`. Pass when a read succeeds after it.
- [ ] Lane 6. A busy redirect port. Save `lf7-port.log`. Pass when it refuses before the browser opens.
- [ ] Lane 7. Grep lane logs and the vault document for token values. Save `lf7-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `lf7-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the two packages. Save `lf7-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Close the receiver and list processes. Save `lf7-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from the code arriving to the row reading `ok`.
- [ ] Probe. Lane 2.
- [ ] Baseline. WU8's server-homed measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** LF7 is the step he will click through.

- [ ] Post to the operator the click-by-click walk-through page from `evidence/wu8/owner-walkthrough.md`, updated for This PC, with a screenshot of each step of lane 2 and a short video of it, before his real sign-in.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on LF6.
- [ ] Real step (G-CT). After he lands the stack, the coordinator walks him through the demo sign-in on This PC, then runs the three cTrader probes.

## Versions that open, upgrade after a backup, or refuse by name (LF3)

Design 62 section B and LF3 (Library AD-35). Ruling 141. Real step none. Done when the label `qmx-home.toml` and each SQLite store's own version and `min_reader` follow B2's five rules, a store one release newer opens without losing what it added, a store too new refuses by name (the Library and price data open read-only), and a pre-change snapshot is taken before any upgrade step.

**Depends on.** LF2 and LF6 (both edit what LF3 versions; `E/ledger/migrations.py` is LF6's too).

**Files.**

- [ ] Edit `QA/qmx-home/` (`Label`, `check_open`), `E/ledger/migrations.py` (`min_reader` and rule 3), each SQLite store's opener (engine, inbox, control, runs index, apps, portfolio, Library catalog), the settings writer (unknown keys kept word for word), and add the pre-change snapshot hook.
- [ ] Add tests in the home, engine, control, Library and apps packages.

**Build.**

- [ ] Write the label and the five rules.
- [ ] Set `application_id`, `user_version` and `min_reader` on every SQLite store.
- [ ] Take the snapshot before every upgrade step.

**You see.**

- [ ] Opening a folder written by a pretend newer release says, in plain words, which version is needed.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A store one version newer opens with `min_reader` unchanged and refuses by name when it is raised; the Library opens read-only then; a settings round trip keeps an unknown section. Run the five suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The suites at parent and head. Save `lf3-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A folder upgraded one step. Save `lf3-upgrade.log`. Pass when the snapshot exists first and the store opens after.
- [ ] Lane 3. The parent's code opening the head's folder. Save `lf3-rollback.log`. Pass when it opens (one release back).
- [ ] Lane 4. A store with a raised `min_reader`. Save `lf3-refuse.log`. Pass when the refusal names the version and the Library is read-only.
- [ ] Lane 5. An index of an unknown version. Save `lf3-index.log`. Pass when it rebuilds.
- [ ] Lane 6. An upgrade step that fails. Save `lf3-failstep.log`. Pass when the store stays at the last good version with an incident.
- [ ] Lane 7. Grep lane logs for key values. Save `lf3-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `lf3-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the touched packages. Save `lf3-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the throwaway folders and list processes. Save `lf3-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds for `check_open` on a full folder.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the tip after LF2 and LF7.

## Bringing in his old data on the first start (LF4)

Design 62 section F step 4 and LF4, with section L guard 5. Rulings 141 and 142. Real step his first real start on This PC (with him). Done when the first start finds his old-layout `~/.qmx`, copies it into the new folder's `data/`, checks every hash, runs the built switch on the copy only, shows the report, never writes the old folder, refuses a folder under a live sync client, and a host refuses to start on an old-layout folder with no label.

**Depends on.** LF3.

**Files.**

- [ ] Add the first-start backend route in `HO/` (new folder, open an existing folder, restore placeholder, bring in old data), call `scripts/data/switch_library.py` on the copy, and edit `QX/library.py` (the refusal of an unlabelled old-layout folder).
- [ ] Add the sync-client check (OneDrive, Dropbox and Google Drive roots) and tests in the host and control packages and `scripts/data/`.

**Build.**

- [ ] Write the copy, hash list, switch on the copy, and the report in plain words.
- [ ] Refuse the "never" places of A1 by name.
- [ ] Leave the old folders for him to remove later from the start screen.

**You see.**

- [ ] On a synthetic old-layout folder, the first start's report lists items per kind, what was filtered and what moved.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. 

- [ ] The old folder's file list and hashes are identical before and after; a path under a OneDrive root is refused. Run the host and control suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The suites at parent and head. Save `lf4-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A synthetic old-layout folder brought in. Save `lf4-bringin.log`. Pass when the report matches and the old folder is unchanged.
- [ ] Lane 3. A host started on the unlabelled old folder. Save `lf4-refuse.log`. Pass when it refuses and names the first start.
- [ ] Lane 4. A chat on the new folder after the switch. Save `lf4-chat.log`. Pass when it finds an old item by search.
- [ ] Lane 5. A failed verification (a corrupted copy). Save `lf4-fail.log`. Pass when the new folder is left unfinished and the old one untouched.
- [ ] Lane 6. A target under a fake OneDrive root. Save `lf4-onedrive.log`. Pass when it is refused by name.
- [ ] Lane 7. Grep lane logs for key values. Save `lf4-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `lf4-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the touched packages. Save `lf4-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the throwaway folders and list processes. Save `lf4-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds to bring in a 10,000-item old folder.
- [ ] Probe. Lane 2 with a generated folder.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** LF4 is the first thing he sees on his real start.

- [ ] Post to the operator a screenshot of lane 2's report and a short video of the bring-in, with one plain sentence on what happens to his old folder.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on LF3.
- [ ] Real step. After he lands the stack, the first real start on This PC with him (design 62 section F), then the first chat, memory, templates and his old ticks.

## Close the program

- [ ] Every PR is stacked with a CLEAN verdict, or skipped with its reason in `RESUME.md`.
- [ ] `just ci` at the stack tip exits 0, or every failure is a named environmental gap.
- [ ] The stack list is sent to him; he lands it himself.
- [ ] The first real start runs with him, then the cTrader demo sign-in on This PC.
- [ ] Tell him in plain words what changed and what waits on him.

## Appendix A. Prototype evidence

- Design 62 section J, run on built code at `d7391716`, found that the new zones root passes the built guard; `home_of` returns the wrong folder for it (three templates call it); an older engine refuses any newer ledger; the ledger's CHECK refuses any place but `pc` and `contabo`.
- Walk 62a covers 29 systems, the three hard-coded telemetry sites, the five `~/.qmx` defaults and three current-folder defaults, his real `~/.qmx` still in the old layout.
- Research 62b found the Velopack and MSIX uninstall trap, OpenObserve and Hindsight run on Windows.
- The wrap-up stack landed on `engine/base` at `d82be318` on 2026-10-26.

## Appendix B. Not in this program

Phases 2 to 4 of design 62 (LF8 backup and restore, LF9 the sealed key copy, LF10 the local deep logs, LF11 optional parts, LF12 places on every screen, LF13 the add-a-server walk), the stand-in round, the UI wiring (UI session), and the backtest door (unit session).

## Appendix C. Files two PRs share

| Pair | Shared file | Order |
|---|---|---|
| LF5, LF1 | `QX/node.py`, `QX/server.py` (LF1 default home only) | LF5 first |
| LF5, LF2 | `MM/hindsight.py` | LF5 first |
| LF1, LF2, LF3 | `QA/qmx-home/` | LF1, LF2, LF3 |
| WU11, LF6, LF2 | `HO/host.py` (`market_door`, `--place`, logs) | WU11, LF6, then LF2 after the chains join |
| LF6, LF3 | `E/ledger/migrations.py` | LF6 first |

Parallel pairs and their intersections. LF5 and WU11 share none (the market-door and import lines moved into WU11). LF1 and LF6 share none. LF2 and LF7 share none. LF2 starts only after the data chain's LF6 is stacked and merged into the foundation chain, because both edit `HO/host.py`.

## Appendix D. Defaults

- No hourly tick, as in the wrap-up. Claude's default.
- rclone on `PATH` from `D:/Tools/rclone` for `just ci`. Claude's default.

## Appendix E. Gates and calls

- G-LAND. Real steps run only on code he landed.
- G-CT. His cTrader demo sign-in on This PC, after LF7 lands.
- His first real start, after LF4 lands.
