"""P3's chat half: each chat-completions row, ten turns with a tool and thinking, through the lane.

    p3_chat.py                 the cheapest OpenRouter row, its wire overridden to chat completions
    p3_chat.py <qmx_id> ...    the rows named

The probe is the lane's own client. It mints one grant per row on a loopback `Relay` and posts an
Anthropic Messages request per turn, so the key stays inside the router's keyring read and this
file never sees it. The relay's registry is the bundled one with the OpenRouter rows' `wire`
changed to `openai_chat` in memory: no profile file is written, because a probe records and a
registry PR applies.

Each turn carries one `echo` tool and `stream: true`. Every `tool_use` is fed back as a
`tool_result` under the id the lane carried, ten times in a row, so the id mapping is proved on
the provider rather than on a fixture. A row PASSes when ten turns finish, at least one turn
called the tool, and a row that declares thinking returned thinking at least once. Anything else
is a FAIL with the provider's own words, and that row stays off the chat lane.

Exit 1 on any FAIL.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from dataclasses import replace
from types import MappingProxyType
from typing import Any, Final, cast

import httpx

from qmx_router.ids import SessionId
from qmx_router.profiles import ProfileName, Profiles, parse_profiles
from qmx_router.registry import ModelRow, Registry, bundled
from qmx_router.relay import Relay, RelayUsage, keyring_secret

PROFILE: Final = ProfileName("openrouter")
TURNS: Final = 10
MAX_TOKENS: Final = 4_096
"""Above any thinking ceiling, because a provider refuses one at or below its budget."""
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


def verdict(ok: bool, line: str, detail: object = "") -> None:
    if not ok:
        FAILS.append(line)
    shown = f" {detail}" if detail != "" else ""
    log(f"{'PASS' if ok else 'FAIL'} {line}{shown}")


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


class Tee(httpx.AsyncBaseTransport):
    """Forwards to the network and keeps the chat lane's request bodies, which is where the
    thinking rule is read. Never a header, so no key reaches this list."""

    def __init__(self) -> None:
        self.inner = httpx.AsyncHTTPTransport()
        self.bodies: list[dict[str, Any]] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/v1/chat/completions"):
            self.bodies.append(json.loads(request.content))
        return await self.inner.handle_async_request(request)

    async def aclose(self) -> None:
        await self.inner.aclose()


FOREIGN = {
    "type": "thinking",
    "thinking": "a foreign provider's hidden state",
    "signature": "EqQBCgIYAhIMforeignprovidersignaturenotours==",
}
"""A thinking block another provider signed. The translator must drop it rather than replay it."""


def marked(value: object, key: str) -> list[str]:
    """Every path under `value` where an object carries `key`, so a body can be read for a field
    without a substring match on its text."""
    found: list[str] = []
    pending: list[tuple[str, object]] = [("", value)]
    while pending:
        path, item = pending.pop()
        if isinstance(item, dict):
            for name, child in cast("dict[str, Any]", item).items():
                if name == key:
                    found.append(f"{path}/{name}")
                pending.append((f"{path}/{name}", child))
        elif isinstance(item, list):
            for index, child in enumerate(cast("list[Any]", item)):
                pending.append((f"{path}[{index}]", child))
    return found


def chat_registry() -> Registry:
    """The bundled registry with every OpenRouter row on the chat wire. The profile's one base URL
    serves both routes, so `/v1/chat/completions` is the other half of the same host."""
    base = bundled()
    provider = base.provider(PROFILE)
    rows = tuple(replace(row, wire="openai_chat") for row in provider.models)
    return Registry(
        MappingProxyType({**dict(base.providers), PROFILE: replace(provider, models=rows)}),
        base.errors,
    )


def settings_row(registry: Registry) -> dict[str, Any]:
    """The key-main settings row: the profile's URL, credential and pinned tiers."""
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
    note: str | None = None,
) -> tuple[dict[str, Any], dict[str, int]]:
    """One Messages turn. Returns the assistant message and the usage it reported."""
    body: dict[str, Any] = {
        "model": row.qmx_id,
        "max_tokens": MAX_TOKENS,
        "stream": True,
        "tools": [TOOL],
        "messages": [
            *history,
            {
                "role": "user",
                "content": note
                or (
                    f"Turn {index} of {TURNS}. Call echo with text 'turn {index}', then wait for "
                    "its result."
                ),
            },
        ],
    }
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
        event = _event(line[5:])
        if event is None:
            continue
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


def _event(text: str) -> dict[str, Any] | None:
    """One `data:` payload, or None for a keep-alive or terminator a vendor adds."""
    try:
        found = json.loads(text)
    except ValueError:
        return None
    return cast("dict[str, Any]", found) if isinstance(found, dict) else None


