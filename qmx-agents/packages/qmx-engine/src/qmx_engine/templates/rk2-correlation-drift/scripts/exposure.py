"""Exposure, correlation and the drift rules (card R2 steps 1 to 3).

Positions become currency legs (EURUSD long = +EUR -USD) weighted by open risk in R. Unit daily R
over 60 days gives the correlation matrix; time in trade gives the overlap correlation; the matrix's
eigenvalues give the effective number of bets, (sum of eigenvalues)^2 / sum of their squares. A unit
with too little history is unknown, and unknown counts as fully correlated, the conservative choice.
The drift rules trip on any pair whose correlation moved more than 0.3 from its promotion baseline,
on effective bets down more than 25%, or on open risk in one currency above the guard's limit.
"""

import json
import sys
from itertools import combinations

DRIFT = 0.3
BETS_DROP = 0.25
MIN_DAYS = 20


def corr(a, b):
    n = min(len(a), len(b))
    if n < MIN_DAYS:
        return None
    a, b = a[-n:], b[-n:]
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b, strict=True))
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    return cov / (va * vb) ** 0.5 if va and vb else None


def eigenvalues(matrix, sweeps=60):
    """Jacobi rotation on the symmetric matrix; small books only."""
    a = [row[:] for row in matrix]
    size = len(a)
    for _ in range(sweeps):
        for p, q in combinations(range(size), 2):
            if abs(a[p][q]) < 1e-12:
                continue
            theta = (a[q][q] - a[p][p]) / (2 * a[p][q])
            t = (1 if theta >= 0 else -1) / (abs(theta) + (theta * theta + 1) ** 0.5)
            c = 1 / (t * t + 1) ** 0.5
            s = t * c
            for k in range(size):
                akp, akq = a[k][p], a[k][q]
                a[k][p], a[k][q] = c * akp - s * akq, s * akp + c * akq
            for k in range(size):
                apk, aqk = a[p][k], a[q][k]
                a[p][k], a[q][k] = c * apk - s * aqk, s * apk + c * aqk
    return [a[i][i] for i in range(size)]


book = json.load(sys.stdin)["in"]
units = book["units"]
legs = {}
for unit in units:
    for held in unit["open"]:
        base, quote = held["instrument"][:3], held["instrument"][3:]
        sign = 1 if held["side"] == "long" else -1
        legs[base] = legs.get(base, 0) + sign * held["risk_r"]
        legs[quote] = legs.get(quote, 0) - sign * held["risk_r"]
names = [u["unit"] for u in units]
matrix = [[1.0] * len(units) for _ in units]
pairs = []
for i, j in combinations(range(len(units)), 2):
    rho = corr(units[i]["daily_r"], units[j]["daily_r"])
    overlap = corr(units[i]["minutes_in_trade"], units[j]["minutes_in_trade"])
    used = 1.0 if rho is None else rho
    matrix[i][j] = matrix[j][i] = used
    base = book["baseline"].get(f"{names[i]}|{names[j]}")
    pairs.append(
        {
            "pair": [names[i], names[j]],
            "rho": None if rho is None else round(rho, 3),
            "overlap": None if overlap is None else round(overlap, 3),
            "baseline": base,
            "drift": None if base is None else round(used - base, 3),
        }
    )
values = eigenvalues(matrix) if units else []
bets = sum(values) ** 2 / sum(v * v for v in values) if values else 0
trips = [
    f"{p['pair'][0]} and {p['pair'][1]} correlation moved {p['drift']} from its baseline"
    for p in pairs
    if p["drift"] is not None and abs(p["drift"]) > DRIFT
]
baseline_bets = book.get("baseline_effective_bets")
if baseline_bets and bets < (1 - BETS_DROP) * baseline_bets:
    trips.append(f"effective bets fell to {bets:.2f} from {baseline_bets}")
limit = book["currency_limit_r"]
trips += [
    f"open risk in {c} is {abs(r):.2f} R, above the guard's {limit} R"
    for c, r in legs.items()
    if abs(r) > limit
]
print(
    json.dumps(
        {
            "at": book["at"],
            "currency_r": {c: round(r, 2) for c, r in sorted(legs.items())},
            "pairs": pairs,
            "effective_bets": round(bets, 2),
            "unknown_units": [u["unit"] for u in units if len(u["daily_r"]) < MIN_DAYS],
            "trips": trips,
        }
    )
)
