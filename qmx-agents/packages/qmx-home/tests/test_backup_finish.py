"""Finishing a staged restore (design 62 C3, Appendix D's locks of a finish): one end state from
every kill point, never under a running host, nothing changed when a rename fails, and the pause
after a restore until he carries on. Every folder and target is in pytest's tmp folder."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import psutil
import pytest
from backup_fixtures import SECRETS, Filled, filled_folder, folder

from qmx_home import Label, Layout, resolve
from qmx_home.backup import restore
from qmx_home.backup.plan import Plan
from qmx_home.backup.repository import FolderRepository
from qmx_home.backup.restore import HostServes, RestoreRefused
from qmx_home.backup.round import run_round
from qmx_home.files import long_path, sha256_of
from qmx_home.versions import log_lines

NOW = datetime(2026, 10, 27, 3, 0, tzinfo=UTC)
LEASE = "locks/demo.lock"


class Killed(BaseException):
    """The process stopping at a step, as a kill or a power cut would."""


def staged(tmp_path: Path) -> tuple[Filled, FolderRepository, str, dict[str, str]]:
    """A folder copied to a USB target, then changed, with that copy staged; and the folder's
    data as it was before the finish."""
    filled = filled_folder(tmp_path / "QMX", files=4)
    report = run_round(filled.layout, Plan(storages=(folder(tmp_path / "usb"),)), now=NOW, floor=0)
    place, stamp = report.places[1], report.places[1].stamp
    assert stamp is not None
    target = FolderRepository(Path(place.where))
    (filled.layout.data / "chats" / "c1.json").write_bytes(b'{"title": "renamed"}')
    (filled.layout.data / "workspaces" / "w" / "file-0000.txt").unlink()
    before = listing(filled.layout.data)
    restore.stage(filled.layout, target, stamp, keep_free=0)
    return filled, target, stamp, before


def listing(folder: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    pending = [long_path(folder)]
    while pending:
        for entry in os.scandir(pending.pop()):
            if entry.is_symlink() or entry.is_junction():
                continue
            if entry.is_dir():
                pending.append(Path(entry.path))
            else:
                found[Path(entry.path).relative_to(long_path(folder)).as_posix()] = sha256_of(
                    Path(entry.path)
                )
    return found


def assert_restored(
    filled: Filled, target: FolderRepository, stamp: str, before: dict[str, str]
) -> None:
    layout = filled.layout
    copied = {e.path: e.sha256 for e in target.manifest(stamp).entries}
    carried = {p: sha256_of(layout.data / p) for p in (*SECRETS, LEASE)}
    assert listing(layout.data) == {**copied, **carried}
    for path in SECRETS:
        assert (layout.data / path).read_bytes() == filled.planted[path]
    asides = list(layout.backups.glob("before-restore-*"))
    assert len(asides) == 1
    assert listing(asides[0] / "data") == before
    assert [line["copy"] for line in log_lines(layout) if line["kind"] == "restored"] == [stamp]
    assert not (layout.backups / "restore.json").exists()
    assert not list(layout.backups.glob("restoring-*"))


@pytest.mark.parametrize("after", [False, True], ids=["before-its-journal", "after-its-journal"])
@pytest.mark.parametrize("step", restore.STEPS[1:])
def test_a_finish_killed_at_any_step_is_completed_by_the_next_with_one_end_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, step: str, after: bool
) -> None:
    filled, target, stamp, before = staged(tmp_path)
    real = restore._journal  # pyright: ignore[reportPrivateUsage]

    def journal(layout: Layout, record: restore._Journal) -> None:  # pyright: ignore[reportPrivateUsage]
        if record.step == step and not after:
            raise Killed
        real(layout, record)
        if record.step == step and after:
            raise Killed

    monkeypatch.setattr(restore, "_journal", journal)
    with pytest.raises(Killed):
        restore.finish(filled.layout)
    monkeypatch.setattr(restore, "_journal", real)

    finished = restore.finish(filled.layout)

    assert finished is not None
    assert_restored(filled, target, stamp, before)
    assert restore.finish(filled.layout) is None


def test_a_finish_refuses_and_renames_nothing_while_another_process_holds_the_engine_lock(
    tmp_path: Path,
) -> None:
    filled, _, stamp, before = staged(tmp_path)
    lock = filled.layout.data / "engine.lock"
    holder = subprocess.Popen(
        [sys.executable, "-I", "-c", HOLD, str(lock)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout is not None
        assert holder.stdout.readline().strip() == "held"
        with pytest.raises(HostServes, match=re.escape(f"QMX is running on {filled.layout.root}")):
            restore.finish(filled.layout)
    finally:
        holder.communicate("")

    assert listing(filled.layout.data) == before
    assert not list(filled.layout.backups.glob("before-restore-*"))
    assert (filled.layout.backups / f"restoring-{stamp}" / "data").is_dir()


HOLD = """
import sys
lock = open(sys.argv[1], "a+b")
if sys.platform == "win32":
    import msvcrt
    lock.seek(0)
    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
