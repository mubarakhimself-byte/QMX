"""The `calendar-open` block's one step: whether a market is open, from its own calendar (WF-02).

Its input is `{"in": {"calendar_ref": ..., "at": ...}}`. `calendar_ref` names a shipped calendar
(`crypto-24x7@1`, `fx-24x5@1`, `cme-equity@1` and the rest); an instrument record's fields carry
it under that name, so a template passes the record it read. `at` is an ISO 8601 time, and the
run's own clock when it is left out. The calendars are the ones the engine's `market_open:<id>`
trigger check reads, so no template holds a market's hours of its own and no forex rule holds
crypto on a Saturday.

Prints `open`, the calendar, its zone, `at` in UTC, `next_open` (null while open, or when the
calendar stays shut past the engine's horizon) and `why` in plain words. A template routes on
`outputs.open.main.open`.
"""

import json
import os
import sys
from datetime import UTC, datetime

from qmx_engine.triggers.preflight import shipped_calendars

FAILURE = "[QMX_FAILURE]"


def fail(why):
    print(f"{FAILURE} {why}")
    raise SystemExit(0)


given = json.load(sys.stdin).get("in")
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
asked = next((r for r in rows if isinstance(r.get("calendar_ref"), str)), None)
if asked is None:
    fail("the calendar-open block needs a calendar_ref, or an instrument record that holds one")
ref = asked["calendar_ref"]
calendar = shipped_calendars().get(ref)
if calendar is None:
    fail(f"no shipped calendar is named {ref!r}")
text = str(asked.get("at") or os.environ.get("QMX_NOW") or datetime.now(UTC).isoformat())
try:
    at = datetime.fromisoformat(text.replace("Z", "+00:00"))
except ValueError:
    fail(f"at {text!r} is not an ISO 8601 time")
if at.tzinfo is None:
    at = at.replace(tzinfo=UTC)
at = at.astimezone(UTC)
local = at.astimezone(calendar.zone).strftime("%A %Y-%m-%d %H:%M")
is_open = calendar.open_at(at)
next_open = None if is_open else calendar.next_open(at)
why = f"{ref} is {'open' if is_open else 'shut'} at {local} in {calendar.zone.key}"
if next_open is not None:
    why += f"; it opens at {next_open.isoformat().replace('+00:00', 'Z')}"
print(
    json.dumps(
        {
            "open": is_open,
            "calendar_ref": ref,
            "zone": calendar.zone.key,
            "at": at.isoformat().replace("+00:00", "Z"),
            "next_open": None
            if next_open is None
            else next_open.isoformat().replace("+00:00", "Z"),
            "why": why,
        }
    )
)
