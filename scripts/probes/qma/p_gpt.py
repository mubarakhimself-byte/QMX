"""Probe GPT on the ChatGPT plan through Sign in with ChatGPT (HARNESS-PLAN HP2, 02b section D).

A throwaway client registered as "QMA" runs probes P0 to P5 in order and stops at the first
failure, except P4. The refresh token lives in the OS keyring under `qmx/chatgpt`. Access
tokens live in this process only. No log line, file or stdout line carries a token.

    run      P0 sign-in (the operator approves "QMA" in the browser), P1 to P5, the P2 perf
             series, then the secrets scan. `--reuse` skips P0 and refreshes the stored token.
    refresh  Force one refresh, check the rotated refresh token is stored, then scan.
    scan     Search the evidence folder and FINDINGS.md for the current token values.

Needs `keyring`, which the qmx-agents environment has:
    uv run --project qmx-agents --no-sync python scripts/probes/qma/p_gpt.py run
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib
import itertools
import json
import secrets
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Literal, Protocol, cast

AUTHORIZE_URL = "https://auth.openai.com/api/accounts/authorize"
TOKEN_URL = "https://auth.openai.com/api/accounts/oauth/token"  # noqa: S105
ISSUER = "https://auth.openai.com"
API = "https://api.openai.com/v1"
RESOURCE = API
SCOPES = "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct"
DIRECT_SCOPE = "chatgpt.tokens.use.direct"
AGENT_NAME = "QMA"
REGISTRATION_CLIENT = "dynamic_agent_client"
KEYRING_SERVICE = "qmx/chatgpt"
KEYRING_USER = "chatgpt"
CALLBACK_PATH = "/auth/callback"
CALLBACK_PORTS = (1455, 1456, 1457, 1458)
NAMESPACE = "qma"
USER_AGENT = "QMA-probe/0.1"
NOT_ELIGIBLE = "subscription_sharing_user_not_eligible"
REFRESH_MARGIN_S = 300
MAX_REFRESH_WAIT_S = 1800
PERF_LIMIT_S = 10.0
DEFAULT_EVIDENCE = Path("D:/QMX-worktrees/qma-ship/evidence/hp2")
FINDINGS = Path(__file__).with_name("FINDINGS.md")

Json = dict[str, Any]
ToolsShape = Literal["namespace", "plain"]


def responses_body(
    request: Mapping[str, Any],
    *,
    tools_shape: ToolsShape = "namespace",
    include_reasoning: bool = False,
) -> Json:
    """Build a `/v1/responses` body from an Anthropic Messages request.

    The body is built from scratch, so a field the route bars (`max_tokens`, `temperature`,
    `metadata` and the rest) can never ride along from the Anthropic side.
    """
    body: Json = {
        "model": request["model"],
        "input": [item for message in request["messages"] for item in _input_items(message)],
        "store": False,
        "stream": True,
    }
    instructions = _system_text(request.get("system"))
    if instructions:
        body["instructions"] = instructions
    tools = request.get("tools")
    if tools:
        body["tools"] = _tools(tools, tools_shape)
    if include_reasoning:
        body["include"] = ["reasoning.encrypted_content"]
    return body


def _system_text(system: object) -> str:
    if isinstance(system, str):
        return system
    if isinstance(system, list):
        blocks = cast("list[Json]", system)
        return "\n\n".join(block["text"] for block in blocks if block.get("type") == "text")
    return ""


def _input_items(message: Mapping[str, Any]) -> list[Json]:
    role = message["role"]
    content = message["content"]
    if isinstance(content, str):
        return [{"role": role, "content": content}]
    items: list[Json] = []
    text: list[str] = []

    def flush() -> None:
        if text:
            items.append({"role": role, "content": "\n\n".join(text)})
            text.clear()

    for block in content:
        match block["type"]:
            case "text":
                text.append(block["text"])
            case "tool_use":
                flush()
                items.append(
                    {
                        "type": "function_call",
                        "call_id": block["id"],
                        "name": block["name"],
                        "arguments": json.dumps(block["input"]),
                    }
                )
            case "tool_result":
                flush()
                items.append(
                    {
                        "type": "function_call_output",
                        "call_id": block["tool_use_id"],
                        "output": _system_text(block["content"]),
                    }
                )
            case other:
                raise ValueError(f"content block {other!r} has no Responses mapping in this probe")
    flush()
    return items


def _tools(tools: Sequence[Mapping[str, Any]], shape: ToolsShape) -> list[Json]:
    functions: list[Json] = [
        {
            "type": "function",
            "name": tool["name"],
            "description": tool.get("description", ""),
            "parameters": tool["input_schema"],
        }
        for tool in tools
    ]
    if shape == "plain":
        return functions
    return [
        {"type": "namespace", "name": NAMESPACE, "description": "QMA tools", "tools": functions}
    ]


def replay_items(output: Sequence[Mapping[str, Any]], *, keep_reasoning: bool) -> list[Json]:
    """Turn-one output items to send back in turn two. `store` is false, so nothing is
    referenced by id. Reasoning items go back only when they carry `encrypted_content`."""
    replay: list[Json] = []
    for item in output:
        kind = item.get("type")
        if kind == "function_call" or (
            kind == "reasoning" and keep_reasoning and item.get("encrypted_content")
        ):
            replay.append({k: v for k, v in item.items() if k not in {"id", "status"}})
    return replay


@dataclass(frozen=True)
class StreamResult:
    status: int
    request_id: str | None
    first_byte_s: float | None
    event_types: tuple[str, ...]
    terminal: str | None
    output: tuple[Json, ...]
    text: str
    error_code: str | None
    error_param: str | None
    error_message: str | None

    @property
    def completed(self) -> bool:
        return self.terminal == "response.completed"

    def function_calls(self) -> list[Json]:
        return [item for item in self.output if item.get("type") == "function_call"]

    def lines(self) -> list[str]:
        return [
            f"http_status: {self.status}",
            f"request_id: {self.request_id}",
            f"first_byte_s: {self.first_byte_s}",
            f"terminal: {self.terminal}",
            f"error: code={self.error_code} param={self.error_param} msg={self.error_message}",
            f"event_types: {' '.join(dict.fromkeys(self.event_types))}",
            f"output_item_types: {[item.get('type') for item in self.output]}",
            f"text: {self.text[:400]!r}",
        ]


def parse_sse(lines: Iterable[str]) -> Iterator[Json]:
    data: list[str] = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if line.startswith("data:"):
            data.append(line[5:].strip())
        elif not line and data:
            payload = "\n".join(data)
            data.clear()
            if payload != "[DONE]":
                yield json.loads(payload)
    if data and data[0] != "[DONE]":
        yield json.loads("\n".join(data))


def fold_events(
    status: int, request_id: str | None, first_byte_s: float | None, events: Iterable[Json]
) -> StreamResult:
    types: list[str] = []
    text: list[str] = []
    terminal: str | None = None
    output: tuple[Json, ...] = ()
    error: Json = {}
    for event in events:
        kind = str(event.get("type"))
        types.append(kind)
        if kind == "response.output_text.delta":
            text.append(event.get("delta", ""))
        elif kind in {"response.completed", "response.failed", "response.incomplete"}:
            terminal = kind
            response: Json = event.get("response") or {}
            output = tuple(response.get("output") or ())
            error = response.get("error") or error
        elif kind == "error":
            error = event.get("error") or event
    return StreamResult(
        status=status,
        request_id=request_id,
        first_byte_s=first_byte_s,
        event_types=tuple(types),
        terminal=terminal,
        output=output,
        text="".join(text),
        error_code=error.get("code"),
        error_param=error.get("param"),
        error_message=error.get("message"),
    )


def error_result(status: int, request_id: str | None, raw: bytes) -> StreamResult:
    try:
        payload: Any = json.loads(raw)
    except ValueError:
        payload = {"detail": raw[:300].decode(errors="replace")}
    if not isinstance(payload, dict):
        payload = {"detail": payload}
    body = cast("Json", payload)
    error: Json = body["error"] if isinstance(body.get("error"), dict) else {}
    if not error:
        error = {"message": str(body.get("detail", body))[:300]}
    return StreamResult(
        status=status,
        request_id=request_id,
        first_byte_s=None,
        event_types=(),
        terminal=None,
        output=(),
        text="",
        error_code=error.get("code"),
        error_param=error.get("param"),
        error_message=error.get("message"),
    )


def model_slugs(payload: Mapping[str, Any]) -> list[str]:
    """`/v1/models` on this route returns `models` with `slug` and `visibility`."""
    models: list[Json] | None = payload.get("models")
    if models is not None:
        return [m["slug"] for m in models if m.get("visibility", "list") == "list"]
    data: list[Json] = payload.get("data", [])
    return [m["id"] for m in data]


def jwt_claims(token: str) -> Json:
    """Decode a JWT payload without verifying it. The probe checks iss, aud and nonce only;
    signature checks against OpenAI's JWKS belong to the real `qma.gpt.siwc` (HP16)."""
    payload = token.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def authorize_url(
    *, client_id: str, host_id: str, redirect_uri: str, state: str, nonce: str, challenge: str
) -> str:
    params = {
        "client_id": client_id,
        "ext_agent_host_id": host_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
        "resource": RESOURCE,
        "state": state,
        "nonce": nonce,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
    }
    if client_id == REGISTRATION_CLIENT:
        params["agent_name_hint"] = AGENT_NAME
    return f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"


