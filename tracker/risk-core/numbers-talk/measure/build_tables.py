"""Turn results/*.csv|json into the markdown tables used in N3-which-markets-move.md.

Run after analyze.py and sanity.py:  python -I build_tables.py  -> results/tables.md
"""
import ast
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
CRYPTO = ["BTC", "ETH", "SOL"]
DEC = {"EURUSD": 5, "GBPUSD": 5, "USDJPY": 3, "XAUUSD": 2, "US500": 2, "US100": 1, "DE40": 1, "BTC": 0, "ETH": 2, "SOL": 3,
       "JP225": 0, "HK50": 0, "AU200": 1, "UK100": 1, "EU50": 1}
UNIT = {"EURUSD": "USD", "GBPUSD": "USD", "USDJPY": "JPY", "XAUUSD": "USD/oz", "US500": "pts", "US100": "pts", "DE40": "pts",
        "BTC": "USD", "ETH": "USD", "SOL": "USD", "JP225": "pts", "HK50": "pts", "AU200": "pts", "UK100": "pts", "EU50": "pts"}

rank = pd.read_csv(RES / "ranking.csv")
for c in ("best_hours_a", "best_hours_b"):
    rank[c] = rank[c].apply(ast.literal_eval)
detail = pd.read_csv(RES / "hourly_detail.csv")
detail.columns = ["key", "hour"] + list(detail.columns[2:])
sanity = json.loads((RES / "sanity.json").read_text())
corr = pd.read_csv(RES / "corr_5m_returns_a.csv", index_col=0)

# Hyperliquid-adjusted crypto ratio: Binance 5m ranges run a little wider than Hyperliquid's own
# (measured over the ~17-day overlap in sanity.py), so scale the proxy ratio by HL/Binance.
adj = {c: sanity["hyperliquid_vs_binance"][c]["median_5m_range_pct_hl"] / sanity["hyperliquid_vs_binance"][c]["median_5m_range_pct_binance"] for c in CRYPTO}
rank["ratio_used_a"] = [r.ratio_best_a * adj.get(r.instrument, 1.0) for r in rank.itertuples()]
rank["ratio_used_b"] = [r.ratio_best_b * adj.get(r.instrument, 1.0) for r in rank.itertuples()]
rank["ratio_used_ab"] = [r.ratio_a_hours_in_b * adj.get(r.instrument, 1.0) for r in rank.itertuples()]
rank = rank.sort_values("ratio_used_a", ascending=False).reset_index(drop=True)


def f(x, d):
    return "n/a" if pd.isna(x) else f"{x:,.{d}f}"


