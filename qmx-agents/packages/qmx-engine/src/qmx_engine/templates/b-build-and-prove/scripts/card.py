"""Funnel stage 12: a passing verdict gets a "start paper trial?" card for his click, with the
demo-only minimal risk profile (fixed small r, tighten-only). Anything else becomes a dead-end row
with the judge's outcome, its plain words and the tries behind it, kept for R6. The verdict is the
`judge` block's, decided by script; the block hands on its child's outputs nested, so the verdict
is found by its key. Nothing starts here; the trial is his act.
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


verdict = judged(json.load(sys.stdin)["in"])
if verdict["overall"] == "pass":
    card = {
        "kind": "start paper trial",
        "options": ["start paper trial", "send to D3 to improve", "not now"],
        "recommended": "start paper trial",
        "risk_profile": {"r": "fixed, the smallest step", "changes": "tighten-only"},
    }
    print(json.dumps({"card": card, "dead_end": None}))
else:
    dead_end = {
        "tag": "negative_result",
        "verdict": verdict["overall"],
        "says": verdict["says"],
        "tries": verdict["raw_tries"],
        "effective_tries": verdict["effective_tries"],
    }
    print(json.dumps({"card": None, "dead_end": dead_end}))
