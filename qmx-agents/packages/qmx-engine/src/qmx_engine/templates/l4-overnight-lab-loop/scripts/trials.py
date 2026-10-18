"""One revolution's trials (card L4 steps 5 to 7): each fresh candidate compiled to a sealed spec
(card D2, fanned out), backtested in-sample with costs on QMB, then validated: walk-forward on the
validation window, Monte Carlo, cost stress at 1.5x and minimum trades, with the thresholds read
from Settings. Its output is `trials`: each candidate's `spec_hash`, `in_sample` and `validated`
scores, `monte_carlo` band, `passed` and `failed` gates, `daily_sharpe`, or `error`. A QMB failure
on one candidate drops it and still counts it as a trial.

Until QMB's doors for agents exist this template stays a draft (`needs: qmb-door`) and this script
refuses to guess.
"""

import sys

sys.stderr.write(
    "waits for QMB's compile, backtest and validation doors for agents (needs: qmb-door)"
)
raise SystemExit(1)
