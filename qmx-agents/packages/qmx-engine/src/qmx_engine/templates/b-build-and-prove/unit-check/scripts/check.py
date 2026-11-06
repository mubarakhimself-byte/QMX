"""The `unit-check` block's check: Part A's `unit_check` row on the unit this round holds.

Its input is `{"in": ...}`. The first check gets `{"unit": <document>}`. Each later check gets the
round's value, `{"unit", "round", "check", "stop", "why"}`, and the fix step's `{"unit": ...}`.
It checks the newest document with `qmx_tools.unit_check.offline_checked`, the row's own check with
no Library, and passes the last result's `problem_set`, so a fix that brings the same problems back
reads `no_progress` and the loop stops (Part A AG-11). A script never opens the Library, so what
only the Library can settle is a note on the result, not an error to spend a fix round on.

It prints the next round's value. `stop` is true once the unit passes or makes no progress, and
`why` says which.
"""

import json
import sys

from qmx_tools.unit_check import offline_checked

FAILURE = "[QMX_FAILURE]"

given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
held = next((r for r in rows if "round" in r), None)
fixed = next((r for r in rows if "round" not in r and isinstance(r.get("unit"), dict)), None)
if held is None and fixed is None:
    print(f"{FAILURE} the unit-check block needs a unit document under `unit`")
    raise SystemExit(0)

document = (fixed or held)["unit"]
previous = None if held is None else (held.get("check") or {}).get("problem_set")
number = 0 if held is None else held["round"] + 1
result = offline_checked(document, previous)
errors = result["counts"]["errors"]
why = None
if result["verdict"] == "pass":
    why = "the unit passes its check"
elif result["no_progress"]:
    why = (
        f"the same {errors} problem(s) came back after fix round {number}, "
        f"problem set {result['problem_set']}"
    )
print(
    json.dumps(
        {"unit": document, "round": number, "check": result, "stop": why is not None, "why": why}
    )
)
