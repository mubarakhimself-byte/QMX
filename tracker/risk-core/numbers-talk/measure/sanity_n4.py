"""N4 sanity checks. Run: python -I sanity_n4.py -> results/n4_sanity.json
1. Key-pair correlations in period b (does the period-a picture hold a year earlier?).
2. Dukascopy median spread (all open hours) against the IC Markets / Pepperstone published average spread.
3. Largest 5m ranges for the new instruments (spikes or real moves?).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import analyze as A  # noqa: E402
import analyze_n4 as N  # noqa: E402

PAIRS = [("US30", "US100"), ("US30", "US500"), ("US100", "US500"), ("JP225", "US100"), ("DE40", "EU50"),
         ("DE40", "UK100"), ("WTI", "US500"), ("WTI", "BRENT"), ("XAUUSD", "XAGUSD"), ("CN50", "HK50"), ("NVDA", "US100")]
out = {"pairs": {}, "spreads": {}, "outliers": {}}
rets = {p: {} for p in ("a", "b")}
need = sorted({x for pr in PAIRS for x in pr})
for name in N.INST:
    inst = N.INST[name][0]
    for p in ("a", "b"):
        df, _ = A.keep_weekdays(A.load_duka(inst, p))
        b5 = A.five_minute(df)
        if name in need:
            act = b5[b5["active"] > 0]
            rets[p][name] = np.log(act["close"]).diff().where(act.index.to_series().diff() == 300_000)
        if p == "a":
            op = df[df["active"]]
            hr_open = op.groupby(op["t"].dt.hour)["active"].size() / df.groupby(df["t"].dt.hour).size()
            open_hours = hr_open[hr_open >= A.OPEN_SHARE].index
            sp = float(op[op["t"].dt.hour.isin(open_hours)]["spread"].median())
            out["spreads"][name] = {"duka_median_spread_open_hours": sp,
                                    "ic_avg": N.IC_AVG.get(name), "pep_avg": N.PEP_AVG.get(name),
                                    "ic_over_duka": (N.IC_AVG[name] / sp) if name in N.IC_AVG and sp else None}
            if N.INST[name][4]:
                big = b5.sort_values("range", ascending=False).head(3)
                out["outliers"][name] = [(str(t), round(float(r), 4), round(float(r / c * 100), 3)) for t, r, c in zip(big["t"], big["range"], big["close"])]
for p in ("a", "b"):
    R = pd.DataFrame(rets[p])
    for a, b in PAIRS:
        m = R[a].notna() & R[b].notna()
        out["pairs"].setdefault(f"{a}/{b}", {})[p] = round(float(R.loc[m, a].corr(R.loc[m, b])), 3)
(A.OUT / "n4_sanity.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out["pairs"], indent=1))
for k, v in out["spreads"].items():
    print(k, v)
for k, v in out["outliers"].items():
    print(k, v)
