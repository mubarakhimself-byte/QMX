"""Gathers the evidence pointers for each proposed decision (card T6 step 1, card P4 step 1): the
unit and the decision asked (promote to paper, paper to live, demote, add to the book), its term
sheet, lineage and content hash, backtest, walk-forward and holdout results, the demo or paper
journal against its Monte Carlo band, live-calibrated costs against the assumed cost, the overfit
audit on the current hash, the stress result with the unit added, the validation verdict, the
tighten-only history, the P1 study, open red incidents, and the account's prop-firm rules, each as
the evidence itself plus a pointer.

Everything is read-only, from the trading node, the Lab and the Library. The promotion thresholds
are the risk session's. Until both exist this template stays a draft (`needs: trading-node,
risk-session`) and this script refuses to guess.
"""

import sys

sys.stderr.write(
    "waits for the trading node's reads and the risk session's promotion rules "
    "(needs: trading-node, risk-session)"
)
raise SystemExit(1)
