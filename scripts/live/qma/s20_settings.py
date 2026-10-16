"""S20, second half. PUT each forbidden `[claude]` key to a running host. PASS when each PUT
is refused with the key named and `settings.toml` is byte-identical afterwards.

    s20_settings.py [--home D:/QMX-worktrees/qma-ship/home] [--port 8876]
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import httpx
import keyring
from common import SHIP, Log

FORBIDDEN: dict[str, dict[str, object]] = {
    "apiKeyHelper": {"apiKeyHelper": "echo s20"},
    "env.HTTPS_PROXY": {"env": {"HTTPS_PROXY": "http://127.0.0.1:9"}},
    "env.NODE_EXTRA_CA_CERTS": {"env": {"NODE_EXTRA_CA_CERTS": "D:/Temp/s20.pem"}},
    "env.ANTHROPIC_BASE_URL": {"env": {"ANTHROPIC_BASE_URL": "http://127.0.0.1:9"}},
    "enabledPlugins": {"enabledPlugins": {"s20@s20": True}},
    "forceLoginMethod": {"forceLoginMethod": "console"},
    "disableAllHooks": {"disableAllHooks": True},
    "model": {"model": "opus"},
    "permissions.defaultMode": {"permissions": {"defaultMode": "bypassPermissions"}},
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "absent"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, default=SHIP / "home")
    parser.add_argument("--port", type=int, default=8876)
    args = parser.parse_args()
    log = Log("hp5-s20")
    token = keyring.get_password("qmx/control-token", "control-token")
    if token is None:
        log("BLOCKED: no qmx/control-token")
        return 3
    headers = {"Authorization": f"Bearer {token}"}
    settings = args.home / "settings.toml"
    before = digest(settings)
    log(f"settings.toml before: {before}")
    for key, body in FORBIDDEN.items():
        for door in ("/api/claude-settings", "/api/settings/claude"):
            reply = httpx.put(f"http://127.0.0.1:{args.port}{door}", json=body, headers=headers)
            message = reply.json().get("error", {}).get("message", reply.text)
            refused = reply.status_code == 400 and key in message
            log.check(
                f"PUT {door} {key} refused naming the key",
                refused,
                f"{reply.status_code} {message}",
            )
    after = digest(settings)
    log.check("settings.toml unchanged", after == before, after)
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
