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
| 2 | MD2 | Every broker read says demo or live | MD1 | an account read from a demo connection carries `environment: demo` |
| 3 | MD3 | The old-data import labels what it cannot prove | none | a bucket run with no mode imports as `unknown` |

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

Audit H2, H3, H4, M6, L6 and L8. Rulings 141 and 142 (his data lives in one place, and nothing he relies on is a stand-in). Today eight template scripts open `E/ports/library_fake.py`'s hidden `engine/library-fake.sqlite`, because a script child has no way into the host's Library. `crystallise-a-workflow` reads its shipped fixtures on every run, and the runner falls back to the fake Library when it has no memory. Real step none. Done when no production path opens `LibraryFake`. Template scripts then read the real Library read-only and hand their writes to the runner, which stores them through the host's `LibraryPort` as `run:<run_id>`. A clipping, a lineage edge and a digest come from or land in the Library he sees. `crystallise-a-workflow` reads the target workflow's real runs or refuses with "no replays yet", and reads fixtures only when its input asks for one.

**Depends on.** The root `4dd2c5c6`.

**Files.**

- [ ] Edit `E/nodes/script.py` and `E/runner.py` (a script's JSON output may carry a `library` list of writes, `put_artifact` with type, metadata and an intent key, which the runner stores through the port, idempotent per run and node; the fake-Library fallback near the memory port goes), and `E/ports/memory.py` (a missing provider is named, not silent).
- [ ] Edit the scripts of `T/morning-digest/`, `T/clippings-into-research/`, `T/revolution-loop/` (`lineage.py` and `revolution/scripts/brief.py`), the six `lineage.py` copies (`b-build-and-prove`, `bc-build-a-component`, `d3-iterate-against-qmb`, `d4-variant-comparison`, `l1-idea-to-first-result`, `p1-portfolio-combination`) and `T/crystallise-a-workflow/` (`scripts/replays.py`, `scripts/batch.py`, `definition.json`).
- [ ] Reads open the Library's own store read-only through `qmx_library` on the folder's `data/library` (LF3's read-only opener), never the writer.
- [ ] Keep `E/ports/library_fake.py` for tests only, with a test that no module under `E/` outside `tests/` imports it.
- [ ] Add tests in the engine package.

**Build.**

- [ ] Add the runner's Library write from script output.
- [ ] Move every template read to the real Library and the run ledger, and every write to the runner.
- [ ] Make `crystallise-a-workflow` read real replays or refuse by name.

**You see.**

- [ ] On a throwaway folder, "Clippings into research" stores a clipping that the Library screen's search route finds, and the morning digest lists it the next morning.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A script's `library` writes land once through a recording port, even on a retried attempt; no production module imports `LibraryFake`; `crystallise-a-workflow` with no replays refuses with "no replays yet". Run the engine, host and Library suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The three suites at parent and head. Save `md1-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host on a throwaway folder runs "Clippings into research" on two clippings. Save `md1-clippings.log`. Pass when `/api/library` search finds both and no `library-fake.sqlite` exists.
- [ ] Lane 3. The morning digest after lane 2. Save `md1-digest.log`. Pass when it lists the two clippings.
- [ ] Lane 4. `crystallise-a-workflow` on a workflow with no runs, then on one with three. Save `md1-crystallise.log`. Pass when the first refuses by name and the second reads those three runs.
- [ ] Lane 5. "Revolution loop" one round. Save `md1-lineage.log`. Pass when its lineage edges are in the real Library.
- [ ] Lane 6. A rerun of lane 2's run id. Save `md1-idempotent.log`. Pass when no clipping is stored twice.
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

Audit M5. Ruling 135 (live-trading keys only on a trading server) and his standing rule that he never reads a demo number as his own. Today `BR/service.py`'s `read` returns what the adapter gives, and only `list_accounts` and `list_connections` carry `environment`; a demo balance reaches an agent with no label. Real step none. Done when every broker read result, account state, positions, orders and history, carries `environment` (`demo` or `live`) and, for cTrader, the account's `isLive`, and the agent-facing tool text says "demo" beside every money figure from a demo account.

**Depends on.** The root `4dd2c5c6`.

**Files.**

- [ ] Edit `BR/service.py` (`read` and every read that returns money), `BR/adapters.py` (cTrader near lines 180 to 197, CCXT near 327 to 333, carrying the account kind through), `BR/models.py` (the result types).
- [ ] Edit the agent-facing tool text in `TL/` that renders a broker read, if any renders one.
- [ ] Add tests in the broker and tools packages.

**Build.**

- [ ] Stamp the account kind on every read result.
- [ ] Say "demo" in the tool text beside every figure from a demo account.

**You see.**

- [ ] A chat that reads the demo account's balance answers with "demo" in the same line as the number.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A cTrader demo read and a CCXT sandbox read each carry `environment: demo`; a live read carries `live`; a read whose kind is unknown says `unknown`, never `live`. Run the broker, tools and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The three suites at parent and head. Save `md2-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host with a fake cTrader endpoint (demo account) answers the account read route. Save `md2-read.log`. Pass when the result carries `environment: demo` and `isLive: false`.
- [ ] Lane 3. The tool text for that read. Save `md2-tool.log`. Pass when "demo" sits beside the balance.
- [ ] Lane 4. A CCXT sandbox read through the fake exchange. Save `md2-ccxt.log`. Pass when it carries `environment: demo`.
- [ ] Lane 5. A read with no account kind. Save `md2-unknown.log`. Pass when it says `unknown`.
- [ ] Lane 6. Positions and history reads. Save `md2-reads.log`. Pass when each carries the kind.
- [ ] Lane 7. Grep lane logs for key values. Save `md2-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `md2-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the touched packages. Save `md2-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the throwaway folder and list processes. Save `md2-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds for one account read through the fake endpoint.
- [ ] Probe. Lane 2.
- [ ] Baseline. The same read at the parent.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on MD1 by a merge commit (the two share no file).

## The old-data import labels what it cannot prove (MD3)

Audit M8. Rulings 141 and 142. Today `LB/migrate/from_bucket.py` imports a bucket run with no recorded mode as `mode: "live"`, and `LB/migrate/from_library_b.py` filters old test rows by 16 fixed ids only, so other test rows import as his. LF4's bring-in calls this switch on his real first start. Real step none (his first start, after landing). Done when a run with no recorded mode imports as `unknown`, rows written by a `run:` principal or titled like a test lane are counted and named in the bring-in report under "made by test runs", imported off `main` (onto a `refs/imported/test-runs` ref he can open), and nothing is deleted.

**Depends on.** MD2 (stack order only; no shared file).

**Files.**

- [ ] Edit `LB/migrate/from_bucket.py` (a missing mode is `unknown`) and `LB/migrate/from_library_b.py` (the test-row rule beside the 16 ids, and the ref they land on).
- [ ] Edit `HO/bring_in.py` (the report's "made by test runs" line counts these rows and names the ref).
- [ ] Add tests in the Library and host packages.

**Build.**

- [ ] Change the missing-mode default.
- [ ] Add the test-row rule and its ref.
- [ ] Count and name them in the report.

**You see.**

- [ ] On a synthetic old folder, the bring-in report says how many test-run items it found and where they are.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A bucket run with no mode imports as `unknown`; a row by `run:lane-x` lands on the test-runs ref and not on `main`; the report counts it. Run the Library and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The two suites at parent and head. Save `md3-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. LF4's lane 2 on a synthetic old folder holding two test-lane rows and one bucket run with no mode. Save `md3-bringin.log`. Pass when the report counts the two, the run reads `unknown`, and the old folder is unchanged.
- [ ] Lane 3. Library search on the new folder for a test-lane title. Save `md3-search.log`. Pass when `main` does not return it and the test-runs ref does.
- [ ] Lane 4. LF4's real-folder lane (an LF1-era host's flat home) through the head. Save `md3-real.log`. Pass when it still brings in and a head host lists the old chat.
- [ ] Lane 5. A rerun of lane 2. Save `md3-rerun.log`. Pass when it returns the same report.
- [ ] Lane 6. An old folder with no test rows. Save `md3-clean.log`. Pass when the report has no test-run line.
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
- On the tip `4dd2c5c6`, `LibraryFake` is imported by `E/runner.py`, `E/service/api.py` and the eight template scripts; no other path from a script child into the Library exists (`E/nodes/script.py` passes only `QMX_*` variables).

## Appendix B. Not in this program

The UI findings (UI session). L3 and L4 (run cards showing "fake" and "test (sample data)") need the UI. L5, L7, L9, L10 and M7 are developer paths or examples he must install by hand; they stay in `BACKLOG.md`.

## Appendix C. Files two PRs share

| Pair | Shared file | Order |
|---|---|---|
| MD1, MD2 | none | in parallel |
| MD2, MD3 | none | MD2 first (stack order) |
| MD1, MD3 | none | MD1 first (stack order) |

## Appendix D. Defaults

- No hourly tick. Claude's default.
- A read with no account kind says `unknown`, never `live`. Claude's default, from his rule that he never reads a demo number as his own.

## Appendix E. Gates and calls

- G-LAND. He lands the stack himself.
