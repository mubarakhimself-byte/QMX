# Run a unit on every market it trades

His ask, "run it on every bot across multiple instruments" (T1:442): one unit, every market he names, judged as one family so the best market is never the luckiest one. Part B `workflows.md` section 3, "Run on every market".

## Steps

1. `Route the run` (`scripts/route.py`) writes QMB's sweep: the unit's pin, the window, and a grid of his markets alone.
2. `Sweep every market on QMB` (`app_op`, job `sweep`) trades the unit on each market alone, each in its own compiled cell. QMB's lander lands one counted try per cell in the unit's family, a failed cell included.
3. `Ask the referee` (role `judge`, toolset `backtest`) presses the core's `backtest_judge_run` on the sweep's result. The core's script judges every market by one rule, shrunk toward the unit's whole result and deflated by every try, and lands the verdict with its papers.
4. `Hand on the verdict` (`scripts/hand.py`), `Read the stored verdict` (the `library` node) and `The stored verdict` (`scripts/stored.py`) read what the Library holds. The referee's copy decides nothing, and the run stops by name on a verdict of another unit or another run.
5. `One row per market` (`scripts/table.py`) lists each market's outcome and trades from the stored verdict. A market he named that the verdict does not judge is listed under `unjudged`, never dropped.

A test run names `fixture: recorded`, and `Replay the recorded run` stands in for QMB and the referee: it lands the recorded verdict and papers from `fixtures/qmb.json` on the run's own ref, and the real read crosses them.

## Left out, and why

- A market the unit does not trade: QMB's sweep narrows the unit's own markets, so a new market is a new version of the unit (`unit_check` with its item), made first.
- A paper proposal per market: the verdict is the family's, and paper is one unit's step (`b`).
