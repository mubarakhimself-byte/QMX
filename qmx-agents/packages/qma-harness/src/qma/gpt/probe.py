"""The GPT gate: probes run in order, each needing the previous one green.

P0 the sign-in grants `chatgpt.tokens.use.direct`. P1 `/v1/models` lists the GPT profile's
model. P2 a hello through the relay's GPT lane completes. P3 a tool call in the `qma`
namespace and its result complete two turns through the lane. P6 the bundled CLI through the
lane runs one Bash call. P7 the same through `ClaudeSDKClient` on the GPT route. P8, ChatGPT's
usage page listing QMA, is the operator's.

HP2 measured P4 and P5 on this route and HP16 builds on its row: no reasoning item came back,
so carry-over is off, and the translator drops every barred field by construction, which the
unit tests over its body hold.

P2 to P7 need a CLI talking to the GPT lane before any `ProbePassed` exists. They get it
through `ProbeDoor`, which the harness backs with `Relay.probe_grant(run)`: a single-use grant
bound to one `ProbeRun`, revoked when the run ends. The lane's only other door stays
`Relay.open_gpt_lane(ProbePassed)` (A13). `qma.gpt` never imports `qma.harness`; the door is
the seam.

The stored result lives in `<qmx_home>/state/gpt-probe.json`, inside the protected paths, keyed
to the translator's version hash. It is a correctness gate (this translator works on this
route), not a security gate: an agent with Bash under the same OS user could edit it.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, Literal, Protocol, cast

import httpx
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

from qma.gpt import translate
from qma.gpt.siwc import DIRECT_SCOPE, SignInError, SiwcSession, list_models

PROBE_FILE: Final = "gpt-probe.json"
STEP_TIMEOUT_S: Final = 240.0
BASH_PROMPT: Final = "Use Bash to run: echo hello. Then say done."
ECHO_TOOL: Final = {
    "name": "echo_word",
    "description": "Echo one word back to the caller.",
    "input_schema": {
        "type": "object",
        "properties": {"word": {"type": "string"}},
        "required": ["word"],
    },
}

_MINT: Final = object()
"""Module-private. Only this module builds a `ProbeRun` or a `ProbePassed`."""

type Step = Literal["P0", "P1", "P2", "P3", "P6", "P7"]
type Say = Callable[[str], None]


def translator_version() -> str:
    """The hash of `translate.py` as it is on disk now, read at every call, so a changed
    translator reads as unprobed without a restart. Line endings are normalized first, so a
    checkout with CRLF endings hashes the same as one with LF."""
    source = Path(translate.__file__).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(source).hexdigest()[:16]


@dataclass(frozen=True)
class ProbeRun:
    """One probe run's identity, for `Relay.probe_grant`."""

    run_id: str
    _mint: object = field(repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        if self._mint is not _MINT:
            raise TypeError("a ProbeRun is minted only by qma.gpt.probe.run_probe")


@dataclass(frozen=True)
class ProbePassed:
    """Built only by `run_probe` and `stored_result`. Guarded, not unrepresentable: Python
    cannot stop code that imports `_MINT`, and a CI check allows `ProbePassed(` only in this
    file. The guard stops an accidental unprobed GPT launch."""

    at: datetime
    translator_version: str
    model: str
    _mint: object = field(repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        if self._mint is not _MINT:
            raise TypeError("a ProbePassed is built only by qma.gpt.probe")


@dataclass(frozen=True)
class ProbeFailed:
    at: datetime
    step: Step
    detail: str


class ProbeDoor(Protocol):
    """What the probe needs from the harness: the environment of a relayed CLI launch whose
    grant is the run's probe grant, and the revoke when the run ends."""

    async def open(self, run: ProbeRun) -> Mapping[str, str]: ...
    async def close(self, run: ProbeRun) -> None: ...


class _Failed(Exception):
    def __init__(self, step: Step, detail: str) -> None:
        super().__init__(detail)
        self.step: Step = step
        self.detail = detail


async def run_probe(
    session: SiwcSession,
    door: ProbeDoor,
    *,
    model: str,
    state_dir: Path,
    workspace: Path,
    say: Say,
) -> ProbePassed | ProbeFailed:
    """Runs P0 to P7 and stores the result for this translator version. The probe grant is
    revoked at the end whatever the outcome."""
    run = ProbeRun(str(uuid.uuid4()), _mint=_MINT)
    version = translator_version()
    result: ProbePassed | ProbeFailed
    try:
        await _sign_in_steps(session, model, say)
        env = await door.open(run)
        try:
            await _lane_steps(env, model, say)
            workspace.mkdir(parents=True, exist_ok=True)
            await _cli_step(env, model, workspace, say)
            await _sdk_step(env, model, workspace, say)
        finally:
            await door.close(run)
        result = ProbePassed(datetime.now(UTC), version, model, _mint=_MINT)
    except _Failed as failed:
        say(f"{failed.step} FAIL {failed.detail}")
        result = ProbeFailed(datetime.now(UTC), failed.step, failed.detail)
    store(state_dir, result)
    return result


def store(state_dir: Path, result: ProbePassed | ProbeFailed) -> None:
    document: dict[str, object] = {"at": result.at.isoformat()}
    match result:
        case ProbePassed():
            document |= {
                "outcome": "passed",
                "translator_version": result.translator_version,
                "model": result.model,
            }
        case ProbeFailed():
            document |= {
                "outcome": "failed",
                "translator_version": translator_version(),
                "step": result.step,
                "detail": result.detail,
            }
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / PROBE_FILE
    staged = path.with_suffix(".tmp")
    staged.write_text(json.dumps(document, indent=2), encoding="utf-8")
    staged.replace(path)


def stored_result(state_dir: Path, version: str) -> ProbePassed | ProbeFailed | None:
    """A stored result for a different translator version, or none at all, reads as None."""
    try:
        document: object = json.loads((state_dir / PROBE_FILE).read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            return None
        found = cast("dict[str, Any]", document)
        if found.get("translator_version") != version:
            return None
        at = datetime.fromisoformat(str(found["at"]))
        if found.get("outcome") == "passed":
            return ProbePassed(at, version, str(found["model"]), _mint=_MINT)
        if found.get("outcome") == "failed":
            return ProbeFailed(at, cast("Step", found["step"]), str(found["detail"]))
    except OSError, ValueError, KeyError:
        return None
    return None


async def _sign_in_steps(session: SiwcSession, model: str, say: Say) -> None:
    if DIRECT_SCOPE not in session.scopes:
        raise _Failed("P0", f"the stored grant lacks {DIRECT_SCOPE}")
    say(f"P0 PASS the grant holds {DIRECT_SCOPE}")
    try:
        slugs = await list_models(session)
    except SignInError as error:
        raise _Failed("P1", str(error)) from None
    if model not in slugs:
        raise _Failed("P1", f"{model} is not among the listed models {slugs}")
    say(f"P1 PASS {model} is listed among {len(slugs)} models")


@dataclass
class _Reply:
    text: str = ""
    tools: list[tuple[str, str, dict[str, Any]]] = field(
        default_factory=list[tuple[str, str, dict[str, Any]]]
    )
    stop_reason: str | None = None
    error: str | None = None
    status: int = 0


async def _relay_turn(env: Mapping[str, str], body: dict[str, Any]) -> _Reply:
    """One streamed Anthropic request through the GPT lane, read the way the CLI reads it."""
    headers = {
        "authorization": f"Bearer {env['ANTHROPIC_AUTH_TOKEN']}",
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    reply = _Reply()
    arguments: dict[int, str] = {}
    blocks: dict[int, dict[str, Any]] = {}
    url = f"{env['ANTHROPIC_BASE_URL']}/v1/messages"
    async with (
        httpx.AsyncClient(timeout=STEP_TIMEOUT_S, trust_env=False) as client,
        client.stream("POST", url, headers=headers, json=body | {"stream": True}) as response,
    ):
        reply.status = response.status_code
        if response.status_code != 200:
            reply.error = (await response.aread()).decode(errors="replace")[:300]
            return reply
        lines: list[str] = []
        async for line in response.aiter_lines():
            if line:
                lines.append(line)
                continue
            for event in translate.parse_sse(lines):
                _read_event(event, reply, blocks, arguments)
            lines = []
        for event in translate.parse_sse(lines):
            _read_event(event, reply, blocks, arguments)
    for index, block in blocks.items():
        if block.get("type") == "tool_use":
            raw = arguments.get(index) or "{}"
            reply.tools.append((str(block["id"]), str(block["name"]), json.loads(raw)))
    return reply


def _read_event(
    event: dict[str, Any], reply: _Reply, blocks: dict[int, dict[str, Any]], args: dict[int, str]
) -> None:
    match event.get("type"):
        case "content_block_start":
            blocks[int(event["index"])] = cast("dict[str, Any]", event["content_block"])
        case "content_block_delta":
            delta = cast("dict[str, Any]", event["delta"])
            index = int(event["index"])
            if delta.get("type") == "text_delta":
                reply.text += str(delta.get("text", ""))
            elif delta.get("type") == "input_json_delta":
                args[index] = args.get(index, "") + str(delta.get("partial_json", ""))
        case "message_delta":
            reply.stop_reason = cast("dict[str, Any]", event["delta"]).get("stop_reason")
        case "error":
            reply.error = str(cast("dict[str, Any]", event.get("error") or {}).get("message"))
        case _:
            pass


async def _lane_steps(env: Mapping[str, str], model: str, say: Say) -> None:
    hello = {
        "model": model,
        "max_tokens": 64,
        "system": "You are a terse probe.",
        "messages": [{"role": "user", "content": "Say exactly: hello from QMA"}],
    }
    first = await _relay_turn(env, hello)
    if first.stop_reason != "end_turn" or first.error:
        raise _Failed("P2", f"status {first.status}, stop {first.stop_reason}, {first.error}")
    say(f"P2 PASS hello completed: {first.text[:80]!r}")
    ask = {
        "role": "user",
        "content": "Call the echo_word tool with word set to pineapple. Do not answer first.",
    }
    tools = {"model": model, "max_tokens": 256, "tools": [ECHO_TOOL], "messages": [ask]}
    call = await _relay_turn(env, tools)
    echo = [tool for tool in call.tools if tool[1] == ECHO_TOOL["name"]]
    if call.stop_reason != "tool_use" or not echo:
        raise _Failed("P3", f"no echo_word call: stop {call.stop_reason}, {call.error}")
    call_id, name, arguments = echo[0]
    turn_two = tools | {
        "messages": [
            ask,
            {
                "role": "assistant",
                "content": [{"type": "tool_use", "id": call_id, "name": name, "input": arguments}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": call_id, "content": "pineapple"}
                ],
            },
        ]
    }
    second = await _relay_turn(env, turn_two)
    if second.stop_reason != "end_turn" or second.error:
        raise _Failed("P3", f"turn two: stop {second.stop_reason}, {second.error}")
    say(f"P3 PASS echo_word({arguments}) in namespace qma, turn two completed")


def _cli_argv(cli: Path, model: str) -> list[str]:
    return [
        str(cli),
        "-p",
        BASH_PROMPT,
        "--output-format",
        "stream-json",
        "--verbose",
        "--model",
        model,
        "--tools",
        "Bash",
        "--allowedTools",
        "Bash(echo:*)",
        "--setting-sources",
        "",
        "--max-turns",
        "4",
    ]


def bundled_cli() -> Path:
    import claude_agent_sdk  # noqa: PLC0415

    name = "claude.exe" if os.name == "nt" else "claude"
    return Path(claude_agent_sdk.__file__).parent / "_bundled" / name


@dataclass
class _Turn:
    bash_calls: int = 0
    hello_seen: bool = False
    ok: bool = False
    detail: str = ""


def read_cli_stream(lines: list[str]) -> _Turn:
    """P6's verdict from the CLI's stream-json output."""
    turn = _Turn()
    for line in lines:
        try:
            message = json.loads(line)
        except ValueError:
            continue
        if not isinstance(message, dict):
            continue
        found = cast("dict[str, Any]", message)
        inner = cast("dict[str, Any]", found.get("message") or {})
        content = cast("list[dict[str, Any]]", inner.get("content") or [])
        for block in content:
            if block.get("type") == "tool_use" and block.get("name") == "Bash":
                turn.bash_calls += 1
            if block.get("type") == "tool_result" and "hello" in json.dumps(block.get("content")):
                turn.hello_seen = True
        if found.get("type") == "result":
            turn.ok = found.get("subtype") == "success" and not found.get("is_error")
            turn.detail = str(found.get("result") or found.get("subtype"))[:200]
    return turn


async def _cli_step(env: Mapping[str, str], model: str, workspace: Path, say: Say) -> None:
    def run() -> tuple[int, list[str]]:
        try:
            done = subprocess.run(
                _cli_argv(bundled_cli(), model),
                env={**os.environ, **env},
                cwd=workspace,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=STEP_TIMEOUT_S,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return -1, []
        return done.returncode, done.stdout.splitlines()

    code, lines = await asyncio.to_thread(run)
    turn = read_cli_stream(lines)
    detail = (
        f"exit {code}, Bash calls {turn.bash_calls}, hello in a tool result {turn.hello_seen}, "
        f"result ok {turn.ok}: {turn.detail!r}"
    )
    if code != 0 or not turn.bash_calls or not turn.hello_seen or not turn.ok:
        raise _Failed("P6", detail)
    say(f"P6 PASS the bundled CLI ran Bash through the GPT lane: {detail}")


async def _sdk_step(env: Mapping[str, str], model: str, workspace: Path, say: Say) -> None:
    options = ClaudeAgentOptions(
        env=dict(env),
        cwd=workspace,
        model=model,
        tools=["Bash"],
        allowed_tools=["Bash(echo:*)"],
        setting_sources=[],
        max_turns=4,
    )
    turn = _Turn()
    try:
        async with asyncio.timeout(STEP_TIMEOUT_S), ClaudeSDKClient(options) as client:
            await client.query(BASH_PROMPT)
            async for message in client.receive_response():
                _read_sdk(message, turn)
    except Exception as error:
        raise _Failed("P7", f"the SDK turn did not finish: {type(error).__name__}") from None
    detail = (
        f"Bash calls {turn.bash_calls}, hello in a tool result {turn.hello_seen}, "
        f"result ok {turn.ok}: {turn.detail!r}"
    )
    if not turn.bash_calls or not turn.hello_seen or not turn.ok:
        raise _Failed("P7", detail)
    say(f"P7 PASS ClaudeSDKClient ran Bash through the GPT lane: {detail}")


def _read_sdk(message: object, turn: _Turn) -> None:
    if isinstance(message, AssistantMessage | UserMessage) and isinstance(message.content, list):
        for block in message.content:
            if isinstance(block, ToolUseBlock) and block.name == "Bash":
                turn.bash_calls += 1
            if isinstance(block, ToolResultBlock) and "hello" in json.dumps(block.content):
                turn.hello_seen = True
    elif isinstance(message, ResultMessage):
        turn.ok = message.subtype == "success" and not message.is_error
        turn.detail = str(message.result or message.subtype)[:200]
