"""Independent check of the fold's handbrake claims. fold_sim.run_path copied with its fold arm's options fixed, plus
switches for what the spine writes that the sim does not run, and honest denominators.

Standard library only. Model numbers only. Run from anywhere, time-limited:
    python -I -B check_sim.py main [paths] [days]
    python -I -B check_sim.py rate [paths] [days]

Metrics, per unit-trade opportunity (rate x N x days):
  taken      the spine's size/base: mean size over the flat live baseline on trades TAKEN only (benched, day-stopped,
             paper, shed and skipped opportunities do not count; freed swing may read above 1).
  capped     the same with each trade capped at 1.0, so freed swing cannot paper over cuts.
  opp        dollars risked over what the unit would risk at the flat baseline of its own N on EVERY opportunity:
             a trade not taken counts as zero. This is the ledger's "share of baseline size a healthy unit must keep".
  live       mean share of the N units trading at the day's start (not shed, not on paper).
  lock       lockouts per unit per 100 days (the spine's bench lockout waits for his resume; the sim lets it expire).

Switches:
  baseline_days 1 is fold_sim (cushion re-read daily); 7 is SPINE 4.3 as written (the baseline derives at the weekly
                allocation anchor; between anchors only open risk moves it, and there is no open risk between sim trades).
  level_floor   "sim" is fold_sim (a level under one lot is lifted, through any lock); "lock" stops at the lock top;
                "none" is the spine as written (the rule appears nowhere in SPINE.md): an under-lot trade skips.
  b_mode        "freed" (fold) or "flat".
  gate_refuse   share of opportunities a gate refuses (SQS, news, admission hours), independent of everything else.
  read_extra    R per trade the brakes' stream reads below the money: a cost counted twice in net_r, or a card built on
                gross r read against a net stream. Money is unchanged.
"""
from __future__ import annotations

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[1:]
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..")))
import fold_sim as fs  # noqa: E402

cs = fs.cs
LOT, LEVELS = cs.LOT, cs.CORE_LEVELS


