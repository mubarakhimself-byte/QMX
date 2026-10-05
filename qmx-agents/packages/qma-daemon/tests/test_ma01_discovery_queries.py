"""MA-01 live owner reads, truthful capability negotiation and exact pin checks."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest
from qma.core.operations import public_operation_descriptors
from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.wire.discovery_queries import DISCOVERY_READ_CAPABILITIES
from qma.wire.initialize import InitializeParams, WireConnection, negotiate_initialize
from qma.wire.invocation_envelope import compute_input_hash
from qma.wire.schemas import validate_instance
from qmf.core import is_ok, is_refusal


def _process(root: Path, boot: str = "boot-ma01") -> DaemonProcess:
    corpus = root / "corpus"
    corpus.mkdir(exist_ok=True, parents=True)
    result = DaemonProcess.compose(
        root,
        machine="ma01-host",
        boot_epoch_id=boot,
        plugin_load_configs=research_corpus_plugin_load_config(corpus),
    )
    assert is_ok(result), result
    return result.value


def _query(process: DaemonProcess, name: str, args: object) -> Mapping[str, object]:
    result = process.discovery_query(
        name,
        args,
        operator_principal=PrincipalClass.OPERATOR,
        capabilities=dict.fromkeys(DISCOVERY_READ_CAPABILITIES, True),
    )
    assert is_ok(result), result
    assert is_ok(validate_instance(result.value, "discovery_read"))
    return result.value


def _hit(process: DaemonProcess) -> dict[str, object]:
    result = _query(process, "facade_search", {"query": "analysis-backtest:qmb"})
    hits = cast("list[dict[str, object]]", result["hits"])
    return next(hit for hit in hits if hit["qualified_id"] == "analysis-backtest:qmb")


def _mint(process: DaemonProcess, profile: str, instance: str | None) -> None:
    result = process.product_sessions.mint(
        product_session_id="psess:ma01",
        profile=profile,
        principal="operator",
        contribution={"qualified_id": "analysis-backtest:qmb", "package_version": "0.1.0"},
        instance_id=instance,
        config_revision=4,
        as_of="2026-09-20T00:00:00Z",
        granted_ops=(),
        selected_refs=(),
        scope_path=[{"kind": "desk", "id": "research"}],
    )
    assert is_ok(result), result


def test_live_roster_roundtrip_literal_empty_and_read_purity(tmp_path: Path) -> None:
    process = _process(tmp_path)
    try:
        before_events = process.journal.read_events()
        assert is_ok(before_events)
        before = process.roster.loader.continuity_snapshot()
        rows = _query(process, "list_installed_plugins", {})
        assert {p["plugin_id"] for p in cast("list[dict[str, object]]", rows["plugins"])} == {
            "analysis-backtest",
            "research-corpus",
            "trading-readonly",
            "dev-factory",
            "pm-coordination",
        }
        hit = _hit(process)
        resolved = _query(process, "facade_get", {"hit": hit})
        assert resolved["hit"] == hit
        assert resolved["instance_id"] == "pack:analysis-backtest"
        assert resolved["authorizes_invoke"] is False
        assert _query(process, "facade_search", {"query": "NO MATCH"})["hits"] == []
        after_events = process.journal.read_events()
        assert is_ok(after_events)
        assert after_events.value == before_events.value
        assert process.roster.loader.continuity_snapshot() == before
        for key in process.roster.loader.loaded_ids():
            loaded = process.roster.loader.get(key)
            assert loaded is not None and loaded.grant_record_ids == ()
    finally:
        process.close()


def test_restart_identity_and_revision_are_exact_without_new_enable_receipts(
    tmp_path: Path,
) -> None:
    first = _process(tmp_path)
    try:
        before = _query(first, "list_installed_plugins", {})
        hit = _hit(first)
        events = first.journal.read_events()
        assert is_ok(events)
        count = len([event for event in events.value if event.event == "plugin.enabled"])
    finally:
        first.close()
    second = _process(tmp_path, "boot-ma01-second")
    try:
        assert _query(second, "list_installed_plugins", {}) == before
        assert _query(second, "facade_get", {"hit": hit})["hit"] == hit
        after = second.journal.read_events()
        assert is_ok(after)
        assert len([event for event in after.value if event.event == "plugin.enabled"]) == count
    finally:
        second.close()


@pytest.mark.parametrize(
    "change",
    [
        {"availability_revision": 999},
        {"package_version": "9.0.0"},
        {"plugin_id": "dev-factory"},
        {"point": "skill"},
    ],
)
def test_exact_identity_stale_and_forged_hits_refuse(
    tmp_path: Path, change: dict[str, object]
) -> None:
    process = _process(tmp_path)
    try:
        result = process.discovery_query(
            "facade_get",
            {"hit": {**_hit(process), **change}},
            operator_principal=PrincipalClass.OPERATOR,
            capabilities={"facade_get": True},
        )
        assert is_refusal(result), result
    finally:
        process.close()


def test_departed_dependency_and_scope_refuse(tmp_path: Path) -> None:
    process = _process(tmp_path)
    try:
        hit = _hit(process)
        _mint(process, "app-use", "pack:dev-factory")
        listed = _query(process, "list_installed_plugins", {"product_session_ref": "psess:ma01"})
        assert len(cast("list[object]", listed["plugins"])) == 1
        result = process.discovery_query(
            "facade_get",
            {"hit": hit, "product_session_ref": "psess:ma01"},
            operator_principal=PrincipalClass.OPERATOR,
            capabilities={"facade_get": True},
        )
        assert is_refusal(result) and result.context["field"] == "instance_id"
        assert is_ok(process.roster.loader.disable("analysis-backtest"))
        result = process.discovery_query(
            "facade_get",
            {"hit": hit},
            operator_principal=PrincipalClass.OPERATOR,
            capabilities={"facade_get": True},
        )
        assert is_refusal(result) and result.context["availability"] == "tombstone"
        assert result.context["silent_retarget"] is False
    finally:
        process.close()


@pytest.mark.parametrize(
    ("name", "args"),
    [
        ("facade_search", {"query": "test", "hit_class": "artifact"}),
        ("facade_search", {"query": "test", "hit_class": "knowledge"}),
        (
            "facade_get",
            {
                "hit": {
                    "hit_class": "knowledge",
                    "source_ref": "s",
                    "snapshot_ref": "snap",
                    "locator": "l",
                }
            },
        ),
        ("get_instance_health", {"instance_id": "pack:analysis-backtest"}),
    ],
)
def test_missing_owner_is_explicit(tmp_path: Path, name: str, args: object) -> None:
    process = _process(tmp_path)
    try:
        result = process.discovery_query(
            name,
            args,
            operator_principal=PrincipalClass.OPERATOR,
            capabilities=dict.fromkeys(DISCOVERY_READ_CAPABILITIES, True),
        )
        assert is_refusal(result) and result.context["reason"] == "query_unavailable"
    finally:
        process.close()


@pytest.mark.parametrize("principal", [PrincipalClass.MACHINE, "worker", "agent", None])
def test_principal_cannot_read(tmp_path: Path, principal: object) -> None:
    process = _process(tmp_path)
    try:
        result = process.discovery_query(
            "list_installed_plugins",
            {},
            operator_principal=principal,
            capabilities={"list_installed_plugins": True},
        )
        assert is_refusal(result) and result.context["field"] == "principal_class"
    finally:
        process.close()


def test_initialize_capabilities_cannot_be_echoed_and_preinitialize_query_refuses() -> None:
    params = InitializeParams.try_create(
        protocol_version="1.0.0",
        client_producer_id="ma01-client",
        capabilities={
            **dict.fromkeys(DISCOVERY_READ_CAPABILITIES, True),
            "get_instance_health": True,
        },
    )
    assert is_ok(params)
    result = negotiate_initialize(params.value, server_capabilities={})
    assert is_ok(result)
    assert not DISCOVERY_READ_CAPABILITIES.intersection(result.value.capabilities)
    assert "get_instance_health" not in result.value.capabilities
    connection = WireConnection()
    assert is_refusal(connection.require_query_capability("facade_search"))


def test_invocation_rechecks_submitted_pin_after_selection(tmp_path: Path) -> None:
    process = _process(tmp_path)
    try:
        hit = _hit(process)
        _mint(process, "app-use", "pack:analysis-backtest")
        # Replace the live generation after selection, with the same package version.
        loader = process.roster.loader
        published, revision = loader.snapshot_published_roster()
        loader.restore_published_roster(
            (
                tuple(
                    replace(row, availability_revision=revision + 1)
                    if row.plugin_id == "analysis-backtest"
                    else row
                    for row in published
                ),
                revision + 1,
            )
        )
        connection = WireConnection()
        assert is_ok(connection.authenticate_pairing("prid:ma01"))
        params = InitializeParams.try_create(
            protocol_version="1.0.0", client_producer_id="pin-client"
        )
        assert is_ok(params)
        assert is_ok(connection.complete_initialize(params.value, request_id=1))
        descriptor = next(
            item for item in public_operation_descriptors() if item.op_id == "qmb.analysis.project"
        )
        hashed = compute_input_hash({"run_fp1": "run-1"}, descriptor=descriptor)
        assert is_ok(hashed), hashed
        response = process._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "start_mission",
                    "params": {
                        "product_session_ref": "psess:ma01",
                        "contribution_pin": {
                            key: hit[key]
                            for key in ("qualified_id", "package_version", "availability_revision")
                        },
                        "envelope": {
                            "logical_invocation_id": "inv:ma01",
                            "attempt_id": 1,
                            "op_id": "qmb.analysis.project",
                            "op_version": 1,
                            "contribution": {
                                "qualified_id": "analysis-backtest:qmb",
                                "package_version": "0.1.0",
                            },
                            "instance_id": "pack:analysis-backtest",
                            "config_revision": 4,
                            "caller_session_ref": "psess:ma01",
                            "grant_id": "grant:missing",
                            "effect_class": "read",
                            "idempotency_key": "idem:ma01",
                            "reconcile_policy": "query-then-decide",
                            "input_hash": hashed.value,
                            "call_depth": 0,
                            "caller_kind": "user",
                        },
                        "payload": {},
                    },
                }
            ).encode(),
            session_key="prid:ma01",
            connection_token="pin-client",
        )
        assert response is not None
        error = cast("dict[str,object]", response["error"])
        data = cast("dict[str,object]", error["data"])
        context = cast("dict[str,object]", data["context"])
        assert context.get("availability") == "tombstone", context
        assert context["retarget_refused"] is True
    finally:
        process.close()


def test_discovery_dispatch_negotiates_actual_server_and_missing_capability(tmp_path: Path) -> None:
    process = _process(tmp_path)
    connection = WireConnection()
    assert is_ok(connection.authenticate_pairing("prid:ma01dispatch"))
    try:
        refused = process._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
            connection,
            json.dumps(
                {"jsonrpc": "2.0", "id": 1, "method": "facade_search", "params": {"query": "qmb"}}
            ).encode(),
            session_key="prid:ma01dispatch",
            connection_token="dispatch-ma01",
        )
        assert refused is not None and "error" in refused
        initialized = process._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "1.0.0",
                        "producer_id": "dispatch-ma01",
                        "capabilities": {"facade_search": True, "get_instance_health": True},
                    },
                }
            ).encode(),
            session_key="prid:ma01dispatch",
            connection_token="dispatch-ma01",
        )
        assert initialized is not None and "result" in initialized
        assert connection.capabilities["facade_search"] is True
        assert connection.capabilities["get_instance_health"] is False
        assert connection.capabilities["discovery_hit_classes"] == ["contribution"]
        for method, params, expected_ok in [
            ("facade_search", {"query": "qmb"}, True),
            ("facade_get", {"hit": _hit(process)}, False),
            ("get_instance_health", {"instance_id": "pack:analysis-backtest"}, False),
        ]:
            reply = process._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
                connection,
                json.dumps(
                    {"jsonrpc": "2.0", "id": 3, "method": method, "params": params}
                ).encode(),
                session_key="prid:ma01dispatch",
                connection_token="dispatch-ma01",
            )
            assert reply is not None
            assert ("result" in reply) == expected_ok, reply
    finally:
        process.close()
