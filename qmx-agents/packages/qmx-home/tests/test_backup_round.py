"""A backup round (design 62 C2): the quick undo and a folder target, a round with nothing new,
room, a killed round and the fork guard. Every folder and every target is
in pytest's tmp folder."""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
from datetime import UTC, datetime, time, timedelta, timezone
from pathlib import Path
from typing import IO

import pytest
from backup_fixtures import SECRETS, filled_folder, folder, stored, stored_bytes

from qmx_home import Label, Layout
from qmx_home.backup import repository
from qmx_home.backup.plan import Plan, Storage, span
from qmx_home.backup.repository import FolderRepository
from qmx_home.backup.round import carry_on, due, quick, run_round
from qmx_home.files import Busy, hold
from qmx_home.versions import log_lines

NOW = datetime(2026, 10, 27, 3, 0, tzinfo=UTC)
GIB = 1 << 30


def target(tmp_path: Path, ident: str = "usb") -> Storage:
    return folder(tmp_path / "usb" / "QMX-backup", ident)


def place(layout: Layout, tmp_path: Path) -> FolderRepository:
    home_id = Label.parse(layout.label.read_text(encoding="utf-8")).home_id
    return FolderRepository(tmp_path / "usb" / "QMX-backup" / home_id)


def files_under(folder: Path) -> list[str]:
    return sorted(str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file())


def test_a_round_copies_to_the_quick_undo_and_the_target_and_a_second_copies_nothing(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX")
    plan = Plan(storages=(target(tmp_path),))

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
    assert len(copied.entries) == 65
    assert {e.at for e in copied.entries} == {"pool"}
    for entry in copied.entries:
        assert hashlib.sha256(stored_bytes(usb, entry.sha256, tmp_path / "back")).hexdigest() == (
            entry.sha256
        )
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
    assert [(line["kind"], line.get("result")) for line in log_lines(filled.layout)] == [
        ("round", "copied"),
        ("sent", None),
        ("round", "copied"),
        ("round", "unchanged"),
        ("round", "unchanged"),
    ]


def test_a_changed_file_pools_only_itself_and_the_keep_rule_runs_after_the_new_copy(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=5)
    plan = Plan(storages=(target(tmp_path),))
    run_round(filled.layout, plan, now=NOW, floor=0)
    usb = place(filled.layout, tmp_path)
    pooled = len(stored(usb))
    (filled.layout.data / "chats" / "c1.json").write_bytes(b'{"title": "renamed"}')

    later = run_round(filled.layout, plan, now=NOW + timedelta(days=1), floor=0)

    assert [p.files for p in later.places] == [1, 1]
    assert len(stored(usb)) == pooled + 1
    assert usb.copies() == ("20261027T030000000000Z", "20261028T030000000000Z")


@pytest.mark.parametrize(
    ("last", "now", "every", "expected"),
    [
        (None, "2026-10-27T10:00", "1d", True),
        ("2026-10-27T03:00", "2026-10-27T23:59", "1d", False),
        ("2026-10-27T03:00", "2026-10-28T03:00", "1d", True),
        ("2026-10-20T03:00", "2026-10-27T09:00", "1d", True),
        ("2026-10-27T09:30", "2026-10-27T10:29", "1h", False),
        ("2026-10-27T09:30", "2026-10-27T10:30", "1h", True),
        ("2026-10-27T09:30", "2026-10-27T11:29", "2h", False),
        ("2026-10-27T09:30", "2026-10-27T11:30", "2h", True),
        ("2026-10-26T03:00", "2026-11-01T23:00", "1w", False),
        ("2026-10-26T03:00", "2026-11-02T03:00", "1w", True),
        ("2026-10-26T09:00", "2026-11-02T03:00", "1w", True),
    ],
)
def test_due_answers_for_hour_day_and_week_across_a_pc_that_was_off(
    last: str | None, now: str, every: str, expected: bool
) -> None:
    zone = timezone(timedelta(hours=2))

    def local(text: str) -> datetime:
        return datetime.fromisoformat(text).replace(tzinfo=zone)

    found = due(None if last is None else local(last), local(now), span(every), time(3, 0))
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

    report = run_round(filled.layout, Plan(storages=(target(tmp_path),)), now=NOW, floor=0)

    usb = report.places[1]
    assert (usb.result, usb.files) == ("refused", 0)
    assert usb.line.startswith(f"{usb.where} needs ")
    assert "MB free there, so nothing was written. The biggest part of what it keeps is " in (
        usb.line
    )
    assert usb.line.endswith(
        "free some space there, stop sending that to it in Settings, or connect another storage"
    )
    assert not usb_drive.exists() or files_under(usb_drive) == []


def test_the_quick_undo_refuses_below_the_hosts_floor_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=5)

    def free(_path: Path) -> int:
        return 3 * GIB

    monkeypatch.setattr(repository, "free_bytes", free)

    report = run_round(filled.layout, Plan(storages=(target(tmp_path),)), now=NOW, floor=3 * GIB)

    assert [(p.id, p.result) for p in report.places] == [("quick", "refused"), ("usb", "skipped")]
    assert report.places[0].line.endswith(
        "MB free; QMX keeps at least 3,072 MB free there so QMX itself never runs out of room. "
        "Free some space; the next round tries again"
    )
    assert files_under(filled.layout.backups) == ["backups.jsonl", "backups.lock"]


