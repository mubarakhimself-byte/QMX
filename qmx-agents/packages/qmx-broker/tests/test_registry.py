"""The connection registry, its declarations, the health walk and the two-home refusal."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from qmx_broker.credentials import file_credential
from qmx_broker.models import Account, Broker, BrokerSettings, Connection
from qmx_broker.registry import (
    SETUP,
    WORDS,
    Down,
    ProbeResult,
    Reading,
    SlowDown,
    Slowdowns,
    describe,
    names,
    probe_for,
    walk,
)
from qmx_broker.service import BrokerService


def provider(**values: object) -> Broker:
    body: dict[str, object] = {
        "id": "binance-vision",
        "name": "Binance public files",
        "adapter": "binance-vision",
        "kind": "data",
        **values,
    }
    return Broker.model_validate(body)


def connection(**values: object) -> Connection:
    body: dict[str, object] = {
        "id": "vision",
        "credential_ref": "qmx/data/binance-vision",
        "home": "contabo",
        **values,
    }
    return Connection.model_validate(body)


def test_the_old_brokers_section_reads_into_the_same_accounts(tmp_path: Path) -> None:
    home = tmp_path
    legacy = BrokerSettings(
        brokers=[
            Broker(
                id="ic",
                name="IC Markets",
                adapter="ctrader",
                connections=[
                    Connection(
                        id="demo",
                        credential_ref="qmx/read/ic-demo",
                        accounts=[Account(id="101", currency="USD")],
                    )
                ],
            )
        ]
    )
    modern = BrokerSettings(connections=legacy.providers)
    old = BrokerService(
        home / "old", brokers=lambda: legacy.model_dump(mode="json")
    ).list_accounts()
    new = BrokerService(
        home / "new", brokers=lambda: modern.model_dump(mode="json")
    ).list_accounts()

    assert old == new
    assert new["accounts"][0]["id"] == "101"
    assert new["accounts"][0]["home"] == "pc"
    assert modern.resolve("ic", "demo", "101")[2].currency == "USD"


def test_a_save_that_gives_one_credential_two_homes_is_refused() -> None:
    body = {
        "connections": [
            {
                "id": "binance",
                "name": "Binance",
                "adapter": "ccxt-public",
                "exchange": "binance",
                "kind": "data",
                "connections": [
                    {"id": "a", "credential_ref": "qmx/data/one", "home": "pc"},
                    {"id": "b", "credential_ref": "qmx/data/one", "home": "contabo"},
                ],
            }
        ]
    }

    with pytest.raises(ValidationError, match="two homes"):
        BrokerSettings.model_validate(body)


def test_a_stub_live_trade_key_stores_nothing_and_reads_needs_you() -> None:
    class Store:
        def __init__(self) -> None:
            self.writes: list[tuple[str, str]] = []

        def get_password(self, service: str, username: str) -> str | None:
            return None

        def set_password(self, service: str, username: str, password: str) -> None:
            self.writes.append((service, username))

        def delete_password(self, service: str, username: str) -> None:
            return None

    store = Store()
    refused = file_credential(
        "ctrader-live", {"clientId": "stub"}, can_trade_live=True, store=store
    )
    after_refusal = list(store.writes)
    allowed = file_credential("binance", {"apiKey": "stub"}, kind="data", store=store)

    assert (refused.stored, refused.word, after_refusal) == (False, "needs_you", [])
    assert (allowed.stored, allowed.reference) == (True, "qmx/data/binance")


def test_a_provider_429_with_retry_after_sets_slowed_until() -> None:
    space = Slowdowns()
    calls: list[str] = []

    def limited(_provider: Broker, _connection: Connection) -> ProbeResult:
        calls.append("probe")
        raise SlowDown("rate_limited", retry_after=120)

    first = walk(
        provider(),
        connection(),
        probe=limited,
        now=100.0,
        slowdowns=space,
        egress_ip="203.0.113.9",
    )
    second = walk(
        provider(),
        connection(),
        probe=limited,
        now=130.0,
        slowdowns=space,
        egress_ip="203.0.113.9",
    )

    assert (first.word, first.slowed_until) == ("slowed", 220.0)
    assert second.word == "slowed"
    assert calls == ["probe"]
    assert (
        space.remaining(
            describe("binance-vision"), connection(), now=130.0, egress_ip="203.0.113.9"
        )
        == 90.0
    )


def test_one_egress_address_shares_its_wait_between_two_connections() -> None:
    space = Slowdowns()
    other = connection(id="spot", credential_ref="qmx/data/spot")
    declaration = describe("binance-vision")
    space.note(declaration, connection(), retry_after=60, now=0.0, egress_ip="203.0.113.9")

    assert space.remaining(declaration, other, now=10.0, egress_ip="203.0.113.9") == 50.0
    assert space.remaining(declaration, other, now=10.0, egress_ip="198.51.100.4") == 0.0


def test_the_health_walk_and_the_declarations_cover_every_word_and_setup_state() -> None:
    assert SETUP == ("available", "configured", "authorized", "reachable", "healthy")
    assert WORDS == ("ok", "slowed", "maintenance", "needs_you", "down")
    assert {
        "ctrader",
        "ccxt",
        "mt5",
        "dukascopy",
        "binance-vision",
        "ccxt-public",
        "databento",
        "firecrawl",
        "http",
    } <= set(names())
    for name in names():
        found = describe(name)
        assert found.auth and found.session in ("host", "step")
        assert found.limit_scope in ("connection", "egress")
        assert found.health_check

    live = connection(id="live", scope="trade", environment="live", home="pc")
    assert walk(provider(), live, probe=None, now=0.0) == Reading(
        "live", "configured", "needs_you", code="trade_live_on_pc"
    )

    def broken(_provider: Broker, _connection: Connection) -> ProbeResult:
        raise Down("provider_error")

    closed = provider(adapter="ccxt-public", exchange="binance")
    assert (
        walk(closed, connection(id="spot"), probe=broken, now=0.0, market_open=False).word
        == "maintenance"
    )
    assert probe_for("dukascopy") is not None
