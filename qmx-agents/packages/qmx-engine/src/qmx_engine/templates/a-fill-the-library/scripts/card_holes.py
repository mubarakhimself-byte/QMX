"""Keeps every card's holes, by rule rather than by trust (card R5 step 4, the "no invented exits"
check). A card field may rest only on claims the citation check kept. An entry or exit with no
such claim reads `unresolved`; so does a parameter whose claim is missing or unresolved. A strategy
card whose entry is unresolved or rests only on inferred claims becomes a `hint`, and one with an
unresolved exit stays an `entry_hypothesis`. Each card lists what this step changed.

Its inputs are the citation check's verdict and the extractor's cards, told apart by shape."""

import json
import sys

UNRESOLVED = "unresolved"


def walk(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


given = json.load(sys.stdin)["in"]
graded = next(v for v in given if isinstance(v, dict) and "verdict" in v)
extracted = next(v for v in given if isinstance(v, dict) and "cards" in v)
uncited = {(u["source_id"], u["quote"]) for u in (graded.get("feedback") or {}).get("uncited", [])}
claims = {
    str(c["id"]): c
    for c in walk(graded["input"])
    if {"id", "quote", "source_id", "tag"} <= c.keys()
    and (str(c["source_id"]), str(c["quote"])[:160]) not in uncited
}
sections = [s for s in walk(graded["input"]) if {"id", "locator", "text", "item_id"} <= s.keys()]


def resting(ids):
    return [i for i in ids if i in claims and claims[i]["tag"] != UNRESOLVED]


cards = []
for written in extracted["cards"]:
    card, changes = dict(written), []
    for field in ("entry", "exit"):
        kept = resting(card.get(f"{field}_claims") or [])
        card[f"{field}_claims"] = kept
        if not kept and card.get(field) != UNRESOLVED:
            card[field] = UNRESOLVED
            changes.append(f"{field} rests on no cited claim: unresolved")
    parameters = []
    for parameter in card.get("parameters") or []:
        if parameter["value"] != UNRESOLVED and not resting([parameter["claim_id"]]):
            changes.append(f"parameter {parameter['name']} has no cited claim: unresolved")
            parameters.append(parameter | {"value": UNRESOLVED})
        else:
            parameters.append(parameter)
    card["parameters"] = parameters
    entry_tags = {claims[i]["tag"] for i in card["entry_claims"]}
    if card["kind"] == "strategy" and (card["entry"] == UNRESOLVED or entry_tags == {"inferred"}):
        card["kind"] = "hint"
        changes.append("strategy entry is not source-stated: kept as a hint")
    if card["kind"] == "strategy":
        card["status"] = "entry_hypothesis" if card["exit"] == UNRESOLVED else "complete"
    else:
        card["status"] = card["kind"]
    card["changes"] = changes
    cards.append(card)

used = {c["source_id"] for c in claims.values()}
coverage = {
    "sections": len(sections),
    "with_claims": [s["locator"] for s in sections if s["id"] in used],
    "no_claims": [s["locator"] for s in sections if s["id"] not in used],
}
print(
    json.dumps(
        {
            "cards": cards,
            "claims": list(claims.values()),
            "gaps": extracted.get("gaps", []),
            "coverage": coverage,
        }
    )
)
