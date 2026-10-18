"""The "too few trades" card, zero tokens: fewer than 20 new trades since the last review, so no
slice could pass the significance filter."""

import json
import sys

journal = json.load(sys.stdin)["in"]
print(
    json.dumps(
        {
            "trades": journal["new_trades"],
            "summary": "Too few trades for a review: fewer than 20 since the last one.",
            "significant": [],
            "lessons": [],
        }
    )
)