@dataclass(frozen=True)
class Callback:
    code: str
    client_id: str | None
    scope: str | None


class SignInError(RuntimeError):
    pass


def parse_callback(query: Mapping[str, str], expected_state: str) -> Callback:
    if not secrets.compare_digest(query.get("state", ""), expected_state):
        raise SignInError("callback state does not match this attempt")
    if "error" in query:
        raise SignInError(f"authorization refused: {query['error']}")
    if "code" not in query:
        raise SignInError("callback carried no code")
    return Callback(query["code"], query.get("client_id"), query.get("scope"))


class _CallbackServer(HTTPServer):
    """HTTPServer's SO_REUSEADDR lets a second listener bind a busy port on Windows, which
    splits callbacks between them; a busy port must move this probe to the next one."""

    allow_reuse_address = False
    query: dict[str, str] | None = None


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        url = urllib.parse.urlsplit(self.path)
        if url.path != CALLBACK_PATH:
            self.send_error(404)
            return
        cast("_CallbackServer", self.server).query = dict(urllib.parse.parse_qsl(url.query))
        page = b"<html><body>QMA sign-in received. You can close this tab.</body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def log_message(self, format: str, *args: object) -> None:
        return


def open_callback_server(ports: Sequence[int] = CALLBACK_PORTS) -> _CallbackServer:
    for port in ports:
        try:
            return _CallbackServer(("127.0.0.1", port), _CallbackHandler)
        except OSError:
            continue
    raise SignInError(f"no free loopback port among {list(ports)}")


