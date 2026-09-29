"""Story 69.4 — mailbox send_message inherits product_session_ref; no retarget."""

from __future__ import annotations

from qma.core.ontology import ActorId, DeskSlug, Quant, RoleName
from qma.core.ports.mailbox import (
    DELIVERY_STATE_VALUES,
    ENVELOPE_PRODUCT_SESSION_FIELD,
    INHERITING_MESSAGE_KINDS,
    MESSAGE_KIND_VALUES,
    PRODUCT_CHAT_MESSAGE_KINDS,
)
from qma.core.vocabulary.enums import DeliveryState, MessageKind
from qma.daemon.bus import (
    MailboxStore,
    inherit_product_session_ref_at_write,
    refuse_mailbox_instance_mint,
    refuse_product_session_retarget,
)
from qma.daemon.sessions import ProductSessionService
from qma.wire import (
    LIVE_CT40_SERVING_SEND_MESSAGE_EXISTED_AT_INSPECT_SHA,
    MAILBOX_SEND_IS_INVOKE,
    MAILBOX_SEND_REQUIRES_GRANT_RECORD,
    MAILBOX_SEND_REQUIRES_INSTANCE_ID,
    SEND_MESSAGE_SEED_NAME_EXISTED_AT_INSPECT_SHA,
    WireCommand,
    claim_live_ct40_serving_send_message_existed_at_inspect_sha,
    claim_send_message_seed_name_absent_at_inspect_sha,
    claim_this_story_scaffolded_qmx_ui,
    list_mailbox_snapshots_are_truth,
)
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
    instance_id: str | None = None,
    selected_refs: tuple[object, ...] = (),
) -> ProductSessionService:
    service = ProductSessionService()
    minted = service.mint(
        product_session_id=product_session_id,
        profile="authoring",
        principal=principal,
        contribution={"package_version": "0.1.0", "qualified_id": "analysis-backtest:qmb"},
        instance_id=instance_id,
        config_revision=4,
        as_of="2026-09-20T00:00:00Z",
        granted_ops=(),
        selected_refs=selected_refs,
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
    kind: str = "handoff",
    **extra: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "msg_id": msg_id,
        "from": sender.actor_id.value,
        "to": recipient.actor_id.value,
        "kind": kind,
        "correlation_id": f"corr-{msg_id}",
        "body": {"text": "hello"},
        "priority": 1,
    }
    payload.update(extra)
    return payload


def test_authoring_without_instance_is_legal_and_does_not_mint() -> None:
    store, sender, recipient = _open_store()
    sessions = _mint_session(instance_id=None, selected_refs=())
    session = sessions.get("psess:H")
    assert is_ok(session)
    assert session.value.app_instance_id is None
    assert session.value.selected_refs == ()
    sent = store.send_message(
        _body(sender, recipient, product_session_ref="psess:H"),
        principal_class="operator",
        sessions=sessions,
    )
    assert is_ok(sent)
    assert sent.value.envelope.product_session_ref == "psess:H"
    assert "instance_id" not in sent.value.envelope.to_payload()
    again = sessions.get("psess:H")
    assert is_ok(again)
    assert again.value.app_instance_id is None
    assert again.value.selected_refs == ()
    minted = store.send_message(
        _body(
            sender,
            recipient,
            msg_id="msg-mint",
            product_session_ref="psess:H",
            mint_instance="inst:synthetic",
        ),
        principal_class="operator",
        sessions=sessions,
    )
    assert is_refusal(minted)
    assert minted.context["field"] == "instance_id"
    assert minted.context["minted"] is False
    invoke_keys = store.send_message(
        _body(sender, recipient, msg_id="msg-inv", instance_id="inst:1"),
        principal_class="operator",
        sessions=sessions,
    )
    assert is_refusal(invoke_keys)
    assert invoke_keys.context["field"] == "instance_id"
    assert invoke_keys.context["invoke"] is False
    assert MAILBOX_SEND_IS_INVOKE is False
    assert MAILBOX_SEND_REQUIRES_INSTANCE_ID is False
    assert MAILBOX_SEND_REQUIRES_GRANT_RECORD is False


