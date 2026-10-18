"""Record every trial and detect a plateau (card L4 steps 8 to 10 and its budget guard). Its
inputs, tonight's state, the deduped batch and the trial results, are told apart by shape.

Every trial goes into the family ledger, passed or not; a failed one counts too. The best score is
the best validated score of a trial that passed every gate; a daily Sharpe above 2 never counts
until a lookahead audit clears it. A plateau is no gain in the best validated score over the last
30 trials. The night stops at 200 trials.
"""

import json
import sys

PLATEAU_TRIALS = 30
MAX_TRIALS = 200
LOOKAHEAD_DAILY_SHARPE = 2

given = json.load(sys.stdin)["in"]
state = next(v for v in given if "tried" in v)
deduped = next(v for v in given if "fresh" in v)
results = next(v for v in given if "trials" in v and "tried" not in v)["trials"]
ledger = state.get("ledger", []) + results
tried = sorted(set(state["tried"]) | {t["spec_hash"] for t in deduped["fresh"]})
best, since = state["best_validated"], state.get("trials_since_gain", 0)
for trial in results:
    clean = not trial.get("error") and not trial["failed"]
    if clean and trial["daily_sharpe"] <= LOOKAHEAD_DAILY_SHARPE and trial["validated"] > best:
        best, since = trial["validated"], 0
    else:
        since += 1
tonight = state["trials_tonight"] + len(results)
print(
    json.dumps(
        state
        | {
            "ledger": ledger,
            "tried": tried,
            "trials_tonight": tonight,
            "trials_family": state["trials_family"] + len(results),
            "best_validated": best,
            "trials_since_gain": since,
            "plateau": since >= PLATEAU_TRIALS,
            "stop": tonight >= MAX_TRIALS,
        }
    )
)
