"""PackUiRequest enable ingestion and durable named projection (Epic 72)."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, cast

from qma.core.operations import public_operation_descriptors
from qma.core.plugins.contributes import qualify_pack_contribute
from qma.core.plugins.manifest import PluginManifest
from qma.daemon.persistence.sqlite_writer import SingleSqliteWriter
from qma.wire.pack_ui_request import (
    PACK_UI_REQUEST_SCHEMA,
    PackUiRequest,
    parse_pack_ui_request,
)
from qmf.core.refusal import Ok, Result, is_refusal
from qmf.data.store.refusals import storage_failure

PLUGIN_INSTALL_RECORDS_TABLE = "plugin_install_records"

if TYPE_CHECKING:
    from qma.daemon.journal.authoritative import AuthoritativeJournal


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


def empty_pack_ui_request(
    manifest: PluginManifest, diagnostic: str = "pack_ui_persistence_failed"
) -> IngestedPackUiRequest:
    """Return empty chrome with the required view failure diagnostic."""
    return _empty(manifest, diagnostic)


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
    manifest: PluginManifest,
) -> tuple[set[str], dict[str, str]]:
    allowed: set[str] = set()
    schemas: dict[str, str] = {}
    descriptors = {descriptor.op_id: descriptor for descriptor in public_operation_descriptors()}
    for contribution in manifest.contributes:
        # A view invokes a host operation only through a canonical published
        # tool contribution; other closed points may reuse the same local ID.
        if contribution.point != "tool":
            continue
        qualified = qualify_pack_contribute(manifest.id, contribution)
        identifiers = {contribution.local_id, qualified}
        allowed.update(identifiers)
        for operation_id in identifiers:
            descriptor = descriptors.get(operation_id)
            if descriptor is not None:
                schemas[operation_id] = descriptor.input_schema
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
    allowed_top = {"schema", "pack_id", "pack_version", "views", "nav"}
    diagnostics: list[str] = ["unknown_pack_ui_field"] if set(request) - allowed_top else []
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
    contributed, schemas = _declared_ops(manifest)
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
        if expected is None:
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


def _declare_projection(journal: AuthoritativeJournal) -> None:
    """Declare and materialize the already-ratified plugin definition fold."""
    declared = journal.declare_store(PLUGIN_INSTALL_RECORDS_TABLE)
    if is_refusal(declared):
        raise RuntimeError(f"plugin_install_records declaration refused: {declared!r}")
    folded = journal.register_fold(PLUGIN_INSTALL_RECORDS_TABLE)
    if is_refusal(folded):
        raise RuntimeError(f"plugin_install_records fold refused: {folded!r}")
    materialized = journal.stores.materialize_on_first_write(PLUGIN_INSTALL_RECORDS_TABLE)
    if is_refusal(materialized):
        raise RuntimeError(f"plugin_install_records materialization refused: {materialized!r}")


def ensure_plugin_install_records_projection(sqlite: SingleSqliteWriter) -> None:
    """Ensure the named projection's instance/revision view exists in SQLite.

    This is a materialized view of ``plugin.*`` journal events, not an independent
    source of truth or a new SQLite class. Rebuild it from the journal on startup.
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


def _row_payload(
    *,
    instance_id: str,
    availability_revision: int,
    plugin_id: str,
    package_version: str,
    ingested: IngestedPackUiRequest,
) -> dict[str, object]:
    row: dict[str, object] = {
        "instance_id": instance_id,
        "availability_revision": availability_revision,
        "plugin_id": plugin_id,
        "package_version": package_version,
        "pack_ui_request": dict(ingested.request.to_payload()),
        "diagnostics": list(ingested.diagnostics),
    }
    # Journal payload law omits absent optional values rather than encoding null.
    if ingested.failure_class is not None:
        row["failure_class"] = ingested.failure_class
    return row


def write_pack_ui_request_record(
    sqlite: SingleSqliteWriter,
    journal: AuthoritativeJournal,
    *,
    instance_id: str,
    availability_revision: int,
    plugin_id: str,
    package_version: str,
    ingested: IngestedPackUiRequest,
) -> None:
    """Append an authoritative plugin.enabled event then materialize its projection."""
    _declare_projection(journal)
    row = _row_payload(
        instance_id=instance_id,
        availability_revision=availability_revision,
        plugin_id=plugin_id,
        package_version=package_version,
        ingested=ingested,
    )
    appended = journal.append_event(
        "plugin.enabled",
        payload=row,
        scope_path=(),
    )
    if is_refusal(appended):
        raise RuntimeError(f"plugin.enabled append refused: {appended!r}")
    ensure_plugin_install_records_projection(sqlite)
    sqlite.execute(
        "INSERT INTO plugin_install_records "
        "(instance_id, availability_revision, plugin_id, package_version, "
        "pack_ui_request, diagnostics, failure_class) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            instance_id,
            availability_revision,
            plugin_id,
            package_version,
            json.dumps(row["pack_ui_request"], ensure_ascii=True, sort_keys=True),
            json.dumps(row["diagnostics"], ensure_ascii=True),
            row.get("failure_class"),
        ),
    )


