"""Public footprint and producer-template identity behavior."""

from __future__ import annotations

from typing import TypeVar

from qmf.core import CalendarIdentity, ExactRational, Fingerprint, Instrument, UnitKind, VenueId
from qmf.core.refusal import Result, is_ok, is_refusal
from qml.footprint import mint_footprint, mint_producer_template, resolve_template

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _calendar(name: str = "ny-17") -> CalendarIdentity:
    return _ok(CalendarIdentity.try_create(name, "v3", "2026a"))


def _parameter(value: int, unit: UnitKind = UnitKind.COUNT) -> ExactRational:
    return _ok(ExactRational.try_create(value, 1, unit))


def _template_fields(
    *,
    source: object | None = None,
    bar_spec: object | None = None,
    calendar: CalendarIdentity | None = None,
    declared_budget: object | None = None,
) -> dict[str, object]:
    fields: dict[str, object] = {
        "formula_id": "sma",
        "contract_format_version": 1,
        "inputs": [
            {
                "name": "close",
                "source": source
                if source is not None
                else {"kind": "instrument", "venue": "venue-one", "symbol": "EURUSD"},
                "bar_spec": bar_spec
                if bar_spec is not None
                else {"kind": "time-interval", "seconds": 60},
                "channel_kind": "exact-price",
                "quote_side": "mid",
            }
        ],
        "calendar_requirements": [calendar or _calendar()],
        "alignment_policy": "as-of",
        "missing_value_policy": "mark-gap",
        "warm_up": 5,
        "output_schema": [
            {
                "name": "mean",
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
    }
    if declared_budget is not None:
        fields["declared_budget"] = declared_budget
    return fields


def test_typed_and_canonical_instrument_sources_share_template_identity() -> None:
    venue = _ok(VenueId.try_create("venue-one"))
    typed_instrument = _ok(Instrument.try_create(venue, "EURUSD"))
    typed = _ok(mint_producer_template(_template_fields(source=typed_instrument)))
    canonical = _ok(mint_producer_template(_template_fields()))
    assert _ok(typed.fingerprint_content()) == _ok(canonical.fingerprint_content())

    source_id = _ok(mint_producer_template(_template_fields(source="derived:spread")))
    foreign_venue = _ok(
        mint_producer_template(
            _template_fields(
                source={"kind": "instrument", "venue": "venue-two", "symbol": "EURUSD"}
            )
        )
    )
    assert _ok(source_id.fingerprint_content()) != _ok(canonical.fingerprint_content())
    assert _ok(foreign_venue.fingerprint_content()) != _ok(canonical.fingerprint_content())
    assert is_refusal(mint_producer_template(_template_fields(source="  ")))


def test_barspec_reference_and_embedded_identity_are_distinct_and_stable() -> None:
    bar_spec = {"kind": "time-interval", "seconds": 60}
    embedded = _ok(mint_producer_template(_template_fields(bar_spec=bar_spec)))
    same_embedded = _ok(
        mint_producer_template(
            _template_fields(bar_spec={"seconds": 60, "kind": "time-interval"})
        )
    )
    spec_fp = _ok(Fingerprint.try_create("fp1:sha256:" + "a" * 64))
    referenced = _ok(mint_producer_template(_template_fields(bar_spec=spec_fp)))

    assert _ok(embedded.fingerprint_content()) == _ok(same_embedded.fingerprint_content())
    assert _ok(embedded.fingerprint_content()) != _ok(referenced.fingerprint_content())
    assert is_refusal(mint_producer_template(_template_fields(bar_spec="1 minute")))
    assert is_refusal(
        mint_footprint(
            [{"instrument_role": "primary", "bar_specs": ["timeframe"], "stream_role": "trading"}],
            [_calendar()],
            [],
        )
    )


def test_resolved_parameter_identity_retains_exact_value_and_unit() -> None:
    template = _ok(mint_producer_template(_template_fields()))
    five = _ok(resolve_template(template, {"lookback": _parameter(5)}))
    reordered_extra = _ok(
        resolve_template(template, {"unused": _parameter(99), "lookback": _parameter(5)})
    )
    six = _ok(resolve_template(template, {"lookback": _parameter(6)}))
    wrong_unit = _ok(
        resolve_template(
            template,
            {"lookback": _parameter(5, UnitKind.DIMENSIONLESS_RATIO)},
        )
    )

    assert _ok(five.fingerprint_content()) == _ok(reordered_extra.fingerprint_content())
    assert _ok(five.fingerprint_content()) != _ok(six.fingerprint_content())
    assert _ok(five.fingerprint_content()) != _ok(wrong_unit.fingerprint_content())
    assert is_refusal(resolve_template(template, {"lookback": 5.0}))


def test_budget_boolean_contract_and_changes_are_part_of_resolved_identity() -> None:
    budget: dict[str, object] = {
        "per_update_cost_rung": "bounded",
        "bounded_state": True,
        "window_or_anchor_rule": "rolling-window",
        "synchronous_availability": True,
    }
    base_template = _ok(mint_producer_template(_template_fields(declared_budget=budget)))
    base = _ok(resolve_template(base_template, {"lookback": _parameter(5)}))

    changed_budget = {**budget, "synchronous_availability": False}
    changed_template = _ok(
        mint_producer_template(_template_fields(declared_budget=changed_budget))
    )
    changed = _ok(resolve_template(changed_template, {"lookback": _parameter(5)}))

    assert _ok(base.fingerprint_content()) != _ok(changed.fingerprint_content())
    for field in ("bounded_state", "synchronous_availability"):
        malformed = {**budget, field: 1}
        assert is_refusal(mint_producer_template(_template_fields(declared_budget=malformed)))
