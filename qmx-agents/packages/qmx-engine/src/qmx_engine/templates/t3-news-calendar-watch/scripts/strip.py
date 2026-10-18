"""Turns the day's calendar into the calendar strip for the watchlist: each event that touches a
watched currency, its blackout window when it is high impact, its surprise score once the actual
is in, and one alert line per high-impact event or surprise, each with its source link.

The watchlist stands in for the active units until the trading node exists, so the guard's news
list cannot be cross-checked yet. A surprise is |actual - forecast| / typical_surprise >= 1.5;
at most 10 surprises a day reach the note step.
"""

import json
import re
import sys
from datetime import datetime, timedelta

WATCHLIST = {"EURUSD": ("EUR", "USD"), "USDJPY": ("USD", "JPY")}
BLACKOUT_MIN = 30
SURPRISE_Z = 1.5
MOST_NOTES = 10
NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def number(value):
    if isinstance(value, int | float):
        return float(value)
    found = NUMBER.search(str(value or ""))
    return float(found.group()) if found else None


calendar = json.load(sys.stdin)["in"]["value"]
day = calendar["date"]
strip, blackouts, surprises, alerts = [], [], [], []
for event in sorted(calendar["events"], key=lambda e: e["time_utc"]):
    instruments = [pair for pair, legs in WATCHLIST.items() if event["currency"] in legs]
    if not instruments:
        continue
    actual, forecast = number(event.get("actual")), number(event.get("forecast"))
    typical = number(event.get("typical_surprise"))
    z = None
    if actual is not None and forecast is not None and typical:
        z = round((actual - forecast) / typical, 2)
    strip.append(event | {"instruments": instruments, "z": z})
    at = datetime.fromisoformat(f"{day}T{event['time_utc']}")
    half = timedelta(minutes=BLACKOUT_MIN)
    window = f"{at - half:%H:%M}-{at + half:%H:%M} UTC"
    if event["impact"] == "high":
        blackouts.append({"event": event["title"], "instruments": instruments, "window": window})
        alerts.append(
            f"{event['time_utc']} UTC {event['currency']} {event['title']} (high impact): "
            f"no new entries {window} on {', '.join(instruments)}. Source: {event['source']}"
        )
    if z is not None and abs(z) >= SURPRISE_Z and len(surprises) < MOST_NOTES:
        surprises.append(
            {
                "event": event["title"],
                "currency": event["currency"],
                "instruments": instruments,
                "actual": event["actual"],
                "forecast": event["forecast"],
                "z": z,
                "source": event["source"],
            }
        )
        alerts.append(
            f"{event['time_utc']} UTC {event['currency']} {event['title']} surprised: actual "
            f"{event['actual']} against forecast {event['forecast']} (z {z}). "
            f"Source: {event['source']}"
        )
print(
    json.dumps(
        {
            "date": day,
            "watchlist": sorted(WATCHLIST),
            "strip": strip,
            "blackouts": blackouts,
            "surprises": surprises,
            "surprise_count": len(surprises),
            "alerts": alerts,
            "guard_cross_check": "could not check: trading node",
            "notes": [],
        }
    )
)
