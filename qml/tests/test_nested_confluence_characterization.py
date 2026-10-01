"""Public CT-34 nested composition, multiplicity, and identity contracts."""

from __future__ import annotations

from typing import TypeVar

from qmf.core import ExactRational, UnitKind, fingerprint
from qmf.core.refusal import RefusalCategory, Result, is_ok, is_refusal
from qml.declaration import Confluence, mint_confluence, resolve_confluence_at_layer1
from qml.footprint import ProducerBinding

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _binding(name: str) -> ProducerBinding:
    return _ok(ProducerBinding.try_create(_ok(fingerprint({"producer": name}))))


def _param(value: int) -> ExactRational:
    return _ok(ExactRational.try_create(value, 1, UnitKind.COUNT))


def test_nested_duplicate_child_references_resolve_and_remain_distinct_legs() -> None:
    leaf_binding = _binding("leaf")
    middle_binding = _binding("middle")
    root_binding = _binding("root")
    leaf = _ok(mint_confluence([{"role": "level", "producer_binding": leaf_binding}]))
    leaf_fp = _ok(leaf.fingerprint_content())
    middle = _ok(
        mint_confluence(
            [
                {"role": "confirmation", "confluence_ref": leaf_fp},
                {"role": "trigger", "producer_binding": middle_binding},
            ]
        )
    )
    middle_fp = _ok(middle.fingerprint_content())
    root = _ok(
        mint_confluence(
            [
                {
                    "role": "level",
                    "confluence_ref": middle_fp,
                    "producer_binding": root_binding,
                },
                {"role": "filter", "confluence_ref": middle_fp},
            ]
        )
    )

    assert root.child_refs() == (middle_fp, middle_fp)
    assert _ok(root.fingerprint_content()) != _ok(
        _ok(mint_confluence([{"role": "level", "confluence_ref": middle_fp}])).fingerprint_content()
    )
    resolved = resolve_confluence_at_layer1(
        root,
        [middle, leaf],
        producer_catalog=[root_binding, middle_binding, leaf_binding],
    )
    assert is_ok(resolved), resolved
    assert _ok(resolved.value.fingerprint_content()) == _ok(root.fingerprint_content())


def test_repeated_producer_roles_and_parameters_survive_mapping_roundtrip() -> None:
    shared = _binding("shared-source")
    legs = [
        {
            "role": "level",
            "producer_binding": shared,
            "declared_parameters": {"window": _param(5)},
            "display_ordinal": 0,
        },
        {
            "role": "filter",
            "producer_binding": shared,
            "declared_parameters": {"window": _param(8)},
            "display_ordinal": 1,
        },
    ]
    authored = _ok(mint_confluence(legs))
    payload = authored.identity_payload()
    roundtrip = _ok(Confluence.try_from_mapping(payload))
    assert len(roundtrip.legs) == 2
    assert _ok(roundtrip.fingerprint_content()) == _ok(authored.fingerprint_content())

    reversed_equivalent = _ok(mint_confluence(list(reversed(legs))))
    assert _ok(reversed_equivalent.fingerprint_content()) == _ok(authored.fingerprint_content())
    changed_parameter = [dict(legs[0]), {**legs[1], "declared_parameters": {"window": _param(9)}}]
    changed = _ok(mint_confluence(changed_parameter))
    assert _ok(changed.fingerprint_content()) != _ok(authored.fingerprint_content())

    ordered = _ok(mint_confluence(legs, order_significance=True))
    ordered_roundtrip = _ok(Confluence.try_from_mapping(ordered.identity_payload()))
    assert _ok(ordered_roundtrip.fingerprint_content()) == _ok(ordered.fingerprint_content())


def test_exclusive_group_is_not_an_undeclared_ct34_semantic() -> None:
    refused = mint_confluence(
        [
            {
                "role": "filter",
                "producer_binding": _binding("session"),
                "exclusive_group": "one-of-session-or-news",
            }
        ]
    )
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.INVALID_INPUT
    assert refused.context["field"] == "legs"
    assert refused.context["unknown"] == ("exclusive_group",)
