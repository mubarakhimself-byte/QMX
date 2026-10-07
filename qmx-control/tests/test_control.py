from __future__ import annotations

import asyncio
import json
import secrets
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import httpx
import pytest
import uvicorn
from fastapi.testclient import TestClient
from fastmcp import Client

from qmx_control.server import OPERATIONS, create_app, create_mcp, local_token
from qmx_control.service import (
    ControlError,
    ControlService,
    LibraryInput,
    SessionBlock,
    SessionInput,
)

TOKEN = secrets.token_urlsafe(32)
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def test_rest_mcp_parity_and_openapi(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    service.library_save(LibraryInput(title="Research", kind="note", content={"text": "rates"}))
    session = service.sessions_create(SessionInput(title="Overnight"))
    service.sessions_append(str(session["id"]), SessionBlock(type="text", content={"text": "done"}))
    service.record_work("runs", "run-1", {"status": "running"})
    service.record_work("jobs", "job-1", {"status": "complete"})
    service.settings_put("budgets", {"model_calls": 10})
    cases: list[tuple[str, str, dict[str, Any]]] = [
        ("library_search", "/api/library?query=rates", {"query": "rates"}),
        ("sessions_list", "/api/sessions", {}),
        ("runs_list", "/api/runs", {}),
        ("jobs_list", "/api/jobs", {}),
        ("settings_get", "/api/settings/budgets", {"section": "budgets"}),
        ("sessions_stream", f"/api/sessions/{session['id']}/events", {"session_id": session["id"]}),
    ]

    async def compare() -> None:
        async with Client(create_mcp(service)) as mcp:
            with TestClient(create_app(service, TOKEN)) as rest:
                for name, url, args in cases:
                    response = rest.get(url, headers=HEADERS)
                    assert response.status_code == 200
                    result = await mcp.call_tool(name, args)
                    assert result.data == response.json()
                values = {"model_calls": 25}
                written = rest.put("/api/settings/budgets", headers=HEADERS, json=values)
                assert (
                    await mcp.call_tool("settings_put", {"section": "budgets", "values": values})
                ).data == written.json()
                tools = {tool.name: tool for tool in await mcp.list_tools()}
                assert tools["apps_publish"].annotations is not None
                assert tools["apps_publish"].annotations.model_dump(by_alias=True)[
                    "destructiveHint"
                ]
                assert tools["apps_stop"].meta is not None
                assert tools["apps_stop"].meta["interrupt_on"] is True
                schema = rest.get("/openapi.json", headers=HEADERS).json()
                ids = {
                    op["operationId"] for path in schema["paths"].values() for op in path.values()
                }
                assert {entry[0] for entry in OPERATIONS} <= ids
                assert "HTTPBearer" in schema["components"]["securitySchemes"]

    asyncio.run(compare())


def test_writes_persist_and_errors_are_clear(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    with TestClient(create_app(service, TOKEN)) as rest:
        session = rest.post("/api/sessions", headers=HEADERS, json={"title": "Long session"}).json()
        response = rest.post(
            f"/api/sessions/{session['id']}/blocks",
            headers=HEADERS,
            json={"type": "user", "content": {"text": "hello"}},
        )
        assert response.json()["seq"] == 1
        assert (
            rest.post(
                f"/api/sessions/{session['id']}/blocks",
                headers=HEADERS,
                json={"type": "made_up", "content": {}},
            ).status_code
            == 422
        )
        assert (
            rest.put(
                "/api/settings/providers",
                headers=HEADERS,
                json={"proxy": {"credential_ref": "qmx/proxy"}},
            ).status_code
            == 200
        )
        assert (
            rest.put(
                "/api/settings/providers",
                headers=HEADERS,
                json={"proxy": {"api_key": "do-not-save"}},
            ).status_code
            == 400
        )
        response = rest.get("/api/apps", headers=HEADERS)
        assert response.status_code == 501
        assert response.json()["error"]["code"] == "not_implemented"
    reopened = ControlService(tmp_path)
    assert reopened.sessions_list()[0] == session
    assert reopened.sessions_stream(session["id"])[-1]["data"] == {
        "type": "block",
        "block": {"seq": 1, "type": "user", "content": {"text": "hello"}},
    }
    assert "do-not-save" not in (tmp_path / "settings.toml").read_text()

    async def unavailable() -> None:
        async with Client(create_mcp(reopened)) as mcp:
            result = await mcp.call_tool("apps_list", raise_on_error=False)
            assert result.is_error
            assert "not_implemented" in str(result.content)

    asyncio.run(unavailable())


def test_unavailable_errors_match_across_doors(tmp_path: Path) -> None:
    service = ControlService(tmp_path)

    async def compare() -> None:
        with TestClient(create_app(service, TOKEN)) as rest:
            async with Client(create_mcp(service)) as mcp:
                for name, method, route, _ in OPERATIONS:
                    if not name.startswith(("apps_", "workflows_")):
                        continue
                    args: dict[str, Any] = {}
                    path = route
                    if "{app_id}" in path:
                        args["app_id"] = "missing-app"
                        path = path.replace("{app_id}", "missing-app")
                    if "{workflow_id}" in path:
                        args["workflow_id"] = "missing-workflow"
                        path = path.replace("{workflow_id}", "missing-workflow")
                    params: dict[str, str] = {}
                    body = None
                    if name in {"apps_create", "apps_update"}:
                        args["path"] = "uninstalled"
                        params["path"] = "uninstalled"
                    if name in {"workflows_put", "workflows_validate"}:
                        args["graph"] = {}
                        body = {}
                    response = rest.request(method, path, headers=HEADERS, params=params, json=body)
                    assert response.status_code == 501, (name, response.text)
                    result = await mcp.call_tool(name, args, raise_on_error=False)
                    assert result.is_error
                    assert json.loads(result.content[0].model_dump()["text"]) == response.json()

    asyncio.run(compare())


@pytest.mark.parametrize("path", ["/api/sessions", "/openapi.json", "/mcp/", "/api/events/runs"])
def test_auth_required(tmp_path: Path, path: str) -> None:
    with TestClient(create_app(ControlService(tmp_path), TOKEN)) as client:
        assert client.get(path).status_code == 401
        assert client.get(path, headers={"Authorization": "Bearer wrong"}).status_code == 401


def test_cors_and_token_created_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    saved: dict[tuple[str, str], str] = {}

    def get_password(service: str, username: str) -> str | None:
        return saved.get((service, username))

    def set_password(service: str, username: str, password: str) -> None:
        saved[service, username] = password

    monkeypatch.setattr(
        "qmx_control.server.keyring.get_password",
        get_password,
    )
    monkeypatch.setattr(
        "qmx_control.server.keyring.set_password",
        set_password,
    )
    assert local_token() == local_token()
    assert list(saved) == [("qmx/control-token", "control-token")]
    with TestClient(create_app(ControlService(tmp_path), TOKEN, "http://localhost:5000")) as client:
        allowed = client.options(
            "/api/sessions",
            headers={
                "Origin": "http://localhost:5000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        assert allowed.headers["access-control-allow-origin"] == "http://localhost:5000"
        assert (
            client.options(
                "/api/sessions",
                headers={
                    "Origin": "https://elsewhere.example",
                    "Access-Control-Request-Method": "POST",
                },
            ).status_code
            == 400
        )


def test_sse_replay_for_each_topic(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    session = service.sessions_create(SessionInput(title="SSE"))
    cursor = service.events("sessions")[-1]["id"]
    service.sessions_append(
        str(session["id"]), SessionBlock(type="text", content={"text": "reply"})
    )
    service.record_work("runs", "r1", {"status": "complete"})
    service.record_work("jobs", "j1", {"status": "failed"})
    with TestClient(create_app(service, TOKEN)) as client:
        for topic in ("runs", "jobs", "sessions"):
            headers = {**HEADERS, "Last-Event-ID": str(cursor if topic == "sessions" else 0)}
            response = client.get(f"/api/events/{topic}?max_events=1", headers=headers)
            assert response.headers["content-type"].startswith("text/event-stream")
            assert f"event: {topic}" in response.text
            assert "data:" in response.text
            if topic == "sessions":
                assert "reply" in response.text
                assert "created" not in response.text
        assert (
            client.get("/api/events/runs", headers={**HEADERS, "Last-Event-ID": "bad"}).status_code
            == 422
        )


def test_append_is_serialized_and_cancellation_is_honest(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    session = service.sessions_create(SessionInput(title="Concurrency"))

    def append(index: int) -> int:
        return int(
            str(
                service.sessions_append(
                    str(session["id"]), SessionBlock(type="text", content={"index": index})
                )["seq"]
            )
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(append, range(20))) == list(range(1, 21))
    service.record_work("runs", "r1", {"status": "running"})
    with pytest.raises(ControlError, match="not available"):
        service.runs_cancel("r1")
    assert service.runs_list()[0]["status"] == "running"
    with pytest.raises(ControlError, match="Unknown"):
        service.jobs_cancel("missing")


def test_mcp_over_authenticated_http(tmp_path: Path) -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(ControlService(tmp_path), TOKEN),
            host="127.0.0.1",
            port=port,
            log_level="error",
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        for _ in range(100):
            if server.started:
                break
            time.sleep(0.05)
        assert server.started
        url = f"http://127.0.0.1:{port}/mcp/"
        assert httpx.post(url).status_code == 401

        async def call() -> None:
            async with Client(url, auth=TOKEN) as client:
                result = await client.call_tool(
                    "sessions_create", {"session": {"title": "HTTP MCP"}}
                )
                assert json.loads(json.dumps(result.data))["title"] == "HTTP MCP"

        asyncio.run(call())

        subscribed = threading.Event()

        def receive_event() -> str:
            with httpx.stream(
                "GET",
                f"http://127.0.0.1:{port}/api/events/jobs?max_events=1",
                headers=HEADERS,
                timeout=10,
            ) as response:
                assert response.status_code == 200
                subscribed.set()
                return "\n".join(response.iter_lines())

        with ThreadPoolExecutor(max_workers=1) as pool:
            event = pool.submit(receive_event)
            assert subscribed.wait(timeout=10)
            ControlService(tmp_path).record_work("jobs", "live-job", {"status": "complete"})
            assert '"status": "complete"' in event.result(timeout=10)
    finally:
        server.should_exit = True
        thread.join(timeout=10)
    assert not thread.is_alive()
