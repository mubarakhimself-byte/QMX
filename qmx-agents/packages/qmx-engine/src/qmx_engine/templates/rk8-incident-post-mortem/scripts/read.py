"""One node incident and its timeline, read by script from the node journal before any model reads
it. Zero tokens, and it asks no node anything.

Inputs, all optional, each a card setting with its default in `definition.json`: `node` (one
machine; every node by default), `at` (an ISO instant: the newest incident at or before it; the
run's clock by default), `lookback_h` (how far back before `at` an incident is looked for) and
`around_min` (the minutes either side of it the timeline holds) and `quote_chars` (how much of a
node's outside text is quoted before an ellipsis).

An incident is a heal of the node's runtime (a `node_lifecycle` `stop` row with `what: runtime`),
a stand-down's start, a kill switch rise above GREEN or a protection alarm. The script finds the
newest, then names what restarted or stopped, when, the node's own why, and when it was back:
the runtime's next `start` row for a heal, the stand-down's `clear` row for a stand-down, each
looked for from the incident up to `at`, however long it took. The
timeline is every lifecycle, stand-down, kill, protection and reconcile row of that machine
inside the window, and the order rows are counted. Durations are whole milliseconds between two
rows' own times.

Text the node took from outside (a cause, an error, a reason) is quoted with the `qmx.marked/1`
mark: the writer reads it as data, never as an instruction, and the grader takes no number from
it. A window with no incident is quiet: the step writes the note itself and no model is asked.
"""

import importlib.util
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

spec = importlib.util.spec_from_file_location("door", Path(__file__).with_name("door.py"))
door = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door)

MARK = "qmx.marked/1"
TEXT = frozenset({"cause", "why", "reason", "message", "detail", "error"})
"""Body fields that may carry text the node took from outside."""
TIMELINE = ("node_lifecycle", "stand_down", "kill_level", "protection", "reconcile")

asked = door.settings(json.load(sys.stdin).get("in"))
home = door.home()
at = door.now()
if asked.get("at"):
    at = datetime.fromisoformat(str(asked["at"]).replace("Z", "+00:00")).astimezone(UTC)
lookback = timedelta(hours=float(asked["lookback_h"]))
around = timedelta(minutes=float(asked["around_min"]))
cap = int(asked["quote_chars"])


def instant(text):
    return datetime.fromisoformat(str(text).replace("Z", "+00:00")).astimezone(UTC)


def facts(body):
    """The body with every outside text marked, so its words are data and its digits no receipt."""
    return {
        name: {"text": quoted(value), "marked": MARK} if name in TEXT else value
        for name, value in body.items()
    }


def quoted(value):
    words = " ".join(str(value).split())
    return words if len(words) <= cap else words[:cap] + "..."


def read(kinds, start, end):
    window = {"start": door.iso(start), "end": door.iso(end)}
    found = []
    for kind in kinds:
        answer = door.journal(home, stream="node", window=window, filters={"kind": kind})
        found += [
            {
                "id": r.get("record_id"),
                "at": r["at"],
                "kind": r["kind"],
                "machine": r.get("machine"),
                "body": r["body"] if isinstance(r["body"], dict) else {},
            }
            for r in answer["rows"]
            if not asked.get("node") or r.get("machine") == asked["node"]
        ]
    return sorted(found, key=lambda r: (r["at"], str(r["id"])))


def incident_of(found):
    body = found["body"]
    match found["kind"]:
        case "node_lifecycle":
            return body.get("event") == "stop" and body.get("what") == "runtime"
        case "stand_down":
            return body.get("event") == "start"
        case "kill_level":
            return body.get("level") not in (None, "GREEN")
        case "protection":
            return True
    return False


def ms_between(first, then):
    return int((instant(then) - instant(first)) / timedelta(milliseconds=1))


try:
    found = read(TIMELINE, at - lookback, at + timedelta(milliseconds=1))
    candidates = [r for r in found if incident_of(r)]
except ValueError as refused:
    print(f"[QMX_FAILURE] {refused}")
    raise SystemExit(0) from None

