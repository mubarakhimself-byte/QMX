"""N4 repeatability: best hours and ratio in the two 45-day halves of period a, for every N4 Dukascopy instrument.
Also a timestamp check: the UTC hour where each instrument's median 1m range jumps most (should be its cash open).
Run: python -I split_half_n4.py -> results/n4_split_half.csv
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pandas as pd  # noqa: E402
import analyze as A  # noqa: E402
import analyze_n4 as N  # noqa: E402

CUT = pd.Timestamp("2026-09-25", tz="UTC")
rows = []
for name, (inst, *_r) in N.INST.items():
    df, _ = A.keep_weekdays(A.load_duka(inst, "a"))
    out = {"instrument": name}
    for half, part in (("h1", df[df["t"] < CUT]), ("h2", df[df["t"] >= CUT])):
        if part.empty:
            out[f"best_{half}"], out[f"ratio_{half}"], out[f"days_{half}"] = [], None, 0
            continue
        st = A.hourly_stats(part, A.five_minute(part), has_spread=True)
        st["ratio_all"] = st["r5_med"] / (st["spread_med"] + [N.commission(name, p) for p in st["price"]])
        top = A.top3(st, "ratio_all")
        out[f"best_{half}"] = sorted(top)
        out[f"ratio_{half}"] = round(st.loc[top, "ratio_all"].mean(), 2) if top else None
        out[f"days_{half}"] = part["t"].dt.date.nunique()
    # biggest jump in median 1m range between consecutive UTC hours (old part of period a, summer time: before 2026-10-25)
    s = df[df["t"] < pd.Timestamp("2026-10-24", tz="UTC")]
    s = s[s["active"]]
    med = (s["high"] - s["low"]).groupby(s["t"].dt.hour).median().reindex(range(24))
    jump = (med / med.shift(1).replace(0, float("nan")))
    out["biggest_1m_jump_hour_utc_summer"] = int(jump.idxmax()) if jump.notna().any() else None
    out["jump_factor"] = round(float(jump.max()), 2) if jump.notna().any() else None
    rows.append(out)
res = pd.DataFrame(rows)
res.to_csv(A.OUT / "n4_split_half.csv", index=False)
print(res.to_string())
