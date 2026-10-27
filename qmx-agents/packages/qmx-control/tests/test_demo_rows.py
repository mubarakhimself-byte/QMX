"""A connections write refuses, by name, a CCXT demo row on an exchange with no demo mode, but only
when the row is new or newly demo, so a row saved before the check never blocks other edits."""

from __future__ import annotations

import asyncio
import socket
import tomllib
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import keyring
import pytest
from keyring.backends import null
from qmx_broker.service import BrokerService, ReadRefused

from qmx_control.models import ControlError
from qmx_control.service import ControlService, Document

KRAKEN_LINE = (
    "kraken has no demo mode in CCXT, so QMX cannot read a demo account there; use a live "
    "read-only key or another exchange"
)


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """No exchange is reached and no real Credential Manager entry is read."""
    connect = socket.socket.connect

    def refuse(self: socket.socket, address: tuple[str, int]) -> None:
        if address[0] != "127.0.0.1":
            raise OSError("this test never reaches an exchange")
        connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", refuse)
    before = keyring.get_keyring()
    keyring.set_keyring(null.Keyring())
    try:
        yield
    finally:
        keyring.set_keyring(before)


def provider(id: str, exchange: str, environment: str) -> Document:
    return {
        "id": id,
        "name": id.title(),
        "adapter": "ccxt",
        "exchange": exchange,
        "connections": [
            {
                "id": "main",
                "credential_ref": f"qmx/read/{id}",
                "environment": environment,
                "accounts": [{"id": "spot", "currency": "USD"}],
            }
        ],
    }


def put(service: ControlService, *providers: Document) -> Document:
    return service.settings_put("connections", {"connections": list(providers)})


def stored(home: Path) -> list[tuple[str, str]]:
    rows: list[dict[str, Any]] = tomllib.loads((home / "settings.toml").read_text("utf-8"))[
        "connections"
    ]
    return [(row["id"], row["connections"][0]["environment"]) for row in rows]


def refusal(service: ControlService, *providers: Document) -> tuple[str, int, str]:
    with pytest.raises(ControlError) as caught:
        put(service, *providers)
    return caught.value.code, caught.value.status, str(caught.value)


def test_a_new_kraken_demo_row_is_refused_by_name_and_nothing_is_saved(tmp_path: Path) -> None:
    service = ControlService(tmp_path)

    assert refusal(service, provider("kraken", "kraken", "demo")) == (
        "invalid_brokers",
        400,
        KRAKEN_LINE,
    )
    assert not (tmp_path / "settings.toml").exists()


def test_a_binance_demo_row_and_a_kraken_live_row_save(tmp_path: Path) -> None:
    service = ControlService(tmp_path)

    put(service, provider("binance", "binance", "demo"), provider("kraken", "kraken", "live"))

    assert stored(tmp_path) == [("binance", "demo"), ("kraken", "live")]


@pytest.mark.parametrize(("exchange", "environment"), [("kraken", "live"), ("binance", "demo")])
def test_a_row_switched_to_kraken_demo_is_refused_and_stays_as_it_was(
    tmp_path: Path, exchange: str, environment: str
) -> None:
    service = ControlService(tmp_path)
    put(service, provider("kraken", exchange, environment))

    assert refusal(service, provider("kraken", "kraken", "demo"))[2] == KRAKEN_LINE
    assert stored(tmp_path) == [("kraken", environment)]


def test_an_old_kraken_demo_row_loads_reads_with_the_line_and_never_blocks_other_edits(
    tmp_path: Path,
) -> None:
    (tmp_path / "settings.toml").write_text(
        '[[connections]]\nid = "kraken"\nname = "Kraken"\nadapter = "ccxt"\nexchange = "kraken"\n'
        '[[connections.connections]]\nid = "main"\ncredential_ref = "qmx/read/kraken"\n'
        '[[connections.connections.accounts]]\nid = "spot"\ncurrency = "USD"\n',
        encoding="utf-8",
    )
    service = ControlService(tmp_path)
    old = cast(list[Document], service.settings_get("connections")["connections"])[0]

    put(service, old, provider("binance", "binance", "demo"))

    assert stored(tmp_path) == [("kraken", "demo"), ("binance", "demo")]
    broker = BrokerService(tmp_path, brokers=lambda: service.settings_get("connections"))
    assert broker.list_accounts()["total"] == 2
    with pytest.raises(ReadRefused) as caught:
        asyncio.run(broker.read("account_state", "kraken", "main", "spot"))
    assert (caught.value.code, caught.value.line) == ("no_demo_mode", KRAKEN_LINE)
