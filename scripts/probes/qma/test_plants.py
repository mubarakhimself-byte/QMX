# ruff: noqa: S101
from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from plants import Locked, exclusive, heal, restore, snapshot

EARLIER = '{"theme": "dark"}'
PLANTED = '{"apiKeyHelper": "echo fake", "permissions": {"allow": ["Bash(*)"]}}'


def plant(root: Path) -> Path:
    backup = root.parent / "backup.json"
    settings = root / "settings.json"
    skill = root / "skills" / "hp0-plant-skill" / "SKILL.md"
    snapshot(backup, root, [settings, skill], [root / "plugins" / "cache" / "hp0-local"])
    skill.parent.mkdir(parents=True)
    skill.write_text("planted", encoding="utf-8")
    (root / "plugins" / "cache" / "hp0-local").mkdir(parents=True)
    settings.write_text(PLANTED, encoding="utf-8")
    return backup


def home(tmp_path: Path) -> Path:
    root = tmp_path / "claude"
    (root / "plugins").mkdir(parents=True)
    (root / "settings.json").write_text(EARLIER, encoding="utf-8")
    return root


def test_restore_after_a_crash_mid_plant_puts_the_home_back(tmp_path: Path) -> None:
    root = home(tmp_path)
    backup = plant(root)
    assert restore(backup) == []
    assert (root / "settings.json").read_text(encoding="utf-8") == EARLIER
    assert sorted(p.name for p in root.iterdir()) == ["plugins", "settings.json"]
    assert list((root / "plugins").iterdir()) == []
    assert not backup.exists()
    assert restore(backup) == []


def test_settings_come_back_even_when_a_planted_folder_cannot_be_removed(tmp_path: Path) -> None:
    root = home(tmp_path)
    backup = plant(root)
    locked = root / "skills" / "hp0-plant-skill" / "scanner.tmp"
    with locked.open("w"):
        failures = restore(backup)
    assert (root / "settings.json").read_text(encoding="utf-8") == EARLIER
    assert len(failures) == 1
    assert backup.exists()
    assert restore(backup) == []
    assert not (root / "skills").exists()


def test_snapshot_refuses_to_overwrite_an_unrestored_backup(tmp_path: Path) -> None:
    root = home(tmp_path)
    backup = plant(root)
    refused = False
    try:
        snapshot(backup, root, [root / "settings.json"], [])
    except FileExistsError:
        refused = True
    assert refused
    assert restore(backup) == []
    assert (root / "settings.json").read_text(encoding="utf-8") == EARLIER


@contextmanager
def live_process() -> Generator[int]:
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        yield process.pid
    finally:
        process.kill()
        process.wait()


def dead_pid() -> int:
    process = subprocess.Popen([sys.executable, "-c", "pass"])
    process.wait()
    return process.pid


def test_a_second_holder_is_refused_while_the_first_holder_lives(tmp_path: Path) -> None:
    lock = tmp_path / "plant.lock"
    with live_process() as pid:
        lock.write_text(str(pid), encoding="utf-8")
        refused: int | None = None
        try:
            with exclusive(lock):
                pass
        except Locked as error:
            refused = error.pid
        assert refused == pid
        assert lock.read_text(encoding="utf-8") == str(pid)


def test_a_dead_holders_lock_is_reclaimed_and_released(tmp_path: Path) -> None:
    lock = tmp_path / "plant.lock"
    lock.write_text(str(dead_pid()), encoding="utf-8")
    with exclusive(lock):
        assert lock.read_text(encoding="utf-8") == str(os.getpid())
    assert not lock.exists()


def test_heal_leaves_a_live_runs_plant_alone_and_restores_it_once_that_run_is_dead(
    tmp_path: Path,
) -> None:
    root = home(tmp_path)
    backup = plant(root)
    lock = tmp_path / "plant.lock"
    with live_process() as pid:
        lock.write_text(str(pid), encoding="utf-8")
        refused: int | None = None
        try:
            heal(backup, lock)
        except Locked as error:
            refused = error.pid
        assert refused == pid
        assert (root / "settings.json").read_text(encoding="utf-8") == PLANTED
        assert backup.exists()
    assert heal(backup, lock) == []
    assert (root / "settings.json").read_text(encoding="utf-8") == EARLIER
    assert not backup.exists()
    assert not lock.exists()


def test_heal_without_a_backup_changes_nothing(tmp_path: Path) -> None:
    root = home(tmp_path)
    credentials = root / ".credentials.json"
    credentials.write_text("fake-login-not-a-credential", encoding="utf-8")
    assert heal(tmp_path / "backup.json", tmp_path / "plant.lock") == []
    assert sorted(p.name for p in root.iterdir()) == [
        ".credentials.json",
        "plugins",
        "settings.json",
    ]
    assert credentials.read_text(encoding="utf-8") == "fake-login-not-a-credential"


def test_restore_never_touches_the_login_even_when_the_backup_names_it(tmp_path: Path) -> None:
    root = home(tmp_path)
    credentials = root / ".credentials.json"
    credentials.write_text("fake-login-not-a-credential", encoding="utf-8")
    backup = tmp_path / "backup.json"
    backup.write_text(json.dumps({"files": {str(credentials): None}, "made": []}), encoding="utf-8")
    failures = restore(backup)
    assert len(failures) == 1
    assert credentials.read_text(encoding="utf-8") == "fake-login-not-a-credential"
