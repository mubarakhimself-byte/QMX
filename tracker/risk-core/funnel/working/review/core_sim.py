"""Funnel judge's harder integrated check, extending the reviewer's stack_sim.py (same model, same worked numbers).

Standard library only. Run:  python -I core_sim.py [paths] [days] [N-list] [cost-list] [lot] [mode]
  mode = table (default) | shed (lot-shed check at a coarse lot) | attrib (add core parts one at a time)

MODEL NUMBERS ONLY. Not evidence about a real strategy. Same worked example as the funnel and the review:
$500 seed, $300 floor, eps 1 %, 20-day horizon, 10 trades a day per unit, FI scalper outcomes
(win +1R; half of losers cut at -0.3R, half a full -1R; p set so net EV = edge at cost 1x).

What this adds to stack_sim.py:
  - several correlated units (N) through a common draw with rho 0.3;
  - fat tails: 1.5 % of losses are -3R (gap through the stop), independent per unit;
  - gap days: on 2 % of days every unit's first trade is -3R at once;
  - lot rounding: size rounds down to a lot step of $LOT; below one step the trade skips (dark);
  - the M9 shed rule: at each anchor, if a unit's baseline x level is under two lot steps, the lowest-ranked
    units are shed (paper) until the survivors clear two steps, and B is recomputed on the live count;
  - costs at more than one level: cost multiplier cm adds -(cm-1) x 0.16R to every outcome;
    the card still believes the cost-1x edge, so the drift brakes must catch it;
  - the portfolio day stop (M6) as a tail brake: book day P&L <= -2.5 sigma_book stops new entries
    for the day and expires at the next anchor; the pair's brake half tapers 1 -> 0.25 between -1.3 and
    -2.5 sigma_book (one reading of the book's running loss, reverse house money at portfolio scope);
  - the core's climb: start level from the holdout (0.50 if the card's low end is positive, else 0.25),
    one level per clean cohort, CUSUM warning steps one level down, second warning inside 500 trades -> paper;
  - the unit bench at own p1 over its window with retry-then-lockout (second bench inside 20 days locks one
    level lower for 20 days; third inside 40 days -> paper for 20 days);
  - the edge dial released by proof: once the unit's e-meter mixture >= 20, base x 1.5 (a stand-in for the
    horizon sizer at drift `low`; X2's sim shows about 1.7x average risk), reverted on any CUSUM warning.

Flags: R reserve+cost denominator; S start level from holdout; C cohort climb; D CUSUM step-down;
B unit bench at own p1 with retry-then-lockout; G portfolio day stop; T pair brake half taper to the day stop;
A dial release above baseline by the e-meter; E e-bars as a ceiling under baseline (the old pick, kept to show M2);
H halve at own p10; L that halve drops a level; P probes/memory/lock; M unit brake half floor 0.25; K ratchet
(the reviewer's reading of the old picks); O lot rounding with skip; Y shed rule (needs O); F fat tails; J gap days.
"""
import math
import random
import sys

