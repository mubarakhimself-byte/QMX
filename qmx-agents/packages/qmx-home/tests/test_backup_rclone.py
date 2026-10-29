"""An rclone storage (design 06 sections 3 and 14) on rclone's `local` backend: copies written
only with `rclone copy`, each arrival checked with `lsf`, a restore that fetches one pack at a
time and counts bytes then files, and a storage that is offline or whose sign-in expired."""

from __future__ import annotations

import hashlib
import shutil
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest
from backup_fixtures import filled_folder

from qmx_home import Label, Layout
from qmx_home.backup import restore
from qmx_home.backup.plan import Plan, Storage, open_storage
from qmx_home.backup.repository import RcloneRepository
from qmx_home.backup.round import run_round
from qmx_home.rclone import Failure, Ran, Rclone

needs_rclone = pytest.mark.skipif(shutil.which("rclone") is None, reason="rclone is not on PATH")
NOW = datetime(2026, 10, 27, 3, 0, tzinfo=UTC)


class Keys:
    def __init__(self) -> None:
        self.held: dict[str, str] = {}

    def read(self, name: str) -> str | None:
        return self.held.get(name)

    def replace(self, name: str, value: str) -> None:
        self.held[name] = value


def lane(tmp_path: Path) -> tuple[Layout, Rclone, Storage, Path]:
    filled = filled_folder(tmp_path / "QMX", files=3, secrets=False)
    runner = Rclone(filled.layout, keys=Keys())
    assert runner.run(["config", "create", "qmx_lane", "local"]).code == 0
    store = tmp_path / "store"
    store.mkdir()
    storage = Storage(
        "lane", "lane", "rclone", None, remote="qmx_lane", type="local", root=str(store)
    )
    return filled.layout, runner, storage, store


@needs_rclone
def test_a_round_to_an_rclone_storage_writes_only_by_copy_and_checks_every_arrival(
    tmp_path: Path,
) -> None:
    layout, runner, storage, store = lane(tmp_path)

    report = run_round(layout, Plan(storages=(storage,)), now=NOW, floor=0, rclone=runner)

    home_id = Label.parse(layout.label.read_text(encoding="utf-8")).home_id
    holder = store / "QMX-backup" / home_id
    calls = [call.args for call in runner.record]
    verbs = [next(a for a in args[2:] if not a.startswith("-")) for args in calls]
    assert [(p.id, p.result) for p in report.places] == [("quick", "copied"), ("lane", "copied")]
    assert not {"sync", "bisync", "move", "moveto", "purge"} & set(verbs)
    for number, args in enumerate(calls):
        if verbs[number] == "copy" and args[-1].startswith("qmx_lane:"):
            assert calls[number + 1][-1] == args[-1], "every arrival is checked with lsf"
            assert "lsf" in calls[number + 1]
    assert list((holder / "packs").rglob("*.pack"))
    assert len(list((holder / "snapshots").rglob("manifest.jsonl"))) == 1
    assert (holder / "backup.toml").is_file()


@needs_rclone
def test_a_restore_from_an_rclone_storage_fetches_one_pack_at_a_time_and_counts_its_steps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout, runner, storage, _ = lane(tmp_path)
    run_round(layout, Plan(storages=(storage,)), now=NOW, floor=0, rclone=runner)
    repo = cast("RcloneRepository", open_storage(storage, layout, rclone=runner))
    held: list[int] = []
    real = RcloneRepository.local_pack

    def counted(self: RcloneRepository, name: str) -> Path:
        found = real(self, name)
        held.append(len(list(self.fetched.glob("*.pack"))))
        return found

    monkeypatch.setattr(RcloneRepository, "local_pack", counted)
    steps: list[tuple[str, int, int]] = []

    def heard(step: str, *, done: int = 0, total: int = 0) -> None:
        steps.append((step, done, total))

    fresh = filled_folder(tmp_path / "fresh", files=0, stores=0, secrets=False)
    stamp = repo.copies()[-1]
    staged = restore.stage(fresh.layout, repo, stamp, replace=True, keep_free=0, progress=heard)

    fetching = [s for s in steps if s[0] == f"fetching your copy from {repo.where}"]
    placing = [s for s in steps if s[0] == "placing the copy's files"]
    assert held and max(held) == 1
    assert not list(repo.fetched.glob("*.pack"))
    assert fetching[0][1:] == (0, fetching[-1][2]) and fetching[-1][1] == fetching[-1][2] > 0
    assert placing[-1][1] == placing[-1][2]
    assert staged.files == len(repo.manifest(stamp).entries)
    for entry in repo.manifest(stamp).entries:
        placed = staged.folder / entry.path
        assert hashlib.sha256(placed.read_bytes()).hexdigest() == entry.sha256


class Answering:
    """A runner that answers every call the same way, as rclone does when the storage is offline
    or its sign-in expired."""

    def __init__(self, failure: Failure, line: str) -> None:
        self.ran = Ran(1, line, failure)
        self.record: list[Sequence[str]] = []

    def run(self, args: Sequence[str], *, secrets: Mapping[str, str] | None = None) -> Ran:
        self.record.append(list(args))
        return self.ran

    def secrets_for(self, remote: str, option: str, reference: str) -> dict[str, str]:
        return {}


@pytest.mark.parametrize(
    ("failure", "result", "line"),
    [
        (
            "signin",
            "refused",
            "sign in to gdrive again in Settings, Sync to my storage; This PC's copies go on",
        ),
        (
            "offline",
            "skipped",
            "gdrive was not reached; check the connection. This PC's copies go on, and QMX tries "
            "it again at its next due round",
        ),
    ],
)
def test_an_rclone_storage_that_is_offline_or_needs_a_sign_in_says_so_and_this_pc_goes_on(
    tmp_path: Path, failure: Failure, result: str, line: str
) -> None:
    filled = filled_folder(tmp_path / "QMX", files=2, secrets=False)
    storage = Storage("gdrive", "gdrive", "rclone", None, remote="qmx_gdrive", type="drive")
    runner = Answering(failure, "needs you to sign in again")

    report = run_round(
        filled.layout,
        Plan(storages=(storage,)),
        now=NOW,
        floor=0,
        rclone=cast("Rclone", runner),
    )

    assert [(p.id, p.result) for p in report.places] == [("quick", "copied"), ("gdrive", result)]
    assert report.places[1].line == line
    assert report.places[1].failure == failure
