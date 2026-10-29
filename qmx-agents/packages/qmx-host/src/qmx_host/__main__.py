"""`python -m qmx_host serve [--home <folder> [--create]] --port <port> [--role pc | node |
server] [--place <name>] [--library-root <path>] [--ui-origin <origin>]`, and `start`, `status`
and `stop` for a host in the background. Without `--home` the QMX folder is found by
`qmx_home.resolve`, and a missing folder is made only with `--create`. `--place` is the name he gave
a server in his place list, which `qmx node setup` writes into the server's unit. A `node` or
`server` host with neither it nor `[engine] host_name` refuses to start; This PC is always `pc`.

`server` is the role the server's unit runs: the same node work plus the Library service, because
on the server the one host process opens the store as its one writer and answers the Library routes
in process (AD-19, AD-26).

`backup [--home <folder>] [--target <id>]` runs one backup round in the foreground: the quick
undo and every place that is due, or only the place `--target` names, due or not. It prints each
place's line and exits 0 when it copied or had nothing to copy, and 1 when a place refused or
another round runs. It never imports the host, so it runs beside a host that serves the folder.

`first-start [--serve]`, `new`, `open`, `bring-in [--old <folder>]` and `restore` are the first
start's card (design 62 F): they run with no QMX folder yet and take the chosen one as `--home`.
A command pointed at his old folder, or given no folder while one sits at `~/.qmx`, names the
bring-in; `serve` and `start` refuse a folder holding an unswitched `library.db` or an unfinished
bring-in.

`restore --home <folder> --from <backup place> [--copy <date>] [--yes] [--replace] [--create]`
lists the place's copies when `--copy` is left out, prints what the copy replaces and changes
nothing without `--yes`, and with it restores the copy into the folder (a new one only with
`--create`). It exits 0 when it listed, showed or restored, 1 when a host serves the folder, and 2
when refused.

Before `serve` or `start`, a restore staged for the folder is finished (`qmx_home.backup.restore`),
before any store opens; one that cannot finish stops the start with its line and stays staged.
Then every store of the folder is read against this release (design 62 B2): a store opened
read-only is named on stderr, and a refused one stops the start with its name and the version it
needs. When a store upgrades, `serve` first takes a quick copy of the whole folder tagged
`before-upgrade` (design 62 B3); a copy that cannot be made is one line on stderr and the start
goes on.

Exit codes the desktop app branches on (loose strings P1, Appendix E): `serve`, `start`, `status`
and `stop` exit 3 when a first start is due (no QMX folder yet, only his old data, or an
unfinished bring-in; `serve` and `start` also for a folder whose restore did not finish) and 2 for
a folder found and refused or a staged restore that cannot finish. `first-start --serve` exits 4
when its port is taken, 0 after a handover with the handover line last on stdout, and 1 when it
stopped with no handover.

Order is the invariant: parse the arguments, read the keep list with the standard library, scrub
this process's environment, and only then import the harness, because the SDK reads `os.environ`
at every `connect()`.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import tomllib
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

from qma.boot import read_keep_names, scrub_process_env
from qmx_home import RESTORE_UNFINISHED, Layout, NoQmxFolder, resolve
from qmx_home.versions import check_open

if TYPE_CHECKING:
    from qmx_home.backup.plan import Plan
    from qmx_home.rclone import Rclone

    from qmx_host.first_start import Places

FIRST_START = ("first-start", "new", "open", "bring-in", "restore")
FIRST_START_DUE = 3
PORT_TAKEN = 4
HANDOVER_GRACE_S = 3
"""How long the card's server waits for open requests once it handed over."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m qmx_host")
    parser.add_argument(
        "command", choices=["serve", "start", "status", "stop", "backup", *FIRST_START]
    )
    parser.add_argument(
        "--home", type=Path, default=None, help="the QMX folder; found when left out"
    )
    parser.add_argument(
        "--old", type=Path, default=None, help="bring-in: the old folder; ~/.qmx when left out"
    )
    parser.add_argument(
        "--serve", action="store_true", help="first-start: serve the card's routes on --port"
    )
    parser.add_argument(
        "--again",
        action="store_true",
        help="bring-in: into the --home folder where it did not finish, clearing QMX's own copy",
    )
    parser.add_argument("--create", action="store_true", help="make the --home folder if missing")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--role", choices=["pc", "node", "server"], default="pc")
    parser.add_argument("--library-root", type=Path, default=None)
    parser.add_argument(
        "--place", default="", help="this machine's place name; setup passes it for a server"
    )
    parser.add_argument("--ui-origin", default="http://127.0.0.1:5173")
    parser.add_argument("--target", default=None, help="backup: only this backup place")
    parser.add_argument(
        "--from", dest="source", type=Path, default=None, help="restore: the backup place"
    )
    parser.add_argument("--copy", default=None, help="restore: the copy's date, as listed")
    parser.add_argument("--yes", action="store_true", help="restore: restore it, after the check")
    parser.add_argument(
        "--replace", action="store_true", help="restore: another QMX folder's copy, over this one"
    )
    args = parser.parse_args(argv)
    if args.command in FIRST_START:
        return first_start(parser, args)
    try:
        layout = resolve(args.home, create=args.create)
    except NoQmxFolder as missing:
        if missing.kind == "refused":
            parser.exit(2, f"{missing}\n")
        parser.exit(FIRST_START_DUE, f"{_old_hint(args.home) or missing}\n")
    if args.command == "backup":
        return backup(layout, args.target)
    if args.command in ("serve", "start"):
        from qmx_control.library import UNFINISHED, old_library  # noqa: PLC0415

        _finish_restore(parser, layout)
        if (layout.data / RESTORE_UNFINISHED).is_file():
            parser.exit(
                FIRST_START_DUE,
                f"QMX did not start: restoring a copy into {layout.root} did not finish. Start the "
                "first start and restore it again into the same folder.\n",
            )
        unfit = old_library(layout.home)
        if unfit is not None:
            due = (layout.home / UNFINISHED).is_file()
            parser.exit(FIRST_START_DUE if due else 2, f"QMX did not start: {unfit}\n")
        opening = check_open(layout)
        held = opening.held_back
        for verdict in held:
            print(verdict.line, file=sys.stderr)
        if any(verdict.action == "refused" for verdict in held):
            parser.exit(2, "QMX did not start: a store above is refused.\n")
        if args.command == "serve" and any(v.action == "upgrades" for v in opening.verdicts):
            _copy_before_upgrade(layout)
    home = layout.home
    library_root: Path | None = args.library_root.resolve() if args.library_root else None
    keep = read_keep_names(home / "settings.toml")
    scrubbed = scrub_process_env(os.environ, keep)
    # In-process readers that take no home (the door's bearer on a keyring-less server) resolve
    # the same folder through QMX_HOME instead of guessing.
    os.environ["QMX_HOME"] = str(layout.root)
    from qmx_host import host  # noqa: PLC0415

    match args.command:
        case "serve":
            return host.serve_forever(
                home,
                port=args.port,
                role=args.role,
                ui_origin=args.ui_origin,
                scrubbed=scrubbed,
                keep=sorted(keep),
                library_root=library_root,
                place=args.place,
            )
        case "start":
            return host.start(home, args.port, args.role, args.ui_origin, library_root, args.place)
        case "status":
            return host.status(home)
        case _:
            return host.stop(home)


