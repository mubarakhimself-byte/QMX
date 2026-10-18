"""The proposal pack: one decision card per proposed decision, at most three, each with its evidence
strip, checklist, the validator's findings (a contested critical finding shown in red), the
pre-mortem, and the writer's recommendation, default, consequence of silence, door type and blast
radius. A card can recommend yes only when its checklist is all green and no critical finding
stands; otherwise its recommendation reads "not yet" with the reason. Every card is a proposal: he
signs or refuses it, and the upload to a live node stays his own click in the node UI. Its inputs
are told apart by shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
checked = next(v for v in given if "held_back" in v)
findings = next(v["findings"] for v in given if "findings" in v)
premortem = {p["unit"]: p for p in next(v["premortems"] for v in given if "premortems" in v)}
written = {c["unit"]: c for c in next(v["cards"] for v in given if "cards" in v)}
cards = []
for decision in checked["decisions"]:
    unit = decision["unit"]
    mine = [f for f in findings if f["unit"] == unit]
    critical = [f for f in mine if f["severity"] == "critical"]
    card = written.get(unit, {})
    recommendation = card.get("recommendation", "not yet")
    if recommendation == "yes" and (not decision["all_green"] or critical):
        why = (
            "the checklist is not all green"
            if not decision["all_green"]
            else "a critical finding stands"
        )
        recommendation = f"not yet: {why}"
    cards.append(
        {
            "unit": unit,
            "decision": decision["decision"],
            "checklist": decision["checklist"],
            "findings": [
                f | {"flag": "red" if f["severity"] == "critical" else None} for f in mine
            ],
            "premortem": premortem.get(unit, {}).get("story", ""),
            "recommendation": recommendation,
            "default": card.get("default", "extend demo 1 week"),
            "if_silent": card.get("if_silent", ""),
            "door": card.get("door", "two-way"),
            "blast_radius": card.get("blast_radius", ""),
            "evidence": decision["evidence"],
        }
    )
print(json.dumps({"cards": cards, "held_back": checked["held_back"]}))
