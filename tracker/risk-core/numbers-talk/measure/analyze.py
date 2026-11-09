"""N3 analysis: how much do markets move per 1m / 5m, against what a round trip costs, by UTC hour.

Run with the scratch venv: python -I analyze.py
Reads data/ (written by fetch_dukascopy.mjs, fetch_crypto.py), writes results/.

Definitions used everywhere below
  1m range   = high - low of one 1-minute bar (bid prices for Dukascopy, trade prices for crypto).
  5m range   = highest high - lowest low across the five 1m bars of a clock-aligned 5-minute block.
  spread     = ask close - bid close of the same minute (Dukascopy: both come from the minute's last tick).
  hour       = UTC hour the bar (or 5m block) starts in.
  ratio      = median 5m range in that hour / round-trip cost in that hour.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)

DUKA = {  # name: dukascopy id
    "EURUSD": "eurusd", "GBPUSD": "gbpusd", "USDJPY": "usdjpy", "XAUUSD": "xauusd",
    "US500": "usa500idxusd", "US100": "usatechidxusd", "DE40": "deuidxeur",
    "JP225": "jpnidxjpy", "HK50": "hkgidxhkd", "AU200": "ausidxaud", "UK100": "gbridxgbp", "EU50": "eusidxeur",
}

# World sessions, defined on local exchange clocks so daylight-saving changes do not blur them.
# Order matters: the first matching rule wins.
def session_of(t: pd.Series) -> pd.Series:
    ny = t.dt.tz_convert("America/New_York")
    de = t.dt.tz_convert("Europe/Berlin")
    nym = ny.dt.hour * 60 + ny.dt.minute
    dem = de.dt.hour * 60 + de.dt.minute
    utc_h = t.dt.hour
    s = pd.Series("other", index=t.index)
    s[(utc_h >= 0) & (utc_h < 7)] = "Asia (00-07 UTC)"
    s[(dem >= 9 * 60) & (nym < 8 * 60)] = "Europe (Frankfurt 09:00 to New York 08:00)"
    s[(nym >= 8 * 60) & (nym < 9 * 60 + 30)] = "London-New York overlap (NY 08:00-09:30)"
    s[(nym >= 9 * 60 + 30) & (nym < 11 * 60)] = "US open (NY 09:30-11:00)"
    s[(nym >= 11 * 60) & (nym < 15 * 60)] = "US afternoon (NY 11:00-15:00)"
    s[(nym >= 15 * 60) & (nym < 16 * 60 + 15)] = "US close (NY 15:00-16:15)"
    return s

SESSIONS = ["Asia (00-07 UTC)", "Europe (Frankfurt 09:00 to New York 08:00)", "London-New York overlap (NY 08:00-09:30)",
            "US open (NY 09:30-11:00)", "US afternoon (NY 11:00-15:00)", "US close (NY 15:00-16:15)"]
CRYPTO = ["BTC", "ETH", "SOL"]
PERIODS = {"a": "last 90 days (2026-08-11..2026-11-08)", "b": "2025-11-01..2026-02-28"}

# ASSUMED commission: $3.5 per side per standard lot => $7 round trip per lot, expressed in price units.
# FX standard lot = 100,000 base units; gold lot = 100 oz; index CFDs assumed spread-only (0).
def commission_price_units(name: str, price: float) -> float:
    if name in ("EURUSD", "GBPUSD"):
        return 7.0 / 100_000             # USD per EUR/GBP
    if name == "USDJPY":
        return 7.0 / 100_000 * price     # $7 per $100k notional, in JPY per USD
    if name == "XAUUSD":
        return 7.0 / 100                 # USD per oz
    return 0.0

# Hyperliquid perps base tier (tier 0, no staking/referral), docs page read 2026-11-09:
# https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees  -> taker 0.045%, maker 0.015%
HL_TAKER, HL_MAKER = 0.00045, 0.00015

HOLIDAY_SHARE = 0.5   # a weekday with fewer ticked minutes than this share of the median weekday is dropped
OPEN_SHARE = 0.8      # an hour counts as tradeable only if >= this share of its minutes had ticks


def load_duka(inst: str, period: str) -> pd.DataFrame:
    bid = pd.read_csv(DATA / f"duka_{inst}_{period}_bid.csv")
    ask = pd.read_csv(DATA / f"duka_{inst}_{period}_ask.csv")
    df = bid.merge(ask[["ts", "close", "high", "low"]].rename(columns={"close": "ask_close", "high": "ask_high", "low": "ask_low"}), on="ts", how="inner")
    df["t"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df["active"] = df["volume"] > 0
    df["spread"] = df["ask_close"] - df["close"]
    return df


def load_ohlc(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["t"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df["active"] = df["volume"] > 0
    return df


def keep_weekdays(df: pd.DataFrame):
    """Drop Saturday/Sunday (UTC) and low-activity weekdays (holidays). Returns (df, dropped_days)."""
    df = df[df["t"].dt.day_of_week < 5].copy()
    df["day"] = df["t"].dt.date
    per_day = df.groupby("day")["active"].sum()
    cut = HOLIDAY_SHARE * per_day.median()
    dropped = per_day[per_day < cut]
    df = df[~df["day"].isin(dropped.index)]
    return df, dropped


def five_minute(df: pd.DataFrame) -> pd.DataFrame:
    b = df.assign(blk=(df["ts"] // 300_000) * 300_000).groupby("blk").agg(
        high=("high", "max"), low=("low", "min"), close=("close", "last"), n=("ts", "size"),
        active=("active", "sum"))
    b = b[b["n"] == 5]  # only complete blocks
    b["t"] = pd.to_datetime(b.index, unit="ms", utc=True)
    b["range"] = b["high"] - b["low"]
    return b


def hourly_stats(df: pd.DataFrame, b5: pd.DataFrame, has_spread: bool) -> pd.DataFrame:
    df = df.assign(hour=df["t"].dt.hour, r1=df["high"] - df["low"])
    df["r1p"] = df["r1"] / df["close"] * 100
    b5 = b5.assign(hour=b5["t"].dt.hour)
    b5["r5p"] = b5["range"] / b5["close"] * 100
    g1 = df.groupby("hour")
    g5 = b5.groupby("hour")
    st = pd.DataFrame({
        "active_share": g1["active"].mean(),
        "minutes": g1.size(),
        "price": g1["close"].median(),
        "r1_med": g1["r1"].median(), "r1_p75": g1["r1"].quantile(0.75),
        "r1p_med": g1["r1p"].median(), "r1p_p75": g1["r1p"].quantile(0.75),
        "r5_med": g5["range"].median(), "r5_p75": g5["range"].quantile(0.75),
        "r5p_med": g5["r5p"].median(), "r5p_p75": g5["r5p"].quantile(0.75),
        "blocks5": g5.size(),
    })
    if has_spread:
        act = df[df["active"]]
        st["spread_med"] = act.groupby("hour")["spread"].median()
        st["spread_p75"] = act.groupby("hour")["spread"].quantile(0.75)
        st["spreadp_med"] = st["spread_med"] / st["price"] * 100
    return st


def session_stats(df: pd.DataFrame, b5: pd.DataFrame, has_spread: bool) -> pd.DataFrame:
    """Same measures as hourly_stats, grouped by world session (local exchange clocks)."""
    df = df.assign(sess=session_of(df["t"]))
    b5 = b5.assign(sess=session_of(b5["t"]), r5p=b5["range"] / b5["close"] * 100)
    # Only 5m blocks where the market was open (>= 3 of 5 minutes had ticks), so lunch breaks and
    # closed stretches inside a session do not pull the median toward zero.
    b5 = b5[b5["active"] >= 3]
    st = pd.DataFrame({
        "active_share": df.groupby("sess")["active"].mean(),
        "price": df.groupby("sess")["close"].median(),
        "r5_med": b5.groupby("sess")["range"].median(),
        "r5p_med": b5.groupby("sess")["r5p"].median(),
        "blocks5": b5.groupby("sess").size(),
    })
    if has_spread:
        st["spread_med"] = df[df["active"]].groupby("sess")["spread"].median()
    return st.reindex(SESSIONS)


def top3(st: pd.DataFrame, col: str) -> list:
    ok = st[st["active_share"] >= OPEN_SHARE]
    return list(ok[col].sort_values(ascending=False).index[:3])


def main():
    hourly, sessions, dropped_log, outliers, rets = {}, {}, {}, {}, {}
    # ---------------- Dukascopy instruments ----------------
    for name, inst in DUKA.items():
        for p in PERIODS:
            df = load_duka(inst, p)
            n_all = len(df)
            weekend_rows = int((df["t"].dt.day_of_week >= 5).sum())
            df, dropped = keep_weekdays(df)
            dropped_log[(name, p)] = {"rows_loaded": n_all, "weekend_rows_dropped": weekend_rows,
                                      "holiday_days_dropped": [str(d) for d in dropped.index],
                                      "days_kept": int(df["day"].nunique()),
                                      "neg_spread_minutes": int((df["spread"] < 0).sum()),
                                      "zero_range_active_minutes": int(((df["high"] == df["low"]) & df["active"]).sum())}
            b5 = five_minute(df)
            st = hourly_stats(df, b5, has_spread=True)
            st["comm"] = [commission_price_units(name, px) for px in st["price"]]
            st["cost_spread"] = st["spread_med"]
            st["cost_all"] = st["spread_med"] + st["comm"]
            st["ratio_spread"] = st["r5_med"] / st["cost_spread"]
            st["ratio_all"] = st["r5_med"] / st["cost_all"]
            hourly[(name, p)] = st
            ss = session_stats(df, b5, has_spread=True)
            ss["cost_all"] = ss["spread_med"] + [commission_price_units(name, px) for px in ss["price"]]
            ss["ratio_all"] = ss["r5_med"] / ss["cost_all"]
            sessions[(name, p)] = ss
            big = b5.sort_values("range", ascending=False).head(3)
            outliers[(name, p)] = [(str(t), float(r), float(r / c * 100)) for t, r, c in zip(big["t"], big["range"], big["close"])]
            if p == "a":
                act = b5[b5["active"] > 0]
                rets[name] = np.log(act["close"]).diff().where(act.index.to_series().diff() == 300_000)
    # ---------------- Crypto (Binance perps = PROXY for the move, Hyperliquid = cost) ----------------
    snaps = [json.loads(l) for l in (DATA / "hl_l2book_snapshots.jsonl").read_text().splitlines() if l.strip()]
    snap = pd.DataFrame(snaps)
    snap["spread"] = snap["ask"] - snap["bid"]
    snap["spread_pct"] = snap["spread"] / ((snap["ask"] + snap["bid"]) / 2) * 100
    snap_med = snap.groupby("coin").agg(spread=("spread", "median"), spread_pct=("spread_pct", "median"),
                                        spread_pct_max=("spread_pct", "max"), n=("spread", "size"))
    weekend_cmp = {}
    for coin in CRYPTO:
        for p in PERIODS:
            raw = load_ohlc(DATA / f"binance_{coin}_{p}.csv")
            wk = raw[raw["t"].dt.day_of_week >= 5]
            df, dropped = keep_weekdays(raw)
            dropped_log[(coin, p)] = {"rows_loaded": len(raw), "weekend_rows_dropped": len(wk),
                                      "holiday_days_dropped": [str(d) for d in dropped.index], "days_kept": int(df["day"].nunique())}
            b5 = five_minute(df)
            st = hourly_stats(df, b5, has_spread=False)
            half_spread_pct = snap_med.loc[coin, "spread_pct"] / 2
            st["cost_taker_pct"] = 2 * HL_TAKER * 100 + half_spread_pct      # brief's formula
            st["cost_taker_fullspread_pct"] = 2 * HL_TAKER * 100 + 2 * half_spread_pct
            st["cost_maker_pct"] = 2 * HL_MAKER * 100
            st["ratio_all"] = st["r5p_med"] / st["cost_taker_pct"]
            st["ratio_maker"] = st["r5p_med"] / st["cost_maker_pct"]
            st["ratio_taker_fullspread"] = st["r5p_med"] / st["cost_taker_fullspread_pct"]
            hourly[(coin, p)] = st
            ss = session_stats(df, b5, has_spread=False)
            ss["cost_all_pct"] = st["cost_taker_pct"].iloc[0]
            ss["ratio_all"] = ss["r5p_med"] / ss["cost_all_pct"]
            sessions[(coin, p)] = ss
            wb5 = five_minute(wk.assign(active=wk["volume"] > 0))
            weekend_cmp[(coin, p)] = {"weekday_r5p_med": float((b5["range"] / b5["close"]).median() * 100),
                                      "weekend_r5p_med": float((wb5["range"] / wb5["close"]).median() * 100)}
            big = b5.sort_values("range", ascending=False).head(3)
            outliers[(coin, p)] = [(str(t), float(r), float(r / c * 100)) for t, r, c in zip(big["t"], big["range"], big["close"])]
            if p == "a":
                rets[coin] = np.log(b5["close"]).diff().where(b5.index.to_series().diff() == 300_000)

    # ---------------- Summaries ----------------
    rows = []
    for name in list(DUKA) + CRYPTO:
        sa, sb = hourly[(name, "a")], hourly[(name, "b")]
        ta, tb = top3(sa, "ratio_all"), top3(sb, "ratio_all")
        same_rank = sa["ratio_all"].rank().corr(sb["ratio_all"].rank())  # Spearman = Pearson on ranks
        # how good are period-a best hours when traded in period b (out-of-sample check)
        rows.append({
            "instrument": name,
            "best_hours_a": ta, "ratio_best_a": sa.loc[ta, "ratio_all"].mean(),
            "best_hours_b": tb, "ratio_best_b": sb.loc[tb, "ratio_all"].mean(),
            "ratio_a_hours_in_b": sb.loc[ta, "ratio_all"].mean(),
            "overlap": len(set(ta) & set(tb)),
            "overlap_pm1h": sum(any(abs(h - k) <= 1 for k in tb) for h in ta),
            "spearman_24h": same_rank,
            "ratio_spreadonly_best_a": sa.loc[ta, "ratio_spread"].mean() if "ratio_spread" in sa else np.nan,
            "ratio_maker_best_a": sa.loc[ta, "ratio_maker"].mean() if "ratio_maker" in sa else np.nan,
            "r5_med_best_a": sa.loc[ta, "r5_med"].mean(), "r5p_med_best_a": sa.loc[ta, "r5p_med"].mean(),
            "cost_best_a": sa.loc[ta, "cost_all"].mean() if "cost_all" in sa else np.nan,
            "costp_best_a": (sa.loc[ta, "cost_all"] / sa.loc[ta, "price"] * 100).mean() if "cost_all" in sa else sa.loc[ta, "cost_taker_pct"].mean(),
            "ratio_worst_open_a": sa[sa["active_share"] >= OPEN_SHARE]["ratio_all"].min(),
            "open_hours_a": int((sa["active_share"] >= OPEN_SHARE).sum()),
        })
    summary = pd.DataFrame(rows).sort_values("ratio_best_a", ascending=False)
    summary.to_csv(OUT / "ranking.csv", index=False)
    pd.concat({f"{k[0]}|{k[1]}": v for k, v in hourly.items()}).to_csv(OUT / "hourly_detail.csv")
    pd.concat({f"{k[0]}|{k[1]}": v for k, v in sessions.items()}).to_csv(OUT / "session_detail.csv")

    R = pd.DataFrame(rets)
    corr = R.corr(min_periods=500)
    nobs = R.notna().astype(int).T @ R.notna().astype(int)
    corr.to_csv(OUT / "corr_5m_returns_a.csv")
    nobs.to_csv(OUT / "corr_nobs_a.csv")

    (OUT / "checks.json").write_text(json.dumps({
        "dropped": {f"{k[0]}|{k[1]}": v for k, v in dropped_log.items()},
        "outliers_top3_5m": {f"{k[0]}|{k[1]}": v for k, v in outliers.items()},
        "hl_snapshots": snap_med.reset_index().to_dict(orient="records"),
        "crypto_weekend_vs_weekday": {f"{k[0]}|{k[1]}": v for k, v in weekend_cmp.items()},
    }, indent=1, default=str))
    print(summary.to_string())
    print(corr.round(2).to_string())


if __name__ == "__main__":
    main()
