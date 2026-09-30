"""Pack-side view and navigation request DTOs (Epic 72; FEAT-0070).

Pack UI metadata is presentation-only. It cannot mint a contribution, session,
GrantRecord, or runtime identity.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, cast

from qma.wire.schemas import validate_instance
from qma.wire.vocabulary import WireQuery
from qmf.core.refusal import (
    Ok,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
    is_refusal,
)

PACK_UI_REQUEST_SCHEMA: Final[str] = "qmx.ui.pack_ui_request.v1"
PACK_UI_REQUEST_SCHEMA_NAME: Final[str] = "pack_ui_request"
PACK_UI_REQUEST_CAPABILITY: Final[str] = "pack_ui_request"
GET_PACK_UI_REQUEST_QUERY_NAME: Final[str] = WireQuery.GET_PACK_UI_REQUEST.value
GET_PACK_UI_REQUEST_CAPABILITY: Final[str] = GET_PACK_UI_REQUEST_QUERY_NAME
GET_PACK_UI_REQUEST_HTTP_PATH: Final[str] = f"/q/{GET_PACK_UI_REQUEST_QUERY_NAME}"
PACK_UI_REQUEST_SLOTS: Final[frozenset[str]] = frozenset(
    {"app-nav", "canvas-widget", "detail", "copilot-panel", "preview-tab"}
)
PACK_UI_RENDERERS: Final[frozenset[str]] = frozenset({"native", "json-render", "mcp-app"})
_FORBIDDEN_AUTHORITY_KEYS: Final[frozenset[str]] = frozenset(
    {
        "grant_id",
        "granted_ops",
        "allowed_op_ids",
        "authorizes_invoke",
        "product_session",
        "product_session_id",
        "psess",
        "instance_id",
        "availability_revision",
        "config_revision",
        "account_scope",
        "hit_class",
        "qualified_id",
        "package_version",
        "fp1",
        "tab_id",
        "runtime_id",
    }
)


def _refusal(field: str, reason: str, *, policy: bool = False, **extra: object) -> TypedRefusal:
    ctx = {"field": field, "reason": reason, **extra}
    return TypedRefusal(
        category=RefusalCategory.POLICY_REJECTION if policy else RefusalCategory.INVALID_INPUT,
        retryability=Retryability.NO,
        context=MappingProxyType(ctx),
    )


def _token(field: str, value: object) -> Result[str]:
    if not isinstance(value, str) or not value.strip():
        return _refusal(field, f"{field} must be a non-empty string")
    return Ok(value.strip())


@dataclass(frozen=True, slots=True)
class PackUiView:
    view_id: str
    view_version: int
    op_id: str
    renderer: str
    slot: str
    parameter_schema: str
    ui_resource: str | None = None
    catalog_ref: str | None = None

    def to_payload(self) -> Mapping[str, object]:
        payload: dict[str, object] = {
            "view_id": self.view_id,
            "view_version": self.view_version,
            "op_id": self.op_id,
            "renderer": self.renderer,
            "slot": self.slot,
            "parameter_binding": {"schema": self.parameter_schema},
        }
        if self.ui_resource is not None:
            payload["ui_resource"] = self.ui_resource
        if self.catalog_ref is not None:
            payload["catalog_ref"] = self.catalog_ref
        return MappingProxyType(payload)


@dataclass(frozen=True, slots=True)
class PackUiNavItem:
    id: str
    title: str
    slot: str
    view_ids: tuple[str, ...]

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {"id": self.id, "title": self.title, "slot": self.slot, "view_ids": list(self.view_ids)}
        )


@dataclass(frozen=True, slots=True)
class PackUiRequest:
    pack_id: str
    pack_version: str
    nav: tuple[PackUiNavItem, ...] = ()
    views: tuple[PackUiView, ...] = ()
    schema: str = PACK_UI_REQUEST_SCHEMA

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": self.schema,
                "pack_id": self.pack_id,
                "pack_version": self.pack_version,
                "nav": [dict(row.to_payload()) for row in self.nav],
                "views": [dict(row.to_payload()) for row in self.views],
            }
        )


@dataclass(frozen=True, slots=True)
class PackUiRequestSnapshot:
    instance_id: str
    availability_revision: int
    request: PackUiRequest

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "instance_id": self.instance_id,
                "availability_revision": self.availability_revision,
                "pack_ui_request": dict(self.request.to_payload()),
            }
        )


def _mapping(value: object, field: str) -> Mapping[str, object] | TypedRefusal:
    if not isinstance(value, Mapping):
        return _refusal(field, f"{field} must be an object")
    body = cast("Mapping[object, object]", value)
    if any(not isinstance(key, str) for key in body):
        return _refusal(field, f"{field} keys must be strings")
    return cast("Mapping[str, object]", body)


def parse_pack_ui_request(value: object) -> Result[PackUiRequest]:
    """Strict standalone parser; enable-time ingestion filters items independently."""
    body = _mapping(value, "pack_ui_request")
    if isinstance(body, TypedRefusal):
        return body
    extra = sorted(set(body) - {"schema", "pack_id", "pack_version", "nav", "views"})
    if extra:
        return _refusal("pack_ui_request", "unknown PackUiRequest fields", extra=extra)
    forbidden = sorted(set(body) & _FORBIDDEN_AUTHORITY_KEYS)
    if forbidden:
        return _refusal(
            "pack_ui_request",
            "PackUiRequest cannot declare authority or identity",
            policy=True,
            fields=forbidden,
            refusal="refuse_view_as_contribution_hit",
        )
    if body.get("schema", PACK_UI_REQUEST_SCHEMA) != PACK_UI_REQUEST_SCHEMA:
        return _refusal("schema", "unknown_pack_ui_schema")
    pack_id = _token("pack_id", body.get("pack_id"))
    if not isinstance(pack_id, Ok):
        return pack_id
    pack_version = _token("pack_version", body.get("pack_version"))
    if not isinstance(pack_version, Ok):
        return pack_version
    views_raw = body.get("views", ())
    nav_raw = body.get("nav", ())
    if not isinstance(views_raw, Sequence) or isinstance(views_raw, (str, bytes)):
        return _refusal("views", "views must be an array")
    if not isinstance(nav_raw, Sequence) or isinstance(nav_raw, (str, bytes)):
        return _refusal("nav", "nav must be an array")
    views_sequence = cast("Sequence[object]", views_raw)
    nav_sequence = cast("Sequence[object]", nav_raw)

    views: list[PackUiView] = []
    view_ids: set[str] = set()
    for index, raw_view in enumerate(views_sequence):
        item = _mapping(raw_view, f"views[{index}]")
        if isinstance(item, TypedRefusal):
            return item
        forbidden = sorted(set(item) & _FORBIDDEN_AUTHORITY_KEYS)
        if forbidden:
            return _refusal(
                f"views[{index}]",
                "view cannot declare authority or identity",
                policy=True,
                fields=forbidden,
                refusal="refuse_view_as_contribution_hit",
            )
        allowed = {
            "view_id",
            "view_version",
            "op_id",
            "renderer",
            "slot",
            "parameter_binding",
            "ui_resource",
            "catalog_ref",
        }
        if set(item) - allowed:
            return _refusal(
                f"views[{index}]", "unknown view fields", extra=sorted(set(item) - allowed)
            )
        view_id = _token(f"views[{index}].view_id", item.get("view_id"))
        if not isinstance(view_id, Ok):
            return view_id
        folded = view_id.value.casefold()
        if folded in {"ui_view", "ui-view"} or not folded.startswith("view:"):
            return _refusal(
                f"views[{index}].view_id",
                "refuse_view_as_contribution_hit",
                policy=True,
                given=view_id.value,
            )
        if view_id.value in view_ids:
            return _refusal(f"views[{index}].view_id", "view_id must be unique")
        view_ids.add(view_id.value)
        view_version = item.get("view_version")
        if isinstance(view_version, bool) or not isinstance(view_version, int) or view_version < 1:
            return _refusal(f"views[{index}].view_version", "view_version must be positive")
        op_id = _token(f"views[{index}].op_id", item.get("op_id"))
        renderer = _token(f"views[{index}].renderer", item.get("renderer"))
        slot = _token(f"views[{index}].slot", item.get("slot"))
        if not isinstance(op_id, Ok):
            return op_id
        if not isinstance(renderer, Ok):
            return renderer
        if not isinstance(slot, Ok):
            return slot
        if renderer.value not in PACK_UI_RENDERERS:
            return _refusal(f"views[{index}].renderer", "renderer is outside the closed set")
        if slot.value not in PACK_UI_REQUEST_SLOTS:
            return _refusal(f"views[{index}].slot", "slot is outside the closed set")
        binding = _mapping(item.get("parameter_binding"), f"views[{index}].parameter_binding")
        if isinstance(binding, TypedRefusal):
            return binding
        if set(binding) != {"schema"}:
            return _refusal(
                f"views[{index}].parameter_binding",
                "request-time binding contains only schema",
                extra=sorted(set(binding) - {"schema"}),
            )
        parameter_schema = _token(f"views[{index}].parameter_binding.schema", binding.get("schema"))
        if not isinstance(parameter_schema, Ok):
            return parameter_schema
        ui_resource = item.get("ui_resource")
        catalog_ref = item.get("catalog_ref")
        if ui_resource is not None and not isinstance(ui_resource, str):
            return _refusal(f"views[{index}].ui_resource", "ui_resource must be text")
        if catalog_ref is not None and not isinstance(catalog_ref, str):
            return _refusal(f"views[{index}].catalog_ref", "catalog_ref must be text")
        views.append(
            PackUiView(
                view_id.value,
                view_version,
                op_id.value,
                renderer.value,
                slot.value,
                parameter_schema.value,
                ui_resource,
                catalog_ref,
            )
        )

    nav: list[PackUiNavItem] = []
    nav_ids: set[str] = set()
    for index, raw_nav in enumerate(nav_sequence):
        item = _mapping(raw_nav, f"nav[{index}]")
        if isinstance(item, TypedRefusal):
            return item
        forbidden = sorted(set(item) & _FORBIDDEN_AUTHORITY_KEYS)
        if forbidden:
            return _refusal(
                f"nav[{index}]",
                "nav cannot declare authority or identity",
                policy=True,
                fields=forbidden,
            )
        if set(item) != {"id", "title", "slot", "view_ids"}:
            return _refusal(f"nav[{index}]", "nav item has invalid fields")
        ident = _token(f"nav[{index}].id", item.get("id"))
        title = _token(f"nav[{index}].title", item.get("title"))
        slot = _token(f"nav[{index}].slot", item.get("slot"))
        if not isinstance(ident, Ok):
            return ident
        if not isinstance(title, Ok):
            return title
        if not isinstance(slot, Ok):
            return slot
        if slot.value not in PACK_UI_REQUEST_SLOTS:
            return _refusal(f"nav[{index}].slot", "slot is outside the closed set")
        refs = item.get("view_ids")
        if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes)) or not refs:
            return _refusal(f"nav[{index}].view_ids", "view_ids must be a non-empty array")
        refs_sequence = cast("Sequence[object]", refs)
        if any(not isinstance(ref, str) or ref not in view_ids for ref in refs_sequence):
            return _refusal(f"nav[{index}].view_ids", "nav references an undeclared view_id")
        if ident.value in nav_ids:
            return _refusal(f"nav[{index}].id", "nav id must be unique")
        nav_ids.add(ident.value)
        nav.append(
            PackUiNavItem(
                ident.value,
                title.value,
                slot.value,
                tuple(cast("Sequence[str]", refs_sequence)),
            )
        )
    return Ok(PackUiRequest(pack_id.value, pack_version.value, tuple(nav), tuple(views)))


def parse_pack_ui_request_args(value: object) -> Result[Mapping[str, object]]:
    body = _mapping(value, "args")
    if isinstance(body, TypedRefusal):
        return body
    if set(body) != {"instance_id", "availability_revision"}:
        return _refusal("args", "instance_id and availability_revision are required")
    instance = _token("instance_id", body.get("instance_id"))
    if not isinstance(instance, Ok):
        return instance
    revision = body.get("availability_revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        return _refusal("availability_revision", "availability_revision must be non-negative")
    return Ok(MappingProxyType({"instance_id": instance.value, "availability_revision": revision}))


def query_unavailable(name: object = GET_PACK_UI_REQUEST_QUERY_NAME) -> TypedRefusal:
    token = name if isinstance(name, str) and name else GET_PACK_UI_REQUEST_QUERY_NAME
    return _refusal("name", "negotiated query capability is required", policy=True, name=token)


def require_pack_ui_request_capability(capabilities: object) -> Result[None]:
    if not isinstance(capabilities, Mapping):
        return query_unavailable()
    body = cast("Mapping[object, object]", capabilities)
    if body.get(GET_PACK_UI_REQUEST_CAPABILITY) is True:
        return Ok(None)
    return query_unavailable()


def validate_pack_ui_request(value: object) -> Result[PackUiRequest]:
    checked = validate_instance(value, PACK_UI_REQUEST_SCHEMA_NAME)
    if is_refusal(checked):
        return checked
    return parse_pack_ui_request(checked.value)


def parse_action_input(value: object) -> Result[Mapping[str, object]]:
    body = _mapping(value, "action_input")
    if isinstance(body, TypedRefusal):
        return body
    action = _token("action", body.get("action"))
    if not isinstance(action, Ok):
        return action
    payload = body.get("input", {})
    mapped = _mapping(payload, "input")
    if not isinstance(mapped, Mapping):
        return mapped
    # Authority-bearing renderer fields are intentionally not copied into the result.
    return Ok(MappingProxyType({"action": action.value, "input": MappingProxyType(dict(mapped))}))