PATHS = int(sys.argv[1]) if len(sys.argv) > 1 else 60
DAYS = int(sys.argv[2]) if len(sys.argv) > 2 else 120
NLIST = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else [1, 5, 10]
COSTS = [float(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else [1.0, 1.5]
LOT = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
MODE = sys.argv[6] if len(sys.argv) > 6 else "table"
K_STOP = float(sys.argv[7]) if len(sys.argv) > 7 else 2.5   # portfolio day stop at -K_STOP x sigma_book; taper starts at 0.52 x that
SEED, FLOOR = 500.0, 300.0
Z, HDAYS = 2.5758, 20
RHO, CUT, COST_R = 0.3, 0.3, 0.16
RATE = 10
GRID = [0.02, 0.04, 0.08, 0.16, 0.32]
RESERVE, COST_DEN = 0.85, 0.85
TAIL_P, TAIL_R, GAP_DAY_P, GAP_R = 0.015, -3.0, 0.02, -3.0
OLD_LEVELS = [0.10, 0.25, 0.50, 0.75, 1.00]
CORE_LEVELS = [0.25, 0.50, 0.75, 1.00]


def outcomes(edge):
    loss = 0.5 * CUT + 0.5
    p = (edge + loss) / (1.0 + loss)
    return p, (1 - p) / 2


def spread(edge):
    p, q = outcomes(edge)
    m2 = p + q * CUT * CUT + q
    return math.sqrt(m2 - edge * edge)


def card(edge, n, rng, days=3000):
    """Own p10 and p1 of the window's running minimum, from the frozen card (cost 1x, no tails)."""
    p, q = outcomes(edge)
    w = max(1, math.ceil(10 / n))
    mins, hist = [], []
    for _ in range(days):
        base = sum(hist[-(w - 1):]) if w > 1 else 0.0
        pnl, mn, day = base, min(0.0, base), 0.0
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


def draw(rng, p, q, common, tails, extra):
    """One trade outcome in R. common: a shared uniform (correlated units) or None."""
    u = common if (common is not None and rng.random() < RHO) else rng.random()
    if u < p:
        x = 1.0
    elif u < p + q:
        x = -CUT
    else:
        x = -1.0
        if tails and rng.random() < TAIL_P:
            x = TAIL_R
    return x - extra


def run_path(flags, true_edge, believed, N, cm, rng, thr10, thr1, s_plan, tails, gapdays):
    has = lambda f: f in flags
    n = RATE
    p, q = outcomes(true_edge)
    extra = (cm - 1.0) * COST_R
    levels = CORE_LEVELS if has("S") else OLD_LEVELS
    if has("S"):
        start = 1 if believed - 0.05 > 0 else 0   # holdout low end positive -> 0.50, else 0.25
    else:
        start = 0 if has("C") else len(levels) - 1
    eq, floor = SEED, FLOOR
    H = n * HDAYS
    w = max(1, math.ceil(10 / n))
    cohort = 25
    bars = (0, 20, 50, 100)[:len(levels)] if len(levels) == 4 else (0, 20, 50, 100, 100)
    # per-unit state
    lvl = [start] * N
    live = [True] * N              # not shed, not in paper
    paper_until = [-1] * N
    co_n = [0] * N
    co_r = [0.0] * N
    clean = [0] * N
    cusum = [0.0] * N
    warns = [[] for _ in range(N)]
    e = [[1.0] * len(GRID) for _ in range(N)]
    dial = [1.0] * N
    bench_until = [-1] * N
    bench_days = [[] for _ in range(N)]
    lock_top = [len(levels) - 1] * N
    lock_until = [-1] * N
    warned_e = [False] * N
    # old-pick state
    cool = [0] * N
    probe_left = [0] * N
    probe_r = [0.0] * N
    last_trip = [-999] * N
    hist = [[] for _ in range(N)]
    hwm = SEED
    trades = 0
    sum_frac, n_frac = 0.0, 0
    skipped, attempted = 0, 0
    stop_fires = 0
    shed_total = 0
    lifts = 0
    min_share = 1.0
    start_cushion = SEED - FLOOR
    for day in range(DAYS):
        D = max(eq - floor, 0.0)
        N_live = sum(1 for i in range(N) if live[i] and day >= paper_until[i])
        if N_live == 0:
            N_live = 1
        B = math.sqrt(N_live * (1 + (N_live - 1) * RHO))
        base = D / (s_plan * Z * math.sqrt(H) * B)
        if has("R"):
            base *= RESERVE * COST_DEN
        sigma_book = D / (Z * math.sqrt(HDAYS))
        # M9 shed at the anchor
        if has("Y") and has("O"):
            order = sorted(range(N), key=lambda i: -i)   # lowest rank = highest index
            for i in order:
                if not live[i]:
                    continue
                if base * levels[lvl[i]] < 2 * LOT and N_live > 1:
                    live[i] = False
                    shed_total += 1
                    N_live -= 1
                    B = math.sqrt(N_live * (1 + (N_live - 1) * RHO))
                    base = D / (s_plan * Z * math.sqrt(H) * B) * ((RESERVE * COST_DEN) if has("R") else 1.0)
                elif not live[i] and base * levels[lvl[i]] >= 2 * LOT:
                    pass
            # un-shed when the baseline recovers
            for i in range(N):
                if not live[i]:
                    B2 = math.sqrt((N_live + 1) * (1 + N_live * RHO))
                    base2 = D / (s_plan * Z * math.sqrt(H) * B2) * ((RESERVE * COST_DEN) if has("R") else 1.0)
                    if base2 * levels[lvl[i]] >= 2 * LOT:
                        live[i] = True
                        N_live += 1
                        B = B2
                        base = base2
            # feasibility sets a floor under the level, never above the baseline: a live unit whose level
            # size is under one lot trades at the smallest level that clears one lot, if the full baseline does
            for i in range(N):
                if live[i] and base * levels[lvl[i]] < LOT <= base * levels[-1]:
                    while base * levels[lvl[i]] < LOT:
                        lvl[i] += 1
                    lifts += 1
        for i in range(N):
            if lock_until[i] >= 0 and day > lock_until[i]:
                lock_top[i], lock_until[i] = len(levels) - 1, -1
            if cool[i] > 0:
                cool[i] -= 1
        day_money = 0.0
        day_r = [0.0] * N
        pnl = [sum(hist[i][-(w - 1):]) if w > 1 else 0.0 for i in range(N)]
        benched = [False] * N
        halved = [False] * N
        book_day = 0.0
        stopped = False
        gap_today = gapdays and rng.random() < GAP_DAY_P
        for t in range(n):
            if stopped:
                break
            common = rng.random() if N > 1 else None
            for i in range(N):
                if not live[i] or day < paper_until[i] or benched[i] or day < bench_until[i] or cool[i] > 0:
                    continue
                if gap_today and t == 0:
                    x = GAP_R - extra
                else:
                    x = draw(rng, p, q, common, tails, extra)
                frac = levels[0] if probe_left[i] > 0 else levels[lvl[i]]
                size = base * frac * dial[i]
                if has("M"):
                    L = -thr1
                    size *= max(0.25, min(1.0, (L + pnl[i]) / L))
                if halved[i]:
                    size *= 0.5
                if has("T") and sigma_book > 0:
                    z_day = book_day / sigma_book
                    k_lo = 0.52 * K_STOP
                    if z_day < -k_lo:
                        size *= max(0.25, 1.0 - 0.75 * (-k_lo - z_day) / (K_STOP - k_lo))
                attempted += 1
                if has("O"):
                    size = LOT * math.floor(size / LOT)
                    if size < LOT:
                        skipped += 1
                        continue
                day_money += size * x
                book_day += size * x
                sum_frac += size / max(base, 1e-9)
                n_frac += 1
                trades += 1
                day_r[i] += x
                pnl[i] += x
                for k, lam in enumerate(GRID):
                    e[i][k] *= max(0.05, 1 + lam * x)
                if has("A"):
                    if sum(e[i]) / len(GRID) >= 20 and dial[i] == 1.0 and not warns[i]:
                        dial[i] = 1.5
                if has("D"):
                    cusum[i] = max(0.0, cusum[i] + (believed - 0.05 - x))
                    if cusum[i] >= 17.0:
                        cusum[i] = 0.0
                        warns[i] = [v for v in warns[i] if trades - v <= 500] + [trades]
                        dial[i] = 1.0
                        if len(warns[i]) >= 2:
                            paper_until[i] = DAYS + 1
                        lvl[i] = max(0, lvl[i] - 1)
                        clean[i] = 0
                        warned_e[i] = True
                if probe_left[i] > 0:
                    probe_left[i] -= 1
                    probe_r[i] += x
                    if probe_left[i] == 0 and probe_r[i] < -1.5:
                        cool[i], probe_left[i], probe_r[i] = 2, 5, 0.0
                        benched[i] = True
                if has("C"):
                    co_n[i] += 1
                    co_r[i] += x
                    if co_n[i] >= cohort:
                        bad = co_r[i] <= -0.2 * cohort * s_plan
                        co_n[i], co_r[i] = 0, 0.0
                        if bad:
                            clean[i] = 0
                        else:
                            clean[i] += 1
                            if clean[i] >= (2 if (has("E") and warned_e[i]) else 1):
                                clean[i] = 0
                                top = lock_top[i]
                                if has("E"):
                                    emix = sum(e[i]) / len(GRID)
                                    while top > 0 and emix < bars[top]:
                                        top -= 1
                                if lvl[i] < top:
                                    lvl[i] += 1
                if has("B") and pnl[i] <= thr1 and not benched[i]:
                    benched[i] = True
                    bench_until[i] = day + w
                    bench_days[i] = [d for d in bench_days[i] if day - d <= 40] + [day]
                    recent20 = sum(1 for d in bench_days[i] if day - d <= 20)
                    if len(bench_days[i]) >= 3:
                        paper_until[i] = day + 20
                        bench_days[i] = []
                    elif recent20 >= 2:
                        lock_top[i], lock_until[i] = max(0, lvl[i] - 1), day + 20
                        lvl[i] = min(lvl[i], lock_top[i])
                    if has("P"):
                        cool[i] = w
                        probe_left[i], probe_r[i] = 5, 0.0
                        if day - last_trip[i] <= 20:
                            lock_top[i], lock_until[i] = max(0, lvl[i] - 1), day + 20
                        last_trip[i] = day
                        lvl[i] = 0
                elif has("H") and pnl[i] <= thr10 and not halved[i]:
                    halved[i] = True
                    if has("L"):
                        lvl[i] = max(0, lvl[i] - 1)
            if has("G") and sigma_book > 0 and book_day <= -K_STOP * sigma_book:
                stopped = True
                stop_fires += 1
            if eq + day_money - floor <= 0:
                return dict(eq=floor, min_share=0.0, frac=(sum_frac / n_frac if n_frac else 0.0),
                            touch=True, fires=stop_fires, dark=(skipped / attempted if attempted else 0.0), shed=shed_total, lift=lifts)
        eq += day_money
        for i in range(N):
            hist[i].append(day_r[i])
        if has("K") and eq > hwm:
            floor += 0.25 * (eq - hwm)
        hwm = max(hwm, eq)
        min_share = min(min_share, (eq - floor) / start_cushion)
    return dict(eq=eq, min_share=min_share, frac=(sum_frac / n_frac if n_frac else 0.0),
                touch=False, fires=stop_fires, dark=(skipped / attempted if attempted else 0.0), shed=shed_total, lift=lifts)


def pct(xs, q):
    s = sorted(xs)
    return s[min(len(s) - 1, int(q * len(s)))]


ARMS = [
    ("BARE sizer+reserve", "R"),
    ("CORE", "RSCDBGT"),
    ("CORE+dial by proof", "RSCDBGTA"),
    ("CORE+e-bars (M2 check)", "RSCDBGTE"),
    ("OLD PICKS (review's)", "RCBDEHLPMK"),
]
ATTRIB = [
    ("sizer+reserve", "R"),
    ("+start level from holdout", "RS"),
    ("+cohort climb", "RSC"),
    ("+CUSUM step-down", "RSCD"),
    ("+unit bench p1, retry-lockout", "RSCDB"),
    ("+portfolio day stop", "RSCDBG"),
    ("+pair brake-half taper", "RSCDBGT"),
    ("+dial by proof", "RSCDBGTA"),
]
CASES = [
    ("HEALTHY +0.10R, card +0.10R", 0.10, 0.10),
    ("WEAK +0.05R, card +0.05R", 0.05, 0.05),
    ("OVERSTATED true +0.03R, card +0.10R", 0.03, 0.10),
    ("BLEEDING true -0.05R, card +0.10R", -0.05, 0.10),
]


def table(title, true_edge, believed, N, cm, arms, lot_flags, seed=11):
    rng = random.Random(seed)
    thr10, thr1 = card(believed, RATE, rng)
    s_plan = spread(believed)
    print(f"\n{title}  [N={N} cost x{cm} lot ${LOT} kstop={K_STOP} n={RATE}/day days={DAYS} paths={PATHS}; card p10={thr10:.1f}R p1={thr1:.1f}R; tails+gaps on]")
    print(f"  {'arm':<26} {'median$':>8} {'p10$':>7} {'P(cushion<50%)':>14} {'touch':>6} {'size/base':>9} {'stops/100d':>10} {'dark%':>6} {'shed':>5} {'lift':>5}")
    for name, flags in arms:
        out = [run_path(flags + lot_flags, true_edge, believed, N, cm, rng, thr10, thr1, s_plan, True, True) for _ in range(PATHS)]
        eqs = [o["eq"] for o in out]
        print(f"  {name:<26} {pct(eqs,0.5):8.0f} {pct(eqs,0.1):7.0f} {100*sum(1 for o in out if o['min_share']<0.5)/PATHS:13.1f}% "
              f"{100*sum(1 for o in out if o['touch'])/PATHS:5.1f}% {sum(o['frac'] for o in out)/PATHS:9.2f} "
              f"{100*sum(o['fires'] for o in out)/PATHS/DAYS:10.1f} {100*sum(o['dark'] for o in out)/PATHS:6.1f} {sum(o['shed'] for o in out)/PATHS:5.1f} {sum(o['lift'] for o in out)/PATHS:5.1f}")


if __name__ == "__main__":
    if MODE == "shed":
        for N in NLIST:
            for cm in COSTS:
                for title, te, be in CASES[:2]:
                    table(title + " [lot skip]", te, be, N, cm, [("CORE", "RSCDBGT")], "O")
                    table(title + " [lot shed, M9]", te, be, N, cm, [("CORE", "RSCDBGT")], "OY")
    elif MODE == "attrib":
        for N in NLIST:
            for title, te, be in CASES[:2]:
                table(title, te, be, N, 1.0, ATTRIB, "OY")
    else:
        for N in NLIST:
            for cm in COSTS:
                for title, te, be in CASES:
                    table(title, te, be, N, cm, ARMS, "OY")
