"""CT-33 nominal Bot definitions receive the same admission as mappings."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import TypeVar, cast

from qmf.core import (
    CalendarIdentity,
    Result,
    UnitKind,
    fingerprint,
    is_ok,
    is_refusal,
)
from qml.declaration import BotDefinition, ParameterSpec, mint_bot_definition, mint_confluence
from qml.families import mint_strategy_family
from qml.footprint import ProducerBinding, mint_footprint
from qml.logic import mint_logic_identity
from qml.protocol.factory import construct_bot

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _bot() -> BotDefinition:
    family = _ok(mint_strategy_family("nominal-admission-family"))
    producer_fp = _ok(fingerprint({"class": "nominal-test-producer"}))
    producer = _ok(ProducerBinding.try_create(producer_fp))
    confluence = _ok(mint_confluence([{"role": "level", "producer_binding": producer}]))
    calendar = _ok(CalendarIdentity.try_create("nominal-calendar", "v1", "2026a"))
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
    logic = _ok(
        mint_logic_identity(
            "nominal-admission-bot", "1.0.0", {"bot.py": "def on_instant(): pass\n"}
        )
    )
    return _ok(
        mint_bot_definition(
            strategy_family_id=family.family_id.value,
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


class _CountingFactory:
    def __init__(self) -> None:
        self.calls = 0

    def construct(
        self,
        *,
        declaration: object,
        assignment: Mapping[str, object],
        read_surfaces: Mapping[str, object],
    ) -> object:
        del declaration, assignment, read_surfaces
        self.calls += 1
        return _Callback()


class _Callback:
    def on_instant(self, evidence: object) -> tuple[()]:
        del evidence
        return ()


def test_nominal_and_mapping_bot_admission_match_before_factory_effects() -> None:
    declaration = _bot()
    factory = _CountingFactory()
    nominal = construct_bot(
        factory,
        declaration=declaration,
        assignment={"lookback": 5},
        read_surfaces={},
    )
    assert is_ok(nominal)
    mapping = construct_bot(
        factory,
        declaration=declaration.identity_payload(),
        assignment={"lookback": 5},
        read_surfaces={},
    )
    assert is_ok(mapping)
    assert factory.calls == 2

    invalid_nominals = (
        replace(declaration, logic_reference=None),
        replace(declaration, kind_format_version=True),
        replace(declaration, kind_format_version=0),
        replace(declaration, kind_format_version="1"),
        replace(
            declaration,
            parameter_space=(replace(declaration.parameter_space[0], unit_kind=True),),
        ),
        replace(
            declaration,
            parameter_space=(replace(declaration.parameter_space[0], default=True),),
        ),
    )
    for invalid_declaration in invalid_nominals:
        refused = construct_bot(
            factory,
            declaration=invalid_declaration,
            assignment={"lookback": 5},
            read_surfaces={},
        )
        assert is_refusal(refused)
        assert factory.calls == 2

    for field, bad_value in (
        ("logic_reference", None),
        ("contract_format_version", True),
        ("contract_format_version", 0),
        ("contract_format_version", "1"),
    ):
        payload = declaration.identity_payload()
        cast(dict[str, object], payload["body"])["format_version"] = 1
        if field == "logic_reference":
            cast(dict[str, object], payload["body"])[field] = bad_value
        else:
            payload[field] = bad_value
        refused = construct_bot(
            factory,
            declaration=payload,
            assignment={"lookback": 5},
            read_surfaces={},
        )
        assert is_refusal(refused)
        assert factory.calls == 2

    valid_parameter = declaration.parameter_space[0]
    assert isinstance(valid_parameter, ParameterSpec)
    for changed_parameter in (
        replace(valid_parameter, unit_kind=True),
        replace(valid_parameter, default=True),
    ):
        malformed_nested = replace(declaration, parameter_space=(changed_parameter,))
        refused = construct_bot(
            factory,
            declaration=malformed_nested,
            assignment={"lookback": 5},
            read_surfaces={},
        )
        assert is_refusal(refused)
        assert factory.calls == 2


def test_valid_wrapped_bot_header_is_admitted_and_invalid_header_is_not_masked() -> None:
    declaration = _bot()
    factory = _CountingFactory()
    payload = {
        "kind": "bot-definition",
        "contract_format_version": 1,
        "body": {**declaration.body(), "format_version": 1},
    }
    admitted = construct_bot(
        factory,
        declaration=payload,
        assignment={"lookback": 5},
        read_surfaces={},
    )
    assert is_ok(admitted)
    assert factory.calls == 1

    for malformed_header in (True, 0, "1"):
        malformed = dict(payload)
        malformed["contract_format_version"] = malformed_header
        refused = construct_bot(
            factory,
            declaration=malformed,
            assignment={"lookback": 5},
            read_surfaces={},
        )
        assert is_refusal(refused)
        assert factory.calls == 1
