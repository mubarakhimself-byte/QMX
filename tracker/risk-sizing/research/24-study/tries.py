import numpy as np
rng = np.random.default_rng(11)
T = 500  # trades on a shared clock (daily R, say)
def family(n_tweak, rho_tweak, n_distinct, rho_distinct):
    base = rng.normal(0, 1, T)
    series = [base]
    for _ in range(n_tweak):   # exit or number tweaks: mostly the same trades
        series.append(rho_tweak * base + np.sqrt(1 - rho_tweak**2) * rng.normal(0, 1, T))
    common = rng.normal(0, 1, T)
    for _ in range(n_distinct):  # different blocks: different trades
        series.append(rho_distinct * common + np.sqrt(1 - rho_distinct**2) * rng.normal(0, 1, T))
    X = np.array(series)
    C = np.corrcoef(X)
    ev = np.linalg.eigvalsh(C)
    n_eff = ev.sum()**2 / (ev**2).sum()
    return len(series), n_eff
for args in [(40, 0.95, 0, 0.2), (0, 0.95, 40, 0.2), (40, 0.95, 10, 0.2), (40, 0.80, 10, 0.2)]:
    n, ne = family(*args)
    print(f"tweaks={args[0]} (corr {args[1]}), distinct={args[2]}: raw tries {n}, effective tries {ne:.1f}")

def clusters(C, thr=0.5):
    n = len(C); seen = [False]*n; k = 0
    for i in range(n):
        if seen[i]: continue
        k += 1; stack = [i]; seen[i] = True
        while stack:
            j = stack.pop()
            for m in range(n):
                if not seen[m] and C[j, m] > thr:
                    seen[m] = True; stack.append(m)
    return k
print("-- threshold clustering (corr > 0.5 joins a cluster), a crude stand-in for ONC")
for args in [(40, 0.95, 0, 0.2), (0, 0.95, 40, 0.2), (40, 0.95, 10, 0.2), (40, 0.80, 10, 0.2)]:
    base = rng.normal(0, 1, T); series = [base]
    for _ in range(args[0]): series.append(args[1]*base + np.sqrt(1-args[1]**2)*rng.normal(0, 1, T))
    common = rng.normal(0, 1, T)
    for _ in range(args[2]): series.append(args[3]*common + np.sqrt(1-args[3]**2)*rng.normal(0, 1, T))
    C = np.corrcoef(np.array(series))
    print(f"tweaks={args[0]} (corr {args[1]}), distinct={args[2]}: raw {len(series)}, clusters {clusters(C)}")
