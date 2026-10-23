"""`python -m qmx_host serve --home <home> --port <port> [--role pc | node | server]
[--library-root <path>] [--ui-origin <origin>]`, and `start`, `status` and `stop` for a host in
the background.

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m qmx_host")
    parser.add_argument("command", choices=["serve", "start", "status", "stop"])
    parser.add_argument("--home", type=Path, default=Path.home() / ".qmx")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--role", choices=["pc", "node", "server"], default="pc")
    parser.add_argument("--library-root", type=Path, default=None)
    parser.add_argument("--ui-origin", default="http://127.0.0.1:5173")
    args = parser.parse_args(argv)
    home: Path = args.home.resolve()
    library_root: Path | None = args.library_root.resolve() if args.library_root else None
    keep = read_keep_names(home / "settings.toml")
    scrubbed = scrub_process_env(os.environ, keep)
    home.mkdir(parents=True, exist_ok=True)
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
            )
        case "start":
            return host.start(home, args.port, args.role, args.ui_origin, library_root)
        case "status":
            return host.status(home)
        case _:
            return host.stop(home)


if __name__ == "__main__":
    raise SystemExit(main())
