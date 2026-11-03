"""X3 arithmetic: do unit brakes choke healthy units, do they carry timing, and which slow lane sees decay first?

Standard library only. Run:  python -I x3_brake_sim.py [paths]
Model numbers, not evidence about real strategies. Size is 1 per trade (R units, no compounding),
so "total R" measures how much of the edge a brake keeps or throws away.

Units (costs netted into the outcomes):
  fs10 : full-stop scalper, 10 trades/day, 55 % wins +1R, losses -1R            (EV +0.10R)
  fi10 : fast-invalidation scalper, 10/day, 45.5 % wins +1R, half of losers cut at -0.3R, rest -1R (EV +0.10R)
  fi40 : the same at 40 trades/day
  be4  : intraday with breakeven exits, 4/day, 47 % +1R, 15 % scratch -0.05R, 38 % -1R (EV +0.08R)
  orb2 : ORB-like, 2/day, 40 % +2R, 60 % -1R                                     (EV +0.20R)
Scenarios, 250 trading days:
  healthy : edge constant
  decay   : edge falls to about -0.05R (dead after costs) at day 100 and stays there
  badweek : edge negative (about -0.15R) on days 100-104 only, healthy otherwise
  regime  : hidden good/bad state per trade, good spells ~100 trades, bad ~50 (bad share 1/3, bad EV about -0.15R)
Fast brakes (each arm sees the same trades; a trip benches the rest of the day unless said otherwise):
  none     : no brake
  2stops   : 2 losses at or below -0.9R in a day (the old circuit breaker)
  3inrow   : 3 losses in a row (a loss is R < -0.1, so scratches do not count)
  3nonwin  : 3 non-wins in a row (scratches count: the trap)
  lpts     : loss points (sum of |loss R| today) reach the unit's own p99 of daily loss points
  money    : running day P&L reaches the unit's own p1 of the daily running minimum (expected fire rate 1 %)
  money_h  : same trigger, but halve size for the rest of the day instead of benching (REDUCING)
  random   : fires on a random day at a random trade, at the same healthy rate as `money`
Slow lane (watch the no-brake stream; alarm = demotion candidate):
  dens     : Bernoulli CUSUM on daily `money` fires, p0 from calibration, tuned to p1 = 3 x p0
  cusum    : CUSUM on trade R, allowance half the healthy edge
  Both thresholds are set so a healthy unit alarms in at most 5 % of 250-day runs.
"""
import random
import sys

DAYS = 250
CHANGE = 100

UNITS = {
    # name: (trades per day, healthy outcome table, decayed table, bad table)
    # an outcome table is a list of (probability, R)
    "fs10": (10, [(0.55, 1.0), (0.45, -1.0)], [(0.475, 1.0), (0.525, -1.0)], [(0.425, 1.0), (0.575, -1.0)]),
    "fi10": (10, [(0.455, 1.0), (0.2725, -0.3), (0.2725, -1.0)],
             [(0.3636, 1.0), (0.3182, -0.3), (0.3182, -1.0)],
             [(0.30, 1.0), (0.35, -0.3), (0.35, -1.0)]),
    "fi40": (40, [(0.455, 1.0), (0.2725, -0.3), (0.2725, -1.0)],
             [(0.3636, 1.0), (0.3182, -0.3), (0.3182, -1.0)],
             [(0.30, 1.0), (0.35, -0.3), (0.35, -1.0)]),
    "be4": (4, [(0.47, 1.0), (0.15, -0.05), (0.38, -1.0)],
            [(0.40375, 1.0), (0.15, -0.05), (0.44625, -1.0)],
            [(0.35, 1.0), (0.15, -0.05), (0.50, -1.0)]),
    "orb2": (2, [(0.40, 2.0), (0.60, -1.0)], [(0.3167, 2.0), (0.6833, -1.0)], [(0.28, 2.0), (0.72, -1.0)]),
}


def ev(tab):
    return sum(p * r for p, r in tab)


def draw(rng, tab):
    u = rng.random()
    acc = 0.0
    for p, r in tab:
        acc += p
        if u < acc:
            return r
    return tab[-1][1]


