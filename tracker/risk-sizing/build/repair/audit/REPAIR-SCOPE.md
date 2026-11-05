# Repair scope

**Superseded on 5 November by his word, foundation before demo, and by `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/build/repair/REPAIR-PLAN.md`. Do not plan from this file.** It stays as last night's view. Grounding corrected it in four places: one comparator block alone gives 0 trades without the feeder rule, the 1,900 template lines stay because the copies are the design, engine items (a), (b) and (f) are not needed, and the old QMB door is about 48,200 lines, not 78,000.

Scope only, for a later session to plan. Nothing here has started. He decides in the morning. Ids point at rows in `FINDINGS.tsv`. Sizes are rough guesses.

## The smallest path to his first real start

"First real start" means the one script he runs after landing, `tools/first_real_start.py`, ending with the dummy unit trading on his cTrader demo account and its records home on This PC.

What must be true, in order:

1. The stack is landed on a branch the script accepts. Today it accepts only `origin/main`, which is 2,277 commits behind `engine/base`.
2. The install and the host start cannot hang or stop halfway, and his login is found. The login reader has never been run on a real machine, and an uncommitted edit to it sits in `D:/QMX-worktrees/bld-us-c14`.
3. The dummy may reach paper. Today only the judge can make it `tested`, and only the rehearsal plants that row and the behaviour report.
4. The dummy places an order within a day or so. Today it waits about 10 market days for 921 bars from its own recording.
5. What happens is recorded and reaches him: journal rows, trade records, phone alarms.
6. He can leave it running: the node keeps a true picture through a dropped connection or a restart, and the kill and flatten act.

Cluster 1 gets items 1 to 4. Cluster 3 gets item 5. Cluster 2 gets item 6. Clusters 1 and 3 let him start and watch. Cluster 2 lets him walk away. Then C-15 and his demo sign-in, which the plan calls G-DEMO.

Clusters 4 and 5 are what let him research a real unit. They are not needed for the first start, and they are the first thing he will want after it.

## The clusters

30 must rows come from 18 causes. Every must row is in exactly one cluster. Every should row named here is one I judge worth doing in the same pass. The rest of the 184 should rows stay out until something needs them.

### 1. The first real start runs to its end

Goal: on a fresh folder, with no planted rows, the script reaches PASS on every line, or tells him the one next step.

