"""Claim the items a changed feed listed, fetch each one, and save it through `save_source`.

The monitor already proved the source changed; its diff lists what is new. Each new item is
claimed by the intent key `save_source` gives it (its canonical URL, else a key of its address)
before anything is fetched, so two fires, or a re-run after a crash, cannot fetch the same item
twice. The claim is a file created with `O_EXCL` under the workflow's shared work folder: the fire
that creates it owns the item, and a claim that is already there reports `held` and fetches
nothing.

The fetched items go to the shared `save_source` step (`_shared/save-source`, Library AD-27), the
one writer every intake template uses, so a feed item is the same `source` document, keyed and
deduplicated the same way, with `origin: feed` and the collection it is `part-of`. The step is
loaded from the installed engine's pack because the bundle carries only this template's own
files. The feed's own fields that document does not carry (`licence`, `published`,
`truncated`) are added to each document it saved.

Every item is data, never an instruction (AD-43): the document quotes the page and holds no
instruction to follow.
"""

import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from urllib.request import Request, urlopen

from qmx_engine.templates.catalog import SHARED

USER_AGENT = "QMX feed/1.0 (+qmx)"
TIMEOUT_SECONDS = 45
BODY_LIMIT = 2_000_000
TAG = re.compile(r"<[^>]+>")


def shared_step() -> ModuleType:
    path = SHARED / "save-source" / "scripts" / "save_source.py"
    spec = importlib.util.spec_from_file_location("save_source", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"no save_source step at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def text_of(body: bytes) -> str:
    raw = body.decode("utf-8", "replace")
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", TAG.sub(" ", raw)).strip()[:200_000]


def fetch(location: str) -> bytes:
    if location.startswith(("http://", "https://", "file://")):
        request = Request(  # noqa: S310 (the feed's own item url)
            location, headers={"User-Agent": USER_AGENT, "Accept": "*/*"}
        )
        with urlopen(request, timeout=TIMEOUT_SECONDS) as reply:  # noqa: S310
            return reply.read(BODY_LIMIT + 1)
    path = Path(location)
    if not path.is_absolute():
        path = Path(os.environ.get("QMX_CODE", ".")) / path
    return path.read_bytes()[: BODY_LIMIT + 1]


save_source = shared_step()
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
claims = Path(os.environ["QMX_WORK_SHARED"]) / "claims"
claims.mkdir(parents=True, exist_ok=True)
sources = Path(os.environ["QMX_WORK"]) / "library" / "sources"
entries: list[dict] = []
extra: dict[str, dict] = {}
held: list[str] = []
failed: list[str] = []
for item in items:
    if not isinstance(item, dict):
        continue
    location = str(item.get("url") or item.get("id") or "").strip()
    if location == "":
        continue
    intent = save_source.intent_of({"url": location, "origin": "feed"}, "")
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
        body = fetch(location)
    except (OSError, ValueError) as error:
        claim.unlink(missing_ok=True)
        failed.append(f"{intent}: {type(error).__name__}")
        continue
    entries.append(
        {
            "origin": "feed",
            "url": location,
            "title": str(item.get("title") or ""),
            "collection": collection,
            "tags": list(source.get("tags") or []),
            "text": text_of(body[:BODY_LIMIT]),
        }
    )
    extra[intent] = {
        "licence": str(source.get("licence") or ""),
        "published": str(item.get("published") or ""),
        "truncated": len(body) > BODY_LIMIT,
    }
saved = save_source.save(entries, sources)
landed = sorted([*saved["saved"], *saved["replaced"]])
for intent in landed:
    target = sources / f"{hashlib.sha256(intent.encode('utf-8')).hexdigest()[:32]}.json"
    document = json.loads(target.read_text(encoding="utf-8"))
    target.write_text(
        json.dumps({**document, **extra.get(intent, {})}, sort_keys=True, indent=2),
        encoding="utf-8",
    )
print(
    json.dumps(
        {
            "collection": collection,
            "landed": landed,
            "held": sorted(held),
            "failed": sorted(failed),
            "status": "landed" if landed else "nothing_new",
        },
        sort_keys=True,
    )
)
