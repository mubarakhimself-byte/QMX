"""Restoring a copy (design 62 C3 and B4): what a copy offers, what returning to it replaces, and
the checks `stage` makes before anything of the folder changes. Every folder and every target is
in pytest's tmp folder."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from backup_fixtures import SECRETS, filled_folder, rows

from qmx_home import Label, Layout, NoQmxFolder, resolve
from qmx_home.backup import restore
from qmx_home.backup.plan import Plan, Target
from qmx_home.backup.repository import FolderRepository, Manifest
from qmx_home.backup.restore import RestoreRefused
from qmx_home.backup.round import quick, run_round
from qmx_home.files import long_path, sha256_of

NOW = datetime(2026, 10, 27, 3, 0, tzinfo=UTC)
STAMP = "20261027T030000000000Z"
LEASE = "locks/demo.lock"
"""A mini app's lease generation, never in a copy and carried over by a restore."""


def usb(tmp_path: Path) -> Target:
    return Target("usb", "folder", tmp_path / "usb" / "QMX-backup")


def sent(layout: Layout, tmp_path: Path, now: datetime = NOW) -> tuple[FolderRepository, str]:
    """A round to the USB target; the place and the copy's stamp."""
    report = run_round(layout, Plan(targets=(usb(tmp_path),)), now=now, floor=0)
    place = report.places[1]
    assert place.stamp is not None
    return FolderRepository(Path(place.where)), place.stamp


def listing(folder: Path) -> dict[str, str]:
    """Every file under `folder` by its path and sha256, never through a link or junction."""
    found: dict[str, str] = {}
    pending = [long_path(folder)]
    while pending:
        for entry in os.scandir(pending.pop()):
            if entry.is_symlink() or entry.is_junction():
                continue
            if entry.is_dir():
                pending.append(Path(entry.path))
            else:
                relative = Path(entry.path).relative_to(long_path(folder)).as_posix()
                found[relative] = sha256_of(Path(entry.path))
    return found


def home_id(layout: Layout) -> str:
    return Label.parse(layout.label.read_text(encoding="utf-8")).home_id


def test_a_restore_into_the_same_folder_brings_back_the_copy_and_sets_the_folder_aside_whole(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=5)
    target, stamp = sent(filled.layout, tmp_path, datetime.now(UTC))
    copied = target.manifest(stamp)
    data = filled.layout.data
    (data / "chats" / "c1.json").write_bytes(b'{"title": "renamed"}')
    (data / "workspaces" / "w" / "file-0001.txt").unlink()
    with (data / "library" / "refs" / "log.jsonl").open("ab") as log:
        log.write(b'\n{"seq": 9, "at": "' + datetime.now(UTC).isoformat().encode() + b'"}\n')
    before = listing(data)
    folder_id = home_id(filled.layout)

    staged = restore.stage(filled.layout, target, stamp, keep_free=0)
    finished = restore.finish(filled.layout)

    assert (staged.newer.chats, staged.newer.ref_moves, staged.newer.runs) == (1, 1, 0)
    assert finished is not None
    placed = listing(data)
    assert {e.path: placed[e.path] for e in copied.entries} == {
        e.path: e.sha256 for e in copied.entries
    }
    for entry in copied.entries:
        if entry.kind == "store":
            assert rows(data / entry.path) == entry.tables
    assert listing(finished.aside / "data") == before
    for path in SECRETS:
        assert (data / path).read_bytes() == filled.planted[path]
    assert (filled.layout.keys / "vault.key").read_bytes() == filled.planted["../keys/vault.key"]
    assert set(placed) == {e.path for e in copied.entries} | set(SECRETS) | {LEASE}
    assert home_id(filled.layout) == folder_id
    assert (finished.aside / "qmx-home.toml").is_file()
    assert not (filled.layout.backups / "restore.json").exists()
    assert not (filled.layout.backups / f"restoring-{stamp}").exists()


