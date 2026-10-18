"""The change card: the week's runs, parked runs and open inbox items exactly as the engine reported
them, the analyst's clusters, the linted edits, and a one-line summary counted from those facts.
Its inputs are told apart by shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
week = next(v for v in given if isinstance(v, dict) and "runs" in v)
clusters = next(v for v in given if isinstance(v, dict) and "clusters" in v)["clusters"]
edits = next(v for v in given if isinstance(v, dict) and "edits" in v)["edits"]
passed = sum(run["status"] == "passed" for run in week["runs"])
untested = sum(e["status"].startswith("untested") for e in edits)
summary = (
    f"{len(week['runs'])} runs this week, {passed} passed, {len(week['parked'])} parked, "
    f"{len(week['inbox'])} open inbox items; {len(clusters)} failure clusters and "
    f"{untested} untested edits for review."
)
print(
    json.dumps(
        {
            "summary": summary,
            "week": {"from": week["from"], "to": week["to"], "source": week["source"]},
            "runs": week["runs"],
            "parked": week["parked"],
            "inbox": week["inbox"],
            "clusters": clusters,
            "edits": edits,
        }
    )
)
