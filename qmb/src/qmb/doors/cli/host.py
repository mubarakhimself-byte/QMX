"""``qmb host start|status|stop`` run ``python -m qmx_host`` and report what it printed.

``qmx_host`` owns the process: its home lock, readiness check and process-tree stop. Do not
reuse package ``qmb.host`` (CT-33 HostedBot).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from qmf.core.refusal import Ok, Result

from qmb._refuse import invalid, unavailable

__all__ = [
    "HOST_COMMANDS",
    "HOST_CONFIGURE_COMMANDS",
    "HOST_PAIR_COMMANDS",
    "control_host",
]


HOST_COMMANDS: Final[tuple[str, ...]] = ("start", "status", "stop")
HOST_CONFIGURE_COMMANDS: Final[tuple[str, ...]] = (
    "pairing-ttl",
    "artifact-stage-max-bytes",
    "source-origin",
    "dest-placement",
)
HOST_PAIR_COMMANDS: Final[tuple[str, ...]] = ("revoke",)


def control_host(
    command: str,
    *,
    home: Path | None = None,
    port: int = 8766,
    python: str | None = None,
) -> Result[Mapping[str, object]]:
    """Run ``python -m qmx_host <command>``. ``python`` names an interpreter that has
    ``qmx-host`` installed; without it a checkout runs the workspace package through ``uv``."""
    if command not in HOST_COMMANDS:
        return invalid("host", "expected start, status or stop")
    if not 1 <= port <= 65535:
        return invalid("port", "port must be between 1 and 65535")
    argv = [python or sys.executable, "-m", "qmx_host", command, "--port", str(port)]
    if python is None:
        repo = Path(__file__).resolve().parents[5]
        project = repo / "qmx-agents/packages/qmx-host"
        if (project / "pyproject.toml").exists():
            uv = shutil.which("uv")
            if uv is None:
                return unavailable("host", "uv is required to run qmx-host in this checkout")
            argv = [
                uv,
                "run",
                "--project",
                str(project),
                "--package",
                "qmx-host",
                "--frozen",
                "python",
                *argv[1:],
            ]
    if home is not None:
        argv += ["--home", str(home.resolve())]
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return unavailable("host", f"qmx_host {command} could not complete: {exc}")
    if completed.returncode:
        return unavailable(
            "host", completed.stderr.strip() or completed.stdout.strip() or "qmx_host failed"
        )
    return Ok({"verb": f"host.{command}", "message": completed.stdout.strip()})
