"""Round-trip cost vs ATR. Inputs: atr.json from analyze.py. All costs in price units of the instrument."""
import json, sys, os
A = json.load(open(os.path.join(sys.argv[1], "atr.json")))

rows = []
def add(name, ref, cost, unit_desc, point_usd_min, min_desc, margin_note):
    a = A[ref]
    rows.append((name, ref, cost, a, unit_desc, point_usd_min, min_desc, margin_note))

P = {k: A[k]["last"] for k in A}
# FX on IC cTrader raw: spread (READ avg) + commission $3 per 100k USD per side (READ)
eu = P["EURUSD"]; gu = P["GBPUSD"]; uj = P["USDJPY"]; xau = P["GOLD(GC=F)"]
add("EURUSD IC raw (avg 0.01 pip)", "EURUSD", 0.01e-4 + 6 * eu / 1e5, "price", None, "", "")
add("EURUSD IC raw, if spread 0.2 pip", "EURUSD", 0.2e-4 + 6 * eu / 1e5, "price", None, "", "")
add("GBPUSD IC raw (avg 0.04 pip)", "GBPUSD", 0.04e-4 + 6 * gu / 1e5, "price", None, "", "")
add("USDJPY IC raw (avg 0.03 pip)", "USDJPY", 0.03e-2 + 6 * uj / 1e5, "price", None, "", "")
# Gold: IC avg 0.09 (assumed $/oz), commission $3/100k USD per side on notional 100 oz*P -> per oz RT = 6*P/1e5
add("XAUUSD IC raw (0.09 + comm)", "GOLD(GC=F)", 0.09 + 6 * xau / 1e5, "price", None, "", "")
add("XAUUSD Pepperstone razor ($7 RT/lot + min spread 0.08)", "GOLD(GC=F)", 0.08 + 7 / 100, "price", None, "", "")
# Index CFDs: IC avg spread (ic.com page), no commission
add("US500 IC", "ES", 0.492, "price", None, "", "")
add("USTEC IC", "NQ", 1.807, "price", None, "", "")
add("DE40 IC", "DAX", 1.338, "price", None, "", "")
# Micros: NinjaTrader Free $0.39/side + exchange fee + NFA $0.01/side ; spread = 1 tick (lower bound)
def micro(name, ref, mult, tick, exch):
    fees = 2 * (0.39 + exch + 0.01)
    cost_usd = fees + tick * mult
    add(f"{name} (fees ${fees:.2f} + 1 tick ${tick*mult:.2f})", ref, cost_usd / mult, "price", mult, "", "")
micro("MES", "ES", 5, 0.25, 0.35)
micro("MNQ", "NQ", 2, 0.25, 0.35)
micro("MGC", "GOLD(GC=F)", 10, 0.10, 1.10)
micro("MCL", "CL", 100, 0.01, 0.50)
# Hyperliquid base tier: taker 0.045%, maker 0.015% per side; spread snapshot bps
spr = {"HL-BTC": 0.135e-4, "HL-ETH": 0.474e-4, "HL-SOL": 0.116e-4}
for c in ["HL-BTC", "HL-ETH", "HL-SOL"]:
    p = P[c]
    add(f"{c} taker+taker (0.09% + spread)", c, p * (0.0009 + spr[c]), "price", None, "", "")
    add(f"{c} maker+maker (0.03%)", c, p * 0.0003, "price", None, "", "")

print("instrument | last | RT cost (price units) | 1m TR busy | 1m TR all-hours median | cost/1m busy | cost/1m quiet(median) | 5m TR busy (same 5 days) | cost/5m busy | 5m TR 60d/17d mean | cost/5m 60d")
for name, ref, cost, a, *_ in rows:
    print(f"{name} | {a['last']:.6g} | {cost:.6g} | {a['m1w']:.4g} | {a['m1med']:.4g} | {cost/a['m1w']:.0%} | {cost/a['m1med']:.0%} | {a['m5samew']:.4g} | {cost/a['m5samew']:.0%} | {a['m5']:.4g} | {cost/a['m5']:.0%}")
