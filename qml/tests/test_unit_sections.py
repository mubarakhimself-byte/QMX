"""One function splits a unit into a logic half and a risk half, each with its own fingerprint.

AD-2: anything not named as risk is logic, a number bound by a logic slot or an exit is logic,
a reading a logic slot names is logic, and only `recipe` sits outside both.
"""
# pyright: reportPrivateUsage=false

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from qml.compile import COMPILER_FORMAT_VERSION
from qml.unit.sections import sections
from test_compile_dummy import _compiled, _document

Document = dict[str, Any]

_FORGOTTEN = (
    "baseline",
    "claim_card",
    "context_needs",
    "family_id",
    "lineage",
    "plain_python",
    "routes",
    "title",
    "unit_id",
)
"""AD-2's nine fields that are in neither of its named lists."""

_READ = {
    "reading": "news@1",
    "market": "fx.eurusd",
    "fallback": "treat_as_absent",
    "stale_after_s": 60,
}


def _numbers(section: Any) -> Mapping[str, object]:
    return cast("Mapping[str, object]", section.fields["numbers"])


def test_a_size_edit_moves_only_the_risk_fingerprint() -> None:
    before = _compiled(_document())
    raised = _document()
    numbers = cast("dict[str, dict[str, object]]", raised["numbers"])
    numbers["risk_fraction"]["default"] = "0.01"
    after = _compiled(raised)

    assert after.document_fingerprint != before.document_fingerprint, "the edit did not land"
    assert after.logic_fingerprint.value == before.logic_fingerprint.value
    assert after.risk_fingerprint.value != before.risk_fingerprint.value
    assert after.compiled_fingerprint.value != before.compiled_fingerprint.value


def test_a_forgotten_field_falls_in_logic() -> None:
    document = _document()
    document["baseline"] = "trend-pullback"
    document["context_needs"] = {"require": [], "warn": [], "block": []}
    document["lineage"] = {"parents": []}
    document["plain_python"] = {"block": "ema@1"}
    document["routes"] = {"data": {}}
    document["recipe"] = {"pod_id": "trend", "version": 1, "hash": "abc", "displaced": []}

    logic, risk = sections(document, COMPILER_FORMAT_VERSION)

    for name in _FORGOTTEN:
        assert name in logic.fields, f"{name} fell between the two halves"
    assert set(logic.fields) | set(risk.fields) == set(document) - {"recipe"}
    assert set(logic.fields) & set(risk.fields) <= {"numbers", "pins", "reads"}
    assert "recipe" not in logic.fields
    assert "recipe" not in risk.fields


def test_a_number_bound_in_both_halves_is_logic() -> None:
    document = _document()
    exits = cast("list[dict[str, object]]", document["exit_set"])
    cast("dict[str, dict[str, str]]", exits[1]["params"])["multiple"] = {"number": "risk_fraction"}

    logic, risk = sections(document, COMPILER_FORMAT_VERSION)

    number = cast("Mapping[str, object]", _numbers(logic)["risk_fraction"])
    assert number["default"] == "0.005"
    assert "risk_fraction" not in _numbers(risk)
    assert _numbers(risk) == {}


def test_a_reading_a_logic_slot_names_is_logic() -> None:
    document = _document()
    document["reads"] = [_READ]
    context = cast("dict[str, Any]", document["logic"])["long"]["slots"]["context"]["bindings"][0]
    context["inputs"] = {"series": "reading:news:fx.eurusd"}

    logic, risk = sections(document, COMPILER_FORMAT_VERSION)

    assert [row["reading"] for row in cast("list[Document]", logic.fields["reads"])] == ["news@1"]
    assert risk.fields["reads"] == []

    untouched = _document()
    untouched["reads"] = [_READ]
    logic, risk = sections(untouched, COMPILER_FORMAT_VERSION)
    assert logic.fields["reads"] == []
    assert [row["reading"] for row in cast("list[Document]", risk.fields["reads"])] == ["news@1"]
