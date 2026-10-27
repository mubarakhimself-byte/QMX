"""cTrader's sign-in pieces: the PC's loopback receiver, the code exchange, the app copy, and a
keyless provider's walk (engine AD-67, seam B of file 60)."""

from __future__ import annotations

import json
import socket
import threading
import urllib.request
from dataclasses import dataclass
from urllib.parse import parse_qs, urlsplit

import pytest
from keyring.errors import PasswordDeleteError
from pydantic import ValidationError

from qmx_broker.credentials import (
    CTRADER_APP,
    CTRADER_CLIENT_ID,
    CTRADER_CLIENT_SECRET,
    Joined,
    join_ctrader_app,
)
from qmx_broker.models import Broker, BrokerSettings, Connection
from qmx_broker.oauth import (
    AppCredential,
    Forwarded,
    OAuthRefused,
    PortBusy,
    Receiver,
    Redirect,
    Tokens,
    exchange_code,
)
from qmx_broker.registry import ProbeResult, Reading, walk

APP = AppCredential("4242_demo", "app-pass")


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def redirect() -> Redirect:
    return Redirect.parse(f"http://127.0.0.1:{free_port()}/ctrader/callback")


def test_the_receiver_forwards_one_code_answers_the_browser_and_stops() -> None:
    aim = redirect()
    forwarded: list[str] = []

    def forward(code: str) -> Forwarded:
        forwarded.append(code)
        return Forwarded("ok")

    receiver = Receiver.open(aim, forward)
    result: list[Forwarded] = []
    waiting = threading.Thread(target=lambda: result.append(receiver.wait(deadline=1e12)))
    waiting.start()
    with urllib.request.urlopen(f"{aim.url}?code=one-minute-code", timeout=5) as page:  # noqa: S310
        body = page.read().decode()
    waiting.join(5)

    assert forwarded == ["one-minute-code"]
    assert result == [Forwarded("ok")]
    assert "Signed in" in body
    with socket.socket() as again:
        again.bind(("127.0.0.1", aim.port))


def test_a_busy_port_refuses_before_anything_listens() -> None:
    aim = redirect()
    with socket.socket() as holder:
        holder.bind(("127.0.0.1", aim.port))
        holder.listen()
        with pytest.raises(PortBusy) as refused:
            Receiver.open(aim, lambda _code: Forwarded("ok"))
    assert refused.value.code == "port_busy"


def test_a_receiver_with_no_code_in_ten_minutes_stops_with_a_named_refusal() -> None:
    receiver = Receiver.open(redirect(), lambda _code: Forwarded("ok"))
    ticks = iter([0.0, 601.0])
    assert receiver.wait(deadline=600.0, clock=lambda: next(ticks)) == Forwarded(
        "refused", "sign_in_expired", "no code came back in 10 minutes"
    )


def test_the_exchange_sends_the_code_and_returns_the_pair() -> None:
    asked: list[tuple[str, dict[str, list[str]]]] = []

    def endpoint(method: str, url: str) -> tuple[int, bytes]:
        asked.append((method, parse_qs(urlsplit(url).query)))
        answer = {"accessToken": "acc-1", "refreshToken": "ref-1", "expiresIn": 2628000}
        return 200, json.dumps(answer | {"errorCode": None}).encode()

    aim = Redirect.parse("http://127.0.0.1:47613/ctrader/callback")
    tokens = exchange_code(
        APP, "c0de", aim, token_url="http://fake/apps/token", fetch=endpoint, now=10.0
    )

    assert tokens == Tokens("acc-1", "ref-1", 2628010.0)
    assert asked == [
        (
            "GET",
            {
                "grant_type": ["authorization_code"],
                "code": ["c0de"],
                "redirect_uri": ["http://127.0.0.1:47613/ctrader/callback"],
                "client_id": ["4242_demo"],
                "client_secret": ["app-pass"],
            },
        )
    ]
    assert "acc-1" not in repr(tokens) and "app-pass" not in repr(APP)


