"""P3's key half: each OpenRouter row, ten turns with a tool and thinking, through the router.

    p3_key.py            every row the OpenRouter profile lists
    p3_key.py <qmx_id>   one row

The probe is the router's own client. It mints one grant per row on a loopback `Relay` and posts
an Anthropic Messages request per turn, so the key stays inside the router's keyring read and this
file never sees it. Each turn carries one `echo` tool and a thinking budget. Every `tool_use` is
fed back as a `tool_result`, ten times, and each row ends with a PASS or FAIL plus its quirks.

A row FAILs when a turn errors, when ten turns finish without a tool call, or when a row that
declares thinking returns no thinking block. Quirks are printed for the registry rows to carry;
this probe writes no profile, because a probe records and a registry PR applies.

Exit 1 on any FAIL.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from typing import Any, Final, cast

import httpx
from qmx_router.ids import SessionId
from qmx_router.profiles import ProfileName, parse_profiles
from qmx_router.registry import ModelRow, Registry, bundled
from qmx_router.relay import Relay, RelayUsage, keyring_secret

PROFILE: Final = ProfileName("openrouter")
TURNS: Final = 10
BUDGET: Final = 1_024
MAX_TOKENS: Final = 1_024
TIMEOUT_S: Final = 240.0
TOOL: Final[dict[str, Any]] = {
    "name": "echo",
    "description": "Echo one short line back.",
    "input_schema": {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    },
}
FAILS: list[str] = []


class ProbeError(Exception):
    """One row stopped early, named with what the provider said."""


def log(line: str) -> None:
    print(line, flush=True)


def verdict(ok: bool, line: str) -> None:
    if not ok:
        FAILS.append(line)
    log(f"{'PASS' if ok else 'FAIL'} {line}")


class Journal:
    def append(self, usage: RelayUsage) -> None:
        log(
            f"  journal {usage.model} status={usage.status} in={usage.input_tokens} "
            f"out={usage.output_tokens} cache_read={usage.cache_read_tokens}"
        )

    def close(self) -> None:
        return None


async def alert(_session: SessionId, reason: str) -> None:
    log(f"  alert {reason}")


def profile_row(registry: Registry) -> dict[str, Any]:
    """The settings row a key main needs: the bundled profile's URL, credential and natives."""
    provider = registry.provider(PROFILE)
    tiers = dict.fromkeys(("opus", "sonnet", "haiku", "fable"), provider.models[0].native)
    return {
        "base_url": provider.url,
        "credential_ref": provider.credentials[0],
        "tiers": tiers,
    }


async def turn(
    client: httpx.AsyncClient,
    base: str,
    bearer: str,
    row: ModelRow,
    history: list[Any],
    index: int,
) -> tuple[dict[str, Any], dict[str, int]]:
    """One Messages turn. Returns the assistant message and the usage it reported."""
    body: dict[str, Any] = {
        "model": row.qmx_id,
        "max_tokens": MAX_TOKENS,
        "tools": [TOOL],
        "messages": [
            *history,
            {
                "role": "user",
                "content": (
                    f"Turn {index} of {TURNS}. Call echo with text 'turn {index}', then wait for "
                    "its result."
                ),
            },
        ],
    }
    if row.thinking != "none":
        body["thinking"] = {"type": "enabled", "budget_tokens": BUDGET}
    async with client.stream(
        "POST", f"{base}/v1/messages", json=body, headers={"authorization": f"Bearer {bearer}"}
    ) as answer:
        if answer.status_code != 200:
            detail = (await answer.aread()).decode("latin-1")[:300]
            raise ProbeError(f"HTTP {answer.status_code}: {detail}")
        blocks, usage = await collect(answer)
    return {"role": "assistant", "content": blocks}, usage


