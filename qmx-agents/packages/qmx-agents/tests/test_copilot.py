from __future__ import annotations

import asyncio
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import httpx
import pytest
from conftest import fake
from deepagents.backends import StateBackend
from deepagents.backends.protocol import ExecuteResponse, SandboxBackendProtocol
from fastmcp import Client
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from qmx_apps.manifest import Definition
from qmx_apps.supervisor import Supervisor
from qmx_control.models import Document
from qmx_control.server import create_app
from qmx_control.service import ControlService, SessionInput
from test_spec import call

from qmx_agents.copilot import build_copilot, stream_turn
from qmx_agents.router import ModelRouter, RouterConfig, RunContext
from qmx_agents.spec import BuildContext, load_spec
from qmx_agents.tasks import BackgroundTasks

ROOT = Path(__file__).resolve().parents[4]
APP = ROOT / "examples/apps/macro-daily-bias"


class FakeSandbox(StateBackend, SandboxBackendProtocol):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[str] = []

    @property
    def id(self) -> str:
        return "fake-python"

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        self.calls.append(command)
        return ExecuteResponse(output="recorded Python result", exit_code=0)


class FakeRuntime(Supervisor):
    """Keep the real immutable definitions and road; fake dependency installs and processes."""

    running: str | None = None

    def _install_environment(self, definition: Definition, image: Path) -> None:
        pass

    def start(self, app_id: str, *, definition_hash: str | None = None) -> Document:
        self.running = definition_hash
        return self.status(app_id)

    def status(self, app_id: str) -> Document:
        return {"status": "running" if self.running else "stopped", "definition_hash": self.running}


def models(config: RouterConfig, model: BaseChatModel) -> ModelRouter:
    return ModelRouter(config, dict.fromkeys(config.profiles["daily"].values(), model))


def test_copilot_build_tests_publish_interrupt_and_session_sse(
    tmp_path: Path,
    config: RouterConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = tmp_path / "candidate"
    shutil.copytree(APP, candidate)
    image = Definition.load(candidate)
    owner = FakeRuntime(tmp_path / "home")
    service = ControlService(owner.home)
    monkeypatch.setattr(service, "_apps", owner)

    # The user excludes real servers. These are explicitly fake proof runners;
    # real road currentness, stage ordering and publication CAS are still exercised.
    def validate(*args: Any) -> tuple[Document, Document]:
        return {"fixture": True}, {"passed": True, "tests_run": 1}

    monkeypatch.setattr("qmx_apps.road.validate", validate)
    session_id = str(service.sessions_create(SessionInput(title="Macro"))["id"])
    scripted = fake(
        call("write_todos", {"todos": [{"content": "Build macro app", "status": "in_progress"}]}),
        call("apps_create", {"path": str(candidate), "trust": "reviewed"}),
        call("apps_test", {"app_id": "macro-daily-bias", "stage": "sandbox", "auto_publish": True}),
        call("apps_test", {"app_id": "macro-daily-bias", "stage": "shadow", "auto_publish": True}),
        call(
            "sessions_append",
            {
                "session_id": session_id,
                "block": {
                    "type": "question",
                    "content": {"text": "Use the default daily interval?"},
                },
            },
        ),
        call(
            "sessions_append",
            {
                "session_id": session_id,
                "block": {
                    "type": "panel",
                    "content": {
                        "app_id": "macro-daily-bias",
                        "resource_uri": "ui://macro-daily-bias/view.html",
                        "state": "draft",
                    },
                },
            },
        ),
        call(
            "sessions_append",
            {
                "session_id": session_id,
                "block": {
                    "type": "artifact",
                    "content": {"app_id": "macro-daily-bias", "definition_hash": image.hash},
                },
            },
        ),
        call("apps_publish", {"app_id": "macro-daily-bias", "expected_hash": image.hash}),
        "Macro daily bias is live.",
    )

    async def run() -> None:
        ctx = BuildContext(
            models(config, scripted),
            run=RunContext(session_id=session_id),
            control=service,
            qmx_home=service.home,
            checkpointer=InMemorySaver(),
            agent_backends={"data-analyst": FakeSandbox()},
        )
        try:
            graph = await build_copilot(ctx)
            await stream_turn(graph, service, session_id, "Build Macro daily bias", context=ctx.run)
            assert owner.running is None
            assert service.apps_get("macro-daily-bias")["road"] == {
                "stage": "shadow",
                "active": None,
            }
            state = await graph.aget_state({"configurable": {"thread_id": session_id}})
            assert (
                state.tasks[0].interrupts[0].value["action_requests"][0]["name"] == "apps_publish"
            )
            await stream_turn(
                graph,
                service,
                session_id,
                Command(resume={"decisions": [{"type": "approve"}]}),
                context=ctx.run,
            )
            assert owner.running == image.hash
            evidence = service.apps_evidence("macro-daily-bias")
            assert [row["stage"] for row in evidence] == [
                "build",
                "tests",
                "sandbox",
                "shadow",
                "live",
            ]
            events = service.sessions_stream(session_id, limit=1000)
            types = {
                str(cast(Document, cast(Document, event["data"])["block"])["type"])
                for event in events
                if cast(Document, event["data"])["type"] == "block"
            }
            assert {
                "user",
                "text",
                "plan",
                "tool",
                "question",
                "permission",
                "panel",
                "artifact",
            } <= types
            auth_value = uuid4().hex
            app = create_app(service, token=auth_value)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
                headers={"Authorization": f"Bearer {auth_value}"},
            ) as client:
                response = await client.get(
                    f"/api/events/sessions?subject={session_id}&max_events={len(events)}"
                )
                assert response.status_code == 200
                assert response.headers["content-type"].startswith("text/event-stream")
                streamed = [
                    json.loads(line[6:])
                    for line in response.text.splitlines()
                    if line.startswith("data: ")
                ]
                streamed_types = {
                    event["block"]["type"] for event in streamed if event["type"] == "block"
                }
                assert {"permission", "panel"} <= streamed_types
        finally:
            await ctx.close_memory()
            service.close()

    asyncio.run(run())


