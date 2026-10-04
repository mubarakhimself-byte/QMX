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
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Final, cast
from urllib.parse import urlsplit

from qma.core.operations import OperationDescriptor, public_operation_descriptors
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
    QMB_BACKTEST_TOOL_ID,
    QMB_OWNED_CONCERNS,
    refuse_qmb_import_edge,
    refuse_qmb_owned_concern,
)
from qma.core.ports.telemetry import TelemetryRecord
from qma.core.refusals import NoEnvironment
from qma.core.vocabulary.enums import EffectClass, JobHandleState, PrincipalClass, TaskMissionState
from qma.daemon.artifacts import (
    ArtifactStore,
    DestControlHandle,
    DestinationPlacement,
    InvokeTransferGate,
    StagedArtifact,
    TransferArtifactResult,
    TransferCompleteResult,
    TransferTicketStore,
    gate_invoke_until_transfer_complete,
    handle_stage_artifact_put,
    handle_transfer_artifact,
    handle_transfer_complete,
    parse_stage_content_length,
    place_dest_pulled_bytes,
    placement_from_host_configure,
    refuse_interrupted_stage_put,
)
from qma.daemon.backtest.service import BacktestingService
from qma.daemon.bootstrap_config import (
    backtest_binding,
    backtest_binding_for_instance,
    load_qmb_local_environment,
)
from qma.daemon.bus.mailbox import MailboxStore
from qma.daemon.bus.mailbox_query import (
    LIST_MAILBOX_HTTP_PATH,
    handle_list_mailbox_query,
    query_string_to_args,
)
from qma.daemon.capabilities.spawn import AgentCapabilityStore
from qma.daemon.composition import DaemonRuntimeComposition
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
from qma.daemon.envs.jobs import JobHandleService
from qma.daemon.envs.registry import ExecutionEnvironmentRegistry
from qma.daemon.envs.router import ComputeRouter
from qma.daemon.envs.runtime import RuntimeService
from qma.daemon.experiments import EXPERIMENT_SQLITE_TABLES, ExperimentSpecService
from qma.daemon.hooks.registry import HookRegistry
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
    authenticate_machine_or_worker,
    handle_pair_http,
    header_value,
    is_host_control_http,
    is_websocket_upgrade,
    parse_machine_pull_authorization,
)
from qma.daemon.journal.authoritative import AuthoritativeJournal
from qma.daemon.journal.clock import InjectedUtcClock
from qma.daemon.journal.variables import (
    ARTIFACT_STAGE_MAX_BYTES_REGISTRY_KEY,
    PAIRING_SESSION_TTL_META_KEY,
    PAIRING_SESSION_TTL_REGISTRY_KEY,
    GovernedVariableRegistry,
    fold_pairing_ttl_from_journal,
)
from qma.daemon.knowledge.service import KnowledgeService
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
    load_pairing_session,
    origin_revoke_pairing,
    pairing_status_record_ids,
    redact_pairing_access_log,
    restore_pairing_projections,
    session_revoke_pairing,
)
from qma.daemon.persistence.sqlite_writer import SingleSqliteWriter
from qma.daemon.persistence.substrate import PersistenceSubstrate
from qma.daemon.plugins.pack_ui import (
    read_pack_ui_request_record,
    restore_plugin_install_records_projection,
)
from qma.daemon.plugins.packs import DeskPluginRoster
from qma.daemon.request_runtime.agent_extensions import AgentExtensions
from qma.daemon.request_runtime.canonical_join import CanonicalJoinPlan, CanonicalRequestJoin
from qma.daemon.request_runtime.contracts import ProviderAdapter
from qma.daemon.request_runtime.daemon_bridge import AgentRequestBridge, AgentRequestPolicy
from qma.daemon.request_runtime.domain_tools import bind_daemon_tool_providers
from qma.daemon.request_runtime.experiment_authoring import ExperimentAuthoring
from qma.daemon.request_runtime.service import RequestRuntime
from qma.daemon.request_runtime.spot_state import (
    SPOT_CONTRIBUTION,
    SpotStateBinding,
    configure_spot_host_retry,
    load_spot_state_bindings,
)
from qma.daemon.request_runtime.spot_tools import spot_query_descriptor
from qma.daemon.retry import HostRetryLoop
from qma.daemon.sessions.chrome import PackUiMount, ProductSessionChrome
from qma.daemon.sessions.product_session import (
    BoundSessionGrant,
    ProductSessionService,
    accepted_invocation_binding,
)
from qma.daemon.staging.editor_draft import EditorDraftService
from qma.daemon.taskgraph.dispatcher import TaskGraphDispatcher
from qma.daemon.taskgraph.nested import NestedMissionHost
from qma.daemon.taskgraph.projection import (
    TASK_GRAPH_STATE_SQLITE_TABLES,
    TaskGraphStateService,
)
from qma.daemon.telemetry.store import TelemetryStore
from qma.daemon.tools.registry import ToolRegistry
from qma.wire.agent_request import (
    AGENT_REQUEST_CAPABILITIES,
    GET_AGENT_REQUEST_CAPABILITY,
    RESUME_AGENT_REQUEST_CAPABILITY,
    SUBMIT_AGENT_REQUEST_CAPABILITY,
    parse_cancel_agent_request,
    parse_get_agent_request,
    parse_resume_agent_request,
    parse_submit_agent_request,
    require_agent_request_capability,
)
from qma.wire.cancel_job import require_cancel_job_capability
from qma.wire.editor_draft import (
    EDITOR_DRAFT_HTTP_PATH,
    require_editor_draft_capability,
)
from qma.wire.initialize import (
    CANCEL_JOB_CAPABILITY,
    GET_EDITOR_DRAFT_HEAD_CAPABILITY,
    JSONRPC_VERSION,
    PAIRING_CAPABILITY,
    PUBLISH_EDITOR_DRAFT_CAPABILITY,
    SAVE_EDITOR_DRAFT_CAPABILITY,
    TRANSFER_ARTIFACT_CAPABILITY,
    TRANSFER_COMPLETE_CAPABILITY,
    InitializeParams,
    LiveProducerRegistry,
    WireConnection,
)
from qma.wire.invocation_envelope import (
    BoundInvocation,
    ContributionRecord,
    InstanceRecord,
    InvocationEnvelope,
    PublicCallTransport,
    compute_input_hash,
    format_utc_iso_z,
    parse_invocation_envelope,
)
from qma.wire.list_mailbox import LIST_MAILBOX_CAPABILITY, MailboxSnapshot
from qma.wire.listener import (
    CT40_WS_SUBPROTOCOL,
    DEFAULT_BIND_HOST,
    PAIR_CONFIRM_PATH,
    PAIR_RENEW_PATH,
    PAIR_START_PATH,
    PAIRING_WS_SUBPROTOCOL_PREFIX,
    ListenerBindConfig,
    ListenerPosture,
    artifacts_get_fp1,
    is_am01_cors_route,
    is_artifacts_get_path,
    parse_offered_websocket_subprotocols,
    selected_websocket_subprotocol,
    validate_listener_startup,
)
from qma.wire.pack_ui_request import (
    GET_PACK_UI_REQUEST_CAPABILITY,
    GET_PACK_UI_REQUEST_HTTP_PATH,
    PACK_UI_REQUEST_CAPABILITY,
    PackUiRequestSnapshot,
    parse_pack_ui_request,
    parse_pack_ui_request_args,
    require_pack_ui_request_capability,
)
from qma.wire.schemas import SCHEMA_FILES
from qma.wire.send_message import parse_send_message_payload
from qma.wire.stage_artifact import (
    STAGE_ARTIFACT_CAPABILITY,
    STAGE_ARTIFACT_HTTP_PATH,
    refuse_jsonrpc_stage_artifact,
    require_stage_artifact_capability,
)
from qma.wire.transfer_artifact import require_transfer_artifact_capability
from qma.wire.transfer_complete import require_transfer_complete_capability
from qma.wire.vocabulary import WIRE_VOCABULARY_OWNER, WireCommand, WireQuery
from qmf.core import Ok, RefusalCategory, Result, World, WriterId, fingerprint, is_ok, is_refusal
from qmf.core.chrono import Instant
from qmf.core.refusal import Retryability, TypedRefusal
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


def _emit_dest_control_note(writer: asyncio.StreamWriter, note: Mapping[str, object]) -> bool:
    """Write one dest-control JSON-RPC notification as a WS text frame."""
    is_closing = getattr(writer, "is_closing", None)
    if callable(is_closing) and is_closing():
        return False
    payload = json.dumps(dict(note), ensure_ascii=True).encode("utf-8")
    try:
        writer.write(_encode_ws_frame(payload))
    except ConnectionError, OSError, RuntimeError:
        return False
    return True


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


def _offered_pairing_ws(offered: str | None) -> bool:
    parsed = parse_offered_websocket_subprotocols(offered)
    if is_refusal(parsed):
        return False
    return any(token.startswith(PAIRING_WS_SUBPROTOCOL_PREFIX) for token in parsed.value)


def _offered_ct40_ws(offered: str | None) -> bool:
    parsed = parse_offered_websocket_subprotocols(offered)
    if is_refusal(parsed):
        return False
    return CT40_WS_SUBPROTOCOL in parsed.value


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
    # PUT /artifacts/stage is the AM-05 byte channel: cap is injected
    # registry:artifact.stage_max_bytes, never _MAX_HTTP_BODY (GAP-0110).
    if method == "PUT" and path == STAGE_ARTIFACT_HTTP_PATH:
        return method, path, query, headers, body
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


