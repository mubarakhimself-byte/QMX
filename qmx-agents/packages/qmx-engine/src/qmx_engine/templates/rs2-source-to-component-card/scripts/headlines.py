"""The items to calibrate (card R2 step 6): the claimed effect and the formula, each with the
quote and section of the claim it rests on, and the sections as sources."""

import json
import sys

kept = json.load(sys.stdin)["in"]
card = kept["card"]
claims = {c["id"]: c for c in kept["claims"]}
items = []
for field in ("claimed_effect", "formula"):
    claim = claims.get(card[field]["claim_id"], {})
    items.append(
        {
            "id": field,
            "text": card[field]["value"],
            "quote": claim.get("quote", ""),
            "source_id": claim.get("source_id", ""),
        }
    )
print(json.dumps({"items": items, "sources": kept["sections"]}))
