"""`python -m qmx_control weekly-backup` runs the backup. The host is `python -m qmx_host`."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qmx_control.server import default_home
from qmx_control.service import ControlService


def main() -> int:
    parser = argparse.ArgumentParser(prog="qmx-control")
    parser.add_argument("command", choices=["weekly-backup"])
    parser.add_argument(
        "--dry-run", action="store_true", help="Rehearse backup against a local bare repo"
    )
    parser.add_argument("--home", type=Path, default=default_home())
    args = parser.parse_args()
    home: Path = args.home.resolve()
    home.mkdir(parents=True, exist_ok=True)
    print(json.dumps(ControlService(home).backup_weekly(dry_run=args.dry_run)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
