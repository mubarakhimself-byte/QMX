"""Real CT-40 pairing/grants reach an operator-pinned retained paper ledger."""

from __future__ import annotations

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, cast

import pytest
from qma.daemon.bootstrap_config import load_plugin_load_configs
from qma.daemon.pairing import CT40_WS_SUBPROTOCOL, issue_pairing_session
from qma.daemon.process import DaemonProcess
from qma.daemon.request_runtime.spot_state import SPOT_CONTRIBUTION, load_spot_state_bindings
from qma.daemon.request_runtime.spot_tools import spot_query_descriptor
from qma.wire.initialize import WIRE_PROTOCOL_VERSION
from qma.wire.invocation_envelope import compute_input_hash
from qmf.core import is_ok, is_refusal
from qmn.testing.spot_paper import open_account, tick
from test_pairing_listener import _pair_over_listener  # pyright: ignore[reportPrivateUsage]
from test_request_runtime_daemon import rpc, ws_connect


def seed(root: Path) -> dict[str, Any]:
    root.mkdir(exist_ok=True)
    corpus = root / "corpus"
    corpus.mkdir()
    a, b = open_account(root / "paper"), open_account(root / "paper", "b", "new-york", "15")
    assert is_ok(a) and is_ok(b)
    try:
        assert is_ok(tick(a.value)) and is_ok(tick(b.value))
        assert is_ok(a.value.submit("buy", "buy", "0.200", "100.00", now_ns=1000))
        assert is_refusal(b.value.submit("buy", "buy", "0.200", "100.00", now_ns=1000))
        db_path = a.value.db.execute("PRAGMA database_list").fetchone()[2]
        config = {
            "research_corpus_root_path": str(corpus),
            "host_retry_attempt_ceiling": 1,
            "spot_paper_queries": {
                "pack:trading-readonly": {
                    "config_revision": 7,
                    "package_version": "0.1.0",
                    "provider_connection_id": "conn:recorded",
                    "venue_id": "recorded:crypto",
                    "account_id": "a",
                    "policy_ref": a.value.policy.policy_ref,
                    "state_db_path": db_path,
                }
            },
        }
        (root / "operator-config.json").write_text(json.dumps(config), encoding="utf-8")
        return config
    finally:
        a.value.close()
        b.value.close()


def invocation(
    session: str, grant: str, payload: dict[str, object], logical: str
) -> dict[str, object]:
    hashed = compute_input_hash(payload, descriptor=spot_query_descriptor())
    assert is_ok(hashed)
    return {
        "product_session_ref": session,
        "payload": payload,
        "envelope": {
            "logical_invocation_id": logical,
            "attempt_id": 1,
            "op_id": "qmn.spot.paper.query",
            "op_version": 1,
            "contribution": {"qualified_id": SPOT_CONTRIBUTION, "package_version": "0.1.0"},
            "instance_id": "pack:trading-readonly",
            "config_revision": 7,
            "grant_id": grant,
            "effect_class": "read",
            "idempotency_key": logical,
            "reconcile_policy": "query-then-decide",
            "input_hash": hashed.value,
            "call_depth": 0,
            "caller_kind": "user",
            "caller_session_ref": session,
        },
    }


