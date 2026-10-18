"""The combination study (card P1 steps 3 to 7), a simulation that changes nothing.

Correlation over the full period and inside the crisis windows; drawdown overlap (the share of days
two streams are both in drawdown). Each method in the list (default: equal weight, inverse
volatility, risk parity and hierarchical risk parity) combines the book with each candidate at each
rebalance frequency, weights from a trailing window, turnover charged at the cost rate. Stress: the
combined stream inside each crisis window, and a block bootstrap of its worst drawdown. Marginal
value: the book's Sharpe with the candidate minus without it, with a 90% block-bootstrap band. A
candidate whose band crosses zero is never called "adds to the book". Every method is labelled
"study only" until the risk session ratifies one.
"""

import json
import random
import sys
from itertools import combinations

BLOCK, DRAWS = 20, 500
WINDOW = 63
FREQUENCIES = {"monthly": 21, "quarterly": 63}


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def sd(xs):
    m = mean(xs)
    return (sum((x - m) ** 2 for x in xs) / max(1, len(xs) - 1)) ** 0.5


def corr(a, b):
    sa, sb = sd(a), sd(b)
    if not sa or not sb:
        return 0.0
    ma, mb = mean(a), mean(b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b, strict=True)) / ((len(a) - 1) * sa * sb)


def sharpe(xs):
    return mean(xs) / sd(xs) * 252**0.5 if sd(xs) else 0.0


def drawdown_days(xs):
    peak = total = 0.0
    flags = []
    for x in xs:
        total += x
        peak = max(peak, total)
        flags.append(total < peak)
    return flags


def worst_drawdown(xs):
    peak = total = worst = 0.0
    for x in xs:
        total += x
        peak = max(peak, total)
        worst = max(worst, peak - total)
    return worst


def inverse_vol(window):
    inv = [1 / s if (s := sd(w)) else 0.0 for w in window]
    total = sum(inv) or 1.0
    return [x / total for x in inv]


def risk_parity(window, steps=50):
    n = len(window)
    cov = [[corr(a, b) * sd(a) * sd(b) for b in window] for a in window]
    w = inverse_vol(window)
    for _ in range(steps):
        marginal = [sum(cov[i][j] * w[j] for j in range(n)) for i in range(n)]
        contrib = [w[i] * marginal[i] for i in range(n)]
        target = sum(contrib) / n
        w = [
            max(1e-9, w[i] * (target / contrib[i]) ** 0.5) if contrib[i] > 0 else w[i]
            for i in range(n)
        ]
        total = sum(w)
        w = [x / total for x in w]
    return w


def hrp(window):
    n = len(window)
    dist = {
        (i, j): ((1 - corr(window[i], window[j])) / 2) ** 0.5 for i, j in combinations(range(n), 2)
    }
    clusters = [[i] for i in range(n)]
    while len(clusters) > 1:
        a, b = min(
            combinations(range(len(clusters)), 2),
            key=lambda ab: min(
                dist[tuple(sorted((i, j)))] for i in clusters[ab[0]] for j in clusters[ab[1]]
            ),
        )
        clusters[a] = clusters[a] + clusters[b]
        del clusters[b]
    order, w = clusters[0], [1.0] * n
    parts = [order]
    while parts:
        part = parts.pop()
        if len(part) < 2:
            continue
        left, right = part[: len(part) // 2], part[len(part) // 2 :]
        variance = [
            sd([sum(window[i][t] for i in side) / len(side) for t in range(len(window[0]))]) ** 2
            for side in (left, right)
        ]
        alpha = 1 - variance[0] / sum(variance) if sum(variance) else 0.5
        for i in left:
            w[i] *= alpha
        for i in right:
            w[i] *= 1 - alpha
        parts += [left, right]
    total = sum(w)
    return [x / total for x in w]


METHODS = {
    "equal weight": lambda window: [1 / len(window)] * len(window),
    "inverse volatility": inverse_vol,
    "risk parity": risk_parity,
    "hierarchical risk parity": hrp,
}


def combined(streams, method, every, cost):
    days, out, weights = len(streams[0]), [], None
    for t in range(days):
        if t >= WINDOW and (weights is None or t % every == 0):
            new = METHODS[method]([s[t - WINDOW : t] for s in streams])
            turnover = sum(abs(a - b) for a, b in zip(new, weights or new, strict=True))
            weights = new
        else:
            turnover = 0.0
        w = weights or [1 / len(streams)] * len(streams)
        out.append(sum(wi * s[t] for wi, s in zip(w, streams, strict=True)) - turnover * cost)
    return out


def block_band(with_c, without_c):
    rng = random.Random(0)  # noqa: S311 - a seeded bootstrap, not a secret
    days, diffs = len(with_c), []
    for _ in range(DRAWS):
        picks = []
        while len(picks) < days:
            start = rng.randrange(0, max(1, days - BLOCK))
            picks += range(start, min(days, start + BLOCK))
        picks = picks[:days]
        diffs.append(sharpe([with_c[i] for i in picks]) - sharpe([without_c[i] for i in picks]))
    diffs.sort()
    return [round(diffs[int(0.05 * DRAWS)], 3), round(diffs[int(0.95 * DRAWS)], 3)]


study = json.load(sys.stdin)["in"]
book = [u["daily_r"] for u in study["book"]]
names = [u["unit"] for u in study["book"]]
book_line = [sum(day) / len(book) for day in zip(*book, strict=True)]
results = []
for cand in study["candidates"]:
    streams = [*book, cand["daily_r"]]
    in_stress = [i for w in study["crisis_windows"] for i in range(w["start"], w["end"])]
    row = {
        "candidate": cand["id"],
        "rho_with_book": round(corr(cand["daily_r"], book_line), 3),
        "rho_in_stress": round(
            corr([cand["daily_r"][i] for i in in_stress], [book_line[i] for i in in_stress]), 3
        )
        if len(in_stress) > 2
        else None,
        "drawdown_overlap": round(
            mean(
                [
                    a and b
                    for a, b in zip(
                        drawdown_days(cand["daily_r"]), drawdown_days(book_line), strict=True
                    )
                ]
            ),
            3,
        ),
        "methods": [],
    }
    for method in METHODS:
        for freq, every in FREQUENCIES.items():
            with_c = combined(streams, method, every, study["cost_per_turnover_r"])
            without_c = (
                combined(book, method, every, study["cost_per_turnover_r"])
                if len(book) > 1
                else book_line
            )
            band = block_band(with_c, without_c)
            row["methods"].append(
                {
                    "method": method,
                    "rebalance": freq,
                    "label": "study only",
                    "sharpe_with": round(sharpe(with_c), 3),
                    "sharpe_without": round(sharpe(without_c), 3),
                    "marginal_band": band,
                    "worst_drawdown_r": round(worst_drawdown(with_c), 2),
                    "verdict": "adds to the book" if band[0] > 0 else "not shown to add",
                }
            )
    results.append(row)
print(
    json.dumps(
        {
            "book": names,
            "pairs": [
                {"pair": [names[i], names[j]], "rho": round(corr(book[i], book[j]), 3)}
                for i, j in combinations(range(len(book)), 2)
            ],
            "candidates": results,
            "dropped": study["dropped"],
        }
    )
)
