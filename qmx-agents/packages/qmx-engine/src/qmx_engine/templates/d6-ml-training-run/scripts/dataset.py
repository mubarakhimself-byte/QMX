"""Builds the dataset and its splits in the sandbox (card D6 pre-check and steps 2 and 3): features,
labels and timestamps, all point-in-time; train, validation and the sealed test with purge and
embargo between them, the sealed test created once per model family; a model trained on shuffled
labels; and the compute place with its cost estimate.

Its output is `scope` (the slot, label, horizon, features and family it built), `rows`,
`splits` (each `start` and `end`), `purge_bars`, `embargo_bars`, `feature_lag_bars` (the smallest
gap between a feature's last input and its label's start), `shuffle_score` and `chance_score`,
`sealed_test` (`created`, `touched` count), `estimate_usd` and `runs_on`. Until the sandbox and
QMB's data doors exist this template stays a draft (`needs: qmb-door, sandbox`) and this script
refuses to guess.
"""

import sys

sys.stderr.write("waits for the Lab sandbox and QMB's data doors (needs: qmb-door, sandbox)")
raise SystemExit(1)
