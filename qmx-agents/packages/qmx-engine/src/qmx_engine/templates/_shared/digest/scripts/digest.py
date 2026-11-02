"""The `digest` block's one step: one unit's daily digest, made by script before any model reads it
(Part B AD-211).

Its input is `{"in": {"unit": <unit_id>, "day": "YYYY-MM-DD"}}`, the UTC day, or `window`
(`{"start", "end"}`, such as a session read from the `calendar-open` block) in place of `day`.
It reads the unit's journal through `journal_query`'s `digest` view, the one door to journals,
which leaves backfilled rows out and counts them. It lands the digest as one `digest` artifact on
the run's own ref, keyed by the unit and window, and prints it: per market and day the decisions
by outcome and reason, the trades and their R, plus where the data stops when the window runs
past it. A model step after this one explains these numbers and cites this step as its receipt.
"""

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from qmx_tools.journals import journal_query

from qmx_engine.workers.zones import home_of

FAILURE = "[QMX_FAILURE]"


def fail(why):
    print(f"{FAILURE} {why}")
    raise SystemExit(0)


given = json.load(sys.stdin).get("in")
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
asked = next((r for r in rows if isinstance(r.get("unit"), str) and r["unit"]), None)
if asked is None:
    fail("the digest block needs a unit and its day or window")
unit = asked["unit"]
window = asked.get("window")
if window is None:
    try:
        day = date.fromisoformat(str(asked.get("day")))
    except ValueError:
        fail(f"day {asked.get('day')!r} is not YYYY-MM-DD")
    window = {"start": f"{day}T00:00:00Z", "end": f"{day + timedelta(days=1)}T00:00:00Z"}
try:
    answer = journal_query(
        home_of(Path(os.environ["QMX_WORK_SHARED"])),
        stream="unit",
        window=window,
        filters={"unit_id": unit},
        view="digest",
    )
except ValueError as refused:
    fail(str(refused))

digest = {
    "unit": unit,
    "window": answer["window"],
    "rows": answer["rows"],
    "backfilled_left_out": answer["backfilled_left_out"],
    "data_stops_at": answer.get("data_stops_at"),
}
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
(bodies / "digest.json").write_text(json.dumps(digest, sort_keys=True), encoding="utf-8")
write = {
    "op": "put_artifact",
    "type": "digest",
    "body": "library/digest.json",
    "metadata": digest,
    "intent_key": f"digest|{unit}|{answer['window']['start']}|{answer['window']['end']}",
}
print(json.dumps({"digest": digest, "library": [write]}))
