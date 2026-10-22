"""An operator purge, on every copy (Library AD-6).

`purge(blob_id, reason)` is the one exception to archive-never-delete: the operator alone, for a
blob that holds a secret. The bytes go, the tombstone stays, and the object that named the blob
reads `blob_purged` for that slot. This module is the Hub's side: the store's own purge (AD-6's
verb), the bucket copy, and the ref the replicas follow when they next sync.

The bucket is a directory the server pushes to nightly (AD-16), so "the bucket" here is that
directory's copy of the blob; a bucket that lives behind an S3 API is the same three operations.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from qmx_library.principal import Principal
from qmx_library.store import Store, canonical


@dataclass(frozen=True, slots=True)
class Purged:
    blob_id: str
    reason: str
    at: str
    ref: str
    tombstone: str
    targets: tuple[str, ...]
    """Every copy the tombstone reached, `hub`, `bucket:<path>`."""


OPERATOR: Final = Principal("operator")


def purge_everywhere(
    store: Store,
    blob_id: str,
    reason: str,
    *,
    who: Principal = OPERATOR,
    buckets: Sequence[Path] = (),
) -> Purged:
    """Purge `blob_id` on the Hub store and on each bucket copy, and record the reason.

    `who` is the principal the Hub's door derived. The store refuses anyone but the operator, so
    an agent or a run that reaches this function is refused rather than obeyed.

    The replicas apply the same tombstone on their next sync from the `refs/purges/<hex>` ref the
    store's purge moved, so no other call is needed for them.
    """
    done = store.purge(who, blob_id, reason)
    reached = ["hub"]
    at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    for root in buckets:
        if bucket_tombstone(root, blob_id, reason, at):
            reached.append(f"bucket:{root}")
    return Purged(blob_id, reason, at, done.ref, str(done.tombstone), tuple(reached))


def bucket_tombstone(root: Path, blob_id: str, reason: str, at: str) -> bool:
    """Drop the bucket's copy of one blob and leave its tombstone. False when the bucket never
    held it, which is not a failure: the nightly push may have run before the blob existed."""
    hexdigest = blob_id.removeprefix("sha256:")
    found = False
    for path in (
        root / "blobs" / hexdigest,
        root / "blobs" / hexdigest[:2] / hexdigest[2:4] / hexdigest,
    ):
        if path.exists():
            path.unlink()
            found = True
    tombstone = root / "tombstones" / f"{hexdigest}.json"
    tombstone.parent.mkdir(parents=True, exist_ok=True)
    entry = {"blob_id": blob_id, "reason": reason, "at": at, "principal": "operator"}
    tombstone.write_bytes(canonical(entry))
    return found


def bucket_tombstones(root: Path) -> dict[str, str]:
    """Every purge the bucket holds, by blob id, for a drill or an alarm."""
    folder = root / "tombstones"
    if not folder.is_dir():
        return {}
    found: dict[str, str] = {}
    for path in sorted(folder.glob("*.json")):
        entry = json.loads(path.read_bytes())
        found[str(entry["blob_id"])] = str(entry["reason"])
    return found
