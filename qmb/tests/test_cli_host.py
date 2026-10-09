"""Stories 67.1–67.4 — product QMA_DAEMON_ROOT and qmb host verbs."""

from __future__ import annotations

import json
import os
import socket
import stat
import subprocess
import sys
import threading
from collections.abc import Iterator, Mapping
from pathlib import Path

import pytest
from qmb.doors.cli import host as host_module
from qmb.doors.cli.host import (
    BROWSER_SPAWNS_PYTHON,
    CT40_BIND_PORT,
    DAEMON_LOCK_NAME,
    DAEMON_RECOVER_ENV,
    DAEMON_RECOVER_FLAG,
    HOST_CONTROL_BIND_NAME,
    HOST_CONTROL_FILE,
    INSPECT_CWD_RELATIVE_ROOT,
    LOCAL_OPERATOR_BOOTSTRAP_IS_THIS_STORY,
    PAIRING_SESSION_TTL_REGISTRY_KEY,
    QMB_HOST_CONFIGURE_EXISTED_AT_INSPECT_SHA,
    QMB_HOST_EXISTED_AT_INSPECT_SHA,
    QMB_HOST_PAIR_EXISTED_AT_INSPECT_SHA,
    QMB_HOST_PAIR_REVOKE_EXISTED_AT_INSPECT_SHA,
    QMB_HOST_RECOVER_CONTROL_EXISTED_AT_INSPECT_SHA,
    QMB_HOST_ROTATE_CONTROL_EXISTED_AT_INSPECT_SHA,
    REUSES_QMB_HOST_PACKAGE,
    START_GRANTS,
    START_ORCHESTRATES_MISSIONS,
    START_STARTS_QMN,
    STOP_CANCELS_QMN,
    STOP_STOPS_REMOTE,
    claim_host_configure_existed_at_inspect_sha,
    claim_local_operator_bootstrap_is_this_story,
    claim_qmb_host_existed_at_inspect_sha,
    claim_qmb_host_pair_existed_at_inspect_sha,
    claim_qmb_host_pair_revoke_existed_at_inspect_sha,
    claim_recover_control_existed_at_inspect_sha,
    claim_rotate_control_existed_at_inspect_sha,
    claim_types_absent_at_inspect_sha,
    invoke_host_configure_artifact_stage_max_bytes,
    invoke_host_configure_pairing_ttl,
    invoke_host_pair,
    invoke_host_pair_revoke,
    invoke_host_recover_control,
    invoke_host_rotate_control,
    invoke_host_start,
    invoke_host_status,
    invoke_host_stop,
    product_daemon_root,
    redact_host_surface,
)
from qmb.orchestrator.paths import write_bytes_exclusive_no_follow
from qmf.core.refusal import RefusalCategory, Result, is_ok, is_refusal

_TOKEN = "fixture-host-control-token"
# Allow the fixture's listener thread to run on a busy host (five seconds total).
HOST_START_WAIT_ATTEMPTS = 100


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
    written = write_bytes_exclusive_no_follow(
        root / DAEMON_LOCK_NAME,
        _lock_payload(pid).encode("utf-8"),
        contain_within=root,
    )
    assert is_ok(written), written


def _write_token(root: Path, token: str = _TOKEN) -> None:
    path = root / HOST_CONTROL_FILE
    if path.exists():
        path.unlink()
    written = write_bytes_exclusive_no_follow(
        path,
        (token + "\n").encode("utf-8"),
        contain_within=root,
    )
    assert is_ok(written), written


def _write_bind(root: Path, host: str, port: int) -> None:
    written = write_bytes_exclusive_no_follow(
        root / HOST_CONTROL_BIND_NAME,
        json.dumps({"host": host, "port": port}, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        ),
        contain_within=root,
    )
    assert is_ok(written), written


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
        elif verb == "pair":
            payload = {
                "ok": True,
                "paired": {
                    "pairing_record_id": "pr_fixture",
                    "confirmed": True,
                    "pairing_proof": "must-not-leak",
                    "code": request.get("code"),
                },
            }
        elif verb == "pair-revoke":
            payload = {
                "ok": True,
                "revoked": {
                    "scope": "origin" if request.get("origin") else "session",
                    "origin": request.get("origin"),
                    "pairing_record_id": request.get("pairing_record_id"),
                    "journal_seq": 17,
                    "barrier": "journal_seq",
                    "noop": False,
                    "revoked_record_ids": ["pr_fixture"],
                    "pairing_proof": "must-not-leak",
                },
            }
        elif verb == "rotate-control":
            rotated = "rotated-" + self._token
            _write_token(self._root, rotated)
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


