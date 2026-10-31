"""What landed and what ran since the operator's last look.

The landed items are the objects that moved onto `main` after his cursor's position, which the
runner reads from the Library for this step (`library.landed`). What a test, fake or failed run
wrote stays on its own run ref, so it never lands here. The runs are the live ones on real models
that finished since the cursor's time, with the failed ones named: a failure that needs him is the
part of the digest he acts on.
"""

import json
import os
import sys
from pathlib import Path

from qmx_engine.ledger.store import Reader
from qmx_engine.workers.zones import home_of

payload = json.load(sys.stdin)
given = payload["in"]
state = given if isinstance(given, dict) else next((v for v in given if isinstance(v, dict)), {})
position = int(state.get("position") or 0)
since = state.get("at")
landed = [
    {key: event[key] for key in ("seq", "name", "object_id", "ref")}
    for event in payload["library"]["landed"]
]
ran, failed = [], []
with Reader.open(home_of(Path(os.environ["QMX_WORK_SHARED"]))) as reader:
    created = {
        str(run_id): json.loads(data)
        for run_id, data in reader.connection.execute(
            "SELECT run_id, data FROM events WHERE kind = 'run_created'"
        ).fetchall()
    }
    rows = reader.connection.execute(
        "SELECT run_id, at, data FROM events WHERE kind = 'run_finished' ORDER BY at"
    ).fetchall()
for run_id, at, data in rows:
    if since is not None and str(at) < str(since):
        continue
    made = created.get(str(run_id), {})
    if made.get("mode") != "live" or made.get("fake") is True:
        continue
    found = json.loads(data)
    row = {"run_id": str(run_id), "status": found.get("status"), "reason": found.get("reason")}
    (ran if row["status"] == "passed" else failed).append(row)
print(
    json.dumps(
        {
            "position": position,
            "since": since,
            "landed": landed,
            "ran": ran,
            "failed": failed,
            "highest": max([position, *(item["seq"] for item in landed)]),
            "fixture": state.get("fixture"),
        }
    )
)
