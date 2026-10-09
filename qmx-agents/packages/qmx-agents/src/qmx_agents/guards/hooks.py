"""Deterministic app checks around Copilot tool calls and supervisor events."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any, cast

from langchain.agents.middleware import AgentMiddleware
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from qmx_apps.errors import AppError
from qmx_apps.manifest import AppDefinition
from qmx_control.models import Document
from qmx_control.service import ControlError, ControlService, SessionBlock

from qmx_agents.router import RunContext


class AppHooksMiddleware(AgentMiddleware[Any, RunContext]):
    def __init__(
        self, service: ControlService | None, names: list[str], *, explicit_publish: bool = False
    ) -> None:
        self.service = service
        self.explicit_publish = explicit_publish
        self.names = {
            name: operation
            for name in names
            for operation in (
                "apps_publish",
                "publish_app",
                "apps_create",
                "apps_update",
                "apps_test",
            )
            if name == operation or name.endswith("_" + operation)
        }

    def _test(self, app_id: str, expected_hash: str | None = None) -> Document:
        if self.service is None:
            raise ValueError("App hooks require the owning ControlService or qmx_home.")
        app = self.service.apps_get(app_id)
        manifest = AppDefinition.model_validate(app["definition"])
        if manifest.id != app_id:
            raise ValueError("The installed manifest has a different app id.")
        definition_hash = app.get("definition_hash")
        if not isinstance(definition_hash, str) or not definition_hash:
            raise ValueError("The installed definition has no content hash.")
        if expected_hash is not None and definition_hash != expected_hash:
            raise ValueError("The app version changed before its tests ran.")
        evidence = self.service.apps_evidence(app_id)
        result = next(
            (
                row
                for row in reversed(evidence)
                if row.get("definition_hash") == definition_hash and row.get("stage") == "tests"
            ),
            cast(Document, {}),
        )
        # apps_test advances the road. Never advance sandbox/shadow from a hook.
        if result.get("passed") is not True:
            result = self.service.apps_test(app_id, expected_hash=definition_hash, stage="tests")
        if (
            result.get("stage") != "tests"
            or result.get("passed") is not True
            or result.get("definition_hash") != definition_hash
        ):
            raise ValueError(f"Tests are not green for this app version: {result}")
        if self.service.apps_get(app_id).get("definition_hash") != definition_hash:
            raise ValueError("The app version changed while its tests ran.")
        return result

    def _before(self, request: ToolCallRequest) -> None:
        operation = self.names.get(request.tool_call["name"])
        if self.explicit_publish and operation == "apps_test":
            # A Copilot proof step must never activate code before publish approval.
            request.tool_call["args"]["auto_publish"] = False
        if operation in {"apps_publish", "publish_app"}:
            app_id = request.tool_call["args"].get("app_id")
            if not isinstance(app_id, str) or not app_id:
                raise ValueError("Publishing requires an app_id.")
            self._test(app_id)

    def _after(self, request: ToolCallRequest, result: ToolMessage | Command[Any]) -> None:
        operation = self.names.get(request.tool_call["name"])
        if operation not in {"apps_create", "apps_update"}:
            return
        if not isinstance(result, ToolMessage):
            raise ValueError("A built app must return its definition and content hash.")
        if result.status == "error":
            return
        artifact = cast("dict[str, Any] | None", result.artifact)
        value = artifact.get("structured_content") if isinstance(artifact, dict) else None
        if value is None:
            value = json.loads(result.text)
        if not isinstance(value, dict):
            raise ValueError("A built app must return its definition and content hash.")
        data = cast(Document, value)
        definition = data.get("definition")
        if not isinstance(definition, dict):
            raise ValueError("A built app must return its definition and content hash.")
        app_id = definition.get("id")
        definition_hash = data.get("definition_hash")
        if not isinstance(app_id, str) or not isinstance(definition_hash, str):
            raise ValueError("A built app must return its definition and content hash.")
        self._test(app_id, definition_hash)

    @staticmethod
    def _error(request: ToolCallRequest, error: Exception, *, built: bool = False) -> ToolMessage:
        prefix = "App installed, but automatic tests failed" if built else "App action refused"
        return ToolMessage(
            content=f"{prefix}: {error}",
            tool_call_id=request.tool_call["id"],
            name=request.tool_call["name"],
            status="error",
        )

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        try:
            self._before(request)
        except (ValueError, ControlError, AppError) as error:
            return self._error(request, error)
        result = handler(request)
        try:
            self._after(request, result)
        except (ValueError, ControlError, AppError) as error:
            return self._error(request, error, built=True)
        return result

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        try:
            await asyncio.to_thread(self._before, request)
        except (ValueError, ControlError, AppError) as error:
            return self._error(request, error)
        result = await handler(request)
        try:
            await asyncio.to_thread(self._after, request, result)
        except (ValueError, ControlError, AppError) as error:
            return self._error(request, error, built=True)
        return result


def watch_breakers(service: ControlService, session_id: str) -> None:
    """Keep notifications alive between turns, while the owning service is running."""
    tripped: dict[str, object] = {}

    def on_event(app_id: str, data: Document) -> None:
        status = data.get("status")
        if status != "tripped":
            if status in {"running", "installed"}:
                tripped.pop(app_id, None)
            return
        instance_id = data.get("instance_id")
        if app_id in tripped and tripped[app_id] == instance_id:
            return
        breaker = data.get("breaker")
        reason = breaker.get("reason") if isinstance(breaker, dict) else "App breaker tripped."
        content: Document = {
            "app_id": app_id,
            "instance_id": data.get("instance_id"),
            "reason": reason,
        }
        service.sessions_append(session_id, SessionBlock(type="needs_you", content=content))
        # The operator already receives the supervisor's app event over SSE.
        # Mark it actionable without adding a second notification transport.
        service.notify_app(app_id, {"type": "needs_you", "session_id": session_id, **content})
        tripped[app_id] = instance_id

    service.watch_app_events(session_id, on_event)
