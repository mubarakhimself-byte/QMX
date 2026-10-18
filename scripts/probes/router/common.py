"""Shared setup of the PRB-R probes: the evidence log, the plan client env, the lane lock, the
`qmx` MCP server and one turn's outcome.

The probes drive a raw `claude_agent_sdk` client from the `qmx-agents` venv, never the
harness. Run each from `qmx-agents/` with every `ANTHROPIC_*` and `CLAUDE*` name and
`NODE_USE_SYSTEM_CA` unset, for example
`uv run --no-sync python ../scripts/probes/router/p0_parity.py`. A probe that runs a plan turn
holds `D:/QMX-worktrees/.engine-lane-lock` while it does. No probe reads the plan login or a
provider key: the CLI reads its own saved login, and P1k's keyed upstream reads the OpenRouter
key by keyring name inside the router.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

sys.path.append(str(Path(__file__).resolve().parents[1] / "engine"))
import raw_client
from raw_client import PLAN_CONFIG_DIR, home_env, lane_lock, scrub_process_env

STORE: Final = Path("D:/QMX-worktrees/qma-ship/build")
EVIDENCE: Final = STORE / "evidence" / "prb-r"
HOMES: Final = STORE / "homes"
HAIKU: Final = "haiku"
TURN_TIMEOUT_S: Final = 300.0
LOG_PREFIX: Final = os.environ.get("PRB_R_LOG_PREFIX", "owner-")
"""Read at import, before `scrub_process_env` removes the name. The checker sets `check-`."""

TOOL_SEARCH: Final = {"ENABLE_TOOL_SEARCH": "true"}
FIRST_PARTY: Final = {"_CLAUDE_CODE_ASSUME_FIRST_PARTY_BASE_URL": "1"}
"""A private CLI 2.1.299 name: its `isFirstPartyBaseUrl` check returns true when it is set."""
PLAN_LANE_ENV: Final = TOOL_SEARCH | FIRST_PARTY
"""The plan lane's launch env beyond the base URL and grant, as P0 found it."""

__all__ = ["PLAN_CONFIG_DIR", "home_env", "lane_lock", "scrub_process_env"]


def log(slug: str) -> raw_client.Log:
    """`<EVIDENCE>/<prefix>prb-r-<slug>.log`, through the EP1 probes' `Log`."""
    raw_client.EVIDENCE = EVIDENCE
    raw_client.LOG_PREFIX = LOG_PREFIX
    return raw_client.Log(f"prb-r-{slug}")


def evidence(name: str) -> Path:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    return EVIDENCE / f"{LOG_PREFIX}{name}"


def plan_env(slug: str) -> dict[str, str]:
    """A throwaway HOME with `CLAUDE_CONFIG_DIR` on the ship home's plan login folder."""
    if not (PLAN_CONFIG_DIR / ".credentials.json").exists():
        raise SystemExit("BLOCKED: the ship home has no plan login")
    return home_env(HOMES / f"prb-r-{slug}", PLAN_CONFIG_DIR)


def plan_options(**extra: Any) -> dict[str, Any]:
    """The plan client's options: no settings files, the saved claude.ai login, haiku."""
    return {
        "setting_sources": [],
        "settings": '{"forceLoginMethod": "claudeai"}',
        "strict_mcp_config": True,
        "model": HAIKU,
        "max_turns": 6,
    } | extra


def qmx_server() -> Any:
    """An in-process MCP server named `qmx` with one tool, `ping`."""
    from claude_agent_sdk import create_sdk_mcp_server, tool  # noqa: PLC0415

    @tool("ping", "Answer PONG-<WORD> for a word.", {"word": str})
    async def ping(args: dict[str, Any]) -> dict[str, Any]:
        return {"content": [{"type": "text", "text": f"PONG-{str(args['word']).upper()}"}]}

    return create_sdk_mcp_server("qmx", tools=[ping])


@dataclass
class Outcome:
    """What one client session showed: tool calls, tool results, texts and the result."""

    tool_uses: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    tool_results: list[str] = field(default_factory=list)
    texts: list[str] = field(default_factory=list)
    result: str = ""
    is_error: bool = True
    init_model: str = ""
    kinds: list[str] = field(default_factory=list)
    """Each message the SDK yielded, as its class name and subtype, in order."""
    error: str = ""


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
    return ""


async def run_session(options: Any, prompt: str) -> Outcome:
    """Send `prompt` and read until a result arrives with no sub-agent task still running.
    The CLI runs `Agent` calls in the background, so their results come back as task
    notifications and a further main turn after the first result."""
    from claude_agent_sdk import (  # noqa: PLC0415
        TERMINAL_TASK_STATUSES,
        AssistantMessage,
        ClaudeSDKClient,
        ResultMessage,
        SystemMessage,
        TaskNotificationMessage,
        TaskStartedMessage,
        TaskUpdatedMessage,
        TextBlock,
        ToolResultBlock,
        ToolUseBlock,
        UserMessage,
    )

    outcome = Outcome()
    running: set[str] = set()
    try:
        async with asyncio.timeout(TURN_TIMEOUT_S), ClaudeSDKClient(options) as client:
            await client.query(prompt)
            async for message in client.receive_messages():
                outcome.kinds.append(f"{type(message).__name__}:{getattr(message, 'subtype', '')}")
                if isinstance(message, TaskStartedMessage):
                    running.add(message.task_id)
                elif isinstance(message, TaskNotificationMessage):
                    running.discard(message.task_id)
                    outcome.tool_results.append(json.dumps(message.data))
                elif isinstance(message, TaskUpdatedMessage):
                    if (message.status or message.patch.get("status")) in TERMINAL_TASK_STATUSES:
                        running.discard(message.task_id)
                elif isinstance(message, SystemMessage) and message.subtype == "init":
                    outcome.init_model = str(message.data.get("model", ""))
                elif isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, ToolUseBlock):
                            outcome.tool_uses.append((block.name, dict(block.input)))
                        elif isinstance(block, TextBlock):
                            outcome.texts.append(block.text)
                elif isinstance(message, UserMessage):
                    if isinstance(message.content, str):
                        outcome.tool_results.append(message.content)
                    else:
                        outcome.tool_results += [
                            _content_text(b.content)
                            if isinstance(b, ToolResultBlock)
                            else str(getattr(b, "text", ""))
                            for b in message.content
                        ]
                elif isinstance(message, ResultMessage):
                    outcome.result = str(message.result or "")
                    outcome.is_error = bool(message.is_error)
                    if not running:
                        break
    except Exception as exc:
        outcome.error = f"{type(exc).__name__}: {str(exc)[:300]}"
    return outcome
