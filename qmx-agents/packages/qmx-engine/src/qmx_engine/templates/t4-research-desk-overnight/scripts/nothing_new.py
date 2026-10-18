"""The quiet night: no news item touched the watchlist, so no analyst ran. The brief says so, and
the morning brief reads "desk: nothing new"."""

import json
from datetime import UTC, datetime

print(
    json.dumps(
        {
            "date": datetime.now(UTC).date().isoformat(),
            "instruments": [],
            "summary": "desk: nothing new",
            "sections": {
                s: [] for s in ("HIGH", "MEDIUM", "CALENDAR", "POSITIONING", "CROSS-ASSET")
            },
            "cut": [],
            "hint_cards": [],
            "could_not_check": [],
        }
    )
)
