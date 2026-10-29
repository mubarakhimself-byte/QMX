"""Packs on a storage (design 06 sections 3 and 6): files in zstd frames with their checksum, an
index per confirmed pack, the bad list, the prune's safety window, torn indexes and manifests,
and copies made before packs."""

from __future__ import annotations

import hashlib
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from backup_fixtures import damage, filled_folder, folder, stored, stored_bytes

from qmx_home import Label, Layout
from qmx_home.backup import restore
from qmx_home.backup.plan import Plan
from qmx_home.backup.repository import (
    FORMAT,
    Entry,
    FolderRepository,
    Manifest,
    pack_list,
    stamp_of,
)
from qmx_home.backup.round import run_round

NOW = datetime(2026, 10, 27, 3, 0, tzinfo=UTC)


def storage_of(layout: Layout, usb: Path) -> FolderRepository:
    home_id = Label.parse(layout.label.read_text(encoding="utf-8")).home_id
    return FolderRepository(usb / "QMX-backup" / home_id)


def written(folder: Path, name: str, data: bytes) -> tuple[Path, str]:
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path, hashlib.sha256(data).hexdigest()


def test_a_pack_gives_back_every_file_compressed_with_its_checksum_and_parquet_as_it_is(
    tmp_path: Path,
) -> None:
    repo = FolderRepository(tmp_path / "storage")
    text, text_sha = written(tmp_path / "src", "notes.txt", b"the same line again\n" * 5000)
    month, month_sha = written(tmp_path / "src", "m.parquet", b"PAR1" + os.urandom(4000))

    repo.put_pool(text_sha, text, path="workspaces/notes.txt")
    repo.put_pool(month_sha, month, path="market/x/2026-01/m.parquet")
    repo.seal()

    (pack,) = repo.packs()
    listed = pack_list(repo.local_pack(pack))
    assert listed is not None
    text_at, month_at = listed[1][text_sha], listed[1][month_sha]
    assert (text_at.raw, text_at.size) == (False, 100_000)
    assert text_at.length < 1000
    assert (month_at.raw, month_at.length, month_at.size) == (True, 4004, 4004)
    assert stored_bytes(repo, text_sha, tmp_path / "back") == text.read_bytes()
    assert stored_bytes(repo, month_sha, tmp_path / "back") == month.read_bytes()
    assert len(list((repo.root / "index").iterdir())) == 1


def test_a_flipped_byte_in_a_frame_never_comes_back_as_the_file(tmp_path: Path) -> None:
    repo = FolderRepository(tmp_path / "storage")
    text, sha = written(tmp_path / "src", "notes.txt", b"his strategy\n" * 1000)
    repo.put_pool(sha, text, path="notes.txt")
    repo.seal()

    damage(repo, sha)

    assert repo.fetch(sha, tmp_path / "back.txt") != sha


def test_a_copy_says_its_format_and_restores_every_file_and_row_count(tmp_path: Path) -> None:
    filled = filled_folder(tmp_path / "QMX", files=4, secrets=False)
    run_round(filled.layout, Plan(storages=(folder(tmp_path / "usb"),)), now=NOW, floor=0)
    usb = storage_of(filled.layout, tmp_path / "usb")
    stamp = usb.copies()[-1]
    fresh = filled_folder(tmp_path / "fresh", files=0, stores=0, secrets=False)

    staged = restore.stage(fresh.layout, usb, stamp, replace=True, keep_free=0)

    assert usb.manifest(stamp).header["format"] == FORMAT == "qmx-backup/2"
    assert not (usb.root / "pool").exists()
    assert set(stored(usb)) >= {e.sha256 for e in usb.manifest(stamp).entries}
    assert staged.files == len(usb.manifest(stamp).entries)


def test_a_loose_pool_copy_from_before_packs_still_restores(tmp_path: Path) -> None:
    filled = filled_folder(tmp_path / "QMX", files=2, stores=1, secrets=False)
    run_round(filled.layout, Plan(), now=NOW, floor=0)
    quick = FolderRepository(filled.layout.backups / "quick")
    made = quick.manifest(quick.copies()[-1])
    old = FolderRepository(tmp_path / "old")
    for entry in made.entries:
        old.put_bytes(stored_bytes(quick, entry.sha256, tmp_path / "back"))
    copy = Manifest({**made.header, "format": "qmx-backup/1"}, made.pooled().entries)
    old.put_copy(copy)
    data = filled.layout.data
    (data / "chats" / "c1.json").write_bytes(b'{"title": "changed since"}')

    restore.stage(filled.layout, old, copy.stamp, keep_free=0)
    restore.finish(filled.layout)

    assert not old.packs()
    assert (data / "chats" / "c1.json").read_bytes() == b'{"title": "first chat"}'


