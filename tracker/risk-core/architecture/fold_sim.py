"""The fold's integrated check: the funnel's harder sim (funnel/working/review/core_sim.py) with only what the
fold changed, plus the three graft verifications the fold rests on.

Standard library only. Run from anywhere:
    python -I fold_sim.py fold [paths] [days]          the folded design against the funnel's core, N = 1, 5, 10
    python -I fold_sim.py verify-drift [paths]         candidate 3's finding: healthy units sent to paper by two warnings
    python -I fold_sim.py verify-b [paths]             candidate 2's finding: DP9's level-weighted B cancels the level at N = 1
    python -I fold_sim.py verify-k [paths]             candidate 2's finding: k on the sized sigma, fire rate against bad-day loss
    python -I fold_sim.py choke [paths] [days]         the last round: dollars risked over baseline on every opportunity,
                                                       the admission gate and net_r as fixed (SPINE AD-12, AD-16, 4.4)

MODEL NUMBERS ONLY. Not evidence about a real strategy. The worked example as the funnel and the review: $500 seed,
$300 floor, eps 1 %, 20-day horizon, 10 trades a day per unit, FI scalper outcomes, fat tails, gap days, lot
rounding at $0.50 with the shed rule. core_sim.py is imported for its constants, card, spread, outcomes and draw;
run_path below is core_sim's CORE arm (flags RSCDBGT + OY) written out with the fold's three changes as options:

  drift rule      warnings_to_paper = 2 is the funnel's rule (a second CUSUM warning inside the window moves the unit
                  to paper); 3 is the fold's (every warning is one level down, the third inside the window is paper).
                  The window counts the unit's own trades (core_sim counted every unit's trades together).
  day stop's k    k_mode "budget" is core_sim's (k 2.5 on the budget sigma, which never fires, F26); "sized" reads the
                  book's sized day sigma from the rounded sizes in force; k itself is either a fixed rung or derived
                  as minus the group's own p1 day in sized-sigma units from the cards (k_own_p1).
  freed swing     b_mode "flat" is core_sim's B on the live count; "pure" is DP9 read literally (cancels the level at
                  N = 1); "freed" gives a unit at level 1.00 the swing the others leave idle and keeps a unit below
                  full on flat B.
  raises at anchor a level earned inside a day lands at the next day's anchor (graft 9); cuts act at once.

The last round's options, all off by default so the older modes give the same bytes (mode choke turns them on):
  alloc_days       the cushion is re-read every day; N, B, the shed rule and re-admission only every alloc_days (7 is the
                   weekly allocation anchor, SPINE 4.3). Between anchors a unit that leaves just stops trading.
  admission        SPINE 4.4 as fixed: the card's net low end decides at the door (below zero refused, at zero start 0.25,
                   above zero start 0.50); an hour cell refuses only when its own fills show net edge below zero (at least
                   MIN_CELL fills and the band's high end under zero), read at the day anchor. A refused cell keeps counting
                   its would-have results, so it can come back. In this model the hours are identical, so every refusal
                   of a healthy unit is a false one. HOURS and MIN_CELL are model choices, not values.
  click_days       a lockout (third bench inside 40 days) waits this many days for his click; None is the older sim's
                   20-day return. A large number is a click that never comes.
  floor_at_lock    the level floor (FUNNEL DP13) stops at a lock's top instead of lifting through it.
  open_share       the sizer's live share (SPINE 4.3): a unit's dollars x (cushion - open risk) / cushion, with every
                   earlier entry in the same slot still open, which is the worst case for a scalper.
  hold_n           N does not rise at an allocation anchor under a caution. "group" (the rule as the spine now words it): no rise
                   after a day stop since the last anchor, and a unit that is itself benched or locked is not re-admitted.
                   "wide": any bench or lock on any unit freezes N for all.
  gate_refuse      a share of opportunities SQS and news refuse. A guess: neither has real data yet.
  read_extra       R per trade the brakes' stream reads below the money: B1's double count when it is above zero.

The metric (check_sim's "opp"): dollars risked over what the unit would risk at the flat baseline of its own N on EVERY
opportunity, rate x N x days. A refused, benched, stopped, shed, paper or sub-lot opportunity counts as zero. opp_cap caps
each trade at the flat baseline of the live N, so freed swing cannot hide a cut.
"""
from __future__ import annotations

import math
import os
import random
import sys

ARGS = sys.argv[1:]
sys.argv = sys.argv[:1]  # core_sim reads argv at import
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "funnel", "working", "review")))
import core_sim as cs  # noqa: E402

