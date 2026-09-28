"""``qmb host start|status|stop|configure|rotate-control`` (Stories 67.1–67.3).

Do not reuse package ``qmb.host`` (CT-33 HostedBot). QMB never writes daemon
sqlite. The browser does not spawn Python. Pair is not this story.
"""

from __future__ import annotations

import ctypes
import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Final, cast

from qmf.core.refusal import Ok, RefusalCategory, Result, Retryability, TypedRefusal

from qmb._refuse import invalid, policy, storage, unavailable

__all__ = [
    "BROWSER_SPAWNS_PYTHON",
    "CT40_BIND_PORT",
    "DAEMON_LOCK_NAME",
    "DAEMON_SPAWN_MODULE",
    "HOST_COMMANDS",
    "HOST_CONFIGURE_COMMANDS",
    "HOST_CONTROL_BIND_NAME",
    "HOST_CONTROL_FILE",
    "INSPECT_CWD_RELATIVE_ROOT",
    "INSPECT_SHA_COMMAND_GROUPS",
    "PAIRING_SESSION_TTL_REGISTRY_KEY",
    "QMB_HOST_CONFIGURE_EXISTED_AT_INSPECT_SHA",
    "QMB_HOST_EXISTED_AT_INSPECT_SHA",
    "QMB_HOST_ROTATE_CONTROL_EXISTED_AT_INSPECT_SHA",
    "START_GRANTS",
    "START_ORCHESTRATES_MISSIONS",
    "START_STARTS_QMN",
    "STOP_CANCELS_QMN",
    "STOP_STOPS_REMOTE",
    "claim_host_configure_existed_at_inspect_sha",
    "claim_qmb_host_existed_at_inspect_sha",
    "claim_rotate_control_existed_at_inspect_sha",
    "claim_types_absent_at_inspect_sha",
    "invoke_host_configure_pairing_ttl",
    "invoke_host_rotate_control",
    "invoke_host_start",
    "invoke_host_status",
    "invoke_host_stop",
    "product_daemon_root",
    "redact_host_surface",
]


HOST_COMMANDS: Final[tuple[str, ...]] = (
    "start",
    "status",
    "stop",
    "configure",
    "rotate-control",
)
HOST_CONFIGURE_COMMANDS: Final[tuple[str, ...]] = ("pairing-ttl",)
PAIRING_SESSION_TTL_REGISTRY_KEY: Final[str] = "registry:pairing.session_ttl"
QMB_HOST_CONFIGURE_EXISTED_AT_INSPECT_SHA: Final[bool] = False
QMB_HOST_ROTATE_CONTROL_EXISTED_AT_INSPECT_SHA: Final[bool] = False
DAEMON_LOCK_NAME: Final[str] = ".daemon_writer"
DAEMON_SPAWN_MODULE: Final[str] = "qma.daemon"
HOST_CONTROL_FILE: Final[str] = "host_control"
HOST_CONTROL_BIND_NAME: Final[str] = "host_control.bind"
CT40_BIND_PORT: Final[int] = 8765
INSPECT_CWD_RELATIVE_ROOT: Final[str] = "qma-daemon-data"
QMB_HOST_EXISTED_AT_INSPECT_SHA: Final[bool] = False
INSPECT_SHA: Final[str] = "34c148be"
INSPECT_SHA_COMMAND_GROUPS: Final[tuple[str, ...]] = (
    "backtest",
    "data",
    "optimize",
    "sweep",
    "robustness",
    "ledger",
    "library",
    "analysis",
    "config",
)
START_ORCHESTRATES_MISSIONS: Final[bool] = False
START_GRANTS: Final[bool] = False
START_STARTS_QMN: Final[bool] = False
BROWSER_SPAWNS_PYTHON: Final[bool] = False
STOP_CANCELS_QMN: Final[bool] = False
STOP_STOPS_REMOTE: Final[bool] = False
_MAX_FRAME: Final[int] = 65536
_WAIT_ATTEMPTS: Final[int] = 100
_REDACT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "authorization",
        "host_control",
        "pairing_proof",
        "pending_code",
        "pairing_code",
        "code",
        "token",
        "secret",
        "password",
        "bearer",
        "credential_value",
        "access_token",
        "refresh_token",
        "api_key",
    }
)
_REDACT_PREFIXES: Final[tuple[str, ...]] = ("qmx.pair.", "pairing:")


