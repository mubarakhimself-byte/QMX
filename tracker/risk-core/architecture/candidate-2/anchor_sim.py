"""Candidate 2's check of refresh at anchors. Extends funnel/working/review/core_sim.py (same model, same worked numbers).

Standard library only. Run:  python -I anchor_sim.py <mode> [paths] [days]
  modes: fork | bmodes | bmix | lag | openrisk | coststep | decay | attrib | fixes | bites | kstop | final | attrib2 | trace | all

MODEL NUMBERS ONLY. Not evidence about a real strategy. $500 seed, $300 floor, eps 1 %, 20-day horizon, FI scalper outcomes,
fat tails, gap days, lot rounding with the shed rule, as in core_sim.py. Base flags are core_sim's CORE ("RSCDBGT" + "OY").

What this adds, as named options on run_path:
  raise_at_anchor  level climbs earned inside a day take effect at the next day's anchor; cuts still act at once.
                   False is core_sim's behaviour (a climb lands on the next trade). This is fork F-A (b)'s one rule.
  lag              1 = the baseline uses the cushion from the anchor before (the strict reading of "applied at the next").
  bmode            how B is computed at the anchor:
                     flat    = sqrt(N(1+(N-1)rho)) on live units, what core_sim actually ran;
                     pure    = sqrt(sum l_i^2 + rho sum_{i!=j} l_i l_j), DP9's "level-weighted" read literally;
                     others  = per unit: self counted at full, the others at their level;
                     climbed = flat for a unit below full level; a unit at full level gets `others`.
  open_risk        True: within a round, each later unit's cushion is reduced by the risk at the stops of the units already in
                   that round (the worst case of "the fourth position sizes from what the first three left").
  live_cushion     True: size also follows the day's realised loss inside the day (a second reading of the book's running loss).
  cost_step        (day, mult, mode, min_fills): true cost steps up at the start of `day`; mode ignore | anchor | live.
                   anchor: the measured cost reaches the sheet at the first anchor with min_fills fills since the step.
                   live:   it reaches the number on the trade where min_fills fills exist (an applier in `live` mode).
                   On arrival the denominator follows and the admission gate re-runs: low end <= 0 after costs refuses the unit.
  decay            (end_edge, trades): true edge moves linearly from its start to end_edge over that many trades per unit.
  edges            per-unit (true, believed) list, for mixed books.
  sized_stop       True: the day stop and taper read the book's sized day sigma (DP22, F26), computed at the anchor from the
                   rounded sizes in force; False is core_sim's budget sigma, which never fires.
  cut_bites        True: a warning whose level step changes no lots (or leaves under one lot) moves the unit to paper at once;
                   results still feed cohorts and CUSUM; a clean cohort brings it back. False is core_sim.
  k_stop           the day stop's multiple (taper starts at 0.52 of it).
  bad_day_p        chance per day of X4-14's day: every unit's true edge is -0.40R all day.
  cut_sheds        True: a unit whose level was cut by a warning and cannot express that level in lots goes to paper (results
                   still feed its cohorts and CUSUM, no money) instead of being lifted back by the level floor. False is core_sim.
"""
import math
import random
import sys

SEED, FLOOR = 500.0, 300.0
Z, HDAYS = 2.5758, 20
RHO, CUT, COST_R = 0.3, 0.3, 0.16
RESERVE, COST_DEN = 0.85, 0.85
TAIL_P, TAIL_R, GAP_DAY_P, GAP_R = 0.015, -3.0, 0.02, -3.0
CORE_LEVELS = [0.25, 0.50, 0.75, 1.00]
LOT = 0.5
K_STOP = 2.5


def outcomes(edge):
    loss = 0.5 * CUT + 0.5
    p = (edge + loss) / (1.0 + loss)
    return p, (1 - p) / 2


def spread(edge):
    p, q = outcomes(edge)
    m2 = p + q * CUT * CUT + q
    return math.sqrt(m2 - edge * edge)


def card(edge, n, rng, days=3000):
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


def b_flat(n):
    return math.sqrt(n * (1 + (n - 1) * RHO))


def b_pure(ls):
    s2 = sum(x * x for x in ls)
    s1 = sum(ls)
    return math.sqrt(max(1e-9, s2 + RHO * (s1 * s1 - s2)))


