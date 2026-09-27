"""Repo-root launcher: ``python tools/ui_factory_cli.py <command>``."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ui_factory.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
