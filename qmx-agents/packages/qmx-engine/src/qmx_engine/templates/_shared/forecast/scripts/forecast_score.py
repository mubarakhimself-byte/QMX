"""The `forecast` block's score step: a dated call scored by script after its horizon, never by
its author (WF-11).

Its input is `{"in": {"forecast": {...}, "outcome": {...}}}`. `forecast` is a landed call's fields,
as the write step landed them. `outcome` is what the recorded market did over the call's window,
read by the calling template's own script step: `market`, `open` and `close` as price text, and
`state`, the reading state at the horizon, when the call made one.

The script decides whether the call held: `up` when the close is above the open, `down` when it is
below, a `range` when the close is inside it, a `state` when it matches, and every part a call
makes must hold. It then scores the call's confidence with the judge's own Brier score
(`qmx_judge.judge.score_forecast`). Only the `forecast` kind's fields are read from the call, so
any score, outcome or verdict its author wrote is ignored. A call scored before its horizon, or
against another market, is refused.

It lands the scored call as one `forecast` artifact on the run's own ref, with `happened` and the
outcome it was scored on, and prints it.
"""

import json
import os
import sys
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from qmx_judge.judge import score_forecast

FAILURE = "[QMX_FAILURE]"
KIND_FIELDS = ("market", "call", "horizon", "confidence", "written_at", "written_by")


def fail(why):
    print(f"{FAILURE} {why}")
    raise SystemExit(0)


def instant(text):
    try:
        moment = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None
    return (moment if moment.tzinfo else moment.replace(tzinfo=UTC)).astimezone(UTC)


def price(outcome, name):
    try:
        found = Decimal(outcome[name]) if isinstance(outcome.get(name), str) else None
    except InvalidOperation:
        found = None
    if found is None or not found.is_finite():
        fail(f"the outcome's {name} is not a price as text")
    return found


given = json.load(sys.stdin).get("in")
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
asked = next((r for r in rows if isinstance(r.get("forecast"), dict) and "outcome" in r), None)
if asked is None or not isinstance(asked["outcome"], dict):
    fail("the forecast block's score step needs a forecast and the recorded outcome")
forecast = {k: asked["forecast"][k] for k in KIND_FIELDS if k in asked["forecast"]}
outcome = asked["outcome"]
at = instant(asked.get("at") or os.environ.get("QMX_NOW") or datetime.now(UTC).isoformat())
horizon = instant(forecast.get("horizon"))
if horizon is None or at is None or at < horizon:
    fail(f"the call for {forecast.get('horizon')!r} is scored only after its horizon")
if outcome.get("market") != forecast.get("market"):
    fail(f"the outcome is for {outcome.get('market')!r}, not {forecast.get('market')!r}")

call = forecast.get("call") if isinstance(forecast.get("call"), dict) else {}
opened, closed = price(outcome, "open"), price(outcome, "close")
held = []
if "direction" in call:
    held.append(closed > opened if call["direction"] == "up" else closed < opened)
if "range" in call:
    bounds = call["range"] if isinstance(call["range"], dict) else {}
    held.append(Decimal(str(bounds.get("low"))) <= closed <= Decimal(str(bounds.get("high"))))
if "state" in call:
    held.append(outcome.get("state") == call["state"])
if not held:
    fail("the forecast makes no call to score")

happened = all(held)
stamp = at.isoformat().replace("+00:00", "Z")
scored = {**score_forecast(forecast, happened, stamp), "happened": happened, "outcome": outcome}
bodies = Path(os.environ["QMX_WORK"]) / "library"
bodies.mkdir(parents=True, exist_ok=True)
(bodies / "scored.json").write_text(json.dumps(scored, sort_keys=True), encoding="utf-8")
write = {
    "op": "put_artifact",
    "type": "forecast",
    "body": "library/scored.json",
    "metadata": scored,
    "intent_key": f"forecast-score|{forecast['market']}|{forecast['horizon']}|"
    f"{forecast.get('written_by')}|{forecast.get('written_at')}",
}
print(json.dumps({"scored": scored, "library": [write]}))