def test_start_spawns_when_lock_free(tmp_path: Path, start_control: _HostControlServer) -> None:
    seen: list[tuple[tuple[str, ...], str]] = []

    def spawn(argv: tuple[str, ...], *, env: Mapping[str, str], root: Path) -> int:
        seen.append((argv, env["QMA_DAEMON_ROOT"]))
        assert argv[-2:] == ("-m", "qma.daemon")
        assert env["QMA_DAEMON_ROOT"] == str(tmp_path)
        _write_lock(root, os.getpid())
        _write_token(root)
        _write_bind(root, "127.0.0.1", start_control.port)
        return os.getpid()

    report = _ok_mapping(
        invoke_host_start(
            root=tmp_path, spawn=spawn, wait_attempts=HOST_START_WAIT_ATTEMPTS, sleeper=_no_sleep
        )
    )
    assert report["state"] == "started"
    assert report["spawned"] is True
    assert report["orchestrates_missions"] is START_ORCHESTRATES_MISSIONS is False
    assert report["grants"] is START_GRANTS is False
    assert report["starts_qmn"] is START_STARTS_QMN is False
    assert report["browser_spawns_python"] is BROWSER_SPAWNS_PYTHON is False
    assert seen and seen[0][1] == str(tmp_path)
    assert _TOKEN not in json.dumps(dict(report))


def test_start_failure_points_to_persistent_daemon_diagnostics(tmp_path: Path) -> None:
    def failed_spawn(_argv: tuple[str, ...], *, env: Mapping[str, str], root: Path) -> int:
        _ = env, root
        return 123456

    refused = invoke_host_start(
        root=tmp_path,
        spawn=failed_spawn,
        wait_attempts=1,
        sleeper=_no_sleep,
    )
    assert is_refusal(refused)
    diagnostic = tmp_path / "logs" / "qma-daemon-startup.log"
    assert str(diagnostic) in str(refused.context["reason"])
    assert diagnostic.is_file()


def test_default_spawn_keeps_child_stderr_in_persistent_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, object] = {}

    class FakeProcess:
        pid = 321

    def fake_popen(argv: tuple[str, ...], **kwargs: object) -> FakeProcess:
        _ = argv
        captured.update(kwargs)
        return FakeProcess()

    monkeypatch.setattr(host_module.subprocess, "Popen", fake_popen)
    # Exercise the private process boundary directly to prove stderr is persisted.
    host_module._default_spawn(  # pyright: ignore[reportPrivateUsage]
        ("python", "-m", "qma.daemon"), env={}, root=tmp_path
    )
    stream = captured.get("stderr")
    assert stream is not None and stream is not host_module.subprocess.DEVNULL
    assert getattr(stream, "name", None) == str(tmp_path / "logs" / "qma-daemon-startup.log")


def test_start_already_running_does_not_spawn_or_remint(
    tmp_path: Path, start_control: _HostControlServer
) -> None:
    _write_lock(tmp_path, os.getpid())
    _write_token(tmp_path, _TOKEN)
    _write_bind(tmp_path, "127.0.0.1", start_control.port)
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
    _write_lock(tmp_path, os.getpid())
    refused = invoke_host_status(root=tmp_path)
    assert is_refusal(refused)
    assert refused.category is RefusalCategory.POLICY_REJECTION
    assert refused.context["field"] == "host_control"


def test_status_and_stop_report_stopped_without_using_stale_host_control(
    tmp_path: Path,
) -> None:
    _write_token(tmp_path)
    status = _ok_mapping(invoke_host_status(root=tmp_path))
    assert status["state"] == "stopped"
    assert status["lock"] == "free"
    assert status["bind"] is None
    assert status["operator_established"] is None
    assert status["operator_established_known"] is False
    stopped = _ok_mapping(invoke_host_stop(root=tmp_path))
    assert stopped["state"] == "stopped"
    assert stopped["lock"] == "free"
    assert (tmp_path / HOST_CONTROL_FILE).is_file()


