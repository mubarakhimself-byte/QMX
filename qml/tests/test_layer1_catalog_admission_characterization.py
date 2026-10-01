"""Public Layer 1 admission against host-supplied registry catalogs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import TypeVar, cast

from qmf.core import CalendarIdentity, Fingerprint, Instant, UnitKind, WriterId, fingerprint
from qmf.core.refusal import RefusalCategory, Result, is_ok, is_refusal
from qmf.registry import RegistrationRecord
from qml.conformance import Layer1Verdict, lint_declaration
from qml.declaration import (
    KIND_CONFLUENCE,
    BotDefinition,
    mint_bot_definition,
    mint_confluence,
)
from qml.families import (
    KIND_STRATEGY_FAMILY,
    mint_strategy_family,
)
from qml.footprint import ProducerBinding, mint_footprint, mint_producer_template
from qml.logic import LogicIdentity, mint_logic_identity

T = TypeVar("T")
_SOURCE = {
    "catalog_bot/__init__.py": "",
    "catalog_bot/bot.py": "def on_instant(evidence):\n    return ()\n",
}


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _fp(tag: str) -> Fingerprint:
    return _ok(fingerprint({"producer": tag}))


def _binding(tag: str) -> ProducerBinding:
    return _ok(ProducerBinding.try_create(_fp(tag)))


def _record(kind: str, body: Mapping[str, object], sequence: int) -> RegistrationRecord:
    writer = _ok(WriterId.try_create("qml-catalog", "authoring", kind, "boot-1"))
    created_at = _ok(Instant.try_create(1_700_000_000_000_000_000 + sequence))
    return _ok(RegistrationRecord.try_create(kind, 1, (), body, writer, sequence, created_at))


def _recording_world(
    *,
    footprint_bindings: tuple[ProducerBinding, ...] | None = None,
    cited: object = None,
) -> dict[str, object]:
    family = _ok(mint_strategy_family("catalog-family"))
    binding = _binding("catalog-producer")
    confluence = _ok(mint_confluence([{"role": "level", "producer_binding": binding}]))
    footprint = _ok(
        mint_footprint(
            [
                {
                    "instrument_role": "primary",
                    "bar_specs": [{"kind": "time-interval", "seconds": 60}],
                    "stream_role": "trading",
                }
            ],
            [_ok(CalendarIdentity.try_create("catalog-calendar", "v1", "2026a"))],
            footprint_bindings or (binding,),
        )
    )
    logic = _ok(mint_logic_identity("catalog-bot", "1.0.0", _SOURCE))
    declaration = _ok(
        mint_bot_definition(
            strategy_family_id=family.family_id.value,
            confluence_set=[confluence if cited is None else cited],
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
    confluence_fp = _ok(confluence.fingerprint_content())
    producer_fp = _ok(binding.fingerprint_content())
    family_record = _record(KIND_STRATEGY_FAMILY, family.body(), 0)
    confluence_record = _record(KIND_CONFLUENCE, confluence.body(), 1)
    return {
        "family": family,
        "family_record": family_record,
        "binding": binding,
        "producer_fp": producer_fp,
        "confluence": confluence,
        "confluence_fp": confluence_fp,
        "confluence_record": confluence_record,
        "logic": logic,
        "declaration": declaration,
        "catalogs": {
            "family_catalog": {family.family_id.value: family_record},
            "confluence_catalog": {confluence_fp.value: confluence_record},
            "producer_catalog": {producer_fp.value: binding},
            "formula_catalog": (),
            "logic_catalog": {logic.distribution: logic.as_logic_reference()},
        },
    }


def _lint(world: Mapping[str, object], **changes: object) -> Result[Layer1Verdict]:
    kwargs = dict(cast(Mapping[str, object], world["catalogs"]))
    kwargs.update(changes)
    return lint_declaration(world["declaration"], **kwargs)


def test_registered_records_and_mapping_indexes_resolve_the_same_content() -> None:
    world = _recording_world()
    verdict = _ok(_lint(world))
    assert isinstance(verdict, Layer1Verdict)
    assert verdict.declaration is world["declaration"]
    assert verdict.declaration.strategy_family_id.value == "catalog-family"
    assert verdict.declaration.confluence_set[0].fingerprint == world["confluence_fp"]

    records = _recording_world()
    catalogs = cast(dict[str, object], records["catalogs"])
    catalogs["family_catalog"] = [records["family_record"]]
    catalogs["confluence_catalog"] = [records["confluence_record"]]
    catalogs["producer_catalog"] = [records["binding"]]
    catalogs["logic_catalog"] = [records["logic"]]
    assert is_ok(_lint(records))

    for family_items, confluence_items in (
        (
            [records["family"], records["family_record"]],
            [records["confluence"], records["confluence_record"]],
        ),
        (
            [records["family_record"], records["family"]],
            [records["confluence_record"], records["confluence"]],
        ),
    ):
        mixed = dict(cast(Mapping[str, object], records["catalogs"]))
        mixed["family_catalog"] = family_items
        mixed["confluence_catalog"] = confluence_items
        assert is_ok(lint_declaration(records["declaration"], **mixed))


def test_formula_catalog_rejects_boolean_version_metadata_as_invalid_input() -> None:
    template = _ok(
        mint_producer_template(
            {
                "formula_id": "sma",
                "contract_format_version": 1,
                "inputs": [
                    {
                        "name": "close",
                        "source": {
                            "kind": "instrument",
                            "venue": "catalog-venue",
                            "symbol": "EURUSD",
                        },
                        "bar_spec": {"kind": "time-interval", "seconds": 60},
                        "channel_kind": "exact-price",
                        "quote_side": "mid",
                    }
                ],
                "calendar_requirements": [
                    _ok(CalendarIdentity.try_create("catalog-calendar", "v1", "2026a"))
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
            }
        )
    )
    binding = _ok(ProducerBinding.try_create(template))
    world = _recording_world(footprint_bindings=(binding,))
    # Replace the pinned confluence producer with the same formula template.
    confluence = _ok(mint_confluence([{"role": "level", "producer_binding": binding}]))
    confluence_record = _record(KIND_CONFLUENCE, confluence.body(), 2)
    confluence_fp = _ok(confluence.fingerprint_content())
    declaration = _ok(
        mint_bot_definition(
            strategy_family_id="catalog-family",
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
            footprint=cast(BotDefinition, world["declaration"]).footprint,
            permitted_exit_intents=(),
            logic_reference=cast(LogicIdentity, world["logic"]),
        )
    )
    catalogs = cast(dict[str, object], world["catalogs"])
    catalogs["confluence_catalog"] = {confluence_fp.value: confluence_record}
    catalogs["producer_catalog"] = {}
    catalogs["formula_catalog"] = {
        "sma": True,
    }
    refused = lint_declaration(declaration, **catalogs)
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.INVALID_INPUT
    assert refused.context["field"] == "formula_catalog"
    assert refused.context["journal"] is True


def test_confluence_mapping_key_must_match_registered_record_identity() -> None:
    world = _recording_world()
    foreign_content = _ok(
        mint_confluence([{"role": "filter", "producer_binding": world["binding"]}])
    )
    foreign_record = _record(KIND_CONFLUENCE, foreign_content.body(), 7)
    catalogs = dict(cast(Mapping[str, object], world["catalogs"]))
    catalogs["confluence_catalog"] = {
        cast(Fingerprint, world["confluence_fp"]).value: foreign_record
    }

    refused = lint_declaration(world["declaration"], **catalogs)
    assert is_refusal(refused)
    assert refused.context["journal"] is True


def test_confluence_registration_stable_id_is_checked_and_exact_duplicate_is_idempotent() -> None:
    world = _recording_world()
    wanted = cast(Fingerprint, world["confluence_fp"])
    record = cast(RegistrationRecord, world["confluence_record"])
    declaration = cast(BotDefinition, world["declaration"])
    catalogs = dict(cast(Mapping[str, object], world["catalogs"]))
    catalogs["confluence_catalog"] = [record, record]
    assert is_ok(lint_declaration(declaration, **catalogs))

    substituted = replace(record, stable_id=_fp("forged-registration-id"))
    catalogs["confluence_catalog"] = {wanted.value: substituted}
    refused = lint_declaration(declaration, **catalogs)
    assert is_refusal(refused)
    assert refused.context["field"] == "confluence_catalog"
    assert refused.context["journal"] is True


def test_matching_malformed_logic_identity_refuses_in_either_catalog_order() -> None:
    world = _recording_world()
    valid = cast(LogicIdentity, world["logic"])
    malformed = LogicIdentity(valid.distribution, valid.version, cast(Fingerprint, None))
    outcomes: list[Result[Layer1Verdict]] = []
    for catalog in ([malformed, valid], [valid, malformed]):
        outcomes.append(_lint(world, logic_catalog=catalog))
    for result in outcomes:
        assert is_refusal(result)
        assert result.context["field"] == "source_tree"
        assert result.context["journal"] is True


def test_distinct_valid_logic_sources_and_exact_duplicates_coexist() -> None:
    world = _recording_world()
    valid = cast(LogicIdentity, world["logic"])
    other = _ok(mint_logic_identity(valid.distribution, valid.version, {"other.py": "pass\n"}))
    assert is_ok(_lint(world, logic_catalog=[valid, valid]))
    assert is_ok(_lint(world, logic_catalog=[other, valid]))
    assert is_ok(_lint(world, logic_catalog=[valid, other]))


def test_conflicting_duplicate_family_metadata_is_not_catalog_order_dependent() -> None:
    world = _recording_world()
    valid_record = cast(RegistrationRecord, world["family_record"])
    conflicting_record = _record(
        KIND_STRATEGY_FAMILY,
        {"family_id": "catalog-family", "permitted_timeframes": ["1m"]},
        9,
    )
    outcomes: list[Result[Layer1Verdict]] = []
    for catalog in (
        [valid_record, conflicting_record],
        [conflicting_record, valid_record],
    ):
        catalogs = dict(cast(Mapping[str, object], world["catalogs"]))
        catalogs["family_catalog"] = catalog
        outcomes.append(lint_declaration(world["declaration"], **catalogs))

    for result in outcomes:
        assert is_refusal(result)
        assert result.context["journal"] is True


def test_nested_confluence_missing_transitive_producer_is_not_admitted() -> None:
    family = _ok(mint_strategy_family("nested-catalog-family"))
    leaf_binding = _binding("nested-leaf")
    parent_binding = _binding("nested-parent")
    leaf = _ok(mint_confluence([{"role": "level", "producer_binding": leaf_binding}]))
    leaf_fp = _ok(leaf.fingerprint_content())
    parent = _ok(
        mint_confluence(
            [
                {"role": "trigger", "producer_binding": parent_binding},
                {"role": "filter", "confluence_ref": leaf_fp},
            ]
        )
    )
    parent_fp = _ok(parent.fingerprint_content())
    logic = _ok(mint_logic_identity("nested-catalog-bot", "1.0.0", _SOURCE))
    calendar = _ok(CalendarIdentity.try_create("nested-calendar", "v1", "2026a"))
    producer_fp = _ok(parent_binding.fingerprint_content())
    # The transitive child producer is resolvable, but deliberately absent from the
    # Bot footprint. A valid producer catalog cannot compensate for incomplete use.
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
            [parent_binding],
        )
    )
    declaration = _ok(
        mint_bot_definition(
            strategy_family_id=family.family_id.value,
            confluence_set=[parent],
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
    catalogs = {
        "family_catalog": [_record(KIND_STRATEGY_FAMILY, family.body(), 0)],
        "confluence_catalog": {
            parent_fp.value: _record(KIND_CONFLUENCE, parent.body(), 1),
            leaf_fp.value: _record(KIND_CONFLUENCE, leaf.body(), 2),
        },
        "producer_catalog": {
            producer_fp.value: parent_binding,
            _ok(leaf_binding.fingerprint_content()).value: leaf_binding,
        },
        "formula_catalog": (),
        "logic_catalog": [logic],
    }
    refused = lint_declaration(declaration, **catalogs)
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.INVALID_INPUT
    assert refused.context["field"] == "footprint"
    missing = refused.context["missing"]
    assert isinstance(missing, tuple)
    assert _ok(leaf_binding.fingerprint_content()).value in missing
