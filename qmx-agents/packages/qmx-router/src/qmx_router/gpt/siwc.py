"""Sign in with ChatGPT for QMA (developers.openai.com/siwc; 02b section D items 1, 2 and 9).

Flow, ported from HP2's probe: `client_id=dynamic_agent_client` with `agent_name_hint="QMA"` on
the first sign-in, then the issued `oaiapp_` client id; a persisted `ext_agent_host_id`; PKCE
S256; a loopback callback on 127.0.0.1. The grant must hold `chatgpt.tokens.use.direct`. The
id_token's signature (OpenAI's JWKS), issuer, audience, expiry and nonce are checked, and a
reauthorization must name the same account (`sub`) as the stored one.

Storage: one JSON record in the OS secret store under `qmx/chatgpt`, local and under the user's
control: the registration, the rotating refresh token, the account and the background-consent
flag. The access token lives in this process's memory only. It cannot sit in the record: a
Windows credential holds at most 2,560 bytes, and a record with the access token in it failed
to store (CredWrite error 1783, measured in HP16). Nothing else holds a token: no log line,
file or reply.

Background use needs express consent (SIWC terms). The flag is stored here and enforced at
grant time: `Relay.grant(..., unattended=True)` refuses a GPT grant without it (B17).
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import secrets
import time
import urllib.parse
import uuid
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Final, Protocol, cast

import httpx
import jwt
import keyring

AUTHORIZE_URL: Final = "https://auth.openai.com/api/accounts/authorize"
TOKEN_URL: Final = "https://auth.openai.com/api/accounts/oauth/token"  # noqa: S105
JWKS_URL: Final = "https://auth.openai.com/.well-known/jwks.json"
ISSUER: Final = "https://auth.openai.com"
API: Final = "https://api.openai.com/v1"
SCOPES: Final = "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct"
DIRECT_SCOPE: Final = "chatgpt.tokens.use.direct"
AGENT_NAME: Final = "QMA"
REGISTRATION_CLIENT: Final = "dynamic_agent_client"
ENTRY: Final = "qmx/chatgpt"
ENTRY_USER: Final = "chatgpt"
CALLBACK_PATH: Final = "/auth/callback"
CALLBACK_PORTS: Final = (1455, 1456, 1457, 1458)
REFRESH_MARGIN_S: Final = 300.0
SIGN_IN_TIMEOUT_S: Final = 600.0
HTTP_TIMEOUT: Final = httpx.Timeout(30.0)

TOKEN_ERRORS: Final[Mapping[str, str]] = {
    "invalid_request": "a parameter is missing or the body is not form-encoded",
    "invalid_client": "this client id cannot use the token endpoint",
    "unsupported_grant_type": "grant_type is wrong",
    "invalid_grant": (
        "the code or refresh token was rejected, used or expired; sign in again with /login chatgpt"
    ),
}
"""The token endpoint's `error` codes. Its error bodies carry only `error` (HP2, measured)."""


class SignInError(RuntimeError):
    """The ChatGPT sign-in is missing, refused or expired. The message never holds a token."""


@dataclass(frozen=True)
class Record:
    """The `qmx/chatgpt` entry. HP2's records lack the last two fields."""

    client_id: str
    host_id: str
    refresh_token: str = field(repr=False)
    scopes: tuple[str, ...]
    earliest_refresh_at: float | None = None
    account: str | None = None
    background_consent: bool = False

    def dumps(self) -> str:
        return json.dumps(asdict(self) | {"scopes": list(self.scopes)})

    @classmethod
    def loads(cls, raw: str) -> Record:
        data = cast("dict[str, Any]", json.loads(raw))
        return cls(
            client_id=str(data["client_id"]),
            host_id=str(data["host_id"]),
            refresh_token=str(data.get("refresh_token") or ""),
            scopes=tuple(str(scope) for scope in data.get("scopes") or ()),
            earliest_refresh_at=_epoch(data.get("earliest_refresh_at")),
            account=data.get("account"),
            background_consent=data.get("background_consent") is True,
        )


class Vault(Protocol):
    def get(self) -> str | None: ...
    def set(self, value: str) -> None: ...


