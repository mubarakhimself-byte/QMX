"""P-REPLAY (W5, acceptance): a save whose reply was lost is replayed once and never conflicts
(Library AD-14, AD-26; 55 probe row 6, F11).

A scratch `server` root is the one writer and a scratch `pc` root keeps the outbox. The lost
reply is staged exactly as it happens: the primary commits, the PC never hears it, and the entry
stays pending. Then:

1. The replay of that entry succeeds, the head is the intended object, there is no
   `merge-conflict` and the item exists once.
2. A second item takes the same path, and before its replay a server workflow moves the same ref
   on: the replay still succeeds, the newer head stays, and no conflict is minted.
3. A control case: an entry whose object never landed and whose head moved is parked as one
   `merge-conflict`, never applied silently.

**Pass:** both replays succeed and leave one item each with the intended or newer head, no
conflict for them, and one conflict for the control. **Fail:** a conflict, a `stale_head`, a
duplicate item, or a rewound head. The lost reply is staged by calling the store directly; the
wire is not killed, which is what the outbox replay is answering.

    uv run --no-sync python ../scripts/probes/data/p_replay.py
    uv run --no-sync python ../scripts/probes/data/p_replay.py --keep
"""

from __future__ import annotations

import argparse

from qmx_engine.ledger import redact
from qmx_library.outbox import Entry, Outbox, enter, replay
from qmx_library.port import Commit, Draft
from qmx_library.principal import Principal
from qmx_library.store import Store

from p_sync_disk import drop, two_roots

OPERATOR = Principal("operator")


class Primary:
    """A store seen the way a replay sees the primary: its ref log decides, not a reply."""

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
        return self.store.park_entry(entry.item, entry.ref, expected_head=entry.expected_head, intended=entry.object_id)


def lost(outbox: Outbox, done: Commit, draft: Draft, *, expected_head: str | None) -> Entry:
    """Append the entry a PC keeps when the write landed and the reply never came back."""
    entry = enter(
        draft,
        item=done.item,
        ref=done.ref,
        expected_head=expected_head,
        object_id=done.object_id,
        kind="note",
        schema_version=1,
    )
    outbox.append(entry)
    return entry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true")
    arguments = parser.parse_args(argv)
    root = two_roots("p-replay")
    problems: list[str] = []
    try:
        with Store.open(root / "server", redactor=redact, name="server") as server:
            outbox = Outbox(root / "pc" / "outbox.jsonl")

            draft = Draft("note", "n1", title="one")
            done = server.put(OPERATOR, draft, on="main", expected_head=None)
            lost(outbox, done, draft, expected_head=None)
            first = replay(outbox, Primary(server))
            print(f"(a) applied {first.applied}, parked {first.parked}, kept {first.kept}")
            if first.applied != [done.object_id] or first.parked or first.kept:
                problems.append(f"(a) the replay did not land the intended object: {first}")
            if server.head("n1", "main") != (done.object_id, 1):
                problems.append(f"(a) the head is {server.head('n1', 'main')}, not the intended one")

            saved = Draft("note", "n2", title="from the PC")
            placed = server.put(OPERATOR, saved, on="main", expected_head=None)
            lost(outbox, placed, saved, expected_head=None)
            moved = server.put(
                OPERATOR,
                Draft("note", "n2", title="the workflow moved it on", parents=[placed.object_id]),
                on="main",
                expected_head=placed.object_id,
            )
            second = replay(outbox, Primary(server))
            print(f"(b) applied {second.applied}, parked {second.parked}, head {server.head('n2', 'main')}")
            if second.applied != [placed.object_id] or second.parked:
                problems.append(f"(b) the replay did not succeed: {second}")
            if server.head("n2", "main") != (moved.object_id, 2):
                problems.append("(b) the replay rewound the newer head")
            if len(server.placed("n2", "note", "main")) != 2:
                problems.append("(b) the item is not the two versions it should be")

            anchor = server.put(OPERATOR, Draft("note", "n3", title="base"), on="main", expected_head=None)
            intended = server.ingest(
                {
                    "schema": "qmx.library.object/1",
                    "kind": "note",
                    "schema_version": 1,
                    "item_id": "n3",
                    "title": "never placed",
                    "summary": "",
                    "fields": {},
                    "blobs": {},
                    "parents": [anchor.object_id],
                    "relations": [],
                    "world": None,
                }
            )
            outbox.append(
                enter(
                    Draft("note", "n3", title="never placed", parents=[anchor.object_id]),
                    item="n3",
                    ref="main",
                    expected_head=anchor.object_id,
                    object_id=intended,
                    kind="note",
                    schema_version=1,
                )
            )
            server.put(
                OPERATOR,
                Draft("note", "n3", title="someone else", parents=[anchor.object_id]),
                on="main",
                expected_head=anchor.object_id,
            )
            control = replay(outbox, Primary(server))
            print(f"(c) parked {control.parked}, applied {control.applied}")
            if control.parked != ["refs/conflicts/n3/1"] or control.applied:
                problems.append(f"(c) the moved head was not parked as one conflict: {control}")
            if server.head("n3", "main")[1] != 2:
                problems.append("(c) the control case moved the ref")
            conflicts = server.catalog.refs_like("refs/conflicts/")
            print(f"conflicts on the primary: {conflicts}, entries left {len(outbox)}")
            if conflicts != 1:
                problems.append(f"the primary holds {conflicts} conflicts, expected 1")
            if len(outbox):
                problems.append(f"{len(outbox)} entries are still pending")
    finally:
        if not arguments.keep:
            drop(root)
    for problem in problems:
        print(f"  problem: {problem}")
    print(f"P-REPLAY {'FAIL' if problems else 'PASS'}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