def test_this_pcs_files_written_once_are_hard_links_in_its_pool(tmp_path: Path) -> None:
    filled = filled_folder(tmp_path / "QMX", files=2, secrets=False)

    run_round(filled.layout, Plan(), now=NOW, floor=0)

    quick = FolderRepository(filled.layout.backups / "quick")
    copy = quick.manifest(quick.copies()[-1])
    once = [e for e in copy.entries if e.kind == "once"]
    assert once and {e.at for e in once} == {"pool"}
    for entry in once:
        assert os.stat(quick.pool_path(entry.sha256)).st_nlink == 2
    assert {e.at for e in copy.entries if e.kind != "once"} == {"pool"}
    assert not any(quick.loose(e.sha256) for e in copy.entries if e.kind != "once")


def test_each_confirmed_pack_gets_its_index_before_the_copy_is_written(tmp_path: Path) -> None:
    repo = FolderRepository(tmp_path / "storage")
    shas: list[str] = []
    for number in range(3):
        path, sha = written(tmp_path / "src", f"big-{number}.bin", os.urandom(17 << 20))
        repo.put_pool(sha, path, path=f"workspaces/big-{number}.bin")
        shas.append(sha)

    assert len(repo.packs()) == 3
    assert len(list((repo.root / "index").iterdir())) == 3
    assert not (repo.root / "snapshots").exists()
    again = FolderRepository(tmp_path / "storage")
    assert all(again.pool_has(sha) for sha in shas)


def test_the_bad_list_makes_a_file_read_as_missing_until_it_is_sent_again(tmp_path: Path) -> None:
    repo = FolderRepository(tmp_path / "storage")
    path, sha = written(tmp_path / "src", "notes.txt", b"his notes")
    repo.put_pool(sha, path, path="notes.txt")
    repo.seal()

    repo.mark_bad(sha)
    after = FolderRepository(tmp_path / "storage")
    gone = after.pool_has(sha)
    after.put_pool(sha, path, path="notes.txt")
    after.seal()

    assert gone is False
    assert FolderRepository(tmp_path / "storage").pool_has(sha) is True
    assert len(after.packs()) == 2
    assert stored_bytes(after, sha, tmp_path / "back") == b"his notes"


def copies_of(repo: FolderRepository, files: dict[str, Path], stamps: list[str]) -> None:
    for stamp in stamps:
        entries: list[Entry] = []
        for name, path in files.items():
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            repo.put_pool(sha, path, path=name)
            entries.append(Entry(name, sha, path.stat().st_size, "file", (1, 1)))
        repo.put_copy(Manifest({"format": FORMAT, "stamp": stamp}, tuple(entries)))


def test_no_pack_named_in_the_safety_window_is_deleted_whatever_its_files_mtime(
    tmp_path: Path,
) -> None:
    start = datetime.now(UTC) - timedelta(days=10)
    repo = FolderRepository(tmp_path / "storage", clock=lambda: start)
    old, old_sha = written(tmp_path / "src", "old.txt", b"old work")
    new, _ = written(tmp_path / "src", "new.txt", b"new work")
    hours = [stamp_of(start + timedelta(hours=n)) for n in (1, 2, 3)]
    copies_of(repo, {"old.txt": old}, hours[:1])
    copies_of(repo, {"new.txt": new}, hours[1:])
    first = repo.index().where[old_sha][0].pack
    long_ago = time.time() - 300 * 86400
    for path in (repo.root / "packs").rglob("*.pack"):
        os.utime(path, (long_ago, long_ago))
    repo.drop(hours[0])
    day = timedelta(hours=24)

    young = repo.sweep(safety=day, now=start + timedelta(hours=4))
    marked = repo.sweep(safety=day, now=start + timedelta(days=2))
    gone = repo.sweep(safety=day, now=start + timedelta(days=4))

    assert (young.removed, marked.removed, gone.removed) == (0, 0, 1)
    assert first not in repo.packs()
    assert all(repo.pool_has(e.sha256) for s in repo.copies() for e in repo.manifest(s).entries)


