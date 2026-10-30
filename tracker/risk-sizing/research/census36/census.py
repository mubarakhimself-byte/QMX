"""Vocabulary census over the screened MQL5 articles.
Run: python -I census.py  (from this folder; reads screen.json, dict_entries.json, concepts.py)
Writes: articles.json (per-article concept hits), concept_counts.csv, family_summary.txt,
mql_calls.csv, inputs.csv, discovery.csv."""
import json, re, csv, sys, pathlib
from collections import Counter, defaultdict
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from concepts import C

LIB = pathlib.Path("C:/Users/Mubarak/Desktop/QMX/.worktrees/mql5-library/data/mql5-library")
screen = json.load(open("screen.json"))
dict_entries = json.load(open("dict_entries.json"))
dict_text = " | ".join((e["slug"] + " " + e["title"] + " " + " ".join(e["aliases"])).lower() for e in dict_entries)
slugs = {e["slug"] for e in dict_entries}

FENCE = re.compile(r"```.*?```", re.S)
def split(md):
    md = md.split("\n---\n", 1)[1] if md.startswith("---") else md
    md = re.split(r"\*\*Attached files\*\*", md)[0]
    code = "\n".join(FENCE.findall(md))
    prose = FENCE.sub(" ", md)
    prose = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", prose)
    prose = re.sub(r"\]\([^)]*\)", "]", prose)
    return prose.lower(), code

RX = [(x, re.compile(x["rx"], re.I)) for x in C]
CALLS = re.compile(r"\b(iMA|iRSI|iCCI|iSAR|iADX|iADXWilder|iBands|iStochastic|iMACD|iATR|iMomentum|iDeMarker|iWPR|iAO|iAC|iAlligator|iFractals|iEnvelopes|iIchimoku|iMFI|iBWMFI|iOBV|iAD|iChaikin|iForce|iBearsPower|iBullsPower|iRVI|iStdDev|iTEMA|iDEMA|iAMA|iFrAMA|iVIDyA|iTriX|iOsMA|iGator|iVolumes|iCustom)\s*\(")
INPUT = re.compile(r"^\s*s?input\s+(?:group\s+)?[\w:]+\s+(\w+)\s*=\s*([^;]+);[ \t]*(?://[ \t]*(.*))?$", re.M)
HEAD = re.compile(r"\b([a-z][a-z\-]+(?: [a-z][a-z\-]+)?) (indicator|oscillator|pattern|filter|stop|trailing|exit|strategy|index|bands|channel|model|test|ratio|entry|sizing)\b")
STOP = set("the a an this our that any each one new simple custom our your my its their following main base same first second other basic standard technical trading proposed given entire specific own".split())

INPUT_CAT = [
 ("stop-loss", r"stop.?loss|\bsl\b|^sl|sl_|stoploss"), ("take-profit", r"take.?profit|\btp\b|^tp|tp_|takeprofit|target"),
 ("trailing", r"trail"), ("breakeven", r"break.?even|\bbe\b|^be_"), ("lot/volume", r"\blots?\b|lot|volume"),
 ("risk %", r"risk"), ("magic/id", r"magic"), ("period/length", r"period|length|lookback|window|bars"),
 ("level/threshold", r"level|threshold|upper|lower|overbought|oversold"), ("timeframe", r"timeframe|\btf\b|period_[a-z]"),
 ("time/session", r"hour|minute|session|time|start|end|day"), ("spread/slippage", r"spread|slippage|deviation"),
 ("max positions/orders", r"max.?(pos|trades|orders)"), ("grid/martingale", r"grid|step|multiplier|martingale"),
 ("drawdown/loss limit", r"drawdown|\bdd\b|loss"), ("multiplier/coefficient", r"mult|coef|factor|ratio|k\b"),
 ("ml/training", r"epoch|learning|train|neuron|layer|batch|hidden"), ("other", r"."),
]

