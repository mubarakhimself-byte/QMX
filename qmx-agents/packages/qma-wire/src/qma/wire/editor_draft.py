"""Addable authoring-draft names and capability helpers (Epic 71; AM-03/AM-09)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final, cast

from qma.wire.vocabulary import WireCommand, WireQuery
from qmf.core.refusal import Ok, RefusalCategory, Result, Retryability, TypedRefusal

__all__ = [
    "EDITOR_DRAFT_CAPABILITIES",
    "EDITOR_DRAFT_HTTP_PATH",
    "EDITOR_DRAFT_OWNER",
    "EDITOR_DRAFT_PROJECTION",
    "GET_EDITOR_DRAFT_HEAD_CAPABILITY",
    "PUBLISH_EDITOR_DRAFT_CAPABILITY",
    "SAVE_EDITOR_DRAFT_CAPABILITY",
    "editor_draft_capability_unavailable",
    "require_editor_draft_capability",
]

EDITOR_DRAFT_OWNER: Final[str] = "COMP-QMA-WIRE"
EDITOR_DRAFT_PROJECTION: Final[str] = "editor_draft_head"
SAVE_EDITOR_DRAFT_CAPABILITY: Final[str] = WireCommand.SAVE_EDITOR_DRAFT.value
PUBLISH_EDITOR_DRAFT_CAPABILITY: Final[str] = WireCommand.PUBLISH_EDITOR_DRAFT.value
GET_EDITOR_DRAFT_HEAD_CAPABILITY: Final[str] = WireQuery.GET_EDITOR_DRAFT_HEAD.value
EDITOR_DRAFT_CAPABILITIES: Final[frozenset[str]] = frozenset(
    {
        SAVE_EDITOR_DRAFT_CAPABILITY,
        GET_EDITOR_DRAFT_HEAD_CAPABILITY,
        PUBLISH_EDITOR_DRAFT_CAPABILITY,
    }
)
EDITOR_DRAFT_HTTP_PATH: Final[str] = "/q/get_editor_draft_head"


def editor_draft_capability_unavailable(name: str) -> TypedRefusal:
    """Typed mismatch when initialize omitted a draft command or query."""
    return TypedRefusal(
        category=RefusalCategory.POLICY_REJECTION,
        retryability=Retryability.NO,
        context={
            "field": "capabilities",
            "reason": f"typed mismatch: missing {name}",
            "name": name,
            "missing": name,
            "query_unavailable": name == GET_EDITOR_DRAFT_HEAD_CAPABILITY,
        },
    )


def require_editor_draft_capability(capabilities: object, name: str) -> Result[None]:
    """Require one negotiated Epic 71 capability; absence is never success."""
    if name not in EDITOR_DRAFT_CAPABILITIES:
        return TypedRefusal(
            category=RefusalCategory.INVALID_INPUT,
            retryability=Retryability.NO,
            context={
                "field": "capability",
                "reason": "unknown editor-draft capability",
                "given": name,
            },
        )
    if capabilities is None:
        return editor_draft_capability_unavailable(name)
    if not isinstance(capabilities, Mapping):
        return TypedRefusal(
            category=RefusalCategory.INVALID_INPUT,
            retryability=Retryability.NO,
            context={"field": "capabilities", "reason": "capabilities must be an object"},
        )
    caps = cast(Mapping[str, object], capabilities)
    if caps.get(name) is True:
        return Ok(None)
    return editor_draft_capability_unavailable(name)
