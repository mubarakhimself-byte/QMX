"""Story 69.2 — list_mailbox fold admits by principal equality."""

from __future__ import annotations

from qma.core.ontology import ActorId, DeskSlug, Quant, RoleName
from qma.core.ports.mailbox import ENVELOPE_PRODUCT_SESSION_FIELD
from qma.daemon.bus import MailboxStore, handle_list_mailbox_query
from qma.daemon.sessions import ProductSessionService
from qma.wire.list_mailbox import LIST_MAILBOX_CAPABILITY, LIST_MAILBOX_EXISTED_AT_INSPECT_SHA
from qmf.core import is_ok, is_refusal
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


def _mint_session(
    *,
    product_session_id: str = "psess:H",
    principal: str = "operator",
) -> ProductSessionService:
    service = ProductSessionService()
    minted = service.mint(
        product_session_id=product_session_id,
        profile="authoring",
        principal=principal,
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
    }
    payload.update(extra)
    return payload


def test_list_mailbox_was_absent_at_inspect_sha() -> None:
    assert LIST_MAILBOX_EXISTED_AT_INSPECT_SHA is False


def test_present_query_on_new_psess_is_empty_mailbox() -> None:
    store, _sender, _recipient = _open_store()
    sessions = _mint_session()
    listed = handle_list_mailbox_query(
        store,
        {ENVELOPE_PRODUCT_SESSION_FIELD: "psess:H"},
        operator_principal="operator",
        sessions=sessions,
    )
    assert is_ok(listed)
    assert listed.value.product_chat is True
    assert listed.value.product_session_ref == "psess:H"
    assert listed.value.rows == ()


def test_query_unavailable_never_empty_mailbox() -> None:
    store, _sender, _recipient = _open_store()
    sessions = _mint_session()
    refused = handle_list_mailbox_query(
        store,
        {ENVELOPE_PRODUCT_SESSION_FIELD: "psess:H"},
        operator_principal="operator",
        sessions=sessions,
        capabilities={},
    )
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["reason"] == "query_unavailable"
    assert refused.context["name"] == "list_mailbox"
    assert refused.context["empty_mailbox"] is False


def test_session_snapshot_omits_rows_without_field() -> None:
    store, sender, recipient = _open_store()
    sessions = _mint_session()
    machine = store.send_message(
        _body(sender, recipient, msg_id="msg-machine", body={"text": "restore psess:H"}),
        principal_class="machine",
    )
    assert is_ok(machine)
    named = store.send_message(
        _body(sender, recipient, msg_id="msg-home", product_session_ref="psess:H"),
        principal_class="operator",
        sessions=sessions,
    )
    assert is_ok(named)
    listed = handle_list_mailbox_query(
        store,
        {ENVELOPE_PRODUCT_SESSION_FIELD: "psess:H"},
        operator_principal="operator",
        sessions=sessions,
    )
    assert is_ok(listed)
    assert listed.value.product_chat is True
    assert len(listed.value.rows) == 1
    row = listed.value.rows[0]
    assert row.msg_id == "msg-home"
    assert row.envelope[ENVELOPE_PRODUCT_SESSION_FIELD] == "psess:H"
    assert row.delivery_state == "queued"


def test_list_mailbox_without_psess_is_not_product_chat() -> None:
    store, sender, recipient = _open_store()
    sessions = _mint_session()
    assert is_ok(
        store.send_message(
            _body(sender, recipient, product_session_ref="psess:H"),
            principal_class="operator",
            sessions=sessions,
        )
    )
    listed = handle_list_mailbox_query(
        store,
        {},
        operator_principal="operator",
        sessions=sessions,
    )
    assert is_ok(listed)
    assert listed.value.product_chat is False
    assert listed.value.rows == ()
    assert listed.value.product_session_ref is None


def test_principal_mismatch_is_typed_refusal() -> None:
    store, sender, recipient = _open_store()
    sessions = _mint_session(principal="operator")
    assert is_ok(
        store.send_message(
            _body(sender, recipient, product_session_ref="psess:H"),
            principal_class="operator",
            sessions=sessions,
        )
    )
    refused = handle_list_mailbox_query(
        store,
        {ENVELOPE_PRODUCT_SESSION_FIELD: "psess:H"},
        operator_principal="machine",
        sessions=sessions,
    )
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["field"] == "principal"
    assert refused.context["empty_mailbox"] is False
    send_refused = store.send_message(
        _body(sender, recipient, msg_id="msg-mismatch", product_session_ref="psess:H"),
        principal_class="machine",
        sessions=sessions,
    )
    assert is_refusal(send_refused)
    assert send_refused.context["field"] == "principal"


def test_unknown_psess_is_typed_refusal_not_empty() -> None:
    store, _sender, _recipient = _open_store()
    sessions = _mint_session()
    refused = handle_list_mailbox_query(
        store,
        {ENVELOPE_PRODUCT_SESSION_FIELD: "psess:missing"},
        operator_principal="operator",
        sessions=sessions,
    )
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.INVALID_INPUT


def test_pair_lookup_returns_zero_or_one_without_client_msg_id() -> None:
    store, sender, recipient = _open_store()
    sessions = _mint_session()
    sent = store.send_message(
        _body(
            sender,
            recipient,
            product_session_ref="psess:H",
            producer_id="tab:P",
            wire_id="C1",
        ),
        principal_class="operator",
        sessions=sessions,
    )
    assert is_ok(sent)
    assert sent.value.producer_id == "tab:P"
    assert sent.value.wire_id == "C1"
    hit = handle_list_mailbox_query(
        store,
        {
            ENVELOPE_PRODUCT_SESSION_FIELD: "psess:H",
            "producer_id": "tab:P",
            "wire_id": "C1",
            "msg_id": "client-unknown",
        },
        operator_principal="operator",
        sessions=sessions,
    )
    assert is_ok(hit)
    assert len(hit.value.rows) == 1
    row = hit.value.rows[0]
    assert row.msg_id == "msg-1"
    assert row.producer_id == "tab:P"
    assert row.wire_id == "C1"
    miss = handle_list_mailbox_query(
        store,
        {
            ENVELOPE_PRODUCT_SESSION_FIELD: "psess:H",
            "producer_id": "tab:P",
            "wire_id": "other",
        },
        operator_principal="operator",
        sessions=sessions,
    )
    assert is_ok(miss)
    assert miss.value.product_chat is True
    assert miss.value.rows == ()


def test_ordinary_chat_needs_no_grant_record() -> None:
    store, sender, recipient = _open_store()
    sessions = _mint_session()
    sent = store.send_message(
        _body(sender, recipient, product_session_ref="psess:H"),
        principal_class="operator",
        sessions=sessions,
    )
    assert is_ok(sent)
    assert "grant_id" not in sent.value.envelope.to_payload()
    listed = handle_list_mailbox_query(
        store,
        {ENVELOPE_PRODUCT_SESSION_FIELD: "psess:H"},
        operator_principal="operator",
        sessions=sessions,
        capabilities={LIST_MAILBOX_CAPABILITY: True},
    )
    assert is_ok(listed)
    assert len(listed.value.rows) == 1
