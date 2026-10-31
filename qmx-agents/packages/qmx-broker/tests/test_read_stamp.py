"""Every broker read says demo or live (MD2, audit M5, ruling 135).

Sessions are the recorded cTrader fixture and a fake CCXT exchange; keys sit in an in-memory
keyring or a fake vault. Nothing here reaches cTrader, an exchange or Credential Manager.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, ClassVar, cast

import ccxt  # pyright: ignore[reportMissingTypeStubs] - untyped upstream
import pytest
from fastmcp import Client
from qmf.venue.proto import CompiledProto
from test_broker import CTraderFixture, ExchangeFixture, proposal
from test_pc_home import PAIR, Memory, Session, settings, signed_in, vault

from qmx_broker.adapters import Document, EnvironmentMismatch, ReadAdapter
from qmx_broker.models import Account, Broker, BrokerSettings, Connection
from qmx_broker.server import create_server
from qmx_broker.service import BrokerService, open_adapter

__all__ = ["vault"]

BALANCES = {
    "balances": {
        "free": {"BTC": 1, "USDT": 100},
        "used": {"BTC": 0},
        "total": {"BTC": 1, "USDT": 100, "ZERO": 0},
    },
    "timestamp_ms": 1700000000000,
    "market_type": "spot",
}


def ctrader_service(tmp_path: Path, recorded: CTraderFixture) -> BrokerService:
    async def connect(_proto: CompiledProto, environment: str) -> Session:
        assert environment == "demo"
        return Session(recorded)

    def factory(broker: Broker, connection: Connection, account: Account):
        return open_adapter(broker, connection, account, connect=connect)

    return BrokerService(tmp_path, settings(), factory)


def crypto(environment: str, exchange: str = "binance") -> dict[str, Any]:
    return {
        "connections": [
            {
                "id": "crypto",
                "name": "Crypto",
                "adapter": "ccxt",
                "exchange": exchange,
                "connections": [
                    {
                        "id": "main",
                        "credential_ref": "qmx/crypto",
                        "environment": environment,
                        "accounts": [
                            {"id": "spot", "currency": "USDT", "permissions": ["read", "propose"]}
                        ],
                    }
                ],
            }
        ]
    }


class SandboxedExchange(ExchangeFixture):
    """A fake CCXT exchange whose sandbox flag moves the way CCXT's own `set_sandbox_mode` does."""

    built: ClassVar[list[SandboxedExchange]] = []

    def __init__(self, config: Document) -> None:
        super().__init__()
        self.isSandboxModeEnabled = False
        SandboxedExchange.built.append(self)

    def set_sandbox_mode(self, enabled: bool) -> None:
        self.isSandboxModeEnabled = enabled


@pytest.fixture
def exchange(monkeypatch: pytest.MonkeyPatch) -> list[SandboxedExchange]:
    def fake_vault(reference: str) -> dict[str, str]:
        assert reference == "qmx/crypto"
        return {"apiKey": "fixture", "secret": "fixture"}

    SandboxedExchange.built = []

    def has_demo_mode(_exchange: str) -> None:
        return None

    monkeypatch.setattr("qmx_broker.service.demo_refusal", has_demo_mode)
    monkeypatch.setattr("qmx_broker.service.credentials", fake_vault)
    monkeypatch.setattr(ccxt, "binance", SandboxedExchange)
    return SandboxedExchange.built