def product_daemon_root(
    *,
    system: str | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | str | None = None,
) -> Path:
    """OS product data root. Cwd-relative ``qma-daemon-data`` is not this path."""
    env = os.environ if environ is None else environ
    plat = sys.platform if system is None else system
    if plat.startswith("win"):
        local = env.get("LOCALAPPDATA")
        if not local:
            base = Path.home() if home is None else Path(home)
            local = str(base / "AppData" / "Local")
        return Path(local) / "QMX" / "qma-daemon"
    if plat == "darwin":
        base = Path(env["HOME"]) if "HOME" in env else (Path.home() if home is None else Path(home))
        return base / "Library" / "Application Support" / "QMX" / "qma-daemon"
    xdg = env.get("XDG_STATE_HOME")
    if xdg:
        return Path(xdg) / "qmx" / "qma-daemon"
    base = Path(env["HOME"]) if "HOME" in env else (Path.home() if home is None else Path(home))
    return base / ".local" / "state" / "qmx" / "qma-daemon"


def claim_qmb_host_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming ``qmb host`` existed at inspect SHA ``34c148be`` fails."""
    if existed is True or existed == "true":
        return policy(
            "host",
            "qmb host was absent at inspect SHA 34c148be; COMMAND_GROUPS had no host",
            existed_at_inspect_sha=False,
            inspect_sha=INSPECT_SHA,
            inspect_groups=list(INSPECT_SHA_COMMAND_GROUPS),
        )
    if existed is not False:
        return invalid(
            "existed_at_inspect_sha",
            "inspect-SHA claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def claim_host_configure_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming ``qmb host configure`` existed at inspect SHA ``34c148be`` fails."""
    if existed is True or existed == "true":
        return policy(
            "host.configure",
            "qmb host configure was absent at inspect SHA 34c148be",
            existed_at_inspect_sha=False,
            inspect_sha=INSPECT_SHA,
        )
    if existed is not False:
        return invalid(
            "existed_at_inspect_sha",
            "inspect-SHA claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def claim_rotate_control_existed_at_inspect_sha(existed: object) -> Result[bool]:
    """Claiming ``qmb host rotate-control`` existed at inspect SHA ``34c148be`` fails."""
    if existed is True or existed == "true":
        return policy(
            "host.rotate-control",
            "qmb host rotate-control was absent at inspect SHA 34c148be",
            existed_at_inspect_sha=False,
            inspect_sha=INSPECT_SHA,
        )
    if existed is not False:
        return invalid(
            "existed_at_inspect_sha",
            "inspect-SHA claim is a boolean",
            given=repr(existed),
        )
    return Ok(False)


def claim_types_absent_at_inspect_sha(absent: object) -> Result[bool]:
    """Claiming Envelope / GrantRecord / product_session types were absent fails."""
    if absent is True or absent == "true":
        return policy(
            "inspect_types",
            "Envelope, GrantRecord, and product_session types existed at inspect "
            "SHA 34c148be; claiming they were absent fails",
            types_existed_at_inspect_sha=True,
            inspect_sha=INSPECT_SHA,
        )
    if absent is not False:
        return invalid(
            "types_absent_at_inspect_sha",
            "inspect-SHA absence claim is a boolean",
            given=repr(absent),
        )
    return Ok(False)


def redact_host_surface(value: object) -> object:
    """Redact Authorization, qmx.pair.*, proofs, pending codes, and host_control."""
    if isinstance(value, Mapping):
        body = cast("Mapping[object, object]", value)
        out: dict[str, object] = {}
        for key, item in body.items():
            name = str(key)
            folded = name.casefold()
            if folded == "pairing_record_id" or folded.endswith("_record_id"):
                out[name] = redact_host_surface(item)
                continue
            if folded in _REDACT_KEYS or folded.startswith("qmx.pair."):
                out[name] = "[redacted]"
                continue
            out[name] = redact_host_surface(item)
        return out
    if isinstance(value, list):
        items = cast("list[object]", value)
        return [redact_host_surface(item) for item in items]
    if isinstance(value, tuple):
        items = cast("tuple[object, ...]", value)
        return [redact_host_surface(item) for item in items]
    if isinstance(value, str) and any(
        value.strip().startswith(prefix) for prefix in _REDACT_PREFIXES
    ):
        return "[redacted]"
    return value


def _as_root(root: object, environ: Mapping[str, str] | None) -> Path:
    if isinstance(root, Path):
        return root
    if isinstance(root, str) and root.strip() != "":
        return Path(root)
    return product_daemon_root(environ=environ)


def _pid_is_live(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        access = 0x1000  # PROCESS_QUERY_LIMITED_INFORMATION
        handle = ctypes.windll.kernel32.OpenProcess(access, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
    except (OSError, ProcessLookupError):
        return False
    return True


def _read_lock_pid(root: Path) -> int | None:
    path = root / DAEMON_LOCK_NAME
    if not path.is_file():
        return None
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    pid = cast("dict[str, object]", raw).get("pid")
    if isinstance(pid, bool) or not isinstance(pid, int):
        return None
    return pid


def _live_lock_pid(root: Path) -> int | None:
    pid = _read_lock_pid(root)
    if pid is None:
        return None
    if _pid_is_live(pid):
        return pid
    return None


def _drop_stale_lock(root: Path) -> None:
    pid = _read_lock_pid(root)
    if pid is None:
        return
    if _pid_is_live(pid):
        return
    path = root / DAEMON_LOCK_NAME
    try:
        path.unlink()
    except OSError:
        return


def _encode_frame(payload: Mapping[str, object]) -> bytes:
    raw = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    return len(raw).to_bytes(4, "big") + raw


def _read_token(root: Path) -> Result[str]:
    path = root / HOST_CONTROL_FILE
    try:
        if not path.is_file():
            return policy(
                "host_control",
                "current host_control is not readable",
                root=str(root),
            )
        token = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        return storage("host_control", f"could not read host_control: {exc}", root=str(root))
    if not token:
        return policy(
            "host_control",
            "current host_control is not readable",
            root=str(root),
        )
    return Ok(token)


def _read_bind(root: Path) -> Result[tuple[str, int]]:
    path = root / HOST_CONTROL_BIND_NAME
    try:
        if not path.is_file():
            return unavailable(
                "host_control.bind",
                "host-control bind file is missing",
                root=str(root),
            )
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return storage(
            "host_control.bind",
            f"could not read host_control.bind: {exc}",
            root=str(root),
        )
    if not isinstance(raw, dict):
        return invalid("host_control.bind", "bind file must be a JSON object")
    body = cast("dict[str, object]", raw)
    host = body.get("host")
    port = body.get("port")
    if not isinstance(host, str) or not host.strip():
        return invalid("host_control.bind", "bind host is missing")
    if isinstance(port, bool) or not isinstance(port, int) or port <= 0:
        return invalid("host_control.bind", "bind port is missing")
    if port == CT40_BIND_PORT:
        return policy(
            "host_control",
            "host-control must bind outside port 8765",
            port=port,
        )
    return Ok((host, port))


def _host_control_call(
    root: Path,
    verb: str,
    *,
    timeout_s: float = 2.0,
    fields: Mapping[str, object] | None = None,
) -> Result[Mapping[str, object]]:
    token = _read_token(root)
    if not isinstance(token, Ok):
        return token
    bound = _read_bind(root)
    if not isinstance(bound, Ok):
        return bound
    host, port = bound.value
    request: dict[str, object] = {"verb": verb, "host_control": token.value}
    if fields is not None:
        for key, item in fields.items():
            name = str(key)
            if name in {"verb", "host_control"}:
                continue
            request[name] = item
    try:
        with socket.create_connection((host, port), timeout=timeout_s) as sock:
            sock.sendall(_encode_frame(request))
            header = _recv_exact(sock, 4)
            size = int.from_bytes(header, "big")
            if size < 1 or size > _MAX_FRAME:
                return storage("host_control", "host-control response frame refused", size=size)
            body = _recv_exact(sock, size)
            parsed: object = json.loads(body.decode("utf-8"))
    except (OSError, json.JSONDecodeError, TimeoutError, ValueError) as exc:
        return storage("host_control", f"host-control call failed: {exc}", verb=verb)
    if not isinstance(parsed, dict):
        return invalid("host_control", "host-control response must be an object")
    payload = cast("dict[str, object]", parsed)
    redacted = redact_host_surface(payload)
    if not isinstance(redacted, dict):
        return invalid("host_control", "redacted host-control response must be an object")
    return Ok(cast("dict[str, object]", redacted))


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        piece = sock.recv(size - len(chunks))
        if not piece:
            raise OSError("host-control connection closed")
        chunks.extend(piece)
    return bytes(chunks)


def _spawn_argv(python: str | None) -> tuple[str, ...]:
    exe = sys.executable if python is None else python
    return (exe, "-m", DAEMON_SPAWN_MODULE)


def _default_spawn(
    argv: tuple[str, ...],
    *,
    env: Mapping[str, str],
    root: Path | None = None,
) -> int:
    _ = root
    copied = dict(env)
    if os.name == "nt":
        proc = subprocess.Popen(
            argv,
            env=copied,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    else:
        proc = subprocess.Popen(
            argv,
            env=copied,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    return int(proc.pid)


def _wait_attempts(value: object) -> Result[int]:
    if value is None:
        return Ok(_WAIT_ATTEMPTS)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return invalid("wait_attempts", "wait_attempts is a positive int")
    return Ok(value)


def _pause(sleeper: object) -> None:
    if callable(sleeper):
        sleeper(0.05)
        return
    time.sleep(0.05)


def _id_list(value: object) -> list[object]:
    if isinstance(value, list):
        return list(cast("list[object]", value))
    if isinstance(value, tuple):
        return list(cast("tuple[object, ...]", value))
    return []


def _ready(root: Path) -> bool:
    pid = _live_lock_pid(root)
    if pid is None:
        return False
    return (root / HOST_CONTROL_BIND_NAME).is_file()


def _environ_map(environ: object) -> Result[Mapping[str, str] | None]:
    if environ is None:
        return Ok(None)
    if isinstance(environ, Mapping):
        return Ok(cast("Mapping[str, str]", environ))
    return invalid("environ", "environ is a string mapping")


def _payload_refusal(payload: Mapping[str, object], *, verb: str) -> Result[Mapping[str, object]]:
    if payload.get("ok") is not False:
        return Ok(payload)
    refusal = payload.get("refusal")
    if isinstance(refusal, Mapping):
        body = cast("Mapping[str, object]", refusal)
        category = body.get("category")
        context = body.get("context")
        if isinstance(category, str) and isinstance(context, Mapping):
            try:
                parsed = RefusalCategory(category)
            except ValueError:
                parsed = RefusalCategory.POLICY_REJECTION
            return TypedRefusal(
                category=parsed,
                retryability=Retryability.NO,
                context=dict(cast("Mapping[str, object]", context)),
            )
    return policy("host_control", f"host-control {verb} refused")


def invoke_host_start(
    *,
    root: object = None,
    environ: object = None,
    spawn: object = None,
    python: object = None,
    wait_attempts: object = None,
    sleeper: object = None,
) -> Result[Mapping[str, object]]:
    """Set product ``QMA_DAEMON_ROOT`` and spawn if ``.daemon_writer`` is free."""
    env_map: Mapping[str, str] | None
    if environ is None:
        env_map = None
    elif isinstance(environ, Mapping):
        env_map = cast("Mapping[str, str]", environ)
    else:
        return invalid("environ", "environ is a string mapping")
    target = _as_root(root, env_map)
    if target.name == INSPECT_CWD_RELATIVE_ROOT and not target.is_absolute():
        return policy(
            "QMA_DAEMON_ROOT",
            "cwd-relative qma-daemon-data is not the product root",
            given=str(target),
            product=str(product_daemon_root(environ=env_map)),
        )
    live = _live_lock_pid(target)
    if live is not None:
        report: dict[str, object] = {
            "verb": "host.start",
            "state": "already-running",
            "pid": live,
            "root": str(target),
            "spawned": False,
            "orchestrates_missions": START_ORCHESTRATES_MISSIONS,
            "grants": START_GRANTS,
            "starts_qmn": START_STARTS_QMN,
            "browser_spawns_python": BROWSER_SPAWNS_PYTHON,
        }
        return Ok(cast("Mapping[str, object]", redact_host_surface(report)))
    _drop_stale_lock(target)
    child_env = dict(os.environ if env_map is None else env_map)
    child_env["QMA_DAEMON_ROOT"] = str(target)
    argv = _spawn_argv(python if isinstance(python, str) else None)
    try:
        if spawn is None:
            spawned: object = _default_spawn(argv, env=child_env, root=target)
        elif callable(spawn):
            spawned = spawn(argv, env=child_env, root=target)
        else:
            return invalid("spawn", "spawn must be callable")
    except OSError as exc:
        return storage("spawn", f"could not spawn python -m qma.daemon: {exc}")
    pid: int | None
    if isinstance(spawned, int):
        pid = spawned
    elif spawned is None:
        pid = None
    else:
        maybe = getattr(spawned, "pid", None)
        pid = maybe if isinstance(maybe, int) else None
    parsed_attempts = _wait_attempts(wait_attempts)
    if not isinstance(parsed_attempts, Ok):
        return parsed_attempts
    attempts = parsed_attempts.value
    for _ in range(max(1, attempts)):
        if _ready(target):
            ready_pid = _live_lock_pid(target)
            started: dict[str, object] = {
                "verb": "host.start",
                "state": "started",
                "pid": ready_pid if ready_pid is not None else pid,
                "root": str(target),
                "spawned": True,
                "argv": list(argv[-2:]),
                "orchestrates_missions": START_ORCHESTRATES_MISSIONS,
                "grants": START_GRANTS,
                "starts_qmn": START_STARTS_QMN,
                "browser_spawns_python": BROWSER_SPAWNS_PYTHON,
            }
            return Ok(cast("Mapping[str, object]", redact_host_surface(started)))
        if attempts > 1:
            _pause(sleeper)
    return unavailable(
        "daemon",
        "spawned python -m qma.daemon did not acquire .daemon_writer",
        root=str(target),
        pid=pid,
    )


def invoke_host_status(
    *,
    root: object = None,
    environ: object = None,
    transport: object = None,
) -> Result[Mapping[str, object]]:
    """Report lock, pid, bind, operator-established, TTL, and record ids."""
    env_map: Mapping[str, str] | None
    if environ is None:
        env_map = None
    elif isinstance(environ, Mapping):
        env_map = cast("Mapping[str, str]", environ)
    else:
        return invalid("environ", "environ is a string mapping")
    target = _as_root(root, env_map)
    token = _read_token(target)
    if not isinstance(token, Ok):
        return token
    if callable(transport):
        called = transport("status", token.value, root=target)
        if isinstance(called, TypedRefusal):
            return called
        if not isinstance(called, Mapping):
            return invalid("status", "host-control transport must return a mapping")
        payload = dict(cast("Mapping[str, object]", called))
    else:
        remote = _host_control_call(target, "status")
        if not isinstance(remote, Ok):
            return remote
        payload = dict(remote.value)
    if payload.get("ok") is False:
        refusal = payload.get("refusal")
        if isinstance(refusal, Mapping):
            body = cast("Mapping[str, object]", refusal)
            category = body.get("category")
            context = body.get("context")
            if isinstance(category, str) and isinstance(context, Mapping):
                try:
                    parsed = RefusalCategory(category)
                except ValueError:
                    parsed = RefusalCategory.POLICY_REJECTION
                return TypedRefusal(
                    category=parsed,
                    retryability=Retryability.NO,
                    context=dict(cast("Mapping[str, object]", context)),
                )
        return policy("host_control", "host-control status refused")
    status = payload.get("status")
    if not isinstance(status, Mapping):
        status = payload
    fields = dict(cast("Mapping[str, object]", status))
    report: dict[str, object] = {
        "verb": "host.status",
        "lock": fields.get("lock"),
        "pid": fields.get("pid"),
        "bind": fields.get("bind"),
        "operator_established": fields.get("operator_established", False),
        "ttl": fields.get("ttl", "unset"),
        "pending_record_ids": _id_list(fields.get("pending_record_ids")),
        "bound_record_ids": _id_list(fields.get("bound_record_ids")),
    }
    if "pairing_record_id" in fields:
        report["pairing_record_id"] = fields.get("pairing_record_id")
    return Ok(cast("Mapping[str, object]", redact_host_surface(report)))


def invoke_host_stop(
    *,
    root: object = None,
    environ: object = None,
    transport: object = None,
    wait_attempts: object = None,
    sleeper: object = None,
) -> Result[Mapping[str, object]]:
    """Stop the local daemon and release ``.daemon_writer``. Does not cancel QMN."""
    env_map: Mapping[str, str] | None
    if environ is None:
        env_map = None
    elif isinstance(environ, Mapping):
        env_map = cast("Mapping[str, str]", environ)
    else:
        return invalid("environ", "environ is a string mapping")
    target = _as_root(root, env_map)
    token = _read_token(target)
    if not isinstance(token, Ok):
        return token
    live = _live_lock_pid(target)
    if callable(transport):
        called = transport("stop", token.value, root=target)
        if isinstance(called, TypedRefusal):
            return called
        if not isinstance(called, Mapping):
            return invalid("stop", "host-control transport must return a mapping")
        payload = dict(cast("Mapping[str, object]", called))
    else:
        remote = _host_control_call(target, "stop")
        if not isinstance(remote, Ok):
            return remote
        payload = dict(remote.value)
    refused = _payload_refusal(payload, verb="stop")
    if not isinstance(refused, Ok):
        return refused
    parsed_attempts = _wait_attempts(wait_attempts)
    if not isinstance(parsed_attempts, Ok):
        return parsed_attempts
    attempts = parsed_attempts.value
    for _ in range(max(1, attempts)):
        if _live_lock_pid(target) is None:
            stopped: dict[str, object] = {
                "verb": "host.stop",
                "state": "stopped",
                "pid": live,
                "lock": "free",
                "root": str(target),
                "cancels_qmn": STOP_CANCELS_QMN,
                "stops_remote": STOP_STOPS_REMOTE,
            }
            return Ok(cast("Mapping[str, object]", redact_host_surface(stopped)))
        if attempts > 1:
            _pause(sleeper)
    return unavailable(
        "daemon_writer",
        "local stop did not release .daemon_writer",
        root=str(target),
    )


def invoke_host_configure_pairing_ttl(
    duration: object,
    *,
    root: object = None,
    environ: object = None,
    transport: object = None,
) -> Result[Mapping[str, object]]:
    """Write ``registry:pairing.session_ttl`` over host-control. Mint no duration."""
    if not isinstance(duration, str) or duration.strip() == "":
        return invalid(
            "duration",
            "qmb host configure pairing-ttl requires an operator-supplied "
            "duration; this increment mints no duration (GAP-0109)",
            given=repr(duration),
        )
    env_map = _environ_map(environ)
    if not isinstance(env_map, Ok):
        return env_map
    target = _as_root(root, env_map.value)
    token = _read_token(target)
    if not isinstance(token, Ok):
        return token
    fields: dict[str, object] = {
        "target": "pairing-ttl",
        "duration": duration.strip(),
    }
    if callable(transport):
        called = transport("configure", token.value, root=target, extra=fields)
        if isinstance(called, TypedRefusal):
            return called
        if not isinstance(called, Mapping):
            return invalid("configure", "host-control transport must return a mapping")
        payload = dict(cast("Mapping[str, object]", called))
    else:
        remote = _host_control_call(target, "configure", fields=fields)
        if not isinstance(remote, Ok):
            return remote
        payload = dict(remote.value)
    refused = _payload_refusal(payload, verb="configure")
    if not isinstance(refused, Ok):
        return refused
    configured = payload.get("configured")
    fields_out: dict[str, object]
    if isinstance(configured, Mapping):
        fields_out = dict(cast("Mapping[str, object]", configured))
    else:
        fields_out = {}
    report: dict[str, object] = {
        "verb": "host.configure.pairing-ttl",
        "registry_key": fields_out.get("registry_key", PAIRING_SESSION_TTL_REGISTRY_KEY),
        "ttl": fields_out.get("ttl", "set"),
        "writer": fields_out.get("writer", "host.configure.pairing-ttl"),
    }
    return Ok(cast("Mapping[str, object]", redact_host_surface(report)))


def invoke_host_rotate_control(
    *,
    root: object = None,
    environ: object = None,
    transport: object = None,
) -> Result[Mapping[str, object]]:
    """Remint host_control while presenting the current token. Does not recover."""
    env_map = _environ_map(environ)
    if not isinstance(env_map, Ok):
        return env_map
    target = _as_root(root, env_map.value)
    token = _read_token(target)
    if not isinstance(token, Ok):
        return token
    if callable(transport):
        called = transport("rotate-control", token.value, root=target)
        if isinstance(called, TypedRefusal):
            return called
        if not isinstance(called, Mapping):
            return invalid("rotate-control", "host-control transport must return a mapping")
        payload = dict(cast("Mapping[str, object]", called))
    else:
        remote = _host_control_call(target, "rotate-control")
        if not isinstance(remote, Ok):
            return remote
        payload = dict(remote.value)
    refused = _payload_refusal(payload, verb="rotate-control")
    if not isinstance(refused, Ok):
        return refused
    rotated = payload.get("rotated")
    fields_out: dict[str, object] = (
        dict(cast("Mapping[str, object]", rotated)) if isinstance(rotated, Mapping) else {}
    )
    report: dict[str, object] = {
        "verb": "host.rotate-control",
        "rotated": fields_out.get("rotated", True),
        "local_operator": fields_out.get("local_operator", "unchanged"),
        "writer": fields_out.get("writer", "host.rotate-control"),
    }
    if "host_control_fp1" in fields_out:
        report["host_control_fp1"] = fields_out.get("host_control_fp1")
    if "previous_host_control_fp1" in fields_out:
        report["previous_host_control_fp1"] = fields_out.get("previous_host_control_fp1")
    return Ok(cast("Mapping[str, object]", redact_host_surface(report)))
