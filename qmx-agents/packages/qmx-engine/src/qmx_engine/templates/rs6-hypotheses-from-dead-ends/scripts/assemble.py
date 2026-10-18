"""Rank and short list (card R6 steps 7 and 8). Its inputs, the clusters and the checked
hypotheses, are told apart by shape.

Ranks by evidence (dead ends behind it) less the cost to test its move (a regime filter or a slower
version is cheap, a transplant needs a build, an invert needs the most proof), and keeps at most 5
for his pick. Nothing runs without a pick. Fewer than 5 new dead ends ends silent.
"""

import json
import sys

SHORT_LIST = 5
COST = {"condition": 1, "slow_down": 1, "transplant": 2, "invert": 3}

given = json.load(sys.stdin)["in"]
given = given if isinstance(given, list) else [given]
clusters = next((v for v in given if isinstance(v, list)), [])
checked = next(
    (v for v in given if isinstance(v, dict) and "kept" in v),
    {"kept": [], "dropped": [], "notes": []},
)
ranked = sorted(checked["kept"], key=lambda h: COST[h["move"]] - 2 * len(h["parents"]))
short = ranked[:SHORT_LIST]
print(
    json.dumps(
        {
            "silent": not clusters,
            "new_dead_ends": clusters[0]["new_dead_ends"] if clusters else 0,
            "clusters": len(clusters),
            "short_list": short,
            "scores": [2 * len(h["parents"]) - COST[h["move"]] for h in short],
            "dropped": checked["dropped"],
            "notes": checked["notes"],
            "pick_card": {"kind": "pick hypotheses", "options": len(short)} if short else None,
        }
    )
)
