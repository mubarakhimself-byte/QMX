"""The family's facts (card L4 pre-check and step 2): the usage governor's headroom, the family's
trial count and every spec hash it already tried, its dead-end regions so the first generation
avoids them, its best validated score so far, its sealed holdout, and the gate thresholds read
from Settings and bound to the graph's content hash. The loop's tools hold no Settings write and
no write to the fitness list. No headroom parks the run silent until the window opens.

Its output is the night's starting state: the checked search space and moves, `thresholds`,
`tried` (spec hashes), `dead_regions`, `trials_family`, `trials_tonight` 0, `best_validated`,
`history` (search-space moves) empty, `plateau` false and `stop` false. Until QMB's family ledger
and gate doors exist this template stays a draft (`needs: qmb-door`) and this script refuses to
guess.
"""

import sys

sys.stderr.write(
    "waits for QMB's family ledger, holdout and gate doors for agents (needs: qmb-door)"
)
raise SystemExit(1)
