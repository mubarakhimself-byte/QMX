"""Where the unit's rules hold, by the referee's verdict over every context tried. Zero tokens.

Its inputs are the route's asks and the stored verdict with the core's papers on it, which the
Library holds: the verdict is corrected for every market and session tried. A market the verdict
passes is where the rules hold; it becomes one proposal to admit that market, for his click, with
the core's own paper card among its evidence. Nothing is admitted here. It prints `holds`, `fails`,
`sessions` (the scenarios tried), the verdict, and `proposal` (null when nothing holds). The
referee's answer judges each market, not each session, so the proposal names the sessions tried
and counted but never one session as the one that held.
"""

import json
import sys

given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
routed = next(r for r in rows if "sweep" in r)
stored = next(r for r in rows if "cards" in r)
verdict = stored["verdict"]
core = [c["object_id"] for k, c in stored["cards"].items() if k == "proposal-card"]
holds = [m["market"] for m in verdict["per_market"] if m["outcome"] == "pass"]
fails = [m["market"] for m in verdict["per_market"] if m["outcome"] != "pass"]
unit = routed["sweep"]["unit"]
whatif = routed["whatif"]
sessions = [] if whatif is None else [s["params"] for s in whatif["scenarios"]]
hours = ", ".join(f"{s['from']}:00 to {s['to']}:00 UTC" for s in sessions)
tried = f", with the sessions {hours} tried and counted" if sessions else ""
proposal = None
if holds:
    proposal = {
        "subject": unit,
        "ask": "admit_market",
        "evidence": [verdict["verdict_id"], *core, *verdict["result_ids"]],
        "verdict": verdict["verdict_id"],
        "tries": {"raw": verdict["raw_tries"], "effective": verdict["effective_tries"]},
        "why": f"the rules hold on {', '.join(holds)}{tried}. {verdict['says']}",
        "placeholders": {"markets": holds},
    }
print(
    json.dumps(
        {
            "unit": unit,
            "holds": holds,
            "fails": fails,
            "sessions": sessions,
            "verdict": {
                k: verdict[k]
                for k in ("verdict_id", "overall", "says", "raw_tries", "effective_tries")
            },
            "proposal": proposal,
        }
    )
)
