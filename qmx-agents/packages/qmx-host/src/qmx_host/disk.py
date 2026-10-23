"""The per-machine giving-way rule (F22, D-11; Library AD-10).

A machine running out of room gives way in one fixed order, and the Library is last: the price
cache first, because every file in it can be fetched again by fingerprint, then transient blobs,
then the telemetry queue, then fetched cache copies, which the PC may drop at any time but which
were copied over the tailnet. A class is a folder under the machine's home; taking it means
deleting its oldest files until the machine has the room that was asked for.

The floor is the room a machine keeps for itself. It is measured from the machine's own free space
when the host starts, as a twentieth of it, and `disk.floor_gb` raises it: a Settings value he
edits, never a constant of ours. Below it a writer that cannot fit refuses whole with `disk_full`
rather than leaving half a file, and the Library is the last writer to be refused.
"""

from __future__ import annotations

import contextlib
import shutil
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

MIB: Final = 1024 * 1024
GIB: Final = 1024 * MIB
FLOOR_SETTING: Final = "disk.floor_gb"
FLOOR_SHARE: Final = 1 / 20
"""The share of the free space measured at start that a machine keeps: a floor no run can cross."""


@dataclass(frozen=True, slots=True)
class Expendable:
    """One class of data a machine may lose to make room, and the folders it lives in, in the
    order the class itself is taken. Nothing here is the Library's durable copy."""

    name: str
    folders: tuple[str, ...]


EXPENDABLE: Final[tuple[Expendable, ...]] = (
    Expendable("price cache", ("cache/prices",)),
    Expendable("transient blobs", ("library/blobs/transient",)),
    Expendable("telemetry queue", ("queue/telemetry",)),
    Expendable("fetched cache copies", ("library/blobs/fetched",)),
)
"""The giving-way order, first to last (F22). The Library's durable objects are not in it: they
leave only by replication (Library AD-10)."""


def free_bytes(at: Path) -> int:
    """The room left on the volume that holds `at`."""
    return shutil.disk_usage(at).free


def floor_bytes(settings: Mapping[str, object], free: int) -> int:
    """The room this machine keeps: `disk.floor_gb` when he raised it, else a twentieth of the
    free space measured now (D-11, Appendix D)."""
    raised = settings.get(FLOOR_SETTING)
    if isinstance(raised, int | float) and not isinstance(raised, bool) and raised > 0:
        return int(raised * GIB)
    return int(free * FLOOR_SHARE)


def clear(folder: Path, want: int) -> int:
    """Delete the oldest files under one expendable folder until it has given `want` bytes back.

    Returns the bytes it took. A file that cannot be deleted is left and the next one is tried, so
    one held handle never stops a machine from making room.
    """
    if want <= 0 or not folder.is_dir():
        return 0
    freed = 0
    for path in sorted(
        (found for found in folder.rglob("*") if found.is_file()),
        key=lambda found: found.stat().st_mtime,
    ):
        if freed >= want:
            break
        with contextlib.suppress(OSError):
            size = path.stat().st_size
            path.unlink()
            freed += size
    return freed


def give_way(
    root: Path,
    need: int,
    *,
    free: Callable[[], int] | None = None,
    rows: Sequence[Expendable] = EXPENDABLE,
) -> tuple[str, ...]:
    """Take classes in table order until `free()` says the machine has `need` bytes.

    Returns the classes it took, in the order it took them, which is the log line P-DISKFULL
    reads. Nothing is taken when the room is already there, and a machine whose classes are all
    empty returns them anyway: what is left is that there was nothing to give.
    """
    reading = free or (lambda: free_bytes(root))
    if reading() >= need:
        return ()
    taken: list[str] = []
    for row in rows:
        for name in row.folders:
            clear(root / name, need - reading())
        taken.append(row.name)
        if reading() >= need:
            break
    return tuple(taken)
