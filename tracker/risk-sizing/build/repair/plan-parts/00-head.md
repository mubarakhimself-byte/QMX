# QMX repair program

This program repairs what the unit build shipped, for him as the one person who trades with QMX and for the agents that build and backtest units for him.
It follows his order, the foundation first and the walls after. A unit that does what it says comes before a backtest of it, a backtest on his real facts comes before a verdict on it, and a true verdict comes before anything reaches a node.
There are 24 PRs, `R01` to `R24`, in 6 phases. R01 to R14 are the foundation and stop at a gate that waits for his word. R15 to R24 are the walls.
The stack roots on `build/us-c14` at `50c83a4e`. Nothing lands by itself. He lands the stack, and nothing runs live during the repairs.
The decisions live in `PLAN-SHAPE.md` beside this file. The facts for each repair live in the audit's grounding reports. Where a section and `PLAN-SHAPE.md` differ, `PLAN-SHAPE.md` wins, and his newest word wins over both.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a test run, or a SHA. The body is a how-to. The appendices explain and record.

Each PR section opens with a short preamble, its rows and the source of its facts. Then come the nine blocks `check-plan.mjs` requires. "You see" is written for him in plain words, so it holds no codenames. No PR writes UI code, so no PR changes a screen. Builders read the rest, so the rest uses real symbols and paths.

This file is generated. To change it, edit `plan-parts/`, run `node assemble.mjs` in this folder, then run `check-plan.mjs` on the result. Files and line numbers were read at `50c83a4e` and are starting points, so check them against the code. Code truth beats any line number here. When they differ, follow the code and say so in the PR body. Code from October onward is the truth. The repository's `docs/` folder is stale, so do not read it and do not edit it.

These short names hold across the plan.

- `A` is `D:/QMX-worktrees/audit-ship`, the audit's store. `A/FINDINGS.tsv` holds the rows and `A/reports/` holds the reports.
- `S` is `D:/QMX-worktrees/repair-ship`, this program's store.
- `P` is `D:/QMX-worktrees/unit-plan/tracker/risk-sizing`, the plan branch's folder.
- `$CHECK` is a check worktree of the commit a lane runs at, made by the boot recipe.
- A row id such as `p0a-1` is a row in `A/FINDINGS.tsv`. A row id such as `node-n1` is a new row from a grounding report, listed in Appendix E.
- E1 to E12 and M1 to M11 are the promises in `A/reports/ground-core.md` section 2, about the workflow engine and the mini-app core.
- Level 2 means pointed at the line, level 3 means walked, and level 4 means ran real code. Every safety fact in this plan carries its level.
- "Call 13" means item 13 of Appendix D, the calls already made. No builder reopens them.

The program runs `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md` with these overrides. Builders and reviewers are Claude Opus 5.5 subagents on this PC, not cloud agents. The coordinator is the only topology writer, and it runs no code review of its own. The audit tick comes from the coordinator's prompt in `P/build/repair/PROMPT-REPAIR.md`. The first PR's base is `build/us-c14`, not trunk. There is no 15-minute line and no clock on builders. Bugbot does not run on this repository. Light verification holds, his rule of 15 October, so the coordinator runs lanes 1 to 4 and at most one menu lane per PR, and there is one fix round.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. A menu lane the coordinator did not choose is marked "not chosen", and that counts as checked.

### How this program runs

Each rule answers something that went wrong in the last build.

