"""Check the first content wave's seed folders and land them into a Library (A13).

    uv run python tools/dictionary/land_seed.py [FOLDER ...]
    uv run --project qmx-agents --no-sync python tools/dictionary/land_seed.py --home HOME

Each folder under ``qml/catalogue-seed/wave-1/`` holds one ``qmx.entry/1`` document per entry,
``<entry_id>.json``, for the entries that have no QML code; the entries with code live once,
beside their ``block.py`` in QML's stdlib. With no option the script checks every document and
prints each one's computed status, then exits 1 on a refused entry or a problem. ``--home``
lands every folder into the Library of the QMX folder ``HOME`` as the host does at each start
(``qmx_host.first_start.land_wave``): one collection per folder, each entry a draft, once per
store, keyed by the folder's fingerprint; it needs the qmx-agents environment and a Library no
running host holds.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from qml.catalogue.entry import compute_status

ROOT = Path(__file__).resolve().parents[2]
WAVE = ROOT / "qml" / "catalogue-seed" / "wave-1"


def check(folders: Sequence[Path]) -> tuple[list[str], int]:
    """One line per document, ``<family>/<pin> <status>``, then its problems and gaps."""
    lines: list[str] = []
    failed = False
    for folder in folders:
        for path in sorted(folder.glob("*.json")):
            entry = cast("dict[str, object]", json.loads(path.read_text("utf-8")))
            computed = compute_status(entry)
            pin = f"{entry.get('entry_id')}@{entry.get('version')}"
            lines.append(f"{folder.name}/{pin} {computed.annotation()['value']}")
            lines += [f"  problem {p.where}: {p.message}" for p in computed.problems]
            lines += [f"  missing {m}" for m in computed.missing]
            failed = failed or computed.status is None or bool(computed.problems)
    return lines, 1 if failed else 0


def land(home: Path) -> str:
    """Land every wave folder into the Library of ``home``. The host lives in the qmx-agents
    environment, so it is imported only here, and its checkers are registered first, so each
    draft meets the entry checker a start's put meets."""
    store = importlib.import_module("qmx_control.library").open_store(home)
    try:
        importlib.import_module("qmx_host.host").register_checkers(store)
        landed = importlib.import_module("qmx_host.first_start").land_wave(store, WAVE)
    finally:
        store.close()
    lines = [str(family) for family in cast("list[object]", landed)]
    return "\n".join(lines) or "nothing new: the wave is in this Library already"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check and land the first wave's seed folders.")
    parser.add_argument("folders", nargs="*", type=Path, help="seed folders; every wave folder")
    parser.add_argument("--home", type=Path, help="land the wave into this QMX folder's Library")
    args = parser.parse_args(argv)
    if args.home is not None:
        print(land(cast("Path", args.home)))
        return 0
    given = cast("list[Path]", args.folders)
    folders = given or sorted(p for p in WAVE.iterdir() if p.is_dir())
    lines, code = check(folders)
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
