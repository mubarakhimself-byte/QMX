"""Lag and false-alarm of cheap market-state sensors on simulated 1-minute bars.

Gaussian bars, sigma = 1 per bar. A sensor alarms when its rolling statistic crosses
a threshold. Thresholds are calibrated on a long no-change series so that alarm
episodes (upcrossings) arrive on average once per `fa_spacing` bars. Then the series
switches regime and we count bars until the first alarm.

Run: python -I mis_sensor_lag.py
"""
import sys
import numpy as np

RNG = np.random.default_rng(20261030)
N_NULL = 400_000
REPS = 300
WARM = 600
HORIZON = 4000


def rolling_sum(x, n):
    c = np.cumsum(np.insert(x, 0, 0.0))
    out = np.full(x.shape, np.nan)
    out[n - 1:] = c[n:] - c[:-n]
    return out


def er(ret, n):
    net = np.abs(rolling_sum(ret, n))
    path = rolling_sum(np.abs(ret), n)
    return net / path


def vr(ret, n, q=4):
    one = rolling_sum(ret ** 2, n) / n
    qret = rolling_sum(ret, q)
    qret = np.nan_to_num(qret)
    qvar = rolling_sum(qret ** 2, n) / n
    return qvar / (q * one)


def ac1(ret, n):
    lagged = np.concatenate([[0.0], ret[:-1]])
    num = rolling_sum(ret * lagged, n)
    den = rolling_sum(ret ** 2, n)
    return num / den


def volratio(ret, n):
    return np.sqrt(rolling_sum(ret ** 2, n) / n)


def cusum_vol(ret, k=1.5):
    llr = -np.log(k) + 0.5 * ret ** 2 * (1 - 1 / k ** 2)
    s = np.zeros_like(ret)
    for i in range(1, len(ret)):
        s[i] = max(0.0, s[i - 1] + llr[i])
    return s


def cusum_drift(ret, mu=0.2):
    llr = mu * np.abs(ret) - 0.5 * mu ** 2  # two-sided via |r| is not exact; use one-sided sign below
    s = np.zeros_like(ret)
    for i in range(1, len(ret)):
        s[i] = max(0.0, s[i - 1] + mu * ret[i] - 0.5 * mu ** 2)
    return s


SENSORS = {
    "ER(30)>": (lambda r: er(r, 30), +1),
    "ER(60)>": (lambda r: er(r, 60), +1),
    "ER(240)>": (lambda r: er(r, 240), +1),
    "VR4(60)<": (lambda r: vr(r, 60), -1),
    "VR4(240)<": (lambda r: vr(r, 240), -1),
    "VR4(240)>": (lambda r: vr(r, 240), +1),
    "AC1(60)<": (lambda r: ac1(r, 60), -1),
    "AC1(240)<": (lambda r: ac1(r, 240), -1),
    "Vol(30)>": (lambda r: volratio(r, 30), +1),
    "CUSUMvol1.5>": (cusum_vol, +1),
    "CUSUMdrift0.2>": (cusum_drift, +1),
}


def upcross_spacing(stat, thr, sign):
    s = sign * stat
    above = s > sign * thr
    above = np.nan_to_num(above, nan=False).astype(bool)
    ups = np.sum(above[1:] & ~above[:-1])
    valid = np.sum(~np.isnan(stat))
    return valid / max(ups, 1)


def calibrate(fn, sign, target):
    null = RNG.standard_normal(N_NULL)
    stat = fn(null)
    vals = stat[~np.isnan(stat)]
    lo, hi = 0.5, 0.999999
    for _ in range(40):
        mid = (lo + hi) / 2
        thr = np.quantile(vals, mid) if sign > 0 else np.quantile(vals, 1 - mid)
        if upcross_spacing(stat, thr, sign) < target:
            lo = mid
        else:
            hi = mid
    return np.quantile(vals, hi) if sign > 0 else np.quantile(vals, 1 - hi)


def regime(kind, n):
    e = RNG.standard_normal(n)
    if kind == "drift0.2":
        return e + 0.2
    if kind == "drift0.1":
        return e + 0.1
    if kind == "vol1.5":
        return e * 1.5
    if kind.startswith("ar"):
        phi = float(kind[2:])
        out = np.empty(n)
        prev = 0.0
        for i in range(n):
            prev = phi * prev + e[i]
            out[i] = prev
        return out / np.sqrt(1 / (1 - phi ** 2))
    raise ValueError(kind)


def delays(fn, sign, thr, kind):
    res = []
    for _ in range(REPS):
        r = np.concatenate([RNG.standard_normal(WARM), regime(kind, HORIZON)])
        s = sign * fn(r)[WARM:]
        hit = np.nonzero(np.nan_to_num(s > sign * thr, nan=False))[0]
        res.append(hit[0] if len(hit) else np.inf)
    res = np.array(res)
    found = np.isfinite(res)
    med = np.median(res) if found.mean() >= 0.5 else np.inf
    p90 = np.quantile(res, 0.9) if found.mean() >= 0.9 else np.inf
    return med, p90, found.mean()


def bounce_false_alarms(fn, sign, thr, noise):
    eff = np.cumsum(RNG.standard_normal(N_NULL))
    obs = eff + noise * RNG.standard_normal(N_NULL)
    r = np.diff(obs) / np.sqrt(1 + 2 * noise ** 2)
    stat = fn(r)
    return upcross_spacing(stat, thr, sign)


def main():
    target = float(sys.argv[1]) if len(sys.argv) > 1 else 1440.0
    kinds = ["drift0.2", "drift0.1", "ar-0.2", "ar-0.1", "vol1.5"]
    print(f"false-alarm spacing target = {target:.0f} bars; reps = {REPS}; horizon = {HORIZON}")
    print("sensor | " + " | ".join(f"{k} med/p90/found" for k in kinds) + " | FA spacing with bounce 0.5")
    for name, (fn, sign) in SENSORS.items():
        thr = calibrate(fn, sign, target)
        cells = []
        for k in kinds:
            med, p90, found = delays(fn, sign, thr, k)
            cells.append(f"{med:.0f}/{p90:.0f}/{found:.2f}")
        fa_b = bounce_false_alarms(fn, sign, thr, 0.5)
        print(f"{name} (thr {thr:.3f}) | " + " | ".join(cells) + f" | {fa_b:.0f}")


if __name__ == "__main__":
    main()
