"""Story 36.1 — compose the asyncio daemon process from existing modules."""

from __future__ import annotations

import asyncio
import inspect
import json
import runpy
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

from qma.core.ontology import ActorId, DeskSlug, Quant, RoleName
from qma.core.operations import public_operation_descriptors
from qma.core.plugins.packs import DESK_PLUGIN_PACK_IDS
from qma.core.ports.execution import ExecutionEnvironmentDeclaration
from qma.core.ports.qmb import ANALYSIS_BACKTEST_PLUGIN_ID, QMB_BACKTEST_TOOL_ID
from qma.core.vocabulary.enums import ExecutionEnvironmentKind
from qma.daemon.backtest import BacktestingService, CliQmbDoorTransport
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import (
    COMP_EXP_MINTED,
    HTTP_EXPERIMENT_SERVICE_MINTED,
    QMB_JSONL_MERGED_INTO_SQLITE,
    SIXTH_APPLICATION_MINTED,
    DaemonProcess,
)
from qma.daemon.taskgraph.records import GraphTemplate
from qma.wire.initialize import WIRE_PROTOCOL_VERSION, WireConnection
from qma.wire.invocation_envelope import compute_input_hash
from qma.wire.listener import DEFAULT_BIND_HOST, ListenerBindConfig
from qma.wire.schemas import SCHEMA_FILES
from qma.wire.vocabulary import WIRE_VOCABULARY_OWNER
from qmf.core import RefusalCategory, is_ok, is_refusal

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "daemon_process_usage.py"
PROCESS_SRC = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "process.py"


def _seed_configs(tmp_path: Path) -> dict[str, dict[str, object]]:
    seed = tmp_path / "seed-corpus"
    seed.mkdir(exist_ok=True)
    return research_corpus_plugin_load_config(seed)


def _compose(tmp_path: Path, *, boot: str = "boot-36-1") -> DaemonProcess:
    result = DaemonProcess.compose(
        tmp_path,
        machine="test-host",
        boot_epoch_id=boot,
        bind_port=0,
        plugin_load_configs=_seed_configs(tmp_path),
    )
    assert is_ok(result), result
    return result.value


def test_compose_is_listener_sqlite_writer_and_pack_roster(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path)
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            listener = bound.value
            assert listener.loopback is True
            assert listener.authentication_required is True
            assert listener.host in {DEFAULT_BIND_HOST, "127.0.0.1"}
            assert listener.port > 0
            assert listener.schema_owner == WIRE_VOCABULARY_OWNER
            assert listener.http_experiment_service is False
            assert process.sqlite_connection_count() == 1
            assert process.sqlite.thread_name == "qma-daemon-sqlite"
            assert process.sqlite.recorded_sqlite_version() == sqlite3.sqlite_version
            assert tuple(process.roster.loader.loaded_ids()) == DESK_PLUGIN_PACK_IDS
            assert process.backtesting.plugin_id == ANALYSIS_BACKTEST_PLUGIN_ID
            assert process.backtesting.tool_id == QMB_BACKTEST_TOOL_ID
            assert isinstance(process.backtesting, BacktestingService)
            assert isinstance(process.backtesting.transport, CliQmbDoorTransport)
            assert process.task_dispatcher.store.durable is process.task_graphs
            assert process.task_dispatcher.environments is process.execution_environments
            assert process.task_dispatcher.router is process.compute_router
            assert process.jobs.router is process.compute_router
            assert process.jobs.dispatcher is process.task_dispatcher
            assert process.backtesting.jobs is process.jobs
            assert process.backtesting.environments is process.execution_environments
            assert process.backtesting.tools is process.tool_registry
            assert process.nested_mission_host.compiler is process.roster.compiler
            assert process.nested_mission_host.jobs is process.jobs
            assert process.nested_mission_host.graphs is process.task_graphs
            assert process.runtime_service.jobs is process.jobs
            assert process.runtime_service.tools is process.tool_registry
            assert process.runtime_service.environments is process.execution_environments
            assert process.snapshot()["qmb_door_transport"] == "CliQmbDoorTransport"
            assert process.backtesting.scheduling_authority is None
            assert process.backtesting.parallelism is None
            assert process.backtesting.backtest_state is None
            snap = process.snapshot()
            assert snap["component"] == "COMP-QMA-DAEMON"
            assert snap["sixth_application"] is False
            assert snap["comp_exp"] is False
            assert snap["http_experiment_service"] is False
            assert snap["wire_schema_owner"] == "qma-wire"
            assert snap["wire_schema_files"] == dict(SCHEMA_FILES)
            _reader, writer = await asyncio.open_connection(listener.host, listener.port)
            writer.write(b"ping")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            await asyncio.sleep(0.05)
            assert process.accepted_connections >= 1
        finally:
            await process.aclose()

    asyncio.run(_run())


