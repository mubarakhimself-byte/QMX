"""The head-to-head page: the variants planned with their labels and lineage edges, the comparison,
the refused variants, and the writer's summary. He picks which go forward. Its inputs are told
apart by shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
plan = next(v for v in given if "config" in v)
compared = next(v for v in given if "cards" in v)
prose = next((v for v in given if "summary" in v), {"summary": ""})
lineage = [
    {"variant": v["variant"], "label": v["label"], "edge": v["edge"], "name": v["name"]}
    for v in plan["config"] + plan["build"]
]
print(
    json.dumps(
        compared
        | {
            "parent": plan["parent"],
            "lineage": lineage,
            "refused_variants": plan["refused"],
            "summary": prose["summary"],
        }
    )
)
