"""`python -m qmx_engine`: the engine's own command line."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from qmx_engine.definition.folder import content_hash, load
from qmx_engine.definition.validate import validate


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(
        prog="python -m qmx_engine", description="The QMX workflow engine."
    )
    commands = cli.add_subparsers(dest="command", required=True)
    check = commands.add_parser(
        "validate", help="print a workflow folder's content hash, or every problem in it"
    )
    check.add_argument("folder", type=Path)
    check.add_argument(
        "--publish", action="store_true", help="also refuse note and unconnected nodes"
    )
    return cli


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    folder = load(args.folder)
    problems = validate(folder, publish=args.publish)
    for problem in problems:
        print(f"{problem.code} {problem.path} {problem.message}")
    if problems:
        return 1
    print(f"ok {content_hash(folder)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
