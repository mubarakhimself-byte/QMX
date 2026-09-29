"""Initialize capability ``stage_artifact`` means authenticated PUT /artifacts/stage.

Story 70.1 / AM-05 / AM-09 / DEC-0500. COMP-QMA-WIRE owns the capability name.
COMP-QMA-DAEMON owns the live PUT. It is not a WireCommand, not JSON-RPC, not
REST /invoke, not a UI BFF, and not a fourth CT-40 family. Seed 9/7/10 stay
the seed. Absent as product surface at inspect SHA ``34c148be`` (DEC-0507).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final, cast

from qma.wire.listener import ARTIFACTS_STAGE_PATH
from qma.wire.selected_ref import SELECTED_REF_KINDS
from qma.wire.vocabulary import WIRE_COMMANDS, WIRE_QUERIES
from qmf.core.refusal import (
    Ok,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
)

__all__ = [
    "ARTIFACT_STORE_TYPES_EXISTED_AT_INSPECT_SHA",
    "FORBIDDEN_STAGE_SELECTED_REF_KINDS",
    "JSONRPC_STAGE_ARTIFACT_MINTED",
    "STAGE_ARTIFACT_AMENDMENT",
    "STAGE_ARTIFACT_CAPABILITY",
    "STAGE_ARTIFACT_CAPABILITY_MINTED",
    "STAGE_ARTIFACT_CONTRACT",
    "STAGE_ARTIFACT_DTO_OWNER",
    "STAGE_ARTIFACT_EXISTED_AT_INSPECT_SHA",
    "STAGE_ARTIFACT_HANDLER_OWNER",
    "STAGE_ARTIFACT_HTTP_METHOD",
    "STAGE_ARTIFACT_HTTP_PATH",
    "STAGE_ARTIFACT_INSPECT_SHA",
    "STAGE_ARTIFACT_IS_WIRE_COMMAND",
    "STAGE_ARTIFACT_NEW_CT_MINTED",
    "STAGE_ARTIFACT_REFUSED_CT",
    "claim_artifact_store_types_absent_at_inspect_sha",
    "claim_stage_artifact_put_existed_at_inspect_sha",
    "refuse_jsonrpc_stage_artifact",
    "require_stage_artifact_capability",
    "stage_artifact_capability_unavailable",
]


STAGE_ARTIFACT_DTO_OWNER: Final[str] = "COMP-QMA-WIRE"
STAGE_ARTIFACT_HANDLER_OWNER: Final[str] = "COMP-QMA-DAEMON"
STAGE_ARTIFACT_CONTRACT: Final[str] = "CT-40"
STAGE_ARTIFACT_NEW_CT_MINTED: Final[bool] = False
STAGE_ARTIFACT_REFUSED_CT: Final[str] = "CT-52"
STAGE_ARTIFACT_INSPECT_SHA: Final[str] = "34c148be"
STAGE_ARTIFACT_EXISTED_AT_INSPECT_SHA: Final[bool] = False
ARTIFACT_STORE_TYPES_EXISTED_AT_INSPECT_SHA: Final[bool] = True
STAGE_ARTIFACT_CAPABILITY: Final[str] = "stage_artifact"
STAGE_ARTIFACT_CAPABILITY_MINTED: Final[bool] = True
STAGE_ARTIFACT_IS_WIRE_COMMAND: Final[bool] = False
JSONRPC_STAGE_ARTIFACT_MINTED: Final[bool] = False
STAGE_ARTIFACT_HTTP_METHOD: Final[str] = "PUT"
STAGE_ARTIFACT_HTTP_PATH: Final[str] = ARTIFACTS_STAGE_PATH
STAGE_ARTIFACT_AMENDMENT: Final[str] = "AM-05"
FORBIDDEN_STAGE_SELECTED_REF_KINDS: Final[frozenset[str]] = frozenset(
    {"upload_bytes", "local_path"}
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


def stage_artifact_capability_unavailable() -> TypedRefusal:
    """Typed mismatch when initialize omitted capability ``stage_artifact``."""
    return _policy(
        "capabilities",
        "typed mismatch: missing stage_artifact",
        missing=STAGE_ARTIFACT_CAPABILITY,
        name=STAGE_ARTIFACT_CAPABILITY,
        empty_upload=False,
        jsonrpc_stage_artifact=JSONRPC_STAGE_ARTIFACT_MINTED,
        http_put=STAGE_ARTIFACT_HTTP_PATH,
        named_amendment=STAGE_ARTIFACT_AMENDMENT,
    )


def require_stage_artifact_capability(capabilities: object) -> Result[None]:
    """Missing ``stage_artifact`` is a typed mismatch, never a silent empty upload."""
    if capabilities is None:
        return stage_artifact_capability_unavailable()
    if not isinstance(capabilities, Mapping):
        return _invalid("capabilities", "capabilities must be an object")
    caps = cast("Mapping[str, object]", capabilities)
    if caps.get(STAGE_ARTIFACT_CAPABILITY) is True:
        return Ok(None)
    return stage_artifact_capability_unavailable()


def refuse_jsonrpc_stage_artifact() -> TypedRefusal:
    """JSON-RPC ``stage_artifact`` is not minted (AM-09)."""
    return _policy(
        "command",
        "stage_artifact is the authenticated PUT /artifacts/stage, not a WireCommand",
        name=STAGE_ARTIFACT_CAPABILITY,
        jsonrpc_stage_artifact=JSONRPC_STAGE_ARTIFACT_MINTED,
        is_wire_command=STAGE_ARTIFACT_IS_WIRE_COMMAND,
        in_wire_commands=STAGE_ARTIFACT_CAPABILITY in WIRE_COMMANDS,
        in_wire_queries=STAGE_ARTIFACT_CAPABILITY in WIRE_QUERIES,
        http_put=STAGE_ARTIFACT_HTTP_PATH,
        named_amendment="AM-09",
        forbidden_selected_ref_kinds=sorted(FORBIDDEN_STAGE_SELECTED_REF_KINDS),
        selected_ref_kinds_include_forbidden=any(
            kind in SELECTED_REF_KINDS for kind in FORBIDDEN_STAGE_SELECTED_REF_KINDS
        ),
    )


def claim_stage_artifact_put_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming PUT /artifacts/stage existed at inspect SHA fails."""
    if existed is True or existed == "true":
        return _policy(
            STAGE_ARTIFACT_CAPABILITY,
            "PUT /artifacts/stage was absent as product surface at inspect SHA "
            f"{STAGE_ARTIFACT_INSPECT_SHA} (DEC-0507 ABSENT; DaemonProcess "
            "discarded TCP bytes)",
            existed_at_inspect_sha=False,
            inspect_sha=STAGE_ARTIFACT_INSPECT_SHA,
            named_amendment=STAGE_ARTIFACT_AMENDMENT,
        )
    if existed is not False:
        return _invalid(
            "existed_at_inspect_sha",
            "inspect-SHA existence claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def claim_artifact_store_types_absent_at_inspect_sha(absent: object) -> Result[bool]:
    """Claiming before_artifact_register / artifact-store types were absent fails."""
    if absent is True or absent == "true":
        return _policy(
            "artifact_store_types",
            "before_artifact_register and the in-memory artifact store existed "
            f"at inspect SHA {STAGE_ARTIFACT_INSPECT_SHA}; live PUT did not "
            "(DEC-0507)",
            types_existed_at_inspect_sha=True,
            inspect_sha=STAGE_ARTIFACT_INSPECT_SHA,
        )
    if absent is not False:
        return _invalid(
            "types_absent_at_inspect_sha",
            "inspect-SHA absence claim is a boolean",
            given=repr(absent),
        )
    return Ok(False)
