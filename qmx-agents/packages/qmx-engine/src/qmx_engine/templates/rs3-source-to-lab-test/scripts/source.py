"""The zero-token pre-check (card T8): the source's hash against the source ledger, so a source
already processed shows its old result instead of being read again. A paper is hashed by its id, a
video by its URL with tracking parameters dropped. Passes the source on with `seen`."""

import hashlib
import json
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit

TRACKING = ("si", "feature", "utm_source", "utm_medium", "utm_campaign", "t")

given = json.load(sys.stdin)["in"]
source = given["source"]
if source["kind"] == "paper":
    key = f"paper:{source['id']}"
else:
    url = urlsplit(source["url"])
    query = urlencode([(k, v) for k, v in parse_qsl(url.query) if k not in TRACKING])
    key = f"video:{url.netloc.removeprefix('www.')}{url.path}?{query}"
source_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
seen = source_hash in given.get("ledger", [])
print(json.dumps({"source": source, "source_hash": source_hash, "seen": seen}))
