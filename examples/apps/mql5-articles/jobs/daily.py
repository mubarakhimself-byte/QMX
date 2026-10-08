"""The P12 supervisor invokes run() once a day."""

import asyncio
import json

from collector import run_daily


def run() -> None:
    print(json.dumps(asyncio.run(run_daily())))
