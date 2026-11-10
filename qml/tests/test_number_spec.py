"""RC-23: every number says where it came from, who may move it, and why it holds.

The seam list is the PR section's Verify, unit box. Every assertion goes through the door a
person or a host uses: ``check`` for the two named problems, ``explain`` for the line a person
reads, ``parse`` for the shape, and ``compile_unit`` for a field the compiled format refuses.
"""
# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest
from qml.check import check
from qml.compile import compile_unit
from qml.door import explain
from qml.unit import parse
from qml.unit.model import Authority, Origin

from test_compile_dummy import _context, _document

_QML = Path(__file__).resolve().parents[1]
_TEMPLATES = _QML / "src" / "qml" / "unit" / "templates"
_SHAPES = ("canary", "dummy-trend-pullback")

Document = dict[str, Any]


def _template(name: str) -> Document:
    """A shipped template with every QML block it names pinned, as a host gathers it."""
    document = cast("Document", json.loads((_TEMPLATES / f"{name}.json").read_text("utf-8")))
    document["pins"] = _document()["pins"]
    return document


def _numbers(document: Document) -> dict[str, dict[str, Any]]:
    return cast("dict[str, dict[str, Any]]", document["numbers"])


def _put(document: Document, path: str, value: object) -> None:
    *parents, last = path.split("/")
    target: Any = document
    for part in parents:
        target = target[int(part)] if part.isdigit() else target[part]
    target[last] = value


def _drop(document: Document, path: str) -> None:
    *parents, last = path.split("/")
    target: Any = document
    for part in parents:
        target = target[int(part)] if part.isdigit() else target[part]
    del target[last]


def test_k9_5_every_number_has_a_reason_and_range() -> None:
    labelled = _document()
    assert check(labelled, _context()).errors == ()

    no_reason = _document()
    _put(no_reason, "numbers/risk_fraction/reason", "")
    refused_reason = check(no_reason, _context())

    no_range = _document()
    _drop(no_range, "numbers/time_out_bars/range")
    refused_range = check(no_range, _context())

    assert {(p.kind.value, p.where[0]) for p in refused_reason.errors} == {
        ("number_no_reason", "/numbers/risk_fraction/reason")
    }
    assert {(p.kind.value, p.where[0]) for p in refused_range.errors} == {
        ("number_no_range", "/numbers/time_out_bars/range")
    }


def test_a_template_number_reads_its_label() -> None:
    document = _template("canary")

    lines = explain(document, _context())

    said = [line for line in lines if line.startswith("number risk_fraction:")]
    assert len(said) == 1, lines
    line = said[0]
    assert "default 0.005" in line
    assert "range 0.0001 to 0.05 by 0.0001" in line
    assert "origin placeholder" in line
    assert "owner numbers talk" in line
    assert "unargued until the numbers talk" in line


@pytest.mark.parametrize(
    ("name", "origins"),
    [
        ("canary", {"placeholder"}),
        ("dummy-trend-pullback", {"placeholder", "published_convention", "builder_chosen"}),
    ],
)
def test_every_shipped_number_says_who_may_move_it_and_why(name: str, origins: set[str]) -> None:
    document = _template(name)

    numbers = _numbers(document)

    assert len(numbers) == 10, sorted(numbers)
    for number, spec in numbers.items():
        assert spec.get("reason"), f"{name}/{number} states no reason"
        assert spec.get("owner") == "numbers talk", f"{name}/{number} names no owner"
        assert spec.get("origin") in origins, f"{name}/{number} states {spec.get('origin')}"
        assert {"min", "max", "step"} <= set(cast("dict[str, Any]", spec["range"]))


def test_a_number_reads_back_every_field_it_states() -> None:
    document = _template("canary")
    _put(
        document,
        "numbers/stop_buffer",
        {
            "kind": "fixed",
            "measure": "percent",
            "default": "0.0002",
            "motion": {"mode": "fixed"},
            "authority": "at_anchor",
            "origin": "found_by_replay",
            "range": {"min": "0", "max": "0.01", "step": "0.0001"},
            "derivation": "own-r-step@1",
            "owner": "numbers talk",
            "reason": "a starting buffer",
            "cautious": "down",
            "guard": {"revert_after": 3, "freeze_after": 5},
            "never_self_tune": True,
            "stage_values": {"stage_2": "0.0003"},
        },
    )

    parsed = parse(document)

    assert parsed.problems == ()
    assert parsed.unit is not None
    spec = parsed.unit.numbers["stop_buffer"]
    assert (spec.authority, spec.cautious.value, spec.origin) == (
        Authority.AT_ANCHOR,
        "down",
        Origin.FOUND_BY_REPLAY,
    )
    assert spec.derivation == "own-r-step@1"
    assert spec.owner == "numbers talk"
    assert spec.reason == "a starting buffer"
    assert spec.never_self_tune is True
    assert dict(spec.stage_values) == {"stage_2": "0.0003"}
    assert spec.guard is not None and (spec.guard.revert_after, spec.guard.freeze_after) == (3, 5)


def test_an_old_number_reads_with_no_reason_and_no_owner() -> None:
    document = _template("canary")
    for spec in _numbers(document).values():
        for key in ("reason", "owner", "derivation", "cautious", "guard", "never_self_tune"):
            spec.pop(key, None)
        spec["stage_values"] = {}

    parsed = parse(document)

    assert parsed.problems == ()
    assert parsed.unit is not None
    spec = parsed.unit.numbers["risk_fraction"]
    assert (spec.reason, spec.owner, spec.derivation) == ("", "", None)
    assert (spec.cautious.value, spec.guard, spec.never_self_tune) == ("hold", None, False)


UNRUN = [
    (
        "derivation",
        "numbers/stop_buffer/derivation",
        "own-r-step@1",
        "derivation_not_built",
    ),
    ("guard", "numbers/stop_buffer/guard", {"revert_after": 3, "freeze_after": 5}, "guard_not_built"),
    ("cautious", "numbers/stop_buffer/cautious", "down", "cautious_not_built"),
    (
        "never_self_tune",
        "numbers/min_trend_strength/never_self_tune",
        True,
        "never_self_tune_not_built",
    ),
    (
        "stage_values",
        "numbers/stop_buffer/stage_values",
        {"stage_2": "0.0003"},
        "stage_values_not_built",
    ),
    ("authority", "numbers/stop_buffer/authority", "at_anchor", "authority_not_built"),
]


@pytest.mark.parametrize(("field", "path", "value", "code"), UNRUN, ids=[row[0] for row in UNRUN])
def test_a_number_field_the_format_does_not_run_is_refused_by_name(
    field: str, path: str, value: object, code: str
) -> None:
    document = _document()
    _put(document, path, value)

    built = compile_unit(document, _context())

    assert isinstance(built, tuple), f"{field} compiled unread"
    assert [(problem.kind, problem.where) for problem in built] == [(code, f"/{path}")]


def test_a_number_that_may_not_move_cannot_name_a_motion_rule() -> None:
    document = _document()
    _put(document, "numbers/min_trend_strength/authority", "off")

    built = compile_unit(document, _context())

    assert isinstance(built, tuple)
    assert [(problem.kind, problem.where) for problem in built] == [
        ("authority_not_built", "/numbers/min_trend_strength/authority")
    ]
