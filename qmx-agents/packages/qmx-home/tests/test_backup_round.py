"""A backup round (design 62 C2): the quick undo and a folder target, a round with nothing new,
room, a killed round, the fork guard and the sealed key copy. Every folder and every target is
in pytest's tmp folder."""

from __future__ import annotations

import json
import platform
import shutil
from datetime import UTC, datetime, time, timedelta, timezone
from pathlib import Path

import pytest
from backup_fixtures import SECRETS, filled_folder

from qmx_home import Label, Layout
from qmx_home.backup import repository
from qmx_home.backup.plan import Plan, Target
from qmx_home.backup.repository import FolderRepository
from qmx_home.backup.round import carry_on, due, quick, run_round
from qmx_home.files import Busy, hold, sha256_of
from qmx_home.versions import log_lines

NOW = datetime(2026, 10, 27, 3, 0, tzinfo=UTC)
GIB = 1 << 30


def target(tmp_path: Path, ident: str = "usb") -> Target:
    return Target(ident, "folder", tmp_path / "usb" / "QMX-backup")


def place(layout: Layout, tmp_path: Path) -> FolderRepository:
    home_id = Label.parse(layout.label.read_text(encoding="utf-8")).home_id
    return FolderRepository(tmp_path / "usb" / "QMX-backup" / home_id)


def files_under(folder: Path) -> list[str]:
    return sorted(str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file())


def test_a_round_copies_to_the_quick_undo_and_the_target_and_a_second_copies_nothing(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX")
    plan = Plan(targets=(target(tmp_path),))

    first = run_round(filled.layout, plan, now=NOW, floor=0)
    usb = place(filled.layout, tmp_path)
    quick_files = files_under(filled.layout.backups / "quick")
    usb_files = files_under(usb.root)
    second = run_round(filled.layout, plan, now=NOW + timedelta(days=1), floor=0)

    assert [(p.id, p.result) for p in first.places] == [("quick", "copied"), ("usb", "copied")]
    stamp = "20261027T030000000000Z"
    assert (filled.layout.backups / "quick" / "snapshots" / stamp / "manifest.jsonl").is_file()
    assert (usb.root / "snapshots" / stamp / "manifest.jsonl").is_file()
    copied = usb.manifest(stamp)
    assert len(copied.entries) == 67
    assert {e.at for e in copied.entries} == {"pool"}
    for entry in copied.entries:
        assert sha256_of(usb.pool_path(entry.sha256)) == entry.sha256
    assert not {e.path for e in copied.entries} & set(SECRETS)
    assert usb.about() == {
        "home_id": usb.root.name,
        "folder": str(filled.layout.root),
        "last_copy": stamp,
        "written_by": "0.1.0",
    }
    assert [(p.id, p.result) for p in second.places] == [
        ("quick", "unchanged"),
        ("usb", "unchanged"),
    ]
    assert second.result == "unchanged"
    assert (files_under(filled.layout.backups / "quick"), files_under(usb.root)) == (
        quick_files,
        usb_files,
    )
    assert [line["result"] for line in log_lines(filled.layout)] == ["copied", "unchanged"]


def test_a_changed_file_pools_only_itself_and_the_keep_rule_runs_after_the_new_copy(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=5)
    plan = Plan(targets=(target(tmp_path),))
    run_round(filled.layout, plan, now=NOW, floor=0)
    usb = place(filled.layout, tmp_path)
    pooled = len(files_under(usb.pool))
    (filled.layout.data / "chats" / "c1.json").write_bytes(b'{"title": "renamed"}')

    later = run_round(filled.layout, plan, now=NOW + timedelta(days=1), floor=0)

    assert [p.files for p in later.places] == [1, 1]
    assert len(files_under(usb.pool)) == pooled + 1
    assert usb.copies() == ("20261027T030000000000Z", "20261028T030000000000Z")


@pytest.mark.parametrize(
    ("last", "now", "every", "expected"),
    [
        (None, "2026-10-27T10:00", "day", True),
        ("2026-10-27T03:00", "2026-10-27T23:59", "day", False),
        ("2026-10-27T03:00", "2026-10-28T03:00", "day", True),
        ("2026-10-20T03:00", "2026-10-27T09:00", "day", True),
        ("2026-10-27T09:30", "2026-10-27T10:29", "hour", False),
        ("2026-10-27T09:30", "2026-10-27T10:30", "hour", True),
        ("2026-10-26T03:00", "2026-11-01T23:00", "week", False),
        ("2026-10-26T03:00", "2026-11-02T03:00", "week", True),
        ("2026-10-26T09:00", "2026-11-02T03:00", "week", True),
    ],
)
def test_due_answers_for_hour_day_and_week_across_a_pc_that_was_off(
    last: str | None, now: str, every: str, expected: bool
) -> None:
    zone = timezone(timedelta(hours=2))

    def local(text: str) -> datetime:
        return datetime.fromisoformat(text).replace(tzinfo=zone)

    found = due(None if last is None else local(last), local(now), every, time(3, 0))  # type: ignore[arg-type]
    assert found is expected


def test_a_target_with_too_little_room_refuses_whole_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=5)
    usb_drive = tmp_path / "usb"
    real = repository.free_bytes

    def free(path: Path) -> int:
        return 1000 if path.is_relative_to(usb_drive) else real(path)

    monkeypatch.setattr(repository, "free_bytes", free)

    report = run_round(filled.layout, Plan(targets=(target(tmp_path),)), now=NOW, floor=0)

    usb = report.places[1]
    assert (usb.result, usb.files) == ("refused", 0)
    assert usb.line.startswith(f"{usb.where} needs ")
    assert usb.line.endswith(
        "MB free; nothing was written there. Free some space on it, or name another place in "
        "Settings"
    )
    assert not usb_drive.exists() or files_under(usb_drive) == []