def wait_for_callback(server: _CallbackServer, timeout_s: float) -> dict[str, str]:
    deadline = time.monotonic() + timeout_s
    server.timeout = 1.0
    while server.query is None:
        if time.monotonic() > deadline:
            raise SignInError(f"no callback within {timeout_s:.0f} s")
        server.handle_request()
    return server.query


@dataclass
class Registration:
    client_id: str
    host_id: str
    refresh_token: str
    scopes: tuple[str, ...]
    earliest_refresh_at: float | None = None

    def dumps(self) -> str:
        return json.dumps(self.__dict__ | {"scopes": list(self.scopes)})

    @classmethod
    def loads(cls, raw: str) -> Registration:
        data = json.loads(raw)
        return cls(**data | {"scopes": tuple(data["scopes"])})


class Vault(Protocol):
    def get(self) -> str | None: ...
    def set(self, value: str) -> None: ...


class KeyringVault:
    def get(self) -> str | None:
        keyring: Any = importlib.import_module("keyring")
        return keyring.get_password(KEYRING_SERVICE, KEYRING_USER)

    def set(self, value: str) -> None:
        keyring: Any = importlib.import_module("keyring")
        keyring.set_password(KEYRING_SERVICE, KEYRING_USER, value)


def epoch_seconds(value: object) -> float | None:
    """`earliest_refresh_at` has no documented format; accept Unix seconds or ISO 8601."""
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str) and value:
        try:
            return float(value)
        except ValueError:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    return None


@dataclass(frozen=True)
class HttpReply:
    status: int
    body: bytes
    request_id: str | None


def _send(request: urllib.request.Request, timeout_s: float = 60) -> HttpReply:
    request.add_header("User-Agent", USER_AGENT)
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:  # noqa: S310
            return HttpReply(response.status, response.read(), response.headers.get("x-request-id"))
    except urllib.error.HTTPError as err:
        return HttpReply(err.code, err.read(), err.headers.get("x-request-id"))


def post_form(url: str, form: Mapping[str, str]) -> HttpReply:
    data = urllib.parse.urlencode(form).encode()
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")  # noqa: S310
    return _send(request)


TOKEN_ERRORS = {
    "invalid_request": "request bug: a parameter is missing or the body is not form-encoded",
    "invalid_client": "request bug: this client_id cannot use the token endpoint",
    "unsupported_grant_type": "request bug: grant_type is wrong",
    "invalid_grant": (
        "the code, verifier, redirect_uri or client_id was rejected, or the code was used or"
        " expired. OpenAI's sign-in docs say to discard the code and reauthorize with the"
        " issued client_id. Per those docs an ineligible plan shows instead as a missing"
        f" {DIRECT_SCOPE} scope or a 403 {NOT_ELIGIBLE} at inference"
    ),
}
"""Meanings of the token endpoint's `error` codes. Its error bodies carry only `error`, no
`error_description` (measured 2026-10-14). An unknown client_id also returns invalid_grant."""


