"""Backtesting Service — analysis-backtest plugin daemon half (CT-47; FR-Q55).

Agent → QMA backtest tool → this service → ``qmb`` CLI/MCP door → QMB.
Places exactly one ``qmb`` job per ExecutionEnvironment. Holds no scheduling
authority, no parallelism, and no durable backtest state. QMB keeps those.
The door is a runtime interaction: this module never imports the ``qmb``
package and never places the compute leg through the Compute Router.
Production placement is ``CliQmbDoorTransport``. ``RecordingQmbDoorTransport``
records without spawning and is not a working integration.
"""

from __future__ import annotations

import json
import subprocess
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Literal, cast

from qma.core.control.procedures import (
    PROCEDURE_LINEAGE_EXTRA_KEYS,
    admit_procedure_successor_change,
    admit_procedure_successor_edge,
    classify_procedure_step,
    procedure_step_changes_resolved_config,
    procedure_step_resolved_config_ref,
)
from qma.core.ontology import ActorId
from qma.core.ports.cancel_authority import (
    COORDINATED_CANCEL_AUTHORITY,
    RECORDING_DOOR_MAPS_CANCEL_TO_QMB_ABORT,
    authorize_qmb_ledger_aborted_writer,
    is_unauthorized_cancel_writer,
    refuse_unauthorized_cancel,
)
from qma.core.ports.experiments import (
    ANALYSIS_PUBLISHED_KIND,
    COORDINATED_CONTINUITY_KIND,
    EXPERIMENT_CHANGE_RESOLVED_CONFIG,
    EXPERIMENT_LEDGER_WORKBENCH_LANE,
    EXPERIMENT_LINEAGE_EDGE_TYPE,
    QMB_LEDGER_WORKBENCH_LANE,
    coordinated_run_labels,
    refuse_caller_declared_lane_fields,
)
from qma.core.ports.jobs import JobArtifact, JobHandle
from qma.core.ports.qmb import (
    ANALYSIS_BACKTEST_PLUGIN_ID,
    QMB_ABORTED_LEDGER_STATE,
    QMB_BACKTEST_TOOL_ID,
    QMB_BACKTEST_TOOL_LOCAL_ID,
    QMB_CLI_PROGRAM,
    QMB_OCCUPANCY_QUERY,
    QMB_OCCUPANCY_RUN,
    QMB_OPENS_DAEMON_SQLITE,
    QMB_OWNED_CONCERNS,
    QMB_PROCESS_PER_RUN_CHILD,
    QMB_ROUTE,
    QMB_WORLD_REPLAY,
    QmbAbortReceipt,
    QmbBacktestRequest,
    QmbDoorInvocation,
    QmbDoorKind,
    QmbDoorReceipt,
    QmbDoorTransport,
    admit_qmb_job,
    build_qmb_door_invocation,
    build_qmb_query_invocation,
    classify_qmb_door_occupancy,
    environment_kind_from_ref,
    occupancy_from_invocation,
    parse_qmb_backtest_request,
    qmb_backtest_tool_record,
    qmb_opens_daemon_sqlite,
    refuse_qmb_import_edge,
    refuse_qmb_owned_concern,
    refuse_query_ct32_or_successor,
    release_qmb_job,
)
from qma.core.ports.tools import ToolKind, ToolRecord
from qma.core.refusals import NoEnvironment
from qma.core.vocabulary.enums import ArtifactCompleteness, JobHandleState, PrincipalClass
from qma.daemon.backtest.cli import CliQmbDoorTransport
from qma.daemon.backtest.expected import (
    read_expected_context,
    read_verified_context,
    write_expected_context,
    write_verified_context,
)
from qma.daemon.envs.jobs import JobHandleService
from qma.daemon.envs.registry import ExecutionEnvironmentRegistry
from qma.daemon.experiments.service import (
    ExperimentSpecService,
    PublishedProjection,
    RegisteredExperiment,
)
from qma.daemon.plugins.context import DaemonPluginContext, PluginContextError
from qma.daemon.sessions.product_session import ProductSessionService
from qma.daemon.taskgraph.records import DispatchLease
from qma.daemon.tools.registry import ToolRegistry
from qmf.core import Ok, Result, World, is_ok, is_refusal
from qmf.data.store import AppendStore, EvidenceStore
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = [
    "BacktestingService",
    "CliQmbDoorTransport",
    "ProcedureStepPlacement",
    "QmbPlacement",
    "QmbQueryPlacement",
    "RecordingQmbDoorTransport",
]


def _job_id_for(request: QmbBacktestRequest) -> str:
    return f"qmb:{request.occupancy_key}:{request.task_id}"


def _invocation_from_payload(value: object) -> Result[QmbDoorInvocation]:
    if not isinstance(value, Mapping):
        return invalid_input("invocation", "durable expected context includes an invocation")
    row = cast(Mapping[str, object], value)
    if set(row) != {"program", "kind", "argv", "payload", "import_edge"}:
        return invalid_input("invocation", "stored invocation has the exact QMB wire fields")
    program, kind, argv, payload, import_edge = (
        row[key] for key in ("program", "kind", "argv", "payload", "import_edge")
    )
    if program != QMB_CLI_PROGRAM or not isinstance(kind, str):
        return invalid_input("invocation", "stored invocation is a trusted QMB CLI call")
    if not isinstance(argv, (list, tuple)):
        return invalid_input("invocation.argv", "stored CLI arguments are a sequence")
    argv_values = cast(Sequence[object], argv)
    if any(not isinstance(item, str) for item in argv_values):
        return invalid_input("invocation.argv", "stored CLI arguments are strings")
    if not isinstance(payload, Mapping) or type(import_edge) is not bool or import_edge:
        return invalid_input("invocation", "stored invocation is a trusted QMB CLI call")
    try:
        door_kind = QmbDoorKind(kind)
    except ValueError:
        return invalid_input("invocation.kind", "stored invocation uses a supported door")
    return Ok(
        QmbDoorInvocation(
            program=QMB_CLI_PROGRAM,
            kind=door_kind,
            argv=tuple(cast(str, item) for item in argv_values),
            payload=cast(Mapping[str, object], payload),
            import_edge=False,
        )
    )


def _projection_view_from_stdout(
    stdout: str,
    extra: Mapping[str, object] | None,
) -> Result[dict[str, object]]:
    raw = stdout.strip()
    if not raw and extra is not None:
        candidate = extra.get("view")
        if isinstance(candidate, Mapping):
            mapping = cast("Mapping[object, object]", candidate)
            raw = json.dumps(
                {str(key): value for key, value in mapping.items()},
                separators=(",", ":"),
            )
    if not raw:
        return invalid_input(
            "stdout",
            "coordinated analysis.project waits for canonical saved-view JSON (FR-W24; Story 35.1)",
        )
    try:
        parsed_obj: object = json.loads(raw)
    except json.JSONDecodeError as exc:
        return invalid_input("stdout", "projection JSON is not parseable", error=str(exc))
    if not isinstance(parsed_obj, dict):
        return invalid_input("stdout", "projection JSON is an object")
    mapping = cast("dict[object, object]", parsed_obj)
    view: dict[str, object] = {str(key): value for key, value in mapping.items()}
    if view.get("method") != "projection":
        return invalid_input(
            "method",
            "a projection saved view has method=projection (FR-W24; DEC-0273)",
            given=repr(view.get("method")),
        )
    return Ok(view)


@dataclass
class RecordingQmbDoorTransport:
    """Non-production recorder. Does not spawn ``qmb`` and is not the working door.

    Tests that claim the QMA→QMB door works must spawn ``qmb`` or the documented
    CLI test double via ``CliQmbDoorTransport``. ``JobHandle.cancel`` still
    enters ``cancelled`` on the QMA handle. This recorder does not map that
    cancel onto a live ``qmb`` abort — ``CliQmbDoorTransport`` does.
    """

    production: Literal[False] = False
    spawns_qmb_process: Literal[False] = False
    maps_cancel_to_qmb_abort: Literal[False] = RECORDING_DOOR_MAPS_CANCEL_TO_QMB_ABORT
    _invocations: list[QmbDoorInvocation] = field(default_factory=list[QmbDoorInvocation])
    _abort_invocations: list[str] = field(default_factory=list[str])

    @property
    def invocations(self) -> tuple[QmbDoorInvocation, ...]:
        return tuple(self._invocations)

    @property
    def abort_invocations(self) -> tuple[str, ...]:
        return tuple(self._abort_invocations)

    def abort(self, job_id: str) -> Result[QmbAbortReceipt]:
        """Recording door does not map cancel onto a live qmb abort."""
        return policy_rejection(
            "qmb_abort",
            "mapping JobHandle.cancel onto a live qmb abort is the production "
            "CLI door, not RecordingQmbDoorTransport (AR-W04; FR-W08; FR-W36)",
            job_id=job_id,
            transport="RecordingQmbDoorTransport",
            maps_cancel_to_qmb_abort=self.maps_cancel_to_qmb_abort,
        )

    def submit(self, invocation: QmbDoorInvocation) -> Result[QmbDoorReceipt]:
        if invocation.import_edge or invocation.program != QMB_CLI_PROGRAM:
            return refuse_qmb_import_edge(given=invocation.program)
        payload = dict(invocation.payload)
        if payload.get("import_edge") is True:
            return refuse_qmb_import_edge()
        job_id = payload.get("job_id")
        environment_ref = payload.get("environment_ref")
        occupancy_key = payload.get("occupancy_key")
        if not isinstance(job_id, str) or not job_id:
            return invalid_input("job_id", "QMB door invocation requires a job id")
        if not isinstance(environment_ref, str) or not environment_ref:
            return invalid_input("environment_ref", "QMB door invocation requires environment_ref")
        if not isinstance(occupancy_key, str) or not occupancy_key:
            occupancy_key = environment_ref
        self._invocations.append(invocation)
        classified = occupancy_from_invocation(invocation)
        stdout = ""
        if classified.occupancy == QMB_OCCUPANCY_QUERY:
            stdout = str(payload.get("stdout", ""))
        return Ok(
            QmbDoorReceipt(
                job_id=job_id,
                environment_ref=environment_ref,
                occupancy_key=occupancy_key,
                door=invocation.kind,
                program=invocation.program,
                argv=invocation.argv,
                world=QMB_WORLD_REPLAY,
                route=QMB_ROUTE,
                import_edge=False,
                occupancy=classified.occupancy,
                mints_ct32=classified.mints_ct32,
                mints_experiment_spec=False,
                stdout=stdout,
            )
        )