def test_malformed_lock_does_not_claim_stopped(tmp_path: Path) -> None:
    (tmp_path / DAEMON_LOCK_NAME).write_text("not-json", encoding="utf-8")
    status = invoke_host_status(root=tmp_path)
    assert is_refusal(status)
    assert status.context["field"] == "daemon_lock"
    stopped = invoke_host_stop(root=tmp_path)
    assert is_refusal(stopped)
    assert stopped.context["field"] == "daemon_lock"


def test_status_does_not_hide_unreachable_socket_for_live_writer(tmp_path: Path) -> None:
    _write_lock(tmp_path, os.getpid())
    _write_token(tmp_path)
    _write_bind(tmp_path, "127.0.0.1", 1)
    refused = invoke_host_status(root=tmp_path)
    assert is_refusal(refused)
    assert "host-control call failed" in str(refused.context.get("reason", ""))


def test_honesty_qmb_host_absent_at_inspect_and_types_present() -> None:
    assert QMB_HOST_EXISTED_AT_INSPECT_SHA is False
    assert QMB_HOST_CONFIGURE_EXISTED_AT_INSPECT_SHA is False
    assert QMB_HOST_ROTATE_CONTROL_EXISTED_AT_INSPECT_SHA is False
    assert QMB_HOST_RECOVER_CONTROL_EXISTED_AT_INSPECT_SHA is False
    assert QMB_HOST_PAIR_EXISTED_AT_INSPECT_SHA is False
    assert QMB_HOST_PAIR_REVOKE_EXISTED_AT_INSPECT_SHA is False
    assert LOCAL_OPERATOR_BOOTSTRAP_IS_THIS_STORY is False
    assert REUSES_QMB_HOST_PACKAGE is False
    claimed = claim_qmb_host_existed_at_inspect_sha(True)
    assert is_refusal(claimed)
    assert is_ok(claim_qmb_host_existed_at_inspect_sha(False))
    configure_claimed = claim_host_configure_existed_at_inspect_sha(True)
    assert is_refusal(configure_claimed)
    assert is_ok(claim_host_configure_existed_at_inspect_sha(False))
    rotate_claimed = claim_rotate_control_existed_at_inspect_sha(True)
    assert is_refusal(rotate_claimed)
    assert is_ok(claim_rotate_control_existed_at_inspect_sha(False))
    recover_claimed = claim_recover_control_existed_at_inspect_sha(True)
    assert is_refusal(recover_claimed)
    assert is_ok(claim_recover_control_existed_at_inspect_sha(False))
    pair_claimed = claim_qmb_host_pair_existed_at_inspect_sha(True)
    assert is_refusal(pair_claimed)
    assert is_ok(claim_qmb_host_pair_existed_at_inspect_sha(False))
    revoke_claimed = claim_qmb_host_pair_revoke_existed_at_inspect_sha(True)
    assert is_refusal(revoke_claimed)
    assert is_ok(claim_qmb_host_pair_revoke_existed_at_inspect_sha(False))
    assert is_refusal(claim_local_operator_bootstrap_is_this_story(True))
    assert is_ok(claim_local_operator_bootstrap_is_this_story(False))
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


def test_start_without_token_refuses_and_does_not_write_host_control(tmp_path: Path) -> None:
    def spawn(argv: tuple[str, ...], *, env: Mapping[str, str], root: Path) -> int:
        _ = argv, env
        _write_lock(root, os.getpid())
        _write_bind(root, "127.0.0.1", 19236)
        return os.getpid()

    report = invoke_host_start(root=tmp_path, spawn=spawn, wait_attempts=1, sleeper=_no_sleep)
    assert is_refusal(report)
    assert not (tmp_path / HOST_CONTROL_FILE).exists()


def test_configure_pairing_ttl_over_host_control(tmp_path: Path) -> None:
    server = _HostControlServer(_TOKEN, root=tmp_path)
    server.start()
    try:
        _write_lock(tmp_path, os.getpid())
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


