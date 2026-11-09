"""Repeatability check: do the best hours and ratios hold between the first and second half of period a?

Run: python -I split_half.py  -> results/split_half.csv
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # -I drops the script folder from sys.path; add our own folder back
import pandas as pd  # noqa: E402
import analyze as A  # noqa: E402

CUT = pd.Timestamp("2026-09-25", tz="UTC")  # ~45 days into the 90-day window
rows = []
for name in list(A.DUKA) + A.CRYPTO:
    if name in A.DUKA:
        df = A.load_duka(A.DUKA[name], "a")
    else:
        df = A.load_ohlc(A.DATA / f"binance_{name}_a.csv")
    df, _ = A.keep_weekdays(df)
    out = {"instrument": name}
    for half, part in (("h1", df[df["t"] < CUT]), ("h2", df[df["t"] >= CUT])):
        st = A.hourly_stats(part, A.five_minute(part), has_spread=name in A.DUKA)
        if name in A.DUKA:
            st["ratio_all"] = st["r5_med"] / (st["spread_med"] + [A.commission_price_units(name, p) for p in st["price"]])
        else:
            st["ratio_all"] = st["r5p_med"] / (2 * A.HL_TAKER * 100)  # fee only; spread is a constant snapshot anyway
        top = A.top3(st, "ratio_all")
        out[f"best_{half}"] = sorted(top)
        out[f"ratio_{half}"] = round(st.loc[top, "ratio_all"].mean(), 2)
        out[f"days_{half}"] = part["t"].dt.date.nunique()
    rows.append(out)
res = pd.DataFrame(rows)
res.to_csv(A.OUT / "split_half.csv", index=False)
print(res.to_string())
