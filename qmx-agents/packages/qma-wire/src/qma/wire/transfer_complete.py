"""Addable CT-40 command ``transfer_complete`` (Story 70.3; AM-09).

Dest authors the ack as a machine principal after hash plus byte-count verify
and durable dest placement. COMP-QMA-WIRE owns the name. COMP-QMA-DAEMON owns
the source ack handler. Seed 9/7/10 stay the seed. No new CT. Not a pack op,
not ``dispatchInvoke``, not JSON-RPC ``stage_artifact``, not pairing HTTP, and
not a BFF. ``initialize`` advertises capability ``transfer_complete``. Absent
as product surface at inspect SHA ``34c148be`` (DEC-0507).
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final, cast

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
    "FORBIDDEN_TRANSFER_COMPLETE_CONTRACT_KEYS",
    "JSONRPC_STAGE_ARTIFACT_MINTED",
    "LIVE_CT40_SERVING_TRANSFER_COMPLETE_EXISTED_AT_INSPECT_SHA",
    "MACHINE_ARTIFACT_GET_EXISTED_AT_INSPECT_SHA",
    "QMX_UI_SCAFFOLDED_THIS_STORY",
    "TRANSFER_COMPLETE_AMENDMENT",
    "TRANSFER_COMPLETE_CAPABILITY",
    "TRANSFER_COMPLETE_CAPABILITY_MINTED",
    "TRANSFER_COMPLETE_COMMAND",
    "TRANSFER_COMPLETE_CONTRACT",
    "TRANSFER_COMPLETE_DTO_OWNER",
    "TRANSFER_COMPLETE_EXISTED_AT_INSPECT_SHA",
    "TRANSFER_COMPLETE_HANDLER_OWNER",
    "TRANSFER_COMPLETE_INSPECT_SHA",
    "TRANSFER_COMPLETE_IS_DISPATCH_INVOKE",
    "TRANSFER_COMPLETE_IS_HOST_CONTROL",
    "TRANSFER_COMPLETE_IS_PACK_OP",
    "TRANSFER_COMPLETE_IS_WIRE_COMMAND",
    "TRANSFER_COMPLETE_MINTED",
    "TRANSFER_COMPLETE_NEW_CT_MINTED",
    "TRANSFER_COMPLETE_REFUSED_CT",
    "claim_artifact_store_types_absent_at_inspect_sha",
    "claim_live_ct40_serving_transfer_complete_existed_at_inspect_sha",
    "claim_machine_artifact_get_existed_at_inspect_sha",
    "claim_this_story_scaffolded_qmx_ui",
    "claim_transfer_complete_existed_at_inspect_sha",
    "parse_transfer_complete_payload",
    "require_transfer_complete_capability",
    "transfer_complete_capability_unavailable",
]


TRANSFER_COMPLETE_DTO_OWNER: Final[str] = "COMP-QMA-WIRE"
TRANSFER_COMPLETE_HANDLER_OWNER: Final[str] = "COMP-QMA-DAEMON"
TRANSFER_COMPLETE_CONTRACT: Final[str] = "CT-40"
TRANSFER_COMPLETE_NEW_CT_MINTED: Final[bool] = False
TRANSFER_COMPLETE_REFUSED_CT: Final[str] = "CT-52"
TRANSFER_COMPLETE_INSPECT_SHA: Final[str] = "34c148be"
TRANSFER_COMPLETE_EXISTED_AT_INSPECT_SHA: Final[bool] = False
LIVE_CT40_SERVING_TRANSFER_COMPLETE_EXISTED_AT_INSPECT_SHA: Final[bool] = False
MACHINE_ARTIFACT_GET_EXISTED_AT_INSPECT_SHA: Final[bool] = False
TRANSFER_COMPLETE_COMMAND: Final[str] = WireCommand.TRANSFER_COMPLETE.value
TRANSFER_COMPLETE_CAPABILITY: Final[str] = TRANSFER_COMPLETE_COMMAND
TRANSFER_COMPLETE_CAPABILITY_MINTED: Final[bool] = True
TRANSFER_COMPLETE_MINTED: Final[bool] = True
TRANSFER_COMPLETE_IS_WIRE_COMMAND: Final[bool] = True
TRANSFER_COMPLETE_IS_PACK_OP: Final[bool] = False
TRANSFER_COMPLETE_IS_DISPATCH_INVOKE: Final[bool] = False
TRANSFER_COMPLETE_IS_HOST_CONTROL: Final[bool] = False
JSONRPC_STAGE_ARTIFACT_MINTED: Final[bool] = False
QMX_UI_SCAFFOLDED_THIS_STORY: Final[bool] = False
TRANSFER_COMPLETE_AMENDMENT: Final[str] = "AM-09"
FORBIDDEN_TRANSFER_COMPLETE_CONTRACT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "logical_invocation_id",
        "grant_id",
        "op_id",
        "idempotency_key",
        "dispatchInvoke",
        "pack_op",
        "host_control",
        "stage_artifact",
        "transfer_artifact",
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


def transfer_complete_capability_unavailable() -> TypedRefusal:
    """Typed mismatch when initialize omitted capability ``transfer_complete``."""
    return _policy(
        "capabilities",
        "typed mismatch: missing transfer_complete",
        missing=TRANSFER_COMPLETE_CAPABILITY,
        name=TRANSFER_COMPLETE_CAPABILITY,
        jsonrpc_stage_artifact=JSONRPC_STAGE_ARTIFACT_MINTED,
        pack_op=TRANSFER_COMPLETE_IS_PACK_OP,
        dispatch_invoke=TRANSFER_COMPLETE_IS_DISPATCH_INVOKE,
        host_control=TRANSFER_COMPLETE_IS_HOST_CONTROL,
        named_amendment=TRANSFER_COMPLETE_AMENDMENT,
        seed_command_count=_SEED_COMMAND_COUNT,
        in_wire_commands=TRANSFER_COMPLETE_COMMAND in WIRE_COMMANDS,
    )


def require_transfer_complete_capability(capabilities: object) -> Result[None]:
    """Missing ``transfer_complete`` is a typed mismatch, never a silent skip."""
    if capabilities is None:
        return transfer_complete_capability_unavailable()
    if not isinstance(capabilities, Mapping):
        return _invalid("capabilities", "capabilities must be an object")
    caps = cast("Mapping[str, object]", capabilities)
    if caps.get(TRANSFER_COMPLETE_CAPABILITY) is True:
        return Ok(None)
    return transfer_complete_capability_unavailable()


def claim_transfer_complete_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming transfer_complete existed as product surface at inspect fails."""
    if existed is True or existed == "true":
        return _policy(
            TRANSFER_COMPLETE_COMMAND,
            "transfer_complete was absent as product surface at inspect SHA "
            f"{TRANSFER_COMPLETE_INSPECT_SHA} (DEC-0507 ABSENT; AM-09)",
            existed_at_inspect_sha=False,
            inspect_sha=TRANSFER_COMPLETE_INSPECT_SHA,
            named_amendment=TRANSFER_COMPLETE_AMENDMENT,
        )
    if existed is not False:
        return _invalid(
            "existed_at_inspect_sha",
            "inspect-SHA existence claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def claim_machine_artifact_get_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming machine GET /artifacts/<fp1> existed at inspect fails."""
    if existed is True or existed == "true":
        return _policy(
            "artifacts_get",
            "machine GET /artifacts/<fp1> ticket redeem was absent as product "
            f"surface at inspect SHA {TRANSFER_COMPLETE_INSPECT_SHA} "
            "(DEC-0507 ABSENT; AM-13)",
            existed_at_inspect_sha=False,
            inspect_sha=TRANSFER_COMPLETE_INSPECT_SHA,
            named_amendment="AM-13",
        )
    if existed is not False:
        return _invalid(
            "existed_at_inspect_sha",
            "inspect-SHA existence claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def claim_live_ct40_serving_transfer_complete_existed_at_inspect_sha(
    existed: object,
) -> Result[bool]:
    """Claiming live CT-40 serving of transfer_complete at inspect fails."""
    if existed is True or existed == "true":
        return _policy(
            TRANSFER_COMPLETE_COMMAND,
            "live CT-40 serving of transfer_complete was absent at inspect SHA "
            f"{TRANSFER_COMPLETE_INSPECT_SHA} (DEC-0507 ABSENT)",
            existed_at_inspect_sha=False,
            inspect_sha=TRANSFER_COMPLETE_INSPECT_SHA,
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
    """Library chrome stays Epic 66; this story is the daemon/wire name."""
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


def _parse_required_token(field: str, value: object) -> Result[str]:
    if not isinstance(value, str) or value.strip() == "":
        return _invalid(field, f"{field} is a required non-empty string", given=repr(value))
    return Ok(value.strip())


def _parse_byte_count(value: object) -> Result[int]:
    if isinstance(value, bool) or not isinstance(value, int):
        return _invalid(
            "byte_count",
            "byte_count is a required non-negative integer",
            given=repr(value),
        )
    if value < 0:
        return _invalid(
            "byte_count",
            "byte_count is a required non-negative integer",
            given=value,
        )
    return Ok(value)


def parse_transfer_complete_payload(value: object) -> Result[Mapping[str, object]]:
    """Accept ticket_id, fp1, byte_count, and the original command_id.

    Identity is ``ticket_id`` plus the original ``command_id``, never a new
    wire id. Forbidden pack/invoke/host-control keys are refused.
    """
    if not isinstance(value, Mapping):
        return _invalid("payload", "transfer_complete payload must be an object")
    entry = cast("Mapping[str, object]", value)
    for field in FORBIDDEN_TRANSFER_COMPLETE_CONTRACT_KEYS:
        if field in entry:
            return _policy(
                field,
                "transfer_complete is addable CT-40, not a pack op, "
                "dispatchInvoke, JSON-RPC stage_artifact, or host-control",
                pack_op=TRANSFER_COMPLETE_IS_PACK_OP,
                dispatch_invoke=TRANSFER_COMPLETE_IS_DISPATCH_INVOKE,
                host_control=TRANSFER_COMPLETE_IS_HOST_CONTROL,
                jsonrpc_stage_artifact=JSONRPC_STAGE_ARTIFACT_MINTED,
                named_amendment=TRANSFER_COMPLETE_AMENDMENT,
                given=repr(entry.get(field)),
            )
    ticket_id = _parse_required_token("ticket_id", entry.get("ticket_id"))
    if not isinstance(ticket_id, Ok):
        return ticket_id
    fp1 = _parse_required_token("fp1", entry.get("fp1"))
    if not isinstance(fp1, Ok):
        return fp1
    command_id = _parse_required_token("command_id", entry.get("command_id"))
    if not isinstance(command_id, Ok):
        return command_id
    byte_count = _parse_byte_count(entry.get("byte_count"))
    if not isinstance(byte_count, Ok):
        return byte_count
    return Ok(
        MappingProxyType(
            {
                "ticket_id": ticket_id.value,
                "fp1": fp1.value,
                "byte_count": byte_count.value,
                "command_id": command_id.value,
            }
        )
    )
