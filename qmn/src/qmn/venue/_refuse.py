"""Small private CT-04 builders for sanctioned ``qmn.venue`` adapters."""

from __future__ import annotations

from qmf.core.refusal import RefusalCategory, Retryability, TypedRefusal

__all__ = ["invalid", "policy"]


def invalid(field: str, reason: str, **extra: object) -> TypedRefusal:
    return _refusal(RefusalCategory.INVALID_INPUT, field, reason, **extra)


def policy(field: str, reason: str, **extra: object) -> TypedRefusal:
    return _refusal(RefusalCategory.POLICY_REJECTION, field, reason, **extra)


def _refusal(
    category: RefusalCategory, field: str, reason: str, **extra: object
) -> TypedRefusal:
    context: dict[str, object] = {"field": field, "reason": reason}
    context.update(extra)
    return TypedRefusal(category=category, retryability=Retryability.NO, context=context)
