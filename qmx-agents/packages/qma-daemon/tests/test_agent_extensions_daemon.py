"""Operator startup and authenticated CT40 skills path, with offline transport."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import pytest
from qma.daemon.request_runtime.http_provider import ChatCompletionsProvider
from qma.daemon.request_runtime.provider_config import load_agent_request_config
from qma.daemon.request_runtime.providers import ProviderError
from qma.wire.initialize import WIRE_PROTOCOL_VERSION, WireConnection
from qmf.core import is_refusal
from test_agent_extensions import BODY, FINAL, READ, library
from test_request_runtime_daemon import (
    compose,
    connection,
    dispatch,
    mint,
    receipt,
    rpc,
    submit_params,
    value,
    wait_status,
    ws_connect,
)
from test_request_runtime_tool_loop import ScriptedText


def configure_file(root: Path) -> dict[str, Any]:
    library(root, profile="global", sessions=["psess:agent"])
    sdk: dict[str, Any] = {
        "enabled": True,
        "providers": {
            "offline": {
                "protocol": "chat-completions",
                "endpoint": "http://127.0.0.1:9876/v1/chat/completions",
                "model": "fixture-model",
                "deployment_id": "fixture-only",
            }
        },
        "profiles": {
            "global": {
                "role": "global",
                "authority_profile": "authoring",
                "provider_id": "offline",
                "instructions": "HOST_SENTINEL",
                "tools": [],
            }
        },
        "agent_extensions": {
            "roots": {"local": "approved"},
            "profiles": {
                "global": {
                    "sources": ["local"],
                    "sessions": ["psess:agent"],
                    "middleware": ["audit-v1"],
                }
            },
        },
    }
    write(root, sdk)
    return sdk


def write(root: Path, sdk: dict[str, Any]) -> None:
    (root / "operator-config.json").write_text(json.dumps({"agent_sdk": sdk}), encoding="utf-8")


def offline(monkeypatch: pytest.MonkeyPatch, scripted: ScriptedText) -> None:
    def transport(self: Any, request: Any, emit: Any, cancellation: Any) -> Any:
        return scripted.execute(request, emit, cancellation)

    monkeypatch.setattr(ChatCompletionsProvider, "execute", transport)


def test_authenticated_startup_loads_skills_and_emits_hooks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_file(tmp_path)
    scripted = ScriptedText([READ, FINAL])
    offline(monkeypatch, scripted)
    process = compose(tmp_path)
    try:
        mint(process)
        unauthenticated = dispatch(
            process, WireConnection(), "submit_agent_request", submit_params()
        )
        assert "error" in unauthenticated and not scripted.requests
        conn = connection(process)
        accepted = receipt(dispatch(process, conn, "submit_agent_request", submit_params()))
        row = wait_status(process, conn, str(accepted["request_id"]), "completed")
        assert row["content"] == "Run-1: verified 7 observations"
        assert len(scripted.requests) == 2
        assert "HOST_SENTINEL" in scripted.requests[0].instructions
        assert BODY not in scripted.requests[0].prompt + scripted.requests[0].instructions
        assert BODY in scripted.requests[1].prompt
        events = process.journal.read_events()
        assert not is_refusal(events)
        assert "before_agent" in repr(events.value) and "tool_enter" in repr(events.value)
        # Terminal replay retains receipt, with no new model or hook execution.
        receipt(dispatch(process, conn, "submit_agent_request", submit_params()))
        assert len(scripted.requests) == 2
    finally:
        process.close()


def test_daemon_close_reopen_resumes_checkpointed_skill_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_file(tmp_path)
    scripted = ScriptedText([READ, FINAL])
    offline(monkeypatch, scripted)

    def loss(count: int) -> None:
        if count == 2:
            raise ProviderError("outcome_unknown", "Offline transport loss")

    scripted.after = loss
    first = compose(tmp_path, boot="extensions-one")
    try:
        mint(first)
        conn = connection(first)
        accepted = receipt(dispatch(first, conn, "submit_agent_request", submit_params()))
        request_id = str(accepted["request_id"])
        wait_status(first, conn, request_id, "interrupted")
    finally:
        first.close()
    scripted.after = None
    second = compose(tmp_path, boot="extensions-two")
    try:
        conn = connection(second)
        receipt(
            dispatch(
                second,
                conn,
                "resume_agent_request",
                {"request_id": request_id, "product_session_ref": "psess:agent"},
            )
        )
        row = wait_status(second, conn, request_id, "completed")
        assert row["attempt"] == 2
        assert len(scripted.requests) == 3 and BODY in scripted.requests[-1].prompt
    finally:
        second.close()


def test_content_and_association_change_pin_host_identity(tmp_path: Path) -> None:
    sdk = configure_file(tmp_path)
    first = load_agent_request_config(tmp_path)
    assert not is_refusal(first) and first.value is not None
    identity = first.value.policies["global"].provider_id
    path = tmp_path / "approved" / "analysis" / "SKILL.md"
    path.write_text(path.read_text(encoding="utf-8") + " changed", encoding="utf-8")
    second = load_agent_request_config(tmp_path)
    assert not is_refusal(second) and second.value is not None
    assert second.value.policies["global"].provider_id != identity
    identity = second.value.policies["global"].provider_id
    sdk["agent_extensions"]["profiles"]["global"]["sessions"] = ["psess:other"]
    write(tmp_path, sdk)
    third = load_agent_request_config(tmp_path)
    assert not is_refusal(third) and third.value is not None
    assert third.value.policies["global"].provider_id != identity


def test_generic_extensions_do_not_configure_native_skills(tmp_path: Path) -> None:
    sdk = configure_file(tmp_path)
    sdk["providers"]["offline"] = {
        "protocol": "codex-app-server",
        "executable": "codex",
        "deployment_id": "fixture",
    }
    write(tmp_path, sdk)
    assert is_refusal(load_agent_request_config(tmp_path))


def test_unknown_extension_profile_refused_without_provider_call(tmp_path: Path) -> None:
    sdk = configure_file(tmp_path)
    sdk["agent_extensions"]["profiles"]["unknown"] = {"sources": ["local"]}
    write(tmp_path, sdk)
    assert is_refusal(load_agent_request_config(tmp_path))


def test_unselected_session_keeps_direct_inference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sdk = configure_file(tmp_path)
    sdk["agent_extensions"]["profiles"]["global"]["sessions"] = ["psess:other"]
    write(tmp_path, sdk)
    scripted = ScriptedText(["plain raw answer"])
    offline(monkeypatch, scripted)
    process = compose(tmp_path)
    try:
        mint(process)
        conn = connection(process)
        accepted = receipt(dispatch(process, conn, "submit_agent_request", submit_params()))
        row = wait_status(process, conn, str(accepted["request_id"]), "completed")
        assert row["content"] == "plain raw answer"
        assert len(scripted.requests) == 1
        assert "read_file" not in scripted.requests[0].instructions
    finally:
        process.close()


def test_paired_websocket_executes_progressive_skill_graph(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_file(tmp_path)
    scripted = ScriptedText([READ, FINAL])
    offline(monkeypatch, scripted)

    async def run() -> None:
        process = compose(tmp_path)
        mint(process)
        writer = None
        try:
            value(await process.bind())
            reader, writer, opening = await ws_connect(process)
            assert b"101 Switching Protocols" in opening
            receipt(
                await rpc(
                    reader,
                    writer,
                    "initialize",
                    {"protocolVersion": WIRE_PROTOCOL_VERSION, "capabilities": {}},
                )
            )
            accepted = receipt(await rpc(reader, writer, "submit_agent_request", submit_params()))
            deadline = time.monotonic() + 5
            while True:
                row = receipt(
                    await rpc(
                        reader,
                        writer,
                        "get_agent_request",
                        {
                            "product_session_ref": "psess:agent",
                            "request_id": accepted["request_id"],
                        },
                    )
                )
                if row["status"] == "completed":
                    break
                assert row["status"] in {"queued", "running"} and time.monotonic() < deadline, row
                await asyncio.sleep(0.01)
            assert len(scripted.requests) == 2 and BODY in scripted.requests[1].prompt
        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()
            await process.aclose()

    asyncio.run(run())
