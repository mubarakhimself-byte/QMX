"""The `death-certificate` block's first step: a failed verdict's typed cause, by script.

Its input is `{"in": ...}` holding the `judge` block's output, `{"item", "verdict", "says"}`, as
it is or as the subworkflow node hands it on, `{"run_id", "outputs": {"judge": {"main": ...}}}`.
A verdict that is not `fail` or `no_trades` is refused: only a failed unit gets a certificate.

The cause is the judge's own table (`qmx_judge.judge.CAUSES`), read by the first step a failed
market failed; a fail no step explains is `behaviour`, and a unit that placed no trades is
`no_trades`. It prints the certificate's fields and the `dead_end` memory row the certificate
stands for, keyed by the unit, so a later build's dead-end check finds it.
"""

import json
import sys

from qmx_judge.judge import CAUSES, CLASSIFIER_VERSION

FAILURE = "[QMX_FAILURE]"


def judged(value):
    """The judge block's output inside `value`, or None."""
    if not isinstance(value, dict):
        return None
    if isinstance(value.get("verdict"), dict) and "item" in value:
        return value
    if "main" in value:
        return judged(value["main"])
    outputs = value.get("outputs")
    return judged(outputs.get("judge")) if isinstance(outputs, dict) else None


given = json.load(sys.stdin)["in"]
found = next((j for v in (given if isinstance(given, list) else [given]) if (j := judged(v))), None)
if found is None:
    print(f"{FAILURE} the death-certificate block needs the judge block's verdict")
    raise SystemExit(0)

verdict, item = found["verdict"], found["item"]
overall = verdict.get("overall")
if overall not in ("fail", "no_trades"):
    print(f"{FAILURE} {item} is {overall}; only a failed unit gets a death certificate")
    raise SystemExit(0)

cause = "no_trades"
if overall == "fail":
    failed = [
        step["name"]
        for market in verdict.get("per_market", [])
        if market.get("outcome") == "fail"
        for step in market.get("steps", [])
        if step.get("outcome") == "failed"
    ]
    cause = CAUSES[failed[0]] if failed else "behaviour"

unit = verdict["unit"]
says = found.get("says") or verdict.get("says") or ""
certificate = {
    "unit": unit,
    "verdict": item,
    "cause": cause,
    "classifier_version": CLASSIFIER_VERSION,
}
dead_end = {
    "tag": "dead_end",
    "intent_key": unit,
    "when_to_use": f"before building {unit} again or a unit with the same rules",
    "content": f"{unit} died of {cause}. {says}".strip(),
    "refs": [unit, item],
}
print(json.dumps({"certificate": certificate, "dead_end": dead_end, "says": says}))
