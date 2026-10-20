"""The sink of one revolution: what the parent loop's plateau check reads. A revolution that kept a
candidate says so; one that did not hands on every negative result it made."""

import json
import sys

given = json.load(sys.stdin)["in"]
state = given if isinstance(given, dict) else given[-1]
print(
    json.dumps(
        {
            "idea": state.get("idea"),
            "fixture": state.get("fixture"),
            "passed": bool(state.get("passed")),
            "candidate": state.get("candidate"),
            "score": int(state.get("score") or 0),
            "rounds": int(state.get("rounds") or 0),
            "attempts": list(state.get("attempts") or []),
            "negatives": list(state.get("negatives") or []),
        }
    )
)
