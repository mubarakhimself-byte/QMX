"""Product ``QMA_DAEMON_ROOT`` (Story 67.1; DEC-0510 A14).

Inspect cwd-relative ``qma-daemon-data`` is not the product root.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Final

__all__ = [
    "INSPECT_CWD_RELATIVE_ROOT",
    "product_daemon_root",
    "resolve_daemon_root",
]


INSPECT_CWD_RELATIVE_ROOT: Final[str] = "qma-daemon-data"


def product_daemon_root(
    *,
    system: str | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | str | None = None,
) -> Path:
    """OS product data root for the local workstation daemon.

    Windows ``%LOCALAPPDATA%\\QMX\\qma-daemon``;
    Linux ``${XDG_STATE_HOME:-$HOME/.local/state}/qmx/qma-daemon``;
    macOS ``~/Library/Application Support/QMX/qma-daemon``.
    """
    env = os.environ if environ is None else environ
    plat = sys.platform if system is None else system
    if plat.startswith("win"):
        local = env.get("LOCALAPPDATA")
        if not local:
            base = Path.home() if home is None else Path(home)
            local = str(base / "AppData" / "Local")
        return Path(local) / "QMX" / "qma-daemon"
    if plat == "darwin":
        base = Path(env["HOME"]) if "HOME" in env else (Path.home() if home is None else Path(home))
        return base / "Library" / "Application Support" / "QMX" / "qma-daemon"
    xdg = env.get("XDG_STATE_HOME")
    if xdg:
        return Path(xdg) / "qmx" / "qma-daemon"
    base = Path(env["HOME"]) if "HOME" in env else (Path.home() if home is None else Path(home))
    return base / ".local" / "state" / "qmx" / "qma-daemon"


def resolve_daemon_root(
    environ: Mapping[str, str] | None = None,
    *,
    system: str | None = None,
    home: Path | str | None = None,
) -> Path:
    """Honor ``QMA_DAEMON_ROOT`` when set; otherwise the product root.

    Never falls back to cwd-relative ``qma-daemon-data``.
    """
    env = os.environ if environ is None else environ
    raw = env.get("QMA_DAEMON_ROOT")
    if isinstance(raw, str) and raw.strip() != "":
        return Path(raw)
    return product_daemon_root(system=system, environ=env, home=home)
