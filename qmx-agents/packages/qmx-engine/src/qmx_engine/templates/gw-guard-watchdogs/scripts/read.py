"""Each trading node's health, read by script from what This PC holds. Zero tokens, and it asks
no node anything.

Inputs, all optional, each a card setting with its default in `definition.json`: `nodes` (machine
names; every node seen by default), `here` (this machine's place name, `pc` on This PC),
`lookback_h` (how far back kill rises, protection alarms and heals count), `stand_down_days` (how
far back a stand-down still held is found), `heartbeat_stale_after_s` and `quote_chars` (how much
of a node's outside text is quoted before an ellipsis).

The machines watched are every node in `nodes`, every server node whose tail file This PC keeps,
every node with a row in the windows, and this machine when the trading node app beats here, so a
quiet node that goes silent is still heard missing.

It reads three things, each a read:

- the node journal through `journal_query`: `stand_down` start and clear rows, and `kill_level`,
  `protection` and `node_lifecycle` rows;
- each server node's newest rows in This PC's tail file (`records/tail/<node>.json`), which the
  records job keeps from the node's own `journal_tail`, so they count before the month comes home;
- the heartbeat log's newest row per subject: the trading node app's row for a node on this
  machine, and the Hub's row of the server's host for a node elsewhere.

A node reads Alarm while a stand-down that waits for his resume is held, when the kill switch rose
or the venue did not hold a stop inside the lookback, and when its heartbeat is late. It reads
Watch while a stand-down that clears itself is held (a stale feed, the clock band, the disk guard,
a venue not ready) and when its runtime healed inside the lookback. Otherwise it reads Well.

Every time printed is a row's own, never an age from the run's clock, so the output stays the same
while a node's health does, and the monitor this script feeds lands a note only when it changes.
Text the node took from outside (a stand-down's cause, a heal's error) is quoted as data with the
`qmx.marked/1` mark, never followed.
"""

import importlib.util
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from qmx_engine.heartbeat import latest

spec = importlib.util.spec_from_file_location("door", Path(__file__).with_name("door.py"))
door = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door)

MARK = "qmx.marked/1"
NODE_APP = "trading-node"
WORDS = ("well", "watch", "alarm")
CLEARS = {
    "itself": "clears itself",
    "his_resume": "waits for your resume",
    "his_click": "waits for your click",
}
LOOKBACK_KINDS = ("kill_level", "protection", "node_lifecycle")

asked = door.settings(json.load(sys.stdin).get("in"))
home, now, here = door.home(), door.now(), str(asked["here"])
lookback = timedelta(hours=float(asked["lookback_h"]))
held_back = timedelta(days=float(asked["stand_down_days"]))


def stamp(ms):
    moment = datetime.fromtimestamp(ms / 1_000, tz=UTC)
    return moment.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def instant(text):
    return datetime.fromisoformat(str(text).replace("Z", "+00:00")).astimezone(UTC)


def row(at, record):
    return {
        "at": at,
        "kind": record.get("kind"),
        "record_id": record.get("record_id"),
        "machine": record.get("machine"),
        "body": record.get("body") if isinstance(record.get("body"), dict) else {},
    }


def journalled(kind, since):
    window = {"start": door.iso(now - since), "end": door.iso(now + timedelta(milliseconds=1))}
    answer = door.journal(home, stream="node", window=window, filters={"kind": kind})
    return [row(r["at"], r) for r in answer["rows"]]


