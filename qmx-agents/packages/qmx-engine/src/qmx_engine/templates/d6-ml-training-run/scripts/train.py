"""Trains, tests once and ablates (card D6 steps 5 to 9): each of up to K configurations trained on
the chosen compute with checkpoints and scored on validation (each one a counted trial); the
sealed test touched once, on the chosen configuration only; then the model plugged into its slot
and a host strategy run through D2 and QMB with and without it, after costs.

Its output is `configs` (each `train_score` and `validation_score`), `chosen`, `sealed_score`,
`validation_band` (the chosen configuration's validation spread across seeds), `ablation`
(`with_r` and `without_r`, expectancy after costs), `trials` and `model_ref`. A crash resumes from
the last checkpoint on the same compute. Until the sandbox and QMB's doors exist this template
stays a draft (`needs: qmb-door, sandbox`) and this script refuses to guess.
"""

import sys

sys.stderr.write(
    "waits for the Lab sandbox, its compute and QMB's doors (needs: qmb-door, sandbox)"
)
raise SystemExit(1)
