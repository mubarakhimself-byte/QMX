"""`python -m qmx_host serve [--home <folder> [--create]] --port <port> [--role pc | node |
server] [--place <name>] [--library-root <path>] [--ui-origin <origin>]`, and `start`, `status`
and `stop` for a host in the background. Without `--home` the QMX folder is found by
`qmx_home.resolve`, and a missing folder is made only with `--create`. `--place` is the name he gave
a server in his place list, which `qmx node setup` writes into the server's unit. A `node` or
`server` host with neither it nor `[engine] host_name` refuses to start; This PC is always `pc`.

`server` is the role the server's unit runs: the same node work plus the Library service, because
on the server the one host process opens the store as its one writer and answers the Library routes
in process (AD-19, AD-26).

`first-start [--serve]`, `new`, `open`, `bring-in [--old <folder>]` and `restore` are the first
start's card (design 62 F): they run with no QMX folder yet and take the chosen one as `--home`.
A command pointed at his old folder, or given no folder while one sits at `~/.qmx`, names the
bring-in; `serve` and `start` refuse a folder holding an unswitched `library.db` or an unfinished
bring-in.

Before `serve` or `start`, every store of the folder is read against this release (design 62 B2):
a store opened read-only is named on stderr, and a refused one stops the start with its name and
the version it needs.

Order is the invariant: parse the arguments, read the keep list with the standard library, scrub
this process's environment, and only then import the harness, because the SDK reads `os.environ`
at every `connect()`.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from qma.boot import read_keep_names, scrub_process_env
from qmx_home import NoQmxFolder, resolve
from qmx_home.versions import check_open

FIRST_START = ("first-start", "new", "open", "bring-in", "restore")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m qmx_host")
    parser.add_argument("command", choices=["serve", "start", "status", "stop", *FIRST_START])
    parser.add_argument(
        "--home", type=Path, default=None, help="the QMX folder; found when left out"
    )
    parser.add_argument(
        "--old", type=Path, default=None, help="bring-in: the old folder; ~/.qmx when left out"
    )
    parser.add_argument(
        "--serve", action="store_true", help="first-start: serve the card's routes on --port"
    )
    parser.add_argument("--create", action="store_true", help="make the --home folder if missing")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--role", choices=["pc", "node", "server"], default="pc")
    parser.add_argument("--library-root", type=Path, default=None)
    parser.add_argument(
        "--place", default="", help="this machine's place name; setup passes it for a server"
    )
    parser.add_argument("--ui-origin", default="http://127.0.0.1:5173")
    args = parser.parse_args(argv)
    if args.command in FIRST_START:
        return first_start(parser, args)
    try:
        layout = resolve(args.home, create=args.create)
    except NoQmxFolder as missing:
        parser.exit(2, f"{_old_hint(args.home) or missing}\n")
    if args.command in ("serve", "start"):
        from qmx_control.library import old_library  # noqa: PLC0415

        unfit = old_library(layout.home)
        if unfit is not None:
            parser.exit(2, f"QMX did not start: {unfit}\n")
        held = check_open(layout).held_back
        for verdict in held:
            print(verdict.line, file=sys.stderr)
        if any(verdict.action == "refused" for verdict in held):
            parser.exit(2, "QMX did not start: a store above is refused.\n")
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


def _old_hint(flag: Path | None) -> str | None:
    """The first start's line when the folder a command was given, or his profile's old folder
    when it was given none, holds old QMX data; the resolver's own line otherwise."""
    from qmx_host.first_start import default_old, old_layout_hint  # noqa: PLC0415

    named = flag or (Path(os.environ["QMX_HOME"]) if os.environ.get("QMX_HOME") else None)
    return old_layout_hint(named or default_old())


def first_start(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    """The first-start card's choices on the command line, and its routes with `--serve`."""
    from qmx_host.bring_in import Refused  # noqa: PLC0415
    from qmx_host.first_start import (  # noqa: PLC0415
        RESTORE_LATER,
        Places,
        bring_in_old,
        default_old,
        first_start_app,
        make_new,
        offer,
        open_existing,
    )

    old = args.old or default_old()
    places = Places.this_pc()
    if args.command == "first-start":
        print("\n".join(offer(old).lines()))
        if args.serve:
            import uvicorn  # noqa: PLC0415

            app = first_start_app(places, old, args.ui_origin)
            uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=args.port)).run()
        return 0
    if args.command == "restore":
        print(RESTORE_LATER)
        return 2
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
        report = bring_in_old(old, folder, places)
    except Refused as refused:
        parser.exit(2, f"refused: {refused}\n")
    print(report.text, end="")
    return 0 if report.finished else 1


if __name__ == "__main__":
    raise SystemExit(main())
