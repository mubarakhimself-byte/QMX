"""Stratified sample of screened articles (seed 20261030), one per series, pilot ids excluded.
Writes sample.json and sample_extracts/<id>.txt (condensed: headings, rule sentences, input lines)."""
import json, random, re, pathlib
from collections import defaultdict
LIB = pathlib.Path("C:/Users/Mubarak/Desktop/QMX/.worktrees/mql5-library/data/mql5-library")
PILOT = set("1443 4828 2043 5543 7490 15909 13919 19460 18987 19508 22691 23456 21976 16931 22572 20330 23016 23656 5373 11216 13656 16971 23560 1425 4347 12635 13725 20020 1406 6986 7759 9511 10241 13737 18038 17065 21825 21833 1535 1364 11206 13835 15878 15713 19428 20317 22519 23543 19047 22936".split())
art = json.load(open("articles.json"))
def group(s):
    return s if s in ("Examples", "Trading systems", "Trading", "Tester", "Indicators") else "Other"
def band(y):
    y = int(y or 0)
    return "2005-12" if y <= 2012 else "2013-19" if y <= 2019 else "2020-23" if y <= 2023 else str(y)
ALLOC = {"Examples": 16, "Trading systems": 16, "Trading": 12, "Tester": 6, "Indicators": 6, "Other": 8}
rng = random.Random(20261030)
cells = defaultdict(list)
for aid, v in art.items():
    if v["include"] and aid not in PILOT:
        cells[(group(v["section"]), band(v["year"]))].append(aid)
picked, seen_series = [], set()
for g, n in ALLOC.items():
    bands = {b: sorted(ids) for (gg, b), ids in cells.items() if gg == g}
    total = sum(len(x) for x in bands.values())
    quota = {b: max(1, round(n * len(ids) / total)) for b, ids in bands.items()}
    for b, ids in sorted(bands.items()):
        rng.shuffle(ids)
        k = 0
        for aid in ids:
            s = re.split(r"\(|:| - ", art[aid]["title"] or "")[0].strip().lower()
            if s in seen_series: continue
            seen_series.add(s); picked.append(aid); k += 1
            if k >= quota[b]: break
json.dump(picked, open("sample.json", "w"))
print(len(picked))
KEY = re.compile(r"(enter|entry|open (a )?(buy|sell|long|short|position)|exit|close|stop.?loss|take.?profit|trail|break.?even|lot|risk|size|filter|condition|signal|optimi|parameter|tun|adapt|threshold|session|hour|spread|regime|timeframe|confirm)", re.I)
out = pathlib.Path("sample_extracts"); out.mkdir(exist_ok=True)
FENCE = re.compile(r"```.*?```", re.S)
INPUT = re.compile(r"^\s*s?input\s+.*$", re.M)
for aid in picked:
    md = (LIB / "md" / f"{aid}.md").read_text(encoding="utf-8", errors="replace")
    md = re.split(r"\*\*Attached files\*\*", md.split("\n---\n", 1)[-1])[0]
    code = "\n".join(FENCE.findall(md)); prose = FENCE.sub(" ", md)
    prose = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", prose); prose = re.sub(r"\]\([^)]*\)", "]", prose)
    heads = [l.strip("# ").strip() for l in prose.splitlines() if l.startswith("#")][:30]
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n", prose) if 40 < len(s.strip()) < 400 and KEY.search(s)]
    inputs = [l.strip()[:120] for l in INPUT.findall(code)][:30]
    v = art[aid]
    txt = f"# {aid} | {v['section']} | {v['year']} | {v['title']}\nHEADINGS: " + " / ".join(heads) + "\nINPUTS:\n" + "\n".join(inputs) + "\nRULE SENTENCES:\n" + "\n".join(sents[:45])
    (out / f"{aid}.txt").write_text(txt[:7000], encoding="utf-8")
