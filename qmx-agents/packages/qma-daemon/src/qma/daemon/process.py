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
import base64
import contextlib
import ctypes
import hashlib
import json
import logging
import os
import struct
import subprocess
import sys
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, cast
from urllib.parse import urlsplit

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
from qma.daemon.bus.mailbox import MailboxStore
from qma.daemon.bus.mailbox_query import (
    LIST_MAILBOX_HTTP_PATH,
    handle_list_mailbox_query,
    query_string_to_args,
)
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
from qma.daemon.host_control.local_operator import (
    LOCAL_OPERATOR_PRINCIPAL_ID,
    fold_local_operator_from_journal,
)
from qma.daemon.http_pair import (
    PairHttpDeps,
    PairHttpRequest,
    PairHttpResponse,
    handle_pair_http,
    header_value,
    is_host_control_http,
    is_websocket_upgrade,
)
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
    PairingWsHandle,
    PairingWsRegistry,
    authenticate_http_pairing_bearer,
    authenticate_ws_pairing_upgrade,
    confirm_pairing_pending_by_code,
    is_daemon_http_origin,
    origin_revoke_pairing,
    pairing_status_record_ids,
    redact_pairing_access_log,
    restore_pairing_projections,
    session_revoke_pairing,
)
from qma.daemon.persistence.sqlite_writer import SingleSqliteWriter
from qma.daemon.persistence.substrate import PersistenceSubstrate
from qma.daemon.plugins.packs import DeskPluginRoster
from qma.daemon.sessions.product_session import ProductSessionService
from qma.daemon.taskgraph.projection import (
    TASK_GRAPH_STATE_SQLITE_TABLES,
    TaskGraphStateService,
)
from qma.daemon.telemetry.store import TelemetryStore
from qma.wire.initialize import (
    JSONRPC_VERSION,
    InitializeParams,
    LiveProducerRegistry,
    WireConnection,
)
from qma.wire.list_mailbox import LIST_MAILBOX_CAPABILITY, MailboxSnapshot
from qma.wire.listener import (
    DEFAULT_BIND_HOST,
    PAIR_CONFIRM_PATH,
    PAIR_RENEW_PATH,
    PAIR_START_PATH,
    ListenerBindConfig,
    ListenerPosture,
    is_am01_cors_route,
    selected_websocket_subprotocol,
    validate_listener_startup,
)
from qma.wire.schemas import SCHEMA_FILES
from qma.wire.send_message import parse_send_message_payload
from qma.wire.vocabulary import WIRE_VOCABULARY_OWNER, WireCommand
from qmf.core import Ok, RefusalCategory, Result, World, WriterId, is_ok, is_refusal
from qmf.core.refusal import TypedRefusal
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
_MAX_HTTP_HEAD: Final[int] = 65536
_MAX_HTTP_BODY: Final[int] = 65536
_WS_ACCEPT_GUID: Final[str] = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_HTTP_REASONS: Final[Mapping[int, str]] = MappingProxyType(
    {
        101: "Switching Protocols",
        200: "OK",
        204: "No Content",
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
    }
)
_PAIR_POST_PATHS: Final[frozenset[str]] = frozenset(
    {PAIR_START_PATH, PAIR_CONFIRM_PATH, PAIR_RENEW_PATH}
)
_WS_OP_TEXT: Final[int] = 0x1
_WS_OP_CLOSE: Final[int] = 0x8
_WS_OP_PING: Final[int] = 0x9
_WS_OP_PONG: Final[int] = 0xA
_WS_MAX_BUFFER: Final[int] = 1_048_576
_JSONRPC_APP_ERROR: Final[int] = -32000
_JSONRPC_PARSE_ERROR: Final[int] = -32700
_JSONRPC_INVALID_REQUEST: Final[int] = -32600
_JSONRPC_METHOD_NOT_FOUND: Final[int] = -32601


def _ws_accept_key(key: str) -> str:
    digest = hashlib.sha1((key.strip() + _WS_ACCEPT_GUID).encode("ascii")).digest()  # noqa: S324
    return base64.b64encode(digest).decode("ascii")


def _encode_ws_frame(
    payload: bytes,
    *,
    opcode: int = _WS_OP_TEXT,
    mask: bytes | None = None,
) -> bytes:
    header = bytearray()
    header.append(0x80 | (opcode & 0x0F))
    length = len(payload)
    masked = mask is not None
    flag = 0x80 if masked else 0x00
    if length < 126:
        header.append(flag | length)
    elif length < 65536:
        header.append(flag | 126)
        header.extend(struct.pack("!H", length))
    else:
        header.append(flag | 127)
        header.extend(struct.pack("!Q", length))
    if mask is None:
        return bytes(header) + payload
    header.extend(mask)
    masked_payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
    return bytes(header) + masked_payload


