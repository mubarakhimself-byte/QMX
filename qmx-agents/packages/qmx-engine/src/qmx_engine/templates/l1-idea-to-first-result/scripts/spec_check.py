"""The spec check and the divergence check (card L1 steps 4 and 5). No build before it passes.

Every card field must be filled; a missing exit takes the house policy labelled `external_policy`.
Then the readings: when an open answer would change the logic, two or three structurally different
readings are built side by side (arena) instead of asking again, the recommended answer first;
otherwise one. At most 3 readings, never averaged.
"""

import json
import sys

FIELDS = (
    "mechanism",
    "market",
    "timeframe",
    "session",
    "entry",
    "kill_rule",
    "data_needed",
    "what_would_fake_this",
)
MAX_READINGS = 3

drafted = json.load(sys.stdin)["in"]
card = dict(drafted["card"])
missing = [f for f in FIELDS if not str(card.get(f) or "").strip()]
if card.get("exit") is None:
    card["exit"] = "external_policy"
diverging = next((q for q in drafted["questions"] if q["changes_logic"]), None)
if diverging is None:
    readings = [{"reading": 1, "card": card, "differs_by": None}]
else:
    answers = [diverging["recommended"], *diverging.get("alternatives", [])][:MAX_READINGS]
    readings = [
        {
            "reading": k + 1,
            "card": card | {diverging["field"]: answer},
            "differs_by": {"field": diverging["field"], "answer": answer},
        }
        for k, answer in enumerate(answers)
    ]
print(
    json.dumps(
        {
            "ok": not missing,
            "missing": missing,
            "card": card,
            "questions": drafted["questions"],
            "dead_end_warning": drafted["dead_end_warning"],
            "readings": readings,
        }
    )
)
