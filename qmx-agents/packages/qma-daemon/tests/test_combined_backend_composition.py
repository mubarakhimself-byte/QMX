"""One operator configuration and paired listener across skills, spot and QMB.

The model transport is explicitly offline; spot is recorded simulation. QMB
environment registration does not claim CT47 authoring or execution authority.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import pytest
from qma.daemon.bootstrap_config import load_plugin_load_configs
from qma.daemon.process import DaemonProcess
from qma.daemon.request_runtime.spot_state import SPOT_CONTRIBUTION
from qma.wire.initialize import WIRE_PROTOCOL_VERSION
from qmf.core import is_ok
from test_agent_extensions import BODY, FINAL, READ
from test_agent_extensions_daemon import configure_file, offline
from test_pairing_listener import _pair_over_listener  # pyright: ignore[reportPrivateUsage]
from test_request_runtime_daemon import mint, rpc, submit_params, ws_connect
from test_request_runtime_tool_loop import ScriptedText
from test_spot_daemon_binding import invocation, seed


def test_paired_skills_and_spot_share_startup_and_recover_without_effects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = seed(tmp_path)
    config["agent_sdk"] = configure_file(tmp_path)
    config["qmb_local_environment"] = {
        "provider_ref": "operator-local-qmb",
        "network": "none",
    }
    (tmp_path / "operator-config.json").write_text(json.dumps(config), encoding="utf-8")
    scripted = ScriptedText([READ, FINAL])
    offline(monkeypatch, scripted)

    async def run(boot: str, saved: tuple[str, str] | None) -> tuple[str, str]:
        composed = DaemonProcess.compose(
            tmp_path,
            machine="combined-backend-fixture",
            boot_epoch_id=boot,
            plugin_load_configs=load_plugin_load_configs(tmp_path),
        )
        assert is_ok(composed), composed
        process = composed.value
        try:
            assert process.agent_requests is not None
            environment = process.execution_environments.declaration("local")
            assert environment is not None and environment.network.value == "none"
            assert process.backtesting.environments is process.execution_environments
            assert process.compute_router.environments is process.execution_environments
            if saved is None:
                mint(process)
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
                    {"protocolVersion": WIRE_PROTOCOL_VERSION, "capabilities": {}},
                )
                assert "result" in initialized, initialized
                admitted = await rpc(reader, writer, "submit_agent_request", submit_params())
                assert "result" in admitted, admitted
                request_id = admitted["result"]["request_id"]
                deadline = time.monotonic() + 10
                while True:
                    status = await rpc(
                        reader,
                        writer,
                        "get_agent_request",
                        {"product_session_ref": "psess:agent", "request_id": request_id},
                    )
                    assert "result" in status, status
                    if status["result"]["status"] == "completed":
                        break
                    assert time.monotonic() < deadline, status
                    await asyncio.sleep(0.01)
                assert status["result"]["content"] == "Run-1: verified 7 observations"
                assert len(scripted.requests) == 2
                assert BODY in scripted.requests[1].prompt
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
                assert "result" in opened, opened
                session = opened["result"]["product_session_id"]
                if saved is None:
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
                                "allow_keys": ["account_id", "provider_connection_id", "venue_id"]
                            },
                            "expires_at": "2099-01-01T00:00:00Z",
                        },
                    )
                    assert "result" in granted, granted
                    grant = granted["result"]["grant_id"]
                else:
                    assert session == saved[0]
                    grant = saved[1]
                payload: dict[str, object] = {
                    "account_id": "a",
                    "provider_connection_id": "conn:recorded",
                    "venue_id": "recorded:crypto",
                }
                queried = await rpc(
                    reader, writer, "start_mission", invocation(session, grant, payload, boot)
                )
                assert "result" in queried, queried
                assert queried["result"]["balances"]["USDT"]["reserved"] == "20.02000000"
                denied = await rpc(
                    reader,
                    writer,
                    "start_mission",
                    invocation(session, grant, {**payload, "account_id": "b"}, boot + "wrong"),
                )
                assert "error" in denied, denied
                assert len(scripted.requests) == 2
                report: dict[str, Any] = {
                    "offline_model": True,
                    "recorded_spot_simulation": True,
                    "boot": boot,
                    "model_requests": len(scripted.requests),
                    "skills": status["result"],
                    "spot": queried["result"],
                    "retarget_refused": True,
                    "qmb_environment": environment.provider_ref,
                    "ct47_authority_proven": False,
                }
                (tmp_path / (boot + ".json")).write_text(
                    json.dumps(report, indent=2), encoding="utf-8"
                )
                return session, grant
            finally:
                writer.close()
                await writer.wait_closed()
        finally:
            await process.aclose()

    saved = asyncio.run(run("first", None))
    asyncio.run(run("restart", saved))
