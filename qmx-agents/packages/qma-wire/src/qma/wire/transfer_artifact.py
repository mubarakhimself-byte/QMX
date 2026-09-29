"""Addable CT-40 command ``transfer_artifact`` (Story 70.2; AM-09).

COMP-QMA-WIRE owns the command name. COMP-QMA-DAEMON owns the ticket handler.
Seed 9/7/10 stay the seed. No new CT. Operator principal with durable
``command_id`` (product-session namespace when a ``psess:`` is present).
Not a pack op, not ``dispatchInvoke``, not JSON-RPC ``stage_artifact``,
and not host-control. ``initialize`` advertises capability
``transfer_artifact``. Missing capability is a typed mismatch.
Absent as product surface at inspect SHA ``34c148be`` (DEC-0507).
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final, cast

from qma.core.ports.mailbox import (
    ENVELOPE_PRODUCT_SESSION_FIELD,
    PRODUCT_SESSION_REF_PREFIX,
)
from qma.wire.stage_artifact import (
    ARTIFACT_STORE_TYPES_EXISTED_AT_INSPECT_SHA,
    claim_artifact_store_types_absent_at_inspect_sha,
)
from qma.wire.vocabulary import SEED_COMMAND_COUNT, WIRE_COMMANDS, WireCommand
from qmf.core.refusal import (
    Ok,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
)

__all__ = [
    "ARTIFACT_STORE_TYPES_EXISTED_AT_INSPECT_SHA",
    "FORBIDDEN_TRANSFER_CONTRACT_KEYS",
    "JSONRPC_STAGE_ARTIFACT_MINTED",
    "LIVE_CT40_SERVING_TRANSFER_ARTIFACT_EXISTED_AT_INSPECT_SHA",
    "QMX_UI_SCAFFOLDED_THIS_STORY",
    "TRANSFER_ARTIFACT_AMENDMENT",
    "TRANSFER_ARTIFACT_CAPABILITY",
    "TRANSFER_ARTIFACT_CAPABILITY_MINTED",
    "TRANSFER_ARTIFACT_COMMAND",
    "TRANSFER_ARTIFACT_CONTRACT",
    "TRANSFER_ARTIFACT_DTO_OWNER",
    "TRANSFER_ARTIFACT_EXISTED_AT_INSPECT_SHA",
    "TRANSFER_ARTIFACT_HANDLER_OWNER",
    "TRANSFER_ARTIFACT_INSPECT_SHA",
    "TRANSFER_ARTIFACT_IS_DISPATCH_INVOKE",
    "TRANSFER_ARTIFACT_IS_HOST_CONTROL",
    "TRANSFER_ARTIFACT_IS_PACK_OP",
    "TRANSFER_ARTIFACT_IS_WIRE_COMMAND",
    "TRANSFER_ARTIFACT_NEW_CT_MINTED",
    "TRANSFER_ARTIFACT_REFUSED_CT",
    "TRANSFER_COMPLETE_MINTED",
    "claim_artifact_store_types_absent_at_inspect_sha",
    "claim_live_ct40_serving_transfer_artifact_existed_at_inspect_sha",
    "claim_this_story_scaffolded_qmx_ui",
    "claim_transfer_artifact_existed_at_inspect_sha",
    "durable_transfer_command_id",
    "parse_transfer_artifact_payload",
    "require_transfer_artifact_capability",
    "transfer_artifact_capability_unavailable",
]


TRANSFER_ARTIFACT_DTO_OWNER: Final[str] = "COMP-QMA-WIRE"
TRANSFER_ARTIFACT_HANDLER_OWNER: Final[str] = "COMP-QMA-DAEMON"
TRANSFER_ARTIFACT_CONTRACT: Final[str] = "CT-40"
TRANSFER_ARTIFACT_NEW_CT_MINTED: Final[bool] = False
TRANSFER_ARTIFACT_REFUSED_CT: Final[str] = "CT-52"
TRANSFER_ARTIFACT_INSPECT_SHA: Final[str] = "34c148be"
TRANSFER_ARTIFACT_EXISTED_AT_INSPECT_SHA: Final[bool] = False
LIVE_CT40_SERVING_TRANSFER_ARTIFACT_EXISTED_AT_INSPECT_SHA: Final[bool] = False
TRANSFER_ARTIFACT_COMMAND: Final[str] = WireCommand.TRANSFER_ARTIFACT.value
TRANSFER_ARTIFACT_CAPABILITY: Final[str] = TRANSFER_ARTIFACT_COMMAND
TRANSFER_ARTIFACT_CAPABILITY_MINTED: Final[bool] = True
TRANSFER_ARTIFACT_IS_WIRE_COMMAND: Final[bool] = True
TRANSFER_ARTIFACT_IS_PACK_OP: Final[bool] = False
TRANSFER_ARTIFACT_IS_DISPATCH_INVOKE: Final[bool] = False
TRANSFER_ARTIFACT_IS_HOST_CONTROL: Final[bool] = False
JSONRPC_STAGE_ARTIFACT_MINTED: Final[bool] = False
TRANSFER_COMPLETE_MINTED: Final[bool] = True
QMX_UI_SCAFFOLDED_THIS_STORY: Final[bool] = False
TRANSFER_ARTIFACT_AMENDMENT: Final[str] = "AM-09"
FORBIDDEN_TRANSFER_CONTRACT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "logical_invocation_id",
        "grant_id",
        "op_id",
        "idempotency_key",
        "dispatchInvoke",
        "pack_op",
        "host_control",
        "stage_artifact",
        "transfer_complete",
    }
)
_SEED_COMMAND_COUNT: Final[int] = SEED_COMMAND_COUNT


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


def transfer_artifact_capability_unavailable() -> TypedRefusal:
    """Typed mismatch when initialize omitted capability ``transfer_artifact``."""
    return _policy(
        "capabilities",
        "typed mismatch: missing transfer_artifact",
        missing=TRANSFER_ARTIFACT_CAPABILITY,
        name=TRANSFER_ARTIFACT_CAPABILITY,
        jsonrpc_stage_artifact=JSONRPC_STAGE_ARTIFACT_MINTED,
        pack_op=TRANSFER_ARTIFACT_IS_PACK_OP,
        dispatch_invoke=TRANSFER_ARTIFACT_IS_DISPATCH_INVOKE,
        host_control=TRANSFER_ARTIFACT_IS_HOST_CONTROL,
        named_amendment=TRANSFER_ARTIFACT_AMENDMENT,
        seed_command_count=_SEED_COMMAND_COUNT,
        in_wire_commands=TRANSFER_ARTIFACT_COMMAND in WIRE_COMMANDS,
    )


def require_transfer_artifact_capability(capabilities: object) -> Result[None]:
    """Missing ``transfer_artifact`` is a typed mismatch, never a silent skip."""
    if capabilities is None:
        return transfer_artifact_capability_unavailable()
    if not isinstance(capabilities, Mapping):
        return _invalid("capabilities", "capabilities must be an object")
    caps = cast("Mapping[str, object]", capabilities)
    if caps.get(TRANSFER_ARTIFACT_CAPABILITY) is True:
        return Ok(None)
    return transfer_artifact_capability_unavailable()


def claim_transfer_artifact_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming transfer_artifact / the ticket projection existed fails."""
    if existed is True or existed == "true":
        return _policy(
            TRANSFER_ARTIFACT_COMMAND,
            "transfer_artifact and artifact_transfer_ticket were absent as "
            f"product surface at inspect SHA {TRANSFER_ARTIFACT_INSPECT_SHA} "
            "(DEC-0507 ABSENT; AM-09)",
            existed_at_inspect_sha=False,
            inspect_sha=TRANSFER_ARTIFACT_INSPECT_SHA,
            named_amendment=TRANSFER_ARTIFACT_AMENDMENT,
            ticket_existed_at_inspect_sha=False,
        )
    if existed is not False:
        return _invalid(
            "existed_at_inspect_sha",
            "inspect-SHA existence claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def claim_live_ct40_serving_transfer_artifact_existed_at_inspect_sha(
    existed: object,
) -> Result[bool]:
    """Claiming live CT-40 serving of transfer_artifact at inspect fails."""
    if existed is True or existed == "true":
        return _policy(
            TRANSFER_ARTIFACT_COMMAND,
            "live CT-40 serving of transfer_artifact was absent at inspect SHA "
            f"{TRANSFER_ARTIFACT_INSPECT_SHA} (DEC-0507 ABSENT)",
            existed_at_inspect_sha=False,
            inspect_sha=TRANSFER_ARTIFACT_INSPECT_SHA,
            live_socket_dispatch=False,
        )
    if existed is not False:
        return _invalid(
            "existed_at_inspect_sha",
            "inspect-SHA existence claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def claim_this_story_scaffolded_qmx_ui(scaffolded: object) -> Result[bool]:
    """Library chrome onTransfer is Epic 66; this story is the daemon/wire name."""
    if scaffolded is True or scaffolded == "true":
        return _policy(
            "apps/qmx-ui",
            "onTransfer chrome is Epic 66; this story is the daemon/wire "
            "addable name those callbacks call — do not scaffold apps/qmx-ui",
            scaffolded=QMX_UI_SCAFFOLDED_THIS_STORY,
        )
    if scaffolded is not False:
        return _invalid(
            "qmx_ui_scaffolded",
            "apps/qmx-ui scaffold claim is a boolean",
            given=repr(scaffolded),
        )
    return Ok(False)


def durable_transfer_command_id(
    command_id: str,
    product_session_ref: str | None,
) -> str:
    """Namespace durable command_id by psess: when a product session is present."""
    if product_session_ref is None:
        return command_id
    return f"{product_session_ref}/{command_id}"


def _parse_reachable_hosts(value: object) -> Result[tuple[str, ...]]:
    if isinstance(value, str) and value.strip() != "":
        return Ok((value.strip(),))
    if isinstance(value, (list, tuple)):
        hosts: list[str] = []
        for item in cast("list[object] | tuple[object, ...]", value):
            if not isinstance(item, str) or item.strip() == "":
                return _invalid(
                    "reachable_hosts",
                    "reachable_hosts items are non-empty strings",
                    given=repr(item),
                )
            hosts.append(item.strip())
        return Ok(tuple(hosts))
    return _invalid(
        "reachable_hosts",
        "reachable_hosts is a list of hostnames when present",
        given=repr(value),
    )


def _parse_required_token(field: str, value: object) -> Result[str]:
    if not isinstance(value, str) or value.strip() == "":
        return _invalid(field, f"{field} is a required non-empty string", given=repr(value))
    return Ok(value.strip())


def _parse_optional_token(field: str, value: object) -> Result[str]:
    if not isinstance(value, str) or value.strip() == "":
        return _invalid(
            field,
            f"{field} is a non-empty string when present",
            given=repr(value),
        )
    return Ok(value.strip())


def _parse_optional_psess(value: object) -> Result[str]:
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
            "projection when present",
            given=stripped,
        )
    return Ok(stripped)


