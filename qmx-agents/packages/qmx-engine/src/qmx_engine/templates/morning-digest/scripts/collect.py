"""What landed and what ran since the operator's last look.

The landed items are the Library log's entries after his cursor's position. The runs are the ones
that finished since the cursor's time, with the failed ones named: a failure that needs him is the
part of the digest he acts on.
"""

import json
import os
import sys
from pathlib import Path

from qmx_engine.ledger.store import Reader
from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.workers.zones import home_of

given = json.load(sys.stdin)["in"]
state = given if isinstance(given, dict) else next((v for v in given if isinstance(v, dict)), {})
position = int(state.get("position") or 0)
since = state.get("at")
home = home_of(Path(os.environ["QMX_WORK_SHARED"]))
with LibraryFake.open(home) as library:
    events = library.events(after=position)
landed = [
    {"seq": event.seq, "name": event.name, "object_id": event.object_id, "ref": event.ref}
    for event in events
]
ran, failed = [], []
with Reader.open(home) as reader:
    rows = reader.connection.execute(
        "SELECT run_id, at, data FROM events WHERE kind = 'run_finished' ORDER BY at"
    ).fetchall()
for run_id, at, data in rows:
    if since is not None and str(at) < str(since):
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
