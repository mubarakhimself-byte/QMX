"""A test run's stand-in for QMB and the referee: the verdict a real judge would land on a recorded
run, and its papers, from `fixtures/qmb.json` under the fixture's name. Each lands on this run's own
ref as an artifact of the kind it stands for, the verdict first, so the real `library` node reads it
as it reads a real one. Only a run whose inputs name a `fixture` comes here, and no model is asked
about a run that never happened. Zero tokens. The same file in every template that asks the referee.
"""

import json
import os
import sys
from pathlib import Path

given = json.load(sys.stdin)["in"]
recorded = json.loads((Path(os.environ["QMX_CODE"]) / "fixtures" / "qmb.json").read_text("utf-8"))
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
writes = []
for kind, metadata in recorded[given["recorded"]].items():
    (bodies / f"{kind}.json").write_text(json.dumps(metadata, sort_keys=True), encoding="utf-8")
    writes.append(
        {"op": "put_artifact", "type": kind, "body": f"library/{kind}.json", "metadata": metadata}
    )
print(json.dumps({"library": writes}))
