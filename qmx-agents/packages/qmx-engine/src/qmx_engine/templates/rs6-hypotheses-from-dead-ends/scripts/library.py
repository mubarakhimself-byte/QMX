"""The one read (card R6 step 1 and its pre-check): every Library row tagged `negative_result`
with its failure bucket (died on costs, out-of-sample decay, regime-only edge, too few trades,
lookahead found, not replicated), market, mechanism, source, family, the family's trial count and
every window the parent touched; the ids this workflow already mined; and, for the dedupe, the open
term sheets, the existing cards and his rejected ideas with why.

Its output is `dead_ends`, `mined`, `open_term_sheets`, `cards` and `rejected`. The Library is the
real one, read through its door; the fake Library holds no dead ends. Until it exists this template
stays a draft (`needs: real-library`) and this script refuses to guess.
"""

import sys

sys.stderr.write("waits for the real Library's dead-end and memory rows (needs: real-library)")
raise SystemExit(1)
