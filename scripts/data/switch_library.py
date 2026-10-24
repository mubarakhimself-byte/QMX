"""Switch a home from Library B to the one Library store (MIGRATION steps 0, 2, 4 and 6).

The real step: after the stack is landed (gate G-LAND) and P-TORN and P-REHEARSE passed, the
coordinator runs this on `~/.qmx` while no host answers there. It refuses when a host still holds
the home, because a save during the import would land in the store and never reach `library.db`.

What it does, all of it in `qmx_library.migrate.from_library_b.switch_over`:

1. Step 0: `library.db`, `artifacts.db` and `artifacts/` are frozen under `<home>/migration/pre/`,
   with the acceptance counts.
2. Steps 2 and 4: the frozen items import into `<home>/library/`, with the known test junk
   filtered by id (fix-check 58, N18) and the app artifacts and definitions beside them.
3. The store is verified against step 0's numbers minus the filtered ids: counts per kind, version
   chains, links, memo rows, blob hashes and bytes.
4. Step 6: only after that, `library.db`, `artifacts.db` and `artifacts/` move read-only into
   `<home>/migration/retired/`. A store that fails verification leaves every old file where it was.

The report, every count and the filtered ids, is printed as JSON and written to
`<home>/migration/switch-report.json`.

    uv run --no-sync --project qmx-agents python scripts/data/switch_library.py --home ~/.qmx
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from qmx_control.library import Library
from qmx_engine.ledger import redact
from qmx_library.migrate.from_library_b import switch_over
from qmx_library.port import LibraryRefused

HOME = Path.home() / ".qmx"
REFUSED = 2
"""Exit code when a host still answers on the home: nothing was read, imported or moved."""


def host_answers(home: Path) -> str | None:
    """The store's writer lock, held by whoever serves the home; None when the home is quiet."""
    library = Library(home)
    try:
        opened = library.store
    except LibraryRefused as refused:
        return str(refused)
    finally:
        library.close()
    return None if opened is not None else "unreachable"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=HOME, help="the QMX home to switch")
    arguments = parser.parse_args(argv)
    home = arguments.home.expanduser().resolve()
    if not (home / "library.db").is_file():
        print(f"nothing to switch: {home} holds no library.db")
        return 0
    busy = host_answers(home)
    if busy is not None:
        print(f"refused: a host still answers on {home}: {busy}")
        return REFUSED
    switched = switch_over(home, redactor=redact)
    report = switched.report()
    target = home / "migration" / "switch-report.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=1, sort_keys=True))
    if not switched.ok:
        print("the store failed verification; every old file is still in place", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
