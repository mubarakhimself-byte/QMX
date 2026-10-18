"""The pre-check and the one read (card D3 pre-check and step 1): the parent's full report from
QMB (backtest, walk-forward, Monte Carlo, regime and session breakdown, and its holdout numbers if
any), the family's trial count and ledger of spec hashes, and the budget headroom. A parent without
a full report is refused.

Its output is `parent` (id, spec, `spec_hash`, `validated` score), `report` (its sections),
`holdout` (numbers the diagnoser must not see), `family` (`trials`, `spec_hashes`) and
`headroom`. Until QMB's doors for agents exist this template stays a draft (`needs: qmb-door`) and
this script refuses to guess.
"""

import sys

sys.stderr.write("waits for QMB's report and family ledger doors for agents (needs: qmb-door)")
raise SystemExit(1)
