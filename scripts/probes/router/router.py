"""A loopback test router for the PRB-R probes only. Never a product router.

Every request is routed by its body's `model` field. A Claude id goes to `api.anthropic.com`
with the body and the raw header list unchanged: same order, same repeats, `accept-encoding`
kept. Only `host` is set to the upstream and the router's own `x-qmx-grant` is removed. A
third-party id goes to a local echo upstream, or to a keyed upstream whose key replaces the
incoming credential. Every method and path is recorded.

The router keeps the raw requests in memory only. Nothing it writes holds an `authorization`,
`x-api-key`, `cookie` or grant value: `public` replaces each with `<withheld>`, and
`compare_secret` says only `same` or `different` for two recorded requests.

`InterceptProxy` is the same recorder as an HTTPS proxy, for P0's run with no base URL. It
answers `CONNECT api.anthropic.com:443` with TLS from a probe-made certificate the CLI trusts
through `NODE_EXTRA_CA_CERTS`, then relays exactly as the router does. Other hosts are tunnelled
blind and only their names are recorded.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import select
import socket
import socketserver
import ssl
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from http.client import HTTPConnection, HTTPException, HTTPSConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Final
from urllib.parse import urlsplit

sys.path.append(str(Path(__file__).resolve().parents[2] / "live" / "qma"))
from fake_model import FakeModel, Turn, text, tool_use

ANTHROPIC_URL: Final = "https://api.anthropic.com"
ANTHROPIC_HOST: Final = "api.anthropic.com"
GRANT_HEADER: Final = "x-qmx-grant"
CREDENTIAL_HEADERS: Final = frozenset({"authorization", "x-api-key"})
SECRET_HEADERS: Final = CREDENTIAL_HEADERS | {"cookie", "proxy-authorization", GRANT_HEADER}
WITHHELD: Final = "<withheld>"
REPLY_FRAMING: Final = frozenset(
    {"transfer-encoding", "content-length", "connection", "keep-alive"}
)
UPSTREAM_TIMEOUT_S: Final = 600.0

_VAULT_KEY: Final = secrets.token_bytes(32)
"""Per-process key for comparing secret values as digests; never written anywhere."""


@dataclass(frozen=True)
class Upstream:
    name: str
    url: str
    key: Callable[[], str] | None = None
    """When set, this key is sent as a bearer in place of the incoming credential."""
    third_party: bool = False
    """Drop the incoming `authorization` and `x-api-key`, so no Claude credential leaves."""


Route = Callable[[str | None], Upstream | None]


@dataclass
class Exchange:
    """One request as the router received it, plus its timings. In memory only."""

    run: str
    lane: str
    method: str
    path: str
    headers: list[tuple[str, str]]
    body: bytes
    received_at: float
    status: int = 0
    connect_ms: float = 0.0
    forwarded_at: float = 0.0
    first_byte_at: float = 0.0
    first_byte_out_at: float = 0.0
    done_at: float = 0.0
    error: str = ""

    @property
    def json(self) -> dict[str, Any]:
        try:
            found = json.loads(self.body)
        except ValueError:
            return {}
        return found if isinstance(found, dict) else {}

    @property
    def model(self) -> str | None:
        found = self.json.get("model")
        return found if isinstance(found, str) else None

    def header(self, name: str) -> str | None:
        return next((v for n, v in self.headers if n.lower() == name), None)

    def digest(self, name: str) -> bytes | None:
        value = self.header(name)
        if value is None:
            return None
        return hmac.new(_VAULT_KEY, value.encode(), hashlib.sha256).digest()

    def overhead_ms(self) -> float:
        """Time the router itself added: request read to upstream send, minus the upstream
        connect, plus upstream first byte to the client's first byte."""
        before = (self.forwarded_at - self.received_at) * 1000 - self.connect_ms
        after = (self.first_byte_out_at - self.first_byte_at) * 1000 if self.first_byte_at else 0.0
        return max(before, 0.0) + max(after, 0.0)


def public_headers(headers: list[tuple[str, str]]) -> list[list[str]]:
    return [[n, WITHHELD if n.lower() in SECRET_HEADERS else v] for n, v in headers]


def public(exchange: Exchange, *, keep_body: bool = False) -> dict[str, Any]:
    """`exchange` as a dict safe to write: secret header values withheld."""
    body = exchange.json
    found: dict[str, Any] = {
        "run": exchange.run,
        "lane": exchange.lane,
        "method": exchange.method,
        "path": exchange.path,
        "model": exchange.model,
        "status": exchange.status,
        "error": exchange.error,
        "headers": public_headers(exchange.headers),
        "body_sha256": hashlib.sha256(exchange.body).hexdigest(),
        "body_bytes": len(exchange.body),
        "body_fields": list(body),
        "upstream_ms": round((exchange.done_at - exchange.forwarded_at) * 1000, 1)
        if exchange.done_at
        else None,
        "overhead_ms": round(exchange.overhead_ms(), 2),
    }
    if keep_body:
        found["body"] = body or exchange.body.decode("utf-8", "replace")
    return found


