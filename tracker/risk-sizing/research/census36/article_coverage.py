"""Per-article coverage: share of an article's distinct concepts that the dictionary covers (covered or renamed)."""
import json, sys, pathlib, statistics
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from concepts import C
from collections import Counter
st = {x["id"]: x["status"] for x in C}; fam = {x["id"]: x["family"] for x in C}
art = json.load(open("articles.json"))
def report(name, ids, skip_stats=False):
    shares, any_missing, tot = [], 0, Counter()
    for a in ids:
        h = [k for k in art[a]["hits"] if not (skip_stats and fam[k] == "stats-and-models")]
        if not h: continue
        s = [st[k] for k in h]; tot.update(s)
        shares.append(sum(x in ("covered", "renamed") for x in s) / len(s)); any_missing += any(x == "missing" for x in s)
    n = len(shares); T = sum(tot.values())
    print(f"{name}: n={n} median share covered={statistics.median(shares):.2f} mean={statistics.mean(shares):.2f} with>=1 missing={100*any_missing/n:.0f}% | pooled distinct-concept hits: " + " ".join(f"{k}={100*v/T:.0f}%" for k, v in tot.most_common()))
inc = [a for a, v in art.items() if v["include"]]
report("all included", inc); report("all included, stats family excluded", inc, True)
ent = {"crossover entry", "threshold / overbought-oversold", "breakout", "pullback / retracement", "retest", "ma-crossover", "grid entry", "forecast-direction entry", "engulfing", "pin-bar / hammer / shooting-star", "divergence", "order-block", "fair-value-gap", "liquidity-sweep / stop-hunt"}
strat = [a for a in inc if ent & set(art[a]["hits"]) and ({"stop-loss (generic)", "take-profit (generic)"} & set(art[a]["hits"]))]
report("strategy-bearing", strat); report("strategy-bearing, stats excluded", strat, True)
