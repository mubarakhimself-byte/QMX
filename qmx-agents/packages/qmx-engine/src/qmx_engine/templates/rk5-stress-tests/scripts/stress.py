"""The scenarios and the pass rules (card R5 steps 3 and 4).

Each scenario is applied as a shock to every position it touches: the loss is the risk to the stop,
plus the gap beyond the stop (gap in ATR minus the stop distance, in pips), plus slippage and the
widened spread, each times the pip value. A guard simulation then asks whether the guard's kill
switch, reacting after its configured seconds, holds the overshoot below the kill line within the
allowed amount. A scenario passes when equity stays above the kill line by the buffer, or the guard
stops it with an overshoot no larger than allowed, and the prop daily limit is not breached. A
scenario whose instrument has no cost-model row reads "not run", never "pass".
"""

import json
import sys
from fnmatch import fnmatch
from pathlib import Path

library = json.loads((Path(__file__).parents[1] / "data" / "scenarios.json").read_text("utf-8"))
book = json.load(sys.stdin)["in"]["value"]
account, costs = book["account"], book["costs"]
results = []
for scenario in library["scenarios"]:
    hit = [
        p
        for p in book["positions"]
        if any(fnmatch(p["instrument"], pattern) for pattern in scenario["instruments"])
    ]
    missing = sorted({p["instrument"] for p in hit if p["instrument"] not in costs})
    if missing:
        results.append(
            {"id": scenario["id"], "verdict": "not run", "why": f"no cost model for {missing}"}
        )
        continue
    loss, per_unit = 0.0, {}
    for p in hit:
        cost = costs[p["instrument"]]
        beyond = max(0.0, scenario["gap_atr"] * cost["atr_pips"] - p["stop_pips"])
        extra = (
            beyond + scenario["slippage_pips"] + cost["spread_pips"] * (scenario["spread_x"] - 1)
        )
        unit_loss = p["risk_usd"] + extra * p["pip_value_usd"]
        loss += unit_loss
        per_unit[p["unit"]] = per_unit.get(p["unit"], 0) + unit_loss / p["r_usd"]
    left = account["equity"] - loss - account["kill_line"]
    overshoot = max(0.0, -left)
    guarded = overshoot <= account["max_overshoot_usd"]
    passed = (left >= account["buffer_usd"] or guarded) and loss <= account["daily_limit_usd"]
    results.append(
        {
            "id": scenario["id"],
            "name": scenario["name"],
            "verdict": "pass" if passed else "fail",
            "loss_usd": round(loss, 2),
            "cushion_left_usd": round(left, 2),
            "overshoot_usd": round(overshoot, 2),
            "guard_reaction_s": book["guard"]["kill_reaction_s"],
            "cushion_left_r_by_unit": {u: round(-r, 2) for u, r in per_unit.items()},
        }
    )
ran = [r for r in results if r["verdict"] != "not run"]
worst = sorted(ran, key=lambda r: r["cushion_left_usd"])[:3]
print(json.dumps({"at": book["at"], "results": results, "worst": worst}))
