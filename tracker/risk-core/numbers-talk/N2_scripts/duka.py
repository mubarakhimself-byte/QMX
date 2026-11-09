"""Parse Dukascopy bi5 tick files -> 1m mid bars, mean true range and mean spread. python -I duka.py <dir>"""
import lzma, struct, sys, os, glob, statistics as st
D = sys.argv[1]
SCALE = {"EURUSD": 1e5, "GBPUSD": 1e5, "USDJPY": 1e3, "XAUUSD": 1e3}
PIP = {"EURUSD": 1e-4, "GBPUSD": 1e-4, "USDJPY": 1e-2, "XAUUSD": 1.0}
res = {}
for f in sorted(glob.glob(os.path.join(D, "*.bi5"))):
    sym, day, hr = os.path.basename(f)[:-4].split("_")
    raw = lzma.decompress(open(f, "rb").read())
    ticks = [struct.unpack(">IIIff", raw[i:i+20]) for i in range(0, len(raw), 20)]
    sc = SCALE[sym]
    bars = {}; spreads = []
    for ms, ask, bid, av, bv in ticks:
        a, b = ask / sc, bid / sc; m = (a + b) / 2; spreads.append(a - b)
        k = ms // 60000
        if k not in bars: bars[k] = [m, m, m, m]
        else:
            r = bars[k]; r[1] = max(r[1], m); r[2] = min(r[2], m); r[3] = m
    ks = sorted(bars); trs = []
    for i, k in enumerate(ks):
        o, h, l, c = bars[k]
        if i and ks[i-1] == k - 1:
            pc = bars[ks[i-1]][3]; trs.append(max(h-l, abs(h-pc), abs(l-pc)))
        else: trs.append(h-l)
    grp = "busy 13-16 UTC" if hr != "02" else "quiet 02 UTC"
    r = res.setdefault((sym, grp), {"tr": [], "sp": [], "tr5": []})
    r["tr"] += trs; r["sp"] += spreads
    # 5m from 1m
    for j in range(0, 60, 5):
        blk = [bars[k] for k in ks if j <= k < j+5]
        if len(blk) >= 3:
            r["tr5"].append(max(x[1] for x in blk) - min(x[2] for x in blk))
for (sym, grp), r in sorted(res.items()):
    p = PIP[sym]
    print(f"{sym} {grp}: 1m TR mean {st.mean(r['tr'])/p:.2f} pips (median {st.median(r['tr'])/p:.2f}, n={len(r['tr'])}); 5m range mean {st.mean(r['tr5'])/p:.2f} pips; mean spread {st.mean(r['sp'])/p:.3f} pips, median {st.median(r['sp'])/p:.3f} (ticks {len(r['sp'])})")
