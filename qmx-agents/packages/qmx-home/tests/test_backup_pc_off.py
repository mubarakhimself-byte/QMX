"""This PC's copies switched off (design 06 section 5): the round stages its copy in
`cache/sync-staging/<stamp>/`, sends it, and removes the staging; a killed send's staging goes at
the next round; and a keeping row this QMX cannot open reads its one line."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from backup_fixtures import filled_folder, folder

from qmx_home import Label, Layout
from qmx_home.backup.plan import PC_POLICY, Plan, Storage, parse
from qmx_home.backup.repository import FolderRepository
from qmx_home.backup.round import copy_round, run_round, send

NOW = datetime(2026, 10, 27, 3, 0, tzinfo=UTC)


class Killed(BaseException):
    """A stop in the middle of a step, as a killed process stops."""


def staging(layout: Layout) -> list[str]:
    folder = layout.cache / "sync-staging"
    return sorted(p.name for p in folder.iterdir()) if folder.is_dir() else []


def test_with_this_pcs_copies_off_a_storage_gets_a_whole_copy_and_this_pc_none(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3, secrets=False)
    plan = Plan(pc=replace(PC_POLICY, on=False), storages=(folder(tmp_path / "usb"),))

    report = run_round(filled.layout, plan, now=NOW, floor=0)

    home_id = Label.parse(filled.layout.label.read_text(encoding="utf-8")).home_id
    usb = FolderRepository(tmp_path / "usb" / "QMX-backup" / home_id)
    copy = usb.manifest(usb.copies()[-1])
    assert [(p.id, p.result) for p in report.places] == [("quick", "skipped"), ("usb", "copied")]
    assert report.places[0].line == (
        "copies on this PC are off in Settings, so the copy went only to your storages"
    )
    assert not (filled.layout.backups / "quick" / "snapshots").exists()
    assert {e.path for e in copy.entries} >= set(filled.written_once)
    assert staging(filled.layout) == []


def test_a_staging_left_by_a_killed_send_is_emptied_by_the_next_round(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3, secrets=False)
    plan = Plan(pc=replace(PC_POLICY, on=False), storages=(folder(tmp_path / "usb"),))
    real = FolderRepository._step  # pyright: ignore[reportPrivateUsage]

    def step(self: FolderRepository, op: str) -> None:
        if "usb" in str(self.root) and op == "manifest":
            raise Killed
        real(self, op)

    report, pinned = copy_round(filled.layout, plan, now=NOW, floor=0)
    assert pinned is not None
    with monkeypatch.context() as patched:
        patched.setattr(FolderRepository, "_step", step)
        with pytest.raises(Killed):
            send(filled.layout, plan, "usb", pinned.stamp)
    left = staging(filled.layout)
    later, _ = copy_round(filled.layout, plan, now=NOW + timedelta(hours=1), floor=0)

    assert report.places[0].result == "skipped"
    assert left == [pinned.stamp]
    assert pinned.stamp not in staging(filled.layout)
    assert later.places[0].result == "skipped"


def test_a_keeping_row_this_qmx_cannot_open_reads_one_line_and_the_folder_storage_copies(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3, secrets=False)
    engine = {
        "placement": {
            "usb": {"id": "usb", "via": "folder", "can": ["keep"], "path": str(tmp_path / "usb")},
            "myserver": {"id": "srv", "via": "ssh", "can": ["keep"], "host": "myserver"},
        }
    }
    plan = parse({}, filled.layout, engine)

    report = run_round(filled.layout, plan, now=NOW, floor=0)

    assert [s.id for s in plan.sending] == ["usb"]
    assert plan.not_set_up == (Storage("srv", "myserver", "ssh", None, root="QMX-backup"),)
    assert [(p.id, p.result) for p in report.places] == [
        ("quick", "copied"),
        ("usb", "copied"),
        ("srv", "skipped"),
    ]
    assert report.places[2].line == (
        "myserver is not set up as a storage this QMX can copy to (via 'ssh'); connect it again "
        "in Settings, Sync to my storage"
    )
