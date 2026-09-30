"""Epic 72 wire DTO, query vocabulary, and immutable ActionContext tests."""

from __future__ import annotations

from typing import cast

from qma.core.operations import public_operation_descriptors
from qma.wire.action_context import ActionContext, validate_action_context_press
from qma.wire.pack_ui_request import (
    GET_PACK_UI_REQUEST_CAPABILITY,
    GET_PACK_UI_REQUEST_HTTP_PATH,
    PACK_UI_REQUEST_CAPABILITY,
    PACK_UI_REQUEST_SCHEMA,
    parse_action_input,
    parse_pack_ui_request,
    parse_pack_ui_request_args,
    require_pack_ui_request_capability,
    validate_pack_ui_request,
)
from qma.wire.vocabulary import ADDABLE_QUERY_COUNT, SEED_QUERY_COUNT, WIRE_QUERIES, WireQuery
from qmf.core import is_ok, is_refusal


def _request(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "schema": PACK_UI_REQUEST_SCHEMA,
        "pack_id": "research-corpus",
        "pack_version": "0.1.0",
        "nav": [
            {
                "id": "coverage",
                "title": "Coverage",
                "slot": "app-nav",
                "view_ids": ["view:coverage"],
            }
        ],
        "views": [
            {
                "view_id": "view:coverage",
                "view_version": 1,
                "op_id": "qmb.analysis.project",
                "renderer": "native",
                "slot": "canvas-widget",
                "parameter_binding": {"schema": "qmb.analysis.project.v1"},
            }
        ],
    }
    body.update(overrides)
    return body


def _view() -> dict[str, object]:
    views = cast("list[object]", _request()["views"])
    return cast("dict[str, object]", views[0])


def test_pack_ui_request_is_a_closed_presentation_dto() -> None:
    parsed = validate_pack_ui_request(_request())
    assert is_ok(parsed), parsed
    assert parsed.value.views[0].view_id == "view:coverage"
    assert parsed.value.views[0].renderer == "native"
    assert parsed.value.nav[0].view_ids == ("view:coverage",)
    assert parsed.value.to_payload()["pack_id"] == "research-corpus"

    assert is_ok(parse_pack_ui_request({"pack_id": "research-corpus", "pack_version": "0.1.0"}))
    assert is_refusal(validate_pack_ui_request(_request(unrecognized=True)))
    assert is_refusal(parse_pack_ui_request(_request(copilot_profile={"prompts": []})))


def test_pack_ui_request_refuses_authority_ui_view_and_open_slots() -> None:
    for payload in (
        _request(views=[{**_view(), "view_id": "ui_view"}]),
        _request(views=[{**_view(), "view_id": "ui-view"}]),
        _request(views=[{**_view(), "slot": "pack-defined"}]),
        _request(views=[{**_view(), "grant_id": "grant:foreign"}]),
        _request(nav=[{"id": "x", "title": "X", "slot": "app-nav", "view_ids": ["view:foreign"]}]),
    ):
        assert is_refusal(parse_pack_ui_request(payload))


def test_get_pack_ui_request_is_addable_and_exact_revision_keyed() -> None:
    assert WireQuery.GET_PACK_UI_REQUEST.value == "get_pack_ui_request"
    assert GET_PACK_UI_REQUEST_CAPABILITY == "get_pack_ui_request"
    assert GET_PACK_UI_REQUEST_HTTP_PATH == "/q/get_pack_ui_request"
    assert PACK_UI_REQUEST_CAPABILITY == "pack_ui_request"
    assert len(WIRE_QUERIES) - SEED_QUERY_COUNT == ADDABLE_QUERY_COUNT
    assert is_refusal(require_pack_ui_request_capability({}))
    assert is_ok(require_pack_ui_request_capability({GET_PACK_UI_REQUEST_CAPABILITY: True}))
    assert is_ok(
        parse_pack_ui_request_args(
            {"instance_id": "pack:research-corpus", "availability_revision": 4}
        )
    )
    parsed_http_revision = parse_pack_ui_request_args(
        {"instance_id": "pack:research-corpus", "availability_revision": "42"}
    )
    assert is_ok(parsed_http_revision)
    assert parsed_http_revision.value["availability_revision"] == 42
    for invalid_revision in ("+1", "-1", "1.0", " 1", "\u0661"):
        assert is_refusal(
            parse_pack_ui_request_args(
                {
                    "instance_id": "pack:research-corpus",
                    "availability_revision": invalid_revision,
                }
            )
        )
    assert is_refusal(
        parse_pack_ui_request_args(
            {"instance_id": "pack:research-corpus", "availability_revision": True}
        )
    )


