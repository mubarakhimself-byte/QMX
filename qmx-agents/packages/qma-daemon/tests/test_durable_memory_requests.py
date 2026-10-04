"""Configured daemon and paired socket exercise typed memory across fresh jobs."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from qma.wire.initialize import WIRE_PROTOCOL_VERSION
from test_agent_extensions_daemon import offline
from test_request_runtime_configured_daemon import (
    app_session,
    compose_configured,
    discover,
    sdk_config,
    wait_result,
)
from test_request_runtime_daemon import receipt, rpc, value, ws_connect
from test_request_runtime_tool_loop import ScriptedText


def test_paired_request_fresh_job_recall_and_disk_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    instance, contribution, snapshot = discover(tmp_path)
    config = sdk_config("http://127.0.0.1:9876/v1/chat/completions", instance, snapshot)
    config["research_workflow"] = {
        "specialist_id": "memory-analyst",
        "version": "1",
        "instructions": "Analyze supplied synthetic evidence only.",
        "profiles": ["app-reader"],
    }
    scripted = ScriptedText(
        [json.dumps({"type": "final", "content": f"Synthetic summary {i}"}) for i in range(3)]
    )
    offline(monkeypatch, scripted)
    request_ids: list[str] = []

    async def run(boot: str, first: bool) -> None:
        process = compose_configured(tmp_path, config, boot)
        writer = None
        try:
            if first:
                app_session(process, instance, contribution)
            value(await process.bind())
            reader, writer, opening = await ws_connect(process)
            assert b"101 Switching Protocols" in opening
            receipt(
                await rpc(
                    reader,
                    writer,
                    "initialize",
                    {
                        "protocolVersion": WIRE_PROTOCOL_VERSION,
                        "capabilities": {},
                    },
                )
            )
            for key in ["one", "two"] if first else ["three"]:
                accepted = receipt(
                    await rpc(
                        reader,
                        writer,
                        "submit_agent_request",
                        {
                            "product_session_ref": "psess:configured-app",
                            "profile_id": "app-reader",
                            "prompt": "Analyze the pinned permitted corpus.",
                            "idempotency_key": key,
                        },
                    )
                )
                request_id = str(accepted["request_id"])
                request_ids.append(request_id)
                result = await wait_result(reader, writer, request_id)
                assert result["status"] == "completed", result
            events = value(process.journal.read_events())
            state = next(
                json.loads(str(e.payload["body"]))
                for e in reversed(events)
                if e.event == "agent_graph.record" and e.payload.get("kind") == "typed_memory"
            )
            assert state["revisions"][0]["provenance"]["locators"] == ["README.md"]
            if not first:
                assert [
                    r["validation_state"]
                    for r in state["revisions"]
                    if r["id"] == request_ids[0] + ":summary"
                ] == ["admitted", "superseded"]
                before = len(scripted.requests)
                replay = receipt(
                    await rpc(
                        reader,
                        writer,
                        "get_agent_request",
                        {
                            "product_session_ref": "psess:configured-app",
                            "request_id": request_ids[0],
                        },
                    )
                )
                assert replay["status"] == "completed" and len(scripted.requests) == before
        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()
            await process.aclose()

    asyncio.run(run("memory-one", True))
    asyncio.run(run("memory-two", False))
    assert len(scripted.requests) == 3
    inputs = [
        json.loads(json.loads(request.prompt)["user_request"]) for request in scripted.requests
    ]
    assert inputs[0]["scoped_memory"] is None
    assert inputs[1]["scoped_memory"]["request_id"] == request_ids[0]
    assert inputs[2]["scoped_memory"]["request_id"] == request_ids[1]
    assert inputs[2]["scoped_memory"]["memory_type"] == "summary"
    assert "Other scoped document" not in repr(inputs)
