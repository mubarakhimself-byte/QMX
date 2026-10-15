"""Shared parts of the HP8 money and credential checks on the fake model.

A check scripts tool calls for the fake model, runs one key chat on it through the real CLI and
relay, then reads each call's outcome from the `tool_result` blocks the CLI sent back. An
outcome is `hook` (the gate denied it, the text names the money rule), `rule` (a deny rule in
`disallowed_tools` refused it), `timeout` (the hook outlived its timeout and the CLI blocked
the call), or `ran`.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal

from common import CANARY, FAKE_HOME, SCRATCH, Log, Session, fake_row, put_providers
from fake_model import FakeModel, Turn, text, tool_use

Outcome = Literal["hook", "rule", "timeout", "ran", "missing"]

HOOK_MARK: Final = "money rule:"
AGENT_PROMPT: Final = "QMA sub-agent: run the scripted checks."


@dataclass(frozen=True)
class Call:
    label: str
    tool: str
    tool_input: dict[str, Any]


def direct_row(url: str) -> dict[str, Any]:
    """The fake profile with tool search off, so MCP tools are offered directly."""
    return fake_row(url) | {"quirks": {"env": {"ENABLE_TOOL_SEARCH": "false"}}}


def fake_for(calls: list[Call], *, in_agent: bool) -> FakeModel:
    """One turn per call, then a closing text. Inside a sub-agent, the parent's only call
    starts a general-purpose agent, and the agent's own conversation makes the calls."""
    turns = [Turn([tool_use(call.tool, call.tool_input)]) for call in calls]
    turns.append(Turn([text("calls done")]))
    if not in_agent:
        return FakeModel(turns)
    agent = tool_use(
        "Agent",
        {
            "description": "Run the checks",
            "prompt": AGENT_PROMPT,
            "subagent_type": "general-purpose",
            "run_in_background": False,
        },
    )
    return FakeModel([Turn([agent]), Turn([text("agent done")])], routes={AGENT_PROMPT: turns})


def results(fake: FakeModel) -> dict[str, tuple[str, dict[str, Any], bool, str]]:
    """Every tool call the fake model made, by id: tool, input, is_error and result text."""
    uses: dict[str, tuple[str, dict[str, Any]]] = {}
    outcomes: dict[str, tuple[bool, str]] = {}
    for seen in fake.requests:
        for message in seen.json.get("messages", []):
            content = message.get("content")
            for block in content if isinstance(content, list) else []:
                if block.get("type") == "tool_use":
                    uses[block["id"]] = (block["name"], block.get("input", {}))
                elif block.get("type") == "tool_result":
                    body = block.get("content")
                    flat = (
                        body
                        if isinstance(body, str)
                        else " ".join(part.get("text", "") for part in body or [])
                    )
                    outcomes[block["tool_use_id"]] = (bool(block.get("is_error")), flat)
    return {key: (*uses[key], *outcomes.get(key, (False, "<no result>"))) for key in uses}


def outcome_of(
    call: Call, found: dict[str, tuple[str, dict[str, Any], bool, str]]
) -> tuple[Outcome, str]:
    for tool, tool_input, is_error, result in found.values():
        if tool == call.tool and call.tool_input.items() <= tool_input.items():
            if HOOK_MARK in result:
                return "hook", result
            if "did not respond before its timeout" in result:
                return "timeout", result
            if is_error and ("denied" in result.lower() or "permission" in result.lower()):
                return "rule", result
            return "ran", result
    return "missing", ""


def in_subagent(fake: FakeModel, call: Call) -> bool:
    """True when a request of the sub-agent's own conversation, whose first message is
    `AGENT_PROMPT`, carries this call."""
    for seen in fake.requests:
        messages = seen.json.get("messages", [])
        if messages and AGENT_PROMPT in json.dumps(messages[0]):
            uses = [
                block.get("input", {})
                for message in messages
                for block in (
                    message.get("content") if isinstance(message.get("content"), list) else []
                )
                if block.get("type") == "tool_use" and block.get("name") == call.tool
            ]
            if any(call.tool_input.items() <= used.items() for used in uses):
                return True
    return False


def plant_personal_login() -> Path:
    """A canary login in the throwaway HOME's `.claude`, the gate's personal home here."""
    personal = FAKE_HOME / ".claude"
    personal.mkdir(parents=True, exist_ok=True)
    login = personal / ".credentials.json"
    login.write_text(json.dumps({"claudeAiOauth": {"accessToken": CANARY}}), encoding="utf-8")
    return login


def relative(target: Path, start: Path) -> str:
    return os.path.relpath(target, start).replace("\\", "/")


async def run_calls(
    log: Log,
    root: Path,
    calls: list[Call],
    *,
    test: Any,
    mode: str,
    tools: list[str],
    in_agent: bool = False,
    title: str,
    workspace: Path | None = None,
) -> tuple[Session, FakeModel, dict[str, tuple[Outcome, str]]]:
    """One key chat on the fake model making `calls`. The caller closes the session and the
    fake model."""
    fake = fake_for(calls, in_agent=in_agent).start()
    put_providers(root, {"fake": direct_row(fake.url)})
    session = await Session.start(
        root,
        model="opus",
        workspace=workspace or SCRATCH / "workspace",
        title=title,
        test=test,
        profile="fake",
        mode=mode,
        tools=tools,
    )
    await session.turn(log, "Run the scripted checks.")
    found = results(fake)
    outcomes = {call.label: outcome_of(call, found) for call in calls}
    for call in calls:
        kind, said = outcomes[call.label]
        log(f"  {call.label}: {call.tool} -> {kind}: {said[:200]!r}")
    return session, fake, outcomes
