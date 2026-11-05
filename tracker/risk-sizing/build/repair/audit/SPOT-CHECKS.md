# Spot checks

## Probe of the auditor agent type (stage 0)

The agent type loaded in this session. Actions 1 and 4 were allowed. Actions 2, 3, 5, 6 and 8 were blocked by the hook. Action 7 was refused by the Python credential guard. That is exactly the result the brief wanted. Tools: Read, Grep, Glob, Bash and Write, plus the harness's own hand-back tool, which writes nothing. It saw no project CLAUDE.md and no memory index.

## Stage 1: the rulings file

Five cited sources picked at random (RC:189, RC:341, US:154, US:207, RC:30) all say what the line claims. Every ruling in `RULINGS-2026-11-04.md` is present except 11c, which is about me. Accepted.

## Stage 4: one "this is fine" claim per part, checked by me

**The dummy unit, QML side (p0a).** Claim: stops sit on the loss side and sizes are exact. I reran the same bars through both sides and hand-checked: a short at 1.06858 has its stop above at 1.06887, 0.00029 x 1.72 lots x 100,000 = 49.88, which is 0.5% of 10,000 less rounding. The node also refuses any stop not on the loss side (`runtime.py:980-982`). Holds.

**The dummy unit, QMB side (p0b).** Claim: a unit reaches `main` only by his click. Ran `test_unit_library.py`, 8 passed, and read the route: the promote route checks the caller's principal against `operator` first (`promote.py:641-646`). Holds. I also read `host.py:1885-1920` for p0b-3: a backtest reads only a CSV pair with an exact window name. Confirmed, the finding is real.

**The blocks (p1a).** Claim: no look-ahead. Blocks only prove half of this, so I tested the whole unit. I drove the dummy over the committed month, then rewrote every bar after the 13th of 25 entries by random factors and drove it again. All 13 earlier entries were identical, and the later ones changed (12 entries became 3), so the check can fail. `D:/Temp/audit/chief/lookahead.py`. Holds.

**The lifecycle (p1b).** Claim: only his click moves a unit toward paper or live. Read `machine.py:104-122`. There is one exception, the judge's tested to paper when `auto_paper` is on. A search of all product code finds that word only inside `machine.py`, and `fold` defaults it to off. No setting can turn it on. So p1b's claim holds in practice and plan-check-5 overstates "anyone who turns it on": it is a small dead branch, not a live door.

**QMB in depth (p2).** Claim: a step that did not run is never a pass. Read `judge.py:586-593`: any `not_run` step gives `incomplete` before `pass` can be reached. Also checked its gap literal by hand: (1.07643 - 1.08510) x 10,000 = -86.70 on 51.00 risked is -1.70R. Holds.

**Journals and agents (p34).** Claim: records coming home from a node are not lost. Read `records.py:1154-1249`. A month is confirmed to the node only after its rows are fingerprint-checked and frozen here, a failure holds the watermark back, and staging files are cleaned on every path. Holds.

**The node itself (p5a).** Claim: one send per order, never a resend. The in-memory `_sent` table (`runtime.py:902`) is lost on a restart, so I looked for a resend after restart. Warm-up replays recorded bars with placing switched off (`runtime.py:1548`, `not self.warming`), so an old decision cannot send again. Holds.

**Venues (p5b).** Claim: Hyperliquid is testnet only. Read `ccxt_client.py:430-456`: sandbox mode is set, then every endpoint is checked and refused if off testnet. Holds. It also passed me a loose end the node auditor had already finished without seeing: `ctrader_account.py:919-954` stamps nine facts as "VERIFIED, read on the cTrader session" when only three come from the session. Real, and I added it as chief-1.

**Start and connect (p5c).** Claim: real mode refuses before it reads a credential. `first_real_start.py:775` runs the landed check before the bearer at `:780`. Holds. Its must is real by reading: the promote click at `:472` needs a tested dummy.

**Promote and records (p5d).** Claim: every caller but `operator` is refused first. Read `promote.py:637-646`: the principal check comes before the body. Holds.

**Templates (p6).** Claim: nothing here moves a unit or an order. Every `app` named in every template definition is `qmb`, none is the trading node, and no template names the promote route. Four templates mention the node only as a need they wait for. Holds at reading level.

