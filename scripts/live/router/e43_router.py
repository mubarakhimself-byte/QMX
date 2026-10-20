"""E43's router half: a slow prefill is never resent, and a late usage limit stops the CLI.

    e43_router.py            run the three cases

One fake upstream, one relay, one 1M-token prompt. The fake answers the first case after 400 s
and the second after 900 s, both inside and past the row's first-token bound of 120 s plus 60 s
per 100k tokens, which is 720 s for this prompt. The third case is a usage-limit 429 after 15 s.
The client plays the CLI: it retries up to `CLI_RETRIES` times unless the answer carries
`x-should-retry: false`.

PASS lines:

- 400 s: the first event arrives after the full delay and the upstream saw one request for it.
- 900 s: the relay stops the request at its own bound, sends its error event, and the upstream
  saw one request for it. Nothing was resent.
- 429: the answer carries `x-should-retry: false` and the CLI made one request.

About 19 minutes of wall time, all of it waiting on the fake. Exit 1 on any FAIL.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import sys
import time
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final

import httpx
from qmx_router.ids import SessionId
from qmx_router.profiles import ModelId, ProfileName, parse_profiles
from qmx_router.registry import ModelRow, Provider, QmxId, Registry
from qmx_router.relay import Relay, RelayUsage

PROFILE: Final = ProfileName("fake")
ROW: Final = "fake/one-million"
NATIVE: Final = "fake-1m"
DELAY_S: Final = 400.0
LATE_S: Final = 900.0
BOUND_S: Final = 720.0
"""120 s plus 60 s per 100k tokens on a 1M-token prompt (AD-50 (8), Appendix H)."""
LATE_429_S: Final = 15.0
PROMPT_CHARS: Final = 3_000_000
"""About 1M prompt tokens at the row's chars_per_token of 3."""
USAGE: Final = "You have hit your usage limit"
CLI_RETRIES: Final = 10
TOLERANCE_S: Final = 15.0
FAILS: list[str] = []


class Journal:
    def append(self, usage: RelayUsage) -> None:
        log(
            f"  journal {usage.model} status={usage.status} in={usage.input_tokens} "
            f"out={usage.output_tokens}"
        )

    def close(self) -> None:
        return None


def log(line: str) -> None:
    print(line, flush=True)


def verdict(ok: bool, line: str) -> None:
    if not ok:
        FAILS.append(line)
    log(f"{'PASS' if ok else 'FAIL'} {line}")


async def alert(_session: SessionId, reason: str) -> None:
    log(f"  alert {reason}")


@dataclass(frozen=True)
class Scenario:
    delay_s: float
    status: int
    body: bytes = b""


class FakeUpstream:
    """A raw HTTP/1.1 responder: one scenario per request, in order, after its delay."""

    def __init__(self) -> None:
        self.scenarios: list[Scenario] = []
        self.requests: list[float] = []
        self.port = 0
        self._server: asyncio.Server | None = None

    async def start(self) -> FakeUpstream:
        self._server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        self.port = self._server.sockets[0].getsockname()[1]
        return self

    async def close(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            await _drain(reader)
            self.requests.append(time.monotonic())
            scenario = self.scenarios[min(len(self.requests), len(self.scenarios)) - 1]
            await asyncio.sleep(scenario.delay_s)
            if scenario.status == 200:
                await _stream(writer)
            else:
                await _fail(writer, scenario.status, scenario.body)
        finally:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()


async def _drain(reader: asyncio.StreamReader) -> None:
    head = await reader.readuntil(b"\r\n\r\n")
    length = 0
    for line in head.split(b"\r\n"):
        if line.lower().startswith(b"content-length:"):
            length = int(line.split(b":", 1)[1])
    await reader.readexactly(length)


async def _stream(writer: asyncio.StreamWriter) -> None:
    writer.write(
        b"HTTP/1.1 200 OK\r\ncontent-type: text/event-stream\r\ntransfer-encoding: chunked\r\n\r\n"
    )
    for event in (
        {"type": "message_start", "message": {"model": NATIVE, "usage": {"input_tokens": 5}}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "ok"}},
        {"type": "message_delta", "usage": {"output_tokens": 1}},
        {"type": "message_stop"},
    ):
        name = event["type"]
        payload = f"event: {name}\ndata: {json.dumps(event)}\n\n".encode()
        writer.write(f"{len(payload):x}\r\n".encode() + payload + b"\r\n")
        await writer.drain()
    writer.write(b"0\r\n\r\n")
    await writer.drain()


