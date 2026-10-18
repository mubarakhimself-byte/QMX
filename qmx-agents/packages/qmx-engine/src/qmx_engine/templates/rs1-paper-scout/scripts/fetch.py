"""Fetches the title, abstract, authors and date of each new paper id, newest first, at most 20, in
one arXiv request. It keeps arXiv's one-request-per-3-seconds rule with the pre-check through the
`.arxiv-requests` log in the run's write zone. Fixture replays read `fixtures/papers.json`."""

import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import Request, urlopen

API = "https://export.arxiv.org/api/query?id_list={ids}&max_results={n}"
ATOM = "{http://www.w3.org/2005/Atom}"
GAP_S = 3.0
AGENT = "QMX paper scout (one request per 3 s)"
LOG = Path(".arxiv-requests")
MOST = 20


def polite_get(url):
    if LOG.exists():
        wait = float(LOG.read_text("utf-8").split()[-1]) + GAP_S - time.time()
        if wait > 0:
            time.sleep(wait)
    request = Request(url, headers={"User-Agent": AGENT})  # noqa: S310
    try:
        with urlopen(request, timeout=60) as reply:  # noqa: S310
            return reply.read()
    finally:
        with LOG.open("a", encoding="utf-8") as log:
            log.write(f"{time.time():.3f}\n")


def text(entry, tag):
    return " ".join(entry.findtext(f"{ATOM}{tag}", "").split())


def paper(entry):
    return {
        "id": entry.findtext(f"{ATOM}id", "").rsplit("/abs/", 1)[-1].rsplit("v", 1)[0],
        "title": text(entry, "title"),
        "abstract": text(entry, "summary"),
        "authors": [
            " ".join(a.findtext(f"{ATOM}name", "").split()) for a in entry.iter(f"{ATOM}author")
        ],
        "published": text(entry, "published")[:10],
        "url": entry.findtext(f"{ATOM}id", ""),
    }


new = json.load(sys.stdin)["in"]
ids = sorted(new.get("ids") or [], reverse=True)[:MOST]
if not ids:
    print(json.dumps([]))
elif new.get("source") == "fixture":
    fixture = Path(__file__).parents[1] / "fixtures" / "papers.json"
    papers = json.loads(fixture.read_text("utf-8"))["papers"]
    print(json.dumps([p for p in papers if p["id"] in ids]))
else:
    root = ET.fromstring(polite_get(API.format(ids=",".join(ids), n=len(ids))))  # noqa: S314
    print(json.dumps([paper(entry) for entry in root.iter(f"{ATOM}entry")]))