class KeyringVault:
    """The OS secret store entry `qmx/chatgpt`."""

    def get(self) -> str | None:
        return keyring.get_password(ENTRY, ENTRY_USER)

    def set(self, value: str) -> None:
        keyring.set_password(ENTRY, ENTRY_USER, value)


def _epoch(value: object) -> float | None:
    """`earliest_refresh_at` has no documented format; Unix seconds or ISO 8601 are taken."""
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str) and value:
        try:
            return float(value)
        except ValueError:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    return None


def token_error(response: httpx.Response) -> str:
    try:
        body: object = response.json()
    except ValueError:
        body = None
    code = str(cast("dict[str, Any]", body).get("error")) if isinstance(body, dict) else "not JSON"
    meaning = TOKEN_ERRORS.get(code, "not in the documented set")
    return f"http {response.status_code} {code}: {meaning}"


@dataclass
class SiwcSession:
    """One ChatGPT sign-in, shared by every GPT chat in this process. The lock is the one real
    single-writer rule here: refresh tokens rotate, so two refreshes must never race."""

    record: Record
    vault: Vault = field(repr=False)
    transport: httpx.AsyncBaseTransport | None = None
    """Tests only: an in-process OpenAI."""
    api: str = API
    clock: Callable[[], float] = time.time
    seen: set[str] = field(default_factory=set[str], repr=False)
    """Every token value this process handled, for the S17 search. Never written anywhere."""
    store_error: str | None = None
    """Why the last rotated refresh token could not be stored, if it could not. The session
    keeps working from memory until this process ends."""
    _access: str | None = field(default=None, repr=False)
    _expires_at: float = 0.0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def __post_init__(self) -> None:
        self.seen.add(self.record.refresh_token)

    @property
    def background_consent(self) -> bool:
        return self.record.background_consent

    @property
    def scopes(self) -> tuple[str, ...]:
        return self.record.scopes

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=self.transport, timeout=HTTP_TIMEOUT, trust_env=False)

    async def access_token(self) -> str:
        """The access token, refreshed under the lock when within five minutes of expiry.
        Before a refresh the stored record is re-read, so a refresh token another process
        rotated is the one used."""
        async with self._lock:
            if self._access is None or self.clock() >= self._expires_at - REFRESH_MARGIN_S:
                stored = await asyncio.to_thread(self.vault.get)
                if stored is not None and self.store_error is None:
                    found = Record.loads(stored)
                    if found.client_id == self.record.client_id:
                        self.record = found
                        self.seen.add(found.refresh_token)
                await self._refresh()
            if self._access is None:
                raise SignInError("no ChatGPT access token after a refresh")
            return self._access

    async def set_background_consent(self, consent: bool) -> None:
        async with self._lock:
            self.record = replace(self.record, background_consent=consent)
            await asyncio.to_thread(self.vault.set, self.record.dumps())

    async def _refresh(self) -> None:
        earliest = self.record.earliest_refresh_at
        early = (
            ""
            if earliest is None or earliest <= self.clock()
            else (f"; OpenAI allows the next refresh from {datetime.fromtimestamp(earliest):%H:%M}")
        )
        form = {
            "grant_type": "refresh_token",
            "client_id": self.record.client_id,
            "refresh_token": self.record.refresh_token,
            "resource": API,
        }
        try:
            async with self.client() as client:
                response = await client.post(TOKEN_URL, data=form)
        except httpx.HTTPError as error:
            raise SignInError(
                f"the ChatGPT token refresh did not answer: {type(error).__name__}"
            ) from None
        if response.status_code != 200:
            raise SignInError(f"the ChatGPT token refresh failed: {token_error(response)}{early}")
        await self.accept(response.json())

    async def accept(self, tokens: Mapping[str, Any]) -> None:
        """Take a token reply: the access token into memory, the rotated refresh token into the
        record and the record into the vault. A reply that names its scopes must still grant
        the direct scope. A vault that refuses the write leaves the session working from
        memory and names the reason in `store_error`."""
        access = str(tokens["access_token"])
        self.seen.add(access)
        scopes = self.record.scopes
        if "scope" in tokens:
            scopes = tuple(sorted(str(tokens["scope"]).split()))
            if DIRECT_SCOPE not in scopes:
                raise SignInError(f"the ChatGPT grant no longer holds {DIRECT_SCOPE}")
        self.record = replace(
            self.record,
            refresh_token=str(tokens.get("refresh_token") or self.record.refresh_token),
            scopes=scopes,
            earliest_refresh_at=_epoch(tokens.get("earliest_refresh_at")),
        )
        self.seen.add(self.record.refresh_token)
        self._access = access
        self._expires_at = self.clock() + float(tokens.get("expires_in", 3600))
        try:
            await asyncio.to_thread(self.vault.set, self.record.dumps())
        except Exception as error:
            self.store_error = (
                f"the rotated ChatGPT refresh token could not be stored in {ENTRY} "
                f"({type(error).__name__}); sign in again after this host stops"
            )
        else:
            self.store_error = None


