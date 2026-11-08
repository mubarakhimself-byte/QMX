"""The generation tree and the survivor scorecard (card D3 steps 13 and 15's inputs). Its inputs,
the last generation's state, the holdout touch and the `judge` block's verdict, are told apart by
shape; the verdict is found by its key inside the child's nested outputs.

Dead branches are kept in the tree, each tagged `negative_result`. The survivor holds only when its
holdout score lands inside its validation Monte Carlo band and the judge passes it over the whole
family; otherwise it "did not hold" and is kept as a dead end. With no survivor the parent stays as
it was.
"""

import json
import sys


def judged(value):
    if isinstance(value, dict):
        if isinstance(value.get("verdict"), dict):
            return value["verdict"]
        value = list(value.values())
    if isinstance(value, list):
        return next((found for v in value if (found := judged(v)) is not None), None)
    return None


given = json.load(sys.stdin)["in"]
state = next(v for v in given if "best_score" in v)
touch = next(v for v in given if "holdout" in v)
verdict = judged([v for v in given if v is not state and v is not touch])
improved = state["best"].get("spec_hash") != state["parent"].get("spec_hash")
if not improved:
    says = "no child beat the parent; the parent stays as it was"
else:
    low, high = touch["monte_carlo"]
    held = low <= touch["holdout"] <= high
    passed = verdict is not None and verdict["overall"] == "pass"
    says = "survivor holds" if held and passed else "did not hold"
tree = [
    c | ({"tag": "negative_result"} if c["fate"] != "survivor" else {}) for c in state["children"]
]
print(
    json.dumps(
        {
            "parent": state["parent"].get("spec_hash"),
            "verdict": says,
            "survivor": state["best"].get("spec_hash") if improved else None,
            "validated": state["best_score"],
            "holdout": touch.get("holdout") if improved else None,
            "judge": verdict,
            "generations": state["generation"],
            "tree": tree,
            "trials": state["family_trials"],
        }
    )
)
