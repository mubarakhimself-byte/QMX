"""The `instrument`, `venue` and `account` kinds (Level 0 AD-26, Part C AD-312, C-02): a record
per class lands and reads as QML's record, the keys are the ones Part A reads, and the unit
checker's context reads the Library's records, sizing gold at two contract sizes to the same R."""

from __future__ import annotations

import copy
import importlib.util
from collections.abc import Iterator
from decimal import Decimal
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import JsonValue
from qmf.core import is_refusal
from qml.numbers import InstrumentClass, InstrumentRecord, distance, parse_record
from qml.unit.model import Measure
from qmx_engine.ledger import redact
from qmx_tools.gather import FIXTURE_WARNING, gather, template

from qmx_library.kinds import KindRefused, roster
from qmx_library.port import Draft
from qmx_library.principal import MAIN, Principal
from qmx_library.store import Store

OPERATOR = Principal("operator")

PART_A_KEYS = (
    "market_id", "venue", "symbol", "class", "digits", "tick_size", "pip", "contract_size",
    "value_per_point", "lot_step", "min_lot", "max_lot", "currency", "calendar_ref", "zone",
    "day_boundary", "data_levels", "expiry", "last_trade", "root", "rolls_to",
    "funding_interval", "leverage", "margin", "record_version",
)  # fmt: skip
"""Part A CONTRACTS.md 2.3, the instrument keys layers C and D and the sizer slot read."""
RECORDS_CLASSES = [
    "fx", "metal", "index_cfd", "commodity_cfd", "stock_cfd", "future", "perp", "spot_crypto",
    "stock",
]  # fmt: skip
"""Part C RECORDS.md section 2's one class enum."""

LEVELS: dict[str, JsonValue] = {"schema": "qmx.data-level/1", "levels": [0, 1, 2]}


def record(klass: str, venue: str, symbol: str, market_id: str, **extra: Any) -> dict[str, Any]:
    return {
        "venue": venue,
        "symbol": symbol,
        "market_id": market_id,
        "class": klass,
        "currency": "USD",
        "digits": 2,
        "tick_size": "0.01",
        "contract_size": "1",
        "value_per_point": "1",
        "lot_step": "0.01",
        "min_lot": "0.01",
        "calendar_ref": "fx-24x5@1",
        "zone": "America/New_York",
        "day_boundary": "17:00",
        "data_levels": LEVELS,
        "leverage": {"version": 1, "tiers": [{"leverage": "20"}]},
        "margin": {"intraday": "0.05", "overnight": "0.05"},
        "status": "specified",
    } | extra


ONE_PER_CLASS = [
    record(
        "fx", "icmarkets-ctrader", "EURUSD", "eurusd", digits=5, tick_size="0.00001",
        contract_size="100000", value_per_point="100000",
        pip={"size": "0.0001", "source": "cTrader symbol pip position 4"},
        swap={"long": "-6.5", "short": "1.2", "triple_day": "wednesday"},
    ),
    record(
        "metal", "icmarkets-ctrader", "XAUUSD", "gold", contract_size="100",
        value_per_point="100", calendar_ref="metals-24x5@1",
    ),
    record(
        "index_cfd", "icmarkets-ctrader", "US500", "sp500", contract_size="1",
        events=[{"kind": "dividend", "at": "2026-12-18", "amount_per_lot": "1.42",
                 "side": "long"}],
    ),
    record("commodity_cfd", "icmarkets-ctrader", "XTIUSD", "wti", contract_size="1000",
           value_per_point="1000", digits=3, tick_size="0.001"),
    record("stock_cfd", "icmarkets-ctrader", "AAPL.US", "aapl", lot_step="1", min_lot="1"),
    record(
        "future", "cme", "ESZ6", "sp500", digits=2, tick_size="0.25", contract_size="50",
        value_per_point="50", lot_step="1", min_lot="1", calendar_ref="cme-equity@1",
        expiry="2026-12-18", last_trade="2026-12-18T13:30:00Z", settlement="cash",
        at_expiry_action="cash_settle", root="ES", rolls_to="ESH7",
    ),
    record(
        "perp", "hyperliquid", "BTC/USDC:USDC", "btc", currency="USDC", digits=0,
        tick_size="1", lot_step="0.00001", min_lot="0.00001", calendar_ref="crypto-24x7@1",
        zone="UTC", day_boundary="00:00", funding_interval="PT1H",
        funding_source="hyperliquid: funding every hour",
        data_levels={"schema": "qmx.data-level/1", "levels": [0, 1, 3, 4, 5],
                     "volume": "exchange", "depth": "by_price", "derivatives_clock": "live",
                     "history": "provider_limited", "licence": "exchange-public-api"},
    ),
    record("spot_crypto", "binance", "BTC/USDT", "btc", currency="USDT",
           calendar_ref="crypto-24x7@1", zone="UTC", day_boundary="00:00"),
    record("stock", "ibkr", "AAPL", "aapl", lot_step="1", min_lot="1",
           calendar_ref="nyse@1", day_boundary="16:00"),
]  # fmt: skip


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with Store.open(tmp_path / "library", redactor=redact) as opened:
        yield opened


