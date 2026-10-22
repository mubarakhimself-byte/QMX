"""S19, host half. Start `qmx_host` with a polluted parent environment and read
`/api/doctor`. PASS when every planted name is listed as removed with no value anywhere in the
reply, and the Git Bash path the parent chose is kept.

    s19_boot.py [--home D:/QMX-worktrees/qma-ship/home] [--port 8876]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import keyring
from common import FAKE_HOME, SHIP, Log

GIT_BASH = "C:/Program Files/Git/usr/bin/bash.exe"
PLANTED = {
    "ANTHROPIC_API_KEY": "s19-fake-anthropic-key",
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:9",
    "CLAUDE_CODE_USE_BEDROCK": "1",
    "OPENAI_API_KEY": "s19-fake-openai-key",
    "HTTPS_PROXY": "http://127.0.0.1:9",
    "HTTP_PROXY": "http://127.0.0.1:9",
    "NODE_EXTRA_CA_CERTS": "D:/Temp/s19-fake-ca.pem",
    "CLAUDE_CODE_PROCESS_WRAPPER": "s19-fake-wrapper",
}


def wait_for_health(port: int, headers: dict[str, str]) -> bool:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            if httpx.get(f"http://127.0.0.1:{port}/api/health", headers=headers).status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, default=SHIP / "home")
    parser.add_argument("--port", type=int, default=8876)
    args = parser.parse_args()
    log = Log("hp5-s19")
    FAKE_HOME.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ) | PLANTED | {"CLAUDE_CODE_GIT_BASH_PATH": GIT_BASH}
    env |= {"HOME": str(FAKE_HOME), "USERPROFILE": str(FAKE_HOME)}
    log(f"planted names: {sorted(PLANTED)} and CLAUDE_CODE_GIT_BASH_PATH={GIT_BASH}")
    command = [sys.executable, "-m", "qmx_host", "serve", "--home", str(args.home)]
    host = subprocess.Popen([*command, "--port", str(args.port)], env=env)
    try:
        token = keyring.get_password("qmx/control-token", "control-token")
        headers = {"Authorization": f"Bearer {token}"}
        if token is None or not wait_for_health(args.port, headers):
            log.check("the host answers /api/health", False, "no token or no answer")
            return log.verdict()
        reply = httpx.get(f"http://127.0.0.1:{args.port}/api/doctor", headers=headers, timeout=120)
        lines = {line["name"]: line for line in reply.json()["lines"]}
        removed = lines["boot scrub removed"]["detail"]
        log(f"boot scrub removed: {removed}")
        log(f"git bash: {lines['git bash']['detail']}")
        names = set(removed.split(", "))
        for name in sorted(PLANTED):
            log.check(f"{name} removed", name in names, name in names)
        leaked = [value for value in PLANTED.values() if len(value) > 1 and value in reply.text]
        log.check("no planted value appears in /api/doctor", not leaked, leaked)
        bash = lines["git bash"]
        log.check("the chosen Git Bash path is kept", GIT_BASH in bash["detail"], bash["detail"])
        log.check(
            "CLAUDE_CODE_GIT_BASH_PATH is not removed",
            "CLAUDE_CODE_GIT_BASH_PATH" not in names,
            "CLAUDE_CODE_GIT_BASH_PATH" in names,
        )
    finally:
        host.terminate()
        host.wait(timeout=30)
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