hrs = lambda h: ", ".join(f"{x:02d}" for x in sorted(h))
lines = ["## Ranking (period a = last 90 days; best 3 UTC hours by all-in ratio)", "",
         "| # | Instrument | Best 3 UTC hours (a) | Median 5m range there | All-in round-trip cost | Ratio (a) | Ratio, cheaper case | Best 3 UTC hours (b) | Ratio (b) | Period-a hours, ratio in b | Spearman 24h a vs b |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
for i, r in rank.iterrows():
    n, d = r.instrument, DEC[r.instrument]
    if n in CRYPTO:
        price = r.r5_med_best_a / (r.r5p_med_best_a / 100)
        cost = f"{r.costp_best_a:.4f}% (≈{f(r.costp_best_a / 100 * price, d)} {UNIT[n]}) taker"
        cheap = f"{r.ratio_maker_best_a * adj[n]:.1f} (maker)"
    else:
        cost = f"{f(r.cost_best_a, d)} {UNIT[n]} ({r.costp_best_a:.4f}%)"
        cheap = f"{r.ratio_spreadonly_best_a:.1f} (spread only)" if r.cost_best_a and abs(r.ratio_spreadonly_best_a - r.ratio_best_a) > 1e-9 else "same (no commission assumed)"
    lines.append(f"| {i + 1} | {n} | {hrs(r.best_hours_a)} | {f(r.r5_med_best_a, d)} {UNIT[n]} ({r.r5p_med_best_a:.3f}%) | {cost} | **{r.ratio_used_a:.1f}** | {cheap} | {hrs(r.best_hours_b)} | {r.ratio_used_b:.1f} | {r.ratio_used_ab:.1f} | {r.spearman_24h:.2f} |")
lines += ["", f"Crypto ratios are scaled by the Hyperliquid/Binance 5m-range factor: " + ", ".join(f"{c} {adj[c]:.3f}" for c in CRYPTO) + ".", ""]

# Per-hour detail
lines += ["## Per-hour detail", ""]
for key, g in detail.groupby("key", sort=False):
    n, p = key.split("|")
    d = DEC[n]
    g = g.set_index("hour")
    crypto = n in CRYPTO
    lines += [f"### {n}, period {p} ({UNIT[n]})", ""]
    if crypto:
        lines += ["| UTC hr | 1m med | 1m p75 | 1m med % | 5m med | 5m p75 | 5m med % | 5m p75 % | ratio taker (proxy, unscaled) | ratio maker |", "|---|---|---|---|---|---|---|---|---|---|"]
        for h, r in g.iterrows():
            lines.append(f"| {h:02d} | {f(r.r1_med, d)} | {f(r.r1_p75, d)} | {r.r1p_med:.4f} | {f(r.r5_med, d)} | {f(r.r5_p75, d)} | {r.r5p_med:.4f} | {r.r5p_p75:.4f} | {r.ratio_all:.1f} | {r.ratio_maker:.1f} |")
    else:
        lines += ["| UTC hr | ticked min % | 1m med | 1m p75 | 1m med % | 5m med | 5m p75 | 5m med % | 5m p75 % | spread med | spread % | ratio all-in | ratio spread only |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for h, r in g.iterrows():
            flag = "" if r.active_share >= 0.8 else " (closed/thin)"
            lines.append(f"| {h:02d}{flag} | {r.active_share * 100:.0f} | {f(r.r1_med, d)} | {f(r.r1_p75, d)} | {r.r1p_med:.4f} | {f(r.r5_med, d)} | {f(r.r5_p75, d)} | {r.r5p_med:.4f} | {r.r5p_p75:.4f} | {f(r.spread_med, d + 1)} | {f(r.spreadp_med, 4)} | {f(r.ratio_all, 1)} | {f(r.ratio_spread, 1)} |")
    lines.append("")

# Sessions: which instruments have the best ratio in each world session
sess = pd.read_csv(RES / "session_detail.csv")
sess.columns = ["key", "sess"] + list(sess.columns[2:])
sess["instrument"] = sess["key"].str.split("|").str[0]
sess["period"] = sess["key"].str.split("|").str[1]
sess["ratio_used"] = [r.ratio_all * adj.get(r.instrument, 1.0) for r in sess.itertuples()]
sess = sess[sess["active_share"] >= 0.5]  # instrument must be open for at least half the session
lines += ["## Best move-to-cost ratio per world session", "",
          "| Session | Top 3, period a (ratio) | Top 3, period b (ratio) | Crypto best, period a | FX/gold best, period a |", "|---|---|---|---|---|"]
session_order = list(dict.fromkeys(pd.read_csv(RES / "session_detail.csv").iloc[:, 1]))
for s in session_order:
    cells = []
    for p in ("a", "b"):
        g = sess[(sess["sess"] == s) & (sess["period"] == p)].sort_values("ratio_used", ascending=False)
        cells.append(", ".join(f"{r.instrument} {r.ratio_used:.1f}" for r in g.head(3).itertuples()))
    ga = sess[(sess["sess"] == s) & (sess["period"] == "a")]
    cr = ga[ga["instrument"].isin(CRYPTO)].sort_values("ratio_used", ascending=False).head(1)
    fx = ga[ga["instrument"].isin(["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"])].sort_values("ratio_used", ascending=False).head(1)
    cells.append(", ".join(f"{r.instrument} {r.ratio_used:.1f}" for r in cr.itertuples()))
    cells.append(", ".join(f"{r.instrument} {r.ratio_used:.1f}" for r in fx.itertuples()))
    lines.append(f"| {s} | " + " | ".join(cells) + " |")
lines += ["", "Full session table (all instruments, both periods): measure/results/session_detail.csv.", ""]

lines += ["## Correlation of 5-minute returns, period a", "", "| | " + " | ".join(corr.columns) + " |", "|---" * (len(corr.columns) + 1) + "|"]
for idx, row in corr.iterrows():
    lines.append(f"| {idx} | " + " | ".join(f"{v:.2f}" for v in row) + " |")
(RES / "tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines[:20]))
