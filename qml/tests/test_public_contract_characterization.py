"""Cross-boundary QML characterizations through public author/runtime APIs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeVar

from qmf.core.chrono import CalendarIdentity, Instant
from qmf.core.exact import UnitKind
from qmf.core.fingerprint import fingerprint
from qmf.core.refusal import Result, is_ok, is_refusal
from qml.declaration import mint_bot_definition, mint_confluence
from qml.footprint import ProducerBinding, mint_footprint
from qml.logic import mint_logic_identity
from qml.protocol import (
    FootprintEvidence,
    HostedBot,
    MappingReadSurface,
    PresenceState,
    construct_bot,
)

T = TypeVar("T")
_BASE_NS = 1_800_000_000_000_000_000
_SOURCE = {
    "probe/__init__.py": "",
    "probe/bot.py": "def on_instant(self, evidence):\n    return ()\n",
}


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _instant(offset: int) -> Instant:
    return _ok(Instant.try_create(_BASE_NS + offset))


def _definition():
    producer = _ok(
        ProducerBinding.try_create(_ok(fingerprint({"kind": "fixture-producer"})))
    )
    calendar = _ok(CalendarIdentity.try_create("fixture-calendar", "v1", "2026a"))
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
    confluence = _ok(
        mint_confluence([{"role": "level", "producer_binding": producer}])
    )
    logic = _ok(mint_logic_identity("fixture-family", "1.0.0", _SOURCE))
    return _ok(
        mint_bot_definition(
            strategy_family_id="fixture-family",
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


class _Callback:
    def __init__(self, seen: list[FootprintEvidence]) -> None:
        self.seen = seen

    def on_instant(self, evidence: FootprintEvidence) -> object:
        self.seen.append(evidence)
        return ()


class _CapturingFactory:
    def __init__(self, seen: list[FootprintEvidence]) -> None:
        self.seen = seen
        self.assignment: Mapping[str, object] | None = None
        self.surface_keys: frozenset[str] = frozenset()

    def construct(
        self,
        *,
        declaration: object,
        assignment: Mapping[str, object],
        read_surfaces: Mapping[str, object],
    ) -> _Callback:
        assert declaration is not None
        self.assignment = assignment
        self.surface_keys = frozenset(read_surfaces)
        return _Callback(self.seen)


def _series(presence: str, instant: Instant, value: object = None) -> dict[str, object]:
    sample: dict[str, object] = {"presence": presence, "knowable_at": instant}
    if value is not None:
        sample["value"] = value
    return {"kind": "series", "samples": [sample]}


def test_factory_binding_and_runtime_keep_each_absence_state_at_its_frontier() -> None:
    declaration = _definition()
    first, second, third = (_instant(n) for n in (1, 2, 3))
    surface = _ok(
        MappingReadSurface.try_create(
            {
                first: _series("absent_by_schedule", first),
                second: _series("present", second, 7),
            }
        )
    )
    seen: list[FootprintEvidence] = []
    factory = _CapturingFactory(seen)
    supplied_assignment: dict[str, object] = {"lookback": 7}
    bot = _ok(
        construct_bot(
            factory,
            declaration=declaration,
            assignment=supplied_assignment,
            read_surfaces={"primary": surface},
        )
    )
    supplied_assignment["lookback"] = 19

    assert isinstance(bot, HostedBot)
    assert factory.assignment == {"lookback": 7}
    assert bot.assignment == {"lookback": 7}
    assert factory.surface_keys == frozenset({"primary"})
    assert _ok(bot.on_instant(first)) == ()
    assert _ok(bot.on_instant(second)) == ()
    assert _ok(bot.on_instant(third)) == ()

    first_samples = seen[0].series["primary"].samples
    second_samples = seen[1].series["primary"].samples
    assert len(first_samples) == 1
    assert first_samples[0].presence is PresenceState.ABSENT_BY_SCHEDULE
    assert first_samples[0].value is None
    assert first_samples[0].knowable_at == first
    assert second_samples[0].presence is PresenceState.PRESENT
    assert second_samples[0].value == 7
    assert second_samples[0].knowable_at == second
    # A missing frame means no observation; it is distinct from a reported gap.
    assert "primary" not in seen[2].series


def test_hosted_callback_refuses_future_sample_without_invoking_logic() -> None:
    evaluation, future = _instant(10), _instant(11)
    surface = _ok(
        MappingReadSurface.try_create(
            {evaluation: _series("present", future, 3)}
        )
    )
    seen: list[FootprintEvidence] = []
    bot = _ok(
        construct_bot(
            _CapturingFactory(seen),
            declaration=_definition(),
            assignment={"lookback": 5},
            read_surfaces={"primary": surface},
        )
    )

    refused = bot.on_instant(evaluation)
    assert is_refusal(refused)
    assert seen == []
