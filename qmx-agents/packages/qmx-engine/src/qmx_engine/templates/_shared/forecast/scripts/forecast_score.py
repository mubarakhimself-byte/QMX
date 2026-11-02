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
any score, outcome or verdict its author wrote is ignored. The clock is the run's own (`QMX_NOW`),
never a field of the input. The call is checked again as the write step checks it, against its own
`written_at`: one with no `written_at`, one not written before its horizon, an unknown direction, a
range without both bounds or a confidence not above 0 is refused. So is a call scored before its
horizon, or against another market.

It lands the scored call as one `forecast` artifact on the run's own ref, with `happened` and the
outcome it was scored on, and prints it.
"""

import importlib.util
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


def write_step():
    """The write step's module, for its `instant` and `problems_of`: scripts run with `-I`, so a
    sibling file is loaded by path."""
    path = Path(__file__).with_name("forecast_write.py")
    spec = importlib.util.spec_from_file_location("forecast_write", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
write = write_step()
written_at = write.instant(forecast.get("written_at"))
if written_at is None:
    fail("the call has no written_at time, so nothing shows it was made before its horizon")
problems = write.problems_of(1, forecast, written_at)
if problems:
    fail("; ".join(problems))
at = write.instant(os.environ.get("QMX_NOW") or datetime.now(UTC).isoformat())
if at is None or at < write.instant(forecast["horizon"]):
    fail(f"the call for {forecast['horizon']!r} is scored only after its horizon")
if outcome.get("market") != forecast["market"]:
    fail(f"the outcome is for {outcome.get('market')!r}, not {forecast['market']!r}")

call = forecast["call"]
opened, closed = price(outcome, "open"), price(outcome, "close")
held = []
if "direction" in call:
    held.append(closed > opened if call["direction"] == "up" else closed < opened)
if "range" in call:
    held.append(Decimal(call["range"]["low"]) <= closed <= Decimal(call["range"]["high"]))
if "state" in call:
    held.append(outcome.get("state") == call["state"])

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
