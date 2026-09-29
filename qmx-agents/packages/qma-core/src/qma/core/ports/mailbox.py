"""Mailbox Envelope, MessageKind, DeliveryState, and WakePolicy (CT-48; AD-20).

Definitions only. The daemon owns each Quant's durable Mailbox as a projection
over journal ``message.*`` events and evaluates the Quant ``WakePolicy`` at
delivery time. A message may request work but can never be the work — a
handoff becomes real only when it writes a Task.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Final, cast

from qma.core.ontology import ActorId
from qma.core.ontology.wake_policy import (
    MAX_WAKES_PER_WINDOW_REGISTRY_KEY,
    QUANT_WRITE_COMMAND,
    QUIET_HOURS_REGISTRY_KEY,
    WAKE_CONDITION_ANY,
    WAKE_POLICY_EDITABILITY,
    WAKE_POLICY_HOME,
    WAKE_POLICY_SCOPE,
    QuietHours,
    WakePolicy,
    authorize_quant_write,
    is_wake_condition,
    parse_quiet_hours,
    parse_wake_policy,
    refuse_model_wake_policy_write,
    source_may_write_wake_policy,
    wake_conditions_match,
)
from qma.core.vocabulary.enums import DeliveryState, MessageKind
from qma.core.vocabulary.registry import VocabularyError, parse_closed
from qmf.core import Ok, Result
from qmf.core.refusal import RefusalCategory, Retryability, TypedRefusal

__all__ = [
    "DELIVERY_STATE_VALUES",
    "ENVELOPE_ADDITIVE_FIELDS",
    "ENVELOPE_FP1_EXCLUDED_FIELDS",
    "ENVELOPE_OPTIONAL_REFS",
    "ENVELOPE_PRODUCT_SESSION_FIELD",
    "ENVELOPE_REF_LAW_EXCEPTIONS",
    "ENVELOPE_REQUIRED_FIELDS",
    "ENVELOPE_TYPES_EXISTED_AT_INSPECT_SHA",
    "FORBIDDEN_ENVELOPE_SESSION_FIELDS",
    "GAP_0071_LEAD_MAILBOX_CATCH_ALL",
    "GAP_0079_EXTERNAL_TRANSPORT",
    "HUMAN_APPROVAL_CHANNEL",
    "INHERITING_MESSAGE_KINDS",
    "MAILBOX_INSPECT_SHA",
    "MAX_WAKES_PER_WINDOW_REGISTRY_KEY",
    "MESSAGE_KIND_VALUES",
    "PRODUCT_CHAT_MESSAGE_KINDS",
    "PRODUCT_SESSION_OWN_IDENTITY_FIELD",
    "PRODUCT_SESSION_REF_EXISTED_AT_INSPECT_SHA",
    "PRODUCT_SESSION_REF_PREFIX",
    "QUANT_WRITE_COMMAND",
    "QUIET_HOURS_REGISTRY_KEY",
    "WAKE_CONDITION_ANY",
    "WAKE_POLICY_EDITABILITY",
    "WAKE_POLICY_HOME",
    "WAKE_POLICY_SCOPE",
    "Envelope",
    "QuietHours",
    "WakePolicy",
    "authorize_quant_write",
    "claim_envelope_types_absent_at_inspect_sha",
    "claim_product_session_ref_existed_at_inspect_sha",
    "envelope_identity_content",
    "is_human_approval_channel",
    "is_wake_condition",
    "parse_delivery_state",
    "parse_envelope",
    "parse_message_kind",
    "parse_quiet_hours",
    "parse_wake_policy",
    "product_session_ref_matches",
    "refuse_external_agent_transport",
    "refuse_lead_mailbox_catch_all",
    "refuse_model_wake_policy_write",
    "source_may_write_wake_policy",
    "wake_conditions_match",
]


ENVELOPE_REQUIRED_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "msg_id",
        "from",
        "to",
        "kind",
        "correlation_id",
        "body",
        "priority",
        "created_at",
    }
)

ENVELOPE_OPTIONAL_REFS: Final[frozenset[str]] = frozenset(
    {
        "mission_ref",
        "task_ref",
        "reply_to_ref",
        "causation_id",
    }
)

# AM-02 / AM-14 additive pointer. Story 46.4 required/optional lists stay held.
ENVELOPE_PRODUCT_SESSION_FIELD: Final[str] = "product_session_ref"
PRODUCT_SESSION_OWN_IDENTITY_FIELD: Final[str] = "product_session_id"
PRODUCT_SESSION_REF_PREFIX: Final[str] = "psess:"
ENVELOPE_ADDITIVE_FIELDS: Final[frozenset[str]] = frozenset({ENVELOPE_PRODUCT_SESSION_FIELD})
FORBIDDEN_ENVELOPE_SESSION_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "product_session_id",
        "originating_psess",
        "originating_product_session_ref",
    }
)

# Explicit versioned declaration: tracing ids and the session pointer are never
# Envelope identity (DEC-0319; DEC-0495). Changing only product_session_ref does
# not mint a different fp1.
ENVELOPE_FP1_EXCLUDED_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "correlation_id",
        "causation_id",
        ENVELOPE_PRODUCT_SESSION_FIELD,
    }
)

MAILBOX_INSPECT_SHA: Final[str] = "34c148be"
PRODUCT_SESSION_REF_EXISTED_AT_INSPECT_SHA: Final[bool] = False
ENVELOPE_TYPES_EXISTED_AT_INSPECT_SHA: Final[bool] = True

MESSAGE_KIND_VALUES: Final[frozenset[str]] = frozenset(member.value for member in MessageKind)
DELIVERY_STATE_VALUES: Final[frozenset[str]] = frozenset(member.value for member in DeliveryState)

# Product-chat send uses mailbox kinds; approval_request is the gate-raised
# human-approval channel, not a Home composer mint (Story 69.4; CT-48).
PRODUCT_CHAT_MESSAGE_KINDS: Final[frozenset[str]] = frozenset(
    {
        MessageKind.HANDOFF.value,
        MessageKind.REPLY.value,
        MessageKind.NOTIFY.value,
        MessageKind.STATUS.value,
        MessageKind.QUESTION.value,
    }
)
INHERITING_MESSAGE_KINDS: Final[frozenset[str]] = frozenset(
    {MessageKind.REPLY.value, MessageKind.QUESTION.value}
)

HUMAN_APPROVAL_CHANNEL: Final[MessageKind] = MessageKind.APPROVAL_REQUEST

GAP_0071_LEAD_MAILBOX_CATCH_ALL: Final[str] = "GAP-0071"
GAP_0079_EXTERNAL_TRANSPORT: Final[str] = "GAP-0079"

# from, to, and causation_id are unsuffixed whitelist exceptions (DEC-0304).
# Do not add product_session_id or originating_psess (AM-14; DEC-0495).
ENVELOPE_REF_LAW_EXCEPTIONS: Final[frozenset[str]] = frozenset({"from", "to", "causation_id"})
_REF_LAW_EXCEPTIONS: Final[frozenset[str]] = ENVELOPE_REF_LAW_EXCEPTIONS
_QMA_SESSION_PREFIX: Final[str] = "sess:"


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


def refuse_external_agent_transport(**extra: object) -> TypedRefusal:
    """External agent-to-agent transport is Deferred GAP-0079 (DEC-0319)."""
    return _policy(
        "relay",
        "external agent-to-agent transport is Deferred GAP-0079; the internal "
        "single-operator bus comes first and no relay or signing protocol is "
        "adopted (DEC-0319; CT-48; FR-Q60)",
        gap=GAP_0079_EXTERNAL_TRANSPORT,
        deferred=True,
        **extra,
    )


def refuse_lead_mailbox_catch_all(**extra: object) -> TypedRefusal:
    """Lead-mailbox catch-all is Deferred GAP-0071 (DEC-0349)."""
    return _policy(
        "to",
        "an undeliverable Envelope resolves to dead_letter rather than the lead "
        "Quant mailbox; the lead-mailbox catch-all is Deferred GAP-0071 "
        "(DEC-0349; CT-48; FR-Q60)",
        gap=GAP_0071_LEAD_MAILBOX_CATCH_ALL,
        deferred=True,
        **extra,
    )


def claim_product_session_ref_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming Envelope product_session_ref already existed at inspect fails."""
    if existed is True or existed == "true":
        return _policy(
            ENVELOPE_PRODUCT_SESSION_FIELD,
            "product_session_ref was absent on Envelope at inspect SHA "
            f"{MAILBOX_INSPECT_SHA} (DEC-0507 AMEND-absent; AM-02)",
            existed_at_inspect_sha=False,
            inspect_sha=MAILBOX_INSPECT_SHA,
        )
    if existed is not False:
        return _invalid(
            "existed_at_inspect_sha",
            "inspect-SHA existence claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def claim_envelope_types_absent_at_inspect_sha(absent: object) -> Result[bool]:
    """Claiming Envelope / mailbox types were absent at inspect fails."""
    if absent is True or absent == "true":
        return _policy(
            "envelope",
            "Envelope / mailbox types existed as fixtures at inspect SHA "
            f"{MAILBOX_INSPECT_SHA} (DEC-0507 CONNECT; DEC-0286)",
            existed_at_inspect_sha=True,
            inspect_sha=MAILBOX_INSPECT_SHA,
        )
    if absent is not False:
        return _invalid(
            "absent_at_inspect_sha",
            "inspect-SHA absence claim is a boolean",
            given=repr(absent),
        )
    return Ok(False)


def product_session_ref_matches(envelope: Envelope, product_session_ref: str) -> bool:
    """Fold-by-field equality on the Envelope pointer. Never parse body text."""
    return envelope.product_session_ref == product_session_ref


def is_human_approval_channel(kind: MessageKind | str) -> bool:
    """True only for ``approval_request`` — the single human-approval channel."""
    if isinstance(kind, MessageKind):
        return kind is HUMAN_APPROVAL_CHANNEL
    return kind == HUMAN_APPROVAL_CHANNEL.value


def parse_message_kind(value: object) -> Result[MessageKind]:
    """Parse the closed MessageKind vocabulary (CT-48; DEC-0319)."""
    try:
        return Ok(parse_closed(MessageKind, value))
    except VocabularyError:
        return _invalid(
            "kind",
            "MessageKind is exactly handoff, reply, notify, review_request, "
            "status, question, or approval_request (CT-48; DEC-0319; FR-Q60)",
            given=repr(value),
            allowed=sorted(MESSAGE_KIND_VALUES),
        )


def parse_delivery_state(value: object) -> Result[DeliveryState]:
    """Parse the closed DeliveryState vocabulary (CT-48; DEC-0319)."""
    try:
        return Ok(parse_closed(DeliveryState, value))
    except VocabularyError:
        return _invalid(
            "delivery_state",
            "DeliveryState is exactly delivered, queued, woke, deferred, or "
            "dead_letter (CT-48; DEC-0319; FR-Q60)",
            given=repr(value),
            allowed=sorted(DELIVERY_STATE_VALUES),
        )


def _freeze_body(value: object) -> Result[str | Mapping[str, object]]:
    if isinstance(value, str):
        return Ok(value)
    if isinstance(value, Mapping):
        return Ok(MappingProxyType(dict(cast("Mapping[str, object]", value))))
    return _invalid("body", "body is a string or object (CT-48; DEC-0319)")


def _parse_actor(value: object, field: str) -> Result[ActorId]:
    if isinstance(value, ActorId):
        return Ok(value)
    parsed = ActorId.try_create(value)
    if isinstance(parsed, Ok):
        return parsed
    return _invalid(
        field,
        f"{field} is a Quant ActorId; an Agent has no Mailbox and is never a "
        "to address (CT-48; DEC-0306, DEC-0319)",
        given=repr(value),
    )


def _parse_optional_ref(entry: Mapping[str, object], field: str) -> Result[str | None]:
    if field not in entry:
        return Ok(None)
    value = entry.get(field)
    if value is None:
        return _invalid(
            field,
            f"{field} is omitted as an absent key, never null (CT-48; DEC-0319)",
        )
    if not isinstance(value, str) or value.strip() == "":
        return _invalid(
            field,
            f"{field} is a non-empty reference string when present (CT-48; DEC-0319)",
            given=repr(value),
        )
    return Ok(value.strip())


def _parse_product_session_ref(entry: Mapping[str, object]) -> Result[str | None]:
    parsed = _parse_optional_ref(entry, ENVELOPE_PRODUCT_SESSION_FIELD)
    if not isinstance(parsed, Ok):
        return parsed
    token = parsed.value
    if token is None:
        return Ok(None)
    if token.casefold().startswith(_QMA_SESSION_PREFIX) and not token.startswith(
        PRODUCT_SESSION_REF_PREFIX
    ):
        return _invalid(
            ENVELOPE_PRODUCT_SESSION_FIELD,
            "product_session_ref is a product-session psess: pointer, never a "
            "QMA sess: id (AM-14; DEC-0495)",
            given=token,
        )
    if not token.startswith(PRODUCT_SESSION_REF_PREFIX) or len(token) <= len(
        PRODUCT_SESSION_REF_PREFIX
    ):
        return _invalid(
            ENVELOPE_PRODUCT_SESSION_FIELD,
            "product_session_ref is a non-empty psess: pointer at the "
            "product-session projection (AM-14; DEC-0495)",
            given=token,
        )
    return Ok(token)


def _parse_artifact_refs(value: object) -> Result[tuple[str, ...]]:
    if value is None:
        return _invalid(
            "artifact_refs",
            "artifact_refs may be an empty declared set, never null (CT-48; DEC-0319)",
        )
    if isinstance(value, str):
        if value.strip() == "":
            return _invalid(
                "artifact_refs",
                "artifact refs are non-empty reference strings (CT-48; DEC-0319)",
            )
        return Ok((value.strip(),))
    if isinstance(value, (list, tuple)):
        parsed: list[str] = []
        for item in cast("list[object] | tuple[object, ...]", value):
            if not isinstance(item, str) or item.strip() == "":
                return _invalid(
                    "artifact_refs",
                    "artifact refs are non-empty reference strings, never the "
                    "artifacts themselves (CT-48; DEC-0319)",
                )
            parsed.append(item.strip())
        return Ok(tuple(parsed))
    return _invalid(
        "artifact_refs",
        "artifact_refs is a reference string or list of refs (CT-48; DEC-0319)",
    )


@dataclass(frozen=True, slots=True)
class Envelope:
    """One mailbox Envelope record (CT-48; AD-20; DEC-0319).

    Python fields use ``from_actor`` / ``to_actor`` because ``from`` is reserved;
    the payload keys are the unsuffixed ``from`` and ``to`` whitelist exceptions.
    """

    msg_id: str
    from_actor: ActorId
    to_actor: ActorId
    kind: MessageKind
    correlation_id: str
    body: str | Mapping[str, object]
    priority: int
    created_at: int
    mission_ref: str | None = None
    task_ref: str | None = None
    reply_to_ref: str | None = None
    causation_id: str | None = None
    product_session_ref: str | None = None
    artifact_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.body, Mapping) and not isinstance(self.body, MappingProxyType):
            object.__setattr__(self, "body", MappingProxyType(dict(self.body)))
        object.__setattr__(self, "artifact_refs", tuple(self.artifact_refs))

    def with_task_ref(self, task_ref: str) -> Envelope:
        """Return a copy carrying the Task this handoff wrote."""
        return replace(self, task_ref=task_ref)

    def to_payload(self) -> Mapping[str, object]:
        body: object = dict(self.body) if isinstance(self.body, Mapping) else self.body
        payload: dict[str, object] = {
            "msg_id": self.msg_id,
            "from": self.from_actor.value,
            "to": self.to_actor.value,
            "kind": self.kind.value,
            "correlation_id": self.correlation_id,
            "body": body,
            "priority": self.priority,
            "created_at": self.created_at,
            "artifact_refs": list(self.artifact_refs),
        }
        if self.mission_ref is not None:
            payload["mission_ref"] = self.mission_ref
        if self.task_ref is not None:
            payload["task_ref"] = self.task_ref
        if self.reply_to_ref is not None:
            payload["reply_to_ref"] = self.reply_to_ref
        if self.causation_id is not None:
            payload["causation_id"] = self.causation_id
        if self.product_session_ref is not None:
            payload[ENVELOPE_PRODUCT_SESSION_FIELD] = self.product_session_ref
        return MappingProxyType(payload)


