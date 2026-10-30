import numpy as np
rng = np.random.default_rng(7)

def trades(edge, n, size):
    # +1R / -1R trades with mean = edge
    p = (1 + edge) / 2
    return np.where(rng.random((size, n)) < p, 1.0, -1.0)

# 1) sequential e-process (mixture of betting e-values) vs fixed count
lams = np.array([0.025, 0.05, 0.1, 0.2])
def eproc_cross(x, thr=20.0):
    # x: (sims, n). log wealth per lambda, mixture = mean of wealths
    logw = np.cumsum(np.log1p(x[:, :, None] * lams[None, None, :]), axis=1)
    mix = np.exp(logw).mean(axis=2)
    hit = mix >= thr
    first = np.where(hit.any(axis=1), hit.argmax(axis=1) + 1, -1)
    return first

for edge in [0.0, 0.05, 0.1, 0.15]:
    x = trades(edge, 3000, 4000)
    f = eproc_cross(x)
    crossed = f > 0
    med = np.median(f[crossed]) if crossed.any() else float('nan')
    q90 = np.quantile(f[crossed], 0.9) if crossed.any() else float('nan')
    print(f"e-process edge={edge:+.2f}R: crossed within 3000 trades {crossed.mean():.3f}; median trades {med:.0f}; 90th pct {q90:.0f}")

# fixed-count one-sided t test at n=270, power check
for edge in [0.05, 0.1]:
    x = trades(edge, 270, 20000)
    t = x.mean(1) / (x.std(1, ddof=1) / np.sqrt(270))
    print(f"fixed n=270, edge {edge}: power {np.mean(t > 1.645):.3f}")
x = trades(0.0, 270, 20000); t = x.mean(1) / (x.std(1, ddof=1) / np.sqrt(270))
print(f"fixed n=270, edge 0: false pass {np.mean(t > 1.645):.3f}")

# 2) winner's curse: pick best of N markets by its own record
def pick(N, n, prior_mu=0.02, prior_sd=0.05, sims=4000, k=None):
    true = rng.normal(prior_mu, prior_sd, (sims, N))
    p = np.clip((1 + true) / 2, 0.01, 0.99)
    wins = rng.binomial(n, p)
    obs = (2 * wins - n) / n
    best = obs.argmax(1)
    idx = np.arange(sims)
    raw = obs[idx, best]; tru = true[idx, best]
    # shrink toward pooled mean of all N markets; w = n/(n+k), k = var_noise/var_true
    pooled = obs.mean(1)
    kk = (1.0 / prior_sd**2) if k is None else k   # noise var per trade ~1
    w = n / (n + kk)
    shr = w * raw + (1 - w) * pooled
    return raw.mean(), tru.mean(), shr.mean(), np.mean(tru > 0)

for N in [5, 20, 100]:
    for n in [30, 100, 300, 1000]:
        raw, tru, shr, pos = pick(N, n)
        print(f"best of N={N:3d} markets, n={n:4d} trades each: looks {raw:+.3f}R, true {tru:+.3f}R, shrunk {shr:+.3f}R, P(true>0) {pos:.2f}")

# 3) one week of recorded data: standard error of mean R
for tr in [20, 60, 150, 400]:
    print(f"{tr} trades: standard error of mean R about {1/np.sqrt(tr):.3f}R")
