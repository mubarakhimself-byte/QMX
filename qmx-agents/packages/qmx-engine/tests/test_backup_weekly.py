"""The weekly backup template's one step, run the way the engine runs it: a home with a
repository snapshots, a home without one says so, and a failed snapshot is one
`maintenance:backup` incident."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.templates.catalog import PACK

SCRIPT = PACK / "backup-weekly" / "scripts" / "backup.py"


def run(home: Path, **given: object) -> subprocess.CompletedProcess[str]:
    shared = home.with_name(f"{home.name}.zones") / "run-1" / "work"
    shared.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "QMX_WORK_SHARED": str(shared), "QMX_RUN_ID": "run-1"}
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT)],
        input=json.dumps({"in": given}),
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
        check=False,
    )


def test_the_step_snapshots_the_home_to_the_repository(tmp_path: Path) -> None:
    git = shutil.which("git")
    assert git is not None
    repository = tmp_path / "backup.git"
    subprocess.run([git, "init", "--bare", str(repository)], check=True, capture_output=True)
    home = tmp_path / "home"
    home.mkdir()
    (home / "settings.toml").write_text(
        f'[backup]\nrepository = "{repository.as_posix()}"\n', encoding="utf-8"
    )

    result = run(home)

    body = json.loads(result.stdout)
    assert (result.returncode, body["status"], body["included"]) == (
        0,
        "dry_run",
        ["settings.toml"],
    )
    assert len(body["commit"]) == 40


def test_a_home_without_a_repository_backs_up_nothing(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()

    result = run(home)

    assert (result.returncode, json.loads(result.stdout)) == (0, {"status": "not_configured"})


def test_a_failed_snapshot_files_one_maintenance_incident(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    (home / "settings.toml").write_text(
        '[backup]\nrepository = "not/a/bare/repository"\n', encoding="utf-8"
    )

    result = run(home, dry_run=True)

    assert (result.returncode, json.loads(result.stdout)["status"]) == (1, "failed")
    with InboxTable.open(home) as table:
        incident = table.open_incident("maintenance")
    assert incident is not None
    assert (incident.trigger_id, incident.signature, incident.count) == (
        "maintenance",
        "maintenance:backup",
        1,
    )
