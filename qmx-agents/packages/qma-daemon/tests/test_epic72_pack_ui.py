"""Epic 72 enable isolation, durable instance projection, and ActionContext binding."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import cast

from pytest import MonkeyPatch
from qma.core.operations import public_operation_descriptors
from qma.core.plugins.context import PluginContext
from qma.core.plugins.manifest import parse_plugin_manifest
from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.journal.authoritative import AuthoritativeJournal
from qma.daemon.persistence.substrate import PersistenceSubstrate
from qma.daemon.plugins import loader as plugin_loader_module
from qma.daemon.plugins import packs as plugin_packs_module
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.plugins.loader import PluginLoader
from qma.daemon.plugins.pack_ui import (
    ingest_pack_ui_request,
    read_pack_ui_request_record,
    restore_plugin_install_records_projection,
)
from qma.daemon.process import DaemonProcess
from qma.daemon.sessions.chrome import ProductSessionChrome
from qma.daemon.sessions.product_session import ProductSession, ProductSessionService
from qmf.core import DataDrivenClock, Instant, Ok, Result, is_ok, is_refusal

_OPERATION = next(
    descriptor
    for descriptor in public_operation_descriptors()
    if descriptor.op_id == "qmb.analysis.project"
)


def _raw_manifest(*, pack_ui_request: object = None, include_ui: bool = True) -> dict[str, object]:
    body: dict[str, object] = {
        "id": "research-corpus",
        "version": "0.1.0",
        "qma_api": ">=0.1.0,<1.0.0",
        "desk": "research",
        "entrypoint": "research_corpus.activate",
        "dependencies": [],
        "contributions": [{"point": "tool", "local_id": _OPERATION.op_id}],
        "contributes": [{"point": "tool", "local_id": _OPERATION.op_id}],
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
                "op_id": _OPERATION.op_id,
                "renderer": "native",
                "slot": "canvas-widget",
                "parameter_binding": {"schema": _OPERATION.input_schema},
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
    ctx.register_tool(_OPERATION.op_id, {"name": _OPERATION.op_id})


def _open(tmp_path: Path) -> PersistenceSubstrate:
    opened = PersistenceSubstrate.open(tmp_path, machine="epic72-test", boot_epoch_id="boot-72")
    assert is_ok(opened), opened
    return opened.value


def _bind_journal(substrate: PersistenceSubstrate) -> AuthoritativeJournal:
    base = 1_700_000_000_000_000_000
    clock = DataDrivenClock(
        boot_epoch_id="boot-72",
        wall_instants=tuple(Instant(value_ns=base + index) for index in range(128)),
        monotonic_ns=tuple(index * 1000 for index in range(128)),
    )
    bound = AuthoritativeJournal.bind(substrate, clock=clock)
    assert is_ok(bound), bound
    return bound.value


def test_enable_ingests_valid_view_and_filters_invalid_items(tmp_path: Path) -> None:
    substrate = _open(tmp_path)
    journal = _bind_journal(substrate)
    try:
        loader = PluginLoader(pack_ui_sqlite=substrate.sqlite, journal=journal)
        raw = _valid_request(
            unknown_top_level="diagnose me",
            views=[
                _valid_view(),
                "malformed view item",
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
                    "parameter_binding": {"schema": f"{_OPERATION.input_schema}.v2"},
                },
            ],
            nav=[
                "malformed nav item",
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
        assert "unknown_pack_ui_field" in loaded.value.pack_ui_request.diagnostics
        assert any(
            item.startswith("invalid_view:") for item in loaded.value.pack_ui_request.diagnostics
        )
        assert any(
            item.startswith("invalid_nav:") for item in loaded.value.pack_ui_request.diagnostics
        )
    finally:
        journal.close()
        substrate.close()


def test_invalid_or_duplicate_ui_does_not_rollback_operations_and_empty_is_valid(
    tmp_path: Path,
) -> None:
    substrate = _open(tmp_path)
    journal = _bind_journal(substrate)
    try:
        loader = PluginLoader(pack_ui_sqlite=substrate.sqlite, journal=journal)
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
        journal.close()
        substrate.close()


def test_optional_renderer_resource_is_a_mount_diagnostic_not_enable_failure(
    tmp_path: Path,
) -> None:
    substrate = _open(tmp_path)
    journal = _bind_journal(substrate)
    try:
        request = _valid_request(views=[{**_valid_view(), "renderer": "mcp-app"}])
        loader = PluginLoader(pack_ui_sqlite=substrate.sqlite, journal=journal)
        enabled = loader.enable(
            _raw_manifest(pack_ui_request=request),
            activator=_activate,
        )
        assert is_ok(enabled), enabled
        assert enabled.value.published
        assert enabled.value.pack_ui_request is not None
        assert enabled.value.pack_ui_request.request.views[0].ui_resource is None

        sessions = ProductSessionService(journal=journal, sqlite=substrate.sqlite)
        minted = sessions.mint(
            product_session_id="psess:renderer-adapter",
            profile="authoring",
            principal="operator",
            contribution={
                "qualified_id": f"research-corpus:{_OPERATION.op_id}",
                "package_version": "0.1.0",
            },
            instance_id=enabled.value.instance_id,
            config_revision=0,
            as_of="2026-09-30T00:00:00Z",
            granted_ops=(),
            scope_path=[{"kind": "desk", "id": "research"}],
        )
        assert is_ok(minted), minted
        mounted = ProductSessionChrome(sessions=sessions, journal=journal).mount_pack_ui_view(
            product_session_id="psess:renderer-adapter",
            view_id="view:search",
            loader=loader,
        )
        assert is_ok(mounted), mounted
        assert mounted.value.pane == "empty"
        assert mounted.value.diagnostics == ("mcp_app_resource_missing",)
    finally:
        journal.close()
        substrate.close()


def test_projection_failure_keeps_ops_and_records_empty_view_diagnostic(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    substrate = _open(tmp_path)
    journal = _bind_journal(substrate)

    def fail_projection(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("synthetic projection fault")

    monkeypatch.setattr(plugin_loader_module, "write_pack_ui_request_record", fail_projection)
    try:
        loader = PluginLoader(pack_ui_sqlite=substrate.sqlite, journal=journal)
        loaded = loader.enable(
            _raw_manifest(pack_ui_request=_valid_request()),
            activator=_activate,
        )
        assert is_ok(loaded), loaded
        assert loaded.value.published
        ingested = loaded.value.pack_ui_request
        assert ingested is not None
        assert ingested.failure_class == "view"
        assert ingested.request.views == ()
        assert "pack_ui_persistence_failed" in ingested.diagnostics
        record = read_pack_ui_request_record(
            substrate.sqlite,
            instance_id=loaded.value.instance_id,
            availability_revision=loaded.value.availability_revision,
        )
        assert record is not None
        stored_request = cast("dict[str, object]", record["pack_ui_request"])
        assert stored_request["views"] == []
        assert record["failure_class"] == "view"
        events = journal.read_events()
        assert is_ok(events)
        assert any(event.event == "plugin.pack_ui_projection_failed" for event in events.value)
    finally:
        journal.close()
        substrate.close()


def test_pack_ui_request_is_durable_and_query_checks_capability_instance_revision(
    tmp_path: Path,
) -> None:
    substrate = _open(tmp_path)
    journal = _bind_journal(substrate)
    try:
        loader = PluginLoader(pack_ui_sqlite=substrate.sqlite, journal=journal)
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
        absent_capability = process.get_pack_ui_request(
            {
                "instance_id": loaded.value.instance_id,
                "availability_revision": loaded.value.availability_revision,
            },
            operator_principal=PrincipalClass.OPERATOR,
        )
        assert is_refusal(absent_capability)
        assert missing_capability.context.get("name") == "get_pack_ui_request"
    finally:
        journal.close()
        substrate.close()


def test_pack_ui_action_requires_canonical_tool_contribution() -> None:
    raw = _raw_manifest(
        pack_ui_request=_valid_request(),
    )
    raw["contributes"] = [{"point": "skill", "local_id": _OPERATION.op_id}]
    manifest = parse_plugin_manifest(raw)
    ingested = ingest_pack_ui_request(raw, manifest)
    assert ingested.request.views == ()
    assert "view_op_not_contributed" in ingested.diagnostics


def test_pack_ui_request_projection_survives_writer_reopen(tmp_path: Path) -> None:
    substrate = _open(tmp_path)
    journal = _bind_journal(substrate)
    loader = PluginLoader(pack_ui_sqlite=substrate.sqlite, journal=journal)
    loaded = loader.enable(
        _raw_manifest(pack_ui_request=_valid_request()),
        activator=_activate,
    )
    assert is_ok(loaded), loaded
    instance_id = loaded.value.instance_id
    availability_revision = loaded.value.availability_revision
    journal.close()
    substrate.close()

    reopened = _open(tmp_path)
    reopened_journal = _bind_journal(reopened)
    try:
        restored = restore_plugin_install_records_projection(reopened.sqlite, reopened_journal)
        assert is_ok(restored), restored
        record = read_pack_ui_request_record(
            reopened.sqlite,
            instance_id=instance_id,
            availability_revision=availability_revision,
        )
        assert record is not None
        assert record["pack_ui_request"] == _valid_request()
    finally:
        reopened_journal.close()
        reopened.close()


def test_daemon_compose_rebuilds_instance_rows_and_reuses_revision(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    seed = tmp_path / "seed"
    seed.mkdir()
    configs = research_corpus_plugin_load_config(seed)
    original_load_manifest = plugin_packs_module.load_pack_manifest_raw
    empty_ui_request: dict[str, object] = {
        "schema": "qmx.ui.pack_ui_request.v1",
        "pack_id": "research-corpus",
        "pack_version": "0.1.0",
        "views": [],
        "nav": [],
    }

    def manifest_with_ui(plugin_root: Path) -> dict[str, object]:
        raw = original_load_manifest(plugin_root)
        if plugin_root.name == "research-corpus":
            raw["pack_ui_request"] = empty_ui_request
        return raw

    monkeypatch.setattr(plugin_packs_module, "load_pack_manifest_raw", manifest_with_ui)
    first_result = DaemonProcess.compose(
        tmp_path,
        machine="epic72-compose",
        boot_epoch_id="boot-72-compose-a",
        plugin_load_configs=configs,
    )
    assert is_ok(first_result), first_result
    first = first_result.value
    first_loaded = first.roster.loader.get("research-corpus")
    assert first_loaded is not None
    first_revision = first_loaded.availability_revision
    first_record = read_pack_ui_request_record(
        first.sqlite,
        instance_id=first_loaded.instance_id,
        availability_revision=first_revision,
    )
    assert first_record is not None
    first_request = cast("dict[str, object]", first_record["pack_ui_request"])
    assert first_request == empty_ui_request
    assert cast("list[object]", first_record["diagnostics"]) == []
    first_events = first.journal.read_events()
    assert is_ok(first_events), first_events
    first_plugin_records = [
        (event.journal_seq, event.payload)
        for event in first_events.value
        if event.event == "plugin.enabled" and event.payload.get("plugin_id") == "research-corpus"
    ]
    assert len(first_plugin_records) == 1
    first.close()

    second_result = DaemonProcess.compose(
        tmp_path,
        machine="epic72-compose",
        boot_epoch_id="boot-72-compose-b",
        plugin_load_configs=configs,
    )
    assert is_ok(second_result), second_result
    second = second_result.value
    try:
        second_loaded = second.roster.loader.get("research-corpus")
        assert second_loaded is not None
        assert second_loaded.availability_revision == first_revision
        second_events = second.journal.read_events()
        assert is_ok(second_events), second_events
        second_plugin_records = [
            (event.journal_seq, event.payload)
            for event in second_events.value
            if event.event == "plugin.enabled"
            and event.payload.get("plugin_id") == "research-corpus"
        ]
        assert second_plugin_records == first_plugin_records
        old_record = read_pack_ui_request_record(
            second.sqlite,
            instance_id=first_loaded.instance_id,
            availability_revision=first_revision,
        )
        assert old_record is not None
        old_request = cast("dict[str, object]", old_record["pack_ui_request"])
        assert old_request["views"] == first_request["views"]
        current = second.get_pack_ui_request(
            {
                "instance_id": second_loaded.instance_id,
                "availability_revision": second_loaded.availability_revision,
            },
            operator_principal=PrincipalClass.OPERATOR,
            capabilities={"get_pack_ui_request": True},
        )
        assert is_ok(current), current
        assert current.value.request.views == ()
    finally:
        second.close()


def test_action_context_paint_zero_exactly_one_and_ambiguous_grants(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    substrate = _open(tmp_path)
    journal = _bind_journal(substrate)
    try:
        loader = PluginLoader(pack_ui_sqlite=substrate.sqlite, journal=journal)
        loaded = loader.enable(
            _raw_manifest(pack_ui_request=_valid_request()),
            activator=_activate,
        )
        assert is_ok(loaded), loaded
        ingested = loaded.value.pack_ui_request
        assert ingested is not None
        view = ingested.request.views[0]
        sessions = ProductSessionService(journal=journal, sqlite=substrate.sqlite)
        assert is_ok(
            sessions.mint(
                product_session_id="psess:desk-1",
                profile="authoring",
                principal="operator",
                contribution={
                    "qualified_id": f"research-corpus:{_OPERATION.op_id}",
                    "package_version": "0.1.0",
                },
                instance_id=loaded.value.instance_id,
                config_revision=4,
                as_of="2026-09-30T00:00:00Z",
                granted_ops=(),
                scope_path=[{"kind": "desk", "id": "research"}],
            )
        )
        executed: list[object] = []
        chrome = ProductSessionChrome(
            sessions=sessions,
            journal=journal,
            execute_invocation=executed.append,
        )
        process = DaemonProcess.__new__(DaemonProcess)
        object.__setattr__(process, "_product_session_chrome", chrome)
        object.__setattr__(process, "_roster", SimpleNamespace(loader=loader))
        other_session = sessions.mint(
            product_session_id="psess:desk-elsewhere",
            profile="authoring",
            principal="operator",
            contribution={
                "qualified_id": f"research-corpus:{_OPERATION.op_id}",
                "package_version": "0.1.0",
            },
            instance_id="pack:another-instance",
            config_revision=4,
            as_of="2026-09-30T00:00:00Z",
            granted_ops=(),
            scope_path=[{"kind": "desk", "id": "research"}],
        )
        assert is_ok(other_session), other_session
        cross_instance = process.mount_pack_ui_view(
            product_session_id="psess:desk-elsewhere",
            view_id=view.view_id,
        )
        assert is_refusal(cross_instance)

        ungranted = process.mount_pack_ui_view(
            product_session_id="psess:desk-1",
            view_id=view.view_id,
        )
        assert is_ok(ungranted), ungranted
        assert ungranted.value.action_context is not None
        assert ungranted.value.action_context.grant_id is None
        assert ungranted.value.action_context.allowed_op_ids == ()
        assert is_refusal(
            process.press_pack_ui_action(
                mount_id=ungranted.value.mount_id,
                payload={"action": _OPERATION.op_id, "input": {}},
            )
        )
        expired_only = sessions.host_grant(
            "psess:desk-1",
            grant_id="grant:expired-only",
            op_id=_OPERATION.op_id,
            op_version=_OPERATION.version,
            effect_class="read",
            parameter_ceiling={"allow_keys": list(_OPERATION.configuration.required_keys)},
            expires_at="2020-01-01T00:00:00Z",
        )
        assert is_ok(expired_only), expired_only
        expired_mount = process.mount_pack_ui_view(
            product_session_id="psess:desk-1",
            view_id=view.view_id,
        )
        assert is_ok(expired_mount), expired_mount
        assert expired_mount.value.action_context is not None
        assert expired_mount.value.action_context.grant_id is None

        def grant(grant_id: str) -> None:
            minted = sessions.host_grant(
                "psess:desk-1",
                grant_id=grant_id,
                op_id=_OPERATION.op_id,
                op_version=_OPERATION.version,
                effect_class="read",
                parameter_ceiling={"allow_keys": list(_OPERATION.configuration.required_keys)},
                expires_at="2026-12-31T00:00:00Z",
            )
            assert is_ok(minted), minted

        grant("grant:search-a")
        one = process.mount_pack_ui_view(
            product_session_id="psess:desk-1",
            view_id=view.view_id,
        )
        assert is_ok(one), one
        first_context = one.value.action_context
        assert first_context is not None
        assert first_context.grant_id == "grant:search-a"
        assert first_context.allowed_op_ids == (_OPERATION.op_id,)
        remount = process.mount_pack_ui_view(
            product_session_id="psess:desk-1",
            view_id=view.view_id,
        )
        assert is_ok(remount), remount
        assert remount.value.mount_id != one.value.mount_id
        assert remount.value.action_context is not first_context
        retired_press = process.press_pack_ui_action(
            mount_id=one.value.mount_id,
            payload={
                "action": _OPERATION.op_id,
                "input": {"run_fp1": "run-1"},
                "instance_id": "pack:foreign",
                "grant_id": "grant:foreign",
            },
        )
        assert is_refusal(retired_press)
        press = process.press_pack_ui_action(
            mount_id=remount.value.mount_id,
            payload={
                "action": _OPERATION.op_id,
                "input": {"run_fp1": "run-1"},
                "instance_id": "pack:foreign",
                "grant_id": "grant:foreign",
            },
        )
        assert is_ok(press), press
        assert press.value.invocation is not None
        assert press.value.invocation.envelope.instance_id == loaded.value.instance_id
        assert press.value.invocation.grant.grant_id == "grant:search-a"
        assert press.value.invocation.validated_payload["run_fp1"] == "run-1"
        assert executed == [press.value.invocation]
        assert is_refusal(
            process.press_pack_ui_action(
                mount_id=remount.value.mount_id,
                payload={"action": _OPERATION.op_id, "input": {}, "unknown": True},
            )
        )

        current_session = sessions.get("psess:desk-1")
        assert is_ok(current_session), current_session
        config_changed_session = replace(
            current_session.value,
            context=replace(current_session.value.context, config_revision=5),
        )

        def changed_get(_session_id: object) -> Result[ProductSession]:
            return Ok(config_changed_session)

        monkeypatch.setattr(sessions, "get", changed_get)
        config_changed = process.press_pack_ui_action(
            mount_id=remount.value.mount_id,
            payload={"action": _OPERATION.op_id, "input": {"run_fp1": "run-2"}},
        )
        assert is_refusal(config_changed)
        assert config_changed.context.get("field") == "config_revision"
        monkeypatch.undo()

        loaded.value.availability_revision += 1
        availability_changed = process.press_pack_ui_action(
            mount_id=remount.value.mount_id,
            payload={"action": _OPERATION.op_id, "input": {"run_fp1": "run-2"}},
        )
        assert is_refusal(availability_changed)
        assert availability_changed.context.get("field") == "availability_revision"
        loaded.value.availability_revision -= 1

        changed_snapshot = journal.append_event(
            "pack_ui.test_snapshot_changed",
            payload={"product_session_id": "psess:desk-1"},
        )
        assert is_ok(changed_snapshot), changed_snapshot
        stale_snapshot = process.press_pack_ui_action(
            mount_id=remount.value.mount_id,
            payload={"action": _OPERATION.op_id, "input": {"run_fp1": "run-2"}},
        )
        assert is_refusal(stale_snapshot)
        assert stale_snapshot.context.get("field") == "snapshot_cursor"

        revoked = sessions.revoke_grant(
            "psess:desk-1",
            grant_id="grant:search-a",
            principal="operator",
            reason="test revocation",
            revoked_at="2026-09-30T00:00:00Z",
        )
        assert is_ok(revoked), revoked
        revoked_press = process.press_pack_ui_action(
            mount_id=remount.value.mount_id,
            payload={"action": _OPERATION.op_id, "input": {"run_fp1": "run-2"}},
        )
        assert is_refusal(revoked_press)
        assert revoked_press.context.get("revoked") is True

        grant("grant:search-b")
        grant("grant:search-c")
        ambiguous = process.mount_pack_ui_view(
            product_session_id="psess:desk-1",
            view_id=view.view_id,
        )
        assert is_refusal(ambiguous)
        assert ambiguous.context.get("refusal") == "GRANT_AMBIGUOUS"

        for grant_id in ("grant:search-b", "grant:search-c"):
            assert is_ok(
                sessions.revoke_grant(
                    "psess:desk-1",
                    grant_id=grant_id,
                    principal="operator",
                    reason="test revocation",
                    revoked_at="2026-09-30T00:00:00Z",
                )
            )
        after_revoke = process.mount_pack_ui_view(
            product_session_id="psess:desk-1",
            view_id=view.view_id,
        )
        assert is_ok(after_revoke), after_revoke
        assert after_revoke.value.action_context is not None
        assert after_revoke.value.action_context.grant_id is None
        assert first_context.grant_id == "grant:search-a"
    finally:
        journal.close()
        substrate.close()
