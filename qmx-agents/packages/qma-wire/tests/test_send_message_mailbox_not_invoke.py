"""Story 69.4 — send_message stays mailbox, not invoke."""

from __future__ import annotations

from qma.core.ports.mailbox import (
    DELIVERY_STATE_VALUES,
    MESSAGE_KIND_VALUES,
    PRODUCT_CHAT_MESSAGE_KINDS,
)
from qma.core.vocabulary.enums import DeliveryState, MessageKind
from qma.wire import (
    DISPATCH_CHAT_IS_THIS_STORY,
    FORBIDDEN_MAILBOX_CHAT_CONTRACT_KEYS,
    HOME_COMPOSER_FORBIDDEN_KINDS,
    LIVE_CT40_SERVING_SEND_MESSAGE_EXISTED_AT_INSPECT_SHA,
    LIVE_CT40_SERVING_SEND_MESSAGE_INSPECT_SHA,
    MAILBOX_SEND_IS_INVOKE,
    MAILBOX_SEND_REQUIRES_GRANT_RECORD,
    MAILBOX_SEND_REQUIRES_INSTANCE_ID,
    MAILBOX_SEND_USES_COMMAND_ID_IDENTITY,
    MAILBOX_SEND_USES_INVOKE_IDEMPOTENCY_KEY,
    MESSAGE_DELTA_IS_PROGRESS_ONLY,
    QMX_UI_SCAFFOLDED_THIS_STORY,
    SEND_MESSAGE_COMMAND,
    SEND_MESSAGE_SEED_NAME_EXISTED_AT_INSPECT_SHA,
    TRANSCRIPT_IS_MEMORY_PROVIDER,
    TRANSCRIPT_IS_NEW_STORE,
    TRANSCRIPT_IS_PRIVATE_NOTES,
    TRANSCRIPT_IS_SESS,
    WireCommand,
    WireEvent,
    claim_live_ct40_serving_send_message_existed_at_inspect_sha,
    claim_send_message_seed_name_absent_at_inspect_sha,
    claim_this_story_scaffolded_qmx_ui,
    list_mailbox_snapshots_are_truth,
    parse_send_message_payload,
    refuse_mailbox_send_as_invoke,
)
from qmf.core.refusal import is_ok, is_refusal


def test_send_message_is_mailbox_not_invoke() -> None:
    assert SEND_MESSAGE_COMMAND == "send_message"
    assert WireCommand.SEND_MESSAGE.value == SEND_MESSAGE_COMMAND
    assert MAILBOX_SEND_IS_INVOKE is False
    assert MAILBOX_SEND_REQUIRES_INSTANCE_ID is False
    assert MAILBOX_SEND_REQUIRES_GRANT_RECORD is False
    assert MAILBOX_SEND_USES_INVOKE_IDEMPOTENCY_KEY is False
    assert MAILBOX_SEND_USES_COMMAND_ID_IDENTITY is False
    assert DISPATCH_CHAT_IS_THIS_STORY is False
    assert QMX_UI_SCAFFOLDED_THIS_STORY is False
    legal = parse_send_message_payload(
        {
            "product_session_ref": "psess:H",
            "kind": "handoff",
            "body": {"text": "hello"},
        }
    )
    assert is_ok(legal)


def test_invocation_envelope_keys_are_refused_as_chat_contract() -> None:
    keys = (
        "logical_invocation_id",
        "grant_id",
        "op_id",
        "instance_id",
        "idempotency_key",
        "caller_kind",
        "input_hash",
    )
    assert frozenset(keys) == FORBIDDEN_MAILBOX_CHAT_CONTRACT_KEYS
    for key in keys:
        refused = parse_send_message_payload(
            {"kind": "handoff", "product_session_ref": "psess:H", key: "x"}
        )
        assert is_refusal(refused), key
        assert refused.context["field"] == key
        assert refused.context["invoke"] is False
    nested = parse_send_message_payload(
        {"envelope": {"logical_invocation_id": "inv:1", "kind": "notify"}}
    )
    assert is_refusal(nested)
    assert nested.context["field"] == "logical_invocation_id"
    command_id = parse_send_message_payload({"command_id": "cmd:1", "kind": "handoff"})
    assert is_refusal(command_id)
    assert command_id.context["field"] == "command_id"
    notes = parse_send_message_payload({"private_notes": "secret", "kind": "handoff"})
    assert is_refusal(notes)
    assert notes.context["field"] == "private_notes"
    as_invoke = refuse_mailbox_send_as_invoke(field="grant_id")
    assert as_invoke.context["mailbox_send"] is True
    assert as_invoke.context["invoke"] is False


def test_product_chat_kinds_exclude_approval_request() -> None:
    assert {
        MessageKind.HANDOFF.value,
        MessageKind.REPLY.value,
        MessageKind.NOTIFY.value,
        MessageKind.STATUS.value,
        MessageKind.QUESTION.value,
    } == PRODUCT_CHAT_MESSAGE_KINDS
    assert MessageKind.APPROVAL_REQUEST.value in HOME_COMPOSER_FORBIDDEN_KINDS
    assert MessageKind.REVIEW_REQUEST.value in HOME_COMPOSER_FORBIDDEN_KINDS
    approval = parse_send_message_payload(
        {"kind": "approval_request", "product_session_ref": "psess:H"}
    )
    assert is_refusal(approval)
    assert approval.context["field"] == "kind"
    review = parse_send_message_payload(
        {"kind": "review_request", "product_session_ref": "psess:H"}
    )
    assert is_refusal(review)
    assert {
        "handoff",
        "reply",
        "notify",
        "review_request",
        "status",
        "question",
        "approval_request",
    } == MESSAGE_KIND_VALUES
    assert {
        "delivered",
        "queued",
        "woke",
        "deferred",
        "dead_letter",
    } == DELIVERY_STATE_VALUES
    assert {member.value for member in MessageKind} == MESSAGE_KIND_VALUES
    assert {member.value for member in DeliveryState} == DELIVERY_STATE_VALUES


def test_message_delta_is_progress_list_mailbox_is_truth() -> None:
    assert MESSAGE_DELTA_IS_PROGRESS_ONLY is True
    assert WireEvent.MESSAGE_DELTA.value == "message.delta"
    assert list_mailbox_snapshots_are_truth() is True
    assert TRANSCRIPT_IS_PRIVATE_NOTES is False
    assert TRANSCRIPT_IS_SESS is False
    assert TRANSCRIPT_IS_MEMORY_PROVIDER is False
    assert TRANSCRIPT_IS_NEW_STORE is False


def test_inspect_sha_live_serving_absent_seed_name_present() -> None:
    assert LIVE_CT40_SERVING_SEND_MESSAGE_INSPECT_SHA == "34c148be"
    assert LIVE_CT40_SERVING_SEND_MESSAGE_EXISTED_AT_INSPECT_SHA is False
    assert SEND_MESSAGE_SEED_NAME_EXISTED_AT_INSPECT_SHA is True
    assert WireCommand.SEND_MESSAGE.value == "send_message"
    assert is_refusal(claim_live_ct40_serving_send_message_existed_at_inspect_sha(True))
    assert is_ok(claim_live_ct40_serving_send_message_existed_at_inspect_sha(False))
    assert is_refusal(claim_send_message_seed_name_absent_at_inspect_sha(True))
    assert is_ok(claim_send_message_seed_name_absent_at_inspect_sha(False))
    assert is_refusal(claim_this_story_scaffolded_qmx_ui(True))
    assert is_ok(claim_this_story_scaffolded_qmx_ui(False))
