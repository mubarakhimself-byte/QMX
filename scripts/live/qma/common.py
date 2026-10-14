"""Shared setup for the QMA live checks: the ship home, a throwaway HOME, the evidence log.

Every check runs the agents workspace Python (`qmx-agents/.venv`). No check reads the login
token; `require_login` only tests that the credentials file exists.
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

from claude_agent_sdk import ClaudeAgentOptions
from qma.boot import scrub_process_env

SHIP: Final = Path("D:/QMX-worktrees/qma-ship")
CONFIG_DIR: Final = SHIP / "home" / "claude"
EVIDENCE: Final = SHIP / "evidence" / "hp4"
SCRATCH: Final = Path(os.environ.get("QMA_LIVE_SCRATCH", "D:/Temp/qma-live"))
FAKE_HOME: Final = SCRATCH / "home"
MODEL: Final = "haiku"
LAUNCHER: Final = Path(sys.executable).parent / (
    "qma-cli-launcher.exe" if os.name == "nt" else "qma-cli-launcher"
)


class Log:
    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True

    def __call__(self, line: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {line}"
        print(stamped, flush=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(stamped + "\n")

    def check(self, name: str, ok: bool, seen: object) -> None:
        self(f"{'PASS' if ok else 'FAIL'} {name}: {seen}")
        self.passed &= ok

    def verdict(self) -> int:
        self("PASS" if self.passed else "FAIL")
        return 0 if self.passed else 1


def boot() -> tuple[str, ...]:
    """What `qma.serve` will do first: scrub this process, then set the scratch dirs."""
    removed = scrub_process_env(os.environ)
    FAKE_HOME.mkdir(parents=True, exist_ok=True)
    os.environ |= {"TMP": str(SCRATCH), "TEMP": str(SCRATCH)}
    return removed


def home_env() -> dict[str, str]:
    return {
        "CLAUDE_CONFIG_DIR": str(CONFIG_DIR),
        "HOME": str(FAKE_HOME),
        "USERPROFILE": str(FAKE_HOME),
    }


def chat_env(chat: str, procs_dir: Path, cap: str) -> dict[str, str]:
    return home_env() | {
        "QMA_CHAT_ID": chat,
        "QMA_PROC_DIR": str(procs_dir),
        "QMA_CAP": cap,
    }


def require_login(log: Log) -> None:
    present = (CONFIG_DIR / ".credentials.json").exists()
    log(f"ship home credentials file present: {present}")
    if not present:
        log("BLOCKED: the ship home has no plan login")
        raise SystemExit(3)


def chat_options(env: Mapping[str, str], cwd: Path, **overrides: Any) -> ClaudeAgentOptions:
    cwd.mkdir(parents=True, exist_ok=True)
    kwargs: dict[str, Any] = {
        "cli_path": str(LAUNCHER),
        "env": dict(env),
        "setting_sources": [],
        "settings": json.dumps({"forceLoginMethod": "claudeai"}),
        "strict_mcp_config": True,
        "model": MODEL,
        "cwd": str(cwd),
        "permission_mode": "bypassPermissions",
        "max_turns": 3,
    }
    return ClaudeAgentOptions(**(kwargs | overrides))
