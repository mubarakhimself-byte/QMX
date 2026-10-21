"""APP2b: one home per app instance, moved by a snapshot, a restore and a handed-over lease."""

from __future__ import annotations

import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from qmx_apps import bundle
from qmx_apps.errors import AppError, Document
from qmx_apps.manifest import Definition
from qmx_apps.supervisor import Supervisor
from qmx_apps.volume import VolumeLease

EXAMPLES = Path(__file__).resolve().parents[4] / "examples/apps"
APP = "macro-daily-bias"


class RuntimeFixture(Supervisor):
    """Activation only is faked: no test starts a real app process here."""

    running: str | None = None

    def start(
        self,
        app_id: str,
        *,
        definition_hash: str | None = None,
        profile: str | None = None,
    ) -> Document:
        self.running = definition_hash
        return self.status(app_id)

    def stop(self, app_id: str) -> Document:
        self.running = None
        return self.status(app_id)

    def status(self, app_id: str) -> Document:
        return {"status": "running" if self.running else "stopped"}


def registered(owner: Supervisor, source: Path) -> Definition:
    """The app installed on `owner` from `source`, with its immutable image under its hash."""
    image = Definition.load(source)
    target = owner.home / "definitions" / image.hash
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", ".venv"))
    owner.road.register(Definition.load(target), "first_party", None)
    return Definition.load(target)


def write_state(owner: Supervisor) -> None:
    (owner.home / "apps" / APP / "data" / "bias.json").write_text(
        '{"pair": "EURUSD", "bias": 1}', encoding="utf-8"
    )
    with closing(sqlite3.connect(owner.home / "apps" / APP / "app.db")) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, note TEXT)")
        db.execute("INSERT INTO runs VALUES('r1', 'kept')")


def read_state(owner: Supervisor) -> tuple[str, list[tuple[str, str]]]:
    latest = owner.home / "apps" / APP / "data" / "bias.json"
    with closing(sqlite3.connect(owner.home / "apps" / APP / "app.db")) as db:
        rows = list(db.execute("SELECT id, note FROM runs ORDER BY id"))
    return latest.read_text(encoding="utf-8"), rows


def test_a_move_carries_the_state_to_the_machine_it_names(tmp_path: Path) -> None:
    pc = RuntimeFixture(tmp_path / "pc", placement="pc")
    contabo = RuntimeFixture(tmp_path / "contabo", placement="contabo")
    registered(pc, EXAMPLES / APP)
    registered(contabo, EXAMPLES / APP)
    write_state(pc)

    moved = pc.snapshot_instance(APP, to="contabo")
    assert pc.home_of(APP) == "contabo"
    assert moved.to == "contabo"
    assert moved.files > 0

    restored = contabo.restore_instance(APP, moved.snapshot_id, folder=moved.folder)
    assert contabo.home_of(APP) == "contabo"
    assert restored["generation"] == moved.generation
    assert read_state(contabo) == ('{"pair": "EURUSD", "bias": 1}', [("r1", "kept")])


def test_the_machine_that_gave_an_instance_away_cannot_take_its_volume_back(
    tmp_path: Path,
) -> None:
    pc = RuntimeFixture(tmp_path / "pc", placement="pc")
    registered(pc, EXAMPLES / APP)
    write_state(pc)
    moved = pc.snapshot_instance(APP, to="contabo")

    with pytest.raises(AppError) as refused:
        VolumeLease(pc.home, APP, holder="pc", expect=moved.lease)
    assert refused.value.code == "lease_handed_over"


def test_a_bundle_is_fetched_by_hash_from_another_machines_store(tmp_path: Path) -> None:
    pc = RuntimeFixture(tmp_path / "pc", placement="pc")
    server = RuntimeFixture(tmp_path / "contabo", placement="contabo")
    image = registered(pc, EXAMPLES / APP)

    fetched = bundle.fetch(server.home, image.hash, [pc.home / "definitions"])
    assert bundle.present(server.home, image.hash)
    assert fetched == server.home / "definitions" / image.hash

    with pytest.raises(AppError) as refused:
        bundle.fetch(server.home, "0" * 64, [pc.home / "definitions"])
    assert refused.value.code == "bundle_missing"