def b_others(ls, i):
    rest = [x for j, x in enumerate(ls) if j != i]
    s2 = sum(x * x for x in rest)
    s1 = sum(rest)
    return math.sqrt(1 + s2 + 2 * RHO * s1 + RHO * (s1 * s1 - s2))


def run_path(flags, true_edge, believed, N, cm, rng, thr1, s_plan, rate=10,
             raise_at_anchor=False, lag=0, bmode="flat", open_risk=False, live_cushion=False,
             cost_step=None, decay=None, edges=None, days=120, gapdays=True, tails=True, sized_stop=False, cut_sheds=False, cut_bites=False, k_stop=K_STOP, bad_day_p=0.0):
    has = lambda f: f in flags
    n = rate
    units_true = [e[0] for e in edges] if edges else [true_edge] * N
    units_bel = [e[1] for e in edges] if edges else [believed] * N
    extra = (cm - 1.0) * COST_R
    levels = CORE_LEVELS
    start = [1 if b - 0.05 > 0 else 0 for b in units_bel] if has("S") else [len(levels) - 1] * N
    eq = SEED
    prev_d = SEED - FLOOR
    H = n * HDAYS
    w = max(1, math.ceil(10 / n))
    cohort = 25
    lvl = list(start)
    pending_up = [0] * N
    live = [True] * N
    paper_until = [-1] * N
    co_n = [0] * N
    co_r = [0.0] * N
    cusum = [0.0] * N
    warns = [[] for _ in range(N)]
    bench_until = [-1] * N
    bench_days = [[] for _ in range(N)]
    lock_top = [len(levels) - 1] * N
    lock_until = [-1] * N
    refused = [False] * N
    hist = [[] for _ in range(N)]
    trades = 0
    per_unit_trades = [0] * N
    sum_frac, n_frac = 0.0, 0
    skipped, attempted = 0, 0
    stop_fires = 0
    min_share = 1.0
    start_cushion = SEED - FLOOR
    fills_since = [0] * N
    cost_known = 1.0
    step_day, step_mult, step_mode, step_fills = cost_step if cost_step else (None, 1.0, "ignore", 0)
    lost_in_lag = 0.0
    worst_day, bad_loss, bad_n = 0.0, 0.0, 0
    cut_flag = [False] * N
    on_paper = [False] * N
    for day in range(days):
        true_cm = cm * (step_mult if (step_day is not None and day >= step_day) else 1.0)
        extra = (true_cm - 1.0) * COST_R
        if cost_step and step_mode == "anchor" and day > step_day and cost_known == 1.0 and all(
                fills_since[i] >= step_fills or not live[i] for i in range(N)):
            cost_known = step_mult
        cost_den_now = (1 / (1 + COST_R * cost_known)) / (1 / (1 + COST_R)) * COST_DEN
        for i in range(N):
            low_after = units_bel[i] - 0.05 - (cost_known - 1.0) * COST_R
            refused[i] = bool(cost_step) and cost_known > 1.0 and low_after <= 0
        # --- the anchor: climbs earned yesterday land here; the sheet is written ---
        if raise_at_anchor:
            for i in range(N):
                if pending_up[i] and lvl[i] < lock_top[i]:
                    lvl[i] = min(lock_top[i], lvl[i] + pending_up[i])
                pending_up[i] = 0
        D_now = max(eq - FLOOR, 0.0)
        D = prev_d if lag else D_now
        prev_d = D_now
        order = sorted(range(N), key=lambda i: -i)
        N_live = max(1, sum(1 for i in range(N) if live[i] and day >= paper_until[i]))

        def base_for(nl):
            return D / (s_plan * Z * math.sqrt(H) * b_flat(nl)) * ((RESERVE * cost_den_now) if has("R") else 1.0)

        base = base_for(N_live)
        sigma_book = D / (Z * math.sqrt(HDAYS))
        if has("Y") and has("O"):
            for i in order:
                if live[i] and base * levels[lvl[i]] < 2 * LOT and N_live > 1:
                    live[i] = False
                    N_live -= 1
                    base = base_for(N_live)
            for i in range(N):
                if not live[i]:
                    b2 = base_for(N_live + 1)
                    if b2 * levels[lvl[i]] >= 2 * LOT:
                        live[i] = True
                        N_live += 1
                        base = b2
            for i in range(N):
                if live[i] and base * levels[lvl[i]] < LOT <= base * levels[-1]:
                    if cut_sheds and cut_flag[i]:
                        on_paper[i] = True
                    else:
                        while base * levels[lvl[i]] < LOT:
                            lvl[i] += 1
                elif cut_sheds and on_paper[i] and base * levels[lvl[i]] >= LOT:
                    on_paper[i] = False
        # per-unit size at level 1.00 under the B mode, written once for the day
        active = [i for i in range(N) if live[i] and day >= paper_until[i]]
        ls_active = [levels[lvl[i]] for i in active]
        unit_base = {}
        for pos, i in enumerate(active):
            if bmode == "flat":
                b = b_flat(max(1, len(active)))
            elif bmode == "pure":
                b = b_pure(ls_active)
            elif bmode == "others":
                b = b_others(ls_active, pos)
            elif bmode == "climbed":
                b = b_others(ls_active, pos) if levels[lvl[i]] >= levels[-1] else b_flat(max(1, len(active)))
            unit_base[i] = D / (s_plan * Z * math.sqrt(H) * b) * ((RESERVE * cost_den_now) if has("R") else 1.0)
        if sized_stop:
            sizes = [LOT * math.floor(unit_base[i] * levels[lvl[i]] / LOT) for i in active if not on_paper[i]]
            s2 = sum(x * x for x in sizes)
            s1 = sum(sizes)
            sigma_book = max(LOT, s_plan * math.sqrt(n) * math.sqrt(max(0.0, s2 + RHO * (s1 * s1 - s2))))
        for i in range(N):
            if lock_until[i] >= 0 and day > lock_until[i]:
                lock_top[i], lock_until[i] = len(levels) - 1, -1
        day_money = 0.0
        pnl = [sum(hist[i][-(w - 1):]) if w > 1 else 0.0 for i in range(N)]
        day_r = [0.0] * N
        benched = [False] * N
        book_day = 0.0
        stopped = False
        gap_today = gapdays and rng.random() < GAP_DAY_P
        bad_today = rng.random() < bad_day_p
        d_start = max(eq - FLOOR, 1e-9)
        for t in range(n):
            if stopped:
                break
            common = rng.random() if N > 1 else None
            round_open = 0.0
            for i in range(N):
                if not live[i] or day < paper_until[i] or benched[i] or day < bench_until[i]:
                    continue
                if refused[i]:
                    attempted += 1
                    skipped += 1
                    continue
                if cost_step and step_mode == "live" and day >= step_day and cost_known == 1.0 \
                        and min(fills_since[j] for j in range(N) if live[j]) >= step_fills:
                    cost_known = step_mult
                    low_after = units_bel[i] - 0.05 - (cost_known - 1.0) * COST_R
                    if low_after <= 0:
                        refused = [True] * N
                        attempted += 1
                        skipped += 1
                        continue
                te = units_true[i]
                if decay:
                    frac_done = min(1.0, per_unit_trades[i] / decay[1])
                    te = te + (decay[0] - te) * frac_done
                p, q = outcomes(-0.40 if bad_today else te)
                if gap_today and t == 0:
                    x = GAP_R - extra
                else:
                    u = common if (common is not None and rng.random() < RHO) else rng.random()
                    if u < p:
                        x = 1.0
                    elif u < p + q:
                        x = -CUT
                    else:
                        x = -1.0
                        if tails and rng.random() < TAIL_P:
                            x = TAIL_R
                    x -= extra
                frac = levels[lvl[i]]
                ub = unit_base.get(i, base)
                size = ub * frac
                if open_risk and D > 0:
                    size *= max(0.0, (D - round_open) / D)
                if live_cushion and D > 0:
                    size *= max(0.0, min(1.0, (D + min(0.0, book_day)) / D))
                if has("T") and sigma_book > 0:
                    z_day = book_day / sigma_book
                    k_lo = 0.52 * k_stop
                    if z_day < -k_lo:
                        size *= max(0.25, 1.0 - 0.75 * (-k_lo - z_day) / (k_stop - k_lo))
                attempted += 1
                if on_paper[i]:
                    size = 0.0
                elif has("O"):
                    size = LOT * math.floor(size / LOT)
                    if size < LOT:
                        skipped += 1
                        continue
                day_money += size * x
                book_day += size * x
                round_open += size
                if not on_paper[i]:
                    sum_frac += size / max(base, 1e-9)
                    n_frac += 1
                trades += 1
                per_unit_trades[i] += 1
                if cost_step and day >= step_day:
                    fills_since[i] += 1
                    if cost_known == 1.0 and true_cm > cm:
                        lost_in_lag += size * extra
                day_r[i] += x
                pnl[i] += x
                b_i = units_bel[i]
                if has("D"):
                    cusum[i] = max(0.0, cusum[i] + (b_i - 0.05 - x))
                    if cusum[i] >= 17.0:
                        cusum[i] = 0.0
                        warns[i] = [v for v in warns[i] if trades - v <= 500] + [trades]
                        if len(warns[i]) >= 2:
                            paper_until[i] = days + 1
                        before = LOT * math.floor(unit_base.get(i, base) * levels[lvl[i]] / LOT)
                        lvl[i] = max(0, lvl[i] - 1)
                        after = LOT * math.floor(unit_base.get(i, base) * levels[lvl[i]] / LOT)
                        pending_up[i] = 0
                        cut_flag[i] = True
                        if cut_bites and (after >= before or after < LOT):
                            on_paper[i] = True
                if has("C"):
                    co_n[i] += 1
                    co_r[i] += x
                    if co_n[i] >= cohort:
                        bad = co_r[i] <= -0.2 * cohort * s_plan
                        co_n[i], co_r[i] = 0, 0.0
                        if not bad:
                            cut_flag[i] = False
                            if cut_bites:
                                on_paper[i] = False
                        if not bad and lvl[i] < lock_top[i]:
                            if raise_at_anchor:
                                pending_up[i] = 1  # one level per anchor at most
                            else:
                                lvl[i] += 1
                if has("B") and pnl[i] <= thr1[i] and not benched[i]:
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
                        pending_up[i] = 0
            if has("G") and sigma_book > 0 and book_day <= -k_stop * sigma_book:
                stopped = True
                stop_fires += 1
            if eq + day_money - FLOOR <= 0:
                return dict(eq=FLOOR, min_share=0.0, frac=(sum_frac / n_frac if n_frac else 0.0), touch=True,
                            fires=stop_fires, dark=(skipped / attempted if attempted else 0.0), lag_cost=lost_in_lag,
                            worst_day=1.0, bad_loss=0.0, bad_n=0)
        worst_day = max(worst_day, -day_money / d_start)
        if bad_today:
            bad_loss += -day_money / d_start
            bad_n += 1
        eq += day_money
        for i in range(N):
            hist[i].append(day_r[i])
        min_share = min(min_share, (eq - FLOOR) / start_cushion)
    return dict(eq=eq, min_share=min_share, frac=(sum_frac / n_frac if n_frac else 0.0), touch=False,
                fires=stop_fires, dark=(skipped / attempted if attempted else 0.0), lag_cost=lost_in_lag,
                worst_day=worst_day, bad_loss=bad_loss, bad_n=bad_n)