def run(true_edge, believed, N, rng, thr1, s_plan, k_stop, days=120, baseline_days=1, level_floor="sim", b_mode="freed",
        gate_refuse=0.0, cost_extra=0.0, read_extra=0.0):
    n = cs.RATE
    p, q = cs.outcomes(true_edge)
    start = 1 if believed - 0.05 > 0 else 0
    eq, floor = cs.SEED, cs.FLOOR
    H = n * cs.HDAYS
    w = max(1, math.ceil(10 / n))
    lvl, pending = [start] * N, [0] * N
    live, paper_until = [True] * N, [-1] * N
    co_n, co_r = [0] * N, [0.0] * N
    cusum, warns, unit_trades = [0.0] * N, [[] for _ in range(N)], [0] * N
    bench_until, bench_days = [-1] * N, [[] for _ in range(N)]
    lock_top, lock_until = [len(LEVELS) - 1] * N, [-1] * N
    hist = [[] for _ in range(N)]
    drift_paper = [False] * N
    taken_sum = capped_sum = 0.0
    taken_n = 0
    risked = wanted = 0.0
    live_sum = 0.0
    lockouts = fires = skipped = 0
    min_share, touch = 1.0, False
    start_cushion = cs.SEED - cs.FLOOR
    frozen_D = None
    for day in range(days):
        for i in range(N):
            if pending[i] and lvl[i] < lock_top[i]:
                lvl[i] = min(lock_top[i], lvl[i] + 1)
            pending[i] = 0
        true_D = max(eq - floor, 0.0)
        if frozen_D is None or day % baseline_days == 0:
            frozen_D = true_D
        D = frozen_D
        N_live = max(1, sum(1 for i in range(N) if live[i] and day >= paper_until[i]))

        def base_for(nl):
            return D / (s_plan * cs.Z * math.sqrt(H) * fs.b_flat(nl)) * cs.RESERVE * cs.COST_DEN

        base = base_for(N_live)
        for i in sorted(range(N), key=lambda i: -i):
            if live[i] and base * LEVELS[lvl[i]] < 2 * LOT and N_live > 1:
                live[i] = False
                N_live -= 1
                base = base_for(N_live)
        for i in range(N):
            if not live[i]:
                b2 = base_for(N_live + 1)
                if b2 * LEVELS[lvl[i]] >= 2 * LOT:
                    live[i] = True
                    N_live += 1
                    base = b2
        if level_floor != "none":
            for i in range(N):
                if live[i] and base * LEVELS[lvl[i]] < LOT <= base * LEVELS[-1]:
                    top = lock_top[i] if level_floor == "lock" else len(LEVELS) - 1
                    while base * LEVELS[lvl[i]] < LOT and lvl[i] < top:
                        lvl[i] += 1
        active = [i for i in range(N) if live[i] and day >= paper_until[i]]
        live_sum += len(active) / N
        ls = [LEVELS[lvl[i]] for i in active]
        unit_base = {}
        for pos, i in enumerate(active):
            b = fs.b_others(ls, pos) if (b_mode == "freed" and LEVELS[lvl[i]] >= LEVELS[-1]) else fs.b_flat(max(1, len(active)))
            unit_base[i] = D / (s_plan * cs.Z * math.sqrt(H) * b) * cs.RESERVE * cs.COST_DEN
        flat_N = base_for(N)  # what each of the N units would risk with nothing shed and nothing cut
        sizes = [LOT * math.floor(unit_base[i] * LEVELS[lvl[i]] / LOT) for i in active]
        s2, s1 = sum(x * x for x in sizes), sum(sizes)
        sigma_book = max(LOT, s_plan * math.sqrt(n) * math.sqrt(max(0.0, s2 + cs.RHO * (s1 * s1 - s2))))
        for i in range(N):
            if lock_until[i] >= 0 and day > lock_until[i]:
                lock_top[i], lock_until[i] = len(LEVELS) - 1, -1
        day_money, book_day, stopped = 0.0, 0.0, False
        day_r = [0.0] * N
        pnl = [sum(hist[i][-(w - 1):]) if w > 1 else 0.0 for i in range(N)]
        benched = [False] * N
        gap_today = rng.random() < cs.GAP_DAY_P
        wanted += flat_N * n * N
        for t in range(n):
            if stopped:
                break
            common = rng.random() if N > 1 else None
            for i in range(N):
                if not live[i] or day < paper_until[i] or benched[i] or day < bench_until[i]:
                    continue
                x = (cs.GAP_R - cost_extra) if (gap_today and t == 0) else cs.draw(rng, p, q, common, True, cost_extra)
                if gate_refuse and rng.random() < gate_refuse:
                    continue
                size = unit_base.get(i, base) * LEVELS[lvl[i]]
                z_day = book_day / sigma_book
                k_lo = 0.52 * k_stop
                if z_day < -k_lo:
                    size *= max(0.25, 1.0 - 0.75 * (-k_lo - z_day) / (k_stop - k_lo))
                size = LOT * math.floor(size / LOT)
                if size < LOT:
                    skipped += 1
                    continue
                day_money += size * x
                book_day += size * x
                taken_sum += size / max(base, 1e-9)
                capped_sum += min(1.0, size / max(base, 1e-9))
                taken_n += 1
                risked += size
                unit_trades[i] += 1
                xr = x - read_extra  # what the brakes read; read_extra > 0 is net_r with a cost counted twice
                day_r[i] += xr
                pnl[i] += xr
                cusum[i] = max(0.0, cusum[i] + (believed - 0.05 - xr))
                if cusum[i] >= 17.0:
                    cusum[i] = 0.0
                    warns[i] = [v for v in warns[i] if unit_trades[i] - v <= 500] + [unit_trades[i]]
                    if len(warns[i]) >= 3:
                        paper_until[i] = days + 1
                        drift_paper[i] = True
                    lvl[i] = max(0, lvl[i] - 1)
                    pending[i] = 0
                    lock_top[i] = min(lock_top[i], lvl[i])
                    lock_until[i] = max(lock_until[i], day + 20)
                co_n[i] += 1
                co_r[i] += xr
                if co_n[i] >= 25:
                    bad = co_r[i] <= -0.2 * 25 * s_plan
                    co_n[i], co_r[i] = 0, 0.0
                    if not bad and lvl[i] < lock_top[i]:
                        pending[i] = 1
                if pnl[i] <= thr1 and not benched[i]:
                    benched[i] = True
                    bench_until[i] = day + w
                    bench_days[i] = [d for d in bench_days[i] if day - d <= 40] + [day]
                    recent20 = sum(1 for d in bench_days[i] if day - d <= 20)
                    if len(bench_days[i]) >= 3:
                        paper_until[i] = day + 20
                        bench_days[i] = []
                        lockouts += 1
                    elif recent20 >= 2:
                        lock_top[i], lock_until[i] = max(0, lvl[i] - 1), day + 20
                        lvl[i] = min(lvl[i], lock_top[i])
                        pending[i] = 0
            if book_day <= -k_stop * sigma_book:
                stopped = True
                fires += 1
            if eq + day_money - floor <= 0:
                touch = True
                eq = floor
                break
        if touch:
            min_share = 0.0
            break
        eq += day_money
        for i in range(N):
            hist[i].append(day_r[i])
        min_share = min(min_share, (eq - floor) / start_cushion)
    days_run = day + 1
    return dict(eq=eq, taken=taken_sum / max(1, taken_n), capped=capped_sum / max(1, taken_n), opp=risked / max(1e-9, wanted),
                live=live_sum / days_run, lock=100 * lockouts / N / days_run, fires=100 * fires / days_run,
                half=min_share < 0.5, touch=touch, skipped=skipped / max(1, taken_n + skipped), paper=sum(drift_paper) / N)


