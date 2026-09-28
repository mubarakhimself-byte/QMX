"""Stories 67.1–67.3 — product QMA_DAEMON_ROOT, host start|status|stop|configure|rotate-control."""

from __future__ import annotations

import json
import os
import socket
import stat
import threading
from collections.abc import Mapping
from pathlib import Path

import pytest
from click.testing import CliRunner
from qmb.doors.cli import (
    COMMAND_GROUPS,
    HOST_COMMANDS,
    HOST_CONFIGURE_COMMANDS,
    command_tree,
    invoke_host_configure_pairing_ttl,
    invoke_host_rotate_control,
    invoke_host_start,
    invoke_host_status,
    invoke_host_stop,
    main,
)
from qmb.doors.cli.host import (
    BROWSER_SPAWNS_PYTHON,
    CT40_BIND_PORT,
    DAEMON_LOCK_NAME,
    HOST_CONTROL_BIND_NAME,
    HOST_CONTROL_FILE,
    INSPECT_CWD_RELATIVE_ROOT,
    INSPECT_SHA_COMMAND_GROUPS,
    PAIRING_SESSION_TTL_REGISTRY_KEY,
    QMB_HOST_CONFIGURE_EXISTED_AT_INSPECT_SHA,
    QMB_HOST_EXISTED_AT_INSPECT_SHA,
    QMB_HOST_ROTATE_CONTROL_EXISTED_AT_INSPECT_SHA,
    START_GRANTS,
    START_ORCHESTRATES_MISSIONS,
    START_STARTS_QMN,
    STOP_CANCELS_QMN,
    STOP_STOPS_REMOTE,
    claim_host_configure_existed_at_inspect_sha,
    claim_qmb_host_existed_at_inspect_sha,
    claim_rotate_control_existed_at_inspect_sha,
    claim_types_absent_at_inspect_sha,
    product_daemon_root,
    redact_host_surface,
)
from qmf.core.refusal import RefusalCategory, Result, is_ok, is_refusal

_TOKEN = "fixture-host-control-token"