def pct(xs, q):
    s = sorted(xs)
    return s[min(len(s) - 1, int(q * len(s)))]


CASES = [
    ("HEALTHY +0.10R", 0.10, 0.10),
    ("WEAK +0.05R", 0.05, 0.05),
    ("OVERSTATED +0.03R, card +0.10R", 0.03, 0.10),
    ("BLEEDING -0.05R, card +0.10R", -0.05, 0.10),
]
CORE = "RSCDBGTOY"


def row(name, out, paths, days):
    eqs = [o["eq"] for o in out]
    print(f"  {name:<34} {pct(eqs,0.5):8.0f} {pct(eqs,0.1):7.0f} {100*sum(1 for o in out if o['min_share']<0.5)/paths:6.1f}% "
          f"{100*sum(1 for o in out if o['touch'])/paths:5.1f}% {sum(o['frac'] for o in out)/paths:9.2f} "
          f"{100*sum(o['fires'] for o in out)/paths/days:7.1f} {100*sum(o['dark'] for o in out)/paths:6.1f}"
          + (f" {sum(o['lag_cost'] for o in out)/paths:8.2f}" if any(o["lag_cost"] for o in out) else ""))


def head(title):
    print(f"\n{title}")
    print(f"  {'arm':<34} {'median$':>8} {'p10$':>7} {'<50%cu':>7} {'touch':>6} {'size/base':>9} {'st/100d':>7} {'dark%':>6}")


