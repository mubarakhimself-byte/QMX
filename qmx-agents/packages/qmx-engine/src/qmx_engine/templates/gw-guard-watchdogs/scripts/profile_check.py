"""The tighten-only check (card R6, step 2): a second line of defence behind the node's own refusal.

For each unit, every parameter that changed from profile N-1 to N must move the tighter way in the
direction table, or move within the signed ramp schedule, or carry a signature id. Every value must
stay inside its signed range. Any violation is black, and the suggested action is "revert to the
last signed profile", which only he can approve.
"""

import json
import sys

state = json.load(sys.stdin)["in"]
direction = state["direction"]
results = []
for profile in state["profiles"]:
    current, previous, signed = profile["current"], profile["previous"], profile["signed"]
    violations = []
    for name, value in current.items():
        low, high = signed["ranges"].get(name, (None, None))
        if low is not None and not low <= value <= high:
            violations.append(f"{name} {value} is outside its signed range {low}-{high}")
        before = previous.get(name)
        if before is None or before == value:
            continue
        tighter = (value < before) if direction.get(name) == "down" else (value > before)
        in_ramp = value in signed.get("ramp", {}).get(name, [])
        if not (tighter or in_ramp or profile.get("signature_ids", {}).get(name)):
            violations.append(f"{name} loosened from {before} to {value} with no signature")
    results.append(
        {
            "unit": profile["unit"],
            "verdict": "black" if violations else "pass",
            "violations": violations,
            "suggested": "revert to the last signed profile" if violations else None,
        }
    )
level = "black" if any(r["verdict"] == "black" for r in results) else "pass"
print(json.dumps({"profiles": results, "level": level}))
