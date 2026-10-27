"""cTrader reads on This PC as the connection's home (design 62 E1, engine AD-67, ruling 135).

The app half and the pair live in an in-memory keyring backend, and the session is a recorded
cTrader fixture. Nothing here reaches cTrader or the real Credential Manager.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Iterator
from pathlib import Path
from typing import override

import keyring
import pytest
from keyring.backend import KeyringBackend
from keyring.credentials import Credential, SimpleCredential
from keyring.errors import PasswordDeleteError
from qmf.venue.proto import CompiledProto
from test_broker import CTraderFixture

from qmx_broker.adapters import can_trade_live
from qmx_broker.credentials import CredentialManager, Joined, join_ctrader_app
from qmx_broker.models import Account, Broker, BrokerSettings, Connection, ReadEnvelope
from qmx_broker.oauth import AppCredential
from qmx_broker.service import BrokerService, ReadRefused, grant_accounts, open_adapter

PAIR = json.dumps({"accessToken": "acc-1", "refreshToken": "ref-1", "expiresAt": 4_000_000_000.0})
"""A pair that is not due until 2096, so these reads never refresh it."""


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


def signed_in(vault: Memory) -> None:
    app = json.dumps({"clientId": "4242_demo", "clientSecret": "app-pass"})
    vault.held["qmx/read/ctrader-app", "read/ctrader-app"] = app
    vault.held["qmx/token/ctrader-app", "token/ctrader-app"] = PAIR


def settings(home: str = "pc") -> BrokerSettings:
    connection = Connection(
        id="demo",
        credential_ref="qmx/read/ctrader-app",
        home=home,
        accounts=[Account(id="101", currency="USD")],
    )
    return BrokerSettings(
        connections=[
            Broker(id="ctrader", name="cTrader", adapter="ctrader", connections=[connection])
        ]
    )


class Session:
    def __init__(self, recorded: CTraderFixture) -> None:
        self.request = recorded.request
        self.spot = recorded.request
        self.closed = False

    async def close(self) -> None:
        self.closed = True


def service(tmp_path: Path, recorded: CTraderFixture, home: str = "pc") -> BrokerService:
    async def connect(_proto: CompiledProto, environment: str) -> Session:
        assert environment == "demo"
        return Session(recorded)

    def factory(broker: Broker, connection: Connection, account: Account):
        return open_adapter(broker, connection, account, connect=connect)

    return BrokerService(tmp_path, settings(home), factory)


def read(broker: BrokerService) -> ReadEnvelope:
    return asyncio.run(broker.read("account_state", "ctrader", "demo", "101"))


def test_a_pc_homed_read_opens_its_session_with_this_pcs_pair(
    tmp_path: Path, vault: Memory
) -> None:
    signed_in(vault)
    recorded = CTraderFixture()

    assert read(service(tmp_path, recorded)) == {
        "environment": "demo",
        "is_live": False,
        "connection_id": "demo",
        "account_id": "101",
        "result": {
            "account_id": "101",
            "currency": "USD",
            "balance": "1234.56",
            "leverage": "50.00",
        },
    }
    assert recorded.calls[:3] == [
        ("ProtoOAApplicationAuthReq", {"clientId": "4242_demo", "clientSecret": "app-pass"}),
        ("ProtoOAGetAccountListByAccessTokenReq", {"accessToken": "acc-1"}),
        ("ProtoOAAccountAuthReq", {"ctidTraderAccountId": 101, "accessToken": "acc-1"}),
    ]


def test_a_grant_that_can_trade_live_money_is_refused_by_name_and_its_pair_deleted(
    tmp_path: Path, vault: Memory
) -> None:
    signed_in(vault)
    recorded = CTraderFixture()
    recorded.payload["ProtoOAGetAccountListByAccessTokenReq"]["permissionScope"] = "SCOPE_TRADE"

    with pytest.raises(ValueError, match="live") as refused:
        read(service(tmp_path, recorded))

    assert str(refused.value) == (
        "live_trading_grant: this sign-in can trade live money; it belongs on a trading server. "
        "Sign in again with view-only access, or tick demo accounts only"
    )
    assert vault.get_password("qmx/token/ctrader-app", "token/ctrader-app") is None
    assert "ProtoOAAccountAuthReq" not in [name for name, _ in recorded.calls]


def test_only_a_trading_scope_over_a_live_account_counts_as_able_to_trade_live() -> None:
    demo = {"ctidTraderAccountId": "101", "isLive": False}
    live = {"ctidTraderAccountId": "202", "isLive": True}

    assert can_trade_live({"permissionScope": "SCOPE_VIEW", "ctidTraderAccount": [demo, live]}) is (
        False
    )
    assert can_trade_live({"permissionScope": "SCOPE_TRADE", "ctidTraderAccount": [demo]}) is False
    assert can_trade_live({"permissionScope": "SCOPE_TRADE", "ctidTraderAccount": [live]}) is True
    assert can_trade_live({"ctidTraderAccount": [live]}) is True


def test_a_connection_signed_in_on_a_place_opens_no_session_here(
    tmp_path: Path, vault: Memory
) -> None:
    signed_in(vault)
    recorded = CTraderFixture()

    with pytest.raises(ReadRefused) as refused:
        read(service(tmp_path, recorded, home="contabo"))

    assert (refused.value.code, str(refused.value)) == (
        "signed_in_elsewhere",
        "demo is signed in on contabo, so This PC opens no session for it; read it from "
        "contabo, or sign in to cTrader on This PC",
    )
    assert recorded.calls == []
    assert vault.get_password("qmx/token/ctrader-app", "token/ctrader-app") == PAIR


def test_a_fresh_grants_account_list_is_read_over_one_session_that_closes() -> None:
    recorded = CTraderFixture()
    sessions: list[Session] = []

    async def connect(_proto: CompiledProto, environment: str) -> Session:
        assert environment == "demo"
        sessions.append(Session(recorded))
        return sessions[-1]

    connection = settings().providers[0].connections[0]
    listing = asyncio.run(
        grant_accounts(connection, AppCredential("4242_demo", "app-pass"), "acc-1", connect=connect)
    )

    assert listing["permissionScope"] == "SCOPE_VIEW"
    assert listing["ctidTraderAccount"] == [
        {"ctidTraderAccountId": "101", "isLive": False},
        {"ctidTraderAccountId": "202", "isLive": True},
    ]
    assert recorded.calls == [
        ("ProtoOAApplicationAuthReq", {"clientId": "4242_demo", "clientSecret": "app-pass"}),
        ("ProtoOAGetAccountListByAccessTokenReq", {"accessToken": "acc-1"}),
    ]
    assert [session.closed for session in sessions] == [True]


class WinVault:
    """keyring's Windows backend: an overwrite first re-saves the old value under the compound
    target `<old user>@<service>`, and a delete removes both targets held by that user."""

    def __init__(self) -> None:
        self.held: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.held.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        for (held_service, user), old in list(self.held.items()):
            if held_service == service:
                self.held[f"{user}@{service}", user] = old
        self.held[service, username] = password

    def delete_password(self, service: str, username: str) -> None:
        targets = [(service, username), (f"{username}@{service}", username)]
        if not [self.held.pop(target) for target in targets if target in self.held]:
            raise PasswordDeleteError(service)


def test_a_second_sign_in_on_windows_leaves_one_pair_and_a_delete_leaves_none() -> None:
    windows = WinVault()
    keys = CredentialManager(windows)

    keys.replace("qmx/token/ctrader-app", "first pair")
    keys.replace("qmx/token/ctrader-app", "second pair")
    kept = dict(windows.held)
    windows.held["token/ctrader-app@qmx/token/ctrader-app", "token/ctrader-app"] = "stale pair"
    keys.delete("qmx/token/ctrader-app")

    assert kept == {("qmx/token/ctrader-app", "token/ctrader-app"): "second pair"}
    assert windows.held == {}


class TypedVault(WinVault):
    """WinVault holding his two typed entries, which the join reads by target name."""

    def get_credential(self, service: str, username: str | None) -> Credential | None:
        for (held_service, user), password in self.held.items():
            if held_service == service and username in (None, user):
                return SimpleCredential(user, password)
        return None


def test_a_changed_app_secret_on_windows_leaves_one_app_copy_and_no_companion() -> None:
    windows = TypedVault()
    windows.held["qmx/ctrader-client-id", "anything"] = "4242_demo"
    windows.held["qmx/ctrader-client-secret", "anything"] = "app-pass"
    typed = dict(windows.held)
    app = ("qmx/read/ctrader-app", "read/ctrader-app")
    companion = ("read/ctrader-app@qmx/read/ctrader-app", "read/ctrader-app")

    first = join_ctrader_app(windows)
    windows.held["qmx/ctrader-client-secret", "anything"] = "new-pass"
    changed = join_ctrader_app(windows)
    after_change = dict(windows.held)
    windows.held[companion] = "a stale pair from an older QMX"
    matched = join_ctrader_app(windows)

    assert (first, changed, matched) == (
        Joined("ok", True),
        Joined("ok", True),
        Joined("ok", False),
    )
    assert after_change == {
        **typed,
        ("qmx/ctrader-client-secret", "anything"): "new-pass",
        app: '{"clientId": "4242_demo", "clientSecret": "new-pass"}',
    }
    assert windows.held == after_change
