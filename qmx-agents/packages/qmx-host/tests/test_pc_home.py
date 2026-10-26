"""The cTrader sign-in with This PC as the app's home, and a move of that home to a place
(design 62 E1, engine AD-67). Credential Manager is an in-memory keyring backend, the token
endpoint is a fake, and nothing here reaches cTrader."""

from __future__ import annotations

import urllib.error
import urllib.request
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, override
from urllib.parse import parse_qs, urlsplit

import keyring
import pytest
from fastapi.testclient import TestClient
from keyring.backend import KeyringBackend
from keyring.credentials import Credential, SimpleCredential
from keyring.errors import PasswordDeleteError
from qmx_broker.credentials import CredentialManager, Joined
from qmx_broker.oauth import AppCredential, Redirect, Tokens
from test_venue_session import NOW, PAIRING, free_redirect, home_app, the_home, to, token_endpoint

from qmx_host.venue_session import (
    HomeKeyStore,
    HomeSignIn,
    PcSignIn,
    Refused,
    Target,
    pc_app,
    target,
)

TOKENS = ("qmx/token/ctrader-app", "token/ctrader-app")
ROW: dict[str, Any] = {
    "id": "ctrader",
    "name": "cTrader",
    "adapter": "ctrader",
    "kind": "platform",
    "connections": [{"id": "demo", "credential_ref": "qmx/read/ctrader-app"}],
}
"""A row that names no home, so its home is This PC."""


class Memory(KeyringBackend):
    priority = 1  # pyright: ignore[reportAssignmentType, reportIncompatibleMethodOverride]

    def __init__(self) -> None:
        super().__init__()
        self.held: dict[tuple[str, str], str] = {}

    @override
    def get_password(self, service: str, username: str) -> str | None:
        return self.held.get((service, username))

    @override
    def set_password(self, service: str, username: str, password: str) -> None:
        self.held[service, username] = password

    @override
    def delete_password(self, service: str, username: str) -> None:
        if self.held.pop((service, username), None) is None:
            raise PasswordDeleteError(service)

    @override
    def get_credential(self, service: str, username: str | None) -> Credential | None:
        for (held_service, user), password in self.held.items():
            if held_service == service and username in (None, user):
                return SimpleCredential(user, password)
        return None


@pytest.fixture
def vault() -> Iterator[Memory]:
    before = keyring.get_keyring()
    memory = Memory()
    keyring.set_keyring(memory)
    try:
        yield memory
    finally:
        keyring.set_keyring(before)


def this_pc() -> HomeSignIn:
    keys = CredentialManager()
    return HomeSignIn(
        name=lambda: "pc",
        key=lambda: None,
        app=lambda: pc_app(keys),
        keys=keys,
        fetch=token_endpoint,
        clock=lambda: NOW,
    )


def consents(aim: Redirect, opened: list[str]) -> Any:
    def browser(url: str) -> None:
        opened.append(url)
        with urllib.request.urlopen(f"{aim.url}?code=one-minute-code", timeout=10) as page:  # noqa: S310
            assert "Signed in" in page.read().decode()

    return browser


def refused_in_browser(aim: Redirect) -> Any:
    def browser(_url: str) -> None:
        with pytest.raises(urllib.error.HTTPError) as page:
            urllib.request.urlopen(f"{aim.url}?code=one-minute-code", timeout=10)  # noqa: S310
        assert "did not finish" in page.value.read().decode()

    return browser


def no_server(_url: str, _body: Mapping[str, Any], _headers: Mapping[str, str]) -> Any:
    raise AssertionError("a PC-homed sign-in asks no server")


