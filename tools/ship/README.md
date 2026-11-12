# ship: the scripts behind the shipping method

Agents think and write. These scripts run every check and enforce every gate, so an overnight run cannot drift from the method in `tracker/shipping-method/SHIPPING-METHOD.md`.

Standard library only, Python 3.12 or later. The scripts shell out to `git` and `gh`. Windows 11 is first-class; Linux works too.

Run any command as:

```
python tools/ship <command> --program <program folder> [arguments]
```

The program folder is the planner's handoff (`PROGRAM.yaml`, `SLICES.md`, `slices/<id>/BRIEF.md`, ...). The scripts add their run files to it.

## Commands

| Command | Reads | Writes | Exit |
|---|---|---|---|
| `init --repo R --build-branch B --worktree-root W` | `SLICES.md` | `state.json` (refuses a changed `SLICES.md` once it exists) | 0 |
| `preflight [--protection-push-test]` | `state.json`, the machine, the remote | `preflight/checks.txt`, `ARMED.md`, `main-status.txt`, `runs/`, `KEEP-AWAKE` | 0 armed, 1 refused |
| `main-check` | `main-status.txt`, the main checkout | nothing | 0 unchanged, 1 changed (stop the run) |
| `status` | `state.json`, `heartbeat/`, `HOLD`, remote slice branches | `state.json` (last push seen) | 0, 1 on STALE or breaker |
| `dispatch <id>` | `state.json`, `HOLD`, `slices/<id>/BRIEF.md`, the build tip | the worktree, `evidence/<id>/<attempt>/facts.log`, `leftover.patch`, `state.json` | 0 dispatched (JSON), 2 refused, 3 parked |
| `timed --slice <id> --log L [--timeout S] -- <argv>` | nothing | the log, `heartbeat/<id>` | the command's exit code, 124 on timeout |
| `verify_ready <id> <sha>` | `state.json`, remote, `evidence/<id>/<attempt>/` | the PR, `state.json` | 0 ready, 1 blocked |
| `slice_checks <id>` | `state.json`, `checks.toml`, the brief, head and parent, the quality baselines | `checks/<id>/<head8>/`, `state.json` | 0 green, 1 red |
| `land [<id> ...]` | `state.json`, `checks.toml`, `baseline-reds.txt`, `review/` (verdict mode only) | the build branch, `baseline-reds.txt`, `refs/ship/rebased/<id>`, `checks/_land/<batch>/`, `leftovers.md`, `state.json` | 0 all landed, 1 otherwise |
| `nightly` | `state.json`, `checks.toml`, `baseline-reds.txt` | `checks/_nightly/<tip8>/`, `baseline-reds.txt` on the first run, `state.json` | 0 green, 1 red |
| `quality --from <sha> [--tools vulture,skylos,mutmut]` | `state.json`, `checks.toml`, the quality baselines | `checks/_quality/<tip8>/` | 0 no new finding, 1 otherwise |
| `baseline [--at REF] [--tools ...] [--part K/N]` | `checks.toml`, the code at REF (default the build tip) | `<quality dir>/baseline-<tool>.tsv`, `BACKLOG.md`, `runs/` | 0, 1 when a tool did not run |
| `merged <checkpoint>` | `state.json` | `state.json` (`merged`) | 0 recorded or already, 1 refused |
| `power_watch [--once]` | the power line, the remote | `HOLD`, `power.json`, `state.json` events | 0 |
| `power` | `power.json`, `HOLD` | nothing | 0 go, 1 HOLD (wait), 2 no watcher (start one) |
| `recover [--usage-reset ISO]` | `state.json`, worktrees, remote | `evidence/<id>/<attempt>/leftover.patch`, worktrees, `state.json` | 0 |
| `park <id> --cause dispute\|manual --why TEXT` | `state.json` | `state.json` | 0 |
| `run_report` | `state.json`, `checks/` | `RUN-REPORT.md` | 0, 1 if the counts do not add up |
| `teardown` | `ARMED.md` | the machine, `ARMED.md` (keeps only what is still there) | 0 all gone, 1 otherwise |
| `hook` | hook JSON on stdin, `state.json` | nothing | 0 allow, 2 refuse |

`bisect-step` is internal: `nightly` hands it to `git bisect run`.

## How the coordinator uses them

