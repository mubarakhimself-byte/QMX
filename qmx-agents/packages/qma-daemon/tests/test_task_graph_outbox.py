"""Story 57.2 — one transaction publishes A-terminal, B-ready, and the outbox."""

from __future__ import annotations

import ast
import json
import runpy
import sqlite3
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest
from qma.core.control import author_procedure
from qma.core.ontology import ActorId, DeskSlug, Goal, Quant, RoleName
from qma.core.plugins import analysis_procedure_graph_payload
from qma.core.ports.execution import ExecutionEnvironmentDeclaration
from qma.core.vocabulary.enums import ExecutionEnvironmentKind, JobHandleState, TaskMissionState
from qma.daemon.envs import ExecutionEnvironmentRegistry
from qma.daemon.persistence import task_graph_outbox_migration
from qma.daemon.persistence.sqlite_writer import SingleSqliteWriter
from qma.daemon.persistence.task_graph_outbox_migration import migrate_task_graph_outbox
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.daemon.taskgraph import (
    DEFAULT_PARTITION_ID,
    INITIAL_ROOT_PARTITION_ID,
    OUTBOX_PROVES_EXACTLY_ONCE_EFFECT,
    OUTBOX_UNIQUE_KEY_FIELDS,
    OUTBOXES_MERGED,
    REMOTE_WORKER_OUTBOX_NOUN,
    TASK_GRAPH_ELIGIBILITY_TABLE,
    TASK_GRAPH_OUTBOX_NOUN,
    TASK_GRAPH_OUTBOX_TABLE,
    TASK_GRAPH_RECEIVER_TABLE,
    CompileRequest,
    CompileResult,
    GraphTemplate,
    GraphTemplateCatalog,
    JobHandleEvidence,
    MissionCompiler,
    OutboxAcceptanceState,
    OutboxEffectState,
    OutboxTransportState,
    ProposedTransition,
    TaskGraphDispatcher,
    TaskGraphStateService,
    instantiate_procedure,
    refuse_merge_remote_worker_outbox,
)
from qma.daemon.taskgraph.projection import (
    TaskGraphOutboxSchemaError,
    TaskGraphStateSqliteStore,
)
from qma.wire.outbox import RemoteOutbox
from qmf.core import is_ok, is_refusal

_SRC = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "taskgraph"
_EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "task_graph_outbox_usage.py"


def _quant(*, slug: str = "alpha") -> Quant:
    minted = ActorId.mint(DeskSlug.RESEARCH, slug)
    assert is_ok(minted)
    return Quant(
        actor_id=minted.value,
        desk=DeskSlug.RESEARCH,
        quant_slug=slug,
        role=RoleName.RESEARCHER,
        name=f"Quant {slug}",
    )


def _edge(src: str, dst: str, *, mapping: str = "one") -> dict[str, object]:
    return {
        "from": src,
        "to": dst,
        "mapping": mapping,
        "from_port": "data",
        "to_port": "data",
    }


def _template() -> GraphTemplate:
    return GraphTemplate(
        qualified_id="research-corpus:two-step",
        version="1",
        nodes=(
            {"id": "prepare", "kind": "task", "intent": "prepare corpus"},
            {"id": "survey", "kind": "task", "intent": "survey coverage"},
        ),
        edges=(_edge("prepare", "survey", mapping="one"),),
    )


def _compile(*, slug: str = "alpha") -> tuple[Quant, CompileResult]:
    owner = _quant(slug=slug)
    catalog = GraphTemplateCatalog()
    registered = catalog.register(_template())
    assert is_ok(registered)
    compiler = MissionCompiler(
        templates=catalog,
        known_quant_actor_ids={owner.actor_id.value},
    )
    compiled = compiler.compile(
        CompileRequest(
            goal=Goal(text="survey after prepare"),
            owner=owner,
            graph_template_ref="research-corpus:two-step",
            intent="survey after prepare",
        )
    )
    assert is_ok(compiled)
    return owner, compiled.value


def _compose(tmp_path: Path, *, boot: str) -> DaemonProcess:
    seed = tmp_path / "seed-corpus"
    seed.mkdir(exist_ok=True)
    result = DaemonProcess.compose(
        tmp_path,
        machine="test-host",
        boot_epoch_id=boot,
        bind_port=0,
        plugin_load_configs=research_corpus_plugin_load_config(seed),
    )
    assert is_ok(result), result
    return result.value


def _dispatcher(process: DaemonProcess) -> TaskGraphDispatcher:
    envs = ExecutionEnvironmentRegistry()
    assert is_ok(
        envs.register_declaration(
            ExecutionEnvironmentDeclaration.isolated(
                ExecutionEnvironmentKind.DOCKER,
                provider_ref="local-docker",
            )
        )
    )
    return TaskGraphDispatcher(environments=envs, durable=process.task_graphs)


