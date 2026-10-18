"""Keeps the component card's holes, by rule rather than by trust (card R2 step 2: every parameter
has a value or `unresolved`, nothing invented). A field, parameter or failure case may rest only
on a claim the citation check kept and the reader did not tag unresolved; anything else reads
`unresolved` (a failure case is dropped). Hands on the card, its holes, what this step changed, and
the cited claims and sections as evidence for the steps after it.

Its inputs are the citation check's verdict and the extractor's card, told apart by shape."""

import json
import sys

UNRESOLVED = "unresolved"
STATED = ("formula", "data_frequency", "warm_up", "claimed_effect")


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
card = dict(next(v for v in given if isinstance(v, dict) and "piece" in v and "formula" in v))
uncited = {(u["source_id"], u["quote"]) for u in (graded.get("feedback") or {}).get("uncited", [])}
claims = {
    str(c["id"]): c
    for c in walk(graded["input"])
    if {"id", "quote", "source_id", "tag"} <= c.keys()
    and (str(c["source_id"]), str(c["quote"])[:160]) not in uncited
}
sections = [s for s in walk(graded["input"]) if {"id", "locator", "text", "item_id"} <= s.keys()]


def rests(claim_id):
    return claim_id in claims and claims[claim_id]["tag"] != UNRESOLVED


holes, changes = [], []
for field in STATED:
    stated = dict(card[field])
    if stated["value"] != UNRESOLVED and not rests(stated["claim_id"]):
        stated = {"value": UNRESOLVED, "claim_id": ""}
        changes.append(f"{field} rests on no cited claim: unresolved")
    if stated["value"] == UNRESOLVED:
        holes.append(field)
    card[field] = stated
parameters = []
for written in card["parameters"]:
    parameter = dict(written)
    if parameter["value"] != UNRESOLVED and not rests(parameter["claim_id"]):
        parameter |= {"value": UNRESOLVED, "claim_id": ""}
        changes.append(f"parameter {parameter['name']} rests on no cited claim: unresolved")
    if parameter["value"] == UNRESOLVED:
        holes.append(f"parameter {parameter['name']}")
    parameters.append(parameter)
card["parameters"] = parameters
kept = [case for case in card["failure_cases"] if rests(case["claim_id"])]
if len(kept) < len(card["failure_cases"]):
    changes.append(f"{len(card['failure_cases']) - len(kept)} uncited failure cases dropped")
card["failure_cases"] = kept
print(
    json.dumps(
        {
            "card": card,
            "holes": holes,
            "changes": changes,
            "claims": list(claims.values()),
            "sections": sections,
        }
    )
)