1. Skills are checked, not listed. A script reads each builder's and reviewer's transcript and fails the PR if a required skill was not opened. The script is `S/tools/repair_check.py check`, copied from `P/build/repair/repair_check.py`. A fail goes back to the same agent once. A builder must open poteto-mode, `playbooks/feature.md`, `how`, `architect`, `tdd`, `blast-radius`, and `principle-test-behavior-not-implementation`. A reviewer must open `code-review`, the `bmad-review` verification-gap lens, and `blast-radius`, plus the edge-case lens on the money-adjacent PRs named under "Verdict and merge".
2. Understand first, in writing. A builder's first output is `evidence/<id>/owner-how.md`, which says what is really there, who depends on it, and the safety fact. The next is an `architect` sketch in `owner-sketch.md`. The next is a failing test, saved as `owner-red.log`. No code comes before those three. The script checks that they exist and that they came in that order.
3. There is no clock on builders. Take the time the understanding needs.
4. Every row gets its check lanes. A PR with no lanes run does not stack. The coordinator runs lanes 1 to 4 in the background, and R19 also runs lane 6, as its section says. Lane 1 compares against `A/tests/SUMMARY.txt` for the first PR and against the parent after that. Lane 2 is the PR's fail-today proof, which fails at the parent and passes at the head.
5. Whole-repo runs sit on a schedule that cannot lapse. They run after R03, R05, R06, R10, R11, R14, R15, R19, R20 and R24, in the background, under `D:/QMX-worktrees/.ci-lock`. That is every fifth PR and each phase end. A phase does not close without its run. R21 to R23 change the same money files with no such run between them, so each of them adds the earlier PRs' new test files to its lane 1.
6. The plan cannot grow quietly. Every status line shows the count of PRs done, PRs left and PRs added. A new PR needs his word. A finding is justified as a real bug before it goes anywhere, and most do not become work.
7. Every reviewer answers the stack-time question before a PR stacks. Does anything below this PR make a stop-gap, comment or setting in it false? Does this PR make one below it false? That is how instrument facts were lost last time.
8. Tests use real neighbours. A test for a crossing runs both sides for real, or uses a fake at least as hard as the real neighbour. A test that plants a row the real path never writes is replaced when the PR touches it. His rule stands that there are no hundreds of tests. Tests are few and cross real connections.
9. Subtract first. Each PR opens by deleting the `test-delete` rows and dead code in its own files.
10. The tick re-reads the prompt. After every compaction and every tick the coordinator re-reads `PROMPT-REPAIR.md`, this head and `S/RESUME.md`. Last time it re-read only its notes, and the rules faded.
11. Long tests are the coordinator's. A builder never waits on a long command, because its cache expires while it waits.
12. Each PR gets a fresh Opus reviewer, with `code-review` on both axes, the `bmad-review` verification-gap lens, the edge-case lens on money-adjacent PRs, and `blast-radius` on the one safety fact the section names, rerun for real.

### The gates

Five gates hold steps that are his. The coordinator builds around each one.

- G-LAND. Real steps on his own QMX folder run only on code he has landed. Nothing in the program waits on it. Where the stack lands in the end is his, and it comes up only when landing nears.
- G-FOUNDATION. The program stops after R14, reports to him and waits for his word. The risk session needs nothing from this program to resume, and he may resume it at any time.
- G-DEMO. After R24 come his demo sign-in on cTrader's own page, the first-start script's real run, and the demo proofs. Nothing in the program needs it before then.
- G-WALLET. His Hyperliquid testnet agent wallet, approved on Hyperliquid's own page, opens `p5b-1` to `p5b-7`. R21 and R22 mostly close `p5b-3` and `p5b-6`.
- G-SERVER. His go to run checks against a node on his server opens `plan-check-4`, `p5c-5`, section C-19, `p5d-2` and `p34-7`.

### What the foundation works means

Each check is one real run across a real connection, with a literal expected result. Each fails today. The PR named adds it, or R14 does. `tools/proof_foundation.py`, added by R14, runs all 18 by name.

| # | Check | Added by |
| --- | --- | --- |
| 1 | A repair lands. A changed first-party app and a changed library reach an installed app at the next start, and its data stays. On a money app neither touches the signed version, and the repair arrives as a new version for him to sign | R03 |
| 2 | While one app installs slowly, a running app answers within a second. A stuck install fails by name and the host carries on | R03 |
| 3 | Nothing silent. Every stdlib block, swept as a trigger and as an exit through the real door over a month, either acts or refuses with a pointer. Never "check pass, zero signal, no reason" | R04, R05, R06 |
| 4 | A long-only unit through a QMB job makes zero short fills | R04 |
| 5 | An agent writes "ADX above 25" through `unit_new` and `unit_check`, and a QMB job runs it. It trades, and level 99 gives none | R05 |
| 6 | A QMB run with short trades moves the tuned number as its long mirror does, and the row shows why | R05 |
| 7 | The dictionary at full size. Fresh store, first start, one publish gives 455 pages, none with status None. A clashing save is refused, and an ordinary sentence stays unmatched | R06 |
| 8 | A fresh home with a market that has only a Library record and ticks in the market store lands a finished result that links its data and uses that record's lot step | R08 |
| 9 | With no month, the run is refused before any try, naming the month and the template | R08 |
| 10 | The same month through a CSV and through the store gives the same trades | R08 |
| 11 | A record moved on main shows in the next run with no host restart | R07 |
| 12 | A study forbidding gaps beats a chat allowing them. A sealed month is refused, and no sealed file sits in any run folder | R07, R08 |
| 13 | A stated cost profile changes net money, raw R stays, and the verdict says costs are uncalibrated | R10 |
| 14 | A real backtest of 200,000 steps stays flat in memory | R10 |
| 15 | Real QMB job, real lander, real judge, real scorecard, for one market and for a sweep. The trades are counted, there is one paper, and the cause is right | R12 |
| 16 | A model's copy saying pass over a stored fail routes as fail | R12 |
| 17 | The script gate and the hook on a market only the Library knows. A clean unit reaches QMB, and a broken one gets its error | R13 |
| 18 | His own test. A copilot chat on `haiku`, from one plain sentence, builds a unit from dictionary blocks, checks it, backtests it on data the download template stored, and gets a verdict in plain words. It runs through a real host on a scratch folder, over its chat routes | R14 |

