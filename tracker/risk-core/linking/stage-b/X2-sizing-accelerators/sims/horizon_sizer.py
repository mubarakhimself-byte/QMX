"""X2 stage B check: does a horizon floor-odds sizer hold the floor when the edge is wrong,
and what does it give up against edge-led and split sizing?

Model (model numbers, not evidence about real strategies):
- $500 seed, $300 floor (cushion D = $200 at start), 60 trading days, 10 trades a day per unit.
- Trades: win +1R; a loser is a fast-invalidation cut at -0.35R half the time, else a full -1R stop.
- Believed edge +0.08R per trade; tested at believed, half (+0.04R) and zero edge.
- N units (1 or 10). Units' wins share a common factor per trade slot with loading rho (0 or 0.3).
- Size is set at each day start from that morning's equity or cushion, and held for the day.

Policies (risk in dollars per trade per unit):
  fixed_1pct      1 % of equity
  split_1pct      1 % of equity / N (the literal day-budget split)
  half_kelly      0.5 x EV / var of equity, on the believed point edge (edge-led)
  gitbook_ladder  cushion / 7 per trade, day door shuts after cushion / 5 lost (July ladder shape)
  horizon_zero    cushion / (s x z x sqrt(H x N_eff)): survival over H rounds at zero edge
  horizon_half    largest r with P(book touches floor within H rounds) <= eps at half the believed edge

Run: uv run --no-project --with numpy python -I horizon_sizer.py [paths] [gap_day_prob] [gap_R]
Outputs kept beside this file: out-1000.txt (no gaps), out-1000-gaps.txt (2 % of days, -3R shared gap).
"""
import math
import sys

import numpy as np

SEED, FLOOR, DAYS, TPD = 500.0, 300.0, 60, 10
CUT, FI_SHARE = 0.35, 0.5
EV_BELIEVED = 0.08
EPS, H_ROUNDS, RHO_PLAN = 0.01, 200, 0.3
GAP_DAY_PROB = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
GAP_R = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
Z = 2.5758  # Phi^-1(1 - eps/2) for eps = 1 %


def win_prob(ev):
    loss = FI_SHARE * CUT + (1 - FI_SHARE) * 1.0
    return (ev + loss) / (1.0 + loss)


def trade_moments(ev):
    p = win_prob(ev)
    m2 = p + (1 - p) * (FI_SHARE * CUT**2 + (1 - FI_SHARE))
    return ev, math.sqrt(m2 - ev**2)


def ncdf(x):
    """Standard normal cdf (Abramowitz-Stegun 7.1.26 erf, error below 1.5e-7)."""
    x = np.asarray(x, dtype=float)
    y = np.abs(x) / math.sqrt(2.0)
    t = 1.0 / (1.0 + 0.3275911 * y)
    poly = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))))
    erf = 1.0 - poly * np.exp(-y * y)
    return 0.5 * (1.0 + np.sign(x) * erf)


def touch_prob(d, r, mu_t, sig_t, rounds):
    """Brownian first-passage probability of falling by d within `rounds` steps."""
    mu, sig = mu_t * r, sig_t * r
    T = rounds
    a = (-d - mu * T) / (sig * math.sqrt(T))
    b = (-d + mu * T) / (sig * math.sqrt(T))
    expo = np.exp(np.clip(-2.0 * mu * d / sig**2, -700, 50))
    return ncdf(a) + expo * ncdf(b)


def horizon_half_r(d, n, rho):
    ev_plan, s = trade_moments(EV_BELIEVED / 2)
    n_eff = n / (1 + (n - 1) * RHO_PLAN)
    mu_t = n * ev_plan            # book drift per round, per dollar of r
    sig_t = s * n / math.sqrt(n_eff)  # book sigma per round, per dollar of r
    lo, hi = np.zeros_like(d), d.copy()
    for _ in range(40):
        mid = (lo + hi) / 2
        ok = touch_prob(d, np.maximum(mid, 1e-9), mu_t, sig_t, H_ROUNDS) <= EPS
        lo = np.where(ok, mid, lo)
        hi = np.where(ok, hi, mid)
    return lo


