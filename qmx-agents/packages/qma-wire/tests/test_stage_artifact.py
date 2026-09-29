"""Story 70.1 — initialize capability stage_artifact means PUT /artifacts/stage."""

from __future__ import annotations

from qma.wire import (
    ARTIFACT_STORE_TYPES_EXISTED_AT_INSPECT_SHA,
    FORBIDDEN_STAGE_SELECTED_REF_KINDS,
    JSONRPC_STAGE_ARTIFACT_MINTED,
    STAGE_ARTIFACT_AMENDMENT,
    STAGE_ARTIFACT_CAPABILITY,
    STAGE_ARTIFACT_CAPABILITY_MINTED,
    STAGE_ARTIFACT_EXISTED_AT_INSPECT_SHA,
    STAGE_ARTIFACT_HTTP_METHOD,
    STAGE_ARTIFACT_HTTP_PATH,
    STAGE_ARTIFACT_INSPECT_SHA,
    STAGE_ARTIFACT_IS_WIRE_COMMAND,
    STAGE_ARTIFACT_NEW_CT_MINTED,
    WIRE_COMMANDS,
    WIRE_QUERIES,
    claim_artifact_store_types_absent_at_inspect_sha,
    claim_stage_artifact_put_existed_at_inspect_sha,
    refuse_jsonrpc_stage_artifact,
    require_stage_artifact_capability,
    stage_artifact_capability_unavailable,
)
from qma.wire.selected_ref import SELECTED_REF_KINDS
from qmf.core.refusal import RefusalCategory, is_ok, is_refusal


def test_stage_artifact_is_put_not_wire_command() -> None:
    assert STAGE_ARTIFACT_CAPABILITY == "stage_artifact"
    assert STAGE_ARTIFACT_CAPABILITY_MINTED is True
    assert STAGE_ARTIFACT_HTTP_METHOD == "PUT"
    assert STAGE_ARTIFACT_HTTP_PATH == "/artifacts/stage"
    assert STAGE_ARTIFACT_AMENDMENT == "AM-05"
    assert STAGE_ARTIFACT_IS_WIRE_COMMAND is False
    assert JSONRPC_STAGE_ARTIFACT_MINTED is False
    assert STAGE_ARTIFACT_NEW_CT_MINTED is False
    assert STAGE_ARTIFACT_CAPABILITY not in WIRE_COMMANDS
    assert STAGE_ARTIFACT_CAPABILITY not in WIRE_QUERIES
    assert STAGE_ARTIFACT_EXISTED_AT_INSPECT_SHA is False
    assert STAGE_ARTIFACT_INSPECT_SHA == "34c148be"
    assert ARTIFACT_STORE_TYPES_EXISTED_AT_INSPECT_SHA is True
    assert frozenset({"upload_bytes", "local_path"}) == FORBIDDEN_STAGE_SELECTED_REF_KINDS
    assert not any(kind in SELECTED_REF_KINDS for kind in FORBIDDEN_STAGE_SELECTED_REF_KINDS)


def test_claiming_put_existed_at_inspect_sha_fails() -> None:
    assert is_refusal(claim_stage_artifact_put_existed_at_inspect_sha(True))
    assert is_ok(claim_stage_artifact_put_existed_at_inspect_sha(False))
    assert is_refusal(claim_artifact_store_types_absent_at_inspect_sha(True))
    assert is_ok(claim_artifact_store_types_absent_at_inspect_sha(False))


def test_missing_stage_artifact_capability_is_typed_mismatch() -> None:
    missing = require_stage_artifact_capability({})
    assert is_refusal(missing)
    assert missing.category is RefusalCategory.POLICY_REJECTION
    assert missing.context["missing"] == STAGE_ARTIFACT_CAPABILITY
    assert missing.context["empty_upload"] is False
    assert missing.context["http_put"] == STAGE_ARTIFACT_HTTP_PATH
    none = require_stage_artifact_capability(None)
    assert is_refusal(none)
    present = require_stage_artifact_capability({STAGE_ARTIFACT_CAPABILITY: True})
    assert is_ok(present)
    unavailable = stage_artifact_capability_unavailable()
    assert unavailable.context["jsonrpc_stage_artifact"] is False


def test_jsonrpc_stage_artifact_is_refused() -> None:
    refused = refuse_jsonrpc_stage_artifact()
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["jsonrpc_stage_artifact"] is False
    assert refused.context["is_wire_command"] is False
    assert refused.context["in_wire_commands"] is False
    assert refused.context["http_put"] == STAGE_ARTIFACT_HTTP_PATH
    assert refused.context["named_amendment"] == "AM-09"
    assert refused.context["selected_ref_kinds_include_forbidden"] is False
