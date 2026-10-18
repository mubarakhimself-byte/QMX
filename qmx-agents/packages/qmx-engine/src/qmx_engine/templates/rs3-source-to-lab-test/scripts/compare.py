"""The verdict, set by script (card R3 step 6 and its gates). Its inputs, the assumptions and the
Lab runs, are told apart by shape.

Each reported number is set beside ours. Sharpe holds inside the tolerance band (plus or minus 0.3
by default); every other reported effect must keep its sign. Replicated: every number holds.
Partially: every sign holds, a size is off. Not replicated: a sign flips or a number has no match.
Could not test: the Lab said so. A daily Sharpe above 2 holds the verdict for a lookahead audit.
The decay ratio is the post-publication Sharpe over ours in-sample.
"""

import json
import sys

SHARPE_BAND = 0.3
LOOKAHEAD_DAILY_SHARPE = 2

given = json.load(sys.stdin)["in"]
spec = next(v for v in given if "reported" in v)
runs = next(v for v in given if "in_sample" in v or "could_not_test" in v)
rows = []
if runs.get("could_not_test"):
    verdict = f"could not test: {runs['could_not_test']}"
else:
    for item in spec["reported"]:
        ours = runs["in_sample"].get(item["metric"])
        sign_holds = ours is not None and (ours >= 0) == (item["value"] >= 0)
        if item["metric"] == "sharpe":
            holds = ours is not None and abs(ours - item["value"]) <= SHARPE_BAND
        else:
            holds = sign_holds
        rows.append(
            {
                "metric": item["metric"],
                "reported": item["value"],
                "ours": ours,
                "costs_on": runs["costs_on"].get(item["metric"]),
                "post_publication": runs["post_publication"].get(item["metric"]),
                "holds": holds,
                "sign_holds": sign_holds,
            }
        )
    if runs["in_sample"]["daily_sharpe"] > LOOKAHEAD_DAILY_SHARPE:
        verdict = "held for a lookahead audit"
    elif rows and all(r["holds"] for r in rows):
        verdict = "replicated"
    elif rows and all(r["sign_holds"] for r in rows):
        verdict = "partially"
    else:
        verdict = "not replicated"
ours_sharpe = runs.get("in_sample", {}).get("sharpe")
post = runs.get("post_publication", {}).get("sharpe")
decay = round(post / ours_sharpe, 2) if ours_sharpe and post is not None else None
print(
    json.dumps({"verdict": verdict, "rows": rows, "decay_ratio": decay, "trials": spec["branches"]})
)