def test_host_pair_confirms_without_issuing_proof(tmp_path: Path) -> None:
    server = _HostControlServer(_TOKEN, root=tmp_path)
    server.start()
    try:
        _write_token(tmp_path)
        _write_bind(tmp_path, "127.0.0.1", server.port)
        report = _ok_mapping(invoke_host_pair("pending-code", root=tmp_path))
        assert report["verb"] == "host.pair"
        assert report["confirmed"] is True
        assert report["pairing_record_id"] == "pr_fixture"
        assert "pairing_proof" not in report
        assert "pair" in server.seen_verbs
        missing = invoke_host_pair("", root=tmp_path)
        assert is_refusal(missing)
        assert missing.context["field"] == "code"
        forged = invoke_host_pair("cred://operator/login", root=tmp_path)
        assert is_refusal(forged)
        assert forged.context["field"] == "code"
    finally:
        server.close()
        server.join(timeout=2)


def test_host_pair_revoke_origin_and_session_over_host_control(tmp_path: Path) -> None:
    server = _HostControlServer(_TOKEN, root=tmp_path)
    server.start()
    try:
        _write_token(tmp_path)
        _write_bind(tmp_path, "127.0.0.1", server.port)
        origin = "http://127.0.0.1:5173"
        report = _ok_mapping(invoke_host_pair_revoke(origin=origin, root=tmp_path))
        assert report["verb"] == "host.pair.revoke"
        assert report["scope"] == "origin"
        assert report["origin"] == origin
        assert report["journal_seq"] == 17
        assert report["barrier"] == "journal_seq"
        assert report["noop"] is False
        assert "pairing_proof" not in report
        assert "pair-revoke" in server.seen_verbs
        session_report = _ok_mapping(invoke_host_pair_revoke(session="pr_old", root=tmp_path))
        assert session_report["scope"] == "session"
        assert session_report["pairing_record_id"] == "pr_old"
        both = invoke_host_pair_revoke(origin=origin, session="pr_old", root=tmp_path)
        assert is_refusal(both)
        assert both.context["field"] == "revoke"
        missing = invoke_host_pair_revoke(root=tmp_path)
        assert is_refusal(missing)
        assert missing.context["field"] == "revoke"
    finally:
        server.close()
        server.join(timeout=2)


def test_host_pair_revoke_requires_host_control(tmp_path: Path) -> None:
    refused = invoke_host_pair_revoke(origin="http://127.0.0.1:5173", root=tmp_path)
    assert is_refusal(refused)
    assert refused.context["field"] == "host_control"


def test_rotate_control_while_held_and_old_token_refuses(tmp_path: Path) -> None:
    server = _HostControlServer(_TOKEN, root=tmp_path)
    server.start()
    try:
        _write_lock(tmp_path, os.getpid())
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


@pytest.mark.parametrize("verb", ["status", "stop", "configure", "rotate-control"])
def test_running_daemon_verbs_refuse_without_token(tmp_path: Path, verb: str) -> None:
    _write_lock(tmp_path, os.getpid())
    _write_bind(tmp_path, "127.0.0.1", 19240)
    if verb == "status":
        refused = invoke_host_status(root=tmp_path)
    elif verb == "stop":
        refused = invoke_host_stop(root=tmp_path, wait_attempts=1, owns_root=False)
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


@pytest.mark.skipif(
    os.name == "nt" or getattr(os, "geteuid", lambda: 1)() == 0,
    reason="chmod 000 is not unreadable to Windows or root",
)
@pytest.mark.parametrize("verb", ["status", "stop", "configure", "rotate-control"])
def test_running_daemon_verbs_refuse_unreadable_token(tmp_path: Path, verb: str) -> None:
    _write_lock(tmp_path, os.getpid())
    path = tmp_path / HOST_CONTROL_FILE
    _write_token(tmp_path)
    os.chmod(path, 0)
    try:
        if verb == "status":
            refused = invoke_host_status(root=tmp_path)
        elif verb == "stop":
            refused = invoke_host_stop(root=tmp_path, wait_attempts=1, owns_root=False)
        elif verb == "configure":
            refused = invoke_host_configure_pairing_ttl("PT15M", root=tmp_path)
        else:
            refused = invoke_host_rotate_control(root=tmp_path)
        assert is_refusal(refused)
        assert refused.context["field"] == "host_control"
    finally:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def _recover_spawn(argv: tuple[str, ...], *, env: Mapping[str, str], root: Path) -> int:
    assert DAEMON_RECOVER_FLAG in argv
    assert env[DAEMON_RECOVER_ENV] == "1"
    assert env["QMA_DAEMON_ROOT"] == str(root)
    _write_token(root, "recovered-" + _TOKEN)
    (root / DAEMON_LOCK_NAME).unlink(missing_ok=True)
    return os.getpid()