def tailed():
    """The node rows each tail file holds, timed by the writer's own `ts_write`, and the nodes the
    tail files are kept for."""
    found, kept_for = [], set()
    folder = home / "records" / "tail"
    for path in sorted(folder.glob("*.json")) if folder.is_dir() else []:
        try:
            kept = json.loads(path.read_text("utf-8"))
        except OSError, ValueError:
            continue
        if isinstance(kept, dict) and isinstance(kept.get("node"), str):
            kept_for.add(kept["node"])
        for record in kept.get("rows", []) if isinstance(kept, dict) else []:
            if not isinstance(record, dict) or record.get("stream") != "node":
                continue
            written = record.get("ts_write")
            if isinstance(written, int) and not isinstance(written, bool):
                found.append(row(stamp(written // 1_000_000), record))
    return found, kept_for


def marked(text):
    words = " ".join(str(text or "").split())
    cap = int(asked["quote_chars"])
    return {"text": words if len(words) <= cap else words[:cap] + "...", "marked": MARK}


def said(text):
    return json.dumps(text)


try:
    rows = journalled("stand_down", held_back)
    for kind in LOOKBACK_KINDS:
        rows += journalled(kind, lookback)
except ValueError as refused:
    print(f"[QMX_FAILURE] {refused}")
    raise SystemExit(0) from None
seen = {r["record_id"] for r in rows if r["record_id"]}
tail_rows, tail_nodes = tailed()
for found in tail_rows:
    reach = held_back if found["kind"] == "stand_down" else lookback
    fresh = found["record_id"] not in seen and instant(found["at"]) >= now - reach
    if fresh and found["kind"] in ("stand_down", *LOOKBACK_KINDS):
        rows.append(found)
        seen.add(found["record_id"])
rows.sort(key=lambda r: (r["at"], str(r["record_id"])))
beats = latest(home)

wanted = set(asked.get("nodes") or [])
machines = {r["machine"] for r in rows if isinstance(r["machine"], str)} | tail_nodes | wanted
if f"app:{NODE_APP}" in beats:
    machines.add(here)
machines = sorted(m for m in machines if not wanted or m in wanted)


def stand_downs(machine):
    held = {}
    for found in rows:
        body = found["body"]
        if found["machine"] != machine or found["kind"] != "stand_down":
            continue
        key = (body.get("stand_down"), body.get("scope"))
        if body.get("event") == "start":
            held[key] = found
        elif body.get("event") == "clear":
            held.pop(key, None)
    causes = []
    for found in held.values():
        body = found["body"]
        since = body.get("since_ns")
        clears = str(body.get("clears") or "his_resume")
        causes.append(
            {
                "word": "watch" if clears == "itself" else "alarm",
                "what": "stand_down",
                "stand_down": body.get("stand_down"),
                "scope": body.get("scope"),
                "since": stamp(since // 1_000_000) if isinstance(since, int) else found["at"],
                "clears": clears,
                "headline": body.get("word") or "Stopped",
                "cause": marked(body.get("cause")),
            }
        )
    return causes


def events(machine):
    causes = []
    runtime = [
        r
        for r in rows
        if r["machine"] == machine
        and r["kind"] == "node_lifecycle"
        and r["body"].get("what") == "runtime"
    ]
    healing = bool(runtime) and runtime[-1]["body"].get("event") == "stop"
    for found in rows:
        body = found["body"]
        if found["machine"] != machine or instant(found["at"]) < now - lookback:
            continue
        if found["kind"] == "kill_level" and body.get("level") not in (None, "GREEN"):
            causes.append(
                {
                    "word": "alarm",
                    "what": "kill_level",
                    "level": body.get("level"),
                    "scope": body.get("scope"),
                    "at": found["at"],
                    "positions_closed": body.get("positions_closed", 0),
                }
            )
        elif found["kind"] == "protection":
            causes.append(
                {
                    "word": "alarm",
                    "what": "protection",
                    "alarm": body.get("alarm"),
                    "position": body.get("position"),
                    "market_id": body.get("market_id"),
                    "action": body.get("action"),
                    "at": found["at"],
                }
            )
        elif found in runtime and body.get("event") == "stop":
            causes.append(
                {
                    "word": "watch",
                    "what": "heal",
                    "at": found["at"],
                    "restart": body.get("restart"),
                    "backoff_ms": body.get("backoff_ms"),
                    "healing": healing and found is runtime[-1],
                    "why": marked(body.get("why")),
                }
            )
    return causes


def heartbeat(machine):
    subject = f"app:{NODE_APP}" if machine == here else f"host:{machine}"
    beat = beats.get(subject)
    if beat is None:
        cause = None
        if machine == here:
            cause = {"word": "alarm", "what": "heartbeat", "subject": subject, "last_at": None}
        return {"subject": subject, "read_here": False}, cause
    late = (now - instant(beat.at)).total_seconds() > float(asked["heartbeat_stale_after_s"])
    if not late:
        return {"subject": subject, "read_here": True, "late": False}, None
    cause = {"word": "alarm", "what": "heartbeat", "subject": subject, "last_at": beat.at}
    return {"subject": subject, "read_here": True, "late": True, "last_at": beat.at}, cause


def line(cause):
    match cause["what"]:
        case "stand_down":
            return (
                f"{cause['headline']} at {cause['scope']} since {cause['since']}: "
                f"{cause['stand_down']}, which {CLEARS.get(cause['clears'], cause['clears'])}. "
                f"The node said {said(cause['cause']['text'])}."
            )
        case "kill_level":
            return (
                f"The kill switch rose to {cause['level']} at {cause['scope']} at {cause['at']} "
                f"and closed {cause['positions_closed']} positions."
            )
        case "protection":
            return (
                f"Protection alarm {cause['alarm']} at {cause['at']} on position "
                f"{cause['position']} ({cause['market_id']}): {cause['action']}."
            )
        case "heal":
            state = "is healing now" if cause["healing"] else "healed"
            wait = "no back-off"
            if cause["backoff_ms"] is not None:
                wait = f"back-off {cause['backoff_ms']} ms"
            return (
                f"The runtime failed at {cause['at']} and {state} (restart {cause['restart']}, "
                f"{wait}). It said {said(cause['why']['text'])}."
            )
        case _:
            if cause["last_at"] is None:
                return f"No heartbeat from {cause['subject']} has been read on this machine."
            return f"No heartbeat from {cause['subject']} since {cause['last_at']}."


nodes = []
for machine in machines:
    beat, late = heartbeat(machine)
    causes = stand_downs(machine) + events(machine) + ([late] if late else [])
    word = max((c["word"] for c in causes), key=WORDS.index, default="well")
    nodes.append({"node": machine, "word": word, "heartbeat": beat, "causes": causes})

paragraphs = []
for node in nodes:
    lines = [line(c) for c in node["causes"]]
    subject = node["heartbeat"]["subject"]
    if not node["heartbeat"]["read_here"] and node["node"] != here:
        lines.append(f"No heartbeat of {subject} is read on this machine.")
    paragraphs.append(" ".join([f"{node['node']} reads {node['word'].title()}.", *lines]))
if not nodes:
    title = "No trading node to watch"
    paragraphs = ["No trading node has written to this machine, and none beats here."]
else:
    worst = max((n["word"] for n in nodes), key=WORDS.index)
    title = f"Trading nodes: {', '.join(f'{n["node"]} {n["word"]}' for n in nodes)}"
    if worst != "well":
        paragraphs.append("Nothing was pressed: the watcher reads and tells, and only you act.")

findings = {
    "here": here,
    "lookback_h": asked["lookback_h"],
    "stand_down_days": asked["stand_down_days"],
    "heartbeat_stale_after_s": asked["heartbeat_stale_after_s"],
    "nodes": nodes,
}
print(
    json.dumps(
        {
            "findings": findings,
            "note": {"title": title, "text": "\n\n".join(paragraphs), "receipts": ["watch"]},
            "note_kind": "analysis",
            "about": [{"rel": "node", "ref": n["node"]} for n in nodes],
            "cards": [],
        },
        sort_keys=True,
    )
)
