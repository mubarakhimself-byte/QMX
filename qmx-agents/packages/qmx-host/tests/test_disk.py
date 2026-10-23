"""The giving-way rule (F22, D-11): one order per machine, and the floor it keeps.

A fake volume is a folder declared at a fixed size, so its free space is that size minus what sits
on it. That is what makes the rule testable without filling a real disk.
"""

from __future__ import annotations

from pathlib import Path

from qmx_host.disk import EXPENDABLE, floor_bytes, give_way

MIB = 1024 * 1024
ORDER = ("price cache", "transient blobs", "telemetry queue", "fetched cache copies")


def volume(tmp_path: Path) -> tuple[Path, int]:
    """A fixed-size volume with one part in every expendable class."""
    root = tmp_path / "volume"
    for row in EXPENDABLE:
        folder = root / row.folders[0]
        folder.mkdir(parents=True)
        (folder / "part.bin").write_bytes(b"\0" * MIB)
    return root, MIB * len(EXPENDABLE)


def free_on(root: Path, total: int) -> int:
    return total - sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def test_the_rule_takes_the_classes_in_the_tables_order(tmp_path: Path) -> None:
    root, total = volume(tmp_path)
    need = free_on(root, total) + 2 * MIB

    taken = give_way(root, need, free=lambda: free_on(root, total))

    assert taken == ORDER[:2]
    assert free_on(root, total) >= need
    assert (root / EXPENDABLE[2].folders[0] / "part.bin").exists()


def test_a_machine_with_room_gives_nothing_away(tmp_path: Path) -> None:
    root, total = volume(tmp_path)

    taken = give_way(root, free_on(root, total) - MIB, free=lambda: free_on(root, total))

    assert taken == ()
    assert free_on(root, total) == total - 4 * MIB


def test_the_floor_is_a_twentieth_of_the_measured_free_space_until_he_raises_it() -> None:
    assert floor_bytes({}, 1_000 * MIB) == 50 * MIB
    assert floor_bytes({"disk.floor_gb": 2}, 1_000 * MIB) == 2 * 1024 * MIB
    assert floor_bytes({"disk.floor_gb": 0}, 1_000 * MIB) == 50 * MIB
