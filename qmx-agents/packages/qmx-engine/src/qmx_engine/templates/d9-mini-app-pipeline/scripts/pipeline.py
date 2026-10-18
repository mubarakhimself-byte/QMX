"""The pipeline folder and the enable card (card D9 steps 3 and 6 and its gates). Its inputs, the
wiring and the contract test, are told apart by shape. Zero tokens.

The folder is written as data: the producer's output wired into the consumer's input, `wait` or
the last good artifact marked stale, and the trigger it would run on ("after the producer emits"),
pinned to both apps' versions. A producer version change re-runs the contract test before the
pipeline accepts new output. Nothing is enabled here: a pipeline outside the Lab is a standing
schedule, so the enable card waits for his yes, and only a passed contract test gets one.
"""

import json
import sys

given = json.load(sys.stdin)["in"]
wiring = next(v for v in given if "producer" in v and "emits" in v)
contract = next(v for v in given if "passed" in v)
folder = {
    "inputs_from": {"app": wiring["producer"], "output": wiring["emits"], "wait": wiring["wait"]},
    "accepts": {"app": wiring["consumer"], "input": wiring["accepts"]},
    "transform": contract["transform"],
    "on_late_producer": "wait" if wiring["wait"] else "use the last good artifact, marked stale",
    "runs_after": f"{wiring['producer']} emits {wiring['emits']}",
    "pinned": {"producer": contract["producer_version"], "consumer": contract["consumer_version"]},
}
card = None
if contract["passed"]:
    card = {"kind": "enable pipeline", "waits_for": "his yes", "show_in": wiring["show_in"]}
print(
    json.dumps(
        {
            "folder": folder,
            "contract": contract,
            "questions": wiring["questions"],
            "card": card,
        }
    )
)
