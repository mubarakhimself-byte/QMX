"""Reads the account and guard state through the read-only guard reader (cards R1 and R6, step 1):
equity, the kill line, the daily loss budget and trailing drawdown from the account's prop-firm rule
table, open positions with their risk to stop and lots, the typical slippage per lot (T9) and the
gap allowance near red events (T3) or over the weekend, the largest active r, the guard heartbeat
age, the guard config hash and the signed config hash, and each unit's risk-profile versions N and
N-1 with its signed profile (ranges, ramp schedule, signature ids) and the direction table.

The reader is the trading node's, read-only; no step here writes to the guard or the node. Until it
exists this template stays a draft (`needs: trading-node`) and this script refuses to guess.
"""

import sys

sys.stderr.write("waits for the trading node's read-only guard reader (needs: trading-node)")
raise SystemExit(1)
