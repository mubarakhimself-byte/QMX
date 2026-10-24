# QMX wrap-up build program

This program fixes list A of `HANDOFF-2026-10-24.md` section 2, plus the small follow-ups that touch the same files, and adds the cTrader half of Connections on the operator's word of 2026-10-24.
After it lands, the data round's real steps run behind their gates, QMX boots on his real home, and the branches converge on `main`.
There are 10 PRs. Seven fix list A items 1 to 8, two build the cTrader sign-in and its reads, and one makes the server ready to be the Library's home.
The stack roots on `origin/engine/base` at `f05fc64b`, the merge of the whole data round (PRs 171 to 197), confirmed with `gh pr list` and `git fetch` on 2026-10-24.
Code truth for every Files block was read at `f05fc64b` on 2026-10-24 (Appendix A).

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a test run, or a SHA. The body is a how-to. The appendices explain and record.

Each PR section opens with a preamble. It names the list A item or follow-up it closes, the source backlog lines, its real step if any, its gate, and its done line. Then come the nine blocks `check-plan.mjs` requires.

Path shorthands are those of `DATA-PLAN.md` "How to read this". `QA/` is `qmx-agents/packages/`, `E/` the engine source, `H/` the harness source, `HO/` the host source, `QX/` the control source, `LB/` the Library, `HB/` the Hub, `R/` the router, `BR/` the broker, `TL/` the tools, `RM/` the remote worker, `AP/` the apps, `T/` the engine templates, `QB/` is `qmb/src/qmb/`, `SP/` is `scripts/probes/` and `SL/` is `scripts/live/`. Test folders follow the same names with a trailing `T` (`HT/`, `HOT/`, `ET/`, and so on) or the package's `tests/` folder.

