"""The weekly snapshot of the small stores: the job the control plane's maintenance loop ran, now
one engine run. The repository is `backup.repository` in Settings; a home without one backs up
nothing and says so. A local bare repository is the dry-run path `weekly_backup` itself keeps for
tests. A failed snapshot is the `maintenance:backup` incident."""

import json
import os
import sqlite3
import sys
import tomllib
from datetime import UTC, datetime
from pathlib import Path

from qmx_control.backup import weekly_backup
from qmx_control.models import ControlError

from qmx_engine.ledger.inbox_table import InboxTable
from qmx_engine.workers.zones import home_of

SIGNATURE = "maintenance:backup"

given = json.load(sys.stdin).get("in") or {}
home = home_of(Path(os.environ["QMX_WORK_SHARED"]))
settings = home / "settings.toml"
backup = tomllib.loads(settings.read_text("utf-8")).get("backup", {}) if settings.exists() else {}
repository = backup.get("repository") if isinstance(backup, dict) else None
if not repository:
    print(json.dumps({"status": "not_configured"}))
    raise SystemExit(0)
try:
    dry_run = bool(given.get("dry_run")) or Path(str(repository)).is_dir()
    result = weekly_backup(home, str(repository), dry_run=dry_run)
except (ControlError, OSError, sqlite3.Error) as error:
    cause = error.document()["error"]["message"] if isinstance(error, ControlError) else str(error)
    with InboxTable.open(home) as table:
        table.incident(
            "maintenance",
            SIGNATURE,
            "weekly backup failed",
            cause,
            at=datetime.now(UTC).isoformat(),
        )
    print(json.dumps({"status": "failed", "cause": cause}))
    raise SystemExit(1) from error
print(json.dumps(result))
