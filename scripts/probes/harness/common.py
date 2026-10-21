"""Shared pieces of the PRB-H probes: the verdict shape, the evidence log, plan-login options
for a raw `claude_agent_sdk` client, a turn reader and an argv tap.

The probes drive the pinned SDK 0.2.166 and its bundled CLI 2.1.299 directly. No probe imports
the harness, so each result describes the CLI, not QMX code. Build the probe venv once:

    uv venv D:/QMX-worktrees/qma-ship/build/homes/prb-h-venv --python 3.14
    uv pip install --python <venv>/Scripts/python.exe claude-agent-sdk==0.2.166

then run a probe from this folder with `<venv>/Scripts/python.exe p_set.py`. Model turns run on
`haiku` through the ship home's plan login while the probe holds the engine lane lock. Each
chat gets a throwaway HOME under the store's `homes/`, `setting_sources=[]` and
`strict_mcp_config=True`. The verdict functions are pure, so `test_probes.py` runs them on
recorded observations with no SDK installed.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
from collections.abc import Awaitable, Callable, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Final, TextIO

sys.path.append(str(Path(__file__).resolve().parents[1] / "engine"))
from raw_client import PLAN_CONFIG_DIR, home_env, lane_lock, scrub_process_env

STORE: Final = Path("D:/QMX-worktrees/qma-ship/build")
EVIDENCE: Final = STORE / "evidence" / "prb-h"
HOMES: Final = STORE / "homes"
SHIP_SETTINGS: Final = Path("D:/QMX-worktrees/qma-ship/home/settings.toml")
FIXTURES: Final = Path(__file__).resolve().parent / "fixtures"
LIVE_QMA: Final = Path(__file__).resolve().parents[2] / "live" / "qma"
"""Where `fake_model.py` lives, for the probes that read what the CLI puts on the wire."""
LOG_PREFIX: Final = os.environ.get("PRB_H_LOG_PREFIX", "owner-")
"""Read at import, before `scrub_process_env` removes the name."""
PLAN_MODEL: Final = "haiku"
TURN_TIMEOUT_S: Final = 240.0
ARGV_BUDGET: Final = 30_000
"""The harness's own command-line check (`qma/harness/launch.py` `ARGV_BUDGET` on
`origin/engine/base`), restated so no probe imports the harness."""

__all__ = [
    "ARGV_BUDGET",
    "EVIDENCE",
    "FIXTURES",
    "HOMES",
    "LIVE_QMA",
    "PLAN_CONFIG_DIR",
    "PLAN_MODEL",
    "Case",
    "Log",
    "Verdict",
    "argv_tap",
    "argv_value",
    "fresh",
    "home_env",
    "lane_lock",
    "plan_env",
    "quoted_length",
    "scrub_process_env",
    "ship_settings_hash",
    "turn",
]


@dataclass(frozen=True)
class Case:
    name: str
    ok: bool
    seen: object


@dataclass(frozen=True)
class Verdict:
    """A probe's result. `fallback` is the plan's text for what a FAIL triggers; it is quoted in
    FINDINGS.md and never chosen here."""

    probe: str
    cases: tuple[Case, ...]
    fallback: str

    @property
    def passed(self) -> bool:
        return bool(self.cases) and all(case.ok for case in self.cases)

    def failed(self) -> list[str]:
        return [case.name for case in self.cases if not case.ok]


class Log:
    """Writes `<EVIDENCE>/<PRB_H_LOG_PREFIX><slug>.log` and, with `save`, the observation the
    verdict read as `<slug>.json` beside it."""

    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.slug = slug
        self.path = EVIDENCE / f"{LOG_PREFIX}{slug}.log"
        self._file: TextIO = self.path.open("w", encoding="utf-8")
        self(f"=== {slug} {time.strftime('%Y-%m-%dT%H:%M:%S%z')} python {sys.version.split()[0]}")

    def __call__(self, line: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {line}"
        print(stamped.encode("ascii", "backslashreplace").decode(), flush=True)
        self._file.write(stamped + "\n")
        self._file.flush()

    def save(self, observation: dict[str, Any]) -> Path:
        path = EVIDENCE / f"{LOG_PREFIX}{self.slug}.json"
        path.write_text(json.dumps(observation, indent=2, default=str), encoding="utf-8")
        self(f"observation saved to {path}")
        return path

    def verdict(self, verdict: Verdict) -> int:
        for case in verdict.cases:
            self(f"{'PASS' if case.ok else 'FAIL'} {verdict.probe} {case.name}: {case.seen}")
        if verdict.passed:
            self(f"PASS {verdict.probe}")
        else:
            self(f"FAIL {verdict.probe} ({', '.join(verdict.failed())})")
            self(f"FALLBACK {verdict.probe}: {verdict.fallback}")
        self._file.close()
        return 0 if verdict.passed else 1


def ship_settings_hash() -> str:
    return hashlib.sha256(SHIP_SETTINGS.read_bytes()).hexdigest()


def fresh(slug: str) -> Path:
    """An empty folder `homes/prb-h-<slug>`."""
    root = HOMES / f"prb-h-{slug}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


def plan_env(slug: str) -> dict[str, str]:
    """A throwaway HOME for one chat, with `CLAUDE_CONFIG_DIR` on the ship home's plan login."""
    if not (PLAN_CONFIG_DIR / ".credentials.json").exists():
        raise SystemExit("BLOCKED: the ship home has no plan login")
    return home_env(HOMES / f"prb-h-{slug}-home", PLAN_CONFIG_DIR)