async def list_models(session: SiwcSession) -> list[str]:
    """`GET /v1/models` with the sign-in's token. This route answers `models` with `slug` and
    `visibility` (HP2)."""
    token = await session.access_token()
    try:
        async with session.client() as client:
            reply = await client.get(
                f"{session.api}/models", headers={"authorization": f"Bearer {token}"}
            )
    except httpx.HTTPError as error:
        raise SignInError(f"/v1/models did not answer: {type(error).__name__}") from None
    if reply.status_code != 200:
        raise SignInError(f"/v1/models returned {reply.status_code}")
    payload = cast("dict[str, Any]", reply.json())
    if "models" in payload:
        models = cast("list[dict[str, Any]]", payload["models"])
        return [str(m["slug"]) for m in models if m.get("visibility", "list") == "list"]
    return [str(m["id"]) for m in cast("list[dict[str, Any]]", payload.get("data", []))]


def load(vault: Vault | None = None) -> SiwcSession | None:
    """The stored sign-in, or None when there is none. Makes no network call."""
    vault = vault or KeyringVault()
    raw = vault.get()
    if raw is None:
        return None
    record = Record.loads(raw)
    return SiwcSession(record, vault) if record.refresh_token else None


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def authorize_url(
    *, client_id: str, host_id: str, redirect_uri: str, state: str, nonce: str, challenge: str
) -> str:
    """`agent_name_hint` only on a new registration; a reauthorization uses the issued id."""
    params = {
        "client_id": client_id,
        "ext_agent_host_id": host_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
        "resource": API,
        "state": state,
        "nonce": nonce,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
    }
    if client_id == REGISTRATION_CLIENT:
        params["agent_name_hint"] = AGENT_NAME
    return f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"


class _CallbackServer(HTTPServer):
    """No SO_REUSEADDR: on Windows it lets a second listener bind a busy port and split the
    callbacks."""

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


def _callback_server() -> _CallbackServer:
    for port in CALLBACK_PORTS:
        try:
            return _CallbackServer(("127.0.0.1", port), _CallbackHandler)
        except OSError:
            continue
    raise SignInError(f"no free loopback port among {list(CALLBACK_PORTS)}")


def _wait_for_callback(server: _CallbackServer, timeout_s: float) -> dict[str, str]:
    deadline = time.monotonic() + timeout_s
    server.timeout = 1.0
    with server:
        while server.query is None:
            if time.monotonic() > deadline:
                raise SignInError(f"no sign-in callback within {timeout_s:.0f} s")
            server.handle_request()
        return server.query


@dataclass(frozen=True)
class Callback:
    code: str
    client_id: str


def parse_callback(query: Mapping[str, str], *, state: str, asked_with: str) -> Callback:
    """The code and the client id it was issued to. A new registration's callback names the
    issued `oaiapp_` id; a reauthorization keeps the one it asked with."""
    if not secrets.compare_digest(query.get("state", ""), state):
        raise SignInError("the sign-in callback does not match this attempt")
    if "error" in query:
        raise SignInError(f"OpenAI refused the sign-in: {query['error']}")
    if "code" not in query:
        raise SignInError("the sign-in callback carried no code")
    issued = query.get("client_id") or (None if asked_with == REGISTRATION_CLIENT else asked_with)
    if issued is None or issued == REGISTRATION_CLIENT:
        raise SignInError("the new registration returned no client id")
    if asked_with not in (REGISTRATION_CLIENT, issued):
        raise SignInError("the callback's client id differs from the stored registration")
    return Callback(query["code"], issued)