def test_action_context_ignores_renderer_authority_and_validates_action_input() -> None:
    descriptor = next(
        row for row in public_operation_descriptors() if row.op_id == "qmb.analysis.project"
    )
    created = ActionContext.try_create(
        psess="psess:desk-1",
        view_id="view:coverage",
        qualified_id="research-corpus:project",
        package_version="0.1.0",
        instance_id="pack:research-corpus",
        config_revision=4,
        grant_id="grant:session-a",
        allowed_op_ids=(descriptor.op_id,),
        account_scope=None,
        snapshot_cursor=19,
        operation_descriptor=descriptor,
        parameter_allow_keys=("run_fp1",),
    )
    assert is_ok(created), created
    hostile = {
        "action": descriptor.op_id,
        "input": {"run_fp1": "run-1"},
        "grant_id": "grant:foreign",
        "instance_id": "pack:foreign",
        "config_revision": 900,
        "psess": "psess:foreign",
        "caller_kind": "widget",
        "account_scope": "foreign-account",
        "allowed_op_ids": ["other.op"],
        "snapshot_cursor": 999,
        "availability_revision": 999,
        "view_id": "view:foreign",
        "qualified_id": "other-pack:project",
        "package_version": "999.0.0",
        "op_version": "999",
        "parameter_ceiling": {"allow_keys": ["*snake_fp1"]},
    }
    result = validate_action_context_press(
        hostile,
        context=created.value,
    )
    assert is_ok(result), result
    assert result.value["context"] is created.value
    assert result.value["input"] == {"run_fp1": "run-1"}
    assert is_refusal(
        validate_action_context_press(
            {"action": "other.op", "input": {}, "allowed_op_ids": ["other.op"]},
            context=created.value,
        )
    )
    assert is_refusal(
        validate_action_context_press(
            {"action": descriptor.op_id, "input": {"not_a_field": True}},
            context=created.value,
        )
    )
    assert is_refusal(
        validate_action_context_press(
            {"action": descriptor.op_id, "input": {"run_fp1": "run-1", "other": True}},
            context=created.value,
        )
    )
    parsed = parse_action_input({"action": descriptor.op_id, "input": {}, "grant_id": "attacker"})
    assert is_ok(parsed) and parsed.value["action"] == descriptor.op_id


def test_action_context_is_immutable_and_ungranted_mount_has_no_authority() -> None:
    context = ActionContext.try_create(
        psess="psess:desk-1",
        view_id="view:empty",
        qualified_id="research-corpus:project",
        package_version="0.1.0",
        instance_id="pack:research-corpus",
        config_revision=0,
        grant_id=None,
        allowed_op_ids=(),
        account_scope=None,
        snapshot_cursor=0,
    )
    assert is_ok(context)
    assert context.value.to_payload()["allowed_op_ids"] == []
    assert is_refusal(
        ActionContext.try_create(
            psess="psess:desk-1",
            view_id="view:empty",
            qualified_id="research-corpus:project",
            package_version="0.1.0",
            instance_id="pack:research-corpus",
            config_revision=0,
            grant_id=None,
            allowed_op_ids=("qmb.analysis.project",),
            account_scope=None,
            snapshot_cursor=0,
        )
    )
