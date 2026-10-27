"""cTrader's sign-in, the parts that do not depend on where they run (engine AD-67, seam B).

The PC's loopback receiver takes the one `code` cTrader's consent page redirects to, hands it to
a forward the caller supplies, answers the browser with a plain page and stops. It keeps nothing:
the code lives in one local variable for the length of that forward. The home exchanges the code
with the app's client id and secret at cTrader's token endpoint. That request carries the secret
in its query string, so nothing here logs, prints or raises with a request URL in it.

cTrader's flow sends no `state`. The home's pending window and the single-use code are the replay
guard [retrieved: help.ctrader.com/open-api/account-authentication].
"""

from __future__ import annotations

import json
import os
import socket
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Final, Literal, cast, override
from urllib.parse import parse_qs, urlencode, urlsplit

CONSENT_URL: Final = "https://id.ctrader.com/my/settings/openapi/grantingaccess/"
TOKEN_URL: Final = "https://openapi.ctrader.com/apps/token"  # noqa: S105 - an endpoint, not a token
SCOPE: Final = "accounts"
"""View only: the read app never asks for `trading`."""
DEFAULT_REDIRECT: Final = "http://127.0.0.1:47613/ctrader/callback"
"""Used until Settings names the redirect registered on his app (`[ctrader] redirect`)."""
LOOPBACK_HOSTS: Final = frozenset({"127.0.0.1", "localhost", "::1"})
CALL_TIMEOUT_S: Final = 20.0


class OAuthRefused(Exception):
    """The token endpoint, the redirect or the receiver refused. `code` is the closed word; the
    message never holds a request URL, a code or a token."""

    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(f"{code}: {message}" if message else code)
        self.code = code
        self.message = message


class PortBusy(OAuthRefused):
    """The registered redirect port is taken, so the browser must not open."""


@dataclass(frozen=True, slots=True)
class Redirect:
    """The redirect registered on his app: a loopback address, a port and a path."""

    url: str
    host: str
    port: int
    path: str

    @classmethod
    def parse(cls, text: str) -> Redirect:
        parts = urlsplit(text.strip())
        host = (parts.hostname or "").lower()
        if parts.scheme != "http" or host not in LOOPBACK_HOSTS or parts.port is None:
            raise OAuthRefused(
                "redirect_not_loopback",
                "the redirect must be http on 127.0.0.1, localhost or ::1 with a port",
            )
        return cls(text.strip(), host, parts.port, parts.path or "/")


@dataclass(frozen=True, slots=True)
class AppCredential:
    """The read app's id and secret, as `qmx/read/ctrader-app` holds them."""

    client_id: str = field(repr=False)
    client_secret: str = field(repr=False)

    @classmethod
    def parse(cls, raw: str) -> AppCredential:
        try:
            value = cast("dict[str, object]", json.loads(raw))
            client_id, secret = value["clientId"], value["clientSecret"]
        except ValueError, TypeError, KeyError:
            raise OAuthRefused(
                "app_credential_malformed", "qmx/read/ctrader-app needs clientId and clientSecret"
            ) from None
        if not isinstance(client_id, str) or not isinstance(secret, str) or not client_id:
            raise OAuthRefused("app_credential_malformed", "clientId and clientSecret are text")
        return cls(client_id, secret)


@dataclass(frozen=True, slots=True)
class Tokens:
    """One grant's pair. A refresh rotates both and kills the old pair. `expires_at` is 0 when
    cTrader named no lifetime, and such a pair is never due on time alone."""

    access_token: str = field(repr=False)
    refresh_token: str = field(repr=False)
    expires_at: float

    def due(self, now: float) -> bool:
        return 0 < self.expires_at <= now

    def document(self) -> str:
        return json.dumps(
            {
                "accessToken": self.access_token,
                "refreshToken": self.refresh_token,
                "expiresAt": self.expires_at,
            },
            sort_keys=True,
        )

    @classmethod
    def from_document(cls, raw: str) -> Tokens:
        value = cast("dict[str, object]", json.loads(raw))
        return cls(
            str(value["accessToken"]),
            str(value["refreshToken"]),
            float(cast(float, value["expiresAt"])),
        )


type Fetch = Callable[[str, str], tuple[int, bytes]]
"""`(method, url)` to `(status, body)`. A test injects a fake token endpoint here."""


