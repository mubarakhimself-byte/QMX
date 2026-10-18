"""`python -m qmx_engine`: the engine's own command line. Later PRs add its subcommands."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


def parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="python -m qmx_engine",
        description="The QMX workflow engine. No subcommands yet.",
    )


def main(argv: Sequence[str] | None = None) -> int:
    cli = parser()
    cli.parse_args(argv)
    cli.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