def test_a_storage_that_keeps_one_copy_lets_go_of_the_packs_it_no_longer_needs(
    tmp_path: Path,
) -> None:
    start = datetime.now(UTC) - timedelta(days=10)
    repo = FolderRepository(tmp_path / "storage", clock=lambda: start)
    old, _ = written(tmp_path / "src", "old.txt", b"old work")
    new, new_sha = written(tmp_path / "src", "new.txt", b"new work")
    hours = [stamp_of(start + timedelta(hours=n)) for n in (1, 2)]
    copies_of(repo, {"old.txt": old}, hours[:1])
    copies_of(repo, {"new.txt": new}, hours[1:])
    repo.drop(hours[0])
    day = timedelta(hours=24)

    marked = repo.sweep(safety=day, now=start + timedelta(days=2))
    gone = repo.sweep(safety=day, now=start + timedelta(days=4))

    assert (marked.removed, gone.removed) == (0, 1)
    assert set(repo.packs()) == {repo.index().where[new_sha][0].pack}
    assert repo.pool_has(new_sha)


def test_dropping_a_copy_removes_only_its_manifest(tmp_path: Path) -> None:
    repo = FolderRepository(tmp_path / "storage")
    work, _ = written(tmp_path / "src", "work.txt", b"his work")
    copies_of(repo, {"work.txt": work}, ["20261020T030000000000Z", "20261021T030000000000Z"])
    index = sorted(p.name for p in (repo.root / "index").iterdir())
    packs = set(repo.packs())

    repo.drop("20261020T030000000000Z")

    assert repo.copies() == ("20261021T030000000000Z",)
    assert sorted(p.name for p in (repo.root / "index").iterdir()) == index
    assert set(repo.packs()) == packs


def test_a_torn_index_is_skipped_and_rebuilt_from_its_packs_own_list(tmp_path: Path) -> None:
    repo = FolderRepository(tmp_path / "storage")
    work, sha = written(tmp_path / "src", "work.txt", b"his work")
    copies_of(repo, {"work.txt": work}, ["20261020T030000000000Z", "20261021T030000000000Z"])
    (index,) = (repo.root / "index").iterdir()
    index.write_bytes(index.read_bytes()[:-30])

    torn = FolderRepository(tmp_path / "storage")
    found = torn.pool_has(sha)
    skipped = list(torn.index().torn)
    pruned = torn.prune(safety=timedelta(hours=1), now=datetime.now(UTC))

    assert found is False
    assert skipped == [index.name]
    assert (pruned.torn, pruned.rebuilt) == ((index.name,), 1)
    assert not index.exists()
    assert FolderRepository(tmp_path / "storage").pool_has(sha) is True


def test_a_torn_manifest_older_than_the_newest_whole_copy_is_cleaned(tmp_path: Path) -> None:
    repo = FolderRepository(tmp_path / "storage")
    work, _ = written(tmp_path / "src", "work.txt", b"his work")
    copies_of(repo, {"work.txt": work}, ["20261020T030000000000Z", "20261021T030000000000Z"])
    torn = repo.snapshots / "20261020T030000000000Z" / "manifest.jsonl"
    torn.write_bytes(torn.read_bytes()[:-30])

    cleaned = repo.clean()

    assert cleaned.torn == ("20261020T030000000000Z",)
    assert repo.copies() == ("20261021T030000000000Z",)
    assert repo.sweep(safety=timedelta(hours=1), now=datetime.now(UTC)).blocked is None


def test_an_index_stamp_is_this_machines_clock_at_the_write(tmp_path: Path) -> None:
    moment = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)
    repo = FolderRepository(tmp_path / "storage", clock=lambda: moment)
    work, _ = written(tmp_path / "src", "work.txt", b"his work")
    repo.put_pool(hashlib.sha256(b"his work").hexdigest(), work, path="work.txt")
    repo.seal()

    (index,) = (repo.root / "index").iterdir()

    assert index.name.startswith(f"{stamp_of(moment)}-")


@pytest.mark.parametrize("files", [0, 1])
def test_a_fetch_from_an_empty_storage_says_the_file_is_missing(tmp_path: Path, files: int) -> None:
    repo = FolderRepository(tmp_path / "storage")
    if files:
        work, _ = written(tmp_path / "src", "work.txt", b"his work")
        repo.put_pool(hashlib.sha256(b"his work").hexdigest(), work, path="work.txt")
        repo.seal()

    with pytest.raises(FileNotFoundError):
        repo.fetch("0" * 64, tmp_path / "back")