@pytest.mark.parametrize("approved", [False, True])
def test_global_write_interrupt_reject_then_approve(
    tmp_path: Path, config: RouterConfig, approved: bool
) -> None:
    service = ControlService(tmp_path)
    session_id = str(service.sessions_create(SessionInput(title="Memory"))["id"])
    model = fake(call("memory_put_global", {"content": "Prefer daily summaries"}), "done")

    async def run() -> None:
        ctx = BuildContext(
            models(config, model),
            run=RunContext(session_id=session_id),
            control=service,
            qmx_home=tmp_path,
            checkpointer=InMemorySaver(),
            agent_backends={"data-analyst": FakeSandbox()},
        )
        try:
            graph = await build_copilot(ctx)
            await stream_turn(graph, service, session_id, "Remember globally", context=ctx.run)
            state = await graph.aget_state({"configurable": {"thread_id": session_id}})
            assert state.tasks[0].interrupts[0].value["kind"] == "global_memory"
            await stream_turn(graph, service, session_id, Command(resume=approved), context=ctx.run)
            from qmx_agents.memory import Scope

            assert ctx.memory is not None
            assert [row.content for row in await ctx.memory.builtin.search([Scope.GLOBAL])] == (
                ["Prefer daily summaries"] if approved else []
            )
        finally:
            await ctx.close_memory()
            service.close()

    asyncio.run(run())


def test_named_delegation_and_background_run(tmp_path: Path, config: RouterConfig) -> None:
    service = ControlService(tmp_path)
    session_id = str(service.sessions_create(SessionInput(title="Research"))["id"])
    model = fake(
        call("task", {"subagent_type": "researcher", "description": "Research coverage"}),
        "Coverage missing",
        "Research complete",
    )

    async def run() -> None:
        ctx = BuildContext(
            models(config, model),
            run=RunContext(session_id=session_id),
            control=service,
            qmx_home=tmp_path,
            checkpointer=InMemorySaver(),
            agent_backends={"data-analyst": FakeSandbox()},
        )
        try:
            graph = await build_copilot(ctx)
            await stream_turn(graph, service, session_id, "Research", context=ctx.run)
            assert any(row["parent_id"] == session_id for row in service.sessions_list())
            tasks = cast(BackgroundTasks, ctx.background_resources[0])
            ctx.router = models(config, fake("Built artifact /artifacts/draft"))
            tools = {tool.name: tool for tool in tasks.tools()}
            result = await tools["start_task"].ainvoke(
                {"name": "overnight-builder", "description": "Build overnight"}
            )
            await tasks.running[result["id"]]
            assert service.runs_get(result["id"])["status"] == "completed"
            assert service.runs_get(result["id"])["model"]
            assert list((tmp_path / "copilot/tasks").glob("*/threads.db"))
            assert (await tools["list_tasks"].ainvoke({}))[0]["id"] == result["id"]
            cancelled = await tools["start_task"].ainvoke(
                {"name": "overnight-builder", "description": "Cancel before work"}
            )
            tasks.running[cancelled["id"]].cancel()
            await asyncio.gather(tasks.running[cancelled["id"]], return_exceptions=True)
            assert (await tools["check_task"].ainvoke({"run_id": cancelled["id"]}))[
                "status"
            ] == "cancelled"
        finally:
            await ctx.close_memory()
            service.close()

    asyncio.run(run())


def test_macro_agent_data_and_panel_persist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = importlib.util.spec_from_file_location("macro_bias", APP / "macro_bias.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["macro_bias"] = module
    spec.loader.exec_module(module)
    monkeypatch.setenv("QMX_STAGE", "sandbox")

    async def run() -> None:
        payload = await module.refresh(tmp_path)
        assert payload["bias"] == "neutral" and payload["source"] == "recorded"
        assert module.latest(tmp_path) == payload
        async with Client(module.create_server(tmp_path)) as client:
            response = await client.call_tool("bias", {})
            assert response.structured_content is not None
            assert response.structured_content["data"] == payload
            resources = await client.read_resource(module.VIEW)
            assert hasattr(resources[0], "text")
            assert "coverage" in cast(Any, resources[0]).text
            assert "neutral" in cast(Any, resources[0]).text

    asyncio.run(run())


def test_copilot_spec_and_sandbox_requirement(tmp_path: Path, config: RouterConfig) -> None:
    spec = load_spec()
    assert {"qmx-control", "qmx-data", "qmx-backtest", "qmx-research", "qmx-broker"} == set(
        spec.mcp_servers
    )
    assert len(spec.subagents) == 3
    with pytest.raises(ValueError, match="sandbox"):
        asyncio.run(
            build_copilot(
                BuildContext(
                    models(config, fake("done")),
                    qmx_home=tmp_path,
                    control=ControlService(tmp_path),
                    checkpointer=InMemorySaver(),
                )
            )
        )
