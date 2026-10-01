"""Cross-boundary QML characterizations through public author/runtime APIs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeVar, cast

from qmf.core.chrono import CalendarIdentity, Instant
from qmf.core.exact import ExactRational, UnitKind
from qmf.core.fingerprint import fingerprint
from qmf.core.refusal import Result, TypedRefusal, is_ok, is_refusal
from qml.declaration import mint_bot_definition, mint_confluence
from qml.footprint import (
    ProducerBinding,
    mint_footprint,
    mint_producer_template,
    report_completeness,
    resolve_template,
)
from qml.logic import mint_logic_identity
from qml.protocol import (
    FootprintEvidence,
    HostedBot,
    MappingReadSurface,
    PresenceState,
    construct_bot,
    resolve_assignment,
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


def _definition(*, confluences: object = None):
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
            confluence_set=[confluence] if confluences is None else confluences,
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


def test_factory_initialization_rejects_foreign_frame_before_construction() -> None:
    instant = _instant(15)
    surface = _ok(MappingReadSurface.try_create({instant: _series("present", instant, 1)}))
    factory = _CapturingFactory([])
    refused = construct_bot(
        factory,
        declaration=_definition(),
        assignment={"lookback": 5},
        read_surfaces={
            "primary": surface,
            "foreign-feed": surface,
        },
    )
    assert is_refusal(refused)
    assert factory.assignment is None


def test_factory_refusal_and_callback_exception_keep_their_boundary() -> None:
    class RefusingFactory:
        def construct(self, **kwargs: object) -> TypedRefusal:
            del kwargs
            refused = resolve_assignment(_definition(), {"lookback": 0})
            assert is_refusal(refused)
            return refused

    refused = construct_bot(
        RefusingFactory(),
        declaration=_definition(),
        assignment={"lookback": 5},
        read_surfaces={},
    )
    assert is_refusal(refused)
    assert refused.context["field"] == "assignment"

    class RaisingFactory:
        def construct(self, **kwargs: object) -> object:
            del kwargs

            class Callback:
                def on_instant(self, evidence: FootprintEvidence) -> object:
                    del evidence
                    raise RuntimeError("callback sentinel")

            return Callback()

    bot = _ok(
        construct_bot(
            RaisingFactory(),
            declaration=_definition(),
            assignment={"lookback": 5},
            read_surfaces={},
        )
    )
    try:
        bot.on_instant(_instant(20))
    except RuntimeError as error:
        assert str(error) == "callback sentinel"
    else:
        raise AssertionError("callback exceptions are not converted into empty output")


def test_confluence_order_and_repetition_reach_bot_identity_and_parameter_bounds() -> None:
    left = _ok(ProducerBinding.try_create(_ok(fingerprint({"producer": "left"}))))
    right = _ok(ProducerBinding.try_create(_ok(fingerprint({"producer": "right"}))))
    leg_a = {"role": "level", "producer_binding": left}
    leg_b = {"role": "trigger", "producer_binding": right}
    default_ab = _ok(mint_confluence([leg_a, leg_b]))
    default_ba = _ok(mint_confluence([leg_b, leg_a]))
    ordered_ab = _ok(mint_confluence([leg_a, leg_b], order_significance=True))
    ordered_ba = _ok(mint_confluence([leg_b, leg_a], order_significance=True))
    assert _ok(default_ab.fingerprint_content()) == _ok(default_ba.fingerprint_content())
    assert _ok(ordered_ab.fingerprint_content()) != _ok(ordered_ba.fingerprint_content())

    repeated = _ok(mint_confluence([leg_a, leg_a]))
    assert len(repeated.legs) == 2
    assert _ok(repeated.fingerprint_content()) != _ok(
        _ok(mint_confluence([leg_a])).fingerprint_content()
    )
    duplicate_ordinal = mint_confluence(
        [{**leg_a, "display_ordinal": 0}, {**leg_a, "display_ordinal": 0}]
    )
    assert is_refusal(duplicate_ordinal)

    bot_ab = _definition(confluences=[default_ab])
    bot_ba = _definition(confluences=[default_ba])
    bot_ordered_ab = _definition(confluences=[ordered_ab])
    bot_ordered_ba = _definition(confluences=[ordered_ba])
    assert _ok(bot_ab.fingerprint_content()) == _ok(bot_ba.fingerprint_content())
    assert _ok(bot_ordered_ab.fingerprint_content()) != _ok(bot_ordered_ba.fingerprint_content())

    assert is_ok(resolve_assignment(bot_ab, {"lookback": 1}))
    assert is_ok(resolve_assignment(bot_ab, {"lookback": 20}))
    assert is_refusal(resolve_assignment(bot_ab, {"lookback": 0}))
    assert is_refusal(resolve_assignment(bot_ab, {"lookback": 21}))


def test_resolved_template_retains_budget_and_foreign_source_identity() -> None:
    period = _ok(ExactRational.try_create(5, 1, UnitKind.COUNT))
    base: dict[str, object] = {
        "formula_id": "sma",
        "contract_format_version": 1,
        "inputs": [
            {
                "name": "close",
                "source": {"kind": "instrument", "venue": "fixture", "symbol": "EURUSD"},
                "bar_spec": {"kind": "time-interval", "seconds": 60},
                "channel_kind": "exact-price",
                "quote_side": "mid",
            }
        ],
        "calendar_requirements": [
            _ok(CalendarIdentity.try_create("fixture-calendar", "v1", "2026a"))
        ],
        "alignment_policy": "as-of",
        "missing_value_policy": "mark-gap",
        "warm_up": 5,
        "output_schema": [
            {
                "name": "sma",
                "channel_kind": "float-analytic",
                "arity": "scalar-per-sample",
                "index_offset": 0,
            }
        ],
        "supported_modes": ["batch", "streaming"],
        "arithmetic_reference_configuration": {
            "c_library": "lib@sha256:1",
            "python_wrapper": "wrapper@sha256:2",
            "reference_configuration": {"mode": "classic"},
        },
        "space_bound": {"period": "lookback"},
        "declared_budget": {
            "per_update_cost_rung": "bounded",
            "bounded_state": True,
            "window_or_anchor_rule": "rolling-window",
            "synchronous_availability": True,
        },
    }
    template = _ok(mint_producer_template(base))
    resolved = _ok(resolve_template(template, {"lookback": period}))
    assert resolved.declared_budget == template.declared_budget
    assert resolved.parameters["period"] == period
    assert is_refusal(resolve_template(template, {"lookback": "5"}))

    template_binding = _ok(ProducerBinding.try_create(template))
    template_leg = _ok(mint_confluence([{"role": "level", "producer_binding": template_binding}]))
    stream = [
        {
            "instrument_role": "primary",
            "bar_specs": [{"kind": "time-interval", "seconds": 60}],
            "stream_role": "trading",
        }
    ]
    calendar = base["calendar_requirements"]
    complete_template = _ok(mint_footprint(stream, calendar, [template_binding]))
    template_report = _ok(
        report_completeness(complete_template, template_leg.completeness_legs())
    )
    assert template_report.complete
    resolved_fp = _ok(resolved.fingerprint_content())
    resolved_binding = _ok(ProducerBinding.try_create(resolved_fp))
    pinned_resolved = _ok(mint_footprint(stream, calendar, [resolved_binding]))
    mismatched_report = _ok(
        report_completeness(pinned_resolved, template_leg.completeness_legs())
    )
    assert not mismatched_report.complete
    assert mismatched_report.missing and mismatched_report.extra

    missing_identity = dict(base)
    del missing_identity["output_schema"]
    layer1_refusal = mint_producer_template(missing_identity)
    assert is_refusal(layer1_refusal)
    assert layer1_refusal.context["layer"] == 1

    wrong_binding = {**base, "space_bound": {"period": "other_parameter"}}
    wrong_template = _ok(mint_producer_template(wrong_binding))
    assert is_refusal(resolve_template(wrong_template, {"lookback": period}))
    assert is_ok(resolve_template(wrong_template, {"other_parameter": period}))

    inputs = cast(list[dict[str, object]], base["inputs"])
    foreign_instrument = {
        **base,
        "inputs": [
            {
                **inputs[0],
                "source": {"kind": "instrument", "venue": "fixture", "symbol": "GBPUSD"},
            }
        ],
    }
    foreign_calendar = {
        **base,
        "calendar_requirements": [
            _ok(CalendarIdentity.try_create("foreign-calendar", "v1", "2026a"))
        ],
    }
    changed_instrument = _ok(
        resolve_template(_ok(mint_producer_template(foreign_instrument)), {"lookback": period})
    )
    changed_calendar = _ok(
        resolve_template(_ok(mint_producer_template(foreign_calendar)), {"lookback": period})
    )
    base_fp = _ok(resolved.fingerprint_content())
    assert base_fp != _ok(changed_instrument.fingerprint_content())
    assert base_fp != _ok(changed_calendar.fingerprint_content())
