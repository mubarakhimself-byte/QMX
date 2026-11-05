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
- [ ] Copy the lane helpers from the last build into `S/tools/`. These are `D:/QMX-worktrees/unit-ship/evidence/c14/owner_lane_c14.py`, `owner_lane_host.py` and `owner_red_c14.py`, `evidence/c35/owner_lane_keyring.py`, `evidence/c36/owner_lane.py`, `evidence/a8/owner-lane4-verify.py` and `evidence/b9/owner-phase0.py`.
- [ ] Prove the login for model lanes before any dispatch. Use a check worktree of the root and hold `D:/QMX-worktrees/.engine-lane-lock`. Make a throwaway folder under `S/homes/arm-login/` the way `S/tools/owner_lane_c14.py` makes its folder, make the login junction as the boot recipe says, and start a real host on it with the file keyring. Run one `haiku` turn over `POST /api/chats` and `POST /api/sessions/<sid>/turns`. Save `S/evidence/arm/login.log`, holding the turn's answer and no login file. It passes when the turn answers. If it fails, stop and report to him. Nothing is copied, and no login file is read or printed.
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

| # | Id | PR | Depends on | Proving check |
| --- | --- | --- | --- | --- |
| 1 | R01 | Clear the dead weight | build/us-c14 at 50c83a4e | The whole-repo run stays at the baseline's three reds with these folders gone |
| 2 | R02 | Make the gates tell the truth | R01 | The red gates exit 0, and C-14's commits have a review on record |
| 3 | R03 | Let a repair reach him and stop an install stalling everything | R02 | A repair reaches an installed app at the next start, and a call answers within a second while another app installs |
| 4 | R04 | Refuse what a unit cannot run | R03 | A long-only unit makes zero short fills, and each unrunnable part refuses with a pointer |
| 5 | R05 | Make slots tell the truth | R04 | "ADX above 25" trades through a QMB job and level 99 gives none, and shorts move the tuned number |
| 6 | R06 | Check the dictionary and give session blocks the market's clock | R05 | The dictionary at full size has no page with status None, a clash is refused, and a session opens at the real cash open |
| 7 | R07 | Make backtests read his facts | R06 | A record on main reaches the run folder and the fills, and moving it shows in the next run with no host restart |
| 8 | R08 | Make backtests read his data | R07 | A fresh home with only a Library record and ticks in the store lands a finished result, and a month missing or sealed is refused before any try |
| 9 | R09 | Make long history hold up | R08 | A file cut short lands `data_short` or refuses, and a real December gives no false holes |
| 10 | R10 | Make runs report honestly | R09 | A stated cost profile changes net money with raw R the same, and 200,000 real steps stay flat in memory |
| 11 | R11 | Make a judge that cannot be talked round | R10 | A study written after a result costs a counted try and cannot drop a market, and each market answers for its own evidence |
| 12 | R12 | Give one true verdict and one paper | R11 | A real job, lander, judge and scorecard land one paper with the right cause, and a forged pass routes as fail |
| 13 | R13 | Say what a check with no Library cannot see, and fix the slow-lane words | R12 | On a market only the Library knows, a clean unit reaches QMB through the gate and a broken one gets its error from the hook |
| 14 | R14 | Prove the foundation and stop | R13 | All 18 foundation checks read PASS at the stack tip |
| 15 | R15 | Make the node's records true | G-FOUNDATION, then R14 | A real node trade reaches the Library, and a blocked entry with any of the three unlisted texts that reach a row leaves rows landing |
| 16 | R16 | Make alarms and deep logs reach him | R15 | A wheel-built node env loads the alarm list and a real alarm reaches a loopback ntfy, and a pathological log line does not stop deep logs |
| 17 | R17 | Fix promote's edges | R15 | A deploy stalled past 30 s gives one deployment once the node returns, and a click after a refused deploy deploys again |
| 18 | R18 | Make the MIS publish | R17 | A real download, the configure job and a round give readings, and a read error does not stop the next round |
| 19 | R19 | Make recording hold up over months | R18 | A second records round scores exactly as the first, with projection reading the store, and a million-row stream rounds without re-reading it |
| 20 | R20 | Let the broker win | R19 | Drop the socket, fire the stop, reconnect, and the trade books at the broker's price with nothing phantom |
| 21 | R21 | Make every way out act | R20 | RED and flatten leave the broker flat with true rows, a refused exit keeps going, and a restart replays nothing |
| 22 | R22 | Make what he deployed run | R21 | A reboot with no network waits and then trades at the real balance, a new market gets its bars with a position held, and an unlisted symbol is refused by name while the account keeps trading |
| 23 | R23 | Fix connections and honest words | R22 | An hour of refused socket stays under a set count of sign-ins, and a weekend reads closed, not stopped |
| 24 | R24 | Give the first-start script its new job and ready the demo proofs | R23 | A fresh rehearsal folder with no fixtures reads all PASS and the plain line, and a node that refuses reads FAIL in its own words |

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
- [ ] `source S/tools/env.sh` first, so the keyring guard and the credential guard hold in every lane. Starting a host wipes those guards unless its folder's `settings.toml` keeps them, and then it reads the real `qmx/control-token`. So a lane that boots a host, every menu lane worded "start the host" included, boots it only through `S/tools/owner_lane_c14.py`'s path: `throwaway_environment()`, the keep list it writes to the folder's `settings.toml`, and `refuse_unless_throwaway()` before the boot. Only the coordinator boots a host, and a lane that cannot use that path is skipped and logged. Never run `python -m qmx_host` by hand.
- [ ] A proof script from the audit hard-codes `D:/QMX-worktrees/audit-head`. Run it with `S/tools/proof_at.sh <root|agents> $CHECK <script under S/proofs> [args]`, which copies the script's folder with that path replaced by `$CHECK` and runs it in that worktree's environment, under pytest when the file holds test functions. A script that patches a repair in memory prints its "today" lines first, so at the head read those lines, and an error in its later sections is not a fail.
- [ ] A lane runs on a throwaway QMX folder under `S/homes/<id>-<lane>/`. A lane that checks for stray files points `USERPROFILE`, `APPDATA`, `LOCALAPPDATA` and `HOME` at a scratch profile under the same folder.
- [ ] A lane with a model runs on `haiku`, through a real host on its throwaway folder, over the host's chat routes, holding `D:/QMX-worktrees/.engine-lane-lock`. It uses a real host because the in-process harness has no lander (`attach_landers` is called only at `host.py:1114`), and a chat's `backtest_run` would answer `unknown_lander`. R13's lane 5 is the one exception, because its probe opens the harness on the ship home itself, as `A14_HOME` says, and it needs no lander. There is no Anthropic or OpenAI API spend. A lane with a model that fails is rerun once, and two fails count as FAIL. Most lanes need no model, and a lane says so when it does.
- [ ] The login method is one directory junction, the same for every model lane. A chat's login sits at `<home>/claude` (`QmxHome.plan_dir`, `home.py:133`), and the home is the folder's `data/`. Once the folder exists and before the host starts, run `New-Item -ItemType Junction -Path <folder>/data/claude -Target D:/QMX-worktrees/qma-ship/home/claude` from PowerShell. Nothing is copied, and no login file is read or printed. After the host stops, and before the throwaway folder goes, run `cmd /c rmdir <folder>\data\claude`, which removes the link and leaves the target. The coordinator proves this at arming, and if it fails it stops and reports.
- [ ] A lane that needs real bars uses the months in `D:/QMX-worktrees/unit-ship/data/dukascopy-node/`. A lane that needs ticks in the store commits them through the real door, as `S/proofs/ground-qmb/bridge.py` does, or lands them through `download-dukascopy` on a scratch home. If the network is down, the lane logs "network down" and is rerun later.
- [ ] Each lane script exits non-zero on any failed check. The coordinator greps every PASS and FAIL line, never only the exit code.
- [ ] Every test run has a time limit. Check each agent's own background processes every tick, and stop leftovers after a verdict.
- [ ] Never name a PowerShell variable `$home`. Run Python through the worktree's own `.venv`, never a bare `python`, because on this PC a bare one can be a Windows stub that hangs. Save captures as `S/evidence/<id>/<log>`, then remove the check copy with `git worktree remove` and confirm no `qmx_host`, `claude` or `node` process from the lane is left.

## Clear the dead weight (R01)

Phase A, clean ground. Source is `A/reports/ground-core.md` block K, with `A/reports/deletion.md` behind it. About 40,700 lines and about 5,700 lines of tests go, and no product file changes. He reads a repository that no longer talks about the retired factory. Done when the whole-repo run at the head fails only what `A/tests/SUMMARY.txt` already failed.

Rows carried. `deletion-5` `deletion-8` `deletion-9` `deletion-10`

Proves. The whole-repo run stays at the baseline's three reds with these folders gone.

**Depends on.** `build/us-c14` at `50c83a4e`.

**Files.**

- [ ] Delete `adws/` and `queue/`.
- [ ] Delete `tools/tests/test_sssf_quality_gate.py`.
- [ ] Edit `tools/test_all.py`, `qa/tests/epic_01/test_l3_integration.py`, `justfile`, `pyproject.toml`, `DEPENDENCIES.md`, `.env.sample`, `.gitignore`, `tools/secret_scan.py`, `tools/coverage_report.py` and `.github/workflows/skylos.yml`.
- [ ] Delete `scripts/probes/`, keeping every `scripts/probes/**/FINDINGS*.md`.
- [ ] Move `scripts/probes/server/p_app.py` to `scripts/live/server/p_app.py`, and edit `scripts/live/server/app2b_lanes.py`.
- [ ] Edit `scripts/live/library/e66_marks.py`, `scripts/live/qma/s18_ram.py` and `scripts/live/qma/cat_lanes.py`, which only mention the probes.
- [ ] Delete `qml/examples/`, `packages/qmf-core/examples/`, `packages/qmf-data/examples/`, `packages/qmf-registry/examples/`, `packages/qmf-risk/examples/`, `packages/qmf-venue/examples/` and `extensions/qmf-calendar-forex/examples/`.
- [ ] Delete `qml/tests/test_examples.py`, `qml/tests/test_conformant_bot.py`, `qa/tests/epic_12/test_l3_example_bot.py`, and every `test_*_examples.py` under `packages/qmf-core/tests/`, `packages/qmf-data/tests/`, `packages/qmf-registry/tests/`, `packages/qmf-risk/tests/` and `packages/qmf-venue/tests/`.
- [ ] Edit `extensions/qmf-calendar-forex/tests/test_registration.py`, `qml/tests/test_scaffold.py`, `qa/tests/epic_11/test_a_scaffold.py`, `qml/tests/test_generation_gaps_unfilled.py`, `packages/qmf-venue/README.md` and `extensions/qmf-calendar-forex/README.md`.
- [ ] Delete `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-16/research/query_hermes_sessions.py`, `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-16/research/dump_goldmine_range.py`, `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-16/research/dump_key_msgs.py` and `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-16/research/dump_strats_sessions.py`.

**Build.**

- [ ] Subtract. This whole PR is the subtraction. It has no `test-delete` row of its own, because the tests it deletes go with their folders.
- [ ] Safety fact. Nothing in the product imports these folders, and keeping the gates green is what makes the cut safe. Level 4 on the scratch copy `D:/Temp/audit/ground-core/cut`, whose run is in `D:/Temp/audit/chief/ground-long/cut.log`. That run shows 54 failed and 8 errors. Of those, 29 are the tests this PR deletes or edits (`test_examples` 15, `test_sssf_quality_gate` 6, `test_conformant_bot` 5, `test_scaffold` 1, `test_generation_gaps_unfilled` 2). The other 25 failures and the 8 errors come from what the scratch copy lacked, which is `release/`, `docs/`, `.github/`, `qmx-agents/` and a git repository, plus the known `test_ambient_scan` red. No product file changes, so no promise in `ground-core.md` section 2 is in reach. Keep `qa/tests/epic_12` green, because it builds its own `_world` and the layer gates keep its other tests.
- [ ] `deletion-9`. Delete `adws/` and `queue/`. Drop the `adws` row at `tools/test_all.py:65`. Delete `test_sssf_quality_gate.py`, which the audit's row missed. Delete `test_e1_i04_sssf_factory_gate_stamp_survives` from `test_l3_integration.py`, which the row also missed.
- [ ] `deletion-9`. Cut `justfile` lines 17 and 18, the recipes at lines 46 to 150, and `sessions`, `phases`, `tail`, `procs` and `obs`. Keep `test-all`, `ci` and the node import.
- [ ] `deletion-9`. Cut the factory lines in `pyproject.toml`, which are comments 1 to 23, 35 and 36, 59, 66, 130 and 131, 226 to 229, `[tool.mypy]` at 257 to 263, the ruff lines at 284 and 331, 424, and the comments at 235, 301, 326 to 330, 357, 405 and 506. Line 425 is `_bmad` and stays, with its words "same ruling as adws" cut.
- [ ] Trap. `testpaths = ["adws/tests"]` at `pyproject.toml:229` must change, not vanish, because a bare `pytest` with no target would search the whole tree (expected, not run). Point it at `tools/tests`, `qml/tests`, `qmb/tests` and `qmn/tests`, the suites `tools/test_all.py` names at the root.
- [ ] Trap. Leave `mypy`, `types-PyYAML`, `pydantic` and the others in the `dev` group, and do not touch `uv.lock`. CI runs `uv sync --frozen`, so removing them is a later step with `uv lock`.
- [ ] `deletion-9`. Cut the words at `DEPENDENCIES.md:92-101`, `.env.sample:4`, `.gitignore:44-45`, `tools/secret_scan.py:14,42`, `tools/coverage_report.py:26` and `skylos.yml:91-92`. `examples/apps` stays, because `test_apps.py`, `tools/lanes/*` and `docker-nodes.yml` use it.
- [ ] `deletion-5`. Delete `scripts/probes/` except the `FINDINGS*.md` files, because `qmx_router/gpt/translate.py:5` cites one. Move `p_app.py` beside `app2b_lanes.py` and repoint its imports at lines 35 and 137, because the live lanes stay until G-DEMO. Fix the stale words at `e66_marks.py:15`, `s18_ram.py:6` and `cat_lanes.py:327`.
- [ ] `deletion-8`. Delete the QML and QMF usage examples and their tests as the Files block lists. Do not delete `qmb/examples`, `examples/apps`, `packages/qmf-indicators/examples` or `packages/qmf-structure/examples`, which wait for his word. Drop `test_reference_usage_example_runs_clean` from `test_registration.py`. Edit `test_scaffold.py:26` and `test_a_scaffold.py:28`, which name the folder. Edit `test_generation_gaps_unfilled.py:60,380`, which read it. Cut `packages/qmf-venue/README.md:25-26`, the example line in the forex README, and `pyproject.toml:344-346`, keeping the `qmb/examples` line at 347.
- [ ] `deletion-10`. Delete the four Hermes scripts. No code names them. The evidence note at `release/evidence/setup.md:47` stays as history.

**You see.**

- [ ] Nothing changes in what you use. About 46,000 lines that misled anyone reading how to run QMX are gone, and the instructions at the top of the repository no longer describe the retired factory.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] No test is added, so `owner-red.log` holds one line beginning `NO-RED:` that gives this reason. The tests that must change on purpose are the ones the Files block edits, each because it named a deleted folder. Run `uv run --no-sync python -m pytest tools/tests/test_workspace_structure.py qml/tests/test_scaffold.py qa/tests/epic_11/test_a_scaffold.py qa/tests/epic_01/test_l3_integration.py -q`, adding the file only if the path exists at the head.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against `A/tests/SUMMARY.txt`. The coordinator runs `S/tools/run_tests.sh` at the head under `D:/QMX-worktrees/.ci-lock`. No model. Save `r01-whole.log`. Pass when the only failed tests are `test_the_windows_store_writes_reads_and_deletes_one_throwaway_entry`, `test_the_upkeep_switched_off_never_runs_while_rounds_and_the_drill_still_do` and `test_main_is_clean_on_the_real_workspace`, and each gate's exit code equals SUMMARY's.
- [ ] Lane 2. Fail-today proof. At the parent and at the head, run `git ls-files adws queue scripts/probes qml/examples` and `git grep -n -e adws -e scripts/probes -- '*.py' '*.toml' justfile .github ':!qa/_trace'`. `qa/_trace` is left out because it records the old tree. No model. Save `r01-gone.log`. Pass when the parent lists the folders, and the head lists only `FINDINGS*.md` files, with only the kept citation in the grep.
- [ ] Lane 3. At the head run `.venv/Scripts/python.exe -c "import qml, qmb, qmn"` and the same in `qmx-agents` for `qmx_host, qmx_control, qmx_engine`, then import `scripts/live/server/app2b_lanes.py` from its new neighbour. No model. Save `r01-imports.log`. Pass when each exits 0.
- [ ] Lane 4. At the head run `just --summary`, `uv run --no-sync python -m pytest --collect-only -q` and `git diff --stat 50c83a4e HEAD -- uv.lock`. No model. Save `r01-recipes.log`. Pass when `test-all` and `ci` are listed and no removed recipe is, collection stays inside the named suites, and `uv.lock` shows no change.
- [ ] Lane 5. Rerun the two commands from `ground-core.md` section 9 on the branch itself. No model. Save `r01-qml.log`. Pass when `qml/tests` and `tools/tests` fail only SUMMARY's known reds.
- [ ] Lane 6. `git diff --stat 50c83a4e HEAD -- qmx-agents qml/src qmb/src qmn/src packages/*/src extensions/*/src`. No model. Save `r01-noproduct.log`. Pass when the diff is empty.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r01-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r01-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r01-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r01-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Lines removed, and whole-repo seconds.
- [ ] Probe. `git diff --shortstat 50c83a4e HEAD`, and the `test-all` line of lane 1's summary.
- [ ] Baseline. `A/tests/SUMMARY.txt` gives `test-all rc=1 seconds=7149`.
- [ ] Rule. No fail rule, recorded for the trail. The audit's counts predict about 40,700 and about 5,700 lines. Explain any gap above 10% in the PR body.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r01-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Make the gates tell the truth (R02)

Phase A, clean ground. Source is `A/reports/ground-start.md` blocks I and K, and the whole-repo logs in `A/tests/`. A gate that always reads red hides the next real problem, and C-14's commits have never been read by anyone. Done when `ambient-scan`, the root types and the gates of the two red packages exit 0, and a reviewer has read the two unreviewed diffs.

Rows carried. `whole-repo-1` `whole-repo-2` `whole-repo-3` `whole-repo-4`

Proves. The red gates exit 0, and C-14's commits have a review on record.

**Depends on.** R01.

**Files.**

- [ ] Edit `tools/first_real_start.py` and `tools/tests/test_first_real_start.py`.
- [ ] Edit `tools/lanes/app_enable_hang.py` and `tools/lanes/two_hosts.py`.
- [ ] Edit `qmx-agents/packages/qmx-apps/tests/test_start_heartbeat.py` and `qmx-agents/packages/qmx-apps/tests/test_road_lease.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/first_start.py` and `qmx-agents/packages/qmx-host/src/qmx_host/node_link.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/tests/test_first_party_node.py`, `qmx-agents/packages/qmx-host/tests/test_heartbeats_loop.py` and `qmx-agents/packages/qmx-host/tests/test_connect_node_server.py`.

**Build.**

