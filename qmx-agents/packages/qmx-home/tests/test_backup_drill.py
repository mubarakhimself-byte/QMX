"""The restore drill (design 62 C3, guard L2): it restores a sample of one copy into
`cache/restore-drill/`, checks it, removes the folder and never touches `data/`; a damaged pooled
file is deleted so the next round pools it again. Every folder and target is in pytest's tmp
folder."""

from __future__ import annotations

import os
import random
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from backup_fixtures import filled_folder, folder

from qmx_home import Label, Layout
from qmx_home.backup import restore
from qmx_home.backup.plan import Plan
from qmx_home.backup.repository import FolderRepository, Manifest, Unreadable
from qmx_home.backup.round import run_round
from qmx_home.files import long_path, sha256_of
from qmx_home.versions import log_lines

NOW = datetime(2026, 10, 27, 3, 0, tzinfo=UTC)


def copied(tmp_path: Path) -> tuple[Layout, Plan, FolderRepository]:
    filled = filled_folder(tmp_path / "QMX", files=4, secrets=False)
    plan = Plan(storages=(folder(tmp_path / "usb"),))
    run_round(filled.layout, plan, now=NOW, floor=0)
    home_id = Label.parse(filled.layout.label.read_text(encoding="utf-8")).home_id
    return filled.layout, plan, FolderRepository(tmp_path / "usb" / "QMX-backup" / home_id)


def data_hashes(layout: Layout) -> dict[str, str]:
    found: dict[str, str] = {}
    for where, _, names in os.walk(long_path(layout.data)):
        for name in names:
            path = Path(where, name)
            found[path.relative_to(long_path(layout.data)).as_posix()] = sha256_of(path)
    return found


def whole(place: FolderRepository, stamp: str) -> bool:
    entries = place.manifest(stamp).entries
    return all(
        place.pool_has(e.sha256) and sha256_of(place.pool_path(e.sha256)) == e.sha256
        for e in entries
    )


def test_the_drill_passes_on_a_good_copy_and_leaves_data_and_its_folder_as_they_were(
    tmp_path: Path,
) -> None:
    layout, _, place = copied(tmp_path)
    before = data_hashes(layout)
    stamp = place.copies()[-1]
    stores = len([e for e in place.manifest(stamp).entries if e.kind != "once"])

    drilled = restore.drill(layout, place, sample=2, rng=seeded(7), keep_free=0)

    assert (drilled.stamp, drilled.passed, drilled.checked, drilled.damaged) == (
        stamp,
        True,
        stores + 2,
        (),
    )
    assert drilled.line == (
        f"the drill restored {stores + 2} files of the copy {stamp} from {place.where}, and every "
        "one checked"
    )
    assert not (layout.cache / "restore-drill").exists()
    assert data_hashes(layout) == before
    drills = [line for line in log_lines(layout) if line["kind"] == "drill"]
    assert [(d["stamp"], d["passed"]) for d in drills] == [(stamp, True)]


def test_a_damaged_pooled_file_is_deleted_named_and_pooled_again_by_the_next_round(
    tmp_path: Path,
) -> None:
    layout, plan, place = copied(tmp_path)
    stamp = place.copies()[-1]
    chat = next(e for e in place.manifest(stamp).entries if e.path == "chats/c1.json")
    with long_path(place.pool_path(chat.sha256)).open("r+b") as pooled:
        pooled.truncate(3)

    drilled = restore.drill(layout, place, sample=0, rng=seeded(1), keep_free=0)
    report = run_round(layout, plan, now=NOW + timedelta(days=1), floor=0)
    again = restore.drill(layout, place, sample=0, rng=seeded(1), keep_free=0)

    assert drilled.passed is False
    assert drilled.damaged == (
        f"chats/c1.json (damaged in {place.where}, so QMX removed it there; the next round "
        "copies it again)",
    )
    assert report.places[1].result == "copied"
    assert whole(place, stamp)
    assert again.passed is True
    assert not (layout.cache / "restore-drill").exists()


def test_a_drill_without_room_does_not_run_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout, _, place = copied(tmp_path)
    monkeypatch.setattr(restore, "free_bytes", no_room)

    drilled = restore.drill(layout, place, sample=2, rng=seeded(3), keep_free=0)

    assert (drilled.passed, drilled.checked) == (None, 0)
    assert drilled.line.startswith(f"the drill of {place.where} needs ")
    assert not (layout.cache / "restore-drill").exists()
    assert not [line for line in log_lines(layout) if line["kind"] == "drill"]


def no_room(_path: Path) -> int:
    return 0


def seeded(seed: int) -> random.Random:
    """The drill's pick of a copy and a sample, the same on every run."""
    return random.Random(seed)  # noqa: S311


@pytest.mark.parametrize(
    "named",
    [
        "{canary}",
        r"..\..\..\canary.txt",
        "../../../canary.txt",
        "AB" * 32,
        "0" * 63,
    ],
)
def test_a_manifest_hash_that_is_not_a_sha256_is_unreadable_and_names_no_file_outside_the_pool(
    tmp_path: Path, named: str
) -> None:
    layout, _, place = copied(tmp_path)
    canary = tmp_path / "canary.txt"
    canary.write_bytes(b"his file")
    bad = named.format(canary=canary)
    held = place.manifest(place.copies()[-1])
    forged = Manifest(
        {**held.header, "stamp": "20261028T030000000000Z"},
        (replace(held.entries[0], sha256=bad), *held.entries[1:]),
    )
    place.put_copy(forged)

    with pytest.raises(Unreadable, match="20261028T030000000000Z"):
        place.manifest(forged.stamp)
    for number in range(4):
        restore.drill(layout, place, sample=50, rng=seeded(number), keep_free=0)
    with pytest.raises(restore.RestoreRefused):
        restore.stage(layout, place, forged.stamp, keep_free=0)
    with pytest.raises(ValueError, match="not a sha256"):
        place.pool_path(bad)
    with pytest.raises(ValueError, match="not a sha256"):
        place.discard(bad)

    assert canary.read_bytes() == b"his file"