@dataclass(frozen=True, slots=True)
class QmbPlacement:
    """One placed ``qmb`` job: QMA JobHandle plus the runtime door receipt."""

    handle: JobHandle
    request: QmbBacktestRequest
    invocation: QmbDoorInvocation
    receipt: QmbDoorReceipt
    tool_id: str = QMB_BACKTEST_TOOL_ID
    plugin_id: str = ANALYSIS_BACKTEST_PLUGIN_ID
    route: tuple[str, ...] = QMB_ROUTE
    qmb_ledger_workbench_lane: str = QMB_LEDGER_WORKBENCH_LANE
    experiment_ledger_workbench_lane: str = EXPERIMENT_LEDGER_WORKBENCH_LANE

    def to_payload(self) -> Mapping[str, object]:
        payload: dict[str, object] = {
            "job_id": self.handle.job_id,
            "state": self.handle.state.value,
            "tool_id": self.tool_id,
            "plugin_id": self.plugin_id,
            "route": list(self.route),
            "occupancy_key": self.request.occupancy_key,
            "environment_ref": self.request.environment_ref,
            "world": self.request.world,
            "door": self.request.door.value,
            "program": self.invocation.program,
            "argv": list(self.invocation.argv),
            "import_edge": False,
            "compute_router_used": False,
            "qma_re_specifies": False,
            "qmb_ledger_workbench_lane": self.qmb_ledger_workbench_lane,
            "experiment_ledger_workbench_lane": self.experiment_ledger_workbench_lane,
            "request": dict(self.request.to_payload()),
            "receipt": dict(self.receipt.to_payload()),
            "labels": dict(coordinated_run_labels()),
            "occupancy": QMB_OCCUPANCY_RUN,
            "children_are_qma_jobs": False,
        }
        return MappingProxyType(payload)


@dataclass(frozen=True, slots=True)
class QmbQueryPlacement:
    """One placed QMB query: JobHandle for progress, no environment occupancy."""

    handle: JobHandle
    invocation: QmbDoorInvocation
    receipt: QmbDoorReceipt
    command: str
    occupancy: str = QMB_OCCUPANCY_QUERY
    mints_ct32: Literal[False] = False
    mints_experiment_spec: Literal[False] = False
    published: PublishedProjection | None = None
    tool_id: str = QMB_BACKTEST_TOOL_ID
    plugin_id: str = ANALYSIS_BACKTEST_PLUGIN_ID
    route: tuple[str, ...] = QMB_ROUTE

    def to_payload(self) -> Mapping[str, object]:
        payload: dict[str, object] = {
            "job_id": self.handle.job_id,
            "state": self.handle.state.value,
            "command": self.command,
            "occupancy": self.occupancy,
            "mints_ct32": self.mints_ct32,
            "mints_experiment_spec": self.mints_experiment_spec,
            "consumes_environment": False,
            "children_are_qma_jobs": False,
            "opens_daemon_sqlite": QMB_OPENS_DAEMON_SQLITE,
            "tool_id": self.tool_id,
            "plugin_id": self.plugin_id,
            "route": list(self.route),
            "program": self.invocation.program,
            "argv": list(self.invocation.argv),
            "stdout": self.receipt.stdout,
        }
        if self.published is not None:
            payload["published"] = dict(self.published.to_payload())
        return MappingProxyType(payload)


def _procedure_extra_without_lineage(
    extra: Mapping[str, object] | None,
) -> Mapping[str, object] | None:
    if extra is None:
        return None
    cleaned = {
        key: value for key, value in extra.items() if key not in PROCEDURE_LINEAGE_EXTRA_KEYS
    }
    return MappingProxyType(cleaned) if cleaned else None


@dataclass(frozen=True, slots=True)
class ProcedureStepPlacement:
    """One procedure door step placed through the Story 36.2 QMB door.

    Run-steps occupy the environment. A door step that changes
    resolved-config mints an ExperimentSpec successor via
    ``create_successor`` plus CT-07 ``branches-from``. Query-steps call
    Epic 35/33 door queries: no occupancy, no CT-32, no successor.
    """

    occupancy: str
    command: str
    mints_ct32: bool
    mints_experiment_spec: bool = False
    consumes_environment: bool = False
    run: QmbPlacement | None = None
    query: QmbQueryPlacement | None = None
    successor: RegisteredExperiment | None = None
    experiment_spec_fp1: str | None = None
    continuity: str = COORDINATED_CONTINUITY_KIND

    def to_payload(self) -> Mapping[str, object]:
        payload: dict[str, object] = {
            "occupancy": self.occupancy,
            "command": self.command,
            "mints_ct32": self.mints_ct32,
            "mints_experiment_spec": self.mints_experiment_spec,
            "consumes_environment": self.consumes_environment,
            "continuity": self.continuity,
            "is_experiment_spec": False,
        }
        if self.experiment_spec_fp1 is not None:
            payload["experiment_spec_fp1"] = self.experiment_spec_fp1
        if self.successor is not None:
            payload["successor"] = dict(self.successor.to_payload())
            if self.successor.lineage_edge is not None:
                payload["lineage_edge_type"] = self.successor.lineage_edge.edge_type.value
        if self.run is not None:
            payload["run"] = dict(self.run.to_payload())
        if self.query is not None:
            payload["query"] = dict(self.query.to_payload())
        return MappingProxyType(payload)


