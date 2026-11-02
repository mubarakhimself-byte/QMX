"""The starting state of the generations: the parent as the first best, its validated score as
the bar, the family's spec hashes for the dedupe, the diagnosis each child must answer, and the
loop's counts. Its inputs, the run's request, the blinded report and the diagnosis, are told apart
by shape.

The counts are on the card: `generations` and `generations_without_gain` from the request, each
one left out taking its `default` in `definition.json`. They are starting defaults, never caps."""

import json
import os
import sys
from pathlib import Path

card = json.loads((Path(os.environ["QMX_CODE"]) / "definition.json").read_text("utf-8"))
given = json.load(sys.stdin)["in"]
request = next(v for v in given if "report" not in v and "weaknesses" not in v)
blinded = next(v for v in given if "report" in v)
diagnosis = next(v for v in given if "weaknesses" in v)
counts = {
    name: request.get(name, card["inputs"]["properties"][name]["default"])
    for name in ("generations", "generations_without_gain")
}
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
            **counts,
            "without_gain": 0,
            "stop": False,
        }
    )
)
