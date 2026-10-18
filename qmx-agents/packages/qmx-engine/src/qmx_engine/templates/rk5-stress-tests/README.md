# RK5 Stress tests

Waits for the trading node: its book, guard config and cost model reads (`needs: trading-node`).

Built from card R5 in `research/methodology/16-templates-trader-risk.md`. Every Sunday at 18:00 it asks what the whole book does on the worst days FX has had, and whether the guard stops it in time. It proposes tightenings only; he signs.

## Steps

1. `Book, guard or costs changed?` is a monitor on `scripts/book.py`: the book, the account and its limits, the guard config (read-only) and the live cost model. Nothing changed, nothing runs.
2. `Run the scenarios` applies each scenario in `data/scenarios.json` (the SNB unpeg, Brexit night, the GBP and JPY flash crashes, the COVID week, rollover blowouts, Monday gaps, and the card's synthetic shocks) as a gap, slippage and spread shock, simulates the guard, and passes a scenario only when the cushion holds or the guard stops it within the allowed overshoot and the prop daily limit holds. A scenario with no cost-model row reads "not run".
3. `Explain the worst three` (role `synthesiser`, the card's analyst) explains the three that leave the least cushion and proposes at most three tightenings.
4. `Stress report` and `Render and grade` check every number in the explanations against the book and the results.

## Left out, and why

- Replaying historical windows tick by tick: no tick archive yet, so each window is a shock in ATR. Edit `data/scenarios.json` to change a shock.
- The event triggers (a unit added or promoted, a guard config change) and running as a subflow of the promotion pack: event triggers and real subworkflow bundles come first.
- The optional `rlm` scan of the tick archive for new extreme windows: it needs the RLM node and the tick archive (`rlm` is its own need, TP4's RS8).
- Reusing last week's results with a fresh stamp when nothing changed: the monitor ends the run silent instead.
- Test fixtures: they come with the node's read model, whose real shape they must match.
