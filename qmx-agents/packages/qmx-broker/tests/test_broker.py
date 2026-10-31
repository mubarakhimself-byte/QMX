from __future__ import annotations

import asyncio
import copy
import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

import ccxt  # pyright: ignore[reportMissingTypeStubs] - untyped upstream
import pytest
from fastmcp import Client
from google.protobuf.json_format import MessageToDict, ParseDict
from pydantic import ValidationError
from qmf.venue.proto import CompiledProto
from test_transport import message, protocol

from qmx_broker.adapters import CCXTAdapter, CTraderAdapter, Document, ReadAdapter
from qmx_broker.credentials import credentials
from qmx_broker.ctrader_transport import CTraderTransport
from qmx_broker.models import Account, Broker, BrokerSettings, Connection, OrderProposal
from qmx_broker.server import create_server
from qmx_broker.service import BrokerService, open_adapter

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> Document:
    return cast(Document, json.loads((FIXTURES / name).read_text()))


def settings() -> BrokerSettings:
    return BrokerSettings(
        brokers=[
            Broker(
                id="ic",
                name="IC Markets",
                adapter="ctrader",
                connections=[
                    Connection(
                        id="demo",
                        credential_ref="qmx/ctrader-demo",
                        accounts=[
                            Account(
                                id="101",
                                currency="USD",
                                leverage="50",
                                permissions=["read", "propose"],
                            ),
                            Account(id="303", currency="EUR"),
                        ],
                    )
                ],
            ),
            Broker(
                id="crypto",
                name="Crypto",
                adapter="ccxt",
                exchange="binance",
                connections=[
                    Connection(
                        id="demo",
                        credential_ref="qmx/crypto",
                        accounts=[
                            Account(id="101", currency="USDT", permissions=["read", "propose"])
                        ],
                    )
                ],
            ),
        ]
    )


def proposal(**values: Any) -> OrderProposal:
    return OrderProposal.model_validate(
        {
            "broker_id": "ic",
            "connection_id": "demo",
            "account_id": "101",
            "symbol": "EURUSD",
            "side": "buy",
            "quantity": "100",
            **values,
        }
    )


class CTraderFixture:
    def __init__(self) -> None:
        self.payload = fixture("ctrader-demo.json")
        self.calls: list[tuple[str, Document]] = []

    async def request(self, name: str, values: Document) -> Document:
        self.calls.append((name, values))
        response_name = (
            "ProtoOASpotEvent"
            if name == "ProtoOASubscribeSpotsReq"
            else name.removesuffix("Req") + "Res"
        )
        response = ParseDict(copy.deepcopy(self.payload[name]), message(protocol(), response_name))
        assert response.IsInitialized()
        return MessageToDict(response, preserving_proto_field_name=True)

    def adapter(self) -> CTraderAdapter:
        return CTraderAdapter(
            settings().brokers[0].connections[0].accounts[0], self.request, self.request
        )


class ExchangeFixture:
    precisionMode = ccxt.TICK_SIZE
    isSandboxModeEnabled = True

    def __init__(self) -> None:
        self.payload = fixture("ccxt-spot.json")
        self.calls: list[tuple[Any, ...]] = []

    def load_markets(self) -> dict[str, Document]:
        return {"BTC/USDT": self.payload["market"]}

    def fetch_balance(self) -> Document:
        return self.payload["balance"]

    def fetch_ticker(self, symbol: str) -> Document:
        self.calls.append(("ticker", symbol))
        return self.payload["ticker"]

    def fetch_ohlcv(self, symbol: str, timeframe: str, since: int, limit: int) -> list[list[Any]]:
        self.calls.append(("bars", symbol, timeframe, since, limit))
        return self.payload["bars"]

    def create_order(self, *args: Any, **kwargs: Any) -> None:
        raise AssertionError("A proposal must never call an exchange order API")


def test_multi_account_model_and_pagination(tmp_path: Path) -> None:
    service = BrokerService(tmp_path, settings())
    accounts = service.list_accounts(limit=2)
    assert accounts["total"] == 3
    assert accounts["accounts"][1]["currency"] == "EUR"
    assert "credential_ref" not in json.dumps(accounts)
    assert service.list_accounts(offset=2)["accounts"][0]["broker_id"] == "crypto"
    assert settings().resolve("ic", "demo", "101")[2].currency == "USD"
    assert settings().resolve("crypto", "demo", "101")[2].currency == "USDT"
    with pytest.raises(ValueError, match="Unknown"):
        settings().resolve("ic", "live", "101")


@pytest.mark.parametrize(
    "change",
    [
        {"credential_ref": "plaintext"},
        {"environment": "paper"},
        {"secret": "never-save"},
        {"accounts": [{"id": "101", "currency": "USD"}, {"id": "101", "currency": "EUR"}]},
    ],
)
def test_invalid_connections(change: Document) -> None:
    with pytest.raises(ValidationError):
        Connection.model_validate({"id": "demo", "credential_ref": "qmx/ctrader", **change})


