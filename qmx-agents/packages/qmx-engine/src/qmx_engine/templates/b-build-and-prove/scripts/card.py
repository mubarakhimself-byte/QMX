"""Funnel stage 12: a survivor gets a "start paper trial?" card for his click, with the demo-only
minimal risk profile (fixed small r, tighten-only). Anything else becomes a dead-end row with its
failed gates and the family's trial count, kept for R6. Nothing starts here; the trial is his act.
"""

import json
import sys

gates = json.load(sys.stdin)["in"]
if gates["survives"]:
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
        "verdict": gates["verdict"],
        "failed": gates["failed"],
        "trials": gates["trials"],
    }
    print(json.dumps({"card": None, "dead_end": dead_end}))