LOT = cs.LOT
LEVELS = cs.CORE_LEVELS
HOURS = 8  # hour cells a unit's day falls into; a model choice
MIN_CELL = 60  # fills a cell needs before it may refuse; calibration_min_trades' stated value, the numbers lens owns it
CELL_Z = 1.645  # one-sided 95 % on the cell's own mean; the numbers lens owns it
NEVER = 10**6


def b_flat(n: int) -> float:
    return math.sqrt(n * (1 + (n - 1) * cs.RHO))


def b_pure(ls: list[float]) -> float:
    s2 = sum(x * x for x in ls)
    s1 = sum(ls)
    return math.sqrt(max(1e-9, s2 + cs.RHO * (s1 * s1 - s2)))


def b_others(ls: list[float], i: int) -> float:
    rest = [x for j, x in enumerate(ls) if j != i]
    s2 = sum(x * x for x in rest)
    s1 = sum(rest)
    return math.sqrt(1 + s2 + 2 * cs.RHO * s1 + cs.RHO * (s1 * s1 - s2))


def k_own_p1(N: int, believed: float, rng: random.Random, rate: int = cs.RATE, days: int = 4000, tails: bool = True,
             target: float = 0.01) -> float:
    """The day stop's k as the fold derives it: the group's own bad day at the target fire rate (default one day in a
    hundred), in units of the sized day sigma, drawn from the cards at equal sizes (the allocation anchor's view) with
    the class's tail rows on (fat tails and gap days, as the harness would draw them from worst_step_move_r and
    gap_loss_beyond_stop). The result is a dollar line: k x sigma equals that day's loss whatever the sigma's own bias,
    so a stressed correlation in the sigma does not move the line. A first version without the tails gave k 1.0 at
    N = 10 and fired on most weeks; that run is kept in out-fold-notails.txt."""
    p, q = cs.outcomes(believed)
    s = cs.spread(believed)
    sigma = s * math.sqrt(rate) * b_flat(N)
    sums = []
    for _ in range(days):
        total = 0.0
        gap_today = tails and rng.random() < cs.GAP_DAY_P
        for t in range(rate):
            common = rng.random() if N > 1 else None
            for _i in range(N):
                total += cs.GAP_R if (gap_today and t == 0) else cs.draw(rng, p, q, common, tails, 0.0)
        sums.append(total)
    sums.sort()
    return max(0.5, -sums[int(target * days)] / sigma)


