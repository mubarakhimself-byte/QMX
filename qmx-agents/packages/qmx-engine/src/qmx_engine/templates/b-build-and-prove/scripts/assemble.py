"""The funnel scorecard: the sealed spec, the stage reached, the judge's verdict, the card or the
dead end, and the writer's summary. A spec that failed its checks ends at stage 9 with its
problems and no backtest. Its inputs are told apart by shape; the `judge` block's verdict is found
by its key inside the child's nested outputs."""

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
given = given if isinstance(given, list) else [given]
sealed = next(v for v in given if "memo_key" in v)
verdict = judged([v for v in given if "dead_end" not in v])
card = next((v for v in given if "dead_end" in v), {"card": None, "dead_end": None})
prose = next((v for v in given if "summary" in v), {"summary": ""})
if verdict is None:
    stage, says = 9, "could not test: " + "; ".join(sealed["problems"])
else:
    stage, says = (12 if verdict["overall"] == "pass" else 10), verdict["says"]
print(
    json.dumps(
        {
            "stage_reached": stage,
            "verdict": says,
            "spec": sealed["spec"],
            "memo_key": sealed["memo_key"],
            "judge": verdict,
            "card": card["card"],
            "dead_end": card["dead_end"],
            "summary": prose["summary"],
        }
    )
)
