"""Each unit's record on each market it trades, and the reading states it earned in. Zero tokens.

Inputs are the card's settings, each left out taking its `default` in `definition.json`: `day`
(the record ends with this UTC day, the day before the run by default), `lookback_days`,
`min_trades`, `drop_at_r`, `readings` (the reading ids read beside the trades), and optionally
`units`.

It reads every closed trade in R over the lookback through `journal_query`, and for each market
traded the MIS's reading history of each reading through `readings_query`, whose holdout refuses a
held-out window by name. Each trade is set beside the word every reading said last at or before it
opened (`opened_at` when the trade row carries it, its close otherwise). Per unit and market it
prints the trades, their expectancy and total in R, and the trades and R earned under each word.

A unit and market with at least `min_trades` trades whose expectancy is at or below `drop_at_r`
gets one `drop_market` card for his click. Admitting a new market rests on a backtest, which the
`u1-run-on-every-market` template runs. A week with no card is quiet and asks no model.
"""

import importlib.util
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

spec = importlib.util.spec_from_file_location("door", Path(__file__).with_name("door.py"))
door = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door)

CENT = Decimal("0.01")
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def ns_of(text):
    moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return (moment - EPOCH) // timedelta(microseconds=1) * 1_000


asked = door.settings(json.load(sys.stdin).get("in"))
day, last_day = door.day_window(asked.get("day"))
end = datetime.fromisoformat(last_day["end"].replace("Z", "+00:00"))
window = {
    "start": door.iso(end - timedelta(days=int(asked["lookback_days"]))),
    "end": door.iso(end),
}
qmx_home = door.home()
try:
    answer = door.journal(qmx_home, stream="unit", window=window, filters={"kind": "trade"})
except ValueError as refused:
    print(f"[QMX_FAILURE] {refused}")
    raise SystemExit(0) from None

wanted = set(asked.get("units") or [])
trades = [row for row in answer["rows"] if not wanted or row["unit_id"] in wanted]
markets = sorted({row["market_id"] for row in trades})
history, refused = {}, {}
for reading in asked["readings"] if markets else []:
    found = door.readings(qmx_home, reading, window, markets=markets, source="mis")
    if "refused" in found:
        refused[reading] = found["refused"]
        continue
    for row in found["rows"]:
        history.setdefault((reading, row.get("market_id")), []).append(
            (ns_of(row["at"]), str(row.get("word") or row.get("value")))
        )

cells = {}
for row in trades:
    opened = row["body"].get("opened_at")
    at = opened if isinstance(opened, int) else ns_of(row["at"])
    r = Decimal(str(row["body"].get("r", "0")))
    found = cells.setdefault((row["unit_id"], row["market_id"]), {"r": [], "words": {}})
    found["r"].append(r)
    for reading in asked["readings"]:
        said = [word for t, word in history.get((reading, row["market_id"]), []) if t <= at]
        word = said[-1] if said else "no reading"
        earned = found["words"].setdefault(reading, {}).setdefault(word, [0, Decimal(0)])
        earned[0] += 1
        earned[1] += r

min_trades, drop_at = int(asked["min_trades"]), Decimal(asked["drop_at_r"])
records, cards = [], []
for (unit, market), found in sorted(cells.items()):
    total = sum(found["r"], Decimal(0))
    expectancy = (total / len(found["r"])).quantize(CENT)
    records.append(
        {
            "unit": unit,
            "market": market,
            "trades": len(found["r"]),
            "expectancy_r": str(expectancy),
            "r": str(total),
            "by_reading": {
                reading: {w: {"trades": n, "r": str(r)} for w, (n, r) in sorted(words.items())}
                for reading, words in sorted(found["words"].items())
            },
        }
    )
    if len(found["r"]) >= min_trades and expectancy <= drop_at:
        why = (
            f"{len(found['r'])} trades on {market} over {asked['lookback_days']} days average "
            f"{expectancy}R, at or below {drop_at}R"
        )
        cards.append({"subject": unit, "ask": "drop_market", "placeholders": [market], "why": why})

findings = {
    "day": day,
    "window": answer["window"],
    "settings": {name: asked[name] for name in ("lookback_days", "min_trades", "drop_at_r")},
    "records": records,
    "readings_refused": refused,
    "proposals": len(cards),
}
note = None
if not cards:
    note = {
        "title": f"Markets for the week to {day}: no change proposed",
        "text": f"{len(records)} unit and market records read; none is at or below the drop line "
        "with enough trades. Nothing is proposed.",
        "receipts": ["read"],
    }
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
(bodies / "findings.json").write_text(json.dumps(findings, sort_keys=True), encoding="utf-8")
print(
    json.dumps(
        {
            "findings": findings,
            "quiet": not cards,
            "note": note,
            "note_kind": "proposal",
            "about": [{"rel": "unit", "ref": u} for u in sorted({r["unit"] for r in records})],
            "window": answer["window"],
            "cards": cards,
            "library": [
                {
                    "op": "put_artifact",
                    "type": "market-tags",
                    "body": "library/findings.json",
                    "metadata": findings,
                    "intent_key": f"market-tags|{day}",
                }
            ],
        }
    )
)
