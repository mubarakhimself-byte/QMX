"""Start a host module (`qmx_host`, or another lane module) for a lane, with a lane bearer in
place of the operator's control token in the OS vault.

`python lane_host.py <module> serve --home <home> --port <port>`

The bearer is `QMX_LANE_BEARER` when set, so a lane on the ship home writes nothing into it, and
otherwise the throwaway home's `lane-bearer` file.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

import qmx_control.server

BEARER_FILE = "lane-bearer"
BEARER_ENV = "QMX_LANE_BEARER"


def main() -> None:
    module, *argv = sys.argv[1:]
    bearer = os.environ.pop(BEARER_ENV, None)
    if bearer is None:
        home = Path(argv[argv.index("--home") + 1])
        bearer = (home / BEARER_FILE).read_text(encoding="utf-8").strip()
    qmx_control.server.local_token = lambda: bearer
    sys.argv = [module, *argv]
    runpy.run_module(module, run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main()