else:
    import fcntl
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
print("held", flush=True)
sys.stdin.read()
"""


def test_a_finish_refuses_while_the_folders_record_names_a_live_host_and_not_a_stale_one(
    tmp_path: Path,
) -> None:
    filled, target, stamp, before = staged(tmp_path)
    record = filled.layout.data / "control-process.json"
    me = psutil.Process()
    record.write_text(
        f'{{"pid": {me.pid}, "port": 1, "created": {me.create_time()}}}', encoding="utf-8"
    )

    with pytest.raises(HostServes, match=rf"\(PID {me.pid}\)"):
        restore.finish(filled.layout)
    assert listing(filled.layout.data) == {**before, "control-process.json": sha256_of(record)}

    record.write_text(f'{{"pid": {me.pid}, "port": 1, "created": 1.0}}', encoding="utf-8")
    before = listing(filled.layout.data)
    assert restore.finish(filled.layout) is not None
    assert_restored(filled, target, stamp, before)


@pytest.mark.parametrize("which", ["data", "staged"])
def test_a_rename_that_fails_changes_nothing_and_keeps_the_copy_staged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, which: str
) -> None:
    filled, target, stamp, before = staged(tmp_path)
    real = os.replace
    held = (
        filled.layout.data
        if which == "data"
        else filled.layout.backups / f"restoring-{stamp}" / "data"
    )

    def replace(source: object, destination: object) -> None:
        if Path(str(source)) == long_path(held):
            raise PermissionError(13, "Access is denied", str(source))
        real(source, destination)  # type: ignore[arg-type]

    monkeypatch.setattr(restore.os, "replace", replace)
    with pytest.raises(RestoreRefused, match="a program still has a file in it open") as refused:
        restore.finish(filled.layout)
    monkeypatch.setattr(restore.os, "replace", real)

    assert "nothing changed and the copy stays staged" in str(refused.value)
    assert listing(filled.layout.data) == before
    assert not list(filled.layout.backups.glob("before-restore-*"))
    assert (filled.layout.backups / f"restoring-{stamp}" / "data").is_dir()
    assert restore.finish(filled.layout) is not None
    assert_restored(filled, target, stamp, before)


def test_after_a_restore_sync_and_fires_stay_paused_until_he_carries_on(tmp_path: Path) -> None:
    filled, _, stamp, _ = staged(tmp_path)
    layout = filled.layout
    assert restore.after_restore(layout) is None

    restore.finish(layout)
    first = restore.after_restore(layout)
    restore.paused(layout, False)
    restore.paused(layout, True)
    held = restore.after_restore(layout)
    restore.reindexed(layout)
    restore.carried_on(layout)

    assert first is not None
    assert (first.stamp, first.paused, first.earlier) == (stamp, False, None)
    assert first.aside.startswith("backups/before-restore-")
    assert held is not None
    assert (held.paused, held.earlier) == (True, False)
    assert restore.after_restore(layout) is None
    assert restore.pending_reindex(layout) is None
    assert [line["kind"] for line in log_lines(layout)][-4:] == [
        "restored",
        "restore-paused",
        "reindexed",
        "restore-carried-on",
    ]


def test_a_folder_restored_on_a_new_pc_carries_on_sending_to_the_disk_it_came_from(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3, secrets=False)
    usb = folder(tmp_path / "usb")
    run_round(filled.layout, Plan(storages=(usb,)), now=NOW, floor=0)
    home_id = Label.parse(filled.layout.label.read_text(encoding="utf-8")).home_id
    place = FolderRepository(tmp_path / "usb" / "QMX-backup" / home_id)
    fresh = resolve(tmp_path / "New", create=True)

    restore.stage(fresh, place, place.copies()[-1], keep_free=0)
    restore.finish(fresh)
    (fresh.data / "chats" / "c1.json").write_bytes(b'{"title": "on the new PC"}')
    report = run_round(fresh, Plan(storages=(usb,)), now=datetime.now(UTC), floor=0)

    assert [(p.id, p.result) for p in report.places] == [("quick", "copied"), ("usb", "copied")]


def kill_at(monkeypatch: pytest.MonkeyPatch, step: str, *, after: bool) -> None:
    """Stop the process when the journal records `step`: before the write, or right after."""
    real = restore._journal  # pyright: ignore[reportPrivateUsage]

    def journal(layout: Layout, record: restore._Journal) -> None:  # pyright: ignore[reportPrivateUsage]
        if record.step == step and not after:
            raise Killed
        real(layout, record)
        if record.step == step and after:
            raise Killed

    monkeypatch.setattr(restore, "_journal", journal)


@pytest.mark.parametrize("kill", [None, "before-its-journal", "after-its-journal"])
def test_a_blob_purged_between_stage_and_finish_never_comes_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kill: str | None
) -> None:
    filled, _, _, _ = staged(tmp_path)
    data = filled.layout.data
    blob = next(
        p for p in filled.written_once if p.startswith("library/blobs/") and "/tomb" not in p
    )
    hexdigest = blob.rpartition("/")[2]
    stone = f"library/blobs/tombstones/{hexdigest}.json"
    (data / blob).unlink()
    (data / stone).write_bytes(b'{"reason": "a secret"}')
    if kill is not None:
        kill_at(monkeypatch, "purges", after=kill == "after-its-journal")
        with pytest.raises(Killed):
            restore.finish(filled.layout)
        monkeypatch.undo()

    finished = restore.finish(filled.layout)
    after = restore.after_restore(filled.layout)

    assert finished is not None
    assert not (data / blob).exists()
    assert (data / stone).read_bytes() == b'{"reason": "a secret"}'
    assert finished.purge == (f"sha256:{hexdigest}",)
    assert after is not None
    assert after.purge == (f"sha256:{hexdigest}",)


@pytest.mark.parametrize(
    ("step", "after"),
    [("putting-back", True), ("staged", False)],
    ids=["before-the-rename-back", "after-the-rename-back"],
)
def test_a_finish_killed_while_putting_the_data_back_puts_it_back_at_the_next_finish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, step: str, after: bool
) -> None:
    filled, target, stamp, before = staged(tmp_path)
    layout = filled.layout
    staging = layout.backups / f"restoring-{stamp}" / "data"
    real = os.replace

    def replace(source: object, destination: object) -> None:
        if Path(str(source)) == long_path(staging):
            raise PermissionError(13, "Access is denied", str(source))
        real(source, destination)  # type: ignore[arg-type]

    monkeypatch.setattr(restore.os, "replace", replace)
    kill_at(monkeypatch, step, after=after)
    with pytest.raises(Killed):
        restore.finish(layout)
    monkeypatch.setattr(restore, "_journal", REAL_JOURNAL)

    with pytest.raises(RestoreRefused, match="nothing changed and the copy stays staged"):
        restore.finish(layout)
    assert listing(layout.data) == before
    assert '"step": "staged"' in (layout.backups / "restore.json").read_text(encoding="utf-8")
    assert not list(layout.backups.glob("before-restore-*"))

    monkeypatch.undo()
    assert restore.finish(layout) is not None
    assert_restored(filled, target, stamp, before)


REAL_JOURNAL = restore._journal  # pyright: ignore[reportPrivateUsage]


@pytest.mark.parametrize("after", [False, True], ids=["before-its-journal", "after-its-journal"])
def test_a_new_data_folder_beside_the_set_aside_data_is_refused_and_nothing_is_deleted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, after: bool
) -> None:
    filled, _, stamp, before = staged(tmp_path)
    layout = filled.layout
    kill_at(monkeypatch, "set-aside", after=after)
    with pytest.raises(Killed):
        restore.finish(layout)
    monkeypatch.undo()
    stray = layout.data / "chats" / "new.json"
    stray.parent.mkdir(parents=True)
    stray.write_bytes(b'{"title": "written after the kill"}')
    asides = list(layout.backups.glob("before-restore-*"))

    for _ in range(2):
        with pytest.raises(RestoreRefused, match="changed nothing") as refused:
            restore.finish(layout)
        assert str(layout.data) in str(refused.value)
        assert str(asides[0] / "data") in str(refused.value)

    assert listing(asides[0] / "data") == before
    assert listing(layout.data) == {"chats/new.json": sha256_of(stray)}
    assert (layout.backups / f"restoring-{stamp}" / "data").is_dir()


def test_a_folder_named_like_a_tombstone_is_skipped_with_a_line(tmp_path: Path) -> None:
    filled, target, stamp, before = staged(tmp_path)
    layout = filled.layout
    name = f"{'ab' * 32}.json"
    (layout.data / "library" / "blobs" / "tombstones" / name).mkdir()

    finished = restore.finish(layout)

    assert finished is not None
    assert_restored(filled, target, stamp, before)
    skipped = [line for line in log_lines(layout) if line["kind"] == "restore-skipped"]
    assert [line["path"] for line in skipped] == [f"library/blobs/tombstones/{name}"]


def test_a_cancel_after_a_kill_between_the_set_aside_and_its_journal_puts_the_data_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    filled, _, stamp, before = staged(tmp_path)
    layout = filled.layout
    kill_at(monkeypatch, "set-aside", after=False)
    with pytest.raises(Killed):
        restore.finish(layout)
    monkeypatch.undo()
    assert not layout.data.exists()

    line = restore.cancel(layout)

    assert line.endswith(f"nothing in {layout.root} changed")
    assert listing(layout.data) == before
    assert not list(layout.backups.glob("before-restore-*"))
    assert not (layout.backups / f"restoring-{stamp}").exists()
    assert not (layout.backups / "restore.json").exists()
    assert restore.finish(layout) is None