def test_a_demo_ctrader_account_state_through_the_broker_door_says_demo(
    tmp_path: Path, vault: Memory
) -> None:
    signed_in(vault)
    service = ctrader_service(tmp_path, CTraderFixture())

    async def run() -> Any:
        async with Client(create_server(service)) as client:
            scope = {"broker_id": "ctrader", "connection_id": "demo", "account_id": "101"}
            return (await client.call_tool("account_state", scope)).structured_content

    assert asyncio.run(run()) == {
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


def test_a_ccxt_sandbox_read_says_demo_and_a_live_read_says_live(
    tmp_path: Path, exchange: list[SandboxedExchange]
) -> None:
    for environment, is_live in (("demo", False), ("live", True)):
        service = BrokerService(tmp_path, BrokerSettings.model_validate(crypto(environment)))
        assert asyncio.run(service.read("account_state", "crypto", "main", "spot")) == {
            "environment": environment,
            "is_live": is_live,
            "connection_id": "main",
            "account_id": "spot",
            "result": BALANCES,
        }
    assert [built.isSandboxModeEnabled for built in exchange] == [True, False]


def test_a_switch_between_two_reads_stamps_each_and_never_reuses_the_demo_exchange(
    tmp_path: Path, exchange: list[SandboxedExchange]
) -> None:
    current = {"environment": "demo"}
    service = BrokerService(tmp_path, brokers=lambda: crypto(current["environment"]))

    def stamp(operation: str, **values: Any) -> tuple[str, bool, object]:
        read = asyncio.run(service.read(operation, "crypto", "main", "spot", **values))
        return read["environment"], read["is_live"], read["result"]

    assert stamp("positions")[:2] == ("demo", False)
    current["environment"] = "live"
    assert stamp("positions") == (
        "live",
        True,
        [
            {"asset": "BTC", "quantity": "1", "market_type": "spot"},
            {"asset": "USDT", "quantity": "100", "market_type": "spot"},
        ],
    )
    current["environment"] = "demo"
    assert stamp("quotes", symbol="BTC/USDT")[:2] == ("demo", False)
    assert [built.isSandboxModeEnabled for built in exchange] == [True, False]


def test_a_ctrader_is_live_that_disagrees_with_the_connection_fails_the_read_by_name(
    tmp_path: Path, vault: Memory
) -> None:
    signed_in(vault)
    recorded = CTraderFixture()
    listing = recorded.payload["ProtoOAGetAccountListByAccessTokenReq"]
    listing["ctidTraderAccount"][0]["isLive"] = True

    with pytest.raises(EnvironmentMismatch) as refused:
        asyncio.run(
            ctrader_service(tmp_path, recorded).read("account_state", "ctrader", "demo", "101")
        )

    assert str(refused.value) == (
        "environment_mismatch: connection demo says demo, but its broker session proved a live"
        " account, so nothing was read. Check this connection in Settings"
    )
    assert "environment before" not in str(refused.value)
    assert "ProtoOAAccountAuthReq" not in [name for name, _ in recorded.calls]
    assert vault.get_password("qmx/token/ctrader-app", "token/ctrader-app") == PAIR


@pytest.mark.parametrize(
    ("proven", "found"),
    [(True, "proved a live account"), (None, "proved neither demo nor live")],
)
def test_a_session_that_proves_another_kind_or_none_fails_before_it_reads(
    tmp_path: Path, proven: bool | None, found: str
) -> None:
    reads: list[str] = []

    class Unproven:
        bar_page_limit = None
        is_live = proven

        async def account_state(self) -> Document:
            reads.append("account_state")
            return {}

    @asynccontextmanager
    async def factory(
        broker: Broker, connection: Connection, account: Account
    ) -> AsyncGenerator[ReadAdapter]:
        yield Unproven()  # pyright: ignore[reportReturnType] - a partial fake adapter

    service = BrokerService(tmp_path, BrokerSettings.model_validate(crypto("demo")), factory)
    with pytest.raises(
        EnvironmentMismatch,
        match=f"connection main says demo, but its broker session {found}, so nothing was read",
    ):
        asyncio.run(service.read("account_state", "crypto", "main", "spot"))
    assert reads == []


@pytest.mark.parametrize(("environment", "is_live"), [("demo", False), ("live", True)])
def test_a_real_bitget_connection_reads_under_its_own_kind_without_the_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, environment: str, is_live: bool
) -> None:
    def fake_vault(reference: str) -> dict[str, str]:
        return {"apiKey": "fixture", "secret": "fixture"}

    def no_network(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("this test must not reach Bitget")

    @asynccontextmanager
    async def factory(
        broker: Broker, connection: Connection, account: Account
    ) -> AsyncGenerator[ReadAdapter]:
        async with open_adapter(broker, connection, account) as adapter:
            exchange: Any = cast(Any, adapter).exchange
            exchange.fetch = no_network
            exchange.fetch_balance = ExchangeFixture().fetch_balance
            assert type(exchange) is ccxt.bitget
            yield adapter

    monkeypatch.setattr("qmx_broker.service.credentials", fake_vault)
    settings = BrokerSettings.model_validate(crypto(environment, "bitget"))
    read = asyncio.run(
        BrokerService(tmp_path, settings, factory).read("account_state", "crypto", "main", "spot")
    )
    assert (read["environment"], read["is_live"], read["result"]) == (
        environment,
        is_live,
        BALANCES,
    )


def test_an_order_re_proposed_after_a_switch_gets_a_new_proposal_id(tmp_path: Path) -> None:
    current = {"environment": "demo"}
    service = BrokerService(tmp_path, brokers=lambda: crypto(current["environment"]))
    order = proposal(broker_id="crypto", connection_id="main", account_id="spot", symbol="BTC/USDT")

    first = service.propose_order(order)
    current["environment"] = "live"
    second = service.propose_order(order)

    assert first["proposal_id"] != second["proposal_id"]
    assert [row["proposal"]["environment"] for row in service.proposals()] == ["demo", "live"]
