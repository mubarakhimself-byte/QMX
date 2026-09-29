"""Addable CT-40 query ``list_mailbox`` (Story 69.2; AM-08; DEC-0500).

COMP-QMA-WIRE owns the query name. COMP-QMA-DAEMON owns the handler / mailbox
fold. Seed 9/7/10 stay the seed. No new CT number. ``initialize`` advertises
capability ``list_mailbox``. Absent at inspect SHA ``34c148be`` (DEC-0507).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, cast

from qma.core.ports.mailbox import (
    ENVELOPE_PRODUCT_SESSION_FIELD,
    FORBIDDEN_ENVELOPE_SESSION_FIELDS,
    MAILBOX_INSPECT_SHA,
    PRODUCT_SESSION_REF_PREFIX,
    claim_envelope_types_absent_at_inspect_sha,
)
from qma.wire.vocabulary import WireQuery
from qmf.core.refusal import (
    Ok,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
)

__all__ = [
    "LIST_MAILBOX_CAPABILITY",
    "LIST_MAILBOX_CONTRACT",
    "LIST_MAILBOX_DTO_OWNER",
    "LIST_MAILBOX_EXISTED_AT_INSPECT_SHA",
    "LIST_MAILBOX_HANDLER_OWNER",
    "LIST_MAILBOX_HTTP_PATH",
    "LIST_MAILBOX_INSPECT_SHA",
    "LIST_MAILBOX_NEW_CT_MINTED",
    "LIST_MAILBOX_QUERY_NAME",
    "LIST_MAILBOX_REFUSED_CT",
    "MailboxSnapshot",
    "MailboxSnapshotRow",
    "claim_envelope_types_absent_at_inspect_sha",
    "claim_list_mailbox_existed_at_inspect_sha",
    "parse_list_mailbox_args",
    "parse_mailbox_snapshot",
    "query_unavailable",
    "require_list_mailbox_capability",
]


LIST_MAILBOX_DTO_OWNER: Final[str] = "COMP-QMA-WIRE"
LIST_MAILBOX_HANDLER_OWNER: Final[str] = "COMP-QMA-DAEMON"
LIST_MAILBOX_CONTRACT: Final[str] = "CT-40"
LIST_MAILBOX_NEW_CT_MINTED: Final[bool] = False
LIST_MAILBOX_REFUSED_CT: Final[str] = "CT-52"
LIST_MAILBOX_INSPECT_SHA: Final[str] = MAILBOX_INSPECT_SHA
LIST_MAILBOX_EXISTED_AT_INSPECT_SHA: Final[bool] = False
LIST_MAILBOX_QUERY_NAME: Final[str] = WireQuery.LIST_MAILBOX.value
LIST_MAILBOX_CAPABILITY: Final[str] = LIST_MAILBOX_QUERY_NAME
LIST_MAILBOX_HTTP_PATH: Final[str] = f"/q/{LIST_MAILBOX_QUERY_NAME}"


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


def query_unavailable(name: object = LIST_MAILBOX_QUERY_NAME) -> TypedRefusal:
    """Typed mismatch when initialize omitted the query capability (J-UI-13)."""
    token = LIST_MAILBOX_QUERY_NAME if not isinstance(name, str) or name == "" else name
    return _policy(
        "query",
        "query_unavailable",
        name=token,
        query=token,
        empty_mailbox=False,
    )


def require_list_mailbox_capability(capabilities: object) -> Result[None]:
    """Missing ``list_mailbox`` is query_unavailable, never an empty mailbox."""
    if capabilities is None:
        return query_unavailable(LIST_MAILBOX_QUERY_NAME)
    if not isinstance(capabilities, Mapping):
        return _invalid("capabilities", "capabilities must be an object")
    caps = cast("Mapping[str, object]", capabilities)
    if caps.get(LIST_MAILBOX_CAPABILITY) is True:
        return Ok(None)
    return query_unavailable(LIST_MAILBOX_QUERY_NAME)


def claim_list_mailbox_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming list_mailbox already existed at inspect SHA fails."""
    if existed is True or existed == "true":
        return _policy(
            LIST_MAILBOX_QUERY_NAME,
            "list_mailbox was absent at inspect SHA "
            f"{LIST_MAILBOX_INSPECT_SHA} (DEC-0507 ABSENT; AM-08)",
            existed_at_inspect_sha=False,
            inspect_sha=LIST_MAILBOX_INSPECT_SHA,
        )
    if existed is not False:
        return _invalid(
            "existed_at_inspect_sha",
            "inspect-SHA existence claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def _parse_optional_psess(value: object) -> Result[str | None]:
    if value is None:
        return _invalid(
            ENVELOPE_PRODUCT_SESSION_FIELD,
            "optional product_session_ref is an omitted key, never null (DEC-0495)",
        )
    if not isinstance(value, str) or value.strip() == "":
        return _invalid(
            ENVELOPE_PRODUCT_SESSION_FIELD,
            "product_session_ref is a non-empty psess: pointer when present",
            given=repr(value),
        )
    stripped = value.strip()
    if not stripped.startswith(PRODUCT_SESSION_REF_PREFIX) or len(stripped) <= len(
        PRODUCT_SESSION_REF_PREFIX
    ):
        return _invalid(
            ENVELOPE_PRODUCT_SESSION_FIELD,
            "product_session_ref is a psess: pointer at the product-session "
            "projection (AM-14; DEC-0495)",
            given=stripped,
        )
    return Ok(stripped)


def _parse_pair_token(field: str, value: object) -> Result[str]:
    if not isinstance(value, str) or value.strip() == "":
        return _invalid(
            field,
            "pre-ack pair members are non-empty strings",
            given=repr(value),
        )
    return Ok(value.strip())


def parse_list_mailbox_args(value: object) -> Result[Mapping[str, object]]:
    """Accept ``{product_session_ref}`` or ``{product_session_ref, producer_id, wire_id}``.

    Client ``msg_id`` is not a lookup key. GrantRecord is not required.
    """
    if value is None:
        return Ok(MappingProxyType({}))
    if not isinstance(value, Mapping):
        return _invalid("args", "list_mailbox args must be an object")
    entry = cast("Mapping[str, object]", value)
    for field in FORBIDDEN_ENVELOPE_SESSION_FIELDS:
        if field in entry:
            return _invalid(
                field,
                "list_mailbox names product_session_ref (AM-14); do not name "
                "product_session_id or originating_psess; "
                "originating_product_session_ref is Epic 73 (DEC-0495)",
                given=repr(entry.get(field)),
            )
    outbound: dict[str, object] = {}
    if ENVELOPE_PRODUCT_SESSION_FIELD in entry:
        parsed = _parse_optional_psess(entry.get(ENVELOPE_PRODUCT_SESSION_FIELD))
        if not isinstance(parsed, Ok):
            return parsed
        outbound[ENVELOPE_PRODUCT_SESSION_FIELD] = parsed.value
    has_producer = "producer_id" in entry
    has_wire = "wire_id" in entry
    if has_producer != has_wire:
        missing = "wire_id" if has_producer else "producer_id"
        return _invalid(
            missing,
            "pre-ack lookup names both producer_id and wire_id; do not look up by msg_id",
        )
    if has_producer and has_wire:
        producer = _parse_pair_token("producer_id", entry.get("producer_id"))
        if not isinstance(producer, Ok):
            return producer
        wire = _parse_pair_token("wire_id", entry.get("wire_id"))
        if not isinstance(wire, Ok):
            return wire
        outbound["producer_id"] = producer.value
        outbound["wire_id"] = wire.value
    return Ok(MappingProxyType(outbound))


@dataclass(frozen=True, slots=True)
class MailboxSnapshotRow:
    """One snapshot row: envelope, delivery state, wire pair, server msg_id."""

    envelope: Mapping[str, object]
    delivery_state: str
    msg_id: str | None = None
    producer_id: str | None = None
    wire_id: str | None = None

    def to_payload(self) -> Mapping[str, object]:
        payload: dict[str, object] = {
            "envelope": dict(self.envelope),
            "delivery_state": self.delivery_state,
        }
        if self.msg_id is not None:
            payload["msg_id"] = self.msg_id
        if self.producer_id is not None:
            payload["producer_id"] = self.producer_id
        if self.wire_id is not None:
            payload["wire_id"] = self.wire_id
        return MappingProxyType(payload)


@dataclass(frozen=True, slots=True)
class MailboxSnapshot:
    """Authoritative mailbox snapshot. Product-chat is keyed by psess:."""

    product_chat: bool
    rows: tuple[MailboxSnapshotRow, ...]
    product_session_ref: str | None = None
    query: str = LIST_MAILBOX_QUERY_NAME

    def to_payload(self) -> Mapping[str, object]:
        payload: dict[str, object] = {
            "query": self.query,
            "product_chat": self.product_chat,
            "rows": [dict(row.to_payload()) for row in self.rows],
        }
        if self.product_session_ref is not None:
            payload[ENVELOPE_PRODUCT_SESSION_FIELD] = self.product_session_ref
        return MappingProxyType(payload)


def _parse_snapshot_row(value: object) -> Result[MailboxSnapshotRow]:
    if not isinstance(value, Mapping):
        return _invalid("rows", "mailbox snapshot rows are objects")
    entry = cast("Mapping[str, object]", value)
    envelope = entry.get("envelope")
    if not isinstance(envelope, Mapping):
        return _invalid("envelope", "snapshot row envelope is an object")
    state = entry.get("delivery_state")
    if not isinstance(state, str) or state.strip() == "":
        return _invalid("delivery_state", "snapshot row delivery_state is a non-empty string")
    msg_id = entry.get("msg_id")
    if msg_id is not None and (not isinstance(msg_id, str) or msg_id.strip() == ""):
        return _invalid("msg_id", "server msg_id is a non-empty string when present")
    producer = entry.get("producer_id")
    if producer is not None and (not isinstance(producer, str) or producer.strip() == ""):
        return _invalid("producer_id", "wire producer_id is a non-empty string when present")
    wire = entry.get("wire_id")
    if wire is not None and (not isinstance(wire, str) or wire.strip() == ""):
        return _invalid("wire_id", "wire_id is a non-empty string when present")
    return Ok(
        MailboxSnapshotRow(
            envelope=MappingProxyType(dict(cast("Mapping[str, object]", envelope))),
            delivery_state=state,
            msg_id=None if msg_id is None else msg_id.strip(),
            producer_id=None if producer is None else producer.strip(),
            wire_id=None if wire is None else wire.strip(),
        )
    )


def parse_mailbox_snapshot(value: object) -> Result[MailboxSnapshot]:
    """Parse a list_mailbox snapshot payload."""
    if isinstance(value, MailboxSnapshot):
        return Ok(value)
    if not isinstance(value, Mapping):
        return _invalid("snapshot", "list_mailbox snapshot is an object")
    entry = cast("Mapping[str, object]", value)
    product_chat = entry.get("product_chat")
    if not isinstance(product_chat, bool):
        return _invalid("product_chat", "product_chat is a boolean")
    rows_obj = entry.get("rows")
    if not isinstance(rows_obj, Sequence) or isinstance(rows_obj, (str, bytes)):
        return _invalid("rows", "snapshot rows are an array")
    parsed_rows: list[MailboxSnapshotRow] = []
    for item in cast("Sequence[object]", rows_obj):
        row = _parse_snapshot_row(item)
        if not isinstance(row, Ok):
            return row
        parsed_rows.append(row.value)
    session_ref: str | None = None
    if ENVELOPE_PRODUCT_SESSION_FIELD in entry:
        parsed = _parse_optional_psess(entry.get(ENVELOPE_PRODUCT_SESSION_FIELD))
        if not isinstance(parsed, Ok):
            return parsed
        session_ref = parsed.value
    query = entry.get("query", LIST_MAILBOX_QUERY_NAME)
    if query != LIST_MAILBOX_QUERY_NAME:
        return _invalid("query", "snapshot query name is list_mailbox", given=repr(query))
    return Ok(
        MailboxSnapshot(
            product_chat=product_chat,
            rows=tuple(parsed_rows),
            product_session_ref=session_ref,
        )
    )
