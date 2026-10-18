"""`python -m qmx_engine`: the engine's own command line."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from qmx_engine.definition.folder import content_hash, load
from qmx_engine.definition.validate import validate
from qmx_engine.ledger.store import Reader, ledger_path


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
    ledger = commands.add_parser("ledger", help="read the run ledger")
    ledger_commands = ledger.add_subparsers(dest="ledger_command", required=True)
    stats = ledger_commands.add_parser(
        "stats", help="print the schema version, the SQLite version and the event count"
    )
    stats.add_argument("--home", type=Path, required=True)
    return cli


def ledger_stats(home: Path) -> int:
    path = ledger_path(home)
    if not path.exists():
        print(f"no ledger at {path}")
        return 1
    with Reader(path) as reader:
        stats = reader.stats()
    print(f"schema_version {stats.schema_version}")
    print(f"sqlite_version {stats.sqlite_version}")
    print(f"events {stats.events}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "ledger":
        return ledger_stats(args.home)
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