def simulate(n, rho, ev_true, paths, rng):
    p = win_prob(ev_true)
    f = rng.standard_normal((paths, DAYS, TPD, 1))
    e = rng.standard_normal((paths, DAYS, TPD, n))
    z = math.sqrt(rho) * f + math.sqrt(1 - rho) * e
    u = ncdf(z)
    win = u < p
    cut = rng.random((paths, DAYS, TPD, n)) < FI_SHARE
    R = np.where(win, 1.0, np.where(cut, -CUT, -1.0))
    if GAP_DAY_PROB > 0:
        # a shared gap day: every unit's first trade of the day gaps through its stop together
        gap_day = rng.random((paths, DAYS)) < GAP_DAY_PROB
        R[:, :, 0, :] = np.where(gap_day[:, :, None], -GAP_R, R[:, :, 0, :])
    return R


def run_policy(name, R, n, rho):
    paths = R.shape[0]
    eq = np.full(paths, SEED)
    touched = np.zeros(paths, bool)
    breached = np.zeros(paths, bool)
    risk_used = []
    _, s_b = trade_moments(EV_BELIEVED)
    ev_b, _ = trade_moments(EV_BELIEVED)
    var_b = s_b**2 + 0.0
    n_eff_plan = n / (1 + (n - 1) * RHO_PLAN)
    for day in range(DAYS):
        cushion = np.maximum(eq - FLOOR, 0.0)
        if name == "fixed_1pct":
            r = 0.01 * eq
        elif name == "split_1pct":
            r = 0.01 * eq / n
        elif name == "half_kelly":
            r = 0.5 * ev_b / var_b * eq
        elif name == "gitbook_ladder":
            r = cushion / 7.0
        elif name == "horizon_zero":
            # book sigma per round = s * r * sqrt(n * (1 + (n-1) rho)) = s * r * n / sqrt(n_eff)
            r = cushion / (s_b * Z * math.sqrt(H_ROUNDS) * n / math.sqrt(n_eff_plan))
        elif name == "horizon_half":
            r = horizon_half_r(cushion, n, rho)
        else:
            raise ValueError(name)
        r = np.where(touched, 0.0, r)
        risk_used.append(np.mean(r / np.maximum(eq, 1e-9)))
        day_pnl = np.zeros(paths)
        door_open = np.ones(paths, bool)
        for t in range(TPD):
            step = (R[:, day, t, :].sum(axis=1)) * r * door_open
            day_pnl += step
            cur = eq + day_pnl
            touched |= cur <= FLOOR
            breached |= cur <= 400.0
            if name == "gitbook_ladder":
                door_open &= day_pnl > -(cushion / 5.0)
        eq = np.where(touched, np.minimum(eq + day_pnl, FLOOR), eq + day_pnl)
    return {
        "touch": touched.mean(),
        "below400": breached.mean(),
        "median": float(np.median(eq)),
        "p10": float(np.percentile(eq, 10)),
        "risk_pct": 100 * float(np.mean(risk_used)),
    }


def main():
    paths = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    rng = np.random.default_rng(7)
    policies = ["fixed_1pct", "split_1pct", "half_kelly", "gitbook_ladder", "horizon_zero", "horizon_half"]
    print(f"paths={paths} days={DAYS} trades/day/unit={TPD} FI cut={CUT}R on {int(FI_SHARE*100)}% of losers")
    print(f"believed edge={EV_BELIEVED}R, eps={EPS}, H={H_ROUNDS} rounds, rho_plan={RHO_PLAN}")
    print(f"shared gap day probability={GAP_DAY_PROB}, gap loss={GAP_R}R on every unit at once")
    for n in (1, 10):
        for rho in (0.0, 0.3):
            for label, ev in (("believed", EV_BELIEVED), ("half", EV_BELIEVED / 2), ("zero", 0.0)):
                R = simulate(n, rho, ev, paths, rng)
                print(f"\nN={n} rho={rho} edge={label} ({ev:+.2f}R)")
                print(f"  {'policy':<15} {'touch':>6} {'<$400':>6} {'median':>9} {'p10':>8} {'avg risk/eq':>11}")
                for name in policies:
                    m = run_policy(name, R, n, rho)
                    print(f"  {name:<15} {m['touch']*100:5.1f}% {m['below400']*100:5.1f}% {m['median']:9.0f} {m['p10']:8.0f} {m['risk_pct']:10.2f}%")


if __name__ == "__main__":
    main()
