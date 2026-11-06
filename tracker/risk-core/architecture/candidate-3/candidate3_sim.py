"""Candidate 3 proofs over the funnel's harder sim (funnel/working/review/core_sim.py, imported unchanged).

Standard library only. Run from this folder:  python -I candidate3_sim.py

Three checks, all MODEL NUMBERS on the funnel's worked example ($500 seed, $300 floor, 10 trades a day):

  1. TWO-STAGE ARBITRATION IS ONE RANK TABLE. Under fork F-B(b) the unit applies its own cuts first
     (level, bench, lockout) and the guard applies the portfolio cuts on the intent (taper, day stop,
     bet key, clip, veto, lot round-down). Both stages are cut-only. A property test over random
     control states shows the two-stage answer equals the single-table answer (min over caps,
     max over states, any refusal wins) for every draw, and that a raise never passes while any
     brake is active. This is X4-59's property, proved for the split.

  2. THE TRACE. One unit, one deterministic path per case (healthy, weak, bleeding with an
     overstated card). For sampled trades it prints every factor that touched the size, in the
     order the two stages apply them, and names the binding factor. The unit's running loss is
     read once (the bench, inside the unit); the book's once (the taper and day stop, in the guard).

  3. THE CHOKE BUDGET. core_sim's CORE arm (flags RSCDBGT + OY) at N=1 and N=10, cost 1x, healthy and
     weak: size/base must stay at or above 0.75 on the healthy unit (FUNNEL DP19). The merged
     arithmetic in core_sim is exactly the two-stage product, so this is the number the split ships.
"""
from __future__ import annotations

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.normpath(os.path.join(HERE, "..", "..", "funnel", "working", "review"))
sys.argv = sys.argv[:1]          # core_sim reads argv at import; give it the defaults
sys.path.insert(0, CORE)
import core_sim as cs            # noqa: E402

# --- 1. two-stage arbitration == one rank table -------------------------------------------------

STATES = ("ACTIVE", "REDUCING", "BENCHED", "HALTED")
RANK = {s: i for i, s in enumerate(STATES)}


def unit_stage(ctl: dict) -> tuple[str, float | None, str]:
    """What the compiled unit decides on its own facts before it emits an intent.
    Returns (state, cap as a multiple of base, binding reason). cap None = no entry."""
    state, cap, why = "ACTIVE", 1.0, "level"
    cap *= ctl["level"]
    if ctl["lockout_top"] < ctl["level"]:
        cap = ctl["lockout_top"]
        why = "lockout"
    if ctl["benched"]:
        return "BENCHED", None, "own_p1_bench"
    if ctl["cusum_warned"]:
        state = "REDUCING"
    return state, cap, why


def guard_stage(ctl: dict, state: str, cap: float | None, why: str) -> tuple[str, float | None, str]:
    """What before_order does to the intent: cut or refuse, never raise. The guard's own state is
    folded with max(state) even when the unit already refused (a benched unit under a day stop reads
    HALTED on the RiskState row, not BENCHED): the first run of this test caught that short-circuit."""
    if ctl["kill_yellow"] or ctl["stand_down"] or ctl["day_stop"]:
        g_why = "kill_switch" if ctl["kill_yellow"] else ("stand_down" if ctl["stand_down"] else "portfolio_day_stop")
        return "HALTED", None, (g_why if cap is not None else why)
    if cap is None:
        return state, None, why
    for name in ("taper", "bet_key_cap", "cushion_clip", "margin_headroom", "sanity_band", "agent_cut"):
        if ctl[name] < cap:
            cap, why = ctl[name], name
    if ctl["accelerator"] > 1.0 and state == "ACTIVE" and not any(
        ctl[k] for k in ("benched", "cusum_warned", "day_stop", "stand_down", "kill_yellow")
    ) and ctl["taper"] >= 1.0:
        cap *= ctl["accelerator"]          # the only raise, and only with every brake clear
        why = why + "+accelerator"
    return state, cap, why


