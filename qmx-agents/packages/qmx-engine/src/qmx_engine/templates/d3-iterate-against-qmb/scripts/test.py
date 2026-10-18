"""Tests a generation's built children (card D3 steps 7 to 9): each compiled to a sealed spec (card
D2), then QMB's in-sample and walk-forward runs and template B's robustness gates (100 trades,
walk-forward efficiency 0.5, Monte Carlo 5th percentile above zero, positive expectancy at 1.5x
costs), fanned out. Its output is `results`: each child's `spec_hash`, `in_sample` and `validated`
scores, `daily_sharpe`, `failed` gates, or `could_not_build` and `error` carried through. A failed
build or run counts as a dead child.

Until QMB's doors for agents exist this template stays a draft (`needs: qmb-door`) and this script
refuses to guess.
"""

import sys

sys.stderr.write("waits for QMB's compile, walk-forward and robustness doors (needs: qmb-door)")
raise SystemExit(1)
