"""Running stats per demo unit (card T5 step 2, card T9 step 2): trades, expectancy in R with a 90%
bootstrap interval, win rate, average win and loss in R, drawdown in R, trades per day, cumulative R
against the backtest's Monte Carlo 5-95% band, and the execution costs: worst slippage in R, median
fill latency, and the cost ratio (real cost per trade in R over the assumed cost in R) over the last
50 trades."""

import json
import random
import sys

DRAWS = 2000
COST_WINDOW = 50


def interval(values):
    if len(values) < 2:
        return None
    rng = random.Random(0)  # noqa: S311 - a seeded bootstrap, not a secret
    means = sorted(sum(rng.choices(values, k=len(values))) / len(values) for _ in range(DRAWS))
    return [round(means[int(0.05 * DRAWS)], 3), round(means[int(0.95 * DRAWS)], 3)]


def drawdown(values):
    peak = total = worst = 0.0
    for value in values:
        total += value
        peak = max(peak, total)
        worst = max(worst, peak - total)
    return worst


state = json.load(sys.stdin)["in"]["value"]
units = []
for unit in state["units"]:
    deals = sorted(unit["deals"], key=lambda d: d["closed_at"])
    r = [d["r"] for d in deals]
    wins, losses = [x for x in r if x > 0], [x for x in r if x <= 0]
    days = sorted({d["closed_at"][:10] for d in deals})
    n = len(r)
    band = unit["mc_band"]
    cum = round(sum(r), 2)
    low = band["p05"][n - 1] if 0 < n <= len(band["p05"]) else None
    high = band["p95"][n - 1] if 0 < n <= len(band["p95"]) else None
    verdict = "unknown" if low is None else "in" if low <= cum <= high else "out"
    recent = deals[-COST_WINDOW:]
    cost = sum(d["cost_r"] for d in recent) / len(recent) if recent else None
    latencies = sorted(d["latency_ms"] for d in deals)
    units.append(
        unit
        | {
            "n": n,
            "expectancy_r": round(sum(r) / n, 3) if n else None,
            "expectancy_ci_r": interval(r),
            "win_rate": round(len(wins) / n, 3) if n else None,
            "avg_win_r": round(sum(wins) / len(wins), 3) if wins else None,
            "avg_loss_r": round(sum(losses) / len(losses), 3) if losses else None,
            "drawdown_r": round(drawdown(r), 2),
            "trades_per_day": round(n / len(days), 2) if days else 0,
            "cum_r": cum,
            "band": {"p05": low, "p95": high, "verdict": verdict},
            "cost_ratio": None if cost is None else round(cost / unit["assumed_cost_r"], 2),
            "worst_slippage_r": max(
                (d["slippage_pips"] * d["pip_value_r"] for d in deals), default=0
            ),
            "median_latency_ms": latencies[n // 2] if n else None,
            "today": days[-1] if days else state["at"][:10],
        }
    )
print(json.dumps({"at": state["at"], "units": units}))
