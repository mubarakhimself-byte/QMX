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
| `preflight [--protection-push-test]` | `PROGRAM.yaml` (`gates.go`), `state.json`, the machine, the remote, the active `gh` account, free disk (a WARN, never a refusal) | `preflight/checks.txt`, `ARMED.md`, `main-status.txt`, `runs/`, `KEEP-AWAKE` | 0 armed, 1 refused |
| `main-check` | `main-status.txt`, the main checkout's HEAD (commit and branch) and the status under the code roots (`checks.toml` roots and `tools`, never `tracker/` or `.claude/`) | nothing | 0 unchanged, 1 changed (stop the run) |
| `facts --tip SHA [--slices a,b]` | every brief (or those named), a frozen checkout of SHA | `checks/_facts/<tip8>/summary.txt` | 0 all pass, 1 and one `FAIL <slice> <fact>` line each |
| `status` | `state.json`, `heartbeat/`, `HOLD`, remote slice branches, land runs (github) | `state.json` (last push seen, land run results) | 0, 1 on STALE or breaker |
| `dispatch <id>` | `state.json`, `HOLD`, `slices/<id>/BRIEF.md`, the build tip, `checks.toml` | the worktree (set up: the `setup` of every package the slice's files touch, normally `uv sync --frozen`, run through the timed wrapper before it returns, after the reset on a fix round or restart; a failed setup is a `FAIL setup-...` line, and `run` then starts no worker on it), `evidence/<id>/<attempt>/facts.log`, `leftover.patch`, `checks/_setup/<id>/a<attempt>-r<restart>/`, `state.json` | 0 dispatched (JSON, with a `setup` line per package), 2 refused, 3 parked |
| `timed --slice <id> --log L [--timeout S] -- <argv>` | nothing | the log, `heartbeat/<id>` | the command's exit code, 124 on timeout |
| `verify_ready <id> <sha>` | `state.json`, remote, `evidence/<id>/<attempt>/` | the PR, `state.json` | 0 ready, 1 blocked |
| `slice_checks <id>` | `state.json`, `checks.toml`, the brief, head and parent, the repo's `ci/baselines/` and CI's rules in `tools/ci/` (all read at the parent: quality, `pyright.txt`, `known-reds.txt`, `flaky.txt`), the Linux slice run (github) | `checks/<id>/<head8>/`, `state.json` | 0 green, 1 red |
| `land [<id> ...]` | `state.json`, `checks.toml`, the repo's known reds and flaky list at the batch's base (the build tip before it), `review/` (verdict mode only), the Linux slice runs (github) | the build branch, `refs/ship/rebased/<id>`, `checks/_land/<batch>/`, `leftovers.md`, `state.json` | 0 all landed, 1 otherwise (a `WAIT` slice lands on a later call) |
| `nightly [--no-wait]` | `state.json`, `checks.toml`, the repo's known reds at the tip; with `ci = "github"` the deep run and its `summary.json` | `checks/_nightly/<tip8>/`, `state.json` | 0 green, 1 red, 2 still running on GitHub |
| `ci start [--level L] [--fresh]` | `state.json`, the build tip, GitHub | `state.json` (`ci.deep`) | 0 dispatched or attached, 1 GitHub cannot run it |
| `ci status [--wait]` | `state.json`, the recorded run and its artifacts | `checks/_nightly/<tip8>/` (`ci/` holds the artifacts), `state.json` | 0 green, 1 red, 2 still running |
| `ci gate [--pr N] [--wait]` | `state.json`, the checkpoint PR and its gate run | `state.json` (`ci.gate`), one gate-job rerun | 0 gate passed, 1 it cannot, 2 running |
| `ci read <run id>` | any qmx-ci run | `tmp/ci-read/<run id>/` | 0 green, 1 red, 2 still running |
| `ci summary [--sha SHA]` | the deep run on SHA (default the build tip): the recorded one, else the newest GitHub lists | `checks/_nightly/<sha8>/summary.json`, only when the summary's `sha` is SHA | 0 saved (its blocking reds and quality rows printed as FAIL lines), 1 none for SHA or only one of another commit, 3 GitHub unreachable |
| `quality --from <sha> [--tools vulture,skylos,mutmut]` | `state.json`, `checks.toml`, the repo's `ci/baselines/` and `tools/ci/` (`ratchet.py`, `qci.py`) at `<sha>`; with `ci = "github"` the tip's `summary.json` first | `checks/_quality/<tip8>/` | 0 no new finding, 1 otherwise |
| `baseline` | nothing | nothing: it prints that CI's `baseline` level takes the baselines | 1 |
| `merged <checkpoint>` | `state.json` | `state.json` (`merged`) | 0 recorded or already, 1 refused |
| `power_watch [--once]` | the power line, the remote, `HOLD` (read again right before every write or removal) | `HOLD` (only when absent, created exclusively, or exactly its own text; his written during a probe is never touched), `power.json` (with its own HOLD text), `state.json` events | 0 |
| `power` | `power.json`, `HOLD` | nothing | 0 go, 1 HOLD (wait), 2 no watcher (start one) |
| `hold --why TEXT` | nothing | `HOLD` (`him: TEXT`), a `hold` event | 0 |
| `release` | `HOLD` | removes a manual `HOLD`; never the power watch's (`power: ...`, `network: ...`), which clears itself | 0 released or none, 1 the HOLD is the power watch's |
| `recover [--usage-reset ISO]` | `state.json`, worktrees, remote, the recorded GitHub run | `evidence/<id>/<attempt>/leftover.patch`, worktrees, `state.json` | 0 |
| `park <id> --cause dispute\|manual --why TEXT` | `state.json` | `state.json` | 0 |
| `run_report` | `state.json`, `checks/` | `RUN-REPORT.md` | 0, 1 if the counts do not add up |
| `teardown` | `ARMED.md` | the machine, `ARMED.md` (keeps only what is still there) | 0 all gone, 1 otherwise |
| `hook` | hook JSON on stdin, `state.json`, `SHIP_ROLE` and the role's path variables (`SHIP_NOTES`, `SHIP_STOP`, `SHIP_PART`, `SHIP_WORKTREE`, `SHIP_BRANCH`, `SHIP_REPO`; the table is in `hook.py`) | nothing | 0 allow, 2 refuse (a missing or unknown role, a missing variable, a `SHIP_STOP` or `SHIP_PART` that is not a plain name, or any error refuses) |
| `records init --repo R --plans P [--remote origin]` (no `--program`) | the remote's `plans` branch | the plans worktree, `_records/` seed files, one commit under `records.lock` | 0, 1 refused (another branch there, a full folder in the way, or a local `plans` that diverged from the remote) |
| `records commit --plans P -m MSG` | the plans worktree | one commit of everything changed on `plans`, pushed (an unreachable push stays local). The kit's own records commits (claims, removal rows) commit only `_records/` (D-L22) | 0 |
| `records prefix --plans P --repo R <prefix>` | `PREFIXES.md`, `<plans>/*/SLICES.md`, old programs' `SLICES.md` under `<worktree root>/*/tracker/`, slice branches (remote and local) | nothing | 0 free, 1 and one `CLASH` line each |
| `phase --program P` / `--all --plans P` / `--set PHASE --status S --by WHO` / `--words` (no `--program` needed for `--all` and `--words`) | `PROGRAM.yaml`, `phase.json`, `state.json`, the stop notes, verdicts and merge notes, `chain.lock`, `WAITING.md`, `notes/WAITS-ON-YOU.md` | `phase.json` (`--set` only) | 0 |
| `gate <name> --by WHO --source SRC [--advance]` | `PROGRAM.yaml` | the `gates:` block of `PROGRAM.yaml` and one line of `.kit/gates.log`, the only record arm, phase and merge trust: a gate in `PROGRAM.yaml` that differs from the log waits (D-L22) | 0, 1 when the program's kind has no such gate |
| `run [--once]` | `state.json`, `SLICES.md` (lanes), `run.json`, `BUILDER.md` in `prompt_dir`, the project profile (`RULES`, `PROJECT.*`, its `[roles]`), the remote | workers, `chain.lock`, `run.json`, `notes/run.log`, `notes/WAITS-ON-YOU.md`, `notes/CHAIN-ISSUES.md`, `notes/stop-<X>.json` | 0 built or nothing left, 10 waits, 11 lock held, 1 breaker or main changed |
| `unpark <id> --why TEXT` | `state.json`, `stop-review/<X>/` | `state.json`; removes `notes/stop-<X>.json` | 0, 1 refused (checkpoint merged, not open, its review started, or a quality park) |
| `spike [--parent\|--child\|--recheck]` | the real `claude` CLI (haiku, three tiny runs; `--recheck`: probes 2, 3 and 7 under the isolation flags plus one opus and one fable model probe) | `workers/spike/SPIKE.md`, `roles/RESULT-SHAPE.md`; `--recheck` appends to `roles/SPIKE.md` | 0 all probes pass, 1 otherwise |
| `trace --stop X` | `PROGRAM.yaml` (`chains`), `state.json`, the briefs' `Chain:` and section 7a lines, `git log --first-parent from..tip`, `checks/`, `REMOVED.md` (the program's and `_records/`), `evidence/*/*/report.md`, `notes/CHAIN-ISSUES.md` | `stop-review/X/MAP.md` | 0, 1 on an unchained commit, a scenario with no passing test, or a failed removal guard |
| `review X [--round 1\|2]` | `notes/stop-X.json` (round 2: the fix program's), the readers' notes, the deep run, the verdict file | `START.json`, `.kit/X/review-run.json` (its `result` and `tip` are what `merge` trusts), `MAP.md`, reader checkouts (dropped at the end), workers, `merge/X.md` (`EMPTY` only), `notes/WAITS-ON-YOU.md`; on a round-1 BLOCKED the fix folder's `ship.toml` and `checks.toml` (copied from the parent) and its go gate (through `set_gate`) | 0 CLEAN (or empty), 2 BLOCKED, 10 waits, 11 lock held |
| `merge X` | `PROGRAM.yaml` and `.kit/gates.log`, `state.json`, `.kit/X/review-run.json` (`result` 0 and a `tip` equal to the verdict's END sha, else WAITS), `stop-review/X/` and the fix folder's verdicts, `.kit/X/MERGE-BASE` (accepted only when its first-parent line back to the reviewed tip holds merge and generator commits alone), `merge/X-pr.md`, the remote build and target branches (the profile's `target_branch`, default `ci_gate_base`), the PR's gate run | a merge commit of the target on the build branch when it moved (and its deep run), `.kit/X/MERGE-BASE`, the PR (merged with `--match-head-commit`), `merge/X.md` (`MERGED <sha>`), `state.json` (`merged`), `_records/REMOVED.md` (one commit), a one-slice `<program>-fix-X` on a conflict or a red run; the claims of the stop's patterns that no unmerged slice names, and all of the fix program's | 0 merged or already, 2 refused by the gate or a fix program written, 3 unreachable or the target moved under the PR (retry), 10 waits (a conflict after round 2 included: no third round), 11 another program holds the project's merge lock (its place in the queue is kept) |
| `chain --program P [--detach]` (no `--program` needed for `--resume-all` and the task flags) | `phase.read` every `chain_poll_s`, then the activity for `next` (table in `chain.py`): `check_chain`/`check_plan` and the `plan-review`, `planner-fix`, `grounding`, `later-handoff` workers, `init` and `preflight` (`arm_preflight`), `facts`, `run.Build`, `review.Checkpoint`, `merge`, the docs step, the audit stages (in a frozen checkout of the census tip: `probe_tests.py` once per package root, then one `audit-reader` per `## Parts` line of `CENSUS.md` with `SHIP_PART`, `PART` and `CHECKOUT`, then `collect_findings.py`; the judge, then the `audit-screen` worker, then `apply_screen.py`; the hand-off with `CHECKOUT`), the finish. HOLD (whoever wrote it) starts nothing new (D-L25): one guard in the tick returns before any activity when nothing runs; while something runs its activity is ticked so the result is read, and every start (worker, script child, build branch push, `init`, the audit checkout, `go`, docs, the finish's teardown, a review's readers, deep run and verdict, the build's seats) checks HOLD again and does not happen. An audit probe that does not exit 0, a failed `collect_findings.py`, and an audit reader's `WAITS` reply are WAITS; a reader's usage limit is never one of its runs. A planner-fix round started by his answers is never the second-fixes stop and resets that memory (`planner_fix_done` in `chain.json`): every line of `FIXES.md` must quote an entry of `.desk/answers.md` (written only by the desk) with the same `<id8>:L<line>` source, and the factory's `his_words.py` (run with `his_words_timeout_s`) must find that quote at that line; anything else is the mechanical round | `chain.lock`, `chain.json`, `phase.json`, `notes/chain.log`, `notes/WAITS-ON-YOU.md`, `WAITING.md`, everything the activities write; `--detach` starts it as its own process with output in `chain.log` (Windows: `CREATE_NO_WINDOW`, `CREATE_NEW_PROCESS_GROUP`, `CREATE_BREAKAWAY_FROM_JOB`, never `DETACHED_PROCESS`; every child adds `CREATE_NO_WINDOW`) | 0 finished (or stopped after `STOP-AFTER`'s stop merged), 10 waits on him, 11 lock held, 1 an error written to WAITS |
| `chain --follow [P]` | `phase.read`, `phase.json`, `chain.lock`, the WAITS files | nothing; one line per change | 0 done, 10 waits on him (a conveyor that exited 10 with no WAITS line counts), 1 the conveyor is dead (a `chain.lock` holder is alive only with the same pid and creation time, written since the machine started) |
| `chain --resume-all --plans P` | each program's `phase.json` and `chain.lock` | `recover`, then a detached conveyor for every program that says running with a dead lock | 0 |
| `chain --stop-after X` | nothing | `STOP-AFTER` | 0 |
| `chain --install-task --plans P` / `--remove-task` | nothing | nothing: prints the task (logon and every 15 minutes, least privilege, `chain --resume-all`) and the exact `schtasks` lines; add `--install` to register or remove it | 0 |
| `abandon --why TEXT` | `chain.lock` (its pid and children), `state.json`, `ARMED.md` | stops the conveyor and its children, `recover`, `teardown`, claims released, `abandoned:` in `PROGRAM.yaml`, `notes/ABANDONED.md`, `phase.json` done | 0 |
| `claims claim\|notice\|release\|sweep\|list` | `SLICES.md` (claim), `PROGRAM.yaml` `area` (notice), `_records/CLAIMS.tsv` beside the program folder, the project profile's `shared_generated`, a fix program's `parent` link | `_records/CLAIMS.tsv`, one commit on `plans` per change. Only an earlier claim blocks: a later overlapping pattern gets no row and waits until the earlier one is released; a program and its fix programs (by `parent` in `PROGRAM.yaml`) never block each other | 0; `claim` prints each `blocked-by claim` line and still exits 0 |

`bisect-step` is internal: `nightly` hands it to `git bisect run`.

## Checkpoints and pre-building

A slice's checkpoint is SLICES.md's `stop` column (`checkpoint` is read too); with neither, the program is one checkpoint. The open checkpoint is the first, in table order, not recorded by `merged`. A slice of the next checkpoint may be dispatched before then (pre-built), but only when its files overlap no slice of the open checkpoint, which is building or in review and may get a fix batch. Two checkpoints ahead is refused. A pre-built slice passes its checks and waits in `checked`; `land` holds it until `merged <open>`.

## Quality ratchet

There is one ratchet, and it lives in the repo (FACTORY-DESIGN section 5): `ci/baselines/` holds `vulture.txt`, `skylos.txt`, `mutmut.txt`, `pyright.txt`, `known-reds.txt` and `flaky.txt`, the files qmx-ci judges by. The kit reads them and never writes them. The kit matches qmx-ci exactly, neither stricter (D-L25): CI's own rules come from the checkout's `tools/ci/qci.py` (with its sibling modules), loaded at run time under their own names and never left in `sys.modules`; a checkout with the ratchet but without `qci.py` FAILs Skylos with that reason. Only a NEW finding blocks, and for Skylos only by CI's rule (`qci.skylos_findings`: `SKYLOS_BLOCKING`, `SKYLOS_NOTES_ONLY_PREFIX`, critical or high severity); a new Skylos finding CI keeps as a note gives a `NOTE` line, which never fails a check. A Vulture line with no confidence is an incomplete scan (FAIL), as in CI. A finding is keyed exactly as qmx-ci keys it, `path|rule|message` with no line number (mutmut's path is its package folder, pyright's message has every number as `#`), by the checkout's own `tools/ci/ratchet.py`, loaded from the checkout; keys are counted, so a second copy of a known finding in the same file is new. A checkout without `tools/ci/ratchet.py`, or without the tool's baseline file, gives `NOTRUN no baseline`.

- Per slice, in `slice_checks`: Vulture and Skylos over each touched package at the head; only findings in the slice's changed files count. Vulture is judged against the baseline alone, as qmx-ci's slice level; Skylos also knows what the parent shows, standing in for CI's `--diff-base` slice scan. The baseline is read at the parent, so a slice cannot excuse its own finding. A `types` command that fails is ratcheted against `pyright.txt` alone (no parent run), as qmx-ci's slice level: only an error in a changed file that the baseline does not hold blocks; output whose error count does not add up stays FAIL.
- Per checkpoint, `quality --from <sha>`: with `ci = "github"` and the tip's `summary.json` (`ci summary`), its `quality` rows are the verdict (a `new` row that `blocks` fails; a quality job, `vulture`, `skylos` or `mutmut-<n>`, that did not succeed and left no blocking row crashed before its `*-ratchet.json`, which FAILs too) and nothing runs here; otherwise the same tools at the build tip against `<sha>`, plus mutmut on every function holding a changed line (mutmut 3 mutates whole functions, so that is its finest grain).
- Baselines are taken by CI's `baseline` level and shrink only through `qci ratchet --prune`, which `ship merge` runs as a generator (the profile's `[generators]`) after merging a moved target, under the project's merge lock. `ship baseline` only says so and exits 1.

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

Every evidence file a script accepts ends with the line `END <full 40-character sha> <dispatch id>`, and holds something before it. The kit writes that line on each `evidence_required` file (`how.md`, `red.log`, `report.md`, `pr.md` by default) when the builder replies `READY <sha>`; a builder that wrote its own has it replaced. `verify_ready` then requires each of them in `evidence/<id>/<attempt>/`, ending with the END line for the head it checks and the attempt's dispatch id.

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

Test ids are `<root>::<classname>::<name>` from the JUnit report.

Fail-at-parent counts a JUnit `<failure>` whose message starts with `assert`, `AssertionError`, `Failed: DID NOT RAISE` or `Failed: DID NOT WARN`. Any other failure (an `ImportError` inside the test, a `NameError`) and every `<error>` (collection, module-level import, fixture) do not count, and a test that is not collected at the parent fails the check.

`suite.run_packages` is the one function `land` and `nightly` call to run tests locally. The GitHub backend (`ci.read_run`) returns the same shape, keyed by shard (`suite-linux-3`) with ids `system|unit|class::name`; see "CI on GitHub".

### Known reds

`suite.baseline_for` gives `slice_checks`, `land` and `nightly` the lists of reds that do not block: the repo's `ci/baselines/known-reds.txt` and `ci/baselines/flaky.txt` (qmx-ci's lists, written by `tools/ci/pull_reds.py`, key `system|unit|class::name`), read at the slice's parent (`slice_checks`), the batch's base (`land`) and the tip (`nightly`), so a change cannot excuse its own red. As in qmx-ci (`split_flaky`, `tests_verdict`), every run's reds run once more (`suite.rerun_reds`: their test files, or the whole package when a file cannot be found), and `Baseline.judge` decides: a red that stays red blocks unless known-reds.txt names it; a red that passed on the rerun, in a module the change did not touch, is flaky and blocks unless flaky.txt names it; a flaky red in a touched module is a red. A GitHub shard's flaky tests are those its `flaky-*.txt` lists. A commit without them has no known reds. The kit never writes either file; a known red that passes prints `NOTE known red passes now` (shrink the list with `pull_reds.py`). With `ci = "github"`, the deep run's `summary.json` adds what qmx-ci itself blocks (a newly flaky test, an unfinished shard, a blocking quality row) as FAIL lines.

Ids are compared in one spelling, `system|root|class::name`, where the class loses a leading dotted form of its root (`qml.tests.test_x` under `qml` is `tests.test_x`), because qmx-ci runs some units from the repo root and `checks.toml` runs each package from its own. A local id is on this machine's system: a red known only on Linux still blocks a local Windows run. `slice_checks`' test check fails only on a red outside this list (before, it failed on any red).

### The timed wrapper

Every lint, types and test command runs through `wrapper.run_timed`, and builders use `timed` for their fast checks. Each run gets its own folder under `runs/`, with `TMP`, `TEMP`, `TMPDIR` and each `data_env_vars` folder inside it, deleted afterwards. It sets `PYTHON_KEYRING_BACKEND=keyring.backends.fail.Keyring`, puts `guard/sitecustomize.py` on `PYTHONPATH` (it refuses `Cred*` calls through ctypes), sets the no-prompt git variables, removes `CLAUDE*` and `ANTHROPIC*` variables, closes stdin, and touches `heartbeat/<id>` every `heartbeat_interval_s`. On timeout it stops the whole process tree (`taskkill /T` on Windows, the process group on Linux).

## Workers: headless Claude Code runs

`launch.py` starts every agent as `claude -p` (FACTORY-DESIGN section 11.3) and is the only place that command
line is built: the role's model and effort, `--settings roles/<file>.json` (the write-guard hook, the depth
variable and the allow-list), `--permission-mode dontAsk --permission-prompts none`, `--disallowedTools Agent`
unless the role uses agents, `--add-dir` the program folder and the factory home, a fresh `--session-id`, a
`--name "<role>: <program> <slice>"`, `--fallback-model` for Fable roles, `--setting-sources project,local` (none of
his user settings, hooks, plugins or CLAUDE.md) and `--strict-mcp-config` with no MCP servers, and
`--output-format json`. Never `--bare` (that would drop the plan login) and never `bypassPermissions`. The run's
environment is an allow-list (D-L11: PATH, SYSTEMROOT, TEMP and TMP, USERPROFILE, HOME, APPDATA, LOCALAPPDATA,
COMSPEC, PATHEXT, a few Windows basics, `GIT_*`, `UV_*`, `SHIP_*`, and the `worker_env_extra` setting); it sets
`SHIP_PROGRAM`, `SHIP_ROLE`, `SHIP_KIT` and the depth variable. The role allow-lists hold reads, file writes,
the git calls a builder needs, `uv run --no-sync` and the kit's `timed` wrapper; no bare `python` or `git`. A
result is a `limit` only when the text names a limit and the run ended in an error (`is_error` or a non-zero
exit). Each run's folder is `workers/<id>/` (`prompt.md`, `started.json`, `stdout.log`, `stderr.log`,
`result.json`). A result's `kind` is `ok` (the last non-blank line is `READY`, `BLOCKED`, `DONE` or `WAITS`),
`nocontract`, `limit` (with `limit_reset`), `timeout` or `crash`; `roles/RESULT-SHAPE.md` records the JSON the
parser reads. Roles live in `roles/roles.toml`. `clock.now()` reads the time from the file `SHIP_FAKE_NOW`
names, when set. Tests replace `claude` with `tests/fake_claude.py` (rules in the file `FAKE_CLAUDE_SCRIPT`
names), as `gh` is replaced by `fake_gh.py`. `roles/SPIKE.md` is the spike log from the real machine.

## The build loop: `ship run`

`run` is the build loop, as a script: it holds `chain.lock` (a live holder means
exit 11; a dead holder's children are stopped and its seats recovered), then ticks every `chain_poll_s`. Each
tick: `main-check` (when armed), power and network (`HOLD` on battery or when the internet or GitHub does not
answer: route, start nothing), a pending usage reset (start no worker), route every finished builder,
`verify_ready`, `slice_checks` and `land` by the card's table, `status` (a `STALE` slice whose builder runs has
only that builder stopped and restarted; `BREAKER` stops), fill seats (dead slices, fix rounds, then pending
slices lane by lane from SLICES.md's `lane` column, then pre-builds; one `land` at a time), and write
`notes/stop-<X>.json` once the open checkpoint is built. A builder that dies (`nocontract`, `crash`,
`timeout`, stale) is recovered and restarted; its `max_restarts`-th death (the slice's `deaths`; a usage limit is
a restart, never a death) parks it `manual` with a WAITS line holding its last 20 lines. `chain.lock` holds the
pid and creation time of the run and of each child: a dead holder's children are stopped only on an exact match,
and a lock written before the machine last started is taken over with no kill (D-L14). Each `verify_ready`,
`slice_checks` and `land` child is stopped past its time limit and started again on the next tick. `BLOCKED chain` and `BLOCKED files` go to `notes/CHAIN-ISSUES.md`; any other
`BLOCKED` and a brief mismatch go to WAITS. A usage limit records the reset and restarts the slice after it.
A missing build branch is one WAITS line and exit 10. A `land` that crashes (a traceback, or an exit other than 0 or 1) is counted; the `max_restarts`-th crash in a row is one WAITS line and exit 10 (D-L26 F9). A builder's prompt gets `run.PROMPT_KEYS`: its slice's values, `RULES` (the project's PROJECT-RULES.md) and `PROJECT.<key>` for every key of the profile's [project] table; roles come from `roles.toml` with the profile's `[roles.<name>]` overrides, here and in the checkpoint review. A fix round's reason and paths stay in `run.json` (`fixing`) until `verify_ready` passes, so a fixer that dies is restarted as a fixer with the same `FIX_REASON` and `FIX_PATHS`. When a builder replies `READY <sha>`, the kit stamps `END <sha> <dispatch id>` on each `evidence_required` file in its evidence folder (replacing any END line already there), then `verify_ready` reads them. Routing reads `state.json`, so a run killed anywhere
carries on when started again; `run.json` holds the rest (READY replies waiting for `verify_ready`, fix rounds
for checked slices, a red batch being landed one slice at a time). `--once` starts work in one tick, then only
routes until nothing runs. `verify_ready` exits 3 and changes nothing when the remote or `gh` does not answer.

## CI on GitHub

`ci = "github"` (set in `ship.toml`; the default is `"local"` until qmx-ci is on the target branch) uses qmx-ci (`.github/workflows/qmx-ci.yml` on `origin`; every `gh` call names the repo with `-R github_repo`, because the checkout has other GitHub remotes). Its levels follow the branch names these scripts push: every slice branch is `slice/<id>` (qmx-ci level `slice`, Linux) and the build branch must be `build/<name>` (level `land`, touched tests on Linux and Windows); `init` refuses any other build branch name with `ci = "github"`. Each push is one ref (GitHub sends no event for a push of more than 3 refs).

| Level | What starts it | What the scripts do with it | Blocks |
|---|---|---|---|
| slice | the builder's push to `slice/<id>` | `slice_checks` writes its `linux` line (PASS, FAIL, PENDING, NOTRUN); `land` reads it again (`ci.linux_gate`) | Yes. Red sends the slice back (`red`). Pending: `land` prints `WAIT` and holds the slice up to `ci_slice_grace_s` after `slice_checks` went green, then lands on the local checks with `linux: pending` in the slice's `ci` record; the checkpoint reads it again and a red one is a FAIL there. Not run (no workflow at that commit): lands. |
| land | `land`'s push to `build/<name>` | `land` records each landing in `state.json` (`ci.land`); `status` reads its run and prints `LAND-RED` | No. Evidence for the checkpoint; its deep run decides. |
| deep | `nightly` or `ci start` (`gh workflow run`) | dispatched once per tip and recorded (`ci.deep`); `ci status` reads it into the same verdict as a local nightly | Yes: green only with no new red, every shard reported, every other job green, and a `deep-verdict` naming the tip. |
| gate | the checkpoint PR into `engine/base` | `ci gate` | Yes: merge only on exit 0. A PR opened before the deep run was green has a failed gate job; once ship records the deep run green on the PR head, `ci gate` reruns that job (`gh run rerun <run> --job <id>`), once per gate run. |

Builders never wait on any of this: `slice_checks`, `land` and `status` read whatever GitHub has and return.

**The deep run.** `nightly` calls `ci start`, then `ci status --wait`. `ci start` attaches instead of dispatching when `state.json` holds a run for the same tip that was not cancelled, or when GitHub already lists a deep `workflow_dispatch` run on that tip (a crash between the dispatch and the record); `--fresh` dispatches anyway. `ci status` exits 2 while the run is going and prints the new reds finished shards already show (`SO-FAR`). A finished run is judged once: its lines go to `checks/_nightly/<tip8>/summary.txt` and later calls read them back. New reds on this machine's system are bisected locally as before; reds only on the other system are reported with the slices landed since the last green tip as suspects. `nightly --no-wait` returns after the dispatch, for a caller that polls with `ci status`.

**Fallback.** When `ci start` cannot reach GitHub (no `gh`, no network, gh signed out) or the workflow file is not at the tip, `nightly` prints `CI github unavailable: <why>; the local run stands in` and runs the whole suite on this machine. `ci = "local"`, the default, always runs locally and reads no GitHub evidence.

**Power cut or restart.** The deep run lives on GitHub. `recover` prints `CI deep <run> ... re-attached` for a recorded run with no result, and `nightly` or `ci start` attach to it; nothing dispatches a second run for the same tip. While GitHub is unreachable, `ci status` exits 2 and a `--wait` watcher keeps polling until `ci_wait_timeout_s`.

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
  "ci": {"deep": {"tip": "<sha>", "level": "deep", "run_id": "43474050888", "url": "...", "at": "...", "result": null},
         "land": [{"tip": "<sha>", "batch": "20261113T120000", "slices": ["rc-35"], "result": "green", "url": "..."}],
         "gate": {"<gate run id>": 1}},
  "slices": {
    "rc-35": {
      "id": "rc-35", "name": "Exit ladder", "depends_on": ["rc-34"], "files": ["qmx/risk/exits.py"], "size": "M",
      "ask": "S2", "checkpoint": "B",
      "status": "held", "reason": "first rc-35-a1-r0-20261112T220000", "blocked_by": null,
      "attempts": 1, "restarts": 0,
      "holder": {"dispatch_id": "rc-35-a1-r0-20261112T220000", "attempt": 1, "restart": 0, "started": "2026-11-12T22:00:00+00:00"},
      "parent": "<build tip at dispatch>", "head": null, "pr": null, "patch_id": null, "landed_sha": null,
      "seen_sha": null, "seen_at": null,
      "ci": {"sha": "<pushed head>", "linux": "pass", "url": "..."}
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

Every worker runs with `SHIP_ROLE`; the guard refuses a missing or unknown role. D-L25: no role writes `<program>/.desk/` (his answers, the desk's), a worktree's `ci/baselines/` or `contracts/` (by file tool, redirection or a git write naming them; they change only through the generators at merge), and no role but a builder writes `*.py`, `conftest.py`, `pytest.ini`, `pyproject.toml`, `setup.cfg` or `tox.ini`; such a role runs pytest only on code it did not write (no path in the program folder, no `-p` but `-p no:...`, no `-c`, `-o`, `--rootdir`, `--confcutdir`, `--doctest-glob`). Each role runs only the factory scripts on its list (`hook.ROLE_SCRIPTS`), whose output paths (`--out`, `-o`, the program folder of `chain_packet.py` and `sweep_briefs.py`) must be its own, whose `--ship` must be this kit, with no `check_chain.py --rerun-facts`, and `probe_tests.py --python` only the checkout's interpreter or the kit's. File tools write only the role's paths (the table in `hook.py`): a builder its held worktrees, evidence folders, `review/` and `notes/` (never `notes/stop-*.json`), a verdict only `stop-review/<X>/REVIEW*.md` and `WAITS.md`, `merge/<X>-pr.md` and the plan files of its fix folder. No role writes `.kit/`, the kit's own folder (`review-run.json`, `MERGE-BASE`, `gates.log`). Bash is an allow-list (D-L22): `git`, `uv run [flags]` and the kit's `timed` followed by pytest, `python -m pytest`, ruff, pyright or mypy, the kit's read-only `phase`, and the role's own factory scripts. The role settings files allow the same, script by script: `grounding.json` his_words, check_chain, check_plan; `plan-review.json` check_chain, check_plan; `verdict.json` check_plan; `planner.json` chain_packet, check_chain, check_plan, sweep_briefs; `audit.json` his_words, check_chain, callers, lint_findings (the hook narrows each role further). `gh`, `uvx`, `uv run --with`, inline python (any flag cluster holding `c`, any python name such as `python3.12` or `pythonw`), a nested shell, `$(...)`, a leading `VAR=value`, `git -c`, `git --output` and the git commands that run other programs are refused; redirection (`>`, `>>`, `tee`) is refused for every role but a builder, which may redirect only into its worktree. A path a command names may not be the main checkout, `~/.claude`, `.kit/`, or a program file the role does not write. Git writes stay in a held worktree (builders) or the docs worktree, never through `-C`, `cd`, `--git-dir` or `--work-tree` elsewhere; no force push, no `--mirror`, `--all`, `--tags`, `--delete` or `--prune`, no remote branch deletion, and a push only to the worker's own branch. It fails closed: any error in the guard, a bad `ship.toml` or an unreadable `state.json` refuses with exit 2, and the role settings run it as `... hook ... || exit 2`. Claude Code's hook input does not say which agent is calling, so a builder's allowed set is the union over held slices; it does not stop one builder writing into another held builder's worktree.

## Restart loops and the chaos findings (D-L26)

Every worker restart loop counts toward `max_restarts`, then WAITS. In the conveyor a worker's starts are counted
per name, and the count starts again only when another activity finishes (its step moved on); a usage limit is
never one of its runs. So a plan review that writes no `RESULT:` line, a later or sweep hand-off that writes no
slice, and an audit hand-off are asked at most `max_restarts` times. Also:

- **F1:** `init_state` appends the rows a later hand-off adds for a stop PROGRAM.yaml marks `handoff: deferred`
  (existing rows unchanged, else refused); the conveyor then runs those briefs' facts at the target's tip.
- **F2:** after the intent stage the audit waits on `gates.intent` (a WAITS line naming his questions); no
  reader, judge or screen starts before it.
- **F3:** a scoped audit (one with a `parent`) stops after its judgement: its findings go to the parent's
  `notes/AUDIT-<audit>.md`, no verdicts gate, and `ship phase` says done.
- **F4:** `ship claims notice` prints `OVERLAP <kind> <program>` for another program's live row on the area.
- **F5:** a Fable worker that ran on its fallback gets a line in `notes/FALLBACKS.md`; the conveyor copies it to
  `chain.log` and the run report lists it.
- **F6:** an audit's sweep briefs are armed like a feature's: facts at `parent_tip` and at the target's tip, so a
  merge into the area since the census reruns them (a failing one starts the grounding worker).
- **F7:** an audit hand-off that writes no `SLICES.md` ends the program done, its rows listed in
  `notes/HANDOFF.md`.
- **F8:** a merge refused because the target moved is counted; at `merge_moved_max` it WAITS, naming the merges.
- **F9:** `land` removes a stale `index.lock` in its landing copy when no git process works there.
- **G1:** see `fable_wait_s`.

## Settings

Every number is a named setting in `settings.py` with its default. Override any of them in `<program>/ship.toml` under `[settings]`; an unknown key is an error.

| Setting | Default | Used by |
|---|---|---|
| `seats` | 3 | dispatch |
| `max_attempts` | 2 | dispatch: the build and one fix round |
| `breaker_parks` | 3 | status, run_report |
| `git_timeout_s` | 600 | every git and gh call |
| `fact_timeout_s` | 120 | each brief fact, the preflight guard check |
| `his_words_timeout_s` | 120 | chain: one `his_words.py` run checking a quote of his at its transcript line |
| `check_timeout_s` | 3600 | each slice check command, `timed` without `--timeout`, uv.lock regeneration |
| `land_timeout_s` | 7200 | the landing test run, per package |
| `nightly_timeout_s` | 10800 | the nightly run, per package, and the whole bisect |
| `bisect_step_timeout_s` | 1800 | one bisect step |
| `heartbeat_interval_s` | 30 | the wrapper's heartbeat touch |
| `liveness_stale_s` | 2700 | status: 45 minutes without a push or heartbeat |
| `power_poll_s` | 60 | power_watch loop |
| `power_settle_s` | 600 | power_watch: wait after mains returns |
| `net_timeout_s` | 20 | internet and GitHub probes, status's remote reads |
| `internet_probe` | `1.1.1.1:443` | power_watch; `""` skips it |
| `keep_awake_poll_s` | 30 | the keep-awake helper |
| `teardown_wait_s` | 120 | teardown waiting for the helper to exit |
| `updates_paused_min_h` | 12 | preflight |
| `evidence_required` | `how.md`, `red.log`, `report.md`, `pr.md` | verify_ready |
| `slice_verdict_required` | false | land: also want a CLEAN slice verdict, and a range verdict after a changed rebase |
| `quality_timeout_s` | 3600 | one Skylos, Vulture or mutmut command |
| `watcher_stale_s` | 300 | power: `power.json` older than this means no watcher runs |
| `data_env_vars` | `QMX_HOME`, `QMX_DATA_DIR` | the wrapper |
| `strip_env_prefixes` | `CLAUDE`, `ANTHROPIC` | the wrapper |
| `gh` | `gh` | verify_ready, land |
| `lock_cmd` | `uv lock` | land |
| `protected_branches` | `main`, `engine/base` | the protection push test |
| `ci` | `local` | `github` or `local`; see "CI on GitHub" |
| `github_repo` | `mubarakhimself-byte/QMX` | `-R` on every gh call |
| `ci_workflow` | `qmx-ci.yml` | ci |
| `ci_gate_base` | `engine/base` | ci gate: the checkpoint PR's base |
| `ci_poll_s` | 120 | `--wait` watchers |
| `ci_wait_timeout_s` | 43200 | `--wait` gives up (exit 2); the run goes on |
| `ci_find_s` | 180 | ci start: how long to look for a run it just dispatched |
| `ci_slice_grace_s` | 3600 | land: how long a pending Linux slice run holds a slice |
| `claude` | `claude` | launch: the CLI (tests: python and `tests/fake_claude.py`) |
| `factory_home` | `D:/factory` | launch: `--add-dir`; `FACTORY_HOME` overrides it |
| `limit_patterns` | `usage limit`, `rate limit` | launch: text that marks a usage-limit ending |
| `limit_backoff_s` | 1800 | launch: the wait when a limit names no reset time |
| `max_restarts` | 3 | run, dispatch: infra restarts before a slice is parked for him; also failed worktree setups in a row |
| `disk_warn_gb` | 20 | preflight: WARN below this many GB free on the worktree drive |
| `main_check_ignore` | `tracker`, `.claude` | main-check: folders that never stop a run |
| `prompt_dir` | `""` (`<factory_home>/skills/factory/prompts`) | run: the folder holding `BUILDER.md` |
| `chain_poll_s` | 20 | run: seconds between ticks |
| `verify_timeout_s`, `slice_checks_timeout_s`, `land_run_timeout_s` | 1800, 14400, 14400 | run: a child past this is stopped and started again |
| `worker_env_extra` | none | launch: variables passed to workers beyond the allow-list |
| `merge_moved_max` | 5 | chain: merges GitHub refused because the target moved, then WAITS naming the merges that moved it (D-L26 F8) |
| `fable_wait_s` | 1800 | launch: a Fable role that waited longer for the Fable seat runs on its fallback, logged in `notes/FALLBACKS.md` (D-L26 G1) |

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
| 9. old failures on the tip | the repo's `ci/baselines/known-reds.txt` and `flaky.txt` in `slice_checks`, `land` and `nightly` |
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

Not owned here: 11 (a long session's context) and 19 (spawning skills in briefs) are rules for the planner. Not built: from 14, the machine-wide pytest worker slot file, `flaky.tsv`, and per-run ports (tests should bind port 0); from 22, the money scan's grep for keyring calls, which belongs in a package's `lint` command in `checks.toml`.

## Tests

```
cd tools
python -m unittest discover -s ship/tests -t .
```

or, from the repo root, `python -m pytest tools/ship -q -p no:cacheprovider`. Both run one test at a time (about 45
minutes on the laptop). `cd tools && python ship/tests/run_parallel.py` runs the same tests one class per job,
four at a time (about 17 minutes): every test makes its own temp repo, program and factory home, so classes share
nothing; a failing class prints its whole output and the exit is 1.

The tests build real git repositories (a bare remote and a clone) in temp folders. Only `gh` is replaced, by `tests/fake_gh.py` (PRs, and Actions runs with their jobs and artifacts, each call logged), and Vulture, Skylos, mutmut and pyright, by `tests/fake_tools.py`, which prints their real output shapes; the quality tests plant qmx-ci's own `tools/ci` (`tests/repo_ci/`, origin/ci/c2 at 812b87c98, byte for byte) and `ci/baselines/` in the fixture repo, and `tests/test_k4a.py` runs the same inputs through the kit and through `repo_ci/qci.py`'s own functions and asserts one verdict for Skylos, Vulture, types and flaky (refresh `repo_ci/` when CI's rules change); `pytest` must be installed for the slice-check, landing, nightly and quality tests. Every test's factory home is a temp folder (`factory_home` in the fixture's `ship.toml`), so no test touches the real `<factory_home>/run/`. `tests/test_dl22.py` holds the K3 fix round's checks: the hook's bypasses refused for every role, the review, merge, claims, chain and lock mutants, and the races. `tests/test_chain_chaos.py` is the chaos suite (U12, FACTORY-DESIGN section 13): one named scenario per row of the edge-case matrix, per loop of 3.9 (row 57) and per hand-off X1 to X10, run through `ship chain` with the harness in `tests/chaos.py` (faults: a hard kill after any activity, the remote gone, mains lost through a file `SHIP_FAKE_MAINS` names, a fake clock, a queued or red deep run, another program's merge on the target); its docstring holds the coverage table, rows another test covers name that test, and a scenario that shows a kit bug is an `expectedFailure` with the bug in one line. `DRILLS.md` holds the real-machine drills (13.5), done during U19.
