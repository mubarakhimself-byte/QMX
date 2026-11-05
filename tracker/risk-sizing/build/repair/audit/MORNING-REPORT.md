# QMX audit: morning report

## 1. The answer

The parts are well built and the connections between them are not finished, so QMX cannot start and run for you today. Trust the core of it: no part needs a rewrite, and the backtest and the node decide trades the same way. Answer two questions below, then have three repair PRs built, after which you can start the first real run on your demo account.

## 2. By part

| Part | What it should do | Verdict | Must fix | Lines that could go |
| --- | --- | --- | --- | --- |
| The unit and QML core | Check, compile and run a unit | Repair | 2 | 70 |
| The dictionary's first content | 102 working blocks and their pages | Repair | 3 | 2,591 |
| QML's checker, catalogue and numbers | Versions, lifecycle, search, the risk socket | Repair | 1 | 526 |
| The dummy's backtest | Run a unit in QMB and file the result | Repair | 4 | 1,272 |
| QMB in depth | Costs, data, judge, other run kinds | Repair | 1 | 227 |
| Journals, copilot, MIS | Records, agent help, market readings | Repair | 1 | 9,102 |
| The trading node | Hold units, send orders, kill, heal | Repair | 7 | 216 |
| Venues and broker links | cTrader stop moves, Hyperliquid testnet | Repair | 0 | 30 |
| Starting QMX and connecting a node | First start, keys, the first-start script | Repair | 1 | 34 |
| Promote, records, feeds, servers | Your click to a running deploy | Repair | 0 | 86 |
| Workflow templates and mini apps | Slow work between sessions | Repair | 2 | 3,020 |
| Across parts, the plan, this audit | Connections and findings outside one part | | 8 | |

Total 30 must rows, from 18 causes. Every part reads Repair and none needs a rewrite. Two parts have no must, and their defects can wait.

## 3. Does it fit together?

Where the code decides trades, yes. I ran the same dummy unit over the same nine days of synthetic bars through QMB and through the node, and all 63 decisions and every number matched. All 8 trades matched, 7 of them to the cent, and the eighth differs because a target closes differently. But a backtest does not yet behave like live trading, because of what each side is fed. A backtest copies test facts in place of your instrument records and pays only the spread. The node gives every unit 15-minute bars, whatever bar it was tested on. Target fills differ too: one wicked bar read +2.00R in QMB and -0.55R on the node. The servers and a kill across a node that is away were not reached.

## 4. What must be fixed before the first real start

All below were confirmed by running them, except the first, walked through the code because that script must not run tonight. None stayed unproven. These stop or spoil the first start:

- The first-start script only accepts code landed on `main`, and it refuses anything else.
- The script stops at "dummy unit deployed", because the dummy is a draft. The rehearsal passed only by planting two rows by hand.
- A unit on any market but EURUSD gets no prices after sign-in. It reads "warming up 0 of 921" for ever.
- On an installed node your phone alarms are off, with one hidden log line. I found this one myself, so no second agent checked it.
- One blocked entry with an unlisted reason silences that unit's journal until the next restart, while it keeps trading and reads "Trading".
- Trades the node makes never become Library trades or paper scores.

These hurt once it is running, and they should be fixed before you leave it alone:

- A stop that fires while the connection is down goes unnoticed, and the node then holds a position that no longer exists.
- A refused exit is thrown away with no retry and no alarm.
- RED does not close a position no running unit holds, yet it answers RED.
- A restart before the internet is back starts the unit on equity 0. It reads "Trading" and never enters.
- Flatten answers "accepted" and does nothing.
- After a restart, a position with no stop at the broker is taken over with no repair and no alarm.
- A unit tested on 5-minute or hourly bars silently trades on 15-minute bars.
- A stop moved past entry goes to the wrong side, and the node reports the stop it asked for. No shipped unit does this yet. The sign belongs to the risk session.

These stop research, and they are not needed for the first start:

- A backtest uses test facts instead of your Library's instrument record, and any market without such a fixture cannot run.
- Data you download can never reach a backtest. Runs read only hand-saved files with exact names.
- A unit's direction, sessions and per-market settings are accepted and ignored.
- 21 volume and clock blocks never get a value, and "ADX above 25" cannot be written. Check stays green.
- Six of the new exits never fire, and one can switch off the time exit.
- "Run on every market" reads "Placed no trades" for a unit that traded, and it lands a false death certificate.

## 5. The repair, in clusters

1. **The first real start runs to its end.** About 400 lines. Needs your answers 1 and 2 below. Also gives the dummy broker history, because today its first order is about 10 market days away.
2. **The node keeps a true picture when things go wrong.** About 1,000 lines with a harsher fake broker. The largest. Could be two PRs.
3. **What the node does gets recorded and reaches you, on the market and bar you asked for.** About 300 lines.

4. **A backtest runs on your own data and instrument facts.** About 700 lines.
5. **What a unit says is what it runs.** 60 lines to refuse what it cannot run, then about 400 to make it run. Agree the exit half with the risk session.
6. **Workflow verdicts are true.** About 300 lines, and about 2,000 removed.

Clusters 1 and 3 let you start and watch. Cluster 2 lets you walk away. Then you sign in to your demo account and run the demo proofs, which are still unbuilt. Clusters 4 to 6 come after.

