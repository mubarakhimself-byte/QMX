"""Library hooks enforce the money barrier and record model/tool evidence."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, cast

from deepagents.middleware.filesystem import FilesystemState
from langchain.agents.middleware import (
    AgentMiddleware,
    AgentState,
    HumanInTheLoopMiddleware,
    ModelRequest,
    ModelResponse,
)
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.errors import GraphInterrupt
from langgraph.runtime import Runtime
from langgraph.types import Command, Interrupt

from qmx_agents.guards.journal import RunJournal, encoded, fingerprint
from qmx_agents.guards.money_path import check_tool
from qmx_agents.router import RunContext


class AdmissionStateMiddleware(AgentMiddleware[FilesystemState, RunContext]):
    # Wrapping StateBackend hides it from the SDK's isinstance-based schema
    # discovery. Retain the SDK's public files channel and deletion reducer.
    state_schema = FilesystemState


class MoneyPathMiddleware(AgentMiddleware[Any, RunContext]):
    def wrap_model_call(
        self,
        request: ModelRequest[RunContext],
        handler: Callable[[ModelRequest[RunContext]], ModelResponse[Any]],
    ) -> ModelResponse[Any]:
        for tool in request.tools:
            if isinstance(tool, BaseTool):
                check_tool(tool)
        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest[RunContext],
        handler: Callable[[ModelRequest[RunContext]], Awaitable[ModelResponse[Any]]],
    ) -> ModelResponse[Any]:
        for tool in request.tools:
            if isinstance(tool, BaseTool):
                check_tool(tool)
        return await handler(request)

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        if request.tool:
            check_tool(request.tool)
        return handler(request)

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        if request.tool:
            check_tool(request.tool)
        return await handler(request)


class JournalMiddleware(AgentMiddleware[Any, RunContext]):
    def __init__(self, journal: RunJournal, agent: str, context: RunContext) -> None:
        self.journal = journal
        self.agent = agent
        self.context = context

    def _record(self, event: str, payload: dict[str, object]) -> None:
        self.journal.append(event, {"agent": self.agent, **payload})

    def before_agent(self, state: AgentState[Any], runtime: Runtime[RunContext]) -> None:
        ctx = runtime.context or self.context
        self._record(
            "run_start",
            {
                "app_id": ctx.app_id,
                "session_id": ctx.session_id,
                "workflow_id": ctx.workflow_id,
                "thread_id": runtime.execution_info.thread_id if runtime.execution_info else None,
            },
        )

    async def abefore_agent(self, state: AgentState[Any], runtime: Runtime[RunContext]) -> None:
        self.before_agent(state, runtime)

    def after_agent(self, state: AgentState[Any], runtime: Runtime[RunContext]) -> None:
        self._record("run_end", {"status": "completed"})

    async def aafter_agent(self, state: AgentState[Any], runtime: Runtime[RunContext]) -> None:
        self.after_agent(state, runtime)

    def _model_response(
        self, request: ModelRequest[RunContext], response: ModelResponse[Any]
    ) -> None:
        ctx = request.runtime.context or self.context
        for message in response.result:
            if isinstance(message, AIMessage):
                self._record(
                    "model_call",
                    {
                        "model": ctx.effective_models.get(
                            self.agent, self.context.effective_models.get(self.agent)
                        ),
                        "usage": message.usage_metadata,
                        "metadata": message.response_metadata,
                        "message_id": message.id,
                    },
                )

    def wrap_model_call(
        self,
        request: ModelRequest[RunContext],
        handler: Callable[[ModelRequest[RunContext]], ModelResponse[Any]],
    ) -> ModelResponse[Any]:
        try:
            response = handler(request)
        except Exception as exc:
            self._record("model_error", {"error_type": type(exc).__name__})
            self._record("run_end", {"status": "failed"})
            raise
        self._model_response(request, response)
        return response

    async def awrap_model_call(
        self,
        request: ModelRequest[RunContext],
        handler: Callable[[ModelRequest[RunContext]], Awaitable[ModelResponse[Any]]],
    ) -> ModelResponse[Any]:
        try:
            response = await handler(request)
        except Exception as exc:
            self._record("model_error", {"error_type": type(exc).__name__})
            self._record("run_end", {"status": "failed"})
            raise
        self._model_response(request, response)
        return response

    def _start_tool(self, request: ToolCallRequest) -> None:
        self._record(
            "tool_start",
            {
                "name": request.tool_call["name"],
                "call_id": request.tool_call["id"],
                "arguments_hash": fingerprint(request.tool_call["args"]),
            },
        )

    def _end_tool(self, request: ToolCallRequest, result: ToolMessage | Command[Any]) -> None:
        payload = (
            result.model_dump(mode="json") if isinstance(result, ToolMessage) else result.update
        )
        reference = self.journal.store_result(encoded(payload))
        self._record(
            "tool_end",
            {
                "name": request.tool_call["name"],
                "call_id": request.tool_call["id"],
                "result_ref": reference,
            },
        )

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        self._start_tool(request)
        try:
            result = handler(request)
        except GraphInterrupt:
            # Delegated approval pauses propagate through the task tool.
            raise
        except Exception as exc:
            self._record("run_end", {"status": "failed", "error_type": type(exc).__name__})
            raise
        self._end_tool(request, result)
        return result

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        self._start_tool(request)
        try:
            result = await handler(request)
        except GraphInterrupt:
            raise
        except Exception as exc:
            self._record("run_end", {"status": "failed", "error_type": type(exc).__name__})
            raise
        self._end_tool(request, result)
        return result


class JournalApprovals(HumanInTheLoopMiddleware[Any, RunContext]):
    def __init__(self, journal: RunJournal, interrupt_on: dict[str, bool]) -> None:
        super().__init__(dict(interrupt_on))
        self.journal = journal

    @property
    def name(self) -> str:
        # Deep Agents replaces its default middleware when names match.
        return "HumanInTheLoopMiddleware"

    def after_model(
        self, state: AgentState[Any], runtime: Runtime[RunContext]
    ) -> dict[str, Any] | None:
        try:
            update = super().after_model(state, runtime)
        except GraphInterrupt as exc:
            for item in cast("tuple[Interrupt, ...]", exc.args[0]):
                reference = self.journal.store_result(encoded(item.value))
                self.journal.append("interrupt", {"result_ref": reference})
            raise
        if update and "messages" in update:
            messages = [message.model_dump(mode="json") for message in update["messages"]]
            reference = self.journal.store_result(encoded({**update, "messages": messages}))
            self.journal.append("approval_resolved", {"result_ref": reference})
        return update

    async def aafter_model(
        self, state: AgentState[Any], runtime: Runtime[RunContext]
    ) -> dict[str, Any] | None:
        return self.after_model(state, runtime)