def _token_error_body(reply: HttpReply) -> Json | None:
    try:
        payload: Any = json.loads(reply.body)
    except ValueError:
        return None
    return cast("Json", payload) if isinstance(payload, dict) else None


def token_error_code(reply: HttpReply) -> str | None:
    body = _token_error_body(reply)
    return None if body is None else str(body.get("error"))


def token_error(reply: HttpReply) -> str:
    body = _token_error_body(reply)
    if body is None:
        return f"http {reply.status} request_id={reply.request_id}: body is not a JSON object"
    code = str(body.get("error"))
    text = f"http {reply.status} {code} request_id={reply.request_id}: "
    text += TOKEN_ERRORS.get(code, "not in the documented set")
    for key in ("error_description", "error_uri"):
        if body.get(key):
            text += f"; {key}={str(body[key])[:300]}"
    return text


@dataclass
class Session:
    registration: Registration
    vault: Vault
    secrets_seen: set[str] = field(default_factory=set[str])
    _access: str | None = None
    _expires_at: float = 0.0

    def __post_init__(self) -> None:
        self.secrets_seen.add(self.registration.refresh_token)

    def accept(self, tokens: Mapping[str, Any]) -> None:
        self._access = tokens["access_token"]
        self._expires_at = time.time() + float(tokens.get("expires_in", 3600))
        self.secrets_seen.add(tokens["access_token"])
        if "refresh_token" in tokens:
            self.registration.refresh_token = tokens["refresh_token"]
            self.secrets_seen.add(tokens["refresh_token"])
        if "scope" in tokens:
            self.registration.scopes = tuple(sorted(str(tokens["scope"]).split()))
        self.registration.earliest_refresh_at = epoch_seconds(tokens.get("earliest_refresh_at"))
        self.vault.set(self.registration.dumps())

    def refresh(self) -> None:
        earliest = self.registration.earliest_refresh_at
        wait = (earliest or 0) - time.time()
        if wait > MAX_REFRESH_WAIT_S:
            raise SignInError(f"earliest_refresh_at is {wait:.0f} s away; rerun later")
        if wait > 0:
            print(f"waiting {wait:.0f} s for earliest_refresh_at")
            time.sleep(wait + 1)
        reply = post_form(
            TOKEN_URL,
            {
                "grant_type": "refresh_token",
                "client_id": self.registration.client_id,
                "refresh_token": self.registration.refresh_token,
                "resource": RESOURCE,
            },
        )
        if reply.status != 200:
            raise SignInError(f"refresh failed: {token_error(reply)}")
        self.accept(json.loads(reply.body))

    def access_token(self) -> str:
        if self._access is None or time.time() > self._expires_at - REFRESH_MARGIN_S:
            self.refresh()
        if self._access is None:
            raise SignInError("no access token after refresh")
        return self._access


def load_session(vault: Vault) -> Session:
    raw = vault.get()
    if raw is None:
        raise SignInError(f"no registration under keyring {KEYRING_SERVICE}; run without --reuse")
    registration = Registration.loads(raw)
    if not registration.refresh_token:
        raise SignInError("the saved registration has no refresh token; run without --reuse")
    return Session(registration, vault)


@dataclass(frozen=True)
class Grant:
    client_id: str
    code: str
    verifier: str
    redirect_uri: str
    nonce: str


def authorize(
    client_id: str, host_id: str, *, timeout_s: float, log: Callable[[str], None]
) -> Grant:
    """One browser authorization. Returns the code with the values its exchange must repeat.
    A new registration's callback names the issued client id; a reauthorization keeps the
    one it asked with."""
    verifier, challenge = pkce_pair()
    state, nonce = secrets.token_urlsafe(24), secrets.token_urlsafe(24)
    server = open_callback_server()
    redirect_uri = f"http://127.0.0.1:{server.server_address[1]}{CALLBACK_PATH}"
    url = authorize_url(
        client_id=client_id,
        host_id=host_id,
        redirect_uri=redirect_uri,
        state=state,
        nonce=nonce,
        challenge=challenge,
    )
    new = client_id == REGISTRATION_CLIENT
    log(f"flow: {'new registration' if new else 'reauthorization'}")
    log(f"authorize_endpoint: {AUTHORIZE_URL}")
    log(f"redirect_uri: {redirect_uri}")
    log(f"agent_name_hint: {AGENT_NAME if new else '(omitted on reauthorization)'}")
    print(f"Opening OpenAI's sign-in page. Approve 'QMA' there.\n{url}")
    webbrowser.open(url)
    with server:
        query = wait_for_callback(server, timeout_s)
    log(f"callback_keys: {sorted(query)}")
    callback = parse_callback(query, state)
    issued = callback.client_id or (None if new else client_id)
    if issued is None or issued == REGISTRATION_CLIENT:
        raise SignInError("new registration returned no issued client_id")
    if not new and issued != client_id:
        raise SignInError("callback client_id differs from the saved registration")
    log(f"issued_client_id_prefix: {issued.split('_')[0]}_")
    return Grant(issued, callback.code, verifier, redirect_uri, nonce)