def cell(title, te, be, N, cm, arms, paths, days, rate=10, **common):
    rng0 = random.Random(11)
    _, t1 = card(be, rate, rng0)
    s = spread(be)
    head(f"{title} [N={N} cost x{cm} rate={rate}/day days={days} paths={paths}; card p1={t1:.1f}R]")
    for k, (name, flags, opts) in enumerate(arms):
        rng = random.Random(1000 + k * 0 + N)  # the same stream of seeds for every arm
        kw = dict(common)
        kw.update(opts)
        out = [run_path(flags, te, be, N, cm, rng, [t1] * N, s, rate=rate, days=days, **kw) for _ in range(paths)]
        row(name, out, paths, days)


def mode_fork(paths, days):
    arms = [("as core_sim (climb on next trade)", CORE, {}),
            ("refresh: raises wait for the anchor", CORE, {"raise_at_anchor": True})]
    for N in (1, 5, 10):
        for cm in (1.0, 1.5):
            for t, te, be in CASES:
                cell(t, te, be, N, cm, arms, paths, days)
    for t, te, be in CASES[:2]:
        cell(t, te, be, 10, 1.0, arms, paths, days, rate=40)
        cell(t, te, be, 1, 1.0, arms, paths, days, rate=2)


def mode_bmodes(paths, days):
    arms = [("B flat on live units (as simmed)", CORE, {"raise_at_anchor": True}),
            ("B pure level-weighted (DP9 literal)", CORE, {"raise_at_anchor": True, "bmode": "pure"}),
            ("B others at level, self at full", CORE, {"raise_at_anchor": True, "bmode": "others"}),
            ("B freed swing only to full level", CORE, {"raise_at_anchor": True, "bmode": "climbed"})]
    for N in (1, 5, 10):
        for t, te, be in CASES:
            cell(t, te, be, N, 1.0, arms, paths, days)
    for t, te, be in CASES:
        cell(t, te, be, 10, 1.0, arms, paths, days, rate=2)


