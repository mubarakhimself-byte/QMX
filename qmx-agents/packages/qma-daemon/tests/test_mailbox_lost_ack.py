"""Story 69.3 — lost-ack lookup is (producer_id, id) and never auto-resends."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from qma.core.ontology import ActorId, DeskSlug, Quant, RoleName
from qma.core.ports.mailbox import ENVELOPE_PRODUCT_SESSION_FIELD
from qma.daemon import AuthoritativeJournal, PersistenceSubstrate
from qma.daemon.bus.mailbox import MailboxStore
from qma.daemon.bus.mailbox_query import handle_list_mailbox_query
from qma.daemon.sessions import ProductSessionService
from qma.wire.mailbox_send import (
    LIVE_SOCKET_DISPATCH_EXISTED_AT_INSPECT_SHA,
    MAILBOX_AUTO_RESEND,
    MAILBOX_SEND_RETENTION_FLOOR,
    PAIR_LOOKUP_EMPTY_IS_NEW_SEND,
    claim_live_socket_dispatch_existed_at_inspect_sha,
    hash_wire_payload_bytes,
    mailbox_restore_plan,
    pair_lookup_disposition,
)
from qmf.core import DataDrivenClock, Instant, is_ok, is_refusal
from qmf.core.refusal import RefusalCategory


def _actor(desk: DeskSlug, slug: str) -> ActorId:
    minted = ActorId.mint(desk, slug)
    assert is_ok(minted)
    return minted.value


def _quant(*, slug: str) -> Quant:
    return Quant(
        actor_id=_actor(DeskSlug.RESEARCH, slug),
        desk=DeskSlug.RESEARCH,
        quant_slug=slug,
        role=RoleName.RESEARCHER,
        name=f"Quant {slug}",
        lead=False,
    )


def _clock(*, boot: str = "boot-lost-ack", n: int = 32) -> DataDrivenClock:
    base = 1_700_000_000_000_000_000
    walls = tuple(Instant(value_ns=base + i) for i in range(n))
    monos = tuple(i * 1_000 for i in range(n))
    return DataDrivenClock(boot_epoch_id=boot, wall_instants=walls, monotonic_ns=monos)


def _open_journal(
    tmp_path: Path, *, boot: str = "boot-lost-ack"
) -> tuple[PersistenceSubstrate, AuthoritativeJournal]:
    substrate_result = PersistenceSubstrate.open(tmp_path, machine="test-host", boot_epoch_id=boot)
    assert is_ok(substrate_result), substrate_result
    substrate = substrate_result.value
    journal_result = AuthoritativeJournal.bind(substrate, clock=_clock(boot=boot))
    assert is_ok(journal_result), journal_result
    return substrate, journal_result.value


def _mint_session() -> ProductSessionService:
    service = ProductSessionService()
    minted = service.mint(
        product_session_id="psess:H",
        profile="authoring",
        principal="operator",
        contribution={"package_version": "0.1.0", "qualified_id": "analysis-backtest:qmb"},
        instance_id=None,
        config_revision=4,
        as_of="2026-09-20T00:00:00Z",
        granted_ops=(),
        selected_refs=(),
        scope_path=[{"kind": "desk", "id": "research"}],
    )
    assert is_ok(minted), minted
    return service


def _open_store() -> tuple[MailboxStore, Quant, Quant]:
    store = MailboxStore()
    sender = _quant(slug="alpha")
    recipient = _quant(slug="beta")
    assert is_ok(store.open_for_quant(sender))
    assert is_ok(store.open_for_quant(recipient))
    return store, sender, recipient


def _body(
    sender: Quant,
    recipient: Quant,
    *,
    msg_id: str = "msg-1",
    **extra: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "msg_id": msg_id,
        "from": sender.actor_id.value,
        "to": recipient.actor_id.value,
        "kind": "handoff",
        "correlation_id": f"corr-{msg_id}",
        "body": {"text": "hello"},
        "priority": 1,
        "product_session_ref": "psess:H",
        "producer_id": "P",
        "wire_id": "C1",
    }
    payload.update(extra)
    return payload


def test_send_records_pair_and_payload_hash_on_journal(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path)
    try:
        store = MailboxStore(_journal=journal)
        sender = _quant(slug="alpha")
        recipient = _quant(slug="beta")
        assert is_ok(store.open_for_quant(sender))
        assert is_ok(store.open_for_quant(recipient))
        payload = _body(sender, recipient)
        expected = hash_wire_payload_bytes(payload)
        assert is_ok(expected)
        sent = store.send_message(payload, principal_class="operator", sessions=_mint_session())
        assert is_ok(sent)
        assert sent.value.producer_id == "P"
        assert sent.value.wire_id == "C1"
        assert sent.value.payload_hash == expected.value
        identity_is_pair = (sent.value.producer_id, sent.value.wire_id)
        assert identity_is_pair == ("P", "C1")
        rows = journal.read_all()
        assert is_ok(rows)
        recorded: dict[str, object] | None = None
        for row in rows.value:
            payload_obj = row.get("payload")
            if not isinstance(payload_obj, dict):
                continue
            payload_map = cast("dict[str, object]", payload_obj)
            if payload_map.get("producer_id") == "P":
                recorded = payload_map
                break
        assert recorded is not None
        assert recorded["wire_id"] == "C1"
        assert recorded["payload_hash"] == expected.value
        nested = recorded.get("envelope")
        assert isinstance(nested, dict)
        assert nested["msg_id"] == "msg-1"
    finally:
        journal.close()
        substrate.close()


def test_lost_ack_pair_lookup_returns_landed_row_with_msg_id() -> None:
    store, sender, recipient = _open_store()
    sessions = _mint_session()
    payload = _body(sender, recipient)
    sent = store.send_message(payload, principal_class="operator", sessions=sessions)
    assert is_ok(sent)
    expected = hash_wire_payload_bytes(payload)
    assert is_ok(expected)
    listed = handle_list_mailbox_query(
        store,
        {
            ENVELOPE_PRODUCT_SESSION_FIELD: "psess:H",
            "producer_id": "P",
            "wire_id": "C1",
            "msg_id": "client-does-not-have-this",
        },
        operator_principal="operator",
        sessions=sessions,
    )
    assert is_ok(listed)
    assert len(listed.value.rows) == 1
    row = listed.value.rows[0]
    assert row.msg_id == "msg-1"
    assert row.producer_id == "P"
    assert row.wire_id == "C1"
    assert row.payload_hash == expected.value
    session_rows = handle_list_mailbox_query(
        store,
        {ENVELOPE_PRODUCT_SESSION_FIELD: "psess:H"},
        operator_principal="operator",
        sessions=sessions,
    )
    assert is_ok(session_rows)
    assert session_rows.value.rows[0].payload_hash == expected.value


def test_same_pair_same_hash_returns_prior_result() -> None:
    store, sender, recipient = _open_store()
    sessions = _mint_session()
    first = store.send_message(
        _body(sender, recipient), principal_class="operator", sessions=sessions
    )
    assert is_ok(first)
    before = store.journal_event_count()
    replay = store.send_message(
        _body(sender, recipient),
        principal_class="operator",
        sessions=sessions,
    )
    assert is_ok(replay)
    assert replay.value.envelope.msg_id == first.value.envelope.msg_id
    assert replay.value.payload_hash == first.value.payload_hash
    assert store.journal_event_count() == before


def test_same_pair_different_hash_refuses_for_journal_lifetime() -> None:
    store, sender, recipient = _open_store()
    sessions = _mint_session()
    first = store.send_message(
        _body(sender, recipient), principal_class="operator", sessions=sessions
    )
    assert is_ok(first)
    before = store.journal_event_count()
    collided = store.send_message(
        _body(sender, recipient, msg_id="msg-2", body={"text": "different"}),
        principal_class="operator",
        sessions=sessions,
    )
    assert is_refusal(collided)
    assert collided.category is RefusalCategory.POLICY_REJECTION
    assert collided.context["reason"] == "payload_hash_collision"
    assert collided.context["retention"] == MAILBOX_SEND_RETENTION_FLOOR
    assert collided.context["successful_prior_ack"] is False
    assert collided.context["mailbox_sends_only"] is True
    assert store.journal_event_count() == before
    assert store.record_for("msg-2") is None


def test_cold_start_restore_queries_session_and_never_auto_resends() -> None:
    store, sender, recipient = _open_store()
    sessions = _mint_session()
    assert is_ok(
        store.send_message(_body(sender, recipient), principal_class="operator", sessions=sessions)
    )
    before = store.journal_event_count()
    plan = mailbox_restore_plan(
        product_session_ref="psess:H",
        cold_start=True,
        leftover_composer="unsent draft",
    )
    assert is_ok(plan)
    assert plan.value.auto_resend is False is MAILBOX_AUTO_RESEND
    assert "producer_id" not in plan.value.args
    listed = handle_list_mailbox_query(
        store,
        plan.value.args,
        operator_principal="operator",
        sessions=sessions,
    )
    assert is_ok(listed)
    assert listed.value.product_chat is True
    assert store.journal_event_count() == before
    resend = mailbox_restore_plan(product_session_ref="psess:H", resend=True)
    assert is_refusal(resend)


def test_empty_pair_lookup_is_unknown_not_a_new_send() -> None:
    store, sender, recipient = _open_store()
    sessions = _mint_session()
    assert is_ok(
        store.send_message(_body(sender, recipient), principal_class="operator", sessions=sessions)
    )
    before = store.journal_event_count()
    miss = handle_list_mailbox_query(
        store,
        {
            ENVELOPE_PRODUCT_SESSION_FIELD: "psess:H",
            "producer_id": "P",
            "wire_id": "C2",
        },
        operator_principal="operator",
        sessions=sessions,
    )
    assert is_ok(miss)
    assert miss.value.rows == ()
    assert pair_lookup_disposition(len(miss.value.rows)) == "empty_unknown"
    assert PAIR_LOOKUP_EMPTY_IS_NEW_SEND is False
    assert store.journal_event_count() == before
    assert store.record_for("msg-1") is not None
    later_producer = handle_list_mailbox_query(
        store,
        {
            ENVELOPE_PRODUCT_SESSION_FIELD: "psess:H",
            "producer_id": "P2",
            "wire_id": "C1",
        },
        operator_principal="operator",
        sessions=sessions,
    )
    assert is_ok(later_producer)
    assert later_producer.value.rows == ()
    substituted = store.list_mailbox(
        {
            ENVELOPE_PRODUCT_SESSION_FIELD: "psess:H",
            "producer_id": "P",
            "wire_id": "C1",
            "substitute_producer_id": "P2",
        }
    )
    assert is_refusal(substituted)
    assert substituted.context["field"] == "producer_id"


def test_live_socket_dispatch_was_absent_at_inspect_sha() -> None:
    assert LIVE_SOCKET_DISPATCH_EXISTED_AT_INSPECT_SHA is False
    assert is_refusal(claim_live_socket_dispatch_existed_at_inspect_sha("send_message", True))
    assert is_refusal(claim_live_socket_dispatch_existed_at_inspect_sha("list_mailbox", True))


def test_pair_collision_and_snapshot_survive_fresh_store(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path, boot="boot-fold-1")
    try:
        store = MailboxStore(_journal=journal)
        sender = _quant(slug="alpha")
        recipient = _quant(slug="beta")
        assert is_ok(store.open_for_quant(sender))
        assert is_ok(store.open_for_quant(recipient))
        sessions = _mint_session()
        payload = _body(sender, recipient)
        sent = store.send_message(payload, principal_class="operator", sessions=sessions)
        assert is_ok(sent)
        assert sent.value.envelope.msg_id == "msg-1"
    finally:
        journal.close()
        substrate.close()

    substrate2, journal2 = _open_journal(tmp_path, boot="boot-fold-2")
    try:
        store2 = MailboxStore(_journal=journal2)
        sessions2 = _mint_session()
        sender = _quant(slug="alpha")
        recipient = _quant(slug="beta")
        listed = store2.list_mailbox({ENVELOPE_PRODUCT_SESSION_FIELD: "psess:H"})
        assert is_ok(listed)
        assert listed.value.product_chat is True
        assert len(listed.value.rows) == 1
        assert listed.value.rows[0].msg_id == "msg-1"
        assert listed.value.rows[0].producer_id == "P"
        assert listed.value.rows[0].wire_id == "C1"
        collided = store2.send_message(
            _body(sender, recipient, msg_id="msg-2", body={"text": "different"}),
            principal_class="operator",
            sessions=sessions2,
        )
        assert is_refusal(collided)
        assert collided.category is RefusalCategory.POLICY_REJECTION
        assert collided.context["reason"] == "payload_hash_collision"
        assert collided.context["retention"] == MAILBOX_SEND_RETENTION_FLOOR
        assert store2.record_for("msg-2") is None
        replay = store2.send_message(
            _body(sender, recipient),
            principal_class="operator",
            sessions=sessions2,
        )
        assert is_ok(replay)
        assert replay.value.envelope.msg_id == "msg-1"
    finally:
        journal2.close()
        substrate2.close()
