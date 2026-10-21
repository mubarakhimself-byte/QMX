"""Seat the panel: the question and the three seats, each a node and the angle it answers from.

The seats are named by node id, so the spread reads the row each seat really resolved from the
run's own ledger rather than trusting the settings a lane happened to pass.
"""

import json
import sys

given = json.load(sys.stdin)["in"]
state = given if isinstance(given, dict) else next((v for v in given if isinstance(v, dict)), {})
question = str(
    state.get("question") or "Should this book carry a long euro position into the week?"
)
print(
    json.dumps(
        {
            "question": question,
            "fixture": state.get("fixture"),
            "members": [
                {"slot": "macro", "node": "member_macro", "angle": "macro backdrop"},
                {"slot": "positioning", "node": "member_positioning", "angle": "positioning"},
                {"slot": "sentiment", "node": "member_sentiment", "angle": "sentiment"},
            ],
        }
    )
)
