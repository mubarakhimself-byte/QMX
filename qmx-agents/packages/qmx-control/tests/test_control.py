from __future__ import annotations

import asyncio
import json
import os
import secrets
import socket
import threading
import time
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import httpx
import keyring
import pytest
import uvicorn
from fastapi import APIRouter
from fastapi.testclient import TestClient
from fastmcp import Client
from keyring.backend import KeyringBackend
from keyring.backends import fail, null

from qmx_control.catalog import control_rows, rest_routes
from qmx_control.server import create_app, create_mcp, local_token
from qmx_control.service import (
    ControlError,
    ControlService,
    LibraryInput,
    SessionBlock,
    SessionInput,
)

TOKEN = secrets.token_urlsafe(32)
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def test_firecrawl_settings_are_off_by_default_and_persist_only_a_vault_reference(
    tmp_path: Path,
) -> None:
    service = ControlService(tmp_path)
    default = service.settings_get("mcp_servers")["firecrawl"]
    assert isinstance(default, dict)
    assert default == {
        "url": "https://mcp.firecrawl.dev/v2/mcp",
        "enabled": False,
        "credential_ref": "qmx/firecrawl",
    }
    values = {"firecrawl": {**default, "enabled": True}}
    with TestClient(create_app(service, TOKEN)) as rest:
        assert (
            rest.put("/api/settings/mcp_servers", headers=HEADERS, json=values).status_code == 200
        )
        assert rest.get("/api/settings/mcp_servers", headers=HEADERS).json() == {
            **values,
            "ctrader": CTRADER_OFF,
        }
        for invalid in (
            {"api_key": "do-not-save"},
            {"auth": "do-not-save"},
            {"url": "https://host/?key=do-not-save"},
            {"url": "http://host"},
            {"url": "https://["},
            {"enabled": "true"},
            {"credential_ref": "qmx/other"},
        ):
            assert (
                rest.put(
                    "/api/settings/mcp_servers", headers=HEADERS, json={"firecrawl": invalid}
                ).status_code
                == 400
            )
    assert ControlService(tmp_path).settings_get("mcp_servers") == {
        **values,
        "ctrader": CTRADER_OFF,
    }
    assert "do-not-save" not in (tmp_path / "settings.toml").read_text()


CTRADER_OFF = {"enabled": False, "credential_ref": "qmx/ctrader-mcp", "venue": "ctrader"}


def test_the_ctrader_mcp_row_ships_off_and_keeps_its_vault_reference_and_venue(
    tmp_path: Path,
) -> None:
    service = ControlService(tmp_path)
    assert service.settings_get("mcp_servers")["ctrader"] == CTRADER_OFF
    pasted = {"url": "https://mcp.ctrader.test/remote/mcp", "enabled": True}
    service.settings_put("mcp_servers", {"ctrader": pasted})
    assert service.settings_get("mcp_servers")["ctrader"] == {**CTRADER_OFF, **pasted}
    for invalid, code in (
        ({"venue": "mt5"}, "invalid_settings"),
        ({"credential_ref": "qmx/other"}, "invalid_settings"),
        ({"url": "http://mcp.ctrader.test/mcp"}, "invalid_settings"),
        ({"url": "https://mcp.ctrader.test/mcp?key=do-not-save"}, "invalid_settings"),
        ({"enabled": "true"}, "invalid_settings"),
        ({"token": "do-not-save"}, "secret_ref_required"),
    ):
        with pytest.raises(ControlError) as refused:
            service.settings_put("mcp_servers", {"ctrader": invalid})
        assert refused.value.code == code
    service.settings_put("mcp_servers", {"ctrader": {"url": "http://127.0.0.1:8123/mcp"}})
    assert service.settings_get("mcp_servers")["ctrader"]["url"] == "http://127.0.0.1:8123/mcp"
    assert "do-not-save" not in (tmp_path / "settings.toml").read_text()


def test_telemetry_send_to_is_edited_from_settings(tmp_path: Path) -> None:
    with TestClient(create_app(ControlService(tmp_path), TOKEN)) as rest:
        fresh = rest.get("/api/settings/telemetry", headers=HEADERS).json()
        named = rest.put("/api/settings/telemetry", headers=HEADERS, json={"send_to": "this-pc"})
        stored = rest.get("/api/settings/telemetry", headers=HEADERS).json()

    sizes = {"cache_gb": 1, "keep_days": 30}
    assert (fresh, named.status_code, stored) == (
        {"send_to": "off", "openobserve": sizes},
        200,
        {"send_to": "this-pc", "openobserve": sizes},
    )
    assert '[telemetry]\nsend_to = "this-pc"' in (tmp_path / "settings.toml").read_text()


