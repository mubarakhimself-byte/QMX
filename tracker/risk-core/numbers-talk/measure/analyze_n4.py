"""N4 analysis: the global universe. Same method as N3 (median 5m high-low range / round-trip cost, per UTC hour),
for every Dukascopy instrument (N3's 12 + N4's 21 new), plus correlations, clusters and separate bets per session.

Run: python -I analyze_n4.py     (after run_dukascopy_all.sh with the N4 list, and N3's fetch_crypto.py data)
Writes results/n4_*.csv and results/n4_summary.json.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # -I drops the script folder from sys.path
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import analyze as A  # noqa: E402  (N3 helpers: load_duka, keep_weekdays, five_minute, hourly_stats, session_of, top3)

OUT = A.OUT
NY, BER, ZRH, LON, WAW, JNB = "America/New_York", "Europe/Berlin", "Europe/Zurich", "Europe/London", "Europe/Warsaw", "Africa/Johannesburg"
TYO, HKG, SHA, SIN, SYD = "Asia/Tokyo", "Asia/Hong_Kong", "Asia/Shanghai", "Asia/Singapore", "Australia/Sydney"

def hm(h, m=0):
    return h * 60 + m

US_CASH = (NY, [(hm(9, 30), hm(16))])
EU_CASH = (BER, [(hm(9), hm(17, 30))])
# name: (dukascopy id, group, unit, cash session (tz, [(start_min, end_min) local]), is_new)
INST = {
    "US100": ("usatechidxusd", "index", "pts", US_CASH, False),
    "US500": ("usa500idxusd", "index", "pts", US_CASH, False),
    "US30": ("usa30idxusd", "index", "pts", US_CASH, True),
    "US2000": ("ussc2000idxusd", "index", "pts", US_CASH, True),
    "DE40": ("deuidxeur", "index", "pts", EU_CASH, False),
    "EU50": ("eusidxeur", "index", "pts", EU_CASH, False),
    "FR40": ("fraidxeur", "index", "pts", (BER, [(hm(9), hm(17, 30))]), True),
    "NL25": ("nldidxeur", "index", "pts", (BER, [(hm(9), hm(17, 30))]), True),
    "IT40": ("itaidxeur", "index", "pts", (BER, [(hm(9), hm(17, 30))]), True),
    "ES35": ("espidxeur", "index", "pts", (BER, [(hm(9), hm(17, 30))]), True),
    "CH20": ("cheidxchf", "index", "pts", (ZRH, [(hm(9), hm(17, 20))]), True),
    "UK100": ("gbridxgbp", "index", "pts", (LON, [(hm(8), hm(16, 30))]), False),
    "PL20": ("plnidxpln", "index", "pts", (WAW, [(hm(9), hm(16, 50))]), True),
    "SA40": ("soaidxzar", "index", "pts", (JNB, [(hm(9), hm(17))]), True),
    "JP225": ("jpnidxjpy", "index", "pts", (TYO, [(hm(9), hm(11, 30)), (hm(12, 30), hm(15, 30))]), False),
    "HK50": ("hkgidxhkd", "index", "pts", (HKG, [(hm(9, 30), hm(12)), (hm(13), hm(16))]), False),
    "CN50": ("chiidxusd", "index", "pts", (SHA, [(hm(9, 30), hm(11, 30)), (hm(13), hm(15))]), True),
    "SG": ("sgdidxsgd", "index", "pts", (SIN, [(hm(9), hm(12)), (hm(13), hm(17))]), True),
    "AU200": ("ausidxaud", "index", "pts", (SYD, [(hm(10), hm(16))]), False),
    "XAUUSD": ("xauusd", "metal", "USD/oz", (NY, [(hm(8, 20), hm(13, 30))]), False),
    "XAGUSD": ("xagusd", "metal", "USD/oz", (NY, [(hm(8, 25), hm(13, 25))]), True),
    "COPPER": ("coppercmdusd", "metal", "USD", (NY, [(hm(8, 10), hm(13))]), True),
    "WTI": ("lightcmdusd", "energy", "USD/bbl", (NY, [(hm(9), hm(14, 30))]), True),
    "BRENT": ("brentcmdusd", "energy", "USD/bbl", (NY, [(hm(9), hm(14, 30))]), True),
    "NATGAS": ("gascmdusd", "energy", "USD/MMBtu", (NY, [(hm(9), hm(14, 30))]), True),
    "NVDA": ("nvdaususd", "stock", "USD", US_CASH, True),
    "TSLA": ("tslaususd", "stock", "USD", US_CASH, True),
    "AAPL": ("aaplususd", "stock", "USD", US_CASH, True),
    "MSFT": ("msftususd", "stock", "USD", US_CASH, True),
    "AMZN": ("amznususd", "stock", "USD", US_CASH, True),
    "EURUSD": ("eurusd", "fx", "USD", (LON, [(hm(8), hm(17))]), False),
    "GBPUSD": ("gbpusd", "fx", "USD", (LON, [(hm(8), hm(17))]), False),
    "USDJPY": ("usdjpy", "fx", "JPY", (LON, [(hm(8), hm(17))]), False),
}
CRYPTO = ["BTC", "ETH", "SOL"]  # N3 Binance proxy, all hours count as "own session" (no home exchange)

# Round-trip commission in price units.
def commission(name, price):
    if name in ("EURUSD", "GBPUSD", "USDJPY", "XAUUSD"):
        return A.commission_price_units(name, price)   # N3 rule, ASSUMED $7 per lot round trip
    if name == "XAGUSD":
        return 7.0 / 5000                               # ASSUMED same $7/lot rule, 5,000 oz lot
    if INST[name][1] == "stock":
        return 0.04                                     # READ: $0.02 per share per side (Pepperstone, IC Markets)
    return 0.0                                          # index CFDs READ no commission; energy/copper ASSUMED spread-only

# Published broker average spreads (price units). READ 2026-11-09 unless noted in N4.
IC_AVG = {"AU200": 1.220, "DE40": 1.338, "FR40": 0.749, "JP225": 8.858, "EU50": 1.760, "UK100": 2.133, "US30": 1.411,
          "US500": 0.492, "US100": 1.807, "CN50": 6.953, "ES35": 4.426, "HK50": 8.169, "IT40": 9.000, "NL25": 0.190,
          "SA40": 15.444, "CH20": 3.500, "US2000": 0.480, "WTI": 0.034, "BRENT": 0.034, "NATGAS": 0.004}
PEP_AVG = {"US30": 2.0, "US500": 0.4, "US100": 1.0, "US2000": 0.3,         # READ, Razor, Aug 2026 data
           "DE40": 1.4, "AU200": 1.8, "XAUUSD": 0.25, "HK50": 5.0}          # SNIPPET (costs PDF / third-party for HK50)

CORR_MIN = 300
CLUSTER_T = 0.6
SESSION_MIN_RATIO = 5.0


def cash_mask(t: pd.Series, spec) -> pd.Series:
    tz, wins = spec
    loc = t.dt.tz_convert(tz)
    m = loc.dt.hour * 60 + loc.dt.minute
    ok = pd.Series(False, index=t.index)
    for a, b in wins:
        ok |= (m >= a) & (m < b)
    return ok & (loc.dt.day_of_week < 5)


def leader_clusters(C: pd.DataFrame, order: list, t: float):
    """Leader clustering, the pod's own rule ("one trade per correlated cluster, the strongest one"):
    take the strongest remaining market (order = strongest first); every remaining market whose correlation
    with it is at least t joins its cluster; repeat. NaN correlation (no shared hours) counts as not correlated."""
    left, out = list(order), []
    while left:
        lead = left.pop(0)
        grp = [lead] + [x for x in left if pd.notna(C.loc[lead, x]) and C.loc[lead, x] >= t]
        left = [x for x in left if x not in grp]
        out.append(grp)
    return out


def main():
    hourly, sess, rets, cash, info, hour_sess = {}, {}, {}, {}, {}, {}
    for name, (inst, grp, unit, spec, new) in INST.items():
        for p in ("a", "b"):
            df = A.load_duka(inst, p)
            n_all = len(df)
            df, dropped = A.keep_weekdays(df)
            b5 = A.five_minute(df)
            st = A.hourly_stats(df, b5, has_spread=True)
            st["comm"] = [commission(name, px) for px in st["price"]]
            st["cost_all"] = st["spread_med"] + st["comm"]
            st["ratio_all"] = st["r5_med"] / st["cost_all"]
            st["ratio_spread"] = st["r5_med"] / st["spread_med"]
            hourly[(name, p)] = st
            ss = A.session_stats(df, b5, has_spread=True)
            ss["cost_all"] = ss["spread_med"] + [commission(name, px) for px in ss["price"]]
            ss["ratio_all"] = ss["r5_med"] / ss["cost_all"]
            sess[(name, p)] = ss
            info[(name, p)] = {"rows": n_all, "days_kept": int(df["day"].nunique()),
                               "first": str(df["t"].min()), "last": str(df["t"].max()),
                               "holidays_dropped": [str(d) for d in dropped.index],
                               "neg_spread_min": int((df["spread"] < 0).sum())}
            if p == "a":
                act = b5[b5["active"] > 0]
                r = np.log(act["close"]).diff().where(act.index.to_series().diff() == 300_000)
                rets[name] = r
                cash[name] = cash_mask(act["t"], spec)
                lab = A.session_of(b5["t"])
                hour_sess[name] = lab.groupby(b5["t"].dt.hour).agg(lambda s: s.value_counts().index[0])
    for coin in CRYPTO:
        raw = A.load_ohlc(A.DATA / f"binance_{coin}_a.csv")
        df, _ = A.keep_weekdays(raw)
        b5 = A.five_minute(df)
        rets[coin] = np.log(b5["close"]).diff().where(b5.index.to_series().diff() == 300_000)
        cash[coin] = pd.Series(True, index=b5.index)

    # ---------------- ranking ----------------
    rows = []
    for name, (inst, grp, unit, spec, new) in INST.items():
        sa, sb = hourly[(name, "a")], hourly[(name, "b")]
        ta, tb = A.top3(sa, "ratio_all"), A.top3(sb, "ratio_all")
        r5 = sa.loc[ta, "r5_med"].mean()
        row = {"instrument": name, "new": new, "group": grp, "unit": unit, "dukascopy_id": inst,
               "best_hours_a": sorted(ta), "ratio_best_a": sa.loc[ta, "ratio_all"].mean(),
               "best_hours_b": sorted(tb), "ratio_best_b": sb.loc[tb, "ratio_all"].mean() if tb else np.nan,
               "ratio_a_hours_in_b": sb.loc[ta, "ratio_all"].mean(),
               "spearman_24h": sa["ratio_all"].rank().corr(sb["ratio_all"].rank()),
               "r5_med_best_a": r5, "r5p_med_best_a": sa.loc[ta, "r5p_med"].mean(),
               "price_a": sa["price"].median(),
               "duka_cost_best_a": sa.loc[ta, "cost_all"].mean(), "duka_spread_best_a": sa.loc[ta, "spread_med"].mean(),
               "ratio_spreadonly_best_a": sa.loc[ta, "ratio_spread"].mean(),
               "open_hours_a": int((sa["active_share"] >= A.OPEN_SHARE).sum())}
        row["ratio_ic"] = r5 / IC_AVG[name] if name in IC_AVG else np.nan
        row["ratio_pep"] = r5 / PEP_AVG[name] if name in PEP_AVG else np.nan
        if grp == "stock":
            row["ratio_broker_stock"] = r5 / (0.01 + 0.04)   # ESTIMATE 1-cent exchange spread + READ $0.04 commission
        rows.append(row)
    rank = pd.DataFrame(rows).sort_values("ratio_best_a", ascending=False)

    # ---------------- correlations ----------------
    R = pd.DataFrame(rets)
    M = pd.DataFrame(cash).reindex(R.index).fillna(False).astype(bool)
    corr_all = R.corr(min_periods=CORR_MIN)
    names = list(R.columns)
    corr_cash = pd.DataFrame(np.nan, index=names, columns=names)
    nobs_cash = pd.DataFrame(0, index=names, columns=names)
    for i in names:
        for j in names:
            m = M[i] & M[j] & R[i].notna() & R[j].notna()
            nobs_cash.loc[i, j] = int(m.sum())
            if m.sum() >= CORR_MIN:
                corr_cash.loc[i, j] = R.loc[m, i].corr(R.loc[m, j])
    def pair(a, b, mask):
        m = mask & R[a].notna() & R[b].notna()
        return {"corr": float(R.loc[m, a].corr(R.loc[m, b])) if m.sum() >= CORR_MIN else None, "n": int(m.sum())}
    allm = pd.Series(True, index=R.index)
    jp_us = {"all hours": pair("JP225", "US100", allm),
             "Tokyo cash session only (US100 CFD trading at night)": pair("JP225", "US100", M["JP225"]),
             "New York cash session only (JP225 CFD trading at night)": pair("JP225", "US100", M["US100"]),
             "both in own cash session": pair("JP225", "US100", M["JP225"] & M["US100"]),
             "neither in own cash session": pair("JP225", "US100", ~M["JP225"] & ~M["US100"])}

    # global clusters (all hours)
    order = list(rank["instrument"]) + CRYPTO
    gcl = leader_clusters(corr_cash, order, CLUSTER_T)
    gcl_all = leader_clusters(corr_all, order, CLUSTER_T)
    gmap = {}
    for k, c in enumerate(gcl):
        for x in c:
            gmap[x] = f"G{k + 1}"
    rank["cluster"] = rank["instrument"].map(gmap)

    # ---------------- separate bets per session ----------------
    lab = A.session_of(pd.Series(pd.to_datetime(R.index, unit="ms", utc=True), index=R.index))
    bets = []
    for s in A.SESSIONS:
        cand = []
        for name in INST:
            ss = sess[(name, "a")]
            if s in ss.index and pd.notna(ss.loc[s, "ratio_all"]) and ss.loc[s, "ratio_all"] >= SESSION_MIN_RATIO:
                cand.append((name, float(ss.loc[s, "ratio_all"]), float(ss.loc[s, "r5_med"])))
        cand.sort(key=lambda x: -x[1])
        cn = [c[0] for c in cand]
        if not cn:
            bets.append({"session": s, "n_candidates": 0, "n_bets": 0, "clusters": []}); continue
        Rs = R.loc[lab == s, cn]
        Cs = Rs.corr(min_periods=CORR_MIN)
        rat = {c[0]: c[1] for c in cand}
        cl = leader_clusters(Cs, cn, CLUSTER_T)
        sens = {str(tt): len(leader_clusters(Cs, cn, tt)) for tt in (0.5, 0.6, 0.7)}
        # best UTC hour inside this session for each cluster lead (hour whose blocks mostly fall in the session)
        leads = []
        for c in cl:
            lead = c[0]
            st = hourly[(lead, "a")]
            hs = [h for h in st.index if hour_sess[lead].get(h) == s and st.loc[h, "active_share"] >= A.OPEN_SHARE]
            bh = max(hs, key=lambda h: st.loc[h, "ratio_all"]) if hs else None
            leads.append({"lead": lead, "members": c, "session_ratio": rat[lead],
                          "best_hour_in_session": bh,
                          "r5_med_best_hour": float(st.loc[bh, "r5_med"]) if bh is not None else None,
                          "ratio_best_hour": float(st.loc[bh, "ratio_all"]) if bh is not None else None,
                          "within_cluster_min_corr": float(np.nanmin(Cs.loc[c, c].values)) if len(c) > 1 else None})
        bets.append({"session": s, "n_candidates": len(cn), "n_bets": len(cl), "clusters": leads, "bets_at_threshold": sens,
                     "session_corr": Cs.round(2).to_dict()})

    # ---------------- write ----------------
    rank.to_csv(OUT / "n4_ranking.csv", index=False)
    pd.concat({f"{k[0]}|{k[1]}": v for k, v in hourly.items()}).to_csv(OUT / "n4_hourly_detail.csv")
    pd.concat({f"{k[0]}|{k[1]}": v for k, v in sess.items()}).to_csv(OUT / "n4_session_detail.csv")
    corr_all.to_csv(OUT / "n4_corr_all_hours.csv")
    corr_cash.to_csv(OUT / "n4_corr_cash_sessions.csv")
    nobs_cash.to_csv(OUT / "n4_corr_cash_nobs.csv")
    fx = {k: float(hourly[(k, "a")]["price"].iloc[-1]) for k in ("EURUSD", "GBPUSD", "USDJPY")}
    last_close = {}
    for name, (inst, *_r) in INST.items():
        d = pd.read_csv(A.DATA / f"duka_{inst}_a_bid.csv").tail(1)
        last_close[name] = float(d["close"].iloc[0])
    (OUT / "n4_summary.json").write_text(json.dumps({
        "info": {f"{k[0]}|{k[1]}": v for k, v in info.items()}, "jp225_vs_us100": jp_us,
        "global_clusters": gcl, "global_clusters_all_hours": gcl_all, "bets": bets, "fx_last": fx, "last_close": last_close,
        "corr_nobs_all_min": int((R.notna().astype(int).T @ R.notna().astype(int)).values.min()),
    }, indent=1, default=str))
    pd.set_option("display.width", 250)
    print(rank[["instrument", "new", "best_hours_a", "ratio_best_a", "ratio_best_b", "ratio_a_hours_in_b", "ratio_ic",
                "ratio_pep", "r5_med_best_a", "duka_spread_best_a", "cluster"]].round(2).to_string())
    print("global cash:", gcl)
    print("global all-hours:", gcl_all)
    print(json.dumps(jp_us, indent=1))
    for b in bets:
        print(b["session"], b["n_candidates"], b["n_bets"], b.get("bets_at_threshold"), [c["members"] for c in b["clusters"]])


if __name__ == "__main__":
    main()
