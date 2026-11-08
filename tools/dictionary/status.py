"""Compute each dictionary entry's status from its evidence (Part A AD-113); nobody types it.

    uv run python tools/dictionary/status.py [BLOCKS ...]
    uv run --project qmx-agents --no-sync python tools/dictionary/status.py --library HOME

``BLOCKS`` holds ``<entry_id>/<version>/entry.json`` and ``block.py``, by default QML's own. An
entry's golden cases are read from the repository path its ``golden.cases`` names. ``--library``
reads every entry in the Library of the QMX folder ``HOME`` instead, with its ``code`` and
``golden`` blobs, and writes each status on its object as the ``status`` annotation; it needs
the qmx-agents environment and a Library no running host holds.

One line per entry, ``<pin> <status>``, then a line per problem and per missing piece. The exit
is 1 when any entry is refused or has a problem.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from qml.catalogue.entry import Computed, compute_status

import qml

ROOT = Path(__file__).resolve().parents[2]
STDLIB = Path(qml.__file__).resolve().parent / "blocks" / "stdlib"


def _golden(entry: dict[str, object]) -> object:
    declared = entry.get("golden")
    cases = cast("dict[str, object]", declared).get("cases") if isinstance(declared, dict) else None
    path = ROOT / cases if isinstance(cases, str) else None
    return json.loads(path.read_text("utf-8")) if path is not None and path.is_file() else None


def folder_statuses(blocks: Path) -> list[tuple[str, Computed]]:
    """Each entry under ``blocks`` with its computed status, in pin order."""
    found: list[tuple[str, Computed]] = []
    for face in sorted(blocks.glob("*/*/entry.json")):
        entry = cast("dict[str, object]", json.loads(face.read_text("utf-8")))
        code = face.parent / "block.py"
        source = code.read_bytes() if code.is_file() else None
        pin = f"{face.parent.parent.name}@{face.parent.name}"
        found.append((pin, compute_status(entry, source, _golden(entry))))
    return found


def library_statuses(home: Path) -> list[tuple[str, Computed]]:
    """Each Library entry head in ``home`` with its status, written as its annotation. The
    Library lives in the qmx-agents environment, so it is imported only here."""
    store = importlib.import_module("qmx_control.library").open_store(home)
    write = importlib.import_module("qmx_tools.functions").write_entry_statuses
    try:
        written = cast("list[tuple[str, str, Computed]]", write(store))
        return [(f"{item} on {ref}", c) for item, ref, c in written]
    finally:
        store.close()


def report(found: Sequence[tuple[str, Computed]]) -> tuple[list[str], int]:
    lines: list[str] = []
    failed = False
    for where, computed in found:
        lines.append(f"{where} {computed.annotation()['value']}")
        lines += [f"  problem {p.where}: {p.message}" for p in computed.problems]
        lines += [f"  missing {m}" for m in computed.missing]
        failed = failed or computed.status is None or bool(computed.problems)
    return lines, 1 if failed else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute each dictionary entry's status.")
    parser.add_argument("blocks", nargs="*", type=Path, help="block folders; QML's own if none")
    parser.add_argument("--library", type=Path, help="a QMX folder whose Library entries to mark")
    args = parser.parse_args(argv)
    if args.library is not None:
        found = library_statuses(cast("Path", args.library))
    else:
        folders = cast("list[Path]", args.blocks) or [STDLIB]
        found = [row for folder in folders for row in folder_statuses(folder)]
    lines, code = report(found)
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
