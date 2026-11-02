"""Compiles each built reading to a sealed experiment spec (card D2, as a subflow) and backtests it
on QMB with costs, on the in-sample window only (card L1 steps 7 and 8). Its output is `readings`:
each reading's `reading`, `trades` (time and session of each), `sharpe`, `daily_sharpe`,
`expectancy_r`, `costs_on_expectancy_r`, the stated `session`, the `lookahead_lint` result with any
offending line, and `refused` with QMB's reason. A QMB refusal is a result, not a failure.

Until the facts step's Library read exists this template stays a draft (`needs: real-library`) and this script
refuses to guess.
"""

import sys

sys.stderr.write("waits for a workflow read of its readings, read with the Toolbox facts (needs: real-library)")
raise SystemExit(1)
