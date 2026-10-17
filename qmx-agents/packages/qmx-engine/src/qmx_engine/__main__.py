"""`python -m qmx_engine`: the engine's own command line."""

from __future__ import annotations

import argparse
import asyncio
import json
import tempfile
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from qmx_engine.definition.folder import content_hash, load
from qmx_engine.definition.validate import checked, validate
from qmx_engine.ledger.store import Ledger, Reader, ledger_path
from qmx_engine.runner import Engine, Outcome, Refused, new_run_id
from qmx_engine.service.api import explain_run
from qmx_engine.service.context import Refused as ServiceRefused
from qmx_engine.service.explain import text

EXIT: dict[str, int] = {"passed": 0, "failed": 1, "waiting": 2, "interrupted": 3}


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
    run = commands.add_parser("run", help="start one run from a workflow folder")
    run.add_argument("folder", type=Path)
    run.add_argument("--mode", choices=("test", "live"), default="test")
    run.add_argument("--home", type=Path, help="the QMX home; a fresh temporary one when left out")
    run.add_argument("--inputs", default="null", help="the run's inputs as JSON")
    run.add_argument("--run-id")
    resume = commands.add_parser("resume", help="pick a run up again from the ledger")
    resume.add_argument("run_id")
    resume.add_argument("--home", type=Path, required=True)
    why = commands.add_parser("explain", help="print what a run did, node by node, and why")
    why.add_argument("run_id")
    why.add_argument("--home", type=Path, required=True)
    why.add_argument("--json", action="store_true", help="print the explain document as JSON")
    return cli


def report(outcome: Outcome) -> int:
    if outcome.status == "passed":
        print(f"run finished {outcome.outputs_hash}")
    else:
        print(f"run {outcome.status}: {outcome.reason}")
    return EXIT[outcome.status]


async def start(args: argparse.Namespace) -> int:
    found = checked(args.folder)
    if isinstance(found, list):
        for problem in found:
            print(f"{problem.code} {problem.path} {problem.message}")
        return 1
    home: Path = args.home or Path(tempfile.mkdtemp(prefix="qmx-engine-"))
    run_id = args.run_id or new_run_id(datetime.now(UTC))
    print(f"run {run_id} home {home}", flush=True)
    with Ledger.open(home) as ledger:
        engine = Engine(home, ledger)
        outcome = await engine.start(
            args.folder, found[1], mode=args.mode, inputs=json.loads(args.inputs), run_id=run_id
        )
        await engine.settle()
    return report(outcome)


async def resume(args: argparse.Namespace) -> int:
    print(f"run {args.run_id} resumed", flush=True)
    with Ledger.open(args.home) as ledger:
        engine = Engine(args.home, ledger)
        try:
            outcome = await engine.resume(args.run_id)
        except Refused as refused:
            print(f"refused: {refused}")
            return 1
        await engine.settle()
    return report(outcome)


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


def explain(args: argparse.Namespace) -> int:
    try:
        document = explain_run(args.home, args.run_id)
    except ServiceRefused as refused:
        print(f"refused: {refused}")
        return 1
    if args.json:
        print(json.dumps(document, indent=2))
    else:
        for line in text(document):
            print(line)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "explain":
        return explain(args)
    if args.command == "ledger":
        return ledger_stats(args.home)
    if args.command == "run":
        return asyncio.run(start(args))
    if args.command == "resume":
        return asyncio.run(resume(args))
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
