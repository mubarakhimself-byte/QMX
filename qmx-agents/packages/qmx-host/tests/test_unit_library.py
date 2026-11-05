"""Units in the Library (Part A A7, AD-111, AD-112, AD-118): the host's two checkers, the dummy's
landing on a fresh QMX folder, and what `qmx_tools.gather` hands the checker. Every folder is in
pytest's tmp folder on a scratch profile; no host process is started."""

from __future__ import annotations

import copy
import json
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import cast

import pytest
from pydantic import JsonValue
from qml.unit import schema
from qmx_control.service import ControlError, ControlService
from qmx_library.kinds import KindRefused, kind
from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import MAIN, Principal, drafts_ref
from qmx_library.store import Store
from qmx_tools.gather import DUMMY, check_unit, gather, template

from qmx_host import first_start, venue_records
from qmx_host.first_start import Places, make_new
from qmx_host.host import land_first_unit, open_store, register_checkers

OPERATOR = Principal("operator")
KINDS = Path(first_start.__file__).parents[3] / "qmx-library" / "src" / "qmx_library" / "kinds"


@pytest.fixture
def pc(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    profile = tmp_path / "profile"
    for name, part in (("APPDATA", "Roaming"), ("LOCALAPPDATA", "Local")):
        (profile / part).mkdir(parents=True)
        monkeypatch.setenv(name, str(profile / part))
    monkeypatch.setenv("USERPROFILE", str(profile))
    monkeypatch.setenv("HOME", str(profile))
    monkeypatch.delenv("QMX_HOME", raising=False)
    monkeypatch.setattr("qmx_home._fixed_drives", list)
    monkeypatch.setattr(first_start, "_fixed_drives", list)
    yield tmp_path


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with open_store(tmp_path, tmp_path / "library", serving=False, floor=0) as opened:
        register_checkers(opened)
        yield opened


def dummies(store: Store) -> list[str]:
    return store.with_field("unit", "unit_id", DUMMY)


def draft_unit(store: Store, document: dict[str, object], item: str) -> None:
    fields = cast(dict[str, JsonValue], document)
    draft = Draft("unit", item, item, fields=fields)
    store.put(OPERATOR, draft, on=drafts_ref(item), expected_head=None)


def broken() -> dict[str, object]:
    """The dummy with a pin dropped (B), a number outside its range (C) and a market whose
    instrument_ref names a symbol no record holds (D)."""
    document = template()
    pins = cast(list[dict[str, object]], document["pins"])
    document["pins"] = [p for p in pins if p["entry_id"] != "ema"]
    numbers = cast(dict[str, dict[str, object]], document["numbers"])
    numbers["ema_period"]["default"] = "500"
    markets = cast(list[dict[str, dict[str, str]]], document["markets"])
    markets[0]["instrument_ref"]["symbol"] = "GBPUSD"
    return document


def test_the_unit_kind_holds_qmls_generated_schema() -> None:
    kind_file = json.loads((KINDS / "unit.schema.json").read_text("utf-8"))

    assert kind_file["fields"] == schema()
    assert (kind_file["schema_version"], kind_file["checks"]) == (
        2,
        [{"checker": "qml.unit/1", "on": "publish"}],
    )
    assert kind("unit").schema_version == 2


def test_a_fresh_folder_holds_one_dummy_draft_after_two_starts(pc: Path) -> None:
    layout = make_new(pc / "QMX", Places({"APPDATA": str(pc / "profile" / "Roaming")}))

    for _ in range(2):
        with open_store(layout.home, layout.home / "library", serving=False, floor=0) as opened:
            register_checkers(opened)
            land_first_unit(opened)

    with open_store(layout.home, layout.home / "library", serving=False, floor=0) as opened:
        found = dummies(opened)
        assert len(found) == 1
        view = opened.get(OPERATOR, found[0])
        result, _ = check_unit(opened, view.fields)
        assert (result.verdict.value, len(result.errors)) == ("pass", 0)
        assert opened.head(view.item, drafts_ref(view.item)) is not None
        assert opened.head(view.item, MAIN) is None


def test_a_broken_unit_saves_as_a_draft_and_refuses_to_publish_with_every_problem(
    store: Store,
) -> None:
    draft_unit(store, broken(), "broken")

    with pytest.raises(KindRefused) as refused:
        store.merge(OPERATOR, "broken", from_ref=drafts_ref("broken"), into=MAIN)

    rules = sorted(p.rule for p in refused.value.problems)
    assert refused.value.code == "check_failed"
    assert str(refused.value) == f"check_failed: unit: {refused.value.problems[0].message}"
    assert rules == ["B/block_not_pinned", "C/outside_range", "D/no_record"]
    assert store.head("broken", MAIN) is None


def test_a_unit_whose_shape_breaks_refuses_on_save_with_every_shape_problem(store: Store) -> None:
    document = template()
    document["direction"] = "sideways"
    del document["claim_card"]

    with pytest.raises(KindRefused) as refused:
        draft_unit(store, document, "shapeless")

    assert refused.value.code == "schema_invalid"
    assert sorted(p.where for p in refused.value.problems) == [("",), ("/direction",)]
    assert str(refused.value) == f"schema_invalid: unit: {refused.value.problems[0].message}"


def test_the_dummy_publishes(store: Store) -> None:
    draft_unit(store, template(), "dummy")

    merged = store.merge(OPERATOR, "dummy", from_ref=drafts_ref("dummy"), into=MAIN)

    published = store.head("dummy", MAIN)
    assert merged.outcome == "fast-forward"
    assert published is not None and published[0] == merged.object_id


def test_an_entry_with_a_broken_face_refuses_on_save_and_a_provides_component_saves(
    store: Store,
) -> None:
    entry: dict[str, JsonValue] = {"schema": "qmx.entry/1", "entry_id": "half", "version": 1}
    face: dict[str, JsonValue] = {"component_type": "context", "entry": entry}
    provides: dict[str, JsonValue] = {"legacy_provides": "k", "app_id": "a", "output": "o"}

    with pytest.raises(KindRefused) as refused:
        store.put(
            OPERATOR,
            Draft("component", "half", fields=face),
            on=drafts_ref("half"),
            expected_head=None,
        )
    saved = store.put(
        OPERATOR,
        Draft("component", "app", fields=provides),
        on=drafts_ref("app"),
        expected_head=None,
    )

    assert (refused.value.code, [p.rule for p in refused.value.problems]) == (
        "check_failed",
        ["entry/face"],
    )
    assert saved.object_id.startswith("fp1:sha256:")


def test_a_store_with_no_checker_refuses_an_entry_save(tmp_path: Path) -> None:
    entry: dict[str, JsonValue] = {"schema": "qmx.entry/1"}
    draft = Draft("component", "e", fields={"entry": entry})
    with (
        open_store(tmp_path, tmp_path / "library", serving=False, floor=0) as bare,
        pytest.raises(LibraryRefused) as refused,
    ):
        bare.put(OPERATOR, draft, on=drafts_ref("e"), expected_head=None)

    assert refused.value.code == "checker_unavailable"


def test_gather_binds_a_record_by_the_markets_instrument_ref() -> None:
    document = template()
    markets = cast(list[dict[str, dict[str, str]]], document["markets"])
    swapped = copy.deepcopy(document)
    swapped_markets = cast(list[dict[str, dict[str, str]]], swapped["markets"])
    swapped_markets[0]["instrument_ref"] = markets[1]["instrument_ref"]

    records = gather(None, swapped).context.records

    assert {m: (r.venue, r.symbol) for m, r in records.items()} == {
        "fx.eurusd": ("icmarkets-ctrader", "XAUUSD"),
        "metal.xauusd": ("icmarkets-ctrader", "XAUUSD"),
    }
    assert gather(None, document).warnings == (
        "no Library record for this market, so it reads QML's test fixture: "
        "fx.eurusd reads eurusd.json",
        "no Library record for this market, so it reads QML's test fixture: "
        "metal.xauusd reads xauusd.json",
    )


GBPUSD_ROW: dict[str, JsonValue] = {
    "symbol": "GBPUSD",
    "market_id": "gbpusd",
    "klass": "fx",
    "calendar_ref": "fx-24x5@1",
    "zone": "America/New_York",
    "day_boundary": "17:00",
}
GBPUSD_SYMBOL: dict[str, object] = {
    "symbol": "GBPUSD",
    "quote_currency": "USD",
    "digits": 5,
    "pip_position": 4,
    "lot_size": 10_000_000,
    "step_volume": 100_000,
    "min_volume": 100_000,
    "schedule_zone": "UTC",
    "trading_mode": "ENABLED",
}


def node_call(operation: str, arguments: Mapping[str, object]) -> Mapping[str, object]:
    """A self-tested node with one bound account, answering only the symbols it is asked for, as
    its real `records` operation does."""
    if operation == "passport":
        return {"ok": True, "value": {"checks": [{"ok": True}]}}
    if operation == "status":
        return {"ok": True, "value": {"venues": [{"venue": "ctrader", "accounts": ["9000"]}]}}
    held = {"GBPUSD": GBPUSD_SYMBOL}
    asked = cast("list[str]", arguments["symbols"])
    return {
        "ok": True,
        "value": {
            "venue": {"name": "icmarkets-ctrader", "platform": "ctrader", "sandbox": "demo"},
            "account": {"id": "9000", "world": "demo"},
            "instruments": [held[symbol] for symbol in asked if symbol in held],
        },
    }


def test_a_market_added_to_node_settings_lands_its_record_and_gather_reads_it(
    store: Store, tmp_path: Path
) -> None:
    control = ControlService(tmp_path / "control")
    document = template()
    document["markets"] = [
        {
            "market_id": "fx.gbpusd",
            "instrument_ref": {"venue": "icmarkets-ctrader", "symbol": "GBPUSD"},
        }
    ]

    def as_the_host_builds_it() -> venue_records.VenueRecords:
        section = control.settings_get("node")
        return venue_records.VenueRecords(
            node_call,
            store,
            every_s=venue_records.refresh_s(section),
            markets=venue_records.record_markets(section),
        )

    before = as_the_host_builds_it()
    before.round()
    records_before = gather(store, document).context.records
    control.settings_put("node", {"record_markets": [GBPUSD_ROW], "records_refresh_s": 600})
    after = as_the_host_builds_it()
    after.round()
    found = gather(store, document)

    assert (records_before, before.every_s) == ({}, 86_400)
    assert found.context.records["fx.gbpusd"].name == "icmarkets-ctrader:GBPUSD@1"
    assert (found.warnings, after.every_s) == ((), 600)


def test_a_node_row_missing_a_fact_is_refused_and_a_broken_table_reads_as_the_starting_rows(
    tmp_path: Path,
) -> None:
    control = ControlService(tmp_path)
    missing = {key: value for key, value in GBPUSD_ROW.items() if key != "zone"}

    with pytest.raises(ControlError) as refused:
        control.settings_put("node", {"record_markets": [missing]})
    (tmp_path / "settings.toml").write_text(
        '[node]\nrecord_markets = ["GBPUSD"]\nrecords_refresh_s = "soon"\n', "utf-8"
    )
    broken = control.settings_get("node")

    assert refused.value.code == "invalid_settings"
    assert [m.symbol for m in venue_records.record_markets(broken)] == ["EURUSD", "XAUUSD"]
    assert venue_records.refresh_s(broken) == 86_400
