"""Each unit's recent trades against its own record before them: OK, Watch or Alarm. Zero tokens.

Inputs are the card's settings, each left out taking its `default` in `definition.json`: `day`
(the record ends with this UTC day, the day before the run by default), `record_days`,
`recent_trades`, `min_record_trades`, `watch_drop_r`, `alarm_at_r`, `watch_streak`,
`alarm_streak`, and optionally `units` and `world`.

It reads every closed trade in R over the record through `journal_query`. Per unit, the last
`recent_trades` trades are judged against the trades before them:

- Alarm when the recent expectancy is at or below `alarm_at_r` while the record's is above it, or
  the recent trades hold `alarm_streak` losses in a row;
- Watch when the recent expectancy sits `watch_drop_r` or more below the record's, or the recent
  trades hold `watch_streak` losses in a row;
- OK otherwise.

A unit with fewer than `recent_trades` recent or `min_record_trades` earlier trades is thin and is
not judged. Every Watch and Alarm gets one `tighten` card: what to tighten is the risk session's
call and his click. The check informs only; nothing moves a unit. A run with no flagged unit is
quiet and asks no model.
"""

import importlib.util
import json
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

spec = importlib.util.spec_from_file_location("door", Path(__file__).with_name("door.py"))
door = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door)

CENT = Decimal("0.01")


def r_of(row):
    return Decimal(str(row["body"].get("r", "0")))


def mean(values):
    return sum(values, Decimal(0)) / len(values)


def longest_losing(values):
    streak = longest = 0
    for value in values:
        streak = streak + 1 if value < 0 else 0
        longest = max(longest, streak)
    return longest


asked = door.settings(json.load(sys.stdin).get("in"))
day, last_day = door.day_window(asked.get("day"))
end = datetime.fromisoformat(last_day["end"].replace("Z", "+00:00"))
window = {"start": door.iso(end - timedelta(days=int(asked["record_days"]))), "end": door.iso(end)}
filters = {"kind": "trade"} | ({"world": asked["world"]} if asked.get("world") else {})
try:
    answer = door.journal(door.home(), stream="unit", window=window, filters=filters)
except ValueError as refused:
    print(f"[QMX_FAILURE] {refused}")
    raise SystemExit(0) from None

wanted = set(asked.get("units") or [])
trades = {}
for row in answer["rows"]:
    if not wanted or row["unit_id"] in wanted:
        trades.setdefault(row["unit_id"], []).append(r_of(row))

recent_n, record_n = int(asked["recent_trades"]), int(asked["min_record_trades"])
watch_drop, alarm_at = Decimal(asked["watch_drop_r"]), Decimal(asked["alarm_at_r"])
judged, thin, cards = [], [], []
for unit, values in sorted(trades.items()):
    recent, record = values[-recent_n:], values[:-recent_n]
    if len(recent) < recent_n or len(record) < record_n:
        thin.append({"unit": unit, "trades": len(values)})
        continue
    now_r, before_r = mean(recent).quantize(CENT), mean(record).quantize(CENT)
    streak = longest_losing(recent)
    if (now_r <= alarm_at < before_r) or streak >= int(asked["alarm_streak"]):
        status = "Alarm"
    elif before_r - now_r >= watch_drop or streak >= int(asked["watch_streak"]):
        status = "Watch"
    else:
        status = "OK"
    why = (
        f"its last {len(recent)} trades average {now_r}R against {before_r}R over the "
        f"{len(record)} before them, with at most {streak} losses in a row"
    )
    judged.append(
        {
            "unit": unit,
            "status": status,
            "recent_trades": len(recent),
            "recent_expectancy_r": str(now_r),
            "record_trades": len(record),
            "record_expectancy_r": str(before_r),
            "longest_losing_streak": streak,
            "why": why,
        }
    )
    if status != "OK":
        cards.append({"subject": unit, "ask": "tighten", "why": f"{status}: {why}"})

flagged = [u for u in judged if u["status"] != "OK"]
findings = {
    "day": day,
    "window": answer["window"],
    "settings": {
        name: asked[name]
        for name in (
            "record_days",
            "recent_trades",
            "min_record_trades",
            "watch_drop_r",
            "alarm_at_r",
            "watch_streak",
            "alarm_streak",
        )
    },
    "units": judged,
    "thin": thin,
    "flagged": len(flagged),
}
note = None
if not flagged:
    note = {
        "title": f"Decay check to {day}: nothing flagged",
        "text": f"{len(judged)} units judged, all OK; {len(thin)} too thin to judge. "
        "Nothing is proposed.",
        "receipts": ["read"],
    }
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
(bodies / "findings.json").write_text(json.dumps(findings, sort_keys=True), encoding="utf-8")
print(
    json.dumps(
        {
            "findings": findings,
            "quiet": not flagged,
            "note": note,
            "note_kind": "analysis",
            "about": [{"rel": "unit", "ref": u["unit"]} for u in judged],
            "window": answer["window"],
            "cards": cards,
            "library": [
                {
                    "op": "put_artifact",
                    "type": "decay-check",
                    "body": "library/findings.json",
                    "metadata": findings,
                    "intent_key": f"decay-check|{day}",
                }
            ],
        }
    )
)
