"""The fair comparison (card D4 steps 7 and 8 and its gates). Its inputs, the runs and the `judge`
block's verdict over the variant set, are told apart by shape; the verdict is found by its key
inside the child's nested outputs.

A comparison only on identical windows and costs: a mixed set is refused, never compared. Each
variant's metrics, the correlation of every pair's daily returns, and the luck warning when the
best variant's edge over the median Sharpe is inside the bootstrap spread. A failed variant is
shown as failed and still counted as a trial.
"""

import json
import sys
from statistics import correlation, median


def judged(value):
    if isinstance(value, dict):
        if isinstance(value.get("verdict"), dict):
            return value["verdict"]
        value = list(value.values())
    if isinstance(value, list):
        return next((found for v in value if (found := judged(v)) is not None), None)
    return None


given = json.load(sys.stdin)["in"]
ran = next(v for v in given if "runs" in v)
verdict = judged([v for v in given if v is not ran])
done = [r for r in ran["runs"] if not r.get("failed")]
failed = [{"variant": r["variant"], "why": r["failed"]} for r in ran["runs"] if r.get("failed")]
mixed = len({json.dumps([r["windows"], r["costs"]], sort_keys=True) for r in done}) > 1
if mixed or len(done) < 2:
    why = "the variants do not share windows and costs" if mixed else "fewer than 2 variants ran"
    print(
        json.dumps(
            {
                "refused": why,
                "cards": [],
                "correlations": [],
                "failed": failed,
                "luck_warning": None,
                "judge": verdict,
                "trials": len(ran["runs"]),
            }
        )
    )
    raise SystemExit(0)
cards = [
    {
        k: r[k]
        for k in ("variant", "sharpe", "expectancy_r", "max_drawdown_r", "trades", "equity_ref")
    }
    for r in sorted(done, key=lambda r: -r["sharpe"])
]
correlations = [
    {
        "pair": [a["variant"], b["variant"]],
        "correlation": round(correlation(a["daily_returns"], b["daily_returns"]), 2),
    }
    for i, a in enumerate(done)
    for b in done[i + 1 :]
]
edge = round(cards[0]["sharpe"] - median(r["sharpe"] for r in done), 3)
low, high = ran["bootstrap_spread"]
luck = (
    f"the best edge over the median, {edge}, is inside the bootstrap spread {low} to {high}"
    if low <= edge <= high
    else None
)
print(
    json.dumps(
        {
            "refused": None,
            "cards": cards,
            "correlations": correlations,
            "edge_over_median": edge,
            "failed": failed,
            "luck_warning": luck,
            "judge": verdict,
            "trials": len(ran["runs"]),
        }
    )
)
