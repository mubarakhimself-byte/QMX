"""Funnel stage 7, the Library entry, before its check: every inventory row with its capture,
triage buckets and status; each triage reason; every card with a Library id, its audit verdict
and its calibration; a source row per captured item; and the audit's open questions as recorded
assumptions. Rejected cards and skipped items are kept with their reasons. Ids are letters only
(`STRAT-`, `CMP-`, `KB-`, `HINT-`, `SRC-`), so they never read as numbers in the check after this.

An audit verdict given per rule (`card-1:entry`) counts for its card, and one rejected rule rejects
the card. Inputs are told apart by shape; when nothing reached the extractor, only rows arrive."""

import hashlib
import json
import sys

LETTERS = "abcdefghijklmnop"
PREFIX = {"strategy": "STRAT", "component": "CMP", "knowledge": "KB", "hint": "HINT"}


def letters(text):
    return "".join(LETTERS[int(c, 16)] for c in hashlib.sha256(text.encode()).hexdigest()[:8])


def shaped(given, test):
    return next((v for v in given if test(v)), None)


given = json.load(sys.stdin)["in"]
if not isinstance(given, list) or (given and isinstance(given[0], dict) and "capture" in given[0]):
    given = [given]
rows = shaped(given, lambda v: isinstance(v, list) and v and "capture" in v[0]) or []
triaged = shaped(given, lambda v: isinstance(v, list) and v and "buckets" in v[0]) or []
kept = shaped(given, lambda v: isinstance(v, dict) and "cards" in v) or {"cards": [], "gaps": []}
calibrated = shaped(given, lambda v: isinstance(v, dict) and "calibration" in v) or {}
audited = shaped(given, lambda v: isinstance(v, dict) and "verdicts" in v) or {}

verdicts = {v["item_id"]: v for v in triaged}
audit = {}
for found in audited.get("verdicts", []):
    card_id = str(found["card_id"]).partition(":")[0]
    held = audit.get(card_id)
    if held is None or (held["verdict"] == "accepted" and found["verdict"] == "rejected"):
        audit[card_id] = {"verdict": found["verdict"], "reason": found["reason"]}
chips = {}
for chip in calibrated.get("calibration", []):
    card_id, _, field = chip["id"].partition(":")
    chips.setdefault(card_id, {})[field] = chip["confidence"]

cards = []
for card in kept["cards"]:
    verdict = audit.get(card["id"], {"verdict": "not audited", "reason": "the audit gave none"})
    cards.append(
        {
            "library_id": f"{PREFIX[card['kind']]}-{letters(card['item_id'] + card['title'])}",
            "kind": card["kind"],
            "status": card["status"] if verdict["verdict"] == "accepted" else "rejected",
            "title": card["title"],
            "item_id": card["item_id"],
            "summary": card["summary"],
            "entry": card["entry"],
            "exit": card["exit"],
            "parameters": card["parameters"],
            "market": card["market"],
            "timeframe": card["timeframe"],
            "audit": {"verdict": verdict["verdict"], "reason": verdict["reason"]},
            "confidence": chips.get(card["id"], {}),
            "changes": card["changes"],
        }
    )

carded = {c["item_id"] for c in cards}
inventory = []
for row in rows:
    verdict = verdicts.get(row["id"])
    if row["id"] in carded:
        status = "carded"
    elif verdict is not None:
        status = "no_output"
    elif row.get("segments") or row.get("text"):
        status = "skipped by the pre-filter: no trading words"
    else:
        status = row["capture"]
    inventory.append(
        {
            "id": row["id"],
            "kind": row["kind"],
            "locator": row["locator"],
            "provenance": row["provenance"],
            "capture": row["capture"],
            "buckets": verdict["buckets"] if verdict else [],
            "status": status,
        }
    )
sources = [
    {
        "library_id": f"SRC-{letters(row['locator'])}",
        "item_id": row["id"],
        "locator": row["locator"],
        "capture": row["capture"],
    }
    for row in rows
    if row.get("segments") or row.get("text")
]
accepted = sum(c["audit"]["verdict"] == "accepted" for c in cards)
summary = (
    f"{len(rows)} items in, {len(sources)} captured, {len(cards)} cards entered: "
    f"{accepted} accepted by the audit, {len(cards) - accepted} rejected."
)
print(
    json.dumps(
        {
            "summary": summary,
            "inventory": inventory,
            "triage": [
                {"item_id": v["item_id"], "buckets": v["buckets"], "reason": v["reason"]}
                for v in triaged
            ],
            "cards": cards,
            "sources": sources,
            "coverage": kept.get("coverage", {}),
            "gaps": kept.get("gaps", []),
            "assumptions": audited.get("exceptions", []),
        }
    )
)
