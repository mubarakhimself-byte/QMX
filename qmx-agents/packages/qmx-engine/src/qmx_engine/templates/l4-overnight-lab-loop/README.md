# Overnight Lab loop

Waits for a workflow read of the Library: the family's tries and its sealed holdout (`needs: real-library`). QMB's own door is there now.

Built from card L4 (overnight Lab loop, Build Alpha style) in `research/methodology/17-templates-dev-pm-lab.md`. While he sleeps it generates candidates inside a search space, backtests and validates them, detects a plateau, changes the space by one fixed move, and restarts. Every trial is recorded and every dead end kept. The model proposes; scripts decide, behind gates the loop cannot loosen.

## Steps

1. `Load and check the search space` (zero tokens) refuses a space with an empty class list, a bad range, or a fitness function off his approved list.
2. `Family ledger and gate thresholds` (`scripts/family.py`) reads the headroom, the family's trial count and tried spec hashes, its dead-end regions, its best validated score and the gate thresholds from Settings, read-only. It builds the night's starting state.
3. `Each revolution` runs the card's `revolutions` (6 to start) and stops after `revolutions_without_gain` (2 to start) in a row without gain or at `trials` (200 to start) trials tonight. All are starting defaults he changes on the run's inputs, never caps. The loop node's `max_iterations` of 1000 is only the engine's rule that every loop ends; the card's counts stop the loop long before it.
   1. `Propose candidates` (role `planner`, the card's generator) proposes 10 candidates inside the space.
   2. `Dedupe by spec hash` drops anything already tried or outside the space.
   3. `Compile, backtest and validate` (`scripts/trials.py`) is the revolution's QMB call: compile, in-sample with costs, walk-forward, Monte Carlo, cost stress at 1.5x, minimum trades.
   4. `Record trials and detect a plateau` records every trial, passed or not, and calls a plateau after the card's `plateau_trials` (30 to start) trials without a better validated score. A daily Sharpe above 2 never counts as a gain.
   5. `Plateau?` sends a plateau to `Change the search space` (role `planner`) and `Apply the move`, which takes one move from the fixed list and refuses anything else, including any change to the fitness function or a threshold. The old space becomes a dead region.
4. `Holdout once for the top 3` (`scripts/holdout.py`) is the night's only holdout touch.
5. `Judge the results` (the shared `judge` block, carried in `judge/`) sets the verdict by script over every trial tonight and before, dead parents included.
6. `Rank and keep dead ends` marks a survivor whose holdout falls outside its validation band "did not hold", keeps every dead end tagged `negative_result`, draws the plateau map from the moves, and offers at most two decisions with a recommendation each.
7. `Write the morning card` (role `writer`) writes the summary; `Render and grade` checks the numbers in the summary and in each move's reason against the family facts, the holdout runs and the card's script-made fields.

## Left out, and why

- The wall-clock deadline (07:00) and the drain at a usage cap: the run's `wall_seconds` and the engine's pause at the usage limit cover them until a per-step deadline exists.
- R7 calibrate over seeds and block bootstraps: it joins when QMB returns reruns.
- Writing dead ends and the plateau map to the Library, and the moves that broke plateaus as lessons: they need the real Library and workflow memory rows.
- The heat map of the space: drawing is UI-side; the result carries the moves and the dead regions.
- Test fixtures: they come with QMB's door for agents, whose real result shape they must match.
