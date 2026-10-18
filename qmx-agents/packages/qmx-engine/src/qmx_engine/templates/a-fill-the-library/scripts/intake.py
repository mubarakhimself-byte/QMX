"""Funnel stage 1, intake: each dropped item becomes an inventory row. URLs are normalised (YouTube
short links and tracking parameters folded away), duplicates merge with all their provenance, and
every row gets a stable id from its locator. Anything that is not a URL is a note, kept as written.
The run input is `items`, a list of strings; a run started with `{"fixture": "<name>"}` takes the
items under that name in `fixtures/inventory.json`. Expanding a playlist or channel needs the
operator's approval, so it is left out: such a URL is one row."""

import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

LETTERS = "abcdefghijklmnop"


def letters(text):
    """A short id in letters only, so ids never read as numbers in prose checks."""
    return "".join(LETTERS[int(c, 16)] for c in hashlib.sha256(text.encode()).hexdigest()[:10])


def normal(raw):
    text = raw.strip()
    parts = urlsplit(text)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return "note", text
    host = parts.netloc.casefold().removeprefix("www.").removeprefix("m.")
    if host == "youtu.be":
        return "video", f"https://www.youtube.com/watch?v={parts.path.strip('/')}"
    if host.endswith("youtube.com") and parts.path == "/watch":
        video = parse_qs(parts.query).get("v", [""])[0]
        return "video", f"https://www.youtube.com/watch?v={video}"
    kept = [(k, v) for k, v in parse_qs(parts.query).items() if not k.startswith("utm_")]
    query = urlencode(kept, doseq=True)
    kind = "tradingview" if "tradingview.com" in host else "link"
    if host.endswith("arxiv.org") or parts.path.casefold().endswith(".pdf"):
        kind = "paper"
    return kind, urlunsplit(("https", host, parts.path, query, ""))


given = json.load(sys.stdin).get("in") or {}
fixture = given.get("fixture")
if fixture:
    path = Path(__file__).parents[1] / "fixtures" / "inventory.json"
    items = json.loads(path.read_text("utf-8"))["fixtures"][fixture]
else:
    items = given.get("items") or []
rows = {}
for raw in items:
    kind, locator = normal(str(raw))
    fresh = {"id": f"inv-{letters(locator)}", "kind": kind, "locator": locator, "provenance": []}
    row = rows.setdefault(locator, fresh)
    row["provenance"].append(str(raw))
print(json.dumps({"inventory": list(rows.values()), "fixture": fixture}))
