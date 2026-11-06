"""Arithmetic behind the funnel's logical-flaw checks. Standard library only.

Run:  python -I flaw_arithmetic.py
Every number here is model arithmetic, not evidence about a real strategy.
Dollar figures appear only as worked examples of a formula; the numbers lens sets values.
"""
from math import sqrt, log, erf, comb
from statistics import NormalDist

Z = NormalDist().inv_cdf

print("=" * 78)
print("A. Break-even win rate against cost in R and the fast-invalidation cut")
print("   p* = (L + C) / (W + L)   W = mean win in R, L = mean loss in R, C = round-trip cost in R")
print("   (X0-13's formula). A 1:1 scalper with no cut has W = 1, L = 1.")
print("=" * 78)
for cost in (0.05, 0.10, 0.16, 0.27):
    row = []
    for cut_share, cut_size in ((0.0, 1.0), (0.5, 0.35), (0.7, 0.35)):
        L = cut_share * cut_size + (1 - cut_share) * 1.0
        p_star = (L + cost) / (1.0 + L)
        row.append(f"cut {int(cut_share*100):>2}% of losers at -{cut_size}R -> L={L:.3f} p*={p_star:.3f}")
    print(f"cost {cost:.2f}R: " + " | ".join(row))
print("Reading: at 0.16R cost (0.8 pips on a 5-pip EURUSD stop) a 55% 1:1 scalper with full-size")
print("losses needs p* = 0.58, so it LOSES after costs. With half its losers cut at -0.35R, p* = 0.498,")
print("so 55% clears. The cut, not the win rate, is what makes his scalper viable after costs.")

print()
print("=" * 78)
print("B. Horizon floor-odds sizer (X2-H01): per-unit risk as a share of usable cushion D")
print("   r = D / (s * z * sqrt(H) * B),  B = sqrt(N * (1 + (N-1) rho)),  z = Phi^-1(1 - eps/2)")
print("   and the cushion needed for N units to clear a minimum-lot risk m:  D >= m * s * z * sqrt(H) * B")
print("=" * 78)
s, eps, H = 0.87, 0.01, 200
z = Z(1 - eps / 2)
print(f"s={s} eps={eps} z={z:.2f} H={H}")
print(f"{'N':>3} {'rho':>4} {'B':>5} {'r/D':>8} {'D needed per $1 of min-lot risk':>34}")
for N in (1, 3, 5, 10, 20):
    for rho in (0.0, 0.3):
        B = sqrt(N * (1 + (N - 1) * rho))
        r_over_D = 1 / (s * z * sqrt(H) * B)
        print(f"{N:>3} {rho:>4} {B:>5.2f} {r_over_D:>8.4f} {1/r_over_D:>34.0f}")
print("Reading: one unit risks about 1/32 of the cushion per trade; ten units at rho 0.3 about 1/190 each.")
print("A minimum lot that risks m needs a cushion of about 190 m for ten correlated units. So breadth")
print("across units at a small cushion collides with lot steps: either fewer units, cushion lending")
print("(X2-H30), or feasibility-first admission (X2-H45) must bind before the split does.")

print()
print("=" * 78)
print("C. Are X2-H01 (horizon sizer) and X2-H02 (day-sigma budget) one formula?")
print("   H02: sigma_book = D / (z * sqrt(days)); sigma_unit = sigma_book / B; r = sigma_unit / (s * sqrt(n))")
print("   H01: r = D / (s * z * sqrt(H) * B). Equal iff H = n * days.")
print("=" * 78)
D, days, n = 200.0, 20, 10
B = sqrt(10 * (1 + 9 * 0.3))
r_h02 = (D / (z * sqrt(days))) / B / (s * sqrt(n))
r_h01 = D / (s * z * sqrt(n * days) * B)
print(f"worked example D={D} days={days} n={n} N=10 rho=0.3: H02 r={r_h02:.3f}  H01 r={r_h01:.3f}  (H = n*days = {n*days})")
print("Reading: identical when the survival horizon H is defined as trade rate x days. The pick must")
print("define H that way, or the two sizers disagree and the brake (which reads sigma_unit) and the")
print("sizer drift apart.")

print()
print("=" * 78)
print("D. Can the house-money half (X2-H10) raise size into the money brake (X3-H01)?")
print("   Both read one ledger from one anchor. Brake trips at running P&L <= -L (own p1).")
print("   Multiplier m = (L + P - k*O) / L, extra risk on open trades <= share * P (realised profit).")
print("=" * 78)
L = 7.0   # the unit's own p1 day in R (fs10 in X3's SIM)
for P in (0.0, 2.0, 5.0, 10.0):
    for share in (0.25, 0.5):
        m = (L + P) / L
        extra = min((m - 1) * 1.0, share * P)   # extra risk per trade in R, bounded by share of profit
        size = 1.0 + extra
        losses_to_trip = (P + L) / size
        print(f"P=+{P:>4.1f}R share={share}: m={m:.2f} size={size:.2f}R  full losses before the brake trips={losses_to_trip:.1f}")