def test_no_new_comp_http_experiment_service_or_second_runtime(tmp_path: Path) -> None:
    assert COMP_EXP_MINTED is False
    assert HTTP_EXPERIMENT_SERVICE_MINTED is False
    assert SIXTH_APPLICATION_MINTED is False
    first = _compose(tmp_path)
    try:
        refused = DaemonProcess.compose(
            tmp_path / "other",
            machine="test-host",
            boot_epoch_id="boot-36-1-b",
        )
        assert is_refusal(refused)
        assert refused.category is RefusalCategory.POLICY_REJECTION
        reason = str(refused.context.get("reason", "")).lower()
        assert "second" in reason and "daemon" in reason
        http = first.start_http_experiment_service()
        assert is_refusal(http)
        assert http.context["field"] == "http_experiment_service"
        assert http.context["minted"] is False
    finally:
        first.close()


def test_sqlite_stays_one_connection_and_qmb_jsonl_is_not_merged(tmp_path: Path) -> None:
    assert QMB_JSONL_MERGED_INTO_SQLITE is False
    process = _compose(tmp_path, boot="boot-36-1-sqlite")
    try:
        assert process.sqlite_connection_count() == 1
        process.sqlite.execute(
            "CREATE TABLE IF NOT EXISTS fold_probe (id INTEGER PRIMARY KEY, note TEXT)"
        )
        process.sqlite.checkpoint("PASSIVE")
        assert process.sqlite_connection_count() == 1
        assert process.qmb_jsonl_tables_present() == frozenset()
        merged = process.merge_qmb_jsonl(tmp_path / "qmb" / "run.jsonl")
        assert is_refusal(merged)
        assert merged.context["field"] == "qmb_jsonl"
        assert merged.context["merged"] is False
        owned = merged.context["qmb_owned"]
        assert isinstance(owned, (list, tuple))
        assert "run_ledger" in owned
        assert is_refusal(process.import_qmb_package())
        assert is_refusal(process.take_qmb_owned_concern("run_ledger"))
        source = PROCESS_SRC.read_text(encoding="utf-8")
        assert "import qmb" not in source
        assert "from qmb" not in source
        assert "http.server" not in source
        assert "COMP-EXP" in source
        assert inspect.getsource(DaemonProcess.compose)
    finally:
        process.close()


def test_unauthenticated_and_plaintext_non_loopback_are_startup_refusals(
    tmp_path: Path,
) -> None:
    unauth = ListenerBindConfig.try_create(require_authentication=False)
    assert is_ok(unauth)
    refused_auth = DaemonProcess.compose(
        tmp_path,
        machine="test-host",
        boot_epoch_id="boot-unauth",
        listener=unauth.value,
    )
    assert is_refusal(refused_auth)
    assert refused_auth.context["field"] == "require_authentication"
    assert refused_auth.context["startup"] is True

    plaintext = ListenerBindConfig.try_create(
        host="10.0.0.8",
        websocket_scheme="ws",
        query_scheme="http",
        require_authentication=True,
        operator_recorded_config=True,
    )
    assert is_ok(plaintext)
    refused_plain = DaemonProcess.compose(
        tmp_path,
        machine="test-host",
        boot_epoch_id="boot-plain",
        listener=plaintext.value,
    )
    assert is_refusal(refused_plain)
    assert refused_plain.context["startup"] is True
    assert "plaintext" in str(refused_plain.context["reason"])


