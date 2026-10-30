"""How much faster is a volatility jump seen from bar ranges or ticks than from closes?

Each 1-minute bar is SUB Brownian sub-steps (a stand-in for ticks). Sensors compare
a rolling volatility estimate with the known baseline and alarm above a threshold
calibrated to one alarm episode per TARGET bars on no-change data. Then volatility
rises by K and we count bars to the first alarm.
Run: python -I mis_range_speed.py
"""
import numpy as np

RNG = np.random.default_rng(11)
SUB = 60
TARGET = 14400
REPS = 300
K = 1.5
PARK = 1 / (4 * np.log(2))


def bars(n, scale=1.0):
    steps = RNG.standard_normal((n, SUB)) * scale / np.sqrt(SUB)
    path = np.cumsum(steps, axis=1)
    close = path[:, -1]
    hi = np.maximum(path.max(axis=1), 0.0)
    lo = np.minimum(path.min(axis=1), 0.0)
    tick_rv = (steps ** 2).sum(axis=1)
    return close, hi - lo, tick_rv


def roll_mean(x, n):
    c = np.cumsum(np.insert(x, 0, 0.0))
    out = np.full(x.shape, np.nan)
    out[n - 1:] = (c[n:] - c[:-n]) / n
    return out


SENSORS = {
    "closes RV, 30 bars": lambda c, r, t: roll_mean(c ** 2, 30),
    "closes RV, 10 bars": lambda c, r, t: roll_mean(c ** 2, 10),
    "range (Parkinson), 10 bars": lambda c, r, t: roll_mean(PARK * r ** 2, 10),
    "range (Parkinson), 3 bars": lambda c, r, t: roll_mean(PARK * r ** 2, 3),
    "ticks RV, 3 bars": lambda c, r, t: roll_mean(t, 3),
    "ticks RV, 1 bar": lambda c, r, t: roll_mean(t, 1),
}


def spacing(stat, thr):
    a = np.nan_to_num(stat > thr, nan=False).astype(bool)
    ups = np.sum(a[1:] & ~a[:-1])
    return np.sum(~np.isnan(stat)) / max(ups, 1)


def calibrate(fn):
    c, r, t = bars(300_000)
    s = fn(c, r, t)
    v = s[~np.isnan(s)]
    lo, hi = 0.5, 0.999999
    for _ in range(40):
        mid = (lo + hi) / 2
        if spacing(s, np.quantile(v, mid)) < TARGET:
            lo = mid
        else:
            hi = mid
    return np.quantile(v, hi)


def main():
    print(f"vol x{K}, one alarm episode per {TARGET} bars, {SUB} sub-steps per bar")
    for name, fn in SENSORS.items():
        thr = calibrate(fn)
        d = []
        for _ in range(REPS):
            c0, r0, t0 = bars(100)
            c1, r1, t1 = bars(2000, K)
            s = fn(np.concatenate([c0, c1]), np.concatenate([r0, r1]), np.concatenate([t0, t1]))[100:]
            hit = np.nonzero(np.nan_to_num(s > thr, nan=False))[0]
            d.append(hit[0] if len(hit) else np.inf)
        d = np.array(d)
        print(f"{name:28s} median {np.median(d):5.0f} bars  p90 {np.quantile(d, 0.9):5.0f}")


if __name__ == "__main__":
    main()