print("Reading: the extra size is funded from profit above the anchor, so the distance to the trip in")
print("losses never falls below L / 1 = 7 at P = 0 and grows with P. The accelerator cannot drive into")
print("the brake on the same ledger. It CAN on a different ledger (book house money funding unit size")
print("while the unit's own brake reads the unit ledger), which is why one declared scope per pair holds.")

print()
print("=" * 78)
print("E. Do the picks together choke a healthy unit? Expected share of baseline R given up.")
print("   bench at own p1 (loses the rest of the window), halve at own p10, isolation days, news minutes,")
print("   probation ramp at the start (titration 10% -> 100% doubling per clean cohort).")
print("=" * 78)
bench_days, halve_days = 0.01, 0.10
iso_days = 0.02          # a guess: two days a quarter of class isolation at half a day each
news_share = 0.05        # share of a scalper's trading minutes inside measured windows [guess]
daily_loss = bench_days * 0.5 + halve_days * 0.5 * 0.5 + iso_days * 0.5 + news_share
print(f"steady-state R given up per day ~ {daily_loss*100:.1f}% of healthy R (bench {bench_days*50:.1f}%, halve {halve_days*25:.1f}%, iso {iso_days*50:.1f}%, news {news_share*100:.1f}%)")
levels = [0.10, 0.20, 0.40, 0.80, 1.00]
cohort = 25
ramp_trades = cohort * (len(levels) - 1)
ramp_lost = sum((1 - lv) * cohort for lv in levels[:-1])
print(f"titration ramp: {ramp_trades} trades at reduced size, {ramp_lost:.0f} baseline-trade-equivalents of growth given up per unit start")
print(f"  at 10 trades/day that is {ramp_trades/10:.0f} days; at 40 a day {ramp_trades/40:.1f} days; at 2 a day {ramp_trades/2:.0f} days")
print("Reading: steady state costs ~10% of R, mostly news windows and the halve step; that is inside")
print("X3-H65's choke budget. The ramp is the real cost and it is a one-off per unit start; for a")
print("2-a-day ORB unit it is 50 days, which is where 'too safe' (A14, C13) is still true. The fix is")
print("cohorts in the family (pooled) for slow units, not a shorter ladder.")

print()
print("=" * 78)
print("F. Count brakes on healthy units: P(at least one run of 3 losses in a day) by trade rate")
print("=" * 78)
def p_run3(n, p_win):
    # probability of at least one run of 3 consecutive losses in n independent trades
    q = 1 - p_win
    # dp over states: number of trailing losses 0,1,2
    st = [1.0, 0.0, 0.0]
    hit = 0.0
    for _ in range(n):
        n0 = (st[0] + st[1] + st[2]) * p_win
        n1 = st[0] * q
        n2 = st[1] * q
        hit += st[2] * q
        st = [n0, n1, n2]
        hit_total = hit
    return hit_total
for rate in (2, 4, 10, 16, 40):
    print(f"{rate:>3} trades/day at 55% wins: P(3 in a row) = {p_run3(rate, 0.55)*100:5.1f}%   at 70% wins: {p_run3(rate, 0.70)*100:5.1f}%")
print("Reading: matches STATE item 10 (14% at 4, about 59% at 16). A fixed count is a frequency tax;")
print("his 'about three' survives only as an own-percentile run length (X3-H05).")

print()
print("=" * 78)
print("G. Proof clock against the probation ladder for a 55% 1:1 unit (X5 arithmetic, one unit)")
print("   trades to proof at 95%/80%: ((1.645+0.842)/SR_trade)^2, SR_trade = EV / s")
print("=" * 78)
for p in (0.55, 0.525, 0.58):
    ev = 2 * p - 1
    sd = sqrt(1 - ev * ev)
    n_proof = ((1.645 + 0.842) / (ev / sd)) ** 2
    print(f"p={p}: EV={ev:+.3f}R s={sd:.3f} trades to proof ~ {n_proof:,.0f}")
print("Reading: the ladder (4 cohorts of 25) finishes long before proof (600+ trades). So X5's")
print("'evidence bar rises with the level' (e >= 10/20/50/100) and X2's titration must be the SAME")
print("ladder, or a unit climbs to full size on cohorts while its evidence says 'unproved'. The pick")
print("makes cohorts the speed limit and the e-bar the ceiling per level.")
