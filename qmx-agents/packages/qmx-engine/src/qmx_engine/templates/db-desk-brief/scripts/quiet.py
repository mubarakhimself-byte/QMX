"""The quiet-day card, rendered by script with zero tokens (card T1's pre-check): no release above
low impact, nothing from the desk or research, no alert and no decision."""

import json
import sys

day = json.load(sys.stdin)["in"]
print(
    json.dumps(
        {
            "date": day["date"],
            "edition": day["edition"],
            "headline": "Quiet day: nothing new for the watchlist",
            "summary": "No release above low impact, no desk or research item, no alert and no "
            "decision waiting. The account picture reads could not check: trading node.",
            "node_facts": day["node_facts"],
            "tiles": {"events": [], "alerts": [], "desk": [], "research": []},
            "decisions": [],
            "watch_today": [],
            "could_not_check": day["could_not_check"],
            "quiet": True,
        }
    )
)
