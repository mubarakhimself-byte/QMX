"""The first content wave's markets beyond forex (A13c): the market-profile blocks and the session
clocks against their goldens, cuts restored from state, the clocks across daylight-saving changes,
the seed statuses, every multi-class word's meaning per class, and every order-flow entry's data
level and estimate-labelled fallback chain."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import cast

import pytest
from qml.blocks.api import Block, EntryFace, Instance, parse_entry
from qml.catalogue import Loaded, LockEntry, load
from qml.catalogue.index import match, row
from qml.numbers import InstrumentClass

_QML = Path(__file__).resolve().parents[1]
_STDLIB = _QML / "src" / "qml" / "blocks" / "stdlib"
_SEED = _QML / "catalogue-seed" / "wave-1" / "beyond-fx"
_GOLDEN_DIR = "qml/tests/golden/beyond-fx"
_TABLES: dict[str, dict[str, object]] = {
    f"{_GOLDEN_DIR}/{name}": json.loads((_QML.parent / _GOLDEN_DIR / name).read_text("utf-8"))
    for name in ("profile.json", "clocks.json")
}
_RELATIVE, _ABSOLUTE = Decimal("1e-9"), Decimal("1e-12")  # golden_tolerance's starting default
_NS = 10**9


def _entry(entry_id: str) -> dict[str, object]:
    return json.loads((_STDLIB / entry_id / "1" / "entry.json").read_text("utf-8"))


def _face(entry_id: str) -> EntryFace:
    face = parse_entry((_STDLIB / entry_id / "1" / "entry.json").read_bytes())
    assert isinstance(face, EntryFace), face
    return face


def _cases_file(entry_id: str) -> str | None:
    golden = cast("dict[str, str]", _entry(entry_id).get("golden") or {})
    return golden.get("cases") if golden.get("cases") in _TABLES else None


def _ids() -> list[str]:
    return [
        f.name
        for f in sorted(_STDLIB.iterdir())
        if (f / "1" / "entry.json").is_file() and _cases_file(f.name) is not None
    ]


@cache
def _blocks() -> Mapping[str, Block]:
    ids = _ids()
    loaded = load(
        [LockEntry(i, 1, _face(i).fingerprint) for i in ids],
        {f"{i}@1": (_STDLIB / i / "1" / "block.py").read_bytes() for i in ids},
    )
    assert isinstance(loaded, Loaded), loaded
    return loaded.blocks


def _defaults(entry_id: str) -> dict[str, Decimal]:
    parameters = cast("dict[str, dict[str, str]]", _entry(entry_id)["parameters"])
    return {name: Decimal(spec["default"]) for name, spec in parameters.items()}


def _make(case: str) -> Instance:
    pin, *words = case.split()
    params = _defaults(pin.split("@", maxsplit=1)[0])
    params |= {k: Decimal(v) for k, v in (w.split("=", 1) for w in words)}
    return _blocks()[pin].make(params, {})


def _bars(table: Mapping[str, object]) -> list[dict[str, object]]:
    rows = cast("list[dict[str, object]]", table["bars"])
    return [{k: v if k == "time" else Decimal(str(v)) for k, v in b.items()} for b in rows]


_CASES: list[tuple[str, str]] = sorted(
    (case, name)
    for name, table in _TABLES.items()
    for case in cast("dict[str, object]", table["cases"])
)


def _close(ours: object, theirs: str | None) -> bool:
    if ours is None or theirs is None:
        return ours is None and theirs is None
    expected = Decimal(theirs)
    return abs(cast("Decimal", ours) - expected) <= max(_ABSOLUTE, _RELATIVE * abs(expected))


def test_every_beyond_fx_block_has_golden_cases_and_every_case_a_block() -> None:
    pins = {case.split()[0] for case, _ in _CASES}

    assert pins == {f"{i}@1" for i in _ids()}
    assert sorted(_ids()) == [
        "bar-range-pressure",
        "eia-natural-gas-storage-report-clock",
        "eia-petroleum-status-report-clock",
        "initial-balance-high",
        "initial-balance-low",
        "initial-balance-range-extension",
        "lbma-gold-auction-clock",
        "lbma-silver-auction-clock",
        "perp-funding-settlement-clock",
        "tpo-point-of-control",
        "tpo-value-area-high",
        "tpo-value-area-low",
    ]


@pytest.mark.parametrize(("case", "table"), _CASES)
def test_values_match_the_reference_and_missing_is_never_zero(case: str, table: str) -> None:
    instance = _make(case)
    expected = cast("dict[str, list[str | None]]", _TABLES[table]["cases"])[case]

    ours = [instance.update({"series": b}) for b in _bars(_TABLES[table])]

    assert [
        i for i, (a, b) in enumerate(zip(ours, expected, strict=True)) if not _close(a, b)
    ] == []
    assert any(v is not None for v in ours)


@pytest.mark.parametrize(("case", "table"), _CASES)
def test_a_cut_restored_from_exported_state_equals_the_full_run_and_stays_in_bound(
    case: str, table: str
) -> None:
    series = _bars(_TABLES[table])
    full = _make(case)
    outputs: list[object] = []
    peak = 0
    for b in series:
        outputs.append(full.update({"series": b}))
        peak = max(peak, full.retained())
    samples = range(1, len(series), len(series) // 20)
    unequal: list[int] = []
    for cut in samples:
        before = _make(case)
        for b in series[:cut]:
            before.update({"series": b})
        after = _make(case)
        after.import_state(json.loads(json.dumps(before.export_state())))
        if after.update({"series": series[cut]}) != outputs[cut]:
            unequal.append(cut)

    assert (len(samples), unequal) == (20, [])
    assert sum(outputs[cut] is not None for cut in samples) >= 10
    assert peak <= full.state_bound


def _at(case: str, *closes: datetime) -> list[Decimal | None]:
    instance = _make(case)
    return [
        cast("Decimal | None", instance.update({"series": {"time": int(c.timestamp()) * _NS}}))
        for c in closes
    ]


def test_the_london_and_new_york_clocks_follow_their_daylight_saving_rules() -> None:
    gold = _at(
        "lbma-gold-auction-clock@1 auction=1",
        datetime(2026, 3, 27, 10, 30, tzinfo=UTC),  # Friday, London on GMT
        datetime(2026, 3, 30, 9, 30, tzinfo=UTC),  # Monday, London on BST
        datetime(2026, 3, 30, 9, 15, tzinfo=UTC),
        datetime(2026, 3, 28, 12, 0, tzinfo=UTC),  # Saturday: Friday's auction is nearer
    )
    oil = _at(
        "eia-petroleum-status-report-clock@1",
        datetime(2026, 3, 4, 15, 30, tzinfo=UTC),  # New York on EST
        datetime(2026, 3, 11, 14, 30, tzinfo=UTC),  # New York on EDT
        datetime(2026, 11, 4, 15, 40, tzinfo=UTC),  # back on EST
    )
    funding = _at(
        "perp-funding-settlement-clock@1 interval=28800",
        datetime(2026, 3, 4, 7, 45, tzinfo=UTC),
        datetime(2026, 3, 4, 12, 0, tzinfo=UTC),  # halfway: the later settlement
    )

    assert gold == [Decimal(0), Decimal(0), Decimal(-900), Decimal(91_800)]
    assert oil == [Decimal(0), Decimal(0), Decimal(600)]
    assert funding == [Decimal(-900), Decimal(-14_400)]


def test_a_session_profile_names_its_point_of_control_and_value_area_as_the_algorithm_says() -> (
    None
):
    day = datetime(2026, 3, 2, tzinfo=UTC)
    session = [
        {
            "time": int(day.timestamp()) * _NS + (i + 1) * 1_800 * _NS,
            "high": Decimal(h),
            "low": Decimal(lo),
            "close": Decimal(lo),
        }
        for i, (lo, h) in enumerate(
            [("100", "102"), ("101", "103"), ("101", "102"), ("104", "105")]
        )
    ]
    read: dict[str, object] = {}
    for pin in ("tpo-point-of-control@1", "tpo-value-area-high@1", "tpo-value-area-low@1"):
        instance = _make(f"{pin} row_size=1")
        read[pin] = [instance.update({"series": b}) for b in session][-1]

    assert read == {
        "tpo-point-of-control@1": Decimal(102),
        "tpo-value-area-high@1": Decimal(103),
        "tpo-value-area-low@1": Decimal(101),
    }


def _seed(path: Path) -> dict[str, object]:
    return json.loads(path.read_text("utf-8"))


_SEEDS = {p.stem: _seed(p) for p in sorted(_SEED.glob("*.json"))}


_MULTI_CLASS_WORDS = {
    "volume": "volume-kind",
    "open interest": "open-interest",
    "session": "session-clock",
    "rollover": "contract-roll",
    "basis": "basis",
    "settlement": "settlement-price",
    "gap": "overnight-gap",
    "the open": "the-open",
    "the close": "the-close",
    "spread": "calendar-spread",
    "liquidation": "liquidation",
    "funding against swap": "perp-funding-rate",
    "index price": "index-price",
}


@pytest.mark.parametrize("word", sorted(_MULTI_CLASS_WORDS))
def test_every_multi_class_word_lists_a_meaning_or_not_assessed_for_all_nine_classes(
    word: str,
) -> None:
    entry = _SEEDS[_MULTI_CLASS_WORDS[word]]
    meanings = cast("dict[str, str]", entry["class_meanings"])

    assert sorted(meanings) == sorted(c.value for c in InstrumentClass)
    assert all(text.strip() for text in meanings.values())
    assert len({text for text in meanings.values() if text != "not_assessed"}) >= 2


def _order_flow() -> dict[str, dict[str, object]]:
    found = {n: e for n, e in _SEEDS.items() if e["family"] == "order-flow"}
    return found | {
        f.name: _entry(f.name)
        for f in sorted(_STDLIB.iterdir())
        if (f / "1" / "entry.json").is_file() and _entry(f.name).get("family") == "order-flow"
    }


@pytest.mark.parametrize("entry_id", sorted(_order_flow()))
def test_every_order_flow_entry_names_its_level_its_fallback_chain_and_its_estimates(
    entry_id: str,
) -> None:
    entry = _order_flow()[entry_id]
    market = [
        cast("dict[str, object]", p)
        for p in cast("list[object]", entry["inputs"])
        if "data_level" in cast("dict[str, object]", p)
    ]

    assert market
    if entry_id == "bar-range-pressure":
        assert "An estimate of who pressed" in cast("str", entry["boundaries"])
        return
    for port in market:
        chain = cast("list[dict[str, object]]", port["fallback"])
        levels = [cast("int", step["data_level"]) for step in chain]
        assert levels == sorted(levels, reverse=True)
        assert all("estimate" in cast("str", step["expected_loss"]) for step in chain)
        if not chain:
            assert "no honest fallback" in cast("str", entry["boundaries"]).lower()


def test_only_the_order_by_order_and_size_readings_have_no_fallback() -> None:
    empty = sorted(
        name
        for name, entry in _order_flow().items()
        for p in cast("list[dict[str, object]]", entry["inputs"])
        if p.get("fallback") == []
    )

    assert sorted(set(empty)) == ["iceberg-order", "large-print-filter", "tape-stop-run"]
    assert cast("dict[str, str]", _SEEDS["iceberg-order"]["transfer"])["fx"] == "not_transferable"


def test_trader_sentences_map_to_beyond_fx_entries_and_an_unknown_one_is_an_append_request() -> (
    None
):
    rows = [row(e, None) for e in [*_SEEDS.values(), *(_entry(i) for i in _ids())]]

    report = match(
        "Price returns to the TPO point of control. The London gold fix is near. "
        "The funding settlement window nears. A stacked imbalance forms under price. "
        "Open interest rises with price. The dealer gamma flips.",
        rows,
    )

    assert report.as_json() == {
        "sentences": [
            {
                "sentence": "Price returns to the TPO point of control",
                "entry": "tpo-point-of-control@1",
            },
            {"sentence": "The London gold fix is near", "entry": "lbma-gold-auction-clock@1"},
            {
                "sentence": "The funding settlement window nears",
                "entry": "perp-funding-settlement-clock@1",
            },
            {"sentence": "A stacked imbalance forms under price", "entry": "stacked-imbalance@1"},
            {"sentence": "Open interest rises with price", "entry": "open-interest@1"},
            {"sentence": "The dealer gamma flips", "entry": "unmatched"},
        ],
        "append_requests": [
            {"sentence": "The dealer gamma flips", "words": ["dealer", "gamma", "flip"]}
        ],
    }