def envelope_identity_content(value: Envelope | Mapping[str, object]) -> Mapping[str, object]:
    """fp1 identity payload: tracing ids and ``product_session_ref`` excluded."""
    raw = dict(value.to_payload() if isinstance(value, Envelope) else value)
    for field in ENVELOPE_FP1_EXCLUDED_FIELDS:
        raw.pop(field, None)
    return MappingProxyType(raw)


def parse_envelope(value: object) -> Result[Envelope]:
    """Validate a mailbox Envelope against CT-48."""
    if isinstance(value, Envelope):
        return Ok(value)
    if not isinstance(value, Mapping):
        return _invalid("envelope", "a mailbox Envelope is an object")
    entry = cast("Mapping[str, object]", value)

    aliases = dict(entry)
    if "from" not in aliases and "from_actor" in aliases:
        aliases["from"] = aliases["from_actor"]
    if "to" not in aliases and "to_actor" in aliases:
        aliases["to"] = aliases["to_actor"]
    if "msg_id" not in aliases and "id" in aliases:
        aliases["msg_id"] = aliases["id"]

    missing = [field for field in sorted(ENVELOPE_REQUIRED_FIELDS) if field not in aliases]
    if missing:
        return _invalid(
            "envelope",
            "every mailbox Envelope carries msg_id, from, to, kind, "
            "correlation_id, body, priority, and created_at (CT-48; DEC-0319; FR-Q60)",
            missing=missing,
        )

    msg_id = aliases.get("msg_id")
    if not isinstance(msg_id, str) or msg_id.strip() == "":
        return _invalid("msg_id", "msg_id is the durable message id (CT-48; DEC-0319)")

    from_actor = _parse_actor(aliases.get("from"), "from")
    if not isinstance(from_actor, Ok):
        return from_actor
    to_actor = _parse_actor(aliases.get("to"), "to")
    if not isinstance(to_actor, Ok):
        return to_actor

    kind = parse_message_kind(aliases.get("kind"))
    if not isinstance(kind, Ok):
        return kind

    correlation_id = aliases.get("correlation_id")
    if not isinstance(correlation_id, str) or correlation_id.strip() == "":
        return _invalid(
            "correlation_id",
            "correlation_id is mandatory on every Envelope; a record without one "
            "is refused at the gate (CT-48; DEC-0304, DEC-0319)",
        )

    body = _freeze_body(aliases.get("body"))
    if not isinstance(body, Ok):
        return body

    priority = aliases.get("priority")
    if not isinstance(priority, int) or isinstance(priority, bool):
        return _invalid("priority", "priority is an integer (CT-48; DEC-0319)")

    created_at = aliases.get("created_at")
    if not isinstance(created_at, int) or isinstance(created_at, bool) or created_at < 0:
        return _invalid(
            "created_at",
            "created_at is the creation time as int64 UTC nanoseconds (CT-48; AD-6)",
        )

    refs: dict[str, str | None] = {}
    for field in ENVELOPE_OPTIONAL_REFS:
        parsed_ref = _parse_optional_ref(aliases, field)
        if not isinstance(parsed_ref, Ok):
            return parsed_ref
        refs[field] = parsed_ref.value

    for field in FORBIDDEN_ENVELOPE_SESSION_FIELDS:
        if field in aliases:
            return _invalid(
                field,
                "Envelope pointer is product_session_ref (AM-14); ProductSession "
                "own identity remains product_session_id on that row; "
                "originating_product_session_ref is Epic 73 (DEC-0495)",
                given=repr(aliases.get(field)),
            )

    session_ref = _parse_product_session_ref(aliases)
    if not isinstance(session_ref, Ok):
        return session_ref

    if "artifact_refs" not in aliases:
        artifact_refs: tuple[str, ...] = ()
    else:
        parsed_refs = _parse_artifact_refs(aliases.get("artifact_refs"))
        if not isinstance(parsed_refs, Ok):
            return parsed_refs
        artifact_refs = parsed_refs.value

    # Optional refs never appear as a null key; unsuffixed from/to/causation_id.
    for field in _REF_LAW_EXCEPTIONS:
        if f"{field}_ref" in aliases:
            return _invalid(
                field,
                f"{field} is a whitelist exception against the _ref law and is "
                "never suffixed (DEC-0304, DEC-0319)",
            )

    return Ok(
        Envelope(
            msg_id=msg_id.strip(),
            from_actor=from_actor.value,
            to_actor=to_actor.value,
            kind=kind.value,
            correlation_id=correlation_id.strip(),
            body=body.value,
            priority=priority,
            created_at=created_at,
            mission_ref=refs["mission_ref"],
            task_ref=refs["task_ref"],
            reply_to_ref=refs["reply_to_ref"],
            causation_id=refs["causation_id"],
            product_session_ref=session_ref.value,
            artifact_refs=artifact_refs,
        )
    )
