"""The starting state of the generations: the parent as the first best, its validated score as
the bar, the family's spec hashes for the dedupe, and the diagnosis each child must answer. Its
inputs, the blinded report and the diagnosis, are told apart by shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
blinded = next(v for v in given if "report" in v)
diagnosis = next(v for v in given if "weaknesses" in v)
parent = blinded["parent"]
print(
    json.dumps(
        {
            "parent": parent,
            "best": parent,
            "best_score": parent["validated"],
            "report": blinded["report"],
            "weaknesses": diagnosis["weaknesses"],
            "family_hashes": blinded["family"]["spec_hashes"],
            "family_trials": blinded["family"]["trials"],
            "generation": 0,
            "children": [],
        }
    )
)