def land(store: Store, fields: dict[str, Any], item: str | None = None) -> str:
    """One instrument item put on `main`, a new version when the item is already there."""
    name = item or f"instrument:{fields['venue']}:{fields['symbol']}"
    head = store.head(name, MAIN)
    draft = Draft("instrument", name, name, fields=cast(dict[str, JsonValue], fields))
    store.put(OPERATOR, draft, on=MAIN, expected_head=None if head is None else head[0])
    return name


def unit_on(*refs: tuple[str, str]) -> dict[str, object]:
    """The dummy unit with its markets pointed at these venues and symbols, in order."""
    document = copy.deepcopy(template())
    markets = cast(list[dict[str, Any]], document["markets"])
    for market, (venue, symbol) in zip(markets, refs, strict=True):
        market["instrument_ref"] = {"venue": venue, "symbol": symbol}
    return document


def sizer() -> Any:
    """The dummy unit's sizer block, `fixed-fraction-at-stop@1`, as QML ships it."""
    source = files("qml.blocks") / "stdlib" / "fixed-fraction-at-stop" / "1" / "block.py"
    with as_file(source) as path:
        spec = importlib.util.spec_from_file_location("fixed_fraction_at_stop", path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module.BLOCK.make({"fraction": Decimal("0.01")}, {})


def test_a_record_per_class_lands_on_main_and_reads_as_qmls_record(store: Store) -> None:
    for fields in ONE_PER_CLASS:
        name = land(store, fields)
        head = store.head(name, MAIN)
        assert head is not None
        stored = dict(store.get(OPERATOR, head[0]).fields)
        parsed = parse_record(stored | {"record_version": head[1]})

        assert stored == fields
        assert not is_refusal(parsed), parsed
        assert (parsed.value.instrument_class.value, parsed.value.record_version) == (
            fields["class"],
            1,
        )
    assert sorted(f["class"] for f in ONE_PER_CLASS) == sorted(RECORDS_CLASSES)
    assert {"instrument", "venue", "account"} <= set(roster())


def test_the_instrument_kind_holds_every_key_part_a_reads_and_the_one_class_enum() -> None:
    schema = cast(dict[str, Any], roster()["instrument"].validator.schema)
    properties = cast(dict[str, Any], schema["properties"])

    assert [key for key in PART_A_KEYS if key not in properties] == []
    assert properties["class"]["enum"] == RECORDS_CLASSES
    assert [member.value for member in InstrumentClass] == RECORDS_CLASSES
    assert "roll_rule" not in properties


@pytest.mark.parametrize(
    ("kind", "fields", "pointer"),
    [
        ("instrument", record("future", "cme", "ESZ6", "sp500", roll_rule="calendar"), ""),
        ("instrument", record("fx", "v", "EURUSD", "eurusd", **{"class": "forex"}), "/class"),
        ("instrument", record("metal", "v", "XAUUSD", "gold", tick_size="0,01"), "/tick_size"),
        ("account", {"venue": "hyperliquid", "account_id": "a1", "world": "demo",
                     "token": "never-here"}, ""),
        ("account", {"venue": "ctrader", "account_id": "a1", "world": "paper"}, "/world"),
        ("venue", {"venue": "binance", "rate_limits": {"api_key": "never-here"}}, "/rate_limits"),
        ("instrument", record("perp", "v", "BTC", "btc", measured={"spread": {"Token": "x"}}),
         "/measured/spread"),
        ("instrument", record("fx", "v", "EURUSD", "eurusd",
                              leverage={"version": 1, "tiers": [], "grant": "x"}), "/leverage"),
    ],
    ids=["roll-rule", "class-spelling", "decimal-comma", "account-secret", "account-world",
         "venue-api-key", "instrument-nested-token", "leverage-closed"],
)  # fmt: skip
def test_a_key_outside_the_kinds_or_a_wrong_spelling_is_refused_at_put(
    store: Store, kind: str, fields: dict[str, Any], pointer: str
) -> None:
    draft = Draft(kind, "x", fields=cast(dict[str, JsonValue], fields))
    with pytest.raises(KindRefused) as refused:
        store.put(OPERATOR, draft, on=MAIN, expected_head=None)

    assert refused.value.code == "schema_invalid"
    assert [p.where for p in refused.value.problems] == [(pointer,)]


def test_gold_at_two_contract_sizes_risks_the_same_money_and_gives_equal_r(store: Store) -> None:
    land(store, ONE_PER_CLASS[1])
    small = record("metal", "other-cfd-broker", "GOLD", "gold", contract_size="1",
                   value_per_point="1", lot_step="1", min_lot="1")  # fmt: skip
    land(store, small)

    gathered = gather(store, unit_on(("icmarkets-ctrader", "XAUUSD"), ("other-cfd-broker", "GOLD")))
    records = gathered.context.records
    entry, stop, exit_ = Decimal("2000.00"), Decimal("1996.30"), Decimal("2007.40")
    outcomes: list[tuple[Decimal, Decimal, Decimal]] = []
    for market in ("fx.eurusd", "metal.xauusd"):
        found = records[market]
        size = sizer().update(
            {"equity": Decimal(10000), "entry_price": entry, "stop_price": stop, "record": found}
        )
        risked = (entry - stop) * found.value_per_point * size.lots
        won = (exit_ - entry) * found.value_per_point * size.lots
        outcomes.append((size.lots, risked, won / risked))

    assert gathered.warnings == ()
    assert [(r.market_id, r.contract_size) for r in records.values()] == [
        ("gold", Decimal(100)),
        ("gold", Decimal(1)),
    ]
    assert outcomes == [
        (Decimal("0.27"), Decimal("99.9"), Decimal(2)),
        (Decimal(27), Decimal("99.9"), Decimal(2)),
    ]


def test_a_distance_in_pips_on_a_record_with_no_pip_is_refused_by_name(store: Store) -> None:
    land(store, ONE_PER_CLASS[0])
    land(store, ONE_PER_CLASS[1])
    records = gather(store, template()).context.records

    eurusd = distance(Decimal(20), Measure.PIPS, records["fx.eurusd"])
    gold = distance(Decimal(20), Measure.PIPS, records["metal.xauusd"])

    assert not is_refusal(eurusd) and eurusd.value.value == 200
    assert is_refusal(gold)
    assert gold.context == {
        "field": "pip",
        "reason": "the record icmarkets-ctrader:XAUUSD@1 defines no pip, so a distance in pips "
        "has no meaning on this market",
        "record": "icmarkets-ctrader:XAUUSD@1",
    }


def test_the_check_reads_the_librarys_version_and_a_market_with_no_item_reads_the_fixture(
    store: Store,
) -> None:
    land(store, ONE_PER_CLASS[0])
    land(store, ONE_PER_CLASS[0] | {"swap": {"long": "-7.1", "short": "1.0"}})

    gathered = gather(store, template())
    eurusd = gathered.context.records["fx.eurusd"]

    assert isinstance(eurusd, InstrumentRecord)
    assert (eurusd.name, gathered.context.records["metal.xauusd"].name) == (
        "icmarkets-ctrader:EURUSD@2",
        "icmarkets-ctrader:XAUUSD@1",
    )
    assert gathered.warnings == (f"{FIXTURE_WARNING}: metal.xauusd reads xauusd.json",)


def test_two_items_for_one_symbol_or_an_item_missing_a_fact_bind_nothing_and_say_why(
    store: Store,
) -> None:
    land(store, ONE_PER_CLASS[0], "eurusd-a")
    land(store, ONE_PER_CLASS[0], "eurusd-b")
    gold = {k: v for k, v in ONE_PER_CLASS[1].items() if k != "value_per_point"}
    land(store, gold)

    gathered = gather(store, template())

    assert gathered.context.records == {}
    assert gathered.warnings == (
        "fx.eurusd: 2 instrument items hold icmarkets-ctrader:EURUSD (eurusd-a, eurusd-b), "
        "so the check reads none of them",
        "metal.xauusd: the instrument item instrument:icmarkets-ctrader:XAUUSD is not a full "
        "record: /value_per_point: the required key is missing",
    )


def test_an_archived_item_binds_nothing_and_its_replacement_binds_alone(store: Store) -> None:
    land(store, ONE_PER_CLASS[0], "eur-main")
    land(store, ONE_PER_CLASS[1], "gold-main")
    store.archive(OPERATOR, "eur-main", "withdrawn")
    store.archive(OPERATOR, "gold-main", "withdrawn")
    land(store, ONE_PER_CLASS[0], "eur-main-2")
    land(store, ONE_PER_CLASS[0] | {"swap": {"long": "-7.1", "short": "1.0"}}, "eur-main-2")

    gathered = gather(store, template())

    assert gathered.context.records["fx.eurusd"].name == "icmarkets-ctrader:EURUSD@2"
    assert gathered.warnings == (f"{FIXTURE_WARNING}: metal.xauusd reads xauusd.json",)
