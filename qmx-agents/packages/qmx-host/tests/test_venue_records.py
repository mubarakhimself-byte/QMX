"""The account, venue and instrument records the node reads from cTrader land on the Library's
main (C-34), so his promote click finds them.

The node's answer is the literal `records` answer `qmn/tests/test_app_records.py` proves the
node gives over its fake cTrader. The Library is a real store on a throwaway folder, and the
promote route runs against the conformance node of `test_promote.py`.
"""

from __future__ import annotations

import time
from collections.abc import Iterator, Mapping
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from qmf.core import is_refusal
from qml.compile import CompiledUnit, compile_unit
from qml.numbers.records import parse_record
from qmx_judge.landing import G_CHECK, TEST_REPORT
from qmx_library.port import Draft, JsonObject
from qmx_library.principal import MAIN
from qmx_tools.gather import gather
from test_promote import (
    CLICKED,
    DUMMY,
    HIM,
    OPERATOR,
    TAG,
    ConformanceNode,
    as_caller,
    g_report,
    judged,
)

from qmx_host.first_start import land_dummy
from qmx_host.host import HostStore, LanderLibrary, open_store, register_checkers
from qmx_host.lifecycle import LifecycleWriter
from qmx_host.node_link import NodeLink
from qmx_host.promote import ROUTE, Promoter, harvested_calibrations, promote_router
from qmx_host.venue_records import RUN, Record, land, records_of, refresh

LEVELS: JsonObject = {"schema": "qmx.data-level/1", "levels": [0, 1, 2], "volume": "tick_count"}
ANSWER: dict[str, Any] = {
    "schema_version": "qmx.node.records/1",
    "venue": {"name": "icmarkets-ctrader", "platform": "ctrader", "sandbox": "demo"},
    "account": {
        "id": "demo-1",
        "ctid": 4401,
        "world": "demo",
        "broker": "IC Markets",
        "grant_scope": "SCOPE_TRADE",
        "owner": {"install_id": "a4dqobyha4dqobyha4dqobyha4", "tag": "a4dqobyh"},
        "position_mode": "hedging",
        "base_currency": "USD",
        "leverage": "30",
    },
    "instruments": [
        {
            "symbol": "EURUSD",
            "symbol_id": 1,
            "quote_currency": "USD",
            "digits": 5,
            "pip_position": 4,
            "lot_size": 10_000_000,
            "step_volume": 100_000,
            "min_volume": 100_000,
            "max_volume": 10_000_000_000,
            "schedule_zone": "UTC",
            "trading_mode": "ENABLED",
        },
        {
            "symbol": "XAUUSD",
            "symbol_id": 41,
            "quote_currency": "USD",
            "digits": 2,
            "pip_position": 1,
            "lot_size": 10_000,
            "step_volume": 100,
            "min_volume": 100,
            "max_volume": 10_000_000,
            "schedule_zone": "UTC",
            "trading_mode": "ENABLED",
        },
    ],
    "missing": [],
    "at": "2026-11-03T09:00:00+00:00",
}
LEVERAGE: JsonObject = {
    "version": 1,
    "tiers": [
        {
            "leverage": "30",
            "source": "ctrader: the account's leverageInCents; the symbol's own dynamic"
            " leverage is not read",
        }
    ],
}
EURUSD: JsonObject = {
    "venue": "icmarkets-ctrader",
    "symbol": "EURUSD",
    "market_id": "eurusd",
    "class": "fx",
    "currency": "USD",
    "digits": 5,
    "tick_size": "0.00001",
    "pip": {"size": "0.0001", "source": "ctrader: pipPosition 4"},
    "contract_size": "100000",
    "value_per_point": "100000",
    "lot_step": "0.01",
    "min_lot": "0.01",
    "max_lot": "1000",
    "calendar_ref": "fx-24x5@1",
    "zone": "America/New_York",
    "day_boundary": "17:00",
    "server_zone": "UTC",
    "data_levels": LEVELS,
    "leverage": LEVERAGE,
    "margin": {"intraday": "0.0334", "overnight": "0.0334"},
    "status": "live",
}


def passing_g(store: HostStore, compiled: str) -> None:
    """A passing G report for `compiled`, the unit compiled against the landed records."""
    fields: JsonObject = {
        "check": G_CHECK,
        "run_id": "qmbr-g-records",
        "status": "finished",
        "compiled_fingerprint": compiled,
        "behaviour": {},
        "safety": {"verdict": "pass"},
    }
    store.put(
        OPERATOR, Draft(TEST_REPORT, "qmbr-g-records", fields=fields), on=MAIN, expected_head=None
    )