def gen_path(rng, unit, scen):
    tpd, h, d, b = UNITS[unit]
    days = []
    good = True
    for day in range(DAYS):
        tr = []
        for _ in range(tpd):
            if scen == "healthy":
                tab = h
            elif scen == "decay":
                tab = h if day < CHANGE else d
            elif scen == "badweek":
                tab = b if CHANGE <= day < CHANGE + 5 else h
            else:  # regime: good spells about 100 trades, bad spells about 50; bad share one third
                if rng.random() < (1.0 / 100 if good else 1.0 / 50):
                    good = not good
                tab = h if good else b
            tr.append(draw(rng, tab))
        days.append(tr)
    return days


def quantile(xs, q):
    s = sorted(xs)
    i = min(len(s) - 1, max(0, int(q * len(s))))
    return s[i]


def window_days(unit):
    """The money brake's window is set in trades, not days: at least 10 trades."""
    tpd = UNITS[unit][0]
    return max(1, -(-10 // tpd))


def lower_tail_thr(xs, target):
    """Largest observed value t with P(x <= t) <= target (daily results take few values)."""
    s = sorted(xs)
    n = len(s)
    vals = sorted(set(s))
    best = vals[0]
    import bisect
    for v in vals:
        share = bisect.bisect_right(s, v) / n
        if share <= target:
            best = v
        else:
            break
    return best


def upper_tail_thr(xs, target):
    neg = [-x for x in xs]
    return -lower_tail_thr(neg, target)


def window_mins(days, w):
    """Running minimum of P&L over a rolling w-day window, one value per day."""
    out = []
    prev = []
    for tr in days:
        base = sum(prev[-(w - 1):]) if w > 1 else 0.0
        pnl, mn = base, base if w > 1 else 0.0
        mn = min(0.0, base)
        day = 0.0
        for r in tr:
            pnl += r
            day += r
            mn = min(mn, pnl)
        out.append(mn)
        prev.append(day)
    return out


def calibrate(rng, unit, n_days=6000):
    """Thresholds from a long healthy record, as a holdout or approved backtest would give them."""
    tpd, h, _, _ = UNITS[unit]
    w = window_days(unit)
    days = [[draw(rng, h) for _ in range(tpd)] for _ in range(n_days)]
    run_mins = window_mins(days, w)
    lpts = [sum(-r for r in tr if r < 0) for tr in days]
    money_thr = lower_tail_thr(run_mins, 0.012)
    lp_thr = upper_tail_thr(lpts, 0.012)
    extra = {
        "m5": lower_tail_thr(run_mins, 0.05),
        "m10": lower_tail_thr(run_mins, 0.10),
        "day10": lower_tail_thr([sum(tr) for tr in days], 0.10),
    }
    return money_thr, lp_thr, extra


ARMS = ["none", "2stops", "3inrow", "3nonwin", "3inrow_h", "lpts", "money", "money_h", "money5", "money10h", "ladder", "aimd", "random"]


EXTRA = {}


def run_fast(days, money_thr, lp_thr, rand_rate, rng, w=1, arms=None, rates=None):
    """Return {arm: (total_R, fire_days, maxdd_R, R_after_change)} for one path.
    `rates` maps extra random arms ("rnd:<name>") to their own fire rates (matched controls)."""
    out = {}
    tpd = len(days[0])
    arms = arms or ARMS
    rates = dict(rates or {})
    rates["random"] = rand_rate
    rnd = {a: ([rng.random() < q for _ in days], [rng.randrange(tpd) for _ in days]) for a, q in rates.items()}
    for arm in arms:
        tot, fires, peak, maxdd, after = 0.0, 0, 0.0, 0.0, 0.0
        hist = []  # unbraked daily P&L, for the rolling window
        mult = 1.0  # aimd day multiplier (brake and restore only, never above 1)
        for di, tr in enumerate(days):
            if arm == "aimd" and di > 0:
                yday = hist[-1]
                mult = mult * 0.7 if yday <= EXTRA["day10"] else (min(1.0, mult + 0.05) if yday > 0 else mult)
            base = sum(hist[-(w - 1):]) if w > 1 else 0.0
            pnl, stops, inrow, nonwin, lp = base, 0, 0, 0, 0.0
            hist.append(sum(tr))
            size, benched, fired = (mult if arm == "aimd" else 1.0), False, False
            if arm == "aimd" and mult < 1.0:
                fired = True
            for ti, r in enumerate(tr):
                if benched:
                    break
                if arm in rnd and rnd[arm][0][di] and ti == rnd[arm][1][di]:
                    fired = True
                    break
                x = r * size
                tot += x
                if di >= CHANGE:
                    after += x
                pnl += r
                peak = max(peak, tot)
                maxdd = max(maxdd, peak - tot)
                if r <= -0.9:
                    stops += 1
                inrow = inrow + 1 if r < -0.1 else 0
                nonwin = nonwin + 1 if r <= 0 else 0
                if r < 0:
                    lp += -r
                if arm == "2stops" and stops >= 2:
                    benched = fired = True
                elif arm == "3inrow" and inrow >= 3:
                    benched = fired = True
                elif arm == "3nonwin" and nonwin >= 3:
                    benched = fired = True
                elif arm == "lpts" and lp >= lp_thr:
                    benched = fired = True
                elif arm == "money" and pnl <= money_thr:
                    benched = fired = True
                elif arm == "money_h" and pnl <= money_thr and size == 1.0:
                    size, fired = 0.5, True
                elif arm == "3inrow_h" and inrow >= 3 and size == 1.0:
                    size, fired = 0.5, True
                elif arm == "money5" and pnl <= EXTRA["m5"]:
                    benched = fired = True
                elif arm == "money10h" and pnl <= EXTRA["m10"] and size == 1.0:
                    size, fired = 0.5, True
                elif arm == "ladder":
                    if pnl <= money_thr:
                        benched = fired = True
                    elif pnl <= EXTRA["m10"] and size == 1.0:
                        size, fired = 0.5, True
            fires += fired
        out[arm] = (tot, fires, maxdd, after)
    return out


def slow_stats(days, money_thr, mu0, p0, w=1):
    """Return daily series of the two slow-lane statistics (their running values)."""
    k1 = min(3.0, 0.5 / p0)
    import math
    a = math.log(k1)
    b = math.log((1 - k1 * p0) / (1 - p0))
    dens, cus = 0.0, 0.0
    dens_s, cus_s = [], []
    allow = mu0 / 2.0
    mins = window_mins(days, w)
    for di, tr in enumerate(days):
        for r in tr:
            cus = max(0.0, cus + (mu0 - r - allow))
        fired = mins[di] <= money_thr
        dens = max(0.0, dens + (a if fired else b))
        dens_s.append(dens)
        cus_s.append(cus)
    return dens_s, cus_s


def first_cross(series, thr, start=0):
    for i in range(start, len(series)):
        if series[i] >= thr:
            return i
    return None


def main():
    paths = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    rng = random.Random(20261103)
    for unit in UNITS:
        tpd, h, d, b = UNITS[unit]
        mu0 = ev(h)
        w = window_days(unit)
        money_thr, lp_thr, extra = calibrate(rng, unit)
        EXTRA.clear()
        EXTRA.update(extra)
        sims = {}
        for scen in ["healthy", "decay", "badweek", "regime"]:
            sims[scen] = [gen_path(rng, unit, scen) for _ in range(paths)]
        # healthy fire rate of `money` (target about 1 %)
        hits = sum(sum(1 for m in window_mins(days, w) if m <= money_thr) for days in sims["healthy"])
        p0 = max(hits / (paths * DAYS), 0.002)
        # slow-lane thresholds: 95th percentile of the healthy 250-day maximum
        dmax, cmax = [], []
        for days in sims["healthy"]:
            ds, cs = slow_stats(days, money_thr, mu0, p0, w)
            dmax.append(max(ds))
            cmax.append(max(cs))
        dthr, cthr = quantile(dmax, 0.95), quantile(cmax, 0.95)
        print(f"\n=== {unit}: {tpd}/day, healthy EV {mu0:+.3f}R, decayed EV {ev(d):+.3f}R, bad EV {ev(b):+.3f}R")
        print(f"    money brake: {w}-day window, trips at running P&L <= {money_thr:+.2f}R (own p1, healthy fire rate {100*p0:.1f}%); loss points at {lp_thr:.2f} (own p99)")
        print("    arm       | " + " | ".join(f"{x:>30}" for x in ["healthy: R kept, fire%, DDp95", "decay: R after day 100", "badweek: R", "regime: R (fire%), DDp95"]))
        base = {}
        for scen in sims:
            base[scen] = [run_fast(days, money_thr, lp_thr, p0, rng, w) for days in sims[scen]]
        rows = {}
        for arm in ARMS:
            h_tot = sum(r[arm][0] for r in base["healthy"]) / paths
            h_none = sum(r["none"][0] for r in base["healthy"]) / paths
            h_fire = 100.0 * sum(r[arm][1] for r in base["healthy"]) / (paths * DAYS)
            h_dd = quantile([r[arm][2] for r in base["healthy"]], 0.95)
            d_after = sum(r[arm][3] for r in base["decay"]) / paths
            bw = sum(r[arm][0] for r in base["badweek"]) / paths
            rg = sum(r[arm][0] for r in base["regime"]) / paths
            rg_fire = sum(r[arm][1] for r in base["regime"]) / (paths * DAYS)
            rg_dd = quantile([r[arm][2] for r in base["regime"]], 0.95)
            kept = 100.0 * h_tot / h_none if h_none else 0.0
            rows[arm] = (rg, rg_fire)
            print(f"    {arm:9} | {h_tot:7.1f}R ({kept:5.1f}%) {h_fire:5.1f}% {h_dd:5.1f} | {d_after:28.1f}R | {bw:29.1f}R | {rg:7.1f}R ({100*rg_fire:4.1f}%) {rg_dd:6.1f}")
        # matched random controls in the regime scenario: same fire rate, same action (bench)
        ctrl = {f"rnd:{a}": rows[a][1] for a in ["2stops", "3inrow", "lpts", "money"]}
        res = [run_fast(days, money_thr, lp_thr, p0, rng, w, arms=list(ctrl), rates=ctrl) for days in sims["regime"]]
        line = []
        for a in ["2stops", "3inrow", "lpts", "money"]:
            rr = sum(r[f"rnd:{a}"][0] for r in res) / paths
            line.append(f"{a} {rows[a][0]:+.1f}R vs random {rr:+.1f}R (timing {rows[a][0]-rr:+.1f}R)")
        print("    regime, matched random control: " + "; ".join(line))
        # slow lane
        for name, idx, thr in [("dens", 0, dthr), ("cusum", 1, cthr)]:
            det, delays, bw_alarm, h_alarm = 0, [], 0, 0
            for days in sims["decay"]:
                ser = slow_stats(days, money_thr, mu0, p0, w)[idx]
                pre = first_cross(ser[:CHANGE], thr)
                t = first_cross(ser, thr, CHANGE)
                if pre is None and t is not None:
                    det += 1
                    delays.append(t - CHANGE)
            for days in sims["badweek"]:
                ser = slow_stats(days, money_thr, mu0, p0, w)[idx]
                if first_cross(ser[CHANGE:CHANGE + 20], thr) is not None and first_cross(ser[:CHANGE], thr) is None:
                    bw_alarm += 1
            for days in sims["healthy"]:
                ser = slow_stats(days, money_thr, mu0, p0, w)[idx]
                if first_cross(ser, thr) is not None:
                    h_alarm += 1
            md = quantile(delays, 0.5) if delays else None
            # policies in R: demote at alarm (paper for the rest of the run), or graded (half at 0.5 x thr, paper at thr)
            pol = {}
            for scen in ["healthy", "decay", "badweek"]:
                dem, grd = 0.0, 0.0
                for days in sims[scen]:
                    ser = slow_stats(days, money_thr, mu0, p0, w)[idx]
                    gone = False
                    for di, tr in enumerate(days):
                        prev = ser[di - 1] if di > 0 else 0.0
                        if not gone:
                            dem += sum(tr)
                        g = 0.0 if prev >= thr else (0.5 if prev >= 0.5 * thr else 1.0)
                        grd += g * sum(tr)
                        if ser[di] >= thr:
                            gone = True
                pol[scen] = (dem / paths, grd / paths)
            nb = {sc: sum(sum(sum(tr) for tr in dd) for dd in sims[sc]) / paths for sc in ["healthy", "decay", "badweek"]}
            print(f"    slow {name:5} as policy, total R (no slow lane / demote at alarm / graded): healthy {nb['healthy']:.1f}/{pol['healthy'][0]:.1f}/{pol['healthy'][1]:.1f}; decay {nb['decay']:.1f}/{pol['decay'][0]:.1f}/{pol['decay'][1]:.1f}; badweek {nb['badweek']:.1f}/{pol['badweek'][0]:.1f}/{pol['badweek'][1]:.1f}")
            print(f"    slow {name:5}: healthy false alarm {100.0*h_alarm/paths:4.1f}% | decay caught in 150 days {100.0*det/paths:5.1f}%, median delay {md} days | alarm inside 20 days of a bad week {100.0*bw_alarm/paths:4.1f}%")


if __name__ == "__main__":
    main()
