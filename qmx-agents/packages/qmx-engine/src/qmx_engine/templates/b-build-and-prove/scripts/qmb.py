"""Registers the sealed spec through QMB's host validator and runs it (card D2 steps 5 and 6, card
D3's robustness set; funnel stages 9 and 10): the one-month smoke run, the in-sample backtest with
costs, the walk-forward folds, the Monte Carlo band, the cost stress at 1.5x, and the regime and
session breakdown. Its output carries `trades`, `in_sample` and `walk_forward` (Sharpe, expectancy
in R, max drawdown in R, daily Sharpe), `monte_carlo` (5th and 95th percentile of total R),
`cost_stress` (expectancy at 1.5x costs), `family_trials` and `candidate` for the deflated Sharpe.

A host validator refusal is a result, passed on with its reason. Agents never write QMB's registry.
Until QMB's doors for agents exist (`qmb.spec.register`, `qmb.backtest`, `qmb.walk_forward`,
`qmb.robustness`) this template stays a draft (`needs: qmb-door`) and this script refuses to guess.
"""

import sys

sys.stderr.write("waits for QMB's spec, backtest and robustness doors for agents (needs: qmb-door)")
raise SystemExit(1)
