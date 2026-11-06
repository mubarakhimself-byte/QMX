"""The scorecard of one idea: how far it got, the core's verdict, and what waits for his click.

Its inputs are told apart by shape: the sealed spec (`memo_key`), `Ready to test?`'s answer
(`recorded`), the referee step's `verdict`, the paper card or dead end (`dead_end`), the writer's
`summary`, and the lineage child's output, nested as `outputs.<node>.main`. A refused spec ends
at stage `spec` with its problems, a unit
that is not ready at stage `unit` with why, and a judged unit at stage `verdict` with the
verdict's own words.
"""

import json
import sys


def child(rows, node):
    for row in rows:
        outputs = row.get("outputs")
        if isinstance(outputs, dict) and isinstance(outputs.get(node), dict):
            return outputs[node].get("main")
    return None


given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
sealed = next(r for r in rows if "memo_key" in r)
ready = next((r for r in rows if "recorded" in r), None)
verdict = next((r["verdict"] for r in rows if isinstance(r.get("verdict"), dict)), None)
card = next((r for r in rows if "dead_end" in r), {"card": None, "dead_end": None})
prose = next((r for r in rows if "summary" in r), {"summary": ""})
if not sealed["ok"]:
    stage, says = "spec", "could not test: " + "; ".join(sealed["problems"])
elif ready is None or not ready["ok"]:
    stage = "unit"
    says = "could not test: " + (ready["why"] if ready else "no unit was built")
else:
    stage, says = "verdict", verdict["says"]
print(
    json.dumps(
        {
            "stage_reached": stage,
            "verdict": says,
            "spec": sealed["spec"],
            "memo_key": sealed["memo_key"],
            "unit": None if ready is None else ready["unit"],
            "check": None if ready is None else ready["check"],
            "judge": verdict,
            "card": card["card"],
            "dead_end": card["dead_end"],
            "proposal": None,
            "certificate": None,
            "lineage": (child(rows, "lineage") or {}).get("chain"),
            "summary": prose["summary"],
        }
    )
)