def test_the_quick_undo_refuses_below_the_hosts_floor_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=5)

    def free(_path: Path) -> int:
        return 3 * GIB

    monkeypatch.setattr(repository, "free_bytes", free)

    report = run_round(filled.layout, Plan(targets=(target(tmp_path),)), now=NOW, floor=3 * GIB)

    assert [(p.id, p.result) for p in report.places] == [("quick", "refused"), ("usb", "skipped")]
    assert report.places[0].line.endswith(
        "MB free; QMX keeps at least 3,072 MB free there so QMX itself never runs out of room. "
        "Free some space; the next round tries again"
    )
    assert files_under(filled.layout.backups) == ["backups.jsonl", "backups.lock"]


def test_a_killed_rounds_leftovers_are_removed_by_the_next_round(tmp_path: Path) -> None:
    filled = filled_folder(tmp_path / "QMX", files=5)
    plan = Plan(targets=(target(tmp_path),))
    run_round(filled.layout, plan, now=NOW, floor=0)
    usb = place(filled.layout, tmp_path)
    for where in (filled.layout.backups / "quick", usb.root):
        (where / "pool" / "0f0f.qmx-copying").write_bytes(b"cut short")
        (where / "snapshots" / "20261027T040000000000Z").mkdir()
        (where / "snapshots" / "20261027T040000000000Z" / "manifest.jsonl.new").write_bytes(b"{")
    (filled.layout.data / "settings.toml").write_bytes(b"[engine]\n")

    report = run_round(filled.layout, plan, now=NOW + timedelta(days=1), floor=0)

    assert report.result == "copied"
    for where in (filled.layout.backups / "quick", usb.root):
        names = files_under(where)
        assert not [n for n in names if n.endswith((".qmx-copying", ".new"))]
        assert sorted(p.name for p in (where / "snapshots").iterdir()) == [
            "20261027T030000000000Z",
            "20261028T030000000000Z",
        ]


