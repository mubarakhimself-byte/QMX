"""Land the new clippings in the Library and link the ones already held to what holds them.

A new clipping is stored as one artifact under its intent key. A clipping already held is not
stored again: the run stores one intake note and links it `consumed` to the object that already
holds the clipping, which is the "skip and link" of AD-27. Nothing is deleted.
"""

import json
import os
import sys
from pathlib import Path

from qmx_engine.ports.library_fake import LibraryFake
from qmx_engine.workers.zones import home_of

given = json.load(sys.stdin)["in"]
items = given if isinstance(given, list) else [given]
found = next((v for v in items if isinstance(v, dict) and "new" in v), {})
notes = next((v for v in items if isinstance(v, dict) and "notes" in v), {"notes": []})
summaries = {str(note.get("name")): note for note in notes.get("notes") or []}
run_id = os.environ["QMX_RUN_ID"]
principal = f"run:{run_id}"
new, linked = [], []
with LibraryFake.open(home_of(Path(os.environ["QMX_WORK_SHARED"]))) as library:
    for clipping in found.get("new") or []:
        note = summaries.get(str(clipping["name"]), {})
        body = json.dumps(
            {
                "name": clipping["name"],
                "title": clipping.get("title"),
                "hash": clipping["hash"],
                "summary": note.get("summary", ""),
                "hypothesis": note.get("hypothesis", ""),
            },
            sort_keys=True,
        ).encode()
        stored = library.put_artifact(
            body,
            "clipping",
            {"title": clipping.get("title"), "hash": clipping["hash"],
             "source": clipping.get("source")},
            run_id=run_id,
            principal=principal,
            intent_key=clipping["intent_key"],
        )
        new.append(
            {
                "name": clipping["name"],
                "hash": clipping["hash"],
                "intent_key": clipping["intent_key"],
                "status": "new",
                "object_id": stored.object_id,
                "summary": note.get("summary", ""),
            }
        )
    if found.get("held"):
        intake = library.put_artifact(
            json.dumps({"held": [c["name"] for c in found["held"]]}, sort_keys=True).encode(),
            "clipping-intake",
            {"count": len(found["held"])},
            run_id=run_id,
            principal=principal,
            intent_key=f"clipping-intake|{run_id}",
        )
        for clipping in found["held"]:
            for object_id in clipping["held"]:
                library.link(intake.object_id, "consumed", object_id, principal=principal)
            linked.append(
                {
                    "name": clipping["name"],
                    "hash": clipping["hash"],
                    "intent_key": clipping["intent_key"],
                    "status": "seen",
                    "object_id": clipping["held"][0],
                    "linked_to": list(clipping["held"]),
                    "intake_id": intake.object_id,
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
        }
    )
)
