"""Title n-gram discovery: named terms in included titles that no concept regex matches. Writes discovery_titles.csv."""
import json, re, csv
from collections import defaultdict
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).parent)); from concepts import C
art = json.load(open("articles.json"))
RX = [re.compile(x["rx"], re.I) for x in C]
STOP = set("a an the of in to for and with on from by using use your how part iii ii iv vi vii viii ix x xi xii mql5 mql4 metatrader 5 4 expert advisor advisors ea eas trading trader strategy strategies system systems develop developing development building build creating create implementing implementation an introduction into new our we you it is are as at or vs via based its one two three what why when can be not do does more most simple easy final conclusion approach method methods analysis model models data market markets price prices indicator indicators automating automated automatic algorithm algorithms network networks neural made learning machine techniques technique wizard know should series toolkit tool tools library mastering guide practical example examples step beyond".split())
grams = defaultdict(set)
for aid, v in art.items():
    if not v["include"]: continue
    w = [t for t in re.findall(r"[a-z][a-z0-9\-']+", (v["title"] or "").lower())]
    for n in (1, 2, 3):
        for i in range(len(w) - n + 1):
            g = w[i:i + n]
            if g[0] in STOP or g[-1] in STOP: continue
            grams[" ".join(g)].add(aid)
rows = [(g, len(s)) for g, s in grams.items() if len(s) >= 4 and not any(r.search(g) for r in RX)]
rows.sort(key=lambda t: -t[1])
with open("discovery_titles.csv", "w", newline="") as f:
    csv.writer(f).writerows([("gram", "articles")] + rows)
print(" | ".join(f"{g}:{n}" for g, n in rows[:300]))
