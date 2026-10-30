"""Compact reading extract per sampled article: strategy inputs (no colour/font/panel) and rule sentences."""
import json, re, sys, pathlib
LIB = pathlib.Path("C:/Users/Mubarak/Desktop/QMX/.worktrees/mql5-library/data/mql5-library")
art = json.load(open("articles.json")); ids = json.load(open("sample.json"))
lo, hi, cap = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
FENCE = re.compile(r"```.*?```", re.S)
KEY = re.compile(r"\b(buy|sell|long|short|open(s|ed)? (a )?(position|trade)|enter|entry|exit|close[sd]? (the )?(position|trade)|stop.?loss|take.?profit|trailing|break.?even|lot size|risk|optimi[sz]|filter|session|condition|signal|parameter|adapt|retrain|recalculat|threshold)\b", re.I)
SKIP = re.compile(r"colou?r|font|panel|width|label|draw|corner|style|show|magic|comment|_x\b|_y\b|\bx\b|\by\b", re.I)
for aid in ids[lo:hi]:
    md = (LIB / "md" / f"{aid}.md").read_text(encoding="utf-8", errors="replace")
    md = re.split(r"\*\*Attached files\*\*", md.split("\n---\n", 1)[-1])[0]
    code = "\n".join(FENCE.findall(md)); prose = FENCE.sub(" ", md)
    prose = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", prose); prose = re.sub(r"\]\([^)]*\)", "]", prose)
    inputs = []
    for l in re.findall(r"^\s*s?input\s+(?!group).*$", code, re.M):
        l = re.sub(r"\s+", " ", l.strip())
        if not SKIP.search(l) and l not in inputs: inputs.append(l[:90])
    sents = [re.sub(r"\s+", " ", s.strip()) for s in re.split(r"(?<=[.!?])\s+|\n", prose) if 50 < len(s.strip()) < 300 and KEY.search(s)]
    v = art[aid]
    t = f"## {aid} | {v['section']} | {v['year']} | {v['title']}\nIN: " + " || ".join(inputs[:14]) + "\nTXT: " + " ~ ".join(sents[:60])
    print(t[:cap].encode("ascii", "replace").decode()); print()
