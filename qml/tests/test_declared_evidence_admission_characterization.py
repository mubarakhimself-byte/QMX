"""Public QL-7 read-surface admission and callback evidence boundaries."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TypeVar, cast

import pytest
from qmf.core import CalendarIdentity, ExactRational, Instant, UnitKind, fingerprint
from qmf.core.refusal import Result, is_ok, is_refusal
from qml.declaration import BotDefinition, mint_bot_definition, mint_confluence
from qml.footprint import ProducerBinding, mint_footprint
from qml.logic import mint_logic_identity
from qml.protocol import (
    FootprintEvidence,
    FunctionFactory,
    HostedBot,
    MappingReadSurface,
    construct_bot,
)

T = TypeVar("T")
_SOURCE = {
    "evidence_bot/__init__.py": "",
    "evidence_bot/bot.py": "def on_instant(evidence):\n    return ()\n",
}


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _instant(ns: int) -> Instant:
    return _ok(Instant.try_create(ns))


def _binding(name: str) -> ProducerBinding:
    return _ok(ProducerBinding.try_create(_ok(fingerprint({"producer": name}))))


def _declaration() -> tuple[BotDefinition, str]:
    calendar = _ok(CalendarIdentity.try_create("evidence-calendar", "v1", "2026a"))
    producer = _binding("sma:close")
    confluence = _ok(mint_confluence([{"role": "level", "producer_binding": producer}]))
    footprint = _ok(
        mint_footprint(
            [
                {
                    "instrument_role": "primary",
                    "bar_specs": [{"kind": "time-interval", "seconds": 60}],
                    "stream_role": "trading",
                }
            ],
            [calendar],
            [producer],
        )
    )
    logic = _ok(mint_logic_identity("evidence-boundary", "1.0.0", _SOURCE))
    declaration = _ok(
        mint_bot_definition(
            strategy_family_id="evidence-boundary",
            confluence_set=[confluence],
            parameter_space=[
                {
                    "name": "lookback",
                    "type": "exact integer",
                    "bounds": {"min": 1, "max": 20},
                    "step": 1,
                    "default": 5,
                    "unit_kind": UnitKind.COUNT,
                    "ui": "ui-editable",
                }
            ],
            footprint=footprint,
            permitted_exit_intents=(),
            logic_reference=logic,
        )
    )
    producer_key = _ok(producer.fingerprint_content()).value
    return declaration, producer_key


def _series(
    instant: Instant,
    value: object,
    *,
    producer_key: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "kind": "series",
        "samples": [{"presence": "present", "knowable_at": instant, "value": value}],
    }
    if producer_key is not None:
        payload["producer_key"] = producer_key
    return payload


def _fold(instant: Instant, *, producer_key: str, geometry: object) -> dict[str, object]:
    return {
        "kind": "structure_fold",
        "producer_key": producer_key,
        "knowable_at": instant,
        "observed_at": instant,
        "geometry": geometry,
    }


def _hosted_bot(
    callback: Callable[[FootprintEvidence], object],
    declaration: BotDefinition,
    read_surfaces: Mapping[str, object],
) -> HostedBot:
    return _ok(
        construct_bot(
            FunctionFactory(logic=callback),
            declaration=declaration,
            assignment={"lookback": 5},
            read_surfaces=read_surfaces,
        )
    )


def test_recorded_frontiers_reach_callback_only_at_their_own_instant() -> None:
    declaration, producer_key = _declaration()
    first, gap, later = (_instant(ns) for ns in (10, 11, 12))
    exact = _ok(ExactRational.try_create(3, 2, UnitKind.DIMENSIONLESS_RATIO))
    seen: list[FootprintEvidence] = []
    bot = _hosted_bot(
        lambda evidence: seen.append(evidence) or (),
        declaration,
        {
            "primary": _ok(
                MappingReadSurface.try_create(
                    {
                        first: _series(first, exact),
                        later: _series(later, 9),
                    }
                )
            ),
            producer_key: _ok(
                MappingReadSurface.try_create(
                    {
                        first: _fold(
                            first,
                            producer_key=producer_key,
                            geometry={"anchor": {"price_units": 100}},
                        ),
                        later: _fold(
                            later,
                            producer_key=producer_key,
                            geometry={"anchor": {"price_units": 120}},
                        ),
                    }
                )
            ),
        },
    )

    _ok(bot.on_instant(first))
    _ok(bot.on_instant(gap))
    _ok(bot.on_instant(later))

    assert len(seen) == 3
    assert seen[0].series["primary"].samples[0].value == exact
    first_geometry = cast(
        Mapping[str, object], seen[0].structure_folds[producer_key].geometry["anchor"]
    )
    assert first_geometry["price_units"] == 100
    assert "primary" not in seen[1].series
    assert producer_key not in seen[1].structure_folds
    assert seen[2].series["primary"].samples[0].value == 9
    later_geometry = cast(
        Mapping[str, object], seen[2].structure_folds[producer_key].geometry["anchor"]
    )
    assert later_geometry["price_units"] == 120


@pytest.mark.parametrize("kind", ("series", "structure_fold"))
def test_surface_payload_cannot_relabel_another_declared_producer(kind: str) -> None:
    declaration, producer_key = _declaration()
    instant = _instant(20)
    seen: list[FootprintEvidence] = []
    if kind == "series":
        key = "primary"
        payload: object = _series(instant, 1, producer_key="foreign-producer")
    else:
        key = producer_key
        payload = _fold(
            instant,
            producer_key="foreign-producer",
            geometry={"level": 1},
        )
    surface = _ok(MappingReadSurface.try_create({instant: payload}))
    bot = _hosted_bot(lambda evidence: seen.append(evidence) or (), declaration, {key: surface})

    refused = bot.on_instant(instant)
    assert is_refusal(refused)
    assert seen == []


def test_provisional_sample_refuses_at_callback_boundary() -> None:
    declaration, _ = _declaration()
    instant = _instant(30)
    seen: list[FootprintEvidence] = []
    surface = _ok(
        MappingReadSurface.try_create(
            {
                instant: {
                    "kind": "series",
                    "samples": [{"presence": "provisional", "knowable_at": instant, "value": 7}],
                }
            }
        )
    )
    bot = _hosted_bot(
        lambda evidence: seen.append(evidence) or (), declaration, {"primary": surface}
    )

    refused = bot.on_instant(instant)
    assert is_refusal(refused)
    assert seen == []


def test_requested_r_is_refused_as_a_read_surface_before_bot_construction() -> None:
    declaration, _ = _declaration()
    instant = _instant(40)
    invoked: list[object] = []
    surface = _ok(MappingReadSurface.try_create({instant: _series(instant, 1)}))

    refused = construct_bot(
        FunctionFactory(logic=lambda evidence: invoked.append(evidence) or ()),
        declaration=declaration,
        assignment={"lookback": 5},
        read_surfaces={"requested_r": surface},
    )
    assert is_refusal(refused)
    assert invoked == []


@pytest.mark.parametrize("raw_ns", (True, "bad", 2**63))
def test_invalid_nominal_knowable_at_refuses_before_callback(raw_ns: object) -> None:
    declaration, _ = _declaration()
    evaluation = _instant(50)
    malformed = Instant(cast(int, raw_ns))
    seen: list[FootprintEvidence] = []
    surface = _ok(
        MappingReadSurface.try_create(
            {evaluation: _series(malformed, 1)}
        )
    )
    bot = _hosted_bot(
        lambda evidence: seen.append(evidence) or (),
        declaration,
        {"primary": surface},
    )

    refused = bot.on_instant(evaluation)
    assert is_refusal(refused)
    cause = cast(Mapping[str, object], refused.context["cause"])
    assert cause["field"] == "knowable_at"
    assert "int64" in str(cause["reason"])
    assert seen == []


@pytest.mark.parametrize("raw_ns", (True, "bad", 2**63))
def test_invalid_nominal_evaluation_instant_refuses_before_callback(raw_ns: object) -> None:
    declaration, _ = _declaration()
    malformed = Instant(cast(int, raw_ns))
    seen: list[FootprintEvidence] = []
    surface = _ok(
        MappingReadSurface.try_create(
            {malformed: _series(malformed, 1)}
        )
    )
    bot = _hosted_bot(
        lambda evidence: seen.append(evidence) or (),
        declaration,
        {"primary": surface},
    )

    refused = bot.on_instant(malformed)
    assert is_refusal(refused)
    assert refused.context["field"] == "evaluation_instant"
    assert "int64" in str(refused.context["reason"])
    assert seen == []


def test_valid_signed_int64_instant_endpoints_remain_admissible() -> None:
    declaration, _ = _declaration()
    seen: list[FootprintEvidence] = []
    for ns in (-(2**63), 2**63 - 1):
        instant = _ok(Instant.try_create(ns))
        surface = _ok(
            MappingReadSurface.try_create(
                {instant: _series(instant, ns)}
            )
        )
        bot = _hosted_bot(
            lambda evidence: seen.append(evidence) or (),
            declaration,
            {"primary": surface},
        )
        assert is_ok(bot.on_instant(instant))
    assert len(seen) == 2
