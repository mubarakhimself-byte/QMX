"""`python -m qmx_home layout <folder>`: move a flat home into the folder tree, with QMX closed.

The same command runs on a test home on this PC and on a server home (design 62 guard 4).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from qmx_home import LayoutRefused, step_to_tree


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m qmx_home")
    commands = parser.add_subparsers(dest="command", required=True)
    layout = commands.add_parser("layout", help="move a flat home into the folder tree")
    layout.add_argument("folder", type=Path)
    args = parser.parse_args(argv)
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
