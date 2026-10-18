"""Reads the book (card R2 steps 1 and 2 inputs): each unit's open positions with their instrument,
side and open risk in R, the last 60 days of daily R per unit, the minutes each unit was in a trade
each day, the correlation baseline stored with each unit's promotion, and the guard's per-currency
open-risk limit in R from its table.

Everything is read-only, through the unit adapter and the guard reader. Until they exist this
template stays a draft (`needs: trading-node`) and this script refuses to guess.
"""

import sys

sys.stderr.write("waits for the trading node's unit adapter and guard reader (needs: trading-node)")
raise SystemExit(1)
