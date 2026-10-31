"""A demo row on an exchange CCXT gives no demo mode is named, not read into a TypeError. The
exchanges are offline CCXT objects with fake keys; every socket refuses to connect."""

from __future__ import annotations

import asyncio
import json
import socket
from pathlib import Path

import ccxt  # pyright: ignore[reportMissingTypeStubs] - untyped upstream
import pytest
from test_pc_home import Memory, vault

from qmx_broker.models import BrokerSettings
from qmx_broker.sandbox import demo_refusal
from qmx_broker.service import BrokerService, ReadRefused

__all__ = ["vault"]

NO_DEMO_AT_4_5_85 = {
    "aster", "backpack", "bigone", "bit2c", "bitbank", "bitbns", "bitfinex", "bitflyer",
    "bithumb", "bitopro", "bitrue", "bitstamp", "bitteam", "bittrade", "bitvavo", "btcbox",
    "btcmarkets", "btcturk", "bydfi", "cex", "coinbase", "coincheck", "coinex", "coinmate",
    "coinone", "coinsph", "coinspot", "cryptomus", "deepcoin", "digifinex", "foxbit", "hibachi",
    "htx", "independentreserve", "indodax", "kraken", "kucoin", "kucoinfutures", "latoken",
    "lbank", "luno", "mercado", "mexc", "mudrex", "onetrading", "p2b", "paymium", "revolutx",
    "tokocrypto", "toobit", "upbit", "whitebit", "xt", "zaif",
}  # fmt: skip
KRAKEN_LINE = (
    "kraken has no demo mode in CCXT, so QMX cannot read a demo account there; use a live "
    "read-only key or another exchange"
)


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every socket but the loopback pair asyncio's event loop wakes itself with refuses."""
    connect = socket.socket.connect

    def refuse(self: socket.socket, address: tuple[str, int]) -> None:
        if address[0] != "127.0.0.1":
            raise OSError("this test never reaches an exchange")
        connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", refuse)
    demo_refusal.cache_clear()


def test_the_exchanges_with_no_demo_mode_are_the_54_named_at_ccxt_4_5_85() -> None:
    assert ccxt.__version__ == "4.5.85"
    names = {name for name in ccxt.exchanges if demo_refusal(name) is not None}

    assert names == NO_DEMO_AT_4_5_85
    assert len(names) == 54


def test_the_check_names_kraken_and_passes_binance_and_an_unknown_id() -> None:
    assert demo_refusal("kraken") == KRAKEN_LINE
    assert demo_refusal("binance") is None
    assert demo_refusal("no-such-exchange") is None


def test_an_exchange_that_cannot_be_built_with_no_keys_is_refused_by_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Unbuildable:
        def __init__(self, config: dict[str, object]) -> None:
            raise ccxt.AuthenticationError("requires apiKey")

    monkeypatch.setattr(ccxt, "binance", Unbuildable)

    assert demo_refusal("binance") == (
        "binance has no demo mode in CCXT, so QMX cannot read a demo account there; use a live "
        "read-only key or another exchange"
    )


def kraken(environment: str) -> BrokerSettings:
    return BrokerSettings.model_validate(
        {
            "connections": [
                {
                    "id": "kraken",
                    "name": "Kraken",
                    "adapter": "ccxt",
                    "exchange": "kraken",
                    "connections": [
                        {
                            "id": "main",
                            "credential_ref": "qmx/read/kraken",
                            "environment": environment,
                            "accounts": [{"id": "spot", "currency": "USD"}],
                        }
                    ],
                }
            ]
        }
    )


def test_a_kraken_demo_read_says_kraken_has_no_demo_mode(tmp_path: Path, vault: Memory) -> None:
    vault.held["qmx/read/kraken", "read/kraken"] = json.dumps(
        {"apiKey": "not-a-real-key", "secret": "bm90LWEtcmVhbC1zZWNyZXQ="}
    )

    with pytest.raises(ReadRefused) as caught:
        asyncio.run(
            BrokerService(tmp_path, kraken("demo")).read("account_state", "kraken", "main", "spot")
        )

    assert (caught.value.code, caught.value.line) == ("no_demo_mode", KRAKEN_LINE)