def run_path(true_edge, believed, N, cm, rng, thr1, s_plan, *, days=120, raise_at_anchor=False, b_mode="flat",
             k_mode="budget", k_stop=2.5, warnings_to_paper=2, warn_window=500, drift_lock=False, drift_lock_after=1,
             drift_lock_days=None, alloc_days=1, admission=False, click_days=None, floor_at_lock=False, open_share=False,
             hold_n=False, gate_refuse=0.0, read_extra=0.0):
    """drift_lock: a warning also locks the level's top at the stepped level until the window has passed since that
    warning, so a unit cannot climb straight back between warnings (the bench's retry-then-lockout, applied to drift).
    drift_lock_after: the lock starts at this warning count inside the window (1 = every warning; 2 = the first
    warning stays reversible by cohorts, the second inside the window locks)."""
    n = cs.RATE
    p, q = cs.outcomes(true_edge)
    extra = (cm - 1.0) * cs.COST_R
    start = 1 if believed - 0.05 > 0 else 0
    eq, floor = cs.SEED, cs.FLOOR
    H = n * cs.HDAYS
    w = max(1, math.ceil(10 / n))
    if admission and believed - 0.05 < 0:
        return dict(eq=eq, min_share=1.0, frac=0.0, touch=False, fires=0, dark=0.0, shed=0, paper=0.0, opp=0.0, opp_cap=0.0,
                    live=0.0, locks=0, outcomes={"door": n * N * days}, stream=0.0, refused_door=True)
    cell_n = [[0] * HOURS for _ in range(N)]
    cell_sum = [[0.0] * HOURS for _ in range(N)]
    cell_shut = [[False] * HOURS for _ in range(N)]
    alloc_b = {}
    alloc_n = 1
    fired_since = False
    risked = capped = wanted = 0.0
    live_sum = 0.0
    locks = 0
    stream_sum, stream_n = 0.0, 0
    outcomes = dict(taken=0, skip=0, off=0, bench=0, stop=0, cell=0, gate=0)
    lvl = [start] * N
    pending_up = [0] * N
    live = [True] * N
    paper_until = [-1] * N
    co_n, co_r = [0] * N, [0.0] * N
    cusum = [0.0] * N
    warns = [[] for _ in range(N)]
    unit_trades = [0] * N
    bench_until = [-1] * N
    bench_days = [[] for _ in range(N)]
    lock_top = [len(LEVELS) - 1] * N
    lock_until = [-1] * N
    hist = [[] for _ in range(N)]
    sum_frac, n_frac = 0.0, 0
    skipped, attempted = 0, 0
    stop_fires, shed_total, lifts = 0, 0, 0
    min_share = 1.0
    start_cushion = cs.SEED - cs.FLOOR
    drift_paper = [False] * N
    for day in range(days):
        if raise_at_anchor:
            for i in range(N):
                if pending_up[i] and lvl[i] < lock_top[i]:
                    lvl[i] = min(lock_top[i], lvl[i] + 1)
                pending_up[i] = 0
        D = max(eq - floor, 0.0)
        at_alloc = day % alloc_days == 0
        N_live = max(1, sum(1 for i in range(N) if live[i] and day >= paper_until[i])) if at_alloc else alloc_n

        def base_for(nl):
            return D / (s_plan * cs.Z * math.sqrt(H) * b_flat(nl)) * cs.RESERVE * cs.COST_DEN

        base = base_for(N_live)
        sigma_book = D / (cs.Z * math.sqrt(cs.HDAYS))
        # the M9 shed rule and the level floor, as core_sim; N and B move only at the allocation anchor
        if at_alloc:
            caution = hold_n == "wide" and any(lock_until[i] >= day or day < bench_until[i] for i in range(N))
            caution = caution or (hold_n and fired_since)
            for i in sorted(range(N), key=lambda i: -i):
                if live[i] and base * LEVELS[lvl[i]] < 2 * LOT and N_live > 1:
                    live[i] = False
                    shed_total += 1
                    N_live -= 1
                    base = base_for(N_live)
            if not caution:
                for i in range(N):
                    if not live[i] and not (hold_n and (lock_until[i] >= day or day < bench_until[i])):
                        b2 = base_for(N_live + 1)
                        if b2 * LEVELS[lvl[i]] >= 2 * LOT:
                            live[i] = True
                            N_live += 1
                            base = b2
            fired_since = False
        for i in range(N):
            if live[i] and base * LEVELS[lvl[i]] < LOT <= base * LEVELS[-1]:
                top = lock_top[i] if floor_at_lock else len(LEVELS) - 1
                while base * LEVELS[lvl[i]] < LOT and lvl[i] < top:
                    lvl[i] += 1
                lifts += 1
        # per-unit baseline at level 1.00 under the B mode
        active = [i for i in range(N) if live[i] and day >= paper_until[i]]
        if at_alloc:
            ls = [LEVELS[lvl[i]] for i in active]
            alloc_b = {}
            for pos, i in enumerate(active):
                if b_mode == "flat":
                    alloc_b[i] = b_flat(max(1, len(active)))
                elif b_mode == "pure":
                    alloc_b[i] = b_pure(ls)
                else:  # freed: a unit at full level takes the swing the others leave; a unit below full stays flat
                    alloc_b[i] = b_others(ls, pos) if LEVELS[lvl[i]] >= LEVELS[-1] else b_flat(max(1, len(active)))
            alloc_n = max(1, len(active))
        else:
            active = [i for i in active if i in alloc_b]  # back from paper or shed: waits for the anchor (a raise)
            base = base_for(alloc_n)
        unit_base = {i: D / (s_plan * cs.Z * math.sqrt(H) * alloc_b[i]) * cs.RESERVE * cs.COST_DEN for i in active}
        flat_N = base_for(N)  # what each of the N units would risk with nothing shed and nothing cut
        wanted += flat_N * n * N
        live_sum += len(active) / N
        active_set = set(active)
        if admission:  # a cell's verdict moves at the day anchor, never inside the day
            for i in range(N):
                for h in range(HOURS):
                    c = cell_n[i][h]
                    cell_shut[i][h] = c >= MIN_CELL and cell_sum[i][h] / c + CELL_Z * s_plan / math.sqrt(c) < 0.0
        if k_mode == "sized":
            sizes = [LOT * math.floor(unit_base[i] * LEVELS[lvl[i]] / LOT) for i in active]
            s2 = sum(x * x for x in sizes)
            s1 = sum(sizes)
            sigma_book = max(LOT, s_plan * math.sqrt(n) * math.sqrt(max(0.0, s2 + cs.RHO * (s1 * s1 - s2))))
        for i in range(N):
            if lock_until[i] >= 0 and day > lock_until[i]:
                lock_top[i], lock_until[i] = len(LEVELS) - 1, -1
        day_money, book_day, stopped = 0.0, 0.0, False
        day_r = [0.0] * N
        pnl = [sum(hist[i][-(w - 1):]) if w > 1 else 0.0 for i in range(N)]
        benched = [False] * N
        gap_today = rng.random() < cs.GAP_DAY_P
        for t in range(n):
            if stopped:
                for i in range(N):
                    key = "off" if not (live[i] and day >= paper_until[i] and i in active_set) else (
                        "bench" if benched[i] or day < bench_until[i] else "stop")
                    outcomes[key] += 1
                continue
            common = rng.random() if N > 1 else None
            open_now = 0.0
            for i in range(N):
                if not live[i] or day < paper_until[i] or (alloc_days > 1 and i not in active_set):
                    outcomes["off"] += 1
                    continue
                if benched[i] or day < bench_until[i]:
                    outcomes["bench"] += 1
                    continue
                x = (cs.GAP_R - extra) if (gap_today and t == 0) else cs.draw(rng, p, q, common, True, extra)
                if admission:
                    h = t * HOURS // n
                    cell_n[i][h] += 1
                    cell_sum[i][h] += x - read_extra
                    if cell_shut[i][h]:
                        outcomes["cell"] += 1
                        continue
                if gate_refuse and rng.random() < gate_refuse:
                    outcomes["gate"] += 1
                    continue
                size = unit_base.get(i, base) * LEVELS[lvl[i]]
                if open_share and D > 0:
                    size *= max(0.0, D - open_now) / D
                if sigma_book > 0:
                    z_day = book_day / sigma_book
                    k_lo = 0.52 * k_stop
                    if z_day < -k_lo:
                        size *= max(0.25, 1.0 - 0.75 * (-k_lo - z_day) / (k_stop - k_lo))
                attempted += 1
                size = LOT * math.floor(size / LOT)
                if size < LOT:
                    skipped += 1
                    outcomes["skip"] += 1
                    continue
                outcomes["taken"] += 1
                open_now += size
                risked += size
                capped += min(size, base)
                day_money += size * x
                book_day += size * x
                sum_frac += size / max(base, 1e-9)
                n_frac += 1
                unit_trades[i] += 1
                xr = x - read_extra  # net_r as the brakes read it: (money + cash) / risk, the same basis as the card
                stream_sum += xr
                stream_n += 1
                day_r[i] += xr
                pnl[i] += xr
                # the CUSUM: every warning one level down; the count inside the window decides paper
                cusum[i] = max(0.0, cusum[i] + (believed - 0.05 - xr))
                if cusum[i] >= 17.0:
                    cusum[i] = 0.0
                    warns[i] = [v for v in warns[i] if unit_trades[i] - v <= warn_window] + [unit_trades[i]]
                    if len(warns[i]) >= warnings_to_paper:
                        paper_until[i] = days + 1
                        drift_paper[i] = True
                    lvl[i] = max(0, lvl[i] - 1)
                    pending_up[i] = 0
                    if drift_lock and len(warns[i]) >= drift_lock_after:
                        lock_top[i] = min(lock_top[i], lvl[i])
                        hold = drift_lock_days if drift_lock_days is not None else math.ceil(warn_window / n)
                        lock_until[i] = max(lock_until[i], day + hold)
                # cohorts: one level up per clean cohort, landing at the anchor under the fold
                co_n[i] += 1
                co_r[i] += xr
                if co_n[i] >= 25:
                    bad = co_r[i] <= -0.2 * 25 * s_plan
                    co_n[i], co_r[i] = 0, 0.0
                    if not bad and lvl[i] < lock_top[i]:
                        if raise_at_anchor:
                            pending_up[i] = 1
                        else:
                            lvl[i] += 1
                # the unit bench at own p1 with retry-then-lockout
                if pnl[i] <= thr1 and not benched[i]:
                    benched[i] = True
                    bench_until[i] = day + w
                    bench_days[i] = [d for d in bench_days[i] if day - d <= 40] + [day]
                    recent20 = sum(1 for d in bench_days[i] if day - d <= 20)
                    if len(bench_days[i]) >= 3:
                        paper_until[i] = day + (20 if click_days is None else click_days)
                        bench_days[i] = []
                        locks += 1
                    elif recent20 >= 2:
                        lock_top[i], lock_until[i] = max(0, lvl[i] - 1), day + 20
                        lvl[i] = min(lvl[i], lock_top[i])
                        pending_up[i] = 0
            if sigma_book > 0 and book_day <= -k_stop * sigma_book:
                stopped = True
                stop_fires += 1
                fired_since = True
            if eq + day_money - floor <= 0:
                return dict(eq=floor, min_share=0.0, frac=(sum_frac / n_frac if n_frac else 0.0), touch=True,
                            fires=stop_fires, dark=(skipped / attempted if attempted else 0.0), shed=shed_total,
                            paper=sum(drift_paper) / N, opp=risked / max(wanted, 1e-9), opp_cap=capped / max(wanted, 1e-9),
                            live=live_sum / (day + 1), locks=locks, outcomes=outcomes,
                            stream=stream_sum / max(stream_n, 1), refused_door=False)
        eq += day_money
        for i in range(N):
            hist[i].append(day_r[i])
        min_share = min(min_share, (eq - floor) / start_cushion)
    return dict(eq=eq, min_share=min_share, frac=(sum_frac / n_frac if n_frac else 0.0), touch=False,
                fires=stop_fires, dark=(skipped / attempted if attempted else 0.0), shed=shed_total,
                paper=sum(drift_paper) / N, opp=risked / max(wanted, 1e-9), opp_cap=capped / max(wanted, 1e-9),
                live=live_sum / days, locks=locks, outcomes=outcomes, stream=stream_sum / max(stream_n, 1),
                refused_door=False)


