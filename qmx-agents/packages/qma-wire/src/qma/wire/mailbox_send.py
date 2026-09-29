"""AM-12 mailbox send identity: pair ``(producer_id, id)`` for journal lifetime.

Pre-ack identity is the wire pair. Snapshot/query names the second member
``wire_id``. Payload hash is fp1 of the **wire payload bytes**. Same pair plus
same hash returns the prior result. Same pair plus different hash refuses for
journal lifetime (mailbox ``send_message`` only). Other commands keep Story
41.3 / ``registry:wire.dedup_window``. Daemon and wire never auto-resend.
Live socket dispatch of ``send_message`` / ``list_mailbox`` was absent at
inspect SHA ``34c148be`` (DEC-0507).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal, cast

from qma.core.ports.mailbox import ENVELOPE_PRODUCT_SESSION_FIELD, MAILBOX_INSPECT_SHA
from qma.wire.idempotency import DEDUP_WINDOW_REGISTRY_KEY
from qma.wire.list_mailbox import LIST_MAILBOX_QUERY_NAME
from qma.wire.vocabulary import WireCommand
from qmf.core.fingerprint import fingerprint
from qmf.core.refusal import (
    Ok,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
)

__all__ = [
    "LEFTOVER_COMPOSER_IS_COMMAND",
    "LIVE_SOCKET_DISPATCH_EXISTED_AT_INSPECT_SHA",
    "LIVE_SOCKET_DISPATCH_INSPECT_SHA",
    "LIVE_SOCKET_DISPATCH_NAMES",
    "MAILBOX_AUTO_RESEND",
    "MAILBOX_SEND_AMENDMENT",
    "MAILBOX_SEND_COLLISION_COMMAND",
    "MAILBOX_SEND_NON_PAYLOAD_KEYS",
    "MAILBOX_SEND_OTHER_COMMANDS_WINDOW",
    "MAILBOX_SEND_RETENTION_FLOOR",
    "PAIR_LOOKUP_EMPTY_IS_NEW_SEND",
    "MailboxRestorePlan",
    "MailboxSendPair",
    "claim_live_socket_dispatch_existed_at_inspect_sha",
    "hash_wire_payload_bytes",
    "mailbox_restore_plan",
    "mailbox_send_wire_payload",
    "pair_lookup_disposition",
    "parse_mailbox_send_pair",
    "refuse_mailbox_auto_resend",
    "refuse_mailbox_send_collision",
    "refuse_substitute_live_producer_id",
]


MAILBOX_SEND_AMENDMENT: Final[str] = "AM-12"
MAILBOX_SEND_COLLISION_COMMAND: Final[str] = WireCommand.SEND_MESSAGE.value
MAILBOX_SEND_RETENTION_FLOOR: Final[str] = "journal_lifetime"
MAILBOX_SEND_OTHER_COMMANDS_WINDOW: Final[str] = DEDUP_WINDOW_REGISTRY_KEY
MAILBOX_AUTO_RESEND: Final[bool] = False
LEFTOVER_COMPOSER_IS_COMMAND: Final[bool] = False
PAIR_LOOKUP_EMPTY_IS_NEW_SEND: Final[bool] = False
LIVE_SOCKET_DISPATCH_INSPECT_SHA: Final[str] = MAILBOX_INSPECT_SHA
LIVE_SOCKET_DISPATCH_EXISTED_AT_INSPECT_SHA: Final[bool] = False
LIVE_SOCKET_DISPATCH_NAMES: Final[frozenset[str]] = frozenset(
    {MAILBOX_SEND_COLLISION_COMMAND, LIST_MAILBOX_QUERY_NAME}
)
MAILBOX_SEND_NON_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "envelope",
        "principal_class",
        "producer_id",
        "wire_id",
        "id",
        "grant_id",
        "grant_record",
        "payload_hash",
    }
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


@dataclass(frozen=True, slots=True)
class MailboxSendPair:
    """Wire pair ``(producer_id, id)``. Query/snapshot name the second ``wire_id``."""

    producer_id: str
    wire_id: str

    @property
    def id(self) -> str:
        return self.wire_id

    def as_tuple(self) -> tuple[str, str]:
        return (self.producer_id, self.wire_id)


@dataclass(frozen=True, slots=True)
class MailboxRestorePlan:
    """Cold-start or reload restore is a list_mailbox query, never a resend."""

    args: Mapping[str, object]
    query: str = LIST_MAILBOX_QUERY_NAME
    auto_resend: bool = MAILBOX_AUTO_RESEND
    command: str | None = None
    leftover_composer_is_draft: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "args", MappingProxyType(dict(self.args)))


def mailbox_send_wire_payload(payload: Mapping[str, object]) -> Mapping[str, object]:
    """Command payload bytes hashed for AM-12 — not the envelope frame pair."""
    nested = payload.get("envelope")
    if isinstance(nested, Mapping):
        outbound = dict(cast("Mapping[str, object]", nested))
        if ENVELOPE_PRODUCT_SESSION_FIELD in payload:
            outbound[ENVELOPE_PRODUCT_SESSION_FIELD] = payload[ENVELOPE_PRODUCT_SESSION_FIELD]
    else:
        outbound = {
            key: value for key, value in payload.items() if key not in MAILBOX_SEND_NON_PAYLOAD_KEYS
        }
    for key in MAILBOX_SEND_NON_PAYLOAD_KEYS:
        outbound.pop(key, None)
    return MappingProxyType(outbound)


def hash_wire_payload_bytes(payload: object) -> Result[str]:
    """fp1 of canonical JSON of the wire payload bytes (not Envelope fp1)."""
    if not isinstance(payload, Mapping):
        return _invalid("payload", "wire payload hashed for AM-12 is an object")
    body = mailbox_send_wire_payload(cast("Mapping[str, object]", payload))
    minted = fingerprint(dict(body))
    if not isinstance(minted, Ok):
        return minted
    return Ok(minted.value.value)


def parse_mailbox_send_pair(payload: object) -> Result[MailboxSendPair | None]:
    """Extract ``(producer_id, id)``. Snapshot names the second member ``wire_id``."""
    if not isinstance(payload, Mapping):
        return _invalid("payload", "send_message payload must be an object")
    entry = cast("Mapping[str, object]", payload)
    producer = entry.get("producer_id")
    wire = entry.get("wire_id")
    if not isinstance(wire, str) or wire.strip() == "":
        alt = entry.get("id")
        if isinstance(alt, str) and alt.strip() != "":
            wire = alt
    producer_token = producer.strip() if isinstance(producer, str) else ""
    wire_token = wire.strip() if isinstance(wire, str) else ""
    if producer_token != "" and wire_token != "":
        return Ok(MailboxSendPair(producer_id=producer_token, wire_id=wire_token))
    if producer_token != "" or wire_token != "":
        return _invalid(
            "wire_id" if producer_token != "" else "producer_id",
            "pre-ack identity is the wire pair (producer_id, id); "
            "snapshot/query name the second member wire_id",
        )
    return Ok(None)


def refuse_mailbox_send_collision(
    *,
    producer_id: str,
    wire_id: str,
    stored_hash: str,
    given_hash: str,
    **extra: object,
) -> TypedRefusal:
    """Same pair, different payload hash — not a successful prior ack (AM-12)."""
    return _policy(
        "id",
        "payload_hash_collision",
        producer_id=producer_id,
        wire_id=wire_id,
        stored_hash=stored_hash,
        given_hash=given_hash,
        retention=MAILBOX_SEND_RETENTION_FLOOR,
        amendment=MAILBOX_SEND_AMENDMENT,
        command=MAILBOX_SEND_COLLISION_COMMAND,
        other_commands_keep=MAILBOX_SEND_OTHER_COMMANDS_WINDOW,
        successful_prior_ack=False,
        mailbox_sends_only=True,
        **extra,
    )


def refuse_mailbox_auto_resend(**extra: object) -> TypedRefusal:
    """Daemon and wire never auto-resend. Composer leftover is a local draft."""
    return _policy(
        "send_message",
        "daemon and wire never auto-resend; leftover composer text is a local "
        "draft, not a command (DEC-0501; SCN-0031)",
        auto_resend=MAILBOX_AUTO_RESEND,
        leftover_composer_is_command=LEFTOVER_COMPOSER_IS_COMMAND,
        restore_query=LIST_MAILBOX_QUERY_NAME,
        **extra,
    )


def refuse_substitute_live_producer_id(
    *,
    stored_producer_id: object,
    given_producer_id: object,
    **extra: object,
) -> TypedRefusal:
    """A later live producer_id must not be substituted into pair lookup."""
    return _policy(
        "producer_id",
        "substituting a later live producer_id into the lookup is forbidden",
        stored_producer_id=repr(stored_producer_id)
        if not isinstance(stored_producer_id, str)
        else stored_producer_id,
        given_producer_id=repr(given_producer_id)
        if not isinstance(given_producer_id, str)
        else given_producer_id,
        empty_unknown=True,
        new_send=PAIR_LOOKUP_EMPTY_IS_NEW_SEND,
        **extra,
    )


def mailbox_restore_plan(
    *,
    product_session_ref: str,
    pending_triple: Mapping[str, object] | None = None,
    cold_start: bool = False,
    leftover_composer: object = None,
    resend: bool = False,
) -> Result[MailboxRestorePlan]:
    """Cold start queries ``{product_session_ref}`` only. Reload may query the pair.

    Never auto-resends. Leftover composer text is ignored as a local draft.
    """
    if resend or (leftover_composer is not None and LEFTOVER_COMPOSER_IS_COMMAND):
        return refuse_mailbox_auto_resend(
            cold_start=cold_start,
            product_session_ref=product_session_ref,
            leftover_composer=leftover_composer is not None,
        )
    if cold_start or pending_triple is None:
        return Ok(
            MailboxRestorePlan(
                args={ENVELOPE_PRODUCT_SESSION_FIELD: product_session_ref},
            )
        )
    producer = pending_triple.get("producer_id")
    wire = pending_triple.get("wire_id")
    if not isinstance(producer, str) or producer.strip() == "":
        return _invalid(
            "producer_id",
            "pending triple names producer_id for pair lookup; do not mint id=C2",
        )
    if not isinstance(wire, str) or wire.strip() == "":
        return _invalid(
            "wire_id",
            "pending triple names wire_id (wire id) for pair lookup; do not mint id=C2",
        )
    return Ok(
        MailboxRestorePlan(
            args={
                ENVELOPE_PRODUCT_SESSION_FIELD: product_session_ref,
                "producer_id": producer.strip(),
                "wire_id": wire.strip(),
            },
        )
    )


def claim_live_socket_dispatch_existed_at_inspect_sha(
    name: object,
    existed: object,
) -> Result[bool]:
    """Claiming live socket dispatch of send_message or list_mailbox fails."""
    if not isinstance(name, str) or name not in LIVE_SOCKET_DISPATCH_NAMES:
        return _invalid(
            "name",
            "live socket dispatch claim names send_message or list_mailbox",
            given=repr(name),
            names=sorted(LIVE_SOCKET_DISPATCH_NAMES),
        )
    if existed is True or existed == "true":
        return _policy(
            name,
            "live socket dispatch of send_message and list_mailbox was absent "
            f"at inspect SHA {LIVE_SOCKET_DISPATCH_INSPECT_SHA} (DEC-0507 ABSENT)",
            existed_at_inspect_sha=False,
            inspect_sha=LIVE_SOCKET_DISPATCH_INSPECT_SHA,
            name=name,
        )
    if existed is not False:
        return _invalid(
            "existed_at_inspect_sha",
            "inspect-SHA existence claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def pair_lookup_disposition(row_count: object) -> Literal["empty_unknown", "hit"]:
    """Zero rows is empty/unknown, not a new send."""
    if isinstance(row_count, int) and row_count > 0:
        return "hit"
    return "empty_unknown"