async def _fail(writer: asyncio.StreamWriter, status: int, body: bytes) -> None:
    writer.write(
        f"HTTP/1.1 {status} Too Many Requests\r\ncontent-type: application/json\r\n"
        f"content-length: {len(body)}\r\n\r\n".encode()
        + body
    )
    await writer.drain()


def registry_for(port: int) -> Registry:
    row = ModelRow(
        qmx_id=QmxId(ROW),
        provider=PROFILE,
        native=ModelId(NATIVE),
        window=1_000_000,
    )
    provider = Provider(
        name=PROFILE,
        kind="key",
        base_url=MappingProxyType({"local": f"http://127.0.0.1:{port}"}),
        models=(row,),
    )
    return Registry(MappingProxyType({PROFILE: provider}))


def profiles_for(port: int) -> Any:
    return parse_profiles(
        {
            PROFILE: {
                "base_url": f"http://127.0.0.1:{port}",
                "credential_ref": "qmx/fake",
                "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), NATIVE),
            }
        },
        allow_loopback_http=True,
    )


def prompt() -> bytes:
    return json.dumps(
        {
            "model": ROW,
            "max_tokens": 16,
            "messages": [{"role": "user", "content": "x" * PROMPT_CHARS}],
        }
    ).encode()


async def post(client: httpx.AsyncClient, base: str, bearer: str) -> httpx.Response:
    async with client.stream(
        "POST",
        f"{base}/v1/messages",
        content=prompt(),
        headers={"authorization": f"Bearer {bearer}", "content-type": "application/json"},
    ) as answer:
        await answer.aread()
        return httpx.Response(answer.status_code, headers=answer.headers, content=answer.content)


async def first_event(client: httpx.AsyncClient, base: str, bearer: str) -> tuple[float, bytes]:
    started = time.monotonic()
    async with client.stream(
        "POST",
        f"{base}/v1/messages",
        content=prompt(),
        headers={"authorization": f"Bearer {bearer}", "content-type": "application/json"},
    ) as answer:
        first = b""
        async for chunk in answer.aiter_bytes():
            first += chunk
            if first:
                break
        delay = time.monotonic() - started
        await answer.aread()
    return delay, first


async def main() -> int:
    fake = await FakeUpstream().start()
    fake.scenarios = [
        Scenario(DELAY_S, 200),
        Scenario(LATE_S, 200),
        Scenario(
            LATE_429_S,
            429,
            json.dumps(
                {"type": "error", "error": {"type": "rate_limit_error", "message": USAGE}}
            ).encode(),
        ),
    ]
    relay = await Relay(
        secrets=lambda _reference: "fake-key",
        journal=lambda _session: Journal(),
        alert=alert,
        profiles=lambda: profiles_for(fake.port),
        registry=lambda: registry_for(fake.port),
    ).start()
    handle = await relay.grant(SessionId("e43"), PROFILE)
    client = httpx.AsyncClient(timeout=httpx.Timeout(None))
    try:
        delay, first = await first_event(client, relay.base_url, handle.secret)
        log(f"case 400 s: first bytes after {delay:.0f} s, {len(fake.requests)} request(s)")
        verdict(
            delay >= DELAY_S - TOLERANCE_S,
            f"the first event waited {delay:.0f} s on the provider, nothing synthesised",
        )
        verdict(len(fake.requests) == 1, "the 400 s request was sent once, not resent")

        delay, first = await first_event(client, relay.base_url, handle.secret)
        log(f"case 900 s: stopped after {delay:.0f} s with {first[:120]!r}")
        verdict(
            abs(delay - BOUND_S) <= TOLERANCE_S,
            f"the relay stopped the 900 s prefill at its own {BOUND_S:.0f} s bound",
        )
        verdict(b"no message_start" in first, "the relay sent its own error event, not a resend")
        verdict(len(fake.requests) == 2, "the 900 s request was sent once, not resent")

        attempts = 0
        while attempts < CLI_RETRIES:
            attempts += 1
            answer = await post(client, relay.base_url, handle.secret)
            log(
                f"case 429: attempt {attempts} status={answer.status_code} "
                f"x-should-retry={answer.headers.get('x-should-retry')!r}"
            )
            if answer.headers.get("x-should-retry") == "false" or answer.status_code != 429:
                break
        verdict(attempts == 1, f"the late usage-limit 429 was retried {attempts - 1} times")
        verdict(len(fake.requests) == 3, "the 429 was sent once")
    finally:
        await client.aclose()
        await relay.close()
        await fake.close()
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