def test_a_killed_rounds_leftovers_are_removed_by_the_next_round(tmp_path: Path) -> None:
    filled = filled_folder(tmp_path / "QMX", files=5)
    plan = Plan(storages=(target(tmp_path),))
    run_round(filled.layout, plan, now=NOW, floor=0)
    usb = place(filled.layout, tmp_path)
    for where in (filled.layout.backups / "quick", usb.root):
        (where / "pool").mkdir(exist_ok=True)
        (where / "pool" / "0f0f.qmx-copying").write_bytes(b"cut short")
        (where / "packs" / "1f1f.pack.qmx-copying").write_bytes(b"cut short")
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
    plan = Plan(storages=(target(tmp_path),))
    run_round(filled.layout, plan, now=NOW, floor=0)
    (twin.data / "chats" / "c1.json").write_bytes(b'{"title": "the twin"}')

    forked = run_round(twin, plan, now=NOW + timedelta(hours=1), floor=0)
    carry_on(twin, plan.storages[0])
    after = run_round(twin, plan, now=NOW + timedelta(hours=2), floor=0)
    usb = place(filled.layout, tmp_path)
    (usb.root / "backup.toml").unlink()
    other_disk = run_round(twin, plan, now=NOW + timedelta(days=2), floor=0)
    carry_on(twin, plan.storages[0])
    again = run_round(twin, plan, now=NOW + timedelta(days=3), floor=0)

    assert forked.places[1].result == "refused"
    assert forked.places[1].line == (
        f"{usb.where} holds a copy another QMX folder made since this one last sent there: the "
        f"newest, 20261027T030000000000Z, is from {platform.node()} ({filled.layout.root}). "
        "Carry on to keep sending this "
        "folder's copies there, or pick another storage"
    )
    assert after.places[1].result == "copied"
    assert other_disk.places[1].line == (
        f"{usb.where} is not the place QMX copied to before: its backup.toml is missing, so this "
        "may be another disk on the same drive letter. Plug in the disk QMX copied to, or carry "
        "on to copy there anyway"
    )
    assert again.places[1].result in ("copied", "unchanged")
    assert (usb.root / "backup.toml").is_file()


def test_a_torn_manifest_stops_the_sweep_and_is_never_thinned(tmp_path: Path) -> None:
    filled = filled_folder(tmp_path / "QMX", files=5)
    from qmx_home.backup.plan import Keep

    hourly = folder(tmp_path / "usb" / "QMX-backup", every="1h", keep=Keep(days=1))
    plan = Plan(storages=(hourly,))
    run_round(filled.layout, plan, now=NOW, floor=0)
    usb = place(filled.layout, tmp_path)
    torn = usb.root / "snapshots" / "20261027T030000000000Z" / "manifest.jsonl"
    torn.write_bytes(torn.read_bytes()[:-40])
    pooled = stored(usb)
    (filled.layout.data / "chats" / "c1.json").write_bytes(b'{"title": "changed"}')

    report = run_round(filled.layout, plan, now=NOW + timedelta(hours=1), floor=0)

    assert report.places[1].line.endswith(
        f"the copy {usb.root / 'snapshots' / '20261027T030000000000Z'} is damaged: its list of "
        f"files is not whole; QMX removes no file from {usb.where} until it is"
    )
    assert torn.is_file()
    assert pooled <= stored(usb)


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
    assert json.loads(json.dumps(manifest.header["format"])) == "qmx-backup/2"


def test_a_damaged_blob_is_left_out_of_a_target_copy_by_name_and_the_rest_is_sent(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=5)
    blob = filled.layout.data / filled.written_once[0]
    blob.write_bytes(b"damaged on his disk")

    report = run_round(filled.layout, Plan(storages=(target(tmp_path),)), now=NOW, floor=0)

    usb = place(filled.layout, tmp_path)
    assert [p.result for p in report.places] == ["copied", "copied"]
    assert report.places[1].line.endswith(
        f"; this copy lacks 1 file: {filled.written_once[0]} (it does not hold the bytes its name "
        "says: it changed while it was copied, or it is damaged)"
    )
    copied = usb.manifest(usb.copies()[-1])
    assert copied.header["partial"] is True
    assert filled.written_once[0] not in {e.path for e in copied.entries}
    assert len(copied.entries) == 29
    assert log_lines(filled.layout)[-1]["places"][0]["partial"] is True  # type: ignore[index]


