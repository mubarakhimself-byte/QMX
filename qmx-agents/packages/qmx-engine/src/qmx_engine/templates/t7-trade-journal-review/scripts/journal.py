"""Loads the R journal since the last review (card T7 step 1): every closed trade across units with
its R result and its tags, session, hour, setup, MIS state at entry, minutes to the nearest news
release, spread at entry, slippage, MAE and MFE in R, whether it was manual, and whether it broke a
rule; plus `new_trades`, the count since the last review.

The journal comes from the trading node, read-only. Until it exists this template stays a draft
(`needs: trading-node`) and this script refuses to guess.
"""

import sys

sys.stderr.write("waits for the trading node's R journal (needs: trading-node)")
raise SystemExit(1)
