"""The zero-token pre-check and the one read (cards T5 and T9, step 1): each demo unit's closed
deals since the last tick, joined to the unit's intended price and the quote at signal time, its R
journal, its backtest's Monte Carlo band of cumulative R, its sessions and blackout windows, its
expected risk per trade, its maximum spread and its assumed cost in R, and its heartbeat. The
monitor that runs this wakes the rest only when a deal closed or a heartbeat went stale.

Every fact comes through the unit adapter and the node's deal feed, read-only. Until they exist this
template stays a draft (`needs: trading-node`) and this script refuses to guess.
"""

import sys

sys.stderr.write("waits for the trading node's deal feed and unit adapter (needs: trading-node)")
raise SystemExit(1)