There is no AI reviewer per slice: machine checks gate each slice, and all AI review happens in the checkpoint review session every 5 to 8 slices (`slice_verdict_required` turns the old per-slice verdict back on).

1. Once per run: `init`, then `preflight`. Fix every FAIL line it prints and run it again. It arms nothing until every check passes. Start `power_watch` in the background.
2. On every wake and every 600-second tick: `recover` if the session just started, then `main-check` and `status`. Stop on `MAIN CHANGED` or `BREAKER`. A `STALE` slice gets `recover`, then `dispatch` again (a restart).
3. Fill free seats: `dispatch <id>` for each slice in `status`'s "could start" list, then its `PREBUILD` list. Exit 2 means refused (the reason is printed); exit 3 means parked.
4. A builder replies `READY <sha>`: `verify_ready <id> <sha>`. Exit 1 is BLOCKED; send a fix round with `dispatch <id>`.
5. After ready: `slice_checks <id>`. Red sends a fix round with the summary. Green goes to `land`.
6. `land` (every checked slice of the open checkpoint) or `land <ids>`. `HELD` names pre-built slices that wait for the open checkpoint to merge. `RECHECK <id>` means the rebase changed the slice: run `slice_checks <id>` again (it checks the rebased commit), then `land`.
7. `status` prints `CHECKPOINT <X> built` when every slice of the open checkpoint is landed, parked or blocked-by: the checkpoint review starts. It runs `nightly` and `quality --from <checkpoint start>` (Windows, the whole suite), merges, and records `merged <X>`, after which the pre-built slices land.
8. End of run: `run_report`, then `teardown`. Add only a "Waits on you" section under the report.

### Checkpoints and pre-building

A slice's checkpoint is SLICES.md's `stop` column (`checkpoint` is read too); with neither, the program is one checkpoint. The open checkpoint is the first, in table order, not recorded by `merged`. A slice of the next checkpoint may be dispatched before then (pre-built), but only when its files overlap no slice of the open checkpoint, which is building or in review and may get a fix batch. Two checkpoints ahead is refused. A pre-built slice passes its checks and waits in `checked`; `land` holds it until `merged <open>`.

### Quality ratchet

Skylos, Vulture and mutmut run through `quality.py`. Only a NEW finding blocks. A finding is keyed by tool, file and the tool's words (never the line), and is known when it is in the baseline file or, for Vulture and Skylos, already at the commit the work started from. Every baseline finding is a row in `BACKLOG.md` for a later fixer and never blocks, so no agent loops on old findings.

- Per slice, in `slice_checks`: Vulture and Skylos over each touched package at the head and the parent; only findings in the slice's changed files count. Both tools are fast.
- Per checkpoint, `quality --from <sha>`: the same at the build tip against `<sha>`, plus mutmut on every function holding a changed line (mutmut 3 mutates whole functions, so that is its finest grain).
- `baseline` once (it is not taken yet), then mutmut in parts on a schedule: `baseline --tools mutmut --part K/N` replaces only that part's rows. Rows keep their first-seen date; a rerun at the same commit changes nothing.

The quality folder is the `quality_dir` setting, by default `<worktree_root>/ship-quality`, shared by every program. Only `baseline` writes the baseline files, so one program's fixes never make another program's old findings look new.

## Formats

### SLICES.md

The first markdown table with these columns, in any order:

```
| id | name | ask | stop | lane | depends on | files | size |
|---|---|---|---|---|---|---|---|
| rc-35 | Exit ladder | S2 | A | L1 | rc-34 | qmx/risk/exits.py, qmx/risk/tests/ | M |
```

