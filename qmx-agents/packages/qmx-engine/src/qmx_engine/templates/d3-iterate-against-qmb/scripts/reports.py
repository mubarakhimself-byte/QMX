"""The pre-check and the one read (card D3 pre-check and step 1): the parent's full report from QMB
(backtest, walk-forward, Monte Carlo, regime and session breakdown, and its holdout numbers if any),
the family's trial count and ledger of spec hashes, and the budget headroom. A parent without a full
report is refused.

Its output is `parent` (id, spec, `spec_hash`, `validated` score), `report` (its sections),
`holdout` (numbers the diagnoser must not see), `family` (`trials`, `spec_hashes`) and
`headroom`. Until a workflow can read those Library rows this template stays a draft (`needs:
real-library`) and this script refuses to guess.
"""

import sys

sys.stderr.write(
    "waits for a workflow read of the parent's reports and its family's tries (needs: real-library)"
)
raise SystemExit(1)
