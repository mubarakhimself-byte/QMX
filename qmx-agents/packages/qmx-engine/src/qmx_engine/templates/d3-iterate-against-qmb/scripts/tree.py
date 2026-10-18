"""The generation tree and the survivor scorecard (card D3 steps 13 and 15's inputs). Its inputs,
the last generation's state, the holdout touch and the deflated Sharpe, are told apart by shape.

Dead branches are kept in the tree, each tagged `negative_result`. The survivor holds only when its
holdout score lands inside its validation Monte Carlo band and the deflated Sharpe over the whole
family passes; otherwise it "did not hold" and is kept as a dead end. With no survivor the parent
stays as it was.
"""

import json
import sys

given = json.load(sys.stdin)["in"]
state = next(v for v in given if "best_score" in v)
touch = next(v for v in given if "holdout" in v)
deflated = next(v for v in given if "deflated_sharpe" in v)["deflated_sharpe"]
improved = state["best"].get("spec_hash") != state["parent"].get("spec_hash")
if not improved:
    verdict = "no child beat the parent; the parent stays as it was"
else:
    low, high = touch["monte_carlo"]
    held = low <= touch["holdout"] <= high
    verdict = "survivor holds" if held and deflated["passes"] else "did not hold"
tree = [
    c | ({"tag": "negative_result"} if c["fate"] != "survivor" else {}) for c in state["children"]
]
print(
    json.dumps(
        {
            "parent": state["parent"].get("spec_hash"),
            "verdict": verdict,
            "survivor": state["best"].get("spec_hash") if improved else None,
            "validated": state["best_score"],
            "holdout": touch.get("holdout") if improved else None,
            "deflated_sharpe": deflated,
            "generations": state["generation"],
            "tree": tree,
            "trials": state["family_trials"],
        }
    )
)