`id`, `name`, `depends on`, `files` and `size` are required. `ask` (the SCOPE.md ask, checked against the PR's `TRACE:` line) and `stop` (the checkpoint) are read when present; `lane` and any other column are ignored. `depends on` is a comma list or `-`. `files` is a comma list of paths, folders (`dir/` or `dir/**`) and globs (`*`, `?`, `**`). Two slices overlap when one pattern can name a file of the other, compared case-insensitively. Globs compare by their literal prefix, which over-reports on purpose.

### Brief facts

Each fact in `BRIEF.md` is a fenced block. The first line is `$ ` and the command; the rest is the exact expected output. Add `exit=N` when the command's exit code is not 0. The safety fact uses the id `SAFETY`.

````
```fact F1
$ git grep -c "def size_position" -- qmx/risk/sizing.py
qmx/risk/sizing.py:1
```

```fact SAFETY exit=1
$ git grep -n "keyring" -- qmx/risk
```
````

The command is split like a POSIX shell line and run without a shell, so pipes and redirections do not work; use `python -c` for anything longer. Write paths with forward slashes. Output is compared after CRLF becomes LF, trailing spaces leave each line, and trailing blank lines leave the end. `dispatch` runs the facts in the new worktree at the build tip on a slice's first attempt only (`facts.log`, the SAFETY fact included); a fix round's worktree holds the builder's changes, so the facts would no longer describe the tip. `slice_checks` reruns the SAFETY fact at the head.

### Evidence and the PR body

Every evidence file a script accepts ends with the line `END <full 40-character sha> <dispatch id>`. The dispatch id comes from `dispatch`'s JSON. `verify_ready` requires `how.md`, `red.log`, `report.md` and `pr.md` (the `evidence_required` setting) in `evidence/<id>/<attempt>/`.

`pr.md` is the PR body the builder writes from its brief's section 11, in PR body v2's shape. It must hold the line `TRACE: <slice id> -> <plan ids> -> <ask>`, ending in the slice's `ask` when SLICES.md gives one. Neither it nor any commit message of the slice may carry a credit line (`Co-Authored-By:`, `Generated with`). The PR is opened from `pr.md` with the END line removed.

### Verdicts (only with `slice_verdict_required`)

A review verdict is `review/<id>-<head8>.md`. It holds the line `VERDICT: CLEAN` to pass, and ends with the END line for the head it reviewed. A range verdict after a landing rebase is `review/<id>-range-<patchid8>.md`, with the same two lines; `land` prints its exact path.

### checks.toml

```toml
[[package]]
root = "qmx-agents/packages/qmx-control"
setup = ["uv", "sync", "--frozen"]
lint = ["uv", "run", "--no-sync", "ruff", "check", "."]
types = ["uv", "run", "--no-sync", "pyright"]
test = ["uv", "run", "--no-sync", "python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml={junit}", "{tests}"]
vulture = ["uv", "run", "--no-sync", "vulture", "."]
skylos = ["python", "-m", "skylos.cli", ".", "-a", "--no-upload", "--json"]
mutmut = [["wsl", "-d", "Ubuntu-24.04", "--", "mutmut", "run", "{mutants}"], ["wsl", "-d", "Ubuntu-24.04", "--", "mutmut", "results"]]
```

`vulture`, `skylos` and `mutmut` are optional: one argv, or a list of argv run in order. Their outputs are read as Vulture's text lines, Skylos's `--json` report (the flags the repo's `skylos.yml` uses), and mutmut 3's `results` lines (`<name>: survived`). `{mutants}` becomes mutmut 3 name globs, one per function to mutate. mutmut 3 needs `fork`, so on Windows it runs under WSL; the `wsl` lines above are an example, not tested here. A package without a tool's command gets a `NOTRUN` line for it.

Each command runs from the package root through the timed wrapper. In `test`, `{junit}` becomes the JUnit XML path and `{tests}` the test files (none means the whole package). A changed file belongs to the package with the longest matching root. Without `checks.toml` there is one package, `.`, tested with `python -m pytest`. A package without `lint` or `types` gets a `NOTRUN` line.

Test ids are `<root>::<classname>::<name>` from the JUnit report. `baseline-reds.txt` holds one id per line.

Fail-at-parent counts a JUnit `<failure>` whose message starts with `assert`, `AssertionError`, `Failed: DID NOT RAISE` or `Failed: DID NOT WARN`. Any other failure (an `ImportError` inside the test, a `NameError`) and every `<error>` (collection, module-level import, fixture) do not count, and a test that is not collected at the parent fails the check.

`suite.run_packages` is the one function `land` and `nightly` call to run tests. A CI backend replaces that function and returns the same shape.

### The timed wrapper

Every lint, types and test command runs through `wrapper.run_timed`, and builders use `timed` for their fast checks. Each run gets its own folder under `runs/`, with `TMP`, `TEMP`, `TMPDIR` and each `data_env_vars` folder inside it, deleted afterwards. It sets `PYTHON_KEYRING_BACKEND=keyring.backends.fail.Keyring`, puts `guard/sitecustomize.py` on `PYTHONPATH` (it refuses `Cred*` calls through ctypes), sets the no-prompt git variables, removes `CLAUDE*` and `ANTHROPIC*` variables, closes stdin, and touches `heartbeat/<id>` every `heartbeat_interval_s`. On timeout it stops the whole process tree (`taskkill /T` on Windows, the process group on Linux).

## state.json

```json
{
  "schema": 1,
  "repo": "C:/Users/.../QMX",
  "build_branch": "build/risk-core",
  "remote": "origin",
  "worktree_root": "D:/QMX-worktrees",
  "usage_reset_at": null,
  "last_green": null,
  "nightly": {},
  "merged": ["A"],
  "slices": {
    "rc-35": {
      "id": "rc-35", "name": "Exit ladder", "depends_on": ["rc-34"], "files": ["qmx/risk/exits.py"], "size": "M",
      "ask": "S2", "checkpoint": "B",
      "status": "held", "reason": "first rc-35-a1-r0-20261112T220000", "blocked_by": null,
      "attempts": 1, "restarts": 0,
      "holder": {"dispatch_id": "rc-35-a1-r0-20261112T220000", "attempt": 1, "restart": 0, "started": "2026-11-12T22:00:00+00:00"},
      "parent": "<build tip at dispatch>", "head": null, "pr": null, "patch_id": null, "landed_sha": null,
      "seen_sha": null, "seen_at": null
    }
  },
  "events": [{"at": "...", "kind": "status", "slice": "rc-35", "from": "pending", "to": "held", "reason": "..."}]
}
```

`attempts` counts quality rounds and is the only counter that parks a slice or feeds the breaker. `restarts` counts crashes, usage limits and power cuts. The worktree for slice `<id>` is `<worktree_root>/slice-<id>` on branch `slice/<id>`.

| Status | Meaning | Next |
|---|---|---|
| `pending` | not dispatched | `held`, `parked`, `blocked-by` |
| `held` | a builder holds the seat | `ready`, `red`, `dead`, `parked` |
| `dead` | the holder died; the next dispatch is a restart | `held`, `parked` |
| `ready` | `verify_ready` passed, PR open | `checked`, `red`, `held`, `dead`, `parked` |
| `red` | blocked at ready, checks or landing; awaits a fix round | `red`, `checked`, `held`, `dead`, `parked` |
| `checked` | slice checks green at `head` | `checked`, `ready` (a landing rebase changed it), `red`, `landed`, `held`, `dead`, `parked` |
| `landed` | on the build branch | none |
| `parked` | stopped for this run; `reason` starts with the cause | none |
| `blocked-by` | a dependency parked or was bisected as the nightly culprit; see `blocked_by` | none |

Park causes: `rounds` and `dispute` count toward the breaker; `brief-mismatch` and `manual` do not. The breaker trips at `breaker_parks` quality parks with no landing between them.

## Hook

Add to the settings of every Claude Code session in the run:

```json
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "Write|Edit|MultiEdit|NotebookEdit|Bash",
       "hooks": [{"type": "command", "command": "python D:/QMX-worktrees/ship-kit/tools/ship hook --program <program folder>"}]}
    ]
  }
}
```

It allows writes inside each held slice's worktree and current evidence folder, `review/` and `notes/`, and refuses the rest, including the main checkout and the planner's files. Claude Code's hook input does not say which agent is calling, so the allowed set is the union over held slices; it does not stop one builder writing into another held builder's worktree.

## Settings

Every number is a named setting in `settings.py` with its default. Override any of them in `<program>/ship.toml` under `[settings]`; an unknown key is an error.

| Setting | Default | Used by |
|---|---|---|
| `seats` | 3 | dispatch |
| `max_attempts` | 2 | dispatch: the build and one fix round |
| `breaker_parks` | 3 | status, run_report |
| `git_timeout_s` | 600 | every git and gh call |
| `fact_timeout_s` | 120 | each brief fact, the preflight guard check |
| `check_timeout_s` | 3600 | each slice check command, `timed` without `--timeout`, uv.lock regeneration |
| `land_timeout_s` | 7200 | the landing test run, per package |
| `nightly_timeout_s` | 10800 | the nightly run, per package, and the whole bisect |
| `bisect_step_timeout_s` | 1800 | one bisect step |
| `heartbeat_interval_s` | 30 | the wrapper's heartbeat touch |
| `liveness_stale_s` | 2700 | status: 45 minutes without a push or heartbeat |
| `power_poll_s` | 60 | power_watch loop |
| `power_settle_s` | 600 | power_watch: wait after mains returns |
| `net_timeout_s` | 20 | internet and GitHub probes, status's remote reads |
| `internet_probe` | `1.1.1.1:443` | power_watch |
| `keep_awake_poll_s` | 30 | the keep-awake helper |
| `teardown_wait_s` | 120 | teardown waiting for the helper to exit |
| `updates_paused_min_h` | 12 | preflight |
| `evidence_required` | `how.md`, `red.log`, `report.md`, `pr.md` | verify_ready |
| `slice_verdict_required` | false | land: also want a CLEAN slice verdict, and a range verdict after a changed rebase |
| `quality_dir` | `""` (`<worktree_root>/ship-quality`) | quality, baseline, slice_checks |
| `quality_timeout_s` | 3600 | one Skylos, Vulture or mutmut command |
| `watcher_stale_s` | 300 | power: `power.json` older than this means no watcher runs |
| `data_env_vars` | `QMX_HOME`, `QMX_DATA_DIR` | the wrapper |
| `strip_env_prefixes` | `CLAUDE`, `ANTHROPIC` | the wrapper |
| `gh` | `gh` | verify_ready, land |
| `lock_cmd` | `uv lock` | land |
| `protected_branches` | `main`, `integration`, `engine/base` | the protection push test |

## Edge cases these scripts own

Numbers refer to `tracker/shipping-method/EDGE-CASES-2026-11-12.md`.

| Edge case | Where |
|---|---|
| 1. agent writes in the main checkout | `hook`, `main-check` |
| 2. his click not enforced | `preflight --protection-push-test` (off by default) |
| 3. landing rebase changes behaviour | `land`: patch-id and overlap send the rebased commit back to `slice_checks` (RECHECK), union of packages |
| 4. half-written or stale proof | END line in `verify_ready`; evidence per attempt |
| 5. READY but GitHub does not match | `verify_ready` |
| 6. brief wrong about the code | `dispatch` facts, park as `brief-mismatch` |
| 7. run report lies by omission | `run_report` |
| 8. hung agent | `status` liveness, `timed` heartbeat and time limit, no-prompt git env |
| 9. old failures on the tip | `baseline-reds.txt` in `land` and `nightly` |
| 10. usage limit counted as an attempt | `attempts` and `restarts`, `recover --usage-reset`, `dispatch` refusal until reset |
| 12. two builders touch one file | `dispatch` overlap refusal, `verify_ready` overlap check, `land` uv.lock regeneration |
| 13. no convergence | `dispatch` parks after `max_attempts`; `park --cause dispute` |
| 14. shared temp folders | per-run temp and data folders in the wrapper (partly; see the next paragraph) |
| 15. restart doubles up | `recover`: dead seats, leftover patch, reset to the last pushed sha; new dispatch id per attempt |
| 16. sleep or reboot | `preflight`: pending reboot, updates paused, keep-awake |
| 17. Windows git traps | `preflight` LongPathsEnabled and `.gitattributes`, `core.longpaths` on every git call, `slice_checks` diff-check and case collisions, worktree removal without `--force` after stopping processes, failures to `leftovers.md` |
| 18. parked dependency empties the night | blocked-by cascade in `state.py`, idle cause in `run_report` |
| 21. liveness kills a healthy builder | `status` counts the wrapper heartbeat |
| 22. tests reach real credentials | the wrapper's fake keyring and credential guard |
| 23. nightly red with no suspect | `nightly` bisect |

| 20. tests that cannot fail | fail-at-parent in `slice_checks`; mutmut on changed functions in `quality` at each checkpoint |

Not owned here: 11 (the coordinator's context) and 19 (spawning skills in briefs) are rules for the coordinator and the planner. Not built: from 14, the machine-wide pytest worker slot file, `flaky.tsv`, and per-run ports (tests should bind port 0); from 22, the money scan's grep for keyring calls, which belongs in a package's `lint` command in `checks.toml`.

## Tests

```
cd tools
python -m unittest discover -s ship/tests -t .
```

The tests build real git repositories (a bare remote and a clone) in temp folders. Only `gh` is replaced, by `tests/fake_gh.py`, and Vulture and mutmut, by `tests/fake_tools.py`, which prints their real output shapes; `pytest` must be installed for the slice-check, landing, nightly and quality tests.
