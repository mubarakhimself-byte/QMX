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
from collections.abc import Generator, Mapping, MutableMapping
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, TextIO

if TYPE_CHECKING:
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, ContentBlock, Message

SHIP: Final = Path("D:/QMX-worktrees/qma-ship")
CONFIG_DIR: Final = SHIP / "home" / "claude"
EVIDENCE: Final = SHIP / "evidence" / "hp0"
PROBE_VENV: Final = SHIP / "probe-venv"
SCRATCH: Final = Path("D:/Temp/qma-hp0")
UV_CACHE: Final = Path("D:/Caches/uv")
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
    head = text.strip().split()[0]
    return tuple(int(part) for part in head.split("."))


class Log:
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
        self(f"FINDING\t{question}\t{value}\t{verdict}")


def bundled_cli() -> Path:
    import claude_agent_sdk  # noqa: PLC0415

    exe = "claude.exe" if os.name == "nt" else "claude"
    return Path(claude_agent_sdk.__file__).parent / "_bundled" / exe


def sdk_version() -> str:
    from claude_agent_sdk import __version__  # noqa: PLC0415

    return __version__


def uv_env() -> dict[str, str]:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    return (
        {"UV_CACHE_DIR": str(UV_CACHE)}
        | dict(os.environ)
        | {"TMP": str(SCRATCH), "TEMP": str(SCRATCH)}
    )


def home_env() -> dict[str, str]:
    FAKE_HOME.mkdir(parents=True, exist_ok=True)
    return {
        "CLAUDE_CONFIG_DIR": str(CONFIG_DIR),
        "HOME": str(FAKE_HOME),
        "USERPROFILE": str(FAKE_HOME),
    }


def cli_env() -> dict[str, str]:
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
    """Checks only that the credentials file exists, never its content, before any CLI start,
    so a probe run without the login leaves the ship home untouched."""
    status: dict[str, Any] = {"credentials_file": (CONFIG_DIR / ".credentials.json").exists()}
    if status["credentials_file"]:
        status = auth_method(cli)
    log(f"auth status fields: {status}")
    if not status.get("loggedIn") or status.get("apiProvider") not in (None, "firstParty"):
        log.row("plan login present", status, "BLOCKED")
        log("BLOCKED: run p_login.py with the operator at the keyboard first.")
        raise SystemExit(3)


def plan_options(**overrides: Any) -> ClaudeAgentOptions:
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
    return ClaudeAgentOptions(**(kwargs | overrides))


def describe(message: Message) -> str:
    from claude_agent_sdk import (  # noqa: PLC0415
        AssistantMessage,
        RateLimitEvent,
        ResultMessage,
        SystemMessage,
        UserMessage,
    )

    match message:
        case RateLimitEvent(rate_limit_info=info):
            return f"RateLimitEvent status={info.status} type={info.rate_limit_type}"
        case ResultMessage():
            return (
                f"ResultMessage subtype={message.subtype} is_error={message.is_error} "
                f"turns={message.num_turns} ms={message.duration_ms} "
                f"result={message.result!r:.200}"
            )
        case SystemMessage():
            return f"SystemMessage subtype={message.subtype}"
        case AssistantMessage():
            return f"AssistantMessage model={message.model} blocks={_blocks(message.content)}"
        case UserMessage(content=list() as content):
            return f"UserMessage blocks={_blocks(content)}"
        case _:
            return type(message).__name__


def _blocks(blocks: list[ContentBlock]) -> list[str]:
    from claude_agent_sdk import TextBlock, ToolResultBlock, ToolUseBlock  # noqa: PLC0415

    def one(block: ContentBlock) -> str:
        match block:
            case TextBlock():
                return f"Text({block.text!r:.200})"
            case ToolUseBlock():
                return f"ToolUse({block.name} {json.dumps(block.input)[:200]})"
            case ToolResultBlock():
                return f"ToolResult(error={block.is_error} {str(block.content)[:300]!r})"
            case _:
                return type(block).__name__

    return [one(block) for block in blocks]


def is_ok(messages: list[Message]) -> bool:
    from claude_agent_sdk import ResultMessage  # noqa: PLC0415

    results = [m for m in messages if isinstance(m, ResultMessage)]
    return bool(results) and not results[-1].is_error


@contextmanager
def tap_raw(log: Log) -> Generator[None]:
    """Log every frame the CLI sends, cut to 800 characters, before the SDK parses or drops it."""
    from claude_agent_sdk._internal import message_parser  # noqa: PLC0415

    parse = message_parser.parse_message

    def logged(data: dict[str, Any]) -> Message | None:
        log(f"raw {json.dumps(data)[:800]}")
        return parse(data)

    message_parser.parse_message = logged
    try:
        yield
    finally:
        message_parser.parse_message = parse


async def run_turns(log: Log, options: ClaudeAgentOptions, prompts: list[str]) -> list[Message]:
    from claude_agent_sdk import ClaudeSDKClient  # noqa: PLC0415

    seen: list[Message] = []
    async with ClaudeSDKClient(options=options) as client:
        for prompt in prompts:
            log(f"> {prompt}")
            await client.query(prompt)
            async for message in client.receive_response():
                log(describe(message))
                seen.append(message)
    return seen


def cli_pid(client: ClaudeSDKClient) -> int:
    transport: Any = client._transport  # pyright: ignore[reportPrivateUsage]
    return int(transport._process.pid)


def working_set_mb(pid: int) -> float:
    import ctypes  # noqa: PLC0415
    from ctypes import wintypes  # noqa: PLC0415

    class Counters(ctypes.Structure):
        _fields_ = (
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        )

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    query_limited_and_vm_read = 0x1000 | 0x0010
    handle = kernel32.OpenProcess(query_limited_and_vm_read, False, pid)
    if not handle:
        raise OSError(ctypes.get_last_error(), f"OpenProcess {pid}")
    try:
        counters = Counters()
        counters.cb = ctypes.sizeof(Counters)
        if not kernel32.K32GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            raise OSError(ctypes.get_last_error(), f"K32GetProcessMemoryInfo {pid}")
        return round(counters.WorkingSetSize / 2**20, 1)
    finally:
        kernel32.CloseHandle(handle)
