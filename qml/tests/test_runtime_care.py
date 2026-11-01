"""A restart or an upgrade never silently changes what a unit does (A10)."""
# pyright: reportPrivateUsage=false

from __future__ import annotations

import copy
import dataclasses
import json
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

import pytest
from qmf.core.chrono import Instant
from qmf.core.refusal import TypedRefusal
from qml.check import check
from qml.environment import EnvironmentProblem, environment_check
from qml.protocol.unit import OHLC, QuoteBar, SeamCheck, UnitStep, restore_unit, seam_check
from qml.unit.upgrade import upgrade
from test_compile_dummy import (
    _compiled,
    _context,
    _document,
    _drive,
    _host,
    _instants,
    _ok,
    _slice,
    _surfaces,
    _target,
    _with_default,
)

_QML = Path(__file__).resolve().parents[1]

# --- restore -------------------------------------------------------------------------------


def _changed(snapshot: Mapping[str, object], key: str, value: object) -> dict[str, object]:
    changed = copy.deepcopy(dict(snapshot))
    changed[key] = value
    return changed


def _without_cold_start(steps: list[UnitStep]) -> list[UnitStep]:
    return [
        dataclasses.replace(
            s, state_events=tuple(e for e in s.state_events if e.kind != "cold_start")
        )
        for s in steps
    ]


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ("fingerprint", "the snapshot belongs to another compiled fingerprint"),
        ("schema", "state schema 1, this door reads 2"),
        ("python", "the snapshot was taken under Python 3.13, this is Python 3.14"),
    ],
)
def test_a_snapshot_that_differs_restores_cold_with_its_reason(change: str, reason: str) -> None:
    bars = _slice()
    instants = _instants(bars)
    compiled = _compiled()
    head = _host(compiled, _surfaces(bars))
    _drive(head, instants[:300])
    snapshot = head.snapshot()
    target = compiled
    match change:
        case "fingerprint":
            target = _compiled(_with_default("ema_period", "99"))
        case "schema":
            snapshot = _changed(snapshot, "state_schema_version", 1)
        case _:
            snapshot = _changed(snapshot, "environment", {"python": "3.13"})

    cold = _ok(
        restore_unit(
            snapshot,
            target,
            read_surfaces=_surfaces(bars),
            scope_id="run-a5",
            execution_target=_target(),
        )
    )
    steps = _drive(cold, instants[:300])

    assert [(e.kind, e.market_id, e.reason) for e in steps[0].state_events][:2] == [
        ("cold_start", "fx.eurusd", reason),
        ("cold_start", "metal.xauusd", reason),
    ]
    fresh = _drive(_host(target, _surfaces(bars)), instants[:300])
    assert _without_cold_start(steps) == fresh, "a cold start is a fresh start, never a guess"


def test_a_snapshot_records_the_interpreter_and_resumes_warm_under_it() -> None:
    bars = _slice()
    instants = _instants(bars)
    compiled = _compiled()
    head = _host(compiled, _surfaces(bars))
    _drive(head, instants[:300])
    snapshot = head.snapshot()

    warm = _ok(
        restore_unit(
            snapshot,
            compiled,
            read_surfaces=_surfaces(bars),
            scope_id="run-a5",
            execution_target=_target(),
        )
    )

    assert (snapshot["state_schema_version"], snapshot["environment"]) == (2, {"python": "3.14"})
    assert all(
        e.kind != "cold_start" for s in _drive(warm, instants[300:310]) for e in s.state_events
    )


# --- the warm-up seam -----------------------------------------------------------------------


def _bar(n: int, open_: str, close: str) -> QuoteBar:
    price = OHLC(Decimal(open_), Decimal(open_), Decimal(close), Decimal(close))
    return QuoteBar(Instant(n * 900_000_000_000), price, price)


_TAIL = [_bar(1, "1.1000", "1.1000"), _bar(2, "1.1000", "1.1010"), _bar(3, "1.1010", "1.1000")]


def test_a_five_atr_jump_at_the_seam_flags_and_a_half_atr_join_does_not() -> None:
    assert _ok(seam_check(_TAIL, _bar(4, "1.1050", "1.1050"))) == SeamCheck(True, Decimal(5))
    assert _ok(seam_check(_TAIL, _bar(4, "1.0995", "1.1000"))) == SeamCheck(False, Decimal("0.5"))
    assert _ok(seam_check(_TAIL, _bar(4, "1.1050", "1.1050"), Decimal(6))).flag is False


def test_a_seam_with_nothing_to_scale_by_is_refused() -> None:
    flat = [_bar(1, "1.1000", "1.1000"), _bar(2, "1.1000", "1.1000")]

    assert isinstance(seam_check(_TAIL[:1], _bar(2, "1.1", "1.1")), TypedRefusal)
    assert isinstance(seam_check(flat, _bar(3, "1.2", "1.2")), TypedRefusal)


# --- the interpreter --------------------------------------------------------------------------


def test_python_3_13_gets_one_plain_words_problem_naming_3_14() -> None:
    assert environment_check((3, 13, 2)) == (
        EnvironmentProblem(
            "python",
            "QML needs Python 3.14.x, and this is Python 3.13.2. "
            "Install Python 3.14 and recreate this environment with it.",
        ),
    )
    assert environment_check((3, 14, 6), talib="0.7.1") == ()
    assert environment_check() == ()


def test_a_wrong_talib_build_is_named() -> None:
    assert environment_check((3, 14, 0), talib="0.6.4") == (
        EnvironmentProblem(
            "talib",
            "QML's indicators are checked against TA-Lib 0.7.1, and this machine has "
            "TA-Lib 0.6.4. Install TA-Lib 0.7.1.",
        ),
    )


# --- upgrades -------------------------------------------------------------------------------


def _committed() -> list[tuple[str, dict[str, object]]]:
    paths = [
        *sorted((_QML / "src" / "qml" / "unit" / "templates").glob("*.json")),
        *sorted((_QML / "tests" / "corpus").glob("*.json")),
        *sorted((_QML / "src" / "qml" / "blocks" / "stdlib").glob("*/*/entry.json")),
    ]
    found = [(p.relative_to(_QML).as_posix(), json.loads(p.read_text("utf-8"))) for p in paths]
    return [*found, ("a check result", check(_document(), _context()).to_json())]


def test_every_committed_version_1_document_loads_through_the_upgrader() -> None:
    committed = _committed()
    loaded = [(name, upgrade(document)) for name, document in committed]

    assert len(committed) == 15
    assert [(name, _ok(result)) for name, result in loaded] == committed


@pytest.mark.parametrize(
    ("schema", "reason"),
    [
        ("qmx.unit/2", "qmx.unit/2 is newer than this QML reads (qmx.unit/1); update QML"),
        ("qmx.recipe/1", "qmx.recipe/1 is not a family this QML reads"),
    ],
)
def test_a_document_this_qml_cannot_read_is_refused_by_name(schema: str, reason: str) -> None:
    document = _document() | {"schema": schema}

    refused = upgrade(document)

    assert isinstance(refused, TypedRefusal)
    assert refused.context["reason"] == reason