def _lock_payload(pid: int) -> str:
    return json.dumps(
        {
            "boot_epoch_id": "boot",
            "machine": "test-host",
            "pid": pid,
            "role": "qma-daemon",
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _write_lock(root: Path, pid: int) -> None:
    (root / DAEMON_LOCK_NAME).write_text(_lock_payload(pid), encoding="utf-8")


def _write_token(root: Path, token: str = _TOKEN) -> None:
    (root / HOST_CONTROL_FILE).write_text(token + "\n", encoding="utf-8")


def _write_bind(root: Path, host: str, port: int) -> None:
    (root / HOST_CONTROL_BIND_NAME).write_text(
        json.dumps({"host": host, "port": port}, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )


def _no_sleep(_seconds: float) -> None:
    return None


def _ok_mapping(result: Result[Mapping[str, object]]) -> Mapping[str, object]:
    assert is_ok(result), result
    return result.value


class _HostControlServer(threading.Thread):
    def __init__(self, token: str, *, root: Path) -> None:
        super().__init__(daemon=True)
        self._token = token
        self._root = root
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("127.0.0.1", 0))
        self.port = int(self._sock.getsockname()[1])
        self._sock.listen(8)
        self._sock.settimeout(0.2)
        self._stop = threading.Event()
        self.seen_verbs: list[str] = []

    def run(self) -> None:
        while not self._stop.is_set():
            try:
                conn, _addr = self._sock.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            with conn:
                self._handle(conn)

    def _handle(self, conn: socket.socket) -> None:
        header = conn.recv(4)
        if len(header) < 4:
            return
        size = int.from_bytes(header, "big")
        body = conn.recv(size)
        request = json.loads(body.decode("utf-8"))
        verb = str(request.get("verb"))
        self.seen_verbs.append(verb)
        presented = request.get("host_control")
        if presented != self._token:
            payload = {
                "ok": False,
                "refusal": {
                    "category": RefusalCategory.POLICY_REJECTION.value,
                    "retryability": "no",
                    "context": {
                        "field": "host_control",
                        "reason": "host-control requires the current token",
                    },
                },
            }
        elif verb == "status":
            payload = {
                "ok": True,
                "status": {
                    "lock": "held",
                    "pid": os.getpid(),
                    "bind": "127.0.0.1:8765",
                    "operator_established": False,
                    "ttl": "unset",
                    "pending_record_ids": ["pend:1"],
                    "bound_record_ids": ["pair:1"],
                    "pairing_record_id": "pair:1",
                    "host_control": self._token,
                    "Authorization": "Bearer pairing:secret",
                    "pairing_proof": "raw-proof",
                },
            }
        elif verb == "stop":
            lock = self._root / DAEMON_LOCK_NAME
            if lock.is_file():
                lock.unlink()
            payload = {"ok": True, "stopped": True}
        elif verb == "configure":
            payload = {
                "ok": True,
                "configured": {
                    "registry_key": PAIRING_SESSION_TTL_REGISTRY_KEY,
                    "ttl": "set",
                    "writer": "host.configure.pairing-ttl",
                },
            }
        elif verb == "rotate-control":
            rotated = "rotated-" + self._token
            (self._root / HOST_CONTROL_FILE).write_text(rotated + "\n", encoding="utf-8")
            self._token = rotated
            payload = {
                "ok": True,
                "rotated": {
                    "rotated": True,
                    "local_operator": "unchanged",
                    "writer": "host.rotate-control",
                    "host_control": rotated,
                },
            }
        else:
            payload = {"ok": False, "refusal": {"category": "invalid_input"}}
        raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        conn.sendall(len(raw).to_bytes(4, "big") + raw)

    def close(self) -> None:
        self._stop.set()
        try:
            self._sock.close()
        except OSError:
            return


def test_product_root_is_not_cwd_relative_qma_daemon_data() -> None:
    win = product_daemon_root(
        system="win32",
        environ={"LOCALAPPDATA": r"C:\Users\op\AppData\Local"},
    )
    assert win == Path(r"C:\Users\op\AppData\Local") / "QMX" / "qma-daemon"
    linux = product_daemon_root(system="linux", environ={"HOME": "/home/op"})
    assert linux == Path("/home/op/.local/state/qmx/qma-daemon")
    xdg = product_daemon_root(
        system="linux",
        environ={"HOME": "/home/op", "XDG_STATE_HOME": "/var/state"},
    )
    assert xdg == Path("/var/state/qmx/qma-daemon")
    mac = product_daemon_root(system="darwin", environ={"HOME": "/Users/op"})
    assert mac == Path("/Users/op/Library/Application Support/QMX/qma-daemon")
    product = product_daemon_root()
    assert product.name != INSPECT_CWD_RELATIVE_ROOT
    assert INSPECT_CWD_RELATIVE_ROOT not in product.parts


def test_command_tree_named_adds_host_start_status_stop_configure() -> None:
    assert "host" not in INSPECT_SHA_COMMAND_GROUPS
    assert COMMAND_GROUPS[-1] == "host"
    assert (
        command_tree()["host"]
        == HOST_COMMANDS
        == (
            "start",
            "status",
            "stop",
            "configure",
            "rotate-control",
        )
    )
    assert HOST_CONFIGURE_COMMANDS == ("pairing-ttl",)
    assert "pair" not in HOST_COMMANDS
    assert "recover-control" not in HOST_COMMANDS
    runner = CliRunner()
    helped = runner.invoke(main, ["host", "--help"])
    assert helped.exit_code == 0, helped.output
    assert "start" in helped.output
    assert "status" in helped.output
    assert "stop" in helped.output
    assert "configure" in helped.output
    assert "rotate-control" in helped.output
    assert "pair" not in helped.output
    assert "recover-control" not in helped.output
    missing = runner.invoke(main, ["host", "pair"])
    assert missing.exit_code != 0
    configure_help = runner.invoke(main, ["host", "configure", "--help"])
    assert configure_help.exit_code == 0, configure_help.output
    assert "pairing-ttl" in configure_help.output


def test_start_spawns_when_lock_free(tmp_path: Path) -> None:
    seen: list[tuple[tuple[str, ...], str]] = []

    def spawn(argv: tuple[str, ...], *, env: Mapping[str, str], root: Path) -> int:
        seen.append((argv, env["QMA_DAEMON_ROOT"]))
        assert argv[-2:] == ("-m", "qma.daemon")
        assert env["QMA_DAEMON_ROOT"] == str(tmp_path)
        _write_lock(root, os.getpid())
        _write_token(root)
        _write_bind(root, "127.0.0.1", 19234)
        return os.getpid()

    report = _ok_mapping(
        invoke_host_start(root=tmp_path, spawn=spawn, wait_attempts=1, sleeper=_no_sleep)
    )
    assert report["state"] == "started"
    assert report["spawned"] is True
    assert report["orchestrates_missions"] is START_ORCHESTRATES_MISSIONS is False
    assert report["grants"] is START_GRANTS is False
    assert report["starts_qmn"] is START_STARTS_QMN is False
    assert report["browser_spawns_python"] is BROWSER_SPAWNS_PYTHON is False
    assert seen and seen[0][1] == str(tmp_path)
    assert _TOKEN not in json.dumps(dict(report))


def test_start_already_running_does_not_spawn_or_remint(tmp_path: Path) -> None:
    _write_lock(tmp_path, os.getpid())
    _write_token(tmp_path, _TOKEN)
    before = (tmp_path / HOST_CONTROL_FILE).read_bytes()
    spawned: list[object] = []

    def spawn(*_args: object, **_kwargs: object) -> int:
        spawned.append(1)
        return 0

    report = _ok_mapping(invoke_host_start(root=tmp_path, spawn=spawn, wait_attempts=1))
    assert report["state"] == "already-running"
    assert report["spawned"] is False
    assert spawned == []
    assert (tmp_path / HOST_CONTROL_FILE).read_bytes() == before


def test_status_and_stop_use_host_control_and_redact(tmp_path: Path) -> None:
    server = _HostControlServer(_TOKEN, root=tmp_path)
    server.start()
    try:
        assert server.port != CT40_BIND_PORT
        _write_lock(tmp_path, os.getpid())
        _write_token(tmp_path)
        _write_bind(tmp_path, "127.0.0.1", server.port)
        status = _ok_mapping(invoke_host_status(root=tmp_path))
        rendered = json.dumps(dict(status))
        assert status["verb"] == "host.status"
        assert status["lock"] == "held"
        assert status["bind"] == "127.0.0.1:8765"
        assert status["ttl"] == "unset"
        assert status["pairing_record_id"] == "pair:1"
        assert _TOKEN not in rendered
        assert "raw-proof" not in rendered
        assert "Bearer pairing:secret" not in rendered
        assert "[redacted]" in json.dumps(
            redact_host_surface({"host_control": _TOKEN, "Authorization": "x"})
        )
        stopped = _ok_mapping(invoke_host_stop(root=tmp_path, wait_attempts=1))
        assert stopped["state"] == "stopped"
        assert stopped["lock"] == "free"
        assert stopped["cancels_qmn"] is STOP_CANCELS_QMN is False
        assert stopped["stops_remote"] is STOP_STOPS_REMOTE is False
        assert not (tmp_path / DAEMON_LOCK_NAME).exists()
        assert "status" in server.seen_verbs
        assert "stop" in server.seen_verbs
    finally:
        server.close()
        server.join(timeout=2)


def test_status_without_token_refuses(tmp_path: Path) -> None:
    refused = invoke_host_status(root=tmp_path)
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["field"] == "host_control"


def test_click_host_start_status_stop(tmp_path: Path) -> None:
    def spawn(argv: tuple[str, ...], *, env: Mapping[str, str], root: Path) -> int:
        _ = argv
        assert env["QMA_DAEMON_ROOT"] == str(tmp_path)
        _write_lock(root, os.getpid())
        _write_token(root)
        _write_bind(root, "127.0.0.1", 19235)
        return os.getpid()

    runner = CliRunner()
    started = runner.invoke(
        main,
        ["host", "start"],
        obj={"root": tmp_path, "spawn": spawn, "wait_attempts": 1, "sleeper": _no_sleep},
    )
    assert started.exit_code == 0, started.output
    payload = json.loads(started.stdout)
    assert payload["state"] == "started"
    assert _TOKEN not in started.output

    def transport(verb: str, token: str, *, root: Path) -> Mapping[str, object]:
        assert token == _TOKEN
        if verb == "status":
            return {
                "ok": True,
                "status": {
                    "lock": "held",
                    "pid": 1,
                    "bind": "127.0.0.1:8765",
                    "operator_established": False,
                    "ttl": "unset",
                    "pending_record_ids": [],
                    "bound_record_ids": [],
                },
            }
        (root / DAEMON_LOCK_NAME).unlink(missing_ok=True)
        return {"ok": True, "stopped": True}

    status = runner.invoke(
        main,
        ["host", "status"],
        obj={"root": tmp_path, "transport": transport},
    )
    assert status.exit_code == 0, status.output
    assert "held" in status.output
    stopped = runner.invoke(
        main,
        ["host", "stop"],
        obj={"root": tmp_path, "transport": transport, "wait_attempts": 1},
    )
    assert stopped.exit_code == 0, stopped.output
    assert json.loads(stopped.stdout)["state"] == "stopped"


def test_honesty_qmb_host_absent_at_inspect_and_types_present() -> None:
    assert QMB_HOST_EXISTED_AT_INSPECT_SHA is False
    assert QMB_HOST_CONFIGURE_EXISTED_AT_INSPECT_SHA is False
    assert QMB_HOST_ROTATE_CONTROL_EXISTED_AT_INSPECT_SHA is False
    claimed = claim_qmb_host_existed_at_inspect_sha(True)
    assert is_refusal(claimed)
    assert is_ok(claim_qmb_host_existed_at_inspect_sha(False))
    configure_claimed = claim_host_configure_existed_at_inspect_sha(True)
    assert is_refusal(configure_claimed)
    assert is_ok(claim_host_configure_existed_at_inspect_sha(False))
    rotate_claimed = claim_rotate_control_existed_at_inspect_sha(True)
    assert is_refusal(rotate_claimed)
    assert is_ok(claim_rotate_control_existed_at_inspect_sha(False))
    absent = claim_types_absent_at_inspect_sha(True)
    assert is_refusal(absent)
    assert is_ok(claim_types_absent_at_inspect_sha(False))


def test_cli_host_module_does_not_reuse_hosted_bot_or_write_sqlite() -> None:
    source = Path(__file__).resolve().parents[1] / "src" / "qmb" / "doors" / "cli" / "host.py"
    text = source.read_text(encoding="utf-8")
    assert "from qmb.host" not in text
    assert "import qmb.host" not in text
    assert "sqlite3" not in text
    assert "import qmn" not in text
    assert "from qmn" not in text
    assert "/pair/" not in text
    assert "POST /host/" not in text
    assert "PT15M" not in text


def test_start_ready_without_token_does_not_write_host_control(tmp_path: Path) -> None:
    def spawn(argv: tuple[str, ...], *, env: Mapping[str, str], root: Path) -> int:
        _ = argv, env
        _write_lock(root, os.getpid())
        _write_bind(root, "127.0.0.1", 19236)
        return os.getpid()

    report = _ok_mapping(
        invoke_host_start(root=tmp_path, spawn=spawn, wait_attempts=1, sleeper=_no_sleep)
    )
    assert report["state"] == "started"
    assert not (tmp_path / HOST_CONTROL_FILE).exists()


def test_configure_pairing_ttl_over_host_control(tmp_path: Path) -> None:
    server = _HostControlServer(_TOKEN, root=tmp_path)
    server.start()
    try:
        _write_token(tmp_path)
        _write_bind(tmp_path, "127.0.0.1", server.port)
        fixture_duration = "PT15M"
        report = _ok_mapping(invoke_host_configure_pairing_ttl(fixture_duration, root=tmp_path))
        assert report["verb"] == "host.configure.pairing-ttl"
        assert report["registry_key"] == PAIRING_SESSION_TTL_REGISTRY_KEY
        assert report["ttl"] == "set"
        assert "configure" in server.seen_verbs
        missing = invoke_host_configure_pairing_ttl("", root=tmp_path)
        assert is_refusal(missing)
        assert missing.context["field"] == "duration"
    finally:
        server.close()
        server.join(timeout=2)


def test_click_host_configure_pairing_ttl(tmp_path: Path) -> None:
    _write_token(tmp_path)

    def transport(
        verb: str,
        token: str,
        *,
        root: Path,
        extra: Mapping[str, object] | None = None,
    ) -> Mapping[str, object]:
        _ = root
        assert token == _TOKEN
        assert verb == "configure"
        assert extra is not None
        assert extra["target"] == "pairing-ttl"
        assert extra["duration"] == "PT15M"
        return {
            "ok": True,
            "configured": {
                "registry_key": PAIRING_SESSION_TTL_REGISTRY_KEY,
                "ttl": "set",
                "writer": "host.configure.pairing-ttl",
            },
        }

    runner = CliRunner()
    configured = runner.invoke(
        main,
        ["host", "configure", "pairing-ttl", "PT15M"],
        obj={"root": tmp_path, "transport": transport},
    )
    assert configured.exit_code == 0, configured.output
    payload = json.loads(configured.stdout)
    assert payload["registry_key"] == PAIRING_SESSION_TTL_REGISTRY_KEY
    assert payload["ttl"] == "set"


def test_rotate_control_while_held_and_old_token_refuses(tmp_path: Path) -> None:
    server = _HostControlServer(_TOKEN, root=tmp_path)
    server.start()
    try:
        _write_token(tmp_path)
        _write_bind(tmp_path, "127.0.0.1", server.port)
        report = _ok_mapping(invoke_host_rotate_control(root=tmp_path))
        assert report["verb"] == "host.rotate-control"
        assert report["rotated"] is True
        assert report["local_operator"] == "unchanged"
        dumped = json.dumps(dict(report))
        assert _TOKEN not in dumped
        new_token = (tmp_path / HOST_CONTROL_FILE).read_text(encoding="utf-8").strip()
        assert new_token != _TOKEN
        assert new_token not in dumped
        assert "rotate-control" in server.seen_verbs
        _write_token(tmp_path, _TOKEN)
        stale = invoke_host_status(root=tmp_path)
        assert is_refusal(stale)
        assert stale.context["field"] == "host_control"
        _write_token(tmp_path, new_token)
        status = _ok_mapping(invoke_host_status(root=tmp_path))
        status_dump = json.dumps(dict(status))
        assert new_token not in status_dump
        assert _TOKEN not in status_dump
    finally:
        server.close()
        server.join(timeout=2)


def test_click_host_rotate_control(tmp_path: Path) -> None:
    _write_token(tmp_path)

    def transport(verb: str, token: str, *, root: Path) -> Mapping[str, object]:
        _ = root
        assert token == _TOKEN
        assert verb == "rotate-control"
        return {
            "ok": True,
            "rotated": {
                "rotated": True,
                "local_operator": "unchanged",
                "writer": "host.rotate-control",
                "host_control": "should-redact",
            },
        }

    runner = CliRunner()
    rotated = runner.invoke(
        main,
        ["host", "rotate-control"],
        obj={"root": tmp_path, "transport": transport},
    )
    assert rotated.exit_code == 0, rotated.output
    payload = json.loads(rotated.stdout)
    assert payload["rotated"] is True
    assert payload["local_operator"] == "unchanged"
    assert "should-redact" not in rotated.output
    assert _TOKEN not in rotated.output


@pytest.mark.parametrize("verb", ["status", "stop", "configure", "rotate-control"])
def test_running_daemon_verbs_refuse_without_token(tmp_path: Path, verb: str) -> None:
    _write_bind(tmp_path, "127.0.0.1", 19240)
    if verb == "status":
        refused = invoke_host_status(root=tmp_path)
    elif verb == "stop":
        refused = invoke_host_stop(root=tmp_path, wait_attempts=1)
    elif verb == "configure":
        refused = invoke_host_configure_pairing_ttl("PT15M", root=tmp_path)
    else:
        refused = invoke_host_rotate_control(root=tmp_path)
    assert is_refusal(refused)
    assert refused.context["field"] == "host_control"


@pytest.mark.parametrize("verb", ["status", "stop", "configure", "rotate-control"])
def test_running_daemon_verbs_refuse_stale_token(tmp_path: Path, verb: str) -> None:
    server = _HostControlServer(_TOKEN, root=tmp_path)
    server.start()
    try:
        _write_token(tmp_path, "stale-token")
        _write_bind(tmp_path, "127.0.0.1", server.port)
        _write_lock(tmp_path, os.getpid())
        if verb == "status":
            refused = invoke_host_status(root=tmp_path)
        elif verb == "stop":
            refused = invoke_host_stop(root=tmp_path, wait_attempts=1)
        elif verb == "configure":
            refused = invoke_host_configure_pairing_ttl("PT15M", root=tmp_path)
        else:
            refused = invoke_host_rotate_control(root=tmp_path)
        assert is_refusal(refused)
        assert refused.context["field"] == "host_control"
        assert (tmp_path / DAEMON_LOCK_NAME).is_file()
    finally:
        server.close()
        server.join(timeout=2)


@pytest.mark.skipif(os.name == "nt", reason="posix chmod 000 is the unreadable-file stand-in")
@pytest.mark.parametrize("verb", ["status", "stop", "configure", "rotate-control"])
def test_running_daemon_verbs_refuse_unreadable_token(tmp_path: Path, verb: str) -> None:
    path = tmp_path / HOST_CONTROL_FILE
    path.write_text(_TOKEN + "\n", encoding="utf-8")
    os.chmod(path, 0)
    try:
        if verb == "status":
            refused = invoke_host_status(root=tmp_path)
        elif verb == "stop":
            refused = invoke_host_stop(root=tmp_path, wait_attempts=1)
        elif verb == "configure":
            refused = invoke_host_configure_pairing_ttl("PT15M", root=tmp_path)
        else:
            refused = invoke_host_rotate_control(root=tmp_path)
        assert is_refusal(refused)
        assert refused.context["field"] == "host_control"
    finally:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
