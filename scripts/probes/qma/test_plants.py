# ruff: noqa: S101
from __future__ import annotations

from pathlib import Path

from plants import restore, snapshot

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