def pct(xs, q):
    s = sorted(xs)
    return s[min(len(s) - 1, int(q * len(s)))]


def head(title):
    print(f"\n{title}")
    print(f"  {'arm':<44} {'median$':>8} {'p10$':>7} {'<50%cu':>7} {'touch':>6} {'size/base':>9} {'st/100d':>7} "
          f"{'dark%':>6} {'paper%':>7}")


def row(name, out, paths, days):
    eqs = [o["eq"] for o in out]
    print(f"  {name:<44} {pct(eqs, 0.5):8.0f} {pct(eqs, 0.1):7.0f} "
          f"{100 * sum(1 for o in out if o['min_share'] < 0.5) / paths:6.1f}% "
          f"{100 * sum(1 for o in out if o['touch']) / paths:5.1f}% {sum(o['frac'] for o in out) / paths:9.2f} "
          f"{100 * sum(o['fires'] for o in out) / paths / days:7.2f} {100 * sum(o['dark'] for o in out) / paths:6.1f} "
          f"{100 * sum(o['paper'] for o in out) / paths:6.1f}%")


CASES = [("HEALTHY +0.10R, card +0.10R", 0.10, 0.10), ("WEAK +0.05R, card +0.05R", 0.05, 0.05),
         ("BLEEDING true -0.05R, card +0.10R", -0.05, 0.10)]


