"""New version or new unit by one table (Part A slice A9, AD-115): each default label from a pair
of documents, the highest result wins, and his table is read as data."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest
from qml.identity import (
    EditLabel,
    IdentityTableError,
    Result,
    classify,
    diff,
    parse_table,
)
from qml.unit import Unit, parse

_DUMMY = Path(__file__).resolve().parents[1] / "src" / "qml" / "unit" / "templates"
_TEXT = (_DUMMY / "dummy-trend-pullback.json").read_text("utf-8")


def _row(label: str, result: str, counted: bool, click: bool) -> dict[str, object]:
    return {"label": label, "result": result, "counted_try": counted, "click_before_live": click}


DEFAULT_ROWS = [
    _row("motion_inside_range", "calibration_row", False, False),
    _row("learned_retrain_in_bounds", "calibration_row", False, False),
    _row("learned_retrain_out_of_bounds", "new_version", True, True),
    *(
        _row(label, "new_version", True, True)
        for label in (
            "range_change",
            "motion_rule_change",
            "cadence_change",
            "fixed_value_change",
            "bar_change",
            "session_change",
            "markets_change",
            "market_settings_adopted",
            "block_fix",
            "ambiguity_resolved",
        )
    ),
    *(
        _row(label, "new_unit", True, True)
        for label in (
            "block_swap",
            "role_added",
            "role_removed",
            "combiner_change",
            "transplant",
            "market_logic_change",
            "rewrite",
            "structure_change",
        )
    ),
    _row("title_change", "none", False, False),
]
"""CONTRACTS.md section 7, the same rows `qmx_control.service.UNITS_DEFAULTS` ships."""
TABLE = parse_table(DEFAULT_ROWS)

type Doc = dict[str, Any]


def _unit(document: Doc) -> Unit:
    parsed = parse(document)
    assert parsed.problems == ()
    assert parsed.unit is not None
    return parsed.unit


def _edited(edit: Callable[[Doc], None]) -> Unit:
    document = cast(Doc, json.loads(_TEXT))
    edit(document)
    return _unit(document)


OLD = _unit(cast(Doc, json.loads(_TEXT)))


def _numbers(name: str, field: str, value: object) -> Callable[[Doc], None]:
    def edit(document: Doc) -> None:
        document["numbers"][name][field] = value

    return edit


def _motion(name: str, field: str, value: object) -> Callable[[Doc], None]:
    def edit(document: Doc) -> None:
        document["numbers"][name]["motion"][field] = value

    return edit


def _retrained(default: str) -> Callable[[Doc], None]:
    """A learned number in both documents, so only its value moves."""

    def edit(document: Doc) -> None:
        document["numbers"]["rsi_low"]["motion"] = {"mode": "learned", "source": "own_record"}
        document["numbers"]["rsi_low"]["default"] = default

    return edit


LEARNED = _retrained("30")


def _set(*path: str | int, value: object) -> Callable[[Doc], None]:
    def edit(document: Doc) -> None:
        target: Any = document
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = value

    return edit


def _slots(document: Doc) -> Doc:
    return cast(Doc, document["logic"]["long"]["slots"])


def _add_filter(document: Doc) -> None:
    _slots(document)["filter"] = {
        "role": "filter",
        "combiner": {"kind": "all", "when_inputs_absent": "no_signal"},
        "bindings": [
            {"name": "f", "block": "ema@1", "params": {}, "inputs": {"series": "m15.close"}}
        ],
    }


def _drop_trigger(document: Doc) -> None:
    del _slots(document)["trigger"]


def _add_market(document: Doc) -> None:
    document["markets"].append(
        {"market_id": "fx.gbpusd", "instrument_ref": {"venue": "v", "symbol": "GBPUSD"}}
    )


def _transplant(document: Doc) -> None:
    document["lineage"] = {
        "parents": [{"unit_id": "breakout-x", "version_ref": "v3", "edit_labels": ["transplant"]}]
    }


PAIRS: list[tuple[str, Callable[[Doc], None], set[EditLabel], Result]] = [
    (
        "calibrated number moves inside its range",
        _numbers("min_trend_strength", "default", "0.0010"),
        {EditLabel.MOTION_INSIDE_RANGE},
        Result.CALIBRATION_ROW,
    ),
    (
        "range widened",
        _numbers("ema_period", "range", {"min": "10", "max": "400", "step": "1"}),
        {EditLabel.RANGE_CHANGE},
        Result.NEW_VERSION,
    ),
    (
        "motion rule changed",
        _motion("min_trend_strength", "shrink_k", 50),
        {EditLabel.MOTION_RULE_CHANGE},
        Result.NEW_VERSION,
    ),
    (
        "cadence changed",
        _motion("min_trend_strength", "cadence", {"every_closed_trades": 40}),
        {EditLabel.CADENCE_CHANGE},
        Result.NEW_VERSION,
    ),
    (
        "fixed value changed",
        _numbers("ema_period", "default", "120"),
        {EditLabel.FIXED_VALUE_CHANGE},
        Result.NEW_VERSION,
    ),
    (
        "bar changed",
        _set("streams", 0, "bar", "size", value="3600"),
        {EditLabel.BAR_CHANGE},
        Result.NEW_VERSION,
    ),
    ("market added", _add_market, {EditLabel.MARKETS_CHANGE}, Result.NEW_VERSION),
    (
        "market settings adopted",
        _set("markets", 0, "settings", value={"spread_cap": "0.0002"}),
        {EditLabel.MARKET_SETTINGS_ADOPTED},
        Result.NEW_VERSION,
    ),
    (
        "block fixed to a new version",
        _set("exit_set", 0, "block", value="swing-stop-buffer@2"),
        {EditLabel.BLOCK_FIX},
        Result.NEW_VERSION,
    ),
    (
        "block swapped",
        _set("exit_set", 0, "block", value="atr-stop@1"),
        {EditLabel.BLOCK_SWAP},
        Result.NEW_UNIT,
    ),
    ("role added", _add_filter, {EditLabel.ROLE_ADDED}, Result.NEW_UNIT),
    ("role removed", _drop_trigger, {EditLabel.ROLE_REMOVED}, Result.NEW_UNIT),
    (
        "combiner changed",
        _set("logic", "long", "slots", "context", "combiner", "kind", value="any"),
        {EditLabel.COMBINER_CHANGE},
        Result.NEW_UNIT,
    ),
    ("transplanted from another unit", _transplant, {EditLabel.TRANSPLANT}, Result.NEW_UNIT),
    (
        "rewritten",
        _set("lineage", value={"rewritten_from": "dummy-trend-pullback@v1"}),
        {EditLabel.REWRITE},
        Result.NEW_UNIT,
    ),
    (
        "claim card corrected",
        _set("claim_card", "idea", value="buy pullbacks in an uptrend only"),
        {EditLabel.AMBIGUITY_RESOLVED},
        Result.NEW_VERSION,
    ),
    ("title changed", _set("title", value="Trend pullback"), {EditLabel.TITLE_CHANGE}, Result.NONE),
    (
        "direction changed",
        _set("direction", value="long"),
        {EditLabel.STRUCTURE_CHANGE},
        Result.NEW_UNIT,
    ),
]


@pytest.mark.parametrize(("name", "edit", "labels", "result"), PAIRS, ids=[p[0] for p in PAIRS])
def test_each_edit_gets_its_label_and_the_tables_result(
    name: str, edit: Callable[[Doc], None], labels: set[EditLabel], result: Result
) -> None:
    answer = classify(OLD, _edited(edit), TABLE)

    assert set(answer.labels) == labels, name
    assert answer.result is result
    assert answer.counted_try is (result in {Result.NEW_VERSION, Result.NEW_UNIT})
    assert answer.click_before_live is answer.counted_try


@pytest.mark.parametrize(
    ("default", "label", "result"),
    [
        ("40", EditLabel.LEARNED_RETRAIN_IN_BOUNDS, Result.CALIBRATION_ROW),
        ("140", EditLabel.LEARNED_RETRAIN_OUT_OF_BOUNDS, Result.NEW_VERSION),
    ],
)
def test_a_learned_retrain_is_a_calibration_only_inside_its_bounds(
    default: str, label: EditLabel, result: Result
) -> None:
    answer = classify(_edited(LEARNED), _edited(_retrained(default)), TABLE)

    assert (answer.labels, answer.result) == ((label,), result)


def test_the_same_document_is_no_edit() -> None:
    answer = classify(OLD, _edited(lambda _d: None), TABLE)

    assert (answer.labels, answer.result, answer.counted_try) == ((), Result.NONE, False)


def test_the_highest_result_wins_and_every_edit_keeps_its_pointer() -> None:
    def three(document: Doc) -> None:
        document["title"] = "Renamed"
        document["numbers"]["min_trend_strength"]["default"] = "0.0010"
        document["numbers"]["ema_period"]["default"] = "120"
        document["exit_set"][1]["block"] = "target-atr@1"

    answer = classify(OLD, _edited(three), TABLE)

    assert answer.result is Result.NEW_UNIT
    assert {(edit.label, edit.path) for edit in answer.edits} == {
        (EditLabel.TITLE_CHANGE, "/title"),
        (EditLabel.MOTION_INSIDE_RANGE, "/numbers/min_trend_strength/default"),
        (EditLabel.FIXED_VALUE_CHANGE, "/numbers/ema_period/default"),
        (EditLabel.BLOCK_SWAP, "/exit_set/target_2r/block"),
    }
    assert [edit.label for edit in diff(OLD, _edited(three))][0] is EditLabel.TITLE_CHANGE


def test_his_table_decides_and_a_label_it_lacks_counts_as_a_new_unit() -> None:
    his = parse_table(
        [
            _row("fixed_value_change", "calibration_row", False, False),
            _row("title_change", "none", False, False),
        ]
    )
    value = classify(OLD, _edited(_numbers("ema_period", "default", "120")), his)
    swap = classify(OLD, _edited(_set("exit_set", 0, "block", value="atr-stop@1")), his)

    assert (value.result, value.counted_try, value.unlisted) == (Result.CALIBRATION_ROW, False, ())
    assert (swap.result, swap.click_before_live) == (Result.NEW_UNIT, True)
    assert swap.unlisted == (EditLabel.BLOCK_SWAP,)


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ("not a list", "units.identity_table is a list of rows"),
        (
            [_row("colour_change", "none", False, False)],
            "units.identity_table row 1 names label 'colour_change', which no edit has",
        ),
        (
            [_row("title_change", "maybe", False, False)],
            "units.identity_table row 1 has result 'maybe'; use one of none, calibration_row, "
            "new_version, new_unit",
        ),
        (
            [{**_row("title_change", "none", False, False), "counted_try": "no"}],
            "units.identity_table row 1: counted_try and click_before_live are true or false",
        ),
        (
            [_row("title_change", "none", False, False)] * 2,
            "units.identity_table names title_change twice",
        ),
    ],
)
def test_a_table_qml_cannot_read_is_refused_naming_the_row(rows: object, message: str) -> None:
    with pytest.raises(IdentityTableError) as refused:
        parse_table(rows)

    assert str(refused.value) == message
