"""`python -m qmx_home layout <folder>`: move a flat home into the folder tree, with QMX closed.
`python -m qmx_home check [--home <folder>]`: say, store by store, whether this QMX opens the
folder, upgrades a store after a copy, or refuses one by name (design 62 B2). It changes no
store; it exits 1 when a store is refused or opens read-only.

The same commands run on a test home on this PC and on a server home (design 62 guard 4).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from qmx_home import LayoutRefused, NoQmxFolder, resolve, step_to_tree
from qmx_home.versions import check_open


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m qmx_home")
    commands = parser.add_subparsers(dest="command", required=True)
    layout = commands.add_parser("layout", help="move a flat home into the folder tree")
    layout.add_argument("folder", type=Path)
    check = commands.add_parser("check", help="say which stores open, upgrade or refuse")
    check.add_argument(
        "--home", type=Path, default=None, help="the QMX folder; found when left out"
    )
    args = parser.parse_args(argv)
    if args.command == "check":
        try:
            opening = check_open(resolve(args.home))
        except NoQmxFolder as missing:
            parser.exit(2, f"{missing}\n")
        for verdict in opening.verdicts:
            print(verdict.line)
        print(f"checked in {opening.seconds * 1000:.1f} ms")
        return 1 if opening.held_back else 0
    try:
        moved = step_to_tree(args.folder)
    except LayoutRefused as refused:
        parser.exit(1, f"{refused}\n")
    for source, target in moved:
        print(f"moved {source} to {target}")
    print(f"{args.folder.resolve()} is in the folder tree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
