"""No key, token or login file is ever in a copy in clear (design 62 C1 and C4, ruling 135):
every byte of the quick undo and of a target is searched for each planted value."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from backup_fixtures import SECRETS, filled_folder

from qmx_home.backup.plan import Plan, Target
from qmx_home.backup.round import run_round


def test_no_planted_secret_value_is_anywhere_in_the_quick_undo_or_on_a_target(
    tmp_path: Path,
) -> None:
    filled = filled_folder(tmp_path / "QMX")
    plan = Plan(targets=(Target("usb", "folder", tmp_path / "usb"),))

    report = run_round(filled.layout, plan, now=datetime(2026, 10, 27, tzinfo=UTC), floor=0)

    assert report.result == "copied"
    assert sorted(filled.planted) == sorted([*SECRETS, "../keys/vault.key"])
    searched = [
        path
        for folder in (filled.layout.backups / "quick", tmp_path / "usb")
        for path in folder.rglob("*")
        if path.is_file()
    ]
    assert len(searched) > 60
    for path in searched:
        held = path.read_bytes()
        found = [name for name, value in filled.planted.items() if value in held]
        assert found == [], f"{path} holds {found}"
