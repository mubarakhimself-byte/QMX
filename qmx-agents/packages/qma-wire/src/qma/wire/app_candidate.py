"""MA02 additive CT-40 candidate names and closed request schemas."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final, cast

from qma.core.app_candidate import validate_unicode
from qma.wire.list_mailbox import query_unavailable
from qmf.core import Ok, Result
from qmf.core.refusal import RefusalCategory, Retryability, TypedRefusal


def invalid_input(field: str, reason: str, **extra: object) -> TypedRefusal:
    return TypedRefusal(
        category=RefusalCategory.INVALID_INPUT,
        retryability=Retryability.NO,
        context={"field": field, "reason": reason, **extra},
    )


def policy_rejection(field: str, reason: str, **extra: object) -> TypedRefusal:
    return TypedRefusal(
        category=RefusalCategory.POLICY_REJECTION,
        retryability=Retryability.NO,
        context={"field": field, "reason": reason, **extra},
    )


CANDIDATE_CAPABILITIES: Final[frozenset[str]] = frozenset(
    {"save_app_candidate", "get_app_candidate", "get_app_candidate_history"}
)
CANDIDATE_READS: Final[frozenset[str]] = CANDIDATE_CAPABILITIES - {"save_app_candidate"}
CANDIDATE_PROJECTION: Final[str] = "app_candidate_state"
CANDIDATE_SNAPSHOT_SCHEMA: Final[str] = "qma.wire.app_candidate.v1"


def require_candidate_capability(name: str, capabilities: object) -> Result[None]:
    if name not in CANDIDATE_CAPABILITIES:
        return invalid_input("name", "unknown app-candidate operation")
    if (
        isinstance(capabilities, Mapping)
        and cast(Mapping[str, object], capabilities).get(name) is True
    ):
        return Ok(None)
    if name in CANDIDATE_READS:
        return query_unavailable(name)
    return policy_rejection("capabilities", "missing save_app_candidate", missing=name)


def parse_candidate_args(name: str, args: object) -> Result[dict[str, object]]:
    if not isinstance(args, Mapping):
        return invalid_input("params", "expected an object")
    body = dict(cast(Mapping[str, object], args))
    unicode = validate_unicode(body, "params")
    if not isinstance(unicode, Ok):
        return unicode
    required = {"product_session_ref"}
    allowed = required | {"candidate_id"}
    if name == "save_app_candidate":
        required |= {"expected_context_revision", "content"}
        allowed |= required | {"expected_revision", "instance_id"}
    elif name == "get_app_candidate":
        required |= {"candidate_id"}
        allowed |= {"revision"}
    elif name == "get_app_candidate_history":
        required |= {"candidate_id"}
        allowed |= {"cursor_revision"}
    else:
        return invalid_input("name", "unknown app-candidate operation")
    if not required <= set(body) or not set(body) <= allowed:
        return invalid_input("params", "unknown or missing app-candidate fields")
    for key in (
        "product_session_ref",
        "candidate_id",
        "instance_id",
        "revision",
        "cursor_revision",
        "expected_revision",
    ):
        if key in body and (not isinstance(body[key], str) or not cast(str, body[key]).strip()):
            return invalid_input(key, "expected a non-empty string")
    if not cast(str, body["product_session_ref"]).startswith("psess:"):
        return invalid_input("product_session_ref", "expected a psess reference")
    if "expected_context_revision" in body:
        revision = body["expected_context_revision"]
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
            return invalid_input("expected_context_revision", "expected a non-negative integer")
    if name == "save_app_candidate":
        existing = "candidate_id" in body
        if existing != ("expected_revision" in body):
            return invalid_input(
                "expected_revision", "edits require candidate_id and expected_revision"
            )
        if existing and "instance_id" in body:
            return invalid_input("instance_id", "candidate scope is immutable after first save")
    return Ok(body)