def _complete_predecessor(
    process: DaemonProcess,
    compiled: CompileResult,
) -> tuple[TaskGraphDispatcher, str, str]:
    dispatcher = _dispatcher(process)
    dispatcher.materialize(compiled.task_graph, mission=compiled.mission)
    prepare = compiled.task_graph.ready_tasks()[0]
    decision = dispatcher.dispatch_task(
        task_id=prepare.id,
        holder_agent_id="agent-worker-1",
        environment_kind=ExecutionEnvironmentKind.DOCKER,
    )
    assert is_ok(decision)
    evidence = JobHandleEvidence(
        job_id="job-a",
        task_id=prepare.id,
        state=JobHandleState.DONE,
    )
    applied = dispatcher.apply_job_handle_evidence(evidence)
    assert is_ok(applied)
    survey = compiled.task_graph.task_for_node("survey")
    assert survey is not None
    return dispatcher, prepare.id, survey.id


def test_one_transaction_publishes_terminal_ready_and_outbox(tmp_path: Path) -> None:
    _owner, compiled = _compile()
    process = _compose(tmp_path, boot="boot-57-2-txn")
    try:
        _dispatcher_obj, prepare_id, survey_id = _complete_predecessor(process, compiled)
        restored = process.task_graphs.get(compiled.task_graph.id)
        assert is_ok(restored)
        graph = restored.value
        prepare = graph.task_by_id(prepare_id)
        survey = graph.task_by_id(survey_id)
        assert prepare is not None and prepare.state is TaskMissionState.DONE
        assert survey is not None and survey.state is TaskMissionState.READY
        eligibility = process.task_graphs.eligibility_rows(compiled.task_graph.id)
        assert len(eligibility) == 1
        assert eligibility[0].successor_node_id == "survey"
        assert eligibility[0].predecessor_node_id == "prepare"
        assert eligibility[0].predecessor_revision == 1
        rows = process.task_graphs.outbox_rows(compiled.task_graph.id)
        assert len(rows) == 1
        row = rows[0]
        assert row.unique_key() == (
            compiled.task_graph.id,
            "survey",
            1,
            DEFAULT_PARTITION_ID,
        )
        assert set(OUTBOX_UNIQUE_KEY_FIELDS) == {
            "graph_run_id",
            "successor_node_id",
            "predecessor_revision",
            "partition_id",
        }
        assert row.transport_state is OutboxTransportState.PENDING
        assert row.acceptance_state is None
        assert row.effect_state is None
        assert row.receiver_acceptance_id is None
        assert row.logical_invocation_id.startswith("inv:")
        assert "op_id" in row.target
        assert "op_version" in row.target
        assert "instance_id" in row.target
        assert "config_revision" in row.target
        assert row.envelope_hash.startswith("fp1:sha256:")
        sql_rows = process.sqlite.execute(
            "SELECT successor_node_id, transport_state, acceptance_state, "
            "effect_state FROM task_graph_outbox WHERE graph_run_id = ?",
            (compiled.task_graph.id,),
        )
        assert sql_rows == [("survey", "pending", None, None)]
        _ = _dispatcher_obj
    finally:
        process.close()


def test_initial_root_task_publishes_without_fabricated_predecessor(tmp_path: Path) -> None:
    owner = _quant(slug="initial-root")
    authored = author_procedure(analysis_procedure_graph_payload())
    assert is_ok(authored), authored
    compiler = MissionCompiler(known_quant_actor_ids={owner.actor_id.value})
    compiled_result = instantiate_procedure(
        authored.value,
        owner=owner,
        compiler=compiler,
        goal=Goal(text="run the first registered QMB procedure step"),
    )
    assert is_ok(compiled_result), compiled_result
    compiled = compiled_result.value
    root = compiled.task_graph.ready_tasks()[0]
    assert root.node_id == "backtest"
    root = replace(
        root,
        inputs={
            "op_id": "qmb.backtest.run",
            "op_version": 1,
            "instance_id": "analysis-backtest-instance",
            "config_revision": 4,
            "run_fp1": f"fp1:sha256:{'a' * 64}",
            "evidence_ref": f"fp1:sha256:{'b' * 64}",
            "model_deployment_ref": "deploy:procedure-root-test",
        },
    )
    graph = compiled.task_graph.replace_task(root)
    process = _compose(tmp_path, boot="boot-57-2-root")
    try:
        dispatcher = _dispatcher(process)
        dispatcher.materialize(graph, mission=compiled.mission)
        assert is_ok(process.task_graphs.arm_initial_publication_crash())
        with pytest.raises(RuntimeError, match="injected crash after initial_outbox"):
            dispatcher.dispatch_task(
                task_id=root.id,
                holder_agent_id="agent-initial-root",
                environment_kind=ExecutionEnvironmentKind.DOCKER,
            )
        assert process.task_graphs.outbox_rows(graph.id) == ()
        assert dispatcher.dispatch_lease_for(root.id) is None

        dispatched = dispatcher.dispatch_task(
            task_id=root.id,
            holder_agent_id="agent-initial-root",
            environment_kind=ExecutionEnvironmentKind.DOCKER,
        )
        assert is_ok(dispatched), dispatched
        rows = process.task_graphs.outbox_rows(graph.id)
        assert len(rows) == 1
        assert rows[0].transport_state is OutboxTransportState.DISPATCHED
        assert rows[0].predecessor_node_id is None
        assert rows[0].partition_id == INITIAL_ROOT_PARTITION_ID
        assert rows[0].predecessor_revision == 0
        assert rows[0].target["config_revision"] == 4
        assert rows[0].logical_invocation_id.startswith("inv:")
        assert process.task_graphs.eligibility_rows(graph.id) == ()
        accepted = dispatcher.accept_worker_invocation(rows[0].logical_invocation_id)
        assert is_ok(accepted), accepted
        task_authority = dispatcher.accepted_task_for_invocation(rows[0].logical_invocation_id)
        assert is_ok(task_authority), task_authority
        input_hash = dispatcher.expected_operation_input_hash(root.id)
        assert is_ok(input_hash)
        assert rows[0].target["operation_input_hash"] == input_hash.value
        assert accepted.value.result["operation_input_hash"] == input_hash.value

        process.task_graphs.drop_memory_cache()
        restored = process.task_graphs.reload()
        assert is_ok(restored), restored
        reopened = process.task_graphs.outbox_rows(graph.id)
        assert len(reopened) == 1
        assert reopened[0].outbox_id == rows[0].outbox_id
        assert reopened[0].logical_invocation_id == rows[0].logical_invocation_id
        assert reopened[0].acceptance_state is OutboxAcceptanceState.ACCEPTED
        assert reopened[0].receiver_acceptance_id == accepted.value.receiver_acceptance_id
    finally:
        process.close()


