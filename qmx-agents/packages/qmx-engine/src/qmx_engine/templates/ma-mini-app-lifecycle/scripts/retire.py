"""The deprecate or archive card (card D8 steps 9 to 11 and its gates). Zero tokens.

Deprecating names what replaces the app. Archiving an app with live consumers needs each one
rewired or explicitly accepted as stale; until then the card says which. Versions, evidence, logs
and artifacts are always kept, the old version stays installable for rollback, and there is no
delete. The card waits for his approval; consumers get a "producer archived" event after it.
"""

import json
import sys

read = json.load(sys.stdin)["in"]
request, app = read["request"], read["app"]
live = [c for c in read["consumers"] if not c.get("rewired") and not c.get("accepted_stale")]
problems = []
if app["lifecycle"] == "archived":
    problems.append("the app is already archived")
if request["kind"] == "deprecate" and not request.get("replaced_by"):
    problems.append("a deprecation names what replaces the app")
if request["kind"] == "archive" and live:
    problems.append("live consumers must be rewired or accepted as stale first")
print(
    json.dumps(
        {
            "app": request["app_id"],
            "kind": request["kind"],
            "from": app["lifecycle"],
            "to": "deprecated" if request["kind"] == "deprecate" else "archived",
            "replaced_by": request.get("replaced_by"),
            "blast_radius": [{"id": c["id"], "kind": c["kind"]} for c in read["consumers"]],
            "live_consumers": [c["id"] for c in live],
            "kept": ["versions", "evidence", "logs", "artifacts"],
            "problems": problems,
            "card": None if problems else {"kind": request["kind"], "waits_for": "his approval"},
        }
    )
)
