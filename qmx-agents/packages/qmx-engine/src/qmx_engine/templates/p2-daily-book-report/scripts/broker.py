"""The preflight and the read (card P2 pre-check and steps 1 to 4 inputs): broker reads reachable
and today's journals updated, then the open positions, today's closed trades with their unit, PnL in
USD and r in USD, account equity, the account loss budget and the kill line, and each paper unit's
result against its backtest Monte Carlo band.

The broker reads go through `qmx-broker` with the read-only broker token he makes himself; this
template never holds, names or asks for a broker credential, and it calls no tool that can trade.
Guard fields read "could not check" until the trading node's read model exists. Until the read-only
token exists this template stays a draft (`needs: broker-read-token`) and this script refuses to
guess.
"""

import sys

sys.stderr.write("waits for the read-only broker token (needs: broker-read-token)")
raise SystemExit(1)