def _decode_ws_frame(buf: bytes) -> tuple[int, bytes, bytes] | None:
    if len(buf) < 2:
        return None
    opcode = buf[0] & 0x0F
    masked = (buf[1] & 0x80) != 0
    length = buf[1] & 0x7F
    offset = 2
    if length == 126:
        if len(buf) < 4:
            return None
        length = struct.unpack("!H", buf[2:4])[0]
        offset = 4
    elif length == 127:
        if len(buf) < 10:
            return None
        length = struct.unpack("!Q", buf[2:10])[0]
        offset = 10
    mask = b""
    if masked:
        if len(buf) < offset + 4:
            return None
        mask = buf[offset : offset + 4]
        offset += 4
    if len(buf) < offset + length:
        return None
    payload = buf[offset : offset + length]
    if masked:
        payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
    return opcode, payload, buf[offset + length :]


def _jsonrpc_result(req_id: object, result: Mapping[str, object]) -> dict[str, object]:
    return {"jsonrpc": JSONRPC_VERSION, "id": req_id, "result": dict(result)}


def _jsonrpc_error(
    req_id: object,
    *,
    code: int,
    message: str,
    data: Mapping[str, object] | None = None,
) -> dict[str, object]:
    error: dict[str, object] = {"code": code, "message": message}
    if data is not None:
        error["data"] = dict(data)
    return {"jsonrpc": JSONRPC_VERSION, "id": req_id, "error": error}


def _jsonrpc_refusal(req_id: object, refusal: TypedRefusal) -> dict[str, object]:
    reason = refusal.context.get("reason")
    message = reason if isinstance(reason, str) and reason else refusal.category.value
    return _jsonrpc_error(
        req_id,
        code=_JSONRPC_APP_ERROR,
        message=message,
        data={
            "category": refusal.category.value,
            "retryability": refusal.retryability.value,
            "context": dict(refusal.context),
        },
    )


def _encode_http_response(
    status: int,
    headers: Mapping[str, str],
    body: bytes = b"",
) -> bytes:
    reason = _HTTP_REASONS.get(status, "OK")
    lines = [f"HTTP/1.1 {status} {reason}"]
    emitted = {name.casefold(): name for name in headers}
    for name, value in headers.items():
        lines.append(f"{name}: {value}")
    if "content-length" not in emitted and status != 101:
        lines.append(f"Content-Length: {len(body)}")
    if "connection" not in emitted and status != 101:
        lines.append("Connection: close")
    return ("\r\n".join(lines) + "\r\n\r\n").encode("ascii") + body


def _http_status_for_refusal(refusal: TypedRefusal) -> int:
    field = str(refusal.context.get("field", ""))
    if field in {"authorization", "authentication", "cookie", "subprotocol"}:
        return 401
    if refusal.category is RefusalCategory.INVALID_INPUT:
        return 400
    if refusal.category is RefusalCategory.UNAVAILABLE_DEPENDENCY:
        return 503
    return 403


def _refusal_http_body(refusal: TypedRefusal) -> bytes:
    redacted = redact_pairing_access_log(dict(refusal.context))
    context: dict[str, object]
    if isinstance(redacted, dict):
        raw = cast("dict[object, object]", redacted)
        context = {str(key): item for key, item in raw.items()}
    else:
        context = {}
    payload: dict[str, object] = {
        "ok": False,
        "refusal": {
            "category": refusal.category.value,
            "retryability": refusal.retryability.value,
            "context": context,
        },
    }
    return json.dumps(payload, ensure_ascii=True).encode("utf-8")


def _cors_headers_for_origin(origin: str | None) -> dict[str, str]:
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Credentials": "false",
        "Vary": "Origin",
    }
    if origin is not None and origin != "*" and not is_daemon_http_origin(origin):
        headers["Access-Control-Allow-Origin"] = origin
    return headers


