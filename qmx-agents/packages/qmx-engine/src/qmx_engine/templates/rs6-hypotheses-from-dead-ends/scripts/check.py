"""Dedupe and gate (card R6 steps 4 and 5 and its kill rules). Its inputs, the Library read, the
clusters and every cluster's hypotheses, are told apart by shape.

A hypothesis is dropped, with the reason, when its parents are not dead ends of its own cluster,
when its mechanism or kill rule is empty, when an `invert` has no mechanism beyond the flip, or
when it repeats an open term sheet, an existing card or an idea he rejected (same market and
mechanism). A kept one inherits the highest trial count of its parent families, and its test data
starts after the last window any parent touched: it may never be tested on a parent's holdout.
`drop` moves become "do not retry" notes.
"""

import json
import sys

given = json.load(sys.stdin)["in"]
given = given if isinstance(given, list) else [given]
library = next(v for v in given if isinstance(v, dict) and "dead_ends" in v)
lists = [v for v in given if isinstance(v, list)]
answers = next((v for v in lists if v and all("hypotheses" in a for a in v)), [])
clusters = next((v for v in lists if v is not answers), [])
by_cluster = {c["cluster"]: c for c in clusters}
seen = {
    (s["market"], s["mechanism"].casefold())
    for s in library["open_term_sheets"] + library["cards"] + library["rejected"]
}
kept, dropped, notes = [], [], []
for found in (h for answer in answers for h in answer["hypotheses"]):
    cluster = by_cluster.get(found["cluster"])
    own = {d["id"] for d in cluster["dead_ends"]} if cluster else set()
    if found["move"] == "drop":
        notes.append(
            {
                "tag": "do_not_retry",
                "cluster": found["cluster"],
                "note": found["hypothesis"],
                "parents": found["parents"],
            }
        )
        continue
    reasons = []
    if not found["parents"] or not set(found["parents"]) <= own:
        reasons.append("its parents are not dead ends of its cluster")
    if not found["mechanism"].strip() or not found["kill_rule"].strip():
        reasons.append("it has no mechanism or no kill rule")
    if found["move"] == "invert" and len(found["mechanism"].split()) < 6:
        reasons.append("an invert needs a mechanism, not just a sign flip")
    key = (cluster["market"] if cluster else "", found["mechanism"].casefold())
    if key in seen:
        reasons.append("it repeats an open term sheet, a card or a rejected idea")
    if reasons:
        dropped.append({"hypothesis": found["hypothesis"], "why": "; ".join(reasons)})
        continue
    kept.append(
        found
        | {
            "market": cluster["market"],
            "bucket": cluster["bucket"],
            "inherited_trials": cluster["parent_trials"],
            "test_data_after": cluster["parent_windows_end"],
        }
    )
print(json.dumps({"kept": kept, "dropped": dropped, "notes": notes}))
