"""Story 67.1 — product root, host-control channel, start lock/spawn."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import cast

from qma.daemon.host_control import (
    CT40_BIND_PORT,
    HOST_CONTROL_EXISTED_AT_INSPECT_SHA,
    HOST_CONTROL_FILE,
    HOST_CONTROL_IS_CT40,
    INSPECT_CWD_RELATIVE_ROOT,
    LOCAL_OPERATOR_EXISTED_AT_INSPECT_SHA,
    LOCAL_OPERATOR_NEW_SQLITE_CLASS,
    ROTATE_CONTROL_EXISTED_AT_INSPECT_SHA,
    claim_host_configure_existed_at_inspect_sha,
    claim_host_control_existed_at_inspect_sha,
    claim_local_operator_existed_at_inspect_sha,
    claim_rotate_control_existed_at_inspect_sha,
    claim_types_absent_at_inspect_sha,
    host_control_call,
    load_local_operator,
    principal_count,
    product_daemon_root,
    read_host_control_bind,
    read_host_control_token,
    redact_host_surface,
    resolve_daemon_root,
)
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import (
    BROWSER_SPAWNS_PYTHON,
    DAEMON_SPAWN_MODULE,
    DEFAULT_BIND_PORT,
    HOST_CONTROL_ON_CT40_PORT,
    START_GRANTS,
    START_ORCHESTRATES_MISSIONS,
    START_STARTS_QMN,
    STOP_CANCELS_QMN,
    STOP_STOPS_REMOTE,
    DaemonProcess,
    supervised_spawn_argv,
)
from qma.daemon.sessions import PRODUCT_SESSION_TYPES_EXISTED_AT_INSPECT_SHA_34C148B
from qma.wire import HUMAN_GATE_COMMANDS, GrantRecord, WireEnvelope
from qma.wire.invocation_envelope import INVOCATION_ENVELOPE_EXISTED_AT_INSPECT_SHA_34C148B
from qmf.core import is_ok, is_refusal

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "host_control_usage.py"


def _seed_configs(tmp_path: Path) -> dict[str, dict[str, object]]:
    seed = tmp_path / "seed-corpus"
    seed.mkdir(exist_ok=True)
    return research_corpus_plugin_load_config(seed)


def _compose(tmp_path: Path, *, boot: str = "boot-67-1") -> DaemonProcess:
    result = DaemonProcess.compose(
        tmp_path,
        machine="test-host",
        boot_epoch_id=boot,
        bind_port=0,
        plugin_load_configs=_seed_configs(tmp_path),
    )
    assert is_ok(result), result
    return result.value


def test_product_root_is_not_inspect_cwd_relative() -> None:
    win = product_daemon_root(
        system="win32",
        environ={"LOCALAPPDATA": r"C:\Users\op\AppData\Local"},
    )
    assert win == Path(r"C:\Users\op\AppData\Local") / "QMX" / "qma-daemon"
    linux = product_daemon_root(system="linux", environ={"HOME": "/home/op"})
    assert linux == Path("/home/op/.local/state/qmx/qma-daemon")
    mac = product_daemon_root(system="darwin", environ={"HOME": "/Users/op"})
    assert mac == Path("/Users/op/Library/Application Support/QMX/qma-daemon")
    resolved = resolve_daemon_root({})
    assert resolved == product_daemon_root()
    assert INSPECT_CWD_RELATIVE_ROOT not in resolved.parts
    explicit = resolve_daemon_root({"QMA_DAEMON_ROOT": "/var/qmx/custom-root"})
    assert explicit == Path("/var/qmx/custom-root")


def test_host_control_binds_outside_8765_and_status_stop(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path)
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            listener = bound.value
            assert listener.port != 0
            channel = process.host_control
            assert channel is not None
            assert channel.bound is not None
            assert channel.bound.port != CT40_BIND_PORT
            assert channel.bound.port != DEFAULT_BIND_PORT
            assert HOST_CONTROL_ON_CT40_PORT is False
            assert HOST_CONTROL_IS_CT40 is False
            token = read_host_control_token(tmp_path)
            assert is_ok(token)
            bind = read_host_control_bind(tmp_path)
            assert is_ok(bind)
            assert bind.value[1] == channel.bound.port
            again = ensure_not_reminted(tmp_path, token.value)
            assert again == token.value
            status = await asyncio.to_thread(host_control_call, tmp_path, "status")
            assert is_ok(status), status
            payload = status.value
            assert payload["ok"] is True
            snapshot = payload["status"]
            assert isinstance(snapshot, dict)
            fields = cast("dict[str, object]", snapshot)
            assert fields["lock"] == "held"
            assert fields["pid"] == os.getpid()
            assert fields["operator_established"] is True
            assert fields["ttl"] == "unset"
            assert str(listener.port) in str(fields["bind"])
            live = load_local_operator(process.sqlite)
            assert live is not None
            assert principal_count(process.sqlite) == 1
            dumped = json.dumps(dict(payload))
            assert token.value not in dumped
            assert "Authorization" not in dumped
            stale = await asyncio.to_thread(_stale_status, tmp_path)
            assert stale["ok"] is False
            stopped = await asyncio.to_thread(host_control_call, tmp_path, "stop")
            assert is_ok(stopped), stopped
            assert stopped.value.get("stopped") is True
            for _ in range(50):
                if process.is_closed:
                    break
                await asyncio.sleep(0.01)
            assert process.is_closed is True
        finally:
            if not process.is_closed:
                await process.aclose()

    asyncio.run(_run())


def ensure_not_reminted(root: Path, previous: str) -> str:
    from qma.daemon.host_control import ensure_host_control_token

    minted = ensure_host_control_token(root)
    assert is_ok(minted)
    assert minted.value == previous
    return minted.value


def _stale_status(root: Path) -> dict[str, object]:
    import socket

    from qma.daemon.host_control import encode_host_control_frame, read_host_control_bind

    bound = read_host_control_bind(root)
    assert is_ok(bound)
    host, port = bound.value
    request = {"verb": "status", "host_control": "wrong-token"}
    with socket.create_connection((host, port), timeout=2.0) as sock:
        sock.sendall(encode_host_control_frame(request))
        header = sock.recv(4)
        size = int.from_bytes(header, "big")
        body = sock.recv(size)
    parsed: object = json.loads(body.decode("utf-8"))
    assert isinstance(parsed, dict)
    return cast("dict[str, object]", parsed)


def test_ct40_still_discards_bytes_and_host_control_is_separate(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-67-1-ct40")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            listener = bound.value
            _reader, writer = await asyncio.open_connection(listener.host, listener.port)
            writer.write(b"POST /host/stop HTTP/1.1\r\n\r\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            await asyncio.sleep(0.05)
            assert process.accepted_connections >= 1
            source = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "process.py"
            text = source.read_text(encoding="utf-8")
            assert "POST /host/" not in text
        finally:
            await process.aclose()

    asyncio.run(_run())


def test_spawn_argv_and_lifecycle_flags() -> None:
    argv = supervised_spawn_argv("/usr/bin/python")
    assert argv == ("/usr/bin/python", "-m", DAEMON_SPAWN_MODULE)
    assert START_ORCHESTRATES_MISSIONS is False
    assert START_GRANTS is False
    assert START_STARTS_QMN is False
    assert BROWSER_SPAWNS_PYTHON is False
    assert STOP_CANCELS_QMN is False
    assert STOP_STOPS_REMOTE is False
    assert "start" not in HUMAN_GATE_COMMANDS
    assert "stop" not in HUMAN_GATE_COMMANDS
    assert "recover-control" not in HUMAN_GATE_COMMANDS
    assert "rotate-control" not in HUMAN_GATE_COMMANDS
    assert "host.start" not in HUMAN_GATE_COMMANDS


def test_honesty_inspect_sha() -> None:
    assert HOST_CONTROL_EXISTED_AT_INSPECT_SHA is False
    assert LOCAL_OPERATOR_EXISTED_AT_INSPECT_SHA is False
    assert LOCAL_OPERATOR_NEW_SQLITE_CLASS is False
    assert ROTATE_CONTROL_EXISTED_AT_INSPECT_SHA is False
    claimed = claim_host_control_existed_at_inspect_sha(True)
    assert is_refusal(claimed)
    assert is_ok(claim_host_control_existed_at_inspect_sha(False))
    assert is_refusal(claim_local_operator_existed_at_inspect_sha(True))
    assert is_ok(claim_local_operator_existed_at_inspect_sha(False))
    assert is_refusal(claim_host_configure_existed_at_inspect_sha(True))
    assert is_ok(claim_host_configure_existed_at_inspect_sha(False))
    assert is_refusal(claim_rotate_control_existed_at_inspect_sha(True))
    assert is_ok(claim_rotate_control_existed_at_inspect_sha(False))
    assert INVOCATION_ENVELOPE_EXISTED_AT_INSPECT_SHA_34C148B is True
    assert PRODUCT_SESSION_TYPES_EXISTED_AT_INSPECT_SHA_34C148B is True
    assert WireEnvelope.__name__ == "WireEnvelope"
    assert GrantRecord.__name__ == "GrantRecord"
    absent = claim_types_absent_at_inspect_sha(True)
    assert is_refusal(absent)
    assert is_ok(claim_types_absent_at_inspect_sha(False))


def test_redact_allows_pairing_record_id() -> None:
    redacted = redact_host_surface(
        {
            "pairing_record_id": "pair:1",
            "host_control": "secret",
            "Authorization": "Bearer pairing:abc",
            "qmx.pair.proof": "nope",
            "pairing_proof": "raw",
            "pending_code": "1234",
        }
    )
    assert isinstance(redacted, dict)
    assert redacted["pairing_record_id"] == "pair:1"
    assert redacted["host_control"] == "[redacted]"
    assert redacted["Authorization"] == "[redacted]"
    assert redacted["pairing_proof"] == "[redacted]"


def test_compose_does_not_remint_existing_token(tmp_path: Path) -> None:
    first = _compose(tmp_path, boot="boot-67-1-mint")
    token = read_host_control_token(tmp_path)
    assert is_ok(token)
    first.close()
    second = _compose(tmp_path, boot="boot-67-1-again")
    try:
        again = read_host_control_token(tmp_path)
        assert is_ok(again)
        assert again.value == token.value
        assert (tmp_path / HOST_CONTROL_FILE).is_file()
    finally:
        second.close()


def test_example_script() -> None:
    import runpy

    namespace = runpy.run_path(str(EXAMPLE), run_name="__main__")
    assert namespace["main"] is not None