def test_rest_mcp_parity_and_openapi(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    service.library_save(LibraryInput(title="Research", kind="note", content={"text": "rates"}))
    session = service.sessions_create(SessionInput(title="Overnight"))
    service.sessions_append(str(session["id"]), SessionBlock(type="text", content={"text": "done"}))
    service.settings_put("budgets", {"model_calls": 10})
    cases: list[tuple[str, str, dict[str, Any]]] = [
        ("library_search", "/api/library?query=rates", {"query": "rates"}),
        ("ops_sessions", "/api/sessions", {}),
        ("settings_read_get", "/api/settings/budgets", {"section": "budgets"}),
        (
            "ops_sessions_stream",
            f"/api/sessions/{session['id']}/events",
            {"session_id": session["id"]},
        ),
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
                    await mcp.call_tool(
                        "settings_read_put", {"section": "budgets", "values": values}
                    )
                ).data == written.json()
                tools = {tool.name: tool for tool in await mcp.list_tools()}
                assert tools["apps_admin_publish"].annotations is not None
                assert tools["apps_admin_publish"].annotations.model_dump(by_alias=True)[
                    "destructiveHint"
                ]
                assert tools["apps_admin_stop"].meta is not None
                assert tools["apps_admin_stop"].meta["interrupt_on"] is True
                schema = rest.get("/openapi.json", headers=HEADERS).json()
                ids = {
                    op["operationId"] for path in schema["paths"].values() for op in path.values()
                }
                assert {row.name for row in control_rows()} <= ids
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
        response = rest.post("/api/apps/missing/test", headers=HEADERS)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "not_found"
    reopened = ControlService(tmp_path)
    assert reopened.sessions_list()[0] == session
    assert reopened.sessions_stream(session["id"])[-1]["data"] == {
        "type": "block",
        "block": {"seq": 1, "type": "user", "content": {"text": "hello"}},
    }
    assert "do-not-save" not in (tmp_path / "settings.toml").read_text()

    async def unavailable() -> None:
        async with Client(create_mcp(reopened)) as mcp:
            result = await mcp.call_tool(
                "apps_admin_test", {"app_id": "missing"}, raise_on_error=False
            )
            assert result.is_error
            assert "not_found" in str(result.content)

    asyncio.run(unavailable())


def test_unavailable_errors_match_across_doors(tmp_path: Path) -> None:
    service = ControlService(tmp_path)

    async def compare() -> None:
        with TestClient(create_app(service, TOKEN)) as rest:
            async with Client(create_mcp(service)) as mcp:
                for row, door in rest_routes(control_rows()):
                    name, method, route = row.name, door.verb, door.path
                    if name not in {
                        "apps_admin_test",
                        "apps_admin_publish",
                        "apps_admin_evidence",
                    } and not row.target.startswith("workflows_"):
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
                    if name in {"apps_admin_create", "apps_admin_update"}:
                        args["path"] = "uninstalled"
                        params["path"] = "uninstalled"
                    if name in {"workflows_put", "workflows_validate"}:
                        args["graph"] = {}
                        body = {}
                    response = rest.request(method, path, headers=HEADERS, params=params, json=body)
                    assert response.status_code == (404 if name.startswith("apps_") else 501), (
                        name,
                        response.text,
                    )
                    result = await mcp.call_tool(name, args, raise_on_error=False)
                    assert result.is_error
                    assert json.loads(result.content[0].model_dump()["text"]) == response.json()

    asyncio.run(compare())


@pytest.mark.parametrize("path", ["/api/sessions", "/openapi.json", "/mcp/", "/api/events/runs"])
def test_auth_required(tmp_path: Path, path: str) -> None:
    with TestClient(create_app(ControlService(tmp_path), TOKEN)) as client:
        assert client.get(path).status_code == 401
        assert client.get(path, headers={"Authorization": "Bearer wrong"}).status_code == 401


class MemoryKeyring(KeyringBackend):
    """An OS keyring that lives in this test only."""

    def __init__(self) -> None:
        super().__init__()
        self.saved: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.saved.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.saved[service, username] = password

    def delete_password(self, service: str, username: str) -> None:
        self.saved.pop((service, username), None)


@contextmanager
def os_keyring(backend: KeyringBackend) -> Generator[None]:
    before = keyring.get_keyring()
    keyring.set_keyring(backend)
    try:
        yield
    finally:
        keyring.set_keyring(before)


@pytest.mark.skipif(os.name == "nt", reason="a Windows PC always has Credential Manager")
@pytest.mark.parametrize("missing", [fail.Keyring, null.Keyring])
def test_local_token_uses_the_home_file_without_a_keyring(
    tmp_path: Path, missing: type[KeyringBackend]
) -> None:
    home = tmp_path / "QMX" / "data"
    token = tmp_path / "QMX" / "keys" / "control-token"
    with os_keyring(missing()):
        made = local_token(home, create=True)
        again = local_token(home)
        with pytest.raises(RuntimeError, match=r"^No control token at .*elsewhere"):
            local_token(tmp_path / "elsewhere" / "data")
        mode = token.stat().st_mode & 0o777
        token.chmod(0o640)
        with pytest.raises(PermissionError, match="can be read by other users"):
            local_token(home)

    assert (again, mode, len(made)) == (made, 0o600, 43)
    assert not (tmp_path / "elsewhere").exists()


@pytest.mark.skipif(os.name != "nt", reason="the refusal is Windows' own")
def test_a_windows_pc_without_its_credential_store_is_refused_by_name(tmp_path: Path) -> None:
    with os_keyring(fail.Keyring()), pytest.raises(RuntimeError) as refused:
        local_token(tmp_path, create=True)

    assert str(refused.value) == (
        "Windows Credential Manager is not answering, so QMX cannot read its control token."
    )
    assert list(tmp_path.iterdir()) == []


def test_cors_and_token_created_once(tmp_path: Path) -> None:
    memory = MemoryKeyring()
    with os_keyring(memory):
        assert local_token(tmp_path, create=True) == local_token()
    assert list(memory.saved) == [("qmx/control-token", "control-token")]
    assert list(tmp_path.iterdir()) == []
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
    service.notify_app("exchange-status", {"status": "running"})
    with TestClient(create_app(service, TOKEN)) as client:
        for topic in ("apps", "sessions"):
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


def test_append_is_serialized(tmp_path: Path) -> None:
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
                    "ops_sessions_create", {"session": {"title": "HTTP MCP"}}
                )
                assert json.loads(json.dumps(result.data))["title"] == "HTTP MCP"
                saved = await client.call_tool(
                    "library_save",
                    {
                        "item": {
                            "title": "HTTP strategy",
                            "kind": "strategy",
                            "tags": ["macro"],
                            "content": {"lookback": 20},
                        }
                    },
                )
                item = json.loads(json.dumps(saved.data))
                fetched = httpx.get(
                    f"http://127.0.0.1:{port}/api/library/{item['id']}", headers=HEADERS, timeout=10
                )
                assert fetched.status_code == 200
                assert fetched.json() == item
                versions = await client.call_tool("library_versions", {"artifact_id": item["id"]})
                assert json.loads(json.dumps(versions.data)) == [item]
                searched = httpx.get(
                    f"http://127.0.0.1:{port}/api/library?query=macro", headers=HEADERS, timeout=10
                )
                assert searched.json() == [item]
                aggregate = httpx.get(
                    f"http://127.0.0.1:{port}/api/aggregates", headers=HEADERS, timeout=10
                )
                assert aggregate.json()["library_items"] == 1
                pushed = httpx.get(
                    f"http://127.0.0.1:{port}/api/events/aggregates?max_events=1",
                    headers=HEADERS,
                    timeout=10,
                )
                assert "event: aggregates" in pushed.text
                assert '"library_items": 1' in pushed.text

        asyncio.run(call())

        subscribed = threading.Event()

        def receive_event() -> str:
            with httpx.stream(
                "GET",
                f"http://127.0.0.1:{port}/api/events/apps?max_events=1",
                headers=HEADERS,
                timeout=10,
            ) as response:
                assert response.status_code == 200
                subscribed.set()
                return "\n".join(response.iter_lines())

        with ThreadPoolExecutor(max_workers=1) as pool:
            event = pool.submit(receive_event)
            assert subscribed.wait(timeout=10)
            ControlService(tmp_path).notify_app("exchange-status", {"status": "stopped"})
            assert '"status": "stopped"' in event.result(timeout=10)
    finally:
        server.should_exit = True
        thread.join(timeout=10)
    assert not thread.is_alive()


