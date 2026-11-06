"""Reviewer's integrated check: does the picked set make money from a weak but real edge?

Standard library only. Run:  python -I stack_sim.py [paths] [days] [N] [rates] [mode]
  mode = table (default): the arms against seven unit cases.  mode = attrib: add one pick at a time.

Model numbers, not evidence about a real strategy. It follows DP9, DP10, DP14, DP15, DP16, DP17, DP20 and DP27 together,
which no sim in the funnel does: X2's sim has the sizer and no ladder or brakes; X3's has brakes at size 1 with a
next-day reset; flaw_arithmetic section E adds the ramp without the e-bars.

Worked-example numbers only, the same as the funnel's own: $500 seed, $300 floor, eps 1 %, 20-day horizon.
Trade outcomes (the FI scalper of X3 and X2): win +1R; half of losers cut at -0.3R, half a full -1R; p set so net EV = edge.
Costs are inside the outcomes. No fat tails, no gaps. Final equity is exponential in size, so read the size ratio too.

Every reading of the picks below is the milder one where the text allows two:
  - REDUCING steps one level down (X3-H02 "every step is one level") but with no cool-down or probes, although X3-H15
    says "after a bench or a level cut".
  - e-bars: favourable reading 20/50/100/100 for L2..L5, live from day one at L1 (Q3 yes, no paper bar).
  - the memory ceiling only asks one extra cohort; a second trip inside 20 days locks that level for 20 days.
  - no SQS shrink, no news window, no class caution, no weekend scale, no agent cut, no share ladder, no macro governor.

Flags: R reserve+cost denominator, C cohort climb, B bench at own p1 back next window at the same level,
D CUSUM warning steps down one level (second warning inside 500 trades goes to paper), E e-bars as ceiling,
H halve for the rest of the window at own p10, L that halve also drops a level, P bench restore ladder (cool-down, probes,
memory, lock), M brake half of the cushion pair, K gain-lock ratchet 25 %, X paper first until e>=10 and bars as X5-H13 wrote them.
"""
import math
import random
import sys

