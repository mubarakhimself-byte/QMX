"""Spec completeness and assumptions (card R3 steps 2 and 3, card T8's exit rule). Its input is
the reported-numbers check's verdict on the source and the spec.

A reported number counts only when its value is written in its own quote; any other is dropped and
listed. Every open item becomes a labelled assumption. A missing exit gets the house exit policy,
labelled `external_policy`, never an invented one. More than two meaning-changing assumptions end
in a pick card with the reader's picks as the recommendations; otherwise each meaning-changing
assumption is built as its own branch, at most two, and every branch counts as a trial.
"""

import json
import re
import sys

MAX_BRANCHES = 2
NUMBER = re.compile(r"\d+(?:\.\d+)?")

graded = json.load(sys.stdin)["in"]
spec = next(v for v in graded["input"] if isinstance(v, dict) and "reported" in v)


def written(item):
    return any(abs(float(n) - abs(item["value"])) < 1e-9 for n in NUMBER.findall(item["quote"]))


reported = [r for r in spec["reported"] if written(r)]
dropped = [r["metric"] for r in spec["reported"] if not written(r)]
assumptions = [
    {
        "field": o["field"],
        "pick": o["pick"],
        "label": "assumption",
        "changes_meaning": o["changes_meaning"],
    }
    for o in spec["open_items"]
]
if spec["exit"] is None:
    assumptions.append(
        {
            "field": "exit",
            "pick": "house exit policy",
            "label": "external_policy",
            "changes_meaning": True,
        }
    )
meaning = [a for a in assumptions if a["changes_meaning"]]
pick_card = None
if len(meaning) > MAX_BRANCHES:
    options = [{"field": a["field"], "recommended": a["pick"]} for a in meaning]
    pick_card = {"kind": "pick assumptions", "options": options}
branches = max(len(meaning), 1) if pick_card is None else 1
fields = ("universe", "period", "signal", "rebalance", "costs", "variants_tried")
print(
    json.dumps(
        {
            "replication_spec": {k: spec[k] for k in fields}
            | {"exit": spec["exit"] or "external_policy"},
            "reported": reported,
            "dropped": dropped,
            "assumptions": assumptions,
            "branches": branches,
            "pick_card": pick_card,
        }
    )
)
