"""The family's facts (card L4 pre-check and step 2): the usage governor's headroom, the family's
trial count and every spec hash it already tried, its dead-end regions so the first generation
avoids them, its best validated score so far, its sealed holdout, and the gate thresholds read
from Settings and bound to the graph's content hash. The loop's tools hold no Settings write and
no write to the fitness list. No headroom parks the run silent until the window opens.

Its output is the night's starting state: the checked search space and moves, the card's `counts`
as setup passed them, `thresholds`, `tried` (spec hashes), `dead_regions`, `trials_family`,
`trials_tonight` 0, `revolution` 0, `revolutions_since_gain` 0, `best_validated`, `history`
(search-space moves) empty, `plateau` false and `stop` false. Until a workflow can read the
family's tries and holdout this template stays a draft (`needs: real-library`) and this script refuses to
guess.
"""

import sys

sys.stderr.write("waits for a workflow read of the family's tries and its sealed holdout (needs: real-library)")
raise SystemExit(1)
