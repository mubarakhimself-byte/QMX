"""Check a unit document at layers A to F and name every problem: `python -m qmx_tools.unit_check`.

The `unit_check` row and this command answer with the same `qmx.check/1` result, plus `notes`,
the lines `gather` adds about where the check's inputs came from (Part A AD-117). The command
reads a file, or standard input for `-`, prints the result as one line of JSON, and exits 0 when
the unit passes and 1 when it does not or cannot be read. It opens no Library, so it checks
against QML's own blocks; the row checks against the Library's as well.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from qml.door import check

from qmx_tools.gather import gather

if TYPE_CHECKING:
    from collections.abc import Sequence

    from qmx_library.store import Store

PASSED = 0
FAILED = 1


def checked(
    store: Store | None, document: object, previous_problem_set: str | None = None
) -> dict[str, object]:
    """`document`'s check result with what `gather` found in `store`, and gather's notes."""
    found = gather(store, document)
    result = check(document, found.context, previous_problem_set)
    return {**result.to_json(), "notes": list(found.warnings)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m qmx_tools.unit_check", description="Check a unit document at A to F."
    )
    parser.add_argument("document", help="a unit document's JSON file, or - for standard input")
    parser.add_argument(
        "--previous", help="the problem_set of the last check, to learn no_progress"
    )
    given = parser.parse_args(argv)
    try:
        text = (
            sys.stdin.read() if given.document == "-" else Path(given.document).read_text("utf-8")
        )
        document: object = json.loads(text)
    except (OSError, UnicodeDecodeError, ValueError) as unreadable:
        print(f"{given.document} does not read as JSON: {unreadable}", file=sys.stderr)
        return FAILED
    result = checked(None, document, given.previous)
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return PASSED if result["verdict"] == "pass" else FAILED


if __name__ == "__main__":
    raise SystemExit(main())
