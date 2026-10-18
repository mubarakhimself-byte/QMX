"""Loads the return streams (card P1 steps 1 and 2): each candidate's out-of-sample and paper daily
returns in R and USD, never in-sample, and each book unit's paper and live daily returns from its
journal, all aligned on one calendar with costs on; the named crisis windows; the cost per unit of
turnover; and the study's minimum overlap with the book (default 12 months). A candidate with no
out-of-sample stream is listed in `dropped` with "could not study: no out-of-sample stream".

Book streams come from the trading node's journals and candidate streams from the Lab, read-only.
The combining and sizing method list is data the risk session owns. Until both exist this template
stays a draft (`needs: trading-node, risk-session`) and this script refuses to guess.
"""

import sys

sys.stderr.write(
    "waits for the trading node's journals and the risk session's method list "
    "(needs: trading-node, risk-session)"
)
raise SystemExit(1)
