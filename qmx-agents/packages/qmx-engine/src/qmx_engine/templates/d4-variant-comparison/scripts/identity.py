"""The identity rule and the counts (card D4 steps 2 and 3 and its budget guard). Its inputs, the
run's inputs and the planned variants, are told apart by shape.

The identity rule is a table: an instrument, timeframe, parameter or spiced variant stays a variant
of the strategy (`variant_of`); a structural or model-made variant is a new strategy derived from it
(`derived_from`). A run keeps the card's `variants` (from the run's inputs, else its `default` in
`definition.json`, a starting default and never a cap) and at most 4 that need a builder; the rest
are refused with the reason. Config variants are branches made by script: the parent's spec with
the overrides.
"""

import json
import os
import sys
from pathlib import Path

MAX_BUILT = 4
LINEAGE = {
    "instrument": "variant_of",
    "timeframe": "variant_of",
    "params": "variant_of",
    "spiced": "variant_of",
    "structural": "derived_from",
    "model-made": "derived_from",
}
NEEDS_BUILDER = ("spiced", "structural", "model-made")

card = json.loads((Path(os.environ["QMX_CODE"]) / "definition.json").read_text("utf-8"))
given = json.load(sys.stdin)["in"]
request = next(v for v in given if "strategy" in v)
strategy = request["strategy"]
planned = next(v for v in given if isinstance(v.get("variants"), list))["variants"]
kept = request.get("variants", card["inputs"]["properties"]["variants"]["default"])
config, build, refused = [], [], []
for k, variant in enumerate(planned):
    row = variant | {
        "variant": f"v{k + 1}",
        "edge": LINEAGE[variant["label"]],
        "spec": strategy["spec"] | variant["overrides"],
    }
    if k >= kept:
        refused.append({"variant": row["variant"], "why": f"over the {kept} variants of a run"})
    elif variant["label"] in NEEDS_BUILDER:
        if len(build) < MAX_BUILT:
            build.append(row)
        else:
            refused.append({"variant": row["variant"], "why": "over the 4 built variants"})
    else:
        config.append(row)
print(json.dumps({"parent": strategy["id"], "config": config, "build": build, "refused": refused}))
