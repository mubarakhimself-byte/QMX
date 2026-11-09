"""Build the markdown tables for N4 from results/n4_*.  Run: python -I build_n4_tables.py -> results/n4_tables.md"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
rank = pd.read_csv(OUT / "n4_ranking.csv")
S = json.loads((OUT / "n4_summary.json").read_text())
ca = pd.read_csv(OUT / "n4_corr_all_hours.csv", index_col=0)
cc = pd.read_csv(OUT / "n4_corr_cash_sessions.csv", index_col=0)
sess = pd.read_csv(OUT / "n4_session_detail.csv", index_col=[0, 1])
n3 = pd.read_csv(OUT / "ranking.csv")  # N3 crypto rows (taker ratio, Hyperliquid-scaled in N3 text)

fx = S["last_close"]  # READ: last Dukascopy bid close of period a (2026-11-08)
# READ: Dukascopy bid close 2026-11-06 21:59 UTC (duka_*_fx_bid.csv); HKD = peg band midpoint ESTIMATE
USD = {"USD": 1.0, "EUR": fx["EURUSD"], "GBP": fx["GBPUSD"], "JPY": 1 / fx["USDJPY"], "CHF": 1 / 0.81993,
       "AUD": 0.68616, "HKD": 1 / 7.8, "SGD": 1 / 1.28117, "CAD": 1 / 1.41273}

# Smallest futures contract at IBKR per measured instrument.
# (contract, ccy, point value, tick pts, IBKR intraday initial margin READ 2026-11-09, data fee non-pro READ, label of point/tick)
FUT = {
    "US100": ("CME E-nano Nasdaq-100 NNQ", "USD", 0.20, 0.50, 417.12, "CME L2 $12.10/mo", "READ"),
    "US500": ("CME E-nano S&P 500 NES", "USD", 0.50, 0.50, 233.16, "CME L2 $12.10/mo", "READ"),
    "US30": ("CBOT E-nano Dow NDOW", "USD", 0.05, 2.0, 123.01, "CBOT L2 $12.10/mo", "READ"),
    "US2000": ("CME E-nano Russell 2000 N2K", "USD", 0.50, 0.20, 89.96, "CME L2 $12.10/mo", "READ"),
    "DE40": ("Eurex Micro-DAX FDXS", "EUR", 1.0, 1.0, 1570.99, "Eurex Core L2 EUR 13.00/mo", "READ"),
    "EU50": ("Eurex Micro Euro Stoxx 50 FSXE", "EUR", 1.0, 0.5, 382.07, "Eurex Core L2 EUR 13.00/mo", "READ"),
    "CH20": ("Eurex Micro SMI FSMS", "CHF", 1.0, 1.0, 747.45, "Eurex Core L2 EUR 13.00/mo", "READ"),
    "FR40": ("Euronext Mini CAC 40 MFC", "EUR", 1.0, 0.5, 478.79, "Euronext retail deriv. L2 EUR 1.00/mo (coverage unclear)", "READ"),
    "NL25": ("Euronext Mini AEX MFA", "EUR", 20.0, 0.05, 1152.74, "Euronext retail deriv. L2 EUR 1.00/mo (coverage unclear)", "ESTIMATE"),
    "IT40": ("IDEM Micro FTSE MIB MICR", "EUR", 0.2, 5.0, 749.85, "not listed for IDEM on IBKR page", "ESTIMATE"),
    "ES35": ("MEFF Mini IBEX 35 MIX", "EUR", 1.0, 1.0, 1207.50, "MEFF L2 EUR 6.00/mo", "ESTIMATE"),
    "UK100": ("ICE FTSE 100 Z (no smaller)", "GBP", 10.0, 0.5, 5333.63, "ICE EU Financials L1+L2 $132/mo", "ESTIMATE"),
    "JP225": ("OSE Nikkei 225 Micro (225MC)", "JPY", 10.0, 5.0, 59883.06, "OSE L2 JPY 400/mo", "SNIPPET"),
    "HK50": ("HKEX Mini Hang Seng MHI", "HKD", 10.0, 1.0, 18670.40, "HKFE L2 HKD 100/mo (L1 free)", "ESTIMATE"),
    "CN50": ("SGX FTSE China A50 CN", "USD", 1.0, 1.0, 1231.84, "SGX deriv. L1 SGD 2/mo (no L2 row)", "READ"),
    "AU200": ("ASX SPI 200 AP (mini not at IBKR)", "AUD", 25.0, 1.0, 12673.17, "ASX24 L1+L2 AUD 21.50/mo", "READ"),
    "XAUUSD": ("COMEX 1-Ounce Gold 1OZ", "USD", 1.0, None, 434.09, "COMEX L2 $12.10/mo", "ESTIMATE"),
    "XAGUSD": ("COMEX 100-oz Silver SIC", "USD", 100.0, None, 1147.18, "COMEX L2 $12.10/mo", "ESTIMATE"),
    "WTI": ("NYMEX Micro WTI MCL", "USD", 100.0, 0.01, 1940.27, "NYMEX L2 $12.10/mo", "ESTIMATE"),
    "NATGAS": ("NYMEX Micro Henry Hub MNG", "USD", 1000.0, 0.001, 588.72, "NYMEX L2 $12.10/mo", "ESTIMATE"),
    "COPPER": ("COMEX Micro Copper MHG", "USD", 2500.0, 0.0005, 2339.06, "COMEX L2 $12.10/mo", "ESTIMATE"),
}

def f(x, d=1):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    return f"{x:,.{d}f}"

L = []
# ---------- ranking ----------
L.append("| # | Instrument | New in N4 | Best 3 UTC hours (a) | Median 5m range there | Dukascopy cost | Ratio (a), Dukascopy | Ratio (b) | Period-a hours in b | Ratio at IC Markets avg spread | Ratio at Pepperstone avg spread | Cluster |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
for i, r in enumerate(rank.itertuples(), 1):
    hrs = ", ".join(f"{int(h):02d}" for h in json.loads(r.best_hours_a))
    rb = r.ratio_best_b
    pep = r.ratio_pep
    extra = f" (broker est. {r.ratio_broker_stock:.1f})" if r.group == "stock" and not np.isnan(r.ratio_broker_stock) else ""
    L.append(f"| {i} | {r.instrument} | {'yes' if r.new else ''} | {hrs} | {r.r5_med_best_a:,.4g} {r.unit} ({r.r5p_med_best_a:.3f}%) | {r.duka_cost_best_a:,.3g} | **{r.ratio_best_a:.1f}** | {f(rb)} | {f(r.ratio_a_hours_in_b)} | {f(r.ratio_ic)}{extra} | {f(pep)} | {r.cluster} |")
L.append("")
L.append("Crypto is not re-measured here. N3 (Hyperliquid taker cost): SOL 3.3, ETH 2.9, BTC 2.4; with maker orders 7 to 10.")
L.append("")
# ---------- clusters ----------
L.append("Global clusters (leader rule on the both-in-cash-session correlation, threshold 0.6; strongest market by ratio leads):")
gm = dict(zip(rank.instrument, rank.cluster))
groups = {}
for name, g in gm.items():
    groups.setdefault(g, []).append(name)
for c in S["global_clusters"]:
    lab = gm.get(c[0], "crypto" if c[0] in ("BTC", "ETH", "SOL") else "?")
    L.append(f"- {lab}: {', '.join(c)}")
L.append("")
# ---------- separate bets ----------
L.append("| Session | Instruments at ratio >= 5 | Separate bets | The bets (strongest member first, session ratio) |")
L.append("|---|---|---|---|")
for b in S["bets"]:
    desc = "; ".join("[" + ", ".join(c["members"]) + f"] lead {c['lead']} {c['session_ratio']:.1f}" for c in b["clusters"])
    L.append(f"| {b['session']} | {b['n_candidates']} | **{b['n_bets']}** | {desc} |")
L.append("")
# ---------- futures fit ----------
L.append("| Session | Bet (lead) | Best UTC hour in session | Median 5m range then | Smallest future at IBKR | Value per point | Value per tick | $ risk for a one-median-5m stop | IBKR intraday initial margin (USD) | Order-flow data, non-pro, per month |")
L.append("|---|---|---|---|---|---|---|---|---|---|")
for b in S["bets"]:
    for c in b["clusters"]:
        lead = c["lead"]
        bh = c["best_hour_in_session"]
        r5 = c["r5_med_best_hour"]
        if lead not in FUT:
            L.append(f"| {b['session']} | {lead} | {bh} | {f(r5, 3)} | no IBKR future (CFD only) | - | - | - | - | - |")
            continue
        name, ccy, pv, tick, mg, data, lab = FUT[lead]
        usd = USD[ccy]
        risk = r5 * pv * usd if r5 is not None else None
        tv = f"{ccy} {tick * pv:,.2f}" if tick else "not read"
        L.append(f"| {b['session']} | {lead} | {int(bh):02d} | {f(r5, 3)} | {name} | {ccy} {pv:g} ({lab}) | {tv} | **${f(risk, 0)}** | ${f(mg * usd, 0)} | {data} |")
L.append("")
# ---------- JP vs US ----------
L.append("| Japan 225 vs US tech 100, 5m returns, period a | Correlation | 5m blocks |")
L.append("|---|---|---|")
for k, v in S["jp225_vs_us100"].items():
    L.append(f"| {k} | {f(v['corr'], 2) if v['corr'] is not None else 'n/a'} | {v['n']:,} |")
L.append("")
# ---------- correlation matrices ----------
def mat(C, cols, title):
    L.append(title)
    L.append("")
    L.append("| | " + " | ".join(cols) + " |")
    L.append("|---" * (len(cols) + 1) + "|")
    for a in cols:
        L.append(f"| {a} | " + " | ".join("" if a == b else ("n/a" if pd.isna(C.loc[a, b]) else f"{C.loc[a, b]:.2f}") for b in cols) + " |")
    L.append("")
idx = ["US100", "US500", "US30", "US2000", "DE40", "EU50", "FR40", "NL25", "IT40", "ES35", "CH20", "UK100", "PL20", "SA40", "JP225", "HK50", "CN50", "SG", "AU200"]
oth = ["XAUUSD", "XAGUSD", "COPPER", "WTI", "BRENT", "NATGAS", "NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "EURUSD", "GBPUSD", "USDJPY", "BTC", "ETH", "SOL"]
mat(ca, idx, "**Indices, all hours (period a):**")
mat(cc, idx, "**Indices, only 5m blocks where BOTH markets are inside their own cash session:** (n/a = the two cash sessions never overlap, or fewer than 300 shared blocks)")
L.append("**Commodities, stocks, FX and crypto against the main indices, all hours / both-in-cash-session:**")
L.append("")
key = ["US100", "US500", "DE40", "JP225", "XAUUSD", "WTI"]
L.append("| | " + " | ".join(key) + " |")
L.append("|---" * (len(key) + 1) + "|")
for a in oth:
    cells = []
    for b in key:
        if a == b:
            cells.append("")
            continue
        x, y = ca.loc[a, b], cc.loc[a, b]
        cells.append(f"{x:.2f} / {'n/a' if pd.isna(y) else f'{y:.2f}'}")
    L.append(f"| {a} | " + " | ".join(cells) + " |")
L.append("")
L.append("Pairs at or above 0.6 (all hours | both-in-cash):")
seen = set()
pairs = []
for a in ca.index:
    for b in ca.columns:
        if a < b and ca.loc[a, b] >= 0.6:
            pairs.append((ca.loc[a, b], a, b))
for v, a, b in sorted(pairs, reverse=True):
    y = cc.loc[a, b]
    L.append(f"- {a} / {b}: {v:.2f} | {'n/a' if pd.isna(y) else f'{y:.2f}'}")
L.append("")
(OUT / "n4_tables.md").write_text("\n".join(L), encoding="utf-8")
print("\n".join(L))
