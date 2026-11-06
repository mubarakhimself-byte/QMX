"""The day's data review, counted by script: the price data's gaps, the clock flags and the
cross-source offsets. Zero tokens.

Inputs, all optional: `day` (YYYY-MM-DD, UTC; the day before the run's clock by default).

It reads what this machine's market-data door holds: every price series (journals left out),
each with its dataset card from the door, whose partitions carry their months, frozen marks,
fingerprints and gaps. For the day's journals it reads, through `journal_query`, the market
journal's `offset` rows (one source's price against another's) and every unit, market and node
row stamped `clock_ok = false`, counted per stream and machine. Each series' entry links its card
(`card:<series>`), so the note points at what it counted.
It lands the review as one `data-review` artifact, which alone keeps each series' months, open
months, gaps per month and partition fingerprints. The writer gets their counts, because every
month of every series would cost it a large prompt each morning. A machine with no price series
and no journal rows that day is quiet and asks no model.
"""

import importlib.util
import json
import os
import sys
from collections import Counter
from pathlib import Path

from qmf.core import is_refusal

spec = importlib.util.spec_from_file_location("door", Path(__file__).with_name("door.py"))
door = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door)

FAILURE = "[QMX_FAILURE]"


def unwrapped(found, what):
    if is_refusal(found):
        print(f"{FAILURE} {what} was refused: {found.context}")
        raise SystemExit(0)
    return found.value


asked = door.settings(json.load(sys.stdin).get("in"))
day, window = door.day_window(asked.get("day"))
qmx_home = door.home()
market = door.market_door(qmx_home)
series = []
for info in unwrapped(market.instruments(), "the door's series list"):
    if info.source.startswith("journal-"):
        continue
    card = unwrapped(market.card(info.series), f"the card of {info.series}")
    partitions = card["partitions"]
    series.append(
        {
            "series": info.series,
            "card": f"card:{info.series}",
            "months": [p["month"] for p in partitions],
            "unfrozen": [p["month"] for p in partitions if not p["frozen"]],
            "gaps": {p["month"]: len(p["gaps"]) for p in partitions if p["gaps"]},
            "rows": info.rows,
            "sealed": info.sealed,
            "fingerprints": card["digests"],
        }
    )

try:
    offsets = door.journal(qmx_home, stream="market", window=window, filters={"kind": "offset"})
    flags = Counter()
    for stream in ("unit", "market", "node"):
        found = door.journal(qmx_home, stream=stream, window=window, detailed=True)
        for row in found["rows"]:
            if row["record"].get("clock_ok") is False:
                flags[f"{stream} on {row['record'].get('machine', 'unknown')}"] += 1
except ValueError as refused:
    print(f"{FAILURE} {refused}")
    raise SystemExit(0) from None

offset_rows = Counter(str(row.get("market_id")) for row in offsets["rows"])
findings = {
    "day": day,
    "window": window,
    "series": [
        {
            "series": s["series"],
            "card": s["card"],
            "months": len(s["months"]),
            "unfrozen": len(s["unfrozen"]),
            "gaps": sum(s["gaps"].values()),
            "rows": s["rows"],
            "sealed": s["sealed"],
        }
        for s in series
    ],
    "series_with_gaps": sum(1 for s in series if s["gaps"]),
    "gaps": sum(n for s in series for n in s["gaps"].values()),
    "clock_flags": dict(sorted(flags.items())),
    "clock_flagged_rows": sum(flags.values()),
    "offset_rows": dict(sorted(offset_rows.items())),
}
quiet = not series and not flags and not offset_rows
note = None
if quiet:
    note = {
        "title": f"Data review for {day}: nothing held",
        "text": f"This machine holds no price series, and no journal row on {day} (UTC) is clock "
        "flagged or names an offset. Nothing to review.",
        "receipts": ["read"],
    }
kept = findings | {"series": series}
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
(bodies / "findings.json").write_text(json.dumps(kept, sort_keys=True), encoding="utf-8")
print(
    json.dumps(
        {
            "findings": findings,
            "quiet": quiet,
            "note": note,
            "note_kind": "analysis",
            "about": [{"rel": "dataset", "ref": s["card"]} for s in series],
            "window": window,
            "cards": [],
            "library": [
                {
                    "op": "put_artifact",
                    "type": "data-review",
                    "body": "library/findings.json",
                    "metadata": kept,
                    "intent_key": f"data-review|{day}",
                }
            ],
        }
    )
)
