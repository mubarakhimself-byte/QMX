"""The checklist verdict per proposed decision (card T6 step 6, card P4 pre-check), all green
required. Defaults until the risk session sets them: the demo or paper minimum met (2 weeks and 100
trades for scalpers, 30 trades for paper to live), results inside the Monte Carlo band, live cost at
most 1.25 times the assumed cost, the overfit audit passed on the current content hash, no stress
scenario breaching the kill line unstopped, a validation verdict of approve or approve with
conditions, a clean tighten-only history, the prop-firm rules compatible, and no open red incident.
A missing piece reads "missing", and the checklist cannot then be all green. At most three
decisions go in one pack.
"""

import json
import sys

MOST_CARDS = 3
COST_CEILING = 1.25

pack = json.load(sys.stdin)["in"]
decisions = []
for item in pack["decisions"][:MOST_CARDS]:
    e = item["evidence"]
    tests = {
        "minimum evidence": (
            "journal",
            lambda j, _: j["days"] >= j["min_days"] and j["trades"] >= j["min_trades"],
        ),
        "inside the band": ("journal", lambda j, _: j["band"] == "inside"),
        "live cost": ("costs", lambda c, _: c["ratio"] <= COST_CEILING),
        "overfit audit": (
            "audit",
            lambda a, ev: a["verdict"] == "pass" and a["hash"] == ev.get("content_hash"),
        ),
        "stress": ("stress", lambda s, _: s["unstopped_breaches"] == 0),
        "validation": (
            "validation",
            lambda v, _: v["verdict"] in ("approve", "approve with conditions"),
        ),
        "tighten-only history": ("tighten_history", lambda h, _: h["violations"] == 0),
        "prop-firm rules": ("prop_rules", lambda p, _: p["compatible"]),
        "no open red incident": ("incidents", lambda i, _: i["open_red"] == 0),
    }
    rows = {
        row: "missing" if e.get(name) is None else "green" if test(e[name], e) else "red"
        for row, (name, test) in tests.items()
    }
    decisions.append(
        item | {"checklist": rows, "all_green": all(v == "green" for v in rows.values())}
    )
print(json.dumps({"decisions": decisions, "held_back": len(pack["decisions"]) - len(decisions)}))
