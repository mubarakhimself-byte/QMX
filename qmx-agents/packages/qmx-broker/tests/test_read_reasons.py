"""A broker read that fails says why in one plain line, by a closed code, instead of "Broker read
failed". Sessions, key stores and exchanges are fakes; nothing reaches a broker."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import ccxt  # pyright: ignore[reportMissingTypeStubs] - untyped upstream
import pytest
from qmf.venue.proto import CompiledProto
from test_broker import CTraderFixture
from test_pc_home import PAIR, Memory, Session, settings, signed_in, vault
from test_refresh import Endpoint, Store, broker

from qmx_broker.adapters import Document, ReadAdapter
from qmx_broker.models import Account, Broker, BrokerSettings, Connection
from qmx_broker.oauth import Tokens
from qmx_broker.service import BrokerService, ReadRefused, open_adapter

__all__ = ["vault"]


def refused(service: BrokerService, account: str = "101") -> tuple[str, str]:
    provider, connection = ("ctrader", "demo") if account == "101" else ("crypto", "main")
    with pytest.raises(ReadRefused) as caught:
        asyncio.run(service.read("account_state", provider, connection, account))
    return caught.value.code, str(caught.value)


def ctrader(tmp_path: Path, connect: Any, row: BrokerSettings | None = None) -> BrokerService:
    def factory(provider: Broker, connection: Connection, account: Account):
        return open_adapter(
            provider, connection, account, keys=Store(Tokens("a", "r", 0)), connect=connect
        )

    return BrokerService(tmp_path / "qmx" / "data", row or settings(), factory)


class Failing(Session):
    def __init__(self, recorded: CTraderFixture, failing: str, error: Exception) -> None:
        super().__init__(recorded)
        self.failing, self.error = failing, error

        async def request(name: str, values: Document) -> Document:
            if name == self.failing:
                raise self.error
            return await recorded.request(name, values)

        self.request = request


async def never(_proto: CompiledProto, _environment: str) -> Session:
    raise AssertionError("this read must refuse before it opens a session")


def failing_on(name: str, error: Exception) -> Any:
    async def connect(_proto: CompiledProto, _environment: str) -> Session:
        return Failing(CTraderFixture(), name, error)

    return connect


def test_a_read_with_no_sign_in_says_to_sign_in_on_this_pc_first(
    tmp_path: Path, vault: Memory
) -> None:
    signed_in(vault)

    assert refused(broker(tmp_path, Store(None), Endpoint())) == (
        "not_signed_in",
        "Sign in to cTrader on This PC first; This PC holds no cTrader sign-in",
    )


def test_a_read_with_no_app_credential_names_the_missing_entry(
    tmp_path: Path, vault: Memory
) -> None:
    vault.held["qmx/token/ctrader-app", "token/ctrader-app"] = PAIR

    assert refused(ctrader(tmp_path, never)) == (
        "credential_unusable",
        "Missing Credential Manager entry qmx/read/ctrader-app; configure it before connecting",
    )


def test_a_read_naming_a_protocol_file_that_is_gone_names_the_file(
    tmp_path: Path, vault: Memory
) -> None:
    signed_in(vault)
    row = settings().model_dump()
    row["connections"][0]["connections"][0] |= {"protocol_path": "D:/gone.pb", "protocol_tag": 91}

    assert refused(ctrader(tmp_path, never, BrokerSettings.model_validate(row))) == (
        "protocol_files",
        "The cTrader protocol file D:/gone.pb that demo names does not exist; clear "
        "protocol_path and protocol_tag on demo to use the set QMX ships",
    )


def test_a_read_with_the_network_down_says_so(tmp_path: Path, vault: Memory) -> None:
    signed_in(vault)

    async def offline(_proto: CompiledProto, _environment: str) -> Session:
        raise ConnectionRefusedError(10061, "refused")

    assert refused(ctrader(tmp_path, offline)) == (
        "network",
        "QMX could not reach cTrader to read account 101; check the network and try again",
    )


def test_a_refresh_with_the_token_endpoint_down_says_so(tmp_path: Path, vault: Memory) -> None:
    signed_in(vault)

    def unreachable(_method: str, _url: str) -> tuple[int, bytes]:
        raise OSError("no route")

    store = Store()

    assert refused(broker(tmp_path, store, unreachable)) == (
        "network",
        "QMX could not reach cTrader to read account 101; check the network and try again",
    )
    assert store.writes == []


def test_a_key_or_sign_in_cTrader_refuses_says_which_to_check(
    tmp_path: Path, vault: Memory
) -> None:
    signed_in(vault)
    answer = ValueError("cTrader refused the request; verify permissions and token expiry")

    assert refused(ctrader(tmp_path, failing_on("ProtoOAApplicationAuthReq", answer))) == (
        "key_refused",
        "cTrader refused the app key or the sign-in for account 101; check the app id and "
        "secret in Settings, or sign in to cTrader on This PC again",
    )


def test_an_unexpected_failure_names_the_account_and_broker_with_its_class_as_detail(
    tmp_path: Path, vault: Memory
) -> None:
    signed_in(vault)

    assert refused(ctrader(tmp_path, failing_on("ProtoOATraderReq", KeyError("trader")))) == (
        "read_failed",
        "QMX could not read account 101 at cTrader: an unexpected KeyError; try again",
    )


class Exchange:
    is_live = False
    bar_page_limit = None

    def __init__(self, error: Exception) -> None:
        self.error = error

    async def account_state(self) -> Document:
        raise self.error


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (
            ccxt.AuthenticationError("invalid api key"),
            (
                "key_refused",
                "Crypto refused the key for account spot; check its API key in Settings",
            ),
        ),
        (
            ccxt.RequestTimeout("timed out"),
            (
                "network",
                "QMX could not reach Crypto to read account spot; check the network and try again",
            ),
        ),
    ],
)
def test_an_exchange_that_refuses_the_key_or_times_out_says_which(
    tmp_path: Path, error: Exception, reason: tuple[str, str]
) -> None:
    @asynccontextmanager
    async def factory(_b: Broker, _c: Connection, _a: Account) -> AsyncGenerator[ReadAdapter]:
        yield Exchange(error)  # pyright: ignore[reportReturnType]

    crypto = BrokerSettings.model_validate(
        {
            "connections": [
                {
                    "id": "crypto",
                    "name": "Crypto",
                    "adapter": "ccxt",
                    "exchange": "binance",
                    "connections": [
                        {
                            "id": "main",
                            "credential_ref": "qmx/crypto",
                            "accounts": [{"id": "spot", "currency": "USDT"}],
                        }
                    ],
                }
            ]
        }
    )

    assert refused(BrokerService(tmp_path, crypto, factory), "spot") == reason