- [ ] Subtract. No `test-delete` row and no dead code sit in these files.
- [ ] Safety fact. These are markers and typing edits, so no behaviour moves. The script talks only REST, and its 14 tests with real throwaway git repositories hold today's behaviour, level 4. The only product lines are `first_start.py:637` and `node_link.py:664`, and the second is harmless because deployment ids are strings, level 2. M10 must hold, guarded by `test_first_party_node.py`.
- [ ] `whole-repo-1`. Add `# ambient-scan: allow - <reason>` on `first_real_start.py:200,659,662`, because this script really is a composition root. Do the same in `tools/lanes/app_enable_hang.py:137,141` and `tools/lanes/two_hosts.py:148,149,255,275,278,284,300,302,408`. The marker is line-scoped (`tools/ambient_scan.py:422`), so it goes on the line of the read. `test_ambient_scan.py` stays red until all three files carry it.
- [ ] `whole-repo-2`. Fix the 9 root type errors listed in `A/tests/types-root.log`, which are `first_real_start.py:309,411,440,444,452,486,502,730` and `test_first_real_start.py:375`. Type the answer bodies, drop the two unnecessary casts, and handle the `None` at line 730. Change no check.
- [ ] `whole-repo-3`. In the apps package, format `test_start_heartbeat.py` and fix its import block, its unused `noqa` at line 21 and its long line at 31, the import block in `test_road_lease.py`, and the one private-use type error at line 21.
- [ ] `whole-repo-4`. In the host package, fix the two import blocks in `test_connect_node_server.py` and `test_heartbeats_loop.py`, and the 19 type errors in `A/tests/types-qmx-host.log`. Type `first_start.py:637`, and make the `node_link.py:664` set entry a checked string.
- [ ] Record the two known test reds in `S/evidence/r02/lows-for-coordinator.md` with their causes, and the coordinator files them in `S/lows.md`. `test_the_windows_store_writes_reads_and_deletes_one_throwaway_entry` is red only because the audit's credential guard refuses `CredReadW`, as it should in these lanes. Rerun `test_the_upkeep_switched_off_never_runs_while_rounds_and_the_drill_still_do` alone at the parent. If it passes alone, record it as a flake under load. If it fails alone, justify it in that same file for `BACKLOG.md`. Fix neither here.
- [ ] Replace PR 328's placeholder body with a true one, using `gh pr edit`. PR 328 holds C-14, on top of PR 327, which holds C-35, C-29 and C-38. State that R03 carries PR 327's open blocker, the uv wait with no limit at `supervisor.py:527`, because `RESUME.md` is wrong that `50c83a4e` fixed it. That commit fixed a heartbeat lock.
- [ ] Have this PR's reviewer also read the two diffs nobody has read, `git diff f9607cd4 50c83a4e` (C-14's four commits, 1,542 lines) and `git diff db948daa f9607cd4` (PR 327's own diff). The reviewer writes `S/evidence/r02/review-findings.md`, one line per real finding with its evidence level and the PR id whose Files touch it. Every later dispatch carries its lines.

**You see.**

- [ ] Nothing changes on a screen. The checks that guard the code stop reading red for reasons nobody acts on, so a new real problem now shows up instead of hiding behind an old one.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] No test is added. `test_main_is_clean_on_the_real_workspace` is the existing test that goes green here, and `test_first_real_start.py` must still pass 14 of 14. Run `uv run --no-sync python -m pytest tools/tests/test_ambient_scan.py tools/tests/test_first_real_start.py -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `tools/tests/test_first_real_start.py`, `tools/tests/test_ambient_scan.py`, `qmx-agents/packages/qmx-apps/tests/test_start_heartbeat.py`, `test_road_lease.py`, and in the host package `test_first_party_node.py`, `test_heartbeats_loop.py`, `test_connect_node_server.py`, `test_node_link.py` and `test_node_link_refused.py`, at the parent and the head. No model. Save `r02-regression.log`. Pass when the head fails nothing the parent passes.
- [ ] Lane 2. Fail-today proof. At the parent and the head run `poe ambient-scan`, root `poe types`, and `poe fmt-check`, `poe lint` and `poe types` in `qmx-apps` and `qmx-host`. No model. Save `r02-gates.log`. Pass when the parent gives the rc=1 lines of `A/tests/SUMMARY.txt` and the head gives 0 on all of them.
- [ ] Lane 3. Run `test_main_is_clean_on_the_real_workspace` at the parent and the head. No model. Save `r02-ambient.log`. Pass when it fails at the parent and passes at the head.
- [ ] Lane 4. The coordinator runs this one after the reviewer reports, because the reviewer writes the file. Read `S/evidence/r02/review-findings.md`. No model. Save `r02-review.log`. Pass when it names both diffs by commit range and each finding has a level and a target PR, or it says no real finding with the reader's reason.
- [ ] Lane 5. The rehearsal from `S/tools/owner_lane_c14.py rehearsal <wt> 18941`, on a throwaway folder. No model. Save `r02-rehearsal.log`. Pass when its lines match `owner-c14-rehearsal.log` from the last build.
- [ ] Lane 6. `git diff --stat <parent> HEAD -- 'qmx-agents/**/src/**'`. No model. Save `r02-product.log`. Pass when only `first_start.py` and `node_link.py` appear.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r02-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r02-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r02-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r02-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds of `poe ambient-scan`.
- [ ] Probe. Lane 2.
- [ ] Baseline. `A/tests/SUMMARY.txt` gives 8 seconds.
- [ ] Rule. No fail rule, recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r02-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Let a repair reach him and stop an install stalling everything (R03)

Phase A, clean ground. Source is `A/reports/ground-core.md` blocks A and B, and `A/reports/ground-start.md` block I and its new defects. Today a repair to an installed app or a shared library never reaches his folder, and one install holds up every call to every app, his kill included. This PR must land before any PR that edits `qmx-agents/apps/*`. Done when foundation checks 1 and 2 pass.

Rows carried. `core-n1` `known-2` `triage-7` `triage-4` `triage-5` `triage-8` `p5c-3` `start-n1`

Proves. A repair reaches an installed app at the next start, and a call answers within a second while another app installs.

**Depends on.** R02.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/first_start.py` and `qmx-agents/packages/qmx-host/src/qmx_host/connect_node.py`.
- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/service.py`.
- [ ] Edit `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` and `qmx-agents/packages/qmx-apps/tests/test_restart_backoff.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/tests/test_first_party_node.py` and `tools/tests/test_app_env_fresh.py`.
- [ ] Create `qmx-agents/packages/qmx-apps/tests/test_install_holds_nothing.py`, `qmx-agents/packages/qmx-host/tests/test_repair_lands.py` and `qmx-agents/packages/qmx-control/tests/test_event_rows.py`.

**Build.**

- [ ] Subtract. No `test-delete` row sits in these files. The stale sentence at `enable_first_party` ("An app already installed is only started") goes with the change below.
- [ ] Safety fact. The volume belongs to the app id and a re-install of the same bytes is accepted, so an upgrade at host start loses no data and needs no new door. Level 4 for a non-money app, from `sup_proof.py` sections C to G. For a money app the signed version keeps running until he signs, by M5, level 4 from `test_a_money_app_restarts_only_its_active_signed_version`. The same-bytes install is not safe on a money app, because it rebuilds the environment of the signed hash, since environments live at `envs/<hash>` (`supervisor.py:509`) and the hash covers only the app folder. So new order code would run under the old signature and nothing would ask him (`S/proofs/plan-review-a/money_env.py`, level 4). M1, M2, M4, M5, M6, M7, M8 and M10 must hold. By call 11 these supervisor changes have one reason, that a repair must reach him and his kill must never wait on an install, and a library repair reaches a money app only as a new version for him to sign.
- [ ] `core-n1`. In `Supervisor._install` (`supervisor.py:441-484`), hold `self._lock` for the catalog checks and the image copy, release it for `_install_environment`, then take it again for the second image check, the `road.register` call and the log. The per-app `VolumeLease` taken in `install` keeps two installs of one app apart, and `start` takes the same lease, so an app cannot start during its own build. `call`, `run_job`, `status` and `_log` all take this lock today, and the node's reads and controls go through `call` (`node_link.py:322-343`, level 2).
- [ ] Trap. A plain `subprocess.run(timeout=...)` does not fix `known-2`. Against a child that left a process holding the pipe, `run(timeout=3)` raised only after 25.3 s, because on Windows `run` waits for the pipe after the kill (`pipe_proof.py`, level 4).
- [ ] `known-2`. In `_install_environment` (`supervisor.py:528-547`), send uv's output to a file under the home's logs instead of a pipe, and read the `error:` and `Caused by:` lines from that file. Run uv so the whole tree can be killed, with `WindowsJob` (`qmx_apps/windows_job.py`) on Windows and a process group elsewhere. Past a wall limit, kill the tree and raise `AppError("install_stuck", ...)` naming the app, the limit and the log file.
- [ ] `known-2`. Make the wall limit the setting `[apps] install_limit_s`, default 1800. Add `apps` to `SettingsSection` in `service.py` with its defaults beside `TELEMETRY_DEFAULTS`, and pass the value in `app_runtime` the way `call_depth` is. By call 12 it stops no usage, so the no-caps rule is not touched.
- [ ] `triage-7`. Add `refresh_first_party(runtime, app_id, folder)` beside `enable_first_party` in `first_start.py`. Before an app starts, compare `Definition.load(folder).hash` with what is selected, and compare `path_sources(folder)` with the environment's `BUILT_FROM` record. If the hash differs, call `runtime.install(folder, trust="first_party", expected_id=app_id, expected_hash=<selected hash>)`. If only the path sources differ, install the same bytes, which is accepted and reruns the build (`sup_proof.py` G). The path-source branch is for non-money apps only. A money app is never rebuilt under its signed hash. Its status says a library repair waits for a new signed version. The bump in PR mechanics brings that version.
- [ ] `triage-7`. After a refresh, a non-money app with an active version takes `road_proof` and its publish, because `start` prefers `active` (`supervisor.py:678-695`) and a connected folder would otherwise keep the old version. A money app stops at "waits for your signature" and keeps running its signed version, which is M5.
- [ ] `triage-7`. Use `refresh_first_party` in `connect_node._install` (`connect_node.py:440`) too, in place of `_installed(apps, app) or ...`. `_server_install` (`:1272`) keeps `_installed(...) or install`, because `ServerApps.install(app_id)` takes only a name on the server (`:1080`), with no folder, head or local `BUILT_FROM` to compare, and the server's own host start runs `enable_first_party`. `first_start` imports `connect_node`, and `connect_node` imports `first_start` inside a function at `:553`. Keep that shape, because a new top-level import brings back the circular import of `known-5`.
- [ ] `p5c-3`. In `enable_first_party`, give each app its own try. One bad app must not stop the others. Catch per app, start the old version if a refresh failed, and name who failed and why in the log and in `status`. Today the first refusal ends the loop and the node sits last in the list (`first_start.py:624-627`). The caller's `except` in `host.py:929` stays for the unreadable list.
- [ ] Add a literal table to `test_shipped_apps.py`, one row per app and version, holding a line-ending-normal digest of its folder. Rows are append-only. A PR that edits an app and forgets the version then fails CI, not his next start.
- [ ] Trap. `image_hash` reads raw bytes and `core.autocrlf` is true on this PC, while `.gitattributes` fixes only `*.sh`, `*.service` and `*.conf`. A table of raw `image_hash` values would fail on any checkout with other line endings, so the test computes its own digest with `\r\n` read as `\n`. Level 3, read at `qmx_apps/manifest.py:328` and in the git config.
- [ ] `triage-4`. In `_heal` (`supervisor.py:1025-1040`), start counting again when the instance ran longer than `backoff_max_seconds`. Today four crashes, each after 3 s of health, waited 5, 10, 20 and 40 s, and `Healing.trips` clears only on his stop (`sup_proof.py` H, level 4). The doubling for a crash loop stays, so `test_restart_backoff.py` still holds, because those tests restart at once, under that bound. Wrap the body of `_restart_loop` in one `try`, so an error outside the inner `try` cannot leave the app never restarting.
- [ ] `triage-5`. In `_serve` (`supervisor.py:856-865`), keep the heartbeat and breach check at 0.25 s, but call `_persist` only when status, pid or breaker change, plus a slow metrics beat of 30 s. While an app runs, `status()` reads the live instance, not the row (`supervisor.py:628-631`, level 2). The UI's live metric rate is what changes, so add one line to `S/BACKLOG.md` for the UI session.
- [ ] `triage-5`. In `ControlService`, prune `events` rows by age at start, and make `_push_totals` skip the row when the totals did not change. Today one app writes 3.1 `apps` rows and 3.1 `aggregates` rows a second, about 200 MB a day per app, rough and WAL included (`sup_proof.py` B). `control.db` is in the result backup class, so copies carry it.
- [ ] `triage-8`. At `supervisor.py:1343-1344`, retry the read and the unlink of the answer file on `PermissionError` inside the existing poll loop. A tight read after the replace raised in 2,943 of 3,000 rounds (`done_race.py`, level 4). That proves the window exists, not the real rate.
- [ ] `start-n1`, probe first. Write a test with a real fixture app declaring `restart = "backoff"` and a tool that sleeps past 30 s, and record what happens. By reading, `call` (`supervisor.py:1191-1196`) runs `self.stop(app_id)`, which cancels healing, so the app stays down, level 2. Save the run as `owner-timeout-probe.log`.
- [ ] `start-n1`, then decide against his breaker. An app that opted into back-off takes `self._trip(instance, "tool_timeout")` and goes down the healing path, so `_serve` calls `_heal`. An app that did not opt in keeps `self.stop`. His stop still cancels a pending restart. A money app restarts only its active signed version. All of M5 and M6 hold. If the probe shows any of those broken, stop here and report it, by call 20. The caller still gets `tool_timeout` with status 504, and `test_promote.py:88` pins that word.

**You see.**

- [ ] When a repair lands, QMB and the MIS pick it up at the next start by themselves and keep their data. The trading node waits for your signature before it changes, and a repair to any library it uses arrives as a new version for you to sign. If one app is stuck installing, your kill and every other app still answer at once, and a stuck install stops with a plain message after 30 minutes instead of hanging for ever.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_repair_lands.py::test_a_changed_app_runs_its_new_hash_with_its_data_at_the_next_start`. Real supervisor, uv patched out as `sup_proof.py` does. After changing `server.py` and the version, `enable_first_party` makes `status["definition_hash"]` equal the new hash, and the marker file reads `"kept"`. Fails today.
- [ ] `test_repair_lands.py::test_a_money_app_keeps_its_signed_version_until_he_signs`. After a refresh of a money fixture, `start` still runs the old hash and `status` names the signature. Also `test_one_bad_app_does_not_stop_the_others`, where a failing first app leaves the second `running`.
- [ ] `test_repair_lands.py::test_a_library_repair_does_not_touch_a_signed_money_app`. On a signed money fixture with only a path-source digest changed, a host start does not call uv, `start` runs the signed hash, and `status` says a library repair waits for a new signed version. Today uv rebuilds the signed hash's environment and nothing asks him (`money_env.py`).
- [ ] `test_install_holds_nothing.py::test_a_call_answers_within_a_second_while_another_app_installs`. Today 44.1 s (`stall_proof.py`). Also `test_a_stuck_install_fails_by_name`, with `install_limit_s = 3` and a grandchild holding the output, which gives `install_stuck` in under 6 s with no process left.
- [ ] `test_restart_backoff.py` gains `test_a_calm_crash_waits_five_seconds_again` and `test_a_tool_timeout_on_an_opted_in_app_heals`. Existing tests there stay as they are.
- [ ] `test_event_rows.py::test_a_quiet_app_writes_few_rows`. Over 10 s a running app adds at most 2 `apps` rows and at most 2 `aggregates` rows. Today 31 of each.
- [ ] `test_app_env_fresh.py` gains `test_a_changed_library_reaches_the_app_env_at_the_next_start`, with real uv, which the coordinator runs. Tests that change on purpose are in `test_first_party_node.py`, where the fake supervisor must learn `install` with a head, because an installed app now gets compared.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run the `qmx-apps` and `qmx-control` suites and `qmx-host` `test_first_party_node.py`, `test_connect_node.py`, `test_connect_node_server.py`, then `tools/tests/test_app_env_fresh.py` and `test_app_env_data.py`, at the parent and the head. The second pair builds real environments and calls uv. No model. Save `r03-regression.log`. Pass when the head fails nothing the parent passes.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/ground-core/sup_proof.py` at the parent and the head with `proof_at.sh agents`. No model. Save `r03-sup.log`. Pass when section C prints "same as old True" at the parent and the new hash at the head, and section H waits 5 s after each calm crash at the head.
- [ ] Lane 3. Run `S/proofs/ground-core/stall_proof.py` at the parent and the head. No model. Save `r03-stall.log`. Pass when "answered after" reads about 44 s at the parent and under 1 s at the head.
- [ ] Lane 4. A real install with real uv on a throwaway folder. Start a host with QMB broken by a bad lock, then with a repaired library. No model. Save `r03-host.log`. Pass when the host names QMB's failure, the MIS and the node still start, and after the repair QMB's environment holds the changed module. This is wall check W5.
- [ ] Lane 5. The money path. On a fixture money app with a signed version, change a file and restart, then change a library in its lock and restart. No model. Save `r03-money.log`. Pass when the old hash runs both times, the signed hash's `qmx-sources.json` does not change, and the status names the signature and then the wait for a new signed version.
- [ ] Lane 6. Leave one app running for 10 minutes and count rows in `control.db`. No model. Save `r03-rows.log`. Pass when the row rate is flat and under 1 row per 10 s per app.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r03-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r03-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r03-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r03-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds a running app takes to answer during another app's install, and rows per second per running app.
- [ ] Probe. Lanes 3 and 6.
- [ ] Baseline. 44.1 s, and 6.2 rows a second, about 200 MB a day, rough.
- [ ] Rule. Fails above 1 s for the answer, or above 1 row per 10 s for a quiet app.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r03-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Refuse what a unit cannot run (R04)

Phase B, the unit. Source is `A/reports/ground-unit.md` blocks A, B step 1 and C's trap, with the trial in `A/reports/ground-long.md`. Today a unit passes check and compile with parts that never run, so he reads one strategy and tests another. Every door reaches the compiler, because `check` calls `compile_unit` when the layers pass (`check/run.py:68`). So one change in one place removes every false comfort at once. Done when foundation check 4 passes, and check 3 passes for everything but the list R05 empties.

Rows carried. `p0a-1` `p0a-3` `p0a-2` `p0a-5` `p0a-6` `p0a-7` `p0a-8` `p0a-9` `p1a-5` `p1b-2` `p0a-21` `p0a-24` `p1a-13` `p1a-14` `p1a-15` `p1b-21`

Rows in part. `p1a-1` by refusal of its volume and session blocks. `p1a-2` and `p1b-1` by refusal, and the exits really run after the risk session agrees the socket.

Proves. A long-only unit makes zero short fills, and each unrunnable part refuses with a pointer.

**Depends on.** R03.

**Files.**

- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/src/qml/check/layers.py`.
- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qml/tests/test_check_layers.py`, `qml/tests/test_compile_dummy.py` and `qml/tests/test_socket_contracts.py`.
- [ ] Edit `qml/tests/test_numbers.py`, `qml/tests/test_surface_old_law.py`, `qml/tests/test_wave1_indicators.py`, `qml/tests/test_wave1_exits.py` and `qml/tests/test_wave1_statistics.py`.
- [ ] Create `qml/tests/test_unit_refuses.py` and `qml/tests/test_nothing_silent.py`.
- [ ] Edit `qmx-agents/apps/qmb/tests/test_qmb_app.py` and `qmx-agents/apps/qmb/app.toml`, then `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` for the version row.
- [ ] Edit `qmx-agents/apps/trading-node/app.toml`, by call 11, because `qml` is in its lock, with its row in `test_shipped_apps.py`.
- [ ] Edit `qmx-agents/packages/qmx-judge/tests/test_conformance.py`, which pins QMB's version.

**Build.**

- [ ] Subtract. Delete `p1a-15`, which is `test_blocks_left_missing_by_the_unit_runtime_say_which_input_it_does_not_pass` (`test_wave1_indicators.py:257`) and `test_inside_a_unit_today_an_exit_stays_silent_and_says_so` (`test_wave1_exits.py:343`). They keep a known defect green and run no unit. Delete `p1a-13` (`test_wave1_statistics.py:146`), `p1b-21` (`test_socket_contracts.py:381`), `p0a-21` (`test_numbers.py:72` and `:271`) and `p0a-24` (`test_surface_old_law.py:111`, keeping the repo scan).
- [ ] Delete `p1a-14` (`test_wave1_statistics.py:249`) only after `test_nothing_silent.py` exists. Its row says the sweep at `test_wave1_indicators.py:257` covers it, and `p1a-15` deletes that sweep, so the new sweep is what carries both.
- [ ] Safety fact. No shipped unit document uses the fields this PR refuses, and a refusal changes no decision for a unit that still compiles. Level 4 from `ground-long.md`, where the refusals over all of QML gave 1,445 passed and 1 failed, and over `qmb/tests/test_unit_handler.py` and `test_run_journal.py` gave 18 passed. These must hold from `ground-unit.md` section 2, the dummy with 25 entries on the shipped month and close at bar 48 on both sides, `test_check_layers.py`'s corpus gate, the Book door refusing format 3, and `restore_unit`'s cold start. From `ground-core.md` M8 must hold, because the lander compiles before any try opens.
- [ ] `p0a-3`. Grow `_shape_problems` (`compiler.py:493`) into the list of what the format runs. Refuse `unit.sessions` as `sessions_not_built` at `/sessions`. Refuse any `market.settings` as `settings_not_built` at `/markets/<i>/settings`. Refuse `position_limit.per_instrument` other than 1 as `limit_not_built` at `/position_limit`. Refuse a stream `price` other than `bid_ask` as `price_not_built` at `/streams/<i>/price`. The trial's forms are in `S/proofs/ground-unit/plug/refuse_trial.py`.
- [ ] Trap. Refusing sessions fails one shipped test, `test_a_session_on_either_market_calendar_is_not_an_error` (`test_check_layers.py:240`), because it asserts through `check`. Point it at `check_layers`. It tests layer D and stays true. This is the one test the long trial moved.
- [ ] `p0a-1`. Make sides follow `direction`. In `compile_unit` (`compiler.py:530`) build only the sides `unit.direction` trades, as `S/proofs/ground-unit/p2.py` section A does. `both` keeps both, so the dummy's decisions are unchanged.
- [ ] Trap. Dropping a side makes `new(dummy, {"/direction": "long"})` refuse with `motion_source` at `/numbers/rsi_high/motion/source`, because `_motion` (`compiler.py:371`) wants every derived number bound. Make `_motion` skip a number bound only on a dropped side. A number bound on no stated side still refuses. Run at level 4 by hand with the short side and `rsi_high` removed, 2 long and 0 short.
- [ ] Bump `COMPILER_FORMAT_VERSION` to 2 (`compiler.py:84`), because the direction change alters a decision. Nothing pins it outside the compile package (`git grep`, level 2), and nothing has landed on his machine. Say "format 2" in the refusal words at `compiler.py:495-499`.
- [ ] Trap, call 2. The dummy itself declares `"at": "market_day_close"`, as do three corpus twins and the `b-build-and-prove` fixture, so refusing cadence `at` kills the dummy. Refuse it only when `at` is the sole cadence, as `cadence_not_built` at `/numbers/<name>/motion/cadence`. When `at` sits beside `every_closed_trades`, add a warning in `check/layers.py`. No document changes and no fingerprint moves.
- [ ] `p0a-7`, call 3. Refuse a slot whose role is outside context, location, setup, trigger, confirmation, filter and entry_order, as `role_not_built` at `/logic/<side>/slots/<name>/role`. Today a slot written as `veto` is a must-hold condition, so the unit enters only when the veto fires.
- [ ] `p0a-5`. Refuse a second stop, a second target or a second per-bar exit as `exit_not_built` at `/exit_set/<i>`. Today two targets make every step with an entry refuse, and a second stop is never run.
- [ ] `p1a-2` and `p1b-1`, call 6. Refuse by rule, not by name, so an agent's block of the same shape refuses too. A per-bar exit (`OutputType.EXIT_ACTION`) with any input port gets `exit_not_built`. A stop (a price `LEVEL` with no `stop_price` port) with an input port of `stream_kind` `position` gets `exit_not_built`. Test the kind, because no port is named `position`. The trails' port is `entry_price`, and by port name they would pass (`S/proofs/plan-review-a/a1.py`, level 4). That catches `unrealised-profit-cap`, `roi-table-exit`, `peak-holdings-giveback-exit`, `offset-gated-trailing-stop`, `stepped-profit-stop` and `profit-fraction-trailing-stop`. It passes `swing-stop-buffer`, `target-r-multiple` and `time-exit-bars`. The message says the exit is not built yet and points at the risk session's socket.
- [ ] `p0a-8`, call 1. Refuse a unit with no price stop as `stop_not_built` at `/exit_set`. Whether such units are allowed is the risk session's.
- [ ] `p0a-2`. At `protocol/unit.py:433`, use `next(..., None)` so a unit may have no time exit, since UT-18 calls that a warning. `exits` returns when there is no timer. Keep the reason code `time-exit` for that block.
- [ ] `p0a-6` and `p1a-5`. Make compile build every instance once inside one guard, including the slow rules first made at `_Core.__init__` (`unit.py:279`) and the unguarded `make` calls in `_warm_up` (`compiler.py:449`, `:464`). Turn `ValueError` and `KeyError` into a problem with a pointer to the binding or number. Then `check` lists a block parameter of `period 0` instead of throwing, and a missing rule setting fails at check instead of at `construct_unit`.
- [ ] `p0a-9`. In layer B (`check/layers.py:386`), when a side is a `MirrorSide`, refuse every bound block whose `face.mirroring` is not `supported`, as `bad_mirror` at `/logic/<side>/mirror_of`, with the hint "state both sides". 102 of 112 blocks say `not_applicable`, and QML-17's own line asks for this.
- [ ] Trap, not named by the report and not in the long trial. `test_a_number_both_sides_bind_keeps_one_window_per_side` (`test_compile_dummy.py:272`) mirrors the dummy's long side, and `ema` and `market-next-open` say `not_applicable`, so it now refuses. Rewrite its short side as an explicit copy of the long slots. Its expected windows stay `derived.short.rsi_low: 286`. Level 2, read and not run, so run `qml/tests` with this check on.
- [ ] Trap, the QMB bump. `World.conformance` defaults to version `1.0.0` (`test_conformance.py:97`) and runs the shipped app, and `run_conformance` refuses any other version (`qmx_judge/conformance.py:445-447`), so this PR's bump turns that file red. Have `World.conformance` and the literals at `:173`, `:185`, `:252` and `:307` read `qmx-agents/apps/qmb/app.toml`, so later bumps need no edit there. Lines `:223` and `:234` stay, because `default_tester` stays and `_check_default_tester` returns early on the current value (`qmx_control/service.py:1160`). Level 3.
- [ ] `p1a-1`. Add one table in `compiler.py`, `BLOCKS_NOT_BUILT`, keyed by pin. Name `accumulation-distribution@1`, `chaikin-oscillator@1`, `force-index@1`, `market-facilitation-index@1`, `money-flow-index@1` and `on-balance-volume@1` as needing volume, by call 5. Name `initial-balance-high@1`, `initial-balance-low@1`, `initial-balance-range-extension@1`, `session-running-high@1`, `session-running-low@1`, `session-running-range@1`, `tpo-point-of-control@1`, `tpo-value-area-high@1`, `tpo-value-area-low@1` and `vwap-session-anchored@1` as needing the market's clock, by call 4. A binding on one of them refuses as `block_not_built`, with what it needs. A pin alone does not refuse, because the test helper pins every stdlib block.
- [ ] `p1b-2`. Replace the evidence in `_exit_breaks` (`test_socket_contracts.py:161-182`), which feeds `series`, `entry_price` and `stop_price` that no host passes. Add one test through `compile_unit` and `on_instant`, where the shipped per-bar exit closes at bar 48 and a capped exit refuses. A risk-session exit can then no longer pass the contract and do nothing.

**You see.**

- [ ] When an agent writes a unit using something QMX cannot run yet, such as a London-only session, a setting for one market, a second stop, a profit-cap exit or a VWAP rule, the check now says no and names the field. Before, it said pass and traded something else.
- [ ] A unit written as long only now never sells short. You can ask the copilot to make a long-only copy of the dummy unit and backtest it, and the result shows no short trades.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_unit_refuses.py::test_a_long_only_dummy_enters_long_only`. `new(dummy, {"/direction": "long"})` driven over the shipped slice gives `{"long": 2, "short": 0}`, the count `p2.py` measured with the side removed by hand. At the parent the same document also enters short.
- [ ] `test_unit_refuses.py::test_each_part_format_2_does_not_run_refuses_with_a_pointer`. One parametrized table of a document edit and its literal `(kind, where)`, one row each for sessions, settings, limit, price, sole cadence `at`, role `veto`, two stops, two targets, two per-bar exits, the six exits, no stop, a volume block, a session block and `period 0`. One more row is the dummy with `short: {"mirror_of": "long"}`, expected `bad_mirror` at `/logic/short/mirror_of` with the hint, because no other test uses `mirror_of` once `test_compile_dummy.py:272` is rewritten. Each passes check and compiles at the parent.
- [ ] `test_nothing_silent.py::test_every_stdlib_block_acts_or_refuses`. Foundation check 3. For each of the 112 blocks, drive it as the only trigger over the shipped month through `check`, `compile_unit` and `on_instant`, and bind it as an exit the same way. Build the documents as `trigger_doc` in `S/proofs/ground-unit/p4.py` does, feeding a `bars` port `m15` and a `series` port `m15.close`, with each parameter at its default. Each one refuses with a non-empty `where`, or its output is read as a condition or fires. A block whose output is read and never fires over the month goes in a literal `READ_NEVER_FIRED` list, which the test asserts equal, so a change shows. Blocks R05 brings to life go in a literal `PENDING_R05` list with a reason each, and the assertion is `silent == PENDING_R05`. R05 deletes `PENDING_R05`.
- [ ] `test_qmb_app.py::test_a_long_only_unit_makes_no_short_fills`. Foundation check 4. Real QMB job through the real lander, on the module's `world` fixture. The result's trades count 0 with `side == "short"`, and the same run with `both` counts at least 1.
- [ ] Tests that change on purpose are `test_check_layers.py:240`, `test_compile_dummy.py:272`, `test_socket_contracts.py:161-182`, and `test_qmb_app.py:191` for the version. `test_compile_dummy.py` must stay green otherwise. Run `uv run --no-sync python -m pytest qml/tests -q -n 2`, and the coordinator runs the QMB app test.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qml/tests`, `qmb/tests/test_unit_handler.py`, `qmb/tests/test_run_journal.py`, `qmx-agents/packages/qmx-tools/tests/test_block_tools.py`, `qmx-agents/packages/qmx-engine/tests/test_templates.py`, `qmx-agents/packages/qmx-judge/tests/test_conformance.py` and `qmx-agents/apps/qmb/tests/test_qmb_app.py`, at the parent and the head. No model. Save `r04-regression.log`. Pass when the head fails nothing the parent passes, apart from the tests the unit block changes on purpose.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/p0a/proof1.py` and `S/proofs/p1a/proof_units.py` at the parent and the head with `proof_at.sh root`. No model. Save `r04-proofs.log`. Pass when the parent shows each section passing check and doing nothing, and the head shows a refusal with a pointer or a working trade on every section.
- [ ] Lane 3. The dummy unchanged. Run `S/proofs/ground-unit/p2.py` at the head. No model. Save `r04-dummy.log`. Pass when "dummy on both sides unchanged" reads True, with 25 entries.
- [ ] Lane 4. Rerun the trial in `ground-long.md`, now as real code, over all of QML and the QMB unit path, then `qmx-agents/packages/qmx-tools/tests` and the host's unit tests that the trial did not reach. No model. Save `r04-wide.log`. Pass when the only tests that change are the ones named above.
- [ ] Lane 5. The door. On a throwaway folder call `unit_new` and `unit_check` on a unit with a session window and a VWAP binding. No model. Save `r04-door.log`. Pass when `unit_check` lists both refusals at once, each with its `where`.
- [ ] Lane 6. With a model, ask a copilot chat on `haiku` to make a long-only copy of the dummy. Save `r04-copilot.log`. Pass when the chat's `unit_check` passes and a backtest of it shows 0 short fills.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r04-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r04-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r04-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r04-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds of `compile_unit` on the dummy.
- [ ] Probe. A small timed loop of 20 compiles at the parent and the head, interleaved.
- [ ] Baseline. Record the parent's value first.
- [ ] Rule. Fails if the head is more than 25% slower, since the guard builds each instance only once.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r04-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Make slots tell the truth (R05)

Phase B, the unit. Source is `A/reports/ground-unit.md` blocks C and D and item `p0a-11` of block F. Today 78 of the 112 blocks can never hold a slot, so a trader's plainest rule cannot be written, and check stays green. This PR makes those rules work and refuses what still cannot work. REPAIR-SCOPE's "one new comparator block" is wrong by itself, because the comparator alone gives 0 entries under `all`. Done when foundation checks 3, 5 and 6 pass and `PENDING_R05` is gone.

Rows carried. `p1a-3` `unit-n1` `p0a-4` `p0a-13` `p0a-11`

Rows in part. `p1a-1` by feeding time, with session blocks still refused by R04's table and volume blocks waiting for the volume repair.

Proves. "ADX above 25" trades through a QMB job and level 99 gives none, and shorts move the tuned number.

**Depends on.** R04.

**Files.**

- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/src/qml/protocol/unit.py` and `qml/src/qml/motion/engine.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/value-above/1/block.py` and `qml/src/qml/blocks/stdlib/value-above/1/entry.json`.
- [ ] Create `qml/src/qml/blocks/stdlib/trend-floor-from-record/2/block.py` and `qml/src/qml/blocks/stdlib/trend-floor-from-record/2/entry.json`.
- [ ] Edit `qml/src/qml/unit/templates/dummy-trend-pullback.json`, to pin the fixed rule.
- [ ] Edit the `boundaries` words in `qml/src/qml/blocks/stdlib/lbma-gold-auction-clock/1/entry.json`, `qml/src/qml/blocks/stdlib/lbma-silver-auction-clock/1/entry.json`, `qml/src/qml/blocks/stdlib/eia-petroleum-status-report-clock/1/entry.json`, `qml/src/qml/blocks/stdlib/eia-natural-gas-storage-report-clock/1/entry.json` and `qml/src/qml/blocks/stdlib/perp-funding-settlement-clock/1/entry.json`.
- [ ] Edit `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/b-build-and-prove/fixtures/recorded/build.json` and `qmx-agents/packages/qmx-judge/src/qmx_judge/conformance_pack/fixture.json`, regenerated.
- [ ] Edit `qml/tests/test_nothing_silent.py`, `qml/tests/test_compile_dummy.py` and `qmb/tests/test_run_journal.py`.
- [ ] Create `qml/tests/test_value_above.py`.
- [ ] Edit `qmx-agents/apps/qmb/tests/test_qmb_app.py` and `qmx-agents/apps/qmb/app.toml`, then `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` for the version row.
- [ ] Edit `qmx-agents/apps/trading-node/app.toml`, by call 11, because `qml` is in its lock, with its row in `test_shipped_apps.py`.

**Build.**

- [ ] Subtract. R04 took the `test-delete` rows in these QML test files. Delete `PENDING_R05` from `test_nothing_silent.py` last, once it is empty. No dead code sits here.
- [ ] Safety fact. Bars gaining a field and slots gaining these two rules change nothing for the dummy, because its EMA is a price and stays a condition. Level 4, with entries identical in each trial (`S/proofs/ground-unit/p2.py` section D, `p4.py`, `p6.py`), and `QuoteBar` is untouched here. These must hold from `ground-unit.md` section 2, the dummy with 25 entries and close at bar 48, the corpus gate, and the golden files. M7 and M8 hold because no job or lander changes. Scope stays what the report says, so this PR holds no sizing rule and no exit rule.
- [ ] `p1a-3`, the feeder rule. Mark feeders in `SlotPlan` at compile, so the runtime decides nothing new. `condition` reads an `event`, `state` or `entry_order` output and a `series` of measure `price`. A feeder is a binding with any other output whose name is read by a later binding on that side or by a derived number's `source`. In `combine` (`unit.py:625`), leave feeders out of the conditions. Under `all` this gives 25 entries at level 1 and 0 at level 99 (`p6.py`, level 4). The trial's form is `skip_feeders` in `p6.py`, and it keeps a price series as a condition, which is what leaves the dummy identical.
- [ ] Trap, found by reading, level 2. A slot left with no conditions must hold. Today `combine` gives `any` and `k_of_n` false on an empty list, so a slot holding only a feeder would never hold, while under `all` it would. Decide this before the combiner runs, and test it under all three. `trigger_held` counts only a slot with at least one condition, because any held `trigger` slot sets it today (`unit.py:600`) and a failing side with it true writes a "near miss" row (`:709`), so a `trigger` slot of only feeders would write one on most bars. Level 3.
- [ ] `p1a-3`, the trap. A comparator with no feeder rule passes check and gives 0 entries under `all`, and 25 under `any`, which no agent would guess (`p3.py`, level 4). Both parts land together.
- [ ] `p1a-3`, the comparator. Add `value-above@1` with the source and face from `S/proofs/ground-unit/p3.py`, one `series` port of kind `series`, an `event` output, `mirroring: supported`, and a `level` parameter of measure `ratio`. Add one parameter `below`, measure `category`, range 0 to 1, default 0, where 1 flips the comparison, so "RSI below 30" can be written with the same one block. Give it literal cases in `test_value_above.py`.
- [ ] `p1a-3`, the refusal. Compile refuses a binding that can neither hold nor feed, as `binding_not_read` at `/logic/<side>/slots/<slot>/bindings/<i>`, with the hint to bind `value-above` to it. That removes the remaining false comfort. `parabolic-sar`, `fractal-high-level` and `fractal-low-level` output a price `LEVEL`, which `condition` does not read, so they refuse too unless a later binding reads them.
- [ ] `unit-n1`. In `condition` (`unit.py:612-620`), when the `series` input is a whole bar and not a Decimal, compare the bar's `close`, as `by_close` in `p4.py` does. 14 price series fed whole bars give 0 entries today. With this, as the only trigger on the shipped slice, `alligator-line` gives 1592, `heikin-ashi-close` 1154, `heikin-ashi-open` 1334, `ichimoku-senkou-a` 1595, `moving-average-fractal-adaptive` 1206 and `price-channel-midpoint` 1548 (`p4.py`, rerun by the plan's writer, level 4). The other eight are session or volume blocks and stay refused.
- [ ] `p1a-1`, call 4. In `resolve` (`unit.py:574`), add `"time": bar.knowable_at.value_ns` to the whole-bar answer. The blocks read `bar.get("time")`, the bar's close in nanoseconds UTC. This feeds the five clock blocks, which compute daylight saving themselves and read correctly.
- [ ] Trap. Feeding time turns on `p1a-6`, because ten session blocks would start acting on a fixed UTC second, an hour wrong most of the year, and silence would become a wrong trade. R04's `BLOCKS_NOT_BUILT` must still refuse all ten when this lands, and a test here asserts it. Do not add `volume` to the bar, by call 5.
- [ ] Trap. The five clock blocks' `boundaries` words say the runtime "does not yet pass a bars input its time", which this PR makes false. Change those five. `entry.json` words sit outside the block fingerprint, so no pin moves. The session and volume entries keep their words until their repairs. Clock blocks output seconds, so as a lone trigger they refuse with `binding_not_read`, and with `value-above` they gate.
- [ ] `p0a-4`. Fix the self-tuning rule as a new block version, the contract's `block_fix` row, never as an edit to version 1. `trend-floor-from-record@2` takes the size of the strength at `_edge` (`block.py:59`), so a short's negative stamp no longer clamps into bucket 0. Today a long journal moves 0 to 0.0001, and its mirror in shorts stays at 0 (level 4). Do not fix this in the motion engine, because that would change decisions with no fingerprint change.
- [ ] `p0a-4`. Point the dummy's `min_trend_strength.motion.rule` at `@2` in the template. The pin follows by itself, because `qmx_tools.gather.template()` pins what the document names, and `_own` reads by version. This is the first version 2 in stdlib, and the tests that walk `*/1/` skip it, so test it by name. Regenerate `build.json` and `fixture.json` with what made them, named in `golden.json`'s `made_by` line. If they cannot regenerate here, leave them on `@1`, which stays valid because an old version never changes, and say so in the PR body. The other pins of `@1` in `qml/tests/corpus/` and in tests stay as they are.
- [ ] `p0a-13`. In `calibrate` (`qml/motion/engine.py:124`) and at `unit.py:837`, add the mean R and the mean stamp to the row's `statistic`, beside `trades_read`. `results/journal.py:334` already carries the dict. Today the row holds only a count, so he cannot see why the number moved.
- [ ] `p0a-11`. In `_price` (`unit.py:206`), round to the record's `tick_size` and then to its digits, as `on_tick` in `p3.py` does. Every dummy stop stays identical on real ticks, EURUSD 0.00001 and XAUUSD 0.01 (level 4). This is plumbing, not a rule.
- [ ] Bump `COMPILER_FORMAT_VERSION` to 3, because a slot's truth alters decisions.
- [ ] `p1a-4` is not in this PR. It lands in R06 with `p1b-12`, because the settle length goes through `check_entry`, which R06 builds.

**You see.**

- [ ] You can now tell the copilot a plain rule such as "only enter when ADX is above 25", and it builds a unit that does that. Backtest it and it trades. Set the level to 99 and it places no trades. A rule QMX still cannot run gets a clear no that says what to add.
- [ ] A unit's self-tuned number now learns from its short trades as it does from its long ones, and the record says what it read when it moved.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_nothing_silent.py::test_every_stdlib_block_acts_or_refuses`. Foundation check 3, with `PENDING_R05` deleted, so the assertion is `silent == []`. `READ_NEVER_FIRED` changes on purpose where a block came alive. It also asserts the ten session blocks and seven volume blocks refuse as `block_not_built` with `time` in place.
- [ ] `test_compile_dummy.py` gains `test_a_value_rule_gates_under_all`. ADX with `value-above` in one slot under `all` gives 25 entries at level 1 and 0 at level 99 on the shipped slice. Today 0 at both. It also gains `test_a_whole_bar_price_series_compares_the_close`, with the six literal counts above.
- [ ] `test_compile_dummy.py` gains `test_the_floor_moves_alike_on_a_long_journal_and_its_mirror`. Both journals move `min_trend_strength` from 0 to 0.0001 at `@2`. Today the mirror stays at 0. Replay the fixed rule on the same journal at `@1` to show it still reads the old way.
- [ ] `test_run_journal.py` gains `test_a_short_only_run_moves_the_number_and_the_row_shows_why`. Foundation check 6. A real `run_loaded` of a short-only dummy with `motion on` writes a `calibration` row with `new != old`, and `statistic` holds `trades_read`, `mean_r` and `mean_stamp`.
- [ ] `test_qmb_app.py` gains `test_an_agent_writes_adx_above_25_and_a_job_runs_it`. Foundation check 5. Call `unit_new` and `unit_check` as the tool rows do, land the draft, and run a real QMB job. Level 25 lands a result with at least 1 trade, and the same unit at level 99 lands `zero_trades` true. Record level 25's count as a literal once the first green run gives it. Model the chain on `S/tools/owner-phase0.py`.
- [ ] Tests that change on purpose are `test_min_trend_strength_moves_one_shrunk_step_after_its_20th_trade` if the mirror fix moves its value, and `test_qmb_app.py:191` for the version. Name any other in the PR body with its reason. Run `uv run --no-sync python -m pytest qml/tests qmb/tests/test_run_journal.py -q -n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qml/tests`, `qmb/tests/test_unit_handler.py`, `qmb/tests/test_run_journal.py`, `qmx-agents/packages/qmx-judge/tests/test_conformance.py`, `qmx-agents/packages/qmx-engine/tests/test_templates.py`, `qmx-agents/apps/qmb/tests/test_qmb_app.py` and `tools/tests/test_dictionary_status.py`, at the parent and the head. No model. Save `r05-regression.log`. Pass when the head fails nothing the parent passes, apart from tests named on purpose.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/p1a/proof_units.py a` and `S/proofs/p1a/proof_conditions.py` at the parent and the head with `proof_at.sh root`. No model. Save `r05-proofs.log`. Pass when the parent shows check pass with no signal, and the head shows a trade or a refusal with a pointer on each.
- [ ] Lane 3. Run `S/proofs/ground-unit/p4.py` at the head with `proof_at.sh root`, and diff the first printed table against the literals above. Do not run `p3.py` or `p6.py` at the head, because they inject their own `value-above` and it would clash with the real pin. No model. Save `r05-counts.log`. Pass when the six counts match, the session and volume blocks read refused, and "dummy unchanged" reads True.
- [ ] Lane 4. Run `S/proofs/seams/parity.py 9 <folder>` at the head. No model. Save `r05-parity.log`. Pass when QMB and the node decide alike, 63 of 63, since both drive `unit_handler.py`.
- [ ] Lane 5. With a model, a copilot chat on `haiku` asked "build a unit that enters like the dummy but only when ADX is above 25, then backtest it on EURUSD for March 2025". Save `r05-copilot.log`. Pass when the journal shows `unit_new`, `unit_check` and `backtest_run`, and the result has trades.
- [ ] Lane 6. A golden check of `value-above` with `tools/dictionary/golden_talib.py`'s harness shape, against the literal table. No model. Save `r05-golden.log`. Pass when each case matches.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r05-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r05-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r05-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r05-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Steps per second of the dummy over the shipped month.
- [ ] Probe. `S/proofs/ground-unit/p2.py`'s drive, timed at the parent and the head, interleaved.
- [ ] Baseline. Record the parent's value first.
- [ ] Rule. Fails if the head is more than 10% slower, because `resolve` and `combine` run on every bar.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r05-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Check the dictionary and give session blocks the market's clock (R06)

Phase B, the unit. Source is `A/reports/ground-unit.md` blocks C (`p1a-6`), E, G and H. The dictionary's own rules exist but do not run while QMX runs, so a saved entry can take another's name, and every published page reads status None. Session blocks read one fixed UTC second, an hour wrong from March to November. `lifecycle.auto_paper` contradicts his rule that every move toward paper is his click. Done when foundation check 7 passes and a session block opens at the real cash open on both sides of a clock change. This ends phase B, so a whole-repo run follows it.

Rows carried. `p1a-4` `p1b-11` `p1b-12` `p1b-13` `p1b-14` `p1b-15` `plan-check-5` `p1b-6` `p1b-7` `p1a-6` `p0a-22` `p0a-23` `p0b-23` `p1a-16` `p1a-17` `p1b-19` `p1b-20`

Rows in part. `p1a-1` by giving nine session blocks a true clock, with `vwap-session-anchored@2` and the volume blocks still refused.

Proves. The dictionary at full size has no page with status None, a clash is refused, and a session opens at the real cash open.

**Depends on.** R05.

**Files.**

- [ ] Edit `qml/src/qml/catalogue/entry.py`, `qml/src/qml/catalogue/index.py` and `qml/src/qml/blocks/api.py`.
- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/src/qml/lifecycle/machine.py`, `qmx-agents/packages/qmx-host/src/qmx_host/lifecycle.py`, `qmx-agents/packages/qmx-host/src/qmx_host/promote.py` and `qmx-agents/packages/qmx-control/src/qmx_control/service.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/host.py`, `qmx-agents/packages/qmx-host/src/qmx_host/publish_collection.py` and `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`.
- [ ] Create version 2 of ten blocks, each folder with `block.py` and `entry.json`. They are `qml/src/qml/blocks/stdlib/initial-balance-high/2/`, `qml/src/qml/blocks/stdlib/initial-balance-low/2/`, `qml/src/qml/blocks/stdlib/initial-balance-range-extension/2/`, `qml/src/qml/blocks/stdlib/session-running-high/2/`, `qml/src/qml/blocks/stdlib/session-running-low/2/`, `qml/src/qml/blocks/stdlib/session-running-range/2/`, `qml/src/qml/blocks/stdlib/tpo-point-of-control/2/`, `qml/src/qml/blocks/stdlib/tpo-value-area-high/2/`, `qml/src/qml/blocks/stdlib/tpo-value-area-low/2/` and `qml/src/qml/blocks/stdlib/vwap-session-anchored/2/`.
- [ ] Edit each recursive block's `entry.json` under `qml/src/qml/blocks/stdlib/`, for its `settle_bars`.
- [ ] Delete `tools/qml/recheck_units.py` and `tools/tests/test_recheck_units.py`.
- [ ] Edit `qml/tests/test_lifecycle.py`, `qml/tests/test_entry.py`, `qml/tests/test_stdlib_blocks.py`, `qml/tests/test_loader.py`, `qml/tests/test_wave1_beyond_fx.py`, `qml/tests/test_wave1_exits.py`, `qml/tests/test_wave1_statistics.py`, `tools/tests/test_dictionary_port.py` and `qmx-agents/packages/qmx-control/tests/test_unit_rows.py`.
- [ ] Edit `qml/tests/test_nothing_silent.py`, so its sweep walks every version.
- [ ] Create `qml/tests/test_session_clock.py` and `qmx-agents/packages/qmx-host/tests/test_dictionary_full_size.py`.
- [ ] Edit `qmx-agents/apps/trading-node/app.toml`, by call 11, because `qml` is in its lock, and `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` for its version row.

**Build.**

- [ ] Subtract. Delete `p0a-22` (`test_loader.py:136`), `p0a-23` (`test_stdlib_blocks.py:359` and `:300`), `p0b-23` (`test_unit_rows.py:30`), `p1a-16` (`test_wave1_beyond_fx.py:227` and `test_wave1_exits.py:400`, and shrink `test_wave1_statistics.py:266` to its HMM and GARCH line), `p1a-17` (one corpus-wide link check replaces `test_wave1_beyond_fx.py:319` and `test_wave1_exits.py:446`), `p1b-19` (`test_lifecycle.py:140`) and `p1b-20` (`test_dictionary_port.py:89`).
- [ ] Subtract, `p1b-6` and `p1b-7`. Cut `tools/qml/recheck_units.py` and its three tests. Publish and compile re-check live, so no bad unit gets through, and the script reads a folder nothing writes. Keep `checker_version` and bump the format by hand. No other file names the script (`git grep`). If AD-119's card is ever wanted, this comes back.
- [ ] Subtract, `plan-check-5`, call 7. Delete `lifecycle.auto_paper`. Cut the row at `machine.py:111`, `needs_auto_paper` at `:101`, `AUTO_PAPER_OFF` at `:134`, the parameter and its reads at `:170`, `:177`, `:186-189`, `:202` and `:223`. The report's list misses these callers, so cut them too, `qmx_host/lifecycle.py:106,130,143`, `promote.py:312,340,415`, `host.py:863-869`, and `service.py:427,434,443,448`. Change `test_lifecycle.py:76,80,123-134,157-162`. Add one line to `S/BACKLOG.md` for the UI session, because the setting leaves `[units]`.
- [ ] Safety fact. Nothing writes `auto_paper` on, and judge moves are draft to tested or parked only (`record_judge_moves`, level 2). Across all 455 pages first start lands, `corpus_problems` finds 0 clashes, so the save check cannot refuse the landing (`S/proofs/ground-unit/p6.py`, level 4). `entry.json` words and settle rows sit outside the block fingerprint, so no pin moves. These must hold from `ground-unit.md` section 2, the Library's every-kind save, first-start landing keyed by fingerprint, and the dummy. E7 and E8 are not in reach, because no template or format row changes.
- [ ] `p1a-4` and `p1b-12`. QML-03 lives only in `test_stdlib_blocks.py:130`, and only 2 of 112 entries record a length, `ema` and `rsi-cross-back`, and a length holds for one parameter set. Extend `Settle` (`blocks/api.py:266`) and `settle_bars` with bars per period and the parameter it scales by. Record that for each recursive block, measured with `_settle` and `S/proofs/p1a/proof_settle.py`. Make `_warm_up` (`compiler.py:454`) scale it from the binding's parameters. Warm-ups grow for new units.
- [ ] `p1a-4`, unproven. The dummy's warm-up should not grow, since its slow blocks are recorded and its derived window is longer, but nobody has run it. `test_compile_dummy.py` will show it. If the dummy's warm-up moves, stop and report, because that is the safety fact failing.
- [ ] `p1b-12`. Add the settle check to `check_entry` in `catalogue/entry.py`, so a recursive block that has not settled by its declared length is an error, not a test that only stdlib gets.
- [ ] `p1b-11`. At `entry.py:815-818`, an entry of origin `agent` or `human` with no golden no longer earns `implemented`, and its missing list names the cut-against-full run. Limit this to those origins, because QML's own are covered by tests and 17 stdlib entries would otherwise drop status.
- [ ] `p1b-13`. In `match` (`catalogue/index.py:196`), a one-word name stops matching alone. 229 names are one word, and a false "known" loses an idea silently, while a false "new" only makes an append request someone reviews. `test_entry.py:151-154` tests at full size. `blocks_match` and `u3-dictionary-expansion` use this.
- [ ] `p1b-15`. Make `entry_check` (`host.py:830`) close over the store as `unit_problems(store)` does, and change `register_checkers` to match. It reuses `corpus_problems`. Look names up rather than scan, because the cost per save over 455 rows is unproven. A new version of one entry is not a clash with its old version, so `trend-floor-from-record@2` and the ten new versions must save.
- [ ] `p1b-14`. Call `write_entry_statuses` (`functions.py:845`) after landing, after publish, and per entry after a put, through the post-put hook `_landed` (`host.py:764-773`). A checker runs inside the put and cannot write, so it cannot go there. Rerunning writes the same values.
- [ ] `p1a-6` and `p1a-1`. Write the ten new versions. Add one parameter `clock`, measure `category`, range 0 to 2, where 0 is UTC, 1 is London and 2 is New York. `session_start` becomes a second of that clock's day. Use the civil-date functions from `lbma-gold-auction-clock@1` and `eia-petroleum-status-report-clock@1`. `zoneinfo` appears nowhere under `qml/src/qml`, so do not add it. Update each `boundaries` line, and take out "does not yet pass" where it is no longer true.
- [ ] Trap. A session day must be counted on the clock's local date. `_session` today counts `(closed - 1 - start_ns) // _DAY_NS` in UTC, so naive shifting breaks across the two clock-change weekends. Test both.
- [ ] Move the table in `compiler.py`. `BLOCKS_NOT_BUILT` keeps all ten `@1` pins, now saying "use version 2 and name its clock". It adds `vwap-session-anchored@2` as needing volume, by call 5. The other nine `@2` pins run. Bump `COMPILER_FORMAT_VERSION` to 4.
- [ ] Change the sweep in `test_nothing_silent.py` to walk every version, not only `*/1/`, because R04's and R05's walks skip version 2. Otherwise "every stdlib block acts or refuses" stops being true here, in the area R05 warns about. With `session_start` at its default, each `@2` acts or refuses. Add any `@2` the sweep reads and never fires to `READ_NEVER_FIRED`, on purpose, so it is no surprise red.
- [ ] `p1a-7` stays out. It goes to the risk session with the halts, and compile refuses all halts today, so it cannot bite.

**You see.**

