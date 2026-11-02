"""The holdout, touched once per night (card L4 step 13): the top 3 survivors by validated score
run on the family's sealed holdout, and the touch is logged with who and why. A second look would
be a new counted trial with a new window, so this is the only step that touches it.

Its output is `holdout`: each survivor's `spec_hash`, `holdout` score and the validation
`monte_carlo` band it must land in; plus the `judge` block's request (the study `spec`, the
`study` id, the survivors' landed `results` and the `tries` of every trial in the family tonight
and before). Until a workflow can read the holdout this template stays a draft
(`needs: real-library`) and this script refuses to guess.
"""

import sys

sys.stderr.write("waits for a workflow read of the family's sealed holdout (needs: real-library)")
raise SystemExit(1)