def backup(layout: Layout, only: str | None) -> int:
    """One round in the foreground, with the local floor on the folder's drive, each mini app's
    `road/` copied under its road lease."""
    from qmx_home.backup.plan import PlanRefused, parse  # noqa: PLC0415
    from qmx_home.backup.round import run_round  # noqa: PLC0415
    from qmx_home.files import Busy, local_floor  # noqa: PLC0415

    from qmx_host.backups import road_lease_of  # noqa: PLC0415
    from qmx_host.disk import free_bytes  # noqa: PLC0415

    path = layout.home / "settings.toml"
    settings = tomllib.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    engine = cast("dict[str, object]", settings.get("engine", {}))
    try:
        plan = parse(settings.get("backup", {}), layout, engine)
        report = run_round(
            layout,
            plan,
            now=datetime.now().astimezone(),
            floor=local_floor(engine, free_bytes(layout.home)),
            only=only,
            asked=True,
            progress=lambda step: print(step, file=sys.stderr, flush=True),
            road_lease=road_lease_of(layout),
            rclone=_rclone(layout, plan),
        )
    except (Busy, PlanRefused) as refused:
        print(f"refused: {refused}", file=sys.stderr)
        return 1
    print("\n".join(report.lines))
    return 1 if report.result == "refused" else 0


