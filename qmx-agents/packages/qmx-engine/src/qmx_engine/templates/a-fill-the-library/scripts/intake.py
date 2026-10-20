"""Funnel stage 1, intake: each dropped item becomes an inventory row. URLs are normalised (YouTube
short links and tracking parameters folded away), duplicates merge with all their provenance, and
every row gets a stable id from its locator. Anything that is not a URL is a note, kept as written.

A playlist, a channel or a saved collection is expanded into one row per item without asking
(ruling 35, AD-46): a fixture run reads the pinned expansion under `playlists` in
`fixtures/inventory.json`, a live run asks `yt-dlp` for the entries, and with neither the row is
kept as it stands and `collections` names why. The run input is `items`, a list of strings; a run
started with `{"fixture": "<name>"}` takes that fixture's items from `fixtures/inventory.json`."""

import hashlib
import json
import shutil
import subprocess
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
    elif is_collection(host, parts.path, parts.query):
        kind = "collection"
    return kind, urlunsplit(("https", host, parts.path, query, ""))


def is_collection(host, path, query) -> bool:
    """One URL that stands for a list: a playlist, a channel, a saved collection, a bookmark."""
    if host.endswith("youtube.com"):
        return path == "/playlist" or path.startswith(("/@", "/channel/", "/c/", "/user/"))
    if host.endswith("instagram.com"):
        return path.startswith(("/saved", "/collections"))
    if host.endswith(("x.com", "twitter.com")):
        return path.rstrip("/") == "/i/bookmarks"
    return bool(path.endswith(("/saved", "/bookmarks"))) and "list" in query


def listed(locator, pinned):
    """The members `locator` names: the pinned expansion first, then `yt-dlp`, else why not."""
    if locator in pinned:
        return pinned[locator], "fixture"
    if pinned is not None:
        return None, "no expansion: the fixture pins none for this collection"
    tool = shutil.which("yt-dlp")
    if tool is None:
        return None, "no expansion: yt-dlp is not installed"
    argv = [tool, "--flat-playlist", "--ignore-errors", "--print", "%(url)s", locator]
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=300, check=False)
    except (OSError, subprocess.SubprocessError) as why:
        return None, f"no expansion: yt-dlp failed: {why.__class__.__name__}"
    found = [line.strip() for line in done.stdout.splitlines() if line.strip()]
    return (found, "yt-dlp") if found else (None, "no expansion: yt-dlp listed nothing")


given = json.load(sys.stdin).get("in") or {}
fixture_name = given.get("fixture")
pinned = None
if fixture_name:
    path = Path(__file__).parents[1] / "fixtures" / "inventory.json"
    loaded = json.loads(path.read_text("utf-8"))
    items = loaded["fixtures"][fixture_name]
    pinned = loaded.get("playlists") or {}
else:
    items = given.get("items") or []

rows = {}
collections = []
for raw in items:
    kind, locator = normal(str(raw))
    members = [(kind, locator)]
    if kind == "collection":
        found, how = listed(locator, pinned)
        members = [("link", locator)] if found is None else [normal(member) for member in found]
        collections.append({"locator": locator, "items": len(found or []), "expanded_by": how})
    for member_kind, member in members:
        fresh = {
            "id": f"inv-{letters(member)}",
            "kind": member_kind,
            "locator": member,
            "provenance": [],
        }
        row = rows.setdefault(member, fresh)
        row["provenance"].append(str(raw))
print(
    json.dumps(
        {"inventory": list(rows.values()), "collections": collections, "fixture": fixture_name}
    )
)
