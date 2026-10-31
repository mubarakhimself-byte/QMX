"""`python -m qmx_engine`: the engine's own command line."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from qma.harness import Harness, QmxHome
from qmx_control.server import local_token
from qmx_control.service import ControlService
from qmx_home import NoQmxFolder, resolve
from qmx_library.adapter import EngineLibraryAdapter
from qmx_library.port import LibraryRefused as StoreRefused
from qmx_library.store import Store

from qmx_engine.definition.folder import content_hash, load
from qmx_engine.definition.model import Workflow
from qmx_engine.definition.registry import REGISTRY
from qmx_engine.definition.validate import checked, validate
from qmx_engine.ledger import redact
from qmx_engine.ledger.spans import Span
from qmx_engine.ledger.store import Ledger, Reader, ledger_path
from qmx_engine.nodes.doctor import LlmDoctor
from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_engine.ports.library import LibraryRefused as EngineRefused
from qmx_engine.ports.settings import ControlSettings
from qmx_engine.runner import Engine, Outcome, Refused, new_run_id
from qmx_engine.service.api import EngineService, explain_run
from qmx_engine.service.context import Refused as ServiceRefused
from qmx_engine.service.explain import text
from qmx_engine.settings import DEFAULTS, Setting
from qmx_engine.templates.catalog import CATALOG, Template, find
from qmx_engine.templates.install import install, listing
from qmx_engine.triggers import rows

EXIT: dict[str, int] = {"passed": 0, "failed": 1, "waiting": 2, "interrupted": 3}
HOST_STATE: Final = "control-process.json"
"""The record a running `qmx_host` keeps in the home (`qmx_host.host.STATE`): its pid and port."""
INSTALL_ROUTE: Final = "/api/templates/install"
"""The host's install door (`qmx_host.door.templates_router`)."""
INSTALLED: Final = frozenset({"published", "saved draft", "unchanged"})
REFUSED: Final = (StoreRefused, EngineRefused)

type Line = tuple[str, str, str, str]
"""One installed template as the command prints it: id, folder, action, detail."""


def homed(command: argparse.ArgumentParser) -> None:
    command.add_argument("--home", type=Path, help="the QMX folder; found when left out")
    command.add_argument(
        "--create", action="store_true", help="make the --home folder when it is missing"
    )


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
    homed(stats)
    run = commands.add_parser("run", help="start one run from a workflow folder")
    run.add_argument("folder", type=Path)
    run.add_argument(
        "--mode",
        choices=("test",),
        default="test",
        help="test only; a live run starts through the engine service (AD-11)",
    )
    homed(run)
    run.add_argument("--inputs", default="null", help="the run's inputs as JSON")
    run.add_argument("--run-id")
    run.add_argument(
        "--fake", action="store_true", help="answer model nodes with the fake provider; no spend"
    )
    resume = commands.add_parser("resume", help="pick a run up again from the ledger")
    resume.add_argument("run_id")
    homed(resume)
    triggers = commands.add_parser("triggers", help="read the trigger rows")
    trigger_commands = triggers.add_subparsers(dest="triggers_command", required=True)
    listed = trigger_commands.add_parser(
        "list", help="print each trigger's kind, next_fire_at and last_status"
    )
    homed(listed)
    why = commands.add_parser("explain", help="print what a run did, node by node, and why")
    why.add_argument("run_id")
    homed(why)
    why.add_argument("--json", action="store_true", help="print the explain document as JSON")
    pack = commands.add_parser("templates", help="list or install the template pack")
    pack_commands = pack.add_subparsers(dest="templates_command", required=True)
    shown = pack_commands.add_parser("list", help="print each template's status in the home")
    homed(shown)
    put = pack_commands.add_parser(
        "install", help="install the pack disabled: test and publish runnable ones, draft the rest"
    )
    homed(put)
    put.add_argument(
        "--template",
        action="append",
        dest="templates",
        metavar="ID",
        help="install only this template, by its id or an earlier id; repeat for more",
    )
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
    home: Path = args.home
    run_id = args.run_id or new_run_id(datetime.now(UTC))
    print(f"run {run_id} home {home} mode: {args.mode}", flush=True)
    harness: Harness | None = None
    settings: Mapping[str, Setting] = DEFAULTS
    if not args.fake and model_bearing(found[1]):
        control = ControlService(home)
        harness = await Harness.open(QmxHome(home), control=control)
        settings = ControlSettings(control).values()
    try:
        with Ledger.open(home) as ledger:
            port = HarnessAdapter(harness) if harness is not None else None
            engine = Engine(home, ledger, settings=settings, harness=port)
            engine.doctor = LlmDoctor.of(engine)
            outcome = await engine.start(
                args.folder,
                found[1],
                mode=args.mode,
                inputs=json.loads(args.inputs),
                run_id=run_id,
                fake=args.fake,
            )
            await engine.settle()
    finally:
        if harness is not None:
            await harness.close()
    for span in spans(home, run_id):
        if span.profile is not None:
            print(
                f"span {span.node_id} attempt {span.attempt} {span.status}: "
                f"{span.role} on {span.profile}/{span.model} tokens {span.tokens}"
            )
    return report(outcome)


