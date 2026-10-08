from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest

from qmx_control.backup import MAX_BYTES, weekly_backup
from qmx_control.models import ControlError, LibraryInput
from qmx_control.service import ControlService


def git(directory: Path, *args: str) -> str:
    binary = shutil.which("git")
    assert binary is not None
    result = subprocess.run(
        [binary, "-C", str(directory), *args],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return result.stdout.strip()


def test_backup_restores_wal_and_excludes_bulk_secrets_and_large_files(tmp_path: Path) -> None:
    home = tmp_path / "home"
    service = ControlService(home)
    saved = service.library_save(
        LibraryInput(title="small", kind="note", content={"text": "saved"})
    )
    remote = tmp_path / "backup.git"
    git(tmp_path, "init", "--bare", str(remote))
    service.settings_put("backup", {"repository": str(remote)})
    definition = home / "definitions" / "small"
    definition.mkdir(parents=True)
    (definition / "app.toml").write_text('id="small"')
    (definition / ".env").write_text("PRIVATE_VALUE=secret")
    (home / "market.parquet").write_bytes(b"bulk")
    (home / "oauth.json").write_text('{"token":"do-not-copy"}')
    big = home / "definitions" / "big.json"
    with big.open("wb") as stream:
        stream.truncate(MAX_BYTES + 1)
    with closing(sqlite3.connect(home / "memory.db")) as memory:
        memory.execute("PRAGMA journal_mode=WAL")
        memory.execute("PRAGMA wal_autocheckpoint=0")
        memory.execute("CREATE TABLE memories(value TEXT)")
        memory.execute("INSERT INTO memories VALUES('precious')")
        memory.commit()
        result = service.backup_weekly(dry_run=True)
    included = result["included"]
    assert isinstance(included, list)
    assert {
        "memory.db",
        "library.db",
        "runs.db",
        "settings.toml",
        "definitions/small/app.toml",
    } <= set(included)
    assert "market.parquet" not in included
    assert "definitions/big.json" not in included
    assert not any(str(path).startswith("artifacts/") for path in included)
    tree = git(remote, "ls-tree", "-r", "--name-only", "HEAD")
    assert "oauth.json" not in tree and ".env" not in tree
    assert "parquet" not in tree and "artifacts" not in tree and "big.json" not in tree
    checkout = tmp_path / "restore"
    git(tmp_path, "clone", str(remote), str(checkout))
    with closing(sqlite3.connect(checkout / "snapshot/memory.db")) as restored:
        assert restored.execute("SELECT value FROM memories").fetchone()[0] == "precious"
    with closing(sqlite3.connect(checkout / "snapshot/library.db")) as catalog:
        raw = catalog.execute("SELECT data FROM items WHERE id=?", (saved["id"],)).fetchone()[0]
        assert json.loads(raw)["sha256"] == saved["sha256"]
    assert not (home / "weekly-backup.lock").exists()
    assert not (home / "weekly-backup.json").exists()


def test_backup_requires_configuration_and_local_bare_dry_run(tmp_path: Path) -> None:
    service = ControlService(tmp_path / "home")
    with pytest.raises(ControlError, match="Settings"):
        service.backup_weekly()
    service.settings_put("backup", {"repository": str(tmp_path)})
    with pytest.raises(ControlError, match="bare"):
        service.backup_weekly(dry_run=True)
    with pytest.raises(ControlError, match="owner/private-repo"):
        service.backup_weekly()


def test_backup_refuses_a_public_repo_before_snapshotting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    ControlService(home)
    def which(name: str) -> str:
        return name

    monkeypatch.setattr("qmx_control.backup.shutil.which", which)
    calls: list[list[str]] = []

    def call(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="false\n", stderr="")

    monkeypatch.setattr("qmx_control.backup.subprocess.run", call)
    with pytest.raises(ControlError, match="private"):
        weekly_backup(home, "owner/public")
    assert len(calls) == 1
    assert calls[0][calls[0].index("--hostname") + 1] == "github.com"
    assert not (home / "weekly-backup.json").exists()
    assert not (home / "weekly-backup.lock").exists()


def test_backup_weekly_due_guard_and_failed_snapshot_releases_lock(tmp_path: Path) -> None:
    home = tmp_path / "home"
    ControlService(home)
    remote = tmp_path / "bare.git"
    git(tmp_path, "init", "--bare", str(remote))
    (home / "memory.db").write_bytes(b"not a database")
    with pytest.raises(sqlite3.DatabaseError):
        weekly_backup(home, str(remote), dry_run=True)
    assert not (home / "weekly-backup.lock").exists()
    from datetime import UTC, datetime

    completed = datetime.now(UTC).isoformat()
    (home / "weekly-backup.json").write_text(json.dumps({"completed": completed}))
    assert weekly_backup(home, "unused/unused") == {"status": "not_due", "completed": completed}