def exchange(grant: Grant) -> HttpReply:
    return post_form(
        TOKEN_URL,
        {
            "grant_type": "authorization_code",
            "client_id": grant.client_id,
            "code": grant.code,
            "code_verifier": grant.verifier,
            "redirect_uri": grant.redirect_uri,
            "resource": RESOURCE,
        },
    )


def sign_in(vault: Vault, *, timeout_s: float, log: Callable[[str], None]) -> Session:
    """P0. Opens OpenAI's page; the operator approves "QMA". A saved registration is reused
    (issued client id, same host id) so a second run does not register a second client.
    The issued client id is saved before the code exchange, and an invalid_grant gets one
    fresh reauthorization with it, as OpenAI's sign-in docs prescribe."""
    raw = vault.get()
    saved = Registration.loads(raw) if raw else None
    client_id = saved.client_id if saved else REGISTRATION_CLIENT
    host_id = saved.host_id if saved else f"urn:uuid:{uuid.uuid4()}"
    grant = authorize(client_id, host_id, timeout_s=timeout_s, log=log)
    if saved is None:
        vault.set(Registration(grant.client_id, host_id, "", ()).dumps())
    client_id = grant.client_id
    reply = exchange(grant)
    if token_error_code(reply) == "invalid_grant":
        log(f"exchange_1: {token_error(reply)}")
        grant = authorize(client_id, host_id, timeout_s=timeout_s, log=log)
        reply = exchange(grant)
    if reply.status != 200:
        raise SignInError(f"code exchange failed: {token_error(reply)}")
    tokens = json.loads(reply.body)
    claims = jwt_claims(tokens["id_token"])
    if claims.get("nonce") != grant.nonce or claims.get("iss") != ISSUER:
        raise SignInError("id_token nonce or issuer does not match")
    audience = claims.get("aud")
    if client_id not in (audience if isinstance(audience, list) else [audience]):
        raise SignInError("id_token audience is not the issued client id")
    session = Session(Registration(client_id, host_id, tokens.get("refresh_token", ""), ()), vault)
    session.accept(tokens)
    log(f"granted_scopes: {' '.join(session.registration.scopes)}")
    log(f"expires_in: {tokens.get('expires_in')}")
    log(f"earliest_refresh_at: {tokens.get('earliest_refresh_at')}")
    log(f"refresh_token_stored_under: keyring {KEYRING_SERVICE} / {KEYRING_USER}")
    return session


def get_models(token: str) -> HttpReply:
    headers = {"Authorization": f"Bearer {token}"}
    return _send(urllib.request.Request(f"{API}/models", headers=headers))  # noqa: S310


