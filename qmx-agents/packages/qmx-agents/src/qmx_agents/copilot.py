"""Compose the Copilot and project actual graph events into the shared session log."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Literal, cast

from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from deepagents.backends.protocol import ExecuteResponse, SandboxBackendProtocol
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph  # pyright: ignore[reportMissingTypeStubs]
from langgraph.types import Command, interrupt
from qmx_control.models import Document
from qmx_control.server import create_mcp
from qmx_control.service import ControlService, SessionBlock, SessionInput
from qmx_tools import DomainContext
from qmx_tools.servers import create_server

from qmx_agents.guards import RunJournal
from qmx_agents.memory import MemoryRecord, Scope
from qmx_agents.router import RunContext
from qmx_agents.spec import BuildContext, build_agent, load_spec

SPEC = Path(__file__).with_name("agents") / "copilot.yaml"


class AppSandbox(FilesystemBackend, SandboxBackendProtocol):
    """Delegate execution to an installed, reviewed sandbox app owned by the supervisor."""

    def __init__(self, service: ControlService, app_id: str, root: Path) -> None:
        super().__init__(root_dir=root, virtual_mode=True)
        self.service = service
        self.app_id = app_id

    @property
    def id(self) -> str:
        return self.app_id

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        response = self.service.apps_call(
            self.app_id, "execute", {"command": command, "timeout": timeout}
        )
        result = cast(Document, response["result"])
        return ExecuteResponse(
            output=str(result["output"]),
            exit_code=int(cast(int, result["exit_code"])),
            truncated=result.get("truncated") is True,
        )


async def build_copilot(ctx: BuildContext, data: DomainContext | None = None) -> Any:
    if ctx.control is None or ctx.qmx_home is None or ctx.checkpointer is None:
        raise ValueError("Copilot requires its control service, home and checkpointer.")
    if not isinstance(ctx.agent_backends.get("data-analyst"), SandboxBackendProtocol):
        raise ValueError("data-analyst requires a supervised Python sandbox backend.")
    if ctx.run.session_id is None:
        raise ValueError("Copilot requires a session identity.")
    if ctx.journal is None:
        ctx.journal = RunJournal(
            ctx.qmx_home / "runs" / ctx.run.session_id / "journal.jsonl", ctx.run.session_id
        )
        ctx.journal_resources.append(ctx.journal)
    ctx.mcp_targets.setdefault("qmx-control", create_mcp(ctx.control))
    domain = data or DomainContext(root=ctx.qmx_home / "domain")
    for name in ("data", "backtest", "research"):
        ctx.mcp_targets.setdefault(f"qmx-{name}", create_server(name, domain))
    ctx.backend = CompositeBackend(
        default=ctx.backend or StateBackend(),
        routes={
            "/skills/": FilesystemBackend(root_dir=SPEC.parent.parent / "skills", virtual_mode=True)
        },
    )

    async def approve_global(scope: Scope, record: MemoryRecord | None) -> bool:
        return (
            interrupt({"kind": "global_memory", "content": record.content if record else None})
            is True
        )

    ctx.memory_approval = ctx.memory_approval or approve_global
    ctx.explicit_publish = True
    spec = load_spec(SPEC)
    # Settings are the explicit opt-in for additional servers, including paid providers.
    configured = {**ctx.router.config.mcp_servers, **ctx.control.settings_get("mcp_servers")}
    spec.mcp_servers.extend(
        name
        for name, settings in configured.items()
        if name not in spec.mcp_servers
        and isinstance(settings, dict)
        and settings.get("enabled") is True
    )
    return await build_agent(spec, ctx)


async def stream_turn(
    graph: CompiledStateGraph[Any, RunContext, Any, Any],
    service: ControlService,
    session_id: str,
    prompt: str | Command[Any],
    *,
    context: RunContext | None = None,
    mode: Literal["plan", "do"] = "do",
) -> None:
    """Append completed messages, tool events and approval requests; SSE reads the same log."""
    config: RunnableConfig = {"configurable": {"thread_id": session_id}}
    run = replace(
        context or RunContext(),
        session_id=session_id,
        request_model="tier:reasoning_high" if mode == "plan" else "tier:workhorse",
    )
    if isinstance(prompt, str):
        service.sessions_append(session_id, SessionBlock(type="user", content={"text": prompt}))
        inputs: Any = {"messages": [("user", prompt)]}
    else:
        inputs = prompt
    seen: set[str] = set()
    children: dict[str, str] = {}

    def append(target: str, kind: str, content: Document) -> None:
        service.sessions_append(
            target, SessionBlock.model_validate({"type": kind, "content": content})
        )

    async for chunk in cast(Any, graph).astream(
        inputs, config=config, context=run, stream_mode="updates", subgraphs=True, version="v2"
    ):
        namespace = tuple(chunk["ns"])
        target = session_id
        if namespace:
            key = "/".join(namespace)
            if key not in children:
                child = service.sessions_create(
                    SessionInput(title="Delegated task", parent_id=session_id)
                )
                children[key] = str(child["id"])
                append(
                    session_id,
                    "agents",
                    {"session_id": children[key], "state": "working", "namespace": key},
                )
            target = children[key]
        for node, update in cast(dict[str, Any], chunk["data"]).items():
            if node == "__interrupt__":
                for item in update:
                    append(target, "permission", {"interrupt_id": item.id, "request": item.value})
                continue
            if not isinstance(update, dict):
                continue
            for message in cast(list[Any], cast(dict[str, Any], update).get("messages", [])):
                identity = f"{target}:{message.id}"
                if message.id and identity in seen:
                    continue
                seen.add(identity)
                if isinstance(message, AIMessage):
                    if message.text:
                        append(target, "text", {"text": message.text})
                    for call in message.tool_calls:
                        append(
                            target,
                            "tool",
                            {
                                "id": call["id"],
                                "name": call["name"],
                                "arguments": call["args"],
                                "state": "started",
                            },
                        )
                        if call["name"] == "write_todos":
                            append(target, "plan", {"todos": call["args"].get("todos", [])})
                        if call["name"] in {"task", "start_task"}:
                            append(
                                target,
                                "agents",
                                {
                                    "name": call["args"].get(
                                        "subagent_type", call["args"].get("name")
                                    ),
                                    "state": "working",
                                },
                            )
                elif isinstance(message, ToolMessage):
                    append(
                        target,
                        "tool",
                        {
                            "id": message.tool_call_id,
                            "name": message.name,
                            "state": message.status,
                            "result": message.text,
                        },
                    )
                    if message.status == "error":
                        continue
                    artifact = cast(dict[str, Any], message.artifact or {})
                    result = artifact.get("structured_content")
                    if result is None:
                        try:
                            result = json.loads(message.text)
                        except ValueError:
                            continue
                    if isinstance(result, dict) and "artifact_id" in result:
                        append(target, "artifact", cast(Document, result))
    state = await graph.aget_state(config)
    if not state.next:
        for child in children.values():
            append(session_id, "agents", {"session_id": child, "state": "complete"})