CASES = [("healthy", 0.10, 0.10), ("weak", 0.05, 0.05), ("bleeding", -0.05, 0.10)]


def cell(name, te, be, N, paths, days, **opts):
    rng0 = random.Random(11)
    _, t1 = cs.card(be, cs.RATE, rng0)
    s = cs.spread(be)
    k = fs.k_own_p1(N, be, random.Random(7), rate=cs.RATE)
    rng = random.Random(1000 + N)
    out = [run(te, be, N, rng, t1, s, k, days=days, **opts) for _ in range(paths)]
    eqs = sorted(o["eq"] for o in out)
    print(f"  {name:<9} N={N:<2} k={k:4.2f} med$ {eqs[len(eqs)//2]:7.0f} p10$ {eqs[len(eqs)//10]:6.0f}  half {100*sum(o['half'] for o in out)/paths:5.1f}%"
          f" touch {100*sum(o['touch'] for o in out)/paths:4.1f}%  taken {sum(o['taken'] for o in out)/paths:4.2f} capped {sum(o['capped'] for o in out)/paths:4.2f}"
          f" opp {sum(o['opp'] for o in out)/paths:4.2f} live {sum(o['live'] for o in out)/paths:4.2f}"
          f" fires/100d {sum(o['fires'] for o in out)/paths:4.2f} lockouts/100d {sum(o['lock'] for o in out)/paths:4.2f}"
          f" skip {100*sum(o['skipped'] for o in out)/paths:4.1f}% paper {100*sum(o['paper'] for o in out)/paths:4.1f}%")


def arm(title, paths, days, cases=CASES, Ns=(1, 5, 10), **opts):
    print(f"\n{title}")
    for N in Ns:
        for name, te, be in cases:
            cell(name, te, be, N, paths, days, **opts)


def main(paths, days):
    print("Model numbers only. The fold as fold_sim runs it, then one change at a time.")
    arm("A. fold_sim's fold arm (daily cushion, level floor through locks)", paths, days)
    arm("B. baseline at the weekly allocation anchor, as SPINE 4.3 writes it", paths, days, baseline_days=7)
    arm("C. no level floor, as SPINE.md writes it (the rule is not in it)", paths, days, level_floor="none")
    arm("D. level floor stops at the lock", paths, days, level_floor="lock")
    arm("E. flat B instead of freed swing", paths, days, b_mode="flat")
    arm("F. gates refuse 15 % of opportunities (SQS, news and hourly admission together, a guess)", paths, days,
        cases=CASES[:1], gate_refuse=0.15)
    arm("G. brakes read 0.16R per trade below the card (spread and slippage counted twice, the worked cost)", paths, days,
        cases=CASES[:1], read_extra=0.16)
    arm("H. brakes read 0.08R per trade below the card (half that, e.g. commission only, gross card against net stream)",
        paths, days, cases=CASES[:1], read_extra=0.08)


def rates(paths, days):
    print("Model numbers only. The same fold arm at slower trade rates, healthy and weak, one unit and five.")
    for r in (10, 4, 2):
        cs.RATE = r
        arm(f"rate {r} a day", paths, days, cases=CASES[:2], Ns=(1, 5))
    cs.RATE = 10


if __name__ == "__main__":
    mode = ARGS[0] if ARGS else "main"
    paths = int(ARGS[1]) if len(ARGS) > 1 else 100
    days = int(ARGS[2]) if len(ARGS) > 2 else 120
    {"main": main, "rate": rates}[mode](paths, days)
