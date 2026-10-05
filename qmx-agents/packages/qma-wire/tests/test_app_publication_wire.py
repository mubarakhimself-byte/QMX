"""MA04 closed input contracts and literal-true publication capability gates."""

from __future__ import annotations

from typing import Any

import pytest
from qma.wire.app_publication import (
    PUBLICATION_CAPABILITIES,
    parse_publication_args,
    require_publication_capability,
)
from qma.wire.schemas import validate_instance
from qma.wire.vocabulary import MessageFamily, family_of
from qmf.core import is_ok, is_refusal


def example() -> dict[str, Any]:
    return {
        "product_session_ref": "psess:author",
        "candidate_id": "appcand:identity",
        "revision": "fp1:sha256:" + "1" * 64,
        "validation_fp1": "fp1:sha256:" + "2" * 64,
        "expected_context_revision": 0,
        "expected_active_revision": None,
        "expected_availability_revision": 4,
    }


@pytest.mark.parametrize("name", sorted(PUBLICATION_CAPABILITIES))
def test_wire_family_schema_and_capability(name: str) -> None:
    args = example()
    if name == "get_app_publication":
        args = {key: args[key] for key in ("product_session_ref", "candidate_id")}
    elif name == "undo_app_publication":
        args["target_publication_revision"] = args.pop("revision")
    assert is_ok(parse_publication_args(name, args)) and is_ok(validate_instance(args, name))
    assert is_ok(require_publication_capability(name, {name: True}))
    assert family_of(name) == (
        MessageFamily.QUERY if name == "get_app_publication" else MessageFamily.COMMAND
    )
    for invalid in ({}, {name: False}, {name: 1}, {name: "true"}, None):
        assert is_refusal(require_publication_capability(name, invalid))


@pytest.mark.parametrize(
    "field,value",
    [
        ("expected_context_revision", True),
        ("expected_availability_revision", -1),
        ("expected_active_revision", False),
        ("revision", "wrong"),
        ("validation_fp1", "wrong"),
        ("candidate_id", "forged"),
        ("product_session_ref", "forged"),
        ("product_session_ref", "\ud800"),
        ("candidate_id", "x" * 1025),
        ("grant_id", "invented"),
    ],
)
def test_closed_bounded_untrusted_inputs(field: str, value: Any) -> None:
    assert is_refusal(parse_publication_args("publish_app_candidate", {**example(), field: value}))