async def _read_http_request(
    reader: asyncio.StreamReader,
) -> tuple[str, str, str | None, dict[str, str], bytes] | None:
    try:
        head = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=5.0)
    except TimeoutError, asyncio.IncompleteReadError, asyncio.LimitOverrunError:
        return None
    if not head or len(head) > _MAX_HTTP_HEAD:
        return None
    text = head.decode("iso-8859-1")
    request_line, _, rest = text.partition("\r\n")
    parts = request_line.split()
    if len(parts) < 2:
        return None
    method = parts[0].strip().upper()
    target = parts[1]
    if method == "" or not target.startswith("/"):
        return None
    headers: dict[str, str] = {}
    for line in rest.split("\r\n"):
        if line in {"", "\r"}:
            continue
        name, sep, value = line.partition(":")
        if sep == "":
            return None
        headers[name.strip()] = value.strip()
    split = urlsplit(target)
    path = split.path or "/"
    query = split.query if split.query else None
    length_raw = header_value(headers, "Content-Length")
    body = b""
    if length_raw is not None:
        try:
            length = int(length_raw)
        except ValueError:
            return None
        if length < 0 or length > _MAX_HTTP_BODY:
            return None
        if length > 0:
            try:
                body = await asyncio.wait_for(reader.readexactly(length), timeout=5.0)
            except TimeoutError, asyncio.IncompleteReadError:
                return None
    return method, path, query, headers, body


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
        self._product_sessions = ProductSessionService(
            journal=journal,
            sqlite=substrate.sqlite,
        )
        self._mailboxes = MailboxStore(
            _journal=journal,
            _sessions=self._product_sessions,
        )
        self._live_producers = LiveProducerRegistry()
        self._initialize_capabilities: dict[str, Mapping[str, object]] = {}

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
            restored_mailbox = process._mailboxes.restore_from_journal()
            if is_refusal(restored_mailbox):
                process._closed = True
                process._journal.close()
                process._substrate.close()
                return restored_mailbox
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
    def mailboxes(self) -> MailboxStore:
        return self._mailboxes

    @property
    def product_sessions(self) -> ProductSessionService:
        return self._product_sessions

    def list_mailbox(
        self,
        args: object,
        *,
        operator_principal: object,
        capabilities: object | None = None,
    ) -> Result[MailboxSnapshot]:
        """Authenticated list_mailbox snapshot. Missing capability is typed."""
        caps: object = {LIST_MAILBOX_CAPABILITY: True} if capabilities is None else capabilities
        return handle_list_mailbox_query(
            self._mailboxes,
            args,
            operator_principal=operator_principal,
            sessions=self._product_sessions,
            capabilities=caps,
        )

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
            await self._serve_bound_client(reader, writer)
        except OSError, ConnectionResetError, asyncio.IncompleteReadError:
            return
        finally:
            if not writer.is_closing():
                writer.close()
            with contextlib.suppress(OSError, ConnectionResetError):
                await writer.wait_closed()

    def _pair_http_deps(self) -> PairHttpDeps:
        ttl_result = self._variables.pairing_ttl_duration()
        ttl: object = None if is_refusal(ttl_result) else ttl_result.value
        principal = LOCAL_OPERATOR_PRINCIPAL_ID
        live = self._local_operator
        if live is not None:
            principal = live.principal_id
        stamps = self._journal.stamp_durable()
        now_ns = 0 if is_refusal(stamps) else stamps.value.recorded_at
        return PairHttpDeps(
            journal=self._journal,
            sqlite=self.sqlite,
            ttl=ttl,
            now_ns=now_ns,
            operator_principal=principal,
            ws_registry=self._pairing_ws,
        )

    def _now_ns(self) -> int | None:
        stamps = self._journal.stamp_durable()
        if is_refusal(stamps):
            return None
        return stamps.value.recorded_at

    async def _write_http(
        self,
        writer: asyncio.StreamWriter,
        status: int,
        headers: Mapping[str, str],
        body: bytes = b"",
    ) -> None:
        writer.write(_encode_http_response(status, headers, body))
        await writer.drain()

    async def _write_refusal(
        self,
        writer: asyncio.StreamWriter,
        refusal: TypedRefusal,
        *,
        origin: str | None,
    ) -> None:
        headers = _cors_headers_for_origin(origin)
        await self._write_http(
            writer,
            _http_status_for_refusal(refusal),
            headers,
            _refusal_http_body(refusal),
        )

    async def _write_pair_response(
        self,
        writer: asyncio.StreamWriter,
        response: PairHttpResponse,
    ) -> None:
        await self._write_http(writer, response.status, response.headers, response.body)

    async def _serve_bound_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        parsed = await _read_http_request(reader)
        if parsed is None:
            return
        method, path, query, headers, body = parsed
        origin = header_value(headers, "Origin")
        if is_websocket_upgrade(headers):
            await self._serve_pairing_ws(reader, writer, headers, query)
            return
        built = PairHttpRequest.try_create(
            method=method,
            path=path,
            headers=headers,
            query=query,
            body=body,
            port=CT40_BIND_PORT,
        )
        if is_refusal(built):
            await self._write_refusal(writer, built, origin=origin)
            return
        request = built.value
        if is_host_control_http(request.path, port=CT40_BIND_PORT):
            refused = policy_rejection(
                "host_control",
                "host-control stays outside port 8765 and is not AM-01 HTTP",
                path=request.path,
                ct40_port=CT40_BIND_PORT,
            )
            await self._write_refusal(writer, refused, origin=origin)
            return
        if request.method == "OPTIONS" or (
            request.method == "POST" and request.path in _PAIR_POST_PATHS
        ):
            handled = handle_pair_http(request, self._pair_http_deps())
            if is_ok(handled):
                await self._write_pair_response(writer, handled.value)
                return
            await self._write_refusal(writer, handled, origin=origin)
            return
        if is_am01_cors_route(request.path):
            authed = authenticate_http_pairing_bearer(
                self.sqlite,
                authorization=header_value(headers, "Authorization"),
                origin=origin,
                query=query,
                now_ns=self._now_ns(),
                cookie=header_value(headers, "Cookie"),
                ws_registry=self._pairing_ws,
            )
            if is_refusal(authed):
                await self._write_refusal(writer, authed, origin=origin)
                return
            if request.method == "GET" and request.path == LIST_MAILBOX_HTTP_PATH:
                record_id = authed.value.pairing_record_id
                if isinstance(record_id, str) and record_id in self._initialize_capabilities:
                    caps: object = self._initialize_capabilities[record_id]
                else:
                    caps = {LIST_MAILBOX_CAPABILITY: True}
                listed = handle_list_mailbox_query(
                    self._mailboxes,
                    query_string_to_args(request.query),
                    operator_principal=authed.value.principal_class,
                    sessions=self._product_sessions,
                    capabilities=caps,
                )
                if is_refusal(listed):
                    await self._write_refusal(writer, listed, origin=origin)
                    return
                body = json.dumps(
                    {"ok": True, "result": dict(listed.value.to_payload())},
                    ensure_ascii=True,
                ).encode("utf-8")
                await self._write_http(
                    writer,
                    200,
                    _cors_headers_for_origin(origin),
                    body,
                )
                return
            missing = policy_rejection(
                "path",
                "authenticated route is not pairing HTTP",
                path=request.path,
            )
            await self._write_http(
                writer,
                404,
                _cors_headers_for_origin(origin),
                _refusal_http_body(missing),
            )
            return
        refused = policy_rejection(
            "authentication",
            "every other HTTP method and every WebSocket authenticates before protocol bytes",
            method=request.method,
            path=request.path,
        )
        await self._write_refusal(writer, refused, origin=origin)

    async def _serve_pairing_ws(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        headers: Mapping[str, str],
        query: str | None,
    ) -> None:
        origin = header_value(headers, "Origin")
        offered = header_value(headers, "Sec-WebSocket-Protocol")
        admitted = authenticate_ws_pairing_upgrade(
            self.sqlite,
            offered_subprotocols=offered,
            origin=origin,
            now_ns=self._now_ns(),
            query=query,
            cookie=header_value(headers, "Cookie"),
            ws_registry=self._pairing_ws,
        )
        if is_refusal(admitted):
            await self._write_refusal(writer, admitted, origin=origin)
            return
        key = header_value(headers, "Sec-WebSocket-Key")
        if key is None:
            refused = policy_rejection(
                "upgrade",
                "WebSocket upgrade requires Sec-WebSocket-Key",
            )
            await self._write_refusal(writer, refused, origin=origin)
            return
        handle = PairingWsHandle(proof_fp1=admitted.value.proof_fp1, writer=writer)
        self._pairing_ws.register(handle)
        opening = _encode_http_response(
            101,
            {
                "Upgrade": "websocket",
                "Connection": "Upgrade",
                "Sec-WebSocket-Accept": _ws_accept_key(key),
                "Sec-WebSocket-Protocol": selected_websocket_subprotocol(),
            },
        )
        writer.write(opening)
        await writer.drain()
        connection = WireConnection()
        paired = connection.authenticate_pairing(
            admitted.value.pairing_record_id,
            principal_class=admitted.value.session.principal_class,
        )
        if is_refusal(paired):
            handle.close()
            return
        connection_token = f"{admitted.value.pairing_record_id}:{id(connection)}"
        buf = b""
        try:
            while not handle.closed and not reader.at_eof() and not self._closed:
                chunk = await reader.read(65536)
                if not chunk:
                    break
                buf += chunk
                if len(buf) > _WS_MAX_BUFFER:
                    break
                while True:
                    decoded = _decode_ws_frame(buf)
                    if decoded is None:
                        break
                    opcode, payload, buf = decoded
                    if opcode == _WS_OP_CLOSE:
                        writer.write(_encode_ws_frame(payload, opcode=_WS_OP_CLOSE))
                        await writer.drain()
                        return
                    if opcode == _WS_OP_PING:
                        writer.write(_encode_ws_frame(payload, opcode=_WS_OP_PONG))
                        await writer.drain()
                        continue
                    if opcode != _WS_OP_TEXT:
                        continue
                    response = self._dispatch_paired_ct40(
                        connection,
                        payload,
                        pairing_record_id=admitted.value.pairing_record_id,
                        connection_token=connection_token,
                    )
                    if response is None:
                        continue
                    writer.write(_encode_ws_frame(json.dumps(response).encode("utf-8")))
                    await writer.drain()
        finally:
            producer_id = connection.producer_id
            if producer_id is not None:
                self._live_producers.release(
                    producer_id,
                    connection_token=connection_token,
                )
            handle.close()

    def _dispatch_paired_ct40(
        self,
        connection: WireConnection,
        payload: bytes,
        *,
        pairing_record_id: str,
        connection_token: str,
    ) -> dict[str, object] | None:
        """Authenticated JSON-RPC on a paired CT-40 socket. Host-control stays off."""
        try:
            parsed_obj: object = json.loads(payload.decode("utf-8"))
        except UnicodeDecodeError, json.JSONDecodeError:
            return _jsonrpc_error(
                None,
                code=_JSONRPC_PARSE_ERROR,
                message="parse error",
            )
        if not isinstance(parsed_obj, dict):
            return _jsonrpc_error(
                None,
                code=_JSONRPC_INVALID_REQUEST,
                message="invalid request",
            )
        request = cast("dict[str, object]", parsed_obj)
        req_id = request.get("id")
        method = request.get("method")
        if method == "initialize":
            begun = connection.begin_initialize(request)
            if is_refusal(begun):
                return _jsonrpc_refusal(req_id, begun)
            params = InitializeParams.try_create(
                protocol_version=begun.value.params.get("protocolVersion"),
                capabilities=begun.value.params.get("capabilities"),
                client_producer_id=begun.value.params.get("producer_id"),
            )
            if is_refusal(params):
                return _jsonrpc_refusal(req_id, params)
            raw_caps = params.value.capabilities
            advertise = True
            if raw_caps:
                advertise = raw_caps.get(LIST_MAILBOX_CAPABILITY) is True
            completed = connection.complete_initialize(
                params.value,
                request_id=begun.value.id,
                live_producers=self._live_producers,
                connection_token=connection_token,
                advertise_pairing=advertise,
            )
            if is_refusal(completed):
                return _jsonrpc_refusal(req_id, completed)
            self._initialize_capabilities[pairing_record_id] = dict(connection.capabilities)
            return completed.value.to_dict()
        accepted = connection.accept_family_message(method)
        if is_refusal(accepted):
            return _jsonrpc_refusal(req_id, accepted)
        if method != WireCommand.SEND_MESSAGE.value:
            return _jsonrpc_error(
                req_id,
                code=_JSONRPC_METHOD_NOT_FOUND,
                message="method not found",
            )
        authorized = connection.authorize_command(WireCommand.SEND_MESSAGE.value)
        if is_refusal(authorized):
            return _jsonrpc_refusal(req_id, authorized)
        raw_params = request.get("params")
        if not isinstance(raw_params, Mapping):
            return _jsonrpc_error(
                req_id,
                code=_JSONRPC_INVALID_REQUEST,
                message="params must be an object",
            )
        send_payload: dict[str, object] = dict(cast("Mapping[str, object]", raw_params))
        if "producer_id" not in send_payload and connection.producer_id is not None:
            send_payload["producer_id"] = connection.producer_id
        parsed_send = parse_send_message_payload(send_payload)
        if is_refusal(parsed_send):
            return _jsonrpc_refusal(req_id, parsed_send)
        principal = connection.principal_class
        if principal is None:
            return _jsonrpc_error(
                req_id,
                code=_JSONRPC_APP_ERROR,
                message="unauthenticated",
            )
        sent = self._mailboxes.send_message(
            parsed_send.value,
            principal_class=principal,
            sessions=self._product_sessions,
        )
        if is_refusal(sent):
            return _jsonrpc_refusal(req_id, sent)
        return _jsonrpc_result(req_id, sent.value.to_snapshot_row().to_payload())

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
        self._pairing_ws.close_all()
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
        self._pairing_ws.close_all()
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
