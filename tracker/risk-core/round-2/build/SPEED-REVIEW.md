# Speed review of the risk and sizing build, 10 November

From the store's own timestamps. Hours in the ranking overlap, so they do not add up.

## The short answer

- 21 rows in 46.2 hours is 2.2 hours a row. Before the 9 November speed orders it was 2.0 (12 rows in 24.1 h); after them 2.45 (9 rows in 22.1 h). The orders were applied from RC-13 on, within 20 minutes. They did not make it faster.
- It runs every gate, and more than your light rule asks. But the mechanical gate is softer than it looks (see "Two holes").
- The provider is not the problem. Rows are checked one after another, most need a repair round, and builder seats sit empty half the time.

## Timeline per row (hours)

| Stage | Median | Worst | Sum, 21 rows |
|---|---|---|---|
| Build, dispatch to ready | 0.96 | 2.49 | 26.9 |
| First check, ready to first verdict | 0.65 | 2.63 | 18.4 |
| Repair loop, first to clean verdict | 0.93 | 3.90 | 22.8 |
| Gate and append | 0.09 | 0.49 | 2.3 |
| Whole row | 3.65 | 6.56 | |

Lanes took a median 24 minutes a run (worst 68). Setting up a check copy (`uv sync`) is about 3 minutes, no lane waited on a lock, and the gate takes 5. None of those is the problem.

**Builders together.** Of 48.9 hours, no row was being built for 23.9, one builder ran for 17.9, two or more for only 7.0.

## What cost the time, ranked

1. **Empty builder seats, about 22 hours.** Before the orders the next builder waited for the row below to be stacked: 15 hours. After them, 5.5 hours went on 10 November (12:10 to 17:39) when nothing new started while Stop A was tidied, and 1.3 to an outage. The third seat was last used on 9 November.
2. **Repair rounds, about 20 hours.** 16 of 21 rows needed one, 26 rounds in all. About 10 were real faults the reviewer caught (a warning that released a brake, a money-door test that could not fail), about 9 stale numbers in tests, about 6 paperwork.
3. **Each row waits for the row below, about 9 hours since the orders.** A finished row was not reviewed until the row below was final and merged in. "Ready to first verdict" went from 0.35 to 1.5 hours. Each merge went to an agent that reran suites first. `CHECK carry`, which moves a verdict across a join, was never used.
4. **Builders and fixers running long test suites themselves, 9 to 12 hours.** This was speed order 1. Build time went from 0.77 to 2.35 hours. RC-14 finished its code at 22:57 and reported at 00:45. Stale-number blockers fell, yet every row still got a repair round.
5. **Dead time, about 5 hours.** The price pause (3.1 hours, now removed), internet outages, six dead agents.
6. **The orchestrator's own lane mistakes and a loaded laptop, about 4 hours plus slower lanes.** It hand-wrote a lane script per row and got it wrong on at least 9. The whole-repo check ran three times, 2.3 to 3 hours each, with 2 workers on a 12-thread machine; twice it hit its 3-hour cap unfinished.

## Are we running more than "light verification"?

Yes. Your rule: one build, one check, one fix round, lows never block. Per row it ran the builder's own long suites, lanes 1 to 4 plus custom lanes, the reviewer's own rerun, all of it again after each fix and each join, and up to four repair rounds (RC-11 four, RC-20 three).

**Earn their time:** the fresh reviewer (every real money-path catch was its), lane 1 at the exact head, the red-then-green proof, the whole-repo check at stop points.

**Waste:** builders and fixers running whole-package suites, an agent for a clean merge, repair rounds for wording, a second whole-repo run at one stop, hand-written lane scripts, third and fourth rounds.

**Two holes.** The gate tool counts FAIL lines but does not refuse on them. Nine stacked rows carry a FAIL line in their final lane logs (RC-04, 13, 14, 15, 17, 18, 19, 20, 27), each judged by the orchestrator to be its own script error. RC-20 was stacked with lanes last run nine commits earlier. The whole-repo run due at row 16 was skipped. More checks than asked, weaker proof than it appears.

