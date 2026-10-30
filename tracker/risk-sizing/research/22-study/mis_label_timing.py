"""Does a state label known at entry lift a scalper as much as the same label known afterwards?

Simulated 1-minute bars switch between random walk and AR(1) mean reversion
(phi = -0.2), each spell lasting a geometric number of bars (mean SPELL). A
fade-the-last-bar scalper trades every bar it is allowed to, paying COST (in
bar-sigma) per trade. Gates compared:
  none       trade always
  oracle     true regime (impossible live)
  centred    AC1 over a window centred on the bar (uses future bars: look-ahead)
  at-entry   AC1 over the trailing window ending at the bar (what live can know)
Run: python -I mis_label_timing.py
"""
import numpy as np

RNG = np.random.default_rng(7)
T = 2_000_000
SPELL = 720
PHI = -0.2
COST = 0.05
WIN = 240
THR = -0.08


def simulate():
    state = np.zeros(T, dtype=bool)
    i, s = 0, False
    while i < T:
        n = RNG.geometric(1 / SPELL)
        state[i:i + n] = s
        s = not s
        i += n
    e = RNG.standard_normal(T)
    r = np.empty(T)
    prev = 0.0
    scale = 1 / np.sqrt(1 / (1 - PHI ** 2))
    for t in range(T):
        prev = (PHI * prev if state[t] else 0.0) + e[t]
        r[t] = prev * (scale if state[t] else 1.0)
    return state, r


def roll(x, n):
    c = np.cumsum(np.insert(x, 0, 0.0))
    out = np.full(x.shape, np.nan)
    out[n - 1:] = c[n:] - c[:-n]
    return out


def main():
    state, r = simulate()
    lag = np.concatenate([[0.0], r[:-1]])
    ac_trail = roll(r * lag, WIN) / roll(r ** 2, WIN)
    half = WIN // 2
    ac_centred = np.full(T, np.nan)
    ac_centred[:-half] = ac_trail[half:]
    pnl = -np.sign(r[:-1]) * r[1:] - COST
    gates = {
        "none": np.ones(T - 1, dtype=bool),
        "oracle": state[1:],
        "centred": np.nan_to_num(ac_centred[:-1] < THR, nan=False).astype(bool),
        "at-entry": np.nan_to_num(ac_trail[:-1] < THR, nan=False).astype(bool),
    }
    print(f"bars {T}, mean spell {SPELL}, phi {PHI}, cost {COST} sigma, window {WIN}, threshold {THR}")
    for name, g in gates.items():
        g = g.astype(bool)
        n = g.sum()
        print(f"{name:9s} trades {n:9d}  mean pnl/trade {pnl[g].mean():+.4f} sigma  total {pnl[g].sum():+.0f}")


if __name__ == "__main__":
    main()
