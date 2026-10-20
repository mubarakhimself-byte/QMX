"""Split the clippings into the ones the Library already holds and the ones it does not.

The check reads the Library's own `intent_key` field on its artifacts, computed from the content hash
and the intent key with no model, so the same clipping fed twice runs once and the second run links
to the first (AD-27). Nothing is deleted: a clipping already held stays where it is.

The engine's Library port answers `find_by_intent` once its store writes the `produced-by` edge; until
then the same rows are read from the store's artifact fields, which is the field the port's query
names.
"""

import json
import os
import sys
from pathlib import Path

from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.workers.zones import home_of

HELD = "SELECT object_id FROM objects WHERE kind = 'artifact' AND json_extract(fields, '$.intent_key') = ?"

given = json.load(sys.stdin)["in"]
scanned = given if isinstance(given, dict) else next((v for v in given if isinstance(v, dict)), {})
home = home_of(Path(os.environ["QMX_WORK_SHARED"]))
new, held = [], []
with LibraryFake.open(home) as library:
    for clipping in scanned.get("clippings") or []:
        found = [
            str(row[0])
            for row in library.db.execute(HELD, (clipping["intent_key"],)).fetchall()
        ]
        if found:
            held.append({**clipping, "held": found, "status": "seen"})
        else:
            new.append({**clipping, "held": [], "status": "new"})
print(
    json.dumps(
        {
            "kind": scanned.get("kind", "clipping"),
            "new": new,
            "held": held,
            "has_new": bool(new),
            "count": len(new) + len(held),
        }
    )
)