- Must: plan-check-1 (branch), seams-1 and p5c-1 (the dummy is a draft).
- Should: seams-13 and p5c-2 (deploy reads PASS while compiling), p5c-3 (one failing app stops the rest), known-2 (install can wait for ever, the PR 327 review's blocker), seams-12 and p5a-19 (broker history for warm-up), triage-7 (repairs never reach an installed app), whole-repo-1 and whole-repo-2 (red gates on the script), the uncommitted login edit.
- Files: `tools/first_real_start.py`, `qmx_host/first_start.py`, `qmx_apps/supervisor.py`, `qmn/app/runtime.py` warm-up, `qmn/venue/ctrader_account.py` history.
- It worked when: the rehearsal passes with its two fixture rows removed, and then `c14-real.log` reads all PASS.
- Size: about 400 lines. Needs his answers on the branch and on the dummy.

### 2. The node keeps a true picture when things go wrong

Goal: a dropped connection, a refused order or a restart cannot leave a position he does not know about, or a word on screen that is false.

- Must: p5a-2 (stop fired during an outage goes unnoticed), p5a-3 (a refused exit is lost), p5a-4 (kill misses a position no unit holds), p5a-5 and seams-6 (restart before the network starts on equity 0), p5a-6 (flatten does nothing and says done), p5a-7 (restart adopts a position with no stop), known-1 (the node reports a stop the broker does not hold; the signed distance itself is the risk session's by ruling).
- Should: p5a-8, p5a-9, p5a-10 (five sign-ins a second), p5a-14, p5a-20, p5a-21, p5a-22, p5a-11 (clock stand-down cannot fire), seams-11 and p5a-15 (restart loses calibration silently), p5d-1 and p5d-3 (a timed-out or later-refused deploy), chief-1 (facts stamped verified).
- Files: `qmn/app/runtime.py`, `reconciler.py`, `operations.py`, `stand_down.py`, `qmn/venue/ctrader_account.py`, `qmx_host/promote.py`, `node_link.py`.
- It worked when: the fake cTrader can lose an execution event, refuse a socket and restart mid-position, and each must above has a test on it that fails today. This is the one place new tests earn their cost.
- Size: about 700 lines of product and 300 of fake and tests. The largest cluster. It could split in two.

### 3. What the node does gets recorded and reaches him, on the market and bar he asked for

Goal: a unit on any market and bar runs on that market and bar, and every trade, row and alarm arrives.

- Must: seams-3 and p0b-4 (one unlisted reason silences the unit journal), p34-1 (trades never become Library items or paper scores), chief-2 (phone alarms off on an installed node), p5a-1 and seams-4 (markets fixed at sign-in), seams-5 (every unit gets 15-minute bars).
- Should: p34-10 (the tests that hid p34-1), p5a-12, p34-2 and p34-3 (the MIS is never told what to read, and one read error kills its round), triage-5 (a database row four times a second), triage-4, known-10 to known-12 and triage-9 (deep logs), whole-repo-3 and whole-repo-4 (red gates).
- Files: `qmb/results/journal.py`, `qmn/app/server.py`, `qmn/venue/ctrader_account.py`, `qmn/observability/alerts.py`, `qmx_apps/supervisor.py`, `qmx_host/app_logs.py`, `apps/mis/server.py`.
- It worked when: a built wheel loads the alarm list, XAUUSD deployed after sign-in gets bars, a 5-minute unit gets 5-minute bars or a refusal, and a real journal row becomes a Library trade.
- Size: about 300 lines.

### 4. A backtest runs on his own data and his own instrument facts

Goal: he asks the copilot to backtest a unit on a market and window, and it runs on what the Library and market store hold, with its real costs.

- Must: seams-2, p0b-1, p0b-2 and p6-2 (the run folder copies QML's test fixtures, and any other market cannot run), p0b-3 and p2-4 (data he downloads never reaches a run).
- Should: p2-2, p2-3, p0b-9 (one market of a unit), p0b-10 and p2-10 (the one-line gap rule he already decided), p0b-11 and triage-6 (holdouts), triage-2 (past holidays read as holes), seams-9 and p2-8 (only the spread is charged), seams-10, p0b-13 and p2-6 (R leaves out costs, needs his answer), plan-check-3 and p34-5 (nothing writes the market journal), p2-9, p0b-8, p0b-12 and p2-12 (placeholders hidden), p0b-14, p0b-16, seams-7, seams-8, p5d-4, p5d-5, triage-8.
- Files: `qmx_host/host.py` run layout, `apps/qmb/jobs/backtest.py`, `qmb/host/unit_runner.py`, `qmb/host/replay.py`, `qmx_host/venue_records.py`, the market journal writer.
- It worked when: a backtest of a market with no QML fixture, on data the download template stored, lands a result naming its data and costs.
- Size: about 700 lines. Decide here whether B4's unused 650-line entry gets wired or cut (p0b-17).

### 5. What a unit says is what it runs

Goal: check and compile refuse what a unit cannot run, and the plain things a trader writes do run.

- Must: p0a-1 and p0a-3 (direction, sessions and market settings accepted and ignored), p1a-1 (volume and clock blocks never get a value), p1a-3 (no way to say "ADX above 25"), p1a-2 and p1b-1 (exits that never fire).
- Should: p0a-2, p0a-5, p0a-6, p0a-7, p0a-8, p0a-9, p0a-11, p1a-4, p1a-5, p1a-6, p1b-2, p1b-3, p1b-4, p1b-11, p1b-12, p5a-17.
- Files: `qml/compile/compiler.py`, `qml/protocol/unit.py`, one new comparator block, `qml/check/`.
- It worked when: each proof in `D:/Temp/audit/p0a/proof1.py` and `D:/Temp/audit/p1a/proof_units.py` gives a refusal or a working trade.
- Size: about 60 lines for the first step, refusing at compile, which removes the false comfort on its own. About 400 for making the blocks and exits really run. The exit half overlaps the risk session, so agree the socket with it first. Repair p1b-3 and p1b-4 together with the signed stop distance (known-1, triage-1), because a trailing stop on the loss side starts the day those two work.

### 6. Workflow verdicts are true

Goal: templates that judge a unit say what happened.

- Must: p6-1 (a unit that traded gets "Placed no trades" and a false death certificate).
- Should: p6-3, p6-4, p6-6, p6-7, p6-9, p6-12, p6-13, p2-5, p2-11, p1b-13, p1b-14, p1b-15, p34-4, p34-9. Later, with his engine list after G-DEMO: p6-5, p6-8, p6-15.
- Size: about 300 lines, and about 2,000 removed by p6-14.

### Not before a later gate

- Before any live account: triage-3 (an agent can put any record but a unit on the Library's main line, so a wrong record reaches a deploy), p5d-6 (a settings row with no venue skips the demo check on the agents' cTrader tools), and C-21.
- At the server gate: plan-check-4 and p5c-5 (one click, his ruling), C-19, p5d-2, p34-6, p34-7.
- At the wallet gate: p5b-1 to p5b-7.

## The added sections

All 18 stay. Each auditor who answered for one said keep, and the plan check found each came from a review finding, a plan gap or his request. They are C-12d, C-12e, C-25, C-26, C-26b, C-27, C-27a, C-28, C-29, C-30, C-31, C-32, C-33, C-34, C-35, C-36, C-37 and C-38. None to cut. Folding them now would be churn, because they are built. Several need repair inside them: C-29 (p5a-1), C-12e (p5a-2), C-35 (p5a-4), C-30 (p5a-12), C-34 (p5d-5), C-36 (p5d-6). The 9 fix PRs also stay. One of them, fix-qmbapp, carries the gap rule he overruled (p0b-10).

## PR 327 and PR 328

PR 327 (C-35, C-29, C-38). Its review says not clean, for one blocker, the install wait (known-2), in a file the PR does not touch. Its own three sections work on the fake. This audit adds that the kill misses unhosted positions, and that the market filter fails on a real binding. Keep it. Stack it, and repair the rest in clusters 1 to 3 on top.

PR 328 (C-14). No review, and its body is still a placeholder. Its rehearsal passes only because a lane plants two rows, so it hides a must. Keep the script, because 8 of its 9 steps hold up. Do not treat it as proven. Land it only with cluster 1. Review the uncommitted login edit in that worktree before anyone discards it.

## The four unbuilt sections

- C-15, demo proofs: still wanted. Build it right after cluster 1 and run it at G-DEMO. It settles things no fake can: whether a fill carries the stop, what a close on a gone position answers, and whether `traderId` equals `ctid`.
- C-19, server update and files: still wanted, at G-SERVER. Without it a server node answers `files_missing`, so a server cannot yet trade.
- C-20, the old node cut: still wanted, after `c14-real.log` and `c15-demo.log`. Before it runs: decide SQS, because C-20 deletes the only gate; widen its list (deletion-4); add `tools/release_gate.py:169` and `release/install.py:341` to its readers (deletion-11). Skip the two moves it asks for (deletion-12).
- C-21, live binding: later, by his ruling. Its test asks for an engine refusal he said not yet to, so write it as a labelled placeholder (plan-check-8).

## Deletion plan

Nothing goes before the stack lands, because he lands it himself. Total about 251,000 of 565,000 lines of product Python, plus about 42,000 lines of tests that go whole with them.

| When | Lines | What |
| --- | --- | --- |
| Now | about 55,000 | Probes 21,364, `qmf-indicators` and `qmf-structure` 13,979 (his word first), QML and QMF usage examples 10,166, the retired factory `adws` 8,883, Hermes dump scripts 300 |
| After his first real start | about 41,000 | Live lanes in `scripts/live` 40,660 |
| After the demo evidence | about 77,000 | Old node shell 47,507, old node leftovers C-20 does not list 29,160 |
| After the demo evidence, on his word | about 78,000 | Old QMB door 63,840, QMB usage examples 14,305. No plan section covers these. The first figure is an upper bound: `qmb.data.generate` and `qmb.runloop.stream` are used by tests of living behaviour, so they stay or get repointed |

The guarded parts stay: the workflow engine, the mini-app core, the Library and the local-first stack. `qmf-risk` stays for the risk session. A further 12,800 lines of `qmf-data`, `qmf-risk` and `qmf-registry` lose their callers later, and nobody should cut those on a graph alone. Inside the build, p6-14 removes about 1,900 lines of copied template scripts, and p0b-17 may remove 650.

## Test verdict

About 1,030 of the build's test functions were read. None is hollow, and the 8 I sampled at random agree. 35 rows name about 80 functions that could go, 1,637 lines of about 42,500, or 4%. By part: p0b 547 (mostly B4, only if it is cut), p6 305, p34 221 (three calendar files), p1a 161, p5a 131, p1b 77, p0a 70, p5d 58, p5c 34, p5b 24, p2 9.

Removing them changes little. The real weakness is that green tests did not stop 30 must rows, because each part's tests use a fake of the next part that is kinder than the real one, or plant a row the real path never writes. So the repair is a few tests across real connections, named in the clusters, and no broad new test work. The larger cut is the 42,000 lines that go with dead code, and up to about 60,000 more touching it that need sorting when it goes.

## Old loose ends

1,201 items in the build's lists come to 9 real problems (triage-1 to triage-9), all placed above. 816 are not worth doing. 111 are already fixed. Those lists need not be read again. 9 stayed unknown, and six of those matter enough to look at during cluster 2 or 4. They are at the end of `reports/triage.md`.

## For the risk session

Not repairs here. Pass these on: a unit with no price stop (p0a-8), the placeholder sizer wrong on USDJPY (`reports/p0a.md`), costs and edge numbers missing from the sizer (plan-check-7), targets resting at the broker or closed by the node (seams-7), the signed stop distance (known-1), where SQS sits (plan-check-2).
