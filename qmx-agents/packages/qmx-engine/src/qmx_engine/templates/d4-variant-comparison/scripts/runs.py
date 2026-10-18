"""Compiles every variant to a sealed spec (card D2) on the same windows and the same costs, and
runs them on QMB, fanned out (card D4 steps 5 and 6). The holdout is never used here. Its output is
`runs`: each variant's `variant`, `windows`, `costs`, `sharpe`, `expectancy_r`, `max_drawdown_r`,
`trades`, `daily_returns` and `equity_ref`, or `failed` with the reason; plus `bootstrap_spread`
(the 90% band of the best-minus-median Sharpe under block bootstraps), `family_trials` and
`candidate` (the best variant) for the deflated Sharpe over the variant set.

Until QMB's doors for agents exist this template stays a draft (`needs: qmb-door`) and this script
refuses to guess.
"""

import sys

sys.stderr.write("waits for QMB's compile and backtest doors for agents (needs: qmb-door)")
raise SystemExit(1)