- [ ] The dictionary now tells the truth by itself. Every page shows its real status, an agent cannot give a new entry a name another entry already holds, and an ordinary sentence such as "The trend is your friend" no longer gets filed as a known idea.
- [ ] A session rule now follows the market's own clock, so a New York open stays at 9:30 New York time all year. No setting can move a unit to paper without your click, because that setting is gone.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_dictionary_full_size.py::test_a_fresh_store_lands_and_publishes_with_no_status_none`. Foundation check 7. A fresh store goes through first start's landings and one `publish_collection`. Every entry head has a status. The expected count is the literal 455 of today's 112, 104 and 239, plus what R05 and R06 add. State that sum and its reason in `owner-how.md`, and write the literal into the test.
- [ ] `test_dictionary_full_size.py::test_a_clashing_save_is_refused_and_a_new_version_is_not`. A `component` draft taking `ema`'s name is refused with the name in the message. `trend-floor-from-record@2` saves.
- [ ] `test_dictionary_full_size.py::test_an_ordinary_sentence_stays_unmatched`. `blocks_match("The trend is your friend")` returns the sentence with `pin` None over the full store. At the parent it returns a pin.
- [ ] `test_session_clock.py::test_a_new_york_open_follows_daylight_saving`. `session-running-high@2` with `session_start` 34200 and `clock` 2 starts a new session at 14:30 UTC on 2026-03-06 and at 13:30 UTC on 2026-03-13, the dates in `S/proofs/p1a/proof_edges.py`. `@1` at a fixed 14:30 is an hour wrong on the second date. Also, with `clock` 0 each of the nine runnable `@2` blocks gives `@1`'s exact values over the golden bars, and one test crosses each clock-change weekend.
- [ ] `test_nothing_silent.py::test_every_stdlib_block_acts_or_refuses`. Foundation check 3 over every version. Each of the nine runnable `@2` blocks is driven through `check`, `compile_unit` and `on_instant`, and `vwap-session-anchored@2` refuses as `block_not_built`.
- [ ] `test_entry.py` gains `test_an_agent_block_with_no_golden_is_not_implemented` and `test_an_unsettled_block_fails_check_entry`, the second with a recursive fake and a declared length too short.
- [ ] Tests that change on purpose are `test_lifecycle.py`, because the setting goes, and `test_entry.py:151-154` if its sentence relied on a one-word match. `test_compile_dummy.py` must not change. Run `uv run --no-sync python -m pytest qml/tests -q -n 2`, and in `qmx-agents/packages/qmx-host` run `test_lifecycle.py`, `test_promote.py`, `test_publish_collection.py` and `test_dictionary_full_size.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qml/tests`, `tools/tests`, `qmx-agents/packages/qmx-tools/tests/test_block_tools.py`, and in the host `test_lifecycle.py`, `test_promote.py`, `test_publish_collection.py` and `test_unit_library.py`, with `qmx-control`'s suite, at the parent and the head. No model. Save `r06-regression.log`. Pass when the head fails nothing the parent passes, apart from tests named on purpose.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/p1a/proof_edges.py` and `S/proofs/p1a/proof_settle.py` at the parent and the head with `proof_at.sh root`. No model. Save `r06-proofs.log`. Pass when the parent shows the fixed 14:30 and the two-of-112 settle list, and the head shows 13:30 on 2026-03-13 and every recursive block recorded.
- [ ] Lane 3. A fresh host on a throwaway folder, one publish through `POST /api/library/collections/<id>/publish` with the operator's token. Then `blocks_find`. No model. Save `r06-pages.log`. Pass when no page reads status None.
- [ ] Lane 4. Whole-repo run at this phase end, with `S/tools/run_tests.sh`. No model. Save `r06-whole.log`. Pass when it fails nothing R05's tip passed.
- [ ] Lane 5. With a model, ask a copilot chat on `haiku` "does the dictionary know the idea that the trend is your friend?" Save `r06-copilot.log`. Pass when `blocks_match` answers unmatched and the chat offers an append request.
- [ ] Lane 6. Grep `qmx-agents/apps`, `qmx-agents/packages` and `qml/src` for `auto_paper` and `recheck_units`. No model. Save `r06-gone.log`. Pass when neither appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r06-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r06-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r06-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r06-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds per `component` save over the full store, and seconds for the first landing.
- [ ] Probe. A timed loop of 20 saves on the store lane 3 made, and the landing's own log.
- [ ] Baseline. Record the parent's value first. The parent has no store-wide check.
- [ ] Rule. Fails above 1 s per save, which is where an agent's write loop would feel it.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r06-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Make backtests read his facts (R07)

Phase C, a backtest on his facts and data. Source is `A/reports/ground-qmb.md`, "A run on his facts" and the first line of "Study rules". A backtest checks a unit against his Library's instrument record, then copies a QML test fixture into the run folder, so money and R are computed on the wrong contract, and a market with no fixture cannot run at all. Done when foundation check 11 and the study half of check 12 pass.

Rows carried. `seams-2` `p0b-1` `p0b-2` `p5d-5` `p0b-10` `p2-10` `qmb-n2` `qmb-n5` `p0b-25` `p1b-22`

Rows in part. `p6-2` by its run half, where the real record reaches the run. R13 carries its template half, the words in `check.py` and `ready.py`.

Proves. A record on main reaches the run folder and the fills, and moving it shows in the next run with no host restart.

**Depends on.** R06.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/gather.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/host.py`, `qmx-agents/packages/qmx-host/src/qmx_host/venue_records.py` and `qmx-agents/packages/qmx-host/src/qmx_host/connect_node.py`.
- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/service.py`, for the `[node]` section.
- [ ] Edit `qmx-agents/apps/qmb/jobs/backtest.py`, `qmx-agents/apps/qmb/tests/test_qmb_app.py` and `qmx-agents/apps/qmb/app.toml`, then `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` for the version row.
- [ ] Edit `qmx-agents/packages/qmx-host/tests/test_unit_library.py` and `qmx-agents/packages/qmx-library/tests/test_market_kinds.py`.

**Build.**

