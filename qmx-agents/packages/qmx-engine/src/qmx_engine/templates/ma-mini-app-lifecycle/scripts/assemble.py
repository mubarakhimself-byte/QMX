"""The card the run ends with: an install card with its check report and the review, or a
deprecate or archive card with its blast radius. A refused scaffold ends with its problems. Its
inputs are told apart by shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
given = given if isinstance(given, list) else [given]
install = next((v for v in given if "blocked_by" in v), None)
review = next((v for v in given if "matches_interview" in v), None)
retire = next((v for v in given if "blast_radius" in v), None)
if retire is not None:
    print(json.dumps({"path": retire["kind"], "card": retire, "review": "", "extras": []}))
else:
    card = dict(install)
    if review is not None and not review["matches_interview"]:
        card["card"] = None
        card["blocked_by"] = [*card["blocked_by"], "the app does not do what the interview says"]
    print(
        json.dumps(
            {
                "path": "install",
                "card": card,
                "review": review["notes"] if review else "",
                "extras": review["extras"] if review else [],
            }
        )
    )
