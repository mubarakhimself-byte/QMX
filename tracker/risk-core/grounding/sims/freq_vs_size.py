"""Bigger bets vs more bets, on a $500 seed with a kill line at $300.

Each scenario spends the same total risk per day (risk % x trades a day),
so the only difference is how it is cut: few big bets or many small ones.
Every trade's edge is net of costs. "Half edge" is the case where the live
edge turns out to be half of what paper trading measured.

Run: python freq_vs_size.py
"""
import numpy as np

SEED, KILL, DAYS, PATHS = 500.0, 300.0, 60, 20000
rng = np.random.default_rng(7)


def run(risk, per_day, p_win, win_r, loss_r=1.0):
    n = DAYS * per_day
    wins = rng.random((PATHS, n)) < p_win
    step = np.where(wins, risk * win_r, -risk * loss_r)
    eq = SEED * np.cumprod(1.0 + step, axis=1)
    touched = (eq.min(axis=1) <= KILL)
    # a touched path stops at the kill line
    end = np.where(touched, KILL, eq[:, -1])
    return touched.mean(), np.median(end), (end >= 2 * SEED).mean()


def growth_per_day(risk, per_day, p_win, win_r, loss_r=1.0):
    ev = p_win * win_r - (1 - p_win) * loss_r
    var = p_win * win_r**2 + (1 - p_win) * loss_r**2 - ev**2
    return per_day * (risk * ev - risk**2 * var / 2)


def table(title, rows, p_win, win_r):
    print(f"\n{title}")
    print(f"{'scenario':34s} {'touch $300':>10s} {'median end':>11s} {'doubled':>8s} {'growth/day':>11s}")
    for name, risk, per_day in rows:
        t, m, d = run(risk, per_day, p_win, win_r)
        g = growth_per_day(risk, per_day, p_win, win_r)
        print(f"{name:34s} {t:10.0%} {m:11.0f} {d:8.0%} {g:11.2%}")


SCALP = [
    ("Hit hard: 8% x 2 trades/day", 0.08, 2),
    ("Middle: 2% x 8 trades/day", 0.02, 8),
    ("Hummingbird: 1% x 16 trades/day", 0.01, 16),
    ("Hummingbird: 0.5% x 32 trades/day", 0.005, 32),
]
table("Scalper-like edge, 55% wins at 1:1 (+0.10R a trade), 60 days", SCALP, 0.55, 1.0)
table("Same, but the live edge is half (52.5% wins, +0.05R)", SCALP, 0.525, 1.0)

ORB = [
    ("ORB 8% x 1 trade/day", 0.08, 1),
    ("ORB 4% x 1 trade/day", 0.04, 1),
    ("ORB 2% x 1 trade/day", 0.02, 1),
]
table("Breakout-like edge, 40% wins at 2:1 (+0.20R a trade), 60 days", ORB, 0.40, 2.0)
table("Same, but half edge (36.7% wins, +0.10R)", ORB, 0.3667, 2.0)

# Longest losing run in 60 one-a-day breakout trades at 60% losses
runs = []
for _ in range(PATHS):
    w = rng.random(60) < 0.40
    best = cur = 0
    for x in w:
        cur = 0 if x else cur + 1
        best = max(best, cur)
    runs.append(best)
runs = np.array(runs)
print("\nORB, 60 trades at 40% wins: chance the longest losing run is at least")
for k in (5, 6, 7, 8):
    print(f"  {k} in a row: {np.mean(runs >= k):.0%}   (at 8% each that run costs {1 - 0.92**k:.0%})")
