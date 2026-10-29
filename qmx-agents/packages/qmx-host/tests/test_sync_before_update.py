"""Sync before every update (design 06 section 7): `serve` sends one copy to every storage that is
on before a store upgrades, never waits on a storage past `before_update_wait`, and a store's own
pre-change copy is released when that copy holds it. Every folder and profile is in pytest's tmp
folder; the host itself, Credential Manager and pg0 are never started."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import threading
import time
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest
from qmx_engine.ledger.migrations import STEPS
from qmx_engine.ledger.store import Ledger
from qmx_home import Layout, resolve
from qmx_home.backup.plan import Plan
from qmx_home.backup.repository import FolderRepository
from qmx_home.backup.round import quick, sync_now
from qmx_home.rclone import Rclone
from qmx_home.versions import upgrade_copied, upgrade_moment_ended
from test_connect import Store
from test_restore_command import code, pc, unscrubbed

import qmx_host.__main__
import qmx_host.host

needs_rclone = pytest.mark.skipif(shutil.which("rclone") is None, reason="rclone is not on PATH")
_ = pc, unscrubbed


def old_ledger(layout: Layout) -> Path:
    """A run ledger one schema behind this release, so the host's open upgrades it."""
    path = layout.data / "engine" / "engine.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, isolation_level=None)) as db:
        for statement in (*STEPS[0], *STEPS[1]):
            db.execute(statement)
        db.execute("INSERT INTO meta VALUES ('schema_version', '2')")
    return path


def schema(layout: Layout) -> str:
    with closing(sqlite3.connect(layout.data / "engine" / "engine.sqlite")) as db:
        return str(db.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()[0])


def pre_copies(layout: Layout) -> list[str]:
    return sorted(p.name for p in layout.backups.glob("pre-*")) if layout.backups.is_dir() else []


def storage_row(root: Path, *, wait: str | None = None) -> str:
    upkeep = f'\n[backup.upkeep]\nbefore_update_wait = "{wait}"\n' if wait else ""
    return (
        '[engine.placement.cloud]\nid = "cloud01"\nvia = "rclone"\ncan = ["keep"]\n'
        f'remote = "qmx_cloud"\ntype = "local"\nroot = {json.dumps(str(root))}\n{upkeep}'
    )


@pytest.fixture
def opened(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """What each `serve` found when the host would open its stores, which upgrades them."""
    seen: list[dict[str, Any]] = []

    def serve_forever(home: Path, **_kw: object) -> int:
        stored = list(Path(os.environ.get("SY5_STORAGE", "-")).rglob("manifest.jsonl"))
        with Ledger.open(home):
            pass
        seen.append({"stored_before": len(stored)})
        return 0

    monkeypatch.setattr(qmx_host.host, "serve_forever", serve_forever)
    return seen


class Unanswering:
    """An rclone runner that never answers, as a storage behind a dead network does."""

    def __init__(self) -> None:
        self.stop = threading.Event()
        self.path = ""

    def run(self, *_args: object, **_kw: object) -> Any:
        self.stop.wait()
        raise OSError("the storage never answered")

    def secrets_for(self, *_args: object) -> dict[str, str]:
        return {}


@pytest.fixture
def unanswering(monkeypatch: pytest.MonkeyPatch) -> Iterator[Unanswering]:
    runner = Unanswering()
    monkeypatch.setattr(qmx_host.__main__, "_rclone", lambda _layout, _plan: runner)  # pyright: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
    yield runner
    runner.stop.set()


def test_with_only_this_pc_on_sync_now_needs_no_host_and_copies_once(tmp_path: Path) -> None:
    layout = resolve(tmp_path / "QMX", create=True)
    (layout.data / "notes.txt").write_text("a note", encoding="utf-8")

    synced = sync_now(layout, Plan(), "before-update")

    quick_copies = FolderRepository(layout.backups / "quick").copies()
    assert (synced.copied, synced.sent, synced.late, synced.missed) == (True, (), (), ())
    assert len(quick_copies) == 1
    manifest = FolderRepository(layout.backups / "quick").manifest(quick_copies[0])
    assert manifest.header["why"] == "before-update"


@needs_rclone
def test_serve_sends_a_copy_to_the_storage_before_its_store_upgrades_and_releases_its_pre_copy(
    pc: Path,
    opened: list[dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    layout = resolve(pc / "QMX", create=True)
    old_ledger(layout)
    storage = pc / "storage"
    storage.mkdir()
    keys = Store()
    made = Rclone(layout, keys=keys).run(
        ["config", "create", "qmx_cloud", "local", "--non-interactive"]
    )
    assert made.code == 0, made.line
    (layout.data / "settings.toml").write_text(storage_row(storage), encoding="utf-8")
    monkeypatch.setattr(
        qmx_host.__main__,
        "_rclone",
        lambda folder, _plan: Rclone(folder, keys=keys),  # pyright: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
    )
    monkeypatch.setenv("SY5_STORAGE", str(storage))

    started = code(["serve", "--home", str(layout.root)])
    said = capsys.readouterr().err

    manifests = list(storage.rglob("manifest.jsonl"))
    assert (started, schema(layout)) == (0, str(len(STEPS)))
    assert opened == [{"stored_before": 1}]
    assert len(manifests) == 1
    assert '"why": "before-update"' in manifests[0].read_text(encoding="utf-8")
    assert pre_copies(layout) == []
    assert "before the upgrade: copied " in said
    assert ", and sent to cloud" in said


def test_an_update_never_waits_on_a_storage_it_cannot_reach(
    pc: Path,
    opened: list[dict[str, Any]],
    unanswering: Unanswering,
    capsys: pytest.CaptureFixture[str],
) -> None:
    alone = resolve(pc / "Alone", create=True)
    old_ledger(alone)
    began = time.monotonic()
    assert code(["serve", "--home", str(alone.root)]) == 0
    parent = time.monotonic() - began
    capsys.readouterr()
    layout = resolve(pc / "QMX", create=True)
    old_ledger(layout)
    (layout.data / "settings.toml").write_text(
        storage_row(pc / "storage", wait="2s"), encoding="utf-8"
    )

    began = time.monotonic()
    started = code(["serve", "--home", str(layout.root)])
    took = time.monotonic() - began
    said = capsys.readouterr().err

    (stamp,) = FolderRepository(layout.backups / "quick").copies()
    why = FolderRepository(layout.backups / "quick").manifest(stamp).header["why"]
    assert (started, schema(layout), why) == (0, str(len(STEPS)), "before-update")
    assert took < 2 + parent + 1.0, (took, parent)
    assert (
        "before the upgrade: the sync to cloud did not end within 2 s; it goes on by itself. The "
        "update goes on; your copy on this PC is fresh." in said
    )
    assert pre_copies(layout) == []


def test_a_pre_change_copy_is_released_only_when_this_starts_upgrade_copy_holds_the_store(
    tmp_path: Path,
) -> None:
    covered = resolve(tmp_path / "Covered", create=True)
    old_ledger(covered)
    upgrade_copied(covered, quick(covered, "before-update", floor=0).stamp)
    earlier = resolve(tmp_path / "Earlier", create=True)
    old_ledger(earlier)
    upgrade_copied(earlier, quick(earlier, "before-update", floor=0).stamp)
    upgrade_moment_ended(earlier)
    bare = resolve(tmp_path / "Bare", create=True)
    old_ledger(bare)

    for layout in (covered, earlier, bare):
        with Ledger.open(layout.home):
            pass

    assert pre_copies(covered) == []
    assert len(pre_copies(earlier)) == 1
    assert len(pre_copies(bare)) == 1
