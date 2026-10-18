"""The leakage checks and the spend check (card D6 step 4 and its gates). Its inputs, the run's
inputs, the scope and the built dataset, are told apart by shape.

The purge gap is at least the label horizon, so no training label overlaps a validation label.
Every feature ends before its label starts. A model trained on shuffled labels scores within 0.02
of chance; above that is a leak and the run stops. The sealed test has never been touched for this
family. A training run never starts above his ask-above number (5 USD unless the run names one)
without his yes.
"""

import json
import sys

SHUFFLE_TOLERANCE = 0.02
ASK_ABOVE_USD = 5.0

given = json.load(sys.stdin)["in"]
scope = next(v for v in given if "horizon_bars" in v)
data = next(v for v in given if "splits" in v)
run = next((v for v in given if "goal" in v), {})
problems = []
if data["purge_bars"] < scope["horizon_bars"]:
    problems.append(
        f"purge {data['purge_bars']} bars is shorter than the label horizon {scope['horizon_bars']}"
    )
if data["feature_lag_bars"] < 1:
    problems.append("a feature reads data from inside its label's window")
if data["shuffle_score"] - data["chance_score"] > SHUFFLE_TOLERANCE:
    problems.append(
        f"leak: shuffled labels score {data['shuffle_score']} against chance {data['chance_score']}"
    )
if data["sealed_test"]["touched"] > 0:
    problems.append("the sealed test was already touched; a second look needs a new window")
over = data["estimate_usd"] > run.get("ask_above_usd", ASK_ABOVE_USD)
if over:
    problems.append(f"the estimate {data['estimate_usd']} USD is above his ask-above number")
print(
    json.dumps(
        {
            "ok": not problems,
            "problems": problems,
            "splits": data["splits"],
            "purge_bars": data["purge_bars"],
            "embargo_bars": data["embargo_bars"],
            "shuffle_score": data["shuffle_score"],
            "chance_score": data["chance_score"],
            "estimate_usd": data["estimate_usd"],
            "spend_card": {"kind": "approve compute", "estimate_usd": data["estimate_usd"]}
            if over
            else None,
        }
    )
)
