"""Where the unit's rules hold, by the referee's verdict over every context tried. Zero tokens.

Its inputs are the route's asks and the referee step's `verdict`, copied from the core's
`backtest_judge_run` answer over every result: the verdict is corrected for every market and
session tried. A market the verdict passes is where the rules hold; it becomes one proposal to
admit that market, for his click. Nothing is admitted here. It prints `holds`, `fails`,
`sessions` (the scenarios tried), the verdict, and `proposal` (null when nothing holds).
"""

import json
import sys

given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
routed = next(r for r in rows if "sweep" in r)
verdict = next(r["verdict"] for r in rows if isinstance(r.get("verdict"), dict))
holds = [m["market"] for m in verdict["per_market"] if m["outcome"] == "pass"]
fails = [m["market"] for m in verdict["per_market"] if m["outcome"] != "pass"]
unit = routed["sweep"]["unit"]
proposal = None
if holds:
    proposal = {
        "subject": unit,
        "ask": "admit_market",
        "evidence": [verdict["verdict_id"], *verdict["result_ids"]],
        "verdict": verdict["verdict_id"],
        "tries": {"raw": verdict["raw_tries"], "effective": verdict["effective_tries"]},
        "why": f"the rules hold on {', '.join(holds)}. {verdict['says']}",
        "placeholders": {"markets": holds},
    }
whatif = routed["whatif"]
print(
    json.dumps(
        {
            "unit": unit,
            "holds": holds,
            "fails": fails,
            "sessions": [] if whatif is None else [s["params"] for s in whatif["scenarios"]],
            "verdict": {
                k: verdict[k]
                for k in ("verdict_id", "overall", "says", "raw_tries", "effective_tries")
            },
            "proposal": proposal,
        }
    )
)
