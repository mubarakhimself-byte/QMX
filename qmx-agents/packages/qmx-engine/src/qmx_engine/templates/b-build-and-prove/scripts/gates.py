"""The overfit gates of funnel stage 10 (card D3's robustness set). Every gate is a script; no
model grades a result.

At least 100 trades in-sample; walk-forward efficiency (validation Sharpe over in-sample Sharpe)
at least 0.5; the Monte Carlo 5th percentile of total R above zero; expectancy still positive at
1.5x costs; the deflated Sharpe over the whole family at least 0.95. A daily Sharpe above 2 holds
the verdict for a lookahead audit. Its inputs, the QMB results and the deflated Sharpe, are told
apart by shape.
"""

import json
import sys

MIN_TRADES = 100
MIN_EFFICIENCY = 0.5
LOOKAHEAD_DAILY_SHARPE = 2

given = json.load(sys.stdin)["in"]
results = next(v for v in given if "in_sample" in v)
deflated = next(v for v in given if "deflated_sharpe" in v)["deflated_sharpe"]
in_sample, walk_forward = results["in_sample"], results["walk_forward"]
efficiency = walk_forward["sharpe"] / in_sample["sharpe"] if in_sample["sharpe"] > 0 else 0.0
gates = [
    {
        "gate": "trades",
        "value": results["trades"],
        "bar": MIN_TRADES,
        "passes": results["trades"] >= MIN_TRADES,
    },
    {
        "gate": "walk-forward efficiency",
        "value": round(efficiency, 2),
        "bar": MIN_EFFICIENCY,
        "passes": efficiency >= MIN_EFFICIENCY,
    },
    {
        "gate": "Monte Carlo 5th percentile R",
        "value": results["monte_carlo"]["p05_r"],
        "bar": 0,
        "passes": results["monte_carlo"]["p05_r"] > 0,
    },
    {
        "gate": "expectancy at 1.5x costs R",
        "value": results["cost_stress"]["expectancy_r"],
        "bar": 0,
        "passes": results["cost_stress"]["expectancy_r"] > 0,
    },
    {
        "gate": "deflated Sharpe",
        "value": deflated["probability"],
        "bar": 0.95,
        "passes": deflated["passes"],
    },
]
lookahead = in_sample["daily_sharpe"] > LOOKAHEAD_DAILY_SHARPE
failed = [g["gate"] for g in gates if not g["passes"]]
if lookahead:
    verdict = "held for a lookahead audit"
elif failed:
    verdict = "dies"
else:
    verdict = "survives"
print(
    json.dumps(
        {
            "verdict": verdict,
            "survives": verdict == "survives",
            "gates": gates,
            "failed": failed,
            "lookahead_audit": lookahead,
            "trials": deflated["trials"],
        }
    )
)