@dataclass
class TurnSeen:
    """What one `query` produced, as plain data for the observation file."""

    texts: list[str] = field(default_factory=list[str])
    tool_uses: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])
    tool_results: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])
    init: dict[str, Any] = field(default_factory=dict[str, Any])
    system: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])
    usage: dict[str, Any] = field(default_factory=dict[str, Any])
    subtype: str = ""
    session_id: str = ""
    num_turns: int = 0
    seconds: float = 0.0

    def text(self) -> str:
        return "\n".join(self.texts)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _result_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
    return str(content)


async def turn(client: Any, prompt: str, say: Callable[[str], None]) -> TurnSeen:
    """Send `prompt` and read to its `ResultMessage`, logging each tool call and result."""
    import asyncio  # noqa: PLC0415

    from claude_agent_sdk import (  # noqa: PLC0415
        AssistantMessage,
        ResultMessage,
        SystemMessage,
        TextBlock,
        ToolResultBlock,
        ToolUseBlock,
        UserMessage,
    )

    seen = TurnSeen()
    started = time.perf_counter()
    async with asyncio.timeout(TURN_TIMEOUT_S):
        await client.query(prompt)
        async for message in client.receive_response():
            if isinstance(message, SystemMessage) and message.subtype == "init":
                seen.init = dict(message.data)
            elif isinstance(message, SystemMessage):
                seen.system.append({"subtype": message.subtype, "data": json.dumps(message.data)})
            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        seen.texts.append(block.text)
                    elif isinstance(block, ToolUseBlock):
                        seen.tool_uses.append(
                            {"id": block.id, "name": block.name, "input": block.input}
                        )
                        say(f"  tool_use {block.name} {json.dumps(block.input)[:300]}")
            elif isinstance(message, UserMessage) and isinstance(message.content, list):
                for block in message.content:
                    if isinstance(block, ToolResultBlock):
                        body = _result_text(block.content)
                        seen.tool_results.append(
                            {
                                "id": block.tool_use_id,
                                "is_error": bool(block.is_error),
                                "text": body,
                            }
                        )
                        say(f"  tool_result error={bool(block.is_error)} {body[:300]!r}")
            elif isinstance(message, ResultMessage):
                seen.usage = dict(message.usage or {})
                seen.subtype = message.subtype
                seen.session_id = message.session_id
                seen.num_turns = message.num_turns
    seen.seconds = round(time.perf_counter() - started, 2)
    say(
        f"  turn {seen.subtype} in {seen.seconds} s, {seen.num_turns} model turns, cache read "
        f"{seen.usage.get('cache_read_input_tokens')}, cache write "
        f"{seen.usage.get('cache_creation_input_tokens')}; text {seen.text()[:300]!r}"
    )
    return seen