def test_a_round_killed_after_a_targets_copy_is_up_never_refuses_that_target_next_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qmx_home.backup import round as module

    filled = filled_folder(tmp_path / "QMX", files=5)
    plan = Plan(storages=(target(tmp_path),))

    def killed(*_args: object) -> str:
        raise KeyboardInterrupt

    with monkeypatch.context() as patched:
        patched.setattr(module, "_thin", killed)
        with pytest.raises(KeyboardInterrupt):
            run_round(filled.layout, plan, now=NOW, floor=0)
    (filled.layout.data / "chats" / "c1.json").write_bytes(b'{"title": "after the kill"}')

    report = run_round(filled.layout, plan, now=NOW + timedelta(days=1), floor=0)

    assert [p.result for p in report.places] == ["copied", "copied"]


def test_a_copy_that_landed_reads_copied_when_tidying_the_storage_after_it_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=5)
    plan = Plan(storages=(target(tmp_path),))
    real = FolderRepository.sweep

    def unplugged(self: FolderRepository, **kwargs: object) -> object:
        if "usb" in str(self.root):
            raise OSError(5, "Access is denied")
        return real(self, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(FolderRepository, "sweep", unplugged)
    report = run_round(filled.layout, plan, now=NOW, floor=0)
    usb = place(filled.layout, tmp_path)

    assert report.places[-1].result == "copied"
    assert report.places[-1].line.endswith(
        f"; tidying {usb.where} after the copy stopped (Access is denied); the next round tries "
        "again"
    )
    assert usb.copies() == ("20261027T030000000000Z",)


def test_every_file_a_target_copy_names_is_written_through_to_the_disk_before_its_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qmx_home import files

    filled = filled_folder(tmp_path / "QMX", files=5)
    events: list[tuple[str, str]] = []
    real_new, real_replace = files.create_new, repository.os.replace

    def created(path: Path, *, through: bool = True) -> IO[bytes]:
        events.append(("durable", files.plain(path)))
        return real_new(path, through=through)

    def renamed(source: object, target: object) -> None:
        events.append(("rename", f"{files.plain(source)} -> {files.plain(target)}"))
        real_replace(source, target)  # type: ignore[arg-type]

    monkeypatch.setattr(files, "create_new", created)
    monkeypatch.setattr(repository.os, "replace", renamed)

    run_round(filled.layout, Plan(storages=(target(tmp_path),)), now=NOW, floor=0)

    usb = place(filled.layout, tmp_path)
    manifest_at = next(
        i
        for i, (kind, what) in enumerate(events)
        if kind == "rename" and what.endswith("manifest.jsonl") and str(usb.root) in what
    )
    durable = {what for kind, what in events[:manifest_at] if kind == "durable"}
    placed = [
        what.partition(" -> ")[0]
        for kind, what in events[:manifest_at]
        if kind == "rename"
        and str(usb.root) in what.partition(" -> ")[2]
        and ("packs" in what or "index" in what)
    ]
    assert len([p for p in placed if "index" in p]) >= 1
    assert len([p for p in placed if "packs" in p]) >= 1
    assert set(placed) <= durable


def test_a_copy_missing_a_file_is_partial_and_the_newest_whole_copy_is_never_thinned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from dataclasses import replace

    from qmx_home.backup import snapshot
    from qmx_home.backup.plan import Keep

    filled = filled_folder(tmp_path / "QMX", files=5)
    hourly = folder(tmp_path / "usb" / "QMX-backup", every="1h", keep=Keep(hours=1))
    plan = Plan(pc=replace(Plan().pc, keep=Keep(hours=1)), storages=(hourly,))
    run_round(filled.layout, plan, now=NOW, floor=0)
    real = snapshot.copy_file

    def held_open(source: Path, target: Path, **kwargs: object) -> str:
        if source.name == "settings.toml":
            raise PermissionError(13, "The process cannot access the file", str(source))
        return real(source, target, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(snapshot, "copy_file", held_open)
    for hours in (1, 2):
        (filled.layout.data / "settings.toml").write_bytes(f"[engine]\nround = {hours}\n".encode())
        (filled.layout.data / "chats" / "c1.json").write_bytes(f'{{"n": {hours}}}'.encode())
        report = run_round(filled.layout, plan, now=NOW + timedelta(hours=hours), floor=0)

    whole = "20261027T030000000000Z"
    quick_repo = FolderRepository(filled.layout.backups / "quick")
    usb = place(filled.layout, tmp_path)
    assert quick_repo.copies() == (whole, "20261027T050000000000Z")
    assert usb.copies() == (whole, "20261027T050000000000Z")
    newest = quick_repo.manifest(quick_repo.copies()[-1])
    settings = filled.layout.data / "settings.toml"
    assert (newest.header["partial"], newest.header["unread"]) == (
        True,
        [f"settings.toml (The process cannot access the file: {settings})"],
    )
    assert report.places[0].line.endswith(
        f"; this copy lacks 1 file: settings.toml (The process cannot access the file: "
        f"{filled.layout.data / 'settings.toml'})"
    )
    assert usb.manifest(usb.copies()[-1]).header["partial"] is True
