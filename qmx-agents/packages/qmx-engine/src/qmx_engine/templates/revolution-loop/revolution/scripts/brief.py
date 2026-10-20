"""The brief one revolution's drafter sees: the idea, how many attempts came before, the candidates
the gates already refused, and the score the parent loop has carried this far.

The brief rides the loop's `next` value, so an attempt never reads a file another attempt wrote
(AD-51: each attempt writes only its own overlay).
"""

import json
import sys

state = json.load(sys.stdin)["in"]
if not isinstance(state, dict):
    state = next((found for found in state if isinstance(found, dict)), {})
negatives = list(state.get("negatives") or [])
print(
    json.dumps(
        {
            "idea": state.get("idea") or "a testable trading idea",
            "attempt": len(negatives) + 1,
            "rejected": [item.get("problem") for item in negatives][-3:],
            "score": int(state.get("score") or 0),
            "attempts": list(state.get("attempts") or []),
            "rounds": int(state.get("rounds") or 0),
            "negatives": negatives,
            "fixture": state.get("fixture"),
            "sources": ["fixture:revolution-loop", "brief:idea", "input:idea"],
        }
    )
)