def test_recover_control_c1_positive_then_start_is_legal(
    tmp_path: Path, start_control: _HostControlServer
) -> None:
    journal = tmp_path / "journal.ndjson"
    journal_written = write_bytes_exclusive_no_follow(
        journal,
        b'{"event":"local_operator.established"}\n',
        contain_within=tmp_path,
    )
    assert is_ok(journal_written), journal_written
    sqlite = tmp_path / "daemon.sqlite"
    sqlite_written = write_bytes_exclusive_no_follow(
        sqlite,
        b"sqlite-fixture",
        contain_within=tmp_path,
    )
    assert is_ok(sqlite_written), sqlite_written
    report = _ok_mapping(
        invoke_host_recover_control(
            root=tmp_path,
            spawn=_recover_spawn,
            wait_attempts=1,
            sleeper=_no_sleep,
            owns_root=True,
        )
    )
    assert report["verb"] == "host.recover-control"
    assert report["recovered"] is True
    assert report["local_operator"] == "unchanged"
    assert report["bound_8765"] is False
    assert report["lock"] == "free"
    dumped = json.dumps(dict(report))
    assert "recovered-" + _TOKEN not in dumped
    assert (tmp_path / HOST_CONTROL_FILE).is_file()
    assert journal.read_text(encoding="utf-8") == '{"event":"local_operator.established"}\n'
    assert sqlite.read_bytes() == b"sqlite-fixture"

    start_control._token = "recovered-" + _TOKEN  # pyright: ignore[reportPrivateUsage] - test server token

    def start_spawn(argv: tuple[str, ...], *, env: Mapping[str, str], root: Path) -> int:
        assert DAEMON_RECOVER_FLAG not in argv
        assert env["QMA_DAEMON_ROOT"] == str(root)
        _write_lock(root, os.getpid())
        _write_bind(root, "127.0.0.1", start_control.port)
        return os.getpid()

    started = _ok_mapping(
        invoke_host_start(root=tmp_path, spawn=start_spawn, wait_attempts=1, sleeper=_no_sleep)
    )
    assert started["state"] == "started"


def test_recover_control_negative_a_other_os_user(tmp_path: Path) -> None:
    journal = tmp_path / "journal.ndjson"
    journal_written = write_bytes_exclusive_no_follow(
        journal,
        b"prior-journal\n",
        contain_within=tmp_path,
    )
    assert is_ok(journal_written), journal_written
    spawned: list[object] = []

    def spawn(*_args: object, **_kwargs: object) -> int:
        spawned.append(1)
        return 0

    refused = invoke_host_recover_control(
        root=tmp_path,
        spawn=spawn,
        wait_attempts=1,
        owns_root=False,
    )
    assert is_refusal(refused)
    assert refused.context["field"] == "QMA_DAEMON_ROOT"
    assert spawned == []
    assert not (tmp_path / HOST_CONTROL_FILE).exists()
    assert journal.read_text(encoding="utf-8") == "prior-journal\n"


def test_recover_control_negative_b_file_still_readable(tmp_path: Path) -> None:
    _write_token(tmp_path)
    spawned: list[object] = []

    def spawn(*_args: object, **_kwargs: object) -> int:
        spawned.append(1)
        return 0

    refused = invoke_host_recover_control(
        root=tmp_path,
        spawn=spawn,
        wait_attempts=1,
        owns_root=True,
    )
    assert is_refusal(refused)
    assert refused.context["field"] == "recover-control"
    assert "rotate-control" in str(refused.context.get("reason", ""))
    assert spawned == []
    assert (tmp_path / HOST_CONTROL_FILE).read_text(encoding="utf-8").strip() == _TOKEN


