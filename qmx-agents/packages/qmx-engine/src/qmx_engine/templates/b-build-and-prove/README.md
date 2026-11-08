# Turn a strategy idea into a tested strategy, ending on paper

Waits for QMB's doors for agents: spec register, backtest, walk-forward and robustness (`needs: qmb-door`).

Built from cards D2 (strategy to a sealed QMB experiment spec) and D3 (its robustness gate set) in `research/methodology/17-templates-dev-pm-lab.md`, which carry template B's stages 9 to 12. It takes a built strategy, seals its experiment spec before any result is seen, backtests it on QMB, puts it through the overfit gates, and ends with a paper-trial card for his click or a dead-end row.

## Steps

1. `Seal the experiment spec` (`scripts/spec.py`, zero tokens) reads the study settings, refuses a spec without costs, with a field that is not point-in-time, with a window below its minimum or with a window over the holdout, and hashes the spec into its memo key. The holdout and the split are his choice per study and both start off, so the whole range is one in-sample window. On the card's `study` input, `split` cuts the range into in-sample (`in_sample_share`, 0.6) and `folds` (3) walk-forward folds, and `holdout` seals the family's holdout or the last `holdout_share` (0.2) of the range.
2. `Spec checks pass?` stops a refused spec at stage 9; the scorecard lists the problems.
3. `Register and backtest on QMB` (`scripts/qmb.py`) is the one QMB call: register through the host validator, smoke run, in-sample with costs, walk-forward, Monte Carlo, cost stress at 1.5x.
4. `Judge the results` (the shared `judge` block, carried in `judge/`) sets the verdict by script over the results and every try of the family. No model decides it.
5. `Paper card or dead end` gives a passing verdict a "start paper trial?" card with the demo-only minimal risk profile; anything else becomes a `negative_result` row with the judge's words and tries.
6. `Write the scorecard` (role `writer`) writes the summary; `Assemble the scorecard` builds the result; `Render and grade` checks every number in the summary against the spec, the QMB results and the verdict.

## Left out, and why

- Stage 8 (build vanilla in the Lab) and the builder's repair rounds: building needs the Lab sandbox; BC builds components, and D3 rebuilds children.
- Stage 11 (iterate on a weak result): that is D3, started from this scorecard.
- The holdout touch: it belongs to the final survivor, so D3 and L4 touch it once, and this template never does.
- The paper trial itself: the card ends the run; starting a trial is his act, and the risk profile is the node's.
- Test fixtures: they come with QMB's door for agents, whose real result shape they must match.
