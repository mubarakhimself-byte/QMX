"""The funnel scorecard: the sealed spec, the stage reached, every gate, the verdict, the card or
the dead end, and the writer's summary. A spec that failed its checks ends at stage 9 with its
problems and no backtest. Its inputs are told apart by shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
given = given if isinstance(given, list) else [given]
sealed = next(v for v in given if "memo_key" in v)
gates = next((v for v in given if "gates" in v), None)
card = next((v for v in given if "dead_end" in v), {"card": None, "dead_end": None})
prose = next((v for v in given if "summary" in v), {"summary": ""})
if gates is None:
    stage, verdict = 9, "could not test: " + "; ".join(sealed["problems"])
else:
    stage, verdict = (12 if gates["survives"] else 10), gates["verdict"]
print(
    json.dumps(
        {
            "stage_reached": stage,
            "verdict": verdict,
            "spec": sealed["spec"],
            "memo_key": sealed["memo_key"],
            "gates": gates["gates"] if gates else [],
            "card": card["card"],
            "dead_end": card["dead_end"],
            "summary": prose["summary"],
        }
    )
)