def test_host_sections_are_written_only_through_a_registered_parser(tmp_path: Path) -> None:
    bare = ControlService(tmp_path / "bare")
    with pytest.raises(ControlError, match="written only by the QMA host"):
        bare.settings_put("environment", {"keep": ["JAVA_HOME"]})
    assert not (tmp_path / "bare" / "settings.toml").exists()

    hosted = ControlService(
        tmp_path / "hosted",
        settings_parsers={"environment": lambda values, current: {"keep": ["JAVA_HOME"]}},
    )
    assert hosted.settings_put("environment", {"keep": ["java_home"]}) == {"keep": ["JAVA_HOME"]}
    assert hosted.settings_get("environment") == {"keep": ["JAVA_HOME"]}
    with pytest.raises(ControlError, match="written only by the QMA host"):
        hosted.settings_put("claude", {})


def test_extra_routers_sit_behind_the_bearer(tmp_path: Path) -> None:
    extra = APIRouter()

    @extra.get("/api/extra")
    async def read_extra() -> dict[str, str]:
        return {"extra": "yes"}

    _ = read_extra
    with TestClient(create_app(ControlService(tmp_path), TOKEN, extra_routers=[extra])) as rest:
        assert rest.get("/api/extra").status_code == 401
        assert rest.get("/api/extra", headers=HEADERS).json() == {"extra": "yes"}
