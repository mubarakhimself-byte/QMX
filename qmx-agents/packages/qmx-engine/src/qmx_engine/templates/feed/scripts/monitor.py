"""The feed's cheap look at its source: list what is there now, and let the `monitor` node
compare it with the last fire. Unchanged ends the fire `silent`, so nothing downstream starts
and no tokens are spent.

The run's input is the source definition (AD-68). `method` is `rss`, `sitemap`, `page-diff`,
`api` or `bulk-files`; `firecrawl` and `browser` need a connection adapter this template does
not carry yet and fail loudly rather than reading as an unchanged source.

The output is the snapshot alone: the same source gives the same JSON, byte for byte, because
the node's hash is what decides whether a fire happens at all. Nothing run-scoped goes in it.
"""

import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ElementTree
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

USER_AGENT = "QMX feed/1.0 (+qmx)"
TIMEOUT_SECONDS = 45
FAILURE = "[QMX_FAILURE]"


def fail(why: str) -> None:
    print(f"{FAILURE} {why}")
    raise SystemExit(0)


def read(location: str) -> bytes:
    """The bytes at a url, or at a path (which is what a test and a local file use).

    A relative path resolves under the workflow's own folder (`QMX_CODE`), so a feed can watch a
    file it ships with and its template test run needs no network.
    """
    target = location.strip()
    if target.startswith(("http://", "https://", "file://")):
        request = Request(target, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
        with urlopen(request, timeout=TIMEOUT_SECONDS) as reply:  # noqa: S310
            return reply.read()
    path = Path(target)
    if not path.is_absolute():
        path = Path(os.environ.get("QMX_CODE", ".")) / path
    return path.read_bytes()


def stamp(text: str) -> str:
    """A published time normalised to UTC where it parses, otherwise kept verbatim."""
    token = text.strip()
    if token == "":
        return ""
    try:
        moment = datetime.fromisoformat(token.replace("Z", "+00:00"))
    except ValueError:
        return token
    if moment.tzinfo is None:
        return token
    return moment.astimezone(UTC).isoformat()


def rss(body: bytes) -> list[dict[str, str]]:
    root = ElementTree.fromstring(body)  # noqa: S314 (the feed's own bytes)
    items: list[dict[str, str]] = []
    for element in root.iter():
        name = element.tag.rsplit("}", 1)[-1].lower()
        if name not in ("item", "entry"):
            continue
        found: dict[str, str] = {}
        for child in element:
            key = child.tag.rsplit("}", 1)[-1].lower()
            if key == "link" and child.get("href"):
                found["url"] = child.get("href") or ""
            elif key == "link" and child.text and child.text.strip():
                found["url"] = child.text.strip()
            elif child.text is not None and child.text.strip():
                found[key] = child.text.strip()
        url = found.get("url") or found.get("guid") or found.get("id") or ""
        items.append(
            {
                "id": url or found.get("title", ""),
                "url": url,
                "title": found.get("title", ""),
                "published": stamp(found.get("pubdate") or found.get("published") or ""),
            }
        )
    return items


def sitemap(body: bytes) -> list[dict[str, str]]:
    root = ElementTree.fromstring(body)  # noqa: S314
    items: list[dict[str, str]] = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1].lower() != "url":
            continue
        loc = ""
        changed = ""
        for child in element:
            key = child.tag.rsplit("}", 1)[-1].lower()
            if key == "loc" and child.text:
                loc = child.text.strip()
            elif key == "lastmod" and child.text:
                changed = child.text.strip()
        if loc:
            items.append({"id": loc, "url": loc, "title": loc, "published": stamp(changed)})
    return items


def api(body: bytes) -> list[dict[str, str]]:
    parsed = json.loads(body)
    rows = parsed if isinstance(parsed, list) else parsed.get("items") or parsed.get("results") or []
    items: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        url = str(row.get("url") or row.get("link") or row.get("id") or "")
        items.append(
            {
                "id": url,
                "url": url,
                "title": str(row.get("title") or row.get("name") or ""),
                "published": stamp(str(row.get("published") or row.get("date") or "")),
            }
        )
    return items


def page(body: bytes, location: str) -> list[dict[str, str]]:
    return [
        {"id": hashlib.sha256(body).hexdigest(), "url": location, "title": "", "published": ""}
    ]


given = json.load(sys.stdin).get("in") or {}
source = given.get("source") if isinstance(given, dict) else None
if not isinstance(source, dict):
    fail("the run names no source definition under `source`")
method = str(source.get("method") or "")
location = str(source.get("url") or source.get("endpoint") or source.get("path") or "")
if location == "":
    fail("the source definition names no url, endpoint or path")
if method not in ("rss", "sitemap", "page-diff", "api", "bulk-files"):
    fail(f"the {method!r} method is not built: rss, sitemap, page-diff, api or bulk-files")
try:
    body = read(location)
except OSError as error:
    fail(f"the source could not be read: {type(error).__name__}: {error}")
if method == "rss":
    items = rss(body)
elif method == "sitemap":
    items = sitemap(body)
elif method == "api":
    items = api(body)
elif method == "bulk-files":
    items = [
        {"id": line.strip(), "url": line.strip(), "title": "", "published": ""}
        for line in body.decode("utf-8", "replace").splitlines()
        if line.strip()
    ]
else:
    items = page(body, location)
snapshot = {
    "source": {
        "name": str(source.get("name") or ""),
        "method": method,
        "url": location,
        "lands_as": str(source.get("lands_as") or "source"),
        "collection": str(source.get("collection") or source.get("name") or ""),
        "licence": str(source.get("licence") or ""),
        "tags": sorted(str(tag) for tag in source.get("tags") or ()),
    },
    "items": sorted(items, key=lambda item: item["id"]),
}
print(json.dumps(snapshot, sort_keys=True))
