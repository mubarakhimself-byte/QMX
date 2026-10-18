"""Records every child of the generation, survivor or not (card D3 steps 10 and 11 and its gates).
Its inputs, the generation's state, the checked children and the test results, are told apart by
shape.

Every child counts as a trial, refused, unbuilt and dead ones included. A child survives when it
passed every robustness gate and its validated score beats the current best; one that wins only
in-sample is dead, and a daily Sharpe above 2 is held for a lookahead audit instead of winning.
The best survivor is the next generation's parent. The loop stops after 2 generations with no gain
(the loop's own rule) or at its third generation.
"""

import json
import sys

LOOKAHEAD_DAILY_SHARPE = 2

given = json.load(sys.stdin)["in"]
state = next(v for v in given if "best_score" in v)
checked = next(v for v in given if "refused" in v)
results = {r["spec_hash"]: r for r in next(v for v in given if "results" in v)["results"]}
best, best_score = state["best"], state["best_score"]
children = list(state["children"])
for child in checked["build"]:
    found = results.get(child["spec_hash"], {"error": "no result"})
    row = {
        "generation": checked["generation"],
        "parent": state["best"].get("spec_hash"),
        "change": child["change"],
        "bucket": child["bucket"],
        "spec_hash": child["spec_hash"],
        "in_sample": found.get("in_sample"),
        "validated": found.get("validated"),
    }
    if found.get("could_not_build") or found.get("error"):
        row["fate"] = "dead: " + (found.get("could_not_build") or found["error"])
    elif found["failed"]:
        row["fate"] = "dead: failed " + ", ".join(found["failed"])
    elif found["daily_sharpe"] > LOOKAHEAD_DAILY_SHARPE:
        row["fate"] = "held for a lookahead audit"
    elif found["validated"] > best_score:
        row["fate"] = "survivor"
        best, best_score = child | {"validated": found["validated"]}, found["validated"]
    else:
        row["fate"] = "dead: wins only in-sample"
    children.append(row)
children += [
    {
        "generation": checked["generation"],
        "change": r["change"],
        "spec_hash": r["spec_hash"],
        "fate": "refused: " + r["why"],
    }
    for r in checked["refused"]
]
print(
    json.dumps(
        state
        | {
            "best": best,
            "best_score": best_score,
            "children": children,
            "generation": checked["generation"],
            "family_trials": state["family_trials"]
            + len(checked["build"])
            + len(checked["refused"]),
        }
    )
)