The dummy unit's job is checks 4 to 6 and 15. It does not need to pass the judge.

### What the walls work means

Each is a real run across a real connection. W13 needs his demo account, so it waits for G-DEMO. R24 adds the rest to `tools/proof_foundation.py --walls` and runs them.

| # | Check | Added by |
| --- | --- | --- |
| W1 | A wheel-built node environment loads the alarm list, and a real alarm reaches a loopback ntfy. Status says so when alarms are off | R16 |
| W2 | OpenObserve stopped, then back, with a pathological log line. The doctor returns to green, and trading never noticed | R16 |
| W3 | The real node blocks an entry with each of the three unlisted texts that reach a row, and rows keep landing on disk and in the store | R15 |
| W4 | A real node trade travels writer, harvester and Library. One `trade` and one `paper-run` land, unchanged by a second and third round | R15, R19 |
| W5 | Host start on a fresh folder with QMB broken. The node still starts, and the failure is named | R03 |
| W6 | A real download, the configure job and a round, then `readings_query` answers. A read error follows, and the next round still publishes. With the MIS stopped, a unit still enters | R18 |
| W7 | A deploy stalled past 30 s against a real node gives one deployment once it returns, and a click after a refused deploy deploys again | R17 |
| W8 | Drop the socket, fire the stop, reconnect. The trade books at the broker's price, nothing is phantom, and the unit trades again | R20 |
| W9 | Restart with a position whose stop is gone. It is back, or closed with an alarm, before any entry. Restart with a position already closed, and the trade row exists | R20, R21 |
| W10 | RED with the deployment refused, and flatten with a unit trading. The broker ends flat, the rows say so, and a restart replays nothing | R21 |
| W11 | Reboot with no network. The unit says it waits, then trades at the real balance. Deploy a second market after bind with a position open, and bars arrive while the position holds. Deploy an unlisted symbol, and it is refused by name while the account keeps trading | R22 |
| W12 | Refuse the socket for an hour of clock. Sign-ins stay under a set count, and status reads the cause. Across a weekend it reads closed, not stopped. A 5-minute unit gets a refusal until its bars exist, and `parity.py` still reads 63 of 63 | R22, R23 |
| W13 | The script on a fresh rehearsal folder with no fixtures reads all PASS with the plain "no unit" line, and with a refused unit it reads FAIL in the node's words. On demo, `c14-real.log` and `c15-demo.log` read all PASS, including the cut and refresh drills | R24, G-DEMO |

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to him, then stop. Start nothing from the plan without his word. Log his go in `S/RESUME.md`.
- [ ] Confirm the shell (Windows 11, PowerShell 7 and Git Bash) and the root. `git rev-parse build/us-c14` is `50c83a4e`. Logged in `S/RESUME.md`.
- [ ] Read the trunk rules with `git show origin/main:CLAUDE.md`, then his working copy `C:/Users/Mubarak/Desktop/QMX/CLAUDE.md`. Its QMA v2 section is the pattern here, and the factory lanes in trunk's copy are retired.
- [ ] Read `A/reports/SEEDS-2026-11-05.md`, `P/build/repair/PLAN-SHAPE.md`, and `P/CLEAN-HOUSE-CONTEXT.md` sections 1 to 4, 9 and 10. His newest word wins.
- [ ] Create the store `S` with `RESUME.md`, `decisions.tsv`, `QUESTIONS-FOR-OPERATOR.md`, `BACKLOG.md`, `lows.md`, `ledger.tsv`, `dispatch/`, `review/`, `evidence/`, `homes/`, `data/`, `proofs/` and `tools/`.
- [ ] Copy the proofs out of the temp folder, so a clean-up cannot lose them. Copy `D:/Temp/audit/` folders `ground-core`, `ground-unit`, `ground-qmb`, `ground-start`, `ground-node`, `p0a`, `p1a`, `p2`, `p34`, `p5d`, `p6`, `seams`, `plan-review-a`, `plan-review-b` and `plan-fix-check`, scripts only, into `S/proofs/` with the same folder names. Copy `A/tools/env.sh` and `A/tools/guard/` into `S/tools/`, and `P/build/repair/proof_at.sh` and `P/build/repair/run_tests.sh` beside them. In the copy of `env.sh`, point `PYTHONPATH` at `S/tools/guard`, and leave `AUDIT_ROOT_ENV` and `AUDIT_AGENTS_ENV` out, because `proof_at.sh` picks the environment. Copy the transcript check `P/build/repair/repair_check.py` to `S/tools/repair_check.py`.
- [ ] Copy everything in `P/build/repair/lane_tools/` into `S/tools/`. These are the last build's lane helpers, patched so they write only under `S` and keep the credential guard, plus `safe_host.py`. Never run the originals under `unit-ship`, because their logs would overwrite the evidence R02's lane 5 compares against.
- [ ] Prove the login for model lanes before any dispatch. Use a check worktree of the root and hold `D:/QMX-worktrees/.engine-lane-lock`. Make a throwaway folder under `S/homes/arm-login/` by running `S/tools/safe_host.py <check> <port> S/homes/arm-login/QMX --health-and-stop`, make the login junction as the boot recipe says, and start the host again with `S/tools/safe_host.py <check> <port> S/homes/arm-login/QMX`. Run one `haiku` turn over `POST /api/chats` and `POST /api/sessions/<sid>/turns`. Save `S/evidence/arm/login.log`, holding the turn's answer and no login file. It passes when the turn answers. If it fails, stop and report to him. Nothing is copied, and no login file is read or printed.
- [ ] Confirm the data. `D:/QMX-worktrees/unit-ship/data/dukascopy-node/` holds the January to March 2025 EURUSD and XAUUSD bid and ask CSVs. R09's lane adds one real December through the shipped download template.
- [ ] Arm the audit tick by calling the `loop` skill with no interval and the tick prompt, with a delay of about 3,000 seconds, because an interval of 60 minutes or more makes that skill ask a question that would stall the run. The tick prompt is in `P/build/repair/PROMPT-REPAIR.md`. Post a short status message to him only when a PR is stacked, a verdict lands, a gate opens or a blocker appears. Every status message ends with the count of PRs done, PRs left and PRs added.
- [ ] Never stop to ask him during a phase. A question goes to `S/QUESTIONS-FOR-OPERATOR.md` with the default taken and how to undo it, and the build goes on. Only his money, his sign-ins, his clicks and his gates are his.
- [ ] On his hold or stand-down, send every builder a zero-writes order at once.

