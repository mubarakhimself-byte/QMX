"""S1. The pinned SDK, its bundled CLI and the `qma-cli-launcher` shim, with no model turn.

PASS needs a `win_amd64` wheel on Windows, a bundled CLI at 2.1.248 or later, a launcher
`.exe` that Windows lets run and that prints the CLI's version, and an SDK connect (no query)
with the launcher as `cli_path`, which runs the SDK's version probe through it.
"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
from importlib.metadata import distribution
from pathlib import Path

from claude_agent_sdk import ClaudeSDKClient
from common import LAUNCHER, SCRATCH, Log, boot, chat_options, home_env
from qma.launcher import bundled_cli

CLI_FLOOR = (2, 1, 248)


def version_of(command: list[str], log: Log) -> str:
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False)
    except OSError as error:
        log(f"start refused: {command[0]}: {error!r}")
        return ""
    return done.stdout.strip() if done.returncode == 0 else ""


async def connect(log: Log) -> None:
    options = chat_options(home_env(), SCRATCH / "s01", tools=[])
    try:
        async with ClaudeSDKClient(options=options) as client:
            info = await client.get_server_info()
            log.check(
                "SDK connects through the launcher as cli_path", info is not None, "connected"
            )
    except Exception as error:
        log.check("SDK connects through the launcher as cli_path", False, repr(error)[:300])


def main() -> int:
    log = Log("hp4-s01")
    boot()
    dist = distribution("claude-agent-sdk")
    tags = [line.split(":", 1)[1].strip() for line in (dist.read_text("WHEEL") or "").splitlines()
            if line.startswith("Tag:")]  # fmt: skip
    log(f"claude-agent-sdk {dist.version} wheel tags {tags}")
    if os.name == "nt":
        log.check("wheel tag", any(tag.endswith("win_amd64") for tag in tags), tags)
    cli = bundled_cli()
    log(f"bundled CLI {cli}")
    direct = "" if cli is None else version_of([cli, "-v"], log)
    found = re.match(r"(\d+)\.(\d+)\.(\d+)", direct)
    floor = tuple(int(part) for part in found.groups()) >= CLI_FLOOR if found else False
    log.check("bundled CLI at 2.1.248 or later", floor, direct)
    log.check("launcher is an .exe", os.name != "nt" or LAUNCHER.suffix == ".exe", LAUNCHER)
    shim = version_of([str(LAUNCHER), "-v"], log)
    log.check("launcher -v runs and prints the CLI version", shim == direct != "", shim)
    asyncio.run(connect(log))
    log(f"evidence {Path(log.path)}")
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(main())