class BacktestingService:
    """``analysis-backtest`` daemon half: one Tool Registry entry, one ``qmb`` door."""

    def __init__(
        self,
        *,
        tools: ToolRegistry | None = None,
        jobs: JobHandleService | None = None,
        environments: ExecutionEnvironmentRegistry | None = None,
        transport: QmbDoorTransport | None = None,
        experiments: ExperimentSpecService | None = None,
        artifact_root: Path | str | None = None,
        artifact_store: AppendStore | None = None,
    ) -> None:
        self._jobs = jobs if jobs is not None else JobHandleService()
        self._tools = tools if tools is not None else ToolRegistry()
        self._environments = (
            environments if environments is not None else self._jobs.router.environments
        )
        self._transport: QmbDoorTransport = (
            transport if transport is not None else CliQmbDoorTransport()
        )
        self._experiments = experiments
        self._product_sessions: ProductSessionService | None = None
        self._artifact_root = Path(artifact_root) if artifact_root is not None else None
        self._artifact_store = artifact_store
        self._artifact_store_owner: EvidenceStore | None = None
        self._occupancy: dict[str, str] = {}
        self._observers: list[threading.Thread] = []
        self._observer_lock = threading.RLock()
        self._observer_failures: dict[str, object] = {}
        self._expected_terminal_results: dict[str, Mapping[str, object]] = {}
        self._expected_context_hashes: dict[str, str] = {}

    @property
    def plugin_id(self) -> str:
        return ANALYSIS_BACKTEST_PLUGIN_ID

    @property
    def tool_id(self) -> str:
        return QMB_BACKTEST_TOOL_ID

    @property
    def route(self) -> tuple[str, ...]:
        return QMB_ROUTE

    @property
    def tools(self) -> ToolRegistry:
        return self._tools

    @property
    def jobs(self) -> JobHandleService:
        return self._jobs

    @property
    def environments(self) -> ExecutionEnvironmentRegistry:
        return self._environments

    @property
    def transport(self) -> QmbDoorTransport:
        return self._transport

    @property
    def experiments(self) -> ExperimentSpecService | None:
        return self._experiments

    def bind_experiments(self, experiments: ExperimentSpecService) -> None:
        """Attach ExperimentSpec product truth for coordinated placement."""
        self._experiments = experiments

    def bind_product_sessions(self, sessions: ProductSessionService) -> None:
        """Attach the durable ProductSession projection used to validate UI origin."""
        self._product_sessions = sessions

    def _validated_operator_origin(self, origin: object | None) -> Result[str | None]:
        if origin is None:
            return Ok(None)
        sessions = self._product_sessions
        if sessions is None:
            return invalid_input(
                "originating_product_session_ref",
                "UI-origin placement requires a bound ProductSession projection",
            )
        session = sessions.get(origin)
        if is_refusal(session):
            return invalid_input(
                "originating_product_session_ref",
                "UI-origin placement requires an existing ProductSession",
                given=repr(origin),
            )
        if session.value.principal != "operator":
            return invalid_input(
                "originating_product_session_ref",
                "UI-origin placement requires an operator ProductSession",
                principal=session.value.principal,
            )
        return Ok(session.value.product_session_id)

    @property
    def scheduling_authority(self) -> None:
        return None

    @property
    def parallelism(self) -> None:
        return None

    @property
    def backtest_state(self) -> None:
        return None

    def catalog_backtest_tools(self) -> tuple[ToolRecord, ...]:
        return tuple(tool for tool in self._tools.catalog() if tool.kind is ToolKind.BACKTEST)

    def install(
        self,
        *,
        context: DaemonPluginContext | None = None,
    ) -> Result[ToolRecord]:
        """Register the one analysis-backtest Tool Registry entry."""
        if context is not None and context.plugin_id != ANALYSIS_BACKTEST_PLUGIN_ID:
            return invalid_input(
                "plugin_id",
                "the Backtesting Service is the analysis-backtest plugin's daemon half",
                given=context.plugin_id,
            )
        existing = self._tools.get(QMB_BACKTEST_TOOL_ID)
        if existing is not None:
            if (
                existing.kind is ToolKind.BACKTEST
                and existing.plugin_id == ANALYSIS_BACKTEST_PLUGIN_ID
            ):
                return Ok(existing)
            return invalid_input(
                "tool_id",
                "analysis-backtest already has a non-door tool at the QMB id",
                given=QMB_BACKTEST_TOOL_ID,
            )
        record = qmb_backtest_tool_record()
        registered = self._tools.register_tool(record)
        if is_refusal(registered):
            return registered
        if context is not None:
            snap = context.snapshot()
            already = ("tool", QMB_BACKTEST_TOOL_ID) in snap["multis"]
            if not already:
                try:
                    context.register_tool(
                        QMB_BACKTEST_TOOL_LOCAL_ID,
                        {
                            **dict(record.schema),
                            "name": QMB_BACKTEST_TOOL_LOCAL_ID,
                            "acts": tuple(sorted(record.acts)),
                        },
                    )
                except PluginContextError as exc:
                    return invalid_input("tool", str(exc), plugin_id=ANALYSIS_BACKTEST_PLUGIN_ID)
        return Ok(record)

    def invoke(
        self,
        tool_id: str,
        *,
        owner: ActorId | str,
        task_id: str,
        environment_ref: str,
        experiment_spec_fp1: str,
        evidence_ref: str,
        world: str = QMB_WORLD_REPLAY,
        door: QmbDoorKind | str = QmbDoorKind.CLI,
        extra: Mapping[str, object] | None = None,
        dispatch_lease: DispatchLease | None = None,
        model_deployment_ref: object = None,
        worker_acceptance: Mapping[str, object] | None = None,
        qmb_ledger_ref: object = None,
        ct32_ref: object = None,
        analysis_method: object = None,
        lane: object = None,
        workbench_lane: object = None,
        command: object | None = None,
        originating_product_session_ref: object | None = None,
    ) -> Result[QmbPlacement]:
        """Agent → QMA backtest tool → Backtesting Service."""
        if tool_id != QMB_BACKTEST_TOOL_ID:
            return invalid_input(
                "tool_id",
                "the Backtesting Service exposes one Tool Registry entry "
                f"{QMB_BACKTEST_TOOL_ID} (CT-47; FR-Q55)",
                given=tool_id,
            )
        declared = refuse_caller_declared_lane_fields(
            extra,
            analysis_method=analysis_method,
            lane=lane,
            workbench_lane=workbench_lane,
        )
        if declared is not None:
            return declared
        parsed = parse_qmb_backtest_request(
            owner=owner,
            task_id=task_id,
            environment_ref=environment_ref,
            experiment_spec_fp1=experiment_spec_fp1,
            evidence_ref=evidence_ref,
            world=world,
            door=door,
            tool_id=tool_id,
            extra=extra,
            analysis_method=analysis_method,
            lane=lane,
            workbench_lane=workbench_lane,
        )
        if is_refusal(parsed):
            return parsed
        return self.submit(
            parsed.value,
            dispatch_lease=dispatch_lease,
            model_deployment_ref=model_deployment_ref,
            worker_acceptance=worker_acceptance,
            qmb_ledger_ref=qmb_ledger_ref,
            ct32_ref=ct32_ref,
            command=command,
            originating_product_session_ref=originating_product_session_ref,
        )

    def preflight_registered_run(
        self,
        *,
        owner: ActorId | str,
        task_id: str,
        environment_ref: str,
        experiment_spec_fp1: str,
        evidence_ref: str,
        command: object | None = None,
    ) -> Result[Mapping[str, object] | None]:
        """Resolve the operator runtime before acceptance or job-side effects."""
        if self._experiments is None:
            return Ok(None)
        resolved = self._experiments.resolve(experiment_spec_fp1)
        if is_refusal(resolved):
            return invalid_input(
                "experiment_spec_fp1",
                "runtime preflight requires a registered ExperimentSpec",
                spec_fp1=experiment_spec_fp1,
            )
        if resolved.value.spec.environment_ref != environment_ref:
            return policy_rejection(
                "environment_ref", "runtime preflight matches the registered ExperimentSpec"
            )
        request = parse_qmb_backtest_request(
            owner=owner,
            task_id=task_id,
            environment_ref=environment_ref,
            experiment_spec_fp1=experiment_spec_fp1,
            evidence_ref=evidence_ref,
        )
        if is_refusal(request):
            return request
        existing = self._jobs.handle_for_task(task_id)
        attempt_id = existing.attempt_id if existing is not None else 1
        invocation = build_qmb_door_invocation(
            request.value,
            job_id=_job_id_for(request.value),
            command=command,
            split_manifest_fp1=resolved.value.spec.data_ref,
            attempt_id=attempt_id,
        )
        if is_refusal(invocation):
            return invocation
        preflight = getattr(self._transport, "preflight", None)
        if not callable(preflight):
            return Ok(None)
        checked = cast("Callable[[QmbDoorInvocation], Result[Mapping[str, object]]]", preflight)(
            invocation.value
        )
        if is_refusal(checked):
            return checked
        return Ok(checked.value)

    def submit(
        self,
        request: QmbBacktestRequest,
        *,
        dispatch_lease: DispatchLease | None = None,
        model_deployment_ref: object = None,
        worker_acceptance: Mapping[str, object] | None = None,
        qmb_ledger_ref: object = None,
        ct32_ref: object = None,
        command: object | None = None,
        originating_product_session_ref: object | None = None,
    ) -> Result[QmbPlacement]:
        """Place one ``qmb`` run in an eligible environment through the QMB door."""
        origin = self._validated_operator_origin(originating_product_session_ref)
        if is_refusal(origin):
            return origin
        if command is not None:
            classified = classify_qmb_door_occupancy(command)
            if is_refusal(classified):
                return classified
            if classified.value.occupancy != QMB_OCCUPANCY_RUN:
                return invalid_input(
                    "occupancy",
                    "submit places runs only; queries use place_query (FR-W11; FR-W33)",
                    command=classified.value.command,
                    occupancy=classified.value.occupancy,
                )
        prepared_runtime: Mapping[str, object] | None = None
        split_manifest_fp1: str | None = None
        if self._experiments is not None:
            resolved = self._experiments.resolve(request.experiment_spec_fp1)
            if is_refusal(resolved):
                return invalid_input(
                    "experiment_spec_fp1",
                    "coordinated placement requires a registered ExperimentSpec (FR-W06; DEC-0270)",
                    spec_fp1=request.experiment_spec_fp1,
                )
            split_manifest_fp1 = resolved.value.spec.data_ref
            if dispatch_lease is None:
                return invalid_input(
                    "dispatch_lease",
                    "coordinated QMB placement requires the registered Experiment lease",
                )
            if worker_acceptance is None and (
                dispatch_lease != resolved.value.dispatch_lease
                or model_deployment_ref
                not in {entry.model_deployment_ref for entry in resolved.value.ledger.entries}
            ):
                return policy_rejection(
                    "worker_acceptance",
                    "a changed lease or deployment requires the current receiver acceptance",
                )
            runtime_preflight = self.preflight_registered_run(
                owner=request.owner,
                task_id=request.task_id,
                environment_ref=request.environment_ref,
                experiment_spec_fp1=request.experiment_spec_fp1,
                evidence_ref=request.evidence_ref,
                command=command,
            )
            if is_refusal(runtime_preflight):
                return runtime_preflight
            prepared_runtime = runtime_preflight.value
            if (
                command == "optimize.run"
                and prepared_runtime is None
                and getattr(self._transport, "production", False) is True
            ):
                return invalid_input(
                    "qmb_preflight",
                    "registered optimize.run requires a typed alternative Study preflight",
                )
            validated = self._experiments.validate_coordinated_run(
                spec_fp1=request.experiment_spec_fp1,
                dispatch_lease=dispatch_lease,
                model_deployment_ref=model_deployment_ref,
                evidence_ref=request.evidence_ref,
                worker_acceptance=worker_acceptance,
            )
            if is_refusal(validated):
                return validated
            recorded = self._experiments.record_coordinated_run(
                spec_fp1=request.experiment_spec_fp1,
                dispatch_lease=dispatch_lease,
                model_deployment_ref=model_deployment_ref,
                qmb_ledger_ref=qmb_ledger_ref,
                ct32_ref=ct32_ref,
            )
            if is_refusal(recorded):
                return recorded
        if self._tools.get(QMB_BACKTEST_TOOL_ID) is None:
            installed = self.install()
            if is_refusal(installed):
                return installed
        self._release_terminal()
        kind = request.occupancy_key
        if self._environments.get(kind) is None and self._environments.declaration(kind) is None:
            return NoEnvironment.of(kind=kind, reason="kind_unbound")
        admitted = admit_qmb_job(
            self._occupancy,
            occupancy_key=kind,
            job_id=_job_id_for(request),
            occupancy_class=QMB_OCCUPANCY_RUN,
        )
        if is_refusal(admitted):
            return admitted
        job_id = _job_id_for(request)
        minted = self._jobs.submit(
            owner=request.owner,
            task_id=request.task_id,
            job_id=job_id,
            originating_product_session_ref=origin.value,
        )
        if is_refusal(minted):
            return minted
        if self._jobs.router.lease_for(request.task_id) is not None:
            return policy_rejection(
                "compute_router",
                "the Backtesting Service's compute leg is QMB's own, not QMA's "
                "Compute Router (CT-47; DEC-0316; FR-Q55)",
                task_id=request.task_id,
            )
        invocation = build_qmb_door_invocation(
            request,
            job_id=minted.value.job_id,
            command=command,
            split_manifest_fp1=split_manifest_fp1,
            attempt_id=minted.value.attempt_id,
        )
        if is_refusal(invocation):
            self._occupancy = release_qmb_job(
                admitted.value,
                occupancy_key=kind,
                job_id=job_id,
            )
            return invocation
        expected_result: dict[str, object] = {
            "job_id": minted.value.job_id,
            "attempt_id": minted.value.attempt_id,
            "experiment_spec_fp1": request.experiment_spec_fp1,
            "evidence_ref": request.evidence_ref,
            "split_manifest_fp1": split_manifest_fp1,
            "mints_ct32": (
                prepared_runtime.get("mints_ct32")
                if prepared_runtime is not None
                else invocation.value.payload.get("mints_ct32", True)
            ),
        }
        if prepared_runtime is not None:
            expected_result["operator_descriptor_fp1"] = prepared_runtime.get(
                "operator_descriptor_fp1"
            )
            expected_result["composition_class"] = prepared_runtime.get("composition_class")
            composition = prepared_runtime.get("composition_class")
            if composition == "book":
                expected_result["class"] = "qmb-recorded-replay-result-v1"
            elif composition == "alternative":
                expected_result["class"] = "qmb-alternative-result-v1"
            elif composition == "alternative-study":
                expected_result["class"] = "qmb-operator-alternative-study-result-v1"
                for field_name in (
                    "study_fp1",
                    "operational_fp1",
                    "generation_count",
                    "batch_size",
                ):
                    expected_result[field_name] = prepared_runtime[field_name]
            else:
                return invalid_input(
                    "composition_class", "trusted preflight selects one known QMB composition"
                )
        placed_handle = minted.value
        self._expected_terminal_results[minted.value.job_id] = MappingProxyType(expected_result)
        if prepared_runtime is not None and self._experiments is not None:
            context_store = self._expected_context_store()
            if is_refusal(context_store):
                return context_store
            durable_payload = dict(invocation.value.payload)
            durable_payload["mints_ct32"] = expected_result["mints_ct32"]
            durable_payload["operator_descriptor_fp1"] = expected_result.get(
                "operator_descriptor_fp1"
            )
            saved = write_expected_context(
                store=context_store.value,
                job_id=minted.value.job_id,
                payload={
                    "job_id": minted.value.job_id,
                    "attempt_id": minted.value.attempt_id,
                    "task_id": request.task_id,
                    "owner": request.owner.value,
                    "request": dict(request.to_payload()),
                    "invocation": {
                        "program": invocation.value.program,
                        "kind": invocation.value.kind.value,
                        "argv": list(invocation.value.argv),
                        "payload": durable_payload,
                        "import_edge": invocation.value.import_edge,
                    },
                    "expected_result": dict(expected_result),
                },
            )
            if is_refusal(saved):
                return saved
            expected_ref = saved.value.get("fp1")
            expected_hash = saved.value.get("sha256")
            if not isinstance(expected_ref, str) or not isinstance(expected_hash, str):
                return invalid_input(
                    "expected_context", "CT-11 write returns its immutable fp1 and content digest"
                )
            self._expected_context_hashes[minted.value.job_id] = expected_hash
            expected_artifact = self._jobs.attach_artifact(
                minted.value.job_id,
                JobArtifact(
                    fp1=expected_ref,
                    completeness=ArtifactCompleteness.PARTIAL,
                ),
            )
            if is_refusal(expected_artifact):
                return expected_artifact
            placed_handle = expected_artifact.value
        receipt = self._transport.submit(invocation.value)
        if is_refusal(receipt):
            self._occupancy = release_qmb_job(
                admitted.value,
                occupancy_key=kind,
                job_id=job_id,
            )
            return receipt
        self._occupancy = admitted.value
        self._start_exit_observer(minted.value.job_id)
        return Ok(
            QmbPlacement(
                handle=placed_handle,
                request=request,
                invocation=invocation.value,
                receipt=receipt.value,
            )
        )

    def occupying_job(self, environment_ref: str) -> str | None:
        parsed = environment_kind_from_ref(environment_ref)
        key = parsed.value if is_ok(parsed) else environment_ref
        self._release_terminal()
        return self._occupancy.get(key)

    def observe_outcome(
        self,
        job_id: str,
        state: JobHandleState | str,
    ) -> Result[JobHandle]:
        """Refuse caller-authored completion states; process observation owns outcomes."""
        requested_state = state.value if isinstance(state, JobHandleState) else state
        if requested_state == JobHandleState.DONE.value:
            return policy_rejection(
                "job_state",
                "DONE requires a waited child exit plus exact durable QMB terminal readback",
                job_id=job_id,
            )
        if requested_state == JobHandleState.UNKNOWN.value:
            self._record_lost_certainty(
                job_id,
                invalid_input(
                    "job_state",
                    "QMB outcome is unknown because durable child completion was not observed",
                ),
            )
            handle = self._jobs.handle_for(job_id)
            if handle is None:
                return invalid_input("job_id", "unknown qmb job", given=job_id)
            if handle.state is JobHandleState.UNKNOWN:
                return Ok(handle)
            return policy_rejection("job_state", "lost QMB certainty persists UNKNOWN")
        return self._record_observed_state(job_id, state)

    def _record_observed_state(self, job_id: str, state: JobHandleState | str) -> Result[JobHandle]:
        """Persist an outcome already derived from the owned process boundary."""
        with self._observer_lock:
            handle = self._jobs.handle_for(job_id)
            if handle is None:
                return invalid_input("job_id", "unknown qmb job", given=job_id)
            if handle.is_terminal:
                current_state = handle.state.value
                given_state = state.value if isinstance(state, JobHandleState) else state
                if current_state == given_state:
                    return Ok(handle)
                return policy_rejection(
                    "job_state",
                    "one observed QMB child outcome cannot replace a terminal JobHandle",
                    current=current_state,
                    given=given_state,
                )
            if handle.state is JobHandleState.QUEUED:
                started = self._jobs.start(job_id)
                if is_refusal(started):
                    return started
            completed = self._jobs.complete(job_id, state, writer="qmb_outcome")
            if is_refusal(completed):
                return completed
            self._release_terminal()
            return completed

    def _verify_terminal_result(self, job_id: str) -> Result[Mapping[str, object]]:
        expected = self._expected_terminal_results.get(job_id)
        if expected is None:
            restored = self._restore_expected_context(job_id)
            if is_refusal(restored):
                return restored
            expected = restored.value["expected_result"]
        reader = getattr(self._transport, "terminal_result", None)
        if not callable(reader):
            return invalid_input(
                "qmb_terminal_result",
                "successful QMB exit requires the transport's durable-result readback",
                job_id=job_id,
            )
        read_result = cast(Callable[[str], Result[Mapping[str, object]]], reader)
        result = read_result(job_id)
        if is_refusal(result):
            return result
        return self._validate_terminal_payload(result.value, cast(Mapping[str, object], expected))

    def _validate_terminal_payload(
        self, payload: Mapping[str, object], expected: Mapping[str, object]
    ) -> Result[Mapping[str, object]]:
        study_result = expected.get("class") == "qmb-operator-alternative-study-result-v1"
        for field_name, field_value in expected.items():
            if field_name in {"mints_ct32", "operator_descriptor_fp1"} or (
                study_result
                and field_name
                in {
                    "job_id",
                    "attempt_id",
                    "experiment_spec_fp1",
                    "evidence_ref",
                    "split_manifest_fp1",
                    "composition_class",
                    "generation_count",
                    "batch_size",
                }
            ):
                continue
            actual = payload.get(field_name)
            if type(actual) is not type(field_value) or actual != field_value:
                return policy_rejection(
                    "qmb_terminal_result",
                    "durable QMB result matches this job, attempt, spec, evidence, and split",
                    mismatch_field=field_name,
                )
        expected_mode = expected.get("mints_ct32")
        expected_class = (
            "qmb-recorded-replay-result-v1"
            if expected_mode is True
            else "qmb-alternative-result-v1"
            if expected_mode is False
            else None
        )
        if expected.get("composition_class") == "alternative-study":
            expected_class = "qmb-operator-alternative-study-result-v1"
        if payload.get("class") != expected_class:
            return policy_rejection(
                "qmb_terminal_result", "durable result class matches the trusted preflight mode"
            )
        descriptor_fp = expected.get("operator_descriptor_fp1")
        if isinstance(descriptor_fp, str) and not study_result:
            result_binding = payload.get("operator_binding")
            result_descriptor = (
                cast(Mapping[str, object], result_binding).get("runtime_descriptor_fp1")
                if isinstance(result_binding, Mapping)
                else payload.get("operator_descriptor_fp1")
            )
            if result_descriptor != descriptor_fp:
                return policy_rejection(
                    "qmb_terminal_result",
                    "durable result is pinned to the prepared operator descriptor",
                )
        fingerprint_fields = (
            (
                "operator_binding_fp1",
                "composition_fp1",
                "source_fp1",
                "split_fp1",
                "registry_fp1",
                "interpreter_registration_fp1",
                "run_receipt_fp1",
                "terminal_artifact_fp1",
                "final_accounting_state_fp1",
            )
            if expected_class == "qmb-alternative-result-v1"
            else (
                "study_fp1",
                "operational_fp1",
                "occurrence_event_fp1",
            )
            if expected_class == "qmb-operator-alternative-study-result-v1"
            else ("ct32_fp1", "run_fp1", "terminal_line_fp1")
        )
        for field_name in fingerprint_fields:
            value = payload.get(field_name)
            if (
                not isinstance(value, str)
                or len(value) != 75
                or not value.startswith("fp1:sha256:")
                or any(char not in "0123456789abcdef" for char in value[11:])
            ):
                return invalid_input(
                    field_name,
                    "durable QMB completion carries its canonical composition fingerprints",
                )
        if expected_class == "qmb-operator-alternative-study-result-v1":
            history = payload.get("generation_run")
            artifacts = payload.get("terminal_artifact_fp1s")
            if not isinstance(history, Mapping) or not isinstance(artifacts, (list, tuple)):
                return invalid_input(
                    "generation_run", "durable Study result carries history and terminals"
                )
            history_row = cast(Mapping[str, object], history)
            generation_count = expected.get("generation_count")
            batch_size = expected.get("batch_size")
            generations = history_row.get("completed_generations")
            generation_list = cast(Sequence[object], generations)
            artifact_list = cast(Sequence[object], artifacts)
            if (
                type(generation_count) is not int
                or type(batch_size) is not int
                or type(history_row.get("generation_count")) is not int
                or history_row.get("generation_count") != generation_count
                or not isinstance(generations, (list, tuple))
                or len(generation_list) != generation_count
                or len(artifact_list) != generation_count * batch_size
                or history_row.get("study_fp") != expected.get("study_fp1")
            ):
                return policy_rejection(
                    "generation_run", "Study completion covers the entire pinned budget"
                )
            if any(
                not isinstance(item, str)
                or len(item) != 75
                or not item.startswith("fp1:sha256:")
                or any(char not in "0123456789abcdef" for char in item[11:])
                for item in artifact_list
            ):
                return invalid_input(
                    "terminal_artifact_fp1s", "Study terminal references are canonical fp1 values"
                )
        return Ok(payload)

    def _expected_context_store(self) -> Result[AppendStore]:
        if self._artifact_store is not None:
            if self._artifact_store.world is not World.LIVE:
                return invalid_input(
                    "artifact_store", "QMA expected-result metadata uses the live artifact room"
                )
            return Ok(self._artifact_store)
        if self._artifact_root is not None:
            try:
                if not self._artifact_root.is_absolute() or self._artifact_root.is_symlink():
                    return invalid_input(
                        "artifact_root", "configured CT-11 root is absolute and not a symlink"
                    )
                self._artifact_root.mkdir(mode=0o700, parents=True, exist_ok=True)
                owner = EvidenceStore(self._artifact_root)
                live = owner.for_world(World.LIVE)
                if is_refusal(live):
                    return live
                self._artifact_store_owner = owner
                self._artifact_store = live.value.append_store
                return Ok(self._artifact_store)
            except OSError as exc:
                return invalid_input(
                    "artifact_root", "configured CT-11 store opens", error=str(exc)
                )
        return invalid_input(
            "artifact_store",
            "restart-verifiable QMB placement requires the daemon's declared CT-11 store",
        )

    def _restore_expected_context(self, job_id: str) -> Result[Mapping[str, object]]:
        store = self._expected_context_store()
        if is_refusal(store):
            return store
        handle = self._jobs.handle_for(job_id)
        if handle is None:
            return invalid_input("job_id", "expected context belongs to a durable JobHandle")
        candidates = tuple(
            artifact
            for artifact in handle.artifacts
            if artifact.completeness is ArtifactCompleteness.PARTIAL
        )
        if not candidates:
            return invalid_input(
                "expected_context", "JobHandle references the immutable expected-context artifact"
            )
        valid: list[tuple[Mapping[str, object], str]] = []
        for artifact in candidates:
            candidate = read_expected_context(
                store=store.value,
                reference_fp1=artifact.fp1,
                job_id=job_id,
            )
            if not is_refusal(candidate):
                valid.append((candidate.value, artifact.fp1))
        if len(valid) != 1:
            return invalid_input(
                "expected_context", "JobHandle resolves exactly one checked expected-context row"
            )
        saved = Ok(valid[0][0])
        expected_ref = valid[0][1]
        if is_refusal(saved):
            return saved
        expected = saved.value.get("expected_result")
        if not isinstance(expected, Mapping):
            return invalid_input("expected_result", "durable context contains expected result")
        expected_row = cast(Mapping[str, object], expected)
        handle = self._jobs.handle_for(job_id)
        if (
            expected_row.get("job_id") != job_id
            or handle is None
            or saved.value.get("attempt_id") != handle.attempt_id
            or saved.value.get("task_id") != handle.task_id
        ):
            return invalid_input("expected_result", "durable context binds this JobHandle")
        expected_map = cast(Mapping[str, object], expected)
        digest = saved.value.get("sha256")
        if not isinstance(digest, str):
            return invalid_input("expected_context", "durable context has its verified digest")
        self._expected_terminal_results[job_id] = MappingProxyType(dict(expected_map))
        self._expected_context_hashes[job_id] = digest
        restored_context: dict[str, object] = {
            "expected_result": expected_map,
            "context": saved.value,
            "context_artifact_fp1": expected_ref,
        }
        return Ok(restored_context)

    def reconcile_restored_jobs(self) -> Result[tuple[str, ...]]:
        """Reopen persisted QMB terminals for UNKNOWN jobs without resolving them.

        CT-46 requires restart uncertainty to remain behind the operator gate.
        This method never infers process state from a PID or changes JobHandle
        state; it records only an independently reopened domain result.
        """
        verified_jobs: list[str] = []
        reader = getattr(self._transport, "verify_persisted_result", None)
        if not callable(reader):
            return Ok(())
        for handle in self._jobs.store.all():
            if handle.state is not JobHandleState.UNKNOWN:
                continue
            restored = self._restore_expected_context(handle.job_id)
            if is_refusal(restored):
                continue
            context = restored.value.get("context")
            if not isinstance(context, Mapping):
                continue
            context_map = cast(Mapping[str, object], context)
            invocation_raw = context_map.get("invocation")
            invocation = _invocation_from_payload(cast(object, invocation_raw))
            if is_refusal(invocation):
                continue
            try:
                checked = cast(
                    "Callable[[str, QmbDoorInvocation], Result[Mapping[str, object]]]", reader
                )(handle.job_id, invocation.value)
            except Exception as exc:
                with self._observer_lock:
                    self._observer_failures[handle.job_id] = invalid_input(
                        "qmb_restart_verification",
                        "verify-only child failed; JobHandle remains UNKNOWN",
                        error=str(exc),
                    )
                continue
            if is_refusal(checked):
                continue
            expected_result = restored.value.get("expected_result")
            if not isinstance(expected_result, Mapping):
                continue
            compared = self._validate_terminal_payload(
                checked.value, cast(Mapping[str, object], expected_result)
            )
            if is_refusal(compared):
                continue
            proof = self._persist_verified_result(handle.job_id, compared.value)
            if not is_refusal(proof):
                verified_jobs.append(handle.job_id)
        return Ok(tuple(verified_jobs))

    def resolve_verified_unknown(
        self, job_id: str, *, principal: PrincipalClass | str
    ) -> Result[JobHandle]:
        """Resolve UNKNOWN only after operator action cites reopened durable proof."""
        expected = self._restore_expected_context(job_id)
        if is_refusal(expected):
            return policy_rejection(
                "verified_context", "unknown resolution requires persisted QMB readback"
            )
        context = expected.value.get("context")
        if not isinstance(context, Mapping):
            return policy_rejection("verified_context", "expected artifact contains its context")
        context_map = cast(Mapping[str, object], context)
        expected_sha = context_map.get("sha256")
        if not isinstance(expected_sha, str):
            return policy_rejection("verified_context", "verification matches expected context")
        store = self._expected_context_store()
        if is_refusal(store):
            return store
        handle_before = self._jobs.handle_for(job_id)
        if handle_before is None:
            return invalid_input("job_id", "operator resolution requires its durable JobHandle")
        proofs: list[tuple[Mapping[str, object], str]] = []
        for artifact in handle_before.artifacts:
            if artifact.completeness is not ArtifactCompleteness.COMPLETE:
                continue
            candidate = read_verified_context(
                store=store.value,
                reference_fp1=artifact.fp1,
                job_id=job_id,
                expected_reference_fp1=expected.value["context_artifact_fp1"],
                expected_sha256=expected_sha,
            )
            if not is_refusal(candidate):
                proofs.append((candidate.value, artifact.fp1))
        if len(proofs) != 1:
            return policy_rejection(
                "verified_context", "operator resolution finds exactly one checked proof artifact"
            )
        proof, proof_ref = proofs[0]
        result = proof.get("result")
        if not isinstance(result, Mapping):
            return policy_rejection("verified_context", "verification contains QMB readback")
        expected_result = expected.value.get("expected_result")
        if not isinstance(expected_result, Mapping):
            return policy_rejection("expected_result", "expected context has a result binding")
        compared = self._validate_terminal_payload(
            cast(Mapping[str, object], result), cast(Mapping[str, object], expected_result)
        )
        if is_refusal(compared):
            return compared
        proof_fp = proof.get("sha256")
        if not isinstance(proof_fp, str):
            return invalid_input("verified_context", "proof fingerprint is present")
        handle = self._jobs.handle_for(job_id)
        if handle is None or not any(
            artifact.fp1 == proof_ref and artifact.completeness is ArtifactCompleteness.COMPLETE
            for artifact in handle.artifacts
        ):
            return policy_rejection(
                "verified_context", "operator resolution cites the complete proof artifact"
            )
        return self._jobs.resolve_unknown(
            job_id,
            principal=principal,
            recorded=True,
            to_state=JobHandleState.DONE,
            correlation_id=proof_fp,
        )

    def wait_and_observe(self, job_id: str, *, timeout: float = 10.0) -> Result[JobHandle]:
        """Observe the actual QMB child exit instead of accepting a caller state."""
        waiter = getattr(self._transport, "wait", None)
        if not callable(waiter):
            return invalid_input("transport", "QMB transport has no process wait capability")
        try:
            exit_code = waiter(job_id, timeout=timeout)
        except subprocess.TimeoutExpired:
            return self._jobs.observe_lost_certainty(job_id, trigger="qmb_process_timeout")
        if exit_code is None:
            return invalid_input("job_id", "QMB process exit is not available", given=job_id)
        if isinstance(exit_code, bool) or not isinstance(exit_code, int):
            return invalid_input("exit_code", "QMB process wait returns an integer exit code")
        return self._record_process_exit(job_id, exit_code)

    def _record_process_exit(self, job_id: str, exit_code: int) -> Result[JobHandle]:
        with self._observer_lock:
            current = self._jobs.handle_for(job_id)
            if current is None:
                return invalid_input("job_id", "QMB process exit resolves a durable JobHandle")
            if current.is_terminal:
                return Ok(current)
            return self._record_process_exit_locked(job_id, exit_code)

    def _record_process_exit_locked(self, job_id: str, exit_code: int) -> Result[JobHandle]:
        if exit_code != 0:
            return self._record_observed_state(job_id, JobHandleState.FAILED)
        verified = self._verify_terminal_result(job_id)
        if is_refusal(verified):
            self._record_lost_certainty(job_id, verified)
            uncertain_handle = self._jobs.handle_for(job_id)
            if uncertain_handle is None:
                return invalid_input("job_id", "QMB job remains resolvable after lost certainty")
            return Ok(uncertain_handle)
        persisted_proof = self._persist_verified_result(job_id, verified.value)
        if is_refusal(persisted_proof):
            self._record_lost_certainty(job_id, persisted_proof)
            uncertain_handle = self._jobs.handle_for(job_id)
            if uncertain_handle is None:
                return invalid_input(
                    "job_id", "QMB job remains resolvable after proof persistence refusal"
                )
            return Ok(uncertain_handle)
        return self._record_observed_state(job_id, JobHandleState.DONE)

    def _persist_verified_result(self, job_id: str, result: Mapping[str, object]) -> Result[None]:
        expected_sha = self._expected_context_hashes.get(job_id)
        if expected_sha is None:
            # Explicit test doubles and non-registered diagnostic paths do not
            # claim restart-verifiable coordinated completion.
            return Ok(None)
        expected = self._restore_expected_context(job_id)
        if is_refusal(expected):
            return expected
        context = expected.value.get("context")
        if not isinstance(context, Mapping):
            return invalid_input("expected_context", "checked artifact contains its context")
        context_map = cast(Mapping[str, object], context)
        expected_sha = context_map.get("sha256")
        if not isinstance(expected_sha, str):
            return invalid_input("expected_context", "proof links to the checked expected artifact")
        expected_ref = expected.value.get("context_artifact_fp1")
        if not isinstance(expected_ref, str):
            return invalid_input("expected_context", "JobHandle pins the expected artifact fp1")
        store = self._expected_context_store()
        if is_refusal(store):
            return store
        stored = write_verified_context(
            store=store.value,
            job_id=job_id,
            expected_reference_fp1=expected_ref,
            expected_sha256=expected_sha,
            result=result,
        )
        if is_refusal(stored):
            return stored
        reference = stored.value.get("fp1")
        if not isinstance(reference, str):
            return invalid_input("verified_context", "CT-11 proof returns its durable fp1")
        attached = self._jobs.attach_artifact(
            job_id,
            JobArtifact(
                fp1=reference,
                completeness=ArtifactCompleteness.COMPLETE,
            ),
        )
        if is_refusal(attached):
            return attached
        return Ok(None)

    def _start_exit_observer(self, job_id: str) -> None:
        """Observe a real CLI child exit without accepting caller-authored status."""
        waiter = getattr(self._transport, "wait", None)
        if not callable(waiter):
            return

        def observe() -> None:
            known_exit_code: int | None = None
            while True:
                if known_exit_code is None:
                    try:
                        exit_code = waiter(job_id, timeout=0.25)
                    except subprocess.TimeoutExpired:
                        continue
                    except Exception as exc:  # transport/plugin boundary
                        self._record_lost_certainty(
                            job_id,
                            invalid_input(
                                "qmb_wait",
                                "child wait failed before a terminal code was observed",
                                error=str(exc),
                            ),
                        )
                        return
                    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
                        self._record_lost_certainty(
                            job_id,
                            invalid_input(
                                "exit_code", "child wait must return a process exit code"
                            ),
                        )
                        return
                    known_exit_code = exit_code
                observed = self._record_process_exit(job_id, known_exit_code)
                if is_ok(observed):
                    with self._observer_lock:
                        self._observer_failures.pop(job_id, None)
                    return
                with self._observer_lock:
                    self._observer_failures[job_id] = observed
                    current = self._jobs.handle_for(job_id)
                    if current is None or current.is_terminal:
                        return
                time.sleep(0.25)

        observer = threading.Thread(
            target=observe,
            name=f"qmb-exit-observer-{job_id}",
            daemon=True,
        )
        self._observers.append(observer)
        observer.start()

    def _record_lost_certainty(self, job_id: str, cause: object) -> None:
        """Retry the known UNKNOWN transition until its durable write succeeds."""
        while True:
            with self._observer_lock:
                self._observer_failures[job_id] = cause
                self._start_observation_if_queued(job_id)
                certainty = self._jobs.observe_lost_certainty(job_id, trigger="lost_supervisor")
                if is_ok(certainty):
                    self._release_terminal()
                    return
                self._observer_failures[job_id] = certainty
                current = self._jobs.handle_for(job_id)
                if current is None or current.is_terminal:
                    return
            time.sleep(0.25)

    def _start_observation_if_queued(self, job_id: str) -> None:
        """Move the submitted handle through its started state before resolution."""
        handle = self._jobs.handle_for(job_id)
        if handle is not None and handle.state is JobHandleState.QUEUED:
            started = self._jobs.start(job_id)
            if is_refusal(started):
                self._observer_failures[job_id] = started

    def observer_failure_for(self, job_id: str) -> object | None:
        """Return the retained transport/projection failure for a child observer."""
        with self._observer_lock:
            return self._observer_failures.get(job_id)

    def wait_for_observers(self, *, timeout: float = 10.0) -> bool:
        """Join owned exit observers; useful for bounded shutdown and tests."""
        if isinstance(timeout, bool) or timeout < 0:
            return False
        deadline = time.monotonic() + timeout
        for observer in tuple(self._observers):
            remaining = max(0.0, deadline - time.monotonic())
            observer.join(remaining)
        return all(not observer.is_alive() for observer in self._observers)

    def cancel(
        self,
        job_id: str,
        *,
        writer: str = COORDINATED_CANCEL_AUTHORITY,
    ) -> Result[JobHandle]:
        """Serialize cancellation against the real-child exit observer."""
        with self._observer_lock:
            return self._cancel_locked(job_id, writer=writer)

    def _cancel_locked(
        self,
        job_id: str,
        *,
        writer: str,
    ) -> Result[JobHandle]:
        """JobHandle.cancel only. Production door maps it to QMB abort."""
        mapped = False
        abort_fn = getattr(self._transport, "abort", None)
        if self.maps_cancel_to_qmb_abort and callable(abort_fn):
            abort = cast("Callable[[str], Result[QmbAbortReceipt]]", abort_fn)
            aborted = abort(job_id)
            if is_refusal(aborted):
                return aborted
            mapped = True
        cancelled = self._jobs.cancel(job_id, writer=writer)
        if is_refusal(cancelled):
            return cancelled
        if mapped:
            self._jobs.record_progress(
                job_id,
                "qmb_abort",
                {
                    "mapped_from": COORDINATED_CANCEL_AUTHORITY,
                    "qmb_ledger_state": QMB_ABORTED_LEDGER_STATE,
                    "qmb_ledger_writer": "qmb",
                    "qma_writes_qmb_ledger": False,
                    "new_event_bus": False,
                },
            )
        self._release_terminal()
        return cancelled

    def cancel_from_product_session(
        self,
        payload: object,
        *,
        principal_class: PrincipalClass | str,
        operator_principal: object,
        originating_session_principal: object,
        producer_id: object,
        wire_id: object,
    ) -> Result[JobHandle]:
        """Abort the production QMB child before committing an authorized UI cancel."""
        mapped_job_ids: list[str] = []
        abort_fn = getattr(self._transport, "abort", None)

        def abort_before_transition(handle: JobHandle) -> Result[None]:
            if not self.maps_cancel_to_qmb_abort or not callable(abort_fn):
                return Ok(None)
            abort = cast("Callable[[str], Result[QmbAbortReceipt]]", abort_fn)
            aborted = abort(handle.job_id)
            if is_refusal(aborted):
                return aborted
            mapped_job_ids.append(handle.job_id)
            return Ok(None)

        cancelled = self._jobs.cancel_from_product_session(
            payload,
            principal_class=principal_class,
            operator_principal=operator_principal,
            originating_session_principal=originating_session_principal,
            producer_id=producer_id,
            wire_id=wire_id,
            before_cancel=abort_before_transition,
        )
        if is_refusal(cancelled):
            return cancelled
        for job_id in mapped_job_ids:
            self._jobs.record_progress(
                job_id,
                "qmb_abort",
                {
                    "mapped_from": COORDINATED_CANCEL_AUTHORITY,
                    "qmb_ledger_state": QMB_ABORTED_LEDGER_STATE,
                    "qmb_ledger_writer": "qmb",
                    "qma_writes_qmb_ledger": False,
                    "new_event_bus": False,
                },
            )
        self._release_terminal()
        return cancelled

    @property
    def maps_cancel_to_qmb_abort(self) -> bool:
        return bool(getattr(self._transport, "maps_cancel_to_qmb_abort", False))

    def import_qmb_package(self) -> Result[None]:
        """There is no import edge. Calling this is always a policy rejection."""
        return refuse_qmb_import_edge()

    def set_parallelism(self, workers: int) -> Result[None]:
        _ = workers
        return refuse_qmb_owned_concern(concern="intra_node_parallelism")

    def append_run_ledger(
        self,
        entry: Mapping[str, object],
        *,
        writer: str = "daemon",
    ) -> Result[None]:
        if is_unauthorized_cancel_writer(writer):
            return refuse_unauthorized_cancel(writer=writer, surface="qmb_ledger")
        role = entry.get("role", entry.get("state"))
        if role == QMB_ABORTED_LEDGER_STATE:
            authorized = authorize_qmb_ledger_aborted_writer(writer)
            if is_refusal(authorized):
                return authorized
        _ = entry
        return refuse_qmb_owned_concern(concern="run_ledger")

    def admit_process_per_run_child(
        self,
        occupancy_key: str,
        *,
        child_job_id: str,
    ) -> Result[dict[str, str]]:
        """QMB process-per-run children are not additional QMA jobs (FR-W11)."""
        return admit_qmb_job(
            self._occupancy,
            occupancy_key=occupancy_key,
            job_id=child_job_id,
            kind=QMB_PROCESS_PER_RUN_CHILD,
        )

    def qmb_opened_daemon_sqlite(self) -> bool:
        return qmb_opens_daemon_sqlite()

    def place_query(
        self,
        command: object,
        *,
        owner: ActorId | str,
        task_id: str,
        environment_ref: str,
        extra: Mapping[str, object] | None = None,
        dispatch_lease: DispatchLease | None = None,
        model_deployment_ref: object = None,
        persist_projection: bool = False,
        mint_ct32: object = None,
        successor: object = None,
        experiment_spec_fp1: str | None = None,
    ) -> Result[QmbQueryPlacement]:
        """Place a QMB query: no occupancy, no CT-32, no ExperimentSpec successor."""
        classified = classify_qmb_door_occupancy(command)
        if is_refusal(classified):
            return classified
        row = classified.value
        if row.occupancy != QMB_OCCUPANCY_QUERY:
            return invalid_input(
                "occupancy",
                "place_query places queries only; runs occupy the environment (FR-W11; DEC-0276)",
                command=row.command,
                occupancy=row.occupancy,
            )
        if mint_ct32 is not None and mint_ct32 is not False:
            return refuse_query_ct32_or_successor(command=row.command)
        if successor is not None and successor is not False:
            return refuse_query_ct32_or_successor(command=row.command)
        if persist_projection and row.command != "analysis.project":
            return invalid_input(
                "command",
                "coordinated analysis.published persistence is analysis.project only "
                "(FR-W24; DEC-0273)",
                command=row.command,
            )
        parsed_env = environment_kind_from_ref(environment_ref)
        if is_refusal(parsed_env):
            return parsed_env
        occupancy_key = parsed_env.value
        if (
            self._environments.get(occupancy_key) is None
            and self._environments.declaration(occupancy_key) is None
        ):
            return NoEnvironment.of(kind=occupancy_key, reason="kind_unbound")
        admitted = admit_qmb_job(
            self._occupancy,
            occupancy_key=occupancy_key,
            job_id=f"qmbq:{occupancy_key}:{task_id}",
            occupancy_class=QMB_OCCUPANCY_QUERY,
        )
        if is_refusal(admitted):
            return admitted
        job_id = f"qmbq:{occupancy_key}:{task_id}"
        minted = self._jobs.submit(
            owner=owner,
            task_id=task_id,
            job_id=job_id,
        )
        if is_refusal(minted):
            return minted
        invocation = build_qmb_query_invocation(
            job_id=minted.value.job_id,
            attempt_id=minted.value.attempt_id,
            command=row.command,
            environment_ref=environment_ref,
            occupancy_key=occupancy_key,
            extra=extra,
        )
        if is_refusal(invocation):
            return invocation
        receipt = self._transport.submit(invocation.value)
        if is_refusal(receipt):
            return receipt
        started = self._jobs.start(job_id)
        if is_refusal(started):
            return started
        published: PublishedProjection | None = None
        if persist_projection:
            persisted = self._persist_projection_query(
                receipt=receipt.value,
                extra=extra,
                spec_fp1=experiment_spec_fp1,
                dispatch_lease=dispatch_lease,
                model_deployment_ref=model_deployment_ref,
            )
            if is_refusal(persisted):
                return persisted
            published = persisted.value
        completed = self._jobs.complete(job_id, JobHandleState.DONE, writer="qmb_outcome")
        if is_refusal(completed):
            return completed
        self._jobs.record_progress(
            job_id,
            "query",
            {
                "command": row.command,
                "occupancy": QMB_OCCUPANCY_QUERY,
                "mints_ct32": False,
                "mints_experiment_spec": False,
                "kind": ANALYSIS_PUBLISHED_KIND if published is not None else row.command,
                "new_event_bus": False,
            },
        )
        return Ok(
            QmbQueryPlacement(
                handle=completed.value,
                invocation=invocation.value,
                receipt=receipt.value,
                command=row.command,
                published=published,
            )
        )

    def place_procedure_step(
        self,
        step: Mapping[str, object] | str,
        *,
        owner: ActorId | str,
        task_id: str,
        environment_ref: str,
        experiment_spec_fp1: str | None = None,
        evidence_ref: str | None = None,
        extra: Mapping[str, object] | None = None,
        dispatch_lease: DispatchLease | None = None,
        registering_attempt_no: int | None = None,
        model_deployment_ref: object = None,
        persist_projection: bool = False,
        mint_ct32: object = None,
        successor: object = None,
        resolved_config_ref: object = None,
        change: object = None,
        edge_type: object = None,
        world: str = QMB_WORLD_REPLAY,
        door: QmbDoorKind | str = QmbDoorKind.CLI,
        qmb_ledger_ref: object = None,
        ct32_ref: object = None,
    ) -> Result[ProcedureStepPlacement]:
        """Place one procedure door step through the Story 36.2 QMB door.

        Run-steps occupy the environment as one CLI/MCP run invocation.
        A door step that changes resolved-config mints an ExperimentSpec
        successor via ``create_successor`` plus CT-07 ``branches-from``.
        Query-steps call ``place_query`` (Epic 35/33 door queries): no occupancy,
        no CT-32, no ExperimentSpec successor. A second run-step is refused
        while the slot is held; query-steps still proceed.
        """
        classified = classify_procedure_step(step)
        if is_refusal(classified):
            return classified
        row = classified.value
        admitted_edge = admit_procedure_successor_edge(edge_type)
        if is_refusal(admitted_edge):
            return admitted_edge
        admitted_change = admit_procedure_successor_change(change)
        if is_refusal(admitted_change):
            return admitted_change
        next_config = procedure_step_resolved_config_ref(
            step,
            extra=extra,
            resolved_config_ref=resolved_config_ref,
        )
        predecessor_config: str | None = None
        if (
            self._experiments is not None
            and isinstance(experiment_spec_fp1, str)
            and experiment_spec_fp1.strip()
        ):
            found = self._experiments.resolve(experiment_spec_fp1.strip())
            if is_ok(found):
                predecessor_config = found.value.spec.resolved_config_ref
        changes_config = procedure_step_changes_resolved_config(
            resolved_config_ref=next_config,
            predecessor_resolved_config_ref=predecessor_config,
        )
        door_extra = _procedure_extra_without_lineage(extra)
        if row.occupancy == QMB_OCCUPANCY_QUERY:
            if mint_ct32 is not None and mint_ct32 is not False:
                return refuse_query_ct32_or_successor(command=row.command)
            if successor is not None and successor is not False:
                return refuse_query_ct32_or_successor(command=row.command)
            if changes_config:
                return refuse_query_ct32_or_successor(command=row.command)
            placed = self.place_query(
                row.command,
                owner=owner,
                task_id=task_id,
                environment_ref=environment_ref,
                extra=door_extra,
                dispatch_lease=dispatch_lease,
                model_deployment_ref=model_deployment_ref,
                persist_projection=persist_projection,
                mint_ct32=mint_ct32,
                successor=successor,
                experiment_spec_fp1=experiment_spec_fp1,
            )
            if is_refusal(placed):
                return placed
            query = placed.value
            return Ok(
                ProcedureStepPlacement(
                    occupancy=QMB_OCCUPANCY_QUERY,
                    command=query.command,
                    mints_ct32=False,
                    mints_experiment_spec=False,
                    consumes_environment=False,
                    query=query,
                    experiment_spec_fp1=experiment_spec_fp1,
                )
            )
        if not isinstance(experiment_spec_fp1, str) or experiment_spec_fp1.strip() == "":
            return invalid_input(
                "experiment_spec_fp1",
                "a procedure run-step is placed through the CT-47 qmb door and "
                "requires a registered ExperimentSpec (FR-W33; DEC-0277)",
            )
        if not isinstance(evidence_ref, str) or evidence_ref.strip() == "":
            return invalid_input(
                "evidence_ref",
                "a procedure run-step requires recorded evidence (CT-47; FR-W33)",
            )
        spec_fp1 = experiment_spec_fp1.strip()
        registered_successor: RegisteredExperiment | None = None
        if changes_config:
            minted = self._mint_resolved_config_successor(
                predecessor_fp1=spec_fp1,
                resolved_config_ref=next_config,
                dispatch_lease=dispatch_lease,
                registering_attempt_no=registering_attempt_no,
                model_deployment_ref=model_deployment_ref,
            )
            if is_refusal(minted):
                return minted
            registered_successor = minted.value
            edge = registered_successor.lineage_edge
            if edge is None or edge.edge_type.value != EXPERIMENT_LINEAGE_EDGE_TYPE:
                return policy_rejection(
                    "edge_type",
                    "a config-changing procedure door step must append the "
                    "existing CT-07 branches-from edge; bot supersedes and new "
                    "edge kinds are refused (FR-W34; DEC-0277)",
                    given=None if edge is None else edge.edge_type.value,
                    edge_type=EXPERIMENT_LINEAGE_EDGE_TYPE,
                )
            spec_fp1 = registered_successor.spec.spec_fp1
        placed_run = self.invoke(
            QMB_BACKTEST_TOOL_ID,
            owner=owner,
            task_id=task_id,
            environment_ref=environment_ref,
            experiment_spec_fp1=spec_fp1,
            evidence_ref=evidence_ref,
            world=world,
            door=door,
            extra=door_extra,
            dispatch_lease=dispatch_lease,
            model_deployment_ref=model_deployment_ref,
            qmb_ledger_ref=qmb_ledger_ref,
            ct32_ref=ct32_ref,
            command=row.command,
        )
        if is_refusal(placed_run):
            return placed_run
        run = placed_run.value
        return Ok(
            ProcedureStepPlacement(
                occupancy=QMB_OCCUPANCY_RUN,
                command=row.command,
                mints_ct32=row.mints_ct32,
                mints_experiment_spec=registered_successor is not None,
                consumes_environment=True,
                run=run,
                successor=registered_successor,
                experiment_spec_fp1=spec_fp1,
            )
        )

    def _mint_resolved_config_successor(
        self,
        *,
        predecessor_fp1: str,
        resolved_config_ref: object,
        dispatch_lease: DispatchLease | None,
        registering_attempt_no: int | None,
        model_deployment_ref: object,
    ) -> Result[RegisteredExperiment]:
        """Mint an ExperimentSpec successor via ``create_successor`` (FR-W34)."""
        if self._experiments is None:
            return invalid_input(
                "experiments",
                "a config-changing procedure door step mints an ExperimentSpec "
                "successor via create_successor plus CT-07 branches-from "
                "(FR-W34; DEC-0277)",
            )
        if dispatch_lease is None:
            return invalid_input(
                "dispatch_lease",
                "a config-changing procedure door step requires the Agent holding "
                "dispatch_lease (FR-W34; DEC-0308)",
            )
        if (
            isinstance(registering_attempt_no, bool)
            or not isinstance(registering_attempt_no, int)
            or registering_attempt_no < 0
        ):
            return invalid_input(
                "registering_attempt_no",
                "a config successor requires the observed current TaskLedger attempt",
            )
        return self._experiments.create_successor(
            predecessor_fp1=predecessor_fp1,
            change=EXPERIMENT_CHANGE_RESOLVED_CONFIG,
            dispatch_lease=dispatch_lease,
            registering_attempt_no=registering_attempt_no,
            model_deployment_ref=model_deployment_ref,
            resolved_config_ref=resolved_config_ref,
            source="qma-daemon",
        )

    def _persist_projection_query(
        self,
        *,
        receipt: QmbDoorReceipt,
        extra: Mapping[str, object] | None,
        spec_fp1: str | None,
        dispatch_lease: DispatchLease | None,
        model_deployment_ref: object,
    ) -> Result[PublishedProjection]:
        if self._experiments is None:
            return invalid_input(
                "experiments",
                "coordinated analysis.project persistence requires ExperimentSpec "
                "product truth (FR-W24; Story 36.3)",
            )
        if dispatch_lease is None or not isinstance(spec_fp1, str) or spec_fp1.strip() == "":
            return invalid_input(
                "experiment_spec_fp1",
                "coordinated analysis.published cites a registered ExperimentSpec "
                "fp1 (FR-W24; DEC-0273)",
            )
        view = _projection_view_from_stdout(receipt.stdout, extra)
        if is_refusal(view):
            return view
        return self._experiments.persist_published_view(
            spec_fp1=spec_fp1.strip(),
            dispatch_lease=dispatch_lease,
            model_deployment_ref=model_deployment_ref,
            view=view.value,
            artifact_root=self._artifact_root,
        )

    def store_artifact(self, artifact: Mapping[str, object]) -> Result[None]:
        _ = artifact
        return refuse_qmb_owned_concern(concern="artifact_contract")

    def qmb_owned_concerns(self) -> frozenset[str]:
        return QMB_OWNED_CONCERNS

    def _release_terminal(self) -> None:
        remaining: dict[str, str] = {}
        for key, job_id in self._occupancy.items():
            handle = self._jobs.handle_for(job_id)
            if handle is None or not handle.is_terminal:
                remaining[key] = job_id
        self._occupancy = remaining
