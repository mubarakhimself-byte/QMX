"""A loopback Anthropic Messages server that replays a script and records every request.

Live checks point a key profile at it with `TestMode(loopback_http_provider=True)`, so a chat
makes real tool calls through the real CLI and relay without spending a plan turn or a provider
credit. Each request whose body offers tools takes the next scripted `Turn`; other requests,
such as the CLI's own side calls, get `SIDE_REPLY` unless `every_request` is set. When the
script runs out, every request gets `DONE`.

    fake = FakeModel([Turn([tool_use("Bash", {"command": "env"})]), Turn([text("done")])])
    fake.start()   # fake.url is http://127.0.0.1:<port>
    ...
    fake.stop()
    fake.requests  # every request's method, path, query, headers and raw body
"""

from __future__ import annotations

import itertools
import json
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Final

FAKE_KEY: Final = "qmx-hp7-fake-provider-key"
FAKE_REF: Final = "qmx/hp7-fake"
MODEL: Final = "fake-model"


def text(value: str) -> dict[str, Any]:
    return {"type": "text", "text": value}


def tool_use(name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    return {"type": "tool_use", "name": name, "input": tool_input}


@dataclass(frozen=True)
class Turn:
    blocks: list[dict[str, Any]]
    usage: dict[str, int] = field(
        default_factory=lambda: {"input_tokens": 100, "output_tokens": 10}
    )
    served: str | None = None
    """The `message.model` to report; None reports the requested model."""


SIDE_REPLY: Final = Turn([text("ok")], {"input_tokens": 1, "output_tokens": 1})
DONE: Final = Turn([text("done")], {"input_tokens": 1, "output_tokens": 1})


@dataclass(frozen=True)
class Seen:
    method: str
    path: str
    query: str
    headers: dict[str, str]
    body: bytes
    scripted: bool

    @property
    def json(self) -> dict[str, Any]:
        try:
            found = json.loads(self.body)
        except ValueError:
            return {}
        return found if isinstance(found, dict) else {}


def sse(turn: Turn, model: str, ids: itertools.count[int]) -> bytes:
    def event(kind: str, data: dict[str, Any]) -> bytes:
        return f"event: {kind}\ndata: {json.dumps({'type': kind, **data})}\n\n".encode()

    start_usage = {**turn.usage, "output_tokens": 1}
    out = [
        event(
            "message_start",
            {
                "message": {
                    "id": f"msg_fake{next(ids)}",
                    "type": "message",
                    "role": "assistant",
                    "model": turn.served or model,
                    "content": [],
                    "stop_reason": None,
                    "stop_sequence": None,
                    "usage": start_usage,
                }
            },
        )
    ]
    for index, block in enumerate(turn.blocks):
        if block["type"] == "tool_use":
            start = {"type": "tool_use", "id": f"toolu_fake{next(ids)}", "name": block["name"]}
            delta = {"type": "input_json_delta", "partial_json": json.dumps(block["input"])}
            out.append(
                event(
                    "content_block_start", {"index": index, "content_block": start | {"input": {}}}
                )
            )
        else:
            out.append(
                event(
                    "content_block_start",
                    {"index": index, "content_block": {"type": "text", "text": ""}},
                )
            )
            delta = {"type": "text_delta", "text": block["text"]}
        out.append(event("content_block_delta", {"index": index, "delta": delta}))
        out.append(event("content_block_stop", {"index": index}))
    stop = "tool_use" if any(b["type"] == "tool_use" for b in turn.blocks) else "end_turn"
    out.append(
        event(
            "message_delta",
            {
                "delta": {"stop_reason": stop, "stop_sequence": None},
                "usage": {"output_tokens": turn.usage.get("output_tokens", 1)},
            },
        )
    )
    out.append(event("message_stop", {}))
    return b"".join(out)


class FakeModel:
    def __init__(
        self,
        script: list[Turn],
        *,
        every_request: bool = False,
        routes: dict[str, list[Turn]] | None = None,
    ) -> None:
        self.script = list(script)
        self.every_request = every_request
        self.routes = {marker: list(turns) for marker, turns in (routes or {}).items()}
        """Separate scripts for conversations whose first message holds the marker, such as
        a native sub-agent's, so a parent that keeps running never takes their turns."""
        """Script every `/v1/messages` request, for checks that call the relay directly."""
        self.requests: list[Seen] = []
        self.served_usage: list[dict[str, int]] = []
        """The usage each answered POST reported, in order."""
        self.lock = threading.Lock()
        self.ids = itertools.count(1)
        self.server: ThreadingHTTPServer | None = None
        self.url = ""

    def next_turn(self, scripted: bool, request: dict[str, Any] | None = None) -> Turn:
        with self.lock:
            if not scripted:
                return SIDE_REPLY
            messages = (request or {}).get("messages") or [{}]
            first = json.dumps(messages[0])
            for marker, turns in self.routes.items():
                if marker in first:
                    return turns.pop(0) if turns else DONE
            return self.script.pop(0) if self.script else DONE

    def start(self) -> FakeModel:
        fake = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, format: str, *args: Any) -> None:
                return None

            def record(self, body: bytes, scripted: bool) -> None:
                path, _, query = self.path.partition("?")
                headers = {name.lower(): value for name, value in self.headers.items()}
                with fake.lock:
                    fake.requests.append(Seen(self.command, path, query, headers, body, scripted))

            def reply(self, status: int, content_type: str, data: bytes) -> None:
                self.send_response(status)
                self.send_header("content-type", content_type)
                self.send_header("content-length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_HEAD(self) -> None:
                self.record(b"", False)
                self.reply(200, "text/plain", b"")

            def do_POST(self) -> None:
                body = self.rfile.read(int(self.headers.get("content-length", "0")))
                request: dict[str, Any] = json.loads(body or b"{}")
                path = self.path.partition("?")[0]
                scripted = path == "/v1/messages" and (
                    fake.every_request or bool(request.get("tools"))
                )
                self.record(body, scripted)
                if path.endswith("/count_tokens"):
                    with fake.lock:
                        fake.served_usage.append({})
                    self.reply(200, "application/json", b'{"input_tokens": 10}')
                    return
                turn = fake.next_turn(scripted, request)
                with fake.lock:
                    fake.served_usage.append(dict(turn.usage))
                model = str(request.get("model") or MODEL)
                if request.get("stream"):
                    self.reply(200, "text/event-stream", sse(turn, model, fake.ids))
                    return
                message = {
                    "id": f"msg_fake{next(fake.ids)}",
                    "type": "message",
                    "role": "assistant",
                    "model": turn.served or model,
                    "content": [
                        b if b["type"] == "text" else b | {"id": f"toolu_fake{next(fake.ids)}"}
                        for b in turn.blocks
                    ],
                    "stop_reason": "end_turn",
                    "stop_sequence": None,
                    "usage": turn.usage,
                }
                self.reply(200, "application/json", json.dumps(message).encode())

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        return self

    def stop(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()

    def bodies(self) -> bytes:
        with self.lock:
            return b"\n".join(seen.body for seen in self.requests)

    def header_values(self) -> list[str]:
        with self.lock:
            return [value for seen in self.requests for value in seen.headers.values()]
