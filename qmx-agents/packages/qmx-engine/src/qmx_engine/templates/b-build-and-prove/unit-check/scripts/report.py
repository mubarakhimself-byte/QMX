"""The `unit-check` block's last step: what the check rounds came to, for the calling template.

Its input is the last round's value from `check.py`. It prints `verdict` (`pass` or `fail`),
`rounds` (the fix rounds run), `stopped` (`passed`, `no_progress` or `rounds_used`, when the loop
ran out of rounds with problems left), `why`, the `unit` as last checked, its `problem_set` and its
`errors`. A failed check is a result here, not a failed step, so the template routes it.
"""

import json
import sys

given = json.load(sys.stdin)["in"]
rows = [v for v in (given if isinstance(given, list) else [given]) if isinstance(v, dict)]
last = next(r for r in rows if "round" in r)
check = last["check"]
stopped = "rounds_used"
why = last["why"]
if check["verdict"] == "pass":
    stopped = "passed"
elif check["no_progress"]:
    stopped = "no_progress"
else:
    why = f"{last['round']} fix round(s) ran and {check['counts']['errors']} problem(s) remain"
print(
    json.dumps(
        {
            "verdict": check["verdict"],
            "rounds": last["round"],
            "stopped": stopped,
            "why": why,
            "unit": last["unit"],
            "problem_set": check["problem_set"],
            "errors": check["errors"],
        }
    )
)
