"""Tests a generation's built children (card D3 steps 7 to 9): each compiled to a sealed spec (card
D2), then QMB's in-sample and walk-forward runs and the judge's shipped preset (100 trades, walk-
forward efficiency 0.5, Monte Carlo 5th percentile above zero, positive expectancy at 1.5x costs),
fanned out. Its output is `results`: each child's `spec_hash`, `in_sample` and `validated` scores,
`daily_sharpe`, `failed` gates, or `could_not_build` and `error` carried through. A failed build or
run counts as a dead child.

Until a workflow can read the family's tries this template stays a draft (`needs: real-library`)
and this script refuses to guess.
"""

import sys

sys.stderr.write(
    "waits for a workflow read of the family's tries its judge child counts (needs: real-library)"
)
raise SystemExit(1)