## Changes, ranked by gain

**1. Review and repair each row at its own head. Saves about 1 hour a row. Biggest gain.**

> On STACK-READY, start the lanes and the fresh reviewer at that head at once, whatever the row below is doing, and run the fix round there. When the row below is final, join. A merge with no conflict you do yourself; no agent. Rerun lane 1 at the joined head, then `CHECK carry <id> <old-parent> <old-head> <new-parent> <joined-head>`. Carry PASS, lane 1 PASS and `CHECK gate-dsh` at the joined head stack the row. On a carry FAIL, a conflict, or when the fix below touched a file this row changes, a fresh reviewer reads the join (the whole diff for money, exits or brakes) and writes the review for the joined head.

Risk: a review made on a parent that later moves. The carry refuses unless the change is identical, and lane 1 and the gate still run at the exact head.

**2. Three builders, seats never empty. Saves about 8 hours a day.**

> Keep three builders busy. A row may start when every row in its Depends-on line is STACK-READY, from that head. Append in any order that keeps a row above what it depends on. A stop point, a sweep or a whole-repo run never holds a dispatch. Open now: RC-21 then 22; RC-23 to 26; RC-30 to 34; RC-29.

Risk: more joins, a busier laptop. A test red only under load is rerun alone once.

**3. Builders and fixers stop running long suites. Saves 1 hour a build, 0.5 to 1.5 a fix.** Replaces order 1's text.

> Before STACK-READY, search the tests for every value your change moves, update each with its reason, and run only the test files you changed or that hold those values, ten minutes in all. No whole-package suites; the coordinator runs them. A fixer runs only the failing tests and the files it touched.

Risk: a stale number reaches lane 1 instead. It is caught there.

**4. Blockers mean what your rule says. Saves about 8 hours over the rest.**

> A blocker is only: a test or quality gate red at the head; anything on money, exits, brakes, sign-ins or keys; a money-path test or fact that cannot fail; a missing owner file. Wording, tidiness and skill lists are lows: log them, fix them at the stop sweep. One fix round, one small second, then park.

Risk: a PR description slightly wrong until the sweep.

**5. One lane script, six workers, no FAIL line ever stacked. Saves about 5 hours and closes the holes.**

> Lanes run with `-n 6`. Build each test list from `git diff --name-only <parent> <head>`. Files under `qmx-agents/` run from `qmx-agents` with `uv run --frozen`, the rest from the root. No row stacks with a FAIL line in its final-head lane logs: if the FAIL was your command, fix it and rerun that line. Any commit that changes code or tests means lanes again at the new head.

Risk: none; this one tightens safety.

**6. Whole-repo check once per stop, four workers. Saves 3 laptop-hours per stop.**

> Run the whole-repo check with `-n 4`, after every eighth row and once at each stop point's final head. After a sweep, rerun only the tests that failed.

**7. Tick every 600 seconds,** reading only `RESUME.md` and the watchdog. Recovers faster after an outage or a dead agent.

**8. On takeover, fix DeepSeek rows at the tip. Saves an estimated 8 to 15 hours.** The Opus re-review of the 21 stacked rows stays. A blocker it finds is fixed on the newest row and named in `STACK-LIST.md`, as the RC-20 sweep did, not carried up through twenty rows. Risk: an old row holds a known fault until the fixing row lands; nothing runs live meanwhile.

Unchanged: fresh reviewer per row, gate at the exact head, one straight stack, no merges, every money and exit rule.

## Hours to finish the remaining 48 (estimates)

- **As it runs now:** 48 rows at 2.45 hours is 118 hours, plus two stop sweeps and the takeover re-reviews: **125 to 140 hours**, five to six days round the clock.
- **With changes 1 to 7:** about 1.1 to 1.3 hours a row, limited by the laptop and by repair rounds: **60 to 70 hours**, about three days.
- Going lower needs fewer repair rounds (three rows in four today). Whether Opus builders do better than Flash is not measured.