### Spawn owners

- [ ] Spawn one fresh Opus builder per PR in the background with `subagent_type: qmx-repair-builder` and `model: opus`, from a dispatch file saved in `S/dispatch/`. Its first words are exactly "Read C:/Users/Mubarak/.claude/skills/poteto-mode/SKILL.md in full, including its Principles section, before any work." If the agent type is missing, see the prompt's rule 21.
- [ ] Give the builder `P/build/repair/BRIEF-REPAIR-BUILDER.md`, its section of this plan, the head of this plan, the grounding report block its preamble names, and any line for its id in `S/evidence/r02/review-findings.md`.
- [ ] Run one builder at a time. R16 and R17 are the only pair that may run side by side, and only after the coordinator records their empty Files intersection in `S/ledger.tsv`. Appendix C lists every shared path.
- [ ] No PR touches `apps/qmx-ui/`, `~/.claude`, his real home `~/.qmx`, `C:/Users/Mubarak/Documents`, `C:/Users/Mubarak/Desktop/DATA_NARL`, or any vault value. Lanes run on throwaway folders and a scratch profile only.
- [ ] No PR changes the engine. Call 10 holds. The engine package changes by the one exporter line in R16 and nothing else.
- [ ] After R14, stop. Report to him under G-FOUNDATION and wait for his word before R15.

The dispatch order, generated from the sections below by `assemble.mjs`, which also refuses a PR that depends on a later one.

@spawn-table

### PR mechanics, for every PR

