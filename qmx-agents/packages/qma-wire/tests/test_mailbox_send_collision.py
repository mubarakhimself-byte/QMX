"""Story 69.3 — AM-12 pair+hash collision; never auto-resend."""

from __future__ import annotations

from qma.wire import (
    DEDUP_WINDOW_REGISTRY_KEY,
    LEFTOVER_COMPOSER_IS_COMMAND,
    LIVE_SOCKET_DISPATCH_EXISTED_AT_INSPECT_SHA,
    LIVE_SOCKET_DISPATCH_INSPECT_SHA,
    LIVE_SOCKET_DISPATCH_NAMES,
    MAILBOX_AUTO_RESEND,
    MAILBOX_SEND_AMENDMENT,
    MAILBOX_SEND_COLLISION_COMMAND,
    MAILBOX_SEND_OTHER_COMMANDS_WINDOW,
    MAILBOX_SEND_RETENTION_FLOOR,
    PAIR_LOOKUP_EMPTY_IS_NEW_SEND,
    CommandDedupCursor,
    IdempotencyKey,
    claim_live_socket_dispatch_existed_at_inspect_sha,
    hash_wire_payload_bytes,
    mailbox_restore_plan,
    pair_lookup_disposition,
    parse_mailbox_send_pair,
    refuse_mailbox_auto_resend,
    refuse_mailbox_send_collision,
    refuse_substitute_live_producer_id,
)
from qmf.core.chrono import Duration, Instant
from qmf.core.refusal import Ok, RefusalCategory, is_ok, is_refusal


def _instant(ns: int) -> Instant:
    result = Instant.try_create(ns)
    assert isinstance(result, Ok)
    return result.value


def _duration(ns: int) -> Duration:
    result = Duration.try_create(ns)
    assert isinstance(result, Ok)
    return result.value


def test_pre_ack_pair_is_producer_id_and_wire_id() -> None:
    parsed = parse_mailbox_send_pair({"producer_id": "P", "wire_id": "C1", "body": {"text": "x"}})
    assert isinstance(parsed, Ok)
    assert parsed.value is not None
    assert parsed.value.producer_id == "P"
    assert parsed.value.wire_id == "C1"
    assert parsed.value.id == "C1"
    from_id = parse_mailbox_send_pair({"producer_id": "P", "id": "C1"})
    assert isinstance(from_id, Ok)
    assert from_id.value is not None
    assert from_id.value.wire_id == "C1"
    omitted = parse_mailbox_send_pair({"body": {"text": "x"}})
    assert isinstance(omitted, Ok)
    assert omitted.value is None
    half = parse_mailbox_send_pair({"producer_id": "P"})
    assert is_refusal(half)


def test_payload_hash_is_wire_payload_bytes_not_pair() -> None:
    first = hash_wire_payload_bytes(
        {
            "producer_id": "P",
            "wire_id": "C1",
            "kind": "handoff",
            "body": {"text": "hello"},
            "product_session_ref": "psess:H",
        }
    )
    same_pair_same_body = hash_wire_payload_bytes(
        {
            "producer_id": "P",
            "wire_id": "C1",
            "kind": "handoff",
            "body": {"text": "hello"},
            "product_session_ref": "psess:H",
        }
    )
    same_pair_different_body = hash_wire_payload_bytes(
        {
            "producer_id": "P",
            "wire_id": "C1",
            "kind": "handoff",
            "body": {"text": "other"},
            "product_session_ref": "psess:H",
        }
    )
    assert isinstance(first, Ok) and isinstance(same_pair_same_body, Ok)
    assert isinstance(same_pair_different_body, Ok)
    assert first.value.startswith("fp1:sha256:")
    assert first.value == same_pair_same_body.value
    assert first.value != same_pair_different_body.value