def _merge_destination(entry: Mapping[str, object]) -> Result[dict[str, object]]:
    nested_obj = entry.get("destination")
    nested: Mapping[str, object]
    if nested_obj is None:
        nested = {}
    elif isinstance(nested_obj, Mapping):
        nested = cast("Mapping[str, object]", nested_obj)
    else:
        return _invalid("destination", "destination placement is an object when present")
    merged: dict[str, object] = {}
    for field in (
        "instance_id",
        "environment_id",
        "placement_revision",
        "credential_ref",
        "same_daemon",
        "reachable_hosts",
    ):
        if field in nested:
            merged[field] = nested[field]
        if field in entry:
            merged[field] = entry[field]
    return Ok(merged)


def parse_transfer_artifact_payload(value: object) -> Result[Mapping[str, object]]:
    """Accept local-complete fp1 plus destination placement / instance.

    Durable ``command_id`` is required. Nested ``destination`` may supply
    placement fields. Forbidden pack/invoke/host-control keys are refused.
    """
    if not isinstance(value, Mapping):
        return _invalid("payload", "transfer_artifact payload must be an object")
    entry = cast("Mapping[str, object]", value)
    for field in FORBIDDEN_TRANSFER_CONTRACT_KEYS:
        if field in entry:
            return _policy(
                field,
                "transfer_artifact is addable CT-40, not a pack op, "
                "dispatchInvoke, JSON-RPC stage_artifact, or host-control",
                pack_op=TRANSFER_ARTIFACT_IS_PACK_OP,
                dispatch_invoke=TRANSFER_ARTIFACT_IS_DISPATCH_INVOKE,
                host_control=TRANSFER_ARTIFACT_IS_HOST_CONTROL,
                jsonrpc_stage_artifact=JSONRPC_STAGE_ARTIFACT_MINTED,
                transfer_complete_minted=TRANSFER_COMPLETE_MINTED,
                named_amendment=TRANSFER_ARTIFACT_AMENDMENT,
                given=repr(entry.get(field)),
            )
    fp1 = _parse_required_token("fp1", entry.get("fp1"))
    if not isinstance(fp1, Ok):
        return fp1
    command_id = _parse_required_token("command_id", entry.get("command_id"))
    if not isinstance(command_id, Ok):
        return command_id
    dest = _merge_destination(entry)
    if not isinstance(dest, Ok):
        return dest
    dest_fields = dest.value
    instance_id = _parse_required_token("instance_id", dest_fields.get("instance_id"))
    if not isinstance(instance_id, Ok):
        return instance_id
    outbound: dict[str, object] = {
        "fp1": fp1.value,
        "command_id": command_id.value,
        "instance_id": instance_id.value,
    }
    for field in ("environment_id", "placement_revision", "credential_ref"):
        if field in dest_fields:
            parsed = _parse_optional_token(field, dest_fields.get(field))
            if not isinstance(parsed, Ok):
                return parsed
            outbound[field] = parsed.value
    if "same_daemon" in dest_fields:
        flag = dest_fields.get("same_daemon")
        if not isinstance(flag, bool):
            return _invalid(
                "same_daemon",
                "same_daemon is a boolean when present",
                given=repr(flag),
            )
        outbound["same_daemon"] = flag
    if "reachable_hosts" in dest_fields:
        hosts = _parse_reachable_hosts(dest_fields.get("reachable_hosts"))
        if not isinstance(hosts, Ok):
            return hosts
        outbound["reachable_hosts"] = hosts.value
    if ENVELOPE_PRODUCT_SESSION_FIELD in entry:
        parsed = _parse_optional_psess(entry.get(ENVELOPE_PRODUCT_SESSION_FIELD))
        if not isinstance(parsed, Ok):
            return parsed
        outbound[ENVELOPE_PRODUCT_SESSION_FIELD] = parsed.value
        outbound["durable_command_id"] = durable_transfer_command_id(
            command_id.value,
            parsed.value,
        )
    else:
        outbound["durable_command_id"] = durable_transfer_command_id(command_id.value, None)
    return Ok(MappingProxyType(outbound))