def one_table(ctl: dict) -> tuple[str, float | None]:
    """The single rank table: any refusal wins; max state; min cap; raise only when all clear."""
    if ctl["benched"] or ctl["kill_yellow"] or ctl["stand_down"] or ctl["day_stop"]:
        st = "HALTED" if (ctl["kill_yellow"] or ctl["stand_down"] or ctl["day_stop"]) else "BENCHED"
        return st, None
    caps = [min(ctl["level"], ctl["lockout_top"]), ctl["taper"], ctl["bet_key_cap"], ctl["cushion_clip"],
            ctl["margin_headroom"], ctl["sanity_band"], ctl["agent_cut"]]
    cap = min(caps)
    state = "REDUCING" if ctl["cusum_warned"] else "ACTIVE"
    if ctl["accelerator"] > 1.0 and state == "ACTIVE" and ctl["taper"] >= 1.0:
        cap *= ctl["accelerator"]
    return state, cap


def check_rank(draws: int = 20000, seed: int = 3) -> tuple[int, int]:
    rng = random.Random(seed)
    levels = (0.25, 0.5, 0.75, 1.0)
    bad, raises_blocked = 0, 0
    for _ in range(draws):
        ctl = dict(
            level=rng.choice(levels), lockout_top=rng.choice(levels + (1.0, 1.0)),
            benched=rng.random() < 0.1, cusum_warned=rng.random() < 0.15,
            kill_yellow=rng.random() < 0.05, stand_down=rng.random() < 0.08, day_stop=rng.random() < 0.05,
            taper=rng.choice((1.0, 1.0, 1.0, 0.8, 0.5, 0.25)), bet_key_cap=rng.choice((1.0, 1.0, 0.6)),
            cushion_clip=rng.choice((1.0, 1.0, 0.7)), margin_headroom=rng.choice((1.0, 1.0, 0.9)),
            sanity_band=rng.choice((1.0, 1.0, 0.95)), agent_cut=rng.choice((1.0, 1.0, 1.0, 0.5)),
            accelerator=rng.choice((1.0, 1.0, 1.0, 1.5)),
        )
        s1, c1, _ = guard_stage(ctl, *unit_stage(ctl))
        s2, c2 = one_table(ctl)
        same = (s1 == s2) and ((c1 is None and c2 is None) or (c1 is not None and c2 is not None and abs(c1 - c2) < 1e-12))
        if not same:
            bad += 1
        braking = any(ctl[k] for k in ("benched", "cusum_warned", "day_stop", "stand_down", "kill_yellow")) or ctl["taper"] < 1.0
        if braking and c1 is not None and c1 > min(ctl["level"], ctl["lockout_top"]) + 1e-12:
            bad += 1                                   # a raise slipped through while braking
        if braking and ctl["accelerator"] > 1.0:
            raises_blocked += 1
    return bad, raises_blocked


# --- 2. the trace: every factor that touches size, in stage order ---------------------------------

