"""Each unit's day from its journal, counted by script before any model reads it. Zero tokens.

Inputs, all optional: `day` (YYYY-MM-DD, UTC; the day before the run's clock by default), `units`
(unit ids; every unit with rows that day by default) and `world` (`paper`, `demo`, `live` or
`backtest`; every world by default).

It reads the unit journal through `journal_query`'s `digest` view, which counts each unit's
decisions by outcome and reason, and its trades and their R, per market. Each decision falls in
one bucket: `taken` is traded; `skipped`, `no_signal` and `suppressed_warming` are skipped; every
other outcome (`blocked`, `suppressed`, `suppressed_limit`, `refused_by_door`, `dropped_opposite`)
is missed, because the unit wanted to act and something stopped it. The reasons say why.

It lands the counts as one `unit-review` artifact, the evidence a later card rests on, and prints
them under `findings`. A day with no rows is quiet: the step writes the note itself and no model
is asked. Otherwise the writer explains these numbers and cites this step, `read`, as its receipt.
"""

import importlib.util
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

spec = importlib.util.spec_from_file_location("door", Path(__file__).with_name("door.py"))
door = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door)

TRADED = frozenset({"taken"})
SKIPPED = frozenset({"skipped", "no_signal", "suppressed_warming"})

asked = door.settings(json.load(sys.stdin).get("in"))
day, window = door.day_window(asked.get("day"))
filters = {"world": asked["world"]} if asked.get("world") else {}
try:
    answer = door.journal(door.home(), stream="unit", window=window, filters=filters, view="digest")
except ValueError as refused:
    print(f"[QMX_FAILURE] {refused}")
    raise SystemExit(0) from None

wanted = set(asked.get("units") or [])
units = {}
for row in answer["rows"]:
    if wanted and row["unit_id"] not in wanted:
        continue
    outcomes = row["outcomes"]
    traded = sum(n for o, n in outcomes.items() if o in TRADED)
    skipped = sum(n for o, n in outcomes.items() if o in SKIPPED)
    market = {
        "market": row["market_id"],
        "decisions": row["decisions"],
        "traded": traded,
        "skipped": skipped,
        "missed": row["decisions"] - traded - skipped,
        "outcomes": outcomes,
        "reasons": row["reasons"],
        "trades": row["trades"],
        "r": row["r"],
    }
    units.setdefault(row["unit_id"], []).append(market)

reviewed = []
for unit, markets in sorted(units.items()):
    total = {k: sum(m[k] for m in markets) for k in ("decisions", "traded", "skipped", "missed")}
    total["trades"] = sum(m["trades"] for m in markets)
    total["r"] = str(sum((Decimal(m["r"]) for m in markets), Decimal(0)))
    reviewed.append({"unit": unit, **total, "markets": markets})

findings = {
    "day": day,
    "window": answer["window"],
    "world": asked.get("world") or "every world",
    "units": reviewed,
    "backfilled_left_out": answer["backfilled_left_out"],
    "data_stops_at": answer.get("data_stops_at"),
}
note = None
if not reviewed:
    stops = answer.get("note") or "nothing is recorded yet"
    note = {
        "title": f"No unit journal rows on {day}",
        "text": f"The unit journal holds no decisions or trades on {day} (UTC): {stops}. "
        "Nothing to review.",
        "receipts": ["read"],
    }
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
(bodies / "findings.json").write_text(json.dumps(findings, sort_keys=True), encoding="utf-8")
print(
    json.dumps(
        {
            "findings": findings,
            "quiet": not reviewed,
            "note": note,
            "note_kind": "analysis",
            "about": [{"rel": "unit", "ref": u["unit"]} for u in reviewed],
            "window": answer["window"],
            "cards": [],
            "library": [
                {
                    "op": "put_artifact",
                    "type": "unit-review",
                    "body": "library/findings.json",
                    "metadata": findings,
                    "intent_key": f"unit-review|{day}|{findings['world']}",
                }
            ],
        }
    )
)
