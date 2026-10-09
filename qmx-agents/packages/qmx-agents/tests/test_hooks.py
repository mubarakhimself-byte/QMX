from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, cast

import pytest
from conftest import compiled, fake, fake_models
from langchain.mcp import MCPAdapter
from langchain_core.messages import ToolMessage
from langchain_core.runnables import Runnable
from langchain_core.tools import ToolException, tool
from qmx_apps.manifest import Trust
from qmx_apps.road.models import Stage
from qmx_control.models import Document
from qmx_control.server import create_mcp
from qmx_control.service import ControlError, ControlService, SessionInput
from test_spec import call, write_spec

from qmx_agents.guards import RunJournal
from qmx_agents.router import ModelRouter, RouterConfig, RunContext
from qmx_agents.spec import BuildContext, build_agent


class FakeApps(ControlService):
    def __init__(self, home: Path) -> None:
        super().__init__(home)
        self.definition: Document = {
            "id": "demo",
            "name": "Demo",
            "version": "1.0.0",
            "risk": "shows",
            "kind": "headless",
            "entrypoints": {"mcp": "server.py"},
        }
        self.hash = "version-one"
        self.test_result: Document = {
            "stage": "tests",
            "passed": True,
            "definition_hash": self.hash,
        }
        self.evidence: list[Document] = []
        self.tested: list[str] = []
        self.published: list[str] = []
        self.installed: list[str] = []
        self.unavailable = False
        self.change_during_tests = False

    def apps_get(self, app_id: str) -> Document:
        return {"definition": self.definition, "definition_hash": self.hash}

    def apps_evidence(self, app_id: str) -> list[Document]:
        return self.evidence

    def apps_test(
        self, app_id: str, expected_hash: str | None = None, stage: Stage | None = None
    ) -> Document:
        assert expected_hash == self.hash
        assert stage == "tests"
        self.tested.append(app_id)
        if self.unavailable:
            raise ControlError("test_unavailable", "The app test runner is unavailable.", 503)
        if self.change_during_tests:
            self.hash = "version-two"
        return self.test_result

    def apps_publish(
        self,
        app_id: str,
        expected_hash: str | None = None,
        expected_active: str | None = None,
        signature: str | None = None,
    ) -> Document:
        self.published.append(app_id)
        return {"status": "published"}

    def apps_create(self, path: str, trust: Trust = "agent") -> Document:
        self.installed.append(path)
        return self.apps_get("demo")

    def apps_update(
        self, app_id: str, path: str, trust: Trust = "agent", expected_hash: str | None = None
    ) -> Document:
        return self.apps_create(path, trust)


def messages(result: dict[str, Any]) -> list[ToolMessage]:
    return [item for item in result["messages"] if isinstance(item, ToolMessage)]


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("name", ["publish_app", "apps_publish", "qmx-control_apps_publish"])
@pytest.mark.parametrize(
    "problem",
    [
        "none",
        "manifest",
        "failed",
        "stale",
        "changed",
        "unavailable",
        "no-service",
        "wrong-stage",
        "generic-success",
    ],
)
def test_publish_requires_valid_manifest_and_current_green_tests(
    tmp_path: Path, config: RouterConfig, asynchronous: bool, name: str, problem: str
) -> None:
    service = FakeApps(tmp_path / "home")
    if problem == "manifest":
        service.definition["risk"] = "invalid"
    elif problem == "failed":
        service.test_result["passed"] = False
    elif problem == "stale":
        service.test_result["definition_hash"] = "old-version"
    elif problem == "changed":
        service.change_during_tests = True
    elif problem == "unavailable":
        service.unavailable = True
    elif problem == "wrong-stage":
        service.test_result["stage"] = "shadow"
    elif problem == "generic-success":
        service.test_result = {"status": "passed", "definition_hash": service.hash}

    @tool(name)
    def publish(app_id: str) -> str:
        """Publish the app."""
        return json.dumps(service.apps_publish(app_id))

    with RunJournal(tmp_path / "run.jsonl", "hooks") as journal:
        ctx = BuildContext(
            ModelRouter(config, fake_models(fake(call(name, {"app_id": "demo"}), "done"))),
            tools={name: publish},
            control=service if problem != "no-service" else None,
            journal=journal,
        )
        graph = compiled(write_spec(tmp_path, f"tools: ['{name}']"), ctx)
        inputs = {"messages": [{"role": "user", "content": "Publish demo"}]}
        result = asyncio.run(graph.ainvoke(inputs)) if asynchronous else graph.invoke(inputs)
        response = messages(result)[0]
        if problem == "none":
            assert service.published == ["demo"]
            assert response.status == "success"
        else:
            assert service.published == []
            assert response.status == "error"
            assert "refused" in response.text
        rows = [json.loads(line) for line in journal.path.read_text().splitlines()]
        assert [row["event"] for row in rows].count("tool_end") == 1
        reference = next(row["payload"]["result_ref"] for row in rows if row["event"] == "tool_end")
        assert json.loads(Path(reference).read_text())["status"] == response.status


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("stage", ["tests", "sandbox", "shadow", "live", "failed-tests"])
def test_publish_reuses_current_tests_without_advancing_the_road(
    tmp_path: Path, config: RouterConfig, asynchronous: bool, stage: str
) -> None:
    service = FakeApps(tmp_path / "home")
    service.evidence = [
        {"stage": "tests", "passed": True, "definition_hash": "old-version"},
        dict(service.test_result),
    ]
    failed = stage == "failed-tests"
    service.evidence.append(
        {
            "stage": "tests" if failed else stage,
            "passed": not failed,
            "definition_hash": service.hash,
        }
    )
    service.test_result["passed"] = not failed
    service.unavailable = not failed  # Any extra stage advancement would fail this journey.

    @tool
    def apps_publish(app_id: str) -> str:
        """Publish an app whose current tests have already run."""
        return json.dumps(service.apps_publish(app_id))

    graph = compiled(
        write_spec(tmp_path, "tools: [apps_publish]"),
        BuildContext(
            ModelRouter(
                config, fake_models(fake(call("apps_publish", {"app_id": "demo"}), "done"))
            ),
            tools={"apps_publish": apps_publish},
            control=service,
        ),
    )
    inputs = {"messages": [("user", "Publish")]}
    result = asyncio.run(graph.ainvoke(inputs)) if asynchronous else graph.invoke(inputs)
    assert service.tested == (["demo"] if failed else [])
    assert service.published == ([] if failed else ["demo"])
    assert messages(result)[0].status == ("error" if failed else "success")


