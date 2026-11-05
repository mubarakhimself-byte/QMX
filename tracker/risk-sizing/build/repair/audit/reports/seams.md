The parts fit on the code that decides trades, where QMB and the node agreed on all 63 decisions, but they do not yet fit where a real run feeds that code, and five crossings need a repair before his demo means anything.

Findings: `D:/QMX-worktrees/audit-ship/findings/seams.tsv`. Proof scripts: `D:/Temp/audit/seams/`. Level is the blast-radius level of what I checked.

## The crossings, following one unit

| # | Crossing | What I checked | Level | Fits? | Does a test run both sides for real? |
| --- | --- | --- | --- | --- | --- |
| 1 | Agent door to checker | `unit_new`, `unit_check`, `gather`, QML's check; every problem comes back named | 4, test file passed 8 | Fits | Yes, `test_unit_tools.py` |
| 2 | Checker to compiler | The compiler runs the same layers. It refuses `reads` and `halts` by name instead of ignoring them | 2 | Fits. See p0a-2 and p0a-5 for exit shapes | Yes |
| 3 | Compiler to the unit in the Library | Draft, publish check, compile through a real store | 4, test file passed 8 | Fits | Yes, `test_unit_library.py` |
| 4 | Library to a QMB run folder | What `_lay_out` writes against what the Library holds | 4 | **Does not fit.** Records come from test fixtures (seams-2). No costs or funding (seams-9) | Real, but its store holds the fixtures themselves, so it cannot see this |
| 5 | QMB run to results and journal | The same `RunJournal`, the same row shapes | 2 | Fits | Yes, `test_qmb_app.py` |
| 6 | Results to the judge | Trade and evidence field names on both sides, text not floats | 2 | Fits, but R leaves out commission (seams-10) | Yes, `test_qmb_run_kinds.py:276` |
| 7 | Judge to his promote click | A fresh Library clicked as the first start clicks it | 4 | The rule holds. **It stops his first start** (seams-1) | No. The tests and the rehearsal plant the judge's move and the G report |
| 8 | Promote to deploy on the node | His click's real document into the node's real preflight and compiler | 4 | Fits: preflight clear, same compiled fingerprint | No. `test_promote.py` uses a fake node, and the rehearsal stops at "compiling" (seams-13). Only my script proves it |
| 9 | Same bars to the unit's decisions, QMB against node | The dummy on both, over nine days of the same bars | 4 | **Fits.** 63 of 63 outcomes and numbers equal | **Nothing.** No test compares them. Only my script does |
| 10 | Bar size, unit to node | A 5-minute unit on the node | 4 | **Does not fit.** Always 15 minutes, no refusal (seams-5) | No |
| 11 | Deploy to the feed | A market other than EURUSD, deployed after bind | 4 | **Does not fit.** It goes quiet (seams-4) | No. Conformance venue only |
| 12 | Fills, QMB against node | Entries, stops and time exits on the same bars | 4 | Fits, except a target (seams-7) | No |
| 13 | Order at the venue and its stop | Lots to cTrader volume, stop distance and its sign, digits, the double crossing | 3 | Fits on the fake | The real codec on a fake cTrader. Never a real broker: C-15 is unbuilt |
| 14 | Account facts to the sizer | Equity when the session is down | 4 | **Does not fit** in that case (seams-6) | No |
| 15 | Node's decisions to its journal | Every reason text the node can write against the journal's list | 4 | **Does not fit.** Two reachable texts kill the journal (seams-3) | No test writes those texts |
| 16 | Node's journal to This PC | Real writer, real harvester, real door | 2 | Fits | Yes, `test_harvest.py` and the C-14 rehearsal log. Node rows only in the rehearsal |
| 17 | Home to the live lane's start | Calibration row fields and the unit-version key on both sides | 2 | Fits | The reader is real, the rows are test-written |
| 18 | Home to the replay check | World filter and bar source | 3 | **Does not fit** (seams-8) | No. It runs on a fixture |
| 19 | MIS reading to the unit | `reads`, the board relay, `placement` | 4 | Plain: a unit cannot read one, by compile refusal. Safe by TR:49 (seams-14) | The relay and the node's board read, yes. Promote to placement, no |
| 20 | Venue records to the deployment | C-34's record fields through the node's record parser | 4 | Fits | Yes, the rehearsal lands them through C-34's path |

Crossings nothing proves today, apart from my scripts: 7, 8, 9, 10, 11, 12, 14, and 15 on those texts.

## What I found sound

- **The worst seam is not broken at its centre.** QMB and the node run one handler and one unit door. On the same bars every decision outcome and every number in force was equal, 63 of 63. All 8 trades matched on entry, exit kind and size, and 7 matched to the cent.
- The compiled fingerprint is the same on This PC, in QMB and on the node. Block bytes survive the trip by fingerprint.
- His click cannot be skipped. A draft is refused, and so is a unit with no passing G report. Agents have no route.
- Lot, tick and stop-distance units agree from record to sizer to cTrader volume. Percent is a fraction on both sides. Bar times agree at 15 minutes.
- Refusals at promote are plain sentences with a next step. A node that is away queues the click, and a queued deploy the node later refuses reads back as refused.
- What the compiler cannot run, it refuses by name. Halts and readings are not silently ignored.

## Must

- seams-1: His first real start stops at "dummy unit deployed", because only the rehearsal planted the `tested` move and the G report.
- seams-2: A backtest copies test-fixture instrument records over his Library's, and any market without a fixture cannot run.
- seams-3: One entry blocked with an unlisted reason kills that unit's journal for good, while it keeps trading and reads "Trading".
- seams-4: A unit promoted on XAUUSD after bind never gets a price and reads "warming up 0 of 921" for ever.
- seams-5: The node feeds every unit 15-minute bars, whatever bar it was backtested on, with no refusal.

## Should

- seams-6: A unit that starts while the broker is unreachable sizes from equity 0 for ever and skips every entry.
- seams-7: QMB books a target at its exact price, while the node closes at market after the bar. One wicked bar read +2.00R against -0.55R.
- seams-8: The replay check finds nothing to compare on demo, and would not replay the node's own bars.
- seams-9: Real backtests pay only the spread. Costs, funding and swaps never reach the run folder.
- seams-10: `r_after_costs` and the judge's R leave out commission and swap.
- seams-11: A restart silently throws away what a unit calibrated.
- seams-12: The dummy places no order for about 10 market days after first start, because it warms up 921 bars only from its own recording.
- seams-13: The deploy check prints PASS while the node is still compiling.

Three `leave` rows are in the file: seams-14, seams-15, seams-16.

## Set aside for him

- Must a placeholder dummy earn a passing verdict before it may reach paper? I assumed yes, since US:46 and the lifecycle table say so, and that the first-start script should run that study or say up front that it is needed. If he only wants to see the machine work on demo, he needs to allow a labelled shortcut for the dummy, and that is his call.
- Should targets rest at the broker, or stay closed by the node after the bar? I assumed the node's way stands until the risk session, since exits are theirs (US:306).

## Needs a long run

None. Every proof ran under two minutes. A real check against his broker waits for C-15 and his demo sign-in.

## Not reached

- Contract versions stated on connect, and the refusal on a mismatch (V-H).
- Server paths: C-17, C-19, and This PC reaching a remote node.
- Hyperliquid and CCXT order paths.
- Kill and resume across a node that is away.
- Reading history through `readings_query`, and the slow-lane templates beyond s5.