def test_newer_than_counts_the_runs_saves_chats_and_price_months_made_after_a_copy(
    tmp_path: Path,
) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    data = layout.data
    (data / "engine").mkdir()
    with closing(sqlite3.connect(data / "engine" / "engine.sqlite")) as db:
        db.execute("CREATE TABLE events (run_id TEXT, seq INTEGER, at TEXT, kind TEXT, data TEXT)")
        db.executemany(
            "INSERT INTO events VALUES (?, ?, ?, ?, '{}')",
            [
                ("r0", 1, "2026-10-27T02:59:59+00:00", "run_created"),
                ("r1", 1, "2026-10-27T03:00:01+00:00", "run_created"),
                ("r1", 2, "2026-10-27T03:00:02+00:00", "node_started"),
                ("r2", 1, "2026-10-27T09:00:00.5+00:00", "run_created"),
            ],
        )
        db.commit()
    refs = data / "library" / "refs"
    refs.mkdir(parents=True)
    moves = ["2026-10-26T10:00:00Z", "2026-10-27T03:30:00Z", "2026-10-28T00:00:00Z"]
    (refs / "log.jsonl").write_text(
        "".join(json.dumps({"seq": n, "at": at}) + "\n" for n, at in enumerate(moves))
        + '{"seq": 9, "at": "2026-10-',
        encoding="utf-8",
    )
    early, late = NOW - timedelta(hours=1), NOW + timedelta(hours=1)
    for name, moment in (("old", early), ("new", late), ("newer", late)):
        chat = data / "chats" / f"{name}.json"
        chat.parent.mkdir(exist_ok=True)
        chat.write_text("{}", encoding="utf-8")
        os.utime(chat, (moment.timestamp(), moment.timestamp()))
    for month, moment in (("2026-09", early), ("2026-10", late)):
        state = data / "market" / "binance" / "btc" / month / "state.json"
        state.parent.mkdir(parents=True)
        state.write_text("{}", encoding="utf-8")
        os.utime(state, (moment.timestamp(), moment.timestamp()))

    newer = restore.newer_than(layout, STAMP)

    assert (newer.runs, newer.ref_moves, newer.chats, newer.price_months) == (2, 2, 2, 1)
    assert newer.line == (
        "since this copy the folder holds 2 runs started, 2 Library saves, 2 chats and 1 price "
        "month"
    )


def test_copies_lists_each_copy_newest_first_and_a_partial_copy_with_the_files_it_lacks(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=5)
    target, first = sent(filled.layout, tmp_path)
    (filled.layout.data / "chats" / "c1.json").write_bytes(b'{"title": "renamed"}')
    _, second = sent(filled.layout, tmp_path, NOW + timedelta(days=1))
    held = target.manifest(second)
    gone = next(e for e in held.entries if e.path == "workspaces/w/file-0002.txt")
    partial = Manifest(
        {**held.header, "partial": True, "unread": ["workspaces/w/file-0003.txt (Access denied)"]},
        tuple(e for e in held.entries if e.path not in (gone.path, "workspaces/w/file-0003.txt")),
    )
    third = "20261029T030000000000Z"
    target.put_copy(
        Manifest(
            {**partial.header, "stamp": third, "skipped": [[gone.path, gone.sha256]]},
            partial.entries,
        )
    )

    listed = restore.copies(target)

    assert [(c.stamp, c.why, c.partial) for c in listed] == [
        (third, "round", True),
        (second, "round", False),
        (first, "round", False),
    ]
    assert listed[0].lacks == (
        "workspaces/w/file-0003.txt (Access denied)",
        "workspaces/w/file-0002.txt (its bytes were damaged when it was copied)",
    )
    assert (listed[1].files, listed[1].bytes) == (
        len(held.entries),
        sum(e.size for e in held.entries),
    )
    assert listed[1].home_id == home_id(filled.layout)

    staged = restore.stage(filled.layout, target, third, keep_free=0)
    restore.finish(filled.layout)

    assert staged.lacks == listed[0].lacks
    assert "this copy lacks workspaces/w/file-0003.txt (Access denied)" in staged.line
    data = filled.layout.data
    assert not (data / gone.path).exists()
    assert not (data / "workspaces/w/file-0003.txt").exists()
    assert sha256_of(data / "chats" / "c1.json") == next(
        e.sha256 for e in held.entries if e.path == "chats/c1.json"
    )


def test_another_folders_copy_is_refused_by_name_and_restores_with_replace(
    tmp_path: Path,
) -> None:
    other = filled_folder(tmp_path / "Other", files=3, secrets=False)
    target, stamp = sent(other.layout, tmp_path)
    mine = filled_folder(tmp_path / "Mine", files=4)
    before = listing(mine.layout.data)

    with pytest.raises(RestoreRefused, match="is of another QMX folder") as refused:
        restore.stage(mine.layout, target, stamp, keep_free=0)
    assert str(other.layout.root) in str(refused.value)
    assert listing(mine.layout.data) == before
    assert not list(mine.layout.backups.glob("restoring-*"))

    restore.stage(mine.layout, target, stamp, replace=True, keep_free=0)
    finished = restore.finish(mine.layout)

    assert finished is not None
    assert home_id(mine.layout) == home_id(other.layout)
    assert listing(finished.aside / "data") == before


