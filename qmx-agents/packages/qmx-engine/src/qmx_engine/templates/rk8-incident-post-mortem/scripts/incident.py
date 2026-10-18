"""The incident and its timeline (card R8 step 1): the closed incident (id, signature, level, opened
and closed times, its trigger), and every event within two hours either side from the guard, the
node, the broker's deals, the MIS state, the calendar, spreads and the engine's run logs, each with
an `id`, its `at`, its `source` and its `text`; plus the account's equity, kill line and largest
active r before and after, for the impact.

Everything is read-only, from the trading node's event log and the engine's ledger. Until the node
exists this template stays a draft (`needs: trading-node`) and this script refuses to guess.
"""

import sys

sys.stderr.write("waits for the trading node's event log and account reads (needs: trading-node)")
raise SystemExit(1)
