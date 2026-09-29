"""Composed asyncio daemon process (Story 36.1 / 36.3 / 61.1; FR-W09; FR-W10).

One long-running process from existing modules: the CT-40 loopback listener,
the Story 42.1 sole sqlite writer, the ExperimentSpec / Experiment Ledger /
CT-07 sqlite product truth, and the Epic 48 desk-pack roster. Connect, not a
sixth application: no new COMP, no HTTP experiment service, and no second
daemon runtime. QMB JSONL stays in QMB and is not merged into sqlite.
``analysis-backtest`` remains the Backtesting Service's daemon half.

Story 61.1: the process emits stdlib JSON-lines operator logs. Those lines
are not a journal, not a new sqlite class, and not a fourth observability
product. QMA telemetry store remains the trace/metric plane. Story 61.3:
mini-app failures stay off ``qmn/FAILURES.md``; agents do not write telemetry;
QMB LogSink may remain and no third logger is minted.
"""

from __future__ import annotations

import asyncio
import contextlib
import ctypes
import json
import logging
import os
import subprocess
import sys
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, cast

from qma.core.plugins.hooks import HookSource
from qma.core.plugins.packs import DESK_PLUGIN_PACK_IDS
from qma.core.ports.paper import (
    EPIC_PROMOTION_AUTHORITY,
    QMA_WRITES_HUB,
    refuse_hub_publish_from_qma,
    refuse_qma_hub_write,
    refuse_qma_promotion,
)
from qma.core.ports.qmb import (
    ANALYSIS_BACKTEST_PLUGIN_ID,
    QMB_OWNED_CONCERNS,
    refuse_qmb_import_edge,
    refuse_qmb_owned_concern,
)
from qma.core.ports.telemetry import TelemetryRecord
from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.backtest.service import BacktestingService
from qma.daemon.diagnosis import (
    DIAGNOSIS_EXISTED_AT_INSPECT_SHA,
    DIAGNOSIS_SQLITE_CLASS_MINTED,
    QMN_FAILURES_MD_EXTENDED_BY_KIT,
    Diagnosis,
    DiagnosisQueryService,
    claim_diagnosis_query_at_inspect_sha,
    refuse_diagnosis_fourth_store,
    refuse_qmn_alert_failure_class,
)
from qma.daemon.experiments import EXPERIMENT_SQLITE_TABLES, ExperimentSpecService
from qma.daemon.host_control import (
    CT40_BIND_PORT,
    HOST_CONTROL_EXISTED_AT_INSPECT_SHA,
    HOST_CONTROL_IS_CT40,
    HostControlChannel,
    LocalOperatorLive,
    bootstrap_first_operator,
    caller_owns_daemon_root,
    claim_host_control_existed_at_inspect_sha,
    claim_types_absent_at_inspect_sha,
    load_local_operator,
    read_host_control_token,
    recover_local_operator_control,
    rotate_local_operator_control,
)
from qma.daemon.host_control.local_operator import fold_local_operator_from_journal
from qma.daemon.journal.authoritative import AuthoritativeJournal
from qma.daemon.journal.clock import InjectedUtcClock
from qma.daemon.journal.variables import (
    PAIRING_SESSION_TTL_META_KEY,
    PAIRING_SESSION_TTL_REGISTRY_KEY,
    GovernedVariableRegistry,
    fold_pairing_ttl_from_journal,
)
from qma.daemon.ledgers.experiment import ExperimentLedgerStore
from qma.daemon.observability_boundary import (
    LOGS_REMAIN_LOGS,
    QMB_LOGSINK_MAY_REMAIN,
    THIRD_LOGGER_MINTED,
    emit_telemetry_from_hook,
    mint_third_logger,
    page_qmn_alert_with_mini_app_failure,
    place_typed_failure,
)
from qma.daemon.operator_log import (
    FOURTH_OBSERVABILITY_COMP_MINTED,
    LOGS_ARE_NOT_JOURNALS,
    LOGS_ENTER_FP1_IDENTITY,
    OPERATOR_LOG_SQLITE_CLASS_MINTED,
    OTEL_REMAINS_EXPORT_PORT_ONLY,
    QMN_FAILURES_MD_EXTENDED,
    TELEMETRY_STORE_REMAINS_TRACE_METRIC_PLANE,
    configure_daemon_logging,
    refuse_fourth_observability_comp,
    refuse_operator_log_sqlite_class,
    refuse_qmn_failures_extension,
)
from qma.daemon.operator_log import emit_operator_event as write_operator_json_line
from qma.daemon.operator_log import fingerprint_operator_log as refuse_operator_log_fp1
from qma.daemon.pairing import (
    PairingWsRegistry,
    confirm_pairing_pending_by_code,
    origin_revoke_pairing,
    pairing_status_record_ids,
    restore_pairing_projections,
    session_revoke_pairing,
)
from qma.daemon.persistence.sqlite_writer import SingleSqliteWriter
from qma.daemon.persistence.substrate import PersistenceSubstrate
from qma.daemon.plugins.packs import DeskPluginRoster
from qma.daemon.taskgraph.projection import (
    TASK_GRAPH_STATE_SQLITE_TABLES,
    TaskGraphStateService,
)
from qma.daemon.telemetry.store import TelemetryStore
from qma.wire.listener import (
    DEFAULT_BIND_HOST,
    ListenerBindConfig,
    ListenerPosture,
    validate_listener_startup,
)
from qma.wire.schemas import SCHEMA_FILES
from qma.wire.vocabulary import WIRE_VOCABULARY_OWNER
from qmf.core import Ok, Result, World, WriterId, is_refusal
from qmf.data.store.refusals import invalid_input, policy_rejection, storage_failure

