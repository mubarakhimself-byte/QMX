"""Story 70.2 — addable transfer_artifact command, capability, and inspect SHA."""

from __future__ import annotations

from qma.wire import (
    ADDABLE_COMMAND_COUNT,
    ARTIFACT_STORE_TYPES_EXISTED_AT_INSPECT_SHA,
    DEFERRED_INITIALIZE_CAPABILITIES,
    FORBIDDEN_TRANSFER_CONTRACT_KEYS,
    HUMAN_GATE_COMMANDS,
    SEED_COMMAND_COUNT,
    SEED_EVENT_COUNT,
    SEED_QUERY_COUNT,
    TRANSFER_ARTIFACT_AMENDMENT,
    TRANSFER_ARTIFACT_CAPABILITY,
    TRANSFER_ARTIFACT_COMMAND,
    TRANSFER_ARTIFACT_CONTRACT,
    TRANSFER_ARTIFACT_EXISTED_AT_INSPECT_SHA,
    TRANSFER_ARTIFACT_IS_DISPATCH_INVOKE,
    TRANSFER_ARTIFACT_IS_HOST_CONTROL,
    TRANSFER_ARTIFACT_IS_PACK_OP,
    TRANSFER_ARTIFACT_IS_WIRE_COMMAND,
    TRANSFER_ARTIFACT_NEW_CT_MINTED,
    TRANSFER_COMPLETE_MINTED,
    WIRE_COMMANDS,
    WIRE_PROTOCOL_VERSION,
    WireCommand,
    claim_artifact_store_types_absent_at_inspect_sha,
    claim_transfer_artifact_existed_at_inspect_sha,
    durable_transfer_command_id,
    negotiate_initialize,
    parse_transfer_artifact_payload,
    require_transfer_artifact_capability,
    validate_family_payload,
)
from qma.wire.initialize import InitializeParams
from qma.wire.transfer_artifact import claim_this_story_scaffolded_qmx_ui
from qmf.core.refusal import Ok, RefusalCategory, is_ok, is_refusal


def test_transfer_artifact_is_addable_ct40_and_absent_at_inspect_sha() -> None:
    assert TRANSFER_ARTIFACT_COMMAND == "transfer_artifact" == WireCommand.TRANSFER_ARTIFACT.value
    assert TRANSFER_ARTIFACT_COMMAND in WIRE_COMMANDS
    assert TRANSFER_ARTIFACT_IS_WIRE_COMMAND is True
    assert TRANSFER_ARTIFACT_CONTRACT == "CT-40"
    assert TRANSFER_ARTIFACT_NEW_CT_MINTED is False
    assert TRANSFER_ARTIFACT_IS_PACK_OP is False
    assert TRANSFER_ARTIFACT_IS_DISPATCH_INVOKE is False
    assert TRANSFER_ARTIFACT_IS_HOST_CONTROL is False
    assert TRANSFER_COMPLETE_MINTED is False
    assert TRANSFER_ARTIFACT_AMENDMENT == "AM-09"
    assert SEED_COMMAND_COUNT == 9
    assert ADDABLE_COMMAND_COUNT == 1
    assert SEED_QUERY_COUNT == 7
    assert SEED_EVENT_COUNT == 10
    assert TRANSFER_ARTIFACT_EXISTED_AT_INSPECT_SHA is False
    assert ARTIFACT_STORE_TYPES_EXISTED_AT_INSPECT_SHA is True
    assert TRANSFER_ARTIFACT_COMMAND in HUMAN_GATE_COMMANDS
    assert TRANSFER_ARTIFACT_CAPABILITY not in DEFERRED_INITIALIZE_CAPABILITIES
    assert "transfer_complete" in DEFERRED_INITIALIZE_CAPABILITIES
    assert is_refusal(claim_transfer_artifact_existed_at_inspect_sha(True))
    assert is_ok(claim_transfer_artifact_existed_at_inspect_sha(False))
    assert is_refusal(claim_artifact_store_types_absent_at_inspect_sha(True))
    assert is_ok(claim_artifact_store_types_absent_at_inspect_sha(False))
    assert is_refusal(claim_this_story_scaffolded_qmx_ui(True))
    assert is_ok(validate_family_payload("transfer_artifact", {"fp1": "a", "command_id": "c"}))


def test_missing_transfer_artifact_capability_is_typed_mismatch() -> None:
    missing = require_transfer_artifact_capability({})
    assert is_refusal(missing)
    assert missing.category is RefusalCategory.POLICY_REJECTION
    assert missing.context["missing"] == TRANSFER_ARTIFACT_CAPABILITY
    assert missing.context["pack_op"] is False
    none = require_transfer_artifact_capability(None)
    assert is_refusal(none)
    present = require_transfer_artifact_capability({TRANSFER_ARTIFACT_CAPABILITY: True})
    assert is_ok(present)


def test_initialize_advertises_transfer_artifact() -> None:
    empty = InitializeParams.try_create(
        protocol_version=WIRE_PROTOCOL_VERSION,
        client_producer_id="tab:empty",
    )
    assert isinstance(empty, Ok)
    empty_neg = negotiate_initialize(empty.value, assign_producer_id="tab:empty")
    assert isinstance(empty_neg, Ok)
    assert empty_neg.value.capabilities[TRANSFER_ARTIFACT_CAPABILITY] is True

    asked = InitializeParams.try_create(
        protocol_version=WIRE_PROTOCOL_VERSION,
        capabilities={TRANSFER_ARTIFACT_CAPABILITY: True},
        client_producer_id="tab:asked",
    )
    assert isinstance(asked, Ok)
    asked_neg = negotiate_initialize(asked.value, assign_producer_id="tab:asked")
    assert isinstance(asked_neg, Ok)
    assert asked_neg.value.capabilities[TRANSFER_ARTIFACT_CAPABILITY] is True


def test_parse_transfer_artifact_payload_and_durable_command_id() -> None:
    parsed = parse_transfer_artifact_payload(
        {
            "fp1": "fp1:abc",
            "command_id": "cmd-1",
            "instance_id": "inst-1",
            "product_session_ref": "psess:H",
        }
    )
    assert isinstance(parsed, Ok)
    assert parsed.value["durable_command_id"] == "psess:H/cmd-1"
    assert durable_transfer_command_id("cmd-1", "psess:H") == "psess:H/cmd-1"
    nested = parse_transfer_artifact_payload(
        {
            "fp1": "fp1:abc",
            "command_id": "cmd-2",
            "destination": {
                "instance_id": "inst-2",
                "environment_id": "env-a",
                "placement_revision": "rev-1",
                "credential_ref": "cred://compute/worker-a",
            },
        }
    )
    assert isinstance(nested, Ok)
    assert nested.value["instance_id"] == "inst-2"
    assert nested.value["credential_ref"] == "cred://compute/worker-a"
    for field in FORBIDDEN_TRANSFER_CONTRACT_KEYS:
        refused = parse_transfer_artifact_payload(
            {
                "fp1": "fp1:abc",
                "command_id": "cmd-x",
                "instance_id": "inst-x",
                field: "nope",
            }
        )
        assert is_refusal(refused), field
        assert refused.context["pack_op"] is False