@pytest.mark.parametrize(
    ("invalid_field", "invalid_value"),
    [
        ("op_version", True),
        ("op_id", True),
        ("mission_id", "mission:foreign"),
        ("materialized_mission", "mission:foreign"),
    ],
)
def test_initial_root_rejects_malformed_operation_or_foreign_mission_before_effects(
    tmp_path: Path, invalid_field: str, invalid_value: object
) -> None:
    owner = _quant(slug=f"invalid-{invalid_field[:10]}")
    authored = author_procedure(analysis_procedure_graph_payload())
    assert is_ok(authored), authored
    compiler = MissionCompiler(known_quant_actor_ids={owner.actor_id.value})
    compiled_result = instantiate_procedure(
        authored.value,
        owner=owner,
        compiler=compiler,
        goal=Goal(text="refuse malformed initial operation before dispatch"),
    )
    assert is_ok(compiled_result), compiled_result
    compiled = compiled_result.value
    root = compiled.task_graph.ready_tasks()[0]
    assert root.node_id == "backtest"
    root = replace(
        root,
        inputs={
            "op_id": True if invalid_field == "op_id" else "qmb.backtest.run",
            "op_version": True if invalid_field == "op_version" else 1,
            "instance_id": "analysis-backtest-instance",
            "config_revision": 4,
            "run_fp1": f"fp1:sha256:{'a' * 64}",
            "evidence_ref": f"fp1:sha256:{'b' * 64}",
            "model_deployment_ref": "deploy:procedure-root-test",
        },
    )
    if invalid_field == "mission_id":
        root = replace(root, mission_id=cast("str", invalid_value))
    graph = compiled.task_graph.replace_task(root)
    if invalid_field == "materialized_mission":
        foreign_mission_id = cast("str", invalid_value)
        graph = replace(
            graph,
            mission_id=foreign_mission_id,
            tasks=tuple(replace(task, mission_id=foreign_mission_id) for task in graph.tasks),
        )
    process = _compose(tmp_path, boot=f"boot-invalid-root-{invalid_field}")
    try:
        dispatcher = _dispatcher(process)
        dispatcher.materialize(graph, mission=compiled.mission)
        refused = dispatcher.dispatch_task(
            task_id=root.id,
            holder_agent_id="agent-invalid-root",
            environment_kind=ExecutionEnvironmentKind.DOCKER,
        )
        assert not is_ok(refused)
        assert dispatcher.dispatch_lease_for(root.id) is None
        assert process.task_graphs.outbox_rows(graph.id) == ()
        assert process.compute_router.lease_for(root.id) is None
    finally:
        process.close()