__all__ = [
    "BROWSER_SPAWNS_PYTHON",
    "COMP_EXP_MINTED",
    "DAEMON_RECOVER_ENV",
    "DAEMON_RECOVER_FLAG",
    "DAEMON_SPAWN_MODULE",
    "DEFAULT_BIND_PORT",
    "HOST_CONTROL_ON_CT40_PORT",
    "HTTP_EXPERIMENT_SERVICE_MINTED",
    "QMB_JSONL_MERGED_INTO_SQLITE",
    "SIXTH_APPLICATION_MINTED",
    "START_GRANTS",
    "START_ORCHESTRATES_MISSIONS",
    "START_STARTS_QMN",
    "STOP_CANCELS_QMN",
    "STOP_STOPS_REMOTE",
    "BoundListener",
    "DaemonProcess",
    "run_recover_entry",
    "spawn_supervised_daemon",
    "supervised_recover_argv",
    "supervised_spawn_argv",
]


COMP_EXP_MINTED: Final[bool] = False
HTTP_EXPERIMENT_SERVICE_MINTED: Final[bool] = False
SIXTH_APPLICATION_MINTED: Final[bool] = False
QMB_JSONL_MERGED_INTO_SQLITE: Final[bool] = False
DEFAULT_BIND_PORT: Final[int] = 8765
DAEMON_SPAWN_MODULE: Final[str] = "qma.daemon"
DAEMON_RECOVER_FLAG: Final[str] = "--recover-control"
DAEMON_RECOVER_ENV: Final[str] = "QMA_DAEMON_RECOVER_CONTROL"
DAEMON_LOCK_NAME: Final[str] = ".daemon_writer"
START_ORCHESTRATES_MISSIONS: Final[bool] = False
START_GRANTS: Final[bool] = False
START_STARTS_QMN: Final[bool] = False
BROWSER_SPAWNS_PYTHON: Final[bool] = False
STOP_CANCELS_QMN: Final[bool] = False
STOP_STOPS_REMOTE: Final[bool] = False
HOST_CONTROL_ON_CT40_PORT: Final[bool] = HOST_CONTROL_IS_CT40


def supervised_spawn_argv(python: str | None = None) -> tuple[str, ...]:
    """Canonical ``python -m qma.daemon`` argv (Story 67.1)."""
    exe = sys.executable if python is None else python
    return (exe, "-m", DAEMON_SPAWN_MODULE)


def supervised_recover_argv(python: str | None = None) -> tuple[str, ...]:
    """One-shot recover entry. Does not bind 8765."""
    return (*supervised_spawn_argv(python), DAEMON_RECOVER_FLAG)


