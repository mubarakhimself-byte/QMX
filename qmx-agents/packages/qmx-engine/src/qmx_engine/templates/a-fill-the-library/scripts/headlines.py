"""The items to calibrate (card R5 step 5): each card's entry and exit rules, at most five, each
with the quote and section of the first claim it rests on, and the sections as sources. Its inputs,
the cards with their holes kept and the sections, are told apart by shape."""

import json
import sys

MOST = 5

given = json.load(sys.stdin)["in"]
kept = next(v for v in given if isinstance(v, dict) and "cards" in v)
sections = next(v for v in given if isinstance(v, list))
claims = {c["id"]: c for c in kept["claims"]}
items = []
for card in kept["cards"]:
    for field in ("entry", "exit"):
        if card[field] == "unresolved" or len(items) == MOST:
            continue
        claim = claims.get(next(iter(card[f"{field}_claims"]), ""), {})
        items.append(
            {
                "id": f"{card['id']}:{field}",
                "text": card[field],
                "quote": claim.get("quote", ""),
                "source_id": claim.get("source_id", ""),
            }
        )
print(json.dumps({"items": items, "sources": sections}))
