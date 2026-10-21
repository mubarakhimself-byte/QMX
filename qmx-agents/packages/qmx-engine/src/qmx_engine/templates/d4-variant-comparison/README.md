# Variant generation and comparison

Waits for QMB's doors for agents: compile and backtest (`needs: qmb-door`).

Built from card D4 (variant generation and comparison) in `research/methodology/17-templates-dev-pm-lab.md`. It turns his request ("try this on GBPUSD and on 15 minutes") into labelled variants of one strategy and compares them fairly: the same windows, the same costs, every variant counted as a trial, and a warning when the leader's edge could be luck.

## Steps

1. `Plan the labelled variants` (role `planner`) lists at most 12 variants, each labelled instrument, timeframe, params, spiced, structural or model-made.
2. `Identity rule and caps` reads the label table: instrument, timeframe, params and spiced stay `variant_of` the strategy; structural and model-made are new strategies `derived_from` it. At most 4 variants need a builder.
3. `Any variant to build?` skips the builder when every variant is a config change.
4. `Build the structural variants` (role `builder`, 20 turns per variant) builds the spiced, structural and model-made ones.
5. `Compile and run every variant` (`scripts/runs.py`) compiles each to a sealed spec on identical windows and costs and runs it on QMB. The holdout is never used here.
6. `Deflated Sharpe over the variants` (the shared `overfit-gates` block) counts the whole set.
7. `Compare on identical windows` refuses a mixed set, ranks the variants, correlates every pair, and warns when the best edge over the median is inside the bootstrap spread.
8. `Write the comparison` (role `writer`) writes the summary; `Render and grade` checks its numbers and the variant names against his request, the strategy, the runs and the page's script-made fields.

## Left out, and why

- Branching each variant as a git-style draft branch and writing its lineage edge: they need the Lab's draft and lineage doors; the page carries each variant's edge.
- His pick of which variants go forward: it is his act on the page, because `human_gate` is unavailable.
- Lessons on which label kinds survive for the family: workflow memory rows are not used yet.
- The equity overlay and the correlation grid as pictures: drawing is UI-side; the page carries the numbers and each run's equity reference.
- Test fixtures: they come with QMB's door for agents, whose real result shape they must match.