def test_a_refused_exchange_names_cTraders_code_and_never_the_request() -> None:
    def endpoint(_method: str, _url: str) -> tuple[int, bytes]:
        return 400, b'{"errorCode": "ACCESS_DENIED", "description": "code expired"}'

    aim = Redirect.parse("http://127.0.0.1:47613/ctrader/callback")
    with pytest.raises(OAuthRefused) as refused:
        exchange_code(APP, "c0de", aim, token_url="http://fake/apps/token", fetch=endpoint)
    assert (refused.value.code, str(refused.value)) == (
        "ACCESS_DENIED",
        "ACCESS_DENIED: code expired",
    )


@dataclass
class Held:
    password: str


class Keyring:
    """Credential Manager as WinVault keys it: by target name, with whatever user name."""

    def __init__(self, entries: dict[str, tuple[str, str]]) -> None:
        self.entries = entries

    def get_credential(self, service: str, username: str | None) -> Held | None:
        found = self.entries.get(service)
        return None if found is None else Held(found[1])

    def get_password(self, service: str, username: str) -> str | None:
        found = self.entries.get(service)
        return found[1] if found is not None and found[0] == username else None

    def set_password(self, service: str, username: str, password: str) -> None:
        self.entries[service] = (username, password)

    def delete_password(self, service: str, username: str) -> None:
        if self.entries.pop(service, None) is None:
            raise PasswordDeleteError(service)


def test_the_app_copy_joins_his_two_entries_once_and_keeps_them() -> None:
    vault = Keyring(
        {
            CTRADER_CLIENT_ID: ("Mubarak", " 4242_demo "),
            CTRADER_CLIENT_SECRET: ("ctrader", "app-pass"),
        }
    )

    first, second = join_ctrader_app(vault), join_ctrader_app(vault)

    assert (first, second) == (Joined("ok", True), Joined("ok", False))
    assert vault.entries[CTRADER_APP] == (
        "read/ctrader-app",
        '{"clientId": "4242_demo", "clientSecret": "app-pass"}',
    )
    assert vault.entries[CTRADER_CLIENT_ID] == ("Mubarak", " 4242_demo ")
    assert vault.entries[CTRADER_CLIENT_SECRET] == ("ctrader", "app-pass")
    vault.entries[CTRADER_CLIENT_SECRET] = ("ctrader", "new-pass")
    assert join_ctrader_app(vault) == Joined("ok", True)
    assert join_ctrader_app(Keyring({})) == Joined(
        "needs_you", False, "qmx/ctrader-client-id is not in Credential Manager"
    )


def test_keyless_settings_rows_validate_with_no_reference_and_walk_as_ok() -> None:
    def answered(_provider: Broker, _connection: Connection) -> ProbeResult:
        return ProbeResult(latency_ms=12)

    saved = BrokerSettings.model_validate(
        {
            "connections": [
                {
                    "id": "dukascopy",
                    "name": "Dukascopy",
                    "adapter": "dukascopy",
                    "kind": "data",
                    "connections": [{"id": "duka", "home": "pc"}],
                },
                {
                    "id": "binance-vision",
                    "name": "Binance public files",
                    "adapter": "binance-vision",
                    "kind": "data",
                    "connections": [{"id": "vision", "credential_ref": "", "home": "contabo"}],
                },
            ]
        }
    )

    readings = [
        walk(provider, connection, probe=answered, now=0.0)
        for provider in saved.providers
        for connection in provider.connections
    ]
    assert readings == [
        Reading("duka", "healthy", "ok", latency_ms=12),
        Reading("vision", "healthy", "ok", latency_ms=12),
    ]


def test_a_keyed_provider_still_refuses_an_empty_reference() -> None:
    for adapter in ("databento", "ctrader", "no-such-adapter"):
        with pytest.raises(ValidationError) as refused:
            Broker.model_validate(
                {
                    "id": adapter,
                    "name": adapter,
                    "adapter": adapter,
                    "connections": [{"id": "one", "home": "pc"}],
                }
            )
        assert (
            f"A {adapter} connection needs a qmx/* credential_ref; only a provider with no "
            "sign-in may leave it empty"
        ) in str(refused.value)
    with pytest.raises(ValidationError):
        Connection.model_validate({"id": "one", "credential_ref": "plain-name"})


def test_a_redirect_off_the_loopback_is_refused() -> None:
    with pytest.raises(OAuthRefused) as refused:
        Redirect.parse("https://example.com/callback")
    assert refused.value.code == "redirect_not_loopback"
