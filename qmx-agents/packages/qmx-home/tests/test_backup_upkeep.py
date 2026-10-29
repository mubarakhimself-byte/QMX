"""QMX's monthly upkeep of a storage (design 06 section 6): the re-pack, killed after each of its
four steps, and the check, a different slice of the packs each month that reads every pack
within twelve months."""

from __future__ import annotations

import hashlib
import os
import random
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from backup_fixtures import damage, stored_bytes

from qmx_home.backup.repository import FORMAT, Entry, FolderRepository, Manifest, stamp_of
from qmx_home.backup.upkeep import check, repack

START = datetime.now(UTC) - timedelta(days=20)
LATER = START + timedelta(days=10)


class Killed(BaseException):
    """A stop in the middle of a step, as a killed process stops."""


def storage(tmp_path: Path) -> tuple[FolderRepository, dict[str, bytes]]:
    """A storage whose first pack is mostly unused: ten files, of which the copies it keeps name
    three, beside two packs the copies use whole."""
    repo = FolderRepository(tmp_path / "storage", clock=lambda: START)
    files = {f"f{n}.bin": os.urandom(10_000) for n in range(12)}
    src = tmp_path / "src"
    src.mkdir()
    for name, body in files.items():
        (src / name).write_bytes(body)

    def copy(stamp: str, names: list[str]) -> None:
        entries: list[Entry] = []
        for name in names:
            sha = hashlib.sha256(files[name]).hexdigest()
            repo.put_pool(sha, src / name, path=name)
            entries.append(Entry(name, sha, len(files[name]), "file", (1, 1)))
        repo.put_copy(Manifest({"format": FORMAT, "stamp": stamp}, tuple(entries)))

    stamps = [stamp_of(START + timedelta(hours=n)) for n in range(4)]
    copy(stamps[0], [f"f{n}.bin" for n in range(10)])
    copy(stamps[1], ["f0.bin", "f1.bin", "f2.bin", "f10.bin"])
    copy(stamps[2], ["f0.bin", "f1.bin", "f2.bin", "f10.bin", "f11.bin"])
    repo.drop(stamps[0])
    return repo, files


def every_index_names_a_pack_that_exists(repo: FolderRepository) -> bool:
    fresh = FolderRepository(repo.root)
    held = fresh.index()
    packs = set(fresh.packs())
    return all(at.pack in packs for places in held.where.values() for at in places)


def every_kept_copy_restores(repo: FolderRepository, scratch: Path) -> bool:
    fresh = FolderRepository(repo.root)
    for stamp in fresh.copies():
        for entry in fresh.manifest(stamp).entries:
            body = stored_bytes(fresh, entry.sha256, scratch)
            if hashlib.sha256(body).hexdigest() != entry.sha256:
                return False
    return True


@pytest.mark.parametrize("stop", ["pack", "merged", "unindex", "unpack"])
def test_a_repack_killed_after_any_step_leaves_every_index_naming_packs_that_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stop: str
) -> None:
    repo, _ = storage(tmp_path)
    stopped: list[str] = []

    def step(_self: FolderRepository, op: str) -> None:
        if op == stop:
            stopped.append(op)
            raise Killed

    for moment in (LATER, LATER + timedelta(days=1), LATER + timedelta(days=2)):
        with monkeypatch.context() as patched:
            patched.setattr(FolderRepository, "_step", step)
            with suppress(Killed):
                repack(repo, past=0.05, per_run=None, safety=timedelta(hours=1), now=moment)
        assert every_index_names_a_pack_that_exists(repo)
        assert every_kept_copy_restores(repo, tmp_path / "back")
    assert stopped


def test_a_whole_repack_then_a_second_leaves_under_five_percent_unused(tmp_path: Path) -> None:
    repo, _ = storage(tmp_path)

    first = repack(repo, past=0.05, per_run=None, safety=timedelta(hours=1), now=LATER)
    second = repack(
        repo, past=0.05, per_run=None, safety=timedelta(hours=1), now=LATER + timedelta(days=1)
    )

    assert (first.written, first.deleted) == (1, 0)
    assert second.deleted == 1
    assert second.unused < 0.05
    assert every_kept_copy_restores(repo, tmp_path / "back")


def test_the_check_names_a_flipped_byte_by_its_file_and_puts_it_on_the_bad_list(
    tmp_path: Path,
) -> None:
    repo, files = storage(tmp_path)
    sha = hashlib.sha256(files["f10.bin"]).hexdigest()
    damage(repo, sha)

    months = [check(repo, slice=12, month=m, work=tmp_path / "work") for m in range(12)]
    found = [m for m in months if m.damaged]

    assert [m.packs >= 1 for m in months] == [True] * 12
    assert len(found) == 1
    assert found[0].damaged == ("f10.bin",)
    assert "f10.bin is damaged and goes on the list of damaged files" in found[0].line
    assert "pack" not in found[0].line and sha not in found[0].line
    assert FolderRepository(repo.root).pool_has(sha) is False
    assert not (tmp_path / "work").exists() or not any((tmp_path / "work").iterdir())


def test_every_pack_is_read_back_within_twelve_months_as_packs_come_and_go(tmp_path: Path) -> None:
    repo = FolderRepository(tmp_path / "storage", clock=lambda: START)
    made = random.Random(7)  # noqa: S311 - which slice each pack falls in, not a secret
    src = tmp_path / "src"
    src.mkdir()

    def packed(name: str) -> str:
        body = made.randbytes(4000)
        (src / name).write_bytes(body)
        sha = hashlib.sha256(body).hexdigest()
        repo.put_pool(sha, src / name, path=name)
        repo.seal()
        return sha

    first = [packed(f"first-{n}.bin") for n in range(6)]
    for sha in first:
        damage(repo, sha)

    for month in range(12):
        packed(f"month-{month}-a.bin")
        packed(f"month-{month}-b.bin")
        check(repo, slice=12, month=month, work=tmp_path / "work")

    fresh = FolderRepository(repo.root)
    assert [fresh.pool_has(sha) for sha in first] == [False] * 6