def test_reply_inherits_product_session_ref_and_cannot_retarget() -> None:
    store, sender, recipient = _open_store()
    sessions = _mint_session()
    other = _mint_session(product_session_id="psess:B")
    parent = store.send_message(
        _body(sender, recipient, product_session_ref="psess:H"),
        principal_class="operator",
        sessions=sessions,
    )
    assert is_ok(parent)
    inherited = store.send_message(
        _body(
            recipient,
            sender,
            msg_id="msg-reply",
            kind="reply",
            reply_to_ref="msg-1",
            causation_id="msg-1",
        ),
        principal_class="operator",
        sessions=sessions,
    )
    assert is_ok(inherited)
    assert inherited.value.envelope.product_session_ref == "psess:H"
    assert inherited.value.envelope.kind is MessageKind.REPLY
    matching = store.send_message(
        _body(
            recipient,
            sender,
            msg_id="msg-reply-named",
            kind="reply",
            reply_to_ref="msg-1",
            product_session_ref="psess:H",
        ),
        principal_class="operator",
        sessions=sessions,
    )
    assert is_ok(matching)
    assert matching.value.envelope.product_session_ref == "psess:H"
    retarget = store.send_message(
        _body(
            recipient,
            sender,
            msg_id="msg-retarget",
            kind="reply",
            reply_to_ref="msg-1",
            product_session_ref="psess:B",
        ),
        principal_class="operator",
        sessions=other,
    )
    assert is_refusal(retarget)
    assert retarget.context["field"] == ENVELOPE_PRODUCT_SESSION_FIELD
    assert retarget.context["retarget"] is False
    question = store.send_message(
        _body(
            recipient,
            sender,
            msg_id="msg-q",
            kind="question",
            causation_id="msg-1",
        ),
        principal_class="operator",
        sessions=sessions,
    )
    assert is_ok(question)
    assert question.value.envelope.product_session_ref == "psess:H"
    assert question.value.envelope.kind is MessageKind.QUESTION
    missing_parent = store.send_message(
        _body(
            recipient,
            sender,
            msg_id="msg-orphan",
            kind="reply",
            reply_to_ref="msg-missing",
        ),
        principal_class="operator",
        sessions=sessions,
    )
    assert is_refusal(missing_parent)
    assert missing_parent.context["parent_found"] is False


def test_daemon_originated_reply_cannot_accept_arbitrary_session() -> None:
    store, sender, recipient = _open_store()
    sessions = _mint_session()
    parent = store.send_message(
        _body(sender, recipient, product_session_ref="psess:H"),
        principal_class="operator",
        sessions=sessions,
    )
    assert is_ok(parent)
    inherited = store.send_message(
        _body(
            recipient,
            sender,
            msg_id="msg-daemon",
            kind="reply",
            reply_to_ref="msg-1",
        ),
        principal_class="machine",
        sessions=sessions,
    )
    assert is_ok(inherited)
    assert inherited.value.envelope.product_session_ref == "psess:H"
    arbitrary = store.send_message(
        _body(
            recipient,
            sender,
            msg_id="msg-arb",
            kind="reply",
            product_session_ref="psess:H",
        ),
        principal_class="machine",
        sessions=sessions,
    )
    assert is_refusal(arbitrary)
    assert arbitrary.context["arbitrary"] is True
    retarget = inherit_product_session_ref_at_write(
        {"kind": "reply", "reply_to_ref": "msg-1", "product_session_ref": "psess:B"},
        {"kind": "reply", "reply_to_ref": "msg-1", "product_session_ref": "psess:B"},
        parent.value.envelope,
        parent_named=True,
        principal_class="machine",
    )
    assert is_refusal(retarget)
    assert retarget.context["retarget"] is False


def test_home_composer_cannot_mint_approval_request() -> None:
    store, sender, recipient = _open_store()
    sessions = _mint_session()
    approval = store.send_message(
        _body(
            sender,
            recipient,
            kind="approval_request",
            product_session_ref="psess:H",
        ),
        principal_class="operator",
        sessions=sessions,
    )
    assert is_refusal(approval)
    assert approval.context["field"] == "kind"
    review = store.send_message(
        _body(
            sender,
            recipient,
            msg_id="msg-rev",
            kind="review_request",
            product_session_ref="psess:H",
        ),
        principal_class="operator",
        sessions=sessions,
    )
    assert is_refusal(review)
    grant = store.send_message(
        _body(sender, recipient, msg_id="msg-grant", grant_id="grant:1"),
        principal_class="operator",
        sessions=sessions,
    )
    assert is_refusal(grant)
    assert grant.context["field"] == "grant_id"


def test_closed_vocabs_and_list_mailbox_remain_truth() -> None:
    assert {"reply", "question"} == INHERITING_MESSAGE_KINDS
    assert {
        "handoff",
        "reply",
        "notify",
        "status",
        "question",
    } == PRODUCT_CHAT_MESSAGE_KINDS
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
    assert list_mailbox_snapshots_are_truth() is True
    refused = refuse_product_session_retarget(parent_ref="psess:H", given="psess:B")
    assert refused.category is RefusalCategory.POLICY_REJECTION
    minted = refuse_mailbox_instance_mint()
    assert minted.context["minted"] is False


def test_inspect_sha_live_serving_absent_seed_present() -> None:
    assert LIVE_CT40_SERVING_SEND_MESSAGE_EXISTED_AT_INSPECT_SHA is False
    assert SEND_MESSAGE_SEED_NAME_EXISTED_AT_INSPECT_SHA is True
    assert WireCommand.SEND_MESSAGE.value == "send_message"
    assert is_refusal(claim_live_ct40_serving_send_message_existed_at_inspect_sha(True))
    assert is_ok(claim_live_ct40_serving_send_message_existed_at_inspect_sha(False))
    assert is_refusal(claim_send_message_seed_name_absent_at_inspect_sha(True))
    assert is_ok(claim_send_message_seed_name_absent_at_inspect_sha(False))
    assert is_refusal(claim_this_story_scaffolded_qmx_ui(True))
    assert is_ok(claim_this_story_scaffolded_qmx_ui(False))
