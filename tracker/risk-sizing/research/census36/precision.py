"""Print N random match snippets (seed 7) for named concepts, to judge regex precision by hand.
Usage: python -I precision.py "concept id" ["concept id" ...]"""
import json, random, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from concepts import C
from census import split, LIB
art = json.load(open("articles.json"))
N = 10
for cid in sys.argv[1:]:
    x = next(c for c in C if c["id"] == cid)
    rx = re.compile(x["rx"], re.I)
    ids = sorted(a for a, v in art.items() if v["include"] and cid in v["hits"])
    rng = random.Random(7); rng.shuffle(ids)
    print(f"=== {cid} ({len(ids)} articles)")
    for aid in ids[:N]:
        prose, _ = split((LIB / "md" / f"{aid}.md").read_text(encoding="utf-8", errors="replace"))
        ms = list(rx.finditer(prose)); m = rng.choice(ms)
        s = prose[max(0, m.start() - 70): m.end() + 50].replace("\n", " ")
        print(f"  {aid}: ...{s}...")
