"""Addable CT-40 ``cancel_job`` command for the originating product session.

The payload fences the durable CT-46 JobHandle. ``expected_state`` is an
observation only, so it is deliberately omitted from the canonical command
identity used across a queued-to-running race.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from types import MappingProxyType
from typing import Final, cast

from qma.core.vocabulary import JobHandleState
from qma.core.vocabulary.registry import VocabularyError, parse_closed
from qma.wire.vocabulary import WIRE_COMMANDS, WireCommand
from qmf.core.refusal import (
    Ok,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
)

__all__ = [
    "CANCEL_JOB_AMENDMENT",
    "CANCEL_JOB_CAPABILITY",
    "CANCEL_JOB_CAPABILITY_MINTED",
    "CANCEL_JOB_COMMAND",
    "CANCEL_JOB_DTO_OWNER",
    "CANCEL_JOB_HANDLER_OWNER",
    "CANCEL_JOB_IS_DISPATCH_INVOKE",
    "CANCEL_JOB_IS_HOST_CONTROL",
    "CANCEL_JOB_IS_PACK_OP",
    "CANCEL_JOB_IS_WIRE_COMMAND",
    "CANCEL_JOB_NEW_CT_MINTED",
    "CANCEL_JOB_REFUSED_CT",
    "cancel_job_capability_unavailable",
    "cancel_job_command_hash",
    "durable_cancel_command_id",
    "parse_cancel_job_payload",
    "require_cancel_job_capability",
]

CANCEL_JOB_DTO_OWNER: Final[str] = "COMP-QMA-WIRE"
CANCEL_JOB_HANDLER_OWNER: Final[str] = "COMP-QMA-DAEMON"
CANCEL_JOB_COMMAND: Final[str] = WireCommand.CANCEL_JOB.value
CANCEL_JOB_CAPABILITY: Final[str] = CANCEL_JOB_COMMAND
CANCEL_JOB_CAPABILITY_MINTED: Final[bool] = True
CANCEL_JOB_IS_WIRE_COMMAND: Final[bool] = True
CANCEL_JOB_IS_PACK_OP: Final[bool] = False
CANCEL_JOB_IS_DISPATCH_INVOKE: Final[bool] = False
CANCEL_JOB_IS_HOST_CONTROL: Final[bool] = False
CANCEL_JOB_NEW_CT_MINTED: Final[bool] = False
CANCEL_JOB_REFUSED_CT: Final[str] = "CT-42"
CANCEL_JOB_AMENDMENT: Final[str] = "AM-09"


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


def cancel_job_capability_unavailable() -> TypedRefusal:
    return _policy(
        "capabilities",
        "typed mismatch: missing cancel_job",
        missing=CANCEL_JOB_CAPABILITY,
        name=CANCEL_JOB_CAPABILITY,
        in_wire_commands=CANCEL_JOB_COMMAND in WIRE_COMMANDS,
        dispatch_invoke=CANCEL_JOB_IS_DISPATCH_INVOKE,
        host_control=CANCEL_JOB_IS_HOST_CONTROL,
        new_ct_minted=CANCEL_JOB_NEW_CT_MINTED,
        named_amendment=CANCEL_JOB_AMENDMENT,
    )


def require_cancel_job_capability(capabilities: object) -> Result[None]:
    """Missing capability is a typed mismatch, never an empty cancel."""
    if not isinstance(capabilities, Mapping):
        return cancel_job_capability_unavailable()
    if cast("Mapping[str, object]", capabilities).get(CANCEL_JOB_CAPABILITY) is True:
        return Ok(None)
    return cancel_job_capability_unavailable()


def durable_cancel_command_id(command_id: str, originating_product_session_ref: str) -> str:
    """Namespace command ids by their immutable originating ``psess:``."""
    return f"{originating_product_session_ref}/{command_id}"


def parse_cancel_job_payload(value: object) -> Result[Mapping[str, object]]:
    """Parse exact JobHandle fences and the observational state value."""
    if not isinstance(value, Mapping):
        return _invalid("payload", "cancel_job payload must be an object")
    entry = cast("Mapping[str, object]", value)
    allowed = frozenset(
        {"handle_id", "job_id", "logical_run_id", "attempt_id", "command_id", "expected_state"}
    )
    unknown = tuple(str(key) for key in entry if key not in allowed)
    if unknown:
        return _invalid(
            "payload",
            "cancel_job payload does not accept unrecognized fields",
            unexpected=sorted(unknown),
        )
    handle_id = entry.get("handle_id")
    if not isinstance(handle_id, str) or not handle_id.strip():
        return _invalid("handle_id", "handle_id is the durable JobHandle job_id")
    logical_run_id = entry.get("logical_run_id")
    if not isinstance(logical_run_id, str) or not logical_run_id.strip():
        return _invalid("logical_run_id", "logical_run_id is required")
    attempt_id = entry.get("attempt_id")
    if isinstance(attempt_id, bool) or not isinstance(attempt_id, int) or attempt_id < 1:
        return _invalid("attempt_id", "attempt_id is a positive integer")
    command_id = entry.get("command_id")
    if not isinstance(command_id, str) or not command_id.strip():
        return _invalid("command_id", "command_id is a stable non-empty product-session id")
    raw_state = entry.get("expected_state")
    try:
        expected_state = parse_closed(JobHandleState, raw_state)
    except VocabularyError as exc:
        return _invalid("expected_state", str(exc), given=repr(raw_state))
    if "job_id" in entry and entry["job_id"] != handle_id:
        return _policy(
            "job_id",
            "handle_id is job_id; the two identifiers must match exactly",
            handle_id=handle_id,
            job_id=entry["job_id"],
        )
    parsed: dict[str, object] = {
        "handle_id": handle_id.strip(),
        "logical_run_id": logical_run_id.strip(),
        "attempt_id": attempt_id,
        "command_id": command_id.strip(),
        "expected_state": expected_state.value,
    }
    if "job_id" in entry:
        parsed["job_id"] = handle_id.strip()
    return Ok(MappingProxyType(parsed))


def cancel_job_command_hash(
    payload: Mapping[str, object],
    *,
    originating_product_session_ref: str,
) -> str:
    """Hash cancel identity without expected_state or wire-envelope identity."""
    identity = {
        "attempt_id": payload["attempt_id"],
        "command_id": payload["command_id"],
        "durable_command_id": durable_cancel_command_id(
            str(payload["command_id"]), originating_product_session_ref
        ),
        "handle_id": payload["handle_id"],
        "logical_run_id": payload["logical_run_id"],
    }
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
