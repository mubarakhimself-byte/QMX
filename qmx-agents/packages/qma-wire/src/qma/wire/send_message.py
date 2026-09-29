"""Seed ``send_message`` payload may name additive ``product_session_ref``.

Story 69.1 / AM-02 / AM-14 / DEC-0495. COMP-QMA-WIRE owns the seed command
name. The daemon copies the named field onto the CT-48 Envelope at write.
Optional value is an omitted key, never null. Machine payloads may omit it.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final, cast

from qma.core.ports.mailbox import (
    ENVELOPE_PRODUCT_SESSION_FIELD,
    FORBIDDEN_ENVELOPE_SESSION_FIELDS,
    PRODUCT_SESSION_REF_PREFIX,
)
from qma.wire.vocabulary import WireCommand
from qmf.core.refusal import (
    Ok,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
)

__all__ = [
    "SEND_MESSAGE_COMMAND",
    "parse_send_message_payload",
]


SEND_MESSAGE_COMMAND: Final[str] = WireCommand.SEND_MESSAGE.value


def _invalid(field: str, reason: str, **extra: object) -> TypedRefusal:
    context: dict[str, object] = {"field": field, "reason": reason}
    context.update(extra)
    return TypedRefusal(
        category=RefusalCategory.INVALID_INPUT,
        retryability=Retryability.NO,
        context=context,
    )


def parse_send_message_payload(value: object) -> Result[Mapping[str, object]]:
    """Accept seed send_message args. ``product_session_ref`` is optional.

    The field is copied onto the mailbox Envelope by COMP-QMA-DAEMON at write.
    Body text is not a session source.
    """
    if not isinstance(value, Mapping):
        return _invalid("payload", "send_message payload must be an object")
    entry = cast("Mapping[str, object]", value)
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
