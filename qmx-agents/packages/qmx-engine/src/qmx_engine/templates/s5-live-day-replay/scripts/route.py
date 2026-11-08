"""The live day QMB replays, read from the unit journal. Zero tokens.

Inputs: `unit` (the unit id its journal rows carry), `pin` (the Library object id of the version
that traded, which QMB compiles), `day` (YYYY-MM-DD, UTC; the day before the run's clock by
default), optionally `window` (the bars QMB replays; from `warm_up_days` before the day to its
end by default) and `fixture` (test runs only).

It reads the unit's `live` `signal` rows for the day through `journal_query`, as the node wrote
them and the records job brought them home, and prints the `replay_check` ask: the pin, the
window, the day and the live rows. A day with no live rows is quiet: the note says so and QMB is
not asked.
"""

import importlib.util
import json
import sys
from datetime import date, timedelta
from pathlib import Path

spec = importlib.util.spec_from_file_location("door", Path(__file__).with_name("door.py"))
door = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door)

asked = door.settings(json.load(sys.stdin).get("in"))
day, window = door.day_window(asked.get("day"))
unit = asked["unit"]
try:
    answer = door.journal(
        door.home(),
        stream="unit",
        window=window,
        filters={"unit_id": unit, "world": "live", "kind": "signal"},
    )
except ValueError as refused:
    print(f"[QMX_FAILURE] {refused}")
    raise SystemExit(0) from None

live = [row["body"] for row in answer["rows"]]
warm = date.fromisoformat(day) - timedelta(days=int(asked["warm_up_days"]))
bars = asked.get("window") or {"start": warm.isoformat(), "end": window["end"][:10]}
note = None
if not live:
    note = {
        "title": f"No live day to replay for {unit} on {day}",
        "text": f"The unit journal holds no live decisions for {unit} on {day} (UTC). "
        "QMB was not asked.",
        "receipts": ["route"],
    }
print(
    json.dumps(
        {
            "unit": unit,
            "day": day,
            "live_rows": len(live),
            "warn_below": asked["warn_below"],
            "quiet": not live,
            "note": note,
            "note_kind": "analysis",
            "about": [{"rel": "unit", "ref": unit}],
            "window": window,
            "cards": [],
            "recorded": asked.get("fixture"),
            "replay_check": {"unit": asked["pin"], "window": bars, "day": day, "live": live},
        }
    )
)
