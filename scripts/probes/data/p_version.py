"""P-VERSION (W5, acceptance): a kind or schema version a reader lacks waits in the outbox and
names the side behind, and the other entries land (Library AD-14; 55 probe row 8, F16, N17).

Two scratch roots, `server` and `pc`, and a stand-in for the server at an older schema: a `Store`
subclass that reads `note` at schema version 1 only. Then:

1. A newer PC saves a `note` at schema version 2 plus an ordinary save. The sync refuses only the
   first, with `needs_update` and "the server needs updating"; the ordinary save lands; the first
   stays in the outbox.
2. The server updates (the real store answers) and the replay lands the first save; the outbox is
   empty and the head is the note the newer PC wrote.
3. The reverse case: a PC that reads no `note` at all pulls one from the server, and the sync says
   "this PC needs updating" and leaves the object alone.

**Pass:** the server takes only what it can read, the message names the side that is behind, the
refused save stays and then lands, and a mixed `qmx_version` with the same kinds syncs normally.
**Fail:** a host takes an entry it cannot read, the wrong side is named, or a save is lost.

    uv run --no-sync python ../scripts/probes/data/p_version.py
    uv run --no-sync python ../scripts/probes/data/p_version.py --keep
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path

from qmx_engine.ledger import redact
from qmx_library.client import OwnerTable
from qmx_library.outbox import Entry, Outbox, enter, replay
from qmx_library.port import Commit, Draft
from qmx_library.principal import Principal
from qmx_library.store import Store

from qmx_hub.replicate import StorePeer, sync_since

from p_sync_disk import drop, two_roots

OPERATOR = Principal("operator")


class Older(Store):
    """The server before it updated: it reads `note` at schema version 1 and nothing newer."""

    def versions(self) -> dict[str, int]:
        return {name: 1 if name == "note" else version for name, version in super().versions().items()}

    def can_read(self, kind_name: str, version: int) -> bool:
        return version <= 1 and super().can_read(kind_name, 1)


class Blind(Store):
    """A PC that does not know the `note` kind at all."""

    def versions(self) -> dict[str, int]:
        return {name: found for name, found in super().versions().items() if name != "note"}

    def can_read(self, kind_name: str, version: int) -> bool:
        return kind_name != "note" and super().can_read(kind_name, version)


class Newer(Store):
    """The server after it updated: it reads `note` at schema version 2."""

    def versions(self) -> dict[str, int]:
        return {**super().versions(), "note": 2}

    def can_read(self, kind_name: str, version: int) -> bool:
        return version <= 2 and super().can_read(kind_name, 1)


class Primary:
    """A store as the replay sees the primary."""

    def __init__(self, store: Store) -> None:
        self.store = store

    def ever_placed(self, object_id: str, item: str, ref: str) -> bool:
        return self.store.ever_placed(object_id, item, ref)

    def head(self, item: str, ref: str) -> str | None:
        found = self.store.head(item, ref)
        return None if found is None else found[0]

    def put(self, draft: Draft, *, on: str, expected_head: str | None) -> Commit:
        return self.store.put(OPERATOR, draft, on=on, expected_head=expected_head)

    def can_read(self, kind: str, version: int) -> bool:
        return self.store.can_read(kind, version)

    def park(self, entry: Entry) -> str:
        return self.store.park_entry(
            entry.item, entry.ref, expected_head=entry.expected_head, intended=entry.object_id
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true")
    arguments = parser.parse_args(argv)
    root = two_roots("p-version")
    problems: list[str] = []
    try:
        outbox = Outbox(root / "pc" / "outbox.jsonl")
        newer = Draft("note", "ahead", title="a note from a newer PC")
        plain = Draft("note", "plain", title="an ordinary save")
        intended = "fp1:sha256:" + "a" * 64
        outbox.append(
            enter(
                newer,
                item="ahead",
                ref="main",
                expected_head=None,
                object_id=intended,
                kind="note",
                schema_version=2,
            )
        )
        outbox.append(
            enter(
                plain,
                item="plain",
                ref="main",
                expected_head=None,
                object_id="fp1:sha256:" + "b" * 64,
                kind="note",
                schema_version=1,
            )
        )
        with Older.open(root / "server", redactor=redact, name="server") as older:
            refused = replay(outbox, Primary(older))
            print(f"at the older server: kept {refused.kept}, applied {len(refused.applied)}")
            print(f"  said: {refused.refused}")
            if refused.kept != ["ahead"]:
                problems.append(f"the older server kept {refused.kept}, expected ['ahead']")
            if not refused.refused or not refused.refused[0].startswith(
                "needs_update: the server needs updating"
            ):
                problems.append(f"the refusal does not name the server: {refused.refused}")
            if len(refused.applied) != 1 or older.head("plain", "main") is None:
                problems.append("the ordinary save did not land beside the refused one")
            if len(outbox) != 1:
                problems.append(f"{len(outbox)} entries are waiting, expected 1")
        with Newer.open(root / "server", redactor=redact, name="server") as updated:
            landed = replay(outbox, Primary(updated))
            head = updated.head("ahead", "main")
            print(f"after the update: applied {len(landed.applied)}, head {head}")
            if len(landed.applied) != 1 or head is None:
                problems.append("the waiting save did not land after the server updated")
            elif updated.get(OPERATOR, head[0]).title != "a note from a newer PC":
                problems.append("the landed save is not the one the newer PC wrote")
            if len(outbox):
                problems.append(f"{len(outbox)} entries are still waiting after the update")

        with Store.open(root / "server", redactor=redact, name="server") as server:
            server.put(
                OPERATOR,
                Draft("note", "server-note", title="a note only the server can read"),
                on="main",
                expected_head=None,
            )
            blind_root = root / "pc-blind"
            blind_root.mkdir()
            with Blind.open(blind_root, redactor=redact, name="pc", role="replica") as blind:
                synced = sync_since(StorePeer(blind), StorePeer(server), OwnerTable("server"), cursor=0)
                print(f"reverse: needs_update {synced.needs_update}, pulled {len(synced.pulled)}")
                if not synced.needs_update:
                    problems.append("the PC that lacks the kind pulled it anyway")
                elif "this PC needs updating" not in synced.needs_update[0]:
                    problems.append(f"the reverse refusal names the wrong side: {synced.needs_update}")
    finally:
        if not arguments.keep:
            drop(root)
    for problem in problems:
        print(f"  problem: {problem}")
    print(f"P-VERSION {'FAIL' if problems else 'PASS'}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
