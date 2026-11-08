"""The `lineage` block's one step: the one writer of a run's lineage (Part B AD-213).

Its input is `{"in": {"lineage": {...}}}`, naming a Library object id for any of the stages
`source`, `idea`, `unit`, `version` and `result`. A stage left out is left out, never guessed, and
at least one stage is named.

It lands one `artifact` of type `lineage` on the run's own ref: the run's chain in stage order,
from source to result, each stage with its object. It links the record to every object in the
chain by `consumed`, the one edge of the engine's set a script may write that means "this run
used it", so the record is found from any object in its chain and read from source to result.
No model chooses the lineage. It prints the chain and the writes; the runner answers each link
with whether it was written or refused.
"""

import json
import os
import sys
from pathlib import Path

FAILURE = "[QMX_FAILURE]"
STAGES = ("source", "idea", "unit", "version", "result")
EDGE = "consumed"

given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
named = next((r["lineage"] for r in rows if isinstance(r.get("lineage"), dict)), None)
if named is None:
    print(f"{FAILURE} the lineage block needs a lineage naming {', '.join(STAGES)}")
    raise SystemExit(0)
unknown = sorted(set(named) - set(STAGES))
chain = [
    {"stage": stage, "object_id": named[stage]}
    for stage in STAGES
    if isinstance(named.get(stage), str) and named[stage]
]
if unknown or not chain:
    why = f"no stage {', '.join(unknown)}" if unknown else "it names no stage's object"
    print(f"{FAILURE} the lineage {why}; the stages are {', '.join(STAGES)}")
    raise SystemExit(0)

run_id = os.environ["QMX_RUN_ID"]
record = {"run_id": run_id, "chain": chain}
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
(bodies / "lineage.json").write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
writes = [
    {
        "op": "put_artifact",
        "as": "record",
        "type": "lineage",
        "body": "library/lineage.json",
        "metadata": record,
        "intent_key": f"lineage|{run_id}",
    },
    *({"op": "link", "from": "$record", "edge": EDGE, "to": s["object_id"]} for s in chain),
]
print(json.dumps({"chain": chain, "library": writes}))
