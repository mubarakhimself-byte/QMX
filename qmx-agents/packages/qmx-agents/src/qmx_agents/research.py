"""Persist successful Firecrawl page reads in the node's shared Library."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, cast

from langchain.agents.middleware import AgentMiddleware
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from pydantic import JsonValue
from qmx_control.service import ControlService, LibraryInput

from qmx_agents.router import RunContext


class ResearchLibraryMiddleware(AgentMiddleware[Any, RunContext]):
    def __init__(self, service: ControlService) -> None:
        self.service = service

    def _save(self, request: ToolCallRequest, result: ToolMessage | Command[Any]) -> None:
        url = request.tool_call["args"].get("url")
        if (
            request.tool_call["name"] != "firecrawl_scrape"
            or not isinstance(url, str)
            or not url.startswith(("https://", "http://"))
            or not isinstance(result, ToolMessage)
            or result.status == "error"
        ):
            return
        self.service.library_save(
            LibraryInput(
                title=url[:200],
                kind="article",
                source=url,
                fetched_date=datetime.now(UTC).date().isoformat(),
                content=cast(JsonValue, result.model_dump(mode="json")["content"]),
                tags=["firecrawl"],
            )
        )

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        result = handler(request)
        self._save(request, result)
        return result

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        result = await handler(request)
        self._save(request, result)
        return result
