"""S1. Install the newest claude-agent-sdk with a win_amd64 wheel whose bundled CLI is new enough.

Runs under any Python with `uv` on PATH. Builds the probe venv every later probe uses.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

from common import CLI_FLOOR, PROBE_VENV, SCRATCH, Log, home_env, parse_version, reduced_env, uv_env

PYPI = "https://pypi.org/pypi/claude-agent-sdk/json"
WHEEL_TAG = "win_amd64"


def windows_releases() -> list[tuple[str, str]]:
    """(version, wheel filename) for every release with a win_amd64 wheel, newest first."""
    with urllib.request.urlopen(PYPI, timeout=60) as response:
        releases: dict[str, list[dict[str, str]]] = json.load(response)["releases"]
    found = [
        (version, file["filename"])
        for version, files in releases.items()
        for file in files
        if file["filename"].endswith(f"{WHEEL_TAG}.whl")
    ]
    return sorted(found, key=lambda pair: parse_version(pair[0]), reverse=True)


def venv_python() -> Path:
    return PROBE_VENV / "Scripts" / "python.exe"


def install(uv: str, version: str) -> None:
    env = uv_env()
    if not venv_python().exists():
        subprocess.run([uv, "venv", str(PROBE_VENV), "--python", "3.14"], env=env, check=True)
    subprocess.run(
        [uv, "pip", "install", "--python", str(venv_python()), f"claude-agent-sdk=={version}"],
        env=env,
        check=True,
    )


def installed_versions() -> tuple[str, str, str]:
    """SDK version, bundled CLI path and the CLI's `--version` output, read inside the venv."""
    code = (
        "import claude_agent_sdk, pathlib;"
        "print(claude_agent_sdk.__version__);"
        "print(pathlib.Path(claude_agent_sdk.__file__).parent / '_bundled' / 'claude.exe')"
    )
    out = subprocess.run(
        [str(venv_python()), "-c", code], capture_output=True, text=True, check=True
    )
    sdk, cli = out.stdout.split()
    version = subprocess.run(
        [cli, "--version"],
        env=reduced_env(os.environ) | home_env() | {"CLAUDE_CONFIG_DIR": str(SCRATCH / "config")},
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return sdk, cli, version.stdout.strip()


def main() -> int:
    log = Log("hp0-install")
    uv = shutil.which("uv")
    if uv is None:
        log.row("uv on PATH", "missing", "FAIL")
        return 1
    for version, wheel in windows_releases():
        log(f"candidate claude-agent-sdk {version} wheel {wheel}")
        install(uv, version)
        sdk, cli, cli_version = installed_versions()
        log(f"installed sdk={sdk} cli={cli} cli --version={cli_version!r}")
        floor = ".".join(map(str, CLI_FLOOR))
        if parse_version(cli_version) >= CLI_FLOOR:
            log.row("S1 SDK pin", f"claude-agent-sdk=={sdk} wheel {wheel}", "PASS")
            log.row("S1 bundled CLI", f"{cli_version} >= {floor}", "PASS")
            log(f"probe venv python: {venv_python()}")
            return 0
        log(f"bundled CLI {cli_version} is below {floor}; trying the next release")
    log.row("S1 SDK pin", "no win_amd64 release has a CLI at the floor", "FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
