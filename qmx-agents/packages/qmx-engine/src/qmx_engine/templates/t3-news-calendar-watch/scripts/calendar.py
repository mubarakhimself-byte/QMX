"""The zero-token pre-check: today's economic calendar, normalised to UTC. The monitor that runs
this wakes the rest of the workflow only when the calendar changes.

Live, it reads the free weekly calendar at nfs.faireconomy.media and parses it with the one
calendar parser QMX has, `qmf.data.calendar_feed.decode_calendar_snapshot`: a provider date with
no zone is refused there rather than guessed, the impact label is kept as the provider wrote it,
and the event's id is the provider's own id (or a stable one built from its fields). The
provider's snapshot gives forecast and previous values but no actuals, so a live run lists the
day and its blackouts and finds no surprise.

A run started with `{"fixture": "quiet"}` or `{"fixture": "surprise"}` replays the matching file
in `fixtures/` instead; the replay carries the run id so every test run is a change.
"""

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

from qmf.core import is_refusal
from qmf.data.calendar_feed import decode_calendar_snapshot

FEED = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
IMPACT = {"High": "high", "Medium": "medium", "Low": "low"}
FAILURE = "[QMX_FAILURE]"

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
        body = reply.read()
    raw = json.loads(body)
    known_at_ns = int(datetime.now(UTC).timestamp() * 1_000_000_000)
    decoded = decode_calendar_snapshot(body, known_at_ns=known_at_ns)
    if is_refusal(decoded):
        print(f"{FAILURE} the calendar snapshot was refused: {decoded.context}")
        raise SystemExit(1)
    today = datetime.now(UTC).date().isoformat()
    events = []
    for row, event in zip(raw, decoded.value, strict=True):
        when = datetime.fromtimestamp(event.event_time_ns / 1_000_000_000, tz=UTC)
        if when.date().isoformat() != today:
            continue
        events.append(
            {
                "id": event.source_native_id,
                "title": event.title,
                "currency": event.currency,
                "time_utc": f"{when:%H:%M}",
                "impact": IMPACT.get(event.impact_label, event.impact_label.lower() or "low"),
                "forecast": row.get("forecast") or None,
                "previous": row.get("previous") or None,
                "actual": None,
                "typical_surprise": None,
                "source": FEED,
            }
        )
    print(json.dumps({"date": today, "events": events, "source": "faireconomy"}))