def test_with_no_server_this_pc_signs_in_and_keeps_the_pair_once_in_credential_manager(
    vault: Memory,
) -> None:
    vault.held["qmx/ctrader-client-id", "anything"] = "4242_demo"
    vault.held["qmx/ctrader-client-secret", "anything"] = "app-pass"
    here = this_pc()
    aim = free_redirect()
    opened: list[str] = []
    pc = PcSignIn(
        name=lambda: "pc",
        key=lambda: None,
        resolve=lambda: target({"redirect": aim.url}, [ROW], {}, this="pc"),
        here=here,
        post=no_server,
        open_browser=consents(aim, opened),
        clock=lambda: NOW,
    )

    started = pc.start()
    pc.join(10)

    assert started == {"state": "waiting", "home": "pc"}
    assert (pc.last["state"], pc.last["home"]) == ("ok", "pc")
    assert parse_qs(urlsplit(opened[0]).query)["client_id"] == ["4242_demo"]
    assert sorted(vault.held) == [
        ("qmx/ctrader-client-id", "anything"),
        ("qmx/ctrader-client-secret", "anything"),
        ("qmx/read/ctrader-app", "read/ctrader-app"),
        TOKENS,
    ]
    assert Tokens.from_document(vault.held[TOKENS]) == Tokens("acc-1", "ref-1", NOW + 2628000)
    with pytest.raises(Refused) as replayed:
        here.exchange("one-minute-code")
    assert replayed.value.code == "no_pending_sign_in"


def test_a_home_named_nowhere_is_this_pc_and_a_place_with_no_url_still_waits() -> None:
    callback = Redirect.parse("http://127.0.0.1:47613/ctrader/callback")
    placed: dict[str, Any] = {
        **ROW,
        "connections": [
            {"id": "demo", "credential_ref": "qmx/read/ctrader-app", "home": "contabo"}
        ],
    }

    with pytest.raises(Refused) as waiting:
        target({}, [placed], {}, this="pc")
    with pytest.raises(Refused) as elsewhere:
        target({}, [ROW], {}, this="contabo")

    assert target({}, [], {}, this="pc") == Target("pc", callback)
    assert target({}, [ROW], {}, this="pc") == Target("pc", callback)
    assert waiting.value.code == "waiting_for_server"
    assert elsewhere.value.code == "pc_is_home"


def test_a_fresh_sign_in_on_a_place_deletes_this_pcs_pair(tmp_path: Path, vault: Memory) -> None:
    vault.held[TOKENS] = "the PC's earlier pair"
    server = HomeKeyStore(tmp_path / "server")
    aim = free_redirect()

    with TestClient(home_app(the_home(server))) as rest:
        pc = PcSignIn(
            name=lambda: "pc",
            key=lambda: PAIRING,
            resolve=lambda: Target("contabo", aim, "http://contabo.tail"),
            here=this_pc(),
            join=lambda: Joined("ok", False),
            post=to(rest),
            open_browser=consents(aim, []),
            clock=lambda: NOW,
        )
        pc.start()
        pc.join(10)

    assert pc.last["state"] == "ok"
    assert server.names() == ("qmx/token/ctrader-app",)
    assert TOKENS not in vault.held


def test_a_refused_sign_in_on_a_place_keeps_this_pcs_pair(tmp_path: Path, vault: Memory) -> None:
    vault.held[TOKENS] = "the PC's earlier pair"
    aim = free_redirect()
    late = HomeSignIn(
        name=lambda: "contabo",
        key=lambda: PAIRING,
        app=lambda: AppCredential("4242_demo", "app-pass"),
        keys=HomeKeyStore(tmp_path / "server"),
        fetch=lambda _method, _url: (400, b'{"errorCode": "ACCESS_DENIED"}'),
        clock=lambda: NOW,
    )

    with TestClient(home_app(late)) as rest:
        pc = PcSignIn(
            name=lambda: "pc",
            key=lambda: PAIRING,
            resolve=lambda: Target("contabo", aim, "http://contabo.tail"),
            here=this_pc(),
            join=lambda: Joined("ok", False),
            post=to(rest),
            open_browser=refused_in_browser(aim),
            clock=lambda: NOW,
        )
        pc.start()
        pc.join(10)

    assert pc.last == {
        "state": "refused",
        "code": "exchange_refused",
        "message": "cTrader answered ACCESS_DENIED",
    }
    assert vault.held[TOKENS] == "the PC's earlier pair"
