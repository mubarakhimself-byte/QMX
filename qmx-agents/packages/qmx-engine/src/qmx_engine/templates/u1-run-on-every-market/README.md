# Run a unit on every market it trades

His ask, "run it on every bot across multiple instruments" (T1:442): one unit, every market he names, judged as one family so the best market is never the luckiest one. Part B `workflows.md` section 3, "Run on every market".

## Steps

1. `Route the run` (`scripts/route.py`) writes QMB's sweep: the unit's pin, the window, and a grid of his markets alone.
2. `Sweep every market on QMB` (`app_op`, job `sweep`) trades the unit on each market alone, each in its own compiled cell. QMB's lander lands one counted try per cell in the unit's family, a failed cell included.
3. `Ask the referee` (role `judge`, toolset `backtest`) presses the core's `backtest_judge_run` on the sweep's result and copies its answer. The referee's script judges every market by one rule, shrunk toward the unit's whole result and deflated by every try.
4. `One row per market` (`scripts/table.py`) lists each market's outcome and trades. A market he named that the verdict does not judge is listed under `unjudged`, never dropped.

A test run names `fixture: recorded`, and `Replay the recorded run` stands in for QMB from `fixtures/qmb.json`.

## Left out, and why

- A market the unit does not trade: QMB's sweep narrows the unit's own markets, so a new market is a new version of the unit (`unit_check` with its item), made first.
- A paper proposal per market: the verdict is the family's, and paper is one unit's step (`b`).
