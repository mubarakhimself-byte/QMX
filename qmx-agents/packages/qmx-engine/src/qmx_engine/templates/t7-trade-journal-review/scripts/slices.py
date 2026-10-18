"""Stats by slice and the significance filter (card T7 steps 2 and 3).

Each slice (session, setup, MIS state, and session x setup) gets n, expectancy in R and a 90%
bootstrap interval. A slice is reported only when n >= 20 and its interval excludes the overall
mean, so noise is never a finding. Also: the R-multiple histogram, exit efficiency (captured R over
MFE), the stop-hunt count (MAE just past the stop, then the trade would have reached its target),
the longest losing streak, rule breaks, and manual trades in their own lane.
"""

import json
import random
import sys
from collections import defaultdict

MIN_N = 20
DRAWS = 2000
STOP_HUNT_MAE = (1.0, 1.2)


def interval(values):
    rng = random.Random(0)  # noqa: S311 - a seeded bootstrap, not a secret
    means = sorted(sum(rng.choices(values, k=len(values))) / len(values) for _ in range(DRAWS))
    return round(means[int(0.05 * DRAWS)], 3), round(means[int(0.95 * DRAWS)], 3)


journal = json.load(sys.stdin)["in"]
trades = [t for t in journal["trades"] if not t["manual"]]
overall = sum(t["r"] for t in trades) / len(trades)
groups = defaultdict(list)
for trade in trades:
    for key in ("session", "setup", "mis_state"):
        groups[f"{key}={trade[key]}"].append(trade["r"])
    groups[f"session={trade['session']} x setup={trade['setup']}"].append(trade["r"])
significant = []
for name, values in sorted(groups.items()):
    if len(values) < MIN_N:
        continue
    low, high = interval(values)
    if high < overall or low > overall:
        significant.append(
            {
                "slice": name,
                "n": len(values),
                "expectancy_r": round(sum(values) / len(values), 3),
                "ci_r": [low, high],
            }
        )
histogram = defaultdict(int)
for trade in trades:
    histogram[str(max(-3, min(3, round(trade["r"]))))] += 1
captured = [t["r"] / t["mfe_r"] for t in trades if t["mfe_r"] > 0]
streak = longest = 0
for trade in trades:
    streak = streak + 1 if trade["r"] < 0 else 0
    longest = max(longest, streak)
print(
    json.dumps(
        {
            "trades": len(trades),
            "overall_expectancy_r": round(overall, 3),
            "significant": significant,
            "histogram_r": dict(sorted(histogram.items(), key=lambda kv: int(kv[0]))),
            "exit_efficiency": round(sum(captured) / len(captured), 3) if captured else None,
            "stop_hunts": sum(
                STOP_HUNT_MAE[0] <= t["mae_r"] <= STOP_HUNT_MAE[1] and t["r"] < 0 for t in trades
            ),
            "longest_losing_streak": longest,
            "rule_breaks": [t["id"] for t in trades if t["rule_break"]],
            "manual": [{"id": t["id"], "r": t["r"]} for t in journal["trades"] if t["manual"]],
        }
    )
)
