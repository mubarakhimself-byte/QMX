# QMX mock data out of the live paths, build program

This program removes the fake, sample and canned data that the audit of 2026-10-26 found on paths he will use live (`D:/QMX-worktrees/qma-ship/wrapup/evidence/mock-data-audit-2026-10-26.md`, 4 high, 8 medium, 14 low).
He asked for it on 2026-10-26 ("mock data might become a problem, especially when we start using the live system") and ruled that it runs after the local-first program, through the usual plan, check and review.
There are 3 PRs. MD1 makes the engine's templates read and write the real Library and real run history. MD2 makes every broker read say demo or live. MD3 makes the old-data import label what it cannot prove.
The stack roots on `build/lf4` at `4dd2c5c6`, the CLEAN tip of the local-first stack, where `just ci` passed with 0 failures.
The audit's UI findings (H1, M1 to M4, L1, L2, L11 to L13) belong to the UI session on `ui-review/repair` and go to its handoff, not to this stack.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a test run, or a SHA. The body is a how-to. The appendices explain and record.

Each PR section opens with a preamble naming the audit findings it closes, the rulings it serves, its real step and its done line. Then come the nine blocks `check-plan.mjs` requires.

Path shorthands are those of `LOCAL-FIRST-PLAN.md` "How to read this". `QA/` is `qmx-agents/packages/`, `E/` the engine source, `T/` its templates, `HO/` the host source, `BR/` the broker, `LB/` the Library, `TL/` the tools.

The store is `D:/QMX-worktrees/qma-ship/wrapup/` (the same one the local-first program used), with `QUEUE.md`, `BRIEF-BUILDER.md`, `REVIEWER-BRIEF.md`, `RESUME.md`, `BACKLOG.md`, `lows.md`, `ledger.tsv`, `dispatch/`, `review/` and `evidence/`.

The program follows `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md` with the overrides of `LOCAL-FIRST-PLAN.md`. Builders are Claude Opus 5.5 (`poteto-agent`, `model: opus`), at most two at once, never two on shared files. A fresh Opus reviewer agent reviews every diff and runs `bmad-review-edge-case-hunter` on any PR that touches data, the Library or connections; the coordinator runs the suites, `just ci` and the lanes in the background and allows one fix round. Low findings go to `lows.md`; anything new goes to `BACKLOG.md`. See `playbooks/` in the poteto-mode skill for the rest.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] Confirm the shell (Windows 11, PowerShell 7.6 and Git Bash; in PowerShell `$H` and `$h` are one variable) and the root (`git rev-parse origin/build/lf4` is `4dd2c5c6`). Logged in `RESUME.md`.
- [ ] Read the trunk rules with `git show origin/main:CLAUDE.md`, then the rulings file `research/methodology/26-operator-rulings-and-alignment.md` (rulings 136 to 145), then the audit file named above.
- [ ] No hourly `/loop 1h` tick, because builder and background-job notifications wake the coordinator. Post a short status message to the operator only when a PR opens, a verdict lands or a blocker appears.
- [ ] Never stop to ask him during the build. Stop only for a credential, a real ambiguity in this plan, or a step only he can do (`QUEUE.md`).

### Spawn owners

| # | Id | PR | Runs beside | Proving check |
|---|---|---|---|---|
| 1 | MD1 | Templates use the real Library and real runs | MD2 | a clipping stored by a template run is found by Library search |
| 2 | MD2 | Every broker read says demo or live | MD1 | an `account_state` read from a demo connection carries `environment: demo` |
| 3 | MD3 | The old-data import labels what it cannot prove | none | a test-lane item is archived, and search leaves it out |

- [ ] Spawn one fresh Opus builder per PR in the background with `subagent_type: poteto-agent` and `model: opus`, from a dispatch file saved in `dispatch/`. Its first words are exactly "Read the poteto-mode skill's SKILL.md in full, including its Principles section, before any work. Do not spawn sub-agents."
- [ ] Record the empty Files intersection of MD1 and MD2 in `ledger.tsv` before the second dispatch (Appendix C).
- [ ] No PR touches `apps/qmx-ui/`, `~/.claude`, his real home `~/.qmx`, `C:/Users/Mubarak/Documents`, `C:/Users/Mubarak/Desktop/DATA_NARL`, or any vault value. Lanes run on throwaway folders and a scratch profile only.

