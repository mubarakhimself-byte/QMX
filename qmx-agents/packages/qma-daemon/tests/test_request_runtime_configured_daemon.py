"""Operator config -> real paired socket -> HTTP inference -> scoped domain read."""

from __future__ import annotations

import asyncio
import json
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast

from qma.daemon.knowledge import KnowledgeService
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.wire.initialize import WIRE_PROTOCOL_VERSION
from test_request_runtime_daemon import receipt, rpc, value, ws_connect


@contextmanager
def inference_server(snapshot: str) -> Generator[tuple[str, list[dict[str, Any]]]]:
    calls: list[dict[str, Any]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            assert self.path == "/v1/chat/completions"
            body = cast(
                "dict[str, Any]", json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            )
            calls.append(body)
            context = json.loads(body["messages"][-1]["content"])
            observations = context["tool_observations"]
            action = (
                {
                    "type": "tool",
                    "tool": "research_browse",
                    "arguments": {"snapshot_ref": snapshot, "locator": "README.md"},
                }
                if not observations
                else {
                    "type": "final",
                    "content": "Pinned browse: "
                    + json.dumps(observations[-1]["result"], sort_keys=True),
                }
            )
            encoded = json.dumps(
                {
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": json.dumps(action)},
                            "finish_reason": "stop",
                        }
                    ]
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1/chat/completions", calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def discover(root: Path) -> tuple[str, str, str]:
    corpus = root / "corpus"
    corpus.mkdir()
    (corpus / "README.md").write_text("A permitted research hypothesis.", encoding="utf-8")
    (corpus / "IDEA.md").write_text("Other scoped document.", encoding="utf-8")
    process = value(
        DaemonProcess.compose(
            root,
            machine="configured-test",
            boot_epoch_id="discover",
            bind_port=0,
            plugin_load_configs=research_corpus_plugin_load_config(corpus),
        )
    )
    try:
        pack = process.roster.loader.get("research-corpus")
        assert pack is not None
        contribution = next(row.qualified_id for row in pack.published if row.point == "tool")
        assert contribution is not None
        snapshot = value(KnowledgeService(registry=process.roster.knowledge).snapshot("strats"))
        assert "README.md" in snapshot.file_digests and "IDEA.md" in snapshot.file_digests
        return pack.instance_id, contribution, snapshot.id
    finally:
        process.close()


def sdk_config(endpoint: str, instance: str, snapshot: str) -> dict[str, Any]:
    return {
        "enabled": True,
        "providers": {
            "local-proxy": {
                "protocol": "chat-completions",
                "endpoint": endpoint,
                "model": "offline-workhorse",
                "deployment_id": "fixture-http",
            }
        },
        "profiles": {
            "app-reader": {
                "role": "application",
                "authority_profile": "app-use",
                "app_instance_id": instance,
                "provider_id": "local-proxy",
                "tools": ["research_browse"],
            },
            "authoring": {
                "role": "global",
                "authority_profile": "authoring",
                "provider_id": "local-proxy",
                "tools": [],
            },
        },
        "instance_revisions": {instance: 1},
        "research_browse": {
            "source_id": "strats",
            "snapshot_ref": snapshot,
            "allowed_locators": ["README.md"],
        },
    }


def compose_configured(root: Path, config: dict[str, Any], boot: str) -> DaemonProcess:
    (root / "operator-config.json").write_text(
        json.dumps({"research_corpus_root_path": str(root / "corpus"), "agent_sdk": config}),
        encoding="utf-8",
    )
    return value(
        DaemonProcess.compose(
            root,
            machine="configured-test",
            boot_epoch_id=boot,
            bind_port=0,
            plugin_load_configs=research_corpus_plugin_load_config(root / "corpus"),
        )
    )


def app_session(process: DaemonProcess, instance: str, contribution: str) -> None:
    value(
        process.product_sessions.mint(
            product_session_id="psess:configured-app",
            profile="app-use",
            principal="operator",
            contribution={"qualified_id": contribution, "package_version": "0.1.0"},
            instance_id=instance,
            config_revision=1,
            as_of="2026-10-03T00:00:00Z",
        )
    )
    value(
        process.product_sessions.host_grant(
            "psess:configured-app",
            grant_id="grant:configured-browse",
            op_id="qml.research.browse",
            op_version=1,
            effect_class="read",
            parameter_ceiling={"allow_keys": ["snapshot_ref", "locator"]},
            expires_at="2099-01-01T00:00:00Z",
        )
    )


async def wait_result(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, request_id: str
) -> dict[str, object]:
    deadline = time.monotonic() + 5
    while True:
        row = receipt(
            await rpc(
                reader,
                writer,
                "get_agent_request",
                {"request_id": request_id, "product_session_ref": "psess:configured-app"},
            )
        )
        if row["status"] in {"completed", "failed", "interrupted", "cancelled"}:
            return row
        assert time.monotonic() < deadline, row
        await asyncio.sleep(0.01)


def test_configured_http_domain_request_over_authenticated_socket_and_restart(
    tmp_path: Path,
) -> None:
    instance, contribution, snapshot = discover(tmp_path)
    with inference_server(snapshot) as (endpoint, calls):
        config = sdk_config(endpoint, instance, snapshot)
        accepted_id = ""

        async def first() -> None:
            nonlocal accepted_id
            process = compose_configured(tmp_path, config, "configured-one")
            writer = None
            try:
                assert process.agent_requests is not None
                app_session(process, instance, contribution)
                value(await process.bind())
                reader, writer, opening = await ws_connect(process)
                assert b"101 Switching Protocols" in opening
                initialized = receipt(
                    await rpc(
                        reader,
                        writer,
                        "initialize",
                        {"protocolVersion": WIRE_PROTOCOL_VERSION, "capabilities": {}},
                    )
                )
                assert (
                    cast("dict[str, object]", initialized["capabilities"])["submit_agent_request"]
                    is True
                )
                params: dict[str, object] = {
                    "product_session_ref": "psess:configured-app",
                    "profile_id": "app-reader",
                    "prompt": "Browse the permitted pinned corpus metadata.",
                    "idempotency_key": "configured-one",
                }
                forbidden = await rpc(
                    reader, writer, "submit_agent_request", params | {"profile_id": "authoring"}
                )
                assert "error" in forbidden and len(calls) == 0
                accepted = receipt(await rpc(reader, writer, "submit_agent_request", params))
                accepted_id = cast("str", accepted["request_id"])
                completed = await wait_result(reader, writer, accepted_id)
                assert completed["status"] == "completed", completed
                assert "README.md" in cast("str", completed["content"])
                assert "IDEA.md" not in cast("str", completed["content"])
                assert len(calls) == 2
                assert all(call["model"] == "offline-workhorse" for call in calls)
                observation = json.loads(calls[1]["messages"][-1]["content"])["tool_observations"][
                    0
                ]
                assert observation["result"]["snapshot_ref"] == snapshot
                assert [item["locator"] for item in observation["result"]["items"]] == ["README.md"]
                assert process.sqlite_connection_count() == 1
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                await process.aclose()

        asyncio.run(first())
        # Narrow host context without changing the existing session's grant.
        config["research_browse"]["allowed_locators"] = ["IDEA.md"]

        async def after_restart() -> None:
            process = compose_configured(tmp_path, config, "configured-two")
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
                row = receipt(
                    await rpc(
                        reader,
                        writer,
                        "get_agent_request",
                        {"request_id": accepted_id, "product_session_ref": "psess:configured-app"},
                    )
                )
                assert row["status"] == "completed" and row["content_withheld"] is True
                assert "content" not in row and len(calls) == 2
                replay = await rpc(
                    reader,
                    writer,
                    "submit_agent_request",
                    {
                        "product_session_ref": "psess:configured-app",
                        "profile_id": "app-reader",
                        "prompt": "Browse the permitted pinned corpus metadata.",
                        "idempotency_key": "configured-one",
                    },
                )
                assert "error" in replay and len(calls) == 2
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                await process.aclose()

        asyncio.run(after_restart())
