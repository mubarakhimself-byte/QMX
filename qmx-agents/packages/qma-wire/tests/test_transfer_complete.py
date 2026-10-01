"""Story 70.3 — addable transfer_complete command, capability, and inspect SHA."""

from __future__ import annotations

from qma.wire import (
    ADDABLE_COMMAND_COUNT,
    CONNECT_TYPES_EXISTED_AT_INSPECT_SHA,
    DEFERRED_INITIALIZE_CAPABILITIES,
    FORBIDDEN_TRANSFER_COMPLETE_CONTRACT_KEYS,
    HUMAN_GATE_COMMANDS,
    MACHINE_ARTIFACT_GET_EXISTED_AT_INSPECT_SHA,
    SEED_COMMAND_COUNT,
    SEED_EVENT_COUNT,
    SEED_QUERY_COUNT,
    TRANSFER_COMPLETE_AMENDMENT,
    TRANSFER_COMPLETE_CAPABILITY,
    TRANSFER_COMPLETE_COMMAND,
    TRANSFER_COMPLETE_CONTRACT,
    TRANSFER_COMPLETE_EXISTED_AT_INSPECT_SHA,
    TRANSFER_COMPLETE_IS_DISPATCH_INVOKE,
    TRANSFER_COMPLETE_IS_HOST_CONTROL,
    TRANSFER_COMPLETE_IS_PACK_OP,
    TRANSFER_COMPLETE_IS_WIRE_COMMAND,
    TRANSFER_COMPLETE_MINTED,
    TRANSFER_COMPLETE_NEW_CT_MINTED,
    WIRE_COMMANDS,
    WIRE_PROTOCOL_VERSION,
    WireCommand,
    claim_connect_types_absent_at_inspect_sha,
    claim_machine_artifact_get_existed_at_inspect_sha,
    claim_transfer_complete_existed_at_inspect_sha,
    negotiate_initialize,
    parse_transfer_complete_payload,
    require_transfer_complete_capability,
    validate_family_payload,
)
from qma.wire.initialize import InitializeParams
from qma.wire.transfer_complete import claim_this_story_scaffolded_qmx_ui
from qmf.core.refusal import Ok, RefusalCategory, is_ok, is_refusal


def test_transfer_complete_is_addable_ct40_and_absent_at_inspect_sha() -> None:
    assert TRANSFER_COMPLETE_COMMAND == "transfer_complete"
    assert WireCommand.TRANSFER_COMPLETE.value == TRANSFER_COMPLETE_COMMAND
    assert TRANSFER_COMPLETE_COMMAND in WIRE_COMMANDS
    assert TRANSFER_COMPLETE_IS_WIRE_COMMAND is True
    assert TRANSFER_COMPLETE_CONTRACT == "CT-40"
    assert TRANSFER_COMPLETE_NEW_CT_MINTED is False
    assert TRANSFER_COMPLETE_IS_PACK_OP is False
    assert TRANSFER_COMPLETE_IS_DISPATCH_INVOKE is False
    assert TRANSFER_COMPLETE_IS_HOST_CONTROL is False
    assert TRANSFER_COMPLETE_MINTED is True
    assert TRANSFER_COMPLETE_AMENDMENT == "AM-09"
    assert SEED_COMMAND_COUNT == 9
    assert ADDABLE_COMMAND_COUNT == 7
    assert SEED_QUERY_COUNT == 7
    assert SEED_EVENT_COUNT == 10
    assert TRANSFER_COMPLETE_EXISTED_AT_INSPECT_SHA is False
    assert MACHINE_ARTIFACT_GET_EXISTED_AT_INSPECT_SHA is False
    assert CONNECT_TYPES_EXISTED_AT_INSPECT_SHA is True
    assert TRANSFER_COMPLETE_COMMAND not in HUMAN_GATE_COMMANDS
    assert TRANSFER_COMPLETE_CAPABILITY not in DEFERRED_INITIALIZE_CAPABILITIES
    assert is_refusal(claim_transfer_complete_existed_at_inspect_sha(True))
    assert is_ok(claim_transfer_complete_existed_at_inspect_sha(False))
    assert is_refusal(claim_machine_artifact_get_existed_at_inspect_sha(True))
    assert is_ok(claim_machine_artifact_get_existed_at_inspect_sha(False))
    assert is_refusal(claim_connect_types_absent_at_inspect_sha(True))
    assert is_ok(claim_connect_types_absent_at_inspect_sha(False))
    assert is_refusal(claim_this_story_scaffolded_qmx_ui(True))
    assert is_ok(
        validate_family_payload(
            "transfer_complete",
            {"ticket_id": "att:1", "fp1": "a", "byte_count": 1, "command_id": "c"},
        )
    )


def test_missing_transfer_complete_capability_is_typed_mismatch() -> None:
    missing = require_transfer_complete_capability({})
    assert is_refusal(missing)
    assert missing.category is RefusalCategory.POLICY_REJECTION
    assert missing.context["missing"] == TRANSFER_COMPLETE_CAPABILITY
    none = require_transfer_complete_capability(None)
    assert is_refusal(none)
    present = require_transfer_complete_capability({TRANSFER_COMPLETE_CAPABILITY: True})
    assert is_ok(present)


def test_initialize_advertises_transfer_complete() -> None:
    empty = InitializeParams.try_create(
        protocol_version=WIRE_PROTOCOL_VERSION,
        client_producer_id="tab:empty",
    )
    assert isinstance(empty, Ok)
    empty_neg = negotiate_initialize(empty.value, assign_producer_id="tab:empty")
    assert isinstance(empty_neg, Ok)
    assert empty_neg.value.capabilities[TRANSFER_COMPLETE_CAPABILITY] is True

    asked = InitializeParams.try_create(
        protocol_version=WIRE_PROTOCOL_VERSION,
        capabilities={TRANSFER_COMPLETE_CAPABILITY: True},
        client_producer_id="tab:asked",
    )
    assert isinstance(asked, Ok)
    asked_neg = negotiate_initialize(asked.value, assign_producer_id="tab:asked")
    assert isinstance(asked_neg, Ok)
    assert asked_neg.value.capabilities[TRANSFER_COMPLETE_CAPABILITY] is True


def test_parse_transfer_complete_payload_identity_is_ticket_plus_command_id() -> None:
    parsed = parse_transfer_complete_payload(
        {
            "ticket_id": "att:abc",
            "fp1": "fp1:abc",
            "byte_count": 4,
            "command_id": "cmd-1",
        }
    )
    assert isinstance(parsed, Ok)
    assert parsed.value["ticket_id"] == "att:abc"
    assert parsed.value["command_id"] == "cmd-1"
    assert parsed.value["byte_count"] == 4
    for field in FORBIDDEN_TRANSFER_COMPLETE_CONTRACT_KEYS:
        refused = parse_transfer_complete_payload(
            {
                "ticket_id": "att:abc",
                "fp1": "fp1:abc",
                "byte_count": 4,
                "command_id": "cmd-x",
                field: "nope",
            }
        )
        assert is_refusal(refused), field
        assert refused.context["pack_op"] is False
