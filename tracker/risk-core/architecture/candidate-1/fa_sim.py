"""Fork F-A check for candidate 1: applier with modes (a) against refresh-at-anchors (b).

Standard library only. Run:  python -I fa_sim.py [paths] [rate-list] [seed]

MODEL NUMBERS ONLY. Same worked example as funnel/working/review/core_sim.py: $500 seed, $300 floor,
eps 1 %, 20-day horizon, FI scalper outcomes (win +1R; half of losers cut at -0.3R, half -1R), cost 0.16R
at 1x. One unit. The sizer is the horizon formula with the reserve and the COST DENOMINATOR read from the
cost cell the guard has IN FORCE; the admission gate refuses entries while believed net edge < 0.

Two events, the harness pair FUNNEL.md 5.3 names for F-A:
  X4-39 broker changes its costs: on day 40 the true cost goes 1x -> 1.5x. The learner sees it on the first
        fill of day 40 (one trade pays the old belief). Arm (a) `live`: the cost cell is in force from the next
        trade. Arm (b) `at_anchor`: from the next anchor (day 41). Arm (n) no learner: never.
  X4-60 slow decay: the true edge slides from +0.10R to -0.05R over days 20-80 with no cost change. Both arms
        read the same CUSUM step-down (a state transition, applied at once in both), so they should tie.

Reported: median and p10 ending equity, the dollars lost on the lag days (40 and 41) and the share of the
starting cushion they are, and the size/base ratio.
"""
import math
import random
import statistics
import sys

PATHS = int(sys.argv[1]) if len(sys.argv) > 1 else 200
RATES = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [10, 40]
SEED0 = int(sys.argv[3]) if len(sys.argv) > 3 else 11
CARD = float(sys.argv[4]) if len(sys.argv) > 4 else 0.10  # the card's edge; at 0.05 a 1.5x cost turns net edge negative
SEED, FLOOR = 500.0, 300.0
Z, HDAYS, DAYS = 2.5758, 20, 120
CUT, COST_R = 0.3, 0.16
RESERVE = 0.85
LEVEL = 1.0  # a proved unit at full baseline; the climb is not the question here
CUSUM_LIMIT = 17.0


def outcomes(edge):
    loss = 0.5 * CUT + 0.5
    p = (edge + loss) / (1.0 + loss)
    return p, (1 - p) / 2


def spread(edge):
    p, q = outcomes(edge)
    m2 = p + q * CUT * CUT + q
    return math.sqrt(max(m2 - edge * edge, 1e-9))


def draw(rng, p, q):
    u = rng.random()
    return 1.0 if u < p else (-CUT if u < p + q else -1.0)


def cost_den(c_believed):
    """Size falls as the believed round-trip cost rises: (1 + c0) / (1 + c)."""
    return (1.0 + COST_R) / (1.0 + c_believed)


def run(mode, event, n, rng, believed=0.10):
    """mode: 'live' | 'at_anchor' | 'never'. event: 'cost' | 'decay'."""
    eq = SEED
    H = n * HDAYS
    s = spread(believed)
    c_true = COST_R
    c_inforce = COST_R
    cusum, lvl = 0.0, LEVEL
    lag_loss = 0.0
    sum_frac = n_frac = 0
    for day in range(DAYS):
        if event == "cost" and day == 40:
            c_true = 1.5 * COST_R
        if event == "decay":
            edge_true = 0.10 if day < 20 else (-0.05 if day > 80 else 0.10 - 0.15 * (day - 20) / 60)
        else:
            edge_true = believed
        if mode == "at_anchor":
            c_inforce = c_true if day >= 41 or event != "cost" else c_inforce
        if mode == "never":
            c_inforce = COST_R
        D = max(eq - FLOOR, 0.0)
        base = D / (s * Z * math.sqrt(H)) * RESERVE
        p, q = outcomes(edge_true)
        for t in range(n):
            # admission gate on the believed net edge (card low end minus believed cost over the card's)
            if believed - (c_inforce - COST_R) <= 0:
                continue
            size = base * cost_den(c_inforce) * lvl
            x = draw(rng, p, q) - (c_true - COST_R)
            pnl = size * x
            eq += pnl
            if event == "cost" and day in (40, 41):
                lag_loss += pnl
            sum_frac += size / max(base, 1e-9)
            n_frac += 1
            if mode == "live" and event == "cost" and day == 40 and t == 0:
                c_inforce = c_true  # the first fill shows the new spread; in force from the next trade
            cusum = max(0.0, cusum + (believed - 0.05 - x))
            if cusum >= CUSUM_LIMIT:
                cusum = 0.0
                lvl = max(0.25, lvl - 0.25)
            if eq <= FLOOR:
                return dict(eq=FLOOR, lag=lag_loss, frac=sum_frac / max(n_frac, 1), touch=True)
    return dict(eq=eq, lag=lag_loss, frac=sum_frac / max(n_frac, 1), touch=False)


def pct(xs, q):
    s = sorted(xs)
    return s[min(len(s) - 1, int(q * len(s)))]


def table(event, n):
    print(f"\n{event.upper()}  [n={n}/day, days={DAYS}, paths={PATHS}, card +{CARD:.2f}R, cost 1x->1.5x on day 40 (cost event)]")
    print(f"  {'arm':<14} {'median$':>8} {'p10$':>7} {'lag days $':>11} {'lag/cushion':>11} {'size/base':>9} {'touch':>6}")
    rows = {}
    for mode in ("live", "at_anchor", "never"):
        rng = random.Random(SEED0)
        out = [run(mode, event, n, rng, believed=CARD) for _ in range(PATHS)]
        rows[mode] = out
        eqs = [o["eq"] for o in out]
        lag = statistics.mean(o["lag"] for o in out)
        print(f"  {mode:<14} {pct(eqs, 0.5):8.0f} {pct(eqs, 0.1):7.0f} {lag:11.2f} {100 * lag / (SEED - FLOOR):10.1f}% "
              f"{statistics.mean(o['frac'] for o in out):9.2f} {100 * sum(o['touch'] for o in out) / PATHS:5.1f}%")
    a = statistics.mean(o["lag"] for o in rows["live"])
    b = statistics.mean(o["lag"] for o in rows["at_anchor"])
    print(f"  (a) live minus (b) at_anchor on the lag days: {a - b:+.2f} $ = {100 * (a - b) / (SEED - FLOOR):+.2f}% of the starting cushion")


if __name__ == "__main__":
    for n in RATES:
        table("cost", n)
    for n in RATES:
        table("decay", n)