def test_recover_control_negative_c_live_then_owner_stop(tmp_path: Path) -> None:
    _write_lock(tmp_path, os.getpid())
    spawned: list[object] = []

    def spawn(*_args: object, **_kwargs: object) -> int:
        spawned.append(1)
        return 0

    refused = invoke_host_recover_control(
        root=tmp_path,
        spawn=spawn,
        wait_attempts=1,
        owns_root=True,
    )
    assert is_refusal(refused)
    assert refused.context["field"] == "recover-control"
    assert "live" in str(refused.context.get("reason", ""))
    assert spawned == []
    assert (tmp_path / DAEMON_LOCK_NAME).is_file()

    def signal_stop(pid: int) -> None:
        assert pid == os.getpid()
        (tmp_path / DAEMON_LOCK_NAME).unlink()

    stopped = _ok_mapping(
        invoke_host_stop(
            root=tmp_path,
            wait_attempts=1,
            sleeper=_no_sleep,
            owns_root=True,
            signal_stop=signal_stop,
        )
    )
    assert stopped["state"] == "stopped"
    assert stopped["owner_stop_file_missing"] is True
    assert not (tmp_path / DAEMON_LOCK_NAME).exists()

    recovered = _ok_mapping(
        invoke_host_recover_control(
            root=tmp_path,
            spawn=_recover_spawn,
            wait_attempts=1,
            sleeper=_no_sleep,
            owns_root=True,
        )
    )
    assert recovered["recovered"] is True


def test_owner_stop_when_file_missing_is_not_broadened(tmp_path: Path) -> None:
    _write_lock(tmp_path, os.getpid())
    status = invoke_host_status(root=tmp_path)
    assert is_refusal(status)
    assert status.context["field"] == "host_control"
    configure = invoke_host_configure_pairing_ttl("PT15M", root=tmp_path)
    assert is_refusal(configure)
    assert configure.context["field"] == "host_control"
    rotate = invoke_host_rotate_control(root=tmp_path)
    assert is_refusal(rotate)
    assert rotate.context["field"] == "host_control"
    signaled: list[int] = []

    def signal_stop(pid: int) -> None:
        signaled.append(pid)

    stranger = invoke_host_stop(
        root=tmp_path,
        wait_attempts=1,
        owns_root=False,
        signal_stop=signal_stop,
    )
    assert is_refusal(stranger)
    assert stranger.context["field"] == "host_control"
    assert signaled == []
    assert (tmp_path / DAEMON_LOCK_NAME).is_file()
    (tmp_path / DAEMON_LOCK_NAME).unlink()
    idle = invoke_host_stop(
        root=tmp_path,
        wait_attempts=1,
        owns_root=True,
        signal_stop=signal_stop,
    )
    assert is_ok(idle)
    assert idle.value["state"] == "stopped"
    assert signaled == []


def test_t_h_03_start_without_recover_does_not_remint(tmp_path: Path) -> None:
    def spawn(argv: tuple[str, ...], *, env: Mapping[str, str], root: Path) -> int:
        _ = argv, env
        _write_lock(root, os.getpid())
        _write_bind(root, "127.0.0.1", 19251)
        return os.getpid()

    started = invoke_host_start(root=tmp_path, spawn=spawn, wait_attempts=1, sleeper=_no_sleep)
    assert is_refusal(started)
    assert not (tmp_path / HOST_CONTROL_FILE).exists()
    status = invoke_host_status(root=tmp_path)
    assert is_refusal(status)
    rotate = invoke_host_rotate_control(root=tmp_path)
    assert is_refusal(rotate)
    live_recover = invoke_host_recover_control(
        root=tmp_path,
        spawn=_recover_spawn,
        wait_attempts=1,
        owns_root=True,
    )
    assert is_refusal(live_recover)
    assert live_recover.context["field"] == "recover-control"
    assert not (tmp_path / HOST_CONTROL_FILE).exists()


@pytest.mark.parametrize("value", [True, -1, 1.5, "16", None])
def test_stage_cap_wrapper_refuses_invalid_without_transport(value: object) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("invalid cap reached transport")

    assert is_refusal(invoke_host_configure_artifact_stage_max_bytes(value, transport=forbidden))


@pytest.fixture
def start_control(tmp_path: Path) -> Iterator[_HostControlServer]:
    server = _HostControlServer(_TOKEN, root=tmp_path)
    server.start()
    try:
        yield server
    finally:
        server.close()
        server.join(timeout=2)


def test_start_stale_bind_is_not_readiness(tmp_path: Path) -> None:
    _write_lock(tmp_path, os.getpid())
    _write_token(tmp_path)
    _write_bind(tmp_path, "127.0.0.1", 1)
    refused = invoke_host_start(root=tmp_path, wait_attempts=1)
    assert is_refusal(refused)
    assert "not ready" in str(refused.context["reason"])
    assert (tmp_path / DAEMON_LOCK_NAME).exists()