- [ ] Subtract. Delete `p0b-25` (`test_qmb_app.py:204`), which repeats a full backtest for what the runner test already checks, and `p1b-22` (`test_market_kinds.py:202`), which reads back fields it just put. Delete `_record_file` (`host.py:1829-1838`) and its imports, because only `_lay_out` calls it.
- [ ] Safety fact. The compiled fingerprint holds no records, so swapping the record file keeps the pin and the G report valid. Level 4, where the repaired folder printed "same compiled fp as host True" (`S/proofs/ground-qmb/records.py`). With no item on main the fallback path stays the fixture, so the shipped suite is unaffected, level 3 by `gather.py:161-164`. From `ground-qmb.md` section 2 these must hold, the tester reads only its run folder, a refused run lands no try, and `[qmb] bars` keeps working. M7 and M8 must hold.
- [ ] `seams-2`, `p0b-1` and `p0b-2`. Do this in one place, `gather`. `Gathered` also hands over each market's raw record document, the item's fields with `record_version`, or the fixture's. `RunUnit` keeps it. `_lay_out` writes it to `in/records/<market>.json`, in place of the copy at `host.py:1949-1952`. `load_unit_folder` already reads each record file's raw JSON for carry terms (`unit_runner.py:340-346`), so the raw Library item is the shape it wants. Gold's and GBPUSD's keys all parsed (run, level 4).
- [ ] Trap, `qmb-n2`. `LanderLibrary.unit` caches per pin "because an object never changes" (`host.py:1774-1780`), but the records it gathered do change. With the record moved on main to min lot 0.05, the same host still answered 0.01 version 1, and a new host answered 0.05 version 2 (level 4). Gather on each open, and key the compile cache on the pin plus the record versions.
- [ ] `qmb-n5`, call 8. `LanderLibrary._compiled` throws `gather`'s warnings away, so a run on a fixture says nothing. Keep them on `RunUnit`, write them into `in/request.json` as `fixture_records`, and have `backtest.py` add `fixture_records` to its labels (`backtest.py:214`). Gather's fixture fallback stays, and the warning now reaches the result.
- [ ] Trap. `FIXTURE_WARNING`'s words say "until the instrument kind lands (C-02)", and C-02 kept them only because a test outside its files pinned them. That line told readers C-02 had not landed. Change the words to say the market has no Library record, and change the two pins on purpose, `test_unit_library.py:195` and `test_market_kinds.py:280,313`.
- [ ] `p5d-5`. Add the settings section `"node"` to `SettingsSection` in `service.py` with `NODE_DEFAULTS`, holding `record_markets` (today's two rows of `MARKETS`) and `records_refresh_s` (86400). Read both at the two build sites, `host.py:1129` and `connect_node.py:725`. `Market` already holds what a setting row needs. Without this a real GBPUSD record never exists, so the first fix helps only markets C-34 lands.
- [ ] `p0b-10` and `p2-10`. In `_lay_out` (`host.py:1934-1935`), when a named study states `allow_gaps`, it goes after `**ticket.request`, so the study wins. With no study, or a study that does not state it, the chat still decides, because `test_qmb_run_kinds.py:56` and `test_qmb_app.py:57` send the chat's value. His decided ruling is TR:57. Today it runs "study False, chat True, run reads True" (`records.py`).
- [ ] `p6-2`, the run half. Leave `check.py`, `ready.py` and `test_templates.py:1064` to R13, so one PR owns those lines. The lander compiles the pin with the Library before any try lands, so a GBPUSD unit reaches a run through `backtest_run` after this PR, and through the `b` template after R13.

**You see.**

- [ ] A backtest now trades on the contract facts in your own Library, such as gold's lot step, instead of on a test file. If you change a record, the next run uses it with no restart. A result on a market with no record of its own says so.
- [ ] If a study forbids gaps in the data, a chat can no longer talk its way past that.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_qmb_app.py::test_a_record_on_main_reaches_the_run_and_its_fills`. Put an `instrument` item for gold with lot step 0.10 on the real store, which holds none today, which is why this stayed green. Assert `in/records/metal.xauusd.json` equals the item's fields with `record_version`, and every gold fill's quantity is a whole multiple of 0.10. Fails today.
- [ ] `test_qmb_app.py::test_a_market_with_only_a_library_record_runs`. A GBPUSD unit with a GBPUSD record and its own CSV pair under `[qmb] bars` lands `finished`. Today the tester refuses `no instrument record was given for fx.gbpusd`.
- [ ] `test_qmb_app.py::test_a_record_moved_on_main_shows_in_the_next_run`. Foundation check 11. Two runs on one host, with the record moved between them from min lot 0.01 to 0.05. The second `in/records` reads 0.05 version 2.
- [ ] `test_qmb_app.py::test_a_study_forbidding_gaps_beats_a_chat_allowing_them`. Foundation check 12, study half. On the month in `test_a_study_that_allows_gaps_runs_the_month_the_hole_rule_fails`, a study with `allow_gaps` false plus a chat with `allow_gaps` true lands `failed` with the literal `SUNDAY_HOLE` reason.
- [ ] Tests that change on purpose are `test_unit_library.py:195`, `test_market_kinds.py:280,313`, and `test_qmb_app.py:191` for the version. Run `uv run --no-sync python -m pytest tests/test_unit_library.py -q` in `qmx-host`. The coordinator runs the QMB app test.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qmx-agents/apps/qmb/tests/test_qmb_app.py` and `test_qmb_run_kinds.py`, `qmx-agents/packages/qmx-host/tests/test_unit_library.py` and `test_landers` in `qmx-apps`, `qmx-agents/packages/qmx-judge/tests`, and `qmx-agents/packages/qmx-library/tests/test_market_kinds.py`, at the parent and the head. No model. Save `r07-regression.log`. Pass when the head fails nothing the parent passes, apart from tests named on purpose.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/ground-qmb/records.py <folder>` with `proof_at.sh agents`, at the parent and the head, and read its first sections. No model. Save `r07-records.log`. Pass when the parent prints "records laid []" for GBPUSD and "run reads True", and the head lays the GBPUSD record and reads False. The script's in-memory repair section no longer applies at the head, so an error there is expected and is not a fail.
- [ ] Lane 3. A real-month run. Plant gold lot step 0.10 on a throwaway store and run March 2025 from `D:/QMX-worktrees/unit-ship/data/dukascopy-node/`. No model. Save `r07-gold.log`. Pass when it gives 21 trades and net -169.04, against 29 trades and +22.84 with the fixture. The numbers rest on a planted record, not on his broker.
- [ ] Lane 4. A record moved under a running host, through a real supervisor and two real runs. No model. Save `r07-moved.log`. Pass when the second run's folder holds version 2 with no restart.
- [ ] Lane 5. `[node] record_markets` with GBPUSD added, on the fake cTrader from `test_app_binding.py`. No model. Save `r07-markets.log`. Pass when a GBPUSD record lands.
- [ ] Lane 6. Run `S/proofs/ground-qmb/records.py`'s swap and cost sections at the head, on a record with a swap term. No model. Save `r07-swap.log`. Pass when a swap on the Library item reaches the run with R unchanged at -4.3841.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r07-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r07-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r07-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r07-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from `QmbRun.open` to the job starting, for one market.
- [ ] Probe. Time `open` in lane 4 at the parent and the head, interleaved.
- [ ] Baseline. Record the parent's value first.
- [ ] Rule. No fail rule, recorded for the trail. A gather on each open reads the Library, so name the number if it passes 1 s.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r07-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Make backtests read his data (R08)

Phase C, a backtest on his facts and data. Source is `A/reports/ground-qmb.md`, "A run on his data" with its three-shapes table and its trap. Today the new run path never touches the market store. The data he downloads lands as monthly tick files, and a run reads only hand-saved CSV pairs named for one exact window, so the data he downloads can never be backtested. This is the bridge. Done when foundation checks 8, 9 and 10 and the sealed half of check 12 pass.

Rows carried. `p0b-3` `p0b-9` `p0b-17` `p5d-4` `p0b-8` `p0b-11` `triage-6` `qmb-n1` `qmb-n3` `qmb-n4` `p0b-19` `p0b-27`

Rows in part. `p2-4` by its backtest half, and its nightly replay goes with `seams-8` after G-DEMO. `p2-2` by its label now, and `Bar` rows wire when a one-sided source first needs a run.

Proves. A fresh home with only a Library record and ticks in the store lands a finished result, and a month missing or sealed is refused before any try.

**Depends on.** R07.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/host.py` and `qmx-agents/packages/qmx-host/src/qmx_host/market_data.py`.
- [ ] Edit `qmb/src/qmb/host/unit_runner.py` and `qmb/src/qmb/host/replay.py`.
- [ ] Edit `qmb/src/qmb/host/replay_request.py`, `qmb/src/qmb/host/replay_execution.py` and `qmb/src/qmb/execution/binder.py`, cutting B4's entry only.
- [ ] Delete `qmb/tests/test_typed_execution.py`.
- [ ] Edit `qmx-agents/apps/qmb/jobs/backtest.py`, `qmx-agents/apps/qmb/jobs/optimize.py`, `qmx-agents/apps/qmb/jobs/replay_check.py`, `qmx-agents/apps/qmb/jobs/robustness.py`, `qmx-agents/apps/qmb/jobs/sweep.py`, `qmx-agents/apps/qmb/jobs/walk_forward.py`, `qmx-agents/apps/qmb/jobs/whatif.py` and `qmx-agents/apps/qmb/server.py`, for the fidelity label.
- [ ] Edit `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/download-dukascopy/scripts/download.py`.
- [ ] Edit `qmx-agents/packages/qmx-library/src/qmx_library/kinds/study-spec.schema.json`.
- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/journals.py` and `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`.
- [ ] Edit `qmx-agents/apps/qmb/tests/test_qmb_app.py` and `qmx-agents/apps/qmb/app.toml`, then `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` for the version row.
- [ ] Edit `qmx-agents/apps/trading-node/app.toml`, by call 11, because `qmb` is in its lock, with its row in `test_shipped_apps.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/tests/test_market_data.py`.
- [ ] Create `qmb/tests/test_data_feed.py` and `qmx-agents/packages/qmx-tools/tests/test_journal_seal.py`.

**Build.**

- [ ] Subtract, `p0b-17` and `p0b-27`. Cut B4's typed-partition entry, about 650 product lines and about 547 test lines, none of which the bridge uses, because it reads one partition at a time and builds whole-history frames. `execute_typed_replay_request`, `load_typed_replay_request` and `bind_requested_execution` appear only in `qmb/src` and `test_typed_execution.py`. Cut those, `read_typed_replay_source`, `TypedPartitionRef` and their helpers, using `git log` on those names to find B4's lines. The Book path stays, by `ground-qmb.md`, so keep the rest of `replay_execution.py`, `replay_request.py` and `binder.py`, and keep `test_replay_execution.py` green.
- [ ] Subtract, `p5d-4` read half. The cut also ends the hard-coded scale 5 at `replay.py:105,908`, which only that entry reaches.
- [ ] Safety fact. A tick feed gives the same bars and the same trades as the CSV pair. Level 4 on the real March 2025 EURUSD and XAUUSD files through the real door, commit, `materialise`, feed, with "csv bars 2028, tick-built bars 2028, identical True", 1940 for gold, and "29 trades, net 22.84, R 0.9847" on both paths with "same trades True" (`S/proofs/ground-qmb/bridge.py`). The limit is that those ticks were cut from those bars, four per bar, so it proves the path, not that Dukascopy's real ticks agree with dukascopy-node's bars. From `ground-qmb.md` section 2 these must hold, a full read refuses a sealed month, a commit is the only write, fingerprints verify, `materialise` keeps its meaning for the Lab, `d6-ml-training-run` and `data-quality`, and `[qmb] bars` keeps working. M8 must hold, because refusals come before any try opens.
- [ ] `p0b-3` and `p2-4`, the door. Give `QmbRun` the door. The host already builds it (`market_door`, `host.py:1618-1627`), so pass it through `landers` (`host.py:1976`).
- [ ] `p0b-3`, the read, call 8. `_bars` (`host.py:1884`) looks first at a named `[qmb] bars` folder, which stays as the test and hand-saved route. Otherwise it asks the door for the source's series and months for the market, and prefers `bar-m1` bid and ask pairs over ticks. It refuses before any try, naming each missing month and `download-dukascopy`, and the CSV path too when a `[qmb] bars` folder is named. Drop the stale dukascopy-node wording.
- [ ] `p0b-3`, which source. The door lists series by `<source>/<SYMBOL>/...`, and nothing maps a market to a source. The source for a market is `dukascopy` unless the request or the study names another. `backtest_run` (`functions.py:188`) gains an optional `source`, and `study-spec.schema.json` gains the same field. A usable source is one of those, holding the month with a stated scale. Two usable sources for one month is a refusal before any try, naming both, which happens when the request and the study name different sources. No other source in the store is read, so an old `risk-lab/<symbol>/bar-m1` import with no stated scale cannot block good Dukascopy ticks or change a result. Level 2.
- [ ] `p0b-3`, the copy. `_lay_out` (`host.py:1920`) copies the partitions to `in/data/<market>/` through `door.materialise`, with `into` the run folder and a small `card.json` holding series, scale, fidelity and window.
- [ ] `p0b-3`, the feed. `load_unit_folder` (`unit_runner.py:324`) picks `_BarFiles` when `in/bars/<market>/` exists, or a new feed of about 25 lines when `in/data/<market>/` exists. The feed's shape is `TickFiles` in `bridge.py`, feeding `Tick` or `BarPair` rows to `replay_feed(_QUOTES, rows, BarBuilder(day.span, seconds), until_ns=...)`. It clips to the window, and `until_ns` comes from the window so the last bar closes. Nothing past the feed changes.
- [ ] Trap. Do not tie the bridge to ticks alone. R09 adds derived `bar-m1`, and the reader must not change then. A real month is about 3.5M ticks (a guess), so about a minute to copy and about 45 s per read per market, and a first run reads three times.
- [ ] `p5d-4`, the scale. The door's `card()` holds no price scale, and the scale is written only to a run artifact that never becomes an item. Add one line in `download.py` beside its `ClockLedger` write (`download.py:385,414`) that keeps the scale in a per-series file under the store's `.clocks` folder, and add a door method that reads it. A series with no stated scale is refused by name, which makes C-31's plan line true. His old imported months need one `check` or re-download, so the refusal says that.
- [ ] `p0b-8`. `_lay_out` also lands the `dataset` card with `write_card` (`qmx_library/cards.py:190`), which is idempotent, and records its object id. In `QmbRun.close`, set the bundle's `consumed` to it, and hash `request.json` for `request_fp`. `landing.py:520-527` already links both. No template or engine change is needed. A hand-saved CSV run names no dataset and stays as it is.
- [ ] `p0b-9`. `_bars` stops refusing a subset of the unit's markets, and refuses only a market the unit does not trade. `_lay_out` writes the asked list in `markets`. `load_unit_folder` skips feeds the request does not name, and `run_loaded` then gives "14 trades, ['fx.eurusd']" (`bridge.py`, level 4). The compiled fingerprint does not change. The result must name its markets, because the judge reads `r.markets`.
- [ ] Trap, `qmb-n1`. The door's `read` refuses a sealed month, but `materialise(into=...)` with the same holdout "COPIED 1 file(s)" by its docstring, for a final look's attempt folder (`bridge.py`, level 4). Laying a run out through `materialise` alone opens the leak `p0b-11` is about. Add a small door method that answers which months are sealed for a holdout and a run, and call it in `_bars` before anything is copied. Do not change `materialise` itself, because the Lab (`qmx_control/lab.py:451`), `d6` and `data-quality` use it. Write `d6-ml-training-run/scripts/dataset.py:85` into `S/BACKLOG.md`, since it reaches sealed months once a holdout is on.
- [ ] `p0b-11` and `qmb-n3`. Make the study's `holdout` able to name a real holdout. Change `study-spec.schema.json:99` from a plain string to `"off"` or `{boundary, months}`, the door's own shape. Pass it to the door with `run=`, using the study pin and the window as the name before a run id exists, so one run stays one seal (`_holdout_for`, `market_data.py:744`). A sealed month is refused with the door's reason before any try. Harmless while holdouts stay off, the default.
- [ ] `triage-6`. `journal_query` reads the store directly (`journals.py:321`). Apply the door's Settings default holdout to the rows it serves, or refuse with its reason. An agent read has no study, so a per-study seal cannot apply there, as LD-08's "optional study" says.
- [ ] `p2-2`, `qmb-n4` and `p0b-19`. Change the label now, from `fidelity: bars` to `quotes`, at `backtest.py:218` and the sibling jobs, and in `FIDELITIES` at `server.py:68`, because every run replays both price sides. Wire `Bar` rows later, when a one-sided source first needs a run.

**You see.**

- [ ] Download a month with the download template, then ask the copilot to backtest a unit on it. It runs and the result says which data it read. If the month is missing, it tells you which month and which template to run, before anything starts. You can also backtest one market of a unit that trades two.
- [ ] A study that seals its last months really keeps them out of every run and every agent's reading.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_qmb_app.py::test_a_fresh_home_with_ticks_in_the_store_lands_a_result`. Foundation check 8. A GBPUSD record on main and ticks committed through the real door, real app under a real supervisor. It lands `finished` with one `consumed` edge to a `dataset` item, `request_fp` set, and fills on the record's lot step. Today it refuses at `_bars`.
- [ ] `test_qmb_app.py::test_no_month_is_refused_naming_the_month_and_the_template`. Foundation check 9. `ControlError` code `run_refused`, the message holds `2025-01` and `download-dukascopy`, and the try log gains no row. This replaces `test_a_month_with_no_bars_is_refused_by_name_before_any_try` when no `[qmb] bars` is set, and the CSV form keeps its old words.
- [ ] `test_qmb_app.py::test_a_month_through_a_csv_and_through_the_store_gives_the_same_trades`. Foundation check 10. Both land the same `trade_list_fp`. Use ticks cut from the CSV, as `bridge.py` does.
- [ ] `test_qmb_app.py::test_a_sealed_month_is_refused_and_no_sealed_file_sits_in_a_run_folder`. Foundation check 12, sealed half. A study with `holdout` `{"boundary": "2025-03", "months": 12}` lands no try, and a walk of the volume's `runs/` finds no file of that month.
- [ ] `test_data_feed.py::test_one_market_of_a_two_market_unit_runs`, `::test_a_series_with_no_stated_scale_is_refused_by_name`, and `::test_the_window_end_closes_the_last_bar`, each with literal bar counts.
- [ ] `test_journal_seal.py::test_journal_query_keeps_to_the_default_holdout`. With `[data]` sealing a month, `journal_query` over it answers the refusal or no sealed row. Today it serves them.
- [ ] Tests that change on purpose are `test_a_month_with_no_bars_is_refused_by_name_before_any_try`, any test pinning `fidelity: bars` (check `conformance_pack/golden.json`, and regenerate it if it holds the label), and `test_qmb_app.py:191`. Run `uv run --no-sync python -m pytest qmb/tests/test_data_feed.py qmb/tests/test_unit_runner.py -q`. The coordinator runs the app test.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qmx-agents/apps/qmb/tests/`, `qmb/tests`, `qmx-agents/packages/qmx-host/tests/test_market_data*.py`, `qmx-agents/packages/qmx-judge/tests` and `qmx-agents/packages/qmx-engine/tests/test_templates.py`, at the parent and the head. No model. Save `r08-regression.log`. Pass when the head fails nothing the parent passes, apart from tests named on purpose.
- [ ] Lane 2. Fail-today proof. Copy the four new tests into the parent's check worktree and run them there, then at the head. No model. Save `r08-red-green.log`. Pass when all four fail at the parent and pass at the head.
- [ ] Lane 3. Run `S/proofs/ground-qmb/bridge.py <folder>` at the head with `proof_at.sh agents`. No model. Save `r08-bridge.log`. Pass when it reads "identical True" for both markets, "same trades True", and the sealed `materialise` line reads as it did, because the door did not change.
- [ ] Lane 4. A real download on a scratch home. Run `download-dukascopy` for one real EURUSD month, then a real job on it. No model. Save `r08-real.log`. Pass when a result lands with its `consumed` edge. Record ticks per month and seconds per read, because the 3.5M is a guess. Compare its trades with the dukascopy-node CSV of that month, and write any gap into `S/BACKLOG.md`. If the network is down, log it and rerun later.
- [ ] Lane 5. The Lab and `data-quality` on a sealed month, which still behave as they did. No model. Save `r08-door.log`. Pass when `qmx-agents/packages/qmx-control` Lab tests and `data-quality`'s template test are green.
- [ ] Lane 6. With a model, a copilot chat on `haiku` on a scratch home with a landed month, asked "backtest the dummy on EURUSD for March 2025". Save `r08-copilot.log`. Pass when the result's fields name the dataset.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r08-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r08-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r08-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r08-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds to copy and verify, ticks to bars per second, and the whole first run for one market-month.
- [ ] Probe. `bridge.py`'s speed section at the head, and lane 4's real month.
- [ ] Baseline. 800,000 synthetic ticks copied in 13.1 s, at 80,581 ticks a second, and `BarPair` rows at 156,012 a second.
- [ ] Rule. Fails below 60,000 ticks a second on the same synthetic month. The whole-run number is recorded for R09, which is what brings it down.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r08-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Make long history hold up (R09)

Phase C, a backtest on his facts and data. Source is `A/reports/ground-qmb.md`, "The rest of this group" and "How long it takes" in "A run on his data". Reading raw ticks makes a year of two markets take over an hour, on a guess of 3.5M ticks a month. A data file that stops early passes the hole check. A past holiday can read as a hole, because the calendars list closures for 2026 and 2027 only. Done when a real December and a real January run give honest answers, and a market-month through derived bars is at least five times faster than through ticks.

Rows carried. `p2-9` `triage-2` `p2-13` `p34-11` `p34-12` `p34-13`

Proves. A file cut short lands `data_short` or refuses, and a real December gives no false holes.

**Depends on.** R08.

**Files.**

- [ ] Edit `qmb/src/qmb/host/unit_runner.py` and `qmb/src/qmb/data/gap_check.py`.
- [ ] Create `qmx-agents/packages/qmx-tools/src/qmx_tools/derive_bars.py`.
- [ ] Edit `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/download-dukascopy/scripts/download.py`, `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/download-binance/scripts/download.py` and `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/download-ccxt/scripts/download.py`.
- [ ] Edit `extensions/qmf-calendar-forex/src/qmf/calendar_forex/calendars/fx-24x5@1.json` and `extensions/qmf-calendar-cme/src/qmf/calendar_cme/calendars/metals-24x5@1.json`.
- [ ] Edit `qmx-agents/apps/qmb/jobs/backtest.py`, `qmx-agents/apps/qmb/tests/test_qmb_app.py` and `qmx-agents/apps/qmb/app.toml`, then `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` for the version row.
- [ ] Edit `qmx-agents/apps/trading-node/app.toml`, by call 11, because `qmb` and the calendars are in its lock, with its row in `test_shipped_apps.py`.
- [ ] Delete `extensions/qmf-calendar-cme/tests/test_calendar_cme.py`, `extensions/qmf-calendar-crypto247/tests/test_calendar_crypto247.py` and `extensions/qmf-calendar-indices/tests/test_calendar_indices.py`.
- [ ] Create `qmb/tests/test_data_ends.py` and `qmx-agents/packages/qmx-tools/tests/test_derive_bars.py`.

**Build.**

- [ ] Subtract. Delete `p34-11`, `p34-12` and `p34-13`, the three calendar test files, whose tests retype the data files' own values. They fail only when someone edits a calendar, and this PR edits calendars. `test_preflight_calendar.py`'s sweep proves the behaviour.
- [ ] Step one, before any code, probe a real December. Fetch EURUSD for December 2024 at m15 with the tool that made `D:/QMX-worktrees/unit-ship/data/dukascopy-node`, into `S/data/`, both sides. Point `S/proofs/ground-qmb/holes.py` at the file. Save `owner-december.log` with the holes and their dates. The audit could not run this, because it needs a download. Real EURUSD January to March 2025 has 0 holes past the limit, so `triage-2`'s "stops most long runs" is not shown, and mid-window Christmas is still untested.
- [ ] Safety fact. Past dates in a calendar file cannot change a live decision, because the node asks only about now, level 3. The reader does not change, because R08's feed already takes `BarPair` rows. `BarPair` rows fold at 156,012 a second with the same bar count, level 4 on synthetic prices. From `ground-qmb.md` section 2, `bar-m1` readers must not break, which are the MIS (`apps/mis/mis_core.py:475`) and `download-ccxt`, and neither must the door's write rule. E2 means a changed template is a new version, as it should be.
- [ ] Trap. `p2-9` and `triage-2` must land together. A check at the window's ends looks one line long, but on real January data it fails. Real EURUSD January to March has 88 "missing" open bars before its first bar, because the calendar reads 1 Jan 2025 and 25 Dec 2024 as open and reads 25 Dec 2026 as shut (run, level 4).
- [ ] `triage-2`. Add past closures as data to `fx-24x5@1` and `metals-24x5@1`, Christmas Day and New Year's Day for 2020 to 2025, with the same rule as their 2026 rows, and bump each `issued`. Check December 2024 against step one's file. Other calendars keep their lists until a market on them needs a run.
- [ ] `p2-9`. In `_preflight` (`unit_runner.py:497`), count the open-time bars missing between the window's start and the first bar, and between the last bar and the window's end, with `hours.open_at`, as the last section of `bridge.py` does. Add the label `data_short`, naming each market and both counts. Refuse only where the calendar's earliest closure comes before the window's start, because only then do past closures exist as data, and only past `gap_bars_refuse`, and never when the run allows gaps. Elsewhere it stays a label. `backtest.py` carries `data_short` into the result's labels.
- [ ] Derived bars. Add `derive_month(door, series, year, month)` in `qmx_tools/derive_bars.py`. It reads a landed tick month through the door, folds it into `bar-m1` bid and ask rows at the same integer scale, and commits them as `<source>/<SYMBOL>/bar-m1/bid` and `/ask` with `TypedWriter(..., BAR_COLUMNS)` and `door.commit`, as the door's docstring names a derived-data step. A rerun lands the same rows. The scale file R08 added is written for these series too.
- [ ] Have `download.py` in `download-dukascopy` call `derive_month` right after the tick commit (`download.py:414`), with the same `hold`. R08's `_bars` already prefers pairs and falls back on ticks, so a month landed before this PR still runs.
- [ ] `p2-13`. At `download.py:312` and the same line in `download-binance` and `download-ccxt` (`:160`), default `calendar` from the source when it names none, `fx-24x5@1` for a six-letter currency pair, `metals-24x5@1` for XAU and XAG, `crypto-24x7@1` for both crypto templates. Any other symbol keeps none and prints that. A month with one empty open hour then waits for a correction instead of freezing silently.

**You see.**

- [ ] Backtests over long history run several times faster, because each download also stores ready-made one-minute bars. If a data file stops early, the result says the data is short and by how much. Christmas and New Year no longer read as missing data in the markets that have them on file.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_data_ends.py::test_a_file_cut_two_weeks_short_says_so`. The committed synthetic March slice (`qml/tests/fixtures/slices/`) cut at 17 March, with a window to 1 April and `gap_bars_refuse` 4, so its 4-bar Sunday holes pass. On `fx-24x5@1`, whose past closures now exist, the run refuses naming the market and the bar count. With `allow_gaps` it finishes, carrying `data_short`. Today it finishes clean.
- [ ] `test_data_ends.py::test_real_january_to_march_has_no_short_head`. The real January to March 2025 EURUSD pair gives 0 and 0, where the same check today gives 88 at the head. It reads `QML_REAL_SLICE_DIR` and skips when the months are not on the machine, as `test_two_drives_over_the_real_month_give_the_same_steps` does.
- [ ] `test_data_ends.py::test_a_calendar_with_no_past_closures_only_labels`. On a calendar with none before the window, the same cut file lands `finished` with `data_short`.
- [ ] `test_derive_bars.py::test_derived_pairs_give_the_same_bars_and_trades_as_the_ticks`. Ticks cut from the synthetic slice as `bridge.py` cuts them, derived, run through both feeds. Both give the CSV's own bars and the same trade list.
- [ ] `test_derive_bars.py::test_deriving_twice_lands_the_same_fingerprints`. Tests that change on purpose are any template test whose sample month now has a calendar, and `test_qmb_app.py:191`. Run `uv run --no-sync python -m pytest qmb/tests/test_data_ends.py -q`, and in `qmx-agents` `packages/qmx-tools/tests/test_derive_bars.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qmb/tests`, `qmx-agents/apps/qmb/tests/`, `qmx-agents/apps/mis/tests/`, `qmx-agents/packages/qmx-engine/tests/test_preflight_calendar.py`, `qmx-agents/packages/qmx-engine/tests/test_templates.py` and `qmx-agents/packages/qmx-host/tests/test_market_data*.py`, at the parent and the head. No model. Save `r09-regression.log`. Pass when the head fails nothing the parent passes, apart from tests named on purpose.
- [ ] Lane 2. Fail-today proof. Copy `test_data_ends.py` to the parent's check worktree and run it there, then at the head. No model. Save `r09-ends.log`. Pass when it fails at the parent and passes at the head.
- [ ] Lane 3. Real December. Run `S/proofs/ground-qmb/holes.py` on step one's file at the parent and the head, then a real job over December 2024. No model. Save `r09-december.log`. Pass when the head lists no hole inside a closure, and any hole left has its date named in the PR body.
- [ ] Lane 4. Speed. On a scratch home, land one real month through `download-dukascopy`, then time one market-month through ticks and through pairs. No model. Save `r09-speed.log`. Pass when pairs are at least five times faster.
- [ ] Lane 5. The MIS reads the derived bars. On the scratch home, point `S/proofs/ground-start/mis_real.py`'s `source` at `dukascopy`. No model. Save `r09-mis.log`. Pass when a round publishes readings for it.
- [ ] Lane 6. Whole-window run over January to March 2025 for both markets through the store, against the CSV result. No model. Save `r09-compare.log`. Pass when the trade lists match.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r09-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r09-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r09-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r09-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for one market-month through ticks against through pairs, and memory at the end of each.
- [ ] Probe. Lane 4.
- [ ] Baseline. R08's lane 4 value, about 3 minutes a market-month, resting on a guess at the tick rate.
- [ ] Rule. Fails if pairs are less than five times faster than ticks. A month is about 30,000 pairs, at 156,012 a second.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r09-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Make runs report honestly (R10)

Phase C, a backtest on his facts and data. Source is `A/reports/ground-qmb.md`, "Running well" and "Costs". Long runs grow in memory, a first run can answer nothing to poll, a host restart leaves a run open for ever, a raising block loses its reason, run folders fill his disk, and every real backtest pays the spread and nothing else. R stays as it is, by call 9, and a cash number sits beside it. Done when foundation checks 13 and 14 pass.

Rows carried. `p2-1` `p2-16` `p0b-5` `p0b-6` `p0b-7` `p2-14` `p0b-12` `p2-12` `p0b-14` `p0b-15` `p0b-16` `p2-15` `seams-9` `p2-8` `p0b-18` `p0b-22` `p0b-26` `p2-17`

Proves. A stated cost profile changes net money with raw R the same, and 200,000 real steps stay flat in memory.

**Depends on.** R09.

**Files.**

- [ ] Edit `qmb/src/qmb/host/unit_runner.py`, `qmb/src/qmb/host/behaviour.py`, `qmb/src/qmb/host/unit_handler.py` and `qmb/src/qmb/robustness/unit_battery.py`.
- [ ] Edit `qmx-agents/apps/qmb/jobs/backtest.py`, `qmx-agents/apps/qmb/jobs/robustness.py` and `qmx-agents/apps/qmb/qmb_tester.py`, then `qmx-agents/apps/qmb/app.toml` and `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py`.
- [ ] Edit `qmx-agents/apps/trading-node/app.toml`, by call 11, because `qmb` is in its lock, with its row in `test_shipped_apps.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/host.py`.
- [ ] Edit `qmx-agents/packages/qmx-judge/src/qmx_judge/landing.py` and `qmx-agents/packages/qmx-judge/src/qmx_judge/judge.py`.
- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/service.py` and `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`.
- [ ] Delete `qmx-agents/packages/qmx-judge/tests/test_library_landing.py`.
- [ ] Edit `qmb/tests/test_windowed_reader.py`, `qmx-agents/apps/qmb/tests/test_qmb_app.py` and `qmx-agents/packages/qmx-host/tests/test_promote.py`.
- [ ] Create `qmx-agents/apps/qmb/tests/test_run_honesty.py` and `qmx-agents/packages/qmx-host/tests/test_restart_closes_runs.py`.

**Build.**

- [ ] Subtract. Delete `p0b-18`, the dead `land`, `BacktestResult`, `BacktestLanding` and `BASE_PRINCIPAL` at `landing.py:128`, with `p0b-26`, the two tests in `test_library_landing.py` that pin them. Delete `p2-17` (`test_windowed_reader.py:88`), which proves the memory probe works, not that QMX does.
- [ ] Safety fact. The feed is opened fresh on each read (the `LoadedUnit` docstring, level 2), and `motion = both` already relies on that, so none of these changes what the unit sees. The runner already books costs given files, with no code change. Commission of 3.50 a lot moved net from -169.04 to -249.91 with R unchanged at -4.3841, 42 cash rows, and the label stayed `costs_uncalibrated` (`S/proofs/ground-qmb/records.py`, level 4, on a planted record). `unit_handler.py` is shared with the node, so a change to how `r` is computed would change the node's calibration too, and this PR only adds to it. M6, M7 and M8 must hold, and `parity.py` must still read 63 of 63.
- [ ] `p2-1`. `_preflight` (`unit_runner.py:508-513`) builds a list of bar times, and `find_holes` takes any iterable. Make it a generator that stops on a refusal and still gives R09's first and last bar for `data_short`. Today memory grows eleven times from 10,000 to 200,000 steps (`S/proofs/p2/p1/mem.py`).
- [ ] `p2-16`. Point the memory test at `run_loaded`, the real run (`test_windowed_reader.py:76`). It stayed green while `p2-1` grew, because it drives only the row reader and the window.
- [ ] `p0b-7`. `check_behaviour` (`behaviour.py:70`) holds all bars, and it needs only `needed` bars. Make it take the first `needed` bars. The behaviour half never gates a run, only safety does.
- [ ] `p2-14`. `robustness.py:58` truly reads random spans (`unit_battery.py:107`), so a slice is wrong. Give `unit_battery` compact arrays of the bars, so memory stays bounded on long history.
- [ ] `p0b-5`. `landing.py:480` passes `motion: both` into the behaviour check, which cannot parse it. Force `on` for the check, and add `both` to the row at `functions.py:195`.
- [ ] `p0b-6`. `service.py:307-317` catches only `ControlError`, and the run id exists only after the check. Catch everything in the worker. A slow first run answers `checking` with the check's run id, and a poll on it names the run once opened. Change only the service.
- [ ] `p0b-12` and `p2-12`. `compiled.placeholders` is dropped at the job's labels, so add it to the labels in `backtest.py`. `functions.py:350` passes none to `land_judgement`, so pass them (`judge.py:927`). `JudgedResult.read` reads only `zero_trades` from labels, so have it read `costs_uncalibrated` as well, and put those words in the verdict, as judge.md section 3 says they are always shown.
- [ ] `p0b-14`. At host start, before apps start (`host.py:929`), each `opened` try on this machine with no close gets `fail("host restarted")`, and its request file is removed. The waiter thread dies with the host, and `bootstrap.py:226` would then run a leftover request with nobody to close it. Change only the host. The supervisor stays as it is. This rests on reading, not on a run, so the test below is the proof.
- [ ] `p0b-15`. `backtest.py:101-113` lists six measures, and `results/measures.py`, 981 lines naming the 27 money measures of the contract, has no caller on this path. Reuse it for money. Track MAE, MFE and drawdown in R in `unit_handler.py`, adds only.
- [ ] `p0b-16`. Catch a raise in `_run` (`backtest.py:187`) and land `failed` with the type and the message. The node's path is untouched. Today the reason is lost and it counts toward the breaker, whose third trip can kill a run queued behind it.
- [ ] `p2-15`. In `QmbRun.close` and `fail`, remove `in/bars` and `in/data` after landing. Keep `in/request.json` and `in/records`, because tests read them. Leave the supervisor untouched. This must run after the lander has read what it needs, so do it last.
- [ ] `seams-9`, `p2-8` and `p0b-22`. In `_lay_out`, copy a stated cost profile to `in/costs/` and funding to `in/funding/` when the study's `cost_rule` or the request names one. `CONTRACTS.md` section 2 allows a Library pin. It stays uncalibrated, which is honest. A swap on a Library item already reaches the run through R07, and its `triple_day` is a full weekday name, because `wed` is refused.
- [ ] Costs, call 9. Per trade, add the trade's cash and a second number beside `r`, keyed by the cash event's `position_id`. Leave `r`, `total_r`, `r_after_costs` and the judge's numbers exactly as they are. Put the judge's read of a trade's R (`judge.py:259`) behind one named function, `trade_r`, so the risk session can flip one line when it decides whether R includes costs.
- [ ] Do not write a `minute` row or a profile from fills here. That is R19 and after G-DEMO. Do not rename `r_after_costs`, which is in Part A's contract and goes to the risk session.

**You see.**

- [ ] A backtest result now shows drawdown and how close each trade came to its stop, in R. If you name a cost profile, the money result changes while R stays the same, and the verdict says plainly that costs are not calibrated yet.
- [ ] A long run no longer eats memory. If a block breaks, the result says why. If the host restarts mid-run, the run closes as failed instead of saying "running" for ever. Run folders clean up after themselves.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_run_honesty.py::test_a_stated_cost_profile_changes_money_and_not_r`. Foundation check 13. Two real jobs on the `world` fixture's synthetic month, with no profile and with commission 3.50 a lot in a stated profile. `total_r` is the same literal in both, net money falls by the literal commission, cash rows appear, and the label `costs_uncalibrated` stays true. Record the literals at the first green run. Run the second through `backtest_judge_run`, and the verdict's words hold "costs uncalibrated".
- [ ] `test_windowed_reader.py::test_a_real_backtest_of_200000_steps_stays_flat`. Foundation check 14. Real `run_loaded` at 10,000 and 200,000 steps. Peak memory stays within `WINDOW_MEMORY_TOLERANCE`. Today it fails by eleven times. The coordinator runs it, because it is long.
- [ ] `test_run_honesty.py::test_a_block_that_raises_lands_a_failed_result_with_its_reason`. A block raising `ZeroDivisionError` lands `failed` with the type and the message, and `metrics.errors` stays 0.
- [ ] `test_restart_closes_runs.py::test_an_opened_try_with_no_close_fails_at_host_start`. Real lander and real store. An `opened` try gets a `failed` close with reason "host restarted", and a second start writes nothing.
- [ ] `test_run_honesty.py::test_a_slow_first_run_answers_something_to_poll` and `::test_motion_both_runs_from_the_row` and `::test_a_run_folder_loses_its_bars_after_landing`. Each asserts its literal status or its file list.
- [ ] Tests that change on purpose are `test_promote.py` where it pins placeholders, and `test_qmb_app.py:191`. Run `uv run --no-sync python -m pytest qmb/tests/test_unit_handler.py qmb/tests/test_run_journal.py -q`. The coordinator runs the app tests.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qmb/tests`, `qmx-agents/apps/qmb/tests/`, `qmx-agents/packages/qmx-judge/tests`, `qmx-agents/packages/qmx-tools/tests`, and in the host `test_promote.py`, at the parent and the head. No model. Save `r10-regression.log`. Pass when the head fails nothing the parent passes, apart from tests named on purpose.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/p2/p1/mem.py <folder>` with `proof_at.sh root`, at the parent and the head. Then run a real job at both on the real March month, with gold's lot step planted at 0.10 and commission 3.50 named in the request. No model. Save `r10-memory.log`. Pass when the parent shows the growth and a net of -169.04, and the head stays inside the tolerance and gives net -249.91, R -4.3841 and 42 cash rows.
- [ ] Lane 3. Run `S/proofs/seams/parity.py 9 <folder>` at the head. No model. Save `r10-parity.log`. Pass when it reads 63 of 63.
- [ ] Lane 4. Whole-repo run, because R10 is the tenth PR. Use `S/tools/run_tests.sh`. No model. Save `r10-whole.log`. Pass when it fails nothing R09's tip passed.
- [ ] Lane 5. Kill a host in the middle of a real run on a throwaway folder and start it again. No model. Save `r10-restart.log`. Pass when `backtest_status` answers failed with "host restarted" and no job runs for it.
- [ ] Lane 6. A sweep of 20 runs on a scratch home. No model. Save `r10-disk.log`. Pass when no `in/bars` or `in/data` folder is left.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r10-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r10-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r10-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r10-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Peak memory of a real backtest at 10,000 and at 200,000 steps, and of `robustness` over a year.
- [ ] Probe. Lane 2's script, interleaved at the parent and the head.
- [ ] Baseline. About eleven times growth, about 340 MB per market on 20 years of M1, a labelled estimate from `p2-1`.
- [ ] Rule. Fails if 200,000 steps exceed 10,000 steps by more than `WINDOW_MEMORY_TOLERANCE`.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r10-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Make a judge that cannot be talked round (R11)

Phase C, a backtest on his facts and data. Source is `A/reports/ground-qmb.md`, "Study rules". An agent can read a result, write a new study naming only the luckiest market with a tiny k, and judge under it at no counted try. The cheap checks take one whole-run number and apply it to every market. Done when both tricks fail by test. This ends phase C, so a whole-repo run follows it. The judge is not a guarded part, but it is what he relies on.

Rows carried. `p2-5` `p2-11` `p2-18`

Proves. A study written after a result costs a counted try and cannot drop a market, and each market answers for its own evidence.

**Depends on.** R10.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-judge/src/qmx_judge/judge.py`.
- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`.
- [ ] Edit `qmx-agents/apps/qmb/jobs/robustness.py` and `qmb/src/qmb/robustness/unit_battery.py`, then `qmx-agents/apps/qmb/app.toml` and `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py`.
- [ ] Edit `qmx-agents/apps/trading-node/app.toml`, by call 11, because `qmb` is in its lock, with its row in `test_shipped_apps.py`.
- [ ] Edit `qmx-agents/packages/qmx-judge/tests/test_judge_verdicts.py` and `qmx-agents/apps/qmb/tests/test_qmb_run_kinds.py`.
- [ ] Create `qmx-agents/packages/qmx-judge/tests/test_judge_cannot_be_talked_round.py`.

**Build.**

- [ ] Subtract. Delete `p2-18`, the clustering test at `test_judge_verdicts.py:237`, which repeats what the next test proves through the verdict.
- [ ] Safety fact. The judge's core is outside the engine and the mini-app core, so no promise in `ground-core.md` section 2 is in reach except M8's one-landing rule. From `ground-qmb.md` section 2 the judge's rules must hold, `test_judge_verdicts.py` and `test_lifecycle.py`, and its numbers still come from `trade_r`. Both shapes rest on reading, level 2, so `S/proofs/p2/p3/shrink.py` flipping is the proof, and a shape that does not flip it stops the PR, by call 20.
- [ ] `p2-5`, the counted try. In `backtest_judge_run` (`functions.py:324`, with `_study` at `:637`), when the study version named was made after the earliest try of the results' families, it lands a counted `spec_edit`, reusing the existing try kind. `_tries` (`:660`) already returns the family, which also closes a rerun after reading. Keying on the version named closes an older study edited after the result, which keeps its k today because its first version predates the try (`S/proofs/plan-review-a/shrink2.py`, level 4). `land_spec_edit` (`host.py:888`) looks only at earlier versions of the same item, and it lands nothing if no result used that study.
- [ ] `p2-5`, the tiny k. A counted try alone does not switch the luckiest-market pull back on, because `judge.py:710` still honours the late study's `fixed` k, and a tiny k leaves every weight near 1. So a study version made after the earliest try judges with the `spread` estimator and `FALLBACK_K`, whatever `k` it names, and the verdict says so in its words. `FALLBACK_K` matters because `estimate_k` falls back to `spec.k` under two markets (`shrink.py:43`). This goes one step past the report's shape, because `shrink.py` cannot flip without it.
- [ ] Trap. Exempt only a `study-quick-*` item whose fields equal `quick_spec`'s, because it is written late by design. `origin` is a free field (`judge.py:196`), and the schema allows `quick`, so an agent could write its own study as `quick` and take the exemption if the test read that word. A study version made before the results lands no try and keeps its own `k`, as today.
- [ ] `p2-5`, the shrink. At `judge.py:706-709`, the shrink always uses every market the results traded, unioned with the markets the study names, as judge.md says "none is dropped for looking bad". Today `sorted(set(named) or ...)` lets a spec narrow the list.
- [ ] `p2-11`. Make the evidence per market. `robustness.py:77` computes one expectancy over all trades, so make the job measure `cost_stress` per market, through `unit_battery`, as a table keyed by market with its window. Make `_evidence` (`judge.py:496`) take a market, and make `_cost_stress`, `_random_entries` and `_walk_forward` read that market's row, and compare its window with the judged result's.
- [ ] Trap. A result whose evidence has no row for a market reads "not run" for that step, so the verdict is incomplete, never a pass. A market that would lose under doubled costs can then no longer pass because another market carried the run.
- [ ] Trap. Do not change R, `trade_r` or the shrink's arithmetic. The risk session owns whether R includes costs, by call 9.

**You see.**

- [ ] The judge can no longer be argued with. An agent that writes a friendlier study after seeing a result pays for it as a counted try, and no market can be dropped for looking bad. Each market now has to pass the cost stress on its own numbers.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_judge_cannot_be_talked_round.py::test_a_study_written_after_the_result_counts_a_try`. On 20 markets of +0.06R through `backtest_judge_run`, as `shrink.py` does, `fx.m02` keeps raw 0.2193 shrunk to 0.0558 under the late study too, all 20 markets stay in `per_market`, deflated Sharpe is no higher than 0.1024, and `spec_edit` tries landed is 1. Today it reads shrunk 0.2193, weight 1.0000, deflated Sharpe 0.7084, one market and 0 tries. An older idle study edited after the result gives the same counted try and the same 0.0558, where today it reads shrunk 0.2193, weight 1.0000, deflated Sharpe 0.7084 and 0 `spec_edit` tries (`shrink2.py`).
- [ ] `test_judge_cannot_be_talked_round.py::test_a_market_that_loses_under_doubled_costs_does_not_pass_on_another`. Two markets with their own evidence rows, one failing `cost_stress`, give that market's step `fail`. Today both read the first result's number.
- [ ] `test_judge_cannot_be_talked_round.py::test_quick_spec_lands_no_try`. Tests that change on purpose are in `test_qmb_run_kinds.py`, which pins the robustness measures' shape, and in `test_judge_verdicts.py`, whose fixtures must now give evidence per market. Run `uv run --no-sync python -m pytest tests -q` in `qmx-judge`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qmx-agents/packages/qmx-judge/tests`, `qmx-agents/packages/qmx-host/tests/test_lifecycle.py`, `qmx-agents/apps/qmb/tests/test_qmb_run_kinds.py` and `qmx-agents/packages/qmx-engine/tests/test_templates.py`, at the parent and the head. No model. Save `r11-regression.log`. Pass when the head fails nothing the parent passes, apart from tests named on purpose.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/p2/p3/shrink.py <folder>` with `proof_at.sh agents`, at the parent and the head. No model. Save `r11-shrink.log`. Pass when the parent prints shrunk 0.2193 and 0 tries, and the head prints shrunk 0.0558 and 1 try.
- [ ] Lane 3. A real `robustness` job on two markets and `backtest_judge_run` over it. No model. Save `r11-evidence.log`. Pass when the verdict's cost step names each market with its own number.
- [ ] Lane 4. Whole-repo run at this phase end, with `S/tools/run_tests.sh`. No model. Save `r11-whole.log`. Pass when it fails nothing R10's tip passed.
- [ ] Lane 5. With a model, ask a copilot chat on `haiku` to judge the dummy's result under a friendlier study it writes. Save `r11-copilot.log`. Pass when the try log gains a `spec_edit` and the verdict is unchanged in substance.
- [ ] Lane 6. Rerun `test_conformance.py` in `qmx-judge`, which `reports/p2.md` owed. No model. Save `r11-conformance.log`. Pass when it reads 38 passed or names each change on purpose.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r11-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r11-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r11-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r11-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds of `backtest_judge_run` on 20 markets.
- [ ] Probe. Lane 2.
- [ ] Baseline. Record the parent's value first.
- [ ] Rule. No fail rule, recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r11-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Give one true verdict and one paper (R12)

Phase D, agents can build a unit and backtest it. Source is `A/reports/ground-core.md` blocks C and D, which correct the audit on one point. Neither `p6-5` nor `p6-15` needs an engine change, by call 10. Today a sweep that traded reads as "placed no trades", a template routes on a verdict a model copied, one failed unit gets two papers, and every failed unit dies of "behaviour". Done when foundation checks 15 and 16 pass.

Rows carried. `p6-1` `p6-7` `p6-3` `p6-4` `p6-5` `p6-15` `p6-20`

Proves. A real job, lander, judge and scorecard land one paper with the right cause, and a forged pass routes as fail.

**Depends on.** R11.

**Files.**

- [ ] Edit `qmx-agents/apps/qmb/jobs/sweep.py`, `qmx-agents/apps/qmb/jobs/backtest.py` and `qmx-agents/apps/qmb/qmb_tester.py`, then `qmx-agents/apps/qmb/app.toml` and `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py`.
- [ ] Edit `qmx-agents/packages/qmx-judge/src/qmx_judge/judge.py`, `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py` and `qmx-agents/packages/qmx-host/src/qmx_host/host.py`.
- [ ] Edit the templates `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/b-build-and-prove/definition.json`, `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/u1-run-on-every-market/definition.json` and `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/u2-where-its-rules-hold/definition.json`, with their `scripts/`.
- [ ] Delete `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/_shared/death-certificate/` and `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/b-build-and-prove/death-certificate/`.
- [ ] Edit `qmx-agents/packages/qmx-engine/tests/test_templates.py` and `qmx-agents/apps/qmb/tests/test_qmb_run_kinds.py`.

**Build.**

- [ ] Subtract. Delete the certificate block with its one caller, `b` (`p6-4`). `proposal-card` has two callers, so it stays for u2. This removes about 420 lines. Trim `p6-20` in `test_templates.py:355`, the hand-kept id lists of 65 lines, keeping the uniqueness and folder relations.
- [ ] Safety fact. The core already lands certificate and card once per verdict (`judge.py:933-960`), so removing the block loses nothing but the model's explanation, and the scorecard's writer already explains. Level 3. A script can hand on `@library:<verdict_id>`, the shipped `library` node reads the real object, and the rule routes on that. Level 4 on the real engine with a fake Library (`S/proofs/ground-core/test_verdict_read.py`). The read on the real store is level 2, from `test_served.py::test_a_read_is_served_while_the_hosts_store_holds_the_writer_lock`. E1, E2, E5, E8, E11 and M8 must hold. The engine is untouched, so E12 is not in reach.
- [ ] `p6-1`. `jobs/sweep.py:69` writes `{"cells": rows}` with counts, while `functions.py:629` reads `body["trades"]`, so 6 trades measured give `no_trades` and a death certificate on main (`S/proofs/p6/test_sweep_verdict.py`, level 4). Have `sweep.py` add a flat `trades` list only when the grid names no numbers. Move `_trade` from `jobs/backtest.py:56` to `qmb_tester.py` so both jobs share it.
- [ ] Trap. A numbers grid must never be flattened. The judge pools a result's trades by market and refuses overlaps (`judge.py:638`), and flattening would pool variants of one market as one record. `test_qmb_run_kinds.py:176` pins `cells`, and it must stay. u1 and u2 ask a markets-only grid (`route.py` in each), so one cell per market means no overlap and each market judged alone. Level 3, read at `judge.py:707-711`. `robustness`, `whatif` and `walk_forward` list no trades, so u2's sweep plus what-if will not trip the overlap refusal, level 2.
- [ ] `p6-15`, call 10. In `b`, u1 and u2, add a read step after the referee. A script hands on `@library:<verdict_id>`, a `library` node reads the object, and a script gives the rule the Library's `overall`. Catch a forged id by comparing `fields.unit` to the run's pin and by the verdict's results. The trial's form is `HAND`, `read` and `JUDGE` in `test_verdict_read.py`.
- [ ] `p6-3` and `p6-4`. In `b`, drop the `propose` and `certify` subworkflows and show the core's `cards` in the scorecard. The block's cause reader goes with it (`classify.py:47-54`, where the answer at `functions.py:364` has no steps). u2 keeps `proposal-card`, reading the core's card.
- [ ] `p6-5`, call 10. `land_judgement` gains a port, `RecallEngine.write("home", "judge", row)`, which the host already composes (`host.py:1136`). The certificate fills its `memory_row` field (`death-certificate.schema.json:31`). `home` rows reach every chat's snapshot (`surface.py:661`), and adding the `memory` toolset to `b`'s builder gives it `memory_check`. All of this is level 2, read and not run. If it does not hold when run, stop and report, by call 20, because the answer then is the engine's U1(a), which needs his word.
- [ ] Trap. The schema file `death-certificate.schema.json` lives with the deleted block, so check that the core's certificate kind in `qmx_library/kinds/` is what the row writes to, and keep that one.
- [ ] Trap, on purpose. The tests at `test_templates.py:997` and `:1023` must change, because fixtures must now plant a real verdict. That also closes the `p6-7` gap, which is why `p6-1` passed every check.

**You see.**

- [ ] Run a unit on every market and it now tells the truth about what traded. You get one paper per decision, with the real reason it failed, and an agent building a new unit is warned when an idea has already died. A model cannot talk a failed unit into a pass, because the route reads the stored verdict, not the model's copy.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_qmb_run_kinds.py::test_a_sweep_that_traded_is_judged_on_its_trades`. `p6-7`, the audit's test with literals. Real sweep on `fx.eurusd` with `grid={"markets": ["fx.eurusd"]}`, then real `backtest_judge_run`. `measures.trades` is 6, `overall` is not `no_trades`, and `per_market` has one row. Today `no_trades` with an empty `per_market`.
- [ ] `test_templates.py::test_b_real_qmb_real_referee_real_scorecard`. Foundation check 15. On the `world` fixture for one market and for a sweep, it lands one certificate, cause `costs` when the cost step failed, and no second paper on the run's ref.
- [ ] `test_templates.py::test_a_forged_pass_routes_as_fail`. Foundation check 16. A referee step answering `pass` over a stored `fail` reads `overall: fail`, takes the rule's false port, and the propose path does not run. A forged id naming another unit's verdict is refused.
- [ ] `test_templates.py::test_a_dead_unit_leaves_a_memory_row_the_builder_can_read`. The row is in `memory_check`'s answer for that idea.
- [ ] Tests that change on purpose are `test_templates.py:997`, `:1023`, and `:355`. Run the engine's `test_templates.py` and `test_shared*.py`. The coordinator runs them, because they are long.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qmx-agents/packages/qmx-engine/tests`, `qmx-agents/packages/qmx-judge/tests`, `qmx-agents/apps/qmb/tests/`, and in the host `test_lifecycle.py` and `test_memory*.py`, at the parent and the head. No model. Save `r12-regression.log`. Pass when the head fails nothing the parent passes, apart from tests named on purpose.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/p6/test_sweep_verdict.py` at the parent and the head with `proof_at.sh agents`, under pytest. No model. Save `r12-sweep.log`. Pass when the parent fails with "the sweep traded but the referee says it placed no trades" and the head passes.
- [ ] Lane 3. Run `S/proofs/ground-core/test_verdict_read.py`, then the same read on a real store through the real `library` node. No model. Save `r12-read.log`. Pass when both route on `fail` with no engine diff, confirmed by `git diff <parent> HEAD -- qmx-agents/packages/qmx-engine/src/qmx_engine ':!qmx-agents/packages/qmx-engine/src/qmx_engine/templates'` being empty.
- [ ] Lane 4. Install the pack on a throwaway folder, and run `b-build-and-prove` on `haiku` with no `fixture`, on the store's data. This lane uses a model. Save `r12-b.log`. Pass when one paper lands, its cause matches the verdict's failed step, and the scorecard reads the core's card.
- [ ] Lane 5. Run `u1-run-on-every-market` on `haiku` over two markets. This lane uses a model. Save `r12-u1.log`. Pass when each market has its own row and the verdict counts the trades.
- [ ] Lane 6. Reinstall the pack and read versions. No model. Save `r12-versions.log`. Pass when `b`, u1 and u2 publish new versions, each with a new hash, as E2 and E8 say.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r12-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r12-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r12-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r12-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds of one `b` run on the recorded fixture.
- [ ] Probe. The fixture test's own time at the parent and the head.
- [ ] Baseline. Record the parent's value first.
- [ ] Rule. No fail rule, recorded for the trail. The template gains one read and loses two subworkflows.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r12-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Say what a check with no Library cannot see, and fix the slow-lane words (R13)

Phase D, agents can build a unit and backtest it. Source is `A/reports/ground-core.md` blocks E and F and its new defect `core-n2`. The script gate and the hook check with no Library, and they misread what only the Library can settle. The hook goes silent when any such kind is present, even beside a real error, and the block fails on them and spends fix rounds. So build and prove can test only three markets. Done when foundation check 17 passes.

Rows carried. `p34-9` `core-n2` `p34-15` `p6-9` `p6-12` `p6-13`

Rows in part. `p6-2` by its template half, which finishes that row. R07 carried its run half.

Proves. On a market only the Library knows, a clean unit reaches QMB through the gate and a broken one gets its error from the hook.

**Depends on.** R12.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/unit_check.py`.
- [ ] Edit `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/_shared/unit-check/scripts/check.py`, `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/b-build-and-prove/unit-check/scripts/check.py` and `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/b-build-and-prove/scripts/ready.py`.
- [ ] Edit `qmx-agents/plugin/hooks/hooks.json` and regenerate `qmx-agents/plugin/plugin.manifest.json`.
- [ ] Edit `qmx-agents/packages/qma-harness/src/qma/harness/launch.py`, `qmx-agents/packages/qma-harness/tests/test_launch.py` and `qmx-agents/packages/qma-harness/tests/live/test_unit_hook_probe.py`.
- [ ] Edit `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/gw-guard-watchdogs/scripts/read.py`, `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/u3-dictionary-expansion/definition.json` and `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/s4-daily-data-review/scripts/read.py`.
- [ ] Edit `qmx-agents/packages/qmx-engine/tests/test_templates.py`.
- [ ] Create `qmx-agents/packages/qmx-tools/tests/test_offline_check.py`.

**Build.**

- [ ] Subtract. No `test-delete` row is left in these files, and R12 took `p6-20`. `p6-21` stays, because `marked-sources` is now wired and the other three blocks stay.
- [ ] Safety fact. With the hook's five kinds removed, the dummy on GBPUSD and on US500 is left with no errors, and a broken number on GBPUSD is left with `outside_range`. Level 4 with the real checker (`S/proofs/ground-core/template_facts.py`). The lander still compiles with the Library before any run (`LanderLibrary._compiled`), level 2, so nothing unsafe gets through. E2 means each changed template gets a new version. E4 and E6 must hold, because a script still opens no Library and an agent gets only the tools it declares. E11 must hold for the slow lane.
- [ ] `p6-2` and `p34-9`. Add one function with one name in `qmx_tools/unit_check.py`, `offline_checked(document, previous=None)`. It calls `checked(None, ...)` and moves `no_record`, `no_pip`, `calendar_not_held`, `data_level_missing` and `pin_unresolved` out of `errors` into `notes`. A pass with deferred kinds says so in `notes`. Only when that move is what emptied `errors`, it also calls `compile_unit` with `gather(None, document).context` and keeps its problems outside the five kinds, because `check/run.py:67` calls the compiler only when the layers found no errors, and on GBPUSD `no_record` is an error. In any other case the check already reached the compiler or still has errors to fix, and `compile_unit` reruns the layers, so the agent would read each error twice (`S/proofs/plan-fix-check/offline2.py`, level 4). Without this call, everything R04 and R05 refuse is invisible on a Library-only market. A halt on GBPUSD reads `no_record` from `checked` alone, while `compile_unit` says `halts_not_built` and `no_record` (`S/proofs/plan-review-a/offline.py`, level 4). The hook and `_shared/unit-check/scripts/check.py:32` both call it, and the copy in `b-build-and-prove/unit-check/` follows, because the drift test checks the copies.
- [ ] `p6-2`. `ready.py:40-52` stops treating those kinds as fatal, because the verdict is now a pass with notes. `test_templates.py:1064` pins today's words, and it must change on purpose.
- [ ] `p34-9`. In `hooks.json:10`, drop the `library_settles` filter that goes silent, and print the errors `offline_checked` leaves. Update the hook's `description`. `hooks.json` changes, so regenerate `plugin.manifest.json`, which `test_packs.py:72` guards.
- [ ] `core-n2` and `p34-15`. The hook runs a bare `python -c`, so it works only if the first `python` on the CLI's PATH is the host's environment. Under `uv run` PATH has the environment first, which is how A14's probe passed. A host started another way would make every Write or Edit in every chat wait out the 8 s timeout and give no feedback. Have the harness put its own interpreter's folder first on the CLI's PATH in `launch.py`. Level 2, unproven, and the test below is its proof.
- [ ] `p6-9`. In `gw-guard-watchdogs/scripts/read.py:121`, read `kill_level` over `held_back`, as `stand_down` already is, and let the latest row per scope decide, with GREEN clearing. It bears on money, since he reads this word. A row with no `level` decides nothing, because R21's flatten row has none. The audit's test is `S/proofs/p6/test_gw_kill.py`.
- [ ] `p6-12`. In `u3-dictionary-expansion/definition.json`, call `_shared/marked-sources` as a child before `draft`. Exposure is narrow, because the agent holds `blocks` only.
- [ ] `p6-13`. In `s4-daily-data-review/scripts/read.py:52-60`, give the writer counts and keep `months` and `fingerprints` only in the landed artifact. A guess of 30 series over 6 years at 80 bytes is about 170 KB of prompt.
- [ ] Trap. The record half of a Library-only market came with R07 and R08, so run `b` on GBPUSD only at this head, not lower.

**You see.**

- [ ] Agents can now build and prove a unit on any market with a record in your Library, not only three. When an agent writes a broken unit, it hears exactly what is wrong straight away, whichever market it picked.
- [ ] The node watcher note no longer says "Well" while a kill still holds. The daily data review costs a short prompt.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_offline_check.py::test_the_dummy_on_gbpusd_passes_with_notes` and `::test_a_broken_number_on_gbpusd_keeps_its_error`. The first gives verdict `pass` and five or fewer deferred kinds in `notes`, and the second gives `outside_range` in `errors`. Both real `checked`.
- [ ] `test_offline_check.py::test_a_second_stop_on_gbpusd_keeps_its_error`. Part of foundation check 17. A second stop on GBPUSD gives `exit_not_built` in `errors`, with no other error left after the five kinds move to `notes`. Without the `compile_unit` call it reads a pass with notes.
- [ ] `test_templates.py::test_b_on_a_library_only_market_reaches_qmb`. Foundation check 17. A GBPUSD record on the real store, with `b` on its recorded fixture path through `ready`, reaches the `backtest` node. Today `no_record` stops it.
- [ ] `qma-harness` gains `test_the_hook_tells_the_agent_on_a_library_only_market`, in `tests/live/test_unit_hook_probe.py`'s command-alone form, needing no model. A broken GBPUSD unit gets `additionalContext` naming `outside_range`, and a clean one prints nothing.
- [ ] `test_launch.py` gains `test_the_cli_path_starts_with_the_host_interpreter`. The first PATH entry equals `Path(sys.executable).parent`.
- [ ] `test_templates.py` gains `test_the_watcher_reads_a_held_kill_after_a_day_and_clears_on_green`, from `S/proofs/p6/test_gw_kill.py`, and `test_s4_gives_the_writer_counts_only`.
- [ ] Tests that change on purpose are `test_templates.py:1064`. Run `uv run --no-sync python -m pytest tests/test_offline_check.py -q` in `qmx-tools`, and `test_packs.py -k shipped_plugin_manifest` in `qma-harness`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qmx-agents/packages/qmx-tools/tests`, `qmx-agents/packages/qma-harness/tests/test_packs.py` and `qmx-agents/packages/qmx-engine/tests/test_templates.py`, at the parent and the head. No model. Save `r13-regression.log`. Pass when the head fails nothing the parent passes, apart from tests named on purpose.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/p6/gate_proof.py` and `S/proofs/ground-core/template_facts.py` with `proof_at.sh agents`, at the parent and the head. No model. Save `r13-gate.log`. Pass when the parent reads `no_record` as fatal and the hook silent, and the head reads a pass with notes and the error left over.
- [ ] Lane 3. The hook with the venv off PATH. Start the probe's command with the environment removed from PATH, as `ground-core.md` `core-n2` says would prove it, through the harness's launch. No model. Save `r13-path.log`. Pass when the hook answers within its timeout.
- [ ] Lane 4. With a model, `b-build-and-prove` on `haiku` for a unit on GBPUSD with one month in the store. Save `r13-b.log`. Pass when the run reaches a verdict, and the gate spent no fix round on `no_record`.
- [ ] Lane 5. With a model, the probe's Windows form, `QMX_TEST_LIVE=1 ... test_unit_hook_probe.py -k reaches_the_model`, on `haiku`. Save `r13-probe.log`. Pass when its PASS lines read as `evidence/a14` did.
- [ ] Lane 6. Run `s4-daily-data-review` on a store with 30 fake series, and read the writer's prompt size. No model. Save `r13-s4.log`. Pass when it is under 10 KB.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r13-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r13-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r13-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r13-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds of the hook's command on a unit document, and bytes of `s4`'s prompt.
- [ ] Probe. Lane 3's timing and lane 6.
- [ ] Baseline. The hook's timeout is 8 s. `s4`'s prompt is about 170 KB on a guess.
- [ ] Rule. Fails if the hook passes 8 s, or if `s4`'s prompt passes 10 KB on 30 series.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r13-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Prove the foundation and stop (R14)

Phase D, agents can build a unit and backtest it. Source is "What the foundation works means" in `P/build/repair/PLAN-SHAPE.md`, and the head of this plan. He asked one question, whether agents can build units and backtest them. This PR adds the proof checks no earlier PR added, which is check 18 and the runner that names all 18, runs all 18, and stops. Done when `tools/proof_foundation.py` prints 18 PASS lines, and he has been told in plain words. Passing the judge is not the dummy's goal.

Rows carried. None. This PR carries the proof, not a row.

Proves. All 18 foundation checks read PASS at the stack tip.

**Depends on.** R13.

**Files.**

- [ ] Create `tools/proof_foundation.py` and `tools/tests/test_proof_foundation.py`.
- [ ] Create `qmx-agents/packages/qma-harness/tests/live/test_his_own_test.py`.

**Build.**

- [ ] Subtract. No `test-delete` row sits in these files.
- [ ] Safety fact. This PR adds a runner and one live test, and it changes no product file, so no promise in `ground-core.md` section 2 is in reach. Confirm that with `git diff --stat <parent> HEAD`. Every safety fact of R03 to R13 is reread here by its own check.
- [ ] Write `tools/proof_foundation.py` with one literal table, one row per check, holding its number, its plain name, the environment (root or agents), the pytest node ids and a time limit. Print one `PASS 7 ...` or `FAIL 7 ...` line per check, and exit non-zero on any FAIL. Read pytest's summary and count a skipped test as FAIL, because pytest exits 0 when every test skips, check 18 skips unless `QMX_TEST_LIVE=1` is set, and other tests here skip on a missing machine fact. `--list` prints the table. `--only 7` runs one, and `--only 1-17` runs that range. Add a `--walls` table, empty until R24 fills it. Put `# ambient-scan: allow` on any line that reads the clock.
- [ ] Fill the table from the sections that added each check.
  - [ ] Check 1 is `qmx-host/tests/test_repair_lands.py` and `tools/tests/test_app_env_fresh.py::test_a_changed_library_reaches_the_app_env_at_the_next_start`. Check 2 is `qmx-apps/tests/test_install_holds_nothing.py`.
  - [ ] Check 3 is `qml/tests/test_nothing_silent.py`. Check 4 is `qmx-agents/apps/qmb/tests/test_qmb_app.py::test_a_long_only_unit_makes_no_short_fills`. Check 5 is `::test_an_agent_writes_adx_above_25_and_a_job_runs_it` in that file. Check 6 is `qmb/tests/test_run_journal.py::test_a_short_only_run_moves_the_number_and_the_row_shows_why`.
  - [ ] Check 7 is `qmx-host/tests/test_dictionary_full_size.py`. In `test_qmb_app.py`, check 8 is `::test_a_fresh_home_with_ticks_in_the_store_lands_a_result`, check 9 is `::test_no_month_is_refused_naming_the_month_and_the_template`, check 10 is `::test_a_month_through_a_csv_and_through_the_store_gives_the_same_trades`, check 11 is `::test_a_record_moved_on_main_shows_in_the_next_run`, and check 12 is `::test_a_study_forbidding_gaps_beats_a_chat_allowing_them` with `::test_a_sealed_month_is_refused_and_no_sealed_file_sits_in_a_run_folder`.
  - [ ] Check 13 is `qmx-agents/apps/qmb/tests/test_run_honesty.py::test_a_stated_cost_profile_changes_money_and_not_r`. Check 14 is `qmb/tests/test_windowed_reader.py::test_a_real_backtest_of_200000_steps_stays_flat`.
  - [ ] Checks 15 and 16 are `qmx-engine/tests/test_templates.py::test_b_real_qmb_real_referee_real_scorecard` and `::test_a_forged_pass_routes_as_fail`. Check 17 is `::test_b_on_a_library_only_market_reaches_qmb` in that file, with `qma-harness/tests/live/test_unit_hook_probe.py::test_the_hook_tells_the_agent_on_a_library_only_market` and `qmx-tools/tests/test_offline_check.py::test_a_second_stop_on_gbpusd_keeps_its_error`.
  - [ ] Check 18 is the live test below, under `QMX_TEST_LIVE=1`.
- [ ] If a section's test is missing at this head, add it here and name it in the PR body. A check nobody added would otherwise read as nothing. That is why this PR exists.
- [ ] Write `test_his_own_test.py`, check 18. It goes through a real host on a scratch folder, over the host's chat routes, as the boot recipe says for every model lane. It holds `D:/QMX-worktrees/.engine-lane-lock`. It makes the folder under `S/homes/r14-18/` with the first-start card, so QMB is enabled and `[qmb] bars` is empty. It makes the login junction by the boot recipe, starts `python -m qmx_host serve --home <folder> --port <port>` with the file keyring, and removes the junction in its `finally`. It lands EURUSD for March 2025 through `download-dukascopy` first, or through the door from R09's saved month if the network is down or `QMX_TEST_SAVED_MONTH=1` is set, and says which in its log.
- [ ] The sentence is exactly "Build me a unit on EURUSD from the dictionary blocks that only enters when ADX is above 25, backtest it on March 2025, and tell me in plain words what the judge says." The dummy lacks that rule, so a chat cannot pass by calling `unit_new` with no overrides (`functions.py:719`). The test opens the chat with `POST /api/chats` on model `haiku`, sends the sentence with `POST /api/sessions/<sid>/turns`, reads its blocks from `GET /api/events/sessions?subject=<sid>`, and answers each ask with `POST /api/approvals/<ask_id>`, as he would.
- [ ] The test asserts from the chat's tool-call journal, in order, `blocks_find` or `blocks_match`, then `unit_new`, then `unit_check` until it passes, then `backtest_run`, then `backtest_judge_run`. It asserts from the store that the draft binds `adx@1` and `value-above@1`, that the result has at least 1 trade, that the result's `consumed` edge names a `dataset` item, and that a verdict exists. It asserts that the chat's last message holds the verdict's words from `says()`, which are the words before " by the " in the stored verdict's `says` field, compared without case. A search for the raw `overall` would fail for no reason, because the word `incomplete` reads "Not judged yet". It does not assert which verdict. A fail is rerun once, and two fails count as FAIL.
- [ ] Do not touch a product file to make check 18 pass. A failure here is a finding against the PR that owns it. Stop and report it to the coordinator, which sends it to one fix round on a new head.

**You see.**

- [ ] You get one short message that says what now works, in plain words, and one thing you can ask the copilot to see it yourself. For example, "Build me a unit on EURUSD from the dictionary blocks that only enters when ADX is above 25, backtest it on March 2025, and tell me in plain words what the judge says."
- [ ] The work then stops and waits for your word. The risk session needs nothing from this program, and you can resume it whenever you like.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_proof_foundation.py::test_every_check_names_a_test_that_exists`. Each node id in the table collects in its environment, and the table has rows 1 to 18 with no gap. This is a relation across rows, which keeps the runner from lying.
- [ ] `test_proof_foundation.py::test_a_failing_check_prints_fail_and_exits_non_zero`. With a table of one failing fake node, it prints `FAIL 1 ...` and exits 1, and a fake node that only skips prints `FAIL 1 ...` and exits 1 too. Run `uv run --no-sync python -m pytest tools/tests/test_proof_foundation.py -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Whole-repo run at this phase end, with `S/tools/run_tests.sh`. No model. Save `r14-whole.log`. Pass when it fails only what `A/tests/SUMMARY.txt` failed for a named reason, or fewer.
- [ ] Lane 2. Fail-today proof. Run `tools/proof_foundation.py --list`, then match each check to its PR's `owner-red.log` in `S/evidence/`, which names the test failing at that PR's parent. A check whose test that log does not name is copied to that PR's parent and run there, as R08's lane 2 does. No model. Save `r14-red.log`. Pass when every check from 1 to 17 has its red named.
- [ ] Lane 3. Run `tools/proof_foundation.py --only 1-17` at the head. No model. Save `r14-proof.log`. Pass when it prints 17 PASS lines.
- [ ] Lane 4. Check 18 on `haiku`, through `tools/proof_foundation.py --only 18`. This lane uses a model. Save `r14-his-test.log`. Pass when it prints PASS, and the saved chat journal reads as the Build box says.
- [ ] Lane 5. Check 18 again with `QMX_TEST_SAVED_MONTH=1`, so the month comes through the door and the fallback path runs too. This lane uses a model. Save `r14-saved-month.log`. Pass when it prints PASS and its log says the door landed the month.
- [ ] Lane 6. Reinstall the template pack on check 18's folder with `python -m qmx_engine templates install`. No model. Save `r14-pack.log`. Pass when no template refuses, and any enabled trigger stays on what was enabled.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r14-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r14-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r14-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r14-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Minutes for the whole proof, and plan usage on `haiku` for check 18.
- [ ] Probe. The runner's own totals in lanes 3 and 4.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule, recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log`.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.
- [ ] Stop the program at G-FOUNDATION. Send him the plain message from "You see", the count of PRs done, left and added, and the stack list up to here. Disarm the tick. Do not start R15 without his word.

## Make the node's records true (R15)

Phase E, records and what reaches him. This is the first PR after G-FOUNDATION, so start it only on his word. Source is `A/reports/ground-start.md` block A. One entry blocked with a reason the journal's closed list does not hold kills that deployment's journal for good, while the unit keeps trading. And every trade the node makes never becomes a Library trade or a paper score, because its rows carry no account. Everything about records rests on this PR. Done when wall checks W3 and the first half of W4 pass.

Rows carried. `seams-3` `p0b-4` `p34-1` `p34-10`

Proves. A real node trade reaches the Library, and a blocked entry with any of the three unlisted texts that reach a row leaves rows landing.

**Depends on.** G-FOUNDATION, then R14.

**Files.**

- [ ] Edit `qmb/src/qmb/results/journal.py` and `packages/qmf-data/src/qmf/data/journal_kinds/unit.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmx-agents/apps/trading-node/app.toml`, by call 11, because `qmb`, `qmn` and `qmf-data` are in its lock, and `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` for its version row.
- [ ] Edit `qmx-agents/packages/qmx-host/tests/test_harvest.py` and `qmx-agents/packages/qmx-judge/tests/test_no_bot_writes.py`.
- [ ] Create `qmn/tests/test_journal_reason_census.py` and `qmx-agents/packages/qmx-host/tests/test_node_trade_reaches_the_library.py`.
- [ ] Edit `qmb/tests/test_run_journal.py`, to pin that a QMB run stays strict.

**Build.**

- [ ] Subtract. No `test-delete` row sits in these files. The hand-written accounts at `test_harvest.py:95-103` and `test_no_bot_writes.py:47-54` go, replaced by rows from the real writer, which is `p34-10`.
- [ ] Safety fact. The account field only adds to a row, and the proof's control run shows the rest of the path already works once it is set. Level 4 (`S/proofs/p34/p1_trade_account.py`, as written trades=0 paper_runs=0, with the account set trades=1 paper_runs=1). Account is not in the partition key, so no series moves, and backtest worlds are not projected. From `ground-start.md` section 2 these must hold, a write to a live stream fsyncs before the node acts, one writer per stream, and a QMB run fails at `close()` when a reason has no code. M5 and M6 are not in reach. `parity.py` must still read 63 of 63.
- [ ] `p34-1`. `open_live` (`journal.py:171`) takes `account`. Its one caller (`runtime.py:2421`) holds `deployment.account_id`. `RunJournal._facts` (`journal.py:247`) sets it, because `records.py:527` and `:567` return None without one.
- [ ] `seams-3` and `p0b-4`. Make a live journal tolerant. On a journal from `open_live`, a text with no code writes the row with one new appended code, as the design says "closed and appendable", so an unlisted word costs a label and not the journal. The new code goes in `REASON_CODES` too (`packages/qmf-data/src/qmf/data/journal_kinds/unit.py:43-74`), because `RunJournal` is not the only gate. The writer checks `reason` against that list, and with the code only in `journal.py` the writer refuses the row and the journal dies as it does today (`S/proofs/plan-review-b/p2_small.py`, level 4). Today `journal.py:376` and `:305` set `_refused`, `journal.py:259` then drops every later row, `append` returns None, `_Journal.append` (`runtime.py:1297`) ignores it, and only `close()` reports it, which the node never calls.
- [ ] Trap. `RunJournal.open`, the QMB path, stays strict. A QMB run must keep failing at `close()` when a reason has no code, because that protects evidence. Nothing in `qmb/tests` or `qmn/tests` pins this by the words "closed list", so add a test that does.
- [ ] `seams-3`. Add the four texts with no code to `_REASON_WORDS` (`journal.py:46`). They are at `runtime.py:1007`, `:1186`, `:2301` and `:1609`. The census found the first three among 32 Blocked and guard texts, and `:1609` reaches the journal through `Unprotected`, not `Blocked`. `:1186` cannot reach a row, because a close's `Blocked` writes no `Skip`, so only the census holds it, level 3. Whether `:1007` reaches the journal was not walked, level 2, and the repair covers it either way.
- [ ] `p0b-4`. Expose a real write failure as a read-only property on `RunJournal`. `guard.check` (`runtime.py:2269`) answers "the node journal could not be written", which already maps to `health_stop` and stops entries only, as design JR-13 says. The status word stops saying Trading, and `operations.py:853` already has the reason line. Exits are not touched. `cross_unit_hook` is plumbing around a placeholder, so leave it.
- [ ] Add the census as a test, moving `S/proofs/ground-start/census.py` into `test_journal_reason_census.py`. It walks `runtime.py`, `unit_handler.py`, `reconciler.py` and `stand_down.py` for every `Blocked`, `Unprotected`, `Skip`, guard and `blocks =` text and asserts each has a code, so a new text with no code fails CI. It must use repo-relative paths.

**You see.**

- [ ] Every trade your practice node makes now reaches your Library and counts toward its paper score. A strange block reason can no longer silently stop the node's record while it keeps trading. If the record truly cannot be written, the node stops new entries, keeps its exits, and tells you why.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_node_trade_reaches_the_library.py::test_a_real_writer_row_lands_a_trade_and_a_paper_run`. A real `RunJournal.open_live` row through a real `Records` round, with no patch and no hand-written account. It gives 1 `trade` item and 1 `paper-run`, unchanged by a second round. Today 0 and 0.
- [ ] `test_node_trade_reaches_the_library.py::test_each_unlisted_text_keeps_rows_landing`. On the real node harness, an entry blocked with each of the three texts that reach a row, `:1007`, `:2301` and `:1609`, writes a row with a code, and the next signal row lands on disk and in the store. This is W3.
- [ ] `test_journal_reason_census.py::test_every_text_the_node_can_write_has_a_code`. The literal expected value for texts with no code is `{}`. Today it holds 4, the 3 the proof script finds and `:1609` through `Unprotected`. This test holds `:1186`, which no row can reach.
- [ ] `test_run_journal.py::test_a_qmb_run_with_an_unlisted_reason_fails_at_close`. Keeps the strict path honest. It passes today and must keep passing.
- [ ] Tests that change on purpose are `test_harvest.py:95-103` and `test_no_bot_writes.py:47-54`, because a test that plants a row the real path never writes is replaced when the PR touches it. Run `uv run --no-sync python -m pytest qmn/tests/test_journal_reason_census.py qmb/tests/test_run_journal.py -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qmn/tests/test_app_runtime.py`, `test_app_stand_down.py`, `test_app_status_truth.py`, `qmb/tests/test_run_journal.py`, `packages/qmf-data/tests`, and in the host `test_harvest.py`, `test_records.py`, and `qmx-judge/tests/test_no_bot_writes.py`, at the parent and the head. No model. Save `r15-regression.log`. Pass when the head fails nothing the parent passes, apart from tests named on purpose.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/p34/p1_trade_account.py <folder>` with `proof_at.sh agents` and `S/proofs/seams/poison.py <folder>` with `proof_at.sh root`, at the parent and the head. No model. Save `r15-proofs.log`. Pass when the parent gives trades=0 and a journal that stops, and the head gives trades=1 and rows that keep landing.
- [ ] Lane 3. Run `S/proofs/ground-start/census.py` at the head. No model. Save `r15-census.log`. Pass when it prints "no code 0".
- [ ] Lane 4. Run `S/proofs/seams/parity.py 9 <folder>` at the head. No model. Save `r15-parity.log`. Pass when it reads 63 of 63.
- [ ] Lane 5. Whole-repo run, because R15 is the fifteenth PR. Use `S/tools/run_tests.sh`. No model. Save `r15-whole.log`. Pass when it fails nothing R14's tip passed.
- [ ] Lane 6. Make the journal folder read-only under a running node on the conformance venue, then send a signal. No model. Save `r15-writefail.log`. Pass when status gives the journal reason, entries stop, and an exit still goes.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r15-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r15-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r15-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r15-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Microseconds per journal row at the node.
- [ ] Probe. A timed loop of 10,000 rows through `open_live` at the parent and the head, interleaved.
- [ ] Baseline. Record the parent's value first.
- [ ] Rule. Fails if the head is more than 10% slower, because this sits on the order path.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r15-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Make alarms and deep logs reach him (R16)

Phase E, records and what reaches him. Source is `A/reports/ground-start.md` blocks B, C and D. On every installed node his phone alarms are silently off, because the node reads its alarm list from a file an installed node does not have. One odd log line stops deep logs for every app, and every supervisor event reads as plain info. Done when wall checks W1 and W2 pass.

Rows carried. `chief-2` `known-10` `known-11` `known-12` `triage-9` `p5a-12`

Proves. A wheel-built node env loads the alarm list and a real alarm reaches a loopback ntfy, and a pathological log line does not stop deep logs.

**Depends on.** R15.

**Files.**

- [ ] Move `qmn/FAILURES.md` to `qmn/src/qmn/observability/FAILURES.md`.
- [ ] Edit `qmn/src/qmn/observability/alerts.py`, `qmn/src/qmn/observability/failures_gate.py`, `qmn/src/qmn/host/qa_debt_matrix.py`, `qmn/src/qmn/seats/containment_limit.py`, `qmn/tests/test_qmn_failures_gate.py` and `qmn/tests/test_qmn_alerts.py`.
- [ ] Edit `qmx-agents/apps/trading-node/app.toml`, by call 11, because `qmn` is in its lock, and `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` for its version row.
- [ ] Edit `qmn/src/qmn/app/alarms.py` and `qmn/src/qmn/app/operations.py`.
- [ ] Edit `tools/tests/test_app_env_data.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/app_logs.py` and `qmx-agents/packages/qmx-host/tests/test_app_logs.py`.
- [ ] Edit `qmx-agents/packages/qmx-engine/src/qmx_engine/telemetry.py` and `qmx-agents/packages/qmx-engine/tests/test_telemetry.py`.

**Build.**

- [ ] Subtract. `p5a-31` sits in `test_app_alarms.py`, which this PR does not need, so R21 takes it. No dead code sits in these files.
- [ ] Safety fact. `uv_build` carries every non-Python file under `src/qmn`, as `openapi-91.pb` shows. With the register inside the package and the two path functions pointed there, the wheel layout loads it and `attach` returns a real `PushSender`. Level 4 on a copied layout (`S/proofs/ground-start/alarm_wheel.py`). The real wheel build is lane 3. Deep logs sit off the trading path, because the exporter has its own thread and timeout, level 2. From `ground-start.md` section 2 these must hold, deep logs never touch trading, and a failed post drops and counts by design. E12 holds, because the engine package changes by one line and it is the exporter, not the workflow core. M3 holds, because no secret path moves.
- [ ] `chief-2`. Move the file, then change `default_failures_path` (`alerts.py:249-251`) and `_failures_root` (`:254`), which climb to `parents[3]`, which is `Lib` in a wheel. Change the text at `qa_debt_matrix.py:607` and whatever `failures_gate.py` and `test_qmn_failures_gate.py` read. Change `containment_limit.py:425`, which reads the old path, and `test_qmn_alerts.py:40,60`, which assert it. Add one read to `NODE_READS` in `test_app_env_data.py`.
- [ ] The class was searched in full. Every `__file__` and `parents[` in `qmn`, `qmb`, `qml`, `qmf-*`, the extensions and the three apps was read, and this is the only one on a running app's path, level 2. Do not widen this PR to the others, which an installed app does not reach.
- [ ] `chief-2`. Put "alarms off" in the node's `status` reasons (`operations.py:846-888`), because silent off is the real failure and stderr reaches nobody. Have `_off` (`alarms.py:708-710`) keep its reason where `status` can read it. Do not split `_off`, because it is one place.
- [ ] `known-10`. In `record_of` (`app_logs.py:97`), also catch `RecursionError` and send the line as text. In `run()` (`app_logs.py:203`), catch `Exception`, because a shipper that ends is worse than one that logs. Today the task ends and the cursor was not saved, so a restart dies on the same line.
- [ ] `known-12`. In `record_of`, move `event` to `message`, and map a short list of supervisor events (`breaker_open`, `restart_refused`, `restart_failed`, `process_error`) to `error`. Keep this inside `record_of`, so the mini-app core is untouched.
- [ ] `triage-9`. At `telemetry.py:458`, move the `json.dumps(...)` line inside the `try`. One non-finite number ends the sender today. `_sent` protects shipped lines, but heartbeats and spans go through the same post.
- [ ] `known-11`, call 16. In `doctor_line` (`app_logs.py:207-221`), the row reads red only when the last post failed, still naming the count of dropped lines. Waiting lines dropped during an outage are the module's stated design, and the local files keep them, so do not change that.
- [ ] `p5a-12`, call 15. No code changes. No keys are passed into a running node, because sending secrets as tool arguments adds a risk for something that happens rarely, and `_rotate` (`connect_node.py:410-415`) already restarts at the next safe moment and says so. C-30's lane 4 pass line changes, as Appendix B records. The no-op re-registration stays unless its test goes with it.

**You see.**

- [ ] Your phone alarms now work on the real installed node. If alarms are ever off, the node's status says so in plain words instead of staying quiet. After an outage of the log server, the health row goes back to green and still tells you how many lines were dropped, and a breaker opening now stands out as an error.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_app_env_data.py` gains the read of the register in `NODE_READS`. In a real wheel env, `load_alert_allow_list()` answers a list, not a refusal. Today it refuses with "no such file". The coordinator runs it, because it builds environments and calls uv.
- [ ] `test_qmn_failures_gate.py` keeps passing at the new path, and it gains `test_the_installed_layout_gives_a_push_sender`, using `alarm_wheel.py`'s copied layout. `attach` returns a `PushSender`, where today it gives `push: None`.
- [ ] `test_app_logs.py` gains `test_a_200000_deep_line_ships_as_text_and_the_next_line_ships`, `test_a_breaker_line_reads_as_an_error`, and `test_outage_then_recovery_leaves_the_doctor_green_with_the_count`. The second asserts `severityText` "ERROR" with body `breaker_open`.
- [ ] `test_telemetry.py` gains `test_a_non_finite_number_is_counted_and_the_sender_lives`. Run `uv run --no-sync python -m pytest tests/test_app_logs.py -q` in `qmx-host` and `tests/test_telemetry.py -q` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qmn/tests/test_qmn_failures_gate.py`, `test_qmn_alerts.py`, `test_qmn_seat_containment_limit.py`, `test_app_alarms.py`, `qmx-agents/packages/qmx-host/tests/test_app_logs.py` and `qmx-agents/packages/qmx-engine/tests/test_telemetry.py`, at the parent and the head. No model. Save `r16-regression.log`. Pass when the head fails nothing the parent passes.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/ground-start/alarm_wheel.py` and `S/proofs/ground-start/logs.py` with `proof_at.sh agents`, at the parent and the head. No model. Save `r16-proofs.log`. Pass when the parent reads refused and `push: None`, "known-10 raised" and severity INFO, and the head reads a real sender, sent as text and ERROR.
- [ ] Lane 3. A real wheel build. Run `tools/tests/test_app_env_data.py` with real uv, then send one real alarm from that env to a loopback ntfy. No model. Save `r16-wheel.log`. Pass when the ntfy server receives the alarm. This is W1.
- [ ] Lane 4. Stop OpenObserve on a throwaway host, ship a pathological line, start OpenObserve again. No model. Save `r16-outage.log`. Pass when the doctor row returns to green with the count named, and a node on the conformance venue placed its trades throughout. This is W2.
- [ ] Lane 5. Break the register on purpose in a throwaway env and read `status`. No model. Save `r16-off.log`. Pass when `status` names "alarms off".
- [ ] Lane 6. Change the ntfy key while a node holds a position, on the conformance venue. No model. Save `r16-keys.log`. Pass when the setup says the new key is read at the next safe restart, and the first alarm after that restart uses it.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r16-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r16-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r16-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r16-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Shipped log lines per second.
- [ ] Probe. A timed `run()` over a 100,000-line file at the parent and the head.
- [ ] Baseline. Record the parent's value first.
- [ ] Rule. No fail rule, recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r16-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Fix promote's edges (R17)

Phase E, records and what reaches him. Source is `A/reports/ground-start.md` blocks G and H. A deploy whose ask times out is told to him as "the node refused", no move is recorded and nothing withdraws it, though the node may have kept it, and a second click makes two deployments. A deploy refused later leaves the unit reading paper with nothing running and no way back. A settings row with a credential and no venue skips the demo check. Done when wall check W7 passes. `p5d-2` waits for G-SERVER.

Rows carried. `p5d-1` `p5d-3` `p5d-6`

Proves. A deploy stalled past 30 s gives one deployment once the node returns, and a click after a refused deploy deploys again.

**Depends on.** R15.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/node_link.py` and `qmx-agents/packages/qmx-host/src/qmx_host/promote.py`.
- [ ] Edit `qmx-agents/packages/qma-harness/src/qma/harness/tools.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/tests/test_node_link_refused.py`, `qmx-agents/packages/qmx-host/tests/test_promote.py` and `qmx-agents/packages/qma-harness/tests/test_demo_only.py`.
- [ ] Create `qmx-agents/packages/qmx-host/tests/test_promote_edges.py`.

**Build.**

- [ ] Subtract. No `test-delete` row sits in these files, and `p5d-9` sits in `test_manifest_host_secrets.py`, which this PR does not touch.
- [ ] Safety fact. Only deploy and withdraw use the outbox, and each carries a stable op id that the node answers with its first answer. Level 4 for the node's memo (`test_a_direct_call_gets_an_op_id_and_a_repeated_op_id_answers_its_first_answer`), level 2 for the two callers (`promote.py:375`, `:448`). From `ground-start.md` section 2 these must hold, a repeated click with the same op id gets the same answer (`test_promote.py`), only `operator` passes promote, `draft` to `paper` is refused, and the lifecycle table stays as it is. M9 holds, because a pin is still rechecked before the app sees the ask.
- [ ] `p5d-1`. Add `tool_timeout` to `WAITING_CODES` (`node_link.py:69`). With it added in memory, the first click gives 200 queued with one move and one deployment. The same click again is accepted and still one. A new click is refused `paper to paper` and still one. Today the second click makes two (`S/proofs/ground-start/proof_waiting.py`, level 4 on the rig's fake node).
- [ ] Trap, from R03. The real supervisor used to stop the app on that timeout, so the retry read `not_running`. R03's `start-n1` makes an opted-in node heal. The retry then lands when the node returns. Test this crossing on a real supervisor, not only on the rig's fake.
- [ ] Trap, on purpose. `test_node_link_refused.py:126` and `test_promote.py:88`, `:563` pin today's wording, so they change with this PR.
- [ ] `p5d-3`. Leave the table alone. In `_admit` (`promote.py:321`), when the market already reads the target and the node says it holds no live deployment for it, deploy again without recording a move, pointing at the existing move. If the node cannot answer, refuse as today. Read the node through its `deployments` row, never the promote answer, because `NodeLink.flush` settles a refused queued deploy silently. That row holds no market (`qmn/src/qmn/app/operations.py:969-975`), and one unit on two markets is normal, with one deployment per market (`promote.py:547`). So map each live row to its market through `self.nodes.outbox.get(deployment_id)`, whose `deployment` names it. A live row of this unit version the outbox does not know counts as live, so no second deployment starts.
- [ ] `p5d-3`, the way back out. `_leave` also withdraws every `deploy` row in `self.nodes.outbox` whose `deployment` names this unit version and this market, through a small `Outbox.deploys(place)` beside `refused_deploys` (`node_link.py:226`), not only those its moves name. The deployment id is the op id (`promote.py:380`), and nothing deletes outbox rows. This reads no node, so a node that is down or slow queues the withdraw as today, and his answer says queued. Do not read the node's `deployments` for this, because that row holds no market, and a match by unit would also withdraw the unit's other markets. A deploy the node never held answers `unknown_deployment`, which `_withdraw` already takes as nothing left to stop. Today it withdraws only what `deployment_of(move)` names (`promote.py:417,433`), and a redeploy with no new move has a new `dep-` id that no move names. Reusing the old id fails too, because the node skips any id it already hosts (`runtime.py:2367`). Without this, he clicks promote after a refusal, it trades, he clicks park, the screen says done, and the node keeps trading. Level 3.
- [ ] `p5d-6`. At `tools.py:1093-1096`, a row naming the wired credential must name its venue. Three lines. Flip `test_a_row_with_no_venue_is_never_checked` (`test_demo_only.py:152`) on purpose. It takes his own hand edit to trigger, so the grade stands, and it is cheap enough to do here.
- [ ] `p5d-2` stays out. `host_route.py:311` wrapping `files_missing` bites at G-SERVER only.

**You see.**

- [ ] If your node is slow to answer when you click promote, the click waits and lands once when the node returns, instead of telling you the node refused while it quietly keeps a copy. If a deploy is refused later, clicking again works, instead of leaving the unit stuck on paper with nothing running.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_promote_edges.py::test_a_timed_out_deploy_waits_and_lands_once`. On a real node behind a real supervisor, a `deploy` stalled past 30 s, then released. It gives one `paper` move and one row in `deployments`, then the same click gives still one, then a new click is refused `paper to paper`. Today two deployments.
- [ ] `test_promote_edges.py::test_a_click_after_a_refused_deploy_deploys_again`. A queued deploy refused by the node leaves `paper` with no live deployment, and a new click deploys with no new move. If the node is down, it refuses as today.
- [ ] `test_promote_edges.py::test_a_park_after_a_redeploy_withdraws_it`. After that redeploy, a park leaves no deployment on this market and unit in the node's `deployments` read, and the same unit's deployment on a second market stays. A park with the node down queues, and lands once the node returns. Today the park reads done and the deployment stays.
- [ ] `test_demo_only.py` flips `test_a_row_with_no_venue_is_never_checked`, so the row is now refused with its reason. Run `uv run --no-sync python -m pytest tests/test_promote_edges.py tests/test_promote.py tests/test_node_link_refused.py -q` in `qmx-host`. The stall test is long, so the coordinator runs it.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qmx-agents/packages/qmx-host/tests/test_promote.py`, `test_node_link.py`, `test_node_link_refused.py`, and `qmx-agents/packages/qma-harness/tests/test_demo_only.py`, at the parent and the head. No model. Save `r17-regression.log`. Pass when the head fails nothing the parent passes, apart from tests named on purpose.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/p5d/proof_orphan.py -k test_timed_out_deploy_is_left_on_the_node` with `proof_at.sh agents`, at the parent and the head, with no patch. No model. Save `r17-orphan.log`. Pass when the parent shows two deployments after a second click and the head shows one.
- [ ] Lane 3. W7 on a real node. Stall the node's `deploy` past 30 s on a throwaway folder and the conformance venue, with the real supervisor healing it. No model. Save `r17-stall.log`. Pass when one deployment exists after it returns.
- [ ] Lane 4. A refused deploy on the same rig, then a new click, then a park. No model. Save `r17-refused.log`. Pass when it deploys, the lifecycle shows one move before the park, and the park leaves no deployment on the node.
- [ ] Lane 5. Rerun `test_a_direct_call_gets_an_op_id_and_a_repeated_op_id_answers_its_first_answer`. No model. Save `r17-memo.log`. Pass when it passes.
- [ ] Lane 6. With a model, ask a copilot chat on `haiku` to use a server row holding the cTrader credential and no venue. Save `r17-mcp.log`. Pass when the chat's note says the row was refused.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r17-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r17-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r17-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r17-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from his click to the answer when the node is well, and when it stalls.
- [ ] Probe. Time the promote route in lanes 3 and 4.
- [ ] Baseline. Record the parent's value first.
- [ ] Rule. No fail rule, recorded for the trail. A stalled click answers queued in about 30 s, the supervisor's limit.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r17-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Make the MIS publish (R18)

Phase E, records and what reaches him. Source is `A/reports/ground-start.md` block E. The MIS starts by itself and does nothing until something calls its `configure` operation, and nothing does. Calling it is not enough, because a round then publishes 0 readings silently, since the MIS looks for bars under the record's venue and the bars live under the source that downloaded them. Done when wall check W6 passes. `p34-4` stays out, and `p34-14` stays until someone decides it.

Rows carried. `p34-2` `p34-3`

Proves. A real download, the configure job and a round give readings, and a read error does not stop the next round.

**Depends on.** R17.

**Files.**

- [ ] Create `qmx-agents/packages/qmx-host/src/qmx_host/mis_configure.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/host.py`.
- [ ] Edit `qmx-agents/apps/mis/server.py`, `qmx-agents/apps/mis/mis_core.py`, `qmx-agents/apps/mis/app.toml` and `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py`.
- [ ] Edit `qmx-agents/apps/mis/tests/mis_app_test.py`.
- [ ] Create `qmx-agents/packages/qmx-host/tests/test_mis_configure.py`.

**Build.**

- [ ] Subtract. No `test-delete` row and no dead code sit in these files.
- [ ] Safety fact. The MIS is not on the order path, so wrong or empty configuration costs only readings. Level 2, with the invariant in MIS.md and `p34`'s "units stand alone" check. From `ground-start.md` section 2 this must hold, a unit trades with the MIS stopped. M2 must hold, because the bump keeps the MIS's volume. The relay reads the board file and falls back safely, and the market board stays unwired, by TR:49.
- [ ] `p34-2`. Add one small host job in `mis_configure.py`, beside `VenueRecords.round` (`venue_records.py:412`), This PC only. For each `instrument` on Library main, find which source in the store holds `bar-m1` for its symbol, through the door's `instruments()`, and call `configure` with `source` naming it. Use an op id that is the fingerprint of that list, so repeats do nothing. That meets MIS.md's "This PC configures its own instance". Wire it in `host.py` next to where `venue_records` starts (`host.py:1129`), and run it after the app starts and on the same cadence.
- [ ] Trap. `mis_core.py:573` defaults `source` to the record's venue, and `MarketData._keys` looks in `<source>/<symbol>/bar-m1`. Given the record C-34 really lands, configure accepts it and a round publishes 0 readings, silently. With `source` naming where the bars are, it publishes 4 (`S/proofs/ground-start/mis_real.py`, level 4).
- [ ] A market with no bars is named in `status`, not silently empty. Add it to `mis_core.py`'s status answer. Before his demo sign-in and with no download there is nothing to configure from, and that is a plain line, not a fault.
- [ ] `p34-3`. Give `rounds()` (`apps/mis/server.py:64`) a guard, and record its last error in `status`. Today one read error kills the round thread for good, while the app stays up and the breaker never restarts it (`S/proofs/p34/p2_rounds_thread.py`).
- [ ] Leave `p34-4` out. The missing readings are block work, and some of what they need sits in the never-run regime code. Do not delete `p34-14`.
- [ ] Note. The node's own `journal-market` bar rows do not become `bar-m1` partitions, because no product code calls `append_series`. So the MIS on a node machine finds nothing. That is `start-n2`, and it is settled with the bars repair after G-DEMO.

**You see.**

- [ ] The MIS now does its job by itself. After a download it reads your markets and publishes readings, and the copilot's MIS answers and the five templates that read them stop coming back empty. If one read fails, the next round carries on. If a market has no data, the status says which one.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_mis_configure.py::test_a_market_with_bars_under_a_source_is_configured_and_publishes`. A real store with `dukascopy/EURUSD/bar-m1/bid` from R09, a real `instrument` item, and the real MIS core. `configure` names `source` `dukascopy`, and a round publishes 4 readings. Today 0.
- [ ] `test_mis_configure.py::test_running_twice_does_nothing_and_a_market_with_no_bars_is_named`. The second run has the same op id and answers its first answer. `status` lists the bare market by id.
- [ ] `mis_app_test.py` gains `test_a_read_error_in_a_round_leaves_the_thread_alive`. One raising read, then the next round publishes, and `status` holds the last error. Run `uv run --no-sync python -m pytest tests/test_mis_configure.py -q` in `qmx-host`. The coordinator runs the app test.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qmx-agents/apps/mis/tests/`, in the host `test_first_party_node.py`, and in the engine the five MIS-reading templates' tests, at the parent and the head. No model. Save `r18-regression.log`. Pass when the head fails nothing the parent passes.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/ground-start/mis_real.py <folder>` and `S/proofs/p34/p2_rounds_thread.py <folder>` with `proof_at.sh agents`, at the parent and the head. No model. Save `r18-proofs.log`. Pass when the parent gives 0 readings with the record's venue and a dead thread, and the head gives 4 and a live thread.
- [ ] Lane 3. W6 on a real host. A real download on a scratch home, the job runs, `readings_query` answers. No model. Save `r18-real.log`. Pass when the answer holds readings for that market. If the network is down, use R09's saved month through the door, and say so.
- [ ] Lane 4. On that host, stop the MIS and let a unit on the conformance venue enter. No model. Save `r18-stopped.log`. Pass when the unit enters.
- [ ] Lane 5. With a model, ask a copilot chat on `haiku` what the MIS reads on EURUSD. Save `r18-copilot.log`. Pass when the chat calls `readings_query` and quotes a reading.
- [ ] Lane 6. Run `s3-mis-check` on that host. No model beyond what its writer step uses on `haiku`. Save `r18-s3.log`. Pass when it reads a market by name.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r18-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r18-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r18-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r18-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds of one MIS round per market.
- [ ] Probe. The round's own log line in lane 3.
- [ ] Baseline. None, first measure, because a round does nothing today.
- [ ] Rule. No fail rule, recorded for the trail. The `round_s` setting is what bounds it.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r18-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Make recording hold up over months (R19)

Phase E, records and what reaches him. Source is `A/reports/ground-start.md` block F. The minute job re-reads a stream's whole history for one new row, about 30 to 39 s and 3.3 GB each minute at 1,000,000 rows. Trades from a server node never become Library items. Nothing writes the market journal's minute row, so "why didn't it trade at 08:00" never gets the spread. Done when the second half of wall check W4 passes and a million-row round is cheap. This ends phase E, so a whole-repo run follows it.

Rows carried. `p34-8` `p34-6` `p34-5` `plan-check-3` `p0b-24`

Proves. A second records round scores exactly as the first, with projection reading the store, and a million-row stream rounds without re-reading it.

**Depends on.** R18.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/records.py`.
- [ ] Edit `packages/qmf-data/src/qmf/data/journal_reader.py` and `packages/qmf-data/tests/test_journal_partition.py`.
- [ ] Edit `qmn/src/qmn/app/feed_keeper.py` and `qmn/tests/test_app_feed_keeper.py`.
- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/journals.py` and `qmx-agents/packages/qmx-tools/tests/test_journal_seal.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/tests/test_records.py` and `qmx-agents/packages/qmx-host/tests/test_harvest.py`.
- [ ] Edit `qmx-agents/apps/trading-node/app.toml`, by call 11, because `qmf-data` and `qmn` are in its lock, and `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` for its version row.

**Build.**

- [ ] Subtract. Delete `p0b-24` (`test_journal_partition.py:76`), which restates two constants.
- [ ] Trap, the one that shapes this PR. `Projection._paper` (`records.py:736-741`, `:769-773`) scores only the rows it is handed and overwrites the score when it differs. Today it is handed the whole history, so it is right. Any repair that hands it fewer rows silently rewrites a paper score with fewer trades. `p34-6` and `p34-8` both walk into this if done separately, so do them as one. Level 2, by reading.
- [ ] Safety fact. Rotation files are 8 MB, and the writer only appends to the last (`jsonl.py:53`, `:264`), so older rotation files never change. Level 2, unproven by running, so the proof is the million-row run after this PR and a test that a second round scores the same as the first. From `ground-start.md` section 2 these must hold, a write to a live stream fsyncs first, one writer per stream, and readers never change the files. No promise in `ground-core.md` section 2 is in reach. Trading never waits on this job.
- [ ] `p34-6`. Make `Projection` read `trade` and `lifecycle` partitions from the market store, not from stream lines. The store holds local and pulled rows alike and every month. A committed key names the lanes it touches, and each lane is scored from every month of its series in the store. Reading only the committed keys would rewrite a score, because a closed month is never committed again, so a lane older than a month would be scored from the open month alone. Round 1 commits `2026-09` and `2026-11` for 3 trades, round 2 commits `2026-11` only with four trades in all, and that form reads `(2, '2.0')` (`S/proofs/plan-review-b/test_r19_months.py`, level 4). A key whose projection failed is told again at the next round, because a frozen month is committed only once. Today `Records.round:1376` projects only harvester lines, and `Pull` commits to the door and returns counts. Trades from a server then project too.
- [ ] `p34-8`. Then only the harvester needs bounding. A stream remembers the first rotation file holding an unfrozen month and reads from there, in `read_committed` (`journal_reader.py:60`) and `Harvester.round` (`records.py:399`). The open month is still rewritten whole, as the design says.
- [ ] `p34-5` and `plan-check-3`, the journal side only. `minute` is registered and nothing writes it. Write it in `Recording`, with `FeedKeeper.pump` (`feed_keeper.py`), which see every quote and hold the market writer. A row holds the market id and the minute's spread at close.
- [ ] Trap. `journals.py:279` matches a minute by the row's write time, so a row written at the close of 08:00 reads as 08:01. Write it so the two agree, and test the 08:00 case by literal. Fees and slippage stay out, because they belong with the cost work after G-DEMO.
- [ ] `p34-7` and the pull trigger wait for G-SERVER. Do not start them here.

**You see.**

- [ ] The records job stays quick after months of trading, instead of slowing down and eating memory every minute. Ask the copilot "why didn't it trade at 08:00?" and the answer now shows the spread at that minute, not only the reason.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_records.py` gains `test_a_second_and_third_round_score_the_same_paper_run`. Foundation of W4. A real writer's trades that span a month end, three rounds, one `paper-run` with the same trade count and score, so the second round commits only the new month and still counts the closed month's trades. This is the guard against the trap, so it must fail against a naive bounded harvester, and the builder shows that in `owner-red.log`.
- [ ] `test_records.py` gains `test_a_pulled_trade_lands_a_library_item`. A trade committed through `Pull` from a server-shaped folder gives one `trade` and one `paper-run`. Today 0.
- [ ] `test_harvest.py` gains `test_a_round_reads_only_from_the_unfrozen_file`. Over a stream of frozen months, with a counting reader, the round opens only the last rotation file.
- [ ] `test_app_feed_keeper.py` gains `test_a_minute_row_holds_the_spread_at_its_close`, and `qmx-tools` gains in `tests/test_journal_seal.py` `test_the_0800_question_reads_the_0800_minute`, the literal spread at 08:00 and not 08:01. Run `uv run --no-sync python -m pytest tests/test_records.py tests/test_harvest.py -q` in `qmx-host`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qmx-agents/packages/qmx-host/tests/test_records.py`, `test_harvest.py`, `packages/qmf-data/tests`, `qmn/tests/test_app_feed_keeper.py`, and `qmx-agents/packages/qmx-tools/tests`, at the parent and the head. No model. Save `r19-regression.log`. Pass when the head fails nothing the parent passes.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/p34/p4_harvest_cost.py <folder> 1000000`, the command in `reports/p34.md`, at the parent and the head under a 25-minute limit. No model. Save `r19-harvest.log`. Pass when the parent gives about 30 to 39 s and 3.3 GB per round for one new row, and the head gives under 2 s and under 200 MB.
- [ ] Lane 3. A real node trade travels writer, harvester and Library, with a second and third round. No model. Save `r19-w4.log`. Pass when one `trade` and one `paper-run` land, unchanged by the later rounds. This is W4.
- [ ] Lane 4. Whole-repo run at this phase end, with `S/tools/run_tests.sh`. No model. Save `r19-whole.log`. Pass when it fails nothing R18's tip passed.
- [ ] Lane 5. With a model, ask a copilot chat on `haiku` "why didn't the dummy trade at 08:00 on that day?" on a store with node rows. Save `r19-copilot.log`. Pass when the answer quotes the spread at 08:00.
- [ ] Lane 6. Restart the host mid-round on a throwaway folder. This lane is in this PR's proving set, so the coordinator runs it with lanes 1 to 4, and it uses no menu choice. No model. Save `r19-restart.log`. Pass when the next round lands every row once, and a key whose projection the restart cut is told again.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r19-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r19-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r19-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r19-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds and memory of one records round for one new row at 1,000,000 rows, and microseconds per quote in `FeedKeeper.pump`.
- [ ] Probe. Lane 2, and a timed pump over a day of quotes, at the parent and the head.
- [ ] Baseline. 424 s and 3.4 GB on the first round, then 30 to 39 s and about 3.3 GB per round (`A/SPOT-CHECKS.md`).
- [ ] Rule. Fails above 2 s or 200 MB for the later rounds. Fails if `pump` is more than 5% slower, because it is on the feed path.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r19-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Let the broker win (R20)

Phase F, the node. Source is `A/reports/ground-node.md` Cause A and "The fakes". The node trusts its own memory where it should ask the broker. `_reconciled` (`ctrader_account.py:689-690`) returns its own memory for any position it already holds and ignores the broker's row, so a reconcile can never see a stop that fired, moved or was removed, or a size that changed. The missing-position case is only the loudest. And the fakes never made it pay for that. Done when wall check W8 and the closed half of W9 pass on a harsher fake.

Rows carried. `p5a-2` `node-n2` `node-n3` `node-n4` `p5a-9`

Proves. Drop the socket, fire the stop, reconnect, and the trade books at the broker's price with nothing phantom.

**Depends on.** R19.

**Files.**

- [ ] Edit `qmn/src/qmn/venue/ctrader_account.py`.
- [ ] Edit `qmn/src/qmn/app/reconciler.py` and `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmn/tests/test_app_binding.py`, for the fake.
- [ ] Edit `qmx-agents/apps/trading-node/app.toml`, by call 11, because `qmn` is in its lock, and `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` for its version row.
- [ ] Create `qmn/tests/test_app_broker_wins.py`.

**Build.**

- [ ] Subtract. No `test-delete` row sits in these files.
- [ ] Safety fact. Broker-wins `read_back` breaks no shipped test and heals the rest. Level 4 with `S/proofs/ground-node/venuewins.py` patched in, `test_app_binding.py` 17 passed, `test_app_reconcile_filled.py` and `test_app_partial_fill.py` 11 passed, and `test_app_runtime.py` with `test_app_unknown_drill.py` 11 passed (`A/reports/ground-long.md`). That run holds for `read_back` only. `venuewins.py` never asks for history, because it books every missing position at the held stop, so nothing has run the history path or `node-n4`. `read_back` is called only by `Reconciler.run`, and `closed()` drives `NodeUnit.protective`, `venue_open`, `_orphans` and the kill, so one truthful `_closed` entry heals all of them. From `ground-node.md` section 2 all must hold, every order carries its stop at the broker, journal before send, one send per client order id, partial fills book the broker's size, and positions without his node's tag are never touched. M5 and M6 are not touched. Rerun `parity.py` after this change, because no repo test holds it.
- [ ] `p5a-2`, `node-n2`. In `CTraderVenue.read_back` (`ctrader_account.py:665`), for each held position take stop and volume from the broker's row, as `venuewins.py`'s `truthful` does. Today the broker's stop 1.07522 and half the size read as the node's stop 1.08022 and full size, and the `reconcile` row writes the node's memory under `venue_stop` (`truth.py f1`, level 4).
- [ ] Known limit. Volume from the broker's row changes `_open`, not the handler's `OwnPosition.quantity`. After a part close by hand, close orders are right, and the trade row still books full size. Write one line in `S/BACKLOG.md`, because the Library's money field stays wrong in that case until a later PR feeds the handler.
- [ ] `p5a-2`. For each held position the broker no longer lists, ask `ProtoOADealListByPositionIdReq` for the closing deal, which is in the pinned definitions, then fill `_closed` with its price and kind. `ProtoOADeal` has no kind field, only `orderId` (`S/proofs/plan-review-b/p3_defs.py`, level 4), so the kind comes from a join to `ProtoOAOrderListByPositionIdReq`.
- [ ] Trap. The deal-history fields for a stop can be read only on demo, by C-15. So if history gives nothing, ask reconcile once more first, because a missing report is not flat (`catalogue.md:628`). If the position is still not listed, close it at the held stop and raise an alarm that says the price is a guess. A later listing clears `_closed` with an alarm, because today `_reconciled` refills `_open` while `_closed[name]` stays, so `closed()` keeps answering and R21's kill skips it (`runtime.py:2130`). Never leave a position held because history was silent.
- [ ] `node-n3`. In `_execution` (`ctrader_account.py:1095-1101`), read `stopLoss` on every non-closing event. An absent `stopLoss` on an event keeps the held stop, as `_amend` does (`ctrader_account.py:1348`), and only a reconcile row may clear it. Today a stop he moves by hand while connected is never read, because the code updates only volume (`truth3.py h2`, level 4).
- [ ] `node-n4`, which send counts. For the process-down case, the reconciler (`reconciler.py`) compares the journal's sends with the broker's list. A send counts only if it is `kind` entry, in this account's demo world, has a `filled` row or a resolved unknown, and its unit journal has no `trade` row for that position. Today a stop fired while the process was down leaves an entry with no exit and no alarm, and status reads Ready (`truth2.py g3`, level 4). A plain "sends without an exit" is wrong, because only `OrderPath._close` writes a `closed` row (`runtime.py:1204`), so every past stop-out would read as no exit. `journal_sends` also returns every `node` folder's sends, paper too, with no world or account in the body (`reconciler.py:87-104`).
- [ ] `node-n4`, who writes the close. The close goes through the hosted unit, which adopts the position with `_closed` set, so the handler writes the trade, and then the alarm is raised. `NodeUnit.adopt` skips a name the venue reads closed today (`runtime.py:1448`), so that skip changes. With no hosted unit, it raises the alarm only, because the reconciler holds only the node journal and a unit journal has one writer.
- [ ] `node-n4`, finding the closing deal. Journal `positionId` in the `filled` note from this PR on (`runtime.py:1065-1068`), because no journal row holds a position id today. With no id, use `ProtoOADealListReq` over the send's time window, or the guess alarm.
- [ ] `node-n4`, the guard. Two old stop-outs and one paper send, then a restart, give no alarm and no new row. Without the three boxes above, each old trade raises an alarm and a phantom close at every restart, and the paper score doubles. `test_old_stop_outs_and_a_paper_send_stay_quiet_at_a_restart` holds this.
- [ ] `p5a-9`. `_position_row` (`reconciler.py:441`) skips a send with no stop. Today the self-test's stuck trade raises `KeyError` on every pass, the node heals in a loop, stands down after 5, and no unit is driven.
- [ ] Make the fake cTrader harsher, about 80 lines added to its 470, all opt-in flags, so they turn nothing red by themselves. Add lost events while down, which the scripts do now by clearing `_out`. Add a socket refused N times (`Flaky`, from `truth3.py`). Add answers for deal history and trendbars, holding only the pinned fields, so a test is not kinder than the wire. Add the stop on a later event, not the fill (`StopLater`, from `truth3.py`). Add a close answered by `ProtoOAErrorRes`. A symbol the account does not list already exists as `SYMBOLS`.
- [ ] Trap. With the stop on a later event, the node waits 2 s, sends one amend and ends protected with no alarm (`truth3.py h1`). That spends one amend per entry, and only C-15's demo says whether a real fill carries the stop. Do not change it here.

**You see.**

- [ ] If your connection drops and the broker's stop fires while you are away, the node now learns the truth when it reconnects. It books the trade at the broker's price, stops holding a position that no longer exists, and the unit can trade again. A stop you move by hand in cTrader now shows up on the node, and a stop that fired while the node was off now leaves a record and an alarm.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_app_broker_wins.py::test_a_stop_fired_while_down_books_at_the_brokers_price`. W8. On the harsher fake, drop the socket, fire the stop, reconnect. `closed` reads STOP, trade rows 1, safe to restart true, entries after 2. Today closed None, trade rows 0, entries after 0 (`truth2.py g2`).
- [ ] `test_app_broker_wins.py::test_the_reconcile_row_writes_the_brokers_stop_and_size`. With the broker at 1.07522 and half the size, the node's position and the row's `venue_stop` both read 1.07522 (`truth.py f1`).
- [ ] `test_app_broker_wins.py::test_a_stop_moved_by_hand_is_read` and `::test_a_stop_fired_while_the_process_was_down_writes_the_missing_close`. W9's closed half. Each asserts the journal row and the alarm by literal.
- [ ] `test_app_broker_wins.py::test_old_stop_outs_and_a_paper_send_stay_quiet_at_a_restart`. Two old stop-outs and one paper send, then a restart. No alarm and no new row. As first written, an alarm and a phantom close for each old trade.
- [ ] `test_app_broker_wins.py::test_history_silent_closes_at_the_held_stop_with_a_guess_alarm`, after one more reconcile, and `::test_a_send_with_no_stop_is_skipped_not_a_keyerror`. No existing test needs to change, as `venuewins.py` showed. Run `uv run --no-sync python -m pytest qmn/tests/test_app_broker_wins.py qmn/tests/test_app_binding.py -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qmn/tests/test_app_binding.py`, `test_app_reconcile_filled.py`, `test_app_partial_fill.py`, `test_app_unknown_drill.py`, `test_app_attribution.py`, `test_protection_every_order.py` and `test_app_runtime.py`, at the parent and the head. No model. Save `r20-regression.log`. Pass when the head fails nothing the parent passes.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/ground-node/truth2.py g2 g3`, `truth.py` and `truth3.py` with `proof_at.sh root`, at the parent and the head. No model. Save `r20-truth.log`. Pass when the parent prints closed None and rows 0, and the head prints closed STOP and rows 1, with no in-memory patch.
- [ ] Lane 3. Run `S/proofs/seams/parity.py 9 <folder>` at the head. No model. Save `r20-parity.log`. Pass when it reads 63 of 63.
- [ ] Lane 4. Whole-repo run, because R20 is the twentieth PR. Use `S/tools/run_tests.sh`. No model. Save `r20-whole.log`. Pass when it fails nothing R19's tip passed.
- [ ] Lane 5. A kill after a stop fired while down, on the harsher fake. No model. Save `r20-kill.log`. Pass when no close is refused 5 times a second, withdraw ends, and safe to restart reads true.
- [ ] Lane 6. The self-test's stuck trade. No answer to the close for 5 s, then ten reconcile passes. No model. Save `r20-stuck.log`. Pass when no pass raises and the unit is still driven.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r20-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r20-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r20-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r20-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds of one reconcile with 10 held positions on the fake.
- [ ] Probe. A timed `Reconciler.run` at the parent and the head, interleaved.
- [ ] Baseline. Record the parent's value first.
- [ ] Rule. No fail rule, recorded for the trail. Only a position the broker no longer lists costs a history request, and history is limited to 5 a second.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r20-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Make every way out act (R21)

Phase F, the node. Source is `A/reports/ground-node.md` Cause B and "Kill effects", with `A/reports/ground-unit.md` block B for the stop sign. There are three separate closers and none is complete. RED does not close a position no hosted unit holds, flatten answers "accepted" and does nothing, a refused unit exit is thrown away for good, and a restart adopts a position with no stop as if it had one. Nothing new is needed but joining what exists. Done when wall checks W9 and W10 pass on the harsher conformance venue.

Rows carried. `p5a-3` `p5a-4` `p5a-6` `p5a-7` `p5a-21` `p5a-23` `p5a-29` `p5a-30` `p5a-31` `p5a-32` `p5a-33` `p5a-34` `known-3`

Rows in part. `known-1` by its false report and its silent loss, and the signed stop distance goes to the risk session. `p5b-3` by the close's reference price at the runtime's lines, and Hyperliquid's real refusal still needs testnet.

Proves. RED and flatten leave the broker flat with true rows, a refused exit keeps going, and a restart replays nothing.

**Depends on.** R20.

**Files.**

- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmn/src/qmn/app/operations.py`.
- [ ] Edit `qmn/src/qmn/app/stand_down.py`.
- [ ] Edit `qmn/tests/test_app_operations.py`, `qmn/tests/test_protection_every_order.py`, `qmn/tests/test_app_alarms.py`, `qmn/tests/test_app_stand_down.py` and `qmn/tests/test_app_status_truth.py`.
- [ ] Edit `qmx-agents/apps/trading-node/tests/trading_node_app_test.py` and `qmx-agents/apps/trading-node/app.toml`, then `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` for the version row.
- [ ] Create `qmn/tests/test_app_every_way_out.py`.

**Build.**

- [ ] Subtract. Delete `p5a-23`, the code at `stand_down.py:292` and its 64-line test, which read journal rows "written before C-13", though no node has ever run and no such row exists. Delete `p5a-29` (`test_app_operations.py:60`), `p5a-30` (`test_protection_every_order.py:305`), `p5a-31` (`test_app_alarms.py:166`), `p5a-32` (`test_app_stand_down.py:437`), `p5a-33` (`test_app_status_truth.py:32`), `p5a-34` (`trading_node_app_test.py:257`) and `known-3`, the one assert at `test_protection_every_order.py:250` that restates its own parameter.
- [ ] Safety fact. `OrderPath.close` reaches an orphan on the real binding, because `_reconciled` filled `_open`. With the sketch, RED leaves the broker empty and the kill row reads 1, where today it stays open and reads 0 (`S/proofs/ground-node/truth4.py`, level 4). Adding a refused exit to the existing retry set books the trade, 2 closes, flat, 3 trades, where today it is 1 close, 0.75 still open, 2 trades (`truth4.py`). `amend` puts a missing stop back on an adopted position at the journal's level (`truth2.py g5`). With the sketches and the harsher venue, `test_protection_every_order.py` and `test_app_status_truth.py` passed 26 of 26, `test_app_kill_scopes.py` 17, and `test_app_runtime.py` with `test_app_unknown_drill.py` 11 (`ground-long.md`). From `ground-node.md` section 2 all must hold, and a kill repair must close only `Claim.MINE`. Kill stays escalate-only, and his resume brings it down.
- [ ] Add one method on `Runtime` that closes every `Claim.MINE` position in a scope, hosted or not, through `OrderPath.close`. It joins `unit.venue_open()` and the orphans, because `reconciler.mine` is a snapshot from the last run, so `S/proofs/ground-node/reach.py`'s form misses positions opened since, and paper positions. A hosted position takes the same `covers` test `_enact` already uses for a scope. An orphan has no unit for `instrument_scopes`, so its scope test is `same_market` (`operations.py:337`). Nothing new is needed but joining. `_protect` (`runtime.py:2255`) already closes on every tick until the broker shows closed, `close` already counts refusals and raises the alarm at the third, and `_orphans` already names the unhosted positions.
- [ ] `p5a-4`, call 13. `_enact` (`runtime.py:2231-2235`) walks hosted units only. Have kill call the new method each tick while the level holds. A kill closes every position carrying this node's tag at the scope, hosted or not. The positions it closes are the `positions_closed` count, which is written once, at the rising tick (`runtime.py:2185-2190`). So the count is true only when the first close succeeds. A RED pressed with the session down, or held across a restart before the first reconcile, reads 0 and then closes, and there the close rows and the broker are the truth. What each kill level means stays the risk session's placeholder, so do not edit `PLACEHOLDER_KILL_EFFECTS`.
- [ ] `p5a-6`, call 13. `_apply_flatten` (`operations.py:549`) returns a constant, and `Target.fold` (`operations.py:384`) has no flatten branch. Add the branch, so the target holds each accepted flatten by op id and scope. An operation never touches the broker, so the op still answers at once with `{"state": "accepted", "positions": <count>}`, the count of this node's positions at that scope in its last view, 0 on an empty node. Each tick, the runtime calls the new method for each flatten op not yet journalled done. When the scope reads flat, it writes the op's done row with the count it closed. The done row is a `kill_level` row, the kind that exists, with `op_id`, `scope`, `positions_closed` and no `level`, so it reads as neither a kill nor a clear. Read those rows at start with the shape of `journalled_resumes` (`runtime.py:1821`), so a restart never replays an old flatten on new positions. Do not copy its failure rule, where a refused folder reads as holding none (`:1823`), because for a flatten that replays old ops on new positions. A refused read holds the op and does not act on it.
- [ ] `p5a-6`. Flatten closes positions and does not stop the unit, so a unit may enter again on its next signal, and RED is how he gets out and stays out.
- [ ] Trap, on purpose. `trading_node_app_test.py:258-260` pins flatten's empty answer, so that line must change, and `p5a-34` deletes the rest of that test. Editing this folder bumps the money app's version, so M5 means a real folder waits for his signature, which is right.
- [ ] `p5a-3`. `execute_resting` (`runtime.py:1521-1530`) marks a refused exit done. Add a refused unit exit to the existing retry set, a full close only, never `ClosePartial` or `AmendProtection`, so it keeps going until the broker shows it closed. Those two also answer `Blocked` through the same branch, including this PR's new past-entry `Blocked`, and in the retry set a refused stop move would close the whole position. The sketch excludes both (`reach.py:43`).
- [ ] `p5a-7`. `NodeUnit.adopt` (`runtime.py:1461-1464`) feeds the journal's stop to the handler and sends nothing to the broker. Each tick after `adopt`, walk `unit.venue_open()`, and every position in it whose stop reads None goes through the `_protected` steps, which put it back and then close it and raise the alarm. Walk that list, because `stop_of` also reads None for a position that has left `_open` (`ctrader_account.py:654`), and walk it each tick, because `adopt` runs each tick from a snapshot and compile runs in a thread, so a restart's reconcile can come before the unit is hosted (`runtime.py:2117`, `:2379`). This is not only at adoption, because `adopt` skips any name already in `placed` (`runtime.py:1447`), and R20 now shows a stop lost during a dropped connection as `held.stop = None` in the same process.
- [ ] Trap. If the price is already past the stop, cTrader refuses it, and the fake reads `TRADING_BAD_STOPS`. So the shape must fall through to a close and an alarm, as `_protected` does for a new entry. This runs before any entry on that position's unit.
- [ ] `known-1`, the false report. `amend` returns `Placed(new_stop)` at `runtime.py:1253`, whatever was sent. Return the broker's stop, read from the venue's held position, which R20 made true, and raise an alarm if they differ after rounding to the symbol's digits, so a trail on an unrounded indicator value does not alarm each time. The handler keeps the asked stop whatever `Placed` says (`unit_handler.py:605-607`). Today `positions` shows the broker's truth, 1.06916, while the `Placed` answer, the handler and the journal row hold 1.06800 (`truth2.py g8`).
- [ ] `known-1`, the silence. A stop past entry is sent as an unsigned distance (`abs(entry - new_stop)`, `runtime.py:1223`), so it lands on the wrong side, and a stop far past entry is refused as "widens" and lost with no row or alarm. When the new stop is past entry, `amend` answers `Blocked` with that reason and writes its row, instead of sending a level nobody asked for. Add the text to `_REASON_WORDS` with the code `stop_wrong_side`, which `REASON_CODES` already holds, because R15's census fails otherwise. The signed distance stays the risk session's, by ruling, and no shipped unit can reach this today. Rerun `pytest qmn/tests -k amend`, which is 13 passed at the audit head, and name any that moves.
- [ ] `p5b-3`. `Runtime` passes the current quote as the close's reference. It is harmless on cTrader, and it clears the close limit set from entry at the same lines.
- [ ] `p5a-21`. Make the conformance venue answer as the real binding does when the session is down, in `OrderPath._send` for `ConformanceAccount`, four lines as `S/proofs/ground-node/harsh.py` does. `test_app_stand_down.py:245`, the `venue_not_ready` case, goes red, which is exactly the false green. Change it on purpose to say the exit goes once the session is back. `test_app_healing.py` stays 0 red of 16. `ConformanceAccount` stays where it is (`p5a-26`).
- [ ] Trap. A kill's repeated closes do not flood the journal, 25 ticks wrote 1 row, but the broker does see 5 requests a second per position (`truth.py`). Leave that rate as it is. R23's back-off is about sign-ins, not this.

**You see.**

- [ ] When you press RED, every position this node opened at that scope closes, even one no running unit holds, and the kill's report counts what closed on the first try. If the connection is down when you press it, the report reads 0, and the positions close when the connection is back. When you press flatten, the positions really close. A unit may then enter again on its next signal, so RED is how you get out and stay out.
- [ ] A close the broker refuses keeps trying and raises an alarm instead of being forgotten. After a restart or a reconnect, a position with no stop gets its stop back, or it is closed with an alarm, before anything else happens.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_app_every_way_out.py::test_red_closes_a_position_no_unit_holds`. W10. On the fake cTrader with the deployment refused at restart, as `orphan` in `truth4.py` sets it up, RED leaves `fake.held` empty and the kill row reads 1. Today it stays open and reads 0.
- [ ] `test_app_every_way_out.py::test_flatten_closes_and_a_restart_replays_nothing`. W10. With a unit trading, flatten leaves the broker flat with the op's row, and a restart with new positions closes none of them. Today it answers "accepted, positions 0" and every position stays open.
- [ ] `test_app_every_way_out.py::test_a_refused_exit_keeps_going_and_books_the_trade`. 2 closes, flat, 3 trades (`truth4.py`). Also `::test_a_blocked_stop_move_leaves_the_position_open`, where a refused stop move keeps the position and its row.
- [ ] `test_app_every_way_out.py::test_a_restart_puts_a_missing_stop_back_before_any_entry` and `::test_a_stop_it_cannot_put_back_closes_with_an_alarm`. W9. The second uses `TRADING_BAD_STOPS`. Also `::test_a_stop_lost_across_a_reconnect_is_put_back`, in one process with no restart.
- [ ] `test_app_every_way_out.py::test_amend_answers_the_brokers_stop_and_a_past_entry_stop_is_blocked_with_its_row`. Asserts 1.06916 in the answer, as `truth2.py g8` sets it up, and `Blocked` with a journal row at 1.1020 on a long from 1.1000. Today the venue is sent 1.09800.
- [ ] Tests that change on purpose are `test_app_stand_down.py:245` and `trading_node_app_test.py:258-260`. Run `uv run --no-sync python -m pytest qmn/tests/test_app_every_way_out.py qmn/tests/test_app_stand_down.py -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qmn/tests/test_app_runtime.py`, `test_app_unknown_drill.py`, `test_app_kill_scopes.py`, `test_protection_every_order.py`, `test_app_status_truth.py`, `test_app_healing.py`, `test_app_stand_down.py`, `test_app_broker_wins.py`, and `qmx-agents/apps/trading-node/tests/`, at the parent and the head. No model. Save `r21-regression.log`. Pass when the head fails nothing the parent passes, apart from tests named on purpose.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/ground-node/truth4.py` with `proof_at.sh root`, at the parent and the head, reading its "today" lines. No model. Save `r21-truth4.log`. Pass when the parent prints 1 close with 0.75 open and a kill row of 0, and the head prints 2 closes, flat, and a kill row of 1, with no sketch applied.
- [ ] Lane 3. Rerun `qmn/tests -k amend`. No model. Save `r21-amend.log`. Pass when each of the 13 passes or is named in the PR body with its reason.
- [ ] Lane 4. Run `S/proofs/seams/parity.py 9 <folder>`. No model. Save `r21-parity.log`. Pass when it reads 63 of 63.
- [ ] Lane 5. A hand-opened position with no tag on the fake, then RED and flatten. No model. Save `r21-manual.log`. Pass when it stays open, untouched, and no alarm blames it.
- [ ] Lane 6. Flatten with the session down on the harsher venue. No model. Save `r21-down.log`. Pass when the op stays not done, retries once the session is back, and ends flat.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r21-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r21-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r21-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r21-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds per runtime tick with 10 positions under a kill.
- [ ] Probe. A timed tick loop at the parent and the head, interleaved.
- [ ] Baseline. Record the parent's value first. A tick is every 200 ms.
- [ ] Rule. Fails if a tick passes 100 ms on the fake, because a kill runs each tick while the level holds.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r21-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Make what he deployed run (R22)

Phase F, the node. Source is `A/reports/ground-node.md` Cause C, Cause D step 1 and its new defect N1. `_host` assumes the world is ready when the compile ends. A unit promoted on any market but EURUSD never gets a bar, a restart with no network starts a unit at equity 0 for life, a deploy before bind waits for ever, and one symbol the broker does not list kills the whole account after a restart. Done when wall check W11 and the refusal half of W12 pass.

Rows carried. `node-n1` `p5a-1` `seams-4` `p5a-5` `seams-6` `p5a-8` `p5a-20` `p5a-15` `seams-11` `p5b-11` `p5b-12`

Rows in part. `seams-5` and `p5a-18` by refusal, and the bars he tested on come after G-DEMO. `p5b-6` by the same one-rule refusal on a Hyperliquid coin.

Proves. A reboot with no network waits and then trades at the real balance, a new market gets its bars with a position held, and an unlisted symbol is refused by name while the account keeps trading.

**Depends on.** R21.

**Files.**

- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmn/src/qmn/app/server.py`.
- [ ] Edit `qmn/src/qmn/venue/ctrader_account.py`.
- [ ] Edit `qmn/tests/test_qmn_venue_selection.py` and `qmn/tests/test_ccxt_client.py`.
- [ ] Edit `qmx-agents/apps/trading-node/app.toml`, by call 11, because `qmn` is in its lock, and `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` for its version row.
- [ ] Create `qmn/tests/test_app_deployed_runs.py`.

**Build.**

- [ ] Subtract. Delete `p5b-11` (`test_qmn_venue_selection.py:80`), which only restates the list of venue kinds, and `p5b-12` (`test_ccxt_client.py:450`), which compares the error table to a hand copy of itself.
- [ ] Safety fact. Holding the compiled unit until `feed.ready` fixes the zero equity and the deploy before bind together (`S/proofs/ground-node/truth2.py g7`, level 4), waiting during the outage, then equity 10000.00, trading, 2 entries. Widening through the existing reconnect needs no new protocol (`truth2.py g6`, level 4), subscribed `['1','41']`, bars arrive, the EURUSD position stayed held at broker and node, and the last reconcile reads `reconnect`. The unit's own snapshot survives JSON and restores identically (`truth2.py g9`, level 4, 37,988 bytes). From `ground-node.md` section 2 all must hold, operations answer fast and deploy answers before compile, and M5 and M6 are not touched.
- [ ] `p5a-5`, `seams-6` and `p5a-8`. These are one fault in `_host` (`runtime.py:2389-2463`). It reads equity whether or not the session is up (`:2448`, with balance starting at 0, `ctrader_account.py:587`), and it throws the compile away when no venue is bound (`:2403`, and `_deployments` retries only COMPILING). Have `_host` wait with a plain reason and keep the compiled unit until the session is ready. A deploy before bind then moves from waiting to warming once bound.
- [ ] `p5a-1` and `seams-4`. `server.py:570,584` read `_markets` once. When a deployment names a new market, widen through the existing reconnect path, which is tested and already resets feed, books and reconcile. Add the market and drop the session once. `_markets` (`server.py:852`) walks every market of every kept deployment.
- [ ] Trap, `node-n1`. `_authorise` (`ctrader_account.py:800-805`) refuses the whole session if one symbol is unlisted, so widening without a check would kill a working account. A broker naming gold `XAUUSD.pro` is enough. `_markets` also includes refused deployments and markets he did not choose (`server.py:855-866`). Today one such deployment gives session down, one sign-in per tick, and RED sends 0 closes with a position open (`truth2.py g1`, level 4). The refusal is marked no-retry and is retried anyway.
- [ ] `node-n1`. Have `_authorise` keep the listed markets and report the others instead of refusing all. Treat `symbol_facts_missing` (`ctrader_account.py:820-826`) the same way, as unlisted, because today it also refuses the whole session for one symbol. Refuse that deployment by name, with the symbol the broker does not list. `_markets` takes only the markets he chose.
- [ ] Trap, held markets. `_authorise` empties `self.symbols` first (`ctrader_account.py:813`), so a market this session no longer carries loses its facts, whether it went unlisted, its facts went missing, or it left `_markets`. A position in `_open` on such a market then breaks R20 and R21. R20's read of the broker's stop goes through `_execution_price`, which answers None with no facts (`:1117`), so the stop reads None while the broker holds it, and R21 closes a protected position with a false alarm (`S/proofs/plan-fix-check/held_market.py`, level 4 to the None, level 3 from there). A later fill raises `KeyError` at `:1100`. So `_authorise` builds the new list first, and each market a position in `_open` sits on keeps the `SymbolFacts` it had and is not refused. After a restart `_open` is empty, so a position on such a market reads as a twin and the account stands down, which is no worse than today's refused session.
- [ ] Trap, from R21. `_markets` keeps a refused deployment's markets. Skipping them would undo R21's kill, because a position on a market the session does not know comes back from `_reconciled` with no market and no client order id (`ctrader_account.py:699-705`), reads as a twin, stands the whole account down, and RED cannot close it. With `_authorise` keeping the listed markets, a skip cures nothing. With the market kept the run reads claim mine, broker empty, kill row 1, and with it left out it reads `[('twin', '')]`, alarm twin, broker holds 9001, kill row 0, closes 0 (`S/proofs/plan-review-b/p1_orphan_market.py`, level 4).
- [ ] `p5a-20` and `p5b-6`. Add a one-rule refusal for a second unit on a symbol where `position_model` nets (`runtime.py:2389`), and the same rule for a Hyperliquid coin. One seam holds both. A long and a short on one coin cancel at the venue today.
- [ ] `p5a-15` and `seams-11`. Write `hosted_unit.snapshot()` under `data/deployments/<id>/` when a slow number moves. Pass it to `unit.start`, which already calls `restore_unit` and writes its cold reason when it cannot resume. A real restart then keeps what the unit calibrated, or says why not. Calibration content belongs to the unit, but saving it is plumbing and ours. Write the file whole and replace it, so a stop halfway leaves the old one.
- [ ] `seams-5` and `p5a-18`, by refusal. In `_host`, compare the stream's seconds with the venue's `BAR_NS` (`ctrader_account.py:114`), and refuse by name when they differ, about 15 lines. QMB already parses stream names (`unit_runner.py:244`). Today a 1-hour unit trades on 15-minute bars with no refusal. Steps 2 and 3, which give it the right bars, wait for G-DEMO, because history can be read only on demo.

**You see.**

- [ ] Promote a unit on gold, and gold's prices arrive with no restart, while a EURUSD trade already open stays held. Adding the market restarts the connection, so units already running on that account miss one bar's record, and no position is touched. If your PC reboots with no internet, the unit says it is waiting, then trades at your real balance. If you deploy a symbol your broker does not list, that one deployment is refused by name and everything else keeps trading.
- [ ] A unit tested on 5-minute bars is refused with a clear reason, instead of quietly trading on 15-minute bars. A restart keeps what a unit has learned, or says why it could not.
- [ ] If your broker stops giving a market's details while a position is open on it, that position and its stop stay as they are. If the node restarts in that state, the account stands down and an alarm tells you. RED cannot reach that one position then, so you would close it on cTrader yourself.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_app_deployed_runs.py::test_a_reboot_with_no_network_waits_then_trades_at_the_real_balance`. W11. Today it reads Trading at equity 0 with no entries. At the head it waits with its reason, then equity 10000.00, trading, 2 entries (`truth2.py g7`).
- [ ] `test_app_deployed_runs.py::test_a_new_market_after_bind_gets_its_bars_with_a_position_held`. W11. Subscribed `['1','41']`, bars arrive, the EURUSD position is held at broker and node, and the last reconcile reads `reconnect` (`truth2.py g6`). Running units on that account miss one bar's row, because `_shut` clears `_building` (`ctrader_account.py:993-998`), which is known and accepted.
- [ ] `test_app_deployed_runs.py::test_red_closes_an_orphan_on_a_market_other_than_the_self_tests`. With the deployment refused and the orphan on a market other than `fx.eurusd`, RED leaves the broker empty and the kill row reads 1, as `p1_orphan_market.py` sets it up. R21's W10 cannot see this, because its rig trades the self-test's market, which `_markets` always keeps.
- [ ] `test_app_deployed_runs.py::test_a_held_market_keeps_its_facts_and_its_position`. A reconnect where cTrader's answer omits a held market's facts, a second where it no longer lists that market, and a third where the market has left `_markets`. Each time the stop reads the broker's stop, nothing closes, no alarm rises, and a fill on that position raises nothing.
- [ ] `test_app_deployed_runs.py::test_an_unlisted_symbol_is_refused_by_name_and_the_account_keeps_trading`. W11. With `XAUUSD.pro`, the deployment's row reads refused and names the symbol, the session stays up, and RED sends its closes. Today session down and 0 closes (`truth2.py g1`).
- [ ] `test_app_deployed_runs.py::test_a_second_unit_on_a_netting_symbol_is_refused`, `::test_a_deploy_before_bind_warms_once_bound`, `::test_a_restart_restores_a_moved_number_or_writes_its_cold_reason`, and `::test_a_five_minute_unit_is_refused_by_name`. Each asserts its literal row or reason.
- [ ] No existing test is expected to change, because the reconnect path and the bind tests stand. Run `uv run --no-sync python -m pytest qmn/tests/test_app_deployed_runs.py qmn/tests/test_app_binding.py -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qmn/tests/test_app_binding.py`, `test_app_runtime.py`, `test_app_feed_reconnect.py`, `test_app_healing.py`, `test_app_grants.py`, `test_app_operations.py`, `test_ccxt_client.py`, `test_app_every_way_out.py` and `test_app_broker_wins.py`, at the parent and the head. No model. Save `r22-regression.log`. Pass when the head fails nothing the parent passes.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/ground-node/truth2.py g1 g6 g7 g9` with `proof_at.sh root`, at the parent and the head. No model. Save `r22-truth.log`. Pass when the parent shows session down with 0 closes, and the head shows the deployment refused, trading kept, and 2 entries, with no patch.
- [ ] Lane 3. Run `S/proofs/seams/feed.py bars <folder>` at the parent and the head. No model. Save `r22-bars.log`. Pass when the parent warms on 15-minute bars and the head refuses by name.
- [ ] Lane 4. Run `S/proofs/seams/parity.py 9 <folder>`. No model. Save `r22-parity.log`. Pass when it reads 63 of 63.
- [ ] Lane 5. A real restart of the node process on a throwaway folder after a moved number, on the conformance venue. No model. Save `r22-restart.log`. Pass when the number holds or a `cold_start` row names the reason.
- [ ] Lane 6. Promote a second market through the real host route on a throwaway folder, on the fake cTrader. No model. Save `r22-promote.log`. Pass when its row leaves `warming up 0` with bars arriving.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r22-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r22-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r22-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r22-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from a promote on a new market to its first bar, and the size of a snapshot.
- [ ] Probe. Lane 6, and the snapshot file's size in lane 5.
- [ ] Baseline. `truth2.py g9` gives 37,988 bytes. A new market today never gets a bar.
- [ ] Rule. Fails if the widening's reconnect takes more than 30 s on the fake, the supervisor's limit on a call.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r22-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Fix connections and honest words (R23)

Phase F, the node. Source is `A/reports/ground-node.md` Cause E, with `A/reports/ground-unit.md` block G for `p1b-8`. A session that cannot open is retried five full sign-ins a second. Every weekend a forex node reads "Stopped by a health check". The clock stand-down can never fire. A paper position vanishes at a restart. A naked manual trade reads "protected". Done when the rest of wall check W12 passes.

Rows carried. `p5a-10` `p5a-11` `p5a-14` `p5a-16` `p5a-22` `chief-1` `p1b-8` `p0a-20`

Rows in part. `seams-16` by rebuilding paper positions at a restart.

Proves. An hour of refused socket stays under a set count of sign-ins, and a weekend reads closed, not stopped.

**Depends on.** R22.

**Files.**

- [ ] Edit `qmn/src/qmn/app/feed_keeper.py`, `qmn/src/qmn/app/stand_down.py` and `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmn/src/qmn/app/paper_lane.py`, `qmn/src/qmn/app/attribution.py` and `qmn/src/qmn/app/reconciler.py`.
- [ ] Edit `qmn/src/qmn/venue/ctrader_account.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/host.py`.
- [ ] Edit `qmn/tests/test_app_feed_reconnect.py`, `qmn/tests/test_app_stand_down.py` and `qmn/tests/test_app_attribution.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/tests/test_heartbeats_loop.py`.
- [ ] Edit `qmx-agents/apps/trading-node/app.toml`, by call 11, because `qmn` is in its lock, and `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` for its version row.
- [ ] Create `qmn/tests/test_app_connections.py`.

**Build.**

- [ ] Subtract. `p5a-32` went in R21. No other `test-delete` row or dead code sits in these files.
- [ ] Safety fact. Each change reuses what exists. `Backoff` is in `healing.py`, `alarms.market_hours` (`alarms.py:575`) already answers open or shut, and `StandDowns` already takes `clock_offset_ns` (`stand_down.py:446`), with the clock row passing in `test_app_stand_down.py` under an injected probe. Most of this is level 2, and the back-off, weekend, clock and paper-restart shapes were not run, so this PR's tests are their proof. `chief-1` must keep `VERIFIED`, because `verify.py:270` refuses anything else and the client would never trade. From `ground-node.md` section 2 all must hold, and "not ours" positions are still never touched. No new network comes from the money process. No promise in `ground-core.md` section 2 is in reach, because the host's one change adds two facts to a file it already writes after a Settings write, and refreshes that file after each probe through the existing `refresh_facts`.
- [ ] `p5a-10`. `FeedKeeper.pump` (`feed_keeper.py:286`) reopens on every tick. Reuse `Backoff` from `healing.py` with `cap_s=300`, because its default of 1 s with a 60 s cap (`healing.py:57-59`) gives about 60 sign-ins an hour, above the 40 rule. A small wrapper makes the first retry at once, so `test_app_feed_reconnect.py` keeps its meaning. Status reads the cause. About 15 lines.
- [ ] `p5a-22`. `watch_feed` ignores the calendar. Pass `alarms.market_hours` to `StandDowns`, so a symbol is stale only inside its open calendar (TN-20). `market_hours` raises `LookupError` for a market no deployment names, such as the self-test's, so `StandDowns` reads that as open, as the push sender does. About 10 lines. A test must run across a weekend, because nobody has shown one does.
- [ ] `p5a-11`. The runtime builds `StandDowns` without a clock probe (`runtime.py:1885`). The design has the node import `qmx_host/clock_probe.py`, but that imports the harness and engine. The host already probes every 60 s in its heartbeat loop (`host.py:1472-1475`), and it writes `road/host/facts.json` into the volume only after a Settings write (`keep_facts`, `host.py:2019-2026`). So the facts gain the offset and its time, the probe loop calls `refresh_facts` after each probe, through `asyncio.to_thread` as `keep_facts` does, because on the event loop it would wait on the supervisor's lock, the hazard the comment at `host.py:1478` names. A stale reading reads None. Without that call a real node reads None within a minute, and the clock stand-down still never fires. The node reads the file. No new network comes from the money process. About 30 lines.
- [ ] `p5a-16` and `seams-16`. Paper positions are memory only (`paper_lane.py:55`). Rebuild them from the node journal's `paper` partition, from the send, filled and closed rows, and call `adopt`. Drop any send whose position has a `trade` row in the unit journal, because a paper stop that fires writes no node journal row (`paper_lane.py:88-90`), so each past stopped trade would come back as an open position and may close a second time. Stops crossed while down fire on the next bar, which is accepted. About 60 lines. Level 2, not run.
- [ ] `p5a-14`, call 14. Change the word `NOT_OURS` (`attribution.py:43`) to "not ours, never touched", with "no stop at the broker" added when true, in `reconciler.py:_shown`. A test pins stop None beside the old word, and it changes on purpose. The word is his to change.
- [ ] `chief-1`. `_measured` never reaches the passport, because neither `operations.py` nor `server.py` reads it, and the real protection is the read after the fill, which holds. So this is about words only. Change the `detail` text on the six literal facts (`ctrader_account.py:919-954`) to say they are not measured until the demo probes run. The three that come from the session keep "read on the cTrader session". The verdict stays `VERIFIED`. The passport line waits for C-15, as its plan says.
- [ ] `p1b-8` and `p0a-20`. Call `seam_check` (`qml/protocol/unit.py:1021`) at the first live bar after warm-up in `qmn/app/runtime.py`, and write its `seam_flag` row. A restart gap in the node's own recording is the only case today, since history warm-up waits for G-DEMO. If it cannot land in about 20 lines, leave it for the history PR, and say so in the PR body.
- [ ] Do not read `ProtoOAAccountDisconnectEvent`, `ProtoOATraderUpdatedEvent` or `ProtoOASymbolChangedEvent` here. What the first does to a session is a guess until demo, which is `node-n5`, and it waits for G-DEMO.

**You see.**

- [ ] If the broker's connection will not open, the node backs off instead of signing in five times a second, which could get your app blocked, and it tells you why. Over a weekend a forex node reads closed, not stopped, so that word means something again.
- [ ] A drifting clock now stops entries. Paper positions survive a restart. A manual trade reads "not ours, never touched", and says when it has no stop at the broker. Facts nobody has measured yet no longer say they were read from the session.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_app_connections.py::test_an_hour_of_refused_socket_stays_under_a_set_count_of_sign_ins`. W12. On the fake's `Flaky`, over an hour of injected clock, sign-ins are at most 40 and the first retry is immediate. Today 18,000. Status names the cause.
- [ ] `test_app_connections.py::test_a_weekend_reads_closed_not_stopped`. W12. Across Friday close to Sunday open on `fx-24x5@1`, no `stale_feed` stand-down holds, and a stale feed on Tuesday still stands down.
- [ ] `test_app_connections.py::test_a_stale_host_clock_reads_none_and_a_drift_stops_entries`. Writes `road/host/facts.json` with an offset past the band, then with an old time. Entries stop in the first case and not in the second.
- [ ] `test_heartbeats_loop.py` gains `test_a_drift_reaches_the_nodes_volume_with_no_settings_write`. A real supervisor and a real probe answer with a drift past the band, with no Settings write. The node's `road/host/facts.json` holds that offset after the next probe. Today it holds none.
- [ ] `test_app_connections.py::test_a_paper_position_survives_a_restart_and_a_crossed_stop_fires_on_the_next_bar`, where a past stopped paper trade with a `trade` row in the unit journal stays closed, and `::test_a_seam_writes_its_flag_row`.
- [ ] Tests that change on purpose are `test_app_attribution.py` for the word, and any test reading the literal facts' `detail`. Run `uv run --no-sync python -m pytest qmn/tests/test_app_connections.py qmn/tests/test_app_feed_reconnect.py qmn/tests/test_app_attribution.py -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Regression against the parent. Run `qmn/tests/test_app_feed_reconnect.py`, `test_app_stand_down.py`, `test_app_attribution.py`, `test_app_binding.py`, `test_app_runtime.py`, `test_app_every_way_out.py`, `test_app_broker_wins.py`, `test_app_deployed_runs.py`, and in the host `test_heartbeats_loop.py`, at the parent and the head. No model. Save `r23-regression.log`. Pass when the head fails nothing the parent passes, apart from tests named on purpose.
- [ ] Lane 2. Fail-today proof. Run `S/proofs/ground-node/truth3.py` with the `Flaky` socket and a count of sign-ins, at the parent and the head. No model. Save `r23-flaky.log`. Pass when the parent counts one sign-in per tick and the head stays under the set count.
- [ ] Lane 3. A fake weekend through the real runtime on the conformance venue, with status read each hour of clock. No model. Save `r23-weekend.log`. Pass when no hour reads a health stop while the market is shut.
- [ ] Lane 4. Restart a paper lane mid-trade on a throwaway folder. No model. Save `r23-paper.log`. Pass when the position is held and the journal's entry gets its exit.
- [ ] Lane 5. Read the node's passport on a rehearsal. No model. Save `r23-passport.log`. Pass when the six literal facts' words say not measured, and the verdicts still read `VERIFIED`.
- [ ] Lane 6. Run `S/proofs/seams/parity.py 9 <folder>`. No model. Save `r23-parity.log`. Pass when it reads 63 of 63.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save `r23-boot.log`. Pass when the host answers and stops clean.
- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save `r23-repeat.log`. Pass when the three runs agree.
- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save `r23-leak.log`. Pass when none appears.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r23-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Sign-ins per hour on a refused socket, and microseconds per `pump`.
- [ ] Probe. Lane 2, and a timed `pump` at the parent and the head.
- [ ] Baseline. Five sign-ins a second, by reading.
- [ ] Rule. Fails above 40 sign-ins an hour. The back-off's top wait is 5 minutes, so the steady rate is 12 an hour.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`, and `S/review/r23-check-<head8>.md` on disk.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.

## Give the first-start script its new job and ready the demo proofs (R24)

Phase F, the node. Source is `A/reports/ground-start.md` blocks I and J, and section C-15 of `P/build/UNIT-PLAN.md`, carried here as `A/plan-current.md:3825-3876` writes it. By his word the foundation comes first and the dummy does not skip the judge, so the script's old job, to prove the dummy trades on his demo, is gone. Its new job is to prove that this machine's node is ready to receive a unit, on his real folder. It stops there, by call 17. A unit reaches a node by passing the judge and his click. Done when the rehearsal reads all PASS with the plain "no unit" line, every C-15 mark passes in rehearsal, and `tools/proof_foundation.py --walls` reads PASS for W1 to W12. This ends phase F and the body of the program, and the next step is G-DEMO.

Rows carried. `plan-check-1` `seams-1` `p5c-1` `seams-13` `p5c-2` `p5c-4` `start-n3`

Proves. A fresh rehearsal folder with no fixtures reads all PASS and the plain line, and a node that refuses reads FAIL in its own words.

**Depends on.** R23.

**Files.**

- [ ] Edit `tools/first_real_start.py` and `tools/tests/test_first_real_start.py`.
- [ ] Edit `tools/proof_foundation.py`.
- [ ] Create `qmn/probes/ctrader_demo/run.py`, and one script per mark in that folder, `label_survives.py`, `partial_keeps_label.py`, `repeated_client_order_id.py`, `attribution.py`, `network_cut.py` and `refresh.py`.
- [ ] Create `qmn/tests/test_ctrader_demo_probes.py`.
- [ ] Edit `qmn/tests/test_app_binding.py`, to teach the fake a part-volume close.

**Build.**

- [ ] Subtract. `DUMMY` goes from the script (`first_real_start.py:56`), because the dummy no longer reaches a node through this script. `_dummy_version` (`:449-460`) loses its dummy and becomes `_unit_version(world, unit_id)`, because `--unit` still needs a version lookup. No `test-delete` row sits in these files.
- [ ] Safety fact. The script talks only REST, so changing what it checks cannot change the product. Level 4 for today's behaviour, from 14 tests with real throwaway git repositories for the landing gate. From `ground-start.md` section 2 these must hold, the script's REST-only rule, refusal before reading a credential, convergence on rerun, and only `operator` passes promote with `draft` to `paper` refused. The lifecycle table stays as it is. That refusal is correct and must stay. No promise in `ground-core.md` section 2 is in reach.
- [ ] `plan-check-1` and `p5c-4`, call 17. `landed_refusal` (`first_real_start.py:563-575`) hard-codes main, and he lands into a branch he names. Add `--landed-on`, default `engine/base`, and read the origin ref of that branch. Local `engine/base` is 732 commits behind origin, which does not matter, because the gate reads the origin ref. The fetch and the merge-base use that ref. The words name that branch.
- [ ] `seams-1` and `p5c-1`, call 17. `_deployed` (`:463-497`) assumes a tested dummy, while `land_dummy` (`first_start.py:656`) puts a draft, and the table is correct to refuse it. Make this step `--unit <id>`. With none named it prints one plain line, "no unit has passed the judge yet, so nothing was deployed", and that is not a FAIL. The audit's "labelled shortcut" remedy is closed by his words in SEEDS, so the repair is to the script.
- [ ] Rehearsal. Keep the two fixture rows, labelled, but only for a run that passes `--unit`, so the deploy crossing stays proved. They must never again stand behind an all-PASS on the plain path. Copy `S/tools/owner_lane_c14.py` to `evidence/r24/`, and give its rehearsal a plain mode with no fixture rows and a `--unit` mode with them, because lanes 2 and 3 run those two.
- [ ] `seams-13` and `p5c-2`. `_deployed` reads once and passes at `compiling`. Poll the node's `deployments` row past `compiling` until `warming up`, `trading`, `waiting` or `refused` (`Phase`, `runtime.py:1708`), within `--trade-s`. A refused row is a FAIL with the node's own words. The fake host in `test_first_real_start.py` must learn to turn a row to refused.
- [ ] The other steps stay as they are, which are folder found, practice node Ready, demo session ready, test trade with stop, passport landed, node journal rows and test trade rows. `ctid` against `traderId` stays unproven until a real token.
- [ ] Trap, call 18, `start-n3`. The uncommitted edit in `D:/QMX-worktrees/bld-us-c14` is left out, and it is half of keyring's rule anyway. `real_bearer` (`:620`) ignores `UserName`. Write the login reader's full rule, about 4 lines, in `credential_manager` (`:605-617`). Read `UserName` from the struct it already declares. Read the service entry `qmx/control-token`. If it is missing, or its `UserName` is not `control-token`, read `control-token@qmx/control-token`, because keyring moves the previous value to `user@service` whenever anything writes that service again. The table in `ground-start.md` block J is the case list, and `S/proofs/ground-start/bearer.py` runs keyring's real backend over an in-memory store. No product code writes that service under another user today, so neither failing row can happen yet.
- [ ] Trap. The reader has never run on a real entry, because `owner-c14-bearer.log` is 0 bytes. The builder runs `S/tools/owner_lane_c14.py bearer <wt> 18941`, an owner lane on a throwaway entry outside `qmx/`. It writes to the real Credential Manager, so it runs only in this owner lane, on that one throwaway name, and it never reads or lists a `qmx/*` entry. It is the one lane that runs without `env.sh`'s guard, because the guard refuses `CredReadW`.
- [ ] Section C-15, as planned. Create `qmn/probes/ctrader_demo/` with `run.py` and one script per mark of `P/architecture/parts/C-node-mis-external/EXTERNAL.md` section 2. Write each mark with a rehearsal on R20's harsher fake cTrader over the real codec, and a demo run that reads its grant from the practice node's store only. The old plan's conformance venue will not do, because `ConformanceAccount` takes a `Ticket` and speaks no cTrader wire, so each probe's wire code would first run on his demo and a probe bug would read as a broker fact. Teach the fake a part-volume close, because `_on_ProtoOAClosePositionReq` pops the whole position today (`test_app_binding.py:312-313`). Each mark prints PASS or FAIL per line. The marks are these.
  - [ ] A market order with `label` and `relativeStopLoss` fills, and its position's trade data carries the same `label`.
  - [ ] A partial close keeps the label on the remainder.
  - [ ] A second order with the same `clientOrderId` is either refused by cTrader or accepted, and the probe records which.
  - [ ] Reconcile attributes the test position as mine.
  - [ ] The network-cut drill, TN-01. The socket closed right after a send leaves exactly one position after reconnect, and no resend.
  - [ ] The refresh drill, TN-05. A forced grant refresh stores the new grant before discarding the old, the session comes back ready, and a second refresher is refused.
- [ ] Add to the demo run the questions only his demo settles, from `ground-node.md`, each printing what it found, not PASS or FAIL. They are whether a fill carries the stop, what a close on a gone position answers, whether events carry the request's `clientMsgId`, the deal-history fields for a stop, trendbar retention and side, `traderId` against `ctid`, the six literal facts, and what `ProtoOAAccountDisconnectEvent` does to a session. It also asks these four, each printing what it found. Whether a position with several deals shows its closing deal on the first page of `ProtoOADealListByPositionIdRes`, given `hasMore` and a time window with no stated default. Whether a position missing from one reconcile listing can come back at the next session. Whether a non-closing event can omit `stopLoss`. Whether the refresh drill, run from a separate process, invalidates the running node's session.
- [ ] Fill the `--walls` table in `tools/proof_foundation.py` with the tests the sections R03 and R15 to R23 added for W1 to W12.
- [ ] Plan lines. Appendix B records the change to C-14's You see, C-14's lane 5, and C-20's gate. Do not edit `UNIT-PLAN.md` from this branch.

**You see.**

- [ ] After you land the code and sign in once on cTrader's own demo page, one script checks that your node is ready to receive a unit, on your real folder, one plain line per fact. It says plainly that no unit has passed the judge yet, so nothing was deployed, and that is not a failure. When a unit has passed the judge and you click, you can name it to the script, and if the node refuses it you read the node's own words.
- [ ] The demo proofs are ready and waiting for your sign-in. Nothing here needs your sign-in until then.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_first_real_start.py` gains `test_with_no_unit_named_it_prints_the_plain_line_and_exits_zero`. The line is exactly "no unit has passed the judge yet, so nothing was deployed", and the exit is 0.
- [ ] `test_first_real_start.py` gains `test_a_node_that_refuses_is_a_fail_in_its_own_words`. The fake host turns the row to refused, and the FAIL line holds the node's `detail`. It also gains `test_compiling_is_not_a_pass`, and `test_landed_on_reads_the_named_branch` on real throwaway git repositories, with `engine/base` as the default and main no longer asked.
- [ ] `test_first_real_start.py` gains `test_the_reader_follows_keyrings_rule`, the four rows of `ground-start.md` block J on `bearer.py`'s in-memory store, each giving the literal value keyring gives.
- [ ] `test_ctrader_demo_probes.py::test_each_mark_passes_in_rehearsal_and_fails_when_its_fault_is_injected`. Runs `run.py --rehearsal`. Tests that change on purpose are in `test_first_real_start.py`, where the old all-PASS on the plain path planted two fixture rows. Run `uv run --no-sync python -m pytest tools/tests/test_first_real_start.py qmn/tests/test_ctrader_demo_probes.py -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.

- [ ] Lane 1. Whole-repo run at this phase end, with `S/tools/run_tests.sh`. No model. Save `r24-whole.log`. Pass when it fails nothing R23's tip passed.
- [ ] Lane 2. Fail-today proof. Rehearsal on a fresh throwaway folder with no fixtures, with `S/tools/owner_lane_c14.py rehearsal`, at the parent and the head. No model. Save `r24-rehearsal.log`. Pass when the parent reads FAIL at the dummy line, and the head reads every line PASS and the plain "no unit" line. This is W13's first half.
- [ ] Lane 3. Rehearsal with `--unit` and its two fixture rows, then a node that refuses it. No model. Save `r24-refused.log`. Pass when the first reads PASS past `compiling`, and the second reads FAIL in the node's words.
- [ ] Lane 4. The walls. Run `tools/proof_foundation.py --walls`, then every C-15 mark with `uv run --no-sync python qmn/probes/ctrader_demo/run.py --rehearsal`. No model. Save `r24-walls.log`. Pass when W1 to W12 read PASS, and each mark prints PASS, with its fault run printing FAIL.
- [ ] Lane 5. After G-LAND and G-DEMO, the real run on his folder. It waits for him. Save `c14-real.log`. Pass when every line reads PASS, with the plain "no unit" line when no unit has passed the judge. It no longer implies any unit traded.
- [ ] Lane 6. After G-DEMO, `uv run --no-sync python qmn/probes/ctrader_demo/run.py` on his demo account. It waits for him. Save `c15-demo.log`. Pass when every mark prints PASS, and its answers to the demo questions are saved.
- [ ] Lane 7. Scan every output of lanes 2 to 6 for grant, token and password values. No model. Save `r24-leak.log`. Pass when none appears.
- [ ] Lane 8. The refresh drill and the cut drill in rehearsal, as C-15's lanes 3 and 4. No model. Save `r24-drills.log`. Pass when the new grant is stored before the old one is discarded, the session is ready again, a second refresher is refused, and one position exists after reconnect with no resend.
- [ ] Lane 9. Run the PR's new tests three times in a row. No model. Save `r24-repeat.log`. Pass when the three runs agree.
- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save `r24-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for the rehearsal end to end, and seconds per mark.
- [ ] Probe. Lanes 2 and 4.
- [ ] Baseline. `owner-c14-rehearsal.log` from the last build.
- [ ] Rule. No fail rule, recorded for the trail.

**Review gate.** None. No screen changes.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round. Lanes 5 and 6 wait for G-DEMO, and they do not hold the verdict.
- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log`.
- [ ] Lows in `lows.md`, new findings justified in `BACKLOG.md`, the verdict, head, parent, patch-id and count in `ledger.tsv`.
- [ ] Appended to the stack. Nothing merges. He lands the stack himself.
- [ ] Tell him what G-DEMO asks of him, in plain words, per "Close the program".

## Close the program

- [ ] Every PR is stacked with a CLEAN verdict, or skipped with its reason in `S/RESUME.md`. The count of PRs added reads 0, or each added PR names his word.
- [ ] The last whole-repo run at the stack tip fails nothing but a named environmental gap, such as the credential guard's refusal in `test_app_grants.py` or the 106 `qmx-home` backup tests on a full `C:`.
- [ ] `tools/proof_foundation.py` reads 18 PASS lines, and `--walls` reads W1 to W12 PASS, at the stack tip.
- [ ] `node assemble.mjs` still shows every must row placed, and `S/BACKLOG.md` holds no finding without its evidence level.
- [ ] The stack list goes to him, bottom to top, with each PR's link and its one-line verdict. He lands it himself. Where it lands is his, and the first-start script takes that branch by `--landed-on`.
- [ ] Tell him what G-DEMO asks of him, in plain words. He lands the code, signs in once on cTrader's own demo page, and runs the first-start script on his folder. The coordinator then runs the demo proofs and saves `c14-real.log` and `c15-demo.log`. The old node can be deleted on those two logs before any unit has traded on demo, because the new node loads none of its code, and he may say otherwise.
- [ ] List each later step for him in plain words, with what it waits for (Appendix B).
- [ ] Tell him in plain words what changed, what he can try first, and what waits on him. Do not ask him for anything the record already answers.

## Appendix A. Prototype evidence

The grounding agents ran each repair's shape against real code at `50c83a4e`, patched in memory, with no file changed. This table is what was proven by running. Script paths are under `D:/Temp/audit/` until the Arm box copies them to `S/proofs/`. Logs of the long runs are in `D:/Temp/audit/chief/ground-long/`.

| Question | Script | Result | Level |
| --- | --- | --- | --- |
| Does a repair reach an installed app? | `ground-core/sup_proof.py` C to G | No. A host start runs the old hash, env builds unchanged. The same bytes reinstall and rerun the build, and the volume's data stays | 4 |
| Does `run(timeout=3)` fix a stuck uv? | `ground-core/pipe_proof.py` | No. It raised after 25.3 s, waiting on the pipe | 4 |
| Does an install stall other apps? | `ground-core/stall_proof.py` | Yes. A plain call answered after 44.1 s | 4 |
| How fast does a running app grow the store? | `ground-core/sup_proof.py` B | 3.1 `apps` and 3.1 `aggregates` rows a second, about 200 MB a day, rough | 4 |
| Does the restart wait reset? | `ground-core/sup_proof.py` H | No. 5, 10, 20 and 40 s after calm runs | 4 |
| Is the answer-file race real? | `ground-core/done_race.py` | 2,943 of 3,000 tight rounds. It proves the window, not the rate | 4 |
| Does dead weight detach? | `ground-core/cut`, `chief/ground-long/cut.log` | 54 failed and 8 errors, of which 29 are the named deletions and the rest are what the scratch copy lacked | 4 |
| Do the unit refusals move shipped tests? | `ground-unit/plug/refuse_trial.py`, `chief/ground-long/unit-trial-qml.log`, `unit-trial-qmb.log` | QML 1,445 passed and 1 failed, the named session test. QMB's unit path 18 passed | 4 |
| Does a direction trim run? | `ground-unit/p2.py` A | The obvious form refuses with `motion_source`. Trimmed by hand, 2 long and 0 short | 4 |
| Is a comparator enough? | `ground-unit/p3.py`, `p6.py` | No. 0 entries under `all`. With the feeder rule, 25 at level 1 and 0 at level 99, with the dummy identical | 4 |
| Do price series fed whole bars come alive? | `ground-unit/p4.py`, rerun by this plan's writer | 6 of 14, with 1,154 to 1,595 entries. The dummy is unchanged | 4 |
| Does a bar with `time` change the dummy? | `ground-unit/p2.py` D | No | 4 |
| Does the save-time clash check refuse the landing? | `ground-unit/p6.py` | 0 clashes across 455 pages | 4 |
| Does a record on main reach the run? | `ground-qmb/records.py` | No today. With the one-place repair, same compiled fingerprint, and gold lot step 0.10 moved 29 trades, +22.84 to 21 trades, -169.04, on a planted record | 4 |
| Does a record moved on main show? | `ground-qmb/records.py` | Not in the same host, 0.01 version 1 against 0.05 version 2 | 4 |
| Do costs reach net with R unchanged? | `ground-qmb/records.py` | Commission 3.50 gave -249.91 with R at -4.3841, and swap gave -171.59 | 4 |
| Do ticks through the door match the CSV? | `ground-qmb/bridge.py` | Identical bars and "same trades True". The ticks were cut from those bars, so it proves the path | 4 |
| Does `materialise` honour a sealed month? | `ground-qmb/bridge.py` | No, "COPIED 1 file(s)", by its docstring | 4 |
| Is one market of two possible? | `ground-qmb/bridge.py` | Yes, 14 trades on `fx.eurusd` | 4 |
| Do real months read as holes? | `ground-qmb/holes.py` | 0 past the limit on January to March 2025, and 88 head bars on a window-end check | 4 |
| Do trades reach the Library? | `p34/p1_trade_account.py` | trades=0 as written, trades=1 with the account set | 4 |
| Which reason texts have no code? | `ground-start/census.py` | 3 of 32, plus the one reached through `Unprotected` | 4 |
| Does the alarm list load in a wheel layout? | `ground-start/alarm_wheel.py` | No today. Yes with the register inside the package, on a copied layout | 4 |
| Do the log shapes hold? | `ground-start/logs.py` | known-10 raises, severity INFO, telemetry raises, as filed | 4 |
| Does calling `configure` publish? | `ground-start/mis_real.py` | 0 readings silently with the record's venue, 4 with the right source | 4 |
| Does `tool_timeout` as a waiting code hold? | `ground-start/proof_waiting.py` | One move and one deployment on the rig's fake node | 4 |
| Does the login reader follow keyring? | `ground-start/bearer.py` | Two rows fail, neither reachable today | 4 |
| Does broker-wins break tests? | `ground-node/venuewins.py`, `chief/ground-long/node-runtime.log` | No. 17, 11 and 11 passed. Outage gives closed STOP and rows 1 | 4 |
| Does the kill reach an orphan? | `ground-node/truth4.py`, `reach.py`, `chief/ground-long/node-kill.log` | Yes with the sketch, kill row 1, and 17 passed on the harsher venue | 4 |
| Does a refused exit keep going? | `ground-node/truth4.py` | 2 closes, flat, 3 trades with the sketch | 4 |
| Does holding the compile fix the zero equity? | `ground-node/truth2.py g7` | Yes, equity 10000.00, trading, 2 entries | 4 |
| Does widening work by reconnect? | `ground-node/truth2.py g6` | Yes, subscribed `['1','41']` with the position held | 4 |
| Does one unlisted symbol kill the account? | `ground-node/truth2.py g1` | Yes, 0 closes under RED | 4 |
| Does a snapshot survive JSON? | `ground-node/truth2.py g9` | Yes, 37,988 bytes | 4 |
| Does a sweep's verdict lie? | `p6/test_sweep_verdict.py` | Yes, 6 trades and `no_trades` | 4 |
| Can a template read the real verdict with no engine change? | `ground-core/test_verdict_read.py` | Yes, on the real engine with a fake Library | 4 |
| Does a check with no Library see a real error? | `ground-core/template_facts.py` | Yes, `outside_range` is left after the five kinds | 4 |
| Do QMB and the node decide alike? | `seams/parity.py` | 63 of 63 | 4 |
| Does a same-bytes install change a signed money app? | `plan-review-a/money_env.py` | Yes. uv rebuilt the signed hash's environment, and start asked for no signature, so R03 keeps that branch off money apps | 4 |
| Can an older study edited after a result take a friendly k? | `plan-review-a/shrink2.py` | Yes. Honest study 0.0558 and weight 0.0000, edited study 0.2193, weight 1.0000 and 0 `spec_edit` tries | 4 |
| Does a Library-less check see what compile refuses? | `plan-review-a/offline.py` | Not on GBPUSD. `checked` stops at `no_record`, while `compile_unit` adds `halts_not_built`. The dummy on GBPUSD gives only `no_record` | 4 |
| Does leaving a refused deployment's market out undo RED? | `plan-review-b/p1_orphan_market.py` | Yes. Kept, kill row 1 and broker empty. Left out, a twin alarm, kill row 0 and closes 0 | 4 |
| Does a projection handed only committed keys keep a score? | `plan-review-b/test_r19_months.py` | No. 3 trades in round 1, then `(2, '2.0')` with four trades in the store | 4 |
| Does the writer accept a reason code only `journal.py` knows? | `plan-review-b/p2_small.py` | No. It answers that the reason is not one of `REASON_CODES` | 4 |
| Does a junction hold for the login folder's mechanics? | A throwaway target in the fix round's scratch folder, no login touched | Yes. A write reached the target, `cmd /c rmdir` removed only the link, and `rm -rf`, `Remove-Item -Recurse -Force` and `shutil.rmtree` of the parent each left the target whole | 4 |

These stay unproven until a PR runs them.

- Arming. A real `haiku` turn through the login junction, which the coordinator proves in the Arm box.
- R03. A real `uv` run through the new install shape, because every proof patched uv out. What a tool timeout does on a real opted-in app, because that was read, not run.
- R04. The `p0a-9` check over all of QML. The trial did not hold it, and `test_compile_dummy.py:272` is known to move. No unit trial crossed a QMB job or the fake cTrader.
- R06. The settle-per-period idea and the claim that the dummy's warm-up holds. The cost per save over the full store.
- R07 and R13. The Library-less gate words, `S/proofs/p6/gate_proof.py`'s before and after. `core-n2`'s path fix.
- R08 and R09. Real Dukascopy ticks against dukascopy-node bars. The real tick rate, which is a guess of 3.5M a month. Whether Christmas reads as a hole in a real month. The rule for which source a market reads, which rests on reading.
- R10 and R11. The shapes of `p0b-14`, `p2-5` and `p2-11` rest on reading.
- R12. `p6-5`'s memory row, and the `library` node's read of a verdict on the real store.
- R15. Whether `runtime.py:1007` reaches the journal, which the repair covers either way.
- R16. The real wheel build with a real alarm.
- R19. The bounded harvester, which `p34/p4_harvest_cost.py` must flip.
- R20. The history path and `node-n4`. `venuewins.py` books every missing position at the held stop and never asks for history, so its run says nothing about either.
- R21. Flatten, which ran only through its shared close.
- R23. The back-off, weekend, clock and paper-restart shapes.
- R24. The login reader on a real entry, which belongs to the builder's owner lane.
- G-DEMO only. `label` survival, repeated `clientOrderId`, attribution, the cut and refresh drills, whether a fill carries the stop, what a close on a gone position answers, whether events carry `clientMsgId`, deal-history fields, trendbar retention and side, `traderId` against `ctid`, the six literal facts, and what `ProtoOAAccountDisconnectEvent` does. Also `hasMore` and the default time window on a position's deal list, whether a position missing from one listing can come back, whether a non-closing event can omit `stopLoss`, and whether the refresh drill, run from a separate process, invalidates the running node's session.
- Not reached by anyone. A kill across a node that is away, the server paths, twin and take-over paths, and `CcxtClient.read_back` for Cause A's fault.

## Appendix B. Not in this program

These have no PR section, by `PLAN-SHAPE.md`. Each names what it waits for.

**After G-DEMO, on `c14-real.log` and `c15-demo.log` reading all PASS.**

- The bars he tested on, `ground-node` D steps 2 and 3, with `seams-12`, `p5a-19` and `seams-5` in full. `_building` and `Recording` keyed by market and size, then broker history at `_host`, with the ask built from the current spread and labelled so. It reads `start-n2` too.
- Replay against a recorded day, `seams-8`. The world filter at `route.py:32`, and recorded bars to CSV. It needs `seams-5` first.
- The node's own cost data. Swap and commission from cTrader's symbol, then a host step that turns `minute` rows and fills into a cost profile.
- Removing the live lanes, `deletion-3`.
- The old node cut, section C-20, with `deletion-2`, `deletion-4`, `deletion-11` and `deletion-12`. Move `qmn/host/sqs_baseline_producer.py` out first, and hand the rule text at `decision_root.py:496-510` to the risk session. `runtime_risk_gate.py` is not the gate, and it can go.
- Read `c15-demo.log`'s answers against R20's history parse, the stop-on-later-event amend, `_close`'s five-second wait, and `node-n5`.

**After the risk session agrees the socket.**

- Exits really run, steps 2 and 3 of `ground-unit` B, with `p1b-3`, `p1b-4`, `p5a-17`, `unit-n2`, the signed stop distance, `p0a-12` and `p1a-7`.

**Volume blocks.**

- `p0a-14`, then part 2 of `ground-unit` C, after the bars work.

**On his word.**

- `qmf-indicators` and `qmf-structure`. Write the structure ideas down as a dictionary note first.
- The old QMB door, about 32,700 plain lines and about 15,500 of methods to read first, with `deletion-6`. The Book path and the two test-used modules stay.

**G-SERVER.**

- `plan-check-4`, `p5c-5`, section C-19, `p5d-2` and `p34-7`.

**G-WALLET.**

- `p5b-1` to `p5b-7`. `p5b-3` and `p5b-6` are mostly closed by R21 and R22.

**Before any live account.**

- `triage-3`, two doors, by `ground-start` H, and section C-21.

**Research phase.**

- `p6-6`, `p6-8`, `p6-10`, `p6-11`, `p2-7` and `p2-3`. One engine question for him then, the script read of a family's tries.

**Left out on purpose.**

- `p6-14`, because the copies are the design. Do not count those 1,900 lines.
- `p1b-5`, because the identity table stays unwired until the Lab or judge calls it.
- `known-5`, `known-7`, `p0a-15` to `p0a-20`, and every `leave` row, unless a PR touches the line anyway. R23 touches `p0a-20`.
- The market board stays unwired, by TR:49.
- Rows no block names stay in `A/FINDINGS.tsv`. Appendix E lists them, so nothing is silently lost.

**Lines of the old plan that change.** `A/plan-current.md` is the copy of `P/build/UNIT-PLAN.md` these line numbers read. Do not edit `UNIT-PLAN.md` from a build branch. Whoever picks up those sections reads these lines first.

| Section and line | It said | It now says |
| --- | --- | --- |
| C-14 You see, `:3787` | After he lands the stack and signs in once, his practice node trades the dummy unit on his demo account | After he lands the stack and signs in once, one script proves his node is ready to receive a unit. No unit reaches a node without passing the judge and his click |
| C-14 Build, `:3783` | "Code he has landed" means a commit on `origin/main` | The landing check takes the branch by `--landed-on`, default `engine/base` |
| C-14 lane 5, `:3799` | The real run on his folder, pass when every line reads PASS | The same, and every line reads PASS with the plain "no unit" line when no unit has passed the judge. It no longer implies any unit traded |
| C-15 Build, `:3837`, and its unit test, `:3845` | Each mark rehearses against the conformance venue | Each mark rehearses on R20's harsher fake cTrader over the real codec, because `ConformanceAccount` speaks no cTrader wire |
| C-20 gate, `:4169` | Dispatch when `c14-real.log` and `c15-demo.log` read all PASS, as evidence the new node "traded on demo" | The same two logs, as he ruled. `c14-real.log` proves this machine's node is ready and its test trade traded, and `c15-demo.log` proves attribution, duplicates, the cut and the refresh on demo. Neither implies a unit traded |
| C-20 Files, `:4173` | `qmn/FAILURES.md` stays, because `alerts.py:249-251` reads it | R16 moved it to `qmn/src/qmn/observability/FAILURES.md`, which is one of the kept files there. C-20 also moves `sqs_baseline_producer.py` out before it deletes `qmn/host` |
| C-30 lane 4, `:4654` | Pass when the next alarm uses the new key without a restart | Pass when the setup says the new key is read at the next safe restart, and the first alarm after that restart uses it |

## Appendix C. Files two PRs share

`assemble.mjs` generates this table from every Files block. Two PRs on one row never run at the same time, and the stack is linear, so the later one rebases on the earlier. The crowded ones are `qmn/src/qmn/app/runtime.py`, `qmx-agents/packages/qmx-host/src/qmx_host/host.py`, `qmx-agents/packages/qmx-host/src/qmx_host/first_start.py` and `qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py`. A PR that adds a setting may also edit `qmx-agents/packages/qmx-control/src/qmx_control/service.py` for its default, so the coordinator treats that file as shared by every such PR. A PR that changes an app folder also edits `test_shipped_apps.py`, which is why that file sits on so many rows. A PR that changes a library in the trading node's lock also edits `qmx-agents/apps/trading-node/app.toml`, by call 11.

| Path | PRs |
| --- | --- |
| `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` | R03, R04, R05, R06, R07, R08, R09, R10, R11, R12, R15, R16, R18, R19, R20, R21, R22, R23 |
| `qmx-agents/apps/trading-node/app.toml` | R04, R05, R06, R08, R09, R10, R11, R15, R16, R19, R20, R21, R22, R23 |
| `qmx-agents/apps/qmb/app.toml` | R04, R05, R07, R08, R09, R10, R11, R12 |
| `qmx-agents/packages/qmx-host/src/qmx_host/host.py` | R06, R07, R08, R10, R12, R18, R23 |
| `qmx-agents/apps/qmb/tests/test_qmb_app.py` | R04, R05, R07, R08, R09, R10 |
| `qmn/src/qmn/app/runtime.py` | R15, R20, R21, R22, R23 |
| `qmx-agents/apps/qmb/jobs/backtest.py` | R07, R08, R09, R10, R12 |
| `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py` | R06, R08, R10, R11, R12 |
| `qmb/src/qmb/host/unit_runner.py` | R08, R09, R10 |
| `qml/src/qml/compile/compiler.py` | R04, R05, R06 |
| `qml/tests/test_nothing_silent.py` | R04, R05, R06 |
| `qmn/src/qmn/venue/ctrader_account.py` | R20, R22, R23 |
| `qmx-agents/apps/qmb/jobs/robustness.py` | R08, R10, R11 |
| `qmx-agents/packages/qmx-control/src/qmx_control/service.py` | R03, R06, R07 |
| `qmx-agents/packages/qmx-judge/src/qmx_judge/judge.py` | R10, R11, R12 |
| `qmb/src/qmb/robustness/unit_battery.py` | R10, R11 |
| `qmb/tests/test_run_journal.py` | R05, R15 |
| `qml/src/qml/protocol/unit.py` | R04, R05 |
| `qml/tests/test_compile_dummy.py` | R04, R05 |
| `qml/tests/test_wave1_exits.py` | R04, R06 |
| `qml/tests/test_wave1_statistics.py` | R04, R06 |
| `qmn/src/qmn/app/feed_keeper.py` | R19, R23 |
| `qmn/src/qmn/app/operations.py` | R16, R21 |
| `qmn/src/qmn/app/reconciler.py` | R20, R23 |
| `qmn/src/qmn/app/stand_down.py` | R21, R23 |
| `qmn/tests/test_app_binding.py` | R20, R24 |
| `qmn/tests/test_app_stand_down.py` | R21, R23 |
| `qmx-agents/apps/qmb/jobs/sweep.py` | R08, R12 |
| `qmx-agents/apps/qmb/qmb_tester.py` | R10, R12 |
| `qmx-agents/apps/qmb/tests/test_qmb_run_kinds.py` | R11, R12 |
| `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/download-dukascopy/scripts/download.py` | R08, R09 |
| `qmx-agents/packages/qmx-engine/tests/test_templates.py` | R12, R13 |
| `qmx-agents/packages/qmx-host/src/qmx_host/connect_node.py` | R03, R07 |
| `qmx-agents/packages/qmx-host/src/qmx_host/first_start.py` | R02, R03 |
| `qmx-agents/packages/qmx-host/src/qmx_host/node_link.py` | R02, R17 |
| `qmx-agents/packages/qmx-host/src/qmx_host/promote.py` | R06, R17 |
| `qmx-agents/packages/qmx-host/tests/test_first_party_node.py` | R02, R03 |
| `qmx-agents/packages/qmx-host/tests/test_harvest.py` | R15, R19 |
| `qmx-agents/packages/qmx-host/tests/test_heartbeats_loop.py` | R02, R23 |
| `qmx-agents/packages/qmx-host/tests/test_promote.py` | R10, R17 |
| `qmx-agents/packages/qmx-tools/src/qmx_tools/journals.py` | R08, R19 |
| `qmx-agents/packages/qmx-tools/tests/test_journal_seal.py` | R08, R19 |
| `tools/first_real_start.py` | R02, R24 |
| `tools/proof_foundation.py` | R14, R24 |
| `tools/tests/test_first_real_start.py` | R02, R24 |

## Appendix D. The calls already made

These are the calls in `PLAN-SHAPE.md`, so no builder reopens them.

1. A unit with no price stop refuses for now. Whether such units are allowed is the risk session's.
2. Cadence `at` warns when it sits beside `every_closed_trades`, and refuses only when it is the sole cadence. The dummy uses it.
3. Roles that run are context, location, setup, trigger, confirmation, filter and entry_order. Others refuse.
4. Session blocks refuse until R06 gives them the market's clock. `time` reaches blocks only with that refusal in place.
5. Volume blocks refuse until a later volume repair. Dukascopy's number and a cTrader tick count are different things.
6. The six exits refuse until the risk session agrees the socket.
7. `auto_paper` is deleted. `recheck_units.py` and its tests are cut.
8. `[qmb] bars` stays as the test and hand-saved route. Gather's fixture fallback stays, with a warning that reaches the run.
9. R stays as it is. A cash number sits beside it. Whether R includes costs is the risk session's, behind one named function.
10. No engine change anywhere in this program. His engine items (a), (b) and (f) are withdrawn, because the engine as built does them. A script read of a family's tries waits for the research phase, and he is asked then, once.
11. Supervisor changes in R03 are made for one reason, that a repair must reach him and his kill must never wait on an install. A library repair never rebuilds a signed money app under its signed hash, and it arrives as a new version for him to sign. So any PR that changes a library in `apps/trading-node`'s lock bumps that app's patch version. On those terms the changes break no promise in `ground-core` section 2. Every PR is checked against that list.
12. A stuck install fails at a named setting, default 30 minutes. It stops no usage, so the no-caps rule is not touched.
13. A kill closes every position carrying this node's tag at the scope, hosted or not. Flatten closes positions, does not stop the unit, and never replays after a restart. What each kill level means stays a placeholder for the risk session.
14. The word for a manual position with no stop becomes "not ours, never touched", with "no stop at the broker" added when true. His to change.
15. No keys are passed into a running node. A changed alarm address waits for the next safe restart, and the plan line changes to say so.
16. Waiting lines dropped during an OpenObserve outage are the design, so only the doctor row changes.
17. The first-start script's job is to prove this machine's node is ready to receive a unit. With no unit named it prints one plain line, and that is not a FAIL. The landing check takes the branch by option, default `engine/base`.
18. The uncommitted edit in `D:/QMX-worktrees/bld-us-c14` is left out. R24 writes the login reader's full rule, and the owner lane on a throwaway entry proves it.
19. SQS has no gate built now. The seat is one line in `Runtime.guard`, and the risk session places it.
20. A failure of the safety fact a block names stops that PR and comes back to the coordinator. Nobody works around it.

The plan's writer made these smaller calls so a builder need not ask. Each is cheap to reverse.

- `p1a-4` lands in R06, not R05, because its settle check goes through `check_entry`.
- `p6-2`'s `check.py` and `ready.py` edits land in R13 with `offline_checked`, not in R07, so one PR owns those lines.
- `value-above@1` carries a `below` setting, so "RSI below 30" can be written with the one comparator block.
- The new session blocks take a `clock` of UTC, London or New York, on the clock blocks' civil-date functions, because `zoneinfo` appears nowhere under `qml/src/qml`.
- The app version table holds a line-ending-normal digest, because `core.autocrlf` is true on this PC.
- `known-1` takes both reports' shapes, `amend` answers the broker's stop and a stop past entry answers `Blocked` with its row.
- The setting names are `[apps] install_limit_s` and `[node] record_markets` with `records_refresh_s`.
- The trading node's bump covers a change under a library's `src`, because `path_sources` digests only that folder. A change to a library's tests or examples bumps nothing.
- A usable source for a market's month is the one the request or study names, or `dukascopy` when neither does, holding that month with a stated scale. So two usable sources means the request and the study name different sources, and a copy under any other source is not read.
- The flatten op's done row is a `kill_level` row with no `level`, because that is the row kind with an op id, and R13's watcher reads a row with no `level` as deciding nothing.
- A kill's `positions_closed` stays one count at the rising tick, with its limit named, and no done row is added.

## Appendix E. Every row and where it went

`assemble.mjs` generates this appendix from `A/FINDINGS.tsv`, the Rows lines of each section, `plan-parts/rows-new.tsv` and `plan-parts/rows-out.tsv`, and it refuses to write the plan if a must or should row has no home. The count at this build is must rows 30 of 30 placed, new must rows 3 of 3 placed, should rows 138 of 184 placed and 46 out with a reason, leave rows 10 touched and 66 left.

### Every must row and its PR

| Row | Placed in | The rest waits for | What |
| --- | --- | --- | --- |
| `chief-2` | R16 | nothing, the row closes here | On every installed node his phone alarms are silently off, the node reads its alarm list from FAILURES.md and so on |
| `known-1` | R21 in part | The signed stop distance is the risk session's by his ruling | A stop moved past entry is sent as an unsigned distance, so it lands on the wrong side, and the node then and so on |
| `p0a-1` | R04 | nothing, the row closes here | A unit written as long only still trades short whenever its short side is present, while the checker tells and so on |
| `p0a-3` | R04 | nothing, the row closes here | Parts of the written unit are accepted and silently not run, so it trades and backtests a different strategy and so on |
| `p0b-1` | R07 | nothing, the row closes here | QMB trades on QML's test-fixture contract terms, not his Library's instrument record, the host checks the and so on |
| `p0b-2` | R07 | nothing, the row closes here | A unit on any market that has a Library record but no QML fixture cannot be backtested, the host says it and so on |
| `p0b-3` | R08 | nothing, the row closes here | On a real home the data he downloads can never be backtested, a run reads only hand-saved CSV pairs named for and so on |
| `p0b-4` | R15 | nothing, the row closes here | On the node's live journal, one refused row silently stops every later row while the unit keeps trading, and so on |
| `p1a-1` | R04 in part, R05 in part, R06 in part | Volume blocks, after p0a-14 and the bars work. Time is R05 and and so on | A unit built on VWAP, OBV, MFI, A/D, Force, Chaikin, BW MFI, session high, low or range, initial balance, and so on |
| `p1a-2` | R04 in part | The exits really run after the risk session agrees the socket, steps and so on | A unit that lists a profit cap, ROI table or give-back exit before its time exit loses the time exit with no and so on |
| `p1a-3` | R05 | nothing, the row closes here | A trader's plainest rule, such as ADX above 25, CCI above 100 or Hurst above 0.55, cannot be written with the and so on |
| `p1b-1` | R04 in part | The exits really run after the risk session agrees the socket, steps and so on | Bind any of three shipped exits (roi-table-exit, unrealised-profit-cap, peak-holdings-giveback-exit) in a and so on |
| `p2-4` | R08 in part | Replay against a recorded day, with seams-8, which needs seams-5 first | The nightly replay of a live day and any real backtest read bars only from CSV pairs in a folder nothing in and so on |
| `p34-1` | R15 | nothing, the row closes here | Every trade the node really makes never becomes a Library trade item or a paper-run score, because the node's and so on |
| `p5a-1` | R22 | nothing, the row closes here | A unit promoted on any market but EURUSD after the account is bound never gets a bar, the feed's markets are and so on |
| `p5a-2` | R20 | nothing, the row closes here | If the broker stop fires while his connection is down, the node never learns, after reconnect it still holds and so on |
| `p5a-3` | R21 | nothing, the row closes here | When the unit decides to close and the venue refuses once (a dropped session is enough, and so on |
| `p5a-4` | R21 | nothing, the row closes here | A kill does not close a position of the node's that no hosted unit holds, for example after a code update or and so on |
| `p5a-5` | R22 | nothing, the row closes here | If the node restarts while the internet is not up yet (a PC reboot), the unit is started with an equity of 0 and so on |
| `p5a-6` | R21 | nothing, the row closes here | Flatten answers 'accepted, positions 0' and does nothing at all, he presses it to get out of the market and and so on |
| `p5a-7` | R21 | nothing, the row closes here | After a restart a position of the node's with no stop at the broker is taken over as if it had one, nothing and so on |
| `p5c-1` | R24 | nothing, the row closes here | On his real folder the dummy unit is still a draft with no behaviour report, so the "dummy unit deployed" and so on |
| `p6-1` | R12 | nothing, the row closes here | Run a unit on every market and "Find where a failed unit's rules still hold" always answer "Placed no and so on |
| `p6-2` | R07 in part, R13 in part | R07 and R13 together close it | Build and prove can test a unit only on EURUSD, USDJPY or XAUUSD and only with QML's own blocks, its script and so on |
| `plan-check-1` | R24 | nothing, the row closes here | He lands the stack the way he landed PRs 207 to 234, into engine/base, and the first real start still answers and so on |
| `seams-1` | R24 | nothing, the row closes here | His first real start stops at line six, "dummy unit deployed", because the click is refused unless the dummy and so on |
| `seams-2` | R07 | nothing, the row closes here | A backtest ignores the instrument record his Library holds and copies QML's test fixture instead, so QMB and so on |
| `seams-3` | R15 | nothing, the row closes here | One entry blocked with a reason the journal's closed list does not hold kills that deployment's unit journal and so on |
| `seams-4` | R22 | nothing, the row closes here | A unit promoted on any market but the self-test's EURUSD after the account is bound never gets a price, and so on |
| `seams-5` | R22 in part | The bars he tested on, ground-node D steps 2 and 3, because history and so on | The node builds 15-minute bars for every unit, so a unit backtested on 5-minute or hourly bars silently and so on |

### New rows from the grounding reports

| Row | Grade | Source | Placed in, or waits for | What |
| --- | --- | --- | --- | --- |
| `core-n1` | must | ground-core section 7 | R03 | An install holds the supervisor's lock through uv sync, so every call to every running app waits for it, and so on |
| `core-n2` | should | ground-core section 7 | R13 | The hook runs a bare python, so it works only if the first python on the CLI's PATH is the host's environment |
| `core-n3` | should | ground-core section 7 | A later session may pick it up. The store keeps history, so nothing and so on | A reinstall adds new disabled triggers on every published version and can write the shipped draft over an and so on |
| `core-n4` | leave | ground-core section 7 | Harmless and misleading to read | The settings.memory.scopes key in template definitions is read by no engine code |
| `unit-n1` | must | ground-unit section 7 | R05 | 14 price series fed whole bars never hold a slot, and check stays green |
| `unit-n2` | should | ground-unit section 7 | Repair it with step 2 of ground-unit B, when per-bar exits really run | _Core.timer builds exits on the long side only, so a repair that only feeds evidence gives shorts exits that and so on |
| `unit-n3` | leave | ground-unit section 7 | A dead end for an agent, unless the C-20 cut takes it. Check and so on | The copilot's qml_run row can never succeed, because no code fills ctx.bots |
| `qmb-n1` | should | ground-qmb section 7 | R08 | materialise copies a sealed month into any folder it is given |
| `qmb-n2` | should | ground-qmb section 7 | R07 | A host keeps the first records it compiled against for its whole life |
| `qmb-n3` | should | ground-qmb section 7 | R08 | A study's holdout cannot name a real holdout, because the schema types it as a plain string |
| `qmb-n4` | should | ground-qmb section 7 | R08 | Every job labels fidelity bars while the run replays quotes |
| `qmb-n5` | should | ground-qmb section 7 | R07 | A run on a fixture says nothing, because gather's warnings are dropped in LanderLibrary._compiled |
| `start-n1` | should | ground-start section 7 | R03 | A 30 second stall stops the trading node for good, because call runs self.stop on a tool timeout and a and so on |
| `start-n2` | should | ground-start section 7 | Settle it with the bars repair, since node bars are 15-minute today | Bars the node records cannot be read as bars, because no product code calls append_series, so the MIS on a and so on |
| `start-n3` | leave | ground-start section 7 | R24 | real_bearer ignores UserName |
| `node-n1` | must | ground-node section 7 | R22 | One deployment naming a symbol the broker does not list kills the whole account after a restart |
| `node-n2` | should | ground-node section 7 | R20 | The reconcile row writes the node's memory under venue_stop |
| `node-n3` | should | ground-node section 7 | R20 | A stop he moves by hand in cTrader is never read |
| `node-n4` | should | ground-node section 7 | R20 | A stop fired while the process is down leaves an entry with no exit and no alarm |
| `node-n5` | should | ground-node section 7 | Its effect on a session is a guess until demo, read in Appendix B | _absorb ignores ProtoOAAccountDisconnectEvent, ProtoOATraderUpdatedEvent and ProtoOASymbolChangedEvent |

### Every should row with its PR, or the reason it stays out

| Row | Kind | Placed in | The rest, or the reason it stays out |
| --- | --- | --- | --- |
| `chief-1` | spec-miss | R23 | nothing left over |
| `deletion-1` | dead | not in this body | The old QMB door, about 32,700 plain lines and about 15,500 of methods to read first, on his word, with the and so on |
| `deletion-2` | dead | not in this body | The old node cut, section C-20, on c14-real.log and c15-demo.log reading all PASS, as he ruled |
| `deletion-3` | dead | not in this body | Removing the live lanes, after the demo evidence |
| `deletion-4` | dead | not in this body | The old node cut, section C-20 |
| `deletion-5` | dead | R01 | nothing left over |
| `deletion-6` | dead | not in this body | QMB's usage examples go with the old QMB door |
| `deletion-7` | dead | not in this body | qmf-indicators and qmf-structure, on his word, with the structure ideas written down as a dictionary note and so on |
| `deletion-8` | dead | R01 | nothing left over |
| `deletion-9` | dead | R01 | nothing left over |
| `deletion-11` | dead | not in this body | The old node cut, section C-20, which must also edit the release gate's readers |
| `known-2` | bug | R03 | nothing left over |
| `known-7` | bug | not in this body | Overstated, because qmx-host depends on qmx-tools, which depends on qml. Left out on purpose by the shape |
| `known-10` | bug | R16 | nothing left over |
| `known-11` | bug | R16 | nothing left over |
| `known-12` | bug | R16 | nothing left over |
| `p0a-2` | bug | R04 | nothing left over |
| `p0a-4` | bug | R05 | nothing left over |
| `p0a-5` | bug | R04 | nothing left over |
| `p0a-6` | bug | R04 | nothing left over |
| `p0a-7` | bug | R04 | nothing left over |
| `p0a-8` | spec-miss | R04 | nothing left over |
| `p0a-9` | spec-miss | R04 | nothing left over |
| `p0a-10` | bug | not in this body | A later session may pick it up. Check runs block code in the calling process, and the agent rules rest on an and so on |
| `p0a-11` | bug | R05 | nothing left over |
| `p0a-12` | spec-miss | not in this body | Nothing reads the receipt, so it goes with the risk session's sizer |
| `p0a-13` | spec-miss | R05 | nothing left over |
| `p0a-14` | spec-miss | not in this body | Layer D's fallback and transfer compare, which must land before volume blocks |
| `p0a-21` | test-delete | R04 | nothing left over |
| `p0a-22` | test-delete | R06 | nothing left over |
| `p0a-23` | test-delete | R06 | nothing left over |
| `p0a-24` | test-delete | R04 | nothing left over |
| `p0b-5` | bug | R10 | nothing left over |
| `p0b-6` | bug | R10 | nothing left over |
| `p0b-7` | bug | R10 | nothing left over |
| `p0b-8` | spec-miss | R08 | nothing left over |
| `p0b-9` | spec-miss | R08 | nothing left over |
| `p0b-10` | spec-miss | R07 | nothing left over |
| `p0b-11` | spec-miss | R08 | nothing left over |
| `p0b-12` | spec-miss | R10 | nothing left over |
| `p0b-13` | bug | not in this body | Whether R includes costs |
| `p0b-14` | plan-gap | R10 | nothing left over |
| `p0b-15` | plan-gap | R10 | nothing left over |
| `p0b-16` | bug | R10 | nothing left over |
| `p0b-17` | dead | R08 | nothing left over |
| `p0b-18` | dead | R10 | nothing left over |
| `p0b-23` | test-delete | R06 | nothing left over |
| `p0b-24` | test-delete | R19 | nothing left over |
| `p0b-25` | test-delete | R07 | nothing left over |
| `p0b-26` | test-delete | R10 | nothing left over |
| `p0b-27` | test-delete | R08 | nothing left over |
| `p1a-4` | bug | R06 | nothing left over |
| `p1a-5` | bug | R04 | nothing left over |
| `p1a-6` | spec-miss | R06 | nothing left over |
| `p1a-7` | bug | not in this body | The halt's silence at zero equity, with the halts. Compile refuses all halts today |
| `p1a-13` | test-delete | R04 | nothing left over |
| `p1a-14` | test-delete | R04 | nothing left over |
| `p1a-15` | test-delete | R04 | nothing left over |
| `p1a-16` | test-delete | R06 | nothing left over |
| `p1b-2` | false-green | R04 | nothing left over |
| `p1b-3` | bug | not in this body | Trailing stops, with the exits socket |
| `p1b-4` | spec-miss | not in this body | Partial closes and stop moves from exit blocks, with the exits socket |
| `p1b-5` | plan-gap | not in this body | The identity table stays unwired until the Lab or judge calls it |
| `p1b-6` | false-green | R06 | nothing left over |
| `p1b-7` | spec-miss | R06 | nothing left over |
| `p1b-8` | plan-gap | R23 | nothing left over |
| `p1b-11` | spec-miss | R06 | nothing left over |
| `p1b-12` | spec-miss | R06 | nothing left over |
| `p1b-13` | bug | R06 | nothing left over |
| `p1b-14` | spec-miss | R06 | nothing left over |
| `p1b-15` | spec-miss | R06 | nothing left over |
| `p1b-19` | test-delete | R06 | nothing left over |
| `p1b-20` | test-delete | R06 | nothing left over |
| `p1b-21` | test-delete | R04 | nothing left over |
| `p1b-22` | test-delete | R07 | nothing left over |
| `p2-1` | bug | R10 | nothing left over |
| `p2-2` | spec-miss | R08 in part | Bar rows wire when a one-sided source first needs a run |
| `p2-3` | spec-miss | not in this body | Futures replay, kept and wired later, because no futures data route exists yet |
| `p2-5` | bug | R11 | nothing left over |
| `p2-6` | bug | not in this body | Whether R includes costs |
| `p2-7` | spec-miss | not in this body | Harmless until a second tester exists, then a job door and one read of the setting |
| `p2-8` | spec-miss | R10 | nothing left over |
| `p2-9` | bug | R09 | nothing left over |
| `p2-10` | spec-miss | R07 | nothing left over |
| `p2-11` | bug | R11 | nothing left over |
| `p2-12` | spec-miss | R10 | nothing left over |
| `p2-13` | bug | R09 | nothing left over |
| `p2-14` | bug | R10 | nothing left over |
| `p2-15` | bug | R10 | nothing left over |
| `p2-16` | false-green | R10 | nothing left over |
| `p34-2` | spec-miss | R18 | nothing left over |
| `p34-3` | bug | R18 | nothing left over |
| `p34-4` | spec-miss | not in this body | Block work, and some of what it needs sits in the never-run regime code. Do not delete p34-14 before someone and so on |
| `p34-5` | spec-miss | R19 | nothing left over |
| `p34-6` | spec-miss | R19 | nothing left over |
| `p34-7` | spec-miss | not in this body | The tail file for a server node's open month |
| `p34-8` | bug | R19 | nothing left over |
| `p34-9` | bug | R13 | nothing left over |
| `p34-10` | false-green | R15 | nothing left over |
| `p34-11` | test-delete | R09 | nothing left over |
| `p34-12` | test-delete | R09 | nothing left over |
| `p34-13` | test-delete | R09 | nothing left over |
| `p5a-8` | bug | R22 | nothing left over |
| `p5a-9` | bug | R20 | nothing left over |
| `p5a-10` | bug | R23 | nothing left over |
| `p5a-11` | spec-miss | R23 | nothing left over |
| `p5a-12` | spec-miss | R16 | nothing left over |
| `p5a-13` | bug | not in this body | A later session may pick it up. Reading the journal by after_sequence loses rows, read and not walked again and so on |
| `p5a-14` | bug | R23 | nothing left over |
| `p5a-15` | spec-miss | R22 | nothing left over |
| `p5a-16` | bug | R23 | nothing left over |
| `p5a-17` | bug | not in this body | Partial close on the node, with the exits socket. No unit can ask for one until p1b-4 lands |
| `p5a-18` | bug | R22 in part | The bars he tested on, ground-node D steps 2 and 3, the same cause as seams-5 |
| `p5a-19` | plan-gap | not in this body | Broker history for warm-up, ground-node D step 3 |
| `p5a-20` | spec-miss | R22 | nothing left over |
| `p5a-21` | false-green | R21 | nothing left over |
| `p5a-22` | bug | R23 | nothing left over |
| `p5a-23` | slop | R21 | nothing left over |
| `p5a-29` | test-delete | R21 | nothing left over |
| `p5a-30` | test-delete | R21 | nothing left over |
| `p5a-31` | test-delete | R21 | nothing left over |
| `p5a-32` | test-delete | R21 | nothing left over |
| `p5a-33` | test-delete | R21 | nothing left over |
| `p5a-34` | test-delete | R21 | nothing left over |
| `p5b-1` | spec-miss | not in this body | Perp positions in his market tools |
| `p5b-2` | plan-gap | not in this body | A slice nobody owns, about 300 lines. R20 to R22 keep the VenueAccount seam, so nothing blocks it |
| `p5b-3` | bug | R21 in part | Hyperliquid's real refusal still needs testnet |
| `p5b-4` | bug | not in this body | Only ccxt_client.py, provable on the shipped fake, about 20 lines with p5b-5 |
| `p5b-5` | bug | not in this body | Only ccxt_client.py, provable on the shipped fake, about 20 lines with p5b-4 |
| `p5b-6` | bug | R22 in part | The rest of the row needs a testnet run |
| `p5b-7` | bug | not in this body | One line, which could go any time, kept with the wallet work |
| `p5b-11` | test-delete | R22 | nothing left over |
| `p5b-12` | test-delete | R22 | nothing left over |
| `p5c-2` | false-green | R24 | nothing left over |
| `p5c-3` | bug | R03 | nothing left over |
| `p5c-4` | plan-gap | R24 | nothing left over |
| `p5c-5` | spec-miss | not in this body | Install both pinned programs in that step, so the card does not hold the sign-in card |
| `p5d-1` | bug | R17 | nothing left over |
| `p5d-2` | bug | not in this body | A waiting code must be neither wrapped nor kept, and it bites at G-SERVER only |
| `p5d-3` | bug | R17 | nothing left over |
| `p5d-4` | spec-miss | R08 | nothing left over |
| `p5d-5` | spec-miss | R07 | nothing left over |
| `p5d-6` | bug | R17 | nothing left over |
| `p6-3` | bug | R12 | nothing left over |
| `p6-4` | slop | R12 | nothing left over |
| `p6-5` | spec-miss | R12 | nothing left over |
| `p6-6` | spec-miss | not in this body | Honest "Not judged yet" today, and not foundation, by his word that the dummy need not pass |
| `p6-7` | false-green | R12 | nothing left over |
| `p6-8` | plan-gap | not in this body | Honest drafts or gaps. One engine question for him then, the script read of a family's tries |
| `p6-9` | bug | R13 | nothing left over |
| `p6-10` | spec-miss | not in this body | A new scoring template, late, because nothing he decides rests on it yet |
| `p6-11` | spec-miss | not in this body | A card setting and an almanac template |
| `p6-12` | spec-miss | R13 | nothing left over |
| `p6-13` | bug | R13 | nothing left over |
| `p6-14` | slop | not in this body | The copies are the design, by ground-core block H, so no repair. Do not count those 1,900 lines |
| `p6-15` | spec-miss | R12 | nothing left over |
| `p6-20` | test-delete | R12 | nothing left over |
| `plan-check-2` | plan-gap | not in this body | The guard's rule text goes to the risk session, and C-20 moves sqs_baseline_producer.py out first. The seat and so on |
| `plan-check-3` | plan-gap | R19 | nothing left over |
| `plan-check-4` | plan-gap | not in this body | The server setup's cards |
| `plan-check-5` | plan-gap | R06 | nothing left over |
| `plan-check-6` | plan-gap | not in this body | This program's rule 8 answers it, with few tests across real connections |
| `plan-check-7` | plan-gap | not in this body | The socket gives a sizer no costs and no edge numbers from QMB |
| `seams-6` | bug | R22 | nothing left over |
| `seams-7` | bug | not in this body | Whether a target rests at the broker or the node closes it is an exit rule. Do not change QMB's fill to match and so on |
| `seams-8` | false-green | not in this body | Replay against a recorded day, and it needs seams-5 first |
| `seams-9` | spec-miss | R10 | nothing left over |
| `seams-10` | bug | not in this body | Whether R includes costs, and the misleading name r_after_costs |
| `seams-11` | bug | R22 | nothing left over |
| `seams-12` | plan-gap | not in this body | Warm-up from broker history, ground-node D step 3 |
| `seams-13` | false-green | R24 | nothing left over |
| `triage-1` | bug | not in this body | The signed stop distance. R21 stops it being sent or reported falsely |
| `triage-2` | bug | R09 | nothing left over |
| `triage-3` | bug | not in this body | Two doors, by ground-start H. Promote reads only versions written by the host's C-34 path or by him |
| `triage-4` | bug | R03 | nothing left over |
| `triage-5` | bug | R03 | nothing left over |
| `triage-6` | bug | R08 | nothing left over |
| `triage-7` | bug | R03 | nothing left over |
| `triage-8` | bug | R03 | nothing left over |
| `triage-9` | bug | R16 | nothing left over |
| `whole-repo-1` | bug | R02 | nothing left over |
| `whole-repo-2` | bug | R02 | nothing left over |
| `whole-repo-3` | bug | R02 | nothing left over |
| `whole-repo-4` | bug | R02 | nothing left over |

### Every leave row

These 66 rows stay in `A/FINDINGS.tsv`, left out on purpose unless a PR touches the line anyway. `deletion-12`, `deletion-13`, `deletion-14`, `deletion-15`, `deletion-16`, `deletion-17`, `known-5`, `p0a-15`, `p0a-16`, `p0a-17`, `p0a-18`, `p0a-19`, `p0b-20`, `p0b-21`, `p0b-28`, `p1a-8`, `p1a-9`, `p1a-10`, `p1a-11`, `p1a-12`, `p1b-9`, `p1b-10`, `p1b-16`, `p1b-17`, `p1b-18`, `p2-19`, `p2-20`, `p2-21`, `p2-22`, `p2-23`, `p2-24`, `p34-14`, `p34-16`, `p34-17`, `p34-18`, `p34-19`, `p34-20`, `p5a-24`, `p5a-25`, `p5a-26`, `p5a-27`, `p5a-28`, `p5b-8`, `p5b-9`, `p5b-10`, `p5c-6`, `p5c-7`, `p5c-8`, `p5c-9`, `p5c-10`, `p5d-7`, `p5d-8`, `p5d-9`, `p5d-10`, `p6-16`, `p6-17`, `p6-18`, `p6-19`, `p6-21`, `p6-22`, `plan-check-8`, `plan-check-9`, `plan-check-10`, `plan-check-11`, `seams-14`, `seams-15`.

These 10 rows are closed because a PR touches their line anyway. `deletion-10` in R01, `known-3` in R21, `p0a-20` in R23, `p0b-19` in R08, `p0b-22` in R10, `p1a-17` in R06, `p2-17` in R10, `p2-18` in R11, `p34-15` in R13, `seams-16` in R23 in part.

### The test-delete rows

35 rows hold 1637 lines. 32 rows, 1305 lines, go in the PRs that touch their files. 3 rows, 332 lines, stay, because no PR touches them. `p5c-10`, `p5d-9`, `p6-21`.

## Appendix F. What the risk session gets

The risk session needs nothing from this program to resume. This is what the repairs hand it, in one list. Every value and rule here is theirs, and the plumbing around each is built or marked.

The paths, for a session in another worktree. The placeholder numbers below are in `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/build/RISK-SIZING-PLACEHOLDERS.md`. `CONTRACTS.md` is `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/architecture/parts/A-qml-dictionary-unit/CONTRACTS.md`. `ground-unit` is `D:/QMX-worktrees/audit-ship/reports/ground-unit.md`. `seams/wick.py` is `D:/Temp/audit/seams/wick.py`, and the Arm box copies it to `D:/QMX-worktrees/repair-ship/proofs/seams/wick.py`.

The placeholder sizer is wrong on USDJPY. It divides account money by a loss in the quote currency, so it is right for EURUSD and XAUUSD on a USD account and wrong for USDJPY (`D:/QMX-worktrees/audit-ship/reports/p0a.md:99`). It belongs on the rip-out list.

What compile refuses after R04, with the list in `_shape_problems` (`qml/src/qml/compile/compiler.py:493`), is a unit with no price stop, a second stop, target or per-bar exit, and the six exits by rule, which are `unrealised-profit-cap`, `roi-table-exit`, `peak-holdings-giveback-exit`, `offset-gated-trailing-stop`, `stepped-profit-stop` and `profit-fraction-trailing-stop`. An agent's block of the same shape refuses too. Flatten closes positions and does not stop a unit, by call 13.

- May a stop go past entry, and how is that sent? The signed distance is theirs by his ruling. R21 stops a wrong side being sent or reported, and it answers `Blocked` until they decide. This covers `known-1`, `triage-1` and whether trails on the node can lock in profit.
- Whether a stop may ever widen, placeholder 9.
- Scale-out ladders, and what a partial close means for R, placeholder 10. `p1b-4`, `p5a-17`.
- Whether a target rests at the broker or the node closes it, `seams-7`. One wicked bar read +2.00R against -0.55R in `seams/wick.py`. QMB's fill does not change meanwhile.
- May a unit have no price stop, placeholder 11. R04 refuses it for now, `p0a-8`.
- Whether a moved number changes an open trade's exits, placeholder 8.
- Which exit wins when two fire on one bar.
- Which position facts exits read. `bars_held`, `mfe_r` and `mae_r` from `CONTRACTS.md` 4.3 are not computed today. R10 tracks MAE, MFE and drawdown in R in the handler, adds only, for results.
- The exits socket itself. Step 2 of `ground-unit` B feeds every per-bar exit real evidence and the position's side, about 60 lines, with `unit-n2`, because `timer()` builds exits long-only. Step 3 is trails, partial closes and stop moves, about 250 lines, with `p1b-3`, and it must not ship on the node before the signed distance is answered. `p1a-8` is theirs, a long-wicked bar giving a stop above the close.
- Whether R includes costs, with the name `r_after_costs`, `p0b-13`, `p2-6` and `seams-10`. R10 puts the judge's read behind `trade_r`, so it is one line.
- What each kill level means, YELLOW to BLACK, placeholder 18. R21 makes whatever the table says act, on positions hosted or not.
- SQS, by call 19. The rule text is at `qmn/host/decision_root.py:496-510`, the baseline producer is `qmn/host/sqs_baseline_producer.py`, and the seat is one line in `Runtime.guard` (`runtime.py:2269-2314`). AD-39 and NODE.md section 6 name spread against the unit's cost target as a guard. This is `plan-check-2`.
- The sizer's socket, `plan-check-7`, which gives a sizer no costs and no edge numbers from QMB. The Kelly sizing he asked for needs them. `p0a-12`, the sizer's receipt, goes with their sizer, by adding the residue to `Size`.
- `p1a-7`, the drawdown halt's silence at zero equity, with the halts, which compile refuses today.

## Appendix G. Risks

| Risk | Where it lands | What the coordinator watches |
| --- | --- | --- |
| A proof script in `D:/Temp/audit/` is lost in a clean-up | every lane 2 | The Arm box copies them to `S/proofs/` before anything else |
| His `C:` drive fills, so 106 `qmx-home` backup tests go red | every whole-repo run | `TEMP` and `TMP` on `D:/Temp` before each run, and those reds read as the disk |
| `D:` fills with check worktrees, real months and envs | every lane | Remove each check worktree after its verdict. Below 3 GB free, stop and clean |
| A first-party app bump is forgotten | R04 to R12, R15, R16, R18 to R23 | R03's literal table fails CI when an app folder changes, and tests under an app folder count too. A library change with no bump does not change the folder, so the table cannot see it. The Files block names the bump, and on a real folder the node's status says a library repair waits |
| A money app's version moves with each library repair | R04 to R06, R08 to R11, R15, R16, R19 to R23 | On a real folder M5 waits for his signature, once, for the stack's last version. That is right, and the coordinator tells him at landing |
| The login junction fails at arming, or a clean-up reaches through it | the Arm box, every model lane | The coordinator stops and reports. The boot recipe removes the link first, and on this PC `rm -rf`, `Remove-Item -Recurse -Force` and `shutil.rmtree` left a throwaway target whole |
| A repair to a block changes the dummy's numbers | R04, R05, R06 | `test_compile_dummy.py`, 25 entries and bar 48. A moved warm-up stops the PR |
| The handler is shared, so a QMB change moves the node | R10, R15, R20 to R23 | `seams/parity.py` reads 63 of 63. No repo test holds this |
| Check 18 on `haiku` gives another answer on a rerun | R14 | One rerun, and a second fail counts. It asserts the path, the two bindings, at least one trade and the words, not which verdict |
| The real tick rate is far from the 3.5M guess | R08, R09 | R08's lane 4 records it. If a month through ticks takes over 10 minutes, name it to him as a finding |
| Past closures in a calendar disagree with real data | R09 | Step one's real December. Any hole left is named in the PR body |
| The bounded harvester rewrites a paper score | R19 | `test_a_second_and_third_round_score_the_same_paper_run` must fail against the naive form first |
| The kill's repeated closes hit broker limits | R21 | 5 requests a second per position is left as built. The demo proofs show if cTrader minds |
| A demo answer disagrees with what R20 assumes | after G-DEMO | Read `c15-demo.log`'s answers against R20's history parse, the stop-on-later-event amend, `_close`'s five-second wait, and `node-n5` |
| Lanes that need a network find it down | R08, R09, R14, R18 | The lane logs "network down" and is rerun later, and a saved month stands in where the lane says |
| Templates have no path to his folder at a host start | R12, R13 | The fourth path is `python -m qmx_engine templates install`. R14's lane 6 runs it, and the landing message tells him. A new version waits beside his enabled trigger |
| An uncommitted edit or a venv edit leaks into a branch | every PR | No `git stash`. Worktrees are clean at dispatch, and venv files are never edited |
| The plan grows quietly | every status message | The count of PRs done, left and added ends each message. A new PR needs his word |
| A builder works around a failed safety fact | every PR | Call 20, and the reviewer reruns the fact for real |
