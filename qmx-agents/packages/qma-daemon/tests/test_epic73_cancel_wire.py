"""Epic 73 — live paired CT-40 dispatch for cancel_job."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from qma.core.ontology import ActorId, DeskSlug
from qma.core.ports.qmb import QmbAbortReceipt
from qma.core.vocabulary.enums import JobHandleState
from qma.daemon.pairing import issue_pairing_session
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.wire.initialize import WIRE_PROTOCOL_VERSION, InitializeParams, WireConnection
from qmf.core import Ok, is_ok


def _compose(tmp_path: Path) -> DaemonProcess:
    seed = tmp_path / "seed-corpus"
    seed.mkdir(exist_ok=True)
    result = DaemonProcess.compose(
        tmp_path,
        machine="epic73-wire-test",
        boot_epoch_id="boot-73-wire-test",
        plugin_load_configs=research_corpus_plugin_load_config(seed),
    )
    assert is_ok(result), result
    return result.value


def _connection(
    pairing_record_id: str,
    *,
    advertise_cancel: bool = True,
) -> WireConnection:
    conn = WireConnection()
    assert is_ok(conn.authenticate_pairing(pairing_record_id))
    params = InitializeParams.try_create(
        protocol_version=WIRE_PROTOCOL_VERSION,
        capabilities={"pairing": True},
        client_producer_id="tab:epic73-wire-test",
    )
    assert is_ok(params)
    initialized = conn.complete_initialize(
        params.value,
        assign_producer_id="tab:epic73-wire-test",
        advertise_pairing=advertise_cancel,
        server_capabilities={} if not advertise_cancel else None,
    )
    assert is_ok(initialized)
    return conn


def test_live_cancel_job_dispatch_uses_durable_origin_and_exact_fences(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = _compose(tmp_path)
    try:
        operator = process.local_operator
        assert operator is not None
        origin = "psess:epic73-live"
        minted = process.product_sessions.mint(
            product_session_id=origin,
            profile="authoring",
            principal="operator",
            contribution={"package_version": "0.1.0", "qualified_id": "analysis-backtest:qmb"},
            instance_id=None,
            config_revision=0,
            as_of="2026-09-30T00:00:00Z",
        )
        assert is_ok(minted), minted
        owner = ActorId.mint(DeskSlug.RESEARCH, "epic73-wire")
        assert is_ok(owner)
        admitted = process.backtesting.jobs.submit(
            owner=owner.value,
            task_id="task:epic73-live",
            job_id="job:epic73-live",
            logical_run_id="run:epic73-live",
            attempt_id=4,
            originating_product_session_ref=origin,
        )
        assert is_ok(admitted), admitted
        abort_calls: list[str] = []

        def _abort(job_id: str):
            abort_calls.append(job_id)
            return Ok(QmbAbortReceipt(job_id=job_id, mapped_from="JobHandle.cancel"))

        monkeypatch.setattr(process.backtesting.transport, "abort", _abort)
        paired = issue_pairing_session(
            journal=process.journal,
            sqlite=process.sqlite,
            origin="http://127.0.0.1:5173",
            expires_at=2**63 - 1,
            operator_principal=operator.principal_id,
        )
        assert is_ok(paired), paired
        conn = _connection(paired.value.pairing_record_id)
        assert conn.capabilities.get("cancel_job") is True
        response = process._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
            conn,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "stable-wire-id",
                    "method": "cancel_job",
                    "params": {
                        "handle_id": admitted.value.job_id,
                        "logical_run_id": admitted.value.logical_run_id,
                        "attempt_id": admitted.value.attempt_id,
                        "command_id": "cancel:epic73-live",
                        "expected_state": "queued",
                    },
                }
            ).encode(),
            session_key=paired.value.pairing_record_id,
            connection_token="epic73-wire-test",
        )
        assert response is not None and "result" in response, response
        result = cast("dict[str, object]", response["result"])
        assert result["state"] == JobHandleState.CANCELLED.value
        assert result["originating_product_session_ref"] == origin
        assert abort_calls == [admitted.value.job_id]

        replay = process._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
            conn,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "stable-wire-id",
                    "method": "cancel_job",
                    "params": {
                        "handle_id": admitted.value.job_id,
                        "logical_run_id": admitted.value.logical_run_id,
                        "attempt_id": admitted.value.attempt_id,
                        "command_id": "cancel:epic73-live",
                        "expected_state": "running",
                    },
                }
            ).encode(),
            session_key=paired.value.pairing_record_id,
            connection_token="epic73-wire-test",
        )
        assert replay is not None and "result" in replay, replay
        assert abort_calls == [admitted.value.job_id]

        extra_field = process._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
            conn,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "extra-field-wire-id",
                    "method": "cancel_job",
                    "params": {
                        "handle_id": admitted.value.job_id,
                        "logical_run_id": admitted.value.logical_run_id,
                        "attempt_id": admitted.value.attempt_id,
                        "command_id": "cancel:epic73-extra-field",
                        "expected_state": "cancelled",
                        "unexpected_extension": True,
                    },
                }
            ).encode(),
            session_key=paired.value.pairing_record_id,
            connection_token="epic73-wire-test",
        )
        assert extra_field is not None and "error" in extra_field
        unchanged = process.backtesting.jobs.handle_for(admitted.value.job_id)
        assert unchanged is not None and unchanged.state is JobHandleState.CANCELLED

        # The CT-42 session exposes only PrincipalClass, so the originating
        # operator resolves to local_operator. The pairing row is the durable
        # identity presented by this connection and must match that singleton.
        different_operator = issue_pairing_session(
            journal=process.journal,
            sqlite=process.sqlite,
            origin="http://127.0.0.1:5173",
            expires_at=2**63 - 1,
            operator_principal="operator:other",
        )
        assert is_ok(different_operator), different_operator
        other_conn = _connection(different_operator.value.pairing_record_id)
        other = process.backtesting.jobs.submit(
            owner=owner.value,
            task_id="task:epic73-other-operator",
            job_id="job:epic73-other-operator",
            logical_run_id="run:epic73-other-operator",
            attempt_id=1,
            originating_product_session_ref=origin,
        )
        assert is_ok(other), other
        mismatch = process._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
            other_conn,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "other-operator-wire-id",
                    "method": "cancel_job",
                    "params": {
                        "handle_id": other.value.job_id,
                        "logical_run_id": other.value.logical_run_id,
                        "attempt_id": other.value.attempt_id,
                        "command_id": "cancel:other-operator",
                        "expected_state": "queued",
                    },
                }
            ).encode(),
            session_key=different_operator.value.pairing_record_id,
            connection_token="epic73-other-operator",
        )
        assert mismatch is not None and "error" in mismatch
        mismatch_error = cast("dict[str, object]", mismatch["error"])
        mismatch_data = cast("dict[str, object]", mismatch_error["data"])
        mismatch_context = cast("dict[str, object]", mismatch_data["context"])
        assert mismatch_context["pairing_operator_principal"] == "operator:other"
    finally:
        process.close()


def test_live_cancel_job_dispatch_reports_missing_capability(tmp_path: Path) -> None:
    process = _compose(tmp_path)
    try:
        conn = _connection(f"prid:{'ab' * 16}", advertise_cancel=False)
        refused = process._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
            conn,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "missing-capability",
                    "method": "cancel_job",
                    "params": {},
                }
            ).encode(),
            session_key="pairing:session-73",
            connection_token="epic73-missing-capability",
        )
        assert refused is not None and "error" in refused
        error = cast("dict[str, object]", refused["error"])
        data = cast("dict[str, object]", error["data"])
        context = cast("dict[str, object]", data["context"])
        assert context["missing"] == "cancel_job"

        machine = WireConnection()
        assert is_ok(machine.authenticate("cred://models/test-machine", principal_class="machine"))
        params = InitializeParams.try_create(
            protocol_version=WIRE_PROTOCOL_VERSION,
            capabilities={"pairing": True},
            client_producer_id="tab:machine-cancel-test",
        )
        assert is_ok(params)
        assert is_ok(
            machine.complete_initialize(
                params.value,
                server_capabilities={"cancel_job": True},
                assign_producer_id="tab:machine-cancel-test",
            )
        )
        origin = "psess:epic73-machine"
        minted = process.product_sessions.mint(
            product_session_id=origin,
            profile="authoring",
            principal="operator",
            contribution={"package_version": "0.1.0", "qualified_id": "analysis-backtest:qmb"},
            instance_id=None,
            config_revision=0,
            as_of="2026-09-30T00:00:00Z",
        )
        assert is_ok(minted), minted
        owner = ActorId.mint(DeskSlug.RESEARCH, "epic73-machine")
        assert is_ok(owner)
        admitted = process.backtesting.jobs.submit(
            owner=owner.value,
            task_id="task:epic73-machine",
            job_id="job:epic73-machine",
            logical_run_id="run:epic73-machine",
            attempt_id=1,
            originating_product_session_ref=origin,
        )
        assert is_ok(admitted), admitted
        refused_machine = process._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
            machine,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 12,
                    "method": "cancel_job",
                    "params": {
                        "handle_id": admitted.value.job_id,
                        "logical_run_id": admitted.value.logical_run_id,
                        "attempt_id": admitted.value.attempt_id,
                        "command_id": "cancel:epic73-machine",
                        "expected_state": "queued",
                    },
                }
            ).encode(),
            session_key="machine-session",
            connection_token="machine-cancel-test",
        )
        assert refused_machine is not None and "error" in refused_machine
        machine_error = cast("dict[str, object]", refused_machine["error"])
        machine_data = cast("dict[str, object]", machine_error["data"])
        machine_context = cast("dict[str, object]", machine_data["context"])
        assert machine_context["principal_class"] == "machine"
    finally:
        process.close()