def work(item):
    aid, meta = item
    prose, code = split((LIB / "md" / f"{aid}.md").read_text(encoding="utf-8", errors="replace"))
    hits = {}
    for x, rx in RX:
        n = len(rx.findall(prose))
        if n:
            hits[x["id"]] = n
    calls = CALLS.findall(code)
    inp = [(aid, a, b.strip()[:40], (c or "").strip()[:80]) for a, b, c in INPUT.findall(code)]
    hd = set()
    for a, b in HEAD.findall(prose):
        w = a.split()
        if w[0] in STOP: a = " ".join(w[1:])
        if a and a not in STOP: hd.add(f"{a} {b}")
    return aid, meta, hits, calls, inp, hd, len(prose), len(code)

def main():
    from multiprocessing import Pool
    art = {}
    concept_articles = defaultdict(set); concept_mentions = Counter(); per_art_mentions = defaultdict(Counter)
    calls_articles = defaultdict(set); calls_n = Counter()
    inputs = []
    heads = defaultdict(set)
    with Pool(10) as pool:
        results = pool.map(work, sorted(screen.items()), chunksize=20)
    for aid, meta, hits, calls, inp, hd, lp, lc in results:
        include = meta["decision"] == "include" or (meta["decision"] == "unmatched" and len(hits) >= 5)
        art[aid] = {"include": include, "hits": hits, "section": meta["section"], "year": meta["year"], "title": meta["title"], "prose_chars": lp, "code_chars": lc, "decision": meta["decision"]}
        if not include:
            continue
        for k, n in hits.items():
            concept_articles[k].add(aid); concept_mentions[k] += n; per_art_mentions[k][aid] = n
        for m in calls:
            calls_articles[m].add(aid); calls_n[m] += 1
        inputs.extend(inp)
        for h in hd: heads[h].add(aid)
    json.dump(art, open("articles.json", "w"))
    inc = [a for a, v in art.items() if v["include"]]
    print("included articles", len(inc), "of", len(art))
    with open("concept_counts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["family", "concept", "status", "slugs", "slugs_exist", "articles", "pct_included", "mentions", "top_ids", "note"])
        for x in C:
            k = x["id"]; s = [t.strip() for t in x["slugs"].split(";") if t.strip()]
            top = [a for a, _ in per_art_mentions[k].most_common(3)]
            w.writerow([x["family"], k, x["status"], x["slugs"], all(t in slugs for t in s), len(concept_articles[k]), round(100 * len(concept_articles[k]) / len(inc), 1), concept_mentions[k], " ".join(top), x["note"]])
    fam = defaultdict(lambda: Counter()); famw = defaultdict(lambda: Counter())
    for x in C:
        fam[x["family"]][x["status"]] += 1; famw[x["family"]][x["status"]] += len(concept_articles[x["id"]])
    with open("family_summary.txt", "w") as f:
        for fm in fam:
            tot = sum(fam[fm].values()); totw = sum(famw[fm].values()) or 1
            line = f"{fm}: concepts {tot} " + " ".join(f"{s}={fam[fm][s]}" for s in ["covered", "renamed", "partial", "missing"]) + \
                   f" | covered+renamed {100*(fam[fm]['covered']+fam[fm]['renamed'])/tot:.0f}% | article-weighted: " + \
                   " ".join(f"{s}={100*famw[fm][s]/totw:.0f}%" for s in ["covered", "renamed", "partial", "missing"])
            print(line); f.write(line + "\n")
    with open("mql_calls.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["call", "articles", "calls"])
        for m, s in sorted(calls_articles.items(), key=lambda t: -len(t[1])): w.writerow([m, len(s), calls_n[m]])
    cat = Counter(); cat_art = defaultdict(set)
    with open("inputs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["article", "name", "default", "comment", "category"])
        for aid, name, val, com in inputs:
            t = (name + " " + com).lower()
            cc = next(c for c, rx in INPUT_CAT if re.search(rx, t))
            cat[cc] += 1; cat_art[cc].add(aid); w.writerow([aid, name, val, com, cc])
    print("inputs", len(inputs), "articles with inputs", len({i[0] for i in inputs}))
    for cc, n in cat.most_common(): print(f"  {cc}: {n} inputs in {len(cat_art[cc])} articles")
    known = [rx for _, rx in RX]
    with open("discovery.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["phrase", "articles", "matched_by_concept_list"])
        for h, s in sorted(heads.items(), key=lambda t: -len(t[1])):
            if len(s) >= 8: w.writerow([h, len(s), any(r.search(h) for r in known)])

if __name__ == "__main__":
    main()
