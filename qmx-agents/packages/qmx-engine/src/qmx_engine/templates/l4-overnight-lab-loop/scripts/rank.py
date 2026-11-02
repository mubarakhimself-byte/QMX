"""The end of the night (card L4 steps 12, 14 and 17 and its gates). Every gate is a script; no
model grades a result. Its inputs, the night's last state, the holdout runs and the `judge`
block's verdict, are told apart by shape; the verdict is found by its key inside the child's
nested outputs.

Survivors are ranked by validated score. A survivor whose holdout score falls outside its
validation Monte Carlo band "did not hold" and is kept as a dead end, tagged `negative_result`
with the run's trial count and the region it came from, as is every trial that failed a gate. The
plateau map is each move, with its reason kept apart as prose; the old spaces are dead regions.
Two decisions at most, each with a recommendation.
"""

import json
import sys


def judged(value):
    if isinstance(value, dict):
        if isinstance(value.get("verdict"), dict):
            return value["verdict"]
        value = list(value.values())
    if isinstance(value, list):
        return next((found for v in value if (found := judged(v)) is not None), None)
    return None


given = json.load(sys.stdin)["in"]
state = next(v for v in given if "ledger" in v)
touched = next(v for v in given if "holdout" in v)
holdout = {h["spec_hash"]: h for h in touched["holdout"]}
verdict = judged([v for v in given if v is not state and v is not touched])
passed = [t for t in state["ledger"] if not t.get("error") and not t["failed"]]
ranked = sorted(passed, key=lambda t: -t["validated"])
survivors, dead_ends = [], []
for trial in ranked:
    touch = holdout.get(trial["spec_hash"])
    if touch is None:
        survivors.append(
            {"spec_hash": trial["spec_hash"], "validated": trial["validated"], "holdout": None}
        )
        continue
    low, high = touch["monte_carlo"]
    held = low <= touch["holdout"] <= high
    row = {
        "spec_hash": trial["spec_hash"],
        "in_sample": trial["in_sample"],
        "validated": trial["validated"],
        "holdout": touch["holdout"],
        "held": held,
    }
    (survivors if held else dead_ends).append(row | ({} if held else {"why": "did not hold"}))
dead_ends += [
    {"spec_hash": t["spec_hash"], "why": t.get("error") or "failed " + ", ".join(t["failed"])}
    for t in state["ledger"]
    if t.get("error") or t["failed"]
]
held = [s for s in survivors if s.get("held")]
decisions = []
if held:
    decisions.append(
        {"decision": f"send {held[0]['spec_hash'][:8]} to D3 to improve", "recommended": "yes"}
    )
if held and verdict is not None and verdict["overall"] == "pass":
    decisions.append(
        {
            "decision": f"check {held[0]['spec_hash'][:8]} against the book in P1",
            "recommended": "yes",
        }
    )
print(
    json.dumps(
        {
            "silent": not state["ledger"],
            "trials_tonight": state["trials_tonight"],
            "trials_family": state["trials_family"],
            "judge": verdict,
            "survivors": survivors[:10],
            "dead_ends": [d | {"tag": "negative_result"} for d in dead_ends],
            "moves": [
                {k: m[k] for k in ("move", "target", "value", "refused")} for m in state["history"]
            ],
            "move_reasons": [m["reason"] for m in state["history"]],
            "dead_regions": len(state["dead_regions"]),
            "decisions": decisions[:2],
        }
    )
)
