"""Two QMX folders on one `home_id` (after a restore) writing to one storage at the same time,
and a send killed halfway (design 06 sections 4 and 14, review M8, M9 and M10)."""

from __future__ import annotations

import os
import random
import shutil
import threading
import time
import uuid
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from backup_fixtures import filled_folder, folder

from qmx_home import Layout
from qmx_home.backup.plan import Plan, Upkeep
from qmx_home.backup.repository import FolderRepository, Unreadable
from qmx_home.backup.round import carry_on, run_round
from qmx_home.files import Busy


class Killed(BaseException):
    """A stop in the middle of a step, as a killed process stops."""


def twins(tmp_path: Path) -> tuple[Layout, Layout]:
    """Two QMX folders with one `home_id`, as a restore on a second PC leaves them."""
    first = filled_folder(tmp_path / "A", files=2, stores=1, once_bytes=4096, secrets=False)
    second = filled_folder(tmp_path / "B", files=2, stores=1, once_bytes=4096, secrets=False)
    second.layout.label.write_bytes(first.layout.label.read_bytes())
    return first.layout, second.layout


def storage_of(tmp_path: Path) -> FolderRepository:
    holder = tmp_path / "usb" / "QMX-backup"
    (home,) = [p for p in holder.iterdir() if p.is_dir()]
    return FolderRepository(home)


def broken_copies(repo: FolderRepository, scratch: Path) -> list[str]:
    """Each copy on the storage that names a file it cannot give back as it was."""
    fresh = FolderRepository(repo.root)
    broken: list[str] = []
    scratch.mkdir(parents=True, exist_ok=True)
    for stamp in fresh.copies():
        try:
            manifest = fresh.manifest(stamp)
        except Unreadable:
            continue
        for entry in manifest.entries:
            target = scratch / uuid.uuid4().hex
            try:
                got = fresh.fetch(entry.sha256, target)
            except FileNotFoundError:
                got = ""
            finally:
                target.unlink(missing_ok=True)
            if got != entry.sha256:
                broken.append(f"{stamp} {entry.path}")
    return broken


def write_round(layout: Layout, plan: Plan, tag: str) -> None:
    (layout.data / "chats" / "c1.json").write_text(f'{{"n": "{tag}"}}', encoding="utf-8")
    carry_on(layout, plan.storages[0])
    with suppress(Busy):
        run_round(layout, plan, now=datetime.now(UTC), floor=0, only="usb")


def test_two_writers_on_one_home_id_never_leave_a_copy_naming_a_file_that_is_gone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qmx_home.backup import repository

    a, b = twins(tmp_path)
    plan = Plan(storages=(folder(tmp_path / "usb"),))
    write_round(a, plan, "first")
    real_copy = repository.copy_file

    def slow_copy(source: Path, target: Path, **kwargs: int | None) -> str:
        time.sleep(0.02)
        return real_copy(source, target, **kwargs)

    monkeypatch.setattr(repository, "copy_file", slow_copy)
    for number in range(30):
        threads = [
            threading.Thread(target=write_round, args=(one, plan, f"{name}{number}"))
            for name, one in (("a", a), ("b", b))
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    assert broken_copies(storage_of(tmp_path), tmp_path / "back") == []


def test_a_killed_send_leaves_its_arrived_packs_named_and_the_next_send_reuses_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=2, stores=1, secrets=False)
    for number in range(3):
        (filled.layout.data / "workspaces" / f"big-{number}.bin").write_bytes(os.urandom(17 << 20))
    plan = Plan(storages=(folder(tmp_path / "usb"),))
    packs: list[str] = []
    real = FolderRepository._step  # pyright: ignore[reportPrivateUsage]

    def step(self: FolderRepository, op: str) -> None:
        if "usb" in str(self.root) and op == "pack":
            packs.append(op)
            if len(packs) == 3:
                raise Killed
        real(self, op)

    with monkeypatch.context() as patched:
        patched.setattr(FolderRepository, "_step", step)
        with pytest.raises(Killed):
            run_round(filled.layout, plan, now=datetime.now(UTC), floor=0)
    usb = storage_of(tmp_path)
    arrived = set(usb.packs())
    report = run_round(filled.layout, plan, now=datetime.now(UTC), floor=0, only="usb")

    held = FolderRepository(usb.root).index()
    assert len(arrived) == 2
    assert [p.result for p in report.places][-1] == "copied"
    assert arrived <= set(FolderRepository(usb.root).packs())
    assert all(len({at.pack for at in places}) == 1 for places in held.where.values())
    assert usb.copies()
    assert broken_copies(usb, tmp_path / "back") == []


def test_the_one_fact_no_kept_copy_ever_names_a_pack_that_is_gone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qmx_home.backup.upkeep import repack

    a, b = twins(tmp_path)
    plan = Plan(storages=(folder(tmp_path / "usb"),), upkeep=Upkeep(safety="2s"))
    write_round(a, plan, "first")
    usb = storage_of(tmp_path)
    killing = threading.local()
    dice = random.Random(20261029)  # noqa: S311 - where the kills land, not a secret
    real = FolderRepository._step  # pyright: ignore[reportPrivateUsage]

    def step(self: FolderRepository, op: str) -> None:
        if getattr(killing, "on", False) and dice.random() < 0.08:
            raise Killed
        real(self, op)

    deleted: list[int] = []

    def writer(layout: Layout, tag: str) -> None:
        killing.on = True
        try:
            write_round(layout, plan, tag)
        except Killed:
            shutil.rmtree(layout.cache / "sync-staging", ignore_errors=True)

    def packer() -> None:
        killing.on = True
        try:
            pruned = repack(
                FolderRepository(usb.root),
                past=0.05,
                per_run=None,
                safety=timedelta(seconds=2),
                now=datetime.now(UTC),
            )
            deleted.append(pruned.deleted)
        except Killed, Busy:
            pass

    monkeypatch.setattr(FolderRepository, "_step", step)
    broken: list[str] = []
    for number in range(200):
        threads = [
            threading.Thread(target=writer, args=(a, f"a{number}")),
            threading.Thread(target=writer, args=(b, f"b{number}")),
            threading.Thread(target=packer),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        broken += broken_copies(usb, tmp_path / "back")
        if broken:
            break

    assert broken == []
    assert sum(deleted) >= 1, "the re-pack never deleted a pack, so the race was not run"
