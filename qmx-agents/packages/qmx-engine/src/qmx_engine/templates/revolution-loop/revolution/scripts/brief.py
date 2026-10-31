"""The brief one revolution's drafter sees: the idea, how many attempts came before, the candidates
the gates already refused, and the score the parent loop has carried this far.

The brief rides the loop's `next` value, so an attempt never reads a file another attempt wrote
(AD-51: each attempt writes only its own overlay). A live run with no idea is refused, never given
a stand-in one; only a fixture run names the recorded fixture as a source, and it is the one run
that may work on the sample idea.
"""

import json
import sys

FAILURE = "[QMX_FAILURE]"
SAMPLE_IDEA = "a testable trading idea"

state = json.load(sys.stdin)["in"]
if not isinstance(state, dict):
    state = next((found for found in state if isinstance(found, dict)), {})
fixture = state.get("fixture")
idea = str(state.get("idea") or "").strip() or (SAMPLE_IDEA if fixture else "")
if not idea:
    print(f"{FAILURE} no idea given")
    raise SystemExit(0)
negatives = list(state.get("negatives") or [])
sources = ["fixture:revolution-loop"] if fixture else []
print(
    json.dumps(
        {
            "idea": idea,
            "attempt": len(negatives) + 1,
            "rejected": [item.get("problem") for item in negatives][-3:],
            "score": int(state.get("score") or 0),
            "attempts": list(state.get("attempts") or []),
            "rounds": int(state.get("rounds") or 0),
            "negatives": negatives,
            "fixture": fixture,
            "sources": [*sources, "brief:idea", "input:idea"],
        }
    )
)
