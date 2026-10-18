# L1 Idea to first result

Waits for QMB's doors for agents and the Lab's Toolbox and data check (`needs: qmb-door`).

Built from card L1 (idea to first result in at most two iterations) in `research/methodology/17-templates-dev-pm-lab.md`. He says "buy pullbacks to the 20 EMA in London when the daily trend is up" and sees an in-sample backtest of what he meant. An iteration is one round trip in which he looks and says "not that"; the target is two, one at the card and one at the result.

## Steps

1. `Library, Toolbox and data facts` (`scripts/facts.py`) runs before any question: prior boards, term sheets, components and dead ends on the mechanism, Toolbox hits, and the data on hand. Facts are shown, never asked.
2. `Draft the card and its questions` (role `planner`, the card's grill) drafts the spec card and up to five numbered questions, each recommended answer already written in. "Yes" accepts all. A dead end with the same mechanism and market goes on top.
3. `Spec check and readings` refuses a card with an empty field (a missing exit takes `external_policy`) and, when an open answer would change the logic, makes two or three readings instead of asking again.
4. `Spec complete?` stops at the card when a field is missing; `One item per reading` hands each reading to its own builder.
5. `Build each reading` (role `builder`, one per reading, 30 turns) builds Graph and Code with tests written first.
6. `Compile and backtest in-sample` (`scripts/run.py`) compiles each reading to a sealed spec and backtests it with costs, in-sample only.
7. `Quick gates`: 30 trades, the lookahead lint (a failure shows "blocked: lookahead" with the line and no number), positive expectancy with costs, every trade inside the stated session, and the lookahead banner above a daily Sharpe of 2.
8. `Write what I built from your words` (role `writer`) puts the build beside each number; `Render and grade` checks every number in the card, the questions and the summary against the facts, the runs and the gates.

## Left out, and why

- His two iterations: the run takes the recommended answers ("yes"), shows the card and the result, and counts "1 of 2". His corrections start the next run, because `human_gate` is unavailable.
- The builder's doctor repair and the arena pick: a reading that cannot build after one repair is shown as "could not build"; picking is his.
- Board, operator and lesson memory (what he rejected, every third iteration's missed question): workflow memory rows are not used yet.
- The animated card and the side-by-side equity curves: drawing is UI-side; the result carries the numbers.
- Test fixtures: they come with QMB's door for agents, whose real result shape they must match.