def test_a_new_empty_folder_takes_the_copys_home_and_holds_no_secret_path(tmp_path: Path) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3)
    target, stamp = sent(filled.layout, tmp_path)
    fresh = resolve(tmp_path / "New", create=True)

    restore.stage(fresh, target, stamp, keep_free=0)
    finished = restore.finish(fresh)

    assert finished is not None
    assert home_id(fresh) == home_id(filled.layout)
    placed = listing(fresh.data)
    assert placed == {e.path: e.sha256 for e in target.manifest(stamp).entries}
    assert not [p for p in placed if p.startswith(("vault/", "claude/.", "claude-relayed/."))]
    assert listing(finished.aside / "data") == {}


@pytest.mark.parametrize(
    "path",
    [
        "../outside.txt",
        "workspaces/../../outside.txt",
        "/etc/outside.txt",
        "C:/outside.txt",
        "workspaces\\outside.txt",
        "vault./pairing-key",
        "vault/pairing-key",
        "claude/.credentials.json",
        "chats/x.json:stream",
        "",
    ],
)
def test_a_manifest_naming_a_path_outside_data_is_refused_and_nothing_is_written(
    tmp_path: Path, path: str
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3, long_path_file=False, secrets=False)
    target, stamp = sent(filled.layout, tmp_path)
    held = target.manifest(stamp)
    bad = replace(held.entries[0], path=path)
    edited = Manifest({**held.header, "stamp": "20261028T030000000000Z"}, (*held.entries, bad))
    target.put_copy(edited)

    with pytest.raises(RestoreRefused, match="not a file QMX copies from data/"):
        restore.stage(filled.layout, target, edited.stamp, keep_free=0)

    assert not (tmp_path / "outside.txt").exists()
    assert not list(filled.layout.backups.glob("restoring-*"))
    assert not (filled.layout.backups / "restore.json").exists()


def test_a_copy_of_a_newer_format_or_with_stores_too_new_is_refused_before_anything_is_written(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3, secrets=False)
    target, stamp = sent(filled.layout, tmp_path)
    held = target.manifest(stamp)
    newer = Manifest(
        {**held.header, "stamp": "20261028T030000000000Z", "format": "qmx-backup/2"},
        held.entries,
    )
    target.put_copy(newer)
    engine = next(e for e in held.entries if e.path == "engine/engine.sqlite")
    closed = Manifest(
        {**held.header, "stamp": "20261029T030000000000Z"},
        tuple(replace(e, version=9, min_reader=7) if e is engine else e for e in held.entries),
    )
    target.put_copy(closed)

    with pytest.raises(RestoreRefused, match=r"copy format \(qmx-backup/2\)"):
        restore.stage(filled.layout, target, newer.stamp, keep_free=0)
    with pytest.raises(RestoreRefused, match=r"run ledger at version 9.*version 7 or newer"):
        restore.stage(filled.layout, target, closed.stamp, keep_free=0)

    assert not list(filled.layout.backups.glob("restoring-*"))


def test_a_folder_refused_for_a_newer_format_opens_after_a_copy_from_before_is_restored(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3, secrets=False)
    target, stamp = sent(filled.layout, tmp_path)
    label = filled.layout.label
    label.write_text(
        label.read_text(encoding="utf-8")
        .replace("format_version = 2", "format_version = 3\nmin_reader = 3")
        .replace('last_written_by = "0.1.0"', 'last_written_by = "9.0.0"'),
        encoding="utf-8",
    )
    with pytest.raises(NoQmxFolder, match="folder format 3"):
        resolve(filled.layout.root)

    restore.stage(filled.layout, target, stamp, keep_free=0)
    restore.finish(filled.layout)

    reopened = resolve(filled.layout.root)
    written = Label.parse(reopened.label.read_text(encoding="utf-8"))
    assert (written.format_version, written.min_reader, written.last_written_by) == (
        2,
        None,
        "0.1.0",
    )


def quick_copy(layout: Layout) -> tuple[FolderRepository, str]:
    report = quick(layout, "test", floor=0, now=NOW)
    assert report.places[0].stamp is not None
    return FolderRepository(layout.backups / "quick"), report.places[0].stamp


