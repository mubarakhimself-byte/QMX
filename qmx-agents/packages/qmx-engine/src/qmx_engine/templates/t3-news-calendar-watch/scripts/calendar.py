"""The zero-token pre-check: today's economic calendar, normalised to UTC. The monitor that runs
this wakes the rest of the workflow only when the calendar changes.

Live, it reads the free weekly calendar at nfs.faireconomy.media, which gives forecasts and
previous values but no actuals, so a live run lists the day and its blackouts and finds no
surprise. A run started with `{"fixture": "quiet"}` or `{"fixture": "surprise"}` replays the
matching file in `fixtures/` instead; the replay carries the run id so every test run is a change.
"""

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

FEED = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
IMPACT = {"High": "high", "Medium": "medium", "Low": "low"}

inputs = json.load(sys.stdin).get("in") or {}
fixture = inputs.get("fixture") if isinstance(inputs, dict) else None
if fixture in ("quiet", "surprise"):
    found = json.loads(
        (Path(__file__).parents[1] / "fixtures" / f"calendar-{fixture}.json").read_text("utf-8")
    )
    run = os.environ.get("QMX_IDEMPOTENCY_KEY", "").split(":")[0]
    print(json.dumps(found | {"source": "fixture", "run": run}))
else:
    request = Request(FEED, headers={"User-Agent": "QMX calendar watch"})
    with urlopen(request, timeout=60) as reply:  # noqa: S310
        week = json.loads(reply.read())
    today = datetime.now(UTC).date().isoformat()
    events = []
    for row in week:
        when = datetime.fromisoformat(row["date"]).astimezone(UTC)
        if when.date().isoformat() != today:
            continue
        events.append(
            {
                "id": f"{row['country']}-{when:%H%M}-{row['title']}",
                "title": row["title"],
                "currency": row["country"],
                "time_utc": f"{when:%H:%M}",
                "impact": IMPACT.get(row.get("impact"), "low"),
                "forecast": row.get("forecast") or None,
                "previous": row.get("previous") or None,
                "actual": None,
                "typical_surprise": None,
                "source": FEED,
            }
        )
    print(json.dumps({"date": today, "events": events, "source": "faireconomy"}))