def cell(title, te, be, N, cm, arms, paths, days):
    rng0 = random.Random(11)
    _, t1 = cs.card(be, cs.RATE, rng0)
    s = cs.spread(be)
    head(f"{title} [N={N} cost x{cm} days={days} paths={paths}; card p1={t1:.1f}R]")
    for k, (name, opts) in enumerate(arms):
        rng = random.Random(1000 + N)  # the same stream for every arm
        out = [run_path(te, be, N, cm, rng, t1, s, days=days, **opts) for _ in range(paths)]
        row(name, out, paths, days)


def mode_fold(paths, days):
    print("The folded design against the funnel's core as core_sim ran it. size/base = mean size over the flat baseline;"
          " paper% = share of units the drift rule sent to paper inside the run. Model numbers only.")
    for N in (1, 5, 10):
        for title, te, be in CASES:
            k = k_own_p1(N, be, random.Random(7))
            print(f"\n  derived k for N={N}, card {be:+.2f}R: {k:.2f} (minus the group's own p1 day in sized sigmas)")
            arms = [
                ("funnel core: flat B, budget k2.5, 2nd warning paper", dict()),
                ("fold: 3rd warning paper, each warning locks for the window",
                 dict(FOLD_BASE, k_stop=k, warnings_to_paper=3, drift_lock=True)),
                ("fold: 3rd warning paper, each warning locks 20 days",
                 dict(FOLD_BASE, k_stop=k, warnings_to_paper=3, drift_lock=True, drift_lock_days=20)),
            ]
            cell(title, te, be, N, 1.0, arms, paths, days)