def urllib_fetch(method: str, url: str) -> tuple[int, bytes]:
    """One call to the token endpoint. A URL that is not http or https with a host is refused as
    `token_url_invalid` before anything is sent; urllib's own errors would quote the URL, whose
    query holds the client secret and the refresh token."""
    invalid = OAuthRefused(
        "token_url_invalid", "the [ctrader] token_url in Settings is not a web address"
    )
    try:
        parts = urlsplit(url)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise invalid
        request = urllib.request.Request(  # noqa: S310 - the token endpoint Settings names
            url, method=method, headers={"Accept": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=CALL_TIMEOUT_S) as answer:  # noqa: S310
            return int(answer.status), answer.read()
    except urllib.error.HTTPError as error:
        return int(error.code), error.read()
    except OSError as error:
        raise OAuthRefused("token_endpoint_unreachable", type(error).__name__) from None
    except ValueError:
        raise invalid from None


def consent_url(app: AppCredential, redirect: Redirect, *, base: str = CONSENT_URL) -> str:
    """cTrader's consent page for the read app: its client id, the redirect, scope `accounts`."""
    query = urlencode(
        {"client_id": app.client_id, "redirect_uri": redirect.url, "scope": SCOPE, "product": "web"}
    )
    return f"{base}?{query}"


def _token_call(
    params: dict[str, str], method: str, token_url: str, fetch: Fetch, now: float
) -> Tokens:
    status, body = fetch(method, f"{token_url}?{urlencode(params)}")
    try:
        answer = cast("dict[str, object]", json.loads(body or b"{}"))
    except ValueError:
        raise OAuthRefused("bad_token_answer", f"HTTP {status}, not JSON") from None
    error = answer.get("errorCode")
    if error:
        raise OAuthRefused(str(error), str(answer.get("description") or ""))
    access, refresh = answer.get("accessToken"), answer.get("refreshToken")
    if status != 200 or not isinstance(access, str) or not isinstance(refresh, str):
        raise OAuthRefused("bad_token_answer", f"HTTP {status} without a token pair")
    expires = answer.get("expiresIn")
    if isinstance(expires, bool) or not isinstance(expires, int) or expires <= 0:
        return Tokens(access, refresh, 0.0)
    return Tokens(access, refresh, now + expires)


def exchange_code(
    app: AppCredential,
    code: str,
    redirect: Redirect,
    *,
    token_url: str = TOKEN_URL,
    fetch: Fetch = urllib_fetch,
    now: float | None = None,
) -> Tokens:
    """The one-minute code for the grant's pair, on the home."""
    params = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect.url,
        "client_id": app.client_id,
        "client_secret": app.client_secret,
    }
    return _token_call(params, "GET", token_url, fetch, time.time() if now is None else now)


def refresh_tokens(
    app: AppCredential,
    refresh_token: str,
    *,
    token_url: str = TOKEN_URL,
    fetch: Fetch = urllib_fetch,
    now: float | None = None,
) -> Tokens:
    """A new pair for the grant's refresh token; the old pair dies at cTrader."""
    params = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": app.client_id,
        "client_secret": app.client_secret,
    }
    return _token_call(params, "POST", token_url, fetch, time.time() if now is None else now)


@dataclass(frozen=True, slots=True)
class Forwarded:
    """What the home answered for the code, or why the receiver stopped without one."""

    word: Literal["ok", "refused"]
    code: str = ""
    message: str = ""


type Forward = Callable[[str], Forwarded]


class _Once(HTTPServer):
    allow_reuse_address = False
    """A port another program holds must refuse here, before the browser opens."""

    def __init__(self, redirect: Redirect, forward: Forward) -> None:
        self.redirect = redirect
        self.forward = forward
        self.result: Forwarded | None = None
        family = socket.AF_INET6 if ":" in redirect.host else socket.AF_INET
        self.address_family = family
        super().__init__((redirect.host, redirect.port), _Handler)

    @override
    def server_bind(self) -> None:
        if os.name == "nt":
            # Windows lets a second socket share a bound port unless the first claims it alone.
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class _Handler(BaseHTTPRequestHandler):
    server: _Once  # pyright: ignore[reportIncompatibleVariableOverride]

    @override
    def log_message(self, format: str, *args: object) -> None:
        """The request line holds the code; nothing is logged."""

    def do_GET(self) -> None:
        parts = urlsplit(self.path)
        if parts.path != self.server.redirect.path:
            self._page(404, "Not the sign-in address.")
            return
        query = parse_qs(parts.query)
        code = (query.get("code") or [""])[0]
        if not code:
            declined = (query.get("error") or ["no code"])[0]
            self.server.result = Forwarded("refused", "consent_declined", declined)
            self._page(400, "cTrader sent no sign-in code. You can close this tab.")
            return
        try:
            result = self.server.forward(code)
        except Exception as error:  # the forward crosses the network; its failure is the answer
            result = Forwarded("refused", "home_unreachable", type(error).__name__)
        del code
        self.server.result = result
        if result.word == "ok":
            self._page(200, "Signed in. QMX has it. You can close this tab.")
        else:
            self._page(400, f"The sign-in did not finish: {result.message or result.code}.")

    def _page(self, status: int, text: str) -> None:
        body = f"<!doctype html><title>QMX</title><p>{text}</p>".encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


class Receiver:
    """The PC's one-shot loopback receiver on the registered redirect.

    `open` binds the port or raises `PortBusy`, so the caller opens the browser only after it
    holds the port. `wait` serves until one redirect arrives or the deadline passes, then stops
    listening either way.
    """

    def __init__(self, server: _Once) -> None:
        self._server = server

    @classmethod
    def open(cls, redirect: Redirect, forward: Forward) -> Receiver:
        try:
            return cls(_Once(redirect, forward))
        except OSError:
            raise PortBusy(
                "port_busy", f"port {redirect.port} is in use; close what holds it and retry"
            ) from None

    def wait(self, *, deadline: float, clock: Callable[[], float] = time.monotonic) -> Forwarded:
        try:
            while self._server.result is None:
                left = deadline - clock()
                if left <= 0:
                    return Forwarded(
                        "refused", "sign_in_expired", "no code came back in 10 minutes"
                    )
                self._server.timeout = min(left, 0.5)
                self._server.handle_request()
            return self._server.result
        finally:
            self.close()

    def close(self) -> None:
        self._server.server_close()
