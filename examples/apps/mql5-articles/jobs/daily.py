"""The supervisor runs run() once a day; what it returns is the job's result, with its outputs."""

from typing import Any

from collector import run_daily


def run() -> dict[str, Any]:
    return run_daily()