def mode_bmix(paths, days):
    """A mixed book: 2 healthy, 8 overstated-and-thin. Does freed swing reach the proved units, and what does it cost?"""
    rng0 = random.Random(11)
    mix = [(0.10, 0.10)] * 2 + [(0.03, 0.05)] * 8
    thr = []
    for _, b in mix:
        _, t1 = card(b, 10, rng0)
        thr.append(t1)
    s = spread(0.10)
    head(f"MIX 2 healthy + 8 thin [N=10 rate=10/day days={days} paths={paths}]")
    for name, kw in [("B flat", {}), ("B pure", {"bmode": "pure"}), ("B others", {"bmode": "others"}), ("B climbed", {"bmode": "climbed"})]:
        rng = random.Random(77)
        out = [run_path(CORE, 0, 0, 10, 1.0, rng, thr, s, raise_at_anchor=True, edges=mix, days=days, **kw) for _ in range(paths)]
        row(name, out, paths, days)


def mode_lag(paths, days):
    arms = [("evidence to anchor k, in force from k", CORE, {"raise_at_anchor": True}),
            ("strict: in force one anchor later", CORE, {"raise_at_anchor": True, "lag": 1})]
    for N in (1, 10):
        for t, te, be in CASES:
            cell(t, te, be, N, 1.0, arms, paths, days)


def mode_openrisk(paths, days):
    arms = [("anchor cushion only", CORE, {"raise_at_anchor": True}),
            ("+ open risk deducted live", CORE, {"raise_at_anchor": True, "open_risk": True}),
            ("+ day's realised loss deducted live", CORE, {"raise_at_anchor": True, "open_risk": True, "live_cushion": True})]
    for N in (1, 5, 10):
        for t, te, be in CASES:
            cell(t, te, be, N, 1.0, arms, paths, days)


