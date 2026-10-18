"""The zero-token pre-check (card R8): every data handle resolves to a size, and a dry estimate of
sub-calls and cost is made before any model call. Sub-calls are the data split into slices of
50 MB, at most 200 children; each is priced at the cheap `rlm-sub` row's list price for one slice.
Above his "ask above" number the run ends with a cost card instead of spending.
"""

import json
import math
import sys

SLICE_BYTES = 50_000_000
MAX_CHILDREN = 200
USD_PER_SUB_CALL = 0.004
ROOT_USD = 0.25

given = json.load(sys.stdin)["in"]
unresolved = [h["name"] for h in given["handles"] if h.get("bytes") is None]
total = sum(h.get("bytes") or 0 for h in given["handles"])
sub_calls = min(math.ceil(total / SLICE_BYTES), MAX_CHILDREN)
usd = round(ROOT_USD + sub_calls * USD_PER_SUB_CALL, 2)
ask_above = given.get("ask_above_usd", 2.0)
within = not unresolved and usd <= ask_above
print(
    json.dumps(
        {
            "question": given["question"],
            "handles": [h["name"] for h in given["handles"]],
            "unresolved": unresolved,
            "total_bytes": total,
            "sub_calls": sub_calls,
            "estimate_usd": usd,
            "ask_above_usd": ask_above,
            "within": within,
        }
    )
)
