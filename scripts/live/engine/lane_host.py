"""Start a host module (`qmx_engine.host` or `qma.serve`) for a lane, with the bearer taken from
the throwaway home's `lane-bearer` file instead of the operator's control token in the OS vault.

`python lane_host.py <module> serve --home <home> --port <port>`
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import qmx_control.server

BEARER_FILE = "lane-bearer"


def main() -> None:
    module, *argv = sys.argv[1:]
    home = Path(argv[argv.index("--home") + 1])
    bearer = (home / BEARER_FILE).read_text(encoding="utf-8").strip()
    qmx_control.server.local_token = lambda: bearer
    sys.argv = [module, *argv]
    runpy.run_module(module, run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main()