def trace(title: str, true_edge: float, believed: float, days: int = 60, seed: int = 5, show=(0, 5, 10, 20, 30, 45, 59), verbose: bool = True):
    """One unit, one path, the core's rules as core_sim applies them (flags RSCDBGT, lot $0.50 with skip),
    printed as the two stages. Facts the guard computes: cushion, base, sigma_book, book_day. The unit's
    own facts: its running loss over the window (the bench reads it once), cohorts, CUSUM, level.
    Returns (end equity, day the unit went to paper or None)."""
    rng = random.Random(seed)
    say = print if verbose else (lambda *a, **k: None)
    reducing = False
    paper_day = None
    thr10, thr1 = cs.card(believed, cs.RATE, rng)
    s_plan = cs.spread(believed)
    p, q = cs.outcomes(true_edge)
    levels = cs.CORE_LEVELS
    lvl = 1 if believed - 0.05 > 0 else 0
    eq, floor = cs.SEED, cs.FLOOR
    H = cs.RATE * cs.HDAYS
    w = max(1, math.ceil(10 / cs.RATE))
    hist, co_n, co_r, clean, cusum, warns = [], 0, 0.0, 0, 0.0, []
    bench_until, bench_days, lock_top, lock_until = -1, [], len(levels) - 1, -1
    paper = False
    say(f"\n{title}  [card p1={thr1:.1f}R over {w} day(s); start level {levels[lvl]}]")
    say(f"  {'day':>3} {'cushion$':>8} {'base$':>6} | unit: {'level':>5} {'bench':>5} {'lock':>4} | guard: {'taper':>5} {'stop':>4} {'lot':>4} | {'size$':>6}  binding")
    for day in range(days):
        if paper:
            say(f"  {day:>3}  unit in paper (cause: drift_warning x2 inside 500 trades, or bench #3 inside 40 days)")
            paper_day = day
            break
        D = max(eq - floor, 0.0)
        base = D / (s_plan * cs.Z * math.sqrt(H) * 1.0) * cs.RESERVE * cs.COST_DEN     # N=1: B=1
        sigma_book = D / (cs.Z * math.sqrt(cs.HDAYS))
        if lock_until >= 0 and day > lock_until:
            lock_top, lock_until = len(levels) - 1, -1
        pnl = sum(hist[-(w - 1):]) if w > 1 else 0.0
        day_money, book_day, benched, stopped = 0.0, 0.0, False, False
        day_r = 0.0
        for t in range(cs.RATE):
            if stopped or benched or day < bench_until:
                break
            # --- unit stage (inside the compiled unit) ---
            u_state = "BENCHED" if day < bench_until else ("REDUCING" if reducing else "ACTIVE")
            frac = levels[min(lvl, lock_top)]
            binding = "level" if lock_top >= lvl else "lockout"
            size = base * frac
            # --- guard stage (before_order on the intent) ---
            taper = 1.0
            if sigma_book > 0:
                z_day = book_day / sigma_book
                k_lo = 0.52 * cs.K_STOP
                if z_day < -k_lo:
                    taper = max(0.25, 1.0 - 0.75 * (-k_lo - z_day) / (cs.K_STOP - k_lo))
            if taper < 1.0:
                size *= taper
                binding = "pair_taper"
            lot_size = cs.LOT * math.floor(size / cs.LOT)
            if lot_size < cs.LOT:
                if day in show and t == 0:
                    say(f"  {day:>3} {D:8.1f} {base:6.2f} |       {frac:5.2f} {'no':>5} {levels[lock_top]:4.2f} |        {taper:5.2f} {'no':>4} skip | {0:6.2f}  below one lot step (dark)")
                continue
            if lot_size < size - 1e-9:
                binding = binding + ">lot_round"
            x = cs.draw(rng, p, q, None, True, 0.0)
            if day in show and t == 0:
                say(f"  {day:>3} {D:8.1f} {base:6.2f} |       {frac:5.2f} {'no':>5} {levels[lock_top]:4.2f} |        {taper:5.2f} {'no':>4} {lot_size/base if base else 0:4.2f} | {lot_size:6.2f}  {binding}; state {u_state}")
            day_money += lot_size * x
            book_day += lot_size * x
            day_r += x
            pnl += x
            # unit facts after the close: CUSUM (step down), cohorts (step up), the bench (own p1)
            cusum = max(0.0, cusum + (believed - 0.05 - x))
            trades_so_far = len(hist) * cs.RATE + t + 1
            if cusum >= 17.0:
                cusum = 0.0
                warns = [v for v in warns if trades_so_far - v <= 500] + [trades_so_far]
                if len(warns) >= 2:
                    paper = True
                lvl = max(0, lvl - 1)
                clean = 0
                reducing = True
                say(f"  {day:>3}  CUSUM warning #{len(warns)} at trade {trades_so_far}: level -> {levels[lvl]} (REDUCING, cause drift_warning)")
            co_n += 1
            co_r += x
            if co_n >= 25:
                bad = co_r <= -0.2 * 25 * s_plan
                co_n, co_r = 0, 0.0
                if bad:
                    clean = 0
                else:
                    clean += 1
                    if clean >= 1 and lvl < lock_top:
                        clean = 0
                        lvl += 1
                        reducing = False
                        say(f"  {day:>3}  clean cohort: level -> {levels[lvl]} (ACTIVE)")
            if pnl <= thr1 and not benched:
                benched = True
                bench_until = day + w
                bench_days = [d for d in bench_days if day - d <= 40] + [day]
                recent20 = sum(1 for d in bench_days if day - d <= 20)
                if len(bench_days) >= 3:
                    paper = True
                    say(f"  {day:>3}  BENCH #3 inside 40 days -> paper for 20 days (retry-then-lockout)")
                elif recent20 >= 2:
                    lock_top, lock_until = max(0, lvl - 1), day + 20
                    lvl = min(lvl, lock_top)
                    say(f"  {day:>3}  BENCH #2 inside 20 days -> locked one level lower ({levels[lock_top]}) for 20 days")
                else:
                    say(f"  {day:>3}  BENCH: own running loss {pnl:.1f}R <= p1 {thr1:.1f}R -> no new entries until day {bench_until} (unit scope)")
            if sigma_book > 0 and book_day <= -cs.K_STOP * sigma_book:
                stopped = True
                say(f"  {day:>3}  PORTFOLIO DAY STOP: book day {book_day:.1f}$ <= -{cs.K_STOP} sigma_book ({sigma_book:.1f}$) -> stand-down at all until the next anchor (guard)")
        eq += day_money
        hist.append(day_r)
    say(f"  end equity ${eq:.0f}; cushion ${max(eq-floor,0):.0f}; level {levels[lvl]}")
    return eq, paper_day


