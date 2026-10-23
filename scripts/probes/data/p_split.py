"""P-SPLIT (W5, acceptance): a restored PC that was primary at an older epoch stops being primary
at its first sync, and its offline moves are parked, never applied (Library AD-14; 55 probe row 7,
F12, F15, N13, N19).

Three scratch roots: `pc` is an old PC restored with `primary = pc` at epoch 1, `server` is the
real primary at epoch 2, and `restored` is the same store reopened after it learned the new epoch.
The PC works offline and moves its own `main` twice. Then its first sync learns epoch 2:

1. The store records the higher epoch and raises `library:epoch:pc`.
2. It refuses to act as primary: its next write is refused `ref_not_owned`.
3. Each offline move is parked as one `merge-conflict` item on `refs/conflicts/<item>/<n>`, and the
   conflict names the object it would have pushed.
4. The sync pushes nothing, and the server's own `main` head is unchanged.
5. The offline moves are still on the restored PC's own `main`: nothing was lost.

**Pass:** the epoch alarm, the refused write, one conflict per offline move, no push, the server's
`main` unchanged, and the offline heads still readable. **Fail:** the server's `main` moves to an
older head, or an offline move is lost or applied silently.

    uv run --no-sync python ../scripts/probes/data/p_split.py
    uv run --no-sync python ../scripts/probes/data/p_split.py --keep
"""

from __future__ import annotations

import argparse

from qmx_engine.ledger import redact
from qmx_library.client import OwnerTable
from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

from qmx_hub.replicate import StorePeer, sync_since

from p_sync_disk import drop, two_roots

OPERATOR = Principal("operator")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true")
    arguments = parser.parse_args(argv)
    root = two_roots("p-split")
    problems: list[str] = []
    try:
        with (
            Store.open(root / "pc", redactor=redact, name="pc") as pc,
            Store.open(root / "server", redactor=redact, name="server") as server,
        ):
            pc.record_primary(OPERATOR, "pc")
            offline = [
                pc.put(
                    OPERATOR,
                    Draft("note", f"moved-{index}", title=f"an offline note {index}"),
                    on="main",
                    expected_head=None,
                )
                for index in range(2)
            ]
            server.record_primary(OPERATOR, "server", epoch=2)
            theirs = server.put(
                OPERATOR,
                Draft("note", "shared", title="the server's own main"),
                on="main",
                expected_head=None,
            )

            shared = 0
            learned = pc.learn_epoch(server.epoch, shared_seq=shared)
            print(
                f"epoch on the PC {learned.primary}@{learned.epoch}, stale {learned.stale}, "
                f"alarms {pc.alarms}"
            )
            print(f"parked {learned.parked}")
            if not learned.stale:
                problems.append("the restored PC did not learn that it is behind")
            if pc.alarms != ("library:epoch:pc",):
                problems.append(f"the PC raised {pc.alarms}, expected library:epoch:pc")
            wanted = {f"refs/conflicts/moved-{index}/{1}" for index in range(2)}
            if set(learned.parked) != wanted:
                problems.append(f"parked {learned.parked}, expected one conflict per offline move")
            for entry, index in zip(learned.parked, range(2), strict=False):
                item = f"moved-{index}"
                head = pc.resolve(OPERATOR, item, entry)
                fields = pc.get(OPERATOR, head).fields
                if fields["ours"] != offline[index].object_id:
                    problems.append(f"{entry} names {fields['ours']}, not the offline move")
            try:
                pc.put(
                    OPERATOR,
                    Draft("note", "after", title="after the flip"),
                    on="main",
                    expected_head=None,
                )
            except LibraryRefused as refused:
                print(f"write after the flip: {refused}")
                if not str(refused).startswith("ref_not_owned:"):
                    problems.append(f"the stale PC refused with {refused}")
            else:
                problems.append("the stale PC still acts as primary")

            synced = sync_since(
                StorePeer(pc),
                StorePeer(server),
                OwnerTable("server" if learned.primary == "server" else "pc"),
                cursor=0,
            )
            print(f"sync pushed {synced.pushed_refs}, alarms {synced.alarms}")
            if synced.pushed_refs:
                problems.append(f"the stale PC pushed {synced.pushed_refs}")
            if not any("library:epoch:pc" in alarm for alarm in synced.alarms):
                problems.append("the sync did not say the PC lost its epoch")
            if server.head("shared", "main") != (theirs.object_id, 1):
                problems.append("the server's main moved")
            for index, done in enumerate(offline):
                if pc.head(f"moved-{index}", "main") != (done.object_id, 1):
                    problems.append(f"the offline move moved-{index} is not on the PC's main")
    finally:
        if not arguments.keep:
            drop(root)
    for problem in problems:
        print(f"  problem: {problem}")
    print(f"P-SPLIT {'FAIL' if problems else 'PASS'}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