def test_existing_successor_outbox_schema_requires_explicit_migration(tmp_path: Path) -> None:
    database = tmp_path / "legacy-task-graph.sqlite3"
    connection = sqlite3.connect(database)
    connection.executescript(
        "CREATE TABLE task_graph_outbox ("
        "graph_run_id TEXT NOT NULL, successor_node_id TEXT NOT NULL, "
        "predecessor_revision INTEGER NOT NULL, partition_id TEXT NOT NULL, "
        "outbox_id TEXT NOT NULL, predecessor_node_id TEXT NOT NULL, "
        "logical_invocation_id TEXT NOT NULL, target TEXT NOT NULL, "
        "envelope_hash TEXT NOT NULL, transport_state TEXT NOT NULL, "
        "acceptance_state TEXT, effect_state TEXT, receiver_acceptance_id TEXT, "
        "PRIMARY KEY (graph_run_id, successor_node_id, predecessor_revision, partition_id));"
        "CREATE UNIQUE INDEX task_graph_outbox_logical "
        "ON task_graph_outbox (logical_invocation_id);"
        "INSERT INTO task_graph_outbox VALUES ("
        "'graph:legacy','child',2,'default','outbox:legacy','parent',"
        "'inv:legacy','{}','fp1:sha256:legacy','dispatched',NULL,NULL,NULL);"
    )
    connection.close()
    writer = SingleSqliteWriter(database)
    assert is_ok(writer.start())
    try:
        before_schema = database.read_bytes()
        store = TaskGraphStateSqliteStore(writer)
        with pytest.raises(TaskGraphOutboxSchemaError, match="explicit"):
            store.ensure_schema()
        assert database.read_bytes() == before_schema
        refusal = TaskGraphStateService().bind_durable(sqlite=writer)
        assert is_refusal(refusal)
        assert "task_graph_outbox_migration" in str(refusal.context)
    finally:
        writer.close()
    migration_source_bytes = database.read_bytes()

    migrated = migrate_task_graph_outbox(
        source=database,
        backup=tmp_path / "legacy-backup.sqlite3",
        destination=tmp_path / "migrated-daemon.sqlite3",
    )
    assert is_ok(migrated), migrated
    assert database.read_bytes() == migration_source_bytes
    assert migrated.value.source_layout_version == 1
    assert migrated.value.destination_layout_version == 2
    assert migrated.value.preserved_outbox_rows == 1
    assert migrated.value.steps == ("preflight", "backup", "dry-run", "migrate", "verify")
    assert migrated.value.restore_path == str(database.resolve())
    assert not list(tmp_path.glob(".migrated-daemon.sqlite3.dry-run-*"))

    migrated_writer = SingleSqliteWriter(tmp_path / "migrated-daemon.sqlite3")
    assert is_ok(migrated_writer.start())
    try:
        store = TaskGraphStateSqliteStore(migrated_writer)
        store.ensure_schema()
        columns = migrated_writer.execute("PRAGMA table_info(task_graph_outbox)")
        predecessor = next(row for row in columns if row[1] == "predecessor_node_id")
        assert predecessor[3] == 0
        marker = migrated_writer.execute(
            "SELECT schema_version FROM task_graph_outbox_schema WHERE singleton = 1"
        )
        assert marker == [(2,)]
        preserved = migrated_writer.execute(
            "SELECT predecessor_node_id, logical_invocation_id, transport_state "
            "FROM task_graph_outbox WHERE graph_run_id = ?",
            ("graph:legacy",),
        )
        assert preserved == [("parent", "inv:legacy", "dispatched")]
    finally:
        migrated_writer.close()


def test_running_daemon_writer_blocks_outbox_migration(tmp_path: Path) -> None:
    database = tmp_path / "daemon" / "daemon.sqlite3"
    database.parent.mkdir()
    writer_lock = database.parent.parent / ".daemon_writer"
    writer_lock.write_text("active", encoding="utf-8")
    source = database.parent.parent / "source.sqlite3"
    connection = sqlite3.connect(source)
    connection.execute(
        "CREATE TABLE task_graph_outbox (graph_run_id TEXT NOT NULL, "
        "successor_node_id TEXT NOT NULL, predecessor_revision INTEGER NOT NULL, "
        "partition_id TEXT NOT NULL, outbox_id TEXT NOT NULL, "
        "predecessor_node_id TEXT NOT NULL, logical_invocation_id TEXT NOT NULL, "
        "target TEXT NOT NULL, envelope_hash TEXT NOT NULL, transport_state TEXT NOT NULL, "
        "acceptance_state TEXT, effect_state TEXT, receiver_acceptance_id TEXT, "
        "PRIMARY KEY (graph_run_id, successor_node_id, predecessor_revision, partition_id))"
    )
    connection.commit()
    connection.close()
    refused = migrate_task_graph_outbox(
        source=source,
        backup=tmp_path / "backup.sqlite3",
        destination=tmp_path / "destination.sqlite3",
    )
    assert not is_ok(refused)
    assert not (tmp_path / "backup.sqlite3").exists()
    assert not (tmp_path / "destination.sqlite3").exists()