- [ ] The coordinator creates `build/repair-NN` from the current stack tip in `D:/QMX-worktrees/bld-repair-NN` before the dispatch, where `NN` is the PR's number. Never `git stash`. The first PR's parent is `build/us-c14`. The uncommitted edit in `D:/QMX-worktrees/bld-us-c14` stays out, by call 18.
- [ ] The builder writes `evidence/<id>/owner-how.md`, then `owner-sketch.md`, then `owner-red.log`, in that order, before any product code. `<id>` is the PR id in lower case, such as `r07`.
- [ ] Once those three exist, the builder's first commit does the Subtract box, so the commits read subtraction first, then the failing test, then the repair.
- [ ] The builder opens the PR ready, never draft, once the red test exists, with `gh pr create --base <parent-branch> --head build/repair-NN --repo MubarakHimself/QMX`. Keep it open through the fix round.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Set `TMP` and `TEMP` to `D:/Temp` and `UV_CACHE_DIR` to `D:/Caches/uv`. Work only on `D:`. His `C:` drive runs full, and 106 red `qmx-home` backup tests on a full `C:` are the disk, never the PR.
- [ ] Never edit a file inside a venv. uv's hardlinks reach every environment.
- [ ] A PR that changes any file under an app folder bumps that app's patch version in `app.toml`, because `image_files` (`qmx_apps/manifest.py:315`) hashes the whole folder, tests included, and the same version with new bytes answers `immutable_version`. It also updates the literal table R03 adds to `test_shipped_apps.py`, and it updates `test_qmb_app.py:191` when QMB moves. From R04 on, `qmx-judge/tests/test_conformance.py` reads QMB's version from `app.toml`, so it follows by itself. `[qmb] default_tester` stays `qmb@1.0.0`, because nothing reads it while `p2-7` waits.
- [ ] A PR that changes a library in `apps/trading-node`'s lock also bumps that app's patch version in `qmx-agents/apps/trading-node/app.toml`, so the repair arrives as a new hash for him to sign, by call 11. The libraries are the lock's path sources, which are `qmn`, `qmb`, `qml` and the `qmf-*` packages and calendars. A change counts when it sits under a library's `src`, because `path_sources` (`qmx_apps/supervisor.py:163`) digests only `src`. The Files block of each such PR names `app.toml` and the version row in `test_shipped_apps.py`. Move any test that pins that version. At `50c83a4e` the one literal is `trading_node_app_test.py:69`, which nothing compares, because `road/history.py:42` reads a version only for `build` evidence, level 2.
- [ ] A PR that adds a foundation check keeps that check's failing test, by name, in `owner-red.log`, because R14's lane 2 reads those logs.
- [ ] The builder runs `fmt-check`, `lint` and `types` in each package it touched, `tools/secret_scan.py` and `tools/money_path_scan.py`, reads each exit code, runs only the fast tests it added or changed, and never waits on a long command. It runs the `blast-radius` skill on its diff before the last push.
- [ ] The builder writes any lane command the plan leaves open into `evidence/<id>/owner-lanes.md`, so the coordinator can run it. Builders do not run model lanes.
- [ ] Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. PR bodies end with the Claude Code line.

### Verdict and merge, for every PR (append to the stack, never merge)

- [ ] At the code-ready head the coordinator runs lanes 1 to 4 and at most one menu lane in the background and saves their logs in `S/evidence/<id>/`. A PR with no lanes run does not stack.
- [ ] A fresh Opus reviewer agent (one per PR, `model: opus`, told not to spawn sub-agents) reads the PR section, the full diff and those logs. It applies `code-review` on both axes and the `bmad-review` verification-gap lens. It answers the stack-time question, reruns the section's safety fact for real under `blast-radius`, and writes `S/review/<id>-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] The reviewer adds the edge-case lens on the money-adjacent PRs, which are R03, R04, R05, R07, R08, R10, R11, R15, R17 and R20 to R24.
- [ ] The coordinator runs `S/tools/repair_check.py check <id> <builder|fix|reviewer>` for the builder and the reviewer, which also runs the order check for the three owner files. A fail goes back to the same agent once.
- [ ] Blockers go to one fix round by a fresh Opus builder on the same branch and worktree, given the dispatch file, the review file and the failing logs. The coordinator reruns the failed lanes and the touched suites at the fix head. Low findings go to `lows.md`.
- [ ] A safety fact that fails stops that PR and comes back to the coordinator, by call 20. Nobody works around it.
- [ ] A new finding is justified as a real bug in `BACKLOG.md` with its evidence level. It goes to the PR whose Files touch it, or it waits. It never becomes a new PR without his word.
- [ ] `ledger.tsv` gets head, parent, patch-id, the verdict and the count of PRs done, left and added.
- [ ] To append, the coordinator fetches the stack tip. If another PR was appended since the dispatch, it rebases the branch onto that tip, pushes with `--force-with-lease` after an `ls-remote` check, and sets the PR base to the tip's branch. A verdict stands when the patch-id is unchanged (`playbooks/shipping.md`).
- [ ] The whole-repo run goes at the stack tip on the schedule in rule 5, whether or not a section also names it as a lane, with `S/tools/run_tests.sh <sha> <out-folder>`, because `tools/ci.py` stops at its first failure and would hide the tests. A red at the tip is traced to its PR by rerunning the failing test at each head since the last green tip, and that PR gets the fix round.
- [ ] He lands the stack himself from the list the coordinator sends. Nobody else merges, closes a PR or deletes a branch.

