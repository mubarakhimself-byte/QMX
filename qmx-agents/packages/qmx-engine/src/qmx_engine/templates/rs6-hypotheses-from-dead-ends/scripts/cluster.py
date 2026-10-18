"""The pre-check and the clusters (card R6 pre-check and step 2). Zero tokens.

Wakes only when at least 5 dead ends were added since the workflow last mined; otherwise prints an
empty list and the run ends silent. Clusters the new dead ends by bucket, market and mechanism,
largest first, at most 10 (one model call each). Each cluster carries its dead ends' ids, sources
and families, the highest trial count among its parent families, and the latest end of any window a
parent touched, so a hypothesis is tested only on data after it.
"""

import json
import sys

WAKE_AT = 5
MAX_CLUSTERS = 10

library = json.load(sys.stdin)["in"]
mined = set(library["mined"])
new = [d for d in library["dead_ends"] if d["id"] not in mined]
groups = {}
for dead in new:
    groups.setdefault((dead["bucket"], dead["market"], dead["mechanism"]), []).append(dead)
clusters = [
    {
        "cluster": f"c{k + 1}",
        "bucket": bucket,
        "market": market,
        "mechanism": mechanism,
        "dead_ends": [
            {"id": d["id"], "source": d["source"], "family": d["family"]} for d in members
        ],
        "parent_trials": max(d["family_trials"] for d in members),
        "parent_windows_end": max(w["end"] for d in members for w in d["windows"]),
        "new_dead_ends": len(new),
    }
    for k, ((bucket, market, mechanism), members) in enumerate(
        sorted(groups.items(), key=lambda kv: -len(kv[1]))[:MAX_CLUSTERS]
    )
]
print(json.dumps(clusters if len(new) >= WAKE_AT else []))