def test_ccxt_multi_account_requires_separate_key_pairs() -> None:
    body = settings().brokers[1].model_dump()
    body["connections"][0]["accounts"].append({"id": "other", "currency": "USD"})
    with pytest.raises(ValidationError, match="distinct account"):
        Broker.model_validate(body)
    for account in body["connections"][0]["accounts"]:
        account["credential_ref"] = "qmx/crypto-" + account["id"]
    assert len(Broker.model_validate(body).connections[0].accounts) == 2


SIGNED_IN = {"clientId": "fixture", "clientSecret": "fixture", "accessToken": "fixture"}


def test_ctrader_auth_and_reads() -> None:
    recorded = CTraderFixture()
    adapter = recorded.adapter()

    async def run() -> None:
        await adapter.authenticate(
            settings().brokers[0].connections[0],
            {"clientId": "fixture", "clientSecret": "fixture", "accessToken": "fixture"},
        )
        assert [name for name, _ in recorded.calls] == [
            "ProtoOAApplicationAuthReq",
            "ProtoOAGetAccountListByAccessTokenReq",
            "ProtoOAAccountAuthReq",
        ]
        assert (await adapter.account_state())["balance"] == "1234.56"
        assert (await adapter.account_state())["leverage"] == "50.00"
        assert (await adapter.positions())[0]["quantity"] == "125.00"
        assert (await adapter.quotes("EURUSD"))["bid"] == "1.10001"
        bars = await adapter.bars("EURUSD", "1m", 1699999980000, 1700000040000, 10)
        assert bars[0] == {
            "timestamp_ms": 1699999980000,
            "open": "1.10010",
            "high": "1.10020",
            "low": "1.10000",
            "close": "1.10015",
            "volume": "25",
            "volume_unit": "ticks",
        }
        assert recorded.calls[-1][1]["period"] == "M1"
        assert await adapter.bars("EURUSD", "1m", 1700000000000, 1700000040000, 10) == []

    asyncio.run(run())


def test_ctrader_refuses_environment_account_and_money_scale_mismatches() -> None:
    recorded = CTraderFixture()
    recorded.payload["ProtoOAGetAccountListByAccessTokenReq"]["ctidTraderAccount"][0]["isLive"] = (
        True
    )
    with pytest.raises(ValueError, match="environment"):
        asyncio.run(
            recorded.adapter().authenticate(
                settings().brokers[0].connections[0],
                {"clientId": "fixture", "clientSecret": "fixture", "accessToken": "fixture"},
            )
        )
    assert "ProtoOAAccountAuthReq" not in [name for name, _ in recorded.calls]
    del recorded.payload["ProtoOATraderReq"]["trader"]["moneyDigits"]
    with pytest.raises(ValueError, match="moneyDigits"):
        asyncio.run(recorded.adapter().account_state())
    recorded.payload["ProtoOAReconcileReq"]["ctidTraderAccountId"] = "202"
    with pytest.raises(ValueError, match="another account"):
        asyncio.run(recorded.adapter().positions())


def test_ccxt_spot_reads_and_metadata_reuse() -> None:
    exchange = ExchangeFixture()
    adapter = CCXTAdapter(exchange)

    async def run() -> None:
        assert (await adapter.symbol_info("BTC/USDT"))["spot_market"]["amount_step"] == "0.001"
        assert (await adapter.positions())[0] == {
            "asset": "BTC",
            "quantity": "1",
            "market_type": "spot",
        }
        assert "private" not in json.dumps(await adapter.account_state())
        assert "private" not in json.dumps(await adapter.quotes("BTC/USDT"))
        bars = await adapter.bars("BTC/USDT", "1m", 1700000000000, 1700000050000, 10)
        assert len(bars) == 1
        assert exchange.calls[-1] == ("bars", "BTC/USDT", "1m", 1700000000000, 10)
        exchange.payload["market"]["contract"] = True
        with pytest.raises(ValueError, match="spot"):
            await adapter.quotes("BTC/USDT")

    asyncio.run(run())


def test_ccxt_sandbox_is_first_and_account_vault_is_selected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    class Exchange:
        def __init__(self, config: Document) -> None:
            calls.append(config)

        def set_sandbox_mode(self, enabled: bool) -> None:
            calls.append(("sandbox", enabled))

    def vault(reference: str) -> dict[str, str]:
        calls.append(reference)
        return {"apiKey": "fixture", "secret": "fixture"}

    def has_demo_mode(_exchange: str) -> None:
        return None

    monkeypatch.setattr("qmx_broker.service.demo_refusal", has_demo_mode)
    monkeypatch.setattr("qmx_broker.service.credentials", vault)
    monkeypatch.setattr(ccxt, "binance", Exchange)
    broker = settings().brokers[1]
    account = (
        broker.connections[0].accounts[0].model_copy(update={"credential_ref": "qmx/subaccount"})
    )

    async def run() -> None:
        exchanges: dict[tuple[str, str, str], CCXTAdapter] = {}
        async with open_adapter(
            broker, broker.connections[0], account, exchanges=exchanges
        ) as first:
            assert calls[0] == "qmx/subaccount"
            assert cast(Document, calls[1])["options"] == {"defaultType": "spot"}
            assert calls[2] == ("sandbox", True)
        async with open_adapter(
            broker, broker.connections[0], account, exchanges=exchanges
        ) as second:
            assert first is second
            assert len(calls) == 4

    asyncio.run(run())


