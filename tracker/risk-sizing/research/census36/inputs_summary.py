"""Summarise inputs.csv: SL/TP units, top 'other' names, defaults of common params."""
import csv, re
from collections import Counter, defaultdict
rows = list(csv.DictReader(open("inputs.csv", encoding="utf-8")))
arts = defaultdict(set)
def unit(r):
    t = (r["name"] + " " + r["comment"]).lower()
    if re.search(r"atr|volatil|mult|coef|factor|ratio|rr\b|reward", t): return "ATR/multiple/ratio"
    if re.search(r"%|percent|pct", t): return "percent"
    if re.search(r"money|\$|usd|currency|cash|deposit", t): return "money"
    if re.search(r"point|pip|tick|pts", t) or re.fullmatch(r"\d+", r["default"].strip()): return "points/pips"
    return "other"
for cat in ("stop-loss", "take-profit", "trailing", "breakeven"):
    c = Counter(); a = defaultdict(set)
    for r in rows:
        if r["category"] == cat: u = unit(r); c[u] += 1; a[u].add(r["article"])
    print(cat, {k: (v, len(a[k])) for k, v in c.most_common()})
oth = Counter(re.sub(r"^(inp|in|i|ext|g)_?", "", r["name"].lower()) for r in rows if r["category"] == "other")
print("top other names:", oth.most_common(60))
for key in ("rsi", "atr", "ma", "bands|bb", "adx"):
    vals = Counter(r["default"].strip() for r in rows if re.search(rf"({key}).*period|period.*({key})", r["name"].lower()))
    print(key, "period defaults:", vals.most_common(8))
