"""Split the clippings into the ones the Library already holds and the ones it does not.

The runner looks every clipping's intent key up in the Library for this step (`library.held`),
computed from the content hash and the source with no model, so the same clipping fed twice runs
once and the second run links to the first (AD-27). Only a clipping a passed live run stored
counts as held: a test, fake or failed run's copy never does. Nothing is deleted.
"""

import json
import sys

payload = json.load(sys.stdin)
given = payload["in"]
scanned = given if isinstance(given, dict) else next((v for v in given if isinstance(v, dict)), {})
holders = payload.get("library", {}).get("held") or {}
new, held = [], []
for clipping in scanned.get("clippings") or []:
    found = [str(object_id) for object_id in holders.get(clipping["intent_key"]) or []]
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