def test_outbox_migration_escapes_uri_metacharacters_and_preserves_all_tables(
    tmp_path: Path,
) -> None:
    database = tmp_path / "source#part?one.sqlite3"
    connection = sqlite3.connect(database)
    connection.executescript(
        "CREATE TABLE task_graph_outbox ("
        "graph_run_id TEXT NOT NULL, successor_node_id TEXT NOT NULL, "
        "predecessor_revision INTEGER NOT NULL, partition_id TEXT NOT NULL, "
        "outbox_id TEXT NOT NULL, predecessor_node_id TEXT NOT NULL, "
        "logical_invocation_id TEXT NOT NULL, target TEXT NOT NULL, "
        "envelope_hash TEXT NOT NULL, transport_state TEXT NOT NULL, "
        "acceptance_state TEXT, effect_state TEXT, receiver_acceptance_id TEXT, "
        "PRIMARY KEY (graph_run_id, successor_node_id, predecessor_revision, partition_id));"
        "CREATE UNIQUE INDEX task_graph_outbox_logical "
        "ON task_graph_outbox (logical_invocation_id);"
        "CREATE TABLE retained_extension (key TEXT PRIMARY KEY, value TEXT NOT NULL);"
        "INSERT INTO retained_extension VALUES ('one', 'preserved');"
    )
    connection.close()
    backup = tmp_path / "backup.sqlite3"
    destination = tmp_path / "destination.sqlite3"
    result = migrate_task_graph_outbox(source=database, backup=backup, destination=destination)
    assert is_ok(result), result
    assert not (tmp_path / "source").exists()
    for path in (backup, destination):
        migrated = sqlite3.connect(path)
        try:
            assert migrated.execute("SELECT key, value FROM retained_extension").fetchall() == [
                ("one", "preserved")
            ]
        finally:
            migrated.close()


def test_outbox_migration_refuses_live_wal_source(tmp_path: Path) -> None:
    database = tmp_path / "wal-source.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute(
        "CREATE TABLE task_graph_outbox (graph_run_id TEXT NOT NULL, "
        "successor_node_id TEXT NOT NULL, predecessor_revision INTEGER NOT NULL, "
        "partition_id TEXT NOT NULL, outbox_id TEXT NOT NULL, "
        "predecessor_node_id TEXT NOT NULL, logical_invocation_id TEXT NOT NULL, "
        "target TEXT NOT NULL, envelope_hash TEXT NOT NULL, transport_state TEXT NOT NULL, "
        "acceptance_state TEXT, effect_state TEXT, receiver_acceptance_id TEXT, "
        "PRIMARY KEY (graph_run_id, successor_node_id, predecessor_revision, partition_id))"
    )
    connection.execute(
        "CREATE UNIQUE INDEX task_graph_outbox_logical ON task_graph_outbox (logical_invocation_id)"
    )
    connection.commit()
    connection.execute(
        "INSERT INTO task_graph_outbox VALUES "
        "('g','n',0,'p','o','parent','i','{}','fp','dispatched',NULL,NULL,NULL)"
    )
    connection.commit()
    assert Path(f"{database}-wal").exists()
    result = migrate_task_graph_outbox(
        source=database,
        backup=tmp_path / "wal-backup.sqlite3",
        destination=tmp_path / "wal-destination.sqlite3",
    )
    assert is_refusal(result)
    assert not (tmp_path / "wal-backup.sqlite3").exists()
    connection.close()


def test_outbox_migration_rechecks_wal_snapshot_after_backup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = tmp_path / "race-source.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.executescript(
        "CREATE TABLE task_graph_outbox ("
        "graph_run_id TEXT NOT NULL, successor_node_id TEXT NOT NULL, "
        "predecessor_revision INTEGER NOT NULL, partition_id TEXT NOT NULL, "
        "outbox_id TEXT NOT NULL, predecessor_node_id TEXT NOT NULL, "
        "logical_invocation_id TEXT NOT NULL, target TEXT NOT NULL, "
        "envelope_hash TEXT NOT NULL, transport_state TEXT NOT NULL, "
        "acceptance_state TEXT, effect_state TEXT, receiver_acceptance_id TEXT, "
        "PRIMARY KEY (graph_run_id, successor_node_id, predecessor_revision, partition_id));"
        "CREATE UNIQUE INDEX task_graph_outbox_logical "
        "ON task_graph_outbox (logical_invocation_id);"
        "CREATE TABLE retained_extension (value TEXT NOT NULL);"
        "INSERT INTO retained_extension VALUES ('before');"
    )
    connection.close()
    assert not Path(f"{database}-wal").exists()

    original_copy = task_graph_outbox_migration._copy_database
    writer_connections: list[sqlite3.Connection] = []

    def copy_then_write(source: Path, destination: Path) -> None:
        original_copy(source, destination)
        if source == database:
            late_writer = sqlite3.connect(database)
            writer_connections.append(late_writer)
            late_writer.execute("INSERT INTO retained_extension VALUES ('during-migration')")
            late_writer.commit()

    monkeypatch.setattr(task_graph_outbox_migration, "_copy_database", copy_then_write)
    backup = tmp_path / "race-backup.sqlite3"
    destination = tmp_path / "race-destination.sqlite3"
    try:
        result = migrate_task_graph_outbox(source=database, backup=backup, destination=destination)
        assert is_refusal(result)
        assert backup.exists()
        assert not destination.exists()
        saved = sqlite3.connect(backup)
        try:
            assert saved.execute("SELECT value FROM retained_extension").fetchall() == [("before",)]
        finally:
            saved.close()
        current = sqlite3.connect(database)
        try:
            assert current.execute("SELECT value FROM retained_extension").fetchall() == [
                ("before",),
                ("during-migration",),
            ]
        finally:
            current.close()
    finally:
        for late_writer in writer_connections:
            late_writer.close()