def test_start_invalid_wait_does_not_spawn(tmp_path: Path) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("invalid wait must refuse before spawning")

    assert is_refusal(invoke_host_start(root=tmp_path, spawn=forbidden, wait_attempts=0))


@pytest.mark.parametrize("early_exit", [False, True])
def test_failed_start_reaps_owned_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, early_exit: bool
) -> None:
    children: list[subprocess.Popen[bytes]] = []
    real_spawn = host_module._default_spawn  # pyright: ignore[reportPrivateUsage]

    def spawn(
        argv: tuple[str, ...], *, env: Mapping[str, str], root: Path
    ) -> subprocess.Popen[bytes]:
        code = (
            "import sys; print('fixture startup refused', file=sys.stderr); sys.exit(2)"
            if early_exit
            else "import time; time.sleep(60)"
        )
        child = real_spawn((sys.executable, "-c", code), env=env, root=root)
        children.append(child)
        return child

    monkeypatch.setattr(host_module, "_default_spawn", spawn)
    refused = invoke_host_start(root=tmp_path, wait_attempts=10 if early_exit else 1)
    assert is_refusal(refused)
    assert children[0].poll() is not None
    assert refused.context["cleanup_error"] is None
    assert not (tmp_path / DAEMON_LOCK_NAME).exists()
    if early_exit:
        assert "fixture startup refused" in (tmp_path / "logs/qma-daemon-startup.log").read_text()


@pytest.mark.parametrize(
    "payload",
    [
        {"ok": False, "status": {"lock": "held", "pid": os.getpid()}},
        {"ok": True, "status": {"lock": "held", "pid": 0}},
        {"ok": True, "status": {"lock": "free", "pid": os.getpid()}},
        {"ok": True, "status": "invalid"},
    ],
)
def test_start_refuses_unready_authenticated_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, payload: Mapping[str, object]
) -> None:
    from qmf.core import Ok

    _write_lock(tmp_path, os.getpid())

    def reply(*args: object, **kwargs: object) -> Ok[Mapping[str, object]]:
        return Ok(payload)

    monkeypatch.setattr(host_module, "_host_control_call", reply)
    assert is_refusal(invoke_host_start(root=tmp_path, wait_attempts=1))


def test_timed_out_interpreter_cannot_keep_or_later_acquire_writer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_spawn = host_module._default_spawn  # pyright: ignore[reportPrivateUsage]
    code = (
        "import os,json,time,pathlib,sys; r=pathlib.Path(sys.argv[1]); "
        "(r/'.daemon_writer').write_text(json.dumps({'pid':os.getpid()})); "
        "time.sleep(60)"
    )

    def spawn(
        argv: tuple[str, ...], *, env: Mapping[str, str], root: Path
    ) -> subprocess.Popen[bytes]:
        return real_spawn((sys.executable, "-c", code, str(root)), env=env, root=root)

    monkeypatch.setattr(host_module, "_default_spawn", spawn)
    refused = invoke_host_start(root=tmp_path, wait_attempts=10)
    assert is_refusal(refused)
    assert refused.context["cleanup_error"] is None
    status = _ok_mapping(invoke_host_status(root=tmp_path))
    assert status["lock"] == "free"
    assert not (tmp_path / DAEMON_LOCK_NAME).exists()


def test_interrupted_start_reaps_owned_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    children: list[subprocess.Popen[bytes]] = []
    real_spawn = host_module._default_spawn  # pyright: ignore[reportPrivateUsage]

    def spawn(
        argv: tuple[str, ...], *, env: Mapping[str, str], root: Path
    ) -> subprocess.Popen[bytes]:
        child = real_spawn(
            (sys.executable, "-c", "import time; time.sleep(60)"), env=env, root=root
        )
        children.append(child)
        return child

    def interrupted(*args: object, **kwargs: object) -> bool:
        raise KeyboardInterrupt

    monkeypatch.setattr(host_module, "_default_spawn", spawn)
    monkeypatch.setattr(host_module, "_ready", interrupted)
    with pytest.raises(KeyboardInterrupt):
        invoke_host_start(root=tmp_path)
    assert children[0].poll() is not None