def record_pack_ui_projection_failure(
    sqlite: SingleSqliteWriter,
    journal: AuthoritativeJournal,
    *,
    instance_id: str,
    availability_revision: int,
    plugin_id: str,
    package_version: str,
    ingested: IngestedPackUiRequest,
) -> None:
    """Append a corrective projection event while retaining the enable event."""
    _declare_projection(journal)
    row = _row_payload(
        instance_id=instance_id,
        availability_revision=availability_revision,
        plugin_id=plugin_id,
        package_version=package_version,
        ingested=ingested,
    )
    row["failure_class"] = "view"
    appended = journal.append_event("plugin.pack_ui_projection_failed", payload=row)
    if is_refusal(appended):
        raise RuntimeError(f"plugin.pack_ui_projection_failed append refused: {appended!r}")
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
            json.dumps(row["pack_ui_request"], ensure_ascii=True, sort_keys=True),
            json.dumps(row["diagnostics"], ensure_ascii=True),
            "view",
        ),
    )


def restore_plugin_install_records_projection(
    sqlite: SingleSqliteWriter,
    journal: AuthoritativeJournal,
) -> Result[int]:
    """Rebuild all Epic 72 instance rows and recover the durable revision high-water."""
    try:
        _declare_projection(journal)
        events = journal.read_events()
        if is_refusal(events):
            return events
        rows: dict[tuple[str, int], Mapping[str, object]] = {}
        max_revision = 0
        for event in events.value:
            if event.event not in {"plugin.enabled", "plugin.pack_ui_projection_failed"}:
                continue
            payload = event.payload
            instance_id = payload.get("instance_id")
            revision = payload.get("availability_revision")
            if (
                not isinstance(instance_id, str)
                or isinstance(revision, bool)
                or not isinstance(revision, int)
                or revision < 0
            ):
                continue
            max_revision = max(max_revision, revision)
            rows[(instance_id, revision)] = payload
        ensure_plugin_install_records_projection(sqlite)

        def rebuild(conn: sqlite3.Connection) -> None:
            conn.execute("DELETE FROM plugin_install_records")
            for payload in rows.values():
                conn.execute(
                    "INSERT INTO plugin_install_records "
                    "(instance_id, availability_revision, plugin_id, package_version, "
                    "pack_ui_request, diagnostics, failure_class) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        payload["instance_id"],
                        payload["availability_revision"],
                        payload["plugin_id"],
                        payload["package_version"],
                        json.dumps(payload["pack_ui_request"], ensure_ascii=True, sort_keys=True),
                        json.dumps(payload["diagnostics"], ensure_ascii=True),
                        payload.get("failure_class"),
                    ),
                )

        sqlite.run(rebuild)
        return Ok(max_revision)
    except (OSError, RuntimeError, ValueError, TypeError, sqlite3.Error) as exc:
        return storage_failure(
            f"could not rebuild plugin_install_records from plugin.* journal: {exc}",
            context={"field": PLUGIN_INSTALL_RECORDS_TABLE},
        )


def plugin_availability_revision_high_water(journal: AuthoritativeJournal) -> Result[int]:
    """Read the journal-backed availability revision, including disabled packs."""
    _declare_projection(journal)
    events = journal.read_events()
    if is_refusal(events):
        return events
    revisions = [
        revision
        for event in events.value
        if event.event in {"plugin.enabled", "plugin.pack_ui_projection_failed"}
        and isinstance(revision := event.payload.get("availability_revision"), int)
        and not isinstance(revision, bool)
        and revision >= 0
    ]
    return Ok(max(revisions, default=0))


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


def read_latest_plugin_install_record(
    sqlite: SingleSqliteWriter,
    *,
    instance_id: str,
) -> Mapping[str, object] | None:
    """Read the newest instance row for journal-backed boot rehydration."""
    ensure_plugin_install_records_projection(sqlite)
    rows = sqlite.execute(
        "SELECT availability_revision FROM plugin_install_records "
        "WHERE instance_id = ? ORDER BY availability_revision DESC LIMIT 1",
        (instance_id,),
    )
    if not rows:
        return None
    revision = rows[0][0]
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        raise ValueError("plugin_install_records has an invalid latest availability revision")
    return read_pack_ui_request_record(
        sqlite,
        instance_id=instance_id,
        availability_revision=revision,
    )