def spawn_supervised_daemon(
    *,
    root: Path,
    python: str | None = None,
    extra_env: Mapping[str, str] | None = None,
) -> subprocess.Popen[bytes]:
    """Spawn ``python -m qma.daemon`` with ``QMA_DAEMON_ROOT`` set.

    The child acquires ``.daemon_writer``. This does not orchestrate Missions,
    grant, or start QMN.
    """
    env = os.environ.copy()
    env["QMA_DAEMON_ROOT"] = str(root)
    if extra_env is not None:
        env.update(dict(extra_env))
    argv = supervised_spawn_argv(python)
    if os.name == "nt":
        return subprocess.Popen(
            argv,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    return subprocess.Popen(
        argv,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _pid_is_live(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        access = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(access, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
    except OSError, ProcessLookupError:
        return False
    return True


def _live_writer_pid(root: Path) -> int | None:
    path = root / DAEMON_LOCK_NAME
    if not path.is_file():
        return None
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except OSError, json.JSONDecodeError:
        return None
    if not isinstance(raw, dict):
        return None
    mapping = cast("dict[str, object]", raw)
    pid = mapping.get("pid")
    if isinstance(pid, bool) or not isinstance(pid, int):
        return None
    if _pid_is_live(pid):
        return pid
    return None


def run_recover_entry(
    root: Path | str,
    *,
    machine: str,
    boot_epoch_id: str,
    plugins_root: Path | None = None,
    plugin_load_configs: Mapping[str, Mapping[str, object]] | None = None,
    log_handler: logging.Handler | None = None,
    owns_root: object = None,
) -> Result[Mapping[str, object]]:
    """Acquire ``.daemon_writer``, remint host_control, exit without binding 8765."""
    path = Path(root)
    owned = caller_owns_daemon_root(path) if owns_root is None else owns_root is True
    if owns_root is not None and callable(owns_root):
        try:
            owned = owns_root(path) is True
        except OSError, TypeError, ValueError:
            owned = False
    if not owned:
        return policy_rejection(
            "QMA_DAEMON_ROOT",
            "caller is not the OS owner of the daemon root",
            root=str(path),
        )
    held = read_host_control_token(path)
    if not is_refusal(held):
        return policy_rejection(
            "recover-control",
            "host_control is still readable; use rotate-control",
            root=str(path),
        )
    live = _live_writer_pid(path)
    if live is not None:
        return policy_rejection(
            "recover-control",
            "daemon is live; stop first then recover-control",
            pid=live,
        )
    stale = path / DAEMON_LOCK_NAME
    if stale.is_file():
        with contextlib.suppress(OSError):
            stale.unlink()
    composed = DaemonProcess.compose(
        path,
        machine=machine,
        boot_epoch_id=boot_epoch_id,
        bind_port=0,
        plugins_root=plugins_root,
        plugin_load_configs=plugin_load_configs,
        log_handler=log_handler,
        bootstrap=False,
    )
    if is_refusal(composed):
        return composed
    process = composed.value
    try:
        if process.bound is not None:
            return policy_rejection(
                "recover-control",
                "recover-control must not bind 8765",
            )
        return process.recover_control(owns_root=owns_root)
    finally:
        process.close()


_QMB_SQLITE_TABLE_DENY: Final[frozenset[str]] = frozenset(
    {"qmb_jsonl", "qmb_ledger", "qmb_run_ledger", "ct32"}
)


class _ProcessGate:
    """In-process singleton — at most one composed DaemonProcess."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.holder: DaemonProcess | None = None


_process_gate = _ProcessGate()


@dataclass(frozen=True, slots=True)
class BoundListener:
    """Loopback CT-40 listener after asyncio bind. Not a second wire schema."""

    host: str
    port: int
    loopback: bool
    websocket_url_prefix: str
    query_url_prefix: str
    authentication_required: bool
    schema_owner: str = WIRE_VOCABULARY_OWNER
    http_experiment_service: bool = HTTP_EXPERIMENT_SERVICE_MINTED


class DaemonProcess:
    """One asyncio process: loopback listener + sole sqlite writer + pack roster."""

    def __init__(
        self,
        *,
        substrate: PersistenceSubstrate,
        roster: DeskPluginRoster,
        posture: ListenerPosture,
        bind_port: int,
        journal: AuthoritativeJournal,
        experiments: ExperimentSpecService,
        task_graphs: TaskGraphStateService,
    ) -> None:
        self._substrate = substrate
        self._roster = roster
        self._posture = posture
        self._bind_port = bind_port
        self._journal = journal
        self._experiments = experiments
        self._task_graphs = task_graphs
        self._server: asyncio.Server | None = None
        self._bound: BoundListener | None = None
        self._accepted = 0
        self._closed = False
        self._operator_logger = configure_daemon_logging()
        self._diagnosis = DiagnosisQueryService()
        self._host_control: HostControlChannel | None = None
        self._variables = GovernedVariableRegistry.with_builtins()
        self._local_operator: LocalOperatorLive | None = None
        self._pairing_ws = PairingWsRegistry()

    @classmethod
    def compose(
        cls,
        root: Path | str,
        *,
        machine: str,
        boot_epoch_id: str,
        listener: ListenerBindConfig | None = None,
        bind_port: object = 0,
        plugins_root: Path | None = None,
        plugin_load_configs: Mapping[str, Mapping[str, object]] | None = None,
        world: World = World.LIVE,
        log_handler: logging.Handler | None = None,
        bootstrap: bool = True,
    ) -> Result[DaemonProcess]:
        """Compose the daemon from existing modules. Does not mint a new COMP.

        ``bootstrap=False`` is the recover-control one-shot: load an existing
        ``local_operator`` and do not mint a principal.
        """
        if COMP_EXP_MINTED or SIXTH_APPLICATION_MINTED or HTTP_EXPERIMENT_SERVICE_MINTED:
            return policy_rejection(
                "daemon_runtime",
                "a sixth application, COMP-EXP, or HTTP experiment service is not minted "
                "(FR-W01; DEC-0269)",
            )
        if isinstance(bind_port, bool) or not isinstance(bind_port, int) or bind_port < 0:
            return invalid_input(
                "bind_port",
                "bind_port must be a non-negative int (0 selects an ephemeral port)",
                given=repr(bind_port),
            )
        port = bind_port

        if listener is None:
            created = ListenerBindConfig.try_create()
            if is_refusal(created):
                return created
            bind_config = created.value
        else:
            bind_config = listener

        posture = validate_listener_startup(bind_config)
        if is_refusal(posture):
            return posture

        with _process_gate.lock:
            holder = _process_gate.holder
            if holder is not None and not holder._closed:
                return policy_rejection(
                    "daemon_runtime",
                    "exactly one Python asyncio daemon process may run; a second "
                    "daemon runtime is refused (FR-W09; FR-W01; FR-Q22; AD-4)",
                    holder_root=str(holder.root),
                    attempted_root=str(root),
                )

            opened = PersistenceSubstrate.open(
                root,
                machine=machine,
                boot_epoch_id=boot_epoch_id,
                world=world,
            )
            if is_refusal(opened):
                return opened
            substrate = opened.value

            journal_bound = AuthoritativeJournal.bind(
                substrate,
                clock=InjectedUtcClock(boot_epoch_id),
            )
            if is_refusal(journal_bound):
                substrate.close()
                return journal_bound
            journal = journal_bound.value

            lineage_writer = WriterId.try_create(
                machine, "authoring", "experiment-lineage", boot_epoch_id
            )
            if is_refusal(lineage_writer):
                journal.close()
                substrate.close()
                return lineage_writer

            experiments = ExperimentSpecService(
                writer=lineage_writer.value,
                ledgers=ExperimentLedgerStore(_journal=journal),
            )
            restored = experiments.bind_durable(
                sqlite=substrate.sqlite,
                journal=journal,
            )
            if is_refusal(restored):
                journal.close()
                substrate.close()
                return restored

            task_graphs = TaskGraphStateService()
            restored_graphs = task_graphs.bind_durable(
                sqlite=substrate.sqlite,
                journal=journal,
            )
            if is_refusal(restored_graphs):
                journal.close()
                substrate.close()
                return restored_graphs

            roster = DeskPluginRoster(
                plugins_root=plugins_root,
                plugin_load_configs=plugin_load_configs,
            )
            roster.backtesting.bind_experiments(experiments)
            activated = roster.activate(
                principal=PrincipalClass.OPERATOR,
                correlation_id=f"daemon-process:{boot_epoch_id}",
            )
            if is_refusal(activated):
                journal.close()
                substrate.close()
                return activated

            process = cls(
                substrate=substrate,
                roster=roster,
                posture=posture.value,
                bind_port=port,
                journal=journal,
                experiments=experiments,
                task_graphs=task_graphs,
            )
            process._bind_operator_logger(
                boot_epoch_id=boot_epoch_id,
                handler=log_handler,
            )
            if bootstrap:
                bootstrapped = bootstrap_first_operator(
                    process.root,
                    journal=process.journal,
                    sqlite=process.sqlite,
                )
                if is_refusal(bootstrapped):
                    process._closed = True
                    process._journal.close()
                    process._substrate.close()
                    return bootstrapped
                process._local_operator = bootstrapped.value
            else:
                existing = load_local_operator(process.sqlite)
                if existing is None:
                    existing = fold_local_operator_from_journal(process.journal)
                process._local_operator = existing
            process._restore_pairing_ttl()
            restored_pairing = restore_pairing_projections(process.journal, process.sqlite)
            if is_refusal(restored_pairing):
                process._closed = True
                process._journal.close()
                process._substrate.close()
                return restored_pairing
            _process_gate.holder = process
            return Ok(process)

    @property
    def root(self) -> Path:
        return self._substrate.root

    @property
    def substrate(self) -> PersistenceSubstrate:
        return self._substrate

    @property
    def sqlite(self) -> SingleSqliteWriter:
        return self._substrate.sqlite

    @property
    def journal(self) -> AuthoritativeJournal:
        return self._journal

    @property
    def variables(self) -> GovernedVariableRegistry:
        return self._variables

    @property
    def local_operator(self) -> LocalOperatorLive | None:
        return self._local_operator

    @property
    def host_control(self) -> HostControlChannel | None:
        return self._host_control

    @property
    def is_closed(self) -> bool:
        return self._closed

    @property
    def experiments(self) -> ExperimentSpecService:
        return self._experiments

    @property
    def task_graphs(self) -> TaskGraphStateService:
        return self._task_graphs

    @property
    def roster(self) -> DeskPluginRoster:
        return self._roster

    @property
    def backtesting(self) -> BacktestingService:
        return self._roster.backtesting

    @property
    def posture(self) -> ListenerPosture:
        return self._posture

    @property
    def bound(self) -> BoundListener | None:
        return self._bound

    @property
    def accepted_connections(self) -> int:
        return self._accepted

    @property
    def wire_schema_owner(self) -> str:
        return WIRE_VOCABULARY_OWNER

    @property
    def wire_schema_files(self) -> Mapping[str, str]:
        return MappingProxyType(dict(SCHEMA_FILES))

    def sqlite_connection_count(self) -> int:
        """Story 42.1: exactly one writable connection in one writer thread."""
        return self._substrate.sqlite.connection_count_evidence()

    def start_http_experiment_service(self) -> Result[None]:
        """Refused — CT-40 queries are not a COMP-EXP HTTP experiment service."""
        return policy_rejection(
            "http_experiment_service",
            "no HTTP experiment service is minted; the composed process is "
            "qma-daemon over existing CT-40 modules, not COMP-EXP (FR-W01; DEC-0269)",
            minted=HTTP_EXPERIMENT_SERVICE_MINTED,
            sixth_application=SIXTH_APPLICATION_MINTED,
        )

    def merge_qmb_jsonl(self, path: object = None) -> Result[None]:
        """Refused — QMB JSONL stays WriterId-scoped and is never merged here."""
        return policy_rejection(
            "qmb_jsonl",
            "QMB JSONL remains WriterId-scoped in QMB; it is not merged into "
            "the daemon sqlite store (NFR-W04; DEC-0305)",
            merged=QMB_JSONL_MERGED_INTO_SQLITE,
            path=repr(path),
            qmb_owned=sorted(QMB_OWNED_CONCERNS),
        )

    def write_hub(self, *_args: object, **_kwargs: object) -> Result[None]:
        """Refused — QMA never writes the B-15 hub (candidate refs only)."""
        _ = QMA_WRITES_HUB
        return refuse_qma_hub_write(act="hub_write", given=_kwargs.get("ref"))

    def hub_publish(self, *_args: object, **_kwargs: object) -> Result[None]:
        """Refused — hub_publish is human."""
        return refuse_hub_publish_from_qma()

    def promote(self, *_args: object, **_kwargs: object) -> Result[None]:
        """Refused — this epic grants no promotion authority."""
        _ = EPIC_PROMOTION_AUTHORITY
        return refuse_qma_promotion(given=_kwargs.get("artifact", "promote"))

    def import_qmb_package(self) -> Result[None]:
        """The QMB door stays a runtime interaction — no package-import edge."""
        return refuse_qmb_import_edge()

    def take_qmb_owned_concern(self, concern: str) -> Result[None]:
        """QMB keeps its run ledger, parallelism, and artifact contract."""
        return refuse_qmb_owned_concern(concern=concern)

    def _bind_operator_logger(
        self,
        *,
        boot_epoch_id: str,
        handler: logging.Handler | None,
    ) -> None:
        """Stdlib JSON-lines only — not a journal and not a new sqlite class."""
        self._operator_logger = configure_daemon_logging(handler=handler)
        self.emit_operator_event(
            "daemon.composed",
            correlation_id=f"daemon-process:{boot_epoch_id}",
        )

    def emit_operator_event(
        self,
        event: str,
        *,
        correlation_id: str,
        level: int = logging.INFO,
        instance_id: str | None = None,
        op_id: str | None = None,
        logical_invocation_id: str | None = None,
        graph_run_id: str | None = None,
        **extra: object,
    ) -> Result[None]:
        """Emit one operator JSON-line for a public operation or Task Graph run."""
        return write_operator_json_line(
            self._operator_logger,
            level,
            event,
            correlation_id=correlation_id,
            instance_id=instance_id,
            op_id=op_id,
            logical_invocation_id=logical_invocation_id,
            graph_run_id=graph_run_id,
            **extra,
        )

    def mint_fourth_observability_comp(self) -> Result[None]:
        """Refused — operator logs are not a fourth observability product."""
        return refuse_fourth_observability_comp()

    def mint_operator_log_sqlite_class(self) -> Result[None]:
        """Refused — operator logs are not a new sqlite class."""
        return refuse_operator_log_sqlite_class()

    def extend_qmn_failures_md(self) -> Result[None]:
        """Refused — qmn/FAILURES.md stays the QMN alert allow-list."""
        return refuse_qmn_failures_extension()

    def place_typed_failure(self, *, owner: str, target_failures_md: str) -> Result[str]:
        """Mini-app first ids stay in the owning package FAILURES.md."""
        return place_typed_failure(owner=owner, target_failures_md=target_failures_md)

    def page_qmn_alert_with_mini_app_failure(self, failure_id: object) -> Result[None]:
        """Refused — a pack cannot page the node with a mini-app failure."""
        return page_qmn_alert_with_mini_app_failure(failure_id)

    def emit_telemetry_from_hook(
        self,
        raw: Mapping[str, object],
        *,
        source: HookSource | str,
        authored_by: str,
    ) -> Result[TelemetryRecord]:
        """Refused for mission/model/agent authors — telemetry is harness-authored."""
        return emit_telemetry_from_hook(
            TelemetryStore(),
            raw,
            source=source,
            authored_by=authored_by,
        )

    def mint_third_logger(self, name: object = None) -> Result[None]:
        """Refused — QMB LogSink may remain; no third daemon logger is minted."""
        return mint_third_logger(name)

    def fingerprint_operator_log(self, payload: object = None) -> Result[None]:
        """Refused — operator logs do not enter fp1 identity."""
        return refuse_operator_log_fp1(payload)

    def diagnose_failure(
        self,
        *,
        correlation_id: str,
        refusal: object,
        healthy: bool,
        log_line: Mapping[str, object],
        failure_class: object = None,
        job_handle: object = None,
        view_reason: str | None = None,
    ) -> Result[Diagnosis]:
        """Headless diagnosis of a failed public operation or Task Graph run."""
        from qmf.core.refusal import TypedRefusal  # noqa: PLC0415

        if not isinstance(refusal, TypedRefusal):
            return policy_rejection(
                "refusal",
                "how-it-failed includes a typed refusal (FR-PG-20)",
                given=type(refusal).__name__,
            )
        return self._diagnosis.observe(
            correlation_id=correlation_id,
            refusal=refusal,
            healthy=healthy,
            log_line=log_line,
            failure_class=failure_class,
            job_handle=job_handle,
            view_reason=view_reason,
        )

    def get_diagnosis(self, correlation_id: str) -> Result[Diagnosis]:
        """CT-40 ``get_diagnosis`` query — join on correlation_id, never fp1."""
        return self._diagnosis.query(correlation_id)

    def claim_diagnosis_query_at_inspect_sha(self, existed: object) -> Result[bool]:
        """Claiming this diagnosis query existed at 34c148b fails."""
        return claim_diagnosis_query_at_inspect_sha(existed)

    def mint_diagnosis_sqlite_class(self) -> Result[None]:
        """Refused — diagnosis is not a fourth store."""
        return refuse_diagnosis_fourth_store(
            minted=DIAGNOSIS_SQLITE_CLASS_MINTED,
            on_closed_list="diagnosis" in self.sqlite_table_names(),
        )

    def use_qmn_alert_failure_class(self, value: object) -> Result[None]:
        """Refused — QMN alert failure_class is a different noun."""
        return refuse_qmn_alert_failure_class(given=repr(value))

    def request_stop(self) -> None:
        """Stop after the current host-control handler finishes."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            self.close()
            return
        loop.call_soon(self.close)

    def host_status_snapshot(self) -> Mapping[str, object]:
        """Lock, pid, CT-40 bind, operator/TTL/record-id presence. Never secrets."""
        bound = self._bound
        bind = None if bound is None else f"{bound.host}:{bound.port}"
        record_ids = pairing_status_record_ids(self._substrate.sqlite)
        return MappingProxyType(
            {
                "lock": "held" if self._substrate.lock_held else "free",
                "pid": os.getpid(),
                "bind": bind,
                "operator_established": self._local_operator is not None,
                "ttl": self._variables.pairing_ttl_status(),
                "pending_record_ids": record_ids["pending_record_ids"],
                "bound_record_ids": record_ids["bound_record_ids"],
            }
        )

    def rotate_control(self) -> Result[Mapping[str, object]]:
        """Remint host_control while the current token is held (T-H-01)."""
        rotated = rotate_local_operator_control(
            self.root,
            journal=self._journal,
            sqlite=self._substrate.sqlite,
        )
        if is_refusal(rotated):
            return rotated
        result = rotated.value
        self._local_operator = result.live
        channel = self._host_control
        if channel is not None:
            channel.replace_expected_token(result.token)
        return Ok(
            MappingProxyType(
                {
                    "rotated": True,
                    "local_operator": "unchanged",
                    "principal_id": result.live.principal_id,
                    "host_control_fp1": result.live.host_control_fp1,
                    "previous_host_control_fp1": result.previous_host_control_fp1,
                    "writer": "host.rotate-control",
                }
            )
        )

    def recover_control(self, *, owns_root: object = None) -> Result[Mapping[str, object]]:
        """One-shot recover writer. Does not bind 8765 (C1 / T-H-02)."""
        if self._bound is not None or self._server is not None or self._host_control is not None:
            return policy_rejection(
                "recover-control",
                "daemon is live; stop first then recover-control",
            )
        recovered = recover_local_operator_control(
            self.root,
            journal=self._journal,
            sqlite=self._substrate.sqlite,
            owns_root=owns_root,
        )
        if is_refusal(recovered):
            return recovered
        result = recovered.value
        self._local_operator = result.live
        return Ok(
            MappingProxyType(
                {
                    "recovered": True,
                    "local_operator": "unchanged",
                    "principal_id": result.live.principal_id,
                    "host_control_fp1": result.live.host_control_fp1,
                    "previous_host_control_fp1": result.previous_host_control_fp1,
                    "writer": "host.recover-control",
                    "bound_8765": False,
                }
            )
        )

    def configure_pairing_ttl(self, duration: object) -> Result[Mapping[str, object]]:
        """Sole writer of ``registry:pairing.session_ttl`` (AM-10; GAP-0109)."""
        written = self._variables.configure_pairing_session_ttl(
            duration,
            journal=self._journal,
        )
        if is_refusal(written):
            return written
        self._substrate.sqlite.execute(
            "INSERT OR REPLACE INTO daemon_meta (key, value) VALUES (?, ?)",
            (PAIRING_SESSION_TTL_META_KEY, written.value),
        )
        return Ok(
            MappingProxyType(
                {
                    "registry_key": PAIRING_SESSION_TTL_REGISTRY_KEY,
                    "ttl": "set",
                    "writer": "host.configure.pairing-ttl",
                }
            )
        )

    def refuse_pair_issue(self) -> Result[None]:
        """Missing-TTL refuse gate for ``/pair/start`` and ``/pair/confirm`` issue."""
        return self._variables.refuse_pair_issue()

    def pair_pending(self, code: object) -> Result[Mapping[str, object]]:
        """Host-control pair: confirm pending by code. Does not mint a browser proof."""
        stamps = self._journal.stamp_durable()
        now_ns = None if is_refusal(stamps) else stamps.value.recorded_at
        confirmed = confirm_pairing_pending_by_code(
            journal=self._journal,
            sqlite=self.sqlite,
            code=code,
            now_ns=now_ns,
        )
        if is_refusal(confirmed):
            return confirmed
        live = confirmed.value
        return Ok(
            MappingProxyType(
                {
                    "pairing_record_id": live.pairing_record_id,
                    "confirmed": True,
                }
            )
        )

    def pair_revoke(
        self,
        origin: object = None,
        pairing_record_id: object = None,
    ) -> Result[Mapping[str, object]]:
        """Host-control pair revoke: origin barrier or one pairing_record_id."""
        origin_given = isinstance(origin, str) and origin.strip() != ""
        session_given = isinstance(pairing_record_id, str) and pairing_record_id.strip() != ""
        if origin_given and session_given:
            return policy_rejection(
                "revoke",
                "use --origin or --session, not both",
            )
        if origin_given:
            revoked = origin_revoke_pairing(
                journal=self._journal,
                sqlite=self.sqlite,
                origin=origin,
                ws_registry=self._pairing_ws,
            )
        elif session_given:
            revoked = session_revoke_pairing(
                journal=self._journal,
                sqlite=self.sqlite,
                pairing_record_id=pairing_record_id,
                ws_registry=self._pairing_ws,
            )
        else:
            return invalid_input(
                "revoke",
                "qmb host pair revoke requires --origin or --session",
            )
        if is_refusal(revoked):
            return revoked
        return Ok(MappingProxyType(dict(revoked.value)))

    def _restore_pairing_ttl(self) -> None:
        folded = fold_pairing_ttl_from_journal(self._journal)
        if folded is not None:
            self._variables.load_pairing_session_ttl(folded)
            return
        rows = self._substrate.sqlite.execute(
            "SELECT value FROM daemon_meta WHERE key = ?",
            (PAIRING_SESSION_TTL_META_KEY,),
        )
        if not rows:
            return
        cached = rows[0][0]
        if isinstance(cached, str) and cached.strip():
            self._variables.load_pairing_session_ttl(cached)

    def claim_host_control_at_inspect_sha(self, existed: object) -> Result[bool]:
        """Claiming ``qmb host`` / host-control existed at 34c148be fails."""
        return claim_host_control_existed_at_inspect_sha(existed)

    def claim_envelope_types_absent_at_inspect_sha(self, absent: object) -> Result[bool]:
        """Claiming Envelope / GrantRecord / product_session types were absent fails."""
        return claim_types_absent_at_inspect_sha(absent)

    async def bind(self) -> Result[BoundListener]:
        """Bind the loopback listener. Does not start an HTTP experiment service."""
        if self._closed:
            return policy_rejection(
                "daemon_runtime",
                "composed daemon process is closed",
            )
        if self._bound is not None and self._server is not None:
            attached = await self._bind_host_control()
            if is_refusal(attached):
                return attached
            return Ok(self._bound)
        try:
            server = await asyncio.start_server(
                self._handle_client,
                host=self._posture.host,
                port=self._bind_port,
            )
        except OSError as exc:
            return storage_failure(
                f"could not bind the loopback listener: {exc}",
                context={
                    "field": "listener",
                    "host": self._posture.host,
                    "port": self._bind_port,
                },
            )
        sockets = server.sockets
        if not sockets:
            server.close()
            await server.wait_closed()
            return storage_failure(
                "loopback listener bound with no sockets",
                context={"field": "listener", "host": self._posture.host},
            )
        sockname = sockets[0].getsockname()
        bound = BoundListener(
            host=str(sockname[0]),
            port=int(sockname[1]),
            loopback=self._posture.loopback,
            websocket_url_prefix=self._posture.websocket_url_prefix,
            query_url_prefix=self._posture.query_url_prefix,
            authentication_required=self._posture.authentication_required,
        )
        self._server = server
        self._bound = bound
        attached = await self._bind_host_control()
        if is_refusal(attached):
            server.close()
            await server.wait_closed()
            self._server = None
            self._bound = None
            return attached
        self.emit_operator_event(
            "daemon.listener_bound",
            correlation_id=f"daemon-listener:{bound.host}:{bound.port}",
        )
        return Ok(bound)

    async def _bind_host_control(self) -> Result[None]:
        """Bind the token-gated host-control channel outside port 8765."""
        existing = self._host_control
        if existing is not None and existing.bound is not None:
            return Ok(None)
        channel = HostControlChannel(
            self.root,
            status=self.host_status_snapshot,
            on_stop=self.request_stop,
            on_configure_pairing_ttl=self.configure_pairing_ttl,
            on_rotate_control=self.rotate_control,
            on_pair=self.pair_pending,
            on_pair_revoke=self.pair_revoke,
        )
        bound = await channel.bind()
        if is_refusal(bound):
            return bound
        if bound.value.port == CT40_BIND_PORT:
            await channel.aclose()
            return policy_rejection(
                "host_control",
                "host-control must bind outside port 8765 (AM-15)",
                port=bound.value.port,
                ct40_port=CT40_BIND_PORT,
            )
        self._host_control = channel
        return Ok(None)

    async def serve(self) -> Result[None]:
        """Bind if needed and serve until cancelled. One inbound listener."""
        bound = await self.bind()
        if is_refusal(bound):
            return bound
        server = self._server
        if server is None:
            return policy_rejection("listener", "loopback listener is not bound")
        try:
            async with server:
                await server.serve_forever()
        except asyncio.CancelledError:
            return Ok(None)
        return Ok(None)

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        self._accepted += 1
        try:
            while not reader.at_eof():
                chunk = await reader.read(65536)
                if not chunk:
                    break
        finally:
            if not writer.is_closing():
                writer.close()
            await writer.wait_closed()

    def sqlite_table_names(self) -> frozenset[str]:
        rows = self._substrate.sqlite.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return frozenset(str(row[0]) for row in rows)

    def qmb_jsonl_tables_present(self) -> frozenset[str]:
        """Names that would mean QMB JSONL was merged into daemon sqlite."""
        return self.sqlite_table_names() & _QMB_SQLITE_TABLE_DENY

    def snapshot(self) -> Mapping[str, object]:
        bound = self._bound
        return MappingProxyType(
            {
                "component": "COMP-QMA-DAEMON",
                "sixth_application": SIXTH_APPLICATION_MINTED,
                "comp_exp": COMP_EXP_MINTED,
                "http_experiment_service": HTTP_EXPERIMENT_SERVICE_MINTED,
                "qmb_jsonl_merged": QMB_JSONL_MERGED_INTO_SQLITE,
                "wire_schema_owner": WIRE_VOCABULARY_OWNER,
                "wire_schema_files": dict(SCHEMA_FILES),
                "default_bind_host": DEFAULT_BIND_HOST,
                "listener_loopback": self._posture.loopback,
                "listener_host": self._posture.host,
                "sqlite_connections": self.sqlite_connection_count(),
                "sqlite_thread": self._substrate.sqlite.thread_name,
                "sqlite_tables": sorted(self.sqlite_table_names()),
                "experiment_sqlite_tables": sorted(
                    self.sqlite_table_names() & EXPERIMENT_SQLITE_TABLES
                ),
                "experiment_product_truth": self._experiments.product_truth,
                "task_graph_state_tables": sorted(
                    self.sqlite_table_names() & TASK_GRAPH_STATE_SQLITE_TABLES
                ),
                "task_graph_state_product_truth": self._task_graphs.product_truth,
                "occupancy_table_minted": self._task_graphs.occupancy_table_minted,
                "second_scheduler_minted": self._task_graphs.second_scheduler_minted,
                "pack_ids": list(self._roster.loader.loaded_ids()),
                "expected_pack_ids": list(DESK_PLUGIN_PACK_IDS),
                "analysis_backtest_plugin_id": self.backtesting.plugin_id,
                "expected_analysis_backtest_plugin_id": ANALYSIS_BACKTEST_PLUGIN_ID,
                "qmb_jsonl_tables": sorted(self.qmb_jsonl_tables_present()),
                "backtesting_service": type(self.backtesting).__name__,
                "qmb_door_transport": type(self.backtesting.transport).__name__,
                "qmb_door_production": bool(
                    getattr(self.backtesting.transport, "production", False)
                ),
                "scheduling_authority": self.backtesting.scheduling_authority,
                "parallelism": self.backtesting.parallelism,
                "backtest_state": self.backtesting.backtest_state,
                "bound_host": None if bound is None else bound.host,
                "bound_port": None if bound is None else bound.port,
                "operator_json_lines": True,
                "operator_logs_are_journal": not LOGS_ARE_NOT_JOURNALS,
                "operator_logs_enter_fp1": LOGS_ENTER_FP1_IDENTITY,
                "fourth_observability_comp": FOURTH_OBSERVABILITY_COMP_MINTED,
                "operator_log_sqlite_class": OPERATOR_LOG_SQLITE_CLASS_MINTED,
                "qmn_failures_extended": QMN_FAILURES_MD_EXTENDED,
                "telemetry_store_remains": TELEMETRY_STORE_REMAINS_TRACE_METRIC_PLANE,
                "otel_export_port_only": OTEL_REMAINS_EXPORT_PORT_ONLY,
                "diagnosis_query": True,
                "diagnosis_existed_at_inspect_sha": DIAGNOSIS_EXISTED_AT_INSPECT_SHA,
                "diagnosis_sqlite_class": DIAGNOSIS_SQLITE_CLASS_MINTED,
                "qmn_alert_failure_class_is_kit": QMN_FAILURES_MD_EXTENDED_BY_KIT,
                "logs_remain_logs": LOGS_REMAIN_LOGS,
                "qmb_logsink_may_remain": QMB_LOGSINK_MAY_REMAIN,
                "third_logger_minted": THIRD_LOGGER_MINTED,
                "host_control_is_ct40": HOST_CONTROL_IS_CT40,
                "host_control_on_ct40_port": HOST_CONTROL_ON_CT40_PORT,
                "host_control_existed_at_inspect_sha": HOST_CONTROL_EXISTED_AT_INSPECT_SHA,
                "host_control_port": None
                if self._host_control is None or self._host_control.bound is None
                else self._host_control.bound.port,
                "start_orchestrates_missions": START_ORCHESTRATES_MISSIONS,
                "start_grants": START_GRANTS,
                "start_starts_qmn": START_STARTS_QMN,
                "browser_spawns_python": BROWSER_SPAWNS_PYTHON,
                "stop_cancels_qmn": STOP_CANCELS_QMN,
                "stop_stops_remote": STOP_STOPS_REMOTE,
            }
        )

    def close(self) -> None:
        """Release the listener sockets and the sole-writer substrate."""
        channel = self._host_control
        self._host_control = None
        if channel is not None:
            channel.close()
        server = self._server
        self._server = None
        if server is not None:
            server.close()
        self._release()

    async def aclose(self) -> None:
        channel = self._host_control
        self._host_control = None
        if channel is not None:
            await channel.aclose()
        server = self._server
        self._server = None
        if server is not None:
            server.close()
            await server.wait_closed()
        self._release()

    def _release(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._bound = None
        self._journal.close()
        closer = getattr(self.backtesting.transport, "close", None)
        try:
            if callable(closer):
                closer()
        finally:
            self._substrate.close()
            with _process_gate.lock:
                if _process_gate.holder is self:
                    _process_gate.holder = None

    def __enter__(self) -> DaemonProcess:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