def test_does_not_invent_a_second_wire_schema(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="boot-36-1-wire")
    try:
        assert process.wire_schema_owner == WIRE_VOCABULARY_OWNER
        assert dict(process.wire_schema_files) == dict(SCHEMA_FILES)
        assert "envelope" in process.wire_schema_files
        assert "experiment_http" not in process.wire_schema_files
        source = PROCESS_SRC.read_text(encoding="utf-8")
        assert "schema.json" not in source
        assert "from qma.wire.listener import" in source
        assert "from qma.wire.schemas import SCHEMA_FILES" in source
        assert "from qma.wire.vocabulary import WIRE_VOCABULARY_OWNER" in source
    finally:
        process.close()


def test_process_module_does_not_import_qmb() -> None:
    before = {name for name in sys.modules if name == "qmb" or name.startswith("qmb.")}
    import qma.daemon.process as proc

    after = {name for name in sys.modules if name == "qmb" or name.startswith("qmb.")}
    assert after == before
    assert "import qmb" not in inspect.getsource(proc)
    assert "from qmb" not in inspect.getsource(proc)


def test_procedure_start_compiles_registered_template_for_registered_quant(
    tmp_path: Path,
) -> None:
    process = _compose(tmp_path)
    try:
        actor = ActorId.mint(DeskSlug.RESEARCH, "alpha")
        assert is_ok(actor)
        quant = Quant(
            actor_id=actor.value,
            desk=DeskSlug.RESEARCH,
            quant_slug="alpha",
            role=RoleName.RESEARCHER,
            name="Quant alpha",
        )
        assert is_ok(process._mailboxes.open_for_quant(quant))
        assert is_ok(
            process.execution_environments.register_declaration(
                ExecutionEnvironmentDeclaration.isolated(
                    ExecutionEnvironmentKind.LOCAL,
                    provider_ref="local-ct40-test",
                )
            )
        )
        template = GraphTemplate(
            qualified_id="research-corpus:host-start",
            version="1.0.0",
            nodes=({"id": "work", "kind": "task", "intent": "complete the requested work"},),
        )
        assert is_ok(process.nested_mission_host.register_template(template))
        (tmp_path / "operator-config.json").write_text(
            json.dumps(
                {
                    "qmb_bindings": {
                        "instance:one": {
                            "owner_actor_id": actor.value.value,
                            "environment_ref": "env:local",
                            "config_revision": 2,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        bound = SimpleNamespace(
            envelope=SimpleNamespace(op_id="qma.procedure.start", logical_invocation_id="inv:one"),
            instance=SimpleNamespace(instance_id="instance:one", config_revision=2),
            validated_payload={"procedure_id": "research-corpus:host-start"},
        )
        launched = process._execute_bound_product_operation(bound)
        assert is_ok(launched), launched
        assert launched.value.owner.actor_id == actor.value
        assert process.jobs.handle_for(launched.value.handle.job_id) is not None
    finally:
        process.close()


def test_public_ct40_start_mission_uses_minted_product_session_grant(
    tmp_path: Path,
) -> None:
    process = _compose(tmp_path)
    try:
        loaded = process.roster.loader.get("research-corpus")
        assert loaded is not None
        published = next(
            row
            for row in loaded.published
            if row.point == "graph_template" and row.qualified_id == "research-corpus:survey"
        )
        contribution = {
            "qualified_id": published.qualified_id,
            "package_version": published.package_version,
        }
        descriptor = next(
            item
            for item in public_operation_descriptors()
            if item.op_id == "qma.procedure.start" and item.version == 1
        )
        request_payload = {"procedure_id": "research-corpus:survey"}
        input_hash = compute_input_hash(request_payload, descriptor=descriptor)
        assert is_ok(input_hash), input_hash
        actor = ActorId.mint(DeskSlug.RESEARCH, "alpha")
        assert is_ok(actor)
        quant = Quant(
            actor_id=actor.value,
            desk=DeskSlug.RESEARCH,
            quant_slug="alpha",
            role=RoleName.RESEARCHER,
            name="Quant alpha",
        )
        assert is_ok(process._mailboxes.open_for_quant(quant))
        assert is_ok(
            process.execution_environments.register_declaration(
                ExecutionEnvironmentDeclaration.isolated(
                    ExecutionEnvironmentKind.LOCAL,
                    provider_ref="local-ct40-public-test",
                )
            )
        )
        second_loaded = process.roster.loader.get("analysis-backtest")
        assert second_loaded is not None
        second_published = next(
            row
            for row in second_loaded.published
            if row.point == "graph_template" and row.qualified_id == "analysis-backtest:procedure"
        )
        second_contribution = {
            "qualified_id": second_published.qualified_id,
            "package_version": second_published.package_version,
        }
        (tmp_path / "operator-config.json").write_text(
            json.dumps(
                {
                    "qmb_bindings": {
                        loaded.instance_id: {
                            "owner_actor_id": actor.value.value,
                            "environment_ref": "env:local",
                            "config_revision": 2,
                        },
                        second_loaded.instance_id: {
                            "owner_actor_id": actor.value.value,
                            "environment_ref": "env:local",
                            "config_revision": 2,
                        },
                    }
                }
            ),
            encoding="utf-8",
        )
        connection = WireConnection()
        assert is_ok(connection.authenticate_pairing("prid:ct40positive"))
        connection_token = "ct40-test-connection"
        initialized = process._dispatch_paired_ct40(
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": WIRE_PROTOCOL_VERSION,
                        "capabilities": {},
                    },
                }
            ).encode(),
            session_key="prid:ct40positive",
            connection_token=connection_token,
        )
        assert initialized is not None and "error" not in initialized, initialized
        injected_binding = process._dispatch_paired_ct40(
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 19,
                    "method": "open_product_session",
                    "params": {
                        "instance_id": loaded.instance_id,
                        "qualified_id": published.qualified_id,
                        "package_version": published.package_version,
                        "owner_actor_id": "actor:caller-invented",
                    },
                }
            ).encode(),
            session_key="prid:ct40positive",
            connection_token=connection_token,
        )
        assert injected_binding is not None and "error" in injected_binding
        opened = process._dispatch_paired_ct40(
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "open_product_session",
                    "params": {
                        "instance_id": loaded.instance_id,
                        "qualified_id": published.qualified_id,
                        "package_version": published.package_version,
                    },
                }
            ).encode(),
            session_key="prid:ct40positive",
            connection_token=connection_token,
        )
        assert opened is not None and "error" not in opened, opened
        opened_result = opened.get("result")
        assert isinstance(opened_result, dict)
        session_id = opened_result.get("product_session_id")
        assert isinstance(session_id, str)
        reopened = process._dispatch_paired_ct40(
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 20,
                    "method": "open_product_session",
                    "params": {
                        "instance_id": loaded.instance_id,
                        "qualified_id": published.qualified_id,
                        "package_version": published.package_version,
                    },
                }
            ).encode(),
            session_key="prid:ct40positive",
            connection_token=connection_token,
        )
        assert reopened is not None and "error" not in reopened
        assert reopened["result"]["product_session_id"] == session_id
        granted = process._dispatch_paired_ct40(
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "grant_product_session",
                    "params": {
                        "product_session_ref": session_id,
                        "expected_revision": opened_result["context_revision"],
                        "op_id": descriptor.op_id,
                        "op_version": descriptor.version,
                        "parameter_ceiling": {"allow_keys": ["procedure_id"]},
                        "expires_at": "2099-01-01T00:00:00Z",
                    },
                }
            ).encode(),
            session_key="prid:ct40positive",
            connection_token=connection_token,
        )
        assert granted is not None and "error" not in granted, granted
        grant_result = granted.get("result")
        assert isinstance(grant_result, dict)
        assert grant_result["context_revision"] == 1
        assert process.product_sessions.get(session_id).value.context_revision == 1
        recovered_session = process._dispatch_paired_ct40(
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 23,
                    "method": "get_product_session",
                    "params": {"product_session_ref": session_id},
                }
            ).encode(),
            session_key="prid:ct40positive",
            connection_token=connection_token,
        )
        assert recovered_session is not None and "error" not in recovered_session
        recovered_result = recovered_session["result"]
        assert recovered_result["product_session_id"] == session_id
        recovered_grants = recovered_result["grant_records"]
        assert len(recovered_grants) == 1
        assert recovered_grants[0]["grant_id"] == grant_result["grant_id"]
        assert recovered_grants[0]["op_id"] == descriptor.op_id
        injected_query = process._dispatch_paired_ct40(
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 24,
                    "method": "get_product_session",
                    "params": {
                        "product_session_ref": session_id,
                        "owner_actor_id": "actor:caller-invented",
                    },
                }
            ).encode(),
            session_key="prid:ct40positive",
            connection_token=connection_token,
        )
        assert injected_query is not None and "error" in injected_query
        stale_grant = process._dispatch_paired_ct40(
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 21,
                    "method": "grant_product_session",
                    "params": {
                        "product_session_ref": session_id,
                        "expected_revision": 0,
                        "op_id": descriptor.op_id,
                        "op_version": descriptor.version,
                        "parameter_ceiling": {"allow_keys": ["procedure_id"]},
                        "expires_at": "2099-01-01T00:00:00Z",
                    },
                }
            ).encode(),
            session_key="prid:ct40positive",
            connection_token=connection_token,
        )
        assert stale_grant is not None and "error" in stale_grant
        envelope = {
            "logical_invocation_id": "inv:ct40-positive",
            "attempt_id": 1,
            "op_id": descriptor.op_id,
            "op_version": descriptor.version,
            "contribution": contribution,
            "instance_id": loaded.instance_id,
            "config_revision": 2,
            "grant_id": grant_result["grant_id"],
            "effect_class": descriptor.effect_class.value,
            "idempotency_key": "idem:ct40-positive",
            "reconcile_policy": "query-then-decide",
            "input_hash": input_hash.value,
            "call_depth": 0,
            "caller_kind": "user",
            "caller_session_ref": session_id,
        }
        response = process._dispatch_paired_ct40(
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "start_mission",
                    "params": {
                        "product_session_ref": session_id,
                        "envelope": envelope,
                        "payload": request_payload,
                    },
                }
            ).encode(),
            session_key="prid:ct40positive",
            connection_token=connection_token,
        )
        assert response is not None and "error" not in response, response
        result = response.get("result")
        assert isinstance(result, dict)
        job_id = result.get("job_id")
        assert isinstance(job_id, str)
        assert process.jobs.handle_for(job_id) is not None

        second_open = process._dispatch_paired_ct40(
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 5,
                    "method": "open_product_session",
                    "params": {
                        "instance_id": second_loaded.instance_id,
                        "qualified_id": second_published.qualified_id,
                        "package_version": second_published.package_version,
                    },
                }
            ).encode(),
            session_key="prid:ct40positive",
            connection_token=connection_token,
        )
        assert second_open is not None and "error" not in second_open, second_open
        second_session = second_open["result"]["product_session_id"]
        second_grant = process._dispatch_paired_ct40(
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 6,
                    "method": "grant_product_session",
                    "params": {
                        "product_session_ref": second_session,
                        "expected_revision": 0,
                        "op_id": descriptor.op_id,
                        "op_version": descriptor.version,
                        "parameter_ceiling": {"allow_keys": ["procedure_id"]},
                        "expires_at": "2099-01-01T00:00:00Z",
                    },
                }
            ).encode(),
            session_key="prid:ct40positive",
            connection_token=connection_token,
        )
        assert second_grant is not None and "error" not in second_grant, second_grant
        assert second_grant["result"]["context_revision"] == 1
        # A tool operation is not declared by this pack's graph-template contribution.
        foreign_grant = process._dispatch_paired_ct40(
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 22,
                    "method": "grant_product_session",
                    "params": {
                        "product_session_ref": second_session,
                        "expected_revision": 0,
                        "op_id": "qmb.backtest.run",
                        "op_version": 1,
                        "parameter_ceiling": {"allow_keys": ["run_fp1"]},
                        "expires_at": "2099-01-01T00:00:00Z",
                    },
                }
            ).encode(),
            session_key="prid:ct40positive",
            connection_token=connection_token,
        )
        assert foreign_grant is not None and "error" in foreign_grant
        assert second_session != session_id
        second_payload = {"procedure_id": second_published.qualified_id}
        second_input_hash = compute_input_hash(second_payload, descriptor=descriptor)
        assert is_ok(second_input_hash), second_input_hash
        second_envelope = {
            "logical_invocation_id": "inv:ct40-second-pack",
            "attempt_id": 1,
            "op_id": descriptor.op_id,
            "op_version": descriptor.version,
            "contribution": second_contribution,
            "instance_id": second_loaded.instance_id,
            "config_revision": 2,
            "grant_id": second_grant["result"]["grant_id"],
            "effect_class": descriptor.effect_class.value,
            "idempotency_key": "idem:ct40-second-pack",
            "reconcile_policy": "query-then-decide",
            "input_hash": second_input_hash.value,
            "call_depth": 0,
            "caller_kind": "user",
            "caller_session_ref": second_session,
        }
        second_started = process._dispatch_paired_ct40(
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "start_mission",
                    "params": {
                        "product_session_ref": second_session,
                        "envelope": second_envelope,
                        "payload": second_payload,
                    },
                }
            ).encode(),
            session_key="prid:ct40positive",
            connection_token=connection_token,
        )
        assert second_started is not None and "error" not in second_started
        second_job_id = second_started["result"]["job_id"]
        assert second_job_id != job_id
        assert process.jobs.handle_for(second_job_id) is not None

        forged = dict(envelope)
        forged["logical_invocation_id"] = "inv:ct40-forged"
        forged["idempotency_key"] = "idem:ct40-forged"
        forged["grant_id"] = "grant:caller-invented"
        forged["input_hash"] = input_hash.value
        refused = process._dispatch_paired_ct40(
            connection,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "start_mission",
                    "params": {
                        "product_session_ref": session_id,
                        "envelope": forged,
                        "payload": request_payload,
                    },
                }
            ).encode(),
            session_key="prid:ct40positive",
            connection_token=connection_token,
        )
        assert refused is not None and "error" in refused, refused
        first_before_restart = process.jobs.handle_for(job_id)
        second_before_restart = process.jobs.handle_for(second_job_id)
        assert first_before_restart is not None
        assert second_before_restart is not None
    finally:
        process.close()

    restarted = _compose(tmp_path, boot="boot-ct40-restart")
    try:
        first_after_restart = restarted.jobs.handle_for(job_id)
        second_after_restart = restarted.jobs.handle_for(second_job_id)
        assert first_after_restart is not None
        assert second_after_restart is not None
        assert first_after_restart.job_id == first_before_restart.job_id
        assert first_after_restart.state.value == "queued"
        assert second_after_restart.job_id == second_before_restart.job_id
        assert second_after_restart.state.value == "queued"
        assert restarted.jobs.handle_for(job_id) == first_after_restart
        reconnect = WireConnection()
        assert is_ok(reconnect.authenticate_pairing("prid:ct40positive"))
        reconnect_token = "ct40-restart-connection"
        initialized_again = restarted._dispatch_paired_ct40(
            reconnect,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 30,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": WIRE_PROTOCOL_VERSION,
                        "capabilities": {},
                    },
                }
            ).encode(),
            session_key="prid:ct40positive",
            connection_token=reconnect_token,
        )
        assert initialized_again is not None and "error" not in initialized_again
        recovered_job = restarted._dispatch_paired_ct40(
            reconnect,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 31,
                    "method": "get_job",
                    "params": {"handle_id": job_id, "product_session_ref": session_id},
                }
            ).encode(),
            session_key="prid:ct40positive",
            connection_token=reconnect_token,
        )
        assert recovered_job is not None and "error" not in recovered_job
        assert recovered_job["result"]["job_id"] == job_id
        assert recovered_job["result"]["state"] == "queued"
        stolen_job = restarted._dispatch_paired_ct40(
            reconnect,
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 32,
                    "method": "get_job",
                    "params": {"handle_id": job_id, "product_session_ref": second_session},
                }
            ).encode(),
            session_key="prid:ct40positive",
            connection_token=reconnect_token,
        )
        assert stolen_job is not None and "error" in stolen_job
    finally:
        restarted.close()


def test_example_script() -> None:
    namespace = runpy.run_path(str(EXAMPLE), run_name="__main__")
    assert namespace["main"] is not None