def test_outbox_migration_rechecks_schema_objects_written_to_wal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = tmp_path / "schema-race-source.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.executescript(
        "CREATE TABLE task_graph_outbox ("
        "graph_run_id TEXT NOT NULL, successor_node_id TEXT NOT NULL, "
        "predecessor_revision INTEGER NOT NULL, partition_id TEXT NOT NULL, "
        "outbox_id TEXT NOT NULL, predecessor_node_id TEXT NOT NULL, "
        "logical_invocation_id TEXT NOT NULL, target TEXT NOT NULL, "
        "envelope_hash TEXT NOT NULL, transport_state TEXT NOT NULL, "
        "acceptance_state TEXT, effect_state TEXT, receiver_acceptance_id TEXT, "
        "PRIMARY KEY (graph_run_id, successor_node_id, predecessor_revision, partition_id));"
        "CREATE UNIQUE INDEX task_graph_outbox_logical "
        "ON task_graph_outbox (logical_invocation_id);"
        "CREATE TABLE retained_extension (value TEXT NOT NULL);"
    )
    connection.close()
    assert not Path(f"{database}-wal").exists()

    original_copy = task_graph_outbox_migration._copy_database
    writer_connections: list[sqlite3.Connection] = []

    def copy_then_create_index(source: Path, destination: Path) -> None:
        original_copy(source, destination)
        if source == database:
            late_writer = sqlite3.connect(database)
            writer_connections.append(late_writer)
            late_writer.execute("CREATE INDEX preserved_note_idx ON retained_extension(value)")
            late_writer.commit()

    monkeypatch.setattr(task_graph_outbox_migration, "_copy_database", copy_then_create_index)
    backup = tmp_path / "schema-race-backup.sqlite3"
    destination = tmp_path / "schema-race-destination.sqlite3"
    try:
        result = migrate_task_graph_outbox(source=database, backup=backup, destination=destination)
        assert is_refusal(result)
        assert backup.exists()
        assert not destination.exists()
        saved = sqlite3.connect(backup)
        try:
            assert (
                saved.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' "
                    "AND name='preserved_note_idx'"
                ).fetchall()
                == []
            )
        finally:
            saved.close()
        current = sqlite3.connect(database)
        try:
            assert current.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='preserved_note_idx'"
            ).fetchall() == [("preserved_note_idx",)]
        finally:
            current.close()
    finally:
        for late_writer in writer_connections:
            late_writer.close()


def test_crash_inside_transaction_rolls_back_terminal_and_outbox(tmp_path: Path) -> None:
    _owner, compiled = _compile(slug="crash")
    process = _compose(tmp_path, boot="boot-57-2-crash")
    try:
        dispatcher = _dispatcher(process)
        dispatcher.materialize(compiled.task_graph, mission=compiled.mission)
        prepare = compiled.task_graph.ready_tasks()[0]
        decision = dispatcher.dispatch_task(
            task_id=prepare.id,
            holder_agent_id="agent-worker-1",
            environment_kind=ExecutionEnvironmentKind.DOCKER,
        )
        assert is_ok(decision)
        armed = process.task_graphs.arm_completion_crash("eligibility")
        assert is_ok(armed)
        applied = dispatcher.apply_job_handle_evidence(
            JobHandleEvidence(
                job_id="job-crash",
                task_id=prepare.id,
                state=JobHandleState.DONE,
            )
        )
        assert is_refusal(applied)
        assert applied.context.get("rolled_back") is True
        sql_state = process.sqlite.execute(
            "SELECT payload FROM task_graph_state WHERE graph_id = ?",
            (compiled.task_graph.id,),
        )
        assert sql_state
        payload = json.loads(str(sql_state[0][0]))
        tasks = cast("list[dict[str, object]]", payload["tasks"])
        prepare_row = next(task for task in tasks if task["id"] == prepare.id)
        survey_row = next(task for task in tasks if task["node_id"] == "survey")
        assert prepare_row["state"] == "running"
        assert survey_row["state"] == "pending"
        outbox = process.sqlite.execute(
            "SELECT COUNT(*) FROM task_graph_outbox WHERE graph_run_id = ?",
            (compiled.task_graph.id,),
        )
        assert outbox == [(0,)]
        eligibility = process.sqlite.execute(
            "SELECT COUNT(*) FROM task_graph_successor_eligibility WHERE graph_run_id = ?",
            (compiled.task_graph.id,),
        )
        assert eligibility == [(0,)]
    finally:
        process.close()