def _said(step: str, **_counts: int) -> None:
    print(step, file=sys.stderr, flush=True)


def _rclone(layout: Layout, plan: Plan) -> Rclone | None:
    """The one rclone runner, on Credential Manager, when a storage is reached through rclone."""
    if not any(storage.via == "rclone" for storage in plan.sending):
        return None
    from qmx_broker.credentials import CredentialManager  # noqa: PLC0415
    from qmx_home.rclone import Rclone  # noqa: PLC0415

    return Rclone(layout, keys=CredentialManager(), path=plan.rclone_path)


def _finish_restore(parser: argparse.ArgumentParser, layout: Layout) -> None:
    """A restore staged for the folder, finished before any store opens; a finish that cannot run
    stops the start with its line, and the copy stays staged."""
    from qmx_home.backup.restore import JOURNAL, RestoreRefused, finish  # noqa: PLC0415
    from qmx_home.files import Busy  # noqa: PLC0415

    from qmx_host.process_record import recorded_host  # noqa: PLC0415

    if not (layout.backups / JOURNAL).is_file():
        return
    try:
        done = finish(layout, running=recorded_host)
    except (Busy, RestoreRefused) as refused:
        parser.exit(2, f"QMX did not start: {refused}\n")
    if done is not None:
        print(done.line, file=sys.stderr, flush=True)


def _copy_before_upgrade(layout: Layout) -> None:
    """One copy of the whole folder into This PC's copies tagged `before-upgrade`, with the local
    floor. One that cannot be made is a line on stderr, and the start goes on: each store still
    copies itself before its own upgrade."""
    from qmx_home.backup.plan import PlanRefused, parse  # noqa: PLC0415
    from qmx_home.backup.round import quick  # noqa: PLC0415
    from qmx_home.files import local_floor  # noqa: PLC0415

    from qmx_host.backups import road_lease_of  # noqa: PLC0415
    from qmx_host.disk import free_bytes  # noqa: PLC0415

    path = layout.home / "settings.toml"
    try:
        settings = tomllib.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        engine = cast("dict[str, object]", settings.get("engine", {}))
        leave_out = parse(settings.get("backup", {}), layout, engine).leave_out
    except OSError, ValueError, PlanRefused:
        settings, leave_out = {}, ()
    engine = cast("dict[str, object]", settings.get("engine", {}))
    try:
        report = quick(
            layout,
            "before-upgrade",
            floor=local_floor(engine, free_bytes(layout.home)),
            leave_out=leave_out,
            road_lease=road_lease_of(layout),
        )
    except Exception as failed:  # the stores' own pre-change copies still guard the upgrade
        why = str(failed) or type(failed).__name__
    else:
        place = report.places[0]
        if place.result == "copied":
            print(f"before the upgrade: {place.line}", file=sys.stderr, flush=True)
            return
        why = place.line
    print(
        f"QMX made no copy of the folder before the upgrade: {why.rstrip('.')}. The start goes "
        "on; each store still copies itself before it upgrades.",
        file=sys.stderr,
        flush=True,
    )


def _old_hint(flag: Path | None) -> str | None:
    """The first start's line when the folder a command was given, or his profile's old folder
    when it was given none, holds old QMX data; the resolver's own line otherwise."""
    from qmx_host.first_start import default_old, old_layout_hint  # noqa: PLC0415

    named = flag or (Path(os.environ["QMX_HOME"]) if os.environ.get("QMX_HOME") else None)
    return old_layout_hint(named or default_old())


