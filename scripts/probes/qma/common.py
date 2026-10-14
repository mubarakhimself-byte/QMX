"""Shared pieces of the HP0 probes. Standard library at import time; the SDK loads lazily.

Run every probe with the probe venv's Python that `p_install.py` builds, for example
`D:/QMX-worktrees/qma-ship/probe-venv/Scripts/python.exe scripts/probes/qma/p_env.py`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any, Final, TextIO

SHIP: Final = Path("D:/QMX-worktrees/qma-ship")
CONFIG_DIR: Final = SHIP / "home" / "claude"
EVIDENCE: Final = SHIP / "evidence" / "hp0"
PROBE_VENV: Final = SHIP / "probe-venv"
SCRATCH: Final = Path("D:/Temp/qma-hp0")
FAKE_HOME: Final = SCRATCH / "home"
"""HOME and USERPROFILE for every CLI a probe starts, so nothing reads or writes his `~/.claude`."""
CLI_FLOOR: Final = (2, 1, 248)
PROBE_MODEL: Final = "haiku"
FORCE_LOGIN: Final = {"forceLoginMethod": "claudeai"}

KEEP_NAMES: Final[frozenset[str]] = frozenset(
    {
        "PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "TERM", "USER", "LOGNAME", "SHELL",
        "TMPDIR", "SSH_AUTH_SOCK",
        "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "PATHEXT", "USERPROFILE", "USERNAME",
        "USERDOMAIN", "COMPUTERNAME", "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA",
        "PROGRAMDATA", "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "COMMONPROGRAMFILES",
        "TEMP", "TMP", "OS", "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS",
        "CLAUDE_CODE_GIT_BASH_PATH",
        "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS", "DISPLAY", "WAYLAND_DISPLAY",
    }
)  # fmt: skip
"""The sketch's `boot.KEEP_NAMES` (DESIGN, `sketch/qma/boot.py`), copied verbatim."""

PROBE_KEEP: Final = KEEP_NAMES | {"CLAUDE_CONFIG_DIR"}


def reduced_env(environ: Mapping[str, str]) -> dict[str, str]:
    """The variables of `environ` whose names are in `PROBE_KEEP`, matched case-insensitively."""
    return {name: value for name, value in environ.items() if name.upper() in PROBE_KEEP}


def scrub_process_env(environ: MutableMapping[str, str]) -> tuple[str, ...]:
    """Reduce `environ` in place to `reduced_env`. Returns the removed names, never values.

    The SDK builds the CLI's environment from `os.environ` with `options.env` merged over
    it (02a trap 6), so a probe scrubs `os.environ` itself before it connects.
    """
    removed = sorted(name for name in environ if name.upper() not in PROBE_KEEP)
    for name in removed:
        del environ[name]
    return tuple(removed)


def parse_version(text: str) -> tuple[int, ...]:
    """`2.1.296 (Claude Code)` gives `(2, 1, 296)`."""
    head = text.strip().split()[0]
    return tuple(int(part) for part in head.split("."))


class Log:
    """Prints each line and appends it to `EVIDENCE/<slug>.log`."""

    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"{slug}.log"
        self._file: TextIO = self.path.open("a", encoding="utf-8")
        self(f"=== {slug} {time.strftime('%Y-%m-%dT%H:%M:%S%z')} python {sys.version.split()[0]}")

    def __call__(self, line: str) -> None:
        print(line, flush=True)
        self._file.write(line + "\n")
        self._file.flush()

    def row(self, question: str, value: object, verdict: str) -> None:
        """One FINDINGS-shaped line: question, observed value, PASS/FAIL/BLOCKED."""
        self(f"FINDING\t{question}\t{value}\t{verdict}")


def bundled_cli() -> Path:
    """The `claude.exe` inside the installed SDK wheel."""
    import claude_agent_sdk  # noqa: PLC0415

    exe = "claude.exe" if os.name == "nt" else "claude"
    return Path(claude_agent_sdk.__file__).parent / "_bundled" / exe


def sdk_version() -> str:
    from claude_agent_sdk import __version__  # noqa: PLC0415

    return __version__


def home_env() -> dict[str, str]:
    """The ship's `CLAUDE_CONFIG_DIR` and the throwaway HOME and USERPROFILE."""
    FAKE_HOME.mkdir(parents=True, exist_ok=True)
    return {
        "CLAUDE_CONFIG_DIR": str(CONFIG_DIR),
        "HOME": str(FAKE_HOME),
        "USERPROFILE": str(FAKE_HOME),
    }


def cli_env() -> dict[str, str]:
    """The full environment of a CLI a probe starts directly, without the SDK."""
    return reduced_env(os.environ) | home_env()


def auth_method(cli: Path) -> dict[str, Any]:
    """Only the login fields of `claude auth status`. Never the email or org."""
    done = subprocess.run(
        [str(cli), "auth", "status"],
        env=cli_env(),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    try:
        status: dict[str, Any] = json.loads(done.stdout)
    except json.JSONDecodeError:
        return {"exit": done.returncode, "parsed": False}
    keep = ("loggedIn", "authMethod", "apiProvider", "subscriptionType")
    return {key: status.get(key) for key in keep}


def require_plan_login(log: Log, cli: Path) -> None:
    """Exit before any turn unless the ship home holds a claude.ai login."""
    status = auth_method(cli)
    log(f"auth status fields: {status}")
    if not status.get("loggedIn") or status.get("apiProvider") not in (None, "firstParty"):
        log.row("plan login present", status, "BLOCKED")
        log("BLOCKED: run p_login.py with the operator at the keyboard first.")
        raise SystemExit(3)


def plan_options(**overrides: Any) -> Any:
    """`ClaudeAgentOptions` for one plan turn in the ship home, isolated from his setup."""
    from claude_agent_sdk import ClaudeAgentOptions  # noqa: PLC0415

    kwargs: dict[str, Any] = {
        "env": home_env(),
        "setting_sources": [],
        "settings": json.dumps(FORCE_LOGIN),
        "strict_mcp_config": True,
        "model": PROBE_MODEL,
        "cwd": str(SCRATCH),
        "permission_mode": "bypassPermissions",
        "max_turns": 4,
    }
    kwargs.update(overrides)
    return ClaudeAgentOptions(**kwargs)


def describe(message: Any) -> str:
    """One line per SDK message: its type plus the fields a probe reads."""
    kind = type(message).__name__
    if kind == "RateLimitEvent":
        info = message.rate_limit_info
        return f"RateLimitEvent status={info.status} type={info.rate_limit_type}"
    if kind == "ResultMessage":
        return (
            f"ResultMessage subtype={message.subtype} is_error={message.is_error} "
            f"turns={message.num_turns} ms={message.duration_ms} result={message.result!r:.200}"
        )
    if kind == "SystemMessage":
        return f"SystemMessage subtype={message.subtype}"
    if kind == "AssistantMessage":
        parts = [type(block).__name__ for block in message.content]
        return f"AssistantMessage model={message.model} blocks={parts}"
    return kind