def test_a_place_another_folder_wrote_to_or_a_missing_backup_toml_is_refused_until_carry_on(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=5)
    twin_root = tmp_path / "twin"
    shutil.copytree(filled.layout.root, twin_root)
    (twin_root / "backups" / "backups.jsonl").unlink(missing_ok=True)
    shutil.rmtree(twin_root / "backups" / "quick", ignore_errors=True)
    twin = Layout(twin_root)
    plan = Plan(targets=(target(tmp_path),))
    run_round(filled.layout, plan, now=NOW, floor=0)
    (twin.data / "chats" / "c1.json").write_bytes(b'{"title": "the twin"}')

    forked = run_round(twin, plan, now=NOW + timedelta(hours=1), floor=0)
    carry_on(twin, plan.targets[0])
    after = run_round(twin, plan, now=NOW + timedelta(hours=2), floor=0)
    usb = place(filled.layout, tmp_path)
    (usb.root / "backup.toml").unlink()
    other_disk = run_round(twin, plan, now=NOW + timedelta(days=2), floor=0)
    carry_on(twin, plan.targets[0])
    again = run_round(twin, plan, now=NOW + timedelta(days=3), floor=0)

    assert forked.places[1].result == "refused"
    assert forked.places[1].line == (
        f"{usb.where} holds a copy another QMX folder made since this one last sent there: the "
        f"newest, 20261027T030000000000Z, is from {platform.node()} ({filled.layout.root}). "
        "Carry on to keep sending this "
        "folder's copies there, or name another place"
    )
    assert after.places[1].result == "copied"
    assert other_disk.places[1].line == (
        f"{usb.where} is not the place QMX copied to before: its backup.toml is missing, so this "
        "may be another disk on the same drive letter. Plug in the disk QMX copied to, or carry "
        "on to copy there anyway"
    )
    assert again.places[1].result in ("copied", "unchanged")
    assert (usb.root / "backup.toml").is_file()


def test_the_sealed_key_copy_lands_beside_a_target_copy_only_and_a_new_digest_makes_a_copy(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=5)
    plan = Plan(targets=(target(tmp_path),))
    sealed = [(b'{"sealed": 1}', "digest-1")]

    first = run_round(filled.layout, plan, now=NOW, floor=0, sealed_keys=lambda: sealed[0])
    sealed[0] = (b'{"sealed": 2}', "digest-2")
    second = run_round(
        filled.layout, plan, now=NOW + timedelta(days=1), floor=0, sealed_keys=lambda: sealed[0]
    )

    usb = place(filled.layout, tmp_path)
    assert [p.result for p in first.places] == ["copied", "copied"]
    assert [p.result for p in second.places] == ["unchanged", "copied"]
    newest = usb.copies()[-1]
    assert usb.read_extra(newest, "keys.sealed.json") == b'{"sealed": 2}'
    assert usb.manifest(newest).header["keys"] == "digest-2"
    assert not list((filled.layout.backups / "quick").rglob("keys.sealed.json"))


def test_a_torn_manifest_stops_the_sweep_and_is_never_thinned(tmp_path: Path) -> None:
    filled = filled_folder(tmp_path / "QMX", files=5)
    keep_one = Target("usb", "folder", tmp_path / "usb" / "QMX-backup", every="hour")
    from dataclasses import replace

    from qmx_home.backup.plan import Keep

    plan = Plan(targets=(replace(keep_one, keep=Keep(days=1)),))
    run_round(filled.layout, plan, now=NOW, floor=0)
    usb = place(filled.layout, tmp_path)
    torn = usb.root / "snapshots" / "20261027T030000000000Z" / "manifest.jsonl"
    torn.write_bytes(torn.read_bytes()[:-40])
    pooled = files_under(usb.pool)
    (filled.layout.data / "chats" / "c1.json").write_bytes(b'{"title": "changed"}')

    report = run_round(filled.layout, plan, now=NOW + timedelta(hours=1), floor=0)

    assert report.places[1].line.endswith(
        f"the copy {usb.root / 'snapshots' / '20261027T030000000000Z'} is damaged: its list of "
        f"files is not whole; QMX removes no file from {usb.where} until it is"
    )
    assert torn.is_file()
    assert set(pooled) <= set(files_under(usb.pool))


def test_a_round_is_refused_while_another_holds_the_lock_and_quick_copies_at_once(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=5)
    with hold(filled.layout.backups / "backups.lock", "held by the test"), pytest.raises(Busy):
        run_round(filled.layout, Plan(), now=NOW, floor=0)
    run_round(filled.layout, Plan(), now=NOW, floor=0)

    before = quick(filled.layout, "before-upgrade", floor=0, now=NOW + timedelta(minutes=5))

    assert before.places[0].result == "copied"
    newest = FolderRepository(filled.layout.backups / "quick").copies()[-1]
    manifest = FolderRepository(filled.layout.backups / "quick").manifest(newest)
    assert manifest.header["why"] == "before-upgrade"
    assert json.loads(json.dumps(manifest.header["format"])) == "qmx-backup/1"