@dataclass
class Library:
    home: Path
    store: HostStore
    writer: LifecycleWriter
    node: ConformanceNode
    app: FastAPI
    unit: str

    def heads(self, kind: str) -> dict[str, tuple[int, JsonObject]]:
        """Each item of `kind` on main: its version and fields."""
        found: dict[str, tuple[int, JsonObject]] = {}
        for object_id in self.store.with_field(kind, "venue", "icmarkets-ctrader"):
            item = self.store.get(OPERATOR, object_id).item
            head = self.store.head(item, MAIN)
            assert head is not None
            found[item] = (head[1], self.store.get(OPERATOR, head[0]).fields)
        return found

    def compiled(self) -> str:
        document = self.store.get(OPERATOR, self.unit).fields
        compiled = compile_unit(document, gather(self.store, document).context)
        assert isinstance(compiled, CompiledUnit), compiled
        return compiled.compiled_fingerprint.value

    def click(self, op_id: str, to: str = "paper") -> dict[str, Any]:
        sent: dict[str, object] = {
            "schema_version": "qmx.units.promote/1",
            "unit": {"id": DUMMY, "version": self.unit},
            "market_id": "fx.eurusd",
            "node": {"tag": TAG},
            "account": {"id": "demo-1"},
            "op_id": op_id,
            "to": to,
        }
        if to == "live":
            sent["placeholders_acknowledged"] = True
        return TestClient(as_caller(self.app, HIM)).post(ROUTE, json=sent).json()


@pytest.fixture
def library(tmp_path: Path) -> Iterator[Library]:
    home = tmp_path / "QMX"
    with open_store(home, home / "library", serving=False, floor=0) as store:
        register_checkers(store)
        writer = LifecycleWriter(home / "journals", "pc", "test")
        store.lifecycle = writer
        unit = cast(str, land_dummy(store))
        node = ConformanceNode(home)
        link = NodeLink(
            home,
            here="pc",
            apps=cast(Any, node),
            settings=dict,
            key=lambda: None,
            blobs=lambda fingerprint: [store.read_blob(fingerprint)],
        )
        promoter = Promoter(
            store,
            writer,
            link,
            LanderLibrary(store),
            calibrations=harvested_calibrations(home, lambda: time.time_ns() + 10**12),
            trading_profile=lambda _place: False,
            now=lambda: CLICKED,
        )
        app = FastAPI()
        app.include_router(promote_router(promoter))
        made = Library(home, store, writer, node, app, unit)
        judged(writer, unit, made.compiled(), "fx.eurusd")
        yield made
        writer.close()


def test_the_node_s_answer_lands_one_account_one_venue_and_an_instrument_per_market(
    library: Library,
) -> None:
    landed = land(library.store, records_of(ANSWER))

    assert [(found.kind, found.item, found.outcome, found.version) for found in landed] == [
        ("account", "account-icmarkets-ctrader-demo-1", "landed", 1),
        ("venue", "venue-icmarkets-ctrader", "landed", 1),
        ("instrument", "instrument-icmarkets-ctrader-eurusd", "landed", 1),
        ("instrument", "instrument-icmarkets-ctrader-xauusd", "landed", 1),
    ]
    assert library.heads("account") == {
        "account-icmarkets-ctrader-demo-1": (
            1,
            {
                "venue": "icmarkets-ctrader",
                "account_id": "demo-1",
                "world": "demo",
                "broker": "IC Markets",
                "position_mode": "hedging",
                "base_currency": "USD",
                "leverage": "30",
                "owner": {"install_id": "a4dqobyha4dqobyha4dqobyha4", "tag": "a4dqobyh"},
                "grant_scope": "SCOPE_TRADE",
            },
        )
    }
    assert library.heads("venue") == {
        "venue-icmarkets-ctrader": (
            1,
            {"venue": "icmarkets-ctrader", "sandbox": "demo", "data_levels": LEVELS},
        )
    }
    instruments = library.heads("instrument")
    assert instruments["instrument-icmarkets-ctrader-eurusd"] == (1, EURUSD)
    gold = instruments["instrument-icmarkets-ctrader-xauusd"][1]
    assert (gold["contract_size"], gold["lot_step"], gold["tick_size"], gold["pip"]) == (
        "100",
        "0.01",
        "0.01",
        {"size": "0.1", "source": "ctrader: pipPosition 1"},
    )
    parsed = parse_record({**EURUSD, "record_version": 1})
    assert not is_refusal(parsed)
    assert parsed.value.name == "icmarkets-ctrader:EURUSD@1"
    heads = library.store.placed("account-icmarkets-ctrader-demo-1", "account", MAIN)
    authors = [library.store.get(OPERATOR, head).annotations["author"] for head, _ in heads]
    assert authors == [{"kind": "run", "id": RUN}]


