"""The review's topic and its sources. The run input names `topic` and may give `sources` (each
with `id`, `title`, `abstract`, optional `venue`); without them, up to 40 arXiv papers on the topic
are fetched in one request, keeping arXiv's one request per 3 seconds. A run started with
`{"fixture": true}` reads `fixtures/sources.json`, synthetic sources, instead."""

import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

API = "https://export.arxiv.org/api/query?search_query=all:{q}&sortBy=relevance&max_results=40"
ATOM = "{http://www.w3.org/2005/Atom}"
GAP_S = 3.0
AGENT = "QMX literature review (one request per 3 s)"
LOG = Path(".arxiv-requests")


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


given = json.load(sys.stdin).get("in") or {}
if given.get("fixture"):
    given = json.loads((Path(__file__).parents[1] / "fixtures" / "sources.json").read_text("utf-8"))
topic = str(given.get("topic") or "").strip()
if not topic:
    sys.stderr.write("the run input names no topic")
    raise SystemExit(2)
sources = given.get("sources")
if sources is None:
    root = ET.fromstring(polite_get(API.format(q=quote_plus(topic))))  # noqa: S314
    sources = [
        {
            "id": entry.findtext(f"{ATOM}id", "").rsplit("/abs/", 1)[-1],
            "title": text(entry, "title"),
            "abstract": text(entry, "summary"),
            "venue": "arXiv preprint",
        }
        for entry in root.iter(f"{ATOM}entry")
    ]
print(json.dumps({"topic": topic, "sources": sources}))