async def _read_stage_put_body(reader: asyncio.StreamReader, length: int) -> Result[bytes]:
    """Read exactly Content-Length bytes. Peer close or timeout is interrupt."""
    if length == 0:
        return Ok(b"")
    try:
        return Ok(await asyncio.wait_for(reader.readexactly(length), timeout=5.0))
    except TimeoutError, asyncio.IncompleteReadError:
        return refuse_interrupted_stage_put()


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
        runtime_composition: DaemonRuntimeComposition,
        variables: GovernedVariableRegistry,
    ) -> None:
        self._substrate = substrate
        self._roster = roster
        self._posture = posture
        self._bind_port = bind_port
        self._journal = journal
        self._experiments = experiments
        self._task_graphs = task_graphs
        self._runtime_composition = runtime_composition
        self._server: asyncio.Server | None = None
        self._bound: BoundListener | None = None
        self._accepted = 0
        self._closed = False
        self._operator_logger = configure_daemon_logging()
        self._diagnosis = DiagnosisQueryService()
        self._host_control: HostControlChannel | None = None
        self._variables = variables
        self._host_retry_loop = HostRetryLoop(variables=variables)
        self._local_operator: LocalOperatorLive | None = None
        self._pairing_ws = PairingWsRegistry()
        self._product_sessions = ProductSessionService(
            journal=journal,
            sqlite=substrate.sqlite,
        )
        self._product_session_chrome = ProductSessionChrome(
            sessions=self._product_sessions,
            journal=journal,
        )
        self._mailboxes = MailboxStore(
            _journal=journal,
            _sessions=self._product_sessions,
        )
        self._artifacts = ArtifactStore(
            hooks=HookRegistry(),
            journal=journal,
            durable_store=substrate.artifact_store,
        )
        self._editor_drafts = EditorDraftService(
            journal=self._journal,
            sqlite=self.sqlite,
            artifacts=self._artifacts,
            authoring_roster_root=self.root / "authoring-pack",
            authoring_lifecycle=self._roster,
        )
        self._transfers = TransferTicketStore(
            journal=journal,
            sqlite=substrate.sqlite,
            artifacts=self._artifacts,
        )
        self._live_producers = LiveProducerRegistry()
        self._initialize_capabilities: dict[str, Mapping[str, object]] = {}
        self._agent_requests: AgentRequestBridge | None = None
        self._agent_capabilities = AgentCapabilityStore()
        self._experiment_authoring: ExperimentAuthoring | None = None
        self._canonical_requests: CanonicalRequestJoin | None = None
        self._agent_instance_revisions: Mapping[str, int] = {}
        self._spot_state_bindings: Mapping[str, SpotStateBinding] = {}

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

            local_environment = load_qmb_local_environment(root)
            if is_refusal(local_environment):
                return local_environment
            environments = ExecutionEnvironmentRegistry()
            if local_environment.value is not None:
                registered_environment = environments.register_declaration(local_environment.value)
                if is_refusal(registered_environment):
                    return registered_environment

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
                authoring_roster_root=Path(root) / "authoring-pack",
                authoring_journal=journal,
                sqlite=substrate.sqlite,
            )
            variables = GovernedVariableRegistry.with_builtins()
            runtime_composition = DaemonRuntimeComposition.create(
                journal=journal,
                task_graphs=task_graphs,
                variables=variables,
                compiler=roster.compiler,
                artifact_store=substrate.artifact_store,
                environments=environments,
            )
            roster.backtesting = runtime_composition.backtesting
            roster.backtesting.bind_experiments(experiments)
            process = cls(
                substrate=substrate,
                roster=roster,
                posture=posture.value,
                bind_port=port,
                journal=journal,
                experiments=experiments,
                task_graphs=task_graphs,
                runtime_composition=runtime_composition,
                variables=variables,
            )
            process.backtesting.bind_product_sessions(process.product_sessions)
            restored_jobs = process.jobs.restore_durable_jobs()
            if is_refusal(restored_jobs):
                process._closed = True
                process._journal.close()
                process._substrate.close()
                return restored_jobs
            reconciled_qmb = process.backtesting.reconcile_restored_jobs()
            if is_refusal(reconciled_qmb):
                process._closed = True
                process._journal.close()
                process._substrate.close()
                return reconciled_qmb
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
            restored_artifacts = process._artifacts.restore_from_journal()
            if is_refusal(restored_artifacts):
                process._closed = True
                process._journal.close()
                process._substrate.close()
                return restored_artifacts
            restored_tickets = process._transfers.restore()
            if is_refusal(restored_tickets):
                process._closed = True
                process._journal.close()
                process._substrate.close()
                return restored_tickets
            restored_drafts = process._editor_drafts.restore_from_journal()
            if is_refusal(restored_drafts):
                process._closed = True
                process._journal.close()
                process._substrate.close()
                return restored_drafts
            restored_plugin_records = restore_plugin_install_records_projection(
                process.sqlite,
                process.journal,
            )
            if is_refusal(restored_plugin_records):
                process._closed = True
                process._journal.close()
                process._substrate.close()
                return restored_plugin_records
            roster.loader.restore_availability_revision(restored_plugin_records.value)
            roster.loader.set_rehydrating_persisted_plugins(True)
            try:
                activated = roster.activate(
                    principal=PrincipalClass.OPERATOR,
                    correlation_id=f"daemon-process:{boot_epoch_id}",
                )
            finally:
                roster.loader.set_rehydrating_persisted_plugins(False)
            if is_refusal(activated):
                process._closed = True
                process._journal.close()
                process._substrate.close()
                return activated
            spot_bindings = load_spot_state_bindings(process.root)
            if is_refusal(spot_bindings):
                process._release(release_process_gate=False)
                return spot_bindings
            for instance_id, binding in spot_bindings.value.items():
                loaded_spot = next(
                    (
                        item
                        for plugin_id in roster.loader.loaded_ids()
                        if (item := roster.loader.get(plugin_id)) is not None
                        and item.instance_id == instance_id
                    ),
                    None,
                )
                if loaded_spot is None or not any(
                    row.point == "tool"
                    and row.qualified_id == SPOT_CONTRIBUTION
                    and row.package_version == binding.package_version
                    and row.availability == "enabled"
                    for row in loaded_spot.published
                ):
                    process._release(release_process_gate=False)
                    return policy_rejection("spot_binding", "spot read contribution is not enabled")
            process._spot_state_bindings = spot_bindings.value
            if spot_bindings.value:
                restored_spot_sessions = process.product_sessions.restore_from_journal()
                if is_refusal(restored_spot_sessions):
                    process._release(release_process_gate=False)
                    return restored_spot_sessions
                retry_configured = configure_spot_host_retry(
                    process.root, process.variables, journal
                )
                if is_refusal(retry_configured):
                    process._release(release_process_gate=False)
                    return retry_configured
            # Optional host configuration adds no listener, grants or implicit
            # transport. Local import keeps configuration/policy types acyclic.
            from .request_runtime.provider_config import load_agent_request_config  # noqa: PLC0415

            configured = load_agent_request_config(process.root)
            if is_refusal(configured):
                process._closed = True
                process._journal.close()
                process._substrate.close()
                return configured
            if configured.value is not None:
                sdk = configured.value
                installed = process.configure_agent_requests(
                    providers=sdk.providers,
                    policies=sdk.policies,
                    profile_tools=sdk.profile_tools,
                    research_browse=sdk.research_browse,
                    research_workflow=sdk.research_workflow,
                    agent_extensions=sdk.agent_extensions,
                    instance_revisions=sdk.instance_revisions,
                    max_workers=sdk.max_workers,
                    max_inflight=sdk.max_inflight,
                    shutdown_timeout_seconds=sdk.shutdown_timeout_seconds,
                )
                if is_refusal(installed):
                    process._closed = True
                    process._journal.close()
                    process._substrate.close()
                    return installed
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

    @property
    def agent_requests(self) -> AgentRequestBridge | None:
        return self._agent_requests

    @property
    def agent_capabilities(self) -> AgentCapabilityStore:
        """Canonical spawn-time records; startup must explicitly admit each Agent."""
        return self._agent_capabilities

    @property
    def canonical_requests(self) -> CanonicalRequestJoin | None:
        """Trusted host join administration, never a wire authority mint."""
        return self._canonical_requests

    def reconcile_experiment_authoring(self, request_id: str) -> Result[Mapping[str, object]]:
        """Explicit trusted host recovery; no model replay or implicit query effect."""
        if self._experiment_authoring is None:
            return policy_rejection("authoring", "authoring runtime is not configured")
        return self._experiment_authoring.reconcile_receipt(request_id)

    def _agent_request_now(self) -> str:
        value = self._now_ns()
        if value is None:
            raise RuntimeError("daemon clock is unavailable")
        return format_utc_iso_z(Instant(value_ns=value))

    def _agent_tool_target(
        self, session_ref: str
    ) -> Result[tuple[ContributionRecord, InstanceRecord]]:
        loaded_session = self.product_sessions.get(session_ref)
        if is_refusal(loaded_session):
            return loaded_session
        session = loaded_session.value
        instance_id = session.app_instance_id
        revision = self._agent_instance_revisions.get(instance_id or "")
        if instance_id is None or revision is None or revision != session.context.config_revision:
            return policy_rejection(
                "instance_id", "tool target has no matching current host revision"
            )
        loaded = next(
            (
                item
                for plugin_id in self.roster.loader.loaded_ids()
                if (item := self.roster.loader.get(plugin_id)) is not None
                and item.instance_id == instance_id
            ),
            None,
        )
        if loaded is None:
            return policy_rejection(
                "instance_id", "tool instance is not enabled on the live roster"
            )
        published = next(
            (
                row
                for row in loaded.published
                if row.qualified_id == session.context.contribution.qualified_id
                and row.package_version == session.context.contribution.package_version
                and row.availability == "enabled"
            ),
            None,
        )
        if published is None:
            return policy_rejection(
                "contribution", "tool contribution is not enabled on the live roster"
            )
        return Ok(
            (
                ContributionRecord(
                    qualified_id=published.qualified_id or "",
                    package_version=published.package_version,
                    availability=published.availability,
                ),
                InstanceRecord(instance_id=instance_id, config_revision=revision),
            )
        )

    def configure_agent_requests(
        self,
        *,
        providers: Mapping[str, ProviderAdapter],
        policies: Mapping[str, AgentRequestPolicy],
        profile_tools: Mapping[str, frozenset[str]] | None = None,
        research_browse: Mapping[str, object] | None = None,
        research_workflow: Mapping[str, object] | None = None,
        agent_extensions: AgentExtensions | None = None,
        instance_revisions: Mapping[str, int] | None = None,
        max_workers: int = 2,
        max_inflight: int = 16,
        shutdown_timeout_seconds: float = 2,
        canonical_joins: tuple[CanonicalJoinPlan, ...] = (),
    ) -> Result[None]:
        """Trusted startup seam; paired clients never mutate provider or tool policy."""
        if self._agent_requests is not None or self._closed or self._server is not None:
            return policy_rejection(
                "agent_requests", "request policy installs once before listener startup"
            )
        restored = self.product_sessions.restore_from_journal()
        if is_refusal(restored):
            return restored
        self._agent_instance_revisions = MappingProxyType(dict(instance_revisions or {}))
        runtime = RequestRuntime(
            journal=self.journal, product_sessions=self.product_sessions, providers=providers
        )
        authoring = ExperimentAuthoring(
            runtime=runtime,
            policies=policies,
            dispatcher=self.task_dispatcher,
            agents=self.agent_capabilities,
            experiments=self.experiments,
            now=self._agent_request_now,
        )
        runtime.execution_admission = authoring.admit
        runtime.execution_completion = authoring.complete
        runtime.acceptance_binding = authoring.bind_acceptance
        try:
            wrapped = bind_daemon_tool_providers(
                runtime,
                providers,
                profile_tools or {},
                research_browse or {},
                KnowledgeService(registry=self.roster.knowledge, hooks=self._artifacts.hooks),
                target_resolver=self._agent_tool_target,
                now=self._agent_request_now,
                research_workflow=research_workflow,
                agent_extensions=agent_extensions,
                hooks=self._artifacts.hooks,
            )
            if is_refusal(wrapped):
                return wrapped
            from qma.daemon.request_runtime.actor_workflow import (  # noqa: PLC0415
                bind_actor_workflows,
            )

            actor_providers, actor_policies = bind_actor_workflows(
                self.root,
                runtime,
                providers,
                wrapped.value,
                policies,
                profile_tools or {},
                now=self._agent_request_now,
                extensions=agent_extensions,
                hooks=self._artifacts.hooks,
            )
            runtime.providers = dict(actor_providers)
            canonical = None
            if canonical_joins:
                canonical = CanonicalRequestJoin(
                    runtime=runtime,
                    plans=canonical_joins,
                    dispatcher=self.task_dispatcher,
                    agents=self.agent_capabilities,
                    mailboxes=self.mailboxes,
                    jobs=self.jobs,
                )
                runtime.submission_admission = canonical.accept
                runtime.lifecycle_admission = canonical.guard
                runtime.outcome_observation = canonical.observe
                runtime.canonical_projection = canonical.projection
                self.jobs.cancel_admission = canonical.allow_canonical_cancel
            bridge = AgentRequestBridge(
                runtime=runtime,
                policies=actor_policies,
                now=self._agent_request_now,
                max_workers=max_workers,
                max_inflight=max_inflight,
                shutdown_timeout_seconds=shutdown_timeout_seconds,
            )
        except ValueError:
            return invalid_input("agent_requests", "host SDK policy could not be installed")
        self._agent_requests = bridge
        self._experiment_authoring = authoring
        self._canonical_requests = canonical
        return Ok(None)

    def mount_pack_ui_view(
        self, *, product_session_id: object, view_id: object
    ) -> Result[PackUiMount]:
        """Production host entry: derive pack, snapshot, clock, and grants from daemon state."""
        return self._product_session_chrome.mount_pack_ui_view(
            product_session_id=product_session_id,
            view_id=view_id,
            loader=self._roster.loader,
        )

    def press_pack_ui_action(
        self,
        *,
        mount_id: object,
        payload: object,
        execute_invocation: Callable[[BoundInvocation], None],
    ) -> Result[BoundSessionGrant]:
        """Dispatch through a trusted host executor; renderer input cannot provide it."""
        return self._product_session_chrome.press_pack_ui_action(
            mount_id,
            payload,
            loader=self._roster.loader,
            execute_invocation=execute_invocation,
        )

    def unmount_pack_ui_view(self, mount_id: object) -> bool:
        return self._product_session_chrome.unmount_pack_ui_view(mount_id)

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

    def get_pack_ui_request(
        self,
        args: object,
        *,
        operator_principal: object,
        capabilities: object | None = None,
    ) -> Result[PackUiRequestSnapshot]:
        """Read the exact durable UI request for a currently enabled pack instance."""
        gated = require_pack_ui_request_capability(capabilities)
        if is_refusal(gated):
            return gated
        if operator_principal is not PrincipalClass.OPERATOR:
            return policy_rejection(
                "principal_class", "get_pack_ui_request requires an operator pairing"
            )
        parsed = parse_pack_ui_request_args(args)
        if is_refusal(parsed):
            return parsed
        instance_id = cast(str, parsed.value["instance_id"])
        revision = cast(int, parsed.value["availability_revision"])
        active = next(
            (
                plugin
                for plugin_id in self._roster.loader.loaded_ids()
                if (plugin := self._roster.loader.get(plugin_id)) is not None
                and plugin.instance_id == instance_id
                and plugin.availability_revision == revision
            ),
            None,
        )
        if active is None:
            return policy_rejection(
                "instance_id",
                "enabled pack instance and availability_revision must match exactly",
                instance_id=instance_id,
                availability_revision=revision,
                mismatch="instance_revision",
            )
        try:
            row = read_pack_ui_request_record(
                self.sqlite,
                instance_id=instance_id,
                availability_revision=revision,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            return storage_failure(
                f"could not read PackUiRequest projection: {exc}",
                context={"field": "plugin_install_records", "instance_id": instance_id},
            )
        if (
            row is None
            or row.get("pack_id") != active.manifest.id
            or row.get("pack_version") != active.manifest.version
        ):
            return policy_rejection(
                "instance_id",
                "no exact PackUiRequest record exists for the enabled instance revision",
                instance_id=instance_id,
                availability_revision=revision,
                mismatch="record_unavailable",
            )
        request = parse_pack_ui_request(row.get("pack_ui_request"))
        if is_refusal(request):
            return request
        return Ok(PackUiRequestSnapshot(instance_id, revision, request.value))

    @property
    def artifacts(self) -> ArtifactStore:
        return self._artifacts

    def stage_artifact(
        self,
        body: bytes,
        *,
        content_length: object,
        capabilities: object | None = None,
    ) -> Result[StagedArtifact]:
        """Library admission of complete PUT bytes. Live HTTP must call the listener."""
        caps: object = {STAGE_ARTIFACT_CAPABILITY: True} if capabilities is None else capabilities
        got = self._variables.artifact_stage_max_bytes()
        max_bytes: object = None if is_refusal(got) else got.value
        return handle_stage_artifact_put(
            self._artifacts,
            body,
            content_length=content_length,
            max_bytes=max_bytes,
            capabilities=caps,
        )

    @property
    def transfers(self) -> TransferTicketStore:
        return self._transfers

    def record_source_tls_origin(self, origin: object) -> Result[str]:
        """Operator-recorded non-loopback TLS origin dest will pull."""
        return self._transfers.record_source_tls_origin(origin)

    def register_destination_placement(self, placement: DestinationPlacement) -> None:
        self._transfers.register_destination(placement)

    def dest_control_up(self, credential_ref: object) -> Result[DestControlHandle]:
        """Dest control reconnect: issued and notified open tickets are pushed."""
        return self._transfers.dest_control_up(credential_ref)

    def dest_control_down(self, credential_ref: str, *, writer: object | None = None) -> None:
        self._transfers.dest_control_down(credential_ref, writer=writer)

    def transfer_artifact(
        self,
        payload: object,
        *,
        capabilities: object | None = None,
        principal_class: object = PrincipalClass.OPERATOR,
    ) -> Result[TransferArtifactResult]:
        """Library admission of transfer_artifact. Live CT-40 must call the WS path."""
        caps: object = (
            {TRANSFER_ARTIFACT_CAPABILITY: True} if capabilities is None else capabilities
        )
        operator_id = (
            self._local_operator.principal_id if self._local_operator is not None else None
        )
        return handle_transfer_artifact(
            self._transfers,
            payload,
            capabilities=caps,
            principal_class=principal_class,
            operator_principal=operator_id,
        )

    @property
    def dest_artifacts(self) -> ArtifactStore:
        return self._transfers.dest_artifacts

    def place_dest_pulled_bytes(
        self,
        body: object,
        *,
        ticket_id: object,
        interrupted: bool = False,
    ) -> Result[StagedArtifact]:
        """Dest daemon sole writer of dest store. Source bytes stay on source."""
        return place_dest_pulled_bytes(
            self._transfers,
            body,
            ticket_id=ticket_id,
            interrupted=interrupted,
        )

    def transfer_complete(
        self,
        payload: object,
        *,
        capabilities: object | None = None,
        principal_class: object = PrincipalClass.MACHINE,
        credential_ref: object,
    ) -> Result[TransferCompleteResult]:
        """Library admission of transfer_complete. Live CT-40 must call the WS path."""
        caps: object = (
            {TRANSFER_COMPLETE_CAPABILITY: True} if capabilities is None else capabilities
        )
        return handle_transfer_complete(
            self._transfers,
            payload,
            capabilities=caps,
            principal_class=principal_class,
            credential_ref=credential_ref,
        )

    def gate_invoke_until_transfer_complete(
        self,
        *,
        fp1: object,
        instance_id: object,
    ) -> Result[InvokeTransferGate]:
        """Refuse remote invoke citing fp1 until dest-authored transfer_complete."""
        return gate_invoke_until_transfer_complete(
            self._transfers,
            fp1=fp1,
            instance_id=instance_id,
        )

    def _paired_http_capabilities(self, pairing_record_id: object) -> object:
        stored = self._initialize_capabilities
        if isinstance(pairing_record_id, str) and pairing_record_id in stored:
            return stored[pairing_record_id]
        return {
            LIST_MAILBOX_CAPABILITY: True,
            STAGE_ARTIFACT_CAPABILITY: True,
            TRANSFER_ARTIFACT_CAPABILITY: True,
            TRANSFER_COMPLETE_CAPABILITY: True,
        }

    def _operator_principal(self) -> str | None:
        operator = self._local_operator
        return None if operator is None else operator.principal_id

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
    def execution_environments(self) -> ExecutionEnvironmentRegistry:
        """The process-shared ExecutionEnvironment registry."""
        return self._runtime_composition.environments

    @property
    def compute_router(self) -> ComputeRouter:
        """The process-shared ComputeRouter used by task and job services."""
        return self._runtime_composition.router

    @property
    def task_dispatcher(self) -> TaskGraphDispatcher:
        """The durable TaskGraph dispatcher composed for this process."""
        return self._runtime_composition.dispatcher

    @property
    def jobs(self) -> JobHandleService:
        """The shared daemon-owned JobHandle service."""
        return self._runtime_composition.jobs

    @property
    def nested_mission_host(self) -> NestedMissionHost:
        """The nested Mission host mapped to the active roster compiler."""
        return self._runtime_composition.nested_missions

    @property
    def runtime_service(self) -> RuntimeService:
        """The Dialogue/RLM façade sharing this process's jobs and tools."""
        return self._runtime_composition.runtime_service

    @property
    def tool_registry(self) -> ToolRegistry:
        """The process-wide governed QMA Tool Registry."""
        return self._runtime_composition.tools

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

    def configure_source_origin(self, origin: object) -> Result[Mapping[str, object]]:
        """Operator-recorded TLS origin dest will pull. Loopback/http refuse."""
        recorded = self.record_source_tls_origin(origin)
        if is_refusal(recorded):
            return recorded
        return Ok(
            MappingProxyType(
                {
                    "source_origin": recorded.value,
                    "writer": "host.configure.source-origin",
                }
            )
        )

    def configure_dest_placement(self, payload: object) -> Result[Mapping[str, object]]:
        """Register destination placement. Host-control may set same_daemon."""
        if not isinstance(payload, Mapping):
            return invalid_input(
                "dest-placement",
                "destination placement is an object",
                given=repr(payload),
                local_fallback=False,
            )
        entry = cast("Mapping[str, object]", payload)
        placed = placement_from_host_configure(entry)
        if is_refusal(placed):
            return placed
        placement = placed.value
        self._transfers.register_destination(placement)
        return Ok(
            MappingProxyType(
                {
                    "instance_id": placement.instance_id,
                    "environment_id": placement.environment_id,
                    "placement_revision": placement.placement_revision,
                    "credential_ref": placement.credential_ref,
                    "same_daemon": placement.same_daemon,
                    "writer": "host.configure.dest-placement",
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
            on_configure_source_origin=self.configure_source_origin,
            on_configure_dest_placement=self.configure_dest_placement,
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
            offered = header_value(headers, "Sec-WebSocket-Protocol")
            authorization = header_value(headers, "Authorization")
            if (
                not _offered_pairing_ws(offered)
                and _offered_ct40_ws(offered)
                and authorization is not None
            ):
                await self._serve_machine_ws(reader, writer, headers, query)
                return
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
        if request.method == "GET" and is_artifacts_get_path(request.path):
            await self._serve_artifact_machine_get(
                writer,
                request,
                headers,
                origin=origin,
            )
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
                listed = handle_list_mailbox_query(
                    self._mailboxes,
                    query_string_to_args(request.query),
                    operator_principal=authed.value.principal_class,
                    sessions=self._product_sessions,
                    capabilities=self._paired_http_capabilities(authed.value.pairing_record_id),
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
            if request.method == "GET" and request.path == GET_PACK_UI_REQUEST_HTTP_PATH:
                requested = self.get_pack_ui_request(
                    query_string_to_args(request.query),
                    operator_principal=authed.value.principal_class,
                    capabilities=self._paired_http_capabilities(authed.value.pairing_record_id),
                )
                if is_refusal(requested):
                    await self._write_refusal(writer, requested, origin=origin)
                    return
                body = json.dumps(
                    {"ok": True, "result": dict(requested.value.to_payload())},
                    ensure_ascii=True,
                ).encode("utf-8")
                await self._write_http(
                    writer,
                    200,
                    _cors_headers_for_origin(origin),
                    body,
                )
                return
            if request.method == "GET" and request.path == EDITOR_DRAFT_HTTP_PATH:
                if (
                    authed.value.principal_class is not PrincipalClass.OPERATOR
                    or self._operator_principal() is None
                ):
                    refused = policy_rejection(
                        "principal_class",
                        "editor drafts require an authenticated operator principal",
                    )
                    await self._write_refusal(writer, refused, origin=origin)
                    return
                capabilities = self._paired_http_capabilities(authed.value.pairing_record_id)
                capability = require_editor_draft_capability(
                    capabilities,
                    GET_EDITOR_DRAFT_HEAD_CAPABILITY,
                )
                if is_refusal(capability):
                    await self._write_refusal(writer, capability, origin=origin)
                    return
                head = self._editor_drafts.get_editor_draft_head(
                    query_string_to_args(request.query),
                    operator_principal=self._operator_principal(),
                    capabilities=capabilities,
                )
                if is_refusal(head):
                    await self._write_refusal(writer, head, origin=origin)
                    return
                body = json.dumps(
                    {"ok": True, "result": dict(head.value.to_payload())},
                    ensure_ascii=True,
                ).encode("utf-8")
                await self._write_http(
                    writer,
                    200,
                    _cors_headers_for_origin(origin),
                    body,
                )
                return
            if request.method == "PUT" and request.path == STAGE_ARTIFACT_HTTP_PATH:
                await self._serve_stage_artifact_put(
                    reader,
                    writer,
                    headers,
                    origin=origin,
                    pairing_record_id=authed.value.pairing_record_id,
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

    async def _serve_artifact_machine_get(
        self,
        writer: asyncio.StreamWriter,
        request: PairHttpRequest,
        headers: Mapping[str, str],
        *,
        origin: str | None,
    ) -> None:
        """AM-13 machine GET /artifacts/<fp1> with X-QMX-Transfer-Ticket."""
        fp1 = artifacts_get_fp1(request.path)
        if fp1 is None:
            refused = policy_rejection("path", "GET /artifacts/<fp1> requires an fp1")
            await self._write_refusal(writer, refused, origin=origin)
            return
        parsed_auth = parse_machine_pull_authorization(header_value(headers, "Authorization"))
        if is_refusal(parsed_auth):
            await self._write_refusal(writer, parsed_auth, origin=origin)
            return
        session = authenticate_machine_or_worker(parsed_auth.value)
        if is_refusal(session):
            await self._write_refusal(writer, session, origin=origin)
            return
        credential_ref = session.value.credential_ref
        redeemed = self._transfers.redeem_get(
            ticket_id=header_value(headers, "X-QMX-Transfer-Ticket"),
            fp1=fp1,
            credential_ref=credential_ref,
        )
        if is_refusal(redeemed):
            await self._write_refusal(writer, redeemed, origin=origin)
            return
        out_headers: dict[str, str] = {
            "Content-Type": "application/octet-stream",
            "Access-Control-Allow-Credentials": "false",
            "Vary": "Origin",
        }
        if origin is not None and origin != "*" and not is_daemon_http_origin(origin):
            out_headers["Access-Control-Allow-Origin"] = origin
        await self._write_http(writer, 200, out_headers, redeemed.value.content)

    async def _serve_stage_artifact_put(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        headers: Mapping[str, str],
        *,
        origin: str | None,
        pairing_record_id: object,
    ) -> None:
        """Authenticated AM-05 PUT /artifacts/stage on the bound listener."""
        caps = self._paired_http_capabilities(pairing_record_id)
        gated = require_stage_artifact_capability(caps)
        if is_refusal(gated):
            await self._write_refusal(writer, gated, origin=origin)
            return
        max_bytes = self._variables.artifact_stage_max_bytes()
        if is_refusal(max_bytes):
            await self._write_refusal(writer, max_bytes, origin=origin)
            return
        length = parse_stage_content_length(header_value(headers, "Content-Length"))
        if is_refusal(length):
            await self._write_refusal(writer, length, origin=origin)
            return
        if length.value > max_bytes.value:
            oversize = policy_rejection(
                "content_length",
                "Content-Length exceeds registry:artifact.stage_max_bytes",
                content_length=length.value,
                registry_key=ARTIFACT_STAGE_MAX_BYTES_REGISTRY_KEY,
                wrote_object=False,
                http_put=STAGE_ARTIFACT_HTTP_PATH,
            )
            await self._write_refusal(writer, oversize, origin=origin)
            return
        body = await _read_stage_put_body(reader, length.value)
        if is_refusal(body):
            self._artifacts.abandon_incomplete()
            await self._write_refusal(writer, body, origin=origin)
            return
        staged = handle_stage_artifact_put(
            self._artifacts,
            body.value,
            content_length=length.value,
            max_bytes=max_bytes.value,
            capabilities=caps,
        )
        if is_refusal(staged):
            await self._write_refusal(writer, staged, origin=origin)
            return
        payload = json.dumps(
            {"ok": True, "result": dict(staged.value.to_payload())},
            ensure_ascii=True,
        ).encode("utf-8")
        await self._write_http(
            writer,
            200,
            _cors_headers_for_origin(origin),
            payload,
        )

    async def _serve_machine_ws(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        headers: Mapping[str, str],
        query: str | None,
    ) -> None:
        """Machine CT-40: qmx.ct40.v1 plus credential_ref Authorization."""
        origin = header_value(headers, "Origin")
        _ = query
        parsed_auth = parse_machine_pull_authorization(header_value(headers, "Authorization"))
        if is_refusal(parsed_auth):
            await self._write_refusal(writer, parsed_auth, origin=origin)
            return
        session = authenticate_machine_or_worker(parsed_auth.value)
        if is_refusal(session):
            await self._write_refusal(writer, session, origin=origin)
            return
        credential_ref = session.value.credential_ref
        if credential_ref is None:
            refused = policy_rejection(
                "credential_ref",
                "machine CT-40 sessions carry credential_ref",
            )
            await self._write_refusal(writer, refused, origin=origin)
            return
        key = header_value(headers, "Sec-WebSocket-Key")
        if key is None:
            refused = policy_rejection(
                "upgrade",
                "WebSocket upgrade requires Sec-WebSocket-Key",
            )
            await self._write_refusal(writer, refused, origin=origin)
            return
        validated = self._transfers.validate_dest_control(credential_ref)
        if is_refusal(validated):
            await self._write_refusal(writer, validated, origin=origin)
            return
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
        connection_token = f"{credential_ref}:{id(connection)}"
        buf = b""
        try:
            authed = connection.authenticate(
                credential_ref,
                principal_class=PrincipalClass.MACHINE,
            )
            if is_refusal(authed):
                return
            attached = self._transfers.attach_dest_control(
                credential_ref,
                writer=writer,
                emit=lambda note: _emit_dest_control_note(writer, note),
            )
            if is_refusal(attached):
                writer.close()
                await writer.wait_closed()
                return
            await writer.drain()
            while not reader.at_eof() and not self._closed:
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
                        session_key=credential_ref,
                        connection_token=connection_token,
                    )
                    if response is None:
                        continue
                    writer.write(_encode_ws_frame(json.dumps(response).encode("utf-8")))
                    await writer.drain()
        finally:
            self._transfers.dest_control_down(credential_ref, writer=writer)
            producer_id = connection.producer_id
            if producer_id is not None:
                self._live_producers.release(
                    producer_id,
                    connection_token=connection_token,
                )

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
                        session_key=admitted.value.pairing_record_id,
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
        session_key: str,
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
                advertise = (
                    raw_caps.get(PAIRING_CAPABILITY) is True
                    or raw_caps.get(LIST_MAILBOX_CAPABILITY) is True
                    or raw_caps.get(STAGE_ARTIFACT_CAPABILITY) is True
                    or raw_caps.get(TRANSFER_ARTIFACT_CAPABILITY) is True
                    or raw_caps.get(TRANSFER_COMPLETE_CAPABILITY) is True
                    or raw_caps.get(SAVE_EDITOR_DRAFT_CAPABILITY) is True
                    or raw_caps.get(GET_EDITOR_DRAFT_HEAD_CAPABILITY) is True
                    or raw_caps.get(PUBLISH_EDITOR_DRAFT_CAPABILITY) is True
                    or PACK_UI_REQUEST_CAPABILITY in raw_caps
                    or GET_PACK_UI_REQUEST_CAPABILITY in raw_caps
                    or raw_caps.get(CANCEL_JOB_CAPABILITY) is True
                    or any(raw_caps.get(name) is True for name in AGENT_REQUEST_CAPABILITIES)
                )
            completed = connection.complete_initialize(
                params.value,
                request_id=begun.value.id,
                live_producers=self._live_producers,
                connection_token=connection_token,
                advertise_pairing=advertise,
                server_capabilities={}
                if self._agent_requests is None
                else self._agent_requests.capabilities,
            )
            if is_refusal(completed):
                return _jsonrpc_refusal(req_id, completed)
            self._initialize_capabilities[session_key] = dict(connection.capabilities)
            return completed.value.to_dict()
        if method == STAGE_ARTIFACT_CAPABILITY:
            return _jsonrpc_refusal(req_id, refuse_jsonrpc_stage_artifact())
        accepted = connection.accept_family_message(method)
        if is_refusal(accepted):
            return _jsonrpc_refusal(req_id, accepted)
        if method in AGENT_REQUEST_CAPABILITIES:
            return self._dispatch_agent_request(connection, request, req_id, cast("str", method))
        if method == WireCommand.SAVE_EDITOR_DRAFT.value:
            return self._dispatch_editor_draft_command(connection, request, req_id, publish=False)
        if method == WireCommand.PUBLISH_EDITOR_DRAFT.value:
            return self._dispatch_editor_draft_command(connection, request, req_id, publish=True)
        if method == WireQuery.GET_PACK_UI_REQUEST.value:
            gated_query = connection.require_query_capability(method)
            if is_refusal(gated_query):
                return _jsonrpc_refusal(req_id, gated_query)
            result = self.get_pack_ui_request(
                request.get("params"),
                operator_principal=connection.principal_class,
                capabilities=connection.capabilities,
            )
            if is_refusal(result):
                return _jsonrpc_refusal(req_id, result)
            return _jsonrpc_result(req_id, result.value.to_payload())
        if method == WireQuery.GET_EDITOR_DRAFT_HEAD.value:
            gated_query = connection.require_query_capability(method)
            if is_refusal(gated_query):
                return _jsonrpc_refusal(req_id, gated_query)
            if (
                connection.principal_class is not PrincipalClass.OPERATOR
                or self._operator_principal() is None
            ):
                return _jsonrpc_refusal(
                    req_id,
                    policy_rejection(
                        "principal_class",
                        "editor drafts require an authenticated operator principal",
                    ),
                )
            raw_params = request.get("params")
            head = self._editor_drafts.get_editor_draft_head(
                raw_params,
                operator_principal=self._operator_principal(),
                capabilities=connection.capabilities,
            )
            if is_refusal(head):
                return _jsonrpc_refusal(req_id, head)
            return _jsonrpc_result(req_id, head.value.to_payload())
        if method == WireQuery.GET_PRODUCT_SESSION.value:
            gated_query = connection.require_query_capability(method)
            if is_refusal(gated_query):
                return _jsonrpc_refusal(req_id, gated_query)
            if (
                connection.principal_class is not PrincipalClass.OPERATOR
                or self._operator_principal() is None
            ):
                return _jsonrpc_refusal(
                    req_id,
                    policy_rejection(
                        "principal_class", "ProductSession reads require an authenticated operator"
                    ),
                )
            raw_params = request.get("params")
            if not isinstance(raw_params, Mapping):
                return _jsonrpc_refusal(req_id, invalid_input("params", "expected object"))
            params = cast("Mapping[str, object]", raw_params)
            unknown = sorted(set(params) - {"product_session_ref"})
            if unknown:
                return _jsonrpc_refusal(
                    req_id,
                    invalid_input("params", "unknown get_product_session fields", fields=unknown),
                )
            session_ref = params.get("product_session_ref")
            if not isinstance(session_ref, str) or not session_ref.startswith("psess:"):
                return _jsonrpc_refusal(
                    req_id, invalid_input("product_session_ref", "expected psess: id")
                )
            session_result = self._product_sessions.get(session_ref)
            if is_refusal(session_result):
                return _jsonrpc_refusal(req_id, session_result)
            if session_result.value.principal != PrincipalClass.OPERATOR.value:
                return _jsonrpc_refusal(
                    req_id,
                    policy_rejection("principal", "ProductSession is not operator-owned"),
                )
            grants = self._product_sessions.granted_records(session_ref)
            if is_refusal(grants):
                return _jsonrpc_refusal(req_id, grants)
            session_payload: dict[str, object] = dict(session_result.value.to_payload())
            session_payload["grant_records"] = [
                dict(record.to_payload()) for record in grants.value
            ]
            return _jsonrpc_result(req_id, session_payload)
        if method == WireQuery.GET_JOB.value:
            gated_query = connection.require_query_capability(method)
            if is_refusal(gated_query):
                return _jsonrpc_refusal(req_id, gated_query)
            if (
                connection.principal_class is not PrincipalClass.OPERATOR
                or self._operator_principal() is None
            ):
                return _jsonrpc_refusal(
                    req_id,
                    policy_rejection(
                        "principal_class", "JobHandle reads require an authenticated operator"
                    ),
                )
            raw_params = request.get("params")
            if not isinstance(raw_params, Mapping):
                return _jsonrpc_refusal(req_id, invalid_input("params", "expected object"))
            params = cast("Mapping[str, object]", raw_params)
            unknown = sorted(set(params) - {"handle_id", "product_session_ref"})
            if unknown:
                return _jsonrpc_refusal(
                    req_id, invalid_input("params", "unknown get_job fields", fields=unknown)
                )
            handle_id = params.get("handle_id")
            session_ref = params.get("product_session_ref")
            if not isinstance(handle_id, str) or not isinstance(session_ref, str):
                return _jsonrpc_refusal(
                    req_id,
                    invalid_input("params", "get_job requires handle_id and product_session_ref"),
                )
            handle = self.jobs.handle_for(handle_id)
            if handle is None:
                return _jsonrpc_refusal(
                    req_id, invalid_input("handle_id", "requires a minted JobHandle")
                )
            if handle.originating_product_session_ref != session_ref:
                return _jsonrpc_refusal(
                    req_id,
                    policy_rejection(
                        "product_session_ref",
                        "JobHandle may be read only through its exact originating ProductSession",
                        handle_id=handle_id,
                    ),
                )
            session = self._product_sessions.get(session_ref)
            if is_refusal(session):
                return _jsonrpc_refusal(req_id, session)
            if session.value.principal != PrincipalClass.OPERATOR.value:
                return _jsonrpc_refusal(
                    req_id,
                    policy_rejection("principal", "ProductSession is not operator-owned"),
                )
            job_payload = dict(handle.to_payload())
            if handle.state is JobHandleState.DONE and handle.job_id.startswith("qmb:"):
                verified = self.backtesting.read_completed_result(handle.job_id, owner=handle.owner)
                if is_refusal(verified):
                    return _jsonrpc_refusal(req_id, verified)
                job_payload["verified_result"] = verified.value["result"]
            return _jsonrpc_result(req_id, job_payload)
        if method == WireCommand.TRANSFER_ARTIFACT.value:
            return self._dispatch_transfer_artifact(connection, request, req_id)
        if method == WireCommand.TRANSFER_COMPLETE.value:
            return self._dispatch_transfer_complete(connection, request, req_id)
        if method == WireCommand.CANCEL_JOB.value:
            return self._dispatch_cancel_job(connection, request, req_id)
        if method == WireCommand.OPEN_PRODUCT_SESSION.value:
            return self._dispatch_open_product_session(connection, request, req_id)
        if method == WireCommand.GRANT_PRODUCT_SESSION.value:
            return self._dispatch_grant_product_session(connection, request, req_id)
        if method in {WireCommand.START_MISSION.value, WireCommand.LAUNCH_TASK.value}:
            gated = self._gate_live_invoke(method, request, req_id)
            if gated is not None:
                return gated
            return self._dispatch_product_session_invoke(
                connection, request, req_id, cast("str", method)
            )
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

    def _dispatch_agent_request(
        self,
        connection: WireConnection,
        request: Mapping[str, object],
        req_id: object,
        method: str,
    ) -> dict[str, object]:
        gated = require_agent_request_capability(connection.capabilities, method)
        if is_refusal(gated):
            return _jsonrpc_refusal(req_id, gated)
        if (
            not connection.authenticated
            or connection.pairing_record_id is None
            or connection.principal_class is not PrincipalClass.OPERATOR
        ):
            return _jsonrpc_refusal(
                req_id,
                policy_rejection(
                    "authentication", "agent requests require authenticated operator pairing"
                ),
            )
        bridge = self._agent_requests
        if bridge is None:
            return _jsonrpc_refusal(
                req_id, policy_rejection("agent_requests", "SDK request policy is not configured")
            )
        if method == GET_AGENT_REQUEST_CAPABILITY:
            authorized_query = connection.require_query_capability(method)
            if is_refusal(authorized_query):
                return _jsonrpc_refusal(req_id, authorized_query)
        else:
            authorized_command = connection.authorize_command(method)
            if is_refusal(authorized_command):
                return _jsonrpc_refusal(req_id, authorized_command)
        try:
            if method == SUBMIT_AGENT_REQUEST_CAPABILITY:
                params = parse_submit_agent_request(request.get("params"))
                if is_refusal(params):
                    return _jsonrpc_refusal(req_id, params)
                result = bridge.submit(params.value, principal=connection.principal_class)
            else:
                reference = (
                    parse_get_agent_request(request.get("params"))
                    if method == GET_AGENT_REQUEST_CAPABILITY
                    else parse_resume_agent_request(request.get("params"))
                    if method == RESUME_AGENT_REQUEST_CAPABILITY
                    else parse_cancel_agent_request(request.get("params"))
                )
                if is_refusal(reference):
                    return _jsonrpc_refusal(req_id, reference)
                result = (
                    bridge.get(reference.value, principal=connection.principal_class)
                    if method == GET_AGENT_REQUEST_CAPABILITY
                    else bridge.resume(reference.value, principal=connection.principal_class)
                    if method == RESUME_AGENT_REQUEST_CAPABILITY
                    else bridge.cancel(reference.value, principal=connection.principal_class)
                )
        except RuntimeError:
            return _jsonrpc_refusal(
                req_id,
                policy_rejection("agent_requests", "daemon request admission is unavailable"),
            )
        if is_refusal(result):
            return _jsonrpc_refusal(req_id, result)
        if (
            method == GET_AGENT_REQUEST_CAPABILITY
            and self._experiment_authoring is not None
            and result.value.get("content_withheld") is not True
        ):
            request_id = result.value.get("request_id")
            if isinstance(request_id, str):
                authored = self._experiment_authoring.receipt(request_id)
                if is_refusal(authored):
                    return _jsonrpc_refusal(req_id, authored)
                if authored.value is not None:
                    return _jsonrpc_result(
                        req_id, {**result.value, "experiment_authoring": dict(authored.value)}
                    )
        return _jsonrpc_result(req_id, result.value)

    def _dispatch_product_session_invoke(
        self,
        connection: WireConnection,
        request: Mapping[str, object],
        req_id: object,
        method: str,
    ) -> dict[str, object]:
        """Resolve CT-40 invoke authority from the originating product session."""
        authorized = connection.authorize_command(method)
        if is_refusal(authorized):
            return _jsonrpc_refusal(req_id, authorized)
        principal_class = connection.principal_class
        if principal_class is None:
            return _jsonrpc_error(req_id, code=_JSONRPC_APP_ERROR, message="unauthenticated")
        raw_params = request.get("params")
        if not isinstance(raw_params, Mapping):
            return _jsonrpc_error(
                req_id,
                code=_JSONRPC_INVALID_REQUEST,
                message="params must be an object",
            )
        params = cast("Mapping[str, object]", raw_params)
        session_ref = params.get("product_session_ref")
        if not isinstance(session_ref, str) or not session_ref.startswith("psess:"):
            return _jsonrpc_refusal(
                req_id,
                invalid_input("product_session_ref", "an originating psess: reference is required"),
            )
        session_result = self._product_sessions.get(session_ref)
        if is_refusal(session_result):
            return _jsonrpc_refusal(req_id, session_result)
        session = session_result.value
        if session.principal != principal_class.value:
            return _jsonrpc_refusal(
                req_id,
                policy_rejection(
                    "principal_class",
                    "the authenticated CT-40 principal must match the originating product session",
                ),
            )
        parsed_envelope = parse_invocation_envelope(params.get("envelope"))
        if is_refusal(parsed_envelope):
            return _jsonrpc_refusal(req_id, parsed_envelope)
        envelope = parsed_envelope.value
        if envelope.caller_session_ref != session_ref:
            return _jsonrpc_refusal(
                req_id,
                policy_rejection("product_session_ref", "envelope caller session does not match"),
            )
        instance_id = session.app_instance_id or session.context.instance_id
        if instance_id is None:
            selected = tuple(
                item.id for item in session.selected_refs if item.kind == "instance_id"
            )
            if len(selected) != 1:
                return _jsonrpc_refusal(
                    req_id,
                    policy_rejection(
                        "instance_id", "session must resolve to exactly one enabled instance"
                    ),
                )
            instance_id = selected[0]
        if envelope.instance_id != instance_id:
            return _jsonrpc_refusal(
                req_id,
                policy_rejection("instance_id", "envelope instance does not match session binding"),
            )
        loaded = next(
            (
                item
                for plugin_id in self._roster.loader.loaded_ids()
                if (item := self._roster.loader.get(plugin_id)) is not None
                and item.instance_id == instance_id
            ),
            None,
        )
        if loaded is None:
            return _jsonrpc_refusal(
                req_id,
                policy_rejection(
                    "instance_id", "session instance is not enabled on the live roster"
                ),
            )
        published = next(
            (
                row
                for row in loaded.published
                if row.qualified_id == envelope.contribution.qualified_id
                and row.package_version == envelope.contribution.package_version
                and row.availability == "enabled"
            ),
            None,
        )
        if published is None:
            return _jsonrpc_refusal(
                req_id,
                policy_rejection("contribution", "contribution is not enabled for this instance"),
            )
        descriptors = self._operation_descriptors()
        descriptor = next(
            (
                item
                for item in descriptors
                if item.door_key == (envelope.op_id, envelope.op_version)
            ),
            None,
        )
        if descriptor is None:
            return _jsonrpc_refusal(
                req_id,
                policy_rejection("operation", "operation has no published host descriptor"),
            )
        if envelope.op_id == "qmn.spot.paper.query":
            spot_binding = self._spot_state_bindings.get(instance_id)
            raw_spot_payload = params.get("payload")
            if (
                spot_binding is None
                or not isinstance(raw_spot_payload, Mapping)
                or dict(cast("Mapping[str, object]", raw_spot_payload)) != spot_binding.scope
                or session.context.account_scope != spot_binding.authority_scope
            ):
                return _jsonrpc_refusal(
                    req_id,
                    policy_rejection(
                        "account_scope", "query requires exactly the host account scope"
                    ),
                )
        contribution = ContributionRecord(
            qualified_id=published.qualified_id or "",
            package_version=published.package_version,
            availability=published.availability,
        )
        instance = InstanceRecord(instance_id=instance_id, config_revision=envelope.config_revision)
        timestamp = self._journal.stamp_durable()
        if is_refusal(timestamp):
            return _jsonrpc_refusal(req_id, timestamp)
        now = format_utc_iso_z(Instant(value_ns=timestamp.value.recorded_at))
        execution: list[Result[object]] = []

        def execute(bound: BoundInvocation) -> None:
            if bound.envelope.op_id in {"qmb.backtest.run", "qmb.optimize.run"}:
                # Canonical dispatch has checked the current grant. Refuse
                # altered Task inputs before consuming this place-run binding.
                dispatched_task = self.task_dispatcher.dispatched_task_for_invocation(
                    bound.envelope.logical_invocation_id
                )
                if is_refusal(dispatched_task):
                    execution.append(dispatched_task)
                    return
                expected_hash = self.task_dispatcher.expected_operation_input_hash(
                    dispatched_task.value[0].id
                )
                if is_refusal(expected_hash):
                    execution.append(expected_hash)
                    return
                if expected_hash.value != bound.envelope.input_hash:
                    execution.append(
                        policy_rejection(
                            "input_hash",
                            "QMB invocation retains the complete dispatched Task payload",
                        )
                    )
                    return
            current_session = self._product_sessions.get(session_ref)
            if is_refusal(current_session):
                execution.append(current_session)
                return
            binding = accepted_invocation_binding(
                bound,
                session_context=current_session.value.context.to_payload(),
            )
            if is_refusal(binding):
                execution.append(binding)
                return

            def execute_attempt(attempt: InvocationEnvelope) -> Result[object]:
                if attempt.attempt_id == 1:
                    accepted = self._product_sessions.accept_work(
                        session_ref,
                        grant_id=attempt.grant_id,
                        logical_invocation_id=attempt.logical_invocation_id,
                        attempt_id=attempt.attempt_id,
                        binding_fp1=binding.value[0],
                        binding_body=binding.value[1],
                        now=now,
                    )
                    if is_refusal(accepted):
                        return accepted
                elif attempt.attempt_id > bound.envelope.attempt_id:
                    accepted = self._product_sessions.record_retry_attempt(
                        session_ref,
                        grant_id=attempt.grant_id,
                        logical_invocation_id=attempt.logical_invocation_id,
                        previous_attempt_id=attempt.attempt_id - 1,
                        attempt_id=attempt.attempt_id,
                        binding_fp1=binding.value[0],
                        binding_body=binding.value[1],
                        now=now,
                    )
                    if is_refusal(accepted):
                        return accepted
                return self._execute_bound_product_operation(
                    replace(bound, envelope=attempt),
                    originating_product_session_ref=session_ref,
                )

            if bound.envelope.effect_class not in {EffectClass.NONE, EffectClass.READ}:
                execution.append(execute_attempt(bound.envelope))
                return
            retried = self._host_retry_loop.run(bound.envelope, execute_attempt)
            if is_refusal(retried):
                execution.append(retried)
                return
            outcome = retried.value
            if outcome.refusal is not None:
                execution.append(outcome.refusal)
                return
            execution.append(Ok(outcome.value))

        dispatched = self._product_sessions.dispatch_public_call(
            session_ref,
            transport=PublicCallTransport.WIRE,
            envelope=envelope,
            payload=params.get("payload"),
            now=now,
            principal=session.principal,
            selected_refs=[{"kind": "instance_id", "id": instance_id}],
            contributions={contribution.as_tuple(): contribution},
            descriptors={descriptor.door_key: descriptor},
            instances={(instance.instance_id, instance.config_revision): instance},
            execute=execute,
        )
        if is_refusal(dispatched):
            return _jsonrpc_refusal(req_id, dispatched)
        if not execution:
            return _jsonrpc_refusal(
                req_id,
                policy_rejection("invocation", "grant dispatch produced no runtime result"),
            )
        result = execution[0]
        if is_refusal(result):
            return _jsonrpc_refusal(req_id, result)
        payload_method = getattr(result.value, "to_payload", None)
        payload_out: Mapping[str, object] = {}
        if callable(payload_method):
            serialized = cast("Callable[[], object]", payload_method)()
            if isinstance(serialized, Mapping):
                payload_out = cast("Mapping[str, object]", serialized)
        else:
            runtime_value: object = result.value
            if isinstance(runtime_value, Mapping):
                payload_out = cast("Mapping[str, object]", runtime_value)
        return _jsonrpc_result(req_id, payload_out)

    def _dispatch_open_product_session(
        self,
        connection: WireConnection,
        request: Mapping[str, object],
        req_id: object,
    ) -> dict[str, object]:
        """Open an operator-owned app-use session on an enabled, bound instance."""
        authorized = connection.authorize_command(WireCommand.OPEN_PRODUCT_SESSION.value)
        if is_refusal(authorized):
            return _jsonrpc_refusal(req_id, authorized)
        if connection.principal_class is not PrincipalClass.OPERATOR:
            return _jsonrpc_refusal(
                req_id,
                policy_rejection("principal_class", "ProductSession opening requires operator"),
            )
        raw = request.get("params")
        if not isinstance(raw, Mapping):
            return _jsonrpc_refusal(req_id, invalid_input("params", "expected object"))
        params = cast("Mapping[str, object]", raw)
        unknown = sorted(set(params) - {"instance_id", "qualified_id", "package_version"})
        if unknown:
            return _jsonrpc_refusal(
                req_id,
                invalid_input("params", "unknown open_product_session fields", fields=unknown),
            )
        instance_id = params.get("instance_id")
        qualified_id = params.get("qualified_id")
        package_version = params.get("package_version")
        if not all(
            isinstance(value, str) and value.strip()
            for value in (instance_id, qualified_id, package_version)
        ):
            return _jsonrpc_refusal(
                req_id,
                invalid_input(
                    "contribution", "instance_id, qualified_id and package_version are required"
                ),
            )
        loaded = next(
            (
                self.roster.loader.get(plugin_id)
                for plugin_id in self.roster.loader.loaded_ids()
                if (candidate := self.roster.loader.get(plugin_id)) is not None
                and candidate.instance_id == instance_id
            ),
            None,
        )
        if loaded is None:
            return _jsonrpc_refusal(
                req_id,
                policy_rejection("instance_id", "instance is not enabled on the live roster"),
            )
        published = next(
            (
                row
                for row in loaded.published
                if row.qualified_id == qualified_id
                and row.package_version == package_version
                and row.availability == "enabled"
            ),
            None,
        )
        if published is None:
            return _jsonrpc_refusal(
                req_id,
                policy_rejection("contribution", "contribution is not enabled for this instance"),
            )
        spot_binding = self._spot_state_bindings.get(loaded.instance_id)
        if published.qualified_id == SPOT_CONTRIBUTION and spot_binding is not None:
            config_revision = spot_binding.config_revision
            account_scope = spot_binding.authority_scope
        else:
            account_scope = None
            binding = backtest_binding_for_instance(self.root, loaded.instance_id)
            if is_refusal(binding):
                return _jsonrpc_refusal(req_id, binding)
            if self._mailboxes.quant_for(binding.value[0]) is None:
                return _jsonrpc_refusal(
                    req_id,
                    TypedRefusal(
                        category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
                        retryability=Retryability.AFTER_CONDITION,
                        context={
                            "reason": "operator QMB binding owner has no registered Quant record",
                            "owner_actor_id": binding.value[0].value,
                        },
                    ),
                )
            environment_kind = binding.value[1].removeprefix("env:")
            if self._runtime_composition.environments.declaration(environment_kind) is None:
                return _jsonrpc_refusal(
                    req_id, NoEnvironment.of(kind=environment_kind, reason="kind_unbound")
                )
            config_revision = binding.value[2]
        # The instance owns one durable app-use session. Returning it makes an
        # open retry after a lost response or browser reload idempotent.
        existing = self._product_sessions.session_for_instance(loaded.instance_id)
        if not is_refusal(existing):
            current = existing.value
            if (
                current.principal != PrincipalClass.OPERATOR.value
                or dict(current.context.contribution.to_payload())
                != {
                    "qualified_id": published.qualified_id,
                    "package_version": published.package_version,
                }
                or current.context.config_revision != config_revision
                or current.context.account_scope != account_scope
            ):
                return _jsonrpc_refusal(
                    req_id,
                    policy_rejection(
                        "product_session",
                        "the instance already has a session with different bindings",
                    ),
                )
            return _jsonrpc_result(req_id, current.to_payload())
        if existing.context.get("field") != "tab":
            return _jsonrpc_refusal(req_id, existing)
        stamp = self._journal.stamp_durable()
        if is_refusal(stamp):
            return _jsonrpc_refusal(req_id, stamp)
        session_id = f"psess:{uuid.uuid4().hex}"
        minted = self._product_sessions.mint(
            product_session_id=session_id,
            profile="app-use",
            principal=PrincipalClass.OPERATOR.value,
            contribution={
                "qualified_id": published.qualified_id,
                "package_version": published.package_version,
            },
            instance_id=loaded.instance_id,
            app_instance_id=loaded.instance_id,
            config_revision=config_revision,
            account_scope=account_scope,
            as_of=format_utc_iso_z(Instant(value_ns=stamp.value.recorded_at)),
            selected_refs=[{"kind": "instance_id", "id": loaded.instance_id}],
        )
        if is_refusal(minted):
            return _jsonrpc_refusal(req_id, minted)
        return _jsonrpc_result(req_id, minted.value.to_payload())

    def _dispatch_grant_product_session(
        self,
        connection: WireConnection,
        request: Mapping[str, object],
        req_id: object,
    ) -> dict[str, object]:
        """Mint a bounded grant after checking the operator's expected revision."""
        authorized = connection.authorize_command(WireCommand.GRANT_PRODUCT_SESSION.value)
        if is_refusal(authorized):
            return _jsonrpc_refusal(req_id, authorized)
        if connection.principal_class is not PrincipalClass.OPERATOR:
            return _jsonrpc_refusal(
                req_id,
                policy_rejection("principal_class", "ProductSession grants require operator"),
            )
        raw = request.get("params")
        if not isinstance(raw, Mapping):
            return _jsonrpc_refusal(req_id, invalid_input("params", "expected object"))
        params = cast("Mapping[str, object]", raw)
        unknown = sorted(
            set(params)
            - {
                "product_session_ref",
                "expected_revision",
                "op_id",
                "op_version",
                "parameter_ceiling",
                "expires_at",
            }
        )
        if unknown:
            return _jsonrpc_refusal(
                req_id,
                invalid_input("params", "unknown grant_product_session fields", fields=unknown),
            )
        session_ref = params.get("product_session_ref")
        expected_revision = params.get("expected_revision")
        op_id = params.get("op_id")
        op_version = params.get("op_version")
        ceiling = params.get("parameter_ceiling")
        expires_at = params.get("expires_at")
        if not isinstance(session_ref, str) or not session_ref.startswith("psess:"):
            return _jsonrpc_refusal(
                req_id, invalid_input("product_session_ref", "expected psess: id")
            )
        loaded_session = self._product_sessions.get(session_ref)
        if is_refusal(loaded_session):
            return _jsonrpc_refusal(req_id, loaded_session)
        session = loaded_session.value
        if session.principal != PrincipalClass.OPERATOR.value:
            return _jsonrpc_refusal(
                req_id, policy_rejection("principal", "session is not operator-owned")
            )
        if (
            not isinstance(expected_revision, int)
            or isinstance(expected_revision, bool)
            or expected_revision != session.context_revision
        ):
            return _jsonrpc_refusal(
                req_id,
                policy_rejection(
                    "expected_revision",
                    "ProductSession changed; reload before granting",
                    expected_revision=expected_revision,
                    current_revision=session.context_revision,
                ),
            )
        loaded_pack = next(
            (
                self.roster.loader.get(plugin_id)
                for plugin_id in self.roster.loader.loaded_ids()
                if (candidate := self.roster.loader.get(plugin_id)) is not None
                and candidate.instance_id == session.context.instance_id
            ),
            None,
        )
        if loaded_pack is None:
            return _jsonrpc_refusal(
                req_id,
                policy_rejection("instance_id", "session instance is not enabled"),
            )
        session_contribution = dict(session.context.contribution.to_payload())
        published = next(
            (
                row
                for row in loaded_pack.published
                if row.qualified_id == session_contribution.get("qualified_id")
                and row.package_version == session_contribution.get("package_version")
                and row.availability == "enabled"
            ),
            None,
        )
        if published is None:
            return _jsonrpc_refusal(
                req_id,
                policy_rejection("contribution", "session contribution is not enabled"),
            )
        if (
            not isinstance(op_id, str)
            or not isinstance(op_version, int)
            or isinstance(op_version, bool)
        ):
            return _jsonrpc_refusal(
                req_id, invalid_input("operation", "op_id and op_version are required")
            )
        descriptor = next(
            (
                item
                for item in self._operation_descriptors()
                if item.door_key == (op_id, op_version)
            ),
            None,
        )
        if descriptor is None:
            return _jsonrpc_refusal(
                req_id, policy_rejection("operation", "operation has no published descriptor")
            )
        required_point = {
            "qma.procedure.start": "graph_template",
            "qmb.backtest.run": "tool",
            "qmb.optimize.run": "tool",
            "qmb.analysis.project": "tool",
            "qmn.spot.paper.query": "tool",
        }.get(op_id)
        expected_contribution = {
            "qma.procedure.start": published.qualified_id,
            "qmb.backtest.run": "analysis-backtest:qmb",
            "qmb.optimize.run": "analysis-backtest:qmb",
            "qmb.analysis.project": "analysis-backtest:qmb",
            "qmn.spot.paper.query": SPOT_CONTRIBUTION,
        }.get(op_id)
        if (
            required_point is None
            or published.point != required_point
            or published.qualified_id != expected_contribution
        ):
            return _jsonrpc_refusal(
                req_id,
                policy_rejection(
                    "operation",
                    "operation adapter is not declared by this enabled contribution",
                    op_id=op_id,
                    contribution=published.qualified_id,
                    point=published.point,
                ),
            )
        if not isinstance(ceiling, Mapping):
            return _jsonrpc_refusal(
                req_id, invalid_input("parameter_ceiling", "allow_keys array required")
            )
        allowed_raw = cast("Mapping[str, object]", ceiling).get("allow_keys")
        if not isinstance(allowed_raw, list):
            return _jsonrpc_refusal(
                req_id, invalid_input("parameter_ceiling", "allow_keys array required")
            )
        allowed_items = cast("list[object]", allowed_raw)
        if any(not isinstance(key, str) for key in allowed_items):
            return _jsonrpc_refusal(
                req_id, invalid_input("parameter_ceiling", "allow_keys array required")
            )
        allowed = [cast("str", key) for key in allowed_items]
        accepted_keys = set(descriptor.configuration.required_keys) | set(
            descriptor.configuration.optional_keys
        )
        if any(key not in accepted_keys for key in allowed):
            return _jsonrpc_refusal(
                req_id, policy_rejection("parameter_ceiling", "ceiling exceeds operation schema")
            )
        if not set(descriptor.configuration.required_keys).issubset(set(allowed)):
            return _jsonrpc_refusal(
                req_id,
                invalid_input("parameter_ceiling", "ceiling must include required operation keys"),
            )
        if op_id == "qmn.spot.paper.query":
            spot_binding = self._spot_state_bindings.get(session.context.instance_id or "")
            if spot_binding is None:
                return _jsonrpc_refusal(
                    req_id, policy_rejection("spot_binding", "no host spot binding")
                )
            if session.context.account_scope != spot_binding.authority_scope:
                return _jsonrpc_refusal(
                    req_id, policy_rejection("account_scope", "host spot binding changed")
                )
            current_target = spot_binding.validate_target(
                contribution=published.qualified_id or "",
                package_version=published.package_version,
                config_revision=session.context.config_revision,
            )
            if is_refusal(current_target):
                return _jsonrpc_refusal(req_id, current_target)
        else:
            binding = backtest_binding(
                self.root, session.context.instance_id or "", session.context.config_revision
            )
            if is_refusal(binding):
                return _jsonrpc_refusal(req_id, binding)
        grant = self._product_sessions.host_grant(
            session_ref,
            expected_context_revision=expected_revision,
            op_id=descriptor.op_id,
            op_version=descriptor.version,
            effect_class=descriptor.effect_class.value,
            parameter_ceiling={"allow_keys": list(allowed)},
            expires_at=expires_at,
            scope_path=(),
        )
        if is_refusal(grant):
            return _jsonrpc_refusal(req_id, grant)
        grant_payload = dict(grant.value.to_payload())
        grant_payload["context_revision"] = expected_revision + 1
        return _jsonrpc_result(req_id, grant_payload)

    def _operation_descriptors(self) -> tuple[OperationDescriptor, ...]:
        descriptors = tuple(public_operation_descriptors())
        if self._spot_state_bindings:
            return (*descriptors, spot_query_descriptor())
        return descriptors

    def _execute_bound_product_operation(
        self,
        bound: BoundInvocation,
        *,
        originating_product_session_ref: str | None = None,
    ) -> Result[object]:
        """Trusted operation adapter; payload fields never supply owner or environment."""
        op_id = bound.envelope.op_id
        if op_id == "qmn.spot.paper.query":
            spot_binding = self._spot_state_bindings.get(bound.instance.instance_id)
            if spot_binding is None:
                return policy_rejection("spot_binding", "no host spot binding")
            target = spot_binding.validate_target(
                contribution=bound.contribution.qualified_id,
                package_version=bound.contribution.package_version,
                config_revision=bound.instance.config_revision,
            )
            if is_refusal(target):
                return target
            queried = spot_binding.query(bound.validated_payload)
            if is_refusal(queried):
                return queried
            return Ok(cast("object", queried.value))
        if op_id == "qma.procedure.start":
            configured = backtest_binding(
                self.root, bound.instance.instance_id, bound.instance.config_revision
            )
            if is_refusal(configured):
                return configured
            owner_id, _environment_ref = configured.value
            owner = self._mailboxes.quant_for(owner_id)
            if owner is None:
                return TypedRefusal(
                    category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
                    retryability=Retryability.AFTER_CONDITION,
                    context={
                        "reason": "operator-bound owner has no registered Quant record",
                        "owner_actor_id": owner_id.value,
                    },
                )
            procedure_id = bound.validated_payload.get("procedure_id")
            if not isinstance(procedure_id, str) or not procedure_id.strip():
                return invalid_input("procedure_id", "registered procedure id is required")
            template = self.nested_mission_host.templates.get(procedure_id.strip())
            if template is None:
                return TypedRefusal(
                    category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
                    retryability=Retryability.AFTER_CONDITION,
                    context={
                        "reason": "procedure id does not resolve to one registered Graph Template",
                        "procedure_id": procedure_id,
                    },
                )
            compiled_parent = self.nested_mission_host.compile_parent(
                owner=owner,
                template=template,
                goal=procedure_id.strip(),
                originating_product_session_ref=originating_product_session_ref,
            )
            if is_refusal(compiled_parent):
                return compiled_parent
            return Ok(cast("object", compiled_parent.value))
        if op_id in {"qmb.backtest.run", "qmb.optimize.run"}:
            qmb_command = op_id.removeprefix("qmb.")
            binding = backtest_binding(
                self.root, bound.instance.instance_id, bound.instance.config_revision
            )
            if is_refusal(binding):
                return binding
            owner_id, environment_ref = binding.value
            owner = self._mailboxes.quant_for(owner_id)
            if owner is None:
                return TypedRefusal(
                    category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
                    retryability=Retryability.AFTER_CONDITION,
                    context={
                        "reason": "QMB binding owner has no registered Quant record",
                        "owner_actor_id": owner_id.value,
                    },
                )
            payload = bound.validated_payload
            if "owner_actor_id" in payload or "environment_ref" in payload:
                return policy_rejection(
                    "payload", "QMB owner and environment are operator-bound fields"
                )
            spec_fp1 = payload.get("run_fp1")
            resolved = self.experiments.resolve(spec_fp1)
            if is_refusal(resolved):
                return resolved
            evidence_ref = payload.get("evidence_ref")
            if not isinstance(evidence_ref, str) or not evidence_ref.strip():
                return invalid_input(
                    "evidence_ref",
                    "qmb.backtest.run requires a persisted QMB replay-request fingerprint",
                )
            environment_kind = environment_ref.removeprefix("env:")
            if self._runtime_composition.environments.declaration(environment_kind) is None:
                return NoEnvironment.of(kind=environment_kind, reason="kind_unbound")
            dispatched = self.task_dispatcher.dispatched_task_for_invocation(
                bound.envelope.logical_invocation_id
            )
            if is_refusal(dispatched):
                return dispatched
            accepted_task, accepted_lease, accepted_row = dispatched.value
            current_ledger = self.task_dispatcher.ledgers.get(accepted_task.id)
            pinned_deployment = accepted_task.inputs.get("model_deployment_ref")
            expected_input_hash = self.task_dispatcher.expected_operation_input_hash(
                accepted_task.id
            )
            if is_refusal(expected_input_hash):
                return expected_input_hash
            received_input_hash = compute_input_hash(
                bound.validated_payload,
                descriptor=bound.descriptor,
            )
            if is_refusal(received_input_hash):
                return received_input_hash
            acceptance_checks = {
                "task_running": accepted_task.state is TaskMissionState.RUNNING,
                "lease_owner": accepted_lease.owner == owner.actor_id,
                "task_owner": accepted_task.owner == owner.actor_id,
                "lease_task": accepted_lease.task_id == resolved.value.dispatch_lease.task_id,
                "lease_mission": accepted_lease.mission_id
                == resolved.value.dispatch_lease.mission_id,
                "environment": resolved.value.spec.environment_ref == environment_ref,
                "ledger_present": current_ledger is not None,
                "deployment_pinned": isinstance(pinned_deployment, str)
                and bool(pinned_deployment.strip()),
                "run_fp1": accepted_task.inputs.get("run_fp1") == resolved.value.spec.spec_fp1,
                "evidence_ref": accepted_task.inputs.get("evidence_ref") == evidence_ref,
                "input_op": accepted_task.inputs.get("op_id") == bound.envelope.op_id,
                "input_version": accepted_task.inputs.get("op_version")
                == bound.envelope.op_version,
                "input_instance": accepted_task.inputs.get("instance_id")
                == bound.envelope.instance_id,
                "input_revision": accepted_task.inputs.get("config_revision")
                == bound.envelope.config_revision,
                "target_op": accepted_row.target.get("op_id") == bound.envelope.op_id,
                "target_version": accepted_row.target.get("op_version")
                == bound.envelope.op_version,
                "target_instance": accepted_row.target.get("instance_id")
                == bound.envelope.instance_id,
                "target_revision": accepted_row.target.get("config_revision")
                == bound.envelope.config_revision,
                "task_input_hash": expected_input_hash.value == bound.envelope.input_hash,
                "received_input_hash": received_input_hash.value == bound.envelope.input_hash,
            }
            if (
                accepted_task.state is not TaskMissionState.RUNNING
                or accepted_lease.owner != owner.actor_id
                or accepted_task.owner != owner.actor_id
                or accepted_lease.task_id != resolved.value.dispatch_lease.task_id
                or accepted_lease.mission_id != resolved.value.dispatch_lease.mission_id
                or resolved.value.spec.environment_ref != environment_ref
                or current_ledger is None
                or isinstance(current_ledger.attempt_no, bool)
                or current_ledger.attempt_no < 0
                or not isinstance(pinned_deployment, str)
                or not pinned_deployment.strip()
                or accepted_task.inputs.get("run_fp1") != resolved.value.spec.spec_fp1
                or accepted_task.inputs.get("evidence_ref") != evidence_ref
                or accepted_task.inputs.get("op_id") != bound.envelope.op_id
                or accepted_task.inputs.get("op_version") != bound.envelope.op_version
                or accepted_task.inputs.get("instance_id") != bound.envelope.instance_id
                or accepted_task.inputs.get("config_revision") != bound.envelope.config_revision
                or accepted_row.target.get("op_id") != bound.envelope.op_id
                or accepted_row.target.get("op_version") != bound.envelope.op_version
                or accepted_row.target.get("instance_id") != bound.envelope.instance_id
                or accepted_row.target.get("config_revision") != bound.envelope.config_revision
                or expected_input_hash.value != bound.envelope.input_hash
                or received_input_hash.value != bound.envelope.input_hash
            ):
                return policy_rejection(
                    "dispatch_lease",
                    "QMB execution requires a current dispatched outbox Task bound to this "
                    "operation, complete payload, spec, evidence, deployment, and attempt",
                    task_id=accepted_task.id,
                    failed_checks=tuple(key for key, okay in acceptance_checks.items() if not okay),
                    dispatched_config_revision=accepted_row.target.get("config_revision"),
                    request_config_revision=bound.envelope.config_revision,
                )
            if bound.validated_payload.get("as_of") is not None:
                return TypedRefusal(
                    category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
                    retryability=Retryability.AFTER_CONDITION,
                    context={
                        "reason": (
                            "the current QMB runtime transport cannot preserve "
                            "the CT-40 as_of input"
                        ),
                        "op_id": bound.envelope.op_id,
                        "field": "as_of",
                    },
                )
            runtime_preflight = self.backtesting.preflight_registered_run(
                owner=owner.actor_id,
                task_id=accepted_task.id,
                environment_ref=environment_ref,
                experiment_spec_fp1=resolved.value.spec.spec_fp1,
                evidence_ref=evidence_ref,
                command=qmb_command,
            )
            if is_refusal(runtime_preflight):
                return runtime_preflight
            # The read-only QMB preparation is a subprocess and can take long
            # enough for the dispatched Task or lease to change. Re-resolve the
            # authoritative outbox/Task/lease/attempt/deployment immediately
            # before recording receiver acceptance or placing a QMB job.
            refreshed = self.task_dispatcher.dispatched_task_for_invocation(
                bound.envelope.logical_invocation_id
            )
            if is_refusal(refreshed):
                return refreshed
            fresh_task, fresh_lease, fresh_row = refreshed.value
            fresh_ledger = self.task_dispatcher.ledgers.get(fresh_task.id)
            fresh_input_hash = self.task_dispatcher.expected_operation_input_hash(fresh_task.id)
            if is_refusal(fresh_input_hash):
                return fresh_input_hash
            if (
                fresh_task.id != accepted_task.id
                or fresh_task.state is not TaskMissionState.RUNNING
                or fresh_task.owner != owner.actor_id
                or fresh_lease != accepted_lease
                or fresh_row.graph_run_id != accepted_row.graph_run_id
                or fresh_row.successor_node_id != accepted_row.successor_node_id
                or fresh_row.envelope_hash != accepted_row.envelope_hash
                or fresh_ledger is None
                or fresh_ledger.attempt_no != current_ledger.attempt_no
                or fresh_task.inputs.get("model_deployment_ref") != pinned_deployment
                or fresh_task.inputs.get("run_fp1") != resolved.value.spec.spec_fp1
                or fresh_task.inputs.get("evidence_ref") != evidence_ref
                or fresh_input_hash.value != bound.envelope.input_hash
            ):
                return policy_rejection(
                    "dispatch_lease",
                    "QMB preparation completed for a Task authority that is no longer current",
                    task_id=accepted_task.id,
                )
            # The authenticated worker route is the acceptance point. Persist its
            # exact current Task/lease/attempt receipt only after the incoming
            # operation and registered spec match the dispatched Task inputs.
            accepted_receipt = self.task_dispatcher.accept_worker_invocation(
                bound.envelope.logical_invocation_id
            )
            if is_refusal(accepted_receipt):
                return accepted_receipt
            if (
                accepted_receipt.value.result.get("operation_input_hash")
                != expected_input_hash.value
            ):
                return policy_rejection(
                    "receiver_acceptance",
                    "accepted worker receipt binds the full compiled public input",
                    task_id=accepted_task.id,
                )
            accepted = self.task_dispatcher.accepted_task_for_invocation(
                bound.envelope.logical_invocation_id
            )
            if is_refusal(accepted):
                return accepted
            accepted_task, accepted_lease, accepted_row, receiver = accepted.value
            worker_acceptance = receiver.result
            if (
                worker_acceptance.get("attempt_no") != current_ledger.attempt_no
                or worker_acceptance.get("model_deployment_ref") != pinned_deployment
            ):
                return policy_rejection(
                    "receiver_acceptance",
                    "worker receipt retains this current Task attempt and deployment",
                    task_id=accepted_task.id,
                )
            placement = self.backtesting.invoke(
                QMB_BACKTEST_TOOL_ID,
                owner=owner.actor_id,
                task_id=accepted_task.id,
                environment_ref=environment_ref,
                experiment_spec_fp1=resolved.value.spec.spec_fp1,
                evidence_ref=evidence_ref,
                dispatch_lease=accepted_lease,
                model_deployment_ref=pinned_deployment,
                worker_acceptance=worker_acceptance,
                originating_product_session_ref=originating_product_session_ref,
                command=qmb_command,
            )
            if is_refusal(placement):
                return placement
            return Ok(cast("object", placement.value))
        if op_id != "qmb.analysis.project":
            return TypedRefusal(
                category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
                retryability=Retryability.AFTER_CONDITION,
                context={
                    "reason": "no host adapter is available for this enabled operation",
                    "op_id": op_id,
                    "instance_id": bound.instance.instance_id,
                },
            )
        binding = backtest_binding(
            self.root, bound.instance.instance_id, bound.instance.config_revision
        )
        if is_refusal(binding):
            return binding
        owner, environment_ref = binding.value
        quant = self._mailboxes.quant_for(owner)
        if quant is None:
            return TypedRefusal(
                category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
                retryability=Retryability.AFTER_CONDITION,
                context={
                    "reason": "QMB binding owner has no registered Quant record",
                    "owner_actor_id": owner.value,
                },
            )
        environment_kind = environment_ref.removeprefix("env:")
        if self._runtime_composition.environments.declaration(environment_kind) is None:
            return NoEnvironment.of(kind=environment_kind, reason="kind_unbound")
        payload = bound.validated_payload
        if "owner_actor_id" in payload or "environment_ref" in payload:
            return policy_rejection(
                "payload", "QMB owner and environment are operator-bound fields"
            )
        projected = self.backtesting.project_completed_run(
            owner=quant.actor_id,
            environment_ref=environment_ref,
            run_fp1=payload.get("run_fp1"),
            as_of=payload.get("as_of"),
        )
        if is_refusal(projected):
            return projected
        view_ref = fingerprint(dict(projected.value))
        if is_refusal(view_ref):
            return view_ref
        # v1 returns a content reference and its inline bytes. This read does
        # not persist a view or publish analysis into the Experiment Ledger.
        return Ok(
            {"fp1": view_ref.value.value, "kind": "saved-view", "body": dict(projected.value)}
        )

    def _dispatch_cancel_job(
        self,
        connection: WireConnection,
        request: Mapping[str, object],
        req_id: object,
    ) -> dict[str, object]:
        """Serve originating-session cancel as an additive CT-40 command."""
        capability = require_cancel_job_capability(connection.capabilities)
        if is_refusal(capability):
            return _jsonrpc_refusal(req_id, capability)
        authorized = connection.authorize_command(WireCommand.CANCEL_JOB.value)
        if is_refusal(authorized):
            return _jsonrpc_refusal(req_id, authorized)
        raw_params = request.get("params")
        if not isinstance(raw_params, Mapping):
            return _jsonrpc_error(
                req_id,
                code=_JSONRPC_INVALID_REQUEST,
                message="params must be an object",
            )
        params = cast("Mapping[str, object]", raw_params)
        # The client does not select authority. The durable handle supplies its
        # origin; resolve that row only after locating the exact durable handle.
        handle_id = params.get("handle_id")
        if not isinstance(handle_id, str):
            return _jsonrpc_refusal(
                req_id,
                invalid_input("handle_id", "cancel_job requires a durable JobHandle id"),
            )
        handle = self.backtesting.jobs.handle_for(handle_id)
        if handle is None:
            return _jsonrpc_refusal(
                req_id,
                invalid_input(
                    "handle_id", "cancel_job requires a minted JobHandle", given=handle_id
                ),
            )
        origin = handle.originating_product_session_ref
        if origin is None:
            return _jsonrpc_refusal(
                req_id,
                policy_rejection(
                    "originating_product_session_ref",
                    "UI cancel is unavailable for a headless JobHandle",
                    handle_id=handle_id,
                ),
            )
        session = self._product_sessions.get(origin)
        if is_refusal(session):
            return _jsonrpc_refusal(req_id, session)
        authenticated_operator = self._operator_principal()
        pairing_record_id = connection.pairing_record_id
        pairing = (
            None
            if pairing_record_id is None
            else load_pairing_session(self.sqlite, pairing_record_id)
        )
        if (
            session.value.principal != PrincipalClass.OPERATOR.value
            or connection.principal_class is not PrincipalClass.OPERATOR
            or authenticated_operator is None
            or pairing is None
            or pairing.revoked
            or pairing.operator_principal != authenticated_operator
        ):
            return _jsonrpc_refusal(
                req_id,
                policy_rejection(
                    "operator_principal",
                    "cancel_job requires the operator who owns the local paired session",
                    originating_principal_class=session.value.principal,
                    connection_principal_class=(
                        None
                        if connection.principal_class is None
                        else connection.principal_class.value
                    ),
                    pairing_record_id=pairing_record_id,
                    pairing_operator_principal=(
                        None if pairing is None else pairing.operator_principal
                    ),
                ),
            )
        cancel = (
            self.jobs.cancel_from_product_session
            if self._canonical_requests is not None
            and self._canonical_requests.owns_job(handle.job_id)
            else self.backtesting.cancel_from_product_session
        )
        cancelled = cancel(
            params,
            principal_class=connection.principal_class or "",
            operator_principal=authenticated_operator,
            # Pair admission is bound to this daemon's sole local_operator. The
            # CT-42 ProductSession record stores PrincipalClass, not an identity;
            # its operator class therefore resolves to that sole durable ID.
            originating_session_principal=authenticated_operator,
            producer_id=connection.producer_id,
            wire_id=req_id,
        )
        if is_refusal(cancelled):
            return _jsonrpc_refusal(req_id, cancelled)
        return _jsonrpc_result(req_id, cancelled.value.to_payload())

    def _dispatch_editor_draft_command(
        self,
        connection: WireConnection,
        request: Mapping[str, object],
        req_id: object,
        *,
        publish: bool,
    ) -> dict[str, object]:
        method = (
            WireCommand.PUBLISH_EDITOR_DRAFT.value
            if publish
            else WireCommand.SAVE_EDITOR_DRAFT.value
        )
        if (
            connection.principal_class is not PrincipalClass.OPERATOR
            or self._operator_principal() is None
        ):
            return _jsonrpc_refusal(
                req_id,
                policy_rejection(
                    "principal_class",
                    "editor drafts require an authenticated operator principal",
                ),
            )
        capability = require_editor_draft_capability(connection.capabilities, method)
        if is_refusal(capability):
            return _jsonrpc_refusal(req_id, capability)
        authorized = connection.authorize_command(method)
        if is_refusal(authorized):
            return _jsonrpc_refusal(req_id, authorized)
        params = request.get("params")
        if not isinstance(params, Mapping):
            return _jsonrpc_error(
                req_id,
                code=_JSONRPC_INVALID_REQUEST,
                message="params must be an object",
            )
        payload_params = cast(Mapping[str, object], params)
        if publish:
            result = self._editor_drafts.publish_editor_draft(
                payload_params,
                operator_principal=self._operator_principal(),
                capabilities=connection.capabilities,
                principal_class=connection.principal_class,
            )
            if is_refusal(result):
                return _jsonrpc_refusal(req_id, result)
            return _jsonrpc_result(req_id, result.value)
        saved = self._editor_drafts.save_editor_draft(
            payload_params,
            operator_principal=self._operator_principal(),
            capabilities=connection.capabilities,
        )
        if is_refusal(saved):
            return _jsonrpc_refusal(req_id, saved)
        return _jsonrpc_result(req_id, saved.value.to_payload())

    def _gate_live_invoke(
        self,
        method: object,
        request: Mapping[str, object],
        req_id: object,
    ) -> dict[str, object] | None:
        """Refuse start_mission / launch_task that cite fp1 until transfer_complete."""
        _ = method
        raw_params = request.get("params")
        params: Mapping[str, object] = (
            cast("Mapping[str, object]", raw_params) if isinstance(raw_params, Mapping) else {}
        )
        if any(key in params for key in ("editor_draft_id", "editor_revision", "unsaved_buffer")):
            return _jsonrpc_refusal(
                req_id,
                policy_rejection(
                    "invoke_target",
                    "mutable or saved editor drafts are not runnable; publish and enable first",
                    refusal="draft_not_runnable",
                    minted_job_handle=False,
                ),
            )
        fp1 = params.get("fp1")
        instance_id = params.get("instance_id")
        if not (isinstance(fp1, str) and fp1.strip() != ""):
            return None
        if self._editor_drafts.is_editor_revision(fp1):
            return _jsonrpc_refusal(
                req_id,
                policy_rejection(
                    "fp1",
                    "saved editor draft revisions are not runnable; publish and enable first",
                    refusal="draft_not_runnable",
                    minted_job_handle=False,
                ),
            )
        gated = gate_invoke_until_transfer_complete(
            self._transfers,
            fp1=fp1,
            instance_id=instance_id,
        )
        if is_refusal(gated):
            return _jsonrpc_refusal(req_id, gated)
        return None

    def _dispatch_transfer_artifact(
        self,
        connection: WireConnection,
        request: Mapping[str, object],
        req_id: object,
    ) -> dict[str, object]:
        """Serve addable transfer_artifact on the live paired CT-40 socket."""
        gated = require_transfer_artifact_capability(connection.capabilities)
        if is_refusal(gated):
            return _jsonrpc_refusal(req_id, gated)
        authorized = connection.authorize_command(WireCommand.TRANSFER_ARTIFACT.value)
        if is_refusal(authorized):
            return _jsonrpc_refusal(req_id, authorized)
        raw_params = request.get("params")
        if not isinstance(raw_params, Mapping):
            return _jsonrpc_error(
                req_id,
                code=_JSONRPC_INVALID_REQUEST,
                message="params must be an object",
            )
        principal = connection.principal_class
        if principal is None:
            return _jsonrpc_error(
                req_id,
                code=_JSONRPC_APP_ERROR,
                message="unauthenticated",
            )
        operator_id = connection.pairing_record_id
        if operator_id is None and self._local_operator is not None:
            operator_id = self._local_operator.principal_id
        transferred = handle_transfer_artifact(
            self._transfers,
            dict(cast("Mapping[str, object]", raw_params)),
            capabilities=connection.capabilities,
            principal_class=principal,
            operator_principal=operator_id,
        )
        if is_refusal(transferred):
            return _jsonrpc_refusal(req_id, transferred)
        return _jsonrpc_result(req_id, transferred.value.to_payload())

    def _dispatch_transfer_complete(
        self,
        connection: WireConnection,
        request: Mapping[str, object],
        req_id: object,
    ) -> dict[str, object]:
        """Serve dest-authored transfer_complete on the live CT-40 socket."""
        gated = require_transfer_complete_capability(connection.capabilities)
        if is_refusal(gated):
            return _jsonrpc_refusal(req_id, gated)
        authorized = connection.authorize_command(WireCommand.TRANSFER_COMPLETE.value)
        if is_refusal(authorized):
            return _jsonrpc_refusal(req_id, authorized)
        raw_params = request.get("params")
        if not isinstance(raw_params, Mapping):
            return _jsonrpc_error(
                req_id,
                code=_JSONRPC_INVALID_REQUEST,
                message="params must be an object",
            )
        principal = connection.principal_class
        if principal is None:
            return _jsonrpc_error(
                req_id,
                code=_JSONRPC_APP_ERROR,
                message="unauthenticated",
            )
        completed = handle_transfer_complete(
            self._transfers,
            dict(cast("Mapping[str, object]", raw_params)),
            capabilities=connection.capabilities,
            principal_class=principal,
            credential_ref=connection.credential_ref,
        )
        if is_refusal(completed):
            return _jsonrpc_refusal(req_id, completed)
        return _jsonrpc_result(req_id, completed.value.to_payload())

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

    def _release(self, *, release_process_gate: bool = True) -> None:
        if self._closed:
            return
        self._closed = True
        self._bound = None
        if self._agent_requests is not None:
            self._agent_requests.close()
        self._journal.close()
        closer = getattr(self.backtesting.transport, "close", None)
        try:
            if callable(closer):
                closer()
        finally:
            self._substrate.close()
            if release_process_gate:
                with _process_gate.lock:
                    if _process_gate.holder is self:
                        _process_gate.holder = None

    def __enter__(self) -> DaemonProcess:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