def test_the_same_facts_land_no_version_and_a_changed_lot_step_lands_one(
    library: Library,
) -> None:
    land(library.store, records_of(ANSWER))

    again = land(library.store, records_of(ANSWER))
    changed = deepcopy(ANSWER)
    changed["instruments"][0]["step_volume"] = 1_000_000
    stepped = land(library.store, records_of(changed))

    assert [found.outcome for found in again] == ["unchanged"] * 4
    assert [(found.item, found.outcome, found.version) for found in stepped] == [
        ("account-icmarkets-ctrader-demo-1", "unchanged", 1),
        ("venue-icmarkets-ctrader", "unchanged", 1),
        ("instrument-icmarkets-ctrader-eurusd", "landed", 2),
        ("instrument-icmarkets-ctrader-xauusd", "unchanged", 1),
    ]
    assert (
        library.heads("instrument")["instrument-icmarkets-ctrader-eurusd"][1]["lot_step"] == "0.1"
    )


def test_his_own_keys_stay_and_a_live_flag_lands_world_live(library: Library) -> None:
    land(library.store, records_of(ANSWER))
    item = "instrument-icmarkets-ctrader-eurusd"
    head = library.store.head(item, MAIN)
    assert head is not None
    library.store.put(
        OPERATOR,
        Draft("instrument", item, fields={**EURUSD, "calendar_ref": "fx-his@2"}),
        on=MAIN,
        expected_head=head[0],
    )
    live = deepcopy(ANSWER)
    live["account"] = {**live["account"], "world": "live"}

    land(library.store, records_of(live))

    assert library.heads("instrument")[item] == (2, {**EURUSD, "calendar_ref": "fx-his@2"})
    assert library.heads("account")["account-icmarkets-ctrader-demo-1"][1]["world"] == "live"


def test_a_promote_that_found_no_record_builds_its_deployment_once_the_records_land(
    library: Library,
) -> None:
    g_report(library.store, library.compiled())
    before = library.click("click-before")

    land(library.store, records_of(ANSWER))
    passing_g(library.store, library.compiled())
    after = library.click("click-after")

    assert (before["ok"], before["code"], before["message"]) == (
        False,
        "no_record",
        "the Library holds no record for account demo-1",
    )
    assert (after["ok"], after["value"]["node_answer"]) == (True, "accepted")
    (sent,) = library.node.deploys()
    snapshots = cast(list[Mapping[str, object]], sent["snapshots"])
    assert [(s.get("symbol"), s.get("record_version")) for s in snapshots[:2]] == [
        ("EURUSD", 1),
        ("XAUUSD", 1),
    ]
    assert snapshots[2] == {"venue": "icmarkets-ctrader", "sandbox": "demo", "data_levels": LEVELS}
    assert snapshots[3]["world"] == "demo"
    assert sent["account"] == {
        "id": "demo-1",
        "version": 1,
        "fingerprint": library.store.head("account-icmarkets-ctrader-demo-1", MAIN)[0],  # pyright: ignore[reportOptionalSubscript]
    }


def test_a_live_world_record_keeps_a_live_promote_refused_without_the_trading_profile(
    library: Library,
) -> None:
    live = deepcopy(ANSWER)
    live["account"] = {**live["account"], "world": "live"}
    land(library.store, records_of(live))
    g_report(library.store, library.compiled())

    paper = library.click("click-paper")
    answer = library.click("click-live", to="live")

    assert paper["ok"] is True
    assert (answer["ok"], answer["code"]) == (False, "trading_profile_off")


def test_only_the_three_record_kinds_land_by_this_path(library: Library) -> None:
    note = Record("note", {"title": "x"}, "note-x", "x", {"title": "x"}, {})

    (refused,) = land(library.store, [note])

    assert (refused.outcome, refused.why) == (
        "refused",
        "only account, venue and instrument records land by this path",
    )
    assert library.store.head("note-x", MAIN) is None


def test_the_refresh_lands_only_after_a_passing_self_test(library: Library) -> None:
    checks: list[dict[str, object]] = []
    asked: list[str] = []

    def call(operation: str, arguments: Mapping[str, object]) -> Mapping[str, object]:
        asked.append(operation)
        answers: dict[str, object] = {
            "passport": {"checks": checks},
            "status": {"venues": [{"venue": "ctrader", "accounts": ["demo-1"]}]},
            "records": ANSWER,
        }
        return {"ok": True, "value": answers[operation]}

    untested = refresh(call, library.store)
    checks.append({"name": "broker session", "ok": True})
    tested = refresh(call, library.store)

    assert (untested, asked[:1]) == ([], ["passport"])
    assert [(found.account, len(found.landed), found.refused) for found in tested] == [
        ("demo-1", 4, None)
    ]
    assert len(library.heads("instrument")) == 2