type Keys = Callable[[str], Any]
"""The signing key for a JWT, from OpenAI's JWKS."""


def jwks_keys(token: str) -> Any:
    return jwt.PyJWKClient(JWKS_URL).get_signing_key_from_jwt(token).key


def check_id_token(
    id_token: str, *, client_id: str, nonce: str, account: str | None, keys: Keys = jwks_keys
) -> str:
    """The account (`sub`) of a verified id_token: signature against OpenAI's keys, issuer,
    audience and expiry by PyJWT, then the nonce, then the stored account if one exists."""
    try:
        claims: dict[str, Any] = jwt.decode(
            id_token,
            keys(id_token),
            algorithms=["RS256"],
            audience=client_id,
            issuer=ISSUER,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except jwt.PyJWTError as error:
        raise SignInError(f"the id_token did not verify: {type(error).__name__}") from None
    if not secrets.compare_digest(str(claims.get("nonce", "")), nonce):
        raise SignInError("the id_token nonce does not match this sign-in")
    subject = str(claims["sub"])
    if account is not None and subject != account:
        raise SignInError("this sign-in is a different ChatGPT account from the stored one")
    return subject


async def sign_in(
    vault: Vault | None = None,
    *,
    open_page: Callable[[str], object],
    timeout_s: float = SIGN_IN_TIMEOUT_S,
    keys: Keys = jwks_keys,
) -> SiwcSession:
    """Opens OpenAI's page with `open_page`; the operator approves "QMA". A stored registration
    is reused (issued client id, same host id, same account), so a second sign-in does not
    register a second client. Refuses a grant without `chatgpt.tokens.use.direct`."""
    vault = vault or KeyringVault()
    raw = await asyncio.to_thread(vault.get)
    saved = Record.loads(raw) if raw else None
    asked_with = saved.client_id if saved else REGISTRATION_CLIENT
    host_id = saved.host_id if saved else f"urn:uuid:{uuid.uuid4()}"
    verifier, challenge = pkce_pair()
    state, nonce = secrets.token_urlsafe(24), secrets.token_urlsafe(24)
    server = _callback_server()
    redirect_uri = f"http://127.0.0.1:{server.server_address[1]}{CALLBACK_PATH}"
    open_page(
        authorize_url(
            client_id=asked_with,
            host_id=host_id,
            redirect_uri=redirect_uri,
            state=state,
            nonce=nonce,
            challenge=challenge,
        )
    )
    query = await asyncio.to_thread(_wait_for_callback, server, timeout_s)
    callback = parse_callback(query, state=state, asked_with=asked_with)
    form = {
        "grant_type": "authorization_code",
        "client_id": callback.client_id,
        "code": callback.code,
        "code_verifier": verifier,
        "redirect_uri": redirect_uri,
        "resource": API,
    }
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, trust_env=False) as client:
        response = await client.post(TOKEN_URL, data=form)
    if response.status_code != 200:
        raise SignInError(f"the ChatGPT code exchange failed: {token_error(response)}")
    tokens = cast("dict[str, Any]", response.json())
    account = await asyncio.to_thread(
        check_id_token,
        str(tokens.get("id_token", "")),
        client_id=callback.client_id,
        nonce=nonce,
        account=saved.account if saved else None,
        keys=keys,
    )
    if DIRECT_SCOPE not in str(tokens.get("scope", "")).split():
        raise SignInError(f"OpenAI did not grant {DIRECT_SCOPE}; this plan cannot use it")
    record = Record(
        client_id=callback.client_id,
        host_id=host_id,
        refresh_token=str(tokens.get("refresh_token", "")),
        scopes=(),
        account=account,
        background_consent=saved.background_consent if saved else False,
    )
    session = SiwcSession(record, vault)
    await session.accept(tokens)
    return session
