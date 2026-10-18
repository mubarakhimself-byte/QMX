"""Loads each live and demo unit's journal in R and its baselines (card R3 step 1, card P3 steps 1
to 3 inputs): closed trades with R and cost, the backtest's expected R per trade, its standard
deviation, win rate, payoff ratio and trades per day, the Monte Carlo 5-95% band of cumulative R,
the term sheet's kill criterion as a drawdown in R, and the unit's and the account's limit use,
read-only.

Everything comes through the unit adapter and the guard reader. Until they exist this template stays
a draft (`needs: trading-node`) and this script refuses to guess.
"""

import sys

sys.stderr.write("waits for the trading node's unit adapter and guard reader (needs: trading-node)")
raise SystemExit(1)