async def collect(answer: httpx.Response) -> tuple[list[Any], dict[str, int]]:
    """The assistant's blocks from one SSE stream, merged by block index."""
    blocks: dict[int, dict[str, Any]] = {}
    partial: dict[int, str] = {}
    usage: dict[str, int] = {}
    kind = ""
    async for line in answer.aiter_lines():
        if line.startswith("event:"):
            kind = line[6:].strip()
            continue
        if not line.startswith("data:"):
            continue
        event = cast("dict[str, Any]", json.loads(line[5:]))
        match kind:
            case "message_start":
                usage |= _counts(event)
            case "content_block_start":
                index = int(event["index"])
                blocks[index] = dict(event["content_block"])
                partial[index] = ""
            case "content_block_delta":
                index = int(event["index"])
                delta = cast("dict[str, Any]", event["delta"])
                match delta.get("type"):
                    case "text_delta":
                        partial[index] += str(delta.get("text", ""))
                    case "thinking_delta":
                        partial[index] += str(delta.get("thinking", ""))
                    case "signature_delta":
                        blocks[index]["signature"] = str(delta.get("signature", ""))
                    case "input_json_delta":
                        partial[index] += str(delta.get("partial_json", ""))
            case "content_block_stop":
                index = int(event["index"])
                block = blocks[index]
                if block.get("type") == "tool_use":
                    block["input"] = _json(partial[index])
                elif block.get("type") == "text":
                    block["text"] = partial[index]
                elif block.get("type") == "thinking":
                    block["thinking"] = partial[index]
            case "message_delta":
                usage |= _counts(event)
            case "error":
                raise ProbeError(str(event.get("error", event)))
    return [blocks[index] for index in sorted(blocks)], usage


def _json(text: str) -> dict[str, Any]:
    try:
        found = json.loads(text or "{}")
    except ValueError:
        return {}
    return cast("dict[str, Any]", found) if isinstance(found, dict) else {}


def _counts(event: dict[str, Any]) -> dict[str, int]:
    found = (
        event.get("usage") or cast("dict[str, Any]", event.get("message", {})).get("usage") or {}
    )
    return {name: value for name, value in found.items() if isinstance(value, int)}


async def probe(row: ModelRow, relay: Relay, client: httpx.AsyncClient, session: str) -> None:
    log(f"row {row.qmx_id} native={row.native} thinking={row.thinking} window={row.window}")
    handle = await relay.grant(SessionId(session), PROFILE)
    history: list[Any] = []
    thinking = 0
    tools = 0
    started = time.perf_counter()
    try:
        for index in range(1, TURNS + 1):
            message, usage = await turn(client, relay.base_url, handle.secret, row, history, index)
            content = cast("list[dict[str, Any]]", message["content"])
            text = "".join(
                str(block.get("text", "")) for block in content if block.get("type") == "text"
            )
            calls = [block for block in content if block.get("type") == "tool_use"]
            thinking += sum(1 for block in content if block.get("type") == "thinking")
            tools += len(calls)
            history.append(message)
            for call in calls:
                history.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": call["id"],
                                "content": json.dumps(
                                    {"echo": cast("dict[str, Any]", call["input"]).get("text", "")}
                                ),
                            }
                        ],
                    }
                )
            log(
                f"  turn {index}: text={text.strip()[:60]!r} tool_uses={len(calls)} "
                f"thinking={thinking} in={usage.get('input_tokens', 0)} "
                f"out={usage.get('output_tokens', 0)}"
            )
        ms = (time.perf_counter() - started) * 1000
        log(
            f"quirks {row.qmx_id}: tool_search={row.tool_search} tools_used={tools} "
            f"thinking_blocks={thinking} total_ms={ms:.0f}"
        )
        verdict(tools > 0, f"{row.qmx_id} called the echo tool inside ten turns")
        verdict(
            row.thinking == "none" or thinking > 0,
            f"{row.qmx_id} returned thinking for a row that declares it",
        )
    except (ProbeError, httpx.HTTPError) as error:
        verdict(False, f"{row.qmx_id} stopped after {len(history)} turns: {error}")
    finally:
        await relay.revoke(handle)


async def main(selected: list[str]) -> int:
    registry = bundled()
    provider = registry.provider(PROFILE)
    targets = [row for row in provider.models if not selected or row.qmx_id in selected]
    if not targets:
        raise SystemExit(f"no OpenRouter row matches {selected}")
    profiles = parse_profiles({PROFILE: profile_row(registry)}, allow_loopback_http=True)
    relay = await Relay(
        secrets=keyring_secret,
        journal=lambda _session: Journal(),
        alert=alert,
        profiles=lambda: profiles,
    ).start()
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
            for row in targets:
                await probe(row, relay, client, f"p3-{row.qmx_id.replace('/', '-')}")
    finally:
        await relay.close()
    log(f"{len(targets)} OpenRouter rows probed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
