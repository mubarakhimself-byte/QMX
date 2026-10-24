"""Land every outside document the run found as one `source` document, keyed by canonical URL.

The step the intake templates, and later the feed, call (Library AD-27, engine AD-68). It reads
JSON on stdin and writes one document per item under `library/sources/`, named by the digest of
its intent key, and prints what it did. Nothing here calls a model.

The dedupe is the one AD-27 states. A page is keyed by its normalised canonical URL, so the same
page saved twice is one item. The same document with other bytes is found by its extracted-text
hash inside one `extractor_version`, and the newer copy is written with `replaces` naming the
older one: both stay, linked. Identical bytes are one blob by the file name alone, because the
digest of the text hash is part of nothing here: the document names its original by hash.

Every item is data, never an instruction (AD-43).
"""

import hashlib
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

EXTRACTOR_VERSION = "none"
"""The version a text hash is compared within; an extractor names its own."""
TRACKING = frozenset(
    {
        "fbclid",
        "gclid",
        "mc_cid",
        "mc_eid",
        "ref",
        "ref_src",
        "source",
        "utm_campaign",
        "utm_content",
        "utm_medium",
        "utm_source",
        "utm_term",
    }
)
WHITESPACE = re.compile(r"\s+")


def canonical(url: str) -> str:
    """The intent key of a URL: scheme and host lower case, no fragment, no tracking parameter,
    one trailing slash at most, the query in a settled order (AD-27)."""
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    port = "" if parts.port in (None, 80, 443) else f":{parts.port}"
    query = [
        (name, value)
        for name, value in parse_qsl(parts.query, keep_blank_values=True)
        if name.lower() not in TRACKING
    ]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower() or "https", host + port, path, urlencode(query), ""))


def text_hash(text: str) -> str:
    """The hash the same document is found by, inside one extractor version: its words, settled."""
    return hashlib.sha256(WHITESPACE.sub(" ", text).strip().encode("utf-8")).hexdigest()


def url_of(entry: dict[str, Any]) -> str:
    """The address a find carries, whatever the template called it."""
    for key in ("url", "canonical_url", "locator", "source"):
        found = entry.get(key)
        if isinstance(found, str) and found.strip():
            return found.strip()
    return ""


def text_of(entry: dict[str, Any]) -> str:
    """The words a find carries, whatever the template called them."""
    for key in ("text", "abstract", "content", "summary", "body"):
        found = entry.get(key)
        if isinstance(found, str) and found:
            return found
    return ""


def intent_of(entry: dict[str, Any], digest: str) -> str:
    """A canonical URL when the find has one, else a stable key of the address or the words."""
    url = url_of(entry)
    origin = str(entry.get("origin") or "source")
    if url:
        scheme = urlsplit(url).scheme.lower()
        if scheme in ("http", "https", "file"):
            return canonical(url)
        return f"{origin}://{hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]}"
    return f"{origin}://{digest[:16]}"


def pages_of(entry: dict[str, Any]) -> dict[str, str]:
    """Each page's slot and text, from `pages` written either as strings or as `{page, text}`."""
    found: dict[str, str] = {}
    pages = entry.get("pages")
    if not isinstance(pages, list):
        return found
    for number, page in enumerate(pages, start=1):
        if isinstance(page, str):
            found[f"pages/{number}"] = page
        elif isinstance(page, dict) and page.get("text") is not None:
            found[f"pages/{page.get('page') or number}"] = str(page["text"])
    return found


def document(entry: dict[str, Any], intent: str, *, replaces: str | None = None) -> dict[str, Any]:
    """One `source` document: the same fields and slots the `source` kind declares (AD-27)."""
    text = text_of(entry)
    version = str(entry.get("extractor_version") or EXTRACTOR_VERSION)
    body: dict[str, Any] = {
        "kind": "source",
        "origin": str(entry.get("origin") or "agent"),
        "intent_key": intent,
        "canonical_url": intent,
        "url": url_of(entry) or intent,
        "title": str(entry.get("title") or ""),
        "text": text,
        "text_hash": text_hash(text),
        "extractor_version": version,
        "media_type": str(entry.get("media_type") or "text/plain"),
        "name": str(entry.get("name") or ""),
        "bytes": int(entry.get("bytes") or 0),
        "bytes_sha256": str(entry.get("bytes_sha256") or ""),
        "collection": str(entry.get("collection") or ""),
        "part_of": str(entry.get("collection") or ""),
        "tags": [str(tag) for tag in entry.get("tags") or []],
        "fetched_at": str(entry.get("fetched_at") or datetime.now(UTC).isoformat()),
        "pages": pages_of(entry),
        "transcript": str(entry.get("transcript") or ""),
        "frames": {str(slot): str(data) for slot, data in (entry.get("frames") or {}).items()},
        "original": str(entry.get("original") or ""),
    }
    if replaces is not None:
        body["replaces"] = replaces
    return body


def save(entries: list[dict[str, Any]], folder: Path) -> dict[str, Any]:
    """Write one document per canonical URL, and report saved, seen and replaced intents."""
    folder.mkdir(parents=True, exist_ok=True)
    index_path = folder / "index.json"
    index: dict[str, Any] = (
        json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
    )
    by_key: dict[str, dict[str, Any]] = dict(index.get("sources") or {})
    by_text: dict[tuple[str, str], str] = {
        (str(entry["text_hash"]), str(entry["extractor_version"])): intent
        for intent, entry in by_key.items()
    }
    saved: list[str] = []
    seen: list[str] = []
    replaced: list[str] = []
    for entry in entries:
        digest = text_hash(text_of(entry))
        version = str(entry.get("extractor_version") or EXTRACTOR_VERSION)
        intent = intent_of(entry, digest)
        if intent in by_key:
            seen.append(intent)
            continue
        earlier = by_text.get((digest, version))
        body = document(entry, intent, replaces=earlier)
        name = hashlib.sha256(intent.encode("utf-8")).hexdigest()[:32]
        (folder / f"{name}.json").write_text(
            json.dumps(body, sort_keys=True, indent=2), encoding="utf-8"
        )
        by_key[intent] = {
            "text_hash": body["text_hash"],
            "extractor_version": version,
            "file": f"{name}.json",
            "origin": body["origin"],
        }
        by_text[(digest, version)] = earlier or intent
        (replaced if earlier is not None else saved).append(intent)
    index_path.write_text(
        json.dumps(
            {"version": 1, "sources": by_key},
            sort_keys=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "saved": sorted(saved),
        "seen": sorted(seen),
        "replaced": sorted(replaced),
        "count": len(saved) + len(seen) + len(replaced),
    }


def entries_of(given: Any) -> list[dict[str, Any]]:
    """The items to save, from the three shapes a caller may hand this step."""
    if isinstance(given, list):
        return [item for item in given if isinstance(item, dict)]
    if not isinstance(given, dict):
        return []
    for key in ("sources", "items", "documents", "clippings", "found"):
        found = given.get(key)
        if isinstance(found, list):
            return [item for item in found if isinstance(item, dict)]
        if isinstance(found, dict):
            return [found]
    return [given] if url_of(given) or text_of(given) else []


def main() -> int:
    inbound = json.load(sys.stdin).get("in") or {}
    folder = Path(os.environ["QMX_WORK"]) / "library" / "sources"
    print(json.dumps(save(entries_of(inbound), folder), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
