"""`python -m qmx_host serve [--home <folder> [--create]] --port <port> [--role pc | node |
server] [--place <name>] [--library-root <path>] [--ui-origin <origin>]`, and `start`, `status`
and `stop` for a host in the background. Without `--home` the QMX folder is found by
`qmx_home.resolve`, and a missing folder is made only with `--create`. `--place` is the name he gave
a server in his place list, which `qmx node setup` writes into the server's unit. A `node` or
`server` host with neither it nor `[engine] host_name` refuses to start; This PC is always `pc`.

`server` is the role the server's unit runs: the same node work plus the Library service, because
on the server the one host process opens the store as its one writer and answers the Library routes
in process (AD-19, AD-26).

Order is the invariant: parse the arguments, read the keep list with the standard library, scrub
this process's environment, and only then import the harness, because the SDK reads `os.environ`
at every `connect()`.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from qma.boot import read_keep_names, scrub_process_env
from qmx_home import NoQmxFolder, resolve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m qmx_host")
    parser.add_argument("command", choices=["serve", "start", "status", "stop"])
    parser.add_argument(
        "--home", type=Path, default=None, help="the QMX folder; found when left out"
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
    try:
        layout = resolve(args.home, create=args.create)
    except NoQmxFolder as missing:
        parser.exit(2, f"{missing}\n")
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


if __name__ == "__main__":
    raise SystemExit(main())