def _json(text: str) -> dict[str, Any]:
    try:
        found = json.loads(text or "{}")
    except ValueError:
        return {}
    return cast("dict[str, Any]", found) if isinstance(found, dict) else {}


def _counts(event: dict[str, Any]) -> dict[str, int]:
    message = cast("dict[str, Any]", event.get("message", {}))
    found = event.get("usage") or message.get("usage") or {}
    return {name: value for name, value in found.items() if isinstance(value, int)}


async def probe(row: ModelRow, relay: Relay, client: httpx.AsyncClient, tee: Tee) -> None:
    """One row's ten turns. A missing keyring entry is a row FAIL, not a crash."""
    log(f"row {row.qmx_id} native={row.native} thinking={row.thinking} window={row.window}")
    try:
        handle = await relay.grant(SessionId(f"p3-chat-{row.qmx_id.replace('/', '-')}"), PROFILE)
    except Exception as error:
        verdict(False, f"{row.qmx_id} minted no grant: {error}")
        return
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
                                    {
                                        "echo": cast("dict[str, Any]", call["input"]).get(
                                            "text", ""
                                        )
                                    }
                                ),
                            }
                        ],
                    }
                )
            log(
                f"  turn {index}: text={text.strip()[:60]!r} tool_uses={len(calls)} "
                f"thinking_blocks={thinking} in={usage.get('input_tokens', 0)} "
                f"out={usage.get('output_tokens', 0)}"
            )
        ms = (time.perf_counter() - started) * 1000
        log(
            f"quirks {row.qmx_id}: tool_search={row.tool_search} thinking={row.thinking} "
            f"tools_used={tools} thinking_blocks={thinking} total_ms={ms:.0f}"
        )
        verdict(tools > 0, f"{row.qmx_id} called the echo tool inside ten turns")
        verdict(
            row.thinking == "none" or thinking > 0,
            f"{row.qmx_id} returned thinking for a row that declares it",
        )
        await foreign_turn(row, relay, client, tee, handle.secret)
        reasoning = [
            str(message["reasoning_content"])
            for body in tee.bodies
            for message in cast("list[dict[str, Any]]", body.get("messages") or [])
            if isinstance(message.get("reasoning_content"), str)
        ]
        signatures = [path for body in tee.bodies for path in marked(body, "signature")]
        verdict(
            bool(reasoning),
            f"{row.qmx_id} sent the lane's thinking back as reasoning_content",
            len(reasoning),
        )
        verdict(
            not signatures,
            f"{row.qmx_id} sent no signature field to the chat-lane model",
            signatures[:2],
        )
    except (ProbeError, httpx.HTTPError) as error:
        verdict(False, f"{row.qmx_id} stopped after {len(history)} turns: {error}")
    finally:
        await relay.revoke(handle)


async def foreign_turn(
    row: ModelRow, relay: Relay, client: httpx.AsyncClient, tee: Tee, bearer: str
) -> None:
    """One extra request whose history holds a thinking block another provider signed. The lane
    must drop it: no reasoning_content and no signature field in what leaves."""
    before = len(tee.bodies)
    history: list[Any] = [
        {"role": "user", "content": "Name a colour."},
        {"role": "assistant", "content": [FOREIGN, {"type": "text", "text": "Blue."}]},
        {"role": "user", "content": "Name another colour."},
    ]
    await turn(client, relay.base_url, bearer, row, history, 1, note="Name another colour.")
    sent = tee.bodies[before:]
    dropped = bool(sent) and not any(str(FOREIGN["thinking"]) in json.dumps(b) for b in sent)
    clean = all(not marked(body, "signature") for body in sent)
    verdict(
        dropped and clean,
        f"{row.qmx_id} dropped a thinking block another provider signed",
        f"requests={len(sent)} dropped={dropped} clean={clean}",
    )


def cheapest(registry: Registry) -> ModelRow:
    """The provider's cheapest row: the one OpenRouter spend this probe is allowed."""
    return min(
        registry.provider(PROFILE).models, key=lambda row: (row.class_ != "cheap", row.qmx_id)
    )


async def main(selected: list[str]) -> int:
    registry = chat_registry()
    targets = (
        [row for row in registry.provider(PROFILE).models if row.qmx_id in selected]
        if selected
        else [cheapest(registry)]
    )
    if not targets:
        raise SystemExit(f"no OpenRouter row matches {selected}")
    profiles: Profiles = parse_profiles({PROFILE: settings_row(registry)}, allow_loopback_http=True)
    tee = Tee()
    relay = await Relay(
        secrets=keyring_secret,
        journal=lambda _session: Journal(),
        alert=alert,
        profiles=lambda: profiles,
        registry=chat_registry,
        transport=tee,
    ).start()
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
            for row in targets:
                await probe(row, relay, client, tee)
    finally:
        await relay.close()
    log(f"{len(targets)} chat-wire rows probed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