### PR mechanics, for every PR

- [ ] The coordinator creates `build/<id>` from the right parent in `D:/QMX-worktrees/bld-<id>` before the dispatch. Never `git stash`.
- [ ] The builder opens the PR ready with `gh pr create --base <parent-branch> --head build/<id> --repo MubarakHimself/QMX`.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Set `TMP` and `TEMP` to `D:/Temp`, `UV_CACHE_DIR` to `D:/Caches/uv`, and put `D:/Tools/rclone` on `PATH`.
- [ ] The builder runs `fmt-check`, `lint` and `types` in each package it touched and `tools/secret_scan.py`, reads each exit code, runs only the fast tests it added or changed, and never waits on a long command. It runs the `blast-radius` skill on its diff before the last push.
- [ ] Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. PR bodies end with the Claude Code line.

### Verdict and merge, for every PR (append to the stack, merge on his go)

- [ ] At the code-ready head the coordinator runs the touched suites with `-n 2` and lanes 1 to 4 in the background, reads every package block of each log (not its tail), and saves the logs. A fresh Opus reviewer agent (one per PR, `model: opus`, told not to spawn sub-agents) reads the PR section, the full diff, the edge-case lens where the PR touches data, the Library or connections, and those logs, and writes `review/<id>-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] Blockers go back to the same builder for one fix round. Low findings go to `lows.md`.
- [ ] `ledger.tsv` gets head, parent and patch-id.
- [ ] `just ci` runs at the stack tip once at the end, with `D:/Tools/rclone` on `PATH`, under `D:/QMX-worktrees/.ci-lock`.
- [ ] Stacks join with merge commits, never a rebase. He lands the stack himself from the one full list the coordinator sends when `QUEUE.md` is empty.

### Boot recipe, for every live lane

- [ ] `git worktree add --detach D:/Temp/<id>-check <head>`, then `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`.
- [ ] A lane runs on a throwaway QMX folder under `D:/QMX-worktrees/qma-ship/wrapup/homes/<id>-<lane>/`, made with `qmx_home.resolve(..., create=True)`, with `USERPROFILE`, `APPDATA`, `LOCALAPPDATA` and `HOME` on a scratch profile under the same folder.
- [ ] A lane that starts a host injects its bearer and turns the memory database off (`hindsight_runs` patched), because on Windows pg0 writes his real profile (design 62 L7).
- [ ] Save captures as `evidence/<id>/check-<slug>.log`, then remove the check copy with `git worktree remove` and confirm no `qmx_host`, `claude` or `node` process from the lane is left.

## Templates use the real Library and real runs (MD1)

Audit H2, H3, H4, M6, L6 and L8, with the plan review `review/plan-mock-data-edge-cases.md` (MD1 items 1 to 19). Rulings 141 and 142 (his data lives in one place, and nothing he relies on is a stand-in). Today ten template scripts in nine templates open `E/ports/library_fake.py`'s hidden `engine/library-fake.sqlite`, because the host holds the Library's single writer lock (`LB/store.py` `writer.lock`), so a script child that finds the folder through `home_of(QMX_WORK_SHARED)` can only open the fake file. `E/service/api.py`, `E/control_door.py` and `E/__main__.py` (`run`, `resume`) still fall back to the fake when no Library is given, and the runner does too when it has no memory. `crystallise-a-workflow` reads its shipped fixtures on every run. Real step none. Done when no production path opens `LibraryFake`; the runner serves every template Library read and write through the host's `LibraryPort`, stamped `run:<run_id>` on `refs/runs/<run_id>`; a test, fake or failed run's writes never reach `main`, the digest or another run's duplicate check; the digest lists what moved onto `main` since his cursor; and `crystallise-a-workflow` reads real live replays of a named workflow step or refuses with "no replays yet".

**Depends on.** The root `4dd2c5c6`.

**Files.**

- [ ] Edit `E/nodes/script.py` and `E/runner.py` (the served reads and writes below; the runner's fake-Library fallback goes), `E/ports/memory.py` (a missing provider is named, not silent), `E/ports/library.py` (`RunSummary` carries `fake`), `E/service/api.py`, `E/control_door.py` and `E/__main__.py` (no fake default; `run` and `resume` open `home_library(home)` or refuse by name), `E/trace_export.py` (each write receipt is linked `produced-by` to the run summary at run end, as `run_files` does).
- [ ] Edit `LB/adapter.py` (`_land` lands nothing for a fake run's summary, and a `find_by_write_key` read beside `find_by_intent`, over `Store.with_field`), `LB/store.py` (a query for objects moved onto `main` after a sequence, since `placements()` lists only first placements), and `E/ports/library.py` and `E/ports/library_fake.py` (the new port verbs, so the fake still satisfies the port in tests).
- [ ] Edit `qmx-control/src/qmx_control/service.py` (the digest cursor records the store it counts in; a cursor with no store tag, or above the real `last_seq`, resets once to 0 with a log line).
- [ ] Edit the scripts of `T/morning-digest/` (`collect.py`, `assemble.py`, `advance.py`), `T/clippings-into-research/` (`write.py`, `dedupe.py`), the seven `lineage.py` copies (`revolution-loop`, `b-build-and-prove`, `bc-build-a-component`, `d3-iterate-against-qmb`, `d4-variant-comparison`, `l1-idea-to-first-result`, `p1-portfolio-combination`), `T/revolution-loop/revolution/scripts/brief.py`, and `T/crystallise-a-workflow/` (`definition.json`, `scripts/replays.py`, `scripts/batch.py`).
- [ ] Keep `E/ports/library_fake.py` for tests and dev lanes only. Engine tests that relied on the default pass it explicitly. `scripts/live/*` users of it are dev lanes (Appendix B).
- [ ] Add tests in the engine, Library and control packages, run against `EngineLibraryAdapter(Store.open(tmp))` (a real store), not a recording port.

**Build.**

- [ ] Served reads. A script node declares what it reads (`parameters.library_reads`, for example `moved_to_main_after: <cursor>` or `find_by_intent: [keys]`), and the runner answers through the host's `LibraryPort` into the script's stdin before the child starts. No script opens `<folder>/data/library`. This works the same on a stand-in place.
- [ ] Served writes. A script's JSON output may carry `library`, a list of `put_artifact` and `link` writes. A write's body is a file under the attempt's overlay (`body: "library/<name>"`), never inline bytes. At node finish the runner:
  - [ ] ignores any `principal`, `run_id` or `ref` in a write and stamps `run:<run_id>` on `refs/runs/<run_id>`;
  - [ ] keys idempotence by slot (`run:node:iteration:partition`, never the attempt) and write index, writing `metadata.write_key = <slot>:<index>` in the same put, and before each write looks the key up on the run ref, skipping and returning the object it finds;
  - [ ] prefixes each intent key with the workflow item (`<workflow_item>|<key>`) and never uses it for its own idempotence;
  - [ ] accepts a `link` only from a write of the same slot (by local handle, `"as": "intake"` then `"$intake"`), never with edge `produced-by`, `run-of` or `tested-by`, and only to an object that exists;
  - [ ] removes `library` from the outputs before `node_finished`, records only receipts, and returns `library_written: [{handle, object_id, refused}]` in the node's outputs;
  - [ ] fails the node with the store's own refusal named (`disk_full`, `read_only_replica`), with `retryable=False`, and adds no QMX cap.
- [ ] Test, fake and failed runs. In a `test`-mode or fake run the writes stay on its run ref, the digest never reads them, and `advance.py` does not move the cursor (`QMX_MODE == "test"` or `QMX_FAKE == "1"`). `put_run_summary` lands nothing for a fake run. The digest reads moves onto `main` after the cursor, not first placements. Duplicate checks go through `find_by_intent`, which counts only passed runs.
- [ ] `crystallise-a-workflow` takes inputs `workflow` (item), `node` (the agent step) and a `batch` source. Its replays are that node's `node_finished` outputs in that workflow's runs, read from the ledger, where `run_created.fake` is not true, `mode` is `live` and `status` is `passed`, for the published version's content hash. With none it refuses with "no replays yet (N fake or test runs left out)". A step whose outputs are not `{item_id, title, label}` is refused by name. Any truthy `fixture` selects the fixture path, so the install test still passes.
- [ ] `brief.py` lists `fixture:revolution-loop` as a source only when `fixture` is set, and fails with `[QMX_FAILURE] no idea given` when `idea` is empty.

**You see.**

- [ ] On a throwaway folder, "Clippings into research" stores a clipping that the Library search route finds, and the morning digest lists it after the run lands.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Against a real store, a retried attempt (attempt 2 of the same slot) writes nothing twice; a run that fails after write 2 of 3 and is retried writes only write 3, and nothing from the failed run reaches the digest; a test-mode run leaves the cursor and the digest alone; a fake live run lands nothing; a forged principal, ref or `produced-by` link is ignored or refused; a template read runs while the host's `Store` is open; `EngineService.open(home)` with no Library refuses; no production module imports `LibraryFake`; a fake-seq cursor resets once; `crystallise-a-workflow` with no replays refuses with "no replays yet". Run the engine, control, host and Library suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The four suites at parent and head. Save `md1-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host on a throwaway folder runs "Clippings into research" on two clippings. Save `md1-clippings.log`. Pass when Library search finds both after the run lands and no `library-fake.sqlite` exists.
- [ ] Lane 3. The morning digest after lane 2, with a cursor left holding a fake-file seq. Save `md1-digest.log`. Pass when the cursor resets once and the digest lists the two clippings.
- [ ] Lane 4. `crystallise-a-workflow` on a workflow step with no runs, then on one with three runs, one of them fake. Save `md1-crystallise.log`. Pass when the first refuses by name and the second reads only the two real runs.
- [ ] Lane 5. "Revolution loop" one round. Save `md1-lineage.log`. Pass when its lineage edges are in the real Library and its links carry the returned ids.
- [ ] Lane 6. Kill the engine after the write node's attempt and before `node_finished`, then resume the run. Save `md1-idempotent.log`. Pass when no clipping is stored twice.
- [ ] Lane 7. Grep lane logs for key values. Save `md1-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `md1-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the touched packages. Save `md1-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the throwaway folder and list processes. Save `md1-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for a 50-clipping "Clippings into research" run.
- [ ] Probe. Lane 2 with 50 clippings.
- [ ] Baseline. The same run at the parent (into the fake file).
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on `build/lf4`.

## Every broker read says demo or live (MD2)

Audit M5, with the plan review (MD2 items 1 to 5). Ruling 135 (live-trading keys only on a trading server) and his standing rule that he never reads a demo number as his own. Today `BR/service.py` `read` serves `account_state`, `positions`, `quotes`, `bars` and `symbol_info` as plain dicts and lists; only `list_accounts` and `list_connections` carry `environment`, so a demo balance reaches an agent through `BR/server.py` and the harness with no label. `Connection.environment` is `demo` or `live` (default `demo`), and cTrader's sign-in already keeps only accounts whose `isLive` matches. Real step none. Done when every one of the five reads returns one envelope, `{environment, is_live, connection_id, account_id, result}`, stamped from the connection the read resolved and the adapter's proven `isLive` (a disagreement fails the read by name); the kind survives the harness's paging and spill; and the tool descriptions the model reads say a figure from a demo account is demo.

**Depends on.** The root `4dd2c5c6`.

**Files.**

- [ ] Edit `BR/service.py` (`read` returns the envelope, stamped from the same resolved connection; a cached CCXT adapter for `demo` is never reused for `live`), `BR/adapters.py` (the cTrader adapter keeps the `isLive` its `authenticate` saw), `BR/models.py` (the read envelope type) and `BR/server.py` (the tools' return types become the envelope).
- [ ] Edit `qmx-control/src/qmx_control/catalog.py` (the broker rows' descriptions near lines 226 to 231) and `qma-harness/src/qma/harness/tools.py` (`_paged` and `spill` keep `environment` on every page and on the spill pointer).
- [ ] Add tests in the broker, harness and control packages.

**Build.**

- [ ] Add the envelope and stamp all five reads.
- [ ] Keep the kind through paging and spill, and in the catalog descriptions.

**You see.**

- [ ] The broker `account_state` tool's text for a demo account carries `environment: demo` beside the balance. Whether a model repeats "demo" in its own words is its choice; a chat that drops it is logged to `BACKLOG.md`, not a blocker.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A cTrader demo read and a CCXT sandbox read carry `environment: demo`; a live read carries `live`; flipping a connection's environment between two reads stamps each read with its own kind; a cTrader `isLive` that disagrees with the connection fails the read by name; a re-proposed order after a switch gets a new `proposal_id`. Run the broker, harness and control suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The three suites at parent and head. Save `md2-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. The broker `account_state` tool through `create_server(BrokerService(home, settings, factory=<fake cTrader>))` on a demo connection. Save `md2-read.log`. Pass when the envelope carries `environment: demo` and `is_live: false`.
- [ ] Lane 3. The same read and a long `bars` read through the harness's tool wrapping. Save `md2-tool.log`. Pass when the kind is on the text, on every page and on the spill pointer.
- [ ] Lane 4. A CCXT sandbox read through a fake exchange. Save `md2-ccxt.log`. Pass when it carries `environment: demo`.
- [ ] Lane 5. A connection switched from demo to live between two reads. Save `md2-switch.log`. Pass when each read carries its own kind and the CCXT cache is not reused.
- [ ] Lane 6. `positions`, `quotes` and `bars` reads. Save `md2-reads.log`. Pass when each carries the kind.
- [ ] Lane 7. Grep lane logs for key values. Save `md2-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `md2-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the touched packages. Save `md2-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the throwaway folder and list processes. Save `md2-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds for one `account_state` read through the fake endpoint.
- [ ] Probe. Lane 2.
- [ ] Baseline. The same read at the parent.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on MD1 by a merge commit (the two share no file).

## The old-data import labels what it cannot prove (MD3)

Audit M8, with the plan review (MD3 items 1 to 5 and fact e). Rulings 141 and 142. Today `LB/migrate/from_bucket.py` imports a bucket run with no mode as `live`, and the `workflow-run` schema allows only `live` and `test`; the bucket import runs through the server's `qmx-control node import`, not the bring-in. `LB/migrate/from_library_b.py` filters 16 fixed junk ids and imports every other old row onto `main`; old rows carry no principal. LF4's bring-in calls `from_library_b` on his first start. Real step none (his first start, after landing). Done when a bucket run whose mode is not `live` or `test` imports as `unknown`; Library B items whose `title`, `source` or `tags` match a named test-lane pattern list (kept beside `JUNK`, judged per `root_id`) import and are archived at once with `Store.archive(OPERATOR, item, reason="made by test runs")`, so search and recall leave them out and nothing is deleted; the bring-in report counts them on their own line and leaves them out of "Your Library"; and a folder brought in before MD3 gets the same archive once at host start.

**Depends on.** MD2 (stack order). It shares `E/ports/library.py` with MD1 (Appendix C).

**Files.**

- [ ] Edit `LB/kinds/workflow-run.schema.json` (`unknown` in `mode`), `LB/landing.py` and `E/ports/library.py` (the `Mode` values), and `LB/migrate/from_bucket.py` (any mode outside `live` and `test` is `unknown`).
- [ ] Edit `LB/migrate/from_library_b.py` (the test-lane pattern list beside `JUNK`, judged per `root_id`, then archived; fix-check 58 and N18 named, and why this rule archives rather than skips).
- [ ] Edit `HO/bring_in.py` (the report's "made by test runs" line, counted apart from `JUNK` and subtracted from "Your Library") and `HO/host.py` (a one-shot pass at host start archives matching items when the saved bring-in report has no `test_rule` stamp, appends the counts to the report, deletes nothing, and runs once per rule version).
- [ ] Add tests in the Library, control and host packages.

**Build.**

- [ ] Add `unknown` to the mode and map the bucket import to it.
- [ ] Add the pattern list and archive matching items per root.
- [ ] Count them in the report, and add the one-shot pass for folders brought in earlier.

**You see.**

- [ ] On a synthetic old folder, the bring-in report says how many items were made by test runs and that they are archived, not deleted.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `import_bucket` with no mode imports `unknown`; a test-lane item is archived with its whole version chain; search leaves it out and `include_archived=True` finds it; the 16 junk ids still show only the "remote-flow" line; a folder brought in at `4dd2c5c6` gets the one-shot archive once. Run the Library, control and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The three suites at parent and head. Save `md3-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. LF4's lane 2 on a synthetic old folder holding two test-lane items. Save `md3-bringin.log`. Pass when the report counts the two apart and the old folder is unchanged.
- [ ] Lane 3. Library search on the new folder for a test-lane title. Save `md3-search.log`. Pass when search does not return it and `include_archived=True` does.
- [ ] Lane 4. `qmx-control node import` on a throwaway store with a bucket run that has no mode. Save `md3-bucket.log`. Pass when the run reads `unknown`.
- [ ] Lane 5. A folder brought in at `4dd2c5c6`, then a head host started on it. Save `md3-oneshot.log`. Pass when the test-lane items are archived once and the report gains the count.
- [ ] Lane 6. The same old folder brought into a new empty folder. Save `md3-rerun.log`. Pass when the counts match lane 2.
- [ ] Lane 7. Grep lane logs for key values. Save `md3-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `md3-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the touched packages. Save `md3-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the throwaway folders and list processes. Save `md3-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds to bring in a 2,000-item old folder.
- [ ] Probe. Lane 2 with 2,000 items.
- [ ] Baseline. LF4's 92.7 s for 2,000 items.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on MD2.

## Close the program

- [ ] Every PR is stacked with a CLEAN verdict, or skipped with its reason in `RESUME.md`.
- [ ] `just ci` at the stack tip exits 0, or every failure is a named environmental gap.
- [ ] The UI findings are written into the UI session's handoff.
- [ ] `QUEUE.md` moves on to its next item.

## Appendix A. Prototype evidence

- The audit file named above, read at `44943f2b` (backend) and `eea09941` (UI).
- On the tip `4dd2c5c6`, `LibraryFake` is imported by `E/runner.py`, `E/service/api.py` and ten template scripts in nine templates, and reached through `library=None` from `E/control_door.py` and `E/__main__.py`. A script child finds the folder through `home_of(QMX_WORK_SHARED)`, but `Store.open` refuses while the host holds `writer.lock` (plan review, fact a).
- The plan review `D:/QMX-worktrees/qma-ship/wrapup/review/plan-mock-data-edge-cases.md` checked every fact against `4dd2c5c6` and set the MUST changes folded in here.

## Appendix B. Not in this program

The UI findings (UI session). L3 and L4 (run cards showing "fake" and "test (sample data)") need the UI. L5, L7, L9, L10 and M7 are developer paths or examples he must install by hand; they stay in `BACKLOG.md`. The `scripts/live/*` lanes that open `LibraryFake` (`e07_lifecycle.py`, `e10_library.py`, `e21_real_tests.py`, `e37_redaction.py`, `tpl3_templates.py`, `lib1_lanes.py`) are dev lanes and keep it.

## Appendix C. Files two PRs share

| Pair | Shared file | Order |
|---|---|---|
| MD1, MD2 | none (MD1 adds `qmx_control/service.py`, MD2 adds `qmx_control/catalog.py`) | in parallel |
| MD2, MD3 | none | MD2 first (stack order) |
| MD1, MD3 | `E/ports/library.py` (`RunSummary.fake`, the new verbs, the `Mode` values) | MD1 first |

## Appendix D. Defaults

- No hourly tick. Claude's default.
- A broker read whose stamp and proven `isLive` disagree fails by name. Claude's default, from his rule that he never reads a demo number as his own.
- Test-lane items are archived, never deleted or skipped. Claude's default, from ruling 141.

## Appendix E. Gates and calls

- G-LAND. He lands the stack himself.
