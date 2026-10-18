"""The quick gates of a first result (card L1 step 9 and its kill rules). Every result is
in-sample only and says so.

At least 30 trades; the lookahead lint passes, or the result is shown as "blocked: lookahead" with
the line and no number; expectancy stays positive with costs on; every trade sits inside the
stated session. A daily Sharpe above 2 carries the banner "assume lookahead until shown otherwise".
"""

import json
import sys

MIN_TRADES = 30
LOOKAHEAD_DAILY_SHARPE = 2

runs = json.load(sys.stdin)["in"]
results = []
for found in runs["readings"]:
    if found.get("refused"):
        results.append({"reading": found["reading"], "status": f"refused: {found['refused']}"})
        continue
    lint = found["lookahead_lint"]
    if not lint["passed"]:
        results.append(
            {"reading": found["reading"], "status": f"blocked: lookahead at {lint['line']}"}
        )
        continue
    outside = [t for t in found["trades"] if t["session"] != found["session"]]
    gates = {
        "trades": len(found["trades"]) >= MIN_TRADES,
        "costs on": found["costs_on_expectancy_r"] > 0,
        "in session": not outside,
    }
    results.append(
        {
            "reading": found["reading"],
            "status": "shown",
            "stamp": "in-sample only",
            "trades": len(found["trades"]),
            "sharpe": found["sharpe"],
            "expectancy_r": found["expectancy_r"],
            "costs_on_expectancy_r": found["costs_on_expectancy_r"],
            "trades_outside_session": len(outside),
            "gates": gates,
            "banner": "assume lookahead until shown otherwise"
            if found["daily_sharpe"] > LOOKAHEAD_DAILY_SHARPE
            else None,
        }
    )
print(json.dumps({"results": results}))
