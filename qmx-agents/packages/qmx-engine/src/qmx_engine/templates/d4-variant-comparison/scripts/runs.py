"""Compiles every variant to a sealed spec (card D2) on the same windows and the same costs, and
runs them on QMB, fanned out (card D4 steps 5 and 6). The holdout is never used here. Its output is
`runs`: each variant's `variant`, `windows`, `costs`, `sharpe`, `expectancy_r`, `max_drawdown_r`,
`trades`, `daily_returns` and `equity_ref`, or `failed` with the reason; plus `bootstrap_spread`
(the 90% band of the best-minus-median Sharpe under block bootstraps), and the `judge` block's
request over the variant set: the study `spec`, the `study` id, the landed `results` and the
`tries`.

Until a workflow can read the family's tries this template stays a draft (`needs: real-library`)
and this script refuses to guess.
"""

import sys

sys.stderr.write(
    "waits for a workflow read of the family's tries and each variant's daily returns "
    "(needs: real-library)"
)
raise SystemExit(1)