window = {"start": door.iso(at - lookback), "end": door.iso(at)}
findings = {"looked_from": window["start"], "looked_to": window["end"], "incident": None}
note = None
if not candidates:
    where = f" on {asked['node']}" if asked.get("node") else ""
    note = {
        "title": f"No node incident{where} up to {window['end']}",
        "text": f"The node journal{where} holds no heal, stand-down, kill rise or protection "
        f"alarm between {window['start']} and {window['end']}. Nothing to explain.",
        "receipts": ["read"],
    }
else:
    chosen = candidates[-1]
    started = instant(chosen["at"])
    window = {"start": door.iso(started - around), "end": door.iso(started + around)}
    machine = chosen["machine"]
    timeline = [
        r for r in read(TIMELINE, started - around, started + around) if r["machine"] == machine
    ]
    orders = read(("order",), started - around, started + around)
    body = chosen["body"]
    incident = {"id": chosen["id"], "at": chosen["at"], "node": machine, "kind": chosen["kind"]}
    after = [
        r
        for r in read(("node_lifecycle", "stand_down"), started, at + timedelta(milliseconds=1))
        if r["machine"] == machine and r["at"] > chosen["at"]
    ]
    if chosen["kind"] == "node_lifecycle":
        back = next(
            (
                r
                for r in after
                if r["kind"] == "node_lifecycle"
                and r["body"].get("what") == "runtime"
                and r["body"].get("event") == "start"
            ),
            None,
        )
        incident |= {
            "what": "the node's runtime restarted inside the running node",
            "restart": body.get("restart"),
            "backoff_ms": body.get("backoff_ms"),
            "why": facts(body).get("why"),
            "back_at": None if back is None else back["at"],
            "back_after_ms": None if back is None else ms_between(chosen["at"], back["at"]),
        }
    elif chosen["kind"] == "stand_down":
        cleared = next(
            (
                r
                for r in after
                if r["kind"] == "stand_down"
                and r["body"].get("event") == "clear"
                and r["body"].get("stand_down") == body.get("stand_down")
                and r["body"].get("scope") == body.get("scope")
            ),
            None,
        )
        incident |= {
            "what": f"new entries stopped at {body.get('scope')}: {body.get('stand_down')}",
            "word": body.get("word"),
            "clears": body.get("clears"),
            "why": facts(body).get("cause"),
            "back_at": None if cleared is None else cleared["at"],
            "back_after_ms": None if cleared is None else ms_between(chosen["at"], cleared["at"]),
        }
    elif chosen["kind"] == "kill_level":
        incident |= {
            "what": f"the kill switch rose to {body.get('level')} at {body.get('scope')}",
            "positions_closed": body.get("positions_closed", 0),
        }
    else:
        incident |= {
            "what": f"protection alarm {body.get('alarm')} on {body.get('position')}",
            "market_id": body.get("market_id"),
            "action": body.get("action"),
        }
    counts = {}
    for r in timeline:
        name = f"{r['kind']} {r['body'].get('event', '')}".strip()
        counts[name] = counts.get(name, 0) + 1
    findings |= {
        "incident": incident,
        "timeline": [{**r, "body": facts(r["body"])} for r in timeline],
        "counts": counts,
        "order_rows": len([r for r in orders if r["machine"] == machine]),
        "incidents_in_lookback": len(candidates),
    }

bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
(bodies / "findings.json").write_text(json.dumps(findings, sort_keys=True), encoding="utf-8")
incident = findings["incident"]
print(
    json.dumps(
        {
            "findings": findings,
            "quiet": incident is None,
            "note": note,
            "note_kind": "analysis",
            "about": [] if incident is None else [{"rel": "node", "ref": incident["node"]}],
            "window": window,
            "cards": [],
            "library": [
                {
                    "op": "put_artifact",
                    "type": "node-incident",
                    "body": "library/findings.json",
                    "metadata": findings,
                    "intent_key": f"node-incident|{json.dumps(window, sort_keys=True)}",
                }
            ],
        }
    )
)
