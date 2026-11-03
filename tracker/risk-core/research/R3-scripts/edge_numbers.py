"""R3 worked numbers: trades needed to prove an edge, sequential looks, and analogue arithmetic.

Standard library only. Run: python -I edge_numbers.py
Assumptions are printed next to each block. Trades are independent. Wins pay +1R and losses -1R
unless stated, so the per-trade Sharpe of a p-win unit is (2p - 1) / sqrt(1 - (2p - 1)^2).
"""
import math
import random
from statistics import NormalDist

N01 = NormalDist()
Z95 = N01.inv_cdf(0.95)    # one-sided 95 %
Z80 = N01.inv_cdf(0.80)    # 80 % power
EULER = 0.5772156649


def binary_moments(p):
    """Mean, sd, skew, kurtosis (not excess) of a +1/-1 trade that wins with probability p."""
    mean = 2 * p - 1
    var = 1 - mean ** 2
    sd = math.sqrt(var)
    q = 1 - p
    skew = (q - p) / math.sqrt(p * q)
    kurt = (1 - 6 * p * q) / (p * q) + 3
    return mean, sd, skew, kurt


def min_trl(sr, skew, kurt, sr_star=0.0, z=Z95):
    """Bailey and Lopez de Prado minimum track record length, in trades."""
    return 1 + (1 - skew * sr + (kurt - 1) / 4 * sr ** 2) * (z / (sr - sr_star)) ** 2


def expected_max_null(n_trials):
    """Expected maximum of n_trials standard normals (the DSR paper's approximation)."""
    if n_trials <= 1:
        return 0.0
    return (1 - EULER) * N01.inv_cdf(1 - 1 / n_trials) + EULER * N01.inv_cdf(1 - 1 / (n_trials * math.e))