PATHS = int(sys.argv[1]) if len(sys.argv) > 1 else 200
DAYS = int(sys.argv[2]) if len(sys.argv) > 2 else 180
N = int(sys.argv[3]) if len(sys.argv) > 3 else 1
RATES = [int(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else [10]
MODE = sys.argv[5] if len(sys.argv) > 5 else "table"
SEED, FLOOR = 500.0, 300.0
Z, HDAYS = 2.5758, 20
RHO = 0.3
CUT = 0.3
LEVELS = [0.10, 0.25, 0.50, 0.75, 1.00]
GRID = [0.02, 0.04, 0.08, 0.16, 0.32]  # a mixture e-process, a fair reading of "the e-meter"
RESERVE, COST_DEN = 0.85, 0.85


def outcomes(edge):
    loss = 0.5 * CUT + 0.5
    p = (edge + loss) / (1.0 + loss)
    return p, (1 - p) / 2


def card(edge, n, rng, days=4000):
    """Own percentile thresholds on the running minimum of the window, as the frozen card would give them."""
    p, q = outcomes(edge)
    w = max(1, math.ceil(10 / n))
    mins = []
    hist = []
    for _ in range(days):
        base = sum(hist[-(w - 1):]) if w > 1 else 0.0
        pnl, mn = base, min(0.0, base)
        day = 0.0
        for _ in range(n):
            u = rng.random()
            x = 1.0 if u < p else (-CUT if u < p + q else -1.0)
            pnl += x
            day += x
            mn = min(mn, pnl)
        mins.append(mn)
        hist.append(day)
    mins.sort()
    return mins[int(0.10 * days)], mins[int(0.012 * days)]


def spread(edge):
    p, q = outcomes(edge)
    m2 = p + q * CUT * CUT + q
    return math.sqrt(m2 - edge * edge)


def run_path(flags, edge_fn, believed, n, rng, thr10, thr1, s_plan):
    eq, floor, hwm = SEED, FLOOR, SEED
    B = math.sqrt(N * (1 + (N - 1) * RHO))
    H = n * HDAYS
    w = max(1, math.ceil(10 / n))
    cohort = 25 if n >= 10 else (15 if n >= 4 else 10)
    has = lambda f: f in flags
    bars = (0, 50, 100, 200, 400) if has("X") else (0, 20, 50, 100, 100)
    lvl = 0 if has("C") else 4
    lock_top, lock_until = 4, -1
    warned = False
    e = [1.0] * len(GRID)
    co_n, co_r, clean = 0, 0.0, 0
    cusum, warn_trades = 0.0, []
    paper = False
    need_paper = has("X")
    cool, probe_left, probe_r = 0, 0, 0.0
    trades, last_trip_day = 0, -999
    min_share = 1.0
    start_cushion = SEED - FLOOR
    sum_frac, n_frac = 0.0, 0
    hist = []
    bench_until_next_window = -1
    for day in range(DAYS):
        edge = edge_fn(day)
        p, q = outcomes(edge)
        D = max(eq - floor, 0.0)
        base = D / (s_plan * Z * math.sqrt(H) * B)
        if has("R"):
            base *= RESERVE * COST_DEN
        if lock_until >= 0 and day > lock_until:
            lock_top, lock_until = 4, -1
        day_money, day_r = 0.0, 0.0
        window_base = sum(hist[-(w - 1):]) if w > 1 else 0.0
        trade_today = cool == 0 and day >= bench_until_next_window
        if cool > 0:
            cool -= 1
        halved, benched = False, False
        pnl = window_base
        for t in range(n):
            if not trade_today or benched:
                break
            for u_i in range(N):
                u = rng.random()
                x = 1.0 if u < p else (-CUT if u < p + q else -1.0)
                frac = LEVELS[0] if probe_left > 0 else LEVELS[lvl]
                size = base * frac
                if has("M"):
                    L = -thr1
                    size *= max(0.25, min(1.0, (L + pnl) / L))
                if halved:
                    size *= 0.5
                live = not (paper or need_paper)
                if live:
                    day_money += size * x
                    sum_frac += size / max(base, 1e-9)
                    n_frac += 1
                trades += 1
                day_r += x
                if has("E") or has("X"):
                    for k, lam in enumerate(GRID):
                        e[k] *= 1 + lam * x
                if has("D"):
                    cusum = max(0.0, cusum + (believed - 0.05 - x))
                    if cusum >= 17.0:
                        cusum = 0.0
                        warned = True
                        warn_trades = [v for v in warn_trades if trades - v <= 500] + [trades]
                        if len(warn_trades) >= 2:
                            paper = True
                        lvl = max(0, lvl - 1)
                        clean = 0
                if probe_left > 0:
                    probe_left -= 1
                    probe_r += x
                    if probe_left == 0 and probe_r < -1.5:
                        cool, probe_left, probe_r = 2, 5, 0.0
                        benched = True
                if has("C"):
                    co_n += 1
                    co_r += x
                    if co_n >= cohort:
                        bad = co_r <= -0.2 * cohort * s_plan
                        co_n, co_r = 0, 0.0
                        if bad:
                            warned = warned or has("E")
                            clean = 0
                        else:
                            clean += 1
                            if clean >= (2 if (has("E") and warned) else 1):
                                clean = 0
                                top = lock_top
                                if has("E") or has("X"):
                                    emix = sum(e) / len(e)
                                    while top > 0 and emix < bars[top]:
                                        top -= 1
                                if lvl < top:
                                    lvl += 1
                pnl += x
                if has("B") and pnl <= thr1 and not benched:
                    benched = True
                    bench_until_next_window = day + w
                    if has("P"):
                        cool = w
                        probe_left, probe_r = 5, 0.0
                        if day - last_trip_day <= 20:
                            lock_top, lock_until = max(0, lvl - 1), day + 20
                        last_trip_day = day
                        lvl = 0
                        warned = True
                elif has("H") and pnl <= thr10 and not halved:
                    halved = True
                    if has("L"):
                        lvl = max(0, lvl - 1)
            if eq + day_money - floor <= 0:
                return floor, 0.0, (sum_frac / n_frac if n_frac else 0.0), trades, True
        eq += day_money
        hist.append(day_r)
        if need_paper and sum(e) / len(e) >= 10:
            need_paper = False
        if has("K") and eq > hwm:
            floor += 0.25 * (eq - hwm)
        hwm = max(hwm, eq)
        min_share = min(min_share, (eq - floor) / start_cushion)
    return eq, min_share, (sum_frac / n_frac if n_frac else 0.0), trades, False


def pct(xs, q):
    s = sorted(xs)
    return s[min(len(s) - 1, int(q * len(s)))]


ARMS = [("BARE", ""), ("CORE", "RCBD"), ("PICK", "RCBDEHLPMK"), ("PICK_X5", "RCBDEHLPMKX")]
ATTRIB = [
    ("sizer alone", ""),
    ("+reserve,cost denominator", "R"),
    ("+cohort climb", "RC"),
    ("+own-p1 bench, next window", "RCB"),
    ("+CUSUM step-down", "RCBD"),
    ("+e-bars as ceiling", "RCBDE"),
    ("+halve at own p10", "RCBDEH"),
    ("+that halve drops a level", "RCBDEHL"),
    ("+probes,memory,lock", "RCBDEHLP"),
    ("+brake half of cushion pair", "RCBDEHLPM"),
    ("+ratchet 25 %", "RCBDEHLPMK"),
]


def table(title, edge_fn, believed, n, arms, seed=11):
    rng = random.Random(seed)
    thr10, thr1 = card(believed, n, rng)
    s_plan = spread(believed)
    print(f"\n{title}  [n={n}/day N={N} days={DAYS} paths={PATHS}; card p10={thr10:.1f}R p1={thr1:.1f}R s={s_plan:.2f}]")
    print(f"  {'arm':<28} {'median$':>8} {'gain$':>7} {'p10$':>7} {'P(cushion<50%)':>14} {'touch':>6} {'size/baseline':>13} {'x seed':>6}")
    for name, flags in arms:
        out = [run_path(flags, edge_fn, believed, n, rng, thr10, thr1, s_plan) for _ in range(PATHS)]
        eqs = [o[0] for o in out]
        med = pct(eqs, 0.5)
        below = sum(1 for o in out if o[1] < 0.5) / PATHS
        touch = sum(1 for o in out if o[4]) / PATHS
        frac = sum(o[2] for o in out) / PATHS
        print(f"  {name:<28} {med:8.0f} {med-SEED:7.0f} {pct(eqs,0.1):7.0f} {below*100:13.1f}% {touch*100:5.1f}% {frac:13.2f} {med/SEED:6.2f}")


if __name__ == "__main__":
    for n in RATES:
        if MODE == "attrib":
            table("HEALTHY +0.10R", lambda d: 0.10, 0.10, n, ATTRIB)
            table("WEAK +0.05R", lambda d: 0.05, 0.05, n, ATTRIB)
        else:
            table("HEALTHY +0.10R, as believed", lambda d: 0.10, 0.10, n, ARMS)
            table("WEAK +0.05R, as believed", lambda d: 0.05, 0.05, n, ARMS)
            table("THIN +0.03R, as believed", lambda d: 0.03, 0.03, n, ARMS)
            table("OVERSTATED true +0.03R, card +0.10R", lambda d: 0.03, 0.10, n, ARMS)
            table("NO EDGE true 0, card +0.10R", lambda d: 0.0, 0.10, n, ARMS)
            table("BLEEDING true -0.05R, card +0.10R", lambda d: -0.05, 0.10, n, ARMS)
            table("GOOD STREAK +0.03R, +0.30R on days 40-60, +0.03R", lambda d: 0.30 if 40 <= d < 60 else 0.03, 0.03, n, ARMS)