The two PRs never stacked: keep both. PR 327 (kill, market choice and installed-node data) goes in as it is, with its review's one blocker, the install that can wait for ever, in cluster 1. PR 328 (the first-start script) has no review and hides a must, so land it only with cluster 1. An uncommitted edit in its worktree changes how the script finds your login, and no run has proved that lookup, so look at it before anyone throws it away.

All 18 added sections stay. All 9 fix PRs stay. Of the four unbuilt sections, the demo proofs come right after cluster 1, server updates wait for your server, the old-node cut waits for the demo evidence, and the live path comes later as you ruled.

## 6. What can be deleted

About 251,000 of the 565,000 lines of product Python, plus about 42,000 lines of tests that go with them. Your "97,000 lines is too much" was right: the new node needs about 21,500 of them.

| When | Lines | Biggest groups |
| --- | --- | --- |
| Now, after you land | about 55,000 | Old probes 21,364, two unused packages 13,979 (your word first), usage examples 10,166, the retired factory 8,883 |
| After your first real start | about 41,000 | Build-time live checks 40,660 |
| After the demo evidence | about 77,000 | Old node shell 47,507, old node leftovers the plan missed 29,160 |
| After the demo evidence, on your word | about 78,000 | Old QMB door 63,840 (an upper bound), QMB examples 14,305 |

The workflow engine, the mini-app core, the Library, the local-first stack and `qmf-risk` stay. The old node cut must wait for your SQS decision, because it deletes the only SQS gate.

## 7. Tests, slop and the plan

**Tests.** You were right not to trust them, and wrong about why. The build added 989 test functions. Auditors read about 1,030, counting moved ones, and none is hollow. I sampled 8 at random and agree. Only about 80 functions, 1,637 of 42,500 lines (4%), could go. Your "no hundreds of tests" ruling was not kept, but cutting them would fix nothing. 12,972 tests passed with these 30 must rows underneath, because tests use fakes kinder than the real thing, or plant rows the real path never writes. The fix is a few tests across real connections.

**Slop.** No. The auditors' guess for a plain version is about 60,000 lines against 74,000, and no whole layer could go. The real weakness is parts finished and tested that nothing calls: a 650-line data entry, the market board, the tester-approval pack, the identity table. The real fat is the old code in section 6.

**The plan.** Largely faithful, and all 27 additions earned their place. Four things got lost or softened. SQS appears nowhere in the plan. Nothing writes the market journal, so costs stay uncalibrated. "One click" for a server still has five cards. The first-start script names `main`, against your ruling. Of the old loose ends, 1,201 items come to 9 real problems, all now in the repair list. You need not read those lists again.

## 8. How far to trust this audit

Nobody started QMX tonight, so startup problems were found by reading and short tests, not by running it.

- **Known defects.** The auditors found 4 of 12 known defects that were kept from them as a test. All 3 serious ones were seen, and 2 were filed. Below that they filed 2 of 9. So trust the must list as real, but not as complete. "Sound" means nothing serious turned up.
- **One "this is fine" was wrong.** The log shipper was called sound, and a focused read of it found three defects. The promote part had 86 files, and a wide read misses things.
- **Refuted must rows.** None. Two verifiers reran the proofs on 34 rows. They lowered 6 to should: a unit with no time exit (it fails loud), the tuning rule on shorts (placeholder only), backtest memory, no data card in real runs, futures replay, and the MIS never being configured (the copilot can do it).
- **Spot checks.** I checked one "this is fine" per part, plus the seams and deletion claims, by code or by running it. All held, including the 63 of 63 and a test that rewrites future bars and finds no look-ahead. A thinned copy of the node passed 140 tests, and its 18 alarm failures led me to the phone-alarm defect.
- **Skills check.** Every part passed on skills and on opening every file. The deletion auditor shows one false alarm, marked partial: the words "uv run" sat inside a search pattern, and the guard refused the command.
- **Whole-repo run.** 12,972 passed, 3 failed, 85 skipped, in about 2 hours. Two failures were known. The third is known, plus new hits on the first-start script. Type and lint checks are red on the root, apps and host packages.
- **Not run.** The first-start script, the real login reader, two real hosts, statistics reference data (downloads), and anything reaching a broker.
- **Slips.** One auditor's command held a forbidden Python switch, but a hung step stopped it before it ran, and it was only reading test data. That spelling also gets past the check script, which I left unchanged. Another auditor read its own saved output under `.claude`. I stopped three hung Python stubs. No key was read and no file in the repository changed.
- **Run.** The app refused my request to hold the laptop awake, and I did not retry it. The run was not interrupted. It used 9% of the weekly bar, and every exit line passes.

## 9. What needs you

Two answers before the first repair can be planned:

1. Where does the stack land? I assumed `engine/base`, so the script must learn that branch.
2. May the placeholder dummy reach your demo by a labelled route without passing the judge? I assumed yes, because it will probably never pass. If no, your first start waits for a real unit that passes.

Eleven more can wait, each with a default taken, in `FOR-HIM.md`: SQS timing, the old QMB door, two unused packages, flatten, RED on unheld positions, whether R includes costs, what "live logins never in QMX" means, the MIS widening a unit, the market board, futures, and the batched engine changes. Everything is in `D:/QMX-worktrees/audit-ship/`. Start with `REPAIR-SCOPE.md`.
