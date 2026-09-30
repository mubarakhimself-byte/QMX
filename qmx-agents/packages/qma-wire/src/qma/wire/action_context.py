"""Immutable host-minted ActionContext and renderer action filtering (Epic 72)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import cast

from qma.wire.invocation_envelope import OperationDescriptor, validate_input_payload
from qmf.core.refusal import Ok, RefusalCategory, Result, Retryability, TypedRefusal, is_refusal


def _refusal(field: str, reason: str, *, policy: bool = False, **extra: object) -> TypedRefusal:
    return TypedRefusal(
        category=RefusalCategory.POLICY_REJECTION if policy else RefusalCategory.INVALID_INPUT,
        retryability=Retryability.NO,
        context=MappingProxyType({"field": field, "reason": reason, **extra}),
    )


@dataclass(frozen=True, slots=True)
class ActionContext:
    """All invocation authority is copied from host stores at mount time."""

    psess: str
    view_id: str
    qualified_id: str
    package_version: str
    instance_id: str
    config_revision: int
    grant_id: str | None
    allowed_op_ids: tuple[str, ...]
    account_scope: str | None
    snapshot_cursor: int
    # Host-only binding data: intentionally excluded from the wire payload.
    operation_descriptor: OperationDescriptor | None = None
    parameter_allow_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "allowed_op_ids", tuple(self.allowed_op_ids))

    @classmethod
    def try_create(
        cls,
        *,
        psess: object,
        view_id: object,
        qualified_id: object,
        package_version: object,
        instance_id: object,
        config_revision: object,
        grant_id: object | None,
        allowed_op_ids: object,
        account_scope: object | None,
        snapshot_cursor: object,
        operation_descriptor: OperationDescriptor | None = None,
        parameter_allow_keys: object = (),
    ) -> Result[ActionContext]:
        strings = {
            "psess": psess,
            "view_id": view_id,
            "qualified_id": qualified_id,
            "package_version": package_version,
            "instance_id": instance_id,
        }
        for field, value in strings.items():
            if not isinstance(value, str) or not value.strip():
                return _refusal(field, f"{field} must be a non-empty host value")
        if not cast(str, psess).startswith("psess:"):
            return _refusal("psess", "ActionContext requires an existing psess:")
        if not cast(str, view_id).casefold().startswith("view:"):
            return _refusal("view_id", "ActionContext requires a declared view: id", policy=True)
        if (
            isinstance(config_revision, bool)
            or not isinstance(config_revision, int)
            or config_revision < 0
        ):
            return _refusal("config_revision", "config_revision must be non-negative")
        if (
            isinstance(snapshot_cursor, bool)
            or not isinstance(snapshot_cursor, int)
            or snapshot_cursor < 0
        ):
            return _refusal("snapshot_cursor", "snapshot_cursor must be non-negative")
        if grant_id is not None and (not isinstance(grant_id, str) or not grant_id.strip()):
            return _refusal("grant_id", "grant_id is a non-empty identifier or null")
        if account_scope is not None and (
            not isinstance(account_scope, str) or not account_scope.strip()
        ):
            return _refusal("account_scope", "account_scope is non-empty text or null")
        if not isinstance(allowed_op_ids, (tuple, list)):
            return _refusal("allowed_op_ids", "allowed_op_ids is an array of operation ids")
        raw_ops = cast("tuple[object, ...] | list[object]", allowed_op_ids)
        if any(not isinstance(op, str) or not op.strip() for op in raw_ops):
            return _refusal("allowed_op_ids", "allowed_op_ids is an array of operation ids")
        ops = tuple(cast("tuple[str, ...] | list[str]", raw_ops))
        if len(set(ops)) != len(ops):
            return _refusal("allowed_op_ids", "allowed operation ids are unique")
        if grant_id is None and (ops or account_scope is not None):
            return _refusal("grant_id", "ungranted context has no invoke authority", policy=True)
        if operation_descriptor is not None and ops and operation_descriptor.op_id not in ops:
            return _refusal("operation_descriptor", "descriptor is outside allowed operations")
        if not isinstance(parameter_allow_keys, (tuple, list)):
            return _refusal("parameter_ceiling", "allow_keys is an array of field names")
        raw_keys = cast("tuple[object, ...] | list[object]", parameter_allow_keys)
        if any(not isinstance(key, str) or not key.strip() for key in raw_keys):
            return _refusal("parameter_ceiling", "allow_keys is an array of field names")
        allow_keys = tuple(cast("tuple[str, ...] | list[str]", raw_keys))
        if len(set(allow_keys)) != len(allow_keys):
            return _refusal("parameter_ceiling", "allow_keys must be unique")
        return Ok(
            cls(
                cast(str, psess),
                cast(str, view_id),
                cast(str, qualified_id),
                cast(str, package_version),
                cast(str, instance_id),
                config_revision,
                grant_id,
                ops,
                account_scope,
                snapshot_cursor,
                operation_descriptor,
                allow_keys,
            )
        )

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "psess": self.psess,
                "view_id": self.view_id,
                "contribution": {
                    "qualified_id": self.qualified_id,
                    "package_version": self.package_version,
                },
                "instance_id": self.instance_id,
                "config_revision": self.config_revision,
                "grant_id": self.grant_id,
                "allowed_op_ids": list(self.allowed_op_ids),
                "account_scope": self.account_scope,
                "snapshot_cursor": self.snapshot_cursor,
            }
        )


def validate_action_context_press(
    payload: object,
    *,
    context: ActionContext,
) -> Result[Mapping[str, object]]:
    """Validate renderer input against the descriptor frozen into this mount."""
    if not isinstance(payload, Mapping):
        return _refusal("payload", "renderer action must be an object")
    raw = cast("Mapping[object, object]", payload)
    if any(not isinstance(key, str) for key in raw):
        return _refusal("payload", "renderer action keys must be strings")
    body = cast("Mapping[str, object]", raw)
    authority_keys = {
        "grant_id",
        "instance_id",
        "config_revision",
        "availability_revision",
        "psess",
        "caller_kind",
        "account_scope",
        "contribution",
        "qualified_id",
        "package_version",
        "view_id",
        "op_version",
        "parameter_ceiling",
        "allowed_op_ids",
        "effect_class",
        "snapshot_cursor",
    }
    unrelated = set(body) - {"action", "input"} - authority_keys
    if unrelated:
        return _refusal(
            "payload", "renderer action contains undeclared fields", extra=sorted(unrelated)
        )
    action = body.get("action")
    if not isinstance(action, str) or not action.strip():
        return _refusal("action", "action is a non-empty op_id")
    if action not in context.allowed_op_ids:
        return _refusal(
            "action",
            "action is not allowed by this mount's ActionContext",
            policy=True,
            action=action,
        )
    descriptor = context.operation_descriptor
    if descriptor is None or descriptor.op_id != action:
        return _refusal(
            "action", "host operation descriptor is unavailable", policy=True, action=action
        )
    input_payload = body.get("input", {})
    if not isinstance(input_payload, Mapping):
        return _refusal("input", "input must be an object")
    raw_input = cast("Mapping[object, object]", input_payload)
    if any(not isinstance(key, str) for key in raw_input):
        return _refusal("input", "input keys must be strings")
    checked_input = cast("Mapping[str, object]", raw_input)
    input_keys = set(checked_input)
    schema_keys = (
        set(descriptor.configuration.required_keys)
        | set(descriptor.configuration.optional_keys)
        | set(descriptor.configuration.defaults)
    )
    schema_extra = sorted(input_keys - schema_keys)
    if schema_extra:
        return _refusal(
            "input",
            "input contains fields outside the host operation descriptor",
            extra=schema_extra,
        )
    ceiling_extra = sorted(input_keys - set(context.parameter_allow_keys))
    if ceiling_extra:
        return _refusal(
            "input",
            "input exceeds the host-bound GrantRecord parameter ceiling",
            policy=True,
            extra=ceiling_extra,
        )
    validated = validate_input_payload(descriptor, checked_input)
    if is_refusal(validated):
        return validated
    return Ok(
        MappingProxyType(
            {
                "action": action,
                "input": validated.value,
                "context": context,
            }
        )
    )
