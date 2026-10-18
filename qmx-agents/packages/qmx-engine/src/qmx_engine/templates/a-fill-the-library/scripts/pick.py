"""The items to understand (funnel stage 4): every triaged item in the strategy, component, hint or
knowledge buckets, carrying its triage time map so the sections step skips promo windows. Its
inputs, the items and their triage verdicts, are told apart by shape."""

import json
import sys

WANTED = {"full strategy", "component", "hint", "knowledge"}

given = json.load(sys.stdin)["in"]
items = next(v for v in given if v and "keyword_hits" in v[0])
verdicts = {v["item_id"]: v for v in next(v for v in given if v and "buckets" in v[0])}
print(
    json.dumps(
        [
            item | {"time_map": verdicts[item["id"]].get("time_map") or []}
            for item in items
            if item["id"] in verdicts and WANTED & set(verdicts[item["id"]]["buckets"])
        ]
    )
)
