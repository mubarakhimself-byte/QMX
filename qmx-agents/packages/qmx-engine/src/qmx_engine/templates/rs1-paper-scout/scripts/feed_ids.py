"""The zero-token pre-check: the newest q-fin paper ids on arXiv (trading, portfolio management,
statistical finance, risk management). The monitor that runs this wakes the rest of the workflow
only when the ids change.

arXiv asks for at most one request every 3 seconds; each request's time is appended to
`.arxiv-requests` in the run's write zone, and the next request waits for the gap. A run started
with `{"fixture": true}` reads `fixtures/feed.json` instead of the network, so a test run is pinned;
the replay carries the run id, so the monitor fires on every test run.
"""

import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import Request, urlopen

FEED = (
    "https://export.arxiv.org/api/query?search_query=cat:q-fin.TR+OR+cat:q-fin.PM"
    "+OR+cat:q-fin.ST+OR+cat:q-fin.RM&sortBy=submittedDate&sortOrder=descending&max_results=30"
)
ATOM = "{http://www.w3.org/2005/Atom}"
GAP_S = 3.0
AGENT = "QMX paper scout (one request per 3 s)"
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


def arxiv_id(entry):
    return entry.findtext(f"{ATOM}id", "").rsplit("/abs/", 1)[-1].rsplit("v", 1)[0]


inputs = json.load(sys.stdin).get("in") or {}
if isinstance(inputs, dict) and inputs.get("fixture"):
    fixture = Path(__file__).parents[1] / "fixtures" / "feed.json"
    ids = json.loads(fixture.read_text("utf-8"))["ids"]
    run = os.environ.get("QMX_IDEMPOTENCY_KEY", "").split(":")[0]
    print(json.dumps({"ids": ids, "source": "fixture", "run": run}))
else:
    root = ET.fromstring(polite_get(FEED))  # noqa: S314
    ids = sorted({arxiv_id(entry) for entry in root.iter(f"{ATOM}entry")} - {""})
    print(json.dumps({"ids": ids, "source": "arxiv"}))
