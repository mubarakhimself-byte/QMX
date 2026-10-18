"""The explainer: the question, the reproduced findings with the reproduced-by-script badge, the
ones that were not, the evidence pack's state and the cost. Above his ask-above number, or with a
handle that did not resolve, it is a cost card and nothing was spent. Its inputs are told apart by
shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
given = given if isinstance(given, list) else [given]
estimate = next(v for v in given if "estimate_usd" in v)
kept = next((v for v in given if "not_reproduced" in v), None)
prose = next((v for v in given if "summary" in v), {"summary": ""})
cost_card = None
if not estimate["within"]:
    cost_card = {
        "kind": "approve spend",
        "estimate_usd": estimate["estimate_usd"],
        "ask_above_usd": estimate["ask_above_usd"],
        "sub_calls": estimate["sub_calls"],
        "unresolved_handles": estimate["unresolved"],
    }
print(
    json.dumps(
        {
            "question": estimate["question"],
            "cost_card": cost_card,
            "findings": kept["findings"] if kept else [],
            "not_reproduced": kept["not_reproduced"] if kept else [],
            "evidence_complete": kept["evidence_complete"] if kept else False,
            "cost_usd": kept["cost_usd"] if kept else 0,
            "summary": prose["summary"],
        }
    )
)
