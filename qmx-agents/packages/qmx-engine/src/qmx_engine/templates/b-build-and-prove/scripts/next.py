"""What follows the referee's verdict, for the shared blocks to land. Zero tokens.

Its inputs are `Ready to test?`'s answer (the unit's pin) and the referee step's `verdict`, which
the referee step copies from the core's `backtest_judge_run` answer; the verdict is the core's
script's, and nothing here changes it. It prints:

- `proposal`, for the `proposal-card` block on a pass: ask `paper`, the unit's pin as its subject,
  the verdict and the results as its evidence, the tries behind it. Otherwise null.
- `item`, `verdict` and `says`, the `judge` block's shape, for the `death-certificate` block on a
  `fail` or `no_trades`, which classifies the cause and refuses any other outcome.
- `lineage`, for the `lineage` block: the unit's pin and the first result it was tested by.
"""

import json
import sys

given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
ready = next(r for r in rows if "recorded" in r)
verdict = next(r["verdict"] for r in rows if isinstance(r.get("verdict"), dict))
pin = ready["unit"]["pin"]
results = verdict["result_ids"]
tries = {"raw": verdict["raw_tries"], "effective": verdict["effective_tries"]}
proposal = None
if verdict["overall"] == "pass":
    proposal = {
        "subject": pin,
        "ask": "paper",
        "evidence": [verdict["verdict_id"], *results],
        "verdict": verdict["verdict_id"],
        "tries": tries,
        "why": verdict["says"],
        "cost": {"qmb_runs": len(results)},
    }
print(
    json.dumps(
        {
            "proposal": proposal,
            "item": verdict["verdict_id"],
            "verdict": {
                "overall": verdict["overall"],
                "unit": pin,
                "per_market": verdict["per_market"],
            },
            "says": verdict["says"],
            "lineage": {"unit": pin, "result": results[0]},
        }
    )
)
