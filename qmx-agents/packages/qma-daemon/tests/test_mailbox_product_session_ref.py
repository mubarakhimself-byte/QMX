"""Story 69.1 — copy product_session_ref onto Envelope at send_message write."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from qma.core.content import content_address
from qma.core.ontology import ActorId, DeskSlug, Quant, RoleName
from qma.core.ports.mailbox import (
    ENVELOPE_PRODUCT_SESSION_FIELD,
    envelope_identity_content,
    parse_envelope,
)
from qma.core.vocabulary.enums import DeliveryState
from qma.daemon import AuthoritativeJournal, PersistenceSubstrate
from qma.daemon.bus import MailboxStore, copy_product_session_ref_at_write
from qma.daemon.sessions import ProductSessionService
from qmf.core import DataDrivenClock, Instant, is_ok, is_refusal


def _actor(desk: DeskSlug, slug: str) -> ActorId:
    minted = ActorId.mint(desk, slug)
    assert is_ok(minted)
    return minted.value


def _quant(*, slug: str = "lead", lead: bool = True) -> Quant:
    return Quant(
        actor_id=_actor(DeskSlug.RESEARCH, slug),
        desk=DeskSlug.RESEARCH,
        quant_slug=slug,
        role=RoleName.RESEARCHER,
        name=f"Quant {slug}",
        lead=lead,
    )


def _clock(*, boot: str = "boot-psess", n: int = 32) -> DataDrivenClock:
    base = 1_700_000_000_000_000_000
    walls = tuple(Instant(value_ns=base + i) for i in range(n))
    monos = tuple(i * 1_000 for i in range(n))
    return DataDrivenClock(boot_epoch_id=boot, wall_instants=walls, monotonic_ns=monos)


def _open_journal(
    tmp_path: Path, *, boot: str = "boot-psess"
) -> tuple[PersistenceSubstrate, AuthoritativeJournal]:
    substrate_result = PersistenceSubstrate.open(tmp_path, machine="test-host", boot_epoch_id=boot)
    assert is_ok(substrate_result), substrate_result
    substrate = substrate_result.value
    journal_result = AuthoritativeJournal.bind(substrate, clock=_clock(boot=boot))
    assert is_ok(journal_result), journal_result
    return substrate, journal_result.value


def _sessions(*, product_session_id: str = "psess:H") -> ProductSessionService:
    service = ProductSessionService()
    minted = service.mint(
        product_session_id=product_session_id,
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


def _send_body(
    sender: Quant,
    recipient: Quant,
    *,
    msg_id: str = "msg-1",
    kind: str = "handoff",
    **extra: object,
) -> dict[str, object]:
    body: dict[str, object] = {
        "msg_id": msg_id,
        "from": sender.actor_id.value,
        "to": recipient.actor_id.value,
        "kind": kind,
        "correlation_id": f"corr-{msg_id}",
        "body": {"text": "hello"},
        "priority": 1,
    }
    body.update(extra)
    return body


def test_operator_send_message_copies_product_session_ref_at_write() -> None:
    store = MailboxStore()
    sender = _quant(slug="alpha", lead=False)
    recipient = _quant(slug="beta", lead=False)
    assert is_ok(store.open_for_quant(sender))
    assert is_ok(store.open_for_quant(recipient))
    payload = _send_body(sender, recipient, product_session_ref="psess:H")
    sent = store.send_message(payload, principal_class="operator", sessions=_sessions())
    assert is_ok(sent)
    envelope = sent.value.envelope
    assert envelope.product_session_ref == "psess:H"
    assert sent.value.state is DeliveryState.QUEUED
    payload_out = envelope.to_payload()
    assert payload_out[ENVELOPE_PRODUCT_SESSION_FIELD] == "psess:H"


def test_machine_send_message_omits_product_session_ref() -> None:
    store = MailboxStore()
    sender = _quant(slug="alpha", lead=False)
    recipient = _quant(slug="beta", lead=False)
    store.open_for_quant(sender)
    store.open_for_quant(recipient)
    sent = store.send_message(_send_body(sender, recipient), principal_class="machine")
    assert is_ok(sent)
    assert sent.value.envelope.product_session_ref is None
    assert "product_session_ref" not in sent.value.envelope.to_payload()


def test_quant_bus_send_omits_product_session_ref() -> None:
    store = MailboxStore()
    sender = _quant(slug="alpha", lead=False)
    recipient = _quant(slug="beta", lead=False)
    store.open_for_quant(sender)
    store.open_for_quant(recipient)
    sent = store.send(_send_body(sender, recipient, kind="notify", body="bus ping"))
    assert is_ok(sent)
    assert sent.value.envelope.product_session_ref is None
    assert "product_session_ref" not in sent.value.envelope.to_payload()


def test_body_text_is_never_parsed_for_session() -> None:
    store = MailboxStore()
    sender = _quant(slug="alpha", lead=False)
    recipient = _quant(slug="beta", lead=False)
    store.open_for_quant(sender)
    store.open_for_quant(recipient)
    payload = _send_body(
        sender,
        recipient,
        body={"text": "please restore psess:H", "product_session_ref": "psess:H"},
    )
    sent = store.send_message(payload, principal_class="operator")
    assert is_ok(sent)
    assert sent.value.envelope.product_session_ref is None
    assert "product_session_ref" not in sent.value.envelope.to_payload()


def test_copy_at_write_uses_payload_field_not_body() -> None:
    envelope = {
        "msg_id": "msg-1",
        "from": "quant:research/alpha",
        "to": "quant:research/beta",
        "kind": "handoff",
        "correlation_id": "corr-1",
        "body": {"text": "psess:BODY"},
        "priority": 0,
        "created_at": 1,
    }
    copied = copy_product_session_ref_at_write(
        envelope, {"product_session_ref": "psess:H", "body": envelope["body"]}
    )
    assert is_ok(copied)
    assert copied.value["product_session_ref"] == "psess:H"
    omitted = copy_product_session_ref_at_write(envelope, {"body": envelope["body"]})
    assert is_ok(omitted)
    assert "product_session_ref" not in omitted.value
    null = copy_product_session_ref_at_write(envelope, {"product_session_ref": None})
    assert is_refusal(null)
    assert null.context["field"] == "product_session_ref"
    aliased = copy_product_session_ref_at_write(envelope, {"product_session_id": "psess:H"})
    assert is_refusal(aliased)
    assert aliased.context["field"] == "product_session_id"


def test_journal_message_row_persists_copied_product_session_ref(tmp_path: Path) -> None:
    substrate, journal = _open_journal(tmp_path)
    try:
        store = MailboxStore(_journal=journal)
        sender = _quant(slug="alpha", lead=False)
        recipient = _quant(slug="beta", lead=False)
        store.open_for_quant(sender)
        store.open_for_quant(recipient)
        sent = store.send_message(
            _send_body(sender, recipient, product_session_ref="psess:H"),
            principal_class="operator",
            sessions=_sessions(),
        )
        assert is_ok(sent)
        rows = journal.read_all()
        assert is_ok(rows)
        recorded: dict[str, object] | None = None
        for row in rows.value:
            payload_obj = row.get("payload")
            if not isinstance(payload_obj, dict):
                continue
            payload = cast("dict[str, object]", payload_obj)
            nested_obj: object | None = payload.get("envelope")
            if isinstance(nested_obj, dict):
                recorded = cast("dict[str, object]", nested_obj)
                break
        assert recorded is not None
        assert recorded["product_session_ref"] == "psess:H"
        first = parse_envelope(recorded)
        retarget_body = dict(recorded)
        retarget_body["product_session_ref"] = "psess:B"
        retarget = parse_envelope(retarget_body)
        assert is_ok(first) and is_ok(retarget)
        hashed_a = content_address(dict(envelope_identity_content(first.value)))
        hashed_b = content_address(dict(envelope_identity_content(retarget.value)))
        assert is_ok(hashed_a) and is_ok(hashed_b)
        assert hashed_a.value == hashed_b.value
    finally:
        journal.close()
        substrate.close()