def test_restart_replays_unacked_and_receiver_dedupes(tmp_path: Path) -> None:
    _owner, compiled = _compile(slug="replay")
    process = _compose(tmp_path, boot="boot-57-2-replay-a")
    try:
        _dispatcher_obj, _prepare_id, survey_id = _complete_predecessor(process, compiled)
        replayable = process.task_graphs.replayable_rows(compiled.task_graph.id)
        assert len(replayable) == 1
        assert replayable[0].transport_state is OutboxTransportState.PENDING
        _ = _dispatcher_obj
        _ = survey_id
    finally:
        process.close()

    restarted = _compose(tmp_path, boot="boot-57-2-replay-b")
    try:
        restored = restarted.task_graphs.get(compiled.task_graph.id)
        assert is_ok(restored)
        survey = restored.value.task_for_node("survey")
        assert survey is not None
        assert survey.state is TaskMissionState.READY
        pending = restarted.task_graphs.replayable_rows(compiled.task_graph.id)
        assert len(pending) == 1
        logical_id = pending[0].logical_invocation_id
        acked = restarted.task_graphs.ack_dispatch(logical_invocation_id=logical_id)
        assert is_ok(acked)
        dispatched = acked.value[0]
        assert dispatched.transport_state is OutboxTransportState.DISPATCHED
        assert dispatched.acceptance_state is None
        still_replayable = restarted.task_graphs.replayable_rows(compiled.task_graph.id)
        assert len(still_replayable) == 1
        first = restarted.task_graphs.accept_logical(
            logical_id, result={"node": "survey", "attempt": 1}
        )
        assert is_ok(first)
        assert first.value.replayed is False
        assert first.value.receiver_acceptance_id.startswith("recv:")
        accepted_row = restarted.task_graphs.outbox_rows(compiled.task_graph.id)[0]
        assert accepted_row.acceptance_state is OutboxAcceptanceState.ACCEPTED
        assert accepted_row.effect_state is None
        assert OUTBOX_PROVES_EXACTLY_ONCE_EFFECT is False
        assert accepted_row.to_payload()["outbox_proves_exactly_once_effect"] is False
        second = restarted.task_graphs.accept_logical(
            logical_id, result={"node": "survey", "attempt": 2}
        )
        assert is_ok(second)
        assert second.value.replayed is True
        assert second.value.result == {"node": "survey", "attempt": 1}
        assert second.value.receiver_acceptance_id == first.value.receiver_acceptance_id
        assert restarted.task_graphs.replayable_rows(compiled.task_graph.id) == ()
        effected = restarted.task_graphs.mark_effected(logical_id)
        assert is_ok(effected)
        assert effected.value.effect_state is OutboxEffectState.EFFECTED
        assert effected.value.acceptance_state is OutboxAcceptanceState.ACCEPTED
        assert effected.value.transport_state is OutboxTransportState.DISPATCHED
    finally:
        restarted.close()


def test_dispatch_acks_outbox_transport_not_acceptance(tmp_path: Path) -> None:
    _owner, compiled = _compile(slug="ack")
    process = _compose(tmp_path, boot="boot-57-2-ack")
    try:
        dispatcher, _prepare_id, survey_id = _complete_predecessor(process, compiled)
        decision = dispatcher.dispatch_task(
            task_id=survey_id,
            holder_agent_id="agent-worker-2",
            environment_kind=ExecutionEnvironmentKind.DOCKER,
        )
        assert is_ok(decision)
        rows = process.task_graphs.outbox_rows(compiled.task_graph.id)
        assert len(rows) == 1
        assert rows[0].transport_state is OutboxTransportState.DISPATCHED
        assert rows[0].acceptance_state is None
        assert rows[0].effect_state is None
    finally:
        process.close()


def test_failed_predecessor_does_not_ready_successor(tmp_path: Path) -> None:
    _owner, compiled = _compile(slug="fail")
    process = _compose(tmp_path, boot="boot-57-2-fail")
    try:
        dispatcher = _dispatcher(process)
        dispatcher.materialize(compiled.task_graph, mission=compiled.mission)
        prepare = compiled.task_graph.ready_tasks()[0]
        assert is_ok(
            dispatcher.dispatch_task(
                task_id=prepare.id,
                holder_agent_id="agent-worker-1",
                environment_kind=ExecutionEnvironmentKind.DOCKER,
            )
        )
        applied = dispatcher.apply_job_handle_evidence(
            JobHandleEvidence(
                job_id="job-fail",
                task_id=prepare.id,
                state=JobHandleState.FAILED,
            )
        )
        assert is_ok(applied)
        graph = dispatcher.store.get(compiled.task_graph.id)
        assert graph is not None
        survey = graph.task_for_node("survey")
        assert survey is not None
        assert survey.state is TaskMissionState.PENDING
        assert process.task_graphs.outbox_rows(compiled.task_graph.id) == ()
    finally:
        process.close()