def test_am12_collision_is_not_successful_prior_ack() -> None:
    assert MAILBOX_SEND_AMENDMENT == "AM-12"
    assert MAILBOX_SEND_COLLISION_COMMAND == "send_message"
    assert MAILBOX_SEND_RETENTION_FLOOR == "journal_lifetime"
    assert MAILBOX_SEND_OTHER_COMMANDS_WINDOW == DEDUP_WINDOW_REGISTRY_KEY
    refused = refuse_mailbox_send_collision(
        producer_id="P",
        wire_id="C1",
        stored_hash="fp1:sha256:aa",
        given_hash="fp1:sha256:bb",
    )
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["reason"] == "payload_hash_collision"
    assert refused.context["retention"] == "journal_lifetime"
    assert refused.context["successful_prior_ack"] is False
    assert refused.context["mailbox_sends_only"] is True
    assert refused.context["other_commands_keep"] == "wire.dedup_window"


def test_other_commands_keep_story_41_3_dedup_window() -> None:
    cursor = CommandDedupCursor(window=_duration(100))
    key = IdempotencyKey.try_create(producer_id="P", id="C1")
    assert isinstance(key, Ok)
    assert cursor.window_registry_key == DEDUP_WINDOW_REGISTRY_KEY
    assert isinstance(cursor.observe(key.value, now=_instant(0)), Ok)
    later = cursor.observe(key.value, now=_instant(101))
    assert isinstance(later, Ok)
    assert later.value.disposition == "accept"
    assert MAILBOX_SEND_RETENTION_FLOOR != DEDUP_WINDOW_REGISTRY_KEY


def test_cold_start_restore_is_list_mailbox_only_never_resend() -> None:
    assert MAILBOX_AUTO_RESEND is False
    assert LEFTOVER_COMPOSER_IS_COMMAND is False
    cold = mailbox_restore_plan(
        product_session_ref="psess:H",
        cold_start=True,
        leftover_composer="draft in composer",
    )
    assert isinstance(cold, Ok)
    assert cold.value.query == "list_mailbox"
    assert cold.value.command is None
    assert cold.value.auto_resend is False
    assert dict(cold.value.args) == {"product_session_ref": "psess:H"}
    reload_plan = mailbox_restore_plan(
        product_session_ref="psess:H",
        pending_triple={"producer_id": "P", "wire_id": "C1"},
        cold_start=False,
    )
    assert isinstance(reload_plan, Ok)
    assert reload_plan.value.command is None
    assert dict(reload_plan.value.args) == {
        "product_session_ref": "psess:H",
        "producer_id": "P",
        "wire_id": "C1",
    }
    resend = mailbox_restore_plan(
        product_session_ref="psess:H",
        pending_triple={"producer_id": "P", "wire_id": "C1"},
        resend=True,
    )
    assert is_refusal(resend)
    assert resend.context["auto_resend"] is False
    assert refuse_mailbox_auto_resend().context["leftover_composer_is_command"] is False


def test_empty_pair_lookup_is_unknown_not_a_new_send() -> None:
    assert PAIR_LOOKUP_EMPTY_IS_NEW_SEND is False
    assert pair_lookup_disposition(0) == "empty_unknown"
    assert pair_lookup_disposition(1) == "hit"
    substituted = refuse_substitute_live_producer_id(
        stored_producer_id="P",
        given_producer_id="P2",
    )
    assert is_refusal(substituted)
    assert substituted.context["new_send"] is False
    assert substituted.context["empty_unknown"] is True


def test_live_socket_dispatch_absent_at_inspect_sha() -> None:
    assert LIVE_SOCKET_DISPATCH_INSPECT_SHA == "34c148be"
    assert LIVE_SOCKET_DISPATCH_EXISTED_AT_INSPECT_SHA is False
    assert frozenset({"send_message", "list_mailbox"}) == LIVE_SOCKET_DISPATCH_NAMES
    assert is_refusal(claim_live_socket_dispatch_existed_at_inspect_sha("send_message", True))
    assert is_ok(claim_live_socket_dispatch_existed_at_inspect_sha("send_message", False))
    assert is_refusal(claim_live_socket_dispatch_existed_at_inspect_sha("list_mailbox", True))
    assert is_ok(claim_live_socket_dispatch_existed_at_inspect_sha("list_mailbox", False))
    unknown = claim_live_socket_dispatch_existed_at_inspect_sha("cancel_job", False)
    assert is_refusal(unknown)
