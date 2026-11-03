"""Lands what a slow-lane run wrote, as proposals only (Level 0 AD-31, Part B AD-213).

Its inputs are the read step's output and, when a model wrote the note, the `receipts-grader`
child's output, nested as `outputs.deliver.main.note`. The read step's output carries `note` (the
script's own note when nothing needed a model), `note_kind`, `about`, `window`, `cards`, the
receipts of the findings it landed, and optionally `examples`, which the note carries.

It lands one `note` artifact and one `proposal-card` artifact per card, on the run's own ref and
as the run, each marked `proposal: true`. A note a model wrote lands only after the grader passed
it, so every number in it is held by a receipt. A card rests on the read step's landed findings,
asks only `tighten`, `admit_market`, `drop_market` or `bench` and never `paper` or `live`, names
what it is about in `placeholders` (such as the market to drop), and waits for his click.
Nothing here moves a unit, a ref on `main`, a lifecycle row or an order.
"""

import json
import os
import sys
from pathlib import Path

FAILURE = "[QMX_FAILURE]"
ASKS = ("tighten", "admit_market", "drop_market", "bench")


def fail(why):
    print(f"{FAILURE} {why}")
    raise SystemExit(0)


given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
read = next((r for r in rows if "note_kind" in r), None)
if read is None:
    fail("the land step needs the read step's findings")
graded = next(
    (
        r["outputs"]["deliver"]["main"]["note"]
        for r in rows
        if isinstance(r.get("outputs"), dict) and "deliver" in r["outputs"]
    ),
    None,
)
note = graded or read.get("note")
if not isinstance(note, dict) or not note.get("text"):
    fail("no note to land: no graded note and no note of the read step's own")
findings = [w["object_id"] for w in read.get("library_written", []) if w.get("object_id")]
code = Path(os.environ["QMX_CODE"])
template = json.loads((code / "definition.json").read_text("utf-8"))["id"]
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
landed = {
    "title": str(note.get("title") or ""),
    "text": str(note["text"]),
    "note_kind": read["note_kind"],
    "receipts": [str(r) for r in note.get("receipts", [])],
    "about": read.get("about", []),
    "window": read.get("window"),
    "findings": findings,
    "author": f"agent:{template}" if graded else f"script:{template}",
    "proposal": True,
}
if isinstance(read.get("examples"), list):
    landed["examples"] = read["examples"]
(bodies / "note.md").write_text(landed["text"], encoding="utf-8")
writes = [
    {
        "op": "put_artifact",
        "type": "note",
        "body": "library/note.md",
        "metadata": landed,
        "intent_key": f"note|{template}|{json.dumps(landed['window'], sort_keys=True)}",
    }
]
cards = []
for place, proposal in enumerate(read.get("cards", []), start=1):
    subject, ask = proposal.get("subject"), proposal.get("ask")
    if not isinstance(subject, str) or not subject or ask not in ASKS:
        fail(f"card {place} names no subject or asks {ask!r}, not one of {', '.join(ASKS)}")
    if not findings:
        fail(f"card {place} has no landed findings to rest on")
    card = {
        "subject": subject,
        "ask": ask,
        "evidence": [*findings, *proposal.get("evidence", [])],
        "why": str(proposal.get("why") or ""),
        "made_by": f"run:{os.environ['QMX_RUN_ID']}",
        "proposal": True,
    }
    if isinstance(proposal.get("placeholders"), list):
        card["placeholders"] = [str(p) for p in proposal["placeholders"]]
    (bodies / f"card-{place}.json").write_text(json.dumps(card, sort_keys=True), "utf-8")
    writes.append(
        {
            "op": "put_artifact",
            "type": "proposal-card",
            "body": f"library/card-{place}.json",
            "metadata": card,
            "intent_key": f"proposal|{subject}|{ask}|{'|'.join(card['evidence'])}",
        }
    )
    cards.append(card)
print(json.dumps({"note": landed, "cards": cards, "library": writes}))