def paper_rate(title: str, true_edge: float, believed: float, paths: int = 200, days: int = 120):
    """How often the drift rules (two CUSUM warnings inside 500 trades, or bench #3 inside 40 days) send a
    unit to paper inside `days`, and the median day. A healthy unit's rate is the price of the second-warning
    rule at h = 17 and a 500-trade window; both are the numbers lens's (FUNNEL DP18, DP27)."""
    out = [trace(title, true_edge, believed, days=days, seed=100 + k, verbose=False) for k in range(paths)]
    to_paper = [d for _, d in out if d is not None]
    med = sorted(to_paper)[len(to_paper) // 2] if to_paper else None
    print(f"  {title:<38} to paper inside {days} days: {100*len(to_paper)/paths:5.1f}% of {paths} paths"
          + (f"; median day {med}" if med is not None else ""))


# --- 3. the choke budget on the merged arithmetic -------------------------------------------------

def choke(paths: int = 30):
    cs.PATHS = paths
    print("\nChoke budget (core_sim CORE arm = the two stages' product; healthy must stay >= 0.75 of base)")
    for N in (1, 10):
        for title, te, be in cs.CASES[:2]:
            cs.table(title, te, be, N, 1.0, [("CORE (unit stage x guard stage)", "RSCDBGT")], "OY", seed=11)
        cs.table(cs.CASES[3][0], cs.CASES[3][1], cs.CASES[3][2], N, 1.0, [("CORE (unit stage x guard stage)", "RSCDBGT")], "OY", seed=11)


if __name__ == "__main__":
    bad, blocked = check_rank()
    print(f"1. Two-stage == one rank table: {bad} mismatches in 20000 random control states; "
          f"{blocked} draws had an accelerator >1 while braking, none raised size.")
    trace("2a. HEALTHY +0.10R, card +0.10R", 0.10, 0.10)
    trace("2b. WEAK +0.05R, card +0.05R", 0.05, 0.05)
    trace("2c. BLEEDING true -0.05R, card +0.10R", -0.05, 0.10)
    print("\n2d. How often the drift rules send a unit to paper (N=1, one-unit model, 120 days):")
    paper_rate("HEALTHY +0.10R, card +0.10R", 0.10, 0.10)
    paper_rate("WEAK +0.05R, card +0.05R", 0.05, 0.05)
    paper_rate("OVERSTATED true +0.03R, card +0.10R", 0.03, 0.10)
    paper_rate("BLEEDING true -0.05R, card +0.10R", -0.05, 0.10)
    choke()
