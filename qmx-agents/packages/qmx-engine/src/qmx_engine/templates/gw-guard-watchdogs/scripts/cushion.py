"""Distance to the kill line (card R1, steps 2 and 3).

Cushion D = equity - kill line. Worst case D_wc = D - open risk to stops - k x typical slippage x
open lots - the gap allowance. The same worst case is taken against the day's loss budget left.
Distance in R = D_wc / the largest active r. Amber below 30% of the daily budget or 3R; red below
10% or 1R; black when the guard heartbeat is older than 60 s or the guard config hash differs from
the signed one. R1 only watches and tells; the guard acts.
"""

import json
import sys

AMBER_PCT, RED_PCT = 0.30, 0.10
AMBER_R, RED_R = 3, 1
HEARTBEAT_S = 60

state = json.load(sys.stdin)["in"]
risk = sum(p["risk_to_stop"] for p in state["open_positions"])
lots = sum(p["lots"] for p in state["open_positions"])
allowance = state["slippage_k"] * state["typical_slippage_per_lot"] * lots + state["gap_allowance"]
cushion = state["equity"] - state["kill_line"]
worst = cushion - risk - allowance
budget = state["daily_budget"]["limit"]
budget_left = budget - state["daily_budget"]["used"]
budget_worst = budget_left - risk - allowance
distance_r = worst / state["largest_r"] if state["largest_r"] else None
budget_pct = budget_worst / budget if budget else None
guard = state["guard"]
if guard["heartbeat_age_s"] > HEARTBEAT_S or guard["config_hash"] != guard["signed_config_hash"]:
    level = "black"
elif (budget_pct is not None and budget_pct < RED_PCT) or (
    distance_r is not None and distance_r < RED_R
):
    level = "red"
elif (budget_pct is not None and budget_pct < AMBER_PCT) or (
    distance_r is not None and distance_r < AMBER_R
):
    level = "amber"
else:
    level = "green"
print(
    json.dumps(
        {
            "at": state["at"],
            "cushion_usd": round(cushion, 2),
            "worst_case_usd": round(worst, 2),
            "budget_left_usd": round(budget_left, 2),
            "budget_worst_case_usd": round(budget_worst, 2),
            "budget_worst_case_pct": None if budget_pct is None else round(100 * budget_pct, 1),
            "distance_r": None if distance_r is None else round(distance_r, 2),
            "heartbeat_age_s": guard["heartbeat_age_s"],
            "config_hash_matches": guard["config_hash"] == guard["signed_config_hash"],
            "level": level,
        }
    )
)
