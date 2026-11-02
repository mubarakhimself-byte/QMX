"""The `receipts-grader` block's check: every number an agent states is held by a receipt it
cites (AG-12).

Its input holds the agent's note, the first object with a `text` and a `receipts` list, as
`notes_write` takes it. A receipt is the id of a `script` or `app_op` node of a run that called
this block, read up its `parent_run_id` chain: the engine recorded that step's output, and no model
wrote it. Every number in the note's `title` and `text` must be found, as written or rounded to its
own decimal places, in the output of a receipt the note cites. Dates, times, hashes, ids and
version strings are cut from both sides first, and so is any value marked `qmx.marked/1` (the
`marked-sources` block's quoted outside text), so a number a source supplied never counts.

The model's own steps, a `subworkflow`'s output and this block's own run are never receipts. A
script that copies a model's words would make them one, so a template grades the note straight
from the step that wrote it.

Prints the verdict with the `note`, `numbers` (how many were checked), `uncited` (each number no
cited receipt holds) and `unknown_receipts` (each cited id that is no such step).
"""

import json
import os
import re
import sys
from decimal import Decimal
from pathlib import Path

from qmx_engine.ledger.store import Reader
from qmx_engine.workers.zones import home_of

MARK = "qmx.marked/1"
RECEIPT_KINDS = frozenset({"script", "app_op"})
PROSE = ("title", "text")
NUMBER = re.compile(r"(?<![A-Za-z_\d.])\d+(?:[.,]\d+)*")
CUT = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?"
    r"|\b\d{4}-\d{2}-\d{2}\b"
    r"|\b\d{2}:\d{2}(?::\d{2})?\b"
    r"|\b[0-9a-f]{16,}\b"
    r"|\b\d+\.\d+\.\d+\b"
    r"|\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b"
)


def walk(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


def numbers(value):
    if isinstance(value, str):
        return [Decimal(text.replace(",", "")) for text in NUMBER.findall(CUT.sub(" ", value))]
    if isinstance(value, bool) or value is None:
        return []
    if isinstance(value, int | float):
        return [abs(Decimal(str(value)))]
    if isinstance(value, dict):
        if value.get("marked") == MARK:
            return []
        return [n for item in value.values() for n in numbers(item)]
    if isinstance(value, list):
        return [n for item in value for n in numbers(item)]
    return []


def held(number, evidence):
    places = max(-number.as_tuple().exponent, 0)
    return any(round(seen, places) == number for seen in evidence)


def receipts():
    """Each `script` and `app_op` node's outputs in the runs above this one, by node id."""
    found = {}
    with Reader.open(home_of(Path(os.environ["QMX_WORK_SHARED"]))) as reader:
        events = reader.events(os.environ["QMX_RUN_ID"])
        seen = set()
        while events and events[0].kind == "run_created":
            parent = events[0].data.get("parent_run_id")
            if not parent or parent in seen:
                break
            seen.add(parent)
            events = reader.events(str(parent))
            if not events or events[0].kind != "run_created":
                break
            folder = Path(str(events[0].data["folder"]))
            definition = json.loads((folder / "definition.json").read_text("utf-8"))
            kinds = {node["id"]: node["type"] for node in definition["nodes"]}
            for event in events:
                node_id = event.data.get("node_id")
                if event.kind == "node_finished" and kinds.get(node_id) in RECEIPT_KINDS:
                    found.setdefault(node_id, []).append(event.data.get("outputs"))
    return found


given = json.load(sys.stdin)["in"]
note = next(
    (
        v
        for v in walk(given)
        if isinstance(v.get("text"), str) and isinstance(v.get("receipts"), list)
    ),
    None,
)
if note is None:
    print(
        json.dumps(
            {"verdict": "fail", "feedback": {"problems": ["no note with text and receipts"]}}
        )
    )
    raise SystemExit(0)

recorded = receipts()
cited = [str(r) for r in note["receipts"]]
unknown = [r for r in cited if r not in recorded]
evidence = [n for r in cited if r in recorded for n in numbers(recorded[r])]
stated = [n for key in PROSE for n in numbers(note.get(key) or "")]
uncited = list(dict.fromkeys(str(n) for n in stated if not held(n, evidence)))
feedback = {"note": note, "numbers": len(stated), "uncited": uncited, "unknown_receipts": unknown}
print(json.dumps({"verdict": "fail" if uncited or unknown else "pass", "feedback": feedback}))
