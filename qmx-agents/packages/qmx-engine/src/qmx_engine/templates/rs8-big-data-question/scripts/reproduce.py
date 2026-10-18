"""Reproduce (card R8 step 3): restore the kernel from the saved snapshot and re-run, by script,
the cells behind each finding, without any model. Its output is `reproduced`: each finding's `id`
with the `value` the re-run gave, or `error`.

It needs the same kernel's snapshot and restore. Until the `rlm` node kind and its kernel exist
this template stays a draft (`needs: rlm`) and this script refuses to guess.
"""

import sys

sys.stderr.write("waits for the rlm kernel's snapshot restore (needs: rlm)")
raise SystemExit(1)
