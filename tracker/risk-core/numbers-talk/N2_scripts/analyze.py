"""N2 scalping instruments: compute 1m/5m true-range (ATR proxy), correlations, HL book spread.
Pure stdlib. Usage: python -I analyze.py <datadir>"""
import json, sys, math, statistics as st, os
from datetime import datetime, timezone

D = sys.argv[1]

def yahoo(path):
    j = json.load(open(os.path.join(D, path)))
    r = j["chart"]["result"][0]
    ts = r["timestamp"]; q = r["indicators"]["quote"][0]
    out = []
    for i, t in enumerate(ts):
        o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
        if None in (o, h, l, c):
            continue
        out.append((t, o, h, l, c))
    return out

def hl(path):
    j = json.load(open(os.path.join(D, path)))
    return [(int(x["t"]) // 1000, float(x["o"]), float(x["h"]), float(x["l"]), float(x["c"])) for x in j]

def utc_minutes(t):
    d = datetime.fromtimestamp(t, timezone.utc)
    return d.hour * 60 + d.minute, d.weekday()

def tr_stats(bars, step, window=None):
    trs = []
    prev = None
    for b in bars:
        t, o, h, l, c = b
        if window:
            m, wd = utc_minutes(t)
            if not (window[0] <= m < window[1]) or wd >= 5:
                prev = b; continue
        if prev and t - prev[0] == step:
            pc = prev[4]
            tr = max(h - l, abs(h - pc), abs(l - pc))
        else:
            tr = h - l
        if tr > 0:
            trs.append(tr)
        prev = b
    if not trs:
        return None
    return {"n": len(trs), "mean": st.mean(trs), "median": st.median(trs)}

def rets(bars, step):
    d = {}
    for a, b in zip(bars, bars[1:]):
        if b[0] - a[0] == step and a[4] > 0 and b[4] > 0:
            d[b[0]] = math.log(b[4] / a[4])
    return d

def corr(x, y):
    keys = [k for k in x if k in y]
    if len(keys) < 30:
        return None, len(keys)
    a = [x[k] for k in keys]; b = [y[k] for k in keys]
    ma, mb = st.mean(a), st.mean(b)
    sa = math.sqrt(sum((v - ma) ** 2 for v in a)); sb = math.sqrt(sum((v - mb) ** 2 for v in b))
    if sa == 0 or sb == 0:
        return None, len(keys)
    return sum((u - ma) * (v - mb) for u, v in zip(a, b)) / (sa * sb), len(keys)

def per_day_corr(x, y):
    days = {}
    for k in x:
        if k in y:
            dd = datetime.fromtimestamp(k, timezone.utc).date()
            days.setdefault(dd, []).append(k)
    res = []
    for dd, ks in sorted(days.items()):
        if len(ks) < 50:
            continue
        a = {k: x[k] for k in ks}; b = {k: y[k] for k in ks}
        c, n = corr(a, b)
        vol = math.sqrt(sum(v * v for v in a.values()))
        if c is not None:
            res.append((dd, c, vol, n))
    return res

def daily_rets(bars):
    d = {}
    for a, b in zip(bars, bars[1:]):
        if a[4] > 0 and b[4] > 0:
            d[datetime.fromtimestamp(b[0], timezone.utc).date()] = math.log(b[4] / a[4])
    return d

def window_corr(x, y, start, end):
    from datetime import date
    s, e = date.fromisoformat(start), date.fromisoformat(end)
    xs = {k: v for k, v in x.items() if s <= k <= e}
    keys = [k for k in xs if k in y]
    if len(keys) < 15:
        return None, len(keys)
    a = [xs[k] for k in keys]; b = [y[k] for k in keys]
    ma, mb = st.mean(a), st.mean(b)
    sa = math.sqrt(sum((v - ma) ** 2 for v in a)); sb = math.sqrt(sum((v - mb) ** 2 for v in b))
    return sum((u - ma) * (v - mb) for u, v in zip(a, b)) / (sa * sb), len(keys)

def resample5(bars):
    g = {}
    for t, o, h, l, c in bars:
        k = t - t % 300
        if k not in g:
            g[k] = [k, o, h, l, c, 1]
        else:
            r = g[k]; r[2] = max(r[2], h); r[3] = min(r[3], l); r[4] = c; r[5] += 1
    return [tuple(r[:5]) for k, r in sorted(g.items()) if r[5] >= 3]

# ---------------- instruments ----------------
Y = {"EURUSD": "EURUSDX", "GBPUSD": "GBPUSDX", "USDJPY": "JPYX", "GOLD(GC=F)": "GCF",
     "ES": "ESF", "NQ": "NQF", "YM": "YMF", "DAX": "5EGDAXI", "CL": "CLF"}
WIN = {"EURUSD": (720, 1020), "GBPUSD": (720, 1020), "USDJPY": (720, 1020), "GOLD(GC=F)": (720, 1020),
       "CL": (780, 1110), "ES": (810, 1200), "NQ": (810, 1200), "YM": (810, 1200), "DAX": (480, 990)}
bars1, bars5, barsD = {}, {}, {}
for k, f in Y.items():
    bars1[k] = yahoo(f + ".json"); bars5[k] = yahoo("m5_" + f + ".json"); barsD[k] = yahoo("d_" + f + ".json")
for c in ["BTC", "ETH", "SOL"]:
    bars1["HL-" + c] = hl("hl_" + c + ".json"); bars5["HL-" + c] = hl("hl5_" + c + ".json")
    barsD["Y-" + c] = yahoo("d_" + c + "USD.json")
    WIN["HL-" + c] = None

print("== ATR proxy (true range) ==")
print("inst | last | 1m n | 1m mean | 1m median | 1m busy mean | 5m mean | 5m median | 5m busy mean | 1m span | 5m span")
atr = {}
for k in bars1:
    b1, b5 = bars1[k], bars5[k]
    s1 = tr_stats(b1, 60); s5 = tr_stats(b5, 300)
    w = WIN.get(k)
    s1w = tr_stats(b1, 60, w) if w else s1
    s5w = tr_stats(b5, 300, w) if w else s5
    span1 = f"{datetime.fromtimestamp(b1[0][0], timezone.utc):%Y-%m-%d %H:%M}..{datetime.fromtimestamp(b1[-1][0], timezone.utc):%Y-%m-%d %H:%M}"
    r5 = resample5(b1); s5s = tr_stats(r5, 300); s5sw = tr_stats(r5, 300, w) if w else s5s
    span5 = f"{datetime.fromtimestamp(b5[0][0], timezone.utc):%Y-%m-%d}..{datetime.fromtimestamp(b5[-1][0], timezone.utc):%Y-%m-%d}"
    atr[k] = dict(last=b1[-1][4], m1=s1["mean"], m1med=s1["median"], m1w=s1w["mean"], m5=s5["mean"], m5med=s5["median"], m5w=s5w["mean"], m5same=s5s["mean"], m5samew=s5sw["mean"])
    print(f"{k} | {b1[-1][4]:.5g} | {s1['n']} | {s1['mean']:.5g} | {s1['median']:.5g} | {s1w['mean']:.5g} | {s5['mean']:.5g} | {s5['median']:.5g} | {s5w['mean']:.5g} | same-window 5m mean {s5s['mean']:.5g} busy {s5sw['mean']:.5g} | {span1} | {span5}")

print("\n== correlations of log returns ==")
pairs = [("ES", "NQ"), ("ES", "YM"), ("NQ", "YM"), ("ES", "DAX"), ("EURUSD", "GBPUSD"), ("EURUSD", "USDJPY"),
         ("GBPUSD", "USDJPY"), ("GOLD(GC=F)", "EURUSD"), ("GOLD(GC=F)", "ES"), ("HL-BTC", "HL-ETH"), ("HL-BTC", "HL-SOL"), ("HL-ETH", "HL-SOL"), ("HL-BTC", "NQ")]
for a, b in pairs:
    c1, n1 = corr(rets(bars1[a], 60), rets(bars1[b], 60))
    r5a, r5b = rets(bars5[a], 300), rets(bars5[b], 300)
    c5, n5 = corr(r5a, r5b)
    pdc = per_day_corr(r5a, r5b)
    if pdc:
        cs = [x[1] for x in pdc]
        hv = max(pdc, key=lambda x: x[2])
        extra = f"per-day 5m corr min {min(cs):.2f} med {st.median(cs):.2f} max {max(cs):.2f} over {len(cs)} days; most volatile day {hv[0]} corr {hv[1]:.2f}"
    else:
        extra = ""
    f = lambda v: "n/a" if v is None else f"{v:.2f}"
    print(f"{a}~{b} | 1m {f(c1)} (n={n1}) | 5m {f(c5)} (n={n5}) | {extra}")

print("\n== daily return correlations, calm vs stress windows ==")
dr = {k: daily_rets(v) for k, v in barsD.items()}
wins = [("2024 calm year", "2024-01-01", "2024-12-31"), ("COVID crash", "2020-02-20", "2020-04-30"),
        ("Apr-2025 tariff shock", "2025-04-01", "2025-04-30"), ("2022 crypto bear (May-Jun)", "2022-05-01", "2022-06-30"),
        ("Oct-2025 crypto liquidation", "2025-10-01", "2025-10-31")]
dpairs = [("ES", "NQ"), ("ES", "YM"), ("NQ", "YM"), ("ES", "DAX"), ("EURUSD", "GBPUSD"), ("EURUSD", "USDJPY"),
          ("Y-BTC", "Y-ETH"), ("Y-BTC", "Y-SOL"), ("Y-ETH", "Y-SOL")]
for a, b in dpairs:
    row = []
    for name, s, e in wins:
        c, n = window_corr(dr[a], dr[b], s, e)
        row.append(f"{name}: {'n/a' if c is None else f'{c:.2f}'} (n={n})")
    print(f"{a}~{b} | " + " | ".join(row))

print("\n== Hyperliquid book snapshot and meta ==")
meta = json.load(open(os.path.join(D, "hl_meta.json")))
uni = meta[0]["universe"]; ctx = meta[1]
for c in ["BTC", "ETH", "SOL"]:
    bk = json.load(open(os.path.join(D, f"hl_book_{c}.json")))
    bid = float(bk["levels"][0][0]["px"]); ask = float(bk["levels"][1][0]["px"])
    mid = (bid + ask) / 2
    depth_b = sum(float(x["sz"]) for x in bk["levels"][0]) * mid
    depth_a = sum(float(x["sz"]) for x in bk["levels"][1]) * mid
    i = next(i for i, u in enumerate(uni) if u["name"] == c)
    tr = json.load(open(os.path.join(D, f"hl_trades_{c}.json")))
    sides = sorted(set(t["side"] for t in tr))
    print(f"{c} | bid {bid} ask {ask} spread {ask-bid:.4g} = {(ask-bid)/mid*1e4:.3f} bps | levels {len(bk['levels'][0])}/{len(bk['levels'][1])} | depth $ bid {depth_b:,.0f} ask {depth_a:,.0f} | maxLeverage {uni[i].get('maxLeverage')} szDecimals {uni[i]['szDecimals']} | markPx {ctx[i]['markPx']} | dayNtlVlm {float(ctx[i]['dayNtlVlm']):,.0f} | trade sides seen {sides} | book time {datetime.fromtimestamp(bk['time']/1000, timezone.utc):%Y-%m-%d %H:%M:%S}")

json.dump(atr, open(os.path.join(D, "atr.json"), "w"), indent=1)
