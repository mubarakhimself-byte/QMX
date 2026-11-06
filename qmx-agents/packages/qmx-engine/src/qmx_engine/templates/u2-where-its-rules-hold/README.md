# Find where a failed unit's rules still hold

The fail branch of "Build and prove": for a unit that died, a search over the contexts where its rules may still hold, with every context counted, so the one that held is judged against everything that was tried. Part B `workflows.md` section 3, "Where would its rules hold".

## Steps

1. `Route the run` (`scripts/route.py`) writes QMB's asks: a sweep over his markets, each traded alone, and one `session_hours` what-if per session he names. Session hours are his, from his calendars; nothing here writes a clock.
2. `Sweep the markets on QMB` (`app_op`, job `sweep`) and, when he names sessions, `Try the sessions on QMB` (job `whatif`) run them. QMB's lander counts every market cell, and every `session_hours` scenario as a `whatif_rerun` try.
3. `Ask the referee` (role `judge`, toolset `backtest`) presses the core's `backtest_judge_run` on every result.
4. `Hand on the verdict` (`scripts/hand.py`), `Read the stored verdict` (the `library` node) and `The stored verdict` (`scripts/stored.py`) read what the Library holds. The referee's copy decides nothing, and the run stops by name on a verdict of another unit or another run.
5. `Where the rules hold` (`scripts/holds.py`) splits the markets by the stored verdict. When any held, `Propose admitting those markets` (the shared `proposal-card` block, carried in `proposal-card/`) lands one `admit_market` card for his click, naming the sessions tried and counted, with the core's own paper card among its evidence. Nothing is admitted here.

A test run names `fixture: recorded`, and `Replay the recorded runs` stands in for QMB and the referee: it lands the recorded verdict and papers from `fixtures/qmb.json` on the run's own ref, and the real read crosses them.

## Left out, and why

- Which session held: the referee's answer judges each market across every result, not each session, so the report lists the sessions tried and names none as the one that held.
- Readings states as a context: the unit's conditions read them, and a sweep over them needs QMB to replay the MIS's reading history, which it does not yet.
- Starting on a death certificate's landing: the landing event names only the certificate's object id, so a start needs a step to read the unit from it. The run is started with the unit's pin.
