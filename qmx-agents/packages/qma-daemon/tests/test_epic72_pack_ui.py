"""Epic 72 enable isolation, durable instance projection, and ActionContext binding."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

from qma.core.plugins.context import PluginContext
from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.persistence.substrate import PersistenceSubstrate
from qma.daemon.plugins.loader import PluginLoader
from qma.daemon.plugins.pack_ui import read_pack_ui_request_record
from qma.daemon.process import DaemonProcess
from qma.daemon.sessions.chrome import ProductSessionChrome
from qma.daemon.sessions.product_session import ProductSessionService
from qmf.core import is_ok, is_refusal


def _raw_manifest(*, pack_ui_request: object = None, include_ui: bool = True) -> dict[str, object]:
    body: dict[str, object] = {
        "id": "research-corpus",
        "version": "0.1.0",
        "qma_api": ">=0.1.0,<1.0.0",
        "desk": "research",
        "entrypoint": "research_corpus.activate",
        "dependencies": [],
        "contributions": [{"point": "tool", "local_id": "search"}],
        "contributes": [
            {
                "point": "tool",
                "local_id": "search",
                "input_schema": "search.input.v1",
            }
        ],
        "permissions": [],
        "migrations": [],
    }
    if include_ui:
        body["pack_ui_request"] = pack_ui_request
    return body


def _valid_request(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "schema": "qmx.ui.pack_ui_request.v1",
        "pack_id": "research-corpus",
        "pack_version": "0.1.0",
        "views": [
            {
                "view_id": "view:search",
                "view_version": 1,
                "op_id": "search",
                "renderer": "native",
                "slot": "canvas-widget",
                "parameter_binding": {"schema": "search.input.v1"},
            }
        ],
        "nav": [
            {"id": "search", "title": "Search", "slot": "app-nav", "view_ids": ["view:search"]}
        ],
    }
    body.update(overrides)
    return body


def _valid_view() -> dict[str, object]:
    views = cast("list[object]", _valid_request()["views"])
    return cast("dict[str, object]", views[0])


def _activate(ctx: PluginContext) -> None:
    ctx.register_tool("search", {"name": "search"})


def _open(tmp_path: Path) -> PersistenceSubstrate:
    opened = PersistenceSubstrate.open(tmp_path, machine="epic72-test", boot_epoch_id="boot-72")
    assert is_ok(opened), opened
    return opened.value


def test_enable_ingests_valid_view_and_filters_invalid_items(tmp_path: Path) -> None:
    substrate = _open(tmp_path)
    try:
        loader = PluginLoader(pack_ui_sqlite=substrate.sqlite)
        raw = _valid_request(
            views=[
                _valid_view(),
                {
                    **_valid_view(),
                    "view_id": "view:missing-op",
                    "op_id": "not-contributed",
                },
                {
                    **_valid_view(),
                    "view_id": "ui_view",
                },
                {
                    **_valid_view(),
                    "view_id": "view:schema-drift",
                    "parameter_binding": {"schema": "search.input.v2"},
                },
            ],
            nav=[
                {"id": "search", "title": "Search", "slot": "app-nav", "view_ids": ["view:search"]},
                {
                    "id": "missing",
                    "title": "Missing",
                    "slot": "app-nav",
                    "view_ids": ["view:missing-op"],
                },
            ],
        )
        loaded = loader.enable(_raw_manifest(pack_ui_request=raw), activator=_activate)
        assert is_ok(loaded), loaded
        assert loaded.value.published
        assert loaded.value.pack_ui_request is not None
        assert tuple(view.view_id for view in loaded.value.pack_ui_request.request.views) == (
            "view:search",
        )
        assert tuple(nav.id for nav in loaded.value.pack_ui_request.request.nav) == ("search",)
        assert "view_op_not_contributed" in loaded.value.pack_ui_request.diagnostics
        assert "refuse_view_as_contribution_hit" in loaded.value.pack_ui_request.diagnostics
        assert "view_schema_drift" in loaded.value.pack_ui_request.diagnostics
        assert "nav_view_id_not_declared" in loaded.value.pack_ui_request.diagnostics
    finally:
        substrate.close()


def test_invalid_or_duplicate_ui_does_not_rollback_operations_and_empty_is_valid(
    tmp_path: Path,
) -> None:
    substrate = _open(tmp_path)
    try:
        loader = PluginLoader(pack_ui_sqlite=substrate.sqlite)
        malformed = loader.enable(
            _raw_manifest(pack_ui_request={"schema": "qmx.ui.pack_ui_request.v2"}),
            activator=_activate,
        )
        assert is_ok(malformed), malformed
        assert malformed.value.published
        assert malformed.value.pack_ui_request is not None
        assert malformed.value.pack_ui_request.failure_class == "view"
        assert malformed.value.pack_ui_request.diagnostics == ("unknown_pack_ui_schema",)
        assert is_ok(loader.disable("research-corpus"))

        duplicate = loader.enable(
            _raw_manifest(pack_ui_request=[_valid_request(), _valid_request()]),
            activator=_activate,
        )
        assert is_ok(duplicate), duplicate
        assert duplicate.value.published
        assert duplicate.value.pack_ui_request is not None
        assert duplicate.value.pack_ui_request.diagnostics == ("duplicate_pack_ui_request",)
        assert is_ok(loader.disable("research-corpus"))

        empty = loader.enable(_raw_manifest(pack_ui_request=[]), activator=_activate)
        assert is_ok(empty), empty
        assert empty.value.published
        assert empty.value.pack_ui_request is not None
        assert empty.value.pack_ui_request.failure_class is None
        assert empty.value.pack_ui_request.request.views == ()
        assert is_ok(loader.disable("research-corpus"))

        identity_mismatch = loader.enable(
            _raw_manifest(
                pack_ui_request={
                    **_valid_request(),
                    "pack_version": "9.9.9",
                }
            ),
            activator=_activate,
        )
        assert is_ok(identity_mismatch), identity_mismatch
        assert identity_mismatch.value.published
        assert identity_mismatch.value.pack_ui_request is not None
        assert identity_mismatch.value.pack_ui_request.diagnostics == ("pack_ui_identity_mismatch",)
        assert is_ok(loader.disable("research-corpus"))

        headless = loader.enable(_raw_manifest(include_ui=False), activator=_activate)
        assert is_ok(headless), headless
        assert headless.value.pack_ui_request is not None
        assert headless.value.pack_ui_request.failure_class is None
        assert headless.value.pack_ui_request.request.views == ()
    finally:
        substrate.close()


def test_pack_ui_request_is_durable_and_query_checks_capability_instance_revision(
    tmp_path: Path,
) -> None:
    substrate = _open(tmp_path)
    try:
        loader = PluginLoader(pack_ui_sqlite=substrate.sqlite)
        loaded = loader.enable(
            _raw_manifest(pack_ui_request=_valid_request()),
            activator=_activate,
        )
        assert is_ok(loaded), loaded
        record = read_pack_ui_request_record(
            substrate.sqlite,
            instance_id=loaded.value.instance_id,
            availability_revision=loaded.value.availability_revision,
        )
        assert record is not None
        assert record["pack_ui_request"] == _valid_request()

        process = DaemonProcess.__new__(DaemonProcess)
        object.__setattr__(process, "_roster", SimpleNamespace(loader=loader))
        object.__setattr__(process, "_substrate", substrate)
        found = process.get_pack_ui_request(
            {
                "instance_id": loaded.value.instance_id,
                "availability_revision": loaded.value.availability_revision,
            },
            operator_principal=PrincipalClass.OPERATOR,
            capabilities={"get_pack_ui_request": True},
        )
        assert is_ok(found), found
        assert found.value.request.views[0].view_id == "view:search"
        assert is_refusal(
            process.get_pack_ui_request(
                {
                    "instance_id": loaded.value.instance_id,
                    "availability_revision": loaded.value.availability_revision + 1,
                },
                operator_principal=PrincipalClass.OPERATOR,
                capabilities={"get_pack_ui_request": True},
            )
        )
        missing_capability = process.get_pack_ui_request(
            {
                "instance_id": loaded.value.instance_id,
                "availability_revision": loaded.value.availability_revision,
            },
            operator_principal=PrincipalClass.OPERATOR,
            capabilities={},
        )
        assert is_refusal(missing_capability)
        assert missing_capability.context.get("name") == "get_pack_ui_request"
    finally:
        substrate.close()


def test_pack_ui_request_projection_survives_writer_reopen(tmp_path: Path) -> None:
    substrate = _open(tmp_path)
    loader = PluginLoader(pack_ui_sqlite=substrate.sqlite)
    loaded = loader.enable(
        _raw_manifest(pack_ui_request=_valid_request()),
        activator=_activate,
    )
    assert is_ok(loaded), loaded
    instance_id = loaded.value.instance_id
    availability_revision = loaded.value.availability_revision
    substrate.close()

    reopened = _open(tmp_path)
    try:
        record = read_pack_ui_request_record(
            reopened.sqlite,
            instance_id=instance_id,
            availability_revision=availability_revision,
        )
        assert record is not None
        assert record["pack_ui_request"] == _valid_request()
    finally:
        reopened.close()


def test_action_context_paint_zero_exactly_one_and_ambiguous_grants(tmp_path: Path) -> None:
    substrate = _open(tmp_path)
    try:
        loader = PluginLoader(pack_ui_sqlite=substrate.sqlite)
        loaded = loader.enable(
            _raw_manifest(pack_ui_request=_valid_request()),
            activator=_activate,
        )
        assert is_ok(loaded), loaded
        ingested = loaded.value.pack_ui_request
        assert ingested is not None
        view = ingested.request.views[0]
        sessions = ProductSessionService(sqlite=substrate.sqlite)
        assert is_ok(
            sessions.mint(
                product_session_id="psess:desk-1",
                profile="authoring",
                principal="operator",
                contribution={"qualified_id": "research-corpus:search", "package_version": "0.1.0"},
                instance_id=loaded.value.instance_id,
                config_revision=4,
                as_of="2026-09-30T00:00:00Z",
                granted_ops=(),
                scope_path=[{"kind": "desk", "id": "research"}],
            )
        )
        chrome = ProductSessionChrome(sessions=sessions)
        other_session = sessions.mint(
            product_session_id="psess:desk-elsewhere",
            profile="authoring",
            principal="operator",
            contribution={"qualified_id": "research-corpus:search", "package_version": "0.1.0"},
            instance_id="pack:another-instance",
            config_revision=4,
            as_of="2026-09-30T00:00:00Z",
            granted_ops=(),
            scope_path=[{"kind": "desk", "id": "research"}],
        )
        assert is_ok(other_session), other_session
        cross_instance = chrome.mint_action_context(
            product_session_id="psess:desk-elsewhere",
            view=view,
            loader=loader,
            instance_id=loaded.value.instance_id,
            config_revision=4,
            snapshot_cursor=1,
            now="2026-09-30T00:00:00Z",
        )
        assert is_refusal(cross_instance)

        ungranted = chrome.mint_action_context(
            product_session_id="psess:desk-1",
            view=view,
            loader=loader,
            instance_id=loaded.value.instance_id,
            config_revision=4,
            snapshot_cursor=1,
            now="2026-09-30T00:00:00Z",
        )
        assert is_ok(ungranted), ungranted
        assert ungranted.value.grant_id is None and ungranted.value.allowed_op_ids == ()

        def grant(grant_id: str) -> None:
            minted = sessions.host_grant(
                "psess:desk-1",
                grant_id=grant_id,
                op_id="search",
                op_version=1,
                effect_class="read",
                parameter_ceiling={"allow_keys": []},
                expires_at="2026-12-31T00:00:00Z",
            )
            assert is_ok(minted), minted

        grant("grant:search-a")
        one = chrome.mint_action_context(
            product_session_id="psess:desk-1",
            view=view,
            loader=loader,
            instance_id=loaded.value.instance_id,
            config_revision=4,
            snapshot_cursor=2,
            now="2026-09-30T00:00:00Z",
        )
        assert is_ok(one), one
        assert one.value.grant_id == "grant:search-a"
        assert one.value.allowed_op_ids == ("search",)
        grant("grant:search-b")
        ambiguous = chrome.mint_action_context(
            product_session_id="psess:desk-1",
            view=view,
            loader=loader,
            instance_id=loaded.value.instance_id,
            config_revision=4,
            snapshot_cursor=3,
            now="2026-09-30T00:00:00Z",
        )
        assert is_refusal(ambiguous)
        assert ambiguous.context.get("refusal") == "GRANT_AMBIGUOUS"
    finally:
        substrate.close()
