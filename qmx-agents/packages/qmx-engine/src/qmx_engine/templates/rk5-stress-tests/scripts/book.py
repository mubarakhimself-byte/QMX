"""The pre-check and the read (card R5 step 1): the current book (each unit's open risk in R per
instrument, its r in USD, its stop distance in pips and its pip value), the account (equity, kill
line, prop daily loss limit, the buffer above the kill line and the largest overshoot allowed
below it), the guard config read-only (its kill-switch reaction in seconds), and the live cost
model (typical slippage in pips and normal spread per instrument, ATR in pips). The monitor that
runs this wakes the stress run only when one of them changed since last week.

Everything comes through the unit adapter and the guard reader. Until they exist this template stays
a draft (`needs: trading-node`) and this script refuses to guess.
"""

import sys

sys.stderr.write("waits for the trading node's unit adapter and guard reader (needs: trading-node)")
raise SystemExit(1)