def test_a_quick_copy_skips_a_purged_blob_places_its_tombstone_and_names_it_for_a_new_purge(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3, secrets=False)
    undo, stamp = quick_copy(filled.layout)
    data = filled.layout.data
    blob = next(
        p for p in filled.written_once if p.startswith("library/blobs/") and "/tomb" not in p
    )
    hexdigest = blob.rpartition("/")[2]
    (data / blob).unlink()
    stone = f"library/blobs/tombstones/{hexdigest}.json"
    (data / stone).write_bytes(b'{"reason": "a secret"}')

    staged = restore.stage(filled.layout, undo, stamp, keep_free=0)
    restore.finish(filled.layout)
    after = restore.after_restore(filled.layout)

    assert staged.purge == (f"sha256:{hexdigest}",)
    assert not (data / blob).exists()
    assert (data / stone).read_bytes() == b'{"reason": "a secret"}'
    assert after is not None
    assert after.purge == (f"sha256:{hexdigest}",)


def test_a_quick_copy_whose_file_written_once_is_gone_without_a_tombstone_is_refused_by_name(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3, secrets=False)
    undo, stamp = quick_copy(filled.layout)
    data = filled.layout.data
    gone = next(p for p in filled.written_once if p.startswith("library/objects/"))
    (data / gone).unlink()
    before = listing(data)

    with pytest.raises(RestoreRefused, match=f"needs {gone} as it was.*second drive"):
        restore.stage(filled.layout, undo, stamp, keep_free=0)
    (data / gone).write_bytes(b"not the same")
    with pytest.raises(RestoreRefused, match=f"needs {gone} as it was"):
        restore.stage(filled.layout, undo, stamp, keep_free=0)

    assert {k: v for k, v in listing(data).items() if k != gone} == {
        k: v for k, v in before.items() if k != gone
    }
    assert not list(filled.layout.backups.glob("restoring-*"))


def test_a_quick_copy_from_before_an_earlier_restore_reads_its_files_from_that_set_aside_folder(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3, secrets=False)
    undo, early = quick_copy(filled.layout)
    target, stamp = sent(filled.layout, tmp_path, datetime.now(UTC))
    data = filled.layout.data
    once = next(p for p in filled.written_once if p.startswith("library/objects/"))
    restore.stage(filled.layout, target, stamp, keep_free=0)
    first = restore.finish(filled.layout)
    assert first is not None
    (data / once).unlink()

    restore.stage(filled.layout, undo, early, keep_free=0)
    restore.finish(filled.layout)

    assert sha256_of(data / once) == next(
        e.sha256 for e in undo.manifest(early).entries if e.path == once
    )


def test_files_written_once_are_linked_where_the_drive_allows_and_copied_elsewhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3, secrets=False)
    undo, stamp = quick_copy(filled.layout)
    once = len([e for e in undo.manifest(stamp).entries if e.at == "live"])

    linked = restore.stage(filled.layout, undo, stamp, keep_free=0)
    restore.cancel(filled.layout)

    def refused(*_: object) -> None:
        raise OSError(1, "links are not allowed on this drive")

    monkeypatch.setattr(restore.os, "link", refused)
    copied = restore.stage(filled.layout, undo, stamp, keep_free=0)
    restore.finish(filled.layout)

    assert (linked.linked, copied.linked) == (once, 0)
    assert copied.bytes == linked.bytes + sum(
        e.size for e in undo.manifest(stamp).entries if e.at == "live"
    )
    placed = {e.path: e.sha256 for e in undo.manifest(stamp).entries}
    assert listing(filled.layout.data) == {**placed, LEASE: sha256_of(filled.layout.data / LEASE)}


def test_too_little_room_refuses_before_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3, secrets=False)
    target, stamp = sent(filled.layout, tmp_path)
    monkeypatch.setattr(restore, "free_bytes", little_room)

    with pytest.raises(RestoreRefused, match=r"needs .* MB in .* and its drive has 0 MB free"):
        restore.stage(filled.layout, target, stamp, keep_free=0)

    assert not list(filled.layout.backups.glob("restoring-*"))
    assert not (filled.layout.backups / "restore.json").exists()


def test_a_second_stage_is_refused_while_one_waits_and_cancel_drops_it(tmp_path: Path) -> None:
    filled = filled_folder(tmp_path / "QMX", files=3, secrets=False)
    target, stamp = sent(filled.layout, tmp_path)
    before = listing(filled.layout.data)
    restore.stage(filled.layout, target, stamp, keep_free=0)

    with pytest.raises(RestoreRefused, match=f"a restore of the copy {stamp} .* staged and waits"):
        restore.stage(filled.layout, target, stamp, keep_free=0)
    line = restore.cancel(filled.layout)

    assert line == (
        f"the restore of the copy {stamp} from {target.where} is cancelled; nothing in "
        f"{filled.layout.root} changed"
    )
    assert restore.finish(filled.layout) is None
    assert listing(filled.layout.data) == before
    assert not list(filled.layout.backups.glob("restoring-*"))


def little_room(_path: Path) -> int:
    return 1000
