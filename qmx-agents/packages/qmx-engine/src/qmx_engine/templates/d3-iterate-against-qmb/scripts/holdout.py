"""The holdout, touched once, on the final survivor only (card D3 step 12). A parent with no
survivor touches nothing. Its output is the survivor's `holdout` score with the validation
`monte_carlo` band it must land in, plus `family_trials` (every trial's per-period Sharpe in the
family, dead children included) and `candidate` for the deflated Sharpe.

Until QMB's sealed-holdout door exists this template stays a draft (`needs: qmb-door`) and this
script refuses to guess.
"""

import sys

sys.stderr.write("waits for QMB's sealed-holdout door for agents (needs: qmb-door)")
raise SystemExit(1)