def compare_secret(a: Exchange, b: Exchange, name: str) -> str:
    """`same`, `different`, or which side lacks the header. Values never leave memory."""
    da, db = a.digest(name), b.digest(name)
    if da is None or db is None:
        return f"absent in {'both' if da is db else ('first' if da is None else 'second')}"
    return "same" if hmac.compare_digest(da, db) else "different"


def raw_request(exchange: Exchange) -> bytes:
    """The request as it arrived, with secret header values withheld."""
    lines = [f"{exchange.method} {exchange.path} HTTP/1.1"]
    lines += [f"{n}: {v}" for n, v in public_headers(exchange.headers)]
    return ("\r\n".join(lines) + "\r\n\r\n").encode() + exchange.body


class Recorder:
    """Shared state of a router or proxy: the exchanges and the run label."""

    def __init__(self) -> None:
        self.exchanges: list[Exchange] = []
        self.tunnels: list[str] = []
        self.run = ""
        self.lock = threading.Lock()

    def add(self, exchange: Exchange) -> None:
        with self.lock:
            self.exchanges.append(exchange)

    def of(self, run: str) -> list[Exchange]:
        with self.lock:
            return [e for e in self.exchanges if e.run == run]

    def write(self, path: Path, *, keep_body: Callable[[Exchange], bool] = lambda _: False) -> None:
        with self.lock:
            rows = [public(e, keep_body=keep_body(e)) for e in self.exchanges]
            tunnels = list(self.tunnels)
        path.write_text(json.dumps({"requests": rows, "tunnels": tunnels}, indent=1), "utf-8")


def _read_body(handler: BaseHTTPRequestHandler) -> tuple[bytes, bytes]:
    """`(decoded body, bytes as framed on the wire)`. Chunked bodies are forwarded framed."""
    if "chunked" not in handler.headers.get("transfer-encoding", "").lower():
        length = int(handler.headers.get("content-length", "0") or 0)
        body = handler.rfile.read(length) if length else b""
        return body, body
    decoded, framed = bytearray(), bytearray()
    while size_line := handler.rfile.readline():
        framed += size_line
        size = int(size_line.split(b";")[0].strip() or b"0", 16)
        if size == 0:
            while line := handler.rfile.readline():
                framed += line
                if line in (b"\r\n", b"\n"):
                    break
            break
        chunk = handler.rfile.read(size + 2)
        framed += chunk
        decoded += chunk[:size]
    return bytes(decoded), bytes(framed)


