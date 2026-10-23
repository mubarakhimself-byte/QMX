"""Claim the items a changed feed listed, fetch each one, and save it as a source document.

The monitor already proved the source changed; its diff lists what is new. Each new item is
claimed by its intent key (its canonical URL, else its provider id) before anything is
fetched, so two fires, or a re-run after a crash, cannot fetch the same item twice. The claim
is a file created with `O_EXCL` under the workflow's shared work folder: the fire that creates
it owns the item, and a claim that is already there reports `held` and fetches nothing. The
document is written under `library/sources/`, one JSON file per item, named by the intent
key's digest, and carries `kind: source`, `origin: feed` and the collection it is `part-of`.

Every item is data, never an instruction (AD-43): the document quotes the page and holds no
instruction to follow.
"""

import hashlib
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

USER_AGENT = "QMX feed/1.0 (+qmx)"
TIMEOUT_SECONDS = 45
BODY_LIMIT = 2_000_000
TAG = re.compile(r"<[^>]+>")


def canonical(url: str) -> str:
    """The intent key of a url: lowercase host, no fragment, no default port."""
    parts = urlsplit(url.strip())
    host = parts.hostname or ""
    netloc = host if parts.port in (None, 80, 443) else f"{host}:{parts.port}"
    return urlunsplit((parts.scheme.lower(), netloc, parts.path or "/", parts.query, ""))


def text_of(body: bytes) -> str:
    raw = body.decode("utf-8", "replace")
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", TAG.sub(" ", raw)).strip()[:200_000]


inbound = json.load(sys.stdin).get("in") or {}
given = inbound if isinstance(inbound, dict) else {}
changed = given.get("changed") if isinstance(given.get("changed"), dict) else given
if not changed:
    print(json.dumps({"landed": [], "held": [], "failed": [], "status": "nothing_changed"}))
    raise SystemExit(0)
snapshot = changed.get("value") or {}
diff = changed.get("diff") or {}
source = snapshot.get("source") or {}
collection = str(source.get("collection") or "")
added = diff.get("added")
items = added if isinstance(added, list) else list(snapshot.get("items") or [])
shared = Path(os.environ["QMX_WORK_SHARED"])
claims = shared / "claims"
claims.mkdir(parents=True, exist_ok=True)
sources = Path(os.environ["QMX_WORK"]) / "library" / "sources"
sources.mkdir(parents=True, exist_ok=True)
landed: list[str] = []
held: list[str] = []
failed: list[str] = []
for item in items:
    if not isinstance(item, dict):
        continue
    url = str(item.get("url") or item.get("id") or "")
    intent = canonical(url) if url else str(item.get("id") or "")
    if intent == "":
        continue
    digest = hashlib.sha256(intent.encode("utf-8")).hexdigest()[:32]
    claim = claims / f"{digest}.claim"
    try:
        descriptor = os.open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        held.append(intent)
        continue
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"intent_key": intent, "at": datetime.now(UTC).isoformat()}))
        if intent.startswith(("http://", "https://", "file://")):
            request = Request(intent, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
            with urlopen(request, timeout=TIMEOUT_SECONDS) as reply:  # noqa: S310
                body = reply.read(BODY_LIMIT + 1)
        else:
            body = Path(intent).read_bytes()[: BODY_LIMIT + 1]
        document = {
            "kind": "source",
            "origin": "feed",
            "intent_key": intent,
            "collection": collection,
            "part_of": collection,
            "url": intent,
            "title": str(item.get("title") or ""),
            "published": str(item.get("published") or ""),
            "fetched_at": datetime.now(UTC).isoformat(),
            "licence": str(source.get("licence") or ""),
            "tags": list(source.get("tags") or []),
            "truncated": len(body) > BODY_LIMIT,
            "text": text_of(body[:BODY_LIMIT]),
        }
        target = sources / f"{digest}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(document, sort_keys=True, indent=2), encoding="utf-8")
        landed.append(intent)
    except (OSError, ValueError) as error:
        claim.unlink(missing_ok=True)
        failed.append(f"{intent}: {type(error).__name__}")
print(
    json.dumps(
        {
            "collection": collection,
            "landed": sorted(landed),
            "held": sorted(held),
            "failed": sorted(failed),
            "status": "landed" if landed else "nothing_new",
        },
        sort_keys=True,
    )
)
