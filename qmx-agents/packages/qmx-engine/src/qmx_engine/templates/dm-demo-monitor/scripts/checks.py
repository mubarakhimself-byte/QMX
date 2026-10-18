"""Behaviour faults, the band verdict and the cost rules (card T5 step 3, card T9 step 3).

A fault is a trade outside the unit's sessions or inside a blackout, a size more than 10% off the
expected risk, a missing stop, a duplicate order, or a spread at entry above the unit's own maximum.
Costs are amber above 1.25 times the assumed cost over the last 50 trades, red above 1.5, or on any
slippage worse than 0.5R. On demo, a drawdown of 8R or more, or two faults in one day, makes a bench
proposal: tighten-only, demo only, and only his click benches the unit. Nothing here acts.
"""

import json
import sys

SIZE_TOLERANCE = 0.10
COST_AMBER, COST_RED, SLIPPAGE_RED_R = 1.25, 1.5, 0.5
BENCH_DRAWDOWN_R, BENCH_FAULTS = 8, 2


def inside(clock, windows):
    return any(start <= clock < end for start, end in windows)


def faults(unit):
    found, seen = [], set()
    for deal in unit["deals"]:
        clock, day = deal["opened_at"][11:16], deal["opened_at"][:10]
        expected = unit["expected_r_usd"]
        problems = [
            (not inside(clock, unit["sessions"]), "outside sessions"),
            (inside(clock, unit["blackouts"]), "in a blackout"),
            (abs(deal["size_r_usd"] - expected) > SIZE_TOLERANCE * expected, "size off by >10%"),
            (deal["stop"] is None, "no stop"),
            (deal["spread_pips"] > unit["max_spread_pips"], "spread above its maximum"),
            ((deal["opened_at"], deal["size_r_usd"]) in seen, "duplicate order"),
        ]
        found += [{"deal": deal["id"], "day": day, "fault": what} for hit, what in problems if hit]
        seen.add((deal["opened_at"], deal["size_r_usd"]))
    return found


state = json.load(sys.stdin)["in"]
units, out_of_band = [], []
for unit in state["units"]:
    found = faults(unit)
    today = [f for f in found if f["day"] == unit["today"]]
    ratio = unit["cost_ratio"]
    if (ratio is not None and ratio > COST_RED) or unit["worst_slippage_r"] > SLIPPAGE_RED_R:
        cost_level = "red"
    elif ratio is not None and ratio > COST_AMBER:
        cost_level = "amber"
    else:
        cost_level = "green"
    bench = unit["drawdown_r"] >= BENCH_DRAWDOWN_R or len(today) >= BENCH_FAULTS
    if unit["band"]["verdict"] == "out":
        out_of_band.append(unit["unit"])
    units.append(
        {k: v for k, v in unit.items() if k != "deals"}
        | {
            "faults": found,
            "cost_level": cost_level,
            "bench_proposal": "bench on demo, tighten-only: his click" if bench else None,
        }
    )
print(json.dumps({"at": state["at"], "units": units, "out_of_band": out_of_band}))