def block(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def trades_needed():
    block("1. Trades needed to tell an edge from luck (1:1 payoff, independent trades)")
    print("unit              edge/trade  SR/trade  MinTRL95  t>3 (HLZ)  80%power  DSR N=10  DSR N=100")
    rows = []
    for label, p in [("55 % wins (as believed)", 0.55), ("52.5 % wins (half edge)", 0.525),
                     ("51 % wins (a fifth)", 0.51)]:
        mean, sd, skew, kurt = binary_moments(p)
        sr = mean / sd
        mtrl = min_trl(sr, skew, kurt)
        hlz = (3.0 / sr) ** 2
        power80 = ((Z95 + Z80) / sr) ** 2
        dsr10 = ((expected_max_null(10) + Z95) / sr) ** 2
        dsr100 = ((expected_max_null(100) + Z95) / sr) ** 2
        rows.append((label, mean, sr, mtrl, hlz, power80, dsr10, dsr100))
        print(f"{label:24s} {mean:+.3f}R  {sr:7.4f}  {mtrl:8.0f}  {hlz:9.0f}  {power80:8.0f}  {dsr10:8.0f}  {dsr100:9.0f}")
    print("Rule of thumb: trades needed scale with 1 / edge^2. Half the edge -> about 4x the trades.")
    print(f"Expected best-of-N luck, in standard errors: N=10 {expected_max_null(10):.2f}, "
          f"N=100 {expected_max_null(100):.2f}, N=1000 {expected_max_null(1000):.2f}")
    return rows


def calendar_time(rows):
    block("2. Calendar days to reach the 80 %-power count, by trades per day")
    print("Pooling across units only helps when the units test the SAME claim and trade independently.")
    print("unit                     trades   1/day   4/day   10 units x 4/day   40 units x 4/day")
    for label, _m, _sr, _mt, _h, power80, _d10, _d100 in rows:
        print(f"{label:24s} {power80:6.0f}  {power80/1:6.0f}  {power80/4:6.0f}  {power80/40:16.0f}  {power80/160:16.0f}")


def group_sequential(seed=3, paths=20000):
    block("3. A trial-style plan for one unit: 5 looks, every 200 trades, max 1,000")
    print("Efficacy bound: O'Brien-Fleming, z_k = 2.04 / sqrt(k/5) (two-sided 0.05, one-sided 0.025).")
    print("Futility: non-binding rule 'stop if the running mean is below 0 at look 2 or later'.")
    bounds = [2.04 / math.sqrt(k / 5) for k in range(1, 6)]
    print("bounds:", ", ".join(f"{b:.2f}" for b in bounds))
    rng = random.Random(seed)
    looks = [200, 400, 600, 800, 1000]
    print("true edge   P(proved)  P(stopped as futile)  P(undecided at 1,000)  mean trades used")
    for mu in (0.0, 0.05, 0.10):
        proved = futile = undecided = 0
        used = 0
        for _ in range(paths):
            s = 0.0
            n = 0
            done = False
            for k, lk in enumerate(looks):
                while n < lk:
                    s += rng.gauss(mu, 1.0)
                    n += 1
                z = s / math.sqrt(n)
                if z >= bounds[k]:
                    proved += 1
                    done = True
                    break
                if k >= 1 and s < 0:
                    futile += 1
                    done = True
                    break
            if not done:
                undecided += 1
            used += n
        print(f"{mu:+.2f}R      {proved/paths:8.3f}  {futile/paths:20.3f}  {undecided/paths:21.3f}  {used/paths:16.0f}")
    print("Pocock's flat bound for 5 looks is 2.41 at every look: earlier stops, bigger final bar.")


def basel_zones():
    block("4. Basel traffic light: exceptions in 250 days when the model is right (p = 1 %)")
    n, p = 250, 0.01
    cum = 0.0
    for k in range(0, 11):
        pk = math.comb(n, k) * p ** k * (1 - p) ** (n - k)
        cum += pk
        zone = "green" if k <= 4 else ("yellow" if k <= 9 else "red")
        print(f"k={k:2d}  P(X=k)={pk:6.4f}  P(X<=k)={cum:7.5f}  zone if k exceptions: {zone}")
    p_yellow_or_worse = 1 - sum(math.comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(5))
    print(f"A correct model lands in yellow or red {p_yellow_or_worse:.1%} of years.")
    q = 0.03
    p_green_bad = sum(math.comb(n, k) * q ** k * (1 - q) ** (n - k) for k in range(5))
    print(f"A model that is really 97 % (3 % breaches) still lands green {p_green_bad:.1%} of years.")


def sre_burn():
    block("5. SRE burn-rate arithmetic (30-day window = 720 hours)")
    for rate, hours in ((14.4, 1), (6, 6), (1, 72)):
        print(f"burn rate {rate:>4} for {hours:>2} h uses {rate*hours/720:.0%} of the month's budget")


def cscv_count():
    block("6. CSCV: number of train/test splits for S slices")
    for s in (8, 10, 16):
        print(f"S={s:2d}: C(S, S/2) = {math.comb(s, s//2):,} splits")
    print("With S = 16 and 1,000 trades, each slice holds about 62 trades.")


def obf_alpha_spent():
    block("7. How a Lan-DeMets O'Brien-Fleming-type function spends 0.025 (one-sided) over time")
    a = 0.025
    za = N01.inv_cdf(1 - a)  # 1.96
    for t in (0.2, 0.4, 0.6, 0.8, 1.0):
        spent = 1 - N01.cdf(za / math.sqrt(t))
        print(f"information fraction {t:.1f}: alpha spent so far {spent:.5f}")


def check_constants(seed=5, paths=200000):
    block("8. Check the published 5-look constants by simulation (two-sided 0.05)")
    rng = random.Random(seed)
    obf_hits = poc_hits = 0
    for _ in range(paths):
        s = 0.0
        obf = poc = False
        for k in range(1, 6):
            s += rng.gauss(0, 1)
            z = s / math.sqrt(k)
            if abs(z) >= 2.04 * math.sqrt(5 / k):
                obf = True
            if abs(z) >= 2.41:
                poc = True
        obf_hits += obf
        poc_hits += poc
    print(f"O'Brien-Fleming 2.04*sqrt(5/k): overall false-positive rate {obf_hits/paths:.4f} (target 0.05)")
    print(f"Pocock flat 2.41:               overall false-positive rate {poc_hits/paths:.4f} (target 0.05)")
    print(f"Naive 1.96 at every look would give about {5*0.05:.2f} as an upper bound; simulate:")
    rng = random.Random(seed + 1)
    naive = 0
    for _ in range(paths // 4):
        s = 0.0
        hit = False
        for k in range(1, 6):
            s += rng.gauss(0, 1)
            if abs(s / math.sqrt(k)) >= 1.96:
                hit = True
        naive += hit
    print(f"Naive 1.96 at 5 looks: false-positive rate {naive/(paths//4):.4f}")


def boin_bounds(phi=0.30, phi1=0.18, phi2=0.42):
    block("9. BOIN escalation and de-escalation boundaries (Liu and Yuan 2015 formulas)")
    lam_e = math.log((1 - phi1) / (1 - phi)) / math.log(phi * (1 - phi1) / (phi1 * (1 - phi)))
    lam_d = math.log((1 - phi) / (1 - phi2)) / math.log(phi2 * (1 - phi) / (phi * (1 - phi2)))
    print(f"target {phi}: escalate if observed rate <= {lam_e:.3f}; de-escalate if >= {lam_d:.3f}; else stay")


if __name__ == "__main__":
    check_constants()
    boin_bounds()
    rows = trades_needed()
    calendar_time(rows)
    group_sequential()
    basel_zones()
    sre_burn()
    cscv_count()
    obf_alpha_spent()
