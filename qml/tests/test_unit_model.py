"""The unit document ``qmx.unit/1``: the dummy parses, broken documents name every problem,
and the committed schema is the generated one (Part A slice A2)."""

from __future__ import annotations

import copy
import json
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest
from qml.unit import ProblemKind, parse, parse_text, schema
from qml.unit.model import NumberParam, Origin, SlotsSide

_UNIT = Path(__file__).resolve().parents[1] / "src" / "qml" / "unit"
_DUMMY_TEXT = (_UNIT / "templates" / "dummy-trend-pullback.json").read_text("utf-8")


def _dummy() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(_DUMMY_TEXT))


def test_the_dummy_parses_with_zero_problems() -> None:
    parsed = parse_text(_DUMMY_TEXT)

    assert parsed.problems == ()
    unit = parsed.unit
    assert unit is not None
    assert unit.unit_id == "dummy-trend-pullback"
    assert [market.market_id for market in unit.markets] == ["fx.eurusd", "metal.xauusd"]
    assert unit.streams[0].bar.size == Decimal("900")
    assert isinstance(unit.logic.short, SlotsSide)
    assert unit.logic.short.slots["trigger"].bindings[0].params["level"] == NumberParam("rsi_high")
    assert unit.sizer is not None and str(unit.sizer.block) == "fixed-fraction-at-stop@2"
    assert [str(binding.block) for binding in unit.exit_set] == [
        "swing-stop-buffer@1",
        "target-r-multiple@1",
        "time-exit-bars@1",
    ]
    floor = unit.numbers["min_trend_strength"]
    assert floor.range is not None and floor.range.max == Decimal("0.0030")
    assert floor.motion.min_count == 20
    assert {name for name, spec in unit.numbers.items() if spec.origin is Origin.PLACEHOLDER} == {
        "stop_buffer",
        "target_r",
        "time_out_bars",
        "risk_fraction",
    }


def _parent(document: dict[str, Any], path: str) -> tuple[Any, str]:
    *parents, last = path.split("/")
    target: Any = document
    for part in parents:
        target = target[int(part) if part.isdigit() else part]
    return target, last


def _set(path: str, value: object) -> Any:
    def edit(document: dict[str, Any]) -> None:
        target, last = _parent(document, path)
        target[last] = value

    return edit


def _drop(path: str) -> Any:
    def edit(document: dict[str, Any]) -> None:
        target, last = _parent(document, path)
        del target[last]

    return edit


def _many(*edits: Any) -> Any:
    def edit(document: dict[str, Any]) -> None:
        for one in edits:
            one(document)

    return edit


_SESSION = {
    "name": "london",
    "calendar_ref": "fx",
    "zone": "Europe/London",
    "windows": [{"from": "9:30", "to": "16:00"}],
}

MALFORMED = [
    ("wrong marker", _set("schema", "qmx.unit/2"), {("not_in_vocabulary", "/schema")}),
    ("no unit id", _drop("unit_id"), {("missing_field", "/unit_id")}),
    ("misspelt field", _set("exit_sets", []), {("unknown_field", "/exit_sets")}),
    (
        "float where a decimal string goes",
        _set("numbers/ema_period/range/min", 20.5),
        {("wrong_type", "/numbers/ema_period/range/min")},
    ),
    (
        "exponent decimal",
        _set("numbers/stop_buffer/range/step", "1e-2"),
        {("not_decimal", "/numbers/stop_buffer/range/step")},
    ),
    (
        "block without version",
        _set("logic/long/slots/context/bindings/0/block", "ema"),
        {("bad_ref", "/logic/long/slots/context/bindings/0/block")},
    ),
    (
        "symbol and root together",
        _set("markets/0/instrument_ref/root", "6E"),
        {("no_shape_matches", "/markets/0/instrument_ref")},
    ),
    ("exit without scope", _drop("exit_set/1/scope"), {("missing_field", "/exit_set/1/scope")}),
    (
        "role outside the vocabulary",
        _set("logic/long/slots/trigger/role", "entry"),
        {("not_in_vocabulary", "/logic/long/slots/trigger/role")},
    ),
    (
        "four problems at once",
        _many(
            _set("streams/0/bar/kind", "minute"),
            _set("position_limit", {"per_instrument": 0}),
            _set("sessions", [_SESSION]),
            _drop("claim_card/sources"),
        ),
        {
            ("not_in_vocabulary", "/streams/0/bar/kind"),
            ("too_small", "/position_limit/per_instrument"),
            ("bad_format", "/sessions/0/windows/0/from"),
            ("missing_field", "/claim_card/sources"),
        },
    ),
]


@pytest.mark.parametrize(("name", "edit", "expected"), MALFORMED, ids=[m[0] for m in MALFORMED])
def test_a_malformed_document_names_every_problem_with_its_pointer(
    name: str, edit: Any, expected: set[tuple[str, str]]
) -> None:
    document = _dummy()
    edit(document)

    parsed = parse(copy.deepcopy(document))

    assert parsed.unit is None, name
    assert {(p.kind.value, p.where[0]) for p in parsed.problems} == expected
    assert all(p.layer == "A" and p.message and p.hint for p in parsed.problems)


def test_text_that_is_not_json_is_one_problem() -> None:
    parsed = parse_text('{"schema": "qmx.unit/1",')

    assert parsed.unit is None
    assert [(p.kind, p.where) for p in parsed.problems] == [(ProblemKind.NOT_JSON, ("",))]


def test_the_committed_schema_is_the_generated_one() -> None:
    committed = json.loads((_UNIT / "qmx.unit.1.schema.json").read_text("utf-8"))

    assert committed == schema()
    assert committed["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert committed["properties"]["schema"] == {"type": "string", "enum": ["qmx.unit/1"]}


def _filled_from(spec: dict[str, Any]) -> dict[str, Any]:
    """The same walk as ``filled_from`` in qmx-library's ``tests/test_view.py``, which saves
    the smallest item of every kind; QML may not import that package."""
    properties = cast(dict[str, dict[str, Any]], spec.get("properties") or {})
    filled: dict[str, Any] = {}
    for name in cast(list[str], spec.get("required") or []):
        field = properties.get(name, {})
        if "enum" in field:
            filled[name] = field["enum"][0]
        elif "required" in field:
            filled[name] = _filled_from(field)
        elif field.get("type") == "integer":
            filled[name] = 1
        elif field.get("type") == "array":
            filled[name] = []
        elif field.get("type") == "object":
            filled[name] = {}
        else:
            filled[name] = f"{name}-1"
    return filled


def test_the_library_schema_minimal_unit_is_a_valid_draft() -> None:
    smallest = _filled_from(schema())

    assert smallest == {
        "schema": "qmx.unit/1",
        "unit_id": "unit_id-1",
        "family_id": "family_id-1",
        "claim_card": {"idea": "idea-1", "sources": [], "written_at": "written_at-1"},
        "markets": [],
        "streams": [],
        "direction": "long",
        "logic": {},
        "exit_set": [],
        "halts": {},
        "reads": [],
        "numbers": {},
        "pins": [],
    }
    assert parse(smallest).problems == ()
