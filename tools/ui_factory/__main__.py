"""``python -m ui_factory`` entry when ``tools/`` is on PYTHONPATH."""

from __future__ import annotations

from ui_factory.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
