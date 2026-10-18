"""The gauge and the alert lines (cards R1 and R6, step 3): cushion in dollars, in R and in percent
of the day's budget, one line per amber, red or black finding, and each profile verdict. Its inputs,
the cushion and the profile check, are told apart by shape."""

import json
import sys

ORDER = ("green", "pass", "amber", "red", "black")

given = json.load(sys.stdin)["in"]
gauge = next(v for v in given if "cushion_usd" in v)
profiles = next(v for v in given if "profiles" in v)
alerts = []
if gauge["level"] in ("amber", "red", "black"):
    alerts.append(
        f"{gauge['level']}: worst-case cushion {gauge['worst_case_usd']} USD, "
        f"{gauge['distance_r']} R, {gauge['budget_worst_case_pct']}% of the day's budget"
    )
if not gauge["config_hash_matches"]:
    alerts.append("black: the guard config hash differs from the signed config")
alerts += [
    f"black: {p['unit']} {violation}; suggested: {p['suggested']}"
    for p in profiles["profiles"]
    for violation in p["violations"]
]
level = max(gauge["level"], profiles["level"], key=ORDER.index)
print(
    json.dumps(
        {
            "at": gauge["at"],
            "level": level,
            "gauge": gauge,
            "profiles": profiles["profiles"],
            "alerts": alerts,
        }
    )
)