def first_start(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    """The first-start card's choices on the command line, and its routes with `--serve`."""
    from qmx_home.files import Busy  # noqa: PLC0415

    from qmx_host.first_start import (  # noqa: PLC0415
        Places,
        bring_in_old,
        default_old,
        first_start_app,
        make_new,
        offer,
        open_existing,
    )

    sock = _bound(parser, args.port) if args.command == "first-start" and args.serve else None
    old = args.old or default_old()
    places = Places.this_pc()
    if args.command == "first-start":
        print("\n".join(offer(old, places).lines()), flush=True)
        if sock is None:
            return 0
        import uvicorn  # noqa: PLC0415

        handed: list[Path] = []

        def handover(folder: Path) -> None:
            handed[:] = [folder]
            server.should_exit = True

        app = first_start_app(places, old, args.ui_origin, port=args.port, on_handover=handover)
        config = uvicorn.Config(app, access_log=False, timeout_graceful_shutdown=HANDOVER_GRACE_S)
        server = uvicorn.Server(config)
        server.run(sockets=[sock])
        if not handed:
            print("the first start stopped with no QMX folder handed over", file=sys.stderr)
            return 1
        print(json.dumps({"handover": {"folder": str(handed[0]), "port": args.port}}), flush=True)
        return 0
    if args.command == "restore":
        return restore(parser, args, places)
    if args.home is None:
        parser.exit(2, f"{args.command} needs --home <folder>\n")
    folder: Path = args.home
    try:
        if args.command == "new":
            print(f"made the QMX folder {make_new(folder, places).root}")
            return 0
        if args.command == "open":
            print(f"QMX now uses the folder {open_existing(folder, places).root}")
            return 0
        warning = places.warning(folder)
        if warning is not None:
            print(f"note: {warning}", file=sys.stderr)
        report = bring_in_old(old, folder, places, anew=args.again)
    except Busy as refused:
        parser.exit(2, f"refused: {refused}\n")
    print(report.text, end="")
    return 0 if report.finished else 1


def restore(parser: argparse.ArgumentParser, args: argparse.Namespace, places: Places) -> int:
    """`restore`: list a place's copies, show what one replaces, and restore it with `--yes`,
    holding the first start as the card does."""
    from qmx_home.backup.restore import HostServes, RestoreRefused, copies  # noqa: PLC0415
    from qmx_home.files import Busy, hold  # noqa: PLC0415

    from qmx_host.bring_in import BUSY  # noqa: PLC0415
    from qmx_host.first_start import (  # noqa: PLC0415
        backup_source,
        check_restore,
        lock_file,
        picked,
        refuse_restore,
        restore_copy,
        restore_into,
    )

    if args.home is None or args.source is None:
        parser.exit(2, "restore needs --home <folder> and --from <backup place>\n")
    try:
        repository = backup_source({"kind": "folder", "path": str(args.source.absolute())})
        if args.copy is None:
            print(f"Copies in {repository.where}, newest first:")
            for copy in copies(repository):
                lacks = f"; partial, it lacks {', '.join(copy.lacks)}" if copy.partial else ""
                print(
                    f"  {copy.stamp}  {copy.why}  {copy.files:,} files, "
                    f"{copy.bytes / (1 << 20):,.0f} MB, made by QMX {copy.release} on "
                    f"{copy.machine}{lacks}"
                )
            print(
                f"Restore one: python -m qmx_host restore --home {args.home} --from {args.source} "
                "--copy <date> --yes"
            )
            return 0
        into = restore_into(args.home, places, make=False)
        if into.new and not args.create:
            raise RestoreRefused(
                f"there is no QMX folder at {into.layout.root}; add --create to make one from the "
                "copy"
            )
        copy = picked(repository, args.copy)
        if not args.yes:
            print(check_restore(into, copy)["line"])
            print("Nothing was changed. Add --yes to restore it.")
            return 0
        refuse_restore(into, repository, copy, replace=args.replace)
        with hold(lock_file(), BUSY, removed=True):
            if into.new:
                into = restore_into(args.home, places, make=True)
            done = restore_copy(
                into,
                repository,
                copy,
                replace=args.replace,
                progress=_said,
            )
    except HostServes as hosted:
        print(f"refused: {hosted}", file=sys.stderr)
        return 1
    except (Busy, RestoreRefused) as refused:
        print(f"refused: {refused}", file=sys.stderr)
        return 2
    print(done.line)
    return 0


def _bound(parser: argparse.ArgumentParser, port: int) -> socket.socket:
    """The card's socket on the loopback, bound once before anything is served, so a port taken
    between a check and the bind cannot be read as a stop with no handover."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
    except OSError:
        sock.close()
        parser.exit(
            PORT_TAKEN,
            f"port {port} is in use: stop what holds it, or start the first start on another "
            "port\n",
        )
    return sock


if __name__ == "__main__":
    raise SystemExit(main())