@pytest.mark.parametrize(
    "change",
    [
        {"quantity": 0.1},
        {"quantity": "NaN"},
        {"quantity": "0"},
        {"operator_signature": "invented"},
        {"order_type": "limit"},
        {"limit_price": "1.1"},
    ],
)
def test_proposals_cannot_carry_invalid_amounts_or_execution_authority(change: Document) -> None:
    with pytest.raises(ValidationError):
        proposal(**change)


def test_proposal_persists_without_connecting_and_retries_are_idempotent(tmp_path: Path) -> None:
    @asynccontextmanager
    async def never_connect(
        broker: Broker, connection: Connection, account: Account
    ) -> AsyncGenerator[ReadAdapter]:
        raise AssertionError("Proposing an order must not connect")
        yield CCXTAdapter(ExchangeFixture())  # pragma: no cover

    service = BrokerService(tmp_path, settings(), never_connect)
    first = service.propose_order(proposal())
    assert first == service.propose_order(proposal())
    restarted = BrokerService(tmp_path, settings())
    assert len(restarted.proposals()) == 1
    assert restarted.proposals()[0]["proposal"]["environment"] == "demo"
    assert first["status"] == "awaiting_operator_signature" and first["executed"] is False
    with pytest.raises(ValueError, match="permission"):
        service.propose_order(proposal(account_id="303"))


def test_mcp_tools_list_and_every_call_in_process(tmp_path: Path) -> None:
    recorded = CTraderFixture()

    @asynccontextmanager
    async def factory(
        broker: Broker, connection: Connection, account: Account
    ) -> AsyncGenerator[ReadAdapter]:
        assert (broker.id, connection.id, account.id) == ("ic", "demo", "101")
        adapter = recorded.adapter()
        await adapter.authenticate(connection, SIGNED_IN)
        yield adapter

    service = BrokerService(tmp_path, settings(), factory)

    async def run() -> None:
        async with Client(create_server(service)) as client:
            tools = await client.list_tools()
            assert {tool.name for tool in tools} == {
                "list_accounts",
                "list_connections",
                "account_state",
                "positions",
                "quotes",
                "bars",
                "symbol_info",
                "propose_order",
            }
            for tool in tools:
                assert tool.annotations is not None
                assert tool.annotations.model_dump(by_alias=True)["readOnlyHint"] is (
                    tool.name != "propose_order"
                )
                if tool.name == "propose_order":
                    assert tool.meta is not None and tool.meta["money_path"] is True
            scope = {"broker_id": "ic", "connection_id": "demo", "account_id": "101"}
            inputs = {
                "list_accounts": {},
                "list_connections": {},
                "account_state": scope,
                "positions": scope,
                "quotes": {**scope, "symbol": "EURUSD"},
                "symbol_info": {**scope, "symbol": "EURUSD"},
                "bars": {
                    **scope,
                    "symbol": "EURUSD",
                    "timeframe": "1m",
                    "since": 1699999980000,
                    "until": 1700000040000,
                },
                "propose_order": {"proposal": proposal().model_dump()},
            }
            for name, arguments in inputs.items():
                result = await client.call_tool(name, arguments)
                assert result.data is not None
            assert len(service.proposals()) == 1
            assert not any("Order" in name for name, _ in recorded.calls)

    asyncio.run(run())


def test_credentials_never_fall_back_to_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []

    def get_password(service: str, username: str) -> str:
        calls.append((service, username))
        return '{"clientId":"fixture"}'

    monkeypatch.setattr("qmx_broker.credentials.keyring.get_password", get_password)
    assert credentials("qmx/ctrader-demo") == {"clientId": "fixture"}
    assert calls == [("qmx/ctrader-demo", "ctrader-demo")]

    def missing(service: str, username: str) -> None:
        return None

    monkeypatch.setattr("qmx_broker.credentials.keyring.get_password", missing)
    monkeypatch.setenv("CTRADER_ACCESS_TOKEN", "must-not-use")
    with pytest.raises(ValueError, match="Missing"):
        credentials("qmx/ctrader-demo")


def test_transport_rejects_order_messages_before_any_io() -> None:
    async def run() -> None:
        transport = CTraderTransport(
            cast(CompiledProto, object()),
            asyncio.StreamReader(),
            cast(asyncio.StreamWriter, object()),
        )
        with pytest.raises(ValueError, match="read requests"):
            await transport.request("ProtoOANewOrderReq", {})

    asyncio.run(run())
