"""Restoring a copy (design 62 C3 and B4): what a copy offers, what returning to it replaces, and
the checks `stage` makes before anything of the folder changes. Every folder and every target is
in pytest's tmp folder."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from backup_fixtures import filled_folder

from qmx_home.backup import restore
from qmx_home.backup.plan import Plan, Target
from qmx_home.backup.repository import FolderRepository
from qmx_home.backup.round import run_round
from qmx_home.files import sha256_of

NOW = datetime(2026, 10, 27, 3, 0, tzinfo=UTC)
STAMP = "20261027T030000000000Z"


def usb(tmp_path: Path) -> Target:
    return Target("usb", "folder", tmp_path / "usb" / "QMX-backup")


def place_of(report_where: str) -> FolderRepository:
    return FolderRepository(Path(report_where))


def test_a_folder_changed_after_its_copy_comes_back_whole_from_the_target(tmp_path: Path) -> None:
    filled = filled_folder(tmp_path / "QMX", files=5)
    report = run_round(filled.layout, Plan(targets=(usb(tmp_path),)), now=NOW, floor=0)
    target = place_of(report.places[1].where)
    copied = target.manifest(STAMP)
    data = filled.layout.data
    (data / "chats" / "c1.json").write_bytes(b'{"title": "renamed"}')
    (data / "workspaces" / "w" / "file-0001.txt").unlink()

    restore.stage(filled.layout, target, STAMP, keep_free=0)
    restore.finish(filled.layout)

    placed = {e.path: sha256_of(data / e.path) for e in copied.entries}
    assert placed == {e.path: e.sha256 for e in copied.entries}