@contextmanager
def argv_tap() -> Iterator[list[list[str]]]:
    """Every argv the SDK builds for a CLI start while the block runs."""
    from claude_agent_sdk._internal.transport.subprocess_cli import (  # noqa: PLC0415
        SubprocessCLITransport,
    )

    seen: list[list[str]] = []
    original = SubprocessCLITransport._build_command  # pyright: ignore[reportPrivateUsage]

    def tapped(self: Any) -> list[str]:
        argv = original(self)
        seen.append(list(argv))
        return argv

    SubprocessCLITransport._build_command = tapped  # pyright: ignore[reportPrivateUsage]
    try:
        yield seen
    finally:
        SubprocessCLITransport._build_command = original  # pyright: ignore[reportPrivateUsage]


ToolHandler = Callable[[dict[str, Any]], Awaitable[str]]


def answers(text: str) -> ToolHandler:
    async def handler(_: dict[str, Any]) -> str:
        return text

    return handler


class QmxServer:
    """One in-process MCP server, as the harness's `qmx` server is, whose tool list the probe
    changes mid-session by editing `tools`. It counts `tools/list` requests, records each call,
    and keeps the session it was listed on so it can send `tools/list_changed` from outside a
    request, as the harness would."""

    def __init__(self, tools: dict[str, ToolHandler], name: str = "qmx") -> None:
        from mcp.server import Server  # noqa: PLC0415
        from mcp.server.lowlevel.server import NotificationOptions  # noqa: PLC0415

        self.name = name
        self.tools = dict(tools)
        self.list_calls = 0
        self.listed: list[list[str]] = []
        self.calls: list[str] = []
        self.session: Any = None

        server: Any = Server(
            name, version="1.0.0", on_list_tools=self._list, on_call_tool=self._call
        )
        plain = server.create_initialization_options

        def advertise_list_changed(*_: Any, **__: Any) -> Any:
            return plain(NotificationOptions(tools_changed=True))

        server.create_initialization_options = advertise_list_changed
        self.server = server

    @property
    def config(self) -> dict[str, Any]:
        return {"type": "sdk", "name": self.name, "instance": self.server}

    def wire(self, tool: str) -> str:
        return f"mcp__{self.name}__{tool}"

    async def _list(self, ctx: Any, _params: Any) -> Any:
        from mcp.types import ListToolsResult, Tool  # noqa: PLC0415

        self.list_calls += 1
        self.session = getattr(ctx, "session", None)
        self.listed.append(sorted(self.tools))
        return ListToolsResult(
            tools=[
                Tool(
                    name=tool,
                    description=f"Probe tool {tool}. Takes no arguments.",
                    input_schema={"type": "object", "properties": {}},
                )
                for tool in self.tools
            ]
        )

    async def _call(self, _ctx: Any, params: Any) -> Any:
        from mcp.types import CallToolResult, TextContent  # noqa: PLC0415

        self.calls.append(str(params.name))
        handler = self.tools.get(str(params.name))
        if handler is None:
            return CallToolResult(
                content=[TextContent(type="text", text=f"no tool {params.name}")], is_error=True
            )
        text = await handler(dict(params.arguments or {}))
        return CallToolResult(content=[TextContent(type="text", text=text)], is_error=False)

    async def send_list_changed(self) -> str:
        """Send `notifications/tools/list_changed` on the session the CLI listed on."""
        if self.session is None:
            return "no session captured"
        try:
            await self.session.send_tool_list_changed()
        except Exception as error:
            return f"raised {type(error).__name__}: {error}"
        return "sent"


def argv_value(argv: Iterable[str], flag: str) -> str | None:
    items = list(argv)
    for index, item in enumerate(items[:-1]):
        if item == flag:
            return items[index + 1]
    return None


def quoted_length(argv: list[str]) -> int:
    """The command line length after Windows quoting, as the harness's check measures it."""
    import subprocess  # noqa: PLC0415

    return len(subprocess.list2cmdline(argv))