def test_real_pairing_grant_query_scope_revocation_and_restart(tmp_path: Path) -> None:
    seed(tmp_path)

    async def run(phase: str, saved: tuple[str, str] | None = None) -> tuple[str, str]:
        composed = DaemonProcess.compose(
            tmp_path,
            machine="spot-test",
            boot_epoch_id=phase,
            plugin_load_configs=load_plugin_load_configs(tmp_path),
        )
        assert is_ok(composed), composed
        process = composed.value
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            _, proof = await _pair_over_listener(process, bound.value.host, bound.value.port)
            reader, writer, opening = await ws_connect(process, proof=proof)
            assert b"101 Switching Protocols" in opening
            try:
                initialized = await rpc(
                    reader,
                    writer,
                    "initialize",
                    {
                        "protocolVersion": WIRE_PROTOCOL_VERSION,
                        "capabilities": {},
                    },
                )
                assert "result" in initialized, initialized
                opened = await rpc(
                    reader,
                    writer,
                    "open_product_session",
                    {
                        "instance_id": "pack:trading-readonly",
                        "qualified_id": SPOT_CONTRIBUTION,
                        "package_version": "0.1.0",
                    },
                )
                if phase == "retarget":
                    assert "error" in opened, opened
                    assert saved is not None
                    return saved
                assert "result" in opened, opened
                session = cast(str, cast(dict[str, Any], opened["result"])["product_session_id"])
                if saved is None:
                    denied_without_grant = await rpc(
                        reader,
                        writer,
                        "start_mission",
                        invocation(
                            session,
                            "grant:missing",
                            {
                                "account_id": "a",
                                "provider_connection_id": "conn:recorded",
                                "venue_id": "recorded:crypto",
                            },
                            phase + "no-grant",
                        ),
                    )
                    assert "error" in denied_without_grant
                    granted = await rpc(
                        reader,
                        writer,
                        "grant_product_session",
                        {
                            "product_session_ref": session,
                            "expected_revision": 0,
                            "op_id": "qmn.spot.paper.query",
                            "op_version": 1,
                            "parameter_ceiling": {
                                "allow_keys": [
                                    "account_id",
                                    "provider_connection_id",
                                    "venue_id",
                                ]
                            },
                            "expires_at": "2099-01-01T00:00:00Z",
                        },
                    )
                    assert "result" in granted, granted
                    grant = cast(str, cast(dict[str, Any], granted["result"])["grant_id"])
                else:
                    assert saved[0] == session
                    grant = saved[1]
                payload: dict[str, object] = {
                    "provider_connection_id": "conn:recorded",
                    "venue_id": "recorded:crypto",
                    "account_id": "a",
                }
                result = await rpc(
                    reader, writer, "start_mission", invocation(session, grant, payload, phase)
                )
                assert "result" in result, result
                view = cast(dict[str, Any], result["result"])
                assert view["balances"]["USDT"]["reserved"] == "20.02000000"
                assert view["retained"] is True
                assert "writer_available" not in view
                for key, value in (
                    ("account_id", "b"),
                    ("venue_id", "elsewhere"),
                    ("provider_connection_id", "other"),
                    ("state_db_path", "x"),
                ):
                    wrong = {**payload, key: value}
                    denied = await rpc(
                        reader,
                        writer,
                        "start_mission",
                        invocation(session, grant, wrong, phase + key),
                    )
                    assert "error" in denied, denied
                execution = await rpc(
                    reader,
                    writer,
                    "grant_product_session",
                    {
                        "product_session_ref": session,
                        "expected_revision": 1,
                        "op_id": "qmn.spot.paper.submit",
                        "op_version": 1,
                        "parameter_ceiling": {"allow_keys": []},
                        "expires_at": "2099-01-01T00:00:00Z",
                    },
                )
                assert "error" in execution
                if saved is not None:
                    revoked = process.product_sessions.revoke_grant(
                        session,
                        grant_id=grant,
                        principal="operator",
                        reason="spot integration",
                        revoked_at="2026-10-04T00:00:00Z",
                    )
                    assert is_ok(revoked)
                    denied = await rpc(
                        reader,
                        writer,
                        "start_mission",
                        invocation(session, grant, payload, phase + "revoked"),
                    )
                    assert "error" in denied
                (tmp_path / (phase + "-auth-proof.json")).write_text(
                    json.dumps(
                        {
                            "transport": "paired CT-40 websocket",
                            "simulation": True,
                            "query_view": view,
                            "grant_checked": True,
                            "scope_retarget_denied": True,
                            "execution_grant_denied": True,
                            "grant_revocation_checked": saved is not None,
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                return session, grant
            finally:
                writer.close()
                await writer.wait_closed()
        finally:
            await process.aclose()

    saved = asyncio.run(run("seed"))
    asyncio.run(run("restart", saved))
    # Even if the operator accidentally reuses a config revision, a retained
    # account session/grant must not silently become authority over account b.
    other = open_account(tmp_path / "paper", "b", "new-york", "15")
    assert is_ok(other)
    try:
        config = json.loads((tmp_path / "operator-config.json").read_text())
        row = config["spot_paper_queries"]["pack:trading-readonly"]
        row["account_id"] = "b"
        row["policy_ref"] = other.value.policy.policy_ref
        row["state_db_path"] = other.value.db.execute("PRAGMA database_list").fetchone()[2]
        (tmp_path / "operator-config.json").write_text(json.dumps(config), encoding="utf-8")
    finally:
        other.value.close()
    asyncio.run(run("retarget", saved))


@pytest.mark.parametrize("change", ["policy_ref", "account_id", "state_db_path"])
def test_retained_view_identity_or_storage_mismatch_refuses(tmp_path: Path, change: str) -> None:
    config = seed(tmp_path)
    row = config["spot_paper_queries"]["pack:trading-readonly"]
    row[change] = str(tmp_path / "absent.sqlite") if change == "state_db_path" else "wrong"
    (tmp_path / "operator-config.json").write_text(json.dumps(config), encoding="utf-8")
    bindings = load_spot_state_bindings(tmp_path)
    assert is_ok(bindings)
    binding = bindings.value["pack:trading-readonly"]
    assert is_refusal(binding.query(binding.scope))
    assert not (tmp_path / "absent.sqlite").exists()


def test_invalid_spot_startup_refuses_without_hanging(tmp_path: Path) -> None:
    config = seed(tmp_path)
    rows = config["spot_paper_queries"]
    rows["pack:missing"] = rows.pop("pack:trading-readonly")
    (tmp_path / "operator-config.json").write_text(json.dumps(config), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "qma.daemon"],
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(sys.path),
            "QMA_DAEMON_ROOT": str(tmp_path),
        },
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 2
    assert "spot read contribution is not enabled" in result.stderr


def test_normal_module_entrypoint_loads_spot_binding(tmp_path: Path) -> None:
    seed(tmp_path)
    composed = DaemonProcess.compose(
        tmp_path,
        machine="entry-seed",
        boot_epoch_id="seed",
        plugin_load_configs=load_plugin_load_configs(tmp_path),
    )
    assert is_ok(composed)
    seed_process = composed.value
    try:
        bindings = load_spot_state_bindings(tmp_path)
        assert is_ok(bindings)
        minted = seed_process.product_sessions.mint(
            product_session_id="psess:entry",
            profile="app-use",
            principal="operator",
            contribution={"qualified_id": SPOT_CONTRIBUTION, "package_version": "0.1.0"},
            instance_id="pack:trading-readonly",
            app_instance_id="pack:trading-readonly",
            config_revision=7,
            as_of="2026-10-04T00:00:00Z",
            account_scope=bindings.value["pack:trading-readonly"].authority_scope,
            selected_refs=[{"kind": "instance_id", "id": "pack:trading-readonly"}],
        )
        assert is_ok(minted)
        granted = seed_process.product_sessions.host_grant(
            "psess:entry",
            grant_id="grant:entry",
            op_id="qmn.spot.paper.query",
            op_version=1,
            effect_class="read",
            parameter_ceiling={
                "allow_keys": [
                    "account_id",
                    "provider_connection_id",
                    "venue_id",
                ]
            },
            expires_at="2099-01-01T00:00:00Z",
        )
        assert is_ok(granted)
        issued = issue_pairing_session(
            journal=seed_process.journal,
            sqlite=seed_process.sqlite,
            origin="http://127.0.0.1:5173",
            expires_at=time.time_ns() + 3600_000_000_000,
        )
        assert is_ok(issued)
        proof = issued.value.pairing_proof
    finally:
        seed_process.close()
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    environment = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(sys.path),
        "QMA_DAEMON_ROOT": str(tmp_path),
        "QMA_DAEMON_BIND_PORT": str(port),
    }
    with (tmp_path / "entrypoint.log").open("w", encoding="utf-8") as log:
        child = subprocess.Popen(
            [sys.executable, "-m", "qma.daemon"],
            env=environment,
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            deadline = time.monotonic() + 15
            while True:
                assert child.poll() is None, (tmp_path / "entrypoint.log").read_text()
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2) as connection:
                        connection.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
                        reply = connection.recv(4096)
                        assert b"HTTP/1.1" in reply
                        break
                except OSError:
                    assert time.monotonic() < deadline
                    time.sleep(0.05)

            async def query_entrypoint() -> None:
                reader, writer = await asyncio.open_connection("127.0.0.1", port)
                try:
                    writer.write(
                        (
                            f"GET / HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\n"
                            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
                            "Sec-WebSocket-Version: 13\r\n"
                            "Sec-WebSocket-Key: YWdlbnQtdGVzdC1rZXkxMg==\r\n"
                            f"Sec-WebSocket-Protocol: {CT40_WS_SUBPROTOCOL}, qmx.pair.{proof}\r\n"
                            "Origin: http://127.0.0.1:5173\r\n\r\n"
                        ).encode()
                    )
                    await writer.drain()
                    opening = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=3)
                    assert b"101 Switching Protocols" in opening
                    initialized = await rpc(
                        reader,
                        writer,
                        "initialize",
                        {
                            "protocolVersion": WIRE_PROTOCOL_VERSION,
                            "capabilities": {},
                        },
                    )
                    assert "result" in initialized
                    queried = await rpc(
                        reader,
                        writer,
                        "start_mission",
                        invocation(
                            "psess:entry",
                            "grant:entry",
                            {
                                "account_id": "a",
                                "provider_connection_id": "conn:recorded",
                                "venue_id": "recorded:crypto",
                            },
                            "entrypoint-query",
                        ),
                    )
                    assert "result" in queried, queried
                    view = cast(dict[str, Any], queried["result"])
                    assert view["scope"]["account_id"] == "a"
                    assert view["balances"]["USDT"]["reserved"] == "20.02000000"
                    (tmp_path / "entrypoint-auth-proof.json").write_text(
                        json.dumps(
                            {
                                "entrypoint": "python -m qma.daemon",
                                "transport": "paired CT-40 websocket",
                                "query_view": view,
                                "restored_grant_checked": True,
                            },
                            indent=2,
                        ),
                        encoding="utf-8",
                    )
                finally:
                    writer.close()
                    await writer.wait_closed()

            asyncio.run(query_entrypoint())
        finally:
            child.terminate()
            child.wait(timeout=5)
