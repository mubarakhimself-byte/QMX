"""The `forecast` block's write step: dated calls landed before their session (WF-11).

Its input is `{"in": {"forecasts": [...], "author": ...}}`. Each forecast names its `market`, its
`call` (`direction` `up` or `down`, a price `range` `{low, high}`, a reading `state`, or several of
them, all of which must hold), its `horizon` (the ISO 8601 time the call is for, such as the
session's close) and its `confidence` (the chance it holds, above 0 and at most 1, as text).
`author` is who made the calls, such as `agent:market-review`.

Each call lands as one `forecast` artifact on the run's own ref, stamped `written_at` the run's own
clock and `written_by` the author, with only the `forecast` kind's fields: anything else the author
wrote, a score or an outcome of its own included, is dropped. A call whose horizon is not after its
writing is refused, with every problem named. The block's score step scores it later.
"""

import json
import os
import sys
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

FAILURE = "[QMX_FAILURE]"
DIRECTIONS = ("up", "down")
CALLS = ("direction", "range", "state")


def instant(text):
    try:
        moment = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None
    return (moment if moment.tzinfo else moment.replace(tzinfo=UTC)).astimezone(UTC)


def number(text):
    try:
        found = Decimal(text) if isinstance(text, str) else None
    except InvalidOperation:
        return None
    return found if found is not None and found.is_finite() else None


def problems_of(place, forecast, written_at):
    found = []
    call = forecast.get("call")
    if not isinstance(forecast.get("market"), str) or not forecast["market"]:
        found.append(f"forecast {place} names no market")
    if not isinstance(call, dict) or not set(CALLS) & set(call):
        found.append(f"forecast {place} makes no call: a direction, a range or a state")
        call = {}
    if "direction" in call and call["direction"] not in DIRECTIONS:
        found.append(f"forecast {place}: direction {call['direction']!r} is not up or down")
    if "range" in call:
        bounds = call["range"] if isinstance(call["range"], dict) else {}
        low, high = (number(bounds.get(k)) for k in ("low", "high"))
        if low is None or high is None or low > high:
            found.append(f"forecast {place}: range is not {{low, high}} as text with low <= high")
    if "state" in call and not isinstance(call["state"], str):
        found.append(f"forecast {place}: state is not text")
    horizon = instant(forecast.get("horizon"))
    if horizon is None or horizon <= written_at:
        found.append(f"forecast {place}: horizon {forecast.get('horizon')!r} is not after now")
    confidence = number(forecast.get("confidence"))
    if confidence is None or not Decimal(0) < confidence <= Decimal(1):
        found.append(f"forecast {place}: confidence is not text above 0 and at most 1")
    return found


given = json.load(sys.stdin).get("in")
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
asked = next((r for r in rows if isinstance(r.get("forecasts"), list)), None)
if asked is None or not isinstance(asked.get("author"), str) or not asked["author"]:
    print(f"{FAILURE} the forecast block needs forecasts and the author who made them")
    raise SystemExit(0)
now = os.environ.get("QMX_NOW") or datetime.now(UTC).isoformat()
written_at = instant(now)
problems = [p for i, f in enumerate(asked["forecasts"], 1) for p in problems_of(i, f, written_at)]
if not asked["forecasts"]:
    problems.append("there are no forecasts to write")
if problems:
    print(f"{FAILURE} {'; '.join(problems)}")
    raise SystemExit(0)

stamp = written_at.isoformat().replace("+00:00", "Z")
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
landed, writes = [], []
for place, given_forecast in enumerate(asked["forecasts"], 1):
    forecast = {
        "market": given_forecast["market"],
        "call": {k: v for k, v in given_forecast["call"].items() if k in CALLS},
        "horizon": given_forecast["horizon"],
        "confidence": given_forecast["confidence"],
        "written_at": stamp,
        "written_by": asked["author"],
    }
    (bodies / f"forecast-{place}.json").write_text(json.dumps(forecast, sort_keys=True), "utf-8")
    call = json.dumps(forecast["call"], sort_keys=True)
    writes.append(
        {
            "op": "put_artifact",
            "type": "forecast",
            "body": f"library/forecast-{place}.json",
            "metadata": forecast,
            "intent_key": f"forecast|{forecast['market']}|{forecast['horizon']}|"
            f"{asked['author']}|{call}",
        }
    )
    landed.append(forecast)
print(json.dumps({"forecasts": landed, "library": writes}))