def mode_coststep(paths, days):
    """X4-39: the broker's cost steps up overnight before day 60."""
    for rate in (10, 40):
        for mult in (1.5, 2.0):
            arms = [("sizer ignores it", CORE, {"raise_at_anchor": True, "cost_step": (60, mult, "ignore", 20)}),
                    ("refresh: at the anchor after 20 fills", CORE, {"raise_at_anchor": True, "cost_step": (60, mult, "anchor", 20)}),
                    ("applier live: on the 20th fill", CORE, {"raise_at_anchor": True, "cost_step": (60, mult, "live", 20)})]
            for N in (1, 10):
                for t, te, be in CASES[:2]:
                    cell(f"{t}, cost x{mult} from day 60", te, be, N, 1.0, arms, paths, days, rate=rate)


def mode_decay(paths, days):
    """X4-60: edge fades linearly to +0.01R over 400 then 1,200 trades."""
    for trades in (400, 1200):
        arms = [("as core_sim (climb on next trade)", CORE, {"decay": (0.01, trades)}),
                ("refresh: raises wait for the anchor", CORE, {"decay": (0.01, trades), "raise_at_anchor": True})]
        for N in (1, 10):
            cell(f"DECAY +0.10R to +0.01R over {trades} trades", 0.10, 0.10, N, 1.0, arms, paths, days)


def mode_fixes(paths, days):
    base = {"raise_at_anchor": True}
    arms = [("refresh, budget sigma (core_sim)", CORE, dict(base)),
            ("+ day stop on sized sigma k2.5", CORE, dict(base, sized_stop=True)),
            ("+ a cut unit goes to paper, not lifted", CORE, dict(base, cut_sheds=True)),
            ("+ both", CORE, dict(base, sized_stop=True, cut_sheds=True))]
    for N in (1, 5, 10):
        for cm in (1.0, 1.5):
            for t, te, be in CASES:
                cell(t, te, be, N, cm, arms, paths, days)


def mode_bites(paths, days):
    base = {"raise_at_anchor": True}
    arms = [("refresh", CORE, dict(base)), ("+ a cut that changes no lots goes to paper", CORE, dict(base, cut_bites=True))]
    for N in (1, 5, 10):
        for cm in (1.0, 1.5):
            for t, te, be in CASES:
                cell(t, te, be, N, cm, arms, paths, days)


def mode_kstop(paths, days):
    """The day stop's fire rate, and what it saves on X4-14's day (about two such days a year in this run)."""
    print("k = day stop multiple on the book's sized day sigma. bad-day loss = mean share of the morning's cushion lost on an X4-14 day.")
    for N in (1, 5, 10):
        for t, te, be in CASES[:2] + CASES[3:]:
            rng0 = random.Random(11)
            _, t1 = card(be, 10, rng0)
            s = spread(be)
            print()
            print(f"{t} [N={N} days={days} paths={paths}, X4-14 day at 1 % of days]")
            print(f"  {'arm':<30} {'median$':>8} {'size/base':>9} {'stops/100d':>10} {'bad-day loss':>12} {'worst day':>9} {'<50%cu':>7}")
            for name, kw in [("no day stop", dict(k_stop=99.0, sized_stop=True)),
                             ("budget sigma k2.5", dict(k_stop=2.5)),
                             ("sized sigma k2.5", dict(k_stop=2.5, sized_stop=True)),
                             ("sized sigma k2.0", dict(k_stop=2.0, sized_stop=True)),
                             ("sized sigma k1.5", dict(k_stop=1.5, sized_stop=True))]:
                rng = random.Random(500 + N)
                out = [run_path(CORE, te, be, N, 1.0, rng, [t1] * N, s, days=days, raise_at_anchor=True, bad_day_p=0.01, **kw) for _ in range(paths)]
                eqs = [o["eq"] for o in out]
                bad = sum(o["bad_loss"] for o in out) / max(1, sum(o["bad_n"] for o in out))
                print(f"  {name:<30} {pct(eqs,0.5):8.0f} {sum(o['frac'] for o in out)/paths:9.2f} {100*sum(o['fires'] for o in out)/paths/days:10.2f} "
                      f"{100*bad:11.1f}% {100*pct([o['worst_day'] for o in out],0.5):8.1f}% {100*sum(1 for o in out if o['min_share']<0.5)/paths:6.1f}%")