FOLD_BASE = dict(raise_at_anchor=True, b_mode="freed", k_mode="sized")


def mode_decompose(paths, days):
    """Each fold change added one at a time on the cases the fold moved most: the bleeding book and the healthy book."""
    print("The fold's changes added one at a time. Model numbers only.")
    for N in (5, 10):
        for title, te, be in (CASES[0], CASES[2]):
            k = k_own_p1(N, be, random.Random(7))
            print(f"\n  derived k for N={N}, card {be:+.2f}R: {k:.2f}")
            arms = [("funnel core (core_sim)", dict()),
                    ("+ raises at the anchor", dict(raise_at_anchor=True)),
                    ("+ freed swing B", dict(raise_at_anchor=True, b_mode="freed")),
                    ("+ sized sigma, k derived", dict(raise_at_anchor=True, b_mode="freed", k_mode="sized", k_stop=k)),
                    ("+ 3rd warning to paper (no lock)", dict(FOLD_BASE, k_stop=k, warnings_to_paper=3)),
                    ("+ 3rd warning to paper, warnings lock the top", dict(FOLD_BASE, k_stop=k, warnings_to_paper=3, drift_lock=True))]
            cell(title, te, be, N, 1.0, arms, paths, days)


def mode_drift_variants(paths, days):
    """The drift rule's shapes on the fold's base: paper rate on one unit, survival on a bleeding book."""
    print("Drift rule variants on the fold's base (raises at anchor, freed B, sized sigma with derived k). Model numbers only.")
    variants = [("2 warnings in 500 -> paper (funnel)", dict(warnings_to_paper=2)),
                ("3 warnings in 500 -> paper", dict(warnings_to_paper=3)),
                ("3 in 500 -> paper; every warning locks the top", dict(warnings_to_paper=3, drift_lock=True)),
                ("3 in 500 -> paper; the 2nd locks the top (retry-then-lockout)", dict(warnings_to_paper=3, drift_lock=True, drift_lock_after=2)),
                ("3 in 500 -> paper; every warning locks 20 days (the bench's lockout)", dict(warnings_to_paper=3, drift_lock=True, drift_lock_days=20)),
                ("2 in 500 -> paper; a warning locks the top", dict(warnings_to_paper=2, drift_lock=True)),
                ("2 warnings in 300 -> paper", dict(warnings_to_paper=2, warn_window=300))]
    cases1 = CASES + [("OVERSTATED true +0.03R, card +0.10R", 0.03, 0.10)]
    for title, te, be in cases1:
        k = k_own_p1(1, be, random.Random(7))
        cell(title, te, be, 1, 1.0, [(n, dict(FOLD_BASE, k_stop=k, **o)) for n, o in variants], paths, days)
    for N in (5, 10):
        for title, te, be in (CASES[0], CASES[2]):
            k = k_own_p1(N, be, random.Random(7))
            cell(title, te, be, N, 1.0, [(n, dict(FOLD_BASE, k_stop=k, **o)) for n, o in variants], max(20, paths // 3), days)


def mode_verify_drift(paths, days):
    print("Candidate 3's finding, re-run: share of one-unit paths the drift rule sends to paper inside the run (N=1).")
    cases = CASES + [("OVERSTATED true +0.03R, card +0.10R", 0.03, 0.10)]
    arms = [("funnel: 2nd warning inside 500 trades -> paper", dict(warnings_to_paper=2)),
            ("fold: each warning one level down; 3rd -> paper", dict(warnings_to_paper=3))]
    for title, te, be in cases:
        cell(title, te, be, 1, 1.0, arms, paths, days)


def mode_verify_b(paths, days):
    print("Candidate 2's finding, re-run: DP9's level-weighted B read literally. At N=1 B = l, so size = D/(s z sqrt(H) l) x l:"
          " the level cancels and a stepped-down unit trades at full size.")
    arms = [("B flat on live units (core_sim)", dict(raise_at_anchor=True)),
            ("B pure level-weighted (DP9 literal)", dict(raise_at_anchor=True, b_mode="pure")),
            ("B freed swing only to full-level units (fold)", dict(raise_at_anchor=True, b_mode="freed"))]
    for N in (1, 10):
        for title, te, be in CASES:
            cell(title, te, be, N, 1.0, arms, paths, days)


def mode_verify_k(paths, days):
    print("Candidate 2's finding, re-run: the day stop on the budget sigma never fires; on the sized sigma k decides the rate.")
    for N in (1, 10):
        for title, te, be in CASES:
            k = k_own_p1(N, be, random.Random(7))
            arms = [("budget sigma k2.5 (core_sim)", dict(raise_at_anchor=True)),
                    ("sized sigma k2.5", dict(raise_at_anchor=True, k_mode="sized", k_stop=2.5)),
                    (f"sized sigma k derived ({k:.2f})", dict(raise_at_anchor=True, k_mode="sized", k_stop=k)),
                    ("sized sigma k1.7 (preset rung)", dict(raise_at_anchor=True, k_mode="sized", k_stop=1.7))]
            cell(title, te, be, N, 1.0, arms, paths, days)


CHOKE = 0.75
FIXED = dict(FOLD_BASE, b_mode="flat", warnings_to_paper=3, drift_lock=True, drift_lock_days=20, alloc_days=7, admission=True,
             click_days=2, floor_at_lock=True, open_share=True, hold_n="group")
"""The spine as the last round fixed it. Flat B until he signs the freed-swing once-rule (SPINE 4.3, Q9); a lockout waits
for his click, assumed two days here; the day stop's k from the group's own bad day with the tail rows on."""


def admission_table():
    """B2: the worked healthy unit against the gate as first written and as fixed. Deterministic."""
    edge, cost, half = 0.10, cs.COST_R, 0.05
    low = edge - half
    print("\nB2, the worked healthy unit at the door (net +0.10R, stressed cost 0.16R, band half-width 0.05R):")
    print(f"  gross band low end minus stressed cost this hour : {low + cost:.2f} - {2 * cost:.2f} = {low + cost - 2 * cost:+.2f}  refuses at every hour")
    print(f"  net band low end minus stressed cost             : {low:.2f} - {cost:.2f} = {low - cost:+.2f}  refuses at every hour")
    print(f"  ratio of 2 (edge_to_cost_ratio_min) on gross     : {low + cost:.2f} / {cost:.2f} = {(low + cost) / cost:.2f}  refuses at every hour")
    print(f"  as fixed: the holdout's net low end at the door  : {low:+.2f}  passes, starts at 0.50; a cell refuses only on its own fills")


def first_seed_live(believed, N):
    """Units trading at the first anchor on the $500 seed, by the shed rule at the start level. Deterministic."""
    start = 1 if believed - 0.05 > 0 else 0
    s = cs.spread(believed)
    D = cs.SEED - cs.FLOOR
    H = cs.RATE * cs.HDAYS
    live = N
    while live > 1 and D / (s * cs.Z * math.sqrt(H) * b_flat(live)) * cs.RESERVE * cs.COST_DEN * LEVELS[start] < 2 * LOT:
        live -= 1
    return live


def choke_arm(title, cases, Ns, paths, days, **opts):
    print(f"\n{title}")
    print(f"  {'case':<9} {'N':>2} {'k':>5} {'opp':>5} {'cap':>5} {'raw':>5} {'room':>6} {'live':>5} {'seed':>4} {'med$':>6} {'p10$':>6} {'half':>6} "
          f"{'touch':>5} {'st/100d':>7} {'lock/100d':>9} {'paper':>6} {'cell':>5} {'skip':>5} {'stream':>7}")
    out_rows = {}
    for name, te, be in cases:
        for N in Ns:
            rng0 = random.Random(11)
            _, t1 = cs.card(be, cs.RATE, rng0)
            s = cs.spread(be)
            k = k_own_p1(N, be, random.Random(7))
            rng = random.Random(1000 + N)
            out = [run_path(te, be, N, 1.0, rng, t1, s, days=days, k_stop=k, **opts) for _ in range(paths)]
            eqs = [o["eq"] for o in out]
            opp = sum(o["opp"] for o in out) / paths
            cap = sum(o["opp_cap"] for o in out) / paths
            oc = {key: sum(o["outcomes"].get(key, 0) for o in out) for key in ("taken", "skip", "off", "bench", "stop", "cell", "gate")}
            tot = max(1, sum(oc.values()))
            room = 1 - CHOKE / opp if opp > 0 else 0.0
            print(f"  {name:<9} {N:>2} {k:5.2f} {opp:5.2f} {cap:5.2f} {opp * cs.RESERVE * cs.COST_DEN:5.2f} {100 * room:5.1f}% {sum(o['live'] for o in out) / paths:5.2f} "
                  f"{first_seed_live(be, N):>4} {pct(eqs, 0.5):6.0f} {pct(eqs, 0.1):6.0f} {100 * sum(1 for o in out if o['min_share'] < 0.5) / paths:5.1f}% "
                  f"{100 * sum(1 for o in out if o['touch']) / paths:4.1f}% {100 * sum(o['fires'] for o in out) / paths / days:7.2f} "
                  f"{100 * sum(o['locks'] for o in out) / paths / days / N:9.2f} {100 * sum(o['paper'] for o in out) / paths:5.1f}% "
                  f"{100 * oc['cell'] / tot:4.1f}% {100 * oc['skip'] / tot:4.1f}% {sum(o['stream'] for o in out) / paths:+7.3f}")
            out_rows[(name, N)] = (opp, oc, tot)
    return out_rows


def mode_choke(paths, days):
    print("The last round's choke test. MODEL NUMBERS ONLY: not evidence about a real strategy.")
    print("opp = dollars risked over the flat baseline of N on every opportunity, refusals at zero; cap = the same with each trade capped at the live N's baseline;")
    print(f"raw = opp against the raw formula: the baseline already holds reserve {cs.RESERVE} x cost denominator {cs.COST_DEN} = {cs.RESERVE * cs.COST_DEN:.4f};")
    print(f"room = the share of opportunities still free to be refused before opp reaches {CHOKE}; live = mean share of N trading;")
    print("seed = units trading at the first anchor on the $500 seed; cell = opportunities an hour cell refused; stream = mean net_r the brakes read.")
    print(f"Hours per day {HOURS}, a cell needs {MIN_CELL} fills, high end at z {CELL_Z}: model choices the numbers lens owns. {paths} paths, {days} days.")
    admission_table()
    cases = [(n.split()[0].lower(), te, be) for n, te, be in CASES]
    fixed = choke_arm("A. The spine as fixed: flat B, a lockout's click after 2 days", cases, (1, 5, 10), paths, days, **FIXED)
    choke_arm("B. The same with freed swing on (his once-rule, Q9)", cases, (1, 5, 10), paths, days, **dict(FIXED, b_mode="freed"))
    healthy = cases[:1]
    choke_arm("C. Healthy, a lockout's click never comes", healthy, (1, 5, 10), paths, days, **dict(FIXED, click_days=NEVER))
    for g in (0.05, 0.10, 0.15):
        choke_arm(f"D. Healthy, SQS and news refuse {int(100 * g)} % of opportunities (a guess)", healthy, (1, 5, 10), paths, days, **dict(FIXED, gate_refuse=g))
    choke_arm("F. Healthy, N frozen by any unit's bench or lock (the wide reading of the rule)", healthy, (1, 5, 10), paths, days, **dict(FIXED, hold_n="wide"))
    choke_arm("E. Healthy, net_r as first written: spread and slippage counted twice (0.16R), to show what the fix closes", healthy, (1, 5, 10), paths, days, **dict(FIXED, read_extra=cs.COST_R))
    print("\nWhere a healthy unit's opportunities go under arm A (share of every opportunity):")
    for (name, N), (opp, oc, tot) in fixed.items():
        if name != "healthy":
            continue
        print(f"  N={N:<2} opp {opp:.2f}: " + "  ".join(f"{key} {100 * oc[key] / tot:.1f}%" for key in ("taken", "off", "bench", "stop", "cell", "skip", "gate")))
    print("\nRuns, of the 23 things that bind: reserve, cost denominator, B, level, open-risk share, bench, drift, taper, day stop, lot shed, round-down,")
    print("admission (12). Not run, no values or no model of markets yet: cushion clip, bet key, per-trade cap, sanity band, margin, order rate, stop side,")
    print("SQS, news, resets, buffer stop (11). Arm D is a stand-in for SQS and news. The harness's choke test in CI must run all 23 (SPINE slice 8).")


if __name__ == "__main__":
    mode = ARGS[0] if ARGS else "fold"
    paths = int(ARGS[1]) if len(ARGS) > 1 else 40
    days = int(ARGS[2]) if len(ARGS) > 2 else 120
    {"fold": mode_fold, "verify-drift": mode_verify_drift, "verify-b": mode_verify_b, "verify-k": mode_verify_k,
     "decompose": mode_decompose, "drift-variants": mode_drift_variants, "choke": mode_choke}[mode](paths, days)
