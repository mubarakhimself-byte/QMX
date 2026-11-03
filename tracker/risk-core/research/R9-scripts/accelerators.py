"""R9 arithmetic: do accelerators pay, and how do count and money brakes behave?

Standard library only. Run:  python -I accelerators.py [paths]
All results are model arithmetic, not evidence about real strategies.

Part 1. Sizing policies on the same simulated trade streams (common random numbers).
  Trades pay +1R or -1R (costs already netted into the win rate).
  10 trades a day, 250 days, base risk f = 0.5 % of current equity per trade.
  Scenarios:
    iid-thin   : independent trades, win rate 52.5 % (edge +0.05R)
    iid-55     : independent trades, win rate 55 %   (edge +0.10R)
    regime-fast: hidden good/bad state, 60 % / 45 % wins, stay prob 0.98 per trade
                 (mean run 50 trades = 5 days); long-run win rate 52.5 %
    regime-slow: same, stay prob 0.998 per trade (mean run 500 trades = 50 days)
  Policies (risk multiplier on f):
    const-0.8, const-1.0, const-1.25, const-1.5 : fixed fraction (references)
    hm-step     : old house money, 1.5x once day P&L >= +0.5 % of day-start equity
    rhm-streak  : old reverse house money, 1.0 / 0.7 / 0.5 at <2, 2-3, 4+ losses in a row (per day)
    hm+rhm-old  : both old multipliers, multiplied
    cushion-day : size x (L + dayPnL) / L with L = 2 % day loss limit, clamp 0..2, stop at -L
                  (house money and its mirror on one ledger)
    ec-flip     : last-50-trade sum > 0 -> 1.5x, else 0.5x (equity-curve pair, no dead band)
    ec-band     : > +5R -> 1.5x, < -5R -> 0.5x, else 1.0x (with a dead band)
    aimd-day    : multiplier x0.7 after a day <= -1.5 %, +0.05 after a green day, 0.25..2.0

Part 2. Count brakes against money brakes, with fast-invalidation cuts and scratches.
"""
import math
import random
import sys

DAYS, TPD, F = 250, 10, 0.005


def gen_outcomes(rng, scen, n):
    if scen == "iid-thin":
        return [1 if rng.random() < 0.525 else -1 for _ in range(n)]
    if scen == "iid-55":
        return [1 if rng.random() < 0.55 else -1 for _ in range(n)]
    stay = 0.98 if scen == "regime-fast" else 0.998
    good = rng.random() < 0.5
    out = []
    for _ in range(n):
        if rng.random() > stay:
            good = not good
        p = 0.60 if good else 0.45
        out.append(1 if rng.random() < p else -1)
    return out


POLICIES = ["const-0.8", "const-1.0", "const-1.25", "const-1.5", "hm-step", "rhm-streak", "hm+rhm-old",
            "cushion-day", "ec-flip", "ec-band", "aimd-day"]


def run_path(outs, pol):
    eq, peak, maxdd = 1.0, 1.0, 0.0
    risk_sum, n_tr = 0.0, 0
    hist = []  # last 50 outcomes in R
    s50 = 0
    aimd = 1.0
    i = 0
    for _d in range(DAYS):
        day_start = eq
        streak = 0
        stopped = False
        for _t in range(TPD):
            o = outs[i]
            i += 1
            day_frac = eq / day_start - 1.0
            m = 1.0
            if pol == "const-0.8":
                m = 0.8
            elif pol == "const-1.25":
                m = 1.25
            elif pol == "const-1.5":
                m = 1.5
            elif pol in ("hm-step", "hm+rhm-old"):
                m = 1.5 if day_frac >= 0.005 else 1.0
            if pol in ("rhm-streak", "hm+rhm-old"):
                m *= 1.0 if streak < 2 else (0.7 if streak < 4 else 0.5)
            if pol == "cushion-day":
                L = 0.02
                if stopped or day_frac <= -L:
                    stopped = True
                    m = 0.0
                else:
                    m = max(0.0, min(2.0, (L + day_frac) / L))
            if pol == "ec-flip":
                m = 1.5 if (len(hist) >= 50 and s50 > 0) else (0.5 if len(hist) >= 50 else 1.0)
            if pol == "ec-band":
                if len(hist) >= 50 and s50 > 5:
                    m = 1.5
                elif len(hist) >= 50 and s50 < -5:
                    m = 0.5
                else:
                    m = 1.0
            if pol == "aimd-day":
                m = aimd
            r = F * m
            if r > 0:
                risk_sum += m
                n_tr += 1
            eq *= (1.0 + r * o)
            if eq > peak:
                peak = eq
            dd = 1.0 - eq / peak
            if dd > maxdd:
                maxdd = dd
            streak = 0 if o > 0 else streak + 1
            hist.append(o)
            s50 += o
            if len(hist) > 50:
                s50 -= hist.pop(0)
        if pol == "aimd-day":
            dr = eq / day_start - 1.0
            if dr <= -0.015:
                aimd = max(0.25, aimd * 0.7)
            elif dr > 0:
                aimd = min(2.0, aimd + 0.05)
    avg_m = risk_sum / max(1, n_tr)
    return math.log(eq), maxdd, avg_m


