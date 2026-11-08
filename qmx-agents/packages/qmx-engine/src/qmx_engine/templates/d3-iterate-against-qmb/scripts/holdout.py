"""The holdout, touched once, on the final survivor only (card D3 step 12). A parent with no
survivor touches nothing. Its output is the survivor's `holdout` score with the validation
`monte_carlo` band it must land in, plus the `judge` block's request: the study `spec`, the `study`
id, the survivor's landed `results` and the `tries` of the family, dead children included.

Until a workflow can read the sealed holdout this template stays a draft (`needs: real-library`)
and this script refuses to guess.
"""

import sys

sys.stderr.write("waits for a workflow read of the family's sealed holdout (needs: real-library)")
raise SystemExit(1)