def model_bearing(workflow: Workflow) -> bool:
    return any(
        (kind := REGISTRY.kind(node.type)) is not None and kind.model_bearing
        for node in workflow.nodes
    )


def spans(home: Path, run_id: str) -> list[Span]:
    with Reader.open(home) as reader:
        return reader.spans(run_id)


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


def list_triggers(home: Path) -> int:
    path = ledger_path(home)
    if not path.exists():
        print(f"no ledger at {path}")
        return 1
    with Reader(path) as reader:
        found = rows.triggers(reader.connection)
    for trigger in found:
        print(
            f"{trigger.id} {trigger.kind} {trigger.workflow_item}"
            f" next_fire_at={trigger.next_fire_at} last_status={trigger.last_status}"
        )
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


def host_port(home: Path) -> int | None:
    """The port the home's running host recorded, or None when no host has recorded one."""
    try:
        port = json.loads((home / HOST_STATE).read_text(encoding="utf-8"))["port"]
    except OSError, ValueError, KeyError, TypeError:
        return None
    return port if isinstance(port, int) else None


def through_host(home: Path, port: int, names: list[str] | None) -> list[Line] | None:
    """The install, run by the home's host on its loopback port with its bearer. None when no
    host answers there: the record of a host that died. No timeout, because an install's test
    runs take as long as their models do."""
    request = Request(
        f"http://127.0.0.1:{port}{INSTALL_ROUTE}",
        data=json.dumps({"templates": names}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {local_token(home)}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request) as reply:  # noqa: S310 - the port the home's own host recorded
            rows = cast(list[dict[str, str]], json.loads(reply.read()))
    except HTTPError:
        raise
    except URLError:
        return None
    return [(row["id"], row["folder"], row["action"], row["detail"]) for row in rows]


@contextmanager
def home_library(home: Path) -> Generator[EngineLibraryAdapter]:
    """The Library store the home's host serves, `<home>/library/`, for a command run while no
    host runs. A running host holds its writer lock, so this refuses rather than opening a second
    writer."""
    with Store.open(home / "library", redactor=redact) as store:
        yield EngineLibraryAdapter(store)


def list_templates(home: Path) -> int:
    try:
        with home_library(home) as library, EngineService.open(home, library=library) as svc:
            found = listing(svc)
    except REFUSED as refused:
        print(f"refused: {refused}")
        return 1
    for row in found:
        version = f" {row.version}" if row.version else ""
        print(f"{row.template.id:<4} {row.template.name:<42} {row.status}{version}")
    print(f"{len(found)} templates")
    return 0


def chosen(ids: Sequence[str] | None) -> list[Template] | str:
    """The templates `--template` names, the whole catalogue when none, or the first unknown id."""
    if ids is None:
        return list(CATALOG)
    picked: list[Template] = []
    for wanted in ids:
        try:
            picked.append(find(wanted))
        except KeyError:
            return wanted
    return picked


async def install_templates(home: Path, ids: Sequence[str] | None) -> int:
    """Through the running host's door when the home has one, so its one writer does the work;
    otherwise into `<home>/library/` here, with the harness open for the test runs' models."""
    templates = chosen(ids)
    if isinstance(templates, str):
        print(f"refused: no template {templates!r} in the catalogue")
        return 1
    port = host_port(home)
    lines: list[Line] | None = None
    if port is not None:
        try:
            lines = through_host(home, port, None if ids is None else [t.id for t in templates])
        except HTTPError as refused:
            print(f"refused: {refused.code} {refused.read().decode('utf-8', 'replace')}")
            return 1
    if lines is None:
        control = ControlService(home)
        harness = await Harness.open(QmxHome(home), control=control)
        try:
            with (
                home_library(home) as library,
                EngineService.open(
                    home,
                    library=library,
                    settings=ControlSettings(control),
                    harness=HarnessAdapter(harness),
                ) as svc,
            ):
                done = await install(svc, templates)
        except REFUSED as refused:
            print(f"refused: {refused}")
            return 1
        finally:
            await harness.close()
        lines = [(f.template.id, f.template.folder, f.action, f.detail) for f in done]
    for template_id, folder, action, detail in lines:
        print(f"{template_id:<4} {folder} {action}: {detail}")
    return 0 if all(line[2] in INSTALLED for line in lines) else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command != "validate":
        try:
            args.home = resolve(args.home, create=args.create).home
        except NoQmxFolder as missing:
            print(missing, file=sys.stderr)
            return 1
    if args.command == "templates":
        if args.templates_command == "list":
            return list_templates(args.home)
        return asyncio.run(install_templates(args.home, args.templates))
    if args.command == "explain":
        return explain(args)
    if args.command == "ledger":
        return ledger_stats(args.home)
    if args.command == "triggers":
        return list_triggers(args.home)
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