class _Relay(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    recorder: Recorder
    route: Route
    lane_override: Upstream | None = None

    def log_message(self, format: str, *args: Any) -> None:
        return None

    def do_GET(self) -> None:
        self.relay()

    do_POST = do_PUT = do_PATCH = do_DELETE = do_HEAD = do_OPTIONS = do_GET

    def relay(self) -> None:
        received = time.perf_counter()
        headers = list(self.headers.items())
        body, framed = _read_body(self)
        exchange = Exchange(self.recorder.run, "", self.command, self.path, headers, body, received)
        upstream = self.lane_override or self.route(exchange.model)
        exchange.lane = upstream.name if upstream else "refused"
        self.recorder.add(exchange)
        if upstream is None:
            exchange.status = 400
            self.refuse(400, f"probe router: no route for model {exchange.model!r}")
            exchange.done_at = time.perf_counter()
            return
        try:
            self.forward(exchange, upstream, framed)
        except (OSError, HTTPException) as exc:
            exchange.error = type(exc).__name__
            if exchange.status:
                self.close_connection = True
                return
            exchange.status = 502
            self.refuse(502, f"probe router: upstream {upstream.name} failed: {exchange.error}")
        exchange.done_at = exchange.done_at or time.perf_counter()

    def refuse(self, status: int, message: str) -> None:
        data = json.dumps(
            {"type": "error", "error": {"type": "api_error", "message": message}}
        ).encode()
        self.send_response_only(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        self.wfile.flush()

    def forward(self, exchange: Exchange, upstream: Upstream, framed: bytes) -> None:
        target = urlsplit(upstream.url)
        host = target.hostname or ""
        if target.scheme == "https":
            conn: HTTPConnection = HTTPSConnection(
                host,
                target.port or 443,
                timeout=UPSTREAM_TIMEOUT_S,
                context=ssl.create_default_context(),
            )
        else:
            conn = HTTPConnection(host, target.port or 80, timeout=UPSTREAM_TIMEOUT_S)
        started = time.perf_counter()
        conn.connect()
        exchange.connect_ms = (time.perf_counter() - started) * 1000
        conn.putrequest(
            self.command,
            target.path.rstrip("/") + self.path,
            skip_host=True,
            skip_accept_encoding=True,
        )
        for name, value in exchange.headers:
            low = name.lower()
            if low == GRANT_HEADER or (upstream.third_party and low in CREDENTIAL_HEADERS):
                continue
            conn.putheader(name, target.netloc if low == "host" else value)
        if upstream.key is not None:
            conn.putheader("authorization", f"Bearer {upstream.key()}")
        conn.endheaders(framed or None)
        exchange.forwarded_at = time.perf_counter()
        reply = conn.getresponse()
        exchange.status = reply.status
        self.send_response_only(reply.status, reply.reason)
        for name, value in reply.getheaders():
            if name.lower() not in REPLY_FRAMING:
                self.send_header(name, value)
        bodiless = self.command == "HEAD" or reply.status in (204, 304)
        if bodiless:
            self.send_header("content-length", "0")
            self.end_headers()
        else:
            self.send_header("transfer-encoding", "chunked")
            self.end_headers()
            while chunk := reply.read1(65536):
                if not exchange.first_byte_at:
                    exchange.first_byte_at = time.perf_counter()
                self.wfile.write(f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n")
                self.wfile.flush()
                if not exchange.first_byte_out_at:
                    exchange.first_byte_out_at = time.perf_counter()
            self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()
        exchange.done_at = time.perf_counter()
        conn.close()


class _Server(ThreadingHTTPServer):
    daemon_threads = True


class Router:
    """The loopback router. `url` is its base URL once started."""

    def __init__(self, route: Route) -> None:
        self.recorder = Recorder()
        handler = type(
            "Handler", (_Relay,), {"recorder": self.recorder, "route": staticmethod(route)}
        )
        self.server = _Server(("127.0.0.1", 0), handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> Router:
        self.thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.server.shutdown()
        self.server.server_close()


class _Intercept(_Relay):
    tls: ssl.SSLContext

    def do_CONNECT(self) -> None:
        host, _, port = self.path.partition(":")
        with self.recorder.lock:
            self.recorder.tunnels.append(self.path)
        if host != ANTHROPIC_HOST:
            self.tunnel(host, int(port or 443))
            return
        self.send_response_only(200, "Connection Established")
        self.end_headers()
        self.wfile.flush()
        inner = self.tls.wrap_socket(self.connection, server_side=True)
        self.connection = inner
        self.rfile = inner.makefile("rb")
        self.wfile = socketserver._SocketWriter(inner)  # type: ignore[attr-defined]
        self.lane_override = Upstream("anthropic", ANTHROPIC_URL)
        self.close_connection = False
        while not self.close_connection:
            self.handle_one_request()

    def tunnel(self, host: str, port: int) -> None:
        try:
            far = socket.create_connection((host, port), timeout=30)
        except OSError:
            self.send_error(502)
            return
        self.send_response_only(200, "Connection Established")
        self.end_headers()
        self.wfile.flush()
        ends = [self.connection, far]
        try:
            while True:
                ready, _, _ = select.select(ends, [], [], 60)
                if not ready:
                    return
                for end in ready:
                    data = end.recv(65536)
                    if not data:
                        return
                    (far if end is self.connection else self.connection).sendall(data)
        finally:
            far.close()
            self.close_connection = True


class InterceptProxy:
    """An HTTPS proxy that records `api.anthropic.com` requests and relays them unchanged."""

    def __init__(self, cert: Path, key: Path) -> None:
        self.recorder = Recorder()
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.load_cert_chain(cert, key)
        tls.set_alpn_protocols(["http/1.1"])
        fields = {"recorder": self.recorder, "route": staticmethod(lambda _: None), "tls": tls}
        self.server = _Server(("127.0.0.1", 0), type("Handler", (_Intercept,), fields))
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> InterceptProxy:
        self.thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.server.shutdown()
        self.server.server_close()


HANDBACK_TOOL: Final = "SubagentHandback"
"""CLI 2.1.299 ends a sub-agent's run only when it calls this tool with its report."""


class Echo(FakeModel):
    """A third-party upstream that answers every request with `reply`. When the CLI offers
    `SubagentHandback`, it delivers `reply` through that tool, as a sub-agent must."""

    def __init__(self, reply: str) -> None:
        super().__init__([])
        self.reply = reply

    def next_turn(self, scripted: bool, request: dict[str, Any] | None = None) -> Turn:
        offered = {t.get("name") for t in (request or {}).get("tools", []) if isinstance(t, dict)}
        if HANDBACK_TOOL in offered:
            return Turn([tool_use(HANDBACK_TOOL, {"message": self.reply})])
        return Turn([text(self.reply)])

    def upstream(self, name: str) -> Upstream:
        return Upstream(name, self.url, third_party=True)


def is_claude(model: str | None) -> bool:
    """A Claude id or tier alias, or no model at all (a GET or HEAD the CLI sends)."""
    return model is None or model.startswith("claude") or model in {"haiku", "sonnet", "opus"}