The store is `D:/QMX-worktrees/qma-ship/wrapup/`. It holds `decisions.md` (the operator's decisions for this run), `BRIEF-BUILDER.md`, `RESUME.md`, `BACKLOG.md`, `lows.md`, `ledger.tsv`, `dispatch/`, `review/` and `evidence/`. Gates the operator must open are posted to `D:/QMX-worktrees/qma-ship/data/QUESTIONS-FOR-OPERATOR.md`.

The program follows `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md` with the overrides of `DATA-PLAN.md` "How to read this", changed as follows. Builders are Claude Opus 5.5 (`model: opus`, agent type `poteto-agent`), at most two at once, one builder per chain of related PRs. The coordinator checks each PR itself with no checker agent, one build and one check per PR and one fix round. Lanes 1 to 4 are the proving set, lanes 5 to 10 a menu, and model turns in lanes run on haiku through the ship home's plan login (ruling 105). Low findings go to `lows.md` and never block. Anything new goes to `BACKLOG.md` (no unplanned work). See `playbooks/` in the poteto-mode skill for the rest.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] Confirm the shell. The PC runs Windows 11 with PowerShell 7.6 and Git Bash, the server Ubuntu 24.04 with bash. Logged in `RESUME.md`.
- [ ] Confirm the root. `gh pr list --repo MubarakHimself/QMX --state all --limit 60` shows 171 to 197 merged into `engine/base`, and `git rev-parse origin/engine/base` is `f05fc64b`. Logged in `RESUME.md`.
- [ ] Read the trunk rules with `git show origin/main:CLAUDE.md`, then the uncommitted QMA v2 section in `C:/Users/Mubarak/Desktop/QMX/CLAUDE.md`, which is newer.
- [ ] Read the rulings file `research/methodology/26-operator-rulings-and-alignment.md` (the latest ruling wins) and the store's `decisions.md`.
- [ ] Run the baseline `just ci` at the root in a detached check copy under `D:/Temp/wrapup-ci0`, in the background, and save `evidence/ci0-f05fc64b.log`. Its failures are the parent set every PR is compared with.
- [ ] Measure the disks. On 2026-10-24 C had 22.4 GB free and D had 65.4 GB. Below 3 GB free on D, one builder at a time.
- [ ] No hourly `/loop 1h` tick in this program. The coordinator is woken by builder and background-job notifications, so a tick would only spend usage. Recorded in `decisions.md`.
- [ ] Post a short status message to the operator in chat only when a PR opens, a verdict lands, a gate opens or a blocker appears.

### Spawn owners

The table is the build order. Two builders run at once only when their Files blocks share no file (Appendix C). Each PR branches from the stack tip at dispatch. A parallel PR is rebased onto the tip when it is stacked, and keeps its verdict only when `git patch-id --stable` is unchanged.

| # | Id | Chain | List A | PR | Runs beside | Proving check |
|---|---|---|---|---|---|---|
| 1 | WU1 | harness | 2, 6 (tool row) | Mini-app tools reach a chat | WU5 | harness tool-row test green |
| 2 | WU5 | engine | 5 | Templates install into the real Library | WU1 | install visible through the Store |
| 3 | WU2 | harness | 3 | Test providers from a chat, serve `library_mark` | WU6 | chat-wire row Test answers ok |
| 4 | WU6 | engine | 6 | `just ci` green | WU2 | `just ci` exit 0 apart from named gaps |
| 5 | WU3 | harness | 4 | Skip providers with no key, drop disabled sub-agents | WU7 | missing-key row skipped |
| 6 | WU7 | engine | 8 | The Hub counts real copies per blob | WU3 | unpushed blob answers 1 copy |
| 7 | WU4 | harness | 1 | Agent backtests run and land | WU8 | a backtest lands one result |
| 8 | WU8 | broker | added | The cTrader demo sign-in | WU4 | receiver forwards and keeps nothing |
| 9 | WU9 | engine | 7 | The server is ready to be home | none | setup sequence and one root |
| 10 | WU10 | broker | added | cTrader reads through the server, broker history | none | a forwarded read after a refresh |

- [ ] Spawn one Opus builder per chain in the background with `subagent_type: poteto-agent` and `model: opus`. The prompt is `PROMPT-DATA.md`'s builder template, filled from this plan, pointing at the store's `BRIEF-BUILDER.md`, saved as `dispatch/<id>.md` before it is sent. It says "Do not spawn sub-agents."
- [ ] Record the empty Files intersection of each parallel pair in `ledger.tsv` before the second dispatch.
- [ ] No PR touches `apps/qmx-ui/`, `~/.claude`, his real home `~/.qmx`, `C:/Users/Mubarak/Documents`, `C:/Users/Mubarak/Desktop/DATA_NARL`, or any vault value.
- [ ] WU10 is skipped until gate G-CT opens (Appendix E). WU9 waits for WU4 to be stacked, because both edit `HO/host.py`.

### PR mechanics, for every PR

- [ ] The coordinator creates branch `build/<id>` from the stack tip in the worktree `D:/QMX-worktrees/bld-<id>` before the dispatch. Never `git stash`.
- [ ] The builder opens the PR ready with `gh pr create --base <parent-branch> --head build/<id> --repo MubarakHimself/QMX`.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Set `TMP` and `TEMP` to `D:/Temp` and `UV_CACHE_DIR` to `D:/Caches/uv`.
- [ ] The builder runs `fmt-check`, `lint` and `types` in each package it touched (not only the workspace root, data BACKLOG DR6) and `tools/secret_scan.py`, and reads each exit code. It runs only the fast tests it added or changed. It never waits on a long command.
- [ ] Before opening the PR, the builder runs the `blast-radius` skill on its diff and saves the result as `evidence/<id>/owner-blast-radius.md`. Where a seam moves (WU4's landing and door, WU8's code exchange, WU9's pass secret), it reads the `codebase-design` skill first and names the seam in the PR body.
- [ ] Add only the tests that prove the PR's point, at the public interface, with literal expected values.
- [ ] Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. PR bodies end with the Claude Code line.

### Verdict and merge, for every PR (append to the stack, merge on his go)

- [ ] At the code-ready head the coordinator reads the full diff, then runs the touched suites with `-n 2` and lanes 1 to 4 in the background, and reads every exit code. It writes `review/<id>-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] Blockers go back to the same builder for one fix round. Low findings go to `lows.md`.
- [ ] `ledger.tsv` gets head, parent and patch-id.
- [ ] The coordinator runs the full `just ci` twice in the program, at WU6's head and at the stack tip, under the lock `D:/QMX-worktrees/.ci-lock`, with `D:/Tools/rclone` on `PATH` (Appendix D).
- [ ] Nobody merges until the operator says go, once for the whole stack or per PR. `main` moves only by his click.

### Boot recipe, for every live lane

- [ ] `git worktree add --detach D:/Temp/<id>-check <head>`, then `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`.
- [ ] A lane with no model runs on a throwaway home under the store's `homes/<id>-<lane>`. A lane with a model uses the ship home `D:/QMX-worktrees/qma-ship/home` on haiku, holding `D:/QMX-worktrees/.engine-lane-lock`.
- [ ] Never name a PowerShell variable `$home`. Assert every lane home starts with `D:/QMX-worktrees/qma-ship/wrapup/homes/` or `D:/Temp/` before a host starts.
- [ ] Save captures as `evidence/<id>/check-<slug>.log`. Remove the lock and the check copy with `git worktree remove` after the verdict, and confirm no `qmx_host`, `claude` or `node` process from the lane is left.

## Mini-app tools reach a chat (WU1)

Closes list A item 2 and the harness tool-row half of item 6. Sources are build BACKLOG APP2a and PACK, and data BACKLOG DR10 and DEL2R. The Library sink is already attached (`QX/service.py:1420`). Real step none. Gate none. Done when `tool_defs` serves one MCP server per enabled app toolset and `apps_admin_move`, a pinned or profiled `app_op` node runs, and a newly published pack reaches a new chat without a restart.

**Depends on.** The root `f05fc64b`.

**Files.**

- [ ] Edit `H/tools.py` (`tool_defs` gains the `app_server` branch and feeds `rows(apps=...)`) and `HT/test_tools.py`.
- [ ] Edit `QX/service.py` (`app_job` takes `pin` and `profile` and passes them to `run_job`) and `E/control_door.py` (line 294 passes `dispatch`).
- [ ] Edit `HO/sessions.py` (`PackLanding.__call__` calls `materialise_packs` after the put).
- [ ] Add one pinned `app_op` test in `ET/` and one publish test in `HOT/`.

**Build.**

- [ ] Bind each enabled app's toolset as one `create_sdk_mcp_server`, forwarding to `control.app_runtime().call`, and bind `apps_admin_move` to the supervisor's move.
- [ ] Thread pin and profile through `app_job`.
- [ ] Materialise a pack on publish.

**You see.**

- [ ] On a throwaway home, a new chat lists an enabled example app's tools, and a pack published a minute ago shows its skills in the next chat.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `HT/test_tools.py::test_the_real_tool_list_builds_and_derives_the_gate` passes (it failed 77 against 78 at the root). The new `app_op` and publish tests pass. Run the harness, control, engine and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The four suites at parent and head. Save `wu1-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A chat on haiku calls one tool of `examples/apps/exchange-status`. Save `wu1-app-call.log`. Pass when the call returns the app's answer.
- [ ] Lane 3. A workflow with a pinned `app_op` node runs. Save `wu1-pinned.log`. Pass when the node settles ok, not `pin_unsupported`.
- [ ] Lane 4. Publish a pack, then open a new chat. Save `wu1-publish.log`. Pass when the chat's skill list holds the pack's skills with no restart.
- [ ] Lane 5. `apps_admin_move` from a chat on a throwaway app. Save `wu1-move.log`. Pass when the app moves.
- [ ] Lane 6. Disable the app, open a new chat. Save `wu1-disabled.log`. Pass when its tools are gone.
- [ ] Lane 7. Grep the chat journal for key values. Save `wu1-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `wu1-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the four packages. Save `wu1-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Processes after the lanes. Save `wu1-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from publish to the pack's skills in a new chat.
- [ ] Probe. Lane 4.
- [ ] Baseline. A host restart at the root.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the tip.

## Templates install into the real Library (WU5)

Closes list A item 5 and three engine follow-ups in the same files. Sources are data BACKLOG RUN1C and DR6, build BACKLOG TPL1. Real step the weekly backup trigger enabled on his real home after the first boot. Gate none. Done when `python -m qmx_engine templates install` lands into the Store the host serves, through the running host's door when one runs, `--template <id>` installs one template, a `[QMX_FAILURE]` reason survives an exit code of 1, and a feed's new items land as Library `source` items through `save_source`.

**Depends on.** The root `f05fc64b`.

**Files.**

- [ ] Edit `E/__main__.py` (`--template`, repeatable, and the host route call) and `E/service/api.py` (no silent `LibraryFake` fallback outside tests).
- [ ] Add the route `POST /api/templates/install` in `HO/door.py`.
- [ ] Edit `E/nodes/script.py` (read the marker on either exit code).
- [ ] Edit `T/feed/land.py` (call `T/_shared/save_source.py`).
- [ ] Add tests in `ET/test_templates.py`, `ET/` for the script marker, and `HOT/` for the route.

**Build.**

- [ ] With a host running on the home, the CLI posts to the route. With none, it opens `Store.open(home / "library")` through `EngineLibraryAdapter`. `LibraryFake` stays only for tests.
- [ ] Add `--template`.
- [ ] Read `[QMX_FAILURE]` on any exit code.
- [ ] Land feed items as `source` items.

**You see.**

- [ ] On a throwaway home, `templates install --template backup-weekly` then enabling its trigger answers ok instead of `409 unknown_object`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Three tests. An installed template is visible through the real Store. A script exiting 1 with the marker fails with the marker's reason. A feed run lands one `source` item. Run the engine and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The two suites at parent and head. Save `wu5-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. Install with no host running, then start the host and enable the backup trigger. Save `wu5-cold.log`. Pass when the enable answers ok.
- [ ] Lane 3. Install through a running host. Save `wu5-route.log`. Pass when the Store holds the templates and no second writer opened it.
- [ ] Lane 4. Run the feed template once against a fixture source. Save `wu5-feed.log`. Pass when one `source` item is found by `library_search`.
- [ ] Lane 5. `--template` with an unknown id. Save `wu5-unknown.log`. Pass when it refuses by name.
- [ ] Lane 6. Install twice. Save `wu5-twice.log`. Pass when the second install changes nothing.
- [ ] Lane 7. Grep the run logs for key values. Save `wu5-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `wu5-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the engine and host packages. Save `wu5-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Processes after the lanes. Save `wu5-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds to install the whole catalogue.
- [ ] Probe. Lane 2.
- [ ] Baseline. The same command at the root (into the fake).
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the tip.

## Test providers from a chat, and serve library_mark (WU2)

Closes list A item 3 and build BACKLOG LIB2's served row. Sources are build BACKLOG RTR1, RTR3, RTR4, RTR5 and LIB2. Real step none. Gate none. Done when a chat's tool list holds `ops_providers`, `ops_provider_test` and `library_mark`, the host serves the reads `provider_rows`, `provider_test` and `mark`, and a chat-wire row's Test sends one one-token turn through the chat lane and answers ok or a named error.

**Depends on.** WU1 (both edit `H/tools.py`).

**Files.**

- [ ] Edit `HO/host.py` (three host reads passed in `host_reads`).
- [ ] Edit `H/tools.py` (`HOST_SCHEMAS` for `provider_test` and `mark`) and `HT/test_tools.py`.
- [ ] Edit `R/registry.py` (`_key_test` gains the chat-wire branch) and add a test in the router's `tests/`.

**Build.**

- [ ] Serve `provider_rows` from `registry.describe(registry.load(home / "profiles"))`, `provider_test` from `one_token_test` with the plan test, and `mark` from `store.mark` with the MANAGE ask.
- [ ] Post one `max_tokens: 1` turn through the chat lane for a chat-wire row.

**You see.**

- [ ] A chat asked to "test my OpenRouter provider" answers with the row's result and its latency.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Two tests. `one_token_test` on a chat-wire row with a mock transport answers ok. `tool_defs(host=...)` holds `ops_provider_test` and `library_mark`. Run the router, harness and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The three suites at parent and head. Save `wu2-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. On a throwaway home with the OpenRouter row (credential ref `qmx/openrouter`, value never read), a chat runs `ops_provider_test`. Save `wu2-openrouter.log`. Pass when it answers ok.
- [ ] Lane 3. A chat runs `ops_providers`. Save `wu2-rows.log`. Pass when every configured row is listed with its wire.
- [ ] Lane 4. A chat marks a scratch item quarantined. Save `wu2-mark.log`. Pass when the ask appears, and after approval the item reads quarantined.
- [ ] Lane 5. Test a row whose key is missing. Save `wu2-nokey.log`. Pass when it answers a named error, not `not_run`.
- [ ] Lane 6. Test the plan row. Save `wu2-plan.log`. Pass when it answers ok.
- [ ] Lane 7. Grep lane logs for key values. Save `wu2-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `wu2-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the three packages. Save `wu2-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Processes after the lanes. Save `wu2-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds for one row Test.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the tip.

## Make just ci green (WU6)

Closes list A item 6's remaining causes. Sources are data BACKLOG DR10, DR13 and stack-wide, build BACKLOG MEM. The six stack-wide QA failures pass on a clean checkout at the root (Appendix A), so they get no fix. rclone is an environmental gap, closed by putting `D:/Tools/rclone` on `PATH` for the coordinator's runs (Appendix D). Real step none. Gate none. Done when the telemetry exporter's `flush` means sent by return, the DLL-path test reaches 260 characters on any temp root, the `qmx-memory` and `qmx-hub` suites run under `tools/test_all.py`, and `just ci` exits 0 apart from the named gaps.

**Depends on.** WU5 (same chain).

**Files.**

- [ ] Edit `E/telemetry.py` (one send lock across the swap and the send in `flush`) and `ET/test_telemetry.py` only if the test needs no change after the fix (otherwise leave it).
- [ ] Edit `QA/qmx-apps/tests/test_apps.py` (grow the nesting until the path passes 260 characters).
- [ ] Edit `tools/test_all.py` (two `suites.append` blocks for `qmx-memory` and `qmx-hub`).
- [ ] If the qmx-apps lock-install failure reproduces in the baseline log, fix it in the file the log names and add that file here, recorded in `ledger.tsv`.

**Build.**

- [ ] Fix the flush race.
- [ ] Fix the path test.
- [ ] Add the two suites.

**You see.**

- [ ] `just ci` ends with exit 0 on a clean check copy.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `ET/test_telemetry.py::test_an_exported_record_carries_no_value_the_redactor_masks` passes 20 times in a row with `-n 4` under a parallel engine suite. The DLL-path test passes with `TMP=D:/Temp`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The engine and apps suites at parent and head. Save `wu6-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. The full `just ci` at head with rclone on `PATH`. Save `wu6-ci.log`. Pass when it exits 0, or every failure is one named in Appendix D.
- [ ] Lane 3. The telemetry test 20 times under load. Save `wu6-telemetry.log`. Pass when all 20 pass.
- [ ] Lane 4. `tools/test_all.py --list` or its dry form. Save `wu6-suites.log`. Pass when memory and hub are listed.
- [ ] Lane 5. `just ci` without rclone on `PATH`. Save `wu6-norclone.log`. Pass when only the rclone tests fail.
- [ ] Lane 6. The telemetry exporter against a slow fake collector. Save `wu6-slow.log`. Pass when `flush` returns after the post.
- [ ] Lane 7. Grep the CI log for key values. Save `wu6-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `wu6-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the engine and apps packages. Save `wu6-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Processes after the lanes. Save `wu6-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Minutes for one `just ci`.
- [ ] Probe. Lane 2.
- [ ] Baseline. `evidence/ci0-f05fc64b.log`.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the tip.

## Skip providers with no key, and drop disabled sub-agents (WU3)

Closes list A item 4. Sources are build BACKLOG HYG0, RTR4 and RTR6. Real step none. Gate none. Done when the engine's role resolution skips a row whose key is missing or whose row is disabled, a chat's and a delegate's sub-agents come from the configured and enabled rows only, and the engine reads its role tiers from `qmx_router.agents` instead of a second copy.

**Depends on.** WU2 (both edit `R/registry.py`).

**Files.**

- [ ] Edit `E/ports/harness_adapter.py` (`profiles()` drops a row with no keyring entry or a disabled row) and `E/settings.py` (read `ROLE_TIERS` from the router).
- [ ] Edit `R/registry.py` (one helper restricting `load(home / "profiles")` to the configured, enabled `[providers]` rows) and `R/agents.py` if the helper needs it.
- [ ] Edit `H/chat.py` (pass `Supply(registry=...)`) and `H/delegate.py` (line 421).
- [ ] Add tests in `ET/`, the router's `tests/` and `HT/`.

**Build.**

- [ ] Check the keyring by reference (existence only, never the value).
- [ ] Write the helper and pass it into both call sites.
- [ ] Remove the engine's table copy.

**You see.**

- [ ] With an OpenRouter row and no Kimi key, a strong-role chat runs on OpenRouter on the first try.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Two tests. A key row with a missing keyring entry is skipped by `profiles()`. Removing a `[providers]` row drops its sub-agent from the Surface. Run the engine, router and harness suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The three suites at parent and head. Save `wu3-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A throwaway home with a Kimi row and no key and an OpenRouter row. Save `wu3-roles.log`. Pass when the strong role resolves to OpenRouter first.
- [ ] Lane 3. Disable the OpenRouter row, open a chat. Save `wu3-disabled.log`. Pass when no OpenRouter sub-agent is listed.
- [ ] Lane 4. A delegate on the same home. Save `wu3-delegate.log`. Pass when it targets only enabled rows.
- [ ] Lane 5. Rerun `SL/engine/x10_llm.py` in its provider-proof mode. Save `wu3-x10.log`. Pass when it passes or names the lane as stale in `BACKLOG.md`.
- [ ] Lane 6. Compare the generated lists before and after the dedupe. Save `wu3-tiers.log`. Pass when they are equal.
- [ ] Lane 7. Grep lane logs for key values. Save `wu3-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `wu3-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the three packages. Save `wu3-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Processes after the lanes. Save `wu3-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds to resolve one role.
- [ ] Probe. Lane 2.
- [ ] Baseline. The root.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the tip.

## The Hub counts real copies per blob (WU7)

Closes list A item 8 and two store follow-ups in the same chain of files. Sources are data BACKLOG DR7, DR2D, DR2B-EPOCH and `QUESTIONS-FOR-OPERATOR.md` G-R2. The operator has no bucket for now (`decisions.md` 3), so nothing is switched on. Real step none. Gate none. Done when `Hub.copies` answers one for the local store plus one only when a real read finds the blob in the bucket, an upload whose bucket push is still pending answers one, the PC keeps its staging copy until two real copies exist, `learn_epoch` does not re-park on a second higher epoch, and a real PC sync learns the server's epoch.

**Depends on.** WU6 (same chain).

**Files.**

- [ ] Edit `HB/server.py` (`copies(blob_id)` and `_landed`) and `HB/bucket.py` (a pushed set read by `copies`, and a real `view`).
- [ ] Edit `QX/server.py` only where it reads the answer.
- [ ] Edit `LB/store.py` (skip `park_primary_moves` when the known epoch is already stale) and `HB/replicate.py` (call `learn_epoch` in `sync` and `sync_since` if it is still absent, checked first).
- [ ] Add tests in the Hub's `tests/` and `LBT/`.

**Build.**

- [ ] Count copies from a real read.
- [ ] Fix the re-park.
- [ ] Wire `learn_epoch` into the real sync if it is absent.

**You see.**

- [ ] Nothing on screen. The data health read reports one copy for a server-made file.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Three tests. A configured bucket with an unpushed blob answers one copy. A second higher epoch does not re-park. A sync through `replicate` learns the server's epoch. Run the Hub, Library and control suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The three suites at parent and head. Save `wu7-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A PC upload to a scratch Hub with a local-folder bucket, before and after the push. Save `wu7-copies.log`. Pass when it answers one then two, and the staging copy is dropped only after two.
- [ ] Lane 3. Rerun `SP/data/p_split.py` through the real sync path. Save `wu7-split.log`. Pass when P-SPLIT passes.
- [ ] Lane 4. Two higher epochs in a row on a scratch store. Save `wu7-epoch.log`. Pass when the history parks once.
- [ ] Lane 5. Rerun `SP/data/p_serverlost.py` no-bucket case. Save `wu7-serverlost.log`. Pass when it passes.
- [ ] Lane 6. Data health read on the scratch home. Save `wu7-health.log`. Pass when it reports real counts.
- [ ] Lane 7. Grep lane logs for key values. Save `wu7-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `wu7-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the three packages. Save `wu7-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Processes after the lanes. Save `wu7-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds added per upload by the copy read.
- [ ] Probe. Lane 2.
- [ ] Baseline. The root.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the tip.

## Agent backtests run and land (WU4)

Closes list A item 1 and restores the tamper test. Sources are data BACKLOG DR4 and the DR1B landing review. The blob read already re-verifies its hash (`LB/store.py:1627`). Real step the import of QMB's result files on his real home (DR4's real step). Gate none. Done when a `StoreLanding` adapter lands a `backtest-result` on the real Store, a `BacktestDoor` runs QMB in process, the host binds `backtest_door`, `landing` and the recorded run configurations after the Store opens, the engine has a `qmb_backtest` app operation for workflows, and the qmx-tools tamper step is back against the store's blob path.

**Depends on.** WU3 (same chain).

**Files.**

- [ ] Edit `LB/adapter.py` (add `StoreLanding`, about 20 lines, mapping `put` to a `Draft` on `main` and `link` to `store.relate`).
- [ ] Add the door in `QB/host/` beside `library_landing.py`, running QMB's placement in process.
- [ ] Edit `HO/host.py` (bind the door, the landing and the run configurations where `control.attach_library(store)` runs), `H/harness.py:405` and `TL/servers.py:44` (take them from the host instead of building an empty context).
- [ ] Add the `qmb_backtest` operation in `E/control_door.py` beside `app_op`, and remove `needs: qmb-door` from its templates in `T/catalog.py`.
- [ ] Edit `SL/qma/cat_lanes.py` and `SL/qma/s28_effects.py` to pass the same fields.
- [ ] Edit `QA/qmx-tools/tests/test_tools.py` (a landing test and the restored tamper step). Add tests in `QBT/` and `ET/`.

**Build.**

- [ ] Write `StoreLanding` and the door.
- [ ] Bind them on the host.
- [ ] Add the engine operation.
- [ ] Restore the tamper step, and make `DomainContext.artifact` surface a corrupt blob as a named refusal.

**You see.**

- [ ] On a throwaway home with one imported month, the copilot runs a backtest of an example bot and the Library holds one `backtest-result` card.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Three tests. A backtest lands through `StoreLanding` on a real Store with its `consumed` and `uses` edges. A tampered blob is refused by name. A workflow `qmb_backtest` node lands one result. Run the qmb, tools, Library, host, harness and engine suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The six suites at parent and head. Save `wu4-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. DR4's lane 3, the copilot on haiku runs a backtest on a scratch home. Save `wu4-copilot.log`. Pass when one `backtest-result` lands with its edges and the old `library.db` is not written.
- [ ] Lane 3. A workflow with one `qmb_backtest` node. Save `wu4-workflow.log`. Pass when it lands one result.
- [ ] Lane 4. `library_search` for the result. Save `wu4-search.log`. Pass when it is found.
- [ ] Lane 5. A backtest over a sealed month. Save `wu4-sealed.log`. Pass when it is refused by the seal.
- [ ] Lane 6. Rerun `SP/data/p_qmbread.py`. Save `wu4-qmbread.log`. Pass when it passes.
- [ ] Lane 7. Grep lane logs for key values. Save `wu4-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `wu4-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the six packages. Save `wu4-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Processes after the lanes. Save `wu4-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for one month's backtest from the chat.
- [ ] Probe. Lane 2.
- [ ] Baseline. DR4's P-QMBREAD replay time.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** WU4 changes what his copilot answers about backtests.

- [ ] Post to the operator in chat a screenshot of lane 2's answer and a short video of the copilot running a backtest and opening the result, with one plain sentence on what changes for him.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the tip.
- [ ] Real step (G-LAND). After he lands the stack, the coordinator imports QMB's existing result files on his real home with `LB/migrate/from_qmb_results.py` and logs the counts.

## The cTrader demo sign-in (WU8)

Added on the operator's word (`decisions.md` 2). It is the first half of DATA-PLAN's DR5B, with PRB-CT's probe scripts, split so the sign-in exists before the probes need it. Also closes the keyless-provider follow-up in the same file (data BACKLOG DR6). Real step his demo sign-in, click by click with the coordinator (gate G-CT). Done when the PC's loopback receiver on the registered port forwards the one-minute code to the connection's home and keeps nothing, the home exchanges it with the app's client id and secret read by reference from the vault (`qmx/ctrader-client-id`, `qmx/ctrader-client-secret`) and keeps the tokens in its own key store, the three probe scripts exist ready to run, and a keyless data provider reads `ok` when its declaration says `auth == "none"`.

**Depends on.** WU7 (same chain).

**Files.**

- [ ] Add `BR/oauth.py` (the loopback receiver, its port a Settings value that defaults to the redirect registered on his app).
- [ ] Add `HO/venue_session.py` (the code exchange and the home's token store) and mount its `user`-only route in `HO/door.py`.
- [ ] Edit `BR/credentials.py` (read the client id and secret by reference) and `BR/registry.py` (the keyless check).
- [ ] Add `SP/data/p_ctscope.py`, `SP/data/p_ctrefresh.py`, `SP/data/p_ct2conn.py` and `SP/data/FINDINGS-ctrader.md` as written in DATA-PLAN's PRB-CT section.
- [ ] Add tests in the broker's `tests/` and `HOT/`.

**Build.**

- [ ] Write the receiver and the forward. The browser carries only the code.
- [ ] Write the exchange on the home. The tokens never enter the vault document or the PC's keyring.
- [ ] Write the three probes. They do not run in this PR.
- [ ] Fix the keyless read.

**You see.**

- [ ] On a scratch home with a fake cTrader token endpoint, the sign-in link opens, the receiver forwards the code, and the Connections row reads `ok`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Four tests. The receiver forwards a code and stores nothing. A second home for the same app is refused. The exchange stores the tokens only on the home. A keyless provider walks as `ok`. Run the broker and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The two suites at parent and head. Save `wu8-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. The full flow against the fake token endpoint on a scratch PC home and a scratch home acting as the server. Save `wu8-flow.log`. Pass when the home holds the tokens and the PC holds none.
- [ ] Lane 3. The Dukascopy and Binance rows on a scratch home. Save `wu8-keyless.log`. Pass when both read `ok`.
- [ ] Lane 4. Grep lane logs, the vault document and the PC keyring listing for token and secret values. Save `wu8-leak.log`. Pass when none appears.
- [ ] Lane 5. A code replayed twice. Save `wu8-replay.log`. Pass when the second is refused.
- [ ] Lane 6. The receiver with no home reachable. Save `wu8-nohome.log`. Pass when it refuses by name and stores nothing.
- [ ] Lane 7. The probe scripts with `--dry-run`. Save `wu8-probes.log`. Pass when each parses its inputs and exits without a network call.
- [ ] Lane 8. `tools/secret_scan.py`. Save `wu8-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the two packages and `SP/data/`. Save `wu8-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Processes after the lanes. Save `wu8-processes.log`. Pass when no receiver is left listening.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from the code arriving to the row reading `ok`.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** WU8 asks him to sign in, so he must see each click before it is real.

- [ ] Post to the operator a click-by-click walk-through page with a screenshot of each step of the scratch run, and a short video of lane 2, before his real sign-in.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the tip.
- [ ] Real step (G-LAND, G-CT). After he lands the stack and the server host runs (WU9's real step), the coordinator walks him through the demo sign-in, then runs the three probes and writes their rows. That opens WU10.

## The server is ready to be home (WU9)

Closes list A item 7 and the server follow-ups in the same files. Sources are data BACKLOG DR2B, DR2D, DR1A and DR14, and build BACKLOG RUN1b. Real step the server setup on the real server (DR2B's real step). Gate none for the PR. Done when `qmx node import`, `rebuild` and the host unit name one Library root, `setup` stops and disables the standalone Hub, imports as `qmx`, then starts `qmx-host`, `rebuild` stops the services first, `pair` writes the pairing key where the Hub reads it, ordinary saves go through the flip's quiesce check, `qmx-host` declares `qmx-hub`, the host's doctor shows the Library store's health, the run-pass secret survives a restart and is shared by the machines of one home, each placement gets its door address by default, and the remote providers and Dockerfile start the sidecar.

**Depends on.** WU4 (both edit `HO/host.py`).

**Files.**

- [ ] Edit `QX/node.py` (one root `/srv/qmx/library`, the setup order, `rebuild`, `pair`) and `QX/primary.py` only if the quiesce check needs a public read.
- [ ] Edit `HO/host.py` (the save path checks the flip's held flag, the doctor row reads `Store.state`, `door_url` defaults per placement) and `QA/qmx-host/pyproject.toml` plus `qmx-agents/uv.lock` (the `qmx-hub` dependency).
- [ ] Edit `R/passes.py` (the secret is read from the home's vault and created once, not drawn per process).
- [ ] Edit `RM/providers.py` and `QA/qmx-remote/Dockerfile` (start `qmx_remote.sidecar`).
- [ ] Add tests in `QXT/test_node*.py`, `HOT/` and the router's `tests/`.

**Build.**

- [ ] Fix the node commands.
- [ ] Wire the quiesce check and the doctor row.
- [ ] Make the pass secret durable and per home, and set the default door address.
- [ ] Point the remote providers at the sidecar.

**You see.**

- [ ] `qmx node setup --dry-run` on the PC prints the commands in the new order with one root.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Four tests. `setup` records stop, import, then `enable --now qmx-host`. `import` and the host unit name the same root. A save during a held flip is refused. A pass minted before a host restart verifies after it. Run the control, host, router and remote suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The four suites at parent and head. Save `wu9-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. `qmx node setup` on the server against a scratch prefix under `/srv/qmx/check/wu9` as `qmx`. Save `wu9-setup.log`. Pass when the host runs under the unit, serves the one root, and no standalone Hub is left.
- [ ] Lane 3. A PC sync to that scratch server host. Save `wu9-sync.log`. Pass when a PC item reaches the server store.
- [ ] Lane 4. A run pass minted on a scratch PC host, used at the scratch server door after a restart. Save `wu9-pass.log`. Pass when the read succeeds.
- [ ] Lane 5. `qmx node rebuild` on the scratch prefix. Save `wu9-rebuild.log`. Pass when it stops the services first and the store opens.
- [ ] Lane 6. The doctor route on a store opened read-only. Save `wu9-doctor.log`. Pass when it names the store's health.
- [ ] Lane 7. Build the remote Dockerfile, or read it if Docker is absent. Save `wu9-docker.log`. Pass when the entry point is the sidecar.
- [ ] Lane 8. `tools/secret_scan.py`. Save `wu9-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the four packages. Save `wu9-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove `/srv/qmx/check/wu9` and list processes on both machines. Save `wu9-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for `qmx node setup` on the server.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the tip.
- [ ] Real step (G-LAND). After he lands the stack, the coordinator runs the server setup on the real server as DATA-PLAN's DR2B real step describes, with the store at `/srv/qmx/library`. The PC stays primary until his flip click.

## cTrader reads through the server, and broker history (WU10)

The rest of DATA-PLAN's DR5B, on the facts PRB-CT's probes record after his sign-in. The MT5 adapter is left out, because he asked for the cTrader half and gave no investor login (`BACKLOG.md`). Real step his first real cTrader demo connection read through the server (G-CT). Gate G-CT and PRB-CT's rows without the P-CTREFRESH fallback. Done when `qmx_broker`'s cTrader reads go through the home host's one long-running `qmf-venue` session, other machines' reads forward to it, existing `qmx/ctrader-*` entries are re-filed with the client id and secret as `qmx/read/ctrader-app` and no token left on the PC, the health walk gains a liveness read if P-CT2CONN says so, and a `download-broker` template pages demo history into one partition.

**Depends on.** WU8, and gate G-CT with PRB-CT's three rows written.

**Files.**

- [ ] Edit `BR/ctrader_transport.py` (reads through the home session) and `BR/credentials.py` (the re-filing).
- [ ] Edit `HO/venue_session.py` (the long-running session per app and environment).
- [ ] Edit `BR/registry.py` (the cTrader declaration with PRB-CT's facts, and `bar_page_limit` from DR11's paging proof).
- [ ] Add the template folder `T/download-broker/` and its row in `T/catalog.py`.
- [ ] Add tests in the broker's `tests/` and `HOT/`. Extend `SP/data/p_notrade.py` with the token half.

**Build.**

- [ ] Route every cTrader read through the home session.
- [ ] Re-file the old entries, removing local tokens with no tombstone.
- [ ] Add the liveness read only if P-CT2CONN recorded a silent drop.
- [ ] Write `download-broker`.

**You see.**

- [ ] A PC read of the demo account's balance goes through the server, and the Connections row reads `ok`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Three tests. Deleting a server-homed connection from the PC publishes no tombstone. A PC read forwards to the home. `download-broker` pages a fake history of three pages into one partition. Run the broker, host and engine suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. The three suites at parent and head. Save `wu10-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P-NOTRADE (tokens) on demo. Save `wu10-p-notrade.log`. Pass when its token line holds.
- [ ] Lane 3. A refresh on the server home, then a forwarded PC read. Save `wu10-refresh.log`. Pass when the read succeeds after the refresh.
- [ ] Lane 4. One week of demo EURUSD ticks through `download-broker`. Save `wu10-history.log`. Pass when one partition lands with its card and no request exceeds the provider's own rate.
- [ ] Lane 5. P-CT2CONN's case as a lane. Save `wu10-2conn.log`. Pass when the health walk detects a dropped first connection within one check.
- [ ] Lane 6. Paging backwards past one page of bars. Save `wu10-paging.log`. Pass when `hasMore` paging returns the whole range.
- [ ] Lane 7. Grep lane logs, Settings, the vault document and the Library for token values. Save `wu10-leak.log`. Pass when none appears.
- [ ] Lane 8. `tools/secret_scan.py`. Save `wu10-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Gates in the three packages. Save `wu10-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Close every venue session and list processes on both machines. Save `wu10-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds per week of ticks through the home session.
- [ ] Probe. Lane 4.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. His sign-in already happened on cTrader's own page in WU8's real step.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the tip, after the first stack has landed, as its own short stack.

## Close the program

- [ ] Every PR is stacked with a CLEAN verdict, or skipped with its gate named in `RESUME.md`.
- [ ] `just ci` at the stack tip exits 0, or every failure is a named environmental gap in Appendix D.
- [ ] The operator's go is recorded in `ledger.tsv`, and the stack is merged into `engine/base` in order.
- [ ] The data round's real steps run behind their gates (Appendix E), each with its log in `evidence/real-<step>.log`, and each closed gate is posted to `QUESTIONS-FOR-OPERATOR.md`.
- [ ] Tell the operator in plain words what changed for him and what still waits on him.

## Appendix A. Prototype evidence

Facts read at `f05fc64b` on 2026-10-24 by a read-only Opus pass (no edits, no spawns), each with file and line.

- `run_backtest` refuses because `DomainContext` gets neither `backtest_door` nor `landing` at four call sites, and `BacktestDoor` has no implementation outside a test (`TL/service.py:175-192`).
- `tool_defs` binds no `app_server` row, so the harness tool-row test fails 77 against 78 on `apps_admin_move` (`H/tools.py:475-516`, run at the root).
- The Library sink is already attached (`QX/service.py:1420`). Packs materialise only at start-up (`HO/sessions.py:656-664`).
- `one_token_test` answers `not_run` for every non-Anthropic key row (`R/registry.py:485-489`).
- `HarnessAdapter.profiles()` checks no keyring (`E/ports/harness_adapter.py:215-217`). `chat.py:1311-1317` builds `Supply` with no registry.
- `templates install` falls back to `LibraryFake` (`E/service/api.py:92-93`).
- The telemetry failure is a race in `E/telemetry.py` (`flush` at 396-399 against the thread at 419-424), not an exporter process.
- The six stack-wide QA failures of data BACKLOG line 67 pass on a clean checkout (168 tests). The pyright one needs the venv on `PATH`.
- The flip's five preconditions hold as listed in list A item 7 (`QX/node.py:353, 501, 536, 564, 587-599`).
- `Hub.copies` is `1 + (1 if self.buckets else 0)` (`HB/server.py:116-122`).
- The blob read already re-verifies its hash (`LB/store.py:1627-1629`).

## Appendix B. Not in this program

- Push of `ui-review/repair`, the build store moves and the risk-lab copy are not in the operator's 2026-10-24 paste. They go to `BACKLOG.md` unless he asks.
- The MT5 adapter (DR5B's other half), the cTrader live connection, and anything that needs the R2 bucket (`decisions.md` 3).
- Hindsight on the server (DR2E), which still waits on the recall check.

## Appendix C. Files two PRs share

| Pair | Shared file | Order |
|---|---|---|
| WU1, WU2 | `H/tools.py`, `HT/test_tools.py` | WU1 first |
| WU2, WU3 | `R/registry.py` | WU2 first |
| WU2, WU4, WU9 | `HO/host.py` | WU2, WU4, WU9 |
| WU1, WU4 | `E/control_door.py` | WU1 first |
| WU5, WU8 | `HO/door.py` | WU5 first |
| WU8, WU10 | `BR/credentials.py`, `BR/registry.py`, `HO/venue_session.py` | WU8 first |
| WU5, WU10 | `T/catalog.py` (WU4 too) | WU4, then WU10 |
| WU7, WU9 | none (`QX/server.py` in WU7, `QX/node.py` in WU9) | free |

Parallel pairs and their intersections, checked from the Files blocks above. WU1 and WU5 share none. WU2 and WU6 share none. WU3 and WU7 share none. WU4 and WU8 share none, unless WU8 needs `HO/host.py` to build the venue session, in which case WU8 waits for WU4 to be stacked.

## Appendix D. Defaults

- No hourly tick. Claude's default, because notifications wake the coordinator.
- rclone on `PATH` from `D:/Tools/rclone` for the coordinator's `just ci` runs. Claude's default. It is a named environmental gap on a machine without rclone (`QA/qmx-apps/tests/test_storage.py:38`, `QA/qmx-control/tests/test_backup.py:16`).
- The pyright half of the QA static gate is run with the venv on `PATH`. Claude's default.
- The cTrader loopback port defaults to the redirect registered on his app, editable in Settings.

## Appendix E. Gates and calls

- G-GO. His go to merge the stack into `engine/base`, once for the whole stack or per PR.
- G-LAND. Real steps run only on landed code.
- G-FLIP. His click on "Move the Library to the server". The coordinator never presses it.
- G-CT. His demo sign-in, walked through click by click after WU8 lands and the server host runs.
- G-SEAL. The month his holdout starts. Until he names it, the price door stays shut.
- G-R2. Closed by his decision. Anything that needs a bucket waits and says so.
- G-CAL. His yes to remove the old calendar task on his PC.
- G-OO. His OpenObserve sign-up, only if the install asks.