@pytest.mark.parametrize("operation", ["apps_create", "apps_update"])
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("outcome", ["passed", "failed", "unavailable", "install-failed"])
def test_new_versions_run_tests_automatically(
    tmp_path: Path, config: RouterConfig, operation: str, asynchronous: bool, outcome: str
) -> None:
    service = FakeApps(tmp_path / "home")
    service.test_result["passed"] = outcome == "passed"
    service.unavailable = outcome == "unavailable"

    @tool(operation)
    def install(path: str) -> str:
        """Build an immutable version."""
        if outcome == "install-failed":
            raise ToolException("install failed")
        return json.dumps(service.apps_create(path))

    install.handle_tool_error = True
    graph = compiled(
        write_spec(tmp_path, f"tools: [{operation}]"),
        BuildContext(
            ModelRouter(config, fake_models(fake(call(operation, {"path": "fixture"}), "done"))),
            tools={operation: install},
            control=service,
        ),
    )
    inputs = {"messages": [{"role": "user", "content": "Build a version"}]}
    result = asyncio.run(graph.ainvoke(inputs)) if asynchronous else graph.invoke(inputs)
    assert service.tested == ([] if outcome == "install-failed" else ["demo"])
    response = messages(result)[0]
    assert response.status == ("success" if outcome == "passed" else "error")
    if outcome in {"failed", "unavailable"}:
        assert "App installed, but automatic tests failed" in response.text


def test_mcp_structured_version_result_triggers_tests(tmp_path: Path, config: RouterConfig) -> None:
    async def journey() -> None:
        service = FakeApps(tmp_path / "home")
        async with MCPAdapter(create_mcp(service)) as adapter:
            tools = await adapter.list_tools()
            create = next(item for item in tools if item.name == "apps_create")
        graph = cast(
            "Runnable[Any, dict[str, Any]]",
            await build_agent(
                write_spec(tmp_path, "tools: [create]"),
                BuildContext(
                    ModelRouter(
                        config, fake_models(fake(call("apps_create", {"path": "fixture"}), "done"))
                    ),
                    tools={"create": create},
                    control=service,
                ),
            ),
        )
        result = await graph.ainvoke({"messages": [("user", "Build")]})
        assert messages(result)[0].status == "success"
        assert service.tested == ["demo"]
        assert service.installed == ["fixture"]

    asyncio.run(journey())


def test_breaker_notifies_copilot_and_operator_between_turns(
    tmp_path: Path, config: RouterConfig
) -> None:
    service = ControlService(tmp_path / "home")
    session = service.sessions_create(SessionInput(title="Copilot"))
    session_id = str(session["id"])
    ctx = BuildContext(
        ModelRouter(config, fake_models(fake("done"))),
        control=service,
        run=RunContext(session_id=session_id),
    )
    spec = write_spec(tmp_path)
    compiled(spec, ctx).invoke({"messages": [("user", "Hello")]})
    compiled(spec, ctx)  # Rebuilding keeps the subscription rather than duplicating it.
    sink = service.app_runtime().event_sink
    assert sink is not None
    trip: Document = {
        "status": "tripped",
        "instance_id": "fake-instance",
        "breaker": {"open": True, "reason": "error budget exceeded"},
    }
    try:
        sink("demo", trip)
        compiled(spec, ctx)
        sink("demo", trip)
        events = cast("list[dict[str, Any]]", service.sessions_stream(session_id))
        blocks = [event["data"]["block"] for event in events if event["data"]["type"] == "block"]
        assert len(blocks) == 1
        assert blocks[0]["type"] == "needs_you"
        assert blocks[0]["content"]["reason"] == "error budget exceeded"
        app_events = cast("list[dict[str, Any]]", service.events("apps"))
        notices = [event for event in app_events if event["data"].get("type") == "needs_you"]
        assert len(notices) == 1
        assert notices[0]["data"]["session_id"] == session_id
        assert service.jobs_list()[0]["status"] == "failed"
        sink("demo", {"status": "running", "instance_id": "second"})
        sink("demo", {**trip, "instance_id": "second"})
        app_events = cast("list[dict[str, Any]]", service.events("apps"))
        assert len([event for event in app_events if event["data"].get("type") == "needs_you"]) == 2
    finally:
        service.close()
