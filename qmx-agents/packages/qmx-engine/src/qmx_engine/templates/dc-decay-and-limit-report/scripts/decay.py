"""The decay tests and the red, amber, green rule per unit (card R3 steps 2 and 3, card P3 steps 1
to 4). The definition of decay is pluggable: these are the defaults until the risk session settles
it.

Tests: a downside CUSUM of (expected R - R) with k = 0.5 sd and h = 5 sd; the last 50 trades'
expectancy with a 90% bootstrap interval wholly below the expected R; cumulative R below the Monte
Carlo 5% line; a one-sided binomial test on the win rate (z below -1.645); the payoff ratio below
75% of the backtest's; the trade count off its Poisson expectation (|z| above 1.96); and the cost
ratio above 1.25. Red needs a CUSUM breach, two or more failed tests, or the term sheet's kill
criterion, which avoids small-sample false alarms. Amber is one failed test, the last 10 trades all
outside the band, or a limit at 80% of its budget. Missing data reads "could not check", never
green.
"""

import json
import random
import sys

K_SD, H_SD = 0.5, 5
WINDOW, DRAWS = 50, 2000
Z_ONE, Z_TWO = 1.645, 1.96
PAYOFF_FLOOR, COST_CEILING, LIMIT_WARN = 0.75, 1.25, 0.8
BAND_RUN = 10


def cusum(r, expected, sd):
    total = 0.0
    for value in r:
        total = max(0.0, total + (expected - value) - K_SD * sd)
        if total > H_SD * sd:
            return True
    return False


def below(r, expected):
    recent = r[-WINDOW:]
    if len(recent) < 2:
        return False
    rng = random.Random(0)  # noqa: S311 - a seeded bootstrap, not a secret
    means = sorted(sum(rng.choices(recent, k=len(recent))) / len(recent) for _ in range(DRAWS))
    return means[int(0.95 * DRAWS)] < expected


def tests(unit):
    r = [t["r"] for t in unit["trades"]]
    n, base = len(r), unit["baseline"]
    wins = [x for x in r if x > 0]
    losses = [-x for x in r if x <= 0]
    p = base["win_rate"]
    z_win = (len(wins) - n * p) / (n * p * (1 - p)) ** 0.5 if n else 0
    payoff = (sum(wins) / len(wins)) / (sum(losses) / len(losses)) if wins and losses else None
    expected_count = base["trades_per_day"] * unit["days"]
    z_count = (n - expected_count) / expected_count**0.5 if expected_count else 0
    cum, p05 = sum(r), unit["band"]["p05"]
    cost = sum(t["cost_r"] for t in unit["trades"][-WINDOW:]) / max(1, min(n, WINDOW))
    return {
        "cusum_breach": cusum(r, base["expected_r"], base["sd_r"]),
        "expectancy_below": below(r, base["expected_r"]),
        "below_band": n <= len(p05) and n > 0 and cum < p05[n - 1],
        "win_rate_low": z_win < -Z_ONE,
        "payoff_drift": payoff is not None and payoff < PAYOFF_FLOOR * base["payoff_ratio"],
        "frequency_drift": abs(z_count) > Z_TWO,
        "cost_drift": cost / unit["assumed_cost_r"] > COST_CEILING,
    }


journal = json.load(sys.stdin)["in"]
units, flagged = [], []
for unit in journal["units"]:
    if not unit.get("trades") or not unit.get("baseline"):
        units.append({"unit": unit["unit"], "level": "could not check", "failed": []})
        continue
    found = tests(unit)
    failed = [name for name, hit in found.items() if hit and name != "cusum_breach"]
    r = [t["r"] for t in unit["trades"]]
    peak = total = drawdown = 0.0
    for value in r:
        total += value
        peak = max(peak, total)
        drawdown = max(drawdown, peak - total)
    killed = drawdown >= unit["kill_drawdown_r"]
    p05 = unit["band"]["p05"]
    run = [
        sum(r[: i + 1]) < p05[i] for i in range(max(0, len(r) - BAND_RUN), min(len(r), len(p05)))
    ]
    limit_use = unit["limit_used_r"] / unit["limit_r"] if unit["limit_r"] else 0
    if found["cusum_breach"] or len(failed) >= 2 or killed:
        level = "red"
    elif failed or (len(run) == BAND_RUN and all(run)) or limit_use >= LIMIT_WARN:
        level = "amber"
    else:
        level = "green"
    if level in ("red", "amber"):
        flagged.append(unit["unit"])
    units.append(
        {
            "unit": unit["unit"],
            "level": level,
            "cusum_breach": found["cusum_breach"],
            "failed": failed,
            "kill_criterion_hit": killed,
            "drawdown_r": round(drawdown, 2),
            "cum_r": round(sum(r), 2),
            "trades": len(r),
            "limit_use_pct": round(100 * limit_use, 1),
        }
    )
print(json.dumps({"at": journal["at"], "units": units, "flagged": flagged}))
