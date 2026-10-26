"""Switch a home from Library B to the one Library store (MIGRATION steps 0, 2, 4 and 6).

The first start's bring-in (`python -m qmx_host bring-in`, design 62 F step 4) runs the same
`switch_over` on its copy of the old folder; this script is the same switch by hand, on the `data/`
of a QMX folder only, so an old folder is never switched in place. It refuses when a host still
holds the home, because a save during the import would land in the store and never reach
`library.db`.

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

    uv run --no-sync --project qmx-agents python scripts/data/switch_library.py --home D:/QMX/data
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from qmx_control.library import LIBRARY, WRITING
from qmx_engine.ledger import redact
from qmx_home.versions import folder_of
from qmx_library.migrate.from_library_b import switch_over
from qmx_library.port import LibraryRefused
from qmx_library.store import Store

REFUSED = 2
"""Exit code when a host still answers on the home, or the home is not a copy inside a QMX folder:
nothing was read, imported or moved."""


def host_answers(home: Path) -> str | None:
    """The store's writer lock, held by whoever serves the home; None when the home is quiet. The
    store is opened directly, because the Library refuses to open beside an unswitched
    `library.db`, which is exactly what this script switches."""
    try:
        Store.open(home / LIBRARY, redactor=WRITING, name="pc").close()
    except LibraryRefused as refused:
        return str(refused)
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--home", type=Path, required=True, help="the data/ of the QMX folder holding the copy"
    )
    arguments = parser.parse_args(argv)
    home = arguments.home.expanduser().resolve()
    if folder_of(home) is None:
        print(
            f"refused: {home} is not the data/ of a QMX folder. The switch runs only on a copy, "
            "so an old folder is never changed: python -m qmx_host bring-in copies it first"
        )
        return REFUSED
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