def post_responses(token: str, body: Mapping[str, Any]) -> StreamResult:
    request = urllib.request.Request(  # noqa: S310
        f"{API}/responses",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    started = time.perf_counter()
    try:
        response = urllib.request.urlopen(request, timeout=180)  # noqa: S310
    except urllib.error.HTTPError as err:
        return error_result(err.code, err.headers.get("x-request-id"), err.read())
    with response:
        first = response.readline()
        first_byte_s = time.perf_counter() - started
        lines = (raw.decode() for raw in itertools.chain([first], response))
        return fold_events(
            response.status, response.headers.get("x-request-id"), first_byte_s, parse_sse(lines)
        )


@dataclass(frozen=True)
class StepResult:
    step: str
    passed: bool
    detail: str


class Evidence:
    def __init__(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self.folder = folder

    def writer(self, slug: str) -> Callable[[str], None]:
        path = self.folder / f"{slug}.log"
        path.write_text(f"# {slug} {datetime.now(UTC).isoformat()}\n", encoding="utf-8")

        def write(line: str) -> None:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
            print(f"[{slug}] {line}")

        return write


HELLO = {"role": "user", "content": "Say exactly: hello from QMA"}
ECHO_TOOL = {
    "name": "echo_word",
    "description": "Echo one word back to the caller.",
    "input_schema": {
        "type": "object",
        "properties": {"word": {"type": "string"}},
        "required": ["word"],
        "additionalProperties": False,
    },
}
TOOL_ASK = {
    "role": "user",
    "content": "Call the echo_word tool with word set to pineapple. Do not answer in text first.",
}


def hello_body(model: str) -> Json:
    return responses_body(
        {"model": model, "system": "You are a terse probe.", "messages": [HELLO], "max_tokens": 64}
    )


def tool_request(model: str) -> Json:
    return {
        "model": model,
        "system": "You are a probe. Use the tool when asked.",
        "messages": [TOOL_ASK],
        "tools": [ECHO_TOOL],
    }


def _log_body(log: Callable[[str], None], label: str, body: Mapping[str, Any]) -> None:
    log(f"{label}_body: {json.dumps(body, sort_keys=True)}")


def _log_result(log: Callable[[str], None], label: str, result: StreamResult) -> None:
    for line in result.lines():
        log(f"{label}_{line}")


def probe_models(session: Session, ev: Evidence) -> tuple[StepResult, list[str]]:
    log = ev.writer("hp2-p1")
    reply = get_models(session.access_token())
    log(f"http_status: {reply.status}")
    log(f"request_id: {reply.request_id}")
    if reply.status != 200:
        log(f"body: {reply.body[:400]!r}")
        return StepResult("P1", False, f"/v1/models returned {reply.status}"), []
    slugs = model_slugs(json.loads(reply.body))
    log(f"slugs: {slugs}")
    gpt = [s for s in slugs if s.startswith("gpt")]
    detail = f"{len(slugs)} models, gpt slugs {gpt}"
    log(f"result: {'PASS' if gpt else 'FAIL'} {detail}")
    return StepResult("P1", bool(gpt), detail), gpt


def probe_hello(session: Session, ev: Evidence, model: str, slug: str = "hp2-p2") -> StepResult:
    log = ev.writer(slug)
    body = hello_body(model)
    _log_body(log, "request", body)
    result = post_responses(session.access_token(), body)
    _log_result(log, "response", result)
    if result.completed:
        detail = f"completed, first byte {result.first_byte_s:.2f} s"
    elif result.error_code == NOT_ELIGIBLE:
        detail = f"stop rule: {NOT_ELIGIBLE}"
    else:
        detail = f"no response.completed (status {result.status}, code {result.error_code})"
    log(f"result: {'PASS' if result.completed else 'FAIL'} {detail}")
    return StepResult("P2", result.completed, detail)


def probe_tools(session: Session, ev: Evidence, model: str, shape: ToolsShape) -> StepResult:
    log = ev.writer(f"hp2-p3-{shape}")
    body = responses_body(tool_request(model), tools_shape=shape)
    _log_body(log, "turn1", body)
    first = post_responses(session.access_token(), body)
    _log_result(log, "turn1", first)
    calls = [c for c in first.function_calls() if c.get("name") == ECHO_TOOL["name"]]
    if not first.completed or not calls:
        detail = (
            f"no echo_word call (status {first.status}, code {first.error_code}, "
            f"param {first.error_param})"
        )
        log(f"result: FAIL {detail}")
        return StepResult(f"P3-{shape}", False, detail)
    call = calls[0]
    log(f"function_call: name={call.get('name')} namespace={call.get('namespace')}")
    follow = {
        **body,
        "input": [
            *body["input"],
            *replay_items(first.output, keep_reasoning=False),
            {"type": "function_call_output", "call_id": call["call_id"], "output": "pineapple"},
        ],
    }
    _log_body(log, "turn2", follow)
    second = post_responses(session.access_token(), follow)
    _log_result(log, "turn2", second)
    detail = f"call {call.get('name')} namespace={call.get('namespace')}, turn2 {second.terminal}"
    log(f"result: {'PASS' if second.completed else 'FAIL'} {detail}")
    return StepResult(f"P3-{shape}", second.completed, detail)


def probe_reasoning(session: Session, ev: Evidence, model: str, shape: ToolsShape) -> StepResult:
    log = ev.writer("hp2-p4")
    body = responses_body(tool_request(model), tools_shape=shape, include_reasoning=True)
    _log_body(log, "turn1", body)
    first = post_responses(session.access_token(), body)
    _log_result(log, "turn1", first)
    reasoning = [i for i in first.output if i.get("type") == "reasoning"]
    encrypted = [i for i in reasoning if i.get("encrypted_content")]
    log(f"reasoning_items: {len(reasoning)} with_encrypted_content: {len(encrypted)}")
    calls = first.function_calls()
    if not first.completed or not encrypted or not calls:
        detail = (
            f"turn1 {first.terminal}, code {first.error_code}, "
            f"param {first.error_param}, encrypted {len(encrypted)}"
        )
        log(f"result: FAIL {detail}")
        return StepResult("P4", False, detail)
    follow = {
        **body,
        "input": [
            *body["input"],
            *replay_items(first.output, keep_reasoning=True),
            {"type": "function_call_output", "call_id": calls[0]["call_id"], "output": "pineapple"},
        ],
    }
    log(f"turn2_replayed_reasoning_items: {len(encrypted)}")
    second = post_responses(session.access_token(), follow)
    _log_result(log, "turn2", second)
    detail = f"encrypted_content returned, replay turn2 {second.terminal} code {second.error_code}"
    log(f"result: {'PASS' if second.completed else 'FAIL'} {detail}")
    return StepResult("P4", second.completed, detail)


BARRED: dict[str, Callable[[Json], Json]] = {
    "max_output_tokens": lambda body: {**body, "max_output_tokens": 64},
    "temperature": lambda body: {**body, "temperature": 0.2},
    "metadata": lambda body: {**body, "metadata": {"probe": "qma"}},
    "system_role_item": lambda body: {
        **body,
        "input": [
            {"type": "message", "role": "system", "content": "You are a probe."},
            *body["input"],
        ],
    },
}


def probe_barred(session: Session, ev: Evidence, model: str) -> StepResult:
    log = ev.writer("hp2-p5")
    refused: list[str] = []
    for name, mutate in BARRED.items():
        result = post_responses(session.access_token(), mutate(hello_body(model)))
        log(
            f"{name}: http_status={result.status} code={result.error_code} "
            f"param={result.error_param} terminal={result.terminal}"
        )
        if result.status == 400:
            refused.append(name)
    accepted = [name for name in BARRED if name not in refused]
    detail = f"400 for {refused}; accepted {accepted}"
    log(f"result: {'PASS' if not accepted else 'FAIL'} {detail}")
    return StepResult("P5", not accepted, detail)


def perf_series(
    session: Session, ev: Evidence, model: str, runs: int, spacing_s: float
) -> StepResult:
    log = ev.writer("hp2-perf")
    samples: list[float] = []
    for index in range(runs):
        if index:
            time.sleep(spacing_s)
        result = post_responses(session.access_token(), hello_body(model))
        log(f"run {index + 1}: first_byte_s={result.first_byte_s} terminal={result.terminal}")
        if result.completed and result.first_byte_s is not None:
            samples.append(result.first_byte_s)
    if len(samples) < runs:
        log(f"result: FAIL only {len(samples)} of {runs} runs completed")
        return StepResult("perf", False, f"{len(samples)} of {runs} completed")
    median = statistics.median(samples)
    log("baseline: trunk has no GPT route; this head median is the reference for HP16")
    log(f"median_first_byte_s: {median:.3f} limit_s: {PERF_LIMIT_S}")
    passed = median <= PERF_LIMIT_S
    log(f"result: {'PASS' if passed else 'FAIL'}")
    return StepResult("perf", passed, f"median first byte {median:.2f} s over {runs} runs")


def scan_for_secrets(paths: Iterable[Path], values: Iterable[str]) -> list[Path]:
    needles = [v for v in values if v]
    return [
        path
        for path in paths
        if path.is_file()
        and any(n in path.read_text(encoding="utf-8", errors="replace") for n in needles)
    ]


def secrets_scan(session: Session, ev: Evidence, findings: Path) -> StepResult:
    log = ev.writer("hp2-secrets")
    paths = sorted(p for p in ev.folder.iterdir() if p.name != "hp2-secrets.log")
    paths.append(findings)
    log(f"token_values_checked: {len(session.secrets_seen)} (access and refresh, this process)")
    for path in paths:
        log(f"scanned: {path}")
    hits = scan_for_secrets(paths, session.secrets_seen)
    log(f"files_with_a_token_value: {[str(p) for p in hits]}")
    log(f"result: {'PASS' if not hits else 'FAIL'}")
    return StepResult("secrets", not hits, f"{len(hits)} files hold a token value")


@dataclass(frozen=True)
class Verdict:
    viable: bool
    model: str | None
    tools_shape: ToolsShape | None
    reasoning_replay: bool | None
    stopped_at: str | None
    steps: tuple[StepResult, ...]

    def row(self) -> str:
        if self.viable:
            outcome = (
                f"viable | model `{self.model}` | tools_shape `{self.tools_shape}` "
                f"| reasoning_replay `{str(self.reasoning_replay).lower()}`"
            )
        else:
            outcome = f"not viable | stop rule at {self.stopped_at} | |"
        steps = "; ".join(
            f"{s.step} {'PASS' if s.passed else 'FAIL'}: {s.detail}" for s in self.steps
        )
        return f"| GPT on ChatGPT plan | {datetime.now(UTC).date()} | {outcome} | {steps} |"


def run_chain(
    session: Session, ev: Evidence, *, model: str | None, perf_runs: int, perf_spacing_s: float
) -> Verdict:
    steps: list[StepResult] = []

    def stop(at: str) -> Verdict:
        return Verdict(False, model, None, None, at, tuple(steps))

    p1, gpt = probe_models(session, ev)
    steps.append(p1)
    if not p1.passed:
        return stop("P1")
    model = model or gpt[0]
    steps.append(probe_hello(session, ev, model))
    if not steps[-1].passed:
        return stop(f"P2 ({steps[-1].detail})")
    namespace = probe_tools(session, ev, model, "namespace")
    plain = probe_tools(session, ev, model, "plain")
    steps += [namespace, plain]
    if not namespace.passed and not plain.passed:
        return stop("P3 (both tool shapes failed)")
    shape: ToolsShape = "namespace" if namespace.passed else "plain"
    p4 = probe_reasoning(session, ev, model, shape)
    steps.append(p4)
    p5 = probe_barred(session, ev, model)
    steps.append(p5)
    if not p5.passed:
        return stop(f"P5 ({p5.detail})")
    if perf_runs:
        steps.append(perf_series(session, ev, model, perf_runs, perf_spacing_s))
    return Verdict(True, model, shape, p4.passed, None, tuple(steps))


def _write_verdict(ev: Evidence, verdict: Verdict) -> None:
    payload = {
        "viable": verdict.viable,
        "model": verdict.model,
        "tools_shape": verdict.tools_shape,
        "reasoning_replay": verdict.reasoning_replay,
        "stopped_at": verdict.stopped_at,
        "steps": [s.__dict__ for s in verdict.steps],
    }
    (ev.folder / "hp2-verdict.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (ev.folder / "hp2-findings-row.md").write_text(verdict.row() + "\n", encoding="utf-8")


def cmd_run(args: argparse.Namespace) -> int:
    ev = Evidence(args.evidence)
    vault = KeyringVault()
    if args.reuse:
        session = load_session(vault)
    else:
        log = ev.writer("hp2-p0")
        try:
            session = sign_in(vault, timeout_s=args.signin_timeout, log=log)
        except SignInError as err:
            log(f"result: FAIL {err}")
            return 1
        granted = DIRECT_SCOPE in session.registration.scopes
        log(f"result: {'PASS' if granted else 'FAIL'} {DIRECT_SCOPE} granted={granted}")
        if not granted:
            return 1
    verdict = run_chain(
        session, ev, model=args.model, perf_runs=args.perf_runs, perf_spacing_s=args.perf_spacing
    )
    _write_verdict(ev, verdict)
    print(verdict.row())
    scan = secrets_scan(session, ev, args.findings)
    return 0 if verdict.viable and scan.passed else 1


def cmd_refresh(args: argparse.Namespace) -> int:
    ev = Evidence(args.evidence)
    vault = KeyringVault()
    session = load_session(vault)
    log = ev.writer("hp2-refresh")
    before = session.registration.refresh_token
    session.refresh()
    stored = load_session(vault).registration.refresh_token
    rotated = stored != before
    in_store = stored == session.registration.refresh_token
    access = session.access_token()
    raw = vault.get() or ""
    log(f"keyring: {KEYRING_SERVICE} / {KEYRING_USER}")
    log(f"refresh_token_rotated: {rotated}")
    log(f"keyring_holds_rotated_token: {in_store}")
    log(f"access_token_in_keyring_record: {access in raw}")
    passed = rotated and in_store and access not in raw
    log(f"result: {'PASS' if passed else 'FAIL'}")
    scan = secrets_scan(session, ev, args.findings)
    return 0 if passed and scan.passed else 1


def cmd_scan(args: argparse.Namespace) -> int:
    session = load_session(KeyringVault())
    session.access_token()
    return 0 if secrets_scan(session, Evidence(args.evidence), args.findings).passed else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "refresh", "scan"):
        command = sub.add_parser(name)
        command.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
        command.add_argument("--findings", type=Path, default=FINDINGS)
        if name == "run":
            command.add_argument(
                "--reuse", action="store_true", help="skip P0, use the stored token"
            )
            command.add_argument("--model", help="GPT slug; default is the first listed by P1")
            command.add_argument("--signin-timeout", type=float, default=600)
            command.add_argument("--perf-runs", type=int, default=5)
            command.add_argument("--perf-spacing", type=float, default=60)
    args = parser.parse_args(argv)
    handlers = {"run": cmd_run, "refresh": cmd_refresh, "scan": cmd_scan}
    try:
        return handlers[args.command](args)
    except SignInError as err:
        print(f"FAIL: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
