"""Land the new clippings in the Library and link the ones already held to what holds them.

A new clipping is stored as one artifact under its intent key. A clipping already held is not
stored again: the run stores one intake note and links it `consumed` to the object that already
holds the clipping, which is the "skip and link" of AD-27. Nothing is deleted.

The script never opens the Library. It writes each body under `library/` in its overlay and lists
the writes under `library`; the runner makes them on the run's own ref and answers with
`library_written`, one receipt per write with the object id it got.
"""

import json
import os
import sys
from pathlib import Path

given = json.load(sys.stdin)["in"]
items = given if isinstance(given, list) else [given]
found = next((v for v in items if isinstance(v, dict) and "new" in v), {})
notes = next((v for v in items if isinstance(v, dict) and "notes" in v), {"notes": []})
summaries = {str(note.get("name")): note for note in notes.get("notes") or []}
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
writes, new, linked = [], [], []
for index, clipping in enumerate(found.get("new") or []):
    note = summaries.get(str(clipping["name"]), {})
    name = f"clipping-{index}.json"
    (bodies / name).write_text(
        json.dumps(
            {
                "name": clipping["name"],
                "title": clipping.get("title"),
                "hash": clipping["hash"],
                "summary": note.get("summary", ""),
                "hypothesis": note.get("hypothesis", ""),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    handle = f"clipping-{index}"
    writes.append(
        {
            "op": "put_artifact",
            "as": handle,
            "type": "clipping",
            "body": f"library/{name}",
            "metadata": {
                "title": clipping.get("title"),
                "hash": clipping["hash"],
                "source": clipping.get("source"),
            },
            "intent_key": clipping["intent_key"],
        }
    )
    new.append(
        {
            "name": clipping["name"],
            "hash": clipping["hash"],
            "intent_key": clipping["intent_key"],
            "status": "new",
            "handle": handle,
            "summary": note.get("summary", ""),
        }
    )
if found.get("held"):
    (bodies / "intake.json").write_text(
        json.dumps({"held": [c["name"] for c in found["held"]]}, sort_keys=True), encoding="utf-8"
    )
    writes.append(
        {
            "op": "put_artifact",
            "as": "intake",
            "type": "clipping-intake",
            "body": "library/intake.json",
            "metadata": {"count": len(found["held"])},
            "intent_key": f"clipping-intake|{os.environ['QMX_RUN_ID']}",
        }
    )
    for clipping in found["held"]:
        writes += [
            {"op": "link", "from": "$intake", "edge": "consumed", "to": object_id}
            for object_id in clipping["held"]
        ]
        linked.append(
            {
                "name": clipping["name"],
                "hash": clipping["hash"],
                "intent_key": clipping["intent_key"],
                "status": "seen",
                "object_id": clipping["held"][0],
                "linked_to": list(clipping["held"]),
                "handle": "intake",
            }
        )
counts = {"new": len(new), "seen": len(linked), "scanned": len(new) + len(linked)}
text = (
    f"{counts['new']} clippings were new and were summarised; "
    f"{counts['seen']} were already held and were linked to what holds them. "
    "A clipping is held once by its content hash and its intent key, so feeding the same one twice "
    "reads it once."
)
print(
    json.dumps(
        {
            "summary": text,
            "figures": counts,
            "new": new,
            "held": linked,
            "notes": notes.get("notes") or [],
            "library": writes,
        }
    )
)
