"""Builds the spec in the Lab sandbox and runs it on QMB (card R3 steps 4, 5, 7 and 8; card T8
steps 7 and 8): the experiment spec (code ref, data snapshot, the paper's costs, seed), the run on
the paper's own in-sample period, the run with our cost model, and the post-publication run on the
period after the paper's sample end, touched once. Its output carries `in_sample`, `costs_on` and
`post_publication`, each with `sharpe`, `daily_sharpe` and every reported metric by name, or
`could_not_test` with the reason when the data is missing. An engine refusal is a result.

A finished backtest never reruns on resume (memo key). Until QMB's doors for agents and the Lab
build exist this template stays a draft (`needs: qmb-door`) and this script refuses to guess.
"""

import sys

sys.stderr.write("waits for the Lab build and QMB's backtest doors for agents (needs: qmb-door)")
raise SystemExit(1)
