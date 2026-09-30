"""PackUiRequest enable ingestion and durable named projection (Epic 72)."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import cast

from qma.core.plugins.manifest import PluginManifest
from qma.daemon.persistence.sqlite_writer import SingleSqliteWriter
from qma.wire.pack_ui_request import (
    PACK_UI_REQUEST_SCHEMA,
    PackUiRequest,
    parse_pack_ui_request,
)
from qmf.core.refusal import is_refusal

PLUGIN_INSTALL_RECORDS_TABLE = "plugin_install_records"


@dataclass(frozen=True, slots=True)
class IngestedPackUiRequest:
    request: PackUiRequest
    diagnostics: tuple[str, ...] = ()
    failure_class: str | None = None


def _empty(manifest: PluginManifest, *diagnostics: str) -> IngestedPackUiRequest:
    return IngestedPackUiRequest(
        PackUiRequest(manifest.id, manifest.version),
        tuple(diagnostics),
        "view" if diagnostics else None,
    )


def _seq(value: object) -> Sequence[object] | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return None
    return cast("Sequence[object]", value)


def _map(value: object) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    body = cast("Mapping[object, object]", value)
    if any(not isinstance(key, str) for key in body):
        return None
    return cast("Mapping[str, object]", body)


def _single(
    manifest: PluginManifest,
    *,
    views: Sequence[object] = (),
    nav: Sequence[object] = (),
):
    return parse_pack_ui_request(
        {
            "schema": PACK_UI_REQUEST_SCHEMA,
            "pack_id": manifest.id,
            "pack_version": manifest.version,
            "views": list(views),
            "nav": list(nav),
        }
    )


def _declared_ops(
    raw_manifest: Mapping[str, object], manifest: PluginManifest
) -> tuple[set[str], dict[str, str]]:
    allowed: set[str] = set()
    schemas: dict[str, str] = {}
    rows = (
        _seq(raw_manifest.get("contributes", ()))
        or _seq(raw_manifest.get("contributions", ()))
        or ()
    )
    for candidate in rows:
        row = _map(candidate)
        if row is None:
            continue
        local = row.get("local_id")
        qualified = row.get("qualified_id")
        op_id = row.get("op_id")
        identifiers = {
            value.strip()
            for value in (local, qualified, op_id)
            if isinstance(value, str) and value.strip()
        }
        if isinstance(local, str) and local.strip():
            identifiers.add(f"{manifest.id}:{local.strip()}")
        allowed.update(identifiers)
        schema = row.get("input_schema")
        if isinstance(schema, str) and schema.strip():
            for identifier in identifiers:
                schemas[identifier] = schema.strip()
    for contribution in manifest.contributes:
        allowed.add(contribution.local_id)
        allowed.add(f"{manifest.id}:{contribution.local_id}")
        if contribution.qualified_id is not None:
            allowed.add(contribution.qualified_id)
    return allowed, schemas


def ingest_pack_ui_request(
    raw_manifest: Mapping[str, object],
    manifest: PluginManifest,
) -> IngestedPackUiRequest:
    """Parse chrome after ops are accepted; filter a bad item without failing enable."""
    if "pack_ui_request" not in raw_manifest:
        return _empty(manifest)
    raw = raw_manifest["pack_ui_request"]
    if raw == {}:
        return _empty(manifest)
    if _seq(raw) is not None:
        documents = cast(Sequence[object], raw)
        if not documents:
            return _empty(manifest)
        if len(documents) > 1:
            return _empty(manifest, "duplicate_pack_ui_request")
        raw = documents[0]
    request = _map(raw)
    if request is None or request.get("schema") != PACK_UI_REQUEST_SCHEMA:
        return _empty(manifest, "unknown_pack_ui_schema")
    if request.get("pack_id") != manifest.id or request.get("pack_version") != manifest.version:
        return _empty(manifest, "pack_ui_identity_mismatch")
    diagnostics: list[str] = []
    forbidden = {
        "copilot_profile",
        "grant_id",
        "granted_ops",
        "allowed_op_ids",
        "psess",
        "product_session",
        "product_session_id",
        "instance_id",
        "config_revision",
        "availability_revision",
        "account_scope",
        "authorizes_invoke",
        "qualified_id",
    }
    if forbidden.intersection(request):
        return _empty(manifest, "refuse_view_as_contribution_hit")
    raw_views = _seq(request.get("views", ()))
    raw_nav = _seq(request.get("nav", ()))
    if raw_views is None:
        diagnostics.append("invalid_views")
        raw_views = ()
    if raw_nav is None:
        diagnostics.append("invalid_nav")
        raw_nav = ()
    contributed, schemas = _declared_ops(raw_manifest, manifest)
    valid_views: list[Mapping[str, object]] = []
    seen_view_ids: set[str] = set()
    for index, candidate in enumerate(raw_views):
        row = _map(candidate)
        if row is None:
            diagnostics.append(f"invalid_view:{index}")
            continue
        view_id = row.get("view_id")
        if isinstance(view_id, str):
            folded_view_id = view_id.casefold()
            if folded_view_id in {"ui_view", "ui-view"} or not folded_view_id.startswith("view:"):
                diagnostics.append("refuse_view_as_contribution_hit")
                continue
        op_id = row.get("op_id")
        if not isinstance(op_id, str) or op_id.strip() not in contributed:
            diagnostics.append("view_op_not_contributed")
            continue
        if isinstance(view_id, str) and view_id in seen_view_ids:
            diagnostics.append("duplicate_view_id")
            continue
        binding = _map(row.get("parameter_binding"))
        expected = schemas.get(op_id.strip())
        if expected is not None and (binding is None or binding.get("schema") != expected):
            diagnostics.append("view_schema_drift")
            continue
        checked = _single(manifest, views=(candidate,))
        if is_refusal(checked):
            fields = checked.context.get("fields", ())
            if fields or checked.context.get("refusal") == "refuse_view_as_contribution_hit":
                diagnostics.append("refuse_view_as_contribution_hit")
            else:
                diagnostics.append(f"invalid_view:{index}")
            continue
        checked_views = cast("list[object]", checked.value.to_payload()["views"])
        valid_views.append(cast(Mapping[str, object], checked_views[0]))
        if isinstance(view_id, str):
            seen_view_ids.add(view_id)
    view_ids: set[str] = set()
    for item in valid_views:
        view = _map(item)
        if view is not None and isinstance(view.get("view_id"), str):
            view_ids.add(cast(str, view.get("view_id")))
    valid_nav: list[Mapping[str, object]] = []
    seen_nav_ids: set[str] = set()
    for index, candidate in enumerate(raw_nav):
        row = _map(candidate)
        if row is None:
            diagnostics.append(f"invalid_nav:{index}")
            continue
        refs = _seq(row.get("view_ids"))
        if (
            refs is None
            or not refs
            or any(not isinstance(ref, str) or ref not in view_ids for ref in refs)
        ):
            diagnostics.append("nav_view_id_not_declared")
            continue
        if forbidden.intersection(row):
            diagnostics.append("refuse_view_as_contribution_hit")
            continue
        nav_id = row.get("id")
        if isinstance(nav_id, str) and nav_id in seen_nav_ids:
            diagnostics.append("duplicate_nav_id")
            continue
        checked = _single(manifest, views=valid_views, nav=(candidate,))
        if is_refusal(checked):
            diagnostics.append(f"invalid_nav:{index}")
            continue
        checked_nav = cast("list[object]", checked.value.to_payload()["nav"])
        valid_nav.append(cast(Mapping[str, object], checked_nav[0]))
        if isinstance(nav_id, str):
            seen_nav_ids.add(nav_id)
    checked = _single(manifest, views=valid_views, nav=valid_nav)
    if is_refusal(checked):
        return _empty(manifest, *diagnostics, "invalid_pack_ui_request")
    return IngestedPackUiRequest(
        checked.value,
        tuple(diagnostics),
        "view" if diagnostics else None,
    )


def ensure_plugin_install_records_projection(sqlite: SingleSqliteWriter) -> None:
    """Materialize the minimal Epic 72 columns on the existing sole-writer path.

    The named ``plugin_install_records`` store had no concrete SQLite projection
    at the baseline. This bridges that gap in place: no extra SQLite/store class,
    and only instance identity, availability revision, sanitized UI, and diagnostics.
    """
    sqlite.run(
        lambda conn: conn.execute(
            "CREATE TABLE IF NOT EXISTS plugin_install_records ("
            "instance_id TEXT NOT NULL, availability_revision INTEGER NOT NULL, "
            "plugin_id TEXT NOT NULL, package_version TEXT NOT NULL, "
            "pack_ui_request TEXT NOT NULL, diagnostics TEXT NOT NULL, "
            "failure_class TEXT, PRIMARY KEY(instance_id, availability_revision))"
        )
    )


def write_pack_ui_request_record(
    sqlite: SingleSqliteWriter,
    *,
    instance_id: str,
    availability_revision: int,
    plugin_id: str,
    package_version: str,
    ingested: IngestedPackUiRequest,
) -> None:
    """Store the sanitized UI DTO on the existing plugin_install_records projection."""
    ensure_plugin_install_records_projection(sqlite)
    sqlite.execute(
        "INSERT OR REPLACE INTO plugin_install_records "
        "(instance_id, availability_revision, plugin_id, package_version, "
        "pack_ui_request, diagnostics, failure_class) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            instance_id,
            availability_revision,
            plugin_id,
            package_version,
            json.dumps(dict(ingested.request.to_payload()), ensure_ascii=True, sort_keys=True),
            json.dumps(list(ingested.diagnostics), ensure_ascii=True),
            ingested.failure_class,
        ),
    )


def read_pack_ui_request_record(
    sqlite: SingleSqliteWriter,
    *,
    instance_id: str,
    availability_revision: int,
) -> Mapping[str, object] | None:
    ensure_plugin_install_records_projection(sqlite)
    rows = sqlite.execute(
        "SELECT plugin_id, package_version, pack_ui_request, diagnostics, failure_class "
        "FROM plugin_install_records WHERE instance_id = ? AND availability_revision = ?",
        (instance_id, availability_revision),
    )
    if not rows:
        return None
    plugin_id, package_version, encoded, diagnostics, failure_class = rows[0]
    if not all(
        isinstance(value, str) for value in (plugin_id, package_version, encoded, diagnostics)
    ):
        raise ValueError("plugin_install_records projection has invalid identity or payload")
    parsed: object = json.loads(cast(str, encoded))
    parsed_diagnostics: object = json.loads(cast(str, diagnostics))
    if not isinstance(parsed, dict) or not isinstance(parsed_diagnostics, list):
        raise ValueError("plugin_install_records projection payload has invalid JSON shape")
    record: dict[str, object] = {
        "instance_id": instance_id,
        "availability_revision": availability_revision,
        "pack_id": cast(str, plugin_id),
        "pack_version": cast(str, package_version),
        "pack_ui_request": cast("dict[str, object]", parsed),
        "diagnostics": cast("list[object]", parsed_diagnostics),
        "failure_class": failure_class,
    }
    return MappingProxyType(record)
