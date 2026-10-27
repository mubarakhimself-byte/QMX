"""The record a running host keeps in its home: its pid, port and start time. Light on purpose, so
the first start can ask whether a host still serves a folder without importing the host."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

import psutil

STATE: Final = "control-process.json"
"""The running host's pid, port and start time, for `status`, `stop` and the refusal line."""


def recorded_host(home: Path) -> int | None:
    """The pid of the live host the home's record names, or None."""
    try:
        state = json.loads((home / STATE).read_text(encoding="utf-8"))
        pid, created = state["pid"], state["created"]
    except OSError, ValueError, KeyError, TypeError:
        return None
    if not isinstance(pid, int):
        return None
    try:
        return pid if psutil.Process(pid).create_time() == created else None
    except psutil.Error:
        return None