def test_join_waits_for_all_predecessors(tmp_path: Path) -> None:
    owner = _quant(slug="join")
    catalog = GraphTemplateCatalog()
    template = GraphTemplate(
        qualified_id="research-corpus:join",
        version="1",
        nodes=(
            {"id": "left", "kind": "task", "intent": "left"},
            {"id": "right", "kind": "task", "intent": "right"},
            {"id": "join", "kind": "task", "intent": "join"},
        ),
        edges=(
            _edge("left", "join"),
            _edge("right", "join"),
        ),
    )
    assert is_ok(catalog.register(template))
    compiler = MissionCompiler(
        templates=catalog,
        known_quant_actor_ids={owner.actor_id.value},
    )
    compiled = compiler.compile(
        CompileRequest(
            goal=Goal(text="join after both"),
            owner=owner,
            graph_template_ref="research-corpus:join",
        )
    )
    assert is_ok(compiled)
    process = _compose(tmp_path, boot="boot-57-2-join")
    try:
        dispatcher = _dispatcher(process)
        graph = compiled.value.task_graph
        dispatcher.materialize(graph, mission=compiled.value.mission)
        left = graph.task_for_node("left")
        right = graph.task_for_node("right")
        assert left is not None and right is not None
        assert is_ok(
            dispatcher.apply_proposed_transition(
                ProposedTransition(
                    target_kind="task",
                    target_id=right.id,
                    from_state=TaskMissionState.PENDING,
                    to_state=TaskMissionState.READY,
                    proposed_by_agent_id="agent-director",
                )
            )
        )
        assert is_ok(
            dispatcher.dispatch_task(
                task_id=left.id,
                holder_agent_id="agent-l",
                environment_kind=ExecutionEnvironmentKind.DOCKER,
            )
        )
        assert is_ok(
            dispatcher.apply_job_handle_evidence(
                JobHandleEvidence(job_id="job-l", task_id=left.id, state=JobHandleState.DONE)
            )
        )
        after_left = dispatcher.store.get(graph.id)
        assert after_left is not None
        join_task = after_left.task_for_node("join")
        assert join_task is not None
        assert join_task.state is TaskMissionState.PENDING
        assert process.task_graphs.outbox_rows(graph.id) == ()
        assert is_ok(
            dispatcher.dispatch_task(
                task_id=right.id,
                holder_agent_id="agent-r",
                environment_kind=ExecutionEnvironmentKind.DOCKER,
            )
        )
        assert is_ok(
            dispatcher.apply_job_handle_evidence(
                JobHandleEvidence(job_id="job-r", task_id=right.id, state=JobHandleState.DONE)
            )
        )
        after_right = dispatcher.store.get(graph.id)
        assert after_right is not None
        join_ready = after_right.task_for_node("join")
        assert join_ready is not None
        assert join_ready.state is TaskMissionState.READY
        rows = process.task_graphs.outbox_rows(graph.id)
        assert len(rows) == 1
        assert rows[0].successor_node_id == "join"
        assert rows[0].predecessor_node_id == "right"
    finally:
        process.close()


def test_remote_worker_outbox_is_a_different_noun() -> None:
    assert TASK_GRAPH_OUTBOX_NOUN != REMOTE_WORKER_OUTBOX_NOUN
    assert OUTBOXES_MERGED is False
    refused = refuse_merge_remote_worker_outbox(given=RemoteOutbox.__name__)
    assert is_refusal(refused)
    assert refused.context["merged"] is False
    assert refused.context["task_graph_outbox"] == TASK_GRAPH_OUTBOX_NOUN
    assert refused.context["remote_worker_outbox"] == REMOTE_WORKER_OUTBOX_NOUN
    assert RemoteOutbox.__name__ == "RemoteOutbox"


def test_outbox_tables_are_task_graph_state_not_a_new_class(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="boot-57-2-tables")
    try:
        names = process.sqlite_table_names()
        assert TASK_GRAPH_OUTBOX_TABLE in names
        assert TASK_GRAPH_ELIGIBILITY_TABLE in names
        assert TASK_GRAPH_RECEIVER_TABLE in names
        tables = process.snapshot()["task_graph_state_tables"]
        assert isinstance(tables, list)
        assert TASK_GRAPH_OUTBOX_TABLE in cast("list[str]", tables)
    finally:
        process.close()


def test_example_and_source_keep_distinct_nouns() -> None:
    tree = ast.parse((_SRC / "outbox.py").read_text(encoding="utf-8"))
    assigned: dict[str, object] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.value is not None
            and isinstance(node.value, (ast.Constant, ast.Tuple, ast.List))
        ):
            assigned[node.target.id] = ast.literal_eval(node.value)
        elif (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, (ast.Constant, ast.Tuple, ast.List))
        ):
            assigned[node.targets[0].id] = ast.literal_eval(node.value)
    assert assigned.get("TASK_GRAPH_OUTBOX_NOUN") == "task_graph_outbox"
    assert assigned.get("REMOTE_WORKER_OUTBOX_NOUN") == "remote_worker_outbox"
    assert assigned.get("OUTBOXES_MERGED") is False
    assert assigned.get("OUTBOX_PROVES_EXACTLY_ONCE_EFFECT") is False
    namespace = runpy.run_path(str(_EXAMPLE))
    assert callable(namespace["main"])
    namespace["main"]()
