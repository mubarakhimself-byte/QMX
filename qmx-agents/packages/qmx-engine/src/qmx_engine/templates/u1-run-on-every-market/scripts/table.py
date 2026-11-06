"""One row per market he asked for: the referee's outcome and trades for it. Zero tokens.

Its inputs are the route's `ask` and the stored verdict, which the Library holds. Every cell of
the sweep is a counted try in the unit's
family, so the verdict is already corrected for having looked at every market. A market he asked
for that the verdict does not judge is listed under `unjudged`, so a market with no data is
never silently dropped.
"""

import json
import sys

given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
ask = next(r["ask"] for r in rows if "ask" in r)
verdict = next(r["verdict"] for r in rows if isinstance(r.get("verdict"), dict))
judged = {m["market"]: m for m in verdict["per_market"]}
asked = ask["grid"]["markets"]
print(
    json.dumps(
        {
            "unit": ask["unit"],
            "window": ask["window"],
            "markets": [
                {"market": m, "outcome": judged[m]["outcome"], "trades": judged[m].get("trades")}
                for m in asked
                if m in judged
            ],
            "unjudged": [m for m in asked if m not in judged],
            "verdict": {
                k: verdict[k]
                for k in ("verdict_id", "overall", "says", "raw_tries", "effective_tries")
            },
        }
    )
)