def part1(paths):
    print("PART 1: sizing policies, %d paths x %d trades" % (paths, DAYS * TPD))
    for scen in ["iid-thin", "iid-55", "regime-fast", "regime-slow"]:
        rng = random.Random(9 + len(scen))
        res = {p: [] for p in POLICIES}
        ac_num = ac_den = 0.0
        for _ in range(paths):
            outs = gen_outcomes(rng, scen, DAYS * TPD)
            mu = sum(outs) / len(outs)
            ac_num += sum((outs[k] - mu) * (outs[k - 1] - mu) for k in range(1, len(outs)))
            ac_den += sum((x - mu) ** 2 for x in outs)
            for p in POLICIES:
                res[p].append(run_path(outs, p))
        print("\nscenario %s   lag-1 autocorrelation of trade outcomes = %.4f" % (scen, ac_num / ac_den))
        print("%-12s %9s %9s %9s %9s %9s %11s" % ("policy", "meanLogG", "medianX", "P(DD>15%)",
                                                   "P(DD>25%)", "avgRisk", "logG/avgRisk"))
        for p in POLICIES:
            lg = sorted(x[0] for x in res[p])
            dd = [x[1] for x in res[p]]
            am = sum(x[2] for x in res[p]) / paths
            mlg = sum(lg) / paths
            print("%-12s %9.3f %9.2f %9.3f %9.3f %9.2f %11.3f" % (
                p, mlg, math.exp(lg[paths // 2]), sum(d > 0.15 for d in dd) / paths,
                sum(d > 0.25 for d in dd) / paths, am, mlg / am))


def day_pnl_and_flags(rng, n, kind):
    """One day of n trades. Returns (pnl_R, max_consecutive_losses, max_consecutive_nonwins)."""
    pnl, run_l, best_l, run_nw, best_nw = 0.0, 0, 0, 0, 0
    for _ in range(n):
        u = rng.random()
        if kind == "plain-55":            # 55 % wins at 1:1, edge +0.10R
            x = 1.0 if u < 0.55 else -1.0
        elif kind == "fi-cuts":           # 45.5 % wins +1R; losers half cut at -0.3R, half -1R; edge +0.10R
            if u < 0.4545:
                x = 1.0
            elif u < 0.4545 + 0.5455 / 2:
                x = -0.3
            else:
                x = -1.0
        else:                              # "scratches": 15 % breakeven, 47 % +1R, 38 % -1R, edge +0.09R
            x = 0.0 if u < 0.15 else (1.0 if u < 0.15 + 0.47 else -1.0)
        pnl += x
        if x < 0:
            run_l += 1
            best_l = max(best_l, run_l)
        else:
            run_l = 0
        if x <= 0:
            run_nw += 1
            best_nw = max(best_nw, run_nw)
        else:
            run_nw = 0
    return pnl, best_l, best_nw


def part2(days=20000):
    print("\nPART 2: share of days a brake fires, healthy units, %d simulated days each" % days)
    print("%-10s %4s %10s %10s %12s %12s %14s" % ("unit", "N", "3-in-row", "3 non-win", "day<=-3R",
                                                   "day<=-1%ile", "1%ile in R"))
    rng = random.Random(42)
    for kind in ["plain-55", "fi-cuts", "scratches"]:
        for n in [4, 10, 16, 40]:
            rows = [day_pnl_and_flags(rng, n, kind) for _ in range(days)]
            pn = sorted(r[0] for r in rows)
            q01 = pn[int(0.01 * days)]
            print("%-10s %4d %10.3f %10.3f %12.3f %12.3f %14.2f" % (
                kind, n, sum(r[1] >= 3 for r in rows) / days, sum(r[2] >= 3 for r in rows) / days,
                sum(r[0] <= -3 for r in rows) / days, sum(r[0] <= q01 for r in rows) / days, q01))


def part3():
    print("\nPART 3: cushion-day multiplier versus old house money at several day loss limits")
    print("day profit (% of day-start equity) -> size multiplier (L + P) / L")
    for L in [0.01, 0.02, 0.05, 0.10]:
        print("  L=%4.0f%%: " % (L * 100) + "  ".join(
            "P=%+.1f%%:%.2f" % (P * 100, (L + P) / L) for P in [-0.01, -0.005, 0.0, 0.005, 0.01]))
    print("\nPART 4: trades needed before a lag-1 autocorrelation rho is 2 standard errors from zero")
    for rho in [0.02, 0.05, 0.10, 0.20]:
        print("  rho=%.2f -> about %d trades" % (rho, round(4 / rho ** 2)))
    print("\nPART 5: extra edge from pressing after a win (size 1+k after a win, 1-k after a loss)")
    print("for +/-1R trades with lag-1 autocorrelation rho: extra ~ k * rho per trade in R")
    for rho in [0.02, 0.05, 0.10]:
        print("  rho=%.2f, k=0.5 -> +%.3fR per trade (compare a thin edge of +0.05R)" % (rho, 0.5 * rho))


def part6(paths=300):
    """Persistence shows up in block sums long before it shows in lag-1 trade autocorrelation."""
    print("\nPART 6: correlation of consecutive block P&L sums, and trades to reach 2 standard errors")
    for scen in ["iid-thin", "regime-fast", "regime-slow"]:
        rng = random.Random(7 + len(scen))
        streams = [gen_outcomes(rng, scen, DAYS * TPD) for _ in range(paths)]
        line = []
        for B in [1, 10, 50, 200]:
            xs, ys = [], []
            for outs in streams:
                sums = [sum(outs[k:k + B]) for k in range(0, len(outs) - B + 1, B)]
                xs += sums[:-1]
                ys += sums[1:]
            mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
            cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
            vx = sum((a - mx) ** 2 for a in xs)
            vy = sum((b - my) ** 2 for b in ys)
            rho = cov / math.sqrt(vx * vy)
            need = (B * 4 / rho ** 2) if rho > 0.005 else float("inf")
            line.append("B=%d rho=%.3f trades~%s" % (B, rho, "inf" if need == float("inf") else "%d" % need))
        print("  %-12s " % scen + " | ".join(line))


if __name__ == "__main__":
    paths = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    if len(sys.argv) > 2 and sys.argv[2] == "blocks":
        part6()
        sys.exit(0)
    part3()
    part2()
    part1(paths)
    part6()
