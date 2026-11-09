"""Sanity checks for N3. Run: python -I sanity.py  -> results/sanity.json and printed lines.

1. Dukascopy 1m bars vs a second view: raw ticks for chosen hours (rebuild bid OHLC per minute,
   and the spread of every tick vs the last-tick-per-minute spread used in analyze.py).
2. Dukascopy 1m bars vs Dukascopy hourly (h1) bars for the same day.
3. Timestamps are UTC: the minute where the US500 1m range jumps should be 13:30 UTC while
   New York is on summer time (EDT, UTC-4) and 14:30 UTC on winter time (EST, UTC-5).
4. Weekday coverage of every file (no Saturday bars; Sunday only the evening re-open).
5. Crypto proxy check: Hyperliquid's own 1m/5m candles vs Binance perps over the overlap.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA, OUT = HERE / "data", HERE / "results"
OUT.mkdir(exist_ok=True)
res = {}


def bars(path):
    df = pd.read_csv(path)
    df["t"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    return df


# 1 + 2: ticks and h1 vs m1
tick_checks = []
for f in sorted(DATA.glob("sanity_tick_*.csv")):
    inst = f.stem.split("_")[2]
    hour = pd.Timestamp("-".join(f.stem.split("_")[3].split("-")[:3]) + " " + f.stem.split("-")[-1] + ":00", tz="UTC")
    period = "a" if hour >= pd.Timestamp("2026-08-11", tz="UTC") else "b"
    ticks = pd.read_csv(f)
    ticks["t"] = pd.to_datetime(ticks["ts"], unit="ms", utc=True)
    ticks["m"] = ticks["t"].dt.floor("min")
    tb = ticks.groupby("m").agg(open=("bid", "first"), high=("bid", "max"), low=("bid", "min"), close=("bid", "last"),
                                 ask_close=("ask", "last"))
    m1 = bars(DATA / f"duka_{inst}_{period}_bid.csv").set_index("t")
    a1 = bars(DATA / f"duka_{inst}_{period}_ask.csv").set_index("t")
    m1 = m1.loc[tb.index.intersection(m1.index)]
    j = tb.join(m1[["open", "high", "low", "close"]], rsuffix="_m1", how="inner")
    j = j.join(a1[["close"]].rename(columns={"close": "ask_close_m1"}), how="inner")
    rng_tick, rng_m1 = j["high"] - j["low"], j["high_m1"] - j["low_m1"]
    tick_spread = (ticks["ask"] - ticks["bid"])
    tick_checks.append({
        "file": f.name, "minutes_compared": len(j),
        "ohlc_exact_match_share": float(((j["open"] == j["open_m1"]) & (j["high"] == j["high_m1"]) & (j["low"] == j["low_m1"]) & (j["close"] == j["close_m1"])).mean()),
        "median_abs_range_diff": float((rng_tick - rng_m1).abs().median()),
        "median_range_tick": float(rng_tick.median()), "median_range_m1": float(rng_m1.median()),
        "spread_all_ticks_median": float(tick_spread.median()),
        "spread_tick_time_weighted_median": float((j["ask_close"] - j["close"]).median()),
        "spread_m1_last_tick_median": float((j["ask_close_m1"] - j["close_m1"]).median()),
    })
    # h1 vs m1 for the whole day
    day = hour.strftime("%Y-%m-%d")
    h1 = bars(DATA / f"sanity_h1_{inst}_{day}.csv")
    h1 = h1[h1["volume"] > 0].set_index("t")
    full = bars(DATA / f"duka_{inst}_{period}_bid.csv")
    full = full[full["t"].dt.strftime("%Y-%m-%d") == day]
    agg = full.groupby(full["t"].dt.floor("h")).agg(high=("high", "max"), low=("low", "min"), open=("open", "first"), close=("close", "last"))
    jj = h1[["open", "high", "low", "close"]].join(agg, rsuffix="_m1", how="inner")
    tick_checks[-1]["h1_hours_compared"] = len(jj)
    tick_checks[-1]["h1_high_low_exact_share"] = float(((jj["high"] - jj["high_m1"]).abs().lt(1e-9) & (jj["low"] - jj["low_m1"]).abs().lt(1e-9)).mean())
    tick_checks[-1]["h1_max_abs_diff"] = float(np.nanmax(np.abs(jj[["high", "low", "open", "close"]].values - jj[["high_m1", "low_m1", "open_m1", "close_m1"]].values)))
res["tick_and_h1_vs_m1"] = tick_checks

# 3: UTC check on US500 - average 1m range per minute-of-day, NY summer vs winter weeks
us = pd.concat([bars(DATA / "duka_usa500idxusd_a_bid.csv"), bars(DATA / "duka_usa500idxusd_b_bid.csv")])
us = us[us["t"].dt.day_of_week < 5]
us["r"] = us["high"] - us["low"]
us["mod"] = us["t"].dt.strftime("%H:%M")
# US DST 2025 ended Nov 2; 2026 starts Mar 8, ends Nov 1.
summer = us[(us["t"] >= "2026-08-11") & (us["t"] < "2026-10-31")]
winter = us[((us["t"] >= "2025-11-03") & (us["t"] < "2026-02-28")) | (us["t"] >= "2026-11-02")]
def jump(df):
    m = df.groupby("mod")["r"].median()
    d = (m - m.shift(1)).sort_values(ascending=False)
    return [{"minute_utc": k, "median_1m_range": float(m[k]), "previous_minute": float(m.shift(1)[k])} for k in d.index[:3]]
res["utc_check_us500_biggest_jump_minutes"] = {"ny_summer_time_weeks": jump(summer), "ny_winter_time_weeks": jump(winter)}

# 4: weekday coverage
cov = {}
for f in sorted(DATA.glob("duka_*_bid.csv")) + sorted(DATA.glob("binance_*.csv")):
    t = bars(f)
    t = t[t["volume"] > 0]
    dow = t["t"].dt.day_of_week.value_counts().sort_index()
    sun = t[t["t"].dt.day_of_week == 6]["t"].dt.hour
    cov[f.name] = {"active_minutes_by_weekday_mon0": {int(k): int(v) for k, v in dow.items()},
                   "sunday_first_hour_utc": int(sun.min()) if len(sun) else None}
res["weekday_coverage"] = cov

# 5: Hyperliquid vs Binance proxy
px = {}
for coin in ["BTC", "ETH", "SOL"]:
    hl1, bn = bars(DATA / f"hl_{coin}_1m_recent.csv"), bars(DATA / f"binance_{coin}_a.csv")
    j = hl1.set_index("ts")[["high", "low", "close"]].join(bn.set_index("ts")[["high", "low", "close"]], lsuffix="_hl", rsuffix="_bn", how="inner")
    r_hl, r_bn = (j["high_hl"] - j["low_hl"]) / j["close_hl"], (j["high_bn"] - j["low_bn"]) / j["close_bn"]
    hl5 = bars(DATA / f"hl_{coin}_5m_recent.csv")
    bb = bn.assign(blk=(bn["ts"] // 300_000) * 300_000).groupby("blk").agg(high=("high", "max"), low=("low", "min"), close=("close", "last"), n=("ts", "size"))
    bb = bb[bb["n"] == 5]
    j5 = hl5.set_index("ts")[["high", "low", "close"]].join(bb[["high", "low", "close"]], lsuffix="_hl", rsuffix="_bn", how="inner")
    r5_hl, r5_bn = (j5["high_hl"] - j5["low_hl"]) / j5["close_hl"], (j5["high_bn"] - j5["low_bn"]) / j5["close_bn"]
    px[coin] = {
        "overlap_1m_bars": len(j), "overlap_1m_from": str(pd.to_datetime(j.index.min(), unit="ms", utc=True)), "overlap_1m_to": str(pd.to_datetime(j.index.max(), unit="ms", utc=True)),
        "median_1m_range_pct_hl": float(r_hl.median() * 100), "median_1m_range_pct_binance": float(r_bn.median() * 100),
        "corr_1m_range": float(r_hl.corr(r_bn)),
        "median_abs_close_gap_pct": float(((j["close_hl"] - j["close_bn"]) / j["close_bn"]).abs().median() * 100),
        "overlap_5m_blocks": len(j5), "median_5m_range_pct_hl": float(r5_hl.median() * 100), "median_5m_range_pct_binance": float(r5_bn.median() * 100),
        "corr_5m_range": float(r5_hl.corr(r5_bn)),
    }
res["hyperliquid_vs_binance"] = px

(OUT / "sanity.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