**Seams.** Claim: a backtest and the node decide the same. This is the biggest claim in the whole audit, so I read its script and ran it myself: 63 decisions on each side, 63 the same, numbers in force all equal, 8 trades on each side. Seven match to the cent. The eighth is a target trade, 95.38 against 97.25, which is seams-7. Holds on the dummy over nine days of synthetic bars, and only there.

**Deletion.** Claim: `qmf-indicators` and `qmf-structure` are used by nothing. `git grep` outside their own folders and tests finds one file, `qmb/_backends.py:16,19`, and it reads only their version numbers. Nothing outside `adws` imports `adws`. Its table adds up to its headline. Holds.

**The tests.** Eleven auditors found zero hollow tests out of about 1,030 read, which could be agents approving. I drew 8 at random with a fixed seed from 1,008 in whole test files and read them. All 8 call real code and assert literal values. A few are thin round trips, none is hollow. The auditors' count stands. `D:/Temp/audit/chief/sample_tests.py`.

## Where reports disagreed

- Reason table: p0b says it covers all QML and handler texts, seams-3 says two node texts kill the journal. Not a contradiction, p0b did not check node texts. p0b-4 and seams-3 are one defect.
- Same defect, different grade: p5a-5 must and seams-6 should; p5a-18 should and seams-5 must; plan-check-1 must and p5c-4 should. The verifier sees the must row, and I treat each pair as one repair.

## Whole-repo run

Finished in about 2 hours of test time, 12,972 passed, 3 failed, 85 skipped. No red names a keyring outside the one known test. Two of the three are known: the Windows store test the guard refuses, and the upkeep test. The ambient scan is known for its two lanes, but it also hits `tools/first_real_start.py`, which is new (whole-repo-1). Red gates: types on root, format, lint and types on the apps package, lint and types on the host package (whole-repo-2 to 4). The suites the auditors could not finish in time all passed here, including `test_conformance.py`, which p2 asked to run first (qmx-judge 38 passed), `test_app_kill_scopes.py`, and QML's whole suite. The known supervisor and backup-floor reds did not appear this time.

## Long checks

**Deletion, new node on the thinned tree** (`del1.log`): 140 passed, 20 failed, 1 import error, 5 minutes 25. One failure is the known credential guard. The import error is `test_app_partial_fill.py` wanting `qmn.venue.ccxt_client`, which the auditor's copy left out but which it says must stay. The other 18 are alarm tests that fail because the thinned copy cannot find `FAILURES.md`. That is a side effect of the copy's folder, not a need for old code, so the deletion claim stands. No old modules were loaded.

The same 18 pointed at a real defect the auditors missed. An installed node has the same layout as that copy. I built the wheel to scratch: no `FAILURES.md`. The alarm list then refuses and the node turns its phone sender off with one stderr line. Added as chief-2, a must.

**Deletion, QMB tests on the thinned tree** (`del2.log`): 27 passed, 2 collection errors. `test_realism.py` wants `qmb.data.generate` and `test_futures_rolls.py` wants `qmb.runloop.stream`. So the old-door group is not all removable as listed: those two modules hold things tests of living behaviour use. The 63,840 figure is an upper bound.

**Records job cost** (p34-8, `harvest.log`): a stream of 1,000,000 rows costs 424 s and 3.4 GB on the first round, then 30 to 39 s and about 3.3 GB each minute for one new row. The growth is real, as p34-8 says. It reaches trouble only at about a million rows in one stream, so `should` is right.

**Block timing rule** (p1a): 79 passed in 12 s.

**Other requested runs**, all inside the whole-repo run and passing there: QML's suite, the Library suite, `test_connect_node.py`, `test_connect_node_server.py`, `test_app_kill_scopes.py`, `test_app_env_data.py`, trading-node app tests, `test_lock_order.py`, `test_feed_relay.py`, `test_venue_records.py`, `test_shipped_apps.py`, `test_templates.py`, `test_conformance.py`, `test_qmb_run_kinds.py`, `test_data_quality_block.py`, `test_import_stamps.py`.

**Not run, and why**: statistics goldens (`uv run` with downloads of arch and statsmodels), p5c's bearer reader (reaches the Credential Manager), C-17's two real hosts (Linux only), p1b's `lib_proof.py` reprint (its numbers are already in the findings, and it can run past the limit), p2's memory rerun (only useful after the fix).