def mode_final(paths, days):
    """This candidate's design against the funnel's core as core_sim ran it, and the choke budget (0.75)."""
    design = dict(raise_at_anchor=True, open_risk=True, bmode="climbed", sized_stop=True, k_stop=1.7)
    arms = [("funnel core as core_sim ran it", CORE, {}),
            ("candidate 2", CORE, design)]
    for N in (1, 3, 5, 10):
        for cm in (1.0, 1.5):
            for t, te, be in CASES:
                cell(t, te, be, N, cm, arms, paths, days)


def mode_attrib2(paths, days):
    """Every binding factor the sim holds, added one at a time, in the order the design applies them."""
    arms = [("sizer: cushion, spread, B, reserve, cost", "ROY", dict(bmode="climbed")),
            ("+ start level from holdout", "RSOY", dict(bmode="climbed")),
            ("+ cohort climb, raises at anchor", "RSCOY", dict(bmode="climbed", raise_at_anchor=True)),
            ("+ CUSUM step, second warning to paper", "RSCDOY", dict(bmode="climbed", raise_at_anchor=True)),
            ("+ unit bench, retry-lockout", "RSCDBOY", dict(bmode="climbed", raise_at_anchor=True)),
            ("+ day stop, sized sigma k1.7", "RSCDBGOY", dict(bmode="climbed", raise_at_anchor=True, sized_stop=True, k_stop=1.7)),
            ("+ pair's taper into it", "RSCDBGTOY", dict(bmode="climbed", raise_at_anchor=True, sized_stop=True, k_stop=1.7)),
            ("+ open risk deducted live", "RSCDBGTOY", dict(bmode="climbed", raise_at_anchor=True, sized_stop=True, k_stop=1.7, open_risk=True))]
    for N in (1, 5, 10):
        for t, te, be in [CASES[0], CASES[1], CASES[3]]:
            cell(t, te, be, N, 1.0, arms, paths, days)


def mode_attrib(paths, days):
    arms = [("sizer+reserve", "ROY", {}),
            ("+start level from holdout", "RSOY", {}),
            ("+cohort climb, raises at anchor", "RSCOY", {"raise_at_anchor": True}),
            ("+CUSUM step-down", "RSCDOY", {"raise_at_anchor": True}),
            ("+unit bench, retry-lockout", "RSCDBOY", {"raise_at_anchor": True}),
            ("+day stop", "RSCDBGOY", {"raise_at_anchor": True}),
            ("+pair's taper", "RSCDBGTOY", {"raise_at_anchor": True}),
            ("+open risk deducted live", "RSCDBGTOY", {"raise_at_anchor": True, "open_risk": True})]
    for N in (1, 5, 10):
        for t, te, be in CASES:
            cell(t, te, be, N, 1.0, arms, paths, days)


def mode_trace():
    """One order, by hand, with the worked example's numbers: every factor in order."""
    for name, be, level in [("healthy", 0.10, 1.00), ("weak", 0.05, 0.75), ("bleeding (card +0.10R, CUSUM stepped once)", 0.10, 0.50)]:
        for N in (1, 10):
            D = 200.0
            s = spread(be)
            H = 10 * HDAYS
            B = b_flat(N)
            raw = D / (s * Z * math.sqrt(H) * B)
            res = raw * RESERVE
            den = res * COST_DEN
            lv = den * level
            taper = 1.0
            final = LOT * math.floor(lv * taper / LOT)
            print(f"{name:<44} N={N:<3} D=${D:.0f} s={s:.3f} z={Z} H={H} B={B:.2f}: base ${raw:.2f}; reserve 0.85 ${res:.2f}; "
                  f"cost den 0.85 ${den:.2f}; level {level:.2f} ${lv:.2f}; taper 1.00; lot ${LOT} -> ${final:.2f}; "
                  f"sigma_book ${D/(Z*math.sqrt(HDAYS)):.2f}, day stop at -${K_STOP*D/(Z*math.sqrt(HDAYS)):.2f}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "fork"
    paths = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    table = {"fork": mode_fork, "bmodes": mode_bmodes, "bmix": mode_bmix, "lag": mode_lag, "openrisk": mode_openrisk,
             "coststep": mode_coststep, "decay": mode_decay, "attrib": mode_attrib, "fixes": mode_fixes, "bites": mode_bites, "kstop": mode_kstop, "final": mode_final, "attrib2": mode_attrib2}
    if mode == "trace":
        mode_trace()
    elif mode == "all":
        for f in table.values():
            f(paths, days)
    else:
        table[mode](paths, days)