### Boot recipe, for every live lane

- [ ] `git worktree add --detach D:/Temp/<id>-check <head>`, then `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`. For a parent run, do the same at `D:/Temp/<id>-parent`.
- [ ] `source S/tools/env.sh` first, so the keyring guard and the credential guard hold in every lane. Starting a host wipes those guards unless its folder's `settings.toml` keeps them, and then it reads the real `qmx/control-token`. So a lane that boots a host, every menu lane worded "start the host" included, boots it only with `S/tools/safe_host.py`, or through the patched `S/tools/owner_lane_c14.py` for its rehearsal lanes. Both put the keyring in a throwaway file, write the keep list and refuse to start otherwise. Only the coordinator boots a host, and never with `python -m qmx_host` by hand. The guard stays on inside a node the host starts, so a node lane that stops at the guard is skipped and logged, because the node's grant store is the real Credential Manager on Windows.
- [ ] A proof script from the audit hard-codes `D:/QMX-worktrees/audit-head`. Run it with `S/tools/proof_at.sh <root|agents> $CHECK <script under S/proofs> [args]`, which copies the script's folder with that path replaced by `$CHECK` and runs it in that worktree's environment, under pytest when the file holds test functions. A script that patches a repair in memory prints its "today" lines first, so at the head read those lines, and an error in its later sections is not a fail.
- [ ] A lane runs on a throwaway QMX folder under `S/homes/<id>-<lane>/`. A lane that checks for stray files points `USERPROFILE`, `APPDATA`, `LOCALAPPDATA` and `HOME` at a scratch profile under the same folder.
- [ ] A lane with a model runs on `haiku`, through a real host on its throwaway folder, over the host's chat routes, holding `D:/QMX-worktrees/.engine-lane-lock`. It uses a real host because the in-process harness has no lander (`attach_landers` is called only at `host.py:1114`), and a chat's `backtest_run` would answer `unknown_lander`. R13's lane 5 is the one exception, because its probe opens the harness on the ship home itself, as `A14_HOME` says, and it needs no lander. There is no Anthropic or OpenAI API spend. A lane with a model that fails is rerun once, and two fails count as FAIL. Most lanes need no model, and a lane says so when it does.
- [ ] The login method is one directory junction, the same for every model lane. A chat's login sits at `<home>/claude` (`QmxHome.plan_dir`, `home.py:133`), and the home is the folder's `data/`. Once the folder exists and before the host starts, run `New-Item -ItemType Junction -Path <folder>/data/claude -Target D:/QMX-worktrees/qma-ship/home/claude` from PowerShell. Nothing is copied, and no login file is read or printed. After the host stops, and before the throwaway folder goes, run `cmd /c rmdir <folder>\data\claude`, which removes the link and leaves the target. The coordinator proves this at arming, and if it fails it stops and reports.
- [ ] A lane that needs real bars uses the months in `D:/QMX-worktrees/unit-ship/data/dukascopy-node/`. A lane that needs ticks in the store commits them through the real door, as `S/proofs/ground-qmb/bridge.py` does, or lands them through `download-dukascopy` on a scratch home. If the network is down, the lane logs "network down" and is rerun later.
- [ ] Each lane script exits non-zero on any failed check. The coordinator greps every PASS and FAIL line, never only the exit code.
- [ ] Every test run has a time limit. Check each agent's own background processes every tick, and stop leftovers after a verdict.
- [ ] Never name a PowerShell variable `$home`. Run Python through the worktree's own `.venv`, never a bare `python`, because on this PC a bare one can be a Windows stub that hangs. Save captures as `S/evidence/<id>/<log>`, then remove the check copy with `git worktree remove` and confirm no `qmx_host`, `claude` or `node` process from the lane is left.

