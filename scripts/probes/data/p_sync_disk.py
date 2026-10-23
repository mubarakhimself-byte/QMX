"""P-SYNC-DISK (W5, acceptance): a PC sync copies text and nothing else, and a blob it opens is a
cache copy (Library AD-10; 55 probe row 5).

Two scratch roots stand in for the two machines: `server` is the one writer and `pc` is a replica
of it. The server holds `source` items whose `transcript` carries a phrase that exists nowhere
else, and whose `content` is a binary of a size the probe names. Then:

1. One selective sync copies each transcript and no `content` at all, and the PC's search finds the
   phrase that only the server extracted (N1, S-30).
2. Opening one item on the PC fetches exactly that item's other blobs, and they arrive as cache
   copies a disk pressure may drop; a blob born on a store that holds one copy is never dropped
   (N3).
3. A second sync asks only for the ref moves after its cursor, and neither side lists its object
   ids (F10, F18).

**Pass:** the text slots arrive, the phrase is found, no original arrives unopened, the opened
blobs are cache copies and evictable, a born blob is not evicted, the second sync pulls nothing.
**Fail:** any of those does not hold. **Bound:** the originals here total `--megabytes` (default
24) because this probe runs on a builder's disk; Lane 2 runs it with 5 GB on the scratch server.

    uv run --no-sync python ../scripts/probes/data/p_sync_disk.py --megabytes 24
    uv run --no-sync python ../scripts/probes/data/p_sync_disk.py --keep
"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

from qmx_engine.ledger import redact
from qmx_library.client import Move, OwnerTable
from qmx_library.port import Draft
from qmx_library.principal import Principal
from qmx_library.store import Store

from qmx_hub.replicate import StorePeer, sync_since

SCRATCH = Path(os.environ.get("QMX_PROBE_SCRATCH", "D:/Temp/dr2b"))
OPERATOR = Principal("operator")
PHRASE = "the phrase only the server extracted"
ITEMS = 12


def two_roots(name: str) -> Path:
    """One scratch folder with a `server` root and a `pc` root, emptied first."""
    root = SCRATCH / name
    shutil.rmtree(root, ignore_errors=True)
    (root / "server").mkdir(parents=True)
    (root / "pc").mkdir(parents=True)
    return root


def drop(root: Path) -> None:
    shutil.rmtree(root, ignore_errors=True)


def bytes_in(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


class CountingPeer(StorePeer):
    """A store, plus the call a selective sync must never make: an object-id listing."""

    def __init__(self, store: Store) -> None:
        super().__init__(store)
        self.moves_asked: list[int] = []

    def moves(self, after: int) -> list[Move]:
        self.moves_asked.append(after)
        return super().moves(after)

    def object_ids(self) -> set[str]:
        raise AssertionError("a selective sync listed every object id")


class Serving:
    """The server root as the PC's `upstream`: an opened blob comes from there (AD-10)."""

    def __init__(self, store: Store) -> None:
        self.store = store

    def fetch(self, blob_id: str) -> bytes | None:
        try:
            return self.store.read_blob(blob_id)
        except Exception:
            return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--megabytes", type=int, default=24)
    parser.add_argument("--keep", action="store_true")
    arguments = parser.parse_args(argv)
    root = two_roots("p-sync-disk")
    problems: list[str] = []
    try:
        content = b"\x00" * (arguments.megabytes * 1024 * 1024 // ITEMS)
        with (
            Store.open(root / "server", redactor=redact, name="server") as server,
            Store.open(root / "pc", redactor=redact, name="pc", role="replica") as pc,
        ):
            heads = []
            for index in range(ITEMS):
                done = server.put(
                    OPERATOR,
                    Draft(
                        "source",
                        f"doc-{index}",
                        title=f"Paper {index}",
                        blobs={"transcript": f"{PHRASE} {index}".encode(), "content": content},
                    ),
                    on="main",
                    expected_head=None,
                )
                heads.append(done.object_id)
            server_bytes = bytes_in(root / "server")
            pc.upstream = Serving(server)
            remote, local = CountingPeer(server), CountingPeer(pc)

            synced = sync_since(local, remote, OwnerTable("server"), cursor=0)

            hits = sorted(hit.item for hit in pc.search(OPERATOR, "extracted"))
            copied = bytes_in(root / "pc" / "blobs")
            originals = [
                pc.get(OPERATOR, object_id).blobs["content"].blob_id for object_id in heads
            ]
            arrived_unasked = [blob_id for blob_id in originals if pc.has_blob(blob_id)]
            print(f"server root {server_bytes} bytes; pc blobs {copied} bytes after one sync")
            print(f"text blobs {synced.text_blobs}, objects {len(synced.pulled)}")
            print(f"pc search for 'extracted': {hits}")
            print(f"moves asked for: {remote.moves_asked}")
            print(f"originals that arrived without being opened: {len(arrived_unasked)}")
            if len(hits) != ITEMS:
                problems.append(f"the PC's search found {len(hits)} of {ITEMS} extracted items")
            if synced.text_blobs != ITEMS:
                problems.append(f"the sync copied {synced.text_blobs} text blobs, expected {ITEMS}")
            if arrived_unasked:
                problems.append(f"{len(arrived_unasked)} originals arrived without being opened")
            if remote.moves_asked != [0]:
                problems.append(f"the sync asked for moves {remote.moves_asked}, expected [0]")

            opened = pc.get(OPERATOR, heads[0], blobs="fetch")
            opened_bytes = sum(len(data) for data in opened.data.values())
            print(f"opened {opened.item}: {len(opened.data)} blobs, {opened_bytes} bytes")
            if opened_bytes <= len(content):
                problems.append("opening the item did not fetch its original too")
            cache = [blob_id for blob_id in pc.cached_blob_ids()]
            evicted = pc.evict_cache()
            print(f"cache copies on the PC {len(cache)}, evicted {len(evicted)}")
            if set(evicted) != set(cache):
                problems.append("a fetched blob cannot be evicted")
            born = server.blob_ids()
            server.evict_cache()
            if sorted(server.blob_ids()) != sorted(born):
                problems.append("an eviction took a blob born on the server")

            again = sync_since(local, remote, OwnerTable("server"), cursor=synced.cursor)
            print(f"second sync pulled {len(again.pulled)}, cursor {again.cursor}")
            if again.pulled:
                problems.append(f"the second sync pulled {len(again.pulled)} objects, expected 0")
    finally:
        if not arguments.keep:
            drop(root)
    for problem in problems:
        print(f"  problem: {problem}")
    print(f"P-SYNC-DISK {'FAIL' if problems else 'PASS'}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
