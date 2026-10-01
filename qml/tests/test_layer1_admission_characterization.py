"""Public Layer 1 admission and parameter/source identity contracts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeVar, cast

from qmf.core import CalendarIdentity, ExactRational, Fingerprint, UnitKind, fingerprint
from qmf.core.refusal import Result, is_ok, is_refusal
from qml.conformance import Layer1Verdict, lint_declaration
from qml.declaration import BotDefinition, mint_bot_definition, mint_confluence
from qml.families import mint_strategy_family
from qml.footprint import (
    ProducerBinding,
    mint_footprint,
    mint_producer_template,
    resolve_template,
)
from qml.logic import mint_logic_identity
from qml.protocol import resolve_assignment

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _fp(tag: str) -> Fingerprint:
    return _ok(fingerprint({"class": "layer1-admission-fixture", "tag": tag}))


def _calendar(token: str = "fixture-calendar") -> CalendarIdentity:
    return _ok(CalendarIdentity.try_create(token, "v1", "2026a"))


def _parameter(name: str, *, type_: str, default: object, unit: UnitKind) -> dict[str, object]:
    if type_ == "exact integer":
        return {
            "name": name,
            "type": type_,
            "bounds": {"min": 1, "max": 20},
            "step": 1,
            "default": default,
            "unit_kind": unit,
            "ui": "ui-editable",
        }
    if type_ == "exact rational":
        return {
            "name": name,
            "type": type_,
            "bounds": {
                "min": _ok(ExactRational.try_create(1, 4, unit)),
                "max": _ok(ExactRational.try_create(4, 1, unit)),
            },
            "step": _ok(ExactRational.try_create(1, 4, unit)),
            "default": default,
            "unit_kind": unit,
            "ui": "ui-editable",
        }
    return {
        "name": name,
        "type": type_,
        "default": default,
        "unit_kind": unit,
        "ui": "uneditable",
    }


def _template_fields(
    *, source_symbol: str = "EURUSD", calendar_token: str = "fixture-calendar"
) -> dict[str, object]:
    return {
        "formula_id": "sma",
        "contract_format_version": 1,
        "inputs": [
            {
                "name": "close",
                "source": {"kind": "instrument", "venue": "fixture", "symbol": source_symbol},
                "bar_spec": {"kind": "time-interval", "seconds": 60},
                "channel_kind": "exact-price",
                "quote_side": "mid",
            }
        ],
        "calendar_requirements": [_calendar(calendar_token)],
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
    }


def _world(
    *, template_fields: Mapping[str, object] | None = None, bool_default: object = False
) -> tuple[BotDefinition, dict[str, object]]:
    producer = _ok(ProducerBinding.try_create(_fp("zone")))
    template = _ok(
        mint_producer_template(_template_fields() if template_fields is None else template_fields)
    )
    template_binding = _ok(ProducerBinding.try_create(template))
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
            [_calendar()],
            [producer, template_binding],
        )
    )
    family = _ok(mint_strategy_family("layer1-characterization"))
    logic = _ok(
        mint_logic_identity(
            "layer1-characterization",
            "1.0.0",
            {
                "layer1_bot/__init__.py": "",
                "layer1_bot/bot.py": "def on_instant(evidence):\n    return ()\n",
            },
        )
    )
    bot = _ok(
        mint_bot_definition(
            {
                "strategy_family_id": family.family_id.value,
                "confluence_set": [confluence],
                "parameter_space": [
                    _parameter("lookback", type_="exact integer", default=5, unit=UnitKind.COUNT),
                    _parameter(
                        "enabled", type_="boolean", default=bool_default, unit=UnitKind.COUNT
                    ),
                    _parameter(
                        "risk_fraction",
                        type_="exact rational",
                        default=_ok(ExactRational.try_create(1, 2, UnitKind.DIMENSIONLESS_RATIO)),
                        unit=UnitKind.DIMENSIONLESS_RATIO,
                    ),
                ],
                "footprint": footprint,
                "permitted_exit_intents": (),
                "logic_reference": logic,
            }
        )
    )
    catalogs: dict[str, object] = {
        "family_catalog": [family],
        "confluence_catalog": [confluence],
        "producer_catalog": [producer],
        "formula_catalog": [{"formula_id": "sma", "contract_format_version": 1}],
        "logic_catalog": [logic],
    }
    return bot, catalogs


def _admit(bot: object, catalogs: Mapping[str, object]) -> Result[Layer1Verdict]:
    return lint_declaration(
        bot,
        family_catalog=catalogs["family_catalog"],
        confluence_catalog=catalogs["confluence_catalog"],
        producer_catalog=catalogs["producer_catalog"],
        formula_catalog=catalogs["formula_catalog"],
        logic_catalog=catalogs["logic_catalog"],
    )


def test_layer1_admits_boolean_parameter_without_integer_aliasing() -> None:
    bot, catalogs = _world(bool_default=False)
    verdict = _ok(_admit(bot, catalogs))
    assert verdict.declaration is bot
    half_price = _ok(ExactRational.try_create(1, 2, UnitKind.DIMENSIONLESS_RATIO))
    assert bot.canonical_assignment() == {
        "lookback": 5,
        "enabled": False,
        "risk_fraction": half_price,
    }
    assert is_ok(
        resolve_assignment(
            bot,
            {
                "lookback": 20,
                "enabled": True,
                "risk_fraction": _ok(ExactRational.try_create(1, 1, UnitKind.DIMENSIONLESS_RATIO)),
            },
        )
    )
    for integer_alias in (0, 1):
        assert is_refusal(
            resolve_assignment(
                bot,
                {"lookback": 5, "enabled": integer_alias, "risk_fraction": half_price},
            )
        )
    assert is_refusal(
        resolve_assignment(
            bot,
            {"lookback": True, "enabled": False, "risk_fraction": half_price},
        )
    )


def test_layer1_boolean_default_and_parameter_unit_errors_are_typed() -> None:
    bool_as_integer = {
        **_parameter("lookback", type_="exact integer", default=True, unit=UnitKind.COUNT),
    }
    bot, catalogs = _world()
    bool_bot_payload = bot.identity_payload()
    body = cast(dict[str, object], bool_bot_payload["body"])
    body["parameter_space"] = [
        bool_as_integer,
        _parameter("enabled", type_="boolean", default=False, unit=UnitKind.COUNT),
        _parameter(
            "risk_fraction",
            type_="exact rational",
            default=_ok(ExactRational.try_create(1, 2, UnitKind.DIMENSIONLESS_RATIO)),
            unit=UnitKind.DIMENSIONLESS_RATIO,
        ),
    ]
    bool_bot_payload["body"] = body
    refused = _admit(bool_bot_payload, catalogs)
    assert is_refusal(refused)
    assert refused.context.get("field") == "default"
    assert refused.context.get("layer") == 1
    assert refused.context.get("journal") is True

    wrong_unit = _ok(ExactRational.try_create(1, 2, UnitKind.R_MULTIPLE))
    refused_assignment = resolve_assignment(
        bot,
        {
            "lookback": 5,
            "enabled": False,
            "risk_fraction": wrong_unit,
        },
    )
    assert is_refusal(refused_assignment)
    assert refused_assignment.context.get("field") == "assignment"


def test_resolved_template_fp_tracks_space_binding_source_and_calendar() -> None:
    bot, catalogs = _world()
    assert is_ok(_admit(bot, catalogs))
    period_5 = _ok(ExactRational.try_create(5, 1, UnitKind.COUNT))
    period_8 = _ok(ExactRational.try_create(8, 1, UnitKind.COUNT))
    template = _ok(mint_producer_template(_template_fields()))
    resolved_5 = _ok(resolve_template(template, {"lookback": period_5}))
    resolved_8 = _ok(resolve_template(template, {"lookback": period_8}))
    assert _ok(resolved_5.fingerprint_content()) != _ok(resolved_8.fingerprint_content())
    assert is_refusal(resolve_template(template, {"lookback": "5"}))
    assert is_refusal(resolve_template(template, {"other_parameter": period_5}))

    source_changed = _ok(
        resolve_template(
            _ok(mint_producer_template(_template_fields(source_symbol="GBPUSD"))),
            {"lookback": period_5},
        )
    )
    calendar_changed = _ok(
        resolve_template(
            _ok(mint_producer_template(_template_fields(calendar_token="foreign-calendar"))),
            {"lookback": period_5},
        )
    )
    source_fp = _ok(resolved_5.fingerprint_content())
    assert source_fp != _ok(source_changed.fingerprint_content())
    assert source_fp != _ok(calendar_changed.fingerprint_content())


def test_layer1_rejects_malformed_source_and_boolean_index_offset() -> None:
    malformed_source = _template_fields()
    malformed_inputs = list(cast(list[object], malformed_source["inputs"]))
    source_input = cast(Mapping[str, object], malformed_inputs[0])
    malformed_inputs[0] = {
        **source_input,
        "source": {"kind": "instrument", "venue": "fixture"},
    }
    malformed_source["inputs"] = malformed_inputs
    source_refusal = mint_producer_template(malformed_source)
    assert is_refusal(source_refusal)
    assert source_refusal.context.get("field") == "inputs"
    cause = source_refusal.context.get("cause")
    assert isinstance(cause, Mapping)
    cause_mapping = cast(Mapping[str, object], cause)
    assert cause_mapping.get("field") == "source"

    malformed_offset = _template_fields()
    malformed_schema = list(cast(list[object], malformed_offset["output_schema"]))
    output_channel = cast(Mapping[str, object], malformed_schema[0])
    malformed_schema[0] = {**output_channel, "index_offset": True}
    malformed_offset["output_schema"] = malformed_schema
    bot, _catalogs = _world()
    bot_payload = bot.identity_payload()
    body = cast(dict[str, object], bot_payload["body"])
    footprint = cast(dict[str, object], body["footprint"])
    bindings = list(cast(list[object], footprint["producer_bindings"]))
    bindings[1] = {"form": "template", "template": malformed_offset}
    body["footprint"] = {**footprint, "producer_bindings": bindings}
    bot_payload["body"] = body
    decoy: dict[str, object] = {
        "producer_bindings": [{}, {"form": "template", "template": {}}],
        **bot_payload,
    }
    for declaration in (bot_payload, decoy):
        offset_refusal = lint_declaration(declaration)
        assert is_refusal(offset_refusal)
        refusal_context: Mapping[str, object] = offset_refusal.context
        nested_fields = ("producer_bindings", "output_schema", "index_offset")
        for index, expected_field in enumerate(nested_fields):
            assert refusal_context.get("field") == expected_field
            if index < len(nested_fields) - 1:
                cause = refusal_context.get("cause")
                assert isinstance(cause, Mapping)
                refusal_context = cast(Mapping[str, object], cause)
        assert "integer position" in str(refusal_context.get("reason"))
        assert offset_refusal.context.get("layer") == 1
        assert offset_refusal.context.get("journal") is True
