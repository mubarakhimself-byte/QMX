"""The sign-in and the refresh check a grant in one order: list its accounts, refuse a grant that
can trade live money, and only then keep the pair (ruling 135). One fake live grant drives both,
and the key store never holds its pair at any write. Nothing reaches cTrader."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from qmf.venue.proto import CompiledProto
from qmx_broker.adapters import LiveGrant
from qmx_broker.credentials import CTRADER_TOKENS
from qmx_broker.models import Account, Broker, BrokerSettings, Connection
from qmx_broker.oauth import AppCredential, Tokens
from qmx_broker.service import BrokerService, grant_accounts, open_adapter
from test_pc_home import Memory, vault
from test_protocol_default import Listing
from test_venue_session import NOW, free_redirect, token_endpoint

from qmx_host.venue_session import HomeSignIn, Refused

__all__ = ["vault"]

APP = AppCredential("4242_demo", "app-pass")
LIVE_GRANT = {
    "permissionScope": "SCOPE_TRADE",
    "ctidTraderAccount": [{"ctidTraderAccountId": "202", "isLive": True}],
}
ROW = Connection(
    id="demo", credential_ref="qmx/read/ctrader-app", accounts=[Account(id="101", currency="USD")]
)


class Store:
    """This PC's key store, recording what it held after every write."""

    def __init__(self, held: dict[str, str]) -> None:
        self.held = held
        self.after_writes: list[dict[str, str]] = []

    def read(self, name: str) -> str | None:
        return self.held.get(name)

    def replace(self, name: str, value: str) -> None:
        self.held[name] = value
        self.after_writes.append(dict(self.held))

    def delete(self, name: str) -> None:
        self.held.pop(name, None)
        self.after_writes.append(dict(self.held))


async def live_grant(_proto: CompiledProto, _environment: str) -> Listing:
    return Listing(LIVE_GRANT, [])


def renewing(method: str, url: str) -> tuple[int, bytes]:
    assert (method, parse_qs(urlsplit(url).query)["grant_type"]) == ("POST", ["refresh_token"])
    pair = {"accessToken": "acc-live", "refreshToken": "ref-live", "expiresIn": 2_628_000}
    return 200, json.dumps(pair).encode()


def test_the_sign_in_and_the_refresh_never_keep_a_live_grants_pair(
    tmp_path: Path, vault: Memory
) -> None:
    signing_store = Store({})
    signing = HomeSignIn(
        name=lambda: "pc",
        pass_keys=dict,
        app=lambda: APP,
        keys=signing_store,
        accounts=lambda app, tokens: asyncio.run(
            grant_accounts(ROW, app, tokens.access_token, connect=live_grant)
        ),
        fetch=token_endpoint,
        clock=lambda: NOW,
    )
    signing.open(free_redirect())
    vault.held["qmx/read/ctrader-app", "read/ctrader-app"] = json.dumps(
        {"clientId": APP.client_id, "clientSecret": APP.client_secret}
    )
    refreshing_store = Store({CTRADER_TOKENS: Tokens("acc-1", "ref-1", NOW - 1).document()})

    def factory(provider: Broker, connection: Connection, account: Account) -> Any:
        return open_adapter(
            provider,
            connection,
            account,
            keys=refreshing_store,
            connect=live_grant,
            folder=tmp_path / "qmx",
            fetch=renewing,
            clock=lambda: NOW,
        )

    rows = BrokerSettings(
        connections=[Broker(id="ctrader", name="cTrader", adapter="ctrader", connections=[ROW])]
    )
    reading = BrokerService(tmp_path / "qmx" / "data", rows, factory)

    with pytest.raises(Refused) as signed:
        signing.exchange("one-minute-code")
    with pytest.raises(LiveGrant):
        asyncio.run(reading.read("account_state", "ctrader", "demo", "101"))

    assert signed.value.code == "live_trading_grant"
    assert (signing_store.after_writes, signing_store.held) == ([], {})
    assert (refreshing_store.after_writes, refreshing_store.held) == ([{}], {})
