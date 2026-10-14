"""02a trap 7 on a canary. `p_echo.py` writes hp1-echo.log.

A loopback echo server stands in for a third-party host. The CLI runs from a throwaway
home whose login file holds only the canary, never the plan login. Run 1 sets a fake
provider key with the base URL. Run 2 sets the base URL alone. Run 3 sets the base URL
alone with the canary as `CLAUDE_CODE_OAUTH_TOKEN`, the long-lived plan token form, which
makes model requests without a profile check.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import threading
import time
from collections.abc import Generator, Iterable
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Final, Literal

from common import (
    HP1_EVIDENCE,
    SCRATCH,
    Lockdown,
    Log,
    Provider,
    describe,
    plan_options,
    provider_env,
    scrub_process_env,
)

CANARY: Final = "sk-ant-oat01-QMXCANARY"
FAKE_KEY: Final = "qmx-hp1-fake-provider-key"
ECHO_HOME: Final = SCRATCH / "hp1" / "echo" / "claude"
AUTH_HEADERS: Final = frozenset({"authorization", "x-api-key"})

Seen = Literal["fake-key", "canary", "other"]


def classify(value: str) -> Seen:
    if CANARY in value:
        return "canary"
    return "fake-key" if FAKE_KEY in value else "other"


@dataclass(frozen=True)
class Request:
    method: str
    path: str
    auth: dict[str, Seen]
    canary_anywhere: bool


@dataclass(frozen=True)
class ToolCall:
    name: str
    input: dict[str, Any]


@dataclass
class Echo:
    requests: list[Request] = field(default_factory=list[Request])
    script: list[ToolCall] = field(default_factory=list[ToolCall])
    bodies: list[bytes] = field(default_factory=list[bytes])
    lock: threading.Lock = field(default_factory=threading.Lock)

    def record(self, request: Request, body: bytes) -> None:
        with self.lock:
            self.requests.append(request)
            self.bodies.append(body)

    def next_call(self, offers_tools: bool) -> ToolCall | None:
        with self.lock:
            return self.script.pop(0) if offers_tools and self.script else None


def tool_use_events(call: ToolCall) -> list[dict[str, Any]]:
    start: dict[str, Any] = {
        "type": "tool_use",
        "id": f"toolu_hp1_{call.name}",
        "name": call.name,
        "input": {},
    }
    delta = {"type": "input_json_delta", "partial_json": json.dumps(call.input)}
    return [
        {"type": "content_block_start", "index": 0, "content_block": start},
        {"type": "content_block_delta", "index": 0, "delta": delta},
        {"type": "content_block_stop", "index": 0},
        {
            "type": "message_delta",
            "delta": {"stop_reason": "tool_use", "stop_sequence": None},
            "usage": {"output_tokens": 1},
        },
    ]


def text_events() -> list[dict[str, Any]]:
    return [
        {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "ok"}},
        {"type": "content_block_stop", "index": 0},
        {
            "type": "message_delta",
            "delta": {"stop_reason": "end_turn", "stop_sequence": None},
            "usage": {"output_tokens": 1},
        },
    ]


def sse_reply(model: str, call: ToolCall | None = None) -> bytes:
    events: list[dict[str, Any]] = [
        {
            "type": "message_start",
            "message": {
                "id": "msg_hp1echo",
                "type": "message",
                "role": "assistant",
                "model": model,
                "content": [],
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        },
        *(tool_use_events(call) if call else text_events()),
        {"type": "message_stop"},
    ]
    return b"".join(
        f"event: {event['type']}\ndata: {json.dumps(event)}\n\n".encode() for event in events
    )


def json_reply(model: str) -> bytes:
    message = {
        "id": "msg_hp1echo",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": [{"type": "text", "text": "ok"}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 1, "output_tokens": 1},
    }
    return json.dumps(message).encode()


def handler(echo: Echo) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            pass

        def _record(self) -> bytes:
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else b""
            headers = "\n".join(f"{k}: {v}" for k, v in self.headers.items())
            echo.record(
                Request(
                    method=self.command,
                    path=self.path,
                    auth={
                        name.lower(): classify(value)
                        for name, value in self.headers.items()
                        if name.lower() in AUTH_HEADERS
                    },
                    canary_anywhere=CANARY in headers or CANARY.encode() in body,
                ),
                body,
            )
            return body

        def _send(self, status: int, content_type: str, payload: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:
            self._record()
            self._send(200, "application/json", b"{}")

        def do_HEAD(self) -> None:
            self._record()
            self._send(200, "application/json", b"")

        def do_POST(self) -> None:
            body = self._record()
            try:
                request: dict[str, Any] = json.loads(body or b"{}")
            except json.JSONDecodeError:
                request = {}
            model = str(request.get("model", "echo"))
            if self.path.split("?")[0].endswith("/count_tokens"):
                self._send(200, "application/json", b'{"input_tokens": 1}')
            elif request.get("stream"):
                call = echo.next_call(bool(request.get("tools")))
                self._send(200, "text/event-stream", sse_reply(model, call))
            else:
                self._send(200, "application/json", json_reply(model))

    return Handler


@contextmanager
def serve(script: Iterable[ToolCall] = ()) -> Generator[tuple[str, Echo]]:
    echo = Echo(script=list(script))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler(echo))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", echo
    finally:
        server.shutdown()
        server.server_close()


def canary_home(root: Path) -> Path:
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    login = {
        "claudeAiOauth": {
            "accessToken": CANARY,
            "refreshToken": "sk-ant-ort01-QMXCANARY",
            "expiresAt": int((time.time() + 365 * 86400) * 1000),
            "scopes": ["user:inference", "user:profile"],
            "subscriptionType": "max",
        }
    }
    (root / ".credentials.json").write_text(json.dumps(login), encoding="utf-8")
    return root


def with_token_verdict(requests: list[Request]) -> str:
    seen = {kind for r in requests for kind in r.auth.values()}
    leaked = any(r.canary_anywhere for r in requests)
    return "PASS" if requests and seen == {"fake-key"} and not leaked else "FAIL"


def without_token_verdict(requests: list[Request]) -> str:
    if any(r.canary_anywhere for r in requests):
        return "LEAK"
    model_requests = [r for r in requests if r.path.split("?")[0].endswith("/v1/messages")]
    return "NO LEAK" if model_requests else "NO MODEL REQUEST"


async def one_turn(log: Log, env: dict[str, str]) -> None:
    from claude_agent_sdk import ClaudeSDKClient  # noqa: PLC0415

    options = plan_options(Lockdown(), env=env, model="sonnet", max_turns=1)
    async with ClaudeSDKClient(options=options) as client:
        await client.query("say ok")
        async for message in client.receive_response():
            log(describe(message))


async def run(log: Log, label: str, env: dict[str, str], echo: Echo) -> list[Request]:
    before = len(echo.requests)
    log(f"--- {label}: env names {sorted(env)}")
    try:
        await asyncio.wait_for(one_turn(log, env), timeout=180)
    except (TimeoutError, OSError, RuntimeError) as error:
        log(f"{label} turn ended with {type(error).__name__}: {str(error)[:300]}")
    requests = echo.requests[before:]
    for r in requests:
        log(f"{label} received {r.method} {r.path} auth={r.auth} canary={r.canary_anywhere}")
    return requests


async def main_async(log: Log) -> int:
    log(f"scrubbed from this process: {scrub_process_env(os.environ)}")
    with serve() as (url, echo):
        provider = Provider("echo", url, "echo-model")
        env = provider_env(os.environ, provider, FAKE_KEY, canary_home(ECHO_HOME))
        with_token = await run(log, "with token", env, echo)
        log.row(
            "trap 7 with token: echo saw only the fake key",
            len(with_token),
            with_token_verdict(with_token),
        )

        bare = {
            k: v for k, v in env.items() if k not in ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY")
        }
        env = bare | {"CLAUDE_CONFIG_DIR": str(canary_home(ECHO_HOME))}
        without = await run(log, "without token", env, echo)
        log.row(
            "trap 7 base URL without a token: canary at the base URL",
            [f"{r.method} {r.path}" for r in without],
            without_token_verdict(without),
        )

        env = bare | {
            "CLAUDE_CONFIG_DIR": str(canary_home(ECHO_HOME)),
            "CLAUDE_CODE_OAUTH_TOKEN": CANARY,
        }
        as_env = await run(log, "without token, canary as CLAUDE_CODE_OAUTH_TOKEN", env, echo)
        log.row(
            "trap 7 base URL without a token, login as CLAUDE_CODE_OAUTH_TOKEN",
            [f"{r.method} {r.path}" for r in as_env],
            without_token_verdict(as_env),
        )
    return 0


def main() -> int:
    return asyncio.run(main_async(Log("hp1-echo", HP1_EVIDENCE)))


if __name__ == "__main__":
    raise SystemExit(main())
