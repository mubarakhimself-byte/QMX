"""Seed ``send_message`` is mailbox delivery, not invoke (Story 69.4).

Story 69.1 / AM-02 / AM-14 / DEC-0495: payload may name additive
``product_session_ref``. COMP-QMA-WIRE owns the seed command name. The
daemon copies the named field onto the CT-48 Envelope at write. Optional
value is an omitted key, never null. Machine payloads may omit it.

Story 69.4 / DEC-0484: Home/Copilot product chat remains mailbox
``send_message``. It does not build an ``InvocationEnvelope``, does not
require ``instance_id`` or a GrantRecord, and does not use invoke
``idempotency_key`` or product-session ``command_id`` as send identity.
Unique chrome issuer ``dispatchChat`` is Epic 66 — do not scaffold
``apps/qmx-ui``. Live CT-40 serving of ``send_message`` was absent at
inspect SHA ``34c148be``; the seed name ``WireCommand.SEND_MESSAGE``
existed (DEC-0507).
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final, cast

from qma.core.ports.mailbox import (
    ENVELOPE_PRODUCT_SESSION_FIELD,
    FORBIDDEN_ENVELOPE_SESSION_FIELDS,
    MAILBOX_INSPECT_SHA,
    PRODUCT_CHAT_MESSAGE_KINDS,
    PRODUCT_SESSION_REF_PREFIX,
)
from qma.core.vocabulary.enums import MessageKind
from qma.wire.families import progress_is_authoritative, snapshots_are_authoritative
from qma.wire.vocabulary import WireCommand, WireEvent, WireQuery
from qmf.core.refusal import (
    Ok,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
)

__all__ = [
    "DISPATCH_CHAT_IS_THIS_STORY",
    "FORBIDDEN_MAILBOX_CHAT_CONTRACT_KEYS",
    "HOME_COMPOSER_FORBIDDEN_KINDS",
    "LIVE_CT40_SERVING_SEND_MESSAGE_EXISTED_AT_INSPECT_SHA",
    "LIVE_CT40_SERVING_SEND_MESSAGE_INSPECT_SHA",
    "MAILBOX_SEND_IS_INVOKE",
    "MAILBOX_SEND_REQUIRES_GRANT_RECORD",
    "MAILBOX_SEND_REQUIRES_INSTANCE_ID",
    "MAILBOX_SEND_USES_COMMAND_ID_IDENTITY",
    "MAILBOX_SEND_USES_INVOKE_IDEMPOTENCY_KEY",
    "MESSAGE_DELTA_IS_PROGRESS_ONLY",
    "PRODUCT_CHAT_MESSAGE_KINDS",
    "QMX_UI_SCAFFOLDED_THIS_STORY",
    "SEND_MESSAGE_COMMAND",
    "SEND_MESSAGE_SEED_NAME_EXISTED_AT_INSPECT_SHA",
    "TRANSCRIPT_IS_MEMORY_PROVIDER",
    "TRANSCRIPT_IS_NEW_STORE",
    "TRANSCRIPT_IS_PRIVATE_NOTES",
    "TRANSCRIPT_IS_SESS",
    "claim_live_ct40_serving_send_message_existed_at_inspect_sha",
    "claim_send_message_seed_name_absent_at_inspect_sha",
    "claim_this_story_scaffolded_qmx_ui",
    "list_mailbox_snapshots_are_truth",
    "parse_send_message_payload",
    "refuse_mailbox_chat_contract",
    "refuse_mailbox_send_as_invoke",
]


SEND_MESSAGE_COMMAND: Final[str] = WireCommand.SEND_MESSAGE.value
MAILBOX_SEND_IS_INVOKE: Final[bool] = False
MAILBOX_SEND_REQUIRES_INSTANCE_ID: Final[bool] = False
MAILBOX_SEND_REQUIRES_GRANT_RECORD: Final[bool] = False
MAILBOX_SEND_USES_INVOKE_IDEMPOTENCY_KEY: Final[bool] = False
MAILBOX_SEND_USES_COMMAND_ID_IDENTITY: Final[bool] = False
DISPATCH_CHAT_IS_THIS_STORY: Final[bool] = False
QMX_UI_SCAFFOLDED_THIS_STORY: Final[bool] = False
LIVE_CT40_SERVING_SEND_MESSAGE_INSPECT_SHA: Final[str] = MAILBOX_INSPECT_SHA
LIVE_CT40_SERVING_SEND_MESSAGE_EXISTED_AT_INSPECT_SHA: Final[bool] = False
SEND_MESSAGE_SEED_NAME_EXISTED_AT_INSPECT_SHA: Final[bool] = True
MESSAGE_DELTA_IS_PROGRESS_ONLY: Final[bool] = True
TRANSCRIPT_IS_PRIVATE_NOTES: Final[bool] = False
TRANSCRIPT_IS_SESS: Final[bool] = False
TRANSCRIPT_IS_MEMORY_PROVIDER: Final[bool] = False
TRANSCRIPT_IS_NEW_STORE: Final[bool] = False
HOME_COMPOSER_FORBIDDEN_KINDS: Final[frozenset[str]] = frozenset(
    {MessageKind.APPROVAL_REQUEST.value, MessageKind.REVIEW_REQUEST.value}
)
FORBIDDEN_MAILBOX_CHAT_CONTRACT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "logical_invocation_id",
        "grant_id",
        "op_id",
        "instance_id",
        "idempotency_key",
        "caller_kind",
        "input_hash",
    }
)
_FORBIDDEN_SEND_IDENTITY_KEYS: Final[frozenset[str]] = frozenset({"command_id"})
_FORBIDDEN_TRANSCRIPT_KEYS: Final[frozenset[str]] = frozenset(
    {"private_notes", "MemoryProvider", "memory_provider"}
)


def _invalid(field: str, reason: str, **extra: object) -> TypedRefusal:
    context: dict[str, object] = {"field": field, "reason": reason}
    context.update(extra)
    return TypedRefusal(
        category=RefusalCategory.INVALID_INPUT,
        retryability=Retryability.NO,
        context=context,
    )


def _policy(field: str, reason: str, **extra: object) -> TypedRefusal:
    context: dict[str, object] = {"field": field, "reason": reason}
    context.update(extra)
    return TypedRefusal(
        category=RefusalCategory.POLICY_REJECTION,
        retryability=Retryability.NO,
        context=context,
    )


def refuse_mailbox_send_as_invoke(*, field: str, **extra: object) -> TypedRefusal:
    """send_message left the mailbox send contract (DEC-0484)."""
    return _policy(
        field,
        "send_message is mailbox delivery, not invoke; InvocationEnvelope keys "
        "are not the chat contract (DEC-0484; FR-UI-36)",
        mailbox_send=True,
        invoke=MAILBOX_SEND_IS_INVOKE,
        requires_instance_id=MAILBOX_SEND_REQUIRES_INSTANCE_ID,
        requires_grant_record=MAILBOX_SEND_REQUIRES_GRANT_RECORD,
        uses_idempotency_key=MAILBOX_SEND_USES_INVOKE_IDEMPOTENCY_KEY,
        uses_command_id=MAILBOX_SEND_USES_COMMAND_ID_IDENTITY,
        **extra,
    )


def refuse_mailbox_chat_contract(value: object) -> Result[None]:
    """Refuse InvocationEnvelope keys, command_id identity, and transcript aliases."""
    if not isinstance(value, Mapping):
        return _invalid("payload", "send_message payload must be an object")
    entry = cast("Mapping[str, object]", value)
    bodies: list[Mapping[str, object]] = [entry]
    nested = entry.get("envelope")
    if isinstance(nested, Mapping):
        bodies.append(cast("Mapping[str, object]", nested))
    for body in bodies:
        for field in FORBIDDEN_MAILBOX_CHAT_CONTRACT_KEYS:
            if field in body:
                return refuse_mailbox_send_as_invoke(field=field, given=repr(body.get(field)))
        for field in _FORBIDDEN_SEND_IDENTITY_KEYS:
            if field in body:
                return _policy(
                    field,
                    "send identity is the wire pair (producer_id, id), not "
                    "product-session command_id (DEC-0484; FR-UI-36)",
                    uses_command_id=MAILBOX_SEND_USES_COMMAND_ID_IDENTITY,
                    given=repr(body.get(field)),
                )
        for field in _FORBIDDEN_TRANSCRIPT_KEYS:
            if field in body:
                return _policy(
                    field,
                    "transcript is the mailbox Envelope / list_mailbox snapshot, "
                    "not private_notes, sess:, MemoryProvider, or a new store "
                    "(DEC-0484; NFR-UI-07)",
                    private_notes=TRANSCRIPT_IS_PRIVATE_NOTES,
                    sess=TRANSCRIPT_IS_SESS,
                    memory_provider=TRANSCRIPT_IS_MEMORY_PROVIDER,
                    new_store=TRANSCRIPT_IS_NEW_STORE,
                )
    return Ok(None)


def list_mailbox_snapshots_are_truth() -> bool:
    """list_mailbox query snapshots are truth; message.delta is progress only."""
    return (
        snapshots_are_authoritative()
        and not progress_is_authoritative()
        and WireEvent.MESSAGE_DELTA.value == "message.delta"
        and WireQuery.LIST_MAILBOX.value == "list_mailbox"
        and MESSAGE_DELTA_IS_PROGRESS_ONLY
    )


def claim_live_ct40_serving_send_message_existed_at_inspect_sha(
    existed: object,
) -> Result[bool]:
    """Claiming live CT-40 serving of send_message at inspect fails."""
    if existed is True or existed == "true":
        return _policy(
            SEND_MESSAGE_COMMAND,
            "live CT-40 serving of send_message was absent at inspect SHA "
            f"{LIVE_CT40_SERVING_SEND_MESSAGE_INSPECT_SHA} (DEC-0507 ABSENT); "
            "WireCommand.SEND_MESSAGE seed name existed; socket dispatch is absent",
            existed_at_inspect_sha=False,
            inspect_sha=LIVE_CT40_SERVING_SEND_MESSAGE_INSPECT_SHA,
            seed_name_existed=SEND_MESSAGE_SEED_NAME_EXISTED_AT_INSPECT_SHA,
        )
    if existed is not False:
        return _invalid(
            "existed_at_inspect_sha",
            "inspect-SHA existence claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def claim_send_message_seed_name_absent_at_inspect_sha(absent: object) -> Result[bool]:
    """Claiming the seed name send_message was absent at inspect fails."""
    if absent is True or absent == "true":
        return _policy(
            SEND_MESSAGE_COMMAND,
            "WireCommand.SEND_MESSAGE existed at inspect SHA "
            f"{LIVE_CT40_SERVING_SEND_MESSAGE_INSPECT_SHA}; live socket dispatch "
            "was absent (DEC-0507 CONNECT)",
            existed_at_inspect_sha=True,
            inspect_sha=LIVE_CT40_SERVING_SEND_MESSAGE_INSPECT_SHA,
            seed_name=SEND_MESSAGE_COMMAND,
        )
    if absent is not False:
        return _invalid(
            "absent_at_inspect_sha",
            "inspect-SHA absence claim is a boolean",
            given=repr(absent),
        )
    return Ok(False)


def claim_this_story_scaffolded_qmx_ui(scaffolded: object) -> Result[bool]:
    """dispatchChat chrome is Epic 66; this story is the daemon/wire contract."""
    if scaffolded is True or scaffolded == "true":
        return _policy(
            "apps/qmx-ui",
            "unique chrome issuer dispatchChat is Epic 66; this story is the "
            "daemon/wire contract those issuers call — do not scaffold apps/qmx-ui",
            scaffolded=QMX_UI_SCAFFOLDED_THIS_STORY,
            dispatch_chat_is_this_story=DISPATCH_CHAT_IS_THIS_STORY,
        )
    if scaffolded is not False:
        return _invalid(
            "qmx_ui_scaffolded",
            "apps/qmx-ui scaffold claim is a boolean",
            given=repr(scaffolded),
        )
    return Ok(False)


def parse_send_message_payload(value: object) -> Result[Mapping[str, object]]:
    """Accept seed send_message args. ``product_session_ref`` is optional.

    The field is copied onto the mailbox Envelope by COMP-QMA-DAEMON at write.
    Body text is not a session source. InvocationEnvelope keys are refused.
    """
    if not isinstance(value, Mapping):
        return _invalid("payload", "send_message payload must be an object")
    entry = cast("Mapping[str, object]", value)
    contract = refuse_mailbox_chat_contract(entry)
    if not isinstance(contract, Ok):
        return contract
    for field in FORBIDDEN_ENVELOPE_SESSION_FIELDS:
        if field in entry:
            return _invalid(
                field,
                "send_message names product_session_ref (AM-14); do not name "
                "product_session_id or originating_psess; "
                "originating_product_session_ref is Epic 73 (DEC-0495)",
                given=repr(entry.get(field)),
            )
    outbound = dict(entry)
    kind = outbound.get("kind")
    if (
        ENVELOPE_PRODUCT_SESSION_FIELD in outbound
        and isinstance(kind, str)
        and kind in HOME_COMPOSER_FORBIDDEN_KINDS
    ):
        return _policy(
            "kind",
            "product-chat send uses mailbox kinds handoff|reply|notify|status|"
            "question; approval_request is not a Home composer mint "
            "(CT-48; Story 46.4; FR-UI-33)",
            given=kind,
            allowed=sorted(PRODUCT_CHAT_MESSAGE_KINDS),
        )
    if ENVELOPE_PRODUCT_SESSION_FIELD not in outbound:
        return Ok(MappingProxyType(outbound))
    token = outbound.get(ENVELOPE_PRODUCT_SESSION_FIELD)
    if token is None:
        return _invalid(
            ENVELOPE_PRODUCT_SESSION_FIELD,
            "optional product_session_ref is an omitted key, never null (DEC-0495)",
        )
    if not isinstance(token, str) or token.strip() == "":
        return _invalid(
            ENVELOPE_PRODUCT_SESSION_FIELD,
            "product_session_ref is a non-empty psess: pointer when present",
            given=repr(token),
        )
    stripped = token.strip()
    if not stripped.startswith(PRODUCT_SESSION_REF_PREFIX) or len(stripped) <= len(
        PRODUCT_SESSION_REF_PREFIX
    ):
        return _invalid(
            ENVELOPE_PRODUCT_SESSION_FIELD,
            "product_session_ref is a psess: pointer at the product-session "
            "projection (AM-14; DEC-0495)",
            given=stripped,
        )
    outbound[ENVELOPE_PRODUCT_SESSION_FIELD] = stripped
    return Ok(MappingProxyType(outbound))
