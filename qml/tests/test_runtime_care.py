"""A restart or an upgrade never silently changes what a unit does (A10)."""
# pyright: reportPrivateUsage=false

from __future__ import annotations

import copy
import dataclasses
import json
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any

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


Edit = Callable[[dict[str, Any]], None]


def _put(value: object, *path: str) -> Edit:
    def edit(snapshot: dict[str, Any]) -> None:
        node = snapshot
        for step in path[:-1]:
            node = node[step]
        node[path[-1]] = value

    return edit


def _drop(*path: str) -> Edit:
    def edit(snapshot: dict[str, Any]) -> None:
        node = snapshot
        for step in path[:-1]:
            node = node[step]
        del node[path[-1]]

    return edit


def _empty_every_blocks(snapshot: dict[str, Any]) -> None:
    for market in snapshot["markets"].values():
        market["blocks"] = {}


_SHAPE = "the snapshot does not hold this unit's state"
_EURUSD_BLOCKS = (
    "derived.long.rsi_low, derived.short.rsi_high, long.exit.swing_stop, long.exit.target_2r, "
    "long.next_open, long.rsi_cross, long.strength, long.trend, short.exit.swing_stop, "
    "short.exit.target_2r, short.next_open, short.rsi_cross, short.strength, short.trend, sizer"
)
_DROPPED_BLOCKS = (
    "long.trend",
    "long.rsi_cross",
    "short.trend",
    "short.strength",
    "short.rsi_cross",
    "derived.long.rsi_low",
    "derived.short.rsi_high",
)


def _without_cold_start(steps: list[UnitStep]) -> list[UnitStep]:
    return [
        dataclasses.replace(
            s, state_events=tuple(e for e in s.state_events if e.kind != "cold_start")
        )
        for s in steps
    ]


@pytest.mark.parametrize(
    ("edit", "reason"),
    [
        pytest.param(
            None, "the snapshot belongs to another compiled fingerprint", id="fingerprint"
        ),
        pytest.param(
            _put(2, "state_schema_version"), "state schema 2, this door reads 3", id="schema"
        ),
        pytest.param(
            _put({"python": "3.13"}, "environment"),
            "the snapshot was taken under Python 3.13, this is Python 3.14",
            id="python",
        ),
        pytest.param(
            _put("3.14", "environment"),
            "the snapshot does not record its interpreter, this is Python 3.14",
            id="string-environment",
        ),
        *(
            pytest.param(
                _drop("markets", "fx.eurusd", "blocks", key),
                f"{_SHAPE} (markets.fx.eurusd.blocks lacks {key})",
                id=f"missing-{key}",
            )
            for key in _DROPPED_BLOCKS
        ),
        pytest.param(
            _empty_every_blocks,
            f"{_SHAPE} (markets.fx.eurusd.blocks lacks {_EURUSD_BLOCKS})",
            id="emptied-blocks",
        ),
        pytest.param(
            _put({}, "markets", "fx.eurusd", "blocks", "long.extra"),
            f"{_SHAPE} (markets.fx.eurusd.blocks has unknown long.extra)",
            id="unknown-block",
        ),
        pytest.param(
            _drop("slow", "min_trend_strength"),
            f"{_SHAPE} (slow lacks min_trend_strength)",
            id="missing-slow-entry",
        ),
        pytest.param(_put({}, "slow"), f"{_SHAPE} (slow lacks min_trend_strength)", id="no-slow"),
        pytest.param(_drop("markets"), f"{_SHAPE} (it lacks markets)", id="missing-markets"),
        pytest.param(
            _drop("markets", "metal.xauusd"),
            f"{_SHAPE} (markets lacks metal.xauusd)",
            id="missing-market",
        ),
        pytest.param(
            _drop("markets", "fx.eurusd", "exited"),
            f"{_SHAPE} (markets.fx.eurusd lacks exited)",
            id="missing-exited",
        ),
        pytest.param(
            _put({"middle": {}}, "markets", "fx.eurusd", "derived"),
            f"{_SHAPE} (markets.fx.eurusd.derived has unknown middle)",
            id="unknown-derived-side",
        ),
        pytest.param(
            _put({"pos-1": {}}, "markets", "fx.eurusd", "timers"),
            f"{_SHAPE} (markets.fx.eurusd.timers.pos-1 lacks exit.time_out)",
            id="malformed-timer",
        ),
    ],
)
def test_a_snapshot_that_differs_restores_cold_with_its_reason(
    edit: Edit | None, reason: str
) -> None:
    bars = _slice()
    instants = _instants(bars)
    compiled = _compiled()
    head = _host(compiled, _surfaces(bars))
    _drive(head, instants[:300])
    snapshot = copy.deepcopy(dict(head.snapshot()))
    target = compiled
    if edit is None:
        target = _compiled(_with_default("ema_period", "99"))
    else:
        edit(snapshot)

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

    assert (snapshot["state_schema_version"], snapshot["environment"]) == (3, {"python": "3.14"})
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

    stdlib = list((_QML / "src" / "qml" / "blocks" / "stdlib").glob("*/*/entry.json"))
    templates, corpus, a_check = 2, 3, 1
    assert len(committed) == templates + corpus + len(stdlib) + a_check
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
